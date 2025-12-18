"""Core engine components for RepliMap."""

from .cache import (
    ScanCache,
    populate_graph_from_cache,
    update_cache_from_graph,
)
from .filters import ScanFilter, apply_filter_to_graph
from .graph_engine import GraphEngine
from .models import ResourceNode
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
