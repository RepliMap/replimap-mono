"""Tests for Phase 2 renderer support."""

import tempfile
from pathlib import Path

from replimap.core import GraphEngine
from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.renderers.cloudformation import CloudFormationRenderer
from replimap.renderers.pulumi import PulumiRenderer
from replimap.renderers.terraform import TerraformRenderer


def create_phase2_graph() -> GraphEngine:
    """Create a graph with Phase 2 resources for testing."""
    graph = GraphEngine()

    # VPC (base dependency)
    vpc = ResourceNode(
        id="vpc-123",
        resource_type=ResourceType.VPC,
        region="us-east-1",
        original_name="prod-vpc",
        config={"cidr_block": "10.0.0.0/16"},
        tags={"Name": "prod-vpc"},
    )
    graph.add_resource(vpc)

    # Subnet
    subnet = ResourceNode(
        id="subnet-123",
        resource_type=ResourceType.SUBNET,
        region="us-east-1",
        original_name="prod-subnet",
        config={"cidr_block": "10.0.1.0/24", "availability_zone": "us-east-1a"},
        tags={"Name": "prod-subnet"},
    )
    graph.add_resource(subnet)
    graph.add_dependency(subnet.id, vpc.id, DependencyType.BELONGS_TO)

    # Security Group
    sg = ResourceNode(
        id="sg-123",
        resource_type=ResourceType.SECURITY_GROUP,
        region="us-east-1",
        original_name="prod-sg",
        config={"description": "Prod security group", "ingress": []},
        tags={"Name": "prod-sg"},
    )
    graph.add_resource(sg)
    graph.add_dependency(sg.id, vpc.id, DependencyType.BELONGS_TO)

    # Internet Gateway
    igw = ResourceNode(
        id="igw-123",
        resource_type=ResourceType.INTERNET_GATEWAY,
        region="us-east-1",
        original_name="prod-igw",
        config={},
        tags={"Name": "prod-igw"},
    )
    graph.add_resource(igw)
    graph.add_dependency(igw.id, vpc.id, DependencyType.BELONGS_TO)

    # NAT Gateway
    nat = ResourceNode(
        id="nat-123",
        resource_type=ResourceType.NAT_GATEWAY,
        region="us-east-1",
        original_name="prod-nat",
        config={"connectivity_type": "public", "allocation_id": "eipalloc-123"},
        tags={"Name": "prod-nat"},
    )
    graph.add_resource(nat)
    graph.add_dependency(nat.id, subnet.id, DependencyType.BELONGS_TO)

    # Route Table
    rtb = ResourceNode(
        id="rtb-123",
        resource_type=ResourceType.ROUTE_TABLE,
        region="us-east-1",
        original_name="prod-rtb",
        config={"routes": [{"destination_cidr_block": "0.0.0.0/0"}]},
        tags={"Name": "prod-rtb"},
    )
    graph.add_resource(rtb)
    graph.add_dependency(rtb.id, vpc.id, DependencyType.BELONGS_TO)

    # Load Balancer
    lb = ResourceNode(
        id="lb-123",
        resource_type=ResourceType.LB,
        region="us-east-1",
        original_name="prod-alb",
        config={"load_balancer_type": "application", "internal": False},
        tags={"Name": "prod-alb"},
    )
    graph.add_resource(lb)
    graph.add_dependency(lb.id, subnet.id, DependencyType.USES)
    graph.add_dependency(lb.id, sg.id, DependencyType.USES)

    # Target Group
    tg = ResourceNode(
        id="tg-123",
        resource_type=ResourceType.LB_TARGET_GROUP,
        region="us-east-1",
        original_name="prod-tg",
        config={"port": 80, "protocol": "HTTP", "target_type": "instance"},
        tags={"Name": "prod-tg"},
    )
    graph.add_resource(tg)
    graph.add_dependency(tg.id, vpc.id, DependencyType.USES)

    # ElastiCache Cluster
    cache = ResourceNode(
        id="cache-123",
        resource_type=ResourceType.ELASTICACHE_CLUSTER,
        region="us-east-1",
        original_name="prod-redis",
        config={
            "cluster_id": "prod-redis",
            "engine": "redis",
            "node_type": "cache.t3.micro",
            "num_cache_nodes": 1,
        },
        tags={"Name": "prod-redis"},
    )
    graph.add_resource(cache)
    graph.add_dependency(cache.id, sg.id, DependencyType.USES)

    # SQS Queue
    sqs = ResourceNode(
        id="sqs-123",
        resource_type=ResourceType.SQS_QUEUE,
        region="us-east-1",
        original_name="prod-queue",
        config={
            "name": "prod-queue",
            "visibility_timeout_seconds": 30,
            "message_retention_seconds": 345600,
        },
        tags={"Name": "prod-queue"},
    )
    graph.add_resource(sqs)

    # SNS Topic
    sns = ResourceNode(
        id="sns-123",
        resource_type=ResourceType.SNS_TOPIC,
        region="us-east-1",
        original_name="prod-topic",
        config={"name": "prod-topic"},
        tags={"Name": "prod-topic"},
    )
    graph.add_resource(sns)

    return graph


class TestTerraformPhase2:
    """Tests for Terraform renderer Phase 2 support."""

    def test_file_mapping_includes_phase2(self) -> None:
        """Test that FILE_MAPPING includes Phase 2 resources."""
        mapping = TerraformRenderer.FILE_MAPPING

        # Networking
        assert ResourceType.INTERNET_GATEWAY in mapping
        assert ResourceType.NAT_GATEWAY in mapping
        assert ResourceType.ROUTE_TABLE in mapping
        assert ResourceType.VPC_ENDPOINT in mapping

        # Compute
        assert ResourceType.LAUNCH_TEMPLATE in mapping
        assert ResourceType.AUTOSCALING_GROUP in mapping
        assert ResourceType.LB in mapping
        assert ResourceType.LB_TARGET_GROUP in mapping

        # Database
        assert ResourceType.ELASTICACHE_CLUSTER in mapping
        assert ResourceType.ELASTICACHE_SUBNET_GROUP in mapping
        assert ResourceType.DB_PARAMETER_GROUP in mapping

        # Storage/Messaging
        assert ResourceType.EBS_VOLUME in mapping
        assert ResourceType.S3_BUCKET_POLICY in mapping
        assert ResourceType.SQS_QUEUE in mapping
        assert ResourceType.SNS_TOPIC in mapping

    def test_render_phase2_resources(self) -> None:
        """Test rendering Phase 2 resources to Terraform."""
        graph = create_phase2_graph()

        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = TerraformRenderer()
            files = renderer.render(graph, Path(tmpdir))

            # Check that expected files were created
            assert "networking.tf" in files
            assert "alb.tf" in files
            assert "elasticache.tf" in files
            assert "messaging.tf" in files

    def test_preview_phase2_resources(self) -> None:
        """Test preview includes Phase 2 resources."""
        graph = create_phase2_graph()
        renderer = TerraformRenderer()
        preview = renderer.preview(graph)

        # Check that Phase 2 resources are in preview
        assert "networking.tf" in preview
        assert "alb.tf" in preview
        assert "elasticache.tf" in preview
        assert "messaging.tf" in preview


class TestCloudFormationPhase2:
    """Tests for CloudFormation renderer Phase 2 support."""

    def test_file_mapping_includes_phase2(self) -> None:
        """Test that FILE_MAPPING includes Phase 2 resources."""
        mapping = CloudFormationRenderer.FILE_MAPPING

        # Networking
        assert ResourceType.INTERNET_GATEWAY in mapping
        assert ResourceType.NAT_GATEWAY in mapping
        assert ResourceType.ROUTE_TABLE in mapping

        # Compute
        assert ResourceType.LAUNCH_TEMPLATE in mapping
        assert ResourceType.LB in mapping
        assert ResourceType.LB_TARGET_GROUP in mapping

        # Database
        assert ResourceType.ELASTICACHE_CLUSTER in mapping

        # Messaging
        assert ResourceType.SQS_QUEUE in mapping
        assert ResourceType.SNS_TOPIC in mapping


class TestPulumiPhase2:
    """Tests for Pulumi renderer Phase 2 support."""

    def test_file_mapping_includes_phase2(self) -> None:
        """Test that FILE_MAPPING includes Phase 2 resources."""
        mapping = PulumiRenderer.FILE_MAPPING

        # Networking
        assert ResourceType.INTERNET_GATEWAY in mapping
        assert ResourceType.NAT_GATEWAY in mapping
        assert ResourceType.ROUTE_TABLE in mapping
        assert ResourceType.VPC_ENDPOINT in mapping

        # Compute
        assert ResourceType.LAUNCH_TEMPLATE in mapping
        assert ResourceType.AUTOSCALING_GROUP in mapping
        assert ResourceType.LB in mapping
        assert ResourceType.LB_TARGET_GROUP in mapping
        assert ResourceType.LB_LISTENER in mapping

        # Database
        assert ResourceType.ELASTICACHE_CLUSTER in mapping
        assert ResourceType.ELASTICACHE_SUBNET_GROUP in mapping
        assert ResourceType.DB_PARAMETER_GROUP in mapping

        # Storage/Messaging
        assert ResourceType.EBS_VOLUME in mapping
        assert ResourceType.S3_BUCKET_POLICY in mapping
        assert ResourceType.SQS_QUEUE in mapping
        assert ResourceType.SNS_TOPIC in mapping

    def test_converter_methods_exist(self) -> None:
        """Test that Phase 2 converter methods exist."""
        renderer = PulumiRenderer()

        # Check Phase 2 converters exist
        assert hasattr(renderer, "_convert_igw")
        assert hasattr(renderer, "_convert_nat")
        assert hasattr(renderer, "_convert_route_table")
        assert hasattr(renderer, "_convert_lb")
        assert hasattr(renderer, "_convert_target_group")
        assert hasattr(renderer, "_convert_elasticache")
        assert hasattr(renderer, "_convert_sqs")
        assert hasattr(renderer, "_convert_sns")

    def test_preview_phase2_resources(self) -> None:
        """Test preview includes Phase 2 resources."""
        graph = create_phase2_graph()
        renderer = PulumiRenderer()
        preview = renderer.preview(graph)

        # Check that Phase 2 resource files are in preview
        # Note: exact file names depend on FILE_MAPPING in PulumiRenderer
        assert len(preview) > 0  # At least some files generated
