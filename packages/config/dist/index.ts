/**
 * @replimap/config v4.0 - Auto-generated configuration
 * DO NOT EDIT - This file is generated from src/*.json
 *
 * Philosophy: "Gate Output, Not Input"
 * - Unlimited scans for all tiers
 * - Charge when users export/download
 *
 * Content Hash: fd3749d4c50e
 */

// =============================================================================
// Version
// =============================================================================

export const CONFIG_VERSION = "fd3749d4c50e" as const;

// =============================================================================
// Plan Types
// =============================================================================

export const PLAN_NAMES = ["community", "pro", "team", "sovereign"] as const;
export type PlanName = typeof PLAN_NAMES[number];

/** Legacy plan names that map to v4.0 plans */
export const LEGACY_PLAN_MIGRATIONS: Record<string, PlanName> = {
  free: "community",
  solo: "pro",
  enterprise: "sovereign",
} as const;

export type LegacyPlanName = "free" | "solo" | "enterprise";

export interface PlanUI {
  cta: string;
  badge: string | null;
  highlight: boolean;
}

export interface PlanAddOn {
  name: string;
  description: string;
  /** Price in cents per month */
  price_monthly: number;
}

export interface PlanConfig {
  name: string;
  tagline: string;
  description: string;
  /** Price in cents per month */
  price_monthly: number;
  /** Price in cents per year */
  price_yearly: number;
  /** Price in cents for lifetime (null if not available) */
  price_lifetime: number | null;
  /** Scans per month (null = unlimited) */
  scans_per_month: number | null;
  /** Resources per scan (null = unlimited) */
  resources_per_scan: number | null;
  /** Maximum AWS accounts (null = unlimited) */
  aws_accounts: number | null;
  /** Maximum team members (null = unlimited) */
  team_members: number | null;
  /** Maximum machines (null = unlimited) */
  machines: number | null;
  /** History retention in days (null = unlimited) */
  history_retention_days: number | null;
  /** Feature flags - "*" means all features, "!feature" means excluded */
  features: string[];
  ui: PlanUI;
  addons?: Record<string, PlanAddOn>;
}

export const PLANS: Record<PlanName, PlanConfig> = {
  "community": {
    "name": "COMMUNITY",
    "tagline": "Full visibility, export when ready",
    "description": "See your entire AWS infrastructure. Upgrade when you're ready to take it home.",
    "price_monthly": 0,
    "price_yearly": 0,
    "price_lifetime": null,
    "scans_per_month": null,
    "resources_per_scan": null,
    "aws_accounts": 1,
    "team_members": 1,
    "machines": 1,
    "history_retention_days": 7,
    "features": [
      "basic_scanning",
      "dependency_graph",
      "cost_analysis",
      "compliance_view",
      "security_score",
      "export_json",
      "snapshot",
      "snapshot_diff"
    ],
    "ui": {
      "cta": "Get Started Free",
      "badge": null,
      "highlight": false
    }
  },
  "pro": {
    "name": "PRO",
    "tagline": "Export your infrastructure as code",
    "description": "Take your Terraform code home. Perfect for individual DevOps engineers and SREs.",
    "price_monthly": 2900,
    "price_yearly": 29000,
    "price_lifetime": 19900,
    "scans_per_month": null,
    "resources_per_scan": null,
    "aws_accounts": 3,
    "team_members": 1,
    "machines": 2,
    "history_retention_days": 90,
    "features": [
      "basic_scanning",
      "dependency_graph",
      "cost_analysis",
      "compliance_view",
      "security_score",
      "export_json",
      "export_terraform",
      "export_csv",
      "export_html",
      "export_markdown",
      "graph_full",
      "graph_security",
      "graph_export_no_watermark",
      "audit_full_findings",
      "audit_fix",
      "audit_report_export",
      "snapshot",
      "snapshot_diff",
      "api_access"
    ],
    "ui": {
      "cta": "Start PRO Trial",
      "badge": "Most Popular",
      "highlight": true
    }
  },
  "team": {
    "name": "TEAM",
    "tagline": "Continuous compliance for your organization",
    "description": "Drift alerts, compliance reports, and CI/CD integration for growing teams.",
    "price_monthly": 9900,
    "price_yearly": 99000,
    "price_lifetime": 49900,
    "scans_per_month": null,
    "resources_per_scan": null,
    "aws_accounts": 10,
    "team_members": 5,
    "machines": 10,
    "history_retention_days": 365,
    "features": [
      "*",
      "!compliance_reports_apra",
      "!compliance_reports_dora",
      "!compliance_reports_essential8",
      "!custom_compliance_mapping",
      "!sso",
      "!dedicated_support",
      "!air_gap_deployment",
      "!report_signature",
      "!tamper_evident_audit_trail",
      "!white_labeling"
    ],
    "ui": {
      "cta": "Start TEAM Trial",
      "badge": null,
      "highlight": false
    }
  },
  "sovereign": {
    "name": "SOVEREIGN",
    "tagline": "Data sovereignty for regulated industries",
    "description": "When your regulator asks 'Where does the data go?', the answer is: Nowhere.",
    "price_monthly": 250000,
    "price_yearly": 2500000,
    "price_lifetime": null,
    "scans_per_month": null,
    "resources_per_scan": null,
    "aws_accounts": null,
    "team_members": null,
    "machines": null,
    "history_retention_days": null,
    "features": [
      "*"
    ],
    "addons": {
      "apra_cps234": {
        "name": "APRA CPS 234 Module",
        "description": "Australian Prudential Regulation Authority compliance mapping",
        "price_monthly": 50000
      },
      "dora": {
        "name": "DORA Compliance Module",
        "description": "Digital Operational Resilience Act (EU) compliance mapping",
        "price_monthly": 50000
      },
      "essential_eight": {
        "name": "Essential Eight Module",
        "description": "Australian Cyber Security Centre maturity assessment",
        "price_monthly": 30000
      },
      "rbnz_bs11": {
        "name": "RBNZ BS11 Module",
        "description": "Reserve Bank of New Zealand outsourcing requirements",
        "price_monthly": 30000
      },
      "dedicated_am": {
        "name": "Dedicated Account Manager",
        "description": "Named contact for your organization",
        "price_monthly": 50000
      },
      "sla_999": {
        "name": "99.9% SLA Guarantee",
        "description": "Uptime guarantee with financial penalties",
        "price_monthly": 20000
      }
    },
    "ui": {
      "cta": "Request Demo",
      "badge": "Sovereign Grade",
      "highlight": false
    }
  }
} as const;

// =============================================================================
// Features
// =============================================================================

export const ALL_FEATURES = [
  "api_access",
  "audit_fix",
  "audit_full_findings",
  "audit_report_export",
  "basic_scanning",
  "compliance_view",
  "cost_analysis",
  "dependency_graph",
  "export_csv",
  "export_html",
  "export_json",
  "export_markdown",
  "export_terraform",
  "graph_export_no_watermark",
  "graph_full",
  "graph_security",
  "security_score",
  "snapshot",
  "snapshot_diff"
] as const;

export type FeatureName = typeof ALL_FEATURES[number];

// =============================================================================
// Compliance Frameworks
// =============================================================================

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

// =============================================================================
// AWS Resources
// =============================================================================

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

// =============================================================================
// Helper Functions
// =============================================================================

export function isPlanName(value: string): value is PlanName {
  return PLAN_NAMES.includes(value as PlanName);
}

export function isLegacyPlanName(value: string): value is LegacyPlanName {
  return value in LEGACY_PLAN_MIGRATIONS;
}

/**
 * Normalize a plan name, converting legacy names to v4.0 names
 */
export function normalizePlanName(value: string): PlanName {
  if (isPlanName(value)) return value;
  if (isLegacyPlanName(value)) return LEGACY_PLAN_MIGRATIONS[value];
  return "community"; // Default to community for unknown plans
}

export function isFrameworkId(value: string): value is FrameworkId {
  return FRAMEWORK_IDS.includes(value as FrameworkId);
}

export function isAwsResourceType(value: string): value is AwsResourceType {
  return ALL_AWS_RESOURCES.includes(value as AwsResourceType);
}

/**
 * Check if a plan has a specific feature
 */
export function planHasFeature(plan: PlanName, feature: string): boolean {
  const config = PLANS[plan];

  // Check for "*" (all features)
  if (config.features.includes("*")) {
    // Check if explicitly excluded
    return !config.features.includes(`!${feature}`);
  }

  return config.features.includes(feature);
}

/**
 * Get all features for a plan (resolving "*" and "!" modifiers)
 */
export function getPlanFeatures(plan: PlanName): string[] {
  const config = PLANS[plan];

  if (config.features.includes("*")) {
    // All features except excluded ones
    const excluded = config.features
      .filter(f => f.startsWith("!"))
      .map(f => f.slice(1));
    return ALL_FEATURES.filter(f => !excluded.includes(f));
  }

  return config.features.filter(f => !f.startsWith("!"));
}

/**
 * Check if a limit is unlimited (null or -1)
 */
export function isUnlimited(value: number | null): boolean {
  return value === null || value === -1;
}

/**
 * Format a limit for display
 */
export function formatLimit(value: number | null): string {
  if (isUnlimited(value)) return "Unlimited";
  return value!.toLocaleString();
}

/**
 * Format price in dollars from cents
 */
export function formatPrice(cents: number): string {
  if (cents === 0) return "Free";
  return `$${(cents / 100).toLocaleString()}`;
}

/**
 * Get the minimum plan required for a feature
 */
export function getRequiredPlanForFeature(feature: string): PlanName {
  for (const planName of PLAN_NAMES) {
    if (planHasFeature(planName, feature)) {
      return planName;
    }
  }
  return "sovereign"; // Default to highest tier
}

/**
 * Get upgrade path from current plan
 */
export function getUpgradePath(currentPlan: PlanName): PlanName | null {
  const upgradePaths: Record<PlanName, PlanName | null> = {
    community: "pro",
    pro: "team",
    team: "sovereign",
    sovereign: null,
  };
  return upgradePaths[currentPlan];
}

// =============================================================================
// Plan Comparison
// =============================================================================

export const PLAN_RANK: Record<PlanName | LegacyPlanName, number> = {
  // v4.0 plans
  community: 0,
  pro: 1,
  team: 2,
  sovereign: 3,
  // Legacy plans (mapped to their v4.0 equivalents)
  free: 0,
  solo: 1,
  enterprise: 3,
};

export function isPlanUpgrade(from: string, to: string): boolean {
  const fromRank = PLAN_RANK[normalizePlanName(from)] ?? 0;
  const toRank = PLAN_RANK[normalizePlanName(to)] ?? 0;
  return toRank > fromRank;
}

export function isPlanDowngrade(from: string, to: string): boolean {
  const fromRank = PLAN_RANK[normalizePlanName(from)] ?? 0;
  const toRank = PLAN_RANK[normalizePlanName(to)] ?? 0;
  return toRank < fromRank;
}
