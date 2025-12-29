"""
Core models for Dependency Analysis Framework.

Defines the relationship types, severity levels, and data structures
for comprehensive AWS resource dependency analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RelationType(str, Enum):
    """Types of relationships between resources."""

    # Controls this resource's lifecycle
    MANAGER = "manager"  # ASG → EC2, CloudFormation → *

    # Resources that depend on this one (upstream blast radius)
    CONSUMER = "consumer"  # EC2 → SG, Lambda → IAM Role

    # Resources this one depends on (downstream)
    DEPENDENCY = "dependency"  # EC2 → VPC, RDS → Subnet Group

    # Resources managed by this one
    MANAGED = "managed"  # ASG → EC2 instances

    # Network context
    NETWORK = "network"  # VPC, Subnet, AZ

    # Permission/identity context
    IDENTITY = "identity"  # IAM Role, KMS Key

    # Trust relationships (IAM specific)
    TRUST = "trust"  # Who can assume a role

    # Replication relationships
    REPLICATION = "replication"  # RDS replicas, S3 cross-region

    # Event triggers
    TRIGGER = "trigger"  # S3 → Lambda, CloudWatch → Lambda

    def __str__(self) -> str:
        return self.value


class Severity(str, Enum):
    """Impact severity levels for dependencies."""

    # Deletion/modification will immediately break things
    CRITICAL = "critical"

    # Modification requires careful planning
    HIGH = "high"

    # Should be aware of
    MEDIUM = "medium"

    # Informational
    INFO = "info"

    def __str__(self) -> str:
        return self.value


class ResourceCriticality(Enum):
    """Resource criticality weights for blast radius calculation."""

    # Data layer - most important
    DATABASE = 10  # RDS, Aurora, DynamoDB
    CACHE = 8  # ElastiCache, DAX
    STORAGE = 7  # S3 (if data source)

    # Compute layer
    CONTAINER = 7  # ECS, EKS
    COMPUTE = 5  # EC2, Lambda

    # Network layer
    LOAD_BALANCER = 8  # ALB, NLB (entry points)
    API_GATEWAY = 8  # API Gateway (entry points)

    # Security layer
    IAM_ROLE = 8  # IAM Role (permissions)
    KMS_KEY = 9  # KMS (encryption)

    # Infrastructure
    SECURITY_GROUP = 6  # SG
    NETWORK = 3  # VPC, Subnet

    # Other
    DEFAULT = 4


# Resource type to criticality mapping
RESOURCE_WEIGHTS: dict[str, ResourceCriticality] = {
    "aws_db_instance": ResourceCriticality.DATABASE,
    "aws_rds_cluster": ResourceCriticality.DATABASE,
    "aws_dynamodb_table": ResourceCriticality.DATABASE,
    "aws_elasticache_cluster": ResourceCriticality.CACHE,
    "aws_elasticache_replication_group": ResourceCriticality.CACHE,
    "aws_instance": ResourceCriticality.COMPUTE,
    "aws_lambda_function": ResourceCriticality.COMPUTE,
    "aws_ecs_service": ResourceCriticality.CONTAINER,
    "aws_eks_cluster": ResourceCriticality.CONTAINER,
    "aws_lb": ResourceCriticality.LOAD_BALANCER,
    "aws_api_gateway_rest_api": ResourceCriticality.API_GATEWAY,
    "aws_iam_role": ResourceCriticality.IAM_ROLE,
    "aws_kms_key": ResourceCriticality.KMS_KEY,
    "aws_security_group": ResourceCriticality.SECURITY_GROUP,
    "aws_s3_bucket": ResourceCriticality.STORAGE,
    "aws_vpc": ResourceCriticality.NETWORK,
    "aws_subnet": ResourceCriticality.NETWORK,
}


@dataclass
class Dependency:
    """A dependency relationship to another resource."""

    resource_type: str  # aws_instance, aws_security_group, etc.
    resource_id: str  # i-xxx, sg-xxx, etc.
    relation_type: RelationType
    severity: Severity
    resource_name: str | None = None  # Friendly name
    warning: str | None = None  # Special warning message
    children: list[Dependency] = field(default_factory=list)  # Nested dependencies
    metadata: dict[str, Any] = field(default_factory=dict)  # Extra info

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "relation_type": self.relation_type.value,
            "severity": self.severity.value,
            "warning": self.warning,
        }
        if self.children:
            result["children"] = [c.to_dict() for c in self.children]
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass
class BlastRadiusScore:
    """Blast radius impact score."""

    score: int  # 0-100
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    affected_count: int  # Total resources affected
    weighted_impact: int  # Sum of weighted impacts
    breakdown: dict[str, dict[str, int]]  # By resource type
    summary: str  # Human-readable summary

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "affected_count": self.affected_count,
            "weighted_impact": self.weighted_impact,
            "breakdown": self.breakdown,
            "summary": self.summary,
        }


@dataclass
class DependencyAnalysis:
    """Complete dependency analysis result."""

    # The resource being analyzed
    center_resource: Dependency

    # Dependencies grouped by relation type
    dependencies: dict[RelationType, list[Dependency]] = field(default_factory=dict)

    # Warnings and recommendations
    warnings: list[str] = field(default_factory=list)

    # Blast radius assessment
    blast_radius: BlastRadiusScore | None = None

    # Additional context (VPC, Subnet, AZ, etc.)
    context: dict[str, Any] = field(default_factory=dict)

    # IaC management status
    iac_status: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "center_resource": self.center_resource.to_dict(),
            "dependencies": {
                k.value: [d.to_dict() for d in v] for k, v in self.dependencies.items()
            },
            "warnings": self.warnings,
            "blast_radius": self.blast_radius.to_dict() if self.blast_radius else None,
            "context": self.context,
            "iac_status": self.iac_status,
        }

    def get_all_consumers(self) -> list[Dependency]:
        """Get all consumer dependencies."""
        return self.dependencies.get(RelationType.CONSUMER, [])

    def get_total_affected_count(self) -> int:
        """Get total count of affected resources."""
        count = 0
        for deps in self.dependencies.values():
            for dep in deps:
                count += 1
                count += len(dep.children)
        return count
