"""Tests for GraphEngine."""

import tempfile
from pathlib import Path

import pytest

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import DependencyType, ResourceNode, ResourceType


class TestGraphEngine:
    """Tests for GraphEngine class."""

    def test_create_empty_graph(self) -> None:
        """Test creating an empty graph."""
        graph = GraphEngine()

        assert graph.node_count == 0
        assert graph.edge_count == 0
        assert len(graph) == 0

    def test_add_resource(self) -> None:
        """Test adding a resource to the graph."""
        graph = GraphEngine()
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )

        graph.add_resource(node)

        assert graph.node_count == 1
        assert graph.get_resource("vpc-12345") == node

    def test_add_dependency(self) -> None:
        """Test adding dependency between resources."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_dependency("subnet-12345", "vpc-12345", DependencyType.BELONGS_TO)

        assert graph.edge_count == 1
        deps = graph.get_dependencies("subnet-12345")
        assert len(deps) == 1
        assert deps[0].id == "vpc-12345"

    def test_add_dependency_missing_source(self) -> None:
        """Test adding dependency with missing source."""
        graph = GraphEngine()
        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        graph.add_resource(vpc)

        with pytest.raises(ValueError, match="Source resource not found"):
            graph.add_dependency("subnet-missing", "vpc-12345")

    def test_add_dependency_missing_target(self) -> None:
        """Test adding dependency with missing target."""
        graph = GraphEngine()
        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )
        graph.add_resource(subnet)

        with pytest.raises(ValueError, match="Target resource not found"):
            graph.add_dependency("subnet-12345", "vpc-missing")

    def test_get_dependents(self) -> None:
        """Test getting resources that depend on a resource."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-12345",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_dependency("subnet-12345", "vpc-12345")

        dependents = graph.get_dependents("vpc-12345")
        assert len(dependents) == 1
        assert dependents[0].id == "subnet-12345"

    def test_get_resources_by_type(self) -> None:
        """Test filtering resources by type."""
        graph = GraphEngine()

        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        vpcs = graph.get_resources_by_type(ResourceType.VPC)
        assert len(vpcs) == 2

        subnets = graph.get_resources_by_type(ResourceType.SUBNET)
        assert len(subnets) == 1

    def test_topological_sort(self) -> None:
        """Test topological sorting of resources."""
        graph = GraphEngine()

        # Create a chain: VPC <- Subnet <- EC2
        vpc = ResourceNode(
            id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
        )
        subnet = ResourceNode(
            id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
        )
        ec2 = ResourceNode(
            id="i-12345", resource_type=ResourceType.EC2_INSTANCE, region="us-east-1"
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_resource(ec2)
        graph.add_dependency("subnet-1", "vpc-1")
        graph.add_dependency("i-12345", "subnet-1")

        sorted_resources = graph.topological_sort()
        sorted_ids = [r.id for r in sorted_resources]

        # VPC should come before Subnet, Subnet before EC2
        assert sorted_ids.index("vpc-1") < sorted_ids.index("subnet-1")
        assert sorted_ids.index("subnet-1") < sorted_ids.index("i-12345")

    def test_remove_resource(self) -> None:
        """Test removing a resource."""
        graph = GraphEngine()
        node = ResourceNode(
            id="vpc-12345",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        graph.add_resource(node)

        result = graph.remove_resource("vpc-12345")
        assert result is True
        assert graph.node_count == 0
        assert graph.get_resource("vpc-12345") is None

        # Removing non-existent should return False
        result = graph.remove_resource("vpc-12345")
        assert result is False

    def test_statistics(self) -> None:
        """Test graph statistics."""
        graph = GraphEngine()

        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )
        graph.add_dependency("subnet-1", "vpc-1")

        stats = graph.statistics()

        assert stats["total_resources"] == 2
        assert stats["total_dependencies"] == 1
        assert stats["has_cycles"] is False
        assert stats["resources_by_type"]["aws_vpc"] == 1
        assert stats["resources_by_type"]["aws_subnet"] == 1

    def test_save_and_load(self) -> None:
        """Test saving and loading graph from file."""
        graph = GraphEngine()

        graph.add_resource(
            ResourceNode(
                id="vpc-1",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={"cidr_block": "10.0.0.0/16"},
                tags={"Name": "test-vpc"},
            )
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1",
                resource_type=ResourceType.SUBNET,
                region="us-east-1",
                config={"vpc_id": "vpc-1"},
            )
        )
        graph.add_dependency("subnet-1", "vpc-1")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            graph.save(path)
            loaded = GraphEngine.load(path)

            assert loaded.node_count == 2
            assert loaded.edge_count == 1

            vpc = loaded.get_resource("vpc-1")
            assert vpc is not None
            assert vpc.config["cidr_block"] == "10.0.0.0/16"
            assert vpc.tags["Name"] == "test-vpc"

        finally:
            path.unlink()

    def test_to_dict(self) -> None:
        """Test converting graph to dictionary."""
        graph = GraphEngine()

        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )
        graph.add_dependency("subnet-1", "vpc-1")

        data = graph.to_dict()

        assert "version" in data
        assert "nodes" in data
        assert "edges" in data
        assert "statistics" in data
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_get_subgraph(self) -> None:
        """Test creating a subgraph with specific resources."""
        graph = GraphEngine()

        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )
        graph.add_dependency("subnet-1", "vpc-1")

        subgraph = graph.get_subgraph(["vpc-1", "subnet-1"])

        assert subgraph.node_count == 2
        assert subgraph.edge_count == 1
        assert subgraph.get_resource("vpc-2") is None
