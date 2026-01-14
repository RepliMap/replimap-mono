"""
GraphEngine Adapter - Bridges old GraphEngine API to UnifiedGraphEngine.

This adapter provides backward compatibility for existing code that uses the
old GraphEngine interface (ResourceNode, DependencyType) while using the new
UnifiedGraphEngine (Node, Edge) backend under the hood.

The adapter:
1. Converts ResourceNode ↔ Node
2. Converts DependencyType ↔ edge.relation
3. Implements full GraphEngine interface
4. Stores in SQLite instead of JSON

Usage:
    # Drop-in replacement for old GraphEngine
    from replimap.core.unified_storage import GraphEngineAdapter

    graph = GraphEngineAdapter()  # Uses SQLite in memory
    graph = GraphEngineAdapter(cache_dir="~/.replimap/cache/prod")  # Persistent

    # Same API as old GraphEngine
    graph.add_resource(ResourceNode(...))
    graph.add_dependency(source_id, target_id, DependencyType.USES)
    nodes = graph.get_all_resources()
"""

from __future__ import annotations

import json
import logging
import re
import threading
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.sanitizer import sanitize_resource_config

from .base import Edge, Node
from .engine import UnifiedGraphEngine

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Patterns for inferring resource type from AWS ID prefix
_AWS_ID_PATTERNS: dict[str, ResourceType] = {
    r"^vpc-": ResourceType.VPC,
    r"^subnet-": ResourceType.SUBNET,
    r"^sg-": ResourceType.SECURITY_GROUP,
    r"^i-": ResourceType.EC2_INSTANCE,
    r"^rtb-": ResourceType.ROUTE_TABLE,
    r"^igw-": ResourceType.INTERNET_GATEWAY,
    r"^nat-": ResourceType.NAT_GATEWAY,
    r"^vpce-": ResourceType.VPC_ENDPOINT,
    r"^lt-": ResourceType.LAUNCH_TEMPLATE,
    r"^asg-": ResourceType.AUTOSCALING_GROUP,
    r"^arn:aws:elasticloadbalancing:": ResourceType.LB,
    r"^arn:aws:rds:": ResourceType.RDS_INSTANCE,
    r"^arn:aws:s3:::": ResourceType.S3_BUCKET,
}


@dataclass
class SCCResult:
    """
    Result of Strongly Connected Components analysis.

    Attributes:
        components: List of SCCs, each is a set of node IDs
        node_to_scc: Map from node ID to its SCC index
        has_cycles: True if any SCC has size > 1 (actual cycles)
        cycle_groups: Only SCCs with size > 1 (the actual cycles)
    """

    components: list[set[str]]
    node_to_scc: dict[str, int]
    has_cycles: bool
    cycle_groups: list[set[str]]


class RepliMapJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that handles types from AWS/Boto3 responses.

    Handles:
    - datetime objects (from Boto3 timestamps like CreateTime, LaunchTime)
    - set/frozenset (from some Boto3 responses)
    - bytes (from binary data fields)
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (set, frozenset)):
            return list(obj)
        if isinstance(obj, bytes):
            return "[BINARY DATA]"
        return super().default(obj)


def resource_node_to_node(resource: ResourceNode) -> Node:
    """Convert old ResourceNode to new Node format."""
    # Store ResourceNode-specific fields in attributes
    attributes = {
        "config": resource.config,
        "tags": resource.tags,
        "dependencies": resource.dependencies,
        "terraform_name": resource.terraform_name,
        "original_name": resource.original_name,
        "arn": resource.arn,
    }

    return Node(
        id=resource.id,
        type=str(resource.resource_type),
        name=resource.original_name or resource.tags.get("Name"),
        region=resource.region,
        account_id=None,  # ResourceNode doesn't track this
        attributes=attributes,
        is_phantom=resource.is_phantom,
        phantom_reason=resource.phantom_reason,
    )


def node_to_resource_node(node: Node) -> ResourceNode:
    """Convert new Node to old ResourceNode format."""
    attrs = node.attributes or {}

    # Extract ResourceType from type string
    try:
        resource_type = ResourceType(node.type)
    except ValueError:
        resource_type = ResourceType.UNKNOWN

    return ResourceNode(
        id=node.id,
        resource_type=resource_type,
        region=node.region or "unknown",
        config=attrs.get("config", {}),
        arn=attrs.get("arn"),
        tags=attrs.get("tags", {}),
        dependencies=attrs.get("dependencies", []),
        terraform_name=attrs.get("terraform_name"),
        original_name=attrs.get("original_name") or node.name,
        is_phantom=node.is_phantom,
        phantom_reason=node.phantom_reason,
    )


def dependency_type_to_relation(dep_type: DependencyType) -> str:
    """Convert DependencyType to edge relation string."""
    return str(dep_type)


def relation_to_dependency_type(relation: str) -> DependencyType:
    """Convert edge relation string to DependencyType."""
    try:
        return DependencyType(relation)
    except ValueError:
        return DependencyType.BELONGS_TO


class GraphEngineAdapter:
    """
    Adapter that provides old GraphEngine interface over UnifiedGraphEngine.

    This is a drop-in replacement for the old GraphEngine class. It uses the
    new UnifiedGraphEngine (SQLite-based) backend while exposing the exact
    same API that existing code expects.

    All data is stored in SQLite instead of the legacy JSON format.
    """

    def __init__(
        self,
        create_phantom_nodes: bool = True,
        cache_dir: str | None = None,
        db_path: str | None = None,
    ) -> None:
        """
        Initialize the adapter.

        Args:
            create_phantom_nodes: If True, automatically create phantom nodes
                for missing dependencies instead of raising errors.
            cache_dir: Directory for persistent storage (creates graph.db)
            db_path: Direct database path (overrides cache_dir)
        """
        self._engine = UnifiedGraphEngine(cache_dir=cache_dir, db_path=db_path)
        self._create_phantom_nodes = create_phantom_nodes
        self._phantom_nodes: set[str] = set()
        self._lock = threading.RLock()

        # Cache for ResourceNode objects (to avoid repeated conversions)
        self._resource_cache: dict[str, ResourceNode] = {}

    @property
    def node_count(self) -> int:
        """Number of resources in the graph."""
        return self._engine.node_count()

    @property
    def edge_count(self) -> int:
        """Number of dependencies in the graph."""
        return self._engine.edge_count()

    @property
    def phantom_count(self) -> int:
        """Number of phantom (placeholder) nodes in the graph."""
        return len(self._phantom_nodes)

    @property
    def _graph(self) -> Any:
        """
        Access underlying NetworkX graph (for backward compatibility).

        Note: This creates a temporary projection. Use sparingly.
        """
        return self._engine.to_networkx()

    def add_resource(self, node: ResourceNode) -> None:
        """
        Add a resource node to the graph.

        If a resource with the same ID already exists, it will be updated.
        Thread-safe: uses internal lock for concurrent access.

        Security: Config is sanitized BEFORE storage to prevent sensitive
        data (passwords, API keys, UserData) from being persisted to cache.

        Args:
            node: The ResourceNode to add
        """
        # SECURITY: Sanitize config BEFORE locking and storage
        # This runs outside the lock to minimize contention (regex is expensive)
        if node.config:
            sanitized_config = sanitize_resource_config(node.config)
            # Update config in-place (dict is mutable)
            node.config.clear()
            node.config.update(sanitized_config)

        # Convert and store
        unified_node = resource_node_to_node(node)

        with self._lock:
            self._engine.add_node(unified_node)
            self._resource_cache[node.id] = node

            if node.is_phantom:
                self._phantom_nodes.add(node.id)

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
        Thread-safe: uses internal lock for concurrent access.

        Args:
            source_id: ID of the dependent resource
            target_id: ID of the resource being depended on
            relation_type: Type of dependency relationship

        Raises:
            ValueError: If either resource doesn't exist and create_phantom_nodes is False
        """
        with self._lock:
            # Handle missing source
            if self._engine.get_node(source_id) is None:
                if self._create_phantom_nodes:
                    self._create_phantom_node(source_id)
                else:
                    raise ValueError(f"Source resource not found: {source_id}")

            # Handle missing target
            if self._engine.get_node(target_id) is None:
                if self._create_phantom_nodes:
                    self._create_phantom_node(target_id)
                else:
                    raise ValueError(f"Target resource not found: {target_id}")

            # Create edge
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                relation=dependency_type_to_relation(relation_type),
            )
            self._engine.add_edge(edge)

            # Update source's dependencies list in cache
            if source_id in self._resource_cache:
                self._resource_cache[source_id].add_dependency(target_id)

        logger.debug(
            f"Added dependency: {source_id} --[{relation_type}]--> {target_id}"
        )

    def _create_phantom_node(self, node_id: str) -> None:
        """
        Create a phantom placeholder node for a missing resource.

        Args:
            node_id: The ID of the missing resource
        """
        resource_type = self._infer_type_from_id(node_id)

        phantom = ResourceNode(
            id=node_id,
            resource_type=resource_type,
            region="unknown",
            config={},
            tags={},
            terraform_name=f"phantom_{node_id.replace('-', '_')}",
            original_name=f"[Missing] {node_id}",
            is_phantom=True,
            phantom_reason="Referenced by other resources but not discovered during scan",
        )

        unified_node = resource_node_to_node(phantom)
        self._engine.add_node(unified_node)
        self._resource_cache[node_id] = phantom
        self._phantom_nodes.add(node_id)

        logger.warning(
            f"Created phantom node for missing resource: {node_id} (type: {resource_type})"
        )

    def _infer_type_from_id(self, node_id: str) -> ResourceType:
        """Infer resource type from AWS ID prefix pattern or ARN."""
        for pattern, resource_type in _AWS_ID_PATTERNS.items():
            if re.match(pattern, node_id):
                return resource_type

        if node_id.startswith("arn:aws:"):
            parts = node_id.split(":")
            if len(parts) >= 3:
                service = parts[2]
                arn_service_map: dict[str, ResourceType] = {
                    "ec2": ResourceType.EC2_INSTANCE,
                    "rds": ResourceType.RDS_INSTANCE,
                    "s3": ResourceType.S3_BUCKET,
                    "elasticache": ResourceType.ELASTICACHE_CLUSTER,
                    "elasticloadbalancing": ResourceType.LB,
                    "sqs": ResourceType.SQS_QUEUE,
                    "sns": ResourceType.SNS_TOPIC,
                    "iam": ResourceType.IAM_ROLE,
                    "logs": ResourceType.CLOUDWATCH_LOG_GROUP,
                    "cloudwatch": ResourceType.CLOUDWATCH_METRIC_ALARM,
                }
                if service in arn_service_map:
                    return arn_service_map[service]

        return ResourceType.UNKNOWN

    def get_resource(self, resource_id: str) -> ResourceNode | None:
        """Get a resource by its ID."""
        # Check cache first
        if resource_id in self._resource_cache:
            resource = self._resource_cache[resource_id]
            # Ensure dependencies are populated (cache may have been populated
            # by iter_resources() which doesn't load dependencies)
            self._ensure_dependencies_loaded(resource)
            return resource

        node = self._engine.get_node(resource_id)
        if node is None:
            return None

        resource = node_to_resource_node(node)

        # Populate dependencies from edges (edges are stored separately in SQLite)
        self._ensure_dependencies_loaded(resource)

        self._resource_cache[resource_id] = resource
        return resource

    def _ensure_dependencies_loaded(self, resource: ResourceNode) -> None:
        """Ensure a resource has its dependencies populated from edges."""
        # Only load if dependencies list is empty (avoid duplicate loading)
        # This works because scanners always create at least one dependency edge
        # if a resource has dependencies, so empty list means not loaded yet
        if not resource.dependencies:
            for edge in self._engine.get_edges_from(resource.id):
                if edge.target_id not in resource.dependencies:
                    resource.dependencies.append(edge.target_id)

    def get_all_resources(self) -> list[ResourceNode]:
        """Get all resources in the graph."""
        resources = []
        for node in self._engine.get_all_nodes():
            if node.id in self._resource_cache:
                resources.append(self._resource_cache[node.id])
            else:
                resource = node_to_resource_node(node)
                self._resource_cache[node.id] = resource
                resources.append(resource)

        # Populate dependencies from edges (edges are stored separately in SQLite)
        # This is needed because node_to_resource_node gets dependencies from
        # node.attributes which may be empty when loaded from cache
        self._populate_dependencies_from_edges(resources)

        return resources

    def _populate_dependencies_from_edges(self, resources: list[ResourceNode]) -> None:
        """Populate resource dependencies from edges stored in SQLite."""
        # For small resource lists, query edges per resource (more efficient)
        # For large lists, scan all edges once
        if len(resources) < 50:
            for resource in resources:
                self._ensure_dependencies_loaded(resource)
        else:
            # Build a lookup for quick access
            resource_map = {r.id: r for r in resources}

            # Get all edges and populate dependencies
            for edge in self._engine.get_all_edges():
                source_resource = resource_map.get(edge.source_id)
                if source_resource is not None:
                    # Add target to dependencies if not already present
                    if edge.target_id not in source_resource.dependencies:
                        source_resource.dependencies.append(edge.target_id)

    def get_resources_by_type(self, resource_type: ResourceType) -> list[ResourceNode]:
        """Get all resources of a specific type."""
        nodes = self._engine.get_nodes_by_type(str(resource_type))
        resources = []
        for node in nodes:
            if node.id in self._resource_cache:
                resources.append(self._resource_cache[node.id])
            else:
                resource = node_to_resource_node(node)
                self._resource_cache[node.id] = resource
                resources.append(resource)

        # Populate dependencies from edges for all returned resources
        self._populate_dependencies_from_edges(resources)

        return resources

    def get_dependencies(self, resource_id: str) -> list[ResourceNode]:
        """Get all resources that this resource depends on."""
        nodes = self._engine.get_dependencies(resource_id, recursive=False)
        resources = []
        for n in nodes:
            resource = self.get_resource(n.id)
            if resource is None:
                # Fallback: create from node and populate dependencies
                resource = node_to_resource_node(n)
                self._ensure_dependencies_loaded(resource)
                self._resource_cache[n.id] = resource
            resources.append(resource)
        return resources

    def get_dependents(self, resource_id: str) -> list[ResourceNode]:
        """Get all resources that depend on this resource."""
        nodes = self._engine.get_dependents(resource_id, recursive=False)
        resources = []
        for n in nodes:
            resource = self.get_resource(n.id)
            if resource is None:
                # Fallback: create from node and populate dependencies
                resource = node_to_resource_node(n)
                self._ensure_dependencies_loaded(resource)
                self._resource_cache[n.id] = resource
            resources.append(resource)
        return resources

    def get_phantom_nodes(self) -> list[ResourceNode]:
        """Get all phantom nodes in the graph."""
        resources = [
            self._resource_cache[pid]
            for pid in self._phantom_nodes
            if pid in self._resource_cache
        ]
        # Ensure dependencies are loaded for all phantom nodes
        for resource in resources:
            self._ensure_dependencies_loaded(resource)
        return resources

    def is_phantom(self, resource_id: str) -> bool:
        """Check if a resource is a phantom node."""
        return resource_id in self._phantom_nodes

    def topological_sort(self) -> list[ResourceNode]:
        """
        Return resources in dependency order.

        Resources that have no dependencies come first (e.g., VPCs),
        followed by resources that depend on them.

        Raises:
            ValueError: If the graph contains cycles
        """
        try:
            sorted_ids = self._engine.topological_sort()
            return [
                self.get_resource(rid) or self._get_or_create_resource(rid)
                for rid in sorted_ids
            ]
        except ValueError as e:
            raise ValueError("Dependency graph contains cycles") from e

    def _get_or_create_resource(self, resource_id: str) -> ResourceNode:
        """Get resource or create minimal stub."""
        resource = self.get_resource(resource_id)
        if resource:
            return resource
        # Fallback - shouldn't happen normally
        node = self._engine.get_node(resource_id)
        if node:
            resource = node_to_resource_node(node)
            self._ensure_dependencies_loaded(resource)
            self._resource_cache[node.id] = resource
            return resource
        raise ValueError(f"Resource not found: {resource_id}")

    def has_cycles(self) -> bool:
        """Check if the graph contains any cycles."""
        return self._engine.has_cycles()

    def find_cycles(self) -> list[list[str]]:
        """Find and return all cycles in the graph."""
        return self._engine.find_cycles()

    def find_strongly_connected_components(self) -> SCCResult:
        """
        Find all strongly connected components using Tarjan's algorithm.

        Returns:
            SCCResult with components, cycle groups, and node mapping
        """
        sccs = self._engine.strongly_connected_components()

        node_to_scc: dict[str, int] = {}
        for i, scc in enumerate(sccs):
            for node_id in scc:
                node_to_scc[node_id] = i

        cycle_groups = [scc for scc in sccs if len(scc) > 1]

        return SCCResult(
            components=list(sccs),
            node_to_scc=node_to_scc,
            has_cycles=len(cycle_groups) > 0,
            cycle_groups=cycle_groups,
        )

    def get_safe_dependency_order(self) -> list[ResourceNode]:
        """
        Get topologically sorted node order, handling cycles safely.

        Unlike topological_sort(), this method:
        1. Detects strongly connected components (cycles)
        2. Collapses cycles into "super-nodes" for ordering
        3. Returns nodes in a valid dependency order
        4. Nodes within a cycle are returned in arbitrary order

        This never raises an exception for cyclic graphs.

        Returns:
            List of ResourceNodes in safe dependency order
        """
        import networkx as nx

        scc_result = self.find_strongly_connected_components()

        if scc_result.has_cycles:
            logger.warning(
                f"Found {len(scc_result.cycle_groups)} circular dependency groups. "
                f"Resources in cycles: {sum(len(g) for g in scc_result.cycle_groups)}"
            )

        # Build condensation graph (DAG of SCCs)
        # Each SCC becomes a single node
        condensed: nx.DiGraph = nx.DiGraph()
        for i, _scc in enumerate(scc_result.components):
            condensed.add_node(i)

        # Add edges between SCCs
        for edge in self._engine.get_all_edges():
            source_scc = scc_result.node_to_scc.get(edge.source_id)
            target_scc = scc_result.node_to_scc.get(edge.target_id)
            if source_scc is not None and target_scc is not None:
                if source_scc != target_scc:
                    condensed.add_edge(source_scc, target_scc)

        # Topologically sort the condensed graph (guaranteed to work, it's a DAG)
        scc_order = list(reversed(list(nx.topological_sort(condensed))))

        # Flatten back to node order
        result = []
        for scc_idx in scc_order:
            for node_id in scc_result.components[scc_idx]:
                resource = self.get_resource(node_id)
                if resource:
                    result.append(resource)

        return result

    def remove_resource(self, resource_id: str) -> bool:
        """Remove a resource and all its edges from the graph."""
        if self._engine.get_node(resource_id) is None:
            return False

        self._engine.remove_node(resource_id)
        self._resource_cache.pop(resource_id, None)
        self._phantom_nodes.discard(resource_id)
        logger.debug(f"Removed resource: {resource_id}")
        return True

    def get_subgraph(self, resource_ids: list[str]) -> GraphEngineAdapter:
        """Create a new GraphEngineAdapter containing only the specified resources."""
        subgraph = GraphEngineAdapter(create_phantom_nodes=self._create_phantom_nodes)

        for rid in resource_ids:
            resource = self.get_resource(rid)
            if resource:
                subgraph.add_resource(resource)

        # Add edges between included resources
        for source_id in resource_ids:
            for edge in self._engine.get_edges_from(source_id):
                if edge.target_id in resource_ids:
                    relation = relation_to_dependency_type(edge.relation)
                    subgraph.add_dependency(source_id, edge.target_id, relation)

        return subgraph

    def iter_resources(self) -> Iterator[ResourceNode]:
        """Iterate over all resources."""
        for node in self._engine.get_all_nodes():
            if node.id in self._resource_cache:
                yield self._resource_cache[node.id]
            else:
                resource = node_to_resource_node(node)
                self._resource_cache[node.id] = resource
                yield resource

    def statistics(self) -> dict[str, Any]:
        """Get statistics about the graph."""
        type_counts: dict[str, int] = {}
        for resource in self.iter_resources():
            type_name = str(resource.resource_type)
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_resources": self.node_count,
            "total_dependencies": self.edge_count,
            "resources_by_type": type_counts,
            "has_cycles": self.has_cycles(),
            "phantom_count": self.phantom_count,
            "phantom_nodes": list(self._phantom_nodes),
        }

    def merge(self, other: GraphEngineAdapter) -> None:
        """
        Merge another graph into this one.

        Merge rules:
        - Real nodes take precedence over phantom nodes
        - Edges are combined additively
        """
        with self._lock:
            # Merge nodes
            for resource in other.iter_resources():
                existing = self.get_resource(resource.id)
                if existing is None:
                    self.add_resource(resource)
                elif existing.is_phantom and not resource.is_phantom:
                    # Replace phantom with real node
                    self.remove_resource(resource.id)
                    self.add_resource(resource)

            # Merge edges
            for source_id in [r.id for r in other.get_all_resources()]:
                for edge in other._engine.get_edges_from(source_id):
                    # Check if edge already exists
                    existing_edges = self._engine.get_edges_from(edge.source_id)
                    edge_exists = any(
                        e.target_id == edge.target_id for e in existing_edges
                    )
                    if not edge_exists:
                        relation = relation_to_dependency_type(edge.relation)
                        self.add_dependency(edge.source_id, edge.target_id, relation)

    def to_dict(self) -> dict[str, Any]:
        """Export the graph to a serializable dictionary."""
        nodes = [resource.to_dict() for resource in self.iter_resources()]

        edges = []
        for resource in self.iter_resources():
            for edge in self._engine.get_edges_from(resource.id):
                edges.append(
                    {
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "relation": edge.relation,
                    }
                )

        return {
            "version": "1.0",
            "nodes": nodes,
            "edges": edges,
            "statistics": self.statistics(),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        cache_dir: str | None = None,
    ) -> GraphEngineAdapter:
        """Create a GraphEngineAdapter from a dictionary."""
        engine = cls(cache_dir=cache_dir)

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
        Save the graph to a JSON file (for compatibility).

        Note: Prefer using snapshot() for SQLite-native storage.
        """
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, cls=RepliMapJSONEncoder)
        logger.info(f"Graph saved to {path}")

    @classmethod
    def load(cls, path: Path) -> GraphEngineAdapter:
        """Load a graph from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        logger.info(f"Graph loaded from {path}")
        return cls.from_dict(data)

    def snapshot(self, target_path: str | None = None) -> str:
        """Create a SQLite snapshot of current graph state."""
        return self._engine.snapshot(target_path)

    @classmethod
    def load_snapshot(cls, snapshot_path: str) -> GraphEngineAdapter:
        """Load a SQLite snapshot as a new GraphEngineAdapter instance."""
        adapter = cls(db_path=snapshot_path)
        # Populate cache and phantom set
        for node in adapter._engine.get_all_nodes():
            if node.is_phantom:
                adapter._phantom_nodes.add(node.id)
        return adapter

    def close(self) -> None:
        """Close the underlying engine."""
        self._engine.close()

    def __enter__(self) -> GraphEngineAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"GraphEngineAdapter(nodes={self.node_count}, edges={self.edge_count})"

    def __len__(self) -> int:
        return self.node_count
