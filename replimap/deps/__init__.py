"""
Dependency Analysis Framework.

Provides comprehensive dependency analysis for AWS resources with:
- MANAGER: Resources controlling lifecycle (ASG, CloudFormation)
- CONSUMERS: Resources that depend on this one (upstream blast radius)
- DEPENDENCIES: Resources this one depends on (downstream)
- NETWORK: Network context (VPC, Subnet, SG)
- IDENTITY: Permission context (IAM Role, KMS Key)
"""

from replimap.deps.models import (
    RelationType,
    Severity,
    Dependency,
    DependencyAnalysis,
    BlastRadiusScore,
)
from replimap.deps.analyzers import get_analyzer, ANALYZERS
from replimap.deps.blast_radius import calculate_blast_radius

__all__ = [
    "RelationType",
    "Severity",
    "Dependency",
    "DependencyAnalysis",
    "BlastRadiusScore",
    "get_analyzer",
    "ANALYZERS",
    "calculate_blast_radius",
]
