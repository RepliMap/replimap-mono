/**
 * Shared configuration from @replimap/config
 * Re-exports and helper functions for the web app
 */

import {
  PLANS,
  PLAN_NAMES,
  CONFIG_VERSION,
  COMPLIANCE_FRAMEWORKS,
  FRAMEWORK_IDS,
  isPlanName,
  isFrameworkId,
  getPlanFeatures,
  type PlanName,
  type PlanConfig,
  type FrameworkId,
  type FrameworkConfig,
} from '@replimap/config';

// Re-export everything
export {
  PLANS,
  PLAN_NAMES,
  CONFIG_VERSION,
  COMPLIANCE_FRAMEWORKS,
  FRAMEWORK_IDS,
  isPlanName,
  isFrameworkId,
  getPlanFeatures,
  type PlanName,
  type PlanConfig,
  type FrameworkId,
  type FrameworkConfig,
};

/**
 * Get the monthly price for a plan in cents
 */
export function getPlanPrice(planId: string): number {
  if (!isPlanName(planId)) return 0;
  return PLANS[planId].price_monthly;
}

/**
 * Get the monthly price for a plan formatted as currency
 */
export function getPlanPriceFormatted(planId: string): string {
  const cents = getPlanPrice(planId);
  if (cents === 0) return 'Free';
  return `$${(cents / 100).toFixed(0)}/mo`;
}

/**
 * Check if a plan has unlimited scans
 */
export function hasUnlimitedScans(planId: string): boolean {
  if (!isPlanName(planId)) return false;
  return PLANS[planId].scans_per_month === null;
}
