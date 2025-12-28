"""
DR Readiness Assessment for RepliMap.

Provides comprehensive disaster recovery readiness analysis:
- Compute/database/storage coverage assessment
- RTO (Recovery Time Objective) estimation
- RPO (Recovery Point Objective) estimation
- Gap analysis and recommendations
- DR Readiness Scorecard generation

The assessment analyzes infrastructure across regions to determine
DR capabilities and identify gaps in coverage.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.graph.visualizer import GraphNode, VisualizationGraph
    from replimap.graph.multi_region import MultiRegionGraph

logger = logging.getLogger(__name__)


class DRTier(str, Enum):
    """
    Disaster Recovery tiers based on RTO/RPO requirements.

    Based on common industry DR tier definitions:
    - Tier 0: No DR (development/test)
    - Tier 1: Cold standby (hours to days)
    - Tier 2: Warm standby (minutes to hours)
    - Tier 3: Hot standby (seconds to minutes)
    - Tier 4: Active-Active (zero/near-zero)
    """

    TIER_0 = "tier_0"  # No DR capability
    TIER_1 = "tier_1"  # Cold standby (RTO: 24-72h, RPO: 24h)
    TIER_2 = "tier_2"  # Warm standby (RTO: 1-4h, RPO: 1h)
    TIER_3 = "tier_3"  # Hot standby (RTO: 15min-1h, RPO: 15min)
    TIER_4 = "tier_4"  # Active-Active (RTO: <1min, RPO: 0)

    def __str__(self) -> str:
        return self.value

    @property
    def display_name(self) -> str:
        """Get human-readable tier name."""
        names = {
            DRTier.TIER_0: "No DR",
            DRTier.TIER_1: "Cold Standby",
            DRTier.TIER_2: "Warm Standby",
            DRTier.TIER_3: "Hot Standby",
            DRTier.TIER_4: "Active-Active",
        }
        return names.get(self, self.value)

    @property
    def typical_rto_minutes(self) -> int:
        """Get typical RTO in minutes for this tier."""
        rtos = {
            DRTier.TIER_0: 99999,  # No target
            DRTier.TIER_1: 1440,   # 24 hours
            DRTier.TIER_2: 240,    # 4 hours
            DRTier.TIER_3: 60,     # 1 hour
            DRTier.TIER_4: 1,      # 1 minute
        }
        return rtos.get(self, 99999)

    @property
    def typical_rpo_minutes(self) -> int:
        """Get typical RPO in minutes for this tier."""
        rpos = {
            DRTier.TIER_0: 99999,  # No target
            DRTier.TIER_1: 1440,   # 24 hours
            DRTier.TIER_2: 60,     # 1 hour
            DRTier.TIER_3: 15,     # 15 minutes
            DRTier.TIER_4: 0,      # Zero
        }
        return rpos.get(self, 99999)


class ResourceCategory(str, Enum):
    """Categories of resources for DR assessment."""

    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORKING = "networking"
    LOAD_BALANCING = "load_balancing"
    CACHING = "caching"
    MESSAGING = "messaging"

    def __str__(self) -> str:
        return self.value


# Map resource types to categories
RESOURCE_CATEGORIES: dict[str, ResourceCategory] = {
    # Compute
    "aws_instance": ResourceCategory.COMPUTE,
    "aws_autoscaling_group": ResourceCategory.COMPUTE,
    "aws_launch_template": ResourceCategory.COMPUTE,
    "aws_ecs_cluster": ResourceCategory.COMPUTE,
    "aws_ecs_service": ResourceCategory.COMPUTE,
    "aws_lambda_function": ResourceCategory.COMPUTE,
    # Database
    "aws_db_instance": ResourceCategory.DATABASE,
    "aws_rds_cluster": ResourceCategory.DATABASE,
    "aws_dynamodb_table": ResourceCategory.DATABASE,
    "aws_docdb_cluster": ResourceCategory.DATABASE,
    "aws_neptune_cluster": ResourceCategory.DATABASE,
    # Storage
    "aws_s3_bucket": ResourceCategory.STORAGE,
    "aws_ebs_volume": ResourceCategory.STORAGE,
    "aws_efs_file_system": ResourceCategory.STORAGE,
    "aws_fsx_file_system": ResourceCategory.STORAGE,
    # Networking
    "aws_vpc": ResourceCategory.NETWORKING,
    "aws_subnet": ResourceCategory.NETWORKING,
    "aws_nat_gateway": ResourceCategory.NETWORKING,
    "aws_vpn_gateway": ResourceCategory.NETWORKING,
    "aws_transit_gateway": ResourceCategory.NETWORKING,
    # Load Balancing
    "aws_lb": ResourceCategory.LOAD_BALANCING,
    "aws_lb_target_group": ResourceCategory.LOAD_BALANCING,
    "aws_globalaccelerator_accelerator": ResourceCategory.LOAD_BALANCING,
    # Caching
    "aws_elasticache_cluster": ResourceCategory.CACHING,
    "aws_elasticache_replication_group": ResourceCategory.CACHING,
    # Messaging
    "aws_sqs_queue": ResourceCategory.MESSAGING,
    "aws_sns_topic": ResourceCategory.MESSAGING,
    "aws_kinesis_stream": ResourceCategory.MESSAGING,
}


class DRGapCategory(str, Enum):
    """Categories of DR gaps."""

    NO_REPLICATION = "no_replication"
    SINGLE_REGION = "single_region"
    NO_BACKUP = "no_backup"
    NO_FAILOVER = "no_failover"
    MANUAL_RECOVERY = "manual_recovery"
    LONG_RTO = "long_rto"
    HIGH_RPO = "high_rpo"
    MISSING_RUNBOOK = "missing_runbook"
    UNTESTED = "untested"

    def __str__(self) -> str:
        return self.value


class DRRecommendationType(str, Enum):
    """Types of DR recommendations."""

    ENABLE_REPLICATION = "enable_replication"
    ENABLE_MULTI_AZ = "enable_multi_az"
    ENABLE_CROSS_REGION = "enable_cross_region"
    ENABLE_BACKUP = "enable_backup"
    ENABLE_PITR = "enable_pitr"
    ADD_READ_REPLICA = "add_read_replica"
    USE_GLOBAL_TABLE = "use_global_table"
    ADD_FAILOVER = "add_failover"
    AUTOMATE_RECOVERY = "automate_recovery"
    CREATE_RUNBOOK = "create_runbook"
    TEST_DR = "test_dr"

    def __str__(self) -> str:
        return self.value


class DRRecommendationPriority(str, Enum):
    """Priority levels for DR recommendations."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

    def __str__(self) -> str:
        return self.value


@dataclass
class RTOEstimate:
    """Recovery Time Objective estimate."""

    resource_id: str
    resource_type: str
    resource_name: str
    estimated_minutes: int
    tier: DRTier
    factors: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "estimated_minutes": self.estimated_minutes,
            "estimated_hours": round(self.estimated_minutes / 60, 1),
            "tier": self.tier.value,
            "tier_name": self.tier.display_name,
            "factors": self.factors,
            "assumptions": self.assumptions,
        }


@dataclass
class RPOEstimate:
    """Recovery Point Objective estimate."""

    resource_id: str
    resource_type: str
    resource_name: str
    estimated_minutes: int
    tier: DRTier
    backup_frequency: str | None = None
    replication_lag: str | None = None
    factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "estimated_minutes": self.estimated_minutes,
            "tier": self.tier.value,
            "tier_name": self.tier.display_name,
            "backup_frequency": self.backup_frequency,
            "replication_lag": self.replication_lag,
            "factors": self.factors,
        }


@dataclass
class ResourceCoverage:
    """DR coverage status for a resource."""

    resource_id: str
    resource_type: str
    resource_name: str
    category: ResourceCategory
    region: str
    has_multi_az: bool = False
    has_cross_region: bool = False
    has_backup: bool = False
    has_replication: bool = False
    dr_region: str | None = None
    tier: DRTier = DRTier.TIER_0

    @property
    def coverage_score(self) -> int:
        """Calculate coverage score (0-100)."""
        score = 0
        if self.has_multi_az:
            score += 25
        if self.has_cross_region:
            score += 35
        if self.has_backup:
            score += 20
        if self.has_replication:
            score += 20
        return score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "category": self.category.value,
            "region": self.region,
            "has_multi_az": self.has_multi_az,
            "has_cross_region": self.has_cross_region,
            "has_backup": self.has_backup,
            "has_replication": self.has_replication,
            "dr_region": self.dr_region,
            "tier": self.tier.value,
            "coverage_score": self.coverage_score,
        }


@dataclass
class CoverageAnalysis:
    """DR coverage analysis for a category of resources."""

    category: ResourceCategory
    total_resources: int
    covered_resources: int
    multi_az_count: int
    cross_region_count: int
    backup_count: int
    replication_count: int
    resources: list[ResourceCoverage] = field(default_factory=list)

    @property
    def coverage_percentage(self) -> float:
        """Calculate coverage percentage."""
        if self.total_resources == 0:
            return 100.0
        return (self.covered_resources / self.total_resources) * 100

    @property
    def multi_az_percentage(self) -> float:
        """Calculate Multi-AZ percentage."""
        if self.total_resources == 0:
            return 100.0
        return (self.multi_az_count / self.total_resources) * 100

    @property
    def cross_region_percentage(self) -> float:
        """Calculate cross-region percentage."""
        if self.total_resources == 0:
            return 0.0
        return (self.cross_region_count / self.total_resources) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "total_resources": self.total_resources,
            "covered_resources": self.covered_resources,
            "coverage_percentage": round(self.coverage_percentage, 1),
            "multi_az_count": self.multi_az_count,
            "multi_az_percentage": round(self.multi_az_percentage, 1),
            "cross_region_count": self.cross_region_count,
            "cross_region_percentage": round(self.cross_region_percentage, 1),
            "backup_count": self.backup_count,
            "replication_count": self.replication_count,
        }


@dataclass
class DRGap:
    """A gap in DR coverage."""

    resource_id: str
    resource_type: str
    resource_name: str
    category: DRGapCategory
    severity: DRRecommendationPriority
    description: str
    impact: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "impact": self.impact,
        }


@dataclass
class DRRecommendation:
    """A recommendation to improve DR posture."""

    resource_id: str
    resource_type: str
    resource_name: str
    recommendation_type: DRRecommendationType
    priority: DRRecommendationPriority
    title: str
    description: str
    estimated_cost_impact: str | None = None
    estimated_rto_improvement: str | None = None
    estimated_rpo_improvement: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "resource_name": self.resource_name,
            "type": self.recommendation_type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "estimated_cost_impact": self.estimated_cost_impact,
            "estimated_rto_improvement": self.estimated_rto_improvement,
            "estimated_rpo_improvement": self.estimated_rpo_improvement,
        }


@dataclass
class DRScorecard:
    """
    DR Readiness Scorecard.

    Provides an overall assessment of DR readiness including:
    - Overall score (0-100)
    - Category-specific scores
    - RTO/RPO estimates
    - Gaps and recommendations
    """

    overall_score: int
    tier: DRTier
    coverage_by_category: dict[ResourceCategory, CoverageAnalysis] = field(
        default_factory=dict
    )
    rto_estimates: list[RTOEstimate] = field(default_factory=list)
    rpo_estimates: list[RPOEstimate] = field(default_factory=list)
    gaps: list[DRGap] = field(default_factory=list)
    recommendations: list[DRRecommendation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def overall_rto_minutes(self) -> int:
        """Get the worst-case (highest) RTO across all resources."""
        if not self.rto_estimates:
            return 0
        return max(e.estimated_minutes for e in self.rto_estimates)

    @property
    def overall_rpo_minutes(self) -> int:
        """Get the worst-case (highest) RPO across all resources."""
        if not self.rpo_estimates:
            return 0
        return max(e.estimated_minutes for e in self.rpo_estimates)

    @property
    def critical_gaps_count(self) -> int:
        """Count of critical gaps."""
        return len([g for g in self.gaps if g.severity == DRRecommendationPriority.CRITICAL])

    @property
    def high_priority_recommendations(self) -> list[DRRecommendation]:
        """Get high priority recommendations."""
        return [
            r for r in self.recommendations
            if r.priority in (DRRecommendationPriority.CRITICAL, DRRecommendationPriority.HIGH)
        ]

    def get_grade(self) -> str:
        """Get letter grade based on score."""
        if self.overall_score >= 90:
            return "A"
        elif self.overall_score >= 80:
            return "B"
        elif self.overall_score >= 70:
            return "C"
        elif self.overall_score >= 60:
            return "D"
        else:
            return "F"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "overall_score": self.overall_score,
            "grade": self.get_grade(),
            "tier": self.tier.value,
            "tier_name": self.tier.display_name,
            "overall_rto_minutes": self.overall_rto_minutes,
            "overall_rpo_minutes": self.overall_rpo_minutes,
            "coverage_by_category": {
                cat.value: analysis.to_dict()
                for cat, analysis in self.coverage_by_category.items()
            },
            "rto_estimates": [e.to_dict() for e in self.rto_estimates],
            "rpo_estimates": [e.to_dict() for e in self.rpo_estimates],
            "gaps": [g.to_dict() for g in self.gaps],
            "gaps_summary": {
                "total": len(self.gaps),
                "critical": self.critical_gaps_count,
            },
            "recommendations": [r.to_dict() for r in self.recommendations],
            "recommendations_summary": {
                "total": len(self.recommendations),
                "high_priority": len(self.high_priority_recommendations),
            },
            "metadata": self.metadata,
        }


@dataclass
class ReadinessConfig:
    """Configuration for DR readiness assessment."""

    # Target tier for assessment
    target_tier: DRTier = DRTier.TIER_2

    # Primary region
    primary_region: str | None = None

    # Expected DR region
    dr_region: str | None = None

    # Categories to assess
    include_categories: set[ResourceCategory] = field(
        default_factory=lambda: set(ResourceCategory)
    )

    # Weight for each category in overall score
    category_weights: dict[ResourceCategory, float] = field(
        default_factory=lambda: {
            ResourceCategory.DATABASE: 0.30,
            ResourceCategory.COMPUTE: 0.25,
            ResourceCategory.STORAGE: 0.20,
            ResourceCategory.NETWORKING: 0.10,
            ResourceCategory.LOAD_BALANCING: 0.05,
            ResourceCategory.CACHING: 0.05,
            ResourceCategory.MESSAGING: 0.05,
        }
    )

    @classmethod
    def default(cls) -> ReadinessConfig:
        """Create default configuration."""
        return cls()

    @classmethod
    def for_tier(cls, tier: DRTier) -> ReadinessConfig:
        """Create configuration for a specific target tier."""
        return cls(target_tier=tier)


class ReadinessAssessor:
    """
    Assesses DR readiness of infrastructure.

    Analyzes resources across regions to determine:
    - Coverage levels for compute, database, storage
    - RTO/RPO estimates based on current configuration
    - Gaps in DR coverage
    - Recommendations for improvement
    """

    def __init__(self, config: ReadinessConfig | None = None) -> None:
        """
        Initialize the assessor.

        Args:
            config: Assessment configuration
        """
        self.config = config or ReadinessConfig.default()

    def assess(
        self,
        graph: VisualizationGraph,
        cross_region_pairs: dict[str, str] | None = None,
    ) -> DRScorecard:
        """
        Assess DR readiness from a visualization graph.

        Args:
            graph: Infrastructure graph to assess
            cross_region_pairs: Known cross-region resource pairs

        Returns:
            DRScorecard with assessment results
        """
        cross_region_pairs = cross_region_pairs or {}

        # Analyze coverage by category
        coverage_by_category = self._analyze_coverage(graph, cross_region_pairs)

        # Calculate RTO/RPO estimates
        rto_estimates = self._estimate_rto(graph)
        rpo_estimates = self._estimate_rpo(graph)

        # Identify gaps
        gaps = self._identify_gaps(graph, coverage_by_category)

        # Generate recommendations
        recommendations = self._generate_recommendations(gaps, coverage_by_category)

        # Calculate overall score
        overall_score = self._calculate_overall_score(coverage_by_category)

        # Determine tier
        tier = self._determine_tier(overall_score, rto_estimates, rpo_estimates)

        return DRScorecard(
            overall_score=overall_score,
            tier=tier,
            coverage_by_category=coverage_by_category,
            rto_estimates=rto_estimates,
            rpo_estimates=rpo_estimates,
            gaps=gaps,
            recommendations=recommendations,
            metadata={
                "config": {
                    "target_tier": self.config.target_tier.value,
                    "primary_region": self.config.primary_region,
                    "dr_region": self.config.dr_region,
                },
                "resources_analyzed": len(graph.nodes),
            },
        )

    def _analyze_coverage(
        self,
        graph: VisualizationGraph,
        cross_region_pairs: dict[str, str],
    ) -> dict[ResourceCategory, CoverageAnalysis]:
        """Analyze DR coverage by resource category."""
        coverage: dict[ResourceCategory, CoverageAnalysis] = {}

        # Group nodes by category
        by_category: dict[ResourceCategory, list[GraphNode]] = {}
        for node in graph.nodes:
            cat = RESOURCE_CATEGORIES.get(node.resource_type)
            if cat and cat in self.config.include_categories:
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(node)

        # Analyze each category
        for category, nodes in by_category.items():
            resources: list[ResourceCoverage] = []

            for node in nodes:
                resource_coverage = self._analyze_resource_coverage(
                    node, cross_region_pairs
                )
                resources.append(resource_coverage)

            # Aggregate coverage
            covered = len([r for r in resources if r.coverage_score >= 50])
            multi_az = len([r for r in resources if r.has_multi_az])
            cross_region = len([r for r in resources if r.has_cross_region])
            backup = len([r for r in resources if r.has_backup])
            replication = len([r for r in resources if r.has_replication])

            coverage[category] = CoverageAnalysis(
                category=category,
                total_resources=len(nodes),
                covered_resources=covered,
                multi_az_count=multi_az,
                cross_region_count=cross_region,
                backup_count=backup,
                replication_count=replication,
                resources=resources,
            )

        return coverage

    def _analyze_resource_coverage(
        self,
        node: GraphNode,
        cross_region_pairs: dict[str, str],
    ) -> ResourceCoverage:
        """Analyze DR coverage for a single resource."""
        props = node.properties
        resource_type = node.resource_type

        # Determine category
        category = RESOURCE_CATEGORIES.get(resource_type, ResourceCategory.COMPUTE)

        # Check for Multi-AZ
        has_multi_az = self._check_multi_az(node)

        # Check for cross-region
        has_cross_region = node.id in cross_region_pairs
        dr_region = cross_region_pairs.get(node.id)

        # Check for backup
        has_backup = self._check_backup(node)

        # Check for replication
        has_replication = self._check_replication(node)

        # Determine tier
        tier = self._determine_resource_tier(
            has_multi_az, has_cross_region, has_backup, has_replication
        )

        return ResourceCoverage(
            resource_id=node.id,
            resource_type=resource_type,
            resource_name=node.name,
            category=category,
            region=props.get("region", "unknown"),
            has_multi_az=has_multi_az,
            has_cross_region=has_cross_region,
            has_backup=has_backup,
            has_replication=has_replication,
            dr_region=dr_region,
            tier=tier,
        )

    def _check_multi_az(self, node: GraphNode) -> bool:
        """Check if resource has Multi-AZ enabled."""
        props = node.properties
        resource_type = node.resource_type

        # RDS Multi-AZ
        if resource_type in ("aws_db_instance", "aws_rds_cluster"):
            return bool(props.get("multi_az", False) or props.get("MultiAZ", False))

        # ElastiCache Multi-AZ
        if resource_type == "aws_elasticache_replication_group":
            return bool(props.get("automatic_failover_enabled", False))

        # ALB/NLB are inherently multi-AZ
        if resource_type == "aws_lb":
            subnets = props.get("subnets", []) or props.get("subnet_ids", [])
            return len(subnets) > 1 if isinstance(subnets, list) else False

        # EFS is inherently multi-AZ in standard mode
        if resource_type == "aws_efs_file_system":
            return True  # EFS is always multi-AZ

        return False

    def _check_backup(self, node: GraphNode) -> bool:
        """Check if resource has backup enabled."""
        props = node.properties
        resource_type = node.resource_type

        # RDS backup
        if resource_type in ("aws_db_instance", "aws_rds_cluster"):
            retention = props.get("backup_retention_period", 0)
            return int(retention) > 0 if isinstance(retention, (int, float)) else False

        # DynamoDB backup
        if resource_type == "aws_dynamodb_table":
            pitr = props.get("point_in_time_recovery", {})
            if isinstance(pitr, dict):
                return bool(pitr.get("enabled", False))
            return False

        # S3 versioning (form of backup)
        if resource_type == "aws_s3_bucket":
            versioning = props.get("versioning", {})
            if isinstance(versioning, dict):
                return bool(versioning.get("enabled", False))
            return False

        # EBS snapshots would be separate resources
        if resource_type == "aws_ebs_volume":
            return props.get("snapshot_id") is not None

        return False

    def _check_replication(self, node: GraphNode) -> bool:
        """Check if resource has replication enabled."""
        props = node.properties
        resource_type = node.resource_type

        # RDS Read Replica indicator
        if resource_type == "aws_db_instance":
            return props.get("replicate_source_db") is not None

        # Aurora Global Database
        if resource_type == "aws_rds_cluster":
            return props.get("global_cluster_identifier") is not None

        # DynamoDB Global Tables
        if resource_type == "aws_dynamodb_table":
            replicas = props.get("replica", [])
            return len(replicas) > 0 if isinstance(replicas, list) else False

        # S3 cross-region replication
        if resource_type == "aws_s3_bucket":
            return props.get("replication_configuration") is not None

        # ElastiCache Global Datastore
        if resource_type == "aws_elasticache_replication_group":
            return props.get("global_replication_group_id") is not None

        return False

    def _determine_resource_tier(
        self,
        has_multi_az: bool,
        has_cross_region: bool,
        has_backup: bool,
        has_replication: bool,
    ) -> DRTier:
        """Determine DR tier for a resource based on its configuration."""
        if has_cross_region and has_replication:
            return DRTier.TIER_4 if has_multi_az else DRTier.TIER_3
        elif has_cross_region or has_replication:
            return DRTier.TIER_3 if has_multi_az else DRTier.TIER_2
        elif has_multi_az and has_backup:
            return DRTier.TIER_2
        elif has_backup:
            return DRTier.TIER_1
        else:
            return DRTier.TIER_0

    def _estimate_rto(self, graph: VisualizationGraph) -> list[RTOEstimate]:
        """Estimate RTO for resources."""
        estimates: list[RTOEstimate] = []

        for node in graph.nodes:
            category = RESOURCE_CATEGORIES.get(node.resource_type)
            if category not in self.config.include_categories:
                continue

            estimate = self._estimate_resource_rto(node)
            if estimate:
                estimates.append(estimate)

        return estimates

    def _estimate_resource_rto(self, node: GraphNode) -> RTOEstimate | None:
        """Estimate RTO for a single resource."""
        props = node.properties
        resource_type = node.resource_type
        factors: list[str] = []
        assumptions: list[str] = []

        # Base RTO estimates by resource type (in minutes)
        base_rto = {
            "aws_instance": 30,  # EC2 instance
            "aws_autoscaling_group": 15,  # ASG can scale quickly
            "aws_db_instance": 60,  # RDS restore
            "aws_rds_cluster": 30,  # Aurora faster
            "aws_dynamodb_table": 5,  # DynamoDB point-in-time
            "aws_s3_bucket": 0,  # S3 is always available
            "aws_elasticache_cluster": 20,  # Cache warmup
            "aws_lb": 5,  # LB creation
        }

        rto_minutes = base_rto.get(resource_type, 60)

        # Adjust for Multi-AZ (automatic failover)
        if self._check_multi_az(node):
            if resource_type in ("aws_db_instance", "aws_rds_cluster"):
                rto_minutes = min(rto_minutes, 5)  # Automatic failover
                factors.append("Multi-AZ with automatic failover")
            else:
                rto_minutes = int(rto_minutes * 0.5)
                factors.append("Multi-AZ deployment")

        # Adjust for cross-region (manual intervention typically)
        if props.get("region") != self.config.dr_region:
            factors.append("Cross-region failover required")
            assumptions.append("Manual DNS/routing update")

        # Determine tier
        if rto_minutes <= 1:
            tier = DRTier.TIER_4
        elif rto_minutes <= 60:
            tier = DRTier.TIER_3
        elif rto_minutes <= 240:
            tier = DRTier.TIER_2
        else:
            tier = DRTier.TIER_1

        return RTOEstimate(
            resource_id=node.id,
            resource_type=resource_type,
            resource_name=node.name,
            estimated_minutes=rto_minutes,
            tier=tier,
            factors=factors,
            assumptions=assumptions,
        )

    def _estimate_rpo(self, graph: VisualizationGraph) -> list[RPOEstimate]:
        """Estimate RPO for resources."""
        estimates: list[RPOEstimate] = []

        for node in graph.nodes:
            category = RESOURCE_CATEGORIES.get(node.resource_type)
            if category not in self.config.include_categories:
                continue

            estimate = self._estimate_resource_rpo(node)
            if estimate:
                estimates.append(estimate)

        return estimates

    def _estimate_resource_rpo(self, node: GraphNode) -> RPOEstimate | None:
        """Estimate RPO for a single resource."""
        props = node.properties
        resource_type = node.resource_type
        factors: list[str] = []

        # Determine backup frequency and replication status
        backup_frequency: str | None = None
        replication_lag: str | None = None
        rpo_minutes = 1440  # Default: 24 hours

        if resource_type in ("aws_db_instance", "aws_rds_cluster"):
            # Check for synchronous replication
            if self._check_replication(node):
                rpo_minutes = 0
                replication_lag = "synchronous"
                factors.append("Synchronous replication enabled")
            elif self._check_multi_az(node):
                rpo_minutes = 0
                factors.append("Multi-AZ synchronous replication")
            else:
                retention = props.get("backup_retention_period", 0)
                if retention > 0:
                    rpo_minutes = 1440  # Daily backup
                    backup_frequency = "daily"
                    factors.append(f"Automated backups (retention: {retention} days)")

        elif resource_type == "aws_dynamodb_table":
            if props.get("point_in_time_recovery", {}).get("enabled"):
                rpo_minutes = 5  # PITR granularity
                backup_frequency = "continuous (PITR)"
                factors.append("Point-in-time recovery enabled")
            elif self._check_replication(node):
                rpo_minutes = 1  # Global tables async
                replication_lag = "typically < 1 second"
                factors.append("Global Tables replication")

        elif resource_type == "aws_s3_bucket":
            if props.get("replication_configuration"):
                rpo_minutes = 15  # Async replication
                replication_lag = "typically < 15 minutes"
                factors.append("Cross-region replication enabled")
            elif props.get("versioning", {}).get("enabled"):
                rpo_minutes = 0  # Versioning means no data loss
                factors.append("Versioning enabled - objects recoverable")

        # Determine tier
        if rpo_minutes == 0:
            tier = DRTier.TIER_4
        elif rpo_minutes <= 15:
            tier = DRTier.TIER_3
        elif rpo_minutes <= 60:
            tier = DRTier.TIER_2
        else:
            tier = DRTier.TIER_1

        return RPOEstimate(
            resource_id=node.id,
            resource_type=resource_type,
            resource_name=node.name,
            estimated_minutes=rpo_minutes,
            tier=tier,
            backup_frequency=backup_frequency,
            replication_lag=replication_lag,
            factors=factors,
        )

    def _identify_gaps(
        self,
        graph: VisualizationGraph,
        coverage: dict[ResourceCategory, CoverageAnalysis],
    ) -> list[DRGap]:
        """Identify gaps in DR coverage."""
        gaps: list[DRGap] = []

        for category, analysis in coverage.items():
            for resource in analysis.resources:
                resource_gaps = self._identify_resource_gaps(resource)
                gaps.extend(resource_gaps)

        return gaps

    def _identify_resource_gaps(self, resource: ResourceCoverage) -> list[DRGap]:
        """Identify gaps for a single resource."""
        gaps: list[DRGap] = []

        # Critical: Database without any backup
        if resource.category == ResourceCategory.DATABASE:
            if not resource.has_backup and not resource.has_replication:
                gaps.append(
                    DRGap(
                        resource_id=resource.resource_id,
                        resource_type=resource.resource_type,
                        resource_name=resource.resource_name,
                        category=DRGapCategory.NO_BACKUP,
                        severity=DRRecommendationPriority.CRITICAL,
                        description="Database has no backup or replication configured",
                        impact="Complete data loss possible in case of failure",
                    )
                )

            if not resource.has_multi_az:
                gaps.append(
                    DRGap(
                        resource_id=resource.resource_id,
                        resource_type=resource.resource_type,
                        resource_name=resource.resource_name,
                        category=DRGapCategory.NO_FAILOVER,
                        severity=DRRecommendationPriority.HIGH,
                        description="Database is not Multi-AZ enabled",
                        impact="Extended downtime during AZ failure",
                    )
                )

        # High: Single region for critical resources
        if not resource.has_cross_region:
            if resource.category in (ResourceCategory.DATABASE, ResourceCategory.COMPUTE):
                gaps.append(
                    DRGap(
                        resource_id=resource.resource_id,
                        resource_type=resource.resource_type,
                        resource_name=resource.resource_name,
                        category=DRGapCategory.SINGLE_REGION,
                        severity=DRRecommendationPriority.MEDIUM,
                        description="Resource exists in a single region only",
                        impact="Region-wide outage would cause service unavailability",
                    )
                )

        return gaps

    def _generate_recommendations(
        self,
        gaps: list[DRGap],
        coverage: dict[ResourceCategory, CoverageAnalysis],
    ) -> list[DRRecommendation]:
        """Generate recommendations to improve DR posture."""
        recommendations: list[DRRecommendation] = []

        for gap in gaps:
            rec = self._gap_to_recommendation(gap)
            if rec:
                recommendations.append(rec)

        # Sort by priority
        priority_order = {
            DRRecommendationPriority.CRITICAL: 0,
            DRRecommendationPriority.HIGH: 1,
            DRRecommendationPriority.MEDIUM: 2,
            DRRecommendationPriority.LOW: 3,
        }
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 4))

        return recommendations

    def _gap_to_recommendation(self, gap: DRGap) -> DRRecommendation | None:
        """Convert a gap to a recommendation."""
        rec_map = {
            DRGapCategory.NO_BACKUP: (
                DRRecommendationType.ENABLE_BACKUP,
                "Enable automated backups",
                "Configure automated backup with appropriate retention period",
            ),
            DRGapCategory.NO_REPLICATION: (
                DRRecommendationType.ENABLE_REPLICATION,
                "Enable replication",
                "Set up cross-region replication for data durability",
            ),
            DRGapCategory.NO_FAILOVER: (
                DRRecommendationType.ENABLE_MULTI_AZ,
                "Enable Multi-AZ",
                "Deploy across multiple availability zones for automatic failover",
            ),
            DRGapCategory.SINGLE_REGION: (
                DRRecommendationType.ENABLE_CROSS_REGION,
                "Enable cross-region deployment",
                "Deploy replica or standby in secondary region",
            ),
        }

        mapping = rec_map.get(gap.category)
        if not mapping:
            return None

        rec_type, title, description = mapping

        return DRRecommendation(
            resource_id=gap.resource_id,
            resource_type=gap.resource_type,
            resource_name=gap.resource_name,
            recommendation_type=rec_type,
            priority=gap.severity,
            title=title,
            description=description,
        )

    def _calculate_overall_score(
        self,
        coverage: dict[ResourceCategory, CoverageAnalysis],
    ) -> int:
        """Calculate overall DR readiness score (0-100)."""
        if not coverage:
            return 0

        weighted_sum = Decimal("0")
        total_weight = Decimal("0")

        for category, analysis in coverage.items():
            weight = Decimal(str(self.config.category_weights.get(category, 0.1)))
            score = Decimal(str(analysis.coverage_percentage))
            weighted_sum += weight * score
            total_weight += weight

        if total_weight == 0:
            return 0

        return int(weighted_sum / total_weight)

    def _determine_tier(
        self,
        score: int,
        rto_estimates: list[RTOEstimate],
        rpo_estimates: list[RPOEstimate],
    ) -> DRTier:
        """Determine overall DR tier."""
        # Get worst-case RTO/RPO
        max_rto = max((e.estimated_minutes for e in rto_estimates), default=99999)
        max_rpo = max((e.estimated_minutes for e in rpo_estimates), default=99999)

        # Tier based on worst-case
        if max_rto <= 1 and max_rpo == 0:
            return DRTier.TIER_4
        elif max_rto <= 60 and max_rpo <= 15:
            return DRTier.TIER_3
        elif max_rto <= 240 and max_rpo <= 60:
            return DRTier.TIER_2
        elif max_rto <= 1440 and max_rpo <= 1440:
            return DRTier.TIER_1
        else:
            return DRTier.TIER_0


def analyze_dr_readiness(
    graph: VisualizationGraph,
    config: ReadinessConfig | None = None,
    cross_region_pairs: dict[str, str] | None = None,
) -> DRScorecard:
    """
    Analyze DR readiness for an infrastructure graph.

    Args:
        graph: Infrastructure graph to assess
        config: Assessment configuration
        cross_region_pairs: Known cross-region resource pairs

    Returns:
        DRScorecard with assessment results
    """
    assessor = ReadinessAssessor(config)
    return assessor.assess(graph, cross_region_pairs)


def calculate_rto_estimate(
    graph: VisualizationGraph,
    config: ReadinessConfig | None = None,
) -> list[RTOEstimate]:
    """Calculate RTO estimates for all resources."""
    assessor = ReadinessAssessor(config)
    return assessor._estimate_rto(graph)


def calculate_rpo_estimate(
    graph: VisualizationGraph,
    config: ReadinessConfig | None = None,
) -> list[RPOEstimate]:
    """Calculate RPO estimates for all resources."""
    assessor = ReadinessAssessor(config)
    return assessor._estimate_rpo(graph)


def generate_dr_recommendations(
    graph: VisualizationGraph,
    config: ReadinessConfig | None = None,
) -> list[DRRecommendation]:
    """Generate DR improvement recommendations."""
    scorecard = analyze_dr_readiness(graph, config)
    return scorecard.recommendations
