"""
End-to-End tests for UnifiedGraphEngine simulating realistic CLI command scenarios.

These tests verify that the SQLite backend works correctly in scenarios
that simulate how the CLI commands would use it.

Test Coverage:
- Full scan workflow (scan command)
- Incremental scanning with ghost cleanup
- Multi-region scanning
- Cross-account dependencies (phantom nodes)
- Large-scale scenarios
- Compression handling
- Schema migration
- Graph algorithms with scan context
- Snapshot functionality
- Error handling
- CLI command integration patterns for ALL commands:
  * scan - Resource scanning workflow
  * analyze - Critical resource and SPOF analysis
  * deps - Dependency traversal
  * graph - Resource export for visualization
  * snapshot - State snapshot save/list/diff
  * clone - Terraform generation from graph
  * audit - Security scanning and findings
  * drift - Configuration drift detection
  * cost - Cost estimation from resource attributes
  * dr - Disaster recovery readiness assessment
  * transfer - Cross-AZ data transfer analysis
  * unused - Unused resource detection
  * validate - Topology constraint validation
  * iam - Least-privilege IAM policy generation
"""

from __future__ import annotations

import json
import shutil
import tempfile
import time
import zlib
from pathlib import Path

import pytest

from replimap.core.unified_storage import (
    Edge,
    Node,
    ScanStatus,
    SQLiteBackend,
    UnifiedGraphEngine,
)
from replimap.core.unified_storage.sqlite_backend import compress_json, decompress_json


class TestFullScanWorkflow:
    """Tests simulating a complete scan -> process -> cleanup workflow."""

    def test_complete_scan_lifecycle(self) -> None:
        """Simulate: replimap scan --profile prod --region us-east-1."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # 1. Start scan session
            session = engine.start_scan(profile="prod", region="us-east-1")
            assert session.status == ScanStatus.RUNNING
            assert session.profile == "prod"
            assert session.region == "us-east-1"

            # 2. Simulate scanner adding resources (like VPC scanner)
            vpc_nodes = [
                Node(
                    id="vpc-12345",
                    type="aws_vpc",
                    name="prod-vpc",
                    attributes={"cidr_block": "10.0.0.0/16", "state": "available"},
                ),
                Node(
                    id="vpc-67890",
                    type="aws_vpc",
                    name="staging-vpc",
                    attributes={"cidr_block": "10.1.0.0/16", "state": "available"},
                ),
            ]
            engine.add_nodes(vpc_nodes)

            # 3. Simulate subnet scanner
            subnet_nodes = [
                Node(
                    id="subnet-a1",
                    type="aws_subnet",
                    name="prod-private-1",
                    attributes={"vpc_id": "vpc-12345", "cidr_block": "10.0.1.0/24"},
                ),
                Node(
                    id="subnet-a2",
                    type="aws_subnet",
                    name="prod-private-2",
                    attributes={"vpc_id": "vpc-12345", "cidr_block": "10.0.2.0/24"},
                ),
            ]
            engine.add_nodes(subnet_nodes)

            # 4. Add edges (dependencies)
            edges = [
                Edge(source_id="subnet-a1", target_id="vpc-12345", relation="in_vpc"),
                Edge(source_id="subnet-a2", target_id="vpc-12345", relation="in_vpc"),
            ]
            engine.add_edges(edges)

            # 5. Simulate EC2 scanner
            ec2_nodes = [
                Node(
                    id="i-abc123",
                    type="aws_instance",
                    name="web-server-1",
                    attributes={"instance_type": "t3.micro", "state": "running"},
                ),
            ]
            engine.add_nodes(ec2_nodes)
            engine.add_edge(
                Edge(source_id="i-abc123", target_id="subnet-a1", relation="in_subnet")
            )

            # 6. End scan
            engine.end_scan(session.id)

            # 7. Verify results
            stats = engine.get_stats()
            assert stats["node_count"] == 5
            assert stats["edge_count"] == 3

            # 8. Verify all nodes are tagged with scan_id
            for node_id in [
                "vpc-12345",
                "vpc-67890",
                "subnet-a1",
                "subnet-a2",
                "i-abc123",
            ]:
                node = engine.get_node(node_id)
                assert node is not None
                assert node.scan_id == session.id

            engine.close()

    def test_incremental_scan_with_ghost_cleanup(self) -> None:
        """Simulate: Two consecutive scans where resources disappear (ghost cleanup)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # First scan: Add 5 resources
            session1 = engine.start_scan(profile="prod", region="us-east-1")
            engine.add_nodes(
                [
                    Node(id="vpc-1", type="aws_vpc"),
                    Node(id="subnet-1", type="aws_subnet"),
                    Node(id="subnet-2", type="aws_subnet"),
                    Node(id="i-1", type="aws_instance"),
                    Node(
                        id="i-2", type="aws_instance"
                    ),  # This will be "deleted" in scan 2
                ]
            )
            engine.end_scan(session1.id)
            assert engine.node_count() == 5

            # Second scan: Only 4 resources remain (i-2 was terminated)
            session2 = engine.start_scan(profile="prod", region="us-east-1")
            engine.add_nodes(
                [
                    Node(id="vpc-1", type="aws_vpc"),
                    Node(id="subnet-1", type="aws_subnet"),
                    Node(id="subnet-2", type="aws_subnet"),
                    Node(id="i-1", type="aws_instance"),
                    # i-2 is NOT added - it no longer exists
                ]
            )
            engine.end_scan(session2.id)

            # Ghost cleanup: Remove resources not seen in current scan
            removed = engine.cleanup_stale_resources(session2.id)
            assert removed == 1  # i-2 should be removed

            # Verify only 4 resources remain
            assert engine.node_count() == 4
            assert engine.get_node("i-2") is None  # Ghost removed

            engine.close()

    def test_multiple_region_scans(self) -> None:
        """Simulate: Scanning multiple regions sequentially."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # Scan us-east-1
            session1 = engine.start_scan(profile="prod", region="us-east-1")
            engine.add_nodes(
                [
                    Node(
                        id="vpc-east-1",
                        type="aws_vpc",
                        attributes={"region": "us-east-1"},
                    ),
                    Node(
                        id="i-east-1",
                        type="aws_instance",
                        attributes={"region": "us-east-1"},
                    ),
                ]
            )
            engine.end_scan(session1.id)

            # Scan us-west-2
            session2 = engine.start_scan(profile="prod", region="us-west-2")
            engine.add_nodes(
                [
                    Node(
                        id="vpc-west-1",
                        type="aws_vpc",
                        attributes={"region": "us-west-2"},
                    ),
                    Node(
                        id="i-west-1",
                        type="aws_instance",
                        attributes={"region": "us-west-2"},
                    ),
                ]
            )
            engine.end_scan(session2.id)

            # Verify all resources from both scans exist
            assert engine.node_count() == 4
            assert engine.get_node("vpc-east-1") is not None
            assert engine.get_node("vpc-west-1") is not None

            engine.close()

    def test_scan_with_complex_attributes(self) -> None:
        """Test that complex AWS-like attributes are preserved correctly."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Complex attributes similar to real AWS API responses
        complex_attrs = {
            "cidr_block": "10.0.0.0/16",
            "tags": {
                "Name": "Production VPC",
                "Environment": "prod",
                "CostCenter": "12345",
            },
            "enable_dns_hostnames": True,
            "enable_dns_support": True,
            "instance_tenancy": "default",
            "dhcp_options": {"domain_name": "ec2.internal"},
            "nested": {"level1": {"level2": {"level3": "deep_value"}}},
            "list_of_dicts": [
                {"key": "value1"},
                {"key": "value2"},
            ],
            "numbers": [1, 2, 3, 4, 5],
        }

        engine.add_node(
            Node(
                id="vpc-complex",
                type="aws_vpc",
                name="Complex VPC",
                attributes=complex_attrs,
            )
        )
        engine.end_scan(session.id)

        # Retrieve and verify
        node = engine.get_node("vpc-complex")
        assert node is not None
        assert node.attributes == complex_attrs
        assert node.attributes["tags"]["Name"] == "Production VPC"
        assert node.attributes["nested"]["level1"]["level2"]["level3"] == "deep_value"

        engine.close()


class TestCrossAccountDependencies:
    """Tests for phantom nodes representing cross-account resources."""

    def test_cross_account_peering(self) -> None:
        """Simulate: VPC peering to another account's VPC (phantom node)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add our VPC
        engine.add_node(Node(id="vpc-12345", type="aws_vpc", name="prod-vpc"))

        # Add peering connection referencing another account's VPC
        engine.add_node(
            Node(
                id="pcx-abc123",
                type="aws_vpc_peering_connection",
                attributes={
                    "requester_vpc_id": "vpc-12345",
                    "accepter_vpc_id": "vpc-other-account",
                },
            )
        )

        # Create phantom node for cross-account VPC
        engine.add_phantom_node(
            node_id="vpc-other-account",
            node_type="aws_vpc",
            reason="Cross-account VPC in account 123456789012",
        )

        # Add edge to phantom
        engine.add_edge(
            Edge(
                source_id="pcx-abc123",
                target_id="vpc-other-account",
                relation="peers_with",
            )
        )

        engine.end_scan(session.id)

        # Verify phantom node exists
        phantoms = engine.get_phantom_nodes()
        assert len(phantoms) == 1
        assert phantoms[0].id == "vpc-other-account"
        assert phantoms[0].is_phantom is True

        engine.close()

    def test_phantom_nodes_preserved_during_cleanup(self) -> None:
        """Ghost cleanup should NOT remove phantoms."""
        engine = UnifiedGraphEngine()

        session1 = engine.start_scan(profile="prod", region="us-east-1")
        engine.add_node(Node(id="vpc-12345", type="aws_vpc"))
        engine.add_node(Node(id="pcx-abc123", type="aws_vpc_peering_connection"))
        engine.add_phantom_node(
            "vpc-other-account", "aws_vpc", "Cross-account reference"
        )
        engine.end_scan(session1.id)

        # Start a new scan without the peering connection
        session2 = engine.start_scan(profile="prod", region="us-east-1")
        engine.add_node(Node(id="vpc-12345", type="aws_vpc"))
        # pcx-abc123 not added
        engine.end_scan(session2.id)

        # Cleanup stale resources
        removed = engine.cleanup_stale_resources(session2.id)

        # pcx-abc123 should be removed, but phantom should be preserved
        assert removed == 1  # pcx-abc123 removed
        assert engine.get_node("vpc-other-account") is not None  # Phantom preserved

        engine.close()

    def test_resolve_phantom_when_discovered(self) -> None:
        """Simulate: Phantom node gets resolved when actually scanned."""
        engine = UnifiedGraphEngine()

        # First scan: Create phantom for cross-account resource
        session1 = engine.start_scan(profile="prod", region="us-east-1")
        engine.add_node(Node(id="sg-local", type="aws_security_group"))
        engine.add_phantom_node(
            node_id="sg-cross-account",
            node_type="aws_security_group",
            reason="Referenced from another account",
        )
        engine.add_edge(
            Edge(
                source_id="sg-local",
                target_id="sg-cross-account",
                relation="references",
            )
        )
        engine.end_scan(session1.id)

        # Verify phantom
        phantom = engine.get_node("sg-cross-account")
        assert phantom is not None
        assert phantom.is_phantom is True

        # Resolve the phantom with real data
        real_node = Node(
            id="sg-cross-account",
            type="aws_security_group",
            name="actual-sg-name",
            attributes={"vpc_id": "vpc-xyz", "description": "Real SG data"},
        )
        resolved = engine.resolve_phantom("sg-cross-account", real_node)
        assert resolved is True

        # Verify phantom is now a real node
        resolved_node = engine.get_node("sg-cross-account")
        assert resolved_node is not None
        assert resolved_node.is_phantom is False
        assert resolved_node.name == "actual-sg-name"
        assert resolved_node.attributes["description"] == "Real SG data"

        engine.close()


class TestLargeScaleScenarios:
    """Tests with large datasets simulating production environments."""

    def test_large_vpc_with_many_subnets(self) -> None:
        """Simulate: Large VPC with 100+ subnets and instances."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="enterprise", region="us-east-1")

        # Add VPC
        engine.add_node(
            Node(
                id="vpc-enterprise",
                type="aws_vpc",
                attributes={"cidr_block": "10.0.0.0/8"},
            )
        )

        # Add 100 subnets (batch)
        subnets = [
            Node(
                id=f"subnet-{i:04d}",
                type="aws_subnet",
                attributes={"cidr_block": f"10.{i // 256}.{i % 256}.0/24"},
            )
            for i in range(100)
        ]
        engine.add_nodes(subnets)

        # Add edges (subnets -> VPC)
        subnet_edges = [
            Edge(
                source_id=f"subnet-{i:04d}",
                target_id="vpc-enterprise",
                relation="in_vpc",
            )
            for i in range(100)
        ]
        engine.add_edges(subnet_edges)

        # Add 500 instances across subnets
        instances = [
            Node(
                id=f"i-{i:06d}",
                type="aws_instance",
                attributes={
                    "instance_type": "t3.micro",
                    "subnet_id": f"subnet-{i % 100:04d}",
                },
            )
            for i in range(500)
        ]
        engine.add_nodes(instances)

        # Add instance -> subnet edges
        instance_edges = [
            Edge(
                source_id=f"i-{i:06d}",
                target_id=f"subnet-{i % 100:04d}",
                relation="in_subnet",
            )
            for i in range(500)
        ]
        engine.add_edges(instance_edges)

        engine.end_scan(session.id)

        # Verify counts
        assert engine.node_count() == 601  # 1 VPC + 100 subnets + 500 instances
        assert engine.edge_count() == 600  # 100 subnet->VPC + 500 instance->subnet

        # Test queries
        vpc_dependents = engine.get_dependents("vpc-enterprise", recursive=True)
        assert len(vpc_dependents) == 600  # All subnets and instances

        # Test FTS search
        search_results = engine.search("subnet")
        assert len(search_results) == 100

        engine.close()

    def test_dependency_traversal_performance(self) -> None:
        """Test that dependency traversal is fast even with deep graphs."""
        engine = UnifiedGraphEngine()

        # Create a deep chain: A -> B -> C -> ... -> Z (26 levels)
        nodes = [Node(id=f"node-{chr(65 + i)}", type="aws_resource") for i in range(26)]
        engine.add_nodes(nodes)

        edges = [
            Edge(
                source_id=f"node-{chr(65 + i)}",
                target_id=f"node-{chr(65 + i + 1)}",
                relation="depends_on",
            )
            for i in range(25)
        ]
        engine.add_edges(edges)

        # Time the recursive dependency lookup
        start = time.time()
        deps = engine.get_dependencies("node-A", recursive=True, max_depth=50)
        duration = time.time() - start

        # Should find all 25 dependencies
        assert len(deps) == 25
        # Should be fast (< 100ms)
        assert duration < 0.1, f"Dependency traversal took {duration:.3f}s"

        engine.close()

    def test_batch_operations_performance(self) -> None:
        """Test that batch operations are efficient."""
        engine = UnifiedGraphEngine()

        # Create 1000 nodes in batch
        nodes = [
            Node(
                id=f"resource-{i:05d}",
                type="aws_instance",
                name=f"Instance {i}",
                attributes={"index": i, "data": "x" * 100},
            )
            for i in range(1000)
        ]

        start = time.time()
        engine.add_nodes(nodes)
        node_duration = time.time() - start

        # Create edges
        edges = [
            Edge(
                source_id=f"resource-{i:05d}",
                target_id=f"resource-{(i + 1) % 1000:05d}",
                relation="connects",
            )
            for i in range(1000)
        ]

        start = time.time()
        engine.add_edges(edges)
        edge_duration = time.time() - start

        # Verify
        assert engine.node_count() == 1000
        assert engine.edge_count() == 1000

        # Should be reasonably fast (< 2s for each operation)
        assert node_duration < 2.0, f"Node batch took {node_duration:.3f}s"
        assert edge_duration < 2.0, f"Edge batch took {edge_duration:.3f}s"

        engine.close()


class TestCompressionScenarios:
    """Tests for compression handling in various scenarios."""

    def test_compression_with_large_json_attributes(self) -> None:
        """Test compression savings with large JSON attributes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create engine with compression
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # Large attributes (like a security group with many rules)
            large_rules = [
                {
                    "protocol": "tcp",
                    "from_port": i,
                    "to_port": i,
                    "cidr_blocks": ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
                    "description": f"Rule number {i} for application traffic handling",
                }
                for i in range(100)
            ]

            engine.add_node(
                Node(
                    id="sg-rules",
                    type="aws_security_group",
                    name="complex-sg",
                    attributes={
                        "ingress_rules": large_rules,
                        "egress_rules": large_rules,
                    },
                )
            )

            engine.close()

            # Get file size
            db_path = Path(tmpdir) / "graph.db"
            compressed_size = db_path.stat().st_size

            # Create another engine without compression
            uncompressed_dir = tmpdir + "_uncompressed"
            Path(uncompressed_dir).mkdir(parents=True, exist_ok=True)
            backend = SQLiteBackend(
                db_path=str(Path(uncompressed_dir) / "graph.db"),
                enable_compression=False,
            )

            backend.add_node(
                Node(
                    id="sg-rules",
                    type="aws_security_group",
                    name="complex-sg",
                    attributes={
                        "ingress_rules": large_rules,
                        "egress_rules": large_rules,
                    },
                )
            )

            backend.close()

            uncompressed_path = Path(uncompressed_dir) / "graph.db"
            uncompressed_size = uncompressed_path.stat().st_size

            # Compressed should be smaller (at least some compression)
            compression_ratio = compressed_size / uncompressed_size
            assert compression_ratio < 0.9, (
                f"Expected some compression, got {(1 - compression_ratio) * 100:.1f}%"
            )

            # Cleanup
            shutil.rmtree(uncompressed_dir)

    def test_backwards_compatible_decompression(self) -> None:
        """Test reading uncompressed legacy data."""
        # Test decompressing actual JSON string (legacy format)
        legacy_json = '{"key": "value"}'
        result = decompress_json(legacy_json)
        assert result == {"key": "value"}

        # Test decompressing actual compressed data
        compressed = zlib.compress(json.dumps({"key": "value"}).encode())
        result = decompress_json(compressed)
        assert result == {"key": "value"}

    def test_compression_roundtrip(self) -> None:
        """Test compression and decompression roundtrip."""
        test_data = {
            "string": "hello world",
            "number": 42,
            "nested": {"a": 1, "b": 2},
            "list": [1, 2, 3],
            "unicode": "日本語テスト",
        }

        compressed = compress_json(test_data)
        decompressed = decompress_json(compressed)
        assert decompressed == test_data


class TestSchemaMigrationScenarios:
    """Tests for schema migration handling."""

    def test_migration_preserves_data(self) -> None:
        """Test that schema migration preserves all existing data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create initial data
            engine = UnifiedGraphEngine(cache_dir=tmpdir)
            engine.add_nodes(
                [
                    Node(
                        id="node-1",
                        type="aws_vpc",
                        name="vpc-1",
                        attributes={"cidr": "10.0.0.0/16"},
                    ),
                    Node(
                        id="node-2",
                        type="aws_subnet",
                        name="subnet-1",
                        attributes={"az": "us-east-1a"},
                    ),
                ]
            )
            engine.add_edge(
                Edge(source_id="node-2", target_id="node-1", relation="in_vpc")
            )
            engine.close()

            # Reopen - migration should be idempotent
            engine2 = UnifiedGraphEngine(cache_dir=tmpdir)

            # Verify data is intact
            assert engine2.node_count() == 2
            assert engine2.edge_count() == 1

            node1 = engine2.get_node("node-1")
            assert node1 is not None
            assert node1.name == "vpc-1"
            assert node1.attributes["cidr"] == "10.0.0.0/16"

            engine2.close()

    def test_schema_version_reported_correctly(self) -> None:
        """Test that schema version is correctly reported."""
        engine = UnifiedGraphEngine()

        version = engine.get_schema_version()
        assert version == 2  # Current schema version

        stats = engine.get_stats()
        assert stats["schema_version"] == 2

        engine.close()

    def test_multiple_reopens_safe(self) -> None:
        """Test that repeatedly opening the same database is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(5):
                engine = UnifiedGraphEngine(cache_dir=tmpdir)
                engine.add_node(Node(id=f"node-{i}", type="aws_vpc", name=f"VPC {i}"))
                count = engine.node_count()
                engine.close()

                assert count == i + 1


class TestGraphAlgorithmsWithScanContext:
    """Tests for graph algorithms in scan context."""

    def test_safe_apply_order_with_scan_session(self) -> None:
        """Test Terraform apply order generation with scan session."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources in random order
        engine.add_nodes(
            [
                Node(id="i-instance", type="aws_instance"),
                Node(id="vpc-main", type="aws_vpc"),
                Node(id="subnet-a", type="aws_subnet"),
                Node(id="sg-web", type="aws_security_group"),
            ]
        )

        # Add dependencies
        engine.add_edges(
            [
                Edge(
                    source_id="i-instance", target_id="subnet-a", relation="in_subnet"
                ),
                Edge(source_id="i-instance", target_id="sg-web", relation="uses_sg"),
                Edge(source_id="subnet-a", target_id="vpc-main", relation="in_vpc"),
                Edge(source_id="sg-web", target_id="vpc-main", relation="in_vpc"),
            ]
        )

        engine.end_scan(session.id)

        # Get safe apply order
        order = engine.safe_apply_order()

        # VPC must come before subnet and SG
        vpc_idx = order.index("vpc-main")
        subnet_idx = order.index("subnet-a")
        sg_idx = order.index("sg-web")
        instance_idx = order.index("i-instance")

        assert vpc_idx < subnet_idx
        assert vpc_idx < sg_idx
        assert subnet_idx < instance_idx
        assert sg_idx < instance_idx

        engine.close()

    def test_safe_destroy_order(self) -> None:
        """Test Terraform destroy order (reverse of apply)."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="subnet", type="aws_subnet"),
                Node(id="instance", type="aws_instance"),
            ]
        )

        engine.add_edges(
            [
                Edge(source_id="subnet", target_id="vpc", relation="in_vpc"),
                Edge(source_id="instance", target_id="subnet", relation="in_subnet"),
            ]
        )

        # Destroy order should be reverse: instance -> subnet -> vpc
        destroy_order = engine.safe_destroy_order()

        vpc_idx = destroy_order.index("vpc")
        subnet_idx = destroy_order.index("subnet")
        instance_idx = destroy_order.index("instance")

        assert instance_idx < subnet_idx
        assert subnet_idx < vpc_idx

        engine.close()

    def test_critical_resources_with_real_data(self) -> None:
        """Test finding critical resources (hub nodes) in realistic graph."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # VPC is a hub - many things depend on it
        engine.add_node(Node(id="vpc-main", type="aws_vpc"))

        # Add many subnets depending on VPC
        for i in range(10):
            engine.add_node(Node(id=f"subnet-{i}", type="aws_subnet"))
            engine.add_edge(
                Edge(source_id=f"subnet-{i}", target_id="vpc-main", relation="in_vpc")
            )

        # Add many SGs depending on VPC
        for i in range(5):
            engine.add_node(Node(id=f"sg-{i}", type="aws_security_group"))
            engine.add_edge(
                Edge(source_id=f"sg-{i}", target_id="vpc-main", relation="in_vpc")
            )

        # Add instances depending on subnets
        for i in range(20):
            engine.add_node(Node(id=f"i-{i}", type="aws_instance"))
            engine.add_edge(
                Edge(
                    source_id=f"i-{i}",
                    target_id=f"subnet-{i % 10}",
                    relation="in_subnet",
                )
            )

        engine.end_scan(session.id)

        # VPC should be most critical (highest degree centrality)
        # Use "degree" algorithm to avoid numpy dependency
        critical = engine.get_most_critical_resources(top_n=3, algorithm="degree")
        critical_ids = [node.id for node, score in critical]
        assert "vpc-main" in critical_ids

        engine.close()

    def test_cycle_detection(self) -> None:
        """Test cycle detection in dependency graph."""
        engine = UnifiedGraphEngine()

        # Create a cycle: A -> B -> C -> A
        engine.add_nodes(
            [
                Node(id="sg-a", type="aws_security_group"),
                Node(id="sg-b", type="aws_security_group"),
                Node(id="sg-c", type="aws_security_group"),
            ]
        )

        engine.add_edges(
            [
                Edge(source_id="sg-a", target_id="sg-b", relation="allows_from"),
                Edge(source_id="sg-b", target_id="sg-c", relation="allows_from"),
                Edge(source_id="sg-c", target_id="sg-a", relation="allows_from"),
            ]
        )

        assert engine.has_cycles() is True

        cycles = engine.find_cycles(limit=5)
        assert len(cycles) >= 1

        engine.close()

    def test_strongly_connected_components(self) -> None:
        """Test SCC detection."""
        engine = UnifiedGraphEngine()

        # Create two SCCs: {A,B} and {C,D,E}
        engine.add_nodes(
            [
                Node(id="a", type="aws_resource"),
                Node(id="b", type="aws_resource"),
                Node(id="c", type="aws_resource"),
                Node(id="d", type="aws_resource"),
                Node(id="e", type="aws_resource"),
            ]
        )

        # SCC 1: a <-> b
        engine.add_edge(Edge(source_id="a", target_id="b", relation="r"))
        engine.add_edge(Edge(source_id="b", target_id="a", relation="r"))

        # SCC 2: c -> d -> e -> c
        engine.add_edge(Edge(source_id="c", target_id="d", relation="r"))
        engine.add_edge(Edge(source_id="d", target_id="e", relation="r"))
        engine.add_edge(Edge(source_id="e", target_id="c", relation="r"))

        sccs = engine.strongly_connected_components()

        # Should have 2 SCCs with size > 1
        large_sccs = [scc for scc in sccs if len(scc) > 1]
        assert len(large_sccs) == 2

        engine.close()


class TestSnapshotWithScanSession:
    """Tests for snapshot functionality with scan sessions."""

    def test_snapshot_preserves_scan_metadata(self) -> None:
        """Test that snapshots preserve scan session data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source engine with scan data
            source = UnifiedGraphEngine(cache_dir=tmpdir)

            session = source.start_scan(profile="prod", region="eu-west-1")
            source.add_nodes(
                [
                    Node(id="vpc-1", type="aws_vpc"),
                    Node(id="subnet-1", type="aws_subnet"),
                ]
            )
            source.end_scan(session.id)
            source.close()

            # Create snapshot
            snapshot_path = Path(tmpdir) / "snapshot.db"
            source2 = UnifiedGraphEngine(cache_dir=tmpdir)
            source2.snapshot(str(snapshot_path))
            source2.close()

            # Open snapshot and verify
            restored = UnifiedGraphEngine(db_path=str(snapshot_path))

            assert restored.node_count() == 2

            # Verify nodes have scan_id
            node = restored.get_node("vpc-1")
            assert node is not None
            assert node.scan_id == session.id

            restored.close()

    def test_snapshot_memory_to_file(self) -> None:
        """Test snapshot from memory mode to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create in-memory engine
            engine = UnifiedGraphEngine()  # No cache_dir = memory mode
            assert not engine.is_persistent

            engine.add_nodes(
                [
                    Node(id="resource-1", type="aws_vpc"),
                    Node(id="resource-2", type="aws_subnet"),
                ]
            )
            engine.add_edge(
                Edge(source_id="resource-2", target_id="resource-1", relation="in")
            )

            # Snapshot to file
            snapshot_path = str(Path(tmpdir) / "snapshot.db")
            engine.snapshot(snapshot_path)
            engine.close()

            # Load and verify
            restored = UnifiedGraphEngine.load_snapshot(snapshot_path)
            assert restored.node_count() == 2
            assert restored.edge_count() == 1
            restored.close()


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_nonexistent_node_operations(self) -> None:
        """Test operations on nonexistent nodes."""
        engine = UnifiedGraphEngine()

        # Get nonexistent node
        node = engine.get_node("does-not-exist")
        assert node is None

        # Dependencies of nonexistent node
        deps = engine.get_dependencies("does-not-exist")
        assert deps == []

        # Dependents of nonexistent node
        dependents = engine.get_dependents("does-not-exist")
        assert dependents == []

        engine.close()

    def test_scan_session_error_handling(self) -> None:
        """Test error handling in scan sessions."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add some resources
        engine.add_node(Node(id="vpc-1", type="aws_vpc"))

        # End with failure
        engine.end_scan(session.id, success=False, error="AWS API rate limit exceeded")

        # Verify session status
        stored_session = engine.get_scan_session(session.id)
        assert stored_session is not None
        assert stored_session.status == ScanStatus.FAILED
        assert "rate limit" in stored_session.error_message

        engine.close()

    def test_duplicate_node_handling(self) -> None:
        """Test that duplicate nodes update rather than fail."""
        engine = UnifiedGraphEngine()

        engine.add_node(Node(id="vpc-1", type="aws_vpc", name="Original"))
        engine.add_node(Node(id="vpc-1", type="aws_vpc", name="Updated"))

        assert engine.node_count() == 1
        node = engine.get_node("vpc-1")
        assert node is not None
        assert node.name == "Updated"

        engine.close()

    def test_duplicate_edge_handling(self) -> None:
        """Test that duplicate edges raise an integrity error (expected behavior)."""
        import sqlite3

        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="a", type="aws_vpc"),
                Node(id="b", type="aws_subnet"),
            ]
        )

        # Add first edge
        engine.add_edge(Edge(source_id="b", target_id="a", relation="in"))

        # Adding same edge again should raise IntegrityError (UNIQUE constraint)
        with pytest.raises(sqlite3.IntegrityError):
            engine.add_edge(Edge(source_id="b", target_id="a", relation="in"))

        # Should only have one edge
        assert engine.edge_count() == 1

        engine.close()

    def test_context_manager_closes_properly(self) -> None:
        """Test that context manager closes engine properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with UnifiedGraphEngine(cache_dir=tmpdir) as engine:
                engine.add_node(Node(id="test", type="aws_vpc"))
                assert engine.node_count() == 1

            # After context exit, engine should be closed
            # Reopening should work
            engine2 = UnifiedGraphEngine(cache_dir=tmpdir)
            assert engine2.node_count() == 1
            engine2.close()


class TestCLICommandIntegrationPatterns:
    """Tests simulating how CLI commands would use the storage layer."""

    def test_scan_command_pattern(self) -> None:
        """Simulate scan command workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # Start scan session
            session = engine.start_scan(profile="default", region="us-east-1")

            # Scanners would add resources
            resources = [
                Node(id="vpc-1", type="aws_vpc", region="us-east-1"),
                Node(id="subnet-1", type="aws_subnet", region="us-east-1"),
                Node(id="sg-1", type="aws_security_group", region="us-east-1"),
            ]
            engine.add_nodes(resources)

            # Add dependencies
            engine.add_edges(
                [
                    Edge(source_id="subnet-1", target_id="vpc-1", relation="in_vpc"),
                    Edge(source_id="sg-1", target_id="vpc-1", relation="in_vpc"),
                ]
            )

            # End scan
            engine.end_scan(session.id)

            # Verify stats (like what scan command would print)
            stats = engine.get_stats()
            assert stats["node_count"] == 3
            assert stats["edge_count"] == 2

            engine.close()

    def test_analyze_command_pattern(self) -> None:
        """Simulate analyze command workflow."""
        engine = UnifiedGraphEngine()

        # Add a realistic graph
        engine.add_nodes(
            [
                Node(id="vpc-main", type="aws_vpc"),
                Node(id="subnet-pub", type="aws_subnet"),
                Node(id="subnet-priv", type="aws_subnet"),
                Node(id="nat-gw", type="aws_nat_gateway"),
                Node(id="igw", type="aws_internet_gateway"),
                Node(id="web-server", type="aws_instance"),
                Node(id="db-server", type="aws_instance"),
            ]
        )

        engine.add_edges(
            [
                Edge(source_id="subnet-pub", target_id="vpc-main", relation="in_vpc"),
                Edge(source_id="subnet-priv", target_id="vpc-main", relation="in_vpc"),
                Edge(source_id="nat-gw", target_id="subnet-pub", relation="in_subnet"),
                Edge(source_id="igw", target_id="vpc-main", relation="attached_to"),
                Edge(
                    source_id="web-server", target_id="subnet-pub", relation="in_subnet"
                ),
                Edge(
                    source_id="db-server", target_id="subnet-priv", relation="in_subnet"
                ),
            ]
        )

        # Critical resource analysis (--critical)
        # Use "degree" algorithm to avoid numpy dependency
        critical = engine.get_most_critical_resources(top_n=5, algorithm="degree")
        assert len(critical) > 0

        # SPOF analysis (--spof)
        spofs = engine.find_single_points_of_failure(min_dependents=2)
        assert len(spofs) > 0

        # Blast radius (--blast-radius vpc-main)
        impact = engine.get_impact_analysis("vpc-main")
        assert impact["blast_radius"] >= 2  # At least 2 subnets depend on VPC

        engine.close()

    def test_deps_command_pattern(self) -> None:
        """Simulate deps command workflow."""
        engine = UnifiedGraphEngine()

        # Build a dependency graph
        engine.add_nodes(
            [
                Node(id="alb-web", type="aws_lb"),
                Node(id="tg-web", type="aws_lb_target_group"),
                Node(id="asg-web", type="aws_autoscaling_group"),
                Node(id="lc-web", type="aws_launch_configuration"),
                Node(id="ami-base", type="aws_ami"),
            ]
        )

        engine.add_edges(
            [
                Edge(source_id="alb-web", target_id="tg-web", relation="forwards_to"),
                Edge(source_id="tg-web", target_id="asg-web", relation="targets"),
                Edge(source_id="asg-web", target_id="lc-web", relation="uses"),
                Edge(source_id="lc-web", target_id="ami-base", relation="uses"),
            ]
        )

        # Get dependencies of ALB (what it depends on)
        deps = engine.get_dependencies("alb-web", recursive=True)
        dep_ids = {n.id for n in deps}
        assert "tg-web" in dep_ids
        assert "asg-web" in dep_ids
        assert "lc-web" in dep_ids
        assert "ami-base" in dep_ids

        # Get dependents of AMI (what depends on it)
        dependents = engine.get_dependents("ami-base", recursive=True)
        dependent_ids = {n.id for n in dependents}
        assert "lc-web" in dependent_ids
        assert "asg-web" in dependent_ids
        assert "tg-web" in dependent_ids
        assert "alb-web" in dependent_ids

        engine.close()

    def test_graph_command_pattern(self) -> None:
        """Simulate graph command workflow (visualization data export)."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc-1", type="aws_vpc", name="Main VPC"),
                Node(id="subnet-1", type="aws_subnet", name="Subnet A"),
            ]
        )
        engine.add_edge(Edge(source_id="subnet-1", target_id="vpc-1", relation="in"))

        # Export all resources (for D3.js visualization)
        resources = engine.get_all_resources()
        assert len(resources) == 2

        # Each resource should have visualization-friendly data
        for resource in resources:
            assert "id" in resource
            assert "type" in resource
            assert "name" in resource

        engine.close()

    def test_snapshot_command_pattern(self) -> None:
        """Simulate snapshot save/list/diff workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # Add initial data
            engine.add_nodes(
                [
                    Node(id="vpc-1", type="aws_vpc"),
                    Node(id="subnet-1", type="aws_subnet"),
                ]
            )

            # Create snapshot (snapshot save) with explicit path
            snapshot1_path = str(Path(tmpdir) / "snapshot_1.db")
            result_path1 = engine.snapshot(snapshot1_path)
            assert Path(result_path1).exists()

            # Add more data
            engine.add_node(Node(id="instance-1", type="aws_instance"))

            # Create another snapshot with different name
            snapshot2_path = str(Path(tmpdir) / "snapshot_2.db")
            result_path2 = engine.snapshot(snapshot2_path)
            assert Path(result_path2).exists()

            # List snapshots (snapshot list)
            snapshots = list(Path(tmpdir).glob("snapshot_*.db"))
            assert len(snapshots) >= 2

            engine.close()


class TestFTSSearch:
    """Tests for full-text search functionality."""

    def test_search_by_name(self) -> None:
        """Test searching nodes by name."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc-1", type="aws_vpc", name="Production VPC"),
                Node(id="vpc-2", type="aws_vpc", name="Staging VPC"),
                Node(id="vpc-3", type="aws_vpc", name="Development Network"),
            ]
        )

        # Search for "Production"
        results = engine.search("Production")
        assert len(results) >= 1
        assert any(n.name == "Production VPC" for n in results)

        engine.close()

    def test_search_by_type(self) -> None:
        """Test searching nodes by type."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc-1", type="aws_vpc"),
                Node(id="subnet-1", type="aws_subnet"),
                Node(id="sg-1", type="aws_security_group"),
            ]
        )

        # Search for "subnet"
        results = engine.search("subnet")
        assert len(results) >= 1
        assert any(n.type == "aws_subnet" for n in results)

        engine.close()

    def test_search_by_id(self) -> None:
        """Test searching nodes by ID."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc-abc123", type="aws_vpc"),
                Node(id="vpc-xyz789", type="aws_vpc"),
            ]
        )

        # Search for partial ID
        results = engine.search("abc123")
        assert len(results) >= 1
        assert any(n.id == "vpc-abc123" for n in results)

        engine.close()


class TestMetadata:
    """Tests for metadata storage."""

    def test_metadata_roundtrip(self) -> None:
        """Test metadata set and get."""
        engine = UnifiedGraphEngine()

        engine.set_metadata("scan_time", "2025-01-06T12:00:00")
        engine.set_metadata("version", "1.0")
        engine.set_metadata("scanner_count", "15")

        assert engine.get_metadata("scan_time") == "2025-01-06T12:00:00"
        assert engine.get_metadata("version") == "1.0"
        assert engine.get_metadata("scanner_count") == "15"
        assert engine.get_metadata("nonexistent") is None

        engine.close()

    def test_metadata_persistence(self) -> None:
        """Test that metadata persists across reopens."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)
            engine.set_metadata("key1", "value1")
            engine.close()

            engine2 = UnifiedGraphEngine(cache_dir=tmpdir)
            assert engine2.get_metadata("key1") == "value1"
            engine2.close()


class TestCLICommandIntegrationPatternsExtended:
    """Additional tests covering ALL CLI commands that use the storage layer."""

    def test_clone_command_pattern(self) -> None:
        """Simulate clone command workflow (Terraform generation from graph)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources typical for clone command (VPC, subnets, instances)
        engine.add_nodes(
            [
                Node(
                    id="vpc-prod",
                    type="aws_vpc",
                    name="production-vpc",
                    attributes={
                        "cidr_block": "10.0.0.0/16",
                        "enable_dns_hostnames": True,
                        "enable_dns_support": True,
                        "tags": {"Name": "production-vpc", "Environment": "prod"},
                    },
                ),
                Node(
                    id="subnet-pub-1",
                    type="aws_subnet",
                    name="public-subnet-1",
                    attributes={
                        "vpc_id": "vpc-prod",
                        "cidr_block": "10.0.1.0/24",
                        "availability_zone": "us-east-1a",
                        "map_public_ip_on_launch": True,
                    },
                ),
                Node(
                    id="i-web-01",
                    type="aws_instance",
                    name="web-server-01",
                    attributes={
                        "instance_type": "t3.small",
                        "ami": "ami-12345678",
                        "subnet_id": "subnet-pub-1",
                        "key_name": "prod-key",
                        "tags": {"Name": "web-server-01", "Role": "web"},
                    },
                ),
                Node(
                    id="sg-web",
                    type="aws_security_group",
                    name="web-security-group",
                    attributes={
                        "vpc_id": "vpc-prod",
                        "description": "Web server security group",
                        "ingress": [
                            {
                                "from_port": 80,
                                "to_port": 80,
                                "protocol": "tcp",
                                "cidr_blocks": ["0.0.0.0/0"],
                            },
                            {
                                "from_port": 443,
                                "to_port": 443,
                                "protocol": "tcp",
                                "cidr_blocks": ["0.0.0.0/0"],
                            },
                        ],
                    },
                ),
            ]
        )

        # Add dependencies
        engine.add_edges(
            [
                Edge(source_id="subnet-pub-1", target_id="vpc-prod", relation="in_vpc"),
                Edge(
                    source_id="i-web-01", target_id="subnet-pub-1", relation="in_subnet"
                ),
                Edge(source_id="i-web-01", target_id="sg-web", relation="uses_sg"),
                Edge(source_id="sg-web", target_id="vpc-prod", relation="in_vpc"),
            ]
        )

        engine.end_scan(session.id)

        # Clone command would get all resources for Terraform generation
        all_resources = engine.get_all_resources()
        assert len(all_resources) == 4

        # Verify resource attributes are preserved (needed for Terraform output)
        vpc = engine.get_node("vpc-prod")
        assert vpc is not None
        assert vpc.attributes["cidr_block"] == "10.0.0.0/16"
        assert vpc.attributes["tags"]["Environment"] == "prod"

        # Get safe apply order (Terraform apply order)
        apply_order = engine.safe_apply_order()
        vpc_idx = apply_order.index("vpc-prod")
        subnet_idx = apply_order.index("subnet-pub-1")
        instance_idx = apply_order.index("i-web-01")
        assert vpc_idx < subnet_idx < instance_idx

        engine.close()

    def test_audit_command_pattern(self) -> None:
        """Simulate audit command workflow (security scanning with graph)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources with security-relevant attributes
        engine.add_nodes(
            [
                Node(
                    id="s3-logs",
                    type="aws_s3_bucket",
                    name="company-logs",
                    attributes={
                        "bucket": "company-logs-bucket",
                        "acl": "private",
                        "versioning": {"enabled": True},
                        "server_side_encryption_configuration": {
                            "rule": {
                                "apply_server_side_encryption_by_default": {
                                    "sse_algorithm": "AES256"
                                }
                            }
                        },
                    },
                ),
                Node(
                    id="s3-public",
                    type="aws_s3_bucket",
                    name="public-assets",
                    attributes={
                        "bucket": "public-assets-bucket",
                        "acl": "public-read",  # Security finding!
                        "versioning": {"enabled": False},
                    },
                ),
                Node(
                    id="rds-main",
                    type="aws_db_instance",
                    name="main-database",
                    attributes={
                        "engine": "postgres",
                        "storage_encrypted": True,
                        "publicly_accessible": False,
                        "backup_retention_period": 7,
                        "multi_az": True,
                    },
                ),
                Node(
                    id="rds-dev",
                    type="aws_db_instance",
                    name="dev-database",
                    attributes={
                        "engine": "mysql",
                        "storage_encrypted": False,  # Security finding!
                        "publicly_accessible": True,  # Security finding!
                        "backup_retention_period": 0,  # Security finding!
                    },
                ),
            ]
        )

        engine.end_scan(session.id)

        # Audit command queries resources and checks attributes
        all_nodes = engine.get_all_nodes()

        # Count security issues (simulating audit checks)
        security_findings = []
        for node in all_nodes:
            if node.type == "aws_s3_bucket":
                if node.attributes.get("acl") == "public-read":
                    security_findings.append(f"{node.id}: Public S3 bucket")
            elif node.type == "aws_db_instance":
                if not node.attributes.get("storage_encrypted"):
                    security_findings.append(f"{node.id}: Unencrypted RDS")
                if node.attributes.get("publicly_accessible"):
                    security_findings.append(f"{node.id}: Public RDS instance")
                if node.attributes.get("backup_retention_period", 0) == 0:
                    security_findings.append(f"{node.id}: No backups enabled")

        # Should find 4 security issues
        assert len(security_findings) == 4

        engine.close()

    def test_drift_command_pattern(self) -> None:
        """Simulate drift command workflow (comparing state to live resources)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            engine = UnifiedGraphEngine(cache_dir=tmpdir)

            # Simulate "Terraform state" as baseline scan
            session1 = engine.start_scan(profile="prod", region="us-east-1")
            engine.add_nodes(
                [
                    Node(
                        id="i-baseline",
                        type="aws_instance",
                        name="web-server",
                        attributes={
                            "instance_type": "t3.medium",
                            "ami": "ami-12345678",
                        },
                    ),
                    Node(
                        id="sg-baseline",
                        type="aws_security_group",
                        name="web-sg",
                        attributes={
                            "ingress": [{"from_port": 80, "to_port": 80}],
                        },
                    ),
                ]
            )
            engine.end_scan(session1.id)

            # Create snapshot as "baseline" state
            baseline_path = str(Path(tmpdir) / "baseline.db")
            engine.snapshot(baseline_path)

            # Now simulate "live" AWS state with drift
            session2 = engine.start_scan(profile="prod", region="us-east-1")
            engine.add_nodes(
                [
                    Node(
                        id="i-baseline",
                        type="aws_instance",
                        name="web-server",
                        attributes={
                            "instance_type": "t3.large",  # DRIFTED - changed!
                            "ami": "ami-12345678",
                        },
                    ),
                    Node(
                        id="sg-baseline",
                        type="aws_security_group",
                        name="web-sg",
                        attributes={
                            "ingress": [
                                {"from_port": 80, "to_port": 80},
                                {"from_port": 22, "to_port": 22},  # DRIFTED - new rule!
                            ],
                        },
                    ),
                    Node(
                        id="i-unmanaged",
                        type="aws_instance",
                        name="rogue-server",  # DRIFTED - new resource!
                        attributes={"instance_type": "t2.micro"},
                    ),
                ]
            )
            engine.end_scan(session2.id)
            engine.cleanup_stale_resources(session2.id)

            # Drift detection: Load baseline and compare
            baseline_engine = UnifiedGraphEngine(db_path=baseline_path)

            baseline_nodes = {n.id: n for n in baseline_engine.get_all_nodes()}
            live_nodes = {n.id: n for n in engine.get_all_nodes()}

            # Detect drift
            added = set(live_nodes.keys()) - set(baseline_nodes.keys())
            removed = set(baseline_nodes.keys()) - set(live_nodes.keys())
            modified = []
            for node_id in set(baseline_nodes.keys()) & set(live_nodes.keys()):
                if baseline_nodes[node_id].attributes != live_nodes[node_id].attributes:
                    modified.append(node_id)

            assert "i-unmanaged" in added  # New unmanaged resource
            assert len(removed) == 0  # Nothing removed
            assert "i-baseline" in modified  # Instance type changed
            assert "sg-baseline" in modified  # Ingress rules changed

            baseline_engine.close()
            engine.close()

    def test_cost_command_pattern(self) -> None:
        """Simulate cost command workflow (cost estimation from graph)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources with cost-relevant attributes
        engine.add_nodes(
            [
                Node(
                    id="i-large-1",
                    type="aws_instance",
                    name="compute-heavy-1",
                    attributes={
                        "instance_type": "c5.4xlarge",
                        "state": "running",
                    },
                ),
                Node(
                    id="i-large-2",
                    type="aws_instance",
                    name="compute-heavy-2",
                    attributes={
                        "instance_type": "c5.4xlarge",
                        "state": "running",
                    },
                ),
                Node(
                    id="rds-main",
                    type="aws_db_instance",
                    name="production-db",
                    attributes={
                        "db_instance_class": "db.r5.2xlarge",
                        "engine": "postgres",
                        "multi_az": True,
                        "allocated_storage": 500,
                    },
                ),
                Node(
                    id="nat-1",
                    type="aws_nat_gateway",
                    name="nat-gateway-1",
                    attributes={"state": "available"},
                ),
                Node(
                    id="ebs-vol-1",
                    type="aws_ebs_volume",
                    name="data-volume",
                    attributes={
                        "volume_type": "gp3",
                        "size": 1000,
                        "iops": 3000,
                    },
                ),
            ]
        )

        engine.end_scan(session.id)

        # Cost command would iterate resources and calculate estimates
        all_nodes = engine.get_all_nodes()

        # Simulate cost calculation based on resource types
        cost_by_type: dict[str, float] = {}
        for node in all_nodes:
            if node.type == "aws_instance":
                # Simplified pricing
                instance_type = node.attributes.get("instance_type", "")
                if "4xlarge" in instance_type:
                    cost = 500.0  # Monthly estimate
                elif "xlarge" in instance_type:
                    cost = 200.0
                else:
                    cost = 50.0
                cost_by_type.setdefault("EC2", 0.0)
                cost_by_type["EC2"] += cost
            elif node.type == "aws_db_instance":
                cost_by_type.setdefault("RDS", 0.0)
                cost_by_type["RDS"] += 800.0  # Multi-AZ r5.2xlarge estimate
            elif node.type == "aws_nat_gateway":
                cost_by_type.setdefault("NAT Gateway", 0.0)
                cost_by_type["NAT Gateway"] += 45.0  # Base monthly cost
            elif node.type == "aws_ebs_volume":
                size = node.attributes.get("size", 0)
                cost_by_type.setdefault("EBS", 0.0)
                cost_by_type["EBS"] += size * 0.08  # GP3 pricing

        assert cost_by_type["EC2"] == 1000.0  # 2 x c5.4xlarge
        assert cost_by_type["RDS"] == 800.0
        assert cost_by_type["NAT Gateway"] == 45.0
        assert cost_by_type["EBS"] == 80.0  # 1000GB x $0.08

        engine.close()

    def test_dr_command_pattern(self) -> None:
        """Simulate DR (disaster recovery) command workflow."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources with DR-relevant attributes
        engine.add_nodes(
            [
                Node(
                    id="rds-primary",
                    type="aws_db_instance",
                    name="primary-db",
                    attributes={
                        "engine": "postgres",
                        "multi_az": True,
                        "backup_retention_period": 7,
                        "storage_encrypted": True,
                        "availability_zone": "us-east-1a",
                    },
                ),
                Node(
                    id="rds-replica",
                    type="aws_db_instance",
                    name="replica-db",
                    attributes={
                        "engine": "postgres",
                        "replicate_source_db": "rds-primary",
                        "availability_zone": "us-west-2a",  # Cross-region replica
                    },
                ),
                Node(
                    id="s3-backup",
                    type="aws_s3_bucket",
                    name="backup-bucket",
                    attributes={
                        "bucket": "prod-backups",
                        "versioning": {"enabled": True},
                        "replication_configuration": {
                            "rules": [
                                {"destination": {"bucket": "arn:aws:s3:::dr-backups"}}
                            ]
                        },
                    },
                ),
                Node(
                    id="asg-web",
                    type="aws_autoscaling_group",
                    name="web-asg",
                    attributes={
                        "min_size": 2,
                        "max_size": 10,
                        "desired_capacity": 4,
                        "availability_zones": ["us-east-1a", "us-east-1b"],
                    },
                ),
            ]
        )

        engine.add_edge(
            Edge(
                source_id="rds-replica", target_id="rds-primary", relation="replicates"
            )
        )

        engine.end_scan(session.id)

        # DR assessment: Check for DR capabilities
        dr_score = 0
        dr_findings = []

        for node in engine.get_all_nodes():
            if node.type == "aws_db_instance":
                if node.attributes.get("multi_az"):
                    dr_score += 20
                    dr_findings.append(f"{node.id}: Multi-AZ enabled")
                if node.attributes.get("backup_retention_period", 0) > 0:
                    dr_score += 10
                    dr_findings.append(f"{node.id}: Backups enabled")
                if node.attributes.get("replicate_source_db"):
                    dr_score += 30  # Cross-region replica
                    dr_findings.append(f"{node.id}: Cross-region replica")
            elif node.type == "aws_s3_bucket":
                if node.attributes.get("replication_configuration"):
                    dr_score += 15
                    dr_findings.append(f"{node.id}: S3 replication enabled")
            elif node.type == "aws_autoscaling_group":
                azs = node.attributes.get("availability_zones", [])
                if len(azs) >= 2:
                    dr_score += 15
                    dr_findings.append(f"{node.id}: Multi-AZ ASG")

        assert dr_score == 90  # Good DR posture
        assert len(dr_findings) == 5

        engine.close()

    def test_transfer_command_pattern(self) -> None:
        """Simulate transfer command workflow (data transfer cost analysis)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources with networking topology for transfer analysis
        engine.add_nodes(
            [
                Node(
                    id="vpc-main",
                    type="aws_vpc",
                    name="main-vpc",
                    attributes={"cidr_block": "10.0.0.0/16"},
                ),
                Node(
                    id="subnet-pub-1a",
                    type="aws_subnet",
                    name="public-1a",
                    attributes={
                        "vpc_id": "vpc-main",
                        "availability_zone": "us-east-1a",
                    },
                ),
                Node(
                    id="subnet-priv-1a",
                    type="aws_subnet",
                    name="private-1a",
                    attributes={
                        "vpc_id": "vpc-main",
                        "availability_zone": "us-east-1a",
                    },
                ),
                Node(
                    id="subnet-priv-1b",
                    type="aws_subnet",
                    name="private-1b",
                    attributes={
                        "vpc_id": "vpc-main",
                        "availability_zone": "us-east-1b",  # Different AZ!
                    },
                ),
                Node(
                    id="nat-1",
                    type="aws_nat_gateway",
                    name="nat-gateway",
                    attributes={"subnet_id": "subnet-pub-1a"},
                ),
                Node(
                    id="i-app-1a",
                    type="aws_instance",
                    name="app-server-1a",
                    attributes={
                        "subnet_id": "subnet-priv-1a",
                        "availability_zone": "us-east-1a",
                    },
                ),
                Node(
                    id="i-app-1b",
                    type="aws_instance",
                    name="app-server-1b",
                    attributes={
                        "subnet_id": "subnet-priv-1b",
                        "availability_zone": "us-east-1b",
                    },
                ),
            ]
        )

        engine.add_edges(
            [
                Edge(
                    source_id="subnet-pub-1a", target_id="vpc-main", relation="in_vpc"
                ),
                Edge(
                    source_id="subnet-priv-1a", target_id="vpc-main", relation="in_vpc"
                ),
                Edge(
                    source_id="subnet-priv-1b", target_id="vpc-main", relation="in_vpc"
                ),
                Edge(
                    source_id="nat-1", target_id="subnet-pub-1a", relation="in_subnet"
                ),
                Edge(
                    source_id="i-app-1a",
                    target_id="subnet-priv-1a",
                    relation="in_subnet",
                ),
                Edge(
                    source_id="i-app-1b",
                    target_id="subnet-priv-1b",
                    relation="in_subnet",
                ),
                Edge(
                    source_id="i-app-1a",
                    target_id="i-app-1b",
                    relation="communicates_with",
                ),
            ]
        )

        engine.end_scan(session.id)

        # Transfer analysis: Find cross-AZ communication
        # Iterate through all nodes and check their outgoing edges
        cross_az_pairs = []
        for node in engine.get_all_nodes():
            for edge in engine.get_edges_from(node.id):
                if edge.relation == "communicates_with":
                    source = engine.get_node(edge.source_id)
                    target = engine.get_node(edge.target_id)
                    if source and target:
                        source_az = source.attributes.get("availability_zone", "")
                        target_az = target.attributes.get("availability_zone", "")
                        if source_az and target_az and source_az != target_az:
                            cross_az_pairs.append((edge.source_id, edge.target_id))

        # Should detect cross-AZ communication
        assert len(cross_az_pairs) == 1
        assert ("i-app-1a", "i-app-1b") in cross_az_pairs

        # Count NAT gateways (potential internet egress cost)
        nat_count = len(
            [n for n in engine.get_all_nodes() if n.type == "aws_nat_gateway"]
        )
        assert nat_count == 1

        engine.close()

    def test_unused_command_pattern(self) -> None:
        """Simulate unused command workflow (unused resource detection)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources with varying utilization
        engine.add_nodes(
            [
                # Active resources
                Node(
                    id="i-active",
                    type="aws_instance",
                    name="active-server",
                    attributes={
                        "instance_type": "t3.medium",
                        "state": "running",
                    },
                ),
                # Stopped instance (potentially unused)
                Node(
                    id="i-stopped",
                    type="aws_instance",
                    name="stopped-server",
                    attributes={
                        "instance_type": "t3.large",
                        "state": "stopped",
                    },
                ),
                # Unattached EBS volume (unused)
                Node(
                    id="vol-unattached",
                    type="aws_ebs_volume",
                    name="orphan-volume",
                    attributes={
                        "volume_type": "gp3",
                        "size": 500,
                        "state": "available",  # Not attached
                    },
                ),
                # Attached EBS volume (used)
                Node(
                    id="vol-attached",
                    type="aws_ebs_volume",
                    name="active-volume",
                    attributes={
                        "volume_type": "gp3",
                        "size": 100,
                        "state": "in-use",
                    },
                ),
                # Unused elastic IP
                Node(
                    id="eip-unused",
                    type="aws_eip",
                    name="orphan-eip",
                    attributes={
                        "public_ip": "3.4.5.6",
                        "association_id": None,  # Not associated
                    },
                ),
                # Used elastic IP
                Node(
                    id="eip-used",
                    type="aws_eip",
                    name="active-eip",
                    attributes={
                        "public_ip": "1.2.3.4",
                        "association_id": "eipassoc-12345",
                    },
                ),
            ]
        )

        # Add edge for attached volume
        engine.add_edge(
            Edge(source_id="vol-attached", target_id="i-active", relation="attached_to")
        )

        engine.end_scan(session.id)

        # Unused detection logic
        unused_resources = []
        for node in engine.get_all_nodes():
            if node.type == "aws_instance":
                if node.attributes.get("state") == "stopped":
                    unused_resources.append((node.id, "Stopped instance"))
            elif node.type == "aws_ebs_volume":
                if node.attributes.get("state") == "available":
                    unused_resources.append((node.id, "Unattached volume"))
            elif node.type == "aws_eip":
                if not node.attributes.get("association_id"):
                    unused_resources.append((node.id, "Unassociated EIP"))

        # Should find 3 unused resources
        assert len(unused_resources) == 3
        unused_ids = [r[0] for r in unused_resources]
        assert "i-stopped" in unused_ids
        assert "vol-unattached" in unused_ids
        assert "eip-unused" in unused_ids

        engine.close()

    def test_validate_command_pattern(self) -> None:
        """Simulate validate command workflow (topology constraint validation)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add resources to validate against constraints
        engine.add_nodes(
            [
                Node(
                    id="rds-encrypted",
                    type="aws_db_instance",
                    name="secure-db",
                    attributes={
                        "storage_encrypted": True,
                        "publicly_accessible": False,
                        "tags": {"Environment": "prod", "Owner": "team-a"},
                    },
                ),
                Node(
                    id="rds-unencrypted",
                    type="aws_db_instance",
                    name="insecure-db",
                    attributes={
                        "storage_encrypted": False,  # Violates constraint
                        "publicly_accessible": True,  # Violates constraint
                        "tags": {},  # Missing required tags
                    },
                ),
                Node(
                    id="s3-encrypted",
                    type="aws_s3_bucket",
                    name="secure-bucket",
                    attributes={
                        "server_side_encryption": "AES256",
                        "tags": {"Environment": "prod", "Owner": "team-b"},
                    },
                ),
                Node(
                    id="s3-unencrypted",
                    type="aws_s3_bucket",
                    name="insecure-bucket",
                    attributes={
                        "server_side_encryption": None,  # Violates constraint
                        "tags": {"Environment": "prod"},  # Missing Owner tag
                    },
                ),
            ]
        )

        engine.end_scan(session.id)

        # Simulate constraint validation
        violations = []

        # Constraint 1: RDS must be encrypted
        for node in engine.get_all_nodes():
            if node.type == "aws_db_instance":
                if not node.attributes.get("storage_encrypted"):
                    violations.append(
                        {
                            "constraint": "require-rds-encryption",
                            "resource": node.id,
                            "severity": "critical",
                        }
                    )
                if node.attributes.get("publicly_accessible"):
                    violations.append(
                        {
                            "constraint": "prohibit-public-rds",
                            "resource": node.id,
                            "severity": "critical",
                        }
                    )
            elif node.type == "aws_s3_bucket":
                if not node.attributes.get("server_side_encryption"):
                    violations.append(
                        {
                            "constraint": "require-s3-encryption",
                            "resource": node.id,
                            "severity": "critical",
                        }
                    )

        # Constraint 2: Required tags
        for node in engine.get_all_nodes():
            tags = node.attributes.get("tags", {})
            if "Environment" not in tags:
                violations.append(
                    {
                        "constraint": "require-environment-tag",
                        "resource": node.id,
                        "severity": "high",
                    }
                )
            if "Owner" not in tags:
                violations.append(
                    {
                        "constraint": "require-owner-tag",
                        "resource": node.id,
                        "severity": "medium",
                    }
                )

        # Should find violations
        assert len(violations) >= 4  # At least encryption and public access issues

        critical_violations = [v for v in violations if v["severity"] == "critical"]
        assert (
            len(critical_violations) >= 3
        )  # RDS encryption, public access, S3 encryption

        engine.close()

    def test_iam_command_pattern(self) -> None:
        """Simulate IAM command workflow (least-privilege policy generation)."""
        engine = UnifiedGraphEngine()

        session = engine.start_scan(profile="prod", region="us-east-1")

        # Add compute resource with dependencies
        engine.add_nodes(
            [
                Node(
                    id="lambda-processor",
                    type="aws_lambda_function",
                    name="data-processor",
                    attributes={
                        "function_name": "data-processor",
                        "runtime": "python3.11",
                        "handler": "handler.main",
                    },
                ),
                Node(
                    id="sqs-input",
                    type="aws_sqs_queue",
                    name="input-queue",
                    attributes={
                        "queue_name": "data-input-queue",
                        "arn": "arn:aws:sqs:us-east-1:123456789012:data-input-queue",
                    },
                ),
                Node(
                    id="s3-output",
                    type="aws_s3_bucket",
                    name="output-bucket",
                    attributes={
                        "bucket": "processed-data-output",
                        "arn": "arn:aws:s3:::processed-data-output",
                    },
                ),
                Node(
                    id="dynamodb-state",
                    type="aws_dynamodb_table",
                    name="state-table",
                    attributes={
                        "table_name": "processor-state",
                        "arn": "arn:aws:dynamodb:us-east-1:123456789012:table/processor-state",
                    },
                ),
                Node(
                    id="kms-key",
                    type="aws_kms_key",
                    name="encryption-key",
                    attributes={
                        "key_id": "12345678-1234-1234-1234-123456789012",
                        "arn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
                    },
                ),
            ]
        )

        # Lambda dependencies
        engine.add_edges(
            [
                Edge(
                    source_id="lambda-processor",
                    target_id="sqs-input",
                    relation="reads_from",
                ),
                Edge(
                    source_id="lambda-processor",
                    target_id="s3-output",
                    relation="writes_to",
                ),
                Edge(
                    source_id="lambda-processor",
                    target_id="dynamodb-state",
                    relation="uses",
                ),
                Edge(
                    source_id="lambda-processor",
                    target_id="kms-key",
                    relation="uses_key",
                ),
            ]
        )

        engine.end_scan(session.id)

        # IAM policy generation: Get dependencies
        lambda_deps = engine.get_dependencies("lambda-processor")
        dep_ids = {n.id for n in lambda_deps}

        assert "sqs-input" in dep_ids
        assert "s3-output" in dep_ids
        assert "dynamodb-state" in dep_ids
        assert "kms-key" in dep_ids

        # Generate policy statements based on resource types
        policy_statements = []
        for dep in lambda_deps:
            if dep.type == "aws_sqs_queue":
                policy_statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "sqs:ReceiveMessage",
                            "sqs:DeleteMessage",
                            "sqs:GetQueueAttributes",
                        ],
                        "Resource": dep.attributes.get("arn", "*"),
                    }
                )
            elif dep.type == "aws_s3_bucket":
                policy_statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["s3:PutObject", "s3:GetObject"],
                        "Resource": [
                            dep.attributes.get("arn", "*"),
                            f"{dep.attributes.get('arn', '*')}/*",
                        ],
                    }
                )
            elif dep.type == "aws_dynamodb_table":
                policy_statements.append(
                    {
                        "Effect": "Allow",
                        "Action": [
                            "dynamodb:GetItem",
                            "dynamodb:PutItem",
                            "dynamodb:UpdateItem",
                        ],
                        "Resource": dep.attributes.get("arn", "*"),
                    }
                )
            elif dep.type == "aws_kms_key":
                policy_statements.append(
                    {
                        "Effect": "Allow",
                        "Action": ["kms:Decrypt", "kms:Encrypt", "kms:GenerateDataKey"],
                        "Resource": dep.attributes.get("arn", "*"),
                    }
                )

        # Should generate 4 policy statements (one per dependency)
        assert len(policy_statements) == 4

        engine.close()


class TestNetworkXProjection:
    """Tests for NetworkX projection functionality."""

    def test_to_networkx_lightweight(self) -> None:
        """Test lightweight NetworkX projection."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="a", type="aws_vpc", name="VPC A"),
                Node(id="b", type="aws_subnet", name="Subnet B"),
            ]
        )
        engine.add_edge(Edge(source_id="b", target_id="a", relation="in_vpc"))

        G = engine.to_networkx(lightweight=True)

        assert G.number_of_nodes() == 2
        assert G.number_of_edges() == 1
        assert "a" in G.nodes
        assert "b" in G.nodes

        engine.close()

    def test_centrality_calculations(self) -> None:
        """Test centrality metric calculations."""
        engine = UnifiedGraphEngine()

        # Create a hub-and-spoke topology
        engine.add_node(Node(id="hub", type="aws_vpc"))
        for i in range(5):
            engine.add_node(Node(id=f"spoke-{i}", type="aws_subnet"))
            engine.add_edge(
                Edge(source_id=f"spoke-{i}", target_id="hub", relation="in")
            )

        # Degree centrality
        degree = engine.get_centrality("degree")
        assert degree["hub"] > degree["spoke-0"]
        assert "hub" in degree
        assert all(f"spoke-{i}" in degree for i in range(5))

        # Betweenness (doesn't require numpy)
        betweenness = engine.get_centrality("betweenness")
        assert "hub" in betweenness

        engine.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
