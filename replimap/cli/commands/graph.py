"""Graph visualization command for RepliMap CLI."""

from __future__ import annotations

import webbrowser
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_aws_session, get_profile_region


def graph_command(
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
        help="AWS region to visualize",
    ),
    vpc: str | None = typer.Option(
        None,
        "--vpc",
        "-v",
        help="VPC ID to scope the visualization (optional)",
    ),
    output: Path = typer.Option(
        Path("./infrastructure_graph.html"),
        "--output",
        "-o",
        help="Path for output file",
    ),
    output_format: str = typer.Option(
        "html",
        "--format",
        "-f",
        help="Output format: html (interactive D3.js), mermaid, or json",
    ),
    open_graph: bool = typer.Option(
        True,
        "--open/--no-open",
        help="Open graph in browser after generation (HTML only)",
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Don't use cached credentials",
    ),
    # Graph simplification options
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Show all resources (disable filtering)",
    ),
    show_sg_rules: bool = typer.Option(
        False,
        "--sg-rules",
        help="Show security group rules (hidden by default)",
    ),
    show_routes: bool = typer.Option(
        False,
        "--routes",
        help="Show routes and route tables (hidden by default)",
    ),
    no_collapse: bool = typer.Option(
        False,
        "--no-collapse",
        help="Disable resource grouping (show all individual resources)",
    ),
    security_view: bool = typer.Option(
        False,
        "--security",
        help="Security-focused view (show SGs, IAM, KMS)",
    ),
) -> None:
    """
    Generate visual dependency graph of AWS infrastructure.

    Scans your AWS environment and generates an interactive visualization
    showing resources and their dependencies.

    By default, the graph is simplified for readability:
    - Noisy resources (SG rules, routes) are hidden
    - Large groups of similar resources are collapsed

    Output formats:
    - html: Interactive D3.js force-directed graph (default)
    - mermaid: Mermaid diagram syntax for documentation
    - json: Raw JSON data for integration

    Examples:
        replimap graph --region us-east-1
        replimap graph -p prod -r us-west-2 -v vpc-abc123
        replimap graph -r us-east-1 --all           # Show everything
        replimap graph -r us-east-1 --sg-rules      # Include SG rules
        replimap graph -r us-east-1 --routes        # Include routes
        replimap graph -r us-east-1 --no-collapse   # No grouping
        replimap graph -r us-east-1 --security      # Security focus
        replimap graph -r us-east-1 --format mermaid -o docs/graph.md
    """
    from replimap.graph import GraphVisualizer, OutputFormat

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

    # Parse output format
    try:
        fmt = OutputFormat(output_format.lower())
    except ValueError:
        console.print(
            f"[red]Error:[/] Invalid format '{output_format}'. "
            f"Use one of: html, mermaid, json"
        )
        raise typer.Exit(1)

    # Build filter summary
    filter_parts = []
    if show_all:
        filter_parts.append("all resources")
    else:
        filter_parts.append("simplified")
        if show_sg_rules:
            filter_parts.append("+SG rules")
        if show_routes:
            filter_parts.append("+routes")
        if security_view:
            filter_parts.append("+security focus")
    if no_collapse:
        filter_parts.append("no grouping")

    filter_desc = ", ".join(filter_parts)

    console.print()
    console.print(
        Panel(
            f"[bold cyan]📊 RepliMap Graph Visualizer[/bold cyan]\n\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            + (f"VPC: [cyan]{vpc}[/]\n" if vpc else "")
            + f"Format: [cyan]{fmt.value}[/]\n"
            f"Filter: [cyan]{filter_desc}[/]\n"
            f"Output: [cyan]{output}[/]",
            border_style="cyan",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Configure filter based on options
    effective_show_sg_rules = show_sg_rules or security_view
    effective_show_routes = show_routes

    # Run visualization
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)

        try:
            visualizer = GraphVisualizer(
                session=session,
                region=effective_region,
                profile=profile,
            )

            result = visualizer.generate(
                vpc_id=vpc,
                output_format=fmt,
                output_path=output,
                show_all=show_all,
                show_sg_rules=effective_show_sg_rules,
                show_routes=effective_show_routes,
                no_collapse=no_collapse,
            )

            progress.update(task, completed=True)
        except Exception as e:
            progress.stop()
            console.print()
            console.print(
                Panel(
                    f"[red]Graph generation failed:[/]\n{e}",
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    # Output result
    console.print()
    if isinstance(result, Path):
        console.print(f"[green]✓ Graph generated:[/] {result.absolute()}")

        # Open in browser for HTML
        if open_graph and fmt == OutputFormat.HTML:
            console.print()
            console.print("[dim]Opening graph in browser...[/dim]")
            webbrowser.open(f"file://{result.absolute()}")
    else:
        # Content returned for stdout mode
        console.print(result)

    console.print()


def register(app: typer.Typer) -> None:
    """Register the graph command with the Typer app."""
    app.command(name="graph")(graph_command)
