"""
VCR-based scanner tests.

These tests use recorded AWS API responses (cassettes) for:
- Offline testing without AWS credentials
- Deterministic, reproducible tests
- Fast CI/CD (no network calls)

To record new cassettes:
    1. Set AWS credentials for a profile with resources
    2. Delete the cassette file you want to re-record
    3. Run the test - it will record actual AWS responses
    4. Cassette is saved and will be replayed on subsequent runs

Usage:
    # Run VCR tests
    pytest tests/test_vcr_scanners.py -v

    # Record new cassettes (requires AWS credentials)
    python scripts/record_cassettes.py --profile myprofile --region us-east-1
"""

from __future__ import annotations

import pytest

from tests.conftest import VCR_AVAILABLE, use_cassette
from tests.vcr_async import AsyncVCRTestCase, async_vcr_cassette

# Skip all tests in this module if VCR is not available
pytestmark = pytest.mark.skipif(
    not VCR_AVAILABLE,
    reason="VCR.py not installed (pip install vcrpy)",
)


class TestVCRConfiguration:
    """Test VCR configuration and fixtures."""

    def test_vcr_is_available(self) -> None:
        """Verify VCR is properly configured."""
        from tests.conftest import CASSETTES_DIR, vcr_config

        assert VCR_AVAILABLE is True
        assert vcr_config is not None
        assert CASSETTES_DIR.exists()

    def test_sanitize_response_removes_account_ids(self) -> None:
        """Test that account IDs are sanitized."""
        from tests.conftest import sanitize_response

        response = {
            "body": {
                "string": b"account: 987654321098, arn:aws:ec2:us-east-1:987654321098:instance/i-123"
            }
        }

        sanitized = sanitize_response(response)
        body = sanitized["body"]["string"].decode("utf-8")

        # Account IDs should be replaced with placeholder
        assert "987654321098" not in body
        assert "123456789012" in body

    def test_sanitize_response_removes_access_keys(self) -> None:
        """Test that access keys are sanitized."""
        from tests.conftest import sanitize_response

        response = {"body": {"string": b"key: AKIAIOSFODNN7REALKEY"}}

        sanitized = sanitize_response(response)
        body = sanitized["body"]["string"].decode("utf-8")

        # Real key should be replaced
        assert "REALKEY" not in body
        assert "AKIAIOSFODNN7EXAMPLE" in body


class TestVCRFixtureUsage:
    """Examples of using VCR fixtures and decorators."""

    @use_cassette("example_empty")
    def test_with_decorator(self) -> None:
        """
        Example test with @use_cassette decorator.

        When this test runs:
        1. First run: Records any HTTP calls to example_empty.yaml
        2. Subsequent runs: Replays from cassette (no network)
        """
        # This test doesn't make actual calls
        # It demonstrates the pattern
        assert True

    def test_with_fixture(self, vcr_cassette: object) -> None:
        """
        Example test with vcr_cassette fixture.

        The fixture provides a context manager for the cassette.
        """
        # The cassette is automatically named from test name:
        # test_with_fixture.yaml
        assert vcr_cassette is not None


class TestVCRAsyncPatterns:
    """Examples of async VCR patterns."""

    @async_vcr_cassette("example_async")
    async def test_async_with_decorator(self) -> None:
        """
        Example async test with VCR.

        The @async_vcr_cassette decorator handles:
        1. Setting up the cassette context
        2. Running the async function
        3. Tearing down the cassette
        """
        # This demonstrates the pattern for async scanner tests
        import asyncio

        await asyncio.sleep(0)  # Minimal async operation
        assert True


class TestAsyncVCRTestCase(AsyncVCRTestCase):
    """
    Example of AsyncVCRTestCase usage.

    Each test method gets its own cassette automatically named:
    {cassette_name}_{method_name}.yaml
    """

    cassette_name = "example_async_class"

    async def test_automatic_cassette(self) -> None:
        """
        This test uses cassette: example_async_class_test_automatic_cassette.yaml
        """
        import asyncio

        await asyncio.sleep(0)
        assert True


# ═══════════════════════════════════════════════════════════════════════════════
# Scanner Tests with VCR (Examples)
# ═══════════════════════════════════════════════════════════════════════════════
#
# Below are patterns for testing actual scanners with VCR.
# These require cassettes to be recorded first.
#
# To record:
#   python scripts/record_cassettes.py --profile your-profile --region us-east-1


class TestVPCScannerWithVCR:
    """
    VPC scanner tests using recorded cassettes.

    These tests require a vpc_scan.yaml cassette to exist.
    Record it with: python scripts/record_cassettes.py --scanner vpc
    """

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("vpc_scan")
    def test_vpc_scan_from_cassette(self) -> None:
        """Test VPC scanning with recorded responses."""
        from unittest.mock import MagicMock

        from replimap.core import GraphEngine
        from replimap.scanners.vpc_scanner import VPCScanner

        # Create a mock session - VCR handles the actual HTTP calls
        session = MagicMock()
        session.client.return_value = session
        session.region_name = "us-east-1"

        _graph = GraphEngine()  # noqa: F841
        _scanner = VPCScanner(session, "us-east-1")  # noqa: F841

        # This would use the recorded cassette
        # _scanner.scan(_graph)

        # Assertions would verify the graph structure
        # assert graph.statistics()["total_resources"] > 0


class TestEC2ScannerWithVCR:
    """
    EC2 scanner tests using recorded cassettes.

    Demonstrates testing EC2 instance discovery with VCR.
    """

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("ec2_scan")
    def test_ec2_scan_from_cassette(self) -> None:
        """Test EC2 scanning with recorded responses."""
        # Similar pattern to VPC scanner test
        pass

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("ec2_empty_account")
    def test_ec2_empty_account(self) -> None:
        """Test EC2 scanning when account has no instances."""
        # Test edge case: empty account
        pass

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("ec2_pagination")
    def test_ec2_pagination(self) -> None:
        """Test EC2 scanning handles pagination correctly."""
        # Test edge case: many instances requiring pagination
        pass


class TestS3ScannerWithVCR:
    """S3 scanner tests using recorded cassettes."""

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("s3_scan")
    def test_s3_list_buckets(self) -> None:
        """Test S3 bucket discovery with recorded responses."""
        pass


class TestRDSScannerWithVCR:
    """RDS scanner tests using recorded cassettes."""

    @pytest.mark.skip(reason="Requires recorded cassette")
    @use_cassette("rds_scan")
    def test_rds_scan_from_cassette(self) -> None:
        """Test RDS scanning with recorded responses."""
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Integration Test Patterns
# ═══════════════════════════════════════════════════════════════════════════════


class TestFullScanWithVCR:
    """
    Full scan integration tests.

    These tests run multiple scanners and verify the complete graph.
    Requires cassettes from: python scripts/record_cassettes.py --scanner all
    """

    @pytest.mark.skip(reason="Requires recorded cassettes for all scanners")
    @use_cassette("full_scan")
    def test_full_scan_integration(self) -> None:
        """
        Test complete AWS scan with all scanners.

        This is an integration test that:
        1. Runs all scanners (using recorded responses)
        2. Verifies graph structure
        3. Checks dependency relationships
        """
        pass
