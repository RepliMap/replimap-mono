/**
 * Constants and configuration for RepliMap Backend
 */

import type { PlanFeatures } from '../types';

// ============================================================================
// Plan Configuration
// ============================================================================

export type PlanType = 'free' | 'solo' | 'pro' | 'team';

export const PLAN_FEATURES: Record<PlanType, PlanFeatures> = {
  free: {
    resources_per_scan: 5,
    scans_per_month: 3,
    aws_accounts: 1,
    machines: 1,
    export_formats: ['terraform'],
  },
  solo: {
    resources_per_scan: -1, // unlimited
    scans_per_month: -1,    // unlimited
    aws_accounts: 1,
    machines: 2,
    export_formats: ['terraform', 'cloudformation'],
  },
  pro: {
    resources_per_scan: -1,
    scans_per_month: -1,
    aws_accounts: 3,
    machines: 3,
    export_formats: ['terraform', 'cloudformation'],
  },
  team: {
    resources_per_scan: -1,
    scans_per_month: -1,
    aws_accounts: 10,
    machines: 10,
    export_formats: ['terraform', 'cloudformation'],
  },
};

// ============================================================================
// Machine Change Limits
// ============================================================================

/** Maximum machine changes allowed per month */
export const MAX_MACHINE_CHANGES_PER_MONTH = 3;

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
// Plan Pricing
// Updated: 2025-12-25
// New pricing: Solo $29, Pro $79, Team $149, Enterprise $399
// ============================================================================

/**
 * Plan prices in cents (monthly)
 */
export const PLAN_PRICES: Record<string, number> = {
  'free': 0,
  'solo': 2900,       // $29/month
  'pro': 7900,        // $79/month
  'team': 14900,      // $149/month
  'enterprise': 39900, // $399/month
} as const;

/**
 * Annual plan prices in cents (total per year)
 * Significant discount compared to monthly billing
 */
export const PLAN_ANNUAL_PRICES: Record<string, number> = {
  'free': 0,
  'solo': 19900,       // $199/year (~$17/month, save $149)
  'pro': 59900,        // $599/year (~$50/month, save $349)
  'team': 119900,      // $1,199/year (~$100/month, save $589)
  'enterprise': 399900, // $3,999/year (~$333/month, save $789)
} as const;

// ============================================================================
// Stripe Price ID to Plan Mapping
// ============================================================================

// TODO: Update these Stripe Price IDs after creating new prices in Stripe Dashboard
// Current IDs are for OLD pricing ($49/$99/$199) and need to be replaced
export const STRIPE_PRICE_TO_PLAN: Record<string, PlanType> = {
  // Development/test price IDs (OLD PRICING - needs update)
  'price_1SiMWsAKLIiL9hdweoTnH17A': 'solo',  // DONE: Replace with $29/mo price
  'price_1SiMYgAKLIiL9hdwZLjLUOPm': 'pro',   // DONE: Replace with $79/mo price
  'price_1SiMZvAKLIiL9hdw8LAIvjrS': 'team',  // DONE: Replace with $149/mo price
  // Test price IDs (for unit testing)
  'price_test_solo': 'solo',
  'price_test_pro': 'pro',
  'price_test_team': 'team',
  // Production price IDs - add after creating products in Stripe:
  // Monthly
  // 'price_xxx_solo_monthly': 'solo',     // $29/mo
  // 'price_xxx_pro_monthly': 'pro',       // $79/mo
  // 'price_xxx_team_monthly': 'team',     // $149/mo
  // Annual
  // 'price_xxx_solo_annual': 'solo',      // $199/year
  // 'price_xxx_pro_annual': 'pro',        // $599/year
  // 'price_xxx_team_annual': 'team',      // $1,199/year
};

/**
 * Plan to Stripe Price ID (for creating checkout sessions)
 * TODO: Update these after creating new prices in Stripe Dashboard
 */
export const PLAN_TO_STRIPE_PRICE: Record<string, string> = {
  // Monthly prices (OLD PRICING - needs update)
  'solo': 'price_1SiMWsAKLIiL9hdweoTnH17A',  // DONE: Create new $29/mo price
  'pro': 'price_1SiMYgAKLIiL9hdwZLjLUOPm',   // DONE: Create new $79/mo price
  'team': 'price_1SiMZvAKLIiL9hdw8LAIvjrS',  // DONE: Create new $149/mo price
  // Production - uncomment and update after creating products in Stripe:
  // 'solo': 'price_xxx_solo_monthly',
  // 'pro': 'price_xxx_pro_monthly',
  // 'team': 'price_xxx_team_monthly',
};

/**
 * Plan to Stripe Annual Price ID (for annual checkout sessions)
 * TODO: Create annual price IDs in Stripe Dashboard
 */
export const PLAN_TO_STRIPE_ANNUAL_PRICE: Record<string, string> = {
  'solo': 'price_1SiMpmAKLIiL9hdwhhn1dAVG',  // DONE: Create $199/year price
  'pro': 'price_1SiMqMAKLIiL9hdwj1EgfQMs',   // DONE: Create $599/year price
  'team': 'price_1SiMrJAKLIiL9hdwF8xq4poz',  // DONE: Create $1,199/year price
};

/**
 * Get plan type from Stripe price ID
 */
export function getPlanFromPriceId(priceId: string): PlanType {
  return STRIPE_PRICE_TO_PLAN[priceId] ?? 'free';
}

// ============================================================================
// API URLs
// ============================================================================

export const REPLIMAP_URLS = {
  dashboard: 'https://replimap.io/dashboard',
  renew: 'https://replimap.io/renew',
  upgrade: 'https://replimap.io/upgrade',
  support: 'https://replimap.io/support',
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
  const upgradeUrl = 'https://replimap.io/docs/upgrade';

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
