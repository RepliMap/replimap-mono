/**
 * License Deactivation Handler
 * POST /v1/license/deactivate
 *
 * Remove a machine from a license
 */

import type { Env } from '../types/env';
import type {
  DeactivateLicenseRequest,
  DeactivateLicenseResponse,
} from '../types/api';
import { Errors, AppError } from '../lib/errors';
import {
  validateLicenseKey,
  validateMachineId,
  normalizeLicenseKey,
  normalizeMachineId,
} from '../lib/license';
import { rateLimit } from '../lib/rate-limiter';
import {
  getLicenseByKey,
  deactivateMachine,
  logUsage,
  getActiveMachines,
} from '../lib/db';

/**
 * Handle license deactivation request
 */
export async function handleDeactivateLicense(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  // Rate limiting
  const rateLimitHeaders = await rateLimit(env.CACHE, 'deactivate', clientIP);

  try {
    // Parse and validate request body
    const body = await request.json() as DeactivateLicenseRequest;

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

    // Get license
    const license = await getLicenseByKey(env.DB, licenseKey);

    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Deactivate the machine
    const deactivated = await deactivateMachine(env.DB, license.id, machineId);

    if (!deactivated) {
      // Machine wasn't active or doesn't exist - still return success
      const activeMachines = await getActiveMachines(env.DB, license.id);
      const response: DeactivateLicenseResponse = {
        deactivated: true,
        machines_remaining: activeMachines.length,
      };

      return new Response(JSON.stringify(response), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }

    // Log usage
    await logUsage(env.DB, {
      licenseId: license.id,
      machineId,
      action: 'deactivate',
    });

    // Get remaining active machines
    const activeMachines = await getActiveMachines(env.DB, license.id);

    const response: DeactivateLicenseResponse = {
      deactivated: true,
      machines_remaining: activeMachines.length,
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
