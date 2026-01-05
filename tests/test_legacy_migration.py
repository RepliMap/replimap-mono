"""
Tests for migrated legacy features (Prompt 3.7.1).

Tests cover:
- Topological sorting
- Cycle detection
- Strongly connected components
- Recursive dependencies (SQL CTE)
- Safe apply/destroy ordering
- Graph merging
- Centrality metrics
- Node removal
"""

from __future__ import annotations

import pytest

from replimap.core.unified_storage import Edge, Node, UnifiedGraphEngine


class TestTopologicalSort:
    """Test topological sorting."""

    def test_simple_chain(self) -> None:
        """VPC -> Subnet -> Instance chain sorts correctly."""
        engine = UnifiedGraphEngine()

        # VPC must be created first, then Subnet, then Instance
        engine.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="subnet", type="aws_subnet"),
                Node(id="instance", type="aws_instance"),
            ]
        )
        # Instance depends on Subnet, Subnet depends on VPC
        engine.add_edges(
            [
                Edge(source_id="instance", target_id="subnet", relation="in"),
                Edge(source_id="subnet", target_id="vpc", relation="in"),
            ]
        )

        order = engine.topological_sort()

        # VPC must come before Subnet, Subnet before Instance
        assert order.index("vpc") < order.index("subnet")
        assert order.index("subnet") < order.index("instance")

        engine.close()

    def test_diamond_dependency(self) -> None:
        """Diamond pattern: A depends on B and C, both depend on D."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="A", type="t"),
                Node(id="B", type="t"),
                Node(id="C", type="t"),
                Node(id="D", type="t"),
            ]
        )
        engine.add_edges(
            [
                Edge(source_id="A", target_id="B", relation="r"),
                Edge(source_id="A", target_id="C", relation="r"),
                Edge(source_id="B", target_id="D", relation="r"),
                Edge(source_id="C", target_id="D", relation="r"),
            ]
        )

        order = engine.topological_sort()

        # D must come before B and C, B and C before A
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")

        engine.close()

    def test_cycle_raises_error(self) -> None:
        """Cyclic graph raises ValueError."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="A", type="t"),
                Node(id="B", type="t"),
                Node(id="C", type="t"),
            ]
        )
        # A -> B -> C -> A (cycle)
        engine.add_edges(
            [
                Edge(source_id="A", target_id="B", relation="r"),
                Edge(source_id="B", target_id="C", relation="r"),
                Edge(source_id="C", target_id="A", relation="r"),
            ]
        )

        assert engine.has_cycles()
        assert len(engine.find_cycles()) > 0

        with pytest.raises(ValueError, match="cycles"):
            engine.topological_sort()

        engine.close()


class TestCycleDetection:
    """Test cycle detection methods."""

    def test_no_cycles(self) -> None:
        """DAG has no cycles."""
        engine = UnifiedGraphEngine()

        engine.add_nodes([Node(id="a", type="t"), Node(id="b", type="t")])
        engine.add_edge(Edge(source_id="a", target_id="b", relation="r"))

        assert not engine.has_cycles()
        assert engine.find_cycles() == []

        engine.close()

    def test_self_loop(self) -> None:
        """Self-loop is detected as cycle."""
        engine = UnifiedGraphEngine()

        engine.add_node(Node(id="a", type="t"))
        engine.add_edge(Edge(source_id="a", target_id="a", relation="self"))

        assert engine.has_cycles()
        cycles = engine.find_cycles()
        assert len(cycles) >= 1

        engine.close()

    def test_multiple_cycles(self) -> None:
        """Multiple cycles are detected."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="a", type="t"),
                Node(id="b", type="t"),
                Node(id="c", type="t"),
                Node(id="d", type="t"),
            ]
        )
        # Cycle 1: a -> b -> a
        # Cycle 2: c -> d -> c
        engine.add_edges(
            [
                Edge(source_id="a", target_id="b", relation="r"),
                Edge(source_id="b", target_id="a", relation="r"),
                Edge(source_id="c", target_id="d", relation="r"),
                Edge(source_id="d", target_id="c", relation="r"),
            ]
        )

        assert engine.has_cycles()
        cycles = engine.find_cycles(limit=10)
        assert len(cycles) >= 2

        engine.close()


class TestDependencies:
    """Test dependency queries with correct edge semantics."""

    @pytest.fixture
    def engine(self) -> UnifiedGraphEngine:
        """Create engine with standard test graph."""
        e = UnifiedGraphEngine()

        # Edge semantics: source DEPENDS ON target
        # Instance depends on SG, SG depends on VPC
        e.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="sg", type="aws_security_group"),
                Node(id="instance", type="aws_instance"),
            ]
        )
        e.add_edges(
            [
                Edge(source_id="sg", target_id="vpc", relation="in_vpc"),
                Edge(source_id="instance", target_id="sg", relation="uses"),
            ]
        )
        return e

    def test_get_dependencies_direct(self, engine: UnifiedGraphEngine) -> None:
        """Direct dependencies are correct."""
        # Instance depends on SG (direct)
        direct = engine.get_dependencies("instance", recursive=False)
        assert len(direct) == 1
        assert direct[0].id == "sg"

        engine.close()

    def test_get_dependencies_recursive(self, engine: UnifiedGraphEngine) -> None:
        """Recursive dependencies include transitive deps."""
        # Instance depends on SG and VPC (recursive)
        recursive = engine.get_dependencies("instance", recursive=True)
        dep_ids = {d.id for d in recursive}
        assert dep_ids == {"sg", "vpc"}

        engine.close()

    def test_get_dependents_direct(self, engine: UnifiedGraphEngine) -> None:
        """Direct dependents are correct."""
        # What directly depends on SG? Only Instance
        direct = engine.get_dependents("sg", recursive=False)
        assert len(direct) == 1
        assert direct[0].id == "instance"

        engine.close()

    def test_get_dependents_recursive(self, engine: UnifiedGraphEngine) -> None:
        """Recursive dependents include transitive deps."""
        # What depends on VPC? SG directly, Instance transitively
        dependents = engine.get_dependents("vpc", recursive=True)
        dep_ids = {d.id for d in dependents}
        assert dep_ids == {"sg", "instance"}

        engine.close()

    def test_no_dependencies(self, engine: UnifiedGraphEngine) -> None:
        """VPC has no dependencies (it's a root)."""
        deps = engine.get_dependencies("vpc", recursive=True)
        assert len(deps) == 0

        engine.close()

    def test_no_dependents(self, engine: UnifiedGraphEngine) -> None:
        """Instance has no dependents (it's a leaf)."""
        deps = engine.get_dependents("instance", recursive=True)
        assert len(deps) == 0

        engine.close()


class TestSafeOrdering:
    """Test Terraform apply/destroy ordering."""

    def test_safe_apply_order(self) -> None:
        """Apply order: dependencies before dependents."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="subnet", type="aws_subnet"),
            ]
        )
        # Subnet depends on VPC
        engine.add_edge(Edge(source_id="subnet", target_id="vpc", relation="in"))

        order = engine.safe_apply_order()

        # VPC must be created BEFORE Subnet
        assert order.index("vpc") < order.index("subnet")

        engine.close()

    def test_safe_destroy_order(self) -> None:
        """Destroy order: dependents before dependencies."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="subnet", type="aws_subnet"),
            ]
        )
        engine.add_edge(Edge(source_id="subnet", target_id="vpc", relation="in"))

        order = engine.safe_destroy_order()

        # Subnet must be destroyed BEFORE VPC
        assert order.index("subnet") < order.index("vpc")

        engine.close()


class TestStronglyConnectedComponents:
    """Test SCC detection."""

    def test_dag_all_singletons(self) -> None:
        """DAG has all singleton SCCs."""
        engine = UnifiedGraphEngine()

        engine.add_nodes([Node(id="a", type="t"), Node(id="b", type="t")])
        engine.add_edge(Edge(source_id="a", target_id="b", relation="r"))

        sccs = engine.strongly_connected_components()

        # Each node is its own SCC (no cycles)
        assert len(sccs) == 2
        assert all(len(scc) == 1 for scc in sccs)

        engine.close()

    def test_cycle_forms_scc(self) -> None:
        """Cycle forms single SCC."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [Node(id="a", type="t"), Node(id="b", type="t"), Node(id="c", type="t")]
        )
        # a -> b -> c -> a (cycle)
        engine.add_edges(
            [
                Edge(source_id="a", target_id="b", relation="r"),
                Edge(source_id="b", target_id="c", relation="r"),
                Edge(source_id="c", target_id="a", relation="r"),
            ]
        )

        sccs = engine.strongly_connected_components()
        largest = engine.get_largest_scc()

        # All three nodes form one SCC
        assert {"a", "b", "c"} in sccs or largest == {"a", "b", "c"}

        engine.close()


class TestMerge:
    """Test graph merging with batch operations."""

    def test_merge_uses_batch(self) -> None:
        """Merge adds nodes and edges efficiently."""
        engine1 = UnifiedGraphEngine()
        engine2 = UnifiedGraphEngine()

        engine1.add_nodes([Node(id=f"e1-{i}", type="t") for i in range(100)])
        engine2.add_nodes([Node(id=f"e2-{i}", type="t") for i in range(100)])

        nodes_added, _ = engine1.merge_from(engine2)

        assert nodes_added == 100
        assert engine1.node_count() == 200

        engine1.close()
        engine2.close()

    def test_merge_includes_edges(self) -> None:
        """Merge includes edges from other graph."""
        engine1 = UnifiedGraphEngine()
        engine2 = UnifiedGraphEngine()

        engine2.add_nodes([Node(id="a", type="t"), Node(id="b", type="t")])
        engine2.add_edge(Edge(source_id="a", target_id="b", relation="r"))

        engine1.merge_from(engine2)

        assert engine1.node_count() == 2
        assert engine1.edge_count() == 1

        engine1.close()
        engine2.close()


class TestCentrality:
    """Test centrality metrics."""

    def test_hub_has_highest_degree(self) -> None:
        """Hub node has highest degree centrality."""
        engine = UnifiedGraphEngine()

        engine.add_node(Node(id="hub", type="t"))
        for i in range(10):
            engine.add_node(Node(id=f"spoke-{i}", type="t"))
            # All spokes depend on hub
            engine.add_edge(
                Edge(source_id=f"spoke-{i}", target_id="hub", relation="uses")
            )

        centrality = engine.get_centrality("degree")

        # Hub should have highest degree
        assert centrality["hub"] == max(centrality.values())

        engine.close()

    def test_pagerank_identifies_important(self) -> None:
        """PageRank identifies important nodes (or degree if numpy unavailable)."""
        engine = UnifiedGraphEngine()

        engine.add_node(Node(id="hub", type="t"))
        for i in range(5):
            engine.add_node(Node(id=f"spoke-{i}", type="t"))
            engine.add_edge(
                Edge(source_id=f"spoke-{i}", target_id="hub", relation="uses")
            )

        # PageRank requires numpy, fall back to degree if unavailable
        try:
            critical = engine.get_most_critical_resources(top_n=1, algorithm="pagerank")
        except ModuleNotFoundError:
            # numpy not installed, use degree centrality instead
            critical = engine.get_most_critical_resources(top_n=1, algorithm="degree")

        assert len(critical) == 1
        assert critical[0][0].id == "hub"

        engine.close()

    def test_invalid_algorithm_raises(self) -> None:
        """Invalid algorithm raises ValueError."""
        engine = UnifiedGraphEngine()
        engine.add_node(Node(id="a", type="t"))

        with pytest.raises(ValueError, match="Unknown algorithm"):
            engine.get_centrality("invalid")

        engine.close()


class TestSubgraph:
    """Test subgraph extraction."""

    def test_extract_subgraph(self) -> None:
        """Subgraph contains only specified nodes."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="a", type="t"),
                Node(id="b", type="t"),
                Node(id="c", type="t"),
            ]
        )
        engine.add_edges(
            [
                Edge(source_id="a", target_id="b", relation="r"),
                Edge(source_id="b", target_id="c", relation="r"),
            ]
        )

        nodes, edges = engine.get_subgraph({"a", "b"})

        assert len(nodes) == 2
        assert {n.id for n in nodes} == {"a", "b"}
        # Only edge a->b should be included
        assert len(edges) == 1
        assert edges[0].source_id == "a"
        assert edges[0].target_id == "b"

        engine.close()

    def test_connected_subgraph(self) -> None:
        """Connected subgraph includes deps and dependents."""
        engine = UnifiedGraphEngine()

        engine.add_nodes(
            [
                Node(id="vpc", type="aws_vpc"),
                Node(id="subnet", type="aws_subnet"),
                Node(id="instance", type="aws_instance"),
                Node(id="other", type="aws_instance"),  # Not connected
            ]
        )
        engine.add_edges(
            [
                Edge(source_id="subnet", target_id="vpc", relation="in"),
                Edge(source_id="instance", target_id="subnet", relation="in"),
            ]
        )

        nodes, edges = engine.get_connected_subgraph("subnet", max_depth=3)

        node_ids = {n.id for n in nodes}
        # Should include subnet, its dependency (vpc), and its dependent (instance)
        assert "subnet" in node_ids
        assert "vpc" in node_ids
        assert "instance" in node_ids
        # Should NOT include unconnected node
        assert "other" not in node_ids

        engine.close()


class TestNodeRemoval:
    """Test node removal."""

    def test_remove_existing_node(self) -> None:
        """Removing existing node returns True."""
        engine = UnifiedGraphEngine()

        engine.add_node(Node(id="a", type="t"))
        assert engine.node_count() == 1

        result = engine.remove_node("a")

        assert result is True
        assert engine.node_count() == 0
        assert engine.get_node("a") is None

        engine.close()

    def test_remove_nonexistent_node(self) -> None:
        """Removing nonexistent node returns False."""
        engine = UnifiedGraphEngine()

        result = engine.remove_node("nonexistent")

        assert result is False

        engine.close()

    def test_remove_node_cascades_edges(self) -> None:
        """Removing node cascades to remove edges."""
        engine = UnifiedGraphEngine()

        engine.add_nodes([Node(id="a", type="t"), Node(id="b", type="t")])
        engine.add_edge(Edge(source_id="a", target_id="b", relation="r"))

        assert engine.edge_count() == 1

        engine.remove_node("a")

        assert engine.edge_count() == 0

        engine.close()
