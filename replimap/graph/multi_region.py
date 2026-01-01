"""
Multi-Region Graph Aggregation for RepliMap.

Provides capabilities to:
- Scan multiple AWS regions in parallel
- Aggregate resources into a unified graph
- Label nodes with region attributes
- Detect cross-region relationships

This module enables global infrastructure visualization
by combining resources from all regions into a single
coherent graph with proper region attribution.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import as_completed

from replimap.core.concurrency import create_thread_pool
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from replimap.graph.visualizer import (
    GraphEdge,
    GraphNode,
    VisualizationGraph,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Standard AWS regions organized by geography
class RegionGroup(str, Enum):
    """AWS region groups by geography."""

    US_EAST = "us-east"
    US_WEST = "us-west"
    EU = "eu"
    ASIA_PACIFIC = "asia-pacific"
    SOUTH_AMERICA = "south-america"
    MIDDLE_EAST = "middle-east"
    AFRICA = "africa"
    CANADA = "canada"

    def __str__(self) -> str:
        return self.value


# Map regions to their geographic groups
REGION_GROUPS: dict[str, RegionGroup] = {
    # US East
    "us-east-1": RegionGroup.US_EAST,
    "us-east-2": RegionGroup.US_EAST,
    # US West
    "us-west-1": RegionGroup.US_WEST,
    "us-west-2": RegionGroup.US_WEST,
    # Europe
    "eu-west-1": RegionGroup.EU,
    "eu-west-2": RegionGroup.EU,
    "eu-west-3": RegionGroup.EU,
    "eu-central-1": RegionGroup.EU,
    "eu-central-2": RegionGroup.EU,
    "eu-north-1": RegionGroup.EU,
    "eu-south-1": RegionGroup.EU,
    "eu-south-2": RegionGroup.EU,
    # Asia Pacific
    "ap-southeast-1": RegionGroup.ASIA_PACIFIC,
    "ap-southeast-2": RegionGroup.ASIA_PACIFIC,
    "ap-southeast-3": RegionGroup.ASIA_PACIFIC,
    "ap-southeast-4": RegionGroup.ASIA_PACIFIC,
    "ap-northeast-1": RegionGroup.ASIA_PACIFIC,
    "ap-northeast-2": RegionGroup.ASIA_PACIFIC,
    "ap-northeast-3": RegionGroup.ASIA_PACIFIC,
    "ap-south-1": RegionGroup.ASIA_PACIFIC,
    "ap-south-2": RegionGroup.ASIA_PACIFIC,
    "ap-east-1": RegionGroup.ASIA_PACIFIC,
    # South America
    "sa-east-1": RegionGroup.SOUTH_AMERICA,
    # Middle East
    "me-south-1": RegionGroup.MIDDLE_EAST,
    "me-central-1": RegionGroup.MIDDLE_EAST,
    # Africa
    "af-south-1": RegionGroup.AFRICA,
    # Canada
    "ca-central-1": RegionGroup.CANADA,
    "ca-west-1": RegionGroup.CANADA,
}

# Common AWS regions for quick scanning
COMMON_REGIONS = [
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-central-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
]

# Region display names
REGION_DISPLAY_NAMES: dict[str, str] = {
    "us-east-1": "N. Virginia",
    "us-east-2": "Ohio",
    "us-west-1": "N. California",
    "us-west-2": "Oregon",
    "eu-west-1": "Ireland",
    "eu-west-2": "London",
    "eu-west-3": "Paris",
    "eu-central-1": "Frankfurt",
    "eu-central-2": "Zurich",
    "eu-north-1": "Stockholm",
    "eu-south-1": "Milan",
    "eu-south-2": "Spain",
    "ap-southeast-1": "Singapore",
    "ap-southeast-2": "Sydney",
    "ap-southeast-3": "Jakarta",
    "ap-southeast-4": "Melbourne",
    "ap-northeast-1": "Tokyo",
    "ap-northeast-2": "Seoul",
    "ap-northeast-3": "Osaka",
    "ap-south-1": "Mumbai",
    "ap-south-2": "Hyderabad",
    "ap-east-1": "Hong Kong",
    "sa-east-1": "São Paulo",
    "me-south-1": "Bahrain",
    "me-central-1": "UAE",
    "af-south-1": "Cape Town",
    "ca-central-1": "Montreal",
    "ca-west-1": "Calgary",
}


@dataclass
class RegionScanResult:
    """Result of scanning a single region."""

    region: str
    graph: VisualizationGraph | None
    resource_count: int
    error: str | None = None
    scan_time_ms: float = 0.0

    @property
    def success(self) -> bool:
        """Check if scan was successful."""
        return self.error is None and self.graph is not None

    @property
    def display_name(self) -> str:
        """Get human-readable region name."""
        return REGION_DISPLAY_NAMES.get(self.region, self.region)

    @property
    def region_group(self) -> RegionGroup | None:
        """Get the geographic group for this region."""
        return REGION_GROUPS.get(self.region)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "region": self.region,
            "display_name": self.display_name,
            "region_group": str(self.region_group) if self.region_group else None,
            "success": self.success,
            "resource_count": self.resource_count,
            "error": self.error,
            "scan_time_ms": round(self.scan_time_ms, 2),
        }


@dataclass
class MultiRegionConfig:
    """Configuration for multi-region scanning."""

    # Regions to scan (empty = all available)
    regions: list[str] = field(default_factory=list)

    # Maximum parallel scans
    max_parallel: int = 5

    # Timeout per region (seconds)
    region_timeout: float = 300.0

    # Skip regions with no resources
    skip_empty: bool = True

    # Include region prefix in node IDs
    prefix_node_ids: bool = True

    # Add region attribute to all nodes
    add_region_attribute: bool = True

    # Use region colors for visual distinction
    use_region_colors: bool = True

    @classmethod
    def default(cls) -> MultiRegionConfig:
        """Create default configuration."""
        return cls(regions=COMMON_REGIONS.copy())

    @classmethod
    def all_regions(cls) -> MultiRegionConfig:
        """Create configuration for all AWS regions."""
        return cls(regions=list(REGION_GROUPS.keys()))

    @classmethod
    def us_only(cls) -> MultiRegionConfig:
        """Create configuration for US regions only."""
        return cls(
            regions=[
                r
                for r, g in REGION_GROUPS.items()
                if g in (RegionGroup.US_EAST, RegionGroup.US_WEST)
            ]
        )

    @classmethod
    def eu_only(cls) -> MultiRegionConfig:
        """Create configuration for EU regions only."""
        return cls(regions=[r for r, g in REGION_GROUPS.items() if g == RegionGroup.EU])

    @classmethod
    def asia_pacific_only(cls) -> MultiRegionConfig:
        """Create configuration for Asia Pacific regions only."""
        return cls(
            regions=[
                r for r, g in REGION_GROUPS.items() if g == RegionGroup.ASIA_PACIFIC
            ]
        )


# Region-based color palette for visual distinction
REGION_COLORS: dict[RegionGroup, str] = {
    RegionGroup.US_EAST: "#3b82f6",  # Blue
    RegionGroup.US_WEST: "#8b5cf6",  # Purple
    RegionGroup.EU: "#10b981",  # Green
    RegionGroup.ASIA_PACIFIC: "#f59e0b",  # Amber
    RegionGroup.SOUTH_AMERICA: "#ef4444",  # Red
    RegionGroup.MIDDLE_EAST: "#ec4899",  # Pink
    RegionGroup.AFRICA: "#14b8a6",  # Teal
    RegionGroup.CANADA: "#6366f1",  # Indigo
}


def get_region_color(region: str) -> str:
    """Get the color for a specific region."""
    group = REGION_GROUPS.get(region)
    if group:
        return REGION_COLORS.get(group, "#6b7280")  # Default gray
    return "#6b7280"


@dataclass
class MultiRegionGraph:
    """
    Aggregated graph from multiple regions.

    Combines resources from multiple AWS regions into a single
    unified graph with proper region attribution and cross-region
    relationship detection.
    """

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    region_results: dict[str, RegionScanResult] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_resources(self) -> int:
        """Total number of resources across all regions."""
        return len(self.nodes)

    @property
    def regions_scanned(self) -> list[str]:
        """List of regions that were scanned."""
        return list(self.region_results.keys())

    @property
    def successful_regions(self) -> list[str]:
        """List of regions that were scanned successfully."""
        return [r for r, result in self.region_results.items() if result.success]

    @property
    def failed_regions(self) -> list[str]:
        """List of regions that failed to scan."""
        return [r for r, result in self.region_results.items() if not result.success]

    @property
    def resources_by_region(self) -> dict[str, int]:
        """Count of resources per region."""
        return {
            r: result.resource_count
            for r, result in self.region_results.items()
            if result.success
        }

    @property
    def resources_by_type(self) -> dict[str, int]:
        """Count of resources by type across all regions."""
        counts: dict[str, int] = {}
        for node in self.nodes:
            counts[node.resource_type] = counts.get(node.resource_type, 0) + 1
        return counts

    def get_nodes_in_region(self, region: str) -> list[GraphNode]:
        """Get all nodes in a specific region."""
        return [node for node in self.nodes if node.properties.get("region") == region]

    def get_cross_region_edges(self) -> list[GraphEdge]:
        """Get edges that connect resources in different regions."""
        # Build node->region mapping
        node_regions: dict[str, str] = {}
        for node in self.nodes:
            node_regions[node.id] = node.properties.get("region", "unknown")

        # Find edges crossing regions
        cross_region: list[GraphEdge] = []
        for edge in self.edges:
            source_region = node_regions.get(edge.source, "unknown")
            target_region = node_regions.get(edge.target, "unknown")
            if source_region != target_region:
                cross_region.append(edge)

        return cross_region

    def to_visualization_graph(self) -> VisualizationGraph:
        """Convert to a standard VisualizationGraph."""
        return VisualizationGraph(
            nodes=self.nodes.copy(),
            edges=self.edges.copy(),
            metadata={
                **self.metadata,
                "multi_region": True,
                "regions": self.regions_scanned,
                "resources_by_region": self.resources_by_region,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.resource_type,
                    "name": n.name,
                    "properties": n.properties,
                    "icon": n.icon,
                    "color": n.color,
                    "group": n.group,
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                    "type": e.edge_type,
                }
                for e in self.edges
            ],
            "metadata": self.metadata,
            "regions": {
                region: result.to_dict()
                for region, result in self.region_results.items()
            },
            "summary": {
                "total_resources": self.total_resources,
                "regions_scanned": len(self.regions_scanned),
                "successful_regions": len(self.successful_regions),
                "failed_regions": len(self.failed_regions),
                "resources_by_region": self.resources_by_region,
                "resources_by_type": self.resources_by_type,
                "cross_region_edges": len(self.get_cross_region_edges()),
            },
        }


class MultiRegionScanner:
    """
    Scanner for aggregating resources across multiple AWS regions.

    Uses parallel scanning to efficiently collect resources from
    multiple regions and aggregate them into a unified graph.
    """

    def __init__(
        self,
        config: MultiRegionConfig | None = None,
        graph_builder_factory: Callable[[str], Any] | None = None,
    ) -> None:
        """
        Initialize the multi-region scanner.

        Args:
            config: Multi-region configuration
            graph_builder_factory: Factory function that creates a graph builder
                                   for a given region. If None, uses default.
        """
        self.config = config or MultiRegionConfig.default()
        self._graph_builder_factory = graph_builder_factory

    def _scan_region(
        self,
        region: str,
        scan_func: Callable[[str], VisualizationGraph],
    ) -> RegionScanResult:
        """
        Scan a single region.

        Args:
            region: AWS region code
            scan_func: Function that takes a region and returns a VisualizationGraph

        Returns:
            RegionScanResult with the scan results
        """
        import time

        start_time = time.time()

        try:
            graph = scan_func(region)
            elapsed_ms = (time.time() - start_time) * 1000

            return RegionScanResult(
                region=region,
                graph=graph,
                resource_count=len(graph.nodes) if graph else 0,
                scan_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Failed to scan region {region}: {e}")
            return RegionScanResult(
                region=region,
                graph=None,
                resource_count=0,
                error=str(e),
                scan_time_ms=elapsed_ms,
            )

    def scan_parallel(
        self,
        scan_func: Callable[[str], VisualizationGraph],
        progress_callback: Callable[[str, RegionScanResult], None] | None = None,
    ) -> MultiRegionGraph:
        """
        Scan multiple regions in parallel.

        Args:
            scan_func: Function that takes a region and returns a VisualizationGraph
            progress_callback: Optional callback for progress updates

        Returns:
            MultiRegionGraph with aggregated results
        """
        regions = self.config.regions or COMMON_REGIONS
        results: dict[str, RegionScanResult] = {}

        # Use tracked thread pool - global signal handler will shutdown on Ctrl-C
        executor = create_thread_pool(
            max_workers=self.config.max_parallel,
            thread_name_prefix="multi-region-",
        )
        try:
            # Submit all region scans
            future_to_region = {
                executor.submit(self._scan_region, region, scan_func): region
                for region in regions
            }

            # Collect results as they complete
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    result = future.result(timeout=self.config.region_timeout)
                    results[region] = result

                    if progress_callback:
                        progress_callback(region, result)

                    if result.success:
                        logger.info(
                            f"Scanned {region}: {result.resource_count} resources "
                            f"in {result.scan_time_ms:.0f}ms"
                        )
                    else:
                        logger.warning(f"Failed to scan {region}: {result.error}")

                except Exception as e:
                    results[region] = RegionScanResult(
                        region=region,
                        graph=None,
                        resource_count=0,
                        error=str(e),
                    )
        finally:
            executor.shutdown(wait=True)

        return self._aggregate_results(results)

    async def scan_parallel_async(
        self,
        scan_func: Callable[[str], VisualizationGraph],
        progress_callback: Callable[[str, RegionScanResult], None] | None = None,
    ) -> MultiRegionGraph:
        """
        Scan multiple regions in parallel using asyncio.

        Args:
            scan_func: Function that takes a region and returns a VisualizationGraph
            progress_callback: Optional callback for progress updates

        Returns:
            MultiRegionGraph with aggregated results
        """
        regions = self.config.regions or COMMON_REGIONS
        results: dict[str, RegionScanResult] = {}

        # Create semaphore to limit parallelism
        semaphore = asyncio.Semaphore(self.config.max_parallel)

        async def scan_with_semaphore(region: str) -> tuple[str, RegionScanResult]:
            async with semaphore:
                # Run sync scan in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, self._scan_region, region, scan_func
                )
                return region, result

        # Run all scans concurrently
        tasks = [scan_with_semaphore(region) for region in regions]
        for coro in asyncio.as_completed(tasks):
            region, result = await coro
            results[region] = result

            if progress_callback:
                progress_callback(region, result)

        return self._aggregate_results(results)

    def _aggregate_results(
        self,
        results: dict[str, RegionScanResult],
    ) -> MultiRegionGraph:
        """
        Aggregate scan results into a unified multi-region graph.

        Args:
            results: Dictionary of region -> scan result

        Returns:
            MultiRegionGraph with all resources aggregated
        """
        all_nodes: list[GraphNode] = []
        all_edges: list[GraphEdge] = []
        node_id_mapping: dict[str, str] = {}  # Original -> prefixed ID

        for region, result in results.items():
            if not result.success or not result.graph:
                continue

            if self.config.skip_empty and result.resource_count == 0:
                continue

            # Process nodes
            for node in result.graph.nodes:
                # Create new node with region attribution
                new_id = (
                    f"{region}:{node.id}" if self.config.prefix_node_ids else node.id
                )
                node_id_mapping[node.id] = new_id

                # Copy properties and add region
                new_properties = node.properties.copy()
                if self.config.add_region_attribute:
                    new_properties["region"] = region
                    new_properties["region_display"] = REGION_DISPLAY_NAMES.get(
                        region, region
                    )
                    group = REGION_GROUPS.get(region)
                    if group:
                        new_properties["region_group"] = str(group)

                # Determine color
                color = node.color
                if self.config.use_region_colors:
                    color = get_region_color(region)

                new_node = GraphNode(
                    id=new_id,
                    resource_type=node.resource_type,
                    name=node.name,
                    properties=new_properties,
                    icon=node.icon,
                    color=color,
                    group=f"{region}:{node.group}" if node.group else region,
                )
                all_nodes.append(new_node)

            # Process edges (update IDs if prefixing)
            for edge in result.graph.edges:
                new_source = node_id_mapping.get(edge.source, edge.source)
                new_target = node_id_mapping.get(edge.target, edge.target)

                new_edge = GraphEdge(
                    source=new_source,
                    target=new_target,
                    label=edge.label,
                    edge_type=edge.edge_type,
                )
                all_edges.append(new_edge)

        return MultiRegionGraph(
            nodes=all_nodes,
            edges=all_edges,
            region_results=results,
            metadata={
                "aggregated": True,
                "config": {
                    "prefix_node_ids": self.config.prefix_node_ids,
                    "add_region_attribute": self.config.add_region_attribute,
                    "use_region_colors": self.config.use_region_colors,
                },
            },
        )


def aggregate_regional_graphs(
    graphs: dict[str, VisualizationGraph],
    config: MultiRegionConfig | None = None,
) -> MultiRegionGraph:
    """
    Aggregate pre-scanned regional graphs into a single multi-region graph.

    This is useful when you already have VisualizationGraph objects for
    each region and just want to combine them.

    Args:
        graphs: Dictionary mapping region code to VisualizationGraph
        config: Optional multi-region configuration

    Returns:
        MultiRegionGraph with aggregated resources
    """
    config = config or MultiRegionConfig.default()

    # Create scan results from existing graphs
    results: dict[str, RegionScanResult] = {}
    for region, graph in graphs.items():
        results[region] = RegionScanResult(
            region=region,
            graph=graph,
            resource_count=len(graph.nodes),
        )

    # Use scanner's aggregation logic
    scanner = MultiRegionScanner(config)
    return scanner._aggregate_results(results)


def create_multi_region_scanner(
    regions: list[str] | None = None,
    max_parallel: int = 5,
) -> MultiRegionScanner:
    """
    Factory function to create a multi-region scanner.

    Args:
        regions: List of AWS regions to scan (default: common regions)
        max_parallel: Maximum number of parallel scans

    Returns:
        Configured MultiRegionScanner
    """
    config = MultiRegionConfig(
        regions=regions or COMMON_REGIONS.copy(),
        max_parallel=max_parallel,
    )
    return MultiRegionScanner(config)


def enrich_nodes_with_region(
    nodes: list[GraphNode],
    region: str,
) -> list[GraphNode]:
    """
    Add region information to a list of graph nodes.

    Args:
        nodes: List of GraphNode objects
        region: AWS region code

    Returns:
        List of nodes with region properties added
    """
    enriched: list[GraphNode] = []
    for node in nodes:
        new_properties = node.properties.copy()
        new_properties["region"] = region
        new_properties["region_display"] = REGION_DISPLAY_NAMES.get(region, region)

        group = REGION_GROUPS.get(region)
        if group:
            new_properties["region_group"] = str(group)

        enriched.append(
            GraphNode(
                id=node.id,
                resource_type=node.resource_type,
                name=node.name,
                properties=new_properties,
                icon=node.icon,
                color=get_region_color(region),
                group=node.group,
            )
        )

    return enriched


def get_regions_for_group(group: RegionGroup) -> list[str]:
    """Get all regions in a geographic group."""
    return [r for r, g in REGION_GROUPS.items() if g == group]


def detect_primary_region(graph: MultiRegionGraph) -> str | None:
    """
    Detect the primary region based on resource distribution.

    The primary region is the one with the most resources,
    which often serves as the main deployment region.

    Args:
        graph: Multi-region graph to analyze

    Returns:
        Region code of the primary region, or None if empty
    """
    if not graph.resources_by_region:
        return None

    return max(graph.resources_by_region, key=graph.resources_by_region.get)  # type: ignore[arg-type]


def calculate_region_distribution(
    graph: MultiRegionGraph,
) -> dict[str, dict[str, Any]]:
    """
    Calculate resource distribution across regions.

    Args:
        graph: Multi-region graph to analyze

    Returns:
        Dictionary with distribution statistics per region
    """
    total = graph.total_resources or 1  # Avoid division by zero
    distribution: dict[str, dict[str, Any]] = {}

    for region, count in graph.resources_by_region.items():
        percentage = (count / total) * 100
        group = REGION_GROUPS.get(region)

        distribution[region] = {
            "count": count,
            "percentage": round(percentage, 2),
            "display_name": REGION_DISPLAY_NAMES.get(region, region),
            "region_group": str(group) if group else None,
            "is_primary": count == max(graph.resources_by_region.values()),
        }

    return distribution
