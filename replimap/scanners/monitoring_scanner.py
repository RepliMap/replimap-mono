"""
Monitoring Scanners for RepliMap.

Scans CloudWatch and related monitoring resources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import ResourceNode, ResourceType
from replimap.scanners.base import BaseScanner, ScannerRegistry

if TYPE_CHECKING:
    from replimap.core import GraphEngine

logger = logging.getLogger(__name__)


@ScannerRegistry.register
class CloudWatchLogGroupScanner(BaseScanner):
    """
    Scanner for CloudWatch Log Groups.

    Captures:
    - Log group name (used as ID in TF state)
    - Retention policy
    - KMS encryption key
    - Tags
    """

    resource_types: ClassVar[list[str]] = ["aws_cloudwatch_log_group"]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all CloudWatch Log Groups in the region."""
        logger.info(f"Scanning CloudWatch Log Groups in {self.region}...")

        logs = self.get_client("logs")
        log_group_count = 0

        try:
            paginator = logs.get_paginator("describe_log_groups")
            for page in paginator.paginate():
                for log_group in page.get("logGroups", []):
                    if self._process_log_group(log_group, logs, graph):
                        log_group_count += 1

            logger.info(f"Scanned {log_group_count} CloudWatch Log Groups")

        except ClientError as e:
            self._handle_aws_error(e, "describe_log_groups")

    def _process_log_group(
        self,
        log_group: dict,
        logs_client: object,
        graph: GraphEngine,
    ) -> bool:
        """Process a single CloudWatch Log Group."""
        log_group_name = log_group.get("logGroupName", "")
        log_group_arn = log_group.get("arn", "")

        if not log_group_name:
            return False

        # Get tags for this log group
        tags = {}
        try:
            # Note: list_tags_log_group is not paginated
            tags_response = logs_client.list_tags_log_group(logGroupName=log_group_name)
            tags = tags_response.get("tags", {})
        except ClientError as e:
            logger.debug(f"Could not get tags for log group {log_group_name}: {e}")

        # Build config
        config = {
            "name": log_group_name,
            "retention_in_days": log_group.get("retentionInDays"),
            "kms_key_id": log_group.get("kmsKeyId"),
            "stored_bytes": log_group.get("storedBytes"),
            "metric_filter_count": log_group.get("metricFilterCount"),
            "log_group_class": log_group.get("logGroupClass"),
        }

        # Use log group name as ID (matches TF state format)
        node = ResourceNode(
            id=log_group_name,
            resource_type=ResourceType.CLOUDWATCH_LOG_GROUP,
            region=self.region,
            config=config,
            arn=log_group_arn,
            tags=tags,
        )

        graph.add_resource(node)
        logger.debug(f"Added CloudWatch Log Group: {log_group_name}")
        return True
