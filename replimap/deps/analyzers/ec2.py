"""
EC2 Instance Dependency Analyzer.

Analyzes dependencies for EC2 instances including:
- MANAGER: ASG, CloudFormation, Spot Fleet
- CONSUMERS: Target Groups, Route53 records
- DEPENDENCIES: AMI, EBS, Key Pair, IAM Profile
- NETWORK: VPC, Subnet, Security Groups, ENI
- IDENTITY: IAM Role, KMS Keys
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


class EC2Analyzer(ResourceDependencyAnalyzer):
    """Analyzer for EC2 instances."""

    @property
    def resource_type(self) -> str:
        return "aws_instance"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze EC2 instance dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"Instance not found: {resource_id}")

        tags = {t["Key"]: t["Value"] for t in data.get("Tags", [])}

        # Build center resource
        center = Dependency(
            resource_type="aws_instance",
            resource_id=resource_id,
            resource_name=tags.get("Name", resource_id),
            relation_type=RelationType.DEPENDENCY,  # self
            severity=Severity.HIGH,
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this instance's lifecycle
        managers = self._find_managers(data, tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # CONSUMERS - who depends on this instance (blast radius)
        consumers = self._find_consumers(resource_id, data)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # DEPENDENCIES - what this instance depends on
        deps = self._find_dependencies(data)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # NETWORK - network context
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - permission context
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "instance_type": data.get("InstanceType"),
            "availability_zone": data.get("Placement", {}).get("AvailabilityZone"),
            "vpc_id": data.get("VpcId"),
            "subnet_id": data.get("SubnetId"),
            "private_ip": data.get("PrivateIpAddress"),
            "public_ip": data.get("PublicIpAddress"),
            "state": data.get("State", {}).get("Name"),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get EC2 instance data from AWS API."""
        if not self.ec2:
            return {}

        try:
            response = self.ec2.describe_instances(InstanceIds=[resource_id])
            reservations = response.get("Reservations", [])
            if reservations:
                instances = reservations[0].get("Instances", [])
                if instances:
                    return instances[0]
        except Exception:
            pass

        return {}

    def _find_managers(
        self, data: dict[str, Any], tags: dict[str, str]
    ) -> list[Dependency]:
        """Find resources that control this instance's lifecycle."""
        managers = []

        # Auto Scaling Group
        asg_name = tags.get("aws:autoscaling:groupName")
        if asg_name:
            managers.append(
                Dependency(
                    resource_type="aws_autoscaling_group",
                    resource_id=asg_name,
                    resource_name=asg_name,
                    relation_type=RelationType.MANAGER,
                    severity=Severity.CRITICAL,
                    warning=(
                        f"Instance is managed by ASG '{asg_name}'. "
                        "Manual changes will be REVERTED by Auto Scaling!"
                    ),
                    metadata={"type": "asg"},
                )
            )

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
                    metadata={"type": "cfn"},
                )
            )

        # Spot Fleet Request
        spot_fleet_id = tags.get("aws:ec2spot:fleet-request-id")
        if spot_fleet_id:
            managers.append(
                Dependency(
                    resource_type="aws_spot_fleet_request",
                    resource_id=spot_fleet_id,
                    resource_name=spot_fleet_id,
                    relation_type=RelationType.MANAGER,
                    severity=Severity.HIGH,
                    warning="Managed by Spot Fleet Request",
                    metadata={"type": "spot_fleet"},
                )
            )

        return managers

    def _find_consumers(
        self, instance_id: str, data: dict[str, Any]
    ) -> list[Dependency]:
        """Find resources that depend on this instance."""
        consumers = []

        # Check Target Group registrations
        if self.elbv2:
            try:
                tgs = self._find_target_groups_for_instance(instance_id)
                for tg in tgs:
                    consumers.append(
                        Dependency(
                            resource_type="aws_lb_target_group",
                            resource_id=tg["arn"],
                            resource_name=tg["name"],
                            relation_type=RelationType.CONSUMER,
                            severity=Severity.HIGH,
                            warning="Instance is registered in this Target Group",
                            metadata={"health_status": tg.get("health_status")},
                        )
                    )
            except Exception:
                pass

        # Note: Route53 records would need Route53 client
        # Note: ElastiCache client connections are application-level

        return consumers

    def _find_target_groups_for_instance(
        self, instance_id: str
    ) -> list[dict[str, Any]]:
        """Find all target groups this instance is registered to."""
        target_groups = []

        if not self.elbv2:
            return target_groups

        try:
            # List all target groups
            paginator = self.elbv2.get_paginator("describe_target_groups")
            for page in paginator.paginate():
                for tg in page["TargetGroups"]:
                    # Check if instance is registered
                    try:
                        health = self.elbv2.describe_target_health(
                            TargetGroupArn=tg["TargetGroupArn"]
                        )
                        for target in health.get("TargetHealthDescriptions", []):
                            if target.get("Target", {}).get("Id") == instance_id:
                                target_groups.append(
                                    {
                                        "arn": tg["TargetGroupArn"],
                                        "name": tg["TargetGroupName"],
                                        "health_status": target.get(
                                            "TargetHealth", {}
                                        ).get("State"),
                                    }
                                )
                    except Exception:
                        continue
        except Exception:
            pass

        return target_groups

    def _find_dependencies(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources this instance depends on."""
        dependencies = []

        # AMI
        ami_id = data.get("ImageId")
        if ami_id:
            dependencies.append(
                Dependency(
                    resource_type="aws_ami",
                    resource_id=ami_id,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                    metadata={"category": "source"},
                )
            )

        # EBS Volumes from block device mappings
        for bd in data.get("BlockDeviceMappings", []):
            ebs = bd.get("Ebs", {})
            volume_id = ebs.get("VolumeId")
            if volume_id:
                dependencies.append(
                    Dependency(
                        resource_type="aws_ebs_volume",
                        resource_id=volume_id,
                        resource_name=bd.get("DeviceName"),
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.HIGH,
                        metadata={
                            "category": "storage",
                            "device_name": bd.get("DeviceName"),
                            "delete_on_termination": ebs.get("DeleteOnTermination"),
                        },
                    )
                )

        # Key Pair
        key_name = data.get("KeyName")
        if key_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_key_pair",
                    resource_id=key_name,
                    resource_name=key_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                    metadata={"category": "access"},
                )
            )

        return dependencies

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network dependencies."""
        network = []

        # VPC
        vpc_id = data.get("VpcId")
        if vpc_id:
            network.append(
                Dependency(
                    resource_type="aws_vpc",
                    resource_id=vpc_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.INFO,
                )
            )

        # Subnet
        subnet_id = data.get("SubnetId")
        if subnet_id:
            network.append(
                Dependency(
                    resource_type="aws_subnet",
                    resource_id=subnet_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.INFO,
                )
            )

        # Security Groups from all network interfaces
        seen_sgs: set[str] = set()
        for eni in data.get("NetworkInterfaces", []):
            eni_id = eni.get("NetworkInterfaceId")
            if eni_id:
                network.append(
                    Dependency(
                        resource_type="aws_network_interface",
                        resource_id=eni_id,
                        relation_type=RelationType.NETWORK,
                        severity=Severity.MEDIUM,
                    )
                )

            for sg in eni.get("Groups", []):
                sg_id = sg.get("GroupId")
                if sg_id and sg_id not in seen_sgs:
                    seen_sgs.add(sg_id)
                    network.append(
                        Dependency(
                            resource_type="aws_security_group",
                            resource_id=sg_id,
                            resource_name=sg.get("GroupName"),
                            relation_type=RelationType.NETWORK,
                            severity=Severity.MEDIUM,
                        )
                    )

        # Also check top-level security groups
        for sg in data.get("SecurityGroups", []):
            sg_id = sg.get("GroupId")
            if sg_id and sg_id not in seen_sgs:
                seen_sgs.add(sg_id)
                network.append(
                    Dependency(
                        resource_type="aws_security_group",
                        resource_id=sg_id,
                        resource_name=sg.get("GroupName"),
                        relation_type=RelationType.NETWORK,
                        severity=Severity.MEDIUM,
                    )
                )

        # Elastic IP (if any)
        public_ip = data.get("PublicIpAddress")
        if public_ip:
            # Check if it's an EIP (would need additional API call)
            # For now, just note the association
            network.append(
                Dependency(
                    resource_type="aws_eip",
                    resource_id=public_ip,
                    resource_name=f"Public IP: {public_ip}",
                    relation_type=RelationType.NETWORK,
                    severity=Severity.MEDIUM,
                )
            )

        return network

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # IAM Instance Profile → Role
        iam_profile = data.get("IamInstanceProfile", {})
        profile_arn = iam_profile.get("Arn")
        if profile_arn:
            profile_name = (
                profile_arn.split("/")[-1] if "/" in profile_arn else profile_arn
            )

            # Get the role from the profile
            role_dep = Dependency(
                resource_type="aws_iam_instance_profile",
                resource_id=profile_arn,
                resource_name=profile_name,
                relation_type=RelationType.IDENTITY,
                severity=Severity.HIGH,
            )

            # Try to get the role name
            if self.iam:
                try:
                    profile_data = self.iam.get_instance_profile(
                        InstanceProfileName=profile_name
                    )
                    roles = profile_data.get("InstanceProfile", {}).get("Roles", [])
                    if roles:
                        role_name = roles[0].get("RoleName")
                        role_dep.children.append(
                            Dependency(
                                resource_type="aws_iam_role",
                                resource_id=roles[0].get("Arn", role_name),
                                resource_name=role_name,
                                relation_type=RelationType.IDENTITY,
                                severity=Severity.HIGH,
                            )
                        )
                except Exception:
                    pass

            identity.append(role_dep)

        # KMS Keys for EBS encryption - need to query volumes for KmsKeyId
        volume_ids = []
        for bd in data.get("BlockDeviceMappings", []):
            ebs = bd.get("Ebs", {})
            vol_id = ebs.get("VolumeId")
            if vol_id:
                volume_ids.append(vol_id)

        # Query volume details to get KMS key info
        if volume_ids and self.ec2:
            try:
                volumes_response = self.ec2.describe_volumes(VolumeIds=volume_ids)
                seen_kms_keys: set[str] = set()
                for vol in volumes_response.get("Volumes", []):
                    kms_key_id = vol.get("KmsKeyId")
                    if kms_key_id and kms_key_id not in seen_kms_keys:
                        seen_kms_keys.add(kms_key_id)
                        identity.append(
                            Dependency(
                                resource_type="aws_kms_key",
                                resource_id=kms_key_id,
                                relation_type=RelationType.IDENTITY,
                                severity=Severity.HIGH,
                                warning="EBS encryption key - do not delete!",
                                metadata={"volume_id": vol.get("VolumeId")},
                            )
                        )
            except Exception:
                pass

        return identity
