/**
 * Pure-function tests for license/lifetime helpers and price mapping.
 * Extracted from the old stripe-webhook.test.ts (which never invoked the
 * webhook handler); the real handler is now tested in stripe-webhook.test.ts.
 */

import { describe, it, expect, vi, afterEach } from 'vitest';
import {
  LIFETIME_EXPIRY,
  isLifetimePriceId,
  getPlanInfoFromPriceId,
  getStripePriceMapping,
} from '../src/lib/constants';
import {
  isLifetimeLicense,
  isLicenseExpired,
  calculatePeriodEnd,
  generateLicenseKey,
} from '../src/lib/license';
import type { Env } from '../src/types/env';

describe('generateLicenseKey', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('produces keys in the RM-XXXX-XXXX-XXXX-XXXX format', () => {
    for (let i = 0; i < 100; i++) {
      expect(generateLicenseKey()).toMatch(
        /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/
      );
    }
  });

  it('P2-11 regression: does not depend on Math.random (must use a CSPRNG)', () => {
    // License keys are bearer credentials — they must come from a
    // cryptographically secure source, not V8's predictable PRNG.
    vi.spyOn(Math, 'random').mockImplementation(() => {
      throw new Error('Math.random is not a CSPRNG — use crypto instead');
    });

    expect(generateLicenseKey()).toMatch(
      /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/
    );
  });

  it('does not produce duplicate keys across a large sample', () => {
    const keys = new Set(
      Array.from({ length: 5000 }, () => generateLicenseKey())
    );
    expect(keys.size).toBe(5000);
  });
});

describe('LIFETIME_EXPIRY constant', () => {
  it('is a far-future date', () => {
    expect(LIFETIME_EXPIRY).toBe('2099-12-31T23:59:59.000Z');
  });

  it('is a valid ISO date string', () => {
    const date = new Date(LIFETIME_EXPIRY);
    expect(date.getUTCFullYear()).toBe(2099);
    expect(date.getUTCMonth()).toBe(11);
    expect(date.getUTCDate()).toBe(31);
  });
});

describe('isLifetimeLicense', () => {
  it('returns true for LIFETIME_EXPIRY date', () => {
    expect(isLifetimeLicense(LIFETIME_EXPIRY)).toBe(true);
  });

  it('returns false for regular expiry dates', () => {
    const regularExpiry = new Date(
      Date.now() + 30 * 24 * 60 * 60 * 1000
    ).toISOString();
    expect(isLifetimeLicense(regularExpiry)).toBe(false);
  });

  it('returns false for null', () => {
    expect(isLifetimeLicense(null)).toBe(false);
  });
});

describe('isLicenseExpired', () => {
  it('returns false for lifetime licenses', () => {
    expect(isLicenseExpired(LIFETIME_EXPIRY)).toBe(false);
  });

  it('returns false for null period end', () => {
    expect(isLicenseExpired(null)).toBe(false);
  });

  it('returns true for past dates', () => {
    expect(isLicenseExpired('2020-01-01T00:00:00.000Z')).toBe(true);
  });

  it('returns false for future dates', () => {
    const future = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString();
    expect(isLicenseExpired(future)).toBe(false);
  });
});

describe('calculatePeriodEnd', () => {
  it('returns LIFETIME_EXPIRY for lifetime billing type', () => {
    expect(calculatePeriodEnd('lifetime')).toBe(LIFETIME_EXPIRY);
  });

  it('returns ~1 year from now for annual billing type', () => {
    const end = new Date(calculatePeriodEnd('annual')).getTime();
    const expected = Date.now() + 365 * 24 * 60 * 60 * 1000;
    expect(Math.abs(end - expected)).toBeLessThan(2 * 24 * 60 * 60 * 1000);
  });

  it('returns ~1 month from now for monthly billing type', () => {
    const end = new Date(calculatePeriodEnd('monthly')).getTime();
    const expected = Date.now() + 30 * 24 * 60 * 60 * 1000;
    expect(Math.abs(end - expected)).toBeLessThan(3 * 24 * 60 * 60 * 1000);
  });
});

describe('lifetime price mapping', () => {
  it('isLifetimePriceId returns true for test lifetime price IDs', () => {
    expect(isLifetimePriceId('price_test_pro_lifetime')).toBe(true);
    expect(isLifetimePriceId('price_test_team_lifetime')).toBe(true);
  });

  it('isLifetimePriceId returns false for regular price IDs', () => {
    expect(isLifetimePriceId('price_test_pro')).toBe(false);
    expect(isLifetimePriceId('price_unknown')).toBe(false);
  });

  it('getPlanInfoFromPriceId returns lifetime billing for lifetime prices', () => {
    expect(getPlanInfoFromPriceId('price_test_pro_lifetime')).toEqual({
      plan: 'pro',
      billingType: 'lifetime',
    });
  });

  it('getPlanInfoFromPriceId returns monthly billing for regular prices', () => {
    expect(getPlanInfoFromPriceId('price_test_pro')).toEqual({
      plan: 'pro',
      billingType: 'monthly',
    });
  });

  it('getPlanInfoFromPriceId falls back to community for unknown prices', () => {
    expect(getPlanInfoFromPriceId('price_does_not_exist')).toEqual({
      plan: 'community',
      billingType: 'monthly',
    });
  });

  it('getStripePriceMapping includes env-configured lifetime prices', () => {
    const env = {
      STRIPE_PRO_LIFETIME_PRICE_ID: 'price_env_pro_life',
      STRIPE_TEAM_LIFETIME_PRICE_ID: 'price_env_team_life',
    } as unknown as Env;
    const mapping = getStripePriceMapping(env);
    expect(mapping['price_env_pro_life']).toEqual({
      plan: 'pro',
      billingType: 'lifetime',
    });
    expect(mapping['price_env_team_life']).toEqual({
      plan: 'team',
      billingType: 'lifetime',
    });
  });

  it('getStripePriceMapping includes built-in test lifetime prices', () => {
    const mapping = getStripePriceMapping({} as Env);
    expect(mapping['price_test_pro_lifetime']).toEqual({
      plan: 'pro',
      billingType: 'lifetime',
    });
  });

  it('getStripePriceMapping includes subscription prices', () => {
    const mapping = getStripePriceMapping({} as Env);
    expect(mapping['price_test_pro']).toEqual({
      plan: 'pro',
      billingType: 'monthly',
    });
  });
});
