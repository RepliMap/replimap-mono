"""
RepliMap CLI Entry Point.

Usage:
    replimap scan --profile <aws-profile> --region <region> [--output graph.json]
    replimap clone --profile <source-profile> --region <region> --output-dir ./terraform
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Optional

import boto3
import typer
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from replimap import __version__
from replimap.core import GraphEngine
from replimap.scanners import (
    EC2Scanner,
    RDSScanner,
    S3Scanner,
    ScannerRegistry,
    VPCScanner,
)
from replimap.scanners.base import run_all_scanners
from replimap.renderers import TerraformRenderer
from replimap.transformers import create_default_pipeline


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("replimap")

# Create Typer app
app = typer.Typer(
    name="replimap",
    help="AWS Environment Replication Tool - Clone your production to staging in minutes",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"RepliMap v{__version__}")
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

        logger.info(
            f"Authenticated as {identity['Arn']} "
            f"(Account: {identity['Account']})"
        )

        return session

    except NoCredentialsError:
        typer.secho(
            "Error: No AWS credentials found. Configure credentials with "
            "'aws configure' or set environment variables.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    except ClientError as e:
        typer.secho(f"Error: AWS authentication failed: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)


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
    profile: Optional[str] = typer.Option(
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
    output: Optional[Path] = typer.Option(
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
    typer.secho(f"\n🔍 RepliMap Scanner v{__version__}", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"   Region: {region}", fg=typer.colors.CYAN)
    if profile:
        typer.secho(f"   Profile: {profile}", fg=typer.colors.CYAN)
    typer.echo()

    # Get AWS session
    session = get_aws_session(profile, region)

    # Initialize graph
    graph = GraphEngine()

    # Run all registered scanners
    typer.secho("📡 Scanning AWS resources...", fg=typer.colors.YELLOW)
    results = run_all_scanners(session, region, graph)

    # Report results
    typer.echo()
    typer.secho("━" * 50, fg=typer.colors.WHITE)

    failed = [name for name, err in results.items() if err is not None]
    succeeded = [name for name, err in results.items() if err is None]

    if succeeded:
        typer.secho(f"✅ Completed: {', '.join(succeeded)}", fg=typer.colors.GREEN)
    if failed:
        typer.secho(f"❌ Failed: {', '.join(failed)}", fg=typer.colors.RED)
        for name, err in results.items():
            if err:
                typer.secho(f"   - {name}: {err}", fg=typer.colors.RED)

    # Print statistics
    stats = graph.statistics()
    typer.echo()
    typer.secho("📊 Graph Statistics:", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"   Total Resources: {stats['total_resources']}")
    typer.echo(f"   Total Dependencies: {stats['total_dependencies']}")

    if stats["resources_by_type"]:
        typer.echo("   Resources by Type:")
        for rtype, count in sorted(stats["resources_by_type"].items()):
            typer.echo(f"      - {rtype}: {count}")

    if stats["has_cycles"]:
        typer.secho("   ⚠️  Warning: Dependency graph has cycles!", fg=typer.colors.YELLOW)

    # Save output if requested
    if output:
        graph.save(output)
        typer.secho(f"\n💾 Graph saved to {output}", fg=typer.colors.GREEN)

    typer.echo()


@app.command()
def clone(
    profile: Optional[str] = typer.Option(
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
    rename_pattern: Optional[str] = typer.Option(
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
    typer.secho(f"\n🚀 RepliMap Clone v{__version__}", fg=typer.colors.CYAN, bold=True)
    typer.secho(f"   Region: {region}", fg=typer.colors.CYAN)
    typer.secho(f"   Mode: {mode}", fg=typer.colors.CYAN)
    typer.secho(f"   Output: {output_dir}", fg=typer.colors.CYAN)
    typer.echo()

    if mode not in ("dry-run", "generate"):
        typer.secho(
            f"Error: Invalid mode '{mode}'. Use 'dry-run' or 'generate'.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Get AWS session
    session = get_aws_session(profile, region)

    # Initialize graph
    graph = GraphEngine()

    # Run all scanners
    typer.secho("📡 Scanning AWS resources...", fg=typer.colors.YELLOW)
    run_all_scanners(session, region, graph)

    stats = graph.statistics()
    typer.secho(
        f"   Found {stats['total_resources']} resources with "
        f"{stats['total_dependencies']} dependencies",
        fg=typer.colors.GREEN,
    )

    # Apply transformations
    typer.echo()
    typer.secho("🔄 Applying transformations...", fg=typer.colors.YELLOW)
    pipeline = create_default_pipeline(
        downsize=downsize,
        rename_pattern=rename_pattern,
        sanitize=True,
    )
    typer.secho(f"   Pipeline: {len(pipeline)} transformers", fg=typer.colors.CYAN)

    graph = pipeline.execute(graph)
    typer.secho("   Transformations complete", fg=typer.colors.GREEN)

    # Preview or generate
    renderer = TerraformRenderer()
    preview = renderer.preview(graph)

    typer.echo()
    typer.secho("📁 Output files:", fg=typer.colors.CYAN, bold=True)
    for filename, resources in sorted(preview.items()):
        typer.echo(f"   {filename}: {len(resources)} resources")

    if mode == "dry-run":
        typer.echo()
        typer.secho(
            "ℹ️  This is a dry-run. Use --mode generate to create files.",
            fg=typer.colors.YELLOW,
        )
    else:
        typer.echo()
        typer.secho("⚙️  Generating Terraform files...", fg=typer.colors.YELLOW)
        written = renderer.render(graph, output_dir)
        typer.secho(
            f"✅ Generated {len(written)} files in {output_dir}",
            fg=typer.colors.GREEN,
        )

    typer.echo()


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
        typer.secho(f"Error: File not found: {input_file}", fg=typer.colors.RED)
        raise typer.Exit(1)

    graph = GraphEngine.load(input_file)
    stats = graph.statistics()

    typer.secho(f"\n📊 Graph from {input_file}:", fg=typer.colors.CYAN, bold=True)
    typer.echo(f"   Total Resources: {stats['total_resources']}")
    typer.echo(f"   Total Dependencies: {stats['total_dependencies']}")

    if stats["resources_by_type"]:
        typer.echo("   Resources by Type:")
        for rtype, count in sorted(stats["resources_by_type"].items()):
            typer.echo(f"      - {rtype}: {count}")

    # Show resources
    typer.echo()
    typer.secho("📦 Resources:", fg=typer.colors.CYAN, bold=True)
    for resource in graph.topological_sort()[:20]:  # Limit output
        deps = graph.get_dependencies(resource.id)
        dep_str = f" → depends on {len(deps)} resources" if deps else ""
        typer.echo(f"   [{resource.resource_type}] {resource.id}{dep_str}")

    if stats["total_resources"] > 20:
        typer.echo(f"   ... and {stats['total_resources'] - 20} more")

    typer.echo()


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
