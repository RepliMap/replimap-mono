/**
 * Tests for Admin Endpoints
 *
 * POST /v1/admin/licenses - Create license
 * GET /v1/admin/licenses/{key} - Get license details
 * POST /v1/admin/licenses/{key}/revoke - Revoke license
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  handleCreateLicense,
  handleGetLicense,
  handleRevokeLicense,
} from '../src/handlers/admin';
import {
  createMockEnv,
  createRequest,
  parseResponse,
} from './helpers';
import type { Env } from '../src/types';
import type { ErrorResponse } from '../src/types/api';

describe('Admin Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  describe('POST /v1/admin/licenses', () => {
    it('should reject request without API key', async () => {
      const request = createRequest('POST', '/v1/admin/licenses', {
        email: 'test@example.com',
        plan: 'pro',
      });

      const response = await handleCreateLicense(request, env);
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(401);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject request with invalid API key', async () => {
      const request = createRequest('POST', '/v1/admin/licenses', {
        email: 'test@example.com',
        plan: 'pro',
      }, {
        'X-API-Key': 'wrong-key',
      });

      const response = await handleCreateLicense(request, env);
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(403);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.io/v1/admin/licenses', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': 'test-admin-key',
        },
        body: 'not json',
      });

      const response = await handleCreateLicense(request, env);
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing email', async () => {
      const request = createRequest('POST', '/v1/admin/licenses', {
        plan: 'pro',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleCreateLicense(request, env);
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('customer_email');
    });

    it('should reject invalid plan', async () => {
      const request = createRequest('POST', '/v1/admin/licenses', {
        customer_email: 'test@example.com',
        plan: 'invalid-plan',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleCreateLicense(request, env);
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should create license with valid request', async () => {
      let firstCallCount = 0;
      const now = new Date().toISOString();
      const mockDB = {
        prepare: (query: string) => ({
          bind: (...args: unknown[]) => ({
            first: async () => {
              firstCallCount++;
              // First call: check existing user (SELECT ... FROM users WHERE email = ?)
              if (firstCallCount === 1) {
                return null; // No existing user
              }
              // Second call: return created user (SELECT * FROM users WHERE id = ?)
              if (firstCallCount === 2) {
                return {
                  id: 'user_test_123',
                  email: 'test@example.com',
                  stripe_customer_id: null,
                  created_at: now,
                  updated_at: now,
                };
              }
              // Third call: return created license (SELECT * FROM licenses WHERE id = ?)
              // The createLicense function uses: bind(id, userId, licenseKey, ...)
              // So args[2] is the license key in INSERT, but for SELECT it's just the id
              return {
                id: 'lic_test_123',
                user_id: 'user_test_123',
                license_key: 'RM-TEST-1234-5678-ABCD', // Use fixed test key
                plan: 'pro',
                status: 'active',
                current_period_start: now,
                current_period_end: null,
                created_at: now,
                updated_at: now,
              };
            },
            run: async () => ({ success: true, results: [], meta: { last_row_id: 1, changes: 1 } }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/admin/licenses', {
        customer_email: 'test@example.com',
        plan: 'pro',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleCreateLicense(request, env);
      const data = await response.json() as { license_key: string; plan: string };

      expect(response.status).toBe(201);
      expect(data.license_key).toMatch(/^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
      expect(data.plan).toBe('pro');
    });
  });

  describe('GET /v1/admin/licenses/{key}', () => {
    it('should reject request without API key', async () => {
      const request = createRequest('GET', '/v1/admin/licenses/RM-TEST-1234-5678-ABCD');

      const response = await handleGetLicense(request, env, 'RM-TEST-1234-5678-ABCD');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(401);
    });

    it('should return 404 for non-existent license', async () => {
      const request = createRequest('GET', '/v1/admin/licenses/RM-XXXX-XXXX-XXXX-XXXX', undefined, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleGetLicense(request, env, 'RM-XXXX-XXXX-XXXX-XXXX');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should return license details for valid key', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              id: 'lic_123',
              license_key: 'RM-TEST-1234-5678-ABCD',
              plan: 'pro',
              status: 'active',
              current_period_start: new Date().toISOString(),
              current_period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
              email: 'test@example.com',
              stripe_customer_id: 'cus_123',
              stripe_subscription_id: 'sub_123',
              created_at: new Date().toISOString(),
              active_machines: 2,
              active_aws_accounts: 1,
            }),
            all: async () => ({ results: [], success: true }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('GET', '/v1/admin/licenses/RM-TEST-1234-5678-ABCD', undefined, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleGetLicense(request, env, 'RM-TEST-1234-5678-ABCD');
      const data = await response.json() as Record<string, unknown>;

      expect(response.status).toBe(200);
      expect(data.license_key).toBe('RM-TEST-1234-5678-ABCD');
      expect(data.plan).toBe('pro');
      expect(data.status).toBe('active');
    });
  });

  describe('POST /v1/admin/licenses/{key}/revoke', () => {
    it('should reject request without API key', async () => {
      const request = createRequest('POST', '/v1/admin/licenses/RM-TEST-1234-5678-ABCD/revoke');

      const response = await handleRevokeLicense(request, env, 'RM-TEST-1234-5678-ABCD');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(401);
    });

    it('should return 404 for non-existent license', async () => {
      const request = createRequest('POST', '/v1/admin/licenses/RM-XXXX-XXXX-XXXX-XXXX/revoke', {
        reason: 'Test revocation',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleRevokeLicense(request, env, 'RM-XXXX-XXXX-XXXX-XXXX');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should revoke license successfully', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              id: 'lic_123',
              status: 'active',
            }),
            run: async () => ({ success: true, results: [] }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/admin/licenses/RM-TEST-1234-5678-ABCD/revoke', {
        reason: 'Fraud detected',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleRevokeLicense(request, env, 'RM-TEST-1234-5678-ABCD');
      const data = await response.json() as { revoked: boolean };

      expect(response.status).toBe(200);
      expect(data.revoked).toBe(true);
    });
  });
});
