"""
Smart aggregation for infrastructure graphs.

Instead of "117 security groups" as one node, aggregate by:
- VPC (most useful context)
- Service/Application (from tags)
- Subnet (for resources like EC2)

This provides meaningful groupings that preserve context while
reducing visual complexity.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from replimap.graph.naming import get_type_plural_name


@dataclass
class AggregatedNode:
    """
    A node that represents multiple resources.

    Represents a group of similar resources within a scope,
    such as "45 security groups in prod VPC".
    """

    id: str
    type: str
    name: str
    icon: str
    color: str
    group: str
    count: int
    is_group: bool = True
    scope_id: str | None = None  # VPC ID, Subnet ID, etc.
    scope_name: str | None = None  # Human-readable scope
    scope_type: str | None = None  # 'vpc', 'subnet', 'global'
    member_ids: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    expandable: bool = True
    environment: str = "unknown"
    env_color: str = "#6b7280"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "icon": self.icon,
            "color": self.color,
            "group": self.group,
            "count": self.count,
            "is_group": self.is_group,
            "scope_id": self.scope_id,
            "scope_name": self.scope_name,
            "scope_type": self.scope_type,
            "member_ids": self.member_ids[:10],  # Limit for JSON size
            "properties": self.properties,
            "expandable": self.expandable,
            "environment": self.environment,
            "env_color": self.env_color,
        }


@dataclass
class AggregationConfig:
    """Configuration for smart aggregation."""

    # Thresholds for aggregation
    min_group_size: int = 3  # Don't aggregate fewer than this
    max_visible_per_type: int = 8  # Show at most this many individual nodes per type

    # Important resources to never aggregate (entry points, databases, etc.)
    never_aggregate: set[str] = field(
        default_factory=lambda: {
            "aws_vpc",
            "aws_subnet",
            "aws_lb",  # ALBs are important entry points
            "aws_db_instance",  # Databases are critical
            "aws_nat_gateway",  # Network infrastructure
            "aws_internet_gateway",
            "aws_elasticache_cluster",  # Cache clusters
        }
    )

    # Always aggregate these (usually many and noisy)
    always_aggregate: set[str] = field(
        default_factory=lambda: {
            "aws_security_group",
            "aws_security_group_rule",
            "aws_sqs_queue",
            "aws_sns_topic",
            "aws_s3_bucket_policy",
            "aws_ebs_volume",
            "aws_lb_target_group",
            "aws_lb_listener",
            "aws_route",
            "aws_route_table_association",
            "aws_iam_role_policy_attachment",
            "aws_iam_policy",
        }
    )

    # Tag keys to use for sub-grouping within VPC
    service_tags: list[str] = field(
        default_factory=lambda: ["Service", "Application", "Component", "Name"]
    )

    environment_tags: list[str] = field(
        default_factory=lambda: ["Environment", "Env", "Stage"]
    )


class SmartAggregator:
    """
    Aggregates resources intelligently based on context.

    Strategy:
    1. Group by resource type
    2. Within type, group by VPC
    3. Keep important individual resources visible
    4. Preserve environment context in aggregated nodes
    """

    def __init__(self, config: AggregationConfig | None = None) -> None:
        """Initialize the aggregator."""
        self.config = config or AggregationConfig()

    def aggregate(
        self,
        nodes: list[dict[str, Any]],
        links: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Aggregate nodes intelligently.

        Args:
            nodes: List of node dictionaries
            links: List of link dictionaries

        Returns:
            Tuple of (aggregated_nodes, updated_links)
        """
        # Build VPC map for quick lookup
        vpc_map = self._build_vpc_map(nodes)

        # Group nodes by type
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for node in nodes:
            by_type[node.get("type", "unknown")].append(node)

        result_nodes: list[dict[str, Any]] = []
        id_mapping: dict[str, str] = {}  # old_id -> new_id

        for resource_type, type_nodes in by_type.items():
            if resource_type in self.config.never_aggregate:
                # Keep individual nodes
                result_nodes.extend(type_nodes)
                for n in type_nodes:
                    id_mapping[n["id"]] = n["id"]
            elif (
                resource_type in self.config.always_aggregate
                or len(type_nodes) > self.config.max_visible_per_type
            ):
                # Aggregate by VPC
                aggregated = self._aggregate_by_vpc(type_nodes, vpc_map)
                result_nodes.extend(aggregated)
                # Map individual IDs to aggregated nodes
                for n in type_nodes:
                    vpc_id = vpc_map.get(n["id"])
                    agg_id = self._get_aggregation_id(resource_type, vpc_id)
                    id_mapping[n["id"]] = agg_id
            else:
                # Keep individual nodes
                result_nodes.extend(type_nodes)
                for n in type_nodes:
                    id_mapping[n["id"]] = n["id"]

        # Update links
        updated_links = self._update_links(links, id_mapping)

        return result_nodes, updated_links

    def _build_vpc_map(self, nodes: list[dict[str, Any]]) -> dict[str, str]:
        """Build mapping from resource ID to VPC ID."""
        vpc_map: dict[str, str] = {}

        for node in nodes:
            resource_id = node["id"]
            props = node.get("properties", {})

            # Direct vpc_id property
            vpc_id = props.get("vpc_id")
            if vpc_id:
                vpc_map[resource_id] = vpc_id

            # If this is a VPC, map it to itself
            if node.get("type") == "aws_vpc":
                vpc_map[resource_id] = resource_id

        return vpc_map

    def _aggregate_by_vpc(
        self,
        nodes: list[dict[str, Any]],
        vpc_map: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Aggregate nodes by their VPC."""
        by_vpc: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for node in nodes:
            vpc_id = vpc_map.get(node["id"])
            if not vpc_id:
                vpc_id = node.get("properties", {}).get("vpc_id")
            if not vpc_id:
                vpc_id = "global"  # Resources not in a VPC

            by_vpc[vpc_id].append(node)

        aggregated: list[dict[str, Any]] = []

        for vpc_id, vpc_nodes in by_vpc.items():
            if len(vpc_nodes) < self.config.min_group_size:
                # Too few to aggregate, keep individual
                aggregated.extend(vpc_nodes)
            else:
                # Create aggregated node
                agg_node = self._create_aggregated_node(vpc_nodes, vpc_id)
                aggregated.append(agg_node)

        return aggregated

    def _create_aggregated_node(
        self,
        nodes: list[dict[str, Any]],
        vpc_id: str,
    ) -> dict[str, Any]:
        """Create an aggregated node from a list of nodes."""
        sample = nodes[0]
        resource_type = sample.get("type", "unknown")
        vpc_name = self._get_vpc_name(vpc_id, nodes)
        count = len(nodes)

        # Determine dominant environment
        env_counts: dict[str, int] = defaultdict(int)
        for n in nodes:
            env = n.get("environment", "unknown")
            env_counts[env] += 1

        dominant_env = max(env_counts.items(), key=lambda x: x[1])[0]
        env_colors = {
            "prod": "#ef4444",
            "stage": "#f59e0b",
            "test": "#22c55e",
            "dev": "#3b82f6",
            "unknown": "#6b7280",
        }

        # Create label
        type_plural = get_type_plural_name(resource_type, count)
        if vpc_id == "global":
            name = f"{count} {type_plural}"
        else:
            name = f"{count} {type_plural}"

        return {
            "id": self._get_aggregation_id(resource_type, vpc_id),
            "type": resource_type,
            "name": name,
            "icon": f"[{count}]",
            "color": self._lighten_color(sample.get("color", "#6b7280")),
            "group": sample.get("group", "other"),
            "is_group": True,
            "count": count,
            "scope_id": vpc_id if vpc_id != "global" else None,
            "scope_name": vpc_name,
            "scope_type": "vpc" if vpc_id != "global" else "global",
            "member_ids": [n["id"] for n in nodes[:10]],  # First 10 for preview
            "expandable": True,
            "environment": dominant_env,
            "env_color": env_colors.get(dominant_env, "#6b7280"),
            "properties": {
                "count": count,
                "is_group": True,
                "scope_id": vpc_id if vpc_id != "global" else None,
                "scope_name": vpc_name,
                "ids": [n["id"] for n in nodes[:5]],
                "unique_tags": self._get_unique_tags(nodes),
                "environments": dict(env_counts),
                "vpc_id": vpc_id if vpc_id != "global" else None,
            },
        }

    def _get_aggregation_id(
        self,
        resource_type: str,
        scope_id: str | None,
    ) -> str:
        """Generate consistent ID for aggregated nodes."""
        type_short = resource_type.replace("aws_", "")
        scope_safe = (scope_id or "global").replace("-", "_").replace(":", "_")
        return f"group_{type_short}_{scope_safe}"

    def _get_vpc_name(
        self,
        vpc_id: str,
        nodes: list[dict[str, Any]],
    ) -> str:
        """Extract VPC name from nodes or ID."""
        if vpc_id == "global":
            return "Global"

        # Try to find VPC name from node properties
        for node in nodes:
            vpc_name = node.get("properties", {}).get("vpc_name")
            if vpc_name:
                return vpc_name

        # Try to extract from ID patterns
        vpc_lower = vpc_id.lower()
        if "prod" in vpc_lower:
            return "prod VPC"
        if "public" in vpc_lower:
            return "public VPC"
        if "private" in vpc_lower:
            return "private VPC"
        if "staging" in vpc_lower or "stage" in vpc_lower:
            return "stage VPC"
        if "test" in vpc_lower:
            return "test VPC"
        if "dev" in vpc_lower:
            return "dev VPC"

        # Return last part of ID
        if vpc_id.startswith("vpc-"):
            return f"VPC ...{vpc_id[-6:]}"

        return vpc_id

    def _get_unique_tags(self, nodes: list[dict[str, Any]]) -> list[str]:
        """Get unique tag keys across all nodes."""
        all_tags: set[str] = set()

        for node in nodes:
            tags = node.get("properties", {}).get("tags", {})
            if isinstance(tags, dict):
                all_tags.update(tags.keys())

        return sorted(all_tags)[:10]  # Limit to 10

    def _lighten_color(self, hex_color: str) -> str:
        """Lighten a hex color for group display (add transparency)."""
        if hex_color.startswith("#") and len(hex_color) == 7:
            return hex_color + "80"  # 50% opacity
        return hex_color

    def _update_links(
        self,
        links: list[dict[str, Any]],
        id_mapping: dict[str, str],
    ) -> list[dict[str, Any]]:
        """Update links to point to aggregated nodes."""
        updated: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        for link in links:
            source = link.get("source", "")
            target = link.get("target", "")

            # Handle D3 format where source/target may be objects
            if isinstance(source, dict):
                source = source.get("id", "")
            if isinstance(target, dict):
                target = target.get("id", "")

            # Map to new IDs
            new_source = id_mapping.get(source, source)
            new_target = id_mapping.get(target, target)

            # Skip self-links
            if new_source == new_target:
                continue

            # Deduplicate
            link_key = (new_source, new_target)
            if link_key in seen:
                continue
            seen.add(link_key)

            updated.append(
                {
                    **link,
                    "source": new_source,
                    "target": new_target,
                }
            )

        return updated

    def get_aggregation_summary(
        self,
        original_nodes: list[dict[str, Any]],
        aggregated_nodes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Get summary of aggregation results."""
        original_count = len(original_nodes)
        aggregated_count = len(aggregated_nodes)
        reduction = original_count - aggregated_count

        groups = [n for n in aggregated_nodes if n.get("is_group")]
        individual = [n for n in aggregated_nodes if not n.get("is_group")]

        grouped_count = sum(n.get("count", 1) for n in groups)

        return {
            "original_count": original_count,
            "after_aggregation": aggregated_count,
            "reduction": reduction,
            "reduction_percent": (
                round(reduction / original_count * 100, 1) if original_count > 0 else 0
            ),
            "group_count": len(groups),
            "individual_count": len(individual),
            "resources_in_groups": grouped_count,
            "groups": [
                {
                    "id": g["id"],
                    "type": g["type"],
                    "count": g.get("count", 1),
                    "scope_name": g.get("scope_name"),
                }
                for g in groups
            ],
        }


def create_aggregator(
    min_group_size: int = 3,
    max_visible_per_type: int = 8,
) -> SmartAggregator:
    """
    Factory function to create a configured aggregator.

    Args:
        min_group_size: Minimum number of resources to form a group
        max_visible_per_type: Maximum individual resources to show per type

    Returns:
        Configured SmartAggregator instance
    """
    config = AggregationConfig(
        min_group_size=min_group_size,
        max_visible_per_type=max_visible_per_type,
    )
    return SmartAggregator(config)
