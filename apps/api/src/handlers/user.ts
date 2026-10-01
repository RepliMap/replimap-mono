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
  maskEmail,
} from '../lib/license';
import { sendLicenseKeyEmail } from '../lib/email';
import {
  PLAN_FEATURES,
  MAX_MACHINE_CHANGES_PER_MONTH,
  type PlanType,
} from '../lib/constants';
import { OFFLINE_GRACE_DAYS, type Plan } from '../features';
import { rateLimit } from '../lib/rate-limiter';
import { createDb, getLicenseByKey } from '../lib/db';
import { sql } from 'drizzle-orm';

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
    /**
     * Offline grace period in days — authoritative per-plan value from
     * OFFLINE_GRACE_DAYS (features.ts). Server-issued so the frontend never
     * derives entitlement values itself. Fails closed to 0 (must be online)
     * for unknown plan values.
     */
    offline_grace_days: number;
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
  /**
   * Full machine id. Owner-scoped: this endpoint only ever returns machines
   * of the license whose key was presented, and the deactivate flow needs the
   * full id (it filters on license_id AND machine_id, so the id alone can
   * never touch another license's device).
   */
  machine_id: string;
  machine_id_truncated: string;
  machine_name: string | null;
  is_active: boolean;
  first_seen_at: string;
  last_seen_at: string;
  /** Migration 010 metadata — drives the dashboard device-type badges. */
  fingerprint_type: string;
  ci_provider: string | null;
  ci_repo: string | null;
  container_type: string | null;
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
  /**
   * Present when sent=false — machine-readable reason a caller/UI can branch
   * on (e.g. show a "try again later" vs. a generic message). Additive field:
   * existing consumers reading only `sent`/`message` are unaffected.
   */
  reason?: string;
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
  const db = createDb(env.DB);

  try {
    const url = new URL(request.url);
    const licenseKey = url.searchParams.get('license_key');

    if (!licenseKey) {
      throw Errors.invalidRequest('Missing license_key query parameter');
    }

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license with counts
    const result = await db.get<{
      license_key: string;
      plan: string;
      status: string;
      current_period_start: string | null;
      current_period_end: string | null;
      stripe_subscription_id: string | null;
      created_at: string;
      active_machines: number;
    }>(sql`
      SELECT
        l.license_key,
        l.plan,
        l.status,
        l.current_period_start,
        l.current_period_end,
        l.stripe_subscription_id,
        l.created_at,
        (SELECT COUNT(*) FROM license_machines lm WHERE lm.license_id = l.id AND lm.is_active = 1) as active_machines
      FROM licenses l
      WHERE l.license_key = ${normalizedKey}
    `);

    if (!result) {
      throw Errors.licenseNotFound();
    }

    const plan = result.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

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
        offline_grace_days: OFFLINE_GRACE_DAYS[plan as unknown as Plan] ?? 0,
      },
      usage: {
        scans_this_month: 0, // frozen contract key: the server no longer records scans
        machines_active: result.active_machines,
        machines_limit: features.machines,
        aws_accounts_active: 0, // frozen contract key: the server no longer records AWS accounts
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
  const db = createDb(env.DB);

  try {
    const url = new URL(request.url);
    const licenseKey = url.searchParams.get('license_key');

    if (!licenseKey) {
      throw Errors.invalidRequest('Missing license_key query parameter');
    }

    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license
    const license = await getLicenseByKey(db, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

    // Get machines — scoped strictly to the presented key's license
    const machinesResult = await db.all<{
      machine_id: string;
      machine_name: string | null;
      is_active: number;
      first_seen_at: string;
      last_seen_at: string;
      fingerprint_type: string | null;
      ci_provider: string | null;
      ci_repo: string | null;
      container_type: string | null;
    }>(sql`
      SELECT machine_id, machine_name, is_active, first_seen_at, last_seen_at,
             fingerprint_type, ci_provider, ci_repo, container_type
      FROM license_machines
      WHERE license_id = ${license.id}
      ORDER BY last_seen_at DESC
    `);

    // Get machine changes this month
    const changesResult = await db.get<{ count: number }>(sql`
      SELECT COUNT(*) as count
      FROM machine_changes
      WHERE license_id = ${license.id}
      AND changed_at >= datetime('now', 'start of month')
    `);

    const machines: MachineInfo[] = machinesResult.map((m) => ({
      machine_id: m.machine_id,
      machine_id_truncated: truncateMachineId(m.machine_id),
      machine_name: m.machine_name,
      is_active: m.is_active === 1,
      first_seen_at: m.first_seen_at,
      last_seen_at: m.last_seen_at,
      // Rows predating migration 010 have NULL — default to plain machine.
      fingerprint_type: m.fingerprint_type ?? 'machine',
      ci_provider: m.ci_provider,
      ci_repo: m.ci_repo,
      container_type: m.container_type,
    }));

    const response: GetMachinesResponse = {
      machines,
      active_count: machines.filter((m) => m.is_active).length,
      limit: features.machines,
      changes_this_month: changesResult?.count ?? 0,
      changes_limit: MAX_MACHINE_CHANGES_PER_MONTH,
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
 * Sends via Resend (lib/email.ts) when RESEND_API_KEY/EMAIL_FROM are
 * configured; degrades honestly to {sent:false, reason:'email_not_configured'}
 * otherwise. Always returns a generic sent:true for a nonexistent account
 * (anti email-enumeration) — see the comment at the found/not-found branch
 * below before changing that behavior.
 */
export async function handleResendKey(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Stricter rate limit for resend (prevent abuse)
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);
  const db = createDb(env.DB);

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

    // Find user and their licenses (Note: uses 'user' table with new schema)
    const result = await db.all<{
      license_key: string;
      plan: string;
      status: string;
    }>(sql`
      SELECT l.license_key, l.plan, l.status
      FROM user u
      JOIN licenses l ON u.id = l.user_id
      WHERE u.email = ${email}
      AND l.status IN ('active', 'canceled', 'past_due')
      ORDER BY l.created_at DESC
      LIMIT 5
    `);

    // Anti-enumeration: only attempt to send (and only vary the response) when
    // a matching account was found. A request for a nonexistent email always
    // gets the same generic `sent:true` response below — do not "fix" that
    // branch to reflect send status; there is nothing to send, and returning
    // sent:false there would leak account existence.
    let response: ResendKeyResponse;

    if (result.length > 0) {
      const emailResult = await sendLicenseKeyEmail(env, {
        to: email,
        licenses: result.map((r) => ({ plan: r.plan, licenseKey: r.license_key })),
      });

      console.log(
        `License resend requested for ${maskEmail(email)}, found ${result.length} ` +
          `license(s), sent=${emailResult.sent}` +
          (emailResult.reason ? ` reason=${emailResult.reason}` : '')
      );

      response = emailResult.sent
        ? {
            sent: true,
            message: 'If an account exists with this email, license keys have been sent.',
          }
        : {
            sent: false,
            message:
              'We found your account but could not deliver the email right now. Please try again shortly.',
            reason: emailResult.reason,
          };
    } else {
      response = {
        sent: true,
        message: 'If an account exists with this email, license keys have been sent.',
      };
    }

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
