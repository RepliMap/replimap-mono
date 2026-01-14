"""
Graph caching layer for RepliMap CLI.

Enables instant graph/deps/clone/cost/audit after initial scan by caching
the scan results to disk. Cache is per profile/region/vpc combination.

Storage: Uses SQLite via UnifiedGraphEngine for persistent storage.
Legacy JSON files are auto-migrated on first read.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rich.table import Table

if TYPE_CHECKING:
    from rich.console import Console

    from replimap.core.unified_storage import GraphEngineAdapter

logger = logging.getLogger(__name__)

# Directory structure
REPLIMAP_ROOT = Path.home() / ".replimap"
CACHE_DIR = REPLIMAP_ROOT / "cache"
GRAPH_CACHE_DIR = CACHE_DIR / "graphs"

# Default cache TTL: 1 hour
DEFAULT_CACHE_TTL = 3600

# Cache format version (incremented for SQLite migration)
CACHE_VERSION = "2.0"
LEGACY_CACHE_VERSION = "1.0"


class CacheManager:
    """Manages cached scan results per profile/region/vpc combination."""

    def __init__(
        self,
        profile: str,
        region: str,
        vpc: str | None = None,
        account_id: str | None = None,
    ):
        """
        Initialize cache manager.

        Args:
            profile: AWS profile name
            region: AWS region
            vpc: Optional VPC filter
            account_id: Optional AWS account ID for cache key
        """
        self.profile = profile or "default"
        self.region = region
        self.vpc = vpc
        self.account_id = account_id

        # Ensure cache directory exists
        GRAPH_CACHE_DIR.mkdir(parents=True, exist_ok=True)

        # Build cache filename (sanitize profile name)
        safe_profile = self.profile.replace("/", "_").replace("\\", "_")
        if vpc:
            base_filename = f"graph_{safe_profile}_{region}_{vpc}"
        else:
            base_filename = f"graph_{safe_profile}_{region}"

        # New SQLite path (primary)
        self.cache_path = GRAPH_CACHE_DIR / f"{base_filename}.db"
        # Legacy JSON path (for migration)
        self.legacy_json_path = GRAPH_CACHE_DIR / f"{base_filename}.json"

    def save(
        self,
        graph: GraphEngineAdapter,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Save graph to SQLite cache file.

        Uses SQLite's native backup API for efficient O(1) copy when possible,
        falling back to batch operations otherwise.

        Args:
            graph: The GraphEngineAdapter to cache
            metadata: Optional additional metadata

        Returns:
            True if successful, False otherwise
        """
        from replimap.core.unified_storage import GraphEngineAdapter, UnifiedGraphEngine

        try:
            start = time.time()

            # Get resource counts
            node_count = graph.node_count
            edge_count = graph.edge_count

            # Use temporary path then rename for atomicity
            temp_path = self.cache_path.with_suffix(".tmp.db")
            if temp_path.exists():
                temp_path.unlink()

            # Fast path: Use SQLite's native backup API if graph uses SQLite backend
            if isinstance(graph, GraphEngineAdapter) and hasattr(
                graph._engine, "_backend"
            ):
                # Direct snapshot from in-memory SQLite to file
                graph._engine._backend.snapshot(str(temp_path))

                # Now open the snapshot and add metadata
                engine = UnifiedGraphEngine(db_path=str(temp_path))
                try:
                    engine.set_metadata("version", CACHE_VERSION)
                    engine.set_metadata("timestamp", str(time.time()))
                    engine.set_metadata("profile", self.profile)
                    engine.set_metadata("region", self.region)
                    if self.vpc:
                        engine.set_metadata("vpc", self.vpc)
                    if self.account_id:
                        engine.set_metadata("account_id", self.account_id)
                    engine.set_metadata("resource_count", str(node_count))
                    engine.set_metadata("dependency_count", str(edge_count))

                    # Store additional metadata
                    if metadata:
                        for key, value in metadata.items():
                            engine.set_metadata(f"extra_{key}", str(value))
                finally:
                    engine.close()
            else:
                # Slow path: Copy nodes and edges using batch operations
                engine = UnifiedGraphEngine(db_path=str(temp_path))

                try:
                    if isinstance(graph, GraphEngineAdapter):
                        # Use batch operations for better performance
                        nodes = list(graph._engine.get_all_nodes())
                        edges = list(graph._engine.get_all_edges())

                        engine.add_nodes(nodes)
                        engine.add_edges(edges)
                    else:
                        # Legacy GraphEngine - convert to dict and load
                        data = graph.to_dict()
                        from replimap.core.unified_storage.base import Edge
                        from replimap.core.unified_storage.migrate import (
                            _convert_node_data,
                        )

                        nodes = [_convert_node_data(n) for n in data.get("nodes", [])]
                        engine.add_nodes(nodes)

                        edges = [
                            Edge(
                                source_id=e["source"],
                                target_id=e["target"],
                                relation=e.get("relation", "belongs_to"),
                            )
                            for e in data.get("edges", [])
                        ]
                        engine.add_edges(edges)

                    # Store metadata
                    engine.set_metadata("version", CACHE_VERSION)
                    engine.set_metadata("timestamp", str(time.time()))
                    engine.set_metadata("profile", self.profile)
                    engine.set_metadata("region", self.region)
                    if self.vpc:
                        engine.set_metadata("vpc", self.vpc)
                    if self.account_id:
                        engine.set_metadata("account_id", self.account_id)
                    engine.set_metadata("resource_count", str(node_count))
                    engine.set_metadata("dependency_count", str(edge_count))

                    # Store additional metadata
                    if metadata:
                        for key, value in metadata.items():
                            engine.set_metadata(f"extra_{key}", str(value))

                finally:
                    engine.close()

            # Atomic rename
            if self.cache_path.exists():
                self.cache_path.unlink()
            temp_path.rename(self.cache_path)

            duration = time.time() - start
            logger.debug(f"Graph cached in {duration:.2f}s to {self.cache_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to cache graph: {e}")
            # Clean up temp file if it exists
            if temp_path.exists():
                temp_path.unlink()
            return False

    def load(
        self, max_age: int = DEFAULT_CACHE_TTL
    ) -> tuple[GraphEngineAdapter, dict[str, Any]] | None:
        """
        Load graph from cache if valid.

        Supports both SQLite (new) and JSON (legacy) formats.
        Legacy JSON files are auto-migrated to SQLite on read.

        Args:
            max_age: Maximum cache age in seconds

        Returns:
            Tuple of (GraphEngineAdapter, meta_info) if cache valid, None otherwise
        """

        # Try SQLite cache first
        if self.cache_path.exists():
            result = self._load_sqlite(max_age)
            if result:
                return result

        # Try legacy JSON and migrate
        if self.legacy_json_path.exists():
            result = self._load_and_migrate_json(max_age)
            if result:
                return result

        logger.debug(f"Cache miss: no cache found for {self.profile}/{self.region}")
        return None

    def _load_sqlite(
        self, max_age: int
    ) -> tuple[GraphEngineAdapter, dict[str, Any]] | None:
        """Load from SQLite cache."""
        from replimap.core.unified_storage import GraphEngineAdapter

        try:
            # Create adapter directly - this opens the database once
            adapter = GraphEngineAdapter(db_path=str(self.cache_path))
            engine = adapter._engine  # Access underlying engine for metadata

            # Read metadata
            version = engine.get_metadata("version")
            timestamp_str = engine.get_metadata("timestamp")
            profile = engine.get_metadata("profile")
            region = engine.get_metadata("region")
            vpc = engine.get_metadata("vpc")
            resource_count_str = engine.get_metadata("resource_count")
            dependency_count_str = engine.get_metadata("dependency_count")

            # Version check - handle schema migration case
            if version != CACHE_VERSION:
                # Check if this is a migrated database (schema v2 but old cache version)
                schema_version = engine.get_schema_version()
                if schema_version >= 2 and version in (None, "1.0", LEGACY_CACHE_VERSION):
                    # Schema was just migrated, update cache version metadata
                    logger.debug(
                        f"Updating cache version from {version} to {CACHE_VERSION} "
                        f"after schema migration"
                    )
                    engine.set_metadata("version", CACHE_VERSION)
                    version = CACHE_VERSION
                else:
                    logger.debug("Cache version mismatch, invalidating")
                    adapter.close()
                    return None

            # Expiry check
            timestamp = float(timestamp_str) if timestamp_str else 0
            age = time.time() - timestamp
            if age > max_age:
                logger.debug(f"Cache expired (age: {age:.0f}s > {max_age}s)")
                adapter.close()
                return None

            # Profile/region match
            if profile != self.profile or region != self.region:
                logger.debug("Cache profile/region mismatch")
                adapter.close()
                return None

            # VPC match (if specified)
            if self.vpc and vpc != self.vpc:
                logger.debug("Cache VPC mismatch")
                adapter.close()
                return None

            # Build metadata dict
            meta = {
                "version": version,
                "timestamp": timestamp,
                "profile": profile,
                "region": region,
                "vpc": vpc,
                "account_id": engine.get_metadata("account_id"),
                "resource_count": int(resource_count_str) if resource_count_str else 0,
                "dependency_count": (
                    int(dependency_count_str) if dependency_count_str else 0
                ),
                "age_seconds": age,
                "age_human": self._format_age(age),
                "cache_path": str(self.cache_path),
                "format": "sqlite",
            }

            logger.debug(
                f"Cache hit: {meta['resource_count']} resources, {meta['age_human']}"
            )
            return adapter, meta

        except Exception as e:
            logger.warning(f"Error loading SQLite cache: {e}")
            return None

    def _load_and_migrate_json(
        self, max_age: int
    ) -> tuple[GraphEngineAdapter, dict[str, Any]] | None:
        """Load from legacy JSON and migrate to SQLite."""
        from replimap.core.unified_storage import GraphEngineAdapter
        from replimap.core.unified_storage.migrate import migrate_json_to_sqlite

        try:
            # First check if JSON is valid and not expired
            with open(self.legacy_json_path, encoding="utf-8") as f:
                payload = json.load(f)

            meta = payload.get("meta", {})

            # Expiry check
            age = time.time() - meta.get("timestamp", 0)
            if age > max_age:
                logger.debug(f"Legacy cache expired (age: {age:.0f}s > {max_age}s)")
                return None

            # Profile/region match
            if meta.get("profile") != self.profile or meta.get("region") != self.region:
                logger.debug("Legacy cache profile/region mismatch")
                return None

            # VPC match (if specified)
            if self.vpc and meta.get("vpc") != self.vpc:
                logger.debug("Legacy cache VPC mismatch")
                return None

            # Migrate JSON to SQLite
            logger.info(
                f"Migrating legacy JSON cache to SQLite: {self.legacy_json_path}"
            )
            migrate_json_to_sqlite(
                self.legacy_json_path,
                self.cache_path,
                delete_json=False,  # Keep JSON for now, user can delete manually
            )

            # Now load from SQLite (skip age check since we just migrated)
            adapter = GraphEngineAdapter(db_path=str(self.cache_path))

            # Update metadata
            meta["age_seconds"] = age
            meta["age_human"] = self._format_age(age)
            meta["cache_path"] = str(self.cache_path)
            meta["format"] = "sqlite"
            meta["migrated_from"] = str(self.legacy_json_path)

            logger.debug(
                f"Cache hit (migrated): {meta['resource_count']} resources, "
                f"{meta['age_human']}"
            )
            return adapter, meta

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Corrupt legacy cache file: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error migrating legacy cache: {e}")
            return None

    def invalidate(self) -> None:
        """Delete cached graph (both SQLite and legacy JSON)."""
        if self.cache_path.exists():
            self.cache_path.unlink()
            logger.debug(f"Cache invalidated: {self.cache_path}")
        if self.legacy_json_path.exists():
            self.legacy_json_path.unlink()
            logger.debug(f"Legacy cache invalidated: {self.legacy_json_path}")

    def exists(self) -> bool:
        """Check if cache file exists (SQLite or legacy JSON)."""
        return self.cache_path.exists() or self.legacy_json_path.exists()

    def get_age(self) -> float | None:
        """Get cache age in seconds, or None if no cache."""
        if self.cache_path.exists():
            return time.time() - self.cache_path.stat().st_mtime
        if self.legacy_json_path.exists():
            return time.time() - self.legacy_json_path.stat().st_mtime
        return None

    def _format_age(self, seconds: float) -> str:
        """Format age as human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s ago"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        else:
            return f"{seconds / 3600:.1f}h ago"

    @classmethod
    def clear_all(cls) -> int:
        """
        Clear all cached graphs (both SQLite and legacy JSON).

        Returns:
            Number of cache files deleted
        """
        count = 0
        if GRAPH_CACHE_DIR.exists():
            # Clear SQLite files
            for f in GRAPH_CACHE_DIR.glob("graph_*.db"):
                f.unlink()
                count += 1
            # Clear legacy JSON files
            for f in GRAPH_CACHE_DIR.glob("graph_*.json"):
                f.unlink()
                count += 1
            logger.info(f"Cleared {count} cached graphs")
        return count

    @classmethod
    def list_all(cls) -> list[dict[str, Any]]:
        """
        List all cached graphs with metadata.

        Returns:
            List of cache info dictionaries
        """
        from replimap.core.unified_storage import UnifiedGraphEngine

        caches = []
        if GRAPH_CACHE_DIR.exists():
            # List SQLite caches
            for f in sorted(GRAPH_CACHE_DIR.glob("graph_*.db")):
                try:
                    engine = UnifiedGraphEngine(db_path=str(f))
                    timestamp_str = engine.get_metadata("timestamp")
                    timestamp = float(timestamp_str) if timestamp_str else 0
                    age = time.time() - timestamp
                    resource_count_str = engine.get_metadata("resource_count")
                    dependency_count_str = engine.get_metadata("dependency_count")

                    caches.append(
                        {
                            "path": f,
                            "filename": f.name,
                            "size_kb": f.stat().st_size / 1024,
                            "profile": engine.get_metadata("profile") or "?",
                            "region": engine.get_metadata("region") or "?",
                            "vpc": engine.get_metadata("vpc"),
                            "resource_count": (
                                int(resource_count_str) if resource_count_str else 0
                            ),
                            "dependency_count": (
                                int(dependency_count_str) if dependency_count_str else 0
                            ),
                            "age_seconds": age,
                            "age_human": cls._format_age(cls, age),
                            "expired": age > DEFAULT_CACHE_TTL,
                            "format": "sqlite",
                        }
                    )
                    engine.close()
                except Exception:
                    # Corrupt cache file
                    caches.append(
                        {
                            "path": f,
                            "filename": f.name,
                            "size_kb": f.stat().st_size / 1024,
                            "error": "corrupt",
                            "format": "sqlite",
                        }
                    )

            # List legacy JSON caches (that don't have corresponding SQLite)
            for f in sorted(GRAPH_CACHE_DIR.glob("graph_*.json")):
                # Skip if SQLite version exists
                sqlite_version = f.with_suffix(".db")
                if sqlite_version.exists():
                    continue

                try:
                    with open(f, encoding="utf-8") as fp:
                        payload = json.load(fp)
                    meta = payload.get("meta", {})
                    age = time.time() - meta.get("timestamp", 0)
                    caches.append(
                        {
                            "path": f,
                            "filename": f.name,
                            "size_kb": f.stat().st_size / 1024,
                            "profile": meta.get("profile", "?"),
                            "region": meta.get("region", "?"),
                            "vpc": meta.get("vpc"),
                            "resource_count": meta.get("resource_count", 0),
                            "dependency_count": meta.get("dependency_count", 0),
                            "age_seconds": age,
                            "age_human": cls._format_age(cls, age),
                            "expired": age > DEFAULT_CACHE_TTL,
                            "format": "json (legacy)",
                        }
                    )
                except (json.JSONDecodeError, OSError):
                    # Corrupt cache file
                    caches.append(
                        {
                            "path": f,
                            "filename": f.name,
                            "size_kb": f.stat().st_size / 1024,
                            "error": "corrupt",
                            "format": "json (legacy)",
                        }
                    )
        return caches


def get_or_load_graph(
    profile: str,
    region: str,
    console: Console,
    refresh: bool = False,
    cache_ttl: int = DEFAULT_CACHE_TTL,
    vpc: str | None = None,
    account_id: str | None = None,
) -> tuple[GraphEngineAdapter | None, dict[str, Any] | None]:
    """
    Try to load graph from cache.

    This is a helper function for commands that want to check cache first
    before running a full scan.

    Args:
        profile: AWS profile name
        region: AWS region
        console: Rich console for output
        refresh: If True, ignore cache
        cache_ttl: Cache time-to-live in seconds
        vpc: Optional VPC filter
        account_id: Optional AWS account ID

    Returns:
        Tuple of (GraphEngineAdapter, meta) if cache hit, (None, None) if miss
    """
    if refresh:
        console.print("[dim]--refresh specified, ignoring cache...[/dim]")
        return None, None

    cache = CacheManager(profile, region, vpc, account_id)
    result = cache.load(max_age=cache_ttl)

    if result:
        graph, meta = result
        console.print(
            f"[bold green]Using cached scan[/bold green] "
            f"[dim]({meta['age_human']})[/dim] • "
            f"{meta['resource_count']:,} resources • "
            f"{meta['dependency_count']:,} dependencies"
        )
        return graph, meta

    return None, None


def save_graph_to_cache(
    graph: GraphEngineAdapter,
    profile: str,
    region: str,
    console: Console,
    vpc: str | None = None,
    account_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Save graph to cache after a scan.

    Args:
        graph: The GraphEngineAdapter to cache
        profile: AWS profile name
        region: AWS region
        console: Rich console for output
        vpc: Optional VPC filter
        account_id: Optional AWS account ID
        metadata: Optional additional metadata

    Returns:
        True if saved successfully
    """
    cache = CacheManager(profile, region, vpc, account_id)
    if cache.save(graph, metadata):
        console.print("[dim]Scan cached for subsequent commands[/dim]")
        return True
    return False


def print_cache_status(console: Console) -> None:
    """Print cache status table."""
    caches = CacheManager.list_all()

    if not caches:
        console.print("[dim]No cached scans found.[/dim]")
        return

    table = Table(title="Cached Scans", show_header=True, header_style="bold cyan")
    table.add_column("Profile", style="dim")
    table.add_column("Region")
    table.add_column("Resources", justify="right")
    table.add_column("Size", justify="right")
    table.add_column("Age")
    table.add_column("Format", style="dim")
    table.add_column("Status")

    for cache in caches:
        if "error" in cache:
            table.add_row(
                cache["filename"],
                "",
                "",
                f"{cache['size_kb']:.1f} KB",
                "",
                cache.get("format", "?"),
                "[red]corrupt[/red]",
            )
        else:
            status = (
                "[red]expired[/red]" if cache["expired"] else "[green]valid[/green]"
            )
            table.add_row(
                cache["profile"],
                cache["region"],
                f"{cache['resource_count']:,}",
                f"{cache['size_kb']:.1f} KB",
                cache["age_human"],
                cache.get("format", "?"),
                status,
            )

    console.print(table)


__all__ = [
    "CacheManager",
    "CACHE_DIR",
    "GRAPH_CACHE_DIR",
    "DEFAULT_CACHE_TTL",
    "get_or_load_graph",
    "save_graph_to_cache",
    "print_cache_status",
]
