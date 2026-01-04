"""Tests for centrality analysis module."""

from __future__ import annotations

import pytest

from replimap.core.analysis.centrality import (
    AttackSurfaceAnalyzer,
    BlastRadiusResult,
    CentralityAnalyzer,
    CriticalityLevel,
    CriticalResourceFinder,
    SinglePointOfFailureResult,
)
from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType


class TestCentralityAnalyzer:
    """Tests for CentralityAnalyzer."""

    @pytest.fixture
    def graph(self) -> GraphEngine:
        """Create a test graph with hub structure."""
        graph = GraphEngine()

        # Create a hub: VPC that everything depends on
        hub = ResourceNode(
            id="vpc-hub",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="vpc_hub",
            original_name="Hub VPC",
        )
        graph.add_resource(hub)

        # Create multiple resources that depend on the hub
        for i in range(5):
            node = ResourceNode(
                id=f"subnet-{i}",
                resource_type=ResourceType.SUBNET,
                region="us-east-1",
                config={},
                tags={},
                terraform_name=f"subnet_{i}",
                original_name=f"Subnet {i}",
            )
            graph.add_resource(node)
            graph.add_dependency(f"subnet-{i}", "vpc-hub")

        # Add EC2 instances that depend on subnets
        for i in range(3):
            node = ResourceNode(
                id=f"i-{i}",
                resource_type=ResourceType.EC2_INSTANCE,
                region="us-east-1",
                config={},
                tags={},
                terraform_name=f"instance_{i}",
                original_name=f"Instance {i}",
            )
            graph.add_resource(node)
            graph.add_dependency(f"i-{i}", f"subnet-{i}")

        return graph

    def test_compute_betweenness_centrality(self, graph: GraphEngine) -> None:
        """Test betweenness centrality computation."""
        analyzer = CentralityAnalyzer(graph)
        betweenness = analyzer.compute_betweenness_centrality()

        # All nodes should have a score
        assert len(betweenness) == graph.node_count

        # VPC should have high betweenness (it's the hub)
        assert "vpc-hub" in betweenness

    def test_compute_pagerank(self, graph: GraphEngine) -> None:
        """Test PageRank computation."""
        analyzer = CentralityAnalyzer(graph)
        pagerank = analyzer.compute_pagerank()

        # All nodes should have a score
        assert len(pagerank) == graph.node_count

        # Sum of PageRank should be approximately 1
        total = sum(pagerank.values())
        assert abs(total - 1.0) < 0.01

    def test_find_single_points_of_failure(self, graph: GraphEngine) -> None:
        """Test SPOF detection."""
        analyzer = CentralityAnalyzer(graph)
        spofs = analyzer.find_single_points_of_failure(threshold_percentile=50)

        # VPC should be identified as SPOF
        vpc_spof = next((s for s in spofs if s.resource_id == "vpc-hub"), None)
        assert vpc_spof is not None
        assert vpc_spof.dependent_count == 5  # All subnets depend on it

    def test_find_spof_with_threshold(self, graph: GraphEngine) -> None:
        """Test SPOF detection with different thresholds."""
        analyzer = CentralityAnalyzer(graph)

        # High threshold = fewer results
        spofs_high = analyzer.find_single_points_of_failure(threshold_percentile=90)
        # Low threshold = more results
        spofs_low = analyzer.find_single_points_of_failure(threshold_percentile=30)

        assert len(spofs_low) >= len(spofs_high)

    def test_compute_blast_radius(self, graph: GraphEngine) -> None:
        """Test blast radius computation."""
        analyzer = CentralityAnalyzer(graph)

        # VPC failure should cascade to all subnets and instances
        result = analyzer.compute_blast_radius("vpc-hub")

        assert result.resource_id == "vpc-hub"
        assert result.affected_count == 8  # 5 subnets + 3 instances

    def test_blast_radius_leaf_node(self, graph: GraphEngine) -> None:
        """Test blast radius for leaf node (no dependents)."""
        analyzer = CentralityAnalyzer(graph)

        result = analyzer.compute_blast_radius("i-0")

        assert result.affected_count == 0
        assert result.depth == 0

    def test_blast_radius_nonexistent_node(self, graph: GraphEngine) -> None:
        """Test blast radius for non-existent node."""
        analyzer = CentralityAnalyzer(graph)

        result = analyzer.compute_blast_radius("nonexistent")

        assert result.affected_count == 0

    def test_blast_radius_cascade_depth(self, graph: GraphEngine) -> None:
        """Test cascade depth in blast radius."""
        analyzer = CentralityAnalyzer(graph)

        result = analyzer.compute_blast_radius("vpc-hub")

        # Depth should be 2: VPC -> Subnet -> Instance
        assert result.depth == 2

    def test_get_top_by_betweenness(self, graph: GraphEngine) -> None:
        """Test top nodes by betweenness."""
        analyzer = CentralityAnalyzer(graph)
        top = analyzer.get_top_by_betweenness(n=3)

        assert len(top) == 3
        assert all(isinstance(t, tuple) and len(t) == 2 for t in top)

    def test_get_top_by_pagerank(self, graph: GraphEngine) -> None:
        """Test top nodes by PageRank."""
        analyzer = CentralityAnalyzer(graph)
        top = analyzer.get_top_by_pagerank(n=3)

        assert len(top) == 3
        # VPC should be in top 3 (it's the most important)
        top_ids = [t[0] for t in top]
        assert "vpc-hub" in top_ids


class TestAttackSurfaceAnalyzer:
    """Tests for AttackSurfaceAnalyzer."""

    @pytest.fixture
    def graph_with_exposure(self) -> GraphEngine:
        """Create a graph with exposed resources."""
        graph = GraphEngine()

        # Internet gateway (exposed)
        igw = ResourceNode(
            id="igw-123",
            resource_type=ResourceType.INTERNET_GATEWAY,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="igw",
            original_name="Internet Gateway",
        )
        graph.add_resource(igw)

        # Load balancer (exposed)
        lb = ResourceNode(
            id="lb-123",
            resource_type=ResourceType.LB,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="lb",
            original_name="Load Balancer",
        )
        graph.add_resource(lb)

        # Security group with public access
        sg = ResourceNode(
            id="sg-123",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            config={
                "IpPermissions": [
                    {"IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
                ]
            },
            tags={},
            terraform_name="sg",
            original_name="Security Group",
        )
        graph.add_resource(sg)

        # EC2 with public IP
        ec2 = ResourceNode(
            id="i-123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={"PublicIpAddress": "1.2.3.4"},
            tags={},
            terraform_name="instance",
            original_name="Public Instance",
        )
        graph.add_resource(ec2)

        return graph

    def test_find_exposed_resources(self, graph_with_exposure: GraphEngine) -> None:
        """Test exposed resource detection."""
        analyzer = AttackSurfaceAnalyzer(graph_with_exposure)
        exposed = analyzer.find_exposed_resources()

        # IGW, LB, and EC2 with public IP should be exposed
        assert "igw-123" in exposed
        assert "lb-123" in exposed
        assert "i-123" in exposed

    def test_find_public_resources(self, graph_with_exposure: GraphEngine) -> None:
        """Test public resource detection."""
        analyzer = AttackSurfaceAnalyzer(graph_with_exposure)
        public = analyzer.find_public_resources()

        # Security group with 0.0.0.0/0 should be flagged
        assert "sg-123" in public

    def test_compute_attack_surface(self, graph_with_exposure: GraphEngine) -> None:
        """Test full attack surface computation."""
        analyzer = AttackSurfaceAnalyzer(graph_with_exposure)
        result = analyzer.compute_attack_surface()

        assert len(result.exposed_resources) >= 2
        assert len(result.public_resources) >= 1
        assert result.risk_score > 0

    def test_attack_surface_clean_graph(self) -> None:
        """Test attack surface on clean graph."""
        graph = GraphEngine()

        # Internal VPC only
        vpc = ResourceNode(
            id="vpc-internal",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="vpc",
            original_name="Internal VPC",
        )
        graph.add_resource(vpc)

        analyzer = AttackSurfaceAnalyzer(graph)
        result = analyzer.compute_attack_surface()

        assert len(result.exposed_resources) == 0
        assert len(result.public_resources) == 0
        assert result.risk_score == 0.0


class TestCriticalResourceFinder:
    """Tests for CriticalResourceFinder."""

    @pytest.fixture
    def complex_graph(self) -> GraphEngine:
        """Create a complex graph for criticality testing."""
        graph = GraphEngine()

        # Create hierarchy: VPC -> Subnets -> Instances
        vpc = ResourceNode(
            id="vpc-main",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="main_vpc",
            original_name="Main VPC",
        )
        graph.add_resource(vpc)

        for i in range(3):
            subnet = ResourceNode(
                id=f"subnet-{i}",
                resource_type=ResourceType.SUBNET,
                region="us-east-1",
                config={},
                tags={},
                terraform_name=f"subnet_{i}",
                original_name=f"Subnet {i}",
            )
            graph.add_resource(subnet)
            graph.add_dependency(f"subnet-{i}", "vpc-main")

            for j in range(2):
                instance = ResourceNode(
                    id=f"i-{i}-{j}",
                    resource_type=ResourceType.EC2_INSTANCE,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=f"instance_{i}_{j}",
                    original_name=f"Instance {i}-{j}",
                )
                graph.add_resource(instance)
                graph.add_dependency(f"i-{i}-{j}", f"subnet-{i}")

        return graph

    def test_find_critical(self, complex_graph: GraphEngine) -> None:
        """Test critical resource detection."""
        finder = CriticalResourceFinder(complex_graph)
        critical = finder.find_critical(top_n=5)

        assert len(critical) <= 5

        # VPC should be most critical
        assert critical[0].resource_id == "vpc-main"
        assert critical[0].level in (CriticalityLevel.CRITICAL, CriticalityLevel.HIGH)

    def test_find_critical_scores(self, complex_graph: GraphEngine) -> None:
        """Test that critical resources have valid scores."""
        finder = CriticalResourceFinder(complex_graph)
        critical = finder.find_critical(top_n=10)

        for result in critical:
            assert 0 <= result.score <= 100
            assert result.blast_radius >= 0
            assert result.dependent_count >= 0

    def test_criticality_levels(self, complex_graph: GraphEngine) -> None:
        """Test criticality level assignment."""
        finder = CriticalResourceFinder(complex_graph)
        critical = finder.find_critical(top_n=10)

        # Should have variety of levels
        levels = {r.level for r in critical}
        assert len(levels) >= 1

    def test_generate_report(self, complex_graph: GraphEngine) -> None:
        """Test report generation."""
        finder = CriticalResourceFinder(complex_graph)
        report = finder.generate_report(top_n=5)

        assert "Critical Resource Analysis Report" in report
        assert "Total Resources:" in report
        assert "Attack Surface Score:" in report
        assert "vpc-main" in report

    def test_factors_populated(self, complex_graph: GraphEngine) -> None:
        """Test that criticality factors are populated."""
        finder = CriticalResourceFinder(complex_graph)
        critical = finder.find_critical(top_n=5)

        # VPC should have factors explaining its criticality
        vpc_result = next(r for r in critical if r.resource_id == "vpc-main")
        assert len(vpc_result.factors) > 0


class TestDataClasses:
    """Tests for analysis data classes."""

    def test_single_point_of_failure_result(self) -> None:
        """Test SinglePointOfFailureResult."""
        result = SinglePointOfFailureResult(
            resource_id="vpc-123",
            resource_type="vpc",
            dependent_count=10,
            dependents=["subnet-1", "subnet-2"],
            in_degree_percentile=95.0,
        )

        assert result.resource_id == "vpc-123"
        assert result.dependent_count == 10
        assert len(result.dependents) == 2

    def test_blast_radius_result(self) -> None:
        """Test BlastRadiusResult."""
        result = BlastRadiusResult(
            resource_id="vpc-123",
            affected_count=5,
            affected_resources=["a", "b", "c", "d", "e"],
            depth=3,
            by_type={"subnet": 3, "instance": 2},
            cascade_path={"a": 1, "b": 1, "c": 2, "d": 2, "e": 3},
        )

        assert result.affected_count == 5
        assert result.depth == 3
        assert result.by_type["subnet"] == 3

    def test_criticality_level_values(self) -> None:
        """Test CriticalityLevel enum values."""
        assert CriticalityLevel.LOW.value == "low"
        assert CriticalityLevel.MEDIUM.value == "medium"
        assert CriticalityLevel.HIGH.value == "high"
        assert CriticalityLevel.CRITICAL.value == "critical"


class TestEmptyGraph:
    """Tests for edge cases with empty graphs."""

    def test_centrality_analyzer_empty(self) -> None:
        """Test CentralityAnalyzer on empty graph."""
        graph = GraphEngine()
        analyzer = CentralityAnalyzer(graph)

        assert analyzer.compute_betweenness_centrality() == {}
        assert analyzer.find_single_points_of_failure() == []

    def test_critical_finder_empty(self) -> None:
        """Test CriticalResourceFinder on empty graph."""
        graph = GraphEngine()
        finder = CriticalResourceFinder(graph)

        critical = finder.find_critical(top_n=10)
        assert critical == []

    def test_attack_surface_empty(self) -> None:
        """Test AttackSurfaceAnalyzer on empty graph."""
        graph = GraphEngine()
        analyzer = AttackSurfaceAnalyzer(graph)

        result = analyzer.compute_attack_surface()
        assert result.risk_score == 0.0
