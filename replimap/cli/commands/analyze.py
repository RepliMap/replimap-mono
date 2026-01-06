"""
Analyze command for RepliMap CLI.

Provides infrastructure analysis capabilities:
- Critical resource identification
- Single point of failure detection
- Blast radius computation
- Graph simplification (transitive reduction)
- Attack surface analysis

Usage:
    # Analyze a saved graph (JSON or SQLite)
    replimap analyze graph.db --critical
    replimap analyze graph.json --critical

    # Compute blast radius for a resource
    replimap analyze graph.db --blast-radius vpc-12345

    # Simplify graph (transitive reduction)
    replimap analyze graph.db --simplify --output reduced.db

    # Full analysis report
    replimap analyze graph.db --report
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from replimap.core.analysis.centrality import (
    AttackSurfaceAnalyzer,
    CentralityAnalyzer,
    CriticalityLevel,
    CriticalResourceFinder,
)
from replimap.core.graph.algorithms import GraphSimplifier, TransitiveReducer

if TYPE_CHECKING:
    # Use union type for type hints since we support both
    from replimap.core.graph_engine import GraphEngine
    from replimap.core.unified_storage import GraphEngineAdapter

    GraphType = GraphEngine | GraphEngineAdapter

console = Console()


def _load_graph(graph_file: Path):
    """
    Load a graph from file (supports both JSON and SQLite formats).

    Args:
        graph_file: Path to the graph file (.json or .db)

    Returns:
        GraphEngine or GraphEngineAdapter instance
    """
    suffix = graph_file.suffix.lower()

    if suffix == ".db":
        # SQLite format - use new adapter
        from replimap.core.unified_storage import GraphEngineAdapter

        return GraphEngineAdapter(db_path=str(graph_file))
    elif suffix == ".json":
        # Legacy JSON format - use old GraphEngine
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)
    else:
        # Try to detect format by content
        try:
            # Try SQLite first (check for SQLite header)
            with open(graph_file, "rb") as f:
                header = f.read(16)
                if header.startswith(b"SQLite format"):
                    from replimap.core.unified_storage import GraphEngineAdapter

                    return GraphEngineAdapter(db_path=str(graph_file))
        except Exception:
            pass

        # Default to JSON
        from replimap.core.graph_engine import GraphEngine

        return GraphEngine.load(graph_file)


def register(app: typer.Typer) -> None:
    """Register the analyze command with the app."""

    @app.command("analyze")
    def analyze_command(
        graph_file: Path = typer.Argument(
            ...,
            help="Path to graph file (.db for SQLite, .json for legacy)",
            exists=True,
        ),
        critical: bool = typer.Option(
            False,
            "--critical",
            "-c",
            help="Find critical resources (SPOFs, high blast radius)",
        ),
        spof: bool = typer.Option(
            False,
            "--spof",
            help="Find single points of failure",
        ),
        blast_radius: str | None = typer.Option(
            None,
            "--blast-radius",
            "-b",
            help="Compute blast radius for a specific resource ID",
        ),
        simplify: bool = typer.Option(
            False,
            "--simplify",
            "-s",
            help="Perform transitive reduction to simplify graph",
        ),
        attack_surface: bool = typer.Option(
            False,
            "--attack-surface",
            "-a",
            help="Analyze attack surface (exposed/public resources)",
        ),
        report: bool = typer.Option(
            False,
            "--report",
            "-r",
            help="Generate comprehensive analysis report",
        ),
        top_n: int = typer.Option(
            10,
            "--top",
            "-n",
            help="Number of top results to show",
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="Output file for simplified graph (with --simplify)",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output results as JSON",
        ),
    ) -> None:
        """Analyze a resource dependency graph for critical infrastructure.

        This command loads a previously saved graph and performs various
        analyses to identify critical resources, single points of failure,
        and attack surface exposure.

        Examples:

            replimap analyze graph.db --critical

            replimap analyze graph.db --spof

            replimap analyze graph.db --blast-radius vpc-12345

            replimap analyze graph.db --simplify --output simplified.db

            replimap analyze graph.db --report
        """
        # Load the graph
        try:
            graph = _load_graph(graph_file)
        except Exception as e:
            console.print(f"[red]Error loading graph:[/] {e}")
            raise typer.Exit(1)

        console.print(
            f"[green]Loaded graph:[/] {graph.node_count} resources, "
            f"{graph.edge_count} dependencies"
        )
        console.print()

        # Track if any analysis was requested
        analysis_done = False

        # Critical resource analysis
        if critical or report:
            analysis_done = True
            _show_critical_analysis(graph, top_n, json_output)

        # Single point of failure analysis
        if spof and not critical:  # Avoid duplicate if --critical already shows SPOFs
            analysis_done = True
            _show_spof_analysis(graph, top_n, json_output)

        # Blast radius for specific resource
        if blast_radius:
            analysis_done = True
            _show_blast_radius(graph, blast_radius, json_output)

        # Simplify graph
        if simplify:
            analysis_done = True
            _simplify_graph(graph, output, json_output)

        # Attack surface analysis
        if attack_surface or report:
            analysis_done = True
            _show_attack_surface(graph, json_output)

        # If report, show graph stats too
        if report:
            _show_graph_stats(graph, json_output)

        # If no specific analysis requested, show summary
        if not analysis_done:
            _show_summary(graph)


def _show_critical_analysis(graph: Any, top_n: int, json_output: bool) -> None:
    """Display critical resource analysis."""
    finder = CriticalResourceFinder(graph)
    critical = finder.find_critical(top_n)

    if json_output:
        import json

        data = [
            {
                "resource_id": r.resource_id,
                "resource_type": r.resource_type,
                "level": r.level.value,
                "score": r.score,
                "blast_radius": r.blast_radius,
                "dependent_count": r.dependent_count,
                "factors": r.factors,
            }
            for r in critical
        ]
        console.print(json.dumps(data, indent=2))
        return

    console.print(
        Panel(
            f"[bold]Critical Resource Analysis[/]\n"
            f"Analyzing {graph.node_count} resources for criticality...",
            style="blue",
        )
    )

    if not critical:
        console.print("[yellow]No critical resources found.[/]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Rank", style="dim", width=4)
    table.add_column("Resource ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Level", width=10)
    table.add_column("Score", justify="right", width=6)
    table.add_column("Blast Radius", justify="right", width=12)
    table.add_column("Factors", style="dim")

    level_colors = {
        CriticalityLevel.CRITICAL: "bold red",
        CriticalityLevel.HIGH: "red",
        CriticalityLevel.MEDIUM: "yellow",
        CriticalityLevel.LOW: "green",
    }

    for i, result in enumerate(critical, 1):
        level_style = level_colors.get(result.level, "white")
        table.add_row(
            str(i),
            result.resource_id[:40],
            result.resource_type,
            f"[{level_style}]{result.level.value.upper()}[/]",
            f"{result.score:.1f}",
            str(result.blast_radius),
            ", ".join(result.factors[:2]) if result.factors else "-",
        )

    console.print(table)
    console.print()


def _show_spof_analysis(graph: Any, top_n: int, json_output: bool) -> None:
    """Display single point of failure analysis."""
    analyzer = CentralityAnalyzer(graph)
    spofs = analyzer.find_single_points_of_failure()[:top_n]

    if json_output:
        import json

        data = [
            {
                "resource_id": s.resource_id,
                "resource_type": s.resource_type,
                "dependent_count": s.dependent_count,
                "percentile": s.in_degree_percentile,
                "dependents": s.dependents[:10],
            }
            for s in spofs
        ]
        console.print(json.dumps(data, indent=2))
        return

    console.print(Panel("[bold]Single Points of Failure[/]", style="red"))

    if not spofs:
        console.print("[green]No single points of failure detected.[/]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Resource ID", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Dependents", justify="right")
    table.add_column("Percentile", justify="right")

    for spof in spofs:
        table.add_row(
            spof.resource_id[:40],
            spof.resource_type,
            str(spof.dependent_count),
            f"{spof.in_degree_percentile:.0f}%",
        )

    console.print(table)
    console.print()


def _show_blast_radius(graph: Any, resource_id: str, json_output: bool) -> None:
    """Display blast radius for a specific resource."""
    analyzer = CentralityAnalyzer(graph)
    result = analyzer.compute_blast_radius(resource_id)

    if json_output:
        import json

        data = {
            "resource_id": result.resource_id,
            "affected_count": result.affected_count,
            "depth": result.depth,
            "by_type": result.by_type,
            "affected_resources": result.affected_resources,
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(
        Panel(
            f"[bold]Blast Radius Analysis[/]\nResource: {resource_id}",
            style="yellow",
        )
    )

    if result.affected_count == 0:
        console.print(f"[green]Resource '{resource_id}' has no dependents.[/]")
        if resource_id not in [r.id for r in graph.get_all_resources()]:
            console.print("[yellow]Note: Resource not found in graph.[/]")
        return

    console.print(f"[red]Affected Resources:[/] {result.affected_count}")
    console.print(f"[yellow]Maximum Cascade Depth:[/] {result.depth}")
    console.print()

    if result.by_type:
        table = Table(title="Affected by Type", show_header=True)
        table.add_column("Resource Type", style="cyan")
        table.add_column("Count", justify="right")

        for rtype, count in sorted(
            result.by_type.items(), key=lambda x: x[1], reverse=True
        ):
            table.add_row(rtype, str(count))

        console.print(table)
        console.print()


def _simplify_graph(graph: Any, output: Path | None, json_output: bool) -> None:
    """Perform transitive reduction and optionally save."""
    simplifier = GraphSimplifier(graph)
    stats_before = simplifier.compute_stats()

    reducer = TransitiveReducer(graph)
    result = reducer.reduce(in_place=True)

    stats_after = simplifier.compute_stats()

    if json_output:
        import json

        data = {
            "original_edges": result.original_edge_count,
            "reduced_edges": result.reduced_edge_count,
            "removed": result.edges_removed,
            "reduction_ratio": result.reduction_ratio,
            "removed_edges": result.removed_edges,
        }
        console.print(json.dumps(data, indent=2))
    else:
        console.print(
            Panel("[bold]Graph Simplification (Transitive Reduction)[/]", style="blue")
        )

        console.print(f"[dim]Before:[/] {result.original_edge_count} edges")
        console.print(f"[green]After:[/]  {result.reduced_edge_count} edges")
        console.print(
            f"[cyan]Removed:[/] {result.edges_removed} redundant edges "
            f"({result.reduction_ratio:.1f}% reduction)"
        )
        console.print()

        console.print(
            f"Density: {stats_before.density:.4f} → {stats_after.density:.4f}"
        )
        console.print(f"Complexity Score: {simplifier.get_complexity_score():.2f}/1.00")
        console.print()

    if output:
        graph.save(output)
        console.print(f"[green]Simplified graph saved to:[/] {output}")
        console.print()


def _show_attack_surface(graph: Any, json_output: bool) -> None:
    """Display attack surface analysis."""
    analyzer = AttackSurfaceAnalyzer(graph)
    result = analyzer.compute_attack_surface()

    if json_output:
        import json

        data = {
            "risk_score": result.risk_score,
            "exposed_resources": result.exposed_resources,
            "high_privilege_resources": result.high_privilege_resources,
            "public_resources": result.public_resources,
        }
        console.print(json.dumps(data, indent=2))
        return

    # Determine risk level color
    if result.risk_score >= 60:
        risk_style = "bold red"
        risk_label = "HIGH RISK"
    elif result.risk_score >= 30:
        risk_style = "yellow"
        risk_label = "MEDIUM RISK"
    else:
        risk_style = "green"
        risk_label = "LOW RISK"

    console.print(
        Panel(
            f"[bold]Attack Surface Analysis[/]\n"
            f"[{risk_style}]Risk Score: {result.risk_score:.1f}/100 ({risk_label})[/]",
            style="magenta",
        )
    )

    table = Table(show_header=True, header_style="bold")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Resources", style="dim")

    def format_resources(resources: list[str], max_show: int = 3) -> str:
        if not resources:
            return "-"
        shown = resources[:max_show]
        result_str = ", ".join(r[:20] for r in shown)
        if len(resources) > max_show:
            result_str += f" (+{len(resources) - max_show} more)"
        return result_str

    table.add_row(
        "Internet Exposed",
        str(len(result.exposed_resources)),
        format_resources(result.exposed_resources),
    )
    table.add_row(
        "High Privilege",
        str(len(result.high_privilege_resources)),
        format_resources(result.high_privilege_resources),
    )
    table.add_row(
        "Public Access",
        str(len(result.public_resources)),
        format_resources(result.public_resources),
    )

    console.print(table)
    console.print()


def _show_graph_stats(graph: Any, json_output: bool) -> None:
    """Display graph statistics."""
    simplifier = GraphSimplifier(graph)
    stats = simplifier.compute_stats()

    if json_output:
        import json

        data = {
            "nodes": stats.node_count,
            "edges": stats.edge_count,
            "density": stats.density,
            "avg_degree": stats.avg_degree,
            "max_in_degree": stats.max_in_degree,
            "max_out_degree": stats.max_out_degree,
            "has_cycles": stats.has_cycles,
            "components": stats.connected_components,
            "complexity_score": simplifier.get_complexity_score(),
        }
        console.print(json.dumps(data, indent=2))
        return

    console.print(Panel("[bold]Graph Statistics[/]", style="cyan"))

    table = Table(show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right")

    table.add_row("Nodes", str(stats.node_count))
    table.add_row("Edges", str(stats.edge_count))
    table.add_row("Density", f"{stats.density:.4f}")
    table.add_row("Avg Degree", f"{stats.avg_degree:.2f}")
    table.add_row(
        "Max In-Degree", f"{stats.max_in_degree} ({stats.max_in_degree_node or 'N/A'})"
    )
    table.add_row(
        "Max Out-Degree",
        f"{stats.max_out_degree} ({stats.max_out_degree_node or 'N/A'})",
    )
    table.add_row("Has Cycles", "Yes" if stats.has_cycles else "No")
    table.add_row("Components", str(stats.connected_components))
    table.add_row("Complexity Score", f"{simplifier.get_complexity_score():.2f}/1.00")

    console.print(table)
    console.print()


def _show_summary(graph: Any) -> None:
    """Show a summary when no specific analysis is requested."""
    console.print(
        Panel(
            "[bold]Graph Analysis Options[/]\n\n"
            "Use one of the following options:\n"
            "  --critical, -c     Find critical resources\n"
            "  --spof             Find single points of failure\n"
            "  --blast-radius ID  Compute blast radius\n"
            "  --simplify, -s     Transitive reduction\n"
            "  --attack-surface   Analyze attack surface\n"
            "  --report, -r       Full analysis report",
            style="blue",
        )
    )

    # Show quick stats
    simplifier = GraphSimplifier(graph)
    stats = simplifier.compute_stats()

    console.print("\n[dim]Quick stats:[/]")
    console.print(f"  Resources: {stats.node_count}")
    console.print(f"  Dependencies: {stats.edge_count}")
    console.print(f"  Cycles: {'Yes' if stats.has_cycles else 'No'}")
    console.print(f"  Complexity: {simplifier.get_complexity_score():.2f}/1.00")
