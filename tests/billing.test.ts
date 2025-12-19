/**
 * Tests for Billing Endpoints
 *
 * POST /v1/checkout/session - Create Stripe Checkout session
 * POST /v1/billing/portal - Create Stripe Customer Portal session
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
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

// Mock fetch for Stripe API calls
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('Billing Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
    mockFetch.mockReset();
  });

  describe('POST /v1/checkout/session', () => {
    it('should reject request when Stripe is not configured', async () => {
      env = createMockEnv({ STRIPE_SECRET_KEY: undefined });

      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(503);
      expect(data.error_code).toBe('INTERNAL_ERROR');
    });

    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.io/v1/checkout/session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing plan', async () => {
      const request = createRequest('POST', '/v1/checkout/session', {
        email: 'test@example.com',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('plan');
    });

    it('should reject missing email', async () => {
      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('email');
    });

    it('should reject invalid email format', async () => {
      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        email: 'not-an-email',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('email');
    });

    it('should reject invalid plan', async () => {
      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'invalid',
        email: 'test@example.com',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('plan');
    });

    it('should reject invalid URLs', async () => {
      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'not-a-url',
        cancel_url: 'https://example.com/cancel',
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

      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await response.json() as { checkout_url: string; session_id: string };

      expect(response.status).toBe(200);
      expect(data.checkout_url).toBe('https://checkout.stripe.com/pay/cs_test_123');
      expect(data.session_id).toBe('cs_test_123');
    });

    it('should handle Stripe API errors', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({
          error: {
            message: 'Invalid request',
          },
        }),
      });

      const request = createRequest('POST', '/v1/checkout/session', {
        plan: 'pro',
        email: 'test@example.com',
        success_url: 'https://example.com/success',
        cancel_url: 'https://example.com/cancel',
      });

      const response = await handleCreateCheckout(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INTERNAL_ERROR');
    });
  });

  describe('POST /v1/billing/portal', () => {
    it('should reject request when Stripe is not configured', async () => {
      env = createMockEnv({ STRIPE_SECRET_KEY: undefined });

      const request = createRequest('POST', '/v1/billing/portal', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        return_url: 'https://example.com/dashboard',
      });

      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(503);
    });

    it('should reject invalid license key format', async () => {
      const request = createRequest('POST', '/v1/billing/portal', {
        license_key: 'invalid-key',
        return_url: 'https://example.com/dashboard',
      });

      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_LICENSE_FORMAT');
    });

    it('should return 404 for non-existent license', async () => {
      const request = createRequest('POST', '/v1/billing/portal', {
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        return_url: 'https://example.com/dashboard',
      });

      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should reject license without billing account', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              stripe_subscription_id: null,
              stripe_customer_id: null, // No billing account
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/billing/portal', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        return_url: 'https://example.com/dashboard',
      });

      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('billing account');
    });

    it('should create portal session successfully', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              stripe_subscription_id: 'sub_123',
              stripe_customer_id: 'cus_123',
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          url: 'https://billing.stripe.com/session/test_123',
        }),
      });

      const request = createRequest('POST', '/v1/billing/portal', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        return_url: 'https://example.com/dashboard',
      });

      const response = await handleCreateBillingPortal(request, env, '1.2.3.4');
      const data = await response.json() as { portal_url: string };

      expect(response.status).toBe(200);
      expect(data.portal_url).toBe('https://billing.stripe.com/session/test_123');
    });
  });
});
