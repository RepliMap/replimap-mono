"""
Operation Classifier - Classifies operations by safety level.

Safety Levels:
- SAFE: Can execute silently (timeout, retry, concurrency adjustments)
- CAUTION: Notify user after execution (skip service, use cached data)
- SENSITIVE: Must confirm before execution (identity switch, write ops)

This classification drives the behavior of the SilentRecoveryEngine
and determines when user interaction is required.
"""

from __future__ import annotations

from enum import Enum


class OperationSafety(Enum):
    """Operation safety level classification."""

    SAFE = "safe"
    """Execute silently - no user notification needed.

    Examples: timeout increase, retry with backoff, reduce concurrency
    """

    CAUTION = "caution"
    """Notify user after execution - no confirmation needed.

    Examples: skip service due to permission, use cached data
    """

    SENSITIVE = "sensitive"
    """Confirm before execution - requires user approval.

    Examples: switch profile, modify credentials, write operations
    """


class OperationClassifier:
    """
    Classifies operations by safety level.

    Used by the SilentRecoveryEngine to determine behavior:
    - SAFE operations are executed silently
    - CAUTION operations execute but notify the user
    - SENSITIVE operations require explicit confirmation (or fail in CI)

    Usage:
        safety = OperationClassifier.classify("switch_profile")
        if safety == OperationSafety.SENSITIVE:
            # Requires user confirmation
            pass
    """

    # Operations that can be executed silently (no user impact)
    SAFE_OPERATIONS: frozenset[str] = frozenset(
        {
            # Timeout/retry adjustments
            "increase_timeout",
            "decrease_timeout",
            "wait_and_retry",
            "use_exponential_backoff",
            "reset_retry_count",
            # Concurrency adjustments
            "reduce_concurrency",
            "increase_concurrency",
            "serialize_requests",
            # Caching
            "enable_cache",
            "refresh_cache",
            # Network adjustments
            "switch_region_endpoint",
            "use_regional_endpoint",
            "rotate_endpoint",
        }
    )

    # Operations that require user notification (may affect results)
    CAUTION_OPERATIONS: frozenset[str] = frozenset(
        {
            # Scope reduction
            "skip_service",
            "skip_resource",
            "skip_region",
            "reduce_scan_scope",
            # Fallback data
            "use_cached_data",
            "use_stale_data",
            "use_partial_data",
            # Degraded mode
            "enable_degraded_mode",
            "disable_enrichment",
            "disable_validation",
        }
    )

    # Operations that require explicit confirmation
    SENSITIVE_OPERATIONS: frozenset[str] = frozenset(
        {
            # Identity/credentials
            "switch_profile",
            "switch_credentials",
            "assume_role",
            "refresh_credentials",
            "clear_credential_cache",
            # Output modifications
            "modify_output_dir",
            "overwrite_output",
            "delete_output",
            # Write operations
            "write_operation",
            "delete_operation",
            "modify_resource",
            # Security
            "skip_ssl_verify",
            "disable_encryption",
            "use_insecure_connection",
            # State changes
            "clear_decisions",
            "import_decisions",
        }
    )

    @classmethod
    def classify(cls, operation: str) -> OperationSafety:
        """
        Classify an operation by safety level.

        Args:
            operation: Operation identifier (e.g., "switch_profile")

        Returns:
            OperationSafety level for the operation
        """
        if operation in cls.SAFE_OPERATIONS:
            return OperationSafety.SAFE
        if operation in cls.CAUTION_OPERATIONS:
            return OperationSafety.CAUTION
        if operation in cls.SENSITIVE_OPERATIONS:
            return OperationSafety.SENSITIVE
        # Unknown operations default to CAUTION (notify but don't block)
        return OperationSafety.CAUTION

    @classmethod
    def is_safe(cls, operation: str) -> bool:
        """Check if operation can be executed silently."""
        return cls.classify(operation) == OperationSafety.SAFE

    @classmethod
    def is_caution(cls, operation: str) -> bool:
        """Check if operation requires user notification."""
        return cls.classify(operation) == OperationSafety.CAUTION

    @classmethod
    def is_sensitive(cls, operation: str) -> bool:
        """Check if operation requires user confirmation."""
        return cls.classify(operation) == OperationSafety.SENSITIVE

    @classmethod
    def requires_confirmation(cls, operation: str) -> bool:
        """Check if operation requires user confirmation before execution."""
        return cls.classify(operation) == OperationSafety.SENSITIVE

    @classmethod
    def requires_notification(cls, operation: str) -> bool:
        """Check if operation requires user notification after execution."""
        return cls.classify(operation) in (
            OperationSafety.CAUTION,
            OperationSafety.SENSITIVE,
        )

    @classmethod
    def list_operations(cls, safety: OperationSafety) -> frozenset[str]:
        """
        List all operations of a given safety level.

        Args:
            safety: Safety level to filter by

        Returns:
            Frozenset of operation names
        """
        if safety == OperationSafety.SAFE:
            return cls.SAFE_OPERATIONS
        if safety == OperationSafety.CAUTION:
            return cls.CAUTION_OPERATIONS
        if safety == OperationSafety.SENSITIVE:
            return cls.SENSITIVE_OPERATIONS
        return frozenset()


__all__ = [
    "OperationClassifier",
    "OperationSafety",
]
