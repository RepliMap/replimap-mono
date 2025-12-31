"""
Local Right-Sizer Rule Engine.

Provides offline right-sizing recommendations using rule-based logic.
This serves as a fallback when the API is unavailable and enables
truly autonomous operation per the Seven Laws of Sovereign Code.

Features:
- EC2 instance downgrade paths for staging environments
- RDS instance class optimization
- ElastiCache node type recommendations
- Approximate pricing for savings calculations
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Strategy for right-sizing recommendations."""

    CONSERVATIVE = "conservative"  # Safe downsizes, high confidence
    BALANCED = "balanced"  # Moderate savings, medium confidence
    AGGRESSIVE = "aggressive"  # Maximum savings, lower confidence


@dataclass
class LocalRecommendation:
    """A single right-sizing recommendation from local rules."""

    resource_id: str
    resource_type: str
    current_instance: str
    recommended_instance: str
    monthly_savings: float
    annual_savings: float
    confidence: float  # 0.0 - 1.0
    rationale: str
    savings_percentage: float = 0.0

    def __post_init__(self) -> None:
        """Calculate derived fields."""
        self.annual_savings = self.monthly_savings * 12


# =============================================================================
# EC2 Instance Pricing (On-Demand, us-east-1, USD/hour)
# These are approximate values for savings calculation
# =============================================================================
EC2_PRICING: dict[str, float] = {
    # M5 General Purpose
    "m5.large": 0.096,
    "m5.xlarge": 0.192,
    "m5.2xlarge": 0.384,
    "m5.4xlarge": 0.768,
    "m5.8xlarge": 1.536,
    "m5.12xlarge": 2.304,
    "m5.16xlarge": 3.072,
    "m5.24xlarge": 4.608,
    # M6i General Purpose (newer)
    "m6i.large": 0.096,
    "m6i.xlarge": 0.192,
    "m6i.2xlarge": 0.384,
    "m6i.4xlarge": 0.768,
    # T3 Burstable
    "t3.micro": 0.0104,
    "t3.small": 0.0208,
    "t3.medium": 0.0416,
    "t3.large": 0.0832,
    "t3.xlarge": 0.1664,
    "t3.2xlarge": 0.3328,
    # T3a (AMD)
    "t3a.micro": 0.0094,
    "t3a.small": 0.0188,
    "t3a.medium": 0.0376,
    "t3a.large": 0.0752,
    "t3a.xlarge": 0.1504,
    "t3a.2xlarge": 0.3008,
    # R5 Memory Optimized
    "r5.large": 0.126,
    "r5.xlarge": 0.252,
    "r5.2xlarge": 0.504,
    "r5.4xlarge": 1.008,
    "r5.8xlarge": 2.016,
    "r5.12xlarge": 3.024,
    # R6i Memory Optimized (newer)
    "r6i.large": 0.126,
    "r6i.xlarge": 0.252,
    "r6i.2xlarge": 0.504,
    # C5 Compute Optimized
    "c5.large": 0.085,
    "c5.xlarge": 0.17,
    "c5.2xlarge": 0.34,
    "c5.4xlarge": 0.68,
    "c5.9xlarge": 1.53,
    # C6i Compute Optimized (newer)
    "c6i.large": 0.085,
    "c6i.xlarge": 0.17,
    "c6i.2xlarge": 0.34,
}

# Hours per month for cost calculation
HOURS_PER_MONTH = 730

# =============================================================================
# RDS Instance Pricing (On-Demand, us-east-1, USD/hour, Single-AZ)
# =============================================================================
RDS_PRICING: dict[str, float] = {
    # db.t3 Burstable
    "db.t3.micro": 0.017,
    "db.t3.small": 0.034,
    "db.t3.medium": 0.068,
    "db.t3.large": 0.136,
    "db.t3.xlarge": 0.272,
    "db.t3.2xlarge": 0.544,
    # db.t4g (Graviton, cheaper)
    "db.t4g.micro": 0.016,
    "db.t4g.small": 0.032,
    "db.t4g.medium": 0.065,
    "db.t4g.large": 0.129,
    # db.m5 General Purpose
    "db.m5.large": 0.171,
    "db.m5.xlarge": 0.342,
    "db.m5.2xlarge": 0.684,
    "db.m5.4xlarge": 1.368,
    # db.m6i General Purpose (newer)
    "db.m6i.large": 0.171,
    "db.m6i.xlarge": 0.342,
    "db.m6i.2xlarge": 0.684,
    # db.r5 Memory Optimized
    "db.r5.large": 0.24,
    "db.r5.xlarge": 0.48,
    "db.r5.2xlarge": 0.96,
    "db.r5.4xlarge": 1.92,
    # db.r6i Memory Optimized (newer)
    "db.r6i.large": 0.24,
    "db.r6i.xlarge": 0.48,
    "db.r6i.2xlarge": 0.96,
}

# =============================================================================
# ElastiCache Node Pricing (On-Demand, us-east-1, USD/hour)
# =============================================================================
ELASTICACHE_PRICING: dict[str, float] = {
    # cache.t3
    "cache.t3.micro": 0.017,
    "cache.t3.small": 0.034,
    "cache.t3.medium": 0.068,
    # cache.t4g (Graviton)
    "cache.t4g.micro": 0.016,
    "cache.t4g.small": 0.032,
    "cache.t4g.medium": 0.065,
    # cache.m5
    "cache.m5.large": 0.142,
    "cache.m5.xlarge": 0.284,
    "cache.m5.2xlarge": 0.568,
    # cache.r5
    "cache.r5.large": 0.228,
    "cache.r5.xlarge": 0.456,
    "cache.r5.2xlarge": 0.912,
    # cache.r6g (Graviton)
    "cache.r6g.large": 0.205,
    "cache.r6g.xlarge": 0.41,
    "cache.r6g.2xlarge": 0.82,
}

# =============================================================================
# Downgrade Rules by Strategy
# Format: { current_type: (recommended_type, confidence) }
# =============================================================================

EC2_RULES: dict[str, dict[str, tuple[str, float]]] = {
    "conservative": {
        # M5 -> one size down
        "m5.24xlarge": ("m5.16xlarge", 0.90),
        "m5.16xlarge": ("m5.12xlarge", 0.90),
        "m5.12xlarge": ("m5.8xlarge", 0.90),
        "m5.8xlarge": ("m5.4xlarge", 0.90),
        "m5.4xlarge": ("m5.2xlarge", 0.90),
        "m5.2xlarge": ("m5.xlarge", 0.85),
        "m5.xlarge": ("m5.large", 0.85),
        "m5.large": ("t3.large", 0.75),
        # M6i -> one size down
        "m6i.4xlarge": ("m6i.2xlarge", 0.90),
        "m6i.2xlarge": ("m6i.xlarge", 0.85),
        "m6i.xlarge": ("m6i.large", 0.85),
        # R5 Memory -> one size down
        "r5.12xlarge": ("r5.8xlarge", 0.90),
        "r5.8xlarge": ("r5.4xlarge", 0.90),
        "r5.4xlarge": ("r5.2xlarge", 0.90),
        "r5.2xlarge": ("r5.xlarge", 0.85),
        "r5.xlarge": ("r5.large", 0.85),
        # C5 Compute -> one size down
        "c5.9xlarge": ("c5.4xlarge", 0.90),
        "c5.4xlarge": ("c5.2xlarge", 0.90),
        "c5.2xlarge": ("c5.xlarge", 0.85),
        "c5.xlarge": ("c5.large", 0.85),
        # T3 -> T3a (AMD, cheaper)
        "t3.2xlarge": ("t3a.2xlarge", 0.90),
        "t3.xlarge": ("t3a.xlarge", 0.90),
        "t3.large": ("t3a.large", 0.90),
        "t3.medium": ("t3a.medium", 0.90),
    },
    "balanced": {
        # M5 -> two sizes down or to T3
        "m5.4xlarge": ("m5.xlarge", 0.75),
        "m5.2xlarge": ("t3.xlarge", 0.70),
        "m5.xlarge": ("t3.large", 0.70),
        "m5.large": ("t3.medium", 0.65),
        # R5 -> one to two sizes down
        "r5.4xlarge": ("r5.xlarge", 0.75),
        "r5.2xlarge": ("r5.large", 0.70),
        "r5.xlarge": ("t3.xlarge", 0.65),
        # C5 -> more aggressive
        "c5.4xlarge": ("c5.xlarge", 0.75),
        "c5.2xlarge": ("c5.large", 0.70),
    },
    "aggressive": {
        # M5 -> T3 burstable (significant savings)
        "m5.4xlarge": ("t3.xlarge", 0.55),
        "m5.2xlarge": ("t3.large", 0.55),
        "m5.xlarge": ("t3.medium", 0.50),
        "m5.large": ("t3.small", 0.45),
        # R5 -> T3 (may not have enough memory)
        "r5.2xlarge": ("t3.xlarge", 0.50),
        "r5.xlarge": ("t3.large", 0.45),
        "r5.large": ("t3.medium", 0.40),
        # C5 -> T3
        "c5.2xlarge": ("t3.xlarge", 0.55),
        "c5.xlarge": ("t3.large", 0.50),
    },
}

RDS_RULES: dict[str, dict[str, tuple[str, float]]] = {
    "conservative": {
        # db.r5 -> one size down
        "db.r5.4xlarge": ("db.r5.2xlarge", 0.90),
        "db.r5.2xlarge": ("db.r5.xlarge", 0.85),
        "db.r5.xlarge": ("db.r5.large", 0.85),
        # db.m5 -> one size down
        "db.m5.4xlarge": ("db.m5.2xlarge", 0.90),
        "db.m5.2xlarge": ("db.m5.xlarge", 0.85),
        "db.m5.xlarge": ("db.m5.large", 0.85),
        "db.m5.large": ("db.t3.large", 0.75),
        # db.r6i -> one size down
        "db.r6i.2xlarge": ("db.r6i.xlarge", 0.85),
        "db.r6i.xlarge": ("db.r6i.large", 0.85),
        # db.t3 -> db.t4g (Graviton, 10% cheaper)
        "db.t3.2xlarge": ("db.t4g.large", 0.80),
        "db.t3.xlarge": ("db.t4g.large", 0.85),
        "db.t3.large": ("db.t4g.medium", 0.85),
        "db.t3.medium": ("db.t4g.small", 0.85),
    },
    "balanced": {
        # db.r5 -> two sizes down or to db.m5
        "db.r5.4xlarge": ("db.r5.xlarge", 0.70),
        "db.r5.2xlarge": ("db.m5.xlarge", 0.65),
        "db.r5.xlarge": ("db.m5.large", 0.65),
        # db.m5 -> db.t3
        "db.m5.2xlarge": ("db.t3.xlarge", 0.65),
        "db.m5.xlarge": ("db.t3.large", 0.65),
    },
    "aggressive": {
        # db.r5 -> db.t3 (may hit memory limits)
        "db.r5.2xlarge": ("db.t3.xlarge", 0.50),
        "db.r5.xlarge": ("db.t3.large", 0.45),
        "db.r5.large": ("db.t3.medium", 0.40),
        # db.m5 -> db.t3 small
        "db.m5.xlarge": ("db.t3.medium", 0.50),
        "db.m5.large": ("db.t3.small", 0.45),
    },
}

ELASTICACHE_RULES: dict[str, dict[str, tuple[str, float]]] = {
    "conservative": {
        # cache.r5 -> cache.r6g (Graviton, 10% cheaper)
        "cache.r5.2xlarge": ("cache.r6g.2xlarge", 0.90),
        "cache.r5.xlarge": ("cache.r6g.xlarge", 0.90),
        "cache.r5.large": ("cache.r6g.large", 0.90),
        # cache.m5 -> one size down
        "cache.m5.2xlarge": ("cache.m5.xlarge", 0.85),
        "cache.m5.xlarge": ("cache.m5.large", 0.85),
        "cache.m5.large": ("cache.t3.medium", 0.75),
        # cache.t3 -> cache.t4g (Graviton)
        "cache.t3.medium": ("cache.t4g.medium", 0.90),
        "cache.t3.small": ("cache.t4g.small", 0.90),
    },
    "balanced": {
        # cache.r5 -> cache.m5 (less memory)
        "cache.r5.2xlarge": ("cache.m5.xlarge", 0.65),
        "cache.r5.xlarge": ("cache.m5.large", 0.65),
        # cache.m5 -> cache.t3
        "cache.m5.xlarge": ("cache.t3.medium", 0.60),
    },
    "aggressive": {
        # cache.r5 -> cache.t3 (significant downgrade)
        "cache.r5.xlarge": ("cache.t3.medium", 0.45),
        "cache.r5.large": ("cache.t3.small", 0.40),
        # cache.m5 -> cache.t3 small
        "cache.m5.large": ("cache.t3.small", 0.45),
    },
}


class LocalRightSizer:
    """
    Local rule-based right-sizing engine.

    Provides offline recommendations for staging/dev environments
    based on predefined downgrade paths and pricing data.
    """

    def __init__(
        self, strategy: OptimizationStrategy = OptimizationStrategy.CONSERVATIVE
    ) -> None:
        """Initialize with optimization strategy."""
        self.strategy = strategy

    def analyze(self, resources: list[dict[str, Any]]) -> list[LocalRecommendation]:
        """
        Analyze resources and return right-sizing recommendations.

        Args:
            resources: List of resource dicts with keys:
                - id: Resource identifier
                - type: Resource type (ec2, rds, etc.)
                - instance_type: Current instance type

        Returns:
            List of recommendations sorted by savings (descending)
        """
        recommendations: list[LocalRecommendation] = []

        for resource in resources:
            rec = self._analyze_resource(resource)
            if rec:
                recommendations.append(rec)

        # Sort by monthly savings descending
        return sorted(recommendations, key=lambda r: r.monthly_savings, reverse=True)

    def _analyze_resource(
        self, resource: dict[str, Any]
    ) -> LocalRecommendation | None:
        """Analyze a single resource."""
        resource_type = resource.get("resource_type", resource.get("type", "")).lower()
        instance_type = resource.get("instance_type", resource.get("instance_class", ""))

        if not instance_type:
            return None

        # Route to appropriate analyzer
        if "ec2" in resource_type or resource_type in ("instance", "aws_instance"):
            return self._analyze_ec2(resource, instance_type)
        elif "rds" in resource_type or "db_instance" in resource_type:
            return self._analyze_rds(resource, instance_type)
        elif "elasticache" in resource_type or "cache" in resource_type:
            return self._analyze_elasticache(resource, instance_type)

        return None

    def _analyze_ec2(
        self, resource: dict[str, Any], instance_type: str
    ) -> LocalRecommendation | None:
        """Analyze EC2 instance."""
        rules = EC2_RULES.get(self.strategy.value, {})

        if instance_type not in rules:
            logger.debug(f"No EC2 rule for {instance_type} with {self.strategy.value}")
            return None

        target, confidence = rules[instance_type]
        current_price = EC2_PRICING.get(instance_type, 0)
        target_price = EC2_PRICING.get(target, 0)

        if current_price == 0:
            logger.debug(f"No pricing data for {instance_type}")
            return None

        monthly_savings = (current_price - target_price) * HOURS_PER_MONTH
        savings_pct = (
            (monthly_savings / (current_price * HOURS_PER_MONTH)) * 100
            if current_price > 0
            else 0
        )

        return LocalRecommendation(
            resource_id=resource.get("id", resource.get("resource_id", "unknown")),
            resource_type="aws_instance",
            current_instance=instance_type,
            recommended_instance=target,
            monthly_savings=round(monthly_savings, 2),
            annual_savings=round(monthly_savings * 12, 2),
            confidence=confidence,
            savings_percentage=round(savings_pct, 1),
            rationale=f"Downsize from {instance_type} to {target} ({self.strategy.value} strategy)",
        )

    def _analyze_rds(
        self, resource: dict[str, Any], instance_type: str
    ) -> LocalRecommendation | None:
        """Analyze RDS instance."""
        rules = RDS_RULES.get(self.strategy.value, {})

        if instance_type not in rules:
            logger.debug(f"No RDS rule for {instance_type} with {self.strategy.value}")
            return None

        target, confidence = rules[instance_type]
        current_price = RDS_PRICING.get(instance_type, 0)
        target_price = RDS_PRICING.get(target, 0)

        if current_price == 0:
            logger.debug(f"No pricing data for {instance_type}")
            return None

        monthly_savings = (current_price - target_price) * HOURS_PER_MONTH
        savings_pct = (
            (monthly_savings / (current_price * HOURS_PER_MONTH)) * 100
            if current_price > 0
            else 0
        )

        return LocalRecommendation(
            resource_id=resource.get("id", resource.get("resource_id", "unknown")),
            resource_type="aws_db_instance",
            current_instance=instance_type,
            recommended_instance=target,
            monthly_savings=round(monthly_savings, 2),
            annual_savings=round(monthly_savings * 12, 2),
            confidence=confidence,
            savings_percentage=round(savings_pct, 1),
            rationale=f"Downsize from {instance_type} to {target} ({self.strategy.value} strategy)",
        )

    def _analyze_elasticache(
        self, resource: dict[str, Any], instance_type: str
    ) -> LocalRecommendation | None:
        """Analyze ElastiCache node."""
        rules = ELASTICACHE_RULES.get(self.strategy.value, {})

        # Normalize node_type to instance_type key
        node_type = instance_type

        if node_type not in rules:
            logger.debug(
                f"No ElastiCache rule for {node_type} with {self.strategy.value}"
            )
            return None

        target, confidence = rules[node_type]
        current_price = ELASTICACHE_PRICING.get(node_type, 0)
        target_price = ELASTICACHE_PRICING.get(target, 0)

        if current_price == 0:
            logger.debug(f"No pricing data for {node_type}")
            return None

        monthly_savings = (current_price - target_price) * HOURS_PER_MONTH
        savings_pct = (
            (monthly_savings / (current_price * HOURS_PER_MONTH)) * 100
            if current_price > 0
            else 0
        )

        return LocalRecommendation(
            resource_id=resource.get("id", resource.get("resource_id", "unknown")),
            resource_type="aws_elasticache_cluster",
            current_instance=node_type,
            recommended_instance=target,
            monthly_savings=round(monthly_savings, 2),
            annual_savings=round(monthly_savings * 12, 2),
            confidence=confidence,
            savings_percentage=round(savings_pct, 1),
            rationale=f"Downsize from {node_type} to {target} ({self.strategy.value} strategy)",
        )

    def get_total_savings(
        self, recommendations: list[LocalRecommendation]
    ) -> dict[str, float]:
        """Calculate total savings from recommendations."""
        total_monthly = sum(r.monthly_savings for r in recommendations)
        total_annual = sum(r.annual_savings for r in recommendations)
        avg_confidence = (
            sum(r.confidence for r in recommendations) / len(recommendations)
            if recommendations
            else 0.0
        )

        return {
            "monthly_savings": round(total_monthly, 2),
            "annual_savings": round(total_annual, 2),
            "resource_count": len(recommendations),
            "average_confidence": round(avg_confidence, 2),
        }
