/**
 * RepliMap Backend - Cloudflare Workers Entry Point
 *
 * API Endpoints:
 * - POST /v1/license/validate - Validate license and bind machine (HOT PATH)
 * - POST /v1/license/activate - Explicitly activate license on machine
 * - POST /v1/license/deactivate - Deactivate license from machine
 * - POST /v1/webhooks/stripe - Handle Stripe subscription events
 *
 * AWS Account Endpoints:
 * - POST /v1/aws-accounts/track - Track AWS account usage
 * - GET /v1/licenses/{key}/aws-accounts - Get AWS accounts for license
 *
 * Usage Endpoints:
 * - POST /v1/usage/sync - Sync usage data
 * - GET /v1/usage/{license_key} - Get usage for license
 * - GET /v1/usage/{license_key}/history - Get usage history
 * - POST /v1/usage/check-quota - Check quota availability
 *
 * Admin Endpoints (require X-API-Key):
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
  handleTrackAwsAccount,
  handleGetAwsAccounts,
  handleSyncUsage,
  handleGetUsage,
  handleGetUsageHistory,
  handleCheckQuota,
} from './handlers';
import { AppError, Errors } from './lib/errors';

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
    // Admin Endpoints
    // ========================================================================
    if (!response && path === '/v1/admin/licenses' && method === 'POST') {
      response = await handleCreateLicense(request, env);
    } else if (!response && method === 'GET') {
      const adminLicenseKey = matchPathParam(path, '/v1/admin/licenses/{key}');
      if (adminLicenseKey) {
        response = await handleGetLicense(request, env, adminLicenseKey);
      }
    } else if (!response && method === 'POST') {
      const revokeKey = matchPathParam(path, '/v1/admin/licenses/{key}/revoke');
      if (revokeKey) {
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
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } else if (!response && path === '/' && method === 'GET') {
      response = new Response(JSON.stringify({
        name: 'RepliMap License API',
        version: env.API_VERSION || 'v1',
        environment: env.ENVIRONMENT,
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

    // Log unknown errors
    console.error('Unhandled error:', error);

    // Return generic error
    const internalError = Errors.internal('An unexpected error occurred');
    return new Response(JSON.stringify(internalError.toResponse()), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
        ...corsHeaders,
      },
    });
  }
}

// ============================================================================
// Worker Export
// ============================================================================

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    return handleRequest(request, env);
  },
};
