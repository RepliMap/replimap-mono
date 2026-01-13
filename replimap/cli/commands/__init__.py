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
    analyze,
    audit,
    cache,
    clone,
    completion,
    cost,
    deps,
    doctor,
    dr,
    drift,
    explain,
    graph,
    iam,
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
from replimap.decisions.cli import create_decisions_app


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
    analyze.register(app)
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
    iam.register(app)
    license.register(app)
    upgrade.register(app)
    snapshot.register(app)
    trust_center.register(app)
    dr.register(app)
    completion.register(app)

    # Register new P2 UX commands
    doctor.register(app)
    explain.register(app)
    app.add_typer(create_decisions_app())


__all__ = [
    "register_all_commands",
    "scan",
    "clone",
    "analyze",
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
    "iam",
    "license",
    "upgrade",
    "snapshot",
    "trust_center",
    "dr",
    "completion",
    "doctor",
    "explain",
]
