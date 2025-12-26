/**
 * RepliMap Backend - Cloudflare Workers Entry Point
 *
 * Public Endpoints (No Auth):
 * - POST /v1/license/validate - Validate license and bind machine (HOT PATH)
 * - POST /v1/license/activate - Explicitly activate license on machine
 * - POST /v1/license/deactivate - Deactivate license from machine
 * - POST /v1/checkout/session - Create Stripe Checkout session
 * - POST /v1/billing/portal - Create Stripe Customer Portal session
 * - POST /v1/webhooks/stripe - Handle Stripe subscription events
 * - GET /health - Health check
 *
 * User Self-Service Endpoints (auth via license_key):
 * - GET /v1/me/license - Get own license details
 * - GET /v1/me/machines - Get machines for own license
 * - POST /v1/me/resend-key - Resend license key via email
 *
 * AWS Account Endpoints:
 * - POST /v1/aws-accounts/track - Track AWS account usage
 * - GET /v1/licenses/{key}/aws-accounts - Get AWS accounts for license
 *
 * Usage Endpoints:
 * - POST /v1/usage/sync - Sync usage data
 * - POST /v1/usage/track - Track feature usage event (NEW)
 * - GET /v1/usage/{license_key} - Get usage for license
 * - GET /v1/usage/{license_key}/history - Get usage history
 * - POST /v1/usage/check-quota - Check quota availability
 *
 * Feature Endpoints (NEW):
 * - GET /v1/features - Get all features info
 * - POST /v1/features/check - Check feature access
 * - GET /v1/features/flags - Get feature flags for license
 *
 * Metrics Endpoints (NEW, require X-API-Key):
 * - GET /v1/metrics/adoption - Feature adoption metrics
 * - GET /v1/metrics/conversion - Conversion metrics
 * - GET /v1/metrics/remediation-impact - Remediation impact
 * - GET /v1/metrics/snapshot-usage - Snapshot usage metrics
 * - GET /v1/metrics/deps-usage - Dependency explorer metrics
 *
 * Right-Sizer Endpoints (Solo+ feature):
 * - POST /v1/rightsizer/suggestions - Analyze resources and get downgrade suggestions
 *
 * Admin Endpoints (require X-API-Key):
 * - GET /v1/admin/stats - Get system stats ("God Mode" for operational visibility)
 * - POST /v1/admin/licenses - Create a new license
 * - GET /v1/admin/licenses/{key} - Get license details
 * - POST /v1/admin/licenses/{key}/revoke - Revoke a license
 */

import type { Env } from './types';
import {
  handleValidateLicense,
  handleActivateLicense,
  handleDeactivateLicense,
  handleStripeWebhook,
  handleCreateLicense,
  handleRevokeLicense,
  handleGetLicense,
  handleGetStats,
  handleTrackAwsAccount,
  handleGetAwsAccounts,
  handleSyncUsage,
  handleGetUsage,
  handleGetUsageHistory,
  handleCheckQuota,
  handleTrackEvent,
  handleCreateCheckout,
  handleCreateBillingPortal,
  handleGetOwnLicense,
  handleGetOwnMachines,
  handleResendKey,
  handleGetFeatures,
  handleCheckFeature,
  handleGetFeatureFlags,
  handleGetAdoption,
  handleGetConversion,
  handleGetRemediationImpact,
  handleGetSnapshotUsage,
  handleGetDepsUsage,
  handleRightSizerSuggestions,
} from './handlers';
import { AppError, Errors, generateSupportId } from './lib/errors';
import { validateContentLength, MAX_CONTENT_LENGTH, logError } from './lib/security';
import { rateLimit } from './lib/rate-limiter';

// ============================================================================
// CORS Configuration
// ============================================================================

function getCorsHeaders(env: Env, origin: string | null): Record<string, string> {
  const allowedOrigin = env.CORS_ORIGIN || '*';

  // In production, check if origin is allowed
  if (allowedOrigin !== '*' && origin) {
    const allowedOrigins = allowedOrigin.split(',').map((o) => o.trim());
    if (!allowedOrigins.includes(origin)) {
      return {}; // Don't set CORS headers for disallowed origins
    }
  }

  return {
    'Access-Control-Allow-Origin': allowedOrigin === '*' ? '*' : (origin || '*'),
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-API-Key',
    'Access-Control-Max-Age': '86400', // 24 hours
  };
}

function handleOptions(env: Env, request: Request): Response {
  const origin = request.headers.get('Origin');
  const corsHeaders = getCorsHeaders(env, origin);

  return new Response(null, {
    status: 204,
    headers: corsHeaders,
  });
}

// ============================================================================
// Client IP Extraction
// ============================================================================

function getClientIP(request: Request): string {
  // Cloudflare provides the original client IP
  const cfIP = request.headers.get('CF-Connecting-IP');
  if (cfIP) return cfIP;

  // Fallback to X-Forwarded-For
  const forwardedFor = request.headers.get('X-Forwarded-For');
  if (forwardedFor) {
    return forwardedFor.split(',')[0].trim();
  }

  // Last resort - use X-Real-IP
  const realIP = request.headers.get('X-Real-IP');
  if (realIP) return realIP;

  return '0.0.0.0';
}

// ============================================================================
// Route Matching Helpers
// ============================================================================

/**
 * Extract path parameter from pattern like /v1/licenses/{key}/aws-accounts
 */
function matchPathParam(path: string, pattern: string): string | null {
  const patternParts = pattern.split('/');
  const pathParts = path.split('/');

  if (patternParts.length !== pathParts.length) {
    return null;
  }

  let paramValue: string | null = null;

  for (let i = 0; i < patternParts.length; i++) {
    if (patternParts[i].startsWith('{') && patternParts[i].endsWith('}')) {
      paramValue = pathParts[i];
    } else if (patternParts[i] !== pathParts[i]) {
      return null;
    }
  }

  return paramValue;
}

// ============================================================================
// Request Router
// ============================================================================

async function handleRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const path = url.pathname;
  const method = request.method;
  const origin = request.headers.get('Origin');
  const corsHeaders = getCorsHeaders(env, origin);

  // Handle CORS preflight
  if (method === 'OPTIONS') {
    return handleOptions(env, request);
  }

  // Get client IP for rate limiting
  const clientIP = getClientIP(request);

  try {
    // ========================================================================
    // Content-Length Validation (DoS Protection)
    // ========================================================================
    if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
      // Stripe webhook needs larger payload (up to 1MB for large events)
      const maxLength = path === '/v1/webhooks/stripe' ? 1024 * 1024 : MAX_CONTENT_LENGTH;
      validateContentLength(request, maxLength);
    }

    let response: Response | undefined;

    // ========================================================================
    // License Endpoints
    // ========================================================================
    if (path === '/v1/license/validate' && method === 'POST') {
      response = await handleValidateLicense(request, env, clientIP);
    } else if (path === '/v1/license/activate' && method === 'POST') {
      response = await handleActivateLicense(request, env, clientIP);
    } else if (path === '/v1/license/deactivate' && method === 'POST') {
      response = await handleDeactivateLicense(request, env, clientIP);
    }

    // ========================================================================
    // Checkout & Billing Endpoints
    // ========================================================================
    else if (path === '/v1/checkout/session' && method === 'POST') {
      response = await handleCreateCheckout(request, env, clientIP);
    } else if (path === '/v1/billing/portal' && method === 'POST') {
      response = await handleCreateBillingPortal(request, env, clientIP);
    }

    // ========================================================================
    // User Self-Service Endpoints
    // ========================================================================
    else if (path === '/v1/me/license' && method === 'GET') {
      response = await handleGetOwnLicense(request, env, clientIP);
    } else if (path === '/v1/me/machines' && method === 'GET') {
      response = await handleGetOwnMachines(request, env, clientIP);
    } else if (path === '/v1/me/resend-key' && method === 'POST') {
      response = await handleResendKey(request, env, clientIP);
    }

    // ========================================================================
    // AWS Account Endpoints
    // ========================================================================
    else if (path === '/v1/aws-accounts/track' && method === 'POST') {
      response = await handleTrackAwsAccount(request, env, clientIP);
    } else if (method === 'GET') {
      const awsAccountsKey = matchPathParam(path, '/v1/licenses/{key}/aws-accounts');
      if (awsAccountsKey) {
        response = await handleGetAwsAccounts(request, env, awsAccountsKey, clientIP);
      }
    }

    // ========================================================================
    // Usage Endpoints
    // ========================================================================
    if (!response && path === '/v1/usage/sync' && method === 'POST') {
      response = await handleSyncUsage(request, env, clientIP);
    } else if (!response && path === '/v1/usage/track' && method === 'POST') {
      response = await handleTrackEvent(request, env, clientIP);
    } else if (!response && path === '/v1/usage/check-quota' && method === 'POST') {
      response = await handleCheckQuota(request, env, clientIP);
    } else if (!response && method === 'GET') {
      // GET /v1/usage/{license_key}/history
      const historyKey = matchPathParam(path, '/v1/usage/{key}/history');
      if (historyKey) {
        response = await handleGetUsageHistory(request, env, historyKey, clientIP);
      } else {
        // GET /v1/usage/{license_key}
        const usageKey = matchPathParam(path, '/v1/usage/{key}');
        if (usageKey) {
          response = await handleGetUsage(request, env, usageKey, clientIP);
        }
      }
    }

    // ========================================================================
    // Feature Endpoints (NEW)
    // ========================================================================
    if (!response && path === '/v1/features' && method === 'GET') {
      response = await handleGetFeatures(request, env, clientIP);
    } else if (!response && path === '/v1/features/check' && method === 'POST') {
      response = await handleCheckFeature(request, env, clientIP);
    } else if (!response && path === '/v1/features/flags' && method === 'GET') {
      response = await handleGetFeatureFlags(request, env, clientIP);
    }

    // ========================================================================
    // Metrics Endpoints (NEW - require X-API-Key)
    // ========================================================================
    if (!response && path === '/v1/metrics/adoption' && method === 'GET') {
      response = await handleGetAdoption(request, env, clientIP);
    } else if (!response && path === '/v1/metrics/conversion' && method === 'GET') {
      response = await handleGetConversion(request, env, clientIP);
    } else if (!response && path === '/v1/metrics/remediation-impact' && method === 'GET') {
      response = await handleGetRemediationImpact(request, env, clientIP);
    } else if (!response && path === '/v1/metrics/snapshot-usage' && method === 'GET') {
      response = await handleGetSnapshotUsage(request, env, clientIP);
    } else if (!response && path === '/v1/metrics/deps-usage' && method === 'GET') {
      response = await handleGetDepsUsage(request, env, clientIP);
    }

    // ========================================================================
    // Right-Sizer Endpoints (Solo+ feature)
    // ========================================================================
    if (!response && path === '/v1/rightsizer/suggestions' && method === 'POST') {
      response = await handleRightSizerSuggestions(request, env, clientIP);
    }

    // ========================================================================
    // Admin Endpoints (rate limited to prevent brute-force attacks)
    // ========================================================================
    if (!response && path === '/v1/admin/stats' && method === 'GET') {
      // "God Mode" endpoint - operational visibility
      await rateLimit(env.CACHE, 'admin', clientIP);
      response = await handleGetStats(request, env);
    } else if (!response && path === '/v1/admin/licenses' && method === 'POST') {
      await rateLimit(env.CACHE, 'admin', clientIP);
      response = await handleCreateLicense(request, env);
    } else if (!response && method === 'GET') {
      const adminLicenseKey = matchPathParam(path, '/v1/admin/licenses/{key}');
      if (adminLicenseKey) {
        await rateLimit(env.CACHE, 'admin', clientIP);
        response = await handleGetLicense(request, env, adminLicenseKey);
      }
    } else if (!response && method === 'POST') {
      const revokeKey = matchPathParam(path, '/v1/admin/licenses/{key}/revoke');
      if (revokeKey) {
        await rateLimit(env.CACHE, 'admin', clientIP);
        response = await handleRevokeLicense(request, env, revokeKey);
      }
    }

    // ========================================================================
    // Stripe Webhook
    // ========================================================================
    if (!response && path === '/v1/webhooks/stripe' && method === 'POST') {
      // Stripe webhook - no CORS needed (server-to-server)
      return handleStripeWebhook(request, env);
    }

    // ========================================================================
    // Utility Endpoints
    // ========================================================================
    if (!response && path === '/health' && method === 'GET') {
      response = new Response(JSON.stringify({
        status: 'ok',
        timestamp: new Date().toISOString(),
        version: env.API_VERSION || '2.1.0',
        // Date when AWS pricing data was last refreshed
        // Update this when refreshing pricing data in the right-sizer
        pricing_data_date: '2025-12-26',
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } else if (!response && path === '/' && method === 'GET') {
      response = new Response(JSON.stringify({
        name: 'RepliMap License API',
        version: env.API_VERSION || 'v1.2.0',
        environment: env.ENVIRONMENT,
        features: {
          new: ['audit_fix', 'snapshot', 'snapshot_diff', 'graph_full', 'graph_security'],
          renamed: [{ old: 'blast', new: 'deps' }],
        },
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }

    // ========================================================================
    // 404 Not Found
    // ========================================================================
    if (!response) {
      throw Errors.notFound(`Endpoint ${method} ${path} not found`);
    }

    // Add CORS headers to response
    const headers = new Headers(response.headers);
    Object.entries(corsHeaders).forEach(([key, value]) => {
      headers.set(key, value);
    });

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers,
    });
  } catch (error) {
    // Handle known errors
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // Generate support ID for tracking
    const supportId = generateSupportId();

    // Log full error internally (with support ID for correlation)
    logError(`Unhandled error [${supportId}]`, error);

    // Return sanitized error - NEVER expose stack traces or internal details
    return new Response(JSON.stringify({
      valid: false,
      error_code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred. Please try again.',
      support_id: supportId,
    }), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  }
}

// ============================================================================
// Scheduled Handler (Cron Cleanup)
// ============================================================================

/**
 * Scheduled handler for database maintenance.
 * Runs weekly (configure in wrangler.toml: crons = ["0 0 * * 0"])
 *
 * Tasks:
 * - Prune old usage_events (> 90 days)
 * - Prune orphaned devices (not seen in 90 days)
 * - Clean up expired idempotency keys
 */
async function handleScheduled(
  _controller: ScheduledController,
  env: Env
): Promise<void> {
  const startTime = Date.now();
  console.log(`[Cron] Starting scheduled cleanup at ${new Date().toISOString()}`);

  try {
    // 1. Prune old usage_events (> 90 days)
    const usageEventsResult = await env.DB.prepare(`
      DELETE FROM usage_events
      WHERE created_at < datetime('now', '-90 days')
    `).run();
    console.log(`[Cron] Deleted ${usageEventsResult.meta.changes} old usage_events`);

    // 2. Prune orphaned devices (not seen in 90 days)
    const devicesResult = await env.DB.prepare(`
      DELETE FROM license_machines
      WHERE last_seen_at < datetime('now', '-90 days')
        AND is_active = 0
    `).run();
    console.log(`[Cron] Deleted ${devicesResult.meta.changes} orphaned devices`);

    // 3. Mark stale devices as inactive (not seen in 30 days)
    const staleResult = await env.DB.prepare(`
      UPDATE license_machines
      SET is_active = 0
      WHERE last_seen_at < datetime('now', '-30 days')
        AND is_active = 1
    `).run();
    console.log(`[Cron] Marked ${staleResult.meta.changes} stale devices as inactive`);

    // 4. Clean up old idempotency keys (> 7 days)
    const idempotencyResult = await env.DB.prepare(`
      DELETE FROM usage_idempotency
      WHERE created_at < datetime('now', '-7 days')
    `).run();
    console.log(`[Cron] Deleted ${idempotencyResult.meta.changes} old idempotency keys`);

    // 5. Clean up old processed events (> 30 days)
    const processedResult = await env.DB.prepare(`
      DELETE FROM processed_events
      WHERE processed_at < datetime('now', '-30 days')
    `).run();
    console.log(`[Cron] Deleted ${processedResult.meta.changes} old processed_events`);

    const elapsed = Date.now() - startTime;
    console.log(`[Cron] Cleanup completed in ${elapsed}ms`);
  } catch (error) {
    console.error('[Cron] Cleanup failed:', error);
    throw error;
  }
}

// ============================================================================
// Worker Export
// ============================================================================

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    return handleRequest(request, env);
  },

  async scheduled(
    controller: ScheduledController,
    env: Env,
    ctx: ExecutionContext
  ): Promise<void> {
    ctx.waitUntil(handleScheduled(controller, env));
  },
};
