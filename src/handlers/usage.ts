/**
 * Usage Tracking Handlers
 * POST /v1/usage/sync
 * GET /v1/usage/{license_key}
 * GET /v1/usage/{license_key}/history
 * POST /v1/usage/check-quota
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey, nowISO, generateId } from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import { rateLimit } from '../lib/rate-limiter';
import { getLicenseByKey, getMonthlyUsageCount } from '../lib/db';

// ============================================================================
// Request/Response Types
// ============================================================================

interface SyncUsageRequest {
  license_key: string;
  machine_id: string;
  usage: {
    scans_count?: number;
    resources_scanned?: number;
    terraform_generations?: number;
  };
  period?: string; // YYYY-MM format
  idempotency_key?: string;
}

interface SyncUsageResponse {
  synced: boolean;
  period: string;
  current_usage: UsageData;
  quotas: QuotaInfo;
}

interface UsageData {
  scans_count: number;
  resources_scanned: number;
  terraform_generations: number;
}

interface QuotaInfo {
  scans_limit: number | null; // null = unlimited
  resources_per_scan_limit: number | null;
  scans_remaining: number | null;
}

interface CheckQuotaRequest {
  license_key: string;
  operation: 'scans' | 'resources';
  amount?: number;
}

interface CheckQuotaResponse {
  allowed: boolean;
  unlimited: boolean;
  current: number;
  limit: number | null;
  remaining: number | null;
  requested: number;
}

interface UsageHistoryResponse {
  license_key: string;
  history: Array<{
    period: string;
    scans_count: number;
    resources_scanned: number;
  }>;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Sync usage data from CLI
 * POST /v1/usage/sync
 */
export async function handleSyncUsage(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let body: SyncUsageRequest;
    try {
      body = await request.json() as SyncUsageRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate required fields
    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }
    if (!body.machine_id) {
      throw Errors.invalidRequest('Missing machine_id');
    }
    if (!body.usage) {
      throw Errors.invalidRequest('Missing usage data');
    }

    validateLicenseKey(body.license_key);
    const licenseKey = normalizeLicenseKey(body.license_key);

    // Get license
    const license = await getLicenseByKey(env.DB, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Determine period
    const period = body.period || getCurrentPeriod();

    // Check idempotency
    if (body.idempotency_key) {
      const exists = await checkIdempotencyKey(env.DB, body.idempotency_key);
      if (exists) {
        // Return current usage without updating
        const currentUsage = await getUsageForPeriod(env.DB, license.id, period);
        const plan = license.plan as PlanType;
        const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

        return new Response(JSON.stringify({
          synced: true,
          duplicate: true,
          period,
          current_usage: currentUsage,
          quotas: {
            scans_limit: features.scans_per_month === -1 ? null : features.scans_per_month,
            resources_per_scan_limit: features.resources_per_scan === -1 ? null : features.resources_per_scan,
            scans_remaining: features.scans_per_month === -1 ? null : Math.max(0, features.scans_per_month - currentUsage.scans_count),
          },
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
        });
      }
    }

    // Record usage
    await recordUsage(env.DB, license.id, body.machine_id, period, body.usage, body.idempotency_key);

    // Get updated usage
    const currentUsage = await getUsageForPeriod(env.DB, license.id, period);
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    const response: SyncUsageResponse = {
      synced: true,
      period,
      current_usage: currentUsage,
      quotas: {
        scans_limit: features.scans_per_month === -1 ? null : features.scans_per_month,
        resources_per_scan_limit: features.resources_per_scan === -1 ? null : features.resources_per_scan,
        scans_remaining: features.scans_per_month === -1 ? null : Math.max(0, features.scans_per_month - currentUsage.scans_count),
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
 * Get usage for a license
 * GET /v1/usage/{license_key}
 */
export async function handleGetUsage(
  request: Request,
  env: Env,
  licenseKey: string,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get period from query param
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || getCurrentPeriod();

    // Get license
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Get usage
    const usage = await getUsageForPeriod(env.DB, license.id, period);
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    return new Response(JSON.stringify({
      period,
      usage,
      quotas: {
        scans_limit: features.scans_per_month === -1 ? null : features.scans_per_month,
        resources_per_scan_limit: features.resources_per_scan === -1 ? null : features.resources_per_scan,
        scans_remaining: features.scans_per_month === -1 ? null : Math.max(0, features.scans_per_month - usage.scans_count),
      },
      limits: {
        max_resources_per_scan: features.resources_per_scan === -1 ? null : features.resources_per_scan,
        max_scans_per_month: features.scans_per_month === -1 ? null : features.scans_per_month,
      },
    }), {
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
 * Get usage history for a license
 * GET /v1/usage/{license_key}/history
 */
export async function handleGetUsageHistory(
  request: Request,
  env: Env,
  licenseKey: string,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get months from query param
    const url = new URL(request.url);
    const months = Math.min(12, Math.max(1, parseInt(url.searchParams.get('months') || '6', 10)));

    // Get license
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Get history
    const history = await getUsageHistory(env.DB, license.id, months);

    const response: UsageHistoryResponse = {
      license_key: normalizedKey,
      history,
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
 * Check if an operation is allowed within quota
 * POST /v1/usage/check-quota
 */
export async function handleCheckQuota(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let body: CheckQuotaRequest;
    try {
      body = await request.json() as CheckQuotaRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }
    if (!body.operation) {
      throw Errors.invalidRequest('Missing operation');
    }

    validateLicenseKey(body.license_key);
    const licenseKey = normalizeLicenseKey(body.license_key);
    const amount = body.amount || 1;

    // Get license
    const license = await getLicenseByKey(env.DB, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    let current = 0;
    let limit: number | null = null;
    let unlimited = false;

    if (body.operation === 'scans') {
      current = await getMonthlyUsageCount(env.DB, license.id, 'scan');
      limit = features.scans_per_month === -1 ? null : features.scans_per_month;
      unlimited = features.scans_per_month === -1;
    } else if (body.operation === 'resources') {
      // Resources per scan is checked per-scan, not cumulative
      limit = features.resources_per_scan === -1 ? null : features.resources_per_scan;
      unlimited = features.resources_per_scan === -1;
    } else {
      throw Errors.invalidRequest(`Unknown operation: ${body.operation}`);
    }

    const allowed = unlimited || (limit !== null && current + amount <= limit);
    const remaining = unlimited ? null : (limit !== null ? Math.max(0, limit - current) : null);

    const response: CheckQuotaResponse = {
      allowed,
      unlimited,
      current,
      limit,
      remaining,
      requested: amount,
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

// ============================================================================
// Database Helpers
// ============================================================================

function getCurrentPeriod(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

async function checkIdempotencyKey(db: D1Database, key: string): Promise<boolean> {
  const result = await db.prepare(`
    SELECT 1 FROM usage_idempotency WHERE idempotency_key = ?
  `).bind(key).first();
  return result !== null;
}

async function recordUsage(
  db: D1Database,
  licenseId: string,
  machineId: string,
  period: string,
  usage: SyncUsageRequest['usage'],
  idempotencyKey?: string
): Promise<void> {
  const id = generateId();
  const now = nowISO();

  // Record in usage_logs for each scan
  if (usage.scans_count && usage.scans_count > 0) {
    await db.prepare(`
      INSERT INTO usage_logs (id, license_id, machine_id, action, resources_count, metadata, created_at)
      VALUES (?, ?, ?, 'scan', ?, ?, ?)
    `).bind(
      id,
      licenseId,
      machineId,
      usage.resources_scanned || 0,
      JSON.stringify({ period, scans_count: usage.scans_count }),
      now
    ).run();
  }

  // Record idempotency key if provided
  if (idempotencyKey) {
    await db.prepare(`
      INSERT OR IGNORE INTO usage_idempotency (idempotency_key, license_id, created_at)
      VALUES (?, ?, ?)
    `).bind(idempotencyKey, licenseId, now).run();
  }
}

async function getUsageForPeriod(
  db: D1Database,
  licenseId: string,
  period: string
): Promise<UsageData> {
  // Parse period to get start and end dates
  const [year, month] = period.split('-').map(Number);
  const startDate = new Date(year, month - 1, 1);
  const endDate = new Date(year, month, 1);

  const result = await db.prepare(`
    SELECT
      COUNT(CASE WHEN action = 'scan' THEN 1 END) as scans_count,
      COALESCE(SUM(resources_count), 0) as resources_scanned
    FROM usage_logs
    WHERE license_id = ?
    AND created_at >= ?
    AND created_at < ?
  `).bind(
    licenseId,
    startDate.toISOString(),
    endDate.toISOString()
  ).first<{ scans_count: number; resources_scanned: number }>();

  return {
    scans_count: result?.scans_count || 0,
    resources_scanned: result?.resources_scanned || 0,
    terraform_generations: 0, // Could be tracked separately
  };
}

async function getUsageHistory(
  db: D1Database,
  licenseId: string,
  months: number
): Promise<Array<{ period: string; scans_count: number; resources_scanned: number }>> {
  const results: Array<{ period: string; scans_count: number; resources_scanned: number }> = [];

  for (let i = 0; i < months; i++) {
    const date = new Date();
    date.setMonth(date.getMonth() - i);
    const period = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

    const usage = await getUsageForPeriod(db, licenseId, period);
    results.push({
      period,
      scans_count: usage.scans_count,
      resources_scanned: usage.resources_scanned,
    });
  }

  return results;
}
