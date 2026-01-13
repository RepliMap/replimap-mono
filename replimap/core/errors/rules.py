"""
Service-specific rules for AWS error handling and circuit breaker isolation.

This module defines which services are global vs regional, and critically,
implements the S3 hybrid strategy where some operations are global
(Control Plane) and others are regional (Data Plane).

Design Decision - S3 Hybrid Strategy:
    S3 is unique in AWS - it has both global and regional APIs:

    Global (Control Plane):
    - ListBuckets: Lists all buckets in the account (global operation)
    - GetBucketLocation: Returns bucket region (must work from any endpoint)
    - CreateBucket: Creates bucket (though specifies region)

    Regional (Data Plane):
    - ListObjectsV2: Lists objects in a bucket (region-specific)
    - GetObject, PutObject: Object operations (region-specific)
    - All bucket configuration APIs (region-specific)

    Impact of incorrect classification:
    - If we treat all S3 as global: us-east-1 outage opens circuit,
      blocking access to healthy eu-west-1 buckets -> cascading failure
    - If we treat all S3 as regional: ListBuckets failures aren't
      properly isolated -> unnecessary errors

Example:
    >>> ServiceSpecificRules.is_global_operation('s3', 'ListBuckets')
    True
    >>> ServiceSpecificRules.is_global_operation('s3', 'ListObjectsV2')
    False
    >>> ServiceSpecificRules.get_circuit_breaker_key('s3', 'us-east-1', 'ListBuckets')
    's3:global'
    >>> ServiceSpecificRules.get_circuit_breaker_key('s3', 'us-east-1', 'ListObjectsV2')
    's3:us-east-1'
"""

from __future__ import annotations

import logging
from typing import ClassVar

logger = logging.getLogger(__name__)


class ServiceSpecificRules:
    """
    Service-specific rules for error handling and circuit breaker isolation.

    This class provides:
    1. Global vs Regional service classification
    2. S3 hybrid strategy (per-operation classification)
    3. Service-specific error codes
    4. Recommended rate limits
    """

    # ═══════════════════════════════════════════════════════════════════════
    # GLOBAL VS REGIONAL SERVICE CLASSIFICATION
    # ═══════════════════════════════════════════════════════════════════════

    # Services where ALL operations are global
    FULLY_GLOBAL_SERVICES: ClassVar[set[str]] = {
        "iam",  # Identity (global)
        "sts",  # Security Token Service (global endpoints exist)
        "route53",  # DNS (global)
        "cloudfront",  # CDN (global)
        "waf",  # Web Application Firewall (global)
        "wafv2",  # WAF v2 (global for CloudFront)
        "organizations",  # AWS Organizations (global)
        "account",  # Account management (global)
        "budgets",  # Budgets (global)
        "ce",  # Cost Explorer (global)
        "cur",  # Cost and Usage Reports (global)
        "globalaccelerator",  # Global Accelerator (global)
        "shield",  # Shield (global)
    }

    # ═══════════════════════════════════════════════════════════════════════
    # S3 HYBRID STRATEGY
    # ═══════════════════════════════════════════════════════════════════════

    # S3 Control Plane operations (global)
    S3_GLOBAL_OPERATIONS: ClassVar[set[str]] = {
        "ListBuckets",  # List all buckets in account
        "GetBucketLocation",  # Get bucket's region
        "CreateBucket",  # Create bucket (global endpoint)
    }

    # S3 Data Plane operations (regional)
    # This is a non-exhaustive list for documentation; any operation NOT in
    # S3_GLOBAL_OPERATIONS is treated as regional
    S3_REGIONAL_OPERATIONS: ClassVar[set[str]] = {
        # Object operations
        "ListObjectsV2",
        "ListObjects",
        "GetObject",
        "PutObject",
        "DeleteObject",
        "DeleteObjects",
        "CopyObject",
        "HeadObject",
        "GetObjectAcl",
        "PutObjectAcl",
        "GetObjectTagging",
        "PutObjectTagging",
        # Multipart upload
        "CreateMultipartUpload",
        "UploadPart",
        "CompleteMultipartUpload",
        "AbortMultipartUpload",
        "ListParts",
        "ListMultipartUploads",
        # Bucket configuration (region-specific)
        "GetBucketPolicy",
        "PutBucketPolicy",
        "DeleteBucketPolicy",
        "GetBucketAcl",
        "PutBucketAcl",
        "GetBucketCors",
        "PutBucketCors",
        "DeleteBucketCors",
        "GetBucketVersioning",
        "PutBucketVersioning",
        "GetBucketEncryption",
        "PutBucketEncryption",
        "GetBucketTagging",
        "PutBucketTagging",
        "DeleteBucketTagging",
        "GetBucketLogging",
        "PutBucketLogging",
        "GetBucketNotification",
        "PutBucketNotification",
        "GetBucketReplication",
        "PutBucketReplication",
        "DeleteBucketReplication",
        "GetBucketLifecycle",
        "PutBucketLifecycle",
        "DeleteBucketLifecycle",
        "GetBucketWebsite",
        "PutBucketWebsite",
        "DeleteBucketWebsite",
        "DeleteBucket",  # Must be called in bucket's region
    }

    # ═══════════════════════════════════════════════════════════════════════
    # SERVICE-SPECIFIC ERROR CODES
    # ═══════════════════════════════════════════════════════════════════════

    # Additional retryable errors per service (beyond global list)
    SERVICE_RETRYABLE_ERRORS: ClassVar[dict[str, set[str]]] = {
        "s3": {
            "SlowDown",  # S3 rate limiting
            "ServiceUnavailable",
            "503",  # Sometimes returned as HTTP code string
        },
        "dynamodb": {
            "ProvisionedThroughputExceededException",
            "InternalServerError",
            "TransactionConflictException",
            "TransactionCanceledException",  # Sometimes transient
        },
        "lambda": {
            "TooManyRequestsException",
            "EC2ThrottledException",
            "ENILimitReachedException",  # VPC ENI limits
        },
        "sqs": {
            "OverLimit",
            "KmsThrottled",
        },
        "kinesis": {
            "ProvisionedThroughputExceededException",
            "InternalFailure",
        },
        "elasticache": {
            "InsufficientCacheClusterCapacity",  # Sometimes transient
        },
    }

    # Service-specific fatal errors (beyond global list)
    SERVICE_FATAL_ERRORS: ClassVar[dict[str, set[str]]] = {
        "iam": {
            "NoSuchEntity",
            "EntityAlreadyExists",
            "DeleteConflict",
            "MalformedPolicyDocument",
        },
        "s3": {
            "NoSuchBucket",
            "NoSuchKey",
            "NoSuchUpload",
            "BucketAlreadyExists",
            "BucketAlreadyOwnedByYou",
            "BucketNotEmpty",
        },
        "dynamodb": {
            "TableNotFoundException",
            "TableAlreadyExistsException",
            "ConditionalCheckFailedException",
            "TransactionCanceledException",  # Usually indicates conflict
        },
        "lambda": {
            "FunctionNotFoundException",
            "ResourceConflictException",
            "CodeStorageExceededException",
        },
        "ec2": {
            "InvalidInstanceID.NotFound",
            "InvalidAMIID.NotFound",
            "InvalidKeyPair.NotFound",
            "InvalidGroup.NotFound",
        },
    }

    # ═══════════════════════════════════════════════════════════════════════
    # RECOMMENDED RATE LIMITS (requests per second)
    # ═══════════════════════════════════════════════════════════════════════

    RECOMMENDED_RATE_LIMITS: ClassVar[dict[str, float]] = {
        "ec2": 20.0,  # EC2 API is generous
        "rds": 10.0,  # RDS has lower limits
        "iam": 5.0,  # IAM is strict
        "s3": 10.0,  # S3 control plane
        "sts": 20.0,  # STS is fairly generous
        "dynamodb": 25.0,  # DynamoDB describe operations
        "lambda": 10.0,  # Lambda management API
        "cloudwatch": 15.0,  # CloudWatch (not Logs)
        "logs": 10.0,  # CloudWatch Logs
        "sqs": 10.0,  # SQS management
        "sns": 10.0,  # SNS management
        "elasticache": 10.0,  # ElastiCache
        "efs": 10.0,  # EFS
        "cloudformation": 5.0,  # CFN is slow, be conservative
        "route53": 5.0,  # Route53 has strict limits
        "secretsmanager": 10.0,  # Secrets Manager
        "ssm": 10.0,  # Systems Manager
    }

    DEFAULT_RATE_LIMIT: ClassVar[float] = 10.0

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    @classmethod
    def is_global_operation(
        cls,
        service_name: str,
        operation_name: str,
    ) -> bool:
        """
        Determine if an operation should use global circuit breaker isolation.

        Args:
            service_name: AWS service name (e.g., 's3', 'ec2')
            operation_name: API operation name (e.g., 'ListBuckets', 'DescribeInstances')

        Returns:
            True if this operation should use a single global circuit breaker,
            False if it should use per-region circuit breakers.

        Examples:
            >>> ServiceSpecificRules.is_global_operation('iam', 'GetUser')
            True   # IAM is fully global

            >>> ServiceSpecificRules.is_global_operation('s3', 'ListBuckets')
            True   # S3 ListBuckets is global (Control Plane)

            >>> ServiceSpecificRules.is_global_operation('s3', 'ListObjectsV2')
            False  # S3 ListObjects is regional (Data Plane)

            >>> ServiceSpecificRules.is_global_operation('ec2', 'DescribeInstances')
            False  # EC2 is fully regional
        """
        service = service_name.lower()

        # Fully global services
        if service in cls.FULLY_GLOBAL_SERVICES:
            return True

        # S3 hybrid strategy
        if service == "s3":
            if operation_name in cls.S3_GLOBAL_OPERATIONS:
                return True
            # All other S3 operations are regional
            if operation_name not in cls.S3_REGIONAL_OPERATIONS:
                # Unknown operation - log and default to regional (conservative)
                logger.debug(
                    f"Unknown S3 operation '{operation_name}', treating as regional"
                )
            return False

        # All other services are regional
        return False

    @classmethod
    def get_circuit_breaker_key(
        cls,
        service_name: str,
        region: str,
        operation_name: str,
    ) -> str:
        """
        Generate the circuit breaker key for a service/region/operation.

        Args:
            service_name: AWS service name
            region: AWS region
            operation_name: API operation name

        Returns:
            Circuit breaker key string.

        Examples:
            >>> ServiceSpecificRules.get_circuit_breaker_key('iam', 'us-east-1', 'GetUser')
            'iam:global'

            >>> ServiceSpecificRules.get_circuit_breaker_key('s3', 'us-east-1', 'ListBuckets')
            's3:global'

            >>> ServiceSpecificRules.get_circuit_breaker_key('s3', 'us-east-1', 'ListObjectsV2')
            's3:us-east-1'

            >>> ServiceSpecificRules.get_circuit_breaker_key('ec2', 'eu-west-1', 'DescribeInstances')
            'ec2:eu-west-1'
        """
        service = service_name.lower()

        if cls.is_global_operation(service_name, operation_name):
            return f"{service}:global"
        else:
            return f"{service}:{region}"

    @classmethod
    def get_service_retryable_errors(cls, service_name: str) -> set[str]:
        """Get service-specific retryable errors (in addition to global list)."""
        return cls.SERVICE_RETRYABLE_ERRORS.get(service_name.lower(), set())

    @classmethod
    def get_service_fatal_errors(cls, service_name: str) -> set[str]:
        """Get service-specific fatal errors (in addition to global list)."""
        return cls.SERVICE_FATAL_ERRORS.get(service_name.lower(), set())

    @classmethod
    def get_rate_limit(cls, service_name: str) -> float:
        """
        Get recommended rate limit for a service.

        Args:
            service_name: AWS service name

        Returns:
            Requests per second (float)
        """
        return cls.RECOMMENDED_RATE_LIMITS.get(
            service_name.lower(), cls.DEFAULT_RATE_LIMIT
        )
