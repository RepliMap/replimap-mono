"""
D3.js Interactive HTML Formatter.

Generates an interactive force-directed graph visualization using D3.js.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from jinja2 import Environment, PackageLoader, select_autoescape

if TYPE_CHECKING:
    from replimap.graph.visualizer import VisualizationGraph


class D3Formatter:
    """
    Formats a VisualizationGraph as an interactive HTML page with D3.js.

    Features:
    - Force-directed graph layout
    - Drag and drop nodes
    - Zoom and pan
    - Click to highlight connections
    - Filter by resource type
    - Search functionality
    """

    def __init__(self) -> None:
        """Initialize the formatter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("replimap.graph", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def format(self, graph: VisualizationGraph) -> str:
        """
        Format the graph as an interactive HTML page.

        Args:
            graph: The visualization graph to format

        Returns:
            HTML content as a string
        """
        # Prepare graph data for D3.js
        graph_data = self._prepare_graph_data(graph)

        # Get unique groups for filter controls
        groups = sorted({node.group for node in graph.nodes})

        # Get unique resource types
        resource_types = sorted({node.resource_type for node in graph.nodes})

        # Render template
        template = self.env.get_template("graph.html.j2")
        return template.render(
            graph_data=json.dumps(graph_data),
            metadata=graph.metadata,
            groups=groups,
            resource_types=resource_types,
            node_count=len(graph.nodes),
            edge_count=len(graph.edges),
        )

    def _prepare_graph_data(self, graph: VisualizationGraph) -> dict:
        """
        Prepare graph data in D3.js-compatible format.

        D3.js force simulation expects:
        - nodes: array of {id, ...}
        - links: array of {source, target, ...}
        """
        return {
            "nodes": [
                {
                    "id": node.id,
                    "type": node.resource_type,
                    "name": node.name,
                    "icon": node.icon,
                    "color": node.color,
                    "group": node.group,
                    "properties": node.properties,
                }
                for node in graph.nodes
            ],
            "links": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "label": edge.label,
                    "type": edge.edge_type,
                }
                for edge in graph.edges
            ],
        }
