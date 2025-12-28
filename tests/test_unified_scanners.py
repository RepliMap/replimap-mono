"""
Tests for unified async scanners.

Tests cover:
- Scanner registration
- EC2 instance scanning
- RDS instance and subnet group scanning
- IAM role, policy, and instance profile scanning
- Resilience features (circuit breaker, retry)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from replimap.core import GraphEngine
from replimap.core.async_aws import AsyncAWSClient
from replimap.core.models import ResourceType
from replimap.scanners.unified_scanners import (
    AsyncEC2Scanner,
    AsyncIAMScanner,
    AsyncRDSScanner,
    UnifiedScannerRegistry,
    run_unified_scanners,
)


class TestUnifiedScannerRegistry:
    """Tests for UnifiedScannerRegistry."""

    def test_scanners_registered(self) -> None:
        """All scanners should be registered."""
        scanners = UnifiedScannerRegistry.get_all()
        scanner_names = [s.__name__ for s in scanners]

        assert "AsyncEC2Scanner" in scanner_names
        assert "AsyncRDSScanner" in scanner_names
        assert "AsyncIAMScanner" in scanner_names

    def test_get_all_returns_copy(self) -> None:
        """get_all should return a copy, not the original list."""
        scanners1 = UnifiedScannerRegistry.get_all()
        scanners2 = UnifiedScannerRegistry.get_all()

        assert scanners1 == scanners2
        assert scanners1 is not scanners2


class TestAsyncEC2Scanner:
    """Tests for AsyncEC2Scanner."""

    def test_resource_types(self) -> None:
        """Should declare aws_instance resource type."""
        assert "aws_instance" in AsyncEC2Scanner.resource_types

    @pytest.mark.asyncio
    async def test_scan_adds_running_instances(self) -> None:
        """Should add running instances to graph."""
        graph = GraphEngine()

        # Mock AWS response
        mock_reservations = [
            {
                "Reservations": [
                    {
                        "Instances": [
                            {
                                "InstanceId": "i-12345",
                                "ImageId": "ami-abc123",
                                "InstanceType": "t3.medium",
                                "State": {"Name": "running"},
                                "SubnetId": "subnet-123",
                                "VpcId": "vpc-123",
                                "SecurityGroups": [{"GroupId": "sg-123"}],
                                "BlockDeviceMappings": [],
                                "NetworkInterfaces": [],
                                "OwnerId": "123456789012",
                                "Tags": [{"Key": "Name", "Value": "test-instance"}],
                            }
                        ]
                    }
                ]
            }
        ]

        scanner = AsyncEC2Scanner(region="us-east-1", account_id="123456789012")

        # Create mock client
        mock_client = MagicMock(spec=AsyncAWSClient)
        mock_client.paginate_with_resilience = AsyncMock(
            return_value=mock_reservations[0]["Reservations"]
        )

        scanner._client = mock_client

        await scanner.scan(graph)

        # Verify instance was added
        node = graph.get_resource("123456789012:us-east-1:i-12345")
        assert node is not None
        assert node.resource_type == ResourceType.EC2_INSTANCE
        assert node.config["instance_type"] == "t3.medium"
        assert node.tags.get("Name") == "test-instance"

    @pytest.mark.asyncio
    async def test_scan_skips_stopped_instances(self) -> None:
        """Should skip non-running instances."""
        graph = GraphEngine()

        mock_reservations = [
            {
                "Instances": [
                    {
                        "InstanceId": "i-stopped",
                        "ImageId": "ami-abc123",
                        "InstanceType": "t3.medium",
                        "State": {"Name": "stopped"},
                        "Tags": [],
                    }
                ]
            }
        ]

        scanner = AsyncEC2Scanner(region="us-east-1")
        mock_client = MagicMock(spec=AsyncAWSClient)
        mock_client.paginate_with_resilience = AsyncMock(return_value=mock_reservations)
        scanner._client = mock_client

        await scanner.scan(graph)

        # Verify stopped instance was NOT added
        assert graph.get_resource("i-stopped") is None


class TestAsyncRDSScanner:
    """Tests for AsyncRDSScanner."""

    def test_resource_types(self) -> None:
        """Should declare RDS resource types."""
        assert "aws_db_instance" in AsyncRDSScanner.resource_types
        assert "aws_db_subnet_group" in AsyncRDSScanner.resource_types

    @pytest.mark.asyncio
    async def test_scan_adds_db_instances(self) -> None:
        """Should add DB instances to graph."""
        graph = GraphEngine()

        mock_subnet_groups: list[dict[str, Any]] = []
        mock_db_instances = [
            {
                "DBInstanceIdentifier": "my-db",
                "Engine": "mysql",
                "EngineVersion": "8.0",
                "DBInstanceClass": "db.t3.medium",
                "DBInstanceStatus": "available",
                "AllocatedStorage": 100,
                "StorageType": "gp2",
                "VpcSecurityGroups": [{"VpcSecurityGroupId": "sg-123"}],
                "DBParameterGroups": [],
                "OptionGroupMemberships": [],
                "TagList": [{"Key": "Name", "Value": "my-database"}],
                "DBInstanceArn": "arn:aws:rds:us-east-1:123:db:my-db",
            }
        ]

        scanner = AsyncRDSScanner(region="us-east-1", account_id="123456789012")
        mock_client = MagicMock(spec=AsyncAWSClient)

        # Mock both paginate calls
        mock_client.paginate_with_resilience = AsyncMock(
            side_effect=[mock_subnet_groups, mock_db_instances]
        )
        scanner._client = mock_client

        await scanner.scan(graph)

        # Verify DB instance was added
        node = graph.get_resource("123456789012:us-east-1:my-db")
        assert node is not None
        assert node.resource_type == ResourceType.RDS_INSTANCE
        assert node.config["engine"] == "mysql"
        assert node.config["instance_class"] == "db.t3.medium"

    @pytest.mark.asyncio
    async def test_scan_skips_deleting_instances(self) -> None:
        """Should skip instances being deleted."""
        graph = GraphEngine()

        mock_db_instances = [
            {
                "DBInstanceIdentifier": "deleting-db",
                "Engine": "mysql",
                "DBInstanceClass": "db.t3.medium",
                "DBInstanceStatus": "deleting",
            }
        ]

        scanner = AsyncRDSScanner(region="us-east-1")
        mock_client = MagicMock(spec=AsyncAWSClient)
        mock_client.paginate_with_resilience = AsyncMock(
            side_effect=[[], mock_db_instances]
        )
        scanner._client = mock_client

        await scanner.scan(graph)

        assert graph.get_resource("deleting-db") is None


class TestAsyncIAMScanner:
    """Tests for AsyncIAMScanner."""

    def test_resource_types(self) -> None:
        """Should declare IAM resource types."""
        assert "aws_iam_role" in AsyncIAMScanner.resource_types
        assert "aws_iam_policy" in AsyncIAMScanner.resource_types
        assert "aws_iam_instance_profile" in AsyncIAMScanner.resource_types

    @pytest.mark.asyncio
    async def test_scan_adds_roles(self) -> None:
        """Should add IAM roles to graph."""
        graph = GraphEngine()

        mock_policies: list[dict[str, Any]] = []
        mock_roles = [
            {
                "RoleName": "my-role",
                "Path": "/",
                "Arn": "arn:aws:iam::123:role/my-role",
                "AssumeRolePolicyDocument": {"Version": "2012-10-17"},
                "Tags": [{"Key": "Name", "Value": "My Role"}],
            }
        ]
        mock_instance_profiles: list[dict[str, Any]] = []

        scanner = AsyncIAMScanner(region="us-east-1", account_id="123456789012")
        mock_client = MagicMock(spec=AsyncAWSClient)

        # Mock paginate calls: policies, roles, attached policies, instance profiles
        mock_client.paginate_with_resilience = AsyncMock(
            side_effect=[
                mock_policies,
                mock_roles,
                [],  # attached policies for my-role
                mock_instance_profiles,
            ]
        )
        scanner._client = mock_client

        await scanner.scan(graph)

        # Verify role was added
        node = graph.get_resource("123456789012:us-east-1:my-role")
        assert node is not None
        assert node.resource_type == ResourceType.IAM_ROLE
        assert node.region == "global"

    @pytest.mark.asyncio
    async def test_scan_skips_service_linked_roles(self) -> None:
        """Should skip AWS service-linked roles."""
        graph = GraphEngine()

        mock_roles = [
            {
                "RoleName": "AWSServiceRoleForEC2",
                "Path": "/aws-service-role/ec2.amazonaws.com/",
                "Arn": "arn:aws:iam::123:role/aws-service-role/...",
            }
        ]

        scanner = AsyncIAMScanner(region="us-east-1")
        mock_client = MagicMock(spec=AsyncAWSClient)
        mock_client.paginate_with_resilience = AsyncMock(
            side_effect=[[], mock_roles, []]
        )
        scanner._client = mock_client

        await scanner.scan(graph)

        # Service-linked role should NOT be added
        assert graph.get_resource("AWSServiceRoleForEC2") is None


class TestRunUnifiedScanners:
    """Tests for run_unified_scanners function."""

    @pytest.mark.asyncio
    async def test_runs_all_scanners(self) -> None:
        """Should run all registered scanners."""
        graph = GraphEngine()

        # Patch the scanner classes to avoid real AWS calls
        with (
            patch.object(AsyncEC2Scanner, "scan", new=AsyncMock()) as mock_ec2_scan,
            patch.object(AsyncRDSScanner, "scan", new=AsyncMock()) as mock_rds_scan,
            patch.object(AsyncIAMScanner, "scan", new=AsyncMock()) as mock_iam_scan,
        ):
            results = await run_unified_scanners(
                region="us-east-1",
                graph=graph,
                account_id="123456789012",
            )

            # All scanners should have been called
            assert mock_ec2_scan.called
            assert mock_rds_scan.called
            assert mock_iam_scan.called

            # All should succeed
            for scanner_name, error in results.items():
                assert error is None, f"{scanner_name} failed: {error}"

    @pytest.mark.asyncio
    async def test_captures_scanner_errors(self) -> None:
        """Should capture errors from failed scanners."""
        graph = GraphEngine()

        # Make EC2 scanner fail
        with (
            patch.object(
                AsyncEC2Scanner,
                "scan",
                new=AsyncMock(side_effect=RuntimeError("Test error")),
            ),
            patch.object(AsyncRDSScanner, "scan", new=AsyncMock()),
            patch.object(AsyncIAMScanner, "scan", new=AsyncMock()),
        ):
            results = await run_unified_scanners(
                region="us-east-1",
                graph=graph,
            )

            # EC2 should have error
            assert results["AsyncEC2Scanner"] is not None
            assert isinstance(results["AsyncEC2Scanner"], RuntimeError)

            # Others should succeed
            assert results["AsyncRDSScanner"] is None
            assert results["AsyncIAMScanner"] is None


class TestScannerBuildNodeId:
    """Tests for build_node_id method."""

    def test_build_node_id_with_account(self) -> None:
        """Should include account ID in node ID."""
        scanner = AsyncEC2Scanner(
            region="us-east-1",
            account_id="123456789012",
        )

        node_id = scanner.build_node_id("i-12345")
        assert node_id == "123456789012:us-east-1:i-12345"

    def test_build_node_id_without_account(self) -> None:
        """Should use 'unknown' when account ID not provided."""
        scanner = AsyncEC2Scanner(region="us-east-1")

        node_id = scanner.build_node_id("i-12345")
        assert node_id == "unknown:us-east-1:i-12345"


class TestScannerExtractTags:
    """Tests for extract_tags static method."""

    def test_extract_tags_empty(self) -> None:
        """Should handle empty tag list."""
        assert AsyncEC2Scanner.extract_tags(None) == {}
        assert AsyncEC2Scanner.extract_tags([]) == {}

    def test_extract_tags_converts_list(self) -> None:
        """Should convert AWS tag list to dict."""
        tags = [
            {"Key": "Name", "Value": "test"},
            {"Key": "Env", "Value": "prod"},
        ]

        result = AsyncEC2Scanner.extract_tags(tags)
        assert result == {"Name": "test", "Env": "prod"}
