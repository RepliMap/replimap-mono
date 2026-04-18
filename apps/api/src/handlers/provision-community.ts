/**
 * Community License Auto-Provisioning
 * POST /v1/license/provision-community
 *
 * Idempotently creates a free-tier community license for a given email.
 * Called on first dashboard load after Clerk sign-up, so users never need
 * to manually request a license.
 *
 * If the user already has any active license (community OR paid), returns
 * the existing key without modification. Never overwrites a paid license.
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { generateLicenseKey, nowISO } from '../lib/license';
import { LIFETIME_EXPIRY } from '../lib/constants';
import {
  createDb,
  findOrCreateUser,
  createLicense,
  getLicenseByUserEmailLatest,
} from '../lib/db';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface ProvisionCommunityRequest {
  email: string;
}

interface ProvisionCommunityResponse {
  license_key: string;
  plan: string;
  status: string;
  created: boolean;
}

export async function handleProvisionCommunity(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);

  try {
    let body: ProvisionCommunityRequest;
    try {
      body = (await request.json()) as ProvisionCommunityRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    if (!body.email || typeof body.email !== 'string') {
      throw Errors.invalidRequest('Missing email');
    }
    if (!EMAIL_PATTERN.test(body.email)) {
      throw Errors.invalidRequest('Invalid email format');
    }

    const email = body.email.toLowerCase();
    const db = createDb(env.DB);

    // Idempotency: return existing active license (community OR paid — never
    // overwrite). "created: false" signals the caller not to show a welcome toast.
    const existing = await getLicenseByUserEmailLatest(db, email);
    if (existing) {
      const payload: ProvisionCommunityResponse = {
        license_key: existing.licenseKey,
        plan: existing.plan,
        status: existing.status,
        created: false,
      };
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      });
    }

    // No license yet — create user (idempotent) + community license
    const user = await findOrCreateUser(db, email);
    const licenseKey = generateLicenseKey();

    await createLicense(db, {
      userId: user.id,
      licenseKey,
      plan: 'community',
      planType: 'free',
      currentPeriodStart: nowISO(),
      currentPeriodEnd: LIFETIME_EXPIRY,
    });

    const payload: ProvisionCommunityResponse = {
      license_key: licenseKey,
      plan: 'community',
      status: 'active',
      created: true,
    };

    return new Response(JSON.stringify(payload), {
      status: 201,
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
