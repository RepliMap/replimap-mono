"""
Graph visualization module for RepliMap.

Provides infrastructure visualization with:
- Multiple output formats (HTML, Mermaid, JSON)
- Graph simplification (filtering, grouping)
- Security-focused and full views
- Hierarchical container layout (VPCs/Subnets)
- Environment detection and filtering
- Smart VPC-based aggregation
- Overview mode with progressive disclosure
"""

from replimap.graph.aggregation import (
    AggregatedNode,
    AggregationConfig,
    SmartAggregator,
    create_aggregator,
)
from replimap.graph.builder import BuilderConfig, GraphBuilder
from replimap.graph.environment import (
    EnvironmentDetector,
    EnvironmentInfo,
)
from replimap.graph.filters import (
    NOISY_RESOURCE_TYPES,
    RESOURCE_VISIBILITY,
    ROUTE_TYPES,
    SG_RULE_TYPES,
    GraphFilter,
    ResourceVisibility,
)
from replimap.graph.grouper import (
    DEFAULT_COLLAPSE_THRESHOLD,
    GroupingConfig,
    GroupingStrategy,
    ResourceGroup,
    ResourceGrouper,
)
from replimap.graph.layout import (
    HierarchicalLayoutEngine,
    LayoutBox,
    LayoutConfig,
    LayoutNode,
    create_layout,
)
from replimap.graph.naming import (
    DisplayName,
    ResourceNamer,
    get_type_display_name,
    get_type_plural_name,
)
from replimap.graph.views import (
    GlobalCategorySummary,
    ViewManager,
    ViewMode,
    ViewState,
    VPCSummary,
)
from replimap.graph.visualizer import (
    RESOURCE_VISUALS,
    GraphEdge,
    GraphNode,
    GraphVisualizer,
    OutputFormat,
    VisualizationGraph,
)

__all__ = [
    # Visualizer
    "GraphVisualizer",
    "GraphNode",
    "GraphEdge",
    "VisualizationGraph",
    "OutputFormat",
    "RESOURCE_VISUALS",
    # Builder
    "GraphBuilder",
    "BuilderConfig",
    # Filter
    "GraphFilter",
    "ResourceVisibility",
    "RESOURCE_VISIBILITY",
    "NOISY_RESOURCE_TYPES",
    "SG_RULE_TYPES",
    "ROUTE_TYPES",
    # Grouper
    "ResourceGrouper",
    "ResourceGroup",
    "GroupingConfig",
    "GroupingStrategy",
    "DEFAULT_COLLAPSE_THRESHOLD",
    # Environment
    "EnvironmentDetector",
    "EnvironmentInfo",
    # Naming
    "ResourceNamer",
    "DisplayName",
    "get_type_display_name",
    "get_type_plural_name",
    # Layout
    "HierarchicalLayoutEngine",
    "LayoutBox",
    "LayoutNode",
    "LayoutConfig",
    "create_layout",
    # Aggregation
    "SmartAggregator",
    "AggregatedNode",
    "AggregationConfig",
    "create_aggregator",
    # Views
    "ViewManager",
    "ViewMode",
    "ViewState",
    "VPCSummary",
    "GlobalCategorySummary",
]
