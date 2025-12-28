"""
Australia Local Pricing (P1-5).

Provides Australia-specific AWS pricing including:
- ap-southeast-2 (Sydney) and ap-southeast-4 (Melbourne) pricing
- Australian Dollar (AUD) currency support
- GST (10%) calculation
- Sydney vs Melbourne price comparison
- EDP (Enterprise Discount Program) support
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, ClassVar

from replimap.cost.models import CostCategory, PricingTier
from replimap.cost.pricing_engine import (
    BasePricingEngine,
    Currency,
    PricePoint,
    PricingUnit,
    ResourceCost,
)


# Australian GST rate
AU_GST_RATE = Decimal("0.10")  # 10%

# AUD exchange rate (approximate, should be fetched dynamically in production)
AUD_EXCHANGE_RATE = Decimal("1.55")  # 1 USD = 1.55 AUD


@dataclass
class AUPricingConfig:
    """Configuration for Australian pricing."""

    include_gst: bool = True
    currency: Currency = Currency.AUD
    edp_discount_percent: Decimal = Decimal("0")
    ppa_prices: dict[str, Decimal] | None = None  # Private Pricing Agreement


@BasePricingEngine.register("ap-southeast-2")
@BasePricingEngine.register("ap-southeast-4")
class AustraliaPricingEngine(BasePricingEngine):
    """
    Pricing engine for Australian AWS regions.

    Supports:
    - ap-southeast-2 (Sydney)
    - ap-southeast-4 (Melbourne)
    """

    # Sydney EC2 prices (AUD, hourly, on-demand)
    # These are actual AWS prices for Sydney region
    SYDNEY_EC2_PRICES: ClassVar[dict[str, Decimal]] = {
        # T3 - General Purpose Burstable
        "t3.nano": Decimal("0.0084"),
        "t3.micro": Decimal("0.0168"),
        "t3.small": Decimal("0.0336"),
        "t3.medium": Decimal("0.0672"),
        "t3.large": Decimal("0.1344"),
        "t3.xlarge": Decimal("0.2688"),
        "t3.2xlarge": Decimal("0.5376"),
        # T3a - AMD
        "t3a.nano": Decimal("0.0076"),
        "t3a.micro": Decimal("0.0152"),
        "t3a.small": Decimal("0.0303"),
        "t3a.medium": Decimal("0.0606"),
        "t3a.large": Decimal("0.1213"),
        "t3a.xlarge": Decimal("0.2426"),
        "t3a.2xlarge": Decimal("0.4851"),
        # M5 - General Purpose
        "m5.large": Decimal("0.155"),
        "m5.xlarge": Decimal("0.310"),
        "m5.2xlarge": Decimal("0.620"),
        "m5.4xlarge": Decimal("1.240"),
        "m5.8xlarge": Decimal("2.480"),
        "m5.12xlarge": Decimal("3.720"),
        "m5.16xlarge": Decimal("4.960"),
        "m5.24xlarge": Decimal("7.440"),
        # M6i - Latest Gen General Purpose
        "m6i.large": Decimal("0.155"),
        "m6i.xlarge": Decimal("0.310"),
        "m6i.2xlarge": Decimal("0.620"),
        "m6i.4xlarge": Decimal("1.240"),
        "m6i.8xlarge": Decimal("2.480"),
        # M7i - 7th Gen
        "m7i.large": Decimal("0.163"),
        "m7i.xlarge": Decimal("0.326"),
        "m7i.2xlarge": Decimal("0.652"),
        # C5 - Compute Optimized
        "c5.large": Decimal("0.137"),
        "c5.xlarge": Decimal("0.274"),
        "c5.2xlarge": Decimal("0.548"),
        "c5.4xlarge": Decimal("1.096"),
        "c5.9xlarge": Decimal("2.466"),
        # C6i - Latest Gen Compute
        "c6i.large": Decimal("0.137"),
        "c6i.xlarge": Decimal("0.274"),
        "c6i.2xlarge": Decimal("0.548"),
        # R5 - Memory Optimized
        "r5.large": Decimal("0.203"),
        "r5.xlarge": Decimal("0.406"),
        "r5.2xlarge": Decimal("0.812"),
        "r5.4xlarge": Decimal("1.624"),
        "r5.8xlarge": Decimal("3.248"),
        # R6i - Latest Gen Memory
        "r6i.large": Decimal("0.203"),
        "r6i.xlarge": Decimal("0.406"),
        "r6i.2xlarge": Decimal("0.812"),
        # Graviton (ARM)
        "t4g.nano": Decimal("0.0067"),
        "t4g.micro": Decimal("0.0134"),
        "t4g.small": Decimal("0.0269"),
        "t4g.medium": Decimal("0.0538"),
        "t4g.large": Decimal("0.1075"),
        "m6g.large": Decimal("0.124"),
        "m6g.xlarge": Decimal("0.248"),
        "m6g.2xlarge": Decimal("0.496"),
        "c6g.large": Decimal("0.110"),
        "c6g.xlarge": Decimal("0.219"),
        "c6g.2xlarge": Decimal("0.438"),
        "r6g.large": Decimal("0.163"),
        "r6g.xlarge": Decimal("0.325"),
        "r6g.2xlarge": Decimal("0.650"),
    }

    # Melbourne premium over Sydney (Melbourne is ~5% more expensive)
    MELBOURNE_PREMIUM: ClassVar[Decimal] = Decimal("1.05")

    # Sydney RDS prices (AUD, hourly, on-demand, single-AZ)
    SYDNEY_RDS_PRICES: ClassVar[dict[str, Decimal]] = {
        # db.t3
        "db.t3.micro": Decimal("0.027"),
        "db.t3.small": Decimal("0.055"),
        "db.t3.medium": Decimal("0.110"),
        "db.t3.large": Decimal("0.219"),
        "db.t3.xlarge": Decimal("0.439"),
        "db.t3.2xlarge": Decimal("0.878"),
        # db.m5
        "db.m5.large": Decimal("0.276"),
        "db.m5.xlarge": Decimal("0.552"),
        "db.m5.2xlarge": Decimal("1.103"),
        "db.m5.4xlarge": Decimal("2.206"),
        "db.m5.8xlarge": Decimal("4.413"),
        # db.r5
        "db.r5.large": Decimal("0.387"),
        "db.r5.xlarge": Decimal("0.774"),
        "db.r5.2xlarge": Decimal("1.548"),
        "db.r5.4xlarge": Decimal("3.096"),
        # db.r6g (Graviton)
        "db.r6g.large": Decimal("0.348"),
        "db.r6g.xlarge": Decimal("0.697"),
        "db.r6g.2xlarge": Decimal("1.393"),
    }

    # Sydney storage prices (AUD, per GB-month)
    SYDNEY_STORAGE_PRICES: ClassVar[dict[str, Decimal]] = {
        # EBS
        "ebs_gp2": Decimal("0.16"),
        "ebs_gp3": Decimal("0.13"),
        "ebs_io1": Decimal("0.20"),
        "ebs_io2": Decimal("0.20"),
        "ebs_st1": Decimal("0.072"),
        "ebs_sc1": Decimal("0.024"),
        # RDS Storage
        "rds_gp2": Decimal("0.185"),
        "rds_gp3": Decimal("0.148"),
        "rds_io1": Decimal("0.20"),
        # S3
        "s3_standard": Decimal("0.037"),
        "s3_ia": Decimal("0.020"),
        "s3_glacier": Decimal("0.0064"),
        "s3_glacier_deep": Decimal("0.0016"),
        # EFS
        "efs_standard": Decimal("0.48"),
        "efs_ia": Decimal("0.040"),
    }

    # Sydney network prices (AUD)
    SYDNEY_NETWORK_PRICES: ClassVar[dict[str, Decimal]] = {
        "nat_gateway_hourly": Decimal("0.072"),
        "nat_gateway_per_gb": Decimal("0.072"),
        "alb_hourly": Decimal("0.036"),
        "nlb_hourly": Decimal("0.036"),
        "clb_hourly": Decimal("0.040"),
        "vpc_endpoint_hourly": Decimal("0.016"),
        "vpc_endpoint_per_gb": Decimal("0.016"),
        # Data Transfer
        "data_transfer_out_first_10tb": Decimal("0.145"),
        "data_transfer_out_next_40tb": Decimal("0.138"),
        "data_transfer_out_next_100tb": Decimal("0.120"),
        "data_transfer_cross_az": Decimal("0.016"),
        "data_transfer_to_cloudfront": Decimal("0.00"),  # Free
    }

    # ElastiCache prices (AUD, hourly)
    SYDNEY_ELASTICACHE_PRICES: ClassVar[dict[str, Decimal]] = {
        "cache.t3.micro": Decimal("0.027"),
        "cache.t3.small": Decimal("0.055"),
        "cache.t3.medium": Decimal("0.110"),
        "cache.m5.large": Decimal("0.252"),
        "cache.m5.xlarge": Decimal("0.503"),
        "cache.m5.2xlarge": Decimal("1.006"),
        "cache.r5.large": Decimal("0.365"),
        "cache.r5.xlarge": Decimal("0.729"),
        "cache.r5.2xlarge": Decimal("1.459"),
    }

    def __init__(
        self,
        region: str,
        currency: Currency = Currency.AUD,
        exchange_rates: dict[str, Decimal] | None = None,
        config: AUPricingConfig | None = None,
    ) -> None:
        """
        Initialize Australian pricing engine.

        Args:
            region: AWS region (ap-southeast-2 or ap-southeast-4)
            currency: Output currency (default AUD)
            exchange_rates: Custom exchange rates
            config: Australian pricing configuration
        """
        super().__init__(region, currency, exchange_rates)
        self.config = config or AUPricingConfig()
        self.is_melbourne = region == "ap-southeast-4"

        # Override exchange rates with accurate AUD rate
        self.exchange_rates["AUD"] = AUD_EXCHANGE_RATE

    def get_ec2_price(
        self,
        instance_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
        os: str = "Linux",
    ) -> PricePoint:
        """Get EC2 instance price in AUD."""
        # Check for PPA price first
        base: Decimal
        if self.config.ppa_prices and instance_type in self.config.ppa_prices:
            base = self.config.ppa_prices[instance_type]
        elif instance_type in self.SYDNEY_EC2_PRICES:
            base = self.SYDNEY_EC2_PRICES[instance_type]
        else:
            base = self._estimate_ec2_price(instance_type)

        # Apply Melbourne premium if applicable
        if self.is_melbourne:
            base = base * self.MELBOURNE_PREMIUM

        # Apply tier discount
        price = base * self._get_tier_multiplier(tier)

        # Apply EDP discount if configured
        if self.config.edp_discount_percent > 0:
            price = price * (
                Decimal("1") - self.config.edp_discount_percent / Decimal("100")
            )

        return PricePoint(
            amount=price,
            currency=Currency.AUD,
            unit=PricingUnit.HOURLY,
            region=self.region,
            service="ec2",
            resource_type="instance",
            description=f"{instance_type} ({os})",
            tier=tier,
            includes_tax=False,
            tax_rate=AU_GST_RATE if self.config.include_gst else Decimal("0"),
        )

    def get_rds_price(
        self,
        instance_class: str,
        engine: str = "mysql",
        multi_az: bool = False,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get RDS instance price in AUD."""
        base = self.SYDNEY_RDS_PRICES.get(instance_class)

        if base is None:
            base = self._estimate_rds_price(instance_class)

        if self.is_melbourne:
            base = base * self.MELBOURNE_PREMIUM

        price = base * self._get_tier_multiplier(tier)

        if multi_az:
            price = price * Decimal("2")

        if self.config.edp_discount_percent > 0:
            price = price * (
                Decimal("1") - self.config.edp_discount_percent / Decimal("100")
            )

        return PricePoint(
            amount=price,
            currency=Currency.AUD,
            unit=PricingUnit.HOURLY,
            region=self.region,
            service="rds",
            resource_type="db_instance",
            description=f"{instance_class} ({engine})",
            tier=tier,
            includes_tax=False,
            tax_rate=AU_GST_RATE if self.config.include_gst else Decimal("0"),
        )

    def get_storage_price(
        self,
        storage_type: str,
        size_gb: float = 1.0,
    ) -> PricePoint:
        """Get storage price in AUD."""
        base = self.SYDNEY_STORAGE_PRICES.get(storage_type, Decimal("0.16"))

        if self.is_melbourne:
            base = base * self.MELBOURNE_PREMIUM

        return PricePoint(
            amount=base,
            currency=Currency.AUD,
            unit=PricingUnit.PER_GB_MONTH,
            region=self.region,
            service="storage",
            resource_type=storage_type,
            description=f"{storage_type} storage",
            includes_tax=False,
            tax_rate=AU_GST_RATE if self.config.include_gst else Decimal("0"),
        )

    def get_network_price(
        self,
        service: str,
        transfer_type: str = "out",
    ) -> PricePoint:
        """Get network price in AUD."""
        key = f"{service}_{transfer_type}"
        base = self.SYDNEY_NETWORK_PRICES.get(key, Decimal("0.016"))

        if self.is_melbourne:
            base = base * self.MELBOURNE_PREMIUM

        unit = (
            PricingUnit.HOURLY if "hourly" in transfer_type else PricingUnit.PER_GB
        )

        return PricePoint(
            amount=base,
            currency=Currency.AUD,
            unit=unit,
            region=self.region,
            service="network",
            resource_type=service,
            description=f"{service} {transfer_type}",
            includes_tax=False,
            tax_rate=AU_GST_RATE if self.config.include_gst else Decimal("0"),
        )

    def get_elasticache_price(
        self,
        node_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get ElastiCache price in AUD."""
        base = self.SYDNEY_ELASTICACHE_PRICES.get(node_type)

        if base is None:
            # Estimate based on similar EC2 type
            ec2_type = node_type.replace("cache.", "")
            base = self.SYDNEY_EC2_PRICES.get(ec2_type, Decimal("0.10"))

        if self.is_melbourne:
            base = base * self.MELBOURNE_PREMIUM

        price = base * self._get_tier_multiplier(tier)

        return PricePoint(
            amount=price,
            currency=Currency.AUD,
            unit=PricingUnit.HOURLY,
            region=self.region,
            service="elasticache",
            resource_type="cache_cluster",
            description=f"{node_type}",
            tier=tier,
            includes_tax=False,
            tax_rate=AU_GST_RATE if self.config.include_gst else Decimal("0"),
        )

    def calculate_resource_cost(
        self,
        resource_type: str,
        config: dict[str, Any],
    ) -> ResourceCost:
        """Calculate resource cost with GST."""
        cost = super().calculate_resource_cost(resource_type, config)

        # Apply GST if configured
        if self.config.include_gst:
            cost.tax_rate = AU_GST_RATE
            cost.pre_tax_cost = cost.monthly_cost
            cost.tax_amount = cost.monthly_cost * AU_GST_RATE
            cost.monthly_cost = cost.monthly_cost + cost.tax_amount
            cost.notes.append("Price includes 10% GST")

        return cost

    def _get_tier_multiplier(self, tier: PricingTier) -> Decimal:
        """Get pricing tier multiplier."""
        multipliers = {
            PricingTier.ON_DEMAND: Decimal("1.0"),
            PricingTier.RESERVED_1Y: Decimal("0.58"),  # ~42% savings in AU
            PricingTier.RESERVED_3Y: Decimal("0.37"),  # ~63% savings in AU
            PricingTier.SPOT: Decimal("0.25"),  # More variable in AU
            PricingTier.SAVINGS_PLAN: Decimal("0.62"),  # ~38% savings
        }
        return multipliers.get(tier, Decimal("1.0"))

    def _estimate_ec2_price(self, instance_type: str) -> Decimal:
        """Estimate EC2 price for unknown types (in AUD)."""
        parts = instance_type.split(".")
        if len(parts) < 2:
            return Decimal("0.08")

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

        base = Decimal("0.016")  # AUD base
        multiplier = size_multipliers.get(size, Decimal("8"))
        return base * multiplier

    def _estimate_rds_price(self, instance_class: str) -> Decimal:
        """Estimate RDS price for unknown classes (in AUD)."""
        clean = instance_class.replace("db.", "")
        parts = clean.split(".")
        if len(parts) < 2:
            return Decimal("0.16")

        size = parts[1]
        size_multipliers = {
            "micro": Decimal("1"),
            "small": Decimal("2"),
            "medium": Decimal("4"),
            "large": Decimal("10"),
            "xlarge": Decimal("20"),
            "2xlarge": Decimal("40"),
        }

        base = Decimal("0.027")  # AUD base
        multiplier = size_multipliers.get(size, Decimal("10"))
        return base * multiplier


@dataclass
class RegionComparison:
    """Comparison between Sydney and Melbourne pricing."""

    resource_type: str
    resource_config: dict[str, Any]
    sydney_cost: ResourceCost
    melbourne_cost: ResourceCost
    difference_aud: Decimal
    difference_percent: Decimal

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_type": self.resource_type,
            "sydney": {
                "monthly_cost": float(self.sydney_cost.monthly_cost),
                "currency": self.sydney_cost.currency.value,
            },
            "melbourne": {
                "monthly_cost": float(self.melbourne_cost.monthly_cost),
                "currency": self.melbourne_cost.currency.value,
            },
            "difference": {
                "aud": float(self.difference_aud),
                "percent": float(self.difference_percent),
            },
            "recommendation": (
                "Sydney"
                if self.sydney_cost.monthly_cost < self.melbourne_cost.monthly_cost
                else "Melbourne"
            ),
        }


def compare_au_regions(
    resource_type: str,
    config: dict[str, Any],
    include_gst: bool = True,
) -> RegionComparison:
    """
    Compare costs between Sydney and Melbourne regions.

    Args:
        resource_type: AWS resource type
        config: Resource configuration
        include_gst: Whether to include GST in calculations

    Returns:
        RegionComparison with cost details for both regions
    """
    au_config = AUPricingConfig(include_gst=include_gst)

    sydney_engine = AustraliaPricingEngine(
        region="ap-southeast-2",
        config=au_config,
    )
    melbourne_engine = AustraliaPricingEngine(
        region="ap-southeast-4",
        config=au_config,
    )

    sydney_cost = sydney_engine.calculate_resource_cost(resource_type, config)
    melbourne_cost = melbourne_engine.calculate_resource_cost(resource_type, config)

    difference = melbourne_cost.monthly_cost - sydney_cost.monthly_cost
    if sydney_cost.monthly_cost > 0:
        percent = (difference / sydney_cost.monthly_cost) * Decimal("100")
    else:
        percent = Decimal("0")

    return RegionComparison(
        resource_type=resource_type,
        resource_config=config,
        sydney_cost=sydney_cost,
        melbourne_cost=melbourne_cost,
        difference_aud=difference,
        difference_percent=percent,
    )


def calculate_gst(amount: Decimal) -> tuple[Decimal, Decimal]:
    """
    Calculate GST component from a total amount.

    Args:
        amount: Total amount including GST

    Returns:
        Tuple of (pre_gst_amount, gst_amount)
    """
    # GST is 10%, so total = base * 1.10
    # base = total / 1.10
    pre_gst = amount / (Decimal("1") + AU_GST_RATE)
    gst = amount - pre_gst
    return pre_gst, gst


def add_gst(amount: Decimal) -> Decimal:
    """Add GST to an amount."""
    return amount * (Decimal("1") + AU_GST_RATE)
