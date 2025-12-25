/**
 * Right-Sizer Rules Database
 *
 * Hardcoded downgrade rules for common AWS instance types.
 * Contains the top 30+ most common instance types with pricing.
 *
 * Pricing: Approximate monthly cost in USD (us-east-1 baseline, on-demand)
 * Source: AWS Pricing as of 2024-Q4
 *
 * Future: Replace with AWS Pricing API integration for real-time data
 */

// =============================================================================
// Types
// =============================================================================

export interface InstanceSpec {
  type: string;
  vcpu: number;
  memory_gb: number;
  baseline_monthly_usd: number;
  family: string;
  generation: number;
  size: string;
}

export type ResourceCategory = 'ec2' | 'rds' | 'elasticache';
export type DowngradeStrategy = 'conservative' | 'moderate' | 'aggressive';

// =============================================================================
// Regional Price Multipliers (relative to us-east-1)
// =============================================================================

export const REGIONAL_MULTIPLIERS: Record<string, number> = {
  'us-east-1': 1.0,
  'us-east-2': 1.0,
  'us-west-1': 1.08,
  'us-west-2': 1.0,
  'eu-west-1': 1.1,
  'eu-west-2': 1.12,
  'eu-west-3': 1.14,
  'eu-central-1': 1.15,
  'eu-north-1': 1.08,
  'ap-southeast-1': 1.12,
  'ap-southeast-2': 1.15,
  'ap-northeast-1': 1.18,
  'ap-northeast-2': 1.14,
  'ap-northeast-3': 1.16,
  'ap-south-1': 1.08,
  'sa-east-1': 1.25,
  'ca-central-1': 1.05,
  'me-south-1': 1.18,
  'af-south-1': 1.2,
};

const DEFAULT_MULTIPLIER = 1.15;

// =============================================================================
// EC2 Instance Specifications (us-east-1 on-demand pricing)
// =============================================================================

export const EC2_INSTANCES: Record<string, InstanceSpec> = {
  // T3 Family (Burstable - great for dev/staging)
  't3.nano': { type: 't3.nano', vcpu: 2, memory_gb: 0.5, baseline_monthly_usd: 3.80, family: 't3', generation: 3, size: 'nano' },
  't3.micro': { type: 't3.micro', vcpu: 2, memory_gb: 1, baseline_monthly_usd: 7.59, family: 't3', generation: 3, size: 'micro' },
  't3.small': { type: 't3.small', vcpu: 2, memory_gb: 2, baseline_monthly_usd: 15.18, family: 't3', generation: 3, size: 'small' },
  't3.medium': { type: 't3.medium', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 30.37, family: 't3', generation: 3, size: 'medium' },
  't3.large': { type: 't3.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 60.74, family: 't3', generation: 3, size: 'large' },
  't3.xlarge': { type: 't3.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 121.47, family: 't3', generation: 3, size: 'xlarge' },
  't3.2xlarge': { type: 't3.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 242.94, family: 't3', generation: 3, size: '2xlarge' },

  // T3a Family (AMD - cheaper alternative)
  't3a.nano': { type: 't3a.nano', vcpu: 2, memory_gb: 0.5, baseline_monthly_usd: 3.42, family: 't3a', generation: 3, size: 'nano' },
  't3a.micro': { type: 't3a.micro', vcpu: 2, memory_gb: 1, baseline_monthly_usd: 6.84, family: 't3a', generation: 3, size: 'micro' },
  't3a.small': { type: 't3a.small', vcpu: 2, memory_gb: 2, baseline_monthly_usd: 13.68, family: 't3a', generation: 3, size: 'small' },
  't3a.medium': { type: 't3a.medium', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 27.38, family: 't3a', generation: 3, size: 'medium' },
  't3a.large': { type: 't3a.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 54.75, family: 't3a', generation: 3, size: 'large' },
  't3a.xlarge': { type: 't3a.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 109.50, family: 't3a', generation: 3, size: 'xlarge' },
  't3a.2xlarge': { type: 't3a.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 219.00, family: 't3a', generation: 3, size: '2xlarge' },

  // M5 Family (General Purpose)
  'm5.large': { type: 'm5.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 70.08, family: 'm5', generation: 5, size: 'large' },
  'm5.xlarge': { type: 'm5.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 140.16, family: 'm5', generation: 5, size: 'xlarge' },
  'm5.2xlarge': { type: 'm5.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 280.32, family: 'm5', generation: 5, size: '2xlarge' },
  'm5.4xlarge': { type: 'm5.4xlarge', vcpu: 16, memory_gb: 64, baseline_monthly_usd: 560.64, family: 'm5', generation: 5, size: '4xlarge' },
  'm5.8xlarge': { type: 'm5.8xlarge', vcpu: 32, memory_gb: 128, baseline_monthly_usd: 1121.28, family: 'm5', generation: 5, size: '8xlarge' },
  'm5.12xlarge': { type: 'm5.12xlarge', vcpu: 48, memory_gb: 192, baseline_monthly_usd: 1681.92, family: 'm5', generation: 5, size: '12xlarge' },
  'm5.16xlarge': { type: 'm5.16xlarge', vcpu: 64, memory_gb: 256, baseline_monthly_usd: 2242.56, family: 'm5', generation: 5, size: '16xlarge' },

  // M6i Family (Latest Gen General Purpose)
  'm6i.large': { type: 'm6i.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 70.08, family: 'm6i', generation: 6, size: 'large' },
  'm6i.xlarge': { type: 'm6i.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 140.16, family: 'm6i', generation: 6, size: 'xlarge' },
  'm6i.2xlarge': { type: 'm6i.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 280.32, family: 'm6i', generation: 6, size: '2xlarge' },
  'm6i.4xlarge': { type: 'm6i.4xlarge', vcpu: 16, memory_gb: 64, baseline_monthly_usd: 560.64, family: 'm6i', generation: 6, size: '4xlarge' },
  'm6i.8xlarge': { type: 'm6i.8xlarge', vcpu: 32, memory_gb: 128, baseline_monthly_usd: 1121.28, family: 'm6i', generation: 6, size: '8xlarge' },

  // R5 Family (Memory Optimized)
  'r5.large': { type: 'r5.large', vcpu: 2, memory_gb: 16, baseline_monthly_usd: 91.98, family: 'r5', generation: 5, size: 'large' },
  'r5.xlarge': { type: 'r5.xlarge', vcpu: 4, memory_gb: 32, baseline_monthly_usd: 183.96, family: 'r5', generation: 5, size: 'xlarge' },
  'r5.2xlarge': { type: 'r5.2xlarge', vcpu: 8, memory_gb: 64, baseline_monthly_usd: 367.92, family: 'r5', generation: 5, size: '2xlarge' },
  'r5.4xlarge': { type: 'r5.4xlarge', vcpu: 16, memory_gb: 128, baseline_monthly_usd: 735.84, family: 'r5', generation: 5, size: '4xlarge' },
  'r5.8xlarge': { type: 'r5.8xlarge', vcpu: 32, memory_gb: 256, baseline_monthly_usd: 1471.68, family: 'r5', generation: 5, size: '8xlarge' },

  // R6i Family (Latest Gen Memory Optimized)
  'r6i.large': { type: 'r6i.large', vcpu: 2, memory_gb: 16, baseline_monthly_usd: 91.98, family: 'r6i', generation: 6, size: 'large' },
  'r6i.xlarge': { type: 'r6i.xlarge', vcpu: 4, memory_gb: 32, baseline_monthly_usd: 183.96, family: 'r6i', generation: 6, size: 'xlarge' },
  'r6i.2xlarge': { type: 'r6i.2xlarge', vcpu: 8, memory_gb: 64, baseline_monthly_usd: 367.92, family: 'r6i', generation: 6, size: '2xlarge' },
  'r6i.4xlarge': { type: 'r6i.4xlarge', vcpu: 16, memory_gb: 128, baseline_monthly_usd: 735.84, family: 'r6i', generation: 6, size: '4xlarge' },

  // C5 Family (Compute Optimized)
  'c5.large': { type: 'c5.large', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 62.05, family: 'c5', generation: 5, size: 'large' },
  'c5.xlarge': { type: 'c5.xlarge', vcpu: 4, memory_gb: 8, baseline_monthly_usd: 124.10, family: 'c5', generation: 5, size: 'xlarge' },
  'c5.2xlarge': { type: 'c5.2xlarge', vcpu: 8, memory_gb: 16, baseline_monthly_usd: 248.20, family: 'c5', generation: 5, size: '2xlarge' },
  'c5.4xlarge': { type: 'c5.4xlarge', vcpu: 16, memory_gb: 32, baseline_monthly_usd: 496.40, family: 'c5', generation: 5, size: '4xlarge' },
  'c5.9xlarge': { type: 'c5.9xlarge', vcpu: 36, memory_gb: 72, baseline_monthly_usd: 1116.90, family: 'c5', generation: 5, size: '9xlarge' },

  // C6i Family (Latest Gen Compute Optimized)
  'c6i.large': { type: 'c6i.large', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 62.05, family: 'c6i', generation: 6, size: 'large' },
  'c6i.xlarge': { type: 'c6i.xlarge', vcpu: 4, memory_gb: 8, baseline_monthly_usd: 124.10, family: 'c6i', generation: 6, size: 'xlarge' },
  'c6i.2xlarge': { type: 'c6i.2xlarge', vcpu: 8, memory_gb: 16, baseline_monthly_usd: 248.20, family: 'c6i', generation: 6, size: '2xlarge' },
  'c6i.4xlarge': { type: 'c6i.4xlarge', vcpu: 16, memory_gb: 32, baseline_monthly_usd: 496.40, family: 'c6i', generation: 6, size: '4xlarge' },
};

// =============================================================================
// RDS Instance Specifications
// =============================================================================

export const RDS_INSTANCES: Record<string, InstanceSpec> = {
  // db.t3 Family (Burstable)
  'db.t3.micro': { type: 'db.t3.micro', vcpu: 2, memory_gb: 1, baseline_monthly_usd: 12.41, family: 'db.t3', generation: 3, size: 'micro' },
  'db.t3.small': { type: 'db.t3.small', vcpu: 2, memory_gb: 2, baseline_monthly_usd: 24.82, family: 'db.t3', generation: 3, size: 'small' },
  'db.t3.medium': { type: 'db.t3.medium', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 49.64, family: 'db.t3', generation: 3, size: 'medium' },
  'db.t3.large': { type: 'db.t3.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 99.28, family: 'db.t3', generation: 3, size: 'large' },
  'db.t3.xlarge': { type: 'db.t3.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 198.56, family: 'db.t3', generation: 3, size: 'xlarge' },
  'db.t3.2xlarge': { type: 'db.t3.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 397.12, family: 'db.t3', generation: 3, size: '2xlarge' },

  // db.t4g Family (Graviton - ARM)
  'db.t4g.micro': { type: 'db.t4g.micro', vcpu: 2, memory_gb: 1, baseline_monthly_usd: 11.83, family: 'db.t4g', generation: 4, size: 'micro' },
  'db.t4g.small': { type: 'db.t4g.small', vcpu: 2, memory_gb: 2, baseline_monthly_usd: 23.65, family: 'db.t4g', generation: 4, size: 'small' },
  'db.t4g.medium': { type: 'db.t4g.medium', vcpu: 2, memory_gb: 4, baseline_monthly_usd: 47.30, family: 'db.t4g', generation: 4, size: 'medium' },
  'db.t4g.large': { type: 'db.t4g.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 94.61, family: 'db.t4g', generation: 4, size: 'large' },

  // db.m5 Family (General Purpose)
  'db.m5.large': { type: 'db.m5.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 124.10, family: 'db.m5', generation: 5, size: 'large' },
  'db.m5.xlarge': { type: 'db.m5.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 248.20, family: 'db.m5', generation: 5, size: 'xlarge' },
  'db.m5.2xlarge': { type: 'db.m5.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 496.40, family: 'db.m5', generation: 5, size: '2xlarge' },
  'db.m5.4xlarge': { type: 'db.m5.4xlarge', vcpu: 16, memory_gb: 64, baseline_monthly_usd: 992.80, family: 'db.m5', generation: 5, size: '4xlarge' },
  'db.m5.8xlarge': { type: 'db.m5.8xlarge', vcpu: 32, memory_gb: 128, baseline_monthly_usd: 1985.60, family: 'db.m5', generation: 5, size: '8xlarge' },

  // db.m6i Family (Latest Gen)
  'db.m6i.large': { type: 'db.m6i.large', vcpu: 2, memory_gb: 8, baseline_monthly_usd: 124.10, family: 'db.m6i', generation: 6, size: 'large' },
  'db.m6i.xlarge': { type: 'db.m6i.xlarge', vcpu: 4, memory_gb: 16, baseline_monthly_usd: 248.20, family: 'db.m6i', generation: 6, size: 'xlarge' },
  'db.m6i.2xlarge': { type: 'db.m6i.2xlarge', vcpu: 8, memory_gb: 32, baseline_monthly_usd: 496.40, family: 'db.m6i', generation: 6, size: '2xlarge' },
  'db.m6i.4xlarge': { type: 'db.m6i.4xlarge', vcpu: 16, memory_gb: 64, baseline_monthly_usd: 992.80, family: 'db.m6i', generation: 6, size: '4xlarge' },

  // db.r5 Family (Memory Optimized)
  'db.r5.large': { type: 'db.r5.large', vcpu: 2, memory_gb: 16, baseline_monthly_usd: 175.20, family: 'db.r5', generation: 5, size: 'large' },
  'db.r5.xlarge': { type: 'db.r5.xlarge', vcpu: 4, memory_gb: 32, baseline_monthly_usd: 350.40, family: 'db.r5', generation: 5, size: 'xlarge' },
  'db.r5.2xlarge': { type: 'db.r5.2xlarge', vcpu: 8, memory_gb: 64, baseline_monthly_usd: 700.80, family: 'db.r5', generation: 5, size: '2xlarge' },
  'db.r5.4xlarge': { type: 'db.r5.4xlarge', vcpu: 16, memory_gb: 128, baseline_monthly_usd: 1401.60, family: 'db.r5', generation: 5, size: '4xlarge' },
  'db.r5.8xlarge': { type: 'db.r5.8xlarge', vcpu: 32, memory_gb: 256, baseline_monthly_usd: 2803.20, family: 'db.r5', generation: 5, size: '8xlarge' },

  // db.r6i Family (Latest Gen Memory)
  'db.r6i.large': { type: 'db.r6i.large', vcpu: 2, memory_gb: 16, baseline_monthly_usd: 175.20, family: 'db.r6i', generation: 6, size: 'large' },
  'db.r6i.xlarge': { type: 'db.r6i.xlarge', vcpu: 4, memory_gb: 32, baseline_monthly_usd: 350.40, family: 'db.r6i', generation: 6, size: 'xlarge' },
  'db.r6i.2xlarge': { type: 'db.r6i.2xlarge', vcpu: 8, memory_gb: 64, baseline_monthly_usd: 700.80, family: 'db.r6i', generation: 6, size: '2xlarge' },
  'db.r6i.4xlarge': { type: 'db.r6i.4xlarge', vcpu: 16, memory_gb: 128, baseline_monthly_usd: 1401.60, family: 'db.r6i', generation: 6, size: '4xlarge' },
};

// =============================================================================
// ElastiCache Instance Specifications
// =============================================================================

export const ELASTICACHE_INSTANCES: Record<string, InstanceSpec> = {
  // cache.t3 Family
  'cache.t3.micro': { type: 'cache.t3.micro', vcpu: 2, memory_gb: 0.5, baseline_monthly_usd: 12.41, family: 'cache.t3', generation: 3, size: 'micro' },
  'cache.t3.small': { type: 'cache.t3.small', vcpu: 2, memory_gb: 1.37, baseline_monthly_usd: 24.09, family: 'cache.t3', generation: 3, size: 'small' },
  'cache.t3.medium': { type: 'cache.t3.medium', vcpu: 2, memory_gb: 3.09, baseline_monthly_usd: 48.18, family: 'cache.t3', generation: 3, size: 'medium' },

  // cache.t4g Family (Graviton)
  'cache.t4g.micro': { type: 'cache.t4g.micro', vcpu: 2, memory_gb: 0.5, baseline_monthly_usd: 11.17, family: 'cache.t4g', generation: 4, size: 'micro' },
  'cache.t4g.small': { type: 'cache.t4g.small', vcpu: 2, memory_gb: 1.37, baseline_monthly_usd: 21.69, family: 'cache.t4g', generation: 4, size: 'small' },
  'cache.t4g.medium': { type: 'cache.t4g.medium', vcpu: 2, memory_gb: 3.09, baseline_monthly_usd: 43.37, family: 'cache.t4g', generation: 4, size: 'medium' },

  // cache.m5 Family
  'cache.m5.large': { type: 'cache.m5.large', vcpu: 2, memory_gb: 6.38, baseline_monthly_usd: 111.69, family: 'cache.m5', generation: 5, size: 'large' },
  'cache.m5.xlarge': { type: 'cache.m5.xlarge', vcpu: 4, memory_gb: 12.93, baseline_monthly_usd: 223.38, family: 'cache.m5', generation: 5, size: 'xlarge' },
  'cache.m5.2xlarge': { type: 'cache.m5.2xlarge', vcpu: 8, memory_gb: 26.04, baseline_monthly_usd: 446.76, family: 'cache.m5', generation: 5, size: '2xlarge' },
  'cache.m5.4xlarge': { type: 'cache.m5.4xlarge', vcpu: 16, memory_gb: 52.26, baseline_monthly_usd: 893.52, family: 'cache.m5', generation: 5, size: '4xlarge' },

  // cache.m6g Family (Graviton)
  'cache.m6g.large': { type: 'cache.m6g.large', vcpu: 2, memory_gb: 6.38, baseline_monthly_usd: 100.37, family: 'cache.m6g', generation: 6, size: 'large' },
  'cache.m6g.xlarge': { type: 'cache.m6g.xlarge', vcpu: 4, memory_gb: 12.93, baseline_monthly_usd: 200.75, family: 'cache.m6g', generation: 6, size: 'xlarge' },
  'cache.m6g.2xlarge': { type: 'cache.m6g.2xlarge', vcpu: 8, memory_gb: 26.04, baseline_monthly_usd: 401.49, family: 'cache.m6g', generation: 6, size: '2xlarge' },

  // cache.r5 Family (Memory Optimized)
  'cache.r5.large': { type: 'cache.r5.large', vcpu: 2, memory_gb: 13.07, baseline_monthly_usd: 156.95, family: 'cache.r5', generation: 5, size: 'large' },
  'cache.r5.xlarge': { type: 'cache.r5.xlarge', vcpu: 4, memory_gb: 26.32, baseline_monthly_usd: 313.90, family: 'cache.r5', generation: 5, size: 'xlarge' },
  'cache.r5.2xlarge': { type: 'cache.r5.2xlarge', vcpu: 8, memory_gb: 52.82, baseline_monthly_usd: 627.80, family: 'cache.r5', generation: 5, size: '2xlarge' },
  'cache.r5.4xlarge': { type: 'cache.r5.4xlarge', vcpu: 16, memory_gb: 105.81, baseline_monthly_usd: 1255.60, family: 'cache.r5', generation: 5, size: '4xlarge' },

  // cache.r6g Family (Graviton Memory)
  'cache.r6g.large': { type: 'cache.r6g.large', vcpu: 2, memory_gb: 13.07, baseline_monthly_usd: 141.26, family: 'cache.r6g', generation: 6, size: 'large' },
  'cache.r6g.xlarge': { type: 'cache.r6g.xlarge', vcpu: 4, memory_gb: 26.32, baseline_monthly_usd: 282.51, family: 'cache.r6g', generation: 6, size: 'xlarge' },
  'cache.r6g.2xlarge': { type: 'cache.r6g.2xlarge', vcpu: 8, memory_gb: 52.82, baseline_monthly_usd: 565.02, family: 'cache.r6g', generation: 6, size: '2xlarge' },
};

// =============================================================================
// Size Hierarchy for Downgrade Calculations
// =============================================================================

export const SIZE_HIERARCHY = [
  'nano',
  'micro',
  'small',
  'medium',
  'large',
  'xlarge',
  '2xlarge',
  '4xlarge',
  '8xlarge',
  '9xlarge',
  '12xlarge',
  '16xlarge',
  '24xlarge',
];

// =============================================================================
// Cross-Family Downgrade Recommendations
// For aggressive downgrades, suggest cheaper families
// =============================================================================

const FAMILY_DOWNGRADES: Record<string, string> = {
  // EC2: General Purpose → Burstable
  'm5': 't3',
  'm6i': 't3',
  // EC2: Memory Optimized → General Purpose
  'r5': 'm5',
  'r6i': 'm6i',
  // EC2: Compute Optimized → Burstable
  'c5': 't3',
  'c6i': 't3',
  // RDS: General Purpose → Burstable
  'db.m5': 'db.t3',
  'db.m6i': 'db.t3',
  // RDS: Memory Optimized → General Purpose
  'db.r5': 'db.m5',
  'db.r6i': 'db.m6i',
  // ElastiCache: General Purpose → Burstable
  'cache.m5': 'cache.t3',
  'cache.m6g': 'cache.t4g',
  // ElastiCache: Memory Optimized → General Purpose
  'cache.r5': 'cache.m5',
  'cache.r6g': 'cache.m6g',
};

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Get the instance catalog for a resource category
 */
export function getInstanceCatalog(category: ResourceCategory): Record<string, InstanceSpec> {
  switch (category) {
    case 'ec2':
      return EC2_INSTANCES;
    case 'rds':
      return RDS_INSTANCES;
    case 'elasticache':
      return ELASTICACHE_INSTANCES;
  }
}

/**
 * Get instance spec by type and category
 */
export function getInstanceSpec(
  instanceType: string,
  category: ResourceCategory
): InstanceSpec | null {
  const catalog = getInstanceCatalog(category);
  return catalog[instanceType] ?? null;
}

/**
 * Calculate monthly cost for an instance in a specific region
 */
export function calculateMonthlyCost(
  instanceType: string,
  category: ResourceCategory,
  region: string
): number | null {
  const spec = getInstanceSpec(instanceType, category);
  if (!spec) return null;

  const multiplier = REGIONAL_MULTIPLIERS[region] ?? DEFAULT_MULTIPLIER;
  return Math.round(spec.baseline_monthly_usd * multiplier * 100) / 100;
}

/**
 * Find the target size based on strategy
 */
function getTargetSizeIndex(
  currentSizeIndex: number,
  strategy: DowngradeStrategy
): number {
  switch (strategy) {
    case 'conservative':
      // One size down
      return Math.max(0, currentSizeIndex - 1);
    case 'moderate':
      // Two sizes down
      return Math.max(0, currentSizeIndex - 2);
    case 'aggressive':
      // Go to 'small' or 'micro' for burstable, 'large' for others
      return Math.max(0, Math.min(currentSizeIndex - 3, 2));
  }
}

/**
 * Get downgrade recommendation for an instance
 */
export function getDowngradeRecommendation(
  instanceType: string,
  category: ResourceCategory,
  strategy: DowngradeStrategy
): {
  target: string;
  reason: string;
  warnings: string[];
  confidence: 'high' | 'medium' | 'low';
} | null {
  const catalog = getInstanceCatalog(category);
  const currentSpec = catalog[instanceType];

  if (!currentSpec) {
    return null; // Unknown instance type
  }

  const currentSizeIndex = SIZE_HIERARCHY.indexOf(currentSpec.size);
  if (currentSizeIndex <= 0) {
    return null; // Already at minimum or unknown size
  }

  let targetFamily = currentSpec.family;
  let targetSizeIndex = getTargetSizeIndex(currentSizeIndex, strategy);
  const warnings: string[] = [];
  let confidence: 'high' | 'medium' | 'low' = 'high';

  // For aggressive strategy, consider family downgrade
  if (strategy === 'aggressive') {
    const cheaperFamily = FAMILY_DOWNGRADES[currentSpec.family];
    if (cheaperFamily) {
      targetFamily = cheaperFamily;
      warnings.push(`Switching from ${currentSpec.family} to ${cheaperFamily} family`);
      confidence = 'medium';
    }
  }

  // Find the target size
  const targetSize = SIZE_HIERARCHY[targetSizeIndex];
  const targetType = `${targetFamily}.${targetSize}`;

  // Verify target exists in catalog
  if (!catalog[targetType]) {
    // Try one size up if target doesn't exist
    const fallbackIndex = Math.min(targetSizeIndex + 1, currentSizeIndex - 1);
    if (fallbackIndex >= 0 && fallbackIndex < SIZE_HIERARCHY.length) {
      const fallbackSize = SIZE_HIERARCHY[fallbackIndex];
      const fallbackType = `${targetFamily}.${fallbackSize}`;
      if (catalog[fallbackType]) {
        return {
          target: fallbackType,
          reason: `${strategy} downgrade: ${currentSpec.size} → ${fallbackSize}`,
          warnings: ['Verify application resource requirements before applying'],
          confidence: 'high',
        };
      }
    }
    return null;
  }

  // Add warnings based on the change
  const targetSpec = catalog[targetType];
  if (targetSpec) {
    if (currentSpec.memory_gb / targetSpec.memory_gb > 2) {
      warnings.push('Significant memory reduction - verify application memory requirements');
    }
    if (currentSpec.vcpu / targetSpec.vcpu > 2) {
      warnings.push('Significant CPU reduction - verify application CPU requirements');
    }
  }

  if (strategy === 'aggressive') {
    warnings.push('Aggressive downgrade - recommended for non-production environments only');
    confidence = 'low';
  } else if (strategy === 'moderate') {
    warnings.push('Verify application resource requirements before applying');
    confidence = 'medium';
  } else {
    warnings.push('Verify application resource requirements before applying');
  }

  return {
    target: targetType,
    reason: `${strategy} downgrade: ${currentSpec.size} → ${targetSize}${targetFamily !== currentSpec.family ? ` (${targetFamily})` : ''}`,
    warnings,
    confidence,
  };
}
