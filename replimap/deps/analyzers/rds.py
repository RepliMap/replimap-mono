"""
RDS Instance Dependency Analyzer.

Analyzes dependencies for RDS instances including:
- MANAGER: CloudFormation
- CONSUMERS: Read replicas
- DEPENDENCIES: Parameter Group, Option Group, Subnet Group
- NETWORK: VPC, Security Groups
- IDENTITY: IAM Role (monitoring), KMS Key (encryption)

RDS instances are critical infrastructure - changes require careful planning.
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


class RDSInstanceAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for RDS Database Instances."""

    @property
    def resource_type(self) -> str:
        return "aws_db_instance"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze RDS instance dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"RDS instance not found: {resource_id}")

        tags = {t["Key"]: t["Value"] for t in data.get("TagList", [])}

        # Build center resource
        center = Dependency(
            resource_type="aws_db_instance",
            resource_id=resource_id,
            resource_name=data.get("DBInstanceIdentifier", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.CRITICAL,
            metadata={
                "engine": data.get("Engine"),
                "engine_version": data.get("EngineVersion"),
                "instance_class": data.get("DBInstanceClass"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this RDS instance
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # CONSUMERS - what depends on this RDS instance
        consumers = self._find_consumers(resource_id, data)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # DEPENDENCIES - what this RDS depends on
        deps = self._find_dependencies(data)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # NETWORK - network context
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - permission/encryption context
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "db_instance_identifier": data.get("DBInstanceIdentifier"),
            "engine": data.get("Engine"),
            "engine_version": data.get("EngineVersion"),
            "instance_class": data.get("DBInstanceClass"),
            "status": data.get("DBInstanceStatus"),
            "multi_az": data.get("MultiAZ"),
            "storage_type": data.get("StorageType"),
            "allocated_storage": data.get("AllocatedStorage"),
            "endpoint": data.get("Endpoint", {}).get("Address"),
            "port": data.get("Endpoint", {}).get("Port"),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get RDS instance data from AWS API."""
        if not self.rds:
            return {}

        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=resource_id)
            instances = response.get("DBInstances", [])
            if instances:
                return instances[0]
        except Exception:
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this RDS instance."""
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

    def _find_consumers(self, db_id: str, data: dict[str, Any]) -> list[Dependency]:
        """Find resources that depend on this RDS instance."""
        consumers = []

        # Read replicas depend on this source instance
        read_replicas = data.get("ReadReplicaDBInstanceIdentifiers", [])
        for replica_id in read_replicas:
            consumers.append(
                Dependency(
                    resource_type="aws_db_instance",
                    resource_id=replica_id,
                    resource_name=replica_id,
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                    warning="Read replica depends on this source database",
                    metadata={"type": "read_replica"},
                )
            )

        # Read replica clusters (Aurora)
        replica_clusters = data.get("ReadReplicaDBClusterIdentifiers", [])
        for cluster_id in replica_clusters:
            consumers.append(
                Dependency(
                    resource_type="aws_rds_cluster",
                    resource_id=cluster_id,
                    resource_name=cluster_id,
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                    warning="Read replica cluster depends on this source",
                    metadata={"type": "replica_cluster"},
                )
            )

        return consumers

    def _find_dependencies(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources this RDS instance depends on."""
        dependencies = []

        # Source DB instance (if this is a replica)
        source_id = data.get("ReadReplicaSourceDBInstanceIdentifier")
        if source_id:
            dependencies.append(
                Dependency(
                    resource_type="aws_db_instance",
                    resource_id=source_id,
                    resource_name=source_id,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.CRITICAL,
                    warning="This is a read replica - depends on source database",
                    metadata={"type": "source_instance"},
                )
            )

        # Source cluster (Aurora replica)
        source_cluster = data.get("ReadReplicaSourceDBClusterIdentifier")
        if source_cluster:
            dependencies.append(
                Dependency(
                    resource_type="aws_rds_cluster",
                    resource_id=source_cluster,
                    resource_name=source_cluster,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.CRITICAL,
                    metadata={"type": "source_cluster"},
                )
            )

        # DB Subnet Group
        subnet_group = data.get("DBSubnetGroup", {})
        subnet_group_name = subnet_group.get("DBSubnetGroupName")
        if subnet_group_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_db_subnet_group",
                    resource_id=subnet_group_name,
                    resource_name=subnet_group_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                    metadata={"vpc_id": subnet_group.get("VpcId")},
                )
            )

        # Parameter Group
        for pg in data.get("DBParameterGroups", []):
            pg_name = pg.get("DBParameterGroupName")
            if pg_name:
                dependencies.append(
                    Dependency(
                        resource_type="aws_db_parameter_group",
                        resource_id=pg_name,
                        resource_name=pg_name,
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.MEDIUM,
                        metadata={"status": pg.get("ParameterApplyStatus")},
                    )
                )

        # Option Group
        for og in data.get("OptionGroupMemberships", []):
            og_name = og.get("OptionGroupName")
            if og_name:
                dependencies.append(
                    Dependency(
                        resource_type="aws_db_option_group",
                        resource_id=og_name,
                        resource_name=og_name,
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.MEDIUM,
                        metadata={"status": og.get("Status")},
                    )
                )

        return dependencies

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network dependencies."""
        network = []

        # VPC from subnet group
        subnet_group = data.get("DBSubnetGroup", {})
        vpc_id = subnet_group.get("VpcId")
        if vpc_id:
            network.append(
                Dependency(
                    resource_type="aws_vpc",
                    resource_id=vpc_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.INFO,
                )
            )

            # Subnets
            for subnet in subnet_group.get("Subnets", []):
                subnet_id = subnet.get("SubnetIdentifier")
                if subnet_id:
                    network.append(
                        Dependency(
                            resource_type="aws_subnet",
                            resource_id=subnet_id,
                            relation_type=RelationType.NETWORK,
                            severity=Severity.INFO,
                            metadata={
                                "availability_zone": subnet.get(
                                    "SubnetAvailabilityZone", {}
                                ).get("Name")
                            },
                        )
                    )

        # Security Groups
        for sg in data.get("VpcSecurityGroups", []):
            sg_id = sg.get("VpcSecurityGroupId")
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

        return network

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # KMS Key for encryption
        kms_key_id = data.get("KmsKeyId")
        if kms_key_id:
            identity.append(
                Dependency(
                    resource_type="aws_kms_key",
                    resource_id=kms_key_id,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.HIGH,
                    warning="Database encryption key - do not delete!",
                    metadata={"encrypted": True},
                )
            )

        # Performance Insights KMS Key
        pi_kms_key = data.get("PerformanceInsightsKMSKeyId")
        if pi_kms_key and pi_kms_key != kms_key_id:
            identity.append(
                Dependency(
                    resource_type="aws_kms_key",
                    resource_id=pi_kms_key,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.MEDIUM,
                    metadata={"purpose": "performance_insights"},
                )
            )

        # Enhanced Monitoring IAM Role
        monitoring_role = data.get("MonitoringRoleArn")
        if monitoring_role:
            role_name = (
                monitoring_role.split("/")[-1]
                if "/" in monitoring_role
                else monitoring_role
            )
            identity.append(
                Dependency(
                    resource_type="aws_iam_role",
                    resource_id=monitoring_role,
                    resource_name=role_name,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.MEDIUM,
                    metadata={"purpose": "enhanced_monitoring"},
                )
            )

        # Associated IAM Roles (for S3 integration, etc.)
        for role in data.get("AssociatedRoles", []):
            role_arn = role.get("RoleArn")
            if role_arn:
                role_name = role_arn.split("/")[-1] if "/" in role_arn else role_arn
                identity.append(
                    Dependency(
                        resource_type="aws_iam_role",
                        resource_id=role_arn,
                        resource_name=role_name,
                        relation_type=RelationType.IDENTITY,
                        severity=Severity.MEDIUM,
                        metadata={
                            "feature": role.get("FeatureName"),
                            "status": role.get("Status"),
                        },
                    )
                )

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to RDS instances."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Multi-AZ warning
        if center.metadata.get("multi_az"):
            warnings.insert(0, "Multi-AZ enabled - failover may occur during changes")

        # Read replica warning
        consumers = dependencies.get(RelationType.CONSUMER, [])
        replicas = [c for c in consumers if c.metadata.get("type") == "read_replica"]
        if replicas:
            warnings.insert(
                0,
                f"This database has {len(replicas)} read replica(s) - "
                "changes will replicate downstream",
            )

        # Is a replica warning
        deps = dependencies.get(RelationType.DEPENDENCY, [])
        source = [d for d in deps if d.metadata.get("type") == "source_instance"]
        if source:
            warnings.insert(
                0,
                "This is a READ REPLICA - some operations must be "
                "performed on the source instance",
            )

        return warnings
