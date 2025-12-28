"""
General Pricing Engine (P1-4).

Provides an extensible pricing architecture supporting:
- Multiple regions with accurate pricing
- Multiple currencies (USD, AUD, EUR, etc.)
- Multiple pricing units (hourly, monthly, per-GB)
- Enterprise discounts (EDP, PPA)
- Reserved instance and Savings Plans awareness
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, ClassVar, Protocol, runtime_checkable

from replimap.cost.models import CostCategory, PricingTier


class Currency(Enum):
    """Supported currencies."""

    USD = "USD"
    AUD = "AUD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    SGD = "SGD"
    INR = "INR"
    BRL = "BRL"
    CAD = "CAD"


class PricingUnit(Enum):
    """Standard pricing units."""

    HOURLY = "hourly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    PER_GB = "per_gb"
    PER_GB_MONTH = "per_gb_month"
    PER_REQUEST = "per_request"
    PER_MILLION_REQUESTS = "per_million_requests"
    PER_GB_TRANSFERRED = "per_gb_transferred"
    PER_IOPS = "per_iops"
    PER_LCU_HOUR = "per_lcu_hour"


@dataclass
class PricePoint:
    """A single price point with full metadata."""

    amount: Decimal
    currency: Currency
    unit: PricingUnit
    region: str
    service: str
    resource_type: str
    sku: str = ""
    description: str = ""
    effective_date: str = ""
    tier: PricingTier = PricingTier.ON_DEMAND

    # Tax information
    includes_tax: bool = False
    tax_rate: Decimal = Decimal("0")

    def to_monthly(self) -> Decimal:
        """Convert to monthly cost."""
        if self.unit == PricingUnit.HOURLY:
            return self.amount * Decimal("730")  # Average hours per month
        elif self.unit == PricingUnit.YEARLY:
            return self.amount / Decimal("12")
        elif self.unit == PricingUnit.MONTHLY:
            return self.amount
        else:
            return self.amount  # Other units need context

    def to_hourly(self) -> Decimal:
        """Convert to hourly cost."""
        if self.unit == PricingUnit.MONTHLY:
            return self.amount / Decimal("730")
        elif self.unit == PricingUnit.YEARLY:
            return self.amount / Decimal("8760")
        elif self.unit == PricingUnit.HOURLY:
            return self.amount
        else:
            return self.amount

    def with_tax(self, tax_rate: Decimal | None = None) -> Decimal:
        """Get amount with tax applied."""
        if self.includes_tax:
            return self.amount
        rate = tax_rate if tax_rate is not None else self.tax_rate
        return self.amount * (Decimal("1") + rate)

    def convert_currency(
        self,
        target: Currency,
        exchange_rates: dict[str, Decimal],
    ) -> PricePoint:
        """Convert to different currency."""
        if self.currency == target:
            return self

        # Get exchange rate (relative to USD)
        from_rate = exchange_rates.get(self.currency.value, Decimal("1"))
        to_rate = exchange_rates.get(target.value, Decimal("1"))

        # Convert: amount -> USD -> target
        usd_amount = self.amount / from_rate
        new_amount = usd_amount * to_rate

        return PricePoint(
            amount=new_amount.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP),
            currency=target,
            unit=self.unit,
            region=self.region,
            service=self.service,
            resource_type=self.resource_type,
            sku=self.sku,
            description=self.description,
            effective_date=self.effective_date,
            tier=self.tier,
            includes_tax=self.includes_tax,
            tax_rate=self.tax_rate,
        )


@dataclass
class ResourceCost:
    """Calculated cost for a resource."""

    resource_id: str
    resource_type: str
    resource_name: str
    region: str

    # Cost breakdown
    monthly_cost: Decimal
    currency: Currency
    category: CostCategory

    # Components
    compute_cost: Decimal = Decimal("0")
    storage_cost: Decimal = Decimal("0")
    network_cost: Decimal = Decimal("0")
    license_cost: Decimal = Decimal("0")
    other_cost: Decimal = Decimal("0")

    # Tax
    pre_tax_cost: Decimal = Decimal("0")
    tax_amount: Decimal = Decimal("0")
    tax_rate: Decimal = Decimal("0")

    # Metadata
    pricing_tier: PricingTier = PricingTier.ON_DEMAND
    notes: list[str] = field(default_factory=list)
    price_points: list[PricePoint] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        if self.pre_tax_cost == Decimal("0"):
            self.pre_tax_cost = self.monthly_cost
        if self.tax_rate > Decimal("0") and self.tax_amount == Decimal("0"):
            self.tax_amount = self.pre_tax_cost * self.tax_rate

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "monthly_cost": float(self.monthly_cost),
            "currency": self.currency.value,
            "category": self.category.value,
            "breakdown": {
                "compute": float(self.compute_cost),
                "storage": float(self.storage_cost),
                "network": float(self.network_cost),
                "license": float(self.license_cost),
                "other": float(self.other_cost),
            },
            "tax": {
                "pre_tax": float(self.pre_tax_cost),
                "tax_amount": float(self.tax_amount),
                "tax_rate": float(self.tax_rate),
            },
            "pricing_tier": self.pricing_tier.value,
            "notes": self.notes,
        }


@runtime_checkable
class PricingProvider(Protocol):
    """Protocol for pricing data providers."""

    def get_price(
        self,
        service: str,
        resource_type: str,
        region: str,
        **kwargs: Any,
    ) -> PricePoint | None:
        """Get price for a resource type."""
        ...

    def list_regions(self) -> list[str]:
        """List supported regions."""
        ...

    def list_services(self) -> list[str]:
        """List supported services."""
        ...


class BasePricingEngine(ABC):
    """
    Abstract base class for pricing engines.

    Subclass this to implement region-specific pricing.
    """

    # Class-level registry of pricing engines
    _registry: ClassVar[dict[str, type[BasePricingEngine]]] = {}

    # Default exchange rates (relative to USD)
    DEFAULT_EXCHANGE_RATES: ClassVar[dict[str, Decimal]] = {
        "USD": Decimal("1.0"),
        "AUD": Decimal("1.55"),
        "EUR": Decimal("0.92"),
        "GBP": Decimal("0.79"),
        "JPY": Decimal("149.0"),
        "SGD": Decimal("1.34"),
        "INR": Decimal("83.0"),
        "BRL": Decimal("4.97"),
        "CAD": Decimal("1.36"),
    }

    def __init__(
        self,
        region: str,
        currency: Currency = Currency.USD,
        exchange_rates: dict[str, Decimal] | None = None,
    ) -> None:
        """
        Initialize pricing engine.

        Args:
            region: AWS region code
            currency: Output currency
            exchange_rates: Custom exchange rates (optional)
        """
        self.region = region
        self.currency = currency
        self.exchange_rates = exchange_rates or self.DEFAULT_EXCHANGE_RATES.copy()
        self._price_cache: dict[str, PricePoint] = {}

    @classmethod
    def register(cls, region_pattern: str) -> Any:
        """Decorator to register a pricing engine for a region pattern."""

        def decorator(engine_cls: type[BasePricingEngine]) -> type[BasePricingEngine]:
            cls._registry[region_pattern] = engine_cls
            return engine_cls

        return decorator

    @classmethod
    def for_region(
        cls,
        region: str,
        currency: Currency = Currency.USD,
        **kwargs: Any,
    ) -> BasePricingEngine:
        """
        Get appropriate pricing engine for a region.

        Args:
            region: AWS region code
            currency: Output currency
            **kwargs: Additional arguments for engine

        Returns:
            Pricing engine instance
        """
        # Check for exact match
        if region in cls._registry:
            return cls._registry[region](region, currency, **kwargs)

        # Check for pattern match (e.g., "ap-southeast-*" for Australia)
        for pattern, engine_cls in cls._registry.items():
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if region.startswith(prefix):
                    return engine_cls(region, currency, **kwargs)

        # Fall back to default engine
        from replimap.cost.pricing_engine import DefaultPricingEngine

        return DefaultPricingEngine(region, currency, **kwargs)

    @abstractmethod
    def get_ec2_price(
        self,
        instance_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
        os: str = "Linux",
    ) -> PricePoint:
        """Get EC2 instance price."""
        ...

    @abstractmethod
    def get_rds_price(
        self,
        instance_class: str,
        engine: str = "mysql",
        multi_az: bool = False,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get RDS instance price."""
        ...

    @abstractmethod
    def get_storage_price(
        self,
        storage_type: str,
        size_gb: float = 1.0,
    ) -> PricePoint:
        """Get storage price (EBS, S3, etc.)."""
        ...

    @abstractmethod
    def get_network_price(
        self,
        service: str,
        transfer_type: str = "out",
    ) -> PricePoint:
        """Get network/data transfer price."""
        ...

    def calculate_resource_cost(
        self,
        resource_type: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """
        Calculate total cost for a resource.

        Args:
            resource_type: AWS resource type
            config: Resource configuration

        Returns:
            ResourceCost with full breakdown
        """
        resource_id = config.get("id", "unknown")
        resource_name = config.get("name", resource_id)

        # Dispatch to appropriate calculator
        if resource_type == "aws_instance":
            return self._calculate_ec2_cost(resource_id, resource_name, config)
        elif resource_type == "aws_db_instance":
            return self._calculate_rds_cost(resource_id, resource_name, config)
        elif resource_type == "aws_s3_bucket":
            return self._calculate_s3_cost(resource_id, resource_name, config)
        elif resource_type == "aws_nat_gateway":
            return self._calculate_nat_cost(resource_id, resource_name, config)
        elif resource_type in ("aws_lb", "aws_alb"):
            return self._calculate_lb_cost(resource_id, resource_name, config)
        elif resource_type == "aws_ebs_volume":
            return self._calculate_ebs_cost(resource_id, resource_name, config)
        elif resource_type == "aws_elasticache_cluster":
            return self._calculate_elasticache_cost(resource_id, resource_name, config)
        else:
            return self._calculate_unknown_cost(
                resource_id, resource_name, resource_type, config
            )

    def _calculate_ec2_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate EC2 instance cost."""
        instance_type = config.get("instance_type", "t3.medium")
        tier = PricingTier(config.get("pricing_tier", "ON_DEMAND"))

        price = self.get_ec2_price(instance_type, tier)
        monthly = price.to_monthly()

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_instance",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=monthly,
            currency=self.currency,
            category=CostCategory.COMPUTE,
            compute_cost=monthly,
            pricing_tier=tier,
            price_points=[price],
        )

    def _calculate_rds_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate RDS instance cost."""
        instance_class = config.get("instance_class", "db.t3.medium")
        engine = config.get("engine", "mysql")
        multi_az = config.get("multi_az", False)
        storage_gb = config.get("allocated_storage", 20)
        storage_type = config.get("storage_type", "gp2")
        tier = PricingTier(config.get("pricing_tier", "ON_DEMAND"))

        # Instance cost
        instance_price = self.get_rds_price(instance_class, engine, multi_az, tier)
        instance_monthly = instance_price.to_monthly()

        # Storage cost
        storage_price = self.get_storage_price(f"rds_{storage_type}", storage_gb)
        storage_monthly = storage_price.amount * Decimal(str(storage_gb))

        total = instance_monthly + storage_monthly

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_db_instance",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=total,
            currency=self.currency,
            category=CostCategory.DATABASE,
            compute_cost=instance_monthly,
            storage_cost=storage_monthly,
            pricing_tier=tier,
            price_points=[instance_price, storage_price],
            notes=[f"Engine: {engine}", f"Multi-AZ: {multi_az}"],
        )

    def _calculate_s3_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate S3 bucket cost."""
        storage_gb = config.get("size_gb", 0)
        storage_class = config.get("storage_class", "STANDARD")

        price = self.get_storage_price(f"s3_{storage_class.lower()}", storage_gb)
        monthly = price.amount * Decimal(str(storage_gb))

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_s3_bucket",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=monthly,
            currency=self.currency,
            category=CostCategory.STORAGE,
            storage_cost=monthly,
            price_points=[price],
            notes=[f"Storage class: {storage_class}", f"Size: {storage_gb} GB"],
        )

    def _calculate_nat_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate NAT Gateway cost."""
        data_gb = config.get("data_processed_gb", 100)

        # Hourly cost
        hourly_price = self.get_network_price("nat_gateway", "hourly")
        hourly_monthly = hourly_price.to_monthly()

        # Data processing cost
        data_price = self.get_network_price("nat_gateway", "per_gb")
        data_monthly = data_price.amount * Decimal(str(data_gb))

        total = hourly_monthly + data_monthly

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_nat_gateway",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=total,
            currency=self.currency,
            category=CostCategory.NETWORK,
            network_cost=total,
            price_points=[hourly_price, data_price],
            notes=[f"Data processed: {data_gb} GB/month"],
        )

    def _calculate_lb_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate Load Balancer cost."""
        price = self.get_network_price("alb", "hourly")
        monthly = price.to_monthly()

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_lb",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=monthly,
            currency=self.currency,
            category=CostCategory.NETWORK,
            network_cost=monthly,
            price_points=[price],
        )

    def _calculate_ebs_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate EBS volume cost."""
        size_gb = config.get("size", 100)
        volume_type = config.get("volume_type", "gp2")

        price = self.get_storage_price(f"ebs_{volume_type}", size_gb)
        monthly = price.amount * Decimal(str(size_gb))

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_ebs_volume",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=monthly,
            currency=self.currency,
            category=CostCategory.STORAGE,
            storage_cost=monthly,
            price_points=[price],
            notes=[f"Type: {volume_type}", f"Size: {size_gb} GB"],
        )

    def _calculate_elasticache_cost(
        self,
        resource_id: str,
        resource_name: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate ElastiCache cost."""
        node_type = config.get("node_type", "cache.t3.medium")
        num_nodes = config.get("num_cache_nodes", 1)
        tier = PricingTier(config.get("pricing_tier", "ON_DEMAND"))

        price = self.get_ec2_price(
            node_type.replace("cache.", ""), tier
        )  # Reuse EC2 pricing
        monthly = price.to_monthly() * Decimal(str(num_nodes))

        return ResourceCost(
            resource_id=resource_id,
            resource_type="aws_elasticache_cluster",
            resource_name=resource_name,
            region=self.region,
            monthly_cost=monthly,
            currency=self.currency,
            category=CostCategory.DATABASE,
            compute_cost=monthly,
            pricing_tier=tier,
            price_points=[price],
            notes=[f"Node type: {node_type}", f"Nodes: {num_nodes}"],
        )

    def _calculate_unknown_cost(
        self,
        resource_id: str,
        resource_name: str,
        resource_type: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate cost for unknown resource type."""
        return ResourceCost(
            resource_id=resource_id,
            resource_type=resource_type,
            resource_name=resource_name,
            region=self.region,
            monthly_cost=Decimal("0"),
            currency=self.currency,
            category=CostCategory.OTHER,
            notes=["Pricing not available for this resource type"],
        )

    def apply_discount(
        self,
        cost: ResourceCost,
        discount_percent: Decimal,
        discount_name: str = "Custom Discount",
    ) -> ResourceCost:
        """Apply a discount to a resource cost."""
        multiplier = Decimal("1") - (discount_percent / Decimal("100"))

        return ResourceCost(
            resource_id=cost.resource_id,
            resource_type=cost.resource_type,
            resource_name=cost.resource_name,
            region=cost.region,
            monthly_cost=cost.monthly_cost * multiplier,
            currency=cost.currency,
            category=cost.category,
            compute_cost=cost.compute_cost * multiplier,
            storage_cost=cost.storage_cost * multiplier,
            network_cost=cost.network_cost * multiplier,
            license_cost=cost.license_cost * multiplier,
            other_cost=cost.other_cost * multiplier,
            pricing_tier=cost.pricing_tier,
            notes=cost.notes + [f"{discount_name}: {discount_percent}% off"],
            price_points=cost.price_points,
        )


class DefaultPricingEngine(BasePricingEngine):
    """Default pricing engine using us-east-1 base prices with multipliers."""

    # Regional multipliers relative to us-east-1
    REGION_MULTIPLIERS: ClassVar[dict[str, Decimal]] = {
        "us-east-1": Decimal("1.00"),
        "us-east-2": Decimal("1.00"),
        "us-west-1": Decimal("1.10"),
        "us-west-2": Decimal("1.00"),
        "eu-west-1": Decimal("1.10"),
        "eu-west-2": Decimal("1.15"),
        "eu-west-3": Decimal("1.15"),
        "eu-central-1": Decimal("1.15"),
        "eu-north-1": Decimal("1.10"),
        "ap-northeast-1": Decimal("1.25"),
        "ap-northeast-2": Decimal("1.20"),
        "ap-northeast-3": Decimal("1.25"),
        "ap-southeast-1": Decimal("1.15"),
        "ap-southeast-2": Decimal("1.20"),
        "ap-southeast-4": Decimal("1.25"),
        "ap-south-1": Decimal("1.10"),
        "sa-east-1": Decimal("1.50"),
        "ca-central-1": Decimal("1.05"),
        "me-south-1": Decimal("1.20"),
        "af-south-1": Decimal("1.30"),
    }

    # Base EC2 prices (us-east-1, hourly)
    EC2_BASE_PRICES: ClassVar[dict[str, Decimal]] = {
        "t3.nano": Decimal("0.0052"),
        "t3.micro": Decimal("0.0104"),
        "t3.small": Decimal("0.0208"),
        "t3.medium": Decimal("0.0416"),
        "t3.large": Decimal("0.0832"),
        "t3.xlarge": Decimal("0.1664"),
        "t3.2xlarge": Decimal("0.3328"),
        "m5.large": Decimal("0.096"),
        "m5.xlarge": Decimal("0.192"),
        "m5.2xlarge": Decimal("0.384"),
        "m5.4xlarge": Decimal("0.768"),
        "m6i.large": Decimal("0.096"),
        "m6i.xlarge": Decimal("0.192"),
        "m6i.2xlarge": Decimal("0.384"),
        "r5.large": Decimal("0.126"),
        "r5.xlarge": Decimal("0.252"),
        "r5.2xlarge": Decimal("0.504"),
        "c5.large": Decimal("0.085"),
        "c5.xlarge": Decimal("0.17"),
        "c5.2xlarge": Decimal("0.34"),
    }

    # Base RDS prices (us-east-1, hourly, single-AZ)
    RDS_BASE_PRICES: ClassVar[dict[str, Decimal]] = {
        "db.t3.micro": Decimal("0.017"),
        "db.t3.small": Decimal("0.034"),
        "db.t3.medium": Decimal("0.068"),
        "db.t3.large": Decimal("0.136"),
        "db.m5.large": Decimal("0.171"),
        "db.m5.xlarge": Decimal("0.342"),
        "db.m5.2xlarge": Decimal("0.684"),
        "db.r5.large": Decimal("0.24"),
        "db.r5.xlarge": Decimal("0.48"),
        "db.r5.2xlarge": Decimal("0.96"),
    }

    # Storage prices (per GB-month)
    STORAGE_PRICES: ClassVar[dict[str, Decimal]] = {
        "ebs_gp2": Decimal("0.10"),
        "ebs_gp3": Decimal("0.08"),
        "ebs_io1": Decimal("0.125"),
        "ebs_io2": Decimal("0.125"),
        "ebs_st1": Decimal("0.045"),
        "ebs_sc1": Decimal("0.015"),
        "rds_gp2": Decimal("0.115"),
        "rds_gp3": Decimal("0.092"),
        "rds_io1": Decimal("0.125"),
        "s3_standard": Decimal("0.023"),
        "s3_ia": Decimal("0.0125"),
        "s3_glacier": Decimal("0.004"),
    }

    # Network prices
    NETWORK_PRICES: ClassVar[dict[str, Decimal]] = {
        "nat_gateway_hourly": Decimal("0.045"),
        "nat_gateway_per_gb": Decimal("0.045"),
        "alb_hourly": Decimal("0.0225"),
        "nlb_hourly": Decimal("0.0225"),
        "clb_hourly": Decimal("0.025"),
        "data_transfer_out": Decimal("0.09"),
        "data_transfer_cross_az": Decimal("0.01"),
    }

    def __init__(
        self,
        region: str,
        currency: Currency = Currency.USD,
        exchange_rates: dict[str, Decimal] | None = None,
    ) -> None:
        super().__init__(region, currency, exchange_rates)
        self.region_multiplier = self.REGION_MULTIPLIERS.get(region, Decimal("1.0"))

    def get_ec2_price(
        self,
        instance_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
        os: str = "Linux",
    ) -> PricePoint:
        """Get EC2 instance price."""
        base = self.EC2_BASE_PRICES.get(instance_type)

        if base is None:
            # Estimate based on size
            base = self._estimate_ec2_price(instance_type)

        price = base * self.region_multiplier * self._get_tier_multiplier(tier)

        return PricePoint(
            amount=price,
            currency=Currency.USD,
            unit=PricingUnit.HOURLY,
            region=self.region,
            service="ec2",
            resource_type="instance",
            description=f"{instance_type} ({os})",
            tier=tier,
        )

    def get_rds_price(
        self,
        instance_class: str,
        engine: str = "mysql",
        multi_az: bool = False,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get RDS instance price."""
        base = self.RDS_BASE_PRICES.get(instance_class)

        if base is None:
            base = self._estimate_rds_price(instance_class)

        price = base * self.region_multiplier * self._get_tier_multiplier(tier)

        if multi_az:
            price *= Decimal("2")

        return PricePoint(
            amount=price,
            currency=Currency.USD,
            unit=PricingUnit.HOURLY,
            region=self.region,
            service="rds",
            resource_type="db_instance",
            description=f"{instance_class} ({engine})",
            tier=tier,
        )

    def get_storage_price(
        self,
        storage_type: str,
        size_gb: float = 1.0,
    ) -> PricePoint:
        """Get storage price."""
        base = self.STORAGE_PRICES.get(storage_type, Decimal("0.10"))
        price = base * self.region_multiplier

        return PricePoint(
            amount=price,
            currency=Currency.USD,
            unit=PricingUnit.PER_GB_MONTH,
            region=self.region,
            service="storage",
            resource_type=storage_type,
            description=f"{storage_type} storage",
        )

    def get_network_price(
        self,
        service: str,
        transfer_type: str = "out",
    ) -> PricePoint:
        """Get network price."""
        key = f"{service}_{transfer_type}"
        base = self.NETWORK_PRICES.get(key, Decimal("0.01"))
        price = base * self.region_multiplier

        unit = PricingUnit.HOURLY if "hourly" in transfer_type else PricingUnit.PER_GB

        return PricePoint(
            amount=price,
            currency=Currency.USD,
            unit=unit,
            region=self.region,
            service="network",
            resource_type=service,
            description=f"{service} {transfer_type}",
        )

    def _get_tier_multiplier(self, tier: PricingTier) -> Decimal:
        """Get pricing tier multiplier."""
        multipliers = {
            PricingTier.ON_DEMAND: Decimal("1.0"),
            PricingTier.RESERVED_1Y: Decimal("0.60"),
            PricingTier.RESERVED_3Y: Decimal("0.40"),
            PricingTier.SPOT: Decimal("0.30"),
            PricingTier.SAVINGS_PLAN: Decimal("0.65"),
        }
        return multipliers.get(tier, Decimal("1.0"))

    def _estimate_ec2_price(self, instance_type: str) -> Decimal:
        """Estimate EC2 price for unknown types."""
        parts = instance_type.split(".")
        if len(parts) < 2:
            return Decimal("0.05")

        size = parts[1]
        size_multipliers = {
            "nano": Decimal("0.5"),
            "micro": Decimal("1"),
            "small": Decimal("2"),
            "medium": Decimal("4"),
            "large": Decimal("8"),
            "xlarge": Decimal("16"),
            "2xlarge": Decimal("32"),
            "4xlarge": Decimal("64"),
            "8xlarge": Decimal("128"),
        }

        base = Decimal("0.01")
        multiplier = size_multipliers.get(size, Decimal("8"))
        return base * multiplier

    def _estimate_rds_price(self, instance_class: str) -> Decimal:
        """Estimate RDS price for unknown classes."""
        clean = instance_class.replace("db.", "")
        parts = clean.split(".")
        if len(parts) < 2:
            return Decimal("0.10")

        size = parts[1]
        size_multipliers = {
            "micro": Decimal("1"),
            "small": Decimal("2"),
            "medium": Decimal("4"),
            "large": Decimal("10"),
            "xlarge": Decimal("20"),
            "2xlarge": Decimal("40"),
        }

        base = Decimal("0.017")
        multiplier = size_multipliers.get(size, Decimal("10"))
        return base * multiplier


# Register default engine for all regions
BasePricingEngine._registry["*"] = DefaultPricingEngine
