"""
RepliMap Licensing Module.

Provides license validation, feature gating, and usage tracking
for the commercial tiers of RepliMap.
"""

from replimap.licensing.gates import feature_gate, require_plan
from replimap.licensing.manager import LicenseManager, is_dev_mode
from replimap.licensing.models import (
    Feature,
    License,
    LicenseStatus,
    LicenseValidationError,
    Plan,
    PlanFeatures,
    get_plan_features,
)
from replimap.licensing.tracker import UsageTracker

__all__ = [
    "Feature",
    "License",
    "LicenseManager",
    "LicenseStatus",
    "LicenseValidationError",
    "Plan",
    "PlanFeatures",
    "UsageTracker",
    "feature_gate",
    "get_plan_features",
    "is_dev_mode",
    "require_plan",
]
