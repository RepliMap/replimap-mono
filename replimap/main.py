"""
RepliMap CLI Entry Point.

Usage:
    replimap scan --profile <aws-profile> --region <region> [--output graph.json]
    replimap clone --profile <source-profile> --region <region> --output-dir ./terraform
    replimap license activate <key>
    replimap license status
"""

from __future__ import annotations

import configparser
import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import boto3
import typer
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table

from replimap import __version__
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

# Credential cache directory
CACHE_DIR = Path.home() / ".replimap" / "cache"
CREDENTIAL_CACHE_FILE = CACHE_DIR / "credentials.json"
CREDENTIAL_CACHE_TTL = timedelta(hours=12)  # Cache MFA credentials for 12 hours

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
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]RepliMap[/] v{__version__}")
        raise typer.Exit()


def get_available_profiles() -> list[str]:
    """Get list of available AWS profiles from config."""
    profiles = ["default"]
    config_path = Path.home() / ".aws" / "config"
    credentials_path = Path.home() / ".aws" / "credentials"

    for path in [config_path, credentials_path]:
        if path.exists():
            config = configparser.ConfigParser()
            config.read(path)
            for section in config.sections():
                # Config file uses "profile xxx" format, credentials uses just "xxx"
                if section.startswith("profile "):
                    profiles.append(section.replace("profile ", ""))
                elif section != "default":
                    profiles.append(section)

    return sorted(set(profiles))


def get_profile_region(profile: str | None) -> str | None:
    """
    Get the default region for a profile from AWS config.

    Args:
        profile: AWS profile name

    Returns:
        Region string if found, None otherwise
    """
    config_path = Path.home() / ".aws" / "config"
    if not config_path.exists():
        return None

    config = configparser.ConfigParser()
    config.read(config_path)

    # Determine section name
    if profile and profile != "default":
        section = f"profile {profile}"
    else:
        section = "default"

    if section in config and "region" in config[section]:
        return config[section]["region"]

    # Also check environment variable
    return os.environ.get("AWS_DEFAULT_REGION")


def get_credential_cache_key(profile: str | None) -> str:
    """Generate a cache key for credentials."""
    key = f"profile:{profile or 'default'}"
    return hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()


def get_cached_credentials(profile: str | None) -> dict | None:
    """
    Get cached credentials if valid.

    Returns cached session credentials to avoid repeated MFA prompts.
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        return None

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)

        cache_key = get_credential_cache_key(profile)
        if cache_key not in cache:
            return None

        entry = cache[cache_key]
        expires_at = datetime.fromisoformat(entry["expires_at"])

        if datetime.now() >= expires_at:
            return None

        return entry["credentials"]
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def save_cached_credentials(
    profile: str | None,
    credentials: dict,
    expiration: datetime | None = None,
) -> None:
    """Save credentials to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache = {}
    if CREDENTIAL_CACHE_FILE.exists():
        try:
            with open(CREDENTIAL_CACHE_FILE) as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            cache = {}

    cache_key = get_credential_cache_key(profile)

    # Use provided expiration or default TTL
    if expiration:
        expires_at = expiration
    else:
        expires_at = datetime.now() + CREDENTIAL_CACHE_TTL

    cache[cache_key] = {
        "credentials": credentials,
        "expires_at": expires_at.isoformat(),
        "profile": profile,
    }

    with open(CREDENTIAL_CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

    # Secure the cache file
    os.chmod(CREDENTIAL_CACHE_FILE, 0o600)


def clear_credential_cache(profile: str | None = None) -> None:
    """Clear credential cache for a profile or all profiles."""
    if not CREDENTIAL_CACHE_FILE.exists():
        return

    if profile is None:
        # Clear all
        CREDENTIAL_CACHE_FILE.unlink()
        return

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)

        cache_key = get_credential_cache_key(profile)
        if cache_key in cache:
            del cache[cache_key]

        with open(CREDENTIAL_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except (json.JSONDecodeError, KeyError):
        pass


def get_aws_session(
    profile: str | None, region: str, use_cache: bool = True
) -> boto3.Session:
    """
    Create a boto3 session with the specified profile and region.

    Supports credential caching to avoid repeated MFA prompts.

    Args:
        profile: AWS profile name (optional)
        region: AWS region
        use_cache: Whether to use credential caching (default: True)

    Returns:
        Configured boto3 Session

    Raises:
        typer.Exit: If credentials are invalid
    """
    # Try cached credentials first (for MFA sessions)
    if use_cache:
        cached = get_cached_credentials(profile)
        if cached:
            try:
                session = boto3.Session(
                    aws_access_key_id=cached["access_key"],
                    aws_secret_access_key=cached["secret_key"],
                    aws_session_token=cached.get("session_token"),
                    region_name=region,
                )
                sts = session.client("sts")
                identity = sts.get_caller_identity()
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](cached credentials)[/]"
                )
                return session
            except (ClientError, NoCredentialsError):
                # Cache invalid, continue with normal auth
                clear_credential_cache(profile)

    try:
        session = boto3.Session(profile_name=profile, region_name=region)

        # Verify credentials work
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        # Cache the credentials if they're temporary (MFA)
        credentials = session.get_credentials()
        if credentials and use_cache:
            frozen = credentials.get_frozen_credentials()
            if frozen.token:  # Has session token = temporary credentials
                save_cached_credentials(
                    profile,
                    {
                        "access_key": frozen.access_key,
                        "secret_key": frozen.secret_key,
                        "session_token": frozen.token,
                    },
                )
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"[dim](credentials cached for 12h)[/]"
                )
            else:
                console.print(
                    f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                    f"(Account: {identity['Account']})"
                )
        else:
            console.print(
                f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
                f"(Account: {identity['Account']})"
            )

        return session

    except ProfileNotFound:
        available = get_available_profiles()
        console.print(
            Panel(
                f"[red]Profile '{profile}' not found.[/]\n\n"
                f"Available profiles: [cyan]{', '.join(available)}[/]\n\n"
                "Configure a new profile with: [bold]aws configure --profile <name>[/]",
                title="Profile Not Found",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except NoCredentialsError:
        console.print(
            Panel(
                "[red]No AWS credentials found.[/]\n\n"
                "Configure credentials with:\n"
                "  [bold]aws configure[/] (for default profile)\n"
                "  [bold]aws configure --profile <name>[/] (for named profile)\n\n"
                "Or set environment variables:\n"
                "  [dim]AWS_ACCESS_KEY_ID[/]\n"
                "  [dim]AWS_SECRET_ACCESS_KEY[/]\n"
                "  [dim]AWS_SESSION_TOKEN[/] (optional)",
                title="Authentication Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "ExpiredToken":
            clear_credential_cache(profile)
            console.print(
                Panel(
                    "[yellow]Session token expired.[/]\n\n"
                    "Please re-authenticate. Your cached credentials have been cleared.",
                    title="Session Expired",
                    border_style="yellow",
                )
            )
        else:
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
        console.print("[dim]Performing incremental scan for updated resources...[/]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Scanning AWS resources ({scan_mode})...", total=None)
        results = run_all_scanners(
            session, effective_region, graph, parallel=use_parallel
        )
        progress.update(task, completed=True)
    scan_duration = time.time() - scan_start

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
                f"[dim]Filtered: {pre_filter_count} → {pre_filter_count - removed_count} resources[/]"
            )

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
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region to scan (uses profile's region or us-east-1)",
    ),
    output_dir: Path = typer.Option(
        Path("./terraform"),
        "--output-dir",
        "-o",
        help="Output directory for generated files",
    ),
    output_format: str = typer.Option(
        "terraform",
        "--format",
        "-f",
        help="Output format: 'terraform' (Free+), 'cloudformation' (Solo+), 'pulumi' (Pro+)",
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
) -> None:
    """
    Clone AWS environment to Infrastructure-as-Code.

    The region is determined in this order:
    1. --region flag (if provided)
    2. Profile's configured region (from ~/.aws/config)
    3. AWS_DEFAULT_REGION environment variable
    4. us-east-1 (fallback)

    Output formats:
    - terraform: Terraform HCL (Free tier and above)
    - cloudformation: AWS CloudFormation YAML (Solo plan and above)
    - pulumi: Pulumi Python (Pro plan and above)

    Examples:
        replimap clone --profile prod --mode dry-run
        replimap clone --profile prod --format terraform --mode generate
        replimap clone -i  # Interactive mode
        replimap clone --profile prod --format cloudformation -o ./cfn
    """
    from replimap.licensing.gates import FeatureNotAvailableError
    from replimap.renderers import CloudFormationRenderer, PulumiRenderer

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

    # Validate output format
    valid_formats = ("terraform", "cloudformation", "pulumi")
    if output_format not in valid_formats:
        console.print(
            f"[red]Error:[/] Invalid format '{output_format}'. "
            f"Use one of: {', '.join(valid_formats)}"
        )
        raise typer.Exit(1)

    if interactive:
        console.print(f"\n[dim]Current format: {output_format}[/]")
        if not Confirm.ask("Use this format?", default=True):
            output_format = Prompt.ask(
                "Select format",
                default="terraform",
                choices=list(valid_formats),
            )

    # Get the appropriate renderer
    format_info = {
        "terraform": ("Terraform HCL", "Free+"),
        "cloudformation": ("CloudFormation YAML", "Solo+"),
        "pulumi": ("Pulumi Python", "Pro+"),
    }
    format_name, plan_required = format_info[output_format]

    manager = get_license_manager()
    plan_badge = f"[dim]({manager.current_plan.value})[/]"

    console.print(
        Panel(
            f"[bold]RepliMap Clone[/] v{__version__} {plan_badge}\n"
            f"Region: [cyan]{effective_region}[/] [dim](from {region_source})[/]\n"
            f"Profile: [cyan]{profile or 'default'}[/]\n"
            f"Format: [cyan]{format_name}[/] ({plan_required})\n"
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
    session = get_aws_session(profile, effective_region, use_cache=not no_cache)

    # Initialize graph
    graph = GraphEngine()

    # Run all scanners with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning AWS resources...", total=None)
        run_all_scanners(session, effective_region, graph)
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

    # Select renderer based on format
    if output_format == "terraform":
        renderer = TerraformRenderer()
    elif output_format == "cloudformation":
        renderer = CloudFormationRenderer()
    else:  # pulumi
        renderer = PulumiRenderer()

    # Preview
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
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"Generating {format_name} files...", total=None
                )
                written = renderer.render(graph, output_dir)
                progress.update(task, completed=True)

            console.print(
                Panel(
                    f"[green]Generated {len(written)} files[/] in [bold]{output_dir}[/]",
                    border_style="green",
                )
            )
        except FeatureNotAvailableError as e:
            console.print()
            console.print(
                Panel(
                    f"[red]Feature not available:[/] {e}\n\n"
                    f"Upgrade your plan to use {format_name} output:\n"
                    f"[bold]https://replimap.io/upgrade[/]",
                    title="Upgrade Required",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

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


@app.command()
def profiles() -> None:
    """
    List available AWS profiles.

    Shows all configured AWS profiles from ~/.aws/config and ~/.aws/credentials.

    Examples:
        replimap profiles
    """
    available = get_available_profiles()

    table = Table(
        title="Available AWS Profiles", show_header=True, header_style="bold cyan"
    )
    table.add_column("Profile", style="cyan")
    table.add_column("Region", style="dim")
    table.add_column("Status")

    for profile_name in available:
        region = get_profile_region(profile_name) or "[dim]not set[/]"

        # Check if credentials are cached
        cached = get_cached_credentials(profile_name)
        if cached:
            status = "[green]cached[/]"
        else:
            status = "[dim]-[/]"

        table.add_row(profile_name, region, status)

    console.print(table)

    console.print()
    console.print("[dim]Tip: Use --profile <name> to select a profile[/]")
    console.print("[dim]Tip: Use --interactive or -i for guided setup[/]")
    console.print()


# Cache subcommand group
cache_app = typer.Typer(
    name="cache",
    help="Credential cache management",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(cache_app, name="cache")


@cache_app.command("clear")
def cache_clear(
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="Clear cache for specific profile (all if not specified)",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Clear cached AWS credentials.

    Examples:
        replimap cache clear
        replimap cache clear --profile prod
    """
    if not yes:
        if profile:
            confirm = Confirm.ask(f"Clear cached credentials for profile '{profile}'?")
        else:
            confirm = Confirm.ask("Clear all cached credentials?")
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    clear_credential_cache(profile)

    if profile:
        console.print(f"[green]Cleared cached credentials for profile '{profile}'[/]")
    else:
        console.print("[green]Cleared all cached credentials[/]")


@cache_app.command("status")
def cache_status() -> None:
    """
    Show credential cache status.

    Examples:
        replimap cache status
    """
    if not CREDENTIAL_CACHE_FILE.exists():
        console.print("[dim]No cached credentials.[/]")
        return

    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            cache = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        console.print("[dim]No cached credentials.[/]")
        return

    if not cache:
        console.print("[dim]No cached credentials.[/]")
        return

    table = Table(
        title="Cached Credentials", show_header=True, header_style="bold cyan"
    )
    table.add_column("Profile")
    table.add_column("Expires", style="dim")
    table.add_column("Status")

    now = datetime.now()
    for _cache_key, entry in cache.items():
        profile_name = entry.get("profile") or "default"
        expires_at = datetime.fromisoformat(entry["expires_at"])

        if now >= expires_at:
            status = "[red]expired[/]"
            expires_str = expires_at.strftime("%Y-%m-%d %H:%M")
        else:
            remaining = expires_at - now
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            status = f"[green]valid ({hours}h {minutes}m remaining)[/]"
            expires_str = expires_at.strftime("%Y-%m-%d %H:%M")

        table.add_row(profile_name, expires_str, status)

    console.print(table)
    console.print()


# Scan cache subcommand group
scan_cache_app = typer.Typer(
    name="scan-cache",
    help="Scan result cache management",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
app.add_typer(scan_cache_app, name="scan-cache")


@scan_cache_app.command("status")
def scan_cache_status() -> None:
    """
    Show scan cache status for all regions.

    Examples:
        replimap scan-cache status
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache found.[/]")
        return

    cache_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
    if not cache_files:
        console.print("[dim]No scan cache found.[/]")
        return

    table = Table(title="Scan Cache Status", show_header=True, header_style="bold cyan")
    table.add_column("Account")
    table.add_column("Region")
    table.add_column("Resources", justify="right")
    table.add_column("Last Updated", style="dim")

    total_resources = 0
    for cache_file in cache_files:
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)

            metadata = cache_data.get("metadata", {})
            entries = cache_data.get("entries", {})

            account_id = metadata.get("account_id", "unknown")
            region = metadata.get("region", "unknown")
            resource_count = len(entries)
            total_resources += resource_count

            last_updated = metadata.get("last_updated", 0)
            if last_updated:
                updated_str = datetime.fromtimestamp(last_updated).strftime(
                    "%Y-%m-%d %H:%M"
                )
            else:
                updated_str = "unknown"

            # Truncate account ID for display
            account_display = (
                f"{account_id[:4]}...{account_id[-4:]}"
                if len(account_id) > 10
                else account_id
            )

            table.add_row(account_display, region, str(resource_count), updated_str)
        except (json.JSONDecodeError, KeyError):
            continue

    console.print(table)
    console.print(f"\n[dim]Total cached resources: {total_resources}[/]")
    console.print(f"[dim]Cache directory: {DEFAULT_CACHE_DIR}[/]")
    console.print()


@scan_cache_app.command("clear")
def scan_cache_clear(
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="Clear cache for specific region only",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation",
    ),
) -> None:
    """
    Clear scan result cache.

    Examples:
        replimap scan-cache clear
        replimap scan-cache clear --region us-east-1
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache to clear.[/]")
        return

    cache_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
    if not cache_files:
        console.print("[dim]No scan cache to clear.[/]")
        return

    # Filter by region if specified
    files_to_delete = []
    for cache_file in cache_files:
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
            metadata = cache_data.get("metadata", {})
            if region is None or metadata.get("region") == region:
                files_to_delete.append(cache_file)
        except (json.JSONDecodeError, KeyError):
            files_to_delete.append(cache_file)  # Delete corrupt files

    if not files_to_delete:
        console.print(f"[dim]No cache found for region '{region}'.[/]")
        return

    if not yes:
        if region:
            confirm = Confirm.ask(
                f"Clear scan cache for region '{region}'? ({len(files_to_delete)} files)"
            )
        else:
            confirm = Confirm.ask(
                f"Clear all scan cache? ({len(files_to_delete)} files)"
            )
        if not confirm:
            console.print("[dim]Cancelled.[/]")
            raise typer.Exit(0)

    for cache_file in files_to_delete:
        cache_file.unlink()

    console.print(f"[green]Cleared {len(files_to_delete)} cache files.[/]")


@scan_cache_app.command("info")
def scan_cache_info(
    region: str = typer.Argument(
        ...,
        help="Region to show cache info for",
    ),
    account: str | None = typer.Option(
        None,
        "--account",
        "-a",
        help="AWS account ID (uses first found if not specified)",
    ),
) -> None:
    """
    Show detailed cache info for a region.

    Examples:
        replimap scan-cache info us-east-1
    """
    from replimap.core.cache import DEFAULT_CACHE_DIR

    if not DEFAULT_CACHE_DIR.exists():
        console.print("[dim]No scan cache found.[/]")
        raise typer.Exit(1)

    # Find cache file for region
    cache_file = None
    for cf in DEFAULT_CACHE_DIR.glob("scan-*.json"):
        try:
            with open(cf) as f:
                cache_data = json.load(f)
            metadata = cache_data.get("metadata", {})
            if metadata.get("region") == region:
                if account is None or metadata.get("account_id") == account:
                    cache_file = cf
                    break
        except (json.JSONDecodeError, KeyError):
            continue

    if cache_file is None:
        console.print(f"[red]No cache found for region '{region}'.[/]")
        raise typer.Exit(1)

    with open(cache_file) as f:
        cache_data = json.load(f)

    metadata = cache_data.get("metadata", {})
    entries = cache_data.get("entries", {})

    # Count by type
    type_counts: dict[str, int] = {}
    for entry in entries.values():
        resource = entry.get("resource", {})
        rtype = resource.get("resource_type", "unknown")
        type_counts[rtype] = type_counts.get(rtype, 0) + 1

    console.print(
        Panel(
            f"Account: [cyan]{metadata.get('account_id', 'unknown')}[/]\n"
            f"Region: [cyan]{metadata.get('region', 'unknown')}[/]\n"
            f"Total Resources: [bold]{len(entries)}[/]\n"
            f"Created: {datetime.fromtimestamp(metadata.get('created_at', 0)).strftime('%Y-%m-%d %H:%M')}\n"
            f"Last Updated: {datetime.fromtimestamp(metadata.get('last_updated', 0)).strftime('%Y-%m-%d %H:%M')}",
            title="Cache Info",
            border_style="cyan",
        )
    )

    if type_counts:
        console.print()
        table = Table(
            title="Cached Resources by Type",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Resource Type", style="dim")
        table.add_column("Count", justify="right")

        for rtype, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(rtype, str(count))

        console.print(table)

    console.print()


# License subcommand group
license_app = typer.Typer(
    name="license",
    help="License management commands",
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
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
