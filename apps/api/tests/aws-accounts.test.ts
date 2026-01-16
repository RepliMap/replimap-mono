/**
 * Tests for AWS Account Endpoints
 *
 * POST /v1/aws-accounts/track - Track AWS account usage
 * GET /v1/licenses/{key}/aws-accounts - Get AWS accounts for license
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  handleTrackAwsAccount,
  handleGetAwsAccounts,
} from '../src/handlers/aws-accounts';
import {
  createMockEnv,
  createRequest,
  parseResponse,
  generateAwsAccountId,
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
    trackAwsAccount: vi.fn(),
    getActiveAwsAccountCount: vi.fn().mockResolvedValue(0),
    getAwsAccountsForLicense: vi.fn().mockResolvedValue([]),
  };
});

describe('AWS Account Endpoints', () => {
  let env: Env;

  beforeEach(() => {
    vi.clearAllMocks();
    env = createMockEnv();
  });

  describe('POST /v1/aws-accounts/track', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/aws-accounts/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: 'not json',
      });

      const response = await handleTrackAwsAccount(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
    });

    it('should reject missing license_key', async () => {
      const request = createRequest('POST', '/v1/aws-accounts/track', {
        aws_account_id: generateAwsAccountId(),
      });

      const response = await handleTrackAwsAccount(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('license_key');
    });

    it('should reject missing aws_account_id', async () => {
      const request = createRequest('POST', '/v1/aws-accounts/track', {
        license_key: mockLicense.license_key,
      });

      const response = await handleTrackAwsAccount(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.message).toContain('aws_account_id');
    });

    it('should reject invalid AWS account ID format', async () => {
      const request = createRequest('POST', '/v1/aws-accounts/track', {
        license_key: mockLicense.license_key,
        aws_account_id: 'invalid',
      });

      const response = await handleTrackAwsAccount(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('POST', '/v1/aws-accounts/track', {
        license_key: 'RM-XXXX-XXXX-XXXX-XXXX',
        aws_account_id: generateAwsAccountId(),
      });

      const response = await handleTrackAwsAccount(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
    });
  });

  describe('GET /v1/licenses/{key}/aws-accounts', () => {
    it('should reject invalid license key format', async () => {
      const request = createRequest('GET', '/v1/licenses/invalid-key/aws-accounts');

      const response = await handleGetAwsAccounts(request, env, 'invalid-key', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
    });

    it('should return 404 for non-existent license', async () => {
      vi.mocked(db.getLicenseByKey).mockResolvedValue(null);

      const request = createRequest('GET', '/v1/licenses/RM-XXXX-XXXX-XXXX-XXXX/aws-accounts');

      const response = await handleGetAwsAccounts(request, env, 'RM-XXXX-XXXX-XXXX-XXXX', '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(404);
    });
  });
});
