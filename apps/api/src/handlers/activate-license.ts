/**
 * License Activation Handler
 * POST /v1/license/activate
 *
 * First-time activation of a license on a new machine.
 * Returns Ed25519 signed license_blob for offline validation.
 */

import type { Env } from '../types/env';
import type {
  ActivateLicenseRequest,
  ActivateLicenseResponse,
} from '../types/api';
import { PLAN_FEATURES, MAX_MACHINE_CHANGES_PER_MONTH, type PlanType } from '../lib/constants';
import { Plan, buildSecureLicenseLimits, getEnabledFeatures } from '../features';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  normalizeLicenseKey,
  normalizeMachineId,
  truncateMachineId,
  nextMonthStartISO,
  formatDate,
} from '../lib/license';
import { rateLimit } from '../lib/rate-limiter';
import {
  createDb,
  getLicenseForValidation,
  registerMachine,
  recordMachineChange,
  logUsage,
  getActiveMachines,
} from '../lib/db';
import { signLicenseBlob, type LicensePayload } from '../lib/ed25519';
import { detectFingerprintType, validateFingerprint } from '../lib/fingerprint';

/**
 * Handle license activation request
 */
export async function handleActivateLicense(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Rate limiting (stricter for activation)
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);

  // Create Drizzle client
  const db = createDb(env.DB);

  try {
    // Parse and validate request body
    let body: ActivateLicenseRequest;
    try {
      body = await request.json() as ActivateLicenseRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }

    // Support both machine_fingerprint (new) and machine_id (legacy)
    const rawFingerprint = body.machine_fingerprint || body.machine_id;
    if (!rawFingerprint) {
      throw Errors.invalidRequest('Missing machine_fingerprint');
    }

    // Validate fingerprint format (32 char lowercase hex)
    if (!validateFingerprint(rawFingerprint.toLowerCase())) {
      throw Errors.invalidRequest('Invalid fingerprint format (expected 32 char hex)');
    }

    // Validate license key format
    validateLicenseKey(body.license_key);

    const licenseKey = normalizeLicenseKey(body.license_key);
    const machineId = normalizeMachineId(rawFingerprint);

    // Detect fingerprint type
    const fpMetadata = detectFingerprintType(
      body.machine_info,
      body.fingerprint_type
    );

    // Get license with all related data
    const license = await getLicenseForValidation(db, licenseKey, machineId);

    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const planEnum = license.plan as Plan;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.community;

    // Check license status
    if (license.status === 'expired' || license.status === 'revoked') {
      throw Errors.licenseExpired(formatDate(license.current_period_end ?? 'Unknown'));
    }
    if (license.status === 'past_due') {
      throw Errors.licensePastDue();
    }

    // Helper to build and sign license blob
    const buildLicenseBlob = async (): Promise<string> => {
      const now = Math.floor(Date.now() / 1000);
      const expSeconds = 24 * 60 * 60; // 24 hours

      const payload: LicensePayload = {
        license_key: licenseKey,
        plan: license.plan,
        status: license.status,
        machine_fingerprint: machineId,
        fingerprint_type: fpMetadata.type,
        limits: buildSecureLicenseLimits(planEnum),
        features: getEnabledFeatures(planEnum),
        iat: now,
        exp: now + expSeconds,
        nbf: now - 60, // 1 minute clock skew tolerance
      };

      return signLicenseBlob(payload, env.ED25519_PRIVATE_KEY);
    };

    // Check if already activated on this machine
    if (license.machine_is_active === 1) {
      // Already activated - return success with license_blob
      const licenseBlob = await buildLicenseBlob();

      const response: ActivateLicenseResponse = {
        activated: true,
        license_blob: licenseBlob,
        plan: license.plan,
        status: license.status,
        machines_used: license.active_machines,
        machines_limit: features.machines,
      };

      return new Response(JSON.stringify(response), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }

    // Check machine limit
    if (license.active_machines >= features.machines) {
      const machines = await getActiveMachines(db, license.license_id);
      const truncatedIds = machines.map((m) => truncateMachineId(m.machineId));
      throw Errors.machineLimitExceeded(truncatedIds, features.machines);
    }

    // Check monthly change limit
    if (license.monthly_changes >= MAX_MACHINE_CHANGES_PER_MONTH) {
      throw Errors.machineChangeLimitExceeded(nextMonthStartISO());
    }

    // Register the machine with fingerprint metadata
    await registerMachine(
      db,
      license.license_id,
      machineId,
      body.machine_name,
      fpMetadata.type,
      {
        ci_provider: fpMetadata.ci_provider,
        ci_repo: fpMetadata.ci_repo,
        container_type: fpMetadata.container_type,
      }
    );
    await recordMachineChange(db, license.license_id, machineId);

    // Log usage
    await logUsage(db, {
      licenseId: license.license_id,
      machineId,
      action: 'activate',
      metadata: {
        machine_name: body.machine_name,
        fingerprint_type: fpMetadata.type,
        cli_version: body.cli_version,
      },
    });

    // Generate license blob
    const licenseBlob = await buildLicenseBlob();

    const response: ActivateLicenseResponse = {
      activated: true,
      license_blob: licenseBlob,
      plan: license.plan,
      status: license.status,
      machines_used: license.active_machines + 1,
      machines_limit: features.machines,
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
