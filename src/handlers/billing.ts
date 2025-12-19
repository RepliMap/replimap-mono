/**
 * Stripe Checkout and Customer Portal Handlers
 *
 * POST /v1/checkout/session - Create a Stripe Checkout session
 * POST /v1/billing/portal - Create a Stripe Customer Portal session
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { validateLicenseKey, normalizeLicenseKey } from '../lib/license';
import { PLAN_TO_STRIPE_PRICE } from '../lib/constants';
import { rateLimit } from '../lib/rate-limiter';

// ============================================================================
// Request/Response Types
// ============================================================================

interface CreateCheckoutRequest {
  plan: 'solo' | 'pro' | 'team';
  email: string;
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
 * Returns a URL to redirect the user to Stripe's hosted checkout page.
 */
export async function handleCreateCheckout(
  request: Request,
  env: Env,
  clientIP: string
): Promise<Response> {
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);

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
    if (!body.email) {
      throw Errors.invalidRequest('Missing email');
    }
    if (!body.success_url) {
      throw Errors.invalidRequest('Missing success_url');
    }
    if (!body.cancel_url) {
      throw Errors.invalidRequest('Missing cancel_url');
    }

    // Validate email format
    if (!isValidEmail(body.email)) {
      throw Errors.invalidRequest('Invalid email format');
    }

    // Validate plan
    const priceId = PLAN_TO_STRIPE_PRICE[body.plan];
    if (!priceId) {
      throw Errors.invalidRequest(`Invalid plan. Must be one of: solo, pro, team`);
    }

    // Validate URLs
    if (!isValidUrl(body.success_url) || !isValidUrl(body.cancel_url)) {
      throw Errors.invalidRequest('Invalid URL format');
    }

    // Create Stripe Checkout Session
    const session = await stripeRequest(env, 'checkout/sessions', {
      'mode': 'subscription',
      'payment_method_types[0]': 'card',
      'customer_email': body.email,
      'line_items[0][price]': priceId,
      'line_items[0][quantity]': 1,
      'success_url': `${body.success_url}${body.success_url.includes('?') ? '&' : '?'}session_id={CHECKOUT_SESSION_ID}`,
      'cancel_url': body.cancel_url,
      'metadata[plan]': body.plan,
      'subscription_data[metadata][plan]': body.plan,
      'allow_promotion_codes': true,
    });

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
  const rateLimitHeaders = await rateLimit(env.CACHE, 'activate', clientIP);

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

    // Find license and associated Stripe customer
    const result = await env.DB.prepare(`
      SELECT l.stripe_subscription_id, u.stripe_customer_id
      FROM licenses l
      JOIN users u ON l.user_id = u.id
      WHERE l.license_key = ?
    `).bind(licenseKey).first<{
      stripe_subscription_id: string | null;
      stripe_customer_id: string | null;
    }>();

    if (!result) {
      throw Errors.licenseNotFound();
    }

    if (!result.stripe_customer_id) {
      throw new AppError(
        'INVALID_REQUEST',
        'No billing account associated with this license. This may be a free or manually created license.',
        400
      );
    }

    // Create Stripe Customer Portal Session
    const session = await stripeRequest(env, 'billing_portal/sessions', {
      'customer': result.stripe_customer_id,
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

function isValidUrl(url: string): boolean {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
