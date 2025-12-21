"""
Cost Estimator module for RepliMap.

Provides monthly cost estimation for AWS infrastructure:
- Resource-level cost breakdown
- Category-based analysis
- Optimization recommendations
- Multiple output formats

This is a Pro+ feature ($99/mo).
"""

from replimap.cost.estimator import CostEstimator
from replimap.cost.models import (
    CostBreakdown,
    CostCategory,
    CostConfidence,
    CostEstimate,
    OptimizationRecommendation,
    PricingTier,
    ResourceCost,
)
from replimap.cost.pricing import (
    EBS_VOLUME_PRICING,
    EC2_INSTANCE_PRICING,
    ELASTICACHE_PRICING,
    RDS_INSTANCE_PRICING,
    PricingLookup,
)
from replimap.cost.reporter import CostReporter

__all__ = [
    # Models
    "CostBreakdown",
    "CostCategory",
    "CostConfidence",
    "CostEstimate",
    "OptimizationRecommendation",
    "PricingTier",
    "ResourceCost",
    # Core classes
    "CostEstimator",
    "CostReporter",
    "PricingLookup",
    # Pricing data
    "EC2_INSTANCE_PRICING",
    "EBS_VOLUME_PRICING",
    "ELASTICACHE_PRICING",
    "RDS_INSTANCE_PRICING",
]
