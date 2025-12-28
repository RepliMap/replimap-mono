"""
Compliance Rule Engine.

Evaluates compliance rules against AWS resources in a GraphEngine.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from .models import (
    ComplianceResult,
    ComplianceResults,
    Condition,
    Rule,
    RuleFinding,
)

if TYPE_CHECKING:
    from replimap.core import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


class RuleEngine:
    """
    Evaluates compliance rules against resources.

    Usage:
        engine = RuleEngine(rules)
        results = engine.evaluate(graph)
        print(f"Score: {results.score}%, Grade: {results.grade}")
    """

    def __init__(
        self,
        rules: list[Rule],
        include_disabled: bool = False,
    ) -> None:
        """
        Initialize the rule engine.

        Args:
            rules: List of rules to evaluate
            include_disabled: If True, include disabled rules in evaluation
        """
        self._all_rules = rules
        self._include_disabled = include_disabled

    @property
    def rules(self) -> list[Rule]:
        """Get active rules."""
        if self._include_disabled:
            return self._all_rules
        return [r for r in self._all_rules if r.enabled]

    @property
    def rule_count(self) -> int:
        """Get number of active rules."""
        return len(self.rules)

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID."""
        for rule in self._all_rules:
            if rule.id == rule_id:
                return rule
        return None

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        self._all_rules.append(rule)

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a rule by ID.

        Returns:
            True if rule was removed, False if not found
        """
        for i, rule in enumerate(self._all_rules):
            if rule.id == rule_id:
                del self._all_rules[i]
                return True
        return False

    def evaluate(
        self,
        graph: GraphEngine,
        resource_filter: dict[str, Any] | None = None,
    ) -> ComplianceResults:
        """
        Evaluate all rules against resources in a graph.

        Args:
            graph: GraphEngine containing resources to evaluate
            resource_filter: Optional filter for resources (e.g., {"region": "us-east-1"})

        Returns:
            ComplianceResults with findings and scores
        """
        logger.info(f"Evaluating {len(self.rules)} rules against {graph.statistics()['total_resources']} resources")

        results = ComplianceResults(
            timestamp=datetime.now(),
            total_resources=graph.statistics()["total_resources"],
        )

        # Evaluate each rule
        for rule in self.rules:
            result = self._evaluate_rule(rule, graph, resource_filter)
            results.results.append(result)

            if result.failed_count > 0:
                logger.debug(
                    f"Rule {rule.id}: {result.failed_count} failures, "
                    f"{result.passed_count} passed"
                )

        logger.info(
            f"Evaluation complete: Score={results.score:.1f}% "
            f"Grade={results.grade} "
            f"Findings={results.total_findings}"
        )

        return results

    def _evaluate_rule(
        self,
        rule: Rule,
        graph: GraphEngine,
        resource_filter: dict[str, Any] | None,
    ) -> ComplianceResult:
        """Evaluate a single rule against all applicable resources."""
        result = ComplianceResult(rule=rule)

        for resource in graph.iter_resources():
            # Check if rule applies to this resource type
            resource_type = str(resource.resource_type)
            if not rule.applies_to(resource_type):
                result.skipped_count += 1
                continue

            # Apply optional filter
            if resource_filter and not self._matches_filter(resource, resource_filter):
                result.skipped_count += 1
                continue

            # Evaluate the rule
            passed = rule.evaluate(resource)

            if passed:
                result.passed_count += 1
            else:
                result.failed_count += 1

                # Create finding with failed conditions
                failed_conditions = self._get_failed_conditions(rule, resource)

                finding = RuleFinding(
                    rule=rule,
                    resource_id=resource.id,
                    resource_type=resource_type,
                    resource_name=resource.original_name or resource.id,
                    region=resource.region or "",
                    failed_conditions=failed_conditions,
                )
                result.findings.append(finding)

        return result

    def _matches_filter(
        self,
        resource: ResourceNode,
        filter_dict: dict[str, Any],
    ) -> bool:
        """Check if a resource matches a filter."""
        for key, value in filter_dict.items():
            if key == "region":
                if resource.region != value:
                    return False
            elif key == "resource_type":
                if str(resource.resource_type) != value:
                    return False
            elif key == "tags":
                if isinstance(value, dict):
                    for tag_key, tag_value in value.items():
                        if resource.tags.get(tag_key) != tag_value:
                            return False
            elif key in resource.config:
                if resource.config.get(key) != value:
                    return False

        return True

    def _get_failed_conditions(
        self,
        rule: Rule,
        resource: ResourceNode,
    ) -> list[Condition]:
        """Get the list of conditions that failed for a resource."""
        failed = []
        for condition in rule.conditions:
            if not condition.evaluate(resource):
                failed.append(condition)
        return failed

    def evaluate_resource(
        self,
        resource: ResourceNode,
    ) -> list[RuleFinding]:
        """
        Evaluate all rules against a single resource.

        Args:
            resource: Resource to evaluate

        Returns:
            List of findings for this resource
        """
        findings = []
        resource_type = str(resource.resource_type)

        for rule in self.rules:
            if not rule.applies_to(resource_type):
                continue

            if not rule.evaluate(resource):
                failed_conditions = self._get_failed_conditions(rule, resource)
                finding = RuleFinding(
                    rule=rule,
                    resource_id=resource.id,
                    resource_type=resource_type,
                    resource_name=resource.original_name or resource.id,
                    region=resource.region or "",
                    failed_conditions=failed_conditions,
                )
                findings.append(finding)

        return findings

    def get_rules_for_resource_type(self, resource_type: str) -> list[Rule]:
        """Get all rules that apply to a resource type."""
        return [r for r in self.rules if r.applies_to(resource_type)]

    def get_rules_by_severity(self, severity: str) -> list[Rule]:
        """Get all rules with a specific severity."""
        from .models import Severity
        try:
            sev = Severity(severity.lower())
            return [r for r in self.rules if r.severity == sev]
        except ValueError:
            return []

    def get_rules_by_tag(self, tag: str) -> list[Rule]:
        """Get all rules with a specific tag."""
        return [r for r in self.rules if tag in r.tags]

    def validate_rules(self) -> list[str]:
        """
        Validate all rules for common issues.

        Returns:
            List of validation error messages (empty if all valid)
        """
        errors = []
        rule_ids = set()

        for rule in self._all_rules:
            # Check for duplicate IDs
            if rule.id in rule_ids:
                errors.append(f"Duplicate rule ID: {rule.id}")
            rule_ids.add(rule.id)

            # Check for empty conditions
            if not rule.conditions:
                errors.append(f"Rule {rule.id} has no conditions")

            # Check for empty resource types
            if not rule.resource_types:
                errors.append(
                    f"Rule {rule.id} has no resource_types "
                    "(will apply to all resources)"
                )

        return errors
