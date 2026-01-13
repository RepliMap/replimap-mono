"""Drift detection command for RepliMap CLI.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
- Console output goes to stderr for stdout hygiene
- JSON mode available via global --format flag
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich import box
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import console, get_aws_session, get_profile_region
from replimap.core.browser import open_in_browser
from replimap.licensing import check_drift_allowed


def _load_graph(graph_file: Path):
    """Load a graph from file (supports both JSON and SQLite formats)."""
    suffix = graph_file.suffix.lower()

    if suffix == ".db":
        from replimap.core.unified_storage import GraphEngineAdapter

        return GraphEngineAdapter(db_path=str(graph_file))
    elif suffix == ".json":
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)
    else:
        # Try SQLite first
        try:
            with open(graph_file, "rb") as f:
                if f.read(16).startswith(b"SQLite format"):
                    from replimap.core.unified_storage import GraphEngineAdapter

                    return GraphEngineAdapter(db_path=str(graph_file))
        except (OSError, ValueError):
            pass  # Fall through to JSON loader
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)


# Create a Typer app for drift subcommands
drift_app = typer.Typer(
    help="Infrastructure drift detection commands",
    no_args_is_help=False,
)


def drift_command(
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
        help="AWS region to scan",
    ),
    state: Path | None = typer.Option(
        None,
        "--state",
        "-s",
        help="Path to terraform.tfstate file",
    ),
    state_bucket: str | None = typer.Option(
        None,
        "--state-bucket",
        help="S3 bucket for remote state",
    ),
    state_key: str | None = typer.Option(
        None,
        "--state-key",
        help="S3 key for remote state",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the scan (optional)",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (HTML or JSON)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, html, or json",
    ),
    fail_on_drift: bool = typer.Option(
        False,
        "--fail-on-drift",
        help="Exit with code 1 if any drift detected (for CI/CD)",
    ),
    fail_on_high: bool = typer.Option(
        False,
        "--fail-on-high",
        help="Exit with code 1 only for HIGH/CRITICAL drift (for CI/CD)",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        "-R",
        help="Force fresh AWS scan (ignore cached graph)",
    ),
) -> None:
    """Detect infrastructure drift between Terraform state and AWS.

    \b

    Compares your Terraform state file against the actual AWS resources
    to identify changes made outside of Terraform (console, CLI, etc).

    \b

    State Sources:

    - Local file: --state ./terraform.tfstate

    - S3 remote: --state-bucket my-bucket --state-key path/terraform.tfstate

    \b

    Output formats:

    - console: Rich terminal output (default)

    - html: Professional HTML report

    - json: Machine-readable JSON

    \b

    Examples:

        replimap drift -r us-east-1 -s ./terraform.tfstate

        replimap drift -r us-east-1 --state-bucket my-bucket
            --state-key prod/tf.tfstate

        replimap drift -r us-east-1 -s ./tf.tfstate -f html -o report.html

        replimap drift -r us-east-1 -s ./tf.tfstate --fail-on-drift --no-open

        replimap drift -r us-east-1 -s ./tf.tfstate --fail-on-high --no-open
    """
    from replimap.drift import DriftEngine, DriftReporter

    # Check drift feature access (Pro+ feature)
    drift_gate = check_drift_allowed()
    if not drift_gate.allowed:
        console.print(drift_gate.prompt)
        raise typer.Exit(1)

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

    # Validate inputs
    if not state and not (state_bucket and state_key):
        console.print(
            Panel(
                "[red]Either --state or --state-bucket/--state-key is required.[/]\n\n"
                "Examples:\n"
                "  [bold]replimap drift -r us-east-1 -s ./terraform.tfstate[/]\n"
                "  [bold]replimap drift -r us-east-1 --state-bucket my-bucket --state-key prod/terraform.tfstate[/]",
                title="Missing State Source",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Determine state source for display
    if state:
        state_display = str(state)
    else:
        state_display = f"s3://{state_bucket}/{state_key}"

    console.print()
    console.print(
        Panel(
            f"[bold orange1]RepliMap Drift Detector[/bold orange1]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"State: [cyan]{state_display}[/]\n"
            f"Format: [cyan]{output_format}[/]",
            border_style="orange1",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Build remote backend config if using S3
    remote_backend = None
    if state_bucket and state_key:
        remote_backend = {
            "bucket": state_bucket,
            "key": state_key,
            "region": effective_region,
        }

    # Try to use cached graph for AWS state
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    # Run drift detection (global signal handler handles Ctrl-C)
    try:
        console.print()
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=console,
            refresh=refresh,
            vpc=vpc,
        )
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Detecting drift...", total=None)

            engine = DriftEngine(
                session=session,
                region=effective_region,
                profile=profile,
            )

            report = engine.detect(
                state_path=state,
                remote_backend=remote_backend,
                vpc_id=vpc,
                graph=cached_graph,
            )

            # Save to cache if we did a fresh scan
            if cached_graph is None and hasattr(engine, "_graph"):
                save_graph_to_cache(
                    graph=engine._graph,
                    profile=profile or "default",
                    region=effective_region,
                    console=console,
                    vpc=vpc,
                )

            progress.update(task, completed=True)
    except FileNotFoundError as e:
        console.print()
        console.print(
            Panel(
                f"[red]State file not found:[/]\n{e}",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Drift detection failed:[/]\n{e}",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Generate output
    reporter = DriftReporter()

    # Console output (always show summary)
    if output_format == "console" or not output:
        console.print()
        if report.has_drift:
            console.print(
                Panel(
                    f"[bold red]DRIFT DETECTED[/bold red]\n\n"
                    f"[red]Total drifts:[/] {report.drifted_resources}\n"
                    f"[green]  Added (not in TF):[/] {report.added_resources}\n"
                    f"[red]  Removed (deleted):[/] {report.removed_resources}\n"
                    f"[yellow]  Modified:[/] {report.modified_resources}",
                    border_style="red",
                )
            )

            # Show high priority drifts
            critical_high = report.critical_drifts + report.high_drifts
            if critical_high:
                console.print()
                console.print("[bold red]High Priority Drifts:[/bold red]")
                for d in critical_high[:5]:
                    drift_icon = {"added": "+", "removed": "-", "modified": "~"}.get(
                        d.drift_type.value, "?"
                    )
                    console.print(
                        f"  [{d.severity.value.upper()}] [{drift_icon}] {d.resource_type}: {d.resource_id}"
                    )
                if len(critical_high) > 5:
                    console.print(f"  [dim]... and {len(critical_high) - 5} more[/dim]")
        else:
            console.print(
                Panel(
                    f"[bold green]NO DRIFT[/bold green]\n\n"
                    f"Your AWS resources match your Terraform state.\n"
                    f"Total resources checked: {report.total_resources}",
                    border_style="green",
                )
            )

    # HTML output
    if output_format == "html" or (output and output.suffix == ".html"):
        output_path = output or Path("./drift-report.html")
        reporter.to_html(report, output_path)
        console.print()
        console.print(f"[green]HTML report:[/] {output_path.absolute()}")
        if open_report:
            open_in_browser(output_path, console=console)

    # JSON output
    if output_format == "json" or (output and output.suffix == ".json"):
        output_path = output or Path("./drift-report.json")
        reporter.to_json(report, output_path)
        console.print()
        console.print(f"[green]JSON report:[/] {output_path.absolute()}")

    # CI/CD exit codes
    exit_code = 0

    if fail_on_drift and report.has_drift:
        console.print()
        console.print(
            f"[bold red]CI/CD FAILED: {report.drifted_resources} drift(s) detected[/bold red]"
        )
        exit_code = 1

    if fail_on_high and (report.critical_drifts or report.high_drifts):
        high_count = len(report.critical_drifts) + len(report.high_drifts)
        console.print()
        console.print(
            f"[bold red]CI/CD FAILED: {high_count} HIGH/CRITICAL drift(s)[/bold red]"
        )
        exit_code = 1

    if exit_code == 0 and (fail_on_drift or fail_on_high):
        console.print()
        console.print("[bold green]CI/CD PASSED: No significant drift[/bold green]")

    console.print()
    console.print(f"[dim]Scan completed in {report.scan_duration_seconds}s[/dim]")
    console.print()

    if exit_code != 0:
        raise typer.Exit(exit_code)


@drift_app.command("offline")
def offline_detect_command(
    profile: str = typer.Option(
        "default",
        "-p",
        "--profile",
        help="RepliMap profile (cached scan)",
    ),
    state_file: str = typer.Option(
        "./terraform.tfstate",
        "-s",
        "--state",
        help="Path to terraform.tfstate",
    ),
    output: str | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output JSON report file",
    ),
    sarif: str | None = typer.Option(
        None,
        "--sarif",
        help="Output SARIF file for GitHub Security",
    ),
    fail_on_drift: bool = typer.Option(
        False,
        "--fail-on-drift",
        help="Exit code 1 if drift detected (for CI/CD)",
    ),
    severity: str = typer.Option(
        "low",
        "--severity",
        help="Minimum severity to report: critical, high, medium, low",
    ),
    ignore_config: str | None = typer.Option(
        None,
        "--ignore",
        help="Path to .replimapignore file",
    ),
    quiet: bool = typer.Option(
        False,
        "-q",
        "--quiet",
        help="Minimal output (for scripts)",
    ),
) -> None:
    """Offline drift detection using cached RepliMap scan.

    \b

    This is an "offline terraform plan" - faster and doesn't require
    AWS connection or Terraform installation. Uses cached scan data.

    \b

    Examples:

        # Basic offline drift detection
        replimap drift offline -p prod -s ./terraform.tfstate

        # For CI/CD (fail on drift)
        replimap drift offline -p prod --fail-on-drift

        # Only critical/high severity
        replimap drift offline -p prod --severity high

        # With custom ignore rules
        replimap drift offline -p prod --ignore .replimapignore

        # Output for GitHub Security
        replimap drift offline -p prod --sarif drift-results.sarif
    """
    from replimap.core.cache_manager import get_cache_path
    from replimap.core.drift import DriftFilter, DriftSeverity, OfflineDriftDetector

    state_path = Path(state_file)

    if not state_path.exists():
        console.print(f"[red]State file not found: {state_path}[/red]")
        console.print()
        console.print("[dim]To create the state file:[/dim]")
        console.print("  terraform state pull > terraform.tfstate")
        raise typer.Exit(1)

    # Load cached scan
    try:
        cache_path = get_cache_path(profile)
        if not cache_path.exists():
            console.print(f"[red]No cached scan found for profile '{profile}'.[/red]")
            console.print(f"Run 'replimap scan -p {profile}' first.")
            raise typer.Exit(1)

        graph = _load_graph(cache_path)
        resources = list(graph.get_all_resources())
    except Exception as e:
        console.print(f"[red]Failed to load cached scan: {e}[/red]")
        raise typer.Exit(1)

    # Convert resources to dict format for detector
    live_resources = []
    for resource in resources:
        resource_dict = {
            "id": resource.id,
            "type": getattr(resource, "terraform_type", str(resource.resource_type)),
            "name": getattr(resource, "original_name", resource.id),
            "attributes": getattr(resource, "config", {}) or {},
        }
        live_resources.append(resource_dict)

    # Load ignore rules
    drift_filter = None
    if ignore_config:
        ignore_path = Path(ignore_config)
        if ignore_path.exists():
            drift_filter = DriftFilter.from_config(ignore_path)
            if not quiet:
                console.print(f"[dim]Loaded ignore rules from {ignore_config}[/dim]")

    if not quiet:
        console.print(
            f"[dim]Comparing {len(live_resources)} cached resources "
            f"against Terraform state...[/dim]"
        )

    # Run detection
    detector = OfflineDriftDetector(ignore_filter=drift_filter)
    report = detector.detect(live_resources, state_path)

    # Filter by severity
    severity_map = {
        "critical": DriftSeverity.CRITICAL,
        "high": DriftSeverity.HIGH,
        "medium": DriftSeverity.MEDIUM,
        "low": DriftSeverity.LOW,
    }
    min_severity = severity_map.get(severity.lower(), DriftSeverity.LOW)

    severity_order = [
        DriftSeverity.CRITICAL,
        DriftSeverity.HIGH,
        DriftSeverity.MEDIUM,
        DriftSeverity.LOW,
        DriftSeverity.INFO,
    ]
    min_index = severity_order.index(min_severity)

    report.findings = [
        f
        for f in report.findings
        if severity_order.index(f.max_change_severity) <= min_index
    ]

    # Output JSON
    if output:
        Path(output).write_text(report.to_json())
        if not quiet:
            console.print(f"[green]Report saved to {output}[/green]")

    # Output SARIF
    if sarif:
        sarif_data = report.to_sarif()
        Path(sarif).write_text(json.dumps(sarif_data, indent=2))
        if not quiet:
            console.print(f"[green]SARIF saved to {sarif}[/green]")

    # Display report
    if not quiet:
        _display_offline_report(report)
    else:
        _display_quiet(report)

    # Exit code
    if fail_on_drift and report.has_drift:
        raise typer.Exit(1)


@drift_app.command("compare-scans")
def compare_scans_command(
    profile: str = typer.Option(
        "default",
        "-p",
        "--profile",
        help="Current RepliMap profile",
    ),
    previous: str = typer.Option(
        ...,
        "--previous",
        help="Path to previous scan cache file",
    ),
    output: str | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output JSON report file",
    ),
) -> None:
    """Compare current scan against a previous scan.

    Useful for detecting AWS changes over time without Terraform.

    Example:

        replimap drift compare-scans -p prod --previous baseline.db
    """
    from replimap.core.cache_manager import get_cache_path
    from replimap.core.drift import ScanComparator

    try:
        cache_path = get_cache_path(profile)
        if not cache_path.exists():
            console.print(f"[red]No cached scan found for profile '{profile}'.[/red]")
            raise typer.Exit(1)

        current_graph = _load_graph(cache_path)
    except Exception as e:
        console.print(f"[red]Failed to load current scan: {e}[/red]")
        raise typer.Exit(1)

    prev_path = Path(previous)
    if not prev_path.exists():
        console.print(f"[red]Previous scan not found: {previous}[/red]")
        raise typer.Exit(1)

    try:
        prev_graph = _load_graph(prev_path)
    except Exception as e:
        console.print(f"[red]Failed to load previous scan: {e}[/red]")
        raise typer.Exit(1)

    current_resources = list(current_graph.get_all_resources())
    prev_resources = list(prev_graph.get_all_resources())

    console.print(
        f"[dim]Comparing {len(current_resources)} current vs "
        f"{len(prev_resources)} previous resources...[/dim]"
    )

    # Convert to dict format
    def resources_to_list(resources):
        result = []
        for r in resources:
            result.append(
                {
                    "id": r.id,
                    "type": getattr(r, "terraform_type", str(r.resource_type)),
                    "name": getattr(r, "original_name", r.id),
                    "attributes": getattr(r, "config", {}) or {},
                }
            )
        return result

    comparator = ScanComparator()
    report = comparator.compare(
        resources_to_list(current_resources),
        resources_to_list(prev_resources),
    )

    if output:
        Path(output).write_text(report.to_json())
        console.print(f"[green]Report saved to {output}[/green]")

    _display_offline_report(report)


def _display_offline_report(report) -> None:
    """Display drift report with rich formatting."""
    from replimap.core.drift import DriftType

    console.print()

    if not report.has_drift:
        console.print(
            Panel(
                "[bold green]No drift detected![/bold green]\n\n"
                "Infrastructure is in sync.",
                title="Drift Report",
                border_style="green",
            )
        )
        return

    # Summary panel
    summary = report.summary
    border_color = "red" if report.critical_count > 0 else "yellow"

    unmanaged = summary.get("by_drift_type", {}).get("unmanaged", 0)
    missing = summary.get("by_drift_type", {}).get("missing", 0)
    drifted = summary.get("by_drift_type", {}).get("drifted", 0)

    critical = summary.get("by_severity", {}).get("critical", 0)
    high = summary.get("by_severity", {}).get("high", 0)
    medium = summary.get("by_severity", {}).get("medium", 0)
    low = summary.get("by_severity", {}).get("low", 0)

    console.print(
        Panel(
            f"[bold]Found {len(report.findings)} drift findings[/bold]\n\n"
            f"By Type:\n"
            f"   Unmanaged: {unmanaged}\n"
            f"   Missing: {missing}\n"
            f"   Drifted: {drifted}\n\n"
            f"By Severity:\n"
            f"   Critical: {critical}\n"
            f"   High: {high}\n"
            f"   Medium: {medium}\n"
            f"   Low: {low}",
            title="Drift Report",
            border_style=border_color,
        )
    )

    # Group findings by type
    by_type: dict = {}
    for finding in report.findings:
        if finding.drift_type not in by_type:
            by_type[finding.drift_type] = []
        by_type[finding.drift_type].append(finding)

    # Display each type
    for drift_type in [DriftType.MISSING, DriftType.DRIFTED, DriftType.UNMANAGED]:
        findings = by_type.get(drift_type, [])
        if not findings:
            continue

        console.print()
        console.print(f"[bold]{drift_type.value.upper()} ({len(findings)})[/bold]")

        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("Resource", style="cyan", width=35)
        table.add_column("Type", width=25)
        table.add_column("Changes / Status", width=45)

        for finding in findings[:10]:
            # Build changes display
            if finding.changes:
                changes_text = ""
                for c in finding.changes[:3]:
                    changes_text += (
                        f"[{c.severity.value}] {c.field}: "
                        f"[red]{_truncate(c.expected)}[/] -> "
                        f"[green]{_truncate(c.actual)}[/]\n"
                    )
                if len(finding.changes) > 3:
                    changes_text += f"[dim]...and {len(finding.changes) - 3} more[/dim]"
            else:
                changes_text = f"[dim]{drift_type.value}[/dim]"

            # Resource info
            resource_text = finding.resource_name
            if finding.terraform_address:
                resource_text += f"\n[dim]{finding.terraform_address}[/dim]"
            resource_id_display = finding.resource_id
            if len(resource_id_display) > 40:
                resource_id_display = resource_id_display[:40] + "..."
            resource_text += f"\n[dim]{resource_id_display}[/dim]"

            table.add_row(
                resource_text,
                finding.resource_type,
                changes_text.strip(),
            )

        console.print(table)

        if len(findings) > 10:
            console.print(f"[dim]  ...and {len(findings) - 10} more[/dim]")

        # Remediation hint
        console.print()
        console.print(f"   [dim]{findings[0].remediation_hint}[/dim]")


def _display_quiet(report) -> None:
    """Minimal output for scripts."""
    if not report.has_drift:
        console.print("NO_DRIFT")
        return

    console.print(f"DRIFT_FOUND:{len(report.findings)}")
    console.print(f"CRITICAL:{report.critical_count}")
    console.print(f"HIGH:{report.high_count}")


def _truncate(val, max_len: int = 25) -> str:
    """Truncate value for display."""
    if val is None:
        return "null"
    s = str(val)
    if len(s) > max_len:
        return s[: max_len - 3] + "..."
    return s


def register(app: typer.Typer) -> None:
    """Register the drift command with the Typer app."""
    # Register the main drift command (online detection)
    app.command(name="drift")(enhanced_cli_error_handler(drift_command))
    # Also add drift as a subcommand group for offline detection
    app.add_typer(drift_app, name="drift-offline", help="Offline drift detection")
