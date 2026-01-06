"""
Network Reachability Analyzer for Graph Enrichment.

Analyzes Security Group rules to infer implicit dependencies between
compute resources and data services.

Strategy:
1. Build SG → Resources mapping (which resources use which SGs)
2. For each compute resource (EC2, Lambda, ECS):
   a. Get its Security Groups
   b. For each SG, analyze egress rules
   c. If egress allows traffic to another SG used by a data resource,
      infer a dependency

Port-to-Service Mapping:
- 3306: MySQL/Aurora → aws_db_instance
- 5432: PostgreSQL → aws_db_instance
- 6379: Redis → aws_elasticache_cluster
- 11211: Memcached → aws_elasticache_cluster
- 443/80: API endpoints (lower confidence)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from replimap.core.models import ResourceType

from .enricher import ConfidenceLevel, EnrichedEdge, EnrichmentSource

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


# Well-known port to service type mapping
PORT_SERVICE_MAP: dict[int, tuple[str, str]] = {
    # Database ports
    3306: ("MySQL/Aurora", "aws_db_instance"),
    5432: ("PostgreSQL", "aws_db_instance"),
    1433: ("MSSQL", "aws_db_instance"),
    1521: ("Oracle", "aws_db_instance"),
    5439: ("Redshift", "aws_db_instance"),
    # Cache ports
    6379: ("Redis", "aws_elasticache_cluster"),
    11211: ("Memcached", "aws_elasticache_cluster"),
    # Message queue ports
    5672: ("RabbitMQ", "aws_mq_broker"),
    9092: ("Kafka", "aws_msk_cluster"),
    # Search ports
    9200: ("Elasticsearch", "aws_elasticsearch_domain"),
    9300: ("Elasticsearch", "aws_elasticsearch_domain"),
    # Document DB
    27017: ("DocumentDB/MongoDB", "aws_docdb_cluster"),
}

# Compute resource types that can be sources of dependencies
COMPUTE_TYPES: set[ResourceType] = {
    ResourceType.EC2_INSTANCE,
    ResourceType.AUTOSCALING_GROUP,
    ResourceType.LB,
}

# Data resource types that can be targets of dependencies
DATA_TYPES: set[ResourceType] = {
    ResourceType.RDS_INSTANCE,
    ResourceType.ELASTICACHE_CLUSTER,
    ResourceType.S3_BUCKET,
    ResourceType.SQS_QUEUE,
    ResourceType.SNS_TOPIC,
}


class NetworkReachabilityAnalyzer:
    """
    Analyzes Security Group rules to infer network-level dependencies.

    The analyzer builds a mapping of which resources use which Security Groups,
    then traces egress rules from compute resources to data resources.

    High Confidence (SG-to-SG rules):
        If EC2's SG allows egress to RDS's SG on port 3306, this is strong
        evidence of a database dependency.

    Medium Confidence (Port-based heuristics):
        If EC2's SG allows egress to 0.0.0.0/0 on port 3306, we check if
        there are any RDS instances in the same VPC and infer a possible
        dependency.

    Example:
        # EC2 instance i-abc123 uses sg-compute
        # RDS instance prod-db uses sg-database
        # sg-compute has egress rule: port 3306 -> sg-database

        analyzer = NetworkReachabilityAnalyzer(graph)
        edges = analyzer.analyze()
        # Returns: [EnrichedEdge(source=i-abc123, target=prod-db, ...)]
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the analyzer.

        Args:
            graph: The graph to analyze
        """
        self.graph = graph
        self._sg_to_resources: dict[str, list[str]] = {}
        self._resource_to_sgs: dict[str, list[str]] = {}
        self._sg_rules: dict[str, dict] = {}
        self._vpc_resources: dict[str, list[str]] = {}

    def analyze(self) -> list[EnrichedEdge]:
        """
        Analyze Security Group rules and return inferred edges.

        Returns:
            List of EnrichedEdge objects for discovered dependencies
        """
        edges: list[EnrichedEdge] = []

        # Build mappings
        self._build_sg_mappings()
        self._build_vpc_mappings()

        # Get all compute resources
        compute_resources = self._get_compute_resources()

        for compute in compute_resources:
            # Get SGs for this compute resource
            sgs = self._resource_to_sgs.get(compute.id, [])
            if not sgs:
                continue

            vpc_id = compute.config.get("vpc_id")

            # Analyze egress rules for each SG
            for sg_id in sgs:
                sg_node = self.graph.get_resource(sg_id)
                if not sg_node:
                    continue

                egress_rules = sg_node.config.get("egress", [])
                for rule in egress_rules:
                    rule_edges = self._analyze_egress_rule(
                        compute.id,
                        sg_id,
                        rule,
                        vpc_id,
                    )
                    edges.extend(rule_edges)

        logger.info(f"Network analysis found {len(edges)} potential dependencies")
        return edges

    def _build_sg_mappings(self) -> None:
        """Build bidirectional mapping between SGs and resources."""
        for node in self.graph.get_all_resources():
            # EC2 instances
            if node.resource_type == ResourceType.EC2_INSTANCE:
                sg_ids = node.config.get("security_group_ids", [])
                self._resource_to_sgs[node.id] = sg_ids
                for sg_id in sg_ids:
                    self._sg_to_resources.setdefault(sg_id, []).append(node.id)

            # RDS instances
            elif node.resource_type == ResourceType.RDS_INSTANCE:
                sg_ids = node.config.get("vpc_security_group_ids", [])
                self._resource_to_sgs[node.id] = sg_ids
                for sg_id in sg_ids:
                    self._sg_to_resources.setdefault(sg_id, []).append(node.id)

            # ElastiCache clusters
            elif node.resource_type == ResourceType.ELASTICACHE_CLUSTER:
                sg_ids = node.config.get("security_group_ids", [])
                self._resource_to_sgs[node.id] = sg_ids
                for sg_id in sg_ids:
                    self._sg_to_resources.setdefault(sg_id, []).append(node.id)

            # Load Balancers
            elif node.resource_type == ResourceType.LB:
                sg_ids = node.config.get("security_groups", [])
                self._resource_to_sgs[node.id] = sg_ids
                for sg_id in sg_ids:
                    self._sg_to_resources.setdefault(sg_id, []).append(node.id)

            # Store SG rules for later analysis
            elif node.resource_type == ResourceType.SECURITY_GROUP:
                self._sg_rules[node.id] = {
                    "ingress": node.config.get("ingress", []),
                    "egress": node.config.get("egress", []),
                }

    def _build_vpc_mappings(self) -> None:
        """Build mapping of VPC to resources for VPC-scoped inference."""
        for node in self.graph.get_all_resources():
            vpc_id = node.config.get("vpc_id")
            if vpc_id:
                self._vpc_resources.setdefault(vpc_id, []).append(node.id)

    def _get_compute_resources(self) -> list:
        """Get all compute resources from the graph."""
        resources = []
        for node in self.graph.get_all_resources():
            if node.resource_type in COMPUTE_TYPES:
                resources.append(node)
        return resources

    def _analyze_egress_rule(
        self,
        source_id: str,
        sg_id: str,
        rule: dict,
        vpc_id: str | None,
    ) -> list[EnrichedEdge]:
        """
        Analyze a single egress rule and return any inferred edges.

        Args:
            source_id: The compute resource ID
            sg_id: The security group ID
            rule: The egress rule dictionary
            vpc_id: The VPC ID for scoping

        Returns:
            List of inferred edges
        """
        edges: list[EnrichedEdge] = []

        from_port = rule.get("from_port", 0)
        to_port = rule.get("to_port", 0)
        protocol = rule.get("protocol", "-1")

        # Skip rules that don't specify ports (all traffic)
        if protocol == "-1" and from_port == 0 and to_port == 0:
            return edges

        # Check for SG-to-SG references (HIGH confidence)
        sg_refs = rule.get("security_groups", [])
        for sg_ref in sg_refs:
            target_sg_id = sg_ref.get("security_group_id")
            if not target_sg_id:
                continue

            # Find resources using the target SG
            target_resources = self._sg_to_resources.get(target_sg_id, [])
            for target_id in target_resources:
                target = self.graph.get_resource(target_id)
                if not target or target.resource_type not in DATA_TYPES:
                    continue

                # Check if port matches expected service
                port_info = self._get_port_service(from_port, to_port)
                if port_info:
                    service_name, expected_type = port_info
                    if str(target.resource_type) == expected_type:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.HIGH,
                            enrichment_source=EnrichmentSource.SECURITY_GROUP,
                            evidence=(
                                f"SG {sg_id} egress:{from_port} ({service_name}) "
                                f"-> SG {target_sg_id} -> {target_id}"
                            ),
                            port=from_port,
                        )
                        edges.append(edge)
                else:
                    # Generic SG-to-SG dependency without port matching
                    edge = EnrichedEdge(
                        source_id=source_id,
                        target_id=target_id,
                        target_type=str(target.resource_type),
                        confidence=ConfidenceLevel.HIGH,
                        enrichment_source=EnrichmentSource.SECURITY_GROUP,
                        evidence=(
                            f"SG {sg_id} allows egress to SG {target_sg_id} "
                            f"used by {target_id}"
                        ),
                        port=from_port if from_port else None,
                    )
                    edges.append(edge)

        # Check for port-based inference when no SG refs (MEDIUM confidence)
        # Only if rule has CIDR blocks (not SG refs)
        cidr_blocks = rule.get("cidr_blocks", [])
        if cidr_blocks and not sg_refs:
            port_info = self._get_port_service(from_port, to_port)
            if port_info:
                service_name, expected_type = port_info
                # Find data resources of matching type in the same VPC
                candidate_targets = self._find_vpc_resources_by_type(
                    vpc_id, expected_type
                )
                for target_id in candidate_targets:
                    target = self.graph.get_resource(target_id)
                    if not target:
                        continue

                    edge = EnrichedEdge(
                        source_id=source_id,
                        target_id=target_id,
                        target_type=str(target.resource_type),
                        confidence=ConfidenceLevel.MEDIUM,
                        enrichment_source=EnrichmentSource.SECURITY_GROUP,
                        evidence=(
                            f"SG {sg_id} allows egress on port {from_port} "
                            f"({service_name}); {target_id} is a {service_name} "
                            f"resource in the same VPC"
                        ),
                        port=from_port,
                    )
                    edges.append(edge)

        return edges

    def _get_port_service(
        self, from_port: int, to_port: int
    ) -> tuple[str, str] | None:
        """
        Get service info for a port range.

        Args:
            from_port: Start of port range
            to_port: End of port range

        Returns:
            Tuple of (service_name, resource_type) or None
        """
        # For single port or small range, check exact match
        if from_port == to_port:
            return PORT_SERVICE_MAP.get(from_port)

        # Check if any known port is in the range
        for port, info in PORT_SERVICE_MAP.items():
            if from_port <= port <= to_port:
                return info

        return None

    def _find_vpc_resources_by_type(
        self, vpc_id: str | None, resource_type: str
    ) -> list[str]:
        """
        Find resources of a given type in a VPC.

        Args:
            vpc_id: The VPC to search in
            resource_type: The resource type string

        Returns:
            List of resource IDs
        """
        if not vpc_id:
            return []

        results = []
        vpc_resource_ids = self._vpc_resources.get(vpc_id, [])
        for rid in vpc_resource_ids:
            resource = self.graph.get_resource(rid)
            if resource and str(resource.resource_type) == resource_type:
                results.append(rid)
        return results
