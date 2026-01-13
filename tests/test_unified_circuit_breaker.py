"""
Comprehensive tests for the unified circuit breaker module.

Tests cover:
- Circuit breaker state transitions
- ErrorClassification integration
- should_count_for_circuit behavior
- S3 hybrid key generation
- Registry functionality
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from replimap.core.errors.classifier import ErrorAction, ErrorClassification
from replimap.core.resilience.circuit_breaker import (
    BackpressureMonitor,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
)


class TestCircuitBreakerConfig:
    """Tests for circuit breaker configuration."""

    def test_default_config(self) -> None:
        """Default config should have reasonable values."""
        config = CircuitBreakerConfig()

        assert config.failure_threshold == 5
        assert config.throttle_failure_threshold == 10
        assert config.success_threshold == 2
        assert config.timeout_seconds == 60.0
        assert config.window_seconds == 60.0

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            throttle_failure_threshold=5,
            success_threshold=1,
            timeout_seconds=30.0,
        )

        assert config.failure_threshold == 3
        assert config.throttle_failure_threshold == 5
        assert config.success_threshold == 1
        assert config.timeout_seconds == 30.0


class TestCircuitBreaker:
    """Tests for circuit breaker state machine."""

    @pytest.fixture
    def breaker(self) -> CircuitBreaker:
        """Create a circuit breaker with fast config for testing."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            throttle_failure_threshold=5,
            success_threshold=2,
            timeout_seconds=1.0,  # Fast timeout for tests
        )
        return CircuitBreaker(name="test:us-east-1", config=config)

    def test_initial_state_is_closed(self, breaker: CircuitBreaker) -> None:
        """Circuit should start CLOSED."""
        assert breaker.state == CircuitState.CLOSED

    def test_success_keeps_circuit_closed(self, breaker: CircuitBreaker) -> None:
        """Successful calls should keep circuit CLOSED."""
        breaker.record_result(success=True)
        breaker.record_result(success=True)
        breaker.record_result(success=True)

        assert breaker.state == CircuitState.CLOSED

    # ═══════════════════════════════════════════════════════════════════════
    # FAILURE COUNTING TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_failures_open_circuit(self, breaker: CircuitBreaker) -> None:
        """Enough failures should open circuit."""
        classification = ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            reason="Test error",
        )

        breaker.record_result(success=False, classification=classification)
        breaker.record_result(success=False, classification=classification)
        assert breaker.state == CircuitState.CLOSED  # Not yet

        breaker.record_result(success=False, classification=classification)
        assert breaker.state == CircuitState.OPEN  # Now open

    def test_fatal_errors_do_not_open_circuit(self, breaker: CircuitBreaker) -> None:
        """Fatal errors (should_count_for_circuit=False) should NOT open circuit."""
        fatal_classification = ErrorClassification(
            action=ErrorAction.FAIL,
            should_count_for_circuit=False,  # KEY: This is the bug fix
            reason="AccessDenied",
        )

        # Record many fatal errors
        for _ in range(10):
            breaker.record_result(success=False, classification=fatal_classification)

        # Circuit should still be CLOSED
        assert breaker.state == CircuitState.CLOSED

    def test_mixed_errors_only_count_retryable(self, breaker: CircuitBreaker) -> None:
        """Only errors with should_count_for_circuit=True should count."""
        retryable = ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            reason="ServiceUnavailable",
        )
        fatal = ErrorClassification(
            action=ErrorAction.FAIL,
            should_count_for_circuit=False,
            reason="AccessDenied",
        )

        # Mix of errors - only 2 retryable
        breaker.record_result(success=False, classification=fatal)
        breaker.record_result(success=False, classification=retryable)
        breaker.record_result(success=False, classification=fatal)
        breaker.record_result(success=False, classification=retryable)
        breaker.record_result(success=False, classification=fatal)

        # Should still be CLOSED (only 2 counted, need 3)
        assert breaker.state == CircuitState.CLOSED

        # One more retryable opens it
        breaker.record_result(success=False, classification=retryable)
        assert breaker.state == CircuitState.OPEN

    # ═══════════════════════════════════════════════════════════════════════
    # THROTTLING THRESHOLD TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_throttling_uses_higher_threshold(self, breaker: CircuitBreaker) -> None:
        """Throttling errors should use higher threshold (5 instead of 3)."""
        throttle = ErrorClassification(
            action=ErrorAction.BACKOFF,  # Indicates throttling
            should_count_for_circuit=True,
            reason="Throttling",
        )

        # 4 throttle errors - should still be closed
        for _ in range(4):
            breaker.record_result(success=False, classification=throttle)

        assert breaker.state == CircuitState.CLOSED

        # 5th opens it
        breaker.record_result(success=False, classification=throttle)
        assert breaker.state == CircuitState.OPEN

    # ═══════════════════════════════════════════════════════════════════════
    # STATE TRANSITION TESTS
    # ═══════════════════════════════════════════════════════════════════════

    @pytest.mark.asyncio
    async def test_circuit_transitions_to_half_open_after_timeout(
        self, breaker: CircuitBreaker
    ) -> None:
        """Circuit should go to HALF_OPEN after timeout."""
        classification = ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            reason="Test",
        )

        # Open the circuit
        for _ in range(3):
            breaker.record_result(success=False, classification=classification)

        assert breaker.state == CircuitState.OPEN

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Trigger state check
        breaker._check_state_transition()

        assert breaker.state == CircuitState.HALF_OPEN

    def test_half_open_closes_after_successes(self, breaker: CircuitBreaker) -> None:
        """Circuit should close after enough successes in HALF_OPEN."""
        # Manually set to HALF_OPEN
        breaker._state = CircuitState.HALF_OPEN
        breaker._stats.successes = 0

        # Need 2 successes to close
        breaker.record_result(success=True)
        assert breaker.state == CircuitState.HALF_OPEN

        breaker.record_result(success=True)
        assert breaker.state == CircuitState.CLOSED

    def test_half_open_reopens_on_failure(self, breaker: CircuitBreaker) -> None:
        """Any failure in HALF_OPEN should reopen circuit."""
        breaker._state = CircuitState.HALF_OPEN

        classification = ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            reason="Test",
        )

        breaker.record_result(success=False, classification=classification)

        assert breaker.state == CircuitState.OPEN

    # ═══════════════════════════════════════════════════════════════════════
    # RESET TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_reset_closes_circuit(self, breaker: CircuitBreaker) -> None:
        """Reset should close circuit and clear stats."""
        # Open the circuit
        breaker._state = CircuitState.OPEN
        breaker._stats.failures = 10

        breaker.reset()

        assert breaker.state == CircuitState.CLOSED
        assert breaker._stats.failures == 0

    # ═══════════════════════════════════════════════════════════════════════
    # STATS TESTS
    # ═══════════════════════════════════════════════════════════════════════

    def test_get_stats(self, breaker: CircuitBreaker) -> None:
        """Should return useful statistics."""
        classification = ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            reason="Test",
        )

        breaker.record_result(success=True)
        breaker.record_result(success=False, classification=classification)

        stats = breaker.get_stats()

        assert stats["name"] == "test:us-east-1"
        assert stats["state"] == "CLOSED"
        assert stats["failures"] == 1
        assert stats["successes"] == 1


@pytest.mark.asyncio
class TestCircuitBreakerRegistry:
    """Tests for circuit breaker registry."""

    async def asyncSetUp(self) -> None:
        """Reset registry before each test."""
        CircuitBreakerRegistry.reset_all_sync()

    async def test_creates_breaker_for_new_key(self) -> None:
        """Should create new breaker for unknown key."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
        )

        assert breaker is not None
        assert breaker.name == "ec2:us-east-1"

    async def test_returns_same_breaker_for_same_key(self) -> None:
        """Should return cached breaker for same key."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker1 = await CircuitBreakerRegistry.get_breaker(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
        )
        breaker2 = await CircuitBreakerRegistry.get_breaker(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeSecurityGroups",  # Different operation
        )

        # Same key (ec2:us-east-1), so same breaker
        assert breaker1 is breaker2

    async def test_different_regions_get_different_breakers(self) -> None:
        """Different regions should get different breakers."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker1 = await CircuitBreakerRegistry.get_breaker(
            service_name="ec2",
            region="us-east-1",
            operation_name="DescribeInstances",
        )
        breaker2 = await CircuitBreakerRegistry.get_breaker(
            service_name="ec2",
            region="eu-west-1",
            operation_name="DescribeInstances",
        )

        assert breaker1 is not breaker2
        assert breaker1.name == "ec2:us-east-1"
        assert breaker2.name == "ec2:eu-west-1"

    async def test_s3_hybrid_global_operation(self) -> None:
        """S3 global operations should share one breaker."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker_us = await CircuitBreakerRegistry.get_breaker(
            service_name="s3",
            region="us-east-1",
            operation_name="ListBuckets",
        )
        breaker_eu = await CircuitBreakerRegistry.get_breaker(
            service_name="s3",
            region="eu-west-1",
            operation_name="ListBuckets",
        )

        # Both should use s3:global
        assert breaker_us is breaker_eu
        assert breaker_us.name == "s3:global"

    async def test_s3_hybrid_regional_operation(self) -> None:
        """S3 regional operations should get per-region breakers."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker_us = await CircuitBreakerRegistry.get_breaker(
            service_name="s3",
            region="us-east-1",
            operation_name="ListObjectsV2",
        )
        breaker_eu = await CircuitBreakerRegistry.get_breaker(
            service_name="s3",
            region="eu-west-1",
            operation_name="ListObjectsV2",
        )

        # Should be different (regional)
        assert breaker_us is not breaker_eu
        assert breaker_us.name == "s3:us-east-1"
        assert breaker_eu.name == "s3:eu-west-1"

    async def test_iam_always_global(self) -> None:
        """IAM should always use global breaker."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name="iam",
            region="us-west-2",
            operation_name="GetUser",
        )

        assert breaker.name == "iam:global"

    async def test_get_open_circuits(self) -> None:
        """Should list all open circuits."""
        CircuitBreakerRegistry.reset_all_sync()

        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name="rds",
            region="us-east-1",
            operation_name="DescribeDBInstances",
        )

        # Open the circuit
        breaker._state = CircuitState.OPEN

        open_circuits = await CircuitBreakerRegistry.get_open_circuits()
        assert "rds:us-east-1" in open_circuits


@pytest.mark.asyncio
class TestBackpressureMonitor:
    """Tests for backpressure monitoring."""

    async def test_initial_state_no_slowdown(self) -> None:
        """Should not slow down with no history."""
        await BackpressureMonitor.reset()

        result = await BackpressureMonitor.should_slow_down()
        assert result is False

    async def test_low_latency_no_slowdown(self) -> None:
        """Low latency should not trigger slowdown."""
        await BackpressureMonitor.reset()

        for _ in range(20):
            await BackpressureMonitor.record_latency(100.0)  # 100ms

        result = await BackpressureMonitor.should_slow_down()
        assert result is False

    async def test_high_latency_triggers_slowdown(self) -> None:
        """High latency should trigger slowdown."""
        await BackpressureMonitor.reset()

        for _ in range(20):
            await BackpressureMonitor.record_latency(3000.0)  # 3s

        result = await BackpressureMonitor.should_slow_down()
        assert result is True

    async def test_get_average_latency(self) -> None:
        """Should calculate correct average latency."""
        await BackpressureMonitor.reset()

        await BackpressureMonitor.record_latency(100.0)
        await BackpressureMonitor.record_latency(200.0)
        await BackpressureMonitor.record_latency(300.0)

        avg = await BackpressureMonitor.get_average_latency()
        assert avg == 200.0


class TestCircuitOpenError:
    """Tests for CircuitOpenError exception."""

    def test_retry_after_seconds(self) -> None:
        """Should store retry_after_seconds."""
        error = CircuitOpenError("Test", retry_after_seconds=30.0)

        assert error.retry_after_seconds == 30.0
        assert str(error) == "Test"

    def test_default_retry_after(self) -> None:
        """Should default to 0 retry_after_seconds."""
        error = CircuitOpenError("Test")

        assert error.retry_after_seconds == 0
