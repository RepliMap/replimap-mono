"""
Auto Scaling Group Dependency Analyzer.

Analyzes dependencies for Auto Scaling Groups including:
- MANAGED: EC2 instances controlled by this ASG
- CONSUMERS: Target Groups receiving traffic
- DEPENDENCIES: Launch Template/Config, AMI
- NETWORK: VPC, Subnets, Security Groups
- IDENTITY: IAM Service-linked Role

ASGs are lifecycle managers - they control EC2 instance creation/termination.
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


class ASGAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for Auto Scaling Groups."""

    @property
    def resource_type(self) -> str:
        return "aws_autoscaling_group"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze Auto Scaling Group dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"Auto Scaling Group not found: {resource_id}")

        tags = {t["Key"]: t["Value"] for t in data.get("Tags", [])}

        # Build center resource
        center = Dependency(
            resource_type="aws_autoscaling_group",
            resource_id=resource_id,
            resource_name=data.get("AutoScalingGroupName", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.CRITICAL,
            metadata={
                "min_size": data.get("MinSize"),
                "max_size": data.get("MaxSize"),
                "desired_capacity": data.get("DesiredCapacity"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this ASG
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # MANAGED - EC2 instances this ASG controls (critical for blast radius)
        managed = self._find_managed_instances(data)
        if managed:
            dependencies[RelationType.MANAGED] = managed

        # CONSUMERS - Target Groups that receive traffic from ASG instances
        consumers = self._find_consumers(data)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # DEPENDENCIES - Launch Template/Config, AMI
        deps = self._find_dependencies(data)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # NETWORK - VPC, Subnets
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - Service-linked role
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "asg_name": data.get("AutoScalingGroupName"),
            "min_size": data.get("MinSize"),
            "max_size": data.get("MaxSize"),
            "desired_capacity": data.get("DesiredCapacity"),
            "health_check_type": data.get("HealthCheckType"),
            "health_check_grace_period": data.get("HealthCheckGracePeriod"),
            "status": data.get("Status"),
            "suspended_processes": [
                p.get("ProcessName") for p in data.get("SuspendedProcesses", [])
            ],
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get Auto Scaling Group data from AWS API."""
        if not self.autoscaling:
            return {}

        try:
            response = self.autoscaling.describe_auto_scaling_groups(
                AutoScalingGroupNames=[resource_id]
            )
            groups = response.get("AutoScalingGroups", [])
            if groups:
                return groups[0]
        except Exception:  # noqa: S110
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this ASG."""
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

    def _find_managed_instances(self, data: dict[str, Any]) -> list[Dependency]:
        """Find EC2 instances managed by this ASG."""
        managed = []

        for instance in data.get("Instances", []):
            instance_id = instance.get("InstanceId")
            if instance_id:
                lifecycle_state = instance.get("LifecycleState", "")
                health = instance.get("HealthStatus", "")

                severity = Severity.MEDIUM
                if lifecycle_state == "InService" and health == "Healthy":
                    severity = Severity.HIGH

                managed.append(
                    Dependency(
                        resource_type="aws_instance",
                        resource_id=instance_id,
                        relation_type=RelationType.MANAGED,
                        severity=severity,
                        metadata={
                            "lifecycle_state": lifecycle_state,
                            "health_status": health,
                            "availability_zone": instance.get("AvailabilityZone"),
                            "protected_from_scale_in": instance.get(
                                "ProtectedFromScaleIn", False
                            ),
                        },
                    )
                )

        return managed

    def _find_consumers(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources that consume this ASG (receive traffic)."""
        consumers = []

        # Target Groups
        for tg_arn in data.get("TargetGroupARNs", []):
            # Extract name from ARN
            tg_name = tg_arn.split("/")[-2] if "/" in tg_arn else tg_arn

            consumers.append(
                Dependency(
                    resource_type="aws_lb_target_group",
                    resource_id=tg_arn,
                    resource_name=tg_name,
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                    warning="Target Group receives traffic from ASG instances",
                )
            )

        # Classic Load Balancers
        for lb_name in data.get("LoadBalancerNames", []):
            consumers.append(
                Dependency(
                    resource_type="aws_elb",
                    resource_id=lb_name,
                    resource_name=lb_name,
                    relation_type=RelationType.CONSUMER,
                    severity=Severity.HIGH,
                    warning="Classic ELB receives traffic from ASG instances",
                )
            )

        return consumers

    def _find_dependencies(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources this ASG depends on."""
        dependencies = []

        # Launch Template
        lt = data.get("LaunchTemplate")
        if lt:
            lt_id = lt.get("LaunchTemplateId")
            lt_name = lt.get("LaunchTemplateName")
            version = lt.get("Version")

            if lt_id:
                dependencies.append(
                    Dependency(
                        resource_type="aws_launch_template",
                        resource_id=lt_id,
                        resource_name=lt_name,
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.CRITICAL,
                        warning="Launch Template defines instance configuration",
                        metadata={"version": version},
                    )
                )

        # Launch Configuration (legacy)
        lc_name = data.get("LaunchConfigurationName")
        if lc_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_launch_configuration",
                    resource_id=lc_name,
                    resource_name=lc_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.CRITICAL,
                    warning="Launch Configuration defines instance configuration (legacy)",
                )
            )

        # Mixed Instances Policy (has additional Launch Templates)
        mip = data.get("MixedInstancesPolicy", {})
        lt_spec = mip.get("LaunchTemplate", {})
        lt_override = lt_spec.get("LaunchTemplateSpecification", {})
        if lt_override.get("LaunchTemplateId"):
            override_id = lt_override["LaunchTemplateId"]
            override_name = lt_override.get("LaunchTemplateName")
            if override_id != (lt.get("LaunchTemplateId") if lt else None):
                dependencies.append(
                    Dependency(
                        resource_type="aws_launch_template",
                        resource_id=override_id,
                        resource_name=override_name,
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.HIGH,
                        metadata={"source": "mixed_instances_policy"},
                    )
                )

        # Placement Group
        pg_name = data.get("PlacementGroup")
        if pg_name:
            dependencies.append(
                Dependency(
                    resource_type="aws_placement_group",
                    resource_id=pg_name,
                    resource_name=pg_name,
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                )
            )

        return dependencies

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network dependencies."""
        network = []
        seen_vpcs: set[str] = set()

        # Get VPC from subnets
        subnet_ids = []
        if data.get("VPCZoneIdentifier"):
            subnet_ids = data["VPCZoneIdentifier"].split(",")

        for subnet_id in subnet_ids:
            subnet_id = subnet_id.strip()
            if not subnet_id:
                continue

            network.append(
                Dependency(
                    resource_type="aws_subnet",
                    resource_id=subnet_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.MEDIUM,
                )
            )

            # Try to get VPC from subnet
            if self.ec2 and subnet_id not in seen_vpcs:
                try:
                    response = self.ec2.describe_subnets(SubnetIds=[subnet_id])
                    subnets = response.get("Subnets", [])
                    if subnets:
                        vpc_id = subnets[0].get("VpcId")
                        if vpc_id and vpc_id not in seen_vpcs:
                            seen_vpcs.add(vpc_id)
                            network.insert(
                                0,
                                Dependency(
                                    resource_type="aws_vpc",
                                    resource_id=vpc_id,
                                    relation_type=RelationType.NETWORK,
                                    severity=Severity.INFO,
                                ),
                            )
                except Exception:  # noqa: S110
                    pass

        # Availability Zones (from instances)
        azs = set()
        for instance in data.get("Instances", []):
            az = instance.get("AvailabilityZone")
            if az:
                azs.add(az)

        return network

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # Service-linked role
        service_role = data.get("ServiceLinkedRoleARN")
        if service_role:
            role_name = (
                service_role.split("/")[-1] if "/" in service_role else service_role
            )
            identity.append(
                Dependency(
                    resource_type="aws_iam_service_linked_role",
                    resource_id=service_role,
                    resource_name=role_name,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.MEDIUM,
                    metadata={"type": "service_linked_role"},
                )
            )

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to ASGs."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Count managed instances
        managed = dependencies.get(RelationType.MANAGED, [])
        if managed:
            healthy = [
                m for m in managed if m.metadata.get("lifecycle_state") == "InService"
            ]
            warnings.insert(
                0,
                f"ASG manages {len(managed)} instance(s) ({len(healthy)} in service)",
            )

        # Check for suspended processes
        context = center.metadata
        min_size = context.get("min_size", 0)
        max_size = context.get("max_size", 0)
        desired = context.get("desired_capacity", 0)

        if min_size == max_size == desired and min_size > 0:
            warnings.append(
                f"Fixed capacity ASG (min=max=desired={min_size}) - "
                "no auto-scaling active"
            )

        # Target groups warning
        consumers = dependencies.get(RelationType.CONSUMER, [])
        tgs = [c for c in consumers if c.resource_type == "aws_lb_target_group"]
        if tgs:
            warnings.append(
                f"ASG instances registered to {len(tgs)} Target Group(s) - "
                "traffic will be affected by scaling events"
            )

        return warnings
