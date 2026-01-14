"""
Lambda Function Dependency Analyzer.

Analyzes dependencies for Lambda functions including:
- MANAGER: CloudFormation
- CONSUMERS: API Gateway, EventBridge rules, S3 triggers
- DEPENDENCIES: Layers, Container images
- NETWORK: VPC, Subnets, Security Groups (if VPC-attached)
- IDENTITY: Execution Role, KMS Key (for env encryption)
- TRIGGER: Event sources (SQS, Kinesis, DynamoDB)

Lambda functions often have complex dependency chains - understand before modifying.
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


class LambdaFunctionAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for Lambda Functions."""

    @property
    def resource_type(self) -> str:
        return "aws_lambda_function"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze Lambda function dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"Lambda function not found: {resource_id}")

        tags = data.get("Tags", {})

        # Build center resource
        center = Dependency(
            resource_type="aws_lambda_function",
            resource_id=data.get("FunctionArn", resource_id),
            resource_name=data.get("FunctionName", resource_id),
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
            metadata={
                "runtime": data.get("Runtime"),
                "memory": data.get("MemorySize"),
                "timeout": data.get("Timeout"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this function
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # TRIGGER - event sources that invoke this function
        triggers = self._find_triggers(resource_id, data)
        if triggers:
            dependencies[RelationType.TRIGGER] = triggers

        # DEPENDENCIES - layers, container images
        deps = self._find_dependencies(data)
        if deps:
            dependencies[RelationType.DEPENDENCY] = deps

        # NETWORK - VPC config (if any)
        network = self._find_network(data)
        if network:
            dependencies[RelationType.NETWORK] = network

        # IDENTITY - execution role, KMS key
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "function_name": data.get("FunctionName"),
            "function_arn": data.get("FunctionArn"),
            "runtime": data.get("Runtime"),
            "handler": data.get("Handler"),
            "memory_size": data.get("MemorySize"),
            "timeout": data.get("Timeout"),
            "last_modified": data.get("LastModified"),
            "code_size": data.get("CodeSize"),
            "state": data.get("State"),
            "architectures": data.get("Architectures", ["x86_64"]),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get Lambda function data from AWS API."""
        if not self.lambda_client:
            return {}

        try:
            # Get function configuration
            response = self.lambda_client.get_function(FunctionName=resource_id)
            data = response.get("Configuration", {})

            # Get tags
            data["Tags"] = response.get("Tags", {})

            return data
        except Exception:  # noqa: S110
            pass

        return {}

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this function."""
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

        # SAM (Serverless Application Model)
        sam_app = tags.get("aws:serverlessrepo:applicationId")
        if sam_app:
            managers.append(
                Dependency(
                    resource_type="aws_serverlessrepo_application",
                    resource_id=sam_app,
                    resource_name=sam_app,
                    relation_type=RelationType.MANAGER,
                    severity=Severity.HIGH,
                    warning="Managed by SAM application",
                )
            )

        return managers

    def _find_triggers(
        self, function_name: str, data: dict[str, Any]
    ) -> list[Dependency]:
        """Find event sources that trigger this function."""
        triggers = []

        if not self.lambda_client:
            return triggers

        try:
            # List event source mappings (SQS, Kinesis, DynamoDB)
            paginator = self.lambda_client.get_paginator("list_event_source_mappings")
            for page in paginator.paginate(FunctionName=function_name):
                for esm in page.get("EventSourceMappings", []):
                    source_arn = esm.get("EventSourceArn", "")
                    state = esm.get("State", "")

                    # Determine source type
                    if ":sqs:" in source_arn:
                        resource_type = "aws_sqs_queue"
                        name = source_arn.split(":")[-1]
                    elif ":kinesis:" in source_arn:
                        resource_type = "aws_kinesis_stream"
                        name = source_arn.split("/")[-1]
                    elif ":dynamodb:" in source_arn:
                        resource_type = "aws_dynamodb_table"
                        # Extract table name from stream ARN
                        name = (
                            source_arn.split("/")[1]
                            if "/" in source_arn
                            else source_arn
                        )
                    else:
                        resource_type = "aws_event_source"
                        name = source_arn

                    triggers.append(
                        Dependency(
                            resource_type=resource_type,
                            resource_id=source_arn,
                            resource_name=name,
                            relation_type=RelationType.TRIGGER,
                            severity=Severity.HIGH,
                            warning=f"Event source trigger (state: {state})",
                            metadata={
                                "state": state,
                                "batch_size": esm.get("BatchSize"),
                                "uuid": esm.get("UUID"),
                            },
                        )
                    )
        except Exception:  # noqa: S110
            pass

        return triggers

    def _find_dependencies(self, data: dict[str, Any]) -> list[Dependency]:
        """Find resources this function depends on."""
        dependencies = []

        # Lambda Layers
        for layer in data.get("Layers", []):
            layer_arn = layer.get("Arn", "")
            # Extract layer name and version from ARN
            # Format: arn:aws:lambda:region:account:layer:name:version
            parts = layer_arn.split(":")
            if len(parts) >= 8:
                layer_name = parts[6]
                layer_version = parts[7]
            else:
                layer_name = layer_arn
                layer_version = "unknown"

            dependencies.append(
                Dependency(
                    resource_type="aws_lambda_layer_version",
                    resource_id=layer_arn,
                    resource_name=f"{layer_name}:{layer_version}",
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.HIGH,
                    warning="Function depends on this layer",
                    metadata={
                        "code_size": layer.get("CodeSize"),
                    },
                )
            )

        # Container image (if using container packaging)
        package_type = data.get("PackageType")
        if package_type == "Image":
            image_uri = data.get("ImageUri") or data.get("Code", {}).get("ImageUri")
            if image_uri:
                dependencies.append(
                    Dependency(
                        resource_type="aws_ecr_repository",
                        resource_id=image_uri,
                        resource_name=image_uri.split("/")[-1].split(":")[0],
                        relation_type=RelationType.DEPENDENCY,
                        severity=Severity.HIGH,
                        warning="Function uses container image from ECR",
                        metadata={"image_uri": image_uri},
                    )
                )

        # Dead letter queue
        dlc = data.get("DeadLetterConfig", {})
        dlq_arn = dlc.get("TargetArn")
        if dlq_arn:
            if ":sqs:" in dlq_arn:
                resource_type = "aws_sqs_queue"
            elif ":sns:" in dlq_arn:
                resource_type = "aws_sns_topic"
            else:
                resource_type = "aws_resource"

            dependencies.append(
                Dependency(
                    resource_type=resource_type,
                    resource_id=dlq_arn,
                    resource_name=dlq_arn.split(":")[-1],
                    relation_type=RelationType.DEPENDENCY,
                    severity=Severity.MEDIUM,
                    warning="Dead letter queue for failed invocations",
                )
            )

        return dependencies

    def _find_network(self, data: dict[str, Any]) -> list[Dependency]:
        """Find network dependencies (VPC-attached functions only)."""
        network = []

        vpc_config = data.get("VpcConfig", {})
        vpc_id = vpc_config.get("VpcId")

        if not vpc_id:
            return network  # Not VPC-attached

        # VPC
        network.append(
            Dependency(
                resource_type="aws_vpc",
                resource_id=vpc_id,
                relation_type=RelationType.NETWORK,
                severity=Severity.INFO,
            )
        )

        # Subnets
        for subnet_id in vpc_config.get("SubnetIds", []):
            network.append(
                Dependency(
                    resource_type="aws_subnet",
                    resource_id=subnet_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.MEDIUM,
                )
            )

        # Security Groups
        for sg_id in vpc_config.get("SecurityGroupIds", []):
            network.append(
                Dependency(
                    resource_type="aws_security_group",
                    resource_id=sg_id,
                    relation_type=RelationType.NETWORK,
                    severity=Severity.MEDIUM,
                )
            )

        return network

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # Execution Role
        role_arn = data.get("Role")
        if role_arn:
            role_name = role_arn.split("/")[-1] if "/" in role_arn else role_arn
            identity.append(
                Dependency(
                    resource_type="aws_iam_role",
                    resource_id=role_arn,
                    resource_name=role_name,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.CRITICAL,
                    warning="Execution role - defines what this function can access",
                )
            )

        # KMS Key for environment variables
        kms_key = data.get("KMSKeyArn")
        if kms_key:
            identity.append(
                Dependency(
                    resource_type="aws_kms_key",
                    resource_id=kms_key,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.HIGH,
                    warning="Encrypts environment variables",
                )
            )

        # Signing config
        signing_config = data.get("SigningProfileVersionArn")
        if signing_config:
            identity.append(
                Dependency(
                    resource_type="aws_signer_signing_profile",
                    resource_id=signing_config,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.MEDIUM,
                    warning="Code signing profile",
                )
            )

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to Lambda functions."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Event source warnings
        triggers = dependencies.get(RelationType.TRIGGER, [])
        if triggers:
            trigger_types = {t.resource_type for t in triggers}
            warnings.insert(
                0,
                f"Function has {len(triggers)} event source(s): "
                f"{', '.join(t.replace('aws_', '') for t in trigger_types)}",
            )

        # Layer warnings
        deps = dependencies.get(RelationType.DEPENDENCY, [])
        layers = [d for d in deps if d.resource_type == "aws_lambda_layer_version"]
        if layers:
            warnings.append(
                f"Uses {len(layers)} layer(s) - layer updates may affect this function"
            )

        # VPC warning
        network = dependencies.get(RelationType.NETWORK, [])
        if network:
            warnings.append(
                "VPC-attached function - cold starts may be longer, "
                "ensure NAT Gateway for internet access"
            )

        return warnings
