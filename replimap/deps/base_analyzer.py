"""
Base Analyzer Class.

Abstract base class for resource-specific dependency analyzers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from replimap.deps.models import (
    Dependency,
    DependencyAnalysis,
    RelationType,
    Severity,
)
from replimap.deps.blast_radius import calculate_blast_radius


class ResourceDependencyAnalyzer(ABC):
    """
    Base class for resource dependency analyzers.

    Each resource type (EC2, SG, IAM Role, etc.) has its own
    analyzer that knows how to find its dependencies.
    """

    def __init__(
        self,
        ec2_client: Any = None,
        rds_client: Any = None,
        iam_client: Any = None,
        lambda_client: Any = None,
        elbv2_client: Any = None,
        autoscaling_client: Any = None,
        elasticache_client: Any = None,
        sts_client: Any = None,
    ):
        """Initialize with AWS clients."""
        self.ec2 = ec2_client
        self.rds = rds_client
        self.iam = iam_client
        self.lambda_client = lambda_client
        self.elbv2 = elbv2_client
        self.autoscaling = autoscaling_client
        self.elasticache = elasticache_client
        self.sts = sts_client
        self._current_account_id: str | None = None

    @property
    @abstractmethod
    def resource_type(self) -> str:
        """Resource type identifier (e.g., 'aws_instance')."""
        pass

    @abstractmethod
    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """
        Analyze dependencies for a resource.

        Args:
            resource_id: The AWS resource ID
            region: AWS region

        Returns:
            Complete DependencyAnalysis
        """
        pass

    @abstractmethod
    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """
        Get raw AWS API data for the resource.

        Args:
            resource_id: The AWS resource ID

        Returns:
            Raw API response data
        """
        pass

    def get_current_account_id(self) -> str:
        """Get the current AWS account ID."""
        if self._current_account_id is None and self.sts:
            identity = self.sts.get_caller_identity()
            self._current_account_id = identity["Account"]
        return self._current_account_id or "unknown"

    def _build_analysis(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        context: dict[str, Any] | None = None,
        iac_status: dict[str, Any] | None = None,
    ) -> DependencyAnalysis:
        """
        Build a complete DependencyAnalysis with blast radius.

        Args:
            center: The center resource
            dependencies: Grouped dependencies
            context: Additional context (VPC, Subnet, etc.)
            iac_status: IaC management status

        Returns:
            Complete DependencyAnalysis
        """
        # Calculate blast radius
        blast_radius = calculate_blast_radius(dependencies)

        # Generate warnings
        warnings = self._generate_warnings(center, dependencies, blast_radius)

        return DependencyAnalysis(
            center_resource=center,
            dependencies=dependencies,
            warnings=warnings,
            blast_radius=blast_radius,
            context=context or {},
            iac_status=iac_status or {},
        )

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings based on analysis."""
        warnings = []

        # Manager warnings
        managers = dependencies.get(RelationType.MANAGER, [])
        for manager in managers:
            if manager.warning:
                warnings.append(manager.warning)

        # High blast radius warning
        if blast_radius and blast_radius.level in ("CRITICAL", "HIGH"):
            warnings.append(
                f"High blast radius: {blast_radius.summary}. "
                "Review all affected resources before making changes."
            )

        # Cross-account warnings from trust relationships
        trust = dependencies.get(RelationType.TRUST, [])
        for t in trust:
            if t.severity == Severity.CRITICAL and t.warning:
                warnings.append(t.warning)

        return warnings

    def _detect_iac_status(self, tags: dict[str, str]) -> dict[str, Any]:
        """
        Detect IaC management status from tags.

        Args:
            tags: Resource tags

        Returns:
            Dict with IaC status info
        """
        status: dict[str, Any] = {
            "managed": False,
            "tool": None,
            "stack": None,
            "signs_of_manual_modification": [],
        }

        # CloudFormation
        if "aws:cloudformation:stack-name" in tags:
            status["managed"] = True
            status["tool"] = "cloudformation"
            status["stack"] = tags["aws:cloudformation:stack-name"]

            # Check for non-CFN tags (sign of manual modification)
            non_cfn_tags = [k for k in tags if not k.startswith("aws:")]
            if non_cfn_tags:
                status["signs_of_manual_modification"].append(
                    "Has non-CloudFormation tags"
                )

        # Terraform
        elif any(k.lower() in ("terraform", "tf_workspace") for k in tags):
            status["managed"] = True
            status["tool"] = "terraform"

        # Other IaC tools
        elif "ManagedBy" in tags or "CreatedBy" in tags:
            status["managed"] = True
            status["tool"] = tags.get("ManagedBy") or tags.get("CreatedBy")

        else:
            status["signs_of_manual_modification"].append(
                "No IaC tags detected - possibly manually created"
            )

        return status
