"""Validate command for topology constraints."""

from __future__ import annotations

import os
from pathlib import Path

import boto3
import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from replimap.cli.utils import console, get_profile_region
from replimap.core import GraphEngine
from replimap.scanners.base import run_all_scanners


def validate_command(
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
        help="AWS region to validate",
    ),
    config: Path = typer.Option(
        Path("constraints.yaml"),
        "--config",
        "-c",
        help="Path to constraints YAML file",
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output file for validation report (JSON or Markdown)",
    ),
    fail_on: str = typer.Option(
        "critical",
        "--fail-on",
        help="Fail on severity level: critical, high, medium, low, info",
    ),
    generate_defaults: bool = typer.Option(
        False,
        "--generate-defaults",
        help="Generate default constraints file",
    ),
    refresh: bool = typer.Option(
        False,
        "--refresh",
        "-R",
        help="Force fresh AWS scan (ignore cached graph)",
    ),
) -> None:
    """
    Validate infrastructure against topology constraints.

    Checks your AWS infrastructure against policy rules defined in a
    constraints YAML file. Perfect for enforcing security policies,
    tagging standards, and architectural patterns.

    Examples:
        # Generate default constraints file
        replimap validate --generate-defaults

        # Validate with default constraints
        replimap validate -p prod -r us-east-1

        # Use custom constraints file
        replimap validate -p prod -r us-east-1 -c my-constraints.yaml

        # Fail on high severity violations (for CI/CD)
        replimap validate -p prod -r us-east-1 --fail-on high

        # Export validation report
        replimap validate -p prod -r us-east-1 -o report.json
    """
    from replimap.core.topology_constraints import (
        ConstraintSeverity,
        TopologyConstraint,
        TopologyValidator,
    )

    # Handle generate-defaults
    if generate_defaults:
        default_constraints = """# RepliMap Topology Constraints
# See: https://docs.replimap.io/topology-constraints

version: "1.0"

constraints:
  # Require Environment tag on all resources
  - name: require-environment-tag
    constraint_type: require_tag
    severity: high
    description: All resources must have Environment tag
    required_tags:
      Environment: null  # Any value accepted

  # Require Owner tag
  - name: require-owner-tag
    constraint_type: require_tag
    severity: medium
    description: All resources should have Owner tag
    required_tags:
      Owner: null

  # Require encryption on RDS instances
  - name: require-rds-encryption
    constraint_type: require_encryption
    severity: critical
    description: All RDS instances must be encrypted
    source_type: aws_db_instance

  # Require encryption on S3 buckets
  - name: require-s3-encryption
    constraint_type: require_encryption
    severity: critical
    description: All S3 buckets must have encryption enabled
    source_type: aws_s3_bucket

  # Prohibit public RDS instances
  - name: prohibit-public-rds
    constraint_type: prohibit_public_access
    severity: critical
    description: RDS instances must not be publicly accessible
    source_type: aws_db_instance
"""
        config.write_text(default_constraints)
        console.print(f"[green]✓ Generated default constraints: {config}[/]")
        raise typer.Exit(0)

    # Check constraints file exists
    if not config.exists():
        console.print(
            f"[red]Constraints file not found: {config}[/]\n"
            "Run with --generate-defaults to create one:\n"
            "  replimap validate --generate-defaults"
        )
        raise typer.Exit(1)

    # Parse fail-on severity
    severity_map = {
        "critical": ConstraintSeverity.CRITICAL,
        "high": ConstraintSeverity.HIGH,
        "medium": ConstraintSeverity.MEDIUM,
        "low": ConstraintSeverity.LOW,
        "info": ConstraintSeverity.INFO,
    }
    fail_severity = severity_map.get(fail_on.lower(), ConstraintSeverity.CRITICAL)

    # Load constraints
    import yaml

    with open(config) as f:
        config_data = yaml.safe_load(f)

    constraints = []
    for c in config_data.get("constraints", []):
        constraints.append(
            TopologyConstraint(
                name=c["name"],
                constraint_type=c["constraint_type"],
                severity=ConstraintSeverity(c.get("severity", "medium")),
                description=c.get("description", ""),
                source_type=c.get("source_type"),
                target_type=c.get("target_type"),
                required_tags=c.get("required_tags", {}),
                config=c.get("config", {}),
            )
        )

    if not constraints:
        console.print("[yellow]No constraints defined in config file[/]")
        raise typer.Exit(0)

    console.print(f"[dim]Loaded {len(constraints)} constraints from {config}[/]\n")

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

    console.print(f"[dim]Region: {effective_region} (from {region_source})[/]\n")

    # Try to load from cache first
    from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache

    try:
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

                session = boto3.Session(profile_name=effective_profile)
                graph = GraphEngine()
                run_all_scanners(session, graph, effective_region)
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=effective_profile,
                region=effective_region,
                console=console,
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        raise typer.Exit(130)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)

    # Validate
    try:
        validator = TopologyValidator(constraints)
        result = validator.validate(graph)
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)

    # Display results
    console.print("[bold]Validation Results[/bold]\n")
    console.print(f"Region: {effective_region}")
    console.print(f"Resources: {len(graph.nodes)}")
    console.print(f"Constraints: {len(constraints)}")
    console.print()

    if result.is_valid:
        console.print("[green]✓ All constraints passed![/green]")
    else:
        # Group by severity
        by_severity: dict[str, list] = {}
        for v in result.violations:
            sev = v.severity.value
            if sev not in by_severity:
                by_severity[sev] = []
            by_severity[sev].append(v)

        console.print(f"[red]✗ Found {len(result.violations)} violations[/red]\n")

        for severity in ["critical", "high", "medium", "low", "info"]:
            if severity in by_severity:
                console.print(
                    f"[bold]{severity.upper()}[/bold] ({len(by_severity[severity])})"
                )
                for v in by_severity[severity][:5]:  # Show first 5
                    console.print(f"  • {v.constraint_name}: {v.resource_id}")
                    if v.message:
                        console.print(f"    [dim]{v.message}[/dim]")
                if len(by_severity[severity]) > 5:
                    console.print(f"  ... and {len(by_severity[severity]) - 5} more")
                console.print()

    # Export if requested
    if output:
        if output.suffix == ".json":
            import json as json_module

            with open(output, "w") as f:
                json_module.dump(result.to_dict(), f, indent=2)
            console.print(f"\n[green]✓ Saved report: {output}[/]")
        else:
            # Markdown
            with open(output, "w") as f:
                f.write("# Topology Validation Report\n\n")
                f.write(f"- Region: {effective_region}\n")
                f.write(f"- Resources: {len(graph.nodes)}\n")
                f.write(f"- Valid: {'Yes' if result.is_valid else 'No'}\n")
                f.write(f"- Violations: {len(result.violations)}\n\n")
                for v in result.violations:
                    f.write(
                        f"- **{v.constraint_name}** ({v.severity.value}): {v.resource_id}\n"
                    )
            console.print(f"\n[green]✓ Saved report: {output}[/]")

    # Exit code based on severity
    if not result.is_valid:
        max_severity = max(v.severity for v in result.violations)
        if max_severity.value in ["critical", "high"] and fail_severity in [
            ConstraintSeverity.CRITICAL,
            ConstraintSeverity.HIGH,
        ]:
            raise typer.Exit(1 if max_severity == ConstraintSeverity.HIGH else 2)


def register(app: typer.Typer) -> None:
    """Register the validate command with the Typer app."""
    app.command(name="validate")(validate_command)
