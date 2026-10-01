import { describe, it, expect } from 'vitest';
import { PLANS, SOVEREIGN_FEATURES } from './pricing';

/**
 * Regression coverage for the sovereign-claims sync fix (2026-07-14):
 * PLANS.sovereign.features and SOVEREIGN_FEATURES used to be two hand-
 * maintained lists that drifted apart and both claimed "DORA compliance"
 * / "Essential Eight assessment" — features never ratified in the CLI
 * repo's Pricing/Feature Matrix (docs/technical-reference.md). Both are
 * now derived from a single SOVEREIGN_FEATURE_CLAIMS array; these tests
 * lock that in so the two lists cannot silently diverge again.
 */

const UNRATIFIED_CLAIMS = [
  /dora/i,
  /essential eight/i,
  /sha256/i,
  /digital signature/i, // no implementation in the CLI
  /white-label/i, // no implementation in the CLI
];

describe('sovereign feature claims — matrix sync', () => {
  it('SOVEREIGN_FEATURES contains no unratified claims', () => {
    for (const feature of SOVEREIGN_FEATURES) {
      for (const pattern of UNRATIFIED_CLAIMS) {
        expect(feature).not.toMatch(pattern);
      }
    }
  });

  it('PLANS.sovereign.features contains no unratified claims', () => {
    for (const feature of PLANS.sovereign.features) {
      for (const pattern of UNRATIFIED_CLAIMS) {
        expect(feature.text).not.toMatch(pattern);
      }
    }
  });

  it('PLANS.sovereign.features and SOVEREIGN_FEATURES agree on every ratified claim (single source of truth)', () => {
    const planClaims = new Set(PLANS.sovereign.features.map((f) => f.text));
    for (const claim of SOVEREIGN_FEATURES) {
      expect(planClaims.has(claim)).toBe(true);
    }
  });

  it('claims air-gapped activation by license file and the compliance packs', () => {
    const joined = SOVEREIGN_FEATURES.join(' | ');
    expect(joined).toMatch(/air-gapped activation by signed license file/i);
    expect(joined).toMatch(/apra cps 234/i);
    expect(joined).toMatch(/rbnz bs11/i);
    expect(joined).toMatch(/nzism/i);
    expect(joined).toMatch(/dedicated support/i);
  });
});

describe('offline grace', () => {
  it('is 0 / 7 / 14 / 30 days across plans', () => {
    expect(PLANS.community.offlineGraceDays).toBe(0);
    expect(PLANS.pro.offlineGraceDays).toBe(7);
    expect(PLANS.team.offlineGraceDays).toBe(14);
    expect(PLANS.sovereign.offlineGraceDays).toBe(30);
  });
});
