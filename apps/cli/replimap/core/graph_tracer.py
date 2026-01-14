"""
Graph Tracer for debugging RepliMap's graph processing pipeline.

This module provides tracing capabilities to export intermediate graph states
during the processing lifecycle. Useful for debugging complex topology issues.

Usage:
    from replimap.core.graph_tracer import GraphTracer, GraphPhase

    tracer = GraphTracer(output_dir=Path("./debug"))
    tracer.snapshot(GraphPhase.DISCOVERY, graph)
    tracer.snapshot(GraphPhase.LINKING, graph)

    # Get diff between phases
    diff = tracer.diff(GraphPhase.DISCOVERY, GraphPhase.LINKING)

    # Export summary
    tracer.export_summary()

Supported export formats:
    - .graphml (for Gephi, Cytoscape)
    - .json (for programmatic analysis)
    - .diff.json (phase-to-phase changes)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine


class GraphPhase(str, Enum):
    """Phases in the graph processing lifecycle."""

    DISCOVERY = "1_discovery"
    LINKING = "2_linking"
    PHANTOM_RESOLUTION = "3_phantom"
    SANITIZATION = "4_sanitization"
    OPTIMIZATION = "5_optimization"
    VARIABLE_INJECTION = "6_variables"
    FINAL = "7_final"


@dataclass
class GraphSnapshot:
    """A point-in-time snapshot of the graph."""

    phase: GraphPhase
    timestamp: str
    node_count: int
    edge_count: int
    phantom_count: int
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase.value,
            "timestamp": self.timestamp,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "phantom_count": self.phantom_count,
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": self.metadata,
        }


@dataclass
class GraphDiff:
    """Difference between two graph snapshots."""

    from_phase: GraphPhase
    to_phase: GraphPhase
    nodes_added: list[str]
    nodes_removed: list[str]
    edges_added: list[tuple[str, str, str]]  # (source, target, type)
    edges_removed: list[tuple[str, str, str]]
    attributes_changed: dict[str, dict[str, Any]]  # node_id -> {attr: (old, new)}

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_phase": self.from_phase.value,
            "to_phase": self.to_phase.value,
            "nodes_added": self.nodes_added,
            "nodes_removed": self.nodes_removed,
            "nodes_added_count": len(self.nodes_added),
            "nodes_removed_count": len(self.nodes_removed),
            "edges_added": [
                {"source": s, "target": t, "type": ty} for s, t, ty in self.edges_added
            ],
            "edges_removed": [
                {"source": s, "target": t, "type": ty}
                for s, t, ty in self.edges_removed
            ],
            "edges_added_count": len(self.edges_added),
            "edges_removed_count": len(self.edges_removed),
            "attributes_changed": self.attributes_changed,
        }

    @property
    def has_changes(self) -> bool:
        return bool(
            self.nodes_added
            or self.nodes_removed
            or self.edges_added
            or self.edges_removed
            or self.attributes_changed
        )


class GraphTracer:
    """
    Traces graph state through processing phases.

    Enabled via --trace-graph CLI flag. When disabled, all methods are no-ops.
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the graph tracer.

        Args:
            output_dir: Directory to write trace files. If None, uses ./replimap_trace
            enabled: If False, all operations are no-ops (for production)
        """
        self.enabled = enabled
        self.output_dir = output_dir or Path("./replimap_trace")
        self.snapshots: dict[GraphPhase, GraphSnapshot] = {}
        self.start_time = datetime.now(UTC)

        if self.enabled:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(
        self,
        phase: GraphPhase,
        graph: GraphEngine,
        metadata: dict[str, Any] | None = None,
    ) -> GraphSnapshot | None:
        """
        Take a snapshot of the current graph state.

        Args:
            phase: The current processing phase
            graph: The GraphEngine instance to snapshot
            metadata: Optional additional metadata to include

        Returns:
            The created snapshot, or None if tracing is disabled
        """
        if not self.enabled:
            return None

        # Extract nodes
        nodes = []
        phantom_count = 0
        for node_id in graph.nodes():
            node = graph.get_node(node_id)
            if node:
                node_data = {
                    "id": node.id,
                    "resource_type": node.resource_type.value
                    if hasattr(node.resource_type, "value")
                    else str(node.resource_type),
                    "name": node.name,
                    "is_phantom": getattr(node, "is_phantom", False),
                }
                if getattr(node, "is_phantom", False):
                    phantom_count += 1
                    node_data["phantom_reason"] = getattr(node, "phantom_reason", "")
                nodes.append(node_data)

        # Extract edges
        edges = []
        for source, target, data in graph._graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "type": data.get("dependency_type", "unknown"),
                    "label": data.get("label", ""),
                }
            )

        snapshot = GraphSnapshot(
            phase=phase,
            timestamp=datetime.now(UTC).isoformat(),
            node_count=len(nodes),
            edge_count=len(edges),
            phantom_count=phantom_count,
            nodes=nodes,
            edges=edges,
            metadata=metadata or {},
        )

        self.snapshots[phase] = snapshot

        # Auto-export
        self._export_snapshot(snapshot)

        return snapshot

    def diff(
        self,
        from_phase: GraphPhase,
        to_phase: GraphPhase,
    ) -> GraphDiff | None:
        """
        Calculate the difference between two snapshots.

        Args:
            from_phase: The earlier phase
            to_phase: The later phase

        Returns:
            A GraphDiff object, or None if either snapshot doesn't exist
        """
        if not self.enabled:
            return None

        from_snap = self.snapshots.get(from_phase)
        to_snap = self.snapshots.get(to_phase)

        if not from_snap or not to_snap:
            return None

        # Calculate node diffs
        from_node_ids = {n["id"] for n in from_snap.nodes}
        to_node_ids = {n["id"] for n in to_snap.nodes}

        nodes_added = list(to_node_ids - from_node_ids)
        nodes_removed = list(from_node_ids - to_node_ids)

        # Calculate edge diffs
        from_edges = {(e["source"], e["target"], e["type"]) for e in from_snap.edges}
        to_edges = {(e["source"], e["target"], e["type"]) for e in to_snap.edges}

        edges_added = list(to_edges - from_edges)
        edges_removed = list(from_edges - to_edges)

        # Calculate attribute changes (simplified - just track existence)
        attributes_changed: dict[str, dict[str, Any]] = {}

        diff = GraphDiff(
            from_phase=from_phase,
            to_phase=to_phase,
            nodes_added=nodes_added,
            nodes_removed=nodes_removed,
            edges_added=edges_added,
            edges_removed=edges_removed,
            attributes_changed=attributes_changed,
        )

        # Auto-export
        self._export_diff(diff)

        return diff

    def _export_snapshot(self, snapshot: GraphSnapshot) -> None:
        """Export a snapshot to files."""
        base_name = f"graph_{snapshot.phase.value}"

        # Export JSON
        json_path = self.output_dir / f"{base_name}.json"
        json_path.write_text(json.dumps(snapshot.to_dict(), indent=2, default=str))

        # Export GraphML for Gephi/Cytoscape
        graphml_path = self.output_dir / f"{base_name}.graphml"
        self._export_graphml(snapshot, graphml_path)

    def _export_diff(self, diff: GraphDiff) -> None:
        """Export a diff to file."""
        diff_path = (
            self.output_dir
            / f"diff_{diff.from_phase.value}_to_{diff.to_phase.value}.json"
        )
        diff_path.write_text(json.dumps(diff.to_dict(), indent=2, default=str))

    def _export_graphml(self, snapshot: GraphSnapshot, path: Path) -> None:
        """Export snapshot as GraphML format."""
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
            '  <key id="resource_type" for="node" attr.name="resource_type" attr.type="string"/>',
            '  <key id="name" for="node" attr.name="name" attr.type="string"/>',
            '  <key id="is_phantom" for="node" attr.name="is_phantom" attr.type="boolean"/>',
            '  <key id="edge_type" for="edge" attr.name="type" attr.type="string"/>',
            '  <graph id="G" edgedefault="directed">',
        ]

        # Add nodes
        for node in snapshot.nodes:
            node_id = node["id"].replace("&", "&amp;").replace("<", "&lt;")
            name = (node.get("name") or "").replace("&", "&amp;").replace("<", "&lt;")
            rtype = node.get("resource_type", "unknown")
            is_phantom = str(node.get("is_phantom", False)).lower()

            lines.append(f'    <node id="{node_id}">')
            lines.append(f'      <data key="resource_type">{rtype}</data>')
            lines.append(f'      <data key="name">{name}</data>')
            lines.append(f'      <data key="is_phantom">{is_phantom}</data>')
            lines.append("    </node>")

        # Add edges
        for i, edge in enumerate(snapshot.edges):
            source = edge["source"].replace("&", "&amp;").replace("<", "&lt;")
            target = edge["target"].replace("&", "&amp;").replace("<", "&lt;")
            etype = edge.get("type", "dependency")

            lines.append(f'    <edge id="e{i}" source="{source}" target="{target}">')
            lines.append(f'      <data key="edge_type">{etype}</data>')
            lines.append("    </edge>")

        lines.append("  </graph>")
        lines.append("</graphml>")

        path.write_text("\n".join(lines))

    def export_summary(self) -> Path | None:
        """
        Export a summary of all snapshots and diffs.

        Returns:
            Path to the summary file
        """
        if not self.enabled or not self.snapshots:
            return None

        summary = {
            "trace_start": self.start_time.isoformat(),
            "trace_end": datetime.now(UTC).isoformat(),
            "phases_captured": [p.value for p in self.snapshots.keys()],
            "snapshots": {},
            "progression": [],
        }

        # Add snapshot summaries
        for phase, snapshot in sorted(self.snapshots.items(), key=lambda x: x[0].value):
            summary["snapshots"][phase.value] = {
                "timestamp": snapshot.timestamp,
                "node_count": snapshot.node_count,
                "edge_count": snapshot.edge_count,
                "phantom_count": snapshot.phantom_count,
            }

        # Calculate progression between consecutive phases
        phases = sorted(self.snapshots.keys(), key=lambda x: x.value)
        for i in range(len(phases) - 1):
            from_phase = phases[i]
            to_phase = phases[i + 1]
            diff = self.diff(from_phase, to_phase)
            if diff:
                summary["progression"].append(
                    {
                        "from": from_phase.value,
                        "to": to_phase.value,
                        "nodes_added": len(diff.nodes_added),
                        "nodes_removed": len(diff.nodes_removed),
                        "edges_added": len(diff.edges_added),
                        "edges_removed": len(diff.edges_removed),
                    }
                )

        summary_path = self.output_dir / "trace_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2, default=str))

        return summary_path

    def get_snapshot(self, phase: GraphPhase) -> GraphSnapshot | None:
        """Get a previously captured snapshot."""
        return self.snapshots.get(phase)

    def clear(self) -> None:
        """Clear all captured snapshots."""
        self.snapshots.clear()


# Singleton for global access
_global_tracer: GraphTracer | None = None


def get_tracer() -> GraphTracer | None:
    """Get the global tracer instance."""
    return _global_tracer


def init_tracer(output_dir: Path | None = None, enabled: bool = True) -> GraphTracer:
    """Initialize and return the global tracer."""
    global _global_tracer
    _global_tracer = GraphTracer(output_dir=output_dir, enabled=enabled)
    return _global_tracer
