"""
@replimap/config - Auto-generated configuration
DO NOT EDIT - This file is generated from src/*.json

Content Hash: 7abec13bd128
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal, Optional


# ============================================================================
# Version
# ============================================================================

CONFIG_VERSION: str = "7abec13bd128"


# ============================================================================
# Plans
# ============================================================================

PlanName = Literal["free", "pro", "team", "sovereign"]

PLAN_NAMES: tuple[PlanName, ...] = ("free", "pro", "team", "sovereign",)


@dataclass(frozen=True)
class PlanConfig:
    """Configuration for a pricing plan."""
    price_monthly: int
    scans_per_month: Optional[int]
    max_accounts: Optional[int]
    features: list[str]
    addons: Optional[dict[str, int]] = None


PLANS: dict[PlanName, PlanConfig] = {
    "free": PlanConfig(
        price_monthly=0,
        scans_per_month=10,
        max_accounts=None,
        features=["basic_scan","graph_preview"],
        addons=None,
    ),
    "pro": PlanConfig(
        price_monthly=2900,
        scans_per_month=None,
        max_accounts=None,
        features=["basic_scan","graph_preview","terraform_download","full_audit"],
        addons=None,
    ),
    "team": PlanConfig(
        price_monthly=9900,
        scans_per_month=None,
        max_accounts=10,
        features=["*"],
        addons=None,
    ),
    "sovereign": PlanConfig(
        price_monthly=250000,
        scans_per_month=None,
        max_accounts=None,
        features=["*"],
        addons={"apra_cps234": 50000, "essential_eight": 30000, "rbnz_bs11": 40000, "dora": 50000},
    ),
}


# ============================================================================
# Compliance Frameworks
# ============================================================================

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


# ============================================================================
# AWS Resources
# ============================================================================

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


# ============================================================================
# Helper Functions
# ============================================================================

def is_plan_name(value: str) -> bool:
    """Check if a string is a valid plan name."""
    return value in PLAN_NAMES


def is_framework_id(value: str) -> bool:
    """Check if a string is a valid framework ID."""
    return value in FRAMEWORK_IDS


def is_aws_resource_type(value: str) -> bool:
    """Check if a string is a valid AWS resource type."""
    return value in ALL_AWS_RESOURCES


def get_plan_features(plan: PlanName) -> list[str]:
    """Get the list of features for a plan."""
    config = PLANS[plan]
    if "*" in config.features:
        return ["basic_scan", "graph_preview", "terraform_download", "full_audit"]
    return list(config.features)
