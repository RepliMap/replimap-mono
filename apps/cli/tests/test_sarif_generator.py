"""
Comprehensive tests for the Robust SARIF Generator.

Tests cover:
- SARIFRule dataclass and to_dict
- SARIFLocation with hybrid locations
- SARIFResult with fingerprinting
- MarkdownBuilder helper methods
- RuleRegistry with predefined and fallback rules
- SARIFGenerator for drift, audit, and analysis findings
"""

from __future__ import annotations

import json

from replimap.core.drift.detector import (
    AttributeChange,
    DriftFinding,
    DriftReport,
    DriftSeverity,
    DriftType,
)
from replimap.core.formatters.sarif import (
    MarkdownBuilder,
    RuleRegistry,
    SARIFGenerator,
    SARIFLevel,
    SARIFLocation,
    SARIFResult,
    SARIFRule,
)

# ============================================================
# SARIFLevel Tests
# ============================================================


class TestSARIFLevel:
    """Tests for SARIFLevel enum."""

    def test_level_values(self):
        """Test that levels have correct string values."""
        assert SARIFLevel.ERROR.value == "error"
        assert SARIFLevel.WARNING.value == "warning"
        assert SARIFLevel.NOTE.value == "note"
        assert SARIFLevel.NONE.value == "none"


# ============================================================
# SARIFRule Tests
# ============================================================


class TestSARIFRule:
    """Tests for SARIFRule dataclass."""

    def test_basic_rule_to_dict(self):
        """Test basic rule conversion to SARIF format."""
        rule = SARIFRule(
            id="TEST001",
            name="TestRule",
            short_description="Short desc",
            full_description="Full description here",
        )

        result = rule.to_dict()

        assert result["id"] == "TEST001"
        assert result["name"] == "TestRule"
        assert result["shortDescription"]["text"] == "Short desc"
        assert result["fullDescription"]["text"] == "Full description here"
        assert result["helpUri"] == "https://replimap.dev/docs"
        assert result["defaultConfiguration"]["level"] == "warning"
        assert "security-severity" in result["properties"]

    def test_rule_with_cwe_ids(self):
        """Test rule with CWE relationships."""
        rule = SARIFRule(
            id="SEC001",
            name="SecurityRule",
            short_description="Security issue",
            full_description="Details",
            cwe_ids=["CWE-284", "CWE-200"],
        )

        result = rule.to_dict()

        assert "relationships" in result
        assert len(result["relationships"]) == 2
        assert result["relationships"][0]["target"]["id"] == "CWE-284"
        assert result["relationships"][0]["target"]["toolComponent"]["name"] == "CWE"

    def test_rule_with_help_text(self):
        """Test rule with help markdown."""
        help_md = "## Help\n\nThis is help text."
        rule = SARIFRule(
            id="HELP001",
            name="HelpRule",
            short_description="Has help",
            full_description="Details",
            help_text=help_md,
        )

        result = rule.to_dict()

        assert "help" in result
        assert result["help"]["text"] == help_md
        assert result["help"]["markdown"] == help_md

    def test_rule_custom_severity(self):
        """Test rule with custom security severity."""
        rule = SARIFRule(
            id="CRIT001",
            name="CriticalRule",
            short_description="Critical issue",
            full_description="Details",
            default_level=SARIFLevel.ERROR,
            security_severity=9.5,
        )

        result = rule.to_dict()

        assert result["defaultConfiguration"]["level"] == "error"
        assert result["properties"]["security-severity"] == "9.5"

    def test_rule_custom_tags(self):
        """Test rule with custom tags."""
        rule = SARIFRule(
            id="TAG001",
            name="TaggedRule",
            short_description="Tagged",
            full_description="Details",
            tags=["security", "iam", "custom"],
        )

        result = rule.to_dict()

        assert result["properties"]["tags"] == ["security", "iam", "custom"]


# ============================================================
# SARIFLocation Tests
# ============================================================


class TestSARIFLocation:
    """Tests for SARIFLocation dataclass."""

    def test_physical_location_only(self):
        """Test location with only physical (file) location."""
        loc = SARIFLocation(
            artifact_uri="terraform.tfstate",
            start_line=10,
            start_column=5,
        )

        result = loc.to_dict()

        assert "physicalLocation" in result
        assert (
            result["physicalLocation"]["artifactLocation"]["uri"] == "terraform.tfstate"
        )
        assert result["physicalLocation"]["region"]["startLine"] == 10
        assert result["physicalLocation"]["region"]["startColumn"] == 5

    def test_logical_location_only(self):
        """Test location with only logical location."""
        loc = SARIFLocation(
            logical_name="web-server",
            logical_kind="resource",
            fully_qualified_name="aws_instance.web-server",
        )

        result = loc.to_dict()

        assert "logicalLocations" in result
        assert result["logicalLocations"][0]["name"] == "web-server"
        assert result["logicalLocations"][0]["kind"] == "resource"
        assert (
            result["logicalLocations"][0]["fullyQualifiedName"]
            == "aws_instance.web-server"
        )

    def test_cloud_resource_location(self):
        """Test location with cloud resource info."""
        loc = SARIFLocation(
            resource_id="i-1234567890abcdef0",
            resource_arn="arn:aws:ec2:us-east-1:123456789:instance/i-1234567890abcdef0",
            region="us-east-1",
            cloud_provider="aws",
        )

        result = loc.to_dict()

        assert "logicalLocations" in result
        cloud_logical = result["logicalLocations"][0]
        assert cloud_logical["name"] == "i-1234567890abcdef0"
        assert cloud_logical["kind"] == "cloudResource"

        assert "properties" in result
        assert result["properties"]["cloudProvider"] == "aws"
        assert result["properties"]["resourceId"] == "i-1234567890abcdef0"
        assert result["properties"]["region"] == "us-east-1"

    def test_hybrid_location(self):
        """Test location with both physical and logical."""
        loc = SARIFLocation(
            artifact_uri="terraform.tfstate",
            start_line=42,
            logical_name="web-instance",
            fully_qualified_name="module.vpc.aws_instance.web",
            resource_id="i-abc123",
        )

        result = loc.to_dict()

        assert "physicalLocation" in result
        assert "logicalLocations" in result
        assert len(result["logicalLocations"]) == 2  # resource + cloud

    def test_empty_location(self):
        """Test empty location returns empty dict."""
        loc = SARIFLocation()
        result = loc.to_dict()
        assert result == {}


# ============================================================
# SARIFResult Tests
# ============================================================


class TestSARIFResult:
    """Tests for SARIFResult dataclass."""

    def test_fingerprint_generation(self):
        """Test stable fingerprint generation."""
        result = SARIFResult(
            rule_id="DRIFT001",
            level=SARIFLevel.WARNING,
            message_text="Test message",
            fingerprint_components=["i-1234", "unmanaged"],
        )

        fp = result.fingerprint()

        # Should be 32 char hex string
        assert len(fp) == 32
        assert all(c in "0123456789abcdef" for c in fp)

        # Same components = same fingerprint
        result2 = SARIFResult(
            rule_id="DRIFT001",
            level=SARIFLevel.ERROR,  # Different level, same fingerprint
            message_text="Different message",
            fingerprint_components=["i-1234", "unmanaged"],
        )
        assert result.fingerprint() == result2.fingerprint()

    def test_fingerprint_differs_for_different_components(self):
        """Test that different components produce different fingerprints."""
        result1 = SARIFResult(
            rule_id="DRIFT001",
            level=SARIFLevel.WARNING,
            message_text="Test",
            fingerprint_components=["i-1234"],
        )

        result2 = SARIFResult(
            rule_id="DRIFT001",
            level=SARIFLevel.WARNING,
            message_text="Test",
            fingerprint_components=["i-5678"],
        )

        assert result1.fingerprint() != result2.fingerprint()

    def test_result_to_dict_basic(self):
        """Test basic result conversion."""
        result = SARIFResult(
            rule_id="TEST001",
            level=SARIFLevel.ERROR,
            message_text="Error occurred",
        )

        output = result.to_dict()

        assert output["ruleId"] == "TEST001"
        assert output["level"] == "error"
        assert output["message"]["text"] == "Error occurred"
        assert "fingerprints" in output
        assert "replimap/v1" in output["fingerprints"]

    def test_result_with_markdown_message(self):
        """Test result with markdown message."""
        result = SARIFResult(
            rule_id="MD001",
            level=SARIFLevel.WARNING,
            message_text="Plain text",
            message_markdown="**Bold** text",
        )

        output = result.to_dict()

        assert output["message"]["text"] == "Plain text"
        assert output["message"]["markdown"] == "**Bold** text"

    def test_result_with_locations(self):
        """Test result with locations."""
        loc = SARIFLocation(
            artifact_uri="test.tf",
            logical_name="resource",
        )

        result = SARIFResult(
            rule_id="LOC001",
            level=SARIFLevel.NOTE,
            message_text="Has location",
            locations=[loc],
        )

        output = result.to_dict()

        assert "locations" in output
        assert len(output["locations"]) == 1

    def test_result_with_fixes(self):
        """Test result with fix suggestions."""
        result = SARIFResult(
            rule_id="FIX001",
            level=SARIFLevel.WARNING,
            message_text="Fixable",
            fixes=[{"description": {"text": "Run terraform import"}}],
        )

        output = result.to_dict()

        assert "fixes" in output
        assert output["fixes"][0]["description"]["text"] == "Run terraform import"

    def test_result_with_code_flows(self):
        """Test result with code flows (attack paths)."""
        result = SARIFResult(
            rule_id="PATH001",
            level=SARIFLevel.ERROR,
            message_text="Attack path",
            code_flows=[{"threadFlows": [{"locations": []}]}],
        )

        output = result.to_dict()

        assert "codeFlows" in output

    def test_result_with_related_locations(self):
        """Test result with related locations."""
        related = [
            SARIFLocation(resource_id="r1"),
            SARIFLocation(resource_id="r2"),
        ]

        result = SARIFResult(
            rule_id="REL001",
            level=SARIFLevel.NOTE,
            message_text="Has related",
            related_locations=related,
        )

        output = result.to_dict()

        assert "relatedLocations" in output
        assert len(output["relatedLocations"]) == 2
        assert output["relatedLocations"][0]["id"] == 0
        assert output["relatedLocations"][1]["id"] == 1


# ============================================================
# MarkdownBuilder Tests
# ============================================================


class TestMarkdownBuilder:
    """Tests for MarkdownBuilder helper."""

    def test_header(self):
        """Test header generation."""
        assert MarkdownBuilder.header("Title", 1) == "# Title\n\n"
        assert MarkdownBuilder.header("Section", 2) == "## Section\n\n"
        assert MarkdownBuilder.header("Subsection", 3) == "### Subsection\n\n"

    def test_paragraph(self):
        """Test paragraph generation."""
        assert MarkdownBuilder.paragraph("Text here") == "Text here\n\n"

    def test_bullet_list(self):
        """Test bullet list generation."""
        result = MarkdownBuilder.bullet_list(["Item 1", "Item 2"])
        assert "- Item 1\n" in result
        assert "- Item 2" in result

    def test_numbered_list(self):
        """Test numbered list generation."""
        result = MarkdownBuilder.numbered_list(["First", "Second"])
        assert "1. First\n" in result
        assert "2. Second" in result

    def test_code_block(self):
        """Test fenced code block."""
        result = MarkdownBuilder.code_block("print('hi')", "python")
        assert result == "```python\nprint('hi')\n```\n\n"

    def test_inline_code(self):
        """Test inline code."""
        assert MarkdownBuilder.inline_code("variable") == "`variable`"

    def test_bold(self):
        """Test bold text."""
        assert MarkdownBuilder.bold("important") == "**important**"

    def test_italic(self):
        """Test italic text."""
        assert MarkdownBuilder.italic("emphasis") == "*emphasis*"

    def test_link(self):
        """Test markdown link."""
        result = MarkdownBuilder.link("Click here", "https://example.com")
        assert result == "[Click here](https://example.com)"

    def test_table(self):
        """Test markdown table."""
        headers = ["Name", "Value"]
        rows = [["foo", "1"], ["bar", "2"]]

        result = MarkdownBuilder.table(headers, rows)

        assert "| Name | Value |" in result
        assert "| --- | --- |" in result
        assert "| foo | 1 |" in result
        assert "| bar | 2 |" in result

    def test_collapsible(self):
        """Test collapsible section."""
        result = MarkdownBuilder.collapsible("Details", "Hidden content")

        assert "<details>" in result
        assert "<summary>Details</summary>" in result
        assert "Hidden content" in result
        assert "</details>" in result

    def test_badge(self):
        """Test shield.io badge."""
        result = MarkdownBuilder.badge("status", "active", "green")
        assert "shields.io" in result
        assert "status-active-green" in result

    def test_severity_badge(self):
        """Test severity badge with correct colors."""
        critical = MarkdownBuilder.severity_badge("critical")
        assert "red" in critical

        high = MarkdownBuilder.severity_badge("high")
        assert "orange" in high

        medium = MarkdownBuilder.severity_badge("medium")
        assert "yellow" in medium

        low = MarkdownBuilder.severity_badge("low")
        assert "blue" in low

        info = MarkdownBuilder.severity_badge("info")
        assert "gray" in info


# ============================================================
# RuleRegistry Tests
# ============================================================


class TestRuleRegistry:
    """Tests for RuleRegistry."""

    def test_predefined_rules_exist(self):
        """Test that predefined rules are loaded."""
        registry = RuleRegistry()

        # Check some audit rules
        assert "AUDIT001" in registry.PREDEFINED_RULES
        assert "AUDIT003" in registry.PREDEFINED_RULES

        # Check drift rules
        assert "DRIFT001" in registry.PREDEFINED_RULES
        assert "DRIFT004" in registry.PREDEFINED_RULES

        # Check analysis rules
        assert "ANALYSIS001" in registry.PREDEFINED_RULES
        assert "ANALYSIS002" in registry.PREDEFINED_RULES

    def test_get_predefined_rule(self):
        """Test getting a predefined rule."""
        registry = RuleRegistry()

        rule = registry.get_rule("DRIFT001")

        assert rule.id == "DRIFT001"
        assert rule.name == "UnmanagedResource"
        assert "unmanaged" in rule.short_description.lower()

    def test_fallback_rule_creation(self):
        """Test fallback rule is created for unknown IDs."""
        registry = RuleRegistry()

        rule = registry.get_rule("UNKNOWN_RULE_123")

        assert rule.id == "UNKNOWN_RULE_123"
        assert rule.name  # Should have some name
        assert rule.short_description  # Should have description

    def test_fallback_rule_parses_hints(self):
        """Test fallback rule uses hints from rule ID."""
        registry = RuleRegistry()

        # Security-related ID should get higher severity
        sec_rule = registry.get_rule("security_iam_issue")
        assert sec_rule.default_level == SARIFLevel.ERROR
        assert sec_rule.security_severity == 7.0
        assert "security" in sec_rule.tags

    def test_used_rules_tracking(self):
        """Test that used rules are tracked."""
        registry = RuleRegistry()

        registry.get_rule("DRIFT001")
        registry.get_rule("AUDIT001")
        registry.get_rule("DRIFT001")  # Duplicate

        used = registry.get_used_rules()

        assert len(used) == 2
        rule_ids = [r.id for r in used]
        assert "AUDIT001" in rule_ids
        assert "DRIFT001" in rule_ids

    def test_register_custom_rule(self):
        """Test registering a custom rule."""
        registry = RuleRegistry()

        custom = SARIFRule(
            id="CUSTOM001",
            name="CustomRule",
            short_description="My custom rule",
            full_description="Details",
        )

        registry.register_rule(custom)
        retrieved = registry.get_rule("CUSTOM001")

        assert retrieved.id == "CUSTOM001"
        assert retrieved.name == "CustomRule"


# ============================================================
# SARIFGenerator Tests
# ============================================================


class TestSARIFGenerator:
    """Tests for SARIFGenerator."""

    def test_sarif_structure(self):
        """Test basic SARIF document structure."""
        generator = SARIFGenerator()

        report = DriftReport(
            findings=[],
            scan_timestamp="2024-01-01T00:00:00Z",
            state_file_path="terraform.tfstate",
        )

        sarif = generator.from_drift_report(report)

        assert "$schema" in sarif
        assert sarif["version"] == "2.1.0"
        assert "runs" in sarif
        assert len(sarif["runs"]) == 1
        assert "tool" in sarif["runs"][0]
        assert "results" in sarif["runs"][0]
        assert "invocations" in sarif["runs"][0]

    def test_tool_info(self):
        """Test tool information in SARIF."""
        generator = SARIFGenerator()

        report = DriftReport(findings=[], scan_timestamp="2024-01-01T00:00:00Z")
        sarif = generator.from_drift_report(report)

        tool = sarif["runs"][0]["tool"]["driver"]

        assert tool["name"] == "replimap"
        assert "version" in tool
        assert "informationUri" in tool

    def test_unmanaged_resource_finding(self):
        """Test SARIF output for unmanaged resource."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-unmanaged123",
            resource_type="aws_instance",
            resource_name="rogue-server",
            drift_type=DriftType.UNMANAGED,
            severity=DriftSeverity.MEDIUM,
        )

        report = DriftReport(
            findings=[finding],
            scan_timestamp="2024-01-01T00:00:00Z",
            state_file_path="terraform.tfstate",
        )

        sarif = generator.from_drift_report(report)

        results = sarif["runs"][0]["results"]
        assert len(results) == 1

        result = results[0]
        assert result["ruleId"] == "DRIFT001"
        assert result["level"] == "warning"
        assert "unmanaged" in result["message"]["text"].lower()
        assert "fingerprints" in result

    def test_missing_resource_finding(self):
        """Test SARIF output for missing resource."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-deleted123",
            resource_type="aws_instance",
            resource_name="deleted-server",
            drift_type=DriftType.MISSING,
            severity=DriftSeverity.HIGH,
        )

        report = DriftReport(
            findings=[finding],
            scan_timestamp="2024-01-01T00:00:00Z",
        )

        sarif = generator.from_drift_report(report)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "DRIFT002"
        assert result["level"] == "error"

    def test_configuration_drift_finding(self):
        """Test SARIF output for configuration drift."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-drifted123",
            resource_type="aws_instance",
            resource_name="drifted-server",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange(
                    field="instance_type",
                    expected="t2.micro",
                    actual="t2.large",
                    severity=DriftSeverity.HIGH,
                )
            ],
        )

        report = DriftReport(
            findings=[finding],
            scan_timestamp="2024-01-01T00:00:00Z",
        )

        sarif = generator.from_drift_report(report)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "DRIFT003"
        assert "instance_type" in result["message"]["text"]

    def test_security_drift_finding(self):
        """Test SARIF output for security-critical drift."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="sg-sec123",
            resource_type="aws_security_group",
            resource_name="critical-sg",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange(
                    field="ingress",
                    expected=[],
                    actual=[{"from_port": 22, "cidr_blocks": ["0.0.0.0/0"]}],
                    severity=DriftSeverity.CRITICAL,
                )
            ],
        )

        report = DriftReport(
            findings=[finding],
            scan_timestamp="2024-01-01T00:00:00Z",
        )

        sarif = generator.from_drift_report(report)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "DRIFT004"  # Security drift
        assert result["level"] == "error"

    def test_result_has_fixes(self):
        """Test that results include fix suggestions."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=DriftType.UNMANAGED,
        )

        report = DriftReport(findings=[finding], scan_timestamp="2024-01-01T00:00:00Z")
        sarif = generator.from_drift_report(report)

        result = sarif["runs"][0]["results"][0]
        assert "fixes" in result
        assert len(result["fixes"]) > 0
        assert "description" in result["fixes"][0]

    def test_result_has_markdown(self):
        """Test that results include markdown message."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange("field1", "a", "b", DriftSeverity.MEDIUM),
            ],
        )

        report = DriftReport(findings=[finding], scan_timestamp="2024-01-01T00:00:00Z")
        sarif = generator.from_drift_report(report)

        result = sarif["runs"][0]["results"][0]
        assert "markdown" in result["message"]

    def test_rules_included_in_output(self):
        """Test that used rules are included in output."""
        generator = SARIFGenerator()

        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=DriftType.UNMANAGED,
        )

        report = DriftReport(findings=[finding], scan_timestamp="2024-01-01T00:00:00Z")
        sarif = generator.from_drift_report(report)

        rules = sarif["runs"][0]["tool"]["driver"]["rules"]
        assert len(rules) >= 1

        rule_ids = [r["id"] for r in rules]
        assert "DRIFT001" in rule_ids

    def test_from_audit_findings(self):
        """Test converting audit findings to SARIF."""
        generator = SARIFGenerator()

        findings = [
            {
                "rule_id": "AUDIT001",
                "severity": "high",
                "resource_id": "bucket-123",
                "resource_arn": "arn:aws:s3:::bucket-123",
                "message": "S3 bucket is publicly accessible",
            },
            {
                "rule_id": "AUDIT002",
                "severity": "medium",
                "resource_id": "rds-123",
                "message": "RDS instance is not encrypted",
            },
        ]

        sarif = generator.from_audit_findings(findings)

        results = sarif["runs"][0]["results"]
        assert len(results) == 2

        assert results[0]["ruleId"] == "AUDIT001"
        assert results[0]["level"] == "error"
        assert results[1]["ruleId"] == "AUDIT002"
        assert results[1]["level"] == "warning"

    def test_from_analysis_results_attack_paths(self):
        """Test converting attack paths to SARIF."""
        generator = SARIFGenerator()

        analysis = {
            "attack_paths": [
                {
                    "path_id": "path-1",
                    "hops": [
                        {
                            "resource_id": "igw-123",
                            "resource_type": "aws_internet_gateway",
                            "resource_name": "main-igw",
                        },
                        {
                            "resource_id": "sg-123",
                            "resource_type": "aws_security_group",
                            "resource_name": "open-sg",
                        },
                        {
                            "resource_id": "i-123",
                            "resource_type": "aws_instance",
                            "resource_name": "db-server",
                        },
                    ],
                    "risk_score": 8.5,
                }
            ]
        }

        sarif = generator.from_analysis_results(analysis)

        results = sarif["runs"][0]["results"]
        assert len(results) == 1

        result = results[0]
        assert result["ruleId"] == "ANALYSIS001"
        assert result["level"] == "error"
        assert "codeFlows" in result
        assert "relatedLocations" in result

    def test_from_analysis_results_blast_radius(self):
        """Test converting blast radius findings to SARIF."""
        generator = SARIFGenerator()

        analysis = {
            "high_blast_radius": [
                {
                    "resource_id": "vpc-123",
                    "resource_type": "aws_vpc",
                    "resource_name": "main-vpc",
                    "connection_count": 150,
                }
            ]
        }

        sarif = generator.from_analysis_results(analysis)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "ANALYSIS002"
        assert "150" in result["message"]["text"]

    def test_from_analysis_results_orphans(self):
        """Test converting orphaned resources to SARIF."""
        generator = SARIFGenerator()

        analysis = {
            "orphaned_resources": [
                {
                    "resource_id": "sg-orphan",
                    "resource_type": "aws_security_group",
                    "resource_name": "unused-sg",
                }
            ]
        }

        sarif = generator.from_analysis_results(analysis)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "ANALYSIS003"
        assert result["level"] == "note"

    def test_from_analysis_results_circular_deps(self):
        """Test converting circular dependencies to SARIF."""
        generator = SARIFGenerator()

        analysis = {
            "circular_dependencies": [
                {
                    "cycle_id": "cycle-1",
                    "resources": [
                        {"resource_id": "r1", "resource_name": "resource-a"},
                        {"resource_id": "r2", "resource_name": "resource-b"},
                        {"resource_id": "r3", "resource_name": "resource-c"},
                    ],
                }
            ]
        }

        sarif = generator.from_analysis_results(analysis)

        result = sarif["runs"][0]["results"][0]
        assert result["ruleId"] == "ANALYSIS004"
        assert "resource-a" in result["message"]["text"]
        assert "resource-b" in result["message"]["text"]
        assert "resource-c" in result["message"]["text"]

    def test_legacy_class_method(self):
        """Test legacy class method for backwards compatibility."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=DriftType.UNMANAGED,
        )

        report = DriftReport(findings=[finding], scan_timestamp="2024-01-01T00:00:00Z")

        # Should work without instantiating
        sarif = SARIFGenerator.from_drift_report_legacy(report)

        assert "$schema" in sarif
        assert len(sarif["runs"][0]["results"]) == 1


# ============================================================
# Integration Tests
# ============================================================


class TestSARIFIntegration:
    """Integration tests for full SARIF workflow."""

    def test_full_drift_report_workflow(self):
        """Test complete drift report to SARIF workflow."""
        # Create a realistic drift report
        findings = [
            DriftFinding(
                resource_id="i-unmanaged",
                resource_type="aws_instance",
                resource_name="ghost-server",
                drift_type=DriftType.UNMANAGED,
            ),
            DriftFinding(
                resource_id="bucket-deleted",
                resource_type="aws_s3_bucket",
                resource_name="deleted-bucket",
                drift_type=DriftType.MISSING,
                terraform_address="module.storage.aws_s3_bucket.main",
            ),
            DriftFinding(
                resource_id="sg-modified",
                resource_type="aws_security_group",
                resource_name="web-sg",
                drift_type=DriftType.DRIFTED,
                terraform_address="aws_security_group.web",
                changes=[
                    AttributeChange(
                        "ingress", [], [{"port": 22}], DriftSeverity.CRITICAL
                    ),
                    AttributeChange("description", "Old", "New", DriftSeverity.LOW),
                ],
            ),
        ]

        report = DriftReport(
            findings=findings,
            scan_timestamp="2024-01-15T10:30:00Z",
            state_file_path="/path/to/terraform.tfstate",
        )

        # Convert to SARIF
        generator = SARIFGenerator()
        sarif = generator.from_drift_report(report)

        # Validate structure
        assert sarif["version"] == "2.1.0"
        assert len(sarif["runs"]) == 1

        run = sarif["runs"][0]

        # Check results
        assert len(run["results"]) == 3

        # Check rules are included
        rules = run["tool"]["driver"]["rules"]
        rule_ids = [r["id"] for r in rules]
        assert "DRIFT001" in rule_ids  # Unmanaged
        assert "DRIFT002" in rule_ids  # Missing
        assert "DRIFT004" in rule_ids  # Security drift (critical change)

        # Check fingerprints are unique
        fingerprints = [r["fingerprints"]["replimap/v1"] for r in run["results"]]
        assert len(fingerprints) == len(set(fingerprints))  # All unique

    def test_sarif_json_serializable(self):
        """Test that SARIF output is JSON serializable."""
        finding = DriftFinding(
            resource_id="i-123",
            resource_type="aws_instance",
            resource_name="test",
            drift_type=DriftType.DRIFTED,
            changes=[
                AttributeChange("tags", {"a": 1}, {"b": 2}, DriftSeverity.LOW),
            ],
        )

        report = DriftReport(findings=[finding], scan_timestamp="2024-01-01T00:00:00Z")
        generator = SARIFGenerator()
        sarif = generator.from_drift_report(report)

        # Should not raise
        json_str = json.dumps(sarif, indent=2)
        assert len(json_str) > 0

        # Should be valid JSON
        parsed = json.loads(json_str)
        assert parsed["version"] == "2.1.0"
