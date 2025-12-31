"""Audit command for RepliMap CLI."""

from __future__ import annotations

import json
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session, get_profile_region
from replimap.licensing import check_audit_ci_mode_allowed, check_audit_fix_allowed
from replimap.ui import print_audit_findings_fomo

if TYPE_CHECKING:
    from replimap.audit.checkov_runner import CheckovResults


def _output_audit_json(
    results: CheckovResults,
    output_path: Path,
    region: str,
    profile: str | None,
    vpc_id: str | None,
) -> Path:
    """
    Output audit results as JSON.

    Args:
        results: Checkov scan results
        output_path: Base path for output (will change extension to .json)
        region: AWS region
        profile: AWS profile name
        vpc_id: VPC ID if specified

    Returns:
        Path to the generated JSON file
    """
    from replimap.audit.fix_suggestions import FIX_SUGGESTIONS
    from replimap.audit.soc2_mapping import get_soc2_mapping

    # Build SOC2 summary
    soc2_summary: dict = {}
    for f in results.findings:
        if f.check_result != "FAILED":
            continue
        mapping = get_soc2_mapping(f.check_id)
        if mapping:
            control = mapping.control
            if control not in soc2_summary:
                soc2_summary[control] = {
                    "control": control,
                    "category": mapping.category,
                    "count": 0,
                    "checks": [],
                }
            soc2_summary[control]["count"] += 1
            if f.check_id not in soc2_summary[control]["checks"]:
                soc2_summary[control]["checks"].append(f.check_id)

    # Build JSON output
    json_output = {
        "summary": {
            "score": results.score,
            "grade": results.grade,
            "passed": results.passed,
            "failed": results.failed,
            "skipped": results.skipped,
            "total": results.total,
            "high_severity_count": len(results.high_severity),
        },
        "metadata": {
            "account_id": "N/A",  # Would need to pass this through
            "region": region,
            "profile": profile,
            "vpc_id": vpc_id,
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
        "severity_breakdown": {
            "critical": len(results.findings_by_severity["CRITICAL"]),
            "high": len(results.findings_by_severity["HIGH"]),
            "medium": len(results.findings_by_severity["MEDIUM"]),
            "low": len(results.findings_by_severity["LOW"]),
        },
        "findings": [
            {
                "check_id": f.check_id,
                "check_name": f.check_name,
                "severity": f.severity,
                "result": f.check_result,
                "resource": f.resource,
                "file_path": f.file_path,
                "line_range": list(f.file_line_range),
                "soc2_mapping": (
                    {
                        "control": m.control,
                        "category": m.category,
                        "description": m.description,
                    }
                    if (m := get_soc2_mapping(f.check_id))
                    else None
                ),
                "has_fix_suggestion": f.check_id in FIX_SUGGESTIONS,
                "guideline": f.guideline,
            }
            for f in results.findings
            if f.check_result == "FAILED"
        ],
        "soc2_summary": soc2_summary,
    }

    # Determine output path
    json_path = output_path.with_suffix(".json")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(json_output, indent=2))

    return json_path


def _generate_remediation(results: CheckovResults, output_dir: Path) -> None:
    """
    Generate Terraform remediation code from audit results.

    Args:
        results: Checkov scan results containing findings
        output_dir: Directory to write remediation files
    """
    from replimap.audit.remediation import RemediationGenerator
    from replimap.audit.remediation.models import RemediationSeverity

    console.print()
    console.print(
        Panel(
            "[bold blue]🔧 Generating Remediation Code[/bold blue]\n\n"
            f"Output: [cyan]{output_dir}[/]",
            border_style="blue",
        )
    )

    generator = RemediationGenerator(results.findings, output_dir)
    plan = generator.generate()

    if plan.files:
        # Write all files
        plan.write_all(output_dir)

        console.print()
        console.print(
            Panel(
                f"[bold]Remediation Generated[/bold]\n\n"
                f"[green]✓ Files:[/] {len(plan.files)}\n"
                f"[green]✓ Coverage:[/] {plan.coverage_percent}%\n"
                f"[dim]Skipped:[/] {plan.skipped_findings} (no template available)",
                title="🔧 Remediation Summary",
                border_style="green",
            )
        )

        # Show by severity
        by_severity = plan.files_by_severity()

        severity_info = []
        if by_severity[RemediationSeverity.CRITICAL]:
            severity_info.append(
                f"[red]CRITICAL: {len(by_severity[RemediationSeverity.CRITICAL])}[/]"
            )
        if by_severity[RemediationSeverity.HIGH]:
            severity_info.append(
                f"[orange1]HIGH: {len(by_severity[RemediationSeverity.HIGH])}[/]"
            )
        if by_severity[RemediationSeverity.MEDIUM]:
            severity_info.append(
                f"[yellow]MEDIUM: {len(by_severity[RemediationSeverity.MEDIUM])}[/]"
            )
        if by_severity[RemediationSeverity.LOW]:
            severity_info.append(
                f"[green]LOW: {len(by_severity[RemediationSeverity.LOW])}[/]"
            )

        if severity_info:
            console.print(f"  Fixes by severity: {' | '.join(severity_info)}")

        console.print()
        console.print(f"[green]✓ Remediation:[/] {output_dir.absolute()}")
        console.print(f"[green]✓ README:[/] {output_dir.absolute()}/README.md")

        if plan.has_imports:
            console.print(
                f"[yellow]⚠ Import script:[/] {output_dir.absolute()}/import.sh"
            )
            console.print()
            console.print(
                "[dim]Some fixes require terraform import. "
                "Run import.sh before terraform apply.[/dim]"
            )

        if plan.warnings:
            console.print()
            for warning in plan.warnings:
                console.print(f"[yellow]⚠[/] {warning}")
    else:
        console.print()
        console.print(
            "[yellow]No remediation templates available for the detected findings.[/yellow]"
        )


def audit_command(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to audit",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the audit (optional)",
    ),
    output: Path = typer.Option(
        Path("./audit_report.html"),
        "--output",
        "-o",
        help="Path for HTML/JSON report",
    ),
    terraform_dir: Path = typer.Option(
        Path("./audit_output"),
        "--terraform-dir",
        "-t",
        help="Directory for generated Terraform files",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open report in browser after generation",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    fail_on_high: bool = typer.Option(
        False,
        "--fail-on-high",
        help="Exit with code 1 if HIGH/CRITICAL issues found (for CI/CD)",
    ),
    fail_on_score: int | None = typer.Option(
        None,
        "--fail-on-score",
        help="Exit with code 1 if score below threshold (e.g., --fail-on-score 70)",
    ),
    output_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html or json",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        help="Generate Terraform remediation code for findings",
    ),
    fix_output: Path = typer.Option(
        Path("./remediation"),
        "--fix-output",
        help="Directory for remediation Terraform files",
    ),
) -> None:
    """
    Run security audit on AWS infrastructure.

    Scans your AWS environment, generates a forensic Terraform snapshot,
    runs Checkov security analysis, and produces an HTML report with
    findings mapped to SOC2 controls.

    Requires Checkov to be installed: pip install checkov

    Examples:
        replimap audit --region us-east-1
        replimap audit -p prod -r ap-southeast-2 -v vpc-abc123
        replimap audit -r us-west-2 --no-open
        replimap audit -r us-east-1 --fail-on-high --no-open  # CI/CD mode
        replimap audit -r us-east-1 --fail-on-score 70 --no-open
        replimap audit -r us-east-1 --format json
        replimap audit -r us-east-1 --fix --fix-output ./remediation
    """
    from replimap.audit import AuditEngine, CheckovNotInstalledError

    # Determine region
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = "us-east-1"
            region_source = "default"

    console.print()
    console.print(
        Panel(
            f"[bold blue]🔒 RepliMap Security Audit[/bold blue]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Output: [cyan]{output}[/]\n"
            f"Terraform: [cyan]{terraform_dir}[/]",
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Check Checkov is installed
    try:
        engine = AuditEngine(
            session=session,
            region=effective_region,
            profile=profile,
            vpc_id=vpc,
        )
    except CheckovNotInstalledError:
        console.print()
        console.print(
            Panel(
                "[red]Checkov is not installed.[/]\n\n"
                "Install Checkov with:\n"
                "  [bold]pipx install checkov[/]  (recommended)\n\n"
                "Or:\n"
                "  [bold]pip install checkov[/]",
                title="Missing Dependency",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Run audit
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            results, report_path = engine.run(
                output_dir=terraform_dir,
                report_path=output,
            )
        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Audit failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        progress.update(task, completed=True)

    # Handle JSON output format
    if output_format.lower() == "json":
        json_path = _output_audit_json(results, output, effective_region, profile, vpc)
        console.print()
        console.print(f"[green]✓ JSON Report:[/] {json_path.absolute()}")
        console.print(f"[green]✓ Terraform:[/] {terraform_dir.absolute()}")
    else:
        # Display results with FOMO design
        # This shows ALL issue titles (even for FREE users)
        # First CRITICAL gets 2-line remediation preview
        # Remaining remediation details are gated by plan
        console.print()
        print_audit_findings_fomo(results, console_out=console)

        # Output paths
        console.print()
        console.print(f"[green]✓ Report:[/] {report_path.absolute()}")
        console.print(f"[green]✓ Terraform:[/] {terraform_dir.absolute()}")

        # Open report in browser (only for HTML format)
        if open_report:
            console.print()
            console.print("[dim]Opening report in browser...[/dim]")
            webbrowser.open(f"file://{report_path.absolute()}")

    # Generate remediation if requested (SOLO+ feature)
    if fix:
        fix_gate = check_audit_fix_allowed()
        if not fix_gate.allowed:
            console.print(fix_gate.prompt)
            raise typer.Exit(1)
        if results.findings:
            _generate_remediation(results, fix_output)

    # CI/CD checks (PRO+ feature)
    exit_code = 0

    if fail_on_high or fail_on_score is not None:
        ci_gate = check_audit_ci_mode_allowed()
        if not ci_gate.allowed:
            console.print(ci_gate.prompt)
            raise typer.Exit(1)

    if fail_on_high and results.high_severity:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: {len(results.high_severity)} HIGH/CRITICAL issues found[/bold red]"
        )
        for f in results.high_severity[:5]:
            console.print(f"   • {f.check_id}: {f.check_name}")
        if len(results.high_severity) > 5:
            console.print(f"   ... and {len(results.high_severity) - 5} more")
        exit_code = 1

    if fail_on_score is not None and results.score < fail_on_score:
        console.print()
        console.print(
            f"[bold red]❌ CI/CD FAILED: Score {results.score} below threshold {fail_on_score}[/bold red]"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_high or fail_on_score is not None):
        console.print()
        console.print("[bold green]✓ CI/CD PASSED[/bold green]")

    console.print()

    if exit_code != 0:
        raise typer.Exit(exit_code)


def register(app: typer.Typer) -> None:
    """Register the audit command with the Typer app."""
    app.command(name="audit")(audit_command)
