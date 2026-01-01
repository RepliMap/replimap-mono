"""RepliMap CLI - AWS Infrastructure Intelligence Engine.

This is the main entry point for the RepliMap CLI.
All command implementations are in replimap/cli/commands/*.py.
"""

from __future__ import annotations

import logging
import os
import signal
import sys

import typer
from rich.console import Console

from replimap import __version__
from replimap.cli.commands import register_all_commands

# Create console and app
console = Console()

app = typer.Typer(
    name="replimap",
    help="AWS Infrastructure Intelligence Engine",
    pretty_exceptions_show_locals=False,
    no_args_is_help=False,  # We handle this in the callback
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress verbose output",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
    ),
) -> None:
    """RepliMap - AWS Infrastructure Intelligence Engine."""
    if version:
        console.print(f"RepliMap v{__version__}")
        raise typer.Exit(0)

    if quiet:
        logging.getLogger("replimap").setLevel(logging.WARNING)
        os.environ["REPLIMAP_QUIET"] = "1"

    # Show help if no command provided (mimic no_args_is_help)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)


# Register ALL commands from cli/commands/
register_all_commands(app)


def _signal_handler(sig: int, frame: object) -> None:
    """Handle SIGINT (Ctrl+C) gracefully."""
    console.print("\n[yellow]Cancelled by user[/yellow]")
    sys.exit(130)  # 130 is standard SIGINT exit code


def main() -> None:
    """Entry point for the CLI."""
    # Register signal handler for graceful Ctrl-C handling
    # This prevents ugly threading shutdown exceptions
    signal.signal(signal.SIGINT, _signal_handler)

    try:
        app()
    except KeyboardInterrupt:
        # Fallback in case signal handler doesn't catch it
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
