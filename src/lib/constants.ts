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
  'price_test_solo': 'solo',
  'price_test_pro': 'pro',
  'price_test_team': 'team',
  // Production price IDs - update these after creating products in Stripe
  // 'price_xxx_solo': 'solo',
  // 'price_xxx_pro': 'pro',
  // 'price_xxx_team': 'team',
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
