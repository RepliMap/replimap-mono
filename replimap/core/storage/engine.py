"""
UnifiedGraphEngine - Unified facade for graph operations.

Key Design Decisions:
1. Single SQLite backend for all scales
2. Mode selection based on cache_dir parameter only
3. NetworkX projection on-demand for complex analysis

Note: This is distinct from replimap.core.graph_engine.GraphEngine,
which is the existing NetworkX-based graph for resource traversal.
This module provides the unified storage layer.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from .base import Edge, Node
from .sqlite_backend import SQLiteBackend

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class UnifiedGraphEngine:
    """
    Unified graph engine with SQLite backend.

    Mode Selection (Simplified):
    - cache_dir provided → File-based SQLite (persistent)
    - cache_dir is None → Memory SQLite (ephemeral)

    No resource count threshold - mode is based on user intent.

    Example:
        # Memory mode (ephemeral, fast)
        engine = UnifiedGraphEngine()
        engine.add_nodes([...])

        # File mode (persistent)
        engine = UnifiedGraphEngine(cache_dir="~/.replimap/cache/my-profile")
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        db_path: str | None = None,
    ) -> None:
        """
        Initialize graph engine.

        Args:
            cache_dir: Directory for persistent storage (creates graph.db)
            db_path: Direct database path (overrides cache_dir)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None

        # Determine database path
        if db_path:
            self._db_path = db_path
        elif self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._db_path = str(self.cache_dir / "graph.db")
        else:
            self._db_path = ":memory:"

        self._backend = SQLiteBackend(db_path=self._db_path)

        mode = "memory" if self._db_path == ":memory:" else "file"
        logger.info(f"UnifiedGraphEngine initialized ({mode} mode)")

    @property
    def backend(self) -> SQLiteBackend:
        """Get the underlying SQLite backend."""
        return self._backend

    @property
    def is_persistent(self) -> bool:
        """Check if this engine uses persistent storage."""
        return self._db_path != ":memory:"

    # =========================================================
    # NODE OPERATIONS
    # =========================================================

    def add_node(self, node: Node) -> None:
        """Add a single node to the graph."""
        self._backend.add_node(node)

    def add_nodes(self, nodes: list[Node]) -> int:
        """Add multiple nodes in batch. Returns count added."""
        return self._backend.add_nodes_batch(nodes)

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        return self._backend.get_node(node_id)

    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        return self._backend.get_nodes_by_type(node_type)

    def search(self, query: str, limit: int = 100) -> list[Node]:
        """Search nodes by text query."""
        return self._backend.search_nodes(query, limit)

    def get_all_nodes(self) -> Iterator[Node]:
        """Iterate over all nodes."""
        return self._backend.get_all_nodes()

    def node_count(self) -> int:
        """Get total number of nodes."""
        return self._backend.node_count()

    # =========================================================
    # EDGE OPERATIONS
    # =========================================================

    def add_edge(self, edge: Edge) -> None:
        """Add a single edge to the graph."""
        self._backend.add_edge(edge)

    def add_edges(self, edges: list[Edge]) -> int:
        """Add multiple edges in batch. Returns count added."""
        return self._backend.add_edges_batch(edges)

    def get_edges_from(self, node_id: str) -> list[Edge]:
        """Get all edges originating from a node."""
        return self._backend.get_edges_from(node_id)

    def get_edges_to(self, node_id: str) -> list[Edge]:
        """Get all edges pointing to a node."""
        return self._backend.get_edges_to(node_id)

    def edge_count(self) -> int:
        """Get total number of edges."""
        return self._backend.edge_count()

    # =========================================================
    # TRAVERSAL
    # =========================================================

    def get_neighbors(self, node_id: str, direction: str = "both") -> list[Node]:
        """Get neighboring nodes. Direction: 'in', 'out', or 'both'."""
        return self._backend.get_neighbors(node_id, direction)

    def find_path(
        self, source_id: str, target_id: str, max_depth: int = 10
    ) -> list[str] | None:
        """Find shortest path between two nodes."""
        return self._backend.find_path(source_id, target_id, max_depth)

    # =========================================================
    # ANALYTICS
    # =========================================================

    def get_node_degree(self, node_id: str) -> tuple[int, int]:
        """Get (in_degree, out_degree) for a node."""
        return self._backend.get_node_degree(node_id)

    def get_high_degree_nodes(self, top_n: int = 10) -> list[tuple[Node, int]]:
        """Get nodes with highest total degree."""
        return self._backend.get_high_degree_nodes(top_n)

    def get_impact_analysis(self, node_id: str) -> dict[str, Any]:
        """Analyze blast radius of a resource."""
        in_deg, out_deg = self.get_node_degree(node_id)

        # Get dependents (who depends on this)
        dependents = []
        for edge in self._backend.get_edges_to(node_id):
            node = self.get_node(edge.source_id)
            if node:
                dependents.append({"id": node.id, "type": node.type, "name": node.name})

        # Get dependencies (what this depends on)
        dependencies = []
        for edge in self._backend.get_edges_from(node_id):
            node = self.get_node(edge.target_id)
            if node:
                dependencies.append(
                    {"id": node.id, "type": node.type, "name": node.name}
                )

        return {
            "node_id": node_id,
            "in_degree": in_deg,
            "out_degree": out_deg,
            "blast_radius": len(dependents),
            "dependency_count": len(dependencies),
            "dependents": dependents,
            "dependencies": dependencies,
        }

    def find_single_points_of_failure(
        self, min_dependents: int = 3
    ) -> list[dict[str, Any]]:
        """Find resources with high blast radius (many dependents)."""
        spofs = []
        for node, degree in self.get_high_degree_nodes(top_n=50):
            in_deg, _ = self.get_node_degree(node.id)
            if in_deg >= min_dependents:
                spofs.append(
                    {
                        "id": node.id,
                        "type": node.type,
                        "name": node.name,
                        "dependent_count": in_deg,
                        "category": node.category.value,
                    }
                )
        return sorted(spofs, key=lambda x: x["dependent_count"], reverse=True)

    # =========================================================
    # NETWORKX PROJECTION (On-demand for complex analysis)
    # =========================================================

    def to_networkx(self, lightweight: bool = True) -> Any:
        """
        Project graph data to NetworkX for complex analysis.

        This creates a TEMPORARY in-memory graph for algorithms like:
        - Betweenness Centrality
        - PageRank
        - Community Detection
        - Clustering Coefficient

        Args:
            lightweight: If True, only load IDs (faster). If False, load full attributes.

        Returns:
            nx.DiGraph: NetworkX directed graph

        Usage:
            G = engine.to_networkx()
            centrality = nx.betweenness_centrality(G)
            pagerank = nx.pagerank(G)
        """
        try:
            import networkx as nx
        except ImportError as e:
            raise ImportError(
                "NetworkX required for complex analysis. "
                "Install with: pip install networkx"
            ) from e

        G: nx.DiGraph = nx.DiGraph()

        # Add nodes
        for node in self.get_all_nodes():
            if lightweight:
                G.add_node(node.id, type=node.type, name=node.name)
            else:
                G.add_node(node.id, **node.to_dict())

        # Add edges
        for edge in self._backend.get_all_edges():
            G.add_edge(
                edge.source_id,
                edge.target_id,
                relation=edge.relation,
                weight=edge.weight,
            )

        logger.info(
            f"Projected to NetworkX: {G.number_of_nodes()} nodes, "
            f"{G.number_of_edges()} edges"
        )
        return G

    # =========================================================
    # SNAPSHOT
    # =========================================================

    def snapshot(self, target_path: str | None = None) -> str:
        """
        Create a snapshot of current graph state.

        Args:
            target_path: Where to save snapshot. If None, auto-generates path.

        Returns:
            Path to created snapshot file.
        """
        if target_path is None:
            if self.cache_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                target_path = str(self.cache_dir / f"snapshot_{timestamp}.db")
            else:
                raise ValueError("target_path required for memory-mode graphs")

        self._backend.snapshot(target_path)
        return target_path

    @classmethod
    def load_snapshot(cls, snapshot_path: str) -> UnifiedGraphEngine:
        """Load a snapshot as a new UnifiedGraphEngine instance."""
        return cls(db_path=snapshot_path)

    # =========================================================
    # RESOURCE EXPORT (for drift detection)
    # =========================================================

    def get_all_resources(self) -> list[dict[str, Any]]:
        """Export all resources as dictionaries (for drift detection)."""
        return [node.to_dict() for node in self.get_all_nodes()]

    # =========================================================
    # PERSISTENCE
    # =========================================================

    def clear(self) -> None:
        """Clear all data from the graph."""
        self._backend.clear()

    def close(self) -> None:
        """Close the engine and release resources."""
        self._backend.close()

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata key-value pair."""
        self._backend.set_metadata(key, value)

    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value by key."""
        return self._backend.get_metadata(key)

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        return self._backend.get_stats()

    # =========================================================
    # CLASS METHODS
    # =========================================================

    @classmethod
    def load_from_cache(
        cls, profile: str, cache_base: str | None = None
    ) -> UnifiedGraphEngine:
        """Load graph from profile cache directory."""
        if cache_base is None:
            cache_base = str(Path.home() / ".replimap" / "cache")

        cache_dir = Path(cache_base) / profile
        db_path = cache_dir / "graph.db"

        if not db_path.exists():
            raise FileNotFoundError(f"No cached graph for profile: {profile}")

        return cls(db_path=str(db_path))

    # =========================================================
    # CONTEXT MANAGER
    # =========================================================

    def __enter__(self) -> UnifiedGraphEngine:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        mode = "memory" if self._db_path == ":memory:" else "file"
        return (
            f"UnifiedGraphEngine(mode={mode}, "
            f"nodes={self.node_count()}, edges={self.edge_count()})"
        )
