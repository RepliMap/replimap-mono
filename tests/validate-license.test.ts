/**
 * Tests for POST /v1/license/validate
 *
 * This is the HOT PATH - called on every CLI run
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { handleValidateLicense } from '../src/handlers/validate-license';
import {
  createMockEnv,
  createRequest,
  parseResponse,
  generateMachineId,
  mockLicense,
} from './helpers';
import type { Env } from '../src/types';
import type { ValidateLicenseResponse, ErrorResponse } from '../src/types/api';

describe('POST /v1/license/validate', () => {
  let env: Env;

  beforeEach(() => {
    env = createMockEnv();
  });

  describe('request validation', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.io/v1/license/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing license_key', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        machine_id: generateMachineId(),
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('license_key');
    });

    it('should reject missing machine_id', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('machine_id');
    });

    it('should reject invalid license key format', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'INVALID-KEY',
        machine_id: generateMachineId(),
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_LICENSE_FORMAT');
    });

    it('should reject invalid machine ID format', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: 'invalid-machine-id',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_MACHINE_FORMAT');
    });
  });

  describe('license lookup', () => {
    it('should return 404 for non-existent license', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        machine_id: generateMachineId(),
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
      expect(data.error_code).toBe('LICENSE_NOT_FOUND');
    });
  });

  describe('response format', () => {
    it('should include all required fields in success response', async () => {
      // Create mock DB with license data
      const mockDB = {
        prepare: (query: string) => ({
          bind: () => ({
            first: async () => ({
              license_id: mockLicense.id,
              plan: 'pro',
              status: 'active',
              current_period_end: mockLicense.current_period_end,
              machine_is_active: 1,
              active_machines: 1,
              monthly_changes: 0,
              active_aws_accounts: 1,
            }),
            all: async () => ({ results: [], success: true }),
            run: async () => ({ success: true, results: [] }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: generateMachineId(),
        cli_version: '1.0.0',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      expect(response.status).toBe(200);
      expect(data.valid).toBe(true);
      expect(data.plan).toBe('pro');
      expect(data.status).toBe('active');
      expect(data.features).toBeDefined();
      expect(data.features.resources_per_scan).toBe(-1); // unlimited for pro
      expect(data.features.machines).toBe(3);
      expect(data.usage).toBeDefined();
      expect(data.cache_until).toBeDefined();
      expect(data.cli_version).toBeDefined();
      expect(data.cli_version?.status).toBe('ok');
    });
  });

  describe('CLI version check', () => {
    it('should return ok for current version', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              license_id: mockLicense.id,
              plan: 'pro',
              status: 'active',
              current_period_end: mockLicense.current_period_end,
              machine_is_active: 1,
              active_machines: 1,
              monthly_changes: 0,
              active_aws_accounts: 0,
            }),
            all: async () => ({ results: [], success: true }),
            run: async () => ({ success: true, results: [] }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: generateMachineId(),
        cli_version: '1.0.0',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      expect(data.cli_version?.status).toBe('ok');
    });

    it('should return deprecated for old versions', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              license_id: mockLicense.id,
              plan: 'pro',
              status: 'active',
              current_period_end: mockLicense.current_period_end,
              machine_is_active: 1,
              active_machines: 1,
              monthly_changes: 0,
              active_aws_accounts: 0,
            }),
            all: async () => ({ results: [], success: true }),
            run: async () => ({ success: true, results: [] }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: generateMachineId(),
        cli_version: '0.9.0', // deprecated version
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      expect(data.cli_version?.status).toBe('deprecated');
      expect(data.cli_version?.message).toBeDefined();
    });

    it('should return unsupported for very old versions', async () => {
      const mockDB = {
        prepare: () => ({
          bind: () => ({
            first: async () => ({
              license_id: mockLicense.id,
              plan: 'pro',
              status: 'active',
              current_period_end: mockLicense.current_period_end,
              machine_is_active: 1,
              active_machines: 1,
              monthly_changes: 0,
              active_aws_accounts: 0,
            }),
            all: async () => ({ results: [], success: true }),
            run: async () => ({ success: true, results: [] }),
          }),
        }),
      } as unknown as D1Database;

      env = createMockEnv({ DB: mockDB });

      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: generateMachineId(),
        cli_version: '0.1.0', // unsupported version
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      expect(data.cli_version?.status).toBe('unsupported');
    });
  });
});
