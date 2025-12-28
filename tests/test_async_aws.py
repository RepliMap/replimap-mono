"""
Tests for the async AWS client wrapper.

Tests cover:
- Rate limiter token bucket behavior
- Circuit breaker integration
- Retry logic for transient errors
- Client caching and lifecycle
- Resource scanner base class
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest
from botocore.exceptions import ClientError

from replimap.core.async_aws import (
    AsyncAWSClient,
    AsyncRateLimiter,
    AWSResourceScanner,
    CallStats,
    RateLimiterRegistry,
    get_rate_limiter_registry,
)
from replimap.core.circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
)


class TestAsyncRateLimiter:
    """Tests for AsyncRateLimiter."""

    @pytest.mark.asyncio
    async def test_acquire_immediate_with_tokens(self) -> None:
        """Acquire should be immediate when tokens are available."""
        limiter = AsyncRateLimiter(requests_per_second=10.0, burst_size=5)

        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should be nearly instant (< 100ms)
        assert elapsed < 0.1

    @pytest.mark.asyncio
    async def test_acquire_waits_when_depleted(self) -> None:
        """Acquire should wait when tokens are depleted."""
        # Low rate to force waiting
        limiter = AsyncRateLimiter(requests_per_second=10.0, burst_size=1)

        # Exhaust the single token
        await limiter.acquire()

        # Next acquire should wait
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        # Should have waited ~100ms for token refill
        assert elapsed >= 0.05  # At least 50ms wait

    @pytest.mark.asyncio
    async def test_burst_allows_multiple_immediate(self) -> None:
        """Burst size should allow multiple immediate acquires."""
        limiter = AsyncRateLimiter(requests_per_second=5.0, burst_size=5)

        start = time.monotonic()
        # Should be able to acquire burst_size tokens immediately
        for _ in range(5):
            await limiter.acquire()
        elapsed = time.monotonic() - start

        # All 5 should complete quickly (burst)
        assert elapsed < 0.2

    @pytest.mark.asyncio
    async def test_tokens_refill_over_time(self) -> None:
        """Tokens should refill based on elapsed time."""
        limiter = AsyncRateLimiter(requests_per_second=100.0, burst_size=2)

        # Exhaust tokens
        await limiter.acquire()
        await limiter.acquire()

        # Wait for refill
        await asyncio.sleep(0.1)  # Should get ~10 tokens back

        # Should be able to acquire immediately now
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start

        assert elapsed < 0.05


class TestRateLimiterRegistry:
    """Tests for RateLimiterRegistry."""

    @pytest.mark.asyncio
    async def test_get_creates_limiter(self) -> None:
        """Get should create a new limiter if none exists."""
        registry = RateLimiterRegistry()

        limiter = await registry.get("ec2")
        assert limiter is not None
        assert isinstance(limiter, AsyncRateLimiter)

    @pytest.mark.asyncio
    async def test_get_returns_same_limiter(self) -> None:
        """Get should return the same limiter for the same service."""
        registry = RateLimiterRegistry()

        limiter1 = await registry.get("ec2")
        limiter2 = await registry.get("ec2")

        assert limiter1 is limiter2

    @pytest.mark.asyncio
    async def test_different_services_different_limiters(self) -> None:
        """Different services should get different limiters."""
        registry = RateLimiterRegistry()

        ec2_limiter = await registry.get("ec2")
        rds_limiter = await registry.get("rds")

        assert ec2_limiter is not rds_limiter

    @pytest.mark.asyncio
    async def test_region_isolation(self) -> None:
        """Same service in different regions should get different limiters."""
        registry = RateLimiterRegistry()

        east_limiter = await registry.get("ec2", "us-east-1")
        west_limiter = await registry.get("ec2", "us-west-2")

        assert east_limiter is not west_limiter

    @pytest.mark.asyncio
    async def test_stats(self) -> None:
        """Stats should return information about all limiters."""
        registry = RateLimiterRegistry()

        await registry.get("ec2")
        await registry.get("rds")

        stats = registry.stats()

        assert "ec2" in stats
        assert "rds" in stats


class TestCallStats:
    """Tests for CallStats."""

    def test_default_values(self) -> None:
        """Stats should start at zero."""
        stats = CallStats()

        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.retried_calls == 0
        assert stats.failed_calls == 0
        assert stats.circuit_breaker_skips == 0


class TestAsyncAWSClientUnit:
    """Unit tests for AsyncAWSClient (mocked AWS)."""

    @pytest.mark.asyncio
    async def test_call_success(self) -> None:
        """Successful API call should return result."""
        client = AsyncAWSClient(region="us-east-1")

        # Mock the aiobotocore client
        mock_ec2 = AsyncMock()
        mock_ec2.describe_vpcs = AsyncMock(
            return_value={"Vpcs": [{"VpcId": "vpc-123"}]}
        )

        with patch.object(client, "_get_client") as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_ec2)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await client.call("ec2", "describe_vpcs")

            assert "Vpcs" in result
            assert client.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_call_circuit_open(self) -> None:
        """Should raise CircuitOpenError when circuit is open."""
        circuit_registry = CircuitBreakerRegistry()
        client = AsyncAWSClient(
            region="us-east-1",
            circuit_registry=circuit_registry,
        )

        # Force circuit open
        circuit = circuit_registry.get_for_region_service("us-east-1", "ec2")
        circuit.force_open()

        with pytest.raises(CircuitOpenError):
            await client.call("ec2", "describe_vpcs")

        assert client.stats.circuit_breaker_skips == 1

    @pytest.mark.asyncio
    async def test_call_retries_on_throttling(self) -> None:
        """Should retry on throttling errors."""
        client = AsyncAWSClient(region="us-east-1", max_retries=2)

        mock_ec2 = AsyncMock()
        # First call: throttle, second call: success
        throttle_error = ClientError(
            {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
            "DescribeVpcs",
        )
        mock_ec2.describe_vpcs = AsyncMock(side_effect=[throttle_error, {"Vpcs": []}])

        with patch.object(client, "_get_client") as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_ec2)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Patch sleep to speed up test
            with patch("replimap.core.async_aws.asyncio.sleep", new=AsyncMock()):
                result = await client.call("ec2", "describe_vpcs")

            assert result == {"Vpcs": []}
            assert client.stats.retried_calls == 1
            assert client.stats.successful_calls == 1

    @pytest.mark.asyncio
    async def test_call_no_retry_on_access_denied(self) -> None:
        """Should not retry on access denied (fatal error)."""
        client = AsyncAWSClient(region="us-east-1", max_retries=3)

        mock_ec2 = AsyncMock()
        access_denied = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Permission denied"}},
            "DescribeVpcs",
        )
        mock_ec2.describe_vpcs = AsyncMock(side_effect=access_denied)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_ec2)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            with pytest.raises(ClientError) as exc_info:
                await client.call("ec2", "describe_vpcs")

            assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
            assert client.stats.failed_calls == 1
            assert client.stats.retried_calls == 0  # No retries for fatal errors

    @pytest.mark.asyncio
    async def test_call_exhausts_retries(self) -> None:
        """Should fail after exhausting retries."""
        # Use a fresh circuit registry with high threshold to avoid circuit opening
        circuit_registry = CircuitBreakerRegistry(failure_threshold=100)
        client = AsyncAWSClient(
            region="us-east-1",
            max_retries=2,
            circuit_registry=circuit_registry,
        )

        mock_ec2 = AsyncMock()
        throttle_error = ClientError(
            {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
            "DescribeVpcs",
        )
        mock_ec2.describe_vpcs = AsyncMock(side_effect=throttle_error)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_ec2)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            with patch("replimap.core.async_aws.asyncio.sleep", new=AsyncMock()):
                with pytest.raises(ClientError):
                    await client.call("ec2", "describe_vpcs")

            # Should have tried max_retries + 1 times
            assert mock_ec2.describe_vpcs.call_count == 3
            assert client.stats.failed_calls == 1


class TestAWSResourceScanner:
    """Tests for AWSResourceScanner base class."""

    def test_build_node_id(self) -> None:
        """Should build node ID in correct format."""
        scanner = AWSResourceScanner(
            region="us-east-1",
            account_id="123456789012",
        )

        node_id = scanner.build_node_id("vpc-abc123")

        assert node_id == "123456789012:us-east-1:vpc-abc123"

    def test_build_node_id_unknown_account(self) -> None:
        """Should use 'unknown' for missing account ID."""
        scanner = AWSResourceScanner(region="us-east-1")

        node_id = scanner.build_node_id("vpc-abc123")

        assert node_id == "unknown:us-east-1:vpc-abc123"

    def test_extract_tags_empty(self) -> None:
        """Should handle empty tag list."""
        tags = AWSResourceScanner.extract_tags(None)
        assert tags == {}

        tags = AWSResourceScanner.extract_tags([])
        assert tags == {}

    def test_extract_tags_converts_list(self) -> None:
        """Should convert AWS tag list to dict."""
        tag_list = [
            {"Key": "Name", "Value": "test-vpc"},
            {"Key": "Environment", "Value": "dev"},
        ]

        tags = AWSResourceScanner.extract_tags(tag_list)

        assert tags == {"Name": "test-vpc", "Environment": "dev"}


class TestCircuitBreakerIntegration:
    """Tests for circuit breaker integration with AsyncAWSClient."""

    @pytest.mark.asyncio
    async def test_failures_open_circuit(self) -> None:
        """Repeated failures should open the circuit."""
        circuit_registry = CircuitBreakerRegistry(failure_threshold=2)
        client = AsyncAWSClient(
            region="us-east-1",
            circuit_registry=circuit_registry,
            max_retries=0,  # No retries for this test
        )

        mock_ec2 = AsyncMock()
        # Non-retryable error that still counts as failure
        error = ClientError(
            {"Error": {"Code": "InternalError", "Message": "Oops"}},
            "DescribeVpcs",
        )
        mock_ec2.describe_vpcs = AsyncMock(side_effect=error)

        with patch.object(client, "_get_client") as mock_get_client:
            mock_get_client.return_value.__aenter__ = AsyncMock(return_value=mock_ec2)
            mock_get_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # First failure
            with pytest.raises(ClientError):
                await client.call("ec2", "describe_vpcs")

            # Second failure - should open circuit
            with pytest.raises(ClientError):
                await client.call("ec2", "describe_vpcs")

            # Circuit should now be open
            circuit = circuit_registry.get_for_region_service("us-east-1", "ec2")
            assert circuit.state == CircuitState.OPEN

            # Third call should be blocked by circuit
            with pytest.raises(CircuitOpenError):
                await client.call("ec2", "describe_vpcs")


class TestGlobalRegistry:
    """Tests for global registry singleton."""

    def test_get_rate_limiter_registry_singleton(self) -> None:
        """Should return the same registry instance."""
        # Note: This test might be flaky in parallel test runs
        # due to global state. Reset the global before testing.
        import replimap.core.async_aws as async_aws_module

        # Reset global
        async_aws_module._rate_limiter_registry = None

        registry1 = get_rate_limiter_registry()
        registry2 = get_rate_limiter_registry()

        assert registry1 is registry2


class TestAsyncContextManager:
    """Tests for async context manager behavior."""

    @pytest.mark.asyncio
    async def test_client_context_manager(self) -> None:
        """Client should work as async context manager."""
        async with AsyncAWSClient(region="us-east-1") as client:
            assert client is not None
            assert client.region == "us-east-1"

    @pytest.mark.asyncio
    async def test_scanner_context_manager(self) -> None:
        """Scanner should work as async context manager."""
        async with AWSResourceScanner(
            region="us-east-1",
            account_id="123456789012",
        ) as scanner:
            assert scanner is not None
            assert scanner.region == "us-east-1"
            assert scanner.account_id == "123456789012"
