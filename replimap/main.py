"""RepliMap CLI - AWS Infrastructure Intelligence Engine.

This is the main entry point for the RepliMap CLI.
All command implementations are in replimap/cli/commands/*.py.
"""

from __future__ import annotations

import logging
import os

import typer
from rich.console import Console

from replimap import __version__
from replimap.cli.commands import register_all_commands
from replimap.core.signals import setup_signal_handlers

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
    profile: str | None = typer.Option(
        None,
        "--profile",
        "-p",
        help="AWS profile name (can also be set per-command)",
    ),
    region: str | None = typer.Option(
        None,
        "--region",
        "-r",
        help="AWS region (can also be set per-command)",
    ),
) -> None:
    """RepliMap - AWS Infrastructure Intelligence Engine."""
    if version:
        console.print(f"RepliMap v{__version__}")
        raise typer.Exit(0)

    if quiet:
        logging.getLogger("replimap").setLevel(logging.WARNING)
        os.environ["REPLIMAP_QUIET"] = "1"

    # Store global options in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["global_profile"] = profile
    ctx.obj["global_region"] = region

    # Show help if no command provided (mimic no_args_is_help)
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())
        raise typer.Exit(0)


# Register ALL commands from cli/commands/
register_all_commands(app)


def main() -> None:
    """Entry point for the CLI."""
    # Install global signal handlers for graceful Ctrl-C handling
    # This prevents ugly threading shutdown exceptions by:
    # 1. Shutting down all tracked thread pools
    # 2. Using os._exit() to skip Python cleanup
    setup_signal_handlers(console)

    # Run the app - no need for KeyboardInterrupt handling here
    # since the signal handler uses os._exit()
    app()


if __name__ == "__main__":
    main()
