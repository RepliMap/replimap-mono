"""
Tests for disclaimer presence in Dependency Explorer output.

These tests ensure that disclaimers are ALWAYS present in all outputs.
This is critical for legal compliance - the analysis is based on AWS API
metadata only and cannot detect application-level dependencies.
"""

import json
import tempfile
from pathlib import Path

from replimap.dependencies import (
    DISCLAIMER_FULL,
    DISCLAIMER_SHORT,
    STANDARD_LIMITATIONS,
    DependencyExplorerReporter,
    DependencyExplorerResult,
    DependencyZone,
    ImpactLevel,
    ResourceNode,
)


def create_mock_result() -> DependencyExplorerResult:
    """Create a mock result for testing."""
    center = ResourceNode(
        id="sg-123",
        type="aws_security_group",
        name="web-sg",
        impact_level=ImpactLevel.HIGH,
        impact_score=75,
    )

    affected1 = ResourceNode(
        id="i-456",
        type="aws_instance",
        name="web-1",
        impact_level=ImpactLevel.HIGH,
        impact_score=80,
        depth=1,
    )

    zone1 = DependencyZone(
        depth=1,
        resources=[affected1],
        total_impact_score=80,
    )

    return DependencyExplorerResult(
        center_resource=center,
        zones=[zone1],
        affected_resources=[affected1],
        total_affected=1,
        max_depth=1,
        estimated_impact=ImpactLevel.HIGH,
        estimated_score=80,
        suggested_review_order=["i-456", "sg-123"],
        warnings=["Production resources detected"],
    )


class TestDisclaimerConstants:
    """Test disclaimer constants are properly defined."""

    def test_disclaimer_short_exists(self):
        """Short disclaimer constant must exist."""
        assert DISCLAIMER_SHORT
        assert "AWS API metadata only" in DISCLAIMER_SHORT

    def test_disclaimer_full_exists(self):
        """Full disclaimer constant must exist."""
        assert DISCLAIMER_FULL
        assert "AWS API metadata" in DISCLAIMER_FULL
        assert "Hardcoded IP" in DISCLAIMER_FULL
        assert "DNS" in DISCLAIMER_FULL
        assert "Configuration file" in DISCLAIMER_FULL

    def test_standard_limitations_complete(self):
        """Standard limitations list must be complete."""
        assert len(STANDARD_LIMITATIONS) >= 5
        limitations_str = " ".join(STANDARD_LIMITATIONS)
        assert "Application-level" in limitations_str
        assert "Hardcoded" in limitations_str
        assert "DNS" in limitations_str
        assert "Cross-account" in limitations_str
        assert "Configuration" in limitations_str


class TestResultDisclaimers:
    """Test DependencyExplorerResult includes disclaimers."""

    def test_result_has_limitations(self):
        """Result object must include limitations."""
        result = create_mock_result()

        assert len(result.limitations) > 0
        assert any("Application-level" in lim for lim in result.limitations)

    def test_result_has_disclaimer(self):
        """Result object must include disclaimer text."""
        result = create_mock_result()

        assert result.disclaimer
        assert "AWS API metadata" in result.disclaimer

    def test_result_has_default_warning(self):
        """Result object must auto-add API metadata warning."""
        result = DependencyExplorerResult(
            center_resource=ResourceNode(id="test", type="aws_instance", name="test"),
        )

        assert len(result.warnings) > 0
        assert any("AWS API metadata" in w for w in result.warnings)

    def test_result_to_dict_includes_disclaimer(self):
        """Result dictionary must include disclaimer."""
        result = create_mock_result()
        data = result.to_dict()

        assert "disclaimer" in data
        assert "limitations" in data
        assert len(data["limitations"]) > 0


class TestConsoleOutput:
    """Test console output includes disclaimer."""

    def test_console_output_has_disclaimer(self, capsys):
        """Console output must include disclaimer."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        reporter.to_console(result)

        captured = capsys.readouterr()
        assert "AWS API metadata only" in captured.out
        assert "Application-level dependencies" in captured.out

    def test_console_output_has_important_disclaimer_panel(self, capsys):
        """Console output must show Important Disclaimer panel in verbose mode."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        # Verbose mode shows full disclaimer panel
        reporter.to_console(result, verbose=True)

        captured = capsys.readouterr()
        # Should have the full disclaimer panel
        assert "Important Disclaimer" in captured.out or "CANNOT" in captured.out

    def test_console_output_compact_has_disclaimer(self, capsys):
        """Console output (compact mode) must show disclaimer hint."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        # Default compact mode shows short disclaimer with hint
        reporter.to_console(result, verbose=False)

        captured = capsys.readouterr()
        # Should have compact disclaimer with hint to use --verbose
        assert "AWS API metadata only" in captured.out
        assert "--verbose" in captured.out


class TestJsonOutput:
    """Test JSON output includes disclaimer."""

    def test_json_output_has_disclaimer(self):
        """JSON output must include disclaimer."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deps.json"
            reporter.to_json(result, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert "disclaimer" in data
            assert "limitations" in data
            assert len(data["limitations"]) > 0
            assert "AWS API" in data["disclaimer"] or "AWS API" in str(data)


class TestHtmlOutput:
    """Test HTML output includes disclaimer."""

    def test_html_output_has_disclaimer(self):
        """HTML output must include disclaimer."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, output_path)

            assert output_path.exists()

            content = output_path.read_text()

            assert "Important Disclaimer" in content
            assert "AWS API metadata only" in content
            assert "Hardcoded IP" in content

    def test_html_has_top_disclaimer(self):
        """HTML must have disclaimer at top of page."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, output_path)

            content = output_path.read_text()

            # Disclaimer should appear early in the HTML
            disclaimer_pos = content.find("Important Disclaimer")
            graph_pos = content.find('id="graph"')
            assert disclaimer_pos < graph_pos, "Disclaimer should appear before graph"

    def test_html_has_footer_disclaimer(self):
        """HTML must have disclaimer at bottom too."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, output_path)

            content = output_path.read_text()

            assert "footer-disclaimer" in content
            assert "RepliMap provides suggestions only" in content


class TestNoSafeLanguage:
    """Test that 'safe' language is not used."""

    def test_no_safe_deletion_order(self):
        """Output must not use 'Safe Deletion Order'."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, html_path)

            html_content = html_path.read_text()
            assert "Safe Deletion" not in html_content
            assert "safe deletion" not in html_content.lower()

    def test_uses_suggested_review_order(self):
        """Output must use 'Suggested Review Order' instead."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, html_path)

            html_content = html_path.read_text()
            assert "Suggested Review Order" in html_content

    def test_uses_estimated_impact(self):
        """Output must use 'Estimated' instead of absolute impact."""
        reporter = DependencyExplorerReporter()
        result = create_mock_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "deps.html"
            reporter.to_html(result, html_path)

            html_content = html_path.read_text()
            # Should say "Estimated" or "Est."
            assert "Est" in html_content


class TestModelBackwardCompatibility:
    """Test backward compatibility aliases work."""

    def test_blast_node_alias(self):
        """BlastNode alias should work."""
        from replimap.dependencies import BlastNode

        node = BlastNode(id="test", type="aws_instance", name="test")
        assert node.id == "test"

    def test_blast_radius_result_alias(self):
        """BlastRadiusResult alias should work."""
        from replimap.dependencies import BlastRadiusResult

        result = BlastRadiusResult(
            center_resource=ResourceNode(id="test", type="aws_instance", name="test"),
        )
        assert result.center_resource.id == "test"

    def test_blast_radius_reporter_alias(self):
        """BlastRadiusReporter alias should work."""
        from replimap.dependencies import BlastRadiusReporter

        reporter = BlastRadiusReporter()
        assert reporter is not None
