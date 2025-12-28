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
- Multi-region graph aggregation
- Global resource context and views
"""

from replimap.graph.aggregation import (
    AggregatedNode,
    AggregationConfig,
    SmartAggregator,
    create_aggregator,
)
from replimap.graph.blast_radius import (
    AffectedResource,
    BlastRadiusCalculator,
    BlastRadiusResult,
    ImpactSeverity,
    calculate_blast_radius,
    enrich_nodes_with_blast_radius,
    find_critical_nodes,
)
from replimap.graph.builder import BuilderConfig, GraphBuilder
from replimap.graph.cost_overlay import (
    CostCalculator,
    CostEstimate,
    CostTier,
    calculate_container_cost,
    enrich_nodes_with_cost,
    generate_cost_overlay_css,
    generate_cost_overlay_js,
)
from replimap.graph.drift import (
    DriftDetector,
    DriftedAttribute,
    DriftResult,
    DriftSeverity,
    DriftStatus,
    detect_drift_from_plan,
    enrich_nodes_with_drift,
    generate_drift_visualization_css,
    generate_drift_visualization_js,
)
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
from replimap.graph.link_classification import (
    LinkType,
    classify_link,
    enrich_links_with_classification,
    get_dependency_links,
    get_traffic_flow_links,
)
from replimap.graph.naming import (
    DisplayName,
    ResourceNamer,
    get_type_display_name,
    get_type_plural_name,
)
from replimap.graph.orphan_detection import (
    OrphanDetector,
    OrphanedResource,
    OrphanReason,
    OrphanSeverity,
    calculate_orphan_costs,
    detect_orphans,
    enrich_nodes_with_orphan_status,
    generate_orphan_visualization_css,
    generate_orphan_visualization_js,
)
from replimap.graph.summary_links import (
    SummaryLink,
    SummaryLinkCalculator,
    calculate_summary_links,
)
from replimap.graph.tool_modes import (
    ToolMode,
    generate_tool_palette_css,
    generate_tool_palette_html,
    generate_tool_palette_js,
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
from replimap.graph.multi_region import (
    COMMON_REGIONS,
    REGION_COLORS,
    REGION_DISPLAY_NAMES,
    REGION_GROUPS,
    MultiRegionConfig,
    MultiRegionGraph,
    MultiRegionScanner,
    RegionGroup,
    RegionScanResult,
    aggregate_regional_graphs,
    calculate_region_distribution,
    create_multi_region_scanner,
    detect_primary_region,
    enrich_nodes_with_region,
    get_region_color,
    get_regions_for_group,
)
from replimap.graph.global_context import (
    CATEGORY_COLORS,
    CATEGORY_ICONS,
    RESOURCE_CATEGORY,
    GlobalCategory,
    GlobalContext,
    GlobalContextConfig,
    GlobalContextExtractor,
    GlobalResourceType,
    SuperNode,
    ViewMode as GlobalViewMode,
    categorize_node,
    extract_global_context,
    find_unused_global_resources,
    get_iam_role_usage,
    is_global_resource,
    merge_global_context,
)
from replimap.graph.cross_region import (
    CrossRegionAnalysis,
    CrossRegionDependency,
    CrossRegionDetector,
    CrossRegionType,
    ReplicationDirection,
    calculate_replication_coverage,
    detect_cross_region_dependencies,
    enrich_graph_with_cross_region,
    find_single_region_resources,
    get_cross_region_pairs,
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
    # Link Classification
    "LinkType",
    "classify_link",
    "enrich_links_with_classification",
    "get_dependency_links",
    "get_traffic_flow_links",
    # Summary Links
    "SummaryLink",
    "SummaryLinkCalculator",
    "calculate_summary_links",
    # Tool Modes
    "ToolMode",
    "generate_tool_palette_css",
    "generate_tool_palette_html",
    "generate_tool_palette_js",
    # Cost Overlay
    "CostCalculator",
    "CostEstimate",
    "CostTier",
    "calculate_container_cost",
    "enrich_nodes_with_cost",
    "generate_cost_overlay_css",
    "generate_cost_overlay_js",
    # Blast Radius
    "AffectedResource",
    "BlastRadiusCalculator",
    "BlastRadiusResult",
    "ImpactSeverity",
    "calculate_blast_radius",
    "enrich_nodes_with_blast_radius",
    "find_critical_nodes",
    # Drift Detection
    "DriftDetector",
    "DriftResult",
    "DriftSeverity",
    "DriftStatus",
    "DriftedAttribute",
    "detect_drift_from_plan",
    "enrich_nodes_with_drift",
    "generate_drift_visualization_css",
    "generate_drift_visualization_js",
    # Orphan Detection
    "OrphanDetector",
    "OrphanReason",
    "OrphanSeverity",
    "OrphanedResource",
    "calculate_orphan_costs",
    "detect_orphans",
    "enrich_nodes_with_orphan_status",
    "generate_orphan_visualization_css",
    "generate_orphan_visualization_js",
    # Multi-Region
    "MultiRegionScanner",
    "MultiRegionGraph",
    "MultiRegionConfig",
    "RegionScanResult",
    "RegionGroup",
    "REGION_GROUPS",
    "REGION_COLORS",
    "REGION_DISPLAY_NAMES",
    "COMMON_REGIONS",
    "aggregate_regional_graphs",
    "create_multi_region_scanner",
    "enrich_nodes_with_region",
    "get_region_color",
    "get_regions_for_group",
    "detect_primary_region",
    "calculate_region_distribution",
    # Global Context
    "GlobalContext",
    "GlobalContextConfig",
    "GlobalContextExtractor",
    "GlobalCategory",
    "GlobalResourceType",
    "GlobalViewMode",
    "SuperNode",
    "CATEGORY_COLORS",
    "CATEGORY_ICONS",
    "RESOURCE_CATEGORY",
    "extract_global_context",
    "merge_global_context",
    "get_iam_role_usage",
    "find_unused_global_resources",
    "categorize_node",
    "is_global_resource",
    # Cross-Region Dependencies
    "CrossRegionDetector",
    "CrossRegionDependency",
    "CrossRegionAnalysis",
    "CrossRegionType",
    "ReplicationDirection",
    "detect_cross_region_dependencies",
    "enrich_graph_with_cross_region",
    "get_cross_region_pairs",
    "find_single_region_resources",
    "calculate_replication_coverage",
]
