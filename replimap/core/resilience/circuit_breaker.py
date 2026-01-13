"""
Hybrid Circuit Breaker with operation-aware isolation.

This circuit breaker implementation provides:
1. Per-service/region isolation (with S3 hybrid strategy)
2. Separate thresholds for throttling vs other failures
3. Respect for ErrorClassification.should_count_for_circuit
4. Thread-safe state management
5. Async-safe with proper locking

Key Design Decisions:

1. Throttling Has Higher Threshold:
   Throttling is expected under load and often clears quickly.
   We use threshold of 10 (vs 5 for other errors) to avoid
   opening circuit too eagerly.

2. Fatal Errors Don't Count:
   AccessDenied, ValidationException, etc. are configuration
   problems, not service health problems. Counting them would
   cause a single IAM mistake to trip the circuit.

3. S3 Hybrid Isolation:
   S3 has both global (ListBuckets) and regional (ListObjects)
   operations. We use ServiceSpecificRules to determine the
   correct circuit breaker key.
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, ClassVar, TypeVar

from replimap.core.errors.classifier import (
    ErrorAction,
    ErrorClassification,
    ErrorClassifier,
    ErrorContext,
)
from replimap.core.errors.rules import ServiceSpecificRules

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker state."""

    CLOSED = auto()  # Normal operation
    OPEN = auto()  # Blocking all calls
    HALF_OPEN = auto()  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """
    Circuit breaker configuration.

    Attributes:
        failure_threshold: Number of failures before opening circuit (default: 5)
        throttle_failure_threshold: Threshold for throttling errors (default: 10)
        success_threshold: Successes needed to close circuit from half-open (default: 2)
        timeout_seconds: How long circuit stays open before half-open (default: 60)
        window_seconds: Time window for counting failures (default: 60)
    """

    failure_threshold: int = 5
    throttle_failure_threshold: int = 10
    success_threshold: int = 2
    timeout_seconds: float = 60.0
    window_seconds: float = 60.0


@dataclass
class CircuitStats:
    """Internal statistics for circuit breaker."""

    failures: int = 0
    throttle_failures: int = 0
    successes: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    state_changed_at: datetime = field(default_factory=datetime.utcnow)

    def reset(self) -> None:
        """Reset all counters."""
        self.failures = 0
        self.throttle_failures = 0
        self.successes = 0
        self.last_failure_time = None
        self.last_success_time = None


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, retry_after_seconds: float = 0) -> None:
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class CircuitBreaker:
    """
    Circuit breaker with ErrorClassification integration.

    Usage:
        breaker = CircuitBreaker(name="ec2:us-east-1")

        classification = classifier.classify(error, context)
        breaker.record_result(success=False, classification=classification)

        if breaker.state == CircuitState.OPEN:
            raise CircuitOpenError(...)

    Or use the call() method for automatic handling:

        result = await breaker.call(
            func=client.describe_instances,
            classifier=classifier,
            context=context,
        )
    """

    def __init__(
        self,
        name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            name: Identifier for this circuit (e.g., "ec2:us-east-1")
            config: Configuration options
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._stats = CircuitStats()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        return self._state

    async def call(
        self,
        func: Callable[..., T],
        classifier: ErrorClassifier,
        context: ErrorContext,
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute function through circuit breaker.

        Args:
            func: Async function to execute
            classifier: Error classifier for handling failures
            context: Error context for classification
            *args, **kwargs: Arguments to pass to func

        Returns:
            Result of func

        Raises:
            CircuitOpenError: If circuit is open
            Original exception: If func fails and shouldn't be suppressed
        """
        async with self._lock:
            self._check_state_transition()

            if self._state == CircuitState.OPEN:
                retry_after = self._seconds_until_retry()
                raise CircuitOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Retry after {retry_after:.1f} seconds.",
                    retry_after_seconds=retry_after,
                )

        try:
            result = await func(*args, **kwargs)

            async with self._lock:
                self._record_success()

            return result

        except Exception as e:
            classification = classifier.classify(e, context)

            async with self._lock:
                self._record_failure(classification)

            raise

    def record_result(
        self,
        success: bool,
        classification: ErrorClassification | None = None,
    ) -> None:
        """
        Record a result (for manual circuit breaker management).

        Args:
            success: Whether the operation succeeded
            classification: Error classification (required if success=False)
        """
        if success:
            self._record_success()
        elif classification:
            self._record_failure(classification)

    def _check_state_transition(self) -> None:
        """Check and perform state transitions."""
        now = datetime.utcnow()

        if self._state == CircuitState.OPEN:
            # Check if we should transition to HALF_OPEN
            elapsed = (now - self._stats.state_changed_at).total_seconds()
            if elapsed >= self.config.timeout_seconds:
                logger.info(
                    f"Circuit '{self.name}' transitioning OPEN -> HALF_OPEN "
                    f"after {elapsed:.1f}s timeout"
                )
                self._state = CircuitState.HALF_OPEN
                self._stats.state_changed_at = now
                self._stats.successes = 0

        elif self._state == CircuitState.CLOSED:
            # Clean up old failures outside the window
            if self._stats.last_failure_time:
                window = timedelta(seconds=self.config.window_seconds)
                if now - self._stats.last_failure_time > window:
                    self._stats.failures = 0
                    self._stats.throttle_failures = 0

    def _record_success(self) -> None:
        """Record a successful call."""
        self._stats.successes += 1
        self._stats.last_success_time = datetime.utcnow()

        if self._state == CircuitState.HALF_OPEN:
            if self._stats.successes >= self.config.success_threshold:
                logger.info(
                    f"Circuit '{self.name}' transitioning HALF_OPEN -> CLOSED "
                    f"after {self._stats.successes} successes"
                )
                self._state = CircuitState.CLOSED
                self._stats.reset()

    def _record_failure(self, classification: ErrorClassification) -> None:
        """
        Record a failed call.

        CRITICAL: Only counts if classification.should_count_for_circuit is True.
        """
        # KEY CHECK: Fatal errors don't count toward circuit
        if not classification.should_count_for_circuit:
            logger.debug(
                f"Circuit '{self.name}' not counting failure: {classification.reason}"
            )
            return

        self._stats.last_failure_time = datetime.utcnow()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            logger.warning(
                f"Circuit '{self.name}' transitioning HALF_OPEN -> OPEN "
                f"due to failure: {classification.reason}"
            )
            self._trip_circuit()
            return

        # Count failure based on type
        if classification.action == ErrorAction.BACKOFF:
            # Throttling error - use higher threshold
            self._stats.throttle_failures += 1
            if self._stats.throttle_failures >= self.config.throttle_failure_threshold:
                logger.warning(
                    f"Circuit '{self.name}' OPEN due to throttling "
                    f"({self._stats.throttle_failures} failures)"
                )
                self._trip_circuit()
        else:
            # Regular failure
            self._stats.failures += 1
            if self._stats.failures >= self.config.failure_threshold:
                logger.warning(
                    f"Circuit '{self.name}' OPEN due to failures "
                    f"({self._stats.failures} failures)"
                )
                self._trip_circuit()

    def _trip_circuit(self) -> None:
        """Open the circuit."""
        self._state = CircuitState.OPEN
        self._stats.state_changed_at = datetime.utcnow()

    def _seconds_until_retry(self) -> float:
        """Calculate seconds until circuit can be retried."""
        elapsed = (datetime.utcnow() - self._stats.state_changed_at).total_seconds()
        return max(0, self.config.timeout_seconds - elapsed)

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.name,
            "failures": self._stats.failures,
            "throttle_failures": self._stats.throttle_failures,
            "successes": self._stats.successes,
            "last_failure": (
                self._stats.last_failure_time.isoformat()
                if self._stats.last_failure_time
                else None
            ),
            "state_changed_at": self._stats.state_changed_at.isoformat(),
        }

    def reset(self) -> None:
        """Reset the circuit breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._stats.reset()
        logger.info(f"Circuit '{self.name}' manually reset to CLOSED")


class CircuitBreakerRegistry:
    """
    Registry for circuit breakers with automatic key generation.

    Usage:
        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name='s3',
            region='us-east-1',
            operation_name='ListObjectsV2',
        )

        # For S3 ListBuckets (global):
        # Returns breaker with key "s3:global"

        # For S3 ListObjectsV2 (regional):
        # Returns breaker with key "s3:us-east-1"
    """

    _breakers: ClassVar[dict[str, CircuitBreaker]] = {}
    _lock: ClassVar[asyncio.Lock | None] = None
    _default_config: ClassVar[CircuitBreakerConfig | None] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the lock (lazy initialization for thread safety)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def get_breaker(
        cls,
        service_name: str,
        region: str,
        operation_name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker for a service/region/operation.

        Uses ServiceSpecificRules to determine the correct key:
        - Global operations: "{service}:global"
        - Regional operations: "{service}:{region}"

        Args:
            service_name: AWS service name (e.g., 's3')
            region: AWS region (e.g., 'us-east-1')
            operation_name: API operation (e.g., 'ListObjectsV2')
            config: Optional custom configuration

        Returns:
            CircuitBreaker instance
        """
        key = ServiceSpecificRules.get_circuit_breaker_key(
            service_name, region, operation_name
        )

        async with cls._get_lock():
            if key not in cls._breakers:
                effective_config = config or cls._default_config or CircuitBreakerConfig()
                cls._breakers[key] = CircuitBreaker(
                    name=key,
                    config=effective_config,
                )
                logger.debug(f"Created circuit breaker: {key}")

            return cls._breakers[key]

    @classmethod
    def get_breaker_sync(
        cls,
        service_name: str,
        region: str,
        operation_name: str,
        config: CircuitBreakerConfig | None = None,
    ) -> CircuitBreaker:
        """
        Synchronous version of get_breaker for non-async contexts.

        Args:
            service_name: AWS service name
            region: AWS region
            operation_name: API operation
            config: Optional custom configuration

        Returns:
            CircuitBreaker instance
        """
        key = ServiceSpecificRules.get_circuit_breaker_key(
            service_name, region, operation_name
        )

        if key not in cls._breakers:
            effective_config = config or cls._default_config or CircuitBreakerConfig()
            cls._breakers[key] = CircuitBreaker(
                name=key,
                config=effective_config,
            )
            logger.debug(f"Created circuit breaker (sync): {key}")

        return cls._breakers[key]

    @classmethod
    async def get_all_stats(cls) -> dict[str, dict[str, Any]]:
        """Get statistics for all circuit breakers."""
        async with cls._get_lock():
            return {name: breaker.get_stats() for name, breaker in cls._breakers.items()}

    @classmethod
    async def get_open_circuits(cls) -> list[str]:
        """Get list of currently open circuit breakers."""
        async with cls._get_lock():
            return [
                name
                for name, breaker in cls._breakers.items()
                if breaker.state == CircuitState.OPEN
            ]

    @classmethod
    def set_default_config(cls, config: CircuitBreakerConfig) -> None:
        """Set default configuration for new circuit breakers."""
        cls._default_config = config

    @classmethod
    async def reset_all(cls) -> None:
        """Reset all circuit breakers (for testing)."""
        async with cls._get_lock():
            cls._breakers.clear()
        logger.info("All circuit breakers reset")

    @classmethod
    def reset_all_sync(cls) -> None:
        """Synchronous reset for testing."""
        cls._breakers.clear()
        logger.info("All circuit breakers reset (sync)")


class BackpressureMonitor:
    """
    Monitor API latency and signal backpressure.

    When average latency exceeds threshold, scanners should slow down
    to prevent cascading failures.
    """

    _latency_history: ClassVar[deque[float]] = deque(maxlen=100)
    _slowdown_threshold_ms: ClassVar[float] = 2000.0
    _lock: ClassVar[asyncio.Lock | None] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the lock."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    async def record_latency(cls, latency_ms: float) -> None:
        """Record an API call latency."""
        async with cls._get_lock():
            cls._latency_history.append(latency_ms)

    @classmethod
    async def should_slow_down(cls) -> bool:
        """Check if scanners should slow down due to high latency."""
        async with cls._get_lock():
            if len(cls._latency_history) < 10:
                return False
            avg = sum(cls._latency_history) / len(cls._latency_history)
            return avg > cls._slowdown_threshold_ms

    @classmethod
    async def get_average_latency(cls) -> float:
        """Get current average latency."""
        async with cls._get_lock():
            if not cls._latency_history:
                return 0.0
            return sum(cls._latency_history) / len(cls._latency_history)

    @classmethod
    async def reset(cls) -> None:
        """Reset latency history (for testing)."""
        async with cls._get_lock():
            cls._latency_history.clear()

    @classmethod
    def set_threshold(cls, threshold_ms: float) -> None:
        """Set the slowdown threshold."""
        cls._slowdown_threshold_ms = threshold_ms
