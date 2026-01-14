"""
Messaging Scanner for RepliMap Phase 2.

Scans SQS Queues and SNS Topics.
These resources provide asynchronous messaging infrastructure.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any, ClassVar

from botocore.exceptions import ClientError

from replimap.core.models import DependencyType, ResourceNode, ResourceType
from replimap.core.rate_limiter import rate_limited_paginate

from .base import BaseScanner, ScannerRegistry, parallel_process_items

if TYPE_CHECKING:
    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)


@ScannerRegistry.register
class SQSScanner(BaseScanner):
    """
    Scans SQS Queues.

    SQS Queues are standalone resources but may reference SNS topics
    or other AWS resources in their policies.
    """

    resource_types: ClassVar[list[str]] = [
        "aws_sqs_queue",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all SQS Queues and add to graph."""
        logger.info(f"Scanning SQS Queues in {self.region}...")

        try:
            sqs = self.get_client("sqs")
            self._scan_queues(sqs, graph)
        except ClientError as e:
            self._handle_aws_error(e, "SQS scanning")

    def _scan_queues(self, sqs: Any, graph: GraphEngine) -> None:
        """Scan all SQS Queues in the region."""
        logger.debug("Scanning SQS Queues...")

        # First, collect all queue URLs from pagination
        queue_urls: list[str] = []
        paginator = sqs.get_paginator("list_queues")
        for page in rate_limited_paginate("sqs", self.region)(paginator.paginate()):
            queue_urls.extend(page.get("QueueUrls", []))

        # Process queues in parallel (attribute/tag fetching is the bottleneck)
        results, failures = parallel_process_items(
            items=queue_urls,
            processor=lambda url: self._process_queue(url, sqs, graph),
            description="SQS Queues",
        )

        queue_count = sum(1 for r in results if r)
        logger.info(f"Scanned {queue_count} SQS Queues")

        if failures:
            for url, error in failures:
                logger.warning(f"Failed to process queue {url}: {error}")

    def _process_queue(self, queue_url: str, sqs: Any, graph: GraphEngine) -> bool:
        """Process a single SQS queue."""
        try:
            # Get queue attributes
            attrs_resp = sqs.get_queue_attributes(
                QueueUrl=queue_url,
                AttributeNames=["All"],
            )
            attrs = attrs_resp.get("Attributes", {})

            queue_arn = attrs.get("QueueArn", "")
            queue_name = queue_url.split("/")[-1]

            # Parse redrive policy if exists
            redrive_policy = {}
            if attrs.get("RedrivePolicy"):
                try:
                    redrive_policy = json.loads(attrs["RedrivePolicy"])
                except json.JSONDecodeError:
                    pass

            # Parse policy if exists
            policy = {}
            if attrs.get("Policy"):
                try:
                    policy = json.loads(attrs["Policy"])
                except json.JSONDecodeError:
                    pass

            # Get tags
            try:
                tags_resp = sqs.list_queue_tags(QueueUrl=queue_url)
                tags = tags_resp.get("Tags", {})
            except ClientError:
                tags = {}

            node = ResourceNode(
                id=queue_arn,
                resource_type=ResourceType.SQS_QUEUE,
                region=self.region,
                config={
                    "name": queue_name,
                    "url": queue_url,
                    "fifo_queue": queue_name.endswith(".fifo"),
                    "visibility_timeout_seconds": int(
                        attrs.get("VisibilityTimeout", 30)
                    ),
                    "message_retention_seconds": int(
                        attrs.get("MessageRetentionPeriod", 345600)
                    ),
                    "max_message_size": int(attrs.get("MaximumMessageSize", 262144)),
                    "delay_seconds": int(attrs.get("DelaySeconds", 0)),
                    "receive_wait_time_seconds": int(
                        attrs.get("ReceiveMessageWaitTimeSeconds", 0)
                    ),
                    "content_based_deduplication": attrs.get(
                        "ContentBasedDeduplication"
                    )
                    == "true",
                    "deduplication_scope": attrs.get("DeduplicationScope"),
                    "fifo_throughput_limit": attrs.get("FifoThroughputLimit"),
                    "kms_master_key_id": attrs.get("KmsMasterKeyId"),
                    "kms_data_key_reuse_period_seconds": int(
                        attrs.get("KmsDataKeyReusePeriodSeconds", 300)
                    )
                    if attrs.get("KmsDataKeyReusePeriodSeconds")
                    else None,
                    "sqs_managed_sse_enabled": attrs.get("SqsManagedSseEnabled")
                    == "true",
                    "redrive_policy": redrive_policy,
                    "policy": policy,
                },
                arn=queue_arn,
                tags=tags,
            )

            graph.add_resource(node)

            # Check for dead letter queue reference
            dlq_arn = redrive_policy.get("deadLetterTargetArn")
            if dlq_arn and graph.get_resource(dlq_arn):
                # This queue depends on its DLQ
                graph.add_dependency(queue_arn, dlq_arn, DependencyType.REFERENCES)

            logger.debug(f"Added SQS Queue: {queue_name}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AccessDenied":
                logger.warning(f"Access denied for queue: {queue_url}")
                return False
            raise


@ScannerRegistry.register
class SNSScanner(BaseScanner):
    """
    Scans SNS Topics.

    Note: Subscriptions are NOT scanned by default as they may contain
    sensitive email/phone information.
    """

    resource_types: ClassVar[list[str]] = [
        "aws_sns_topic",
    ]

    def scan(self, graph: GraphEngine) -> None:
        """Scan all SNS Topics and add to graph."""
        logger.info(f"Scanning SNS Topics in {self.region}...")

        try:
            sns = self.get_client("sns")
            self._scan_topics(sns, graph)
        except ClientError as e:
            self._handle_aws_error(e, "SNS scanning")

    def _scan_topics(self, sns: Any, graph: GraphEngine) -> None:
        """Scan all SNS Topics in the region."""
        logger.debug("Scanning SNS Topics...")

        # Collect all topics first
        topics_to_process: list[dict[str, Any]] = []
        paginator = sns.get_paginator("list_topics")
        for page in rate_limited_paginate("sns", self.region)(paginator.paginate()):
            topics_to_process.extend(page.get("Topics", []))

        if not topics_to_process:
            logger.debug("No SNS Topics found")
            return

        # Process topics in parallel (attribute/tag fetching is the bottleneck)
        results, failures = parallel_process_items(
            items=topics_to_process,
            processor=lambda topic: self._process_topic(topic, sns, graph),
            description="SNS Topics",
        )

        topic_count = sum(1 for r in results if r)
        logger.info(f"Scanned {topic_count} SNS Topics")

        if failures:
            for topic, error in failures:
                logger.warning(
                    f"Failed to process topic {topic.get('TopicArn')}: {error}"
                )

    def _process_topic(
        self, topic: dict[str, Any], sns: Any, graph: GraphEngine
    ) -> bool:
        """Process a single SNS Topic."""
        topic_arn = topic["TopicArn"]
        topic_name = topic_arn.split(":")[-1]

        try:
            # Get topic attributes
            attrs_resp = sns.get_topic_attributes(TopicArn=topic_arn)
            attrs = attrs_resp.get("Attributes", {})

            # Parse policy if exists
            policy = {}
            if attrs.get("Policy"):
                try:
                    policy = json.loads(attrs["Policy"])
                except json.JSONDecodeError:
                    pass

            # Get tags
            try:
                tags_resp = sns.list_tags_for_resource(ResourceArn=topic_arn)
                tags = {tag["Key"]: tag["Value"] for tag in tags_resp.get("Tags", [])}
            except ClientError:
                tags = {}

            # Check if FIFO
            is_fifo = topic_name.endswith(".fifo")

            node = ResourceNode(
                id=topic_arn,
                resource_type=ResourceType.SNS_TOPIC,
                region=self.region,
                config={
                    "name": topic_name,
                    "display_name": attrs.get("DisplayName"),
                    "fifo_topic": is_fifo,
                    "content_based_deduplication": attrs.get(
                        "ContentBasedDeduplication"
                    )
                    == "true"
                    if is_fifo
                    else None,
                    "kms_master_key_id": attrs.get("KmsMasterKeyId"),
                    "policy": policy,
                    "delivery_policy": attrs.get("DeliveryPolicy"),
                    "effective_delivery_policy": attrs.get("EffectiveDeliveryPolicy"),
                    "owner": attrs.get("Owner"),
                    "subscriptions_confirmed": int(
                        attrs.get("SubscriptionsConfirmed", 0)
                    ),
                    "subscriptions_pending": int(attrs.get("SubscriptionsPending", 0)),
                    "subscriptions_deleted": int(attrs.get("SubscriptionsDeleted", 0)),
                },
                arn=topic_arn,
                tags=tags,
            )

            graph.add_resource(node)
            logger.debug(f"Added SNS Topic: {topic_name}")
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "AuthorizationError":
                logger.warning(f"Authorization error for topic: {topic_arn}")
                return False
            raise
