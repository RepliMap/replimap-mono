"""
RepliMap CLI Module.

This module provides the command-line interface for RepliMap.
It exports the Typer app instance and shared utilities.
"""

from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_aws_session,
    get_profile_region,
    logger,
)

__all__ = [
    "console",
    "logger",
    "get_aws_session",
    "get_available_profiles",
    "get_profile_region",
]
