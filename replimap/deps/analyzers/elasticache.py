"""
ElastiCache Cluster Dependency Analyzer.

Analyzes dependencies for Redis/Memcached clusters including:
- MANAGER: CloudFormation
- CONSUMERS: Applications connecting to cache
- DEPENDENCIES: Parameter Group, Subnet Group
- NETWORK: VPC, Subnets, Security Groups
- IDENTITY: KMS Key (encryption), Auth Token
- REPLICATION: Replication groups

ElastiCache is often critical for application performance - outages cause cascading failures.
"""

from __future__ import annotations

from typing import Any

from replimap.deps.base_analyzer import ResourceDependencyAnalyzer
from replimap.deps.models import (
    Dependency,
    DependencyAnalysis,
    RelationType,
    Severity,
)


class ElastiCacheAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for ElastiCache Clusters."""

    @property
    def resource_type(self) -> str:
        return "aws_elasticache_cluster"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze ElastiCache cluster dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"ElastiCache cluster not found: {resource_id}")

        tags = data.get("tags", {})

        # Build center resource
        center = Dependency(
            resource_type="aws_elasticache_cluster",
            resource_id=resource_id,
            resource_name=data.get("CacheClusterId", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.CRITICAL,
            metadata={
                "engine": data.get("Engine"),
                "engine_version": data.get("EngineVersion"),
                "node_type": data.get("CacheNodeType"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this cluster
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # REPLICATION - replication group membership
        replication = self._find_replication(data)
        if replication:
            dependencies[RelationType.REPLICATION] = replication

        # DEPENDENCIES - parameter group, subnet group
        deps = self._find_dependencies(data)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # NETWORK - VPC, Security Groups
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - KMS keys
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "cluster_id": data.get("CacheClusterId"),
            "engine": data.get("Engine"),
            "engine_version": data.get("EngineVersion"),
            "node_type": data.get("CacheNodeType"),
            "num_nodes": data.get("NumCacheNodes"),
            "status": data.get("CacheClusterStatus"),
            "endpoint": self._get_endpoint(data),
            "az_mode": data.get("AZMode"),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get ElastiCache cluster data from AWS API."""
        if not self.elasticache:
            return {}

        try:
            response = self.elasticache.describe_cache_clusters(
                CacheClusterId=resource_id,
                ShowCacheNodeInfo=True,
            )
            clusters = response.get("CacheClusters", [])
            if clusters:
                data = clusters[0]
                # Get tags
                try:
                    # Build ARN
                    arn = data.get("ARN")
                    if arn:
                        tags_response = self.elasticache.list_tags_for_resource(
                            ResourceName=arn
                        )
                        data["tags"] = {
                            t["Key"]: t["Value"]
                            for t in tags_response.get("TagList", [])
                        }
                except Exception:  # noqa: S110
                    data["tags"] = {}
                return data
        except Exception:  # noqa: S110
            pass

        return {}

    def _get_endpoint(self, data: dict[str, Any]) -> str | None:
        """Get the cluster endpoint."""
        # For Redis
        config_endpoint = data.get("ConfigurationEndpoint", {})
        if config_endpoint:
            return f"{config_endpoint.get('Address')}:{config_endpoint.get('Port')}"

        # For Memcached or single-node Redis
        nodes = data.get("CacheNodes", [])
        if nodes:
            endpoint = nodes[0].get("Endpoint", {})
            return f"{endpoint.get('Address')}:{endpoint.get('Port')}"

        return None

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this cluster."""
        managers = []

        # CloudFormation
        cfn_stack = tags.get("aws:cloudformation:stack-name")
        if cfn_stack:
            managers.append(
                Dependency(
                    resource_type="aws_cloudformation_stack",
                    resource_id=cfn_stack,
                    resource_name=cfn_stack,
                    relation_type=RelationType.MANAGER,
                    severity=Severity.HIGH,
                    warning=f"Managed by CloudFormation stack '{cfn_stack}'",
                )
            )

        return managers

    def _find_replication(self, data: dict[str, Any]) -> list[Dependency]:
        """Find replication group membership."""
        replication = []

        rg_id = data.get("ReplicationGroupId")
        if rg_id:
            replication.append(
                Dependency(
                    resource_type="aws_elasticache_replication_group",
                    resource_id=rg_id,
                    resource_name=rg_id,
                    relation_type=RelationType.REPLICATION,
                    severity=Severity.HIGH,
                    warning="Part of replication group - failover possible",
                )
            )

        return replication

    def _find_dependencies(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources this cluster depends on."""
        dependencies = []

        # Parameter Group
        pg = data.get("CacheParameterGroup", {})
        pg_name = pg.get("CacheParameterGroupName")
        if pg_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_elasticache_parameter_group",
                    resource_id=pg_name,
                    resource_name=pg_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                    metadata={"status": pg.get("ParameterApplyStatus")},
                )
            )

        # Subnet Group
        sg_name = data.get("CacheSubnetGroupName")
        if sg_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_elasticache_subnet_group",
                    resource_id=sg_name,
                    resource_name=sg_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                )
            )

        return dependencies

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network dependencies."""
        network = []

        # Security Groups
        for sg in data.get("SecurityGroups", []):
            sg_id = sg.get("SecurityGroupId")
            if sg_id:
                network.append(
                    Dependency(
                        resource_type="aws_security_group",
                        resource_id=sg_id,
                        relation_type=RelationType.NETWORK,
                        severity=Severity.MEDIUM,
                        metadata={"status": sg.get("Status")},
                    )
                )

        # Try to get VPC from cache nodes
        nodes = data.get("CacheNodes", [])
        if nodes:
            # ElastiCache doesn't directly expose VPC ID
            # Would need to query subnet group for VPC info
            pass

        return network

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # Note: ElastiCache doesn't expose KMS key ID directly in describe_cache_clusters
        # AtRestEncryptionEnabled is a boolean, not a key ID
        # Would need to check replication group for encryption settings

        # Auth token (if transit encryption enabled)
        if data.get("TransitEncryptionEnabled"):
            identity.append(
                Dependency(
                    resource_type="aws_elasticache_auth_token",
                    resource_id="auth-token",
                    resource_name="Transit Encryption Token",
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.HIGH,
                    warning="Transit encryption enabled - auth token required",
                )
            )

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to ElastiCache."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Replication group warning
        replication = dependencies.get(RelationType.REPLICATION, [])
        if replication:
            warnings.insert(
                0,
                "Part of replication group - changes may trigger failover",
            )
        else:
            warnings.insert(
                0,
                "Standalone cluster - no automatic failover configured",
            )

        # Engine-specific warnings
        engine = center.metadata.get("engine")
        if engine == "redis":
            warnings.append(
                "Redis cluster - ensure clients handle connection drops gracefully"
            )
        elif engine == "memcached":
            warnings.append(
                "Memcached cluster - data is not persistent, restart clears cache"
            )

        return warnings
