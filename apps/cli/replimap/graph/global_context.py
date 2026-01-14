"""
Global Context for RepliMap.

Manages global (non-regional) AWS resources and provides:
- Global resource extraction (IAM, Route53, CloudFront, etc.)
- Super-node collapsing for simplified views
- Multi-view modes (simplified, detailed, security, cost, dr)

Global resources are account-level resources that exist outside
of specific regions or span multiple regions.
"""

from __future__ import annotations

import logging
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


class GlobalResourceType(str, Enum):
    """Types of global (non-regional) AWS resources."""

    # IAM Resources
    IAM_USER = "aws_iam_user"
    IAM_GROUP = "aws_iam_group"
    IAM_ROLE = "aws_iam_role"
    IAM_POLICY = "aws_iam_policy"
    IAM_INSTANCE_PROFILE = "aws_iam_instance_profile"
    IAM_SAML_PROVIDER = "aws_iam_saml_provider"
    IAM_OIDC_PROVIDER = "aws_iam_openid_connect_provider"

    # Route 53
    ROUTE53_ZONE = "aws_route53_zone"
    ROUTE53_RECORD = "aws_route53_record"
    ROUTE53_HEALTH_CHECK = "aws_route53_health_check"
    ROUTE53_DELEGATION_SET = "aws_route53_delegation_set"

    # CloudFront
    CLOUDFRONT_DISTRIBUTION = "aws_cloudfront_distribution"
    CLOUDFRONT_ORIGIN_ACCESS_IDENTITY = "aws_cloudfront_origin_access_identity"
    CLOUDFRONT_FUNCTION = "aws_cloudfront_function"
    CLOUDFRONT_CACHE_POLICY = "aws_cloudfront_cache_policy"

    # WAF (Global)
    WAF_WEB_ACL = "aws_waf_web_acl"
    WAF_RULE = "aws_waf_rule"
    WAF_RULE_GROUP = "aws_waf_rule_group"
    WAFV2_WEB_ACL = "aws_wafv2_web_acl"

    # Global Accelerator
    GLOBAL_ACCELERATOR = "aws_globalaccelerator_accelerator"
    GLOBAL_ACCELERATOR_LISTENER = "aws_globalaccelerator_listener"
    GLOBAL_ACCELERATOR_ENDPOINT_GROUP = "aws_globalaccelerator_endpoint_group"

    # S3 (buckets are global namespace)
    S3_BUCKET = "aws_s3_bucket"

    # Organizations
    ORGANIZATIONS_ACCOUNT = "aws_organizations_account"
    ORGANIZATIONS_OU = "aws_organizations_organizational_unit"
    ORGANIZATIONS_POLICY = "aws_organizations_policy"

    # ACM (Certificates - global for CloudFront)
    ACM_CERTIFICATE = "aws_acm_certificate"

    # Budgets
    BUDGET = "aws_budgets_budget"

    def __str__(self) -> str:
        return self.value


# Categories for global resources
class GlobalCategory(str, Enum):
    """Categories for global resources."""

    IDENTITY = "identity"  # IAM
    DNS = "dns"  # Route 53
    CDN = "cdn"  # CloudFront
    SECURITY = "security"  # WAF, Shield
    NETWORKING = "networking"  # Global Accelerator, Transit Gateway
    STORAGE = "storage"  # S3
    ORGANIZATION = "organization"  # Organizations
    CERTIFICATES = "certificates"  # ACM
    COST = "cost"  # Budgets

    def __str__(self) -> str:
        return self.value


# Map resource types to categories
RESOURCE_CATEGORY: dict[str, GlobalCategory] = {
    # IAM
    "aws_iam_user": GlobalCategory.IDENTITY,
    "aws_iam_group": GlobalCategory.IDENTITY,
    "aws_iam_role": GlobalCategory.IDENTITY,
    "aws_iam_policy": GlobalCategory.IDENTITY,
    "aws_iam_instance_profile": GlobalCategory.IDENTITY,
    "aws_iam_saml_provider": GlobalCategory.IDENTITY,
    "aws_iam_openid_connect_provider": GlobalCategory.IDENTITY,
    # Route 53
    "aws_route53_zone": GlobalCategory.DNS,
    "aws_route53_record": GlobalCategory.DNS,
    "aws_route53_health_check": GlobalCategory.DNS,
    "aws_route53_delegation_set": GlobalCategory.DNS,
    # CloudFront
    "aws_cloudfront_distribution": GlobalCategory.CDN,
    "aws_cloudfront_origin_access_identity": GlobalCategory.CDN,
    "aws_cloudfront_function": GlobalCategory.CDN,
    "aws_cloudfront_cache_policy": GlobalCategory.CDN,
    # WAF
    "aws_waf_web_acl": GlobalCategory.SECURITY,
    "aws_waf_rule": GlobalCategory.SECURITY,
    "aws_waf_rule_group": GlobalCategory.SECURITY,
    "aws_wafv2_web_acl": GlobalCategory.SECURITY,
    # Global Accelerator
    "aws_globalaccelerator_accelerator": GlobalCategory.NETWORKING,
    "aws_globalaccelerator_listener": GlobalCategory.NETWORKING,
    "aws_globalaccelerator_endpoint_group": GlobalCategory.NETWORKING,
    # S3
    "aws_s3_bucket": GlobalCategory.STORAGE,
    # Organizations
    "aws_organizations_account": GlobalCategory.ORGANIZATION,
    "aws_organizations_organizational_unit": GlobalCategory.ORGANIZATION,
    "aws_organizations_policy": GlobalCategory.ORGANIZATION,
    # ACM
    "aws_acm_certificate": GlobalCategory.CERTIFICATES,
    # Budgets
    "aws_budgets_budget": GlobalCategory.COST,
}


class ViewMode(str, Enum):
    """View modes for graph visualization."""

    SIMPLIFIED = "simplified"  # Collapsed super-nodes, minimal detail
    DETAILED = "detailed"  # All resources expanded
    SECURITY = "security"  # Focus on security-related resources
    COST = "cost"  # Focus on cost-bearing resources
    DR = "dr"  # Disaster recovery view
    NETWORK = "network"  # Network topology focus
    IDENTITY = "identity"  # IAM and access focus

    def __str__(self) -> str:
        return self.value


# Category colors for visualization
CATEGORY_COLORS: dict[GlobalCategory, str] = {
    GlobalCategory.IDENTITY: "#f59e0b",  # Amber
    GlobalCategory.DNS: "#10b981",  # Green
    GlobalCategory.CDN: "#3b82f6",  # Blue
    GlobalCategory.SECURITY: "#ef4444",  # Red
    GlobalCategory.NETWORKING: "#8b5cf6",  # Purple
    GlobalCategory.STORAGE: "#06b6d4",  # Cyan
    GlobalCategory.ORGANIZATION: "#6366f1",  # Indigo
    GlobalCategory.CERTIFICATES: "#84cc16",  # Lime
    GlobalCategory.COST: "#f97316",  # Orange
}

# Category icons
CATEGORY_ICONS: dict[GlobalCategory, str] = {
    GlobalCategory.IDENTITY: "👤",
    GlobalCategory.DNS: "🌐",
    GlobalCategory.CDN: "⚡",
    GlobalCategory.SECURITY: "🔒",
    GlobalCategory.NETWORKING: "🔀",
    GlobalCategory.STORAGE: "📦",
    GlobalCategory.ORGANIZATION: "🏢",
    GlobalCategory.CERTIFICATES: "📜",
    GlobalCategory.COST: "💰",
}


@dataclass
class SuperNode:
    """
    A collapsed super-node representing multiple related resources.

    Super-nodes are used in simplified views to reduce visual complexity
    by grouping related resources together.
    """

    id: str
    name: str
    category: GlobalCategory
    resource_count: int
    resource_types: set[str] = field(default_factory=set)
    child_ids: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)

    @property
    def color(self) -> str:
        """Get color for this super-node."""
        return CATEGORY_COLORS.get(self.category, "#6b7280")

    @property
    def icon(self) -> str:
        """Get icon for this super-node."""
        return CATEGORY_ICONS.get(self.category, "📁")

    def to_graph_node(self) -> GraphNode:
        """Convert to a GraphNode for visualization."""
        return GraphNode(
            id=self.id,
            resource_type=f"super_{self.category.value}",
            name=self.name,
            properties={
                "category": self.category.value,
                "resource_count": self.resource_count,
                "resource_types": list(self.resource_types),
                "child_ids": self.child_ids,
                "is_super_node": True,
                **self.properties,
            },
            icon=self.icon,
            color=self.color,
            group="global",
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category.value,
            "resource_count": self.resource_count,
            "resource_types": list(self.resource_types),
            "child_ids": self.child_ids,
            "color": self.color,
            "icon": self.icon,
        }


@dataclass
class GlobalContext:
    """
    Context containing global (non-regional) AWS resources.

    Provides:
    - Extraction of global resources from a full graph
    - Super-node collapsing for simplified views
    - Multi-view mode support
    - Category-based organization
    """

    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    super_nodes: dict[GlobalCategory, SuperNode] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_resources(self) -> int:
        """Total number of global resources."""
        return len(self.nodes)

    @property
    def resources_by_category(self) -> dict[GlobalCategory, int]:
        """Count of resources per category."""
        counts: dict[GlobalCategory, int] = {}
        for node in self.nodes:
            category = RESOURCE_CATEGORY.get(node.resource_type)
            if category:
                counts[category] = counts.get(category, 0) + 1
        return counts

    @property
    def resources_by_type(self) -> dict[str, int]:
        """Count of resources by type."""
        counts: dict[str, int] = {}
        for node in self.nodes:
            counts[node.resource_type] = counts.get(node.resource_type, 0) + 1
        return counts

    def get_nodes_by_category(self, category: GlobalCategory) -> list[GraphNode]:
        """Get all nodes in a specific category."""
        return [
            node
            for node in self.nodes
            if RESOURCE_CATEGORY.get(node.resource_type) == category
        ]

    def get_iam_roles(self) -> list[GraphNode]:
        """Get all IAM roles."""
        return [n for n in self.nodes if n.resource_type == "aws_iam_role"]

    def get_route53_zones(self) -> list[GraphNode]:
        """Get all Route 53 hosted zones."""
        return [n for n in self.nodes if n.resource_type == "aws_route53_zone"]

    def get_cloudfront_distributions(self) -> list[GraphNode]:
        """Get all CloudFront distributions."""
        return [
            n for n in self.nodes if n.resource_type == "aws_cloudfront_distribution"
        ]

    def to_visualization_graph(
        self,
        view_mode: ViewMode = ViewMode.SIMPLIFIED,
    ) -> VisualizationGraph:
        """
        Convert to a VisualizationGraph for the specified view mode.

        Args:
            view_mode: The view mode to use

        Returns:
            VisualizationGraph suitable for visualization
        """
        if view_mode == ViewMode.SIMPLIFIED:
            return self._to_simplified_graph()
        elif view_mode == ViewMode.SECURITY:
            return self._to_security_graph()
        elif view_mode == ViewMode.IDENTITY:
            return self._to_identity_graph()
        else:
            return self._to_detailed_graph()

    def _to_simplified_graph(self) -> VisualizationGraph:
        """Create simplified graph with super-nodes."""
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []

        # Add super-nodes for each category
        for _category, super_node in self.super_nodes.items():
            nodes.append(super_node.to_graph_node())

        # Add edges between super-nodes (aggregated from child edges)
        category_edges: set[tuple[GlobalCategory, GlobalCategory]] = set()
        node_categories = {
            node.id: RESOURCE_CATEGORY.get(node.resource_type) for node in self.nodes
        }

        for edge in self.edges:
            source_cat = node_categories.get(edge.source)
            target_cat = node_categories.get(edge.target)
            if source_cat and target_cat and source_cat != target_cat:
                category_edges.add((source_cat, target_cat))

        for source_cat, target_cat in category_edges:
            edges.append(
                GraphEdge(
                    source=f"global_{source_cat.value}",
                    target=f"global_{target_cat.value}",
                    label="references",
                    edge_type="reference",
                )
            )

        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "view_mode": "simplified",
                "is_global": True,
                "super_nodes": True,
            },
        )

    def _to_detailed_graph(self) -> VisualizationGraph:
        """Create detailed graph with all resources."""
        return VisualizationGraph(
            nodes=self.nodes.copy(),
            edges=self.edges.copy(),
            metadata={
                "view_mode": "detailed",
                "is_global": True,
            },
        )

    def _to_security_graph(self) -> VisualizationGraph:
        """Create graph focused on security resources."""
        security_categories = {
            GlobalCategory.SECURITY,
            GlobalCategory.IDENTITY,
            GlobalCategory.CERTIFICATES,
        }

        nodes = [
            node
            for node in self.nodes
            if RESOURCE_CATEGORY.get(node.resource_type) in security_categories
        ]
        node_ids = {node.id for node in nodes}

        edges = [
            edge
            for edge in self.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "view_mode": "security",
                "is_global": True,
            },
        )

    def _to_identity_graph(self) -> VisualizationGraph:
        """Create graph focused on identity resources."""
        nodes = self.get_nodes_by_category(GlobalCategory.IDENTITY)
        node_ids = {node.id for node in nodes}

        edges = [
            edge
            for edge in self.edges
            if edge.source in node_ids and edge.target in node_ids
        ]

        return VisualizationGraph(
            nodes=nodes,
            edges=edges,
            metadata={
                "view_mode": "identity",
                "is_global": True,
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
                }
                for n in self.nodes
            ],
            "edges": [
                {
                    "source": e.source,
                    "target": e.target,
                    "label": e.label,
                }
                for e in self.edges
            ],
            "super_nodes": {
                cat.value: sn.to_dict() for cat, sn in self.super_nodes.items()
            },
            "summary": {
                "total_resources": self.total_resources,
                "by_category": {
                    cat.value: count
                    for cat, count in self.resources_by_category.items()
                },
                "by_type": self.resources_by_type,
            },
        }


@dataclass
class GlobalContextConfig:
    """Configuration for global context extraction."""

    # Include IAM resources
    include_iam: bool = True

    # Include Route 53 resources
    include_route53: bool = True

    # Include CloudFront resources
    include_cloudfront: bool = True

    # Include WAF resources
    include_waf: bool = True

    # Include S3 buckets (global namespace)
    include_s3: bool = True

    # Include Organizations resources
    include_organizations: bool = False

    # Create super-nodes for simplified view
    create_super_nodes: bool = True

    # Minimum resources per category to create super-node
    super_node_threshold: int = 3

    # Categories to exclude
    exclude_categories: set[GlobalCategory] = field(default_factory=set)

    @classmethod
    def default(cls) -> GlobalContextConfig:
        """Create default configuration."""
        return cls()

    @classmethod
    def iam_only(cls) -> GlobalContextConfig:
        """Create configuration for IAM resources only."""
        return cls(
            include_iam=True,
            include_route53=False,
            include_cloudfront=False,
            include_waf=False,
            include_s3=False,
        )

    @classmethod
    def networking_only(cls) -> GlobalContextConfig:
        """Create configuration for networking resources only."""
        return cls(
            include_iam=False,
            include_route53=True,
            include_cloudfront=True,
            include_waf=False,
            include_s3=False,
        )


class GlobalContextExtractor:
    """
    Extracts global resources from a full infrastructure graph.

    Separates global (non-regional) resources and organizes them
    by category with optional super-node collapsing.
    """

    # Set of global resource types
    GLOBAL_TYPES: set[str] = {rt.value for rt in GlobalResourceType}

    def __init__(self, config: GlobalContextConfig | None = None) -> None:
        """
        Initialize the extractor.

        Args:
            config: Configuration for extraction
        """
        self.config = config or GlobalContextConfig.default()

    def extract(self, graph: VisualizationGraph) -> GlobalContext:
        """
        Extract global resources from a visualization graph.

        Args:
            graph: Full infrastructure graph

        Returns:
            GlobalContext with extracted global resources
        """
        # Filter global nodes
        global_nodes: list[GraphNode] = []
        for node in graph.nodes:
            if self._is_global_resource(node):
                # Add category to properties
                category = RESOURCE_CATEGORY.get(node.resource_type)
                if category:
                    new_props = node.properties.copy()
                    new_props["global_category"] = category.value
                    new_props["is_global"] = True

                    global_nodes.append(
                        GraphNode(
                            id=node.id,
                            resource_type=node.resource_type,
                            name=node.name,
                            properties=new_props,
                            icon=node.icon,
                            color=CATEGORY_COLORS.get(category, node.color),
                            group="global",
                        )
                    )

        # Get node IDs for edge filtering
        global_node_ids = {node.id for node in global_nodes}

        # Filter edges that connect global resources
        global_edges: list[GraphEdge] = []
        for edge in graph.edges:
            if edge.source in global_node_ids or edge.target in global_node_ids:
                global_edges.append(edge)

        # Create super-nodes if configured
        super_nodes: dict[GlobalCategory, SuperNode] = {}
        if self.config.create_super_nodes:
            super_nodes = self._create_super_nodes(global_nodes)

        return GlobalContext(
            nodes=global_nodes,
            edges=global_edges,
            super_nodes=super_nodes,
            metadata={
                "extracted_from": graph.metadata.get("source", "unknown"),
                "config": {
                    "include_iam": self.config.include_iam,
                    "include_route53": self.config.include_route53,
                    "include_cloudfront": self.config.include_cloudfront,
                    "include_waf": self.config.include_waf,
                    "include_s3": self.config.include_s3,
                },
            },
        )

    def _is_global_resource(self, node: GraphNode) -> bool:
        """Check if a node represents a global resource."""
        resource_type = node.resource_type

        # Check if it's a known global type
        if resource_type not in self.GLOBAL_TYPES:
            return False

        # Check category exclusions
        category = RESOURCE_CATEGORY.get(resource_type)
        if category and category in self.config.exclude_categories:
            return False

        # Check config-based inclusions
        if resource_type.startswith("aws_iam_") and not self.config.include_iam:
            return False
        if resource_type.startswith("aws_route53_") and not self.config.include_route53:
            return False
        if (
            resource_type.startswith("aws_cloudfront_")
            and not self.config.include_cloudfront
        ):
            return False
        if resource_type.startswith("aws_waf") and not self.config.include_waf:
            return False
        if resource_type == "aws_s3_bucket" and not self.config.include_s3:
            return False
        if (
            resource_type.startswith("aws_organizations_")
            and not self.config.include_organizations
        ):
            return False

        return True

    def _create_super_nodes(
        self,
        nodes: list[GraphNode],
    ) -> dict[GlobalCategory, SuperNode]:
        """Create super-nodes by category."""
        super_nodes: dict[GlobalCategory, SuperNode] = {}

        # Group nodes by category
        by_category: dict[GlobalCategory, list[GraphNode]] = {}
        for node in nodes:
            category = RESOURCE_CATEGORY.get(node.resource_type)
            if category:
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(node)

        # Create super-node for each category meeting threshold
        for category, cat_nodes in by_category.items():
            if len(cat_nodes) >= self.config.super_node_threshold:
                resource_types = {n.resource_type for n in cat_nodes}
                child_ids = [n.id for n in cat_nodes]

                super_nodes[category] = SuperNode(
                    id=f"global_{category.value}",
                    name=f"{category.value.title()} ({len(cat_nodes)})",
                    category=category,
                    resource_count=len(cat_nodes),
                    resource_types=resource_types,
                    child_ids=child_ids,
                )

        return super_nodes


def extract_global_context(
    graph: VisualizationGraph,
    config: GlobalContextConfig | None = None,
) -> GlobalContext:
    """
    Extract global context from a visualization graph.

    Args:
        graph: Full infrastructure graph
        config: Optional extraction configuration

    Returns:
        GlobalContext with global resources
    """
    extractor = GlobalContextExtractor(config)
    return extractor.extract(graph)


def merge_global_context(
    regional_graph: VisualizationGraph,
    global_context: GlobalContext,
    view_mode: ViewMode = ViewMode.DETAILED,
) -> VisualizationGraph:
    """
    Merge a regional graph with global context.

    Args:
        regional_graph: Graph with regional resources
        global_context: Global context to merge
        view_mode: View mode for global resources

    Returns:
        Combined VisualizationGraph
    """
    global_graph = global_context.to_visualization_graph(view_mode)

    # Combine nodes and edges
    all_nodes = regional_graph.nodes + global_graph.nodes
    all_edges = regional_graph.edges + global_graph.edges

    # Merge metadata
    metadata = {
        **regional_graph.metadata,
        "has_global_context": True,
        "global_view_mode": view_mode.value,
    }

    return VisualizationGraph(
        nodes=all_nodes,
        edges=all_edges,
        metadata=metadata,
    )


def get_iam_role_usage(
    global_context: GlobalContext,
    regional_graph: VisualizationGraph,
) -> dict[str, list[str]]:
    """
    Analyze IAM role usage across regional resources.

    Args:
        global_context: Global context with IAM roles
        regional_graph: Regional graph with resources using roles

    Returns:
        Dictionary mapping role IDs to list of resource IDs using them
    """
    role_usage: dict[str, list[str]] = {}
    role_ids = {n.id for n in global_context.get_iam_roles()}

    for edge in regional_graph.edges:
        if edge.target in role_ids:
            if edge.target not in role_usage:
                role_usage[edge.target] = []
            role_usage[edge.target].append(edge.source)
        elif edge.source in role_ids:
            if edge.source not in role_usage:
                role_usage[edge.source] = []
            role_usage[edge.source].append(edge.target)

    return role_usage


def find_unused_global_resources(
    global_context: GlobalContext,
    regional_graph: VisualizationGraph,
) -> list[GraphNode]:
    """
    Find global resources not referenced by any regional resource.

    Args:
        global_context: Global context to analyze
        regional_graph: Regional graph to check references

    Returns:
        List of unused global resources
    """
    global_ids = {n.id for n in global_context.nodes}

    # Find all global IDs referenced in regional edges
    referenced: set[str] = set()
    for edge in regional_graph.edges:
        if edge.source in global_ids:
            referenced.add(edge.source)
        if edge.target in global_ids:
            referenced.add(edge.target)

    # Also check edges within global context
    for edge in global_context.edges:
        if edge.source not in global_ids:
            referenced.add(edge.target)
        if edge.target not in global_ids:
            referenced.add(edge.source)

    # Return unreferenced nodes
    return [n for n in global_context.nodes if n.id not in referenced]


def categorize_node(node: GraphNode) -> GlobalCategory | None:
    """Get the global category for a node, if any."""
    return RESOURCE_CATEGORY.get(node.resource_type)


def is_global_resource(resource_type: str) -> bool:
    """Check if a resource type is global (non-regional)."""
    return resource_type in GlobalContextExtractor.GLOBAL_TYPES
