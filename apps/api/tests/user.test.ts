/**
 * Tests for User Self-Service Endpoints
 *
 * GET /v1/me/license - Get own license details
 * GET /v1/me/machines - Get machines for own license
 * POST /v1/me/resend-key - Resend license key via email
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  handleGetOwnLicense,
  handleGetOwnMachines,
  handleResendKey,
} from '../src/handlers/user';
import {
  createMockEnv,
  createRequest,
  parseResponse,
  mockLicense,
  mockMachine,
} from './helpers';
import type { Env } from '../src/types';
import type { ErrorResponse } from '../src/types/api';

describe('User Self-Service Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  describe('GET /v1/me/license', () => {
    it('should reject request without license_key query param', async () => {
      const request = createRequest('GET', '/v1/me/license');

      const response = await handleGetOwnLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('license_key');
    });

    it('should reject invalid license key format', async () => {
      const request = createRequest('GET', '/v1/me/license?license_key=invalid');

      const response = await handleGetOwnLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_LICENSE_FORMAT');
    });

    it('should return 404 for non-existent license', async () => {
      const request = createRequest('GET', '/v1/me/license?license_key=RM-XXXX-XXXX-XXXX-XXXX');

      const response = await handleGetOwnLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should return license details for valid key', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              license_key: mockLicense.license_key,
              plan: 'pro',
              status: 'active',
              current_period_start: mockLicense.current_period_start,
              current_period_end: mockLicense.current_period_end,
              stripe_subscription_id: 'sub_123',
              created_at: mockLicense.created_at,
              active_machines: 2,
              active_aws_accounts: 1,
              id: mockLicense.id,
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('GET', `/v1/me/license?license_key=${mockLicense.license_key}`);

      const response = await handleGetOwnLicense(request, env, '1.2.3.4');
      const data = await response.json() as Record<string, unknown>;

      expect(response.status).toBe(200);
      expect(data.license_key).toBe(mockLicense.license_key);
      expect(data.plan).toBe('pro');
      expect(data.status).toBe('active');
      expect(data.features).toBeDefined();
      expect(data.usage).toBeDefined();
      expect(data.subscription).toBeDefined();
    });
  });

  describe('GET /v1/me/machines', () => {
    it('should reject request without license_key query param', async () => {
      const request = createRequest('GET', '/v1/me/machines');

      const response = await handleGetOwnMachines(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('license_key');
    });

    it('should return 404 for non-existent license', async () => {
      const request = createRequest('GET', '/v1/me/machines?license_key=RM-XXXX-XXXX-XXXX-XXXX');

      const response = await handleGetOwnMachines(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
    });

    it('should return machines list for valid license', async () => {
      let callCount = 0;
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => {
              callCount++;
              // First call: getLicenseByKey
              if (callCount === 1) {
                return { id: mockLicense.id, plan: 'pro' };
              }
              // Third call: machine changes count
              return { count: 1 };
            },
            all: async () => ({
              results: [
                {
                  machine_id: mockMachine.machine_id,
                  machine_name: 'Test Machine',
                  is_active: 1,
                  first_seen_at: mockMachine.first_seen_at,
                  last_seen_at: mockMachine.last_seen_at,
                },
              ],
              success: true,
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('GET', `/v1/me/machines?license_key=${mockLicense.license_key}`);

      const response = await handleGetOwnMachines(request, env, '1.2.3.4');
      const data = await response.json() as Record<string, unknown>;

      expect(response.status).toBe(200);
      expect(data.machines).toBeDefined();
      expect(Array.isArray(data.machines)).toBe(true);
      expect(data.active_count).toBeDefined();
      expect(data.limit).toBeDefined();
      expect(data.changes_this_month).toBeDefined();
    });

    it('should truncate machine IDs in response', async () => {
      let callCount = 0;
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => {
              callCount++;
              if (callCount === 1) return { id: mockLicense.id, plan: 'pro' };
              return { count: 0 };
            },
            all: async () => ({
              results: [
                {
                  machine_id: 'a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6',
                  machine_name: null,
                  is_active: 1,
                  first_seen_at: new Date().toISOString(),
                  last_seen_at: new Date().toISOString(),
                },
              ],
              success: true,
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('GET', `/v1/me/machines?license_key=${mockLicense.license_key}`);

      const response = await handleGetOwnMachines(request, env, '1.2.3.4');
      const data = await response.json() as { machines: Array<{ machine_id_truncated: string }> };

      expect(response.status).toBe(200);
      expect(data.machines[0].machine_id_truncated).toBe('a1b2c3d4...');
    });
  });

  describe('POST /v1/me/resend-key', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/me/resend-key', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleResendKey(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing email', async () => {
      const request = createRequest('POST', '/v1/me/resend-key', {});

      const response = await handleResendKey(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('email');
    });

    it('should reject invalid email format', async () => {
      const request = createRequest('POST', '/v1/me/resend-key', {
        email: 'not-an-email',
      });

      const response = await handleResendKey(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('email');
    });

    it('should return success even if email not found (prevent enumeration)', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            all: async () => ({
              results: [],
              success: true,
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/me/resend-key', {
        email: 'nonexistent@example.com',
      });

      const response = await handleResendKey(request, env, '1.2.3.4');
      const data = await response.json() as { sent: boolean; message: string };

      expect(response.status).toBe(200);
      expect(data.sent).toBe(true);
      expect(data.message).toContain('If an account exists');
    });

    it('should return success for existing email', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            all: async () => ({
              results: [
                {
                  license_key: mockLicense.license_key,
                  plan: 'pro',
                  status: 'active',
                },
              ],
              success: true,
            }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/me/resend-key', {
        email: 'test@example.com',
      });

      const response = await handleResendKey(request, env, '1.2.3.4');
      const data = await response.json() as { sent: boolean; message: string };

      expect(response.status).toBe(200);
      expect(data.sent).toBe(true);
    });
  });
});
