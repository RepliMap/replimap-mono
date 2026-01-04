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
from replimap.cli.commands import (
    audit,
    cache,
    clone,
    completion,
    cost,
    deps,
    dr,
    drift,
    graph,
    license,
    load,
    profiles,
    remediate,
    scan,
    snapshot,
    transfer,
    trends,
    trust_center,
    unused,
    upgrade,
    validate,
)


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
    audit.register(app)
    graph.register(app)
    drift.register(app)
    deps.register(app)
    cost.register(app)
    remediate.register(app)
    validate.register(app)
    unused.register(app)
    trends.register(app)
    transfer.register(app)

    # Register sub-command groups
    cache.register(app)
    license.register(app)
    upgrade.register(app)
    snapshot.register(app)
    trust_center.register(app)
    dr.register(app)
    completion.register(app)


__all__ = [
    "register_all_commands",
    "scan",
    "clone",
    "load",
    "profiles",
    "audit",
    "graph",
    "drift",
    "deps",
    "cost",
    "remediate",
    "validate",
    "unused",
    "trends",
    "transfer",
    "cache",
    "license",
    "upgrade",
    "snapshot",
    "trust_center",
    "dr",
    "completion",
]
