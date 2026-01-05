"""
Unified graph storage for RepliMap.

This module provides a unified SQLite-based storage layer for graph operations.

Key Components:
- Node: Represents a graph node (AWS resource)
- Edge: Represents a graph edge (resource relationship)
- SQLiteBackend: Unified SQLite storage backend
- UnifiedGraphEngine: High-level facade for graph operations

Architecture:
- Single SQLite backend for ALL scales
- :memory: mode for ephemeral/fast scans
- file mode for persistent/large scans
- NetworkX projection on-demand for complex analysis

Note: InMemoryBackend has been intentionally removed.
SQLite with :memory: mode provides equivalent performance
with unified snapshot and query capabilities.

Usage:
    from replimap.core.storage import UnifiedGraphEngine, Node, Edge

    # Memory mode (ephemeral)
    engine = UnifiedGraphEngine()

    # File mode (persistent)
    engine = UnifiedGraphEngine(cache_dir="~/.replimap/cache/profile")

    # Add nodes and edges
    engine.add_nodes([Node(id="vpc-1", type="aws_vpc", name="Main VPC")])
    engine.add_edges([Edge(source_id="subnet-1", target_id="vpc-1", relation="belongs_to")])

    # Create snapshot
    engine.snapshot("/path/to/snapshot.db")

    # Project to NetworkX for complex analysis
    G = engine.to_networkx()
"""

from .base import Edge, GraphBackend, Node, ResourceCategory
from .engine import UnifiedGraphEngine
from .sqlite_backend import SQLiteBackend

__all__ = [
    # Data classes
    "Node",
    "Edge",
    "ResourceCategory",
    # Backend interface
    "GraphBackend",
    # SQLite implementation
    "SQLiteBackend",
    # High-level engine
    "UnifiedGraphEngine",
]
