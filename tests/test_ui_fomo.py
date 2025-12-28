"""
Tests for the FOMO Design UI output functions.
"""

from dataclasses import dataclass, field
from io import StringIO
from unittest.mock import patch

import pytest
from rich.console import Console

from replimap.licensing.models import Plan


@dataclass
class MockFinding:
    """Mock CheckovFinding for testing."""

    check_id: str
    check_name: str
    severity: str
    resource: str = "aws_s3_bucket.test"
    file_path: str = "/path/to/s3.tf"
    file_line_range: tuple[int, int] = (1, 10)
    guideline: str | None = None


@dataclass
class MockResults:
    """Mock CheckovResults for testing."""

    score: float = 75.0
    grade: str = "C"
    passed: int = 100
    failed: int = 10
    skipped: int = 5
    findings: list = field(default_factory=list)
    findings_by_severity: dict = field(default_factory=dict)
    high_severity: list = field(default_factory=list)


class TestFOMODesign:
    """Test the FOMO design output functions."""

    def test_import_ui_module(self) -> None:
        """Test that UI module can be imported."""
        from replimap.ui import (
            print_audit_findings_fomo,
            print_audit_summary_fomo,
            print_finding_title,
            print_remediation_preview,
            print_upgrade_cta,
        )

        assert callable(print_audit_findings_fomo)
        assert callable(print_audit_summary_fomo)
        assert callable(print_finding_title)
        assert callable(print_remediation_preview)
        assert callable(print_upgrade_cta)

    def test_print_finding_title_critical(self) -> None:
        """Test that CRITICAL finding title is printed correctly."""
        from replimap.ui.rich_output import print_finding_title

        finding = MockFinding(
            check_id="CKV_AWS_19",
            check_name="Ensure S3 bucket has encryption enabled",
            severity="CRITICAL",
        )

        # Use string buffer to capture output
        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True, no_color=True)

        with patch("replimap.ui.rich_output.console", console):
            print_finding_title(finding, index=1, show_lock=True)

        output = string_io.getvalue()
        assert "CKV_AWS_19" in output
        assert "Ensure S3 bucket has encryption enabled" in output

    def test_audit_summary_shows_severity_breakdown(self) -> None:
        """Test that audit summary shows severity breakdown."""
        from replimap.ui.rich_output import print_audit_summary_fomo

        results = MockResults(
            score=65.0,
            grade="D",
            passed=50,
            failed=20,
            skipped=5,
            findings_by_severity={
                "CRITICAL": [MockFinding("CKV_1", "Test", "CRITICAL")],
                "HIGH": [MockFinding("CKV_2", "Test", "HIGH")] * 3,
                "MEDIUM": [MockFinding("CKV_3", "Test", "MEDIUM")] * 5,
                "LOW": [MockFinding("CKV_4", "Test", "LOW")] * 2,
            },
        )

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True, no_color=True)

        with patch("replimap.ui.rich_output.console", console):
            print_audit_summary_fomo(results)

        output = string_io.getvalue()
        # Rich formats floats with decimal point
        assert "65" in output or "65.0%" in output
        assert "CRITICAL" in output
        assert "HIGH" in output
        assert "MEDIUM" in output
        assert "LOW" in output

    @patch("replimap.ui.rich_output.get_plan_features")
    def test_free_user_sees_all_titles(self, mock_features, capsys) -> None:
        """Test that FREE users see all issue titles."""
        from replimap.ui.rich_output import print_audit_findings_fomo

        # Mock FREE plan features
        mock_features.return_value = type(
            "Features",
            (),
            {
                "audit_details_visible": False,
                "audit_first_critical_preview_lines": 2,
            },
        )()

        results = MockResults(
            score=50.0,
            grade="F",
            failed=5,
            findings=[
                MockFinding("CKV_1", "Issue 1", "CRITICAL"),
                MockFinding("CKV_2", "Issue 2", "HIGH"),
                MockFinding("CKV_3", "Issue 3", "MEDIUM"),
            ],
            findings_by_severity={
                "CRITICAL": [MockFinding("CKV_1", "Issue 1", "CRITICAL")],
                "HIGH": [MockFinding("CKV_2", "Issue 2", "HIGH")],
                "MEDIUM": [MockFinding("CKV_3", "Issue 3", "MEDIUM")],
            },
        )

        # Use the global console which prints to stdout
        print_audit_findings_fomo(results)

        captured = capsys.readouterr()
        output = captured.out
        # All titles should be visible
        assert "CKV_1" in output
        assert "CKV_2" in output
        assert "CKV_3" in output
        # Upgrade CTA should be shown
        assert "Solo" in output or "upgrade" in output.lower()

    @patch("replimap.ui.rich_output.get_plan_features")
    def test_solo_user_sees_full_remediation(self, mock_features, capsys) -> None:
        """Test that SOLO users see full remediation details."""
        from replimap.ui.rich_output import print_audit_findings_fomo

        # Mock SOLO plan features
        mock_features.return_value = type(
            "Features",
            (),
            {
                "audit_details_visible": True,
                "audit_first_critical_preview_lines": None,
            },
        )()

        results = MockResults(
            score=75.0,
            grade="C",
            failed=2,
            findings=[
                MockFinding("CKV_AWS_19", "Ensure S3 encryption", "CRITICAL"),
                MockFinding("CKV_AWS_20", "Ensure SSL access", "HIGH"),
            ],
            findings_by_severity={
                "CRITICAL": [MockFinding("CKV_AWS_19", "Ensure S3 encryption", "CRITICAL")],
                "HIGH": [MockFinding("CKV_AWS_20", "Ensure SSL access", "HIGH")],
            },
        )

        # Use the global console which prints to stdout
        print_audit_findings_fomo(results)

        captured = capsys.readouterr()
        output = captured.out
        # Should show finding IDs
        assert "CKV_AWS_19" in output
        assert "CKV_AWS_20" in output
        # Should not show upgrade CTA for paid users
        # (No "You can see the problems" for paid users)


class TestUpgradePrompts:
    """Test FOMO upgrade prompt formatting."""

    def test_fomo_unlock_prompt(self) -> None:
        """Test FOMO unlock prompt formatting."""
        from replimap.licensing.prompts import format_audit_fomo_unlock

        prompt = format_audit_fomo_unlock(total_count=15, hidden_count=14)

        assert "15" in prompt
        assert "14" in prompt
        assert "$49/mo" in prompt
        assert "Solo" in prompt

    def test_fomo_summary_prompt(self) -> None:
        """Test FOMO summary prompt formatting."""
        from replimap.licensing.prompts import format_audit_fomo_summary

        prompt = format_audit_fomo_summary(
            score=65,
            grade="D",
            critical_count=2,
            high_count=5,
            medium_count=8,
            low_count=3,
            total_count=18,
        )

        assert "65" in prompt
        assert "D" in prompt
        assert "CRITICAL" in prompt
        assert "18" in prompt


class TestNoFindingsCase:
    """Test output when no findings are present."""

    @patch("replimap.ui.rich_output.get_plan_features")
    def test_no_findings_message(self, mock_features) -> None:
        """Test that no findings shows success message."""
        from replimap.ui.rich_output import print_audit_findings_fomo

        mock_features.return_value = type(
            "Features",
            (),
            {
                "audit_details_visible": False,
                "audit_first_critical_preview_lines": 2,
            },
        )()

        results = MockResults(
            score=100.0,
            grade="A",
            passed=100,
            failed=0,
            findings=[],
            findings_by_severity={},
        )

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=True, no_color=True)

        print_audit_findings_fomo(results, console_out=console)

        output = string_io.getvalue()
        assert "No security issues found" in output
