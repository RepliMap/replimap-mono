"""
Enhanced Error Handling Framework for RepliMap.

This module provides comprehensive error tracking, classification,
aggregation, and reporting for AWS scanning operations.

Features:
- Error categorization (Permission, Transient, Validation, Resource, Service)
- Resource-level error tracking
- Error aggregation and statistics
- Recovery recommendations
- Scan completion status classification
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCategory(str, Enum):
    """Categories of errors for classification and handling."""

    PERMISSION = "permission"  # AccessDenied, UnauthorizedAccess
    TRANSIENT = "transient"  # Throttling, ServiceUnavailable, Timeout
    VALIDATION = "validation"  # MalformedQueryString, InvalidParameter
    RESOURCE = "resource"  # ResourceNotFound, ConflictException
    SERVICE = "service"  # InternalError, ServiceUnavailable
    UNKNOWN = "unknown"  # Unclassified errors

    def __str__(self) -> str:
        return self.value


class ScanCompletionStatus(str, Enum):
    """Status indicating how completely a scan finished."""

    FULL_SUCCESS = "full_success"  # All resources scanned successfully
    PARTIAL_SUCCESS = "partial_success"  # Some resource types failed
    DEGRADED = "degraded"  # Major resource types failed
    FAILED = "failed"  # Complete failure

    def __str__(self) -> str:
        return self.value


# Error code to category mapping
PERMISSION_ERRORS = frozenset([
    "AccessDenied",
    "AccessDeniedException",
    "UnauthorizedAccess",
    "InvalidClientTokenId",
    "ExpiredToken",
    "ExpiredTokenException",
    "UnrecognizedClientException",
    "SignatureDoesNotMatch",
    "IncompleteSignature",
    "MissingAuthenticationToken",
])

TRANSIENT_ERRORS = frozenset([
    "Throttling",
    "ThrottlingException",
    "RequestLimitExceeded",
    "TooManyRequestsException",
    "ProvisionedThroughputExceededException",
    "RequestTimeout",
    "RequestTimeoutException",
    "ServiceUnavailable",
    "ServiceUnavailableException",
])

VALIDATION_ERRORS = frozenset([
    "ValidationException",
    "ValidationError",
    "InvalidParameterValue",
    "InvalidParameterException",
    "InvalidParameter",
    "MalformedQueryString",
    "MissingParameter",
    "MissingRequiredParameter",
    "InvalidInput",
    "InvalidAction",
])

RESOURCE_ERRORS = frozenset([
    "ResourceNotFoundException",
    "ResourceNotFound",
    "NoSuchEntity",
    "NoSuchBucket",
    "DBInstanceNotFound",
    "DBClusterNotFound",
    "ConflictException",
    "ResourceAlreadyExists",
    "EntityAlreadyExists",
])

SERVICE_ERRORS = frozenset([
    "InternalError",
    "InternalFailure",
    "InternalServiceError",
    "ServiceException",
    "ServerException",
])


def categorize_error(error_code: str) -> ErrorCategory:
    """
    Categorize an AWS error code.

    Args:
        error_code: AWS error code (e.g., "AccessDenied")

    Returns:
        ErrorCategory for the error
    """
    if error_code in PERMISSION_ERRORS:
        return ErrorCategory.PERMISSION
    if error_code in TRANSIENT_ERRORS:
        return ErrorCategory.TRANSIENT
    if error_code in VALIDATION_ERRORS:
        return ErrorCategory.VALIDATION
    if error_code in RESOURCE_ERRORS:
        return ErrorCategory.RESOURCE
    if error_code in SERVICE_ERRORS:
        return ErrorCategory.SERVICE
    return ErrorCategory.UNKNOWN


def is_retryable(error_code: str) -> bool:
    """
    Check if an error code indicates a retryable error.

    Args:
        error_code: AWS error code

    Returns:
        True if the error is retryable
    """
    return error_code in TRANSIENT_ERRORS or error_code in SERVICE_ERRORS


def get_recovery_recommendation(category: ErrorCategory, error_code: str) -> str:
    """
    Get a recovery recommendation for an error.

    Args:
        category: Error category
        error_code: AWS error code

    Returns:
        Human-readable recovery recommendation
    """
    recommendations = {
        ErrorCategory.PERMISSION: (
            "Check IAM permissions. Ensure the scanning role/user has "
            "the required read-only permissions for this service."
        ),
        ErrorCategory.TRANSIENT: (
            "This is a temporary issue. Wait a few minutes and retry. "
            "Consider reducing scan concurrency if throttling persists."
        ),
        ErrorCategory.VALIDATION: (
            "Check the resource configuration or request parameters. "
            "This may indicate an invalid filter or resource identifier."
        ),
        ErrorCategory.RESOURCE: (
            "The requested resource was not found or has been deleted. "
            "This may be normal if resources were recently modified."
        ),
        ErrorCategory.SERVICE: (
            "AWS service is experiencing issues. Wait and retry later. "
            "Check AWS Service Health Dashboard for outages."
        ),
        ErrorCategory.UNKNOWN: (
            "Unexpected error occurred. Check logs for details and "
            "consider reporting this issue."
        ),
    }
    return recommendations.get(category, recommendations[ErrorCategory.UNKNOWN])


@dataclass
class DetailedError:
    """
    Detailed error record with full context.

    Extends the basic ErrorRecord with resource-level tracking,
    retry information, and recovery recommendations.
    """

    # Error identification
    error_code: str
    error_message: str
    category: ErrorCategory

    # Context
    timestamp: datetime = field(default_factory=datetime.now)
    scanner_name: str = ""
    operation: str = ""
    region: str = ""
    account_id: str = ""

    # Resource context
    resource_type: str = ""
    resource_id: str = ""
    resource_name: str = ""

    # Retry information
    retry_count: int = 0
    was_retried: bool = False
    retry_successful: bool = False

    # AWS request context
    request_id: str = ""

    # Recovery
    recovery_recommendation: str = ""

    def __post_init__(self) -> None:
        """Generate recovery recommendation if not provided."""
        if not self.recovery_recommendation:
            self.recovery_recommendation = get_recovery_recommendation(
                self.category, self.error_code
            )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error_code": self.error_code,
            "error_message": self.error_message,
            "category": str(self.category),
            "timestamp": self.timestamp.isoformat(),
            "scanner_name": self.scanner_name,
            "operation": self.operation,
            "region": self.region,
            "account_id": self.account_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "retry_count": self.retry_count,
            "was_retried": self.was_retried,
            "retry_successful": self.retry_successful,
            "request_id": self.request_id,
            "recovery_recommendation": self.recovery_recommendation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DetailedError:
        """Create from dictionary."""
        return cls(
            error_code=data["error_code"],
            error_message=data["error_message"],
            category=ErrorCategory(data["category"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            scanner_name=data.get("scanner_name", ""),
            operation=data.get("operation", ""),
            region=data.get("region", ""),
            account_id=data.get("account_id", ""),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            resource_name=data.get("resource_name", ""),
            retry_count=data.get("retry_count", 0),
            was_retried=data.get("was_retried", False),
            retry_successful=data.get("retry_successful", False),
            request_id=data.get("request_id", ""),
            recovery_recommendation=data.get("recovery_recommendation", ""),
        )

    @classmethod
    def from_client_error(
        cls,
        error: Any,  # botocore.exceptions.ClientError
        scanner_name: str = "",
        operation: str = "",
        region: str = "",
        account_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        resource_name: str = "",
        retry_count: int = 0,
    ) -> DetailedError:
        """
        Create from a boto3 ClientError.

        Args:
            error: The ClientError exception
            scanner_name: Name of the scanner that caught the error
            operation: AWS operation being performed
            region: AWS region
            account_id: AWS account ID
            resource_type: Type of resource being processed
            resource_id: ID of the resource
            resource_name: Name of the resource
            retry_count: Number of retry attempts

        Returns:
            DetailedError instance
        """
        error_response = getattr(error, "response", {})
        error_info = error_response.get("Error", {})

        error_code = error_info.get("Code", "Unknown")
        error_message = error_info.get("Message", str(error))

        # Try to get request ID from response metadata
        request_id = error_response.get("ResponseMetadata", {}).get(
            "RequestId", ""
        )

        return cls(
            error_code=error_code,
            error_message=error_message,
            category=categorize_error(error_code),
            scanner_name=scanner_name,
            operation=operation,
            region=region,
            account_id=account_id,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            retry_count=retry_count,
            was_retried=retry_count > 0,
            request_id=request_id,
        )


@dataclass
class ErrorAggregator:
    """
    Aggregates and analyzes errors from scanning operations.

    Provides methods for querying errors by category, resource type,
    scanner, and generating statistics and reports.
    """

    errors: list[DetailedError] = field(default_factory=list)
    max_errors: int = 1000  # Maximum errors to retain

    def record(self, error: DetailedError) -> None:
        """
        Record an error.

        Args:
            error: The error to record
        """
        self.errors.append(error)

        # Trim to max size (FIFO)
        if len(self.errors) > self.max_errors:
            self.errors = self.errors[-self.max_errors :]

        logger.debug(
            f"Recorded error: {error.error_code} in {error.scanner_name} "
            f"({error.category})"
        )

    def record_batch(self, errors: list[DetailedError]) -> None:
        """
        Record multiple errors.

        Args:
            errors: List of errors to record
        """
        for error in errors:
            self.record(error)

    def clear(self) -> None:
        """Clear all recorded errors."""
        self.errors.clear()

    # Query methods

    def get_by_category(self, category: ErrorCategory) -> list[DetailedError]:
        """Get errors by category."""
        return [e for e in self.errors if e.category == category]

    def get_by_scanner(self, scanner_name: str) -> list[DetailedError]:
        """Get errors by scanner name."""
        return [e for e in self.errors if e.scanner_name == scanner_name]

    def get_by_resource_type(self, resource_type: str) -> list[DetailedError]:
        """Get errors by resource type."""
        return [e for e in self.errors if e.resource_type == resource_type]

    def get_by_region(self, region: str) -> list[DetailedError]:
        """Get errors by region."""
        return [e for e in self.errors if e.region == region]

    def get_permission_errors(self) -> list[DetailedError]:
        """Get all permission-related errors."""
        return self.get_by_category(ErrorCategory.PERMISSION)

    def get_transient_errors(self) -> list[DetailedError]:
        """Get all transient/retryable errors."""
        return self.get_by_category(ErrorCategory.TRANSIENT)

    def get_retried_errors(self) -> list[DetailedError]:
        """Get errors that were retried."""
        return [e for e in self.errors if e.was_retried]

    def get_unique_error_codes(self) -> set[str]:
        """Get unique error codes encountered."""
        return {e.error_code for e in self.errors}

    # Statistics

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive error statistics.

        Returns:
            Dictionary with error statistics
        """
        category_counts: dict[str, int] = {}
        for error in self.errors:
            cat_name = str(error.category)
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1

        scanner_counts: dict[str, int] = {}
        for error in self.errors:
            if error.scanner_name:
                scanner_counts[error.scanner_name] = (
                    scanner_counts.get(error.scanner_name, 0) + 1
                )

        resource_type_counts: dict[str, int] = {}
        for error in self.errors:
            if error.resource_type:
                resource_type_counts[error.resource_type] = (
                    resource_type_counts.get(error.resource_type, 0) + 1
                )

        retried = [e for e in self.errors if e.was_retried]
        retry_successful = [e for e in retried if e.retry_successful]

        return {
            "total_errors": len(self.errors),
            "unique_error_codes": len(self.get_unique_error_codes()),
            "by_category": category_counts,
            "by_scanner": scanner_counts,
            "by_resource_type": resource_type_counts,
            "retried_count": len(retried),
            "retry_success_count": len(retry_successful),
            "retry_success_rate": (
                len(retry_successful) / len(retried) if retried else 0.0
            ),
            "has_permission_errors": len(self.get_permission_errors()) > 0,
            "has_transient_errors": len(self.get_transient_errors()) > 0,
        }

    def get_summary(self) -> str:
        """
        Get a human-readable summary of errors.

        Returns:
            Multi-line summary string
        """
        stats = self.get_statistics()

        lines = [
            f"Total Errors: {stats['total_errors']}",
            f"Unique Error Codes: {stats['unique_error_codes']}",
            "",
            "By Category:",
        ]

        for category, count in stats["by_category"].items():
            lines.append(f"  {category}: {count}")

        if stats["by_scanner"]:
            lines.append("")
            lines.append("By Scanner:")
            for scanner, count in stats["by_scanner"].items():
                lines.append(f"  {scanner}: {count}")

        if stats["retried_count"] > 0:
            lines.append("")
            lines.append(
                f"Retried: {stats['retried_count']} "
                f"(success rate: {stats['retry_success_rate']:.1%})"
            )

        return "\n".join(lines)

    # Completion status

    def get_completion_status(
        self,
        total_scanners: int,
        failed_scanners: int,
        critical_resource_types: set[str] | None = None,
    ) -> ScanCompletionStatus:
        """
        Determine scan completion status based on errors.

        Args:
            total_scanners: Total number of scanners attempted
            failed_scanners: Number of scanners that failed completely
            critical_resource_types: Resource types considered critical

        Returns:
            ScanCompletionStatus indicating how completely the scan finished
        """
        if failed_scanners == 0 and len(self.errors) == 0:
            return ScanCompletionStatus.FULL_SUCCESS

        if failed_scanners == total_scanners:
            return ScanCompletionStatus.FAILED

        # Check if critical resource types failed
        if critical_resource_types:
            failed_types = {
                e.resource_type
                for e in self.errors
                if e.category != ErrorCategory.TRANSIENT
            }
            critical_failures = critical_resource_types & failed_types
            if critical_failures:
                return ScanCompletionStatus.DEGRADED

        # Partial success if some scanners succeeded
        if failed_scanners > 0 or len(self.errors) > 0:
            return ScanCompletionStatus.PARTIAL_SUCCESS

        return ScanCompletionStatus.FULL_SUCCESS

    # Recovery recommendations

    def get_recovery_actions(self) -> list[str]:
        """
        Get unique recovery recommendations for all errors.

        Returns:
            List of unique recovery recommendations
        """
        recommendations = set()
        for error in self.errors:
            if error.recovery_recommendation:
                recommendations.add(error.recovery_recommendation)
        return sorted(recommendations)

    def get_permission_requirements(self) -> list[str]:
        """
        Get list of operations that need permissions.

        Returns:
            List of operations that failed due to permission errors
        """
        perm_errors = self.get_permission_errors()
        operations = set()
        for error in perm_errors:
            if error.operation:
                operations.add(error.operation)
            elif error.scanner_name:
                operations.add(f"{error.scanner_name} scanning")
        return sorted(operations)

    def to_dict(self) -> dict[str, Any]:
        """Convert aggregator to dictionary for serialization."""
        return {
            "errors": [e.to_dict() for e in self.errors],
            "statistics": self.get_statistics(),
        }


# Global error aggregator for shared state
_global_aggregator: ErrorAggregator | None = None


def get_error_aggregator() -> ErrorAggregator:
    """Get the global error aggregator."""
    global _global_aggregator
    if _global_aggregator is None:
        _global_aggregator = ErrorAggregator()
    return _global_aggregator


def reset_error_aggregator() -> None:
    """Reset the global error aggregator."""
    global _global_aggregator
    _global_aggregator = ErrorAggregator()
