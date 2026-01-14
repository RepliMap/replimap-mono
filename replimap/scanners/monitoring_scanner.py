"""
Monitoring Scanners for RepliMap.

Scans CloudWatch and related monitoring resources.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.rate_limiter import rate_limited_paginate
from replimap.scanners.base import BaseScanner, ScannerRegistry, parallel_process_items

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

        try:
            # First, collect all log groups from pagination
            log_groups_to_process: list[dict[str, Any]] = []
            paginator = logs.get_paginator("describe_log_groups")
            for page in rate_limited_paginate("cloudwatch", self.region)(
                paginator.paginate()
            ):
                log_groups_to_process.extend(page.get("logGroups", []))

            # Process log groups in parallel (tag fetching is the bottleneck)
            results, failures = parallel_process_items(
                items=log_groups_to_process,
                processor=lambda lg: self._process_log_group(lg, logs, graph),
                description="CloudWatch Log Groups",
            )

            log_group_count = sum(1 for r in results if r)
            logger.info(f"Scanned {log_group_count} CloudWatch Log Groups")

            if failures:
                for lg, error in failures:
                    logger.warning(
                        f"Failed to process log group {lg.get('logGroupName')}: {error}"
                    )

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


@ScannerRegistry.register
class CloudWatchMetricAlarmScanner(BaseScanner):
    """
    Scanner for CloudWatch Metric Alarms.

    Captures:
    - Alarm name (used as ID in TF state)
    - ARN
    - Metric configuration
    - Threshold and comparison
    - Actions
    - Tags
    """

    resource_types: ClassVar[list[str]] = ["aws_cloudwatch_metric_alarm"]

    # Alarms can reference SNS topics for actions
    depends_on_types: ClassVar[list[str]] = [
        "aws_sns_topic",
        "aws_autoscaling_group",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all CloudWatch Metric Alarms in the region."""
        logger.info(f"Scanning CloudWatch Metric Alarms in {self.region}...")

        cloudwatch = self.get_client("cloudwatch")

        try:
            # Collect all alarms first
            alarms_to_process: list[dict[str, Any]] = []
            paginator = cloudwatch.get_paginator("describe_alarms")
            for page in paginator.paginate(AlarmTypes=["MetricAlarm"]):
                alarms_to_process.extend(page.get("MetricAlarms", []))

            if not alarms_to_process:
                logger.info("No CloudWatch Metric Alarms found")
                return

            # Process alarms in parallel (tag fetching is the bottleneck)
            results, failures = parallel_process_items(
                items=alarms_to_process,
                processor=lambda alarm: self._process_alarm(alarm, cloudwatch, graph),
                description="CloudWatch Metric Alarms",
            )

            alarm_count = sum(1 for r in results if r)
            logger.info(f"Scanned {alarm_count} CloudWatch Metric Alarms")

            if failures:
                for alarm, error in failures:
                    logger.warning(
                        f"Failed to process alarm {alarm.get('AlarmName')}: {error}"
                    )

        except ClientError as e:
            self._handle_aws_error(e, "describe_alarms")

    def _process_alarm(
        self,
        alarm: dict[str, Any],
        cloudwatch_client: Any,
        graph: GraphEngine,
    ) -> bool:
        """Process a single CloudWatch Metric Alarm."""
        alarm_name = alarm.get("AlarmName", "")
        alarm_arn = alarm.get("AlarmArn", "")

        if not alarm_name:
            return False

        # Get tags for this alarm
        tags = {}
        try:
            tags_response = cloudwatch_client.list_tags_for_resource(
                ResourceARN=alarm_arn
            )
            for tag in tags_response.get("Tags", []):
                tags[tag["Key"]] = tag["Value"]
        except ClientError as e:
            logger.debug(f"Could not get tags for alarm {alarm_name}: {e}")

        # Extract dimension info
        dimensions = []
        for dim in alarm.get("Dimensions", []):
            dimensions.append({"name": dim.get("Name"), "value": dim.get("Value")})

        # Build config matching TF schema
        config = {
            "alarm_name": alarm_name,
            "comparison_operator": alarm.get("ComparisonOperator"),
            "evaluation_periods": alarm.get("EvaluationPeriods"),
            "metric_name": alarm.get("MetricName"),
            "namespace": alarm.get("Namespace"),
            "period": alarm.get("Period"),
            "statistic": alarm.get("Statistic"),
            "threshold": alarm.get("Threshold"),
            "alarm_description": alarm.get("AlarmDescription"),
            "actions_enabled": alarm.get("ActionsEnabled"),
            "alarm_actions": alarm.get("AlarmActions", []),
            "ok_actions": alarm.get("OKActions", []),
            "insufficient_data_actions": alarm.get("InsufficientDataActions", []),
            "dimensions": dimensions,
            "treat_missing_data": alarm.get("TreatMissingData"),
            "datapoints_to_alarm": alarm.get("DatapointsToAlarm"),
            "extended_statistic": alarm.get("ExtendedStatistic"),
            "unit": alarm.get("Unit"),
            "state_value": alarm.get("StateValue"),
        }

        # Use alarm name as ID (matches TF state format)
        node = ResourceNode(
            id=alarm_name,
            resource_type=ResourceType.CLOUDWATCH_METRIC_ALARM,
            region=self.region,
            config=config,
            arn=alarm_arn,
            tags=tags,
        )

        graph.add_resource(node)

        # Establish dependencies to SNS topics
        for action_arn in alarm.get("AlarmActions", []):
            if ":sns:" in action_arn:
                # Extract topic name from ARN
                topic_name = action_arn.split(":")[-1]
                if graph.get_resource(topic_name):
                    graph.add_dependency(alarm_name, topic_name, DependencyType.USES)

        logger.debug(f"Added CloudWatch Metric Alarm: {alarm_name}")
        return True
