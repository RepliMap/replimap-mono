"""
Graph caching layer for RepliMap CLI.

Enables instant graph/deps/clone/cost/audit after initial scan by caching
the scan results to disk. Cache is per profile/region/vpc combination.
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

    from replimap.core import GraphEngine

logger = logging.getLogger(__name__)

# Directory structure
REPLIMAP_ROOT = Path.home() / ".replimap"
CACHE_DIR = REPLIMAP_ROOT / "cache"
GRAPH_CACHE_DIR = CACHE_DIR / "graphs"

# Default cache TTL: 1 hour
DEFAULT_CACHE_TTL = 3600

# Cache format version
CACHE_VERSION = "1.0"


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
            filename = f"graph_{safe_profile}_{region}_{vpc}.json"
        else:
            filename = f"graph_{safe_profile}_{region}.json"

        self.cache_path = GRAPH_CACHE_DIR / filename

    def save(self, graph: GraphEngine, metadata: dict[str, Any] | None = None) -> bool:
        """
        Save GraphEngine to JSON cache file.

        Args:
            graph: The GraphEngine to cache
            metadata: Optional additional metadata

        Returns:
            True if successful, False otherwise
        """
        from replimap.core.graph_engine import RepliMapJSONEncoder

        try:
            start = time.time()

            # Get graph data using existing to_dict method
            graph_data = graph.to_dict()

            payload = {
                "meta": {
                    "version": CACHE_VERSION,
                    "timestamp": time.time(),
                    "profile": self.profile,
                    "region": self.region,
                    "vpc": self.vpc,
                    "account_id": self.account_id,
                    "resource_count": graph.node_count,
                    "dependency_count": graph.edge_count,
                    **(metadata or {}),
                },
                "graph": graph_data,
            }

            # Write atomically (temp file + rename)
            temp_path = self.cache_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, cls=RepliMapJSONEncoder)
            temp_path.rename(self.cache_path)

            duration = time.time() - start
            logger.debug(f"Graph cached in {duration:.2f}s to {self.cache_path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to cache graph: {e}")
            return False

    def load(
        self, max_age: int = DEFAULT_CACHE_TTL
    ) -> tuple[GraphEngine, dict[str, Any]] | None:
        """
        Load graph from cache if valid.

        Args:
            max_age: Maximum cache age in seconds

        Returns:
            Tuple of (GraphEngine, meta_info) if cache valid, None otherwise
        """
        from replimap.core import GraphEngine

        if not self.cache_path.exists():
            logger.debug(f"Cache miss: {self.cache_path} does not exist")
            return None

        try:
            with open(self.cache_path, encoding="utf-8") as f:
                payload = json.load(f)

            meta = payload.get("meta", {})

            # Version check
            if meta.get("version") != CACHE_VERSION:
                logger.debug("Cache version mismatch, invalidating")
                return None

            # Expiry check
            age = time.time() - meta.get("timestamp", 0)
            if age > max_age:
                logger.debug(f"Cache expired (age: {age:.0f}s > {max_age}s)")
                return None

            # Profile/region match
            if meta.get("profile") != self.profile or meta.get("region") != self.region:
                logger.debug("Cache profile/region mismatch")
                return None

            # VPC match (if specified)
            if self.vpc and meta.get("vpc") != self.vpc:
                logger.debug("Cache VPC mismatch")
                return None

            # Reconstruct GraphEngine using existing from_dict method
            graph = GraphEngine.from_dict(payload["graph"])

            # Add computed fields to meta
            meta["age_seconds"] = age
            meta["age_human"] = self._format_age(age)
            meta["cache_path"] = str(self.cache_path)

            logger.debug(
                f"Cache hit: {meta['resource_count']} resources, {meta['age_human']}"
            )
            return graph, meta

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Corrupt cache file: {e}")
            self.invalidate()
            return None

    def invalidate(self) -> None:
        """Delete cached graph."""
        if self.cache_path.exists():
            self.cache_path.unlink()
            logger.debug(f"Cache invalidated: {self.cache_path}")

    def exists(self) -> bool:
        """Check if cache file exists."""
        return self.cache_path.exists()

    def get_age(self) -> float | None:
        """Get cache age in seconds, or None if no cache."""
        if not self.cache_path.exists():
            return None
        return time.time() - self.cache_path.stat().st_mtime

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
        Clear all cached graphs.

        Returns:
            Number of cache files deleted
        """
        count = 0
        if GRAPH_CACHE_DIR.exists():
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
        caches = []
        if GRAPH_CACHE_DIR.exists():
            for f in sorted(GRAPH_CACHE_DIR.glob("graph_*.json")):
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
) -> tuple[GraphEngine | None, dict[str, Any] | None]:
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
        Tuple of (GraphEngine, meta) if cache hit, (None, None) if miss
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
    graph: GraphEngine,
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
        graph: The GraphEngine to cache
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
    table.add_column("Status")

    for cache in caches:
        if "error" in cache:
            table.add_row(
                cache["filename"],
                "",
                "",
                f"{cache['size_kb']:.1f} KB",
                "",
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
