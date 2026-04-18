/**
 * Tests for GET /v1/checkout/session/:session_id/license
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { handleGetCheckoutLicense } from '../src/handlers/checkout-license';
import { createMockEnv, createRequest, parseResponse } from './helpers';
import * as db from '../src/lib/db';

const mockFetch = vi.fn();
// @ts-expect-error — override global fetch for Stripe calls
global.fetch = mockFetch;

vi.mock('../src/lib/db', async (importOriginal) => {
  const original = await importOriginal<typeof import('../src/lib/db')>();
  return {
    ...original,
    createDb: vi.fn(() => ({}) as unknown as ReturnType<typeof original.createDb>),
    getLicenseBySessionId: vi.fn(),
    getLicenseByUserEmailLatest: vi.fn(),
  };
});

const asMock = <T extends (...args: never[]) => unknown>(fn: T) =>
  fn as unknown as ReturnType<typeof vi.fn>;

describe('GET /v1/checkout/session/:session_id/license', () => {
  beforeEach(() => {
    mockFetch.mockReset();
    asMock(db.getLicenseBySessionId).mockReset();
    asMock(db.getLicenseByUserEmailLatest).mockReset();
  });

  it('returns license by session_id when stamped on license (lifetime path)', async () => {
    asMock(db.getLicenseBySessionId).mockResolvedValue({
      licenseKey: 'RM-TEST-1234-5678-ABCD',
      plan: 'pro',
      status: 'active',
      planType: 'lifetime',
    });

    const env = createMockEnv();
    const request = createRequest(
      'GET',
      '/v1/checkout/session/cs_test_abc123/license'
    );
    const response = await handleGetCheckoutLicense(
      request,
      env,
      '127.0.0.1',
      'cs_test_abc123'
    );

    expect(response.status).toBe(200);
    const body = await parseResponse<{
      license_key: string;
      plan: string;
      status: string;
      plan_type: string;
    }>(response);
    expect(body.license_key).toBe('RM-TEST-1234-5678-ABCD');
    expect(body.plan).toBe('pro');
    expect(body.plan_type).toBe('lifetime');
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('falls back to Stripe email lookup when session_id not stamped (subscription path)', async () => {
    asMock(db.getLicenseBySessionId).mockResolvedValue(null);
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ customer_email: 'sub@example.com' }),
    });
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue({
      licenseKey: 'RM-SUBS-0000-1111-2222',
      plan: 'team',
      status: 'active',
      planType: 'monthly',
    });

    const env = createMockEnv();
    const request = createRequest(
      'GET',
      '/v1/checkout/session/cs_test_xyz789/license'
    );
    const response = await handleGetCheckoutLicense(
      request,
      env,
      '127.0.0.1',
      'cs_test_xyz789'
    );

    expect(response.status).toBe(200);
    const body = await parseResponse<{ license_key: string; plan: string }>(
      response
    );
    expect(body.license_key).toBe('RM-SUBS-0000-1111-2222');
    expect(body.plan).toBe('team');
    expect(mockFetch).toHaveBeenCalledTimes(1);
    expect(asMock(db.getLicenseByUserEmailLatest)).toHaveBeenCalledWith(
      expect.anything(),
      'sub@example.com'
    );
  });

  it('returns 404 NOT_READY when no license found in either path', async () => {
    asMock(db.getLicenseBySessionId).mockResolvedValue(null);
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ customer_email: 'pending@example.com' }),
    });
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue(null);

    const env = createMockEnv();
    const request = createRequest(
      'GET',
      '/v1/checkout/session/cs_test_pending/license'
    );
    const response = await handleGetCheckoutLicense(
      request,
      env,
      '127.0.0.1',
      'cs_test_pending'
    );

    expect(response.status).toBe(404);
    const body = await parseResponse<{ error: string }>(response);
    expect(body.error).toBe('NOT_READY');
  });

  it('rejects malformed session_id with 400', async () => {
    const env = createMockEnv();
    const request = createRequest(
      'GET',
      '/v1/checkout/session/not_a_session_id/license'
    );
    const response = await handleGetCheckoutLicense(
      request,
      env,
      '127.0.0.1',
      'not_a_session_id'
    );

    expect(response.status).toBe(400);
    expect(asMock(db.getLicenseBySessionId)).not.toHaveBeenCalled();
  });

  it('returns 404 when Stripe API call fails (upstream error)', async () => {
    asMock(db.getLicenseBySessionId).mockResolvedValue(null);
    mockFetch.mockResolvedValue({ ok: false, status: 404 });

    const env = createMockEnv();
    const request = createRequest(
      'GET',
      '/v1/checkout/session/cs_test_unknown/license'
    );
    const response = await handleGetCheckoutLicense(
      request,
      env,
      '127.0.0.1',
      'cs_test_unknown'
    );

    expect(response.status).toBe(404);
  });
});
