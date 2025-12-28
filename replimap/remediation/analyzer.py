"""
Remediation Impact Analyzer.

Analyzes the potential impact of remediation actions before execution
to help operators understand risks and plan accordingly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from replimap.core import GraphEngine
from replimap.core.models import ResourceNode
from .actions import RemediationAction, RemediationActionType

logger = logging.getLogger(__name__)


class ImpactLevel(str, Enum):
    """Level of impact for a remediation action."""

    NONE = "none"  # No service impact
    MINIMAL = "minimal"  # Brief interruption, < 1 minute
    MODERATE = "moderate"  # Service degradation possible
    SIGNIFICANT = "significant"  # Restart or brief outage
    CRITICAL = "critical"  # Extended downtime possible

    def __str__(self) -> str:
        return self.value

    @property
    def requires_maintenance_window(self) -> bool:
        """Check if this impact level requires a maintenance window."""
        return self in [ImpactLevel.SIGNIFICANT, ImpactLevel.CRITICAL]


@dataclass
class ResourceImpact:
    """Impact on a single resource."""

    resource_id: str
    resource_type: str
    resource_name: str
    region: str

    # Impact details
    impact_level: ImpactLevel
    impact_description: str

    # Service impact
    service_interruption: bool = False
    estimated_downtime_seconds: int = 0

    # Dependencies
    affected_by_action: bool = True  # Directly affected
    dependent_resources: list[str] = field(default_factory=list)
    upstream_resources: list[str] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "region": self.region,
            "impact_level": str(self.impact_level),
            "impact_description": self.impact_description,
            "service_interruption": self.service_interruption,
            "estimated_downtime_seconds": self.estimated_downtime_seconds,
            "directly_affected": self.affected_by_action,
            "dependent_resources": self.dependent_resources,
            "upstream_resources": self.upstream_resources,
            "recommendations": self.recommendations,
        }


@dataclass
class ImpactAnalysis:
    """
    Complete impact analysis for a remediation action or set of actions.
    """

    # Analysis metadata
    analysis_id: str
    analyzed_at: datetime = field(default_factory=datetime.now)

    # Actions analyzed
    action_ids: list[str] = field(default_factory=list)

    # Overall impact
    overall_impact: ImpactLevel = ImpactLevel.NONE
    requires_maintenance_window: bool = False
    estimated_total_downtime_seconds: int = 0

    # Resource impacts
    resource_impacts: list[ResourceImpact] = field(default_factory=list)
    directly_affected_count: int = 0
    indirectly_affected_count: int = 0

    # Risk assessment
    risk_score: float = 0.0  # 0-100
    risk_factors: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)

    # Dependencies
    blocking_resources: list[str] = field(default_factory=list)
    dependency_chain: list[list[str]] = field(default_factory=list)

    # Recommendations
    pre_action_steps: list[str] = field(default_factory=list)
    post_action_steps: list[str] = field(default_factory=list)

    # Warnings
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "analyzed_at": self.analyzed_at.isoformat(),
            "actions_analyzed": self.action_ids,
            "summary": {
                "overall_impact": str(self.overall_impact),
                "requires_maintenance_window": self.requires_maintenance_window,
                "estimated_downtime_seconds": self.estimated_total_downtime_seconds,
                "directly_affected_resources": self.directly_affected_count,
                "indirectly_affected_resources": self.indirectly_affected_count,
            },
            "risk": {
                "score": round(self.risk_score, 1),
                "factors": self.risk_factors,
                "mitigations": self.mitigations,
            },
            "resource_impacts": [ri.to_dict() for ri in self.resource_impacts],
            "dependencies": {
                "blocking": self.blocking_resources,
                "chain": self.dependency_chain,
            },
            "recommendations": {
                "pre_action": self.pre_action_steps,
                "post_action": self.post_action_steps,
            },
            "warnings": self.warnings,
            "errors": self.errors,
        }

    def is_safe_to_proceed(self) -> bool:
        """Check if it's safe to proceed with remediation."""
        return (
            len(self.errors) == 0
            and self.risk_score < 80
            and self.overall_impact != ImpactLevel.CRITICAL
        )


# Impact profiles for different action types
ACTION_IMPACT_PROFILES: dict[RemediationActionType, dict[str, Any]] = {
    RemediationActionType.ENABLE_ENCRYPTION: {
        "base_impact": ImpactLevel.MINIMAL,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable encryption on resource",
        "risks": ["Data at rest encryption change"],
    },
    RemediationActionType.ENABLE_KMS_ENCRYPTION: {
        "base_impact": ImpactLevel.MINIMAL,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable KMS encryption",
        "risks": ["KMS key dependency added"],
    },
    RemediationActionType.BLOCK_PUBLIC_ACCESS: {
        "base_impact": ImpactLevel.MODERATE,
        "service_interruption": True,
        "base_downtime": 0,
        "description": "Block public access",
        "risks": ["May break public access patterns"],
    },
    RemediationActionType.RESTRICT_SECURITY_GROUP: {
        "base_impact": ImpactLevel.SIGNIFICANT,
        "service_interruption": True,
        "base_downtime": 0,
        "description": "Restrict security group rules",
        "risks": ["May block legitimate traffic", "Immediate effect"],
    },
    RemediationActionType.ENABLE_MULTI_AZ: {
        "base_impact": ImpactLevel.MODERATE,
        "service_interruption": True,
        "base_downtime": 300,  # 5 minutes typical
        "description": "Enable Multi-AZ deployment",
        "risks": ["Database failover during conversion"],
    },
    RemediationActionType.ENABLE_IMDSV2: {
        "base_impact": ImpactLevel.SIGNIFICANT,
        "service_interruption": True,
        "base_downtime": 60,
        "description": "Require IMDSv2 for instance metadata",
        "risks": ["May break applications using IMDSv1", "Instance restart may be needed"],
    },
    RemediationActionType.ENABLE_VERSIONING: {
        "base_impact": ImpactLevel.NONE,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable versioning",
        "risks": ["Increased storage costs"],
    },
    RemediationActionType.ENABLE_LOGGING: {
        "base_impact": ImpactLevel.NONE,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable logging",
        "risks": ["Increased storage/CloudWatch costs"],
    },
    RemediationActionType.ENABLE_FLOW_LOGS: {
        "base_impact": ImpactLevel.NONE,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable VPC flow logs",
        "risks": ["Increased CloudWatch costs"],
    },
    RemediationActionType.ENABLE_DELETION_PROTECTION: {
        "base_impact": ImpactLevel.NONE,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable deletion protection",
        "risks": [],
    },
    RemediationActionType.ENABLE_MONITORING: {
        "base_impact": ImpactLevel.NONE,
        "service_interruption": False,
        "base_downtime": 0,
        "description": "Enable detailed monitoring",
        "risks": ["Increased CloudWatch costs"],
    },
}


class ImpactAnalyzer:
    """
    Analyzes the impact of remediation actions.

    Uses the resource graph to understand dependencies and
    estimate the blast radius of changes.
    """

    def __init__(self, graph: GraphEngine | None = None) -> None:
        """
        Initialize analyzer.

        Args:
            graph: Optional GraphEngine for dependency analysis
        """
        self.graph = graph

    def analyze(
        self,
        actions: list[RemediationAction],
        analysis_id: str | None = None,
    ) -> ImpactAnalysis:
        """
        Analyze the impact of remediation actions.

        Args:
            actions: List of remediation actions to analyze
            analysis_id: Optional analysis ID

        Returns:
            ImpactAnalysis with detailed impact information
        """
        if not analysis_id:
            analysis_id = f"impact-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        analysis = ImpactAnalysis(
            analysis_id=analysis_id,
            action_ids=[a.id for a in actions],
        )

        all_impacts: list[ResourceImpact] = []
        max_impact = ImpactLevel.NONE
        total_downtime = 0

        for action in actions:
            # Get base impact profile
            profile = ACTION_IMPACT_PROFILES.get(
                action.action_type,
                {
                    "base_impact": ImpactLevel.MODERATE,
                    "service_interruption": False,
                    "base_downtime": 0,
                    "description": "Custom remediation action",
                    "risks": [],
                },
            )

            # Create resource impact
            impact = self._analyze_action(action, profile)
            all_impacts.append(impact)

            # Track maximum impact
            if self._compare_impact(impact.impact_level, max_impact) > 0:
                max_impact = impact.impact_level

            total_downtime += impact.estimated_downtime_seconds

            # Add risk factors
            for risk in profile.get("risks", []):
                if risk not in analysis.risk_factors:
                    analysis.risk_factors.append(risk)

        # Analyze dependencies if graph available
        if self.graph:
            self._analyze_dependencies(all_impacts, analysis)

        # Calculate overall metrics
        analysis.resource_impacts = all_impacts
        analysis.overall_impact = max_impact
        analysis.estimated_total_downtime_seconds = total_downtime
        analysis.requires_maintenance_window = max_impact.requires_maintenance_window
        analysis.directly_affected_count = len([i for i in all_impacts if i.affected_by_action])
        analysis.indirectly_affected_count = len([i for i in all_impacts if not i.affected_by_action])

        # Calculate risk score
        analysis.risk_score = self._calculate_risk_score(analysis)

        # Generate recommendations
        self._generate_recommendations(analysis, actions)

        return analysis

    def _analyze_action(
        self,
        action: RemediationAction,
        profile: dict[str, Any],
    ) -> ResourceImpact:
        """Analyze impact of a single action."""
        impact_level = profile.get("base_impact", ImpactLevel.MODERATE)

        # Adjust based on resource criticality
        if self._is_production_resource(action.resource_id):
            # Increase impact for production resources
            impact_level = self._increase_impact(impact_level)

        recommendations = []

        # Add action-specific recommendations
        if action.action_type == RemediationActionType.RESTRICT_SECURITY_GROUP:
            recommendations.append("Verify current traffic patterns before applying")
            recommendations.append("Consider implementing in monitoring mode first")

        if action.action_type == RemediationActionType.ENABLE_IMDSV2:
            recommendations.append("Verify applications don't rely on IMDSv1")
            recommendations.append("Test in non-production first")

        if action.action_type == RemediationActionType.ENABLE_MULTI_AZ:
            recommendations.append("Schedule during low-traffic period")
            recommendations.append("Monitor for failover events")

        return ResourceImpact(
            resource_id=action.resource_id,
            resource_type=action.resource_type,
            resource_name=action.resource_id,  # Could be enhanced with Name tag
            region=action.region,
            impact_level=impact_level,
            impact_description=profile.get("description", ""),
            service_interruption=profile.get("service_interruption", False),
            estimated_downtime_seconds=profile.get("base_downtime", 0),
            recommendations=recommendations,
        )

    def _analyze_dependencies(
        self,
        impacts: list[ResourceImpact],
        analysis: ImpactAnalysis,
    ) -> None:
        """Analyze dependency chain for resources."""
        if not self.graph:
            return

        for impact in impacts:
            resource = self.graph.get_resource(impact.resource_id)
            if resource:
                # Find dependent resources
                dependents = self._find_dependents(resource)
                impact.dependent_resources = [d.id for d in dependents]

                # Find upstream resources
                if resource.dependencies:
                    impact.upstream_resources = resource.dependencies

    def _find_dependents(self, resource: ResourceNode) -> list[ResourceNode]:
        """Find resources that depend on the given resource."""
        if not self.graph:
            return []

        dependents = []
        for node in self.graph.get_all_resources():
            if resource.id in node.dependencies:
                dependents.append(node)

        return dependents

    def _is_production_resource(self, resource_id: str) -> bool:
        """Check if resource appears to be production."""
        # Simple heuristic based on naming
        prod_indicators = ["prod", "production", "prd", "live"]
        resource_lower = resource_id.lower()
        return any(ind in resource_lower for ind in prod_indicators)

    def _compare_impact(self, a: ImpactLevel, b: ImpactLevel) -> int:
        """Compare two impact levels. Returns >0 if a > b."""
        order = [
            ImpactLevel.NONE,
            ImpactLevel.MINIMAL,
            ImpactLevel.MODERATE,
            ImpactLevel.SIGNIFICANT,
            ImpactLevel.CRITICAL,
        ]
        return order.index(a) - order.index(b)

    def _increase_impact(self, level: ImpactLevel) -> ImpactLevel:
        """Increase impact level by one step."""
        order = [
            ImpactLevel.NONE,
            ImpactLevel.MINIMAL,
            ImpactLevel.MODERATE,
            ImpactLevel.SIGNIFICANT,
            ImpactLevel.CRITICAL,
        ]
        idx = order.index(level)
        if idx < len(order) - 1:
            return order[idx + 1]
        return level

    def _calculate_risk_score(self, analysis: ImpactAnalysis) -> float:
        """Calculate overall risk score (0-100)."""
        score = 0.0

        # Impact contribution (0-40)
        impact_scores = {
            ImpactLevel.NONE: 0,
            ImpactLevel.MINIMAL: 10,
            ImpactLevel.MODERATE: 20,
            ImpactLevel.SIGNIFICANT: 30,
            ImpactLevel.CRITICAL: 40,
        }
        score += impact_scores.get(analysis.overall_impact, 20)

        # Resource count contribution (0-20)
        affected = analysis.directly_affected_count + analysis.indirectly_affected_count
        score += min(affected * 2, 20)

        # Downtime contribution (0-20)
        if analysis.estimated_total_downtime_seconds > 0:
            downtime_score = min(analysis.estimated_total_downtime_seconds / 60, 20)
            score += downtime_score

        # Risk factor contribution (0-20)
        score += min(len(analysis.risk_factors) * 5, 20)

        return min(score, 100)

    def _generate_recommendations(
        self,
        analysis: ImpactAnalysis,
        actions: list[RemediationAction],
    ) -> None:
        """Generate pre/post action recommendations."""
        # Pre-action steps
        if analysis.requires_maintenance_window:
            analysis.pre_action_steps.append(
                "Schedule a maintenance window for this remediation"
            )

        if analysis.overall_impact in [ImpactLevel.SIGNIFICANT, ImpactLevel.CRITICAL]:
            analysis.pre_action_steps.append(
                "Create backups of affected resources before proceeding"
            )
            analysis.pre_action_steps.append(
                "Notify stakeholders of planned changes"
            )

        if any(ri.service_interruption for ri in analysis.resource_impacts):
            analysis.pre_action_steps.append(
                "Consider draining connections before applying changes"
            )

        # Post-action steps
        analysis.post_action_steps.append(
            "Verify resource functionality after remediation"
        )
        analysis.post_action_steps.append(
            "Monitor logs and metrics for unexpected behavior"
        )

        if analysis.risk_score > 50:
            analysis.post_action_steps.append(
                "Keep rollback data available for 24-48 hours"
            )

        # Warnings
        if analysis.risk_score > 70:
            analysis.warnings.append(
                "High risk score - consider additional review before proceeding"
            )

        if len(analysis.blocking_resources) > 0:
            analysis.warnings.append(
                f"Blocking dependencies detected: {analysis.blocking_resources}"
            )
