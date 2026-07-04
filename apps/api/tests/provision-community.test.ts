/**
 * Tests for POST /v1/license/provision-community — against a real D1 database
 * and REAL Clerk session tokens (RS256, verified via a real JWKS).
 *
 * Security contract (P0 auth fix):
 *   - No valid Clerk session token → 401. The endpoint must never provision
 *     or return a license for an unauthenticated caller.
 *   - The provisioned/returned email is derived from the verified token, not
 *     from caller-supplied body. A body email that disagrees with the token
 *     identity → 403 (no license issued or leaked).
 *   - Clerk not configured on the server → 503 (fail closed, never open).
 *
 * Idempotency contract (P1-7, unchanged):
 *   - No license → create community license (201).
 *   - Any NON-EXPIRED license (community OR paid) → return it (200, created:false).
 *   - Only a fully `expired` license frees the email for a new community key.
 */

import {
  describe,
  it,
  expect,
  beforeAll,
  afterAll,
  beforeEach,
  afterEach,
  vi,
} from 'vitest';
import { handleProvisionCommunity } from '../src/handlers/provision-community';
import {
  createDb,
  createLicense,
  findOrCreateUser,
  updateLicenseStatus,
} from '../src/lib/db';
import { generateLicenseKey } from '../src/lib/license';
import type { Env } from '../src/types/env';
import { createRealD1, realEnv, type RealD1 } from './real-d1';
import {
  createClerkHarness,
  TEST_CLERK_ISSUER,
  TEST_CLERK_SECRET_KEY,
  type ClerkHarness,
} from './clerk-harness';

let d1: RealD1;
let env: Env;
let clerk: ClerkHarness;

const USER_ID = 'user_clerk_abc123';
const USER_EMAIL = 'owner@example.com';

beforeAll(async () => {
  d1 = await createRealD1();
  clerk = await createClerkHarness();
  env = realEnv(d1.DB, {
    CLERK_ISSUER: TEST_CLERK_ISSUER,
    CLERK_SECRET_KEY: TEST_CLERK_SECRET_KEY,
  });
}, 30_000);

afterAll(async () => {
  await d1.dispose();
});

beforeEach(async () => {
  await d1.reset();
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
  // Default: JWKS + backend resolve USER_ID → USER_EMAIL.
  clerk.installFetchStub({ users: { [USER_ID]: USER_EMAIL } });
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

/** Build a request, optionally with a bearer token and/or JSON body. */
function provisionRequest(opts: {
  token?: string;
  body?: unknown;
} = {}): Request {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (opts.token) headers['Authorization'] = `Bearer ${opts.token}`;
  return new Request('https://api.test/v1/license/provision-community', {
    method: 'POST',
    headers,
    body: JSON.stringify(opts.body ?? {}),
  });
}

async function provision(opts: {
  token?: string;
  body?: unknown;
  overrideEnv?: Env;
} = {}): Promise<Response> {
  return handleProvisionCommunity(
    provisionRequest(opts),
    opts.overrideEnv ?? env,
    '127.0.0.1'
  );
}

async function licenseCount(): Promise<number> {
  const result = await env.DB.prepare(
    'SELECT COUNT(*) AS n FROM licenses'
  ).first<{ n: number }>();
  return result?.n ?? 0;
}

async function seedPaidLicense(
  email: string,
  status: 'active' | 'past_due' | 'canceled' | 'expired' | 'revoked'
): Promise<string> {
  const db = createDb(env.DB);
  const user = await findOrCreateUser(db, email, 'cus_seed_01');
  const licenseKey = generateLicenseKey();
  const license = await createLicense(db, {
    userId: user.id,
    licenseKey,
    plan: 'pro',
    stripeSubscriptionId: 'sub_seed_01',
    stripePriceId: 'price_test_pro',
    currentPeriodStart: new Date().toISOString(),
    currentPeriodEnd: new Date(Date.now() + 30 * 86400_000).toISOString(),
  });
  if (status !== 'active') {
    await updateLicenseStatus(db, license.id, status);
  }
  return licenseKey;
}

// ============================================================================
// Authentication & authorization (the P0 fix)
// ============================================================================

describe('authentication', () => {
  it('P0: rejects an unauthenticated request (no bearer token) with 401 and issues nothing', async () => {
    const res = await provision({ body: { email: 'victim@example.com' } });
    expect(res.status).toBe(401);
    expect(await licenseCount()).toBe(0);
  });

  it('P0: rejects a request whose token identity differs from the body email (403, no leak)', async () => {
    // Attacker holds a valid token for their own account but asks for a
    // victim's email. Must be refused — and must not return any license.
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });
    const res = await provision({
      token,
      body: { email: 'victim@example.com' },
    });
    expect(res.status).toBe(403);
    expect(await licenseCount()).toBe(0);
  });

  it("P0: does not leak a victim's existing paid license key to a mismatched-token caller", async () => {
    const victimKey = await seedPaidLicense('victim@example.com', 'active');

    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });
    const res = await provision({
      token,
      body: { email: 'victim@example.com' },
    });

    expect(res.status).toBe(403);
    const text = await res.text();
    expect(text).not.toContain(victimKey);
  });

  it('P0: rejects a token signed by a different (untrusted) key with 401', async () => {
    const attackerClerk = await createClerkHarness();
    // Our env still trusts the original harness's JWKS (installed in beforeEach).
    const forgedToken = await attackerClerk.mintToken({
      userId: USER_ID,
      email: USER_EMAIL,
    });
    const res = await provision({ token: forgedToken });
    expect(res.status).toBe(401);
    expect(await licenseCount()).toBe(0);
  });

  it('P0: rejects an expired token with 401', async () => {
    const token = await clerk.mintToken({
      userId: USER_ID,
      email: USER_EMAIL,
      expiresInSeconds: -3600, // well beyond the 60s clock-skew tolerance
    });
    const res = await provision({ token });
    expect(res.status).toBe(401);
  });

  it('P0: rejects a token from an untrusted issuer with 401', async () => {
    const token = await clerk.mintToken({
      userId: USER_ID,
      email: USER_EMAIL,
      issuer: 'https://evil.attacker.example',
    });
    const res = await provision({ token });
    expect(res.status).toBe(401);
  });

  it('P0: fails closed (503) when Clerk is not configured on the server', async () => {
    const unconfigured = realEnv(d1.DB); // no CLERK_ISSUER / CLERK_SECRET_KEY
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });
    const res = await provision({ token, overrideEnv: unconfigured });
    expect(res.status).toBe(503);
    expect(await licenseCount()).toBe(0);
  });
});

// ============================================================================
// Normal self-service provisioning (must stay GREEN)
// ============================================================================

describe('self-service provisioning (authenticated)', () => {
  it('creates a community license for the token-identified user (email from token claim)', async () => {
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });
    // Frontend may omit the body email entirely and rely on the token.
    const res = await provision({ token });
    expect(res.status).toBe(201);

    const body = (await res.json()) as {
      license_key: string;
      plan: string;
      status: string;
      created: boolean;
    };
    expect(body.plan).toBe('community');
    expect(body.created).toBe(true);
    expect(body.license_key).toMatch(
      /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/
    );
    expect(await licenseCount()).toBe(1);

    // Provisioned for the token's email.
    const row = await env.DB.prepare(
      'SELECT email FROM user LIMIT 1'
    ).first<{ email: string }>();
    expect(row?.email).toBe(USER_EMAIL);
  });

  it('accepts a body email that matches the token identity (case-insensitive)', async () => {
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });
    const res = await provision({
      token,
      body: { email: USER_EMAIL.toUpperCase() },
    });
    expect(res.status).toBe(201);
    expect(await licenseCount()).toBe(1);
  });

  it('resolves email via the Clerk backend API when the token has no email claim', async () => {
    // Default Clerk session tokens do not carry email — the handler must fall
    // back to the Clerk Backend API (GET /v1/users/{sub}).
    const token = await clerk.mintToken({ userId: USER_ID }); // no email claim
    const res = await provision({ token });
    expect(res.status).toBe(201);

    const row = await env.DB.prepare(
      'SELECT email FROM user LIMIT 1'
    ).first<{ email: string }>();
    expect(row?.email).toBe(USER_EMAIL);
  });

  it('is idempotent — repeated authenticated calls return the same license', async () => {
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });

    const first = await provision({ token });
    const firstBody = (await first.json()) as { license_key: string };

    const second = await provision({ token });
    expect(second.status).toBe(200);
    const secondBody = (await second.json()) as {
      license_key: string;
      created: boolean;
    };
    expect(secondBody.license_key).toBe(firstBody.license_key);
    expect(secondBody.created).toBe(false);
    expect(await licenseCount()).toBe(1);
  });

  it('returns the user own active paid license as-is (never overwrites)', async () => {
    const paidKey = await seedPaidLicense(USER_EMAIL, 'active');
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });

    const res = await provision({ token });
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      license_key: string;
      plan: string;
      created: boolean;
    };
    expect(body.license_key).toBe(paidKey);
    expect(body.plan).toBe('pro');
    expect(body.created).toBe(false);
    expect(await licenseCount()).toBe(1);
  });

  it('P1-7: does NOT issue a second license when the user paid license is past_due', async () => {
    const paidKey = await seedPaidLicense(USER_EMAIL, 'past_due');
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });

    const res = await provision({ token });
    expect(res.status).toBe(200);
    const body = (await res.json()) as {
      license_key: string;
      status: string;
      created: boolean;
    };
    expect(body.created).toBe(false);
    expect(body.license_key).toBe(paidKey);
    expect(body.status).toBe('past_due');
    expect(await licenseCount()).toBe(1);
  });

  it('P1-7: does NOT issue a second license when the user paid license is canceled', async () => {
    const paidKey = await seedPaidLicense(USER_EMAIL, 'canceled');
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });

    const res = await provision({ token });
    expect(res.status).toBe(200);
    const body = (await res.json()) as { license_key: string; created: boolean };
    expect(body.created).toBe(false);
    expect(body.license_key).toBe(paidKey);
    expect(await licenseCount()).toBe(1);
  });

  it('allows a fresh community license once the previous license is fully expired', async () => {
    await seedPaidLicense(USER_EMAIL, 'expired');
    const token = await clerk.mintToken({ userId: USER_ID, email: USER_EMAIL });

    const res = await provision({ token });
    expect(res.status).toBe(201);
    const body = (await res.json()) as { plan: string; created: boolean };
    expect(body.plan).toBe('community');
    expect(body.created).toBe(true);
    expect(await licenseCount()).toBe(2);
  });
});
