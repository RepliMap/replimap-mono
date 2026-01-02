"""Drift detection command for RepliMap CLI."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session, get_profile_region
from replimap.core.browser import open_in_browser
from replimap.licensing import check_drift_allowed


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
    """
    Detect infrastructure drift between Terraform state and AWS.

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
        replimap drift -r us-east-1 --state-bucket my-bucket --state-key prod/tf.tfstate
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


def register(app: typer.Typer) -> None:
    """Register the drift command with the Typer app."""
    app.command(name="drift")(drift_command)
