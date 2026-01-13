"""
Explain Command - Get detailed information about error codes.

Usage:
    replimap explain RM-E001
    replimap explain RM-E001 --verbose
    replimap errors              # List all error codes
"""

from __future__ import annotations

import typer
from rich.panel import Panel
from rich.table import Table

from replimap.cli.error_catalog import (
    ERROR_CATALOG,
    get_error_info,
    list_all_codes,
    search_errors,
)
from replimap.cli.errors import enhanced_cli_error_handler
from replimap.cli.utils import console


def register(app: typer.Typer) -> None:
    """Register the explain and errors commands with the main app."""

    @app.command()
    @enhanced_cli_error_handler
    def explain(
        code: str = typer.Argument(
            ...,
            help="Error code to explain (e.g., RM-E001)",
        ),
        verbose: bool = typer.Option(
            False,
            "--verbose",
            "-v",
            help="Show additional details",
        ),
    ) -> None:
        """
        Get detailed information about an error code.

        Shows the root cause, fix command, and documentation for
        any RepliMap error code.

        Examples:
            replimap explain RM-E001
            replimap explain RM-E100 --verbose
        """
        # Normalize code
        code_upper = code.upper()
        if not code_upper.startswith("RM-"):
            code_upper = f"RM-{code_upper}"

        entry = get_error_info(code_upper)

        if not entry:
            # Try to search
            results = search_errors(code)
            if results:
                console.print(f"[yellow]'{code}' not found. Did you mean:[/yellow]\n")
                for found_code, found_entry in results[:5]:
                    console.print(f"  [cyan]{found_code}[/cyan]: {found_entry.get('summary', '')}")
                console.print(f"\n[dim]Use 'replimap errors' to see all error codes[/dim]")
            else:
                console.print(f"[red]Unknown error code: {code}[/red]")
                console.print(f"[dim]Use 'replimap errors' to see all error codes[/dim]")
            raise typer.Exit(1)

        # Build content
        content_lines = []

        # Summary
        content_lines.append(f"[bold]{entry.get('summary', 'No description')}[/bold]")
        content_lines.append("")

        # Root cause
        if entry.get("root_cause"):
            content_lines.append("[yellow]Root Cause:[/yellow]")
            for line in entry["root_cause"].split("\n"):
                content_lines.append(f"  {line}")
            content_lines.append("")

        # Fix
        if entry.get("fix_command"):
            content_lines.append("[green]Fix:[/green]")
            content_lines.append(f"  [cyan]$ {entry['fix_command']}[/cyan]")
            if entry.get("fix_description"):
                content_lines.append(f"  {entry['fix_description']}")
            content_lines.append("")

        # Examples (verbose only)
        if verbose and entry.get("examples"):
            content_lines.append("[blue]Examples:[/blue]")
            for example in entry["examples"]:
                content_lines.append(f"  [dim]$ {example}[/dim]")
            content_lines.append("")

        # Documentation
        if entry.get("docs"):
            content_lines.append("[magenta]Documentation:[/magenta]")
            for doc in entry["docs"]:
                content_lines.append(f"  [link={doc}]{doc}[/link]")
            content_lines.append("")

        # Related codes
        if entry.get("related_codes"):
            related = ", ".join(entry["related_codes"])
            content_lines.append(f"[dim]Related: {related}[/dim]")

        # Render
        console.print(
            Panel(
                "\n".join(content_lines),
                title=f"[bold cyan]{code_upper}[/bold cyan]",
                border_style="cyan",
                expand=False,
            )
        )

    @app.command("errors")
    @enhanced_cli_error_handler
    def list_errors(
        search: str | None = typer.Option(
            None,
            "--search",
            "-s",
            help="Search for errors by keyword",
        ),
        category: str | None = typer.Option(
            None,
            "--category",
            "-c",
            help="Filter by category (auth, permission, rate, network, config, decision, terraform)",
        ),
    ) -> None:
        """
        List all error codes.

        Shows a table of all RepliMap error codes with their descriptions.

        Examples:
            replimap errors
            replimap errors --search permission
            replimap errors --category auth
        """
        # Get errors to display
        if search:
            results = search_errors(search)
            if not results:
                console.print(f"[yellow]No errors found matching '{search}'[/yellow]")
                return
            errors_to_show = results
        else:
            errors_to_show = [(code, entry) for code, entry in ERROR_CATALOG.items()]

        # Filter by category
        if category:
            category_ranges = {
                "auth": ("RM-E001", "RM-E099"),
                "permission": ("RM-E100", "RM-E199"),
                "rate": ("RM-E200", "RM-E299"),
                "network": ("RM-E300", "RM-E399"),
                "config": ("RM-E400", "RM-E499"),
                "decision": ("RM-E500", "RM-E599"),
                "terraform": ("RM-E600", "RM-E699"),
            }
            cat_lower = category.lower()
            if cat_lower in category_ranges:
                start, end = category_ranges[cat_lower]
                errors_to_show = [
                    (code, entry)
                    for code, entry in errors_to_show
                    if start <= code <= end
                ]
            else:
                console.print(
                    f"[yellow]Unknown category: {category}[/yellow]\n"
                    f"Valid categories: {', '.join(category_ranges.keys())}"
                )
                return

        if not errors_to_show:
            console.print("[dim]No errors to display.[/dim]")
            return

        # Sort by code
        errors_to_show = sorted(errors_to_show, key=lambda x: x[0])

        # Build table
        table = Table(
            title="RepliMap Error Codes",
            show_header=True,
            header_style="bold",
        )
        table.add_column("Code", style="cyan", no_wrap=True)
        table.add_column("Summary", max_width=50)
        table.add_column("Fix Command", style="green", max_width=40)

        for code, entry in errors_to_show:
            table.add_row(
                code,
                entry.get("summary", ""),
                entry.get("fix_command", "")[:40],
            )

        console.print(table)
        console.print()
        console.print(
            f"[dim]Total: {len(errors_to_show)} error codes. "
            f"Use 'replimap explain <code>' for details.[/dim]"
        )


__all__ = ["register"]
