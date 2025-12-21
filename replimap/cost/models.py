"""
Cost Estimator data models.

Models for representing cost analysis results for AWS infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PricingTier(str, Enum):
    """AWS pricing tiers."""

    ON_DEMAND = "ON_DEMAND"  # Pay as you go
    RESERVED_1Y = "RESERVED_1Y"  # 1-year reserved
    RESERVED_3Y = "RESERVED_3Y"  # 3-year reserved
    SPOT = "SPOT"  # Spot instances
    SAVINGS_PLAN = "SAVINGS_PLAN"  # Savings plan

    def __str__(self) -> str:
        return self.value


class CostCategory(str, Enum):
    """Cost categories for grouping."""

    COMPUTE = "COMPUTE"  # EC2, Lambda, ECS, EKS
    DATABASE = "DATABASE"  # RDS, DynamoDB, ElastiCache
    STORAGE = "STORAGE"  # S3, EBS, EFS
    NETWORK = "NETWORK"  # VPC, NAT Gateway, Load Balancer
    SECURITY = "SECURITY"  # IAM, KMS, WAF
    MONITORING = "MONITORING"  # CloudWatch, X-Ray
    OTHER = "OTHER"  # Everything else

    def __str__(self) -> str:
        return self.value


class CostConfidence(str, Enum):
    """Confidence level of cost estimates."""

    HIGH = "HIGH"  # Well-known pricing, standard config
    MEDIUM = "MEDIUM"  # Some assumptions made
    LOW = "LOW"  # Many assumptions, limited data
    UNKNOWN = "UNKNOWN"  # Cannot estimate

    def __str__(self) -> str:
        return self.value


@dataclass
class ResourceCost:
    """Cost estimate for a single resource."""

    resource_id: str
    resource_type: str
    resource_name: str

    # Cost breakdown
    monthly_cost: float = 0.0  # Total monthly cost in USD
    hourly_cost: float = 0.0  # Hourly cost
    annual_cost: float = 0.0  # Projected annual cost

    # Categorization
    category: CostCategory = CostCategory.OTHER
    pricing_tier: PricingTier = PricingTier.ON_DEMAND

    # Cost components
    compute_cost: float = 0.0  # CPU/memory
    storage_cost: float = 0.0  # Disk/storage
    network_cost: float = 0.0  # Data transfer
    other_cost: float = 0.0  # Other charges

    # Metadata
    instance_type: str = ""  # e.g., t3.medium, db.r5.large
    region: str = ""
    confidence: CostConfidence = CostConfidence.MEDIUM
    assumptions: list[str] = field(default_factory=list)

    # Optimization
    optimization_potential: float = 0.0  # Potential savings %
    optimization_tips: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "monthly_cost": round(self.monthly_cost, 2),
            "hourly_cost": round(self.hourly_cost, 4),
            "annual_cost": round(self.annual_cost, 2),
            "category": self.category.value,
            "pricing_tier": self.pricing_tier.value,
            "cost_breakdown": {
                "compute": round(self.compute_cost, 2),
                "storage": round(self.storage_cost, 2),
                "network": round(self.network_cost, 2),
                "other": round(self.other_cost, 2),
            },
            "instance_type": self.instance_type,
            "region": self.region,
            "confidence": self.confidence.value,
            "assumptions": self.assumptions,
            "optimization_potential": round(self.optimization_potential, 1),
            "optimization_tips": self.optimization_tips,
        }


@dataclass
class CostBreakdown:
    """Cost breakdown by category."""

    category: CostCategory
    resources: list[ResourceCost] = field(default_factory=list)
    monthly_total: float = 0.0
    percentage: float = 0.0  # Percentage of total cost

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "category": self.category.value,
            "resource_count": len(self.resources),
            "monthly_total": round(self.monthly_total, 2),
            "percentage": round(self.percentage, 1),
            "resources": [r.resource_id for r in self.resources],
        }


@dataclass
class OptimizationRecommendation:
    """Cost optimization recommendation."""

    title: str
    description: str
    potential_savings: float  # Monthly savings in USD
    effort: str  # LOW, MEDIUM, HIGH
    affected_resources: list[str] = field(default_factory=list)
    action_items: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "potential_savings": round(self.potential_savings, 2),
            "effort": self.effort,
            "affected_resources": self.affected_resources,
            "action_items": self.action_items,
        }


@dataclass
class CostEstimate:
    """Complete cost estimate for infrastructure."""

    # Summary
    monthly_total: float = 0.0
    annual_total: float = 0.0
    daily_average: float = 0.0

    # Resource costs
    resource_costs: list[ResourceCost] = field(default_factory=list)

    # Breakdowns
    by_category: list[CostBreakdown] = field(default_factory=list)
    by_region: dict[str, float] = field(default_factory=dict)

    # Top costs
    top_resources: list[ResourceCost] = field(default_factory=list)

    # Optimization
    total_optimization_potential: float = 0.0  # Potential monthly savings
    optimization_percentage: float = 0.0  # Potential % savings
    recommendations: list[OptimizationRecommendation] = field(default_factory=list)

    # Metadata
    resource_count: int = 0
    estimated_resources: int = 0  # Resources with cost estimates
    unestimated_resources: int = 0  # Resources without estimates
    confidence: CostConfidence = CostConfidence.MEDIUM
    assumptions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON output."""
        return {
            "summary": {
                "monthly_total": round(self.monthly_total, 2),
                "annual_total": round(self.annual_total, 2),
                "daily_average": round(self.daily_average, 2),
                "resource_count": self.resource_count,
                "estimated_resources": self.estimated_resources,
                "unestimated_resources": self.unestimated_resources,
                "confidence": self.confidence.value,
            },
            "by_category": [b.to_dict() for b in self.by_category],
            "by_region": {k: round(v, 2) for k, v in self.by_region.items()},
            "top_resources": [r.to_dict() for r in self.top_resources],
            "resource_costs": [r.to_dict() for r in self.resource_costs],
            "optimization": {
                "potential_monthly_savings": round(self.total_optimization_potential, 2),
                "potential_percentage": round(self.optimization_percentage, 1),
                "recommendations": [r.to_dict() for r in self.recommendations],
            },
            "assumptions": self.assumptions,
            "warnings": self.warnings,
        }
