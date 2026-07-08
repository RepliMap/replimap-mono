/**
 * Path B (subscription email-lookup) race guard for
 * GET /v1/checkout/session/:session_id/license — against real handlers and a
 * real (Miniflare D1) database.
 *
 * The bug this pins down: Path B resolves the buyer's email via the Stripe
 * session, then returns their latest active license with NO plan filter. A
 * user who already holds a community license (provisioned from the dashboard)
 * and whose paid webhook hasn't landed yet would be shown their community key
 * as "Your license" on the success page. Path B must only ever surface paid
 * licenses; a free-tier row means the purchase is still pending → NOT_READY.
 *
 * These tests use real D1 (not the module mocks in checkout-license.test.ts)
 * because the fix lives in the SQL query itself.
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
import { handleGetCheckoutLicense } from '../src/handlers/checkout-license';
import { createRealD1, realEnv, type RealD1 } from './real-d1';
import type { Env } from '../src/types/env';

const BUYER_EMAIL = 'buyer@example.com';
const SESSION_ID = 'cs_test_pathb123';
const KEY_COMMUNITY = 'RM-COMM-0000-0000-0000';
const KEY_PRO = 'RM-PRO0-1111-2222-3333';

let d1: RealD1;
let env: Env;

/** Stripe session fetch stub: resolves the session to the buyer's email. */
const mockFetch = vi.fn();

beforeAll(async () => {
  d1 = await createRealD1();
  env = realEnv(d1.DB);
  vi.stubGlobal('fetch', mockFetch);
}, 30_000);

afterAll(async () => {
  vi.unstubAllGlobals();
  await d1.dispose();
});

beforeEach(async () => {
  await d1.reset();
  mockFetch.mockReset();
  mockFetch.mockResolvedValue({
    ok: true,
    json: async () => ({ customer_email: BUYER_EMAIL }),
  });

  await env.DB.prepare(
    `INSERT INTO user (id, email, name) VALUES ('u_buyer', ?, '')`
  )
    .bind(BUYER_EMAIL)
    .run();
});

afterEach(() => {
  vi.restoreAllMocks();
});

function callHandler(): Promise<Response> {
  const request = new Request(
    `https://api.test/v1/checkout/session/${SESSION_ID}/license`
  );
  return handleGetCheckoutLicense(request, env, '127.0.0.1', SESSION_ID);
}

describe('Path B plan guard (real D1)', () => {
  it('does NOT return a pre-existing community license while the paid webhook is pending', async () => {
    // The user provisioned a free community key earlier (e.g. via dashboard);
    // they just paid, but customer.subscription.created hasn't landed yet.
    await env.DB.prepare(
      `INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status)
       VALUES ('lic_comm', 'u_buyer', ?, 'community', 'free', 'active')`
    )
      .bind(KEY_COMMUNITY)
      .run();

    const response = await callHandler();

    expect(response.status).toBe(404);
    const body = (await response.json()) as { error: string };
    expect(body.error).toBe('NOT_READY');
  });

  it('returns the paid license once the subscription webhook has landed, even with an older community row', async () => {
    await env.DB.prepare(
      `INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status, created_at)
       VALUES ('lic_comm', 'u_buyer', ?, 'community', 'free', 'active', 1751328000000)`
    )
      .bind(KEY_COMMUNITY)
      .run();
    await env.DB.prepare(
      `INSERT INTO licenses (id, user_id, license_key, plan, plan_type, status, created_at)
       VALUES ('lic_pro', 'u_buyer', ?, 'pro', 'monthly', 'active', 1752019200000)`
    )
      .bind(KEY_PRO)
      .run();

    const response = await callHandler();

    expect(response.status).toBe(200);
    const body = (await response.json()) as { license_key: string; plan: string };
    expect(body.license_key).toBe(KEY_PRO);
    expect(body.plan).toBe('pro');
  });

  it('keeps returning NOT_READY for a brand-new user with no licenses at all', async () => {
    const response = await callHandler();

    expect(response.status).toBe(404);
    const body = (await response.json()) as { error: string };
    expect(body.error).toBe('NOT_READY');
  });
});
