"""
CLI Commands Module.

This module contains all CLI command implementations for RepliMap.
Commands are organized into separate files for maintainability.

Usage:
    from replimap.cli.commands import register_all_commands

    app = typer.Typer()
    register_all_commands(app)
"""

from __future__ import annotations

import typer

# Import individual command modules
from replimap.cli.commands import cache, clone, license, load, profiles, scan


def register_all_commands(app: typer.Typer) -> None:
    """
    Register all commands with the Typer app.

    This function imports and registers all command modules.
    Each module should have a `register(app)` function.

    Args:
        app: The Typer application instance
    """
    # Register main commands
    scan.register(app)
    clone.register(app)
    load.register(app)
    profiles.register(app)

    # Register sub-command groups
    cache.register(app)
    license.register(app)


__all__ = [
    "register_all_commands",
    "scan",
    "clone",
    "load",
    "profiles",
    "cache",
    "license",
]
