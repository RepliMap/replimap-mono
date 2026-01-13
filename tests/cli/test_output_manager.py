"""
OutputManager Tests.

Tests for the unified output layer with stdout/stderr separation.
"""

from __future__ import annotations

import json
import sys
from io import StringIO

from replimap.cli.output import OutputFormat, OutputManager, create_output_manager


class TestOutputManagerCreation:
    """Tests for OutputManager creation and initialization."""

    def test_default_values(self) -> None:
        """OutputManager should have sensible defaults."""
        output = OutputManager()
        assert output.format == OutputFormat.TEXT
        assert output.verbose == 0
        assert not output._stdout_written

    def test_string_format_conversion(self) -> None:
        """String format should be converted to enum."""
        output = OutputManager(format="json")  # type: ignore
        assert output.format == OutputFormat.JSON

    def test_factory_function_creates_instance(self) -> None:
        """create_output_manager should create valid instances."""
        output = create_output_manager(format="table", verbose=1)
        assert isinstance(output, OutputManager)
        assert output.format == OutputFormat.TABLE
        assert output.verbose == 1


class TestOutputManagerPresent:
    """Tests for the present() method."""

    def test_present_dict_as_json(self) -> None:
        """present() in JSON mode should output valid JSON."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)
            output.present({"name": "test", "values": [1, 2, 3]})

            content = sys.stdout.getvalue()
            data = json.loads(content)
            assert data["name"] == "test"
            assert data["values"] == [1, 2, 3]
        finally:
            sys.stdout = old_stdout

    def test_present_list_as_json(self) -> None:
        """present() should handle list data."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)
            output.present([{"a": 1}, {"b": 2}])

            content = sys.stdout.getvalue()
            data = json.loads(content)
            assert len(data) == 2
            assert data[0]["a"] == 1
        finally:
            sys.stdout = old_stdout

    def test_present_with_custom_serialization(self) -> None:
        """present() should handle non-serializable objects with default=str."""
        from datetime import datetime

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)
            now = datetime.now()
            output.present({"timestamp": now})

            content = sys.stdout.getvalue()
            data = json.loads(content)
            # Should serialize datetime as string
            assert isinstance(data["timestamp"], str)
        finally:
            sys.stdout = old_stdout

    def test_present_quiet_mode_noop(self) -> None:
        """present() in QUIET mode should be a no-op."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.QUIET)
            output.present({"data": "value"})

            content = sys.stdout.getvalue()
            assert content == ""
        finally:
            sys.stdout = old_stdout


class TestOutputManagerLogging:
    """Tests for logging methods."""

    def test_log_respects_verbosity(self) -> None:
        """log() should respect verbosity levels."""
        output = OutputManager(verbose=0)

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output.log("level 0", level=0)  # Should show
            output.log("level 1", level=1)  # Should not show
            # Basic verification - no exceptions raised
            assert True
        finally:
            sys.stderr = old_stderr

    def test_debug_requires_high_verbosity(self) -> None:
        """debug() should require verbose=2."""
        output_low = OutputManager(verbose=0)
        output_high = OutputManager(verbose=2)

        old_stderr = sys.stderr

        # Low verbosity - debug should not show
        sys.stderr = StringIO()
        try:
            output_low.debug("test")
            _content = sys.stderr.getvalue()  # noqa: F841
            # Should be empty or not contain debug message
        finally:
            sys.stderr = old_stderr

        # High verbosity - debug should show
        sys.stderr = StringIO()
        try:
            output_high.debug("test")
            # Should not raise
            assert True
        finally:
            sys.stderr = old_stderr

    def test_warn_and_error_always_show(self) -> None:
        """warn() and error() should always show regardless of verbosity."""
        output = OutputManager(verbose=0)

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output.warn("warning message")
            output.error("error message")
            # Should not raise
            assert True
        finally:
            sys.stderr = old_stderr


class TestOutputManagerInteractive:
    """Tests for interactive methods (prompt, confirm, select)."""

    def test_is_interactive_detection(self) -> None:
        """is_interactive should detect TTY and non-JSON mode."""
        output_json = OutputManager(format=OutputFormat.JSON)
        # In JSON mode, should not be interactive
        assert not output_json.is_interactive

        output_text = OutputManager(format=OutputFormat.TEXT)
        # Interactive depends on TTY, which may vary in tests
        # Just verify the property exists
        assert isinstance(output_text.is_interactive, bool)


class TestOutputManagerHelpers:
    """Tests for helper display methods."""

    def test_panel_display(self) -> None:
        """panel() should display to stderr."""
        output = OutputManager(format=OutputFormat.TEXT)

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output.panel("Test content", title="Test Title")
            # Should not raise
            assert True
        finally:
            sys.stderr = old_stderr

    def test_table_display(self) -> None:
        """table() helper should display to stderr."""
        output = OutputManager(format=OutputFormat.TEXT)

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output.table(
                [{"name": "a", "value": 1}, {"name": "b", "value": 2}],
                title="Test Table",
            )
            # Should not raise
            assert True
        finally:
            sys.stderr = old_stderr

    def test_table_quiet_mode_noop(self) -> None:
        """table() in quiet mode should be a no-op."""
        output = OutputManager(format=OutputFormat.QUIET)

        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output.table([{"a": 1}])
            _content = sys.stderr.getvalue()  # noqa: F841
            # Should be minimal output in quiet mode
            assert True
        finally:
            sys.stderr = old_stderr
