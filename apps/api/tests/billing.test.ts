/**
 * Tests for Billing Endpoints
 *
 * POST /v1/checkout/session - Create Stripe Checkout session
 * POST /v1/billing/portal - Create Stripe Customer Portal session
 */

import { describe, it, expect, beforeAll, beforeEach, afterEach, vi } from 'vitest';
import {
  handleCreateCheckout,
  handleCreateBillingPortal,
} from '../src/handlers/billing';
import {
  createMockEnv,
  createRequest,
  parseResponse,
} from './helpers';
import type { Env } from '../src/types';
import type { ErrorResponse } from '../src/types/api';
import * as db from '../src/lib/db';
import {
  createClerkHarness,
  TEST_CLERK_ISSUER,
  TEST_CLERK_SECRET_KEY,
  type ClerkHarness,
} from './clerk-harness';

// Mock fetch for Stripe API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock the db module
vi.mock('../src/lib/db', async (importOriginal) => {
  const original = await importOriginal<typeof import('../src/lib/db')>();
  return {
    ...original,
    createDb: vi.fn(() => ({
      get: vi.fn().mockResolvedValue(null),
    })),
  };
});

const USER_ID = 'user_clerk_buyer';
const USER_EMAIL = 'test@example.com';
const ALLOWED_ORIGINS = 'https://www.replimap.com,https://replimap.com';
const authedEnvOverrides = {
  CLERK_ISSUER: TEST_CLERK_ISSUER,
  CLERK_SECRET_KEY: TEST_CLERK_SECRET_KEY,
  CHECKOUT_ALLOWED_ORIGINS: ALLOWED_ORIGINS,
};

describe('Billing Endpoints', () => {
  let env: Env;
  let clerk: ClerkHarness;
  const realFetch = globalThis.fetch;

  beforeAll(async () => {
    clerk = await createClerkHarness();
  }, 30_000);

  beforeEach(() => {
    env = createMockEnv(authedEnvOverrides);
    mockFetch.mockReset();
    // Clerk JWKS/backend stub; Stripe calls are delegated to mockFetch so the
    // tests below can keep using mockFetch.mockResolvedValueOnce(...).
    const clerkStub = clerk.installFetchStub({
      users: { [USER_ID]: USER_EMAIL },
      stripe: ((url: string, init?: RequestInit) =>
        mockFetch(url, init)) as never,
    });
    vi.stubGlobal('fetch', clerkStub);
  });

  afterEach(() => {
    vi.stubGlobal('fetch', realFetch);
  });

  /** Authenticated checkout request (token for USER_ID/USER_EMAIL by default). */
  async function checkoutRequest(
    body: Record<string, unknown>,
    opts: { token?: string | null } = {}
  ): Promise<Request> {
    const token =
      opts.token === undefined
        ? await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL })
        : opts.token;
    return createRequest(
      'POST',
      '/v1/checkout/session',
      body,
      token ? { Authorization: `Bearer ${token}` } : {}
    );
  }

  describe('POST /v1/checkout/session', () => {
    it('should reject request when Stripe is not configured', async () => {
      env = createMockEnv({ ...authedEnvOverrides, STRIPE_SECRET_KEY: undefined });

      const request = await checkoutRequest({
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(503);
      expect(data.error_code).toBe('INTERNAL_ERROR');
    });

    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/checkout/session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL })}`,
        },
        body: 'not json',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing plan', async () => {
      const request = await checkoutRequest({
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('plan');
    });

    it('rejects a malformed body email (mismatch with token) with 403', async () => {
      const request = await checkoutRequest({
        plan: 'pro',
        email: 'not-an-email',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(403);
      expect(JSON.stringify(data)).not.toContain('cs_test');
    });

    it('P2-8: rejects sovereign monthly checkout with contact-sales guidance instead of calling Stripe', async () => {
      const request = await checkoutRequest({
        plan: 'sovereign',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      // The sovereign price ids are placeholders that do not exist in
      // Stripe — forwarding the request would surface an opaque Stripe
      // error. The API must refuse it with a clear, actionable message.
      expect(response.status).toBe(400);
      expect(data.message.toLowerCase()).toContain('sovereign');
      expect(data.message.toLowerCase()).toContain('contact sales');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('P2-8: rejects sovereign annual checkout without calling Stripe', async () => {
      const request = await checkoutRequest({
        plan: 'sovereign',
        billing_period: 'annual',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message.toLowerCase()).toContain('contact sales');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('P2-8: rejects sovereign lifetime checkout without calling Stripe', async () => {
      const request = await checkoutRequest({
        plan: 'sovereign',
        billing_period: 'lifetime',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message.toLowerCase()).toContain('contact sales');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('should reject invalid plan', async () => {
      const request = await checkoutRequest({
        plan: 'invalid',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('plan');
    });

    it('should reject invalid URLs', async () => {
      const request = await checkoutRequest({
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'not-a-url',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('URL');
    });

    it('should create checkout session successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'cs_test_123',
          url: 'https://checkout.stripe.com/pay/cs_test_123',
        }),
      });

      const request = await checkoutRequest({
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await response.json() as { checkout_url: string; session_id: string };

      expect(response.status).toBe(200);
      expect(data.checkout_url).toBe('https://checkout.stripe.com/pay/cs_test_123');
      expect(data.session_id).toBe('cs_test_123');
    });

    it('should create lifetime checkout session with mode=payment', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          id: 'cs_test_lifetime_123',
          url: 'https://checkout.stripe.com/pay/cs_test_lifetime_123',
        }),
      });

      const request = await checkoutRequest({
        plan: 'pro',
        billing_period: 'lifetime',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await response.json() as { checkout_url: string };

      expect(response.status).toBe(200);
      expect(data.checkout_url).toBe('https://checkout.stripe.com/pay/cs_test_lifetime_123');

      // Verify mode=payment (one-time) was passed, not subscription
      const fetchCall = mockFetch.mock.calls[0];
      const requestBody = fetchCall[1]?.body as string;
      expect(requestBody).toContain('mode=payment');
      expect(requestBody).not.toContain('mode=subscription');
      expect(requestBody).not.toContain('subscription_data');
    });

    it('should handle Stripe API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: {
            message: 'No such price: price_internal_detail',
          },
        }),
      });
      const errorLog = vi.spyOn(console, 'error').mockImplementation(() => {});

      const request = await checkoutRequest({
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INTERNAL_ERROR');
      // Stripe's message is logged, never returned to the client.
      expect(data.message).not.toContain('price_internal_detail');
      expect(errorLog.mock.calls.some((c) => String(c[0]).includes('price_internal_detail'))).toBe(true);
      errorLog.mockRestore();
    });

    it('Stripe call has a timeout; a network failure/timeout yields 502, not 500', async () => {
      mockFetch.mockImplementationOnce(async (_url: string, init?: RequestInit) => {
        expect(init?.signal).toBeInstanceOf(AbortSignal);
        throw new DOMException('The operation was aborted due to timeout', 'TimeoutError');
      });

      const request = await checkoutRequest({
        plan: 'pro',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });
      const response = await handleCreateCheckout(request, env, '1.2.3.4');

      expect(response.status).toBe(502);
      expect(mockFetch).toHaveBeenCalledTimes(1);
    });

    it('401 (not 500) when the Clerk JWKS fetch fails or times out', async () => {
      const request = await checkoutRequest({
        plan: 'pro',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout',
      });
      vi.stubGlobal(
        'fetch',
        vi.fn(async () => {
          throw new DOMException('The operation was aborted due to timeout', 'TimeoutError');
        })
      );

      const response = await handleCreateCheckout(request, env, '1.2.3.4');

      expect(response.status).toBe(401);
    });

    describe('auth, binding and redirect allowlist', () => {
      const validBody = {
        plan: 'pro',
        success_url: 'https://www.replimap.com/checkout/success',
        cancel_url: 'https://www.replimap.com/checkout?plan=pro&billing=monthly',
      };

      function stripeOk() {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            id: 'cs_test_auth',
            url: 'https://checkout.stripe.com/pay/cs_test_auth',
          }),
        });
      }

      async function post(
        body: Record<string, unknown>,
        opts: { token?: string | null; env?: Env } = {}
      ) {
        const request = await checkoutRequest(body, opts);
        return handleCreateCheckout(request, opts.env ?? env, '1.2.3.4');
      }

      it('401 without a token and never calls Stripe', async () => {
        const res = await post(validBody, { token: null });
        expect(res.status).toBe(401);
        expect(await res.text()).not.toContain('checkout_url');
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('401 with an invalid token', async () => {
        const res = await post(validBody, { token: 'not.a.jwt' });
        expect(res.status).toBe(401);
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('503 when Clerk is not configured (fail closed)', async () => {
        const res = await post(validBody, {
          env: createMockEnv({
            CHECKOUT_ALLOWED_ORIGINS: ALLOWED_ORIGINS,
          }),
        });
        expect(res.status).toBe(503);
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('403 when the body email differs from the token email', async () => {
        const res = await post({ ...validBody, email: 'victim@example.com' });
        expect(res.status).toBe(403);
        expect(await res.text()).not.toContain('checkout_url');
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('accepts a body email that matches the token case-insensitively', async () => {
        stripeOk();
        const res = await post({ ...validBody, email: 'TEST@Example.com' });
        expect(res.status).toBe(200);
      });

      it('happy path without a body email; Stripe gets token email + Clerk user id', async () => {
        stripeOk();
        const res = await post(validBody);
        expect(res.status).toBe(200);
        const params = new URLSearchParams(
          mockFetch.mock.calls[0][1]?.body as string
        );
        expect(params.get('customer_email')).toBe(USER_EMAIL);
        expect(params.get('client_reference_id')).toBe(USER_ID);
        expect(params.get('success_url')).toContain(
          'https://www.replimap.com/checkout/success?session_id='
        );
      });

      describe('existing customer and subscription', () => {
        function existingUser(row: { customer_id: string | null; has_live_subscription: number }) {
          vi.mocked(db.createDb).mockReturnValue({
            get: vi.fn().mockResolvedValue(row),
          } as unknown as ReturnType<typeof db.createDb>);
        }

        it('reuses the stored Stripe customer instead of customer_email', async () => {
          existingUser({ customer_id: 'cus_existing', has_live_subscription: 0 });
          stripeOk();
          const res = await post(validBody);
          expect(res.status).toBe(200);
          const params = new URLSearchParams(mockFetch.mock.calls[0][1]?.body as string);
          expect(params.get('customer')).toBe('cus_existing');
          expect(params.has('customer_email')).toBe(false);
        });

        it('409 SUBSCRIPTION_EXISTS for a second subscription; Stripe is not called', async () => {
          existingUser({ customer_id: 'cus_existing', has_live_subscription: 1 });
          const res = await post({ ...validBody, plan: 'team', billing_period: 'annual' });
          const data = await parseResponse<ErrorResponse>(res);
          expect(res.status).toBe(409);
          expect(data.error_code).toBe('SUBSCRIPTION_EXISTS');
          expect(data.message).toContain('billing portal');
          expect(mockFetch).not.toHaveBeenCalled();
        });

        it('still allows a lifetime purchase by an existing subscriber, on the same customer', async () => {
          existingUser({ customer_id: 'cus_existing', has_live_subscription: 1 });
          stripeOk();
          const res = await post({ ...validBody, billing_period: 'lifetime' });
          expect(res.status).toBe(200);
          const params = new URLSearchParams(mockFetch.mock.calls[0][1]?.body as string);
          expect(params.get('mode')).toBe('payment');
          expect(params.get('customer')).toBe('cus_existing');
          // Stripe rejects customer_creation together with customer.
          expect(params.has('customer_creation')).toBe(false);
        });

        it('new buyer: customer_email + customer_creation=always for lifetime', async () => {
          existingUser({ customer_id: null, has_live_subscription: 0 });
          stripeOk();
          const res = await post({ ...validBody, billing_period: 'lifetime' });
          expect(res.status).toBe(200);
          const params = new URLSearchParams(mockFetch.mock.calls[0][1]?.body as string);
          expect(params.get('customer_email')).toBe(USER_EMAIL);
          expect(params.has('customer')).toBe(false);
          expect(params.get('customer_creation')).toBe('always');
        });
      });

      it.each([
        ['foreign success_url', { success_url: 'https://evil.com/success' }],
        ['foreign cancel_url', { cancel_url: 'https://evil.com/cancel' }],
        [
          'lookalike suffix origin',
          { success_url: 'https://www.replimap.com.evil.com/checkout/success' },
        ],
        [
          'userinfo trick',
          { cancel_url: 'https://www.replimap.com@evil.com/checkout' },
        ],
        [
          'http downgrade',
          { success_url: 'http://www.replimap.com/checkout/success' },
        ],
        [
          'different port',
          { success_url: 'https://www.replimap.com:8443/checkout/success' },
        ],
      ])('400 for %s', async (_name, override) => {
        const res = await post({ ...validBody, ...override });
        expect(res.status).toBe(400);
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('400 when the allowlist is unset (fail closed)', async () => {
        const res = await post(validBody, {
          env: createMockEnv({
            ...authedEnvOverrides,
            CHECKOUT_ALLOWED_ORIGINS: undefined,
          }),
        });
        expect(res.status).toBe(400);
        expect(mockFetch).not.toHaveBeenCalled();
      });

      it('400 when the allowlist is "*" (fail closed)', async () => {
        const res = await post(validBody, {
          env: createMockEnv({
            ...authedEnvOverrides,
            CHECKOUT_ALLOWED_ORIGINS: '*',
          }),
        });
        expect(res.status).toBe(400);
        expect(mockFetch).not.toHaveBeenCalled();
      });
    });
  });

  describe('POST /v1/billing/portal', () => {
    const RETURN_URL = 'https://www.replimap.com/dashboard';
    const KEY = 'RM-TEST-1234-5678-ABCD';

    async function portalRequest(
      body: Record<string, unknown>,
      opts: { token?: string | null } = {}
    ): Promise<Request> {
      const token =
        opts.token === undefined
          ? await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL })
          : opts.token;
      return createRequest(
        'POST',
        '/v1/billing/portal',
        body,
        token ? { Authorization: `Bearer ${token}` } : {}
      );
    }

    function dbReturns(row: unknown) {
      vi.mocked(db.createDb).mockReturnValue({
        get: vi.fn().mockResolvedValue(row),
      } as unknown as ReturnType<typeof db.createDb>);
    }

    function portalOk() {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ url: 'https://billing.stripe.com/session/test_123' }),
      });
    }

    const ownedRow = {
      stripe_subscription_id: 'sub_123',
      customer_id: 'cus_123',
      email: USER_EMAIL,
    };

    it('should reject request when Stripe is not configured', async () => {
      env = createMockEnv({ ...authedEnvOverrides, STRIPE_SECRET_KEY: undefined });
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      expect(response.status).toBe(503);
    });

    it('should reject invalid license key format', async () => {
      const request = await portalRequest({ license_key: 'invalid-key', return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);
      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_LICENSE_FORMAT');
    });

    it('should return 404 for non-existent license', async () => {
      dbReturns(null);
      const request = await portalRequest({
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        return_url: RETURN_URL,
      });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);
      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should reject license without billing account', async () => {
      dbReturns({ ...ownedRow, stripe_subscription_id: null, customer_id: null });
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);
      expect(response.status).toBe(400);
      expect(data.message).toContain('billing account');
    });

    it('should create portal session successfully for the license owner', async () => {
      dbReturns(ownedRow);
      portalOk();
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await response.json() as { portal_url: string };
      expect(response.status).toBe(200);
      expect(data.portal_url).toBe('https://billing.stripe.com/session/test_123');
      const params = new URLSearchParams(mockFetch.mock.calls[0][1]?.body as string);
      expect(params.get('customer')).toBe('cus_123');
      expect(params.get('return_url')).toBe(RETURN_URL);
    });

    it('401 with a license key but no token, and never calls Stripe', async () => {
      dbReturns(ownedRow);
      const request = await portalRequest(
        { license_key: KEY, return_url: RETURN_URL },
        { token: null }
      );
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      expect(response.status).toBe(401);
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('503 when Clerk is not configured (fail closed)', async () => {
      dbReturns(ownedRow);
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(
        request,
        createMockEnv({ CHECKOUT_ALLOWED_ORIGINS: ALLOWED_ORIGINS }),
        '1.2.3.4'
      );
      expect(response.status).toBe(503);
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it("403 when the token belongs to someone other than the license owner", async () => {
      dbReturns({ ...ownedRow, email: 'victim@example.com' });
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      expect(response.status).toBe(403);
      expect(await response.text()).not.toContain('portal_url');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('matches the owner email case-insensitively', async () => {
      dbReturns({ ...ownedRow, email: 'TEST@Example.com' });
      portalOk();
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      expect(response.status).toBe(200);
    });

    it.each([
      ['foreign origin', 'https://evil.com/dashboard'],
      ['lookalike suffix origin', 'https://www.replimap.com.evil.com/dashboard'],
      ['userinfo trick', 'https://www.replimap.com@evil.com/dashboard'],
      ['http downgrade', 'http://www.replimap.com/dashboard'],
    ])('400 for return_url on a %s', async (_name, returnUrl) => {
      dbReturns(ownedRow);
      const request = await portalRequest({ license_key: KEY, return_url: returnUrl });
      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);
      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(mockFetch).not.toHaveBeenCalled();
    });

    it('400 when the allowlist is unset (fail closed)', async () => {
      dbReturns(ownedRow);
      const request = await portalRequest({ license_key: KEY, return_url: RETURN_URL });
      const response = await handleCreateBillingPortal(
        request,
        createMockEnv({ ...authedEnvOverrides, CHECKOUT_ALLOWED_ORIGINS: undefined }),
        '1.2.3.4'
      );
      expect(response.status).toBe(400);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
