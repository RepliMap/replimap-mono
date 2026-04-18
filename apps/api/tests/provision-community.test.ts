/**
 * Tests for POST /v1/license/provision-community
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { handleProvisionCommunity } from '../src/handlers/provision-community';
import { createMockEnv, createRequest, parseResponse } from './helpers';
import * as db from '../src/lib/db';

vi.mock('../src/lib/db', async (importOriginal) => {
  const original = await importOriginal<typeof import('../src/lib/db')>();
  return {
    ...original,
    createDb: vi.fn(() => ({}) as unknown as ReturnType<typeof original.createDb>),
    findOrCreateUser: vi.fn(),
    createLicense: vi.fn(),
    getLicenseByUserEmailLatest: vi.fn(),
  };
});

const asMock = <T extends (...args: never[]) => unknown>(fn: T) =>
  fn as unknown as ReturnType<typeof vi.fn>;

describe('POST /v1/license/provision-community', () => {
  beforeEach(() => {
    asMock(db.findOrCreateUser).mockReset();
    asMock(db.createLicense).mockReset();
    asMock(db.getLicenseByUserEmailLatest).mockReset();
  });

  it('creates a new community license when user has none', async () => {
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue(null);
    asMock(db.findOrCreateUser).mockResolvedValue({
      id: 'user_new_1',
      email: 'new@example.com',
    });
    asMock(db.createLicense).mockResolvedValue({
      licenseKey: 'RM-COMM-0000-0000-0001',
    });

    const env = createMockEnv();
    const request = createRequest('POST', '/v1/license/provision-community', {
      email: 'new@example.com',
    });
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(201);
    const body = await parseResponse<{
      license_key: string;
      plan: string;
      status: string;
      created: boolean;
    }>(response);
    expect(body.plan).toBe('community');
    expect(body.status).toBe('active');
    expect(body.created).toBe(true);
    expect(body.license_key).toMatch(/^RM-/);
    expect(asMock(db.findOrCreateUser)).toHaveBeenCalledWith(
      expect.anything(),
      'new@example.com'
    );
    expect(asMock(db.createLicense)).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        plan: 'community',
        planType: 'free',
        userId: 'user_new_1',
      })
    );
  });

  it('is idempotent — returns existing community license', async () => {
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue({
      licenseKey: 'RM-EXIST-1234-5678-ABCD',
      plan: 'community',
      status: 'active',
    });

    const env = createMockEnv();
    const request = createRequest('POST', '/v1/license/provision-community', {
      email: 'existing@example.com',
    });
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(200);
    const body = await parseResponse<{
      license_key: string;
      created: boolean;
    }>(response);
    expect(body.license_key).toBe('RM-EXIST-1234-5678-ABCD');
    expect(body.created).toBe(false);
    expect(asMock(db.findOrCreateUser)).not.toHaveBeenCalled();
    expect(asMock(db.createLicense)).not.toHaveBeenCalled();
  });

  it('never overwrites a paid license — returns existing pro license as-is', async () => {
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue({
      licenseKey: 'RM-PAID-9999-8888-7777',
      plan: 'pro',
      status: 'active',
    });

    const env = createMockEnv();
    const request = createRequest('POST', '/v1/license/provision-community', {
      email: 'paid@example.com',
    });
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(200);
    const body = await parseResponse<{ plan: string; created: boolean }>(
      response
    );
    expect(body.plan).toBe('pro');
    expect(body.created).toBe(false);
    expect(asMock(db.createLicense)).not.toHaveBeenCalled();
  });

  it('rejects missing email with 400', async () => {
    const env = createMockEnv();
    const request = createRequest(
      'POST',
      '/v1/license/provision-community',
      {}
    );
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(400);
  });

  it('rejects malformed email with 400', async () => {
    const env = createMockEnv();
    const request = createRequest('POST', '/v1/license/provision-community', {
      email: 'not-an-email',
    });
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(400);
  });

  it('normalizes email case before lookup', async () => {
    asMock(db.getLicenseByUserEmailLatest).mockResolvedValue(null);
    asMock(db.findOrCreateUser).mockResolvedValue({
      id: 'user_case_1',
      email: 'mixed@example.com',
    });
    asMock(db.createLicense).mockResolvedValue({});

    const env = createMockEnv();
    const request = createRequest('POST', '/v1/license/provision-community', {
      email: 'MiXeD@ExAmPlE.CoM',
    });
    const response = await handleProvisionCommunity(
      request,
      env,
      '127.0.0.1'
    );

    expect(response.status).toBe(201);
    expect(asMock(db.getLicenseByUserEmailLatest)).toHaveBeenCalledWith(
      expect.anything(),
      'mixed@example.com'
    );
    expect(asMock(db.findOrCreateUser)).toHaveBeenCalledWith(
      expect.anything(),
      'mixed@example.com'
    );
  });
});
