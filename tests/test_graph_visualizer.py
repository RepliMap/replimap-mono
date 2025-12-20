"""
Comprehensive tests for the Graph Visualizer feature.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from replimap.graph import (
    GraphEdge,
    GraphNode,
    GraphVisualizer,
    OutputFormat,
    VisualizationGraph,
)
from replimap.graph.formatters import D3Formatter, JSONFormatter, MermaidFormatter


class TestGraphModels:
    """Tests for graph data models."""

    def test_graph_node_creation(self):
        """Test GraphNode dataclass creation."""
        node = GraphNode(
            id="vpc-123",
            resource_type="aws_vpc",
            name="production-vpc",
            properties={"cidr_block": "10.0.0.0/16"},
            icon="VPC",
            color="#10b981",
            group="network",
        )

        assert node.id == "vpc-123"
        assert node.resource_type == "aws_vpc"
        assert node.name == "production-vpc"
        assert node.properties["cidr_block"] == "10.0.0.0/16"
        assert node.icon == "VPC"
        assert node.color == "#10b981"
        assert node.group == "network"

    def test_graph_node_defaults(self):
        """Test GraphNode with default values."""
        node = GraphNode(
            id="sg-456",
            resource_type="aws_security_group",
            name="web-sg",
        )

        assert node.properties == {}
        assert node.icon == ""
        assert node.color == "#6366f1"  # Default indigo color
        assert node.group == "other"  # Default group

    def test_graph_edge_creation(self):
        """Test GraphEdge dataclass creation."""
        edge = GraphEdge(
            source="subnet-456",
            target="vpc-123",
            label="vpc_id",
            edge_type="dependency",
        )

        assert edge.source == "subnet-456"
        assert edge.target == "vpc-123"
        assert edge.label == "vpc_id"
        assert edge.edge_type == "dependency"

    def test_graph_edge_defaults(self):
        """Test GraphEdge with default values."""
        edge = GraphEdge(source="a", target="b")

        assert edge.label == ""
        assert edge.edge_type == "dependency"  # Default edge type

    def test_visualization_graph_creation(self):
        """Test VisualizationGraph dataclass."""
        nodes = [
            GraphNode(id="vpc-1", resource_type="aws_vpc", name="vpc"),
            GraphNode(id="subnet-1", resource_type="aws_subnet", name="subnet"),
        ]
        edges = [GraphEdge(source="subnet-1", target="vpc-1")]
        metadata = {"region": "us-east-1"}

        graph = VisualizationGraph(nodes=nodes, edges=edges, metadata=metadata)

        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1
        assert graph.metadata["region"] == "us-east-1"


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_output_format_values(self):
        """Test OutputFormat enum values."""
        assert OutputFormat.MERMAID.value == "mermaid"
        assert OutputFormat.HTML.value == "html"
        assert OutputFormat.JSON.value == "json"

    def test_output_format_from_string(self):
        """Test creating OutputFormat from string."""
        assert OutputFormat("mermaid") == OutputFormat.MERMAID
        assert OutputFormat("html") == OutputFormat.HTML
        assert OutputFormat("json") == OutputFormat.JSON

    def test_output_format_invalid(self):
        """Test invalid OutputFormat raises ValueError."""
        with pytest.raises(ValueError):
            OutputFormat("invalid")


class TestMermaidFormatter:
    """Tests for MermaidFormatter."""

    def create_sample_graph(self) -> VisualizationGraph:
        """Create a sample graph for testing."""
        nodes = [
            GraphNode(
                id="vpc-123",
                resource_type="aws_vpc",
                name="production-vpc",
                properties={"cidr_block": "10.0.0.0/16"},
                icon="VPC",
                color="#10b981",
                group="network",
            ),
            GraphNode(
                id="subnet-456",
                resource_type="aws_subnet",
                name="public-subnet",
                properties={},
                icon="SUB",
                color="#34d399",
                group="network",
            ),
            GraphNode(
                id="i-789",
                resource_type="aws_instance",
                name="web-server",
                properties={"instance_type": "t3.micro"},
                icon="EC2",
                color="#6366f1",
                group="compute",
            ),
        ]
        edges = [
            GraphEdge(source="subnet-456", target="vpc-123", label="vpc_id"),
            GraphEdge(source="i-789", target="subnet-456", label="subnet_id"),
        ]
        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata={"region": "us-east-1", "resource_count": 3, "edge_count": 2},
        )

    def test_mermaid_formatter_output(self):
        """Test MermaidFormatter generates valid output."""
        formatter = MermaidFormatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)

        # Check structure
        assert "```mermaid" in output
        assert "flowchart TB" in output
        # Mermaid block is closed somewhere in the output
        assert output.count("```") >= 2  # Opening and closing

        # Check subgraphs
        assert "subgraph network" in output.lower() or "Network Resources" in output
        assert "subgraph compute" in output.lower() or "Compute Resources" in output

        # Check nodes
        assert "vpc_123" in output or "vpc-123" in output.replace("-", "_")
        assert "VPC" in output

        # Check edges
        assert "-->" in output
        assert "vpc_id" in output

    def test_mermaid_formatter_empty_graph(self):
        """Test MermaidFormatter with empty graph."""
        formatter = MermaidFormatter()
        graph = VisualizationGraph(nodes=[], edges=[], metadata={})

        output = formatter.format(graph)

        assert "```mermaid" in output
        assert "flowchart TB" in output

    def test_mermaid_sanitize_id(self):
        """Test MermaidFormatter sanitizes node IDs correctly."""
        formatter = MermaidFormatter()

        # Test hyphen replacement
        assert formatter._sanitize_id("vpc-123") == "vpc_123"

        # Test special character removal
        assert formatter._sanitize_id("sg/web@prod") == "sgwebprod"

        # Test numeric prefix
        assert formatter._sanitize_id("123abc") == "n123abc"


class TestJSONFormatter:
    """Tests for JSONFormatter."""

    def create_sample_graph(self) -> VisualizationGraph:
        """Create a sample graph for testing."""
        nodes = [
            GraphNode(
                id="vpc-123",
                resource_type="aws_vpc",
                name="production-vpc",
                properties={"cidr_block": "10.0.0.0/16"},
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        edges = []
        return VisualizationGraph(
            nodes=nodes, edges=edges, metadata={"region": "us-east-1"}
        )

    def test_json_formatter_output(self):
        """Test JSONFormatter generates valid JSON."""
        formatter = JSONFormatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)
        data = json.loads(output)

        assert "version" in data
        assert "generated_at" in data
        assert "metadata" in data
        assert "statistics" in data
        assert "nodes" in data
        assert "edges" in data

    def test_json_formatter_statistics(self):
        """Test JSONFormatter includes correct statistics."""
        formatter = JSONFormatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)
        data = json.loads(output)

        assert data["statistics"]["total_nodes"] == 1
        assert data["statistics"]["total_edges"] == 0
        assert "nodes_by_group" in data["statistics"]
        assert "nodes_by_type" in data["statistics"]

    def test_json_formatter_node_structure(self):
        """Test JSONFormatter node structure."""
        formatter = JSONFormatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)
        data = json.loads(output)

        node = data["nodes"][0]
        assert node["id"] == "vpc-123"
        assert node["type"] == "aws_vpc"
        assert node["name"] == "production-vpc"
        assert node["group"] == "network"
        assert "visual" in node
        assert node["visual"]["icon"] == "VPC"
        assert node["visual"]["color"] == "#10b981"


class TestD3Formatter:
    """Tests for D3Formatter."""

    def create_sample_graph(self) -> VisualizationGraph:
        """Create a sample graph for testing."""
        nodes = [
            GraphNode(
                id="vpc-123",
                resource_type="aws_vpc",
                name="production-vpc",
                properties={},
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        edges = []
        return VisualizationGraph(
            nodes=nodes, edges=edges, metadata={"region": "us-east-1"}
        )

    def test_d3_formatter_output(self):
        """Test D3Formatter generates valid HTML."""
        formatter = D3Formatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)

        # Check HTML structure
        assert "<!DOCTYPE html>" in output
        assert "<html" in output
        assert "</html>" in output

        # Check D3.js inclusion
        assert "d3.v7.min.js" in output

        # Check TailwindCSS inclusion
        assert "tailwindcss" in output

        # Check graph data is embedded
        assert "graphData" in output
        assert "vpc-123" in output

    def test_d3_formatter_includes_controls(self):
        """Test D3Formatter includes UI controls."""
        formatter = D3Formatter()
        graph = self.create_sample_graph()

        output = formatter.format(graph)

        # Check control elements
        assert "search" in output.lower()
        assert "filter" in output.lower()
        assert "zoom" in output.lower()

    def test_d3_formatter_groups_in_filter(self):
        """Test D3Formatter includes groups in filter buttons."""
        formatter = D3Formatter()
        nodes = [
            GraphNode(id="1", resource_type="aws_vpc", name="vpc", group="network"),
            GraphNode(id="2", resource_type="aws_instance", name="ec2", group="compute"),
        ]
        graph = VisualizationGraph(nodes=nodes, edges=[], metadata={})

        output = formatter.format(graph)

        assert "network" in output.lower()
        assert "compute" in output.lower()


class TestGraphVisualizer:
    """Tests for GraphVisualizer class."""

    def test_visualizer_initialization(self):
        """Test GraphVisualizer initialization."""
        mock_session = MagicMock()

        visualizer = GraphVisualizer(
            session=mock_session,
            region="us-east-1",
            profile="prod",
        )

        assert visualizer.session == mock_session
        assert visualizer.region == "us-east-1"
        assert visualizer.profile == "prod"

    def test_resource_visuals_mapping(self):
        """Test RESOURCE_VISUALS contains expected resource types."""
        from replimap.graph.visualizer import RESOURCE_VISUALS

        # Check common resource types
        assert "aws_vpc" in RESOURCE_VISUALS
        assert "aws_subnet" in RESOURCE_VISUALS
        assert "aws_instance" in RESOURCE_VISUALS
        assert "aws_security_group" in RESOURCE_VISUALS
        assert "aws_s3_bucket" in RESOURCE_VISUALS
        assert "aws_db_instance" in RESOURCE_VISUALS

        # Check structure
        vpc_visual = RESOURCE_VISUALS["aws_vpc"]
        assert "icon" in vpc_visual
        assert "color" in vpc_visual
        assert "group" in vpc_visual


class TestGraphVisualizerIntegration:
    """Integration tests for GraphVisualizer."""

    def test_full_workflow_mermaid(self):
        """Test full workflow with Mermaid output."""
        nodes = [
            GraphNode(
                id="vpc-test",
                resource_type="aws_vpc",
                name="test-vpc",
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        graph = VisualizationGraph(nodes=nodes, edges=[], metadata={"region": "test"})

        formatter = MermaidFormatter()
        output = formatter.format(graph)

        assert "mermaid" in output
        assert "VPC" in output

    def test_full_workflow_json_to_file(self):
        """Test writing JSON output to file."""
        nodes = [
            GraphNode(
                id="vpc-test",
                resource_type="aws_vpc",
                name="test-vpc",
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        graph = VisualizationGraph(nodes=nodes, edges=[], metadata={"region": "test"})

        formatter = JSONFormatter()
        output = formatter.format(graph)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            f.write(output)
            temp_path = Path(f.name)

        try:
            # Verify file was written and is valid JSON
            content = temp_path.read_text()
            data = json.loads(content)
            assert data["nodes"][0]["id"] == "vpc-test"
        finally:
            temp_path.unlink()

    def test_full_workflow_html_to_file(self):
        """Test writing HTML output to file."""
        nodes = [
            GraphNode(
                id="vpc-test",
                resource_type="aws_vpc",
                name="test-vpc",
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        graph = VisualizationGraph(nodes=nodes, edges=[], metadata={"region": "test"})

        formatter = D3Formatter()
        output = formatter.format(graph)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False
        ) as f:
            f.write(output)
            temp_path = Path(f.name)

        try:
            content = temp_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "vpc-test" in content
        finally:
            temp_path.unlink()


class TestGraphEdgeCases:
    """Edge case tests for graph visualizer."""

    def test_empty_graph(self):
        """Test handling of empty graph."""
        graph = VisualizationGraph(nodes=[], edges=[], metadata={})

        # All formatters should handle empty graphs
        assert MermaidFormatter().format(graph)
        assert JSONFormatter().format(graph)
        assert D3Formatter().format(graph)

    def test_node_with_special_characters_in_name(self):
        """Test nodes with special characters in names."""
        nodes = [
            GraphNode(
                id="vpc-123",
                resource_type="aws_vpc",
                name="vpc-with-special-chars-@#$%",
                icon="VPC",
                color="#10b981",
                group="network",
            ),
        ]
        graph = VisualizationGraph(nodes=nodes, edges=[], metadata={})

        # Should not raise exceptions
        mermaid_output = MermaidFormatter().format(graph)
        json_output = JSONFormatter().format(graph)
        html_output = D3Formatter().format(graph)

        assert mermaid_output
        assert json.loads(json_output)  # Should be valid JSON
        assert html_output

    def test_circular_dependencies(self):
        """Test graph with circular dependencies."""
        nodes = [
            GraphNode(id="a", resource_type="aws_vpc", name="a", group="network"),
            GraphNode(id="b", resource_type="aws_subnet", name="b", group="network"),
        ]
        edges = [
            GraphEdge(source="a", target="b"),
            GraphEdge(source="b", target="a"),  # Circular
        ]
        graph = VisualizationGraph(nodes=nodes, edges=edges, metadata={})

        # Should handle circular references
        output = MermaidFormatter().format(graph)
        assert "a --> b" in output or "a -->" in output

    def test_large_graph_performance(self):
        """Test handling of larger graphs."""
        # Create 100 nodes with connections
        nodes = [
            GraphNode(
                id=f"node-{i}",
                resource_type="aws_instance",
                name=f"instance-{i}",
                group="compute",
            )
            for i in range(100)
        ]
        edges = [
            GraphEdge(source=f"node-{i}", target=f"node-{i+1}")
            for i in range(99)
        ]
        graph = VisualizationGraph(nodes=nodes, edges=edges, metadata={})

        # Should complete without timeout
        mermaid = MermaidFormatter().format(graph)
        json_out = JSONFormatter().format(graph)

        assert len(mermaid) > 1000
        data = json.loads(json_out)
        assert len(data["nodes"]) == 100
