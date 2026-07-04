/**
 * Community License Auto-Provisioning
 * POST /v1/license/provision-community
 *
 * Idempotently creates a free-tier community license for the AUTHENTICATED
 * caller. Called on first dashboard load after Clerk sign-up, so users never
 * need to manually request a license.
 *
 * AUTH (P0): requires a valid Clerk session token (Authorization: Bearer).
 * The email is derived from the verified token identity — NOT from the
 * request body — so a caller can only ever provision or retrieve a license
 * for their own account. A body email that disagrees with the token identity
 * is rejected (403). This closes the credential-disclosure hole where any
 * caller could pass a victim's email and receive that victim's license key.
 *
 * If the user already has any non-expired license (community OR paid),
 * returns the existing key without modification. Never overwrites a paid
 * license.
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { generateLicenseKey, nowISO } from '../lib/license';
import { LIFETIME_EXPIRY } from '../lib/constants';
import { isClerkConfigured, verifyClerkSession } from '../lib/clerk';
import {
  createDb,
  findOrCreateUser,
  createLicense,
  getNonExpiredLicenseByUserEmail,
} from '../lib/db';

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface ProvisionCommunityRequest {
  /** Optional. If present it must match the authenticated token identity. */
  email?: string;
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
  const rateLimitHeaders = await rateLimit(env, 'activate', clientIP);

  try {
    // ── Auth (P0): fail closed if Clerk is not configured, then require a
    // valid session token. The token identity — not the request body — is the
    // source of truth for which account gets provisioned. ──────────────────
    if (!isClerkConfigured(env)) {
      throw new AppError(
        'SERVER_CONFIG_ERROR',
        'Authentication is not configured for this endpoint',
        503
      );
    }

    const identity = await verifyClerkSession(request, env);
    if (!identity) {
      throw Errors.unauthorized(
        'A valid Clerk session token is required (Authorization: Bearer <token>)'
      );
    }

    // The authenticated email is authoritative. Parse the body only to reject
    // a mismatched email — we never provision for a caller-supplied address.
    let body: ProvisionCommunityRequest;
    try {
      body = (await request.json()) as ProvisionCommunityRequest;
    } catch {
      body = {};
    }
    if (
      typeof body.email === 'string' &&
      body.email.toLowerCase() !== identity.email
    ) {
      throw new AppError(
        'FORBIDDEN',
        'The requested email does not match the authenticated account',
        403
      );
    }

    const email = identity.email;
    if (!EMAIL_PATTERN.test(email)) {
      // Defensive: the verified identity should always be a valid email.
      throw Errors.unauthorized('Authenticated account has no valid email');
    }

    const db = createDb(env.DB);

    // Idempotency: return any existing NON-EXPIRED license (community OR
    // paid, in any status except 'expired' — never overwrite). A paid
    // license in past_due/canceled must surface as-is instead of being
    // shadowed by a fresh community key. "created: false" signals the
    // caller not to show a welcome toast.
    const existing = await getNonExpiredLicenseByUserEmail(db, email);
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
