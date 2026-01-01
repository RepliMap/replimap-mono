"""Snapshot command group for RepliMap CLI."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.table import Table

from replimap.cli.utils import console, get_aws_session, get_profile_region


def create_snapshot_app() -> typer.Typer:
    """Create and return the snapshot subcommand app."""
    snapshot_app = typer.Typer(
        help="Infrastructure snapshots for change tracking",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @snapshot_app.callback()
    def snapshot_callback(
        ctx: typer.Context,
        profile: str | None = typer.Option(
            None, "--profile", "-p", help="AWS profile name"
        ),
        region: str | None = typer.Option(
            None, "--region", "-r", help="AWS region"
        ),
    ) -> None:
        """
        Infrastructure snapshots for change tracking.

        Common options (--profile, --region) can be specified before the subcommand.

        Examples:
            replimap snapshot -p prod save -n "before-deploy"
            replimap snapshot -p prod list
            replimap snapshot -p prod diff --baseline v1 --current v2
        """
        ctx.ensure_object(dict)
        ctx.obj["profile"] = profile
        ctx.obj["region"] = region

    @snapshot_app.command("save")
    def snapshot_save(
        ctx: typer.Context,
        name: str = typer.Option(..., "--name", "-n", help="Snapshot name"),
        vpc: str | None = typer.Option(
            None, "--vpc", "-v", help="VPC ID to scope the snapshot (optional)"
        ),
        output: Path | None = typer.Option(
            None, "--output", "-o", help="Custom output file path"
        ),
        no_cache: bool = typer.Option(
            False, "--no-cache", help="Don't use cached credentials"
        ),
        refresh: bool = typer.Option(
            False, "--refresh", "-R", help="Force fresh AWS scan (ignore cached graph)"
        ),
    ) -> None:
        """Save an infrastructure snapshot."""
        from replimap.core import GraphEngine
        from replimap.core.cache_manager import get_or_load_graph, save_graph_to_cache
        from replimap.scanners.base import run_all_scanners
        from replimap.snapshot import InfraSnapshot, ResourceSnapshot, SnapshotStore

        # Get profile and region from context (set by callback)
        profile = ctx.obj.get("profile") if ctx.obj else None
        region = ctx.obj.get("region") if ctx.obj else None

        # Determine region (flag > profile > env > default)
        effective_region = region
        region_source = "flag" if region else None

        if not effective_region:
            profile_region = get_profile_region(profile)
            if profile_region:
                effective_region = profile_region
                region_source = f"profile '{profile or 'default'}'"
            else:
                effective_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
                region_source = "default"

        console.print()
        console.print(
            Panel(
                f"[bold blue]📸 Creating Infrastructure Snapshot[/bold blue]\n\n"
                f"Name: [cyan]{name}[/]\n"
                f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
                f"Profile: [cyan]{profile or 'default'}[/]"
                + (f"\nVPC: [cyan]{vpc}[/]" if vpc else ""),
                border_style="blue",
            )
        )

        session = get_aws_session(profile, effective_region, use_cache=not no_cache)

        # Try to load from cache first (global signal handler handles Ctrl-C)
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
                task = progress.add_task("Scanning infrastructure...", total=None)
                graph = GraphEngine()
                run_all_scanners(session, effective_region, graph)
                progress.update(task, completed=True)

            # Save to cache
            save_graph_to_cache(
                graph=graph,
                profile=profile or "default",
                region=effective_region,
                console=console,
                vpc=vpc,
            )

        if vpc:
            filtered_resources = []
            for resource in graph.get_all_resources():
                resource_vpc = resource.config.get("vpc_id") or resource.config.get(
                    "VpcId"
                )
                if (
                    resource_vpc == vpc
                    or resource.id == vpc
                    or vpc in resource.dependencies
                ):
                    filtered_resources.append(resource)
            resources = filtered_resources
        else:
            resources = graph.get_all_resources()

        console.print(f"[dim]Found {len(resources)} resources[/dim]")

        resource_snapshots = []
        for r in resources:
            rs = ResourceSnapshot(
                id=r.id,
                type=str(r.resource_type),
                arn=r.arn,
                name=r.original_name,
                region=effective_region,
                config=r.config,
                tags=r.tags,
            )
            resource_snapshots.append(rs)

        snapshot = InfraSnapshot(
            name=name,
            region=effective_region,
            vpc_id=vpc,
            profile=profile or "default",
            resources=resource_snapshots,
        )

        if output:
            snapshot.save(output)
            filepath = output
        else:
            store = SnapshotStore()
            filepath = store.save(snapshot)

        console.print()
        console.print(
            Panel(
                f"[bold]Snapshot Saved[/bold]\n\n"
                f"[green]✓ Name:[/] {snapshot.name}\n"
                f"[green]✓ Resources:[/] {snapshot.resource_count}\n"
                f"[green]✓ Created:[/] {snapshot.created_at[:19]}\n"
                f"[green]✓ Path:[/] {filepath}",
                title="📸 Snapshot Complete",
                border_style="green",
            )
        )

        by_type = snapshot.resource_types()
        if by_type:
            console.print()
            console.print("[bold]Resources by Type:[/bold]")
            for rtype, count in sorted(by_type.items(), key=lambda x: -x[1])[:10]:
                console.print(f"  {rtype}: {count}")
            if len(by_type) > 10:
                console.print(f"  [dim]... and {len(by_type) - 10} more types[/dim]")

    @snapshot_app.command("list")
    def snapshot_list(
        ctx: typer.Context,
    ) -> None:
        """List saved snapshots."""
        from replimap.snapshot import SnapshotStore

        # Get region filter from context
        region = ctx.obj.get("region") if ctx.obj else None

        store = SnapshotStore()
        snapshots = store.list(region=region)

        if not snapshots:
            console.print("[dim]No snapshots found[/dim]")
            return

        table = Table(title="Saved Snapshots")
        table.add_column("Name")
        table.add_column("Region")
        table.add_column("Resources", justify="right")
        table.add_column("Created")

        for snap in snapshots:
            table.add_row(
                snap["name"],
                snap.get("region", "-"),
                str(snap.get("resource_count", 0)),
                snap.get("created_at", "-")[:19],
            )

        console.print(table)

    @snapshot_app.command("show")
    def snapshot_show(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="Snapshot name or path"),
    ) -> None:
        """Show snapshot details."""
        from replimap.snapshot import SnapshotStore

        store = SnapshotStore()
        snapshot = store.load(name)

        if not snapshot:
            console.print(f"[red]Snapshot not found: {name}[/red]")
            raise typer.Exit(1)

        console.print()
        console.print(f"[bold]Snapshot: {snapshot.name}[/bold]")
        console.print()
        console.print(f"Created: {snapshot.created_at[:19]}")
        console.print(f"Region: {snapshot.region}")
        console.print(f"Profile: {snapshot.profile}")
        if snapshot.vpc_id:
            console.print(f"VPC: {snapshot.vpc_id}")
        console.print(f"Resources: {snapshot.resource_count}")
        console.print(f"Version: {snapshot.version}")

        by_type = snapshot.resource_types()
        if by_type:
            console.print()
            console.print("[bold]Resources by Type:[/bold]")
            for rtype, count in sorted(by_type.items(), key=lambda x: -x[1]):
                console.print(f"  {rtype}: {count}")

    @snapshot_app.command("diff")
    def snapshot_diff(
        ctx: typer.Context,
        baseline: str = typer.Option(
            ..., "--baseline", "-b", help="Baseline snapshot name or path"
        ),
        current: str | None = typer.Option(None, "--current", "-c"),
        output: Path | None = typer.Option(None, "--output", "-o"),
        output_format: str = typer.Option("console", "--format", "-f"),
        verbose: bool = typer.Option(False, "--verbose", "-V"),
        fail_on_change: bool = typer.Option(False, "--fail-on-change"),
        fail_on_critical: bool = typer.Option(False, "--fail-on-critical"),
        no_cache: bool = typer.Option(False, "--no-cache"),
    ) -> None:
        """Compare snapshots to find infrastructure changes."""
        from replimap.core import GraphEngine
        from replimap.scanners.base import run_all_scanners
        from replimap.snapshot import (
            InfraSnapshot,
            ResourceSnapshot,
            SnapshotDiffer,
            SnapshotReporter,
            SnapshotStore,
        )

        # Get profile and region from context
        profile = ctx.obj.get("profile") if ctx.obj else None
        region = ctx.obj.get("region") if ctx.obj else None

        store = SnapshotStore()
        baseline_snap = store.load(baseline)
        if not baseline_snap:
            console.print(f"[red]Baseline snapshot not found: {baseline}[/red]")
            raise typer.Exit(1)

        # Use baseline region if not specified
        if not region:
            region = baseline_snap.region

        console.print()
        console.print(
            Panel(
                f"[bold blue]📸 Comparing Infrastructure Snapshots[/bold blue]\n\n"
                f"Baseline: [cyan]{baseline_snap.name}[/] ({baseline_snap.created_at[:19]})\n"
                f"Region: [cyan]{region}[/]",
                border_style="blue",
            )
        )

        if current:
            current_snap = store.load(current)
            if not current_snap:
                console.print(f"[red]Current snapshot not found: {current}[/red]")
                raise typer.Exit(1)
            console.print(
                f"Current: [cyan]{current_snap.name}[/] ({current_snap.created_at[:19]})"
            )
        else:
            console.print()
            console.print("[dim]Scanning current infrastructure...[/dim]")

            session = get_aws_session(profile, region, use_cache=not no_cache)

            # Global signal handler handles Ctrl-C
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Scanning...", total=None)
                graph = GraphEngine()
                run_all_scanners(session, region, graph)
                progress.update(task, completed=True)

            if baseline_snap.vpc_id:
                filtered_resources = []
                for resource in graph.get_all_resources():
                    resource_vpc = resource.config.get("vpc_id") or resource.config.get(
                        "VpcId"
                    )
                    if (
                        resource_vpc == baseline_snap.vpc_id
                        or resource.id == baseline_snap.vpc_id
                        or baseline_snap.vpc_id in resource.dependencies
                    ):
                        filtered_resources.append(resource)
                resources = filtered_resources
            else:
                resources = graph.get_all_resources()

            resource_snapshots = [
                ResourceSnapshot(
                    id=r.id,
                    type=str(r.resource_type),
                    arn=r.arn,
                    name=r.original_name,
                    region=region,
                    config=r.config,
                    tags=r.tags,
                )
                for r in resources
            ]

            current_snap = InfraSnapshot(
                name="current",
                region=region,
                vpc_id=baseline_snap.vpc_id,
                resources=resource_snapshots,
            )

        console.print()
        differ = SnapshotDiffer()
        diff_result = differ.diff(baseline_snap, current_snap)

        reporter = SnapshotReporter()

        if output_format == "console":
            reporter.to_console(diff_result, verbose=verbose)
        elif output_format == "json":
            output_path = output or Path("snapshot_diff.json")
            reporter.to_json(diff_result, output_path)
        elif output_format in ("md", "markdown"):
            output_path = output or Path("snapshot_diff.md")
            reporter.to_markdown(diff_result, output_path)
        elif output_format == "html":
            output_path = output or Path("snapshot_diff.html")
            reporter.to_html(diff_result, output_path)
        else:
            reporter.to_console(diff_result, verbose=verbose)
            if output:
                reporter.to_json(diff_result, output)

        exit_code = 0

        if fail_on_change and diff_result.has_changes:
            console.print()
            console.print(
                f"[bold red]❌ CI/CD FAILED: {diff_result.total_changes} changes detected[/bold red]"
            )
            exit_code = 1

        if fail_on_critical and diff_result.has_critical_changes:
            console.print()
            console.print(
                f"[bold red]❌ CI/CD FAILED: {len(diff_result.critical_changes)} critical/high changes detected[/bold red]"
            )
            exit_code = 1

        if exit_code == 0 and (fail_on_change or fail_on_critical):
            console.print()
            console.print("[bold green]✓ CI/CD PASSED[/bold green]")

        console.print()

        if exit_code != 0:
            raise typer.Exit(exit_code)

    @snapshot_app.command("delete")
    def snapshot_delete(
        ctx: typer.Context,
        name: str = typer.Argument(..., help="Snapshot name to delete"),
        force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    ) -> None:
        """Delete a saved snapshot."""
        from replimap.snapshot import SnapshotStore

        store = SnapshotStore()

        if not store.exists(name):
            console.print(f"[red]Snapshot not found: {name}[/red]")
            raise typer.Exit(1)

        if not force:
            if not Confirm.ask(f"Delete snapshot '{name}'?"):
                console.print("[dim]Cancelled[/dim]")
                raise typer.Exit(0)

        if store.delete(name):
            console.print(f"[green]✓ Deleted snapshot: {name}[/green]")
        else:
            console.print(f"[red]Failed to delete snapshot: {name}[/red]")
            raise typer.Exit(1)

    return snapshot_app


def register(app: typer.Typer) -> None:
    """Register the snapshot command group with the Typer app."""
    snapshot_app = create_snapshot_app()
    app.add_typer(snapshot_app, name="snapshot")
