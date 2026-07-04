/**
 * Unit tests for the dashboard license-key acquisition path.
 *
 * P0 auth fix: the client forwards the Clerk session token (never an email);
 * a missing token short-circuits to an error without calling the API.
 *
 * P2-12: getOrProvisionLicenseKey must distinguish "the backend answered"
 * from "the request failed" — a network/API failure must NOT silently render
 * the same as a user without a license.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { getOrProvisionLicenseKey } from './api';

function okResponse() {
  return new Response(
    JSON.stringify({
      license_key: 'RM-AAAA-BBBB-CCCC-DDDD',
      plan: 'community',
      status: 'active',
      created: true,
    }),
    { status: 201, headers: { 'Content-Type': 'application/json' } }
  );
}

describe('getOrProvisionLicenseKey', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
  });

  it('forwards the Clerk token as a bearer header and sends no email in the body', async () => {
    const fetchSpy = vi.fn(async () => okResponse());
    vi.stubGlobal('fetch', fetchSpy);

    const result = await getOrProvisionLicenseKey('clerk_session_token_xyz');

    expect(result).toEqual({
      status: 'ok',
      licenseKey: 'RM-AAAA-BBBB-CCCC-DDDD',
    });

    expect(fetchSpy).toHaveBeenCalledTimes(1);
    const [, init] = fetchSpy.mock.calls[0] as unknown as [string, RequestInit];
    const headers = init.headers as Record<string, string>;
    expect(headers['Authorization']).toBe('Bearer clerk_session_token_xyz');
    // No email leaves the client — the backend derives it from the token.
    expect(init.body).toBe('{}');
  });

  it('P0: returns an error without calling the API when there is no token', async () => {
    const fetchSpy = vi.fn(async () => okResponse());
    vi.stubGlobal('fetch', fetchSpy);

    const result = await getOrProvisionLicenseKey(null);

    expect(result.status).toBe('error');
    expect(fetchSpy).not.toHaveBeenCalled();
  });

  it('P2-12 regression: reports an error (not a silent null) when the API is down', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('fetch failed');
      })
    );

    const result = await getOrProvisionLicenseKey('clerk_session_token_xyz');
    expect(result.status).toBe('error');
    if (result.status === 'error') {
      expect(result.message.length).toBeGreaterThan(0);
    }
  });

  it('P2-12 regression: reports an error when the API responds 5xx', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ error: 'INTERNAL_ERROR' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    );

    const result = await getOrProvisionLicenseKey('clerk_session_token_xyz');
    expect(result.status).toBe('error');
  });
});
