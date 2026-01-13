"""
Core engine components for RepliMap.

This module provides the core infrastructure for RepliMap including:
- Graph storage (SQLite-backed with NetworkX compatibility)
- Error handling utilities
- Resilience patterns

IMPORTANT MIGRATION NOTE (v2.0):
    As of v2.0, GraphEngine now uses SQLite backend via GraphEngineAdapter.
    This provides 10-100x performance improvement with zero code changes.

    To use legacy NetworkX backend (NOT RECOMMENDED):
        export REPLIMAP_USE_LEGACY_STORAGE=1

    For explicit SQLite usage:
        from replimap.core.unified_storage import UnifiedGraphEngine
"""

from __future__ import annotations

import os
import warnings
from typing import TYPE_CHECKING, Any

from .async_aws import (
    AsyncAWSClient,
    AsyncRateLimiter,
    AWSResourceScanner,
    CallStats,
    RateLimiterRegistry,
    get_rate_limiter_registry,
)
from .aws_config import BOTO_CONFIG, get_boto_config
from .bootstrap import (
    EnvironmentDetector,
    ProviderSchemaLoader,
    SchemaBootstrapper,
    VersionAwareBootstrapper,
)
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
from .concurrency import (
    check_shutdown,
    create_thread_pool,
    is_shutdown_requested,
    reset_shutdown_state,
    shutdown_all_executors,
)
from .config import ConfigLoader, RepliMapConfig, deep_merge, generate_example_config
from .errors import (
    DetailedError,
    ErrorAggregator,
    ErrorCategory,
    ScanCompletionStatus,
    categorize_error,
    get_error_aggregator,
    get_recovery_recommendation,
    is_retryable,
    reset_error_aggregator,
)
from .filters import ScanFilter, apply_filter_to_graph
from .models import ResourceNode

# ═══════════════════════════════════════════════════════════════════════════════
# STORAGE LAYER SWITCH (The "Zero-Code Migration" Trick)
# ═══════════════════════════════════════════════════════════════════════════════

# Check for legacy mode escape hatch
_USE_LEGACY_STORAGE = os.environ.get("REPLIMAP_USE_LEGACY_STORAGE", "").lower() in (
    "1",
    "true",
    "yes",
)

if _USE_LEGACY_STORAGE:
    warnings.warn(
        "REPLIMAP_USE_LEGACY_STORAGE is set. Using deprecated NetworkX backend. "
        "This mode will be removed in v3.0. Please migrate to SQLite backend.",
        DeprecationWarning,
        stacklevel=2,
    )
    # Import legacy class directly
    from .graph_engine import GraphEngine as _LegacyGraphEngine
    from .graph_engine import SCCResult, TarjanSCC

    GraphEngine = _LegacyGraphEngine
else:
    # ═══════════════════════════════════════════════════════════════════════════
    # THIS IS THE KEY LINE: GraphEngine now points to SQLite-backed adapter
    # ═══════════════════════════════════════════════════════════════════════════
    from .unified_storage import GraphEngineAdapter as GraphEngine
    from .unified_storage import SCCResult

    # TarjanSCC is only available from legacy module (for direct usage)
    from .graph_engine import TarjanSCC

# Storage backend identifier
__storage_backend__ = "legacy-networkx" if _USE_LEGACY_STORAGE else "sqlite"


def get_storage_info() -> dict[str, Any]:
    """
    Get information about current storage backend.

    Returns:
        Dictionary with storage backend details.

    Example:
        >>> from replimap.core import get_storage_info
        >>> get_storage_info()
        {'backend': 'sqlite', 'legacy_mode': False, 'version': '2.0.0'}
    """
    return {
        "backend": __storage_backend__,
        "legacy_mode": _USE_LEGACY_STORAGE,
        "version": "2.0.0",
        "adapter_class": GraphEngine.__name__,
    }


if TYPE_CHECKING:
    from replimap.core.unified_storage import UnifiedGraphEngine
from .retry import async_retry, with_retry
from .sanitizer import (
    SanitizationResult,
    Sanitizer,
    sanitize_resource_config,
    sanitize_scan_response,
)
from .scope import (
    DataSourceRenderer,
    ResourceScope,
    ScopeEngine,
    ScopeResult,
    ScopeRule,
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
from .state import (
    ErrorRecord,
    RepliMapState,
    ScanRecord,
    SnapshotInfo,
    StateManager,
    compute_config_hash,
)
from .storage import (
    ConfigCompressor,
    GraphStore,
    NodeInfo,
    StorageStats,
    migrate_from_cache,
    migrate_from_json,
)
from .topology_constraints import (
    ConstraintType,
    ConstraintViolation,
    TopologyConstraint,
    TopologyConstraintsConfig,
    TopologyValidator,
    ValidationResult,
    ViolationSeverity,
    create_default_constraints,
    generate_sample_config_yaml,
    load_constraints_from_yaml,
    validate_topology,
)

__all__ = [
    # Models
    "ResourceNode",
    "GraphEngine",
    # Storage Info (v2.0)
    "get_storage_info",
    # SCC Analysis
    "SCCResult",
    "TarjanSCC",
    # Async AWS Client
    "AsyncAWSClient",
    "AsyncRateLimiter",
    "AWSResourceScanner",
    "CallStats",
    "RateLimiterRegistry",
    "get_rate_limiter_registry",
    # AWS Config
    "BOTO_CONFIG",
    "get_boto_config",
    # Error Handling
    "DetailedError",
    "ErrorAggregator",
    "ErrorCategory",
    "ScanCompletionStatus",
    "categorize_error",
    "get_error_aggregator",
    "get_recovery_recommendation",
    "is_retryable",
    "reset_error_aggregator",
    # Configuration (Level 2-5)
    "ConfigLoader",
    "RepliMapConfig",
    "deep_merge",
    "generate_example_config",
    # Scope Engine (Level 2-5)
    "ScopeEngine",
    "ScopeResult",
    "ScopeRule",
    "ResourceScope",
    "DataSourceRenderer",
    # Bootstrap (Level 2-5)
    "SchemaBootstrapper",
    "VersionAwareBootstrapper",
    "EnvironmentDetector",
    "ProviderSchemaLoader",
    # Retry
    "with_retry",
    "async_retry",
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerRegistry",
    "CircuitOpenError",
    "CircuitState",
    "get_circuit_breaker_registry",
    # Concurrency (Global Thread Pool Management)
    "create_thread_pool",
    "shutdown_all_executors",
    "is_shutdown_requested",
    "check_shutdown",
    "reset_shutdown_state",
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
    # Storage Engine
    "GraphStore",
    "NodeInfo",
    "StorageStats",
    "ConfigCompressor",
    "migrate_from_json",
    "migrate_from_cache",
    # State Management
    "StateManager",
    "RepliMapState",
    "ScanRecord",
    "SnapshotInfo",
    "ErrorRecord",
    "compute_config_hash",
    # Topology Constraints (P3-3)
    "TopologyValidator",
    "TopologyConstraint",
    "TopologyConstraintsConfig",
    "ConstraintType",
    "ConstraintViolation",
    "ValidationResult",
    "ViolationSeverity",
    "load_constraints_from_yaml",
    "validate_topology",
    "create_default_constraints",
    "generate_sample_config_yaml",
]
