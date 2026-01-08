/**
 * Tests for Constants and Utility Functions
 */

import { describe, it, expect } from 'vitest';
import {
  PLAN_FEATURES,
  MIN_CLI_VERSION,
  LATEST_CLI_VERSION,
  DEPRECATED_CLI_VERSIONS,
  checkCliVersion,
  getPlanFromPriceId,
  STRIPE_PRICE_TO_PLAN,
  PLAN_TO_STRIPE_PRICE,
  LIFETIME_EXPIRY,
  getPlanInfoFromPriceId,
  isLifetimePriceId,
  getStripePriceMapping,
  getLifetimePriceIds,
} from '../src/lib/constants';

describe('Plan Features', () => {
  it('should have all plan types defined', () => {
    expect(PLAN_FEATURES.free).toBeDefined();
    expect(PLAN_FEATURES.solo).toBeDefined();
    expect(PLAN_FEATURES.pro).toBeDefined();
    expect(PLAN_FEATURES.team).toBeDefined();
  });

  it('should have correct free plan limits', () => {
    expect(PLAN_FEATURES.free.resources_per_scan).toBe(5);
    expect(PLAN_FEATURES.free.scans_per_month).toBe(3);
    expect(PLAN_FEATURES.free.aws_accounts).toBe(1);
    expect(PLAN_FEATURES.free.machines).toBe(1);
    expect(PLAN_FEATURES.free.export_formats).toContain('terraform');
  });

  it('should have unlimited resources for paid plans', () => {
    expect(PLAN_FEATURES.solo.resources_per_scan).toBe(-1);
    expect(PLAN_FEATURES.pro.resources_per_scan).toBe(-1);
    expect(PLAN_FEATURES.team.resources_per_scan).toBe(-1);
  });

  it('should have increasing machine limits', () => {
    expect(PLAN_FEATURES.free.machines).toBeLessThan(PLAN_FEATURES.solo.machines);
    expect(PLAN_FEATURES.solo.machines).toBeLessThan(PLAN_FEATURES.pro.machines);
    expect(PLAN_FEATURES.pro.machines).toBeLessThan(PLAN_FEATURES.team.machines);
  });
});

describe('CLI Version Check', () => {
  it('should return ok for undefined version', () => {
    const result = checkCliVersion(undefined);
    expect(result.status).toBe('ok');
    expect(result.latest_version).toBe(LATEST_CLI_VERSION);
    expect(result.upgrade_url).toBeDefined();
  });

  it('should return ok for current version', () => {
    const result = checkCliVersion(LATEST_CLI_VERSION);
    expect(result.status).toBe('ok');
    expect(result.message).toBeUndefined();
  });

  it('should return ok for newer version', () => {
    const result = checkCliVersion('2.0.0');
    expect(result.status).toBe('ok');
  });

  it('should return deprecated for deprecated versions', () => {
    for (const version of DEPRECATED_CLI_VERSIONS) {
      const result = checkCliVersion(version);
      expect(result.status).toBe('deprecated');
      expect(result.message).toContain('deprecated');
      expect(result.message).toContain(version);
    }
  });

  it('should return unsupported for very old versions', () => {
    const result = checkCliVersion('0.1.0');
    expect(result.status).toBe('unsupported');
    expect(result.message).toContain('no longer supported');
  });

  it('should handle invalid version strings gracefully', () => {
    const result = checkCliVersion('not-a-version');
    expect(result.status).toBe('ok'); // Graceful fallback
  });

  it('should handle partial version strings', () => {
    const result = checkCliVersion('1');
    expect(result.status).toBe('ok'); // Graceful fallback for invalid format
  });

  it('should always include upgrade_url', () => {
    expect(checkCliVersion(undefined).upgrade_url).toBeDefined();
    expect(checkCliVersion('1.0.0').upgrade_url).toBeDefined();
    expect(checkCliVersion('0.1.0').upgrade_url).toBeDefined();
  });
});

describe('Stripe Price Mapping', () => {
  it('should have a primary price ID for each paid plan in PLAN_TO_STRIPE_PRICE', () => {
    // Each plan should have at least one price ID for checkout
    expect(PLAN_TO_STRIPE_PRICE['solo']).toBeDefined();
    expect(PLAN_TO_STRIPE_PRICE['pro']).toBeDefined();
    expect(PLAN_TO_STRIPE_PRICE['team']).toBeDefined();
  });

  it('should have price-to-plan mappings that include all plans', () => {
    // All plans with prices should appear in STRIPE_PRICE_TO_PLAN values
    const plans = new Set(Object.values(STRIPE_PRICE_TO_PLAN));
    expect(plans.has('solo')).toBe(true);
    expect(plans.has('pro')).toBe(true);
    expect(plans.has('team')).toBe(true);
  });

  it('should return free for unknown price IDs', () => {
    expect(getPlanFromPriceId('unknown_price_id')).toBe('free');
  });

  it('should return correct plan for known price IDs', () => {
    expect(getPlanFromPriceId('price_test_solo')).toBe('solo');
    expect(getPlanFromPriceId('price_test_pro')).toBe('pro');
    expect(getPlanFromPriceId('price_test_team')).toBe('team');
  });
});

describe('Lifetime Plan Constants', () => {
  describe('LIFETIME_EXPIRY', () => {
    it('should be defined as far future date', () => {
      expect(LIFETIME_EXPIRY).toBe('2099-12-31T23:59:59.000Z');
    });

    it('should be a valid ISO date string', () => {
      const date = new Date(LIFETIME_EXPIRY);
      expect(date.toString()).not.toBe('Invalid Date');
      expect(date.getFullYear()).toBe(2099);
    });
  });

  describe('isLifetimePriceId', () => {
    it('should return true for test lifetime price IDs', () => {
      expect(isLifetimePriceId('price_test_solo_lifetime')).toBe(true);
      expect(isLifetimePriceId('price_test_pro_lifetime')).toBe(true);
    });

    it('should return false for subscription price IDs', () => {
      expect(isLifetimePriceId('price_test_solo')).toBe(false);
      expect(isLifetimePriceId('price_test_pro')).toBe(false);
    });

    it('should return false for unknown price IDs', () => {
      expect(isLifetimePriceId('unknown')).toBe(false);
    });
  });

  describe('getPlanInfoFromPriceId', () => {
    it('should return lifetime billing type for lifetime prices', () => {
      const result = getPlanInfoFromPriceId('price_test_solo_lifetime');
      expect(result.plan).toBe('solo');
      expect(result.billingType).toBe('lifetime');
    });

    it('should return monthly billing type for subscription prices', () => {
      const result = getPlanInfoFromPriceId('price_test_solo');
      expect(result.plan).toBe('solo');
      expect(result.billingType).toBe('monthly');
    });

    it('should return free plan for unknown prices', () => {
      const result = getPlanInfoFromPriceId('unknown');
      expect(result.plan).toBe('free');
      expect(result.billingType).toBe('monthly');
    });
  });

  describe('getStripePriceMapping', () => {
    it('should include test lifetime prices', () => {
      const mapping = getStripePriceMapping({});
      expect(mapping['price_test_solo_lifetime']).toBeDefined();
      expect(mapping['price_test_solo_lifetime'].billingType).toBe('lifetime');
    });

    it('should include environment-configured lifetime prices', () => {
      const env = {
        STRIPE_SOLO_LIFETIME_PRICE_ID: 'price_live_solo_lt',
        STRIPE_PRO_LIFETIME_PRICE_ID: 'price_live_pro_lt',
      };
      const mapping = getStripePriceMapping(env);

      expect(mapping['price_live_solo_lt']).toEqual({
        plan: 'solo',
        billingType: 'lifetime',
      });
      expect(mapping['price_live_pro_lt']).toEqual({
        plan: 'pro',
        billingType: 'lifetime',
      });
    });

    it('should include subscription prices as monthly', () => {
      const mapping = getStripePriceMapping({});
      expect(mapping['price_test_solo']).toBeDefined();
      expect(mapping['price_test_solo'].billingType).toBe('monthly');
    });
  });

  describe('getLifetimePriceIds', () => {
    it('should return empty array when no lifetime prices configured', () => {
      const ids = getLifetimePriceIds({});
      expect(ids).toEqual([]);
    });

    it('should return configured lifetime price IDs', () => {
      const env = {
        STRIPE_SOLO_LIFETIME_PRICE_ID: 'price_solo_lt',
        STRIPE_PRO_LIFETIME_PRICE_ID: 'price_pro_lt',
      };
      const ids = getLifetimePriceIds(env);

      expect(ids).toContain('price_solo_lt');
      expect(ids).toContain('price_pro_lt');
      expect(ids.length).toBe(2);
    });

    it('should handle partial configuration', () => {
      const env = {
        STRIPE_SOLO_LIFETIME_PRICE_ID: 'price_solo_lt',
      };
      const ids = getLifetimePriceIds(env);

      expect(ids).toContain('price_solo_lt');
      expect(ids.length).toBe(1);
    });
  });
});
