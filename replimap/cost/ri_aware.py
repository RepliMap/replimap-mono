"""
RI/Savings Plan Aware Pricing (P3-4).

Provides reservation-aware cost analysis:
- Read existing RI/SP coverage from AWS
- Right-sizing that considers reservations
- Optimization recommendations adjusted for commitments
- Waste detection for underutilized reservations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from replimap.core.async_aws import AsyncAWSClient, RateLimiterRegistry
from replimap.cost.models import PricingTier
from replimap.cost.pricing_engine import (
    BasePricingEngine,
    Currency,
    DefaultPricingEngine,
    PricePoint,
    PricingUnit,
)

logger = logging.getLogger(__name__)


class ReservationType(str, Enum):
    """Types of AWS reservations."""

    RESERVED_INSTANCE = "reserved_instance"
    SAVINGS_PLAN_COMPUTE = "savings_plan_compute"
    SAVINGS_PLAN_EC2 = "savings_plan_ec2"
    SAVINGS_PLAN_SAGEMAKER = "savings_plan_sagemaker"

    def __str__(self) -> str:
        return self.value


class ReservationState(str, Enum):
    """State of a reservation."""

    ACTIVE = "active"
    RETIRED = "retired"
    PAYMENT_PENDING = "payment-pending"
    PAYMENT_FAILED = "payment-failed"
    QUEUED = "queued"
    QUEUED_DELETED = "queued-deleted"

    def __str__(self) -> str:
        return self.value


class UtilizationLevel(str, Enum):
    """Utilization level of a reservation."""

    HIGH = "high"  # >90%
    MEDIUM = "medium"  # 70-90%
    LOW = "low"  # 50-70%
    CRITICAL = "critical"  # <50%

    def __str__(self) -> str:
        return self.value


class RightSizingAction(str, Enum):
    """Right-sizing recommendation actions."""

    DOWNSIZE = "downsize"
    UPSIZE = "upsize"
    TERMINATE = "terminate"
    MODERNIZE = "modernize"
    CHANGE_FAMILY = "change_family"
    NO_CHANGE = "no_change"

    def __str__(self) -> str:
        return self.value


@dataclass
class ReservedInstance:
    """Represents an AWS Reserved Instance."""

    reservation_id: str
    instance_type: str
    instance_count: int
    availability_zone: str | None
    region: str
    scope: str  # "Availability Zone" or "Region"
    offering_class: str  # "standard" or "convertible"
    offering_type: str  # "No Upfront", "Partial Upfront", "All Upfront"
    state: ReservationState
    start_date: datetime
    end_date: datetime
    fixed_price: Decimal
    usage_price: Decimal
    currency: Currency = Currency.USD

    # Utilization metrics
    utilization_percentage: float = 0.0
    hours_used: float = 0.0
    hours_available: float = 0.0

    @property
    def is_active(self) -> bool:
        """Check if reservation is active."""
        return self.state == ReservationState.ACTIVE

    @property
    def days_remaining(self) -> int:
        """Days until reservation expires."""
        now = datetime.now()
        if self.end_date < now:
            return 0
        return (self.end_date - now).days

    @property
    def is_expiring_soon(self) -> bool:
        """Check if expiring within 30 days."""
        return 0 < self.days_remaining <= 30

    @property
    def monthly_cost(self) -> Decimal:
        """Calculate monthly cost of reservation."""
        if self.hours_available > 0:
            hourly = self.usage_price
        else:
            hourly = Decimal("0")
        # Add amortized fixed cost
        total_months = (self.end_date - self.start_date).days / 30
        if total_months > 0:
            amortized = self.fixed_price / Decimal(str(total_months))
        else:
            amortized = Decimal("0")
        return (hourly * Decimal("730")) + amortized

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reservation_id": self.reservation_id,
            "instance_type": self.instance_type,
            "instance_count": self.instance_count,
            "availability_zone": self.availability_zone,
            "region": self.region,
            "scope": self.scope,
            "offering_class": self.offering_class,
            "offering_type": self.offering_type,
            "state": str(self.state),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "days_remaining": self.days_remaining,
            "is_expiring_soon": self.is_expiring_soon,
            "fixed_price": float(self.fixed_price),
            "usage_price": float(self.usage_price),
            "monthly_cost": float(self.monthly_cost),
            "utilization": {
                "percentage": self.utilization_percentage,
                "hours_used": self.hours_used,
                "hours_available": self.hours_available,
            },
        }


@dataclass
class SavingsPlanCommitment:
    """Represents an AWS Savings Plan commitment."""

    savings_plan_id: str
    savings_plan_arn: str
    savings_plan_type: str  # "Compute", "EC2Instance", "SageMaker"
    payment_option: str  # "No Upfront", "Partial Upfront", "All Upfront"
    term_duration: str  # "1yr" or "3yr"
    state: str
    region: str | None
    start_time: datetime
    end_time: datetime
    commitment: Decimal  # Hourly commitment in USD
    currency: Currency = Currency.USD

    # Utilization
    utilization_percentage: float = 0.0
    used_commitment: Decimal = Decimal("0")
    unused_commitment: Decimal = Decimal("0")

    # EC2 Instance SP specific
    instance_family: str | None = None

    @property
    def is_active(self) -> bool:
        """Check if savings plan is active."""
        return self.state == "active"

    @property
    def days_remaining(self) -> int:
        """Days until savings plan expires."""
        now = datetime.now()
        if self.end_time < now:
            return 0
        return (self.end_time - now).days

    @property
    def is_expiring_soon(self) -> bool:
        """Check if expiring within 30 days."""
        return 0 < self.days_remaining <= 30

    @property
    def monthly_commitment(self) -> Decimal:
        """Monthly commitment amount."""
        return self.commitment * Decimal("730")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "savings_plan_id": self.savings_plan_id,
            "savings_plan_type": self.savings_plan_type,
            "payment_option": self.payment_option,
            "term_duration": self.term_duration,
            "state": self.state,
            "region": self.region,
            "instance_family": self.instance_family,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "days_remaining": self.days_remaining,
            "is_expiring_soon": self.is_expiring_soon,
            "commitment": {
                "hourly": float(self.commitment),
                "monthly": float(self.monthly_commitment),
            },
            "utilization": {
                "percentage": self.utilization_percentage,
                "used": float(self.used_commitment),
                "unused": float(self.unused_commitment),
            },
        }


@dataclass
class ReservationCoverage:
    """Coverage metrics for reservations."""

    # Overall coverage
    total_on_demand_cost: Decimal = Decimal("0")
    covered_cost: Decimal = Decimal("0")
    coverage_percentage: float = 0.0

    # Breakdown by type
    ri_coverage_percentage: float = 0.0
    sp_coverage_percentage: float = 0.0

    # By service
    ec2_coverage: float = 0.0
    rds_coverage: float = 0.0
    elasticache_coverage: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "total_on_demand_cost": float(self.total_on_demand_cost),
            "covered_cost": float(self.covered_cost),
            "coverage_percentage": round(self.coverage_percentage, 1),
            "breakdown": {
                "ri_coverage": round(self.ri_coverage_percentage, 1),
                "sp_coverage": round(self.sp_coverage_percentage, 1),
            },
            "by_service": {
                "ec2": round(self.ec2_coverage, 1),
                "rds": round(self.rds_coverage, 1),
                "elasticache": round(self.elasticache_coverage, 1),
            },
        }


@dataclass
class RightSizingRecommendation:
    """Right-sizing recommendation with reservation awareness."""

    resource_id: str
    resource_type: str
    resource_name: str
    region: str

    # Current state
    current_instance_type: str
    current_monthly_cost: Decimal

    # Recommended
    action: RightSizingAction
    recommended_instance_type: str | None
    recommended_monthly_cost: Decimal

    # Savings
    monthly_savings: Decimal
    savings_percentage: float

    # Reservation considerations
    has_reservation: bool = False
    reservation_id: str | None = None
    reservation_type: ReservationType | None = None
    reservation_impact: str = ""

    # Flexibility metrics
    is_reservation_constrained: bool = False
    can_use_convertible: bool = False
    alternative_actions: list[str] = field(default_factory=list)

    # Confidence
    confidence: str = "MEDIUM"
    rationale: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "current": {
                "instance_type": self.current_instance_type,
                "monthly_cost": float(self.current_monthly_cost),
            },
            "recommended": {
                "action": str(self.action),
                "instance_type": self.recommended_instance_type,
                "monthly_cost": float(self.recommended_monthly_cost),
            },
            "savings": {
                "monthly": float(self.monthly_savings),
                "percentage": round(self.savings_percentage, 1),
            },
            "reservation": {
                "has_reservation": self.has_reservation,
                "reservation_id": self.reservation_id,
                "reservation_type": str(self.reservation_type)
                if self.reservation_type
                else None,
                "impact": self.reservation_impact,
                "is_constrained": self.is_reservation_constrained,
                "can_use_convertible": self.can_use_convertible,
            },
            "alternative_actions": self.alternative_actions,
            "confidence": self.confidence,
            "rationale": self.rationale,
        }


@dataclass
class ReservationWaste:
    """Detected waste from underutilized reservations."""

    reservation_id: str
    reservation_type: ReservationType
    utilization_level: UtilizationLevel
    utilization_percentage: float
    monthly_waste: Decimal
    recommendation: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "reservation_id": self.reservation_id,
            "reservation_type": str(self.reservation_type),
            "utilization": {
                "level": str(self.utilization_level),
                "percentage": round(self.utilization_percentage, 1),
            },
            "monthly_waste": float(self.monthly_waste),
            "recommendation": self.recommendation,
            "details": self.details,
        }


@dataclass
class RIAwareAnalysis:
    """Complete RI/SP aware analysis results."""

    analysis_date: date
    region: str

    # Inventory
    reserved_instances: list[ReservedInstance] = field(default_factory=list)
    savings_plans: list[SavingsPlanCommitment] = field(default_factory=list)

    # Coverage
    coverage: ReservationCoverage = field(default_factory=ReservationCoverage)

    # Recommendations
    right_sizing_recommendations: list[RightSizingRecommendation] = field(
        default_factory=list
    )
    reservation_waste: list[ReservationWaste] = field(default_factory=list)

    # Expiring
    expiring_ris: list[ReservedInstance] = field(default_factory=list)
    expiring_sps: list[SavingsPlanCommitment] = field(default_factory=list)

    # Summary
    total_reservation_cost: Decimal = Decimal("0")
    total_waste: Decimal = Decimal("0")
    total_potential_savings: Decimal = Decimal("0")

    # Warnings
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "region": self.region,
            "inventory": {
                "reserved_instances": [ri.to_dict() for ri in self.reserved_instances],
                "savings_plans": [sp.to_dict() for sp in self.savings_plans],
            },
            "coverage": self.coverage.to_dict(),
            "right_sizing": [r.to_dict() for r in self.right_sizing_recommendations],
            "waste": [w.to_dict() for w in self.reservation_waste],
            "expiring": {
                "reserved_instances": [ri.to_dict() for ri in self.expiring_ris],
                "savings_plans": [sp.to_dict() for sp in self.expiring_sps],
            },
            "summary": {
                "total_reservation_cost": float(self.total_reservation_cost),
                "total_waste": float(self.total_waste),
                "total_potential_savings": float(self.total_potential_savings),
            },
            "warnings": self.warnings,
        }


class RIAwarePricingEngine(BasePricingEngine):
    """
    Pricing engine that considers existing RI/SP commitments.

    Extends the default pricing engine to:
    - Apply reservation discounts when applicable
    - Track which resources have reservation coverage
    - Recommend right-sizing while considering commitments
    """

    def __init__(
        self,
        region: str,
        currency: Currency = Currency.USD,
        exchange_rates: dict[str, Decimal] | None = None,
        reserved_instances: list[ReservedInstance] | None = None,
        savings_plans: list[SavingsPlanCommitment] | None = None,
    ) -> None:
        """
        Initialize RI-aware pricing engine.

        Args:
            region: AWS region
            currency: Output currency
            exchange_rates: Custom exchange rates
            reserved_instances: List of active RIs
            savings_plans: List of active Savings Plans
        """
        super().__init__(region, currency, exchange_rates)
        self.reserved_instances = reserved_instances or []
        self.savings_plans = savings_plans or []
        self._default_engine = DefaultPricingEngine(region, currency, exchange_rates)

        # Build RI lookup by instance type
        self._ri_by_type: dict[str, list[ReservedInstance]] = {}
        for ri in self.reserved_instances:
            if ri.is_active:
                if ri.instance_type not in self._ri_by_type:
                    self._ri_by_type[ri.instance_type] = []
                self._ri_by_type[ri.instance_type].append(ri)

        # Calculate available SP commitment
        self._available_sp_commitment = sum(
            sp.commitment - sp.used_commitment
            for sp in self.savings_plans
            if sp.is_active
        )

    def get_ec2_price(
        self,
        instance_type: str,
        tier: PricingTier = PricingTier.ON_DEMAND,
        os: str = "Linux",
    ) -> PricePoint:
        """
        Get EC2 price considering reservations.

        If the instance type has an RI, return the RI price.
        """
        # Check for matching RI
        if instance_type in self._ri_by_type:
            ris = self._ri_by_type[instance_type]
            # Find one with unused capacity
            for ri in ris:
                if ri.hours_available > ri.hours_used:
                    return PricePoint(
                        amount=ri.usage_price,
                        currency=self.currency,
                        unit=PricingUnit.HOURLY,
                        region=self.region,
                        service="ec2",
                        resource_type="instance",
                        sku=ri.reservation_id,
                        description=f"{instance_type} (Reserved Instance)",
                        tier=PricingTier.RESERVED_1Y
                        if "1" in ri.offering_type.lower()
                        else PricingTier.RESERVED_3Y,
                    )

        # Fall back to default pricing
        return self._default_engine.get_ec2_price(instance_type, tier, os)

    def get_rds_price(
        self,
        instance_class: str,
        engine: str = "mysql",
        multi_az: bool = False,
        tier: PricingTier = PricingTier.ON_DEMAND,
    ) -> PricePoint:
        """Get RDS price (RIs not directly tracked here)."""
        return self._default_engine.get_rds_price(
            instance_class, engine, multi_az, tier
        )

    def get_storage_price(
        self,
        storage_type: str,
        size_gb: float = 1.0,
    ) -> PricePoint:
        """Get storage price."""
        return self._default_engine.get_storage_price(storage_type, size_gb)

    def get_network_price(
        self,
        service: str,
        transfer_type: str = "out",
    ) -> PricePoint:
        """Get network price."""
        return self._default_engine.get_network_price(service, transfer_type)

    def has_reservation_for(
        self,
        instance_type: str,
        service: str = "ec2",
    ) -> tuple[bool, ReservationType | None, str | None]:
        """
        Check if there's a reservation for an instance type.

        Returns:
            Tuple of (has_reservation, reservation_type, reservation_id)
        """
        if service == "ec2":
            if instance_type in self._ri_by_type:
                ri = self._ri_by_type[instance_type][0]
                return (True, ReservationType.RESERVED_INSTANCE, ri.reservation_id)

            # Check if covered by Savings Plan
            for sp in self.savings_plans:
                if sp.is_active and sp.savings_plan_type == "Compute":
                    return (
                        True,
                        ReservationType.SAVINGS_PLAN_COMPUTE,
                        sp.savings_plan_id,
                    )
                if (
                    sp.is_active
                    and sp.savings_plan_type == "EC2Instance"
                    and sp.instance_family
                ):
                    # Check instance family match
                    parts = instance_type.split(".")
                    if len(parts) >= 1 and parts[0] == sp.instance_family:
                        return (
                            True,
                            ReservationType.SAVINGS_PLAN_EC2,
                            sp.savings_plan_id,
                        )

        return (False, None, None)

    def get_right_sizing_impact(
        self,
        current_type: str,
        recommended_type: str,
    ) -> dict[str, Any]:
        """
        Analyze impact of right-sizing on reservations.

        Returns:
            Dict with impact analysis
        """
        has_ri, ri_type, ri_id = self.has_reservation_for(current_type)

        if not has_ri:
            return {
                "has_reservation": False,
                "impact": "none",
                "recommendation": "Proceed with right-sizing",
            }

        # Check if recommended type is in same family
        current_family = current_type.split(".")[0]
        recommended_family = recommended_type.split(".")[0]

        if ri_type == ReservationType.RESERVED_INSTANCE:
            # Standard RIs are instance-type specific
            return {
                "has_reservation": True,
                "reservation_type": str(ri_type),
                "reservation_id": ri_id,
                "impact": "high",
                "recommendation": (
                    "Reserved Instance is instance-type specific. "
                    "Consider waiting until RI expires or exchanging if convertible."
                ),
                "can_proceed": False,
            }

        elif ri_type == ReservationType.SAVINGS_PLAN_EC2:
            # EC2 Instance SP is family-specific
            if current_family == recommended_family:
                return {
                    "has_reservation": True,
                    "reservation_type": str(ri_type),
                    "impact": "low",
                    "recommendation": (
                        "EC2 Instance Savings Plan covers entire instance family. "
                        "Right-sizing within family is recommended."
                    ),
                    "can_proceed": True,
                }
            else:
                return {
                    "has_reservation": True,
                    "reservation_type": str(ri_type),
                    "impact": "medium",
                    "recommendation": (
                        "Changing instance family may reduce Savings Plan utilization. "
                        "Consider instances in the same family first."
                    ),
                    "can_proceed": True,
                    "alternatives": self._get_same_family_alternatives(
                        current_type, current_family
                    ),
                }

        elif ri_type == ReservationType.SAVINGS_PLAN_COMPUTE:
            # Compute SP is fully flexible
            return {
                "has_reservation": True,
                "reservation_type": str(ri_type),
                "impact": "none",
                "recommendation": (
                    "Compute Savings Plan covers all instance types. "
                    "Proceed with right-sizing."
                ),
                "can_proceed": True,
            }

        return {"has_reservation": True, "impact": "unknown"}

    def _get_same_family_alternatives(
        self,
        current_type: str,
        family: str,
    ) -> list[str]:
        """Get alternative instance types in the same family."""
        sizes = [
            "nano",
            "micro",
            "small",
            "medium",
            "large",
            "xlarge",
            "2xlarge",
            "4xlarge",
        ]
        current_size = current_type.split(".")[-1] if "." in current_type else "large"

        try:
            current_idx = sizes.index(current_size)
        except ValueError:
            return []

        alternatives = []
        # Suggest smaller sizes
        for i in range(max(0, current_idx - 2), current_idx):
            alternatives.append(f"{family}.{sizes[i]}")

        return alternatives


class RIAwareAnalyzer:
    """
    Analyzes reservation inventory and provides RI/SP-aware recommendations.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
        profile: str | None = None,
        credentials: dict[str, str] | None = None,
    ) -> None:
        """
        Initialize analyzer.

        Args:
            region: AWS region
            account_id: AWS account ID
            profile: AWS profile name for credentials (deprecated, use credentials)
            credentials: Pre-resolved AWS credentials dict with keys:
                         aws_access_key_id, aws_secret_access_key, aws_session_token
        """
        self.region = region
        self.account_id = account_id
        self.profile = profile
        self._credentials = credentials
        self._client: AsyncAWSClient | None = None

    async def close(self) -> None:
        """Close the AWS client and release resources."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    async def __aenter__(self) -> RIAwareAnalyzer:
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def _get_client(self) -> AsyncAWSClient:
        """Get AWS client."""
        if self._client is None:
            # Create a fresh RateLimiterRegistry to avoid asyncio.Lock event loop issues
            # (global registry may have locks bound to a different event loop)
            self._client = AsyncAWSClient(
                region=self.region,
                credentials=self._credentials,
                rate_registry=RateLimiterRegistry(),
            )
        return self._client

    async def get_reserved_instances(self) -> list[ReservedInstance]:
        """Fetch all Reserved Instances."""
        client = await self._get_client()
        ris: list[ReservedInstance] = []

        try:
            response = await client.call(
                "ec2",
                "describe_reserved_instances",
                Filters=[{"Name": "state", "Values": ["active"]}],
            )

            for ri in response.get("ReservedInstances", []):
                ris.append(
                    ReservedInstance(
                        reservation_id=ri.get("ReservedInstancesId", ""),
                        instance_type=ri.get("InstanceType", ""),
                        instance_count=ri.get("InstanceCount", 0),
                        availability_zone=ri.get("AvailabilityZone"),
                        region=self.region,
                        scope=ri.get("Scope", "Region"),
                        offering_class=ri.get("OfferingClass", "standard"),
                        offering_type=ri.get("OfferingType", "No Upfront"),
                        state=ReservationState(ri.get("State", "active")),
                        start_date=ri.get("Start", datetime.now()),
                        end_date=ri.get("End", datetime.now()),
                        fixed_price=Decimal(str(ri.get("FixedPrice", 0))),
                        usage_price=Decimal(str(ri.get("UsagePrice", 0))),
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to fetch Reserved Instances: {e}")

        return ris

    async def get_savings_plans(self) -> list[SavingsPlanCommitment]:
        """Fetch all Savings Plans."""
        client = await self._get_client()
        sps: list[SavingsPlanCommitment] = []

        try:
            response = await client.call(
                "savingsplans",
                "describe_savings_plans",
                states=["active"],
            )

            for sp in response.get("savingsPlans", []):
                commitment_str = sp.get("commitment", "0")
                sps.append(
                    SavingsPlanCommitment(
                        savings_plan_id=sp.get("savingsPlanId", ""),
                        savings_plan_arn=sp.get("savingsPlanArn", ""),
                        savings_plan_type=sp.get("savingsPlanType", ""),
                        payment_option=sp.get("paymentOption", ""),
                        term_duration=sp.get("termDurationInSeconds", ""),
                        state=sp.get("state", ""),
                        region=sp.get("region"),
                        start_time=datetime.fromisoformat(
                            sp.get("start", datetime.now().isoformat())
                        ),
                        end_time=datetime.fromisoformat(
                            sp.get("end", datetime.now().isoformat())
                        ),
                        commitment=Decimal(commitment_str),
                        instance_family=sp.get("ec2InstanceFamily"),
                    )
                )

        except Exception as e:
            logger.warning(f"Failed to fetch Savings Plans: {e}")

        return sps

    async def get_ri_utilization(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, float]:
        """Fetch RI utilization from Cost Explorer."""
        client = await self._get_client()

        try:
            response = await client.call(
                "ce",
                "get_reservation_utilization",
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Granularity="MONTHLY",
            )

            utilization: dict[str, float] = {}
            for item in response.get("UtilizationsByTime", []):
                total = item.get("Total", {})
                utilization["overall"] = float(total.get("UtilizationPercentage", 0))

            return utilization

        except Exception as e:
            logger.warning(f"Failed to fetch RI utilization: {e}")
            return {"overall": 0.0}

    async def get_sp_utilization(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """Fetch Savings Plan utilization."""
        client = await self._get_client()

        try:
            response = await client.call(
                "ce",
                "get_savings_plans_utilization",
                TimePeriod={
                    "Start": start_date.isoformat(),
                    "End": end_date.isoformat(),
                },
                Granularity="MONTHLY",
            )

            total = response.get("Total", {})
            utilization = total.get("Utilization", {})

            return {
                "utilization_percentage": float(
                    utilization.get("UtilizationPercentage", 0)
                ),
                "used_commitment": Decimal(str(utilization.get("UsedCommitment", 0))),
                "unused_commitment": Decimal(
                    str(utilization.get("UnusedCommitment", 0))
                ),
            }

        except Exception as e:
            logger.warning(f"Failed to fetch SP utilization: {e}")
            return {
                "utilization_percentage": 0.0,
                "used_commitment": Decimal("0"),
                "unused_commitment": Decimal("0"),
            }

    async def analyze(
        self,
        resources: list[dict[str, Any]] | None = None,
        lookback_days: int = 30,
    ) -> RIAwareAnalysis:
        """
        Perform complete RI/SP aware analysis.

        Args:
            resources: Optional list of resources to analyze for right-sizing
            lookback_days: Days of historical data to consider

        Returns:
            RIAwareAnalysis with complete results
        """
        today = date.today()
        start_date = today - timedelta(days=lookback_days)

        # Fetch inventory
        reserved_instances = await self.get_reserved_instances()
        savings_plans = await self.get_savings_plans()

        # Fetch utilization
        ri_util = await self.get_ri_utilization(start_date, today)
        sp_util = await self.get_sp_utilization(start_date, today)

        # Update RI utilization
        for ri in reserved_instances:
            ri.utilization_percentage = ri_util.get("overall", 0.0)

        # Update SP utilization
        for sp in savings_plans:
            sp.utilization_percentage = sp_util.get("utilization_percentage", 0.0)
            sp.used_commitment = sp_util.get("used_commitment", Decimal("0"))
            sp.unused_commitment = sp_util.get("unused_commitment", Decimal("0"))

        # Find expiring reservations
        expiring_ris = [ri for ri in reserved_instances if ri.is_expiring_soon]
        expiring_sps = [sp for sp in savings_plans if sp.is_expiring_soon]

        # Detect waste
        waste = self._detect_waste(reserved_instances, savings_plans)

        # Generate right-sizing recommendations if resources provided
        right_sizing: list[RightSizingRecommendation] = []
        if resources:
            engine = RIAwarePricingEngine(
                region=self.region,
                reserved_instances=reserved_instances,
                savings_plans=savings_plans,
            )
            right_sizing = self._generate_right_sizing(resources, engine)

        # Calculate totals
        total_ri_cost = sum(ri.monthly_cost for ri in reserved_instances)
        total_sp_cost = sum(sp.monthly_commitment for sp in savings_plans)
        total_waste = sum(w.monthly_waste for w in waste)
        total_savings = sum(r.monthly_savings for r in right_sizing)

        # Build warnings
        warnings: list[str] = []
        if expiring_ris:
            warnings.append(
                f"{len(expiring_ris)} Reserved Instance(s) expiring within 30 days"
            )
        if expiring_sps:
            warnings.append(
                f"{len(expiring_sps)} Savings Plan(s) expiring within 30 days"
            )
        if waste:
            warnings.append(f"{len(waste)} underutilized reservation(s) detected")

        return RIAwareAnalysis(
            analysis_date=today,
            region=self.region,
            reserved_instances=reserved_instances,
            savings_plans=savings_plans,
            coverage=ReservationCoverage(),  # Would need more data to populate
            right_sizing_recommendations=right_sizing,
            reservation_waste=waste,
            expiring_ris=expiring_ris,
            expiring_sps=expiring_sps,
            total_reservation_cost=total_ri_cost + total_sp_cost,
            total_waste=total_waste,
            total_potential_savings=total_savings,
            warnings=warnings,
        )

    def _detect_waste(
        self,
        ris: list[ReservedInstance],
        sps: list[SavingsPlanCommitment],
    ) -> list[ReservationWaste]:
        """Detect underutilized reservations."""
        waste: list[ReservationWaste] = []

        for ri in ris:
            if not ri.is_active:
                continue

            util_pct = ri.utilization_percentage

            if util_pct < 50:
                level = UtilizationLevel.CRITICAL
                monthly_waste = ri.monthly_cost * Decimal(str((100 - util_pct) / 100))
                recommendation = (
                    "Critical underutilization. Consider selling on RI Marketplace "
                    "or terminating unused instances."
                )
            elif util_pct < 70:
                level = UtilizationLevel.LOW
                monthly_waste = ri.monthly_cost * Decimal(str((100 - util_pct) / 100))
                recommendation = (
                    "Low utilization. Review running instances and optimize workloads."
                )
            elif util_pct < 90:
                level = UtilizationLevel.MEDIUM
                monthly_waste = ri.monthly_cost * Decimal(str((100 - util_pct) / 100))
                recommendation = "Moderate utilization. Minor optimization opportunity."
            else:
                continue  # Good utilization, no waste

            waste.append(
                ReservationWaste(
                    reservation_id=ri.reservation_id,
                    reservation_type=ReservationType.RESERVED_INSTANCE,
                    utilization_level=level,
                    utilization_percentage=util_pct,
                    monthly_waste=monthly_waste,
                    recommendation=recommendation,
                    details={
                        "instance_type": ri.instance_type,
                        "instance_count": ri.instance_count,
                    },
                )
            )

        for sp in sps:
            if not sp.is_active:
                continue

            util_pct = sp.utilization_percentage

            if util_pct < 50:
                level = UtilizationLevel.CRITICAL
                monthly_waste = sp.unused_commitment * Decimal("730")
                recommendation = "Critical underutilization. Commitment is too high for current usage."
            elif util_pct < 70:
                level = UtilizationLevel.LOW
                monthly_waste = sp.unused_commitment * Decimal("730")
                recommendation = (
                    "Low utilization. Consider increasing compute usage or "
                    "letting SP expire for lower commitment."
                )
            elif util_pct < 90:
                level = UtilizationLevel.MEDIUM
                monthly_waste = sp.unused_commitment * Decimal("730")
                recommendation = "Moderate utilization. Minor optimization opportunity."
            else:
                continue

            waste.append(
                ReservationWaste(
                    reservation_id=sp.savings_plan_id,
                    reservation_type=ReservationType(
                        f"savings_plan_{sp.savings_plan_type.lower()}"
                    )
                    if sp.savings_plan_type
                    else ReservationType.SAVINGS_PLAN_COMPUTE,
                    utilization_level=level,
                    utilization_percentage=util_pct,
                    monthly_waste=monthly_waste,
                    recommendation=recommendation,
                    details={
                        "savings_plan_type": sp.savings_plan_type,
                        "commitment": float(sp.commitment),
                    },
                )
            )

        return waste

    def _generate_right_sizing(
        self,
        resources: list[dict[str, Any]],
        engine: RIAwarePricingEngine,
    ) -> list[RightSizingRecommendation]:
        """Generate right-sizing recommendations with reservation awareness."""
        recommendations: list[RightSizingRecommendation] = []

        # Simple right-sizing rules based on instance type
        downsizing_map = {
            "t3.2xlarge": "t3.xlarge",
            "t3.xlarge": "t3.large",
            "t3.large": "t3.medium",
            "t3.medium": "t3.small",
            "m5.4xlarge": "m5.2xlarge",
            "m5.2xlarge": "m5.xlarge",
            "m5.xlarge": "m5.large",
            "r5.4xlarge": "r5.2xlarge",
            "r5.2xlarge": "r5.xlarge",
            "r5.xlarge": "r5.large",
        }

        for resource in resources:
            resource_type = resource.get("type", "")
            if resource_type not in ("aws_instance", "aws_db_instance"):
                continue

            resource_id = resource.get("id", "")
            resource_name = resource.get("name", resource_id)
            current_type = resource.get("instance_type") or resource.get(
                "instance_class", ""
            )
            region = resource.get("region", self.region)

            # Check if downsizing is possible
            if current_type not in downsizing_map:
                continue

            recommended_type = downsizing_map[current_type]

            # Check reservation impact
            impact = engine.get_right_sizing_impact(current_type, recommended_type)

            # Skip if constrained
            if impact.get("has_reservation") and not impact.get("can_proceed", True):
                recommendations.append(
                    RightSizingRecommendation(
                        resource_id=resource_id,
                        resource_type=resource_type,
                        resource_name=resource_name,
                        region=region,
                        current_instance_type=current_type,
                        current_monthly_cost=Decimal("0"),  # Would calculate
                        action=RightSizingAction.NO_CHANGE,
                        recommended_instance_type=None,
                        recommended_monthly_cost=Decimal("0"),
                        monthly_savings=Decimal("0"),
                        savings_percentage=0.0,
                        has_reservation=True,
                        reservation_id=impact.get("reservation_id"),
                        reservation_type=ReservationType(
                            impact.get("reservation_type", "reserved_instance")
                        ),
                        reservation_impact=impact.get("recommendation", ""),
                        is_reservation_constrained=True,
                        confidence="LOW",
                        rationale=[impact.get("recommendation", "")],
                    )
                )
                continue

            # Calculate costs
            current_price = engine.get_ec2_price(current_type)
            recommended_price = engine.get_ec2_price(recommended_type)

            current_monthly = current_price.to_monthly()
            recommended_monthly = recommended_price.to_monthly()
            monthly_savings = current_monthly - recommended_monthly
            savings_pct = (
                float(monthly_savings / current_monthly * 100)
                if current_monthly > 0
                else 0
            )

            rationale = ["Instance appears oversized based on type"]
            if impact.get("has_reservation"):
                rationale.append(impact.get("recommendation", ""))

            recommendations.append(
                RightSizingRecommendation(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    resource_name=resource_name,
                    region=region,
                    current_instance_type=current_type,
                    current_monthly_cost=current_monthly,
                    action=RightSizingAction.DOWNSIZE,
                    recommended_instance_type=recommended_type,
                    recommended_monthly_cost=recommended_monthly,
                    monthly_savings=monthly_savings,
                    savings_percentage=savings_pct,
                    has_reservation=impact.get("has_reservation", False),
                    reservation_id=impact.get("reservation_id"),
                    reservation_type=ReservationType(impact["reservation_type"])
                    if impact.get("reservation_type")
                    else None,
                    reservation_impact=impact.get("recommendation", ""),
                    is_reservation_constrained=False,
                    can_use_convertible=impact.get("can_use_convertible", False),
                    alternative_actions=impact.get("alternatives", []),
                    confidence="HIGH"
                    if not impact.get("has_reservation")
                    else "MEDIUM",
                    rationale=rationale,
                )
            )

        return recommendations


def get_utilization_level(percentage: float) -> UtilizationLevel:
    """Get utilization level from percentage."""
    if percentage >= 90:
        return UtilizationLevel.HIGH
    elif percentage >= 70:
        return UtilizationLevel.MEDIUM
    elif percentage >= 50:
        return UtilizationLevel.LOW
    else:
        return UtilizationLevel.CRITICAL


async def analyze_ri_sp_coverage(
    region: str = "us-east-1",
    resources: list[dict[str, Any]] | None = None,
    profile: str | None = None,
    credentials: dict[str, str] | None = None,
) -> RIAwareAnalysis:
    """
    Convenience function to analyze RI/SP coverage.

    Args:
        region: AWS region
        resources: Optional resources for right-sizing analysis
        profile: AWS profile name for credentials (deprecated, use credentials)
        credentials: Pre-resolved AWS credentials dict

    Returns:
        RIAwareAnalysis with complete results
    """
    async with RIAwareAnalyzer(
        region=region, profile=profile, credentials=credentials
    ) as analyzer:
        return await analyzer.analyze(resources=resources)
