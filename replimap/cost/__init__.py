"""
Cost Estimator module for RepliMap.

Provides comprehensive cost analysis for AWS infrastructure:
- Resource-level cost breakdown
- Category-based analysis
- Optimization recommendations
- Multiple output formats
- Prominent disclaimers and accuracy ranges

Enhanced Cost Optimization features (P1-2):
- AWS Cost Explorer integration for real cost data
- Savings Plans analysis and recommendations
- Unused/idle resource detection
- Cost trend analysis and forecasting

This is a Pro+ feature ($79/mo).
"""

from replimap.cost.estimator import CostEstimator
from replimap.cost.explorer import (
    CostDataPoint,
    CostExplorerClient,
    CostExplorerResults,
    CostForecast,
    Granularity,
    GroupByDimension,
    GroupedCost,
    MetricType,
    get_cost_comparison,
)
from replimap.cost.models import (
    COST_DISCLAIMER_FULL,
    COST_DISCLAIMER_SHORT,
    EXCLUDED_FACTORS,
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
from replimap.cost.savings_plans import (
    PaymentOption,
    SavingsPlanRecommendation,
    SavingsPlansAnalysis,
    SavingsPlansAnalyzer,
    SavingsPlanType,
    Term,
    UsagePattern,
    get_savings_plan_coverage,
    get_savings_plan_utilization,
)
from replimap.cost.trends import (
    AnomalyType,
    CostAnomaly,
    CostForecastResult,
    CostTrendAnalyzer,
    SeasonalPattern,
    ServiceTrend,
    TrendAnalysis,
    TrendDirection,
    TrendReport,
    get_cost_trend_summary,
)
from replimap.cost.unused_detector import (
    ConfidenceLevel,
    UnusedReason,
    UnusedResource,
    UnusedResourceDetector,
    UnusedResourcesReport,
)

__all__ = [
    # Disclaimer constants
    "COST_DISCLAIMER_SHORT",
    "COST_DISCLAIMER_FULL",
    "EXCLUDED_FACTORS",
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
    # Cost Explorer (P1-2)
    "CostExplorerClient",
    "CostExplorerResults",
    "CostDataPoint",
    "CostForecast",
    "GroupedCost",
    "Granularity",
    "MetricType",
    "GroupByDimension",
    "get_cost_comparison",
    # Savings Plans (P1-2)
    "SavingsPlansAnalyzer",
    "SavingsPlansAnalysis",
    "SavingsPlanRecommendation",
    "SavingsPlanType",
    "PaymentOption",
    "Term",
    "UsagePattern",
    "get_savings_plan_coverage",
    "get_savings_plan_utilization",
    # Unused Resource Detection (P1-2)
    "UnusedResourceDetector",
    "UnusedResourcesReport",
    "UnusedResource",
    "UnusedReason",
    "ConfidenceLevel",
    # Cost Trends (P1-2)
    "CostTrendAnalyzer",
    "TrendReport",
    "TrendAnalysis",
    "TrendDirection",
    "CostAnomaly",
    "AnomalyType",
    "ServiceTrend",
    "SeasonalPattern",
    "CostForecastResult",
    "get_cost_trend_summary",
]
