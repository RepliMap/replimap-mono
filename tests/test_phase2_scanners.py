"""Tests for Phase 2 scanners."""

from replimap.core.models import ResourceType
from replimap.scanners.compute_scanner import ComputeScanner
from replimap.scanners.elasticache_scanner import (
    DBParameterGroupScanner,
    ElastiCacheScanner,
)
from replimap.scanners.messaging_scanner import SNSScanner, SQSScanner
from replimap.scanners.networking_scanner import NetworkingScanner
from replimap.scanners.storage_scanner import EBSScanner, S3PolicyScanner


class TestNetworkingScanner:
    """Tests for NetworkingScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.INTERNET_GATEWAY.value in NetworkingScanner.resource_types
        assert ResourceType.NAT_GATEWAY.value in NetworkingScanner.resource_types
        assert ResourceType.ROUTE_TABLE.value in NetworkingScanner.resource_types
        assert ResourceType.VPC_ENDPOINT.value in NetworkingScanner.resource_types


class TestComputeScanner:
    """Tests for ComputeScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.LAUNCH_TEMPLATE.value in ComputeScanner.resource_types
        assert ResourceType.AUTOSCALING_GROUP.value in ComputeScanner.resource_types
        assert ResourceType.LB.value in ComputeScanner.resource_types
        assert ResourceType.LB_TARGET_GROUP.value in ComputeScanner.resource_types
        assert ResourceType.LB_LISTENER.value in ComputeScanner.resource_types


class TestElastiCacheScanner:
    """Tests for ElastiCacheScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert (
            ResourceType.ELASTICACHE_CLUSTER.value in ElastiCacheScanner.resource_types
        )
        assert (
            ResourceType.ELASTICACHE_SUBNET_GROUP.value
            in ElastiCacheScanner.resource_types
        )


class TestDBParameterGroupScanner:
    """Tests for DBParameterGroupScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert (
            ResourceType.DB_PARAMETER_GROUP.value
            in DBParameterGroupScanner.resource_types
        )


class TestEBSScanner:
    """Tests for EBSScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.EBS_VOLUME.value in EBSScanner.resource_types


class TestS3PolicyScanner:
    """Tests for S3PolicyScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.S3_BUCKET_POLICY.value in S3PolicyScanner.resource_types


class TestSQSScanner:
    """Tests for SQSScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.SQS_QUEUE.value in SQSScanner.resource_types


class TestSNSScanner:
    """Tests for SNSScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares correct resource types."""
        assert ResourceType.SNS_TOPIC.value in SNSScanner.resource_types


class TestPhase2ResourceTypes:
    """Test that all Phase 2 resource types are defined."""

    def test_networking_resource_types(self) -> None:
        """Test networking resource types exist."""
        assert ResourceType.ROUTE_TABLE.value == "aws_route_table"
        assert ResourceType.INTERNET_GATEWAY.value == "aws_internet_gateway"
        assert ResourceType.NAT_GATEWAY.value == "aws_nat_gateway"
        assert ResourceType.VPC_ENDPOINT.value == "aws_vpc_endpoint"

    def test_compute_resource_types(self) -> None:
        """Test compute resource types exist."""
        assert ResourceType.LAUNCH_TEMPLATE.value == "aws_launch_template"
        assert ResourceType.AUTOSCALING_GROUP.value == "aws_autoscaling_group"
        assert ResourceType.LB.value == "aws_lb"
        assert ResourceType.LB_LISTENER.value == "aws_lb_listener"
        assert ResourceType.LB_TARGET_GROUP.value == "aws_lb_target_group"

    def test_database_resource_types(self) -> None:
        """Test database resource types exist."""
        assert ResourceType.DB_PARAMETER_GROUP.value == "aws_db_parameter_group"
        assert ResourceType.ELASTICACHE_CLUSTER.value == "aws_elasticache_cluster"
        assert (
            ResourceType.ELASTICACHE_SUBNET_GROUP.value
            == "aws_elasticache_subnet_group"
        )

    def test_storage_resource_types(self) -> None:
        """Test storage resource types exist."""
        assert ResourceType.S3_BUCKET_POLICY.value == "aws_s3_bucket_policy"
        assert ResourceType.EBS_VOLUME.value == "aws_ebs_volume"

    def test_messaging_resource_types(self) -> None:
        """Test messaging resource types exist."""
        assert ResourceType.SQS_QUEUE.value == "aws_sqs_queue"
        assert ResourceType.SNS_TOPIC.value == "aws_sns_topic"
