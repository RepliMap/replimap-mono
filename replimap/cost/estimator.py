"""
Cost estimation engine.

Calculates monthly costs for AWS infrastructure based on
scanned resources and their configurations.
"""

from __future__ import annotations

import logging
from typing import Any

from replimap.core import GraphEngine
from replimap.cost.models import (
    CostBreakdown,
    CostCategory,
    CostConfidence,
    CostEstimate,
    OptimizationRecommendation,
    PricingTier,
    ResourceCost,
)
from replimap.cost.pricing import PricingLookup

logger = logging.getLogger(__name__)

# Hours per month (average)
HOURS_PER_MONTH = 730


class CostEstimator:
    """
    Estimate costs for AWS infrastructure.

    Uses resource configurations to calculate monthly costs
    and provide optimization recommendations.
    """

    def __init__(self, region: str = "us-east-1") -> None:
        self.region = region
        self.pricing = PricingLookup(region)

    def estimate_from_graph_engine(
        self,
        graph_engine: GraphEngine,
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> CostEstimate:
        """
        Estimate costs from RepliMap's GraphEngine.

        Args:
            graph_engine: Existing graph engine with scanned resources
            pricing_tier: Default pricing tier to use

        Returns:
            CostEstimate with detailed breakdown
        """
        resource_costs: list[ResourceCost] = []
        assumptions: list[str] = []
        warnings: list[str] = []

        for resource in graph_engine.get_all_resources():
            cost = self._estimate_resource_cost(
                resource_id=resource.id,
                resource_type=str(resource.resource_type),
                resource_name=resource.original_name or resource.id,
                config=resource.config or {},
                region=resource.region or self.region,
                pricing_tier=pricing_tier,
            )

            if cost.monthly_cost > 0 or cost.confidence != CostConfidence.UNKNOWN:
                resource_costs.append(cost)
                assumptions.extend(cost.assumptions)

        return self._build_estimate(resource_costs, assumptions, warnings)

    def estimate_from_resources(
        self,
        resources: list[dict[str, Any]],
        pricing_tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> CostEstimate:
        """
        Estimate costs from resource dictionaries.

        Args:
            resources: List of resource dicts from scanner
            pricing_tier: Default pricing tier to use

        Returns:
            CostEstimate with detailed breakdown
        """
        resource_costs: list[ResourceCost] = []
        assumptions: list[str] = []
        warnings: list[str] = []

        for resource in resources:
            cost = self._estimate_resource_cost(
                resource_id=resource["id"],
                resource_type=resource["type"],
                resource_name=resource.get("name", resource["id"]),
                config=resource.get("config", {}),
                region=resource.get("region", self.region),
                pricing_tier=pricing_tier,
            )

            if cost.monthly_cost > 0 or cost.confidence != CostConfidence.UNKNOWN:
                resource_costs.append(cost)
                assumptions.extend(cost.assumptions)

        return self._build_estimate(resource_costs, assumptions, warnings)

    def _estimate_resource_cost(
        self,
        resource_id: str,
        resource_type: str,
        resource_name: str,
        config: dict[str, Any],
        region: str,
        pricing_tier: PricingTier,
    ) -> ResourceCost:
        """Estimate cost for a single resource."""
        category = self.pricing.get_resource_category(resource_type)

        cost = ResourceCost(
            resource_id=resource_id,
            resource_type=resource_type,
            resource_name=resource_name,
            category=category,
            pricing_tier=pricing_tier,
            region=region,
        )

        # Route to type-specific estimators
        if resource_type == "aws_instance":
            self._estimate_ec2(cost, config, pricing_tier)
        elif resource_type == "aws_db_instance":
            self._estimate_rds(cost, config, pricing_tier)
        elif resource_type == "aws_rds_cluster":
            self._estimate_rds_cluster(cost, config, pricing_tier)
        elif resource_type == "aws_elasticache_cluster":
            self._estimate_elasticache(cost, config, pricing_tier)
        elif resource_type == "aws_nat_gateway":
            self._estimate_nat_gateway(cost, config)
        elif resource_type in ("aws_lb", "aws_alb"):
            self._estimate_alb(cost, config)
        elif resource_type == "aws_elb":
            self._estimate_clb(cost, config)
        elif resource_type == "aws_s3_bucket":
            self._estimate_s3(cost, config)
        elif resource_type == "aws_ebs_volume":
            self._estimate_ebs(cost, config)
        elif resource_type == "aws_efs_file_system":
            self._estimate_efs(cost, config)
        elif resource_type == "aws_lambda_function":
            self._estimate_lambda(cost, config)
        elif resource_type == "aws_vpc_endpoint":
            self._estimate_vpc_endpoint(cost, config)
        elif resource_type == "aws_eip":
            self._estimate_eip(cost, config)
        elif resource_type == "aws_eks_cluster":
            self._estimate_eks(cost, config)
        elif resource_type == "aws_cloudwatch_log_group":
            self._estimate_cloudwatch_logs(cost, config)
        # New services
        elif resource_type in ("aws_docdb_cluster", "aws_docdb_cluster_instance"):
            self._estimate_documentdb(cost, config, pricing_tier)
        elif resource_type == "aws_sqs_queue":
            self._estimate_sqs(cost, config)
        elif resource_type == "aws_sns_topic":
            self._estimate_sns(cost, config)
        elif resource_type == "aws_route53_zone":
            self._estimate_route53(cost, config)
        elif resource_type == "aws_kms_key":
            self._estimate_kms(cost, config)
        elif resource_type == "aws_secretsmanager_secret":
            self._estimate_secrets_manager(cost, config)
        elif resource_type == "aws_ecr_repository":
            self._estimate_ecr(cost, config)
        elif resource_type == "aws_cloudfront_distribution":
            self._estimate_cloudfront(cost, config)
        elif resource_type == "aws_guardduty_detector":
            self._estimate_guardduty(cost, config)
        elif resource_type == "aws_cloudwatch_metric_alarm":
            self._estimate_cloudwatch_alarm(cost, config)
        elif resource_type == "aws_cloudwatch_dashboard":
            self._estimate_cloudwatch_dashboard(cost, config)
        elif resource_type in ("aws_cloudtrail", "aws_cloudtrail_trail"):
            self._estimate_cloudtrail(cost, config)
        elif resource_type in self._free_resources():
            cost.monthly_cost = 0.0
            cost.confidence = CostConfidence.HIGH
        else:
            cost.confidence = CostConfidence.UNKNOWN
            cost.assumptions.append(f"No pricing data for {resource_type}")

        # Calculate derived values
        if cost.monthly_cost > 0:
            cost.hourly_cost = cost.monthly_cost / HOURS_PER_MONTH
            cost.annual_cost = cost.monthly_cost * 12

        # Generate optimization tips
        self._add_optimization_tips(cost, config)

        return cost

    def _estimate_ec2(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
        pricing_tier: PricingTier,
    ) -> None:
        """Estimate EC2 instance cost."""
        instance_type = config.get("instance_type", "t3.medium")
        cost.instance_type = instance_type

        hourly = self.pricing.get_ec2_hourly_cost(instance_type, pricing_tier)
        cost.compute_cost = hourly * HOURS_PER_MONTH

        # EBS root volume
        # Handle both list and dict formats - GraphEngine may flatten single-element lists
        rbd_raw = config.get("root_block_device")
        if isinstance(rbd_raw, list) and len(rbd_raw) > 0:
            root_volume = rbd_raw[0]
        elif isinstance(rbd_raw, dict):
            root_volume = rbd_raw
        else:
            root_volume = {}
        volume_size = root_volume.get("volume_size", 8)
        volume_type = root_volume.get("volume_type", "gp2")
        cost.storage_cost = self.pricing.get_ebs_monthly_cost(volume_size, volume_type)

        cost.monthly_cost = cost.compute_cost + cost.storage_cost
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append(f"EC2 {instance_type} running 24/7")

    def _estimate_rds(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
        pricing_tier: PricingTier,
    ) -> None:
        """Estimate RDS instance cost."""
        instance_class = config.get("instance_class", "db.t3.medium")
        cost.instance_type = instance_class

        multi_az = config.get("multi_az", False)
        hourly = self.pricing.get_rds_hourly_cost(
            instance_class, multi_az, pricing_tier
        )
        cost.compute_cost = hourly * HOURS_PER_MONTH

        # Storage
        storage_gb = config.get("allocated_storage", 20)
        storage_type = config.get("storage_type", "gp2")
        iops = config.get("iops", 0)
        cost.storage_cost = self.pricing.get_rds_storage_monthly_cost(
            storage_gb, storage_type, iops
        )

        cost.monthly_cost = cost.compute_cost + cost.storage_cost
        cost.confidence = CostConfidence.HIGH

        assumptions = [f"RDS {instance_class}"]
        if multi_az:
            assumptions.append("Multi-AZ")
        cost.assumptions.extend(assumptions)

    def _estimate_rds_cluster(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
        pricing_tier: PricingTier,
    ) -> None:
        """Estimate RDS Aurora cluster cost."""
        # Aurora clusters charge for compute + I/O + storage
        instance_class = config.get("db_cluster_instance_class", "db.r5.large")
        cost.instance_type = instance_class

        # Default 2 instances in cluster
        instance_count = 2
        hourly = self.pricing.get_rds_hourly_cost(instance_class, False, pricing_tier)
        cost.compute_cost = hourly * HOURS_PER_MONTH * instance_count

        # Aurora storage ($0.10/GB-month, charged for actual usage)
        estimated_storage_gb = 100  # Estimate
        cost.storage_cost = estimated_storage_gb * 0.10

        cost.monthly_cost = cost.compute_cost + cost.storage_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append(f"Aurora cluster with {instance_count} instances")
        cost.assumptions.append(f"Estimated {estimated_storage_gb}GB storage")

    def _estimate_elasticache(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
        pricing_tier: PricingTier,
    ) -> None:
        """Estimate ElastiCache cost."""
        node_type = config.get("node_type", "cache.t3.medium")
        cost.instance_type = node_type

        num_nodes = config.get("num_cache_nodes", 1)
        hourly = self.pricing.get_elasticache_hourly_cost(
            node_type, num_nodes, pricing_tier
        )

        cost.compute_cost = hourly * HOURS_PER_MONTH
        cost.monthly_cost = cost.compute_cost
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append(f"ElastiCache {node_type} x {num_nodes} nodes")

    def _estimate_nat_gateway(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate NAT Gateway cost."""
        # Estimate data processing (default 100GB/month)
        data_gb = config.get("estimated_data_gb", 100)

        cost.compute_cost = 0.045 * HOURS_PER_MONTH  # Hourly charge
        cost.network_cost = data_gb * 0.045  # Data processing

        cost.monthly_cost = cost.compute_cost + cost.network_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append(f"NAT Gateway with ~{data_gb}GB/month data transfer")

    def _estimate_alb(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Application Load Balancer cost."""
        cost.compute_cost = self.pricing.get_load_balancer_monthly_cost("alb")
        cost.monthly_cost = cost.compute_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append("ALB with default LCU usage estimate")

    def _estimate_clb(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Classic Load Balancer cost."""
        cost.compute_cost = self.pricing.get_load_balancer_monthly_cost("clb")
        cost.monthly_cost = cost.compute_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append("Classic LB hourly cost only")

    def _estimate_s3(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate S3 bucket cost."""
        # S3 costs depend on actual usage - provide estimate
        estimated_gb = config.get("estimated_storage_gb", 100)
        storage_class = config.get("storage_class", "STANDARD")

        cost.storage_cost = self.pricing.get_s3_monthly_cost(
            estimated_gb, storage_class
        )
        cost.monthly_cost = cost.storage_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"S3 estimated at {estimated_gb}GB {storage_class}")

    def _estimate_ebs(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate EBS volume cost."""
        size = config.get("size", 100)
        volume_type = config.get("type", "gp2")
        iops = config.get("iops", 0)
        throughput = config.get("throughput", 0)

        cost.storage_cost = self.pricing.get_ebs_monthly_cost(
            size, volume_type, iops, throughput
        )
        cost.monthly_cost = cost.storage_cost
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append(f"EBS {volume_type} {size}GB")

    def _estimate_efs(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate EFS cost."""
        # EFS charges per GB stored
        estimated_gb = config.get("estimated_storage_gb", 50)

        cost.storage_cost = estimated_gb * 0.30  # Standard storage
        cost.monthly_cost = cost.storage_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"EFS estimated at {estimated_gb}GB")

    def _estimate_lambda(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Lambda cost."""
        # Lambda costs depend on invocations - provide estimate
        memory_mb = config.get("memory_size", 128)
        estimated_invocations = config.get("estimated_invocations", 100000)
        avg_duration_ms = config.get("estimated_duration_ms", 100)

        cost.compute_cost = self.pricing.get_lambda_monthly_cost(
            estimated_invocations, avg_duration_ms, memory_mb
        )
        cost.monthly_cost = cost.compute_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"Lambda ~{estimated_invocations} invocations/month")

    def _estimate_vpc_endpoint(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate VPC Endpoint cost."""
        data_gb = config.get("estimated_data_gb", 10)
        cost.network_cost = self.pricing.get_vpc_endpoint_monthly_cost(data_gb)
        cost.monthly_cost = cost.network_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append("VPC Endpoint interface type")

    def _estimate_eip(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Elastic IP cost."""
        # EIP is free when attached, $0.005/hour when not
        # Assume attached by default
        cost.monthly_cost = 0.0
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append("EIP attached to running instance (free)")

    def _estimate_eks(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate EKS cluster cost."""
        # EKS control plane: $0.10/hour
        cost.compute_cost = 0.10 * HOURS_PER_MONTH
        cost.monthly_cost = cost.compute_cost
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append("EKS control plane only (node costs separate)")

    def _estimate_cloudwatch_logs(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate CloudWatch Logs cost."""
        # $0.50 per GB ingested
        estimated_gb = config.get("estimated_ingestion_gb", 1)
        cost.other_cost = estimated_gb * 0.50
        cost.monthly_cost = cost.other_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"CloudWatch ~{estimated_gb}GB/month ingestion")

    def _estimate_documentdb(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
        pricing_tier: PricingTier,
    ) -> None:
        """Estimate DocumentDB cost."""
        instance_class = config.get("instance_class", "db.r5.large")
        cost.instance_type = instance_class

        hourly = self.pricing.get_documentdb_hourly_cost(instance_class, pricing_tier)
        cost.compute_cost = hourly * HOURS_PER_MONTH

        # Storage: $0.10 per GB-month
        storage_gb = config.get("storage_encrypted", 10)
        if isinstance(storage_gb, bool):
            storage_gb = 10  # Default if storage_encrypted is bool flag
        cost.storage_cost = storage_gb * 0.10

        # I/O: estimate based on typical usage
        io_cost = 5.0  # Estimate $5/month I/O

        cost.monthly_cost = cost.compute_cost + cost.storage_cost + io_cost
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append(f"DocumentDB {instance_class}, ~{storage_gb}GB storage")

    def _estimate_sqs(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate SQS queue cost."""
        is_fifo = config.get("fifo_queue", False)
        # Estimate requests based on queue type
        estimated_requests = config.get("estimated_requests_per_month", 10_000_000)
        cost.monthly_cost = self.pricing.get_sqs_monthly_cost(estimated_requests, is_fifo)
        cost.confidence = CostConfidence.LOW
        queue_type = "FIFO" if is_fifo else "Standard"
        cost.assumptions.append(f"SQS {queue_type} ~{estimated_requests/1_000_000:.1f}M requests/month")

    def _estimate_sns(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate SNS topic cost."""
        # Estimate based on typical usage
        estimated_publishes = config.get("estimated_publishes_per_month", 1_000_000)
        estimated_notifications = config.get("estimated_notifications_per_month", 1_000_000)
        cost.monthly_cost = self.pricing.get_sns_monthly_cost(
            estimated_publishes, estimated_notifications
        )
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"SNS ~{estimated_publishes/1_000_000:.1f}M publishes/month")

    def _estimate_route53(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Route 53 hosted zone cost."""
        # $0.50 per hosted zone
        cost.monthly_cost = self.pricing.get_route53_monthly_cost(
            hosted_zones=1,
            queries_per_month=config.get("estimated_queries_per_month", 1_000_000),
            health_checks=config.get("health_checks", 0),
        )
        cost.confidence = CostConfidence.MEDIUM
        cost.assumptions.append("Route 53 hosted zone + estimated queries")

    def _estimate_kms(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate KMS key cost."""
        # Customer managed keys: $1/month
        # AWS managed keys: free
        is_customer_managed = config.get("customer_master_key_spec") is not None
        if is_customer_managed:
            cost.monthly_cost = self.pricing.get_kms_monthly_cost(
                customer_keys=1,
                requests_per_month=config.get("estimated_requests_per_month", 10000),
            )
            cost.confidence = CostConfidence.HIGH
            cost.assumptions.append("KMS customer managed key")
        else:
            cost.monthly_cost = 0.0
            cost.confidence = CostConfidence.HIGH
            cost.assumptions.append("KMS AWS managed key (free)")

    def _estimate_secrets_manager(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate Secrets Manager cost."""
        # $0.40 per secret per month
        cost.monthly_cost = self.pricing.get_secrets_manager_monthly_cost(
            secrets_count=1,
            api_calls_per_month=config.get("estimated_api_calls_per_month", 10000),
        )
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append("Secrets Manager secret")

    def _estimate_ecr(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate ECR repository cost."""
        # $0.10 per GB storage
        estimated_storage_gb = config.get("estimated_storage_gb", 1.0)
        cost.storage_cost = self.pricing.get_ecr_monthly_cost(estimated_storage_gb)
        cost.monthly_cost = cost.storage_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"ECR ~{estimated_storage_gb}GB storage")

    def _estimate_cloudfront(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate CloudFront distribution cost."""
        estimated_transfer_gb = config.get("estimated_transfer_gb", 100.0)
        estimated_requests = config.get("estimated_requests_per_month", 1_000_000)
        cost.network_cost = self.pricing.get_cloudfront_monthly_cost(
            estimated_transfer_gb, estimated_requests
        )
        cost.monthly_cost = cost.network_cost
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append(f"CloudFront ~{estimated_transfer_gb}GB transfer/month")

    def _estimate_guardduty(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate GuardDuty detector cost."""
        # Cost depends on CloudTrail events and VPC Flow Logs analyzed
        estimated_ct_events = config.get("estimated_cloudtrail_events", 1_000_000)
        estimated_vpc_flow_gb = config.get("estimated_vpc_flow_gb", 10.0)
        cost.monthly_cost = self.pricing.get_guardduty_monthly_cost(
            estimated_ct_events, estimated_vpc_flow_gb
        )
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append("GuardDuty based on estimated event volume")

    def _estimate_cloudwatch_alarm(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate CloudWatch alarm cost."""
        # Standard alarms: $0.10/month, High-res: $0.30/month
        period = config.get("period", 60)
        is_high_res = period < 60
        cost.monthly_cost = 0.30 if is_high_res else 0.10
        cost.confidence = CostConfidence.HIGH
        alarm_type = "high-resolution" if is_high_res else "standard"
        cost.assumptions.append(f"CloudWatch {alarm_type} alarm")

    def _estimate_cloudwatch_dashboard(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate CloudWatch dashboard cost."""
        # First 3 dashboards free, then $3/month each
        cost.monthly_cost = 3.00  # Assume not in free tier
        cost.confidence = CostConfidence.HIGH
        cost.assumptions.append("CloudWatch dashboard (if >3 total)")

    def _estimate_cloudtrail(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Estimate CloudTrail cost."""
        # First management trail free, additional trails $2 per 100K events
        is_multi_region = config.get("is_multi_region_trail", False)
        include_data_events = config.get("include_global_service_events", False)
        estimated_events = config.get("estimated_events_per_month", 100_000)

        cost.monthly_cost = self.pricing.get_cloudtrail_monthly_cost(
            management_events_per_month=estimated_events if is_multi_region else 0,
            data_events_per_month=estimated_events if include_data_events else 0,
        )
        cost.confidence = CostConfidence.LOW
        cost.assumptions.append("CloudTrail based on estimated events")

    def _free_resources(self) -> set[str]:
        """Resources that have no direct cost."""
        return {
            "aws_vpc",
            "aws_subnet",
            "aws_internet_gateway",
            "aws_route_table",
            "aws_route",
            "aws_route_table_association",
            "aws_security_group",
            "aws_security_group_rule",
            "aws_iam_role",
            "aws_iam_policy",
            "aws_iam_role_policy_attachment",
            "aws_iam_instance_profile",
            "aws_db_subnet_group",
            "aws_db_parameter_group",
            "aws_lb_target_group",
            "aws_lb_listener",
            "aws_lb_listener_rule",
            "aws_launch_template",
            "aws_key_pair",
        }

    def _add_optimization_tips(
        self,
        cost: ResourceCost,
        config: dict[str, Any],
    ) -> None:
        """Add optimization tips for the resource."""
        tips: list[str] = []
        potential = 0.0

        if cost.resource_type == "aws_instance":
            instance_type = config.get("instance_type", "")

            # Suggest reserved instances for high-cost instances
            if cost.monthly_cost > 100 and cost.pricing_tier == PricingTier.ON_DEMAND:
                tips.append("Consider Reserved Instances for ~40% savings")
                potential = cost.monthly_cost * 0.40

            # Suggest right-sizing
            if instance_type.startswith(("m5.", "m6i.", "r5.")):
                tips.append("Review if instance is right-sized for workload")

            # Suggest Graviton
            if instance_type.startswith(("m5.", "c5.", "r5.")):
                tips.append(
                    "Consider Graviton instances (m6g/c6g/r6g) for ~20% savings"
                )
                potential = max(potential, cost.monthly_cost * 0.20)

        elif cost.resource_type == "aws_db_instance":
            multi_az = config.get("multi_az", False)
            instance_class = config.get("instance_class", "")

            if cost.monthly_cost > 200 and cost.pricing_tier == PricingTier.ON_DEMAND:
                tips.append("Consider Reserved DB Instances for ~40% savings")
                potential = cost.monthly_cost * 0.40

            if not multi_az:
                tips.append("Consider Multi-AZ for high availability")

            if instance_class.startswith("db.r5."):
                tips.append("Consider Aurora Serverless for variable workloads")

        elif cost.resource_type == "aws_nat_gateway":
            if cost.monthly_cost > 100:
                tips.append("Consider NAT instances for lower traffic workloads")
                tips.append("Review if all subnets need NAT Gateway access")
                potential = cost.monthly_cost * 0.50

        elif cost.resource_type == "aws_ebs_volume":
            volume_type = config.get("type", "gp2")
            if volume_type == "gp2":
                tips.append("Consider migrating to gp3 for ~20% savings")
                potential = cost.monthly_cost * 0.20

        elif cost.resource_type == "aws_s3_bucket":
            tips.append("Enable S3 Intelligent-Tiering for automatic cost optimization")
            tips.append("Set lifecycle policies for infrequent access data")

        cost.optimization_tips = tips
        cost.optimization_potential = potential

    def _build_estimate(
        self,
        resource_costs: list[ResourceCost],
        assumptions: list[str],
        warnings: list[str],
    ) -> CostEstimate:
        """Build the complete cost estimate."""
        # Calculate totals
        monthly_total = sum(r.monthly_cost for r in resource_costs)
        annual_total = monthly_total * 12
        daily_average = monthly_total / 30

        # Build category breakdowns
        by_category = self._build_category_breakdown(resource_costs, monthly_total)

        # Build region breakdown
        by_region: dict[str, float] = {}
        for r in resource_costs:
            region = r.region or "unknown"
            by_region[region] = by_region.get(region, 0) + r.monthly_cost

        # Get top 10 most expensive resources
        top_resources = sorted(
            resource_costs, key=lambda r: r.monthly_cost, reverse=True
        )[:10]

        # Generate recommendations first, then calculate total from recommendations
        recommendations = self._generate_recommendations(resource_costs, by_category)

        # Calculate optimization potential from recommendations (not per-resource values)
        # This ensures header total matches the sum of recommendation savings
        total_optimization = sum(rec.potential_savings for rec in recommendations)
        optimization_pct = (
            (total_optimization / monthly_total * 100) if monthly_total > 0 else 0
        )

        # Count estimated vs unestimated
        estimated = len(
            [r for r in resource_costs if r.confidence != CostConfidence.UNKNOWN]
        )
        unestimated = len(resource_costs) - estimated

        # Determine overall confidence
        if unestimated > estimated:
            confidence = CostConfidence.LOW
        elif any(r.confidence == CostConfidence.LOW for r in resource_costs):
            confidence = CostConfidence.MEDIUM
        else:
            confidence = CostConfidence.HIGH

        # Add warnings
        if unestimated > 0:
            warnings.append(f"{unestimated} resources could not be estimated")

        if monthly_total > 10000:
            warnings.append("High monthly cost - review for optimization opportunities")

        return CostEstimate(
            monthly_total=monthly_total,
            annual_total=annual_total,
            daily_average=daily_average,
            resource_costs=resource_costs,
            by_category=by_category,
            by_region=by_region,
            top_resources=top_resources,
            total_optimization_potential=total_optimization,
            optimization_percentage=optimization_pct,
            recommendations=recommendations,
            resource_count=len(resource_costs),
            estimated_resources=estimated,
            unestimated_resources=unestimated,
            confidence=confidence,
            assumptions=list(set(assumptions)),  # Deduplicate
            warnings=warnings,
        )

    def _build_category_breakdown(
        self,
        resource_costs: list[ResourceCost],
        monthly_total: float,
    ) -> list[CostBreakdown]:
        """Build cost breakdown by category."""
        category_resources: dict[CostCategory, list[ResourceCost]] = {}

        for r in resource_costs:
            if r.category not in category_resources:
                category_resources[r.category] = []
            category_resources[r.category].append(r)

        breakdowns: list[CostBreakdown] = []
        for category in CostCategory:
            resources = category_resources.get(category, [])
            total = sum(r.monthly_cost for r in resources)
            pct = (total / monthly_total * 100) if monthly_total > 0 else 0

            if resources:  # Only include non-empty categories
                breakdowns.append(
                    CostBreakdown(
                        category=category,
                        resources=resources,
                        monthly_total=total,
                        percentage=pct,
                    )
                )

        # Sort by total cost descending
        breakdowns.sort(key=lambda b: b.monthly_total, reverse=True)
        return breakdowns

    def _generate_recommendations(
        self,
        resource_costs: list[ResourceCost],
        by_category: list[CostBreakdown],
    ) -> list[OptimizationRecommendation]:
        """Generate optimization recommendations."""
        recommendations: list[OptimizationRecommendation] = []

        # Check for Reserved Instance opportunities
        on_demand_compute = [
            r
            for r in resource_costs
            if r.resource_type in ("aws_instance", "aws_db_instance")
            and r.pricing_tier == PricingTier.ON_DEMAND
            and r.monthly_cost > 100
        ]

        if on_demand_compute:
            total_savings = sum(r.monthly_cost * 0.40 for r in on_demand_compute)
            recommendations.append(
                OptimizationRecommendation(
                    title="Reserved Instances",
                    description="Convert on-demand instances to reserved for significant savings",
                    potential_savings=total_savings,
                    effort="MEDIUM",
                    affected_resources=[r.resource_id for r in on_demand_compute],
                    action_items=[
                        "Analyze instance usage patterns",
                        "Purchase 1-year or 3-year reserved capacity",
                        "Consider Savings Plans for flexibility",
                    ],
                )
            )

        # Check for gp2 to gp3 migration
        gp2_volumes = [
            r
            for r in resource_costs
            if r.resource_type == "aws_ebs_volume"
            and r.assumptions
            and "gp2" in r.assumptions[0]
        ]

        if gp2_volumes:
            total_savings = sum(r.monthly_cost * 0.20 for r in gp2_volumes)
            if total_savings > 10:
                recommendations.append(
                    OptimizationRecommendation(
                        title="Migrate EBS gp2 to gp3",
                        description="gp3 volumes are 20% cheaper with better performance",
                        potential_savings=total_savings,
                        effort="LOW",
                        affected_resources=[r.resource_id for r in gp2_volumes],
                        action_items=[
                            "Identify gp2 volumes",
                            "Modify volume type to gp3 (no downtime)",
                            "Adjust IOPS/throughput if needed",
                        ],
                    )
                )

        # Check for NAT Gateway costs
        nat_gateways = [
            r for r in resource_costs if r.resource_type == "aws_nat_gateway"
        ]

        if len(nat_gateways) > 2:
            total_cost = sum(r.monthly_cost for r in nat_gateways)
            recommendations.append(
                OptimizationRecommendation(
                    title="Review NAT Gateway Architecture",
                    description=f"You have {len(nat_gateways)} NAT Gateways - consider consolidation",
                    potential_savings=total_cost * 0.30,
                    effort="HIGH",
                    affected_resources=[r.resource_id for r in nat_gateways],
                    action_items=[
                        "Review if all AZs need NAT Gateway",
                        "Consider VPC endpoints for AWS services",
                        "Evaluate NAT instances for low-traffic workloads",
                    ],
                )
            )

        # Sort by potential savings
        recommendations.sort(key=lambda r: r.potential_savings, reverse=True)
        return recommendations[:5]  # Top 5 recommendations
