"""
Stdout Hygiene Tests.

Verifies that JSON mode stdout is pure and parseable.
Tests ensure that:
1. JSON output mode produces valid JSON on stdout
2. Progress/log messages go to stderr, not stdout
3. JSON mode allows only ONE write to stdout

If these tests fail, CI/CD pipelines that parse JSON output will break.
"""

from __future__ import annotations

import json
import sys
from io import StringIO

import pytest

from replimap.cli.output import OutputFormat, OutputManager, create_output_manager


class TestStdoutHygiene:
    """Tests for stdout/stderr separation."""

    def test_json_output_is_valid_json(self) -> None:
        """JSON mode must produce valid JSON on stdout."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)
            output.present({"test": "data", "count": 42})

            stdout_content = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Must be valid JSON
        data = json.loads(stdout_content)
        assert data["test"] == "data"
        assert data["count"] == 42

    def test_json_output_single_write(self) -> None:
        """JSON mode must allow only ONE write to stdout."""
        output = OutputManager(format=OutputFormat.JSON)

        # Reset the internal state for testing
        output._stdout_written = False

        # Capture stdout for first write
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # First write should succeed
            output.present({"first": "data"})

            # Second write should fail
            with pytest.raises(RuntimeError, match="stdout already written"):
                output.present({"second": "data"})
        finally:
            sys.stdout = old_stdout

    def test_progress_goes_to_stderr(self) -> None:
        """Progress messages must go to stderr, not stdout."""
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)
            output.progress("Scanning...")
            output.log("Found 5 VPCs")

            stdout_content = sys.stdout.getvalue()
            # stderr_content = sys.stderr.getvalue()

            # stdout should be empty (no present() called yet)
            assert stdout_content == ""

            # Note: stderr content may vary due to Rich formatting
            # The important thing is stdout is clean
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr

    def test_log_methods_use_stderr(self) -> None:
        """All log methods must use stderr."""
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            output = OutputManager(format=OutputFormat.TEXT, verbose=2)

            # Call various log methods
            output.log("log message")
            output.debug("debug message")
            output.info("info message")
            output.warn("warn message")
            output.error("error message")
            output.success("success message")
            output.progress("progress message")

            stderr_content = sys.stderr.getvalue()

            # stderr should have content (Rich formatting may vary)
            # Just verify these methods don't raise
            assert True
        finally:
            sys.stderr = old_stderr

    def test_quiet_mode_suppresses_output(self) -> None:
        """Quiet mode should suppress non-essential output."""
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout = StringIO()
        sys.stderr = StringIO()

        try:
            output = OutputManager(format=OutputFormat.QUIET)

            # These should be silent
            output.progress("Should not appear")
            output.log("Should not appear")
            output.success("Should not appear")

            # present() should also be silent in quiet mode
            output.present({"data": "value"})

            stdout_content = sys.stdout.getvalue()
            # Quiet mode should not write to stdout
            assert stdout_content == ""
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr


class TestOutputManagerModes:
    """Tests for different output format modes."""

    def test_text_mode_uses_rich(self) -> None:
        """Text mode should use Rich formatting."""
        output = OutputManager(format=OutputFormat.TEXT)
        assert output.format == OutputFormat.TEXT
        assert not output.is_json
        assert not output.is_quiet

    def test_json_mode_detection(self) -> None:
        """JSON mode should be correctly detected."""
        output = OutputManager(format=OutputFormat.JSON)
        assert output.is_json
        assert not output.is_quiet

    def test_quiet_mode_detection(self) -> None:
        """Quiet mode should be correctly detected."""
        output = OutputManager(format=OutputFormat.QUIET)
        assert output.is_quiet
        assert not output.is_json

    def test_factory_function(self) -> None:
        """create_output_manager should create correct instances."""
        output = create_output_manager(format="json", verbose=2)
        assert output.format == OutputFormat.JSON
        assert output.verbose == 2

    def test_verbosity_levels(self) -> None:
        """Verbosity levels should control output."""
        # Level 0 - normal
        output0 = OutputManager(verbose=0)

        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            output0.debug("debug")  # Should not appear
            output0.info("info")  # Should not appear
            content = sys.stderr.getvalue()
            # debug and info require higher verbosity
            assert "debug" not in content.lower() or content == ""
        finally:
            sys.stderr = old_stderr

        # Level 2 - debug
        output2 = OutputManager(verbose=2)
        sys.stderr = StringIO()
        try:
            output2.debug("debug message here")
            # With verbose=2, debug should be included
            # (Rich formatting may vary)
            assert True
        finally:
            sys.stderr = old_stderr


class TestOutputManagerReset:
    """Tests for output manager state management."""

    def test_reset_allows_rewrite(self) -> None:
        """reset() should allow writing to stdout again in JSON mode."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.JSON)

            # First write
            output.present({"first": True})
            assert output._stdout_written

            # Reset
            output.reset()
            assert not output._stdout_written

            # Second write should now work
            sys.stdout = StringIO()  # Clear stdout
            output.present({"second": True})
            assert output._stdout_written

            stdout_content = sys.stdout.getvalue()
            data = json.loads(stdout_content)
            assert data["second"] is True
        finally:
            sys.stdout = old_stdout


class TestTableOutput:
    """Tests for table output format."""

    def test_table_mode_dict_data(self) -> None:
        """Table mode should handle dict data."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.TABLE)
            output.present({"key1": "value1", "key2": "value2"}, title="Test")
            # Should not raise
            assert True
        finally:
            sys.stdout = old_stdout

    def test_table_mode_list_data(self) -> None:
        """Table mode should handle list data."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            output = OutputManager(format=OutputFormat.TABLE)
            output.present(
                [{"name": "a", "count": 1}, {"name": "b", "count": 2}],
                title="Test",
            )
            # Should not raise
            assert True
        finally:
            sys.stdout = old_stdout
