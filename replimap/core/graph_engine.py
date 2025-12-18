"""
Graph Engine for RepliMap.

The GraphEngine is the core data structure that maintains the dependency
graph of AWS resources. It wraps networkx.DiGraph and provides domain-specific
methods for resource management and traversal.

Thread Safety:
    GraphEngine uses a threading.RLock to protect all mutations.
    This allows safe concurrent access from multiple scanner threads.
"""

from __future__ import annotations

import json
import logging
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import networkx as nx

from .models import DependencyType, ResourceNode, ResourceType

logger = logging.getLogger(__name__)


class GraphEngine:
    """
    Manages the dependency graph of AWS resources.

    Resources are stored as nodes in a directed graph, with edges representing
    dependencies. The direction of edges indicates "depends on" relationship:
    if A -> B, then A depends on B (B must exist before A).

    This enables:
    - Topological sorting for correct Terraform ordering
    - Dependency analysis for impact assessment
    - Resource grouping by type for organized output
    """

    def __init__(self) -> None:
        """Initialize an empty graph."""
        self._graph: nx.DiGraph = nx.DiGraph()
        self._resources: dict[str, ResourceNode] = {}
        self._lock: threading.RLock = threading.RLock()

    @property
    def node_count(self) -> int:
        """Number of resources in the graph."""
        return self._graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        """Number of dependencies in the graph."""
        return self._graph.number_of_edges()

    def add_resource(self, node: ResourceNode) -> None:
        """
        Add a resource node to the graph.

        If a resource with the same ID already exists, it will be updated.
        Thread-safe: uses internal lock for concurrent access.

        Args:
            node: The ResourceNode to add
        """
        with self._lock:
            self._resources[node.id] = node
            self._graph.add_node(
                node.id,
                resource_type=str(node.resource_type),
                terraform_name=node.terraform_name,
            )
        logger.debug(f"Added resource: {node.id} ({node.resource_type})")

    def add_dependency(
        self,
        source_id: str,
        target_id: str,
        relation_type: DependencyType = DependencyType.BELONGS_TO,
    ) -> None:
        """
        Add a dependency edge between two resources.

        The direction is: source depends on target.
        In Terraform terms, source must reference target.
        Thread-safe: uses internal lock for concurrent access.

        Args:
            source_id: ID of the dependent resource
            target_id: ID of the resource being depended on
            relation_type: Type of dependency relationship

        Raises:
            ValueError: If either resource doesn't exist in the graph
        """
        with self._lock:
            if source_id not in self._resources:
                raise ValueError(f"Source resource not found: {source_id}")
            if target_id not in self._resources:
                raise ValueError(f"Target resource not found: {target_id}")

            self._graph.add_edge(source_id, target_id, relation=str(relation_type))
            self._resources[source_id].add_dependency(target_id)
        logger.debug(
            f"Added dependency: {source_id} --[{relation_type}]--> {target_id}"
        )

    def get_resource(self, resource_id: str) -> ResourceNode | None:
        """
        Get a resource by its ID.

        Thread-safe: uses internal lock for concurrent access.

        Args:
            resource_id: The AWS resource ID

        Returns:
            The ResourceNode if found, None otherwise
        """
        with self._lock:
            return self._resources.get(resource_id)

    def get_all_resources(self) -> list[ResourceNode]:
        """Get all resources in the graph. Thread-safe."""
        with self._lock:
            return list(self._resources.values())

    def get_resources_by_type(self, resource_type: ResourceType) -> list[ResourceNode]:
        """
        Get all resources of a specific type.

        Thread-safe: uses internal lock for concurrent access.

        Args:
            resource_type: The type of resources to retrieve

        Returns:
            List of ResourceNodes matching the type
        """
        with self._lock:
            return [
                node
                for node in self._resources.values()
                if node.resource_type == resource_type
            ]

    def get_dependencies(self, resource_id: str) -> list[ResourceNode]:
        """
        Get all resources that this resource depends on.

        Args:
            resource_id: The resource to check dependencies for

        Returns:
            List of ResourceNodes that this resource depends on
        """
        if resource_id not in self._graph:
            return []

        dep_ids = list(self._graph.successors(resource_id))
        return [self._resources[rid] for rid in dep_ids if rid in self._resources]

    def get_dependents(self, resource_id: str) -> list[ResourceNode]:
        """
        Get all resources that depend on this resource.

        Args:
            resource_id: The resource to check dependents for

        Returns:
            List of ResourceNodes that depend on this resource
        """
        if resource_id not in self._graph:
            return []

        dep_ids = list(self._graph.predecessors(resource_id))
        return [self._resources[rid] for rid in dep_ids if rid in self._resources]

    def topological_sort(self) -> list[ResourceNode]:
        """
        Return resources in dependency order.

        Resources that have no dependencies come first (e.g., VPCs),
        followed by resources that depend on them (e.g., Subnets, then EC2).

        Returns:
            List of ResourceNodes in dependency order

        Raises:
            ValueError: If the graph contains cycles
        """
        try:
            # Reverse because we want dependencies first
            sorted_ids = list(reversed(list(nx.topological_sort(self._graph))))
            return [self._resources[rid] for rid in sorted_ids]
        except nx.NetworkXUnfeasible as e:
            raise ValueError("Dependency graph contains cycles") from e

    def has_cycles(self) -> bool:
        """Check if the graph contains any cycles."""
        try:
            list(nx.topological_sort(self._graph))
            return False
        except nx.NetworkXUnfeasible:
            return True

    def find_cycles(self) -> list[list[str]]:
        """Find and return all cycles in the graph."""
        try:
            return list(nx.simple_cycles(self._graph))
        except nx.NetworkXNoCycle:
            return []

    def remove_resource(self, resource_id: str) -> bool:
        """
        Remove a resource and all its edges from the graph.

        Args:
            resource_id: The resource to remove

        Returns:
            True if resource was removed, False if it didn't exist
        """
        if resource_id not in self._resources:
            return False

        self._graph.remove_node(resource_id)
        del self._resources[resource_id]
        logger.debug(f"Removed resource: {resource_id}")
        return True

    def get_subgraph(self, resource_ids: list[str]) -> GraphEngine:
        """
        Create a new GraphEngine containing only the specified resources.

        Useful for isolating a subset of resources for targeted operations.

        Args:
            resource_ids: List of resource IDs to include

        Returns:
            New GraphEngine with only the specified resources
        """
        subgraph = GraphEngine()
        for rid in resource_ids:
            if rid in self._resources:
                subgraph.add_resource(self._resources[rid])

        # Add edges that exist between included resources
        for source, target, data in self._graph.edges(data=True):
            if source in resource_ids and target in resource_ids:
                relation = DependencyType(data.get("relation", "belongs_to"))
                subgraph.add_dependency(source, target, relation)

        return subgraph

    def iter_resources(self) -> Iterator[ResourceNode]:
        """Iterate over all resources."""
        yield from self._resources.values()

    def statistics(self) -> dict[str, Any]:
        """
        Get statistics about the graph.

        Returns:
            Dictionary with node count, edge count, and type breakdown
        """
        type_counts: dict[str, int] = {}
        for node in self._resources.values():
            type_name = str(node.resource_type)
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_resources": self.node_count,
            "total_dependencies": self.edge_count,
            "resources_by_type": type_counts,
            "has_cycles": self.has_cycles(),
        }

    def to_dict(self) -> dict[str, Any]:
        """
        Export the graph to a serializable dictionary.

        Returns:
            Dictionary representation of the graph
        """
        nodes = [node.to_dict() for node in self._resources.values()]

        edges = []
        for source, target, data in self._graph.edges(data=True):
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "relation": data.get("relation", "belongs_to"),
                }
            )

        return {
            "version": "1.0",
            "nodes": nodes,
            "edges": edges,
            "statistics": self.statistics(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GraphEngine:
        """
        Create a GraphEngine from a dictionary.

        Args:
            data: Dictionary with 'nodes' and 'edges' keys

        Returns:
            Reconstructed GraphEngine
        """
        engine = cls()

        # Add all nodes first
        for node_data in data.get("nodes", []):
            node = ResourceNode.from_dict(node_data)
            engine.add_resource(node)

        # Then add edges
        for edge_data in data.get("edges", []):
            relation = DependencyType(edge_data.get("relation", "belongs_to"))
            try:
                engine.add_dependency(
                    edge_data["source"],
                    edge_data["target"],
                    relation,
                )
            except ValueError as e:
                logger.warning(f"Skipping invalid edge: {e}")

        return engine

    def save(self, path: Path) -> None:
        """
        Save the graph to a JSON file.

        Args:
            path: Path to save the JSON file
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Graph saved to {path}")

    @classmethod
    def load(cls, path: Path) -> GraphEngine:
        """
        Load a graph from a JSON file.

        Args:
            path: Path to the JSON file

        Returns:
            Loaded GraphEngine
        """
        with open(path) as f:
            data = json.load(f)
        logger.info(f"Graph loaded from {path}")
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return f"GraphEngine(nodes={self.node_count}, edges={self.edge_count})"

    def __len__(self) -> int:
        return self.node_count
