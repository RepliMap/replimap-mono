"""
Tests for the Compliance Rules Engine.

Tests cover:
- Condition evaluation
- Rule matching and evaluation
- YAML parsing
- Engine evaluation against graph
- Report generation
"""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from replimap.compliance import (
    ComplianceReporter,
    ComplianceResult,
    ComplianceResults,
    Condition,
    ConditionOperator,
    Rule,
    RuleEngine,
    RuleFinding,
    Severity,
    load_rules_from_dict,
    load_rules_from_yaml,
)
from replimap.compliance.parser import get_builtin_rules
from replimap.core import GraphEngine
from replimap.core.models import ResourceNode, ResourceType


class TestSeverity:
    """Tests for Severity enum."""

    def test_severity_values(self) -> None:
        """Should have correct string values."""
        assert str(Severity.CRITICAL) == "critical"
        assert str(Severity.HIGH) == "high"
        assert str(Severity.MEDIUM) == "medium"
        assert str(Severity.LOW) == "low"
        assert str(Severity.INFO) == "info"

    def test_severity_weights(self) -> None:
        """Should have correct weights for scoring."""
        assert Severity.CRITICAL.weight == 10
        assert Severity.HIGH.weight == 5
        assert Severity.MEDIUM.weight == 3
        assert Severity.LOW.weight == 1
        assert Severity.INFO.weight == 0


class TestConditionOperator:
    """Tests for ConditionOperator enum."""

    def test_all_operators_exist(self) -> None:
        """Should have all expected operators."""
        operators = [
            "equals", "not_equals", "contains", "not_contains",
            "starts_with", "ends_with", "matches", "exists",
            "not_exists", "in", "not_in", "greater_than",
            "less_than", "greater_equal", "less_equal",
        ]
        for op in operators:
            assert ConditionOperator(op) is not None


class TestCondition:
    """Tests for Condition class."""

    def test_equals_operator(self) -> None:
        """Should evaluate equals correctly."""
        condition = Condition(
            field="config.encrypted",
            operator=ConditionOperator.EQUALS,
            value=True,
        )

        # Mock resource
        resource = {"config": {"encrypted": True}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"encrypted": False}}
        assert condition.evaluate(resource) is False

    def test_not_equals_operator(self) -> None:
        """Should evaluate not_equals correctly."""
        condition = Condition(
            field="config.status",
            operator=ConditionOperator.NOT_EQUALS,
            value="deleted",
        )

        resource = {"config": {"status": "active"}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"status": "deleted"}}
        assert condition.evaluate(resource) is False

    def test_contains_operator_string(self) -> None:
        """Should evaluate contains for strings."""
        condition = Condition(
            field="config.name",
            operator=ConditionOperator.CONTAINS,
            value="prod",
        )

        resource = {"config": {"name": "my-prod-server"}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"name": "my-dev-server"}}
        assert condition.evaluate(resource) is False

    def test_contains_operator_list(self) -> None:
        """Should evaluate contains for lists."""
        condition = Condition(
            field="config.tags",
            operator=ConditionOperator.CONTAINS,
            value="security",
        )

        resource = {"config": {"tags": ["security", "compliance"]}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"tags": ["development"]}}
        assert condition.evaluate(resource) is False

    def test_exists_operator(self) -> None:
        """Should evaluate exists correctly."""
        condition = Condition(
            field="config.encryption",
            operator=ConditionOperator.EXISTS,
        )

        resource = {"config": {"encryption": {"enabled": True}}}
        assert condition.evaluate(resource) is True

        resource = {"config": {}}
        assert condition.evaluate(resource) is False

        resource = {"config": {"encryption": None}}
        assert condition.evaluate(resource) is False

        resource = {"config": {"encryption": ""}}
        assert condition.evaluate(resource) is False

    def test_not_exists_operator(self) -> None:
        """Should evaluate not_exists correctly."""
        condition = Condition(
            field="config.password",
            operator=ConditionOperator.NOT_EXISTS,
        )

        resource = {"config": {}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"password": "secret"}}
        assert condition.evaluate(resource) is False

    def test_matches_operator(self) -> None:
        """Should evaluate regex matches."""
        condition = Condition(
            field="config.bucket_name",
            operator=ConditionOperator.MATCHES,
            value=r"^[a-z][a-z0-9-]*$",
        )

        resource = {"config": {"bucket_name": "my-bucket-123"}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"bucket_name": "123-invalid"}}
        assert condition.evaluate(resource) is False

    def test_in_operator(self) -> None:
        """Should evaluate in correctly."""
        condition = Condition(
            field="config.instance_type",
            operator=ConditionOperator.IN,
            value=["t3.micro", "t3.small", "t3.medium"],
        )

        resource = {"config": {"instance_type": "t3.small"}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"instance_type": "m5.large"}}
        assert condition.evaluate(resource) is False

    def test_greater_than_operator(self) -> None:
        """Should evaluate numeric comparisons."""
        condition = Condition(
            field="config.storage_size",
            operator=ConditionOperator.GREATER_THAN,
            value=100,
        )

        resource = {"config": {"storage_size": 200}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"storage_size": 50}}
        assert condition.evaluate(resource) is False

    def test_nested_field_access(self) -> None:
        """Should access nested fields correctly."""
        condition = Condition(
            field="config.metadata.http_tokens",
            operator=ConditionOperator.EQUALS,
            value="required",
        )

        resource = {"config": {"metadata": {"http_tokens": "required"}}}
        assert condition.evaluate(resource) is True

        resource = {"config": {"metadata": {"http_tokens": "optional"}}}
        assert condition.evaluate(resource) is False

    def test_negate_condition(self) -> None:
        """Should negate result when negate=True."""
        condition = Condition(
            field="config.public",
            operator=ConditionOperator.EQUALS,
            value=True,
            negate=True,
        )

        resource = {"config": {"public": True}}
        assert condition.evaluate(resource) is False  # Negated

        resource = {"config": {"public": False}}
        assert condition.evaluate(resource) is True  # Negated

    def test_to_dict_and_from_dict(self) -> None:
        """Should serialize and deserialize correctly."""
        original = Condition(
            field="config.encrypted",
            operator=ConditionOperator.EQUALS,
            value=True,
            negate=False,
        )

        data = original.to_dict()
        restored = Condition.from_dict(data)

        assert restored.field == original.field
        assert restored.operator == original.operator
        assert restored.value == original.value
        assert restored.negate == original.negate


class TestRule:
    """Tests for Rule class."""

    def test_rule_applies_to_exact_match(self) -> None:
        """Should match exact resource types."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=["aws_s3_bucket"],
            conditions=[],
        )

        assert rule.applies_to("aws_s3_bucket") is True
        assert rule.applies_to("aws_ec2_instance") is False

    def test_rule_applies_to_wildcard(self) -> None:
        """Should match wildcard patterns."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=["aws_s3_*"],
            conditions=[],
        )

        assert rule.applies_to("aws_s3_bucket") is True
        assert rule.applies_to("aws_s3_bucket_policy") is True
        assert rule.applies_to("aws_ec2_instance") is False

    def test_rule_applies_to_all_when_empty(self) -> None:
        """Should apply to all types when resource_types is empty."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=[],
            conditions=[],
        )

        assert rule.applies_to("aws_s3_bucket") is True
        assert rule.applies_to("aws_ec2_instance") is True

    def test_rule_evaluate_all_conditions_pass(self) -> None:
        """Should return True when all conditions pass."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=["aws_s3_bucket"],
            conditions=[
                Condition("config.encrypted", ConditionOperator.EQUALS, True),
                Condition("config.versioning", ConditionOperator.EQUALS, True),
            ],
        )

        resource = {"config": {"encrypted": True, "versioning": True}}
        assert rule.evaluate(resource) is True

    def test_rule_evaluate_fails_if_any_condition_fails(self) -> None:
        """Should return False if any condition fails."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=["aws_s3_bucket"],
            conditions=[
                Condition("config.encrypted", ConditionOperator.EQUALS, True),
                Condition("config.versioning", ConditionOperator.EQUALS, True),
            ],
        )

        resource = {"config": {"encrypted": True, "versioning": False}}
        assert rule.evaluate(resource) is False

    def test_disabled_rule_always_passes(self) -> None:
        """Disabled rules should always pass."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test",
            severity=Severity.HIGH,
            resource_types=["aws_s3_bucket"],
            conditions=[
                Condition("config.encrypted", ConditionOperator.EQUALS, True),
            ],
            enabled=False,
        )

        resource = {"config": {"encrypted": False}}
        assert rule.evaluate(resource) is True  # Disabled, so passes


class TestRuleParser:
    """Tests for rule parsing."""

    def test_load_rules_from_dict(self) -> None:
        """Should parse rules from dictionary."""
        data = {
            "rules": [
                {
                    "id": "TEST_001",
                    "name": "Test Rule",
                    "description": "Test description",
                    "severity": "high",
                    "resource_types": ["aws_s3_bucket"],
                    "conditions": [
                        {"field": "config.encrypted", "operator": "equals", "value": True},
                    ],
                    "remediation": "Enable encryption",
                }
            ]
        }

        rules = load_rules_from_dict(data)

        assert len(rules) == 1
        assert rules[0].id == "TEST_001"
        assert rules[0].severity == Severity.HIGH
        assert len(rules[0].conditions) == 1
        assert rules[0].remediation == "Enable encryption"

    def test_load_rules_from_yaml(self) -> None:
        """Should parse rules from YAML file."""
        yaml_content = """
rules:
  - id: TEST_001
    name: Test Rule
    severity: medium
    resource_types:
      - aws_rds_instance
    conditions:
      - field: config.storage_encrypted
        operator: equals
        value: true
"""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            path = Path(f.name)

        try:
            rules = load_rules_from_yaml(path)
            assert len(rules) == 1
            assert rules[0].id == "TEST_001"
            assert rules[0].severity == Severity.MEDIUM
        finally:
            path.unlink()

    def test_builtin_rules_load(self) -> None:
        """Should load built-in rules."""
        rules = get_builtin_rules()
        assert len(rules) > 0

        # Check for some expected rules
        rule_ids = [r.id for r in rules]
        assert "S3_001" in rule_ids
        assert "RDS_001" in rule_ids
        assert "EC2_001" in rule_ids


class TestRuleEngine:
    """Tests for RuleEngine."""

    @pytest.fixture
    def sample_graph(self) -> GraphEngine:
        """Create a sample graph with resources."""
        graph = GraphEngine()

        # Add an S3 bucket (encrypted)
        graph.add_resource(ResourceNode(
            id="bucket-1",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={"server_side_encryption": {"enabled": True}},
            tags={"Name": "encrypted-bucket"},
        ))

        # Add an S3 bucket (not encrypted)
        graph.add_resource(ResourceNode(
            id="bucket-2",
            resource_type=ResourceType.S3_BUCKET,
            region="us-east-1",
            config={},
            tags={"Name": "unencrypted-bucket"},
        ))

        # Add an RDS instance (encrypted)
        graph.add_resource(ResourceNode(
            id="db-1",
            resource_type=ResourceType.RDS_INSTANCE,
            region="us-east-1",
            config={"storage_encrypted": True, "multi_az": True},
            tags={"Name": "encrypted-db"},
        ))

        return graph

    @pytest.fixture
    def sample_rules(self) -> list[Rule]:
        """Create sample rules."""
        return [
            Rule(
                id="S3_ENCRYPT",
                name="S3 Encryption",
                description="S3 buckets must be encrypted",
                severity=Severity.HIGH,
                resource_types=["aws_s3_bucket"],
                conditions=[
                    Condition(
                        "config.server_side_encryption",
                        ConditionOperator.EXISTS,
                    ),
                ],
                remediation="Enable S3 server-side encryption",
            ),
            Rule(
                id="RDS_ENCRYPT",
                name="RDS Encryption",
                description="RDS must be encrypted",
                severity=Severity.HIGH,
                resource_types=["aws_db_instance"],
                conditions=[
                    Condition(
                        "config.storage_encrypted",
                        ConditionOperator.EQUALS,
                        True,
                    ),
                ],
            ),
        ]

    def test_engine_evaluate(
        self, sample_graph: GraphEngine, sample_rules: list[Rule]
    ) -> None:
        """Should evaluate rules against graph."""
        engine = RuleEngine(sample_rules)
        results = engine.evaluate(sample_graph)

        assert results.total_resources == 3
        assert len(results.results) == 2  # 2 rules

        # Check S3 rule results
        s3_result = next(r for r in results.results if r.rule.id == "S3_ENCRYPT")
        assert s3_result.passed_count == 1
        assert s3_result.failed_count == 1
        assert len(s3_result.findings) == 1

        # Check RDS rule results
        rds_result = next(r for r in results.results if r.rule.id == "RDS_ENCRYPT")
        assert rds_result.passed_count == 1
        assert rds_result.failed_count == 0

    def test_engine_score_calculation(
        self, sample_graph: GraphEngine, sample_rules: list[Rule]
    ) -> None:
        """Should calculate compliance score."""
        engine = RuleEngine(sample_rules)
        results = engine.evaluate(sample_graph)

        # 2 passed, 1 failed out of 3 checks
        # Score is weighted by severity
        assert 0 < results.score < 100
        assert results.grade in ("A", "B", "C", "D", "F")

    def test_engine_findings(
        self, sample_graph: GraphEngine, sample_rules: list[Rule]
    ) -> None:
        """Should record findings for failures."""
        engine = RuleEngine(sample_rules)
        results = engine.evaluate(sample_graph)

        findings = results.get_high_findings()
        assert len(findings) == 1
        assert findings[0].resource_id == "bucket-2"
        assert findings[0].rule.id == "S3_ENCRYPT"

    def test_engine_filter_by_region(
        self, sample_graph: GraphEngine, sample_rules: list[Rule]
    ) -> None:
        """Should filter resources by region."""
        # Add resource in different region
        sample_graph.add_resource(ResourceNode(
            id="bucket-west",
            resource_type=ResourceType.S3_BUCKET,
            region="us-west-2",
            config={},
            tags={"Name": "west-bucket"},
        ))

        engine = RuleEngine(sample_rules)
        results = engine.evaluate(
            sample_graph,
            resource_filter={"region": "us-east-1"},
        )

        # Should only evaluate us-east-1 resources
        s3_result = next(r for r in results.results if r.rule.id == "S3_ENCRYPT")
        assert s3_result.passed_count + s3_result.failed_count == 2  # Not 3

    def test_engine_get_rules_by_severity(
        self, sample_rules: list[Rule]
    ) -> None:
        """Should filter rules by severity."""
        engine = RuleEngine(sample_rules)

        high_rules = engine.get_rules_by_severity("high")
        assert len(high_rules) == 2

        critical_rules = engine.get_rules_by_severity("critical")
        assert len(critical_rules) == 0


class TestComplianceResults:
    """Tests for ComplianceResults."""

    def test_score_full_compliance(self) -> None:
        """Score should be 100% for full compliance."""
        results = ComplianceResults()
        results.results.append(
            ComplianceResult(
                rule=Rule("TEST", "Test", "", Severity.HIGH, [], []),
                passed_count=10,
                failed_count=0,
            )
        )

        assert results.score == 100.0
        assert results.grade == "A"

    def test_score_with_failures(self) -> None:
        """Score should decrease with failures."""
        rule = Rule("TEST", "Test", "", Severity.HIGH, [], [])
        results = ComplianceResults()
        results.results.append(
            ComplianceResult(rule=rule, passed_count=5, failed_count=5)
        )

        assert results.score < 100.0
        assert results.total_passed == 5
        assert results.total_failed == 5

    def test_get_summary(self) -> None:
        """Should generate summary statistics."""
        rule = Rule("TEST", "Test", "", Severity.HIGH, [], [])
        finding = RuleFinding(
            rule=rule,
            resource_id="test-resource",
            resource_type="aws_test",
        )

        results = ComplianceResults(total_resources=10)
        results.results.append(
            ComplianceResult(
                rule=rule,
                passed_count=8,
                failed_count=2,
                findings=[finding, finding],
            )
        )

        summary = results.get_summary()

        assert summary["total_resources"] == 10
        assert summary["total_passed"] == 8
        assert summary["total_failed"] == 2
        assert summary["total_findings"] == 2
        assert "high" in summary["findings_by_severity"]


class TestComplianceReporter:
    """Tests for ComplianceReporter."""

    @pytest.fixture
    def sample_results(self) -> ComplianceResults:
        """Create sample results for reporting."""
        rule = Rule(
            id="TEST_001",
            name="Test Rule",
            description="Test description",
            severity=Severity.HIGH,
            resource_types=["aws_test"],
            conditions=[],
            remediation="Fix the issue",
        )

        finding = RuleFinding(
            rule=rule,
            resource_id="test-resource",
            resource_type="aws_test",
            resource_name="My Resource",
            region="us-east-1",
        )

        results = ComplianceResults(total_resources=10)
        results.results.append(
            ComplianceResult(
                rule=rule,
                passed_count=8,
                failed_count=2,
                findings=[finding],
            )
        )

        return results

    def test_get_summary_text(self, sample_results: ComplianceResults) -> None:
        """Should generate summary text."""
        reporter = ComplianceReporter()
        summary = reporter.get_summary_text(sample_results)

        assert "Compliance:" in summary
        assert "%" in summary
        assert "findings" in summary

    def test_write_json(self, sample_results: ComplianceResults) -> None:
        """Should write JSON report."""
        import json

        reporter = ComplianceReporter()

        with NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = Path(f.name)

        try:
            reporter.write_json(sample_results, path)

            with open(path) as f:
                data = json.load(f)

            assert "summary" in data
            assert "results" in data
            assert data["summary"]["total_resources"] == 10
        finally:
            path.unlink()

    def test_write_html(self, sample_results: ComplianceResults) -> None:
        """Should write HTML report."""
        reporter = ComplianceReporter()

        with NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            path = Path(f.name)

        try:
            reporter.write_html(sample_results, path, title="Test Report")

            with open(path) as f:
                html = f.read()

            assert "<!DOCTYPE html>" in html
            assert "Test Report" in html
            assert "TEST_001" in html
        finally:
            path.unlink()
