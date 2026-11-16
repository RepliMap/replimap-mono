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

  describe('authorized party (azp)', () => {
    const azpEnv = {
      ...env,
      CHECKOUT_ALLOWED_ORIGINS: 'https://www.replimap.com,https://replimap.com',
    } as Env;
    const withAzp = async (azp: string) =>
      new Request('https://api.test/x', {
        headers: {
          Authorization: `Bearer ${await clerk.mintToken({ userId: 'user_1', email: 'a@example.com', azp })}`,
        },
      });

    it('accepts a token whose azp is an allowed web origin', async () => {
      clerk.installFetchStub();
      expect(await verifyClerkSession(await withAzp('https://www.replimap.com'), azpEnv)).not.toBeNull();
    });

    it.each([
      ['a foreign origin', 'https://evil.example'],
      ['a lookalike origin', 'https://www.replimap.com.evil.example'],
      ['a malformed value', 'not a url'],
    ])('rejects a token whose azp is %s', async (_name, azp) => {
      clerk.installFetchStub();
      expect(await verifyClerkSession(await withAzp(azp), azpEnv)).toBeNull();
    });

    it('rejects a token carrying azp when no origin allowlist is configured (fail closed)', async () => {
      clerk.installFetchStub();
      expect(await verifyClerkSession(await withAzp('https://www.replimap.com'), env)).toBeNull();
    });

    it('still accepts a token without azp', async () => {
      clerk.installFetchStub();
      expect(await verifyClerkSession(await authed(), azpEnv)).not.toBeNull();
    });
  });

  describe('backend email resolution', () => {
    function stubUser(user: Record<string, unknown>) {
      const stub = clerk.installFetchStub();
      const original = stub.getMockImplementation()!;
      stub.mockImplementation(async (url: RequestInfo | URL, init?: RequestInit) => {
        if (String(url).startsWith('https://api.clerk.com/')) {
          return new Response(JSON.stringify(user), { status: 200 });
        }
        return original(url, init);
      });
    }

    it('uses the verified primary address', async () => {
      stubUser({
        primary_email_address_id: 'idn_p',
        email_addresses: [
          { id: 'idn_x', email_address: 'other@example.com', verification: { status: 'verified' } },
          { id: 'idn_p', email_address: 'Primary@Example.com', verification: { status: 'verified' } },
        ],
      });
      const identity = await verifyClerkSession(await authed({}), env);
      expect(identity?.email).toBe('primary@example.com');
    });

    it('rejects an unverified primary address (no fallback to another address)', async () => {
      stubUser({
        primary_email_address_id: 'idn_p',
        email_addresses: [
          { id: 'idn_p', email_address: 'p@example.com', verification: { status: 'unverified' } },
          { id: 'idn_x', email_address: 'x@example.com', verification: { status: 'verified' } },
        ],
      });
      expect(await verifyClerkSession(await authed({}), env)).toBeNull();
    });

    it('rejects an account without a primary address instead of using addresses[0]', async () => {
      stubUser({
        primary_email_address_id: null,
        email_addresses: [
          { id: 'idn_x', email_address: 'x@example.com', verification: { status: 'verified' } },
        ],
      });
      expect(await verifyClerkSession(await authed({}), env)).toBeNull();
    });
  });
});
