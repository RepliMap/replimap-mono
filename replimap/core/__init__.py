"""Core engine components for RepliMap."""

from .aws_config import BOTO_CONFIG, get_boto_config
from .cache import (
    ScanCache,
    populate_graph_from_cache,
    update_cache_from_graph,
)
from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitOpenError,
    CircuitState,
    get_circuit_breaker_registry,
)
from .filters import ScanFilter, apply_filter_to_graph
from .graph_engine import GraphEngine, SCCResult, TarjanSCC
from .models import ResourceNode
from .retry import async_retry, with_retry
from .sanitizer import (
    SanitizationResult,
    Sanitizer,
    sanitize_resource_config,
    sanitize_scan_response,
)
from .selection import (
    BoundaryAction,
    BoundaryConfig,
    CloneAction,
    CloneDecisionEngine,
    CloneMode,
    DependencyDirection,
    GraphSelector,
    SelectionMode,
    SelectionResult,
    SelectionStrategy,
    TargetContext,
    apply_selection,
    build_subgraph_from_selection,
)

__all__ = [
    # Models
    "ResourceNode",
    "GraphEngine",
    # SCC Analysis
    "SCCResult",
    "TarjanSCC",
    # AWS Config
    "BOTO_CONFIG",
    "get_boto_config",
    # Retry
    "with_retry",
    "async_retry",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitOpenError",
    "CircuitState",
    "get_circuit_breaker_registry",
    # Sanitization
    "Sanitizer",
    "SanitizationResult",
    "sanitize_resource_config",
    "sanitize_scan_response",
    # Legacy filters (for backwards compatibility)
    "ScanFilter",
    "apply_filter_to_graph",
    # Cache
    "ScanCache",
    "populate_graph_from_cache",
    "update_cache_from_graph",
    # Selection engine
    "SelectionMode",
    "DependencyDirection",
    "BoundaryAction",
    "CloneAction",
    "CloneMode",
    "BoundaryConfig",
    "TargetContext",
    "SelectionStrategy",
    "SelectionResult",
    "CloneDecisionEngine",
    "GraphSelector",
    "apply_selection",
    "build_subgraph_from_selection",
]
