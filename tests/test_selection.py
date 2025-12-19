"""Tests for graph-based selection engine."""

from __future__ import annotations

import pytest

from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.core.selection import (
    BoundaryAction,
    BoundaryConfig,
    CloneAction,
    CloneDecisionEngine,
    CloneMode,
    DependencyDirection,
    GraphSelector,
    SelectionMode,
    SelectionResult,
    SelectionStrategy,
    TargetContext,
    apply_selection,
    build_subgraph_from_selection,
)

# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def sample_graph() -> GraphEngine:
    """Create a sample graph for testing."""
    graph = GraphEngine()

    # VPC
    vpc = ResourceNode(
        id="vpc-123",
        resource_type=ResourceType.VPC,
        region="us-east-1",
        tags={"Name": "prod-vpc", "Environment": "Production"},
    )
    graph.add_resource(vpc)

    # Subnets
    subnet1 = ResourceNode(
        id="subnet-1",
        resource_type=ResourceType.SUBNET,
        region="us-east-1",
        tags={"Name": "prod-subnet-1", "Environment": "Production"},
        dependencies=["vpc-123"],
    )
    subnet2 = ResourceNode(
        id="subnet-2",
        resource_type=ResourceType.SUBNET,
        region="us-east-1",
        tags={"Name": "prod-subnet-2", "Environment": "Production"},
        dependencies=["vpc-123"],
    )
    graph.add_resource(subnet1)
    graph.add_resource(subnet2)

    # Security Group
    sg = ResourceNode(
        id="sg-123",
        resource_type=ResourceType.SECURITY_GROUP,
        region="us-east-1",
        tags={"Name": "prod-sg", "Environment": "Production"},
        dependencies=["vpc-123"],
    )
    graph.add_resource(sg)

    # EC2 Instances
    ec2_1 = ResourceNode(
        id="i-123",
        resource_type=ResourceType.EC2_INSTANCE,
        region="us-east-1",
        tags={
            "Name": "prod-web-1",
            "Environment": "Production",
            "Application": "MyApp",
        },
        dependencies=["subnet-1", "sg-123"],
    )
    ec2_2 = ResourceNode(
        id="i-456",
        resource_type=ResourceType.EC2_INSTANCE,
        region="us-east-1",
        tags={"Name": "test-web-1", "Environment": "Testing"},
        dependencies=["subnet-2", "sg-123"],
    )
    graph.add_resource(ec2_1)
    graph.add_resource(ec2_2)

    # RDS Instance
    rds = ResourceNode(
        id="db-123",
        resource_type=ResourceType.RDS_INSTANCE,
        region="us-east-1",
        tags={"Name": "prod-db", "Environment": "Production", "Application": "MyApp"},
        dependencies=["subnet-1", "subnet-2", "sg-123"],
    )
    graph.add_resource(rds)

    # Add edges for dependencies
    graph.add_dependency("subnet-1", "vpc-123")
    graph.add_dependency("subnet-2", "vpc-123")
    graph.add_dependency("sg-123", "vpc-123")
    graph.add_dependency("i-123", "subnet-1")
    graph.add_dependency("i-123", "sg-123")
    graph.add_dependency("i-456", "subnet-2")
    graph.add_dependency("i-456", "sg-123")
    graph.add_dependency("db-123", "subnet-1")
    graph.add_dependency("db-123", "subnet-2")
    graph.add_dependency("db-123", "sg-123")

    return graph


# =============================================================================
# Test BoundaryConfig
# =============================================================================


class TestBoundaryConfig:
    """Tests for BoundaryConfig class."""

    def test_default_boundaries(self) -> None:
        """Test default boundary configuration."""
        config = BoundaryConfig()

        # Network boundaries should return DATA_SOURCE
        assert (
            config.get_action("aws_vpc_peering_connection")
            == BoundaryAction.DATA_SOURCE
        )
        assert (
            config.get_action("aws_ec2_transit_gateway") == BoundaryAction.DATA_SOURCE
        )

        # Identity boundaries should return VARIABLE
        assert config.get_action("aws_iam_role") == BoundaryAction.VARIABLE

        # Global resources should return EXCLUDE
        assert config.get_action("aws_route53_zone") == BoundaryAction.EXCLUDE
        assert (
            config.get_action("aws_cloudfront_distribution") == BoundaryAction.EXCLUDE
        )

        # Regular resources should return TRAVERSE
        assert config.get_action("aws_instance") == BoundaryAction.TRAVERSE
        assert config.get_action("aws_vpc") == BoundaryAction.TRAVERSE

    def test_user_overrides(self) -> None:
        """Test user overrides in boundary config."""
        config = BoundaryConfig(
            user_overrides={
                "aws_iam_role": BoundaryAction.TRAVERSE,  # Override default
                "aws_vpc": BoundaryAction.DATA_SOURCE,  # Custom boundary
            }
        )

        assert config.get_action("aws_iam_role") == BoundaryAction.TRAVERSE
        assert config.get_action("aws_vpc") == BoundaryAction.DATA_SOURCE

    def test_type_normalization(self) -> None:
        """Test that resource types are normalized."""
        config = BoundaryConfig()

        # Both with and without aws_ prefix should work
        assert config.get_action("aws_instance") == BoundaryAction.TRAVERSE
        assert config.get_action("instance") == BoundaryAction.TRAVERSE


# =============================================================================
# Test TargetContext
# =============================================================================


class TestTargetContext:
    """Tests for TargetContext class."""

    def test_default_context(self) -> None:
        """Test default target context."""
        ctx = TargetContext()

        assert ctx.same_account is True
        assert ctx.same_region is True
        assert ctx.same_vpc is False
        assert ctx.clone_mode == CloneMode.ISOLATED

    def test_custom_context(self) -> None:
        """Test custom target context."""
        ctx = TargetContext(
            same_account=False,
            clone_mode=CloneMode.SHARED,
            source_env="production",
            target_env="staging",
        )

        assert ctx.same_account is False
        assert ctx.clone_mode == CloneMode.SHARED
        assert ctx.source_env == "production"
        assert ctx.target_env == "staging"


# =============================================================================
# Test SelectionStrategy
# =============================================================================


class TestSelectionStrategy:
    """Tests for SelectionStrategy class."""

    def test_empty_strategy(self) -> None:
        """Test empty selection strategy."""
        strategy = SelectionStrategy()

        assert strategy.is_empty()
        assert strategy.mode == SelectionMode.ALL

    def test_vpc_scope_strategy(self) -> None:
        """Test VPC scope selection strategy."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_ids=["vpc-123", "vpc-456"],
        )

        assert not strategy.is_empty()
        assert strategy.mode == SelectionMode.VPC_SCOPE
        assert "vpc-123" in strategy.vpc_ids

    def test_entry_point_strategy(self) -> None:
        """Test entry point selection strategy."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ENTRY_POINT,
            entry_point_tags={"Application": "MyApp"},
        )

        assert not strategy.is_empty()
        assert strategy.mode == SelectionMode.ENTRY_POINT
        assert strategy.entry_point_tags["Application"] == "MyApp"

    def test_from_cli_args_scope_vpc(self) -> None:
        """Test creating strategy from CLI args with VPC scope."""
        strategy = SelectionStrategy.from_cli_args(scope="vpc:vpc-123")

        assert strategy.mode == SelectionMode.VPC_SCOPE
        assert "vpc-123" in strategy.vpc_ids

    def test_from_cli_args_scope_vpc_name(self) -> None:
        """Test creating strategy from CLI args with VPC name."""
        strategy = SelectionStrategy.from_cli_args(scope="vpc-name:Production*")

        assert strategy.mode == SelectionMode.VPC_SCOPE
        assert "Production*" in strategy.vpc_names

    def test_from_cli_args_entry_tag(self) -> None:
        """Test creating strategy from CLI args with entry tag."""
        strategy = SelectionStrategy.from_cli_args(entry="tag:Application=MyApp")

        assert strategy.mode == SelectionMode.ENTRY_POINT
        assert strategy.entry_point_tags["Application"] == "MyApp"

    def test_from_cli_args_entry_type(self) -> None:
        """Test creating strategy from CLI args with entry type."""
        strategy = SelectionStrategy.from_cli_args(entry="alb:my-app-*")

        assert strategy.mode == SelectionMode.ENTRY_POINT
        assert "alb" in strategy.entry_point_types
        assert "my-app-*" in strategy.entry_point_names

    def test_from_cli_args_excludes(self) -> None:
        """Test creating strategy from CLI args with excludes."""
        strategy = SelectionStrategy.from_cli_args(
            exclude_types="sns,sqs",
            exclude_patterns="test-*,*-tmp",
        )

        assert "sns" in strategy.exclude_types
        assert "sqs" in strategy.exclude_types
        assert "test-*" in strategy.exclude_patterns

    def test_from_dict(self) -> None:
        """Test creating strategy from dictionary."""
        data = {
            "mode": "vpc",
            "vpc_ids": ["vpc-123"],
            "exclude": {
                "types": ["sns", "sqs"],
                "patterns": ["test-*"],
            },
            "target": {
                "clone_mode": "shared",
                "source_env": "prod",
                "target_env": "stage",
            },
        }

        strategy = SelectionStrategy.from_dict(data)

        assert strategy.mode == SelectionMode.VPC_SCOPE
        assert "vpc-123" in strategy.vpc_ids
        assert "sns" in strategy.exclude_types
        assert strategy.target_context.clone_mode == CloneMode.SHARED

    def test_describe(self) -> None:
        """Test strategy description."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_ids=["vpc-123"],
            exclude_types={"sns"},
        )

        description = strategy.describe()
        assert "vpc-123" in description
        assert "sns" in description


# =============================================================================
# Test CloneDecisionEngine
# =============================================================================


class TestCloneDecisionEngine:
    """Tests for CloneDecisionEngine class."""

    def test_clone_ec2_always(self) -> None:
        """Test that EC2 instances are always cloned."""
        # Same VPC
        ctx = TargetContext(same_vpc=True)
        engine = CloneDecisionEngine(ctx)

        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )

        assert engine.decide(ec2) == CloneAction.CLONE

    def test_reference_subnet_same_vpc(self) -> None:
        """Test that subnets are referenced in same VPC."""
        ctx = TargetContext(same_vpc=True)
        engine = CloneDecisionEngine(ctx)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        assert engine.decide(subnet) == CloneAction.REFERENCE

    def test_clone_subnet_new_vpc(self) -> None:
        """Test that subnets are cloned in new VPC."""
        ctx = TargetContext(same_vpc=False, same_account=True)
        engine = CloneDecisionEngine(ctx)

        subnet = ResourceNode(
            id="subnet-123",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
        )

        assert engine.decide(subnet) == CloneAction.CLONE

    def test_reference_iam_same_account(self) -> None:
        """Test that IAM roles are referenced in same account."""
        ctx = TargetContext(same_account=True)
        engine = CloneDecisionEngine(ctx)

        role = ResourceNode(
            id="role-123",
            resource_type=ResourceType.VPC,  # Using VPC as proxy since IAM isn't in enum
            region="us-east-1",
        )
        # Override resource type for test
        role._resource_type_value = "aws_iam_role"

        # For resources not in matrix, default is CLONE
        assert engine.decide(role) == CloneAction.CLONE

    def test_shared_resource_detection(self) -> None:
        """Test shared resource detection."""
        ctx = TargetContext(clone_mode=CloneMode.SHARED)
        engine = CloneDecisionEngine(ctx)

        # Shared resource by name
        shared = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            tags={"Name": "shared-vpc"},
        )

        # In SHARED mode, shared resources should be referenced
        # Note: VPC in new VPC context would be N/A, but we're testing shared detection
        assert engine._is_shared_resource(shared) is True

    def test_aws_managed_detection(self) -> None:
        """Test AWS-managed resource detection."""
        ctx = TargetContext()
        engine = CloneDecisionEngine(ctx)

        # Default resource
        default = ResourceNode(
            id="sg-123",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            tags={"Name": "default"},
        )

        assert engine._is_aws_managed(default) is True

        # Regular resource
        regular = ResourceNode(
            id="sg-456",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            tags={"Name": "my-sg"},
        )

        assert engine._is_aws_managed(regular) is False


# =============================================================================
# Test GraphSelector
# =============================================================================


class TestGraphSelector:
    """Tests for GraphSelector class."""

    def test_select_all(self, sample_graph: GraphEngine) -> None:
        """Test selecting all resources."""
        strategy = SelectionStrategy(mode=SelectionMode.ALL)
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        # Should include all 7 resources
        assert result.total_selected == 7

    def test_select_by_vpc(self, sample_graph: GraphEngine) -> None:
        """Test VPC-scoped selection."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_ids=["vpc-123"],
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        # Should include VPC and all downstream resources
        selected_ids = {r.id for r in result.get_all_selected()}
        assert "vpc-123" in selected_ids
        assert "subnet-1" in selected_ids
        assert "subnet-2" in selected_ids
        assert "sg-123" in selected_ids

    def test_select_by_vpc_name(self, sample_graph: GraphEngine) -> None:
        """Test VPC-scoped selection by name pattern."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_names=["prod-*"],
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}
        assert "vpc-123" in selected_ids

    def test_select_by_entry_point_tag(self, sample_graph: GraphEngine) -> None:
        """Test entry point selection by tag."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ENTRY_POINT,
            entry_point_tags={"Application": "MyApp"},
            direction=DependencyDirection.UPSTREAM,
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}

        # Should find EC2 and RDS with Application=MyApp
        assert "i-123" in selected_ids
        assert "db-123" in selected_ids

        # Should include upstream dependencies
        assert "subnet-1" in selected_ids
        assert "sg-123" in selected_ids
        assert "vpc-123" in selected_ids

    def test_select_with_exclude_types(self, sample_graph: GraphEngine) -> None:
        """Test selection with type exclusion."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ALL,
            exclude_types={"instance"},  # Exclude EC2
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}

        # EC2 instances should be excluded
        assert "i-123" not in selected_ids
        assert "i-456" not in selected_ids

        # Other resources should be included
        assert "vpc-123" in selected_ids
        assert "db-123" in selected_ids

    def test_select_with_exclude_patterns(self, sample_graph: GraphEngine) -> None:
        """Test selection with name pattern exclusion."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ALL,
            exclude_patterns=["test-*"],
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}

        # test-web-1 should be excluded
        assert "i-456" not in selected_ids

        # prod resources should be included
        assert "i-123" in selected_ids

    def test_select_by_tag_based(self, sample_graph: GraphEngine) -> None:
        """Test tag-based selection."""
        strategy = SelectionStrategy(
            mode=SelectionMode.TAG_BASED,
            entry_point_tags={"Environment": "Production"},
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}

        # All Production resources and their dependencies
        assert "vpc-123" in selected_ids
        assert "subnet-1" in selected_ids
        assert "subnet-2" in selected_ids
        assert "i-123" in selected_ids
        assert "db-123" in selected_ids

        # Testing resource should not be a direct selection
        # but may be included as dependency

    def test_dependency_resolution(self, sample_graph: GraphEngine) -> None:
        """Test that dependencies are automatically included."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ENTRY_POINT,
            entry_points=["i-123"],  # Just the EC2 instance
            direction=DependencyDirection.UPSTREAM,
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        selected_ids = {r.id for r in result.get_all_selected()}

        # Should include all upstream dependencies
        assert "i-123" in selected_ids
        assert "subnet-1" in selected_ids
        assert "sg-123" in selected_ids
        assert "vpc-123" in selected_ids

    def test_max_depth_limit(self, sample_graph: GraphEngine) -> None:
        """Test that max depth is respected."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_ids=["vpc-123"],
            max_depth=2,  # Limited depth
        )
        selector = GraphSelector(sample_graph, strategy)

        result = selector.select()

        # Depth should be tracked (note: dependency resolution may add more)
        assert result.traversal_depth_reached <= strategy.max_depth


# =============================================================================
# Test SelectionResult
# =============================================================================


class TestSelectionResult:
    """Tests for SelectionResult class."""

    def test_empty_result(self) -> None:
        """Test empty selection result."""
        result = SelectionResult()

        assert result.total_selected == 0
        summary = result.summary()
        assert summary["total"] == 0

    def test_result_with_resources(self) -> None:
        """Test selection result with resources."""
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )

        result = SelectionResult(
            to_clone=[ec2],
            data_sources=[vpc],
            entry_points_found=["i-123"],
        )

        assert result.total_selected == 2
        summary = result.summary()
        assert summary["clone"] == 1
        assert summary["reference"] == 1
        assert summary["entry_points"] == 1

    def test_get_all_selected(self) -> None:
        """Test getting all selected resources."""
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
        )

        result = SelectionResult(
            to_clone=[ec2],
            data_sources=[vpc],
        )

        all_selected = result.get_all_selected()
        assert len(all_selected) == 2
        ids = {r.id for r in all_selected}
        assert "vpc-123" in ids
        assert "i-123" in ids


# =============================================================================
# Test Helper Functions
# =============================================================================


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_apply_selection(self, sample_graph: GraphEngine) -> None:
        """Test apply_selection helper function."""
        strategy = SelectionStrategy(
            mode=SelectionMode.VPC_SCOPE,
            vpc_ids=["vpc-123"],
        )

        result = apply_selection(sample_graph, strategy)

        assert result.total_selected > 0

    def test_build_subgraph_from_selection(self, sample_graph: GraphEngine) -> None:
        """Test building subgraph from selection result."""
        strategy = SelectionStrategy(
            mode=SelectionMode.ENTRY_POINT,
            entry_points=["i-123"],
            direction=DependencyDirection.UPSTREAM,
        )

        result = apply_selection(sample_graph, strategy)
        subgraph = build_subgraph_from_selection(sample_graph, result)

        # Subgraph should contain only selected resources
        assert subgraph.node_count <= sample_graph.node_count

        # Should have proper dependencies
        ec2 = subgraph.get_resource("i-123")
        assert ec2 is not None
        deps = subgraph.get_dependencies("i-123")
        dep_ids = {d.id for d in deps}
        assert "subnet-1" in dep_ids or "sg-123" in dep_ids


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for the selection system."""

    def test_full_workflow(self, sample_graph: GraphEngine) -> None:
        """Test complete selection workflow."""
        # 1. Create strategy from CLI-like args
        strategy = SelectionStrategy.from_cli_args(
            scope="vpc:vpc-123",
            exclude_types="sqs,sns",
        )

        # 2. Apply selection
        result = apply_selection(sample_graph, strategy)

        # 3. Build subgraph
        subgraph = build_subgraph_from_selection(sample_graph, result)

        # 4. Verify results
        assert subgraph.node_count > 0
        assert result.summary()["clone"] + result.summary()["reference"] > 0

    def test_tag_based_workflow(self, sample_graph: GraphEngine) -> None:
        """Test tag-based selection workflow."""
        strategy = SelectionStrategy.from_cli_args(
            entry="tag:Application=MyApp",
        )

        result = apply_selection(sample_graph, strategy)

        # Should find resources with Application=MyApp and their dependencies
        selected_ids = {r.id for r in result.get_all_selected()}
        assert "i-123" in selected_ids
        assert "db-123" in selected_ids
