"""Tests for scanner improvements - parallel execution and retry logic."""

import time
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from replimap.scanners.base import (
    MAX_SCANNER_WORKERS,
    BaseScanner,
    ScannerRegistry,
    _run_scanners_parallel,
    _run_scanners_sequential,
    run_all_scanners,
    with_retry,
)


class TestWithRetryDecorator:
    """Tests for the with_retry decorator."""

    def test_successful_call_no_retry(self) -> None:
        """Test that successful calls don't trigger retries."""
        call_count = 0

        @with_retry(max_retries=3)
        def successful_func() -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_non_retryable_error_raises_immediately(self) -> None:
        """Test that non-retryable errors are raised immediately."""
        call_count = 0
        error_response = {"Error": {"Code": "AccessDenied", "Message": "Access denied"}}

        @with_retry(max_retries=3)
        def access_denied_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ClientError(error_response, "DescribeInstances")

        with pytest.raises(ClientError):
            access_denied_func()

        assert call_count == 1  # Should not retry

    def test_retryable_error_retries(self) -> None:
        """Test that retryable errors trigger retries."""
        call_count = 0
        error_response = {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}}

        @with_retry(max_retries=2, base_delay=0.01)
        def throttled_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ClientError(error_response, "DescribeInstances")

        with pytest.raises(ClientError):
            throttled_func()

        assert call_count == 3  # Initial + 2 retries

    def test_retry_succeeds_eventually(self) -> None:
        """Test that retry succeeds if function eventually works."""
        call_count = 0
        error_response = {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}}

        @with_retry(max_retries=3, base_delay=0.01)
        def flaky_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ClientError(error_response, "DescribeInstances")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    def test_custom_retryable_errors(self) -> None:
        """Test that custom retryable errors work."""
        call_count = 0
        error_response = {"Error": {"Code": "CustomError", "Message": "Custom"}}

        @with_retry(max_retries=2, base_delay=0.01, retryable_errors=("CustomError",))
        def custom_error_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ClientError(error_response, "CustomOperation")

        with pytest.raises(ClientError):
            custom_error_func()

        assert call_count == 3  # Initial + 2 retries


class MockScanner(BaseScanner):
    """Mock scanner for testing."""

    resource_types = ["aws_mock"]

    def __init__(
        self,
        session: MagicMock,
        region: str,
        delay: float = 0,
        should_fail: bool = False,
    ):
        super().__init__(session, region)
        self.delay = delay
        self.should_fail = should_fail
        self.scan_called = False

    def scan(self, graph: MagicMock) -> None:
        self.scan_called = True
        if self.delay:
            time.sleep(self.delay)
        if self.should_fail:
            raise RuntimeError("Scanner failed")


class TestParallelScanning:
    """Tests for parallel scanning functionality."""

    def test_sequential_scanning(self) -> None:
        """Test that sequential scanning works."""
        session = MagicMock()
        graph = MagicMock()

        class Scanner1(MockScanner):
            pass

        class Scanner2(MockScanner):
            pass

        scanner_classes = [Scanner1, Scanner2]
        results = _run_scanners_sequential(session, "us-east-1", graph, scanner_classes)

        assert "Scanner1" in results
        assert "Scanner2" in results
        assert results["Scanner1"] is None
        assert results["Scanner2"] is None

    def test_parallel_scanning(self) -> None:
        """Test that parallel scanning works."""
        session = MagicMock()
        graph = MagicMock()

        class Scanner1(MockScanner):
            pass

        class Scanner2(MockScanner):
            pass

        scanner_classes = [Scanner1, Scanner2]
        results = _run_scanners_parallel(
            session, "us-east-1", graph, scanner_classes, max_workers=2
        )

        assert "Scanner1" in results
        assert "Scanner2" in results
        assert results["Scanner1"] is None
        assert results["Scanner2"] is None

    def test_parallel_scanning_handles_errors(self) -> None:
        """Test that parallel scanning handles scanner errors."""
        session = MagicMock()
        graph = MagicMock()

        class FailingScanner(BaseScanner):
            resource_types = ["aws_fail"]

            def scan(self, graph: MagicMock) -> None:
                raise RuntimeError("Test failure")

        class SuccessScanner(BaseScanner):
            resource_types = ["aws_success"]

            def scan(self, graph: MagicMock) -> None:
                pass

        scanner_classes = [FailingScanner, SuccessScanner]
        results = _run_scanners_parallel(
            session, "us-east-1", graph, scanner_classes, max_workers=2
        )

        assert results["FailingScanner"] is not None
        assert isinstance(results["FailingScanner"], RuntimeError)
        assert results["SuccessScanner"] is None

    def test_run_all_scanners_parallel_flag(self) -> None:
        """Test that run_all_scanners respects parallel flag."""
        # Clear registry first
        ScannerRegistry.clear()

        session = MagicMock()
        graph = MagicMock()

        # Test with empty registry
        results = run_all_scanners(session, "us-east-1", graph, parallel=True)
        assert results == {}

        results = run_all_scanners(session, "us-east-1", graph, parallel=False)
        assert results == {}

    def test_max_workers_configuration(self) -> None:
        """Test that max workers is configurable."""
        assert MAX_SCANNER_WORKERS >= 1


class TestRetryableErrorCodes:
    """Tests for AWS error code handling."""

    @pytest.mark.parametrize(
        "error_code",
        [
            "Throttling",
            "ThrottlingException",
            "RequestLimitExceeded",
            "TooManyRequestsException",
            "ProvisionedThroughputExceededException",
            "ServiceUnavailable",
            "InternalError",
        ],
    )
    def test_retryable_error_codes(self, error_code: str) -> None:
        """Test that all expected error codes trigger retries."""
        call_count = 0
        error_response = {"Error": {"Code": error_code, "Message": "Test error"}}

        @with_retry(max_retries=1, base_delay=0.01)
        def error_func() -> None:
            nonlocal call_count
            call_count += 1
            raise ClientError(error_response, "TestOperation")

        with pytest.raises(ClientError):
            error_func()

        assert call_count == 2  # Initial + 1 retry
