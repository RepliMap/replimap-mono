/**
 * Clerk verification: JWKS caching, key-rotation refetch, timeouts, and
 * fail-closed (null → 401) on upstream failure.
 */
import { describe, it, expect, beforeAll, afterEach, vi } from 'vitest';
import { verifyClerkSession } from '../src/lib/clerk';
import { createClerkHarness, TEST_CLERK_ISSUER, TEST_CLERK_SECRET_KEY, type ClerkHarness } from './clerk-harness';
import type { Env } from '../src/types/env';

const env = { CLERK_ISSUER: TEST_CLERK_ISSUER, CLERK_SECRET_KEY: TEST_CLERK_SECRET_KEY } as Env;
const JWKS_URL = `${TEST_CLERK_ISSUER}/.well-known/jwks.json`;

let clerk: ClerkHarness;
beforeAll(async () => {
  clerk = await createClerkHarness();
}, 30_000);

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function authed(opts: { email?: string } = { email: 'a@example.com' }): Promise<Request> {
  const token = await clerk.mintToken({ userId: 'user_1', ...opts });
  return new Request('https://api.test/x', { headers: { Authorization: `Bearer ${token}` } });
}

const jwksCalls = (spy: ReturnType<typeof vi.fn>) =>
  spy.mock.calls.filter(([url]) => String(url) === JWKS_URL);

describe('verifyClerkSession', () => {
  it('caches the JWKS across requests', async () => {
    const spy = clerk.installFetchStub();
    expect(await verifyClerkSession(await authed(), env)).not.toBeNull();
    expect(await verifyClerkSession(await authed(), env)).not.toBeNull();
    expect(jwksCalls(spy)).toHaveLength(1);
  });

  it('refetches the JWKS once when the kid is unknown (key rotation)', async () => {
    const spy = clerk.installFetchStub();
    // Prime the cache with a JWKS that does not contain the token's kid.
    spy.mockImplementationOnce(async () =>
      new Response(JSON.stringify({ keys: [{ kty: 'RSA', kid: 'rotated-out' }] }), { status: 200 })
    );
    expect(await verifyClerkSession(await authed(), env)).toBeNull();
    // Cache is fresh but lacks the kid → one refetch finds the new key.
    expect(await verifyClerkSession(await authed(), env)).not.toBeNull();
    expect(jwksCalls(spy)).toHaveLength(2);
  });

  it('passes a timeout signal on JWKS and backend user fetches', async () => {
    const spy = clerk.installFetchStub({ users: { user_1: 'b@example.com' } });
    const identity = await verifyClerkSession(await authed({}), env); // no email claim → backend lookup
    expect(identity?.email).toBe('b@example.com');
    expect(spy).toHaveBeenCalledTimes(2);
    for (const [, init] of spy.mock.calls) {
      expect((init as RequestInit).signal).toBeInstanceOf(AbortSignal);
    }
  });

  it('returns null (→ 401) instead of throwing when the JWKS fetch fails', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.stubGlobal('fetch', vi.fn(async () => { throw new TypeError('network down'); }));
    await expect(verifyClerkSession(await authed(), env)).resolves.toBeNull();
  });

  it('returns null instead of throwing when the backend user lookup times out', async () => {
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    const stub = clerk.installFetchStub();
    const original = stub.getMockImplementation()!;
    stub.mockImplementation(async (url: RequestInfo | URL, init?: RequestInit) => {
      if (String(url).startsWith('https://api.clerk.com/')) {
        throw new DOMException('timeout', 'TimeoutError');
      }
      return original(url, init);
    });
    await expect(verifyClerkSession(await authed({}), env)).resolves.toBeNull();
  });
});
