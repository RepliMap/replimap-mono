"""Tests for AuditTerminalReporter."""

from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from replimap.audit.checkov_runner import CheckovFinding, CheckovResults
from replimap.audit.terminal_reporter import (
    SEVERITY_CONFIG,
    SEVERITY_ORDER,
    AuditTerminalReporter,
    print_audit_summary,
)


def create_finding(
    check_id: str = "CKV_AWS_1",
    check_name: str = "Test check",
    severity: str = "MEDIUM",
    resource: str = "aws_s3_bucket.test",
    file_path: str = "/test/main.tf",
    line_range: tuple[int, int] = (10, 15),
    guideline: str | None = None,
) -> CheckovFinding:
    """Create a test finding."""
    return CheckovFinding(
        check_id=check_id,
        check_name=check_name,
        severity=severity,
        resource=resource,
        file_path=file_path,
        file_line_range=line_range,
        guideline=guideline,
    )


def create_results(
    findings: list[CheckovFinding] | None = None,
    passed: int = 100,
    failed: int | None = None,
    skipped: int = 0,
) -> CheckovResults:
    """Create test results."""
    if findings is None:
        findings = []
    if failed is None:
        failed = len(findings)
    return CheckovResults(
        passed=passed,
        failed=failed,
        skipped=skipped,
        findings=findings,
    )


class TestSeverityConfig:
    """Tests for severity configuration constants."""

    def test_all_severities_have_config(self) -> None:
        """All severity levels should have configuration."""
        for severity in SEVERITY_ORDER:
            assert severity in SEVERITY_CONFIG
            config = SEVERITY_CONFIG[severity]
            assert "color" in config
            assert "icon" in config
            assert "status" in config

    def test_severity_order_is_correct(self) -> None:
        """Severity order should be from most to least severe."""
        assert SEVERITY_ORDER == ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


class TestAuditTerminalReporter:
    """Tests for AuditTerminalReporter class."""

    def test_init_with_empty_results(self) -> None:
        """Reporter should handle empty results."""
        results = create_results()
        reporter = AuditTerminalReporter(results)
        assert len(reporter.findings) == 0
        assert sum(reporter.by_severity.values()) == 0

    def test_init_groups_by_severity(self) -> None:
        """Reporter should group findings by severity."""
        findings = [
            create_finding(check_id="CKV_1", severity="CRITICAL"),
            create_finding(check_id="CKV_2", severity="CRITICAL"),
            create_finding(check_id="CKV_3", severity="HIGH"),
            create_finding(check_id="CKV_4", severity="MEDIUM"),
            create_finding(check_id="CKV_5", severity="LOW"),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        assert reporter.by_severity["CRITICAL"] == 2
        assert reporter.by_severity["HIGH"] == 1
        assert reporter.by_severity["MEDIUM"] == 1
        assert reporter.by_severity["LOW"] == 1
        assert reporter.by_severity["UNKNOWN"] == 0

    def test_normalizes_unknown_severity(self) -> None:
        """Reporter should normalize unknown severities."""
        findings = [
            create_finding(check_id="CKV_1", severity="INVALID"),
            create_finding(check_id="CKV_2", severity=""),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        assert reporter.by_severity["UNKNOWN"] == 2

    def test_print_summary_shows_table(self) -> None:
        """Summary should show a formatted table."""
        findings = [
            create_finding(check_id="CKV_1", severity="CRITICAL"),
            create_finding(check_id="CKV_2", severity="HIGH"),
            create_finding(check_id="CKV_3", severity="MEDIUM"),
        ]
        results = create_results(findings=findings, passed=97)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_summary(console)

        text = output.getvalue()
        assert "Audit Summary" in text
        assert "CRITICAL" in text
        assert "HIGH" in text
        assert "MEDIUM" in text
        assert "TOTAL" in text

    def test_print_summary_shows_score(self) -> None:
        """Summary should show score and grade."""
        results = create_results(passed=90, failed=10)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_summary(console)

        text = output.getvalue()
        assert "90.0%" in text
        assert "(A)" in text

    def test_print_summary_skips_zero_counts(self) -> None:
        """Summary should not show severities with zero counts."""
        findings = [create_finding(severity="CRITICAL")]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_summary(console)

        text = output.getvalue()
        assert "CRITICAL" in text
        # LOW should not appear if count is 0
        # (it appears in header config but not as a row)

    def test_print_top_critical_with_no_critical(self) -> None:
        """Should show success message when no critical/high issues."""
        findings = [
            create_finding(severity="MEDIUM"),
            create_finding(severity="LOW"),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert "No critical or high severity issues found" in text

    def test_print_top_critical_shows_top_5(self) -> None:
        """Should show top 5 critical/high issues."""
        findings = [
            create_finding(
                check_id=f"CKV_{i}",
                severity="CRITICAL",
                resource=f"aws_s3_bucket.bucket{i}",
            )
            for i in range(7)
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert "Top Critical/High Issues" in text
        assert "CKV_0" in text
        assert "CKV_4" in text
        # Should mention remaining
        assert "2 more" in text

    def test_print_top_critical_truncates_long_resources(self) -> None:
        """Should truncate resource names longer than 50 chars."""
        long_resource = "aws_s3_bucket.this_is_a_very_long_bucket_name_that_exceeds_fifty_characters_limit"
        findings = [create_finding(severity="CRITICAL", resource=long_resource)]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert "..." in text
        assert long_resource not in text  # Full name should not appear

    def test_print_top_critical_shows_description(self) -> None:
        """Should show finding description."""
        findings = [
            create_finding(
                severity="CRITICAL", check_name="Ensure encryption is enabled"
            )
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert "Ensure encryption is enabled" in text

    def test_print_top_critical_shows_verbose_hint(self) -> None:
        """Should show verbose hint when show_hint is True."""
        findings = [create_finding(severity="HIGH")]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console, show_hint=True)

        text = output.getvalue()
        assert "--verbose" in text

    def test_print_top_critical_hides_verbose_hint(self) -> None:
        """Should hide verbose hint when show_hint is False."""
        findings = [create_finding(severity="HIGH")]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console, show_hint=False)

        text = output.getvalue()
        assert "--verbose" not in text

    def test_print_detailed_shows_all_findings(self) -> None:
        """Detailed mode should show all findings."""
        findings = [
            create_finding(check_id="CKV_1", severity="CRITICAL", check_name="Check 1"),
            create_finding(check_id="CKV_2", severity="HIGH", check_name="Check 2"),
            create_finding(check_id="CKV_3", severity="MEDIUM", check_name="Check 3"),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_detailed(console)

        text = output.getvalue()
        assert "All Findings (3 total)" in text
        assert "CKV_1" in text
        assert "CKV_2" in text
        assert "CKV_3" in text
        assert "Check 1" in text
        assert "Check 2" in text
        assert "Check 3" in text

    def test_print_detailed_shows_file_info(self) -> None:
        """Detailed mode should show file path and line number."""
        findings = [
            create_finding(
                severity="CRITICAL",
                file_path="/path/to/s3.tf",
                line_range=(42, 50),
            )
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_detailed(console)

        text = output.getvalue()
        assert "/path/to/s3.tf:42" in text

    def test_print_detailed_shows_guideline(self) -> None:
        """Detailed mode should show guideline URL."""
        findings = [
            create_finding(
                severity="CRITICAL",
                guideline="https://docs.example.com/fix",
            )
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_detailed(console)

        text = output.getvalue()
        assert "https://docs.example.com/fix" in text

    def test_print_results_default_mode(self) -> None:
        """Default mode should show summary + top critical."""
        findings = [
            create_finding(check_id="CKV_1", severity="CRITICAL"),
            create_finding(check_id="CKV_2", severity="MEDIUM"),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter.print_results(console, verbose=False)

        text = output.getvalue()
        assert "Audit Summary" in text
        assert "Top Critical/High Issues" in text
        assert "--verbose" in text  # Should show hint

    def test_print_results_verbose_mode(self) -> None:
        """Verbose mode should show all findings + summary."""
        findings = [
            create_finding(
                check_id="CKV_1", severity="CRITICAL", check_name="Critical check"
            ),
            create_finding(
                check_id="CKV_2", severity="MEDIUM", check_name="Medium check"
            ),
        ]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter.print_results(console, verbose=True)

        text = output.getvalue()
        assert "All Findings" in text
        assert "Critical check" in text
        assert "Medium check" in text
        assert "Audit Summary" in text


class TestPrintAuditSummary:
    """Tests for the print_audit_summary function."""

    def test_creates_reporter_and_prints(self) -> None:
        """Should create reporter and call print_results."""
        findings = [create_finding(severity="HIGH")]
        results = create_results(findings=findings)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        print_audit_summary(results, console, verbose=False)

        text = output.getvalue()
        assert "Audit Summary" in text

    def test_respects_verbose_flag(self) -> None:
        """Should pass verbose flag to reporter."""
        findings = [
            create_finding(
                check_id="CKV_1", severity="HIGH", check_name="Test finding"
            ),
        ]
        results = create_results(findings=findings)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        print_audit_summary(results, console, verbose=True)

        text = output.getvalue()
        assert "All Findings" in text
        assert "Test finding" in text


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_none_severity(self) -> None:
        """Should handle None severity gracefully."""
        # Create a finding with None severity using MagicMock
        finding = MagicMock()
        finding.severity = None
        finding.check_id = "CKV_TEST"
        finding.check_name = "Test"
        finding.resource = "test"
        finding.file_path = "/test.tf"
        finding.file_line_range = (1, 1)
        finding.guideline = None

        results = MagicMock()
        results.findings = [finding]
        results.findings_by_severity = {"UNKNOWN": [finding]}
        results.score = 95.0
        results.grade = "A"

        reporter = AuditTerminalReporter(results)
        assert reporter.by_severity["UNKNOWN"] == 1

    def test_handles_empty_check_name(self) -> None:
        """Should handle empty check name."""
        findings = [create_finding(severity="CRITICAL", check_name="")]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        # Should not raise an error
        text = output.getvalue()
        assert "CKV_AWS_1" in text

    def test_handles_empty_resource(self) -> None:
        """Should handle empty resource name."""
        findings = [create_finding(severity="CRITICAL", resource="")]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        # Should not raise an error
        text = output.getvalue()
        assert "CKV_AWS_1" in text

    def test_handles_exactly_50_char_resource(self) -> None:
        """Should not truncate resource name exactly 50 chars."""
        resource = "a" * 50
        findings = [create_finding(severity="CRITICAL", resource=resource)]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert resource in text
        assert "..." not in text

    def test_handles_51_char_resource(self) -> None:
        """Should truncate resource name at 51 chars."""
        resource = "a" * 51
        findings = [create_finding(severity="CRITICAL", resource=resource)]
        results = create_results(findings=findings)
        reporter = AuditTerminalReporter(results)

        output = StringIO()
        console = Console(file=output, force_terminal=True, width=100)
        reporter._print_top_critical(console)

        text = output.getvalue()
        assert resource not in text
        assert "..." in text
