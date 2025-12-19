/**
 * License Activation Handler
 * POST /v1/license/activate
 *
 * First-time activation of a license on a new machine
 */

import type { Env } from '../types/env';
import type {
  ActivateLicenseRequest,
  ActivateLicenseResponse,
} from '../types/api';
import { PLAN_FEATURES, MAX_MACHINE_CHANGES_PER_MONTH, type PlanType } from '../lib/constants';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  validateMachineId,
  normalizeLicenseKey,
  normalizeMachineId,
  truncateMachineId,
  nextMonthStartISO,
  formatDate,
} from '../lib/license';
import { rateLimit } from '../lib/rate-limiter';
import {
  getLicenseForValidation,
  registerMachine,
  recordMachineChange,
  logUsage,
  getActiveMachines,
} from '../lib/db';

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
    if (!body.machine_id) {
      throw Errors.invalidRequest('Missing machine_id');
    }

    // Validate formats
    validateLicenseKey(body.license_key);
    validateMachineId(body.machine_id);

    const licenseKey = normalizeLicenseKey(body.license_key);
    const machineId = normalizeMachineId(body.machine_id);

    // Get license with all related data
    const license = await getLicenseForValidation(env.DB, licenseKey, machineId);

    if (!license) {
      throw Errors.licenseNotFound();
    }

    const plan = license.plan as PlanType;
    const features = PLAN_FEATURES[plan] ?? PLAN_FEATURES.free;

    // Check license status
    if (license.status === 'expired' || license.status === 'revoked') {
      throw Errors.licenseExpired(formatDate(license.current_period_end ?? 'Unknown'));
    }
    if (license.status === 'past_due') {
      throw Errors.licensePastDue();
    }

    // Check if already activated on this machine
    if (license.machine_is_active === 1) {
      // Already activated - return success
      const response: ActivateLicenseResponse = {
        activated: true,
        plan: license.plan,
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
      const machines = await getActiveMachines(env.DB, license.license_id);
      const truncatedIds = machines.map((m) => truncateMachineId(m.machine_id));
      throw Errors.machineLimitExceeded(truncatedIds, features.machines);
    }

    // Check monthly change limit
    if (license.monthly_changes >= MAX_MACHINE_CHANGES_PER_MONTH) {
      throw Errors.machineChangeLimitExceeded(nextMonthStartISO());
    }

    // Register the machine
    await registerMachine(env.DB, license.license_id, machineId, body.machine_name);
    await recordMachineChange(env.DB, license.license_id, machineId);

    // Log usage
    await logUsage(env.DB, {
      licenseId: license.license_id,
      machineId,
      action: 'activate',
      metadata: { machine_name: body.machine_name },
    });

    const response: ActivateLicenseResponse = {
      activated: true,
      plan: license.plan,
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
