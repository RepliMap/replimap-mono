"""
Base classes and interfaces for unified graph storage.

This module defines the core abstractions:
- Node: Represents a graph node (AWS resource)
- Edge: Represents a graph edge (resource relationship)
- ResourceCategory: Enum for resource categorization
- GraphBackend: Abstract interface for storage backends
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    pass


class ResourceCategory(Enum):
    """Resource categories for filtering and analysis."""

    COMPUTE = "compute"
    STORAGE = "storage"
    NETWORK = "network"
    SECURITY = "security"
    DATABASE = "database"
    OTHER = "other"


@dataclass
class Node:
    """
    Represents a graph node (AWS resource).

    Attributes:
        id: Unique identifier (typically AWS resource ID)
        type: Resource type (e.g., 'aws_instance', 'aws_vpc')
        name: Human-readable name (from Name tag)
        region: AWS region
        account_id: AWS account ID
        attributes: Additional attributes as key-value pairs
    """

    id: str
    type: str
    name: str | None = None
    region: str | None = None
    account_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)

    _category: ResourceCategory | None = field(default=None, repr=False, compare=False)

    @property
    def category(self) -> ResourceCategory:
        """Compute resource category based on type."""
        if self._category is not None:
            return self._category
        self._category = self._compute_category()
        return self._category

    def _compute_category(self) -> ResourceCategory:
        """Infer category from resource type."""
        type_lower = self.type.lower()

        if any(
            t in type_lower
            for t in ("lambda", "instance", "ecs", "eks", "batch", "fargate")
        ):
            return ResourceCategory.COMPUTE
        if any(t in type_lower for t in ("s3", "ebs", "efs", "glacier", "fsx")):
            return ResourceCategory.STORAGE
        if any(
            t in type_lower
            for t in ("vpc", "subnet", "security_group", "route", "nat", "igw")
        ):
            return ResourceCategory.NETWORK
        if any(t in type_lower for t in ("iam", "kms", "secret", "acm", "waf")):
            return ResourceCategory.SECURITY
        if any(
            t in type_lower
            for t in ("rds", "dynamodb", "elasticache", "redshift", "aurora")
        ):
            return ResourceCategory.DATABASE

        return ResourceCategory.OTHER

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "region": self.region,
            "account_id": self.account_id,
            "attributes": self.attributes,
            "category": self.category.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Node:
        """Create Node from dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            name=data.get("name"),
            region=data.get("region"),
            account_id=data.get("account_id"),
            attributes=data.get("attributes", {}),
        )

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Node) and self.id == other.id


@dataclass
class Edge:
    """
    Represents a graph edge (resource relationship).

    Attributes:
        source_id: Source node ID (the resource that depends)
        target_id: Target node ID (the resource being depended on)
        relation: Type of relationship (e.g., 'belongs_to', 'uses')
        attributes: Additional edge attributes
        weight: Edge weight for weighted graph algorithms
    """

    source_id: str
    target_id: str
    relation: str
    attributes: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "attributes": self.attributes,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Edge:
        """Create Edge from dictionary."""
        return cls(
            source_id=data["source_id"],
            target_id=data["target_id"],
            relation=data["relation"],
            attributes=data.get("attributes", {}),
            weight=data.get("weight", 1.0),
        )

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id, self.relation))

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Edge)
            and self.source_id == other.source_id
            and self.target_id == other.target_id
            and self.relation == other.relation
        )


class GraphBackend(ABC):
    """
    Abstract base class for graph storage backends.

    All storage backends (SQLite, memory, etc.) must implement this interface.
    """

    # Node operations
    @abstractmethod
    def add_node(self, node: Node) -> None:
        """Add a single node to the graph."""
        ...

    @abstractmethod
    def add_nodes_batch(self, nodes: list[Node]) -> int:
        """Add multiple nodes in batch. Returns count added."""
        ...

    @abstractmethod
    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        ...

    @abstractmethod
    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        ...

    @abstractmethod
    def search_nodes(self, query: str, limit: int = 100) -> list[Node]:
        """Search nodes by text query."""
        ...

    @abstractmethod
    def node_count(self) -> int:
        """Get total number of nodes."""
        ...

    @abstractmethod
    def get_all_nodes(self) -> Iterator[Node]:
        """Iterate over all nodes."""
        ...

    # Edge operations
    @abstractmethod
    def add_edge(self, edge: Edge) -> None:
        """Add a single edge to the graph."""
        ...

    @abstractmethod
    def add_edges_batch(self, edges: list[Edge]) -> int:
        """Add multiple edges in batch. Returns count added."""
        ...

    @abstractmethod
    def get_edges_from(self, node_id: str) -> list[Edge]:
        """Get all edges originating from a node."""
        ...

    @abstractmethod
    def get_edges_to(self, node_id: str) -> list[Edge]:
        """Get all edges pointing to a node."""
        ...

    @abstractmethod
    def edge_count(self) -> int:
        """Get total number of edges."""
        ...

    @abstractmethod
    def get_all_edges(self) -> Iterator[Edge]:
        """Iterate over all edges."""
        ...

    # Traversal
    @abstractmethod
    def get_neighbors(self, node_id: str, direction: str = "both") -> list[Node]:
        """Get neighboring nodes. Direction: 'in', 'out', or 'both'."""
        ...

    @abstractmethod
    def find_path(
        self, source_id: str, target_id: str, max_depth: int = 10
    ) -> list[str] | None:
        """Find shortest path between two nodes. Returns node IDs or None."""
        ...

    # Analytics
    @abstractmethod
    def get_node_degree(self, node_id: str) -> tuple[int, int]:
        """Get (in_degree, out_degree) for a node."""
        ...

    @abstractmethod
    def get_high_degree_nodes(self, top_n: int = 10) -> list[tuple[Node, int]]:
        """Get nodes with highest total degree."""
        ...

    # Persistence
    @abstractmethod
    def snapshot(self, target_path: str) -> None:
        """Create a snapshot backup at target path."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Clear all data from the backend."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close connections and release resources."""
        ...

    # Metadata
    @abstractmethod
    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata key-value pair."""
        ...

    @abstractmethod
    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value by key."""
        ...
