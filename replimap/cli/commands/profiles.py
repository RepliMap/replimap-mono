"""
Profiles command - List available AWS profiles.
"""

from __future__ import annotations

import typer
from rich.table import Table

from replimap.cli.utils import (
    console,
    get_available_profiles,
    get_cached_credentials,
    get_profile_region,
)


def register(app: typer.Typer) -> None:
    """Register the profiles command with the app."""

    @app.command()
    def profiles() -> None:
        """List available AWS profiles.

        \b

        Shows all configured AWS profiles from ~/.aws/config and ~/.aws/credentials.

        \b

        Examples:

            replimap profiles
        """
        available = get_available_profiles()

        table = Table(
            title="Available AWS Profiles",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Profile", style="cyan")
        table.add_column("Region", style="dim")
        table.add_column("Status")

        for profile_name in available:
            region = get_profile_region(profile_name) or "[dim]not set[/]"

            # Check if credentials are cached
            cached = get_cached_credentials(profile_name)
            if cached:
                status = "[green]cached[/]"
            else:
                status = "[dim]-[/]"

            table.add_row(profile_name, region, status)

        console.print(table)

        console.print()
        console.print("[dim]Tip: Use --profile <name> to select a profile[/]")
        console.print("[dim]Tip: Use --interactive or -i for guided setup[/]")
        console.print()
