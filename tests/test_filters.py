"""Tests for scan filters."""

from __future__ import annotations

from replimap.core.filters import (
    ScanFilter,
    apply_filter_to_graph,
)
from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType


class TestScanFilter:
    """Tests for ScanFilter class."""

    def test_empty_filter(self) -> None:
        """Test empty filter."""
        filter_obj = ScanFilter()
        assert filter_obj.is_empty()

    def test_filter_with_vpc_ids(self) -> None:
        """Test filter with VPC IDs."""
        filter_obj = ScanFilter(vpc_ids=["vpc-123"])
        assert not filter_obj.is_empty()

    def test_filter_with_resource_types(self) -> None:
        """Test filter with resource types."""
        filter_obj = ScanFilter(resource_types=["vpc", "subnet"])
        assert not filter_obj.is_empty()

    def test_filter_with_tags(self) -> None:
        """Test filter with tags."""
        filter_obj = ScanFilter(include_tags={"Environment": "Production"})
        assert not filter_obj.is_empty()

    def test_should_include_resource_empty_filter(self) -> None:
        """Test that empty filter includes all resources."""
        filter_obj = ScanFilter()
        resource = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        assert filter_obj.should_include_resource(resource)

    def test_should_include_resource_by_type(self) -> None:
        """Test filtering by resource type."""
        filter_obj = ScanFilter(resource_types=["vpc"])

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        assert filter_obj.should_include_resource(vpc)
        assert not filter_obj.should_include_resource(subnet)

    def test_should_include_resource_by_full_type(self) -> None:
        """Test filtering by full resource type name."""
        filter_obj = ScanFilter(resource_types=["aws_vpc"])

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )

        assert filter_obj.should_include_resource(vpc)

    def test_should_include_resource_by_tag(self) -> None:
        """Test filtering by tag."""
        filter_obj = ScanFilter(include_tags={"Environment": "Production"})

        prod = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Environment": "Production"},
        )
        dev = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Environment": "Development"},
        )

        assert filter_obj.should_include_resource(prod)
        assert not filter_obj.should_include_resource(dev)

    def test_should_include_resource_by_tag_wildcard(self) -> None:
        """Test filtering by tag with wildcard value."""
        filter_obj = ScanFilter(include_tags={"Environment": "*"})

        with_tag = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Environment": "Production"},
        )
        without_tag = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={},
        )

        assert filter_obj.should_include_resource(with_tag)
        assert not filter_obj.should_include_resource(without_tag)

    def test_exclude_by_type(self) -> None:
        """Test excluding by resource type."""
        filter_obj = ScanFilter(exclude_types=["subnet"])

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        assert filter_obj.should_include_resource(vpc)
        assert not filter_obj.should_include_resource(subnet)

    def test_exclude_by_tag(self) -> None:
        """Test excluding by tag."""
        filter_obj = ScanFilter(exclude_tags={"Environment": "Development"})

        prod = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Environment": "Production"},
        )
        dev = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Environment": "Development"},
        )

        assert filter_obj.should_include_resource(prod)
        assert not filter_obj.should_include_resource(dev)

    def test_exclude_by_name_pattern(self) -> None:
        """Test excluding by name pattern."""
        filter_obj = ScanFilter(exclude_patterns=["*-temp-*"])

        permanent = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "prod-main-vpc"},
        )
        temp = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "prod-temp-vpc"},
        )

        assert filter_obj.should_include_resource(permanent)
        assert not filter_obj.should_include_resource(temp)

    def test_name_pattern_filter(self) -> None:
        """Test filtering by name pattern."""
        filter_obj = ScanFilter(name_patterns=["prod-*"])

        prod = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "prod-main-vpc"},
        )
        dev = ResourceNode(
            id="vpc-456",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "dev-main-vpc"},
        )

        assert filter_obj.should_include_resource(prod)
        assert not filter_obj.should_include_resource(dev)

    def test_from_cli_args(self) -> None:
        """Test creating filter from CLI args."""
        filter_obj = ScanFilter.from_cli_args(
            vpc="vpc-123,vpc-456",
            types="vpc,subnet",
            tags=["Environment=Production", "Team=Platform"],
            exclude_types="sns,sqs",
        )

        assert filter_obj.vpc_ids == ["vpc-123", "vpc-456"]
        assert filter_obj.resource_types == ["vpc", "subnet"]
        assert filter_obj.include_tags == {
            "Environment": "Production",
            "Team": "Platform",
        }
        assert filter_obj.exclude_types == ["sns", "sqs"]

    def test_from_cli_args_empty(self) -> None:
        """Test creating filter from empty CLI args."""
        filter_obj = ScanFilter.from_cli_args()
        assert filter_obj.is_empty()

    def test_describe_empty(self) -> None:
        """Test describe with empty filter."""
        filter_obj = ScanFilter()
        assert filter_obj.describe() == "No filters"

    def test_describe_with_filters(self) -> None:
        """Test describe with active filters."""
        filter_obj = ScanFilter(
            vpc_ids=["vpc-123"],
            resource_types=["vpc"],
        )
        description = filter_obj.describe()

        assert "VPC: vpc-123" in description
        assert "Types: vpc" in description

    def test_get_vpc_filter_for_api(self) -> None:
        """Test generating AWS API VPC filter."""
        filter_obj = ScanFilter(vpc_ids=["vpc-123", "vpc-456"])
        api_filter = filter_obj.get_vpc_filter_for_api()

        assert api_filter == [{"Name": "vpc-id", "Values": ["vpc-123", "vpc-456"]}]

    def test_get_vpc_filter_for_api_empty(self) -> None:
        """Test generating AWS API VPC filter when empty."""
        filter_obj = ScanFilter()
        assert filter_obj.get_vpc_filter_for_api() is None

    def test_get_tag_filters_for_api(self) -> None:
        """Test generating AWS API tag filters."""
        filter_obj = ScanFilter(include_tags={"Environment": "Production", "Team": "*"})
        api_filters = filter_obj.get_tag_filters_for_api()

        assert api_filters is not None
        assert len(api_filters) == 2
        # Check for specific tag filter
        assert {"Name": "tag:Environment", "Values": ["Production"]} in api_filters
        # Check for wildcard tag filter
        assert {"Name": "tag-key", "Values": ["Team"]} in api_filters

    def test_get_tag_filters_for_api_empty(self) -> None:
        """Test generating AWS API tag filters when empty."""
        filter_obj = ScanFilter()
        assert filter_obj.get_tag_filters_for_api() is None


class TestApplyFilterToGraph:
    """Tests for apply_filter_to_graph function."""

    def test_apply_empty_filter(self) -> None:
        """Test applying empty filter doesn't remove anything."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="vpc-123",
                resource_type=ResourceType.VPC,
                region="us-east-1",
            )
        )

        filter_obj = ScanFilter()
        removed = apply_filter_to_graph(graph, filter_obj)

        assert removed == 0
        assert graph.get_resource("vpc-123") is not None

    def test_apply_type_filter(self) -> None:
        """Test applying type filter."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="vpc-123",
                resource_type=ResourceType.VPC,
                region="us-east-1",
            )
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-123",
                resource_type=ResourceType.SUBNET,
                region="us-east-1",
            )
        )

        filter_obj = ScanFilter(resource_types=["vpc"])
        removed = apply_filter_to_graph(graph, filter_obj)

        assert removed == 1
        assert graph.get_resource("vpc-123") is not None
        assert graph.get_resource("subnet-123") is None

    def test_apply_filter_retain_dependencies(self) -> None:
        """Test that dependencies are retained when filtering."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            dependencies=["vpc-123"],  # Subnet depends on VPC
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)

        # Filter for subnets only, but retain dependencies
        filter_obj = ScanFilter(resource_types=["subnet"])
        removed = apply_filter_to_graph(graph, filter_obj, retain_dependencies=True)

        # VPC should be retained because subnet depends on it
        assert graph.get_resource("vpc-123") is not None
        assert graph.get_resource("subnet-123") is not None
        assert removed == 0

    def test_apply_filter_no_retain_dependencies(self) -> None:
        """Test filtering without retaining dependencies."""
        graph = GraphEngine()

        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            dependencies=["vpc-123"],
        )

        graph.add_resource(vpc)
        graph.add_resource(subnet)

        filter_obj = ScanFilter(resource_types=["subnet"])
        removed = apply_filter_to_graph(graph, filter_obj, retain_dependencies=False)

        # VPC should be removed when not retaining dependencies
        assert removed == 1
        assert graph.get_resource("vpc-123") is None
        assert graph.get_resource("subnet-123") is not None

    def test_apply_exclude_filter(self) -> None:
        """Test applying exclusion filter."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="vpc-123",
                resource_type=ResourceType.VPC,
                region="us-east-1",
            )
        )
        graph.add_resource(
            ResourceNode(
                id="sqs-123",
                resource_type=ResourceType.SQS_QUEUE,
                region="us-east-1",
            )
        )

        filter_obj = ScanFilter(exclude_types=["sqs_queue"])
        removed = apply_filter_to_graph(graph, filter_obj)

        assert removed == 1
        assert graph.get_resource("vpc-123") is not None
        assert graph.get_resource("sqs-123") is None
