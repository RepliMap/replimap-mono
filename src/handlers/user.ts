/**
 * User Self-Service Handlers
 * These endpoints allow users to view their own license info without admin key
 *
 * GET /v1/me/license - Get own license details (via license_key query param)
 * GET /v1/me/machines - Get machines for own license
 * POST /v1/me/resend-key - Resend license key via email
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  normalizeLicenseKey,
  truncateMachineId,
} from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import { rateLimit } from '../lib/rate-limiter';
import { getLicenseByKey, getMonthlyUsageCount } from '../lib/db';

// ============================================================================
// Request/Response Types
// ============================================================================

interface GetLicenseResponse {
  license_key: string;
  plan: string;
  status: string;
  features: {
    resources_per_scan: number;
    scans_per_month: number;
    aws_accounts: number;
    machines: number;
    export_formats: string[];
  };
  usage: {
    scans_this_month: number;
    machines_active: number;
    machines_limit: number;
    aws_accounts_active: number;
    aws_accounts_limit: number;
  };
  subscription: {
    current_period_start: string | null;
    current_period_end: string | null;
    has_payment_method: boolean;
  };
  created_at: string;
}

interface MachineInfo {
  machine_id_truncated: string;
  machine_name: string | null;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
}

interface GetMachinesResponse {
  machines: MachineInfo[];
  active_count: number;
  limit: number;
  changes_this_month: number;
  changes_limit: number;
}

interface ResendKeyRequest {
  email: string;
}

interface ResendKeyResponse {
  sent: boolean;
  message: string;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Get own license details
 * GET /v1/me/license?license_key=RM-XXXX-XXXX-XXXX-XXXX
 */
export async function handleGetOwnLicense(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    const url = new URL(request.url);
    const licenseKey = url.searchParams.get('license_key');

    if (!licenseKey) {
      throw Errors.invalidRequest('Missing license_key query parameter');
    }

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license with counts
    const result = await env.DB.prepare(`
      SELECT
        l.license_key,
        l.plan,
        l.status,
        l.current_period_start,
        l.current_period_end,
        l.stripe_subscription_id,
        l.created_at,
        (SELECT COUNT(*) FROM license_machines lm WHERE lm.license_id = l.id AND lm.is_active = 1) as active_machines,
        (SELECT COUNT(*) FROM license_aws_accounts la WHERE la.license_id = l.id AND la.is_active = 1) as active_aws_accounts
      FROM licenses l
      WHERE l.license_key = ?
    `).bind(normalizedKey).first<{
      license_key: string;
      plan: string;
      status: string;
      current_period_start: string | null;
      current_period_end: string | null;
      stripe_subscription_id: string | null;
      created_at: string;
      active_machines: number;
      active_aws_accounts: number;
    }>();

    if (!result) {
      throw Errors.licenseNotFound();
    }

    const plan = result.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    // Get usage count
    const licenseId = await getLicenseId(env.DB, normalizedKey);
    const scansThisMonth = licenseId
      ? await getMonthlyUsageCount(env.DB, licenseId, 'scan')
      : 0;

    const response: GetLicenseResponse = {
      license_key: result.license_key,
      plan: result.plan,
      status: result.status,
      features: {
        resources_per_scan: features.resources_per_scan,
        scans_per_month: features.scans_per_month,
        aws_accounts: features.aws_accounts,
        machines: features.machines,
        export_formats: features.export_formats,
      },
      usage: {
        scans_this_month: scansThisMonth,
        machines_active: result.active_machines,
        machines_limit: features.machines,
        aws_accounts_active: result.active_aws_accounts,
        aws_accounts_limit: features.aws_accounts,
      },
      subscription: {
        current_period_start: result.current_period_start,
        current_period_end: result.current_period_end,
        has_payment_method: !!result.stripe_subscription_id,
      },
      created_at: result.created_at,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...rateLimitHeaders,
      },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }
    throw error;
  }
}

/**
 * Get machines for own license
 * GET /v1/me/machines?license_key=RM-XXXX-XXXX-XXXX-XXXX
 */
export async function handleGetOwnMachines(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    const url = new URL(request.url);
    const licenseKey = url.searchParams.get('license_key');

    if (!licenseKey) {
      throw Errors.invalidRequest('Missing license_key query parameter');
    }

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    // Get machines
    const machinesResult = await env.DB.prepare(`
      SELECT machine_id, machine_name, is_active, first_seen_at, last_seen_at
      FROM license_machines
      WHERE license_id = ?
      ORDER BY last_seen_at DESC
    `).bind(license.id).all<{
      machine_id: string;
      machine_name: string | null;
      is_active: number;
      first_seen_at: string;
      last_seen_at: string;
    }>();

    // Get machine changes this month
    const changesResult = await env.DB.prepare(`
      SELECT COUNT(*) as count
      FROM machine_changes
      WHERE license_id = ?
      AND changed_at >= datetime('now', 'start of month')
    `).bind(license.id).first<{ count: number }>();

    const machines: MachineInfo[] = machinesResult.results.map((m) => ({
      machine_id_truncated: truncateMachineId(m.machine_id),
      machine_name: m.machine_name,
      is_active: m.is_active === 1,
      first_seen_at: m.first_seen_at,
      last_seen_at: m.last_seen_at,
    }));

    const response: GetMachinesResponse = {
      machines,
      active_count: machines.filter((m) => m.is_active).length,
      limit: features.machines,
      changes_this_month: changesResult?.count ?? 0,
      changes_limit: 3,
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...rateLimitHeaders,
      },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }
    throw error;
  }
}

/**
 * Resend license key to email
 * POST /v1/me/resend-key
 *
 * Note: This requires email sending capability (e.g., Resend, SendGrid, etc.)
 * For now, we just verify the email exists and return a success message.
 * In production, integrate with an email provider.
 */
export async function handleResendKey(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Stricter rate limit for resend (prevent abuse)
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);

  try {
    // Parse request body
    let body: ResendKeyRequest;
    try {
      body = await request.json() as ResendKeyRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    if (!body.email) {
      throw Errors.invalidRequest('Missing email');
    }

    // Validate email format
    if (!isValidEmail(body.email)) {
      throw Errors.invalidRequest('Invalid email format');
    }

    const email = body.email.toLowerCase();

    // Find user and their licenses
    const result = await env.DB.prepare(`
      SELECT l.license_key, l.plan, l.status
      FROM users u
      JOIN licenses l ON u.id = l.user_id
      WHERE u.email = ?
      AND l.status IN ('active', 'canceled', 'past_due')
      ORDER BY l.created_at DESC
      LIMIT 5
    `).bind(email).all<{
      license_key: string;
      plan: string;
      status: string;
    }>();

    // Always return success to prevent email enumeration
    // In production, send email only if licenses found
    if (result.results.length > 0) {
      // TODO: Send email with license keys
      // For now, just log (in production, integrate with email provider)
      console.log(`License resend requested for ${email}, found ${result.results.length} license(s)`);

      // Example integration with email API:
      // await sendEmail(env, {
      //   to: email,
      //   subject: 'Your RepliMap License Keys',
      //   body: formatLicenseEmail(result.results),
      // });
    }

    const response: ResendKeyResponse = {
      sent: true,
      message: 'If an account exists with this email, license keys have been sent.',
    };

    return new Response(JSON.stringify(response), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        ...rateLimitHeaders,
      },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
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

async function getLicenseId(db: D1Database, licenseKey: string): Promise<string | null> {
  const result = await db.prepare(`
    SELECT id FROM licenses WHERE license_key = ?
  `).bind(licenseKey).first<{ id: string }>();
  return result?.id ?? null;
}
