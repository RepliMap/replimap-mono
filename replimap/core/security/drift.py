"""
Drift Detection for Sanitized Configurations.

This module provides drift detection capabilities that work with
deterministically redacted sensitive values. It can detect:
- Normal value changes in non-sensitive fields
- Changes in redacted sensitive fields via hash comparison
- Sensitivity status changes (field became/stopped being sensitive)
- Structural changes (fields added/removed)

Architecture:
    The DriftDetector compares two sanitized configurations:
    - Old configuration (from cache)
    - New configuration (from scan)

    For redacted fields, it compares the hash portion to detect changes
    without exposing the actual sensitive values.

Usage:
    detector = DriftDetector()

    old_config = load_from_cache()
    new_config = sanitize(scan_result)

    result = detector.compare(old_config, new_config)
    if result.has_drift:
        for drift in result.drifts:
            print(drift)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from replimap.core.security.redactor import DeterministicRedactor

logger = logging.getLogger(__name__)


class DriftType(Enum):
    """Types of configuration drift."""

    VALUE_CHANGED = "value_changed"  # Normal field value changed
    SENSITIVE_CHANGED = "sensitive_changed"  # Redacted field hash changed
    SENSITIVITY_ADDED = "sensitivity_added"  # Field became sensitive
    SENSITIVITY_REMOVED = "sensitivity_removed"  # Field no longer sensitive
    FIELD_ADDED = "field_added"  # New field appeared
    FIELD_REMOVED = "field_removed"  # Field was removed


@dataclass
class DriftItem:
    """Individual drift detection."""

    field: str
    drift_type: DriftType
    old_value: Any = None
    new_value: Any = None
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None

    def __str__(self) -> str:
        if self.drift_type == DriftType.VALUE_CHANGED:
            return f"{self.field}: {self.old_value!r} → {self.new_value!r}"
        elif self.drift_type == DriftType.SENSITIVE_CHANGED:
            return (
                f"{self.field}: [SENSITIVE VALUE CHANGED] "
                f"({self.old_hash} → {self.new_hash})"
            )
        elif self.drift_type == DriftType.SENSITIVITY_ADDED:
            return f"{self.field}: [BECAME SENSITIVE]"
        elif self.drift_type == DriftType.SENSITIVITY_REMOVED:
            return f"{self.field}: [NO LONGER SENSITIVE]"
        elif self.drift_type == DriftType.FIELD_ADDED:
            return f"{self.field}: [ADDED] = {self.new_value!r}"
        elif self.drift_type == DriftType.FIELD_REMOVED:
            return f"{self.field}: [REMOVED] (was {self.old_value!r})"
        return f"{self.field}: {self.drift_type.value}"


@dataclass
class DriftResult:
    """Result of drift detection."""

    has_drift: bool
    drifts: List[DriftItem] = field(default_factory=list)

    # Categorized counts
    value_changes: int = 0
    sensitive_changes: int = 0
    structural_changes: int = 0

    def __post_init__(self) -> None:
        if self.drifts:
            self.value_changes = sum(
                1 for d in self.drifts if d.drift_type == DriftType.VALUE_CHANGED
            )
            self.sensitive_changes = sum(
                1 for d in self.drifts if d.drift_type == DriftType.SENSITIVE_CHANGED
            )
            self.structural_changes = sum(
                1
                for d in self.drifts
                if d.drift_type
                in (
                    DriftType.FIELD_ADDED,
                    DriftType.FIELD_REMOVED,
                    DriftType.SENSITIVITY_ADDED,
                    DriftType.SENSITIVITY_REMOVED,
                )
            )

    def summary(self) -> str:
        """Human-readable summary."""
        if not self.has_drift:
            return "No drift detected"

        parts = []
        if self.value_changes:
            parts.append(f"{self.value_changes} value change(s)")
        if self.sensitive_changes:
            parts.append(f"{self.sensitive_changes} sensitive field change(s)")
        if self.structural_changes:
            parts.append(f"{self.structural_changes} structural change(s)")

        return f"Drift detected: {', '.join(parts)}"


class DriftDetector:
    """
    Detect configuration drift between sanitized configurations.

    Handles:
    - Normal value comparisons for non-sensitive fields
    - Hash comparisons for redacted sensitive fields
    - Sensitivity status changes (field became/stopped being sensitive)
    - Structural changes (fields added/removed)

    Usage:
        detector = DriftDetector()

        old_config = load_from_cache()
        new_config = sanitize(scan_result)

        result = detector.compare(old_config, new_config)
        if result.has_drift:
            for drift in result.drifts:
                print(drift)
    """

    # Fields to ignore in drift detection
    IGNORE_FIELDS: Set[str] = {
        "last_scanned",
        "scan_timestamp",
        "cache_version",
    }

    def __init__(self, redactor: Optional[DeterministicRedactor] = None) -> None:
        """
        Initialize detector.

        Args:
            redactor: Redactor for checking redaction format (not for redacting)
        """
        self.redactor = redactor or DeterministicRedactor()

    def compare(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        path: str = "",
    ) -> DriftResult:
        """
        Compare two configurations for drift.

        Args:
            old_config: Previous configuration (from cache)
            new_config: Current configuration (from scan)
            path: Current path in nested structure (for recursion)

        Returns:
            DriftResult with all detected drifts
        """
        drifts: List[DriftItem] = []

        self._compare_recursive(old_config, new_config, path, drifts)

        return DriftResult(
            has_drift=len(drifts) > 0,
            drifts=drifts,
        )

    def _compare_recursive(
        self,
        old_data: Any,
        new_data: Any,
        path: str,
        drifts: List[DriftItem],
    ) -> None:
        """Recursively compare data structures."""

        # Both None
        if old_data is None and new_data is None:
            return

        # Type mismatch
        if type(old_data) != type(new_data):
            drifts.append(
                DriftItem(
                    field=path or "root",
                    drift_type=DriftType.VALUE_CHANGED,
                    old_value=type(old_data).__name__,
                    new_value=type(new_data).__name__,
                )
            )
            return

        # Dict comparison
        if isinstance(old_data, dict) and isinstance(new_data, dict):
            self._compare_dicts(old_data, new_data, path, drifts)
            return

        # List comparison
        if isinstance(old_data, list) and isinstance(new_data, list):
            self._compare_lists(old_data, new_data, path, drifts)
            return

        # Scalar comparison
        self._compare_scalars(old_data, new_data, path, drifts)

    def _compare_dicts(
        self,
        old_dict: Dict[str, Any],
        new_dict: Dict[str, Any],
        path: str,
        drifts: List[DriftItem],
    ) -> None:
        """Compare dictionaries."""
        all_keys = set(old_dict.keys()) | set(new_dict.keys())

        for key in all_keys:
            if key.lower() in self.IGNORE_FIELDS:
                continue

            field_path = f"{path}.{key}" if path else key

            old_val = old_dict.get(key)
            new_val = new_dict.get(key)

            # Field removed
            if key not in new_dict:
                drifts.append(
                    DriftItem(
                        field=field_path,
                        drift_type=DriftType.FIELD_REMOVED,
                        old_value=old_val,
                    )
                )
                continue

            # Field added
            if key not in old_dict:
                drifts.append(
                    DriftItem(
                        field=field_path,
                        drift_type=DriftType.FIELD_ADDED,
                        new_value=new_val,
                    )
                )
                continue

            # Both exist - compare values
            self._compare_recursive(old_val, new_val, field_path, drifts)

    def _compare_lists(
        self,
        old_list: List[Any],
        new_list: List[Any],
        path: str,
        drifts: List[DriftItem],
    ) -> None:
        """Compare lists."""
        # Simple length check first
        if len(old_list) != len(new_list):
            drifts.append(
                DriftItem(
                    field=path,
                    drift_type=DriftType.VALUE_CHANGED,
                    old_value=f"list[{len(old_list)}]",
                    new_value=f"list[{len(new_list)}]",
                )
            )
            return

        # Element-by-element comparison
        for i, (old_item, new_item) in enumerate(zip(old_list, new_list)):
            self._compare_recursive(old_item, new_item, f"{path}[{i}]", drifts)

    def _compare_scalars(
        self,
        old_val: Any,
        new_val: Any,
        path: str,
        drifts: List[DriftItem],
    ) -> None:
        """Compare scalar values (strings, numbers, etc.)."""

        # Check if values are redacted
        old_is_redacted = (
            self.redactor.is_redacted(old_val) if isinstance(old_val, str) else False
        )
        new_is_redacted = (
            self.redactor.is_redacted(new_val) if isinstance(new_val, str) else False
        )

        # Both redacted - compare hashes
        if old_is_redacted and new_is_redacted:
            old_hash = self.redactor.extract_hash(old_val)
            new_hash = self.redactor.extract_hash(new_val)

            if old_hash != new_hash:
                drifts.append(
                    DriftItem(
                        field=path,
                        drift_type=DriftType.SENSITIVE_CHANGED,
                        old_hash=old_hash,
                        new_hash=new_hash,
                    )
                )
            return

        # Sensitivity status changed
        if old_is_redacted and not new_is_redacted:
            drifts.append(
                DriftItem(
                    field=path,
                    drift_type=DriftType.SENSITIVITY_REMOVED,
                    old_value="[REDACTED]",
                    new_value=new_val,
                )
            )
            return

        if not old_is_redacted and new_is_redacted:
            drifts.append(
                DriftItem(
                    field=path,
                    drift_type=DriftType.SENSITIVITY_ADDED,
                    old_value=old_val,
                    new_value="[REDACTED]",
                )
            )
            return

        # Normal comparison
        if old_val != new_val:
            drifts.append(
                DriftItem(
                    field=path,
                    drift_type=DriftType.VALUE_CHANGED,
                    old_value=old_val,
                    new_value=new_val,
                )
            )
