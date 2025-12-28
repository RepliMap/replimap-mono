"""
Unified Async Scanners for RepliMap.

This module provides async scanners that use the resilient AsyncAWSClient
with integrated circuit breaker, rate limiting, and retry logic.

These scanners are designed for high-throughput scanning of large AWS
environments while gracefully handling API throttling and transient errors.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from replimap.core.async_aws import AWSResourceScanner
from replimap.core.circuit_breaker import CircuitOpenError
from replimap.core.models import DependencyType, ResourceNode, ResourceType

if TYPE_CHECKING:
    from replimap.core import GraphEngine

logger = logging.getLogger(__name__)


class UnifiedScannerRegistry:
    """
    Registry for unified async scanners.

    Provides centralized management of scanner classes and execution.
    """

    _scanners: ClassVar[list[type[AWSResourceScanner]]] = []

    @classmethod
    def register(
        cls, scanner_class: type[AWSResourceScanner]
    ) -> type[AWSResourceScanner]:
        """Register a scanner class."""
        if scanner_class not in cls._scanners:
            cls._scanners.append(scanner_class)
            logger.debug(f"Registered unified scanner: {scanner_class.__name__}")
        return scanner_class

    @classmethod
    def get_all(cls) -> list[type[AWSResourceScanner]]:
        """Get all registered scanner classes."""
        return cls._scanners.copy()

    @classmethod
    def clear(cls) -> None:
        """Clear all registered scanners (for testing)."""
        cls._scanners.clear()


@UnifiedScannerRegistry.register
class AsyncEC2Scanner(AWSResourceScanner):
    """
    Async scanner for EC2 instances with full resilience.

    Uses AsyncAWSClient for:
    - Circuit breaker per region/service
    - Rate limiting (20 req/s for EC2)
    - Automatic retry with exponential backoff

    Captures:
    - Instance type, AMI, key pair
    - Network configuration (VPC, subnet, security groups)
    - Storage configuration (EBS volumes)
    - IAM instance profile
    - Metadata options
    """

    resource_types: ClassVar[list[str]] = ["aws_instance"]

    async def scan(self, graph: GraphEngine) -> None:
        """Scan all EC2 instances in the region."""
        logger.info(f"Async scanning EC2 instances in {self.region}...")

        try:
            # Use paginate_with_resilience for full retry per page
            reservations = await self.client.paginate_with_resilience(
                "ec2",
                "describe_instances",
                "Reservations",
            )

            instance_count = 0
            for reservation in reservations:
                for instance in reservation.get("Instances", []):
                    if self._process_instance(instance, graph):
                        instance_count += 1

            logger.info(f"Scanned {instance_count} EC2 instances in {self.region}")

        except CircuitOpenError as e:
            logger.warning(f"Circuit open for EC2 in {self.region}: {e}")
            raise

    def _process_instance(self, instance: dict[str, Any], graph: GraphEngine) -> bool:
        """
        Process a single EC2 instance.

        Returns True if instance was added, False if skipped.
        """
        instance_id = instance["InstanceId"]
        state = instance.get("State", {}).get("Name", "unknown")

        # Only include running instances
        if state != "running":
            logger.debug(f"Skipping {state} instance: {instance_id}")
            return False

        tags = self.extract_tags(instance.get("Tags"))
        subnet_id = instance.get("SubnetId")
        vpc_id = instance.get("VpcId")

        # Extract security group IDs
        security_groups = [sg["GroupId"] for sg in instance.get("SecurityGroups", [])]

        # Extract block device mappings
        block_devices = []
        for mapping in instance.get("BlockDeviceMappings", []):
            ebs = mapping.get("Ebs", {})
            block_devices.append(
                {
                    "device_name": mapping["DeviceName"],
                    "volume_id": ebs.get("VolumeId"),
                    "delete_on_termination": ebs.get("DeleteOnTermination", True),
                }
            )

        # Extract network interfaces
        network_interfaces = []
        for eni in instance.get("NetworkInterfaces", []):
            network_interfaces.append(
                {
                    "network_interface_id": eni["NetworkInterfaceId"],
                    "device_index": eni["Attachment"]["DeviceIndex"],
                    "subnet_id": eni.get("SubnetId"),
                    "private_ip_address": eni.get("PrivateIpAddress"),
                    "security_groups": [sg["GroupId"] for sg in eni.get("Groups", [])],
                }
            )

        config = {
            "ami": instance["ImageId"],
            "instance_type": instance["InstanceType"],
            "key_name": instance.get("KeyName"),
            "subnet_id": subnet_id,
            "vpc_id": vpc_id,
            "security_group_ids": security_groups,
            "private_ip_address": instance.get("PrivateIpAddress"),
            "public_ip_address": instance.get("PublicIpAddress"),
            "availability_zone": instance.get("Placement", {}).get("AvailabilityZone"),
            "tenancy": instance.get("Placement", {}).get("Tenancy", "default"),
            "ebs_optimized": instance.get("EbsOptimized", False),
            "monitoring": instance.get("Monitoring", {}).get("State") == "enabled",
            "iam_instance_profile": self._extract_iam_profile(
                instance.get("IamInstanceProfile")
            ),
            "block_device_mappings": block_devices,
            "network_interfaces": network_interfaces,
            "metadata_options": self._extract_metadata_options(
                instance.get("MetadataOptions", {})
            ),
            "state": state,
        }

        # Get root volume info
        root_device_name = instance.get("RootDeviceName")
        if root_device_name:
            for bd in block_devices:
                if bd["device_name"] == root_device_name:
                    config["root_block_device"] = {
                        "device_name": bd["device_name"],
                        "delete_on_termination": bd.get("delete_on_termination", True),
                    }
                    break

        node = ResourceNode(
            id=self.build_node_id(instance_id) if self.account_id else instance_id,
            resource_type=ResourceType.EC2_INSTANCE,
            region=self.region,
            config=config,
            arn=f"arn:aws:ec2:{self.region}:{instance.get('OwnerId', '')}:instance/{instance_id}",
            tags=tags,
        )

        graph.add_resource(node)

        # Establish dependencies
        if subnet_id and graph.get_resource(subnet_id):
            graph.add_dependency(node.id, subnet_id, DependencyType.BELONGS_TO)

        for sg_id in security_groups:
            if graph.get_resource(sg_id):
                graph.add_dependency(node.id, sg_id, DependencyType.USES)

        logger.debug(
            f"Added EC2: {instance_id} ({tags.get('Name', 'unnamed')}) "
            f"- {instance['InstanceType']}"
        )
        return True

    def _extract_iam_profile(
        self, profile: dict[str, Any] | None
    ) -> dict[str, str] | None:
        """Extract IAM instance profile information."""
        if not profile:
            return None
        arn = profile.get("Arn", "")
        return {
            "arn": arn,
            "name": arn.split("/")[-1] if arn else "",
        }

    def _extract_metadata_options(self, options: dict[str, Any]) -> dict[str, Any]:
        """Extract instance metadata options."""
        return {
            "http_endpoint": options.get("HttpEndpoint", "enabled"),
            "http_tokens": options.get("HttpTokens", "optional"),
            "http_put_response_hop_limit": options.get("HttpPutResponseHopLimit", 1),
            "instance_metadata_tags": options.get("InstanceMetadataTags", "disabled"),
        }


@UnifiedScannerRegistry.register
class AsyncRDSScanner(AWSResourceScanner):
    """
    Async scanner for RDS instances and DB subnet groups.

    Uses AsyncAWSClient for resilient API calls with:
    - Circuit breaker per region/service
    - Rate limiting (10 req/s for RDS)
    - Automatic retry with exponential backoff

    Captures:
    - DB instance configuration (engine, version, class)
    - Storage configuration (type, size, encryption)
    - Network configuration (subnet groups, security groups)
    - Backup and maintenance settings

    Does NOT capture:
    - Master password
    - Snapshots
    - Performance Insights data
    """

    resource_types: ClassVar[list[str]] = [
        "aws_db_instance",
        "aws_db_subnet_group",
    ]

    async def scan(self, graph: GraphEngine) -> None:
        """Scan all RDS resources in the region."""
        logger.info(f"Async scanning RDS resources in {self.region}...")

        try:
            # Scan DB subnet groups first (dependency for instances)
            await self._scan_db_subnet_groups(graph)

            # Then scan DB instances
            await self._scan_db_instances(graph)

        except CircuitOpenError as e:
            logger.warning(f"Circuit open for RDS in {self.region}: {e}")
            raise

    async def _scan_db_subnet_groups(self, graph: GraphEngine) -> None:
        """Scan all DB subnet groups."""
        logger.debug("Async scanning DB Subnet Groups...")

        groups = await self.client.paginate_with_resilience(
            "rds",
            "describe_db_subnet_groups",
            "DBSubnetGroups",
        )

        for group in groups:
            group_name = group["DBSubnetGroupName"]

            subnet_ids = [
                subnet["SubnetIdentifier"] for subnet in group.get("Subnets", [])
            ]

            config = {
                "name": group_name,
                "description": group.get("DBSubnetGroupDescription", ""),
                "subnet_ids": subnet_ids,
                "vpc_id": group.get("VpcId"),
            }

            tags = {"Name": group_name}

            node_id = self.build_node_id(group_name) if self.account_id else group_name

            node = ResourceNode(
                id=node_id,
                resource_type=ResourceType.DB_SUBNET_GROUP,
                region=self.region,
                config=config,
                arn=group.get("DBSubnetGroupArn"),
                tags=tags,
            )

            graph.add_resource(node)

            # Add dependencies to subnets
            for subnet_id in subnet_ids:
                if graph.get_resource(subnet_id):
                    graph.add_dependency(node_id, subnet_id, DependencyType.REFERENCES)

            logger.debug(f"Added DB Subnet Group: {group_name}")

    async def _scan_db_instances(self, graph: GraphEngine) -> None:
        """Scan all RDS DB instances."""
        logger.debug("Async scanning RDS instances...")

        instances = await self.client.paginate_with_resilience(
            "rds",
            "describe_db_instances",
            "DBInstances",
        )

        instance_count = 0
        for instance in instances:
            if self._process_db_instance(instance, graph):
                instance_count += 1

        logger.info(f"Scanned {instance_count} RDS instances in {self.region}")

    def _process_db_instance(
        self, instance: dict[str, Any], graph: GraphEngine
    ) -> bool:
        """
        Process a single RDS DB instance.

        Returns True if instance was added, False if skipped.
        """
        db_id = instance["DBInstanceIdentifier"]
        status = instance.get("DBInstanceStatus", "unknown")

        # Skip instances being deleted
        if status in ("deleting", "deleted"):
            logger.debug(f"Skipping deleted RDS instance: {db_id}")
            return False

        # Extract security group IDs
        security_groups = [
            sg["VpcSecurityGroupId"] for sg in instance.get("VpcSecurityGroups", [])
        ]

        # Extract parameter groups
        parameter_groups = [
            {
                "name": pg["DBParameterGroupName"],
                "status": pg.get("ParameterApplyStatus", ""),
            }
            for pg in instance.get("DBParameterGroups", [])
        ]

        # Extract option groups
        option_groups = [
            og["OptionGroupName"] for og in instance.get("OptionGroupMemberships", [])
        ]

        config = {
            "identifier": db_id,
            "engine": instance["Engine"],
            "engine_version": instance.get("EngineVersion"),
            "instance_class": instance["DBInstanceClass"],
            "allocated_storage": instance.get("AllocatedStorage"),
            "storage_type": instance.get("StorageType", "gp2"),
            "storage_encrypted": instance.get("StorageEncrypted", False),
            "kms_key_id": instance.get("KmsKeyId"),
            "multi_az": instance.get("MultiAZ", False),
            "availability_zone": instance.get("AvailabilityZone"),
            "db_subnet_group_name": instance.get("DBSubnetGroup", {}).get(
                "DBSubnetGroupName"
            ),
            "vpc_security_group_ids": security_groups,
            "parameter_group_name": (
                parameter_groups[0]["name"] if parameter_groups else None
            ),
            "option_group_name": option_groups[0] if option_groups else None,
            "backup_retention_period": instance.get("BackupRetentionPeriod", 0),
            "backup_window": instance.get("PreferredBackupWindow"),
            "maintenance_window": instance.get("PreferredMaintenanceWindow"),
            "auto_minor_version_upgrade": instance.get("AutoMinorVersionUpgrade", True),
            "publicly_accessible": instance.get("PubliclyAccessible", False),
            "deletion_protection": instance.get("DeletionProtection", False),
            "db_name": instance.get("DBName"),
            "port": (
                instance.get("DbInstancePort")
                or instance.get("Endpoint", {}).get("Port")
            ),
            "master_username": instance.get("MasterUsername"),
            "iam_database_authentication_enabled": instance.get(
                "IAMDatabaseAuthenticationEnabled", False
            ),
            "performance_insights_enabled": instance.get(
                "PerformanceInsightsEnabled", False
            ),
            "enabled_cloudwatch_logs_exports": instance.get(
                "EnabledCloudwatchLogsExports", []
            ),
            "status": status,
            "endpoint": instance.get("Endpoint", {}).get("Address"),
        }

        # Get tags
        tags = {tag["Key"]: tag["Value"] for tag in instance.get("TagList", [])}
        if "Name" not in tags:
            tags["Name"] = db_id

        node_id = self.build_node_id(db_id) if self.account_id else db_id

        node = ResourceNode(
            id=node_id,
            resource_type=ResourceType.RDS_INSTANCE,
            region=self.region,
            config=config,
            arn=instance.get("DBInstanceArn"),
            tags=tags,
        )

        graph.add_resource(node)

        # Add dependencies
        for sg_id in security_groups:
            if graph.get_resource(sg_id):
                graph.add_dependency(node_id, sg_id, DependencyType.USES)

        subnet_group = config.get("db_subnet_group_name")
        if subnet_group and graph.get_resource(subnet_group):
            graph.add_dependency(node_id, subnet_group, DependencyType.REFERENCES)

        logger.debug(
            f"Added RDS: {db_id} ({instance['Engine']} {instance['DBInstanceClass']})"
        )
        return True


@UnifiedScannerRegistry.register
class AsyncIAMScanner(AWSResourceScanner):
    """
    Async scanner for IAM roles and policies.

    IAM is a global service, so this scanner uses region="global".

    Uses AsyncAWSClient for resilient API calls with:
    - Circuit breaker for IAM service
    - Rate limiting (5 req/s for IAM - stricter limits)
    - Automatic retry with exponential backoff

    Captures:
    - IAM roles with trust policies
    - Attached managed policies
    - Inline policies (by reference)
    - Instance profiles

    Does NOT capture:
    - User credentials
    - Access keys
    - MFA devices
    """

    resource_types: ClassVar[list[str]] = [
        "aws_iam_role",
        "aws_iam_policy",
        "aws_iam_instance_profile",
    ]

    async def scan(self, graph: GraphEngine) -> None:
        """Scan all IAM resources."""
        # IAM is global, but we use the provided region for client creation
        logger.info("Async scanning IAM resources (global)...")

        try:
            # Scan in order: policies -> roles -> instance profiles
            await self._scan_policies(graph)
            await self._scan_roles(graph)
            await self._scan_instance_profiles(graph)

        except CircuitOpenError as e:
            logger.warning(f"Circuit open for IAM: {e}")
            raise

    async def _scan_policies(self, graph: GraphEngine) -> None:
        """Scan customer-managed IAM policies."""
        logger.debug("Async scanning IAM policies...")

        # Only scan customer-managed policies (not AWS-managed)
        policies = await self.client.paginate_with_resilience(
            "iam",
            "list_policies",
            "Policies",
            Scope="Local",  # Only customer-managed policies
        )

        for policy in policies:
            policy_arn = policy["Arn"]
            policy_name = policy["PolicyName"]

            config = {
                "name": policy_name,
                "path": policy.get("Path", "/"),
                "description": policy.get("Description", ""),
                "default_version_id": policy.get("DefaultVersionId"),
                "attachment_count": policy.get("AttachmentCount", 0),
                "is_attachable": policy.get("IsAttachable", True),
            }

            node_id = (
                self.build_node_id(policy_name) if self.account_id else policy_name
            )

            node = ResourceNode(
                id=node_id,
                resource_type=ResourceType.IAM_POLICY,
                region="global",
                config=config,
                arn=policy_arn,
                tags={"Name": policy_name},
            )

            graph.add_resource(node)
            logger.debug(f"Added IAM Policy: {policy_name}")

    async def _scan_roles(self, graph: GraphEngine) -> None:
        """Scan IAM roles."""
        logger.debug("Async scanning IAM roles...")

        roles = await self.client.paginate_with_resilience(
            "iam",
            "list_roles",
            "Roles",
        )

        role_count = 0
        for role in roles:
            # Skip AWS service-linked roles
            if role.get("Path", "").startswith("/aws-service-role/"):
                continue

            role_name = role["RoleName"]

            # Get attached policies for this role
            attached_policies = await self._get_attached_policies(role_name)

            config = {
                "name": role_name,
                "path": role.get("Path", "/"),
                "description": role.get("Description", ""),
                "assume_role_policy": role.get("AssumeRolePolicyDocument"),
                "max_session_duration": role.get("MaxSessionDuration", 3600),
                "attached_policies": attached_policies,
            }

            # Get tags
            tags = {tag["Key"]: tag["Value"] for tag in role.get("Tags", [])}
            if "Name" not in tags:
                tags["Name"] = role_name

            node_id = self.build_node_id(role_name) if self.account_id else role_name

            node = ResourceNode(
                id=node_id,
                resource_type=ResourceType.IAM_ROLE,
                region="global",
                config=config,
                arn=role["Arn"],
                tags=tags,
            )

            graph.add_resource(node)
            role_count += 1

            logger.debug(f"Added IAM Role: {role_name}")

        logger.info(f"Scanned {role_count} IAM roles")

    async def _get_attached_policies(self, role_name: str) -> list[dict[str, str]]:
        """Get policies attached to a role."""
        try:
            policies = await self.client.paginate_with_resilience(
                "iam",
                "list_attached_role_policies",
                "AttachedPolicies",
                RoleName=role_name,
            )
            return [{"name": p["PolicyName"], "arn": p["PolicyArn"]} for p in policies]
        except Exception as e:
            logger.debug(f"Could not get attached policies for {role_name}: {e}")
            return []

    async def _scan_instance_profiles(self, graph: GraphEngine) -> None:
        """Scan IAM instance profiles."""
        logger.debug("Async scanning IAM instance profiles...")

        profiles = await self.client.paginate_with_resilience(
            "iam",
            "list_instance_profiles",
            "InstanceProfiles",
        )

        for profile in profiles:
            profile_name = profile["InstanceProfileName"]

            # Get associated roles
            roles = [
                {"name": r["RoleName"], "arn": r["Arn"]}
                for r in profile.get("Roles", [])
            ]

            config = {
                "name": profile_name,
                "path": profile.get("Path", "/"),
                "roles": roles,
            }

            node_id = (
                self.build_node_id(profile_name) if self.account_id else profile_name
            )

            node = ResourceNode(
                id=node_id,
                resource_type=ResourceType.IAM_INSTANCE_PROFILE,
                region="global",
                config=config,
                arn=profile["Arn"],
                tags={"Name": profile_name},
            )

            graph.add_resource(node)

            # Add dependencies to roles
            for role in roles:
                role_id = (
                    self.build_node_id(role["name"])
                    if self.account_id
                    else role["name"]
                )
                if graph.get_resource(role_id):
                    graph.add_dependency(node_id, role_id, DependencyType.REFERENCES)

            logger.debug(f"Added IAM Instance Profile: {profile_name}")


async def run_unified_scanners(
    region: str,
    graph: GraphEngine,
    account_id: str | None = None,
    profile: str | None = None,
    concurrency: int = 4,
) -> dict[str, Exception | None]:
    """
    Run all registered unified scanners concurrently.

    Args:
        region: AWS region to scan
        graph: GraphEngine to populate
        account_id: AWS account ID (optional)
        profile: AWS profile name (optional)
        concurrency: Maximum concurrent scanners

    Returns:
        Dictionary mapping scanner names to exceptions (None if successful)
    """
    results: dict[str, Exception | None] = {}
    semaphore = asyncio.Semaphore(concurrency)

    async def run_scanner(scanner_class: type[AWSResourceScanner]) -> None:
        scanner_name = scanner_class.__name__
        async with semaphore:
            logger.info(f"Running {scanner_name}...")
            try:
                async with scanner_class(
                    region=region,
                    account_id=account_id,
                    profile=profile,
                ) as scanner:
                    await scanner.scan(graph)
                results[scanner_name] = None
                logger.info(f"{scanner_name} completed successfully")
            except Exception as e:
                results[scanner_name] = e
                logger.error(f"{scanner_name} failed: {e}")

    # Run all scanners concurrently
    await asyncio.gather(
        *[run_scanner(sc) for sc in UnifiedScannerRegistry.get_all()],
        return_exceptions=True,
    )

    return results
