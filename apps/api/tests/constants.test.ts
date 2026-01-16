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

describe('Plan Features v4.0', () => {
  it('should have all v4.0 plan types defined', () => {
    expect(PLAN_FEATURES.community).toBeDefined();
    expect(PLAN_FEATURES.pro).toBeDefined();
    expect(PLAN_FEATURES.team).toBeDefined();
    expect(PLAN_FEATURES.sovereign).toBeDefined();
  });

  it('should have legacy plan aliases for backward compatibility', () => {
    expect(PLAN_FEATURES.free).toBeDefined();
    expect(PLAN_FEATURES.solo).toBeDefined();
    expect(PLAN_FEATURES.enterprise).toBeDefined();
    // Legacy aliases should map to v4.0 plans
    expect(PLAN_FEATURES.free).toBe(PLAN_FEATURES.community);
    expect(PLAN_FEATURES.solo).toBe(PLAN_FEATURES.pro);
    expect(PLAN_FEATURES.enterprise).toBe(PLAN_FEATURES.sovereign);
  });

  it('should have correct community plan limits (v4.0: unlimited scans)', () => {
    expect(PLAN_FEATURES.community.resources_per_scan).toBe(-1); // v4.0: UNLIMITED
    expect(PLAN_FEATURES.community.scans_per_month).toBe(-1);    // v4.0: UNLIMITED
    expect(PLAN_FEATURES.community.aws_accounts).toBe(1);
    expect(PLAN_FEATURES.community.machines).toBe(1);
    expect(PLAN_FEATURES.community.export_formats).toContain('json');
    expect(PLAN_FEATURES.community.export_formats).not.toContain('terraform'); // v4.0: JSON only for community
  });

  it('should have unlimited resources for all plans (v4.0 philosophy)', () => {
    expect(PLAN_FEATURES.community.resources_per_scan).toBe(-1);
    expect(PLAN_FEATURES.pro.resources_per_scan).toBe(-1);
    expect(PLAN_FEATURES.team.resources_per_scan).toBe(-1);
    expect(PLAN_FEATURES.sovereign.resources_per_scan).toBe(-1);
  });

  it('should have increasing machine limits across tiers', () => {
    expect(PLAN_FEATURES.community.machines).toBeLessThan(PLAN_FEATURES.pro.machines);
    expect(PLAN_FEATURES.pro.machines).toBeLessThan(PLAN_FEATURES.team.machines);
    // Sovereign has unlimited machines (-1)
    expect(PLAN_FEATURES.sovereign.machines).toBe(-1);
  });

  it('should have increasing AWS account limits across tiers', () => {
    expect(PLAN_FEATURES.community.aws_accounts).toBe(1);
    expect(PLAN_FEATURES.pro.aws_accounts).toBe(3);
    expect(PLAN_FEATURES.team.aws_accounts).toBe(10);
    expect(PLAN_FEATURES.sovereign.aws_accounts).toBe(-1); // Unlimited
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

describe('Stripe Price Mapping v4.0', () => {
  it('should have a primary price ID for each paid plan in PLAN_TO_STRIPE_PRICE', () => {
    // v4.0 plans: pro, team, sovereign
    expect(PLAN_TO_STRIPE_PRICE['pro']).toBeDefined();
    expect(PLAN_TO_STRIPE_PRICE['team']).toBeDefined();
    expect(PLAN_TO_STRIPE_PRICE['sovereign']).toBeDefined();
    // Legacy alias should also work
    expect(PLAN_TO_STRIPE_PRICE['solo']).toBeDefined();
  });

  it('should have price-to-plan mappings that include all v4.0 plans', () => {
    // v4.0 plans should appear in STRIPE_PRICE_TO_PLAN values
    const plans = new Set(Object.values(STRIPE_PRICE_TO_PLAN));
    expect(plans.has('pro')).toBe(true);
    expect(plans.has('team')).toBe(true);
    expect(plans.has('sovereign')).toBe(true);
  });

  it('should return community for unknown price IDs', () => {
    expect(getPlanFromPriceId('unknown_price_id')).toBe('community');
  });

  it('should return correct plan for known price IDs', () => {
    expect(getPlanFromPriceId('price_test_solo')).toBe('pro');  // v4.0: solo → pro
    expect(getPlanFromPriceId('price_test_pro')).toBe('pro');
    expect(getPlanFromPriceId('price_test_team')).toBe('team');
    expect(getPlanFromPriceId('price_test_sovereign')).toBe('sovereign');
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
      expect(isLifetimePriceId('price_test_solo_lifetime')).toBe(true);  // Legacy
      expect(isLifetimePriceId('price_test_pro_lifetime')).toBe(true);
      expect(isLifetimePriceId('price_test_team_lifetime')).toBe(true);
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
      expect(result.plan).toBe('pro');  // v4.0: solo → pro
      expect(result.billingType).toBe('lifetime');
    });

    it('should return monthly billing type for subscription prices', () => {
      const result = getPlanInfoFromPriceId('price_test_solo');
      expect(result.plan).toBe('pro');  // v4.0: solo → pro
      expect(result.billingType).toBe('monthly');
    });

    it('should return community plan for unknown prices', () => {
      const result = getPlanInfoFromPriceId('unknown');
      expect(result.plan).toBe('community');  // v4.0: free → community
      expect(result.billingType).toBe('monthly');
    });
  });

  describe('getStripePriceMapping', () => {
    it('should include test lifetime prices', () => {
      const mapping = getStripePriceMapping({} as any);
      expect(mapping['price_test_solo_lifetime']).toBeDefined();
      expect(mapping['price_test_solo_lifetime'].billingType).toBe('lifetime');
      expect(mapping['price_test_solo_lifetime'].plan).toBe('pro');  // v4.0: solo → pro
    });

    it('should include environment-configured lifetime prices', () => {
      const env = {
        STRIPE_PRO_LIFETIME_PRICE_ID: 'price_live_pro_lt',
        STRIPE_TEAM_LIFETIME_PRICE_ID: 'price_live_team_lt',
      };
      const mapping = getStripePriceMapping(env as any);

      expect(mapping['price_live_pro_lt']).toEqual({
        plan: 'pro',
        billingType: 'lifetime',
      });
      expect(mapping['price_live_team_lt']).toEqual({
        plan: 'team',
        billingType: 'lifetime',
      });
    });

    it('should include subscription prices as monthly', () => {
      const mapping = getStripePriceMapping({} as any);
      expect(mapping['price_test_solo']).toBeDefined();
      expect(mapping['price_test_solo'].billingType).toBe('monthly');
      expect(mapping['price_test_solo'].plan).toBe('pro');  // v4.0: solo → pro
    });
  });

  describe('getLifetimePriceIds', () => {
    it('should return empty array when no lifetime prices configured', () => {
      const ids = getLifetimePriceIds({} as any);
      expect(ids).toEqual([]);
    });

    it('should return configured lifetime price IDs', () => {
      const env = {
        STRIPE_PRO_LIFETIME_PRICE_ID: 'price_pro_lt',
        STRIPE_TEAM_LIFETIME_PRICE_ID: 'price_team_lt',
      };
      const ids = getLifetimePriceIds(env as any);

      expect(ids).toContain('price_pro_lt');
      expect(ids).toContain('price_team_lt');
      expect(ids.length).toBe(2);
    });

    it('should handle partial configuration', () => {
      const env = {
        STRIPE_PRO_LIFETIME_PRICE_ID: 'price_pro_lt',
      };
      const ids = getLifetimePriceIds(env as any);

      expect(ids).toContain('price_pro_lt');
      expect(ids.length).toBe(1);
    });
  });
});
