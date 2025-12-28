"""
Savings Plans Analyzer.

Analyzes AWS usage patterns and provides recommendations
for Savings Plans purchases to optimize costs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any

from replimap.core.async_aws import AsyncAWSClient
from replimap.cost.explorer import CostExplorerClient, Granularity, MetricType

logger = logging.getLogger(__name__)


class SavingsPlanType(str, Enum):
    """Types of AWS Savings Plans."""

    COMPUTE = "ComputeSavingsPlans"
    EC2_INSTANCE = "EC2InstanceSavingsPlans"
    SAGEMAKER = "SageMakerSavingsPlans"

    def __str__(self) -> str:
        return self.value

    @property
    def description(self) -> str:
        """Get description of the savings plan type."""
        descriptions = {
            "ComputeSavingsPlans": (
                "Most flexible. Applies to EC2, Fargate, and Lambda. "
                "Works across instance families, sizes, OS, and regions."
            ),
            "EC2InstanceSavingsPlans": (
                "Lower discount than Compute SP. Applies to a specific "
                "instance family in a region (any size, OS, tenancy)."
            ),
            "SageMakerSavingsPlans": (
                "Applies to SageMaker instance usage. "
                "Works across instance families and regions."
            ),
        }
        return descriptions.get(self.value, "")


class PaymentOption(str, Enum):
    """Savings Plan payment options."""

    NO_UPFRONT = "No Upfront"
    PARTIAL_UPFRONT = "Partial Upfront"
    ALL_UPFRONT = "All Upfront"

    def __str__(self) -> str:
        return self.value

    @property
    def discount_factor(self) -> float:
        """Relative discount for each payment option."""
        factors = {
            "No Upfront": 1.0,
            "Partial Upfront": 0.95,
            "All Upfront": 0.90,
        }
        return factors.get(self.value, 1.0)


class Term(str, Enum):
    """Savings Plan term length."""

    ONE_YEAR = "1yr"
    THREE_YEAR = "3yr"

    def __str__(self) -> str:
        return self.value

    @property
    def discount_factor(self) -> float:
        """Relative discount for each term."""
        factors = {
            "1yr": 1.0,
            "3yr": 0.80,  # 3yr typically gives additional ~20% off
        }
        return factors.get(self.value, 1.0)


@dataclass
class UsagePattern:
    """Usage pattern for a service/resource type."""

    service: str
    region: str
    usage_type: str
    monthly_cost: float
    hourly_average: float
    peak_hourly: float
    low_hourly: float
    coverage_opportunity: float  # Percentage of steady-state usage
    variability: float  # Usage variability (0-1, lower is better for SP)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "region": self.region,
            "usage_type": self.usage_type,
            "monthly_cost": round(self.monthly_cost, 2),
            "hourly_average": round(self.hourly_average, 4),
            "peak_hourly": round(self.peak_hourly, 4),
            "low_hourly": round(self.low_hourly, 4),
            "coverage_opportunity": round(self.coverage_opportunity, 1),
            "variability": round(self.variability, 2),
        }


@dataclass
class SavingsPlanRecommendation:
    """Recommendation for a Savings Plan purchase."""

    plan_type: SavingsPlanType
    term: Term
    payment_option: PaymentOption
    hourly_commitment: float
    monthly_commitment: float

    # Savings
    estimated_monthly_savings: float
    estimated_annual_savings: float
    savings_percentage: float

    # Coverage
    current_coverage: float  # Current SP coverage (0-100%)
    new_coverage: float  # Coverage with this recommendation

    # Confidence
    confidence: str  # HIGH, MEDIUM, LOW
    rationale: list[str] = field(default_factory=list)

    # Affected services
    covered_services: list[str] = field(default_factory=list)
    covered_regions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "plan_type": str(self.plan_type),
            "plan_description": self.plan_type.description,
            "term": str(self.term),
            "payment_option": str(self.payment_option),
            "commitment": {
                "hourly": round(self.hourly_commitment, 4),
                "monthly": round(self.monthly_commitment, 2),
            },
            "savings": {
                "monthly": round(self.estimated_monthly_savings, 2),
                "annual": round(self.estimated_annual_savings, 2),
                "percentage": round(self.savings_percentage, 1),
            },
            "coverage": {
                "current": round(self.current_coverage, 1),
                "projected": round(self.new_coverage, 1),
            },
            "confidence": self.confidence,
            "rationale": self.rationale,
            "covered_services": self.covered_services,
            "covered_regions": self.covered_regions,
        }


@dataclass
class SavingsPlansAnalysis:
    """Complete Savings Plans analysis results."""

    analysis_date: date
    lookback_days: int

    # Current state
    current_on_demand_cost: float
    current_savings_plan_coverage: float
    current_savings_plan_cost: float
    current_monthly_spend: float

    # Usage patterns
    usage_patterns: list[UsagePattern] = field(default_factory=list)

    # Recommendations
    recommendations: list[SavingsPlanRecommendation] = field(default_factory=list)

    # Totals
    total_potential_savings: float = 0.0
    optimal_commitment: float = 0.0

    # Metadata
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "lookback_days": self.lookback_days,
            "current_state": {
                "on_demand_cost": round(self.current_on_demand_cost, 2),
                "savings_plan_coverage": round(self.current_savings_plan_coverage, 1),
                "savings_plan_cost": round(self.current_savings_plan_cost, 2),
                "monthly_spend": round(self.current_monthly_spend, 2),
            },
            "usage_patterns": [up.to_dict() for up in self.usage_patterns],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "summary": {
                "total_potential_savings": round(self.total_potential_savings, 2),
                "optimal_commitment": round(self.optimal_commitment, 2),
            },
            "warnings": self.warnings,
        }


# Discount rates for Savings Plans (approximate, based on AWS documentation)
SAVINGS_PLAN_DISCOUNTS = {
    SavingsPlanType.COMPUTE: {
        Term.ONE_YEAR: {
            PaymentOption.NO_UPFRONT: 0.22,
            PaymentOption.PARTIAL_UPFRONT: 0.26,
            PaymentOption.ALL_UPFRONT: 0.28,
        },
        Term.THREE_YEAR: {
            PaymentOption.NO_UPFRONT: 0.40,
            PaymentOption.PARTIAL_UPFRONT: 0.46,
            PaymentOption.ALL_UPFRONT: 0.50,
        },
    },
    SavingsPlanType.EC2_INSTANCE: {
        Term.ONE_YEAR: {
            PaymentOption.NO_UPFRONT: 0.30,
            PaymentOption.PARTIAL_UPFRONT: 0.34,
            PaymentOption.ALL_UPFRONT: 0.36,
        },
        Term.THREE_YEAR: {
            PaymentOption.NO_UPFRONT: 0.52,
            PaymentOption.PARTIAL_UPFRONT: 0.56,
            PaymentOption.ALL_UPFRONT: 0.60,
        },
    },
}


class SavingsPlansAnalyzer:
    """
    Analyzes usage patterns and recommends Savings Plans.

    Uses historical cost data to identify steady-state usage
    patterns suitable for Savings Plans commitments.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
    ) -> None:
        """
        Initialize analyzer.

        Args:
            region: AWS region
            account_id: AWS account ID
        """
        self.region = region
        self.account_id = account_id
        self._client: AsyncAWSClient | None = None
        self._ce_client: CostExplorerClient | None = None

    async def _get_ce_client(self) -> CostExplorerClient:
        """Get Cost Explorer client."""
        if self._ce_client is None:
            self._ce_client = CostExplorerClient(
                region=self.region,
                account_id=self.account_id,
            )
        return self._ce_client

    async def analyze(
        self,
        lookback_days: int = 30,
        risk_tolerance: str = "medium",
    ) -> SavingsPlansAnalysis:
        """
        Analyze usage patterns and generate recommendations.

        Args:
            lookback_days: Number of days of historical data to analyze
            risk_tolerance: Risk tolerance level (low, medium, high)

        Returns:
            SavingsPlansAnalysis with recommendations
        """
        today = date.today()
        start_date = today - timedelta(days=lookback_days)

        ce_client = await self._get_ce_client()

        # Get cost data
        cost_data = await ce_client.get_cost_and_usage(
            start_date=start_date,
            end_date=today,
            granularity=Granularity.DAILY,
            metrics=[MetricType.UNBLENDED_COST],
        )

        # Get service breakdown
        service_data = await ce_client.get_cost_by_service(
            start_date=start_date,
            end_date=today,
            granularity=Granularity.DAILY,
        )

        # Analyze usage patterns
        usage_patterns = self._analyze_patterns(service_data)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            usage_patterns,
            risk_tolerance,
        )

        # Calculate totals
        total_savings = sum(r.estimated_monthly_savings for r in recommendations)
        optimal_commitment = sum(r.monthly_commitment for r in recommendations)

        return SavingsPlansAnalysis(
            analysis_date=today,
            lookback_days=lookback_days,
            current_on_demand_cost=cost_data.total_cost,
            current_savings_plan_coverage=0.0,  # Would need SP API
            current_savings_plan_cost=0.0,
            current_monthly_spend=cost_data.total_cost,
            usage_patterns=usage_patterns,
            recommendations=recommendations,
            total_potential_savings=total_savings,
            optimal_commitment=optimal_commitment,
        )

    def _analyze_patterns(
        self,
        service_data: Any,
    ) -> list[UsagePattern]:
        """Analyze usage patterns from cost data."""
        patterns = []

        # Services eligible for Compute Savings Plans
        compute_services = {
            "Amazon Elastic Compute Cloud - Compute",
            "AWS Lambda",
            "Amazon Elastic Container Service",
            "AWS Fargate",
        }

        for grouped_cost in service_data.grouped_costs:
            service = grouped_cost.group_value

            # Skip non-compute services for SP analysis
            if not any(s in service for s in compute_services):
                continue

            if not grouped_cost.data_points:
                continue

            # Calculate statistics
            costs = [dp.amount for dp in grouped_cost.data_points]
            avg_daily = sum(costs) / len(costs) if costs else 0
            peak_daily = max(costs) if costs else 0
            low_daily = min(costs) if costs else 0

            # Calculate variability (coefficient of variation)
            mean = avg_daily
            if mean > 0 and len(costs) > 1:
                variance = sum((c - mean) ** 2 for c in costs) / len(costs)
                std_dev = variance**0.5
                variability = std_dev / mean
            else:
                variability = 0

            # Coverage opportunity is the steady-state portion
            # (low / avg indicates stable base)
            if avg_daily > 0:
                coverage_opportunity = (low_daily / avg_daily) * 100
            else:
                coverage_opportunity = 0

            patterns.append(
                UsagePattern(
                    service=service,
                    region=self.region,
                    usage_type="compute",
                    monthly_cost=avg_daily * 30,
                    hourly_average=avg_daily / 24,
                    peak_hourly=peak_daily / 24,
                    low_hourly=low_daily / 24,
                    coverage_opportunity=coverage_opportunity,
                    variability=variability,
                )
            )

        # Sort by monthly cost (descending)
        patterns.sort(key=lambda x: x.monthly_cost, reverse=True)

        return patterns

    def _generate_recommendations(
        self,
        usage_patterns: list[UsagePattern],
        risk_tolerance: str,
    ) -> list[SavingsPlanRecommendation]:
        """Generate Savings Plan recommendations."""
        recommendations: list[SavingsPlanRecommendation] = []

        # Calculate total eligible compute cost
        total_compute_cost = sum(up.monthly_cost for up in usage_patterns)

        if total_compute_cost == 0:
            return recommendations

        # Determine coverage target based on risk tolerance
        coverage_targets = {
            "low": 0.50,  # Cover 50% of usage
            "medium": 0.70,  # Cover 70% of usage
            "high": 0.85,  # Cover 85% of usage
        }
        coverage_target = coverage_targets.get(risk_tolerance, 0.70)

        # Calculate recommended commitment
        # Use the minimum usage across all patterns as base
        min_usage_pct = min(
            (up.coverage_opportunity / 100 for up in usage_patterns),
            default=0.5,
        )

        # Adjust based on risk tolerance
        commitment_pct = min(min_usage_pct, coverage_target)
        hourly_commitment = (
            total_compute_cost / 720
        ) * commitment_pct  # 720 hours/month

        # Generate recommendation for Compute SP (most flexible)
        discount = SAVINGS_PLAN_DISCOUNTS[SavingsPlanType.COMPUTE][Term.ONE_YEAR][
            PaymentOption.NO_UPFRONT
        ]

        monthly_commitment = hourly_commitment * 720
        monthly_savings = monthly_commitment * discount

        rationale = []
        if min_usage_pct >= 0.7:
            rationale.append("Usage patterns show consistent baseline")
            confidence = "HIGH"
        elif min_usage_pct >= 0.4:
            rationale.append("Usage shows moderate variability")
            confidence = "MEDIUM"
        else:
            rationale.append("High usage variability - conservative recommendation")
            confidence = "LOW"

        rationale.append(f"Based on {len(usage_patterns)} compute services")
        rationale.append(f"Coverage target: {coverage_target * 100:.0f}%")

        if hourly_commitment > 0.01:  # Only recommend if meaningful
            recommendations.append(
                SavingsPlanRecommendation(
                    plan_type=SavingsPlanType.COMPUTE,
                    term=Term.ONE_YEAR,
                    payment_option=PaymentOption.NO_UPFRONT,
                    hourly_commitment=hourly_commitment,
                    monthly_commitment=monthly_commitment,
                    estimated_monthly_savings=monthly_savings,
                    estimated_annual_savings=monthly_savings * 12,
                    savings_percentage=discount * 100,
                    current_coverage=0.0,
                    new_coverage=commitment_pct * 100,
                    confidence=confidence,
                    rationale=rationale,
                    covered_services=[up.service for up in usage_patterns],
                    covered_regions=[self.region],
                )
            )

            # Also recommend 3-year if significant savings
            if total_compute_cost > 1000:  # $1000/month threshold
                discount_3yr = SAVINGS_PLAN_DISCOUNTS[SavingsPlanType.COMPUTE][
                    Term.THREE_YEAR
                ][PaymentOption.NO_UPFRONT]

                recommendations.append(
                    SavingsPlanRecommendation(
                        plan_type=SavingsPlanType.COMPUTE,
                        term=Term.THREE_YEAR,
                        payment_option=PaymentOption.NO_UPFRONT,
                        hourly_commitment=hourly_commitment,
                        monthly_commitment=monthly_commitment,
                        estimated_monthly_savings=monthly_commitment * discount_3yr,
                        estimated_annual_savings=monthly_commitment * discount_3yr * 12,
                        savings_percentage=discount_3yr * 100,
                        current_coverage=0.0,
                        new_coverage=commitment_pct * 100,
                        confidence=confidence,
                        rationale=[
                            "3-year term offers larger discount",
                            "Suitable for stable, long-term workloads",
                        ],
                        covered_services=[up.service for up in usage_patterns],
                        covered_regions=[self.region],
                    )
                )

        return recommendations


async def get_savings_plan_coverage(
    client: AsyncAWSClient,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Get current Savings Plan coverage.

    Args:
        client: AsyncAWSClient instance
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with coverage information
    """
    params = {
        "TimePeriod": {
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        "Granularity": "MONTHLY",
    }

    try:
        response = await client.call("ce", "get_savings_plans_coverage", **params)

        coverages = response.get("SavingsPlansCoverages", [])
        total_coverage = 0.0
        count = 0

        for coverage in coverages:
            attrs = coverage.get("Coverage", {})
            pct = float(attrs.get("CoveragePercentage", 0))
            total_coverage += pct
            count += 1

        return {
            "average_coverage": total_coverage / count if count > 0 else 0,
            "periods": count,
            "details": coverages,
        }
    except Exception as e:
        logger.error(f"Failed to get SP coverage: {e}")
        return {"average_coverage": 0, "periods": 0, "details": [], "error": str(e)}


async def get_savings_plan_utilization(
    client: AsyncAWSClient,
    start_date: date,
    end_date: date,
) -> dict[str, Any]:
    """
    Get Savings Plan utilization.

    Args:
        client: AsyncAWSClient instance
        start_date: Start of period
        end_date: End of period

    Returns:
        Dictionary with utilization information
    """
    params = {
        "TimePeriod": {
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        "Granularity": "MONTHLY",
    }

    try:
        response = await client.call("ce", "get_savings_plans_utilization", **params)

        total = response.get("Total", {})
        utilization = total.get("Utilization", {})

        return {
            "utilization_percentage": float(
                utilization.get("UtilizationPercentage", 0)
            ),
            "total_commitment": float(utilization.get("TotalCommitment", 0)),
            "used_commitment": float(utilization.get("UsedCommitment", 0)),
            "unused_commitment": float(utilization.get("UnusedCommitment", 0)),
        }
    except Exception as e:
        logger.error(f"Failed to get SP utilization: {e}")
        return {
            "utilization_percentage": 0,
            "total_commitment": 0,
            "used_commitment": 0,
            "unused_commitment": 0,
            "error": str(e),
        }
