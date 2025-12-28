"""
Cross-Region Dependency Detection for RepliMap.

Detects and analyzes cross-region relationships between AWS resources:
- RDS Read Replicas
- Aurora Global Databases
- S3 Cross-Region Replication
- DynamoDB Global Tables
- Transit Gateway Peering
- Route 53 Failover
- Global Accelerator

This module identifies resources that span multiple regions
and creates edges to represent these cross-region dependencies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

from replimap.graph.visualizer import GraphEdge, GraphNode, VisualizationGraph

if TYPE_CHECKING:
    from replimap.graph.multi_region import MultiRegionGraph

logger = logging.getLogger(__name__)


class CrossRegionType(str, Enum):
    """Types of cross-region relationships."""

    # Database
    RDS_READ_REPLICA = "rds_read_replica"
    AURORA_GLOBAL = "aurora_global"
    DYNAMODB_GLOBAL_TABLE = "dynamodb_global_table"
    ELASTICACHE_GLOBAL = "elasticache_global"
    DOCUMENTDB_GLOBAL = "documentdb_global"

    # Storage
    S3_REPLICATION = "s3_replication"
    EFS_REPLICATION = "efs_replication"

    # Networking
    TRANSIT_GATEWAY_PEERING = "transit_gateway_peering"
    VPC_PEERING = "vpc_peering"

    # DNS & Traffic
    ROUTE53_FAILOVER = "route53_failover"
    ROUTE53_LATENCY = "route53_latency"
    ROUTE53_GEOLOCATION = "route53_geolocation"
    GLOBAL_ACCELERATOR = "global_accelerator"

    # CDN
    CLOUDFRONT_ORIGIN = "cloudfront_origin"

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable name."""
        names = {
            CrossRegionType.RDS_READ_REPLICA: "RDS Read Replica",
            CrossRegionType.AURORA_GLOBAL: "Aurora Global Database",
            CrossRegionType.DYNAMODB_GLOBAL_TABLE: "DynamoDB Global Table",
            CrossRegionType.ELASTICACHE_GLOBAL: "ElastiCache Global Datastore",
            CrossRegionType.DOCUMENTDB_GLOBAL: "DocumentDB Global Cluster",
            CrossRegionType.S3_REPLICATION: "S3 Cross-Region Replication",
            CrossRegionType.EFS_REPLICATION: "EFS Replication",
            CrossRegionType.TRANSIT_GATEWAY_PEERING: "Transit Gateway Peering",
            CrossRegionType.VPC_PEERING: "VPC Peering",
            CrossRegionType.ROUTE53_FAILOVER: "Route 53 Failover",
            CrossRegionType.ROUTE53_LATENCY: "Route 53 Latency-Based",
            CrossRegionType.ROUTE53_GEOLOCATION: "Route 53 Geolocation",
            CrossRegionType.GLOBAL_ACCELERATOR: "Global Accelerator",
            CrossRegionType.CLOUDFRONT_ORIGIN: "CloudFront Origin",
        }
        return names.get(self, self.value)

    @property
    def is_synchronous(self) -> bool:
        """Check if this replication type is synchronous."""
        async_types = {
            CrossRegionType.RDS_READ_REPLICA,
            CrossRegionType.S3_REPLICATION,
            CrossRegionType.DYNAMODB_GLOBAL_TABLE,
        }
        return self not in async_types


class ReplicationDirection(str, Enum):
    """Direction of replication."""

    PRIMARY_TO_SECONDARY = "primary_to_secondary"
    SECONDARY_TO_PRIMARY = "secondary_to_primary"
    BIDIRECTIONAL = "bidirectional"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


@dataclass
class CrossRegionDependency:
    """
    Represents a cross-region dependency between two resources.

    This captures the relationship between resources in different
    regions, including the type of replication, direction, and
    any relevant configuration details.
    """

    source_id: str
    source_region: str
    source_type: str
    target_id: str
    target_region: str
    target_type: str
    dependency_type: CrossRegionType
    direction: ReplicationDirection = ReplicationDirection.PRIMARY_TO_SECONDARY
    is_active: bool = True
    replication_lag_seconds: float | None = None
    configuration: dict[str, Any] = field(default_factory=dict)

    @property
    def is_same_type(self) -> bool:
        """Check if source and target are the same resource type."""
        return self.source_type == self.target_type

    @property
    def regions(self) -> tuple[str, str]:
        """Get the pair of regions involved."""
        return (self.source_region, self.target_region)

    def to_graph_edge(self) -> GraphEdge:
        """Convert to a GraphEdge for visualization."""
        return GraphEdge(
            source=self.source_id,
            target=self.target_id,
            label=self.dependency_type.display_name,
            edge_type="cross_region",
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "source_id": self.source_id,
            "source_region": self.source_region,
            "source_type": self.source_type,
            "target_id": self.target_id,
            "target_region": self.target_region,
            "target_type": self.target_type,
            "dependency_type": self.dependency_type.value,
            "dependency_type_display": self.dependency_type.display_name,
            "direction": self.direction.value,
            "is_active": self.is_active,
            "replication_lag_seconds": self.replication_lag_seconds,
            "is_synchronous": self.dependency_type.is_synchronous,
            "configuration": self.configuration,
        }


@dataclass
class CrossRegionAnalysis:
    """
    Complete analysis of cross-region dependencies.

    Contains all detected cross-region relationships and
    summary statistics.
    """

    dependencies: list[CrossRegionDependency] = field(default_factory=list)
    by_type: dict[CrossRegionType, list[CrossRegionDependency]] = field(
        default_factory=dict
    )
    region_pairs: dict[tuple[str, str], list[CrossRegionDependency]] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_dependencies(self) -> int:
        """Total number of cross-region dependencies."""
        return len(self.dependencies)

    @property
    def unique_regions(self) -> set[str]:
        """Set of all regions involved in cross-region dependencies."""
        regions: set[str] = set()
        for dep in self.dependencies:
            regions.add(dep.source_region)
            regions.add(dep.target_region)
        return regions

    @property
    def unique_region_pairs(self) -> set[tuple[str, str]]:
        """Set of unique region pairs."""
        return set(self.region_pairs.keys())

    def get_dependencies_for_region(
        self,
        region: str,
    ) -> list[CrossRegionDependency]:
        """Get all dependencies involving a specific region."""
        return [
            dep for dep in self.dependencies
            if dep.source_region == region or dep.target_region == region
        ]

    def get_dependencies_by_type(
        self,
        dep_type: CrossRegionType,
    ) -> list[CrossRegionDependency]:
        """Get all dependencies of a specific type."""
        return self.by_type.get(dep_type, [])

    def get_primary_secondary_pairs(self) -> dict[str, str]:
        """Get mapping of primary resource IDs to secondary resource IDs."""
        pairs: dict[str, str] = {}
        for dep in self.dependencies:
            if dep.direction == ReplicationDirection.PRIMARY_TO_SECONDARY:
                pairs[dep.source_id] = dep.target_id
        return pairs

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_dependencies": self.total_dependencies,
            "unique_regions": list(self.unique_regions),
            "dependencies": [d.to_dict() for d in self.dependencies],
            "by_type": {
                t.value: [d.to_dict() for d in deps]
                for t, deps in self.by_type.items()
            },
            "region_pairs": {
                f"{r1}:{r2}": [d.to_dict() for d in deps]
                for (r1, r2), deps in self.region_pairs.items()
            },
            "summary": {
                "rds_read_replicas": len(
                    self.get_dependencies_by_type(CrossRegionType.RDS_READ_REPLICA)
                ),
                "aurora_global": len(
                    self.get_dependencies_by_type(CrossRegionType.AURORA_GLOBAL)
                ),
                "dynamodb_global_tables": len(
                    self.get_dependencies_by_type(CrossRegionType.DYNAMODB_GLOBAL_TABLE)
                ),
                "s3_replication": len(
                    self.get_dependencies_by_type(CrossRegionType.S3_REPLICATION)
                ),
                "transit_gateway_peering": len(
                    self.get_dependencies_by_type(CrossRegionType.TRANSIT_GATEWAY_PEERING)
                ),
                "route53_failover": len(
                    self.get_dependencies_by_type(CrossRegionType.ROUTE53_FAILOVER)
                ),
                "global_accelerator": len(
                    self.get_dependencies_by_type(CrossRegionType.GLOBAL_ACCELERATOR)
                ),
            },
            "metadata": self.metadata,
        }


class CrossRegionDetector:
    """
    Detects cross-region dependencies in infrastructure graphs.

    Analyzes resource configurations to identify relationships
    that span multiple AWS regions, including:
    - Database replication (RDS, Aurora, DynamoDB)
    - Storage replication (S3, EFS)
    - Network connectivity (Transit Gateway, VPC Peering)
    - Traffic routing (Route 53, Global Accelerator)
    """

    # Resource types that can have cross-region relationships
    CROSS_REGION_TYPES = {
        # Database
        "aws_db_instance",
        "aws_rds_cluster",
        "aws_dynamodb_table",
        "aws_elasticache_replication_group",
        "aws_docdb_cluster",
        # Storage
        "aws_s3_bucket",
        "aws_efs_file_system",
        # Networking
        "aws_ec2_transit_gateway",
        "aws_ec2_transit_gateway_peering_attachment",
        "aws_vpc_peering_connection",
        # DNS & Traffic
        "aws_route53_record",
        "aws_route53_health_check",
        "aws_globalaccelerator_accelerator",
        "aws_globalaccelerator_endpoint_group",
        # CDN
        "aws_cloudfront_distribution",
    }

    def detect(self, graph: VisualizationGraph) -> CrossRegionAnalysis:
        """
        Detect cross-region dependencies in a graph.

        Args:
            graph: Infrastructure graph to analyze

        Returns:
            CrossRegionAnalysis with detected dependencies
        """
        dependencies: list[CrossRegionDependency] = []

        # Build node lookup by ID
        nodes_by_id: dict[str, GraphNode] = {n.id: n for n in graph.nodes}

        # Detect each type of cross-region dependency
        dependencies.extend(self._detect_rds_replicas(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_aurora_global(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_dynamodb_global(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_s3_replication(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_transit_gateway_peering(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_route53_failover(graph.nodes, nodes_by_id))
        dependencies.extend(self._detect_global_accelerator(graph.nodes, nodes_by_id))

        # Organize by type and region pairs
        by_type: dict[CrossRegionType, list[CrossRegionDependency]] = {}
        region_pairs: dict[tuple[str, str], list[CrossRegionDependency]] = {}

        for dep in dependencies:
            # By type
            if dep.dependency_type not in by_type:
                by_type[dep.dependency_type] = []
            by_type[dep.dependency_type].append(dep)

            # By region pair
            pair = (dep.source_region, dep.target_region)
            if pair not in region_pairs:
                region_pairs[pair] = []
            region_pairs[pair].append(dep)

        return CrossRegionAnalysis(
            dependencies=dependencies,
            by_type=by_type,
            region_pairs=region_pairs,
            metadata={
                "nodes_analyzed": len(graph.nodes),
                "cross_region_types_found": [t.value for t in by_type.keys()],
            },
        )

    def _detect_rds_replicas(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect RDS read replicas across regions."""
        dependencies: list[CrossRegionDependency] = []

        for node in nodes:
            if node.resource_type != "aws_db_instance":
                continue

            props = node.properties
            source_db = props.get("replicate_source_db") or props.get("ReplicateSourceDBInstanceIdentifier")

            if source_db:
                # This is a read replica
                source_region = self._extract_region_from_arn(source_db)
                target_region = props.get("region", "unknown")

                if source_region and source_region != target_region:
                    # Cross-region replica found
                    source_id = self._extract_id_from_arn(source_db)

                    dependencies.append(
                        CrossRegionDependency(
                            source_id=source_id,
                            source_region=source_region,
                            source_type="aws_db_instance",
                            target_id=node.id,
                            target_region=target_region,
                            target_type="aws_db_instance",
                            dependency_type=CrossRegionType.RDS_READ_REPLICA,
                            direction=ReplicationDirection.PRIMARY_TO_SECONDARY,
                            configuration={
                                "source_arn": source_db,
                            },
                        )
                    )

        return dependencies

    def _detect_aurora_global(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect Aurora Global Database clusters."""
        dependencies: list[CrossRegionDependency] = []

        # Group clusters by global cluster identifier
        global_clusters: dict[str, list[GraphNode]] = {}

        for node in nodes:
            if node.resource_type != "aws_rds_cluster":
                continue

            props = node.properties
            global_id = props.get("global_cluster_identifier") or props.get("GlobalClusterIdentifier")

            if global_id:
                if global_id not in global_clusters:
                    global_clusters[global_id] = []
                global_clusters[global_id].append(node)

        # Create dependencies between clusters in the same global database
        for global_id, clusters in global_clusters.items():
            if len(clusters) < 2:
                continue

            # Find primary (writer) cluster
            primary = None
            secondaries: list[GraphNode] = []

            for cluster in clusters:
                props = cluster.properties
                # Check various ways to identify primary
                is_primary = (
                    props.get("is_primary_cluster", False) or
                    props.get("replication_source_identifier") is None
                )
                if is_primary and primary is None:
                    primary = cluster
                else:
                    secondaries.append(cluster)

            if primary is None:
                # If no clear primary, use first cluster
                primary = clusters[0]
                secondaries = clusters[1:]

            primary_region = primary.properties.get("region", "unknown")

            for secondary in secondaries:
                secondary_region = secondary.properties.get("region", "unknown")

                if primary_region != secondary_region:
                    dependencies.append(
                        CrossRegionDependency(
                            source_id=primary.id,
                            source_region=primary_region,
                            source_type="aws_rds_cluster",
                            target_id=secondary.id,
                            target_region=secondary_region,
                            target_type="aws_rds_cluster",
                            dependency_type=CrossRegionType.AURORA_GLOBAL,
                            direction=ReplicationDirection.PRIMARY_TO_SECONDARY,
                            configuration={
                                "global_cluster_identifier": global_id,
                            },
                        )
                    )

        return dependencies

    def _detect_dynamodb_global(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect DynamoDB Global Tables."""
        dependencies: list[CrossRegionDependency] = []

        for node in nodes:
            if node.resource_type != "aws_dynamodb_table":
                continue

            props = node.properties
            replicas = props.get("replica", []) or props.get("Replicas", [])

            if not isinstance(replicas, list) or not replicas:
                continue

            source_region = props.get("region", "unknown")

            for replica in replicas:
                if isinstance(replica, dict):
                    target_region = replica.get("region_name") or replica.get("RegionName")
                elif isinstance(replica, str):
                    target_region = replica
                else:
                    continue

                if target_region and target_region != source_region:
                    dependencies.append(
                        CrossRegionDependency(
                            source_id=node.id,
                            source_region=source_region,
                            source_type="aws_dynamodb_table",
                            target_id=f"{node.id}:{target_region}",
                            target_region=target_region,
                            target_type="aws_dynamodb_table",
                            dependency_type=CrossRegionType.DYNAMODB_GLOBAL_TABLE,
                            direction=ReplicationDirection.BIDIRECTIONAL,
                            configuration={
                                "table_name": node.name,
                            },
                        )
                    )

        return dependencies

    def _detect_s3_replication(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect S3 cross-region replication."""
        dependencies: list[CrossRegionDependency] = []

        for node in nodes:
            if node.resource_type != "aws_s3_bucket":
                continue

            props = node.properties
            replication = props.get("replication_configuration") or props.get("ReplicationConfiguration")

            if not replication:
                continue

            source_region = props.get("region", "unknown")

            # Parse replication rules
            rules = []
            if isinstance(replication, dict):
                rules = replication.get("rules", []) or replication.get("Rules", [])
            elif isinstance(replication, list):
                rules = replication

            for rule in rules:
                if not isinstance(rule, dict):
                    continue

                destination = rule.get("destination") or rule.get("Destination", {})
                if not isinstance(destination, dict):
                    continue

                # Get destination bucket
                dest_bucket = destination.get("bucket") or destination.get("Bucket", "")
                dest_region = self._extract_region_from_arn(dest_bucket)

                if dest_region and dest_region != source_region:
                    dependencies.append(
                        CrossRegionDependency(
                            source_id=node.id,
                            source_region=source_region,
                            source_type="aws_s3_bucket",
                            target_id=self._extract_id_from_arn(dest_bucket),
                            target_region=dest_region,
                            target_type="aws_s3_bucket",
                            dependency_type=CrossRegionType.S3_REPLICATION,
                            direction=ReplicationDirection.PRIMARY_TO_SECONDARY,
                            configuration={
                                "destination_bucket": dest_bucket,
                                "rule_status": rule.get("status") or rule.get("Status"),
                            },
                        )
                    )

        return dependencies

    def _detect_transit_gateway_peering(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect Transit Gateway peering attachments."""
        dependencies: list[CrossRegionDependency] = []

        for node in nodes:
            if node.resource_type != "aws_ec2_transit_gateway_peering_attachment":
                continue

            props = node.properties

            # Get local and peer transit gateway info
            local_tgw = props.get("transit_gateway_id")
            peer_tgw = props.get("peer_transit_gateway_id")
            peer_region = props.get("peer_region")
            local_region = props.get("region", "unknown")

            if peer_tgw and peer_region and local_region != peer_region:
                dependencies.append(
                    CrossRegionDependency(
                        source_id=local_tgw or node.id,
                        source_region=local_region,
                        source_type="aws_ec2_transit_gateway",
                        target_id=peer_tgw,
                        target_region=peer_region,
                        target_type="aws_ec2_transit_gateway",
                        dependency_type=CrossRegionType.TRANSIT_GATEWAY_PEERING,
                        direction=ReplicationDirection.BIDIRECTIONAL,
                        configuration={
                            "peering_attachment_id": node.id,
                            "state": props.get("state"),
                        },
                    )
                )

        return dependencies

    def _detect_route53_failover(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect Route 53 failover and latency-based routing."""
        dependencies: list[CrossRegionDependency] = []

        # Group records by name for multi-region sets
        records_by_name: dict[str, list[GraphNode]] = {}

        for node in nodes:
            if node.resource_type != "aws_route53_record":
                continue

            props = node.properties
            record_name = props.get("name") or props.get("Name", "")

            # Check for failover or latency routing
            routing_policy = props.get("set_identifier") or props.get("failover_routing_policy")
            if routing_policy or props.get("latency_routing_policy") or props.get("geolocation_routing_policy"):
                if record_name not in records_by_name:
                    records_by_name[record_name] = []
                records_by_name[record_name].append(node)

        # Find failover pairs
        for record_name, records in records_by_name.items():
            if len(records) < 2:
                continue

            # Identify primary and secondary
            primary = None
            secondaries: list[GraphNode] = []

            for record in records:
                props = record.properties
                failover_policy = props.get("failover_routing_policy")
                if isinstance(failover_policy, dict):
                    if failover_policy.get("type") == "PRIMARY":
                        primary = record
                    else:
                        secondaries.append(record)
                elif props.get("failover") == "PRIMARY":
                    primary = record
                else:
                    secondaries.append(record)

            if primary is None:
                continue

            primary_region = primary.properties.get("region", "unknown")

            for secondary in secondaries:
                secondary_region = secondary.properties.get("region", "unknown")

                if primary_region != secondary_region:
                    dependencies.append(
                        CrossRegionDependency(
                            source_id=primary.id,
                            source_region=primary_region,
                            source_type="aws_route53_record",
                            target_id=secondary.id,
                            target_region=secondary_region,
                            target_type="aws_route53_record",
                            dependency_type=CrossRegionType.ROUTE53_FAILOVER,
                            direction=ReplicationDirection.PRIMARY_TO_SECONDARY,
                            configuration={
                                "record_name": record_name,
                            },
                        )
                    )

        return dependencies

    def _detect_global_accelerator(
        self,
        nodes: list[GraphNode],
        nodes_by_id: dict[str, GraphNode],
    ) -> list[CrossRegionDependency]:
        """Detect Global Accelerator endpoint groups."""
        dependencies: list[CrossRegionDependency] = []

        # Find accelerators and their endpoint groups
        accelerators: dict[str, GraphNode] = {}
        endpoint_groups: list[GraphNode] = []

        for node in nodes:
            if node.resource_type == "aws_globalaccelerator_accelerator":
                accelerators[node.id] = node
            elif node.resource_type == "aws_globalaccelerator_endpoint_group":
                endpoint_groups.append(node)

        # Link endpoint groups to accelerators
        for eg in endpoint_groups:
            props = eg.properties

            # Find parent accelerator
            listener_arn = props.get("listener_arn", "")
            accelerator_arn = self._extract_accelerator_from_listener(listener_arn)

            # Get endpoint group region
            eg_region = props.get("endpoint_group_region") or props.get("region", "unknown")

            # Global Accelerator is global, but endpoint groups are regional
            for acc_id, acc in accelerators.items():
                acc_region = acc.properties.get("region", "us-west-2")  # GA typically us-west-2

                if eg_region != acc_region:
                    dependencies.append(
                        CrossRegionDependency(
                            source_id=acc_id,
                            source_region="global",  # GA is global service
                            source_type="aws_globalaccelerator_accelerator",
                            target_id=eg.id,
                            target_region=eg_region,
                            target_type="aws_globalaccelerator_endpoint_group",
                            dependency_type=CrossRegionType.GLOBAL_ACCELERATOR,
                            direction=ReplicationDirection.UNKNOWN,
                            configuration={
                                "accelerator_name": acc.name,
                            },
                        )
                    )

        return dependencies

    def _extract_region_from_arn(self, arn: str) -> str | None:
        """Extract region from an ARN."""
        if not arn or not isinstance(arn, str):
            return None

        # ARN format: arn:partition:service:region:account:resource
        parts = arn.split(":")
        if len(parts) >= 4 and parts[3]:
            return parts[3]

        return None

    def _extract_id_from_arn(self, arn: str) -> str:
        """Extract resource ID from an ARN."""
        if not arn or not isinstance(arn, str):
            return arn

        # ARN format: arn:partition:service:region:account:resource
        parts = arn.split(":")
        if len(parts) >= 6:
            resource = parts[5]
            # Handle resource/id or resource:id formats
            if "/" in resource:
                return resource.split("/")[-1]
            return resource

        return arn

    def _extract_accelerator_from_listener(self, listener_arn: str) -> str:
        """Extract accelerator ID from listener ARN."""
        if not listener_arn:
            return ""

        # Listener ARN format includes accelerator ID
        match = re.search(r"accelerator/([^/]+)", listener_arn)
        if match:
            return match.group(1)

        return ""


def detect_cross_region_dependencies(
    graph: VisualizationGraph,
) -> CrossRegionAnalysis:
    """
    Detect cross-region dependencies in an infrastructure graph.

    Args:
        graph: Infrastructure graph to analyze

    Returns:
        CrossRegionAnalysis with detected dependencies
    """
    detector = CrossRegionDetector()
    return detector.detect(graph)


def enrich_graph_with_cross_region(
    graph: VisualizationGraph,
    analysis: CrossRegionAnalysis | None = None,
) -> VisualizationGraph:
    """
    Enrich a graph with cross-region dependency edges.

    Args:
        graph: Graph to enrich
        analysis: Pre-computed analysis (will compute if None)

    Returns:
        Enriched VisualizationGraph with cross-region edges
    """
    if analysis is None:
        analysis = detect_cross_region_dependencies(graph)

    # Add cross-region edges
    new_edges = graph.edges.copy()
    for dep in analysis.dependencies:
        new_edges.append(dep.to_graph_edge())

    # Update metadata
    new_metadata = graph.metadata.copy()
    new_metadata["cross_region_dependencies"] = analysis.total_dependencies
    new_metadata["cross_region_types"] = [
        t.value for t in analysis.by_type.keys()
    ]

    return VisualizationGraph(
        nodes=graph.nodes,
        edges=new_edges,
        metadata=new_metadata,
    )


def get_cross_region_pairs(
    analysis: CrossRegionAnalysis,
) -> dict[str, str]:
    """
    Get mapping of source to target resource IDs for cross-region pairs.

    Useful for DR assessment to identify resources with cross-region replicas.

    Args:
        analysis: Cross-region analysis results

    Returns:
        Dictionary mapping source resource IDs to target resource IDs
    """
    pairs: dict[str, str] = {}
    for dep in analysis.dependencies:
        pairs[dep.source_id] = dep.target_id
        # For bidirectional, add reverse mapping too
        if dep.direction == ReplicationDirection.BIDIRECTIONAL:
            pairs[dep.target_id] = dep.source_id
    return pairs


def find_single_region_resources(
    graph: VisualizationGraph,
    analysis: CrossRegionAnalysis,
    resource_types: set[str] | None = None,
) -> list[GraphNode]:
    """
    Find resources that don't have cross-region replicas.

    Args:
        graph: Infrastructure graph
        analysis: Cross-region analysis
        resource_types: Types to check (default: databases and storage)

    Returns:
        List of nodes without cross-region dependencies
    """
    if resource_types is None:
        resource_types = {
            "aws_db_instance",
            "aws_rds_cluster",
            "aws_dynamodb_table",
            "aws_s3_bucket",
        }

    # Get all resources with cross-region dependencies
    has_cross_region: set[str] = set()
    for dep in analysis.dependencies:
        has_cross_region.add(dep.source_id)
        has_cross_region.add(dep.target_id)

    # Find single-region resources
    single_region: list[GraphNode] = []
    for node in graph.nodes:
        if node.resource_type in resource_types and node.id not in has_cross_region:
            single_region.append(node)

    return single_region


def calculate_replication_coverage(
    graph: VisualizationGraph,
    analysis: CrossRegionAnalysis,
) -> dict[str, float]:
    """
    Calculate cross-region replication coverage by resource type.

    Args:
        graph: Infrastructure graph
        analysis: Cross-region analysis

    Returns:
        Dictionary mapping resource type to coverage percentage
    """
    # Count total resources by type
    total_by_type: dict[str, int] = {}
    for node in graph.nodes:
        rt = node.resource_type
        total_by_type[rt] = total_by_type.get(rt, 0) + 1

    # Count replicated resources by type
    replicated_ids: set[str] = set()
    for dep in analysis.dependencies:
        replicated_ids.add(dep.source_id)

    replicated_by_type: dict[str, int] = {}
    for node in graph.nodes:
        if node.id in replicated_ids:
            rt = node.resource_type
            replicated_by_type[rt] = replicated_by_type.get(rt, 0) + 1

    # Calculate coverage
    coverage: dict[str, float] = {}
    for rt, total in total_by_type.items():
        replicated = replicated_by_type.get(rt, 0)
        coverage[rt] = (replicated / total * 100) if total > 0 else 0.0

    return coverage
