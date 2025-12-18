"""Tests for async scanners."""

from replimap.scanners.async_base import (
    AsyncScannerRegistry,
)
from replimap.scanners.async_vpc_scanner import AsyncVPCScanner


class TestAsyncScannerRegistry:
    """Tests for AsyncScannerRegistry."""

    def test_scanner_is_registered(self) -> None:
        """Test that AsyncVPCScanner is registered."""
        scanners = AsyncScannerRegistry.get_all()
        scanner_names = [s.__name__ for s in scanners]
        assert "AsyncVPCScanner" in scanner_names

    def test_clear_registry(self) -> None:
        """Test clearing the registry."""
        # Store current scanners
        original = AsyncScannerRegistry.get_all()

        AsyncScannerRegistry.clear()
        assert len(AsyncScannerRegistry.get_all()) == 0

        # Restore by re-registering
        for scanner in original:
            AsyncScannerRegistry.register(scanner)


class TestAsyncVPCScanner:
    """Tests for AsyncVPCScanner."""

    def test_has_resource_types(self) -> None:
        """Test that scanner declares resource types."""
        assert "aws_vpc" in AsyncVPCScanner.resource_types
        assert "aws_subnet" in AsyncVPCScanner.resource_types
        assert "aws_security_group" in AsyncVPCScanner.resource_types

    def test_extract_tags(self) -> None:
        """Test tag extraction helper."""
        scanner = AsyncVPCScanner(region="us-east-1")

        # Test with valid tags
        tags = [{"Key": "Name", "Value": "test"}, {"Key": "Env", "Value": "prod"}]
        result = scanner._extract_tags(tags)
        assert result == {"Name": "test", "Env": "prod"}

        # Test with None
        assert scanner._extract_tags(None) == {}

        # Test with empty list
        assert scanner._extract_tags([]) == {}

    def test_process_rule(self) -> None:
        """Test security group rule processing."""
        scanner = AsyncVPCScanner(region="us-east-1")

        rule = {
            "IpProtocol": "tcp",
            "FromPort": 443,
            "ToPort": 443,
            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
        }

        processed = scanner._process_rule(rule)

        assert processed["protocol"] == "tcp"
        assert processed["from_port"] == 443
        assert processed["to_port"] == 443
        assert processed["cidr_blocks"] == ["0.0.0.0/0"]

    def test_process_rule_with_security_groups(self) -> None:
        """Test rule processing with security group references."""
        scanner = AsyncVPCScanner(region="us-east-1")

        rule = {
            "IpProtocol": "-1",
            "UserIdGroupPairs": [{"GroupId": "sg-12345", "UserId": "123456789012"}],
        }

        processed = scanner._process_rule(rule)

        assert processed["protocol"] == "-1"
        assert len(processed["security_groups"]) == 1
        assert processed["security_groups"][0]["security_group_id"] == "sg-12345"
