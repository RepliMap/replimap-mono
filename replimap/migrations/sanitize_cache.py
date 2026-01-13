"""
Migration script for sanitizing existing cache data.

This handles the upgrade from pre-sanitization versions to v0.4.0+.

The migration provides two options:
1. Delete cache and re-scan (recommended, safest)
2. Keep existing cache (not recommended - may contain secrets)

Usage:
    from replimap.migrations import check_cache_needs_migration, run_migration

    if check_cache_needs_migration():
        run_migration(interactive=True)
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Marker file indicating successful migration
MIGRATION_MARKER = ".sanitized_v1"


def check_cache_needs_migration(cache_dir: Optional[Path] = None) -> bool:
    """
    Check if cache needs sanitization migration.

    Returns True if:
    - Cache exists
    - No migration marker found

    Args:
        cache_dir: Optional cache directory path. Defaults to ~/.replimap/cache

    Returns:
        True if migration is needed
    """
    cache_dir = cache_dir or Path.home() / ".replimap" / "cache"

    if not cache_dir.exists():
        return False

    marker_file = cache_dir / MIGRATION_MARKER
    return not marker_file.exists()


def run_migration(
    cache_dir: Optional[Path] = None,
    interactive: bool = True,
    force_delete: bool = False,
) -> bool:
    """
    Run sanitization migration.

    Options:
    1. Delete cache and re-scan (recommended, safest)
    2. Attempt in-place sanitization (risky, may miss patterns)

    Args:
        cache_dir: Cache directory path
        interactive: If True, prompt user for confirmation
        force_delete: If True, delete without prompting

    Returns:
        True if migration completed successfully
    """
    try:
        from rich.console import Console
        from rich.panel import Panel

        has_rich = True
    except ImportError:
        has_rich = False

    cache_dir = cache_dir or Path.home() / ".replimap" / "cache"

    if not cache_dir.exists():
        logger.info("No cache directory found, migration not needed")
        return True

    # Check for existing data
    db_file = cache_dir / "replimap.db"
    graph_file = cache_dir / "graph.db"
    json_files = list(cache_dir.glob("*.json"))

    has_data = db_file.exists() or graph_file.exists() or json_files

    if not has_data:
        # Empty cache, just mark as migrated
        _create_migration_marker(cache_dir)
        return True

    # Show migration notice
    if has_rich:
        console = Console()
        console.print()
        console.print(
            Panel(
                "[yellow bold]⚠️  Security Migration Required[/]\n\n"
                "RepliMap v0.4.0 introduces enhanced data sanitization to protect\n"
                "sensitive information (passwords, API keys, private keys).\n\n"
                "[bold]Your existing cache may contain unsanitized sensitive data.[/]\n\n"
                "Options:\n"
                "  [green]1. Delete cache and re-scan[/] (Recommended - ensures clean data)\n"
                "  [yellow]2. Keep existing cache[/] (Not recommended - may contain secrets)\n\n"
                f"Cache location: [cyan]{cache_dir}[/]",
                title="🔐 Data Sanitization Migration",
                border_style="yellow",
            )
        )
    else:
        print()
        print("=" * 60)
        print("⚠️  Security Migration Required")
        print("=" * 60)
        print()
        print("RepliMap v0.4.0 introduces enhanced data sanitization to protect")
        print("sensitive information (passwords, API keys, private keys).")
        print()
        print("Your existing cache may contain unsanitized sensitive data.")
        print()
        print("Options:")
        print("  1. Delete cache and re-scan (Recommended - ensures clean data)")
        print("  2. Keep existing cache (Not recommended - may contain secrets)")
        print()
        print(f"Cache location: {cache_dir}")
        print()

    if force_delete:
        choice = "1"
    elif interactive:
        if has_rich:
            console.print()
            choice = console.input("[bold]Choose option (1 to delete, 2 to keep): [/]").strip()
        else:
            choice = input("Choose option (1 to delete, 2 to keep): ").strip()
    else:
        # Non-interactive, non-force: default to keeping (safer for CI/CD)
        logger.warning("Non-interactive mode: keeping existing cache")
        _create_migration_marker(cache_dir)
        return True

    if choice == "1":
        return _delete_and_migrate(cache_dir, has_rich)
    else:
        if has_rich:
            console = Console()
            console.print()
            console.print(
                "[yellow]Warning:[/] Keeping existing cache. "
                "Consider running 'replimap cache clear' and re-scanning."
            )
        else:
            print()
            print(
                "Warning: Keeping existing cache. "
                "Consider running 'replimap cache clear' and re-scanning."
            )
        _create_migration_marker(cache_dir)
        return True


def _delete_and_migrate(cache_dir: Path, has_rich: bool = True) -> bool:
    """Delete cache and create migration marker."""
    try:
        if has_rich:
            from rich.console import Console

            console = Console()
        else:
            console = None

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = cache_dir.parent / f"cache_backup_{timestamp}"

        if console:
            console.print(f"Creating backup at [cyan]{backup_dir}[/]...")
        else:
            print(f"Creating backup at {backup_dir}...")

        shutil.copytree(cache_dir, backup_dir)

        # Delete original cache contents (keep directory)
        for item in cache_dir.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

        # Create migration marker
        _create_migration_marker(cache_dir)

        if console:
            console.print()
            console.print("[green]✓ Cache cleared successfully[/]")
            console.print(f"  Backup saved to: [cyan]{backup_dir}[/]")
            console.print(
                "  Please run [bold]replimap scan[/] to rebuild with sanitization."
            )
            console.print()
        else:
            print()
            print("✓ Cache cleared successfully")
            print(f"  Backup saved to: {backup_dir}")
            print("  Please run 'replimap scan' to rebuild with sanitization.")
            print()

        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if has_rich:
            from rich.console import Console

            console = Console()
            console.print(f"[red]Migration failed: {e}[/]")
        else:
            print(f"Migration failed: {e}")
        return False


def _create_migration_marker(cache_dir: Path) -> None:
    """Create marker file indicating successful migration."""
    marker_file = cache_dir / MIGRATION_MARKER
    marker_file.write_text(
        f"Sanitization migration completed: {datetime.now().isoformat()}\n"
        f"RepliMap version: 0.4.0\n"
    )
    logger.info("Created sanitization migration marker")


def register_migration_check() -> None:
    """
    Register migration check to run on startup.

    Call this from CLI entry point.
    """
    if check_cache_needs_migration():
        run_migration(interactive=True)
