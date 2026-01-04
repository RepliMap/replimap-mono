"""
Tests for the ScanErrorCollector unified error collection mechanism.

Verifies:
- Error collection and classification
- Severity levels (WARNING, ERROR, CRITICAL)
- Summary generation and Rich console output
- Decorator-based error handling
"""

from unittest.mock import MagicMock

from replimap.core.errors import (
    ErrorSeverity,
    ScanError,
    ScanErrorCollector,
    get_scan_error_collector,
    handle_scan_error,
    reset_scan_error_collector,
)


class TestScanErrorCollector:
    """Test basic ScanErrorCollector functionality."""

    def test_init_empty(self) -> None:
        """Collector initializes with empty state."""
        collector = ScanErrorCollector()
        assert not collector.has_errors()
        assert collector.get_error_count() == 0

    def test_add_error(self) -> None:
        """Add error records correctly."""
        collector = ScanErrorCollector()

        collector.add_error(
            resource_type="aws_instance",
            resource_id="i-1234",
            error=Exception("Test error"),
        )

        assert collector.has_errors()
        assert collector.get_error_count() == 1

    def test_error_classification_access_denied(self) -> None:
        """AccessDenied errors are classified correctly."""
        collector = ScanErrorCollector()

        collector.add_error(
            "aws_instance",
            "i-1234",
            Exception("AccessDenied: Not authorized"),
        )

        assert collector.errors[-1].error_type == "AccessDenied"

    def test_error_classification_throttling(self) -> None:
        """Throttling errors are classified correctly."""
        collector = ScanErrorCollector()

        collector.add_error("aws_instance", "i-1234", Exception("Rate exceeded"))

        assert collector.errors[-1].error_type == "Throttled"

    def test_error_classification_not_found(self) -> None:
        """NotFound errors are classified correctly."""
        collector = ScanErrorCollector()

        collector.add_error(
            "aws_instance", "i-1234", Exception("Resource not found in region")
        )

        assert collector.errors[-1].error_type == "NotFound"

    def test_error_classification_timeout(self) -> None:
        """Timeout errors are classified correctly."""
        collector = ScanErrorCollector()

        collector.add_error("aws_instance", "i-1234", Exception("Connection timeout"))

        assert collector.errors[-1].error_type == "Timeout"

    def test_error_classification_generic(self) -> None:
        """Unknown errors use exception class name."""
        collector = ScanErrorCollector()

        collector.add_error("aws_instance", "i-1234", ValueError("Invalid value"))

        assert collector.errors[-1].error_type == "ValueError"


class TestErrorSeverity:
    """Test severity level handling."""

    def test_has_critical_errors(self) -> None:
        """has_critical_errors detects critical severity."""
        collector = ScanErrorCollector()

        collector.add_error(
            "type",
            "id",
            Exception("Normal"),
            severity=ErrorSeverity.ERROR,
        )
        assert not collector.has_critical_errors()

        collector.add_error(
            "type",
            "id",
            Exception("Critical"),
            severity=ErrorSeverity.CRITICAL,
        )
        assert collector.has_critical_errors()

    def test_severity_in_summary(self) -> None:
        """Summary includes severity breakdown."""
        collector = ScanErrorCollector()

        collector.add_error("t", "1", Exception("e1"), severity=ErrorSeverity.WARNING)
        collector.add_error("t", "2", Exception("e2"), severity=ErrorSeverity.ERROR)
        collector.add_error("t", "3", Exception("e3"), severity=ErrorSeverity.CRITICAL)

        summary = collector.get_summary()

        assert summary["by_severity"]["warning"] == 1
        assert summary["by_severity"]["error"] == 1
        assert summary["by_severity"]["critical"] == 1


class TestSummaryGeneration:
    """Test summary and statistics."""

    def test_get_summary(self) -> None:
        """Summary includes all expected fields."""
        collector = ScanErrorCollector()

        collector.add_error("aws_instance", "i-1", Exception("Error 1"))
        collector.add_error("aws_instance", "i-2", Exception("Error 2"))
        collector.add_error("aws_s3_bucket", "b-1", Exception("Error 3"))

        summary = collector.get_summary()

        assert summary["total_errors"] == 3
        assert summary["by_resource_type"]["aws_instance"] == 2
        assert summary["by_resource_type"]["aws_s3_bucket"] == 1

    def test_get_errors_by_type(self) -> None:
        """Errors can be grouped by type."""
        collector = ScanErrorCollector()

        collector.add_error("t", "1", Exception("AccessDenied: No permissions"))
        collector.add_error("t", "2", Exception("AccessDenied: Unauthorized"))
        collector.add_error("t", "3", Exception("Timeout occurred"))

        by_type = collector.get_errors_by_type()

        assert by_type["AccessDenied"] == 2
        assert by_type["Timeout"] == 1


class TestPrintSummary:
    """Test Rich console output."""

    def test_print_summary_no_errors(self) -> None:
        """No output when no errors."""
        collector = ScanErrorCollector()
        console = MagicMock()

        collector.print_summary(console)

        console.print.assert_not_called()

    def test_print_summary_with_errors(self) -> None:
        """Summary is printed when errors exist."""
        collector = ScanErrorCollector()
        collector.add_error("aws_instance", "i-1", Exception("Test error"))

        console = MagicMock()
        collector.print_summary(console)

        # Should have called print at least twice (header + error)
        assert console.print.call_count >= 2

    def test_print_summary_truncates_long_list(self) -> None:
        """Long error list is truncated without verbose."""
        collector = ScanErrorCollector()

        # Add 10 errors
        for i in range(10):
            collector.add_error("aws_instance", f"i-{i}", Exception(f"Error {i}"))

        console = MagicMock()
        collector.print_summary(console, verbose=False)

        # Check that "and X more" message was printed
        printed_strings = [str(call) for call in console.print.call_args_list]
        has_more_message = any("more" in s for s in printed_strings)
        assert has_more_message

    def test_print_summary_shows_all_when_verbose(self) -> None:
        """Verbose mode shows all errors."""
        collector = ScanErrorCollector()

        for i in range(10):
            collector.add_error("aws_instance", f"i-{i}", Exception(f"Error {i}"))

        console = MagicMock()
        collector.print_summary(console, verbose=True)

        # Should print header + 10 errors + type summary
        # At minimum, more calls than non-verbose
        assert console.print.call_count > 10


class TestGlobalCollector:
    """Test global collector management."""

    def test_get_collector_singleton(self) -> None:
        """get_scan_error_collector returns same instance."""
        reset_scan_error_collector()

        collector1 = get_scan_error_collector()
        collector2 = get_scan_error_collector()

        assert collector1 is collector2

    def test_reset_collector(self) -> None:
        """reset_scan_error_collector creates new instance."""
        collector1 = get_scan_error_collector()
        collector1.add_error("type", "id", Exception("test"))

        collector2 = reset_scan_error_collector()

        assert collector2 is not collector1
        assert not collector2.has_errors()


class TestHandleScanErrorDecorator:
    """Test the handle_scan_error decorator."""

    def test_decorator_catches_exception(self) -> None:
        """Decorator catches exception and returns default."""
        reset_scan_error_collector()

        @handle_scan_error(
            resource_type="aws_instance",
            default_return=None,
        )
        def failing_function():
            raise ValueError("Test failure")

        result = failing_function()

        assert result is None
        collector = get_scan_error_collector()
        assert collector.has_errors()
        assert collector.errors[0].resource_type == "aws_instance"

    def test_decorator_success_passes_through(self) -> None:
        """Decorator allows successful results through."""
        reset_scan_error_collector()

        @handle_scan_error(
            resource_type="aws_instance",
            default_return=None,
        )
        def succeeding_function():
            return "success"

        result = succeeding_function()

        assert result == "success"
        collector = get_scan_error_collector()
        assert not collector.has_errors()

    def test_decorator_with_resource_id_getter(self) -> None:
        """Decorator extracts resource ID when getter provided."""
        reset_scan_error_collector()

        @handle_scan_error(
            resource_type="aws_instance",
            resource_id_getter=lambda args: args[0],
            default_return=None,
        )
        def failing_with_id(resource_id):
            raise ValueError("Test failure")

        failing_with_id("i-12345")

        collector = get_scan_error_collector()
        assert collector.errors[0].resource_id == "i-12345"


class TestScanError:
    """Test ScanError dataclass."""

    def test_str_with_resource_id(self) -> None:
        """String representation includes resource ID."""
        error = ScanError(
            resource_type="aws_instance",
            resource_id="i-1234",
            error_type="ValueError",
            message="Test error",
        )

        assert "i-1234" in str(error)
        assert "aws_instance" in str(error)
        assert "Test error" in str(error)

    def test_str_without_resource_id(self) -> None:
        """String representation works without resource ID."""
        error = ScanError(
            resource_type="aws_instance",
            resource_id=None,
            error_type="ValueError",
            message="Test error",
        )

        assert "aws_instance" in str(error)
        assert "Test error" in str(error)


class TestMaxErrors:
    """Test error limit behavior."""

    def test_max_errors_limit(self) -> None:
        """Collector stops adding after max_errors."""
        collector = ScanErrorCollector()
        collector._max_errors = 5

        for i in range(10):
            collector.add_error("type", f"id-{i}", Exception(f"Error {i}"))

        assert collector.get_error_count() == 5


class TestClear:
    """Test clearing errors."""

    def test_clear_removes_all_errors(self) -> None:
        """Clear removes all collected errors."""
        collector = ScanErrorCollector()

        collector.add_error("type", "id", Exception("test"))
        assert collector.has_errors()

        collector.clear()
        assert not collector.has_errors()
        assert collector.get_error_count() == 0
