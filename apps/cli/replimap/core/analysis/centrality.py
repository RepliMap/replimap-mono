"""
Centrality analysis for AWS resource dependency graphs.

This module identifies critical infrastructure components using
graph centrality metrics:

- Single Point of Failure (SPOF): Resources with high in-degree
  (many resources depend on them)
- High Blast Radius: Resources whose failure cascades widely
- Attack Surface: Internet-exposed or high-privilege resources
- Critical Resources: Combined risk assessment

Metrics Used:
    - Betweenness Centrality: Measures how often a node lies on
      shortest paths between other nodes. High values = bottleneck.
    - In-Degree Centrality: Number of resources depending on this one.
      High values = single point of failure.
    - Out-Degree Centrality: Number of resources this one depends on.
      High values = complex dependency chain.
    - PageRank: Iterative importance measure based on dependency structure.

Usage:
    from replimap.core.analysis.centrality import CentralityAnalyzer

    analyzer = CentralityAnalyzer(graph)

    # Find single points of failure
    spofs = analyzer.find_single_points_of_failure()
    for spof in spofs:
        print(f"{spof.resource_id}: {spof.dependent_count} dependents")

    # Compute blast radius
    blast = analyzer.compute_blast_radius("vpc-12345")
    print(f"Failure would affect {blast.affected_count} resources")

    # Find critical resources
    finder = CriticalResourceFinder(graph)
    critical = finder.find_critical(top_n=10)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import networkx as nx

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


class CriticalityLevel(Enum):
    """Criticality levels for resources."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SinglePointOfFailureResult:
    """
    Result for a single point of failure analysis.

    Attributes:
        resource_id: The ID of the SPOF resource
        resource_type: Type of the resource
        dependent_count: Number of resources that depend on this one
        dependents: List of dependent resource IDs
        in_degree_percentile: How this compares to other nodes (0-100)
    """

    resource_id: str
    resource_type: str
    dependent_count: int
    dependents: list[str]
    in_degree_percentile: float


@dataclass
class BlastRadiusResult:
    """
    Result of blast radius computation for a resource.

    Attributes:
        resource_id: The source resource
        affected_count: Total number of resources affected by failure
        affected_resources: List of affected resource IDs
        depth: Maximum cascade depth
        by_type: Count of affected resources by type
        cascade_path: Map of affected resources to their distance from source
    """

    resource_id: str
    affected_count: int
    affected_resources: list[str]
    depth: int
    by_type: dict[str, int]
    cascade_path: dict[str, int]


@dataclass
class AttackSurfaceResult:
    """
    Attack surface analysis result.

    Attributes:
        exposed_resources: Resources with internet exposure
        high_privilege_resources: Resources with broad permissions
        public_resources: S3 buckets, APIs etc with public access
        risk_score: Overall attack surface score (0-100)
    """

    exposed_resources: list[str]
    high_privilege_resources: list[str]
    public_resources: list[str]
    risk_score: float


@dataclass
class CriticalityResult:
    """
    Combined criticality assessment for a resource.

    Attributes:
        resource_id: The resource being assessed
        resource_type: Type of the resource
        level: Overall criticality level
        score: Numeric score (0-100)
        factors: Contributing factors to criticality
        blast_radius: Number of resources affected by failure
        dependent_count: Direct dependents
        betweenness: Betweenness centrality score
    """

    resource_id: str
    resource_type: str
    level: CriticalityLevel
    score: float
    factors: list[str] = field(default_factory=list)
    blast_radius: int = 0
    dependent_count: int = 0
    betweenness: float = 0.0


class CentralityAnalyzer:
    """
    Analyzes graph centrality to identify critical resources.

    Provides methods for:
    - Single point of failure detection
    - Blast radius computation
    - Betweenness centrality analysis
    - PageRank importance ranking
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the analyzer.

        Args:
            graph: The GraphEngine to analyze
        """
        self._graph = graph
        self._betweenness_cache: dict[str, float] | None = None
        self._pagerank_cache: dict[str, float] | None = None

    def compute_betweenness_centrality(self) -> dict[str, float]:
        """
        Compute betweenness centrality for all nodes.

        Betweenness measures how often a node lies on shortest paths
        between other nodes. High values indicate bottleneck resources
        that are critical for connectivity.

        Returns:
            Dict mapping node IDs to betweenness centrality scores (0-1)
        """
        if self._betweenness_cache is not None:
            return self._betweenness_cache

        g = self._graph._graph
        self._betweenness_cache = nx.betweenness_centrality(g, normalized=True)
        return self._betweenness_cache

    def compute_pagerank(self, damping: float = 0.85) -> dict[str, float]:
        """
        Compute PageRank for all nodes.

        PageRank gives higher scores to nodes that are depended upon
        by many other important nodes. This identifies structurally
        important resources in the dependency hierarchy.

        Args:
            damping: Damping factor (default 0.85, standard value)

        Returns:
            Dict mapping node IDs to PageRank scores
        """
        if self._pagerank_cache is not None:
            return self._pagerank_cache

        g = self._graph._graph
        try:
            self._pagerank_cache = nx.pagerank(g, alpha=damping)
        except (nx.PowerIterationFailedConvergence, ModuleNotFoundError, ImportError):
            # Fall back to simpler method when:
            # - PageRank fails to converge
            # - numpy/scipy not available (required by pagerank)
            logger.warning("PageRank unavailable, using in-degree fallback")
            in_degrees = dict(g.in_degree())
            total = sum(in_degrees.values()) or 1
            self._pagerank_cache = {k: v / total for k, v in in_degrees.items()}

        return self._pagerank_cache

    def find_single_points_of_failure(
        self, threshold_percentile: float = 90
    ) -> list[SinglePointOfFailureResult]:
        """
        Find resources that are single points of failure.

        A SPOF is a resource with unusually high in-degree (many other
        resources depend on it). Failure of a SPOF cascades to all
        its dependents.

        Args:
            threshold_percentile: Only return nodes above this percentile
                                 in terms of in-degree (default: top 10%)

        Returns:
            List of SinglePointOfFailureResult, sorted by dependent count
        """
        g = self._graph._graph
        in_degrees = dict(g.in_degree())

        if not in_degrees:
            return []

        # Compute threshold value
        sorted_degrees = sorted(in_degrees.values())
        threshold_idx = int(len(sorted_degrees) * threshold_percentile / 100)
        threshold = sorted_degrees[min(threshold_idx, len(sorted_degrees) - 1)]

        results: list[SinglePointOfFailureResult] = []

        for node_id, degree in in_degrees.items():
            if degree >= threshold and degree > 0:
                # Compute percentile for this node
                rank = sum(1 for d in sorted_degrees if d <= degree)
                percentile = (rank / len(sorted_degrees)) * 100

                dependents = list(g.predecessors(node_id))
                resource = self._graph.get_resource(node_id)
                resource_type = str(resource.resource_type) if resource else "unknown"

                results.append(
                    SinglePointOfFailureResult(
                        resource_id=node_id,
                        resource_type=resource_type,
                        dependent_count=degree,
                        dependents=dependents,
                        in_degree_percentile=percentile,
                    )
                )

        # Sort by dependent count (highest first)
        results.sort(key=lambda r: r.dependent_count, reverse=True)
        return results

    def compute_blast_radius(self, resource_id: str) -> BlastRadiusResult:
        """
        Compute the blast radius of a resource failure.

        Blast radius is the set of resources that would be affected
        if the given resource failed. This uses reverse BFS to find
        all resources that directly or transitively depend on the source.

        Args:
            resource_id: The resource to analyze

        Returns:
            BlastRadiusResult with affected resources and cascade path
        """
        g = self._graph._graph

        if resource_id not in g:
            return BlastRadiusResult(
                resource_id=resource_id,
                affected_count=0,
                affected_resources=[],
                depth=0,
                by_type={},
                cascade_path={},
            )

        # BFS to find all predecessors (resources that depend on this one)
        affected: dict[str, int] = {}  # node_id -> distance
        queue: list[tuple[str, int]] = [(resource_id, 0)]
        visited: set[str] = {resource_id}

        while queue:
            current, depth = queue.pop(0)

            # Find all nodes that depend on current
            for predecessor in g.predecessors(current):
                if predecessor not in visited:
                    visited.add(predecessor)
                    affected[predecessor] = depth + 1
                    queue.append((predecessor, depth + 1))

        # Count by type
        by_type: dict[str, int] = {}
        for node_id in affected:
            resource = self._graph.get_resource(node_id)
            if resource:
                type_name = str(resource.resource_type)
                by_type[type_name] = by_type.get(type_name, 0) + 1

        max_depth = max(affected.values()) if affected else 0

        return BlastRadiusResult(
            resource_id=resource_id,
            affected_count=len(affected),
            affected_resources=list(affected.keys()),
            depth=max_depth,
            by_type=by_type,
            cascade_path=affected,
        )

    def get_top_by_betweenness(self, n: int = 10) -> list[tuple[str, float]]:
        """
        Get the top N nodes by betweenness centrality.

        Args:
            n: Number of results to return

        Returns:
            List of (node_id, betweenness_score) tuples
        """
        betweenness = self.compute_betweenness_centrality()
        sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:n]

    def get_top_by_pagerank(self, n: int = 10) -> list[tuple[str, float]]:
        """
        Get the top N nodes by PageRank.

        Args:
            n: Number of results to return

        Returns:
            List of (node_id, pagerank_score) tuples
        """
        pagerank = self.compute_pagerank()
        sorted_nodes = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)
        return sorted_nodes[:n]


class AttackSurfaceAnalyzer:
    """
    Analyzes attack surface of infrastructure.

    Identifies:
    - Internet-exposed resources (IGW connections, public IPs)
    - High-privilege IAM resources
    - Publicly accessible storage
    """

    # Resource types that indicate internet exposure
    EXPOSURE_TYPES = {
        "internet_gateway",
        "nat_gateway",
        "lb",
        "alb",
        "nlb",
        "api_gateway",
        "cloudfront_distribution",
    }

    # High-privilege IAM indicators
    HIGH_PRIVILEGE_ACTIONS = {
        "*",
        "iam:*",
        "s3:*",
        "ec2:*",
        "sts:AssumeRole",
    }

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the analyzer.

        Args:
            graph: The GraphEngine to analyze
        """
        self._graph = graph

    def find_exposed_resources(self) -> list[str]:
        """
        Find resources with potential internet exposure.

        Returns:
            List of resource IDs that may be internet-exposed
        """
        exposed: list[str] = []

        for resource in self._graph.get_all_resources():
            type_name = str(resource.resource_type).lower()

            # Check for exposure type
            if any(exp in type_name for exp in self.EXPOSURE_TYPES):
                exposed.append(resource.id)
                continue

            # Check for public IP in config
            config = resource.config or {}
            if config.get("PublicIpAddress") or config.get("PublicDnsName"):
                exposed.append(resource.id)

        return exposed

    def find_high_privilege_resources(self) -> list[str]:
        """
        Find IAM resources with high privileges.

        Returns:
            List of resource IDs with broad permissions
        """
        high_priv: list[str] = []

        for resource in self._graph.get_all_resources():
            type_name = str(resource.resource_type).lower()

            if "iam" not in type_name:
                continue

            # Check for admin-like policies
            config = resource.config or {}

            # Check inline policies
            policies = config.get("PolicyDocument", {})
            if self._has_high_privilege(policies):
                high_priv.append(resource.id)
                continue

            # Check attached policies
            attached = config.get("AttachedPolicies", [])
            for policy in attached:
                policy_name = policy.get("PolicyName", "").lower()
                if "admin" in policy_name or "fullaccess" in policy_name:
                    high_priv.append(resource.id)
                    break

        return high_priv

    def _has_high_privilege(self, policy: dict) -> bool:
        """Check if a policy document grants high privileges."""
        statements = policy.get("Statement", [])
        if isinstance(statements, dict):
            statements = [statements]

        for stmt in statements:
            if stmt.get("Effect") != "Allow":
                continue

            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            for action in actions:
                if action in self.HIGH_PRIVILEGE_ACTIONS:
                    return True

        return False

    def find_public_resources(self) -> list[str]:
        """
        Find resources with public access.

        Returns:
            List of resource IDs with public access configured
        """
        public: list[str] = []

        for resource in self._graph.get_all_resources():
            config = resource.config or {}

            # S3 bucket public access
            if "s3" in str(resource.resource_type).lower():
                acl = config.get("ACL", "")
                if "public" in str(acl).lower():
                    public.append(resource.id)
                    continue

            # Check for public CIDR in security groups
            if "security_group" in str(resource.resource_type).lower():
                ingress = config.get("IpPermissions", [])
                for rule in ingress:
                    ranges = rule.get("IpRanges", [])
                    for ip_range in ranges:
                        if ip_range.get("CidrIp") == "0.0.0.0/0":
                            public.append(resource.id)
                            break

        return public

    def compute_attack_surface(self) -> AttackSurfaceResult:
        """
        Compute comprehensive attack surface analysis.

        Returns:
            AttackSurfaceResult with all findings
        """
        exposed = self.find_exposed_resources()
        high_priv = self.find_high_privilege_resources()
        public = self.find_public_resources()

        # Compute risk score (0-100)
        total_resources = self._graph.node_count or 1
        exposed_ratio = len(exposed) / total_resources
        priv_ratio = len(high_priv) / total_resources
        public_ratio = len(public) / total_resources

        # Weighted score
        risk_score = min(
            (exposed_ratio * 40 + priv_ratio * 35 + public_ratio * 25) * 100, 100
        )

        return AttackSurfaceResult(
            exposed_resources=exposed,
            high_privilege_resources=high_priv,
            public_resources=public,
            risk_score=risk_score,
        )


class CriticalResourceFinder:
    """
    Finds and ranks critical resources in the infrastructure.

    Combines multiple metrics to identify resources that are:
    - Single points of failure
    - High blast radius
    - Structurally important (betweenness, PageRank)
    - High attack surface
    """

    def __init__(self, graph: GraphEngine) -> None:
        """
        Initialize the finder.

        Args:
            graph: The GraphEngine to analyze
        """
        self._graph = graph
        self._centrality = CentralityAnalyzer(graph)
        self._attack_surface = AttackSurfaceAnalyzer(graph)

    def find_critical(self, top_n: int = 10) -> list[CriticalityResult]:
        """
        Find the most critical resources.

        Combines multiple metrics:
        - Blast radius (how many resources would be affected)
        - Betweenness centrality (bottleneck position)
        - In-degree (number of direct dependents)
        - Attack surface exposure

        Args:
            top_n: Number of critical resources to return

        Returns:
            List of CriticalityResult, sorted by criticality score
        """
        g = self._graph._graph
        betweenness = self._centrality.compute_betweenness_centrality()
        attack_surface = self._attack_surface.compute_attack_surface()

        # Build set of exposed resources for quick lookup
        exposed_set = set(attack_surface.exposed_resources)
        high_priv_set = set(attack_surface.high_privilege_resources)
        public_set = set(attack_surface.public_resources)

        results: list[CriticalityResult] = []

        for node_id in g.nodes():
            resource = self._graph.get_resource(node_id)
            if not resource:
                continue

            factors: list[str] = []
            score = 0.0

            # Compute blast radius
            blast = self._centrality.compute_blast_radius(node_id)
            if blast.affected_count > 0:
                # Normalize by total nodes
                blast_score = min(blast.affected_count / g.number_of_nodes() * 40, 40)
                score += blast_score
                if blast.affected_count >= 5:
                    factors.append(
                        f"High blast radius ({blast.affected_count} affected)"
                    )

            # Betweenness centrality
            node_betweenness = betweenness.get(node_id, 0)
            if node_betweenness > 0:
                betweenness_score = node_betweenness * 30
                score += betweenness_score
                if node_betweenness > 0.1:
                    factors.append("Network bottleneck")

            # In-degree (direct dependents)
            in_degree = g.in_degree(node_id)
            if in_degree > 0:
                degree_score = min(in_degree / 10 * 15, 15)
                score += degree_score
                if in_degree >= 3:
                    factors.append(f"SPOF ({in_degree} dependents)")

            # Attack surface
            if node_id in exposed_set:
                score += 10
                factors.append("Internet exposed")
            if node_id in high_priv_set:
                score += 5
                factors.append("High privileges")
            if node_id in public_set:
                score += 5
                factors.append("Public access")

            # Determine criticality level
            if score >= 60:
                level = CriticalityLevel.CRITICAL
            elif score >= 40:
                level = CriticalityLevel.HIGH
            elif score >= 20:
                level = CriticalityLevel.MEDIUM
            else:
                level = CriticalityLevel.LOW

            results.append(
                CriticalityResult(
                    resource_id=node_id,
                    resource_type=str(resource.resource_type),
                    level=level,
                    score=score,
                    factors=factors,
                    blast_radius=blast.affected_count,
                    dependent_count=in_degree,
                    betweenness=node_betweenness,
                )
            )

        # Sort by score (highest first)
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_n]

    def generate_report(self, top_n: int = 10) -> str:
        """
        Generate a human-readable critical resource report.

        Args:
            top_n: Number of critical resources to include

        Returns:
            Formatted report string
        """
        critical = self.find_critical(top_n)
        attack_surface = self._attack_surface.compute_attack_surface()

        lines = [
            "Critical Resource Analysis Report",
            "=" * 50,
            "",
            f"Total Resources: {self._graph.node_count}",
            f"Attack Surface Score: {attack_surface.risk_score:.1f}/100",
            f"  - Exposed: {len(attack_surface.exposed_resources)}",
            f"  - High Privilege: {len(attack_surface.high_privilege_resources)}",
            f"  - Public: {len(attack_surface.public_resources)}",
            "",
            f"Top {len(critical)} Critical Resources:",
            "-" * 50,
        ]

        for i, result in enumerate(critical, 1):
            level_str = result.level.value.upper()
            lines.append(f"\n{i}. {result.resource_id}")
            lines.append(f"   Type: {result.resource_type}")
            lines.append(f"   Criticality: {level_str} (score: {result.score:.1f})")
            lines.append(f"   Blast Radius: {result.blast_radius}")
            lines.append(f"   Direct Dependents: {result.dependent_count}")
            if result.factors:
                lines.append(f"   Factors: {', '.join(result.factors)}")

        return "\n".join(lines)
