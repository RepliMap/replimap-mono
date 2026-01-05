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
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from .base import Edge, GraphBackend, Node, ResourceCategory

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Thread-safe SQLite connection pool.

    Provides separate reader and writer connections for optimal concurrency.
    Uses thread-local storage for reader connections.
    """

    def __init__(self, db_path: str, timeout: float = 60.0) -> None:
        self.db_path = db_path
        self.timeout = timeout
        self._local = threading.local()
        self._writer_lock = threading.Lock()
        self._writer_conn: sqlite3.Connection | None = None

    def get_reader(self) -> sqlite3.Connection:
        """Get a thread-local reader connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._create_connection(readonly=True)
        return self._local.conn

    @contextmanager
    def get_writer(self) -> Iterator[sqlite3.Connection]:
        """Get the exclusive writer connection."""
        acquired = self._writer_lock.acquire(timeout=self.timeout)
        if not acquired:
            raise sqlite3.OperationalError(
                f"Write lock timeout after {self.timeout}s"
            )

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

    SCHEMA_SQL = """
    -- Nodes table
    CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        type TEXT NOT NULL,
        name TEXT,
        region TEXT,
        account_id TEXT,
        attributes TEXT NOT NULL DEFAULT '{}',
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
        attributes TEXT DEFAULT '{}',
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

    -- Scan metadata
    CREATE TABLE IF NOT EXISTS scan_metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """

    def __init__(
        self,
        db_path: str = ":memory:",
        enable_metrics: bool = True,
        backpressure_threshold: int = 5000,
        backpressure_sleep_ms: int = 10,
    ) -> None:
        """
        Initialize SQLite backend.

        Args:
            db_path: ":memory:" for ephemeral, file path for persistent
            enable_metrics: Maintain materialized degree metrics
            backpressure_threshold: Yield to readers every N writes
            backpressure_sleep_ms: Sleep duration for backpressure
        """
        self.db_path = db_path
        self.is_memory = db_path == ":memory:"
        self.enable_metrics = enable_metrics
        self.backpressure_threshold = backpressure_threshold
        self.backpressure_sleep_ms = backpressure_sleep_ms

        self._pool = ConnectionPool(db_path)
        self._init_schema()

        mode = "memory" if self.is_memory else "file"
        logger.info(f"SQLite backend initialized ({mode} mode): {db_path}")

    def _init_schema(self) -> None:
        """Initialize database schema."""
        with self._pool.get_writer() as conn:
            conn.executescript(self.SCHEMA_SQL)
            conn.commit()

    # =========================================================
    # NODE OPERATIONS
    # =========================================================

    def add_node(self, node: Node) -> None:
        """Add a single node to the graph."""
        with self._pool.get_writer() as conn:
            self._insert_node(conn, node)
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
        conn.execute(
            """INSERT INTO nodes (id, type, name, region, account_id, attributes,
                                  is_compute, is_storage, is_network, is_security)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                node.id,
                node.type,
                node.name,
                node.region,
                node.account_id,
                json.dumps(node.attributes),
                1 if cat == ResourceCategory.COMPUTE else 0,
                1 if cat == ResourceCategory.STORAGE else 0,
                1 if cat == ResourceCategory.NETWORK else 0,
                1 if cat == ResourceCategory.SECURITY else 0,
            ),
        )

    def _update_node(self, conn: sqlite3.Connection, node: Node) -> None:
        """Update an existing node."""
        cat = node.category
        conn.execute(
            """UPDATE nodes SET type=?, name=?, region=?, account_id=?, attributes=?,
                               is_compute=?, is_storage=?, is_network=?, is_security=?,
                               updated_at=CURRENT_TIMESTAMP
               WHERE id=?""",
            (
                node.type,
                node.name,
                node.region,
                node.account_id,
                json.dumps(node.attributes),
                1 if cat == ResourceCategory.COMPUTE else 0,
                1 if cat == ResourceCategory.STORAGE else 0,
                1 if cat == ResourceCategory.NETWORK else 0,
                1 if cat == ResourceCategory.SECURITY else 0,
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
        return Node(
            id=row["id"],
            type=row["type"],
            name=row["name"],
            region=row["region"],
            account_id=row["account_id"],
            attributes=json.loads(row["attributes"]) if row["attributes"] else {},
        )

    # =========================================================
    # EDGE OPERATIONS
    # =========================================================

    def add_edge(self, edge: Edge) -> None:
        """Add a single edge to the graph."""
        with self._pool.get_writer() as conn:
            conn.execute(
                """INSERT INTO edges (source_id, target_id, relation, attributes, weight)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    edge.source_id,
                    edge.target_id,
                    edge.relation,
                    json.dumps(edge.attributes),
                    edge.weight,
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
                    try:
                        conn.execute(
                            """INSERT INTO edges
                               (source_id, target_id, relation, attributes, weight)
                               VALUES (?, ?, ?, ?, ?)""",
                            (
                                edge.source_id,
                                edge.target_id,
                                edge.relation,
                                json.dumps(edge.attributes),
                                edge.weight,
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
        return Edge(
            source_id=row["source_id"],
            target_id=row["target_id"],
            relation=row["relation"],
            attributes=json.loads(row["attributes"]) if row["attributes"] else {},
            weight=row["weight"],
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
        return (in_deg_row[0] if in_deg_row else 0, out_deg_row[0] if out_deg_row else 0)

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
        }
