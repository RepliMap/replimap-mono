/**
 * API Client for License Management
 *
 * Communicates with the RepliMap backend API for license operations.
 */

import type {
  LicenseDetails,
  MachinesResponse,
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
  options: RequestInit & { licenseKey?: string; authToken?: string } = {}
): Promise<T> {
  const { licenseKey, authToken, ...fetchOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  if (licenseKey) {
    (headers as Record<string, string>)['X-License-Key'] = licenseKey;
  }

  if (authToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${authToken}`;
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
 * The API accepts the license key as a `?license_key=` query param
 * (see handleGetOwnLicense).
 *
 * @param licenseKey - The user's license key
 * @returns License details including plan, status, and devices
 */
export async function getLicenseDetails(
  licenseKey: string
): Promise<LicenseDetails> {
  const qs = new URLSearchParams({ license_key: licenseKey }).toString();
  return request<LicenseDetails>(`/v1/me/license?${qs}`, {
    method: 'GET',
    cache: 'no-store',
  });
}

/**
 * Get the devices activated on a license.
 *
 * Like getLicenseDetails, this runs browser-side (see useMachines) so the
 * request comes from the user's own IP — Cloudflare Bot Fight Mode blocks
 * Vercel SSR egress. Owner-scoped by license-key possession: the API only
 * ever returns machines belonging to the presented key's license.
 */
export async function getMachines(
  licenseKey: string
): Promise<MachinesResponse> {
  const qs = new URLSearchParams({ license_key: licenseKey }).toString();
  return request<MachinesResponse>(`/v1/me/machines?${qs}`, {
    method: 'GET',
    cache: 'no-store',
  });
}

/**
 * Deactivate a device from the license.
 *
 * @param data - License key and full machine_id to deactivate
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
 * Result of license-key acquisition: a failure to reach the API must be
 * distinguishable from "this user has no license" so the dashboard can show
 * an actionable error instead of silently degrading to the empty state.
 */
export type LicenseKeyResult =
  | { status: 'ok'; licenseKey: string }
  | { status: 'error'; message: string };

/**
 * Get the user's license key, provisioning a free community license on
 * first call. The API is idempotent — safe to call on every dashboard
 * load. Paid licenses are never overwritten.
 *
 * @param authToken - The caller's Clerk session token (from auth().getToken()).
 *   The backend derives the account email from this token — it is never taken
 *   from the client — so a user can only provision/retrieve their own license.
 * @returns ok + license key, or error + user-facing message on API failure
 */
export async function getOrProvisionLicenseKey(
  authToken: string | null
): Promise<LicenseKeyResult> {
  if (!authToken) {
    return {
      status: 'error',
      message:
        'Your session has expired. Please sign in again to load your license.',
    };
  }
  try {
    const response = await provisionCommunityLicense(authToken);
    return { status: 'ok', licenseKey: response.license_key };
  } catch (error) {
    console.error('[api] provision-community failed:', error);
    return {
      status: 'error',
      message:
        'We could not load your license right now. Please refresh in a ' +
        'moment — if this keeps happening, contact support@replimap.com.',
    };
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
 * Create (or return the existing) community license for the authenticated
 * caller. Idempotent — safe to call on every dashboard load. Never overwrites
 * a paid license; if the user already has one, the existing license is
 * returned with `created: false`.
 *
 * The account is identified by the Clerk session token (forwarded as a bearer
 * token); no email is sent from the client.
 */
export async function provisionCommunityLicense(
  authToken: string
): Promise<ProvisionCommunityResponse> {
  // Called from the browser (see useLicense), so the request originates from
  // the user's own IP — Cloudflare Bot Fight Mode challenges Vercel's
  // server-side egress (cloud ASN), not real browser traffic. Identity comes
  // solely from the Clerk bearer token; no email is sent from the client.
  return request<ProvisionCommunityResponse>(
    '/v1/license/provision-community',
    {
      method: 'POST',
      body: JSON.stringify({}),
      authToken,
    }
  );
}

// NOTE: the old getMachinesLimit(plan) helper was deliberately removed — the
// per-plan device cap is server-issued (usage.machines_limit on /v1/me/license
// and `limit` on /v1/me/machines). Never re-derive entitlements from the plan
// name in the frontend.

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
