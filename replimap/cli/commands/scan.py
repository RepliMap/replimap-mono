"""
Scan command - AWS resource discovery and dependency graph building.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import typer
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt

from replimap import __version__
from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_aws_session,
    get_profile_region,
    logger,
    print_graph_stats,
    print_scan_summary,
)
from replimap.core import (
    GraphEngine,
    ScanCache,
    ScanFilter,
    SelectionStrategy,
    apply_filter_to_graph,
    apply_selection,
    build_subgraph_from_selection,
    update_cache_from_graph,
)
from replimap.licensing import Feature, check_scan_allowed, get_scans_remaining
from replimap.licensing.manager import get_license_manager
from replimap.licensing.tracker import get_usage_tracker
from replimap.scanners.base import run_all_scanners


def register(app: typer.Typer) -> None:
    """Register the scan command with the app."""

    @app.command()
    def scan(
        profile: str | None = typer.Option(
            None,
            "--profile",
            "-p",
            help="AWS profile name (uses 'default' if not specified)",
        ),
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="AWS region to scan (uses profile's region or us-east-1)",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output path for graph JSON (optional)",
        ),
        interactive: bool = typer.Option(
            False,
            "--interactive",
            "-i",
            help="Interactive mode - prompt for missing options",
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Don't use cached credentials (re-authenticate)",
        ),
        # New graph-based selection options
        scope: str | None = typer.Option(
            None,
            "--scope",
            "-s",
            help="Selection scope: vpc:<id>, vpc-name:<pattern>, or VPC ID directly",
        ),
        entry: str | None = typer.Option(
            None,
            "--entry",
            "-e",
            help="Entry point: tag:Key=Value, <type>:<name>, or resource ID",
        ),
        config: Path | None = typer.Option(
            None,
            "--config",
            "-c",
            help="Path to YAML selection config file",
        ),
        # Legacy filter options (still supported for backwards compatibility)
        vpc: str | None = typer.Option(
            None,
            "--vpc",
            help="[Legacy] Filter by VPC ID(s), comma-separated",
        ),
        vpc_name: str | None = typer.Option(
            None,
            "--vpc-name",
            help="[Legacy] Filter by VPC name pattern (supports wildcards)",
        ),
        types: str | None = typer.Option(
            None,
            "--types",
            "-t",
            help="[Legacy] Filter by resource types, comma-separated",
        ),
        tag: list[str] | None = typer.Option(
            None,
            "--tag",
            help="Select by tag (Key=Value), can be repeated",
        ),
        exclude_types: str | None = typer.Option(
            None,
            "--exclude-types",
            help="Exclude resource types, comma-separated",
        ),
        exclude_tag: list[str] | None = typer.Option(
            None,
            "--exclude-tag",
            help="Exclude by tag (Key=Value), can be repeated",
        ),
        exclude_patterns: str | None = typer.Option(
            None,
            "--exclude-patterns",
            help="Exclude by name patterns, comma-separated (supports wildcards)",
        ),
        # Scan cache options
        use_scan_cache: bool = typer.Option(
            False,
            "--cache",
            help="Use scan result cache for faster incremental scans",
        ),
        refresh_cache: bool = typer.Option(
            False,
            "--refresh-cache",
            help="Force refresh of scan cache (re-scan all resources)",
        ),
        # Trust Center auditing (P1-9)
        trust_center: bool = typer.Option(
            False,
            "--trust-center",
            "--audit",
            help="Enable Trust Center API auditing for compliance",
        ),
        # Incremental scanning (P3-1)
        incremental: bool = typer.Option(
            False,
            "--incremental",
            help="Use incremental scanning (only detect changes since last scan)",
        ),
    ) -> None:
        """
        Scan AWS resources and build dependency graph.

        The region is determined in this order:
        1. --region flag (if provided)
        2. Profile's configured region (from ~/.aws/config)
        3. AWS_DEFAULT_REGION environment variable
        4. us-east-1 (fallback)

        Examples:
            replimap scan --profile prod
            replimap scan --profile prod --region us-west-2
            replimap scan -i  # Interactive mode
            replimap scan --profile prod --output graph.json

        Selection Examples (Graph-Based - Recommended):
            replimap scan --profile prod --scope vpc:vpc-12345678
            replimap scan --profile prod --scope vpc-name:Production*
            replimap scan --profile prod --entry alb:my-app-alb
            replimap scan --profile prod --entry tag:Application=MyApp
            replimap scan --profile prod --tag Environment=Production

        Filter Examples (Legacy, still supported):
            replimap scan --profile prod --vpc vpc-12345678
            replimap scan --profile prod --types vpc,subnet,ec2,rds
            replimap scan --profile prod --exclude-types sns,sqs

        Advanced Examples:
            replimap scan --profile prod --scope vpc:vpc-123 --exclude-patterns "test-*"
            replimap scan --profile prod --config selection.yaml

        Cache Examples:
            replimap scan --profile prod --cache  # Use cached results
            replimap scan --profile prod --cache --refresh-cache  # Force refresh

        Trust Center Examples (P1-9):
            replimap scan --profile prod --trust-center  # Enable API auditing
            replimap trust-center report  # Generate compliance report

        Incremental Scanning Examples (P3-1):
            replimap scan --profile prod  # First scan (full)
            replimap scan --profile prod --incremental  # Subsequent scans (fast)
        """
        # Interactive mode - prompt for missing options
        if interactive:
            if not profile:
                available = get_available_profiles()
                console.print("\n[bold]Available AWS Profiles:[/]")
                for i, p in enumerate(available, 1):
                    console.print(f"  {i}. {p}")
                console.print()
                profile = Prompt.ask(
                    "Select profile",
                    default="default",
                    choices=available,
                )

        # Determine region: flag > profile config > env var > default
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

        if interactive and not region:
            console.print(
                f"\n[dim]Detected region: {effective_region} (from {region_source})[/]"
            )
            if not Confirm.ask("Use this region?", default=True):
                effective_region = Prompt.ask("Enter region", default=effective_region)
                region_source = "user input"

        # Check license and quotas
        manager = get_license_manager()
        tracker = get_usage_tracker()
        features = manager.current_features

        # Check scan frequency limit (NOT resource count - resources are unlimited!)
        gate_result = check_scan_allowed()
        if not gate_result.allowed:
            console.print(gate_result.prompt)
            raise typer.Exit(1)

        # Show plan badge with dev mode indicator
        if manager.is_dev_mode:
            plan_badge = "[yellow](dev mode)[/]"
        else:
            plan_badge = f"[dim]({manager.current_plan.value})[/]"

        console.print(
            Panel(
                f"[bold]RepliMap Scanner[/] v{__version__} {plan_badge}\n"
                f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]"
                + (
                    f"\nProfile: [cyan]{profile}[/]"
                    if profile
                    else "\nProfile: [cyan]default[/]"
                ),
                title="Configuration",
                border_style="cyan",
            )
        )

        # Get AWS session
        session = get_aws_session(profile, effective_region, use_cache=not no_cache)

        # Get account ID for cache key
        account_id = "unknown"
        if use_scan_cache:
            try:
                sts = session.client("sts")
                account_id = sts.get_caller_identity()["Account"]
            except Exception as e:
                logger.debug(f"Could not get AWS account ID for cache key: {e}")

        # Initialize graph
        graph = GraphEngine()

        # Enable Trust Center auditing if requested (P1-9)
        tc_session_id = None
        if trust_center:
            from replimap.audit import TrustCenter

            tc = TrustCenter.get_instance()
            tc.enable(session)
            tc_session_id = tc.start_session(f"scan_{effective_region}")
            console.print("[dim]Trust Center API auditing enabled[/]")

        # Handle incremental scanning (P3-1)
        if incremental:
            from replimap.scanners.incremental import IncrementalScanner, ScanStateStore

            console.print("[dim]Using incremental scanning mode...[/]")
            state_store = ScanStateStore()
            inc_scanner = IncrementalScanner(session, effective_region, state_store)

            # Detect changes
            changes = inc_scanner.detect_changes()
            if changes:
                created = sum(1 for c in changes if c.change_type.value == "created")
                modified = sum(1 for c in changes if c.change_type.value == "modified")
                deleted = sum(1 for c in changes if c.change_type.value == "deleted")
                console.print(
                    f"[dim]Incremental scan: {created} created, {modified} modified, "
                    f"{deleted} deleted, {len(changes) - created - modified - deleted} unchanged[/]"
                )
            else:
                console.print(
                    "[dim]No previous scan state found - performing full scan[/]"
                )

        # Load scan cache if enabled
        scan_cache: ScanCache | None = None
        cached_count = 0

        if use_scan_cache and not refresh_cache:
            scan_cache = ScanCache.load(
                account_id=account_id,
                region=effective_region,
            )
            stats = scan_cache.get_stats()
            cached_count = stats["total_resources"]
            if cached_count > 0:
                console.print(f"[dim]Loaded {cached_count} resources from cache[/]")
                # Populate graph from cache
                from replimap.core import populate_graph_from_cache

                populate_graph_from_cache(scan_cache, graph)

        # Run all registered scanners with progress
        # Use parallel scanning if license allows (ASYNC_SCANNING feature)
        use_parallel = features.has_feature(Feature.ASYNC_SCANNING)
        scan_mode = "parallel" if use_parallel else "sequential"
        scan_start = time.time()

        # If using cache and we have cached data, show that we're doing incremental scan
        if cached_count > 0:
            console.print(
                "[dim]Performing incremental scan for updated resources...[/]"
            )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"Scanning AWS resources ({scan_mode})...", total=None
            )
            results = run_all_scanners(
                session, effective_region, graph, parallel=use_parallel
            )
            progress.update(task, completed=True)
        scan_duration = time.time() - scan_start

        # Print scan summary with resource counts
        print_scan_summary(graph, scan_duration)

        # Update scan cache with new results
        if use_scan_cache:
            if scan_cache is None:
                scan_cache = ScanCache(
                    account_id=account_id,
                    region=effective_region,
                )
            update_cache_from_graph(scan_cache, graph)
            cache_path = scan_cache.save()
            console.print(f"[dim]Scan cache saved to {cache_path}[/]")

        # Apply selection or filters
        # Check if new graph-based selection is being used
        use_new_selection = scope or entry or config

        if use_new_selection:
            # Load config from YAML if provided
            if config and config.exists():
                import yaml

                with open(config) as f:
                    config_data = yaml.safe_load(f)
                selection_strategy = SelectionStrategy.from_dict(
                    config_data.get("selection", {})
                )
            else:
                # Build strategy from CLI args
                selection_strategy = SelectionStrategy.from_cli_args(
                    scope=scope,
                    entry=entry,
                    tag=tag,
                    exclude_types=exclude_types,
                    exclude_patterns=exclude_patterns,
                )

            if not selection_strategy.is_empty():
                console.print(
                    f"\n[dim]Applying selection: {selection_strategy.describe()}[/]"
                )
                pre_select_count = graph.statistics()["total_resources"]

                # Apply graph-based selection
                selection_result = apply_selection(graph, selection_strategy)

                # Build subgraph from selection
                graph = build_subgraph_from_selection(graph, selection_result)

                post_select_count = graph.statistics()["total_resources"]
                console.print(
                    f"[dim]Selected: {post_select_count} of {pre_select_count} resources "
                    f"({selection_result.summary()['clone']} to clone, "
                    f"{selection_result.summary()['reference']} to reference)[/]"
                )

        else:
            # Legacy filter support (backwards compatibility)
            scan_filter = ScanFilter.from_cli_args(
                vpc=vpc,
                vpc_name=vpc_name,
                types=types,
                tags=tag,
                exclude_types=exclude_types,
                exclude_tags=exclude_tag,
            )

            if not scan_filter.is_empty():
                console.print(f"\n[dim]Applying filters: {scan_filter.describe()}[/]")
                pre_filter_count = graph.statistics()["total_resources"]
                removed_count = apply_filter_to_graph(
                    graph, scan_filter, retain_dependencies=True
                )
                console.print(
                    f"[dim]Filtered: {pre_filter_count} → "
                    f"{pre_filter_count - removed_count} resources[/]"
                )

        # Get resource stats (no limits - resources are unlimited!)
        stats = graph.statistics()
        resource_count = stats["total_resources"]

        # Record usage
        tracker.record_scan(
            scan_id=str(uuid.uuid4()),
            region=effective_region,
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

        # Show remaining scans for FREE users
        remaining = get_scans_remaining()
        if remaining >= 0:
            console.print(
                f"\n[dim]Scans remaining this month: "
                f"{remaining}/{features.max_scans_per_month}[/dim]"
            )

        # Save output if requested
        if output:
            graph.save(output)
            console.print(f"\n[green]Graph saved to[/] {output}")

        # Close Trust Center session if enabled (P1-9)
        if trust_center and tc_session_id:
            from replimap.audit import TrustCenter

            tc = TrustCenter.get_instance()
            tc.end_session(tc_session_id)
            session_info = tc.get_session(tc_session_id)
            if session_info:
                console.print(
                    f"\n[dim]Trust Center: {session_info.total_calls} API calls captured "
                    f"({session_info.read_only_percentage:.1f}% read-only)[/]"
                )
                console.print(
                    "[dim]Run 'replimap trust-center report' to generate "
                    "compliance report[/]"
                )

        console.print()
