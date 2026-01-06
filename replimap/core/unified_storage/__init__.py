"""
Unified graph storage for RepliMap.

This module provides a unified SQLite-based storage layer for graph operations.

Key Components:
- Node: Represents a graph node (AWS resource)
- Edge: Represents a graph edge (resource relationship)
- SQLiteBackend: Unified SQLite storage backend
- UnifiedGraphEngine: High-level facade for graph operations
- ScanSession: Scan session lifecycle management
- ScanStatus: Status enum for scan sessions

Architecture:
- Single SQLite backend for ALL scales
- :memory: mode for ephemeral/fast scans
- file mode for persistent/large scans
- NetworkX projection on-demand for complex analysis
- zlib compression for attributes (80-90% disk savings)
- Schema migration system (version-based upgrades)
- Scan session management (Ghost Fix)

Note: InMemoryBackend has been intentionally removed.
SQLite with :memory: mode provides equivalent performance
with unified snapshot and query capabilities.

Usage:
    from replimap.core.unified_storage import UnifiedGraphEngine, Node, Edge

    # Memory mode (ephemeral)
    engine = UnifiedGraphEngine()

    # File mode (persistent)
    engine = UnifiedGraphEngine(cache_dir="~/.replimap/cache/profile")

    # Add nodes and edges
    engine.add_nodes([Node(id="vpc-1", type="aws_vpc", name="Main VPC")])
    engine.add_edges([Edge(source_id="subnet-1", target_id="vpc-1", relation="belongs_to")])

    # Scan session management (Ghost Fix)
    session = engine.start_scan(profile="prod", region="us-east-1")
    # ... add nodes/edges ...
    engine.end_scan(session.id)

    # Create snapshot
    engine.snapshot("/path/to/snapshot.db")

    # Project to NetworkX for complex analysis
    G = engine.to_networkx()
"""

from .adapter import GraphEngineAdapter, SCCResult
from .base import Edge, GraphBackend, Node, ResourceCategory, ScanSession, ScanStatus
from .engine import UnifiedGraphEngine
from .sqlite_backend import SQLiteBackend

__all__ = [
    # Data classes
    "Node",
    "Edge",
    "ResourceCategory",
    # Scan session management
    "ScanSession",
    "ScanStatus",
    # Backend interface
    "GraphBackend",
    # SQLite implementation
    "SQLiteBackend",
    # High-level engine
    "UnifiedGraphEngine",
    # Backward compatibility adapter
    "GraphEngineAdapter",
    "SCCResult",
]
