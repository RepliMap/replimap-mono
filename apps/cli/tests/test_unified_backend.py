"""
Tests for unified SQLite backend.

Tests cover:
- Both memory and file modes work identically
- Batch operations
- Path finding with recursive CTEs
- Snapshot functionality
- UnifiedGraphEngine facade
- NetworkX projection
"""

from __future__ import annotations

from pathlib import Path

import pytest

from replimap.core.unified_storage import Edge, Node, SQLiteBackend, UnifiedGraphEngine


class TestUnifiedBackend:
    """Test that both memory and file modes work identically."""

    @pytest.fixture(params=[":memory:", "file"])
    def backend(self, request: pytest.FixtureRequest, tmp_path: Path) -> SQLiteBackend:
        """Create backend for testing - parametrized for both modes."""
        if request.param == ":memory:":
            return SQLiteBackend(db_path=":memory:")
        else:
            return SQLiteBackend(db_path=str(tmp_path / "test.db"))

    def test_add_and_get_node(self, backend: SQLiteBackend) -> None:
        """Node can be added and retrieved."""
        node = Node(id="test-1", type="aws_instance", name="web")
        backend.add_node(node)

        retrieved = backend.get_node("test-1")
        assert retrieved is not None
        assert retrieved.id == "test-1"
        assert retrieved.name == "web"
        assert retrieved.type == "aws_instance"

    def test_add_node_with_attributes(self, backend: SQLiteBackend) -> None:
        """Node attributes are preserved."""
        node = Node(
            id="vpc-123",
            type="aws_vpc",
            name="Main VPC",
            region="us-east-1",
            account_id="123456789012",
            attributes={"cidr_block": "10.0.0.0/16", "enable_dns": True},
        )
        backend.add_node(node)

        retrieved = backend.get_node("vpc-123")
        assert retrieved is not None
        assert retrieved.region == "us-east-1"
        assert retrieved.account_id == "123456789012"
        assert retrieved.attributes["cidr_block"] == "10.0.0.0/16"
        assert retrieved.attributes["enable_dns"] is True

    def test_batch_operations(self, backend: SQLiteBackend) -> None:
        """Batch add operations work correctly."""
        nodes = [Node(id=f"n{i}", type="aws_instance") for i in range(100)]
        edges = [
            Edge(source_id=f"n{i}", target_id=f"n{i + 1}", relation="next")
            for i in range(99)
        ]

        added_nodes = backend.add_nodes_batch(nodes)
        added_edges = backend.add_edges_batch(edges)

        assert added_nodes == 100
        assert added_edges == 99
        assert backend.node_count() == 100
        assert backend.edge_count() == 99

    def test_get_nodes_by_type(self, backend: SQLiteBackend) -> None:
        """Nodes can be queried by type."""
        nodes = [
            Node(id="vpc-1", type="aws_vpc", name="VPC 1"),
            Node(id="vpc-2", type="aws_vpc", name="VPC 2"),
            Node(id="sg-1", type="aws_security_group", name="SG 1"),
        ]
        backend.add_nodes_batch(nodes)

        vpcs = backend.get_nodes_by_type("aws_vpc")
        sgs = backend.get_nodes_by_type("aws_security_group")

        assert len(vpcs) == 2
        assert len(sgs) == 1
        assert all(n.type == "aws_vpc" for n in vpcs)

    def test_search_nodes(self, backend: SQLiteBackend) -> None:
        """Full-text search works."""
        nodes = [
            Node(id="web-server-1", type="aws_instance", name="Web Server"),
            Node(id="db-server-1", type="aws_instance", name="Database Server"),
            Node(id="cache-server-1", type="aws_instance", name="Cache Server"),
        ]
        backend.add_nodes_batch(nodes)

        results = backend.search_nodes("web")
        assert len(results) >= 1
        assert any(
            "web" in r.id.lower() or (r.name and "web" in r.name.lower())
            for r in results
        )

    def test_path_finding(self, backend: SQLiteBackend) -> None:
        """Path finding with recursive CTE works."""
        nodes = [Node(id=f"p{i}", type="aws_instance") for i in range(5)]
        edges = [
            Edge(source_id=f"p{i}", target_id=f"p{i + 1}", relation="next")
            for i in range(4)
        ]

        backend.add_nodes_batch(nodes)
        backend.add_edges_batch(edges)

        path = backend.find_path("p0", "p4")
        assert path == ["p0", "p1", "p2", "p3", "p4"]

    def test_path_not_found(self, backend: SQLiteBackend) -> None:
        """Path finding returns None when no path exists."""
        nodes = [
            Node(id="a", type="aws_instance"),
            Node(id="b", type="aws_instance"),
        ]
        backend.add_nodes_batch(nodes)
        # No edges - nodes are disconnected

        path = backend.find_path("a", "b")
        assert path is None

    def test_get_neighbors(self, backend: SQLiteBackend) -> None:
        """Get neighbors in different directions."""
        nodes = [
            Node(id="center", type="aws_vpc"),
            Node(id="in1", type="aws_subnet"),
            Node(id="in2", type="aws_subnet"),
            Node(id="out1", type="aws_instance"),
        ]
        edges = [
            Edge(source_id="in1", target_id="center", relation="belongs_to"),
            Edge(source_id="in2", target_id="center", relation="belongs_to"),
            Edge(source_id="center", target_id="out1", relation="contains"),
        ]
        backend.add_nodes_batch(nodes)
        backend.add_edges_batch(edges)

        in_neighbors = backend.get_neighbors("center", direction="in")
        out_neighbors = backend.get_neighbors("center", direction="out")
        all_neighbors = backend.get_neighbors("center", direction="both")

        assert len(in_neighbors) == 2
        assert len(out_neighbors) == 1
        assert len(all_neighbors) == 3

    def test_get_node_degree(self, backend: SQLiteBackend) -> None:
        """Node degree calculation works."""
        nodes = [
            Node(id="hub", type="aws_vpc"),
            Node(id="s1", type="aws_subnet"),
            Node(id="s2", type="aws_subnet"),
            Node(id="s3", type="aws_subnet"),
        ]
        edges = [
            Edge(source_id="s1", target_id="hub", relation="belongs_to"),
            Edge(source_id="s2", target_id="hub", relation="belongs_to"),
            Edge(source_id="s3", target_id="hub", relation="belongs_to"),
        ]
        backend.add_nodes_batch(nodes)
        backend.add_edges_batch(edges)

        in_deg, out_deg = backend.get_node_degree("hub")
        assert in_deg == 3  # 3 incoming edges
        assert out_deg == 0  # 0 outgoing edges

    def test_clear(self, backend: SQLiteBackend) -> None:
        """Clear removes all data."""
        backend.add_node(Node(id="test", type="aws_instance"))
        backend.add_edge(Edge(source_id="test", target_id="test", relation="self"))

        assert backend.node_count() > 0

        backend.clear()

        assert backend.node_count() == 0
        assert backend.edge_count() == 0


class TestSnapshot:
    """Test snapshot functionality."""

    def test_memory_to_file_snapshot(self, tmp_path: Path) -> None:
        """Snapshot from memory to file works."""
        # Create in-memory backend
        backend = SQLiteBackend(db_path=":memory:")
        backend.add_node(Node(id="snap-1", type="aws_instance", name="test"))
        backend.add_node(Node(id="snap-2", type="aws_instance", name="test2"))
        backend.add_edge(
            Edge(source_id="snap-1", target_id="snap-2", relation="connects")
        )

        # Snapshot to file
        snapshot_path = str(tmp_path / "snapshot.db")
        backend.snapshot(snapshot_path)

        # Load snapshot
        loaded = SQLiteBackend.load_snapshot(snapshot_path)

        assert loaded.node_count() == 2
        assert loaded.edge_count() == 1
        node = loaded.get_node("snap-1")
        assert node is not None
        assert node.name == "test"

        loaded.close()

    def test_file_to_file_snapshot(self, tmp_path: Path) -> None:
        """Snapshot from file to file works."""
        # Create file-based backend
        backend = SQLiteBackend(db_path=str(tmp_path / "original.db"))
        backend.add_node(Node(id="f-1", type="aws_instance"))

        # Snapshot
        snapshot_path = str(tmp_path / "copy.db")
        backend.snapshot(snapshot_path)

        # Verify
        loaded = SQLiteBackend.load_snapshot(snapshot_path)
        assert loaded.node_count() == 1

        backend.close()
        loaded.close()

    def test_snapshot_preserves_edges(self, tmp_path: Path) -> None:
        """Snapshot preserves edge relationships."""
        backend = SQLiteBackend(db_path=":memory:")
        backend.add_nodes_batch(
            [
                Node(id="a", type="aws_vpc"),
                Node(id="b", type="aws_subnet"),
                Node(id="c", type="aws_instance"),
            ]
        )
        backend.add_edges_batch(
            [
                Edge(source_id="b", target_id="a", relation="belongs_to"),
                Edge(source_id="c", target_id="b", relation="in_subnet"),
            ]
        )

        snapshot_path = str(tmp_path / "with_edges.db")
        backend.snapshot(snapshot_path)

        loaded = SQLiteBackend.load_snapshot(snapshot_path)
        assert loaded.edge_count() == 2

        # Verify path finding works on loaded snapshot
        path = loaded.find_path("c", "a")
        assert path == ["c", "b", "a"]

        loaded.close()


class TestUnifiedGraphEngine:
    """Test high-level UnifiedGraphEngine."""

    def test_memory_mode(self) -> None:
        """Memory mode engine works correctly."""
        engine = UnifiedGraphEngine()  # No cache_dir = memory mode
        assert not engine.is_persistent

        engine.add_node(Node(id="e1", type="aws_instance"))
        assert engine.node_count() == 1

        engine.close()

    def test_file_mode(self, tmp_path: Path) -> None:
        """File mode engine persists data."""
        # Create and populate
        engine = UnifiedGraphEngine(cache_dir=str(tmp_path))
        assert engine.is_persistent

        engine.add_node(Node(id="e1", type="aws_instance"))
        engine.close()

        # Reload and verify
        engine2 = UnifiedGraphEngine(cache_dir=str(tmp_path))
        assert engine2.node_count() == 1

        engine2.close()

    def test_context_manager(self, tmp_path: Path) -> None:
        """Engine works as context manager."""
        with UnifiedGraphEngine(cache_dir=str(tmp_path)) as engine:
            engine.add_node(Node(id="ctx", type="aws_instance"))
            assert engine.node_count() == 1

    def test_to_networkx(self) -> None:
        """NetworkX projection works."""
        engine = UnifiedGraphEngine()

        nodes = [Node(id=f"nx{i}", type="aws_instance") for i in range(10)]
        edges = [
            Edge(source_id=f"nx{i}", target_id=f"nx{i + 1}", relation="next")
            for i in range(9)
        ]

        engine.add_nodes(nodes)
        engine.add_edges(edges)

        G = engine.to_networkx()

        assert G.number_of_nodes() == 10
        assert G.number_of_edges() == 9

        engine.close()

    def test_impact_analysis(self) -> None:
        """Impact analysis provides correct data."""
        engine = UnifiedGraphEngine()

        nodes = [
            Node(id="vpc", type="aws_vpc", name="Main VPC"),
            Node(id="subnet1", type="aws_subnet", name="Subnet 1"),
            Node(id="subnet2", type="aws_subnet", name="Subnet 2"),
            Node(id="instance1", type="aws_instance", name="Instance 1"),
        ]
        edges = [
            Edge(source_id="subnet1", target_id="vpc", relation="belongs_to"),
            Edge(source_id="subnet2", target_id="vpc", relation="belongs_to"),
            Edge(source_id="instance1", target_id="subnet1", relation="in_subnet"),
        ]

        engine.add_nodes(nodes)
        engine.add_edges(edges)

        analysis = engine.get_impact_analysis("vpc")

        assert analysis["node_id"] == "vpc"
        assert analysis["in_degree"] == 2  # 2 subnets depend on VPC
        assert analysis["blast_radius"] == 2
        assert len(analysis["dependents"]) == 2

        engine.close()

    def test_snapshot_via_engine(self, tmp_path: Path) -> None:
        """Engine snapshot method works."""
        engine = UnifiedGraphEngine(cache_dir=str(tmp_path))
        engine.add_node(Node(id="s1", type="aws_instance"))

        snapshot_path = engine.snapshot()

        assert Path(snapshot_path).exists()

        loaded = UnifiedGraphEngine.load_snapshot(snapshot_path)
        assert loaded.node_count() == 1

        engine.close()
        loaded.close()

    def test_get_all_resources(self) -> None:
        """get_all_resources returns dicts for drift detection."""
        engine = UnifiedGraphEngine()

        nodes = [
            Node(id="r1", type="aws_vpc", name="VPC1", region="us-east-1"),
            Node(id="r2", type="aws_subnet", name="Subnet1", region="us-east-1"),
        ]
        engine.add_nodes(nodes)

        resources = engine.get_all_resources()

        assert len(resources) == 2
        assert all(isinstance(r, dict) for r in resources)
        assert any(r["id"] == "r1" for r in resources)

        engine.close()

    def test_metadata(self) -> None:
        """Metadata operations work."""
        engine = UnifiedGraphEngine()

        engine.set_metadata("scan_time", "2025-01-05T12:00:00")
        engine.set_metadata("version", "1.0")

        assert engine.get_metadata("scan_time") == "2025-01-05T12:00:00"
        assert engine.get_metadata("version") == "1.0"
        assert engine.get_metadata("nonexistent") is None

        engine.close()

    def test_get_stats(self) -> None:
        """Statistics are accurate."""
        engine = UnifiedGraphEngine()

        nodes = [
            Node(id="v1", type="aws_vpc"),
            Node(id="s1", type="aws_subnet"),
            Node(id="s2", type="aws_subnet"),
        ]
        edges = [
            Edge(source_id="s1", target_id="v1", relation="belongs_to"),
            Edge(source_id="s2", target_id="v1", relation="belongs_to"),
        ]
        engine.add_nodes(nodes)
        engine.add_edges(edges)

        stats = engine.get_stats()

        assert stats["node_count"] == 3
        assert stats["edge_count"] == 2
        assert stats["mode"] == "memory"
        assert "type_distribution" in stats
        assert stats["type_distribution"]["aws_vpc"] == 1
        assert stats["type_distribution"]["aws_subnet"] == 2

        engine.close()


class TestResourceCategory:
    """Test resource category inference."""

    def test_compute_category(self) -> None:
        """Compute resources are categorized correctly."""
        node = Node(id="i-123", type="aws_instance", name="Web Server")
        assert node.category.value == "compute"

    def test_storage_category(self) -> None:
        """Storage resources are categorized correctly."""
        node = Node(id="bucket-1", type="aws_s3_bucket", name="Data Bucket")
        assert node.category.value == "storage"

    def test_network_category(self) -> None:
        """Network resources are categorized correctly."""
        node = Node(id="vpc-123", type="aws_vpc", name="Main VPC")
        assert node.category.value == "network"

    def test_security_category(self) -> None:
        """Security resources are categorized correctly."""
        node = Node(id="role-123", type="aws_iam_role", name="Lambda Role")
        assert node.category.value == "security"

    def test_database_category(self) -> None:
        """Database resources are categorized correctly."""
        node = Node(id="db-123", type="aws_rds_instance", name="Main DB")
        assert node.category.value == "database"

    def test_other_category(self) -> None:
        """Unknown resources get 'other' category."""
        node = Node(id="unknown-1", type="aws_custom_resource", name="Custom")
        assert node.category.value == "other"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_graph(self) -> None:
        """Empty graph operations work."""
        engine = UnifiedGraphEngine()

        assert engine.node_count() == 0
        assert engine.edge_count() == 0
        assert list(engine.get_all_nodes()) == []
        assert engine.get_node("nonexistent") is None

        engine.close()

    def test_duplicate_nodes_update(self) -> None:
        """Adding duplicate node updates existing."""
        backend = SQLiteBackend(db_path=":memory:")

        backend.add_node(Node(id="dup", type="aws_vpc", name="Original"))
        backend.add_nodes_batch([Node(id="dup", type="aws_vpc", name="Updated")])

        assert backend.node_count() == 1
        node = backend.get_node("dup")
        assert node is not None
        assert node.name == "Updated"

    def test_duplicate_edges_ignored(self) -> None:
        """Adding duplicate edges is silently ignored."""
        backend = SQLiteBackend(db_path=":memory:")

        backend.add_nodes_batch(
            [
                Node(id="a", type="aws_vpc"),
                Node(id="b", type="aws_subnet"),
            ]
        )

        backend.add_edge(Edge(source_id="b", target_id="a", relation="belongs_to"))
        backend.add_edges_batch(
            [
                Edge(source_id="b", target_id="a", relation="belongs_to")  # Duplicate
            ]
        )

        assert backend.edge_count() == 1

    def test_path_max_depth(self) -> None:
        """Path finding respects max_depth."""
        backend = SQLiteBackend(db_path=":memory:")

        # Create chain: 0 -> 1 -> 2 -> 3 -> 4 -> 5
        nodes = [Node(id=f"d{i}", type="aws_instance") for i in range(6)]
        edges = [
            Edge(source_id=f"d{i}", target_id=f"d{i + 1}", relation="next")
            for i in range(5)
        ]
        backend.add_nodes_batch(nodes)
        backend.add_edges_batch(edges)

        # Path exists but exceeds max_depth
        path = backend.find_path("d0", "d5", max_depth=3)
        assert path is None  # Can't reach in 3 hops

        path = backend.find_path("d0", "d5", max_depth=10)
        assert path is not None  # Can reach with higher depth
