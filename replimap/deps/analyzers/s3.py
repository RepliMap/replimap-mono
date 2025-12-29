"""
S3 Bucket Dependency Analyzer.

Analyzes dependencies for S3 buckets including:
- MANAGER: CloudFormation
- CONSUMERS: CloudFront distributions, Lambda functions
- DEPENDENCIES: None (S3 is a root resource)
- REPLICATION: Cross-region/cross-account replication targets
- IDENTITY: KMS Keys (encryption), Bucket policies (access)

S3 buckets are often central to data pipelines - changes can affect many services.
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


class S3BucketAnalyzer(ResourceDependencyAnalyzer):
    """Analyzer for S3 Buckets."""

    @property
    def resource_type(self) -> str:
        return "aws_s3_bucket"

    def analyze(self, resource_id: str, region: str) -> DependencyAnalysis:
        """Analyze S3 bucket dependencies."""
        data = self.get_api_data(resource_id)

        if not data:
            raise ValueError(f"S3 bucket not found: {resource_id}")

        tags = data.get("tags", {})

        # Build center resource
        center = Dependency(
            resource_type="aws_s3_bucket",
            resource_id=resource_id,
            resource_name=resource_id,
            relation_type=RelationType.DEPENDENCY,
            severity=Severity.HIGH,
            metadata={
                "region": data.get("region"),
                "versioning": data.get("versioning"),
            },
        )

        # Find all dependencies
        dependencies: dict[RelationType, list[Dependency]] = {}

        # MANAGER - who controls this bucket
        managers = self._find_managers(tags)
        if managers:
            dependencies[RelationType.MANAGER] = managers

        # CONSUMERS - who uses this bucket (Lambda triggers, etc.)
        consumers = self._find_consumers(resource_id, data)
        if consumers:
            dependencies[RelationType.CONSUMER] = consumers

        # REPLICATION - cross-region/cross-account replication
        replication = self._find_replication(data)
        if replication:
            dependencies[RelationType.REPLICATION] = replication

        # IDENTITY - KMS keys, IAM policies
        identity = self._find_identity(data)
        if identity:
            dependencies[RelationType.IDENTITY] = identity

        # Build context
        context = {
            "bucket_name": resource_id,
            "region": data.get("region"),
            "versioning": data.get("versioning"),
            "encryption": data.get("encryption"),
            "public_access_block": data.get("public_access_block"),
            "logging_enabled": data.get("logging", {}).get("enabled", False),
        }

        # Detect IaC status
        iac_status = self._detect_iac_status(tags)

        return self._build_analysis(center, dependencies, context, iac_status)

    def get_api_data(self, resource_id: str) -> dict[str, Any]:
        """Get S3 bucket data from AWS API."""
        if not self.s3:
            return {}

        data: dict[str, Any] = {"bucket_name": resource_id}

        try:
            # Get bucket location
            location = self.s3.get_bucket_location(Bucket=resource_id)
            # LocationConstraint is None for us-east-1
            data["region"] = location.get("LocationConstraint") or "us-east-1"
        except Exception:
            pass

        try:
            # Get versioning
            versioning = self.s3.get_bucket_versioning(Bucket=resource_id)
            data["versioning"] = versioning.get("Status", "Disabled")
        except Exception:
            data["versioning"] = "Unknown"

        try:
            # Get encryption
            encryption = self.s3.get_bucket_encryption(Bucket=resource_id)
            rules = encryption.get("ServerSideEncryptionConfiguration", {}).get(
                "Rules", []
            )
            if rules:
                apply = rules[0].get("ApplyServerSideEncryptionByDefault", {})
                data["encryption"] = {
                    "algorithm": apply.get("SSEAlgorithm"),
                    "kms_key_id": apply.get("KMSMasterKeyID"),
                }
        except Exception:
            data["encryption"] = None

        try:
            # Get replication configuration
            replication = self.s3.get_bucket_replication(Bucket=resource_id)
            data["replication"] = replication.get("ReplicationConfiguration", {})
        except Exception:
            data["replication"] = None

        try:
            # Get logging configuration
            logging_config = self.s3.get_bucket_logging(Bucket=resource_id)
            if logging_config.get("LoggingEnabled"):
                data["logging"] = {
                    "enabled": True,
                    "target_bucket": logging_config["LoggingEnabled"].get(
                        "TargetBucket"
                    ),
                    "target_prefix": logging_config["LoggingEnabled"].get(
                        "TargetPrefix"
                    ),
                }
            else:
                data["logging"] = {"enabled": False}
        except Exception:
            data["logging"] = {"enabled": False}

        try:
            # Get bucket notification configuration
            notifications = self.s3.get_bucket_notification_configuration(
                Bucket=resource_id
            )
            data["notifications"] = {
                "lambda_functions": notifications.get(
                    "LambdaFunctionConfigurations", []
                ),
                "sqs_queues": notifications.get("QueueConfigurations", []),
                "sns_topics": notifications.get("TopicConfigurations", []),
            }
        except Exception:
            data["notifications"] = {}

        try:
            # Get public access block
            pab = self.s3.get_public_access_block(Bucket=resource_id)
            data["public_access_block"] = pab.get("PublicAccessBlockConfiguration", {})
        except Exception:
            data["public_access_block"] = None

        try:
            # Get bucket tagging
            tagging = self.s3.get_bucket_tagging(Bucket=resource_id)
            data["tags"] = {t["Key"]: t["Value"] for t in tagging.get("TagSet", [])}
        except Exception:
            data["tags"] = {}

        return data

    def _find_managers(self, tags: dict[str, str]) -> list[Dependency]:
        """Find resources that manage this bucket."""
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

    def _find_consumers(
        self, bucket_name: str, data: dict[str, Any]
    ) -> list[Dependency]:
        """Find resources that consume this bucket."""
        consumers = []

        # Lambda function triggers from bucket notifications
        notifications = data.get("notifications", {})

        for config in notifications.get("lambda_functions", []):
            lambda_arn = config.get("LambdaFunctionArn")
            if lambda_arn:
                func_name = lambda_arn.split(":")[-1]
                events = config.get("Events", [])
                consumers.append(
                    Dependency(
                        resource_type="aws_lambda_function",
                        resource_id=lambda_arn,
                        resource_name=func_name,
                        relation_type=RelationType.CONSUMER,
                        severity=Severity.HIGH,
                        warning="Lambda triggered by bucket events",
                        metadata={"events": events},
                    )
                )

        # SQS queues
        for config in notifications.get("sqs_queues", []):
            queue_arn = config.get("QueueArn")
            if queue_arn:
                queue_name = queue_arn.split(":")[-1]
                consumers.append(
                    Dependency(
                        resource_type="aws_sqs_queue",
                        resource_id=queue_arn,
                        resource_name=queue_name,
                        relation_type=RelationType.CONSUMER,
                        severity=Severity.MEDIUM,
                        warning="SQS receives bucket event notifications",
                    )
                )

        # SNS topics
        for config in notifications.get("sns_topics", []):
            topic_arn = config.get("TopicArn")
            if topic_arn:
                topic_name = topic_arn.split(":")[-1]
                consumers.append(
                    Dependency(
                        resource_type="aws_sns_topic",
                        resource_id=topic_arn,
                        resource_name=topic_name,
                        relation_type=RelationType.CONSUMER,
                        severity=Severity.MEDIUM,
                        warning="SNS receives bucket event notifications",
                    )
                )

        # Logging target bucket
        logging = data.get("logging", {})
        if logging.get("enabled"):
            target_bucket = logging.get("target_bucket")
            if target_bucket and target_bucket != bucket_name:
                consumers.append(
                    Dependency(
                        resource_type="aws_s3_bucket",
                        resource_id=target_bucket,
                        resource_name=target_bucket,
                        relation_type=RelationType.CONSUMER,
                        severity=Severity.INFO,
                        warning="Receives access logs from this bucket",
                    )
                )

        return consumers

    def _find_replication(self, data: dict[str, Any]) -> list[Dependency]:
        """Find replication targets."""
        replication_deps = []

        replication = data.get("replication")
        if not replication:
            return replication_deps

        for rule in replication.get("Rules", []):
            if rule.get("Status") != "Enabled":
                continue

            dest = rule.get("Destination", {})
            dest_bucket = dest.get("Bucket")
            if dest_bucket:
                # Extract bucket name from ARN
                bucket_name = (
                    dest_bucket.split(":")[-1]
                    if dest_bucket.startswith("arn:")
                    else dest_bucket
                )

                # Check if cross-account
                dest_account = dest.get("Account")
                current_account = self.get_current_account_id()

                severity = Severity.HIGH
                warning = "Replication target bucket"

                if dest_account and dest_account != current_account:
                    severity = Severity.CRITICAL
                    warning = f"CROSS-ACCOUNT replication to {dest_account}"

                replication_deps.append(
                    Dependency(
                        resource_type="aws_s3_bucket",
                        resource_id=bucket_name,
                        resource_name=bucket_name,
                        relation_type=RelationType.REPLICATION,
                        severity=severity,
                        warning=warning,
                        metadata={
                            "destination_account": dest_account,
                            "storage_class": dest.get("StorageClass"),
                            "rule_id": rule.get("ID"),
                        },
                    )
                )

        return replication_deps

    def _find_identity(self, data: dict[str, Any]) -> list[Dependency]:
        """Find identity/permission dependencies."""
        identity = []

        # KMS Key for encryption
        encryption = data.get("encryption")
        if encryption and encryption.get("kms_key_id"):
            kms_key = encryption["kms_key_id"]
            identity.append(
                Dependency(
                    resource_type="aws_kms_key",
                    resource_id=kms_key,
                    relation_type=RelationType.IDENTITY,
                    severity=Severity.HIGH,
                    warning="Bucket encryption key - do not delete!",
                    metadata={"algorithm": encryption.get("algorithm")},
                )
            )

        # Replication IAM role
        replication = data.get("replication")
        if replication:
            role_arn = replication.get("Role")
            if role_arn:
                role_name = role_arn.split("/")[-1] if "/" in role_arn else role_arn
                identity.append(
                    Dependency(
                        resource_type="aws_iam_role",
                        resource_id=role_arn,
                        resource_name=role_name,
                        relation_type=RelationType.IDENTITY,
                        severity=Severity.HIGH,
                        warning="Replication requires this IAM role",
                    )
                )

        return identity

    def _generate_warnings(
        self,
        center: Dependency,
        dependencies: dict[RelationType, list[Dependency]],
        blast_radius: Any,
    ) -> list[str]:
        """Generate warnings specific to S3 buckets."""
        warnings = super()._generate_warnings(center, dependencies, blast_radius)

        # Replication warnings
        replication = dependencies.get(RelationType.REPLICATION, [])
        if replication:
            cross_account = [r for r in replication if r.severity == Severity.CRITICAL]
            if cross_account:
                warnings.insert(
                    0,
                    f"Bucket replicates to {len(cross_account)} cross-account "
                    "destination(s) - changes may affect external systems",
                )
            else:
                warnings.insert(
                    0,
                    f"Bucket replicates to {len(replication)} destination(s)",
                )

        # Lambda trigger warnings
        consumers = dependencies.get(RelationType.CONSUMER, [])
        lambdas = [c for c in consumers if c.resource_type == "aws_lambda_function"]
        if lambdas:
            warnings.insert(
                0,
                f"{len(lambdas)} Lambda function(s) triggered by bucket events",
            )

        return warnings
