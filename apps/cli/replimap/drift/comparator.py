"""Comparison logic for drift detection."""

from __future__ import annotations

import logging
from typing import Any

from replimap.drift.models import (
    AttributeDiff,
    DriftReason,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)
from replimap.drift.normalizer import (
    DriftNormalizer,
    classify_drift_reason,
)
from replimap.drift.state_parser import TFResource

logger = logging.getLogger(__name__)


# Attributes to compare for each resource type
COMPARABLE_ATTRIBUTES: dict[str, dict[str, list[str]]] = {
    "aws_security_group": {
        "critical": ["ingress", "egress"],
        "high": ["vpc_id", "name", "description"],
        "low": ["tags"],
    },
    "aws_instance": {
        "critical": [
            "iam_instance_profile",
            "security_groups",
            "vpc_security_group_ids",
        ],
        "high": ["instance_type", "ami", "subnet_id", "key_name"],
        "medium": ["ebs_optimized", "monitoring", "user_data"],
        "low": ["tags"],
    },
    "aws_s3_bucket": {
        "critical": ["acl"],
        "high": ["versioning", "server_side_encryption_configuration"],
        "medium": ["logging", "lifecycle_rule"],
        "low": ["tags"],
    },
    "aws_db_instance": {
        "critical": ["publicly_accessible", "storage_encrypted"],
        "high": [
            "instance_class",
            "engine_version",
            "multi_az",
            "backup_retention_period",
        ],
        "medium": ["storage_type", "allocated_storage"],
        "low": ["tags"],
    },
    "aws_vpc": {
        "high": ["cidr_block", "enable_dns_hostnames", "enable_dns_support"],
        "low": ["tags"],
    },
    "aws_subnet": {
        "high": ["cidr_block", "availability_zone", "map_public_ip_on_launch"],
        "low": ["tags"],
    },
    "aws_iam_role": {
        "critical": ["assume_role_policy"],
        "high": ["name", "path"],
        "low": ["tags"],
    },
    "aws_lambda_function": {
        "critical": ["role", "vpc_config"],
        "high": ["runtime", "handler", "memory_size", "timeout"],
        "medium": ["environment"],
        "low": ["tags"],
    },
    "aws_lb": {
        "critical": ["internal", "security_groups"],
        "high": ["subnets", "load_balancer_type"],
        "medium": ["access_logs"],
        "low": ["tags"],
    },
    "aws_nat_gateway": {
        "high": ["subnet_id", "allocation_id"],
        "low": ["tags"],
    },
    "aws_eip": {
        "high": ["vpc", "instance", "network_interface"],
        "low": ["tags"],
    },
    "aws_route_table": {
        "high": ["vpc_id", "route"],
        "low": ["tags"],
    },
    "aws_internet_gateway": {
        "high": ["vpc_id"],
        "low": ["tags"],
    },
    "aws_kms_key": {
        "critical": ["policy", "key_usage", "customer_master_key_spec"],
        "high": ["enable_key_rotation", "deletion_window_in_days"],
        "low": ["tags"],
    },
}

# Default attributes for types not explicitly listed
DEFAULT_COMPARABLE: dict[str, list[str]] = {
    "high": ["name"],
    "low": ["tags"],
}


class DriftComparator:
    """Compare Terraform state against actual AWS state."""

    def __init__(self, strict_mode: bool = False) -> None:
        """
        Initialize comparator.

        Args:
            strict_mode: If True, skip normalization (for debugging)
        """
        self.normalizer = DriftNormalizer(strict_mode=strict_mode)
        self.ignore_attributes = {
            "arn",  # ARNs can have account-specific info
            "id",  # ID is used for matching, not comparison
            "owner_id",  # AWS account ID
            "unique_id",  # Generated IDs
            "create_date",  # Timestamps
            "creation_date",
        }

    def compare_resource(
        self,
        tf_resource: TFResource,
        actual_attributes: dict[str, Any],
        include_noise: bool = False,
    ) -> ResourceDrift:
        """Compare a single resource's expected vs actual state.

        Args:
            tf_resource: Resource from Terraform state
            actual_attributes: Attributes from AWS API
            include_noise: If True, include ordering/default_value diffs (for debugging)

        Returns:
            ResourceDrift with all differences
        """
        diffs: list[AttributeDiff] = []
        max_severity = DriftSeverity.INFO

        # Get comparable attributes for this type
        attr_config = COMPARABLE_ATTRIBUTES.get(tf_resource.type, DEFAULT_COMPARABLE)

        # Compare each severity level
        for severity_name, attrs in attr_config.items():
            severity = DriftSeverity(severity_name)

            for attr in attrs:
                if attr in self.ignore_attributes:
                    continue

                expected = tf_resource.attributes.get(attr)
                actual = actual_attributes.get(attr)

                if self._values_differ(expected, actual, attr):
                    # Classify the drift reason
                    reason_str = classify_drift_reason(
                        attr, expected, actual, tf_resource.type
                    )
                    reason = DriftReason(reason_str)

                    # Skip noise diffs unless explicitly requested
                    if not include_noise and reason in (
                        DriftReason.ORDERING,
                        DriftReason.DEFAULT_VALUE,
                    ):
                        logger.debug(
                            "Filtering noise drift for %s.%s: %s (%s)",
                            tf_resource.address,
                            attr,
                            reason.value,
                            f"{expected!r} -> {actual!r}",
                        )
                        continue

                    diff = AttributeDiff(
                        attribute=attr,
                        expected=expected,
                        actual=actual,
                        severity=severity,
                        reason=reason,
                    )
                    diffs.append(diff)

                    # Track maximum severity (only for semantic drifts)
                    if diff.is_semantic:
                        if self._severity_rank(severity) > self._severity_rank(
                            max_severity
                        ):
                            max_severity = severity

        # Determine drift type
        if diffs:
            drift_type = DriftType.MODIFIED
        else:
            drift_type = DriftType.UNCHANGED

        return ResourceDrift(
            resource_type=tf_resource.type,
            resource_id=tf_resource.id,
            resource_name=tf_resource.name,
            tf_address=tf_resource.address,
            drift_type=drift_type,
            diffs=diffs,
            severity=max_severity if diffs else DriftSeverity.INFO,
        )

    def _values_differ(self, expected: Any, actual: Any, attr: str) -> bool:
        """Check if two values are meaningfully different.

        Uses the normalizer's values_equivalent for sophisticated comparison
        that handles falsy equivalence, type coercion, and order-independent
        list/dict comparison.
        """
        from replimap.drift.normalizer import values_equivalent

        # Use normalizer's sophisticated comparison
        return not values_equivalent(expected, actual, attr)

    def _severity_rank(self, severity: DriftSeverity) -> int:
        """Get numeric rank for severity comparison."""
        ranks = {
            DriftSeverity.INFO: 0,
            DriftSeverity.LOW: 1,
            DriftSeverity.MEDIUM: 2,
            DriftSeverity.HIGH: 3,
            DriftSeverity.CRITICAL: 4,
        }
        return ranks.get(severity, 0)

    def identify_added_resources(
        self,
        actual_resources: list[Any],
        tf_state_ids: set[str],
        id_extractor: Any | None = None,
    ) -> list[ResourceDrift]:
        """Find resources in AWS that aren't in Terraform state.

        These are resources created outside of Terraform (console, CLI, etc).

        Args:
            actual_resources: List of resources from AWS
            tf_state_ids: Set of resource IDs from Terraform state
            id_extractor: Optional function(resource_id, resource_type) -> base_id
                         (used when scanner IDs need normalization based on type)
        """
        added = []

        for resource in actual_resources:
            # Get terraform type from resource
            terraform_type = getattr(
                resource, "terraform_type", str(resource.resource_type)
            )
            # Extract base ID for comparison if extractor provided
            if id_extractor:
                base_id = id_extractor(resource.id, terraform_type)
            else:
                base_id = resource.id

            if base_id not in tf_state_ids:
                resource_name = getattr(resource, "original_name", None) or base_id

                drift = ResourceDrift(
                    resource_type=terraform_type,
                    resource_id=base_id,  # Use base ID for display
                    resource_name=resource_name,
                    tf_address="",
                    drift_type=DriftType.ADDED,
                    severity=self._severity_for_added(terraform_type),
                )
                added.append(drift)

        return added

    def identify_removed_resources(
        self,
        tf_resources: list[TFResource],
        actual_ids: set[str],
        id_normalizer: Any | None = None,
    ) -> list[ResourceDrift]:
        """Find resources in Terraform state that no longer exist in AWS.

        These are resources deleted outside of Terraform.

        Args:
            tf_resources: Resources from Terraform state
            actual_ids: Set of normalized resource IDs from AWS
            id_normalizer: Optional function(id, type) -> normalized_id
        """
        removed = []

        for tf_resource in tf_resources:
            # Normalize the TF resource ID if normalizer provided
            if id_normalizer:
                normalized_id = id_normalizer(tf_resource.id, tf_resource.type)
            else:
                normalized_id = tf_resource.id

            if normalized_id not in actual_ids:
                drift = ResourceDrift(
                    resource_type=tf_resource.type,
                    resource_id=tf_resource.id,  # Keep original ID for display
                    resource_name=tf_resource.name,
                    tf_address=tf_resource.address,
                    drift_type=DriftType.REMOVED,
                    severity=DriftSeverity.HIGH,  # Removed resources are always high
                )
                removed.append(drift)

        return removed

    def _severity_for_added(self, resource_type: str) -> DriftSeverity:
        """Determine severity for an added resource."""
        critical_types = {"aws_security_group", "aws_iam_role", "aws_iam_policy"}
        high_types = {"aws_instance", "aws_db_instance", "aws_s3_bucket"}

        if resource_type in critical_types:
            return DriftSeverity.CRITICAL
        elif resource_type in high_types:
            return DriftSeverity.HIGH
        else:
            return DriftSeverity.MEDIUM
