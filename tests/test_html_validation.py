"""
HTML Output Validation Tests.

These tests ensure that HTML outputs (drift reports, graph visualizations)
are structurally correct and contain all required elements.

Test Layers:
1. Structural Validation - HTML parses without errors
2. Required Elements - Critical DOM elements exist
3. JavaScript Integrity - JS variables and functions defined
4. CSS Class Consistency - Classes used in JS exist in HTML
"""

import tempfile
from pathlib import Path

import pytest

from replimap.drift.models import (
    AttributeDiff,
    DriftReason,
    DriftReport,
    DriftSeverity,
    DriftType,
    ResourceDrift,
)
from replimap.drift.reporter import DriftReporter


class TestDriftReportHTMLStructure:
    """Tests for drift report HTML structural integrity."""

    @pytest.fixture
    def sample_drift_report(self) -> DriftReport:
        """Create a sample drift report for testing."""
        drifts = [
            ResourceDrift(
                resource_type="aws_security_group",
                resource_id="sg-12345",
                resource_name="web-sg",
                drift_type=DriftType.MODIFIED,
                severity=DriftSeverity.HIGH,
                tf_address="aws_security_group.web",
                diffs=[
                    AttributeDiff(
                        attribute="ingress",
                        expected=[{"port": 80}],
                        actual=[{"port": 443}],
                        severity=DriftSeverity.HIGH,
                        reason=DriftReason.SEMANTIC,
                    ),
                ],
            ),
            ResourceDrift(
                resource_type="aws_instance",
                resource_id="i-abc123",
                resource_name="web-server",
                drift_type=DriftType.ADDED,
                severity=DriftSeverity.MEDIUM,
                tf_address="",
                diffs=[],
            ),
            ResourceDrift(
                resource_type="aws_s3_bucket",
                resource_id="my-bucket",
                resource_name="data-bucket",
                drift_type=DriftType.REMOVED,
                severity=DriftSeverity.CRITICAL,
                tf_address="aws_s3_bucket.data",
                diffs=[],
            ),
        ]

        return DriftReport(
            region="us-east-1",
            state_file="terraform.tfstate",
            scan_duration_seconds=12.5,
            drifts=drifts,
            total_resources=10,
            drifted_resources=3,
            modified_resources=1,
            added_resources=1,
            removed_resources=1,
        )

    @pytest.fixture
    def empty_drift_report(self) -> DriftReport:
        """Create an empty drift report."""
        return DriftReport(
            region="us-east-1",
            state_file="terraform.tfstate",
            scan_duration_seconds=5.0,
            drifts=[],
        )

    def test_html_parses_without_errors(self, sample_drift_report: DriftReport) -> None:
        """Verify HTML is valid and parses without errors."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()

            # Parse with html5lib for strict validation
            try:
                import html5lib

                html5lib.parse(html_content)
            except ImportError:
                # Fall back to lxml
                pass

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")

            # Basic structure checks
            assert soup.html is not None, "Missing <html> tag"
            assert soup.head is not None, "Missing <head> tag"
            assert soup.body is not None, "Missing <body> tag"
            assert soup.title is not None, "Missing <title> tag"

    def test_required_elements_exist(self, sample_drift_report: DriftReport) -> None:
        """Verify all required DOM elements are present."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Header section
            assert soup.find("header") is not None, "Missing header element"

            # Main content
            main = soup.find("main")
            assert main is not None, "Missing main element"

            # Filter controls (when drift exists)
            assert soup.find(id="search-input") is not None, "Missing search input"
            assert soup.find(id="status-filter") is not None, "Missing status filter"
            assert soup.find(id="classification-filter") is not None, (
                "Missing classification filter"
            )

            # Drift cards
            drift_cards = soup.find_all(class_="drift-card")
            assert len(drift_cards) > 0, "No drift cards found"

            # Footer
            assert soup.find("footer") is not None, "Missing footer element"

    def test_javascript_functions_defined(
        self, sample_drift_report: DriftReport
    ) -> None:
        """Verify JavaScript functions are properly defined."""
        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()

            # Check for required JavaScript functions
            required_functions = [
                "toggleAccordion",
                "toggleDiff",
                "expandAll",
                "collapseAll",
                "copyCommand",
                "filterDrifts",
            ]

            for func in required_functions:
                assert f"function {func}" in html_content, f"Missing function: {func}"

    def test_css_classes_referenced_in_js_exist(
        self, sample_drift_report: DriftReport
    ) -> None:
        """Verify CSS classes used in JavaScript are defined."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # CSS classes that should exist (referenced in JS via classList, querySelector)
            expected_classes = [
                "accordion-content",
                "accordion-icon",
                "diff-content",
                "diff-icon",
                "drift-card",
                "accordion-group",
                "open",
                "hidden",
                "copied",
            ]

            # Check each expected class is either in HTML or defined in CSS
            style_content = "".join(tag.string or "" for tag in soup.find_all("style"))

            for cls in expected_classes:
                in_html = soup.find(class_=cls) is not None
                in_css = f".{cls}" in style_content or cls in style_content
                assert in_html or in_css, f"CSS class '{cls}' not found in HTML or CSS"

    def test_data_attributes_present(self, sample_drift_report: DriftReport) -> None:
        """Verify data attributes needed for JS filtering are present."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Check drift cards have required data attributes
            drift_cards = soup.find_all(class_="drift-card")
            for card in drift_cards:
                assert card.get("data-id") is not None, "Missing data-id"
                assert card.get("data-status") is not None, "Missing data-status"
                assert card.get("data-classification") is not None, (
                    "Missing data-classification"
                )
                assert card.get("data-type") is not None, "Missing data-type"

    def test_remediation_commands_present(
        self, sample_drift_report: DriftReport
    ) -> None:
        """Verify remediation commands are generated for drifted resources."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Find remediation commands
            assert (
                "terraform apply" in html_content or "terraform import" in html_content
            )

            # Check copy buttons have data-cmd attribute
            copy_buttons = soup.find_all(class_="copy-btn")
            for btn in copy_buttons:
                cmd = btn.get("data-cmd")
                assert cmd is not None, "Copy button missing data-cmd"
                assert cmd.startswith("terraform"), f"Invalid command: {cmd}"

    def test_empty_report_renders(self, empty_drift_report: DriftReport) -> None:
        """Verify empty report renders without errors."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(empty_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Should have "No Drift" message
            assert "No Drift" in html_content or "no drift" in html_content.lower()

            # Verify soup parsed correctly (filters may or may not be present)
            assert soup is not None

    def test_special_characters_escaped(self, sample_drift_report: DriftReport) -> None:
        """Verify special characters in resource IDs are properly escaped."""
        # Create drift with special characters
        drift_with_special = ResourceDrift(
            resource_type="aws_cloudwatch_log_group",
            resource_id="/aws/lambda/my-function<script>alert(1)</script>",
            resource_name="test",
            drift_type=DriftType.ADDED,
            severity=DriftSeverity.LOW,
            tf_address="",
            diffs=[],
        )

        report = DriftReport(
            region="us-east-1",
            state_file="test.tfstate",
            scan_duration_seconds=1.0,
            drifts=[drift_with_special],
            drifted_resources=1,  # Must set this for has_drift to work
            added_resources=1,
            total_resources=1,
        )

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(report, output_path)

            html_content = output_path.read_text()

            # Script tags should be escaped (XSS prevention)
            assert "<script>alert(1)</script>" not in html_content
            # The resource should be in the output (escaped form is ok)
            assert "aws_cloudwatch_log_group" in html_content

    def test_long_content_truncated(self) -> None:
        """Verify very long content is handled gracefully."""

        # Create drift with very long attribute value
        long_value = "x" * 10000
        drift = ResourceDrift(
            resource_type="aws_instance",
            resource_id="i-12345",
            resource_name="test",
            drift_type=DriftType.MODIFIED,
            severity=DriftSeverity.LOW,
            tf_address="",
            diffs=[
                AttributeDiff(
                    attribute="user_data",
                    expected=long_value,
                    actual="short",
                    severity=DriftSeverity.LOW,
                    reason=DriftReason.SEMANTIC,
                ),
            ],
        )

        report = DriftReport(
            region="us-east-1",
            state_file="test.tfstate",
            scan_duration_seconds=1.0,
            drifts=[drift],
            drifted_resources=1,
            modified_resources=1,
            total_resources=1,
        )

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(report, output_path)

            html_content = output_path.read_text()

            # Should not contain the full 10000 character string
            # (truncation should have occurred)
            assert long_value not in html_content

            # Should contain truncation indicator
            assert "..." in html_content


class TestGraphVisualizationHTML:
    """Tests for graph visualization HTML output."""

    def test_d3_formatter_html_structure(self) -> None:
        """Verify D3 formatter produces valid HTML."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        from replimap.graph import GraphEdge, GraphNode, VisualizationGraph
        from replimap.graph.formatters import D3Formatter

        # Create sample graph
        nodes = [
            GraphNode(id="vpc-1", resource_type="aws_vpc", name="main-vpc"),
            GraphNode(id="subnet-1", resource_type="aws_subnet", name="public-subnet"),
        ]
        edges = [GraphEdge(source="subnet-1", target="vpc-1")]
        graph = VisualizationGraph(
            nodes=nodes, edges=edges, metadata={"region": "us-east-1"}
        )

        formatter = D3Formatter()
        html = formatter.format(graph)

        # Parse HTML
        soup = BeautifulSoup(html, "html.parser")

        # Basic structure
        assert soup.html is not None
        assert soup.body is not None

        # D3 script should be included or referenced
        scripts = soup.find_all("script")
        script_content = " ".join(tag.string or "" for tag in scripts)
        script_srcs = [tag.get("src", "") for tag in scripts]

        has_d3 = "d3" in script_content.lower() or any(
            "d3" in src for src in script_srcs
        )
        assert has_d3, "D3.js not found in HTML"

        # Should have SVG container or similar
        assert soup.find("svg") is not None or "svg" in html.lower()


class TestHTMLAccessibility:
    """Tests for HTML accessibility features."""

    def test_form_labels_exist(self, sample_drift_report: DriftReport) -> None:
        """Verify form inputs have associated labels."""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            pytest.skip("beautifulsoup4 not installed")

        reporter = DriftReporter()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "report.html"
            reporter.to_html(sample_drift_report, output_path)

            html_content = output_path.read_text()
            soup = BeautifulSoup(html_content, "html.parser")

            # Find all inputs and selects
            inputs = soup.find_all(["input", "select"])

            for input_elem in inputs:
                input_id = input_elem.get("id")
                if input_id:
                    # Should have a label (visible or sr-only)
                    label = soup.find("label", {"for": input_id})
                    assert label is not None, f"Missing label for input #{input_id}"

    @pytest.fixture
    def sample_drift_report(self) -> DriftReport:
        """Create a sample drift report for testing."""
        drifts = [
            ResourceDrift(
                resource_type="aws_security_group",
                resource_id="sg-12345",
                resource_name="web-sg",
                drift_type=DriftType.MODIFIED,
                severity=DriftSeverity.HIGH,
                tf_address="aws_security_group.web",
                diffs=[
                    AttributeDiff(
                        attribute="ingress",
                        expected=[{"port": 80}],
                        actual=[{"port": 443}],
                        severity=DriftSeverity.HIGH,
                        reason=DriftReason.SEMANTIC,
                    ),
                ],
            ),
        ]

        return DriftReport(
            region="us-east-1",
            state_file="terraform.tfstate",
            scan_duration_seconds=12.5,
            drifts=drifts,
            total_resources=5,
            drifted_resources=1,
            modified_resources=1,
        )
