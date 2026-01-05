"""
Advanced Offline Drift Detection Engine.

Production-grade drift detection with:
- Robust Terraform state parsing (v3/v4)
- Intelligent attribute normalization
- Security-aware severity classification
- Configurable ignore rules
- Actionable remediation hints

This is the "offline terraform plan" - faster and doesn't require TF installation.
Compares cached RepliMap scans against Terraform state files.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS AND DATA MODELS
# ============================================================


class DriftType(Enum):
    """Types of drift between AWS and Terraform."""

    UNMANAGED = "unmanaged"  # In AWS, NOT in Terraform (ghost resource)
    MISSING = "missing"  # In Terraform, NOT in AWS (deleted manually)
    DRIFTED = "drifted"  # Exists in both, configuration differs


class DriftSeverity(Enum):
    """Severity levels for drift findings."""

    CRITICAL = "critical"  # Security: IAM, SG rules, encryption
    HIGH = "high"  # Infrastructure: instance types, networking
    MEDIUM = "medium"  # Configuration: most settings
    LOW = "low"  # Metadata: tags, descriptions
    INFO = "info"  # Non-impactful: timestamps


class Remediation(Enum):
    """Suggested remediation actions."""

    IMPORT = "import"  # Run terraform import
    APPLY = "apply"  # Run terraform apply
    UPDATE_CODE = "update_code"  # Update .tf files to match reality
    DELETE = "delete"  # Delete from state or recreate
    INVESTIGATE = "investigate"  # Manual investigation needed


@dataclass
class AttributeChange:
    """A single attribute that has drifted."""

    field: str
    expected: Any  # Value in Terraform State
    actual: Any  # Value in AWS
    severity: DriftSeverity

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "expected": self._serialize(self.expected),
            "actual": self._serialize(self.actual),
            "severity": self.severity.value,
        }

    def _serialize(self, val: Any) -> Any:
        """Serialize value for display."""
        if val is None:
            return None
        if isinstance(val, (str, int, float, bool)):
            if isinstance(val, str) and len(val) > 100:
                return val[:97] + "..."
            return val
        s = json.dumps(val, default=str)
        return s[:97] + "..." if len(s) > 100 else val


@dataclass
class DriftFinding:
    """A single drift finding with remediation hint."""

    resource_id: str
    resource_type: str
    resource_name: str
    drift_type: DriftType
    severity: DriftSeverity = DriftSeverity.MEDIUM
    changes: list[AttributeChange] = field(default_factory=list)
    terraform_address: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def max_change_severity(self) -> DriftSeverity:
        """Get highest severity among changes."""
        if not self.changes:
            return self.severity

        order = [
            DriftSeverity.CRITICAL,
            DriftSeverity.HIGH,
            DriftSeverity.MEDIUM,
            DriftSeverity.LOW,
            DriftSeverity.INFO,
        ]

        for sev in order:
            if any(c.severity == sev for c in self.changes):
                return sev
        return DriftSeverity.INFO

    @property
    def remediation(self) -> Remediation:
        """Get suggested remediation action."""
        if self.drift_type == DriftType.UNMANAGED:
            return Remediation.IMPORT
        if self.drift_type == DriftType.MISSING:
            return Remediation.APPLY
        # DRIFTED - depends on severity
        if self.max_change_severity == DriftSeverity.CRITICAL:
            return Remediation.INVESTIGATE
        return Remediation.APPLY

    @property
    def remediation_hint(self) -> str:
        """Get human-readable remediation hint."""
        hints = {
            DriftType.UNMANAGED: (
                f"Run 'terraform import {self.resource_type}.name {self.resource_id}' "
                "to manage this resource, or delete if unneeded"
            ),
            DriftType.MISSING: (
                "Resource deleted manually. Run 'terraform apply' to recreate, "
                "or 'terraform state rm' to remove from state"
            ),
            DriftType.DRIFTED: (
                "Run 'terraform apply' to restore expected state, "
                "or update .tf code to match current reality"
            ),
        }
        return hints.get(self.drift_type, "Manual investigation required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "drift_type": self.drift_type.value,
            "severity": self.max_change_severity.value,
            "terraform_address": self.terraform_address,
            "changes": [c.to_dict() for c in self.changes],
            "remediation": self.remediation.value,
            "remediation_hint": self.remediation_hint,
        }


@dataclass
class DriftReport:
    """Complete drift detection report."""

    findings: list[DriftFinding] = field(default_factory=list)
    scan_timestamp: str = ""
    state_file_path: str = ""
    summary: dict[str, Any] = field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        return len(self.findings) > 0

    @property
    def critical_count(self) -> int:
        return sum(
            1 for f in self.findings if f.max_change_severity == DriftSeverity.CRITICAL
        )

    @property
    def high_count(self) -> int:
        return sum(
            1 for f in self.findings if f.max_change_severity == DriftSeverity.HIGH
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_drift": self.has_drift,
            "scan_timestamp": self.scan_timestamp,
            "state_file": self.state_file_path,
            "findings_count": len(self.findings),
            "critical_count": self.critical_count,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_sarif(self) -> dict[str, Any]:
        """Convert to SARIF format for GitHub Security."""
        from replimap.core.formatters.sarif import SARIFGenerator

        return SARIFGenerator.from_drift_report(self)


# ============================================================
# TERRAFORM STATE LOADER
# ============================================================


class TerraformStateLoader:
    """
    Parses terraform.tfstate files.

    Supports:
    - Terraform State v4 (TF 0.12+)
    - Terraform State v3 (Legacy)
    - Resources with count/for_each
    - Module-nested resources
    """

    def load(self, state_path: Path) -> dict[str, dict[str, Any]]:
        """
        Load and parse Terraform state file.

        Returns:
            Dict mapping AWS resource ID to state info:
            {
                "i-1234567890abcdef0": {
                    "type": "aws_instance",
                    "name": "web",
                    "module": "module.vpc",
                    "address": "module.vpc.aws_instance.web",
                    "attributes": {...}
                }
            }
        """
        if not state_path.exists():
            logger.warning(f"State file not found: {state_path}")
            return {}

        try:
            data = json.loads(state_path.read_text())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in state file: {e}")
            return {}

        version = data.get("version", 4)

        if version >= 4:
            return self._parse_v4(data)
        else:
            return self._parse_v3(data)

    def _parse_v4(self, data: dict) -> dict[str, dict]:
        """Parse Terraform State v4 format (TF 0.12+)."""
        resources: dict[str, dict] = {}

        for resource in data.get("resources", []):
            resource_type = resource.get("type", "")
            resource_name = resource.get("name", "")
            module = resource.get("module", "")
            mode = resource.get("mode", "managed")

            # Skip data sources
            if mode != "managed":
                continue

            # Skip non-AWS resources
            if not resource_type.startswith("aws_"):
                continue

            # Handle instances (for count/for_each)
            for instance in resource.get("instances", []):
                attrs = instance.get("attributes", {})
                index_key = instance.get("index_key")

                # Get AWS resource ID
                aws_id = self._extract_resource_id(resource_type, attrs)
                if not aws_id:
                    continue

                # Build Terraform address
                address = self._build_address(
                    module, resource_type, resource_name, index_key
                )

                resources[aws_id] = {
                    "type": resource_type,
                    "name": resource_name,
                    "module": module,
                    "address": address,
                    "index_key": index_key,
                    "attributes": attrs,
                }

        logger.info(f"Loaded {len(resources)} managed resources from state")
        return resources

    def _parse_v3(self, data: dict) -> dict[str, dict]:
        """Parse legacy Terraform State v3 format."""
        resources: dict[str, dict] = {}

        for module in data.get("modules", [{}]):
            module_path = ".".join(module.get("path", ["root"]))
            if module_path == "root":
                module_path = ""

            for name, resource in module.get("resources", {}).items():
                parts = name.split(".")
                if len(parts) < 2:
                    continue

                resource_type = parts[0]
                resource_name = ".".join(parts[1:])

                # Skip non-AWS
                if not resource_type.startswith("aws_"):
                    continue

                attrs = resource.get("primary", {}).get("attributes", {})
                aws_id = attrs.get("id")

                if not aws_id:
                    continue

                address = f"{module_path}.{name}" if module_path else name

                resources[aws_id] = {
                    "type": resource_type,
                    "name": resource_name,
                    "module": module_path,
                    "address": address,
                    "attributes": self._flatten_v3_attributes(attrs),
                }

        return resources

    def _flatten_v3_attributes(self, attrs: dict) -> dict:
        """Convert TF v3 flattened attributes to nested structure."""
        # v3 stores lists as "field.0", "field.1", etc.
        # This is a simplified converter
        result = {}

        for key, value in attrs.items():
            if "." in key:
                parts = key.split(".")
                # Simple case: skip nested for now
                base = parts[0]
                if base not in result:
                    result[base] = value
            else:
                result[key] = value

        return result

    def _extract_resource_id(
        self,
        resource_type: str,
        attrs: dict,
    ) -> str | None:
        """Extract AWS resource ID from attributes."""
        # Standard ID field
        if "id" in attrs and attrs["id"]:
            return attrs["id"]

        # S3 bucket uses 'bucket' as ID
        if resource_type == "aws_s3_bucket":
            return attrs.get("bucket")

        # IAM resources use 'name' or 'arn'
        if resource_type in ("aws_iam_role", "aws_iam_policy", "aws_iam_user"):
            return attrs.get("name") or attrs.get("arn")

        # Security group rules have composite IDs
        if resource_type == "aws_security_group_rule":
            return self._build_sg_rule_id(attrs)

        return None

    def _build_sg_rule_id(self, attrs: dict) -> str:
        """Build composite ID for security group rules."""
        parts = [
            attrs.get("security_group_id", ""),
            attrs.get("type", ""),
            attrs.get("protocol", ""),
            str(attrs.get("from_port", "")),
            str(attrs.get("to_port", "")),
        ]
        return "_".join(filter(None, parts))

    def _build_address(
        self,
        module: str,
        resource_type: str,
        resource_name: str,
        index_key: Any,
    ) -> str:
        """Build Terraform resource address."""
        address = f"{resource_type}.{resource_name}"

        if index_key is not None:
            if isinstance(index_key, int):
                address += f"[{index_key}]"
            else:
                address += f'["{index_key}"]'

        if module:
            address = f"{module}.{address}"

        return address


# ============================================================
# ATTRIBUTE NORMALIZER
# ============================================================


class AttributeNormalizer:
    """
    Normalizes attributes between AWS API and Terraform State.

    This is CRITICAL for avoiding false positives.

    Handles:
    - Field name conversion (CamelCase -> snake_case)
    - Tags format (array -> object)
    - Value normalization (booleans, empty strings)
    - Resource-specific field mapping
    """

    # AWS -> TF field name mapping
    FIELD_NAME_MAP: dict[str, str] = {
        # EC2
        "InstanceId": "id",
        "InstanceType": "instance_type",
        "ImageId": "ami",
        "SubnetId": "subnet_id",
        "VpcId": "vpc_id",
        "PrivateIpAddress": "private_ip",
        "PublicIpAddress": "public_ip",
        "SecurityGroups": "vpc_security_group_ids",
        "IamInstanceProfile": "iam_instance_profile",
        "BlockDeviceMappings": "ebs_block_device",
        # S3
        "BucketName": "bucket",
        "Versioning": "versioning",
        "ServerSideEncryptionConfiguration": "server_side_encryption_configuration",
        # RDS
        "DBInstanceIdentifier": "identifier",
        "DBInstanceClass": "instance_class",
        "Engine": "engine",
        "EngineVersion": "engine_version",
        "AllocatedStorage": "allocated_storage",
        "StorageEncrypted": "storage_encrypted",
        "PubliclyAccessible": "publicly_accessible",
        # IAM
        "RoleName": "name",
        "PolicyName": "name",
        "UserName": "name",
        "PolicyDocument": "policy",
        "AssumeRolePolicyDocument": "assume_role_policy",
        # Lambda
        "FunctionName": "function_name",
        "Runtime": "runtime",
        "Handler": "handler",
        "MemorySize": "memory_size",
        "Timeout": "timeout",
        # Security Group
        "GroupId": "id",
        "GroupName": "name",
        "IpPermissions": "ingress",
        "IpPermissionsEgress": "egress",
    }

    # Fields to always ignore in comparison
    GLOBAL_IGNORE_FIELDS: frozenset[str] = frozenset(
        {
            # IDs and ARNs (format differences)
            "id",  # Used for matching, not comparison
            "arn",
            "owner_id",
            "account_id",
            "unique_id",
            # Timestamps
            "creation_date",
            "created_at",
            "create_time",
            "launch_time",
            "last_modified",
            "last_modified_date",
            "updated_at",
            "modify_date",
            # Internal metadata
            "version",
            "serial",
            "revision",
            "etag",
            "request_id",
            "resource_id",
            # Computed/dynamic fields
            "hosted_zone_id",
            "dns_name",
            "endpoint",
            "domain_name",
            "regional_domain_name",
            "website_endpoint",
            "website_domain",
        }
    )

    # Resource-specific ignore fields
    RESOURCE_IGNORE_FIELDS: dict[str, frozenset[str]] = {
        "aws_instance": frozenset(
            {
                "primary_network_interface_id",
                "outpost_arn",
                "placement_partition_number",
                "instance_state",
                "password_data",
            }
        ),
        "aws_security_group": frozenset(
            {
                "name_prefix",
                "revoke_rules_on_delete",
            }
        ),
        "aws_s3_bucket": frozenset(
            {
                "bucket_prefix",
                "force_destroy",
                "bucket_domain_name",
                "bucket_regional_domain_name",
                "region",
                "acceleration_status",
                "request_payer",
            }
        ),
        "aws_db_instance": frozenset(
            {
                "address",
                "endpoint",
                "hosted_zone_id",
                "status",
                "latest_restorable_time",
                "replicas",
                "resource_id",
            }
        ),
        "aws_lambda_function": frozenset(
            {
                "invoke_arn",
                "last_modified",
                "qualified_arn",
                "qualified_invoke_arn",
                "signing_job_arn",
                "signing_profile_version_arn",
                "source_code_size",
                "version",
                "code_sha256",
            }
        ),
        "aws_autoscaling_group": frozenset(
            {
                # ASG auto-adjusts these - CRITICAL to ignore
                "desired_capacity",
                "default_cooldown",
                "default_instance_warmup",
            }
        ),
        "aws_ecs_service": frozenset(
            {
                # ECS auto-adjusts - CRITICAL to ignore
                "desired_count",
                "running_count",
                "pending_count",
            }
        ),
        "aws_iam_role": frozenset(
            {
                "create_date",
                "unique_id",
            }
        ),
    }

    def normalize_aws_attributes(
        self,
        resource_type: str,
        attrs: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize AWS API attributes to match TF State format."""
        normalized = {}

        for key, value in attrs.items():
            # Convert field name
            tf_key = self._normalize_field_name(key)

            # Convert value
            tf_value = self._normalize_value(tf_key, value, resource_type)

            normalized[tf_key] = tf_value

        # Ensure tags_all exists if tags exists
        if "tags" in normalized and "tags_all" not in normalized:
            normalized["tags_all"] = normalized["tags"]

        return normalized

    def _normalize_field_name(self, name: str) -> str:
        """Convert AWS CamelCase to TF snake_case."""
        if name in self.FIELD_NAME_MAP:
            return self.FIELD_NAME_MAP[name]

        # Convert CamelCase to snake_case
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _normalize_value(
        self,
        key: str,
        value: Any,
        resource_type: str,
    ) -> Any:
        """Normalize attribute value."""
        if value is None:
            return None

        # Normalize tags from AWS format to TF format
        if key in ("tags", "tags_all") and isinstance(value, list):
            return self._normalize_tags(value)

        # Normalize boolean strings
        if isinstance(value, str):
            if value.lower() == "true":
                return True
            if value.lower() == "false":
                return False

        # Normalize empty strings to None
        if value == "":
            return None

        # Normalize security group rules
        if key in ("ingress", "egress") and isinstance(value, list):
            return self._normalize_sg_rules(value)

        return value

    def _normalize_tags(self, tags: list[dict]) -> dict[str, str]:
        """Convert AWS tags [{Key, Value}] to TF format {key: value}."""
        if not isinstance(tags, list):
            return tags

        result = {}
        for tag in tags:
            if isinstance(tag, dict):
                key = tag.get("Key") or tag.get("key")
                value = tag.get("Value") or tag.get("value")
                if key:
                    result[key] = value or ""

        return result

    def _normalize_sg_rules(self, rules: list[dict]) -> list[dict]:
        """Normalize security group rules for comparison."""
        normalized = []

        for rule in rules:
            norm_rule = {
                "from_port": rule.get("from_port") or rule.get("FromPort"),
                "to_port": rule.get("to_port") or rule.get("ToPort"),
                "protocol": str(
                    rule.get("protocol") or rule.get("IpProtocol") or ""
                ).lower(),
            }

            # Normalize CIDR blocks
            cidr = rule.get("cidr_blocks") or rule.get("CidrIp")
            if cidr:
                if isinstance(cidr, str):
                    norm_rule["cidr_blocks"] = [cidr]
                else:
                    norm_rule["cidr_blocks"] = sorted(cidr)

            normalized.append(norm_rule)

        # Sort for consistent comparison
        return sorted(
            normalized,
            key=lambda x: (
                x.get("from_port") or 0,
                x.get("to_port") or 0,
                x.get("protocol") or "",
            ),
        )

    def should_ignore_field(
        self,
        resource_type: str,
        field: str,
    ) -> bool:
        """Check if a field should be ignored in comparison."""
        # Global ignore
        if field in self.GLOBAL_IGNORE_FIELDS:
            return True

        # Resource-specific ignore
        resource_ignores = self.RESOURCE_IGNORE_FIELDS.get(resource_type, frozenset())
        if field in resource_ignores:
            return True

        # Ignore internal TF fields
        if field.startswith("_") or field.startswith("timeouts"):
            return True

        # Ignore ID reference fields (usually just linking)
        if field.endswith("_id") and field not in (
            "security_group_id",
            "subnet_id",
            "vpc_id",
        ):
            return True

        return False


# ============================================================
# DRIFT FILTER (IGNORE RULES)
# ============================================================


@dataclass
class DriftIgnoreRule:
    """Rule for ignoring specific drifts."""

    resource_type: str | None = None
    resource_id: str | None = None
    field: str | None = None
    tag_prefix: str | None = None
    drift_type: DriftType | None = None
    reason: str = ""


class DriftFilter:
    """
    Filters out benign/expected drifts.

    Supports:
    - Ignoring specific resource types
    - Ignoring specific resource IDs
    - Ignoring specific fields
    - Ignoring AWS/Kubernetes managed resources
    - Custom .replimapignore file
    """

    # Default ignore rules
    DEFAULT_RULES: list[DriftIgnoreRule] = [
        # Kubernetes-managed resources
        DriftIgnoreRule(
            tag_prefix="kubernetes.io/", reason="Kubernetes-managed resource"
        ),
        DriftIgnoreRule(tag_prefix="k8s.io/", reason="Kubernetes-managed resource"),
        # AWS-managed tags
        DriftIgnoreRule(tag_prefix="aws:", reason="AWS-managed tag"),
        # Auto-scaling fields (CRITICAL - these change automatically)
        DriftIgnoreRule(
            resource_type="aws_autoscaling_group",
            field="desired_capacity",
            reason="Auto-scaling adjusts this automatically",
        ),
        DriftIgnoreRule(
            resource_type="aws_ecs_service",
            field="desired_count",
            reason="Auto-scaling adjusts this automatically",
        ),
        # Spot instance changes
        DriftIgnoreRule(
            field="spot_instance_request_id",
            reason="Spot instance allocation is dynamic",
        ),
    ]

    def __init__(
        self,
        custom_rules: list[DriftIgnoreRule] | None = None,
        include_defaults: bool = True,
    ):
        self.rules: list[DriftIgnoreRule] = []

        if include_defaults:
            self.rules.extend(self.DEFAULT_RULES)

        if custom_rules:
            self.rules.extend(custom_rules)

    @classmethod
    def from_config(cls, config_path: Path) -> DriftFilter:
        """
        Load filter rules from .replimapignore file.

        Format:
            # Comment
            aws_autoscaling_group:desired_capacity  # Ignore field
            aws_cloudwatch_log_group                # Ignore type
            i-1234567890abcdef0                     # Ignore resource
        """
        rules = list(cls.DEFAULT_RULES)

        if not config_path.exists():
            return cls(rules, include_defaults=False)

        try:
            for line in config_path.read_text().strip().split("\n"):
                line = line.strip()

                # Remove inline comments
                if "#" in line:
                    line = line[: line.index("#")].strip()

                if not line:
                    continue

                rule = cls._parse_rule_line(line)
                if rule:
                    rules.append(rule)

        except Exception as e:
            logger.warning(f"Failed to parse ignore config: {e}")

        return cls(rules, include_defaults=False)

    @staticmethod
    def _parse_rule_line(line: str) -> DriftIgnoreRule | None:
        """Parse a single line from ignore config."""
        # Format: resource_type:field
        if ":" in line:
            parts = line.split(":", 1)
            return DriftIgnoreRule(
                resource_type=parts[0] if parts[0] != "*" else None,
                field=parts[1] if len(parts) > 1 and parts[1] else None,
                reason="Custom ignore rule",
            )

        # Format: resource_type (starts with aws_)
        if line.startswith("aws_"):
            return DriftIgnoreRule(resource_type=line, reason="Custom ignore rule")

        # Format: resource_id
        return DriftIgnoreRule(resource_id=line, reason="Custom ignore rule")

    def should_ignore_finding(self, finding: DriftFinding) -> bool:
        """Check if a finding should be completely ignored."""
        for rule in self.rules:
            if self._matches_finding(finding, rule):
                return True
        return False

    def should_ignore_change(
        self,
        resource_type: str,
        resource_id: str,
        change: AttributeChange,
        tags: dict | None = None,
    ) -> bool:
        """Check if a specific attribute change should be ignored."""
        for rule in self.rules:
            # Field-specific rules
            if rule.field and rule.field == change.field:
                if rule.resource_type is None or rule.resource_type == resource_type:
                    return True

            # Tag prefix rules
            if rule.tag_prefix and tags:
                for tag_key in tags.keys():
                    if tag_key.startswith(rule.tag_prefix):
                        return True

        return False

    def _matches_finding(self, finding: DriftFinding, rule: DriftIgnoreRule) -> bool:
        """Check if a finding matches an ignore rule."""
        if rule.resource_type and rule.resource_type != finding.resource_type:
            return False

        if rule.resource_id and rule.resource_id != finding.resource_id:
            return False

        if rule.drift_type and rule.drift_type != finding.drift_type:
            return False

        # If rule has field specified, it's for changes, not full findings
        if rule.field:
            return False

        # If rule has tag_prefix, check finding's metadata tags
        if rule.tag_prefix:
            tags = finding.metadata.get("tags", {})
            if not tags:
                return False
            if not any(k.startswith(rule.tag_prefix) for k in tags.keys()):
                return False

        # Rule must have at least one positive condition to match
        # (avoid matching everything with an empty rule)
        if not any(
            [rule.resource_type, rule.resource_id, rule.drift_type, rule.tag_prefix]
        ):
            return False

        return True

    def filter_findings(self, findings: list[DriftFinding]) -> list[DriftFinding]:
        """Filter a list of findings."""
        return [f for f in findings if not self.should_ignore_finding(f)]


# ============================================================
# ATTRIBUTE COMPARATOR
# ============================================================


class AttributeComparator:
    """
    Deep comparison of attributes with severity classification.
    """

    # Security-critical fields
    SECURITY_FIELDS: frozenset[str] = frozenset(
        {
            "ingress",
            "egress",
            "cidr_blocks",
            "cidr_block",
            "ipv6_cidr_blocks",
            "source_security_group_id",
            "security_groups",
            "vpc_security_group_ids",
            "policy",
            "assume_role_policy",
            "iam_role",
            "iam_instance_profile",
            "encrypted",
            "storage_encrypted",
            "kms_key_id",
            "kms_key_arn",
            "publicly_accessible",
            "public_access_block",
            "acl",
            "block_public_acls",
            "block_public_policy",
            "ignore_public_acls",
            "restrict_public_buckets",
        }
    )

    # High-impact infrastructure fields
    INFRASTRUCTURE_FIELDS: frozenset[str] = frozenset(
        {
            "instance_type",
            "instance_class",
            "ami",
            "image_id",
            "engine",
            "engine_version",
            "allocated_storage",
            "storage_type",
            "availability_zone",
            "availability_zones",
            "subnet_id",
            "subnet_ids",
            "vpc_id",
            "root_block_device",
            "ebs_block_device",
            "launch_template",
            "runtime",
            "memory_size",
            "timeout",
        }
    )

    def __init__(self, normalizer: AttributeNormalizer):
        self.normalizer = normalizer

    def compare(
        self,
        resource_type: str,
        expected: dict[str, Any],  # From TF State
        actual: dict[str, Any],  # From AWS (normalized)
    ) -> list[AttributeChange]:
        """
        Compare expected (TF State) vs actual (AWS) attributes.

        Iterates over STATE fields (source of truth for config).
        """
        changes = []

        for field_name, expected_value in expected.items():
            # Skip ignored fields
            if self.normalizer.should_ignore_field(resource_type, field_name):
                continue

            # Get actual value
            actual_value = actual.get(field_name)

            # Compare with type coercion
            if not self._values_equal(expected_value, actual_value):
                severity = self._determine_severity(field_name)

                changes.append(
                    AttributeChange(
                        field=field_name,
                        expected=expected_value,
                        actual=actual_value,
                        severity=severity,
                    )
                )

        return changes

    def _values_equal(self, a: Any, b: Any) -> bool:
        """Deep equality check with type coercion."""
        # Handle None
        if a is None and b is None:
            return True
        if a is None or b is None:
            # Treat None and empty as equal
            empty_values = ("", [], {}, None)
            return (a in empty_values) and (b in empty_values)

        # Handle dicts
        if isinstance(a, dict) and isinstance(b, dict):
            # Allow different keys if values match for common keys
            a_keys = set(a.keys())
            b_keys = set(b.keys())
            common_keys = a_keys & b_keys

            # Only compare non-empty values
            for k in common_keys:
                if not self._values_equal(a[k], b[k]):
                    return False

            # Check if missing keys have meaningful values
            for k in a_keys - b_keys:
                if a[k] not in (None, "", [], {}):
                    return False
            for k in b_keys - a_keys:
                if b[k] not in (None, "", [], {}):
                    return False

            return True

        # Handle lists (order-insensitive for certain types)
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False

            # Try sorted comparison
            try:
                sorted_a = sorted(json.dumps(x, sort_keys=True, default=str) for x in a)
                sorted_b = sorted(json.dumps(x, sort_keys=True, default=str) for x in b)
                return sorted_a == sorted_b
            except (TypeError, ValueError):
                return a == b

        # Handle booleans vs strings
        if isinstance(a, bool) or isinstance(b, bool):
            return str(a).lower() == str(b).lower()

        # String comparison (handles number vs string)
        return str(a) == str(b)

    def _determine_severity(self, field: str) -> DriftSeverity:
        """Determine severity of a field change."""
        field_lower = field.lower()

        if field in self.SECURITY_FIELDS or field_lower in self.SECURITY_FIELDS:
            return DriftSeverity.CRITICAL

        if (
            field in self.INFRASTRUCTURE_FIELDS
            or field_lower in self.INFRASTRUCTURE_FIELDS
        ):
            return DriftSeverity.HIGH

        if "tag" in field_lower:
            return DriftSeverity.LOW

        if "description" in field_lower or "comment" in field_lower:
            return DriftSeverity.LOW

        return DriftSeverity.MEDIUM


# ============================================================
# MAIN DRIFT DETECTOR
# ============================================================


class OfflineDriftDetector:
    """
    Main drift detection engine.

    Compares AWS live state (from cached RepliMap scan) against Terraform state file.
    This is the "offline terraform plan" - doesn't require AWS connection or TF.
    """

    def __init__(
        self,
        ignore_filter: DriftFilter | None = None,
    ):
        self.loader = TerraformStateLoader()
        self.normalizer = AttributeNormalizer()
        self.comparator = AttributeComparator(self.normalizer)
        self.filter = ignore_filter or DriftFilter()

    def detect(
        self,
        live_resources: list[dict[str, Any]],
        state_path: Path,
    ) -> DriftReport:
        """
        Detect drift between live AWS resources and Terraform state.

        Args:
            live_resources: Resources from RepliMap scan
            state_path: Path to terraform.tfstate

        Returns:
            DriftReport with findings and remediation hints
        """
        findings: list[DriftFinding] = []

        # Build indexes
        live_map = self._build_live_map(live_resources)
        state_map = self.loader.load(state_path)

        logger.info(
            f"Comparing {len(live_map)} AWS resources against "
            f"{len(state_map)} Terraform resources"
        )

        live_ids = set(live_map.keys())
        state_ids = set(state_map.keys())

        # 1. UNMANAGED: In AWS, not in TF State (ghost resources)
        for resource_id in live_ids - state_ids:
            resource = live_map[resource_id]
            tags = resource.get("attributes", {}).get("tags", {})

            # Check if should ignore
            if self._should_ignore_unmanaged(resource, tags):
                continue

            findings.append(
                DriftFinding(
                    resource_id=resource_id,
                    resource_type=resource.get("type", "unknown"),
                    resource_name=resource.get("name", resource_id),
                    drift_type=DriftType.UNMANAGED,
                    severity=DriftSeverity.MEDIUM,
                    metadata={"tags": tags},
                )
            )

        # 2. MISSING: In TF State, not in AWS (deleted manually)
        for resource_id in state_ids - live_ids:
            state_resource = state_map[resource_id]

            findings.append(
                DriftFinding(
                    resource_id=resource_id,
                    resource_type=state_resource["type"],
                    resource_name=state_resource["name"],
                    drift_type=DriftType.MISSING,
                    severity=DriftSeverity.HIGH,
                    terraform_address=state_resource.get("address"),
                )
            )

        # 3. DRIFTED: In both, but configuration differs
        for resource_id in live_ids & state_ids:
            live_resource = live_map[resource_id]
            state_resource = state_map[resource_id]

            changes = self._compare_resource(live_resource, state_resource)

            # Filter changes
            tags = live_resource.get("attributes", {}).get("tags", {})
            changes = [
                c
                for c in changes
                if not self.filter.should_ignore_change(
                    state_resource["type"],
                    resource_id,
                    c,
                    tags,
                )
            ]

            if changes:
                findings.append(
                    DriftFinding(
                        resource_id=resource_id,
                        resource_type=state_resource["type"],
                        resource_name=state_resource["name"],
                        drift_type=DriftType.DRIFTED,
                        changes=changes,
                        terraform_address=state_resource.get("address"),
                    )
                )

        # Apply finding-level filter
        findings = self.filter.filter_findings(findings)

        # Build summary
        summary = self._build_summary(findings, live_map, state_map)

        return DriftReport(
            findings=findings,
            scan_timestamp=datetime.now(UTC).isoformat(),
            state_file_path=str(state_path),
            summary=summary,
        )

    def detect_from_graph(
        self,
        graph: GraphEngine,
        state_path: Path,
    ) -> DriftReport:
        """
        Detect drift using a GraphEngine directly.

        Args:
            graph: GraphEngine with scanned resources
            state_path: Path to terraform.tfstate

        Returns:
            DriftReport with findings and remediation hints
        """
        # Convert graph resources to list format
        resources = []
        for resource in graph.get_all_resources():
            resource_dict = {
                "id": resource.id,
                "type": getattr(
                    resource, "terraform_type", str(resource.resource_type)
                ),
                "name": getattr(resource, "original_name", resource.id),
                "attributes": getattr(resource, "config", {}) or {},
            }
            resources.append(resource_dict)

        return self.detect(resources, state_path)

    def _build_live_map(self, resources: list[dict]) -> dict[str, dict]:
        """Build index of live resources by ID."""
        result: dict[str, dict] = {}

        for resource in resources:
            resource_id = resource.get("id")
            if not resource_id:
                # Try attributes
                resource_id = resource.get("attributes", {}).get("id")

            if resource_id:
                result[resource_id] = resource

        return result

    def _compare_resource(
        self,
        live: dict,
        state: dict,
    ) -> list[AttributeChange]:
        """Compare a single resource."""
        resource_type = state["type"]

        # Normalize AWS attributes
        live_attrs = self.normalizer.normalize_aws_attributes(
            resource_type,
            live.get("attributes", {}),
        )

        state_attrs = state["attributes"]

        return self.comparator.compare(resource_type, state_attrs, live_attrs)

    def _should_ignore_unmanaged(
        self,
        resource: dict,
        tags: dict,
    ) -> bool:
        """Check if an unmanaged resource should be ignored."""
        # Ignore Kubernetes-managed resources
        for tag_key in tags.keys():
            if tag_key.startswith("kubernetes.io/"):
                return True
            if tag_key.startswith("k8s.io/"):
                return True

        # Could add more rules here (e.g., CloudFormation managed)
        for tag_key in tags.keys():
            if tag_key.startswith("aws:cloudformation:"):
                return True

        return False

    def _build_summary(
        self,
        findings: list[DriftFinding],
        live_map: dict,
        state_map: dict,
    ) -> dict[str, Any]:
        """Build summary statistics."""
        by_type: dict[str, int] = defaultdict(int)
        by_severity: dict[str, int] = defaultdict(int)
        by_resource_type: dict[str, int] = defaultdict(int)

        for finding in findings:
            by_type[finding.drift_type.value] += 1
            by_severity[finding.max_change_severity.value] += 1
            by_resource_type[finding.resource_type] += 1

        return {
            "live_resource_count": len(live_map),
            "state_resource_count": len(state_map),
            "total_findings": len(findings),
            "by_drift_type": dict(by_type),
            "by_severity": dict(by_severity),
            "by_resource_type": dict(sorted(by_resource_type.items())),
        }


# ============================================================
# SCAN COMPARATOR (Scan vs Previous Scan)
# ============================================================


class ScanComparator:
    """
    Compare two RepliMap scans to detect changes over time.

    Unlike Drift Detection (AWS vs TF State), this compares
    two points in time of AWS state.
    """

    def __init__(self):
        self.normalizer = AttributeNormalizer()
        self.comparator = AttributeComparator(self.normalizer)

    def compare(
        self,
        current_resources: list[dict],
        previous_resources: list[dict],
    ) -> DriftReport:
        """Compare current scan against previous scan."""
        findings: list[DriftFinding] = []

        current_map = {r.get("id"): r for r in current_resources if r.get("id")}
        previous_map = {r.get("id"): r for r in previous_resources if r.get("id")}

        current_ids = set(current_map.keys())
        previous_ids = set(previous_map.keys())

        # New resources (added since last scan)
        for rid in current_ids - previous_ids:
            resource = current_map[rid]
            findings.append(
                DriftFinding(
                    resource_id=rid,
                    resource_type=resource.get("type", "unknown"),
                    resource_name=resource.get("name", rid),
                    drift_type=DriftType.UNMANAGED,  # Reusing as "NEW"
                    severity=DriftSeverity.MEDIUM,
                    metadata={"change_type": "added"},
                )
            )

        # Removed resources (deleted since last scan)
        for rid in previous_ids - current_ids:
            resource = previous_map[rid]
            findings.append(
                DriftFinding(
                    resource_id=rid,
                    resource_type=resource.get("type", "unknown"),
                    resource_name=resource.get("name", rid),
                    drift_type=DriftType.MISSING,  # Reusing as "REMOVED"
                    severity=DriftSeverity.HIGH,
                    metadata={"change_type": "removed"},
                )
            )

        # Modified resources
        for rid in current_ids & previous_ids:
            current = current_map[rid]
            previous = previous_map[rid]

            resource_type = current.get("type", "unknown")

            current_attrs = self.normalizer.normalize_aws_attributes(
                resource_type, current.get("attributes", {})
            )
            previous_attrs = self.normalizer.normalize_aws_attributes(
                resource_type, previous.get("attributes", {})
            )

            changes = self.comparator.compare(
                resource_type, previous_attrs, current_attrs
            )

            if changes:
                findings.append(
                    DriftFinding(
                        resource_id=rid,
                        resource_type=resource_type,
                        resource_name=current.get("name", rid),
                        drift_type=DriftType.DRIFTED,
                        changes=changes,
                        metadata={"change_type": "modified"},
                    )
                )

        return DriftReport(
            findings=findings,
            scan_timestamp=datetime.now(UTC).isoformat(),
            state_file_path="previous_scan",
            summary={
                "current_count": len(current_resources),
                "previous_count": len(previous_resources),
                "added": len(current_ids - previous_ids),
                "removed": len(previous_ids - current_ids),
                "modified": sum(
                    1 for f in findings if f.drift_type == DriftType.DRIFTED
                ),
            },
        )

    def compare_from_graphs(
        self,
        current_graph: GraphEngine,
        previous_graph: GraphEngine,
    ) -> DriftReport:
        """
        Compare two GraphEngine instances.

        Args:
            current_graph: Current scan
            previous_graph: Previous scan

        Returns:
            DriftReport with changes between scans
        """

        def graph_to_list(graph: GraphEngine) -> list[dict]:
            resources = []
            for resource in graph.get_all_resources():
                resource_dict = {
                    "id": resource.id,
                    "type": getattr(
                        resource, "terraform_type", str(resource.resource_type)
                    ),
                    "name": getattr(resource, "original_name", resource.id),
                    "attributes": getattr(resource, "config", {}) or {},
                }
                resources.append(resource_dict)
            return resources

        current = graph_to_list(current_graph)
        previous = graph_to_list(previous_graph)

        return self.compare(current, previous)
