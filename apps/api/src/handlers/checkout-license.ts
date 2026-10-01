/**
 * Post-Checkout License Lookup
 * GET /v1/checkout/session/:session_id/license
 *
 * Used by the `/checkout/success` page to surface the newly-created license
 * key immediately after a Stripe redirect.
 *
 * AUTH: requires a valid Clerk session token (checked before any DB or Stripe
 * call), and the token email must equal the Stripe session's customer email
 * (403 otherwise). The session id is NOT a bearer credential.
 *
 * The session must be complete AND paid (`paid` or `no_payment_required` for
 * 100% promo codes); anything else is NOT_READY (404) with no key. The license
 * is bound to the session itself:
 *
 *   payment mode (lifetime): license stamped with `stripe_session_id`
 *     by the webhook's `checkout.session.completed`.
 *   subscription mode: license stamped with the session's `subscription` id
 *     by the webhook's `customer.subscription.created`. There is no
 *     latest-license-by-email fallback: an older paid license never satisfies
 *     a newer session.
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { rateLimit } from '../lib/rate-limiter';
import { isClerkConfigured, verifyClerkSession } from '../lib/clerk';
import {
  createDb,
  getLicenseBySessionId,
  getLicenseBySubscriptionId,
} from '../lib/db';
import type { License } from '../db/schema';

// Stripe checkout session IDs: "cs_test_..." or "cs_live_..."
const SESSION_ID_PATTERN = /^cs_(test|live)_[A-Za-z0-9]+$/;

const PAID_STATUSES = new Set(['paid', 'no_payment_required']);

interface StripeSessionResponse {
  mode?: string | null;
  status?: string | null;
  payment_status?: string | null;
  customer_email?: string | null;
  customer_details?: { email?: string | null } | null;
  subscription?: string | { id?: string | null } | null;
}

async function fetchStripeSession(
  env: Env,
  sessionId: string
): Promise<StripeSessionResponse> {
  if (!env.STRIPE_SECRET_KEY) {
    throw new AppError(
      'INTERNAL_ERROR',
      'Payment system not configured',
      503
    );
  }

  let response: Response;
  try {
    response = await fetch(
      `https://api.stripe.com/v1/checkout/sessions/${encodeURIComponent(sessionId)}`,
      { headers: { Authorization: `Bearer ${env.STRIPE_SECRET_KEY}` } }
    );
  } catch {
    throw new AppError(
      'INTERNAL_ERROR',
      'Could not reach the payment provider. Please retry shortly.',
      502
    );
  }

  if (response.status === 404) {
    throw Errors.notFound('Checkout session not found');
  }
  if (!response.ok) {
    throw new AppError(
      'INTERNAL_ERROR',
      'Could not load the checkout session. Please retry shortly.',
      502
    );
  }

  try {
    return (await response.json()) as StripeSessionResponse;
  } catch {
    throw new AppError(
      'INTERNAL_ERROR',
      'Could not load the checkout session. Please retry shortly.',
      502
    );
  }
}

function notReadyResponse(headers: Record<string, string>): Response {
  return new Response(
    JSON.stringify({
      error: 'NOT_READY',
      message: 'License is still being created. Please retry in a moment.',
    }),
    {
      status: 404,
      headers: { 'Content-Type': 'application/json', ...headers },
    }
  );
}

function subscriptionIdOf(session: StripeSessionResponse): string | null {
  const sub = session.subscription;
  if (typeof sub === 'string') return sub || null;
  return sub?.id || null;
}

export async function handleGetCheckoutLicense(
  request: Request,
  env: Env,
  clientIP: string,
  sessionId: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env, 'validate', clientIP);

  try {
    // Auth FIRST — before any DB or Stripe call. Fail closed when Clerk is
    // not configured, then require a valid session token.
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

    if (!SESSION_ID_PATTERN.test(sessionId)) {
      throw Errors.invalidRequest('Invalid session_id format');
    }

    const session = await fetchStripeSession(env, sessionId);

    // Ownership: the token email must be the session's customer email.
    const sessionEmail = (
      session.customer_email ??
      session.customer_details?.email ??
      ''
    ).toLowerCase();
    if (!sessionEmail || sessionEmail !== identity.email) {
      throw new AppError(
        'FORBIDDEN',
        'This checkout session does not belong to the authenticated account',
        403
      );
    }

    // Payment: complete AND paid (or fully discounted). Never reveal a key
    // for an open/unpaid session.
    if (
      session.status !== 'complete' ||
      !PAID_STATUSES.has(session.payment_status ?? '')
    ) {
      return notReadyResponse(rateLimitHeaders);
    }

    // Bind the license to THIS session (no latest-by-email fallback).
    const db = createDb(env.DB);
    let license: License | null = null;
    if (session.mode === 'payment') {
      license = await getLicenseBySessionId(db, sessionId);
    } else if (session.mode === 'subscription') {
      const subscriptionId = subscriptionIdOf(session);
      if (subscriptionId) {
        license = await getLicenseBySubscriptionId(db, subscriptionId);
      }
    }

    if (!license) {
      return notReadyResponse(rateLimitHeaders);
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
