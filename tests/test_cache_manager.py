"""Tests for the cache manager module."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

from replimap.core.cache_manager import (
    CacheManager,
    get_or_load_graph,
    save_graph_to_cache,
)


class TestCacheManager:
    """Tests for CacheManager class."""

    def test_init_creates_cache_directory(self, tmp_path: Path) -> None:
        """Test that CacheManager creates cache directory on init."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            cache = CacheManager("test-profile", "us-east-1")
            assert cache.profile == "test-profile"
            assert cache.region == "us-east-1"
            assert (tmp_path / "graphs").exists()

    def test_cache_path_generation(self, tmp_path: Path) -> None:
        """Test cache file path generation."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            # Without VPC
            cache = CacheManager("prod", "us-west-2")
            assert cache.cache_path.name == "graph_prod_us-west-2.json"

            # With VPC
            cache_vpc = CacheManager("prod", "us-west-2", vpc="vpc-123")
            assert cache_vpc.cache_path.name == "graph_prod_us-west-2_vpc-123.json"

    def test_cache_path_sanitizes_profile(self, tmp_path: Path) -> None:
        """Test that profile names with slashes are sanitized."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            cache = CacheManager("org/profile", "us-east-1")
            assert "/" not in cache.cache_path.name
            assert "org_profile" in cache.cache_path.name

    def test_save_and_load_graph(self, tmp_path: Path) -> None:
        """Test saving and loading a graph."""
        from replimap.core import GraphEngine
        from replimap.core.models import ResourceNode, ResourceType

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            # Create a test graph
            graph = GraphEngine()
            node = ResourceNode(
                id="vpc-123",
                resource_type=ResourceType.VPC,
                region="us-east-1",
                original_name="test-vpc",
            )
            graph.add_resource(node)

            # Save
            cache = CacheManager("test", "us-east-1")
            result = cache.save(graph, metadata={"test_key": "test_value"})
            assert result is True
            assert cache.cache_path.exists()

            # Load
            loaded = cache.load()
            assert loaded is not None
            loaded_graph, meta = loaded
            assert loaded_graph.node_count == 1
            assert meta["profile"] == "test"
            assert meta["region"] == "us-east-1"
            assert meta["resource_count"] == 1
            assert "age_human" in meta

    def test_load_returns_none_if_no_cache(self, tmp_path: Path) -> None:
        """Test that load returns None if no cache exists."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            cache = CacheManager("test", "us-east-1")
            assert cache.load() is None

    def test_load_returns_none_if_expired(self, tmp_path: Path) -> None:
        """Test that load returns None if cache is expired."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            graph = GraphEngine()
            cache = CacheManager("test", "us-east-1")
            cache.save(graph)

            # Manually modify timestamp to be old
            with open(cache.cache_path) as f:
                data = json.load(f)
            data["meta"]["timestamp"] = time.time() - 7200  # 2 hours ago
            with open(cache.cache_path, "w") as f:
                json.dump(data, f)

            # Should return None due to expiry
            assert cache.load(max_age=3600) is None

    def test_load_returns_none_if_version_mismatch(self, tmp_path: Path) -> None:
        """Test that load returns None if version doesn't match."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            graph = GraphEngine()
            cache = CacheManager("test", "us-east-1")
            cache.save(graph)

            # Modify version
            with open(cache.cache_path) as f:
                data = json.load(f)
            data["meta"]["version"] = "0.0.0"
            with open(cache.cache_path, "w") as f:
                json.dump(data, f)

            assert cache.load() is None

    def test_invalidate_deletes_cache(self, tmp_path: Path) -> None:
        """Test that invalidate deletes the cache file."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            graph = GraphEngine()
            cache = CacheManager("test", "us-east-1")
            cache.save(graph)
            assert cache.cache_path.exists()

            cache.invalidate()
            assert not cache.cache_path.exists()

    def test_clear_all(self, tmp_path: Path) -> None:
        """Test clearing all caches."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            # Create multiple caches
            graph = GraphEngine()
            CacheManager("p1", "us-east-1").save(graph)
            CacheManager("p2", "us-west-2").save(graph)

            assert len(list((tmp_path / "graphs").glob("graph_*.json"))) == 2

            count = CacheManager.clear_all()
            assert count == 2
            assert len(list((tmp_path / "graphs").glob("graph_*.json"))) == 0

    def test_list_all(self, tmp_path: Path) -> None:
        """Test listing all caches."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            graph = GraphEngine()
            CacheManager("prod", "us-east-1").save(graph)
            CacheManager("dev", "eu-west-1").save(graph)

            caches = CacheManager.list_all()
            assert len(caches) == 2
            profiles = {c["profile"] for c in caches}
            assert "prod" in profiles
            assert "dev" in profiles

    def test_format_age(self, tmp_path: Path) -> None:
        """Test age formatting."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            cache = CacheManager("test", "us-east-1")

            assert "s ago" in cache._format_age(30)
            assert "m ago" in cache._format_age(120)
            assert "h ago" in cache._format_age(7200)


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_get_or_load_graph_returns_none_on_refresh(self, tmp_path: Path) -> None:
        """Test that refresh=True returns None."""
        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            console = MagicMock()
            graph, meta = get_or_load_graph(
                profile="test",
                region="us-east-1",
                console=console,
                refresh=True,
            )
            assert graph is None
            assert meta is None

    def test_get_or_load_graph_returns_cached(self, tmp_path: Path) -> None:
        """Test that cached graph is returned."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            # Create cache
            graph = GraphEngine()
            CacheManager("test", "us-east-1").save(graph)

            console = MagicMock()
            loaded, meta = get_or_load_graph(
                profile="test",
                region="us-east-1",
                console=console,
                refresh=False,
            )
            assert loaded is not None
            assert meta is not None

    def test_save_graph_to_cache(self, tmp_path: Path) -> None:
        """Test save_graph_to_cache function."""
        from replimap.core import GraphEngine

        with patch("replimap.core.cache_manager.GRAPH_CACHE_DIR", tmp_path / "graphs"):
            graph = GraphEngine()
            console = MagicMock()

            result = save_graph_to_cache(
                graph=graph,
                profile="test",
                region="us-east-1",
                console=console,
            )
            assert result is True
            assert (tmp_path / "graphs" / "graph_test_us-east-1.json").exists()
