"""
Custom autocompleters for Typer CLI options.

Provides dynamic autocompletion for:
- AWS profile names
- AWS regions
- Output formats
- Backend types

Usage:
    @app.command()
    def scan(
        profile: str = typer.Option(
            ...,
            "-p", "--profile",
            autocompletion=profile_completer,
        ),
        region: str = typer.Option(
            ...,
            "-r", "--region",
            autocompletion=region_completer,
        ),
    ):
        pass
"""

from __future__ import annotations

from replimap.cli.completion import get_aws_profiles, get_aws_regions


def profile_completer(incomplete: str) -> list[str]:
    """
    Autocomplete AWS profile names.

    Reads profiles from ~/.aws/credentials and ~/.aws/config.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching profile names
    """
    profiles = get_aws_profiles()
    if not incomplete:
        return profiles
    return [p for p in profiles if p.startswith(incomplete)]


def region_completer(incomplete: str) -> list[str]:
    """
    Autocomplete AWS region names.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching region names
    """
    regions = get_aws_regions()
    if not incomplete:
        return regions
    return [r for r in regions if r.startswith(incomplete)]


def format_completer(incomplete: str) -> list[str]:
    """
    Autocomplete output formats.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching format names
    """
    formats = ["terraform", "cloudformation", "pulumi"]
    if not incomplete:
        return formats
    return [f for f in formats if f.startswith(incomplete)]


def mode_completer(incomplete: str) -> list[str]:
    """
    Autocomplete clone modes.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching mode names
    """
    modes = ["dry-run", "generate"]
    if not incomplete:
        return modes
    return [m for m in modes if m.startswith(incomplete)]


def backend_completer(incomplete: str) -> list[str]:
    """
    Autocomplete backend types.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching backend types
    """
    backends = ["local", "s3"]
    if not incomplete:
        return backends
    return [b for b in backends if b.startswith(incomplete)]


def shell_completer(incomplete: str) -> list[str]:
    """
    Autocomplete shell types for completion command.

    Args:
        incomplete: Partial input to match

    Returns:
        List of matching shell types
    """
    shells = ["bash", "zsh", "fish"]
    if not incomplete:
        return shells
    return [s for s in shells if s.startswith(incomplete)]
