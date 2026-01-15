/**
 * Shared configuration from @replimap/config
 * Re-exports and helper functions for the API
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
 * Validate that a plan ID is valid
 */
export function validatePlan(planId: string): boolean {
  return isPlanName(planId);
}

/**
 * Get the scans limit for a plan (null = unlimited)
 */
export function getPlanScansLimit(planId: string): number | null {
  if (!isPlanName(planId)) return 0;
  return PLANS[planId].scans_per_month;
}

/**
 * Check if a user has access to a feature based on their plan
 */
export function hasFeatureAccess(planId: string, feature: string): boolean {
  if (!isPlanName(planId)) return false;
  const features = getPlanFeatures(planId);
  return features.includes(feature);
}

/**
 * Get the price in cents for a plan
 */
export function getPlanPriceCents(planId: string): number {
  if (!isPlanName(planId)) return 0;
  return PLANS[planId].price_monthly;
}
