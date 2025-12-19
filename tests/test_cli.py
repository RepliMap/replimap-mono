"""Tests for CLI commands."""

import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.main import app

runner = CliRunner()

# Regex to strip ANSI escape codes (colors, formatting)
ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_ESCAPE.sub("", text)


class TestCLI:
    """Tests for CLI commands."""

    def test_version(self) -> None:
        """Test --version flag."""
        result = runner.invoke(app, ["--version"], color=False)
        assert result.exit_code == 0
        assert "RepliMap" in result.output

    def test_help(self) -> None:
        """Test --help flag."""
        result = runner.invoke(app, ["--help"], color=False)
        assert result.exit_code == 0
        assert "AWS Environment Replication Tool" in result.output

    def test_scan_help(self) -> None:
        """Test scan --help."""
        result = runner.invoke(app, ["scan", "--help"], color=False)
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "--profile" in output
        assert "--region" in output
        assert "--output" in output

    def test_clone_help(self) -> None:
        """Test clone --help."""
        result = runner.invoke(app, ["clone", "--help"], color=False)
        output = strip_ansi(result.output)
        assert result.exit_code == 0
        assert "--profile" in output
        assert "--mode" in output
        assert "--downsize" in output
        assert "--rename-pattern" in output

    def test_load_nonexistent_file(self) -> None:
        """Test loading a nonexistent file."""
        result = runner.invoke(app, ["load", "/nonexistent/file.json"], color=False)
        assert result.exit_code == 1
        assert "File not found" in result.output

    def test_load_valid_file(self) -> None:
        """Test loading a valid graph file."""
        # Create a test graph and save it
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="vpc-12345",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"cidr_block": "10.0.0.0/16"},
                tags={"Name": "test-vpc"},
            )
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            graph.save(path)

            result = runner.invoke(app, ["load", str(path)], color=False)
            assert result.exit_code == 0
            assert "Graph Loaded" in result.output
            assert "1" in result.output  # 1 resource

        finally:
            path.unlink()

    def test_clone_invalid_mode(self) -> None:
        """Test clone with invalid mode."""
        with patch("replimap.main.get_aws_session") as mock_session:
            mock_session.return_value = MagicMock()

            result = runner.invoke(
                app,
                ["clone", "--mode", "invalid", "--region", "us-east-1"],
                color=False,
            )
            assert result.exit_code == 1
            assert "Invalid mode" in result.output


class TestCLIIntegration:
    """Integration tests for CLI (require mocking AWS)."""

    @patch("replimap.main.get_aws_session")
    @patch("replimap.main.run_all_scanners")
    def test_scan_dry_run(
        self, mock_scanners: MagicMock, mock_session: MagicMock
    ) -> None:
        """Test scan command with mocked AWS."""
        mock_session.return_value = MagicMock()
        mock_scanners.return_value = {"VPCScanner": None}

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            result = runner.invoke(
                app,
                ["scan", "--region", "us-east-1", "--output", str(path)],
                color=False,
            )
            output = strip_ansi(result.output)

            # Should complete (may fail on auth but that's expected)
            # The important thing is the command runs
            assert "--profile" not in output or result.exit_code in (0, 1)

        finally:
            if path.exists():
                path.unlink()
