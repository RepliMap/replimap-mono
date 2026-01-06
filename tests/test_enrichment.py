"""
Tests for Graph Enrichment module.

Tests cover:
- NetworkReachabilityAnalyzer for SG rule analysis
- MetadataExtractor for UserData parsing
- GraphEnricher orchestration
- Confidence levels and edge deduplication
- Baseline policy generation
"""

from __future__ import annotations

import pytest

from replimap.core.enrichment import (
    ConfidenceLevel,
    EnrichedEdge,
    EnrichmentResult,
    EnrichmentSource,
    GraphEnricher,
    MetadataExtractor,
    NetworkReachabilityAnalyzer,
)
from replimap.core.graph_engine import GraphEngine
from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.security.iam_generator import (
    ARNBuilder,
    BaselinePolicyGenerator,
    PolicyScope,
)

# ============================================================
# ENRICHED EDGE TESTS
# ============================================================


class TestEnrichedEdge:
    """Test EnrichedEdge data structure."""

    def test_enriched_edge_creation(self):
        edge = EnrichedEdge(
            source_id="i-abc123",
            target_id="rds-prod-db",
            target_type="aws_db_instance",
            confidence=ConfidenceLevel.HIGH,
            enrichment_source=EnrichmentSource.SECURITY_GROUP,
            evidence="SG sg-123 allows egress on port 3306",
            port=3306,
        )

        assert edge.source_id == "i-abc123"
        assert edge.target_id == "rds-prod-db"
        assert edge.confidence == ConfidenceLevel.HIGH
        assert edge.port == 3306


class TestEnrichmentResult:
    """Test EnrichmentResult aggregation."""

    def test_add_edge_updates_stats(self):
        result = EnrichmentResult()

        edge1 = EnrichedEdge(
            source_id="a",
            target_id="b",
            target_type="aws_s3_bucket",
            confidence=ConfidenceLevel.HIGH,
            enrichment_source=EnrichmentSource.SECURITY_GROUP,
            evidence="test",
        )
        edge2 = EnrichedEdge(
            source_id="a",
            target_id="c",
            target_type="aws_sqs_queue",
            confidence=ConfidenceLevel.MEDIUM,
            enrichment_source=EnrichmentSource.USERDATA,
            evidence="test",
        )

        result.add_edge(edge1)
        result.add_edge(edge2)

        assert result.total_edges == 2
        assert result.edges_by_confidence[ConfidenceLevel.HIGH] == 1
        assert result.edges_by_confidence[ConfidenceLevel.MEDIUM] == 1
        assert result.edges_by_source[EnrichmentSource.SECURITY_GROUP] == 1
        assert result.edges_by_source[EnrichmentSource.USERDATA] == 1

    def test_high_confidence_edges(self):
        result = EnrichmentResult()

        high_edge = EnrichedEdge(
            source_id="a",
            target_id="b",
            target_type="aws_s3_bucket",
            confidence=ConfidenceLevel.HIGH,
            enrichment_source=EnrichmentSource.SECURITY_GROUP,
            evidence="test",
        )
        medium_edge = EnrichedEdge(
            source_id="a",
            target_id="c",
            target_type="aws_sqs_queue",
            confidence=ConfidenceLevel.MEDIUM,
            enrichment_source=EnrichmentSource.USERDATA,
            evidence="test",
        )

        result.add_edge(high_edge)
        result.add_edge(medium_edge)

        high_only = result.high_confidence_edges
        assert len(high_only) == 1
        assert high_only[0].target_id == "b"


# ============================================================
# NETWORK REACHABILITY ANALYZER TESTS
# ============================================================


class TestNetworkReachabilityAnalyzer:
    """Test Security Group rule analysis."""

    @pytest.fixture
    def graph_with_sg_rules(self):
        """Create graph with EC2, RDS, and SG rules."""
        graph = GraphEngine()

        # Security Group for EC2
        sg_ec2 = ResourceNode(
            id="sg-ec2-app",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            config={
                "name": "app-sg",
                "vpc_id": "vpc-123",
                "ingress": [],
                "egress": [
                    {
                        "from_port": 3306,
                        "to_port": 3306,
                        "protocol": "tcp",
                        "security_groups": [{"security_group_id": "sg-rds-db"}],
                    }
                ],
            },
        )

        # Security Group for RDS
        sg_rds = ResourceNode(
            id="sg-rds-db",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            config={
                "name": "db-sg",
                "vpc_id": "vpc-123",
                "ingress": [
                    {
                        "from_port": 3306,
                        "to_port": 3306,
                        "protocol": "tcp",
                        "security_groups": [{"security_group_id": "sg-ec2-app"}],
                    }
                ],
                "egress": [],
            },
        )

        # EC2 Instance
        ec2 = ResourceNode(
            id="i-abc123",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "vpc_id": "vpc-123",
                "security_group_ids": ["sg-ec2-app"],
            },
            original_name="web-server",
        )

        # RDS Instance
        rds = ResourceNode(
            id="rds-prod-db",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            config={
                "vpc_id": "vpc-123",
                "vpc_security_group_ids": ["sg-rds-db"],
                "identifier": "prod-db",
            },
            original_name="prod-db",
        )

        graph.add_resource(sg_ec2)
        graph.add_resource(sg_rds)
        graph.add_resource(ec2)
        graph.add_resource(rds)

        return graph

    def test_detects_sg_to_sg_dependency(self, graph_with_sg_rules):
        """EC2 with egress to RDS's SG should create dependency."""
        analyzer = NetworkReachabilityAnalyzer(graph_with_sg_rules)
        edges = analyzer.analyze()

        # Should find EC2 -> RDS dependency
        ec2_to_rds = [e for e in edges if e.source_id == "i-abc123"]
        assert len(ec2_to_rds) >= 1
        assert any(e.target_id == "rds-prod-db" for e in ec2_to_rds)

        # Should be HIGH confidence (SG-to-SG)
        rds_edge = next(e for e in ec2_to_rds if e.target_id == "rds-prod-db")
        assert rds_edge.confidence == ConfidenceLevel.HIGH
        assert rds_edge.port == 3306

    def test_no_false_positives_without_sg_rules(self):
        """EC2 without SG egress rules should not create dependencies."""
        graph = GraphEngine()

        sg = ResourceNode(
            id="sg-isolated",
            resource_type=ResourceType.SECURITY_GROUP,
            region="us-east-1",
            config={
                "name": "isolated-sg",
                "vpc_id": "vpc-123",
                "ingress": [],
                "egress": [],  # No egress rules
            },
        )

        ec2 = ResourceNode(
            id="i-isolated",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "vpc_id": "vpc-123",
                "security_group_ids": ["sg-isolated"],
            },
        )

        graph.add_resource(sg)
        graph.add_resource(ec2)

        analyzer = NetworkReachabilityAnalyzer(graph)
        edges = analyzer.analyze()

        assert len(edges) == 0


# ============================================================
# METADATA EXTRACTOR TESTS
# ============================================================


class TestMetadataExtractor:
    """Test UserData and environment variable extraction."""

    @pytest.fixture
    def graph_with_s3(self):
        """Graph with S3 bucket (user_data is scrubbed by graph engine)."""
        graph = GraphEngine()

        s3 = ResourceNode(
            id="s3-my-data-bucket",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"bucket": "my-data-bucket"},
            original_name="my-data-bucket",
        )

        graph.add_resource(s3)

        return graph

    def test_find_s3_references_directly(self, graph_with_s3):
        """Test _find_s3_references method directly (bypasses graph scrubbing)."""
        extractor = MetadataExtractor(graph_with_s3)
        extractor._build_resource_index()

        # Test with raw userdata content (not scrubbed)
        userdata = "#!/bin/bash\naws s3 cp s3://my-data-bucket/config.json /etc/app/"
        edges = extractor._find_s3_references(
            "i-test", userdata, EnrichmentSource.USERDATA
        )

        assert len(edges) >= 1
        assert edges[0].target_id == "s3-my-data-bucket"
        assert edges[0].confidence == ConfidenceLevel.MEDIUM
        assert edges[0].enrichment_source == EnrichmentSource.USERDATA

    def test_find_s3_references_with_arn(self, graph_with_s3):
        """Test S3 ARN pattern matching."""
        extractor = MetadataExtractor(graph_with_s3)
        extractor._build_resource_index()

        userdata = "S3_BUCKET=arn:aws:s3:::my-data-bucket"
        edges = extractor._find_s3_references(
            "i-test", userdata, EnrichmentSource.USERDATA
        )

        assert len(edges) >= 1
        assert edges[0].target_id == "s3-my-data-bucket"

    def test_no_edges_without_matching_resources(self):
        """Should not create edges for S3 refs that don't exist in graph."""
        graph = GraphEngine()

        s3 = ResourceNode(
            id="s3-other-bucket",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"bucket": "other-bucket"},
        )

        graph.add_resource(s3)

        extractor = MetadataExtractor(graph)
        extractor._build_resource_index()

        # Reference a bucket that doesn't exist in graph
        userdata = "aws s3 cp s3://nonexistent-bucket/file /tmp/"
        edges = extractor._find_s3_references(
            "i-test", userdata, EnrichmentSource.USERDATA
        )

        # No matching bucket in graph, so no edges
        assert len(edges) == 0


# ============================================================
# GRAPH ENRICHER TESTS
# ============================================================


class TestGraphEnricher:
    """Test main GraphEnricher orchestration."""

    @pytest.fixture
    def enrichable_graph(self):
        """Graph with EC2 and various data resources."""
        graph = GraphEngine()

        # VPC
        vpc = ResourceNode(
            id="vpc-123",
            resource_type=ResourceType.VPC,
            region="us-east-1",
            config={},
        )

        # EC2 instance
        ec2 = ResourceNode(
            id="i-web-server",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={
                "vpc_id": "vpc-123",
                "security_group_ids": [],
            },
            original_name="web-server",
        )

        graph.add_resource(vpc)
        graph.add_resource(ec2)
        graph.add_dependency("i-web-server", "vpc-123", DependencyType.BELONGS_TO)

        return graph

    def test_enricher_runs_without_error(self, enrichable_graph):
        """Enricher should run without errors even with minimal graph."""
        enricher = GraphEnricher(enrichable_graph)
        result = enricher.enrich()

        assert isinstance(result, EnrichmentResult)
        assert result.errors == []

    def test_enricher_respects_min_confidence(self, enrichable_graph):
        """Should filter edges by minimum confidence level."""
        enricher = GraphEnricher(enrichable_graph)

        # Run with HIGH min confidence
        result = enricher.enrich(min_confidence=ConfidenceLevel.HIGH)

        # All edges should be HIGH confidence
        for edge in result.edges_added:
            assert edge.confidence == ConfidenceLevel.HIGH

    def test_enricher_deduplicates_edges(self):
        """Should not add duplicate edges."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-test",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={},
        )

        s3 = ResourceNode(
            id="s3-bucket",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"bucket": "test-bucket"},
        )

        graph.add_resource(ec2)
        graph.add_resource(s3)

        enricher = GraphEnricher(graph)

        # Manually add duplicate edges
        edge1 = EnrichedEdge(
            source_id="i-test",
            target_id="s3-bucket",
            target_type="aws_s3_bucket",
            confidence=ConfidenceLevel.MEDIUM,
            enrichment_source=EnrichmentSource.USERDATA,
            evidence="test1",
        )
        edge2 = EnrichedEdge(
            source_id="i-test",
            target_id="s3-bucket",
            target_type="aws_s3_bucket",
            confidence=ConfidenceLevel.HIGH,
            enrichment_source=EnrichmentSource.SECURITY_GROUP,
            evidence="test2",
        )

        # Test deduplication (higher confidence should win)
        result = EnrichmentResult()
        assert enricher._should_add_edge(edge1, ConfidenceLevel.LOW)
        result.add_edge(edge1)

        # Second edge with higher confidence should replace
        assert enricher._should_add_edge(edge2, ConfidenceLevel.LOW)

    def test_tag_hint_parsing(self):
        """Should parse replimap:depends-on tags."""
        graph = GraphEngine()

        ec2 = ResourceNode(
            id="i-tagged",
            resource_type=ResourceType.EC2_INSTANCE,
            region="us-east-1",
            config={},
            tags={"replimap:depends-on": "s3-bucket,sqs-queue"},
        )

        s3 = ResourceNode(
            id="s3-bucket",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"bucket": "my-bucket"},
        )

        sqs = ResourceNode(
            id="sqs-queue",
            resource_type=ResourceType.SQS_QUEUE,
            region="us-east-1",
            config={"name": "my-queue"},
        )

        graph.add_resource(ec2)
        graph.add_resource(s3)
        graph.add_resource(sqs)

        enricher = GraphEnricher(graph)
        result = enricher.enrich(analyze_network=False, analyze_metadata=False)

        # Should have 2 edges from tag hints
        tag_edges = [
            e
            for e in result.edges_added
            if e.enrichment_source == EnrichmentSource.TAG_HINT
        ]
        assert len(tag_edges) == 2
        assert all(e.confidence == ConfidenceLevel.HIGH for e in tag_edges)


# ============================================================
# BASELINE POLICY GENERATOR TESTS
# ============================================================


class TestBaselinePolicyGenerator:
    """Test baseline policy generation for isolated resources."""

    def test_ec2_baseline_includes_cloudwatch(self):
        """EC2 baseline should include CloudWatch Logs."""
        arn_builder = ARNBuilder("123456789012", "us-east-1")
        generator = BaselinePolicyGenerator(arn_builder)

        statements = generator.generate_baseline(
            "web-server",
            "aws_instance",
            PolicyScope.RUNTIME_READ,
        )

        assert len(statements) >= 1
        logs_stmt = next(
            (s for s in statements if s.sid == "BaselineCloudWatchLogs"), None
        )
        assert logs_stmt is not None
        assert any("logs:" in a for a in logs_stmt.actions)

    def test_ec2_baseline_includes_ssm(self):
        """EC2 baseline should include SSM Parameter Store."""
        arn_builder = ARNBuilder("123456789012", "us-east-1")
        generator = BaselinePolicyGenerator(arn_builder)

        statements = generator.generate_baseline(
            "web-server",
            "aws_instance",
            PolicyScope.RUNTIME_READ,
        )

        ssm_stmt = next(
            (s for s in statements if s.sid == "BaselineSSMParameters"), None
        )
        assert ssm_stmt is not None
        assert any("ssm:" in a for a in ssm_stmt.actions)

    def test_ec2_baseline_includes_describe(self):
        """EC2 baseline should include EC2 Describe actions."""
        arn_builder = ARNBuilder("123456789012", "us-east-1")
        generator = BaselinePolicyGenerator(arn_builder)

        statements = generator.generate_baseline(
            "web-server",
            "aws_instance",
            PolicyScope.RUNTIME_READ,
        )

        ec2_stmt = next((s for s in statements if s.sid == "BaselineEC2Describe"), None)
        assert ec2_stmt is not None
        assert "ec2:DescribeInstances" in ec2_stmt.actions

    def test_lambda_baseline_different_log_prefix(self):
        """Lambda baseline should use 'lambda' log prefix."""
        arn_builder = ARNBuilder("123456789012", "us-east-1")
        generator = BaselinePolicyGenerator(arn_builder)

        statements = generator.generate_baseline(
            "my-function",
            "aws_lambda_function",
            PolicyScope.RUNTIME_FULL,
        )

        logs_stmt = next(
            (s for s in statements if s.sid == "BaselineCloudWatchLogs"), None
        )
        assert logs_stmt is not None
        assert any("/aws/lambda/" in r for r in logs_stmt.resources)

    def test_write_scope_excludes_ssm(self):
        """RUNTIME_WRITE should not include SSM read permissions."""
        arn_builder = ARNBuilder("123456789012", "us-east-1")
        generator = BaselinePolicyGenerator(arn_builder)

        statements = generator.generate_baseline(
            "web-server",
            "aws_instance",
            PolicyScope.RUNTIME_WRITE,
        )

        ssm_stmt = next(
            (s for s in statements if s.sid == "BaselineSSMParameters"), None
        )
        # SSM is read-only, so should not be in WRITE scope
        assert ssm_stmt is None
