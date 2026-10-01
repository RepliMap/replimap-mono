/**
 * Tests for GET /v1/checkout/session/:session_id/license — real handler, real
 * D1, real Clerk RS256 tokens (clerk-harness), Stripe stubbed on fetch.
 *
 * Every negative case asserts that no `license_key` is present in the body.
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
import {
  BUYER_EMAIL,
  OTHER_EMAIL,
  OTHER_ID,
  createLookupCtx,
  stripeSession,
  type LookupCtx,
} from './checkout-lookup-harness';
import type { Env } from '../src/types/env';

const SESSION = 'cs_test_abc123';
const KEY_LIFETIME = 'RM-LIFE-1111-2222-3333';
const KEY_SUB_OLD = 'RM-OLDS-1111-2222-3333';
const KEY_SUB_NEW = 'RM-NEWS-1111-2222-3333';

let ctx: LookupCtx;

beforeAll(async () => {
  ctx = await createLookupCtx();
}, 30_000);

afterAll(async () => {
  await ctx.d1.dispose();
});

beforeEach(async () => {
  await ctx.d1.reset();
  ctx.stripeCalls.length = 0;
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
  await ctx.seedUser('u_buyer', BUYER_EMAIL);
  await ctx.seedUser('u_other', OTHER_EMAIL);
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

async function expectNoKey(res: Response): Promise<Record<string, unknown>> {
  const text = await res.text();
  expect(text).not.toContain('license_key');
  // Match a full license key, not the bare prefix: error bodies carry a
  // random support id (ERR-<base36 time>-<random>, upper-cased) that can
  // legitimately contain the characters "RM-".
  expect(text).not.toMatch(/RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}/);
  return JSON.parse(text) as Record<string, unknown>;
}

describe('authorization (checked before any DB/Stripe call)', () => {
  it('returns 401 without a token and touches neither DB nor Stripe', async () => {
    ctx.install();
    const prepare = vi.fn(() => {
      throw new Error('DB must not be touched');
    });
    const env = { ...ctx.env, DB: { prepare } as unknown as D1Database } as Env;

    const res = await ctx.call(SESSION, { env });

    expect(res.status).toBe(401);
    await expectNoKey(res);
    expect(prepare).not.toHaveBeenCalled();
    expect(ctx.stripeCalls).toHaveLength(0);
  });

  it('returns 401 for a garbage token without touching Stripe', async () => {
    ctx.install();
    const res = await ctx.call(SESSION, { token: 'not.a.jwt' });
    expect(res.status).toBe(401);
    await expectNoKey(res);
    expect(ctx.stripeCalls).toHaveLength(0);
  });

  it('returns 503 when Clerk is not configured (fail closed)', async () => {
    ctx.install();
    const env = { ...ctx.env, CLERK_ISSUER: undefined, CLERK_SECRET_KEY: undefined } as Env;
    const res = await ctx.call(SESSION, { token: await ctx.token(), env });
    expect(res.status).toBe(503);
    await expectNoKey(res);
    expect(ctx.stripeCalls).toHaveLength(0);
  });

  it('returns 403 for a wrong-email token on a paid lifetime session (Path A)', async () => {
    await ctx.seedLicense({ id: 'l1', userId: 'u_buyer', key: KEY_LIFETIME, planType: 'lifetime', sessionId: SESSION });
    ctx.install(() => stripeSession({ mode: 'payment', subscription: null }));
    const res = await ctx.call(SESSION, { token: await ctx.token(OTHER_ID, OTHER_EMAIL) });
    expect(res.status).toBe(403);
    await expectNoKey(res);
  });

  it('returns 403 for a wrong-email token on a paid subscription session (Path B)', async () => {
    await ctx.seedLicense({ id: 'l2', userId: 'u_buyer', key: KEY_SUB_NEW, subscriptionId: 'sub_new' });
    ctx.install();
    const res = await ctx.call(SESSION, { token: await ctx.token(OTHER_ID, OTHER_EMAIL) });
    expect(res.status).toBe(403);
    await expectNoKey(res);
  });

  it('matches emails case-insensitively (customer_details fallback)', async () => {
    await ctx.seedLicense({ id: 'l2', userId: 'u_buyer', key: KEY_SUB_NEW, subscriptionId: 'sub_new' });
    ctx.install(() =>
      stripeSession({ customer_email: null, customer_details: { email: 'Buyer@Example.com' } })
    );
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(200);
  });
});

describe('payment state', () => {
  it('EXPLOIT: open/unpaid session for an email holding a paid license returns no key', async () => {
    await ctx.seedLicense({ id: 'l_old', userId: 'u_buyer', key: KEY_SUB_OLD, subscriptionId: 'sub_old' });
    ctx.install(() =>
      stripeSession({ status: 'open', payment_status: 'unpaid', subscription: null })
    );
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    const body = await expectNoKey(res);
    expect(body.error).toBe('NOT_READY');
  });

  it('complete but unpaid returns NOT_READY with no key', async () => {
    await ctx.seedLicense({ id: 'l_old', userId: 'u_buyer', key: KEY_SUB_OLD, subscriptionId: 'sub_new' });
    ctx.install(() => stripeSession({ payment_status: 'unpaid' }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    await expectNoKey(res);
  });

  it('accepts status=complete + payment_status=no_payment_required (100% promo)', async () => {
    await ctx.seedLicense({ id: 'l_new', userId: 'u_buyer', key: KEY_SUB_NEW, subscriptionId: 'sub_new' });
    ctx.install(() => stripeSession({ payment_status: 'no_payment_required' }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(200);
    expect(((await res.json()) as { license_key: string }).license_key).toBe(KEY_SUB_NEW);
  });
});

describe('license binding', () => {
  it('Path A: paid lifetime session returns the license stamped with the session id', async () => {
    await ctx.seedLicense({ id: 'l1', userId: 'u_buyer', key: KEY_LIFETIME, planType: 'lifetime', sessionId: SESSION });
    ctx.install(() => stripeSession({ mode: 'payment', subscription: null }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(200);
    const body = (await res.json()) as { license_key: string; plan_type: string };
    expect(body.license_key).toBe(KEY_LIFETIME);
    expect(body.plan_type).toBe('lifetime');
  });

  it('payment-mode session without a stamped license -> 404 even when the user holds an active subscription', async () => {
    await ctx.seedLicense({ id: 'l_sub', userId: 'u_buyer', key: KEY_SUB_OLD, subscriptionId: 'sub_old' });
    ctx.install(() => stripeSession({ mode: 'payment', subscription: null }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    const body = await expectNoKey(res);
    expect(body.error).toBe('NOT_READY');
  });

  it('subscription session whose license does not exist yet -> 404 despite an older paid license, then the NEW key once stamped', async () => {
    await ctx.seedLicense({ id: 'l_old', userId: 'u_buyer', key: KEY_SUB_OLD, subscriptionId: 'sub_old', createdAt: 1751328000000 });
    ctx.install(() => stripeSession({ subscription: 'sub_new' }));
    const token = await ctx.token();

    const pending = await ctx.call(SESSION, { token });
    expect(pending.status).toBe(404);
    const body = await expectNoKey(pending);
    expect(body.error).toBe('NOT_READY');

    await ctx.seedLicense({ id: 'l_new', userId: 'u_buyer', key: KEY_SUB_NEW, subscriptionId: 'sub_new', createdAt: 1752019200000 });
    const ready = await ctx.call(SESSION, { token });
    expect(ready.status).toBe(200);
    expect(((await ready.json()) as { license_key: string }).license_key).toBe(KEY_SUB_NEW);
  });

  it('never surfaces a pre-existing community license while the paid webhook is pending', async () => {
    await ctx.seedLicense({ id: 'l_c', userId: 'u_buyer', key: 'RM-COMM-0000-0000-0000', plan: 'community', planType: 'free' });
    ctx.install(() => stripeSession({ subscription: 'sub_new' }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    await expectNoKey(res);
  });
});

describe('Stripe failures and input validation', () => {
  it('Stripe 5xx -> error without key, and not 403', async () => {
    ctx.install(() => new Response('boom', { status: 500 }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(502);
    expect(res.status).not.toBe(403);
    await expectNoKey(res);
  });

  it('Stripe network error -> error without key, and not 403', async () => {
    ctx.install(() => {
      throw new TypeError('network down');
    });
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(502);
    await expectNoKey(res);
  });

  it('unknown session (Stripe 404) -> 404 without key', async () => {
    ctx.install(() => new Response('{}', { status: 404 }));
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    await expectNoKey(res);
  });

  it('rejects a malformed session_id with 400 and no Stripe call', async () => {
    ctx.install();
    const res = await ctx.call('not_a_session_id', { token: await ctx.token() });
    expect(res.status).toBe(400);
    expect(ctx.stripeCalls).toHaveLength(0);
  });
});
