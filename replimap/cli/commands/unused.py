"""Unused resources detection command for RepliMap CLI."""

from __future__ import annotations

import csv
import json as json_module
import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from replimap.cli.utils import console, get_aws_session, get_profile_region
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners


def unused_command(
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
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file path (JSON, CSV, or Markdown)",
    ),
    output_format: str = typer.Option(
        "console",
        "--format",
        "-f",
        help="Output format: console, json, csv, markdown",
    ),
    confidence: str = typer.Option(
        "all",
        "--confidence",
        "-c",
        help="Filter by confidence: high, medium, low, all",
    ),
    resource_types: str | None = typer.Option(
        None,
        "--types",
        "-t",
        help="Resource types to check: ec2,ebs,rds,nat,elb (comma-separated)",
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
    Detect unused and underutilized AWS resources.

    Identifies resources that may be candidates for termination
    or optimization to reduce costs.

    \b
    Examples:
        replimap unused -r us-east-1
        replimap unused -r us-east-1 --confidence high
        replimap unused -r us-east-1 --types ec2,ebs
        replimap unused -r us-east-1 -f json -o unused.json
    """
    from replimap.cost.unused_detector import (
        ConfidenceLevel,
        UnusedResourceDetector,
    )
    from replimap.licensing import check_cost_allowed

    # Check feature access
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
            f"[bold cyan]Unused Resource Detector[/bold cyan]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{effective_profile}[/]",
            border_style="cyan",
        )
    )

    session = get_aws_session(
        effective_profile, effective_region, use_cache=not no_cache
    )

    types_filter = None
    if resource_types:
        types_filter = [t.strip().lower() for t in resource_types.split(",")]

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
            task = progress.add_task("Scanning for unused resources...", total=None)

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

    # Analyze resource utilization (global signal handler handles Ctrl-C)
    import asyncio

    account_id = session.client("sts").get_caller_identity().get("Account", "")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing resource utilization...", total=None)
        detector = UnusedResourceDetector(
            region=effective_region,
            account_id=account_id,
        )

        async def run_detection():
            return await detector.scan(graph, check_metrics=True)

        report = asyncio.run(run_detection())
        unused_resources = report.unused_resources
        progress.update(task, completed=True)

    # Filter by confidence
    if confidence != "all":
        confidence_map = {
            "high": ConfidenceLevel.HIGH,
            "medium": ConfidenceLevel.MEDIUM,
            "low": ConfidenceLevel.LOW,
        }
        filter_confidence = confidence_map.get(confidence.lower())
        if filter_confidence:
            unused_resources = [
                r for r in unused_resources if r.confidence == filter_confidence
            ]

    # Filter by resource type
    if types_filter:
        unused_resources = [
            r
            for r in unused_resources
            if any(t in r.resource_type.lower() for t in types_filter)
        ]

    console.print()
    if not unused_resources:
        console.print("[green]✓ No unused resources detected![/green]")
        console.print()
        return

    console.print(
        f"[yellow]Found {len(unused_resources)} unused/underutilized resources[/yellow]\n"
    )

    if output_format == "console":
        # Group by resource type
        by_type: dict[str, list] = {}
        for r in unused_resources:
            if r.resource_type not in by_type:
                by_type[r.resource_type] = []
            by_type[r.resource_type].append(r)

        for rtype, resources in sorted(by_type.items()):
            console.print(f"[bold]{rtype}[/bold] ({len(resources)})")
            table = Table(show_header=True)
            table.add_column("Resource ID", style="cyan")
            table.add_column("Name")
            table.add_column("Reason")
            table.add_column("Confidence")
            table.add_column("Monthly Savings", justify="right")

            for r in resources[:10]:
                conf_style = {"high": "green", "medium": "yellow", "low": "dim"}.get(
                    r.confidence.value, "dim"
                )
                table.add_row(
                    r.resource_id,
                    r.resource_name[:30] if r.resource_name else "-",
                    r.reason.description[:40],
                    f"[{conf_style}]{r.confidence.value}[/]",
                    f"${r.estimated_monthly_savings:.2f}"
                    if r.estimated_monthly_savings
                    else "-",
                )

            console.print(table)
            if len(resources) > 10:
                console.print(f"  ... and {len(resources) - 10} more")
            console.print()

        total_savings = sum(r.estimated_monthly_savings or 0 for r in unused_resources)
        if total_savings > 0:
            console.print(
                f"[bold green]Potential monthly savings: ${total_savings:.2f}[/bold green]"
            )

    elif output_format == "json":
        output_path = output or Path("unused_resources.json")
        data = {
            "region": effective_region,
            "total_unused": len(unused_resources),
            "resources": [
                {
                    "resource_id": r.resource_id,
                    "resource_type": r.resource_type,
                    "resource_name": r.resource_name,
                    "reason": r.reason.value,
                    "confidence": r.confidence.value,
                    "details": r.details,
                    "estimated_monthly_savings": float(
                        r.estimated_monthly_savings or 0
                    ),
                }
                for r in unused_resources
            ],
        }
        with open(output_path, "w") as f:
            json_module.dump(data, f, indent=2)
        console.print(f"[green]✓ Saved to {output_path}[/]")

    elif output_format == "csv":
        output_path = output or Path("unused_resources.csv")
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Resource ID",
                    "Type",
                    "Name",
                    "Reason",
                    "Confidence",
                    "Details",
                    "Monthly Savings",
                ]
            )
            for r in unused_resources:
                writer.writerow(
                    [
                        r.resource_id,
                        r.resource_type,
                        r.resource_name,
                        r.reason.value,
                        r.confidence.value,
                        r.details,
                        r.estimated_monthly_savings or 0,
                    ]
                )
        console.print(f"[green]✓ Saved to {output_path}[/]")

    elif output_format in ("md", "markdown"):
        output_path = output or Path("unused_resources.md")
        with open(output_path, "w") as f:
            f.write("# Unused Resources Report\n\n")
            f.write(f"- Region: {effective_region}\n")
            f.write(f"- Total: {len(unused_resources)}\n\n")
            f.write("| Resource ID | Type | Reason | Confidence | Savings |\n")
            f.write("|-------------|------|--------|------------|--------|\n")
            for r in unused_resources:
                f.write(
                    f"| {r.resource_id} | {r.resource_type} | {r.reason.value} | "
                    f"{r.confidence.value} | ${r.estimated_monthly_savings or 0:.2f} |\n"
                )
        console.print(f"[green]✓ Saved to {output_path}[/]")

    console.print()


def register(app: typer.Typer) -> None:
    """Register the unused command with the Typer app."""
    app.command(name="unused")(unused_command)
