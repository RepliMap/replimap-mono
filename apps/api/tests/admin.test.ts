/**
 * Tests for Admin Endpoints
 *
 * POST /v1/admin/licenses - Create license
 * GET /v1/admin/licenses/{key} - Get license details
 * POST /v1/admin/licenses/{key}/revoke - Revoke license
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
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
import * as db from '../src/lib/db';

// Mock the db module
vi.mock('../src/lib/db', async (importOriginal) => {
  const original = await importOriginal<typeof import('../src/lib/db')>();
  return {
    ...original,
    getLicenseByKey: vi.fn(),
    getLicenseWithUserDetails: vi.fn(),
    createLicense: vi.fn(),
    revokeLicense: vi.fn(),
    findOrCreateUser: vi.fn(),
    getActiveMachines: vi.fn().mockResolvedValue([]),
    getActiveAwsAccountCount: vi.fn().mockResolvedValue(0),
  };
});

describe('Admin Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    vi.clearAllMocks();
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
      expect(data.error_code).toBe('UNAUTHORIZED');
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
      expect(data.error_code).toBe('UNAUTHORIZED');
    });

    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/admin/licenses', {
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
      const now = new Date().toISOString();

      // Mock user creation
      vi.mocked(db.findOrCreateUser).mockResolvedValue({
        id: 'user_test_123',
        email: 'test@example.com',
        customerId: null,
        createdAt: new Date(now),
        updatedAt: new Date(now),
      });

      // Mock license creation
      vi.mocked(db.createLicense).mockResolvedValue({
        id: 'lic_test_123',
        userId: 'user_test_123',
        licenseKey: 'RM-TEST-1234-5678-ABCD',
        plan: 'pro',
        planType: 'monthly',
        status: 'active',
        currentPeriodStart: now,
        currentPeriodEnd: null,
        stripeSubscriptionId: null,
        stripePriceId: null,
        stripeSessionId: null,
        createdAt: now,
        updatedAt: now,
        canceledAt: null,
        revokedAt: null,
        revokedReason: null,
      });

      const request = createRequest('POST', '/v1/admin/licenses', {
        customer_email: 'test@example.com',
        plan: 'pro',
      }, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleCreateLicense(request, env);
      const data = await response.json() as { license_key: string; plan: string };

      expect(response.status).toBe(201);
      expect(data.license_key).toBe('RM-TEST-1234-5678-ABCD');
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
      vi.mocked(db.getLicenseWithUserDetails).mockResolvedValue(null);

      const request = createRequest('GET', '/v1/admin/licenses/RM-XXXX-XXXX-XXXX-XXXX', undefined, {
        'X-API-Key': 'test-admin-key',
      });

      const response = await handleGetLicense(request, env, 'RM-XXXX-XXXX-XXXX-XXXX');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });

    it('should return license details for valid key', async () => {
      // Mock getLicenseByKey (not getLicenseWithUserDetails)
      vi.mocked(db.getLicenseByKey).mockResolvedValue({
        id: 'lic_123',
        userId: 'user_123',
        licenseKey: 'RM-TEST-1234-5678-ABCD',
        plan: 'pro',
        planType: 'monthly',
        status: 'active',
        currentPeriodStart: new Date().toISOString(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        stripeSubscriptionId: 'sub_123',
        stripePriceId: null,
        stripeSessionId: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        canceledAt: null,
        revokedAt: null,
        revokedReason: null,
      });

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
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

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
      vi.mocked(db.getLicenseByKey).mockResolvedValue({
        id: 'lic_123',
        userId: 'user_123',
        licenseKey: 'RM-TEST-1234-5678-ABCD',
        plan: 'pro',
        planType: 'monthly',
        status: 'active',
        currentPeriodStart: new Date().toISOString(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
        stripeSubscriptionId: null,
        stripePriceId: null,
        stripeSessionId: null,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        canceledAt: null,
        revokedAt: null,
        revokedReason: null,
      });
      vi.mocked(db.revokeLicense).mockResolvedValue(undefined);

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
