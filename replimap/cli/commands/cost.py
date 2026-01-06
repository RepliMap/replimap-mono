"""Cost estimation command for RepliMap CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from replimap.cli.utils import console, get_aws_session, get_profile_region, logger
from replimap.core import GraphEngine
from replimap.core.browser import open_in_browser
from replimap.scanners.base import run_all_scanners


def cost_command(
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
        help="Output file path (HTML, JSON, CSV, or Markdown)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, table, html, json, csv, or markdown",
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
    acknowledge: bool = typer.Option(
        False,
        "--acknowledge",
        "-y",
        help="Acknowledge that this is an estimate only (skip confirmation for exports)",
    ),
    # RI-Aware Pricing (P3-4)
    ri_aware: bool = typer.Option(
        False,
        "--ri-aware",
        help="Consider Reserved Instances and Savings Plans in cost estimates",
    ),
    show_reservations: bool = typer.Option(
        False,
        "--show-reservations",
        help="Show detailed reservation utilization",
    ),
) -> None:
    """Estimate monthly AWS costs for your infrastructure.

    \b

    IMPORTANT: These are rough estimates only. Actual AWS costs may
    differ by 20-40% depending on usage patterns, data transfer, and
    pricing agreements.

    \b

    Provides cost breakdown by category, resource, and region with
    optimization recommendations. This is a Pro+ feature.

    \b

    Output formats:

    - console: Rich terminal output with summary (default)

    - table: Full table of all resource costs

    - html: Interactive HTML report with charts

    - json: Machine-readable JSON

    - csv: Spreadsheet-compatible CSV

    - markdown: Markdown report

    \b

    Examples:

        replimap cost -r us-east-1

        replimap cost -r us-east-1 --vpc vpc-12345

        replimap cost -r us-east-1 -f html -o cost-report.html

        replimap cost -r us-east-1 -f json -o costs.json --acknowledge

    \b

    RI-Aware Pricing:

        replimap cost -r us-east-1 --ri-aware

        replimap cost -r us-east-1 --ri-aware --show-reservations
    """
    from replimap.cost import CostEstimator, CostReporter
    from replimap.licensing import check_cost_allowed

    # Check cost feature access (Pro+ feature)
    cost_gate = check_cost_allowed()
    if not cost_gate.allowed:
        console.print(cost_gate.prompt)
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

    console.print()
    console.print(
        Panel(
            f"[bold green]Cost Estimator[/bold green]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else ""),
            border_style="green",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Try to load from cache first
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    # Try to load from cache first (global signal handler handles Ctrl-C)
    console.print()
    cached_graph, cache_meta = get_or_load_graph(
        profile=profile or "default",
        region=effective_region,
        console=console,
        refresh=refresh,
        vpc=vpc,
    )

    # Use cached graph or scan
    if cached_graph is not None:
        graph = cached_graph
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning AWS resources...", total=None)

            # Create graph and run scanners
            graph = GraphEngine()
            run_all_scanners(
                session=session,
                region=effective_region,
                graph=graph,
            )

            # Apply VPC filter if specified
            if vpc:
                from replimap.core import ScanFilter, apply_filter_to_graph

                filter_config = ScanFilter(
                    vpc_ids=[vpc],
                    include_vpc_resources=True,
                )
                graph = apply_filter_to_graph(graph, filter_config)

            progress.update(task, completed=True)

        # Save to cache
        save_graph_to_cache(
            graph=graph,
            profile=profile or "default",
            region=effective_region,
            console=console,
            vpc=vpc,
        )

    # Estimate costs
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Estimating costs...", total=None)

        try:
            estimator = CostEstimator(effective_region)
            estimate = estimator.estimate_from_graph_engine(graph)

            # Apply RI-aware pricing if requested (P3-4)
            ri_analysis = None
            if ri_aware:
                progress.update(task, description="Analyzing reservations...")
                try:
                    from replimap.cost.ri_aware import RIAwareAnalyzer

                    # Get credentials from the already-authenticated session
                    # (avoids MFA re-prompt and assume-role hang in async context)
                    ri_credentials: dict[str, str] | None = None
                    session_creds = session.get_credentials()
                    if session_creds:
                        frozen = session_creds.get_frozen_credentials()
                        ri_credentials = {
                            "aws_access_key_id": frozen.access_key,
                            "aws_secret_access_key": frozen.secret_key,
                        }
                        if frozen.token:
                            ri_credentials["aws_session_token"] = frozen.token

                    async def run_ri_analysis():
                        """Run RI analysis with proper cleanup."""
                        async with RIAwareAnalyzer(
                            region=effective_region, credentials=ri_credentials
                        ) as analyzer:
                            return await analyzer.analyze()

                    ri_analysis = asyncio.run(run_ri_analysis())

                    # Adjust costs based on reservations
                    if ri_analysis and ri_analysis.total_potential_savings > 0:
                        console.print(
                            f"\n[dim]RI/Savings Plans coverage: "
                            f"${ri_analysis.total_potential_savings:.2f}/month savings[/]"
                        )
                except Exception as e:
                    logger.warning(f"Could not analyze reservations: {e}")

            progress.update(task, completed=True)

        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Cost estimation failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            logger.exception("Cost estimation failed")
            raise typer.Exit(1)

    # Report results
    reporter = CostReporter()
    console.print()

    # Helper function to confirm export
    def confirm_export() -> bool:
        """Ask user to acknowledge estimate disclaimer before export."""
        if acknowledge:
            return True

        console.print()
        console.print("[yellow]⚠️ Before exporting, please acknowledge:[/yellow]")
        console.print("   This estimate is for planning purposes only.")
        console.print("   Actual costs may differ by 20-40%.")
        console.print("   Data transfer, API calls, and other fees are NOT included.")
        console.print()

        return typer.confirm("I understand this is an estimate only. Export anyway?")

    if output_format == "table":
        reporter.to_table(estimate)
    elif output_format == "json":
        output_path = output or Path("./cost-estimate.json")
        if confirm_export():
            reporter.to_json(estimate, output_path)
    elif output_format == "csv":
        output_path = output or Path("./cost-estimate.csv")
        if confirm_export():
            reporter.to_csv(estimate, output_path)
    elif output_format == "html":
        output_path = output or Path("./cost-estimate.html")
        if confirm_export():
            reporter.to_html(estimate, output_path)
            if open_report:
                console.print()
                open_in_browser(output_path, console=console)
    elif output_format in ("md", "markdown"):
        output_path = output or Path("./cost-estimate.md")
        if confirm_export():
            reporter.to_markdown(estimate, output_path)
    else:
        # Default: console output
        reporter.to_console(estimate)

    # Also export if output path specified but format is console
    if output and output_format == "console":
        if not confirm_export():
            console.print()
            return

        if output.suffix == ".html":
            reporter.to_html(estimate, output)
            if open_report:
                console.print()
                open_in_browser(output, console=console)
        elif output.suffix == ".json":
            reporter.to_json(estimate, output)
        elif output.suffix == ".csv":
            reporter.to_csv(estimate, output)
        elif output.suffix == ".md":
            reporter.to_markdown(estimate, output)

    # Show reservation details if requested (P3-4)
    if show_reservations and ri_analysis:
        console.print("\n[bold]Reservation Utilization[/bold]")
        table = Table(show_header=True)
        table.add_column("Type", style="cyan")
        table.add_column("ID")
        table.add_column("Instance Type")
        table.add_column("Utilization", justify="right")
        table.add_column("Status")

        for ri in ri_analysis.reserved_instances[:10]:  # Show first 10
            util_pct = ri.utilization_percentage
            if util_pct >= 80:
                status = "[green]Healthy[/]"
            elif util_pct >= 60:
                status = "[yellow]Medium[/]"
            elif util_pct >= 40:
                status = "[orange1]Low[/]"
            else:
                status = "[red]Critical[/]"

            table.add_row(
                "RI",
                ri.reservation_id[:16] + "...",
                ri.instance_type,
                f"{util_pct:.1f}%",
                status,
            )

        for sp in ri_analysis.savings_plans[:10]:  # Show first 10
            util_pct = sp.utilization_percentage
            if util_pct >= 80:
                status = "[green]Healthy[/]"
            elif util_pct >= 60:
                status = "[yellow]Medium[/]"
            else:
                status = "[red]Low[/]"

            table.add_row(
                "SP",
                sp.savings_plan_id[:16] + "...",
                sp.savings_plan_type,
                f"{util_pct:.1f}%",
                status,
            )

        console.print(table)

        if ri_analysis.waste_items:
            console.print(
                f"\n[yellow]⚠ Found {len(ri_analysis.waste_items)} underutilized reservations[/]"
            )

    console.print()


def register(app: typer.Typer) -> None:
    """Register the cost command with the Typer app."""
    app.command(name="cost")(cost_command)
