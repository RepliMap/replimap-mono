"""Tests for graph visualization optimization modules."""

from replimap.graph.blast_radius import (
    AffectedResource,
    BlastRadiusCalculator,
    ImpactSeverity,
    calculate_blast_radius,
    enrich_nodes_with_blast_radius,
    find_critical_nodes,
)
from replimap.graph.cost_overlay import (
    CostCalculator,
    CostEstimate,
    CostTier,
    calculate_container_cost,
    enrich_nodes_with_cost,
    get_tier,
)
from replimap.graph.drift import (
    DriftDetector,
    DriftedAttribute,
    DriftResult,
    DriftSeverity,
    DriftStatus,
    detect_drift_from_plan,
    enrich_nodes_with_drift,
)
from replimap.graph.link_classification import (
    LinkType,
    classify_link,
    enrich_links_with_classification,
    get_dependency_links,
    get_traffic_flow_links,
)
from replimap.graph.orphan_detection import (
    OrphanDetector,
    OrphanedResource,
    OrphanReason,
    OrphanSeverity,
    calculate_orphan_costs,
    detect_orphans,
    enrich_nodes_with_orphan_status,
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


class TestLinkClassification:
    """Tests for link classification module."""

    def test_classify_traffic_link(self) -> None:
        """Test classifying traffic links."""
        link_type = classify_link("aws_lb", "aws_lb_target_group")
        assert link_type == LinkType.TRAFFIC

    def test_classify_dependency_link(self) -> None:
        """Test classifying dependency links."""
        link_type = classify_link("aws_instance", "aws_iam_role")
        assert link_type == LinkType.DEPENDENCY

    def test_classify_both_link(self) -> None:
        """Test classifying links that are both traffic and dependency."""
        # SG to SG references are BOTH (security controls traffic)
        link_type = classify_link("aws_security_group", "aws_security_group")
        assert link_type == LinkType.BOTH

    def test_classify_unknown_link(self) -> None:
        """Test classifying unknown resource types."""
        link_type = classify_link("unknown_type", "other_unknown")
        assert link_type == LinkType.DEPENDENCY  # Default

    def test_enrich_links_with_classification(self) -> None:
        """Test enriching links with classification."""
        node_map = {
            "lb-1": {"id": "lb-1", "type": "aws_lb"},
            "tg-1": {"id": "tg-1", "type": "aws_lb_target_group"},
            "i-1": {"id": "i-1", "type": "aws_instance"},
            "role-1": {"id": "role-1", "type": "aws_iam_role"},
        }
        links = [
            {"source": "lb-1", "target": "tg-1"},
            {"source": "i-1", "target": "role-1"},
        ]
        enriched = enrich_links_with_classification(links, node_map)

        assert enriched[0]["link_type"] == "traffic"
        assert enriched[1]["link_type"] == "dependency"

    def test_get_traffic_flow_links(self) -> None:
        """Test filtering traffic flow links."""
        links = [
            {"link_type": "traffic"},
            {"link_type": "dependency"},
            {"link_type": "both"},
        ]
        traffic = get_traffic_flow_links(links)

        assert len(traffic) == 2
        assert all(link["link_type"] in ("traffic", "both") for link in traffic)

    def test_get_dependency_links(self) -> None:
        """Test filtering dependency links."""
        links = [
            {"link_type": "traffic"},
            {"link_type": "dependency"},
            {"link_type": "both"},
        ]
        deps = get_dependency_links(links)

        assert len(deps) == 2
        assert all(link["link_type"] in ("dependency", "both") for link in deps)


class TestSummaryLinks:
    """Tests for summary links module."""

    def test_summary_link_creation(self) -> None:
        """Test creating a summary link."""
        link = SummaryLink(
            id="vpc-1__vpc-2",
            source="vpc-1",
            target="vpc-2",
            link_type="vpc_connection",
            is_summary=True,
            count=5,
        )
        assert link.source == "vpc-1"
        assert link.target == "vpc-2"
        assert link.count == 5

    def test_summary_link_to_dict(self) -> None:
        """Test converting summary link to dict."""
        link = SummaryLink(
            id="vpc-1__vpc-2",
            source="vpc-1",
            target="vpc-2",
            link_type="vpc_connection",
            is_summary=True,
            count=5,
            label="5 connections",
        )
        d = link.to_dict()

        assert d["source"] == "vpc-1"
        assert d["target"] == "vpc-2"
        assert d["count"] == 5
        assert d["label"] == "5 connections"

    def test_summary_link_calculator_empty(self) -> None:
        """Test calculator with no nodes or links."""
        calc = SummaryLinkCalculator([], [])
        summary = calc.calculate_vpc_summary_links()
        assert summary == []

    def test_summary_link_calculator_cross_vpc(self) -> None:
        """Test calculator identifies cross-VPC links."""
        nodes = [
            {"id": "i-1", "type": "aws_instance", "properties": {"vpc_id": "vpc-1"}},
            {"id": "i-2", "type": "aws_instance", "properties": {"vpc_id": "vpc-2"}},
        ]
        links = [
            {
                "source": "i-1",
                "target": "i-2",
                "source_type": "aws_instance",
                "target_type": "aws_instance",
            }
        ]

        calc = SummaryLinkCalculator(nodes, links)
        cross_vpc = calc.get_cross_vpc_links()

        assert len(cross_vpc) == 1

    def test_calculate_summary_links_convenience(self) -> None:
        """Test convenience function."""
        nodes = [
            {"id": "i-1", "type": "aws_instance", "properties": {"vpc_id": "vpc-1"}},
            {"id": "i-2", "type": "aws_instance", "properties": {"vpc_id": "vpc-2"}},
        ]
        links = [{"source": "i-1", "target": "i-2"}]

        summary = calculate_summary_links(nodes, links)
        assert isinstance(summary, list)


class TestToolModes:
    """Tests for tool modes module."""

    def test_tool_mode_enum(self) -> None:
        """Test ToolMode enum values."""
        assert ToolMode.SELECT.value == "select"
        assert ToolMode.TRACE.value == "trace"
        assert ToolMode.BLAST.value == "blast"
        assert ToolMode.COST.value == "cost"

    def test_generate_tool_palette_html(self) -> None:
        """Test HTML generation."""
        html = generate_tool_palette_html()

        assert "<div" in html
        assert "tool-palette" in html
        assert "select" in html.lower()
        assert "trace" in html.lower()
        assert "blast" in html.lower()

    def test_generate_tool_palette_js(self) -> None:
        """Test JavaScript generation."""
        js = generate_tool_palette_js()

        assert "function" in js
        assert "currentTool" in js or "setTool" in js

    def test_generate_tool_palette_css(self) -> None:
        """Test CSS generation."""
        css = generate_tool_palette_css()

        assert ".tool-palette" in css
        assert "position" in css


class TestCostOverlay:
    """Tests for cost overlay module."""

    def test_get_tier_low(self) -> None:
        """Test cost tier classification - low."""
        assert get_tier(10) == CostTier.LOW
        assert get_tier(49) == CostTier.LOW

    def test_get_tier_medium(self) -> None:
        """Test cost tier classification - medium."""
        assert get_tier(50) == CostTier.MEDIUM
        assert get_tier(199) == CostTier.MEDIUM

    def test_get_tier_high(self) -> None:
        """Test cost tier classification - high."""
        assert get_tier(200) == CostTier.HIGH
        assert get_tier(499) == CostTier.HIGH

    def test_get_tier_critical(self) -> None:
        """Test cost tier classification - critical."""
        assert get_tier(500) == CostTier.CRITICAL
        assert get_tier(1000) == CostTier.CRITICAL

    def test_cost_estimate_to_dict(self) -> None:
        """Test CostEstimate serialization."""
        estimate = CostEstimate(
            monthly=100.0,
            tier=CostTier.MEDIUM,
            components={"compute": 80.0, "storage": 20.0},
            confidence="medium",
            notes="Test estimate",
        )
        d = estimate.to_dict()

        assert d["monthly"] == 100.0
        assert d["formatted"] == "$100.00"
        assert d["tier"] == "medium"
        assert "compute" in d["components"]

    def test_cost_calculator_ec2(self) -> None:
        """Test EC2 cost estimation."""
        calc = CostCalculator()
        node = {
            "type": "aws_instance",
            "properties": {"instance_type": "t3.medium"},
        }

        estimate = calc.estimate_resource_cost(node)

        assert estimate is not None
        assert estimate.monthly > 0
        assert "compute" in estimate.components

    def test_cost_calculator_rds(self) -> None:
        """Test RDS cost estimation."""
        calc = CostCalculator()
        node = {
            "type": "aws_db_instance",
            "properties": {
                "instance_class": "db.t3.medium",
                "allocated_storage": 100,
            },
        }

        estimate = calc.estimate_resource_cost(node)

        assert estimate is not None
        assert estimate.monthly > 0

    def test_cost_calculator_lambda(self) -> None:
        """Test Lambda cost estimation."""
        calc = CostCalculator()
        node = {
            "type": "aws_lambda_function",
            "properties": {"memory_size": 256},
        }

        estimate = calc.estimate_resource_cost(node)

        assert estimate is not None
        assert estimate.confidence == "low"  # Lambda costs are variable

    def test_cost_calculator_unknown_type(self) -> None:
        """Test unknown resource type returns None."""
        calc = CostCalculator()
        node = {"type": "unknown_type", "properties": {}}

        estimate = calc.estimate_resource_cost(node)
        assert estimate is None

    def test_enrich_nodes_with_cost(self) -> None:
        """Test enriching nodes with costs."""
        nodes = [
            {
                "id": "1",
                "type": "aws_instance",
                "properties": {"instance_type": "t3.micro"},
            },
            {"id": "2", "type": "unknown_type", "properties": {}},
        ]

        enriched = enrich_nodes_with_cost(nodes)

        assert "cost" in enriched[0]
        assert "cost" not in enriched[1]

    def test_calculate_container_cost(self) -> None:
        """Test container cost calculation."""
        nodes = [
            {
                "id": "1",
                "type": "aws_instance",
                "properties": {"vpc_id": "vpc-1"},
                "cost": {"monthly": 50, "tier": "low"},
            },
            {
                "id": "2",
                "type": "aws_instance",
                "properties": {"vpc_id": "vpc-1"},
                "cost": {"monthly": 100, "tier": "medium"},
            },
        ]

        result = calculate_container_cost(nodes, "vpc-1")

        assert result["total_monthly"] == 150.0
        assert "by_type" in result


class TestBlastRadius:
    """Tests for blast radius module."""

    def test_affected_resource_to_dict(self) -> None:
        """Test AffectedResource serialization."""
        affected = AffectedResource(
            id="i-1",
            name="test-instance",
            resource_type="aws_instance",
            depth=1,
            impact_path=["source", "i-1"],
            criticality=0.8,
        )
        d = affected.to_dict()

        assert d["id"] == "i-1"
        assert d["depth"] == 1
        assert d["criticality"] == 0.8

    def test_blast_radius_calculator_no_dependencies(self) -> None:
        """Test blast radius with no dependencies."""
        nodes = [{"id": "i-1", "type": "aws_instance", "name": "test"}]
        links: list[dict[str, str]] = []

        calc = BlastRadiusCalculator(nodes, links)
        result = calc.calculate("i-1")

        assert len(result.direct) == 0
        assert len(result.indirect) == 0

    def test_blast_radius_calculator_direct_dependency(self) -> None:
        """Test blast radius with direct dependency."""
        nodes = [
            {"id": "db-1", "type": "aws_db_instance", "name": "db"},
            {"id": "i-1", "type": "aws_instance", "name": "instance"},
        ]
        links = [{"source": "i-1", "target": "db-1"}]

        calc = BlastRadiusCalculator(nodes, links)
        result = calc.calculate("db-1")

        assert len(result.direct) == 1
        assert result.direct[0].id == "i-1"

    def test_blast_radius_indirect_dependencies(self) -> None:
        """Test blast radius with indirect dependencies."""
        nodes = [
            {"id": "db-1", "type": "aws_db_instance", "name": "db"},
            {"id": "svc-1", "type": "aws_ecs_service", "name": "service"},
            {"id": "lb-1", "type": "aws_lb", "name": "load-balancer"},
        ]
        links = [
            {"source": "svc-1", "target": "db-1"},
            {"source": "lb-1", "target": "svc-1"},
        ]

        calc = BlastRadiusCalculator(nodes, links)
        result = calc.calculate("db-1")

        assert len(result.direct) == 1  # svc-1
        assert len(result.indirect) == 1  # lb-1

    def test_blast_radius_severity_critical(self) -> None:
        """Test blast radius severity when user-facing affected."""
        nodes = [
            {"id": "db-1", "type": "aws_db_instance", "name": "db"},
            {"id": "lb-1", "type": "aws_lb", "name": "load-balancer"},
        ]
        links = [{"source": "lb-1", "target": "db-1"}]

        calc = BlastRadiusCalculator(nodes, links)
        result = calc.calculate("db-1")

        assert result.severity == ImpactSeverity.CRITICAL

    def test_calculate_blast_radius_convenience(self) -> None:
        """Test convenience function."""
        nodes = [{"id": "i-1", "type": "aws_instance", "name": "test"}]
        links: list[dict[str, str]] = []

        result = calculate_blast_radius(nodes, links, "i-1")

        assert "source" in result
        assert "total_affected" in result

    def test_enrich_nodes_with_blast_radius(self) -> None:
        """Test enriching nodes with blast radius."""
        nodes = [
            {"id": "db-1", "type": "aws_db_instance", "name": "db"},
            {"id": "i-1", "type": "aws_instance", "name": "instance"},
        ]
        links = [{"source": "i-1", "target": "db-1"}]

        enriched = enrich_nodes_with_blast_radius(nodes, links)

        assert "blast_radius" in enriched[0]
        assert enriched[0]["blast_radius"]["direct_count"] == 1

    def test_find_critical_nodes(self) -> None:
        """Test finding critical nodes."""
        nodes = [
            {"id": "db-1", "type": "aws_db_instance", "name": "db"},
            {"id": "i-1", "type": "aws_instance", "name": "instance"},
            {"id": "i-2", "type": "aws_instance", "name": "instance2"},
        ]
        links = [
            {"source": "i-1", "target": "db-1"},
            {"source": "i-2", "target": "db-1"},
        ]

        critical = find_critical_nodes(nodes, links, top_n=2)

        assert len(critical) == 2
        # db-1 should be first since it has highest impact
        assert critical[0]["node"]["id"] == "db-1"


class TestDriftDetection:
    """Tests for drift detection module."""

    def test_drift_status_enum(self) -> None:
        """Test DriftStatus enum values."""
        assert DriftStatus.IN_SYNC.value == "in_sync"
        assert DriftStatus.DRIFTED.value == "drifted"
        assert DriftStatus.DELETED.value == "deleted"
        assert DriftStatus.ORPHANED.value == "orphaned"

    def test_drifted_attribute_to_dict(self) -> None:
        """Test DriftedAttribute serialization."""
        attr = DriftedAttribute(
            attribute="instance_type",
            expected="t3.small",
            actual="t3.medium",
            severity=DriftSeverity.MEDIUM,
        )
        d = attr.to_dict()

        assert d["attribute"] == "instance_type"
        assert d["severity"] == "medium"

    def test_drift_detector_no_drift(self) -> None:
        """Test drift detector with matching states."""
        expected = {"i-1": {"type": "aws_instance", "instance_type": "t3.small"}}
        actual = {"i-1": {"type": "aws_instance", "instance_type": "t3.small"}}

        detector = DriftDetector(expected, actual)
        results = detector.detect_all()

        assert len(results) == 0

    def test_drift_detector_attribute_drift(self) -> None:
        """Test drift detector finds attribute changes."""
        expected = {
            "i-1": {"type": "aws_instance", "instance_type": "t3.small", "name": "test"}
        }
        actual = {
            "i-1": {
                "type": "aws_instance",
                "instance_type": "t3.medium",
                "name": "test",
            }
        }

        detector = DriftDetector(expected, actual)
        results = detector.detect_all()

        assert len(results) == 1
        assert results[0].status == DriftStatus.DRIFTED
        assert len(results[0].drifted_attributes) == 1

    def test_drift_detector_deleted_resource(self) -> None:
        """Test drift detector finds deleted resources."""
        expected = {"i-1": {"type": "aws_instance", "name": "test"}}
        actual: dict[str, dict[str, str]] = {}

        detector = DriftDetector(expected, actual)
        results = detector.detect_all()

        assert len(results) == 1
        assert results[0].status == DriftStatus.DELETED

    def test_drift_detector_orphaned_resource(self) -> None:
        """Test drift detector finds orphaned resources."""
        expected: dict[str, dict[str, str]] = {}
        actual = {"i-1": {"type": "aws_instance", "name": "test"}}

        detector = DriftDetector(expected, actual)
        results = detector.detect_all()

        assert len(results) == 1
        assert results[0].status == DriftStatus.ORPHANED

    def test_drift_severity_security_related(self) -> None:
        """Test drift severity for security-related changes."""
        expected = {"sg-1": {"type": "aws_security_group", "ingress": [], "name": "sg"}}
        actual = {
            "sg-1": {
                "type": "aws_security_group",
                "ingress": [{"port": 22}],
                "name": "sg",
            }
        }

        detector = DriftDetector(expected, actual)
        results = detector.detect_all()

        assert len(results) == 1
        assert results[0].overall_severity == DriftSeverity.HIGH

    def test_detect_drift_from_plan(self) -> None:
        """Test detecting drift from plan changes."""
        changes = [
            {
                "resource_id": "i-1",
                "type": "aws_instance",
                "name": "test",
                "action": "update",
                "before": {"instance_type": "t3.small"},
                "after": {"instance_type": "t3.medium"},
                "changed_attributes": ["instance_type"],
            }
        ]

        results = detect_drift_from_plan(changes)

        assert len(results) == 1
        assert results[0].status == DriftStatus.DRIFTED

    def test_enrich_nodes_with_drift(self) -> None:
        """Test enriching nodes with drift information."""
        nodes = [
            {"id": "i-1", "type": "aws_instance"},
            {"id": "i-2", "type": "aws_instance"},
        ]
        drift_results = [
            DriftResult(
                resource_id="i-1",
                resource_name="test",
                resource_type="aws_instance",
                status=DriftStatus.DRIFTED,
                overall_severity=DriftSeverity.MEDIUM,
            )
        ]

        enriched = enrich_nodes_with_drift(nodes, drift_results)

        assert enriched[0]["drift"]["status"] == "drifted"
        assert enriched[1]["drift"]["status"] == "in_sync"


class TestOrphanDetection:
    """Tests for orphan detection module."""

    def test_orphan_reason_enum(self) -> None:
        """Test OrphanReason enum values."""
        assert OrphanReason.NO_CONNECTIONS.value == "no_connections"
        assert OrphanReason.NO_ATTACHMENTS.value == "no_attachments"

    def test_orphaned_resource_to_dict(self) -> None:
        """Test OrphanedResource serialization."""
        orphan = OrphanedResource(
            resource_id="sg-1",
            resource_name="test-sg",
            resource_type="aws_security_group",
            reason=OrphanReason.NO_ATTACHMENTS,
            severity=OrphanSeverity.LOW,
            estimated_monthly_cost=0.0,
            message="Not attached",
            recommendation="Remove if unused",
        )
        d = orphan.to_dict()

        assert d["id"] == "sg-1"
        assert d["reason"] == "no_attachments"
        assert d["severity"] == "low"

    def test_orphan_detector_no_orphans(self) -> None:
        """Test orphan detector with connected resources."""
        nodes = [
            {"id": "i-1", "type": "aws_instance"},
            {"id": "sg-1", "type": "aws_security_group"},
        ]
        # i-1 connects to sg-1, so sg-1 has incoming connection
        links = [{"source": "i-1", "target": "sg-1"}]

        detector = OrphanDetector(nodes, links)
        orphans = detector.detect_all()

        # sg-1 has incoming from i-1, so it's not orphaned
        sg_orphans = [o for o in orphans if o.resource_id == "sg-1"]
        assert len(sg_orphans) == 0

    def test_orphan_detector_isolated_resource(self) -> None:
        """Test orphan detector finds isolated resources."""
        nodes = [
            {"id": "i-1", "type": "aws_instance"},
            {"id": "i-2", "type": "aws_instance"},
        ]
        links = [{"source": "i-1", "target": "i-2"}]

        detector = OrphanDetector(nodes, links)
        orphans = detector.detect_all()

        # i-1 has only outgoing, no incoming - shouldn't be orphan for instance
        # i-2 has only incoming, no outgoing
        # Should not detect these as orphans since instances can be standalone
        assert all(
            o.reason != OrphanReason.NO_CONNECTIONS
            for o in orphans
            if o.resource_id in ("i-1", "i-2")
        )

    def test_orphan_detector_unattached_security_group(self) -> None:
        """Test orphan detector finds unattached security groups."""
        nodes = [{"id": "sg-1", "type": "aws_security_group"}]
        links: list[dict[str, str]] = []

        detector = OrphanDetector(nodes, links)
        orphans = detector.detect_all()

        sg_orphans = [o for o in orphans if o.resource_id == "sg-1"]
        assert len(sg_orphans) == 1
        assert sg_orphans[0].reason in (
            OrphanReason.NO_CONNECTIONS,
            OrphanReason.NO_ATTACHMENTS,
        )

    def test_orphan_detector_skips_summary_nodes(self) -> None:
        """Test orphan detector skips summary nodes."""
        nodes = [{"id": "summary-1", "type": "summary", "is_summary": True}]
        links: list[dict[str, str]] = []

        detector = OrphanDetector(nodes, links)
        orphans = detector.detect_all()

        assert len(orphans) == 0

    def test_detect_orphans_convenience(self) -> None:
        """Test convenience function."""
        nodes = [{"id": "sg-1", "type": "aws_security_group"}]
        links: list[dict[str, str]] = []

        orphans = detect_orphans(nodes, links)

        assert isinstance(orphans, list)
        assert all("id" in o for o in orphans)

    def test_enrich_nodes_with_orphan_status(self) -> None:
        """Test enriching nodes with orphan status."""
        nodes = [
            {"id": "sg-1", "type": "aws_security_group"},
            {"id": "i-1", "type": "aws_instance"},
        ]
        links = [{"source": "i-1", "target": "sg-1"}]

        enriched = enrich_nodes_with_orphan_status(nodes, links)

        assert "is_orphan" in enriched[0]
        assert "is_orphan" in enriched[1]

    def test_calculate_orphan_costs(self) -> None:
        """Test calculating orphan costs."""
        orphans = [
            OrphanedResource(
                resource_id="vol-1",
                resource_name="vol",
                resource_type="aws_ebs_volume",
                reason=OrphanReason.NO_ATTACHMENTS,
                severity=OrphanSeverity.MEDIUM,
                estimated_monthly_cost=10.0,
                message="Unattached",
                recommendation="Delete",
            ),
            OrphanedResource(
                resource_id="eip-1",
                resource_name="eip",
                resource_type="aws_eip",
                reason=OrphanReason.NO_ATTACHMENTS,
                severity=OrphanSeverity.MEDIUM,
                estimated_monthly_cost=3.60,
                message="Unassociated",
                recommendation="Release",
            ),
        ]

        costs = calculate_orphan_costs(orphans)

        assert costs["total_monthly_savings"] == 13.60
        assert costs["annual_savings"] == 163.20
        assert costs["orphan_count"] == 2
