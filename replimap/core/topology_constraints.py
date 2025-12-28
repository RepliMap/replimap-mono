"""
Topology Constraints Configuration for RepliMap.

Provides policy-based infrastructure validation:
- Prohibit cross-region direct access rules
- Allowed/prohibited relationship types
- Violation detection and alerting
- YAML configuration support

This enables infrastructure governance by defining
what relationships and patterns are acceptable.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from replimap.graph.visualizer import GraphNode, VisualizationGraph

logger = logging.getLogger(__name__)


class ViolationSeverity(str, Enum):
    """Severity levels for constraint violations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    def __str__(self) -> str:
        return self.value


class ConstraintType(str, Enum):
    """Types of topology constraints."""

    # Relationship constraints
    PROHIBIT_RELATIONSHIP = "prohibit_relationship"
    REQUIRE_RELATIONSHIP = "require_relationship"
    LIMIT_RELATIONSHIP_COUNT = "limit_relationship_count"

    # Cross-region constraints
    PROHIBIT_CROSS_REGION = "prohibit_cross_region"
    REQUIRE_CROSS_REGION = "require_cross_region"

    # Resource constraints
    REQUIRE_TAG = "require_tag"
    PROHIBIT_RESOURCE_TYPE = "prohibit_resource_type"
    REQUIRE_ENCRYPTION = "require_encryption"

    # Network constraints
    PROHIBIT_PUBLIC_ACCESS = "prohibit_public_access"
    REQUIRE_VPC_ENDPOINT = "require_vpc_endpoint"

    def __str__(self) -> str:
        return self.value


@dataclass
class TopologyConstraint:
    """
    A single topology constraint rule.

    Defines what relationships or configurations are
    allowed or prohibited in the infrastructure.
    """

    name: str
    constraint_type: ConstraintType
    severity: ViolationSeverity = ViolationSeverity.MEDIUM
    description: str = ""
    enabled: bool = True

    # For relationship constraints
    source_type: str | None = None
    target_type: str | None = None
    relationship_type: str | None = None

    # For cross-region constraints
    allowed_regions: list[str] = field(default_factory=list)
    prohibited_regions: list[str] = field(default_factory=list)
    same_region_only: bool = False

    # For resource constraints
    resource_types: list[str] = field(default_factory=list)
    required_tags: dict[str, str | None] = field(default_factory=dict)

    # For pattern matching
    source_pattern: str | None = None
    target_pattern: str | None = None

    # Exceptions
    exceptions: list[str] = field(default_factory=list)

    def matches_source(self, resource_type: str) -> bool:
        """Check if a resource type matches the source pattern."""
        if not self.source_type and not self.source_pattern:
            return True
        if self.source_type and resource_type == self.source_type:
            return True
        if self.source_pattern:
            return bool(re.match(self.source_pattern, resource_type))
        return False

    def matches_target(self, resource_type: str) -> bool:
        """Check if a resource type matches the target pattern."""
        if not self.target_type and not self.target_pattern:
            return True
        if self.target_type and resource_type == self.target_type:
            return True
        if self.target_pattern:
            return bool(re.match(self.target_pattern, resource_type))
        return False

    def is_exception(self, resource_id: str) -> bool:
        """Check if a resource is in the exception list."""
        return resource_id in self.exceptions

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "constraint_type": self.constraint_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "enabled": self.enabled,
            "source_type": self.source_type,
            "target_type": self.target_type,
            "relationship_type": self.relationship_type,
            "allowed_regions": self.allowed_regions,
            "prohibited_regions": self.prohibited_regions,
            "same_region_only": self.same_region_only,
            "resource_types": self.resource_types,
            "required_tags": self.required_tags,
            "source_pattern": self.source_pattern,
            "target_pattern": self.target_pattern,
            "exceptions": self.exceptions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TopologyConstraint:
        """Create from dictionary."""
        return cls(
            name=data["name"],
            constraint_type=ConstraintType(data["constraint_type"]),
            severity=ViolationSeverity(data.get("severity", "medium")),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            source_type=data.get("source_type"),
            target_type=data.get("target_type"),
            relationship_type=data.get("relationship_type"),
            allowed_regions=data.get("allowed_regions", []),
            prohibited_regions=data.get("prohibited_regions", []),
            same_region_only=data.get("same_region_only", False),
            resource_types=data.get("resource_types", []),
            required_tags=data.get("required_tags", {}),
            source_pattern=data.get("source_pattern"),
            target_pattern=data.get("target_pattern"),
            exceptions=data.get("exceptions", []),
        )


@dataclass
class ConstraintViolation:
    """A violation of a topology constraint."""

    constraint: TopologyConstraint
    resource_id: str
    resource_type: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    related_resource_id: str | None = None
    related_resource_type: str | None = None

    @property
    def severity(self) -> ViolationSeverity:
        """Get violation severity from constraint."""
        return self.constraint.severity

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "constraint_name": self.constraint.name,
            "constraint_type": self.constraint.constraint_type.value,
            "severity": self.severity.value,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "message": self.message,
            "details": self.details,
            "related_resource_id": self.related_resource_id,
            "related_resource_type": self.related_resource_type,
        }


@dataclass
class ValidationResult:
    """Result of topology validation."""

    violations: list[ConstraintViolation] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    resources_checked: int = 0
    constraints_evaluated: int = 0

    @property
    def is_valid(self) -> bool:
        """Check if validation passed (no critical/high violations)."""
        for v in self.violations:
            if v.severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH):
                return False
        return True

    @property
    def critical_count(self) -> int:
        """Count of critical violations."""
        return len(
            [v for v in self.violations if v.severity == ViolationSeverity.CRITICAL]
        )

    @property
    def high_count(self) -> int:
        """Count of high severity violations."""
        return len([v for v in self.violations if v.severity == ViolationSeverity.HIGH])

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "is_valid": self.is_valid,
            "violations": [v.to_dict() for v in self.violations],
            "warnings": self.warnings,
            "summary": {
                "total_violations": len(self.violations),
                "critical": self.critical_count,
                "high": self.high_count,
                "resources_checked": self.resources_checked,
                "constraints_evaluated": self.constraints_evaluated,
            },
        }


@dataclass
class TopologyConstraintsConfig:
    """
    Configuration for topology constraints.

    Loaded from replimap.yaml or programmatically configured.
    """

    constraints: list[TopologyConstraint] = field(default_factory=list)
    global_settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def enabled_constraints(self) -> list[TopologyConstraint]:
        """Get only enabled constraints."""
        return [c for c in self.constraints if c.enabled]

    def get_constraints_by_type(
        self,
        constraint_type: ConstraintType,
    ) -> list[TopologyConstraint]:
        """Get constraints of a specific type."""
        return [
            c for c in self.enabled_constraints if c.constraint_type == constraint_type
        ]

    def add_constraint(self, constraint: TopologyConstraint) -> None:
        """Add a constraint."""
        self.constraints.append(constraint)

    def remove_constraint(self, name: str) -> bool:
        """Remove a constraint by name."""
        for i, c in enumerate(self.constraints):
            if c.name == name:
                self.constraints.pop(i)
                return True
        return False

    @classmethod
    def from_yaml(cls, path: str | Path) -> TopologyConstraintsConfig:
        """Load configuration from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data.get("topology_constraints", {}))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TopologyConstraintsConfig:
        """Create from dictionary."""
        constraints = [
            TopologyConstraint.from_dict(c) for c in data.get("constraints", [])
        ]

        return cls(
            constraints=constraints,
            global_settings=data.get("global_settings", {}),
            metadata=data.get("metadata", {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "constraints": [c.to_dict() for c in self.constraints],
            "global_settings": self.global_settings,
            "metadata": self.metadata,
        }

    def to_yaml(self, path: str | Path) -> None:
        """Save configuration to YAML file."""
        with open(path, "w") as f:
            yaml.dump(
                {"topology_constraints": self.to_dict()}, f, default_flow_style=False
            )


class TopologyValidator:
    """
    Validates infrastructure against topology constraints.

    Checks graphs against defined constraints and reports violations.
    """

    def __init__(self, config: TopologyConstraintsConfig) -> None:
        """
        Initialize the validator.

        Args:
            config: Topology constraints configuration
        """
        self.config = config

    def validate(self, graph: VisualizationGraph) -> ValidationResult:
        """
        Validate a graph against all constraints.

        Args:
            graph: Infrastructure graph to validate

        Returns:
            ValidationResult with all violations found
        """
        violations: list[ConstraintViolation] = []
        warnings: list[str] = []

        # Build lookup maps
        nodes_by_id: dict[str, GraphNode] = {n.id: n for n in graph.nodes}
        nodes_by_type: dict[str, list[GraphNode]] = {}
        for node in graph.nodes:
            if node.resource_type not in nodes_by_type:
                nodes_by_type[node.resource_type] = []
            nodes_by_type[node.resource_type].append(node)

        # Check each constraint
        for constraint in self.config.enabled_constraints:
            try:
                constraint_violations = self._check_constraint(
                    constraint, graph, nodes_by_id, nodes_by_type
                )
                violations.extend(constraint_violations)
            except Exception as e:
                warnings.append(f"Error checking constraint '{constraint.name}': {e}")

        return ValidationResult(
            violations=violations,
            warnings=warnings,
            resources_checked=len(graph.nodes),
            constraints_evaluated=len(self.config.enabled_constraints),
        )

    def _check_constraint(
        self,
        constraint: TopologyConstraint,
        graph: VisualizationGraph,
        nodes_by_id: dict[str, GraphNode],
        nodes_by_type: dict[str, list[GraphNode]],
    ) -> list[ConstraintViolation]:
        """Check a single constraint against the graph."""
        violations: list[ConstraintViolation] = []

        if constraint.constraint_type == ConstraintType.PROHIBIT_RELATIONSHIP:
            violations.extend(
                self._check_prohibit_relationship(constraint, graph, nodes_by_id)
            )
        elif constraint.constraint_type == ConstraintType.PROHIBIT_CROSS_REGION:
            violations.extend(
                self._check_prohibit_cross_region(constraint, graph, nodes_by_id)
            )
        elif constraint.constraint_type == ConstraintType.REQUIRE_TAG:
            violations.extend(self._check_require_tag(constraint, graph.nodes))
        elif constraint.constraint_type == ConstraintType.PROHIBIT_PUBLIC_ACCESS:
            violations.extend(
                self._check_prohibit_public_access(constraint, graph.nodes)
            )
        elif constraint.constraint_type == ConstraintType.REQUIRE_ENCRYPTION:
            violations.extend(self._check_require_encryption(constraint, graph.nodes))

        return violations

    def _check_prohibit_relationship(
        self,
        constraint: TopologyConstraint,
        graph: VisualizationGraph,
        nodes_by_id: dict[str, GraphNode],
    ) -> list[ConstraintViolation]:
        """Check for prohibited relationships."""
        violations: list[ConstraintViolation] = []

        for edge in graph.edges:
            source_node = nodes_by_id.get(edge.source)
            target_node = nodes_by_id.get(edge.target)

            if not source_node or not target_node:
                continue

            # Check if this edge matches the prohibited pattern
            if not constraint.matches_source(source_node.resource_type):
                continue
            if not constraint.matches_target(target_node.resource_type):
                continue

            # Check relationship type if specified
            if constraint.relationship_type:
                if (
                    edge.edge_type != constraint.relationship_type
                    and edge.label != constraint.relationship_type
                ):
                    continue

            # Check exceptions
            if constraint.is_exception(source_node.id) or constraint.is_exception(
                target_node.id
            ):
                continue

            violations.append(
                ConstraintViolation(
                    constraint=constraint,
                    resource_id=source_node.id,
                    resource_type=source_node.resource_type,
                    message=f"Prohibited relationship from {source_node.resource_type} to {target_node.resource_type}",
                    details={
                        "relationship_type": edge.edge_type,
                        "edge_label": edge.label,
                    },
                    related_resource_id=target_node.id,
                    related_resource_type=target_node.resource_type,
                )
            )

        return violations

    def _check_prohibit_cross_region(
        self,
        constraint: TopologyConstraint,
        graph: VisualizationGraph,
        nodes_by_id: dict[str, GraphNode],
    ) -> list[ConstraintViolation]:
        """Check for prohibited cross-region relationships."""
        violations: list[ConstraintViolation] = []

        for edge in graph.edges:
            source_node = nodes_by_id.get(edge.source)
            target_node = nodes_by_id.get(edge.target)

            if not source_node or not target_node:
                continue

            source_region = source_node.properties.get("region", "unknown")
            target_region = target_node.properties.get("region", "unknown")

            # Skip if same region
            if source_region == target_region:
                continue

            # Check if source matches the constraint
            if not constraint.matches_source(source_node.resource_type):
                continue

            # Check for same_region_only constraint
            if constraint.same_region_only:
                # Check exceptions
                if constraint.is_exception(source_node.id) or constraint.is_exception(
                    target_node.id
                ):
                    continue

                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        resource_id=source_node.id,
                        resource_type=source_node.resource_type,
                        message=f"Cross-region relationship not allowed for {source_node.resource_type}",
                        details={
                            "source_region": source_region,
                            "target_region": target_region,
                        },
                        related_resource_id=target_node.id,
                        related_resource_type=target_node.resource_type,
                    )
                )

            # Check for prohibited regions
            if target_region in constraint.prohibited_regions:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        resource_id=source_node.id,
                        resource_type=source_node.resource_type,
                        message=f"Relationship to prohibited region {target_region}",
                        details={
                            "source_region": source_region,
                            "target_region": target_region,
                            "prohibited_regions": constraint.prohibited_regions,
                        },
                        related_resource_id=target_node.id,
                        related_resource_type=target_node.resource_type,
                    )
                )

        return violations

    def _check_require_tag(
        self,
        constraint: TopologyConstraint,
        nodes: list[GraphNode],
    ) -> list[ConstraintViolation]:
        """Check for required tags."""
        violations: list[ConstraintViolation] = []

        for node in nodes:
            # Check if this resource type should be checked
            if (
                constraint.resource_types
                and node.resource_type not in constraint.resource_types
            ):
                continue

            # Check exceptions
            if constraint.is_exception(node.id):
                continue

            tags = node.properties.get("tags", {})
            if not isinstance(tags, dict):
                tags = {}

            for required_tag, required_value in constraint.required_tags.items():
                if required_tag not in tags:
                    violations.append(
                        ConstraintViolation(
                            constraint=constraint,
                            resource_id=node.id,
                            resource_type=node.resource_type,
                            message=f"Missing required tag: {required_tag}",
                            details={"missing_tag": required_tag},
                        )
                    )
                elif (
                    required_value is not None
                    and tags.get(required_tag) != required_value
                ):
                    violations.append(
                        ConstraintViolation(
                            constraint=constraint,
                            resource_id=node.id,
                            resource_type=node.resource_type,
                            message=f"Tag '{required_tag}' has wrong value",
                            details={
                                "tag": required_tag,
                                "expected": required_value,
                                "actual": tags.get(required_tag),
                            },
                        )
                    )

        return violations

    def _check_prohibit_public_access(
        self,
        constraint: TopologyConstraint,
        nodes: list[GraphNode],
    ) -> list[ConstraintViolation]:
        """Check for prohibited public access."""
        violations: list[ConstraintViolation] = []

        for node in nodes:
            # Check if this resource type should be checked
            if (
                constraint.resource_types
                and node.resource_type not in constraint.resource_types
            ):
                continue

            # Check exceptions
            if constraint.is_exception(node.id):
                continue

            props = node.properties

            # Check various public access indicators
            is_public = False
            reason = ""

            # S3 public access
            if node.resource_type == "aws_s3_bucket":
                acl = props.get("acl", "")
                if acl in ("public-read", "public-read-write"):
                    is_public = True
                    reason = f"Bucket has public ACL: {acl}"

            # RDS public access
            elif node.resource_type in ("aws_db_instance", "aws_rds_cluster"):
                if props.get("publicly_accessible", False):
                    is_public = True
                    reason = "Database is publicly accessible"

            # EC2 public IP
            elif node.resource_type == "aws_instance":
                if props.get("associate_public_ip_address", False):
                    is_public = True
                    reason = "Instance has public IP address"

            # Security group 0.0.0.0/0
            elif node.resource_type == "aws_security_group":
                ingress = props.get("ingress", [])
                for rule in ingress if isinstance(ingress, list) else []:
                    cidrs = rule.get("cidr_blocks", [])
                    if "0.0.0.0/0" in cidrs:
                        is_public = True
                        reason = "Security group allows ingress from 0.0.0.0/0"
                        break

            if is_public:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        resource_id=node.id,
                        resource_type=node.resource_type,
                        message=f"Public access detected: {reason}",
                        details={"reason": reason},
                    )
                )

        return violations

    def _check_require_encryption(
        self,
        constraint: TopologyConstraint,
        nodes: list[GraphNode],
    ) -> list[ConstraintViolation]:
        """Check for required encryption."""
        violations: list[ConstraintViolation] = []

        for node in nodes:
            # Check if this resource type should be checked
            if (
                constraint.resource_types
                and node.resource_type not in constraint.resource_types
            ):
                continue

            # Check exceptions
            if constraint.is_exception(node.id):
                continue

            props = node.properties
            is_encrypted = True
            reason = ""

            # S3 bucket encryption
            if node.resource_type == "aws_s3_bucket":
                server_side = props.get("server_side_encryption_configuration")
                if not server_side:
                    is_encrypted = False
                    reason = "No server-side encryption configured"

            # EBS volume encryption
            elif node.resource_type == "aws_ebs_volume":
                if not props.get("encrypted", False):
                    is_encrypted = False
                    reason = "Volume is not encrypted"

            # RDS encryption
            elif node.resource_type in ("aws_db_instance", "aws_rds_cluster"):
                if not props.get("storage_encrypted", False):
                    is_encrypted = False
                    reason = "Database storage is not encrypted"

            # EFS encryption
            elif node.resource_type == "aws_efs_file_system":
                if not props.get("encrypted", False):
                    is_encrypted = False
                    reason = "File system is not encrypted"

            if not is_encrypted:
                violations.append(
                    ConstraintViolation(
                        constraint=constraint,
                        resource_id=node.id,
                        resource_type=node.resource_type,
                        message=f"Encryption not enabled: {reason}",
                        details={"reason": reason},
                    )
                )

        return violations


def load_constraints_from_yaml(path: str | Path) -> TopologyConstraintsConfig:
    """Load topology constraints from a YAML file."""
    return TopologyConstraintsConfig.from_yaml(path)


def validate_topology(
    graph: VisualizationGraph,
    config: TopologyConstraintsConfig,
) -> ValidationResult:
    """
    Validate a graph against topology constraints.

    Args:
        graph: Graph to validate
        config: Constraints configuration

    Returns:
        ValidationResult with violations
    """
    validator = TopologyValidator(config)
    return validator.validate(graph)


def create_default_constraints() -> TopologyConstraintsConfig:
    """Create a default set of recommended constraints."""
    constraints = [
        TopologyConstraint(
            name="require-environment-tag",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.MEDIUM,
            description="All resources should have an Environment tag",
            required_tags={"Environment": None},
        ),
        TopologyConstraint(
            name="require-owner-tag",
            constraint_type=ConstraintType.REQUIRE_TAG,
            severity=ViolationSeverity.LOW,
            description="All resources should have an Owner tag",
            required_tags={"Owner": None},
        ),
        TopologyConstraint(
            name="no-public-rds",
            constraint_type=ConstraintType.PROHIBIT_PUBLIC_ACCESS,
            severity=ViolationSeverity.CRITICAL,
            description="RDS instances should not be publicly accessible",
            resource_types=["aws_db_instance", "aws_rds_cluster"],
        ),
        TopologyConstraint(
            name="require-s3-encryption",
            constraint_type=ConstraintType.REQUIRE_ENCRYPTION,
            severity=ViolationSeverity.HIGH,
            description="S3 buckets should have encryption enabled",
            resource_types=["aws_s3_bucket"],
        ),
        TopologyConstraint(
            name="require-ebs-encryption",
            constraint_type=ConstraintType.REQUIRE_ENCRYPTION,
            severity=ViolationSeverity.HIGH,
            description="EBS volumes should be encrypted",
            resource_types=["aws_ebs_volume"],
        ),
    ]

    return TopologyConstraintsConfig(constraints=constraints)


def generate_sample_config_yaml() -> str:
    """Generate a sample YAML configuration."""
    sample = {
        "topology_constraints": {
            "global_settings": {
                "fail_on_critical": True,
                "fail_on_high": False,
            },
            "constraints": [
                {
                    "name": "require-environment-tag",
                    "constraint_type": "require_tag",
                    "severity": "medium",
                    "description": "All resources should have an Environment tag",
                    "required_tags": {"Environment": None},
                },
                {
                    "name": "no-cross-region-db-access",
                    "constraint_type": "prohibit_cross_region",
                    "severity": "high",
                    "description": "Database access should not cross regions",
                    "source_type": "aws_instance",
                    "target_pattern": "aws_(db_instance|rds_cluster)",
                    "same_region_only": True,
                },
                {
                    "name": "no-public-rds",
                    "constraint_type": "prohibit_public_access",
                    "severity": "critical",
                    "description": "RDS instances should not be publicly accessible",
                    "resource_types": ["aws_db_instance", "aws_rds_cluster"],
                },
                {
                    "name": "require-s3-encryption",
                    "constraint_type": "require_encryption",
                    "severity": "high",
                    "description": "S3 buckets should have encryption enabled",
                    "resource_types": ["aws_s3_bucket"],
                },
            ],
        }
    }

    return yaml.dump(sample, default_flow_style=False)
