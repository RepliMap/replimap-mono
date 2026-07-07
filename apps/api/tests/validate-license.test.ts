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
  TEST_LICENSE_SIGNING_PUBLIC_KEY_PEM,
} from './helpers';
import type { Env } from '../src/types';
import type { ValidateLicenseResponse, ErrorResponse } from '../src/types/api';
import * as db from '../src/lib/db';

// Mock the db module
vi.mock('../src/lib/db', async (importOriginal) => {
  const original = await importOriginal<typeof import('../src/lib/db')>();
  return {
    ...original,
    getLicenseForValidation: vi.fn(),
    getActiveDeviceCount: vi.fn().mockResolvedValue(1),
    getNewDeviceCount: vi.fn().mockResolvedValue(0),
    getActiveCIDeviceCount: vi.fn().mockResolvedValue(0),
    updateMachineLastSeen: vi.fn().mockResolvedValue(undefined),
    registerMachine: vi.fn().mockResolvedValue(undefined),
    recordMachineChange: vi.fn().mockResolvedValue(undefined),
    logUsage: vi.fn().mockResolvedValue(undefined),
    getMonthlyUsageCount: vi.fn().mockResolvedValue(0),
    getActiveMachines: vi.fn().mockResolvedValue([]),
  };
});

// ============================================================================
// License Blob Verification Helpers (contract §1/§4 — base64url + SPKI PEM)
// ============================================================================

function base64UrlDecode(str: string): Uint8Array {
  const padded = str.replace(/-/g, '+').replace(/_/g, '/').padEnd(
    str.length + ((4 - (str.length % 4)) % 4),
    '='
  );
  const binary = atob(padded);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes;
}

async function importSpkiPem(pem: string): Promise<CryptoKey> {
  const body = pem.replace(/-----[A-Z ]+-----/g, '').replace(/\s+/g, '');
  const binary = atob(body);
  const der = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) der[i] = binary.charCodeAt(i);
  return crypto.subtle.importKey('spki', der, { name: 'Ed25519' }, false, ['verify']);
}

describe('POST /v1/license/validate', () => {
  let env: Env;

  beforeEach(() => {
    vi.clearAllMocks();
    env = createMockEnv();
  });

  describe('request validation', () => {
    it('should reject invalid JSON body', async () => {
      const request = new Request('https://api.replimap.com/v1/license/validate', {
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
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('license');
    });

    it('should reject invalid machine ID format', async () => {
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: 'invalid-machine-id',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ErrorResponse>(response);

      expect(response.status).toBe(400);
      expect(data.error_code).toBe('INVALID_REQUEST');
      expect(data.message).toContain('machine');
    });
  });

  describe('license lookup', () => {
    it('should return 404 for non-existent license', async () => {
      // Mock returns null for non-existent license
      vi.mocked(db.getLicenseForValidation).mockResolvedValue(null);

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
      // Mock license data
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 1,
      });

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
      expect(data.features.resources_per_scan).toBe(-1); // unlimited for pro (v4.0)
      expect(data.features.machines).toBe(2); // v4.0 pro plan has 2 machines
      expect(data.usage).toBeDefined();
      expect(data.cache_until).toBeDefined();
      expect(data.cli_version).toBeDefined();
      expect(data.cli_version?.status).toBe('ok');
    });

    it('should include a contract-compliant license_blob when LICENSE_SIGNING_KEY is configured', async () => {
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 1,
      });

      const machineId = generateMachineId();
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: machineId,
        cli_version: '1.0.0',
      });

      const response = await handleValidateLicense(request, env, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      // Existing fields untouched by the addition of license_blob.
      expect(response.status).toBe(200);
      expect(data.valid).toBe(true);
      expect(data.plan).toBe('pro');
      expect(data.status).toBe('active');
      expect(data.features.machines).toBe(2);

      // license_blob: two unpadded base64url segments.
      expect(typeof data.license_blob).toBe('string');
      const parts = (data.license_blob as string).split('.');
      expect(parts).toHaveLength(2);
      for (const part of parts) {
        expect(part).toMatch(/^[A-Za-z0-9_-]+$/);
      }

      // Signature verifies against the matching test public key, and the
      // decoded payload matches contract §2 semantics.
      const [payloadB64, sigB64] = parts;
      const payloadBytes = base64UrlDecode(payloadB64);
      const publicKey = await importSpkiPem(TEST_LICENSE_SIGNING_PUBLIC_KEY_PEM);
      const isValid = await crypto.subtle.verify(
        'Ed25519',
        publicKey,
        base64UrlDecode(sigB64),
        payloadBytes
      );
      expect(isValid).toBe(true);

      const decoded = JSON.parse(new TextDecoder().decode(payloadBytes));
      expect(decoded.v).toBe(1);
      expect(decoded.lic).toBe('RM-TEST-1234-5678-ABCD');
      expect(decoded.plan).toBe('pro');
      expect(decoded.machine_id).toBe(machineId.toLowerCase());
      expect(decoded.kid).toBe('key-test-mono'); // env.LICENSE_SIGNING_KID from createMockEnv
      // exp = DB current_period_end + pro's offline_grace_days (7 days),
      // per contract §11 adjudication D.
      const expectedExp =
        Math.floor(new Date(mockLicense.current_period_end).getTime() / 1000) + 7 * 86400;
      expect(decoded.exp).toBe(expectedExp);
    });

    it('should omit license_blob and return 200 (fail-open) when LICENSE_SIGNING_KEY is not configured', async () => {
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 1,
      });

      const envWithoutSigningKey = createMockEnv({ LICENSE_SIGNING_KEY: undefined });
      const request = createRequest('POST', '/v1/license/validate', {
        license_key: 'RM-TEST-1234-5678-ABCD',
        machine_id: generateMachineId(),
        cli_version: '1.0.0',
      });

      const response = await handleValidateLicense(request, envWithoutSigningKey, '1.2.3.4');
      const data = await parseResponse<ValidateLicenseResponse>(response);

      // Never 500s the hot path — old-client-shaped response, just no blob.
      expect(response.status).toBe(200);
      expect(data.valid).toBe(true);
      expect(data.plan).toBe('pro');
      expect(data.status).toBe('active');
      expect(data.features).toBeDefined();
      expect(data.license_blob).toBeUndefined();
    });
  });

  describe('CLI version check', () => {
    it('should return ok for current version', async () => {
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 0,
      });

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
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 0,
      });

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
      vi.mocked(db.getLicenseForValidation).mockResolvedValue({
        license_id: mockLicense.id,
        license_key: mockLicense.license_key,
        plan: 'pro',
        status: 'active',
        current_period_end: mockLicense.current_period_end,
        machine_is_active: 1,
        machine_last_seen: new Date().toISOString(),
        active_machines: 1,
        monthly_changes: 0,
        active_aws_accounts: 0,
      });

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
