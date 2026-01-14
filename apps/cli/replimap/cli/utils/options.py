"""
Shared Typer options and arguments for CLI commands.

This module provides commonly used Typer Option definitions
that are shared across multiple commands.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer


# Common profile option
def profile_option() -> str | None:
    """AWS profile option."""
    return None


ProfileOption = Annotated[
    str | None,
    typer.Option(
        "--profile",
        "-p",
        help="AWS profile to use (from ~/.aws/credentials)",
        envvar="AWS_PROFILE",
    ),
]

# Common region option
RegionOption = Annotated[
    str,
    typer.Option(
        "--region",
        "-r",
        help="AWS region to scan",
        envvar="AWS_DEFAULT_REGION",
    ),
]

# Optional region (for commands that can infer from profile)
OptionalRegionOption = Annotated[
    str | None,
    typer.Option(
        "--region",
        "-r",
        help="AWS region (defaults to profile's region)",
        envvar="AWS_DEFAULT_REGION",
    ),
]

# Output directory option
OutputDirOption = Annotated[
    Path,
    typer.Option(
        "--output-dir",
        "-o",
        help="Output directory for generated files",
    ),
]

# VPC filter option
VpcOption = Annotated[
    str | None,
    typer.Option(
        "--vpc",
        help="Filter by VPC ID",
    ),
]

# Tag filter option
TagOption = Annotated[
    list[str] | None,
    typer.Option(
        "--tag",
        "-t",
        help="Filter by tag (format: key=value). Can be used multiple times.",
    ),
]

# Format option
FormatOption = Annotated[
    str,
    typer.Option(
        "--format",
        "-f",
        help="Output format (json, yaml, table)",
    ),
]

# Quiet mode option
QuietOption = Annotated[
    bool,
    typer.Option(
        "--quiet",
        "-q",
        help="Suppress non-essential output",
    ),
]

# Dry run option
DryRunOption = Annotated[
    bool,
    typer.Option(
        "--dry-run",
        help="Show what would be done without making changes",
    ),
]

# Force option
ForceOption = Annotated[
    bool,
    typer.Option(
        "--force",
        "-f",
        help="Skip confirmation prompts",
    ),
]

# Yes option (auto-confirm)
YesOption = Annotated[
    bool,
    typer.Option(
        "--yes",
        "-y",
        help="Automatically answer yes to all prompts",
    ),
]
