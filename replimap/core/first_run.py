"""
First-run experience for RepliMap.

Shows a one-time privacy message on first run to build user trust,
confirming that all data processing happens locally.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console

# Shared directory for RepliMap data
REPLIMAP_DIR = Path.home() / ".replimap"
FIRST_RUN_MARKER = REPLIMAP_DIR / ".first_run_complete"


def check_and_show_first_run_message(console: Console) -> None:
    """
    Show welcome message on first run only.

    Creates a marker file to prevent showing again on subsequent runs.
    This message builds user trust by confirming local-only operation.

    Args:
        console: Rich Console instance for output
    """
    from rich.panel import Panel

    # Ensure directory exists
    REPLIMAP_DIR.mkdir(parents=True, exist_ok=True)

    # Check if already shown
    if FIRST_RUN_MARKER.exists():
        return

    # Show first-run message
    message = (
        "[bold green]🔒 100% Local & Private[/bold green]\n\n"
        "RepliMap runs entirely on your machine.\n"
        "• No data is sent to external servers\n"
        "• No telemetry or analytics\n"
        "• Your AWS credentials never leave your computer\n\n"
        "[dim]This message appears once. "
        "Run 'replimap --privacy' for details anytime.[/dim]"
    )

    console.print()
    console.print(Panel(message, title="Welcome to RepliMap", border_style="green"))
    console.print()

    # Create marker file
    try:
        FIRST_RUN_MARKER.touch()
    except OSError:
        pass  # Don't fail if we can't write marker


def show_privacy_info(console: Console) -> None:
    """
    Show privacy information on demand (--privacy flag).

    Args:
        console: Rich Console instance for output
    """
    from rich.panel import Panel

    message = (
        "[bold green]🔒 Privacy & Security[/bold green]\n\n"
        "RepliMap is designed with privacy-first principles:\n\n"
        "• [bold]100% Local:[/bold] All scanning runs on your machine\n"
        "• [bold]No Phone Home:[/bold] No telemetry, analytics, or tracking\n"
        "• [bold]No Cloud:[/bold] Your infrastructure data never leaves your computer\n"
        "• [bold]Credentials:[/bold] AWS credentials are only used locally via boto3\n"
        "• [bold]Cache:[/bold] Scan results stored in ~/.replimap/cache/ (local only)\n\n"
        "[dim]Source code: https://github.com/RepliMap/replimap[/dim]"
    )
    console.print(Panel(message, title="RepliMap Privacy", border_style="green"))


def reset_first_run_marker() -> bool:
    """
    Reset the first-run marker file for testing.

    Returns:
        True if marker was removed, False if it didn't exist
    """
    if FIRST_RUN_MARKER.exists():
        FIRST_RUN_MARKER.unlink()
        return True
    return False
