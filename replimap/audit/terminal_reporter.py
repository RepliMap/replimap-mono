"""
Terminal Reporter for Audit Findings.

Provides concise summary output instead of printing 1000+ lines of findings.
Default: Summary table + Top 5 critical issues
Verbose: All findings + summary
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovResults


# Severity display configuration
SEVERITY_CONFIG = {
    "CRITICAL": {
        "color": "bold red",
        "icon": "\U0001f534",
        "status": "Immediate action required",
    },
    "HIGH": {"color": "red", "icon": "\U0001f7e0", "status": "Should fix soon"},
    "MEDIUM": {"color": "yellow", "icon": "\U0001f7e1", "status": "Review recommended"},
    "LOW": {"color": "blue", "icon": "\U0001f535", "status": "Informational"},
    "UNKNOWN": {"color": "dim", "icon": "\u26aa", "status": "Unclassified"},
}

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]


class AuditTerminalReporter:
    """
    Report audit findings with smart output modes.

    Default: Compact summary table + top 5 critical/high issues
    Verbose: All findings + summary table
    """

    def __init__(self, results: CheckovResults) -> None:
        """
        Initialize the reporter.

        Args:
            results: Checkov scan results (findings are already filtered to FAILED)
        """
        self.results = results
        # Findings in results are already FAILED checks
        self.findings = results.findings
        self.by_severity = self._count_by_severity()

    def _count_by_severity(self) -> Counter[str]:
        """Count findings by severity level."""
        counts: Counter[str] = Counter()
        for finding in self.findings:
            severity = (finding.severity or "UNKNOWN").upper()
            # Normalize unknown severities
            if severity not in SEVERITY_CONFIG:
                severity = "UNKNOWN"
            counts[severity] += 1
        return counts

    def print_results(self, console: Console, verbose: bool = False) -> None:
        """
        Print audit results.

        Args:
            console: Rich console for output
            verbose: If True, show all findings. If False, show summary + top 5.
        """
        if verbose:
            self._print_detailed(console)

        # Always print summary table
        self._print_summary(console)

        # Show top critical issues (in non-verbose mode, it's the main view)
        self._print_top_critical(console, show_hint=not verbose)

    def _print_summary(self, console: Console) -> None:
        """Print compact summary table."""
        table = Table(
            title="Audit Summary",
            show_header=True,
            header_style="bold",
            title_style="bold",
        )
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Count", justify="right", width=8)
        table.add_column("Status", width=30)

        total = 0
        for severity in SEVERITY_ORDER:
            count = self.by_severity.get(severity, 0)
            if count == 0:
                continue

            total += count
            config = SEVERITY_CONFIG[severity]

            table.add_row(
                f"[{config['color']}]{severity}[/]",
                str(count),
                f"{config['icon']} {config['status']}",
            )

        # Add score/grade info
        table.add_section()
        grade_color = (
            "green"
            if self.results.grade in ("A", "B")
            else "yellow"
            if self.results.grade == "C"
            else "red"
        )
        table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold]{total}[/bold]",
            f"Score: [{grade_color}]{self.results.score}% ({self.results.grade})[/]",
        )

        console.print()
        console.print(table)

    def _print_top_critical(self, console: Console, show_hint: bool = True) -> None:
        """
        Print top 5 critical/high issues as preview.

        Args:
            console: Rich console for output
            show_hint: Whether to show the --verbose hint
        """
        # Get critical and high findings
        critical_findings = [
            f
            for f in self.findings
            if (f.severity or "").upper() in ("CRITICAL", "HIGH")
        ]

        if not critical_findings:
            console.print()
            console.print(
                "[green]\u2713 No critical or high severity issues found![/green]"
            )
            if show_hint:
                console.print("[dim]Use --verbose to see all findings.[/dim]")
            return

        console.print()
        console.print("[bold red]\u26a0\ufe0f  Top Critical/High Issues:[/bold red]")

        for i, finding in enumerate(critical_findings[:5], 1):
            severity = (finding.severity or "UNKNOWN").upper()
            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["UNKNOWN"])
            check_id = finding.check_id or ""
            resource = finding.resource or "unknown"
            description = finding.check_name or ""

            # Truncate long resource names
            if len(resource) > 50:
                resource = resource[:47] + "..."

            console.print(
                f"  {config['icon']} {i}. [{config['color']}]{check_id}[/]: {resource}"
            )
            if description:
                console.print(f"      [dim]{description}[/dim]")

        remaining = len(critical_findings) - 5
        if remaining > 0:
            console.print(f"  [dim]... and {remaining} more in HTML report[/dim]")

        if show_hint:
            console.print()
            console.print("[dim]Use --verbose to see all findings in terminal.[/dim]")

    def _print_detailed(self, console: Console) -> None:
        """Print all findings (verbose mode only)."""
        console.print()
        console.print(f"[bold]All Findings ({len(self.findings)} total):[/bold]")

        # Group by severity for organized output
        for severity in SEVERITY_ORDER:
            findings = self.results.findings_by_severity.get(severity, [])
            if not findings:
                continue

            config = SEVERITY_CONFIG.get(severity, SEVERITY_CONFIG["UNKNOWN"])
            console.print()
            console.print(f"[bold]{config['icon']} {severity} ({len(findings)})[/bold]")

            for i, finding in enumerate(findings, 1):
                console.print()
                console.print(
                    f"  {i}. [{config['color']}]{finding.check_id}[/]: {finding.check_name}"
                )
                console.print(f"     [dim]Resource:[/] {finding.resource}")
                if finding.file_path:
                    line_info = (
                        f":{finding.file_line_range[0]}"
                        if finding.file_line_range[0] > 0
                        else ""
                    )
                    console.print(f"     [dim]File:[/] {finding.file_path}{line_info}")
                if finding.guideline:
                    console.print(f"     [dim]Guide:[/] {finding.guideline}")


def print_audit_summary(
    results: CheckovResults,
    console: Console,
    verbose: bool = False,
) -> None:
    """
    Print audit summary to terminal.

    This is the main entry point for terminal audit output.

    Args:
        results: Checkov scan results
        console: Rich console for output
        verbose: If True, show all findings. If False, show summary + top 5.
    """
    reporter = AuditTerminalReporter(results)
    reporter.print_results(console, verbose=verbose)
