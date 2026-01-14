"""
Graph-Aware IAM Least Privilege Policy Generator.

This module generates precise, resource-level IAM policies by analyzing the
dependency graph with intelligent boundary control. It differentiates RepliMap
from tools like Former2 that generate overly permissive policies.

Key Innovation: Instead of "what resources exist → give permissions", we ask
"what does THIS compute resource connect to → give ONLY those permissions
with precise ARNs".

Key Features:
1. Boundary-aware traversal (prevents over-connectivity)
2. Intent-aware action mapping (Producer/Consumer/Controller)
3. Safe resource compression (respects security boundaries)
4. AWS partition detection (aws, aws-cn, aws-us-gov)
5. Policy size optimization (compression + sharding for 6KB limit)
6. Full Terraform module output (Role + Policy + Attachment)
7. Cross-account resource detection
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine
    from replimap.core.models import ResourceNode

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS AND CONSTANTS
# ============================================================


class PolicyScope(Enum):
    """Policy scope determines action granularity."""

    RUNTIME_READ = "runtime_read"  # Get, List, Receive
    RUNTIME_WRITE = "runtime_write"  # Put, Send, Delete
    RUNTIME_FULL = "runtime_full"  # Read + Write
    INFRA_READ = "infra_read"  # Describe* (Terraform plan)
    INFRA_DEPLOY = "infra_deploy"  # Create*, Delete* (Terraform apply)


class AccessRole(Enum):
    """The role a principal plays in relation to a resource."""

    PRODUCER = "producer"  # Writing/sending data
    CONSUMER = "consumer"  # Reading/receiving data
    CONTROLLER = "controller"  # Managing lifecycle
    BIDIRECTIONAL = "bidirectional"  # Both read and write


class ResourceBoundary(Enum):
    """How a resource type behaves in graph traversal."""

    TERMINAL = "terminal"  # Stop traversal (other compute)
    DATA = "data"  # Grant permissions, don't traverse to consumers
    TRANSITIVE = "transitive"  # Transparent, traverse through
    SECURITY = "security"  # Always traverse (encryption dependencies)


# ============================================================
# TRAVERSAL CONTROLLER
# ============================================================


class TraversalController:
    """
    Controls graph traversal to prevent over-connectivity.

    This is the CORE innovation that makes RepliMap's IAM generation
    superior to tools like Former2.
    """

    BOUNDARY_MAP: dict[str, ResourceBoundary] = {
        # TERMINAL - Other compute (NEVER traverse)
        "aws_lambda_function": ResourceBoundary.TERMINAL,
        "aws_instance": ResourceBoundary.TERMINAL,
        "aws_ecs_service": ResourceBoundary.TERMINAL,
        "aws_ecs_task_definition": ResourceBoundary.TERMINAL,
        "aws_eks_node_group": ResourceBoundary.TERMINAL,
        "aws_batch_job_definition": ResourceBoundary.TERMINAL,
        "aws_sagemaker_endpoint": ResourceBoundary.TERMINAL,
        # DATA - Storage, Messaging, Database
        "aws_s3_bucket": ResourceBoundary.DATA,
        "aws_dynamodb_table": ResourceBoundary.DATA,
        "aws_sqs_queue": ResourceBoundary.DATA,
        "aws_sns_topic": ResourceBoundary.DATA,
        "aws_kinesis_stream": ResourceBoundary.DATA,
        "aws_db_instance": ResourceBoundary.DATA,
        "aws_rds_cluster": ResourceBoundary.DATA,
        "aws_elasticache_cluster": ResourceBoundary.DATA,
        "aws_cloudwatch_log_group": ResourceBoundary.DATA,
        # SECURITY - Always traverse
        "aws_kms_key": ResourceBoundary.SECURITY,
        "aws_kms_alias": ResourceBoundary.SECURITY,
        "aws_secretsmanager_secret": ResourceBoundary.SECURITY,
        "aws_ssm_parameter": ResourceBoundary.SECURITY,
        "aws_iam_instance_profile": ResourceBoundary.SECURITY,
        "aws_iam_role": ResourceBoundary.SECURITY,
        # TRANSITIVE - Networking (transparent)
        "aws_vpc": ResourceBoundary.TRANSITIVE,
        "aws_subnet": ResourceBoundary.TRANSITIVE,
        "aws_security_group": ResourceBoundary.TRANSITIVE,
        "aws_network_interface": ResourceBoundary.TRANSITIVE,
        "aws_lb": ResourceBoundary.TRANSITIVE,
        "aws_lb_target_group": ResourceBoundary.TRANSITIVE,
    }

    # Edges that indicate "ownership" (reverse direction) - block these
    OWNERSHIP_EDGES: frozenset[str] = frozenset(
        {
            "event_source_mapping",  # SQS triggers Lambda
            "triggered_by",
            "invoked_by",
            "subscribed_by",
        }
    )

    def __init__(
        self, include_networking: bool = False, strict_mode: bool = True
    ) -> None:
        self.include_networking = include_networking
        self.strict_mode = strict_mode

    def get_boundary(self, resource_type: str) -> ResourceBoundary:
        """Get boundary classification for resource type."""
        return self.BOUNDARY_MAP.get(resource_type, ResourceBoundary.DATA)

    def should_traverse_through(
        self,
        node_type: str,
        depth: int,
        edge_type: str | None = None,
    ) -> bool:
        """Determine if traversal should continue through this node."""
        # Always allow depth 1 (direct neighbors), except ownership edges
        if depth <= 1:
            if edge_type and edge_type.lower() in self.OWNERSHIP_EDGES:
                return False
            return True

        boundary = self.get_boundary(node_type)

        # Never traverse through TERMINAL
        if boundary == ResourceBoundary.TERMINAL:
            return False

        # Always traverse through SECURITY and TRANSITIVE
        if boundary in (ResourceBoundary.SECURITY, ResourceBoundary.TRANSITIVE):
            return True

        # DATA: don't traverse to consumers in strict mode
        if boundary == ResourceBoundary.DATA:
            return not self.strict_mode

        return False

    def should_include_in_results(
        self,
        node_type: str,
        edge_type: str | None = None,
    ) -> bool:
        """Determine if permissions should be granted for this resource."""
        # Skip ownership edges
        if edge_type and edge_type.lower() in self.OWNERSHIP_EDGES:
            return False

        boundary = self.get_boundary(node_type)

        # Never grant permissions on TERMINAL
        if boundary == ResourceBoundary.TERMINAL:
            return False

        # Skip TRANSITIVE unless explicitly requested
        if boundary == ResourceBoundary.TRANSITIVE:
            return self.include_networking

        return True


# ============================================================
# INTENT-AWARE ACTION MAPPER
# ============================================================


class IntentAwareActionMapper:
    """
    Maps resource types to IAM actions based on access intent.

    Actions depend on BOTH scope AND access role (direction).
    """

    ACTION_MAP: dict[str, dict[PolicyScope, dict[AccessRole, list[str]]]] = {
        "aws_s3_bucket": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: ["s3:PutObject", "s3:DeleteObject"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket",
                    "s3:PutObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                ],
            },
            PolicyScope.INFRA_DEPLOY: {
                AccessRole.CONTROLLER: [
                    "s3:CreateBucket",
                    "s3:DeleteBucket",
                    "s3:PutBucketVersioning",
                    "s3:PutBucketPolicy",
                    "s3:PutEncryptionConfiguration",
                    "s3:GetBucketLocation",
                    "s3:GetBucketVersioning",
                    "s3:GetBucketPolicy",
                ],
            },
        },
        "aws_sqs_queue": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ChangeMessageVisibility",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "sqs:SendMessage",
                    "sqs:SendMessageBatch",
                    "sqs:GetQueueUrl",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:SendMessage",
                    "sqs:SendMessageBatch",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ChangeMessageVisibility",
                ],
            },
        },
        "aws_sns_topic": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: ["sns:GetTopicAttributes"],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: ["sns:Publish"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "sns:GetTopicAttributes",
                    "sns:Publish",
                ],
            },
        },
        "aws_dynamodb_table": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "dynamodb:GetItem",
                    "dynamodb:BatchGetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:DescribeTable",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:BatchWriteItem",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "dynamodb:GetItem",
                    "dynamodb:BatchGetItem",
                    "dynamodb:Query",
                    "dynamodb:Scan",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:DeleteItem",
                    "dynamodb:BatchWriteItem",
                    "dynamodb:DescribeTable",
                ],
            },
        },
        "aws_kinesis_stream": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "kinesis:GetRecords",
                    "kinesis:GetShardIterator",
                    "kinesis:DescribeStream",
                    "kinesis:ListShards",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: ["kinesis:PutRecord", "kinesis:PutRecords"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "kinesis:GetRecords",
                    "kinesis:GetShardIterator",
                    "kinesis:DescribeStream",
                    "kinesis:ListShards",
                    "kinesis:PutRecord",
                    "kinesis:PutRecords",
                ],
            },
        },
        "aws_kms_key": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: ["kms:Decrypt", "kms:DescribeKey"],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "kms:Encrypt",
                    "kms:GenerateDataKey",
                    "kms:GenerateDataKeyWithoutPlaintext",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                    "kms:GenerateDataKeyWithoutPlaintext",
                    "kms:DescribeKey",
                ],
            },
        },
        "aws_secretsmanager_secret": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "secretsmanager:PutSecretValue",
                    "secretsmanager:UpdateSecret",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:DescribeSecret",
                    "secretsmanager:PutSecretValue",
                    "secretsmanager:UpdateSecret",
                ],
            },
        },
        "aws_ssm_parameter": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                ],
            },
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "ssm:PutParameter",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "ssm:GetParameter",
                    "ssm:GetParameters",
                    "ssm:GetParametersByPath",
                    "ssm:PutParameter",
                ],
            },
        },
        "aws_cloudwatch_log_group": {
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.PRODUCER: [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
            },
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: [
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents",
                ],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:GetLogEvents",
                    "logs:FilterLogEvents",
                ],
            },
        },
        "aws_lambda_function": {
            PolicyScope.RUNTIME_WRITE: {
                AccessRole.CONTROLLER: ["lambda:InvokeFunction"],
            },
        },
        "aws_db_instance": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: ["rds:DescribeDBInstances"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: ["rds:DescribeDBInstances"],
            },
        },
        "aws_elasticache_cluster": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: ["elasticache:DescribeCacheClusters"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: ["elasticache:DescribeCacheClusters"],
            },
        },
        "aws_ebs_volume": {
            PolicyScope.RUNTIME_READ: {
                AccessRole.CONSUMER: ["ec2:DescribeVolumes"],
            },
            PolicyScope.RUNTIME_FULL: {
                AccessRole.BIDIRECTIONAL: ["ec2:DescribeVolumes"],
            },
            PolicyScope.INFRA_DEPLOY: {
                AccessRole.CONTROLLER: [
                    "ec2:CreateVolume",
                    "ec2:DeleteVolume",
                    "ec2:AttachVolume",
                    "ec2:DetachVolume",
                    "ec2:ModifyVolume",
                    "ec2:DescribeVolumes",
                ],
            },
        },
    }

    # Edge type to access role mapping
    EDGE_ROLE_MAP: dict[str, AccessRole] = {
        "writes_to": AccessRole.PRODUCER,
        "sends_to": AccessRole.PRODUCER,
        "publishes_to": AccessRole.PRODUCER,
        "destination": AccessRole.PRODUCER,
        "reads_from": AccessRole.CONSUMER,
        "receives_from": AccessRole.CONSUMER,
        "triggered_by": AccessRole.CONSUMER,
        "event_source": AccessRole.CONSUMER,
        "invokes": AccessRole.CONTROLLER,
        "manages": AccessRole.CONTROLLER,
        "uses": AccessRole.BIDIRECTIONAL,
        "connects_to": AccessRole.BIDIRECTIONAL,
        "belongs_to": AccessRole.BIDIRECTIONAL,
        "references": AccessRole.BIDIRECTIONAL,
    }

    COMPUTE_TYPES = {
        "aws_lambda_function",
        "aws_instance",
        "aws_ecs_service",
        "aws_ecs_task_definition",
        "aws_eks_node_group",
    }

    def get_actions(
        self,
        resource_type: str,
        scope: PolicyScope,
        access_role: AccessRole = AccessRole.BIDIRECTIONAL,
    ) -> list[str]:
        """Get actions for resource type, scope, and access role."""
        type_actions = self.ACTION_MAP.get(resource_type, {})
        scope_actions = type_actions.get(scope, {})

        # Try exact role match
        actions = scope_actions.get(access_role, [])

        # Fallback to bidirectional for specific roles
        if not actions and access_role != AccessRole.BIDIRECTIONAL:
            actions = scope_actions.get(AccessRole.BIDIRECTIONAL, [])

        # For BIDIRECTIONAL, try combining producer/consumer for the scope
        if not actions and access_role == AccessRole.BIDIRECTIONAL:
            if scope == PolicyScope.RUNTIME_WRITE:
                # BIDIRECTIONAL write should get PRODUCER actions
                actions = scope_actions.get(AccessRole.PRODUCER, [])
            elif scope == PolicyScope.RUNTIME_READ:
                # BIDIRECTIONAL read should get CONSUMER actions
                actions = scope_actions.get(AccessRole.CONSUMER, [])

        # For RUNTIME_FULL, combine read and write
        if not actions and scope == PolicyScope.RUNTIME_FULL:
            read_actions = self.get_actions(
                resource_type, PolicyScope.RUNTIME_READ, access_role
            )
            write_actions = self.get_actions(
                resource_type, PolicyScope.RUNTIME_WRITE, access_role
            )
            actions = list(set(read_actions + write_actions))

        return sorted(set(actions))

    def determine_access_role(
        self,
        source_type: str,
        target_type: str,
        edge_type: str | None = None,
    ) -> AccessRole:
        """Determine access role from edge type or resource types."""
        if edge_type:
            edge_lower = edge_type.lower()
            for key, role in self.EDGE_ROLE_MAP.items():
                if key in edge_lower:
                    return role

        # Infer from types
        if source_type == "aws_lambda_function":
            if target_type in ("aws_sqs_queue", "aws_sns_topic"):
                return AccessRole.PRODUCER
            if target_type == "aws_dynamodb_table":
                return AccessRole.BIDIRECTIONAL

        return AccessRole.BIDIRECTIONAL

    def is_compute_type(self, resource_type: str) -> bool:
        return resource_type in self.COMPUTE_TYPES


# ============================================================
# ARN BUILDER WITH PARTITION DETECTION
# ============================================================


class ARNBuilder:
    """Builds precise ARNs with AWS partition detection."""

    PARTITION_MAP = {
        "cn-north-1": "aws-cn",
        "cn-northwest-1": "aws-cn",
        "us-gov-west-1": "aws-us-gov",
        "us-gov-east-1": "aws-us-gov",
    }

    def __init__(self, account_id: str, region: str):
        self.account_id = account_id
        self.region = region
        self.partition = self._detect_partition(region)

    def _detect_partition(self, region: str) -> str:
        if region in self.PARTITION_MAP:
            return self.PARTITION_MAP[region]
        if region.startswith("cn-"):
            return "aws-cn"
        if region.startswith("us-gov-"):
            return "aws-us-gov"
        return "aws"

    def build_arn(
        self,
        resource_type: str,
        resource_id: str,
        resource_name: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> list[str]:
        """Build ARN(s) for a resource. Some need multiple (S3 bucket + objects)."""
        attributes = attributes or {}

        # Use ARN from attributes if available
        if "arn" in attributes and attributes["arn"]:
            arns = [attributes["arn"]]
            if resource_type == "aws_s3_bucket":
                arns.append(f"{attributes['arn']}/*")
            return arns

        name = resource_name or attributes.get("name") or resource_id

        # S3 (no account ID in ARN)
        if resource_type == "aws_s3_bucket":
            bucket = attributes.get("bucket") or attributes.get("id") or name
            return [
                f"arn:{self.partition}:s3:::{bucket}",
                f"arn:{self.partition}:s3:::{bucket}/*",
            ]

        # DynamoDB (include index wildcard)
        if resource_type == "aws_dynamodb_table":
            table = attributes.get("name") or attributes.get("id") or name
            base_arn = (
                f"arn:{self.partition}:dynamodb:{self.region}:"
                f"{self.account_id}:table/{table}"
            )
            return [base_arn, f"{base_arn}/index/*"]

        # SQS
        if resource_type == "aws_sqs_queue":
            queue = name
            if "url" in attributes:
                queue = attributes["url"].split("/")[-1]
            elif "QueueUrl" in attributes:
                queue = attributes["QueueUrl"].split("/")[-1]
            return [f"arn:{self.partition}:sqs:{self.region}:{self.account_id}:{queue}"]

        # SNS
        if resource_type == "aws_sns_topic":
            topic = (
                attributes.get("name")
                or attributes.get("TopicArn", "").split(":")[-1]
                or name
            )
            return [f"arn:{self.partition}:sns:{self.region}:{self.account_id}:{topic}"]

        # Lambda
        if resource_type == "aws_lambda_function":
            func = (
                attributes.get("function_name")
                or attributes.get("FunctionName")
                or name
            )
            return [
                f"arn:{self.partition}:lambda:{self.region}:"
                f"{self.account_id}:function:{func}"
            ]

        # KMS
        if resource_type == "aws_kms_key":
            key_id = attributes.get("key_id") or attributes.get("KeyId") or resource_id
            return [
                f"arn:{self.partition}:kms:{self.region}:{self.account_id}:key/{key_id}"
            ]

        # Secrets Manager (has random suffix)
        if resource_type == "aws_secretsmanager_secret":
            secret = attributes.get("name") or attributes.get("Name") or name
            return [
                f"arn:{self.partition}:secretsmanager:{self.region}:"
                f"{self.account_id}:secret:{secret}*"
            ]

        # SSM Parameter Store
        if resource_type == "aws_ssm_parameter":
            param = attributes.get("name") or attributes.get("Name") or name
            return [
                f"arn:{self.partition}:ssm:{self.region}:"
                f"{self.account_id}:parameter{param}"
            ]

        # CloudWatch Logs
        if resource_type == "aws_cloudwatch_log_group":
            log_group = attributes.get("name") or attributes.get("logGroupName") or name
            base_arn = (
                f"arn:{self.partition}:logs:{self.region}:"
                f"{self.account_id}:log-group:{log_group}"
            )
            return [base_arn, f"{base_arn}:*"]

        # Kinesis
        if resource_type == "aws_kinesis_stream":
            stream = attributes.get("name") or attributes.get("StreamName") or name
            return [
                f"arn:{self.partition}:kinesis:{self.region}:"
                f"{self.account_id}:stream/{stream}"
            ]

        # RDS
        if resource_type == "aws_db_instance":
            db_id = (
                attributes.get("db_instance_identifier")
                or attributes.get("DBInstanceIdentifier")
                or name
            )
            return [
                f"arn:{self.partition}:rds:{self.region}:{self.account_id}:db:{db_id}"
            ]

        # ElastiCache
        if resource_type == "aws_elasticache_cluster":
            cluster_id = (
                attributes.get("cluster_id") or attributes.get("CacheClusterId") or name
            )
            return [
                f"arn:{self.partition}:elasticache:{self.region}:"
                f"{self.account_id}:cluster:{cluster_id}"
            ]

        # EBS Volume
        if resource_type == "aws_ebs_volume":
            volume_id = resource_id  # EBS volume IDs are already like "vol-xxx"
            return [
                f"arn:{self.partition}:ec2:{self.region}:"
                f"{self.account_id}:volume/{volume_id}"
            ]

        # Fallback
        logger.warning(f"No ARN builder for {resource_type}, using wildcard")
        return ["*"]


# ============================================================
# SAFE RESOURCE COMPRESSOR
# ============================================================


class SafeResourceCompressor:
    """
    Safely compresses ARN lists while respecting security boundaries.

    NEVER compresses: S3 buckets, KMS keys, Secrets (too sensitive)
    """

    MIN_THRESHOLD = 10
    NO_COMPRESS_SERVICES: frozenset[str] = frozenset(
        {
            "s3",
            "kms",
            "secretsmanager",
            "iam",
        }
    )

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def compress(self, resources: list[str]) -> list[str]:
        """Compress ARNs safely."""
        if len(resources) < self.MIN_THRESHOLD:
            return resources

        # Group by service
        by_service: dict[str, list[str]] = defaultdict(list)
        for arn in resources:
            service = self._extract_service(arn)
            by_service[service].append(arn)

        result = []
        for service, arns in by_service.items():
            if service in self.NO_COMPRESS_SERVICES:
                result.extend(arns)
            else:
                result.extend(self._try_compress(arns))

        return sorted(set(result))

    def _extract_service(self, arn: str) -> str:
        if arn == "*":
            return "*"
        parts = arn.split(":")
        return parts[2] if len(parts) > 2 else "unknown"

    def _try_compress(self, arns: list[str]) -> list[str]:
        if len(arns) < self.MIN_THRESHOLD:
            return arns

        prefix = self._find_common_prefix(arns)
        if prefix and len(prefix) > 40:
            logger.info(f"Compressed {len(arns)} ARNs to: {prefix}*")
            return [f"{prefix}*"]

        return arns

    def _find_common_prefix(self, strings: list[str]) -> str | None:
        if not strings:
            return None

        prefix = strings[0]
        for s in strings[1:]:
            while prefix and not s.startswith(prefix):
                prefix = prefix[:-1]

        # Don't cut in middle of component
        if prefix:
            last_sep = max(prefix.rfind(":"), prefix.rfind("/"))
            if last_sep > len(prefix) * 0.5:
                prefix = prefix[: last_sep + 1]

        return prefix if len(prefix) > 30 else None


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class IAMStatement:
    """IAM policy statement."""

    sid: str
    effect: str = "Allow"
    actions: list[str] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    conditions: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        stmt: dict[str, Any] = {
            "Sid": self.sid,
            "Effect": self.effect,
            "Action": sorted(set(self.actions)),
            "Resource": (
                self.resources if len(self.resources) != 1 else self.resources[0]
            ),
        }
        if self.conditions:
            stmt["Condition"] = self._merge_conditions()
        return stmt

    def _merge_conditions(self) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for cond in self.conditions:
            for op, keys in cond.items():
                if op not in merged:
                    merged[op] = {}
                merged[op].update(keys)
        return merged

    def estimated_size(self) -> int:
        return len(json.dumps(self.to_dict()))


@dataclass
class IAMPolicy:
    """IAM policy with Terraform generation."""

    name: str
    description: str
    statements: list[IAMStatement] = field(default_factory=list)
    version: str = "2012-10-17"

    # Service principal mapping for Trust Policy
    SERVICE_PRINCIPAL_MAP: dict[str, str] = field(
        default_factory=lambda: {
            "aws_lambda_function": "lambda.amazonaws.com",
            "aws_instance": "ec2.amazonaws.com",
            "aws_ecs_task_definition": "ecs-tasks.amazonaws.com",
            "aws_eks_node_group": "ec2.amazonaws.com",
            "aws_batch_job_definition": "batch.amazonaws.com",
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "Version": self.version,
            "Statement": [s.to_dict() for s in self.statements],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def estimated_size(self) -> int:
        return len(json.dumps(self.to_dict(), separators=(",", ":")))

    def is_within_limit(self, limit: int = 6144) -> bool:
        return self.estimated_size() <= limit

    def action_count(self) -> int:
        return sum(len(s.actions) for s in self.statements)

    def resource_count(self) -> int:
        return sum(len(s.resources) for s in self.statements)

    def is_least_privilege(self) -> bool:
        for s in self.statements:
            if s.resources == ["*"]:
                return False
            if any(a == "*" or a.endswith(":*") for a in s.actions):
                return False
        return True

    def to_terraform(self) -> str:
        """Generate aws_iam_policy resource."""
        safe_name = re.sub(r"[^a-zA-Z0-9_]", "_", self.name.lower())
        return f'''
resource "aws_iam_policy" "{safe_name}" {{
  name        = "{self.name}"
  description = "{self.description}"

  policy = <<-POLICY
{self.to_json(indent=2)}
  POLICY
}}
'''

    def to_terraform_module(
        self,
        role_name: str,
        create_role: bool = False,
        principal_type: str = "aws_lambda_function",
    ) -> str:
        """Generate complete Terraform module with Role + Policy + Attachment."""
        safe_policy = re.sub(r"[^a-zA-Z0-9_]", "_", self.name.lower())
        safe_role = re.sub(r"[^a-zA-Z0-9_]", "_", role_name.lower())
        service = self.SERVICE_PRINCIPAL_MAP.get(principal_type, "lambda.amazonaws.com")

        parts = []

        if create_role:
            parts.append(
                f'''
resource "aws_iam_role" "{safe_role}" {{
  name = "{role_name}"

  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{ Service = "{service}" }}
    }}]
  }})

  tags = {{ ManagedBy = "RepliMap" }}
}}
'''
            )

        parts.append(self.to_terraform())

        role_ref = f"aws_iam_role.{safe_role}.name" if create_role else f'"{role_name}"'
        parts.append(
            f'''
resource "aws_iam_role_policy_attachment" "{safe_policy}_attach" {{
  role       = {role_ref}
  policy_arn = aws_iam_policy.{safe_policy}.arn
}}
'''
        )

        return "\n".join(parts)


# ============================================================
# POLICY OPTIMIZER
# ============================================================


class PolicyOptimizer:
    """Optimizes policies to fit AWS 6KB limit."""

    MANAGED_LIMIT = 6144
    SAFETY_MARGIN = 0.9

    def __init__(self, strict_compression: bool = True):
        self.compressor = SafeResourceCompressor(strict_mode=strict_compression)
        self.max_size = int(self.MANAGED_LIMIT * self.SAFETY_MARGIN)

    def optimize(self, policy: IAMPolicy) -> list[IAMPolicy]:
        """Optimize policy: compress, then shard if needed."""
        compressed = self._compress(policy)

        if compressed.estimated_size() <= self.max_size:
            return [compressed]

        logger.warning(f"Policy {policy.name} exceeds limit, sharding...")
        return self._shard(compressed)

    def _compress(self, policy: IAMPolicy) -> IAMPolicy:
        return IAMPolicy(
            name=policy.name,
            description=policy.description,
            statements=[
                IAMStatement(
                    sid=s.sid,
                    effect=s.effect,
                    actions=s.actions,
                    resources=self.compressor.compress(s.resources),
                    conditions=s.conditions,
                )
                for s in policy.statements
            ],
        )

    def _shard(self, policy: IAMPolicy) -> list[IAMPolicy]:
        policies = []
        current_stmts: list[IAMStatement] = []
        current_size = 100
        part = 1

        for stmt in policy.statements:
            stmt_size = stmt.estimated_size()

            if current_size + stmt_size > self.max_size and current_stmts:
                policies.append(
                    IAMPolicy(
                        name=f"{policy.name}-part{part}",
                        description=f"{policy.description} (Part {part})",
                        statements=current_stmts,
                    )
                )
                part += 1
                current_stmts = []
                current_size = 100

            current_stmts.append(stmt)
            current_size += stmt_size

        if current_stmts:
            name = f"{policy.name}-part{part}" if part > 1 else policy.name
            policies.append(
                IAMPolicy(
                    name=name, description=policy.description, statements=current_stmts
                )
            )

        return policies


# ============================================================
# BASELINE POLICY GENERATOR
# ============================================================


class BaselinePolicyGenerator:
    """
    Generates baseline IAM policies for isolated compute resources.

    When a compute resource has no data dependencies (only TRANSITIVE connections
    like VPC/Subnet/SG), we provide a safe baseline policy with common patterns:

    1. CloudWatch Logs (write) - for logging
    2. SSM Parameter Store (read) - for configuration
    3. KMS (encrypt/decrypt) - for encryption
    4. EC2 Describe (read) - for instance metadata

    This prevents completely empty policies while still being least-privilege.
    """

    def __init__(self, arn_builder: ARNBuilder):
        self.arn_builder = arn_builder

    def generate_baseline(
        self,
        principal_name: str,
        principal_type: str,
        scope: PolicyScope,
    ) -> list[IAMStatement]:
        """
        Generate baseline statements for a compute resource.

        Args:
            principal_name: Name of the compute resource
            principal_type: Type of compute resource (aws_instance, etc.)
            scope: Policy scope (runtime_read, runtime_write, etc.)

        Returns:
            List of baseline IAM statements
        """
        statements: list[IAMStatement] = []

        # CloudWatch Logs - always needed for observability
        if scope in (
            PolicyScope.RUNTIME_READ,
            PolicyScope.RUNTIME_WRITE,
            PolicyScope.RUNTIME_FULL,
        ):
            log_group = f"/aws/{self._get_log_prefix(principal_type)}/{principal_name}"
            statements.append(
                IAMStatement(
                    sid="BaselineCloudWatchLogs",
                    actions=[
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=[
                        f"arn:{self.arn_builder.partition}:logs:"
                        f"{self.arn_builder.region}:{self.arn_builder.account_id}:"
                        f"log-group:{log_group}",
                        f"arn:{self.arn_builder.partition}:logs:"
                        f"{self.arn_builder.region}:{self.arn_builder.account_id}:"
                        f"log-group:{log_group}:*",
                    ],
                )
            )

        # SSM Parameter Store - common for config (scoped to prefix)
        if scope in (PolicyScope.RUNTIME_READ, PolicyScope.RUNTIME_FULL):
            statements.append(
                IAMStatement(
                    sid="BaselineSSMParameters",
                    actions=[
                        "ssm:GetParameter",
                        "ssm:GetParameters",
                        "ssm:GetParametersByPath",
                    ],
                    resources=[
                        f"arn:{self.arn_builder.partition}:ssm:"
                        f"{self.arn_builder.region}:{self.arn_builder.account_id}:"
                        f"parameter/{principal_name}/*",
                    ],
                )
            )

        # EC2 Describe - for instance metadata (EC2 only)
        if principal_type == "aws_instance" and scope in (
            PolicyScope.RUNTIME_READ,
            PolicyScope.RUNTIME_FULL,
        ):
            statements.append(
                IAMStatement(
                    sid="BaselineEC2Describe",
                    actions=[
                        "ec2:DescribeInstances",
                        "ec2:DescribeTags",
                        "ec2:DescribeVolumes",
                    ],
                    resources=["*"],
                    conditions=[
                        {
                            "StringEquals": {
                                "ec2:ResourceTag/Name": principal_name,
                            }
                        }
                    ],
                )
            )

        return statements

    def _get_log_prefix(self, principal_type: str) -> str:
        """Get CloudWatch Logs prefix for principal type."""
        prefix_map = {
            "aws_lambda_function": "lambda",
            "aws_instance": "ec2",
            "aws_ecs_service": "ecs",
            "aws_ecs_task_definition": "ecs",
            "aws_eks_node_group": "eks",
        }
        return prefix_map.get(principal_type, "compute")


# ============================================================
# MAIN GENERATOR
# ============================================================


class GraphAwareIAMGenerator:
    """
    Production-grade Graph-Aware IAM Policy Generator.

    Features:
    - Boundary-aware traversal (prevents over-connectivity)
    - Intent-aware action mapping (Producer/Consumer)
    - Safe resource compression
    - Cross-account detection
    - Full Terraform module output
    """

    def __init__(
        self,
        graph: GraphEngine,
        account_id: str,
        region: str,
        strict_mode: bool = True,
    ):
        self.graph = graph
        self.account_id = account_id
        self.region = region
        self.strict_mode = strict_mode

        self.mapper = IntentAwareActionMapper()
        self.arn_builder = ARNBuilder(account_id, region)
        self.optimizer = PolicyOptimizer(strict_compression=strict_mode)
        self.baseline_generator = BaselinePolicyGenerator(self.arn_builder)

    def generate_for_principal(
        self,
        principal_resource_id: str,
        scope: PolicyScope = PolicyScope.RUNTIME_READ,
        max_depth: int = 3,
        include_networking: bool = False,
        optimize: bool = True,
        use_baseline_fallback: bool = True,
        enrich_graph: bool = False,
    ) -> list[IAMPolicy]:
        """
        Generate IAM policy for a compute resource.

        Args:
            principal_resource_id: ID of Lambda, EC2, ECS, etc.
            scope: Access level (runtime_read, runtime_write, etc.)
            max_depth: Traversal depth limit
            include_networking: Include VPC/Subnet resources
            optimize: Apply size optimization
            use_baseline_fallback: Generate baseline policy if no deps found
            enrich_graph: Run graph enrichment to discover implicit dependencies

        Returns:
            List of IAM policies (usually 1, multiple if sharded)
        """
        principal = self.graph.get_resource(principal_resource_id)
        if not principal:
            raise ValueError(f"Resource not found: {principal_resource_id}")

        # Optional: Run graph enrichment to discover implicit dependencies
        if enrich_graph:
            try:
                from replimap.core.enrichment import GraphEnricher

                enricher = GraphEnricher(self.graph)
                enricher.enrich()
            except ImportError:
                logger.warning("Graph enrichment module not available")

        controller = TraversalController(
            include_networking=include_networking,
            strict_mode=self.strict_mode,
        )

        # Boundary-aware traversal
        connections = self._traverse_with_boundaries(
            principal_resource_id, controller, max_depth
        )

        logger.info(f"Found {len(connections)} resources for {principal_resource_id}")

        # Build statements
        statements = self._build_statements(principal, connections, scope)

        # Fallback to baseline policy if no data dependencies found
        principal_type = str(principal.resource_type)
        principal_name = principal.original_name or principal_resource_id.split(":")[-1]

        if not statements and use_baseline_fallback:
            statements = self.baseline_generator.generate_baseline(
                principal_name, principal_type, scope
            )

        # Add CloudWatch Logs for Lambda (if not already in baseline)
        if principal_type == "aws_lambda_function" and scope in (
            PolicyScope.RUNTIME_READ,
            PolicyScope.RUNTIME_WRITE,
            PolicyScope.RUNTIME_FULL,
        ):
            log_stmt = self._generate_logs_statement(principal)
            if log_stmt:
                statements.append(log_stmt)

        # Create policy
        is_baseline = not connections and use_baseline_fallback
        policy_suffix = "-baseline" if is_baseline else ""
        policy = IAMPolicy(
            name=f"{principal_name}-{scope.value}{policy_suffix}",
            description=(
                f"{'Baseline ' if is_baseline else ''}Least privilege {scope.value} "
                f"policy for {principal_name}. Generated by RepliMap."
            ),
            statements=statements,
        )

        return self.optimizer.optimize(policy) if optimize else [policy]

    def _traverse_with_boundaries(
        self,
        start_id: str,
        controller: TraversalController,
        max_depth: int,
    ) -> list[dict[str, Any]]:
        """BFS traversal with boundary control."""
        connections: list[dict[str, Any]] = []
        visited: set[str] = set()
        # Queue: (node_id, depth, edge_type)
        queue: list[tuple[str, int, str | None]] = [(start_id, 0, None)]

        while queue:
            node_id, depth, edge_type = queue.pop(0)

            if node_id in visited or depth > max_depth:
                continue

            visited.add(node_id)
            node = self.graph.get_resource(node_id)
            if not node:
                continue

            node_type = str(node.resource_type)

            # Add to results if not start and should include
            if node_id != start_id:
                if controller.should_include_in_results(node_type, edge_type):
                    # Check cross-account
                    self._check_cross_account(node)

                    connections.append(
                        {
                            "id": node.id,
                            "type": node_type,
                            "name": node.original_name,
                            "attributes": node.config,
                            "edge_type": edge_type,
                        }
                    )

            # Continue traversal if allowed
            if not controller.should_traverse_through(node_type, depth, edge_type):
                continue

            # Get edges with relation data
            for dep in node.dependencies:
                if dep not in visited:
                    # Get edge relation from graph
                    relation = self._get_edge_relation(node_id, dep)
                    queue.append((dep, depth + 1, relation))

        return connections

    def _get_edge_relation(self, source: str, target: str) -> str | None:
        """Get the relation type for an edge."""
        for s, t, data in self.graph._graph.edges(data=True):
            if s == source and t == target:
                return data.get("relation")
        return None

    def _build_statements(
        self,
        principal: ResourceNode,
        connections: list[dict[str, Any]],
        scope: PolicyScope,
    ) -> list[IAMStatement]:
        """Build IAM statements from connections."""
        grouped: dict[tuple[str, AccessRole], list[dict[str, Any]]] = defaultdict(list)

        principal_type = str(principal.resource_type)
        for conn in connections:
            role = self.mapper.determine_access_role(
                principal_type, conn["type"], conn.get("edge_type")
            )
            grouped[(conn["type"], role)].append(conn)

        statements = []
        for (rtype, role), resources in sorted(grouped.items()):
            actions = self.mapper.get_actions(rtype, scope, role)
            if not actions:
                continue

            arns = []
            for r in resources:
                arns.extend(
                    self.arn_builder.build_arn(
                        rtype, r["id"], r.get("name"), r.get("attributes", {})
                    )
                )

            statements.append(
                IAMStatement(
                    sid=self._generate_sid(rtype, role),
                    actions=actions,
                    resources=sorted(set(arns)),
                )
            )

        return statements

    def _generate_sid(self, resource_type: str, role: AccessRole) -> str:
        parts = resource_type.replace("aws_", "").split("_")
        type_name = "".join(p.capitalize() for p in parts)
        return f"{type_name}{role.value.capitalize()}"

    def _generate_logs_statement(self, principal: ResourceNode) -> IAMStatement:
        func = (
            principal.config.get("function_name")
            or principal.config.get("FunctionName")
            or principal.original_name
        )
        base = (
            f"arn:{self.arn_builder.partition}:logs:{self.region}:"
            f"{self.account_id}:log-group:/aws/lambda/{func}"
        )
        return IAMStatement(
            sid="CloudWatchLogs",
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            resources=[base, f"{base}:*"],
        )

    def _check_cross_account(self, node: ResourceNode) -> None:
        """Warn about cross-account resources."""
        arn = node.arn or node.config.get("arn", "")
        if arn:
            parts = arn.split(":")
            if len(parts) > 4 and parts[4] and parts[4] != self.account_id:
                logger.warning(
                    f"CROSS-ACCOUNT: {arn} - May need resource policy on target account"
                )

    def generate_terraform_output(
        self,
        policies: list[IAMPolicy],
        role_name: str,
        create_role: bool = True,
        principal_type: str = "aws_lambda_function",
    ) -> str:
        """Generate complete Terraform module for all policies."""
        if len(policies) == 1:
            return policies[0].to_terraform_module(
                role_name, create_role, principal_type
            )

        # Multiple policies - attach all to same role
        parts = []

        if create_role:
            service = IAMPolicy.SERVICE_PRINCIPAL_MAP.get(
                principal_type, "lambda.amazonaws.com"
            )
            safe_role = re.sub(r"[^a-zA-Z0-9_]", "_", role_name.lower())
            parts.append(
                f'''
resource "aws_iam_role" "{safe_role}" {{
  name = "{role_name}"
  assume_role_policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [{{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {{ Service = "{service}" }}
    }}]
  }})
}}
'''
            )

        for policy in policies:
            parts.append(policy.to_terraform())
            safe_policy = re.sub(r"[^a-zA-Z0-9_]", "_", policy.name.lower())
            role_ref = (
                f"aws_iam_role.{safe_role}.name" if create_role else f'"{role_name}"'
            )
            parts.append(
                f'''
resource "aws_iam_role_policy_attachment" "{safe_policy}_attach" {{
  role       = {role_ref}
  policy_arn = aws_iam_policy.{safe_policy}.arn
}}
'''
            )

        return "\n".join(parts)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PolicyScope",
    "AccessRole",
    "ResourceBoundary",
    "TraversalController",
    "IntentAwareActionMapper",
    "ARNBuilder",
    "SafeResourceCompressor",
    "IAMStatement",
    "IAMPolicy",
    "PolicyOptimizer",
    "BaselinePolicyGenerator",
    "GraphAwareIAMGenerator",
]
