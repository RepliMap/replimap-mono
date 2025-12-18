"""
RepliMap CLI Entry Point.

Usage:
    replimap scan --profile <aws-profile> --region <region> [--output graph.json]
    replimap clone --profile <source-profile> --region <region> --output-dir ./terraform
"""

from __future__ import annotations

import logging
from pathlib import Path

import boto3
import typer
from botocore.exceptions import ClientError, NoCredentialsError
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from replimap import __version__
from replimap.core import GraphEngine
from replimap.renderers import TerraformRenderer
from replimap.scanners.base import run_all_scanners
from replimap.transformers import create_default_pipeline

# Initialize rich console
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger("replimap")

# Create Typer app
app = typer.Typer(
    name="replimap",
    help="AWS Environment Replication Tool - Clone your production to staging in minutes",
    add_completion=False,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]RepliMap[/] v{__version__}")
        raise typer.Exit()


def get_aws_session(profile: str | None, region: str) -> boto3.Session:
    """
    Create a boto3 session with the specified profile and region.

    Args:
        profile: AWS profile name (optional)
        region: AWS region

    Returns:
        Configured boto3 Session

    Raises:
        typer.Exit: If credentials are invalid
    """
    try:
        session = boto3.Session(profile_name=profile, region_name=region)

        # Verify credentials work
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        console.print(
            f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
            f"(Account: {identity['Account']})"
        )

        return session

    except NoCredentialsError:
        console.print(
            Panel(
                "[red]No AWS credentials found.[/]\n\n"
                "Configure credentials with 'aws configure' or set environment variables.",
                title="Authentication Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except ClientError as e:
        console.print(
            Panel(
                f"[red]AWS authentication failed:[/]\n{e}",
                title="Authentication Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


def print_graph_stats(graph: GraphEngine) -> None:
    """Print graph statistics in a rich table."""
    stats = graph.statistics()

    table = Table(title="Graph Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Resources", str(stats["total_resources"]))
    table.add_row("Total Dependencies", str(stats["total_dependencies"]))

    if stats["resources_by_type"]:
        table.add_section()
        for rtype, count in sorted(stats["resources_by_type"].items()):
            table.add_row(f"  {rtype}", str(count))

    console.print(table)

    if stats["has_cycles"]:
        console.print(
            "[yellow]Warning:[/] Dependency graph contains cycles!",
            style="bold yellow",
        )


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging",
    ),
) -> None:
    """RepliMap - AWS Environment Replication Tool."""
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


@app.command()
def scan(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name",
    ),
    region: str = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output path for graph JSON (optional)",
    ),
) -> None:
    """
    Scan AWS resources and build dependency graph.

    Examples:
        replimap scan --profile prod --region us-west-2
        replimap scan --profile prod --region us-east-1 --output graph.json
    """
    console.print(
        Panel(
            f"[bold]RepliMap Scanner[/] v{__version__}\n"
            f"Region: [cyan]{region}[/]"
            + (f"\nProfile: [cyan]{profile}[/]" if profile else ""),
            title="Configuration",
            border_style="cyan",
        )
    )

    # Get AWS session
    session = get_aws_session(profile, region)

    # Initialize graph
    graph = GraphEngine()

    # Run all registered scanners with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)
        results = run_all_scanners(session, region, graph)
        progress.update(task, completed=True)

    # Report results
    console.print()

    failed = [name for name, err in results.items() if err is not None]
    succeeded = [name for name, err in results.items() if err is None]

    if succeeded:
        console.print(f"[green]Completed:[/] {', '.join(succeeded)}")
    if failed:
        console.print(f"[red]Failed:[/] {', '.join(failed)}")
        for name, err in results.items():
            if err:
                console.print(f"  [red]-[/] {name}: {err}")

    # Print statistics
    console.print()
    print_graph_stats(graph)

    # Save output if requested
    if output:
        graph.save(output)
        console.print(f"\n[green]Graph saved to[/] {output}")

    console.print()


@app.command()
def clone(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS source profile name",
    ),
    region: str = typer.Option(
        "us-east-1",
        "--region",
        "-r",
        help="AWS region to scan",
    ),
    output_dir: Path = typer.Option(
        Path("./terraform"),
        "--output-dir",
        "-o",
        help="Output directory for Terraform files",
    ),
    mode: str = typer.Option(
        "dry-run",
        "--mode",
        "-m",
        help="Mode: 'dry-run' (preview) or 'generate' (create files)",
    ),
    downsize: bool = typer.Option(
        True,
        "--downsize/--no-downsize",
        help="Enable instance downsizing for cost savings",
    ),
    rename_pattern: str | None = typer.Option(
        None,
        "--rename-pattern",
        help="Renaming pattern, e.g., 'prod:stage'",
    ),
) -> None:
    """
    Clone AWS environment to Terraform code.

    Examples:
        replimap clone --profile prod --region us-west-2 --mode dry-run
        replimap clone --profile prod --region us-west-2 --output-dir ./staging-tf --mode generate
    """
    console.print(
        Panel(
            f"[bold]RepliMap Clone[/] v{__version__}\n"
            f"Region: [cyan]{region}[/]\n"
            f"Mode: [cyan]{mode}[/]\n"
            f"Output: [cyan]{output_dir}[/]\n"
            f"Downsize: [cyan]{downsize}[/]"
            + (f"\nRename: [cyan]{rename_pattern}[/]" if rename_pattern else ""),
            title="Configuration",
            border_style="cyan",
        )
    )

    if mode not in ("dry-run", "generate"):
        console.print(
            f"[red]Error:[/] Invalid mode '{mode}'. Use 'dry-run' or 'generate'."
        )
        raise typer.Exit(1)

    # Get AWS session
    session = get_aws_session(profile, region)

    # Initialize graph
    graph = GraphEngine()

    # Run all scanners with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)
        run_all_scanners(session, region, graph)
        progress.update(task, completed=True)

    stats = graph.statistics()
    console.print(
        f"[green]Found[/] {stats['total_resources']} resources "
        f"with {stats['total_dependencies']} dependencies"
    )

    # Apply transformations
    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Applying transformations...", total=None)
        pipeline = create_default_pipeline(
            downsize=downsize,
            rename_pattern=rename_pattern,
            sanitize=True,
        )
        graph = pipeline.execute(graph)
        progress.update(task, completed=True)

    console.print(f"[green]Applied[/] {len(pipeline)} transformers")

    # Preview or generate
    renderer = TerraformRenderer()
    preview = renderer.preview(graph)

    # Show output files table
    console.print()
    table = Table(title="Output Files", show_header=True, header_style="bold cyan")
    table.add_column("File", style="dim")
    table.add_column("Resources", justify="right")

    for filename, resources in sorted(preview.items()):
        table.add_row(filename, str(len(resources)))

    console.print(table)

    if mode == "dry-run":
        console.print()
        console.print(
            Panel(
                "[yellow]This is a dry-run.[/]\n"
                "Use [bold]--mode generate[/] to create files.",
                border_style="yellow",
            )
        )
    else:
        console.print()
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating Terraform files...", total=None)
            written = renderer.render(graph, output_dir)
            progress.update(task, completed=True)

        console.print(
            Panel(
                f"[green]Generated {len(written)} files[/] in [bold]{output_dir}[/]",
                border_style="green",
            )
        )

    console.print()


@app.command()
def load(
    input_file: Path = typer.Argument(
        ...,
        help="Path to graph JSON file",
    ),
) -> None:
    """
    Load and display a saved graph.

    Examples:
        replimap load graph.json
    """
    if not input_file.exists():
        console.print(f"[red]Error:[/] File not found: {input_file}")
        raise typer.Exit(1)

    graph = GraphEngine.load(input_file)

    console.print(
        Panel(
            f"Loaded graph from [bold]{input_file}[/]",
            title="Graph Loaded",
            border_style="green",
        )
    )

    # Print statistics
    print_graph_stats(graph)

    # Show resources table
    console.print()
    table = Table(
        title="Resources (first 20)", show_header=True, header_style="bold cyan"
    )
    table.add_column("Type", style="dim")
    table.add_column("ID")
    table.add_column("Dependencies", justify="right")

    for resource in graph.topological_sort()[:20]:
        deps = graph.get_dependencies(resource.id)
        table.add_row(
            str(resource.resource_type),
            resource.id,
            str(len(deps)) if deps else "-",
        )

    console.print(table)

    stats = graph.statistics()
    if stats["total_resources"] > 20:
        console.print(f"[dim]... and {stats['total_resources'] - 20} more[/]")

    console.print()


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
