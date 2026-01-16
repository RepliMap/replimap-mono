/**
 * Constants and configuration for RepliMap Backend v4.0
 *
 * Philosophy: "Gate Output, Not Input"
 * - Unlimited scans for all tiers
 * - Unlimited resources per scan
 * - Charge when users export/download
 */

import type { PlanFeatures } from '../types';
import type { Env } from '../types/env';

// ============================================================================
// Plan Configuration v4.0
// ============================================================================

export type PlanType = 'community' | 'pro' | 'team' | 'sovereign';
export type PlanBillingType = 'free' | 'monthly' | 'annual' | 'lifetime';

/** Legacy plan names for backward compatibility */
export type LegacyPlanType = 'free' | 'solo' | 'enterprise';

export const LEGACY_PLAN_MIGRATIONS: Record<LegacyPlanType, PlanType> = {
  free: 'community',
  solo: 'pro',
  enterprise: 'sovereign',
};

/**
 * Normalize a plan name, converting legacy names to v4.0 names
 */
export function normalizePlanName(plan: string): PlanType {
  const lower = plan.toLowerCase();

  // Check v4.0 plan names
  if (['community', 'pro', 'team', 'sovereign'].includes(lower)) {
    return lower as PlanType;
  }

  // Check legacy plan names
  if (lower in LEGACY_PLAN_MIGRATIONS) {
    return LEGACY_PLAN_MIGRATIONS[lower as LegacyPlanType];
  }

  return 'community'; // Default to community for unknown plans
}

// ============================================================================
// Lifetime Plan Constants
// ============================================================================

/** Far future expiry date for lifetime licenses - effectively "never expires" */
export const LIFETIME_EXPIRY = '2099-12-31T23:59:59.000Z';

const V4_PLAN_FEATURES: Record<PlanType, PlanFeatures> = {
  community: {
    resources_per_scan: -1,      // v4.0: UNLIMITED
    scans_per_month: -1,         // v4.0: UNLIMITED
    aws_accounts: 1,
    machines: 1,
    export_formats: ['json'],    // JSON only (with upgrade metadata)
  },
  pro: {
    resources_per_scan: -1,
    scans_per_month: -1,
    aws_accounts: 3,
    machines: 2,
    export_formats: ['json', 'terraform', 'csv', 'html', 'markdown'],
  },
  team: {
    resources_per_scan: -1,
    scans_per_month: -1,
    aws_accounts: 10,
    machines: 10,
    export_formats: ['json', 'terraform', 'csv', 'html', 'markdown', 'pdf'],
  },
  sovereign: {
    resources_per_scan: -1,
    scans_per_month: -1,
    aws_accounts: -1,            // Unlimited
    machines: -1,                // Unlimited
    export_formats: ['json', 'terraform', 'csv', 'html', 'markdown', 'pdf'],
  },
};

/**
 * Plan features with legacy aliases for backward compatibility.
 * - `free` → `community`
 * - `solo` → `pro`
 * - `enterprise` → `sovereign`
 */
export const PLAN_FEATURES: Record<string, PlanFeatures> = {
  ...V4_PLAN_FEATURES,
  // Legacy aliases
  free: V4_PLAN_FEATURES.community,
  solo: V4_PLAN_FEATURES.pro,
  enterprise: V4_PLAN_FEATURES.sovereign,
};

// ============================================================================
// Machine Change Limits
// ============================================================================

/** Maximum machine changes allowed per month */
export const MAX_MACHINE_CHANGES_PER_MONTH = 3;

// ============================================================================
// Plan Hierarchy (for upgrade/downgrade detection)
// ============================================================================

/**
 * Plan rank - higher number = higher tier plan
 * Used to detect upgrades vs downgrades
 */
export const PLAN_RANK: Record<string, number> = {
  // v4.0 plans
  community: 0,
  pro: 1,
  team: 2,
  sovereign: 3,
  // Legacy plans (mapped to v4.0 equivalents)
  free: 0,
  solo: 1,
  enterprise: 3,
};

/**
 * Check if changing from oldPlan to newPlan is a downgrade.
 * A downgrade means moving to a lower tier plan (fewer features/limits).
 */
export function isPlanDowngrade(oldPlan: string, newPlan: string): boolean {
  const oldRank = PLAN_RANK[normalizePlanName(oldPlan)] ?? 0;
  const newRank = PLAN_RANK[normalizePlanName(newPlan)] ?? 0;
  return newRank < oldRank;
}

/**
 * Check if changing from oldPlan to newPlan is an upgrade.
 */
export function isPlanUpgrade(oldPlan: string, newPlan: string): boolean {
  const oldRank = PLAN_RANK[normalizePlanName(oldPlan)] ?? 0;
  const newRank = PLAN_RANK[normalizePlanName(newPlan)] ?? 0;
  return newRank > oldRank;
}

// ============================================================================
// Cache Configuration
// ============================================================================

/** Default cache duration for valid licenses (24 hours) */
export const DEFAULT_CACHE_HOURS = 24;

/** Grace period after subscription ends (7 days) */
export const GRACE_PERIOD_DAYS = 7;

// ============================================================================
// Rate Limiting
// ============================================================================

export const RATE_LIMITS = {
  validate: {
    requests: 100,
    window: 60, // seconds
  },
  activate: {
    requests: 10,
    window: 60,
  },
  deactivate: {
    requests: 10,
    window: 60,
  },
  // Admin endpoints: stricter limits to prevent brute-force attacks
  admin: {
    requests: 10,
    window: 60,
  },
  // Metrics endpoints: moderate limits for analytics access
  metrics: {
    requests: 30,
    window: 60,
  },
} as const;

// ============================================================================
// Validation Patterns
// ============================================================================

/** License key format: RM-XXXX-XXXX-XXXX-XXXX (uppercase alphanumeric) */
export const LICENSE_KEY_PATTERN = /^RM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$/;

/** Machine ID format: 32 character lowercase hex */
export const MACHINE_ID_PATTERN = /^[a-f0-9]{32}$/;

/** AWS Account ID format: 12 digits */
export const AWS_ACCOUNT_ID_PATTERN = /^\d{12}$/;

// ============================================================================
// Plan Pricing v4.0
// Updated: 2025-01-15
// v4.0 Pricing: Community $0, Pro $29, Team $99, Sovereign $2,500
// ============================================================================

/**
 * Plan prices in cents (monthly)
 */
export const PLAN_PRICES: Record<string, number> = {
  'community': 0,
  'pro': 2900,           // $29/month
  'team': 9900,          // $99/month
  'sovereign': 250000,   // $2,500/month
  // Legacy plan prices (mapped to v4.0)
  'free': 0,
  'solo': 2900,          // $29/month (same as PRO)
  'enterprise': 250000,  // $2,500/month (same as SOVEREIGN)
} as const;

/**
 * Annual plan prices in cents (total per year)
 * 2 months free compared to monthly billing
 */
export const PLAN_ANNUAL_PRICES: Record<string, number> = {
  'community': 0,
  'pro': 29000,          // $290/year (~$24/month, 2 months free)
  'team': 99000,         // $990/year (~$83/month, 2 months free)
  'sovereign': 2500000,  // $25,000/year (~$2,083/month, 2 months free)
  // Legacy plans
  'free': 0,
  'solo': 29000,
  'enterprise': 2500000,
} as const;

/**
 * Lifetime plan prices in cents (one-time payment)
 */
export const PLAN_LIFETIME_PRICES: Record<string, number | null> = {
  'community': null,     // No lifetime for free tier
  'pro': 19900,          // $199 Early Bird (Regular: $249)
  'team': 49900,         // $499 Early Bird (Regular: $699)
  'sovereign': null,     // No lifetime for enterprise
  // Legacy plans
  'free': null,
  'solo': 19900,
  'enterprise': null,
} as const;

// ============================================================================
// Stripe Price ID to Plan Mapping v4.0
// ============================================================================

// TODO: Update these Stripe Price IDs after creating new prices in Stripe Dashboard
export const STRIPE_PRICE_TO_PLAN: Record<string, PlanType> = {
  // Development/test price IDs - Monthly v4.0
  'price_v4_pro_monthly': 'pro',
  'price_v4_team_monthly': 'team',
  'price_v4_sovereign_monthly': 'sovereign',

  // Development/test price IDs - Annual v4.0
  'price_v4_pro_annual': 'pro',
  'price_v4_team_annual': 'team',
  'price_v4_sovereign_annual': 'sovereign',

  // Legacy price IDs (keep for backward compatibility)
  'price_1SiMWsAKLIiL9hdweoTnH17A': 'pro',   // Legacy solo → pro
  'price_1SiMYgAKLIiL9hdwZLjLUOPm': 'pro',   // Legacy pro → pro
  'price_1SiMZvAKLIiL9hdw8LAIvjrS': 'team',  // Legacy team → team
  'price_1SiMpmAKLIiL9hdwhhn1dAVG': 'pro',   // Legacy solo annual
  'price_1SiMqMAKLIiL9hdwj1EgfQMs': 'pro',   // Legacy pro annual
  'price_1SiMrJAKLIiL9hdwF8xq4poz': 'team',  // Legacy team annual

  // Test price IDs (for unit testing) - Monthly
  'price_test_pro': 'pro',
  'price_test_team': 'team',
  'price_test_sovereign': 'sovereign',

  // Test price IDs (for unit testing) - Annual
  'price_test_pro_annual': 'pro',
  'price_test_team_annual': 'team',
  'price_test_sovereign_annual': 'sovereign',

  // Legacy test price IDs (for backward compatibility)
  'price_test_solo': 'pro',         // solo → pro
  'price_test_solo_annual': 'pro',  // solo annual → pro
};

/**
 * Plan to Stripe Price ID (for creating checkout sessions)
 * TODO: Update these after creating new prices in Stripe Dashboard
 */
export const PLAN_TO_STRIPE_PRICE: Record<string, string> = {
  // v4.0 Monthly prices
  'pro': 'price_v4_pro_monthly',
  'team': 'price_v4_team_monthly',
  'sovereign': 'price_v4_sovereign_monthly',
  // Legacy aliases
  'solo': 'price_v4_pro_monthly',  // solo → pro
};

/**
 * Plan to Stripe Annual Price ID (for annual checkout sessions)
 */
export const PLAN_TO_STRIPE_ANNUAL_PRICE: Record<string, string> = {
  'pro': 'price_v4_pro_annual',
  'team': 'price_v4_team_annual',
  'sovereign': 'price_v4_sovereign_annual',
};

/**
 * Get plan type from Stripe price ID
 */
export function getPlanFromPriceId(priceId: string): PlanType {
  return STRIPE_PRICE_TO_PLAN[priceId] ?? 'community';
}

// ============================================================================
// Lifetime Price ID Configuration
// ============================================================================

/**
 * Stripe Lifetime Price ID to Plan mapping.
 * These are one-time payment products, not subscriptions.
 */
export const STRIPE_LIFETIME_PRICE_TO_PLAN: Record<string, { plan: PlanType; billingType: PlanBillingType }> = {
  // Development/test lifetime price IDs - v4.0
  'price_v4_pro_lifetime': { plan: 'pro', billingType: 'lifetime' },
  'price_v4_team_lifetime': { plan: 'team', billingType: 'lifetime' },

  // Legacy test price IDs
  'price_test_pro_lifetime': { plan: 'pro', billingType: 'lifetime' },
  'price_test_team_lifetime': { plan: 'team', billingType: 'lifetime' },
  'price_test_solo_lifetime': { plan: 'pro', billingType: 'lifetime' },  // solo → pro
};

/**
 * Check if a price ID is for a lifetime deal.
 */
export function isLifetimePriceId(priceId: string): boolean {
  return priceId in STRIPE_LIFETIME_PRICE_TO_PLAN;
}

/**
 * Get plan info from price ID, including billing type.
 * Checks both subscription and lifetime price mappings.
 */
export function getPlanInfoFromPriceId(priceId: string): { plan: PlanType; billingType: PlanBillingType } {
  // Check lifetime prices first
  if (priceId in STRIPE_LIFETIME_PRICE_TO_PLAN) {
    return STRIPE_LIFETIME_PRICE_TO_PLAN[priceId];
  }

  // Check annual prices
  const annualPrices = Object.values(PLAN_TO_STRIPE_ANNUAL_PRICE);
  if (annualPrices.includes(priceId)) {
    return { plan: STRIPE_PRICE_TO_PLAN[priceId] ?? 'community', billingType: 'annual' };
  }

  // Default to monthly subscription
  return { plan: STRIPE_PRICE_TO_PLAN[priceId] ?? 'community', billingType: 'monthly' };
}

/**
 * Get dynamic Stripe price mapping from environment variables.
 * This allows configuring lifetime price IDs without code changes.
 */
export function getStripePriceMapping(env: Env): Record<string, { plan: PlanType; billingType: PlanBillingType }> {
  const mapping: Record<string, { plan: PlanType; billingType: PlanBillingType }> = {
    ...STRIPE_LIFETIME_PRICE_TO_PLAN,
  };

  // Add monthly subscriptions
  for (const [priceId, plan] of Object.entries(STRIPE_PRICE_TO_PLAN)) {
    mapping[priceId] = { plan, billingType: 'monthly' };
  }

  // Add annual subscriptions
  for (const [plan, priceId] of Object.entries(PLAN_TO_STRIPE_ANNUAL_PRICE)) {
    if (priceId) {
      mapping[priceId] = { plan: plan as PlanType, billingType: 'annual' };
    }
  }

  // Add lifetime prices from environment if configured
  if (env.STRIPE_PRO_LIFETIME_PRICE_ID) {
    mapping[env.STRIPE_PRO_LIFETIME_PRICE_ID] = { plan: 'pro', billingType: 'lifetime' };
  }
  if (env.STRIPE_TEAM_LIFETIME_PRICE_ID) {
    mapping[env.STRIPE_TEAM_LIFETIME_PRICE_ID] = { plan: 'team', billingType: 'lifetime' };
  }

  return mapping;
}

/**
 * Get lifetime price IDs from environment.
 */
export function getLifetimePriceIds(env: Env): string[] {
  const ids: string[] = [];
  if (env.STRIPE_PRO_LIFETIME_PRICE_ID) ids.push(env.STRIPE_PRO_LIFETIME_PRICE_ID);
  if (env.STRIPE_TEAM_LIFETIME_PRICE_ID) ids.push(env.STRIPE_TEAM_LIFETIME_PRICE_ID);
  return ids;
}

// ============================================================================
// API URLs
// ============================================================================

export const REPLIMAP_URLS = {
  dashboard: 'https://replimap.com/dashboard',
  renew: 'https://replimap.com/renew',
  upgrade: 'https://replimap.com/upgrade',
  support: 'https://replimap.com/support',
  pricing: 'https://replimap.com/pricing',
} as const;

// ============================================================================
// CLI Version Compatibility
// ============================================================================

/** Minimum supported CLI version (semver) */
export const MIN_CLI_VERSION = '1.0.0';

/** Current latest CLI version */
export const LATEST_CLI_VERSION = '1.0.0';

/** Deprecated versions that still work but show warning */
export const DEPRECATED_CLI_VERSIONS = ['0.9.0', '0.9.1', '0.9.2'];

/**
 * Check if CLI version is compatible
 * Returns: 'ok' | 'deprecated' | 'unsupported'
 */
export function checkCliVersion(version: string | undefined): {
  status: 'ok' | 'deprecated' | 'unsupported';
  message?: string;
  latest_version: string;
  upgrade_url: string;
} {
  const upgradeUrl = 'https://replimap.com/docs/upgrade';

  if (!version) {
    return {
      status: 'ok',
      latest_version: LATEST_CLI_VERSION,
      upgrade_url: upgradeUrl,
    };
  }

  // Check if deprecated (check this first, before version comparison)
  if (DEPRECATED_CLI_VERSIONS.includes(version)) {
    return {
      status: 'deprecated',
      message: `CLI version ${version} is deprecated. Please upgrade to ${LATEST_CLI_VERSION}.`,
      latest_version: LATEST_CLI_VERSION,
      upgrade_url: upgradeUrl,
    };
  }

  // Parse versions for comparison
  const current = parseVersion(version);
  const minimum = parseVersion(MIN_CLI_VERSION);

  if (!current || !minimum) {
    return {
      status: 'ok',
      latest_version: LATEST_CLI_VERSION,
      upgrade_url: upgradeUrl,
    };
  }

  // Check if unsupported (below minimum)
  if (compareVersions(current, minimum) < 0) {
    return {
      status: 'unsupported',
      message: `CLI version ${version} is no longer supported. Please upgrade to ${LATEST_CLI_VERSION}.`,
      latest_version: LATEST_CLI_VERSION,
      upgrade_url: upgradeUrl,
    };
  }

  return {
    status: 'ok',
    latest_version: LATEST_CLI_VERSION,
    upgrade_url: upgradeUrl,
  };
}

function parseVersion(version: string): [number, number, number] | null {
  const match = version.match(/^(\d+)\.(\d+)\.(\d+)/);
  if (!match) return null;
  return [parseInt(match[1]), parseInt(match[2]), parseInt(match[3])];
}

function compareVersions(a: [number, number, number], b: [number, number, number]): number {
  for (let i = 0; i < 3; i++) {
    if (a[i] > b[i]) return 1;
    if (a[i] < b[i]) return -1;
  }
  return 0;
}
