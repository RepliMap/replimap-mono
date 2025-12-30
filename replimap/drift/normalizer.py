"""
Normalization pipeline for drift detection.

Implements a 3-layer normalization to eliminate false positive drifts:

Layer 1: Attribute Filter
- Remove AWS-managed attributes (aws:* tags, computed fields)
- Apply resource-type specific ignore lists

Layer 2: Structure Normalizer
- Convert tag formats to canonical dict
- Sort all lists recursively for order-independent comparison
- Create deterministic serialization for nested structures

Layer 3: Value Canonicalizer
- Falsy equivalence: None == false == 0 == "" == []
- Type coercion: "8080" -> 8080, "true" -> True
- Unit normalization for time/size attributes
"""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# LAYER 1: Attribute Filter Configuration
# =============================================================================

# Attributes to ignore for ALL resource types
BASE_IGNORES: set[str] = {
    # AWS-generated identifiers
    "arn",
    "id",
    "owner_id",
    "unique_id",
    "account_id",
    # Timestamps
    "create_date",
    "creation_date",
    "last_modified",
    "last_modified_date",
    "latest_restorable_time",
    # Computed networking
    "private_ip",
    "public_ip",
    "private_dns_name",
    "public_dns_name",
    "dns_name",
    "zone_id",
    "hosted_zone_id",
    # AWS internals
    "request_id",
    "reservation_id",
}

# Resource-specific attributes to ignore (merged with BASE_IGNORES)
RESOURCE_IGNORES: dict[str, set[str]] = {
    "aws_autoscaling_group": {
        "instances",  # Dynamic membership
        "load_balancers",  # Can change dynamically
        "target_group_arns",  # Often managed separately
        "availability_zones",  # AWS-assigned order
        "desired_capacity",  # Often auto-adjusted
        "default_cooldown",
    },
    "aws_instance": {
        "instance_state",  # Runtime state
        "private_ip",
        "public_ip",
        "public_dns_name",
        "private_dns_name",
        "network_interface_id",
        "primary_network_interface_id",
    },
    "aws_security_group": {
        "owner_id",  # AWS account specific
    },
    "aws_db_instance": {
        "latest_restorable_time",
        "endpoint",
        "address",
        "hosted_zone_id",
        "resource_id",
        "status",
        "ca_cert_identifier",
    },
    "aws_lambda_function": {
        "last_modified",
        "version",
        "qualified_arn",
        "invoke_arn",
        "source_code_hash",
        "source_code_size",
    },
    "aws_s3_bucket": {
        "bucket_domain_name",
        "bucket_regional_domain_name",
        "arn",
        "region",
        "hosted_zone_id",
    },
    "aws_lb": {
        "dns_name",
        "zone_id",
        "arn_suffix",
        "vpc_id",  # Often implied
    },
    "aws_launch_template": {
        "latest_version",
        "default_version",
    },
    "aws_iam_role": {
        "unique_id",
        "create_date",
    },
}

# Tag prefixes managed by AWS (should be ignored)
AWS_TAG_PREFIXES: tuple[str, ...] = (
    "aws:",
    "elasticmapreduce:",
    "kubernetes.io/",
    "k8s.io/",
    "eks:",
)


def get_ignores_for_type(resource_type: str) -> set[str]:
    """Get combined ignore set for a resource type."""
    return BASE_IGNORES | RESOURCE_IGNORES.get(resource_type, set())


# =============================================================================
# LAYER 2: Structure Normalizer
# =============================================================================


def normalize_tags(tags: Any) -> dict[str, str]:
    """
    Convert any tag format to canonical dict, filtering AWS-managed tags.

    Handles:
    - AWS format: [{"Key": "Name", "Value": "foo"}, ...]
    - Terraform format: {"Name": "foo", ...}
    - None or empty
    """
    if tags is None:
        return {}

    result: dict[str, str] = {}

    if isinstance(tags, list):
        # AWS API format: [{"Key": k, "Value": v}, ...]
        for tag in tags:
            if isinstance(tag, dict):
                key = tag.get("Key") or tag.get("key", "")
                value = tag.get("Value") or tag.get("value", "")
                if key and not any(key.startswith(p) for p in AWS_TAG_PREFIXES):
                    result[key] = str(value) if value is not None else ""
    elif isinstance(tags, dict):
        # Terraform format: {k: v, ...}
        for key, value in tags.items():
            if not any(str(key).startswith(p) for p in AWS_TAG_PREFIXES):
                result[str(key)] = str(value) if value is not None else ""

    return result


def deep_sort(value: Any) -> Any:
    """
    Recursively sort nested structures for deterministic comparison.

    Returns a normalized, comparable representation.
    """
    if value is None:
        return None

    if isinstance(value, dict):
        # Sort dict by keys, recursively normalize values
        return {k: deep_sort(v) for k, v in sorted(value.items())}

    if isinstance(value, list):
        # Sort list items; for complex items, serialize to compare
        try:
            sorted_items = []
            for item in value:
                normalized = deep_sort(item)
                sorted_items.append(normalized)

            # Sort by JSON representation for consistency
            return sorted(
                sorted_items,
                key=lambda x: json.dumps(x, sort_keys=True, default=str),
            )
        except TypeError:
            # Fallback for unhashable/uncomparable items
            return [deep_sort(item) for item in value]

    return value


def canonical_hash(value: Any) -> str:
    """
    Create deterministic hash string for any nested structure.

    Used for comparing complex nested objects regardless of ordering.
    """
    normalized = deep_sort(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), default=str)


# =============================================================================
# LAYER 3: Value Canonicalizer
# =============================================================================

# Values considered semantically "empty/falsy"
# Note: False == 0 and 0 == 0.0 in Python, so we only include distinct values
# and check others via is_falsy() function
FALSY_VALUES: frozenset[Any] = frozenset(
    {
        None,
        False,  # Also covers 0 and 0.0 due to equality
        "",
        "null",
        "None",
        "none",
        "false",
        "False",
        "0",
    }
)

# Empty container representations
EMPTY_CONTAINERS: tuple[Any, ...] = ([], {}, (), set(), frozenset())


def is_falsy(value: Any) -> bool:
    """Check if value is semantically 'empty/default'."""
    # Handle unhashable types first (list, dict, set)
    if isinstance(value, (list, dict, set)):
        return len(value) == 0

    # Check against falsy value set (only for hashable types)
    try:
        if value in FALSY_VALUES:
            return True
    except TypeError:
        # Unhashable type - already handled above
        pass

    if isinstance(value, str) and value.lower() in ("null", "false", "none", ""):
        return True

    return False


def canonicalize_value(value: Any, attr_name: str = "") -> Any:
    """
    Canonicalize a value for comparison.

    - Converts stringified booleans to bool
    - Converts numeric strings to numbers
    - Normalizes empty values to None
    """
    if value is None:
        return None

    # Handle stringified booleans
    if isinstance(value, str):
        lower_val = value.lower().strip()
        if lower_val in ("true", "yes", "1"):
            return True
        if lower_val in ("false", "no", "0", ""):
            return False
        # Handle numeric strings
        if lower_val.isdigit():
            return int(value)
        try:
            if "." in value and value.replace(".", "").isdigit():
                return float(value)
        except (ValueError, AttributeError):
            pass

    # Normalize empty containers
    if isinstance(value, (list, dict, set)) and len(value) == 0:
        return None

    return value


def values_equivalent(expected: Any, actual: Any, attr_name: str = "") -> bool:
    """
    Check if two values are semantically equivalent.

    This is the core comparison function that handles:
    - Falsy value equivalence (None == false == 0 == "" == [])
    - Type coercion (string "80" == int 80)
    - Nested structure comparison with ordering normalization
    """
    # Both falsy = equivalent
    if is_falsy(expected) and is_falsy(actual):
        return True

    # One falsy, one not = different
    if is_falsy(expected) != is_falsy(actual):
        return False

    # Canonicalize values
    expected_canon = canonicalize_value(expected, attr_name)
    actual_canon = canonicalize_value(actual, attr_name)

    # Direct equality after canonicalization
    if expected_canon == actual_canon:
        return True

    # Special handling for tags
    if attr_name == "tags":
        return normalize_tags(expected) == normalize_tags(actual)

    # List comparison (order-independent)
    if isinstance(expected_canon, list) and isinstance(actual_canon, list):
        if len(expected_canon) != len(actual_canon):
            return False
        return canonical_hash(expected_canon) == canonical_hash(actual_canon)

    # Dict comparison
    if isinstance(expected_canon, dict) and isinstance(actual_canon, dict):
        return canonical_hash(expected_canon) == canonical_hash(actual_canon)

    # String comparison (case-insensitive for certain attributes)
    if isinstance(expected_canon, str) and isinstance(actual_canon, str):
        case_insensitive_attrs = {"engine", "instance_type", "instance_class"}
        if attr_name in case_insensitive_attrs:
            return expected_canon.lower() == actual_canon.lower()

    return False


# =============================================================================
# DRIFT REASON CLASSIFICATION
# =============================================================================


def classify_drift_reason(
    attr_name: str,
    expected: Any,
    actual: Any,
    resource_type: str = "",
) -> str:
    """
    Classify the reason for a detected drift.

    Returns one of the DriftReason enum values (as string for compatibility).
    """
    # Import here to avoid circular import (models imports from this module)
    from replimap.drift.models import DriftReason

    # Check if it's a computed/ignored attribute
    ignores = get_ignores_for_type(resource_type)
    if attr_name in ignores:
        return DriftReason.COMPUTED.value

    # Tag-only changes
    if attr_name == "tags":
        return DriftReason.TAG_ONLY.value

    # Default value drift: one side is falsy
    if is_falsy(expected) != is_falsy(actual):
        if is_falsy(expected) or is_falsy(actual):
            return DriftReason.DEFAULT_VALUE.value

    # Ordering drift: same content when sorted
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) == len(actual):
            if canonical_hash(expected) == canonical_hash(actual):
                return DriftReason.ORDERING.value

    # Default to semantic (real) drift
    return DriftReason.SEMANTIC.value


# =============================================================================
# MAIN NORMALIZER CLASS
# =============================================================================


class DriftNormalizer:
    """
    Main normalizer class that orchestrates the 3-layer pipeline.

    Usage:
        normalizer = DriftNormalizer()
        normalized_expected = normalizer.normalize(expected_attrs, "aws_instance")
        normalized_actual = normalizer.normalize(actual_attrs, "aws_instance")
    """

    def __init__(self, strict_mode: bool = False) -> None:
        """
        Initialize normalizer.

        Args:
            strict_mode: If True, skip normalization (for debugging)
        """
        self.strict_mode = strict_mode

    def normalize(
        self,
        attributes: dict[str, Any],
        resource_type: str = "",
    ) -> dict[str, Any]:
        """
        Apply full normalization pipeline to attributes.

        Args:
            attributes: Raw attribute dictionary
            resource_type: Terraform resource type (e.g., "aws_instance")

        Returns:
            Normalized attribute dictionary
        """
        if self.strict_mode:
            return attributes.copy()

        if not attributes:
            return {}

        result: dict[str, Any] = {}

        # Layer 1: Filter ignored attributes
        ignores = get_ignores_for_type(resource_type)

        for attr_name, value in attributes.items():
            # Skip ignored attributes
            if attr_name in ignores:
                continue

            # Layer 2: Structure normalization
            if attr_name == "tags":
                normalized_value = normalize_tags(value)
            elif isinstance(value, (list, dict)):
                normalized_value = deep_sort(value)
            else:
                normalized_value = value

            # Layer 3: Value canonicalization
            normalized_value = canonicalize_value(normalized_value, attr_name)

            # Only include non-falsy values
            if not is_falsy(normalized_value) or normalized_value is False:
                result[attr_name] = normalized_value

        return result

    def compare(
        self,
        expected: dict[str, Any],
        actual: dict[str, Any],
        resource_type: str = "",
    ) -> list[tuple[str, Any, Any, str]]:
        """
        Compare two attribute dicts and return differences with reasons.

        Args:
            expected: Expected attributes (from TF state)
            actual: Actual attributes (from AWS)
            resource_type: Resource type for context

        Returns:
            List of (attr_name, expected_value, actual_value, drift_reason)
        """
        diffs: list[tuple[str, Any, Any, str]] = []

        # Normalize both sides
        norm_expected = self.normalize(expected, resource_type)
        norm_actual = self.normalize(actual, resource_type)

        # Find all keys
        all_keys = set(norm_expected.keys()) | set(norm_actual.keys())

        for key in all_keys:
            exp_val = norm_expected.get(key)
            act_val = norm_actual.get(key)

            if not values_equivalent(exp_val, act_val, key):
                reason = classify_drift_reason(key, exp_val, act_val, resource_type)
                diffs.append((key, exp_val, act_val, reason))

        return diffs
