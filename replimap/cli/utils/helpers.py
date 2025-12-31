"""
Shared helper functions for CLI commands.

This module contains utility functions used across multiple CLI commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table

from replimap.cli.utils.console import console

if TYPE_CHECKING:
    from replimap.core import GraphEngine


def print_scan_summary(graph: GraphEngine, duration: float) -> None:
    """
    Print a summary of scanned resources with counts by type.

    Args:
        graph: The populated graph engine
        duration: Scan duration in seconds
    """
    resources = graph.get_all_resources()
    if not resources:
        console.print("[dim]No resources found.[/]")
        return

    # Count resources by type
    type_counts: dict[str, int] = {}
    for node in resources:
        type_name = str(node.resource_type).replace("aws_", "")
        type_counts[type_name] = type_counts.get(type_name, 0) + 1

    # Sort by count (descending)
    sorted_counts = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)

    # Format summary line
    total = len(resources)
    top_types = sorted_counts[:4]  # Show top 4 resource types
    type_summary = ", ".join(f"{count} {name}" for name, count in top_types)

    if len(sorted_counts) > 4:
        other_count = sum(count for _, count in sorted_counts[4:])
        type_summary += f", +{other_count} others"

    console.print(
        f"[green]✓ Scanned {total} resources[/] ({type_summary}) "
        f"[dim]in {duration:.1f}s[/]"
    )


def print_graph_stats(graph: GraphEngine) -> None:
    """Print graph statistics in a rich table."""
    stats = graph.statistics()

    table = Table(title="Graph Statistics", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Resources", str(stats["total_resources"]))
    table.add_row("Total Dependencies", str(stats["total_dependencies"]))

    if stats["resources_by_type"]:
        table.add_section()
        for rtype, count in sorted(stats["resources_by_type"].items()):
            table.add_row(f"  {rtype}", str(count))

    console.print(table)

    if stats["has_cycles"]:
        console.print(
            "[yellow]Warning:[/] Dependency graph contains cycles!",
            style="bold yellow",
        )


__all__ = [
    "print_scan_summary",
    "print_graph_stats",
]
