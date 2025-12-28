"""
Compliance Rules Engine for RepliMap.

This module provides a policy-as-code framework for defining and evaluating
custom compliance rules against AWS resources.

Features:
- YAML-based rule definitions
- Resource type matching
- Condition expressions (equals, contains, exists, regex)
- Severity levels (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Compliance scoring and reporting
- Built-in rule library

Usage:
    from replimap.compliance import RuleEngine, load_rules_from_yaml

    # Load rules
    rules = load_rules_from_yaml("compliance_rules.yaml")

    # Evaluate against resources
    engine = RuleEngine(rules)
    results = engine.evaluate(graph)

    # Generate report
    print(f"Compliance Score: {results.score}%")
"""

from .engine import RuleEngine
from .models import (
    ComplianceResult,
    ComplianceResults,
    Condition,
    ConditionOperator,
    Rule,
    RuleFinding,
    Severity,
)
from .parser import load_rules_from_dict, load_rules_from_yaml
from .reporter import ComplianceReporter

__all__ = [
    # Engine
    "RuleEngine",
    # Models
    "Rule",
    "Condition",
    "ConditionOperator",
    "Severity",
    "RuleFinding",
    "ComplianceResult",
    "ComplianceResults",
    # Parser
    "load_rules_from_yaml",
    "load_rules_from_dict",
    # Reporter
    "ComplianceReporter",
]
