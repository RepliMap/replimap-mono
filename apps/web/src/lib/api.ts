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
 * Get the user's license key from their profile
 *
 * This would typically fetch from a user-license mapping endpoint
 * or from Clerk user metadata.
 *
 * @param userId - Clerk user ID
 * @returns License key or null if not found
 */
export async function getUserLicenseKey(
  userId: string
): Promise<string | null> {
  try {
    const response = await request<{ license_key: string | null }>(
      `/v1/users/${userId}/license-key`,
      { method: 'GET' }
    );
    return response.license_key;
  } catch {
    // User may not have a license yet
    return null;
  }
}

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
