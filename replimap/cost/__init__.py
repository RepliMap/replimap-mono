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

General Pricing Engine (P1-4):
- Abstract pricing engine with extensible architecture
- Multi-region and multi-currency support
- Standardized pricing units

Australia Local Pricing (P1-5):
- ap-southeast-2 (Sydney) and ap-southeast-4 (Melbourne) pricing
- AUD currency with GST (10%) support
- Sydney vs Melbourne comparison

Data Transfer Cost Analysis (P1-6):
- Cross-AZ traffic detection and costing
- NAT Gateway traffic analysis
- Cross-region transfer costs
- VPC Endpoint optimization suggestions

Enterprise Pricing Engine (P2-7):
- EDP (Enterprise Discount Program) discount application
- PPA (Private Pricing Agreement) custom prices
- Volume discount rules
- YAML configuration support

This is a Pro+ feature ($79/mo).
"""

from replimap.cost.au_pricing import (
    AU_GST_RATE,
    AUD_EXCHANGE_RATE,
    AUPricingConfig,
    AustraliaPricingEngine,
    RegionComparison,
    add_gst,
    calculate_gst,
    compare_au_regions,
)
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
from replimap.cost.pricing_engine import (
    BasePricingEngine,
    Currency,
    DefaultPricingEngine,
    PricePoint,
    PricingUnit,
    ResourceCost as PricingResourceCost,
)
from replimap.cost.reporter import CostReporter
from replimap.cost.transfer_analyzer import (
    DataTransferAnalyzer,
    TrafficDirection,
    TransferCost,
    TransferPath,
    TransferPricingTiers,
    TransferReport,
    TransferType,
)
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
from replimap.cost.enterprise_pricing import (
    CustomPrice,
    DiscountRule,
    DiscountScope,
    DiscountType,
    EDPConfig,
    EnterprisePricingConfig,
    EnterprisePricingEngine,
    VolumeDiscount,
    VolumeDiscountTier,
    create_edp_config,
    create_enterprise_engine,
    generate_sample_config,
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
    # General Pricing Engine (P1-4)
    "BasePricingEngine",
    "DefaultPricingEngine",
    "PricePoint",
    "PricingUnit",
    "Currency",
    "PricingResourceCost",
    # Australia Pricing (P1-5)
    "AustraliaPricingEngine",
    "AUPricingConfig",
    "RegionComparison",
    "AU_GST_RATE",
    "AUD_EXCHANGE_RATE",
    "compare_au_regions",
    "add_gst",
    "calculate_gst",
    # Data Transfer Analysis (P1-6)
    "DataTransferAnalyzer",
    "TransferPath",
    "TransferCost",
    "TransferReport",
    "TransferType",
    "TrafficDirection",
    "TransferPricingTiers",
    # Enterprise Pricing Engine (P2-7)
    "EnterprisePricingEngine",
    "EnterprisePricingConfig",
    "EDPConfig",
    "CustomPrice",
    "DiscountRule",
    "DiscountType",
    "DiscountScope",
    "VolumeDiscount",
    "VolumeDiscountTier",
    "create_enterprise_engine",
    "create_edp_config",
    "generate_sample_config",
]
