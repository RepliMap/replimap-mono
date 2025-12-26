/**
 * License Validation Handler - HOT PATH
 * POST /v1/license/validate
 *
 * This is called on every CLI run, so it must be fast (<50ms target)
 *
 * Security features:
 * - Zod schema validation for all inputs
 * - Optional HMAC signature verification for machine IDs
 * - Timestamp-based replay attack protection
 */

import type { Env } from '../types/env';
import type { ValidateLicenseResponse } from '../types/api';
import {
  PLAN_FEATURES,
  MAX_MACHINE_CHANGES_PER_MONTH,
  DEFAULT_CACHE_HOURS,
  checkCliVersion,
  type PlanType,
} from '../lib/constants';
import { Plan, getFeatureFlags, PLAN_LIMITS } from '../features';
import { Errors, AppError } from '../lib/errors';
import {
  normalizeLicenseKey,
  normalizeMachineId,
  cacheUntilISO,
  isPast,
  isFuture,
  formatDate,
  truncateMachineId,
  nextMonthStartISO,
} from '../lib/license';
import { rateLimit } from '../lib/rate-limiter';
import {
  getLicenseForValidation,
  updateLicenseStatus,
  registerMachine,
  updateMachineLastSeen,
  recordMachineChange,
  logUsage,
  getMonthlyUsageCount,
  getActiveMachines,
} from '../lib/db';
import { validateLicenseRequestSchema, parseRequest } from '../lib/schemas';
import { verifyHmacSignature } from '../lib/security';

/**
 * Handle license validation request
 */
export async function handleValidateLicense(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Rate limiting
  const rateLimitHeaders = await rateLimit(env.CACHE, 'validate', clientIP);

  try {
    // Parse request body
    let rawBody: unknown;
    try {
      rawBody = await request.json();
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate with Zod schema (comprehensive input validation)
    const parseResult = parseRequest(validateLicenseRequestSchema, rawBody);
    if (!parseResult.success) {
      throw Errors.invalidRequest(parseResult.error);
    }

    const body = parseResult.data;
    const licenseKey = normalizeLicenseKey(body.license_key);
    const machineId = normalizeMachineId(body.machine_id);

    // Verify machine signature if MACHINE_SIGNATURE_SECRET is configured
    // This prevents machine ID forgery
    if (env.MACHINE_SIGNATURE_SECRET && body.machine_signature) {
      // Signature should be HMAC-SHA256(machine_id + timestamp, secret)
      const signaturePayload = body.timestamp
        ? `${machineId}:${body.timestamp}`
        : machineId;

      const isValid = await verifyHmacSignature(
        signaturePayload,
        body.machine_signature,
        env.MACHINE_SIGNATURE_SECRET
      );

      if (!isValid) {
        throw Errors.invalidRequest('Invalid machine signature');
      }
    } else if (env.MACHINE_SIGNATURE_SECRET && !body.machine_signature) {
      // If secret is configured but signature not provided, warn but allow
      // This enables gradual migration - old CLIs work, but log a warning
      console.warn(`[SECURITY] Machine validation without signature from ${truncateMachineId(machineId)}`);
    }

    // Get license with all related data in a single query
    const license = await getLicenseForValidation(env.DB, licenseKey, machineId);

    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    // Check license status and expiry
    await checkLicenseStatus(env.DB, license);

    // Handle machine binding
    await handleMachineBinding(
      env.DB,
      license.license_id,
      machineId,
      license.machine_is_active,
      license.active_machines,
      license.monthly_changes,
      features.machines
    );

    // Log usage (non-blocking)
    logUsage(env.DB, {
      licenseId: license.license_id,
      machineId,
      action: 'validate',
      metadata: { cli_version: body.cli_version },
    }).catch(console.error);

    // Get scan count for this month
    const scansThisMonth = await getMonthlyUsageCount(env.DB, license.license_id, 'scan');

    // Check CLI version compatibility
    const cliVersionCheck = checkCliVersion(body.cli_version);

    // Get new feature flags and limits
    const planEnum = license.plan as Plan;
    const featureFlags = getFeatureFlags(planEnum);
    const newLimits = PLAN_LIMITS[planEnum] || PLAN_LIMITS[Plan.FREE];

    // Build success response
    const response: ValidateLicenseResponse = {
      valid: true,
      plan: license.plan,
      status: license.status,
      features: {
        resources_per_scan: features.resources_per_scan,
        scans_per_month: features.scans_per_month,
        aws_accounts: features.aws_accounts,
        machines: features.machines,
        export_formats: features.export_formats,
      },
      usage: {
        scans_this_month: scansThisMonth,
        machines_active: license.machine_is_active !== null
          ? license.active_machines
          : license.active_machines + 1, // Include this new machine
        machines_limit: features.machines,
        aws_accounts_active: license.active_aws_accounts,
        aws_accounts_limit: features.aws_accounts,
      },
      expires_at: license.current_period_end,
      cache_until: calculateCacheUntil(license.status, license.current_period_end),
      cli_version: cliVersionCheck,
      // NEW: Include feature flags for new features
      new_features: featureFlags,
      // NEW: Include extended limits
      limits: {
        audit_fix_count: newLimits.audit_fix_count,
        snapshot_count: newLimits.snapshot_count,
        snapshot_diff_count: newLimits.snapshot_diff_count,
        drift_count: newLimits.drift_count,
        deps_count: newLimits.deps_count,
        cost_count: newLimits.cost_count,
        clone_preview_lines: newLimits.clone_preview_lines,
        audit_visible_findings: newLimits.audit_visible_findings,
      },
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
 * Check license status and update if expired
 */
async function checkLicenseStatus(
  db: D1Database,
  license: {
    license_id: string;
    status: string;
    current_period_end: string | null;
  }
): Promise<void> {
  // Check if expired
  if (license.status === 'expired') {
    throw Errors.licenseExpired(formatDate(license.current_period_end ?? 'Unknown'));
  }

  // Check if revoked
  if (license.status === 'revoked') {
    throw Errors.licenseRevoked();
  }

  // Check if past due
  if (license.status === 'past_due') {
    throw Errors.licensePastDue();
  }

  // Check if canceled but still valid
  if (license.status === 'canceled') {
    if (license.current_period_end && isFuture(license.current_period_end)) {
      // Still valid until period end - allow but log
      return;
    } else {
      // Period ended - update status and reject
      await updateLicenseStatus(db, license.license_id, 'expired');
      throw Errors.licenseExpired(formatDate(license.current_period_end ?? 'Unknown'));
    }
  }

  // Check if active but period has ended
  if (license.status === 'active' && license.current_period_end && isPast(license.current_period_end)) {
    // Grace period: allow 7 days after period end before marking expired
    const periodEnd = new Date(license.current_period_end);
    const gracePeriodEnd = new Date(periodEnd);
    gracePeriodEnd.setDate(gracePeriodEnd.getDate() + 7);

    if (new Date() > gracePeriodEnd) {
      await updateLicenseStatus(db, license.license_id, 'expired');
      throw Errors.licenseExpired(formatDate(license.current_period_end));
    }
    // Within grace period - allow
  }
}

/**
 * Handle machine binding logic
 */
async function handleMachineBinding(
  db: D1Database,
  licenseId: string,
  machineId: string,
  machineIsActive: number | null,
  activeMachines: number,
  monthlyChanges: number,
  machineLimit: number
): Promise<void> {
  // Case 1: Machine already registered and active
  if (machineIsActive === 1) {
    // Just update last_seen
    await updateMachineLastSeen(db, licenseId, machineId);
    return;
  }

  // Case 2: Machine was registered but deactivated
  if (machineIsActive === 0) {
    // This would be a re-activation - counts as a change
    if (monthlyChanges >= MAX_MACHINE_CHANGES_PER_MONTH) {
      throw Errors.machineChangeLimitExceeded(nextMonthStartISO());
    }

    // Re-activate (update is_active = 1 and record change)
    await db.prepare(`
      UPDATE license_machines SET is_active = 1, last_seen_at = datetime('now')
      WHERE license_id = ? AND machine_id = ?
    `).bind(licenseId, machineId).run();

    await recordMachineChange(db, licenseId, machineId);
    return;
  }

  // Case 3: New machine - check limits
  if (activeMachines >= machineLimit) {
    // Get list of active machines for error message
    const machines = await getActiveMachines(db, licenseId);
    const truncatedIds = machines.map((m) => truncateMachineId(m.machine_id));
    throw Errors.machineLimitExceeded(truncatedIds, machineLimit);
  }

  // Case 4: Check monthly change limit
  if (monthlyChanges >= MAX_MACHINE_CHANGES_PER_MONTH) {
    throw Errors.machineChangeLimitExceeded(nextMonthStartISO());
  }

  // Register new machine
  await registerMachine(db, licenseId, machineId);
  await recordMachineChange(db, licenseId, machineId);
}

/**
 * Calculate cache_until timestamp
 */
function calculateCacheUntil(status: string, periodEnd: string | null): string {
  // Default: 24 hours cache
  let cacheHours = DEFAULT_CACHE_HOURS;

  // Shorter cache for non-active statuses
  if (status === 'canceled' || status === 'past_due') {
    cacheHours = 4;
  }

  // Don't cache past period end
  if (periodEnd) {
    const periodEndDate = new Date(periodEnd);
    const cacheDate = new Date();
    cacheDate.setHours(cacheDate.getHours() + cacheHours);

    if (cacheDate > periodEndDate) {
      return periodEnd;
    }
  }

  return cacheUntilISO(cacheHours);
}
