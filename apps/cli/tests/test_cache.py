"""Tests for scan result caching."""

from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from replimap.core.cache import (
    CacheEntry,
    CacheMetadata,
    ScanCache,
    get_uncached_resource_types,
    populate_graph_from_cache,
    update_cache_from_graph,
)
from replimap.core.graph_engine import GraphEngine
from replimap.core.models import ResourceNode, ResourceType


class TestCacheEntry:
    """Tests for CacheEntry class."""

    def test_create_entry(self) -> None:
        """Test creating a cache entry."""
        resource = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"CidrBlock": "10.0.0.0/16"},
        )
        entry = CacheEntry(resource=resource, cached_at=time.time(), ttl=3600)

        assert entry.resource.id == "vpc-123"
        assert entry.ttl == 3600
        assert not entry.is_expired()

    def test_entry_expiration(self) -> None:
        """Test cache entry expiration."""
        resource = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        # Entry with TTL of 0 should be expired
        entry = CacheEntry(
            resource=resource,
            cached_at=time.time() - 10,  # 10 seconds ago
            ttl=5,  # 5 second TTL
        )

        assert entry.is_expired()

    def test_entry_not_expired(self) -> None:
        """Test non-expired cache entry."""
        resource = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
        )
        entry = CacheEntry(resource=resource, cached_at=time.time(), ttl=3600)

        assert not entry.is_expired()

    def test_entry_serialization(self) -> None:
        """Test cache entry to_dict and from_dict."""
        resource = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"CidrBlock": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )
        entry = CacheEntry(resource=resource, cached_at=1234567890.0, ttl=3600)

        data = entry.to_dict()
        restored = CacheEntry.from_dict(data)

        assert restored.resource.id == entry.resource.id
        assert restored.cached_at == entry.cached_at
        assert restored.ttl == entry.ttl


class TestCacheMetadata:
    """Tests for CacheMetadata class."""

    def test_create_metadata(self) -> None:
        """Test creating cache metadata."""
        metadata = CacheMetadata(
            account_id="123456789",
            region="us-east-1",
        )

        assert metadata.account_id == "123456789"
        assert metadata.region == "us-east-1"
        assert metadata.resource_count == 0

    def test_metadata_serialization(self) -> None:
        """Test metadata serialization."""
        metadata = CacheMetadata(
            account_id="123456789",
            region="us-east-1",
            created_at=1234567890.0,
            last_updated=1234567900.0,
            resource_count=10,
        )

        data = metadata.to_dict()
        restored = CacheMetadata.from_dict(data)

        assert restored.account_id == metadata.account_id
        assert restored.region == metadata.region
        assert restored.resource_count == metadata.resource_count


class TestScanCache:
    """Tests for ScanCache class."""

    @pytest.fixture
    def temp_cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_resource(self) -> ResourceNode:
        """Create a sample resource."""
        return ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={"CidrBlock": "10.0.0.0/16"},
            tags={"Name": "test-vpc"},
        )

    def test_create_cache(self, temp_cache_dir: Path) -> None:
        """Test creating a scan cache."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        assert cache.account_id == "123456789"
        assert cache.region == "us-east-1"

    def test_put_and_get(
        self, temp_cache_dir: Path, sample_resource: ResourceNode
    ) -> None:
        """Test putting and getting resources."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        cache.put(sample_resource)
        retrieved = cache.get("vpc-123")

        assert retrieved is not None
        assert retrieved.id == sample_resource.id

    def test_get_nonexistent(self, temp_cache_dir: Path) -> None:
        """Test getting non-existent resource."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        assert cache.get("nonexistent") is None

    def test_get_expired(
        self, temp_cache_dir: Path, sample_resource: ResourceNode
    ) -> None:
        """Test that expired entries return None."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Put with 0 TTL (immediately expired)
        cache.put(sample_resource, ttl=0)

        # Wait a moment for expiration
        time.sleep(0.1)

        assert cache.get("vpc-123") is None

    def test_put_many(self, temp_cache_dir: Path) -> None:
        """Test putting multiple resources."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        resources = [
            ResourceNode(
                id=f"vpc-{i}",
                resource_type=ResourceType.VPC,
                region="us-east-1",
            )
            for i in range(5)
        ]

        cache.put_many(resources)

        for i in range(5):
            assert cache.get(f"vpc-{i}") is not None

    def test_get_by_type(self, temp_cache_dir: Path) -> None:
        """Test getting resources by type."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Add different resource types
        cache.put(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        vpcs = cache.get_by_type(ResourceType.VPC)
        subnets = cache.get_by_type(ResourceType.SUBNET)

        assert len(vpcs) == 2
        assert len(subnets) == 1

    def test_invalidate(
        self, temp_cache_dir: Path, sample_resource: ResourceNode
    ) -> None:
        """Test invalidating a resource."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        cache.put(sample_resource)
        assert cache.get("vpc-123") is not None

        result = cache.invalidate("vpc-123")
        assert result is True
        assert cache.get("vpc-123") is None

        # Invalidating again returns False
        assert cache.invalidate("vpc-123") is False

    def test_invalidate_type(self, temp_cache_dir: Path) -> None:
        """Test invalidating all resources of a type."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Add VPCs and subnets
        for i in range(3):
            cache.put(
                ResourceNode(
                    id=f"vpc-{i}", resource_type=ResourceType.VPC, region="us-east-1"
                )
            )
            cache.put(
                ResourceNode(
                    id=f"subnet-{i}",
                    resource_type=ResourceType.SUBNET,
                    region="us-east-1",
                )
            )

        removed = cache.invalidate_type(ResourceType.VPC)

        assert removed == 3
        assert len(cache.get_by_type(ResourceType.VPC)) == 0
        assert len(cache.get_by_type(ResourceType.SUBNET)) == 3

    def test_clear(self, temp_cache_dir: Path, sample_resource: ResourceNode) -> None:
        """Test clearing the cache."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        cache.put(sample_resource)
        assert cache.get("vpc-123") is not None

        cache.clear()
        assert cache.get("vpc-123") is None

    def test_prune_expired(self, temp_cache_dir: Path) -> None:
        """Test pruning expired entries."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Add one expired and one valid resource
        cache.put(
            ResourceNode(
                id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1"
            ),
            ttl=0,  # Immediately expired
        )
        cache.put(
            ResourceNode(
                id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1"
            ),
            ttl=3600,  # Valid
        )

        # Wait for expiration
        time.sleep(0.1)

        pruned = cache.prune_expired()

        assert pruned == 1
        assert cache.get("vpc-1") is None
        assert cache.get("vpc-2") is not None

    def test_get_stats(self, temp_cache_dir: Path) -> None:
        """Test getting cache statistics."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        cache.put(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(id="vpc-2", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        stats = cache.get_stats()

        assert stats["account_id"] == "123456789"
        assert stats["region"] == "us-east-1"
        assert stats["total_resources"] == 3
        assert stats["by_type"]["aws_vpc"] == 2
        assert stats["by_type"]["aws_subnet"] == 1

    def test_save_and_load(
        self, temp_cache_dir: Path, sample_resource: ResourceNode
    ) -> None:
        """Test saving and loading cache."""
        # Create and populate cache
        cache1 = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )
        cache1.put(sample_resource)
        cache_path = cache1.save()

        assert cache_path.exists()

        # Load cache
        cache2 = ScanCache.load(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        retrieved = cache2.get("vpc-123")
        assert retrieved is not None
        assert retrieved.id == sample_resource.id

    def test_load_nonexistent(self, temp_cache_dir: Path) -> None:
        """Test loading non-existent cache creates empty cache."""
        cache = ScanCache.load(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        assert cache.get_stats()["total_resources"] == 0

    def test_load_corrupt_file(self, temp_cache_dir: Path) -> None:
        """Test loading corrupt cache file creates empty cache."""
        # Create corrupt cache file
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )
        cache_path = cache._get_cache_path()
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w") as f:
            f.write("not valid json")

        # Load should return empty cache
        loaded = ScanCache.load(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        assert loaded.get_stats()["total_resources"] == 0

    def test_delete_cache(
        self, temp_cache_dir: Path, sample_resource: ResourceNode
    ) -> None:
        """Test deleting cache file."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )
        cache.put(sample_resource)
        cache.save()

        result = ScanCache.delete_cache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        assert result is True

        # Deleting again returns False
        result = ScanCache.delete_cache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )
        assert result is False

    def test_default_ttls(self, temp_cache_dir: Path) -> None:
        """Test that default TTLs are applied by resource type."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # VPC should have 24 hour TTL
        vpc_ttl = cache._get_ttl("aws_vpc")
        assert vpc_ttl == 86400

        # EC2 instance should have 1 hour TTL
        ec2_ttl = cache._get_ttl("aws_instance")
        assert ec2_ttl == 3600

    def test_custom_ttls(self, temp_cache_dir: Path) -> None:
        """Test custom TTLs override defaults."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
            ttls={"aws_vpc": 60},  # 1 minute instead of 24 hours
        )

        vpc_ttl = cache._get_ttl("aws_vpc")
        assert vpc_ttl == 60


class TestCacheGraphIntegration:
    """Tests for cache-graph integration functions."""

    @pytest.fixture
    def temp_cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_populate_graph_from_cache(self, temp_cache_dir: Path) -> None:
        """Test populating graph from cache."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Add resources to cache
        cache.put(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        # Populate graph
        graph = GraphEngine()
        count = populate_graph_from_cache(cache, graph)

        assert count == 2
        assert graph.get_resource("vpc-1") is not None
        assert graph.get_resource("subnet-1") is not None

    def test_populate_graph_filtered(self, temp_cache_dir: Path) -> None:
        """Test populating graph with type filter."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        cache.put(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        cache.put(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        graph = GraphEngine()
        count = populate_graph_from_cache(
            cache, graph, resource_types=[ResourceType.VPC]
        )

        assert count == 1
        assert graph.get_resource("vpc-1") is not None
        assert graph.get_resource("subnet-1") is None

    def test_update_cache_from_graph(self, temp_cache_dir: Path) -> None:
        """Test updating cache from graph."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        count = update_cache_from_graph(cache, graph)

        assert count == 2
        assert cache.get("vpc-1") is not None
        assert cache.get("subnet-1") is not None

    def test_update_cache_filtered(self, temp_cache_dir: Path) -> None:
        """Test updating cache with type filter."""
        graph = GraphEngine()
        graph.add_resource(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )
        graph.add_resource(
            ResourceNode(
                id="subnet-1", resource_type=ResourceType.SUBNET, region="us-east-1"
            )
        )

        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        count = update_cache_from_graph(cache, graph, resource_types=[ResourceType.VPC])

        assert count == 1
        assert cache.get("vpc-1") is not None
        assert cache.get("subnet-1") is None

    def test_get_uncached_resource_types(self, temp_cache_dir: Path) -> None:
        """Test determining which types need scanning."""
        cache = ScanCache(
            account_id="123456789",
            region="us-east-1",
            cache_dir=temp_cache_dir,
        )

        # Add only VPCs to cache
        cache.put(
            ResourceNode(id="vpc-1", resource_type=ResourceType.VPC, region="us-east-1")
        )

        all_types = [ResourceType.VPC, ResourceType.SUBNET, ResourceType.EC2_INSTANCE]
        uncached = get_uncached_resource_types(cache, all_types)

        assert ResourceType.SUBNET in uncached
        assert ResourceType.EC2_INSTANCE in uncached
        assert ResourceType.VPC not in uncached
