"""
Analysis modules for RepliMap.

This module provides infrastructure analysis capabilities:
- Centrality Analysis: Identify critical resources
- Single Point of Failure detection
- Blast Radius computation
- Attack Surface mapping
"""

from __future__ import annotations

from replimap.core.analysis.centrality import (
    AttackSurfaceAnalyzer,
    BlastRadiusResult,
    CentralityAnalyzer,
    CriticalityLevel,
    CriticalityResult,
    CriticalResourceFinder,
    SinglePointOfFailureResult,
)

__all__ = [
    "CentralityAnalyzer",
    "CriticalResourceFinder",
    "AttackSurfaceAnalyzer",
    "BlastRadiusResult",
    "SinglePointOfFailureResult",
    "CriticalityResult",
    "CriticalityLevel",
]
