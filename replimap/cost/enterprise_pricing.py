"""
Enterprise Pricing Engine for RepliMap.

Provides enterprise-level pricing capabilities:
- EDP (Enterprise Discount Program) discount application
- PPA (Private Pricing Agreement) custom prices
- Volume discount rules
- YAML configuration support

This module extends the base pricing engine to support
enterprise pricing agreements and custom discount structures.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from replimap.cost.models import CostCategory, PricingTier
from replimap.cost.pricing_engine import (
    BasePricingEngine,
    Currency,
    PricePoint,
    PricingUnit,
    ResourceCost,
)

logger = logging.getLogger(__name__)


class DiscountType(str, Enum):
    """Types of enterprise discounts."""

    EDP = "edp"  # Enterprise Discount Program
    PPA = "ppa"  # Private Pricing Agreement
    VOLUME = "volume"  # Volume-based discount
    COMMITMENT = "commitment"  # Commitment-based (Savings Plans)
    BUNDLED = "bundled"  # Bundled service discount
    PROMOTIONAL = "promotional"  # Promotional discount

    def __str__(self) -> str:
        return self.value


class DiscountScope(str, Enum):
    """Scope of discount application."""

    GLOBAL = "global"  # Applies to all resources
    SERVICE = "service"  # Applies to specific service (EC2, RDS, etc.)
    RESOURCE_TYPE = "resource_type"  # Applies to specific resource type
    REGION = "region"  # Applies to specific region
    ACCOUNT = "account"  # Applies to specific account
    USAGE_TYPE = "usage_type"  # Applies to specific usage type

    def __str__(self) -> str:
        return self.value


@dataclass
class DiscountRule:
    """
    A single discount rule.

    Defines how a discount is applied, including the scope,
    conditions, and discount percentage or fixed amount.
    """

    name: str
    discount_type: DiscountType
    scope: DiscountScope
    discount_percentage: Decimal | None = None
    discount_amount: Decimal | None = None
    priority: int = 100  # Lower = higher priority
    conditions: dict[str, Any] = field(default_factory=dict)
    applies_to: list[str] = field(default_factory=list)
    excludes: list[str] = field(default_factory=list)
    min_spend: Decimal | None = None
    max_discount: Decimal | None = None
    effective_start: str | None = None
    effective_end: str | None = None

    def apply(self, price: Decimal) -> Decimal:
        """
        Apply this discount to a price.

        Args:
            price: Original price

        Returns:
            Discounted price
        """
        if self.discount_percentage is not None:
            discount = price * (self.discount_percentage / Decimal("100"))
            if self.max_discount is not None:
                discount = min(discount, self.max_discount)
            return price - discount
        elif self.discount_amount is not None:
            return max(price - self.discount_amount, Decimal("0"))
        return price

    def matches(
        self,
        resource_type: str | None = None,
        service: str | None = None,
        region: str | None = None,
        usage_type: str | None = None,
    ) -> bool:
        """
        Check if this rule matches the given criteria.

        Args:
            resource_type: Resource type to check
            service: AWS service name
            region: AWS region
            usage_type: Usage type

        Returns:
            True if rule matches
        """
        # Check exclusions first
        if resource_type and resource_type in self.excludes:
            return False
        if service and service in self.excludes:
            return False

        # Check scope-specific matching
        if self.scope == DiscountScope.GLOBAL:
            return True

        if self.scope == DiscountScope.SERVICE and service:
            return service in self.applies_to or not self.applies_to

        if self.scope == DiscountScope.RESOURCE_TYPE and resource_type:
            return resource_type in self.applies_to or not self.applies_to

        if self.scope == DiscountScope.REGION and region:
            return region in self.applies_to or not self.applies_to

        if self.scope == DiscountScope.USAGE_TYPE and usage_type:
            return usage_type in self.applies_to or not self.applies_to

        # If no specific applies_to, match everything in scope
        return not self.applies_to

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "discount_type": self.discount_type.value,
            "scope": self.scope.value,
            "discount_percentage": float(self.discount_percentage) if self.discount_percentage else None,
            "discount_amount": float(self.discount_amount) if self.discount_amount else None,
            "priority": self.priority,
            "applies_to": self.applies_to,
            "excludes": self.excludes,
            "min_spend": float(self.min_spend) if self.min_spend else None,
            "max_discount": float(self.max_discount) if self.max_discount else None,
        }


@dataclass
class VolumeDiscountTier:
    """A tier in a volume discount structure."""

    min_units: int
    max_units: int | None  # None = unlimited
    discount_percentage: Decimal

    def matches(self, units: int) -> bool:
        """Check if this tier applies to the given unit count."""
        if units < self.min_units:
            return False
        if self.max_units is not None and units > self.max_units:
            return False
        return True


@dataclass
class VolumeDiscount:
    """
    Volume-based discount structure.

    Provides tiered discounts based on usage volume.
    """

    name: str
    service: str
    usage_type: str
    unit: str  # e.g., "hours", "GB", "requests"
    tiers: list[VolumeDiscountTier] = field(default_factory=list)

    def get_discount_percentage(self, units: int) -> Decimal:
        """Get the discount percentage for a given unit count."""
        for tier in sorted(self.tiers, key=lambda t: t.min_units, reverse=True):
            if tier.matches(units):
                return tier.discount_percentage
        return Decimal("0")


@dataclass
class CustomPrice:
    """
    Custom price from a Private Pricing Agreement (PPA).

    Overrides default pricing for specific resources or usage types.
    """

    resource_type: str
    instance_type: str | None = None
    region: str | None = None
    price: Decimal = Decimal("0")
    unit: PricingUnit = PricingUnit.HOURLY
    currency: Currency = Currency.USD
    effective_start: str | None = None
    effective_end: str | None = None

    def matches(
        self,
        resource_type: str,
        instance_type: str | None = None,
        region: str | None = None,
    ) -> bool:
        """Check if this custom price applies."""
        if self.resource_type != resource_type:
            return False
        if self.instance_type and instance_type and self.instance_type != instance_type:
            return False
        if self.region and region and self.region != region:
            return False
        return True

    def to_price_point(self, region: str = "us-east-1") -> PricePoint:
        """Convert to a PricePoint."""
        return PricePoint(
            amount=self.price,
            currency=self.currency,
            unit=self.unit,
            region=region,
            service="custom",
            resource_type=self.resource_type,
            description=f"PPA custom price for {self.instance_type or self.resource_type}",
        )


@dataclass
class EDPConfig:
    """
    Enterprise Discount Program configuration.

    EDP provides a flat discount percentage across AWS services
    in exchange for a spending commitment.
    """

    discount_percentage: Decimal
    commitment_amount: Decimal
    commitment_period_months: int = 12
    excluded_services: list[str] = field(default_factory=list)
    included_services: list[str] = field(default_factory=list)  # Empty = all

    def applies_to_service(self, service: str) -> bool:
        """Check if EDP applies to a service."""
        if service in self.excluded_services:
            return False
        if self.included_services and service not in self.included_services:
            return False
        return True


@dataclass
class EnterprisePricingConfig:
    """
    Complete enterprise pricing configuration.

    Combines EDP, PPA, volume discounts, and custom rules.
    """

    edp: EDPConfig | None = None
    custom_prices: list[CustomPrice] = field(default_factory=list)
    volume_discounts: list[VolumeDiscount] = field(default_factory=list)
    discount_rules: list[DiscountRule] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str | Path) -> EnterprisePricingConfig:
        """
        Load configuration from a YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            EnterprisePricingConfig instance
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EnterprisePricingConfig:
        """
        Create configuration from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            EnterprisePricingConfig instance
        """
        # Parse EDP
        edp = None
        if "edp" in data:
            edp_data = data["edp"]
            edp = EDPConfig(
                discount_percentage=Decimal(str(edp_data.get("discount_percentage", 0))),
                commitment_amount=Decimal(str(edp_data.get("commitment_amount", 0))),
                commitment_period_months=edp_data.get("commitment_period_months", 12),
                excluded_services=edp_data.get("excluded_services", []),
                included_services=edp_data.get("included_services", []),
            )

        # Parse custom prices
        custom_prices: list[CustomPrice] = []
        for cp_data in data.get("custom_prices", []):
            custom_prices.append(
                CustomPrice(
                    resource_type=cp_data["resource_type"],
                    instance_type=cp_data.get("instance_type"),
                    region=cp_data.get("region"),
                    price=Decimal(str(cp_data["price"])),
                    unit=PricingUnit(cp_data.get("unit", "hourly")),
                    currency=Currency(cp_data.get("currency", "USD")),
                )
            )

        # Parse volume discounts
        volume_discounts: list[VolumeDiscount] = []
        for vd_data in data.get("volume_discounts", []):
            tiers = [
                VolumeDiscountTier(
                    min_units=t["min_units"],
                    max_units=t.get("max_units"),
                    discount_percentage=Decimal(str(t["discount_percentage"])),
                )
                for t in vd_data.get("tiers", [])
            ]
            volume_discounts.append(
                VolumeDiscount(
                    name=vd_data["name"],
                    service=vd_data["service"],
                    usage_type=vd_data["usage_type"],
                    unit=vd_data["unit"],
                    tiers=tiers,
                )
            )

        # Parse discount rules
        discount_rules: list[DiscountRule] = []
        for rule_data in data.get("discount_rules", []):
            discount_rules.append(
                DiscountRule(
                    name=rule_data["name"],
                    discount_type=DiscountType(rule_data.get("discount_type", "edp")),
                    scope=DiscountScope(rule_data.get("scope", "global")),
                    discount_percentage=Decimal(str(rule_data["discount_percentage"]))
                    if "discount_percentage" in rule_data else None,
                    discount_amount=Decimal(str(rule_data["discount_amount"]))
                    if "discount_amount" in rule_data else None,
                    priority=rule_data.get("priority", 100),
                    applies_to=rule_data.get("applies_to", []),
                    excludes=rule_data.get("excludes", []),
                )
            )

        return cls(
            edp=edp,
            custom_prices=custom_prices,
            volume_discounts=volume_discounts,
            discount_rules=discount_rules,
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result: dict[str, Any] = {}

        if self.edp:
            result["edp"] = {
                "discount_percentage": float(self.edp.discount_percentage),
                "commitment_amount": float(self.edp.commitment_amount),
                "commitment_period_months": self.edp.commitment_period_months,
                "excluded_services": self.edp.excluded_services,
                "included_services": self.edp.included_services,
            }

        if self.custom_prices:
            result["custom_prices"] = [
                {
                    "resource_type": cp.resource_type,
                    "instance_type": cp.instance_type,
                    "region": cp.region,
                    "price": float(cp.price),
                    "unit": cp.unit.value,
                    "currency": cp.currency.value,
                }
                for cp in self.custom_prices
            ]

        if self.discount_rules:
            result["discount_rules"] = [r.to_dict() for r in self.discount_rules]

        if self.metadata:
            result["metadata"] = self.metadata

        return result

    def save_yaml(self, path: str | Path) -> None:
        """
        Save configuration to a YAML file.

        Args:
            path: Path to save to
        """
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


class EnterprisePricingEngine(BasePricingEngine):
    """
    Enterprise pricing engine with discount support.

    Extends the base pricing engine to apply:
    - EDP (Enterprise Discount Program) discounts
    - PPA (Private Pricing Agreement) custom prices
    - Volume-based discounts
    - Custom discount rules
    """

    # Service mapping for discount application
    RESOURCE_TO_SERVICE: dict[str, str] = {
        "aws_instance": "ec2",
        "aws_autoscaling_group": "ec2",
        "aws_launch_template": "ec2",
        "aws_db_instance": "rds",
        "aws_rds_cluster": "rds",
        "aws_dynamodb_table": "dynamodb",
        "aws_s3_bucket": "s3",
        "aws_elasticache_cluster": "elasticache",
        "aws_elasticache_replication_group": "elasticache",
        "aws_lb": "elasticloadbalancing",
        "aws_lambda_function": "lambda",
        "aws_sqs_queue": "sqs",
        "aws_sns_topic": "sns",
        "aws_ebs_volume": "ebs",
        "aws_efs_file_system": "efs",
        "aws_cloudwatch_log_group": "cloudwatch",
    }

    def __init__(
        self,
        config: EnterprisePricingConfig,
        base_engine: BasePricingEngine | None = None,
        region: str = "us-east-1",
        currency: Currency = Currency.USD,
    ) -> None:
        """
        Initialize the enterprise pricing engine.

        Args:
            config: Enterprise pricing configuration
            base_engine: Base pricing engine for list prices
            region: AWS region
            currency: Default currency
        """
        super().__init__(region=region, currency=currency)
        self.enterprise_config = config
        self.base_engine = base_engine

    def get_ec2_price(
        self,
        instance_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
        os: str = "Linux",
    ) -> PricePoint:
        """Get EC2 price with enterprise discounts applied."""
        # Check for PPA custom price first
        for cp in self.enterprise_config.custom_prices:
            if cp.matches("aws_instance", instance_type, self.region):
                return self._apply_edp(cp.to_price_point(self.region), "ec2")

        # Get base price from base engine
        if self.base_engine:
            base_price = self.base_engine.get_ec2_price(instance_type, tier, os)
        else:
            # Use default pricing - call the DefaultPricingEngine directly
            from replimap.cost.pricing_engine import DefaultPricingEngine
            default_engine = DefaultPricingEngine(self.region, self.currency)
            base_price = default_engine.get_ec2_price(instance_type, tier, os)

        # Apply EDP discount
        return self._apply_edp(base_price, "ec2")

    def get_rds_price(
        self,
        instance_class: str,
        engine: str = "mysql",
        multi_az: bool = False,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get RDS price with enterprise discounts applied."""
        # Check for PPA custom price
        for cp in self.enterprise_config.custom_prices:
            if cp.matches("aws_db_instance", instance_class, self.region):
                return self._apply_edp(cp.to_price_point(self.region), "rds")

        # Get base price
        if self.base_engine:
            base_price = self.base_engine.get_rds_price(instance_class, engine, multi_az, tier)
        else:
            from replimap.cost.pricing_engine import DefaultPricingEngine
            default_engine = DefaultPricingEngine(self.region, self.currency)
            base_price = default_engine.get_rds_price(instance_class, engine, multi_az, tier)

        return self._apply_edp(base_price, "rds")

    def get_storage_price(
        self,
        storage_type: str,
        size_gb: float = 1.0,
    ) -> PricePoint:
        """Get storage price with enterprise discounts applied."""
        # Get base price
        if self.base_engine:
            base_price = self.base_engine.get_storage_price(storage_type, size_gb)
        else:
            from replimap.cost.pricing_engine import DefaultPricingEngine
            default_engine = DefaultPricingEngine(self.region, self.currency)
            base_price = default_engine.get_storage_price(storage_type, size_gb)

        service = "ebs" if storage_type == "ebs" else "s3"
        return self._apply_edp(base_price, service)

    def get_network_price(
        self,
        service: str,
        transfer_type: str = "out",
    ) -> PricePoint:
        """Get network price with enterprise discounts applied."""
        # Get base price
        if self.base_engine:
            base_price = self.base_engine.get_network_price(service, transfer_type)
        else:
            from replimap.cost.pricing_engine import DefaultPricingEngine
            default_engine = DefaultPricingEngine(self.region, self.currency)
            base_price = default_engine.get_network_price(service, transfer_type)

        return self._apply_edp(base_price, "ec2")  # Network is usually under EC2 billing

    def _apply_edp(self, price: PricePoint, service: str) -> PricePoint:
        """Apply EDP discount if applicable."""
        if not self.enterprise_config.edp:
            return price

        edp = self.enterprise_config.edp
        if not edp.applies_to_service(service):
            return price

        discount_multiplier = (Decimal("100") - edp.discount_percentage) / Decimal("100")
        discounted_amount = price.amount * discount_multiplier

        return PricePoint(
            amount=discounted_amount,
            currency=price.currency,
            unit=price.unit,
            region=price.region,
            service=price.service,
            resource_type=price.resource_type,
            description=f"{price.description} (EDP {edp.discount_percentage}% discount)",
            tier=price.tier,
        )

    def apply_discounts(
        self,
        cost: ResourceCost,
        resource_type: str | None = None,
        usage_units: int | None = None,
    ) -> ResourceCost:
        """
        Apply all applicable discounts to a resource cost.

        Args:
            cost: Original resource cost
            resource_type: Resource type for matching rules
            usage_units: Usage units for volume discounts

        Returns:
            ResourceCost with discounts applied
        """
        service = self.RESOURCE_TO_SERVICE.get(resource_type or cost.resource_type, "")
        original_cost = cost.monthly_cost
        discounted_cost = original_cost
        applied_discounts: list[str] = []

        # Apply volume discounts first
        if usage_units:
            for vd in self.enterprise_config.volume_discounts:
                if vd.service == service:
                    discount_pct = vd.get_discount_percentage(usage_units)
                    if discount_pct > 0:
                        multiplier = (Decimal("100") - discount_pct) / Decimal("100")
                        discounted_cost = discounted_cost * multiplier
                        applied_discounts.append(f"volume:{vd.name}:{discount_pct}%")

        # Apply discount rules (sorted by priority)
        sorted_rules = sorted(
            self.enterprise_config.discount_rules,
            key=lambda r: r.priority,
        )

        for rule in sorted_rules:
            if rule.matches(
                resource_type=resource_type or cost.resource_type,
                service=service,
                region=cost.region,
            ):
                discounted_cost = rule.apply(discounted_cost)
                if rule.discount_percentage:
                    applied_discounts.append(
                        f"{rule.discount_type.value}:{rule.name}:{rule.discount_percentage}%"
                    )

        # Build notes with discount information
        discount_notes = cost.notes.copy()
        if applied_discounts:
            discount_notes.append(f"Discounts: {', '.join(applied_discounts)}")
            discount_notes.append(
                f"Original: {original_cost}, Savings: {original_cost - discounted_cost}"
            )

        # Create new cost with discounts applied
        return ResourceCost(
            resource_id=cost.resource_id,
            resource_type=cost.resource_type,
            resource_name=cost.resource_name,
            region=cost.region,
            monthly_cost=discounted_cost,
            currency=cost.currency,
            category=cost.category,
            pricing_tier=cost.pricing_tier,
            notes=discount_notes,
        )

    def calculate_total_savings(
        self,
        costs: list[ResourceCost],
        original_costs: list[ResourceCost] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate total savings from enterprise discounts.

        Args:
            costs: List of resource costs with discounts applied
            original_costs: Optional list of original costs for comparison

        Returns:
            Dictionary with savings summary
        """
        total_discounted = Decimal("0")
        total_original = Decimal("0")
        by_discount_type: dict[str, Decimal] = {}

        # Build lookup for original costs if provided
        original_lookup: dict[str, Decimal] = {}
        if original_costs:
            for oc in original_costs:
                original_lookup[oc.resource_id] = oc.monthly_cost

        for cost in costs:
            # Get original cost from lookup or parse from notes
            original = original_lookup.get(cost.resource_id, cost.monthly_cost)

            # Try to parse original from notes if available
            for note in cost.notes:
                if note.startswith("Original:"):
                    try:
                        # Parse "Original: X, Savings: Y"
                        parts = note.split(",")
                        orig_str = parts[0].replace("Original:", "").strip()
                        original = Decimal(str(orig_str))
                    except (ValueError, IndexError):
                        pass
                    break

            total_original += original
            total_discounted += cost.monthly_cost

            # Track savings by discount type from notes
            for note in cost.notes:
                if note.startswith("Discounts:"):
                    discount_info = note.replace("Discounts:", "").strip()
                    for discount in discount_info.split(","):
                        discount = discount.strip()
                        parts = discount.split(":")
                        if parts:
                            discount_type = parts[0]
                            savings = original - cost.monthly_cost
                            by_discount_type[discount_type] = (
                                by_discount_type.get(discount_type, Decimal("0")) + savings
                            )
                    break

        total_savings = total_original - total_discounted
        savings_percentage = (
            (total_savings / total_original * 100) if total_original > 0 else Decimal("0")
        )

        return {
            "total_original": float(total_original),
            "total_discounted": float(total_discounted),
            "total_savings": float(total_savings),
            "savings_percentage": float(savings_percentage),
            "by_discount_type": {k: float(v) for k, v in by_discount_type.items()},
            "currency": self.currency.value,
        }


def create_enterprise_engine(
    config_path: str | Path | None = None,
    config: EnterprisePricingConfig | None = None,
    region: str = "us-east-1",
) -> EnterprisePricingEngine:
    """
    Create an enterprise pricing engine.

    Args:
        config_path: Path to YAML configuration file
        config: Pre-loaded configuration
        region: AWS region

    Returns:
        Configured EnterprisePricingEngine
    """
    if config_path:
        config = EnterprisePricingConfig.from_yaml(config_path)
    elif config is None:
        config = EnterprisePricingConfig()

    return EnterprisePricingEngine(config=config, region=region)


def create_edp_config(
    discount_percentage: float,
    commitment_amount: float,
    commitment_months: int = 12,
    excluded_services: list[str] | None = None,
) -> EDPConfig:
    """
    Create an EDP configuration.

    Args:
        discount_percentage: Discount percentage (e.g., 10 for 10%)
        commitment_amount: Minimum spend commitment
        commitment_months: Commitment period in months
        excluded_services: Services excluded from EDP

    Returns:
        EDPConfig instance
    """
    return EDPConfig(
        discount_percentage=Decimal(str(discount_percentage)),
        commitment_amount=Decimal(str(commitment_amount)),
        commitment_period_months=commitment_months,
        excluded_services=excluded_services or [],
    )


def generate_sample_config() -> str:
    """
    Generate a sample YAML configuration.

    Returns:
        YAML string with sample configuration
    """
    sample = {
        "edp": {
            "discount_percentage": 10,
            "commitment_amount": 1000000,
            "commitment_period_months": 12,
            "excluded_services": ["marketplace"],
        },
        "custom_prices": [
            {
                "resource_type": "aws_instance",
                "instance_type": "m5.xlarge",
                "price": 0.15,
                "unit": "hourly",
                "currency": "USD",
            },
        ],
        "volume_discounts": [
            {
                "name": "S3 Storage Volume",
                "service": "s3",
                "usage_type": "storage",
                "unit": "GB",
                "tiers": [
                    {"min_units": 0, "max_units": 50000, "discount_percentage": 0},
                    {"min_units": 50001, "max_units": 500000, "discount_percentage": 5},
                    {"min_units": 500001, "max_units": None, "discount_percentage": 10},
                ],
            },
        ],
        "discount_rules": [
            {
                "name": "Data Analytics Discount",
                "discount_type": "bundled",
                "scope": "service",
                "discount_percentage": 15,
                "applies_to": ["athena", "glue", "redshift"],
            },
        ],
        "metadata": {
            "agreement_id": "AWS-EDP-2024-001",
            "effective_date": "2024-01-01",
            "expiry_date": "2024-12-31",
        },
    }

    return yaml.dump(sample, default_flow_style=False)
