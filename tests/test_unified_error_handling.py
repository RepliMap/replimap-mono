"""
Comprehensive tests for the unified error handling module.

Tests cover:
- BotocoreErrorLoader with defensive fallback
- ServiceSpecificRules S3 hybrid strategy
- ErrorClassifier context-aware classification
- should_count_for_circuit behavior (the key bug fix)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from replimap.core.resilience.errors.classifier import (
    ErrorAction,
    ErrorClassifier,
    ErrorContext,
)
from replimap.core.resilience.errors.loader import BotocoreErrorLoader
from replimap.core.resilience.errors.rules import ServiceSpecificRules


class TestBotocoreErrorLoader:
    """Tests for defensive botocore loading."""

    def setup_method(self) -> None:
        """Reset cache before each test."""
        BotocoreErrorLoader.reset_cache()

    def test_get_retryable_errors_returns_frozenset(self) -> None:
        """Should always return a frozenset."""
        result = BotocoreErrorLoader.get_retryable_errors()
        assert isinstance(result, frozenset)
        assert len(result) > 0

    def test_get_fatal_errors_returns_frozenset(self) -> None:
        """Should always return a frozenset."""
        result = BotocoreErrorLoader.get_fatal_errors()
        assert isinstance(result, frozenset)
        assert len(result) > 0

    def test_fallback_contains_critical_errors(self) -> None:
        """Fallback should contain all critical error codes."""
        retryable = BotocoreErrorLoader.FALLBACK_RETRYABLE_ERRORS
        fatal = BotocoreErrorLoader.FALLBACK_FATAL_ERRORS

        # Check throttling errors are retryable
        assert "Throttling" in retryable
        assert "ThrottlingException" in retryable
        assert "SlowDown" in retryable

        # Check fatal errors
        assert "AccessDenied" in fatal
        assert "ValidationException" in fatal
        assert "ResourceNotFoundException" in fatal

    def test_fallback_on_import_error(self) -> None:
        """Should use fallback if botocore module access fails."""
        BotocoreErrorLoader.reset_cache()

        # Patch to simulate missing botocore.loaders
        with patch.dict("sys.modules", {"botocore.loaders": None}):
            with patch(
                "replimap.core.resilience.errors.loader.BotocoreErrorLoader._load_retryable_from_botocore"
            ) as mock_load:
                mock_load.side_effect = ImportError("No module")
                result = BotocoreErrorLoader.get_retryable_errors()

                # Should return fallback, not crash
                assert result == BotocoreErrorLoader.FALLBACK_RETRYABLE_ERRORS

    def test_caches_result(self) -> None:
        """Should cache result for subsequent calls."""
        result1 = BotocoreErrorLoader.get_retryable_errors()
        result2 = BotocoreErrorLoader.get_retryable_errors()
        assert result1 is result2  # Same object (cached)

    def test_get_load_status(self) -> None:
        """Should return diagnostic information."""
        BotocoreErrorLoader.get_retryable_errors()  # Trigger load
        status = BotocoreErrorLoader.get_load_status()

        assert "attempted" in status
        assert "succeeded" in status
        assert "using_fallback" in status
        assert "botocore_version" in status
        assert "retryable_count" in status
        assert "fatal_count" in status

        assert isinstance(status["attempted"], bool)
        assert isinstance(status["retryable_count"], int)


class TestServiceSpecificRules:
    """Tests for service rules including S3 hybrid strategy."""

    def test_iam_is_always_global(self) -> None:
        """IAM operations should always be global."""
        assert ServiceSpecificRules.is_global_operation("iam", "GetUser") is True
        assert ServiceSpecificRules.is_global_operation("iam", "ListRoles") is True
        assert ServiceSpecificRules.is_global_operation("iam", "CreateRole") is True
        assert ServiceSpecificRules.is_global_operation("iam", "AnyOperation") is True

    def test_sts_is_always_global(self) -> None:
        """STS operations should always be global."""
        assert (
            ServiceSpecificRules.is_global_operation("sts", "GetCallerIdentity") is True
        )
        assert ServiceSpecificRules.is_global_operation("sts", "AssumeRole") is True

    def test_route53_is_always_global(self) -> None:
        """Route53 operations should always be global."""
        assert (
            ServiceSpecificRules.is_global_operation("route53", "ListHostedZones")
            is True
        )

    def test_ec2_is_always_regional(self) -> None:
        """EC2 operations should always be regional."""
        assert (
            ServiceSpecificRules.is_global_operation("ec2", "DescribeInstances")
            is False
        )
        assert ServiceSpecificRules.is_global_operation("ec2", "DescribeVpcs") is False
        assert ServiceSpecificRules.is_global_operation("ec2", "RunInstances") is False

    def test_rds_is_always_regional(self) -> None:
        """RDS operations should always be regional."""
        assert (
            ServiceSpecificRules.is_global_operation("rds", "DescribeDBInstances")
            is False
        )

    # ═══════════════════════════════════════════════════════════════════════
    # S3 HYBRID STRATEGY TESTS (CRITICAL)
    # ═══════════════════════════════════════════════════════════════════════

    def test_s3_listbuckets_is_global(self) -> None:
        """S3 ListBuckets should be global (Control Plane)."""
        assert ServiceSpecificRules.is_global_operation("s3", "ListBuckets") is True

    def test_s3_getbucketlocation_is_global(self) -> None:
        """S3 GetBucketLocation should be global (Control Plane)."""
        assert (
            ServiceSpecificRules.is_global_operation("s3", "GetBucketLocation") is True
        )

    def test_s3_createbucket_is_global(self) -> None:
        """S3 CreateBucket should be global (Control Plane)."""
        assert ServiceSpecificRules.is_global_operation("s3", "CreateBucket") is True

    def test_s3_listobjects_is_regional(self) -> None:
        """S3 ListObjectsV2 should be regional (Data Plane)."""
        assert ServiceSpecificRules.is_global_operation("s3", "ListObjectsV2") is False
        assert ServiceSpecificRules.is_global_operation("s3", "ListObjects") is False

    def test_s3_getobject_is_regional(self) -> None:
        """S3 GetObject should be regional (Data Plane)."""
        assert ServiceSpecificRules.is_global_operation("s3", "GetObject") is False
        assert ServiceSpecificRules.is_global_operation("s3", "PutObject") is False

    def test_s3_bucket_config_is_regional(self) -> None:
        """S3 bucket configuration operations should be regional."""
        assert (
            ServiceSpecificRules.is_global_operation("s3", "GetBucketPolicy") is False
        )
        assert (
            ServiceSpecificRules.is_global_operation("s3", "GetBucketVersioning")
            is False
        )
        assert (
            ServiceSpecificRules.is_global_operation("s3", "GetBucketEncryption")
            is False
        )

    def test_s3_unknown_operation_defaults_to_regional(self) -> None:
        """Unknown S3 operations should default to regional (conservative)."""
        assert (
            ServiceSpecificRules.is_global_operation("s3", "SomeNewOperation") is False
        )

    # ═══════════════════════════════════════════════════════════════════════
    # CIRCUIT BREAKER KEY TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_circuit_breaker_key_global_service(self) -> None:
        """Global services should have :global suffix."""
        key = ServiceSpecificRules.get_circuit_breaker_key(
            "iam", "us-east-1", "GetUser"
        )
        assert key == "iam:global"

    def test_circuit_breaker_key_regional_service(self) -> None:
        """Regional services should have :region suffix."""
        key = ServiceSpecificRules.get_circuit_breaker_key(
            "ec2", "eu-west-1", "DescribeInstances"
        )
        assert key == "ec2:eu-west-1"

    def test_circuit_breaker_key_s3_hybrid_global(self) -> None:
        """S3 global operations should have :global suffix."""
        key = ServiceSpecificRules.get_circuit_breaker_key(
            "s3", "us-east-1", "ListBuckets"
        )
        assert key == "s3:global"

    def test_circuit_breaker_key_s3_hybrid_regional(self) -> None:
        """S3 regional operations should have :region suffix."""
        key = ServiceSpecificRules.get_circuit_breaker_key(
            "s3", "us-east-1", "ListObjectsV2"
        )
        assert key == "s3:us-east-1"

    def test_circuit_breaker_key_different_regions(self) -> None:
        """Different regions should produce different keys."""
        key1 = ServiceSpecificRules.get_circuit_breaker_key(
            "ec2", "us-east-1", "DescribeInstances"
        )
        key2 = ServiceSpecificRules.get_circuit_breaker_key(
            "ec2", "eu-west-1", "DescribeInstances"
        )
        assert key1 != key2
        assert key1 == "ec2:us-east-1"
        assert key2 == "ec2:eu-west-1"

    def test_get_rate_limit(self) -> None:
        """Should return appropriate rate limits."""
        assert ServiceSpecificRules.get_rate_limit("ec2") == 20.0
        assert ServiceSpecificRules.get_rate_limit("iam") == 5.0
        assert ServiceSpecificRules.get_rate_limit("unknown") == 10.0  # default


class TestErrorClassifier:
    """Tests for context-aware error classification."""

    @pytest.fixture
    def classifier(self) -> ErrorClassifier:
        return ErrorClassifier()

    def _make_client_error(
        self, error_code: str, message: str = "Test error"
    ) -> MagicMock:
        """Create a mock ClientError."""
        error = MagicMock()
        error.response = {
            "Error": {"Code": error_code, "Message": message},
            "ResponseMetadata": {"RequestId": "test-request-123"},
        }
        return error

    # ═══════════════════════════════════════════════════════════════════════
    # THROTTLING TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_throttling_returns_backoff(self, classifier: ErrorClassifier) -> None:
        """Throttling errors should return BACKOFF action."""
        error = self._make_client_error("Throttling")
        context = ErrorContext(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
        )

        # Need to make it a real ClientError for isinstance check
        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="Throttling"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.BACKOFF
        assert result.should_count_for_circuit is True
        assert result.suggested_delay_ms > 0

    def test_slowdown_has_longer_delay(self, classifier: ErrorClassifier) -> None:
        """SlowDown should have longer base delay than other throttling."""
        context = ErrorContext(
            service_name="s3",
            region="us-east-1",
            operation_name="ListObjectsV2",
            consecutive_failures=0,
        )

        # Test delay calculation directly
        slowdown_delay = classifier._calculate_delay(context, "SlowDown")
        throttling_delay = classifier._calculate_delay(context, "Throttling")

        # SlowDown base is 3000ms, Throttling base is 2000ms
        # After jitter, SlowDown should generally be >= Throttling
        assert slowdown_delay >= 2400  # 3000 * 0.8 minimum
        assert throttling_delay >= 1600  # 2000 * 0.8 minimum
        # SlowDown should have higher base than Throttling
        assert slowdown_delay >= throttling_delay * 0.8  # Allow some jitter variance

    # ═══════════════════════════════════════════════════════════════════════
    # FATAL ERROR TESTS (CRITICAL: should_count_for_circuit = False)
    # ═══════════════════════════════════════════════════════════════════════

    def test_access_denied_returns_fail_no_circuit(
        self, classifier: ErrorClassifier
    ) -> None:
        """AccessDenied should FAIL and NOT count for circuit breaker."""
        error = self._make_client_error("AccessDenied")
        context = ErrorContext(
            service_name="s3",
            region="us-east-1",
            operation_name="ListBuckets",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="AccessDenied"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.FAIL
        assert result.should_count_for_circuit is False  # KEY TEST

    def test_validation_exception_returns_fail_no_circuit(
        self, classifier: ErrorClassifier
    ) -> None:
        """ValidationException should FAIL and NOT count for circuit."""
        error = self._make_client_error("ValidationException")
        context = ErrorContext(
            service_name="dynamodb",
            region="us-east-1",
            operation_name="PutItem",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="ValidationException"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.FAIL
        assert result.should_count_for_circuit is False  # KEY TEST

    def test_expired_token_returns_fail_no_circuit(
        self, classifier: ErrorClassifier
    ) -> None:
        """ExpiredToken should FAIL and NOT count for circuit."""
        error = self._make_client_error("ExpiredToken")
        context = ErrorContext(
            service_name="sts",
            region="us-east-1",
            operation_name="GetCallerIdentity",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="ExpiredToken"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.FAIL
        assert result.should_count_for_circuit is False  # KEY TEST

    # ═══════════════════════════════════════════════════════════════════════
    # RESOURCE NOT FOUND TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_resource_not_found_describe_first_attempt_retries(
        self, classifier: ErrorClassifier
    ) -> None:
        """ResourceNotFound on describe (first attempt) should retry for EC."""
        error = self._make_client_error("ResourceNotFoundException")
        context = ErrorContext(
            service_name="dynamodb",
            region="us-east-1",
            operation_name="DescribeTable",
            resource_id="my-table",
            is_describe_operation=True,
            consecutive_failures=0,
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier,
                "_extract_error_code",
                return_value="ResourceNotFoundException",
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.RETRY
        assert result.should_count_for_circuit is False  # Don't penalize for EC

    def test_resource_not_found_describe_second_attempt_ignores(
        self, classifier: ErrorClassifier
    ) -> None:
        """ResourceNotFound on describe (second attempt) should IGNORE."""
        error = self._make_client_error("ResourceNotFoundException")
        context = ErrorContext(
            service_name="dynamodb",
            region="us-east-1",
            operation_name="DescribeTable",
            resource_id="my-table",
            is_describe_operation=True,
            consecutive_failures=1,  # Second attempt
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier,
                "_extract_error_code",
                return_value="ResourceNotFoundException",
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.IGNORE
        assert result.should_count_for_circuit is False

    def test_resource_not_found_non_describe_fails(
        self, classifier: ErrorClassifier
    ) -> None:
        """ResourceNotFound on non-describe should FAIL."""
        error = self._make_client_error("NoSuchBucket")
        context = ErrorContext(
            service_name="s3",
            region="us-east-1",
            operation_name="PutObject",  # Not a describe operation
            is_describe_operation=False,
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="NoSuchBucket"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.FAIL
        assert result.should_count_for_circuit is False

    # ═══════════════════════════════════════════════════════════════════════
    # TRANSIENT ERROR TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_service_unavailable_returns_retry(
        self, classifier: ErrorClassifier
    ) -> None:
        """ServiceUnavailable should retry and count for circuit."""
        error = self._make_client_error("ServiceUnavailable")
        context = ErrorContext(
            service_name="rds",
            region="us-east-1",
            operation_name="DescribeDBInstances",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="ServiceUnavailable"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.RETRY
        assert result.should_count_for_circuit is True

    def test_internal_error_returns_retry(self, classifier: ErrorClassifier) -> None:
        """InternalError should retry and count for circuit."""
        error = self._make_client_error("InternalError")
        context = ErrorContext(
            service_name="lambda",
            region="us-east-1",
            operation_name="ListFunctions",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="InternalError"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.RETRY
        assert result.should_count_for_circuit is True

    # ═══════════════════════════════════════════════════════════════════════
    # UNKNOWN ERROR TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_unknown_error_returns_retry_conservative(
        self, classifier: ErrorClassifier
    ) -> None:
        """Unknown errors should default to RETRY (conservative)."""
        error = self._make_client_error("SomeNewUnknownError")
        context = ErrorContext(
            service_name="newservice",
            region="us-east-1",
            operation_name="NewOperation",
        )

        with patch.object(classifier, "_is_client_error", return_value=True):
            with patch.object(
                classifier, "_extract_error_code", return_value="SomeNewUnknownError"
            ):
                result = classifier.classify(error, context)

        assert result.action == ErrorAction.RETRY
        assert result.should_count_for_circuit is True

    # ═══════════════════════════════════════════════════════════════════════
    # DELAY CALCULATION TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_exponential_backoff(self, classifier: ErrorClassifier) -> None:
        """Delay should increase exponentially with consecutive failures."""
        context = ErrorContext(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
            consecutive_failures=0,
        )

        delay_0 = classifier._calculate_delay(context, "Throttling")

        context.consecutive_failures = 1
        delay_1 = classifier._calculate_delay(context, "Throttling")

        context.consecutive_failures = 2
        delay_2 = classifier._calculate_delay(context, "Throttling")

        # Each should roughly double (allowing for ±20% jitter)
        # Worst case ratio: (base*2*0.8)/(base*1.2) = 1.33
        assert delay_1 > delay_0 * 1.3
        assert delay_2 > delay_1 * 1.3

    def test_max_delay_capped(self, classifier: ErrorClassifier) -> None:
        """Delay should be capped at maximum."""
        context = ErrorContext(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
            consecutive_failures=20,  # Very high
        )

        delay = classifier._calculate_delay(context, "Throttling")

        # Should be capped at 64000ms * jitter (max ~76800)
        assert delay <= 80000
