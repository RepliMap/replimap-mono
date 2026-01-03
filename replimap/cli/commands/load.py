"""
Load command - Load and display a saved graph.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from replimap.cli.utils import console, print_graph_stats
from replimap.core import GraphEngine


def register(app: typer.Typer) -> None:
    """Register the load command with the app."""

    @app.command()
    def load(
        input_file: Path = typer.Argument(
            ...,
            help="Path to graph JSON file",
        ),
    ) -> None:
        """
        Load and display a saved graph.

        \b
        Examples:
            replimap load graph.json
        """
        if not input_file.exists():
            console.print(f"[red]Error:[/] File not found: {input_file}")
            raise typer.Exit(1)

        graph = GraphEngine.load(input_file)

        console.print(
            Panel(
                f"Loaded graph from [bold]{input_file}[/]",
                title="Graph Loaded",
                border_style="green",
            )
        )

        # Print statistics
        print_graph_stats(graph)

        # Show resources table
        console.print()
        table = Table(
            title="Resources (first 20)",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Type", style="dim")
        table.add_column("ID")
        table.add_column("Dependencies", justify="right")

        # Use safe dependency order to handle cycles
        for resource in graph.get_safe_dependency_order()[:20]:
            deps = graph.get_dependencies(resource.id)
            table.add_row(
                str(resource.resource_type),
                resource.id,
                str(len(deps)) if deps else "-",
            )

        console.print(table)

        stats = graph.statistics()
        if stats["total_resources"] > 20:
            console.print(f"[dim]... and {stats['total_resources'] - 20} more[/]")

        console.print()
