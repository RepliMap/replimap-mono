"""
Offline Drift Detection module.

Provides production-grade drift detection comparing cached RepliMap scans
against Terraform state files - the "offline terraform plan".
"""

from .detector import (
    AttributeChange,
    AttributeComparator,
    AttributeNormalizer,
    DriftFilter,
    DriftFinding,
    DriftIgnoreRule,
    DriftReport,
    DriftSeverity,
    DriftType,
    OfflineDriftDetector,
    Remediation,
    ScanComparator,
    TerraformStateLoader,
)

__all__ = [
    # Main detector
    "OfflineDriftDetector",
    # Scan comparator
    "ScanComparator",
    # State loading
    "TerraformStateLoader",
    # Normalization
    "AttributeNormalizer",
    "AttributeComparator",
    # Filtering
    "DriftFilter",
    "DriftIgnoreRule",
    # Data models
    "DriftType",
    "DriftSeverity",
    "Remediation",
    "AttributeChange",
    "DriftFinding",
    "DriftReport",
]
