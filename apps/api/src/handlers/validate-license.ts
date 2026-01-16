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
  createDb,
  getLicenseForValidation,
  updateLicenseStatus,
  registerMachine,
  updateMachineLastSeen,
  recordMachineChange,
  logUsage,
  getMonthlyUsageCount,
  getActiveMachines,
  getActiveDeviceCount,
  getNewDeviceCount,
  getActiveCIDeviceCount,
  type DrizzleDb,
} from '../lib/db';
import { validateLicenseRequestSchema, parseRequest } from '../lib/schemas';
import {
  verifyHmacSignature,
  checkVersionHeader,
  checkDeviceAbuse,
  isCIEnvironment,
  CI_DEVICE_LIMITS,
  createLeaseToken,
} from '../lib/security';
import { sql } from 'drizzle-orm';

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

  // Create Drizzle client
  const db = createDb(env.DB);

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

    // Check version header for warnings (soft - doesn't reject)
    const cliVersionHeader = request.headers.get('X-Replimap-Version');
    const versionWarning = checkVersionHeader(cliVersionHeader);

    // Detect if this is a CI/CD environment
    const isCI = isCIEnvironment(machineId, body.is_ci);

    // Get license with all related data in a single query
    const license = await getLicenseForValidation(db, licenseKey, machineId);

    if (!license) {
      // Random delay to prevent timing attacks on license discovery
      await new Promise((r) => setTimeout(r, 50 + Math.random() * 100));
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

    // ─────────────────────────────────────────────────────────────────────────
    // Device Abuse Detection (check ACTIVE devices, not lifetime total)
    // ─────────────────────────────────────────────────────────────────────────
    const [activeDeviceCount, newDevicesToday] = await Promise.all([
      getActiveDeviceCount(db, license.license_id, 7, true),  // Last 7 days, exclude CI
      getNewDeviceCount(db, license.license_id, 24, true),    // Last 24 hours, exclude CI
    ]);

    const abuseCheck = checkDeviceAbuse(activeDeviceCount, newDevicesToday);

    if (abuseCheck.isAbuse) {
      console.warn(`[ABUSE] License ${licenseKey.slice(0, 12)}... - ${abuseCheck.reason}`);
      throw new AppError(
        'LICENSE_ABUSE_DETECTED',
        abuseCheck.warning || 'This license appears to be shared across too many devices.',
        403,
        {
          action: 'If this is a mistake, contact support@replimap.dev',
          guidance: 'For CI/CD: Set REPLIMAP_MACHINE_ID env var to persist identity across runs',
        }
      );
    }

    // ─────────────────────────────────────────────────────────────────────────
    // CI/CD Device Limit Check
    // ─────────────────────────────────────────────────────────────────────────
    let ciWarning: string | undefined;
    if (isCI) {
      const activeCIDevices = await getActiveCIDeviceCount(db, license.license_id, 30);
      const ciLimit = CI_DEVICE_LIMITS[plan] ?? CI_DEVICE_LIMITS.community;

      if (ciLimit !== -1 && activeCIDevices >= ciLimit) {
        throw new AppError(
          'CI_DEVICE_LIMIT',
          `CI machine limit reached (${activeCIDevices}/${ciLimit}).`,
          403,
          {
            action: 'Set REPLIMAP_MACHINE_ID env var to reuse identity across runs.',
            limit: ciLimit,
            guidance: 'Tip: Use a stable REPLIMAP_MACHINE_ID to avoid consuming new device slots.',
          }
        );
      }

      // Add warning about CI environment
      ciWarning = 'CI environment detected. Set REPLIMAP_MACHINE_ID for consistent identity.';
    }

    // Check license status and expiry
    await checkLicenseStatus(db, license);

    // Handle machine binding (with throttled last_seen updates)
    await handleMachineBinding(
      db,
      license.license_id,
      machineId,
      license.machine_is_active,
      license.machine_last_seen,  // Used for throttled updates
      license.active_machines,
      license.monthly_changes,
      features.machines
    );

    // Log usage (non-blocking)
    logUsage(db, {
      licenseId: license.license_id,
      machineId,
      action: 'validate',
      metadata: { cli_version: body.cli_version },
    }).catch(console.error);

    // Get scan count for this month
    const scansThisMonth = await getMonthlyUsageCount(db, license.license_id, 'scan');

    // Check CLI version compatibility
    const cliVersionCheck = checkCliVersion(body.cli_version);

    // Get new feature flags and limits
    const planEnum = license.plan as Plan;
    const featureFlags = getFeatureFlags(planEnum);
    const newLimits = PLAN_LIMITS[planEnum] || PLAN_LIMITS[Plan.COMMUNITY];

    // Build success response
    const response: ValidateLicenseResponse & {
      _warning?: { message: string; upgrade_command: string };
      _device_warning?: string;
      _ci_warning?: string;
      lease_token?: string;  // Offline validation token
    } = {
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

    // Add version warning if outdated CLI
    if (versionWarning) {
      response._warning = {
        message: versionWarning.message,
        upgrade_command: versionWarning.upgrade_command,
      };
    }

    // Add device warning (non-abuse but suspicious)
    if (abuseCheck.warning && !abuseCheck.isAbuse) {
      response._device_warning = abuseCheck.warning;
    }

    // Add CI environment warning
    if (ciWarning) {
      response._ci_warning = ciWarning;
    }

    // Generate offline lease token if LEASE_TOKEN_SECRET is configured
    // This allows CLI to cache license validity for offline operation
    if (env.LEASE_TOKEN_SECRET) {
      try {
        const leaseToken = await createLeaseToken(
          {
            key: licenseKey.slice(0, 15) + '...', // Truncate for security
            plan: license.plan,
            mid: machineId.slice(0, 8), // Truncate machine ID
          },
          env.LEASE_TOKEN_SECRET
        );
        response.lease_token = leaseToken;
      } catch (err) {
        // Non-fatal: log and continue without lease token
        console.error('[LEASE] Failed to create lease token:', err);
      }
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

/**
 * Check license status and update if expired
 */
async function checkLicenseStatus(
  db: DrizzleDb,
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
 * Throttle interval for last_seen updates (1 hour in milliseconds)
 * This prevents write amplification on every validation request.
 */
const LAST_SEEN_UPDATE_THROTTLE_MS = 60 * 60 * 1000; // 1 hour

/**
 * Check if we should update last_seen_at based on throttle interval.
 * Returns true if last_seen is null/empty or older than LAST_SEEN_UPDATE_THROTTLE_MS.
 *
 * ROBUSTNESS: Handles edge cases where DB returns empty string, 'null', undefined,
 * or invalid date strings. In all these cases, we update the timestamp.
 */
function shouldUpdateLastSeen(lastSeen: string | null): boolean {
  // Handle falsy values (null, undefined, empty string)
  if (!lastSeen || lastSeen === 'null' || lastSeen.trim() === '') {
    return true;
  }

  try {
    const lastSeenTime = new Date(lastSeen).getTime();

    // Handle Invalid Date (getTime() returns NaN for invalid dates)
    // NaN comparisons always return false, so we need explicit check
    if (isNaN(lastSeenTime)) {
      return true;
    }

    const now = Date.now();
    return (now - lastSeenTime) > LAST_SEEN_UPDATE_THROTTLE_MS;
  } catch {
    // If we can't parse the date, update it
    return true;
  }
}

/**
 * Handle machine binding logic
 *
 * Performance Optimization: Uses throttled writes for last_seen_at to prevent
 * write amplification. Only updates if > 1 hour has passed since last update.
 */
async function handleMachineBinding(
  db: DrizzleDb,
  licenseId: string,
  machineId: string,
  machineIsActive: number | null,
  machineLastSeen: string | null,  // Used for throttled updates
  activeMachines: number,
  monthlyChanges: number,
  machineLimit: number
): Promise<void> {
  // Case 1: Machine already registered and active
  if (machineIsActive === 1) {
    // THROTTLED UPDATE: Only update last_seen if > 1 hour has passed
    // This prevents write amplification (SQLite single-writer bottleneck)
    const shouldUpdate = shouldUpdateLastSeen(machineLastSeen);
    if (shouldUpdate) {
      // Fire-and-forget update to avoid blocking the response
      updateMachineLastSeen(db, licenseId, machineId).catch((err) => {
        console.error('[DB] Failed to update last_seen:', err);
      });
    }
    return;
  }

  // Case 2: Machine was registered but deactivated
  if (machineIsActive === 0) {
    // This would be a re-activation - counts as a change
    if (monthlyChanges >= MAX_MACHINE_CHANGES_PER_MONTH) {
      throw Errors.machineChangeLimitExceeded(nextMonthStartISO());
    }

    // Re-activate using Drizzle
    await db.run(sql`
      UPDATE license_machines SET is_active = 1, last_seen_at = datetime('now')
      WHERE license_id = ${licenseId} AND machine_id = ${machineId}
    `);

    await recordMachineChange(db, licenseId, machineId);
    return;
  }

  // Case 3: New machine - check limits
  if (activeMachines >= machineLimit) {
    // Get list of active machines for error message
    const machines = await getActiveMachines(db, licenseId);
    const truncatedIds = machines.map((m) => truncateMachineId(m.machineId));
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
