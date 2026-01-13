"""
Cache commands - Credential and scan cache management.

V3 Architecture:
- Uses @enhanced_cli_error_handler for structured error handling
"""

from __future__ import annotations

import json
from datetime import datetime

import typer
from rich.prompt import Confirm
from rich.table import Table

from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import (
    CREDENTIAL_CACHE_FILE,
    clear_credential_cache,
    console,
)


def create_cache_app() -> typer.Typer:
    """Create the cache sub-command group."""
    cache_app = typer.Typer(
        name="cache",
        help="Credential cache management",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @cache_app.command("clear")
    @enhanced_cli_error_handler
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
                confirm = Confirm.ask(
                    f"Clear cached credentials for profile '{profile}'?"
                )
            else:
                confirm = Confirm.ask("Clear all cached credentials?")
            if not confirm:
                console.print("[dim]Cancelled.[/]")
                raise typer.Exit(0)

        clear_credential_cache(profile)

        if profile:
            console.print(
                f"[green]Cleared cached credentials for profile '{profile}'[/]"
            )
        else:
            console.print("[green]Cleared all cached credentials[/]")

    @cache_app.command("status")
    @enhanced_cli_error_handler
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
            title="Cached Credentials",
            show_header=True,
            header_style="bold cyan",
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

    @cache_app.command("reset-first-run", hidden=True)
    @enhanced_cli_error_handler
    def reset_first_run() -> None:
        """
        Reset first-run marker (for testing).

        This is a hidden command used for development and testing.
        """
        from replimap.core.first_run import reset_first_run_marker

        if reset_first_run_marker():
            console.print("[green]First-run marker reset.[/]")
        else:
            console.print("[dim]First-run marker was not set.[/]")

    return cache_app


def create_scan_cache_app() -> typer.Typer:
    """Create the scan-cache sub-command group."""
    scan_cache_app = typer.Typer(
        name="scan-cache",
        help="Scan result cache management",
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
    )

    @scan_cache_app.command("status")
    def scan_cache_status() -> None:
        """
        Show scan cache status for all regions.

        Examples:
            replimap scan-cache status
        """
        from replimap.core.cache import DEFAULT_CACHE_DIR
        from replimap.core.cache_manager import GRAPH_CACHE_DIR

        has_any_cache = False

        # Show graph cache (SQLite .db files)
        if GRAPH_CACHE_DIR.exists():
            graph_files = list(GRAPH_CACHE_DIR.glob("graph_*.db"))
            if graph_files:
                has_any_cache = True
                table = Table(
                    title="Graph Cache (SQLite)",
                    show_header=True,
                    header_style="bold cyan",
                )
                table.add_column("Profile")
                table.add_column("Region")
                table.add_column("Resources", justify="right")
                table.add_column("Size", justify="right")

                for graph_file in graph_files:
                    # Parse filename: graph_{profile}_{region}.db
                    parts = graph_file.stem.replace("graph_", "").rsplit("_", 1)
                    profile = parts[0] if len(parts) > 1 else "default"
                    region = parts[1] if len(parts) > 1 else parts[0]
                    size_mb = graph_file.stat().st_size / (1024 * 1024)

                    # Try to get resource count from the database
                    try:
                        from replimap.core.unified_storage import GraphEngineAdapter

                        adapter = GraphEngineAdapter(db_path=str(graph_file))
                        resources = adapter.node_count
                    except Exception:
                        resources = "?"

                    table.add_row(profile, region, str(resources), f"{size_mb:.1f} MB")

                console.print(table)
                console.print()

        # Show incremental scan cache (JSON files)
        if DEFAULT_CACHE_DIR.exists():
            cache_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
            if cache_files:
                has_any_cache = True
                table = Table(
                    title="Incremental Scan Cache (JSON)",
                    show_header=True,
                    header_style="bold cyan",
                )
                table.add_column("Account")
                table.add_column("Region")
                table.add_column("Resources", justify="right")
                table.add_column("Last Updated", style="dim")

                total_resources = 0
                for cache_file in cache_files:
                    try:
                        with open(cache_file) as f:
                            cache_data = json.load(f)
                        account = cache_data.get("account_id", "unknown")
                        region = cache_data.get("region", "unknown")
                        resources = len(cache_data.get("resources", {}))
                        updated = cache_data.get("last_updated", "unknown")
                        if updated != "unknown":
                            updated = datetime.fromisoformat(updated).strftime(
                                "%Y-%m-%d %H:%M"
                            )
                        table.add_row(account, region, str(resources), updated)
                        total_resources += resources
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue

                console.print(table)
                console.print(
                    f"\n[dim]Total incrementally cached resources: {total_resources}[/]"
                )
                console.print()

        if not has_any_cache:
            console.print("[dim]No cache found.[/]")

    @scan_cache_app.command("clear")
    def scan_cache_clear(
        region: str | None = typer.Option(
            None,
            "--region",
            "-r",
            help="Clear cache for specific region (all if not specified)",
        ),
        yes: bool = typer.Option(
            False,
            "--yes",
            "-y",
            help="Skip confirmation",
        ),
        graph_only: bool = typer.Option(
            False,
            "--graph-only",
            help="Only clear graph cache (SQLite .db files)",
        ),
        incremental_only: bool = typer.Option(
            False,
            "--incremental-only",
            help="Only clear incremental scan cache (JSON files)",
        ),
    ) -> None:
        """
        Clear scan result cache.

        Examples:
            replimap scan-cache clear
            replimap scan-cache clear --region us-west-2
            replimap scan-cache clear --graph-only
        """
        from replimap.core.cache import DEFAULT_CACHE_DIR
        from replimap.core.cache_manager import GRAPH_CACHE_DIR

        files_to_delete: list = []

        # Collect graph cache files
        if not incremental_only and GRAPH_CACHE_DIR.exists():
            if region:
                graph_files = list(GRAPH_CACHE_DIR.glob(f"graph_*_{region}.db"))
            else:
                graph_files = list(GRAPH_CACHE_DIR.glob("graph_*.db"))
            files_to_delete.extend(graph_files)

        # Collect incremental scan cache files
        if not graph_only and DEFAULT_CACHE_DIR.exists():
            if region:
                scan_files = list(DEFAULT_CACHE_DIR.glob(f"scan-*-{region}.json"))
            else:
                scan_files = list(DEFAULT_CACHE_DIR.glob("scan-*.json"))
            files_to_delete.extend(scan_files)

        if not files_to_delete:
            console.print("[dim]No cache found.[/]")
            return

        if not yes:
            if region:
                confirm = Confirm.ask(
                    f"Clear cache for region '{region}' ({len(files_to_delete)} files)?"
                )
            else:
                confirm = Confirm.ask(
                    f"Clear all cache ({len(files_to_delete)} files)?"
                )
            if not confirm:
                console.print("[dim]Cancelled.[/]")
                raise typer.Exit(0)

        for cache_file in files_to_delete:
            cache_file.unlink()

        console.print(f"[green]Cleared {len(files_to_delete)} cache files.[/]")

    @scan_cache_app.command("info")
    def scan_cache_info(
        region: str = typer.Option(
            ...,
            "--region",
            "-r",
            help="Region to show cache info for",
        ),
    ) -> None:
        """
        Show detailed cache info for a region.

        Examples:
            replimap scan-cache info --region us-west-2
        """
        from replimap.core.cache import DEFAULT_CACHE_DIR

        cache_files = list(DEFAULT_CACHE_DIR.glob(f"scan-*-{region}.json"))
        if not cache_files:
            console.print(f"[dim]No scan cache found for region '{region}'.[/]")
            return

        cache_file = cache_files[0]
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            console.print("[red]Failed to load cache file.[/]")
            return

        # Count resources by type
        resources = cache_data.get("resources", {})
        type_counts: dict[str, int] = {}
        for _resource_id, resource in resources.items():
            rtype = resource.get("resource_type", "unknown")
            type_counts[rtype] = type_counts.get(rtype, 0) + 1

        table = Table(
            title=f"Scan Cache: {region}",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Resource Type")
        table.add_column("Count", justify="right")

        for rtype, count in sorted(
            type_counts.items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(rtype, str(count))

        console.print(table)
        console.print(f"\n[dim]Total: {len(resources)} resources[/]")
        console.print()

    return scan_cache_app


def register(app: typer.Typer) -> None:
    """Register cache commands with the app."""
    app.add_typer(create_cache_app(), name="cache")
    app.add_typer(create_scan_cache_app(), name="scan-cache")
