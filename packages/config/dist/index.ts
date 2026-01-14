/**
 * @replimap/config - Auto-generated configuration
 * DO NOT EDIT - This file is generated from src/*.json
 *
 * Content Hash: 7abec13bd128
 * Generated: 2026-01-14T04:27:50.122Z
 */

// ============================================================================
// Version
// ============================================================================

export const CONFIG_VERSION = "7abec13bd128" as const;

// ============================================================================
// Plans
// ============================================================================

export const PLAN_NAMES = ["free", "pro", "team", "sovereign"] as const;
export type PlanName = typeof PLAN_NAMES[number];

export interface PlanConfig {
  price_monthly: number;
  scans_per_month: number | null;
  max_accounts?: number | null;
  features: string[];
  addons?: Record<string, number>;
}

export const PLANS: Record<PlanName, PlanConfig> = {
  "free": {
    "price_monthly": 0,
    "scans_per_month": 10,
    "features": [
      "basic_scan",
      "graph_preview"
    ]
  },
  "pro": {
    "price_monthly": 2900,
    "scans_per_month": null,
    "features": [
      "basic_scan",
      "graph_preview",
      "terraform_download",
      "full_audit"
    ]
  },
  "team": {
    "price_monthly": 9900,
    "scans_per_month": null,
    "max_accounts": 10,
    "features": [
      "*"
    ]
  },
  "sovereign": {
    "price_monthly": 250000,
    "scans_per_month": null,
    "max_accounts": null,
    "features": [
      "*"
    ],
    "addons": {
      "apra_cps234": 50000,
      "essential_eight": 30000,
      "rbnz_bs11": 40000,
      "dora": 50000
    }
  }
} as const;

// ============================================================================
// Compliance Frameworks
// ============================================================================

export const FRAMEWORK_IDS = ["apra_cps234", "essential_eight", "rbnz_bs11", "dora", "soc2", "iso27001"] as const;
export type FrameworkId = typeof FRAMEWORK_IDS[number];

export interface FrameworkConfig {
  name: string;
  region: string;
  description: string;
  controls_count: number;
}

export const COMPLIANCE_FRAMEWORKS: Record<FrameworkId, FrameworkConfig> = {
  "apra_cps234": {
    "name": "APRA CPS 234",
    "region": "AU",
    "description": "Information Security standard for APRA-regulated entities",
    "controls_count": 36
  },
  "essential_eight": {
    "name": "Essential Eight",
    "region": "AU",
    "description": "Australian Cyber Security Centre mitigation strategies",
    "controls_count": 8
  },
  "rbnz_bs11": {
    "name": "RBNZ BS11",
    "region": "NZ",
    "description": "Reserve Bank of New Zealand outsourcing policy",
    "controls_count": 24
  },
  "dora": {
    "name": "DORA",
    "region": "EU",
    "description": "Digital Operational Resilience Act",
    "controls_count": 64
  },
  "soc2": {
    "name": "SOC 2",
    "region": "GLOBAL",
    "description": "Service Organization Control 2",
    "controls_count": 117
  },
  "iso27001": {
    "name": "ISO 27001",
    "region": "GLOBAL",
    "description": "Information Security Management System",
    "controls_count": 114
  }
} as const;

// ============================================================================
// AWS Resources
// ============================================================================

export const RESOURCE_CATEGORIES = ["compute", "storage", "database", "networking", "security", "messaging", "monitoring"] as const;
export type ResourceCategory = typeof RESOURCE_CATEGORIES[number];

export const AWS_RESOURCES: Record<ResourceCategory, readonly string[]> = {
  "compute": [
    "aws_instance",
    "aws_lambda_function",
    "aws_ecs_cluster",
    "aws_ecs_service",
    "aws_ecs_task_definition",
    "aws_eks_cluster",
    "aws_autoscaling_group"
  ],
  "storage": [
    "aws_s3_bucket",
    "aws_ebs_volume",
    "aws_efs_file_system",
    "aws_fsx_lustre_file_system"
  ],
  "database": [
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_dynamodb_table",
    "aws_elasticache_cluster",
    "aws_redshift_cluster"
  ],
  "networking": [
    "aws_vpc",
    "aws_subnet",
    "aws_security_group",
    "aws_network_acl",
    "aws_route_table",
    "aws_internet_gateway",
    "aws_nat_gateway",
    "aws_lb",
    "aws_lb_target_group",
    "aws_cloudfront_distribution",
    "aws_route53_zone"
  ],
  "security": [
    "aws_iam_role",
    "aws_iam_policy",
    "aws_iam_user",
    "aws_iam_group",
    "aws_kms_key",
    "aws_secretsmanager_secret",
    "aws_acm_certificate"
  ],
  "messaging": [
    "aws_sqs_queue",
    "aws_sns_topic",
    "aws_kinesis_stream",
    "aws_eventbridge_rule"
  ],
  "monitoring": [
    "aws_cloudwatch_log_group",
    "aws_cloudwatch_metric_alarm",
    "aws_cloudtrail"
  ]
} as const;

export const ALL_AWS_RESOURCES = [
  "aws_instance",
  "aws_lambda_function",
  "aws_ecs_cluster",
  "aws_ecs_service",
  "aws_ecs_task_definition",
  "aws_eks_cluster",
  "aws_autoscaling_group",
  "aws_s3_bucket",
  "aws_ebs_volume",
  "aws_efs_file_system",
  "aws_fsx_lustre_file_system",
  "aws_db_instance",
  "aws_rds_cluster",
  "aws_dynamodb_table",
  "aws_elasticache_cluster",
  "aws_redshift_cluster",
  "aws_vpc",
  "aws_subnet",
  "aws_security_group",
  "aws_network_acl",
  "aws_route_table",
  "aws_internet_gateway",
  "aws_nat_gateway",
  "aws_lb",
  "aws_lb_target_group",
  "aws_cloudfront_distribution",
  "aws_route53_zone",
  "aws_iam_role",
  "aws_iam_policy",
  "aws_iam_user",
  "aws_iam_group",
  "aws_kms_key",
  "aws_secretsmanager_secret",
  "aws_acm_certificate",
  "aws_sqs_queue",
  "aws_sns_topic",
  "aws_kinesis_stream",
  "aws_eventbridge_rule",
  "aws_cloudwatch_log_group",
  "aws_cloudwatch_metric_alarm",
  "aws_cloudtrail"
] as const;

export type AwsResourceType = typeof ALL_AWS_RESOURCES[number];

// ============================================================================
// Helper Functions
// ============================================================================

export function isPlanName(value: string): value is PlanName {
  return PLAN_NAMES.includes(value as PlanName);
}

export function isFrameworkId(value: string): value is FrameworkId {
  return FRAMEWORK_IDS.includes(value as FrameworkId);
}

export function isAwsResourceType(value: string): value is AwsResourceType {
  return ALL_AWS_RESOURCES.includes(value as AwsResourceType);
}

export function getPlanFeatures(plan: PlanName): string[] {
  const config = PLANS[plan];
  if (config.features.includes("*")) {
    // Return all possible features
    return ["basic_scan", "graph_preview", "terraform_download", "full_audit"];
  }
  return config.features;
}
