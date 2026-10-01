/**
 * Stripe Checkout and Customer Portal Handlers
 *
 * POST /v1/checkout/session - Create a Stripe Checkout session
 * POST /v1/billing/portal - Create a Stripe Customer Portal session
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey } from '../lib/license';
import {
  PLAN_TO_STRIPE_PRICE,
  PLAN_TO_STRIPE_ANNUAL_PRICE,
  STRIPE_LIFETIME_PRICE_TO_PLAN,
} from '../lib/constants';
import { rateLimit } from '../lib/rate-limiter';
import { createDb } from '../lib/db';
import { isClerkConfigured, verifyClerkSession } from '../lib/clerk';
import { sql } from 'drizzle-orm';

// ============================================================================
// Request/Response Types
// ============================================================================

interface CreateCheckoutRequest {
  plan: 'pro' | 'team' | 'sovereign';
  billing_period?: 'monthly' | 'annual' | 'lifetime';
  /** Optional. If present it must match the authenticated token identity. */
  email?: string;
  success_url: string;
  cancel_url: string;
}

interface CreateCheckoutResponse {
  checkout_url: string;
  session_id: string;
}

interface CreatePortalRequest {
  license_key: string;
  return_url: string;
}

interface CreatePortalResponse {
  portal_url: string;
}

// ============================================================================
// Stripe API Helpers (using fetch instead of SDK for Workers compatibility)
// ============================================================================

async function stripeRequest(
  env: Env,
  endpoint: string,
  body: Record<string, string | number | boolean | undefined>
): Promise<Record<string, unknown>> {
  // Filter out undefined values and convert to URL-encoded form data
  const formData = new URLSearchParams();
  for (const [key, value] of Object.entries(body)) {
    if (value !== undefined) {
      formData.append(key, String(value));
    }
  }

  const response = await fetch(`https://api.stripe.com/v1/${endpoint}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${env.STRIPE_SECRET_KEY}`,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData.toString(),
  });

  const data = await response.json() as Record<string, unknown>;

  if (!response.ok) {
    const error = data.error as Record<string, string> | undefined;
    throw new AppError(
      'INTERNAL_ERROR',
      error?.message || 'Stripe API error',
      response.status >= 500 ? 502 : 400
    );
  }

  return data;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Create a Stripe Checkout Session
 * POST /v1/checkout/session
 *
 * Creates a checkout session for subscription purchase.
 *
 * AUTH: requires a valid Clerk session token. The Stripe customer_email is the
 * token email (a differing body email is rejected with 403) and the Clerk user
 * id is stamped as client_reference_id. success_url / cancel_url must be on an
 * exact origin in CHECKOUT_ALLOWED_ORIGINS (fail-closed).
 * Returns a URL to redirect the user to Stripe's hosted checkout page.
 */
export async function handleCreateCheckout(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env, 'activate', clientIP);

  try {
    // Auth first: fail closed when Clerk is not configured, then require a
    // valid session token.
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

    // Validate Stripe is configured
    if (!env.STRIPE_SECRET_KEY) {
      throw new AppError(
        'INTERNAL_ERROR',
        'Payment system not configured',
        503
      );
    }

    // Parse request body
    let body: CreateCheckoutRequest;
    try {
      body = await request.json() as CreateCheckoutRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate required fields
    if (!body.plan) {
      throw Errors.invalidRequest('Missing plan');
    }
    if (!body.success_url) {
      throw Errors.invalidRequest('Missing success_url');
    }
    if (!body.cancel_url) {
      throw Errors.invalidRequest('Missing cancel_url');
    }

    // The token email is authoritative; a body email may only restate it.
    if (body.email !== undefined && body.email !== null) {
      if (
        typeof body.email !== 'string' ||
        body.email.toLowerCase() !== identity.email
      ) {
        throw new AppError(
          'FORBIDDEN',
          'The requested email does not match the authenticated account',
          403
        );
      }
    }
    if (!isValidEmail(identity.email)) {
      throw Errors.unauthorized('Authenticated account has no valid email');
    }

    // Sovereign is sales-assisted only: its Stripe price ids are placeholders
    // that don't exist, so forwarding the request would fail with an opaque
    // Stripe error. Refuse it up front with an actionable message.
    if (body.plan === 'sovereign') {
      throw Errors.invalidRequest(
        'The sovereign plan is not available for self-serve checkout. ' +
          'Please contact sales to purchase sovereign.'
      );
    }

    // Validate plan and resolve price ID based on billing period
    const billingPeriod = body.billing_period || 'monthly';

    let priceId: string | undefined;
    let isLifetime = false;
    if (billingPeriod === 'lifetime') {
      // Reverse-lookup lifetime price by plan name
      priceId = Object.entries(STRIPE_LIFETIME_PRICE_TO_PLAN).find(
        ([, info]) => info.plan === body.plan
      )?.[0];
      isLifetime = true;
    } else if (billingPeriod === 'annual') {
      priceId = PLAN_TO_STRIPE_ANNUAL_PRICE[body.plan];
    } else {
      priceId = PLAN_TO_STRIPE_PRICE[body.plan];
    }

    if (!priceId) {
      throw Errors.invalidRequest(
        `Invalid plan "${body.plan}" for ${billingPeriod} billing`
      );
    }

    // Validate URLs
    if (!isValidUrl(body.success_url) || !isValidUrl(body.cancel_url)) {
      throw Errors.invalidRequest('Invalid URL format');
    }
    const allowedOrigins = parseAllowedOrigins(env.CHECKOUT_ALLOWED_ORIGINS);
    if (
      !allowedOrigins ||
      !allowedOrigins.has(new URL(body.success_url).origin) ||
      !allowedOrigins.has(new URL(body.cancel_url).origin)
    ) {
      throw Errors.invalidRequest(
        'success_url and cancel_url must be on an allowed origin'
      );
    }

    // Lifetime = one-time payment, subscription = recurring
    // Stripe's API requires mode=payment for one-time line items and
    // disallows subscription_data in that case.
    const checkoutBody: Record<string, string | number | boolean | undefined> = {
      'mode': isLifetime ? 'payment' : 'subscription',
      'payment_method_types[0]': 'card',
      'customer_email': identity.email,
      'client_reference_id': identity.userId,
      'line_items[0][price]': priceId,
      'line_items[0][quantity]': 1,
      'success_url': `${body.success_url}${body.success_url.includes('?') ? '&' : '?'}session_id={CHECKOUT_SESSION_ID}`,
      'cancel_url': body.cancel_url,
      'metadata[plan]': body.plan,
      'metadata[billing_period]': billingPeriod,
      'allow_promotion_codes': true,
    };

    if (!isLifetime) {
      checkoutBody['subscription_data[metadata][plan]'] = body.plan;
    } else {
      // Payment mode defaults to customer_creation=if_required, which
      // usually creates NO Customer — the resulting charge then has
      // customer=null and refund handling can only resolve the license via
      // payment_intent. Always create one so the buyer's user row gets a
      // customer_id and customer-based flows (refunds, support lookups) work.
      checkoutBody['customer_creation'] = 'always';
    }

    const session = await stripeRequest(env, 'checkout/sessions', checkoutBody);

    const response: CreateCheckoutResponse = {
      checkout_url: session.url as string,
      session_id: session.id as string,
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
 * Create a Stripe Customer Portal Session
 * POST /v1/billing/portal
 *
 * Creates a portal session for subscription management.
 * Returns a URL to redirect the user to Stripe's hosted customer portal.
 */
export async function handleCreateBillingPortal(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env, 'activate', clientIP);

  try {
    // Validate Stripe is configured
    if (!env.STRIPE_SECRET_KEY) {
      throw new AppError(
        'INTERNAL_ERROR',
        'Payment system not configured',
        503
      );
    }

    // Parse request body
    let body: CreatePortalRequest;
    try {
      body = await request.json() as CreatePortalRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate required fields
    if (!body.license_key) {
      throw Errors.invalidRequest('Missing license_key');
    }
    if (!body.return_url) {
      throw Errors.invalidRequest('Missing return_url');
    }

    // Validate license key format
    validateLicenseKey(body.license_key);
    const licenseKey = normalizeLicenseKey(body.license_key);

    // Validate URL
    if (!isValidUrl(body.return_url)) {
      throw Errors.invalidRequest('Invalid URL format');
    }

    // Create Drizzle client
    const db = createDb(env.DB);

    // Find license and associated Stripe customer
    // NOTE: Uses 'user' table (singular) and 'customer_id' column (new schema)
    const result = await db.get<{
      stripe_subscription_id: string | null;
      customer_id: string | null;
    }>(sql`
      SELECT l.stripe_subscription_id, u.customer_id
      FROM licenses l
      JOIN user u ON l.user_id = u.id
      WHERE l.license_key = ${licenseKey}
    `);

    if (!result) {
      throw Errors.licenseNotFound();
    }

    if (!result.customer_id) {
      throw new AppError(
        'INVALID_REQUEST',
        'No billing account associated with this license. This may be a free or manually created license.',
        400
      );
    }

    // Create Stripe Customer Portal Session
    const session = await stripeRequest(env, 'billing_portal/sessions', {
      'customer': result.customer_id,
      'return_url': body.return_url,
    });

    const response: CreatePortalResponse = {
      portal_url: session.url as string,
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

// ============================================================================
// Helpers
// ============================================================================

function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Parse the comma-separated origin allowlist into a Set of exact origins.
 * Returns null (fail closed) when unset/empty or when any entry is '*'.
 */
function parseAllowedOrigins(raw: string | undefined): Set<string> | null {
  if (!raw) return null;
  const entries = raw
    .split(',')
    .map((e) => e.trim())
    .filter(Boolean);
  if (entries.length === 0 || entries.includes('*')) return null;
  const origins = new Set<string>();
  for (const entry of entries) {
    try {
      origins.add(new URL(entry).origin);
    } catch {
      // Ignore malformed entries; they can never match.
    }
  }
  return origins.size > 0 ? origins : null;
}

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
