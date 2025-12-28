"""
Unused Resource Detector.

Identifies idle, underutilized, or orphaned AWS resources
that may be candidates for termination or optimization.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from replimap.core import GraphEngine
from replimap.core.async_aws import AsyncAWSClient
from replimap.core.models import ResourceNode, ResourceType

logger = logging.getLogger(__name__)


class UnusedReason(str, Enum):
    """Reasons a resource is considered unused."""

    LOW_CPU = "low_cpu_utilization"
    LOW_NETWORK = "low_network_activity"
    NO_CONNECTIONS = "no_connections"
    UNATTACHED = "unattached"
    ORPHANED = "orphaned_resource"
    STOPPED = "stopped_long_term"
    NO_TRAFFIC = "no_traffic"
    STALE = "stale_resource"
    ZERO_USAGE = "zero_usage"

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        """Get human-readable description."""
        descriptions = {
            "low_cpu_utilization": "CPU utilization below threshold for extended period",
            "low_network_activity": "Network I/O near zero for extended period",
            "no_connections": "No database connections for extended period",
            "unattached": "Resource not attached to any instance or service",
            "orphaned_resource": "Resource has no parent or associated resources",
            "stopped_long_term": "Instance stopped for extended period",
            "no_traffic": "Load balancer receiving no traffic",
            "stale_resource": "Resource not modified or accessed recently",
            "zero_usage": "Zero usage metrics detected",
        }
        return descriptions.get(self.value, self.value)


class ConfidenceLevel(str, Enum):
    """Confidence in unused determination."""

    HIGH = "high"  # Very likely unused, safe to remove
    MEDIUM = "medium"  # Probably unused, verify before removing
    LOW = "low"  # Possibly unused, investigate further

    def __str__(self) -> str:
        return self.value


@dataclass
class UnusedResource:
    """Details about an unused or underutilized resource."""

    resource_id: str
    resource_type: str
    resource_name: str
    region: str
    account_id: str

    # Unused determination
    reason: UnusedReason
    confidence: ConfidenceLevel
    details: str

    # Metrics
    last_activity: datetime | None = None
    idle_days: int = 0
    utilization_pct: float = 0.0

    # Cost impact
    monthly_cost: float = 0.0
    potential_savings: float = 0.0

    # Recommendations
    recommendation: str = ""
    action_items: list[str] = field(default_factory=list)

    # Tags for context
    tags: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "account_id": self.account_id,
            "reason": str(self.reason),
            "reason_description": self.reason.description,
            "confidence": str(self.confidence),
            "details": self.details,
            "last_activity": (
                self.last_activity.isoformat() if self.last_activity else None
            ),
            "idle_days": self.idle_days,
            "utilization_pct": round(self.utilization_pct, 1),
            "monthly_cost": round(self.monthly_cost, 2),
            "potential_savings": round(self.potential_savings, 2),
            "recommendation": self.recommendation,
            "action_items": self.action_items,
            "tags": self.tags,
        }


@dataclass
class UnusedResourcesReport:
    """Report of all unused resources detected."""

    scan_date: datetime
    account_id: str
    regions: list[str]

    # Resources
    unused_resources: list[UnusedResource] = field(default_factory=list)

    # By category
    by_type: dict[str, list[UnusedResource]] = field(default_factory=dict)
    by_region: dict[str, list[UnusedResource]] = field(default_factory=dict)
    by_reason: dict[str, list[UnusedResource]] = field(default_factory=dict)

    # Summary
    total_resources_scanned: int = 0
    total_unused: int = 0
    total_monthly_cost: float = 0.0
    total_potential_savings: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scan_date": self.scan_date.isoformat(),
            "account_id": self.account_id,
            "regions": self.regions,
            "summary": {
                "total_scanned": self.total_resources_scanned,
                "total_unused": self.total_unused,
                "total_monthly_cost": round(self.total_monthly_cost, 2),
                "potential_monthly_savings": round(self.total_potential_savings, 2),
            },
            "unused_resources": [r.to_dict() for r in self.unused_resources],
            "by_type": {
                k: [r.resource_id for r in v] for k, v in self.by_type.items()
            },
            "by_region": {
                k: [r.resource_id for r in v] for k, v in self.by_region.items()
            },
            "by_reason": {
                k: [r.resource_id for r in v] for k, v in self.by_reason.items()
            },
        }


# Thresholds for unused detection
THRESHOLDS = {
    "ec2_cpu_low": 5.0,  # 5% CPU average
    "ec2_network_low": 1000,  # 1KB/s average
    "ec2_stopped_days": 7,  # 7 days stopped
    "rds_connections_low": 1,  # Less than 1 connection average
    "rds_cpu_low": 5.0,  # 5% CPU average
    "ebs_iops_low": 10,  # 10 IOPS average
    "ebs_unattached_days": 7,  # 7 days unattached
    "elb_requests_low": 10,  # Less than 10 requests/day
    "nat_gateway_bytes_low": 1000,  # 1KB total
    "elastic_ip_unattached_days": 1,  # 1 day unattached
}


class UnusedResourceDetector:
    """
    Detects unused and underutilized AWS resources.

    Uses CloudWatch metrics and resource relationships
    to identify resources suitable for cleanup.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
        lookback_days: int = 14,
    ) -> None:
        """
        Initialize detector.

        Args:
            region: AWS region
            account_id: AWS account ID
            lookback_days: Days of metrics to analyze
        """
        self.region = region
        self.account_id = account_id
        self.lookback_days = lookback_days
        self._client: AsyncAWSClient | None = None

    async def _get_client(self) -> AsyncAWSClient:
        """Get or create AWS client."""
        if self._client is None:
            self._client = AsyncAWSClient(region=self.region)
        return self._client

    async def scan(
        self,
        graph: GraphEngine,
        check_metrics: bool = True,
    ) -> UnusedResourcesReport:
        """
        Scan for unused resources.

        Args:
            graph: GraphEngine with resource inventory
            check_metrics: Whether to check CloudWatch metrics

        Returns:
            UnusedResourcesReport with findings
        """
        report = UnusedResourcesReport(
            scan_date=datetime.now(),
            account_id=self.account_id,
            regions=[self.region],
        )

        # Scan different resource types
        unused = []

        # EC2 Instances
        ec2_unused = await self._scan_ec2_instances(graph, check_metrics)
        unused.extend(ec2_unused)

        # EBS Volumes
        ebs_unused = await self._scan_ebs_volumes(graph, check_metrics)
        unused.extend(ebs_unused)

        # RDS Instances
        rds_unused = await self._scan_rds_instances(graph, check_metrics)
        unused.extend(rds_unused)

        # Elastic IPs
        eip_unused = await self._scan_elastic_ips(graph)
        unused.extend(eip_unused)

        # Load Balancers
        elb_unused = await self._scan_load_balancers(graph, check_metrics)
        unused.extend(elb_unused)

        # NAT Gateways
        nat_unused = await self._scan_nat_gateways(graph, check_metrics)
        unused.extend(nat_unused)

        # Build report
        report.unused_resources = unused
        report.total_resources_scanned = len(graph.get_all_resources())
        report.total_unused = len(unused)

        # Calculate totals
        report.total_monthly_cost = sum(r.monthly_cost for r in unused)
        report.total_potential_savings = sum(r.potential_savings for r in unused)

        # Group by type, region, reason
        for resource in unused:
            # By type
            if resource.resource_type not in report.by_type:
                report.by_type[resource.resource_type] = []
            report.by_type[resource.resource_type].append(resource)

            # By region
            if resource.region not in report.by_region:
                report.by_region[resource.region] = []
            report.by_region[resource.region].append(resource)

            # By reason
            reason = str(resource.reason)
            if reason not in report.by_reason:
                report.by_reason[reason] = []
            report.by_reason[reason].append(resource)

        return report

    async def _scan_ec2_instances(
        self,
        graph: GraphEngine,
        check_metrics: bool,
    ) -> list[UnusedResource]:
        """Scan EC2 instances for unused."""
        unused = []

        for node in graph.get_resources_by_type(ResourceType.EC2_INSTANCE):
            # Check if stopped
            state = node.config.get("state", "")
            if state == "stopped":
                # Check how long stopped
                launch_time = node.config.get("launch_time")
                if launch_time:
                    days_stopped = self._days_since(launch_time)
                    if days_stopped >= THRESHOLDS["ec2_stopped_days"]:
                        unused.append(
                            UnusedResource(
                                resource_id=node.id,
                                resource_type=str(node.resource_type),
                                resource_name=node.tags.get("Name", node.id),
                                region=node.region,
                                account_id=self.account_id,
                                reason=UnusedReason.STOPPED,
                                confidence=ConfidenceLevel.HIGH,
                                details=f"Instance stopped for {days_stopped} days",
                                idle_days=days_stopped,
                                monthly_cost=self._estimate_ec2_cost(node),
                                potential_savings=self._estimate_ec2_cost(node),
                                recommendation="Terminate or create AMI and terminate",
                                action_items=[
                                    "Review if instance is still needed",
                                    "Create AMI backup if data preservation required",
                                    "Terminate instance to stop EBS charges",
                                ],
                                tags=node.tags,
                            )
                        )
                continue

            # Check metrics for running instances
            if check_metrics and state == "running":
                metrics = await self._get_ec2_metrics(node.id)
                if metrics:
                    cpu_avg = metrics.get("cpu_avg", 100)
                    network_avg = metrics.get("network_avg", float("inf"))

                    if cpu_avg < THRESHOLDS["ec2_cpu_low"]:
                        unused.append(
                            UnusedResource(
                                resource_id=node.id,
                                resource_type=str(node.resource_type),
                                resource_name=node.tags.get("Name", node.id),
                                region=node.region,
                                account_id=self.account_id,
                                reason=UnusedReason.LOW_CPU,
                                confidence=ConfidenceLevel.MEDIUM,
                                details=f"Average CPU: {cpu_avg:.1f}%",
                                utilization_pct=cpu_avg,
                                monthly_cost=self._estimate_ec2_cost(node),
                                potential_savings=self._estimate_ec2_cost(node) * 0.5,
                                recommendation="Right-size to smaller instance type",
                                action_items=[
                                    "Review workload requirements",
                                    "Consider smaller instance type",
                                    "Evaluate if instance is needed",
                                ],
                                tags=node.tags,
                            )
                        )

        return unused

    async def _scan_ebs_volumes(
        self,
        graph: GraphEngine,
        check_metrics: bool,
    ) -> list[UnusedResource]:
        """Scan EBS volumes for unused."""
        unused = []

        for node in graph.get_resources_by_type(ResourceType.EBS_VOLUME):
            # Check if attached
            attachments = node.config.get("attachments", [])
            if not attachments:
                # Unattached volume
                unused.append(
                    UnusedResource(
                        resource_id=node.id,
                        resource_type=str(node.resource_type),
                        resource_name=node.tags.get("Name", node.id),
                        region=node.region,
                        account_id=self.account_id,
                        reason=UnusedReason.UNATTACHED,
                        confidence=ConfidenceLevel.HIGH,
                        details="Volume not attached to any instance",
                        monthly_cost=self._estimate_ebs_cost(node),
                        potential_savings=self._estimate_ebs_cost(node),
                        recommendation="Delete or create snapshot and delete",
                        action_items=[
                            "Verify data is not needed",
                            "Create snapshot if backup required",
                            "Delete unattached volume",
                        ],
                        tags=node.tags,
                    )
                )

        return unused

    async def _scan_rds_instances(
        self,
        graph: GraphEngine,
        check_metrics: bool,
    ) -> list[UnusedResource]:
        """Scan RDS instances for unused."""
        unused = []

        for node in graph.get_resources_by_type(ResourceType.RDS_INSTANCE):
            status = node.config.get("status", "")

            # Check stopped instances
            if status == "stopped":
                unused.append(
                    UnusedResource(
                        resource_id=node.id,
                        resource_type=str(node.resource_type),
                        resource_name=node.id,
                        region=node.region,
                        account_id=self.account_id,
                        reason=UnusedReason.STOPPED,
                        confidence=ConfidenceLevel.MEDIUM,
                        details="Database instance is stopped",
                        monthly_cost=self._estimate_rds_cost(node),
                        potential_savings=self._estimate_rds_cost(node) * 0.8,
                        recommendation="Delete if not needed (storage still incurs charges)",
                        action_items=[
                            "Review if database is still needed",
                            "Create final snapshot",
                            "Delete instance if not required",
                        ],
                        tags=node.tags,
                    )
                )
                continue

            # Check metrics for running instances
            if check_metrics and status == "available":
                metrics = await self._get_rds_metrics(node.id)
                if metrics:
                    connections_avg = metrics.get("connections_avg", 100)
                    if connections_avg < THRESHOLDS["rds_connections_low"]:
                        unused.append(
                            UnusedResource(
                                resource_id=node.id,
                                resource_type=str(node.resource_type),
                                resource_name=node.id,
                                region=node.region,
                                account_id=self.account_id,
                                reason=UnusedReason.NO_CONNECTIONS,
                                confidence=ConfidenceLevel.MEDIUM,
                                details=f"Average connections: {connections_avg:.1f}",
                                utilization_pct=connections_avg,
                                monthly_cost=self._estimate_rds_cost(node),
                                potential_savings=self._estimate_rds_cost(node),
                                recommendation="Investigate if database is still in use",
                                action_items=[
                                    "Check application connection strings",
                                    "Verify no scheduled jobs use this DB",
                                    "Consider deletion or snapshot",
                                ],
                                tags=node.tags,
                            )
                        )

        return unused

    async def _scan_elastic_ips(
        self,
        graph: GraphEngine,
    ) -> list[UnusedResource]:
        """Scan Elastic IPs for unused.

        Note: Currently no ELASTIC_IP ResourceType in the model.
        This is a placeholder for future implementation.
        """
        # ELASTIC_IP ResourceType not yet defined - return empty
        return []

    async def _scan_load_balancers(
        self,
        graph: GraphEngine,
        check_metrics: bool,
    ) -> list[UnusedResource]:
        """Scan Load Balancers for unused."""
        unused = []

        for node in graph.get_resources_by_type(ResourceType.LB):
            # Check if has targets
            target_groups = node.config.get("target_groups", [])

            if not target_groups:
                unused.append(
                    UnusedResource(
                        resource_id=node.id,
                        resource_type=str(node.resource_type),
                        resource_name=node.tags.get("Name", node.id),
                        region=node.region,
                        account_id=self.account_id,
                        reason=UnusedReason.ORPHANED,
                        confidence=ConfidenceLevel.HIGH,
                        details="Load balancer has no target groups",
                        monthly_cost=self._estimate_alb_cost(node),
                        potential_savings=self._estimate_alb_cost(node),
                        recommendation="Delete unused load balancer",
                        action_items=[
                            "Verify no services depend on this LB",
                            "Delete load balancer",
                        ],
                        tags=node.tags,
                    )
                )
                continue

            # Check metrics
            if check_metrics:
                metrics = await self._get_elb_metrics(node.id)
                if metrics:
                    request_count = metrics.get("request_count", float("inf"))
                    if request_count < THRESHOLDS["elb_requests_low"]:
                        unused.append(
                            UnusedResource(
                                resource_id=node.id,
                                resource_type=str(node.resource_type),
                                resource_name=node.tags.get("Name", node.id),
                                region=node.region,
                                account_id=self.account_id,
                                reason=UnusedReason.NO_TRAFFIC,
                                confidence=ConfidenceLevel.MEDIUM,
                                details=f"Only {request_count:.0f} requests in period",
                                monthly_cost=self._estimate_alb_cost(node),
                                potential_savings=self._estimate_alb_cost(node),
                                recommendation="Investigate low traffic or delete",
                                action_items=[
                                    "Check DNS records pointing to this LB",
                                    "Verify application is still needed",
                                    "Consider deletion if truly unused",
                                ],
                                tags=node.tags,
                            )
                        )

        return unused

    async def _scan_nat_gateways(
        self,
        graph: GraphEngine,
        check_metrics: bool,
    ) -> list[UnusedResource]:
        """Scan NAT Gateways for unused."""
        unused = []

        for node in graph.get_resources_by_type(ResourceType.NAT_GATEWAY):
            if check_metrics:
                metrics = await self._get_nat_metrics(node.id)
                if metrics:
                    bytes_total = metrics.get("bytes_total", float("inf"))
                    if bytes_total < THRESHOLDS["nat_gateway_bytes_low"]:
                        unused.append(
                            UnusedResource(
                                resource_id=node.id,
                                resource_type=str(node.resource_type),
                                resource_name=node.id,
                                region=node.region,
                                account_id=self.account_id,
                                reason=UnusedReason.ZERO_USAGE,
                                confidence=ConfidenceLevel.MEDIUM,
                                details=f"Only {bytes_total:.0f} bytes transferred",
                                monthly_cost=self._estimate_nat_cost(node),
                                potential_savings=self._estimate_nat_cost(node),
                                recommendation="Investigate if NAT is needed",
                                action_items=[
                                    "Check route tables for NAT usage",
                                    "Verify private subnets need NAT",
                                    "Delete if not required",
                                ],
                                tags=node.tags,
                            )
                        )

        return unused

    # Metric retrieval methods

    async def _get_ec2_metrics(self, instance_id: str) -> dict[str, float] | None:
        """Get EC2 CloudWatch metrics."""
        try:
            client = await self._get_client()
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)

            # Get CPU utilization
            response = await client.call(
                "cloudwatch",
                "get_metric_statistics",
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start_time.isoformat(),
                EndTime=end_time.isoformat(),
                Period=3600 * 24,  # Daily
                Statistics=["Average"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                cpu_avg = sum(d["Average"] for d in datapoints) / len(datapoints)
            else:
                cpu_avg = 0

            return {"cpu_avg": cpu_avg, "network_avg": 0}
        except Exception as e:
            logger.debug(f"Failed to get EC2 metrics for {instance_id}: {e}")
            return None

    async def _get_rds_metrics(self, db_id: str) -> dict[str, float] | None:
        """Get RDS CloudWatch metrics."""
        try:
            client = await self._get_client()
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)

            response = await client.call(
                "cloudwatch",
                "get_metric_statistics",
                Namespace="AWS/RDS",
                MetricName="DatabaseConnections",
                Dimensions=[{"Name": "DBInstanceIdentifier", "Value": db_id}],
                StartTime=start_time.isoformat(),
                EndTime=end_time.isoformat(),
                Period=3600 * 24,
                Statistics=["Average"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                connections_avg = sum(d["Average"] for d in datapoints) / len(datapoints)
            else:
                connections_avg = 0

            return {"connections_avg": connections_avg}
        except Exception as e:
            logger.debug(f"Failed to get RDS metrics for {db_id}: {e}")
            return None

    async def _get_elb_metrics(self, lb_id: str) -> dict[str, float] | None:
        """Get ELB CloudWatch metrics."""
        try:
            client = await self._get_client()
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)

            response = await client.call(
                "cloudwatch",
                "get_metric_statistics",
                Namespace="AWS/ApplicationELB",
                MetricName="RequestCount",
                Dimensions=[{"Name": "LoadBalancer", "Value": lb_id}],
                StartTime=start_time.isoformat(),
                EndTime=end_time.isoformat(),
                Period=3600 * 24,
                Statistics=["Sum"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                request_count = sum(d["Sum"] for d in datapoints)
            else:
                request_count = 0

            return {"request_count": request_count}
        except Exception as e:
            logger.debug(f"Failed to get ELB metrics for {lb_id}: {e}")
            return None

    async def _get_nat_metrics(self, nat_id: str) -> dict[str, float] | None:
        """Get NAT Gateway CloudWatch metrics."""
        try:
            client = await self._get_client()
            end_time = datetime.now()
            start_time = end_time - timedelta(days=self.lookback_days)

            response = await client.call(
                "cloudwatch",
                "get_metric_statistics",
                Namespace="AWS/NATGateway",
                MetricName="BytesOutToDestination",
                Dimensions=[{"Name": "NatGatewayId", "Value": nat_id}],
                StartTime=start_time.isoformat(),
                EndTime=end_time.isoformat(),
                Period=3600 * 24,
                Statistics=["Sum"],
            )

            datapoints = response.get("Datapoints", [])
            if datapoints:
                bytes_total = sum(d["Sum"] for d in datapoints)
            else:
                bytes_total = 0

            return {"bytes_total": bytes_total}
        except Exception as e:
            logger.debug(f"Failed to get NAT metrics for {nat_id}: {e}")
            return None

    # Cost estimation methods

    def _estimate_ec2_cost(self, node: ResourceNode) -> float:
        """Estimate monthly EC2 cost."""
        instance_type = node.config.get("instance_type", "t3.medium")
        # Simplified pricing - in real implementation, use pricing module
        hourly_rates = {
            "t3.micro": 0.0104,
            "t3.small": 0.0208,
            "t3.medium": 0.0416,
            "t3.large": 0.0832,
            "m5.large": 0.096,
            "m5.xlarge": 0.192,
        }
        hourly = hourly_rates.get(instance_type, 0.05)
        return hourly * 720  # 720 hours/month

    def _estimate_ebs_cost(self, node: ResourceNode) -> float:
        """Estimate monthly EBS cost."""
        size_gb: int = node.config.get("size", 100)
        volume_type: str = node.config.get("volume_type", "gp2")
        # Simplified pricing
        per_gb = {"gp2": 0.10, "gp3": 0.08, "io1": 0.125, "st1": 0.045}
        return float(size_gb * per_gb.get(volume_type, 0.10))

    def _estimate_rds_cost(self, node: ResourceNode) -> float:
        """Estimate monthly RDS cost."""
        instance_class = node.config.get("instance_class", "db.t3.medium")
        # Simplified pricing
        hourly_rates = {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.t3.large": 0.136,
            "db.m5.large": 0.171,
        }
        hourly = hourly_rates.get(instance_class, 0.10)
        return hourly * 720

    def _estimate_alb_cost(self, node: ResourceNode) -> float:
        """Estimate monthly ALB cost."""
        # Base ALB cost (~$16/month + LCU charges)
        return 16.20

    def _estimate_nat_cost(self, node: ResourceNode) -> float:
        """Estimate monthly NAT Gateway cost."""
        # NAT Gateway hourly cost (~$32/month + data processing)
        return 32.40

    def _days_since(self, timestamp: str | datetime) -> int:
        """Calculate days since a timestamp."""
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                return 0
        else:
            dt = timestamp

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        return (now - dt).days
