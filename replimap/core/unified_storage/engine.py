"""
UnifiedGraphEngine - Unified facade for graph operations.

Key Design Decisions:
1. Single SQLite backend for all scales
2. Mode selection based on cache_dir parameter only
3. NetworkX projection on-demand for complex analysis
4. Defense-in-depth sanitization validation at storage layer

Edge Direction Convention:
    source_id DEPENDS ON target_id
    source_id -> target_id means "source uses/needs target"

    Example:
        aws_instance -> aws_security_group
        (Instance depends on/uses Security Group)

    Therefore:
        get_dependencies(X): Find targets reachable from X (what X needs)
        get_dependents(X): Find sources pointing to X (what needs X / blast radius)
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import Edge, Node
from .sqlite_backend import SQLiteBackend

if TYPE_CHECKING:
    from replimap.core.security.global_sanitizer import GlobalSanitizer

logger = logging.getLogger(__name__)

# Default max depth for recursive queries (supports complex microservice architectures)
DEFAULT_MAX_DEPTH = 20


class SanitizationError(Exception):
    """Raised when sanitization validation fails."""

    pass


class UnifiedGraphEngine:
    """
    Unified graph engine with SQLite backend and defense-in-depth sanitization.

    Mode Selection (Simplified):
    - cache_dir provided → File-based SQLite (persistent)
    - cache_dir is None → Memory SQLite (ephemeral)

    Defense-in-Depth:
    Even if scanners fail to sanitize, storage layer will:
    1. Validate no sensitive patterns exist
    2. Block storage if validation fails (strict mode)
    3. Log security warnings

    Example:
        # Memory mode (ephemeral, fast)
        engine = UnifiedGraphEngine()
        engine.add_nodes([...])

        # File mode (persistent)
        engine = UnifiedGraphEngine(cache_dir="~/.replimap/cache/my-profile")

        # Validate cache security
        report = engine.validate_cache_security()
        if not report['is_secure']:
            logger.error(f"Cache contains sensitive data: {report['findings']}")
    """

    def __init__(
        self,
        cache_dir: str | None = None,
        db_path: str | None = None,
        strict_mode: bool = True,
    ) -> None:
        """
        Initialize graph engine.

        Args:
            cache_dir: Directory for persistent storage (creates graph.db)
            db_path: Direct database path (overrides cache_dir)
            strict_mode: If True, block storage of unsanitized data (default: True)
        """
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.strict_mode = strict_mode

        # Lazy-loaded sanitizer (avoid circular imports)
        self._sanitizer: GlobalSanitizer | None = None

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

    def _get_sanitizer(self) -> GlobalSanitizer:
        """Get or create sanitizer (lazy loading to avoid circular imports)."""
        if self._sanitizer is None:
            from replimap.core.security.global_sanitizer import GlobalSanitizer

            self._sanitizer = GlobalSanitizer()
        return self._sanitizer

    def _validate_node_security(self, node: Node) -> tuple[bool, list[str]]:
        """
        Validate that a node's attributes don't contain sensitive patterns.

        Args:
            node: The node to validate

        Returns:
            Tuple of (is_safe, list_of_findings)
        """
        from replimap.core.security.patterns import SensitivePatternLibrary

        attributes = node.attributes or {}
        if not attributes:
            return True, []

        # Convert attributes to JSON string for pattern scanning
        try:
            attrs_str = json.dumps(attributes, default=str)
        except (TypeError, ValueError):
            # If we can't serialize, assume it's safe
            return True, []

        if SensitivePatternLibrary.contains_sensitive(attrs_str):
            _, findings = SensitivePatternLibrary.scan_text(attrs_str)
            return False, findings

        return True, []

    def add_node_safe(self, node: Node) -> None:
        """
        Add a node with security validation.

        Validates that the node's attributes don't contain sensitive patterns
        before adding to the graph.

        Args:
            node: The node to add

        Raises:
            SanitizationError: If sensitive data detected in strict mode
        """
        is_safe, findings = self._validate_node_security(node)

        if not is_safe:
            logger.error(
                f"SECURITY: Unsanitized data detected in node {node.id}! "
                f"Findings: {findings}"
            )

            if self.strict_mode:
                raise SanitizationError(
                    f"Cannot store node {node.id}: sensitive data detected. "
                    f"Findings: {findings}. "
                    "Ensure scanner calls _add_resource_safe()."
                )
            else:
                # Non-strict: sanitize now (with warning)
                logger.warning(
                    f"Performing emergency sanitization for node {node.id}. "
                    "This indicates a bug in the scanner."
                )
                sanitizer = self._get_sanitizer()
                node.attributes = sanitizer.sanitize(node.attributes)

        self._backend.add_node(node)

    def validate_cache_security(self) -> dict[str, Any]:
        """
        Scan entire cache for unsanitized sensitive data.

        Returns:
            Report with:
            - resources_checked: Number of nodes checked
            - issues_found: Number of nodes with sensitive data
            - findings: List of issues (node_id, type, patterns)
            - is_secure: True if no issues found
        """
        from replimap.core.security.patterns import SensitivePatternLibrary

        findings: list[dict[str, Any]] = []
        resources_checked = 0

        for node in self._backend.get_all_nodes():
            resources_checked += 1

            attributes = node.attributes or {}
            if not attributes:
                continue

            try:
                attrs_str = json.dumps(attributes, default=str)
            except (TypeError, ValueError):
                continue

            if SensitivePatternLibrary.contains_sensitive(attrs_str):
                _, patterns = SensitivePatternLibrary.scan_text(attrs_str)
                findings.append(
                    {
                        "node_id": node.id,
                        "node_type": node.type,
                        "patterns": patterns,
                    }
                )

        return {
            "resources_checked": resources_checked,
            "issues_found": len(findings),
            "findings": findings,
            "is_secure": len(findings) == 0,
        }

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

    def get_all_edges(self) -> Iterator[Edge]:
        """Iterate over all edges."""
        return self._backend.get_all_edges()

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
        for node, _degree in self.get_high_degree_nodes(top_n=50):
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
    # RECURSIVE DEPENDENCIES (SQL CTE Optimized)
    # =========================================================

    def get_dependencies(
        self,
        resource_id: str,
        recursive: bool = True,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> list[Node]:
        """
        Get all resources that this resource DEPENDS ON.

        Edge semantics: source_id -> target_id means "source depends on target"
        So we follow: resource_id -> target_id -> target_id -> ...

        Args:
            resource_id: Starting resource
            recursive: If True, get transitive dependencies
            max_depth: Maximum recursion depth (default 20)

        Returns:
            List of nodes that this resource depends on.

        Optimization: Uses SQL Recursive CTE (10-100x faster than Python recursion).
        """
        if not recursive:
            edges = self._backend.get_edges_from(resource_id)
            return [n for n in (self.get_node(e.target_id) for e in edges) if n]

        conn = self._backend._pool.get_reader()

        # Follow outgoing edges: source -> target (what this resource depends on)
        sql = """
        WITH RECURSIVE deps(node_id, depth) AS (
            -- Base case: direct dependencies
            SELECT target_id, 1 FROM edges WHERE source_id = ?
            UNION
            -- Recursive case: transitive dependencies
            SELECT e.target_id, d.depth + 1
            FROM deps d
            JOIN edges e ON e.source_id = d.node_id
            WHERE d.depth < ?
        )
        SELECT DISTINCT node_id FROM deps
        """

        rows = conn.execute(sql, (resource_id, max_depth)).fetchall()
        return [n for n in (self.get_node(row[0]) for row in rows) if n]

    def get_dependents(
        self,
        resource_id: str,
        recursive: bool = True,
        max_depth: int = DEFAULT_MAX_DEPTH,
    ) -> list[Node]:
        """
        Get all resources that DEPEND ON this resource (blast radius).

        Edge semantics: source_id -> target_id means "source depends on target"
        So we follow: source_id -> resource_id (backwards)

        Args:
            resource_id: Target resource
            recursive: If True, get transitive dependents
            max_depth: Maximum recursion depth (default 20)

        Returns:
            List of nodes that depend on this resource.

        Optimization: Uses SQL Recursive CTE.
        """
        if not recursive:
            edges = self._backend.get_edges_to(resource_id)
            return [n for n in (self.get_node(e.source_id) for e in edges) if n]

        conn = self._backend._pool.get_reader()

        # Follow incoming edges: source -> target (what depends on this resource)
        sql = """
        WITH RECURSIVE deps(node_id, depth) AS (
            -- Base case: direct dependents
            SELECT source_id, 1 FROM edges WHERE target_id = ?
            UNION
            -- Recursive case: transitive dependents
            SELECT e.source_id, d.depth + 1
            FROM deps d
            JOIN edges e ON e.target_id = d.node_id
            WHERE d.depth < ?
        )
        SELECT DISTINCT node_id FROM deps
        """

        rows = conn.execute(sql, (resource_id, max_depth)).fetchall()
        return [n for n in (self.get_node(row[0]) for row in rows) if n]

    # =========================================================
    # TOPOLOGICAL SORT & ORDERING
    # =========================================================

    def topological_sort(self) -> list[str]:
        """
        Return nodes in dependency order (dependencies before dependents).

        Critical for: Terraform resource generation order.

        Our edge semantics: source_id DEPENDS ON target_id
        (edges point from dependents to dependencies)

        NetworkX topological_sort returns nodes such that for every edge (u,v),
        u comes before v. Since our edges go dependent->dependency, NetworkX
        returns dependents before dependencies.

        We reverse to get dependencies before dependents (apply order).

        Returns:
            List of node IDs in topological order (dependencies first).

        Raises:
            ValueError: If graph has cycles (not a DAG).
        """
        G = self._get_networkx_graph()

        import networkx as nx

        if not nx.is_directed_acyclic_graph(G):
            cycles = self.find_cycles(limit=3)
            cycle_str = "; ".join([" -> ".join(c + [c[0]]) for c in cycles])
            raise ValueError(f"Graph has cycles, cannot sort. Found: {cycle_str}")

        # Reverse because our edges point dependent->dependency
        return list(reversed(list(nx.topological_sort(G))))

    def safe_apply_order(self) -> list[str]:
        """
        Get resource order for safe 'terraform apply'.

        Dependencies come before dependents.
        VPC must be created before Subnet, Subnet before Instance.
        """
        return self.topological_sort()

    def safe_destroy_order(self) -> list[str]:
        """
        Get resource order for safe 'terraform destroy'.

        Dependents come before dependencies (reverse of apply).
        Instance must be destroyed before Subnet, Subnet before VPC.
        """
        return list(reversed(self.topological_sort()))

    # =========================================================
    # CYCLE DETECTION
    # =========================================================

    def has_cycles(self) -> bool:
        """Check if graph contains cycles."""
        G = self._get_networkx_graph()

        import networkx as nx

        return not nx.is_directed_acyclic_graph(G)

    def find_cycles(self, limit: int = 10) -> list[list[str]]:
        """
        Find cycles in the graph.

        Args:
            limit: Maximum number of cycles to return.

        Returns:
            List of cycles, each cycle is a list of node IDs.
        """
        G = self._get_networkx_graph()

        import networkx as nx

        cycles: list[list[str]] = []
        try:
            for cycle in nx.simple_cycles(G):
                cycles.append(list(cycle))
                if len(cycles) >= limit:
                    break
        except nx.NetworkXError:
            pass

        return cycles

    # =========================================================
    # STRONGLY CONNECTED COMPONENTS
    # =========================================================

    def strongly_connected_components(self) -> list[set[str]]:
        """
        Find strongly connected components (Tarjan's algorithm).

        Useful for: Identifying tightly coupled resource groups.

        Returns:
            List of SCCs, each is a set of node IDs.
        """
        G = self._get_networkx_graph()

        import networkx as nx

        return [set(c) for c in nx.strongly_connected_components(G)]

    def get_largest_scc(self) -> set[str]:
        """Get the largest strongly connected component."""
        sccs = self.strongly_connected_components()
        return max(sccs, key=len) if sccs else set()

    # =========================================================
    # SUBGRAPH EXTRACTION
    # =========================================================

    def get_subgraph(
        self,
        node_ids: set[str],
        include_edges: bool = True,
    ) -> tuple[list[Node], list[Edge]]:
        """
        Extract a subgraph containing specified nodes.

        Args:
            node_ids: Set of node IDs to include
            include_edges: Whether to include edges between nodes

        Returns:
            Tuple of (nodes, edges) in the subgraph.
        """
        nodes = [n for n in (self.get_node(nid) for nid in node_ids) if n]

        edges: list[Edge] = []
        if include_edges and len(node_ids) > 1:
            for edge in self._backend.get_all_edges():
                if edge.source_id in node_ids and edge.target_id in node_ids:
                    edges.append(edge)

        return nodes, edges

    def get_connected_subgraph(
        self,
        start_id: str,
        max_depth: int = 3,
    ) -> tuple[list[Node], list[Edge]]:
        """
        Get all nodes connected to start_id within max_depth.

        Useful for: Visualizing local infrastructure around a resource.

        Args:
            start_id: Starting node ID
            max_depth: Maximum distance from start node

        Returns:
            Tuple of (nodes, edges) in the connected subgraph.
        """
        reachable = {start_id}

        deps = self.get_dependencies(start_id, recursive=True, max_depth=max_depth)
        dependents = self.get_dependents(start_id, recursive=True, max_depth=max_depth)

        reachable.update(n.id for n in deps)
        reachable.update(n.id for n in dependents)

        return self.get_subgraph(reachable, include_edges=True)

    # =========================================================
    # CENTRALITY METRICS
    # =========================================================

    def get_centrality(self, algorithm: str = "degree") -> dict[str, float]:
        """
        Calculate centrality metrics for importance analysis.

        Args:
            algorithm: One of "degree", "betweenness", "pagerank", "closeness"

        Returns:
            Dict mapping node_id to centrality score.

        Raises:
            ValueError: If algorithm is not recognized.
        """
        G = self._get_networkx_graph(lightweight=True)

        import networkx as nx

        algorithms: dict[str, Any] = {
            "degree": lambda g: {n: float(d) for n, d in g.degree()},
            "betweenness": nx.betweenness_centrality,
            "pagerank": nx.pagerank,
            "closeness": nx.closeness_centrality,
        }

        if algorithm not in algorithms:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. Choose: {list(algorithms.keys())}"
            )

        return algorithms[algorithm](G)

    def get_most_critical_resources(
        self,
        top_n: int = 10,
        algorithm: str = "pagerank",
    ) -> list[tuple[Node, float]]:
        """
        Get most critical resources by centrality.

        Useful for: Identifying infrastructure bottlenecks.

        Args:
            top_n: Number of resources to return
            algorithm: Centrality algorithm to use

        Returns:
            List of (node, score) tuples sorted by score.
        """
        centrality = self.get_centrality(algorithm)
        sorted_ids = sorted(
            centrality.keys(), key=lambda k: centrality[k], reverse=True
        )[:top_n]

        return [
            (n, centrality[n.id])
            for n in (self.get_node(nid) for nid in sorted_ids)
            if n
        ]

    # =========================================================
    # MERGE OPERATIONS
    # =========================================================

    def merge_from(self, other: UnifiedGraphEngine) -> tuple[int, int]:
        """
        Merge another graph into this one using batch operations.

        Use case: Combining scans from multiple regions/accounts.

        Args:
            other: Another UnifiedGraphEngine to merge from

        Returns:
            Tuple of (nodes_added, edges_added)

        Note: Uses batch operations for 10-100x performance vs one-by-one.
        """
        nodes = list(other.get_all_nodes())
        edges = list(other._backend.get_all_edges())

        nodes_added = self.add_nodes(nodes)
        edges_added = self.add_edges(edges)

        return nodes_added, edges_added

    # =========================================================
    # NODE REMOVAL
    # =========================================================

    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the graph.

        Note: Connected edges are automatically removed via FK CASCADE.

        Args:
            node_id: ID of node to remove

        Returns:
            True if node was removed, False if it didn't exist.
        """
        with self._backend._pool.get_writer() as conn:
            cursor = conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            conn.commit()

            if self._backend.enable_metrics:
                self._backend._rebuild_metrics(conn)

            return cursor.rowcount > 0

    # =========================================================
    # NETWORKX PROJECTION (On-demand for complex analysis)
    # =========================================================

    def _get_networkx_graph(self, lightweight: bool = True) -> Any:
        """
        Internal helper to get NetworkX graph with graceful degradation.

        Args:
            lightweight: If True, load minimal data for algorithms.

        Returns:
            nx.DiGraph for use with NetworkX algorithms.

        Raises:
            ImportError: If NetworkX is not installed.
        """
        try:
            import networkx as nx  # noqa: F401
        except ImportError:
            raise ImportError(
                "NetworkX is required for graph algorithms.\n"
                "Install with: pip install networkx\n"
                "Or: pip install replimap[analysis]"
            )

        return self.to_networkx(lightweight=lightweight)

    def to_networkx(self, lightweight: bool = True) -> Any:
        """
        Project graph data to NetworkX for complex analysis.

        This creates a TEMPORARY in-memory graph for algorithms like:
        - Betweenness Centrality
        - PageRank
        - Community Detection
        - Clustering Coefficient

        Args:
            lightweight: If True, only load IDs and types (10x faster, 50% less RAM).
                        If False, load full attributes (for export).

        Returns:
            nx.DiGraph: NetworkX directed graph

        Usage:
            G = engine.to_networkx()
            centrality = nx.betweenness_centrality(G)
            pagerank = nx.pagerank(G)

        Raises:
            ImportError: If NetworkX is not installed.
        """
        try:
            import networkx as nx
        except ImportError as e:
            raise ImportError(
                "NetworkX is required for this operation.\n"
                "Install with: pip install networkx"
            ) from e

        G: nx.DiGraph = nx.DiGraph()
        conn = self._backend._pool.get_reader()

        if lightweight:
            # Fast path: minimal data via direct SQL (10x faster)
            for row in conn.execute("SELECT id, type, name FROM nodes"):
                G.add_node(row["id"], type=row["type"], name=row["name"])

            for row in conn.execute("SELECT source_id, target_id, relation FROM edges"):
                G.add_edge(row["source_id"], row["target_id"], relation=row["relation"])
        else:
            # Full path: all attributes for export
            for node in self.get_all_nodes():
                G.add_node(node.id, **node.to_dict())

            for edge in self._backend.get_all_edges():
                G.add_edge(
                    edge.source_id,
                    edge.target_id,
                    relation=edge.relation,
                    weight=edge.weight,
                    **edge.attributes,
                )

        logger.debug(
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
    # SCAN SESSION MANAGEMENT (Ghost Fix)
    # =========================================================

    def start_scan(self, profile: str | None = None, region: str | None = None) -> Any:
        """
        Start a new scan session.

        Creates a scan session record and sets the current scan ID.
        All nodes/edges added during this session will be tagged with scan_id.

        Args:
            profile: AWS profile being scanned
            region: AWS region being scanned

        Returns:
            ScanSession object with unique ID
        """
        return self._backend.start_scan(profile=profile, region=region)

    def end_scan(
        self, scan_id: str, success: bool = True, error: str | None = None
    ) -> None:
        """
        End a scan session.

        Updates the session status and resource count.

        Args:
            scan_id: The scan session ID to end
            success: Whether the scan completed successfully
            error: Error message if failed
        """
        self._backend.end_scan(scan_id, success=success, error=error)

    def get_scan_session(self, scan_id: str) -> Any:
        """Get a scan session by ID."""
        return self._backend.get_scan_session(scan_id)

    def get_phantom_nodes(self) -> list[Node]:
        """Get all phantom (placeholder) nodes."""
        return self._backend.get_phantom_nodes()

    def cleanup_stale_resources(self, current_scan_id: str) -> int:
        """
        Remove resources not seen in the current scan (Ghost Fix).

        Args:
            current_scan_id: The current scan session ID

        Returns:
            Number of resources removed
        """
        return self._backend.cleanup_stale_resources(current_scan_id)

    def add_phantom_node(
        self,
        node_id: str,
        node_type: str,
        reason: str = "cross-account reference",
    ) -> Node:
        """Add a phantom (placeholder) node for a missing dependency."""
        return self._backend.add_phantom_node(node_id, node_type, reason)

    def resolve_phantom(self, node_id: str, real_node: Node) -> bool:
        """Replace a phantom node with a real node."""
        return self._backend.resolve_phantom(node_id, real_node)

    def get_schema_version(self) -> int:
        """Get current database schema version."""
        return self._backend.get_schema_version()

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
