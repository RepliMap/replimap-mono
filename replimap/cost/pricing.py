"""
AWS pricing data and lookup functions.

Contains default pricing for common AWS resources.
Prices are approximate and based on us-east-1 region.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from replimap.cost.models import CostCategory, PricingTier


@dataclass
class PricingInfo:
    """Pricing information for a resource type."""

    hourly_rate: float = 0.0  # Per hour cost
    monthly_rate: float = 0.0  # Fixed monthly cost
    per_gb_rate: float = 0.0  # Per GB cost
    per_request_rate: float = 0.0  # Per request cost
    category: CostCategory = CostCategory.OTHER
    notes: str = ""


# EC2 Instance pricing (on-demand, us-east-1)
EC2_INSTANCE_PRICING: dict[str, float] = {
    # General Purpose - T3
    "t3.nano": 0.0052,
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "t3.2xlarge": 0.3328,
    # General Purpose - T3a (AMD)
    "t3a.nano": 0.0047,
    "t3a.micro": 0.0094,
    "t3a.small": 0.0188,
    "t3a.medium": 0.0376,
    "t3a.large": 0.0752,
    "t3a.xlarge": 0.1504,
    "t3a.2xlarge": 0.3008,
    # General Purpose - M5
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "m5.8xlarge": 1.536,
    "m5.12xlarge": 2.304,
    "m5.16xlarge": 3.072,
    "m5.24xlarge": 4.608,
    # General Purpose - M6i
    "m6i.large": 0.096,
    "m6i.xlarge": 0.192,
    "m6i.2xlarge": 0.384,
    "m6i.4xlarge": 0.768,
    "m6i.8xlarge": 1.536,
    "m6i.12xlarge": 2.304,
    "m6i.16xlarge": 3.072,
    "m6i.24xlarge": 4.608,
    # Compute Optimized - C5
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
    "c5.4xlarge": 0.68,
    "c5.9xlarge": 1.53,
    "c5.12xlarge": 2.04,
    "c5.18xlarge": 3.06,
    "c5.24xlarge": 4.08,
    # Memory Optimized - R5
    "r5.large": 0.126,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
    "r5.4xlarge": 1.008,
    "r5.8xlarge": 2.016,
    "r5.12xlarge": 3.024,
    "r5.16xlarge": 4.032,
    "r5.24xlarge": 6.048,
    # Storage Optimized - I3
    "i3.large": 0.156,
    "i3.xlarge": 0.312,
    "i3.2xlarge": 0.624,
    "i3.4xlarge": 1.248,
    "i3.8xlarge": 2.496,
    "i3.16xlarge": 4.992,
    # GPU - P3
    "p3.2xlarge": 3.06,
    "p3.8xlarge": 12.24,
    "p3.16xlarge": 24.48,
    # GPU - G4dn
    "g4dn.xlarge": 0.526,
    "g4dn.2xlarge": 0.752,
    "g4dn.4xlarge": 1.204,
    "g4dn.8xlarge": 2.176,
    "g4dn.12xlarge": 3.912,
    "g4dn.16xlarge": 4.352,
}

# RDS Instance pricing (on-demand, us-east-1, single-AZ)
RDS_INSTANCE_PRICING: dict[str, float] = {
    # db.t3
    "db.t3.micro": 0.017,
    "db.t3.small": 0.034,
    "db.t3.medium": 0.068,
    "db.t3.large": 0.136,
    "db.t3.xlarge": 0.272,
    "db.t3.2xlarge": 0.544,
    # db.m5
    "db.m5.large": 0.171,
    "db.m5.xlarge": 0.342,
    "db.m5.2xlarge": 0.684,
    "db.m5.4xlarge": 1.368,
    "db.m5.8xlarge": 2.736,
    "db.m5.12xlarge": 4.104,
    "db.m5.16xlarge": 5.472,
    "db.m5.24xlarge": 8.208,
    # db.r5
    "db.r5.large": 0.24,
    "db.r5.xlarge": 0.48,
    "db.r5.2xlarge": 0.96,
    "db.r5.4xlarge": 1.92,
    "db.r5.8xlarge": 3.84,
    "db.r5.12xlarge": 5.76,
    "db.r5.16xlarge": 7.68,
    "db.r5.24xlarge": 11.52,
    # db.r6g (Graviton)
    "db.r6g.large": 0.216,
    "db.r6g.xlarge": 0.432,
    "db.r6g.2xlarge": 0.864,
    "db.r6g.4xlarge": 1.728,
    "db.r6g.8xlarge": 3.456,
    "db.r6g.12xlarge": 5.184,
    "db.r6g.16xlarge": 6.912,
}

# ElastiCache Node pricing (on-demand, us-east-1)
ELASTICACHE_PRICING: dict[str, float] = {
    # cache.t3
    "cache.t3.micro": 0.017,
    "cache.t3.small": 0.034,
    "cache.t3.medium": 0.068,
    # cache.m5
    "cache.m5.large": 0.156,
    "cache.m5.xlarge": 0.312,
    "cache.m5.2xlarge": 0.624,
    "cache.m5.4xlarge": 1.248,
    "cache.m5.12xlarge": 3.744,
    "cache.m5.24xlarge": 7.488,
    # cache.r5
    "cache.r5.large": 0.226,
    "cache.r5.xlarge": 0.452,
    "cache.r5.2xlarge": 0.904,
    "cache.r5.4xlarge": 1.808,
    "cache.r5.12xlarge": 5.424,
    "cache.r5.24xlarge": 10.848,
}

# EBS Volume pricing (per GB-month, us-east-1)
EBS_VOLUME_PRICING: dict[str, float] = {
    "gp2": 0.10,
    "gp3": 0.08,
    "io1": 0.125,
    "io2": 0.125,
    "st1": 0.045,
    "sc1": 0.015,
    "standard": 0.05,
}

# Storage pricing (per GB-month)
STORAGE_PRICING: dict[str, float] = {
    "s3_standard": 0.023,
    "s3_ia": 0.0125,
    "s3_glacier": 0.004,
    "s3_glacier_deep": 0.00099,
    "efs_standard": 0.30,
    "efs_ia": 0.025,
}

# Network pricing
NETWORK_PRICING: dict[str, float] = {
    "nat_gateway_hourly": 0.045,
    "nat_gateway_per_gb": 0.045,
    "vpc_endpoint_hourly": 0.01,
    "vpc_endpoint_per_gb": 0.01,
    "data_transfer_out_per_gb": 0.09,  # First 10TB
}

# Load Balancer pricing (hourly)
LOAD_BALANCER_PRICING: dict[str, float] = {
    "alb": 0.0225,
    "nlb": 0.0225,
    "clb": 0.025,
    "gateway_lb": 0.0125,
}

# Lambda pricing
LAMBDA_PRICING: dict[str, float] = {
    "per_request": 0.0000002,  # $0.20 per 1M requests
    "per_gb_second": 0.0000166667,  # $0.0000166667 per GB-second
}

# DocumentDB pricing (same instance classes as RDS, slightly higher)
DOCUMENTDB_PRICING: dict[str, float] = {
    # db.t3
    "db.t3.medium": 0.078,
    # db.r5
    "db.r5.large": 0.277,
    "db.r5.xlarge": 0.554,
    "db.r5.2xlarge": 1.108,
    "db.r5.4xlarge": 2.216,
    "db.r5.8xlarge": 4.432,
    "db.r5.12xlarge": 6.648,
    "db.r5.16xlarge": 8.864,
    "db.r5.24xlarge": 13.296,
    # db.r6g (Graviton)
    "db.r6g.large": 0.2495,
    "db.r6g.xlarge": 0.499,
    "db.r6g.2xlarge": 0.998,
    "db.r6g.4xlarge": 1.996,
    "db.r6g.8xlarge": 3.992,
    "db.r6g.12xlarge": 5.988,
    "db.r6g.16xlarge": 7.984,
}

# CloudWatch pricing
CLOUDWATCH_PRICING: dict[str, float] = {
    "metric_per_month": 0.30,  # Per custom metric per month
    "alarm_standard": 0.10,  # Per standard alarm per month
    "alarm_high_resolution": 0.30,  # Per high-resolution alarm
    "dashboard_per_month": 3.00,  # Per dashboard per month
    "logs_ingestion_per_gb": 0.50,  # Per GB ingested
    "logs_storage_per_gb": 0.03,  # Per GB stored per month
    "logs_insights_per_gb": 0.005,  # Per GB scanned
    "metrics_api_per_1k": 0.01,  # GetMetricData, per 1K metrics
}

# SQS pricing
SQS_PRICING: dict[str, float] = {
    "standard_per_million": 0.40,  # Standard queue, per 1M requests
    "fifo_per_million": 0.50,  # FIFO queue, per 1M requests
}

# SNS pricing
SNS_PRICING: dict[str, float] = {
    "publish_per_million": 0.50,  # Per 1M publishes
    "http_per_million": 0.60,  # HTTP/S notifications per 1M
    "email_per_1k": 2.00,  # Email notifications per 1K
    "sms_per_message": 0.00645,  # SMS (US), varies by country
}

# Route 53 pricing
ROUTE53_PRICING: dict[str, float] = {
    "hosted_zone_per_month": 0.50,  # Per hosted zone per month
    "queries_per_million": 0.40,  # Standard queries per 1M
    "queries_latency_per_million": 0.60,  # Latency-based routing
    "queries_geo_per_million": 0.70,  # Geo DNS queries
    "health_check_basic": 0.50,  # Basic health check per month
    "health_check_https": 0.75,  # HTTPS health check
    "health_check_string_match": 1.00,  # String matching
}

# KMS pricing
KMS_PRICING: dict[str, float] = {
    "key_per_month": 1.00,  # Customer managed key per month
    "requests_per_10k": 0.03,  # API requests per 10K
}

# Secrets Manager pricing
SECRETS_MANAGER_PRICING: dict[str, float] = {
    "secret_per_month": 0.40,  # Per secret per month
    "api_calls_per_10k": 0.05,  # API calls per 10K
}

# ECR pricing
ECR_PRICING: dict[str, float] = {
    "storage_per_gb": 0.10,  # Per GB per month
    "data_transfer_per_gb": 0.09,  # Data transfer out per GB
}

# CloudFront pricing (simplified, varies by region)
CLOUDFRONT_PRICING: dict[str, float] = {
    "data_transfer_per_gb": 0.085,  # First 10TB
    "requests_http_per_10k": 0.0075,  # HTTP requests per 10K
    "requests_https_per_10k": 0.01,  # HTTPS requests per 10K
}

# GuardDuty pricing (per million events analyzed)
GUARDDUTY_PRICING: dict[str, float] = {
    "cloudtrail_per_million": 4.00,  # CloudTrail events
    "vpc_flow_per_gb": 1.00,  # VPC Flow Logs per GB
    "dns_per_million": 1.00,  # DNS queries per million
}

# CloudTrail pricing
CLOUDTRAIL_PRICING: dict[str, float] = {
    "management_events_per_100k": 2.00,  # Management events per 100K
    "data_events_per_100k": 0.10,  # Data events per 100K
}

# Step Functions pricing
STEP_FUNCTIONS_PRICING: dict[str, float] = {
    "standard_per_transition": 0.000025,  # Per state transition
    "express_per_million": 1.00,  # Express workflows per 1M requests
    "express_per_gb_seconds": 0.00001667,  # Duration charge
}

# ECS/Fargate pricing
FARGATE_PRICING: dict[str, float] = {
    "vcpu_per_hour": 0.04048,  # Per vCPU per hour
    "memory_per_gb_hour": 0.004445,  # Per GB per hour
}

# Resource type to category mapping
RESOURCE_CATEGORY_MAP: dict[str, CostCategory] = {
    # Compute
    "aws_instance": CostCategory.COMPUTE,
    "aws_launch_template": CostCategory.COMPUTE,
    "aws_autoscaling_group": CostCategory.COMPUTE,
    "aws_lambda_function": CostCategory.COMPUTE,
    "aws_ecs_service": CostCategory.COMPUTE,
    "aws_ecs_cluster": CostCategory.COMPUTE,
    "aws_ecs_task_definition": CostCategory.COMPUTE,
    "aws_eks_cluster": CostCategory.COMPUTE,
    "aws_eks_node_group": CostCategory.COMPUTE,
    # Database
    "aws_db_instance": CostCategory.DATABASE,
    "aws_rds_cluster": CostCategory.DATABASE,
    "aws_rds_cluster_instance": CostCategory.DATABASE,
    "aws_elasticache_cluster": CostCategory.DATABASE,
    "aws_elasticache_replication_group": CostCategory.DATABASE,
    "aws_dynamodb_table": CostCategory.DATABASE,
    "aws_docdb_cluster": CostCategory.DATABASE,
    "aws_docdb_cluster_instance": CostCategory.DATABASE,
    "aws_redshift_cluster": CostCategory.DATABASE,
    # Storage
    "aws_s3_bucket": CostCategory.STORAGE,
    "aws_ebs_volume": CostCategory.STORAGE,
    "aws_efs_file_system": CostCategory.STORAGE,
    "aws_fsx_lustre_file_system": CostCategory.STORAGE,
    "aws_backup_vault": CostCategory.STORAGE,
    "aws_ecr_repository": CostCategory.STORAGE,
    # Network
    "aws_vpc": CostCategory.NETWORK,
    "aws_subnet": CostCategory.NETWORK,
    "aws_nat_gateway": CostCategory.NETWORK,
    "aws_internet_gateway": CostCategory.NETWORK,
    "aws_lb": CostCategory.NETWORK,
    "aws_alb": CostCategory.NETWORK,
    "aws_elb": CostCategory.NETWORK,
    "aws_vpc_endpoint": CostCategory.NETWORK,
    "aws_eip": CostCategory.NETWORK,
    "aws_route53_zone": CostCategory.NETWORK,
    "aws_cloudfront_distribution": CostCategory.NETWORK,
    "aws_api_gateway_rest_api": CostCategory.NETWORK,
    # Security
    "aws_security_group": CostCategory.SECURITY,
    "aws_iam_role": CostCategory.SECURITY,
    "aws_iam_policy": CostCategory.SECURITY,
    "aws_kms_key": CostCategory.SECURITY,
    "aws_kms_alias": CostCategory.SECURITY,
    "aws_waf_web_acl": CostCategory.SECURITY,
    "aws_acm_certificate": CostCategory.SECURITY,
    "aws_secretsmanager_secret": CostCategory.SECURITY,
    "aws_guardduty_detector": CostCategory.SECURITY,
    # Monitoring
    "aws_cloudwatch_log_group": CostCategory.MONITORING,
    "aws_cloudwatch_metric_alarm": CostCategory.MONITORING,
    "aws_cloudwatch_dashboard": CostCategory.MONITORING,
    "aws_cloudwatch_metric_stream": CostCategory.MONITORING,
    "aws_sns_topic": CostCategory.MONITORING,
    "aws_sqs_queue": CostCategory.MONITORING,
    "aws_cloudtrail": CostCategory.MONITORING,
    "aws_cloudtrail_trail": CostCategory.MONITORING,
    # Integration
    "aws_sfn_state_machine": CostCategory.COMPUTE,
    "aws_stepfunction_state_machine": CostCategory.COMPUTE,
}

# Regional price multipliers (relative to us-east-1)
REGION_MULTIPLIERS: dict[str, float] = {
    "us-east-1": 1.0,
    "us-east-2": 1.0,
    "us-west-1": 1.1,
    "us-west-2": 1.0,
    "eu-west-1": 1.1,
    "eu-west-2": 1.15,
    "eu-west-3": 1.15,
    "eu-central-1": 1.15,
    "eu-north-1": 1.1,
    "ap-northeast-1": 1.25,
    "ap-northeast-2": 1.2,
    "ap-northeast-3": 1.25,
    "ap-southeast-1": 1.15,
    "ap-southeast-2": 1.2,
    "ap-south-1": 1.1,
    "sa-east-1": 1.5,
    "ca-central-1": 1.05,
    "me-south-1": 1.2,
    "af-south-1": 1.3,
}

# Reserved instance discount multipliers
RESERVED_MULTIPLIERS: dict[PricingTier, float] = {
    PricingTier.ON_DEMAND: 1.0,
    PricingTier.RESERVED_1Y: 0.60,  # ~40% savings
    PricingTier.RESERVED_3Y: 0.40,  # ~60% savings
    PricingTier.SPOT: 0.30,  # ~70% savings (variable)
    PricingTier.SAVINGS_PLAN: 0.65,  # ~35% savings
}


class PricingLookup:
    """Lookup pricing for AWS resources."""

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region
        self.region_multiplier = REGION_MULTIPLIERS.get(region, 1.0)

    def get_ec2_hourly_cost(
        self,
        instance_type: str,
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> float:
        """Get hourly cost for EC2 instance."""
        base_rate = EC2_INSTANCE_PRICING.get(instance_type, 0.0)

        # If unknown, estimate based on size
        if base_rate == 0.0:
            base_rate = self._estimate_ec2_rate(instance_type)

        return self._apply_multipliers(base_rate, pricing_tier)

    def get_rds_hourly_cost(
        self,
        instance_class: str,
        multi_az: bool = False,
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> float:
        """Get hourly cost for RDS instance."""
        base_rate = RDS_INSTANCE_PRICING.get(instance_class, 0.0)

        # If unknown, estimate based on size
        if base_rate == 0.0:
            base_rate = self._estimate_rds_rate(instance_class)

        # Multi-AZ doubles the cost
        if multi_az:
            base_rate *= 2

        return self._apply_multipliers(base_rate, pricing_tier)

    def get_rds_storage_monthly_cost(
        self,
        storage_gb: int,
        storage_type: str = "gp2",
        iops: int = 0,
    ) -> float:
        """Get monthly storage cost for RDS."""
        rate = EBS_VOLUME_PRICING.get(storage_type, 0.10)
        storage_cost = storage_gb * rate * self.region_multiplier

        # Additional IOPS cost for io1/io2
        if storage_type in ("io1", "io2") and iops > 0:
            storage_cost += iops * 0.065  # $0.065 per IOPS-month

        return storage_cost

    def get_elasticache_hourly_cost(
        self,
        node_type: str,
        num_nodes: int = 1,
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> float:
        """Get hourly cost for ElastiCache cluster."""
        base_rate = ELASTICACHE_PRICING.get(node_type, 0.0)

        if base_rate == 0.0:
            base_rate = self._estimate_cache_rate(node_type)

        return self._apply_multipliers(base_rate * num_nodes, pricing_tier)

    def get_ebs_monthly_cost(
        self,
        volume_size_gb: int,
        volume_type: str = "gp2",
        iops: int = 0,
        throughput: int = 0,
    ) -> float:
        """Get monthly cost for EBS volume."""
        rate = EBS_VOLUME_PRICING.get(volume_type, 0.10)
        cost = volume_size_gb * rate * self.region_multiplier

        # gp3 additional costs
        if volume_type == "gp3":
            # Free tier: 3000 IOPS, 125 MB/s
            if iops > 3000:
                cost += (iops - 3000) * 0.005  # $0.005 per IOPS
            if throughput > 125:
                cost += (throughput - 125) * 0.04  # $0.04 per MB/s

        # io1/io2 IOPS cost
        if volume_type in ("io1", "io2") and iops > 0:
            cost += iops * 0.065

        return cost

    def get_s3_monthly_cost(
        self,
        storage_gb: float,
        storage_class: str = "STANDARD",
    ) -> float:
        """Get monthly cost for S3 storage."""
        rate_key = f"s3_{storage_class.lower()}"
        rate = STORAGE_PRICING.get(rate_key, STORAGE_PRICING["s3_standard"])
        return storage_gb * rate * self.region_multiplier

    def get_nat_gateway_monthly_cost(
        self,
        data_processed_gb: float = 100.0,
    ) -> float:
        """Get monthly cost for NAT Gateway."""
        # Hourly cost (730 hours/month)
        hourly_cost = NETWORK_PRICING["nat_gateway_hourly"] * 730

        # Data processing cost
        data_cost = data_processed_gb * NETWORK_PRICING["nat_gateway_per_gb"]

        return (hourly_cost + data_cost) * self.region_multiplier

    def get_load_balancer_monthly_cost(
        self,
        lb_type: str = "alb",
        lcu_hours: float = 730,
    ) -> float:
        """Get monthly cost for load balancer."""
        hourly_rate = LOAD_BALANCER_PRICING.get(lb_type, 0.0225)

        # Base hourly cost
        base_cost = hourly_rate * 730

        # LCU cost (simplified - $0.008 per LCU-hour)
        lcu_cost = lcu_hours * 0.008

        return (base_cost + lcu_cost) * self.region_multiplier

    def get_lambda_monthly_cost(
        self,
        invocations: int = 1000000,
        avg_duration_ms: int = 100,
        memory_mb: int = 128,
    ) -> float:
        """Get monthly cost for Lambda function."""
        # Request cost
        request_cost = invocations * LAMBDA_PRICING["per_request"]

        # Compute cost
        gb_seconds = (invocations * avg_duration_ms / 1000) * (memory_mb / 1024)
        compute_cost = gb_seconds * LAMBDA_PRICING["per_gb_second"]

        return request_cost + compute_cost

    def get_vpc_endpoint_monthly_cost(
        self,
        data_processed_gb: float = 10.0,
    ) -> float:
        """Get monthly cost for VPC endpoint."""
        hourly_cost = NETWORK_PRICING["vpc_endpoint_hourly"] * 730
        data_cost = data_processed_gb * NETWORK_PRICING["vpc_endpoint_per_gb"]
        return (hourly_cost + data_cost) * self.region_multiplier

    def get_documentdb_hourly_cost(
        self,
        instance_class: str,
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> float:
        """Get hourly cost for DocumentDB instance."""
        base_rate = DOCUMENTDB_PRICING.get(instance_class, 0.0)
        if base_rate == 0.0:
            # Fall back to RDS-like estimation with 15% premium
            base_rate = self._estimate_rds_rate(instance_class) * 1.15
        return self._apply_multipliers(base_rate, pricing_tier)

    def get_sqs_monthly_cost(
        self,
        requests_per_month: int = 1000000,
        is_fifo: bool = False,
    ) -> float:
        """Get monthly cost for SQS queue."""
        rate_key = "fifo_per_million" if is_fifo else "standard_per_million"
        rate = SQS_PRICING[rate_key]
        # First 1M requests free
        billable = max(0, requests_per_month - 1000000)
        return (billable / 1000000) * rate * self.region_multiplier

    def get_sns_monthly_cost(
        self,
        publishes_per_month: int = 1000000,
        notifications_per_month: int = 1000000,
    ) -> float:
        """Get monthly cost for SNS topic."""
        # First 1M publishes free
        billable_publishes = max(0, publishes_per_month - 1000000)
        publish_cost = (billable_publishes / 1000000) * SNS_PRICING[
            "publish_per_million"
        ]
        # HTTP notifications
        notify_cost = (notifications_per_month / 1000000) * SNS_PRICING[
            "http_per_million"
        ]
        return (publish_cost + notify_cost) * self.region_multiplier

    def get_route53_monthly_cost(
        self,
        hosted_zones: int = 1,
        queries_per_month: int = 1000000,
        health_checks: int = 0,
    ) -> float:
        """Get monthly cost for Route 53."""
        # Hosted zones (first 25 at $0.50, then $0.10)
        zone_cost = min(hosted_zones, 25) * ROUTE53_PRICING["hosted_zone_per_month"]
        if hosted_zones > 25:
            zone_cost += (hosted_zones - 25) * 0.10
        # Queries (first 1B at $0.40/M)
        query_cost = (queries_per_month / 1000000) * ROUTE53_PRICING[
            "queries_per_million"
        ]
        # Health checks
        health_cost = health_checks * ROUTE53_PRICING["health_check_basic"]
        return zone_cost + query_cost + health_cost

    def get_kms_monthly_cost(
        self,
        customer_keys: int = 1,
        requests_per_month: int = 10000,
    ) -> float:
        """Get monthly cost for KMS."""
        key_cost = customer_keys * KMS_PRICING["key_per_month"]
        # First 20K requests free
        billable_requests = max(0, requests_per_month - 20000)
        request_cost = (billable_requests / 10000) * KMS_PRICING["requests_per_10k"]
        return (key_cost + request_cost) * self.region_multiplier

    def get_secrets_manager_monthly_cost(
        self,
        secrets_count: int = 1,
        api_calls_per_month: int = 10000,
    ) -> float:
        """Get monthly cost for Secrets Manager."""
        secret_cost = secrets_count * SECRETS_MANAGER_PRICING["secret_per_month"]
        request_cost = (api_calls_per_month / 10000) * SECRETS_MANAGER_PRICING[
            "api_calls_per_10k"
        ]
        return (secret_cost + request_cost) * self.region_multiplier

    def get_ecr_monthly_cost(
        self,
        storage_gb: float = 1.0,
    ) -> float:
        """Get monthly cost for ECR repository."""
        return storage_gb * ECR_PRICING["storage_per_gb"] * self.region_multiplier

    def get_cloudfront_monthly_cost(
        self,
        data_transfer_gb: float = 100.0,
        requests_per_month: int = 1000000,
    ) -> float:
        """Get monthly cost for CloudFront distribution."""
        transfer_cost = data_transfer_gb * CLOUDFRONT_PRICING["data_transfer_per_gb"]
        request_cost = (requests_per_month / 10000) * CLOUDFRONT_PRICING[
            "requests_https_per_10k"
        ]
        return (transfer_cost + request_cost) * self.region_multiplier

    def get_guardduty_monthly_cost(
        self,
        cloudtrail_events_per_month: int = 1000000,
        vpc_flow_gb: float = 10.0,
    ) -> float:
        """Get monthly cost for GuardDuty."""
        # CloudTrail analysis
        ct_cost = (cloudtrail_events_per_month / 1000000) * GUARDDUTY_PRICING[
            "cloudtrail_per_million"
        ]
        # VPC Flow Logs analysis
        flow_cost = vpc_flow_gb * GUARDDUTY_PRICING["vpc_flow_per_gb"]
        return (ct_cost + flow_cost) * self.region_multiplier

    def get_cloudwatch_monthly_cost(
        self,
        custom_metrics: int = 0,
        alarms: int = 0,
        dashboards: int = 0,
        logs_ingestion_gb: float = 0.0,
        logs_storage_gb: float = 0.0,
    ) -> float:
        """Get monthly cost for CloudWatch."""
        # First 10 custom metrics free
        billable_metrics = max(0, custom_metrics - 10)
        metrics_cost = billable_metrics * CLOUDWATCH_PRICING["metric_per_month"]
        # First 10 alarms free
        billable_alarms = max(0, alarms - 10)
        alarms_cost = billable_alarms * CLOUDWATCH_PRICING["alarm_standard"]
        # First 3 dashboards free
        billable_dashboards = max(0, dashboards - 3)
        dashboard_cost = billable_dashboards * CLOUDWATCH_PRICING["dashboard_per_month"]
        # Logs (first 5GB ingestion free)
        billable_ingestion = max(0, logs_ingestion_gb - 5)
        logs_cost = billable_ingestion * CLOUDWATCH_PRICING["logs_ingestion_per_gb"]
        storage_cost = logs_storage_gb * CLOUDWATCH_PRICING["logs_storage_per_gb"]
        return (
            metrics_cost + alarms_cost + dashboard_cost + logs_cost + storage_cost
        ) * self.region_multiplier

    def get_cloudtrail_monthly_cost(
        self,
        management_events_per_month: int = 100000,
        data_events_per_month: int = 0,
    ) -> float:
        """Get monthly cost for CloudTrail."""
        # First trail's management events free
        mgmt_cost = (management_events_per_month / 100000) * CLOUDTRAIL_PRICING[
            "management_events_per_100k"
        ]
        data_cost = (data_events_per_month / 100000) * CLOUDTRAIL_PRICING[
            "data_events_per_100k"
        ]
        return (mgmt_cost + data_cost) * self.region_multiplier

    def get_resource_category(self, resource_type: str) -> CostCategory:
        """Get category for a resource type."""
        return RESOURCE_CATEGORY_MAP.get(resource_type, CostCategory.OTHER)

    def _apply_multipliers(
        self,
        base_rate: float,
        pricing_tier: PricingTier,
    ) -> float:
        """Apply region and pricing tier multipliers."""
        return (
            base_rate
            * self.region_multiplier
            * RESERVED_MULTIPLIERS.get(pricing_tier, 1.0)
        )

    def _estimate_ec2_rate(self, instance_type: str) -> float:
        """Estimate EC2 rate for unknown instance types."""
        # Parse size from instance type (e.g., t3.large -> large)
        parts = instance_type.split(".")
        if len(parts) < 2:
            return 0.05  # Default estimate

        size = parts[1]
        size_multipliers = {
            "nano": 0.5,
            "micro": 1.0,
            "small": 2.0,
            "medium": 4.0,
            "large": 8.0,
            "xlarge": 16.0,
            "2xlarge": 32.0,
            "4xlarge": 64.0,
            "8xlarge": 128.0,
            "12xlarge": 192.0,
            "16xlarge": 256.0,
            "24xlarge": 384.0,
        }

        base = 0.01  # $0.01 base
        multiplier = size_multipliers.get(size, 8.0)
        return base * multiplier

    def _estimate_rds_rate(self, instance_class: str) -> float:
        """Estimate RDS rate for unknown instance classes."""
        # Remove 'db.' prefix and parse
        clean = instance_class.replace("db.", "")
        parts = clean.split(".")
        if len(parts) < 2:
            return 0.10  # Default estimate

        size = parts[1]
        size_multipliers = {
            "micro": 1.0,
            "small": 2.0,
            "medium": 4.0,
            "large": 10.0,
            "xlarge": 20.0,
            "2xlarge": 40.0,
            "4xlarge": 80.0,
            "8xlarge": 160.0,
            "12xlarge": 240.0,
            "16xlarge": 320.0,
            "24xlarge": 480.0,
        }

        base = 0.017  # $0.017 base (t3.micro)
        multiplier = size_multipliers.get(size, 10.0)
        return base * multiplier

    def _estimate_cache_rate(self, node_type: str) -> float:
        """Estimate ElastiCache rate for unknown node types."""
        # Remove 'cache.' prefix and parse
        clean = node_type.replace("cache.", "")
        parts = clean.split(".")
        if len(parts) < 2:
            return 0.05  # Default estimate

        size = parts[1]
        size_multipliers = {
            "micro": 1.0,
            "small": 2.0,
            "medium": 4.0,
            "large": 9.0,
            "xlarge": 18.0,
            "2xlarge": 36.0,
            "4xlarge": 72.0,
            "12xlarge": 216.0,
            "24xlarge": 432.0,
        }

        base = 0.017  # $0.017 base
        multiplier = size_multipliers.get(size, 9.0)
        return base * multiplier


def get_pricing_info(
    resource_type: str, config: dict[str, Any] | None = None
) -> PricingInfo:
    """Get pricing info for a resource type."""
    config = config or {}

    category = RESOURCE_CATEGORY_MAP.get(resource_type, CostCategory.OTHER)

    if resource_type == "aws_instance":
        instance_type = config.get("instance_type", "t3.medium")
        hourly = EC2_INSTANCE_PRICING.get(instance_type, 0.05)
        return PricingInfo(hourly_rate=hourly, category=category)

    if resource_type == "aws_db_instance":
        instance_class = config.get("instance_class", "db.t3.medium")
        hourly = RDS_INSTANCE_PRICING.get(instance_class, 0.10)
        return PricingInfo(hourly_rate=hourly, category=category)

    if resource_type == "aws_elasticache_cluster":
        node_type = config.get("node_type", "cache.t3.medium")
        hourly = ELASTICACHE_PRICING.get(node_type, 0.068)
        return PricingInfo(hourly_rate=hourly, category=category)

    if resource_type == "aws_nat_gateway":
        return PricingInfo(
            hourly_rate=NETWORK_PRICING["nat_gateway_hourly"],
            per_gb_rate=NETWORK_PRICING["nat_gateway_per_gb"],
            category=category,
        )

    if resource_type in ("aws_lb", "aws_alb"):
        return PricingInfo(
            hourly_rate=LOAD_BALANCER_PRICING["alb"],
            category=category,
        )

    if resource_type == "aws_elb":
        return PricingInfo(
            hourly_rate=LOAD_BALANCER_PRICING["clb"],
            category=category,
        )

    if resource_type == "aws_s3_bucket":
        return PricingInfo(
            per_gb_rate=STORAGE_PRICING["s3_standard"],
            category=category,
            notes="Cost depends on storage usage",
        )

    if resource_type == "aws_ebs_volume":
        volume_type = config.get("volume_type", "gp2")
        return PricingInfo(
            per_gb_rate=EBS_VOLUME_PRICING.get(volume_type, 0.10),
            category=category,
        )

    if resource_type == "aws_lambda_function":
        return PricingInfo(
            per_request_rate=LAMBDA_PRICING["per_request"],
            category=category,
            notes="Cost depends on invocations and duration",
        )

    if resource_type == "aws_vpc_endpoint":
        return PricingInfo(
            hourly_rate=NETWORK_PRICING["vpc_endpoint_hourly"],
            per_gb_rate=NETWORK_PRICING["vpc_endpoint_per_gb"],
            category=category,
        )

    # Free resources
    if resource_type in (
        "aws_vpc",
        "aws_subnet",
        "aws_internet_gateway",
        "aws_route_table",
        "aws_route",
        "aws_security_group",
        "aws_iam_role",
        "aws_iam_policy",
    ):
        return PricingInfo(category=category, notes="No direct cost")

    return PricingInfo(category=category, notes="Pricing not available")
