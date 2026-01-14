"""
Base classes and interfaces for unified graph storage.

This module defines the core abstractions:
- Node: Represents a graph node (AWS resource)
- Edge: Represents a graph edge (resource relationship)
- ResourceCategory: Enum for resource categorization
- GraphBackend: Abstract interface for storage backends
- ScanSession: Scan session lifecycle management
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

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


class ScanStatus(Enum):
    """Status of a scan session."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ScanSession:
    """
    Represents a scan session for tracking resource lifecycle.

    Used for Ghost Fix: tracking which resources belong to which scan,
    enabling cleanup of stale (phantom) resources from previous scans.

    Attributes:
        id: Unique scan session ID
        profile: AWS profile used
        region: AWS region scanned
        status: Current scan status
        started_at: When the scan started
        completed_at: When the scan completed (if finished)
        resource_count: Number of resources discovered
        error_message: Error details if failed
    """

    id: str = field(default_factory=lambda: f"scan-{uuid.uuid4().hex[:12]}")
    profile: str | None = None
    region: str | None = None
    status: ScanStatus = ScanStatus.RUNNING
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    resource_count: int = 0
    error_message: str | None = None

    def complete(self, resource_count: int = 0) -> None:
        """Mark session as completed."""
        self.status = ScanStatus.COMPLETED
        self.completed_at = datetime.now(UTC)
        self.resource_count = resource_count

    def fail(self, error: str) -> None:
        """Mark session as failed."""
        self.status = ScanStatus.FAILED
        self.completed_at = datetime.now(UTC)
        self.error_message = error

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "id": self.id,
            "profile": self.profile,
            "region": self.region,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "resource_count": self.resource_count,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ScanSession:
        """Create ScanSession from dictionary."""
        return cls(
            id=data["id"],
            profile=data.get("profile"),
            region=data.get("region"),
            status=ScanStatus(data["status"]),
            started_at=datetime.fromisoformat(data["started_at"]),
            completed_at=(
                datetime.fromisoformat(data["completed_at"])
                if data.get("completed_at")
                else None
            ),
            resource_count=data.get("resource_count", 0),
            error_message=data.get("error_message"),
        )


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
        scan_id: ID of the scan session that discovered this resource
        is_phantom: True if this is a placeholder for a missing dependency
        phantom_reason: Why this node is a phantom (e.g., "cross-account reference")
    """

    id: str
    type: str
    name: str | None = None
    region: str | None = None
    account_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    scan_id: str | None = None
    is_phantom: bool = False
    phantom_reason: str | None = None

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

        # Check DATABASE before COMPUTE since "rds_instance" contains "instance"
        if any(
            t in type_lower
            for t in ("rds", "dynamodb", "elasticache", "redshift", "aurora")
        ):
            return ResourceCategory.DATABASE
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
            "scan_id": self.scan_id,
            "is_phantom": self.is_phantom,
            "phantom_reason": self.phantom_reason,
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
            scan_id=data.get("scan_id"),
            is_phantom=data.get("is_phantom", False),
            phantom_reason=data.get("phantom_reason"),
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
        scan_id: ID of the scan session that discovered this edge
    """

    source_id: str
    target_id: str
    relation: str
    attributes: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    scan_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation": self.relation,
            "attributes": self.attributes,
            "weight": self.weight,
            "scan_id": self.scan_id,
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
            scan_id=data.get("scan_id"),
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

    # Scan Session Management
    @abstractmethod
    def start_scan(
        self, profile: str | None = None, region: str | None = None
    ) -> ScanSession:
        """Start a new scan session."""
        ...

    @abstractmethod
    def end_scan(
        self, scan_id: str, success: bool = True, error: str | None = None
    ) -> None:
        """End a scan session."""
        ...

    @abstractmethod
    def get_scan_session(self, scan_id: str) -> ScanSession | None:
        """Get a scan session by ID."""
        ...

    @abstractmethod
    def get_phantom_nodes(self) -> list[Node]:
        """Get all phantom (placeholder) nodes."""
        ...

    @abstractmethod
    def cleanup_stale_resources(self, current_scan_id: str) -> int:
        """Remove resources not seen in current scan. Returns count removed."""
        ...

    @abstractmethod
    def get_schema_version(self) -> int:
        """Get current database schema version."""
        ...
