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
