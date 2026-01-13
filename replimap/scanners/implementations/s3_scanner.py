"""
Unified S3 Scanner with full resilience stack and hybrid strategy.

This scanner demonstrates the S3 hybrid strategy:
- ListBuckets uses global circuit breaker (Control Plane)
- GetBucketLocation uses global circuit breaker (Control Plane)
- Other operations use regional circuit breakers (Data Plane)

Uses UnifiedScannerBase for:
- Circuit breaker protection with S3 hybrid
- Rate limiting
- Retry with error classification
- Backpressure monitoring
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from replimap.core.errors.classifier import ErrorContext
from replimap.core.models import ResourceNode, ResourceType
from replimap.core.resilience.circuit_breaker import CircuitBreakerRegistry
from replimap.scanners.unified_base import ScanResult, UnifiedScannerBase

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


class UnifiedS3Scanner(UnifiedScannerBase):
    """
    Production-grade S3 scanner with hybrid circuit breaker strategy.

    Key design: S3 has both global and regional operations.
    - ListBuckets: Global (Control Plane) - single circuit breaker
    - GetBucketLocation: Global (Control Plane) - single circuit breaker
    - GetBucketPolicy, etc.: Regional (Data Plane) - per-region circuit breakers

    This prevents a single region's S3 issues from blocking bucket discovery.
    """

    service_name: ClassVar[str] = "s3"
    resource_types: ClassVar[list[str]] = [
        "aws_s3_bucket",
        "aws_s3_bucket_policy",
        "aws_s3_bucket_versioning",
        "aws_s3_bucket_lifecycle_configuration",
        "aws_s3_bucket_server_side_encryption_configuration",
    ]

    async def _do_scan(self, graph: GraphEngine) -> ScanResult:
        """
        Scan S3 buckets and their configurations.

        Strategy:
        1. List all buckets (global operation)
        2. For each bucket, get its region
        3. Only scan detailed config for buckets in our target region

        Args:
            graph: GraphEngine to populate

        Returns:
            ScanResult with statistics
        """
        result = ScanResult(scanner_name=self.__class__.__name__)

        async with await self._get_client() as client:
            # Step 1: List all buckets (GLOBAL operation)
            buckets = await self._list_buckets(client, result)

            # Step 2: Filter to buckets in our region and scan details
            for bucket in buckets:
                bucket_name = bucket["Name"]

                # Get bucket region (GLOBAL operation)
                bucket_region = await self._get_bucket_region(client, bucket_name, result)

                # Only process buckets in our target region
                if bucket_region != self.region:
                    logger.debug(
                        f"Skipping bucket {bucket_name} (in {bucket_region}, "
                        f"scanning {self.region})"
                    )
                    continue

                # Scan bucket details (REGIONAL operations)
                try:
                    await self._scan_bucket(client, bucket, graph, result)
                    result.resources_found += 1
                except Exception as e:
                    logger.warning(f"Failed to scan bucket {bucket_name}: {e}")
                    result.resources_failed += 1

        logger.info(
            f"S3 scan complete: {result.resources_found} buckets found in {self.region}, "
            f"{result.resources_failed} failed"
        )

        return result

    async def _list_buckets(
        self,
        client: Any,
        result: ScanResult,
    ) -> list[dict[str, Any]]:
        """
        List all S3 buckets (GLOBAL operation).

        Uses the global circuit breaker for S3:ListBuckets.
        """
        try:
            # This will use s3:global circuit breaker due to ServiceSpecificRules
            response = await self._call_api(
                client=client,
                method_name="list_buckets",
                operation_name="ListBuckets",  # Global operation
            )
            return response.get("Buckets", [])

        except Exception as e:
            logger.error(f"Failed to list S3 buckets: {e}")
            result.errors.append(f"ListBuckets error: {e}")
            return []

    async def _get_bucket_region(
        self,
        client: Any,
        bucket_name: str,
        result: ScanResult,
    ) -> str:
        """
        Get the region of a bucket (GLOBAL operation).

        Uses the global circuit breaker for S3:GetBucketLocation.
        """
        try:
            response = await self._call_api(
                client=client,
                method_name="get_bucket_location",
                operation_name="GetBucketLocation",  # Global operation
                Bucket=bucket_name,
            )

            # LocationConstraint is None for us-east-1
            location = response.get("LocationConstraint")
            if location is None:
                return "us-east-1"
            return location

        except Exception as e:
            logger.warning(f"Failed to get region for bucket {bucket_name}: {e}")
            # Default to current region on error
            return self.region

    async def _scan_bucket(
        self,
        client: Any,
        bucket: dict[str, Any],
        graph: GraphEngine,
        result: ScanResult,
    ) -> None:
        """
        Scan a single bucket's configuration (REGIONAL operations).

        These operations use regional circuit breakers.
        """
        bucket_name = bucket["Name"]

        # Build bucket config
        config: dict[str, Any] = {
            "Name": bucket_name,
            "CreationDate": bucket.get("CreationDate"),
        }

        # Get bucket policy (regional)
        policy = await self._get_bucket_policy(client, bucket_name)
        if policy:
            config["Policy"] = policy

        # Get versioning (regional)
        versioning = await self._get_bucket_versioning(client, bucket_name)
        if versioning:
            config["Versioning"] = versioning

        # Get encryption (regional)
        encryption = await self._get_bucket_encryption(client, bucket_name)
        if encryption:
            config["ServerSideEncryptionConfiguration"] = encryption

        # Get tags (regional)
        tags = await self._get_bucket_tags(client, bucket_name)

        # Create resource node
        node = ResourceNode(
            id=bucket_name,
            resource_type=ResourceType.S3_BUCKET,
            region=self.region,
            config=config,
            arn=f"arn:aws:s3:::{bucket_name}",
            tags=tags,
            dependencies=[],
            terraform_name=None,
            original_name=bucket_name,
            is_phantom=False,
            phantom_reason=None,
        )

        graph.add_resource(node)

    async def _get_bucket_policy(
        self,
        client: Any,
        bucket_name: str,
    ) -> str | None:
        """Get bucket policy (REGIONAL operation)."""
        try:
            response = await self._call_api(
                client=client,
                method_name="get_bucket_policy",
                operation_name="GetBucketPolicy",  # Regional
                Bucket=bucket_name,
            )
            return response.get("Policy")
        except Exception as e:
            # NoSuchBucketPolicy is expected for buckets without policies
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code != "NoSuchBucketPolicy":
                logger.debug(f"Failed to get policy for {bucket_name}: {e}")
            return None

    async def _get_bucket_versioning(
        self,
        client: Any,
        bucket_name: str,
    ) -> dict[str, Any] | None:
        """Get bucket versioning config (REGIONAL operation)."""
        try:
            response = await self._call_api(
                client=client,
                method_name="get_bucket_versioning",
                operation_name="GetBucketVersioning",  # Regional
                Bucket=bucket_name,
            )
            # Only return if versioning is configured
            if response.get("Status") or response.get("MFADelete"):
                return {
                    "Status": response.get("Status"),
                    "MFADelete": response.get("MFADelete"),
                }
            return None
        except Exception as e:
            logger.debug(f"Failed to get versioning for {bucket_name}: {e}")
            return None

    async def _get_bucket_encryption(
        self,
        client: Any,
        bucket_name: str,
    ) -> dict[str, Any] | None:
        """Get bucket encryption config (REGIONAL operation)."""
        try:
            response = await self._call_api(
                client=client,
                method_name="get_bucket_encryption",
                operation_name="GetBucketEncryption",  # Regional
                Bucket=bucket_name,
            )
            return response.get("ServerSideEncryptionConfiguration")
        except Exception as e:
            # ServerSideEncryptionConfigurationNotFoundError is expected
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if "ServerSideEncryptionConfigurationNotFoundError" not in error_code:
                logger.debug(f"Failed to get encryption for {bucket_name}: {e}")
            return None

    async def _get_bucket_tags(
        self,
        client: Any,
        bucket_name: str,
    ) -> dict[str, str]:
        """Get bucket tags (REGIONAL operation)."""
        try:
            response = await self._call_api(
                client=client,
                method_name="get_bucket_tagging",
                operation_name="GetBucketTagging",  # Regional
                Bucket=bucket_name,
            )
            tags: dict[str, str] = {}
            for tag in response.get("TagSet", []):
                key = tag.get("Key")
                value = tag.get("Value", "")
                if key:
                    tags[key] = value
            return tags
        except Exception as e:
            # NoSuchTagSet is expected for buckets without tags
            error_code = getattr(e, "response", {}).get("Error", {}).get("Code", "")
            if error_code != "NoSuchTagSet":
                logger.debug(f"Failed to get tags for {bucket_name}: {e}")
            return {}
