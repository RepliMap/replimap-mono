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
// Stripe Price ID to Plan Mapping
// ============================================================================

// These should be updated with actual Stripe price IDs after creation
export const STRIPE_PRICE_TO_PLAN: Record<string, PlanType> = {
  // Development/test price IDs
  'price_1Sg0KVAKLIiL9hdwiQFS1xZC': 'solo',
  'price_1Sg0KxAKLIiL9hdw4c6KcQRI': 'pro',
  'price_1Sg0MVAKLIiL9hdwB2DEfWus': 'team',
  // Production price IDs - update these after creating products in Stripe
  // 'price_xxx_solo': 'solo',
  // 'price_xxx_pro': 'pro',
  // 'price_xxx_team': 'team',
};

// Plan to Stripe Price ID (for creating checkout sessions)
// Update these with actual Stripe price IDs after creating products
export const PLAN_TO_STRIPE_PRICE: Record<string, string> = {
  // Development/test price IDs
  'solo': 'price_1Sg0KVAKLIiL9hdwiQFS1xZC',
  'pro': 'price_1Sg0KxAKLIiL9hdw4c6KcQRI',
  'team': 'price_1Sg0MVAKLIiL9hdwB2DEfWus',
  // Production - uncomment and update after creating products in Stripe:
  // 'solo': 'price_xxx_solo_monthly',
  // 'pro': 'price_xxx_pro_monthly',
  // 'team': 'price_xxx_team_monthly',
};

// Plan prices in cents (for display purposes)
export const PLAN_PRICES: Record<string, number> = {
  'free': 0,
  'solo': 4900,  // $49/month
  'pro': 9900,   // $99/month
  'team': 19900, // $199/month
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
