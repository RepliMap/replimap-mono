/**
 * API Client for License Management
 *
 * Communicates with the RepliMap backend API for license operations.
 */

import type {
  LicenseDetails,
  LicenseUsage,
  DeactivateRequest,
  DeactivateResponse,
  ApiErrorResponse,
} from '@/types/license';

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'https://api.replimap.com';

/**
 * API Error class with structured error information
 */
export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic request function with error handling
 */
async function request<T>(
  endpoint: string,
  options: RequestInit & { licenseKey?: string } = {}
): Promise<T> {
  const { licenseKey, ...fetchOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  if (licenseKey) {
    (headers as Record<string, string>)['X-License-Key'] = licenseKey;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  let data: T | ApiErrorResponse;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(
      'PARSE_ERROR',
      'Failed to parse response',
      response.status
    );
  }

  if (!response.ok) {
    const errorData = data as ApiErrorResponse;
    throw new ApiError(
      errorData.error || 'UNKNOWN_ERROR',
      errorData.message || 'An error occurred',
      response.status,
      errorData.details
    );
  }

  return data as T;
}

/**
 * Get license details for the authenticated user
 *
 * @param licenseKey - The user's license key
 * @returns License details including plan, status, and devices
 */
export async function getLicenseDetails(
  licenseKey: string
): Promise<LicenseDetails> {
  return request<LicenseDetails>('/v1/me/license', {
    method: 'GET',
    licenseKey,
    cache: 'no-store',
  });
}

/**
 * Get license usage statistics
 *
 * @param licenseKey - The user's license key
 * @returns Usage statistics
 */
export async function getLicenseUsage(
  licenseKey: string
): Promise<LicenseUsage> {
  return request<LicenseUsage>('/v1/me/usage', {
    method: 'GET',
    licenseKey,
    cache: 'no-store',
  });
}

/**
 * Deactivate a device from the license
 *
 * @param data - License key and fingerprint to deactivate
 * @returns Deactivation result
 */
export async function deactivateDevice(
  data: DeactivateRequest
): Promise<DeactivateResponse> {
  return request<DeactivateResponse>('/v1/license/deactivate', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

/**
 * Get the user's license key, provisioning a free community license on
 * first call. The API is idempotent — safe to call on every dashboard
 * load. Paid licenses are never overwritten.
 *
 * @param email - The authenticated user's email (from Clerk)
 * @returns License key, or null on API failure
 */
export async function getOrProvisionLicenseKey(
  email: string
): Promise<string | null> {
  try {
    const response = await provisionCommunityLicense(email);
    return response.license_key;
  } catch {
    return null;
  }
}

// ============================================================================
// Checkout / Billing
// ============================================================================

interface CreateCheckoutRequest {
  plan: 'pro' | 'team' | 'sovereign';
  billing_period: 'monthly' | 'annual' | 'lifetime';
  email: string;
  success_url: string;
  cancel_url: string;
}

interface CreateCheckoutResponse {
  checkout_url: string;
  session_id: string;
}

/**
 * Create a Stripe Checkout session
 *
 * @param data - Checkout request with plan, billing period, email, and redirect URLs
 * @returns Checkout URL to redirect the user to Stripe
 */
export async function createCheckoutSession(
  data: CreateCheckoutRequest
): Promise<CreateCheckoutResponse> {
  return request<CreateCheckoutResponse>('/v1/checkout/session', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

interface CreatePortalResponse {
  portal_url: string;
}

/**
 * Create a Stripe Customer Portal session for subscription management
 *
 * @param licenseKey - The user's license key
 * @param returnUrl - URL to redirect back to after portal
 * @returns Portal URL to redirect the user to Stripe
 */
export async function createBillingPortalSession(
  licenseKey: string,
  returnUrl: string
): Promise<CreatePortalResponse> {
  return request<CreatePortalResponse>('/v1/billing/portal', {
    method: 'POST',
    body: JSON.stringify({ license_key: licenseKey, return_url: returnUrl }),
  });
}

// ============================================================================
// Post-checkout license lookup
// ============================================================================

export interface CheckoutLicenseResponse {
  license_key: string;
  plan: string;
  status: string;
  plan_type?: string;
}

/**
 * Fetch the license created by a completed Stripe Checkout Session.
 *
 * Returns 404 (as ApiError) while the webhook is still in flight — callers
 * should poll with backoff until the license is ready or a timeout elapses.
 *
 * @param sessionId - The Stripe session ID returned in the success_url
 */
export async function getCheckoutLicense(
  sessionId: string
): Promise<CheckoutLicenseResponse> {
  return request<CheckoutLicenseResponse>(
    `/v1/checkout/session/${encodeURIComponent(sessionId)}/license`,
    {
      method: 'GET',
      cache: 'no-store',
    }
  );
}

// ============================================================================
// Community tier auto-provisioning
// ============================================================================

export interface ProvisionCommunityResponse {
  license_key: string;
  plan: string;
  status: string;
  created: boolean;
}

/**
 * Create (or return the existing) community license for an email address.
 * Idempotent — safe to call on every dashboard load. Never overwrites a
 * paid license; if the user already has one, the existing license is
 * returned with `created: false`.
 */
export async function provisionCommunityLicense(
  email: string
): Promise<ProvisionCommunityResponse> {
  return request<ProvisionCommunityResponse>(
    '/v1/license/provision-community',
    {
      method: 'POST',
      body: JSON.stringify({ email }),
    }
  );
}

// ============================================================================
// Helpers
// ============================================================================

/**
 * Machine limit by plan
 */
export function getMachinesLimit(plan: string): number {
  const limits: Record<string, number> = {
    community: 1,
    pro: 2,
    team: 10,
    sovereign: -1, // Unlimited
  };
  return limits[plan] ?? 1;
}

/**
 * Offline grace days by plan
 */
export function getOfflineGraceDays(plan: string): number {
  const days: Record<string, number> = {
    community: 0,
    pro: 7,
    team: 14,
    sovereign: 365,
  };
  return days[plan] ?? 0;
}
