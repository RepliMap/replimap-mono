"""
Tests for the GraphStore storage layer.

Tests cover:
- Basic CRUD operations
- SQLite + Zstd compression
- Multi-account support with node_id prefixes
- Lazy loading (topology vs full config)
- Atomic transactions
- Performance targets
- Migration from JSON
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.core.storage import (
    ConfigCompressor,
    GraphStore,
    migrate_from_json,
)


class TestConfigCompressor:
    """Tests for the Zstd compression layer."""

    def test_compress_decompress_roundtrip(self) -> None:
        """Config survives compression and decompression."""
        compressor = ConfigCompressor()

        config = {
            "VpcId": "vpc-12345678",
            "CidrBlock": "10.0.0.0/16",
            "Tags": [
                {"Key": "Name", "Value": "Production VPC"},
                {"Key": "Environment", "Value": "production"},
            ],
            "EnableDnsHostnames": True,
            "EnableDnsSupport": True,
        }

        compressed, config_hash, original_size = compressor.compress(config)
        decompressed = compressor.decompress(compressed)

        assert decompressed == config
        assert len(config_hash) == 64  # SHA256 hex
        assert original_size > 0

    def test_compression_ratio(self) -> None:
        """Compression achieves reasonable ratio for typical configs."""
        compressor = ConfigCompressor()

        # Simulate a typical EC2 instance config
        config = {
            "InstanceId": "i-1234567890abcdef0",
            "InstanceType": "t3.micro",
            "ImageId": "ami-12345678",
            "SubnetId": "subnet-12345678",
            "VpcId": "vpc-12345678",
            "SecurityGroups": [{"GroupId": "sg-12345678", "GroupName": "default"}],
            "Tags": [
                {"Key": "Name", "Value": "Web Server"},
                {"Key": "Environment", "Value": "production"},
                {"Key": "Team", "Value": "platform"},
            ],
            "State": {"Code": 16, "Name": "running"},
            "Monitoring": {"State": "disabled"},
            "BlockDeviceMappings": [
                {
                    "DeviceName": "/dev/xvda",
                    "Ebs": {
                        "VolumeId": "vol-12345678",
                        "Status": "attached",
                        "AttachTime": "2024-01-01T00:00:00Z",
                    },
                }
            ],
        }

        compressed, _, original_size = compressor.compress(config)
        compressed_size = len(compressed)

        ratio = original_size / compressed_size
        # Expect at least 1.5x compression for typical configs
        assert ratio > 1.5, f"Compression ratio {ratio:.2f} is too low"

    def test_hash_changes_with_config(self) -> None:
        """Different configs produce different hashes."""
        compressor = ConfigCompressor()

        config1 = {"VpcId": "vpc-111"}
        config2 = {"VpcId": "vpc-222"}

        _, hash1, _ = compressor.compress(config1)
        _, hash2, _ = compressor.compress(config2)

        assert hash1 != hash2

    def test_hash_stable_for_same_config(self) -> None:
        """Same config produces same hash."""
        compressor = ConfigCompressor()

        config = {"VpcId": "vpc-12345", "Tags": [{"Key": "Name", "Value": "Test"}]}

        _, hash1, _ = compressor.compress(config)
        _, hash2, _ = compressor.compress(config)

        assert hash1 == hash2


class TestGraphStore:
    """Tests for the main storage engine."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> GraphStore:
        """Create a temporary GraphStore for testing."""
        db_path = tmp_path / "test_graph.db"
        return GraphStore(db_path=db_path)

    @pytest.fixture
    def sample_graph(self) -> GraphEngine:
        """Create a sample graph for testing."""
        graph = GraphEngine()

        # Add VPC
        vpc = ResourceNode(
            id="vpc-12345678",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"VpcId": "vpc-12345678", "CidrBlock": "10.0.0.0/16"},
            tags={"Name": "TestVPC", "Environment": "test"},
        )
        graph.add_resource(vpc)

        # Add Subnet
        subnet = ResourceNode(
            id="subnet-12345678",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={"SubnetId": "subnet-12345678", "VpcId": "vpc-12345678"},
            tags={"Name": "TestSubnet"},
        )
        graph.add_resource(subnet)

        # Add EC2 instance
        instance = ResourceNode(
            id="i-12345678",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "InstanceId": "i-12345678",
                "InstanceType": "t3.micro",
                "SubnetId": "subnet-12345678",
            },
            tags={"Name": "TestInstance"},
        )
        graph.add_resource(instance)

        # Add dependencies
        graph.add_dependency("subnet-12345678", "vpc-12345678")
        graph.add_dependency("i-12345678", "subnet-12345678")

        return graph

    def test_save_and_load_topology(
        self, store: GraphStore, sample_graph: GraphEngine
    ) -> None:
        """Graph topology can be saved and loaded."""
        account_id = "123456789012"

        # Save
        count = store.save_graph(sample_graph, account_id)
        assert count == 3

        # Load topology
        nodes = store.load_topology(account_id=account_id)
        assert len(nodes) == 3

        # Verify node info
        node_ids = {n.node_id for n in nodes}
        assert f"{account_id}:us-east-1:vpc-12345678" in node_ids
        assert f"{account_id}:us-east-1:subnet-12345678" in node_ids
        assert f"{account_id}:us-east-1:i-12345678" in node_ids

    def test_load_edges(self, store: GraphStore, sample_graph: GraphEngine) -> None:
        """Edges are saved and can be loaded."""
        account_id = "123456789012"

        store.save_graph(sample_graph, account_id)
        edges = store.load_edges(account_id=account_id)

        assert len(edges) == 2

        # Check edge structure
        edge_pairs = {(e[0], e[1]) for e in edges}
        assert (
            f"{account_id}:us-east-1:subnet-12345678",
            f"{account_id}:us-east-1:vpc-12345678",
        ) in edge_pairs
        assert (
            f"{account_id}:us-east-1:i-12345678",
            f"{account_id}:us-east-1:subnet-12345678",
        ) in edge_pairs

    def test_get_node_config(
        self, store: GraphStore, sample_graph: GraphEngine
    ) -> None:
        """Full node config can be retrieved on-demand."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        node_id = f"{account_id}:us-east-1:vpc-12345678"
        config = store.get_node_config(node_id)

        assert config is not None
        assert config["VpcId"] == "vpc-12345678"
        assert config["CidrBlock"] == "10.0.0.0/16"

    def test_get_node_config_not_found(self, store: GraphStore) -> None:
        """Missing node returns None."""
        config = store.get_node_config("nonexistent:us-east-1:vpc-99999")
        assert config is None

    def test_get_node_tags(self, store: GraphStore, sample_graph: GraphEngine) -> None:
        """Tags can be retrieved separately."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        node_id = f"{account_id}:us-east-1:vpc-12345678"
        tags = store.get_node_tags(node_id)

        assert tags is not None
        assert tags["Name"] == "TestVPC"
        assert tags["Environment"] == "test"

    def test_get_nodes_by_type(
        self, store: GraphStore, sample_graph: GraphEngine
    ) -> None:
        """Nodes can be queried by resource type."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        subnets = store.get_nodes_by_type("aws_subnet", account_id=account_id)
        assert len(subnets) == 1
        assert f"{account_id}:us-east-1:subnet-12345678" in subnets

    def test_get_nodes_by_region(
        self, store: GraphStore, sample_graph: GraphEngine
    ) -> None:
        """Nodes can be queried by region."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        nodes = store.get_nodes_by_region("us-east-1", account_id=account_id)
        assert len(nodes) == 3

        nodes = store.get_nodes_by_region("eu-west-1", account_id=account_id)
        assert len(nodes) == 0

    def test_multi_account_isolation(self, store: GraphStore) -> None:
        """Different accounts are isolated."""
        # Create graphs for two accounts
        graph1 = GraphEngine()
        graph1.add_resource(
            ResourceNode(
                id="vpc-account1",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"account": "1"},
            )
        )

        graph2 = GraphEngine()
        graph2.add_resource(
            ResourceNode(
                id="vpc-account2",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"account": "2"},
            )
        )

        store.save_graph(graph1, "111111111111")
        store.save_graph(graph2, "222222222222")

        # Each account should only see its own nodes
        nodes1 = store.load_topology(account_id="111111111111")
        nodes2 = store.load_topology(account_id="222222222222")

        assert len(nodes1) == 1
        assert len(nodes2) == 1
        assert "111111111111" in nodes1[0].node_id
        assert "222222222222" in nodes2[0].node_id

    def test_delete_node(self, store: GraphStore, sample_graph: GraphEngine) -> None:
        """Node can be deleted."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        node_id = f"{account_id}:us-east-1:i-12345678"

        # Delete
        result = store.delete_node(node_id)
        assert result is True

        # Verify gone
        assert store.node_exists(node_id) is False
        assert store.get_node_config(node_id) is None

    def test_delete_nonexistent_node(self, store: GraphStore) -> None:
        """Deleting nonexistent node returns False."""
        result = store.delete_node("nonexistent:us-east-1:vpc-99999")
        assert result is False

    def test_delete_account(self, store: GraphStore, sample_graph: GraphEngine) -> None:
        """All nodes for an account can be deleted."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        count = store.delete_account(account_id)
        assert count == 3

        nodes = store.load_topology(account_id=account_id)
        assert len(nodes) == 0

    def test_get_statistics(self, store: GraphStore, sample_graph: GraphEngine) -> None:
        """Statistics are accurately reported."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        stats = store.get_statistics()

        assert stats.total_nodes == 3
        assert stats.total_edges == 2
        assert stats.by_account[account_id] == 3
        assert stats.by_region["us-east-1"] == 3
        # Compression ratio varies with data size; small data may not compress well
        assert stats.compression_ratio > 0
        assert stats.db_size_bytes > 0

    def test_config_hash_for_change_detection(
        self, store: GraphStore, sample_graph: GraphEngine
    ) -> None:
        """Config hash can be retrieved for change detection."""
        account_id = "123456789012"
        store.save_graph(sample_graph, account_id)

        node_id = f"{account_id}:us-east-1:vpc-12345678"
        hash1 = store.get_config_hash(node_id)

        assert hash1 is not None
        assert len(hash1) == 64  # SHA256 hex

    def test_node_id_format(self, store: GraphStore) -> None:
        """Node IDs follow the expected format."""
        node_id = store.build_node_id("123456789012", "us-east-1", "vpc-12345")
        assert node_id == "123456789012:us-east-1:vpc-12345"

        account, region, resource = store.parse_node_id(node_id)
        assert account == "123456789012"
        assert region == "us-east-1"
        assert resource == "vpc-12345"

    def test_parse_invalid_node_id(self, store: GraphStore) -> None:
        """Invalid node IDs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid node_id format"):
            store.parse_node_id("invalid-format")

    def test_global_resources_use_global_region(self, store: GraphStore) -> None:
        """Global resources (no region) use 'global' placeholder."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="user-admin",
                resource_type=ResourceType.VPC,  # Placeholder for IAM
                region="",  # Empty region for global resource
                config={"UserName": "admin"},
            )
        )

        store.save_graph(graph, "123456789012")

        nodes = store.load_topology(account_id="123456789012")
        assert len(nodes) == 1
        # Empty region becomes 'global' in node_id
        assert nodes[0].node_id == "123456789012:global:user-admin"


class TestAtomicTransactions:
    """Tests for transaction safety."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> GraphStore:
        return GraphStore(db_path=tmp_path / "test_graph.db")

    def test_transaction_rollback_on_error(self, store: GraphStore) -> None:
        """Failed transaction doesn't leave partial data."""
        initial_stats = store.get_statistics()
        assert initial_stats.total_nodes == 0

        try:
            with store.atomic_transaction() as cursor:
                # Insert a node
                cursor.execute(
                    """INSERT INTO nodes
                       (node_id, account_id, region, resource_type)
                       VALUES (?, ?, ?, ?)""",
                    ("test:us-east-1:vpc-1", "test", "us-east-1", "aws_vpc"),
                )
                # Force an error
                raise ValueError("Simulated failure")
        except ValueError:
            pass

        # Verify rollback
        final_stats = store.get_statistics()
        assert final_stats.total_nodes == 0


class TestPerformance:
    """Performance tests for the storage layer."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> GraphStore:
        return GraphStore(db_path=tmp_path / "perf_test.db")

    def test_save_10k_nodes_under_5_seconds(self, store: GraphStore) -> None:
        """10,000 nodes should save in under 5 seconds."""
        graph = GraphEngine()

        # Create 10,000 nodes with realistic configs
        for i in range(10_000):
            node = ResourceNode(
                id=f"vpc-{i:08d}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={
                    "VpcId": f"vpc-{i:08d}",
                    "CidrBlock": f"10.{i % 256}.0.0/16",
                    "Tags": [
                        {"Key": "Name", "Value": f"VPC-{i}"},
                        {"Key": "Index", "Value": str(i)},
                    ],
                },
                tags={"Name": f"VPC-{i}"},
            )
            graph.add_resource(node)

        start = time.time()
        count = store.save_graph(graph, "123456789012")
        elapsed = time.time() - start

        assert count == 10_000
        assert elapsed < 5.0, f"Save took {elapsed:.2f}s, expected < 5s"

    def test_load_topology_10k_under_500ms(self, store: GraphStore) -> None:
        """Loading topology of 10,000 nodes should take < 500ms."""
        # First, save the nodes
        graph = GraphEngine()
        for i in range(10_000):
            node = ResourceNode(
                id=f"vpc-{i:08d}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"VpcId": f"vpc-{i:08d}"},
            )
            graph.add_resource(node)
        store.save_graph(graph, "123456789012")

        # Measure load time
        start = time.time()
        nodes = store.load_topology(account_id="123456789012")
        elapsed = time.time() - start

        assert len(nodes) == 10_000
        assert elapsed < 0.5, f"Load took {elapsed:.3f}s, expected < 0.5s"

    def test_single_config_lookup_under_10ms(self, store: GraphStore) -> None:
        """Single config lookup should take < 10ms."""
        # Save some nodes
        graph = GraphEngine()
        for i in range(1_000):
            node = ResourceNode(
                id=f"vpc-{i:08d}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"VpcId": f"vpc-{i:08d}", "Data": "x" * 1000},
            )
            graph.add_resource(node)
        store.save_graph(graph, "123456789012")

        # Measure single lookup
        node_id = "123456789012:us-east-1:vpc-00000500"

        start = time.time()
        config = store.get_node_config(node_id)
        elapsed = time.time() - start

        assert config is not None
        assert elapsed < 0.01, f"Lookup took {elapsed:.4f}s, expected < 0.01s"

    def test_compression_achieves_meaningful_ratio(self, store: GraphStore) -> None:
        """Compression should achieve meaningful ratio for verbose AWS configs."""
        graph = GraphEngine()

        # Create nodes with realistic, verbose configs
        for i in range(100):
            node = ResourceNode(
                id=f"instance-{i:08d}",
                resource_type=ResourceType.EC2_INSTANCE,
                region="us-east-1",
                config={
                    "InstanceId": f"i-{i:017d}",
                    "InstanceType": "t3.medium",
                    "ImageId": "ami-12345678901234567",
                    "SubnetId": "subnet-12345678901234567",
                    "VpcId": "vpc-12345678901234567",
                    "SecurityGroups": [
                        {"GroupId": "sg-12345678901234567", "GroupName": "default"},
                        {"GroupId": "sg-98765432109876543", "GroupName": "web"},
                    ],
                    "Tags": [
                        {"Key": "Name", "Value": f"Server-{i}"},
                        {"Key": "Environment", "Value": "production"},
                        {"Key": "Team", "Value": "platform"},
                        {"Key": "CostCenter", "Value": "12345"},
                    ],
                    "State": {"Code": 16, "Name": "running"},
                    "LaunchTime": "2024-01-01T00:00:00.000Z",
                    "PrivateIpAddress": f"10.0.{i % 256}.{i // 256}",
                    "PublicIpAddress": f"54.{i % 256}.{i // 256}.1",
                    "BlockDeviceMappings": [
                        {
                            "DeviceName": "/dev/xvda",
                            "Ebs": {
                                "VolumeId": f"vol-{i:017d}",
                                "Status": "attached",
                                "AttachTime": "2024-01-01T00:00:00Z",
                                "DeleteOnTermination": True,
                            },
                        }
                    ],
                },
            )
            graph.add_resource(node)

        store.save_graph(graph, "123456789012")
        stats = store.get_statistics()

        # Zstd typically achieves 1.5-3x for JSON data
        # The ratio improves with more similar/repetitive data
        assert stats.compression_ratio > 1.5, (
            f"Compression ratio {stats.compression_ratio:.2f}x is below target 1.5x"
        )


class TestThreadSafety:
    """Tests for thread safety."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> GraphStore:
        return GraphStore(db_path=tmp_path / "thread_test.db")

    def test_concurrent_reads(self, store: GraphStore) -> None:
        """Multiple threads can read concurrently."""
        # Save some data
        graph = GraphEngine()
        for i in range(100):
            graph.add_resource(
                ResourceNode(
                    id=f"vpc-{i}",
                    resource_type=ResourceType.VPC,
                    region="us-east-1",
                    config={"index": i},
                )
            )
        store.save_graph(graph, "123456789012")

        errors: list[Exception] = []

        def read_nodes() -> None:
            try:
                for _ in range(10):
                    nodes = store.load_topology()
                    assert len(nodes) == 100
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_nodes) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Errors occurred: {errors}"


class TestMigration:
    """Tests for migration from JSON."""

    def test_migrate_from_json(self, tmp_path: Path) -> None:
        """Graph can be migrated from JSON format."""
        # Create a JSON graph file
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="vpc-migration-test",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"VpcId": "vpc-migration-test"},
            )
        )

        json_path = tmp_path / "graph.json"
        graph.save(json_path)

        # Migrate
        store = GraphStore(db_path=tmp_path / "migrated.db")
        count = migrate_from_json(json_path, store, "123456789012")

        assert count == 1

        # Verify data
        nodes = store.load_topology()
        assert len(nodes) == 1
        assert "vpc-migration-test" in nodes[0].node_id


class TestPhantomNodes:
    """Tests for phantom node handling."""

    @pytest.fixture
    def store(self, tmp_path: Path) -> GraphStore:
        return GraphStore(db_path=tmp_path / "phantom_test.db")

    def test_phantom_nodes_stored_correctly(self, store: GraphStore) -> None:
        """Phantom nodes are saved and retrieved with correct flags."""
        graph = GraphEngine()

        # Add a real node
        real = ResourceNode(
            id="vpc-real",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
        )
        graph.add_resource(real)

        # Add dependency to non-existent resource (creates phantom)
        graph.add_dependency("vpc-real", "vpc-missing")

        store.save_graph(graph, "123456789012")

        # Check phantom nodes
        phantoms = store.get_phantom_nodes()
        assert len(phantoms) == 1
        assert "vpc-missing" in phantoms[0]

        # Verify topology shows phantom flag
        nodes = store.load_topology()
        phantom_node = next(n for n in nodes if "vpc-missing" in n.node_id)
        assert phantom_node.is_phantom is True
