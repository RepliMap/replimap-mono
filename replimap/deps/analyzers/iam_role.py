"""
IAM Role Dependency Analyzer.

Analyzes dependencies for IAM Roles including:
- MANAGER: CloudFormation
- CONSUMERS: EC2 (via Instance Profile), Lambda, ECS, other roles
- TRUST: Who can assume this role (services, accounts, federated)
- DEPENDENCY: Attached policies

IAM Roles have high blast radius - many resources may depend on them.
"""

from __future__ import annotations

import json
from concurrent.futures import as_completed
from typing import Any

from replimap.core.concurrency import create_thread_pool
from replimap.deps.base_analyzer import ResourceDependencyAnalyzer
from replimap.deps.models import (
    Dependency,
    DependencyAnalysis,
    RelationType,
    Severity,
)


class IAMRoleAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for IAM Roles."""

    @property
    def resource_type(self) -> str:
        return "aws_iam_role"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze IAM Role dependencies."""
        # resource_id could be role name or ARN
        role_name = resource_id
        if resource_id.startswith("arn:"):
            role_name = resource_id.split("/")[-1]

        data = self.get_api_data(role_name)

        if not data:
            raise ValueError(f"IAM Role not found: {role_name}")

        tags = {t["Key"]: t["Value"] for t in data.get("Tags", [])}

        # Build center resource
        center = Dependency(
            resource_type="aws_iam_role",
            resource_id=data.get("Arn", role_name),
            resource_name=data.get("RoleName", role_name),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
            metadata={
                "path": data.get("Path"),
                "create_date": str(data.get("CreateDate", "")),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this role
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # TRUST - who can assume this role
        trust = self._analyze_trust_policy(data)
        if trust:
            dependencies[RelationType.TRUST] = trust

        # CONSUMERS - who uses this role
        consumers = self._find_consumers(role_name)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # DEPENDENCIES - attached policies
        deps = self._find_attached_policies(role_name)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # Build context
        context = {
            "role_name": data.get("RoleName"),
            "role_arn": data.get("Arn"),
            "path": data.get("Path"),
            "max_session_duration": data.get("MaxSessionDuration"),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, role_name: str) -> dict[str, Any]:
        """Get IAM Role data from AWS API."""
        if not self.iam:
            return {}

        try:
            response = self.iam.get_role(RoleName=role_name)
            return response.get("Role", {})
        except Exception:  # noqa: S110
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this role."""
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

    def _analyze_trust_policy(self, data: dict[str, Any]) -> list[Dependency]:
        """
        Analyze the Trust Policy to find who can assume this role.

        Detects:
        - AWS Services (ec2, lambda, etc.)
        - Same-account principals
        - Cross-account principals (CRITICAL)
        - Federated principals (SAML, OIDC)
        """
        trust = []

        trust_policy = data.get("AssumeRolePolicyDocument", {})

        # Handle string or dict
        if isinstance(trust_policy, str):
            try:
                trust_policy = json.loads(trust_policy)
            except json.JSONDecodeError:
                return trust

        current_account = self.get_current_account_id()

        for statement in trust_policy.get("Statement", []):
            if statement.get("Effect") != "Allow":
                continue

            principal = statement.get("Principal", {})

            # AWS Services
            if "Service" in principal:
                services = principal["Service"]
                if isinstance(services, str):
                    services = [services]
                for svc in services:
                    svc_name = svc.split(".")[0]  # ec2, lambda, etc.
                    trust.append(
                        Dependency(
                            resource_type="aws_service",
                            resource_id=svc,
                            resource_name=svc_name,
                            relation_type=RelationType.TRUST,
                            severity=Severity.INFO,
                            metadata={"type": "service"},
                        )
                    )

            # AWS Account/Principal
            if "AWS" in principal:
                arns = principal["AWS"]
                if isinstance(arns, str):
                    arns = [arns]

                for arn in arns:
                    # Handle "*" (any principal)
                    if arn == "*":
                        trust.append(
                            Dependency(
                                resource_type="aws_any_principal",
                                resource_id="*",
                                resource_name="ANY AWS Principal",
                                relation_type=RelationType.TRUST,
                                severity=Severity.CRITICAL,
                                warning=(
                                    "DANGER: This role can be assumed by ANY AWS principal! "
                                    "Check conditions in the trust policy."
                                ),
                                metadata={"type": "any"},
                            )
                        )
                        continue

                    # Extract account ID
                    is_cross_account = False
                    account_id = None

                    if ":root" in arn or ":user/" in arn or ":role/" in arn:
                        try:
                            account_id = arn.split(":")[4]
                            is_cross_account = account_id != current_account
                        except IndexError:
                            pass

                    principal_name = arn.split("/")[-1] if "/" in arn else arn

                    if is_cross_account:
                        trust.append(
                            Dependency(
                                resource_type="aws_account",
                                resource_id=arn,
                                resource_name=f"Account {account_id}",
                                relation_type=RelationType.TRUST,
                                severity=Severity.CRITICAL,
                                warning=(
                                    f"CROSS-ACCOUNT ACCESS: External account {account_id} "
                                    "can assume this role. Changes may affect external integrations!"
                                ),
                                metadata={
                                    "type": "cross_account",
                                    "account_id": account_id,
                                },
                            )
                        )
                    else:
                        trust.append(
                            Dependency(
                                resource_type="aws_iam_principal",
                                resource_id=arn,
                                resource_name=principal_name,
                                relation_type=RelationType.TRUST,
                                severity=Severity.MEDIUM,
                                metadata={"type": "same_account"},
                            )
                        )

            # Federated (SAML, OIDC)
            if "Federated" in principal:
                federated = principal["Federated"]
                if isinstance(federated, str):
                    federated = [federated]

                for provider in federated:
                    provider_type = "SAML" if "saml" in provider.lower() else "OIDC"
                    trust.append(
                        Dependency(
                            resource_type="aws_federation",
                            resource_id=provider,
                            resource_name=f"{provider_type} Provider",
                            relation_type=RelationType.TRUST,
                            severity=Severity.HIGH,
                            warning="External identity provider can assume this role",
                            metadata={"type": provider_type.lower()},
                        )
                    )

        return trust

    def _find_consumers(self, role_name: str) -> list[Dependency]:
        """Find resources that use this role."""
        consumers: list[Dependency] = []

        # Run queries in parallel
        queries = [
            ("Instance Profiles", self._find_ec2_via_instance_profile),
            ("Lambda Functions", self._find_lambda_using_role),
        ]

        # Use tracked thread pool - global signal handler will shutdown on Ctrl-C
        executor = create_thread_pool(max_workers=3, thread_name_prefix="iam-role-")
        try:
            futures = {
                executor.submit(query_func, role_name): name
                for name, query_func in queries
            }

            for future in as_completed(futures):
                try:
                    result = future.result()
                    consumers.extend(result)
                except Exception:  # noqa: S110
                    pass
        finally:
            executor.shutdown(wait=True)

        return consumers

    def _find_ec2_via_instance_profile(self, role_name: str) -> list[Dependency]:
        """Find EC2 instances using this role via Instance Profiles."""
        consumers = []

        if not self.iam or not self.ec2:
            return consumers

        try:
            # Find instance profiles for this role
            profiles = self.iam.list_instance_profiles_for_role(RoleName=role_name)
            profile_names = [
                p["InstanceProfileName"] for p in profiles.get("InstanceProfiles", [])
            ]

            if not profile_names:
                return consumers

            # Find EC2 instances using these profiles
            for profile_name in profile_names:
                paginator = self.ec2.get_paginator("describe_instances")
                for page in paginator.paginate(
                    Filters=[
                        {
                            "Name": "iam-instance-profile.arn",
                            "Values": [f"*/{profile_name}"],
                        }
                    ]
                ):
                    for reservation in page.get("Reservations", []):
                        for instance in reservation.get("Instances", []):
                            state = instance.get("State", {}).get("Name")
                            if state == "terminated":
                                continue

                            tags = {
                                t["Key"]: t["Value"] for t in instance.get("Tags", [])
                            }
                            consumers.append(
                                Dependency(
                                    resource_type="aws_instance",
                                    resource_id=instance["InstanceId"],
                                    resource_name=tags.get(
                                        "Name", instance["InstanceId"]
                                    ),
                                    relation_type=RelationType.CONSUMER,
                                    severity=Severity.HIGH,
                                    warning="Instance uses this role via Instance Profile",
                                    metadata={
                                        "profile": profile_name,
                                        "state": state,
                                    },
                                )
                            )
        except Exception:  # noqa: S110
            pass

        return consumers

    def _find_lambda_using_role(self, role_name: str) -> list[Dependency]:
        """Find Lambda functions using this role."""
        functions = []

        if not self.lambda_client or not self.iam:
            return functions

        try:
            # Get role ARN
            role = self.iam.get_role(RoleName=role_name)
            role_arn = role["Role"]["Arn"]

            # Find Lambda functions using this role
            paginator = self.lambda_client.get_paginator("list_functions")
            for page in paginator.paginate():
                for func in page.get("Functions", []):
                    if func.get("Role") == role_arn:
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
        except Exception:  # noqa: S110
            pass

        return functions

    def _find_attached_policies(self, role_name: str) -> list[Dependency]:
        """Find policies attached to this role."""
        policies = []

        if not self.iam:
            return policies

        try:
            # Managed policies (AWS and customer managed)
            paginator = self.iam.get_paginator("list_attached_role_policies")
            for page in paginator.paginate(RoleName=role_name):
                for policy in page.get("AttachedPolicies", []):
                    is_aws_managed = policy["PolicyArn"].startswith("arn:aws:iam::aws:")
                    policies.append(
                        Dependency(
                            resource_type="aws_iam_policy",
                            resource_id=policy["PolicyArn"],
                            resource_name=policy["PolicyName"],
                            relation_type=RelationType.DEPENDENCY,
                            severity=Severity.MEDIUM,
                            metadata={
                                "type": "aws_managed"
                                if is_aws_managed
                                else "customer_managed"
                            },
                        )
                    )

            # Inline policies
            inline_paginator = self.iam.get_paginator("list_role_policies")
            for page in inline_paginator.paginate(RoleName=role_name):
                for policy_name in page.get("PolicyNames", []):
                    policies.append(
                        Dependency(
                            resource_type="aws_iam_role_policy",
                            resource_id=f"{role_name}/{policy_name}",
                            resource_name=policy_name,
                            relation_type=RelationType.DEPENDENCY,
                            severity=Severity.MEDIUM,
                            warning="Inline policy - consider externalizing",
                            metadata={"type": "inline"},
                        )
                    )
        except Exception:  # noqa: S110
            pass

        return policies

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to IAM Roles."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Count consumers
        consumers = dependencies.get(RelationType.CONSUMER, [])
        if consumers:
            counts: dict[str, int] = {}
            for c in consumers:
                rt = c.resource_type.replace("aws_", "")
                counts[rt] = counts.get(rt, 0) + 1

            summary = ", ".join(f"{v} {k}(s)" for k, v in counts.items())
            warnings.insert(
                0,
                f"This role is used by: {summary}. Test changes carefully!",
            )

        # Cross-account warnings
        trust = dependencies.get(RelationType.TRUST, [])
        cross_account = [t for t in trust if t.metadata.get("type") == "cross_account"]
        if cross_account:
            accounts = [t.metadata.get("account_id") for t in cross_account]
            warnings.append(
                f"Role can be assumed by external accounts: {', '.join(accounts)}"
            )

        return warnings
