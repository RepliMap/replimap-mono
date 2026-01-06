"""
Metadata Extractor for Graph Enrichment.

Extracts resource references from:
- EC2 UserData scripts (bash scripts, cloud-init)
- Lambda environment variables
- ECS task definition environment variables

Pattern Matching:
- S3 bucket names: s3://bucket-name, arn:aws:s3:::bucket-name
- RDS endpoints: *.rds.amazonaws.com, DB_HOST=...
- ElastiCache endpoints: *.cache.amazonaws.com
- SQS queue URLs: https://sqs.*.amazonaws.com/.../queue-name
- SNS topic ARNs: arn:aws:sns:region:account:topic-name
"""

from __future__ import annotations

import base64
import logging
import re
from typing import TYPE_CHECKING

from replimap.core.models import ResourceType

from .enricher import ConfidenceLevel, EnrichedEdge, EnrichmentSource

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


# Regex patterns for extracting resource references
PATTERNS = {
    # S3 bucket references
    "s3_uri": re.compile(r"s3://([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])(?:/|$)", re.I),
    "s3_arn": re.compile(r"arn:aws:s3:::([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])"),
    "s3_bucket_name": re.compile(
        r"(?:BUCKET[_\-]?NAME|S3[_\-]?BUCKET)\s*[=:]\s*['\"]?([a-z0-9][a-z0-9.-]{1,61}[a-z0-9])['\"]?",
        re.I,
    ),
    # RDS endpoints
    "rds_endpoint": re.compile(
        r"([a-z0-9][a-z0-9-]{0,62})\.[a-z0-9]+\.[a-z]{2}-[a-z]+-\d\.rds\.amazonaws\.com"
    ),
    "db_host": re.compile(
        r"(?:DB[_\-]?HOST|DATABASE[_\-]?HOST|MYSQL[_\-]?HOST|POSTGRES[_\-]?HOST|RDS[_\-]?ENDPOINT)\s*[=:]\s*['\"]?([^'\"\s,]+)['\"]?",
        re.I,
    ),
    # ElastiCache endpoints
    "elasticache_endpoint": re.compile(
        r"([a-z0-9][a-z0-9-]{0,62})\.(?:[a-z0-9]+\.)?[a-z]{2}-[a-z]+-\d\.cache\.amazonaws\.com"
    ),
    "redis_host": re.compile(
        r"(?:REDIS[_\-]?HOST|REDIS[_\-]?ENDPOINT|CACHE[_\-]?HOST|ELASTICACHE[_\-]?HOST)\s*[=:]\s*['\"]?([^'\"\s,]+)['\"]?",
        re.I,
    ),
    # SQS queue references
    "sqs_url": re.compile(
        r"https://sqs\.[a-z]{2}-[a-z]+-\d\.amazonaws\.com/\d{12}/([a-zA-Z0-9_-]+)"
    ),
    "sqs_arn": re.compile(r"arn:aws:sqs:[a-z]{2}-[a-z]+-\d:\d{12}:([a-zA-Z0-9_-]+)"),
    "sqs_name": re.compile(
        r"(?:SQS[_\-]?QUEUE[_\-]?(?:NAME|URL)?|QUEUE[_\-]?NAME)\s*[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?",
        re.I,
    ),
    # SNS topic references
    "sns_arn": re.compile(
        r"arn:aws:sns:[a-z]{2}-[a-z]+-\d:\d{12}:([a-zA-Z0-9_-]+)"
    ),
    "sns_name": re.compile(
        r"(?:SNS[_\-]?TOPIC[_\-]?(?:NAME|ARN)?|TOPIC[_\-]?NAME)\s*[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?",
        re.I,
    ),
    # DynamoDB table references
    "dynamodb_arn": re.compile(
        r"arn:aws:dynamodb:[a-z]{2}-[a-z]+-\d:\d{12}:table/([a-zA-Z0-9_.-]+)"
    ),
    "dynamodb_name": re.compile(
        r"(?:DYNAMODB[_\-]?TABLE[_\-]?(?:NAME)?|TABLE[_\-]?NAME)\s*[=:]\s*['\"]?([a-zA-Z0-9_.-]+)['\"]?",
        re.I,
    ),
}


class MetadataExtractor:
    """
    Extracts resource references from compute resource metadata.

    Analyzes:
    - EC2 UserData (base64 decoded)
    - Lambda environment variables
    - ECS task definition environment variables

    The extractor uses pattern matching to find references to:
    - S3 buckets (URIs, ARNs, env var names)
    - RDS instances (endpoints, DB_HOST vars)
    - ElastiCache clusters (endpoints, REDIS_HOST vars)
    - SQS queues (URLs, ARNs, env vars)
    - SNS topics (ARNs, env vars)

    These are MEDIUM confidence since they're inferred from text patterns
    rather than structural relationships.

    Example:
        extractor = MetadataExtractor(graph)
        edges = extractor.extract()
        # Finds edges like:
        # - i-abc123 -> my-bucket (S3, from UserData: s3://my-bucket)
        # - my-lambda -> my-queue (SQS, from env: QUEUE_URL=...)
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the extractor.

        Args:
            graph: The graph to analyze
        """
        self.graph = graph
        self._resource_index: dict[str, dict[str, str]] = {}

    def extract(self) -> list[EnrichedEdge]:
        """
        Extract resource references from all compute resources.

        Returns:
            List of EnrichedEdge objects for discovered dependencies
        """
        edges: list[EnrichedEdge] = []

        # Build index of data resources for faster lookup
        self._build_resource_index()

        # Process EC2 instances
        for node in self.graph.get_resources_by_type(ResourceType.EC2_INSTANCE):
            ec2_edges = self._extract_from_ec2(node)
            edges.extend(ec2_edges)

        # Note: Lambda and ECS extraction would go here when those
        # resource types are fully supported by scanners

        logger.info(f"Metadata extraction found {len(edges)} potential dependencies")
        return edges

    def _build_resource_index(self) -> None:
        """
        Build an index of data resources for pattern matching.

        Creates indexes by:
        - Resource ID
        - Resource name
        - ARN components
        """
        # S3 buckets
        for node in self.graph.get_resources_by_type(ResourceType.S3_BUCKET):
            bucket_name = node.config.get("bucket", node.id)
            self._resource_index.setdefault("s3", {})[bucket_name.lower()] = node.id

        # RDS instances
        for node in self.graph.get_resources_by_type(ResourceType.RDS_INSTANCE):
            # Index by identifier
            db_id = node.config.get("identifier", node.id)
            self._resource_index.setdefault("rds", {})[db_id.lower()] = node.id

            # Index by endpoint hostname prefix
            endpoint = node.config.get("endpoint", {})
            if isinstance(endpoint, dict):
                address = endpoint.get("address", "")
            else:
                address = str(endpoint)
            if address:
                # Extract hostname prefix (before first dot)
                prefix = address.split(".")[0].lower()
                self._resource_index.setdefault("rds", {})[prefix] = node.id

        # ElastiCache clusters
        for node in self.graph.get_resources_by_type(ResourceType.ELASTICACHE_CLUSTER):
            cluster_id = node.config.get("cluster_id", node.id)
            self._resource_index.setdefault("elasticache", {})[
                cluster_id.lower()
            ] = node.id

        # SQS queues
        for node in self.graph.get_resources_by_type(ResourceType.SQS_QUEUE):
            queue_name = node.config.get("name", "")
            if not queue_name:
                # Try to extract from URL or ARN
                queue_url = node.config.get("url", "")
                if queue_url:
                    queue_name = queue_url.rstrip("/").split("/")[-1]
            if queue_name:
                self._resource_index.setdefault("sqs", {})[queue_name.lower()] = node.id

        # SNS topics
        for node in self.graph.get_resources_by_type(ResourceType.SNS_TOPIC):
            topic_name = node.config.get("name", "")
            if not topic_name and node.arn:
                topic_name = node.arn.split(":")[-1]
            if topic_name:
                self._resource_index.setdefault("sns", {})[topic_name.lower()] = node.id

    def _extract_from_ec2(self, node) -> list[EnrichedEdge]:
        """
        Extract resource references from EC2 instance UserData.

        Args:
            node: The EC2 instance ResourceNode

        Returns:
            List of inferred edges
        """
        edges: list[EnrichedEdge] = []

        # Get UserData (may be base64 encoded)
        userdata = node.config.get("user_data", "")
        if not userdata:
            return edges

        # Try to decode if base64
        decoded = self._decode_userdata(userdata)

        # Extract S3 references
        edges.extend(
            self._find_s3_references(node.id, decoded, EnrichmentSource.USERDATA)
        )

        # Extract RDS references
        edges.extend(
            self._find_rds_references(node.id, decoded, EnrichmentSource.USERDATA)
        )

        # Extract ElastiCache references
        edges.extend(
            self._find_elasticache_references(
                node.id, decoded, EnrichmentSource.USERDATA
            )
        )

        # Extract SQS references
        edges.extend(
            self._find_sqs_references(node.id, decoded, EnrichmentSource.USERDATA)
        )

        # Extract SNS references
        edges.extend(
            self._find_sns_references(node.id, decoded, EnrichmentSource.USERDATA)
        )

        return edges

    def _decode_userdata(self, userdata: str) -> str:
        """
        Attempt to decode base64-encoded UserData.

        Args:
            userdata: Raw UserData string

        Returns:
            Decoded string, or original if not base64
        """
        try:
            decoded = base64.b64decode(userdata).decode("utf-8", errors="replace")
            return decoded
        except Exception:
            # Not base64, return as-is
            return userdata

    def _find_s3_references(
        self,
        source_id: str,
        text: str,
        source: EnrichmentSource,
    ) -> list[EnrichedEdge]:
        """Find S3 bucket references in text."""
        edges: list[EnrichedEdge] = []
        s3_index = self._resource_index.get("s3", {})

        found_buckets: set[str] = set()

        # Check all S3 patterns
        for pattern_name in ["s3_uri", "s3_arn", "s3_bucket_name"]:
            pattern = PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                bucket = match.group(1).lower()
                if bucket in found_buckets:
                    continue
                found_buckets.add(bucket)

                target_id = s3_index.get(bucket)
                if target_id:
                    target = self.graph.get_resource(target_id)
                    if target:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.MEDIUM,
                            enrichment_source=source,
                            evidence=f"S3 ref in UserData: {match.group(0)[:40]}",
                        )
                        edges.append(edge)

        return edges

    def _find_rds_references(
        self,
        source_id: str,
        text: str,
        source: EnrichmentSource,
    ) -> list[EnrichedEdge]:
        """Find RDS instance references in text."""
        edges: list[EnrichedEdge] = []
        rds_index = self._resource_index.get("rds", {})

        found_dbs: set[str] = set()

        # Check RDS patterns
        for pattern_name in ["rds_endpoint", "db_host"]:
            pattern = PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                db_ref = match.group(1).lower()
                if db_ref in found_dbs:
                    continue
                found_dbs.add(db_ref)

                target_id = rds_index.get(db_ref)
                if target_id:
                    target = self.graph.get_resource(target_id)
                    if target:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.MEDIUM,
                            enrichment_source=source,
                            evidence=f"RDS ref in UserData: {match.group(0)[:40]}",
                        )
                        edges.append(edge)

        return edges

    def _find_elasticache_references(
        self,
        source_id: str,
        text: str,
        source: EnrichmentSource,
    ) -> list[EnrichedEdge]:
        """Find ElastiCache cluster references in text."""
        edges: list[EnrichedEdge] = []
        cache_index = self._resource_index.get("elasticache", {})

        found_clusters: set[str] = set()

        # Check ElastiCache patterns
        for pattern_name in ["elasticache_endpoint", "redis_host"]:
            pattern = PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                cluster_ref = match.group(1).lower()
                if cluster_ref in found_clusters:
                    continue
                found_clusters.add(cluster_ref)

                target_id = cache_index.get(cluster_ref)
                if target_id:
                    target = self.graph.get_resource(target_id)
                    if target:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.MEDIUM,
                            enrichment_source=source,
                            evidence=f"Cache ref in UserData: {match.group(0)[:40]}",
                        )
                        edges.append(edge)

        return edges

    def _find_sqs_references(
        self,
        source_id: str,
        text: str,
        source: EnrichmentSource,
    ) -> list[EnrichedEdge]:
        """Find SQS queue references in text."""
        edges: list[EnrichedEdge] = []
        sqs_index = self._resource_index.get("sqs", {})

        found_queues: set[str] = set()

        # Check SQS patterns
        for pattern_name in ["sqs_url", "sqs_arn", "sqs_name"]:
            pattern = PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                queue_ref = match.group(1).lower()
                if queue_ref in found_queues:
                    continue
                found_queues.add(queue_ref)

                target_id = sqs_index.get(queue_ref)
                if target_id:
                    target = self.graph.get_resource(target_id)
                    if target:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.MEDIUM,
                            enrichment_source=source,
                            evidence=f"SQS ref in UserData: {match.group(0)[:40]}",
                        )
                        edges.append(edge)

        return edges

    def _find_sns_references(
        self,
        source_id: str,
        text: str,
        source: EnrichmentSource,
    ) -> list[EnrichedEdge]:
        """Find SNS topic references in text."""
        edges: list[EnrichedEdge] = []
        sns_index = self._resource_index.get("sns", {})

        found_topics: set[str] = set()

        # Check SNS patterns
        for pattern_name in ["sns_arn", "sns_name"]:
            pattern = PATTERNS[pattern_name]
            for match in pattern.finditer(text):
                topic_ref = match.group(1).lower()
                if topic_ref in found_topics:
                    continue
                found_topics.add(topic_ref)

                target_id = sns_index.get(topic_ref)
                if target_id:
                    target = self.graph.get_resource(target_id)
                    if target:
                        edge = EnrichedEdge(
                            source_id=source_id,
                            target_id=target_id,
                            target_type=str(target.resource_type),
                            confidence=ConfidenceLevel.MEDIUM,
                            enrichment_source=source,
                            evidence=f"SNS ref in UserData: {match.group(0)[:40]}",
                        )
                        edges.append(edge)

        return edges
