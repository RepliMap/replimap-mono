"""
Comprehensive tests for Graph Simplification feature.

Tests filtering, grouping, and building of simplified graphs.
"""

import pytest

from replimap.core.models import ResourceNode, ResourceType
from replimap.graph import (
    BuilderConfig,
    GraphBuilder,
    GraphFilter,
    GroupingConfig,
    GroupingStrategy,
    ResourceGroup,
    ResourceGrouper,
    ResourceVisibility,
)
from replimap.graph.filters import (
    NOISY_RESOURCE_TYPES,
    RESOURCE_VISIBILITY,
    ROUTE_TYPES,
    SG_RULE_TYPES,
)


# =============================================================================
# TEST FIXTURES
# =============================================================================


def create_resource(
    resource_id: str,
    resource_type: ResourceType,
    name: str | None = None,
    vpc_id: str | None = None,
    subnet_id: str | None = None,
    dependencies: list[str] | None = None,
) -> ResourceNode:
    """Create a test resource node."""
    config = {}
    if vpc_id:
        config["vpc_id"] = vpc_id
    if subnet_id:
        config["subnet_id"] = subnet_id

    return ResourceNode(
        id=resource_id,
        resource_type=resource_type,
        region="us-east-1",
        config=config,
        tags={"Name": name or resource_id},
        dependencies=dependencies or [],
    )


def create_sample_resources() -> list[ResourceNode]:
    """Create a sample set of resources for testing."""
    return [
        # Core resources
        create_resource("vpc-123", ResourceType.VPC, "main-vpc"),
        create_resource(
            "subnet-1", ResourceType.SUBNET, "public-1", vpc_id="vpc-123"
        ),
        create_resource(
            "subnet-2", ResourceType.SUBNET, "public-2", vpc_id="vpc-123"
        ),
        # Compute resources
        create_resource(
            "i-001", ResourceType.EC2_INSTANCE, "web-1", subnet_id="subnet-1"
        ),
        create_resource(
            "i-002", ResourceType.EC2_INSTANCE, "web-2", subnet_id="subnet-1"
        ),
        create_resource(
            "i-003", ResourceType.EC2_INSTANCE, "web-3", subnet_id="subnet-1"
        ),
        create_resource(
            "i-004", ResourceType.EC2_INSTANCE, "api-1", subnet_id="subnet-2"
        ),
        create_resource(
            "i-005", ResourceType.EC2_INSTANCE, "api-2", subnet_id="subnet-2"
        ),
        # Security resources
        create_resource("sg-web", ResourceType.SECURITY_GROUP, "web-sg", vpc_id="vpc-123"),
        create_resource("sg-api", ResourceType.SECURITY_GROUP, "api-sg", vpc_id="vpc-123"),
        # Database
        create_resource("db-1", ResourceType.RDS_INSTANCE, "primary-db"),
        # Network detail
        create_resource("rtb-1", ResourceType.ROUTE_TABLE, "main-route-table"),
        create_resource("nat-1", ResourceType.NAT_GATEWAY, "nat-gateway"),
    ]


# =============================================================================
# FILTER TESTS
# =============================================================================


class TestGraphFilter:
    """Tests for GraphFilter class."""

    def test_default_filter_creation(self):
        """Test creating default filter."""
        f = GraphFilter.default()

        assert f.show_all is False
        assert f.show_sg_rules is False
        assert f.show_routes is False
        assert f.show_security is True

    def test_show_everything_filter(self):
        """Test filter that shows all resources."""
        f = GraphFilter.show_everything()

        assert f.show_all is True

    def test_security_focused_filter(self):
        """Test security-focused filter."""
        f = GraphFilter.security_focused()

        assert f.show_security is True
        assert f.show_sg_rules is True

    def test_should_show_core_resources(self):
        """Test that core resources are always shown."""
        f = GraphFilter.default()
        resources = create_sample_resources()

        vpc = [r for r in resources if r.resource_type == ResourceType.VPC][0]
        subnet = [r for r in resources if r.resource_type == ResourceType.SUBNET][0]
        ec2 = [r for r in resources if r.resource_type == ResourceType.EC2_INSTANCE][0]
        rds = [r for r in resources if r.resource_type == ResourceType.RDS_INSTANCE][0]

        assert f.should_show(vpc) is True
        assert f.should_show(subnet) is True
        assert f.should_show(ec2) is True
        assert f.should_show(rds) is True

    def test_should_show_security_groups_by_default(self):
        """Test that security groups are shown by default."""
        f = GraphFilter.default()
        resources = create_sample_resources()

        sg = [r for r in resources if r.resource_type == ResourceType.SECURITY_GROUP][0]
        assert f.should_show(sg) is True

    def test_should_hide_routes_by_default(self):
        """Test that routes are hidden by default."""
        f = GraphFilter.default()

        # Route type not in core types
        assert f.should_show_type("aws_route") is False
        assert f.should_show_type("aws_route_table") is False

    def test_should_show_routes_with_flag(self):
        """Test showing routes with flag."""
        f = GraphFilter(show_routes=True)

        assert f.should_show_type("aws_route") is True
        assert f.should_show_type("aws_route_table") is True

    def test_should_show_all_overrides(self):
        """Test that show_all overrides other settings."""
        f = GraphFilter(show_all=True)

        # Even noisy types should be shown
        assert f.should_show_type("aws_route") is True
        assert f.should_show_type("aws_security_group_rule") is True

    def test_explicit_hide_types(self):
        """Test explicitly hiding specific types."""
        f = GraphFilter(hide_types={"aws_instance"})
        resources = create_sample_resources()

        ec2 = [r for r in resources if r.resource_type == ResourceType.EC2_INSTANCE][0]
        assert f.should_show(ec2) is False

    def test_explicit_show_types_overrides_hide(self):
        """Test that show_types overrides hide_types."""
        f = GraphFilter(
            hide_types={"aws_instance"},
            show_types={"aws_instance"},
        )
        resources = create_sample_resources()

        ec2 = [r for r in resources if r.resource_type == ResourceType.EC2_INSTANCE][0]
        assert f.should_show(ec2) is True

    def test_filter_resources_list(self):
        """Test filtering a list of resources."""
        f = GraphFilter.default()
        resources = create_sample_resources()

        filtered = f.filter_resources(resources)

        # All core + security resources should be present
        assert len(filtered) >= 10  # VPC, subnets, instances, SGs, RDS

    def test_get_hidden_count(self):
        """Test counting hidden resources."""
        f = GraphFilter(show_routes=False)

        # Create a resource that would be hidden
        route = create_resource("route-1", ResourceType.ROUTE, "default-route")
        resources = [route]

        hidden = f.get_hidden_count(resources)
        assert "aws_route" in hidden
        assert hidden["aws_route"] == 1

    def test_get_summary(self):
        """Test getting filter summary."""
        f = GraphFilter.default()
        summary = f.get_summary()

        assert "core resources" in summary.lower()
        assert "security" in summary.lower()

    def test_to_dict(self):
        """Test serializing filter to dict."""
        f = GraphFilter(
            show_all=True,
            show_sg_rules=True,
        )
        d = f.to_dict()

        assert d["show_all"] is True
        assert d["show_sg_rules"] is True
        assert isinstance(d["hide_types"], list)
        assert isinstance(d["show_types"], list)

    def test_from_dict(self):
        """Test deserializing filter from dict."""
        d = {
            "show_all": True,
            "show_sg_rules": True,
            "show_routes": False,
            "show_security": True,
            "hide_types": ["aws_instance"],
            "show_types": [],
        }
        f = GraphFilter.from_dict(d)

        assert f.show_all is True
        assert f.show_sg_rules is True
        assert "aws_instance" in f.hide_types


class TestResourceVisibility:
    """Tests for resource visibility classification."""

    def test_core_resources_classified(self):
        """Test core resources are classified correctly."""
        assert RESOURCE_VISIBILITY["aws_vpc"] == ResourceVisibility.CORE
        assert RESOURCE_VISIBILITY["aws_subnet"] == ResourceVisibility.CORE
        assert RESOURCE_VISIBILITY["aws_instance"] == ResourceVisibility.CORE
        assert RESOURCE_VISIBILITY["aws_db_instance"] == ResourceVisibility.CORE
        assert RESOURCE_VISIBILITY["aws_s3_bucket"] == ResourceVisibility.CORE

    def test_security_resources_classified(self):
        """Test security resources are classified correctly."""
        assert RESOURCE_VISIBILITY["aws_security_group"] == ResourceVisibility.SECURITY
        assert RESOURCE_VISIBILITY["aws_iam_role"] == ResourceVisibility.SECURITY
        assert RESOURCE_VISIBILITY["aws_kms_key"] == ResourceVisibility.SECURITY

    def test_noisy_resources_in_set(self):
        """Test noisy resource types are in the set."""
        assert "aws_security_group_rule" in NOISY_RESOURCE_TYPES
        assert "aws_route" in NOISY_RESOURCE_TYPES

    def test_sg_rule_types(self):
        """Test SG rule types set."""
        assert "aws_security_group_rule" in SG_RULE_TYPES

    def test_route_types(self):
        """Test route types set."""
        assert "aws_route" in ROUTE_TYPES
        assert "aws_route_table" in ROUTE_TYPES


# =============================================================================
# GROUPER TESTS
# =============================================================================


class TestResourceGroup:
    """Tests for ResourceGroup class."""

    def test_group_creation(self):
        """Test creating a resource group."""
        group = ResourceGroup(
            group_id="group_instance_subnet-1",
            resource_type="aws_instance",
            count=5,
            scope_id="subnet-1",
            scope_type="aws_subnet",
            member_ids=["i-1", "i-2", "i-3", "i-4", "i-5"],
        )

        assert group.group_id == "group_instance_subnet-1"
        assert group.resource_type == "aws_instance"
        assert group.count == 5
        assert len(group.member_ids) == 5

    def test_group_auto_label(self):
        """Test automatic label generation."""
        group = ResourceGroup(
            group_id="group_instance",
            resource_type="aws_instance",
            count=10,
            member_ids=["i-" + str(i) for i in range(10)],
        )

        assert "10" in group.label
        assert "EC2" in group.label or "instance" in group.label.lower()

    def test_group_is_collapsed(self):
        """Test is_collapsed property."""
        single = ResourceGroup(
            group_id="single",
            resource_type="aws_instance",
            count=1,
            member_ids=["i-1"],
        )
        multiple = ResourceGroup(
            group_id="multiple",
            resource_type="aws_instance",
            count=5,
            member_ids=["i-" + str(i) for i in range(5)],
        )

        assert single.is_collapsed is False
        assert multiple.is_collapsed is True

    def test_group_to_dict(self):
        """Test group serialization."""
        group = ResourceGroup(
            group_id="group_test",
            resource_type="aws_instance",
            count=3,
            member_ids=["i-1", "i-2", "i-3"],
        )
        d = group.to_dict()

        assert d["group_id"] == "group_test"
        assert d["resource_type"] == "aws_instance"
        assert d["count"] == 3
        assert d["is_collapsed"] is True


class TestGroupingConfig:
    """Tests for GroupingConfig class."""

    def test_default_config(self):
        """Test default grouping config."""
        config = GroupingConfig()

        assert config.enabled is True
        assert config.strategy == GroupingStrategy.BY_SUBNET
        assert config.collapse_threshold == 5

    def test_disabled_config(self):
        """Test disabled grouping config."""
        config = GroupingConfig.disabled()

        assert config.enabled is False

    def test_aggressive_config(self):
        """Test aggressive grouping config."""
        config = GroupingConfig.aggressive()

        assert config.collapse_threshold == 3

    def test_should_collapse_with_threshold(self):
        """Test collapse decision based on threshold."""
        config = GroupingConfig(collapse_threshold=5)

        # Instance type is in collapse_types
        assert config.should_collapse("aws_instance", 3) is False
        assert config.should_collapse("aws_instance", 5) is True
        assert config.should_collapse("aws_instance", 10) is True

    def test_should_not_collapse_never_types(self):
        """Test that never_collapse types are not collapsed."""
        config = GroupingConfig()

        # VPC should never be collapsed
        assert config.should_collapse("aws_vpc", 100) is False
        assert config.should_collapse("aws_subnet", 100) is False
        assert config.should_collapse("aws_db_instance", 100) is False


class TestResourceGrouper:
    """Tests for ResourceGrouper class."""

    def test_grouper_creation(self):
        """Test creating a grouper."""
        grouper = ResourceGrouper()

        assert grouper.config.enabled is True

    def test_grouper_disabled_returns_all(self):
        """Test disabled grouper returns all resources."""
        config = GroupingConfig.disabled()
        grouper = ResourceGrouper(config)
        resources = create_sample_resources()

        ungrouped, groups = grouper.group_resources(resources)

        assert len(ungrouped) == len(resources)
        assert len(groups) == 0

    def test_grouper_groups_by_subnet(self):
        """Test grouping resources by subnet."""
        config = GroupingConfig(
            strategy=GroupingStrategy.BY_SUBNET,
            collapse_threshold=3,
        )
        grouper = ResourceGrouper(config)

        # Create 5 instances in same subnet (should collapse)
        resources = [
            create_resource(f"i-{i}", ResourceType.EC2_INSTANCE, f"web-{i}", subnet_id="subnet-1")
            for i in range(5)
        ]

        ungrouped, groups = grouper.group_resources(resources)

        # Should be grouped into one
        assert len(groups) == 1
        assert groups[0].count == 5
        assert len(ungrouped) == 0

    def test_grouper_keeps_small_groups(self):
        """Test that small groups are not collapsed."""
        config = GroupingConfig(collapse_threshold=5)
        grouper = ResourceGrouper(config)

        # Create only 3 instances (below threshold)
        resources = [
            create_resource(f"i-{i}", ResourceType.EC2_INSTANCE, f"web-{i}", subnet_id="subnet-1")
            for i in range(3)
        ]

        ungrouped, groups = grouper.group_resources(resources)

        # Should not be grouped
        assert len(groups) == 0
        assert len(ungrouped) == 3

    def test_grouper_multiple_groups(self):
        """Test grouping creates multiple groups for different scopes."""
        config = GroupingConfig(collapse_threshold=3)
        grouper = ResourceGrouper(config)

        resources = [
            # 5 in subnet-1
            create_resource(f"i-1-{i}", ResourceType.EC2_INSTANCE, f"web-{i}", subnet_id="subnet-1")
            for i in range(5)
        ] + [
            # 4 in subnet-2
            create_resource(f"i-2-{i}", ResourceType.EC2_INSTANCE, f"api-{i}", subnet_id="subnet-2")
            for i in range(4)
        ]

        ungrouped, groups = grouper.group_resources(resources)

        # Should create 2 groups
        assert len(groups) == 2
        assert sum(g.count for g in groups) == 9

    def test_grouper_by_type_strategy(self):
        """Test grouping by type strategy."""
        config = GroupingConfig(
            strategy=GroupingStrategy.BY_TYPE,
            collapse_threshold=3,
        )
        grouper = ResourceGrouper(config)

        # 10 instances across different subnets
        resources = [
            create_resource(f"i-{i}", ResourceType.EC2_INSTANCE, f"inst-{i}", subnet_id=f"subnet-{i % 3}")
            for i in range(10)
        ]

        ungrouped, groups = grouper.group_resources(resources)

        # All instances should be in one group (by type, ignoring subnet)
        assert len(groups) == 1
        assert groups[0].count == 10

    def test_grouping_summary(self):
        """Test getting grouping summary."""
        config = GroupingConfig(collapse_threshold=3)
        grouper = ResourceGrouper(config)

        resources = [
            create_resource(f"i-{i}", ResourceType.EC2_INSTANCE, f"web-{i}", subnet_id="subnet-1")
            for i in range(5)
        ]

        ungrouped, groups = grouper.group_resources(resources)
        summary = grouper.get_grouping_summary(ungrouped, groups)

        assert summary["original_count"] == 5
        assert summary["after_grouping"] == 1
        assert summary["reduction"] == 4
        assert summary["reduction_percent"] == 80.0


# =============================================================================
# BUILDER TESTS
# =============================================================================


class TestBuilderConfig:
    """Tests for BuilderConfig class."""

    def test_simplified_config(self):
        """Test simplified (default) config."""
        config = BuilderConfig.simplified()

        assert config.filter.show_all is False
        assert config.grouping.enabled is True

    def test_full_config(self):
        """Test full config."""
        config = BuilderConfig.full()

        assert config.filter.show_all is True
        assert config.grouping.enabled is False

    def test_security_view_config(self):
        """Test security view config."""
        config = BuilderConfig.security_view()

        assert config.filter.show_sg_rules is True
        assert config.grouping.enabled is False


class TestGraphBuilder:
    """Tests for GraphBuilder class."""

    def create_mock_graph_engine(self):
        """Create a mock graph engine with test resources."""
        from replimap.core import GraphEngine

        graph = GraphEngine()
        for resource in create_sample_resources():
            graph.add_resource(resource)

        return graph

    def test_builder_creation(self):
        """Test creating a builder."""
        builder = GraphBuilder()

        assert builder.config is not None

    def test_build_returns_visualization_graph(self):
        """Test build returns VisualizationGraph."""
        from replimap.graph import VisualizationGraph

        builder = GraphBuilder()
        graph = self.create_mock_graph_engine()

        result = builder.build(graph)

        assert isinstance(result, VisualizationGraph)

    def test_build_includes_metadata(self):
        """Test build includes metadata."""
        builder = GraphBuilder()
        graph = self.create_mock_graph_engine()

        result = builder.build(graph)

        assert "total_resources" in result.metadata
        assert "visible_resources" in result.metadata
        assert "simplification" in result.metadata

    def test_build_with_filtering(self):
        """Test build applies filtering."""
        config = BuilderConfig(
            filter=GraphFilter(show_routes=False),
        )
        builder = GraphBuilder(config)
        graph = self.create_mock_graph_engine()

        result = builder.build(graph)

        # Route tables should be filtered out
        node_types = [n.resource_type for n in result.nodes]
        assert "aws_route_table" not in node_types

    def test_build_with_grouping(self):
        """Test build applies grouping."""
        from replimap.core import GraphEngine

        config = BuilderConfig(
            grouping=GroupingConfig(collapse_threshold=3),
        )
        builder = GraphBuilder(config)

        # Create graph with many instances
        graph = GraphEngine()
        for i in range(10):
            resource = create_resource(
                f"i-{i}",
                ResourceType.EC2_INSTANCE,
                f"web-{i}",
                subnet_id="subnet-1",
            )
            graph.add_resource(resource)

        result = builder.build(graph)

        # Should have grouped nodes
        has_group = any(n.properties.get("is_group") for n in result.nodes)
        assert has_group

    def test_build_preserves_edges(self):
        """Test that edges are preserved after filtering."""
        from replimap.core import GraphEngine

        builder = GraphBuilder()
        graph = GraphEngine()

        vpc = create_resource("vpc-1", ResourceType.VPC, "main")
        subnet = create_resource("subnet-1", ResourceType.SUBNET, "public", vpc_id="vpc-1")

        graph.add_resource(vpc)
        graph.add_resource(subnet)
        graph.add_dependency("subnet-1", "vpc-1")

        result = builder.build(graph)

        # Should have edge from subnet to VPC
        assert len(result.edges) >= 1
        edge_pairs = [(e.source, e.target) for e in result.edges]
        assert ("subnet-1", "vpc-1") in edge_pairs

    def test_simplification_summary(self):
        """Test getting simplification summary."""
        builder = GraphBuilder()
        graph = self.create_mock_graph_engine()

        summary = builder.get_simplification_summary(graph)

        assert "original_count" in summary
        assert "after_filtering" in summary
        assert "after_grouping" in summary
        assert "filter_summary" in summary


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestGraphSimplificationIntegration:
    """Integration tests for the complete simplification pipeline."""

    def test_full_simplification_pipeline(self):
        """Test complete simplification from resources to graph."""
        from replimap.core import GraphEngine

        # Create a realistic set of resources
        graph = GraphEngine()

        # Add VPC and subnets
        vpc = create_resource("vpc-main", ResourceType.VPC, "production-vpc")
        graph.add_resource(vpc)

        for i in range(3):
            subnet = create_resource(
                f"subnet-{i}",
                ResourceType.SUBNET,
                f"public-{i}",
                vpc_id="vpc-main",
            )
            graph.add_resource(subnet)
            graph.add_dependency(f"subnet-{i}", "vpc-main")

        # Add many EC2 instances (should be grouped)
        for i in range(15):
            subnet_id = f"subnet-{i % 3}"
            instance = create_resource(
                f"i-{i:03d}",
                ResourceType.EC2_INSTANCE,
                f"web-{i}",
                subnet_id=subnet_id,
            )
            graph.add_resource(instance)
            graph.add_dependency(f"i-{i:03d}", subnet_id)

        # Add security groups
        for i in range(2):
            sg = create_resource(
                f"sg-{i}",
                ResourceType.SECURITY_GROUP,
                f"sg-{i}",
                vpc_id="vpc-main",
            )
            graph.add_resource(sg)

        # Build simplified graph
        config = BuilderConfig(
            filter=GraphFilter.default(),
            grouping=GroupingConfig(collapse_threshold=5),
        )
        builder = GraphBuilder(config)
        result = builder.build(graph)

        # Verify simplification occurred
        # Original: 1 VPC + 3 subnets + 15 instances + 2 SGs = 21
        # After grouping: 1 VPC + 3 subnets + 3 groups + 2 SGs = 9
        assert len(result.nodes) < 21
        assert result.metadata["total_resources"] == 21

        # Verify groups exist
        groups = [n for n in result.nodes if n.properties.get("is_group")]
        assert len(groups) == 3  # One per subnet

    def test_security_focused_view(self):
        """Test security-focused view shows appropriate resources."""
        from replimap.core import GraphEngine

        graph = GraphEngine()
        graph.add_resource(create_resource("vpc-1", ResourceType.VPC, "vpc"))
        graph.add_resource(create_resource("sg-1", ResourceType.SECURITY_GROUP, "sg", vpc_id="vpc-1"))
        graph.add_resource(create_resource("i-1", ResourceType.EC2_INSTANCE, "ec2", subnet_id="subnet-1"))

        config = BuilderConfig.security_view()
        builder = GraphBuilder(config)
        result = builder.build(graph)

        node_types = [n.resource_type for n in result.nodes]
        assert "aws_security_group" in node_types
        assert "aws_vpc" in node_types

    def test_show_all_mode(self):
        """Test that show_all mode includes all resources."""
        from replimap.core import GraphEngine

        graph = GraphEngine()
        graph.add_resource(create_resource("vpc-1", ResourceType.VPC, "vpc"))
        graph.add_resource(create_resource("rtb-1", ResourceType.ROUTE_TABLE, "rtb"))
        graph.add_resource(create_resource("route-1", ResourceType.ROUTE, "route"))

        config = BuilderConfig.full()
        builder = GraphBuilder(config)
        result = builder.build(graph)

        node_ids = [n.id for n in result.nodes]
        assert "vpc-1" in node_ids
        assert "rtb-1" in node_ids
        assert "route-1" in node_ids

    def test_vpc_filtering_with_simplification(self):
        """Test VPC filtering works with simplification."""
        from replimap.core import GraphEngine

        graph = GraphEngine()

        # Resources in VPC-1
        graph.add_resource(create_resource("vpc-1", ResourceType.VPC, "vpc-1"))
        graph.add_resource(create_resource("subnet-1", ResourceType.SUBNET, "subnet", vpc_id="vpc-1"))

        # Resources in VPC-2 (should be filtered out)
        graph.add_resource(create_resource("vpc-2", ResourceType.VPC, "vpc-2"))
        graph.add_resource(create_resource("subnet-2", ResourceType.SUBNET, "subnet", vpc_id="vpc-2"))

        builder = GraphBuilder()
        result = builder.build(graph, vpc_id="vpc-1")

        node_ids = [n.id for n in result.nodes]
        assert "vpc-1" in node_ids
        assert "subnet-1" in node_ids
        assert "vpc-2" not in node_ids
        assert "subnet-2" not in node_ids
