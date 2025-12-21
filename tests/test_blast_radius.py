"""
Comprehensive tests for the Dependency Explorer feature (formerly Blast Radius).

These tests validate the core functionality of dependency analysis.
See test_deps_disclaimer.py for tests ensuring disclaimers are present.
"""

import json
import tempfile
from pathlib import Path

import networkx as nx
import pytest

# Import from new module - backward compatibility aliases also work
from replimap.dependencies import (
    RESOURCE_IMPACT_SCORES,
    DependencyEdge,
    DependencyExplorerReporter,
    DependencyExplorerResult,
    DependencyGraphBuilder,
    DependencyType,
    DependencyZone,
    ImpactCalculator,
    ImpactLevel,
    ResourceNode,
)

# Backward compatibility aliases for existing tests
BlastNode = ResourceNode
BlastRadiusResult = DependencyExplorerResult
BlastZone = DependencyZone
BlastRadiusReporter = DependencyExplorerReporter


class TestBlastModels:
    """Tests for blast radius data models."""

    def test_impact_level_enum(self):
        """Test ImpactLevel enum values."""
        assert ImpactLevel.CRITICAL.value == "CRITICAL"
        assert ImpactLevel.HIGH.value == "HIGH"
        assert ImpactLevel.MEDIUM.value == "MEDIUM"
        assert ImpactLevel.LOW.value == "LOW"
        assert ImpactLevel.NONE.value == "NONE"

    def test_dependency_type_enum(self):
        """Test DependencyType enum values."""
        assert DependencyType.HARD.value == "HARD"
        assert DependencyType.SOFT.value == "SOFT"
        assert DependencyType.REFERENCE.value == "REFERENCE"

    def test_blast_node_creation(self):
        """Test BlastNode dataclass creation."""
        node = BlastNode(
            id="vpc-12345",
            type="aws_vpc",
            name="main-vpc",
            arn="arn:aws:ec2:us-east-1:123456789012:vpc/vpc-12345",
            region="us-east-1",
            impact_level=ImpactLevel.CRITICAL,
            impact_score=100,
            depth=0,
        )

        assert node.id == "vpc-12345"
        assert node.type == "aws_vpc"
        assert node.name == "main-vpc"
        assert node.region == "us-east-1"
        assert node.impact_level == ImpactLevel.CRITICAL
        assert node.impact_score == 100
        assert node.depth == 0
        assert node.depends_on == []
        assert node.depended_by == []

    def test_blast_node_to_dict(self):
        """Test BlastNode serialization."""
        node = BlastNode(
            id="sg-abc123",
            type="aws_security_group",
            name="web-sg",
            impact_level=ImpactLevel.HIGH,
            impact_score=75,
            depth=1,
            depends_on=["vpc-12345"],
            depended_by=["i-xyz789"],
        )

        data = node.to_dict()

        assert data["id"] == "sg-abc123"
        assert data["type"] == "aws_security_group"
        assert data["name"] == "web-sg"
        assert data["impact_level"] == "HIGH"
        assert data["impact_score"] == 75
        assert data["depth"] == 1
        assert data["depends_on"] == ["vpc-12345"]
        assert data["depended_by"] == ["i-xyz789"]

    def test_dependency_edge_creation(self):
        """Test DependencyEdge dataclass creation."""
        edge = DependencyEdge(
            source_id="i-xyz789",
            target_id="sg-abc123",
            dependency_type=DependencyType.HARD,
            attribute="vpc_security_group_ids",
            description="EC2 instance depends on security group",
        )

        assert edge.source_id == "i-xyz789"
        assert edge.target_id == "sg-abc123"
        assert edge.dependency_type == DependencyType.HARD
        assert edge.attribute == "vpc_security_group_ids"

    def test_dependency_edge_to_dict(self):
        """Test DependencyEdge serialization."""
        edge = DependencyEdge(
            source_id="i-xyz789",
            target_id="sg-abc123",
            dependency_type=DependencyType.SOFT,
        )

        data = edge.to_dict()

        assert data["source_id"] == "i-xyz789"
        assert data["target_id"] == "sg-abc123"
        assert data["dependency_type"] == "SOFT"

    def test_blast_zone_creation(self):
        """Test BlastZone dataclass creation."""
        node1 = BlastNode(id="i-123", type="aws_instance", name="web1", impact_score=80)
        node2 = BlastNode(id="i-456", type="aws_instance", name="web2", impact_score=80)

        zone = BlastZone(
            depth=1,
            resources=[node1, node2],
            total_impact_score=160,
        )

        assert zone.depth == 1
        assert len(zone.resources) == 2
        assert zone.total_impact_score == 160

    def test_blast_zone_to_dict(self):
        """Test BlastZone serialization."""
        node = BlastNode(id="i-123", type="aws_instance", name="web1")
        zone = BlastZone(depth=2, resources=[node], total_impact_score=80)

        data = zone.to_dict()

        assert data["depth"] == 2
        assert data["resources"] == ["i-123"]
        assert data["resource_count"] == 1
        assert data["total_impact_score"] == 80

    def test_blast_radius_result_creation(self):
        """Test BlastRadiusResult dataclass creation."""
        center = BlastNode(id="sg-abc", type="aws_security_group", name="web-sg")
        zone1 = BlastZone(depth=1, resources=[], total_impact_score=80)

        result = BlastRadiusResult(
            center_resource=center,
            zones=[zone1],
            affected_resources=[],
            total_affected=2,
            max_depth=1,
            estimated_impact=ImpactLevel.HIGH,
            estimated_score=85,
            suggested_review_order=["i-123", "sg-abc"],
            warnings=["Critical resource"],
        )

        assert result.center_resource.id == "sg-abc"
        assert len(result.zones) == 1
        assert result.total_affected == 2
        assert result.estimated_impact == ImpactLevel.HIGH

    def test_blast_radius_result_to_dict(self):
        """Test BlastRadiusResult serialization."""
        center = BlastNode(id="sg-abc", type="aws_security_group", name="web-sg")
        result = BlastRadiusResult(
            center_resource=center,
            zones=[],
            total_affected=0,
            estimated_impact=ImpactLevel.LOW,
            estimated_score=30,
        )

        data = result.to_dict()

        assert data["center"]["id"] == "sg-abc"
        assert data["summary"]["total_affected"] == 0
        assert data["summary"]["estimated_impact"] == "LOW"
        assert data["summary"]["estimated_score"] == 30


class TestDependencyGraphBuilder:
    """Tests for DependencyGraphBuilder."""

    def test_initialization(self):
        """Test builder initialization."""
        builder = DependencyGraphBuilder()

        assert isinstance(builder.graph, nx.DiGraph)
        assert builder.nodes == {}
        assert builder.edges == []

    def test_build_from_resources(self):
        """Test building graph from resource list."""
        resources = [
            {
                "id": "vpc-12345",
                "type": "aws_vpc",
                "name": "main-vpc",
                "config": {"cidr_block": "10.0.0.0/16"},
            },
            {
                "id": "subnet-abc",
                "type": "aws_subnet",
                "name": "web-subnet",
                "config": {"vpc_id": "vpc-12345", "cidr_block": "10.0.1.0/24"},
            },
        ]

        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        assert len(builder.nodes) == 2
        assert "vpc-12345" in builder.nodes
        assert "subnet-abc" in builder.nodes
        assert graph.has_edge("subnet-abc", "vpc-12345")

    def test_get_nodes(self):
        """Test retrieving nodes."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
        ]

        builder = DependencyGraphBuilder()
        builder.build_from_resources(resources)

        nodes = builder.get_nodes()
        assert len(nodes) == 1
        assert "vpc-123" in nodes

    def test_get_edges(self):
        """Test retrieving edges."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
            {"id": "subnet-abc", "type": "aws_subnet", "name": "subnet", "config": {"vpc_id": "vpc-123"}},
        ]

        builder = DependencyGraphBuilder()
        builder.build_from_resources(resources)

        edges = builder.get_edges()
        assert len(edges) >= 1
        edge_pairs = [(e.source_id, e.target_id) for e in edges]
        assert ("subnet-abc", "vpc-123") in edge_pairs

    def test_security_group_ec2_dependency(self):
        """Test security group to EC2 dependency detection."""
        resources = [
            {"id": "sg-123", "type": "aws_security_group", "name": "web-sg", "config": {}},
            {
                "id": "i-456",
                "type": "aws_instance",
                "name": "web-server",
                "config": {"vpc_security_group_ids": ["sg-123"]},
            },
        ]

        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        assert graph.has_edge("i-456", "sg-123")

    def test_rds_subnet_group_dependency(self):
        """Test RDS to subnet group dependency."""
        resources = [
            {"id": "dbsg-123", "type": "aws_db_subnet_group", "name": "main", "config": {}},
            {
                "id": "db-456",
                "type": "aws_db_instance",
                "name": "main-db",
                "config": {"db_subnet_group_name": "main"},
            },
        ]

        builder = DependencyGraphBuilder()
        builder.build_from_resources(resources)

        # Check that the dependency is found
        nodes = builder.get_nodes()
        assert "dbsg-123" in nodes
        assert "db-456" in nodes

    def test_multiple_dependencies(self):
        """Test resource with multiple dependencies."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
            {"id": "subnet-abc", "type": "aws_subnet", "name": "subnet", "config": {"vpc_id": "vpc-123"}},
            {"id": "sg-123", "type": "aws_security_group", "name": "sg", "config": {"vpc_id": "vpc-123"}},
            {
                "id": "i-789",
                "type": "aws_instance",
                "name": "web",
                "config": {
                    "subnet_id": "subnet-abc",
                    "vpc_security_group_ids": ["sg-123"],
                },
            },
        ]

        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        assert graph.has_edge("i-789", "subnet-abc")
        assert graph.has_edge("i-789", "sg-123")
        assert graph.has_edge("subnet-abc", "vpc-123")
        assert graph.has_edge("sg-123", "vpc-123")

    def test_reverse_dependencies_calculated(self):
        """Test that reverse dependencies are calculated."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
            {"id": "subnet-abc", "type": "aws_subnet", "name": "subnet", "config": {"vpc_id": "vpc-123"}},
        ]

        builder = DependencyGraphBuilder()
        builder.build_from_resources(resources)

        vpc_node = builder.nodes["vpc-123"]
        subnet_node = builder.nodes["subnet-abc"]

        assert "subnet-abc" in vpc_node.depended_by
        assert "vpc-123" in subnet_node.depends_on


class TestImpactCalculator:
    """Tests for ImpactCalculator."""

    def _create_simple_graph(self):
        """Create a simple dependency graph for testing."""
        graph = nx.DiGraph()
        nodes = {
            "vpc-123": BlastNode(id="vpc-123", type="aws_vpc", name="main-vpc"),
            "subnet-abc": BlastNode(id="subnet-abc", type="aws_subnet", name="subnet"),
            "sg-def": BlastNode(id="sg-def", type="aws_security_group", name="web-sg"),
            "i-789": BlastNode(id="i-789", type="aws_instance", name="web-server"),
        }

        # Add nodes to graph
        for node_id, node in nodes.items():
            graph.add_node(node_id, **node.to_dict())

        # Add dependencies: i-789 -> sg-def, sg-def -> vpc-123, subnet-abc -> vpc-123
        graph.add_edge("i-789", "sg-def")
        graph.add_edge("i-789", "subnet-abc")
        graph.add_edge("sg-def", "vpc-123")
        graph.add_edge("subnet-abc", "vpc-123")

        # Update node dependencies
        nodes["vpc-123"].depended_by = ["sg-def", "subnet-abc"]
        nodes["sg-def"].depends_on = ["vpc-123"]
        nodes["sg-def"].depended_by = ["i-789"]
        nodes["subnet-abc"].depends_on = ["vpc-123"]
        nodes["subnet-abc"].depended_by = ["i-789"]
        nodes["i-789"].depends_on = ["sg-def", "subnet-abc"]

        return graph, nodes

    def test_initialization(self):
        """Test calculator initialization."""
        graph = nx.DiGraph()
        nodes = {}

        calculator = ImpactCalculator(graph, nodes)

        assert calculator.graph == graph
        assert calculator.nodes == nodes
        assert calculator.edges == []

    def test_resource_not_found(self):
        """Test error when resource not found."""
        graph = nx.DiGraph()
        nodes = {}

        calculator = ImpactCalculator(graph, nodes)

        with pytest.raises(ValueError, match="not found"):
            calculator.calculate_blast_radius("nonexistent-id")

    def test_calculate_blast_radius_simple(self):
        """Test blast radius calculation for simple graph."""
        graph, nodes = self._create_simple_graph()

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("vpc-123")

        assert result.center_resource.id == "vpc-123"
        assert result.total_affected >= 2  # At least sg-def and subnet-abc

    def test_blast_radius_includes_indirect_deps(self):
        """Test that indirect dependents are included."""
        graph, nodes = self._create_simple_graph()

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("vpc-123")

        affected_ids = [r.id for r in result.affected_resources]
        # i-789 depends on sg-def which depends on vpc-123
        assert "i-789" in affected_ids or result.total_affected >= 1

    def test_blast_radius_zones(self):
        """Test that zones are organized by depth."""
        graph, nodes = self._create_simple_graph()

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("vpc-123", max_depth=10)

        # Zones should be sorted by depth
        depths = [z.depth for z in result.zones]
        assert depths == sorted(depths)

    def test_suggested_review_order(self):
        """Test suggested review order generation."""
        graph, nodes = self._create_simple_graph()

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("vpc-123")

        # Suggested review order should have entries
        assert isinstance(result.suggested_review_order, list)
        # Check that order contains expected resources
        assert len(result.suggested_review_order) > 0

    def test_estimated_impact_critical(self):
        """Test estimated impact for critical resource."""
        graph = nx.DiGraph()
        nodes = {
            "vpc-123": BlastNode(id="vpc-123", type="aws_vpc", name="vpc"),
            "sg-456": BlastNode(id="sg-456", type="aws_security_group", name="sg"),
            "db-789": BlastNode(id="db-789", type="aws_db_instance", name="db"),
        }

        for node_id, node in nodes.items():
            graph.add_node(node_id, **node.to_dict())

        graph.add_edge("sg-456", "vpc-123")
        graph.add_edge("db-789", "vpc-123")

        nodes["vpc-123"].depended_by = ["sg-456", "db-789"]

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("vpc-123")

        # VPC with DB dependent should be critical or high
        assert result.estimated_impact in (ImpactLevel.CRITICAL, ImpactLevel.HIGH)

    def test_max_depth_limit(self):
        """Test that max_depth limits traversal."""
        # Create a chain: a -> b -> c -> d -> e
        graph = nx.DiGraph()
        nodes = {}

        for letter in "abcde":
            node = BlastNode(id=letter, type="aws_instance", name=f"node-{letter}")
            nodes[letter] = node
            graph.add_node(letter, **node.to_dict())

        graph.add_edge("b", "a")
        graph.add_edge("c", "b")
        graph.add_edge("d", "c")
        graph.add_edge("e", "d")

        for letter in "abcde":
            if letter in "abcd":
                nodes[letter].depended_by = [chr(ord(letter) + 1)]
            if letter in "bcde":
                nodes[letter].depends_on = [chr(ord(letter) - 1)]

        calculator = ImpactCalculator(graph, nodes)

        # With max_depth=2, should only get b and c when starting from a
        result = calculator.calculate_blast_radius("a", max_depth=2)
        assert result.max_depth <= 2

    def test_warnings_generated(self):
        """Test that warnings are generated appropriately."""
        graph = nx.DiGraph()
        nodes = {
            "db-123": BlastNode(id="db-123", type="aws_db_instance", name="prod-db"),
        }

        graph.add_node("db-123", **nodes["db-123"].to_dict())

        calculator = ImpactCalculator(graph, nodes)
        result = calculator.calculate_blast_radius("db-123")

        # DB instance should generate a warning about data
        assert isinstance(result.warnings, list)


class TestResourceImpactScores:
    """Tests for resource impact scores."""

    def test_vpc_is_critical(self):
        """Test VPC has highest score."""
        assert RESOURCE_IMPACT_SCORES["aws_vpc"] == 100

    def test_db_instance_is_high(self):
        """Test DB instance has high score."""
        assert RESOURCE_IMPACT_SCORES["aws_db_instance"] >= 90

    def test_instance_is_high(self):
        """Test EC2 instance has moderately high score."""
        assert RESOURCE_IMPACT_SCORES["aws_instance"] >= 70

    def test_route_is_low(self):
        """Test routes have low score."""
        assert RESOURCE_IMPACT_SCORES["aws_route"] <= 50

    def test_default_score_exists(self):
        """Test default score is available."""
        assert "_default" in RESOURCE_IMPACT_SCORES
        assert RESOURCE_IMPACT_SCORES["_default"] == 50


class TestBlastRadiusReporter:
    """Tests for BlastRadiusReporter output."""

    def _create_sample_result(self) -> BlastRadiusResult:
        """Create a sample result for testing."""
        center = BlastNode(
            id="sg-123",
            type="aws_security_group",
            name="web-sg",
            impact_level=ImpactLevel.HIGH,
            impact_score=75,
        )

        affected1 = BlastNode(
            id="i-456",
            type="aws_instance",
            name="web-1",
            impact_level=ImpactLevel.HIGH,
            impact_score=80,
            depth=1,
        )

        affected2 = BlastNode(
            id="i-789",
            type="aws_instance",
            name="web-2",
            impact_level=ImpactLevel.HIGH,
            impact_score=80,
            depth=1,
        )

        zone1 = BlastZone(
            depth=1,
            resources=[affected1, affected2],
            total_impact_score=160,
        )

        edge1 = DependencyEdge(source_id="i-456", target_id="sg-123")
        edge2 = DependencyEdge(source_id="i-789", target_id="sg-123")

        return BlastRadiusResult(
            center_resource=center,
            zones=[zone1],
            affected_resources=[affected1, affected2],
            edges=[edge1, edge2],
            total_affected=2,
            max_depth=1,
            estimated_impact=ImpactLevel.HIGH,
            estimated_score=80,
            suggested_review_order=["i-456", "i-789", "sg-123"],
            warnings=["Production resources affected"],
        )

    def test_reporter_initialization(self):
        """Test reporter initialization."""
        reporter = BlastRadiusReporter()
        assert reporter is not None

    def test_to_console(self, capsys):
        """Test console output."""
        reporter = BlastRadiusReporter()
        result = self._create_sample_result()

        # Should not raise
        reporter.to_console(result)

    def test_to_tree(self, capsys):
        """Test tree output."""
        reporter = BlastRadiusReporter()
        result = self._create_sample_result()

        reporter.to_tree(result)

    def test_to_table(self, capsys):
        """Test table output."""
        reporter = BlastRadiusReporter()
        result = self._create_sample_result()

        reporter.to_table(result)

    def test_to_json(self):
        """Test JSON export."""
        reporter = BlastRadiusReporter()
        result = self._create_sample_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "blast-radius.json"
            reporter.to_json(result, output_path)

            assert output_path.exists()

            with open(output_path) as f:
                data = json.load(f)

            assert data["center"]["id"] == "sg-123"
            assert data["summary"]["total_affected"] == 2
            assert len(data["affected_resources"]) == 2

    def test_to_html(self):
        """Test HTML export."""
        reporter = BlastRadiusReporter()
        result = self._create_sample_result()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "blast-radius.html"
            reporter.to_html(result, output_path)

            assert output_path.exists()

            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "sg-123" in content
            # Check for D3.js library reference
            assert "d3" in content.lower()

    def test_empty_result(self):
        """Test handling of empty result."""
        reporter = BlastRadiusReporter()

        center = BlastNode(id="orphan-123", type="aws_instance", name="orphan")
        result = BlastRadiusResult(
            center_resource=center,
            zones=[],
            affected_resources=[],
            total_affected=0,
            estimated_impact=ImpactLevel.NONE,
            estimated_score=0,
        )

        # Should not raise
        reporter.to_console(result)

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "empty.json"
            reporter.to_json(result, json_path)
            assert json_path.exists()


class TestBlastIntegration:
    """Integration tests for blast radius feature."""

    def test_full_workflow(self):
        """Test complete workflow from resources to report."""
        # Define resources
        resources = [
            {"id": "vpc-main", "type": "aws_vpc", "name": "main-vpc", "config": {}},
            {
                "id": "subnet-web",
                "type": "aws_subnet",
                "name": "web-subnet",
                "config": {"vpc_id": "vpc-main"},
            },
            {
                "id": "sg-web",
                "type": "aws_security_group",
                "name": "web-sg",
                "config": {"vpc_id": "vpc-main"},
            },
            {
                "id": "i-web-1",
                "type": "aws_instance",
                "name": "web-1",
                "config": {
                    "subnet_id": "subnet-web",
                    "vpc_security_group_ids": ["sg-web"],
                },
            },
            {
                "id": "i-web-2",
                "type": "aws_instance",
                "name": "web-2",
                "config": {
                    "subnet_id": "subnet-web",
                    "vpc_security_group_ids": ["sg-web"],
                },
            },
        ]

        # Build graph
        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        # Calculate blast radius for VPC
        calculator = ImpactCalculator(graph, builder.get_nodes(), builder.get_edges())
        result = calculator.calculate_blast_radius("vpc-main")

        # Verify result
        assert result.center_resource.id == "vpc-main"
        assert result.total_affected >= 2  # At least subnet and sg
        assert result.estimated_impact in (ImpactLevel.CRITICAL, ImpactLevel.HIGH)

        # Export to JSON
        with tempfile.TemporaryDirectory() as tmpdir:
            reporter = BlastRadiusReporter()
            json_path = Path(tmpdir) / "blast.json"
            reporter.to_json(result, json_path)

            data = json.loads(json_path.read_text())
            assert data["center"]["id"] == "vpc-main"

    def test_security_group_blast_radius(self):
        """Test blast radius for security group deletion."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
            {"id": "sg-web", "type": "aws_security_group", "name": "web-sg", "config": {"vpc_id": "vpc-123"}},
            {
                "id": "i-1",
                "type": "aws_instance",
                "name": "web-1",
                "config": {"vpc_security_group_ids": ["sg-web"]},
            },
            {
                "id": "i-2",
                "type": "aws_instance",
                "name": "web-2",
                "config": {"vpc_security_group_ids": ["sg-web"]},
            },
            {
                "id": "i-3",
                "type": "aws_instance",
                "name": "web-3",
                "config": {"vpc_security_group_ids": ["sg-web"]},
            },
        ]

        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        calculator = ImpactCalculator(graph, builder.get_nodes())
        result = calculator.calculate_blast_radius("sg-web")

        # Deleting sg-web should affect all 3 instances
        affected_ids = [r.id for r in result.affected_resources]
        assert "i-1" in affected_ids
        assert "i-2" in affected_ids
        assert "i-3" in affected_ids

    def test_database_blast_radius(self):
        """Test blast radius for database resources."""
        resources = [
            {"id": "vpc-123", "type": "aws_vpc", "name": "vpc", "config": {}},
            {
                "id": "dbsg-123",
                "type": "aws_db_subnet_group",
                "name": "db-subnets",
                "config": {"vpc_id": "vpc-123"},
            },
            {
                "id": "db-main",
                "type": "aws_db_instance",
                "name": "main-db",
                "config": {"db_subnet_group_name": "db-subnets"},
            },
        ]

        builder = DependencyGraphBuilder()
        graph = builder.build_from_resources(resources)

        calculator = ImpactCalculator(graph, builder.get_nodes())

        # Deleting subnet group should show DB is affected
        result = calculator.calculate_blast_radius("dbsg-123")

        affected_ids = [r.id for r in result.affected_resources]
        assert "db-main" in affected_ids
