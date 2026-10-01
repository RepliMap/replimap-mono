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
import {
  ApiError,
  classifyCheckoutLookupError,
  createCheckoutSession,
  getCheckoutLicense,
  getOrProvisionLicenseKey,
} from './api';

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

describe('checkout API client auth', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('getCheckoutLicense sends the bearer token', async () => {
    const fetchSpy = vi.fn(async () => okResponse());
    vi.stubGlobal('fetch', fetchSpy);

    await getCheckoutLicense('cs_test_abc', 'tok_1');

    const [url, init] = fetchSpy.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toContain('/v1/checkout/session/cs_test_abc/license');
    expect((init.headers as Record<string, string>)['Authorization']).toBe(
      'Bearer tok_1'
    );
  });

  it('getCheckoutLicense uses the token it is given on each call (no caching)', async () => {
    const fetchSpy = vi.fn(async () => okResponse());
    vi.stubGlobal('fetch', fetchSpy);

    await getCheckoutLicense('cs_test_abc', 'tok_1');
    await getCheckoutLicense('cs_test_abc', 'tok_2');

    const auth = (i: number) =>
      (
        (fetchSpy.mock.calls[i] as unknown as [string, RequestInit])[1]
          .headers as Record<string, string>
      )['Authorization'];
    expect(auth(0)).toBe('Bearer tok_1');
    expect(auth(1)).toBe('Bearer tok_2');
  });

  it('createCheckoutSession sends the bearer token and keeps the body email', async () => {
    const fetchSpy = vi.fn(
      async () =>
        new Response(
          JSON.stringify({ checkout_url: 'https://stripe.test/x', session_id: 'cs_test_1' }),
          { status: 200 }
        )
    );
    vi.stubGlobal('fetch', fetchSpy);

    await createCheckoutSession(
      {
        plan: 'pro',
        billing_period: 'monthly',
        email: 'a@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      },
      'tok_c'
    );

    const [, init] = fetchSpy.mock.calls[0] as unknown as [string, RequestInit];
    expect((init.headers as Record<string, string>)['Authorization']).toBe(
      'Bearer tok_c'
    );
    expect(JSON.parse(init.body as string).email).toBe('a@example.com');
  });

  it('omits Authorization when no token is available', async () => {
    const fetchSpy = vi.fn(async () => okResponse());
    vi.stubGlobal('fetch', fetchSpy);

    await getCheckoutLicense('cs_test_abc', null);

    const [, init] = fetchSpy.mock.calls[0] as unknown as [string, RequestInit];
    expect((init.headers as Record<string, string>)['Authorization']).toBeUndefined();
  });
});

describe('classifyCheckoutLookupError', () => {
  it('404 NOT_READY is not-ready (keep polling)', () => {
    expect(classifyCheckoutLookupError(new ApiError('NOT_READY', 'x', 404))).toBe('not-ready');
  });

  it('5xx and transport errors are transient (keep polling)', () => {
    expect(classifyCheckoutLookupError(new ApiError('E', 'x', 500))).toBe('transient');
    expect(classifyCheckoutLookupError(new ApiError('E', 'x', 502))).toBe('transient');
    expect(classifyCheckoutLookupError(new ApiError('E', 'x', 503))).toBe('transient');
    expect(classifyCheckoutLookupError(new TypeError('network'))).toBe('transient');
  });

  it('401 and 403 are auth errors (stop immediately)', () => {
    expect(classifyCheckoutLookupError(new ApiError('UNAUTHORIZED', 'x', 401))).toBe('auth');
    expect(classifyCheckoutLookupError(new ApiError('FORBIDDEN', 'x', 403))).toBe('auth');
  });

  it('other 4xx are fatal', () => {
    expect(classifyCheckoutLookupError(new ApiError('E', 'x', 400))).toBe('fatal');
  });
});
