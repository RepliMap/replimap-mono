"""
Context-aware AWS error classifier.

This module provides intelligent error classification that considers:
- Error code (what happened)
- Service (different services have different error semantics)
- Operation type (list vs describe vs mutate)
- Consecutive failures (for backoff calculation)

Key Design Decisions:

1. Fatal Errors Don't Trip Circuit Breaker:
   AccessDenied is a configuration problem, not a service health problem.
   If we count it toward circuit breaker, a single IAM misconfiguration
   could prevent scanning of healthy resources.

2. ResourceNotFound Gets One Retry:
   After a list operation, describe may fail due to eventual consistency.
   We give one retry before treating as "resource deleted".

3. Unknown Errors Default to Retry:
   It's better to retry a non-retryable error (waste some time) than to
   fail on a retryable error (lose data).

4. S3 SlowDown Needs Longer Backoff:
   S3 rate limiting is aggressive. Standard 1s backoff isn't enough;
   we use 3s base delay for SlowDown errors.
"""

from __future__ import annotations

import logging
import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from replimap.core.resilience.errors.loader import BotocoreErrorLoader
from replimap.core.resilience.errors.rules import ServiceSpecificRules

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ErrorAction(Enum):
    """
    Action to take after error classification.

    RETRY: Retry the operation with standard exponential backoff.
    FAIL: Do not retry; propagate the error immediately.
    IGNORE: Silently ignore; used for deleted resources.
    BACKOFF: Retry with extended backoff (for throttling).
    """

    RETRY = auto()
    FAIL = auto()
    IGNORE = auto()
    BACKOFF = auto()


@dataclass(frozen=True)
class ErrorClassification:
    """
    Result of error classification.

    Attributes:
        action: What action to take (RETRY, FAIL, IGNORE, BACKOFF)
        should_count_for_circuit: Whether this error should count toward
            circuit breaker failure threshold. CRITICAL: False for fatal
            errors like AccessDenied.
        suggested_delay_ms: Recommended delay before retry (0 if no retry).
        reason: Human-readable explanation for logging/debugging.
        aws_request_id: AWS request ID if available (for support tickets).
    """

    action: ErrorAction
    should_count_for_circuit: bool
    suggested_delay_ms: int = 0
    reason: str = ""
    aws_request_id: str | None = None


@dataclass
class ErrorContext:
    """
    Context about where the error occurred.

    Attributes:
        service_name: AWS service (e.g., 's3', 'ec2')
        region: AWS region (e.g., 'us-east-1')
        operation_name: API operation (e.g., 'DescribeInstances')
        resource_id: Specific resource being accessed (if known)
        is_list_operation: True if this is a list/scan operation
        is_describe_operation: True if this describes a specific resource
        consecutive_failures: Number of consecutive failures (for backoff)
    """

    service_name: str
    region: str
    operation_name: str
    resource_id: str | None = None
    is_list_operation: bool = False
    is_describe_operation: bool = False
    consecutive_failures: int = 0


class ErrorClassifier:
    """
    Context-aware AWS error classifier.

    Usage:
        classifier = ErrorClassifier()

        context = ErrorContext(
            service_name='dynamodb',
            region='us-east-1',
            operation_name='DescribeTable',
            resource_id='my-table',
            is_describe_operation=True,
            consecutive_failures=0,
        )

        try:
            await client.describe_table(TableName='my-table')
        except ClientError as e:
            classification = classifier.classify(e, context)

            if classification.action == ErrorAction.RETRY:
                await asyncio.sleep(classification.suggested_delay_ms / 1000)
                # retry...
            elif classification.action == ErrorAction.FAIL:
                raise
            elif classification.action == ErrorAction.IGNORE:
                # Remove resource from graph
                graph.remove_node(context.resource_id)
    """

    # Error codes that indicate resource not found
    RESOURCE_NOT_FOUND_CODES: frozenset[str] = frozenset(
        {
            "ResourceNotFoundException",
            "NoSuchEntity",
            "NoSuchBucket",
            "NoSuchKey",
            "NoSuchUpload",
            "NoSuchVersion",
            "TableNotFoundException",
            "FunctionNotFoundException",
            "StreamNotFoundException",
            "EntityNotFoundException",
            "NotFoundException",
            "InvalidInstanceID.NotFound",
            "InvalidAMIID.NotFound",
        }
    )

    # Error codes that indicate throttling (need longer backoff)
    THROTTLING_CODES: frozenset[str] = frozenset(
        {
            "Throttling",
            "ThrottlingException",
            "RequestLimitExceeded",
            "TooManyRequestsException",
            "ProvisionedThroughputExceededException",
            "SlowDown",
            "EC2ThrottledException",
            "BandwidthLimitExceeded",
        }
    )

    def __init__(self) -> None:
        """Initialize classifier with loaded error code sets."""
        self._retryable = BotocoreErrorLoader.get_retryable_errors()
        self._fatal = BotocoreErrorLoader.get_fatal_errors()

    def classify(
        self,
        error: Exception,
        context: ErrorContext,
    ) -> ErrorClassification:
        """
        Classify an error and determine the appropriate action.

        Args:
            error: The caught exception
            context: Context about where the error occurred

        Returns:
            ErrorClassification with action and metadata
        """
        # Extract AWS request ID for debugging
        aws_request_id = self._extract_request_id(error)

        # Handle connection/network errors (not ClientError)
        if self._is_connection_error(error):
            return ErrorClassification(
                action=ErrorAction.RETRY,
                should_count_for_circuit=True,
                suggested_delay_ms=self._calculate_delay(context, "ConnectionError"),
                reason=f"Connection error: {type(error).__name__}",
                aws_request_id=aws_request_id,
            )

        # Handle non-ClientError exceptions
        if not self._is_client_error(error):
            return ErrorClassification(
                action=ErrorAction.RETRY,
                should_count_for_circuit=True,
                suggested_delay_ms=self._calculate_delay(context, "Unknown"),
                reason=f"Non-ClientError: {type(error).__name__}",
                aws_request_id=aws_request_id,
            )

        # Extract error code from ClientError
        error_code = self._extract_error_code(error)

        # Special handling: ResourceNotFound
        if error_code in self.RESOURCE_NOT_FOUND_CODES:
            return self._handle_resource_not_found(error_code, context, aws_request_id)

        # Special handling: Throttling (use BACKOFF, not RETRY)
        if error_code in self.THROTTLING_CODES:
            return self._handle_throttling(error_code, context, aws_request_id)

        # Check service-specific errors
        service_retryable = ServiceSpecificRules.get_service_retryable_errors(
            context.service_name
        )
        if error_code in service_retryable:
            return ErrorClassification(
                action=ErrorAction.RETRY,
                should_count_for_circuit=True,
                suggested_delay_ms=self._calculate_delay(context, error_code),
                reason=f"Service-specific retryable: {error_code}",
                aws_request_id=aws_request_id,
            )

        service_fatal = ServiceSpecificRules.get_service_fatal_errors(
            context.service_name
        )
        if error_code in service_fatal:
            return ErrorClassification(
                action=ErrorAction.FAIL,
                should_count_for_circuit=False,  # KEY: Fatal doesn't trip circuit
                suggested_delay_ms=0,
                reason=f"Service-specific fatal: {error_code}",
                aws_request_id=aws_request_id,
            )

        # Check global fatal errors
        if error_code in self._fatal:
            return ErrorClassification(
                action=ErrorAction.FAIL,
                should_count_for_circuit=False,  # KEY: Fatal doesn't trip circuit
                suggested_delay_ms=0,
                reason=f"Fatal error: {error_code}",
                aws_request_id=aws_request_id,
            )

        # Check global retryable errors
        if error_code in self._retryable:
            return ErrorClassification(
                action=ErrorAction.RETRY,
                should_count_for_circuit=True,
                suggested_delay_ms=self._calculate_delay(context, error_code),
                reason=f"Retryable error: {error_code}",
                aws_request_id=aws_request_id,
            )

        # Unknown error - default to RETRY (conservative)
        logger.warning(
            f"Unknown error code '{error_code}' for "
            f"{context.service_name}:{context.operation_name}. "
            f"Treating as retryable. Please update error classification. "
            f"Request ID: {aws_request_id}"
        )
        return ErrorClassification(
            action=ErrorAction.RETRY,
            should_count_for_circuit=True,
            suggested_delay_ms=self._calculate_delay(context, error_code),
            reason=f"Unknown error (conservative retry): {error_code}",
            aws_request_id=aws_request_id,
        )

    def _handle_resource_not_found(
        self,
        error_code: str,
        context: ErrorContext,
        aws_request_id: str | None,
    ) -> ErrorClassification:
        """
        Handle ResourceNotFound errors with eventual consistency awareness.

        Strategy:
        - On describe operation with resource_id: Give 1 retry for eventual consistency
        - After 1 retry: Treat as IGNORE (remove from graph)
        - On other operations: Treat as FAIL
        """
        if context.is_describe_operation and context.resource_id:
            if context.consecutive_failures == 0:
                # First failure - might be eventual consistency
                return ErrorClassification(
                    action=ErrorAction.RETRY,
                    should_count_for_circuit=False,  # Don't penalize for EC
                    suggested_delay_ms=500,  # Short delay for EC
                    reason="ResourceNotFound on describe, retry for eventual consistency",
                    aws_request_id=aws_request_id,
                )
            else:
                # Second failure - resource is really gone
                logger.info(
                    f"Resource {context.resource_id} not found after retry, "
                    f"treating as deleted"
                )
                return ErrorClassification(
                    action=ErrorAction.IGNORE,
                    should_count_for_circuit=False,
                    suggested_delay_ms=0,
                    reason=f"Resource {context.resource_id} confirmed deleted",
                    aws_request_id=aws_request_id,
                )

        # Not a describe operation - this is a real error
        return ErrorClassification(
            action=ErrorAction.FAIL,
            should_count_for_circuit=False,
            suggested_delay_ms=0,
            reason=f"ResourceNotFound: {error_code}",
            aws_request_id=aws_request_id,
        )

    def _handle_throttling(
        self,
        error_code: str,
        context: ErrorContext,
        aws_request_id: str | None,
    ) -> ErrorClassification:
        """
        Handle throttling errors with extended backoff.

        S3 SlowDown needs longer delay than other throttling errors.
        """
        return ErrorClassification(
            action=ErrorAction.BACKOFF,
            should_count_for_circuit=True,  # Throttling counts toward circuit
            suggested_delay_ms=self._calculate_delay(context, error_code),
            reason=f"Throttling: {error_code}",
            aws_request_id=aws_request_id,
        )

    def _calculate_delay(self, context: ErrorContext, error_code: str) -> int:
        """
        Calculate backoff delay with exponential backoff and jitter.

        Formula: base_delay * 2^attempt * jitter

        S3 SlowDown uses 3s base delay (aggressive rate limiting).
        Other errors use 1s base delay.
        Max delay capped at 64s.
        """
        # Base delay depends on error type
        if error_code == "SlowDown":
            base_delay_ms = 3000  # S3 needs longer backoff
        elif error_code in self.THROTTLING_CODES:
            base_delay_ms = 2000  # Other throttling
        else:
            base_delay_ms = 1000  # Standard errors

        # Exponential backoff
        attempt = min(context.consecutive_failures, 6)  # Cap at 2^6 = 64x
        delay_ms = base_delay_ms * (2**attempt)

        # Cap maximum delay
        delay_ms = min(delay_ms, 64000)

        # Add jitter (+-20%) - not for cryptography, just for spreading out retries
        jitter = random.uniform(0.8, 1.2)  # noqa: S311
        delay_ms = int(delay_ms * jitter)

        return delay_ms

    @staticmethod
    def _is_connection_error(error: Exception) -> bool:
        """Check if error is a connection/network error."""
        try:
            from botocore.exceptions import (
                ConnectionError as BotocoreConnectionError,
            )
            from botocore.exceptions import (
                ConnectTimeoutError,
                EndpointConnectionError,
                ReadTimeoutError,
            )

            return isinstance(
                error,
                (
                    EndpointConnectionError,
                    BotocoreConnectionError,
                    ConnectTimeoutError,
                    ReadTimeoutError,
                    ConnectionError,
                    TimeoutError,
                ),
            )
        except ImportError:
            return isinstance(error, (ConnectionError, TimeoutError))

    @staticmethod
    def _is_client_error(error: Exception) -> bool:
        """Check if error is a botocore ClientError."""
        try:
            from botocore.exceptions import ClientError

            return isinstance(error, ClientError)
        except ImportError:
            return False

    @staticmethod
    def _extract_error_code(error: Exception) -> str:
        """Extract error code from ClientError."""
        try:
            return error.response.get("Error", {}).get("Code", "Unknown")  # type: ignore[union-attr]
        except AttributeError:
            return "Unknown"

    @staticmethod
    def _extract_request_id(error: Exception) -> str | None:
        """Extract AWS request ID from error for debugging."""
        try:
            return error.response.get("ResponseMetadata", {}).get("RequestId")  # type: ignore[union-attr]
        except AttributeError:
            return None
