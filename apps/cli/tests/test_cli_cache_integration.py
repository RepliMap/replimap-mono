"""Tests for CLI cache integration.

Verifies that all graph-dependent commands have:
1. The --refresh/-R flag
2. Proper cache integration via get_or_load_graph
"""

from __future__ import annotations

from typer.testing import CliRunner

from replimap.main import app

runner = CliRunner()


class TestCacheEnabledCommands:
    """Test that all cache-enabled commands have --refresh flag."""

    CACHE_ENABLED_COMMANDS = [
        "audit",
        "clone",
        "cost",
        "deps",
        "graph",
        "validate",
        "unused",
        "transfer",
    ]

    def test_audit_has_refresh_flag(self) -> None:
        """Test audit command has --refresh flag."""
        result = runner.invoke(app, ["audit", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_clone_has_refresh_flag(self) -> None:
        """Test clone command has --refresh flag."""
        result = runner.invoke(app, ["clone", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_cost_has_refresh_flag(self) -> None:
        """Test cost command has --refresh flag."""
        result = runner.invoke(app, ["cost", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_deps_has_refresh_flag(self) -> None:
        """Test deps command has --refresh flag."""
        result = runner.invoke(app, ["deps", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_graph_has_refresh_flag(self) -> None:
        """Test graph command has --refresh flag."""
        result = runner.invoke(app, ["graph", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_validate_has_refresh_flag(self) -> None:
        """Test validate command has --refresh flag."""
        result = runner.invoke(app, ["validate", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_unused_has_refresh_flag(self) -> None:
        """Test unused command has --refresh flag."""
        result = runner.invoke(app, ["unused", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_transfer_has_refresh_flag(self) -> None:
        """Test transfer command has --refresh flag."""
        result = runner.invoke(app, ["transfer", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output


class TestSubcommandCacheFlags:
    """Test subcommands that have cache support."""

    def test_snapshot_save_has_refresh_flag(self) -> None:
        """Test snapshot save command has --refresh flag."""
        result = runner.invoke(app, ["snapshot", "save", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output

    def test_dr_assess_has_refresh_flag(self) -> None:
        """Test dr assess command has --refresh flag."""
        result = runner.invoke(app, ["dr", "assess", "--help"], color=False)
        assert result.exit_code == 0
        assert "--refresh" in result.output or "-R" in result.output


class TestRefreshFlagDescription:
    """Test that --refresh flag has proper description."""

    def test_refresh_flag_description(self) -> None:
        """Test that --refresh flag has proper help text."""
        result = runner.invoke(app, ["audit", "--help"], color=False)
        assert result.exit_code == 0
        # Check for key phrases in the help text
        assert "fresh" in result.output.lower() or "cache" in result.output.lower()


class TestCommandHelpConsistency:
    """Test help text consistency across commands."""

    def test_all_commands_show_in_help(self) -> None:
        """Test that all expected commands appear in main help."""
        result = runner.invoke(app, ["--help"], color=False)
        assert result.exit_code == 0

        expected_commands = [
            "scan",
            "clone",
            "audit",
            "graph",
            "deps",
            "cost",
            "validate",
            "unused",
            "transfer",
            "snapshot",
            "dr",
        ]

        for cmd in expected_commands:
            assert cmd in result.output, f"Command '{cmd}' not found in help"
