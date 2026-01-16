/**
 * Tests for Usage Endpoints
 *
 * POST /v1/usage/sync - Sync usage data
 * GET /v1/usage/{license_key} - Get usage for license
 * GET /v1/usage/{license_key}/history - Get usage history
 * POST /v1/usage/check-quota - Check quota availability
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  handleSyncUsage,
  handleGetUsage,
  handleGetUsageHistory,
  handleCheckQuota,
} from '../src/handlers/usage';
import {
  createMockEnv,
  createRequest,
  parseResponse,
  generateMachineId,
  mockLicense,
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
    logUsage: vi.fn(),
    recordUsageEvent: vi.fn(),
    getUsageForPeriod: vi.fn().mockResolvedValue({ scans: 0, resources: 0 }),
    getUsageHistory: vi.fn().mockResolvedValue([]),
    getMonthlyUsageCount: vi.fn().mockResolvedValue(0),
  };
});

describe('Usage Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    vi.clearAllMocks();
    env = createMockEnv();
  });

  describe('POST /v1/usage/sync', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/usage/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleSyncUsage(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing license_key', async () => {
      const request = createRequest('POST', '/v1/usage/sync', {
        machine_id: generateMachineId(),
        usage: { scans_count: 1 },
      });

      const response = await handleSyncUsage(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('license_key');
    });

    it('should reject missing machine_id', async () => {
      const request = createRequest('POST', '/v1/usage/sync', {
        license_key: mockLicense.license_key,
        usage: { scans_count: 1 },
      });

      const response = await handleSyncUsage(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('machine_id');
    });

    it('should reject missing usage data', async () => {
      const request = createRequest('POST', '/v1/usage/sync', {
        license_key: mockLicense.license_key,
        machine_id: generateMachineId(),
      });

      const response = await handleSyncUsage(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('usage');
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('POST', '/v1/usage/sync', {
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        machine_id: generateMachineId(),
        usage: { scans_count: 1 },
      });

      const response = await handleSyncUsage(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });
  });

  describe('GET /v1/usage/{license_key}', () => {
    it('should reject invalid license key format', async () => {
      const request = createRequest('GET', '/v1/usage/invalid-key');

      const response = await handleGetUsage(request, env, 'invalid-key', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_LICENSE_FORMAT');
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('GET', '/v1/usage/RM-XXXX-XXXX-XXXX-XXXX');

      const response = await handleGetUsage(request, env, 'RM-XXXX-XXXX-XXXX-XXXX', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
    });
  });

  describe('GET /v1/usage/{license_key}/history', () => {
    it('should reject invalid license key format', async () => {
      const request = createRequest('GET', '/v1/usage/invalid-key/history');

      const response = await handleGetUsageHistory(request, env, 'invalid-key', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('GET', '/v1/usage/RM-XXXX-XXXX-XXXX-XXXX/history');

      const response = await handleGetUsageHistory(request, env, 'RM-XXXX-XXXX-XXXX-XXXX', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
    });
  });

  describe('POST /v1/usage/check-quota', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/usage/check-quota', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleCheckQuota(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing license_key', async () => {
      const request = createRequest('POST', '/v1/usage/check-quota', {
        operation: 'scans',
      });

      const response = await handleCheckQuota(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('license_key');
    });

    it('should reject missing operation', async () => {
      const request = createRequest('POST', '/v1/usage/check-quota', {
        license_key: mockLicense.license_key,
      });

      const response = await handleCheckQuota(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('operation');
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('POST', '/v1/usage/check-quota', {
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        operation: 'scans',
      });

      const response = await handleCheckQuota(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });
  });
});
