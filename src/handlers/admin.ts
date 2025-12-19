/**
 * Admin API Handlers
 * Requires X-API-Key header with valid admin API key
 */

import type { Env } from '../types/env';
import { Errors, AppError } from '../lib/errors';
import { generateLicenseKey, validateLicenseKey, normalizeLicenseKey } from '../lib/license';
import { PLAN_FEATURES, type PlanType } from '../lib/constants';
import {
  findOrCreateUser,
  createLicense,
  getLicenseByKey,
  updateLicenseStatus,
} from '../lib/db';

// ============================================================================
// Admin API Key Verification
// ============================================================================

/**
 * Verify admin API key from X-API-Key header
 * Uses constant-time comparison to prevent timing attacks
 */
export function verifyAdminApiKey(request: Request, env: Env): void {
  const adminKey = env.ADMIN_API_KEY;

  if (!adminKey) {
    throw new AppError(
      'INTERNAL_ERROR',
      'Admin API is not configured. Set ADMIN_API_KEY secret.',
      503
    );
  }

  const providedKey = request.headers.get('X-API-Key');

  if (!providedKey) {
    throw new AppError(
      'INVALID_REQUEST',
      'Missing X-API-Key header',
      401
    );
  }

  // Constant-time comparison
  if (providedKey.length !== adminKey.length) {
    throw new AppError('INVALID_REQUEST', 'Invalid API key', 403);
  }

  let result = 0;
  for (let i = 0; i < providedKey.length; i++) {
    result |= providedKey.charCodeAt(i) ^ adminKey.charCodeAt(i);
  }

  if (result !== 0) {
    throw new AppError('INVALID_REQUEST', 'Invalid API key', 403);
  }
}

// ============================================================================
// Request/Response Types
// ============================================================================

interface CreateLicenseRequest {
  customer_email: string;
  plan?: string;
  expires_in_days?: number;
  notes?: string;
}

interface CreateLicenseResponse {
  license_key: string;
  plan: string;
  status: string;
  expires_at: string | null;
  created_at: string;
}

interface RevokeLicenseRequest {
  reason?: string;
}

// ============================================================================
// Handlers
// ============================================================================

/**
 * Create a new license (admin only)
 * POST /v1/admin/licenses
 */
export async function handleCreateLicense(
  request: Request,
  env: Env
): Promise<Response> {
  try {
    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Parse request body
    let body: CreateLicenseRequest;
    try {
      body = await request.json() as CreateLicenseRequest;
    } catch {
      throw Errors.invalidRequest('Invalid JSON body');
    }

    // Validate email
    if (!body.customer_email || !isValidEmail(body.customer_email)) {
      throw Errors.invalidRequest('Valid customer_email is required');
    }

    // Validate plan
    const plan = (body.plan || 'free') as PlanType;
    if (!PLAN_FEATURES[plan]) {
      throw Errors.invalidRequest(`Invalid plan. Must be one of: ${Object.keys(PLAN_FEATURES).join(', ')}`);
    }

    // Find or create user
    const user = await findOrCreateUser(env.DB, body.customer_email);

    // Generate license key
    const licenseKey = generateLicenseKey();

    // Calculate expiration
    let currentPeriodEnd: string | undefined;
    if (body.expires_in_days && body.expires_in_days > 0) {
      const expiresAt = new Date();
      expiresAt.setDate(expiresAt.getDate() + body.expires_in_days);
      currentPeriodEnd = expiresAt.toISOString();
    }

    // Create license
    const license = await createLicense(env.DB, {
      userId: user.id,
      licenseKey,
      plan,
      currentPeriodEnd,
    });

    const response: CreateLicenseResponse = {
      license_key: license.license_key,
      plan: license.plan,
      status: license.status,
      expires_at: license.current_period_end,
      created_at: license.created_at,
    };

    return new Response(JSON.stringify(response), {
      status: 201,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

/**
 * Revoke a license (admin only)
 * POST /v1/admin/licenses/{license_key}/revoke
 */
export async function handleRevokeLicense(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Parse request body (optional)
    let body: RevokeLicenseRequest = {};
    try {
      const text = await request.text();
      if (text) {
        body = JSON.parse(text);
      }
    } catch {
      // Ignore - body is optional
    }

    // Get license
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    // Revoke license
    await updateLicenseStatus(env.DB, license.id, 'revoked');

    return new Response(JSON.stringify({
      revoked: true,
      license_key: normalizedKey,
      reason: body.reason || null,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
      });
    }
    throw error;
  }
}

/**
 * Get license details (admin only)
 * GET /v1/admin/licenses/{license_key}
 */
export async function handleGetLicense(
  request: Request,
  env: Env,
  licenseKey: string
): Promise<Response> {
  try {
    // Verify admin API key
    verifyAdminApiKey(request, env);

    // Validate license key format
    validateLicenseKey(licenseKey);
    const normalizedKey = normalizeLicenseKey(licenseKey);

    // Get license
    const license = await getLicenseByKey(env.DB, normalizedKey);
    if (!license) {
      throw Errors.licenseNotFound();
    }

    const features = PLAN_FEATURES[license.plan as PlanType] ?? PLAN_FEATURES.free;

    return new Response(JSON.stringify({
      license_key: license.license_key,
      plan: license.plan,
      status: license.status,
      features,
      expires_at: license.current_period_end,
      stripe_subscription_id: license.stripe_subscription_id,
      created_at: license.created_at,
      updated_at: license.updated_at,
    }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (error) {
    if (error instanceof AppError) {
      return new Response(JSON.stringify(error.toResponse()), {
        status: error.statusCode,
        headers: { 'Content-Type': 'application/json' },
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
