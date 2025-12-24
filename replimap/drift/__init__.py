"""Drift detection module for RepliMap."""

from replimap.drift.engine import DriftEngine
from replimap.drift.models import (
    AttributeDiff,
    DriftReport,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)
from replimap.drift.plan_engine import (
    DriftReporter,
    PlanBasedDriftEngine,
    PlanChange,
    PlanParser,
    PlanResult,
)
from replimap.drift.state_parser import TerraformStateParser, TFResource, TFState

__all__ = [
    # Legacy engine (deprecated, uses COMPARABLE_ATTRIBUTES)
    "DriftEngine",
    # New plan-based engine (recommended)
    "PlanBasedDriftEngine",
    "PlanParser",
    "PlanChange",
    "PlanResult",
    "DriftReporter",
    # Models
    "DriftType",
    "DriftSeverity",
    "AttributeDiff",
    "ResourceDrift",
    "DriftReport",
    # State parsing
    "TerraformStateParser",
    "TFResource",
    "TFState",
]
