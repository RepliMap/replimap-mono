"""Dependency exploration command for RepliMap CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.status import Status

from replimap.cli.utils import console, get_aws_session, get_profile_region, logger
from replimap.core import GraphEngine
from replimap.core.browser import open_in_browser
from replimap.scanners.base import run_all_scanners


def _run_analyzer_mode(
    resource_id: str,
    session: Any,
    region: str,
    output_format: str,
    output: Path | None,
) -> None:
    """Run deep analyzer mode for deps command."""
    from replimap.deps import get_analyzer
    from replimap.deps.reporter import DependencyAnalysisReporter

    console.print()

    # Create AWS clients
    with Status("[bold blue]Creating AWS clients...", console=console):
        ec2_client = session.client("ec2", region_name=region)
        rds_client = session.client("rds", region_name=region)
        iam_client = session.client("iam")  # IAM is global
        lambda_client = session.client("lambda", region_name=region)
        elbv2_client = session.client("elbv2", region_name=region)
        autoscaling_client = session.client("autoscaling", region_name=region)
        elasticache_client = session.client("elasticache", region_name=region)
        s3_client = session.client("s3", region_name=region)
        sts_client = session.client("sts")

    # Get the appropriate analyzer
    try:
        analyzer = get_analyzer(
            resource_id,
            ec2_client=ec2_client,
            rds_client=rds_client,
            iam_client=iam_client,
            lambda_client=lambda_client,
            elbv2_client=elbv2_client,
            autoscaling_client=autoscaling_client,
            elasticache_client=elasticache_client,
            s3_client=s3_client,
            sts_client=sts_client,
        )
    except ValueError:
        console.print(
            Panel(
                f"[red]Unsupported resource type:[/] {resource_id}\n\n"
                f"Analyzer mode currently supports:\n"
                f"  • EC2 instances (i-xxx)\n"
                f"  • Security Groups (sg-xxx)\n"
                f"  • IAM Roles\n"
                f"  • RDS Instances\n"
                f"  • Auto Scaling Groups\n"
                f"  • S3 Buckets\n"
                f"  • Lambda Functions\n"
                f"  • Load Balancers (ALB/NLB)\n"
                f"  • ElastiCache Clusters\n\n"
                f"Use without --analyze flag for graph-based analysis.",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    # Run analysis with progress feedback
    with Status(
        f"[bold blue]Analyzing {analyzer.resource_type}...",
        console=console,
    ) as status:
        try:
            status.update(f"[bold blue]Analyzing {resource_id}...")
            analysis = analyzer.analyze(resource_id, region)

            # Update status for large queries
            from replimap.deps.models import RelationType

            consumers = analysis.dependencies.get(RelationType.CONSUMER, [])
            if len(consumers) > 10:
                status.update(
                    f"[bold blue]Found {len(consumers)} consumers, calculating blast radius..."
                )

        except ValueError:
            console.print(
                Panel(
                    f"[red]Resource not found:[/] {resource_id}\n\n"
                    f"Make sure the resource ID is correct and exists in region {region}.",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)
        except Exception as e:
            console.print(
                Panel(
                    f"[red]Analysis failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            logger.exception("Analyzer mode failed")
            raise typer.Exit(1)

    # Report results
    reporter = DependencyAnalysisReporter()
    console.print()

    if output_format == "tree":
        reporter.to_tree(analysis)
    elif output_format == "table":
        reporter.to_table(analysis)
    elif output_format == "json":
        output_path = output or Path("./deps.json")
        reporter.to_json(analysis, output_path)
    else:
        # Default: console output
        reporter.to_console(analysis)

    console.print()


def deps_command(
    resource_id: str = typer.Argument(
        ...,
        help="Resource ID to analyze (e.g., vpc-12345, sg-abc123)",
    ),
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
    max_depth: int = typer.Option(
        10,
        "--depth",
        "-d",
        help="Maximum depth to traverse",
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
        help="Output format: console, tree, table, html, or json",
    ),
    open_report: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open HTML report in browser after generation",
    ),
    show_disclaimer: bool = typer.Option(
        True,
        "--disclaimer/--no-disclaimer",
        help="Show disclaimer about limitations",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Show all resources (not summarized by type)",
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
    analyze: bool = typer.Option(
        False,
        "--analyze",
        "-a",
        help="Use deep analyzer mode with categorized output (EC2, SG, IAM Role)",
    ),
) -> None:
    """
    Explore dependencies for a resource.

    Shows what resources MAY be affected if you modify or delete a resource.
    This analysis is based on AWS API metadata only.

    IMPORTANT: Application-level dependencies (hardcoded IPs, DNS,
    config files) are NOT detected. Always validate all dependencies
    before making infrastructure changes.

    This is a Pro+ feature.

    \b
    Output formats:
    - console: Rich terminal output with summary (default)
    - tree: Tree view of dependencies
    - table: Table of affected resources
    - html: Interactive HTML report with D3.js visualization
    - json: Machine-readable JSON

    \b
    Examples:
        replimap deps sg-12345 -r us-east-1              # Security group deps
        replimap deps vpc-abc123 -r us-east-1 -f tree    # Tree view
        replimap deps i-xyz789 -r us-east-1 -f html -o deps.html
        replimap deps vpc-12345 -r us-east-1 --depth 3   # Limit depth
    """
    from replimap.dependencies import (
        DISCLAIMER_SHORT,
        DependencyExplorerReporter,
        DependencyGraphBuilder,
        ImpactCalculator,
    )
    from replimap.licensing import check_deps_allowed

    # Check deps feature access (Pro+ feature)
    deps_gate = check_deps_allowed()
    if not deps_gate.allowed:
        console.print(deps_gate.prompt)
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
            f"[bold blue]Dependency Explorer[/bold blue]\n\n"
            f"Resource: [cyan]{resource_id}[/]\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Max Depth: [cyan]{max_depth}[/]\n\n"
            f"[dim]{DISCLAIMER_SHORT}[/dim]",
            border_style="blue",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Use analyzer mode if requested (deep analysis with categorized output)
    if analyze:
        _run_analyzer_mode(
            resource_id=resource_id,
            session=session,
            region=effective_region,
            output_format=output_format,
            output=output,
        )
        return

    # Graph-based mode (default)
    # Try to load from cache first
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    # Try to load from cache first (global signal handler handles Ctrl-C)
    try:
        console.print()
        cached_graph, cache_meta = get_or_load_graph(
            profile=profile or "default",
            region=effective_region,
            console=console,
            refresh=refresh,
            vpc=vpc,
        )

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
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=profile or "default",
                region=effective_region,
                console=console,
                vpc=vpc,
            )
    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Dependency exploration failed:[/]\n{e}",
                title="Error",
                border_style="red",
            )
        )
        logger.exception("Dependency exploration failed")
        raise typer.Exit(1)

    # Apply VPC filter if specified
    if vpc:
        from replimap.core import ScanFilter, apply_filter_to_graph

        filter_config = ScanFilter(
            vpc_ids=[vpc],
            include_vpc_resources=True,
        )
        graph = apply_filter_to_graph(graph, filter_config)

    # Build dependency graph and explore dependencies
    try:
        builder = DependencyGraphBuilder()
        dep_graph = builder.build_from_graph_engine(graph, effective_region)

        # Build resource configs map for ASG detection
        resource_configs = {res.id: res.config for res in graph.get_all_resources()}

        # Explore dependencies
        calculator = ImpactCalculator(
            dep_graph,
            builder.get_nodes(),
            builder.get_edges(),
            resource_configs=resource_configs,
        )

        try:
            result = calculator.calculate_blast_radius(resource_id, max_depth)
        except ValueError:
            console.print()
            console.print(
                Panel(
                    f"[red]Resource not found:[/] {resource_id}\n\n"
                    f"Make sure the resource ID is correct and exists in region {effective_region}.\n\n"
                    f"[dim]Available resources: {len(builder.get_nodes())}[/]",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    except Exception as e:
        console.print()
        console.print(
            Panel(
                f"[red]Dependency exploration failed:[/]\n{e}",
                title="Error",
                border_style="red",
            )
        )
        logger.exception("Dependency exploration failed")
        raise typer.Exit(1)

    # Report results
    reporter = DependencyExplorerReporter()
    console.print()

    if output_format == "tree":
        reporter.to_tree(result)
    elif output_format == "table":
        reporter.to_table(result)
    elif output_format == "json":
        output_path = output or Path("./deps.json")
        reporter.to_json(result, output_path)
    elif output_format == "html":
        output_path = output or Path("./deps.html")
        reporter.to_html(result, output_path)
        if open_report:
            console.print()
            open_in_browser(output_path, console=console)
    else:
        # Default: console output (compact by default, verbose shows all)
        reporter.to_console(result, verbose=verbose)

    # Also export if output path specified but format is console
    if output and output_format == "console":
        if output.suffix == ".html":
            reporter.to_html(result, output)
            if open_report:
                console.print()
                open_in_browser(output, console=console)
        elif output.suffix == ".json":
            reporter.to_json(result, output)

    console.print()


# Backward compatibility alias for blast command
def blast_command(
    resource_id: str = typer.Argument(...),
    profile: str | None = typer.Option(None, "--profile", "-p"),
    region: str | None = typer.Option(None, "--region", "-r"),
    vpc: str | None = typer.Option(None, "--vpc", "-v"),
    max_depth: int = typer.Option(10, "--depth", "-d"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    output_format: str = typer.Option("console", "--format", "-f"),
    open_report: bool = typer.Option(True, "--open/--no-open"),
    no_cache: bool = typer.Option(False, "--no-cache"),
    refresh: bool = typer.Option(False, "--refresh", "-R"),
) -> None:
    """Deprecated: Use 'replimap deps' instead."""
    console.print(
        "[yellow]Note: 'replimap blast' is deprecated. "
        "Use 'replimap deps' instead.[/yellow]\n"
    )
    deps_command(
        resource_id=resource_id,
        profile=profile,
        region=region,
        vpc=vpc,
        max_depth=max_depth,
        output=output,
        output_format=output_format,
        open_report=open_report,
        show_disclaimer=True,
        no_cache=no_cache,
        refresh=refresh,
        analyze=False,
    )


def register(app: typer.Typer) -> None:
    """Register the deps and blast commands with the Typer app."""
    app.command(name="deps")(deps_command)
    app.command(name="blast", hidden=True)(blast_command)
