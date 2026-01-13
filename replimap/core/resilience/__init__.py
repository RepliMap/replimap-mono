"""
Resilience patterns for AWS API calls.

This module provides production-grade resilience patterns:
- CircuitBreaker: Prevents cascading failures with ErrorClassification integration
- CircuitBreakerRegistry: Manages circuit breakers per service/region with S3 hybrid
- CircuitOpenError: Raised when circuit is open
- BackpressureMonitor: Tracks latency and signals slowdown

Key Features:
- Separate thresholds for throttling vs regular failures
- Fatal errors (AccessDenied) don't trip circuit breaker
- S3 hybrid strategy (global for ListBuckets, regional for ListObjects)
- Async-safe with proper locking
"""

from replimap.core.resilience.circuit_breaker import (
    BackpressureMonitor,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
)
from replimap.core.resilience.errors import (
    BotocoreErrorLoader,
    ErrorAction,
    ErrorClassification,
    ErrorClassifier,
    ErrorContext,
    ServiceSpecificRules,
)

__all__ = [
    # Circuit Breaker
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitOpenError",
    "BackpressureMonitor",
    # Error Handling
    "ErrorAction",
    "ErrorClassification",
    "ErrorContext",
    "ErrorClassifier",
    "BotocoreErrorLoader",
    "ServiceSpecificRules",
]
