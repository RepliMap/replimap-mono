"""
Elastic Load Balancer Dependency Analyzer.

Analyzes dependencies for ALB/NLB including:
- MANAGER: CloudFormation
- CONSUMERS: DNS records, CloudFront distributions
- DEPENDENCIES: Target Groups
- NETWORK: VPC, Subnets, Security Groups (ALB only)
- IDENTITY: SSL Certificates (ACM), WAF

Load balancers are traffic entry points - changes affect all downstream services.
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


class ELBAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for Application and Network Load Balancers."""

    @property
    def resource_type(self) -> str:
        return "aws_lb"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze Load Balancer dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"Load Balancer not found: {resource_id}")

        tags = data.get("tags", {})
        lb_type = data.get("Type", "application")

        # Build center resource
        center = Dependency(
            resource_type="aws_lb",
            resource_id=resource_id,
            resource_name=data.get("LoadBalancerName", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.CRITICAL,
            metadata={
                "type": lb_type,
                "scheme": data.get("Scheme"),
                "dns_name": data.get("DNSName"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this LB
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # CONSUMERS - Target Groups that receive traffic
        consumers = self._find_consumers(resource_id, data)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # NETWORK - VPC, Subnets, Security Groups
        network = self._find_network(data, lb_type)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - SSL certs, WAF
        identity = self._find_identity(resource_id, data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "load_balancer_name": data.get("LoadBalancerName"),
            "type": lb_type,
            "scheme": data.get("Scheme"),
            "dns_name": data.get("DNSName"),
            "state": data.get("State", {}).get("Code"),
            "availability_zones": [
                az.get("ZoneName") for az in data.get("AvailabilityZones", [])
            ],
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get Load Balancer data from AWS API."""
        if not self.elbv2:
            return {}

        try:
            # Try by ARN first
            if resource_id.startswith("arn:"):
                response = self.elbv2.describe_load_balancers(
                    LoadBalancerArns=[resource_id]
                )
            else:
                response = self.elbv2.describe_load_balancers(Names=[resource_id])

            lbs = response.get("LoadBalancers", [])
            if lbs:
                data = lbs[0]
                # Get tags
                try:
                    tags_response = self.elbv2.describe_tags(
                        ResourceArns=[data["LoadBalancerArn"]]
                    )
                    tag_list = tags_response.get("TagDescriptions", [{}])[0].get(
                        "Tags", []
                    )
                    data["tags"] = {t["Key"]: t["Value"] for t in tag_list}
                except Exception:  # noqa: S110
                    data["tags"] = {}
                return data
        except Exception:  # noqa: S110
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this LB."""
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

    def _find_consumers(self, lb_arn: str, data: dict[str, Any]) -> list[Dependency]:
        """Find resources that receive traffic from this LB."""
        consumers = []

        if not self.elbv2:
            return consumers

        try:
            # Get listeners
            listeners = self.elbv2.describe_listeners(LoadBalancerArn=lb_arn)

            for listener in listeners.get("Listeners", []):
                # Find target groups from default actions
                for action in listener.get("DefaultActions", []):
                    tg_arn = action.get("TargetGroupArn")
                    if tg_arn:
                        consumers.append(
                            self._create_target_group_dep(tg_arn, listener)
                        )

                    # Handle forward action with multiple target groups
                    forward_config = action.get("ForwardConfig", {})
                    for tg in forward_config.get("TargetGroups", []):
                        tg_arn = tg.get("TargetGroupArn")
                        if tg_arn:
                            consumers.append(
                                self._create_target_group_dep(tg_arn, listener)
                            )
        except Exception:  # noqa: S110
            pass

        return consumers

    def _create_target_group_dep(
        self, tg_arn: str, listener: dict[str, Any]
    ) -> Dependency:
        """Create a target group dependency."""
        tg_name = tg_arn.split("/")[-2] if "/" in tg_arn else tg_arn
        port = listener.get("Port", "")
        protocol = listener.get("Protocol", "")

        return Dependency(
            resource_type="aws_lb_target_group",
            resource_id=tg_arn,
            resource_name=tg_name,
            relation_type=RelationType.CONSUMER,
            severity=Severity.HIGH,
            warning=f"Receives traffic on {protocol}:{port}",
            metadata={
                "listener_port": port,
                "listener_protocol": protocol,
            },
        )

    def _find_network(self, data: dict[str, Any], lb_type: str) -> list[Dependency]:
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

        # Subnets from AZs
        for az in data.get("AvailabilityZones", []):
            subnet_id = az.get("SubnetId")
            if subnet_id:
                network.append(
                    Dependency(
                        resource_type="aws_subnet",
                        resource_id=subnet_id,
                        relation_type=RelationType.NETWORK,
                        severity=Severity.MEDIUM,
                        metadata={"zone": az.get("ZoneName")},
                    )
                )

        # Security Groups (ALB only)
        if lb_type == "application":
            for sg_id in data.get("SecurityGroups", []):
                network.append(
                    Dependency(
                        resource_type="aws_security_group",
                        resource_id=sg_id,
                        relation_type=RelationType.NETWORK,
                        severity=Severity.MEDIUM,
                    )
                )

        return network

    def _find_identity(self, lb_arn: str, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        if not self.elbv2:
            return identity

        try:
            # Get listeners to find SSL certificates
            listeners = self.elbv2.describe_listeners(LoadBalancerArn=lb_arn)

            for listener in listeners.get("Listeners", []):
                for cert in listener.get("Certificates", []):
                    cert_arn = cert.get("CertificateArn")
                    if cert_arn:
                        identity.append(
                            Dependency(
                                resource_type="aws_acm_certificate",
                                resource_id=cert_arn,
                                relation_type=RelationType.IDENTITY,
                                severity=Severity.HIGH,
                                warning="SSL certificate - expiry affects service",
                                metadata={"listener_port": listener.get("Port")},
                            )
                        )
        except Exception:  # noqa: S110
            pass

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to Load Balancers."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Count target groups
        consumers = dependencies.get(RelationType.CONSUMER, [])
        tgs = [c for c in consumers if c.resource_type == "aws_lb_target_group"]
        if tgs:
            warnings.insert(
                0,
                f"Load Balancer routes to {len(tgs)} Target Group(s) - "
                "changes affect all downstream services",
            )

        # SSL certificate warning
        identity = dependencies.get(RelationType.IDENTITY, [])
        certs = [i for i in identity if i.resource_type == "aws_acm_certificate"]
        if certs:
            warnings.append(
                f"Uses {len(certs)} SSL certificate(s) - monitor for expiry"
            )

        # Internet-facing warning
        if center.metadata.get("scheme") == "internet-facing":
            warnings.insert(0, "Internet-facing LB - public traffic entry point")

        return warnings
