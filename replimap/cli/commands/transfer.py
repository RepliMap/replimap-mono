"""Data transfer analysis command for RepliMap CLI."""

from __future__ import annotations

import json as json_module
import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session, get_profile_region
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners


def transfer_command(
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
        help="AWS region to analyze",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, json",
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
    Analyze data transfer costs and optimization opportunities.

    Identifies costly data transfer patterns.

    Examples:
        replimap transfer -r us-east-1
        replimap transfer -r us-east-1 -f json -o transfer.json
    """
    from replimap.cost.transfer_analyzer import DataTransferAnalyzer
    from replimap.licensing import check_cost_allowed

    cost_gate = check_cost_allowed()
    if not cost_gate.allowed:
        console.print(cost_gate.prompt)
        raise typer.Exit(1)

    # Determine region (flag > profile > env > default)
    effective_region = region
    region_source = "flag"

    if not effective_region:
        profile_region = get_profile_region(profile)
        if profile_region:
            effective_region = profile_region
            region_source = f"profile '{profile or 'default'}'"
        else:
            effective_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
            region_source = "default"

    effective_profile = profile or "default"

    console.print(
        Panel(
            f"[bold cyan]Data Transfer Analyzer[/bold cyan]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{effective_profile}[/]",
            border_style="cyan",
        )
    )

    session = get_aws_session(
        effective_profile, effective_region, use_cache=not no_cache
    )

    # Try to load from cache first (global signal handler handles Ctrl-C)
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    console.print()
    cached_graph, cache_meta = get_or_load_graph(
        profile=effective_profile,
        region=effective_region,
        console=console,
        refresh=refresh,
    )

    if cached_graph is not None:
        graph = cached_graph
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Scanning infrastructure...", total=None)

            graph = GraphEngine()
            run_all_scanners(session, effective_region, graph)
            progress.update(task, completed=True)

        # Save to cache
        save_graph_to_cache(
            graph=graph,
            profile=effective_profile,
            region=effective_region,
            console=console,
        )

    # Analyze transfer paths
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing transfer paths...", total=None)
        try:
            analyzer = DataTransferAnalyzer(session, effective_region)
            report = analyzer.analyze_from_graph(graph)
            progress.update(task, completed=True)
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            raise typer.Exit(1)

    console.print()

    if output_format == "console":
        console.print("[bold]Transfer Cost Summary[/bold]")
        console.print(f"  Total paths analyzed: {report.total_paths}")
        console.print(f"  Estimated monthly cost: ${report.total_monthly_cost:.2f}")
        console.print()

        if report.cross_az_paths:
            console.print(
                f"[bold yellow]Cross-AZ Traffic ({len(report.cross_az_paths)} paths)[/bold yellow]"
            )
            console.print("  [dim]Cross-AZ traffic incurs $0.01/GB each way[/dim]")
            for path in report.cross_az_paths[:5]:
                console.print(
                    f"  • {path.source_type} → {path.destination_type}: "
                    f"~{path.estimated_gb_month} GB/mo (${float(path.estimated_gb_month) * 0.02:.2f})"
                )
            console.print()

        if report.nat_gateway_paths:
            console.print(
                f"[bold yellow]NAT Gateway Traffic ({len(report.nat_gateway_paths)} paths)[/bold yellow]"
            )
            console.print("  [dim]NAT Gateway: $0.045/hour + $0.045/GB processed[/dim]")
            for path in report.nat_gateway_paths[:5]:
                console.print(
                    f"  • {path.source_type} → Internet: ~{path.estimated_gb_month} GB/mo"
                )
            console.print()

        if report.optimizations:
            console.print(
                f"[bold green]Optimization Recommendations ({len(report.optimizations)})[/bold green]"
            )
            for opt in report.optimizations[:5]:
                console.print(f"  ✓ {opt.description}")
                console.print(
                    f"    [dim]Potential savings: ${opt.estimated_savings:.2f}/mo[/dim]"
                )
            console.print()

    elif output_format == "json":
        output_path = output or Path("transfer_analysis.json")
        with open(output_path, "w") as f:
            json_module.dump(report.to_dict(), f, indent=2)
        console.print(f"[green]✓ Saved to {output_path}[/]")

    console.print()


def register(app: typer.Typer) -> None:
    """Register the transfer command with the Typer app."""
    app.command(name="transfer")(transfer_command)
