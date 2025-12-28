"""
Rule Parser for loading compliance rules from YAML.

Supports loading rules from:
- Single YAML file
- Directory of YAML files
- Dictionary (for programmatic use)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from .models import Condition, ConditionOperator, Rule, Severity

logger = logging.getLogger(__name__)


class RuleParseError(Exception):
    """Raised when a rule cannot be parsed."""

    def __init__(self, message: str, rule_id: str | None = None) -> None:
        super().__init__(message)
        self.rule_id = rule_id


def load_rules_from_yaml(path: str | Path) -> list[Rule]:
    """
    Load rules from a YAML file or directory.

    File format:
    ```yaml
    rules:
      - id: ENCRYPT_001
        name: S3 Bucket Encryption
        description: All S3 buckets must have encryption enabled
        severity: high
        resource_types:
          - aws_s3_bucket
        conditions:
          - field: config.server_side_encryption_configuration
            operator: exists
        remediation: Enable server-side encryption on the S3 bucket
    ```

    Args:
        path: Path to YAML file or directory containing YAML files

    Returns:
        List of parsed Rule objects

    Raises:
        RuleParseError: If a rule cannot be parsed
        FileNotFoundError: If path doesn't exist
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Rule file/directory not found: {path}")

    if path.is_dir():
        return _load_from_directory(path)

    return _load_from_file(path)


def _load_from_file(path: Path) -> list[Rule]:
    """Load rules from a single YAML file."""
    logger.debug(f"Loading rules from {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        return []

    return load_rules_from_dict(data)


def _load_from_directory(path: Path) -> list[Rule]:
    """Load rules from all YAML files in a directory."""
    rules: list[Rule] = []

    for yaml_file in sorted(path.glob("*.yaml")):
        rules.extend(_load_from_file(yaml_file))

    for yml_file in sorted(path.glob("*.yml")):
        rules.extend(_load_from_file(yml_file))

    logger.info(f"Loaded {len(rules)} rules from {path}")
    return rules


def load_rules_from_dict(data: dict[str, Any]) -> list[Rule]:
    """
    Load rules from a dictionary.

    Args:
        data: Dictionary with "rules" key containing list of rule definitions

    Returns:
        List of parsed Rule objects

    Raises:
        RuleParseError: If a rule cannot be parsed
    """
    if "rules" not in data:
        # Support direct list format
        if isinstance(data, list):
            return [_parse_rule(r) for r in data]
        raise RuleParseError("YAML must contain 'rules' key with list of rules")

    rules_data = data["rules"]
    if not isinstance(rules_data, list):
        raise RuleParseError("'rules' must be a list")

    rules = []
    for rule_data in rules_data:
        try:
            rule = _parse_rule(rule_data)
            rules.append(rule)
        except Exception as e:
            rule_id = rule_data.get("id", "unknown")
            raise RuleParseError(f"Failed to parse rule: {e}", rule_id=rule_id) from e

    return rules


def _parse_rule(data: dict[str, Any]) -> Rule:
    """Parse a single rule from dictionary."""
    # Required fields
    if "id" not in data:
        raise RuleParseError("Rule must have 'id' field")
    if "name" not in data:
        raise RuleParseError(f"Rule {data['id']} must have 'name' field")

    # Parse severity
    severity_str = data.get("severity", "medium").lower()
    try:
        severity = Severity(severity_str)
    except ValueError:
        valid = [s.value for s in Severity]
        raise RuleParseError(
            f"Invalid severity '{severity_str}' in rule {data['id']}. "
            f"Valid values: {valid}"
        )

    # Parse conditions
    conditions = []
    for cond_data in data.get("conditions", []):
        conditions.append(_parse_condition(cond_data, data["id"]))

    return Rule(
        id=data["id"],
        name=data["name"],
        description=data.get("description", ""),
        severity=severity,
        resource_types=data.get("resource_types", []),
        conditions=conditions,
        enabled=data.get("enabled", True),
        tags=data.get("tags", []),
        remediation=data.get("remediation", ""),
        references=data.get("references", []),
    )


def _parse_condition(data: dict[str, Any], rule_id: str) -> Condition:
    """Parse a condition from dictionary."""
    if "field" not in data:
        raise RuleParseError(f"Condition in rule {rule_id} must have 'field'")
    if "operator" not in data:
        raise RuleParseError(f"Condition in rule {rule_id} must have 'operator'")

    # Parse operator
    operator_str = data["operator"].lower()
    try:
        operator = ConditionOperator(operator_str)
    except ValueError:
        valid = [o.value for o in ConditionOperator]
        raise RuleParseError(
            f"Invalid operator '{operator_str}' in rule {rule_id}. "
            f"Valid values: {valid}"
        )

    return Condition(
        field=data["field"],
        operator=operator,
        value=data.get("value"),
        negate=data.get("negate", False),
    )


# Built-in rules library
BUILTIN_RULES: dict[str, Any] = {
    "rules": [
        # S3 Bucket Security
        {
            "id": "S3_001",
            "name": "S3 Bucket Encryption",
            "description": "S3 buckets must have server-side encryption enabled",
            "severity": "high",
            "resource_types": ["aws_s3_bucket"],
            "conditions": [
                {"field": "config.server_side_encryption", "operator": "exists"},
            ],
            "tags": ["security", "encryption", "s3"],
            "remediation": (
                "Enable server-side encryption on the S3 bucket using "
                "SSE-S3 or SSE-KMS"
            ),
            "references": [
                "https://docs.aws.amazon.com/AmazonS3/latest/userguide/bucket-encryption.html"
            ],
        },
        {
            "id": "S3_002",
            "name": "S3 Bucket Public Access Block",
            "description": "S3 buckets should block public access",
            "severity": "critical",
            "resource_types": ["aws_s3_bucket"],
            "conditions": [
                {"field": "config.block_public_acls", "operator": "equals", "value": True},
            ],
            "tags": ["security", "public-access", "s3"],
            "remediation": "Enable S3 Block Public Access settings",
        },
        # RDS Security
        {
            "id": "RDS_001",
            "name": "RDS Encryption at Rest",
            "description": "RDS instances must have encryption enabled",
            "severity": "high",
            "resource_types": ["aws_db_instance"],
            "conditions": [
                {"field": "config.storage_encrypted", "operator": "equals", "value": True},
            ],
            "tags": ["security", "encryption", "rds"],
            "remediation": (
                "Enable storage encryption on the RDS instance. "
                "Note: This requires recreating the instance."
            ),
        },
        {
            "id": "RDS_002",
            "name": "RDS Multi-AZ Deployment",
            "description": "Production RDS instances should use Multi-AZ",
            "severity": "medium",
            "resource_types": ["aws_db_instance"],
            "conditions": [
                {"field": "config.multi_az", "operator": "equals", "value": True},
            ],
            "tags": ["availability", "rds"],
            "remediation": "Enable Multi-AZ deployment for high availability",
        },
        {
            "id": "RDS_003",
            "name": "RDS Not Publicly Accessible",
            "description": "RDS instances should not be publicly accessible",
            "severity": "critical",
            "resource_types": ["aws_db_instance"],
            "conditions": [
                {"field": "config.publicly_accessible", "operator": "equals", "value": False},
            ],
            "tags": ["security", "network", "rds"],
            "remediation": "Disable public accessibility for the RDS instance",
        },
        # EC2 Security
        {
            "id": "EC2_001",
            "name": "EC2 IMDSv2 Required",
            "description": "EC2 instances should require IMDSv2",
            "severity": "high",
            "resource_types": ["aws_instance"],
            "conditions": [
                {
                    "field": "config.metadata_options.http_tokens",
                    "operator": "equals",
                    "value": "required",
                },
            ],
            "tags": ["security", "ec2", "metadata"],
            "remediation": (
                "Configure the instance to require IMDSv2 by setting "
                "http_tokens to 'required'"
            ),
        },
        {
            "id": "EC2_002",
            "name": "EC2 EBS Optimized",
            "description": "EC2 instances should be EBS-optimized",
            "severity": "low",
            "resource_types": ["aws_instance"],
            "conditions": [
                {"field": "config.ebs_optimized", "operator": "equals", "value": True},
            ],
            "tags": ["performance", "ec2"],
            "remediation": "Enable EBS optimization for better storage performance",
        },
        # VPC Security
        {
            "id": "VPC_001",
            "name": "VPC Flow Logs Enabled",
            "description": "VPCs should have flow logs enabled",
            "severity": "medium",
            "resource_types": ["aws_vpc"],
            "conditions": [
                {"field": "config.enable_dns_support", "operator": "equals", "value": True},
            ],
            "tags": ["security", "logging", "vpc"],
            "remediation": "Enable VPC Flow Logs for network traffic visibility",
        },
        # Security Group
        {
            "id": "SG_001",
            "name": "No Unrestricted SSH",
            "description": "Security groups should not allow SSH from 0.0.0.0/0",
            "severity": "critical",
            "resource_types": ["aws_security_group"],
            "conditions": [
                {
                    "field": "config.ingress",
                    "operator": "not_contains",
                    "value": "0.0.0.0/0",
                },
            ],
            "tags": ["security", "network", "ssh"],
            "remediation": "Restrict SSH access to specific IP ranges",
        },
        # EBS
        {
            "id": "EBS_001",
            "name": "EBS Volume Encryption",
            "description": "EBS volumes should be encrypted",
            "severity": "high",
            "resource_types": ["aws_ebs_volume"],
            "conditions": [
                {"field": "config.encrypted", "operator": "equals", "value": True},
            ],
            "tags": ["security", "encryption", "ebs"],
            "remediation": "Enable encryption on EBS volumes",
        },
    ]
}


def get_builtin_rules() -> list[Rule]:
    """
    Get the built-in rules library.

    Returns:
        List of built-in Rule objects
    """
    return load_rules_from_dict(BUILTIN_RULES)
