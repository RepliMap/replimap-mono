/**
 * Right-Sizer Pricing & Rules Database
 *
 * CRITICAL: All instances must have 'architecture' field for safety.
 * NEVER suggest changing architecture (x86 ↔ ARM) for EC2 instances.
 *
 * Last Updated: 2024-01
 * Prices: On-demand, us-east-1 baseline (hourly rates)
 */

// =============================================================================
// TYPES
// =============================================================================

export interface InstanceSpec {
  type: string;
  vcpu: number;
  memory_gb: number;
  hourly_usd: number;
  family: string;
  generation: number;
  size: string;
  is_burstable: boolean;
  architecture: 'x86_64' | 'arm64';
}

export type ResourceCategory = 'ec2' | 'rds' | 'elasticache';
export type DowngradeStrategy = 'conservative' | 'aggressive';

// =============================================================================
// SKIP REASONS (for observability)
// =============================================================================

export enum SkipReason {
  UNKNOWN_INSTANCE_TYPE = 'Unknown instance type',
  ALREADY_MINIMUM_SIZE = 'Already at minimum size',
  ALREADY_BURSTABLE = 'Already using cost-effective burstable instance',
  NO_SAVINGS_POSSIBLE = 'No cost savings possible',
  UNSUPPORTED_RESOURCE_TYPE = 'Unsupported resource type',
}

// =============================================================================
// REGIONAL MULTIPLIERS
// =============================================================================

export const REGIONAL_MULTIPLIERS: Record<string, number> = {
  'us-east-1': 1.0,
  'us-east-2': 1.0,
  'us-west-1': 1.08,
  'us-west-2': 1.0,
  'eu-west-1': 1.10,
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
  'default': 1.15,
};

// =============================================================================
// SIZE HIERARCHY
// =============================================================================

export const SIZE_HIERARCHY = [
  'nano', 'micro', 'small', 'medium', 'large', 'xlarge', '2xlarge', '4xlarge', '8xlarge', '9xlarge', '12xlarge', '16xlarge', '24xlarge'
];

// =============================================================================
// EC2 INSTANCES
// =============================================================================

export const EC2_INSTANCES: Record<string, InstanceSpec> = {
  // ─────────────────────────────────────────────────────────────────────────
  // x86_64 INSTANCES
  // ─────────────────────────────────────────────────────────────────────────

  // T3 Family (Burstable x86) - PREFERRED FOR DEV
  't3.nano':    { type: 't3.nano',    vcpu: 2,  memory_gb: 0.5,  hourly_usd: 0.0052, family: 't3', generation: 3, size: 'nano',    is_burstable: true,  architecture: 'x86_64' },
  't3.micro':   { type: 't3.micro',   vcpu: 2,  memory_gb: 1,    hourly_usd: 0.0104, family: 't3', generation: 3, size: 'micro',   is_burstable: true,  architecture: 'x86_64' },
  't3.small':   { type: 't3.small',   vcpu: 2,  memory_gb: 2,    hourly_usd: 0.0208, family: 't3', generation: 3, size: 'small',   is_burstable: true,  architecture: 'x86_64' },
  't3.medium':  { type: 't3.medium',  vcpu: 2,  memory_gb: 4,    hourly_usd: 0.0416, family: 't3', generation: 3, size: 'medium',  is_burstable: true,  architecture: 'x86_64' },
  't3.large':   { type: 't3.large',   vcpu: 2,  memory_gb: 8,    hourly_usd: 0.0832, family: 't3', generation: 3, size: 'large',   is_burstable: true,  architecture: 'x86_64' },
  't3.xlarge':  { type: 't3.xlarge',  vcpu: 4,  memory_gb: 16,   hourly_usd: 0.1664, family: 't3', generation: 3, size: 'xlarge',  is_burstable: true,  architecture: 'x86_64' },
  't3.2xlarge': { type: 't3.2xlarge', vcpu: 8,  memory_gb: 32,   hourly_usd: 0.3328, family: 't3', generation: 3, size: '2xlarge', is_burstable: true,  architecture: 'x86_64' },

  // T3a Family (AMD x86 - cheaper alternative)
  't3a.nano':    { type: 't3a.nano',    vcpu: 2,  memory_gb: 0.5,  hourly_usd: 0.0047, family: 't3a', generation: 3, size: 'nano',    is_burstable: true,  architecture: 'x86_64' },
  't3a.micro':   { type: 't3a.micro',   vcpu: 2,  memory_gb: 1,    hourly_usd: 0.0094, family: 't3a', generation: 3, size: 'micro',   is_burstable: true,  architecture: 'x86_64' },
  't3a.small':   { type: 't3a.small',   vcpu: 2,  memory_gb: 2,    hourly_usd: 0.0188, family: 't3a', generation: 3, size: 'small',   is_burstable: true,  architecture: 'x86_64' },
  't3a.medium':  { type: 't3a.medium',  vcpu: 2,  memory_gb: 4,    hourly_usd: 0.0376, family: 't3a', generation: 3, size: 'medium',  is_burstable: true,  architecture: 'x86_64' },
  't3a.large':   { type: 't3a.large',   vcpu: 2,  memory_gb: 8,    hourly_usd: 0.0752, family: 't3a', generation: 3, size: 'large',   is_burstable: true,  architecture: 'x86_64' },
  't3a.xlarge':  { type: 't3a.xlarge',  vcpu: 4,  memory_gb: 16,   hourly_usd: 0.1504, family: 't3a', generation: 3, size: 'xlarge',  is_burstable: true,  architecture: 'x86_64' },
  't3a.2xlarge': { type: 't3a.2xlarge', vcpu: 8,  memory_gb: 32,   hourly_usd: 0.3008, family: 't3a', generation: 3, size: '2xlarge', is_burstable: true,  architecture: 'x86_64' },

  // M5 Family (General Purpose x86)
  'm5.large':    { type: 'm5.large',    vcpu: 2,  memory_gb: 8,    hourly_usd: 0.096,  family: 'm5', generation: 5, size: 'large',    is_burstable: false, architecture: 'x86_64' },
  'm5.xlarge':   { type: 'm5.xlarge',   vcpu: 4,  memory_gb: 16,   hourly_usd: 0.192,  family: 'm5', generation: 5, size: 'xlarge',   is_burstable: false, architecture: 'x86_64' },
  'm5.2xlarge':  { type: 'm5.2xlarge',  vcpu: 8,  memory_gb: 32,   hourly_usd: 0.384,  family: 'm5', generation: 5, size: '2xlarge',  is_burstable: false, architecture: 'x86_64' },
  'm5.4xlarge':  { type: 'm5.4xlarge',  vcpu: 16, memory_gb: 64,   hourly_usd: 0.768,  family: 'm5', generation: 5, size: '4xlarge',  is_burstable: false, architecture: 'x86_64' },
  'm5.8xlarge':  { type: 'm5.8xlarge',  vcpu: 32, memory_gb: 128,  hourly_usd: 1.536,  family: 'm5', generation: 5, size: '8xlarge',  is_burstable: false, architecture: 'x86_64' },
  'm5.12xlarge': { type: 'm5.12xlarge', vcpu: 48, memory_gb: 192,  hourly_usd: 2.304,  family: 'm5', generation: 5, size: '12xlarge', is_burstable: false, architecture: 'x86_64' },
  'm5.16xlarge': { type: 'm5.16xlarge', vcpu: 64, memory_gb: 256,  hourly_usd: 3.072,  family: 'm5', generation: 5, size: '16xlarge', is_burstable: false, architecture: 'x86_64' },

  // M6i Family (Latest Gen x86)
  'm6i.large':   { type: 'm6i.large',   vcpu: 2,  memory_gb: 8,    hourly_usd: 0.096,  family: 'm6i', generation: 6, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'm6i.xlarge':  { type: 'm6i.xlarge',  vcpu: 4,  memory_gb: 16,   hourly_usd: 0.192,  family: 'm6i', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'm6i.2xlarge': { type: 'm6i.2xlarge', vcpu: 8,  memory_gb: 32,   hourly_usd: 0.384,  family: 'm6i', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'm6i.4xlarge': { type: 'm6i.4xlarge', vcpu: 16, memory_gb: 64,   hourly_usd: 0.768,  family: 'm6i', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },
  'm6i.8xlarge': { type: 'm6i.8xlarge', vcpu: 32, memory_gb: 128,  hourly_usd: 1.536,  family: 'm6i', generation: 6, size: '8xlarge', is_burstable: false, architecture: 'x86_64' },

  // R5 Family (Memory Optimized x86)
  'r5.large':   { type: 'r5.large',   vcpu: 2,  memory_gb: 16,   hourly_usd: 0.126,  family: 'r5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'r5.xlarge':  { type: 'r5.xlarge',  vcpu: 4,  memory_gb: 32,   hourly_usd: 0.252,  family: 'r5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'r5.2xlarge': { type: 'r5.2xlarge', vcpu: 8,  memory_gb: 64,   hourly_usd: 0.504,  family: 'r5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'r5.4xlarge': { type: 'r5.4xlarge', vcpu: 16, memory_gb: 128,  hourly_usd: 1.008,  family: 'r5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },
  'r5.8xlarge': { type: 'r5.8xlarge', vcpu: 32, memory_gb: 256,  hourly_usd: 2.016,  family: 'r5', generation: 5, size: '8xlarge', is_burstable: false, architecture: 'x86_64' },

  // R6i Family (Latest Gen Memory x86)
  'r6i.large':   { type: 'r6i.large',   vcpu: 2,  memory_gb: 16,   hourly_usd: 0.126,  family: 'r6i', generation: 6, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'r6i.xlarge':  { type: 'r6i.xlarge',  vcpu: 4,  memory_gb: 32,   hourly_usd: 0.252,  family: 'r6i', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'r6i.2xlarge': { type: 'r6i.2xlarge', vcpu: 8,  memory_gb: 64,   hourly_usd: 0.504,  family: 'r6i', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'r6i.4xlarge': { type: 'r6i.4xlarge', vcpu: 16, memory_gb: 128,  hourly_usd: 1.008,  family: 'r6i', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // C5 Family (Compute Optimized x86)
  'c5.large':   { type: 'c5.large',   vcpu: 2,  memory_gb: 4,    hourly_usd: 0.085,  family: 'c5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'c5.xlarge':  { type: 'c5.xlarge',  vcpu: 4,  memory_gb: 8,    hourly_usd: 0.170,  family: 'c5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'c5.2xlarge': { type: 'c5.2xlarge', vcpu: 8,  memory_gb: 16,   hourly_usd: 0.340,  family: 'c5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'c5.4xlarge': { type: 'c5.4xlarge', vcpu: 16, memory_gb: 32,   hourly_usd: 0.680,  family: 'c5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },
  'c5.9xlarge': { type: 'c5.9xlarge', vcpu: 36, memory_gb: 72,   hourly_usd: 1.530,  family: 'c5', generation: 5, size: '9xlarge', is_burstable: false, architecture: 'x86_64' },

  // C6i Family (Latest Gen Compute x86)
  'c6i.large':   { type: 'c6i.large',   vcpu: 2,  memory_gb: 4,    hourly_usd: 0.085,  family: 'c6i', generation: 6, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'c6i.xlarge':  { type: 'c6i.xlarge',  vcpu: 4,  memory_gb: 8,    hourly_usd: 0.170,  family: 'c6i', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'c6i.2xlarge': { type: 'c6i.2xlarge', vcpu: 8,  memory_gb: 16,   hourly_usd: 0.340,  family: 'c6i', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'c6i.4xlarge': { type: 'c6i.4xlarge', vcpu: 16, memory_gb: 32,   hourly_usd: 0.680,  family: 'c6i', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // ─────────────────────────────────────────────────────────────────────────
  // ARM64 (GRAVITON) INSTANCES
  // ─────────────────────────────────────────────────────────────────────────

  // T4g Family (Burstable ARM) - CHEAPEST FOR ARM DEV
  't4g.nano':    { type: 't4g.nano',    vcpu: 2,  memory_gb: 0.5,  hourly_usd: 0.0042, family: 't4g', generation: 4, size: 'nano',    is_burstable: true,  architecture: 'arm64' },
  't4g.micro':   { type: 't4g.micro',   vcpu: 2,  memory_gb: 1,    hourly_usd: 0.0084, family: 't4g', generation: 4, size: 'micro',   is_burstable: true,  architecture: 'arm64' },
  't4g.small':   { type: 't4g.small',   vcpu: 2,  memory_gb: 2,    hourly_usd: 0.0168, family: 't4g', generation: 4, size: 'small',   is_burstable: true,  architecture: 'arm64' },
  't4g.medium':  { type: 't4g.medium',  vcpu: 2,  memory_gb: 4,    hourly_usd: 0.0336, family: 't4g', generation: 4, size: 'medium',  is_burstable: true,  architecture: 'arm64' },
  't4g.large':   { type: 't4g.large',   vcpu: 2,  memory_gb: 8,    hourly_usd: 0.0672, family: 't4g', generation: 4, size: 'large',   is_burstable: true,  architecture: 'arm64' },
  't4g.xlarge':  { type: 't4g.xlarge',  vcpu: 4,  memory_gb: 16,   hourly_usd: 0.1344, family: 't4g', generation: 4, size: 'xlarge',  is_burstable: true,  architecture: 'arm64' },
  't4g.2xlarge': { type: 't4g.2xlarge', vcpu: 8,  memory_gb: 32,   hourly_usd: 0.2688, family: 't4g', generation: 4, size: '2xlarge', is_burstable: true,  architecture: 'arm64' },

  // M6g Family (General Purpose ARM)
  'm6g.large':   { type: 'm6g.large',   vcpu: 2,  memory_gb: 8,    hourly_usd: 0.077,  family: 'm6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'm6g.xlarge':  { type: 'm6g.xlarge',  vcpu: 4,  memory_gb: 16,   hourly_usd: 0.154,  family: 'm6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'm6g.2xlarge': { type: 'm6g.2xlarge', vcpu: 8,  memory_gb: 32,   hourly_usd: 0.308,  family: 'm6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },
  'm6g.4xlarge': { type: 'm6g.4xlarge', vcpu: 16, memory_gb: 64,   hourly_usd: 0.616,  family: 'm6g', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'arm64' },

  // R6g Family (Memory Optimized ARM)
  'r6g.large':   { type: 'r6g.large',   vcpu: 2,  memory_gb: 16,   hourly_usd: 0.101,  family: 'r6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'r6g.xlarge':  { type: 'r6g.xlarge',  vcpu: 4,  memory_gb: 32,   hourly_usd: 0.202,  family: 'r6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'r6g.2xlarge': { type: 'r6g.2xlarge', vcpu: 8,  memory_gb: 64,   hourly_usd: 0.404,  family: 'r6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },

  // C6g Family (Compute Optimized ARM)
  'c6g.large':   { type: 'c6g.large',   vcpu: 2,  memory_gb: 4,    hourly_usd: 0.068,  family: 'c6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'c6g.xlarge':  { type: 'c6g.xlarge',  vcpu: 4,  memory_gb: 8,    hourly_usd: 0.136,  family: 'c6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'c6g.2xlarge': { type: 'c6g.2xlarge', vcpu: 8,  memory_gb: 16,   hourly_usd: 0.272,  family: 'c6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },
};

// =============================================================================
// RDS INSTANCES
// =============================================================================

export const RDS_INSTANCES: Record<string, InstanceSpec> = {
  // ─────────────────────────────────────────────────────────────────────────
  // x86_64 RDS
  // ─────────────────────────────────────────────────────────────────────────

  // db.t3 Family (Burstable)
  'db.t3.micro':   { type: 'db.t3.micro',   vcpu: 2,  memory_gb: 1,   hourly_usd: 0.017,  family: 'db.t3', generation: 3, size: 'micro',   is_burstable: true,  architecture: 'x86_64' },
  'db.t3.small':   { type: 'db.t3.small',   vcpu: 2,  memory_gb: 2,   hourly_usd: 0.034,  family: 'db.t3', generation: 3, size: 'small',   is_burstable: true,  architecture: 'x86_64' },
  'db.t3.medium':  { type: 'db.t3.medium',  vcpu: 2,  memory_gb: 4,   hourly_usd: 0.068,  family: 'db.t3', generation: 3, size: 'medium',  is_burstable: true,  architecture: 'x86_64' },
  'db.t3.large':   { type: 'db.t3.large',   vcpu: 2,  memory_gb: 8,   hourly_usd: 0.136,  family: 'db.t3', generation: 3, size: 'large',   is_burstable: true,  architecture: 'x86_64' },
  'db.t3.xlarge':  { type: 'db.t3.xlarge',  vcpu: 4,  memory_gb: 16,  hourly_usd: 0.272,  family: 'db.t3', generation: 3, size: 'xlarge',  is_burstable: true,  architecture: 'x86_64' },
  'db.t3.2xlarge': { type: 'db.t3.2xlarge', vcpu: 8,  memory_gb: 32,  hourly_usd: 0.544,  family: 'db.t3', generation: 3, size: '2xlarge', is_burstable: true,  architecture: 'x86_64' },

  // db.m5 Family (General Purpose)
  'db.m5.large':   { type: 'db.m5.large',   vcpu: 2,  memory_gb: 8,   hourly_usd: 0.171,  family: 'db.m5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'db.m5.xlarge':  { type: 'db.m5.xlarge',  vcpu: 4,  memory_gb: 16,  hourly_usd: 0.342,  family: 'db.m5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'db.m5.2xlarge': { type: 'db.m5.2xlarge', vcpu: 8,  memory_gb: 32,  hourly_usd: 0.684,  family: 'db.m5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.m5.4xlarge': { type: 'db.m5.4xlarge', vcpu: 16, memory_gb: 64,  hourly_usd: 1.368,  family: 'db.m5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.m5.8xlarge': { type: 'db.m5.8xlarge', vcpu: 32, memory_gb: 128, hourly_usd: 2.736,  family: 'db.m5', generation: 5, size: '8xlarge', is_burstable: false, architecture: 'x86_64' },

  // db.m6i Family (Latest Gen)
  'db.m6i.large':   { type: 'db.m6i.large',   vcpu: 2,  memory_gb: 8,   hourly_usd: 0.171,  family: 'db.m6i', generation: 6, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'db.m6i.xlarge':  { type: 'db.m6i.xlarge',  vcpu: 4,  memory_gb: 16,  hourly_usd: 0.342,  family: 'db.m6i', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'db.m6i.2xlarge': { type: 'db.m6i.2xlarge', vcpu: 8,  memory_gb: 32,  hourly_usd: 0.684,  family: 'db.m6i', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.m6i.4xlarge': { type: 'db.m6i.4xlarge', vcpu: 16, memory_gb: 64,  hourly_usd: 1.368,  family: 'db.m6i', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // db.r5 Family (Memory Optimized)
  'db.r5.large':   { type: 'db.r5.large',   vcpu: 2,  memory_gb: 16,  hourly_usd: 0.240,  family: 'db.r5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'db.r5.xlarge':  { type: 'db.r5.xlarge',  vcpu: 4,  memory_gb: 32,  hourly_usd: 0.480,  family: 'db.r5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'db.r5.2xlarge': { type: 'db.r5.2xlarge', vcpu: 8,  memory_gb: 64,  hourly_usd: 0.960,  family: 'db.r5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.r5.4xlarge': { type: 'db.r5.4xlarge', vcpu: 16, memory_gb: 128, hourly_usd: 1.920,  family: 'db.r5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.r5.8xlarge': { type: 'db.r5.8xlarge', vcpu: 32, memory_gb: 256, hourly_usd: 3.840,  family: 'db.r5', generation: 5, size: '8xlarge', is_burstable: false, architecture: 'x86_64' },

  // db.r6i Family (Latest Gen Memory)
  'db.r6i.large':   { type: 'db.r6i.large',   vcpu: 2,  memory_gb: 16,  hourly_usd: 0.240,  family: 'db.r6i', generation: 6, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'db.r6i.xlarge':  { type: 'db.r6i.xlarge',  vcpu: 4,  memory_gb: 32,  hourly_usd: 0.480,  family: 'db.r6i', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'db.r6i.2xlarge': { type: 'db.r6i.2xlarge', vcpu: 8,  memory_gb: 64,  hourly_usd: 0.960,  family: 'db.r6i', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'db.r6i.4xlarge': { type: 'db.r6i.4xlarge', vcpu: 16, memory_gb: 128, hourly_usd: 1.920,  family: 'db.r6i', generation: 6, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // ─────────────────────────────────────────────────────────────────────────
  // ARM64 (Graviton) RDS
  // ─────────────────────────────────────────────────────────────────────────

  // db.t4g Family (Burstable ARM)
  'db.t4g.micro':  { type: 'db.t4g.micro',  vcpu: 2,  memory_gb: 1,   hourly_usd: 0.016,  family: 'db.t4g', generation: 4, size: 'micro',  is_burstable: true,  architecture: 'arm64' },
  'db.t4g.small':  { type: 'db.t4g.small',  vcpu: 2,  memory_gb: 2,   hourly_usd: 0.032,  family: 'db.t4g', generation: 4, size: 'small',  is_burstable: true,  architecture: 'arm64' },
  'db.t4g.medium': { type: 'db.t4g.medium', vcpu: 2,  memory_gb: 4,   hourly_usd: 0.065,  family: 'db.t4g', generation: 4, size: 'medium', is_burstable: true,  architecture: 'arm64' },
  'db.t4g.large':  { type: 'db.t4g.large',  vcpu: 2,  memory_gb: 8,   hourly_usd: 0.129,  family: 'db.t4g', generation: 4, size: 'large',  is_burstable: true,  architecture: 'arm64' },
  'db.t4g.xlarge': { type: 'db.t4g.xlarge', vcpu: 4,  memory_gb: 16,  hourly_usd: 0.258,  family: 'db.t4g', generation: 4, size: 'xlarge', is_burstable: true,  architecture: 'arm64' },

  // db.m6g Family (General Purpose ARM)
  'db.m6g.large':   { type: 'db.m6g.large',   vcpu: 2,  memory_gb: 8,   hourly_usd: 0.154,  family: 'db.m6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'db.m6g.xlarge':  { type: 'db.m6g.xlarge',  vcpu: 4,  memory_gb: 16,  hourly_usd: 0.308,  family: 'db.m6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'db.m6g.2xlarge': { type: 'db.m6g.2xlarge', vcpu: 8,  memory_gb: 32,  hourly_usd: 0.616,  family: 'db.m6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },

  // db.r6g Family (Memory Optimized ARM)
  'db.r6g.large':   { type: 'db.r6g.large',   vcpu: 2,  memory_gb: 16,  hourly_usd: 0.216,  family: 'db.r6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'db.r6g.xlarge':  { type: 'db.r6g.xlarge',  vcpu: 4,  memory_gb: 32,  hourly_usd: 0.432,  family: 'db.r6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'db.r6g.2xlarge': { type: 'db.r6g.2xlarge', vcpu: 8,  memory_gb: 64,  hourly_usd: 0.864,  family: 'db.r6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },
};

// =============================================================================
// ELASTICACHE INSTANCES
// =============================================================================

export const ELASTICACHE_INSTANCES: Record<string, InstanceSpec> = {
  // ─────────────────────────────────────────────────────────────────────────
  // x86_64 ElastiCache
  // ─────────────────────────────────────────────────────────────────────────

  // cache.t3 Family (Burstable)
  'cache.t3.micro':   { type: 'cache.t3.micro',   vcpu: 2, memory_gb: 0.5,   hourly_usd: 0.017,  family: 'cache.t3', generation: 3, size: 'micro',   is_burstable: true,  architecture: 'x86_64' },
  'cache.t3.small':   { type: 'cache.t3.small',   vcpu: 2, memory_gb: 1.37,  hourly_usd: 0.034,  family: 'cache.t3', generation: 3, size: 'small',   is_burstable: true,  architecture: 'x86_64' },
  'cache.t3.medium':  { type: 'cache.t3.medium',  vcpu: 2, memory_gb: 3.09,  hourly_usd: 0.068,  family: 'cache.t3', generation: 3, size: 'medium',  is_burstable: true,  architecture: 'x86_64' },

  // cache.m5 Family (General Purpose)
  'cache.m5.large':   { type: 'cache.m5.large',   vcpu: 2, memory_gb: 6.38,  hourly_usd: 0.155,  family: 'cache.m5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'cache.m5.xlarge':  { type: 'cache.m5.xlarge',  vcpu: 4, memory_gb: 12.93, hourly_usd: 0.310,  family: 'cache.m5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'cache.m5.2xlarge': { type: 'cache.m5.2xlarge', vcpu: 8, memory_gb: 26.04, hourly_usd: 0.620,  family: 'cache.m5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'cache.m5.4xlarge': { type: 'cache.m5.4xlarge', vcpu: 16, memory_gb: 52.26, hourly_usd: 1.240, family: 'cache.m5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // cache.r5 Family (Memory Optimized)
  'cache.r5.large':   { type: 'cache.r5.large',   vcpu: 2, memory_gb: 13.07, hourly_usd: 0.218,  family: 'cache.r5', generation: 5, size: 'large',   is_burstable: false, architecture: 'x86_64' },
  'cache.r5.xlarge':  { type: 'cache.r5.xlarge',  vcpu: 4, memory_gb: 26.32, hourly_usd: 0.436,  family: 'cache.r5', generation: 5, size: 'xlarge',  is_burstable: false, architecture: 'x86_64' },
  'cache.r5.2xlarge': { type: 'cache.r5.2xlarge', vcpu: 8, memory_gb: 52.82, hourly_usd: 0.872,  family: 'cache.r5', generation: 5, size: '2xlarge', is_burstable: false, architecture: 'x86_64' },
  'cache.r5.4xlarge': { type: 'cache.r5.4xlarge', vcpu: 16, memory_gb: 105.81, hourly_usd: 1.744, family: 'cache.r5', generation: 5, size: '4xlarge', is_burstable: false, architecture: 'x86_64' },

  // ─────────────────────────────────────────────────────────────────────────
  // ARM64 (Graviton) ElastiCache
  // ─────────────────────────────────────────────────────────────────────────

  // cache.t4g Family (Burstable ARM)
  'cache.t4g.micro':  { type: 'cache.t4g.micro',  vcpu: 2, memory_gb: 0.5,   hourly_usd: 0.016,  family: 'cache.t4g', generation: 4, size: 'micro',  is_burstable: true,  architecture: 'arm64' },
  'cache.t4g.small':  { type: 'cache.t4g.small',  vcpu: 2, memory_gb: 1.37,  hourly_usd: 0.032,  family: 'cache.t4g', generation: 4, size: 'small',  is_burstable: true,  architecture: 'arm64' },
  'cache.t4g.medium': { type: 'cache.t4g.medium', vcpu: 2, memory_gb: 3.09,  hourly_usd: 0.065,  family: 'cache.t4g', generation: 4, size: 'medium', is_burstable: true,  architecture: 'arm64' },

  // cache.m6g Family (General Purpose ARM)
  'cache.m6g.large':   { type: 'cache.m6g.large',   vcpu: 2, memory_gb: 6.38,  hourly_usd: 0.139,  family: 'cache.m6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'cache.m6g.xlarge':  { type: 'cache.m6g.xlarge',  vcpu: 4, memory_gb: 12.93, hourly_usd: 0.278,  family: 'cache.m6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'cache.m6g.2xlarge': { type: 'cache.m6g.2xlarge', vcpu: 8, memory_gb: 26.04, hourly_usd: 0.556,  family: 'cache.m6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },

  // cache.r6g Family (Memory Optimized ARM)
  'cache.r6g.large':   { type: 'cache.r6g.large',   vcpu: 2, memory_gb: 13.07, hourly_usd: 0.196,  family: 'cache.r6g', generation: 6, size: 'large',   is_burstable: false, architecture: 'arm64' },
  'cache.r6g.xlarge':  { type: 'cache.r6g.xlarge',  vcpu: 4, memory_gb: 26.32, hourly_usd: 0.392,  family: 'cache.r6g', generation: 6, size: 'xlarge',  is_burstable: false, architecture: 'arm64' },
  'cache.r6g.2xlarge': { type: 'cache.r6g.2xlarge', vcpu: 8, memory_gb: 52.82, hourly_usd: 0.784,  family: 'cache.r6g', generation: 6, size: '2xlarge', is_burstable: false, architecture: 'arm64' },
};

// =============================================================================
// STORAGE PRICING (RDS)
// =============================================================================

export const STORAGE_PRICING = {
  rds: {
    'gp2': 0.115,      // $/GB/month
    'gp3': 0.08,       // $/GB/month (cheaper!)
    'io1': 0.125,      // $/GB/month
    'io2': 0.125,      // $/GB/month
    'standard': 0.10,  // $/GB/month (magnetic)
  },
  iops: {
    'io1': 0.10,       // $/IOPS/month
    'io2': 0.10,       // $/IOPS/month
    'gp3': 0.0,        // Included up to 3000 IOPS
  },
} as const;

// =============================================================================
// HELPER FUNCTIONS
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
 * Get regional price multiplier
 */
export function getRegionalMultiplier(region: string): number {
  return REGIONAL_MULTIPLIERS[region] ?? REGIONAL_MULTIPLIERS['default'];
}

/**
 * Calculate monthly instance cost (based on hourly rate)
 */
export function calculateMonthlyInstanceCost(hourlyUsd: number, region: string): number {
  const multiplier = getRegionalMultiplier(region);
  return Math.round(hourlyUsd * 730 * multiplier * 100) / 100;
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
  return calculateMonthlyInstanceCost(spec.hourly_usd, region);
}

/**
 * Calculate RDS storage monthly cost
 */
export function calculateStorageMonthlyCost(
  storageType: string,
  sizeGb: number,
  iops: number = 0
): number {
  const basePrice = STORAGE_PRICING.rds[storageType as keyof typeof STORAGE_PRICING.rds] || 0;
  const iopsPrice = STORAGE_PRICING.iops[storageType as keyof typeof STORAGE_PRICING.iops] || 0;

  let cost = basePrice * sizeGb;
  if ((storageType === 'io1' || storageType === 'io2') && iops > 0) {
    cost += iopsPrice * iops;
  }
  return Math.round(cost * 100) / 100;
}

/**
 * Get best dev recommendation for a resource type with architecture constraint
 * CRITICAL: For EC2, this preserves architecture (no x86 ↔ ARM switching)
 */
export function getDevRecommendation(
  resourceCategory: ResourceCategory,
  minMemoryGb: number,
  requiredArch: 'x86_64' | 'arm64'
): string | null {

  const instances = getInstanceCatalog(resourceCategory);

  // Determine preferred burstable family based on architecture
  const preferredFamily = requiredArch === 'arm64'
    ? (resourceCategory === 'ec2' ? 't4g' : resourceCategory === 'rds' ? 'db.t4g' : 'cache.t4g')
    : (resourceCategory === 'ec2' ? 't3' : resourceCategory === 'rds' ? 'db.t3' : 'cache.t3');

  // First, try preferred burstable family
  const preferredCandidates = Object.values(instances)
    .filter(i =>
      i.architecture === requiredArch &&
      i.family === preferredFamily &&
      i.memory_gb >= minMemoryGb
    )
    .sort((a, b) => a.hourly_usd - b.hourly_usd);

  if (preferredCandidates.length > 0) {
    return preferredCandidates[0].type;
  }

  // Fallback: Any burstable with matching architecture
  const burstableCandidates = Object.values(instances)
    .filter(i =>
      i.architecture === requiredArch &&
      i.is_burstable &&
      i.memory_gb >= minMemoryGb
    )
    .sort((a, b) => a.hourly_usd - b.hourly_usd);

  if (burstableCandidates.length > 0) {
    return burstableCandidates[0].type;
  }

  // Last resort: Any matching architecture
  const anyCandidates = Object.values(instances)
    .filter(i =>
      i.architecture === requiredArch &&
      i.memory_gb >= minMemoryGb
    )
    .sort((a, b) => a.hourly_usd - b.hourly_usd);

  return anyCandidates.length > 0 ? anyCandidates[0].type : null;
}
