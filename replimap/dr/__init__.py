"""
Disaster Recovery module for RepliMap.

Provides DR analysis and assessment capabilities:
- DR readiness assessment and scoring
- RTO/RPO estimation
- Cross-region replication analysis
- Gap analysis and recommendations
"""

from replimap.dr.readiness import (
    CoverageAnalysis,
    DRGap,
    DRGapCategory,
    DRRecommendation,
    DRRecommendationPriority,
    DRRecommendationType,
    DRScorecard,
    DRTier,
    ReadinessAssessor,
    ReadinessConfig,
    ResourceCoverage,
    RPOEstimate,
    RTOEstimate,
    analyze_dr_readiness,
    calculate_rpo_estimate,
    calculate_rto_estimate,
    generate_dr_recommendations,
)

__all__ = [
    # Core classes
    "ReadinessAssessor",
    "ReadinessConfig",
    "DRScorecard",
    "CoverageAnalysis",
    "ResourceCoverage",
    # Estimates
    "RTOEstimate",
    "RPOEstimate",
    # Gaps and recommendations
    "DRGap",
    "DRGapCategory",
    "DRRecommendation",
    "DRRecommendationType",
    "DRRecommendationPriority",
    # Enums
    "DRTier",
    # Functions
    "analyze_dr_readiness",
    "calculate_rto_estimate",
    "calculate_rpo_estimate",
    "generate_dr_recommendations",
]
