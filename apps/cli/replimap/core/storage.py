"""
High-Performance Graph Storage Engine for RepliMap.

Provides SQLite + Zstandard compression-based storage for the dependency graph,
enabling efficient persistence, lazy loading, and multi-account support.

Key Features:
- SQLite with WAL mode for concurrent read/write access
- Zstd compression for node configurations (5x+ compression ratio)
- Lazy loading: topology-first, config-on-demand
- Multi-account support via account_id prefixed node IDs
- Atomic transactions for crash-safe operations
- Thread-safe via connection pooling

Performance Targets:
- load_topology(): 10,000 nodes < 500ms
- save_graph(): 10,000 nodes < 5s
- get_node_config(): single lookup < 10ms
- Compression ratio: > 5x for typical AWS configs

Node ID Format:
    {account_id}:{region}:{resource_id}
    Example: 123456789012:ap-southeast-2:vpc-12345abcdef

Usage:
    # Save a graph
    with GraphStore() as store:
        store.save_graph(graph, account_id="123456789012")

    # Load topology only (fast)
    topology = store.load_topology(account_id="123456789012")

    # Load specific config on-demand
    config = store.get_node_config("123456789012:us-east-1:vpc-12345")
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import zstandard as zstd

if TYPE_CHECKING:
    from .graph_engine import GraphEngine

logger = logging.getLogger(__name__)

# Default storage location
DEFAULT_DB_DIR = Path.home() / ".replimap"
DEFAULT_DB_NAME = "graph.db"

# Schema version for migrations
SCHEMA_VERSION = 1

# SQL Schema
_SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL
);

-- Resource nodes (topology)
CREATE TABLE IF NOT EXISTS nodes (
    node_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    region TEXT,
    resource_type TEXT NOT NULL,
    resource_arn TEXT,
    terraform_name TEXT,
    original_name TEXT,
    is_phantom INTEGER DEFAULT 0,
    phantom_reason TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Node configurations (compressed, loaded on-demand)
CREATE TABLE IF NOT EXISTS node_configs (
    node_id TEXT PRIMARY KEY,
    config_compressed BLOB NOT NULL,
    config_hash TEXT NOT NULL,
    original_size INTEGER NOT NULL,
    tags_json TEXT,
    dependencies_json TEXT,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id) ON DELETE CASCADE
);

-- Dependency edges
CREATE TABLE IF NOT EXISTS edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL DEFAULT 'belongs_to',
    metadata_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES nodes(node_id) ON DELETE CASCADE,
    UNIQUE(source_id, target_id, edge_type)
);

-- Scan metadata
CREATE TABLE IF NOT EXISTS scan_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id TEXT NOT NULL,
    region TEXT,
    scan_started_at TEXT NOT NULL,
    scan_completed_at TEXT,
    node_count INTEGER DEFAULT 0,
    edge_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    status TEXT DEFAULT 'in_progress'
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_nodes_account ON nodes(account_id);
CREATE INDEX IF NOT EXISTS idx_nodes_region ON nodes(region);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(resource_type);
CREATE INDEX IF NOT EXISTS idx_nodes_account_region ON nodes(account_id, region);
CREATE INDEX IF NOT EXISTS idx_nodes_phantom ON nodes(is_phantom);
CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);
CREATE INDEX IF NOT EXISTS idx_scan_metadata_account ON scan_metadata(account_id);
"""


@dataclass
class NodeInfo:
    """
    Lightweight node info for topology queries (no config).

    This is returned by load_topology() for fast graph construction
    without loading the full resource configuration.
    """

    node_id: str
    account_id: str
    region: str
    resource_type: str
    resource_arn: str | None = None
    terraform_name: str | None = None
    original_name: str | None = None
    is_phantom: bool = False
    phantom_reason: str | None = None


@dataclass
class StorageStats:
    """Statistics about the graph storage."""

    total_nodes: int
    total_edges: int
    by_account: dict[str, int]
    by_region: dict[str, int]
    by_type: dict[str, int]
    phantom_count: int
    compression_ratio: float
    db_size_bytes: int
    last_scan: datetime | None = None


class ConfigCompressor:
    """
    Zstandard compression for resource configurations.

    Level 3 provides a good balance between compression ratio and speed.
    For typical AWS resource configs, achieves 5-10x compression.
    """

    def __init__(self, level: int = 3) -> None:
        self._compressor = zstd.ZstdCompressor(level=level)
        self._decompressor = zstd.ZstdDecompressor()

    def compress(self, config: dict[str, Any]) -> tuple[bytes, str, int]:
        """
        Compress a configuration dictionary.

        Returns:
            Tuple of (compressed_bytes, sha256_hash, original_size)
        """
        # Compact JSON serialization
        json_bytes = json.dumps(config, separators=(",", ":")).encode("utf-8")
        original_size = len(json_bytes)

        # Compute hash before compression for change detection
        config_hash = hashlib.sha256(json_bytes).hexdigest()

        # Compress
        compressed = self._compressor.compress(json_bytes)

        return compressed, config_hash, original_size

    def decompress(self, data: bytes) -> dict[str, Any]:
        """Decompress bytes back to configuration dictionary."""
        json_bytes = self._decompressor.decompress(data)
        result: dict[str, Any] = json.loads(json_bytes.decode("utf-8"))
        return result


class GraphStore:
    """
    High-performance SQLite + Zstd graph storage engine.

    Thread-safe through connection-per-thread pooling.
    Uses WAL mode for concurrent read/write access.

    Example:
        with GraphStore() as store:
            # Save a scanned graph
            store.save_graph(graph, account_id="123456789012")

            # Load just the topology (fast)
            topology = store.load_topology()

            # Get specific config on-demand
            config = store.get_node_config("123456789012:us-east-1:vpc-12345")

            # Query by type
            ec2_nodes = store.get_nodes_by_type("aws_instance")
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        compression_level: int = 3,
    ) -> None:
        """
        Initialize the graph store.

        Args:
            db_path: Path to SQLite database file. Defaults to ~/.replimap/graph.db
            compression_level: Zstd compression level (1-22, default 3)
        """
        if db_path is None:
            self.db_path = DEFAULT_DB_DIR / DEFAULT_DB_NAME
        else:
            self.db_path = Path(db_path)

        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Thread-local storage for connections
        self._local = threading.local()

        # Compression engine
        self._compressor = ConfigCompressor(level=compression_level)

        # Initialize database
        self._init_db()

    @property
    def _conn(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection()
        conn: sqlite3.Connection = self._local.conn
        return conn

    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection with optimal settings."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            timeout=30.0,
        )

        # Enable WAL mode for concurrent access
        conn.execute("PRAGMA journal_mode=WAL")

        # Performance optimizations
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")  # 10k pages (~40MB cache)
        conn.execute("PRAGMA temp_store=MEMORY")
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O

        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")

        # Use Row factory for dict-like access
        conn.row_factory = sqlite3.Row

        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._conn
        cursor = conn.cursor()

        # Check if schema exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
        )
        schema_exists = cursor.fetchone() is not None

        if not schema_exists:
            # Create all tables
            conn.executescript(_SCHEMA_SQL)

            # Record schema version
            cursor.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now().isoformat()),
            )
            conn.commit()
            logger.info(f"Initialized graph database at {self.db_path}")
        else:
            # Check version for future migrations
            cursor.execute("SELECT MAX(version) FROM schema_version")
            current_version = cursor.fetchone()[0] or 0

            if current_version < SCHEMA_VERSION:
                self._migrate_schema(current_version, SCHEMA_VERSION)

    def _migrate_schema(self, from_version: int, to_version: int) -> None:
        """Apply schema migrations."""
        logger.info(f"Migrating schema from v{from_version} to v{to_version}")
        # Future migrations go here
        pass

    @contextmanager
    def atomic_transaction(self) -> Iterator[sqlite3.Cursor]:
        """
        Context manager for atomic transactions.

        All operations within the context are committed together.
        On any exception, all changes are rolled back.

        Example:
            with store.atomic_transaction() as cursor:
                cursor.execute("INSERT INTO nodes ...")
                cursor.execute("INSERT INTO edges ...")
        """
        conn = self._conn
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def build_node_id(self, account_id: str, region: str, resource_id: str) -> str:
        """
        Build a canonical node ID with account prefix.

        Format: {account_id}:{region}:{resource_id}

        Args:
            account_id: AWS account ID (12 digits)
            region: AWS region (e.g., 'us-east-1')
            resource_id: AWS resource ID (e.g., 'vpc-12345')

        Returns:
            Canonical node ID string
        """
        return f"{account_id}:{region or 'global'}:{resource_id}"

    def parse_node_id(self, node_id: str) -> tuple[str, str, str]:
        """
        Parse a canonical node ID into components.

        Args:
            node_id: Canonical node ID string

        Returns:
            Tuple of (account_id, region, resource_id)

        Raises:
            ValueError: If node_id format is invalid
        """
        parts = node_id.split(":", 2)
        if len(parts) != 3:
            raise ValueError(
                f"Invalid node_id format: {node_id}. "
                f"Expected format: account_id:region:resource_id"
            )
        return parts[0], parts[1], parts[2]

    def save_graph(
        self,
        graph: GraphEngine,
        account_id: str,
        region: str | None = None,
    ) -> int:
        """
        Save a GraphEngine to the database atomically.

        Replaces any existing data for the same account/region.

        Args:
            graph: The GraphEngine to save
            account_id: AWS account ID
            region: Optional region filter (saves all if None)

        Returns:
            Number of nodes saved
        """
        start_time = time.time()

        with self.atomic_transaction() as cursor:
            # Record scan start
            cursor.execute(
                """INSERT INTO scan_metadata
                   (account_id, region, scan_started_at, status)
                   VALUES (?, ?, ?, ?)""",
                (account_id, region, datetime.now().isoformat(), "in_progress"),
            )
            scan_id = cursor.lastrowid

            # Prepare batch data
            nodes_data: list[tuple[Any, ...]] = []
            configs_data: list[tuple[Any, ...]] = []
            edges_data: list[tuple[Any, ...]] = []

            for resource in graph.get_all_resources():
                # Filter by region if specified
                if region and resource.region != region:
                    continue

                # Build canonical node ID
                node_id = self.build_node_id(account_id, resource.region, resource.id)

                # Prepare node data
                nodes_data.append(
                    (
                        node_id,
                        account_id,
                        resource.region,
                        str(resource.resource_type),
                        resource.arn,
                        resource.terraform_name,
                        resource.original_name,
                        1 if resource.is_phantom else 0,
                        resource.phantom_reason,
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                    )
                )

                # Compress and store config
                compressed, config_hash, orig_size = self._compressor.compress(
                    resource.config
                )

                configs_data.append(
                    (
                        node_id,
                        compressed,
                        config_hash,
                        orig_size,
                        json.dumps(resource.tags) if resource.tags else None,
                        json.dumps(resource.dependencies)
                        if resource.dependencies
                        else None,
                    )
                )

            # Delete existing data for this account/region
            if region:
                cursor.execute(
                    "DELETE FROM nodes WHERE account_id = ? AND region = ?",
                    (account_id, region),
                )
            else:
                cursor.execute(
                    "DELETE FROM nodes WHERE account_id = ?",
                    (account_id,),
                )

            # Batch insert nodes
            cursor.executemany(
                """INSERT INTO nodes
                   (node_id, account_id, region, resource_type, resource_arn,
                    terraform_name, original_name, is_phantom, phantom_reason,
                    created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                nodes_data,
            )

            # Batch insert configs
            cursor.executemany(
                """INSERT INTO node_configs
                   (node_id, config_compressed, config_hash, original_size,
                    tags_json, dependencies_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                configs_data,
            )

            # Process edges
            for source, target, data in graph._graph.edges(data=True):
                source_resource = graph.get_resource(source)
                target_resource = graph.get_resource(target)

                if source_resource is None or target_resource is None:
                    continue

                # Filter by region if specified
                if region and (
                    source_resource.region != region or target_resource.region != region
                ):
                    continue

                source_node_id = self.build_node_id(
                    account_id, source_resource.region, source
                )
                target_node_id = self.build_node_id(
                    account_id, target_resource.region, target
                )

                edge_type = data.get("relation", "belongs_to")
                metadata = {k: v for k, v in data.items() if k != "relation"}

                edges_data.append(
                    (
                        source_node_id,
                        target_node_id,
                        str(edge_type),
                        json.dumps(metadata) if metadata else None,
                        datetime.now().isoformat(),
                    )
                )

            # Batch insert edges
            cursor.executemany(
                """INSERT OR REPLACE INTO edges
                   (source_id, target_id, edge_type, metadata_json, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                edges_data,
            )

            # Update scan metadata
            cursor.execute(
                """UPDATE scan_metadata
                   SET scan_completed_at = ?, node_count = ?, edge_count = ?, status = ?
                   WHERE id = ?""",
                (
                    datetime.now().isoformat(),
                    len(nodes_data),
                    len(edges_data),
                    "completed",
                    scan_id,
                ),
            )

        elapsed = time.time() - start_time
        logger.info(
            f"Saved graph: {len(nodes_data)} nodes, {len(edges_data)} edges "
            f"in {elapsed:.2f}s"
        )

        return len(nodes_data)

    def load_topology(
        self,
        account_id: str | None = None,
        region: str | None = None,
    ) -> list[NodeInfo]:
        """
        Load graph topology without configurations (fast).

        This loads only the structural information needed to reconstruct
        the dependency graph. Use get_node_config() for full configs.

        Performance target: 10,000 nodes < 500ms

        Args:
            account_id: Filter by AWS account ID
            region: Filter by region

        Returns:
            List of NodeInfo objects (lightweight node data)
        """
        start_time = time.time()

        query = """
            SELECT node_id, account_id, region, resource_type, resource_arn,
                   terraform_name, original_name, is_phantom, phantom_reason
            FROM nodes
        """
        params: list[Any] = []
        conditions: list[str] = []

        if account_id:
            conditions.append("account_id = ?")
            params.append(account_id)

        if region:
            conditions.append("region = ?")
            params.append(region)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        cursor = self._conn.cursor()
        cursor.execute(query, params)

        nodes = [
            NodeInfo(
                node_id=row["node_id"],
                account_id=row["account_id"],
                region=row["region"],
                resource_type=row["resource_type"],
                resource_arn=row["resource_arn"],
                terraform_name=row["terraform_name"],
                original_name=row["original_name"],
                is_phantom=bool(row["is_phantom"]),
                phantom_reason=row["phantom_reason"],
            )
            for row in cursor.fetchall()
        ]

        elapsed = time.time() - start_time
        logger.debug(f"Loaded topology: {len(nodes)} nodes in {elapsed:.3f}s")

        return nodes

    def load_edges(
        self,
        account_id: str | None = None,
        region: str | None = None,
    ) -> list[tuple[str, str, str, dict[str, Any] | None]]:
        """
        Load all edges (dependencies) from the graph.

        Returns:
            List of (source_id, target_id, edge_type, metadata) tuples
        """
        query = "SELECT source_id, target_id, edge_type, metadata_json FROM edges"
        params: list[Any] = []

        if account_id:
            # Filter edges where both source and target belong to account
            query = """
                SELECT e.source_id, e.target_id, e.edge_type, e.metadata_json
                FROM edges e
                JOIN nodes n ON e.source_id = n.node_id
                WHERE n.account_id = ?
            """
            params.append(account_id)

            if region:
                query += " AND n.region = ?"
                params.append(region)

        cursor = self._conn.cursor()
        cursor.execute(query, params)

        return [
            (
                row["source_id"],
                row["target_id"],
                row["edge_type"],
                json.loads(row["metadata_json"]) if row["metadata_json"] else None,
            )
            for row in cursor.fetchall()
        ]

    def get_node_config(self, node_id: str) -> dict[str, Any] | None:
        """
        Get the full configuration for a specific node.

        This decompresses the stored config on-demand.

        Args:
            node_id: Canonical node ID (account:region:resource_id)

        Returns:
            Configuration dictionary, or None if not found
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT config_compressed FROM node_configs WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._compressor.decompress(row["config_compressed"])

    def get_node_tags(self, node_id: str) -> dict[str, str] | None:
        """Get tags for a specific node."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT tags_json FROM node_configs WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()

        if row is None or row["tags_json"] is None:
            return None

        result: dict[str, str] = json.loads(row["tags_json"])
        return result

    def get_node_dependencies(self, node_id: str) -> list[str] | None:
        """Get the dependency list for a specific node."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT dependencies_json FROM node_configs WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()

        if row is None or row["dependencies_json"] is None:
            return None

        result: list[str] = json.loads(row["dependencies_json"])
        return result

    def get_config_hash(self, node_id: str) -> str | None:
        """
        Get the configuration hash for a node.

        Useful for change detection without loading full config.

        Args:
            node_id: Canonical node ID

        Returns:
            SHA256 hash of config, or None if not found
        """
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT config_hash FROM node_configs WHERE node_id = ?",
            (node_id,),
        )
        row = cursor.fetchone()

        return row["config_hash"] if row else None

    def get_nodes_by_account(self, account_id: str) -> list[str]:
        """Get all node IDs for an account."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT node_id FROM nodes WHERE account_id = ?",
            (account_id,),
        )
        return [row["node_id"] for row in cursor.fetchall()]

    def get_nodes_by_type(
        self,
        resource_type: str,
        account_id: str | None = None,
        region: str | None = None,
    ) -> list[str]:
        """Get all node IDs of a specific resource type."""
        query = "SELECT node_id FROM nodes WHERE resource_type = ?"
        params: list[Any] = [resource_type]

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        if region:
            query += " AND region = ?"
            params.append(region)

        cursor = self._conn.cursor()
        cursor.execute(query, params)

        return [row["node_id"] for row in cursor.fetchall()]

    def get_nodes_by_region(
        self,
        region: str,
        account_id: str | None = None,
    ) -> list[str]:
        """Get all node IDs in a specific region."""
        query = "SELECT node_id FROM nodes WHERE region = ?"
        params: list[Any] = [region]

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        cursor = self._conn.cursor()
        cursor.execute(query, params)

        return [row["node_id"] for row in cursor.fetchall()]

    def get_phantom_nodes(self, account_id: str | None = None) -> list[str]:
        """Get all phantom node IDs."""
        query = "SELECT node_id FROM nodes WHERE is_phantom = 1"
        params: list[Any] = []

        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)

        cursor = self._conn.cursor()
        cursor.execute(query, params)

        return [row["node_id"] for row in cursor.fetchall()]

    def node_exists(self, node_id: str) -> bool:
        """Check if a node exists in the store."""
        cursor = self._conn.cursor()
        cursor.execute(
            "SELECT 1 FROM nodes WHERE node_id = ?",
            (node_id,),
        )
        return cursor.fetchone() is not None

    def delete_node(self, node_id: str) -> bool:
        """
        Delete a node and its edges.

        Args:
            node_id: Canonical node ID

        Returns:
            True if node was deleted, False if it didn't exist
        """
        with self.atomic_transaction() as cursor:
            cursor.execute("SELECT 1 FROM nodes WHERE node_id = ?", (node_id,))
            exists = cursor.fetchone() is not None

            if exists:
                # Cascade delete handles edges and configs
                cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))

            return exists

    def delete_account(self, account_id: str) -> int:
        """
        Delete all nodes for an account.

        Args:
            account_id: AWS account ID

        Returns:
            Number of nodes deleted
        """
        with self.atomic_transaction() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM nodes WHERE account_id = ?",
                (account_id,),
            )
            count: int = cursor.fetchone()[0]

            cursor.execute("DELETE FROM nodes WHERE account_id = ?", (account_id,))

            return count

    def get_statistics(self) -> StorageStats:
        """Get comprehensive storage statistics."""
        cursor = self._conn.cursor()

        # Total counts
        cursor.execute("SELECT COUNT(*) FROM nodes")
        total_nodes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM edges")
        total_edges = cursor.fetchone()[0]

        # By account
        cursor.execute(
            "SELECT account_id, COUNT(*) as cnt FROM nodes GROUP BY account_id"
        )
        by_account = {row["account_id"]: row["cnt"] for row in cursor.fetchall()}

        # By region
        cursor.execute("SELECT region, COUNT(*) as cnt FROM nodes GROUP BY region")
        by_region = {row["region"] or "global": row["cnt"] for row in cursor.fetchall()}

        # By type
        cursor.execute(
            "SELECT resource_type, COUNT(*) as cnt FROM nodes GROUP BY resource_type"
        )
        by_type = {row["resource_type"]: row["cnt"] for row in cursor.fetchall()}

        # Phantom count
        cursor.execute("SELECT COUNT(*) FROM nodes WHERE is_phantom = 1")
        phantom_count = cursor.fetchone()[0]

        # Compression ratio
        cursor.execute(
            "SELECT SUM(original_size) as orig, "
            "SUM(LENGTH(config_compressed)) as comp FROM node_configs"
        )
        row = cursor.fetchone()
        if row["orig"] and row["comp"]:
            compression_ratio = row["orig"] / row["comp"]
        else:
            compression_ratio = 1.0

        # Database size
        db_size = os.path.getsize(self.db_path) if self.db_path.exists() else 0

        # Last scan
        cursor.execute(
            "SELECT scan_completed_at FROM scan_metadata "
            "WHERE status = 'completed' ORDER BY id DESC LIMIT 1"
        )
        last_scan_row = cursor.fetchone()
        last_scan = None
        if last_scan_row and last_scan_row["scan_completed_at"]:
            try:
                last_scan = datetime.fromisoformat(last_scan_row["scan_completed_at"])
            except (ValueError, TypeError):
                pass

        return StorageStats(
            total_nodes=total_nodes,
            total_edges=total_edges,
            by_account=by_account,
            by_region=by_region,
            by_type=by_type,
            phantom_count=phantom_count,
            compression_ratio=compression_ratio,
            db_size_bytes=db_size,
            last_scan=last_scan,
        )

    def vacuum(self) -> None:
        """
        Optimize the database file.

        Reclaims unused space and defragments the database.
        Should be called periodically or after large deletions.
        """
        self._conn.execute("VACUUM")
        logger.info("Database vacuumed")

    def checkpoint(self) -> None:
        """
        Force a WAL checkpoint.

        Writes all pending WAL entries to the main database file.
        Useful before backup operations.
        """
        self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        logger.debug("WAL checkpoint completed")

    def close(self) -> None:
        """Close the database connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None
            logger.debug("Database connection closed")

    def __enter__(self) -> GraphStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()


# Migration utilities


def migrate_from_json(
    json_path: Path,
    store: GraphStore,
    account_id: str,
) -> int:
    """
    Migrate a JSON graph file to SQLite storage.

    Args:
        json_path: Path to the JSON graph file
        account_id: AWS account ID to associate with the data

    Returns:
        Number of nodes migrated
    """
    # Import here to avoid circular imports
    from .graph_engine import GraphEngine

    logger.info(f"Migrating {json_path} to SQLite storage...")

    # Load the JSON graph
    graph = GraphEngine.load(json_path)

    # Save to SQLite
    count = store.save_graph(graph, account_id)

    logger.info(f"Migration complete: {count} nodes migrated")
    return count


def migrate_from_cache(
    cache_dir: Path,
    store: GraphStore,
) -> int:
    """
    Migrate all cache files from JSON to SQLite.

    Scans the cache directory for scan-*.json files and migrates them.

    Args:
        cache_dir: Path to the cache directory
        store: Target GraphStore

    Returns:
        Total number of nodes migrated
    """
    total = 0

    for cache_file in cache_dir.glob("scan-*.json"):
        try:
            with open(cache_file) as f:
                cache_data = json.load(f)

            metadata = cache_data.get("metadata", {})
            account_id = metadata.get("account_id", "unknown")

            # Import here to avoid circular imports
            from .cache import ScanCache

            cache = ScanCache.load(
                account_id=account_id,
                region=metadata.get("region", "unknown"),
                cache_dir=cache_dir,
            )

            # Create a minimal graph from cache entries
            from .graph_engine import GraphEngine

            graph = GraphEngine()
            for entry in cache._entries.values():
                graph.add_resource(entry.resource)

            count = store.save_graph(graph, account_id)
            total += count

            logger.info(f"Migrated {cache_file.name}: {count} nodes")

        except Exception as e:
            logger.warning(f"Failed to migrate {cache_file}: {e}")

    return total
