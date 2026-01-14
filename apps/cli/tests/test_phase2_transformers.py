"""Tests for Phase 2 transformer support."""

from replimap.core import GraphEngine
from replimap.core.models import ResourceNode, ResourceType
from replimap.transformers.downsizer import (
    ELASTICACHE_DOWNSIZE_MAP,
    DownsizeTransformer,
)


class TestElastiCacheDownsizer:
    """Tests for ElastiCache downsizing."""

    def test_downsize_map_exists(self) -> None:
        """Test that ElastiCache downsize map is defined."""
        assert len(ELASTICACHE_DOWNSIZE_MAP) > 0

    def test_downsize_map_contains_common_sizes(self) -> None:
        """Test that common ElastiCache node types are mapped."""
        assert "cache.m5.large" in ELASTICACHE_DOWNSIZE_MAP
        assert "cache.r5.large" in ELASTICACHE_DOWNSIZE_MAP
        assert "cache.m6g.large" in ELASTICACHE_DOWNSIZE_MAP

    def test_downsize_elasticache_cluster(self) -> None:
        """Test downsizing ElastiCache clusters."""
        graph = GraphEngine()

        cache = ResourceNode(
            id="cache-123",
            resource_type=ResourceType.ELASTICACHE_CLUSTER,
            region="us-east-1",
            original_name="prod-redis",
            config={
                "cluster_id": "prod-redis",
                "engine": "redis",
                "node_type": "cache.m5.large",
                "num_cache_nodes": 3,
            },
            tags={"Name": "prod-redis"},
        )
        graph.add_resource(cache)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        # Check that node type was downsized
        updated_cache = graph.get_resource("cache-123")
        assert updated_cache.config["node_type"] == "cache.t3.medium"

    def test_downsize_elasticache_reduces_nodes(self) -> None:
        """Test that ElastiCache clusters are reduced to 1 node in staging."""
        graph = GraphEngine()

        cache = ResourceNode(
            id="cache-456",
            resource_type=ResourceType.ELASTICACHE_CLUSTER,
            region="us-east-1",
            original_name="prod-memcached",
            config={
                "cluster_id": "prod-memcached",
                "engine": "memcached",
                "node_type": "cache.t3.micro",
                "num_cache_nodes": 5,
            },
            tags={"Name": "prod-memcached"},
        )
        graph.add_resource(cache)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        # Check that node count was reduced
        updated_cache = graph.get_resource("cache-456")
        assert updated_cache.config["num_cache_nodes"] == 1

    def test_downsize_preserves_small_elasticache(self) -> None:
        """Test that small ElastiCache nodes are preserved."""
        graph = GraphEngine()

        cache = ResourceNode(
            id="cache-789",
            resource_type=ResourceType.ELASTICACHE_CLUSTER,
            region="us-east-1",
            original_name="staging-redis",
            config={
                "cluster_id": "staging-redis",
                "engine": "redis",
                "node_type": "cache.t3.micro",
                "num_cache_nodes": 1,
            },
            tags={"Name": "staging-redis"},
        )
        graph.add_resource(cache)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        # Node type should be unchanged
        updated_cache = graph.get_resource("cache-789")
        assert updated_cache.config["node_type"] == "cache.t3.micro"


class TestLaunchTemplateDownsizer:
    """Tests for Launch Template downsizing."""

    def test_downsize_launch_template(self) -> None:
        """Test downsizing Launch Templates."""
        graph = GraphEngine()

        lt = ResourceNode(
            id="lt-123",
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region="us-east-1",
            original_name="prod-lt",
            config={
                "launch_template_name": "prod-lt",
                "instance_type": "m5.xlarge",
                "image_id": "ami-12345",
            },
            tags={"Name": "prod-lt"},
        )
        graph.add_resource(lt)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        updated_lt = graph.get_resource("lt-123")
        # Should be downsized to a smaller instance
        assert updated_lt.config["instance_type"] != "m5.xlarge"


class TestASGDownsizer:
    """Tests for Auto Scaling Group downsizing."""

    def test_downsize_asg_capacity(self) -> None:
        """Test that ASG capacities are reduced for staging."""
        graph = GraphEngine()

        asg = ResourceNode(
            id="asg-123",
            resource_type=ResourceType.AUTOSCALING_GROUP,
            region="us-east-1",
            original_name="prod-asg",
            config={
                "auto_scaling_group_name": "prod-asg",
                "min_size": 3,
                "max_size": 10,
                "desired_capacity": 5,
            },
            tags={"Name": "prod-asg"},
        )
        graph.add_resource(asg)

        transformer = DownsizeTransformer()
        transformer.transform(graph)

        updated_asg = graph.get_resource("asg-123")
        assert updated_asg.config["min_size"] == 1
        assert updated_asg.config["max_size"] == 2
        assert updated_asg.config["desired_capacity"] == 1
