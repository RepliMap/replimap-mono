/**
 * Metrics Dashboard API Handlers
 *
 * Aggregated metrics for admin/analytics
 */

import type { Env } from '../types/env';
import { AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { verifyAdminApiKey } from '../lib/security';

// =============================================================================
// Response Types
// =============================================================================

interface FeatureUsageItem {
  event_type: string;
  normalized_event_type?: string;
  unique_users: number;
  total_uses: number;
  deprecated_uses?: number;
}

interface AdoptionResponse {
  period: string;
  feature_usage: FeatureUsageItem[];
  new_feature_adoption: Array<{
    event_type: string;
    adopters: number;
    first_use: string;
  }>;
  deprecation_status?: {
    old_cli_users_last_7_days: number;
    deprecated_events_last_7_days: number;
    migration_complete: boolean;
  };
}

interface ConversionResponse {
  period: string;
  audit_to_fix: {
    audit_users: number;
    fix_users: number;
    conversion_rate: string;
  };
  drift_to_snapshot: {
    drift_users: number;
    snapshot_users: number;
  };
}

interface RemediationImpactResponse {
  period: string;
  summary: {
    total_runs: number;
    total_findings: number;
    total_fixable: number;
    total_manual: number;
    total_files_generated: number;
  };
  estimated_time_saved: {
    hours: number;
    days: string;
  };
  fix_rate: string;
}

interface SnapshotUsageResponse {
  period: string;
  snapshots: {
    total_snapshots: number;
    unique_users: number;
    total_resources_tracked: number;
    avg_resources_per_snapshot: number;
  };
  diffs: {
    total_diffs: number;
  };
  engagement_rate: string;
}

interface DepsUsageResponse {
  period: string;
  summary: {
    total_analyses: number;
    unique_users: number;
    avg_affected: number;
    max_affected: number;
  };
  cli_version_migration: {
    old_cli_percentage: string;
    new_cli_percentage: string;
  };
}

// =============================================================================
// Admin Authentication
// =============================================================================

/**
 * Validate admin API key with constant-time comparison.
 * Uses shared security utility to prevent timing attacks.
 */
function validateAdminAuth(request: Request, env: Env): void {
  verifyAdminApiKey(request, env.ADMIN_API_KEY);
}

// =============================================================================
// Handlers
// =============================================================================

/**
 * Get feature adoption metrics
 * GET /v1/metrics/adoption
 */
export async function handleGetAdoption(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateAdminAuth(request, env);

    // Feature usage last 30 days with normalized event types
    const featureUsage = await env.DB.prepare(`
      SELECT
        CASE
          WHEN event_type IN ('blast', 'deps', 'deps_explore') THEN 'deps'
          WHEN event_type IN ('blast_export', 'deps_export') THEN 'deps_export'
          WHEN event_type = 'blast_analyze' THEN 'deps_explore'
          ELSE event_type
        END as normalized_event_type,
        event_type,
        COUNT(DISTINCT license_id) as unique_users,
        COUNT(*) as total_uses,
        SUM(CASE WHEN event_type LIKE 'blast%' THEN 1 ELSE 0 END) as deprecated_uses
      FROM usage_events
      WHERE created_at > datetime('now', '-30 days')
      GROUP BY 1, 2
      ORDER BY total_uses DESC
    `).all();

    // New feature adoption
    const newFeatures = ['audit_fix', 'snapshot_save', 'snapshot_diff', 'deps', 'deps_explore'];
    const newFeatureAdoption = await env.DB.prepare(`
      SELECT
        event_type,
        COUNT(DISTINCT license_id) as adopters,
        MIN(created_at) as first_use
      FROM usage_events
      WHERE event_type IN (${newFeatures.map(() => '?').join(',')})
      GROUP BY event_type
    `).bind(...newFeatures).all();

    // Deprecation stats
    const deprecationStats = await env.DB.prepare(`
      SELECT
        COUNT(DISTINCT license_id) as users_on_old_cli,
        COUNT(*) as deprecated_event_count
      FROM usage_events
      WHERE event_type LIKE 'blast%'
        AND created_at > datetime('now', '-7 days')
    `).first<{ users_on_old_cli: number; deprecated_event_count: number }>();

    const response: AdoptionResponse = {
      period: 'last_30_days',
      feature_usage: (featureUsage.results || []) as unknown as FeatureUsageItem[],
      new_feature_adoption: (newFeatureAdoption.results || []) as unknown as AdoptionResponse['new_feature_adoption'],
      deprecation_status: {
        old_cli_users_last_7_days: deprecationStats?.users_on_old_cli || 0,
        deprecated_events_last_7_days: deprecationStats?.deprecated_event_count || 0,
        migration_complete: (deprecationStats?.deprecated_event_count || 0) === 0,
      },
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}

/**
 * Get conversion metrics
 * GET /v1/metrics/conversion
 */
export async function handleGetConversion(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateAdminAuth(request, env);

    // Audit → Audit Fix conversion
    const auditConversion = await env.DB.prepare(`
      WITH audit_users AS (
        SELECT DISTINCT license_id
        FROM usage_events
        WHERE event_type = 'audit' AND created_at > datetime('now', '-30 days')
      ),
      fix_users AS (
        SELECT DISTINCT license_id
        FROM usage_events
        WHERE event_type = 'audit_fix' AND created_at > datetime('now', '-30 days')
      )
      SELECT
        (SELECT COUNT(*) FROM audit_users) as audit_users,
        (SELECT COUNT(*) FROM fix_users) as fix_users,
        (SELECT COUNT(*) FROM fix_users WHERE license_id IN (SELECT license_id FROM audit_users)) as converted
    `).first<{ audit_users: number; fix_users: number; converted: number }>();

    // Drift → Snapshot conversion
    const snapshotConversion = await env.DB.prepare(`
      WITH drift_users AS (
        SELECT DISTINCT license_id
        FROM usage_events
        WHERE event_type = 'drift' AND created_at > datetime('now', '-30 days')
      ),
      snapshot_users AS (
        SELECT DISTINCT license_id
        FROM usage_events
        WHERE event_type IN ('snapshot_save', 'snapshot_diff') AND created_at > datetime('now', '-30 days')
      )
      SELECT
        (SELECT COUNT(*) FROM drift_users) as drift_users,
        (SELECT COUNT(*) FROM snapshot_users) as snapshot_users
    `).first<{ drift_users: number; snapshot_users: number }>();

    const auditUsers = auditConversion?.audit_users || 0;
    const converted = auditConversion?.converted || 0;

    const response: ConversionResponse = {
      period: 'last_30_days',
      audit_to_fix: {
        audit_users: auditUsers,
        fix_users: auditConversion?.fix_users || 0,
        conversion_rate: auditUsers > 0 ? ((converted / auditUsers) * 100).toFixed(1) + '%' : '0%',
      },
      drift_to_snapshot: {
        drift_users: snapshotConversion?.drift_users || 0,
        snapshot_users: snapshotConversion?.snapshot_users || 0,
      },
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}

/**
 * Get remediation impact metrics
 * GET /v1/metrics/remediation-impact
 */
export async function handleGetRemediationImpact(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateAdminAuth(request, env);

    const impact = await env.DB.prepare(`
      SELECT
        COUNT(*) as total_runs,
        COALESCE(SUM(total_findings), 0) as total_findings,
        COALESCE(SUM(total_fixable), 0) as total_fixable,
        COALESCE(SUM(total_manual), 0) as total_manual,
        COALESCE(SUM(files_generated), 0) as total_files_generated
      FROM remediations
      WHERE created_at > datetime('now', '-30 days')
    `).first<{
      total_runs: number;
      total_findings: number;
      total_fixable: number;
      total_manual: number;
      total_files_generated: number;
    }>();

    // Estimate time saved (30 min per fix on average)
    const totalFixable = impact?.total_fixable || 0;
    const timeSavedHours = totalFixable * 0.5;
    const totalFindings = impact?.total_findings || 0;

    const response: RemediationImpactResponse = {
      period: 'last_30_days',
      summary: {
        total_runs: impact?.total_runs || 0,
        total_findings: totalFindings,
        total_fixable: totalFixable,
        total_manual: impact?.total_manual || 0,
        total_files_generated: impact?.total_files_generated || 0,
      },
      estimated_time_saved: {
        hours: timeSavedHours,
        days: (timeSavedHours / 8).toFixed(1),
      },
      fix_rate: totalFindings > 0 ? ((totalFixable / totalFindings) * 100).toFixed(1) + '%' : '0%',
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}

/**
 * Get snapshot usage metrics
 * GET /v1/metrics/snapshot-usage
 */
export async function handleGetSnapshotUsage(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateAdminAuth(request, env);

    const usage = await env.DB.prepare(`
      SELECT
        COUNT(*) as total_snapshots,
        COUNT(DISTINCT license_id) as unique_users,
        COALESCE(SUM(resource_count), 0) as total_resources_tracked,
        COALESCE(AVG(resource_count), 0) as avg_resources_per_snapshot
      FROM snapshots
      WHERE created_at > datetime('now', '-30 days')
    `).first<{
      total_snapshots: number;
      unique_users: number;
      total_resources_tracked: number;
      avg_resources_per_snapshot: number;
    }>();

    // Snapshot diff usage
    const diffUsage = await env.DB.prepare(`
      SELECT COUNT(*) as total_diffs
      FROM usage_events
      WHERE event_type = 'snapshot_diff' AND created_at > datetime('now', '-30 days')
    `).first<{ total_diffs: number }>();

    const totalSnapshots = usage?.total_snapshots || 0;
    const totalDiffs = diffUsage?.total_diffs || 0;

    const response: SnapshotUsageResponse = {
      period: 'last_30_days',
      snapshots: {
        total_snapshots: totalSnapshots,
        unique_users: usage?.unique_users || 0,
        total_resources_tracked: usage?.total_resources_tracked || 0,
        avg_resources_per_snapshot: Math.round(usage?.avg_resources_per_snapshot || 0),
      },
      diffs: {
        total_diffs: totalDiffs,
      },
      engagement_rate: totalSnapshots > 0 ? ((totalDiffs / totalSnapshots) * 100).toFixed(1) + '%' : '0%',
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}

/**
 * Get dependency explorer (formerly blast radius) usage metrics
 * GET /v1/metrics/deps-usage
 */
export async function handleGetDepsUsage(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateAdminAuth(request, env);

    // Combine all blast + deps events
    const usage = await env.DB.prepare(`
      SELECT
        COUNT(*) as total_analyses,
        COUNT(DISTINCT license_id) as unique_users,
        COALESCE(AVG(CAST(json_extract(metadata, '$.affected_count') AS INTEGER)), 0) as avg_affected,
        COALESCE(MAX(CAST(json_extract(metadata, '$.affected_count') AS INTEGER)), 0) as max_affected,
        SUM(CASE WHEN event_type LIKE 'blast%' OR original_event_type LIKE 'blast%' THEN 1 ELSE 0 END) as from_old_cli,
        SUM(CASE WHEN event_type LIKE 'deps%' AND (original_event_type IS NULL OR original_event_type NOT LIKE 'blast%') THEN 1 ELSE 0 END) as from_new_cli
      FROM usage_events
      WHERE event_type IN ('blast', 'blast_analyze', 'blast_export', 'deps', 'deps_explore', 'deps_export')
        AND created_at > datetime('now', '-30 days')
    `).first<{
      total_analyses: number;
      unique_users: number;
      avg_affected: number;
      max_affected: number;
      from_old_cli: number;
      from_new_cli: number;
    }>();

    const totalAnalyses = usage?.total_analyses || 0;
    const fromOldCli = usage?.from_old_cli || 0;
    const fromNewCli = usage?.from_new_cli || 0;

    const response: DepsUsageResponse = {
      period: 'last_30_days',
      summary: {
        total_analyses: totalAnalyses,
        unique_users: usage?.unique_users || 0,
        avg_affected: Math.round(usage?.avg_affected || 0),
        max_affected: usage?.max_affected || 0,
      },
      cli_version_migration: {
        old_cli_percentage: totalAnalyses > 0 ? ((fromOldCli / totalAnalyses) * 100).toFixed(1) + '%' : '0%',
        new_cli_percentage: totalAnalyses > 0 ? ((fromNewCli / totalAnalyses) * 100).toFixed(1) + '%' : '0%',
      },
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
      });
    }
    throw error;
  }
}
