"""
Graph algorithms for dependency graph analysis.

This module provides algorithms for simplifying and analyzing
AWS resource dependency graphs, including:

- Transitive Reduction: Remove redundant edges for cleaner visualization
- Graph Statistics: Analyze graph properties and complexity

Transitive Reduction:
    Given a directed graph G, the transitive reduction G' is the minimal
    graph with the same reachability. If A → B → C exists, and also A → C,
    the edge A → C is redundant and can be removed.

    This is particularly useful for:
    - Cleaner Terraform dependency visualization
    - Reducing visual clutter in large graphs
    - Identifying true "direct" dependencies

Usage:
    from replimap.core.graph.algorithms import TransitiveReducer

    reducer = TransitiveReducer(graph_engine)
    result = reducer.reduce()
    print(f"Removed {result.edges_removed} redundant edges")
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


@dataclass
class GraphStats:
    """
    Statistics about a dependency graph.

    Attributes:
        node_count: Total number of nodes
        edge_count: Total number of edges
        density: Graph density (edges / possible edges)
        avg_degree: Average node degree
        max_in_degree: Maximum in-degree (most dependencies)
        max_out_degree: Maximum out-degree (most dependents)
        has_cycles: Whether the graph contains cycles
        cycle_count: Number of simple cycles detected
        connected_components: Number of weakly connected components
        isolated_nodes: Nodes with no edges
    """

    node_count: int = 0
    edge_count: int = 0
    density: float = 0.0
    avg_degree: float = 0.0
    max_in_degree: int = 0
    max_out_degree: int = 0
    max_in_degree_node: str | None = None
    max_out_degree_node: str | None = None
    has_cycles: bool = False
    cycle_count: int = 0
    connected_components: int = 0
    isolated_nodes: list[str] = field(default_factory=list)


@dataclass
class ReductionResult:
    """
    Result of transitive reduction operation.

    Attributes:
        original_edge_count: Number of edges before reduction
        reduced_edge_count: Number of edges after reduction
        edges_removed: Number of redundant edges removed
        removed_edges: List of (source, target) tuples that were removed
        reduction_ratio: Percentage of edges removed
    """

    original_edge_count: int
    reduced_edge_count: int
    edges_removed: int
    removed_edges: list[tuple[str, str]]
    reduction_ratio: float

    @property
    def summary(self) -> str:
        """Human-readable summary of the reduction."""
        return (
            f"Transitive reduction: {self.original_edge_count} → "
            f"{self.reduced_edge_count} edges "
            f"(-{self.edges_removed}, {self.reduction_ratio:.1f}% reduction)"
        )


class TransitiveReducer:
    """
    Performs transitive reduction on dependency graphs.

    Transitive reduction removes "shortcut" edges that are implied
    by longer paths. For example:
        A → B → C
        A → C  (redundant, can reach C via B)

    After reduction, only A → B and B → C remain.

    This is useful for:
    - Cleaner dependency visualization
    - Identifying direct vs. transitive dependencies
    - Reducing Terraform graph complexity

    Thread Safety:
        This class creates a copy of the graph for analysis,
        so it's safe to use while the original graph is being modified.

    Performance:
        Time complexity: O(V * E) for reachability checks
        Space complexity: O(V + E) for the working copy
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the reducer with a graph.

        Args:
            graph: The GraphEngine to analyze
        """
        self._graph = graph
        self._redundant_edges: list[tuple[str, str]] = []

    def get_redundant_edges(self) -> list[tuple[str, str]]:
        """
        Find all redundant (transitively implied) edges.

        An edge (u, v) is redundant if there exists a path u → ... → v
        of length >= 2 (i.e., going through at least one intermediate node).

        Returns:
            List of (source, target) tuples representing redundant edges
        """
        # Work on a copy to avoid modifying the original
        g = self._graph._graph.copy()
        redundant: list[tuple[str, str]] = []

        # For each edge, check if there's an alternative path
        for u, v in list(g.edges()):
            # Temporarily remove the edge
            g.remove_edge(u, v)

            # Check if v is still reachable from u
            if nx.has_path(g, u, v):
                redundant.append((u, v))
            else:
                # Edge is essential, restore it
                g.add_edge(u, v)

        self._redundant_edges = redundant
        return redundant

    def reduce(self, in_place: bool = False) -> ReductionResult:
        """
        Perform transitive reduction on the graph.

        Args:
            in_place: If True, modify the original graph.
                     If False (default), only compute what would be removed.

        Returns:
            ReductionResult with details about the reduction
        """
        original_count = self._graph.edge_count

        # Find redundant edges
        redundant = self.get_redundant_edges()

        if in_place and redundant:
            # Remove redundant edges from the actual graph
            for u, v in redundant:
                if self._graph._graph.has_edge(u, v):
                    self._graph._graph.remove_edge(u, v)
                    # Also update the ResourceNode's dependencies
                    if u in self._graph._resources:
                        resource = self._graph._resources[u]
                        if v in resource.dependencies:
                            resource.dependencies.remove(v)

            logger.info(f"Removed {len(redundant)} redundant edges from graph")

        reduced_count = original_count - len(redundant)
        ratio = (len(redundant) / original_count * 100) if original_count > 0 else 0.0

        return ReductionResult(
            original_edge_count=original_count,
            reduced_edge_count=reduced_count,
            edges_removed=len(redundant),
            removed_edges=redundant,
            reduction_ratio=ratio,
        )

    def get_reduction_preview(self) -> dict[str, list[str]]:
        """
        Preview what edges would be removed, grouped by source.

        Useful for understanding the impact before applying reduction.

        Returns:
            Dict mapping source node IDs to lists of target IDs that would be removed
        """
        redundant = self.get_redundant_edges()
        preview: dict[str, list[str]] = {}

        for source, target in redundant:
            if source not in preview:
                preview[source] = []
            preview[source].append(target)

        return preview


class GraphSimplifier:
    """
    High-level interface for graph simplification operations.

    Combines multiple simplification techniques:
    - Transitive reduction
    - Statistics computation
    - Complexity analysis

    Usage:
        simplifier = GraphSimplifier(graph)
        stats_before = simplifier.compute_stats()

        result = simplifier.simplify()

        stats_after = simplifier.compute_stats()
        print(f"Density: {stats_before.density:.3f} → {stats_after.density:.3f}")
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the simplifier.

        Args:
            graph: The GraphEngine to simplify
        """
        self._graph = graph

    def compute_stats(self) -> GraphStats:
        """
        Compute comprehensive statistics about the graph.

        Returns:
            GraphStats with all computed metrics
        """
        g = self._graph._graph
        n = g.number_of_nodes()
        m = g.number_of_edges()

        # Density: actual edges / possible edges
        max_edges = n * (n - 1) if n > 1 else 1
        density = m / max_edges if max_edges > 0 else 0.0

        # Degree statistics
        in_degrees = dict(g.in_degree())
        out_degrees = dict(g.out_degree())

        max_in = max(in_degrees.values()) if in_degrees else 0
        max_out = max(out_degrees.values()) if out_degrees else 0

        max_in_node = None
        max_out_node = None
        if in_degrees:
            max_in_node = max(in_degrees, key=lambda k: in_degrees[k])
        if out_degrees:
            max_out_node = max(out_degrees, key=lambda k: out_degrees[k])

        # Average degree
        avg_degree = sum(d for _, d in g.degree()) / n if n > 0 else 0.0

        # Cycles
        has_cycles = self._graph.has_cycles()
        cycle_count = 0
        if has_cycles:
            try:
                cycles = list(nx.simple_cycles(g))
                cycle_count = len(cycles)
            except Exception:
                cycle_count = -1  # Unknown

        # Connected components (weakly connected for digraph)
        components = nx.number_weakly_connected_components(g)

        # Isolated nodes (no edges at all)
        isolated = [
            node for node in g.nodes() if g.in_degree(node) == 0 and g.out_degree(node) == 0
        ]

        return GraphStats(
            node_count=n,
            edge_count=m,
            density=density,
            avg_degree=avg_degree,
            max_in_degree=max_in,
            max_out_degree=max_out,
            max_in_degree_node=max_in_node,
            max_out_degree_node=max_out_node,
            has_cycles=has_cycles,
            cycle_count=cycle_count,
            connected_components=components,
            isolated_nodes=isolated,
        )

    def simplify(self, apply: bool = True) -> ReductionResult:
        """
        Perform transitive reduction to simplify the graph.

        Args:
            apply: If True, modify the graph in place.
                  If False, only compute what would change.

        Returns:
            ReductionResult with reduction details
        """
        reducer = TransitiveReducer(self._graph)
        return reducer.reduce(in_place=apply)

    def get_complexity_score(self) -> float:
        """
        Compute a complexity score for the graph.

        Higher scores indicate more complex dependency structures.
        Score is based on:
        - Edge density
        - Cycle presence
        - Maximum degree

        Returns:
            Complexity score from 0.0 (trivial) to 1.0 (very complex)
        """
        stats = self.compute_stats()

        # Base complexity from density (0-0.4 contribution)
        density_score = min(stats.density * 4, 0.4)

        # Cycle penalty (0-0.3 contribution)
        cycle_score = 0.3 if stats.has_cycles else 0.0

        # Degree concentration (0-0.3 contribution)
        # High max degree relative to average indicates bottlenecks
        if stats.avg_degree > 0:
            degree_ratio = stats.max_in_degree / (stats.avg_degree * 2)
            degree_score = min(degree_ratio * 0.3, 0.3)
        else:
            degree_score = 0.0

        return min(density_score + cycle_score + degree_score, 1.0)

    def get_simplification_report(self) -> str:
        """
        Generate a human-readable simplification report.

        Returns:
            Formatted report string
        """
        stats = self.compute_stats()
        reducer = TransitiveReducer(self._graph)
        result = reducer.reduce(in_place=False)

        lines = [
            "Graph Simplification Report",
            "=" * 40,
            "",
            "Current State:",
            f"  Nodes: {stats.node_count}",
            f"  Edges: {stats.edge_count}",
            f"  Density: {stats.density:.4f}",
            f"  Cycles: {'Yes' if stats.has_cycles else 'No'}",
            f"  Components: {stats.connected_components}",
            "",
            "Transitive Reduction:",
            f"  Redundant edges: {result.edges_removed}",
            f"  Reduction: {result.reduction_ratio:.1f}%",
            f"  After reduction: {result.reduced_edge_count} edges",
            "",
            "Complexity Score:",
            f"  {self.get_complexity_score():.2f} / 1.00",
        ]

        if stats.max_in_degree_node:
            lines.append("")
            lines.append("Key Nodes:")
            lines.append(
                f"  Most dependencies: {stats.max_in_degree_node} "
                f"({stats.max_in_degree} deps)"
            )
        if stats.max_out_degree_node:
            lines.append(
                f"  Most dependents: {stats.max_out_degree_node} "
                f"({stats.max_out_degree} dependents)"
            )

        return "\n".join(lines)
