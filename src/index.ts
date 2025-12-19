/**
 * RepliMap Backend - Cloudflare Workers Entry Point
 *
 * API Endpoints:
 * - POST /v1/license/validate - Validate license and bind machine (HOT PATH)
 * - POST /v1/license/activate - Explicitly activate license on machine
 * - POST /v1/license/deactivate - Deactivate license from machine
 * - POST /v1/webhooks/stripe - Handle Stripe subscription events
 */

import type { Env } from './types';
import {
  handleValidateLicense,
  handleActivateLicense,
  handleDeactivateLicense,
  handleStripeWebhook,
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
    let response: Response;

    // Route to appropriate handler
    if (path === '/v1/license/validate' && method === 'POST') {
      response = await handleValidateLicense(request, env, clientIP);
    } else if (path === '/v1/license/activate' && method === 'POST') {
      response = await handleActivateLicense(request, env, clientIP);
    } else if (path === '/v1/license/deactivate' && method === 'POST') {
      response = await handleDeactivateLicense(request, env, clientIP);
    } else if (path === '/v1/webhooks/stripe' && method === 'POST') {
      // Stripe webhook - no CORS needed (server-to-server)
      return handleStripeWebhook(request, env);
    } else if (path === '/health' && method === 'GET') {
      // Health check endpoint
      return new Response(JSON.stringify({ status: 'ok', timestamp: new Date().toISOString() }), {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    } else if (path === '/' && method === 'GET') {
      // Root endpoint - API info
      return new Response(
        JSON.stringify({
          name: 'RepliMap License API',
          version: env.API_VERSION || 'v1',
          environment: env.ENVIRONMENT,
        }),
        {
          status: 200,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        }
      );
    } else {
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
