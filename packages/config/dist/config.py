"""
@replimap/config v4.0 - Auto-generated configuration
DO NOT EDIT - This file is generated from src/*.json

Philosophy: "Gate Output, Not Input"
- Unlimited scans for all tiers
- Charge when users export/download

Content Hash: fd3749d4c50e
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


# =============================================================================
# Version
# =============================================================================

CONFIG_VERSION: str = "fd3749d4c50e"


# =============================================================================
# Plan Types
# =============================================================================

PlanName = Literal["community", "pro", "team", "sovereign"]
LegacyPlanName = Literal["free", "solo", "enterprise"]

PLAN_NAMES: tuple[PlanName, ...] = ("community", "pro", "team", "sovereign",)

LEGACY_PLAN_MIGRATIONS: dict[LegacyPlanName, PlanName] = {
    "free": "community",
    "solo": "pro",
    "enterprise": "sovereign",
}


@dataclass(frozen=True)
class PlanUI:
    """UI configuration for a plan."""
    cta: str
    badge: Optional[str]
    highlight: bool


@dataclass(frozen=True)
class PlanAddOn:
    """Configuration for a plan add-on."""
    name: str
    description: str
    price_monthly: int  # cents


@dataclass(frozen=True)
class PlanConfig:
    """Configuration for a pricing plan."""
    name: str
    tagline: str
    description: str
    price_monthly: int  # cents
    price_yearly: int  # cents
    price_lifetime: Optional[int]  # cents, None if not available
    scans_per_month: Optional[int]  # None = unlimited
    resources_per_scan: Optional[int]  # None = unlimited
    aws_accounts: Optional[int]  # None = unlimited
    team_members: Optional[int]  # None = unlimited
    machines: Optional[int]  # None = unlimited
    history_retention_days: Optional[int]  # None = unlimited
    features: list[str]
    ui: PlanUI
    addons: Optional[dict[str, PlanAddOn]] = None


PLANS: dict[PlanName, PlanConfig] = {
    "community": PlanConfig(
        name="COMMUNITY",
        tagline="Full visibility, export when ready",
        description="See your entire AWS infrastructure. Upgrade when you\'re ready to take it home.",
        price_monthly=0,
        price_yearly=0,
        price_lifetime=None,
        scans_per_month=None,
        resources_per_scan=None,
        aws_accounts=1,
        team_members=1,
        machines=1,
        history_retention_days=7,
        features=["basic_scanning","dependency_graph","cost_analysis","compliance_view","security_score","export_json","snapshot","snapshot_diff"],
        ui=PlanUI(cta="Get Started Free", badge=None, highlight=False),
        addons=None,
    ),
    "pro": PlanConfig(
        name="PRO",
        tagline="Export your infrastructure as code",
        description="Take your Terraform code home. Perfect for individual DevOps engineers and SREs.",
        price_monthly=2900,
        price_yearly=29000,
        price_lifetime=19900,
        scans_per_month=None,
        resources_per_scan=None,
        aws_accounts=3,
        team_members=1,
        machines=2,
        history_retention_days=90,
        features=["basic_scanning","dependency_graph","cost_analysis","compliance_view","security_score","export_json","export_terraform","export_csv","export_html","export_markdown","graph_full","graph_security","graph_export_no_watermark","audit_full_findings","audit_fix","audit_report_export","snapshot","snapshot_diff","api_access"],
        ui=PlanUI(cta="Start PRO Trial", badge="Most Popular", highlight=True),
        addons=None,
    ),
    "team": PlanConfig(
        name="TEAM",
        tagline="Continuous compliance for your organization",
        description="Drift alerts, compliance reports, and CI/CD integration for growing teams.",
        price_monthly=9900,
        price_yearly=99000,
        price_lifetime=49900,
        scans_per_month=None,
        resources_per_scan=None,
        aws_accounts=10,
        team_members=5,
        machines=10,
        history_retention_days=365,
        features=["*","!compliance_reports_apra","!compliance_reports_dora","!compliance_reports_essential8","!custom_compliance_mapping","!sso","!dedicated_support","!air_gap_deployment","!report_signature","!tamper_evident_audit_trail","!white_labeling"],
        ui=PlanUI(cta="Start TEAM Trial", badge=None, highlight=False),
        addons=None,
    ),
    "sovereign": PlanConfig(
        name="SOVEREIGN",
        tagline="Data sovereignty for regulated industries",
        description="When your regulator asks \'Where does the data go?\', the answer is: Nowhere.",
        price_monthly=250000,
        price_yearly=2500000,
        price_lifetime=None,
        scans_per_month=None,
        resources_per_scan=None,
        aws_accounts=None,
        team_members=None,
        machines=None,
        history_retention_days=None,
        features=["*"],
        ui=PlanUI(cta="Request Demo", badge="Sovereign Grade", highlight=False),
        addons={"apra_cps234": PlanAddOn(name="APRA CPS 234 Module", description="Australian Prudential Regulation Authority compliance mapping", price_monthly=50000), "dora": PlanAddOn(name="DORA Compliance Module", description="Digital Operational Resilience Act (EU) compliance mapping", price_monthly=50000), "essential_eight": PlanAddOn(name="Essential Eight Module", description="Australian Cyber Security Centre maturity assessment", price_monthly=30000), "rbnz_bs11": PlanAddOn(name="RBNZ BS11 Module", description="Reserve Bank of New Zealand outsourcing requirements", price_monthly=30000), "dedicated_am": PlanAddOn(name="Dedicated Account Manager", description="Named contact for your organization", price_monthly=50000), "sla_999": PlanAddOn(name="99.9% SLA Guarantee", description="Uptime guarantee with financial penalties", price_monthly=20000)},
    ),
}


# =============================================================================
# Features
# =============================================================================

ALL_FEATURES: tuple[str, ...] = (
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
    "snapshot_diff",
)

FeatureName = Literal["api_access", "audit_fix", "audit_full_findings", "audit_report_export", "basic_scanning", "compliance_view", "cost_analysis", "dependency_graph", "export_csv", "export_html", "export_json", "export_markdown", "export_terraform", "graph_export_no_watermark", "graph_full", "graph_security", "security_score", "snapshot", "snapshot_diff"]


# =============================================================================
# Compliance Frameworks
# =============================================================================

FrameworkId = Literal["apra_cps234", "essential_eight", "rbnz_bs11", "dora", "soc2", "iso27001"]

FRAMEWORK_IDS: tuple[FrameworkId, ...] = ("apra_cps234", "essential_eight", "rbnz_bs11", "dora", "soc2", "iso27001",)


@dataclass(frozen=True)
class FrameworkConfig:
    """Configuration for a compliance framework."""
    name: str
    region: str
    description: str
    controls_count: int


COMPLIANCE_FRAMEWORKS: dict[FrameworkId, FrameworkConfig] = {
    "apra_cps234": FrameworkConfig(
        name="APRA CPS 234",
        region="AU",
        description="Information Security standard for APRA-regulated entities",
        controls_count=36,
    ),
    "essential_eight": FrameworkConfig(
        name="Essential Eight",
        region="AU",
        description="Australian Cyber Security Centre mitigation strategies",
        controls_count=8,
    ),
    "rbnz_bs11": FrameworkConfig(
        name="RBNZ BS11",
        region="NZ",
        description="Reserve Bank of New Zealand outsourcing policy",
        controls_count=24,
    ),
    "dora": FrameworkConfig(
        name="DORA",
        region="EU",
        description="Digital Operational Resilience Act",
        controls_count=64,
    ),
    "soc2": FrameworkConfig(
        name="SOC 2",
        region="GLOBAL",
        description="Service Organization Control 2",
        controls_count=117,
    ),
    "iso27001": FrameworkConfig(
        name="ISO 27001",
        region="GLOBAL",
        description="Information Security Management System",
        controls_count=114,
    ),
}


# =============================================================================
# AWS Resources
# =============================================================================

ResourceCategory = Literal["compute", "storage", "database", "networking", "security", "messaging", "monitoring"]

RESOURCE_CATEGORIES: tuple[ResourceCategory, ...] = ("compute", "storage", "database", "networking", "security", "messaging", "monitoring",)

AWS_RESOURCES: dict[ResourceCategory, list[str]] = {
    "compute": ["aws_instance","aws_lambda_function","aws_ecs_cluster","aws_ecs_service","aws_ecs_task_definition","aws_eks_cluster","aws_autoscaling_group"],
    "storage": ["aws_s3_bucket","aws_ebs_volume","aws_efs_file_system","aws_fsx_lustre_file_system"],
    "database": ["aws_db_instance","aws_rds_cluster","aws_dynamodb_table","aws_elasticache_cluster","aws_redshift_cluster"],
    "networking": ["aws_vpc","aws_subnet","aws_security_group","aws_network_acl","aws_route_table","aws_internet_gateway","aws_nat_gateway","aws_lb","aws_lb_target_group","aws_cloudfront_distribution","aws_route53_zone"],
    "security": ["aws_iam_role","aws_iam_policy","aws_iam_user","aws_iam_group","aws_kms_key","aws_secretsmanager_secret","aws_acm_certificate"],
    "messaging": ["aws_sqs_queue","aws_sns_topic","aws_kinesis_stream","aws_eventbridge_rule"],
    "monitoring": ["aws_cloudwatch_log_group","aws_cloudwatch_metric_alarm","aws_cloudtrail"],
}

ALL_AWS_RESOURCES: tuple[str, ...] = (
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
    "aws_cloudtrail",
)

AwsResourceType = Literal["aws_instance", "aws_lambda_function", "aws_ecs_cluster", "aws_ecs_service", "aws_ecs_task_definition", "aws_eks_cluster", "aws_autoscaling_group", "aws_s3_bucket", "aws_ebs_volume", "aws_efs_file_system", "aws_fsx_lustre_file_system", "aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table", "aws_elasticache_cluster", "aws_redshift_cluster", "aws_vpc", "aws_subnet", "aws_security_group", "aws_network_acl", "aws_route_table", "aws_internet_gateway", "aws_nat_gateway", "aws_lb", "aws_lb_target_group", "aws_cloudfront_distribution", "aws_route53_zone", "aws_iam_role", "aws_iam_policy", "aws_iam_user", "aws_iam_group", "aws_kms_key", "aws_secretsmanager_secret", "aws_acm_certificate", "aws_sqs_queue", "aws_sns_topic", "aws_kinesis_stream", "aws_eventbridge_rule", "aws_cloudwatch_log_group", "aws_cloudwatch_metric_alarm", "aws_cloudtrail"]


# =============================================================================
# Helper Functions
# =============================================================================

def is_plan_name(value: str) -> bool:
    """Check if a string is a valid plan name."""
    return value in PLAN_NAMES


def is_legacy_plan_name(value: str) -> bool:
    """Check if a string is a legacy plan name."""
    return value in LEGACY_PLAN_MIGRATIONS


def normalize_plan_name(value: str) -> PlanName:
    """Normalize a plan name, converting legacy names to v4.0 names."""
    if is_plan_name(value):
        return value  # type: ignore
    if is_legacy_plan_name(value):
        return LEGACY_PLAN_MIGRATIONS[value]  # type: ignore
    return "community"


def is_framework_id(value: str) -> bool:
    """Check if a string is a valid framework ID."""
    return value in FRAMEWORK_IDS


def is_aws_resource_type(value: str) -> bool:
    """Check if a string is a valid AWS resource type."""
    return value in ALL_AWS_RESOURCES


def plan_has_feature(plan: PlanName, feature: str) -> bool:
    """Check if a plan has a specific feature."""
    config = PLANS[plan]

    # Check for "*" (all features)
    if "*" in config.features:
        # Check if explicitly excluded
        return f"!{feature}" not in config.features

    return feature in config.features


def get_plan_features(plan: PlanName) -> list[str]:
    """Get all features for a plan (resolving * and ! modifiers)."""
    config = PLANS[plan]

    if "*" in config.features:
        # All features except excluded ones
        excluded = [f[1:] for f in config.features if f.startswith("!")]
        return [f for f in ALL_FEATURES if f not in excluded]

    return [f for f in config.features if not f.startswith("!")]


def is_unlimited(value: Optional[int]) -> bool:
    """Check if a limit is unlimited (None or -1)."""
    return value is None or value == -1


def format_limit(value: Optional[int]) -> str:
    """Format a limit for display."""
    if is_unlimited(value):
        return "Unlimited"
    return f"{value:,}"


def format_price(cents: int) -> str:
    """Format price in dollars from cents."""
    if cents == 0:
        return "Free"
    return f"${cents / 100:,.0f}"


def get_required_plan_for_feature(feature: str) -> PlanName:
    """Get the minimum plan required for a feature."""
    for plan_name in PLAN_NAMES:
        if plan_has_feature(plan_name, feature):
            return plan_name
    return "sovereign"


def get_upgrade_path(current_plan: PlanName) -> Optional[PlanName]:
    """Get upgrade path from current plan."""
    upgrade_paths: dict[PlanName, Optional[PlanName]] = {
        "community": "pro",
        "pro": "team",
        "team": "sovereign",
        "sovereign": None,
    }
    return upgrade_paths.get(current_plan)


# =============================================================================
# Plan Comparison
# =============================================================================

PLAN_RANK: dict[str, int] = {
    # v4.0 plans
    "community": 0,
    "pro": 1,
    "team": 2,
    "sovereign": 3,
    # Legacy plans
    "free": 0,
    "solo": 1,
    "enterprise": 3,
}


def is_plan_upgrade(from_plan: str, to_plan: str) -> bool:
    """Check if changing plans is an upgrade."""
    from_rank = PLAN_RANK.get(normalize_plan_name(from_plan), 0)
    to_rank = PLAN_RANK.get(normalize_plan_name(to_plan), 0)
    return to_rank > from_rank


def is_plan_downgrade(from_plan: str, to_plan: str) -> bool:
    """Check if changing plans is a downgrade."""
    from_rank = PLAN_RANK.get(normalize_plan_name(from_plan), 0)
    to_rank = PLAN_RANK.get(normalize_plan_name(to_plan), 0)
    return to_rank < from_rank
