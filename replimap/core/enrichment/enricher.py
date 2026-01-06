"""
Graph Enricher - Main orchestrator for dependency enrichment.

Discovers implicit dependencies that AWS infrastructure doesn't expose directly.
Each enrichment source has a confidence level to help downstream consumers
(like IAM policy generation) decide how to handle inferred dependencies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from replimap.core.models import DependencyType

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


class ConfidenceLevel(str, Enum):
    """Confidence level for inferred dependencies."""

    HIGH = "high"  # Strong structural evidence (SG rules, explicit tags)
    MEDIUM = "medium"  # Inferred from metadata/config (UserData, env vars)
    LOW = "low"  # Heuristic matches (naming patterns, conventions)

    def __str__(self) -> str:
        return self.value


class EnrichmentSource(str, Enum):
    """Source of the enriched dependency."""

    SECURITY_GROUP = "security_group"  # Inferred from SG rule analysis
    USERDATA = "userdata"  # Extracted from EC2 UserData
    ENV_VAR = "env_var"  # From Lambda/ECS environment variables
    TAG_HINT = "tag_hint"  # Explicit replimap:depends-on tag
    HEURISTIC = "heuristic"  # Naming pattern match

    def __str__(self) -> str:
        return self.value


@dataclass
class EnrichedEdge:
    """
    An enriched dependency edge with metadata about how it was discovered.

    Attributes:
        source_id: The resource that depends on target
        target_id: The resource being depended upon
        target_type: Resource type of target (aws_rds_instance, aws_s3_bucket, etc.)
        confidence: How confident we are in this dependency
        enrichment_source: How the dependency was discovered
        evidence: Human-readable explanation of why this was inferred
        port: Network port if relevant (for SG-based inference)
    """

    source_id: str
    target_id: str
    target_type: str
    confidence: ConfidenceLevel
    enrichment_source: EnrichmentSource
    evidence: str
    port: int | None = None


@dataclass
class EnrichmentResult:
    """
    Result of graph enrichment.

    Attributes:
        edges_added: List of enriched edges that were added to the graph
        edges_by_confidence: Count of edges by confidence level
        edges_by_source: Count of edges by enrichment source
        errors: Any errors encountered during enrichment
    """

    edges_added: list[EnrichedEdge] = field(default_factory=list)
    edges_by_confidence: dict[ConfidenceLevel, int] = field(default_factory=dict)
    edges_by_source: dict[EnrichmentSource, int] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def add_edge(self, edge: EnrichedEdge) -> None:
        """Add an edge and update statistics."""
        self.edges_added.append(edge)
        self.edges_by_confidence[edge.confidence] = (
            self.edges_by_confidence.get(edge.confidence, 0) + 1
        )
        self.edges_by_source[edge.enrichment_source] = (
            self.edges_by_source.get(edge.enrichment_source, 0) + 1
        )

    @property
    def total_edges(self) -> int:
        """Total number of edges added."""
        return len(self.edges_added)

    @property
    def high_confidence_edges(self) -> list[EnrichedEdge]:
        """Get only high-confidence edges."""
        return [e for e in self.edges_added if e.confidence == ConfidenceLevel.HIGH]


class GraphEnricher:
    """
    Orchestrates graph enrichment to discover implicit dependencies.

    The enricher runs multiple analyzers to find dependencies that aren't
    visible in AWS infrastructure alone:

    1. NetworkReachabilityAnalyzer (HIGH confidence):
       - Analyzes Security Group rules to find network connectivity
       - If EC2 has SG allowing port 3306 from RDS's SG, infer dependency

    2. MetadataExtractor (MEDIUM confidence):
       - Parses EC2 UserData scripts for resource references
       - Extracts Lambda/ECS environment variables
       - Looks for S3 bucket names, RDS endpoints, etc.

    3. TagHintAnalyzer (HIGH confidence):
       - Reads explicit `replimap:depends-on` tags
       - Users can declare dependencies explicitly

    Usage:
        enricher = GraphEnricher(graph)
        result = enricher.enrich()

        print(f"Added {result.total_edges} inferred dependencies")
        for edge in result.high_confidence_edges:
            print(f"  {edge.source_id} -> {edge.target_id} ({edge.evidence})")
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the enricher.

        Args:
            graph: The graph to enrich with inferred dependencies
        """
        self.graph = graph
        self._enriched_edges: dict[tuple[str, str], EnrichedEdge] = {}

    def enrich(
        self,
        analyze_network: bool = True,
        analyze_metadata: bool = True,
        analyze_tags: bool = True,
        min_confidence: ConfidenceLevel = ConfidenceLevel.LOW,
    ) -> EnrichmentResult:
        """
        Run all enabled enrichment analyzers.

        Args:
            analyze_network: Run Security Group network analysis
            analyze_metadata: Extract refs from UserData/env vars
            analyze_tags: Look for explicit replimap:depends-on tags
            min_confidence: Only add edges at or above this confidence level

        Returns:
            EnrichmentResult with all discovered dependencies
        """
        result = EnrichmentResult()

        logger.info("Starting graph enrichment...")

        # Phase 1: Explicit tag hints (highest priority)
        if analyze_tags:
            self._analyze_tag_hints(result, min_confidence)

        # Phase 2: Network reachability from SG rules
        if analyze_network:
            self._analyze_network_reachability(result, min_confidence)

        # Phase 3: Metadata extraction (UserData, env vars)
        if analyze_metadata:
            self._analyze_metadata(result, min_confidence)

        # Add all qualifying edges to the graph
        for edge in result.edges_added:
            self._add_edge_to_graph(edge)

        logger.info(
            f"Enrichment complete: {result.total_edges} edges added "
            f"(high: {result.edges_by_confidence.get(ConfidenceLevel.HIGH, 0)}, "
            f"medium: {result.edges_by_confidence.get(ConfidenceLevel.MEDIUM, 0)}, "
            f"low: {result.edges_by_confidence.get(ConfidenceLevel.LOW, 0)})"
        )

        return result

    def _analyze_tag_hints(
        self,
        result: EnrichmentResult,
        min_confidence: ConfidenceLevel,
    ) -> None:
        """
        Look for explicit replimap:depends-on tags.

        Tag format: replimap:depends-on = "resource-id-1,resource-id-2"
        """
        from replimap.core.models import ResourceType

        compute_types = {
            ResourceType.EC2_INSTANCE,
            ResourceType.AUTOSCALING_GROUP,
            ResourceType.LB,
        }

        for node in self.graph.get_all_resources():
            if node.resource_type not in compute_types:
                continue

            # Check for dependency tag
            depends_on = node.tags.get("replimap:depends-on", "")
            if not depends_on:
                continue

            # Parse comma-separated resource IDs
            target_ids = [t.strip() for t in depends_on.split(",") if t.strip()]

            for target_id in target_ids:
                target = self.graph.get_resource(target_id)
                if not target:
                    logger.warning(
                        f"Tag hint references unknown resource: {target_id} "
                        f"(from {node.id})"
                    )
                    continue

                edge = EnrichedEdge(
                    source_id=node.id,
                    target_id=target_id,
                    target_type=str(target.resource_type),
                    confidence=ConfidenceLevel.HIGH,
                    enrichment_source=EnrichmentSource.TAG_HINT,
                    evidence=f"Explicit tag: replimap:depends-on={target_id}",
                )

                if self._should_add_edge(edge, min_confidence):
                    result.add_edge(edge)

    def _analyze_network_reachability(
        self,
        result: EnrichmentResult,
        min_confidence: ConfidenceLevel,
    ) -> None:
        """
        Analyze Security Group rules to infer network dependencies.

        Delegates to NetworkReachabilityAnalyzer for the actual analysis.
        """
        from .network_analyzer import NetworkReachabilityAnalyzer

        analyzer = NetworkReachabilityAnalyzer(self.graph)
        edges = analyzer.analyze()

        for edge in edges:
            if self._should_add_edge(edge, min_confidence):
                result.add_edge(edge)

    def _analyze_metadata(
        self,
        result: EnrichmentResult,
        min_confidence: ConfidenceLevel,
    ) -> None:
        """
        Extract resource references from UserData and environment variables.

        Delegates to MetadataExtractor for the actual extraction.
        """
        from .metadata_extractor import MetadataExtractor

        extractor = MetadataExtractor(self.graph)
        edges = extractor.extract()

        for edge in edges:
            if self._should_add_edge(edge, min_confidence):
                result.add_edge(edge)

    def _should_add_edge(
        self,
        edge: EnrichedEdge,
        min_confidence: ConfidenceLevel,
    ) -> bool:
        """
        Check if an edge should be added based on confidence and deduplication.

        Args:
            edge: The edge to check
            min_confidence: Minimum confidence level required

        Returns:
            True if the edge should be added
        """
        # Check confidence level
        confidence_order = [
            ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, ConfidenceLevel.HIGH
        ]
        edge_idx = confidence_order.index(edge.confidence)
        min_idx = confidence_order.index(min_confidence)
        if edge_idx < min_idx:
            return False

        # Check if already exists (deduplicate)
        key = (edge.source_id, edge.target_id)
        if key in self._enriched_edges:
            existing = self._enriched_edges[key]
            # Keep higher confidence edge
            existing_idx = confidence_order.index(existing.confidence)
            if edge_idx > existing_idx:
                self._enriched_edges[key] = edge
                return True
            return False

        self._enriched_edges[key] = edge
        return True

    def _add_edge_to_graph(self, edge: EnrichedEdge) -> None:
        """
        Add an enriched edge to the actual graph.

        Uses DependencyType.USES for inferred dependencies.
        """
        # Skip if edge already exists in the original graph
        existing_deps = [d.id for d in self.graph.get_dependencies(edge.source_id)]
        if edge.target_id in existing_deps:
            logger.debug(
                f"Skipping duplicate edge: {edge.source_id} -> {edge.target_id}"
            )
            return

        try:
            self.graph.add_dependency(
                edge.source_id,
                edge.target_id,
                DependencyType.USES,
            )
            logger.debug(
                f"Added enriched edge: {edge.source_id} -> {edge.target_id} "
                f"[{edge.confidence}] ({edge.evidence})"
            )
        except ValueError as e:
            logger.warning(f"Could not add enriched edge: {e}")

    def get_enriched_edges_for_resource(
        self,
        resource_id: str,
    ) -> list[EnrichedEdge]:
        """
        Get all enriched edges for a specific resource.

        Args:
            resource_id: The resource to get edges for

        Returns:
            List of enriched edges where resource_id is the source
        """
        return [
            edge
            for edge in self._enriched_edges.values()
            if edge.source_id == resource_id
        ]
