"""
Data Transfer Cost Analysis (P1-6).

Analyzes AWS data transfer costs including:
- Cross-AZ traffic detection
- NAT Gateway traffic analysis
- Cross-region transfer costs
- VPC Endpoint optimization suggestions
- Internet egress costs
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Any

from replimap.cost.pricing_engine import Currency


class TransferType(Enum):
    """Types of data transfer."""

    INTERNET_EGRESS = "internet_egress"
    INTERNET_INGRESS = "internet_ingress"
    CROSS_AZ = "cross_az"
    CROSS_REGION = "cross_region"
    VPC_PEERING = "vpc_peering"
    TRANSIT_GATEWAY = "transit_gateway"
    NAT_GATEWAY = "nat_gateway"
    VPC_ENDPOINT = "vpc_endpoint"
    DIRECT_CONNECT = "direct_connect"
    CLOUDFRONT = "cloudfront"
    S3_TRANSFER_ACCELERATION = "s3_transfer_acceleration"


class TrafficDirection(Enum):
    """Direction of traffic flow."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class TransferPath:
    """A data transfer path between resources."""

    source_id: str
    source_type: str
    source_region: str
    source_az: str

    destination_id: str
    destination_type: str
    destination_region: str
    destination_az: str

    transfer_type: TransferType
    direction: TrafficDirection

    # Traffic estimates (GB/month)
    estimated_gb_month: Decimal = Decimal("0")
    peak_gbps: Decimal = Decimal("0")

    # Metadata
    description: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    @property
    def is_cross_az(self) -> bool:
        """Check if this is cross-AZ traffic."""
        return (
            self.source_region == self.destination_region
            and self.source_az != self.destination_az
        )

    @property
    def is_cross_region(self) -> bool:
        """Check if this is cross-region traffic."""
        return self.source_region != self.destination_region

    @property
    def is_internet(self) -> bool:
        """Check if this involves internet transfer."""
        return self.transfer_type in (
            TransferType.INTERNET_EGRESS,
            TransferType.INTERNET_INGRESS,
        )


@dataclass
class TransferCost:
    """Cost breakdown for a transfer path."""

    path: TransferPath
    monthly_cost: Decimal
    currency: Currency

    # Rate details
    rate_per_gb: Decimal
    pricing_tier: str = "standard"

    # Breakdown
    data_transfer_cost: Decimal = Decimal("0")
    processing_cost: Decimal = Decimal("0")  # NAT, TGW processing fees
    hourly_cost: Decimal = Decimal("0")  # Fixed hourly fees

    # Optimization
    optimization_available: bool = False
    potential_savings: Decimal = Decimal("0")
    optimization_suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source": {
                "id": self.path.source_id,
                "type": self.path.source_type,
                "region": self.path.source_region,
                "az": self.path.source_az,
            },
            "destination": {
                "id": self.path.destination_id,
                "type": self.path.destination_type,
                "region": self.path.destination_region,
                "az": self.path.destination_az,
            },
            "transfer_type": self.path.transfer_type.value,
            "direction": self.path.direction.value,
            "data_gb_month": float(self.path.estimated_gb_month),
            "cost": {
                "monthly_total": float(self.monthly_cost),
                "currency": self.currency.value,
                "rate_per_gb": float(self.rate_per_gb),
                "data_transfer": float(self.data_transfer_cost),
                "processing": float(self.processing_cost),
                "hourly": float(self.hourly_cost),
            },
            "optimization": {
                "available": self.optimization_available,
                "potential_savings": float(self.potential_savings),
                "suggestion": self.optimization_suggestion,
            },
        }


@dataclass
class TransferReport:
    """Complete data transfer cost report."""

    region: str
    currency: Currency

    # All transfer paths
    paths: list[TransferPath] = field(default_factory=list)
    costs: list[TransferCost] = field(default_factory=list)

    # Totals
    total_monthly_cost: Decimal = Decimal("0")
    total_data_gb: Decimal = Decimal("0")

    # Breakdown by type
    cost_by_type: dict[TransferType, Decimal] = field(default_factory=dict)

    # Optimization summary
    total_potential_savings: Decimal = Decimal("0")
    optimization_count: int = 0

    # Warnings
    warnings: list[str] = field(default_factory=list)

    def add_cost(self, cost: TransferCost) -> None:
        """Add a transfer cost to the report."""
        self.costs.append(cost)
        self.total_monthly_cost += cost.monthly_cost
        self.total_data_gb += cost.path.estimated_gb_month

        # Update type breakdown
        transfer_type = cost.path.transfer_type
        if transfer_type not in self.cost_by_type:
            self.cost_by_type[transfer_type] = Decimal("0")
        self.cost_by_type[transfer_type] += cost.monthly_cost

        # Track optimizations
        if cost.optimization_available:
            self.total_potential_savings += cost.potential_savings
            self.optimization_count += 1

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "currency": self.currency.value,
            "summary": {
                "total_monthly_cost": float(self.total_monthly_cost),
                "total_data_gb": float(self.total_data_gb),
                "path_count": len(self.paths),
            },
            "cost_by_type": {k.value: float(v) for k, v in self.cost_by_type.items()},
            "optimization": {
                "total_potential_savings": float(self.total_potential_savings),
                "optimization_count": self.optimization_count,
            },
            "costs": [c.to_dict() for c in self.costs],
            "warnings": self.warnings,
        }


class TransferPricingTiers:
    """Data transfer pricing tiers."""

    # Internet egress pricing tiers (USD, per GB)
    # Tuple: (cumulative GB threshold, rate per GB)
    INTERNET_EGRESS_TIERS: dict[str, list[tuple[int, Decimal]]] = {
        "us-east-1": [
            (10240, Decimal("0.09")),  # First 10 TB
            (51200, Decimal("0.085")),  # Next 40 TB (cumulative 50TB)
            (153600, Decimal("0.07")),  # Next 100 TB (cumulative 150TB)
            (999999999, Decimal("0.05")),  # Over 150 TB
        ],
        "ap-southeast-2": [
            (10240, Decimal("0.114")),  # First 10 TB
            (51200, Decimal("0.098")),  # Next 40 TB
            (153600, Decimal("0.094")),  # Next 100 TB
            (999999999, Decimal("0.090")),  # Over 150 TB
        ],
    }

    # Cross-AZ pricing (per GB, bidirectional)
    CROSS_AZ_RATES: dict[str, Decimal] = {
        "default": Decimal("0.01"),
        "ap-southeast-2": Decimal("0.01"),  # Sydney
        "ap-southeast-4": Decimal("0.01"),  # Melbourne
    }

    # NAT Gateway pricing
    NAT_GATEWAY_RATES: dict[str, dict[str, Decimal]] = {
        "default": {
            "hourly": Decimal("0.045"),
            "per_gb": Decimal("0.045"),
        },
        "ap-southeast-2": {
            "hourly": Decimal("0.045"),
            "per_gb": Decimal("0.045"),
        },
    }

    # VPC Endpoint pricing
    VPC_ENDPOINT_RATES: dict[str, dict[str, Decimal]] = {
        "default": {
            "hourly": Decimal("0.01"),
            "per_gb": Decimal("0.01"),
        },
        "ap-southeast-2": {
            "hourly": Decimal("0.01"),
            "per_gb": Decimal("0.01"),
        },
    }

    # Transit Gateway pricing
    TRANSIT_GATEWAY_RATES: dict[str, dict[str, Decimal]] = {
        "default": {
            "hourly": Decimal("0.05"),
            "per_gb": Decimal("0.02"),
        },
        "ap-southeast-2": {
            "hourly": Decimal("0.05"),
            "per_gb": Decimal("0.02"),
        },
    }

    # Cross-region data transfer
    CROSS_REGION_RATES: dict[tuple[str, str], Decimal] = {
        # US to other regions
        ("us-east-1", "us-west-2"): Decimal("0.02"),
        ("us-east-1", "eu-west-1"): Decimal("0.02"),
        ("us-east-1", "ap-southeast-2"): Decimal("0.02"),
        # Within AU
        ("ap-southeast-2", "ap-southeast-4"): Decimal("0.02"),
        # Default
        ("default", "default"): Decimal("0.02"),
    }

    @classmethod
    def get_internet_egress_rate(cls, region: str, gb_month: Decimal) -> Decimal:
        """Get internet egress rate for given usage."""
        tiers = cls.INTERNET_EGRESS_TIERS.get(
            region, cls.INTERNET_EGRESS_TIERS.get("us-east-1", [])
        )

        remaining = float(gb_month)
        total_cost = Decimal("0")

        prev_limit = 0
        for limit, rate in tiers:
            if remaining <= 0:
                break

            tier_gb = min(remaining, limit - prev_limit)
            total_cost += Decimal(str(tier_gb)) * rate
            remaining -= tier_gb
            prev_limit = limit

        if gb_month > 0:
            return total_cost / gb_month
        return Decimal("0")

    @classmethod
    def get_cross_az_rate(cls, region: str) -> Decimal:
        """Get cross-AZ transfer rate."""
        return cls.CROSS_AZ_RATES.get(region, cls.CROSS_AZ_RATES["default"])

    @classmethod
    def get_nat_rates(cls, region: str) -> dict[str, Decimal]:
        """Get NAT Gateway rates."""
        return cls.NAT_GATEWAY_RATES.get(region, cls.NAT_GATEWAY_RATES["default"])

    @classmethod
    def get_vpc_endpoint_rates(cls, region: str) -> dict[str, Decimal]:
        """Get VPC Endpoint rates."""
        return cls.VPC_ENDPOINT_RATES.get(region, cls.VPC_ENDPOINT_RATES["default"])

    @classmethod
    def get_cross_region_rate(cls, source: str, destination: str) -> Decimal:
        """Get cross-region transfer rate."""
        key = (source, destination)
        if key in cls.CROSS_REGION_RATES:
            return cls.CROSS_REGION_RATES[key]

        # Try reverse
        key = (destination, source)
        if key in cls.CROSS_REGION_RATES:
            return cls.CROSS_REGION_RATES[key]

        return cls.CROSS_REGION_RATES[("default", "default")]


@dataclass
class TransferOptimization:
    """An optimization recommendation."""

    description: str
    estimated_savings: Decimal
    category: str = "general"


@dataclass
class GraphTransferReport:
    """Transfer report generated from analyzing a GraphEngine."""

    region: str
    total_paths: int = 0
    total_monthly_cost: float = 0.0
    cross_az_paths: list[TransferPath] = field(default_factory=list)
    nat_gateway_paths: list[TransferPath] = field(default_factory=list)
    internet_egress_paths: list[TransferPath] = field(default_factory=list)
    optimizations: list[TransferOptimization] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "total_paths": self.total_paths,
            "total_monthly_cost": self.total_monthly_cost,
            "cross_az_paths": len(self.cross_az_paths),
            "nat_gateway_paths": len(self.nat_gateway_paths),
            "internet_egress_paths": len(self.internet_egress_paths),
            "optimizations": [
                {
                    "description": o.description,
                    "estimated_savings": float(o.estimated_savings),
                }
                for o in self.optimizations
            ],
        }


class DataTransferAnalyzer:
    """
    Analyzes data transfer patterns and costs.

    Detects cross-AZ, cross-region, and internet transfer
    and provides optimization recommendations.
    """

    def __init__(
        self,
        session: Any = None,
        region: str = "us-east-1",
        currency: Currency = Currency.USD,
    ) -> None:
        """
        Initialize analyzer.

        Args:
            session: AWS session (optional, for future CloudWatch metrics)
            region: Primary AWS region
            currency: Output currency
        """
        self.session = session
        self.region = region
        self.currency = currency
        self.pricing = TransferPricingTiers()

    def analyze_paths(
        self,
        paths: list[TransferPath],
    ) -> TransferReport:
        """
        Analyze transfer paths and generate cost report.

        Args:
            paths: List of transfer paths to analyze

        Returns:
            TransferReport with costs and optimizations
        """
        report = TransferReport(
            region=self.region,
            currency=self.currency,
            paths=paths,
        )

        for path in paths:
            cost = self._calculate_path_cost(path)
            report.add_cost(cost)

        # Add warnings for high-cost patterns
        self._add_warnings(report)

        return report

    def detect_cross_az_traffic(
        self,
        resources: list[dict[str, Any]],
        connections: list[dict[str, Any]],
    ) -> list[TransferPath]:
        """
        Detect cross-AZ traffic patterns from resources and connections.

        Args:
            resources: List of resource configurations
            connections: List of connections between resources

        Returns:
            List of detected cross-AZ transfer paths
        """
        paths: list[TransferPath] = []

        # Build resource lookup
        resource_map = {r["id"]: r for r in resources}

        for conn in connections:
            source = resource_map.get(conn.get("source_id"))
            dest = resource_map.get(conn.get("destination_id"))

            if not source or not dest:
                continue

            source_az = source.get("availability_zone", "")
            dest_az = dest.get("availability_zone", "")
            source_region = source.get("region", self.region)
            dest_region = dest.get("region", self.region)

            # Check for cross-AZ within same region
            if source_region == dest_region and source_az != dest_az:
                path = TransferPath(
                    source_id=source["id"],
                    source_type=source.get("type", "unknown"),
                    source_region=source_region,
                    source_az=source_az,
                    destination_id=dest["id"],
                    destination_type=dest.get("type", "unknown"),
                    destination_region=dest_region,
                    destination_az=dest_az,
                    transfer_type=TransferType.CROSS_AZ,
                    direction=TrafficDirection.BIDIRECTIONAL,
                    estimated_gb_month=Decimal(str(conn.get("estimated_gb_month", 10))),
                    description=f"Cross-AZ traffic: {source_az} -> {dest_az}",
                )
                paths.append(path)

        return paths

    def analyze_nat_gateway(
        self,
        nat_config: dict[str, Any],
        estimated_gb_month: Decimal = Decimal("100"),
    ) -> TransferCost:
        """
        Analyze NAT Gateway costs.

        Args:
            nat_config: NAT Gateway configuration
            estimated_gb_month: Estimated monthly data transfer

        Returns:
            TransferCost with breakdown and optimization suggestions
        """
        nat_id = nat_config.get("id", "unknown")
        region = nat_config.get("region", self.region)
        az = nat_config.get("availability_zone", "")

        path = TransferPath(
            source_id="private_subnet",
            source_type="aws_subnet",
            source_region=region,
            source_az=az,
            destination_id="internet",
            destination_type="internet",
            destination_region="",
            destination_az="",
            transfer_type=TransferType.NAT_GATEWAY,
            direction=TrafficDirection.OUTBOUND,
            estimated_gb_month=estimated_gb_month,
            description=f"NAT Gateway: {nat_id}",
        )

        rates = self.pricing.get_nat_rates(region)

        # Hourly cost (730 hours/month)
        hourly_cost = rates["hourly"] * Decimal("730")

        # Data processing cost
        data_cost = estimated_gb_month * rates["per_gb"]

        total = hourly_cost + data_cost

        # Check for VPC Endpoint optimization
        optimization_available = False
        potential_savings = Decimal("0")
        suggestion = ""

        # If significant S3/DynamoDB traffic, suggest VPC endpoints
        if estimated_gb_month > Decimal("100"):
            endpoint_rates = self.pricing.get_vpc_endpoint_rates(region)
            endpoint_cost = (
                endpoint_rates["hourly"] * Decimal("730")
                + estimated_gb_month * endpoint_rates["per_gb"]
            )

            if endpoint_cost < total:
                optimization_available = True
                potential_savings = total - endpoint_cost
                suggestion = (
                    f"Consider VPC Endpoints for S3/DynamoDB to save "
                    f"${potential_savings:.2f}/month"
                )

        return TransferCost(
            path=path,
            monthly_cost=total,
            currency=self.currency,
            rate_per_gb=rates["per_gb"],
            data_transfer_cost=data_cost,
            processing_cost=Decimal("0"),
            hourly_cost=hourly_cost,
            optimization_available=optimization_available,
            potential_savings=potential_savings,
            optimization_suggestion=suggestion,
        )

    def analyze_internet_egress(
        self,
        resource_id: str,
        resource_type: str,
        region: str,
        estimated_gb_month: Decimal,
    ) -> TransferCost:
        """
        Analyze internet egress costs.

        Args:
            resource_id: Source resource ID
            resource_type: Source resource type
            region: AWS region
            estimated_gb_month: Estimated monthly egress

        Returns:
            TransferCost with tiered pricing
        """
        path = TransferPath(
            source_id=resource_id,
            source_type=resource_type,
            source_region=region,
            source_az="",
            destination_id="internet",
            destination_type="internet",
            destination_region="",
            destination_az="",
            transfer_type=TransferType.INTERNET_EGRESS,
            direction=TrafficDirection.OUTBOUND,
            estimated_gb_month=estimated_gb_month,
            description="Internet egress",
        )

        rate = self.pricing.get_internet_egress_rate(region, estimated_gb_month)
        total = estimated_gb_month * rate

        # CloudFront optimization
        optimization_available = False
        potential_savings = Decimal("0")
        suggestion = ""

        if estimated_gb_month > Decimal("1000"):
            # CloudFront typically saves 10-40% on data transfer
            cf_savings = total * Decimal("0.25")  # Estimate 25% savings
            optimization_available = True
            potential_savings = cf_savings
            suggestion = (
                f"Consider CloudFront for caching to save "
                f"~${cf_savings:.2f}/month on data transfer"
            )

        return TransferCost(
            path=path,
            monthly_cost=total,
            currency=self.currency,
            rate_per_gb=rate,
            data_transfer_cost=total,
            optimization_available=optimization_available,
            potential_savings=potential_savings,
            optimization_suggestion=suggestion,
        )

    def analyze_cross_region(
        self,
        source_resource: dict[str, Any],
        dest_resource: dict[str, Any],
        estimated_gb_month: Decimal,
    ) -> TransferCost:
        """
        Analyze cross-region transfer costs.

        Args:
            source_resource: Source resource config
            dest_resource: Destination resource config
            estimated_gb_month: Estimated monthly transfer

        Returns:
            TransferCost with cross-region pricing
        """
        source_region = source_resource.get("region", self.region)
        dest_region = dest_resource.get("region", self.region)

        path = TransferPath(
            source_id=source_resource.get("id", "unknown"),
            source_type=source_resource.get("type", "unknown"),
            source_region=source_region,
            source_az=source_resource.get("availability_zone", ""),
            destination_id=dest_resource.get("id", "unknown"),
            destination_type=dest_resource.get("type", "unknown"),
            destination_region=dest_region,
            destination_az=dest_resource.get("availability_zone", ""),
            transfer_type=TransferType.CROSS_REGION,
            direction=TrafficDirection.OUTBOUND,
            estimated_gb_month=estimated_gb_month,
            description=f"Cross-region: {source_region} -> {dest_region}",
        )

        rate = self.pricing.get_cross_region_rate(source_region, dest_region)
        total = estimated_gb_month * rate

        return TransferCost(
            path=path,
            monthly_cost=total,
            currency=self.currency,
            rate_per_gb=rate,
            data_transfer_cost=total,
        )

    def get_vpc_endpoint_recommendation(
        self,
        nat_monthly_cost: Decimal,
        service: str = "s3",
        estimated_gb_month: Decimal = Decimal("100"),
    ) -> dict[str, Any]:
        """
        Get VPC Endpoint recommendation.

        Args:
            nat_monthly_cost: Current NAT Gateway monthly cost
            service: AWS service (s3, dynamodb, etc.)
            estimated_gb_month: Estimated monthly traffic

        Returns:
            Recommendation with cost comparison
        """
        rates = self.pricing.get_vpc_endpoint_rates(self.region)

        # Gateway endpoints (S3, DynamoDB) are free for data transfer
        if service in ("s3", "dynamodb"):
            endpoint_cost = Decimal("0")
            savings = nat_monthly_cost
            recommendation = (
                f"Use Gateway VPC Endpoint for {service.upper()} - "
                f"FREE data transfer, save ${savings:.2f}/month"
            )
        else:
            # Interface endpoints have hourly + data costs
            hourly = rates["hourly"] * Decimal("730")
            data = estimated_gb_month * rates["per_gb"]
            endpoint_cost = hourly + data
            savings = (
                nat_monthly_cost - endpoint_cost
                if nat_monthly_cost > endpoint_cost
                else Decimal("0")
            )
            recommendation = (
                f"Use Interface VPC Endpoint for {service} - "
                f"${endpoint_cost:.2f}/month vs ${nat_monthly_cost:.2f}/month"
            )

        return {
            "service": service,
            "current_cost": float(nat_monthly_cost),
            "endpoint_cost": float(endpoint_cost),
            "monthly_savings": float(savings),
            "recommendation": recommendation,
            "worthwhile": savings > Decimal("10"),  # Minimum $10 savings
        }

    def _calculate_path_cost(self, path: TransferPath) -> TransferCost:
        """Calculate cost for a single transfer path."""
        if path.transfer_type == TransferType.CROSS_AZ:
            rate = self.pricing.get_cross_az_rate(path.source_region)
            # Cross-AZ is charged both directions
            total = path.estimated_gb_month * rate * Decimal("2")

            return TransferCost(
                path=path,
                monthly_cost=total,
                currency=self.currency,
                rate_per_gb=rate,
                data_transfer_cost=total,
                optimization_available=True,
                potential_savings=total,
                optimization_suggestion=(
                    "Consider placing resources in same AZ to eliminate "
                    f"${total:.2f}/month cross-AZ transfer cost"
                ),
            )

        elif path.transfer_type == TransferType.NAT_GATEWAY:
            return self.analyze_nat_gateway(
                {"id": path.source_id, "region": path.source_region},
                path.estimated_gb_month,
            )

        elif path.transfer_type == TransferType.INTERNET_EGRESS:
            return self.analyze_internet_egress(
                path.source_id,
                path.source_type,
                path.source_region,
                path.estimated_gb_month,
            )

        elif path.transfer_type == TransferType.CROSS_REGION:
            rate = self.pricing.get_cross_region_rate(
                path.source_region, path.destination_region
            )
            total = path.estimated_gb_month * rate

            return TransferCost(
                path=path,
                monthly_cost=total,
                currency=self.currency,
                rate_per_gb=rate,
                data_transfer_cost=total,
            )

        else:
            # Default: minimal cost
            return TransferCost(
                path=path,
                monthly_cost=Decimal("0"),
                currency=self.currency,
                rate_per_gb=Decimal("0"),
            )

    def _add_warnings(self, report: TransferReport) -> None:
        """Add warnings for concerning patterns."""
        # High cross-AZ costs
        cross_az_cost = report.cost_by_type.get(TransferType.CROSS_AZ, Decimal("0"))
        if cross_az_cost > Decimal("100"):
            report.warnings.append(
                f"High cross-AZ transfer costs: ${cross_az_cost:.2f}/month. "
                "Consider consolidating resources to same AZ."
            )

        # High NAT costs
        nat_cost = report.cost_by_type.get(TransferType.NAT_GATEWAY, Decimal("0"))
        if nat_cost > Decimal("500"):
            report.warnings.append(
                f"High NAT Gateway costs: ${nat_cost:.2f}/month. "
                "Consider VPC Endpoints for S3/DynamoDB traffic."
            )

        # High internet egress
        egress_cost = report.cost_by_type.get(
            TransferType.INTERNET_EGRESS, Decimal("0")
        )
        if egress_cost > Decimal("1000"):
            report.warnings.append(
                f"High internet egress costs: ${egress_cost:.2f}/month. "
                "Consider CloudFront or S3 Transfer Acceleration."
            )

        # Cross-region transfers
        cross_region_cost = report.cost_by_type.get(
            TransferType.CROSS_REGION, Decimal("0")
        )
        if cross_region_cost > Decimal("200"):
            report.warnings.append(
                f"Cross-region transfer costs: ${cross_region_cost:.2f}/month. "
                "Verify this traffic is necessary."
            )

    def analyze_from_graph(self, graph: Any) -> GraphTransferReport:
        """
        Analyze data transfer patterns from a GraphEngine.

        Args:
            graph: GraphEngine with resource inventory

        Returns:
            GraphTransferReport with transfer analysis
        """
        from replimap.core.models import ResourceType

        report = GraphTransferReport(region=self.region)
        total_cost = Decimal("0")

        # Build resource lookup for cross-AZ detection
        resources_by_id: dict[str, dict[str, Any]] = {}
        az_groups: dict[str, list[str]] = {}  # AZ -> resource IDs

        for resource in graph.get_all_resources():
            az = resource.config.get("availability_zone", "")
            resource_data = {
                "id": resource.id,
                "type": str(resource.resource_type),
                "region": resource.region,
                "availability_zone": az,
                "config": resource.config,
            }
            resources_by_id[resource.id] = resource_data

            if az:
                if az not in az_groups:
                    az_groups[az] = []
                az_groups[az].append(resource.id)

        # Detect cross-AZ traffic from dependencies
        connections = []
        for resource in graph.get_all_resources():
            for dep_id in resource.dependencies:
                if dep_id in resources_by_id:
                    connections.append(
                        {
                            "source_id": resource.id,
                            "destination_id": dep_id,
                            "estimated_gb_month": 10,  # Default estimate
                        }
                    )

        cross_az_paths = self.detect_cross_az_traffic(
            list(resources_by_id.values()), connections
        )
        report.cross_az_paths = cross_az_paths

        # Calculate cross-AZ costs
        for path in cross_az_paths:
            rate = self.pricing.get_cross_az_rate(path.source_region)
            cost = path.estimated_gb_month * rate * Decimal("2")  # Bidirectional
            total_cost += cost

        # Analyze NAT Gateways
        for resource in graph.get_resources_by_type(ResourceType.NAT_GATEWAY):
            nat_path = TransferPath(
                source_id=resource.id,
                source_type="aws_nat_gateway",
                source_region=resource.region,
                source_az=resource.config.get("availability_zone", ""),
                destination_id="internet",
                destination_type="internet",
                destination_region="",
                destination_az="",
                transfer_type=TransferType.NAT_GATEWAY,
                direction=TrafficDirection.OUTBOUND,
                estimated_gb_month=Decimal("100"),  # Default estimate
                description=f"NAT Gateway: {resource.id}",
            )
            report.nat_gateway_paths.append(nat_path)

            # Calculate NAT cost
            rates = self.pricing.get_nat_rates(resource.region)
            hourly_cost = rates["hourly"] * Decimal("730")
            data_cost = Decimal("100") * rates["per_gb"]
            total_cost += hourly_cost + data_cost

            # Add optimization suggestion
            report.optimizations.append(
                TransferOptimization(
                    description=f"Consider VPC Endpoints for S3/DynamoDB traffic via {resource.id}",
                    estimated_savings=data_cost * Decimal("0.5"),
                    category="nat_gateway",
                )
            )

        report.total_paths = len(cross_az_paths) + len(report.nat_gateway_paths)
        report.total_monthly_cost = float(total_cost)

        return report
