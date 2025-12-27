/**
 * Admin API Handlers
 * Requires X-API-Key header with valid admin API key
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { generateLicenseKey, validateLicenseKey, normalizeLicenseKey } from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import { verifyAdminApiKey as verifyApiKey } from '../lib/security';
import {
  createDb,
  findOrCreateUser,
  createLicense,
  getLicenseByKey,
  updateLicenseStatus,
} from '../lib/db';
import { sql } from 'drizzle-orm';

// ============================================================================
// Admin API Key Verification
// ============================================================================

/**
 * Verify admin API key from X-API-Key header.
 * Uses shared security utility with constant-time comparison.
 */
export function verifyAdminApiKey(request: Request, env: Env): void {
  verifyApiKey(request, env.ADMIN_API_KEY);
}

// ============================================================================
// Request/Response Types
// ============================================================================

interface CreateLicenseRequest {
  customer_email: string;
  plan?: string;
  expires_in_days?: number;
  notes?: string;
}

interface CreateLicenseResponse {
  license_key: string;
  plan: string;
  status: string;
  expires_at: string | null;
  created_at: string;
}

interface RevokeLicenseRequest {
  reason?: string;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Create a new license (admin only)
 * POST /v1/admin/licenses
 */
export async function handleCreateLicense(
  request: Request,
  env: Env
): Promise<Response> {
  try {
    const db = createDb(env.DB);

    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Parse request body
    let body: CreateLicenseRequest;
    try {
      body = await request.json() as CreateLicenseRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate email
    if (!body.customer_email || !isValidEmail(body.customer_email)) {
      throw Errors.invalidRequest('Valid customer_email is required');
    }

    // Validate plan
    const plan = (body.plan || 'free') as PlanType;
    if (!PLAN_FEATURES[plan]) {
      throw Errors.invalidRequest(`Invalid plan. Must be one of: ${Object.keys(PLAN_FEATURES).join(', ')}`);
    }

    // Find or create user
    const user = await findOrCreateUser(db, body.customer_email);

    // Generate license key
    const licenseKey = generateLicenseKey();

    // Calculate expiration
    let currentPeriodEnd: string | undefined;
    if (body.expires_in_days && body.expires_in_days > 0) {
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + body.expires_in_days);
      currentPeriodEnd = expiresAt.toISOString();
    }

    // Create license
    const license = await createLicense(db, {
      userId: user.id,
      licenseKey,
      plan,
      currentPeriodEnd,
    });

    const response: CreateLicenseResponse = {
      license_key: license.licenseKey,
      plan: license.plan,
      status: license.status,
      expires_at: license.currentPeriodEnd,
      created_at: license.createdAt,
    };

    return new Response(JSON.stringify(response), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

/**
 * Revoke a license (admin only)
 * POST /v1/admin/licenses/{license_key}/revoke
 */
export async function handleRevokeLicense(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    const db = createDb(env.DB);

    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Parse request body (optional)
    let body: RevokeLicenseRequest = {};
    try {
      const text = await request.text();
      if (text) {
        body = JSON.parse(text);
      }
    } catch {
      // Ignore - body is optional
    }

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Revoke license
    await updateLicenseStatus(db, license.id, 'revoked');

    return new Response(JSON.stringify({
      revoked: true,
      license_key: normalizedKey,
      reason: body.reason || null,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

/**
 * Get license details (admin only)
 * GET /v1/admin/licenses/{license_key}
 */
export async function handleGetLicense(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    const db = createDb(env.DB);

    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const features = PLAN_FEATURES[license.plan as PlanType] ?? PLAN_FEATURES.free;

    return new Response(JSON.stringify({
      license_key: license.licenseKey,
      plan: license.plan,
      status: license.status,
      features,
      expires_at: license.currentPeriodEnd,
      stripe_subscription_id: license.stripeSubscriptionId,
      created_at: license.createdAt,
      updated_at: license.updatedAt,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

/**
 * Get system stats (admin only) - "God Mode" endpoint
 * GET /v1/admin/stats
 *
 * Provides operational visibility:
 * - User and license counts
 * - Active devices (7d/30d)
 * - Event counts and trends
 * - Database health indicators
 */
export async function handleGetStats(
  request: Request,
  env: Env
): Promise<Response> {
  try {
    const db = createDb(env.DB);

    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Execute all queries in parallel for efficiency
    const [
      userCount,
      licenseCount,
      activeLicenses,
      activeDevices7d,
      activeDevices30d,
      eventsToday,
      eventsThisMonth,
      topEventTypes,
    ] = await Promise.all([
      // Total users
      db.get<{ count: number }>(sql`SELECT COUNT(*) as count FROM user`),

      // Total licenses
      db.get<{ count: number }>(sql`SELECT COUNT(*) as count FROM licenses`),

      // Active licenses (status = 'active')
      db.get<{ count: number }>(sql`SELECT COUNT(*) as count FROM licenses WHERE status = 'active'`),

      // Active devices in last 7 days
      db.get<{ count: number }>(sql`
        SELECT COUNT(*) as count FROM license_machines
        WHERE last_seen_at > datetime('now', '-7 days')
      `),

      // Active devices in last 30 days
      db.get<{ count: number }>(sql`
        SELECT COUNT(*) as count FROM license_machines
        WHERE last_seen_at > datetime('now', '-30 days')
      `),

      // Events today (from usage_daily)
      db.get<{ count: number }>(sql`
        SELECT COALESCE(SUM(count), 0) as count FROM usage_daily
        WHERE date = date('now')
      `),

      // Events this month (from usage_daily)
      db.get<{ count: number }>(sql`
        SELECT COALESCE(SUM(count), 0) as count FROM usage_daily
        WHERE date >= date('now', 'start of month')
      `),

      // Top event types this month
      db.all<{ event_type: string; total: number }>(sql`
        SELECT event_type, SUM(count) as total
        FROM usage_daily
        WHERE date >= date('now', 'start of month')
        GROUP BY event_type
        ORDER BY total DESC
        LIMIT 10
      `),
    ]);

    const stats = {
      timestamp: new Date().toISOString(),
      environment: env.ENVIRONMENT,
      version: env.API_VERSION || 'unknown',
      users: {
        total: userCount?.count ?? 0,
      },
      licenses: {
        total: licenseCount?.count ?? 0,
        active: activeLicenses?.count ?? 0,
      },
      devices: {
        active_7d: activeDevices7d?.count ?? 0,
        active_30d: activeDevices30d?.count ?? 0,
      },
      events: {
        today: eventsToday?.count ?? 0,
        this_month: eventsThisMonth?.count ?? 0,
        top_types: topEventTypes ?? [],
      },
    };

    return new Response(JSON.stringify(stats), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

// ============================================================================
// Helpers
// ============================================================================

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
