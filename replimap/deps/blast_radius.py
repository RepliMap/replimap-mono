"""
Blast Radius Calculation.

Provides weighted blast radius scoring based on resource criticality.
"""

from __future__ import annotations

from replimap.deps.models import (
    BlastRadiusScore,
    Dependency,
    RelationType,
    ResourceCriticality,
    RESOURCE_WEIGHTS,
)


def calculate_blast_radius(
    dependencies: dict[RelationType, list[Dependency]]
) -> BlastRadiusScore:
    """
    Calculate blast radius score from dependencies.

    The score is weighted by resource criticality:
    - Databases (10) > KMS Keys (9) > Load Balancers/IAM Roles (8)
    - Containers/Cache/Storage (7-8) > Security Groups (6) > Compute (5)

    Args:
        dependencies: Dict of relation type to list of dependencies

    Returns:
        BlastRadiusScore with weighted impact assessment
    """
    total_count = 0
    weighted_sum = 0
    breakdown: dict[str, dict[str, int]] = {}

    # Focus on CONSUMER dependencies for blast radius
    # These are resources that will be affected by changes
    consumers = dependencies.get(RelationType.CONSUMER, [])

    # Also include MANAGED resources (for ASG → EC2)
    managed = dependencies.get(RelationType.MANAGED, [])

    all_affected = consumers + managed

    for dep in all_affected:
        resource_type = dep.resource_type
        weight = RESOURCE_WEIGHTS.get(
            resource_type, ResourceCriticality.DEFAULT
        ).value

        # Count the dependency itself
        count = 1

        # Count children (nested dependencies)
        count += len(dep.children)

        total_count += count
        impact = count * weight
        weighted_sum += impact

        if resource_type not in breakdown:
            breakdown[resource_type] = {"count": 0, "weight": weight, "impact": 0}

        breakdown[resource_type]["count"] += count
        breakdown[resource_type]["impact"] += impact

    # Normalize score to 0-100
    # Assume weighted_sum = 100 is "medium risk" baseline
    normalized_score = min(100, int(weighted_sum))

    # Determine risk level
    if normalized_score >= 80:
        level = "CRITICAL"
    elif normalized_score >= 50:
        level = "HIGH"
    elif normalized_score >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"

    # Generate summary
    high_impact_types = [
        f"{v['count']} {k.replace('aws_', '')}"
        for k, v in breakdown.items()
        if v["weight"] >= 7
    ]

    summary = f"{total_count} resources affected"
    if high_impact_types:
        summary += f" (including {', '.join(high_impact_types)})"

    return BlastRadiusScore(
        score=normalized_score,
        level=level,
        affected_count=total_count,
        weighted_impact=weighted_sum,
        breakdown=breakdown,
        summary=summary,
    )


def get_risk_color(level: str) -> str:
    """Get Rich color for risk level."""
    colors = {
        "CRITICAL": "red bold",
        "HIGH": "red",
        "MEDIUM": "yellow",
        "LOW": "green",
    }
    return colors.get(level, "white")


def get_severity_color(severity: str) -> str:
    """Get Rich color for severity."""
    colors = {
        "critical": "red bold",
        "high": "red",
        "medium": "yellow",
        "info": "dim",
    }
    return colors.get(severity, "white")
