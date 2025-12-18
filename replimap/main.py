"""
RepliMap CLI Entry Point.

Usage:
    replimap scan --profile <aws-profile> --region <region> [--output graph.json]
    replimap clone --profile <source-profile> --region <region> --output-dir ./terraform
    replimap license activate <key>
    replimap license status
"""

from __future__ import annotations

import logging
import time
import uuid
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
from replimap.licensing import (
    Feature,
    LicenseStatus,
    LicenseValidationError,
)
from replimap.licensing.manager import get_license_manager
from replimap.licensing.tracker import get_usage_tracker
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
    # Check license and quotas
    manager = get_license_manager()
    tracker = get_usage_tracker()
    features = manager.current_features

    # Check scan quota
    if features.max_scans_per_month is not None:
        scans_this_month = tracker.get_scans_this_month()
        if scans_this_month >= features.max_scans_per_month:
            console.print(
                Panel(
                    f"[red]Scan limit reached![/]\n\n"
                    f"You have used {scans_this_month}/{features.max_scans_per_month} scans this month.\n"
                    f"Upgrade your plan for unlimited scans: [bold]https://replimap.io/upgrade[/]",
                    title="Quota Exceeded",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

    plan_badge = f"[dim]({manager.current_plan.value})[/]"
    console.print(
        Panel(
            f"[bold]RepliMap Scanner[/] v{__version__} {plan_badge}\n"
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
    scan_start = time.time()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)
        results = run_all_scanners(session, region, graph)
        progress.update(task, completed=True)
    scan_duration = time.time() - scan_start

    # Check resource limit
    stats = graph.statistics()
    resource_count = stats["total_resources"]

    if features.max_resources_per_scan is not None:
        if resource_count > features.max_resources_per_scan:
            console.print()
            console.print(
                Panel(
                    f"[yellow]Resource limit reached![/]\n\n"
                    f"Found {resource_count} resources, but your plan allows "
                    f"{features.max_resources_per_scan} per scan.\n"
                    f"Results are truncated. Upgrade for unlimited resources: "
                    f"[bold]https://replimap.io/upgrade[/]",
                    title="Limit Warning",
                    border_style="yellow",
                )
            )

    # Record usage
    tracker.record_scan(
        scan_id=str(uuid.uuid4()),
        region=region,
        resource_count=resource_count,
        resource_types=stats.get("resources_by_type", {}),
        duration_seconds=scan_duration,
        profile=profile,
        success=True,
    )

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


# License subcommand group
license_app = typer.Typer(
    name="license",
    help="License management commands",
    rich_markup_mode="rich",
)
app.add_typer(license_app, name="license")


@license_app.command("activate")
def license_activate(
    license_key: str = typer.Argument(
        ...,
        help="License key (format: XXXX-XXXX-XXXX-XXXX)",
    ),
) -> None:
    """
    Activate a license key.

    Examples:
        replimap license activate SOLO-XXXX-XXXX-XXXX
    """
    manager = get_license_manager()

    try:
        license_obj = manager.activate(license_key)
        console.print(
            Panel(
                f"[green]License activated successfully![/]\n\n"
                f"Plan: [bold cyan]{license_obj.plan.value.upper()}[/]\n"
                f"Email: {license_obj.email}\n"
                f"Expires: {license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}",
                title="License Activated",
                border_style="green",
            )
        )
    except LicenseValidationError as e:
        console.print(
            Panel(
                f"[red]License activation failed:[/]\n{e}",
                title="Activation Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@license_app.command("status")
def license_status() -> None:
    """
    Show current license status.

    Examples:
        replimap license status
    """
    manager = get_license_manager()
    status, message = manager.validate()
    license_obj = manager.current_license
    features = manager.current_features

    # Status panel
    if status == LicenseStatus.VALID:
        status_color = "green"
        status_icon = "[green]Valid[/]"
    elif status == LicenseStatus.EXPIRED:
        status_color = "red"
        status_icon = "[red]Expired[/]"
    else:
        status_color = "yellow"
        status_icon = f"[yellow]{status.value}[/]"

    plan_name = manager.current_plan.value.upper()
    if license_obj:
        info = (
            f"Plan: [bold cyan]{plan_name}[/]\n"
            f"Status: {status_icon}\n"
            f"Email: {license_obj.email}\n"
            f"Expires: {license_obj.expires_at.strftime('%Y-%m-%d') if license_obj.expires_at else 'Never'}"
        )
    else:
        info = (
            f"Plan: [bold cyan]{plan_name}[/]\n"
            f"Status: {status_icon}\n"
            f"[dim]No license key activated. Using free tier.[/]"
        )

    console.print(
        Panel(
            info,
            title="License Status",
            border_style=status_color,
        )
    )

    # Features table
    console.print()
    table = Table(title="Plan Features", show_header=True, header_style="bold cyan")
    table.add_column("Feature", style="dim")
    table.add_column("Available", justify="center")

    feature_display = [
        (Feature.UNLIMITED_RESOURCES, "Unlimited Resources"),
        (Feature.ASYNC_SCANNING, "Async Scanning"),
        (Feature.MULTI_ACCOUNT, "Multi-Account Support"),
        (Feature.CUSTOM_TEMPLATES, "Custom Templates"),
        (Feature.WEB_DASHBOARD, "Web Dashboard"),
        (Feature.COLLABORATION, "Team Collaboration"),
        (Feature.SSO, "SSO Integration"),
        (Feature.AUDIT_LOGS, "Audit Logs"),
    ]

    for feature, display_name in feature_display:
        available = features.has_feature(feature)
        icon = "[green]Yes[/]" if available else "[dim]No[/]"
        table.add_row(display_name, icon)

    console.print(table)

    # Limits
    console.print()
    limits_table = Table(
        title="Usage Limits", show_header=True, header_style="bold cyan"
    )
    limits_table.add_column("Limit", style="dim")
    limits_table.add_column("Value", justify="right")

    limits_table.add_row(
        "Resources per Scan",
        str(features.max_resources_per_scan)
        if features.max_resources_per_scan
        else "Unlimited",
    )
    limits_table.add_row(
        "Scans per Month",
        str(features.max_scans_per_month)
        if features.max_scans_per_month
        else "Unlimited",
    )
    limits_table.add_row(
        "AWS Accounts",
        str(features.max_aws_accounts) if features.max_aws_accounts else "Unlimited",
    )

    console.print(limits_table)

    # Usage stats
    tracker = get_usage_tracker()
    stats = tracker.get_stats()

    if stats.total_scans > 0:
        console.print()
        usage_table = Table(
            title="Usage This Month", show_header=True, header_style="bold cyan"
        )
        usage_table.add_column("Metric", style="dim")
        usage_table.add_column("Value", justify="right")

        usage_table.add_row("Scans", str(stats.scans_this_month))
        usage_table.add_row("Resources Scanned", str(stats.resources_this_month))
        usage_table.add_row("Regions Used", str(len(stats.unique_regions)))

        console.print(usage_table)

    console.print()


@license_app.command("deactivate")
def license_deactivate(
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Deactivate the current license.

    Examples:
        replimap license deactivate --yes
    """
    manager = get_license_manager()

    if manager.current_license is None:
        console.print("[yellow]No license is currently active.[/]")
        raise typer.Exit(0)

    if not confirm:
        confirm = typer.confirm("Are you sure you want to deactivate your license?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    manager.deactivate()
    console.print("[green]License deactivated.[/] You are now on the free tier.")


@license_app.command("usage")
def license_usage() -> None:
    """
    Show detailed usage statistics.

    Examples:
        replimap license usage
    """
    tracker = get_usage_tracker()
    stats = tracker.get_stats()

    console.print(
        Panel(
            f"Total Scans: [bold]{stats.total_scans}[/]\n"
            f"Total Resources Scanned: [bold]{stats.total_resources_scanned}[/]\n"
            f"Unique Regions: [bold]{len(stats.unique_regions)}[/]\n"
            f"Last Scan: [bold]{stats.last_scan.strftime('%Y-%m-%d %H:%M') if stats.last_scan else 'Never'}[/]",
            title="Usage Overview",
            border_style="cyan",
        )
    )

    # Recent scans
    recent = tracker.get_recent_scans(10)
    if recent:
        console.print()
        table = Table(title="Recent Scans", show_header=True, header_style="bold cyan")
        table.add_column("Date", style="dim")
        table.add_column("Region")
        table.add_column("Resources", justify="right")
        table.add_column("Duration", justify="right")

        for scan in recent:
            table.add_row(
                scan.timestamp.strftime("%Y-%m-%d %H:%M"),
                scan.region,
                str(scan.resource_count),
                f"{scan.duration_seconds:.1f}s",
            )

        console.print(table)

    # Resource type breakdown
    if stats.resource_type_counts:
        console.print()
        type_table = Table(
            title="Resources by Type", show_header=True, header_style="bold cyan"
        )
        type_table.add_column("Resource Type", style="dim")
        type_table.add_column("Count", justify="right")

        for rtype, count in sorted(
            stats.resource_type_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            type_table.add_row(rtype, str(count))

        console.print(type_table)

    console.print()


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
