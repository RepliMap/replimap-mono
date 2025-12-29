"""
Resource Dependency Analyzers.

Each analyzer knows how to find dependencies for a specific resource type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from replimap.deps.base_analyzer import ResourceDependencyAnalyzer

# Import analyzers
from replimap.deps.analyzers.ec2 import EC2Analyzer
from replimap.deps.analyzers.iam_role import IAMRoleAnalyzer
from replimap.deps.analyzers.security_group import SecurityGroupAnalyzer

# Analyzer registry
ANALYZERS: dict[str, type[ResourceDependencyAnalyzer]] = {
    # EC2 Instance
    "aws_instance": EC2Analyzer,
    "i-": EC2Analyzer,  # ID prefix shortcut
    # Security Group
    "aws_security_group": SecurityGroupAnalyzer,
    "sg-": SecurityGroupAnalyzer,
    # IAM Role
    "aws_iam_role": IAMRoleAnalyzer,
}


def get_analyzer(
    resource_id_or_type: str,
    **clients,
) -> ResourceDependencyAnalyzer:
    """
    Get the appropriate analyzer for a resource.

    Args:
        resource_id_or_type: Resource ID (i-xxx, sg-xxx) or type (aws_instance)
        **clients: AWS client instances (ec2_client, rds_client, etc.)

    Returns:
        Instantiated analyzer

    Raises:
        ValueError: If resource type is not supported
    """
    # Try exact match first
    if resource_id_or_type in ANALYZERS:
        return ANALYZERS[resource_id_or_type](**clients)

    # Try prefix match
    for prefix, analyzer_cls in ANALYZERS.items():
        if resource_id_or_type.startswith(prefix):
            return analyzer_cls(**clients)

    raise ValueError(f"Unsupported resource: {resource_id_or_type}")


__all__ = [
    "ANALYZERS",
    "get_analyzer",
    "EC2Analyzer",
    "SecurityGroupAnalyzer",
    "IAMRoleAnalyzer",
]
