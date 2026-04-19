/**
 * Post-Checkout License Lookup
 * GET /v1/checkout/session/:session_id/license
 *
 * Used by the `/checkout/success` page to surface the newly-created license
 * key immediately after a Stripe redirect. Two resolution paths:
 *
 *   Path A (lifetime / one-time payment):
 *     The webhook stamps `licenses.stripe_session_id` on the license row
 *     in `checkout.session.completed`. We can look it up directly.
 *
 *   Path B (subscription):
 *     The license is created by `customer.subscription.created`, which has
 *     no session_id. We fetch the Checkout Session from Stripe to get the
 *     customer's email, then return their latest active license.
 *
 * Auth: the session_id from the Stripe redirect URL acts as the bearer
 * token — anyone holding it is assumed to be the purchaser. No additional
 * auth is required.
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import {
  createDb,
  getLicenseBySessionId,
  getLicenseByUserEmailLatest,
} from '../lib/db';

// Stripe checkout session IDs: "cs_test_..." or "cs_live_..."
const SESSION_ID_PATTERN = /^cs_(test|live)_[A-Za-z0-9]+$/;

interface StripeSessionResponse {
  customer_email?: string | null;
  customer_details?: { email?: string | null } | null;
}

async function fetchStripeSessionEmail(
  env: Env,
  sessionId: string
): Promise<string | null> {
  if (!env.STRIPE_SECRET_KEY) return null;

  const response = await fetch(
    `https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(sessionId)}`,
    {
      headers: {
        Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
      },
    }
  );

  if (!response.ok) return null;

  const session = (await response.json()) as StripeSessionResponse;
  return (
    session.customer_email ??
    session.customer_details?.email ??
    null
  );
}

export async function handleGetCheckoutLicense(
  request: Request,
  env: Env,
  clientIP: string,
  sessionId: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env, 'validate', clientIP);

  try {
    if (!SESSION_ID_PATTERN.test(sessionId)) {
      throw Errors.invalidRequest('Invalid session_id format');
    }

    const db = createDb(env.DB);

    // Path A: lifetime — license stamped with session_id
    let license = await getLicenseBySessionId(db, sessionId);

    // Path B: subscription — look up by customer email
    if (!license) {
      const email = await fetchStripeSessionEmail(env, sessionId);
      if (email) {
        license = await getLicenseByUserEmailLatest(db, email);
      }
    }

    if (!license) {
      return new Response(
        JSON.stringify({
          error: 'NOT_READY',
          message:
            'License is still being created. Please retry in a moment.',
        }),
        {
          status: 404,
          headers: {
            'Content-Type': 'application/json',
            ...rateLimitHeaders,
          },
        }
      );
    }

    return new Response(
      JSON.stringify({
        license_key: license.licenseKey,
        plan: license.plan,
        status: license.status,
        plan_type: license.planType,
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...rateLimitHeaders,
        },
      }
    );
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
