"""
Tests for storage enhancements (Prompt 3.7.2):
- Scan Session Management (Ghost Fix)
- zlib Compression
- Schema Migration System
"""

from __future__ import annotations

from pathlib import Path

from replimap.core.unified_storage import (
    Edge,
    Node,
    ScanSession,
    ScanStatus,
    SQLiteBackend,
    UnifiedGraphEngine,
)


class TestScanSession:
    """Test scan session lifecycle management."""

    def test_start_scan_creates_session(self) -> None:
        """Starting a scan creates a session record."""
        backend = SQLiteBackend(db_path=":memory:")

        session = backend.start_scan(profile="test", region="us-east-1")

        assert session.id.startswith("scan-")
        assert session.profile == "test"
        assert session.region == "us-east-1"
        assert session.status == ScanStatus.RUNNING

        backend.close()

    def test_end_scan_completes_session(self) -> None:
        """Ending a scan marks it as completed with resource count."""
        backend = SQLiteBackend(db_path=":memory:")

        session = backend.start_scan(profile="test")
        backend.add_nodes_batch(
            [
                Node(id="vpc-1", type="aws_vpc"),
                Node(id="vpc-2", type="aws_vpc"),
            ]
        )
        backend.end_scan(session.id, success=True)

        completed = backend.get_scan_session(session.id)
        assert completed is not None
        assert completed.status == ScanStatus.COMPLETED
        assert completed.resource_count == 2
        assert completed.completed_at is not None

        backend.close()

    def test_end_scan_with_failure(self) -> None:
        """Ending a scan with failure records error message."""
        backend = SQLiteBackend(db_path=":memory:")

        session = backend.start_scan()
        backend.end_scan(session.id, success=False, error="Test error")

        failed = backend.get_scan_session(session.id)
        assert failed is not None
        assert failed.status == ScanStatus.FAILED
        assert failed.error_message == "Test error"

        backend.close()

    def test_nodes_tagged_with_scan_id(self) -> None:
        """Nodes added during a scan are tagged with scan_id."""
        backend = SQLiteBackend(db_path=":memory:")

        session = backend.start_scan()
        backend.add_node(Node(id="vpc-1", type="aws_vpc"))
        backend.end_scan(session.id)

        node = backend.get_node("vpc-1")
        assert node is not None
        assert node.scan_id == session.id

        backend.close()

    def test_edges_tagged_with_scan_id(self) -> None:
        """Edges added during a scan are tagged with scan_id."""
        backend = SQLiteBackend(db_path=":memory:")

        session = backend.start_scan()
        backend.add_nodes_batch(
            [
                Node(id="vpc-1", type="aws_vpc"),
                Node(id="subnet-1", type="aws_subnet"),
            ]
        )
        backend.add_edge(Edge(source_id="subnet-1", target_id="vpc-1", relation="in"))
        backend.end_scan(session.id)

        edges = backend.get_edges_from("subnet-1")
        assert len(edges) == 1
        assert edges[0].scan_id == session.id

        backend.close()

    def test_scan_session_via_engine(self) -> None:
        """Scan sessions work through UnifiedGraphEngine."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="eu-west-1")
        engine.add_nodes([Node(id="vpc-1", type="aws_vpc")])
        engine.end_scan(session.id)

        retrieved = engine.get_scan_session(session.id)
        assert retrieved is not None
        assert retrieved.status == ScanStatus.COMPLETED

        engine.close()


class TestPhantomNodes:
    """Test phantom node handling for Ghost Fix."""

    def test_add_phantom_node(self) -> None:
        """Can add phantom nodes for missing dependencies."""
        backend = SQLiteBackend(db_path=":memory:")

        phantom = backend.add_phantom_node(
            node_id="cross-account-sg",
            node_type="aws_security_group",
            reason="cross-account reference",
        )

        assert phantom.is_phantom is True
        assert phantom.phantom_reason == "cross-account reference"

        # Verify it's retrievable
        retrieved = backend.get_node("cross-account-sg")
        assert retrieved is not None
        assert retrieved.is_phantom is True

        backend.close()

    def test_get_phantom_nodes(self) -> None:
        """Can list all phantom nodes."""
        backend = SQLiteBackend(db_path=":memory:")

        # Add regular node
        backend.add_node(Node(id="vpc-1", type="aws_vpc"))

        # Add phantom nodes
        backend.add_phantom_node("missing-1", "aws_instance")
        backend.add_phantom_node("missing-2", "aws_rds_instance")

        phantoms = backend.get_phantom_nodes()
        assert len(phantoms) == 2
        assert all(p.is_phantom for p in phantoms)

        backend.close()

    def test_resolve_phantom(self) -> None:
        """Can resolve a phantom node with real data."""
        backend = SQLiteBackend(db_path=":memory:")

        # Add phantom
        backend.add_phantom_node("vpc-123", "aws_vpc", "cross-account")

        # Resolve with real node
        real_node = Node(
            id="vpc-123",
            type="aws_vpc",
            name="Real VPC",
            region="us-east-1",
        )
        result = backend.resolve_phantom("vpc-123", real_node)

        assert result is True

        # Verify phantom is now real
        node = backend.get_node("vpc-123")
        assert node is not None
        assert node.is_phantom is False
        assert node.name == "Real VPC"

        backend.close()

    def test_resolve_non_phantom_fails(self) -> None:
        """Resolving a non-phantom node returns False."""
        backend = SQLiteBackend(db_path=":memory:")

        backend.add_node(Node(id="vpc-1", type="aws_vpc"))

        result = backend.resolve_phantom(
            "vpc-1",
            Node(id="vpc-1", type="aws_vpc", name="New Name"),
        )

        assert result is False

        backend.close()


class TestGhostCleanup:
    """Test stale resource cleanup (Ghost Fix)."""

    def test_cleanup_stale_resources(self) -> None:
        """Cleanup removes resources from previous scans."""
        backend = SQLiteBackend(db_path=":memory:")

        # First scan
        session1 = backend.start_scan()
        backend.add_nodes_batch(
            [
                Node(id="vpc-1", type="aws_vpc"),
                Node(id="vpc-2", type="aws_vpc"),
            ]
        )
        backend.end_scan(session1.id)

        # Second scan (vpc-2 no longer exists)
        session2 = backend.start_scan()
        backend.add_node(Node(id="vpc-1", type="aws_vpc"))
        backend.end_scan(session2.id)

        # Cleanup removes vpc-2 (not in current scan)
        removed = backend.cleanup_stale_resources(session2.id)

        assert removed == 1
        assert backend.get_node("vpc-1") is not None
        assert backend.get_node("vpc-2") is None

        backend.close()

    def test_cleanup_preserves_phantom_nodes(self) -> None:
        """Cleanup does not remove phantom nodes."""
        backend = SQLiteBackend(db_path=":memory:")

        session1 = backend.start_scan()
        backend.add_phantom_node("cross-account-sg", "aws_security_group")
        backend.end_scan(session1.id)

        session2 = backend.start_scan()
        backend.add_node(Node(id="vpc-1", type="aws_vpc"))
        backend.end_scan(session2.id)

        removed = backend.cleanup_stale_resources(session2.id)

        assert removed == 0  # Phantom not removed
        assert backend.get_node("cross-account-sg") is not None

        backend.close()


class TestCompression:
    """Test zlib compression for attributes."""

    def test_compression_enabled_by_default(self) -> None:
        """Compression is enabled by default."""
        backend = SQLiteBackend(db_path=":memory:")
        assert backend.enable_compression is True
        backend.close()

    def test_compressed_attributes_round_trip(self) -> None:
        """Attributes survive compression round-trip."""
        backend = SQLiteBackend(db_path=":memory:", enable_compression=True)

        large_attrs = {
            "cidr_block": "10.0.0.0/16",
            "tags": {"Name": "Main VPC", "Environment": "Production"},
            "dns_hostnames": True,
            "dns_support": True,
            "long_string": "x" * 1000,  # Should compress well
        }

        backend.add_node(
            Node(
                id="vpc-1",
                type="aws_vpc",
                attributes=large_attrs,
            )
        )

        retrieved = backend.get_node("vpc-1")
        assert retrieved is not None
        assert retrieved.attributes == large_attrs

        backend.close()

    def test_compression_reduces_size(self, tmp_path: Path) -> None:
        """Compression significantly reduces database size."""
        db_compressed = str(tmp_path / "compressed.db")
        db_uncompressed = str(tmp_path / "uncompressed.db")

        # Create compressed database
        backend1 = SQLiteBackend(db_path=db_compressed, enable_compression=True)
        large_attrs = {"data": "x" * 5000}  # 5KB of compressible data
        for i in range(100):
            backend1.add_node(
                Node(id=f"node-{i}", type="aws_vpc", attributes=large_attrs)
            )
        backend1.close()

        # Create uncompressed database
        backend2 = SQLiteBackend(db_path=db_uncompressed, enable_compression=False)
        for i in range(100):
            backend2.add_node(
                Node(id=f"node-{i}", type="aws_vpc", attributes=large_attrs)
            )
        backend2.close()

        compressed_size = Path(db_compressed).stat().st_size
        uncompressed_size = Path(db_uncompressed).stat().st_size

        # Compression should reduce size significantly (at least 50%)
        assert compressed_size < uncompressed_size * 0.5

    def test_edge_attributes_compressed(self) -> None:
        """Edge attributes are also compressed."""
        backend = SQLiteBackend(db_path=":memory:", enable_compression=True)

        backend.add_nodes_batch(
            [
                Node(id="a", type="aws_vpc"),
                Node(id="b", type="aws_subnet"),
            ]
        )

        edge_attrs = {"metadata": "x" * 1000}
        backend.add_edge(
            Edge(
                source_id="b",
                target_id="a",
                relation="in",
                attributes=edge_attrs,
            )
        )

        edges = backend.get_edges_from("b")
        assert len(edges) == 1
        assert edges[0].attributes == edge_attrs

        backend.close()


class TestSchemaMigration:
    """Test schema migration system."""

    def test_new_database_gets_latest_schema(self) -> None:
        """New databases get the latest schema version."""
        backend = SQLiteBackend(db_path=":memory:")

        version = backend.get_schema_version()
        assert version == 2  # Current version

        backend.close()

    def test_schema_version_in_stats(self) -> None:
        """Schema version is included in stats."""
        backend = SQLiteBackend(db_path=":memory:")

        stats = backend.get_stats()
        assert "schema_version" in stats
        assert stats["schema_version"] == 2

        backend.close()

    def test_schema_version_via_engine(self) -> None:
        """Schema version accessible via engine."""
        engine = UnifiedGraphEngine()

        version = engine.get_schema_version()
        assert version == 2

        engine.close()

    def test_migration_idempotent(self, tmp_path: Path) -> None:
        """Re-running migrations is safe."""
        db_path = str(tmp_path / "test.db")

        # First open
        backend1 = SQLiteBackend(db_path=db_path)
        backend1.add_node(Node(id="vpc-1", type="aws_vpc"))
        backend1.close()

        # Second open (should not fail)
        backend2 = SQLiteBackend(db_path=db_path)
        assert backend2.get_node("vpc-1") is not None
        assert backend2.get_schema_version() == 2
        backend2.close()


class TestScanSessionDataclass:
    """Test ScanSession dataclass functionality."""

    def test_scan_session_to_dict(self) -> None:
        """ScanSession can be converted to dict."""
        session = ScanSession(
            id="scan-abc123",
            profile="prod",
            region="us-east-1",
        )

        data = session.to_dict()
        assert data["id"] == "scan-abc123"
        assert data["profile"] == "prod"
        assert data["region"] == "us-east-1"
        assert data["status"] == "running"

    def test_scan_session_from_dict(self) -> None:
        """ScanSession can be created from dict."""
        from datetime import datetime

        data = {
            "id": "scan-abc123",
            "profile": "prod",
            "region": "us-east-1",
            "status": "completed",
            "started_at": "2025-01-01T00:00:00+00:00",
            "completed_at": "2025-01-01T00:05:00+00:00",
            "resource_count": 100,
            "error_message": None,
        }

        session = ScanSession.from_dict(data)
        assert session.id == "scan-abc123"
        assert session.status == ScanStatus.COMPLETED
        assert session.resource_count == 100
        assert isinstance(session.started_at, datetime)

    def test_scan_session_complete(self) -> None:
        """ScanSession.complete() updates status."""
        session = ScanSession()
        session.complete(resource_count=50)

        assert session.status == ScanStatus.COMPLETED
        assert session.resource_count == 50
        assert session.completed_at is not None

    def test_scan_session_fail(self) -> None:
        """ScanSession.fail() updates status and error."""
        session = ScanSession()
        session.fail("Access denied")

        assert session.status == ScanStatus.FAILED
        assert session.error_message == "Access denied"


class TestNodePhantomFields:
    """Test Node dataclass phantom fields."""

    def test_node_phantom_defaults(self) -> None:
        """Node has correct phantom defaults."""
        node = Node(id="vpc-1", type="aws_vpc")
        assert node.is_phantom is False
        assert node.phantom_reason is None
        assert node.scan_id is None

    def test_node_to_dict_includes_phantom_fields(self) -> None:
        """Node.to_dict() includes phantom fields."""
        node = Node(
            id="vpc-1",
            type="aws_vpc",
            is_phantom=True,
            phantom_reason="cross-account",
            scan_id="scan-123",
        )

        data = node.to_dict()
        assert data["is_phantom"] is True
        assert data["phantom_reason"] == "cross-account"
        assert data["scan_id"] == "scan-123"

    def test_node_from_dict_with_phantom_fields(self) -> None:
        """Node.from_dict() handles phantom fields."""
        data = {
            "id": "vpc-1",
            "type": "aws_vpc",
            "is_phantom": True,
            "phantom_reason": "cross-account",
            "scan_id": "scan-123",
        }

        node = Node.from_dict(data)
        assert node.is_phantom is True
        assert node.phantom_reason == "cross-account"
        assert node.scan_id == "scan-123"


class TestEdgeScanId:
    """Test Edge dataclass scan_id field."""

    def test_edge_scan_id_default(self) -> None:
        """Edge has correct scan_id default."""
        edge = Edge(source_id="a", target_id="b", relation="uses")
        assert edge.scan_id is None

    def test_edge_to_dict_includes_scan_id(self) -> None:
        """Edge.to_dict() includes scan_id."""
        edge = Edge(
            source_id="a",
            target_id="b",
            relation="uses",
            scan_id="scan-123",
        )

        data = edge.to_dict()
        assert data["scan_id"] == "scan-123"

    def test_edge_from_dict_with_scan_id(self) -> None:
        """Edge.from_dict() handles scan_id."""
        data = {
            "source_id": "a",
            "target_id": "b",
            "relation": "uses",
            "scan_id": "scan-123",
        }

        edge = Edge.from_dict(data)
        assert edge.scan_id == "scan-123"
