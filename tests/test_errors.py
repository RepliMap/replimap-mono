"""
Tests for the enhanced error handling framework.

Tests cover:
- Error categorization
- DetailedError creation and serialization
- ErrorAggregator statistics and queries
- Scan completion status
- Recovery recommendations
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from replimap.core.errors import (
    DetailedError,
    ErrorAggregator,
    ErrorCategory,
    ScanCompletionStatus,
    categorize_error,
    get_error_aggregator,
    get_recovery_recommendation,
    is_retryable,
    reset_error_aggregator,
)


class TestErrorCategorization:
    """Tests for error categorization functions."""

    def test_categorize_permission_errors(self) -> None:
        """Should categorize permission errors correctly."""
        permission_codes = [
            "AccessDenied",
            "AccessDeniedException",
            "UnauthorizedAccess",
            "InvalidClientTokenId",
            "ExpiredToken",
        ]
        for code in permission_codes:
            assert categorize_error(code) == ErrorCategory.PERMISSION

    def test_categorize_transient_errors(self) -> None:
        """Should categorize transient errors correctly."""
        transient_codes = [
            "Throttling",
            "ThrottlingException",
            "RequestLimitExceeded",
            "ServiceUnavailable",
            "RequestTimeout",
        ]
        for code in transient_codes:
            assert categorize_error(code) == ErrorCategory.TRANSIENT

    def test_categorize_validation_errors(self) -> None:
        """Should categorize validation errors correctly."""
        validation_codes = [
            "ValidationException",
            "InvalidParameterValue",
            "MalformedQueryString",
            "MissingParameter",
        ]
        for code in validation_codes:
            assert categorize_error(code) == ErrorCategory.VALIDATION

    def test_categorize_resource_errors(self) -> None:
        """Should categorize resource errors correctly."""
        resource_codes = [
            "ResourceNotFoundException",
            "NoSuchEntity",
            "NoSuchBucket",
            "DBInstanceNotFound",
        ]
        for code in resource_codes:
            assert categorize_error(code) == ErrorCategory.RESOURCE

    def test_categorize_service_errors(self) -> None:
        """Should categorize service errors correctly."""
        service_codes = [
            "InternalError",
            "InternalFailure",
            "ServiceException",
        ]
        for code in service_codes:
            assert categorize_error(code) == ErrorCategory.SERVICE

    def test_categorize_unknown_errors(self) -> None:
        """Should categorize unknown errors as UNKNOWN."""
        assert categorize_error("SomeMadeUpError") == ErrorCategory.UNKNOWN
        assert categorize_error("") == ErrorCategory.UNKNOWN


class TestIsRetryable:
    """Tests for is_retryable function."""

    def test_transient_errors_are_retryable(self) -> None:
        """Transient errors should be retryable."""
        assert is_retryable("Throttling") is True
        assert is_retryable("ServiceUnavailable") is True
        assert is_retryable("RequestTimeout") is True

    def test_service_errors_are_retryable(self) -> None:
        """Service errors should be retryable."""
        assert is_retryable("InternalError") is True
        assert is_retryable("InternalFailure") is True

    def test_permission_errors_not_retryable(self) -> None:
        """Permission errors should not be retryable."""
        assert is_retryable("AccessDenied") is False
        assert is_retryable("UnauthorizedAccess") is False

    def test_validation_errors_not_retryable(self) -> None:
        """Validation errors should not be retryable."""
        assert is_retryable("ValidationException") is False
        assert is_retryable("InvalidParameterValue") is False


class TestRecoveryRecommendation:
    """Tests for recovery recommendations."""

    def test_permission_recommendation(self) -> None:
        """Should provide permission-related recommendation."""
        rec = get_recovery_recommendation(ErrorCategory.PERMISSION, "AccessDenied")
        assert "IAM permissions" in rec

    def test_transient_recommendation(self) -> None:
        """Should provide transient error recommendation."""
        rec = get_recovery_recommendation(ErrorCategory.TRANSIENT, "Throttling")
        assert "retry" in rec.lower()

    def test_validation_recommendation(self) -> None:
        """Should provide validation error recommendation."""
        rec = get_recovery_recommendation(
            ErrorCategory.VALIDATION, "InvalidParameterValue"
        )
        assert "configuration" in rec.lower() or "parameter" in rec.lower()


class TestDetailedError:
    """Tests for DetailedError dataclass."""

    def test_create_basic_error(self) -> None:
        """Should create error with required fields."""
        error = DetailedError(
            error_code="AccessDenied",
            error_message="Access denied to resource",
            category=ErrorCategory.PERMISSION,
        )

        assert error.error_code == "AccessDenied"
        assert error.error_message == "Access denied to resource"
        assert error.category == ErrorCategory.PERMISSION
        assert error.recovery_recommendation != ""  # Auto-generated

    def test_create_error_with_context(self) -> None:
        """Should create error with full context."""
        error = DetailedError(
            error_code="Throttling",
            error_message="Rate exceeded",
            category=ErrorCategory.TRANSIENT,
            scanner_name="EC2Scanner",
            operation="describe_instances",
            region="us-east-1",
            account_id="123456789012",
            resource_type="aws_instance",
            resource_id="i-12345",
            resource_name="my-instance",
            retry_count=3,
            was_retried=True,
        )

        assert error.scanner_name == "EC2Scanner"
        assert error.operation == "describe_instances"
        assert error.region == "us-east-1"
        assert error.retry_count == 3
        assert error.was_retried is True

    def test_to_dict_and_from_dict(self) -> None:
        """Should serialize and deserialize correctly."""
        original = DetailedError(
            error_code="AccessDenied",
            error_message="Access denied",
            category=ErrorCategory.PERMISSION,
            scanner_name="VPCScanner",
            region="us-west-2",
            retry_count=0,
        )

        data = original.to_dict()
        restored = DetailedError.from_dict(data)

        assert restored.error_code == original.error_code
        assert restored.error_message == original.error_message
        assert restored.category == original.category
        assert restored.scanner_name == original.scanner_name
        assert restored.region == original.region

    def test_from_client_error(self) -> None:
        """Should create from boto3 ClientError."""
        mock_error = MagicMock()
        mock_error.response = {
            "Error": {
                "Code": "AccessDenied",
                "Message": "User is not authorized",
            },
            "ResponseMetadata": {"RequestId": "req-123"},
        }

        error = DetailedError.from_client_error(
            mock_error,
            scanner_name="EC2Scanner",
            operation="describe_instances",
            region="us-east-1",
        )

        assert error.error_code == "AccessDenied"
        assert error.error_message == "User is not authorized"
        assert error.category == ErrorCategory.PERMISSION
        assert error.request_id == "req-123"


class TestErrorAggregator:
    """Tests for ErrorAggregator."""

    def test_record_single_error(self) -> None:
        """Should record a single error."""
        aggregator = ErrorAggregator()
        error = DetailedError(
            error_code="AccessDenied",
            error_message="Test",
            category=ErrorCategory.PERMISSION,
        )

        aggregator.record(error)

        assert len(aggregator.errors) == 1
        assert aggregator.errors[0] == error

    def test_record_batch_errors(self) -> None:
        """Should record multiple errors."""
        aggregator = ErrorAggregator()
        errors = [
            DetailedError(
                error_code="AccessDenied",
                error_message="Test1",
                category=ErrorCategory.PERMISSION,
            ),
            DetailedError(
                error_code="Throttling",
                error_message="Test2",
                category=ErrorCategory.TRANSIENT,
            ),
        ]

        aggregator.record_batch(errors)

        assert len(aggregator.errors) == 2

    def test_max_errors_limit(self) -> None:
        """Should trim errors to max limit."""
        aggregator = ErrorAggregator(max_errors=5)

        for i in range(10):
            error = DetailedError(
                error_code=f"Error{i}",
                error_message=f"Test {i}",
                category=ErrorCategory.UNKNOWN,
            )
            aggregator.record(error)

        assert len(aggregator.errors) == 5
        # Should keep most recent
        assert aggregator.errors[0].error_code == "Error5"

    def test_get_by_category(self) -> None:
        """Should filter errors by category."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("AccessDenied", "Test1", ErrorCategory.PERMISSION)
        )
        aggregator.record(
            DetailedError("Throttling", "Test2", ErrorCategory.TRANSIENT)
        )
        aggregator.record(
            DetailedError("ExpiredToken", "Test3", ErrorCategory.PERMISSION)
        )

        perm_errors = aggregator.get_by_category(ErrorCategory.PERMISSION)

        assert len(perm_errors) == 2
        assert all(e.category == ErrorCategory.PERMISSION for e in perm_errors)

    def test_get_by_scanner(self) -> None:
        """Should filter errors by scanner name."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test1", ErrorCategory.PERMISSION,
                scanner_name="EC2Scanner"
            )
        )
        aggregator.record(
            DetailedError(
                "Throttling", "Test2", ErrorCategory.TRANSIENT,
                scanner_name="RDSScanner"
            )
        )

        ec2_errors = aggregator.get_by_scanner("EC2Scanner")

        assert len(ec2_errors) == 1
        assert ec2_errors[0].scanner_name == "EC2Scanner"

    def test_get_by_resource_type(self) -> None:
        """Should filter errors by resource type."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test1", ErrorCategory.PERMISSION,
                resource_type="aws_instance"
            )
        )
        aggregator.record(
            DetailedError(
                "Throttling", "Test2", ErrorCategory.TRANSIENT,
                resource_type="aws_vpc"
            )
        )

        instance_errors = aggregator.get_by_resource_type("aws_instance")

        assert len(instance_errors) == 1

    def test_get_unique_error_codes(self) -> None:
        """Should return unique error codes."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("AccessDenied", "Test1", ErrorCategory.PERMISSION)
        )
        aggregator.record(
            DetailedError("AccessDenied", "Test2", ErrorCategory.PERMISSION)
        )
        aggregator.record(
            DetailedError("Throttling", "Test3", ErrorCategory.TRANSIENT)
        )

        codes = aggregator.get_unique_error_codes()

        assert codes == {"AccessDenied", "Throttling"}

    def test_get_statistics(self) -> None:
        """Should calculate correct statistics."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test1", ErrorCategory.PERMISSION,
                scanner_name="EC2Scanner"
            )
        )
        aggregator.record(
            DetailedError(
                "Throttling", "Test2", ErrorCategory.TRANSIENT,
                scanner_name="RDSScanner", was_retried=True, retry_successful=True
            )
        )

        stats = aggregator.get_statistics()

        assert stats["total_errors"] == 2
        assert stats["unique_error_codes"] == 2
        assert stats["by_category"]["permission"] == 1
        assert stats["by_category"]["transient"] == 1
        assert stats["by_scanner"]["EC2Scanner"] == 1
        assert stats["by_scanner"]["RDSScanner"] == 1
        assert stats["retried_count"] == 1
        assert stats["retry_success_count"] == 1
        assert stats["has_permission_errors"] is True

    def test_get_summary(self) -> None:
        """Should generate readable summary."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("AccessDenied", "Test", ErrorCategory.PERMISSION)
        )

        summary = aggregator.get_summary()

        assert "Total Errors: 1" in summary
        assert "permission" in summary


class TestScanCompletionStatus:
    """Tests for scan completion status determination."""

    def test_full_success(self) -> None:
        """Should return FULL_SUCCESS when no errors."""
        aggregator = ErrorAggregator()

        status = aggregator.get_completion_status(
            total_scanners=5, failed_scanners=0
        )

        assert status == ScanCompletionStatus.FULL_SUCCESS

    def test_failed_all(self) -> None:
        """Should return FAILED when all scanners fail."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("AccessDenied", "Test", ErrorCategory.PERMISSION)
        )

        status = aggregator.get_completion_status(
            total_scanners=3, failed_scanners=3
        )

        assert status == ScanCompletionStatus.FAILED

    def test_partial_success(self) -> None:
        """Should return PARTIAL_SUCCESS when some scanners fail."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("Throttling", "Test", ErrorCategory.TRANSIENT)
        )

        status = aggregator.get_completion_status(
            total_scanners=5, failed_scanners=1
        )

        assert status == ScanCompletionStatus.PARTIAL_SUCCESS

    def test_degraded_with_critical_failures(self) -> None:
        """Should return DEGRADED when critical resources fail."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test", ErrorCategory.PERMISSION,
                resource_type="aws_vpc"
            )
        )

        status = aggregator.get_completion_status(
            total_scanners=5,
            failed_scanners=0,
            critical_resource_types={"aws_vpc", "aws_subnet"},
        )

        assert status == ScanCompletionStatus.DEGRADED


class TestRecoveryActions:
    """Tests for recovery action recommendations."""

    def test_get_recovery_actions(self) -> None:
        """Should return unique recovery actions."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError("AccessDenied", "Test1", ErrorCategory.PERMISSION)
        )
        aggregator.record(
            DetailedError("Throttling", "Test2", ErrorCategory.TRANSIENT)
        )

        actions = aggregator.get_recovery_actions()

        assert len(actions) == 2

    def test_get_permission_requirements(self) -> None:
        """Should list operations needing permissions."""
        aggregator = ErrorAggregator()
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test1", ErrorCategory.PERMISSION,
                operation="describe_instances"
            )
        )
        aggregator.record(
            DetailedError(
                "AccessDenied", "Test2", ErrorCategory.PERMISSION,
                operation="describe_vpcs"
            )
        )

        requirements = aggregator.get_permission_requirements()

        assert "describe_instances" in requirements
        assert "describe_vpcs" in requirements


class TestGlobalAggregator:
    """Tests for global aggregator functions."""

    def test_get_global_aggregator(self) -> None:
        """Should return singleton aggregator."""
        reset_error_aggregator()

        agg1 = get_error_aggregator()
        agg2 = get_error_aggregator()

        assert agg1 is agg2

    def test_reset_global_aggregator(self) -> None:
        """Should create new aggregator on reset."""
        agg1 = get_error_aggregator()
        agg1.record(
            DetailedError("Test", "Test", ErrorCategory.UNKNOWN)
        )

        reset_error_aggregator()
        agg2 = get_error_aggregator()

        assert len(agg2.errors) == 0
