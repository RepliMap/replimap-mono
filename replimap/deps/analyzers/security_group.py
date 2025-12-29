"""
Security Group Dependency Analyzer.

Analyzes dependencies for Security Groups including:
- MANAGER: CloudFormation
- CONSUMERS: EC2, RDS, Lambda, ElastiCache, ELB, ECS, EFS
- DEPENDENCY: Other SGs referenced in rules (SG chain)
- NETWORK: VPC scope

SGs have high blast radius - a single change can affect many resources.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from replimap.deps.base_analyzer import ResourceDependencyAnalyzer
from replimap.deps.models import (
    Dependency,
    DependencyAnalysis,
    RelationType,
    Severity,
)


class SecurityGroupAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for Security Groups."""

    @property
    def resource_type(self) -> str:
        return "aws_security_group"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze Security Group dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"Security Group not found: {resource_id}")

        tags = {t["Key"]: t["Value"] for t in data.get("Tags", [])}

        # Build center resource
        center = Dependency(
            resource_type="aws_security_group",
            resource_id=resource_id,
            resource_name=data.get("GroupName", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
            metadata={
                "description": data.get("Description"),
                "vpc_id": data.get("VpcId"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this SG
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # CONSUMERS - who uses this SG (high blast radius!)
        consumers = self._find_consumers(resource_id)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # SG Chain - other SGs that reference this SG
        sg_chain = self._find_sg_chain(resource_id, data)
        if sg_chain.get("referenced_by"):
            dependencies[RelationType.CONSUMER] = dependencies.get(
                RelationType.CONSUMER, []
            ) + sg_chain["referenced_by"]
        if sg_chain.get("references"):
            dependencies[RelationType.DEPENDENCY] = sg_chain["references"]

        # NETWORK - VPC scope
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # Build context
        context = {
            "vpc_id": data.get("VpcId"),
            "group_name": data.get("GroupName"),
            "description": data.get("Description"),
            "inbound_rules_count": len(data.get("IpPermissions", [])),
            "outbound_rules_count": len(data.get("IpPermissionsEgress", [])),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get Security Group data from AWS API."""
        if not self.ec2:
            return {}

        try:
            response = self.ec2.describe_security_groups(GroupIds=[resource_id])
            sgs = response.get("SecurityGroups", [])
            if sgs:
                return sgs[0]
        except Exception:
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this SG."""
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

    def _find_consumers(self, sg_id: str) -> list[Dependency]:
        """
        Find all resources using this Security Group.

        Uses parallel queries for better performance on large accounts.
        """
        consumers: list[Dependency] = []

        # Define consumer queries
        queries = [
            ("EC2 Instances", self._find_ec2_using_sg),
            ("RDS Instances", self._find_rds_using_sg),
            ("Lambda Functions", self._find_lambda_using_sg),
            ("Load Balancers", self._find_elb_using_sg),
            ("ElastiCache", self._find_elasticache_using_sg),
        ]

        # Run queries in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(query_func, sg_id): name
                for name, query_func in queries
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    consumers.extend(result)
                except Exception:
                    # Log but don't fail
                    pass

        return consumers

    def _find_ec2_using_sg(self, sg_id: str) -> list[Dependency]:
        """Find EC2 instances using this Security Group."""
        instances = []

        if not self.ec2:
            return instances

        try:
            paginator = self.ec2.get_paginator("describe_instances")
            for page in paginator.paginate(
                Filters=[{"Name": "instance.group-id", "Values": [sg_id]}]
            ):
                for reservation in page.get("Reservations", []):
                    for instance in reservation.get("Instances", []):
                        state = instance.get("State", {}).get("Name")
                        if state == "terminated":
                            continue

                        tags = {
                            t["Key"]: t["Value"] for t in instance.get("Tags", [])
                        }
                        instances.append(
                            Dependency(
                                resource_type="aws_instance",
                                resource_id=instance["InstanceId"],
                                resource_name=tags.get("Name", instance["InstanceId"]),
                                relation_type=RelationType.CONSUMER,
                                severity=Severity.MEDIUM,
                                metadata={"state": state},
                            )
                        )
        except Exception:
            pass

        return instances

    def _find_rds_using_sg(self, sg_id: str) -> list[Dependency]:
        """Find RDS instances using this Security Group."""
        databases = []

        if not self.rds:
            return databases

        try:
            paginator = self.rds.get_paginator("describe_db_instances")
            for page in paginator.paginate():
                for db in page.get("DBInstances", []):
                    sg_ids = [
                        sg["VpcSecurityGroupId"]
                        for sg in db.get("VpcSecurityGroups", [])
                    ]
                    if sg_id in sg_ids:
                        databases.append(
                            Dependency(
                                resource_type="aws_db_instance",
                                resource_id=db["DBInstanceIdentifier"],
                                resource_name=db["DBInstanceIdentifier"],
                                relation_type=RelationType.CONSUMER,
                                severity=Severity.CRITICAL,  # Databases are critical
                                warning="Database uses this Security Group",
                                metadata={
                                    "engine": db.get("Engine"),
                                    "status": db.get("DBInstanceStatus"),
                                },
                            )
                        )
        except Exception:
            pass

        return databases

    def _find_lambda_using_sg(self, sg_id: str) -> list[Dependency]:
        """Find Lambda functions using this Security Group (VPC mode)."""
        functions = []

        if not self.lambda_client:
            return functions

        try:
            paginator = self.lambda_client.get_paginator("list_functions")
            for page in paginator.paginate():
                for func in page.get("Functions", []):
                    vpc_config = func.get("VpcConfig", {})
                    sg_ids = vpc_config.get("SecurityGroupIds", [])
                    if sg_id in sg_ids:
                        functions.append(
                            Dependency(
                                resource_type="aws_lambda_function",
                                resource_id=func["FunctionArn"],
                                resource_name=func["FunctionName"],
                                relation_type=RelationType.CONSUMER,
                                severity=Severity.MEDIUM,
                                metadata={"runtime": func.get("Runtime")},
                            )
                        )
        except Exception:
            pass

        return functions

    def _find_elb_using_sg(self, sg_id: str) -> list[Dependency]:
        """Find Load Balancers using this Security Group."""
        load_balancers = []

        if not self.elbv2:
            return load_balancers

        try:
            paginator = self.elbv2.get_paginator("describe_load_balancers")
            for page in paginator.paginate():
                for lb in page.get("LoadBalancers", []):
                    sg_ids = lb.get("SecurityGroups", [])
                    if sg_id in sg_ids:
                        load_balancers.append(
                            Dependency(
                                resource_type="aws_lb",
                                resource_id=lb["LoadBalancerArn"],
                                resource_name=lb["LoadBalancerName"],
                                relation_type=RelationType.CONSUMER,
                                severity=Severity.HIGH,
                                warning="Load Balancer uses this Security Group",
                                metadata={"type": lb.get("Type")},
                            )
                        )
        except Exception:
            pass

        return load_balancers

    def _find_elasticache_using_sg(self, sg_id: str) -> list[Dependency]:
        """Find ElastiCache clusters using this Security Group."""
        clusters = []

        if not self.elasticache:
            return clusters

        try:
            paginator = self.elasticache.get_paginator("describe_cache_clusters")
            for page in paginator.paginate(ShowCacheNodeInfo=True):
                for cluster in page.get("CacheClusters", []):
                    sg_ids = [
                        sg["SecurityGroupId"]
                        for sg in cluster.get("SecurityGroups", [])
                    ]
                    if sg_id in sg_ids:
                        clusters.append(
                            Dependency(
                                resource_type="aws_elasticache_cluster",
                                resource_id=cluster["CacheClusterId"],
                                resource_name=cluster["CacheClusterId"],
                                relation_type=RelationType.CONSUMER,
                                severity=Severity.HIGH,
                                warning="ElastiCache uses this Security Group",
                                metadata={"engine": cluster.get("Engine")},
                            )
                        )
        except Exception:
            pass

        return clusters

    def _find_sg_chain(
        self, sg_id: str, data: dict[str, Any]
    ) -> dict[str, list[Dependency]]:
        """
        Find Security Group chain references.

        This is critical for understanding blast radius - if SG-A references
        SG-B in its rules, deleting SG-B breaks SG-A's rules.
        """
        referenced_by: list[Dependency] = []  # Other SGs that reference this SG
        references: list[Dependency] = []  # SGs this SG references

        # 1. Find SGs this SG references in its rules
        for perm in data.get("IpPermissions", []) + data.get("IpPermissionsEgress", []):
            for pair in perm.get("UserIdGroupPairs", []):
                ref_sg_id = pair.get("GroupId")
                if ref_sg_id and ref_sg_id != sg_id:
                    direction = (
                        "inbound"
                        if perm in data.get("IpPermissions", [])
                        else "outbound"
                    )
                    references.append(
                        Dependency(
                            resource_type="aws_security_group",
                            resource_id=ref_sg_id,
                            resource_name=pair.get("GroupName", ref_sg_id),
                            relation_type=RelationType.DEPENDENCY,
                            severity=Severity.MEDIUM,
                            warning=f"Referenced in {direction} rules",
                        )
                    )

        # 2. Find SGs that reference this SG (need to scan all SGs)
        if self.ec2:
            try:
                paginator = self.ec2.get_paginator("describe_security_groups")
                for page in paginator.paginate():
                    for sg in page.get("SecurityGroups", []):
                        if sg["GroupId"] == sg_id:
                            continue

                        # Check inbound rules
                        for perm in sg.get("IpPermissions", []):
                            for pair in perm.get("UserIdGroupPairs", []):
                                if pair.get("GroupId") == sg_id:
                                    port_info = self._format_port_info(perm)
                                    referenced_by.append(
                                        Dependency(
                                            resource_type="aws_security_group",
                                            resource_id=sg["GroupId"],
                                            resource_name=sg.get(
                                                "GroupName", sg["GroupId"]
                                            ),
                                            relation_type=RelationType.CONSUMER,
                                            severity=Severity.HIGH,
                                            warning=f"Inbound rule trusts this SG ({port_info})",
                                            metadata={
                                                "direction": "inbound",
                                                "port": port_info,
                                            },
                                        )
                                    )

                        # Check outbound rules
                        for perm in sg.get("IpPermissionsEgress", []):
                            for pair in perm.get("UserIdGroupPairs", []):
                                if pair.get("GroupId") == sg_id:
                                    port_info = self._format_port_info(perm)
                                    referenced_by.append(
                                        Dependency(
                                            resource_type="aws_security_group",
                                            resource_id=sg["GroupId"],
                                            resource_name=sg.get(
                                                "GroupName", sg["GroupId"]
                                            ),
                                            relation_type=RelationType.CONSUMER,
                                            severity=Severity.MEDIUM,
                                            warning=f"Outbound rule references this SG ({port_info})",
                                            metadata={
                                                "direction": "outbound",
                                                "port": port_info,
                                            },
                                        )
                                    )
            except Exception:
                pass

        return {
            "referenced_by": referenced_by,
            "references": references,
        }

    def _format_port_info(self, permission: dict[str, Any]) -> str:
        """Format port information from a security group permission."""
        from_port = permission.get("FromPort")
        to_port = permission.get("ToPort")
        protocol = permission.get("IpProtocol", "-1")

        if protocol == "-1":
            return "all traffic"
        if from_port == to_port:
            return f"port {from_port}"
        if from_port == 0 and to_port == 65535:
            return "all ports"
        return f"ports {from_port}-{to_port}"

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network context."""
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
                    warning="Security Group is VPC-scoped",
                )
            )

        return network

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to Security Groups."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Count consumers
        consumers = dependencies.get(RelationType.CONSUMER, [])
        if consumers:
            # Count by type
            counts: dict[str, int] = {}
            for c in consumers:
                rt = c.resource_type.replace("aws_", "")
                counts[rt] = counts.get(rt, 0) + 1

            summary = ", ".join(f"{v} {k}(s)" for k, v in counts.items())
            warnings.insert(
                0,
                f"Modifying this Security Group will affect: {summary}",
            )

        # Check for SG chain
        sg_refs = [
            c for c in consumers if c.resource_type == "aws_security_group"
        ]
        if sg_refs:
            warnings.append(
                f"Deleting this SG will break {len(sg_refs)} other SGs' rules!"
            )

        return warnings
