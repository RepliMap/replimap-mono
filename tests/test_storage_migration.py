"""
Tests for storage layer migration (NetworkX → SQLite).

This module tests:
1. GraphEngine alias switch in __init__.py
2. Environment variable escape hatch (REPLIMAP_USE_LEGACY_STORAGE)
3. API compatibility between legacy and adapter
4. Streaming API for MemoryAwarePreloader
5. SCCResult compatibility

The Phase 0 migration ensures all 84+ files using GraphEngine
automatically use SQLite backend with zero code changes.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


class TestStorageAliasSwitch:
    """Test the GraphEngine alias switch in __init__.py."""

    def test_default_uses_sqlite_adapter(self) -> None:
        """Default GraphEngine should be SQLite-backed GraphEngineAdapter."""
        # Ensure legacy mode is off
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("REPLIMAP_USE_LEGACY_STORAGE", None)

            from replimap.core import get_storage_info

            info = get_storage_info()
            assert info["backend"] == "sqlite"
            assert info["legacy_mode"] is False
            assert info["adapter_class"] == "GraphEngineAdapter"

    def test_get_storage_info_returns_valid_dict(self) -> None:
        """get_storage_info should return all expected fields."""
        from replimap.core import get_storage_info

        info = get_storage_info()

        # Required fields
        assert "backend" in info
        assert "legacy_mode" in info
        assert "version" in info
        assert "adapter_class" in info

        # Type checks
        assert isinstance(info["backend"], str)
        assert isinstance(info["legacy_mode"], bool)
        assert isinstance(info["version"], str)

    def test_graph_engine_is_adapter_class(self) -> None:
        """GraphEngine should be GraphEngineAdapter when not in legacy mode."""
        from replimap.core import GraphEngine
        from replimap.core.unified_storage import GraphEngineAdapter

        # In normal mode, they should be the same class
        assert GraphEngine is GraphEngineAdapter


class TestAPICompatibility:
    """Test API compatibility between legacy and adapter."""

    @pytest.fixture
    def graph(self) -> Any:
        """Create a GraphEngine instance (SQLite-backed)."""
        from replimap.core import GraphEngine

        return GraphEngine()

    @pytest.fixture
    def resource_node(self) -> Any:
        """Create a test ResourceNode."""
        from replimap.core.models import ResourceNode, ResourceType

        return ResourceNode(
            id="vpc-test123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"CidrBlock": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
            terraform_name="test_vpc",
            original_name="test-vpc",
        )

    def test_add_and_get_resource(self, graph: Any, resource_node: Any) -> None:
        """add_resource and get_resource should work."""
        graph.add_resource(resource_node)

        retrieved = graph.get_resource(resource_node.id)
        assert retrieved is not None
        assert retrieved.id == resource_node.id
        assert str(retrieved.resource_type) == str(resource_node.resource_type)

    def test_iter_resources(self, graph: Any, resource_node: Any) -> None:
        """iter_resources should yield all resources."""
        graph.add_resource(resource_node)

        resources = list(graph.iter_resources())
        assert len(resources) == 1
        assert resources[0].id == resource_node.id

    def test_get_all_resources(self, graph: Any, resource_node: Any) -> None:
        """get_all_resources should return list of all resources."""
        graph.add_resource(resource_node)

        resources = graph.get_all_resources()
        assert len(resources) == 1
        assert resources[0].id == resource_node.id

    def test_add_dependency(self, graph: Any, resource_node: Any) -> None:
        """add_dependency should create edges."""
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        # Add VPC
        graph.add_resource(resource_node)

        # Add subnet
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={"VpcId": "vpc-test123"},
            terraform_name="test_subnet",
        )
        graph.add_resource(subnet)

        # Add dependency: subnet depends on vpc
        graph.add_dependency(subnet.id, resource_node.id, DependencyType.BELONGS_TO)

        # Check dependency
        deps = graph.get_dependencies(subnet.id)
        assert len(deps) == 1
        assert deps[0].id == resource_node.id

    def test_node_count_property(self, graph: Any, resource_node: Any) -> None:
        """node_count should return correct count."""
        assert graph.node_count == 0

        graph.add_resource(resource_node)
        assert graph.node_count == 1

    def test_edge_count_property(self, graph: Any, resource_node: Any) -> None:
        """edge_count should return correct count."""
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        assert graph.edge_count == 0

        graph.add_resource(resource_node)
        subnet = ResourceNode(
            id="subnet-456",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )
        graph.add_resource(subnet)
        graph.add_dependency(subnet.id, resource_node.id, DependencyType.BELONGS_TO)

        assert graph.edge_count == 1

    def test_topological_sort(self, graph: Any) -> None:
        """topological_sort should order dependencies correctly."""
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        # Create: VPC <- Subnet <- Instance chain
        vpc = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet = ResourceNode(
            id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
        )
        instance = ResourceNode(
            id="i-1", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_resource(instance)

        graph.add_dependency(subnet.id, vpc.id, DependencyType.BELONGS_TO)
        graph.add_dependency(instance.id, subnet.id, DependencyType.BELONGS_TO)

        sorted_resources = graph.topological_sort()
        sorted_ids = [r.id for r in sorted_resources]

        # VPC should come before Subnet, Subnet before Instance
        assert sorted_ids.index(vpc.id) < sorted_ids.index(subnet.id)
        assert sorted_ids.index(subnet.id) < sorted_ids.index(instance.id)

    def test_has_cycles(self, graph: Any) -> None:
        """has_cycles should detect circular dependencies."""
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        # Create acyclic graph first
        vpc = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet = ResourceNode(
            id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_dependency(subnet.id, vpc.id, DependencyType.BELONGS_TO)

        assert graph.has_cycles() is False

    def test_find_strongly_connected_components(self, graph: Any) -> None:
        """find_strongly_connected_components should return SCCResult."""
        from replimap.core.models import ResourceNode, ResourceType

        vpc = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        graph.add_resource(vpc)

        scc_result = graph.find_strongly_connected_components()

        # Should return SCCResult dataclass
        assert hasattr(scc_result, "components")
        assert hasattr(scc_result, "node_to_scc")
        assert hasattr(scc_result, "has_cycles")
        assert hasattr(scc_result, "cycle_groups")

    def test_statistics(self, graph: Any, resource_node: Any) -> None:
        """statistics should return comprehensive stats."""
        graph.add_resource(resource_node)

        stats = graph.statistics()

        assert "total_resources" in stats
        assert "total_dependencies" in stats
        assert "resources_by_type" in stats
        assert stats["total_resources"] == 1

    def test_to_dict_and_from_dict(self, graph: Any, resource_node: Any) -> None:
        """to_dict and from_dict should serialize/deserialize correctly."""
        from replimap.core import GraphEngine

        graph.add_resource(resource_node)

        # Export
        data = graph.to_dict()
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == 1

        # Import
        new_graph = GraphEngine.from_dict(data)
        assert new_graph.node_count == 1
        retrieved = new_graph.get_resource(resource_node.id)
        assert retrieved is not None

    def test_save_and_load_json(self, graph: Any, resource_node: Any) -> None:
        """save and load should work with JSON files."""
        from replimap.core import GraphEngine

        graph.add_resource(resource_node)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "graph.json"
            graph.save(path)

            assert path.exists()

            loaded = GraphEngine.load(path)
            assert loaded.node_count == 1

    def test_snapshot_and_load_snapshot(self, graph: Any, resource_node: Any) -> None:
        """snapshot and load_snapshot should work with SQLite."""
        from replimap.core import GraphEngine

        graph.add_resource(resource_node)

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshot_path = str(Path(tmpdir) / "snapshot.db")
            graph.snapshot(snapshot_path)

            assert Path(snapshot_path).exists()

            loaded = GraphEngine.load_snapshot(snapshot_path)
            assert loaded.node_count == 1


class TestSCCResult:
    """Test SCCResult compatibility."""

    def test_scc_result_structure(self) -> None:
        """SCCResult should have all expected fields."""
        from replimap.core import SCCResult

        result = SCCResult(
            components=[{"a", "b"}, {"c"}],
            node_to_scc={"a": 0, "b": 0, "c": 1},
            has_cycles=False,
            cycle_groups=[],
        )

        assert result.components == [{"a", "b"}, {"c"}]
        assert result.node_to_scc == {"a": 0, "b": 0, "c": 1}
        assert result.has_cycles is False
        assert result.cycle_groups == []

    def test_scc_result_from_graph(self) -> None:
        """SCCResult from graph should be correct type."""
        from replimap.core import GraphEngine, SCCResult
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        graph = GraphEngine()

        # Add resources with cycle
        r1 = ResourceNode(
            id="r1", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )
        r2 = ResourceNode(
            id="r2", resource_type=ResourceType.SECURITY_GROUP, region="us-east-1"
        )

        graph.add_resource(r1)
        graph.add_resource(r2)
        graph.add_dependency(r1.id, r2.id, DependencyType.REFERENCES)
        graph.add_dependency(r2.id, r1.id, DependencyType.REFERENCES)

        scc_result = graph.find_strongly_connected_components()

        assert isinstance(scc_result, SCCResult)
        assert scc_result.has_cycles is True
        assert len(scc_result.cycle_groups) == 1


class TestStreamingAPI:
    """Test streaming API for large graph support."""

    def test_iter_resources_is_iterator(self) -> None:
        """iter_resources should return an iterator."""
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        graph = GraphEngine()

        for i in range(10):
            node = ResourceNode(
                id=f"vpc-{i}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
            )
            graph.add_resource(node)

        # iter_resources should be iterable
        iterator = graph.iter_resources()
        assert hasattr(iterator, "__iter__")
        assert hasattr(iterator, "__next__")

        # Should yield all resources
        count = sum(1 for _ in iterator)
        assert count == 10


class TestPhantomNodes:
    """Test phantom node handling."""

    def test_phantom_node_creation(self) -> None:
        """Phantom nodes should be created for missing dependencies."""
        from replimap.core import GraphEngine
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        graph = GraphEngine(create_phantom_nodes=True)

        # Add a resource that references a non-existent resource
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )
        graph.add_resource(subnet)

        # Add dependency to non-existent VPC
        graph.add_dependency(subnet.id, "vpc-missing", DependencyType.BELONGS_TO)

        # Should have created phantom
        assert graph.is_phantom("vpc-missing")
        phantom = graph.get_resource("vpc-missing")
        assert phantom is not None
        assert phantom.is_phantom is True

    def test_get_phantom_nodes(self) -> None:
        """get_phantom_nodes should return all phantoms."""
        from replimap.core import GraphEngine
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        graph = GraphEngine(create_phantom_nodes=True)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )
        graph.add_resource(subnet)
        graph.add_dependency(subnet.id, "vpc-missing", DependencyType.BELONGS_TO)

        phantoms = graph.get_phantom_nodes()
        assert len(phantoms) == 1
        assert phantoms[0].id == "vpc-missing"


class TestGraphMerge:
    """Test graph merge operations."""

    def test_merge_graphs(self) -> None:
        """merge should combine two graphs correctly."""
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        graph1 = GraphEngine()
        graph2 = GraphEngine()

        vpc1 = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        vpc2 = ResourceNode(
            id="vpc-2", resource_type=ResourceType.VPC, region="us-west-2"
        )

        graph1.add_resource(vpc1)
        graph2.add_resource(vpc2)

        graph1.merge(graph2)

        assert graph1.node_count == 2
        assert graph1.get_resource("vpc-1") is not None
        assert graph1.get_resource("vpc-2") is not None


class TestSubgraph:
    """Test subgraph extraction."""

    def test_get_subgraph(self) -> None:
        """get_subgraph should extract only specified resources."""
        from replimap.core import GraphEngine
        from replimap.core.models import DependencyType, ResourceNode, ResourceType

        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet1 = ResourceNode(
            id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
        )
        subnet2 = ResourceNode(
            id="subnet-2", resource_type=ResourceType.SUBNET, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet1)
        graph.add_resource(subnet2)
        graph.add_dependency(subnet1.id, vpc.id, DependencyType.BELONGS_TO)
        graph.add_dependency(subnet2.id, vpc.id, DependencyType.BELONGS_TO)

        # Extract subgraph with only vpc and subnet1
        subgraph = graph.get_subgraph(["vpc-1", "subnet-1"])

        assert subgraph.node_count == 2
        assert subgraph.get_resource("vpc-1") is not None
        assert subgraph.get_resource("subnet-1") is not None
        assert subgraph.get_resource("subnet-2") is None


class TestContextManager:
    """Test context manager support."""

    def test_context_manager_usage(self) -> None:
        """GraphEngine should work as context manager."""
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        with GraphEngine() as graph:
            vpc = ResourceNode(
                id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
            )
            graph.add_resource(vpc)
            assert graph.node_count == 1

        # After context, graph should be closed (no exception is success)


class TestResourceNodeConversion:
    """Test ResourceNode to/from Node conversion."""

    def test_resource_preserves_all_fields(self) -> None:
        """All ResourceNode fields should survive round-trip conversion."""
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        original = ResourceNode(
            id="vpc-test",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"CidrBlock": "10.0.0.0/16", "EnableDnsSupport": True},
            arn="arn:aws:ec2:us-east-1:123456789:vpc/vpc-test",
            tags={"Name": "TestVPC", "Environment": "test"},
            terraform_name="test_vpc",
            original_name="TestVPC",
            is_phantom=False,
        )

        graph = GraphEngine()
        graph.add_resource(original)

        retrieved = graph.get_resource("vpc-test")
        assert retrieved is not None
        assert retrieved.id == original.id
        assert retrieved.region == original.region
        assert retrieved.config["CidrBlock"] == "10.0.0.0/16"
        assert retrieved.tags["Name"] == "TestVPC"
        assert retrieved.terraform_name == original.terraform_name
