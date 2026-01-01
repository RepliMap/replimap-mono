"""
Shared helper functions for CLI commands.

This module contains utility functions used across multiple CLI commands.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table

from replimap.cli.utils.console import console

if TYPE_CHECKING:
    from replimap.core import GraphEngine


def print_scan_summary(graph: GraphEngine, duration: float) -> None:
    """
    Print a summary of scanned resources with counts by type.

    Note: This function is deprecated in favor of the progress bar output.
    Kept for backwards compatibility but now a no-op.

    Args:
        graph: The populated graph engine
        duration: Scan duration in seconds
    """
    # No-op: Progress bar now shows this information
    pass


def print_graph_stats(graph: GraphEngine) -> None:
    """Print graph statistics in a rich table (Top 10 + others)."""
    stats = graph.statistics()

    if not stats["resources_by_type"]:
        console.print("[dim]No resources found.[/]")
        return

    # Sort by count descending
    sorted_types = sorted(
        stats["resources_by_type"].items(), key=lambda x: x[1], reverse=True
    )

    table = Table(title="Top Resources", show_header=True, header_style="bold cyan")
    table.add_column("Resource Type", style="dim")
    table.add_column("Count", justify="right")

    # Show top 10
    top_10 = sorted_types[:10]
    for rtype, count in top_10:
        table.add_row(rtype, f"{count:,}")

    # Show "others" summary if more than 10 types
    if len(sorted_types) > 10:
        other_types = sorted_types[10:]
        other_count = sum(count for _, count in other_types)
        table.add_section()
        table.add_row(
            f"[dim]+ {len(other_types)} other types[/]", f"[dim]{other_count:,}[/]"
        )

    console.print(table)

    if stats["has_cycles"]:
        console.print(
            "[yellow]Warning:[/] Dependency graph contains cycles!",
            style="bold yellow",
        )


def print_next_steps() -> None:
    """Print suggested next steps after a scan."""
    from replimap.cli.utils.tips import show_random_tip

    next_steps = """[bold]replimap graph[/]      Visualize infrastructure dependencies
[bold]replimap audit[/]     Check for security and cost issues
[bold]replimap clone[/]     Generate Terraform for staging environment
[bold]replimap deps[/]      Explore resource dependencies"""

    console.print()
    console.print(Panel(next_steps, title="📋 Next Steps", border_style="dim"))

    # Occasionally show a pro tip
    show_random_tip(console, probability=0.3)


__all__ = [
    "print_scan_summary",
    "print_graph_stats",
    "print_next_steps",
]
