"""
Metadata-Driven Identity Resolver for RepliMap.

This module provides a declarative, configuration-driven approach to normalizing
resource IDs from different sources (AWS scanners and Terraform state) to a
common canonical form for accurate drift detection.

Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    IDENTITY_REGISTRY                         │
    │  Declarative mapping: resource_type → normalization strategy │
    └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    IdentityResolver                          │
    │  1. strip_account_prefix()  # Global, always runs            │
    │  2. lookup_strategy()       # From registry                  │
    │  3. safe_execute()          # With fallback on error         │
    └─────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import re
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# STRATEGY FUNCTIONS
# =============================================================================


def _literal(value: str, _pattern: str | None = None) -> str:
    """Return value as-is."""
    return value


def _path_tail(value: str, _pattern: str | None = None) -> str:
    """Extract last segment of a path (after last /)."""
    return value.rstrip("/").split("/")[-1]


def _url_tail(value: str, _pattern: str | None = None) -> str:
    """Extract resource name from URL (last path segment)."""
    # Handle SQS URLs like https://sqs.region.amazonaws.com/account/queue-name
    return value.rstrip("/").split("/")[-1]


def _arn_tail(value: str, _pattern: str | None = None) -> str:
    """Extract last segment of ARN (after last :)."""
    return value.split(":")[-1]


def _arn_resource(value: str, _pattern: str | None = None) -> str:
    """Extract resource portion from ARN (after resource-type/)."""
    # ARN format: arn:partition:service:region:account:resource-type/resource-id
    if "/" in value:
        return value.split("/")[-1]
    return value.split(":")[-1]


def _regex(value: str, pattern: str | None = None) -> str:
    """Extract using regex pattern with group(1)."""
    if not pattern:
        return value
    match = re.search(pattern, value)
    return match.group(1) if match else value


# Strategy registry - maps strategy names to functions
STRATEGIES: dict[str, Callable[[str, str | None], str]] = {
    "literal": _literal,
    "path_tail": _path_tail,
    "url_tail": _url_tail,
    "arn_tail": _arn_tail,
    "arn_resource": _arn_resource,
    "regex": _regex,
}


# =============================================================================
# IDENTITY REGISTRY
# =============================================================================

# Each resource type maps to normalization strategies for both sources.
# scanner_id: How to normalize the ID from AWS scanner output
# tf_state_id: How to normalize the ID from Terraform state
IDENTITY_REGISTRY: dict[str, dict[str, Any]] = {
    # Core resources - typically use literal matching
    "aws_instance": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_vpc": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_subnet": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_security_group": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_internet_gateway": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_nat_gateway": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_route_table": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_eip": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_ebs_volume": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_launch_template": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # SQS: Scanner uses ARN, TF state uses URL
    "aws_sqs_queue": {
        "scanner_id": {
            "strategy": "arn_tail"
        },  # arn:aws:sqs:region:account:name -> name
        "tf_state_id": {"strategy": "url_tail"},  # https://sqs.../account/name -> name
    },
    # SNS: Both use ARN
    "aws_sns_topic": {
        "scanner_id": {"strategy": "arn_tail"},
        "tf_state_id": {"strategy": "arn_tail"},
    },
    # ASG: Scanner uses ARN, TF state uses name
    "aws_autoscaling_group": {
        "scanner_id": {
            "strategy": "regex",
            "pattern": r"autoScalingGroupName/(.+)$",
        },
        "tf_state_id": {"strategy": "literal"},
    },
    # Load Balancer: Both use ARN
    "aws_lb": {
        "scanner_id": {"strategy": "literal"},  # Full ARN
        "tf_state_id": {"strategy": "literal"},  # Full ARN
    },
    "aws_lb_listener": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_lb_target_group": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # CloudWatch Log Group: Name-based
    "aws_cloudwatch_log_group": {
        "scanner_id": {"strategy": "literal"},  # Scanner uses name directly
        "tf_state_id": {"strategy": "literal"},  # TF uses name
    },
    # Lambda: ARN-based scanner (if implemented), name in TF
    "aws_lambda_function": {
        "scanner_id": {"strategy": "arn_resource"},
        "tf_state_id": {"strategy": "literal"},
    },
    # RDS: Identifier-based
    "aws_db_instance": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_db_subnet_group": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # S3: Bucket name
    "aws_s3_bucket": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # ElastiCache
    "aws_elasticache_cluster": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_elasticache_subnet_group": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # IAM: Name-based
    "aws_iam_role": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    "aws_iam_policy": {
        "scanner_id": {"strategy": "arn_resource"},  # ARN -> policy name
        "tf_state_id": {"strategy": "literal"},  # TF uses ARN
    },
    "aws_iam_instance_profile": {
        "scanner_id": {"strategy": "literal"},
        "tf_state_id": {"strategy": "literal"},
    },
    # CloudWatch: Name-based
    "aws_cloudwatch_metric_alarm": {
        "scanner_id": {"strategy": "literal"},  # Scanner uses alarm name
        "tf_state_id": {"strategy": "literal"},  # TF uses alarm name
    },
}


# =============================================================================
# IDENTITY RESOLVER
# =============================================================================


class IdentityResolver:
    """
    Resolves resource identities to a canonical form for comparison.

    This class provides the core logic for normalizing resource IDs from
    different sources (AWS scanners and Terraform state) to enable accurate
    drift detection.

    Usage:
        resolver = IdentityResolver()

        # Normalize scanner ID
        canonical = resolver.normalize(
            "arn:aws:sqs:us-east-1:123456789012:my-queue",
            "aws_sqs_queue",
            source="scanner"
        )
        # Returns: "my-queue"

        # Normalize TF state ID
        canonical = resolver.normalize(
            "https://sqs.us-east-1.amazonaws.com/123456789012/my-queue",
            "aws_sqs_queue",
            source="tf_state"
        )
        # Returns: "my-queue"
    """

    @staticmethod
    def strip_account_prefix(raw_id: str) -> str:
        """
        Strip {account_id}:{region}: prefix from scanner IDs.

        Some scanners (via build_node_id) add this prefix to create unique IDs.
        This is a global preprocessing step before resource-specific strategies.

        Args:
            raw_id: The raw resource ID, possibly with prefix

        Returns:
            ID with account:region prefix removed if present
        """
        if not raw_id or ":" not in raw_id:
            return raw_id

        parts = raw_id.split(":")

        # Check for pattern: {12-digit-account}:{region}:{rest}
        # Account ID is always 12 digits
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 12:
            # Rejoin everything after account:region
            return ":".join(parts[2:])

        return raw_id

    @staticmethod
    def safe_execute(
        strategy_func: Callable[[str, str | None], str],
        value: str,
        pattern: str | None = None,
    ) -> str:
        """
        Execute strategy with exception handling.

        Ensures the system doesn't crash on malformed IDs - falls back to
        the original value if strategy execution fails.

        Args:
            strategy_func: The strategy function to execute
            value: The ID value to normalize
            pattern: Optional regex pattern for regex strategy

        Returns:
            Normalized ID, or original value on error
        """
        try:
            return strategy_func(value, pattern)
        except Exception as e:
            logger.debug(f"Strategy execution failed for '{value}': {e}")
            return value

    @classmethod
    def normalize(
        cls,
        raw_id: str,
        resource_type: str,
        source: str = "scanner",
    ) -> str:
        """
        Normalize a resource ID to canonical form.

        Args:
            raw_id: The raw resource ID from scanner or TF state
            resource_type: Terraform resource type (e.g., "aws_sqs_queue")
            source: Either "scanner" or "tf_state"

        Returns:
            Normalized canonical ID for comparison
        """
        if not raw_id:
            return raw_id

        # Step 1: Global preprocessing - strip account:region prefix for scanner IDs
        if source == "scanner":
            working_id = cls.strip_account_prefix(raw_id)
        else:
            working_id = raw_id

        # Step 2: Lookup resource-specific strategy
        config = IDENTITY_REGISTRY.get(resource_type, {})
        source_key = f"{source}_id"  # "scanner_id" or "tf_state_id"
        strategy_config = config.get(source_key, {"strategy": "literal"})

        strategy_name = strategy_config.get("strategy", "literal")
        pattern = strategy_config.get("pattern")

        # Step 3: Execute strategy with safe fallback
        strategy_func = STRATEGIES.get(strategy_name, _literal)
        return cls.safe_execute(strategy_func, working_id, pattern)

    @classmethod
    def normalize_scanner_id(cls, raw_id: str, resource_type: str) -> str:
        """Convenience method for normalizing scanner IDs."""
        return cls.normalize(raw_id, resource_type, source="scanner")

    @classmethod
    def normalize_tf_state_id(cls, raw_id: str, resource_type: str) -> str:
        """Convenience method for normalizing TF state IDs."""
        return cls.normalize(raw_id, resource_type, source="tf_state")


# =============================================================================
# SCANNER COVERAGE
# =============================================================================


def get_scanner_coverage() -> set[str]:
    """
    Get the set of resource types that have scanner coverage.

    Dynamically queries the ScannerRegistry to determine which resource
    types can be scanned. This avoids manual maintenance of a coverage dict.

    Returns:
        Set of Terraform resource type strings that have scanner implementations
    """
    try:
        from replimap.scanners.base import ScannerRegistry

        covered_types: set[str] = set()
        for scanner_class in ScannerRegistry.get_all():
            covered_types.update(scanner_class.resource_types)

        return covered_types
    except ImportError:
        logger.warning("Could not import ScannerRegistry for coverage detection")
        return set()


def has_scanner_coverage(resource_type: str) -> bool:
    """
    Check if a resource type has scanner coverage.

    Args:
        resource_type: Terraform resource type (e.g., "aws_lambda_function")

    Returns:
        True if a scanner exists for this type, False otherwise
    """
    return resource_type in get_scanner_coverage()
