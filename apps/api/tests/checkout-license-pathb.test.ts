/**
 * Path B (subscription) binding to the Stripe session — real D1.
 *
 * History: Path B used to resolve the buyer's email via the Stripe session and
 * return their latest active paid license, which (a) leaked keys for unpaid
 * sessions and (b) showed an older license for a newer purchase. The license
 * is now looked up by the session's `subscription` id only.
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach, afterEach, vi } from 'vitest';
import {
  BUYER_EMAIL,
  createLookupCtx,
  stripeSession,
  type LookupCtx,
} from './checkout-lookup-harness';

const SESSION = 'cs_test_pathb123';
const KEY_COMMUNITY = 'RM-COMM-0000-0000-0000';
const KEY_PRO = 'RM-PRO0-1111-2222-3333';
const KEY_OTHER_SUB = 'RM-OTHR-1111-2222-3333';

let ctx: LookupCtx;

beforeAll(async () => {
  ctx = await createLookupCtx();
}, 30_000);

afterAll(async () => {
  await ctx.d1.dispose();
});

beforeEach(async () => {
  await ctx.d1.reset();
  vi.spyOn(console, 'log').mockImplementation(() => {});
  await ctx.seedUser('u_buyer', BUYER_EMAIL);
  ctx.install(() => stripeSession({ subscription: 'sub_pathb' }));
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('Path B subscription binding (real D1)', () => {
  it('does NOT return a community license while the paid webhook is pending', async () => {
    await ctx.seedLicense({ id: 'lic_comm', userId: 'u_buyer', key: KEY_COMMUNITY, plan: 'community', planType: 'free' });
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    const text = await res.text();
    expect(text).not.toContain('license_key');
    expect(JSON.parse(text).error).toBe('NOT_READY');
  });

  it('returns the license stamped with the session subscription, ignoring other licenses', async () => {
    await ctx.seedLicense({ id: 'lic_comm', userId: 'u_buyer', key: KEY_COMMUNITY, plan: 'community', planType: 'free', createdAt: 1751328000000 });
    await ctx.seedLicense({ id: 'lic_other', userId: 'u_buyer', key: KEY_OTHER_SUB, subscriptionId: 'sub_other', createdAt: 1753000000000 });
    await ctx.seedLicense({ id: 'lic_pro', userId: 'u_buyer', key: KEY_PRO, subscriptionId: 'sub_pathb', createdAt: 1752019200000 });
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(200);
    const body = (await res.json()) as { license_key: string; plan: string };
    expect(body.license_key).toBe(KEY_PRO);
    expect(body.plan).toBe('pro');
  });

  it('keeps returning NOT_READY for a brand-new user with no licenses at all', async () => {
    const res = await ctx.call(SESSION, { token: await ctx.token() });
    expect(res.status).toBe(404);
    expect(await res.text()).not.toContain('license_key');
  });
});
