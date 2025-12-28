"""
Data models for the Compliance Rules Engine.

Defines the structure for rules, conditions, findings, and results.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity levels for compliance findings."""

    CRITICAL = "critical"  # Must fix immediately, security risk
    HIGH = "high"  # Should fix soon, significant risk
    MEDIUM = "medium"  # Should fix, moderate risk
    LOW = "low"  # Nice to fix, minor risk
    INFO = "info"  # Informational, no action required

    def __str__(self) -> str:
        return self.value

    @property
    def weight(self) -> int:
        """Get numeric weight for scoring."""
        weights = {
            Severity.CRITICAL: 10,
            Severity.HIGH: 5,
            Severity.MEDIUM: 3,
            Severity.LOW: 1,
            Severity.INFO: 0,
        }
        return weights[self]


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""

    EQUALS = "equals"  # Exact match
    NOT_EQUALS = "not_equals"  # Not equal
    CONTAINS = "contains"  # String contains
    NOT_CONTAINS = "not_contains"  # String doesn't contain
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"  # String ends with
    MATCHES = "matches"  # Regex match
    EXISTS = "exists"  # Field exists and is truthy
    NOT_EXISTS = "not_exists"  # Field doesn't exist or is falsy
    IN = "in"  # Value in list
    NOT_IN = "not_in"  # Value not in list
    GREATER_THAN = "greater_than"  # Numeric comparison
    LESS_THAN = "less_than"  # Numeric comparison
    GREATER_EQUAL = "greater_equal"  # Numeric comparison
    LESS_EQUAL = "less_equal"  # Numeric comparison

    def __str__(self) -> str:
        return self.value


@dataclass
class Condition:
    """
    A condition that must be met for a rule to pass.

    Conditions are evaluated against resource configurations.

    Attributes:
        field: Dot-notation path to the config field (e.g., "config.encrypted")
        operator: Comparison operator
        value: Expected value for comparison
        negate: If True, negate the result (for complex logic)
    """

    field: str
    operator: ConditionOperator
    value: Any = None
    negate: bool = False

    def evaluate(self, resource: Any) -> bool:
        """
        Evaluate this condition against a resource.

        Args:
            resource: ResourceNode or dict to evaluate

        Returns:
            True if condition passes, False otherwise
        """
        # Get the field value using dot notation
        actual_value = self._get_field_value(resource, self.field)

        # Evaluate based on operator
        result = self._evaluate_operator(actual_value)

        # Apply negation if specified
        if self.negate:
            result = not result

        return result

    def _get_field_value(self, obj: Any, path: str) -> Any:
        """
        Get a value from an object using dot notation.

        Supports:
        - config.field_name
        - config.nested.field
        - tags.Name
        - region, id, resource_type (direct attributes)

        Args:
            obj: Object to extract from
            path: Dot-notation path

        Returns:
            The value at the path, or None if not found
        """
        parts = path.split(".")
        current = obj

        for part in parts:
            if current is None:
                return None

            # Handle dict-like access
            if isinstance(current, dict):
                current = current.get(part)
            # Handle object attribute access
            elif hasattr(current, part):
                current = getattr(current, part)
            # Handle ResourceNode config access
            elif hasattr(current, "config") and part != "config":
                config = getattr(current, "config", {})
                current = config.get(part) if isinstance(config, dict) else None
            else:
                return None

        return current

    def _evaluate_operator(self, actual: Any) -> bool:
        """Evaluate the operator against actual and expected values."""
        expected = self.value

        if self.operator == ConditionOperator.EXISTS:
            return actual is not None and actual != "" and actual != []

        if self.operator == ConditionOperator.NOT_EXISTS:
            return actual is None or actual == "" or actual == []

        if self.operator == ConditionOperator.EQUALS:
            result: bool = actual == expected
            return result

        if self.operator == ConditionOperator.NOT_EQUALS:
            result = actual != expected
            return result

        if self.operator == ConditionOperator.CONTAINS:
            if isinstance(actual, str):
                return expected in actual
            if isinstance(actual, (list, tuple)):
                return expected in actual
            return False

        if self.operator == ConditionOperator.NOT_CONTAINS:
            if isinstance(actual, str):
                return expected not in actual
            if isinstance(actual, (list, tuple)):
                return expected not in actual
            return True

        if self.operator == ConditionOperator.STARTS_WITH:
            return isinstance(actual, str) and actual.startswith(str(expected))

        if self.operator == ConditionOperator.ENDS_WITH:
            return isinstance(actual, str) and actual.endswith(str(expected))

        if self.operator == ConditionOperator.MATCHES:
            if not isinstance(actual, str):
                return False
            try:
                return bool(re.match(str(expected), actual))
            except re.error:
                return False

        if self.operator == ConditionOperator.IN:
            if not isinstance(expected, (list, tuple)):
                return False
            return actual in expected

        if self.operator == ConditionOperator.NOT_IN:
            if not isinstance(expected, (list, tuple)):
                return True
            return actual not in expected

        # Numeric comparisons
        if self.operator in (
            ConditionOperator.GREATER_THAN,
            ConditionOperator.LESS_THAN,
            ConditionOperator.GREATER_EQUAL,
            ConditionOperator.LESS_EQUAL,
        ):
            try:
                actual_num = float(actual) if actual is not None else 0
                expected_num = float(expected) if expected is not None else 0

                if self.operator == ConditionOperator.GREATER_THAN:
                    return actual_num > expected_num
                if self.operator == ConditionOperator.LESS_THAN:
                    return actual_num < expected_num
                if self.operator == ConditionOperator.GREATER_EQUAL:
                    return actual_num >= expected_num
                if self.operator == ConditionOperator.LESS_EQUAL:
                    return actual_num <= expected_num
            except (TypeError, ValueError):
                return False

        return False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "field": self.field,
            "operator": str(self.operator),
            "value": self.value,
            "negate": self.negate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Condition:
        """Create from dictionary."""
        return cls(
            field=data["field"],
            operator=ConditionOperator(data["operator"]),
            value=data.get("value"),
            negate=data.get("negate", False),
        )


@dataclass
class Rule:
    """
    A compliance rule definition.

    Rules define what conditions resources must meet to be compliant.
    Multiple conditions are AND-ed together by default.

    Attributes:
        id: Unique rule identifier (e.g., "ENCRYPT_001")
        name: Human-readable rule name
        description: Detailed description of the rule
        severity: Severity level for violations
        resource_types: List of resource types this rule applies to
        conditions: List of conditions that must ALL pass
        enabled: Whether the rule is active
        tags: Optional tags for categorization
        remediation: Suggested remediation steps
        references: Links to documentation or standards
    """

    id: str
    name: str
    description: str
    severity: Severity
    resource_types: list[str]
    conditions: list[Condition]
    enabled: bool = True
    tags: list[str] = field(default_factory=list)
    remediation: str = ""
    references: list[str] = field(default_factory=list)

    def applies_to(self, resource_type: str) -> bool:
        """
        Check if this rule applies to a resource type.

        Args:
            resource_type: Resource type string (e.g., "aws_s3_bucket")

        Returns:
            True if rule applies to this resource type
        """
        if not self.resource_types:
            return True  # Empty means all types

        # Support wildcard matching
        for pattern in self.resource_types:
            if pattern == "*":
                return True
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                if resource_type.startswith(prefix):
                    return True
            elif pattern == resource_type:
                return True

        return False

    def evaluate(self, resource: Any) -> bool:
        """
        Evaluate this rule against a resource.

        All conditions must pass for the rule to pass.

        Args:
            resource: ResourceNode to evaluate

        Returns:
            True if resource is compliant, False otherwise
        """
        if not self.enabled:
            return True  # Disabled rules always pass

        # All conditions must pass (AND logic)
        return all(condition.evaluate(resource) for condition in self.conditions)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "severity": str(self.severity),
            "resource_types": self.resource_types,
            "conditions": [c.to_dict() for c in self.conditions],
            "enabled": self.enabled,
            "tags": self.tags,
            "remediation": self.remediation,
            "references": self.references,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rule:
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            severity=Severity(data.get("severity", "medium")),
            resource_types=data.get("resource_types", []),
            conditions=[
                Condition.from_dict(c) for c in data.get("conditions", [])
            ],
            enabled=data.get("enabled", True),
            tags=data.get("tags", []),
            remediation=data.get("remediation", ""),
            references=data.get("references", []),
        )


@dataclass
class RuleFinding:
    """
    A finding from rule evaluation.

    Represents a resource that failed a compliance rule.

    Attributes:
        rule: The rule that was violated
        resource_id: ID of the non-compliant resource
        resource_type: Type of the resource
        resource_name: Human-readable resource name
        region: AWS region
        failed_conditions: Which conditions failed
        timestamp: When the finding was recorded
    """

    rule: Rule
    resource_id: str
    resource_type: str
    resource_name: str = ""
    region: str = ""
    failed_conditions: list[Condition] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def severity(self) -> Severity:
        """Get severity from the rule."""
        return self.rule.severity

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "rule_id": self.rule.id,
            "rule_name": self.rule.name,
            "severity": str(self.severity),
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "failed_conditions": [c.to_dict() for c in self.failed_conditions],
            "remediation": self.rule.remediation,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ComplianceResult:
    """
    Result of evaluating a single rule against all resources.

    Attributes:
        rule: The evaluated rule
        passed_count: Number of resources that passed
        failed_count: Number of resources that failed
        skipped_count: Number of resources skipped (not applicable)
        findings: List of findings for failed resources
    """

    rule: Rule
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    findings: list[RuleFinding] = field(default_factory=list)

    @property
    def total_evaluated(self) -> int:
        """Total resources evaluated (passed + failed)."""
        return self.passed_count + self.failed_count

    @property
    def compliance_rate(self) -> float:
        """Percentage of resources that passed."""
        if self.total_evaluated == 0:
            return 100.0
        return (self.passed_count / self.total_evaluated) * 100


@dataclass
class ComplianceResults:
    """
    Aggregate results from evaluating all rules.

    Attributes:
        results: Per-rule results
        total_resources: Total resources evaluated
        timestamp: When evaluation was performed
    """

    results: list[ComplianceResult] = field(default_factory=list)
    total_resources: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def total_passed(self) -> int:
        """Total passing checks across all rules."""
        return sum(r.passed_count for r in self.results)

    @property
    def total_failed(self) -> int:
        """Total failing checks across all rules."""
        return sum(r.failed_count for r in self.results)

    @property
    def total_findings(self) -> int:
        """Total number of findings."""
        return sum(len(r.findings) for r in self.results)

    @property
    def score(self) -> float:
        """
        Calculate compliance score (0-100).

        Score is weighted by severity:
        - CRITICAL failures reduce score significantly
        - INFO findings don't affect score
        """
        if self.total_passed + self.total_failed == 0:
            return 100.0

        # Calculate weighted score
        total_weight = 0
        failed_weight = 0

        for result in self.results:
            weight = result.rule.severity.weight
            total_weight += (result.passed_count + result.failed_count) * weight
            failed_weight += result.failed_count * weight

        if total_weight == 0:
            return 100.0

        return max(0.0, 100.0 - (failed_weight / total_weight * 100))

    @property
    def grade(self) -> str:
        """
        Get letter grade for compliance score.

        A: 90-100
        B: 80-89
        C: 70-79
        D: 60-69
        F: 0-59
        """
        score = self.score
        if score >= 90:
            return "A"
        if score >= 80:
            return "B"
        if score >= 70:
            return "C"
        if score >= 60:
            return "D"
        return "F"

    def get_findings_by_severity(
        self, severity: Severity
    ) -> list[RuleFinding]:
        """Get all findings of a specific severity."""
        findings = []
        for result in self.results:
            for finding in result.findings:
                if finding.severity == severity:
                    findings.append(finding)
        return findings

    def get_critical_findings(self) -> list[RuleFinding]:
        """Get all critical severity findings."""
        return self.get_findings_by_severity(Severity.CRITICAL)

    def get_high_findings(self) -> list[RuleFinding]:
        """Get all high severity findings."""
        return self.get_findings_by_severity(Severity.HIGH)

    def get_findings_by_resource(self, resource_id: str) -> list[RuleFinding]:
        """Get all findings for a specific resource."""
        findings = []
        for result in self.results:
            for finding in result.findings:
                if finding.resource_id == resource_id:
                    findings.append(finding)
        return findings

    def get_findings_by_resource_type(
        self, resource_type: str
    ) -> list[RuleFinding]:
        """Get all findings for a resource type."""
        findings = []
        for result in self.results:
            for finding in result.findings:
                if finding.resource_type == resource_type:
                    findings.append(finding)
        return findings

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics."""
        severity_counts: dict[str, int] = {}
        for result in self.results:
            for finding in result.findings:
                sev = str(finding.severity)
                severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "score": round(self.score, 1),
            "grade": self.grade,
            "total_resources": self.total_resources,
            "total_rules": len(self.results),
            "total_passed": self.total_passed,
            "total_failed": self.total_failed,
            "total_findings": self.total_findings,
            "findings_by_severity": severity_counts,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "summary": self.get_summary(),
            "results": [
                {
                    "rule": r.rule.to_dict(),
                    "passed_count": r.passed_count,
                    "failed_count": r.failed_count,
                    "skipped_count": r.skipped_count,
                    "compliance_rate": round(r.compliance_rate, 1),
                    "findings": [f.to_dict() for f in r.findings],
                }
                for r in self.results
            ],
        }
