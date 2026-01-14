"""
Rich Console Output Utilities for FOMO Design.

Implements the "Gate at OUTPUT, not at SCAN" philosophy:
- FREE users see ALL issue titles (they know what's wrong)
- First CRITICAL gets 2-line remediation preview (taste of value)
- Remaining remediation details are gated (pay to "take it home")

v3.2 Pricing:
- Solo: $49/mo - Full remediation details
- Pro: $99/mo - CI/CD mode, drift detection
- Team: $199/mo - Trust Center
- Enterprise: From $500/mo - Compliance mapping
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from replimap.licensing.manager import get_license_manager
from replimap.licensing.models import Plan, get_plan_features

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovFinding, CheckovResults


def _get_fix_suggestion(check_id: str) -> str | None:
    """Lazy import to avoid circular dependency with audit module."""
    from replimap.audit.fix_suggestions import get_fix_suggestion

    return get_fix_suggestion(check_id)


# Initialize console
console = Console()

# Severity colors and icons
SEVERITY_STYLES = {
    "CRITICAL": {
        "color": "bold magenta",
        "icon": "🔴",
        "badge": "[magenta]CRITICAL[/]",
    },
    "HIGH": {"color": "bold red", "icon": "🟠", "badge": "[red]HIGH[/]"},
    "MEDIUM": {"color": "bold yellow", "icon": "🟡", "badge": "[yellow]MEDIUM[/]"},
    "LOW": {"color": "bold blue", "icon": "🔵", "badge": "[blue]LOW[/]"},
    "UNKNOWN": {"color": "dim", "icon": "⚪", "badge": "[dim]UNKNOWN[/]"},
}


def print_finding_title(
    finding: CheckovFinding,
    index: int,
    show_lock: bool = False,
) -> None:
    """
    Print a single finding title (visible to all users).

    Args:
        finding: The Checkov finding to display
        index: The finding number (1-indexed)
        show_lock: Whether to show a lock icon (indicating gated content)
    """
    style = SEVERITY_STYLES.get(finding.severity, SEVERITY_STYLES["UNKNOWN"])
    lock = " [dim]🔒[/]" if show_lock else ""

    console.print(
        f"  [{style['color']}]{style['icon']}[/] "
        f"{index}. [{style['color']}]{finding.check_id}[/]: "
        f"{finding.check_name}{lock}"
    )


def print_remediation_preview(
    finding: CheckovFinding,
    max_lines: int = 2,
) -> None:
    """
    Print a 2-line remediation preview for the first CRITICAL finding.

    This gives FREE users a taste of the remediation value.

    Args:
        finding: The Checkov finding
        max_lines: Maximum lines to show (default 2)
    """
    fix = _get_fix_suggestion(finding.check_id)

    if fix:
        # Get first N lines of the fix
        lines = fix.strip().split("\n")[:max_lines]

        console.print()
        console.print("     [dim]┌─ Remediation Preview ──────────────────────[/]")
        for line in lines:
            console.print(f"     [dim]│[/] [cyan]{line}[/]")
        if len(fix.strip().split("\n")) > max_lines:
            remaining = len(fix.strip().split("\n")) - max_lines
            console.print(f"     [dim]│ ... {remaining} more lines[/]")
        console.print("     [dim]└────────────────────────────────────────────[/]")
    else:
        console.print()
        console.print("     [dim]┌─ Remediation ──────────────────────────────[/]")
        console.print(
            f"     [dim]│[/] See: [cyan]{finding.guideline or 'Checkov docs'}[/]"
        )
        console.print("     [dim]└────────────────────────────────────────────[/]")


def print_upgrade_cta(
    total_findings: int,
    hidden_count: int,
    plan: Plan = Plan.FREE,
) -> None:
    """
    Print the upgrade call-to-action panel.

    Args:
        total_findings: Total number of security findings
        hidden_count: Number of findings with hidden remediation
        plan: Current user plan
    """
    if plan != Plan.FREE:
        return

    cta_text = Text()
    cta_text.append("\n")
    cta_text.append("You can see the problems. Now get the cure.\n\n", style="bold")
    cta_text.append(f"All {total_findings} issue titles shown above.\n", style="dim")
    cta_text.append(f"{hidden_count} remediation details hidden.\n\n", style="dim")
    cta_text.append("Upgrade to Solo ($49/mo) to unlock:\n", style="bold cyan")
    cta_text.append(f"  ✓ Complete remediation steps for all {total_findings} issues\n")
    cta_text.append("  ✓ Affected resource lists\n")
    cta_text.append("  ✓ Terraform/AWS CLI fix commands\n")
    cta_text.append("  ✓ Exportable HTML reports\n\n")
    cta_text.append("→ replimap upgrade solo\n", style="bold green")
    cta_text.append("→ https://replimap.com/pricing", style="dim")

    console.print(
        Panel(
            cta_text,
            title="[bold yellow]💊 Unlock Full Remediation[/]",
            border_style="yellow",
            padding=(1, 2),
        )
    )


def print_audit_summary_fomo(
    results: CheckovResults,
    show_grade: bool = True,
) -> None:
    """
    Print the audit summary with FOMO design.

    Shows the security score and severity breakdown.

    Args:
        results: The Checkov scan results
        show_grade: Whether to show the letter grade
    """
    # Determine score color
    if results.score >= 80:
        score_color = "green"
    elif results.score >= 60:
        score_color = "yellow"
    else:
        score_color = "red"

    # Build summary text
    summary = Text()
    summary.append("\n")

    # Score line
    if show_grade:
        summary.append("Security Score: ", style="bold")
        summary.append(f"{results.score}%", style=f"bold {score_color}")
        summary.append("  Grade: ", style="bold")
        summary.append(f"{results.grade}", style=f"bold {score_color}")
    else:
        summary.append("Security Score: ", style="bold")
        summary.append(f"{results.score}%", style=f"bold {score_color}")

    summary.append("\n\n")

    # Severity breakdown
    critical = len(results.findings_by_severity.get("CRITICAL", []))
    high = len(results.findings_by_severity.get("HIGH", []))
    medium = len(results.findings_by_severity.get("MEDIUM", []))
    low = len(results.findings_by_severity.get("LOW", []))

    summary.append("Issues Found:\n", style="bold")
    summary.append(
        f"├── 🔴 CRITICAL:  {critical}\n", style="magenta" if critical > 0 else "dim"
    )
    summary.append(f"├── 🟠 HIGH:      {high}\n", style="red" if high > 0 else "dim")
    summary.append(
        f"├── 🟡 MEDIUM:    {medium}\n", style="yellow" if medium > 0 else "dim"
    )
    summary.append(f"└── 🔵 LOW:       {low}\n", style="blue" if low > 0 else "dim")
    summary.append("\n")
    summary.append(f"TOTAL: {results.failed} security issues detected", style="bold")

    console.print(
        Panel(
            summary,
            title="[bold]🛡️ Security Audit Complete[/]",
            border_style=score_color,
            padding=(0, 2),
        )
    )


def print_audit_findings_fomo(
    results: CheckovResults,
    console_out: Console | None = None,
) -> None:
    """
    Print audit findings with FOMO design.

    FOMO Philosophy:
    - ALL issue titles are visible (user knows what's broken)
    - First CRITICAL gets 2-line remediation preview
    - Remaining remediation is gated by plan

    Args:
        results: The Checkov scan results
        console_out: Optional console override (for testing)
    """
    output = console_out or console
    manager = get_license_manager()
    plan_features = get_plan_features(manager.current_plan)

    # Determine what to show based on plan
    show_full_remediation = plan_features.audit_details_visible
    first_critical_preview_lines = plan_features.audit_first_critical_preview_lines

    # Print summary first
    print_audit_summary_fomo(results)

    if not results.findings:
        output.print()
        output.print("[bold green]✓ No security issues found![/]")
        return

    # Group findings by severity
    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    shown_first_critical = False
    finding_index = 0
    hidden_count = 0

    for severity in severity_order:
        findings = results.findings_by_severity.get(severity, [])
        if not findings:
            continue

        output.print()
        style = SEVERITY_STYLES.get(severity, SEVERITY_STYLES["UNKNOWN"])
        output.print(f"[bold]{style['badge']} Issues ({len(findings)})[/]")
        output.print()

        for finding in findings:
            finding_index += 1

            # Always show the title (FOMO: user knows what's broken)
            show_lock = not show_full_remediation
            print_finding_title(finding, finding_index, show_lock=show_lock)

            # Show remediation based on plan
            if show_full_remediation:
                # SOLO+ users: show full remediation
                _print_full_remediation(finding, output)
            elif severity == "CRITICAL" and not shown_first_critical:
                # FREE users: show 2-line preview for first CRITICAL only
                preview_lines = first_critical_preview_lines or 2
                print_remediation_preview(finding, max_lines=preview_lines)
                shown_first_critical = True
            else:
                # Hidden remediation (counted for FOMO CTA)
                hidden_count += 1

    # Print upgrade CTA for FREE users
    if not show_full_remediation:
        output.print()
        print_upgrade_cta(
            total_findings=len(results.findings),
            hidden_count=hidden_count,
            plan=Plan.FREE,
        )


def _print_full_remediation(
    finding: CheckovFinding,
    output: Console,
) -> None:
    """
    Print full remediation details for a finding (SOLO+ users).

    Args:
        finding: The Checkov finding
        output: Console to print to
    """
    fix = _get_fix_suggestion(finding.check_id)

    output.print()
    output.print(f"     [dim]Resource:[/] {finding.resource}")
    output.print(f"     [dim]File:[/] {finding.file_path}:{finding.file_line_range[0]}")

    if fix:
        output.print()
        output.print("     [dim]┌─ Terraform Fix ───────────────────────────[/]")
        for line in fix.strip().split("\n"):
            output.print(f"     [dim]│[/] [cyan]{line}[/]")
        output.print("     [dim]└───────────────────────────────────────────[/]")
    elif finding.guideline:
        output.print(f"     [dim]Guide:[/] {finding.guideline}")


def format_severity_table(results: CheckovResults) -> Table:
    """
    Create a Rich table showing severity breakdown.

    Args:
        results: The Checkov scan results

    Returns:
        Rich Table with severity counts
    """
    table = Table(title="Severity Breakdown", show_header=True)
    table.add_column("Severity", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Status", justify="center")

    severity_order = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    for severity in severity_order:
        count = len(results.findings_by_severity.get(severity, []))
        style = SEVERITY_STYLES.get(severity, SEVERITY_STYLES["UNKNOWN"])
        status = "⚠️" if count > 0 else "✓"

        table.add_row(
            f"[{style['color']}]{severity}[/]",
            str(count),
            status,
        )

    return table
