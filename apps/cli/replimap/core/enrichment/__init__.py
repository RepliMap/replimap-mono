"""
Graph Enrichment Module for RepliMap.

Discovers implicit dependencies that can't be detected from AWS infrastructure alone.
This includes analyzing Security Group rules, extracting references from metadata,
and supporting explicit tag-based hints.

Key Components:
- GraphEnricher: Main orchestrator that runs all enrichment phases
- NetworkReachabilityAnalyzer: Infers dependencies from SG rules (high confidence)
- MetadataExtractor: Parses UserData/env vars for resource refs (medium confidence)

Confidence Levels:
- HIGH: Network reachability via SG rules (structural evidence)
- MEDIUM: Metadata/UserData references (inferred from config)
- LOW: Heuristic matches (naming patterns, etc.)

Usage:
    from replimap.core.enrichment import GraphEnricher

    enricher = GraphEnricher(graph)
    enricher.enrich()

    # Or with specific analyzers only
    enricher.enrich(
        analyze_network=True,
        analyze_metadata=False,
    )
"""

from .enricher import (
    ConfidenceLevel,
    EnrichedEdge,
    EnrichmentResult,
    EnrichmentSource,
    GraphEnricher,
)
from .metadata_extractor import MetadataExtractor
from .network_analyzer import NetworkReachabilityAnalyzer

__all__ = [
    # Main enricher
    "GraphEnricher",
    "EnrichmentResult",
    "EnrichedEdge",
    "ConfidenceLevel",
    "EnrichmentSource",
    # Analyzers
    "NetworkReachabilityAnalyzer",
    "MetadataExtractor",
]
