"""Tests for graph algorithms (transitive reduction, simplification)."""

from __future__ import annotations

import pytest

from replimap.core.graph.algorithms import (
    GraphSimplifier,
    GraphStats,
    ReductionResult,
    TransitiveReducer,
)
from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType


class TestTransitiveReducer:
    """Tests for TransitiveReducer."""

    def _create_graph(self) -> GraphEngine:
        """Create a test graph with redundant edges."""
        graph = GraphEngine()

        # Create nodes: A -> B -> C, and also A -> C (redundant)
        node_a = ResourceNode(
            id="a",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="vpc_a",
            original_name="VPC A",
        )
        node_b = ResourceNode(
            id="b",
            resource_type=ResourceType.SUBNET,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="subnet_b",
            original_name="Subnet B",
        )
        node_c = ResourceNode(
            id="c",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={},
            tags={},
            terraform_name="instance_c",
            original_name="Instance C",
        )

        graph.add_resource(node_a)
        graph.add_resource(node_b)
        graph.add_resource(node_c)

        # A -> B -> C (chain)
        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        # A -> C (redundant shortcut)
        graph.add_dependency("a", "c")

        return graph

    def test_get_redundant_edges_identifies_shortcuts(self) -> None:
        """Test that redundant shortcut edges are identified."""
        graph = self._create_graph()
        reducer = TransitiveReducer(graph)

        redundant = reducer.get_redundant_edges()

        # A -> C is redundant because A -> B -> C exists
        assert ("a", "c") in redundant
        assert len(redundant) == 1

    def test_reduce_without_modification(self) -> None:
        """Test reduction preview without modifying graph."""
        graph = self._create_graph()
        original_edges = graph.edge_count

        reducer = TransitiveReducer(graph)
        result = reducer.reduce(in_place=False)

        # Graph should not be modified
        assert graph.edge_count == original_edges
        assert result.edges_removed == 1
        assert result.original_edge_count == 3
        assert result.reduced_edge_count == 2

    def test_reduce_in_place(self) -> None:
        """Test reduction with in-place modification."""
        graph = self._create_graph()

        reducer = TransitiveReducer(graph)
        result = reducer.reduce(in_place=True)

        # Graph should be modified
        assert graph.edge_count == 2
        assert result.edges_removed == 1
        assert ("a", "c") in result.removed_edges

    def test_reduce_no_redundant_edges(self) -> None:
        """Test reduction on graph with no redundant edges."""
        graph = GraphEngine()

        # Simple chain: A -> B -> C (no shortcuts)
        for name in ["a", "b", "c"]:
            graph.add_resource(
                ResourceNode(
                    id=name,
                    resource_type=ResourceType.VPC,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=name,
                    original_name=name.upper(),
                )
            )

        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")

        reducer = TransitiveReducer(graph)
        result = reducer.reduce(in_place=False)

        assert result.edges_removed == 0
        assert result.reduction_ratio == 0.0

    def test_reduction_result_summary(self) -> None:
        """Test the summary property of ReductionResult."""
        result = ReductionResult(
            original_edge_count=10,
            reduced_edge_count=7,
            edges_removed=3,
            removed_edges=[("a", "b"), ("c", "d"), ("e", "f")],
            reduction_ratio=30.0,
        )

        summary = result.summary
        assert "10" in summary
        assert "7" in summary
        assert "30.0%" in summary

    def test_get_reduction_preview(self) -> None:
        """Test reduction preview grouped by source."""
        graph = self._create_graph()
        reducer = TransitiveReducer(graph)

        preview = reducer.get_reduction_preview()

        assert "a" in preview
        assert "c" in preview["a"]


class TestGraphSimplifier:
    """Tests for GraphSimplifier."""

    @pytest.fixture
    def graph(self) -> GraphEngine:
        """Create a test graph."""
        graph = GraphEngine()

        for i in range(5):
            graph.add_resource(
                ResourceNode(
                    id=f"node_{i}",
                    resource_type=ResourceType.VPC,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=f"node_{i}",
                    original_name=f"Node {i}",
                )
            )

        # Create some dependencies
        graph.add_dependency("node_0", "node_1")
        graph.add_dependency("node_1", "node_2")
        graph.add_dependency("node_2", "node_3")
        graph.add_dependency("node_0", "node_3")  # Shortcut
        graph.add_dependency("node_3", "node_4")

        return graph

    def test_compute_stats(self, graph: GraphEngine) -> None:
        """Test statistics computation."""
        simplifier = GraphSimplifier(graph)
        stats = simplifier.compute_stats()

        assert stats.node_count == 5
        assert stats.edge_count == 5
        assert stats.density > 0
        assert stats.avg_degree > 0
        assert not stats.has_cycles
        assert stats.connected_components == 1

    def test_compute_stats_empty_graph(self) -> None:
        """Test statistics on empty graph."""
        graph = GraphEngine()
        simplifier = GraphSimplifier(graph)
        stats = simplifier.compute_stats()

        assert stats.node_count == 0
        assert stats.edge_count == 0
        assert stats.density == 0.0

    def test_simplify(self, graph: GraphEngine) -> None:
        """Test graph simplification."""
        simplifier = GraphSimplifier(graph)
        result = simplifier.simplify(apply=True)

        assert result.edges_removed > 0
        assert graph.edge_count < 5

    def test_simplify_preview(self, graph: GraphEngine) -> None:
        """Test simplification preview without modification."""
        simplifier = GraphSimplifier(graph)
        original_edges = graph.edge_count

        result = simplifier.simplify(apply=False)

        assert graph.edge_count == original_edges
        assert result.edges_removed > 0

    def test_complexity_score(self, graph: GraphEngine) -> None:
        """Test complexity score computation."""
        simplifier = GraphSimplifier(graph)
        score = simplifier.get_complexity_score()

        assert 0.0 <= score <= 1.0

    def test_complexity_score_simple_graph(self) -> None:
        """Test complexity score for simple graph."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(
                id="single",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                config={},
                tags={},
                terraform_name="single",
                original_name="Single",
            )
        )

        simplifier = GraphSimplifier(graph)
        score = simplifier.get_complexity_score()

        # Single node, no edges = low complexity
        assert score < 0.3

    def test_simplification_report(self, graph: GraphEngine) -> None:
        """Test report generation."""
        simplifier = GraphSimplifier(graph)
        report = simplifier.get_simplification_report()

        assert "Graph Simplification Report" in report
        assert "Nodes:" in report
        assert "Edges:" in report
        assert "Transitive Reduction:" in report
        assert "Complexity Score:" in report


class TestGraphStats:
    """Tests for GraphStats dataclass."""

    def test_default_values(self) -> None:
        """Test default values are correct."""
        stats = GraphStats()

        assert stats.node_count == 0
        assert stats.edge_count == 0
        assert stats.density == 0.0
        assert stats.isolated_nodes == []

    def test_custom_values(self) -> None:
        """Test custom value assignment."""
        stats = GraphStats(
            node_count=10,
            edge_count=15,
            density=0.5,
            has_cycles=True,
            cycle_count=2,
        )

        assert stats.node_count == 10
        assert stats.edge_count == 15
        assert stats.has_cycles is True
        assert stats.cycle_count == 2


class TestCyclicGraph:
    """Tests for graphs with cycles."""

    def test_stats_with_cycles(self) -> None:
        """Test statistics computation on cyclic graph."""
        graph = GraphEngine()

        # Create a cycle: A -> B -> C -> A
        for name in ["a", "b", "c"]:
            graph.add_resource(
                ResourceNode(
                    id=name,
                    resource_type=ResourceType.SECURITY_GROUP,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=name,
                    original_name=name.upper(),
                )
            )

        graph.add_dependency("a", "b")
        graph.add_dependency("b", "c")
        graph.add_dependency("c", "a")

        simplifier = GraphSimplifier(graph)
        stats = simplifier.compute_stats()

        assert stats.has_cycles is True
        assert stats.cycle_count >= 1

    def test_complexity_score_with_cycles(self) -> None:
        """Test that cycles increase complexity score."""
        # Graph without cycles
        graph1 = GraphEngine()
        for name in ["a", "b", "c"]:
            graph1.add_resource(
                ResourceNode(
                    id=name,
                    resource_type=ResourceType.VPC,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=name,
                    original_name=name.upper(),
                )
            )
        graph1.add_dependency("a", "b")
        graph1.add_dependency("b", "c")

        # Graph with cycles
        graph2 = GraphEngine()
        for name in ["a", "b", "c"]:
            graph2.add_resource(
                ResourceNode(
                    id=name,
                    resource_type=ResourceType.VPC,
                    region="us-east-1",
                    config={},
                    tags={},
                    terraform_name=name,
                    original_name=name.upper(),
                )
            )
        graph2.add_dependency("a", "b")
        graph2.add_dependency("b", "c")
        graph2.add_dependency("c", "a")

        simplifier1 = GraphSimplifier(graph1)
        simplifier2 = GraphSimplifier(graph2)

        # Cyclic graph should have higher complexity
        assert simplifier2.get_complexity_score() > simplifier1.get_complexity_score()
