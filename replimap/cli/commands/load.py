"""
Load command - Load and display a saved graph.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.panel import Panel
from rich.table import Table

from replimap.cli.utils import console, print_graph_stats


def _load_graph(graph_file: Path):
    """Load a graph from file (supports both JSON and SQLite formats)."""
    suffix = graph_file.suffix.lower()

    if suffix == ".db":
        from replimap.core.unified_storage import GraphEngineAdapter

        return GraphEngineAdapter(db_path=str(graph_file))
    elif suffix == ".json":
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)
    else:
        # Try SQLite first
        try:
            with open(graph_file, "rb") as f:
                if f.read(16).startswith(b"SQLite format"):
                    from replimap.core.unified_storage import GraphEngineAdapter

                    return GraphEngineAdapter(db_path=str(graph_file))
        except (OSError, ValueError):
            pass  # Fall through to JSON loader
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)


def register(app: typer.Typer) -> None:
    """Register the load command with the app."""

    @app.command()
    def load(
        input_file: Path = typer.Argument(
            ...,
            help="Path to graph file (.db for SQLite, .json for legacy)",
        ),
    ) -> None:
        """Load and display a saved graph.

        Examples:

            replimap load graph.db

            replimap load graph.json
        """
        if not input_file.exists():
            console.print(f"[red]Error:[/] File not found: {input_file}")
            raise typer.Exit(1)

        graph = _load_graph(input_file)

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
