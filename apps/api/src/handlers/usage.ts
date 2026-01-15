/**
 * Usage Tracking Handlers
 * POST /v1/usage/sync
 * POST /v1/usage/track - Track feature usage events (NEW)
 * GET /v1/usage/{license_key}
 * GET /v1/usage/{license_key}/history
 * POST /v1/usage/check-quota
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey, nowISO, generateId } from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import { Plan, PLAN_LIMITS } from '../features';
import { rateLimit } from '../lib/rate-limiter';
import {
  createDb,
  getLicenseByKey,
  getMonthlyUsageCount,
  recordDailyUsage,
  getDailyUsageCount,
  type DrizzleDb,
} from '../lib/db';
import {
  normalizeEventType,
  isDeprecatedEvent,
  getEventDeprecationWarning,
} from '../utils/event-compat';
import {
  trackEventRequestSchema,
  syncUsageRequestSchema,
  checkQuotaRequestSchema,
  parseRequest,
} from '../lib/schemas';
import { sql } from 'drizzle-orm';

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

// CheckQuotaRequest is now defined via Zod schema in lib/schemas.ts

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

// =============================================================================
// NEW: Event Tracking Types
// =============================================================================

// Event types and validation are now defined via Zod schema in lib/schemas.ts

interface TrackEventResponse {
  success: boolean;
  event_id: string;
  remaining?: number | null;
  deprecation_warning?: string;
  mapped_to?: string;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Sync usage data from CLI
 * POST /v1/usage/sync
 *
 * Input validation includes:
 * - License key and machine ID format validation
 * - Bounded usage counts (scans_count, resources_scanned, terraform_generations)
 * - Period format validation (YYYY-MM)
 */
export async function handleSyncUsage(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate with Zod schema (includes bounds checking)
    const parseResult = parseRequest(syncUsageRequestSchema, rawBody);
    if (!parseResult.success) {
      throw Errors.invalidRequest(parseResult.error);
    }

    const body = parseResult.data;
    const licenseKey = normalizeLicenseKey(body.license_key);

    // Get license
    const license = await getLicenseByKey(db, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Determine period
    const period = body.period || getCurrentPeriod();

    // Check idempotency
    if (body.idempotency_key) {
      const exists = await checkIdempotencyKey(db, body.idempotency_key);
      if (exists) {
        // Return current usage without updating
        const currentUsage = await getUsageForPeriod(db, license.id, period);
        const plan = license.plan as PlanType;
        const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

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
    await recordUsage(db, license.id, body.machine_id, period, body.usage, body.idempotency_key);

    // Get updated usage
    const currentUsage = await getUsageForPeriod(db, license.id, period);
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

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
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get period from query param
    const url = new URL(request.url);
    const period = url.searchParams.get('period') || getCurrentPeriod();

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Get usage
    const usage = await getUsageForPeriod(db, license.id, period);
    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

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
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get months from query param
    const url = new URL(request.url);
    const months = Math.min(12, Math.max(1, parseInt(url.searchParams.get('months') || '6', 10)));

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Get history
    const history = await getUsageHistory(db, license.id, months);

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
 *
 * Input validation includes:
 * - License key format validation
 * - Operation enum validation (scans | resources)
 * - Bounded amount (1-10,000)
 */
export async function handleCheckQuota(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate with Zod schema
    const parseResult = parseRequest(checkQuotaRequestSchema, rawBody);
    if (!parseResult.success) {
      throw Errors.invalidRequest(parseResult.error);
    }

    const body = parseResult.data;
    const licenseKey = normalizeLicenseKey(body.license_key);
    const amount = body.amount;

    // Get license
    const license = await getLicenseByKey(db, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

    let current = 0;
    let limit: number | null = null;
    let unlimited = false;

    if (body.operation === 'scans') {
      current = await getMonthlyUsageCount(db, license.id, 'scan');
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

async function checkIdempotencyKey(db: DrizzleDb, key: string): Promise<boolean> {
  const result = await db.get<{ exists: number }>(sql`
    SELECT 1 as exists FROM usage_idempotency WHERE idempotency_key = ${key}
  `);
  return result !== null;
}

async function recordUsage(
  db: DrizzleDb,
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
    await db.run(sql`
      INSERT INTO usage_logs (id, license_id, machine_id, action, resources_count, metadata, created_at)
      VALUES (${id}, ${licenseId}, ${machineId}, 'scan', ${usage.resources_scanned || 0}, ${JSON.stringify({ period, scans_count: usage.scans_count })}, ${now})
    `);
  }

  // Record idempotency key if provided
  if (idempotencyKey) {
    await db.run(sql`
      INSERT OR IGNORE INTO usage_idempotency (idempotency_key, license_id, created_at)
      VALUES (${idempotencyKey}, ${licenseId}, ${now})
    `);
  }
}

async function getUsageForPeriod(
  db: DrizzleDb,
  licenseId: string,
  period: string
): Promise<UsageData> {
  // Parse period to get start and end dates
  const [year, month] = period.split('-').map(Number);
  const startDate = new Date(year, month - 1, 1);
  const endDate = new Date(year, month, 1);

  const result = await db.get<{ scans_count: number; resources_scanned: number }>(sql`
    SELECT
      COUNT(CASE WHEN action = 'scan' THEN 1 END) as scans_count,
      COALESCE(SUM(resources_count), 0) as resources_scanned
    FROM usage_logs
    WHERE license_id = ${licenseId}
    AND created_at >= ${startDate.toISOString()}
    AND created_at < ${endDate.toISOString()}
  `);

  return {
    scans_count: result?.scans_count || 0,
    resources_scanned: result?.resources_scanned || 0,
    terraform_generations: 0, // Could be tracked separately
  };
}

async function getUsageHistory(
  db: DrizzleDb,
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

// =============================================================================
// NEW: Event Tracking Handler
// =============================================================================

/**
 * Track feature usage event
 * POST /v1/usage/track
 *
 * Input validation includes:
 * - License key format validation
 * - Event type validation against allowed types
 * - Bounded resource_count (0-100,000)
 * - Bounded duration_ms (0-86,400,000 = 24 hours)
 * - Metadata size limit (4KB)
 */
export async function handleTrackEvent(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const db = createDb(env.DB);
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate with Zod schema (includes bounds checking)
    const parseResult = parseRequest(trackEventRequestSchema, rawBody);
    if (!parseResult.success) {
      throw Errors.invalidRequest(parseResult.error);
    }

    const body = parseResult.data;
    const licenseKey = normalizeLicenseKey(body.license_key);

    // Get license
    const license = await getLicenseByKey(db, licenseKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Handle deprecated event types (blast → deps)
    const originalEventType = body.event_type;
    const wasDeprecated = isDeprecatedEvent(body.event_type);
    const eventType = normalizeEventType(body.event_type);

    if (wasDeprecated) {
      console.log(`[COMPAT] Mapped deprecated event: ${originalEventType} → ${eventType}`);
    }

    // Check usage limits
    const plan = license.plan as Plan;
    const limitCheck = await checkEventLimit(db, license.id, plan, eventType);

    if (!limitCheck.allowed) {
      return new Response(
        JSON.stringify({
          error: 'Usage limit exceeded',
          limit: limitCheck.limit,
          used: limitCheck.used,
          reset_at: limitCheck.reset_at,
          upgrade_url: 'https://replimap.dev/pricing',
        }),
        {
          status: 429,
          headers: { 'Content-Type': 'application/json', ...rateLimitHeaders },
        }
      );
    }

    // Record event
    const eventId = generateId();
    const now = nowISO();

    await db.run(sql`
      INSERT INTO usage_events (
        id, license_id, event_type, region, vpc_id,
        resource_count, duration_ms, metadata, original_event_type, created_at
      )
      VALUES (${eventId}, ${license.id}, ${eventType}, ${body.region || null}, ${body.vpc_id || null}, ${body.resource_count || null}, ${body.duration_ms || null}, ${body.metadata ? JSON.stringify(body.metadata) : null}, ${wasDeprecated ? originalEventType : null}, ${now})
    `);

    // ─────────────────────────────────────────────────────────────────────────
    // Daily Aggregation (for efficient counting)
    // This upserts into usage_daily to avoid 1.8M rows/year in usage_events
    // ─────────────────────────────────────────────────────────────────────────
    await recordDailyUsage(db, license.id, eventType, body.resource_count || 0);

    // Track feature-specific data (merge region from body into metadata)
    if (eventType === 'snapshot_save' && body.metadata?.snapshot_name) {
      await trackSnapshot(db, license.id, { ...body.metadata, region: body.region });
    } else if (eventType === 'audit_fix' && body.metadata) {
      await trackRemediation(db, license.id, { ...body.metadata, region: body.region });
    }

    // Build response
    const response: TrackEventResponse = {
      success: true,
      event_id: eventId,
      remaining: limitCheck.remaining,
    };

    if (wasDeprecated) {
      response.deprecation_warning = getEventDeprecationWarning(originalEventType);
      response.mapped_to = eventType;
    }

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

// =============================================================================
// NEW: Feature-Specific Tracking Helpers
// =============================================================================

// ─────────────────────────────────────────────────────────────────────────
// UNLIMITED OPERATIONS - These should NEVER consume quota
// Read-only operations and cleanup operations are always free
// ─────────────────────────────────────────────────────────────────────────
const UNLIMITED_OPERATIONS = new Set([
  // Read-only operations
  'snapshot_list',
  'snapshot_get',
  'license_check',
  'license_status',
  'quota_check',
  'help',
  'version',

  // Cleanup operations (user doing the right thing)
  'snapshot_delete',
]);

async function checkEventLimit(
  db: DrizzleDb,
  licenseId: string,
  plan: Plan,
  eventType: string
): Promise<{
  allowed: boolean;
  limit: number;
  used: number;
  remaining: number | null;
  reset_at: string;
}> {
  // ─────────────────────────────────────────────────────────────────────────
  // Check if this is an unlimited operation (read-only or cleanup)
  // ─────────────────────────────────────────────────────────────────────────
  if (UNLIMITED_OPERATIONS.has(eventType)) {
    return {
      allowed: true,
      limit: -1,
      used: 0,
      remaining: null,
      reset_at: '',
    };
  }

  const limits = PLAN_LIMITS[plan] || PLAN_LIMITS[Plan.COMMUNITY];

  // ─────────────────────────────────────────────────────────────────────────
  // METERED OPERATIONS - These consume quota
  // ─────────────────────────────────────────────────────────────────────────
  const limitKeyMap: Record<string, string> = {
    audit_fix: 'audit_fix_count',
    snapshot_save: 'snapshot_count',
    snapshot_diff: 'snapshot_diff_count',
    deps: 'deps_count',
    deps_explore: 'deps_count',
    deps_export: 'deps_count',
    graph_full: 'graph_count',
    graph_security: 'graph_count',
    drift: 'drift_count',
    cost: 'cost_count',
    scan: 'scan_count',
    rightsizer_analyze: 'rightsizer_count',
  };

  const limitKey = limitKeyMap[eventType] || `${eventType}_count`;
  const limit = limits[limitKey] ?? -1;

  // Unlimited
  if (limit === -1) {
    return {
      allowed: true,
      limit: -1,
      used: 0,
      remaining: null,
      reset_at: '',
    };
  }

  // Disabled (0)
  if (limit === 0) {
    return {
      allowed: false,
      limit: 0,
      used: 0,
      remaining: 0,
      reset_at: getEndOfMonth().toISOString(),
    };
  }

  // Count current period usage using efficient daily aggregation
  // This queries usage_daily (50k rows/year) instead of usage_events (1.8M rows/year)
  const used = await getDailyUsageCount(db, licenseId, eventType);
  const remaining = Math.max(0, limit - used);

  return {
    allowed: used < limit,
    limit,
    used,
    remaining,
    reset_at: getEndOfMonth().toISOString(),
  };
}

async function trackSnapshot(
  db: DrizzleDb,
  licenseId: string,
  metadata: Record<string, unknown>
): Promise<void> {
  await db.run(sql`
    INSERT INTO snapshots (id, license_id, name, region, vpc_id, resource_count, profile, replimap_version)
    VALUES (${generateId()}, ${licenseId}, ${metadata.snapshot_name as string}, ${metadata.region as string}, ${(metadata.vpc_id as string) || null}, ${(metadata.resource_count as number) || 0}, ${(metadata.profile as string) || null}, ${(metadata.version as string) || null})
  `);
}

async function trackRemediation(
  db: DrizzleDb,
  licenseId: string,
  metadata: Record<string, unknown>
): Promise<void> {
  await db.run(sql`
    INSERT INTO remediations (id, license_id, audit_id, region, total_findings, total_fixable, total_manual, files_generated)
    VALUES (${generateId()}, ${licenseId}, ${(metadata.audit_id as string) || null}, ${metadata.region as string}, ${(metadata.total_findings as number) || 0}, ${(metadata.total_fixable as number) || 0}, ${(metadata.total_manual as number) || 0}, ${(metadata.files_generated as number) || 0})
  `);
}

function getEndOfMonth(): Date {
  const date = new Date();
  date.setMonth(date.getMonth() + 1);
  date.setDate(0);
  date.setHours(23, 59, 59, 999);
  return date;
}
