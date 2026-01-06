"""
Unified SQLite graph storage backend.

Single backend for ALL scales:
- :memory: mode for ephemeral/fast scans
- file mode for persistent/large scans

Key Features:
- WAL mode for concurrency (file mode)
- FTS5 for full-text search
- Recursive CTEs for path finding
- Native backup() for snapshots
- Backpressure control for batch ops
- Thread-safe via connection pooling
- zlib compression for attributes (80-90% disk savings)
- Schema migration system (version-based upgrades)
- Scan session management (Ghost Fix)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import zlib
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import Edge, GraphBackend, Node, ResourceCategory, ScanSession, ScanStatus

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Current schema version - increment when schema changes
SCHEMA_VERSION = 2


def compress_json(data: dict[str, Any]) -> bytes:
    """Compress JSON data using zlib for storage."""
    json_str = json.dumps(data, separators=(",", ":"))
    return zlib.compress(json_str.encode("utf-8"), level=6)


def decompress_json(data: bytes | str) -> dict[str, Any]:
    """Decompress JSON data from zlib-compressed bytes."""
    if isinstance(data, str):
        # Legacy uncompressed data
        return json.loads(data) if data else {}
    try:
        decompressed = zlib.decompress(data)
        return json.loads(decompressed.decode("utf-8"))
    except zlib.error:
        # Not compressed, treat as plain JSON string
        return json.loads(data.decode("utf-8")) if data else {}


class ConnectionPool:
    """
    Thread-safe SQLite connection pool.

    Provides separate reader and writer connections for optimal concurrency.
    Uses thread-local storage for reader connections.

    Note: For :memory: mode, a single connection is shared for both reading
    and writing, because each SQLite :memory: connection creates a separate
    in-memory database.
    """

    def __init__(self, db_path: str, timeout: float = 60.0) -> None:
        self.db_path = db_path
        self.timeout = timeout
        self.is_memory = db_path == ":memory:"
        self._local = threading.local()
        self._writer_lock = threading.Lock()
        self._writer_conn: sqlite3.Connection | None = None

    def get_reader(self) -> sqlite3.Connection:
        """Get a thread-local reader connection."""
        # For memory mode, always use the shared writer connection
        # because each :memory: connection creates a separate database
        if self.is_memory:
            if self._writer_conn is None:
                self._writer_conn = self._create_connection(readonly=False)
            return self._writer_conn

        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection(readonly=True)
        return self._local.conn

    @contextmanager
    def get_writer(self) -> Iterator[sqlite3.Connection]:
        """Get the exclusive writer connection."""
        acquired = self._writer_lock.acquire(timeout=self.timeout)
        if not acquired:
            raise sqlite3.OperationalError(f"Write lock timeout after {self.timeout}s")

        try:
            if self._writer_conn is None:
                self._writer_conn = self._create_connection(readonly=False)
            yield self._writer_conn
        finally:
            self._writer_lock.release()

    def _create_connection(self, readonly: bool = False) -> sqlite3.Connection:
        """Create a new database connection with optimal settings."""
        if readonly and self.db_path != ":memory:":
            uri = f"file:{self.db_path}?mode=ro"
            conn = sqlite3.connect(
                uri, uri=True, timeout=self.timeout, check_same_thread=False
            )
        else:
            conn = sqlite3.connect(
                self.db_path, timeout=self.timeout, check_same_thread=False
            )

        conn.row_factory = sqlite3.Row

        # Performance pragmas
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
        conn.execute("PRAGMA temp_store = MEMORY")
        conn.execute("PRAGMA busy_timeout = 60000")  # 60s busy timeout
        conn.execute("PRAGMA foreign_keys = ON")

        return conn

    def get_raw_connection(self) -> sqlite3.Connection:
        """Get raw connection for backup operations."""
        if self._writer_conn:
            return self._writer_conn
        return self._create_connection(readonly=False)

    def close_all(self) -> None:
        """Close all connections."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
        if self._writer_conn:
            self._writer_conn.close()
            self._writer_conn = None


class SQLiteBackend(GraphBackend):
    """
    Unified SQLite graph backend.

    Works identically for both :memory: and file modes.
    The mode is determined solely by the db_path parameter.

    Example:
        # Memory mode (ephemeral)
        backend = SQLiteBackend(db_path=":memory:")

        # File mode (persistent)
        backend = SQLiteBackend(db_path="/path/to/graph.db")
    """

    # Base schema (v1)
    SCHEMA_SQL_V1 = """
    -- Nodes table
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        name TEXT,
        region TEXT,
        account_id TEXT,
        attributes BLOB NOT NULL DEFAULT X'789c636000',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        is_compute INTEGER DEFAULT 0,
        is_storage INTEGER DEFAULT 0,
        is_network INTEGER DEFAULT 0,
        is_security INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
    CREATE INDEX IF NOT EXISTS idx_nodes_region ON nodes(region);
    CREATE INDEX IF NOT EXISTS idx_nodes_name ON nodes(name);

    -- Full-text search
    CREATE VIRTUAL TABLE IF NOT EXISTS nodes_fts USING fts5(
        id, type, name,
        content='nodes',
        content_rowid='rowid',
        tokenize='porter unicode61'
    );

    -- FTS sync triggers
    CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
        INSERT INTO nodes_fts(rowid, id, type, name)
        VALUES (new.rowid, new.id, new.type, new.name);
    END;

    CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
        INSERT INTO nodes_fts(nodes_fts, rowid, id, type, name)
        VALUES('delete', old.rowid, old.id, old.type, old.name);
    END;

    CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
        INSERT INTO nodes_fts(nodes_fts, rowid, id, type, name)
        VALUES('delete', old.rowid, old.id, old.type, old.name);
        INSERT INTO nodes_fts(rowid, id, type, name)
        VALUES (new.rowid, new.id, new.type, new.name);
    END;

    -- Edges table
    CREATE TABLE IF NOT EXISTS edges (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        relation TEXT NOT NULL,
        attributes BLOB DEFAULT X'789c636000',
        weight REAL DEFAULT 1.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
        FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE,
        UNIQUE(source_id, target_id, relation)
    );

    CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id);
    CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id);

    -- Materialized node metrics
    CREATE TABLE IF NOT EXISTS node_metrics (
        node_id TEXT PRIMARY KEY,
        in_degree INTEGER DEFAULT 0,
        out_degree INTEGER DEFAULT 0,
        total_degree INTEGER DEFAULT 0,
        is_leaf INTEGER DEFAULT 0,
        is_root INTEGER DEFAULT 0,
        FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_metrics_degree ON node_metrics(total_degree DESC);

    -- Path cache
    CREATE TABLE IF NOT EXISTS path_cache (
        source_id TEXT,
        target_id TEXT,
        path_type TEXT,
        path_data TEXT NOT NULL,
        path_length INTEGER NOT NULL,
        expires_at TEXT,
        PRIMARY KEY (source_id, target_id, path_type)
    );

    -- Scan metadata (key-value store)
    CREATE TABLE IF NOT EXISTS scan_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    # Migration to v2: Add scan session support and phantom tracking
    SCHEMA_MIGRATION_V2 = """
    -- Add scan_id and phantom tracking to nodes
    ALTER TABLE nodes ADD COLUMN scan_id TEXT;
    ALTER TABLE nodes ADD COLUMN is_phantom INTEGER DEFAULT 0;
    ALTER TABLE nodes ADD COLUMN phantom_reason TEXT;
    CREATE INDEX IF NOT EXISTS idx_nodes_scan_id ON nodes(scan_id);
    CREATE INDEX IF NOT EXISTS idx_nodes_phantom ON nodes(is_phantom);

    -- Add scan_id to edges
    ALTER TABLE edges ADD COLUMN scan_id TEXT;
    CREATE INDEX IF NOT EXISTS idx_edges_scan_id ON edges(scan_id);

    -- Scan sessions table
    CREATE TABLE IF NOT EXISTS scan_sessions (
        id TEXT PRIMARY KEY,
        profile TEXT,
        region TEXT,
        status TEXT NOT NULL DEFAULT 'running',
        started_at TEXT NOT NULL,
        completed_at TEXT,
        resource_count INTEGER DEFAULT 0,
        error_message TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_scan_sessions_status ON scan_sessions(status);
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        enable_metrics: bool = True,
        backpressure_threshold: int = 5000,
        backpressure_sleep_ms: int = 10,
        enable_compression: bool = True,
    ) -> None:
        """
        Initialize SQLite backend.

        Args:
            db_path: ":memory:" for ephemeral, file path for persistent
            enable_metrics: Maintain materialized degree metrics
            backpressure_threshold: Yield to readers every N writes
            backpressure_sleep_ms: Sleep duration for backpressure
            enable_compression: Use zlib compression for attributes (saves 80-90% disk)
        """
        self.db_path = db_path
        self.is_memory = db_path == ":memory:"
        self.enable_metrics = enable_metrics
        self.backpressure_threshold = backpressure_threshold
        self.backpressure_sleep_ms = backpressure_sleep_ms
        self.enable_compression = enable_compression
        self._current_scan_id: str | None = None

        self._pool = ConnectionPool(db_path)
        self._init_schema()
        self._migrate_schema()

        mode = "memory" if self.is_memory else "file"
        logger.info(f"SQLite backend initialized ({mode} mode): {db_path}")

    def _init_schema(self) -> None:
        """Initialize database schema if tables don't exist."""
        with self._pool.get_writer() as conn:
            # Check if nodes table exists
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='nodes'"
            )
            if cursor.fetchone() is None:
                # Fresh database - create v1 schema
                conn.executescript(self.SCHEMA_SQL_V1)
                # Set initial schema version
                conn.execute(
                    "INSERT OR REPLACE INTO scan_metadata (key, value) VALUES (?, ?)",
                    ("schema_version", "1"),
                )
            conn.commit()

    def _migrate_schema(self) -> None:
        """Run schema migrations if needed."""
        current_version = self.get_schema_version()

        if current_version < 2:
            logger.info(f"Migrating schema from v{current_version} to v2...")
            with self._pool.get_writer() as conn:
                # Run v2 migration
                for statement in self.SCHEMA_MIGRATION_V2.strip().split(";"):
                    statement = statement.strip()
                    if statement:
                        try:
                            conn.execute(statement)
                        except sqlite3.OperationalError as e:
                            # Column/table may already exist
                            if (
                                "duplicate column" not in str(e).lower()
                                and "already exists" not in str(e).lower()
                            ):
                                logger.warning(f"Migration statement failed: {e}")
                # Update version
                conn.execute(
                    "INSERT OR REPLACE INTO scan_metadata (key, value) VALUES (?, ?)",
                    ("schema_version", "2"),
                )
                conn.commit()
            logger.info("Schema migration to v2 complete")

    def get_schema_version(self) -> int:
        """Get current database schema version."""
        conn = self._pool.get_reader()
        try:
            row = conn.execute(
                "SELECT value FROM scan_metadata WHERE key = 'schema_version'"
            ).fetchone()
            return int(row["value"]) if row else 1
        except sqlite3.OperationalError:
            # scan_metadata table might not exist
            return 0

    # =========================================================
    # NODE OPERATIONS
    # =========================================================

    def add_node(self, node: Node) -> None:
        """Add a single node to the graph (updates if exists)."""
        with self._pool.get_writer() as conn:
            try:
                self._insert_node(conn, node)
            except sqlite3.IntegrityError:
                self._update_node(conn, node)
            conn.commit()

    def add_nodes_batch(self, nodes: list[Node]) -> int:
        """Add multiple nodes in batch."""
        if not nodes:
            return 0

        count = 0
        with self._pool.get_writer() as conn:
            conn.execute("PRAGMA synchronous = OFF")

            try:
                batch_count = 0
                for node in nodes:
                    try:
                        self._insert_node(conn, node)
                        count += 1
                    except sqlite3.IntegrityError:
                        self._update_node(conn, node)
                        count += 1

                    batch_count += 1
                    if batch_count >= self.backpressure_threshold:
                        conn.commit()
                        if self.backpressure_sleep_ms > 0:
                            time.sleep(self.backpressure_sleep_ms / 1000.0)
                        batch_count = 0

                conn.commit()
            finally:
                conn.execute("PRAGMA synchronous = NORMAL")

            if self.enable_metrics:
                self._rebuild_metrics(conn)

        logger.info(f"Added {count} nodes")
        return count

    def _insert_node(self, conn: sqlite3.Connection, node: Node) -> None:
        """Insert a node into the database."""
        cat = node.category
        # Use compression if enabled
        if self.enable_compression:
            attrs = compress_json(node.attributes)
        else:
            attrs = json.dumps(node.attributes)
        # Use current scan_id if node doesn't have one
        scan_id = node.scan_id or self._current_scan_id
        conn.execute(
            """INSERT INTO nodes (id, type, name, region, account_id, attributes,
                                  is_compute, is_storage, is_network, is_security,
                                  scan_id, is_phantom, phantom_reason)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node.id,
                node.type,
                node.name,
                node.region,
                node.account_id,
                attrs,
                1 if cat == ResourceCategory.COMPUTE else 0,
                1 if cat == ResourceCategory.STORAGE else 0,
                1 if cat == ResourceCategory.NETWORK else 0,
                1 if cat == ResourceCategory.SECURITY else 0,
                scan_id,
                1 if node.is_phantom else 0,
                node.phantom_reason,
            ),
        )

    def _update_node(self, conn: sqlite3.Connection, node: Node) -> None:
        """Update an existing node."""
        cat = node.category
        if self.enable_compression:
            attrs = compress_json(node.attributes)
        else:
            attrs = json.dumps(node.attributes)
        scan_id = node.scan_id or self._current_scan_id
        conn.execute(
            """UPDATE nodes SET type=?, name=?, region=?, account_id=?, attributes=?,
                               is_compute=?, is_storage=?, is_network=?, is_security=?,
                               scan_id=?, is_phantom=?, phantom_reason=?,
                               updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                node.type,
                node.name,
                node.region,
                node.account_id,
                attrs,
                1 if cat == ResourceCategory.COMPUTE else 0,
                1 if cat == ResourceCategory.STORAGE else 0,
                1 if cat == ResourceCategory.NETWORK else 0,
                1 if cat == ResourceCategory.SECURITY else 0,
                scan_id,
                1 if node.is_phantom else 0,
                node.phantom_reason,
                node.id,
            ),
        )

    def get_node(self, node_id: str) -> Node | None:
        """Get a node by ID."""
        conn = self._pool.get_reader()
        row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return self._row_to_node(row) if row else None

    def get_nodes_by_type(self, node_type: str) -> list[Node]:
        """Get all nodes of a specific type."""
        conn = self._pool.get_reader()
        rows = conn.execute(
            "SELECT * FROM nodes WHERE type = ?", (node_type,)
        ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def search_nodes(self, query: str, limit: int = 100) -> list[Node]:
        """Search nodes using full-text search."""
        conn = self._pool.get_reader()
        safe_query = query.replace('"', "").strip()

        try:
            if self.enable_metrics:
                rows = conn.execute(
                    """SELECT n.*, COALESCE(m.total_degree, 0) as deg
                       FROM nodes n
                       JOIN nodes_fts fts ON n.rowid = fts.rowid
                       LEFT JOIN node_metrics m ON n.id = m.node_id
                       WHERE nodes_fts MATCH ?
                       ORDER BY (bm25(nodes_fts) * -10) + (deg * 0.1) DESC
                       LIMIT ?""",
                    (safe_query, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT n.* FROM nodes n
                       JOIN nodes_fts fts ON n.rowid = fts.rowid
                       WHERE nodes_fts MATCH ?
                       LIMIT ?""",
                    (safe_query, limit),
                ).fetchall()
            return [self._row_to_node(row) for row in rows]
        except sqlite3.OperationalError:
            # Fallback to LIKE search
            like = f"%{query}%"
            rows = conn.execute(
                "SELECT * FROM nodes WHERE id LIKE ? OR name LIKE ? LIMIT ?",
                (like, like, limit),
            ).fetchall()
            return [self._row_to_node(row) for row in rows]

    def node_count(self) -> int:
        """Get total number of nodes."""
        conn = self._pool.get_reader()
        result = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()
        return result[0] if result else 0

    def get_all_nodes(self) -> Iterator[Node]:
        """Iterate over all nodes."""
        conn = self._pool.get_reader()
        cursor = conn.execute("SELECT * FROM nodes")
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield self._row_to_node(row)

    def _row_to_node(self, row: sqlite3.Row) -> Node:
        """Convert a database row to a Node object."""
        # Handle both compressed (bytes) and uncompressed (str) attributes
        attrs_raw = row["attributes"]
        if attrs_raw:
            attributes = decompress_json(attrs_raw)
        else:
            attributes = {}

        # Handle new fields that may not exist in older schema
        scan_id = row["scan_id"] if "scan_id" in row.keys() else None
        is_phantom = bool(row["is_phantom"]) if "is_phantom" in row.keys() else False
        phantom_reason = (
            row["phantom_reason"] if "phantom_reason" in row.keys() else None
        )

        return Node(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            region=row["region"],
            account_id=row["account_id"],
            attributes=attributes,
            scan_id=scan_id,
            is_phantom=is_phantom,
            phantom_reason=phantom_reason,
        )

    # =========================================================
    # EDGE OPERATIONS
    # =========================================================

    def add_edge(self, edge: Edge) -> None:
        """Add a single edge to the graph."""
        if self.enable_compression:
            attrs = compress_json(edge.attributes)
        else:
            attrs = json.dumps(edge.attributes)
        scan_id = edge.scan_id or self._current_scan_id
        with self._pool.get_writer() as conn:
            conn.execute(
                """INSERT INTO edges (source_id, target_id, relation, attributes, weight, scan_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    edge.source_id,
                    edge.target_id,
                    edge.relation,
                    attrs,
                    edge.weight,
                    scan_id,
                ),
            )
            conn.commit()

    def add_edges_batch(self, edges: list[Edge]) -> int:
        """Add multiple edges in batch."""
        if not edges:
            return 0

        count = 0
        with self._pool.get_writer() as conn:
            conn.execute("PRAGMA synchronous = OFF")
            try:
                batch_count = 0
                for edge in edges:
                    if self.enable_compression:
                        attrs = compress_json(edge.attributes)
                    else:
                        attrs = json.dumps(edge.attributes)
                    scan_id = edge.scan_id or self._current_scan_id
                    try:
                        conn.execute(
                            """INSERT INTO edges
                               (source_id, target_id, relation, attributes, weight, scan_id)
                               VALUES (?, ?, ?, ?, ?, ?)""",
                            (
                                edge.source_id,
                                edge.target_id,
                                edge.relation,
                                attrs,
                                edge.weight,
                                scan_id,
                            ),
                        )
                        count += 1
                    except sqlite3.IntegrityError:
                        # Duplicate edge, skip
                        pass

                    batch_count += 1
                    if batch_count >= self.backpressure_threshold:
                        conn.commit()
                        if self.backpressure_sleep_ms > 0:
                            time.sleep(self.backpressure_sleep_ms / 1000.0)
                        batch_count = 0

                conn.commit()
            finally:
                conn.execute("PRAGMA synchronous = NORMAL")

            if self.enable_metrics:
                self._rebuild_metrics(conn)

        logger.info(f"Added {count} edges")
        return count

    def get_edges_from(self, node_id: str) -> list[Edge]:
        """Get all edges originating from a node."""
        conn = self._pool.get_reader()
        rows = conn.execute(
            "SELECT * FROM edges WHERE source_id = ?", (node_id,)
        ).fetchall()
        return [self._row_to_edge(row) for row in rows]

    def get_edges_to(self, node_id: str) -> list[Edge]:
        """Get all edges pointing to a node."""
        conn = self._pool.get_reader()
        rows = conn.execute(
            "SELECT * FROM edges WHERE target_id = ?", (node_id,)
        ).fetchall()
        return [self._row_to_edge(row) for row in rows]

    def edge_count(self) -> int:
        """Get total number of edges."""
        conn = self._pool.get_reader()
        result = conn.execute("SELECT COUNT(*) FROM edges").fetchone()
        return result[0] if result else 0

    def get_all_edges(self) -> Iterator[Edge]:
        """Iterate over all edges."""
        conn = self._pool.get_reader()
        cursor = conn.execute("SELECT * FROM edges")
        while True:
            rows = cursor.fetchmany(1000)
            if not rows:
                break
            for row in rows:
                yield self._row_to_edge(row)

    def _row_to_edge(self, row: sqlite3.Row) -> Edge:
        """Convert a database row to an Edge object."""
        # Handle both compressed (bytes) and uncompressed (str) attributes
        attrs_raw = row["attributes"]
        if attrs_raw:
            attributes = decompress_json(attrs_raw)
        else:
            attributes = {}

        # Handle scan_id field that may not exist in older schema
        scan_id = row["scan_id"] if "scan_id" in row.keys() else None

        return Edge(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=row["relation"],
            attributes=attributes,
            weight=row["weight"],
            scan_id=scan_id,
        )

    # =========================================================
    # TRAVERSAL (SQL Recursive CTEs)
    # =========================================================

    def get_neighbors(self, node_id: str, direction: str = "both") -> list[Node]:
        """Get neighboring nodes."""
        conn = self._pool.get_reader()

        if direction == "out":
            sql = """SELECT n.* FROM nodes n
                     JOIN edges e ON n.id = e.target_id
                     WHERE e.source_id = ?"""
            rows = conn.execute(sql, (node_id,)).fetchall()
        elif direction == "in":
            sql = """SELECT n.* FROM nodes n
                     JOIN edges e ON n.id = e.source_id
                     WHERE e.target_id = ?"""
            rows = conn.execute(sql, (node_id,)).fetchall()
        else:  # both
            sql = """SELECT DISTINCT n.* FROM nodes n WHERE n.id IN (
                        SELECT target_id FROM edges WHERE source_id = ?
                        UNION SELECT source_id FROM edges WHERE target_id = ?)"""
            rows = conn.execute(sql, (node_id, node_id)).fetchall()

        return [self._row_to_node(row) for row in rows]

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 10,
    ) -> list[str] | None:
        """
        Find shortest path using Recursive CTE with safety guards.

        Uses BFS via recursive CTE to find the shortest path.
        Returns None if no path exists.
        """
        conn = self._pool.get_reader()

        sql = """
        WITH RECURSIVE path_finder(node_id, path, depth) AS (
            SELECT ?, json_array(?), 0
            UNION ALL
            SELECT e.target_id, json_insert(pf.path, '$[#]', e.target_id), pf.depth + 1
            FROM path_finder pf
            JOIN edges e ON e.source_id = pf.node_id
            WHERE pf.depth < ?
            AND json_array_length(pf.path) < 20
            AND instr(pf.path, '"' || e.target_id || '"') = 0
        )
        SELECT path FROM path_finder WHERE node_id = ? ORDER BY depth LIMIT 1
        """

        try:
            row = conn.execute(
                sql, (source_id, source_id, max_depth, target_id)
            ).fetchone()
            if row:
                result: list[str] = json.loads(row["path"])
                return result
            return None
        except sqlite3.OperationalError:
            return None

    # =========================================================
    # ANALYTICS
    # =========================================================

    def get_node_degree(self, node_id: str) -> tuple[int, int]:
        """Get (in_degree, out_degree) for a node."""
        if self.enable_metrics:
            conn = self._pool.get_reader()
            row = conn.execute(
                "SELECT in_degree, out_degree FROM node_metrics WHERE node_id = ?",
                (node_id,),
            ).fetchone()
            if row:
                return (row["in_degree"], row["out_degree"])

        # Fallback to direct query
        conn = self._pool.get_reader()
        in_deg_row = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE target_id = ?", (node_id,)
        ).fetchone()
        out_deg_row = conn.execute(
            "SELECT COUNT(*) FROM edges WHERE source_id = ?", (node_id,)
        ).fetchone()
        return (
            in_deg_row[0] if in_deg_row else 0,
            out_deg_row[0] if out_deg_row else 0,
        )

    def get_high_degree_nodes(self, top_n: int = 10) -> list[tuple[Node, int]]:
        """Get nodes with highest total degree."""
        conn = self._pool.get_reader()

        if self.enable_metrics:
            rows = conn.execute(
                """SELECT n.*, m.total_degree FROM nodes n
                   JOIN node_metrics m ON n.id = m.node_id
                   ORDER BY m.total_degree DESC LIMIT ?""",
                (top_n,),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT n.*,
                      (SELECT COUNT(*) FROM edges WHERE source_id = n.id) +
                      (SELECT COUNT(*) FROM edges WHERE target_id = n.id) as total_degree
                   FROM nodes n ORDER BY total_degree DESC LIMIT ?""",
                (top_n,),
            ).fetchall()

        return [(self._row_to_node(row), row["total_degree"]) for row in rows]

    def _rebuild_metrics(self, conn: sqlite3.Connection) -> None:
        """Rebuild materialized metrics table."""
        if not self.enable_metrics:
            return

        conn.execute("DELETE FROM node_metrics")
        conn.execute(
            """
            INSERT INTO node_metrics (node_id, in_degree, out_degree, total_degree, is_leaf, is_root)
            SELECT n.id,
                   COALESCE(i.cnt, 0),
                   COALESCE(o.cnt, 0),
                   COALESCE(i.cnt, 0) + COALESCE(o.cnt, 0),
                   CASE WHEN COALESCE(o.cnt, 0) = 0 THEN 1 ELSE 0 END,
                   CASE WHEN COALESCE(i.cnt, 0) = 0 THEN 1 ELSE 0 END
            FROM nodes n
            LEFT JOIN (SELECT target_id, COUNT(*) cnt FROM edges GROUP BY target_id) i ON n.id = i.target_id
            LEFT JOIN (SELECT source_id, COUNT(*) cnt FROM edges GROUP BY source_id) o ON n.id = o.source_id
        """
        )
        conn.commit()

    # =========================================================
    # SNAPSHOT (Unified for memory and file modes)
    # =========================================================

    def snapshot(self, target_path: str) -> None:
        """
        Create a snapshot using SQLite's native backup API.

        Works identically for both :memory: and file modes.
        This is the KEY feature that justifies unified SQLite architecture.
        """
        source_conn = self._pool.get_raw_connection()
        target_conn = sqlite3.connect(target_path)

        try:
            source_conn.backup(target_conn)
            logger.info(f"Snapshot created: {target_path}")
        finally:
            target_conn.close()

    @classmethod
    def load_snapshot(cls, snapshot_path: str) -> SQLiteBackend:
        """Load a snapshot file as a new backend instance."""
        if not Path(snapshot_path).exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        return cls(db_path=snapshot_path)

    # =========================================================
    # PERSISTENCE
    # =========================================================

    def clear(self) -> None:
        """Clear all data from the backend."""
        with self._pool.get_writer() as conn:
            conn.execute("DELETE FROM path_cache")
            conn.execute("DELETE FROM node_metrics")
            conn.execute("DELETE FROM edges")
            conn.execute("DELETE FROM nodes")
            conn.execute("DELETE FROM scan_metadata")
            conn.commit()

    def close(self) -> None:
        """Close all connections."""
        self._pool.close_all()

    # =========================================================
    # METADATA
    # =========================================================

    def set_metadata(self, key: str, value: str) -> None:
        """Set a metadata key-value pair."""
        with self._pool.get_writer() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO scan_metadata (key, value, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)""",
                (key, value),
            )
            conn.commit()

    def get_metadata(self, key: str) -> str | None:
        """Get a metadata value by key."""
        conn = self._pool.get_reader()
        row = conn.execute(
            "SELECT value FROM scan_metadata WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else None

    # =========================================================
    # STATISTICS
    # =========================================================

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive statistics about the backend."""
        conn = self._pool.get_reader()

        page_count_row = conn.execute("PRAGMA page_count").fetchone()
        page_size_row = conn.execute("PRAGMA page_size").fetchone()
        page_count = page_count_row[0] if page_count_row else 0
        page_size = page_size_row[0] if page_size_row else 4096

        type_stats: dict[str, int] = {}
        for row in conn.execute(
            "SELECT type, COUNT(*) cnt FROM nodes GROUP BY type ORDER BY cnt DESC"
        ):
            type_stats[row["type"]] = row["cnt"]

        return {
            "mode": "memory" if self.is_memory else "file",
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "database_size_mb": round((page_count * page_size) / (1024 * 1024), 2),
            "type_distribution": type_stats,
            "schema_version": self.get_schema_version(),
            "compression_enabled": self.enable_compression,
        }

    # =========================================================
    # SCAN SESSION MANAGEMENT (Ghost Fix)
    # =========================================================

    def start_scan(
        self, profile: str | None = None, region: str | None = None
    ) -> ScanSession:
        """
        Start a new scan session.

        Creates a scan session record and sets the current scan ID.
        All nodes/edges added during this session will be tagged with scan_id.

        Args:
            profile: AWS profile being scanned
            region: AWS region being scanned

        Returns:
            ScanSession object with unique ID
        """
        session = ScanSession(profile=profile, region=region)
        self._current_scan_id = session.id

        with self._pool.get_writer() as conn:
            conn.execute(
                """INSERT INTO scan_sessions
                   (id, profile, region, status, started_at, resource_count)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    session.id,
                    session.profile,
                    session.region,
                    session.status.value,
                    session.started_at.isoformat(),
                    0,
                ),
            )
            conn.commit()

        logger.info(f"Started scan session: {session.id}")
        return session

    def end_scan(
        self, scan_id: str, success: bool = True, error: str | None = None
    ) -> None:
        """
        End a scan session.

        Updates the session status and resource count.

        Args:
            scan_id: The scan session ID to end
            success: Whether the scan completed successfully
            error: Error message if failed
        """
        status = ScanStatus.COMPLETED if success else ScanStatus.FAILED
        completed_at = datetime.now(UTC).isoformat()

        # Count resources added in this scan
        conn = self._pool.get_reader()
        count_row = conn.execute(
            "SELECT COUNT(*) FROM nodes WHERE scan_id = ?", (scan_id,)
        ).fetchone()
        resource_count = count_row[0] if count_row else 0

        with self._pool.get_writer() as conn:
            conn.execute(
                """UPDATE scan_sessions
                   SET status = ?, completed_at = ?, resource_count = ?, error_message = ?
                   WHERE id = ?""",
                (status.value, completed_at, resource_count, error, scan_id),
            )
            conn.commit()

        if self._current_scan_id == scan_id:
            self._current_scan_id = None

        logger.info(
            f"Ended scan session: {scan_id} ({status.value}, {resource_count} resources)"
        )

    def get_scan_session(self, scan_id: str) -> ScanSession | None:
        """Get a scan session by ID."""
        conn = self._pool.get_reader()
        row = conn.execute(
            "SELECT * FROM scan_sessions WHERE id = ?", (scan_id,)
        ).fetchone()

        if not row:
            return None

        return ScanSession(
            id=row["id"],
            profile=row["profile"],
            region=row["region"],
            status=ScanStatus(row["status"]),
            started_at=datetime.fromisoformat(row["started_at"]),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            resource_count=row["resource_count"],
            error_message=row["error_message"],
        )

    def get_phantom_nodes(self) -> list[Node]:
        """
        Get all phantom (placeholder) nodes.

        Phantom nodes are created when an edge references a node that doesn't exist,
        typically due to cross-account references or partial scans.
        """
        conn = self._pool.get_reader()
        rows = conn.execute("SELECT * FROM nodes WHERE is_phantom = 1").fetchall()
        return [self._row_to_node(row) for row in rows]

    def cleanup_stale_resources(self, current_scan_id: str) -> int:
        """
        Remove resources not seen in the current scan.

        This is the "Ghost Fix" - removes stale resources from previous scans
        that no longer exist in AWS.

        Args:
            current_scan_id: The current scan session ID

        Returns:
            Number of resources removed
        """
        with self._pool.get_writer() as conn:
            # Count stale resources
            count_row = conn.execute(
                """SELECT COUNT(*) FROM nodes
                   WHERE scan_id != ? AND scan_id IS NOT NULL AND is_phantom = 0""",
                (current_scan_id,),
            ).fetchone()
            stale_count = count_row[0] if count_row else 0

            if stale_count > 0:
                # Delete stale resources (edges cascade via FK)
                conn.execute(
                    """DELETE FROM nodes
                       WHERE scan_id != ? AND scan_id IS NOT NULL AND is_phantom = 0""",
                    (current_scan_id,),
                )
                conn.commit()

                if self.enable_metrics:
                    self._rebuild_metrics(conn)

                logger.info(f"Cleaned up {stale_count} stale resources")

        return stale_count

    def add_phantom_node(
        self,
        node_id: str,
        node_type: str,
        reason: str = "cross-account reference",
    ) -> Node:
        """
        Add a phantom (placeholder) node for a missing dependency.

        Args:
            node_id: The ID of the missing node
            node_type: Inferred type of the node
            reason: Why this is a phantom (e.g., "cross-account reference")

        Returns:
            The created phantom Node
        """
        node = Node(
            id=node_id,
            type=node_type,
            is_phantom=True,
            phantom_reason=reason,
            scan_id=self._current_scan_id,
        )
        self.add_node(node)
        return node

    def resolve_phantom(self, node_id: str, real_node: Node) -> bool:
        """
        Replace a phantom node with a real node.

        Called when a phantom node is discovered to exist
        (e.g., during a subsequent scan of a different account).

        Args:
            node_id: ID of the phantom node
            real_node: The real node to replace it with

        Returns:
            True if phantom was replaced, False if not found
        """
        existing = self.get_node(node_id)
        if not existing or not existing.is_phantom:
            return False

        # Update with real node data
        real_node.is_phantom = False
        real_node.phantom_reason = None
        with self._pool.get_writer() as conn:
            self._update_node(conn, real_node)
            conn.commit()

        logger.info(f"Resolved phantom node: {node_id}")
        return True
