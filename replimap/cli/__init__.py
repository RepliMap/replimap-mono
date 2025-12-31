"""
RepliMap CLI Module.

This module provides the command-line interface for RepliMap.
It exports the Typer app instance and shared utilities.
"""

from __future__ import annotations

import logging

import typer

from replimap import __version__
from replimap.cli.commands import register_all_commands
from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_aws_session,
    get_profile_region,
    logger,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold cyan]RepliMap[/] v{__version__}")
        raise typer.Exit()


def create_app() -> typer.Typer:
    """
    Create and configure the CLI application.

    Returns:
        Configured Typer application with all commands registered.
    """
    app = typer.Typer(
        name="replimap",
        help="AWS Environment Replication Tool - Clone your production to staging in minutes",
        add_completion=False,
        rich_markup_mode="rich",
        context_settings={"help_option_names": ["-h", "--help"]},
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

    # Register all commands
    register_all_commands(app)

    return app


# Create the app instance
app = create_app()

__all__ = [
    # App
    "app",
    "create_app",
    # Utilities
    "console",
    "logger",
    "get_aws_session",
    "get_available_profiles",
    "get_profile_region",
]
