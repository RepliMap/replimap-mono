"""
Unified scanner base class with full resilience stack.

This base class provides:
1. Circuit breaker integration (per-service/region)
2. Rate limiting (configurable per-service)
3. Global concurrency control (prevents OOM)
4. Backpressure monitoring
5. Retry with error classification

All new scanners MUST inherit from this class.
Legacy scanners can be wrapped with LegacyScannerAdapter.

Design Principles:
- Single responsibility: One scanner, one AWS service
- Fail fast: Don't waste time on known-bad circuits
- Graceful degradation: Continue scanning healthy regions
- Observable: Log everything needed for debugging
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

from replimap.core.errors.classifier import (
    ErrorAction,
    ErrorClassifier,
    ErrorContext,
)
from replimap.core.errors.rules import ServiceSpecificRules
from replimap.core.resilience.circuit_breaker import (
    BackpressureMonitor,
    CircuitBreakerRegistry,
    CircuitOpenError,
)

if TYPE_CHECKING:
    from replimap.core.graph_engine import GraphEngine

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result of a scanner run."""

    scanner_name: str
    resources_found: int = 0
    resources_failed: int = 0
    retries: int = 0
    errors: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    circuit_open: bool = False
    skipped_regions: list[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.resources_found + self.resources_failed
        if total == 0:
            return 1.0
        return self.resources_found / total

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "scanner_name": self.scanner_name,
            "resources_found": self.resources_found,
            "resources_failed": self.resources_failed,
            "retries": self.retries,
            "errors": self.errors,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
            "circuit_open": self.circuit_open,
            "skipped_regions": self.skipped_regions,
        }


class UnifiedScannerBase(ABC):
    """
    Unified base class for all AWS scanners.

    Features:
    - Circuit breaker integration
    - Rate limiting
    - Global concurrency control
    - Backpressure monitoring
    - Retry with error classification

    Subclasses must:
    1. Set service_name class variable
    2. Set resource_types class variable
    3. Implement _do_scan() method

    Example:
        class EC2Scanner(UnifiedScannerBase):
            service_name = "ec2"
            resource_types = ["aws_instance", "aws_ami"]

            async def _do_scan(self, graph: GraphEngine) -> ScanResult:
                result = ScanResult(scanner_name=self.__class__.__name__)
                instances = await self._paginate(
                    client=self._client,
                    operation_name="describe_instances",
                    method_name="describe_instances",
                    result_key="Reservations",
                )
                # Process instances...
                return result
    """

    # ═══════════════════════════════════════════════════════════════════════
    # CLASS VARIABLES (Override in subclasses)
    # ═══════════════════════════════════════════════════════════════════════

    service_name: ClassVar[str] = ""
    resource_types: ClassVar[list[str]] = []
    rate_limit: ClassVar[float | None] = None  # Uses ServiceSpecificRules if None

    # ═══════════════════════════════════════════════════════════════════════
    # GLOBAL CONCURRENCY CONTROL
    # ═══════════════════════════════════════════════════════════════════════

    _global_semaphore: ClassVar[asyncio.Semaphore | None] = None
    _max_concurrent_operations: ClassVar[int] = 50

    @classmethod
    def _get_global_semaphore(cls) -> asyncio.Semaphore:
        """Get or create global semaphore (lazy initialization)."""
        if cls._global_semaphore is None:
            cls._global_semaphore = asyncio.Semaphore(cls._max_concurrent_operations)
        return cls._global_semaphore

    @classmethod
    def set_max_concurrency(cls, max_concurrent: int) -> None:
        """Set maximum concurrent operations across all scanners."""
        cls._max_concurrent_operations = max_concurrent
        cls._global_semaphore = asyncio.Semaphore(max_concurrent)

    # ═══════════════════════════════════════════════════════════════════════
    # INSTANCE INITIALIZATION
    # ═══════════════════════════════════════════════════════════════════════

    def __init__(
        self,
        session: Any,  # AioSession or boto3 Session
        region: str,
        account_id: str,
        error_classifier: ErrorClassifier | None = None,
    ) -> None:
        """
        Initialize scanner.

        Args:
            session: aiobotocore or boto3 session
            region: AWS region to scan
            account_id: AWS account ID
            error_classifier: Optional custom error classifier
        """
        self.session = session
        self.region = region
        self.account_id = account_id
        self._classifier = error_classifier or ErrorClassifier()
        self._rate_limiter = self._create_rate_limiter()
        self._client: Any = None

    def _create_rate_limiter(self) -> asyncio.Semaphore:
        """Create rate limiter based on service limits."""
        rate = self.rate_limit or ServiceSpecificRules.get_rate_limit(self.service_name)
        # Simple token bucket: allow 'rate' concurrent requests
        return asyncio.Semaphore(int(rate))

    # ═══════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════

    async def scan(self, graph: GraphEngine) -> ScanResult:
        """
        Run the scanner with full resilience stack.

        Args:
            graph: GraphEngine to populate

        Returns:
            ScanResult with statistics
        """
        start_time = time.time()
        result = ScanResult(scanner_name=self.__class__.__name__)

        # Check circuit breaker before starting
        try:
            breaker = await CircuitBreakerRegistry.get_breaker(
                service_name=self.service_name,
                region=self.region,
                operation_name="Scan",
            )
            if breaker.state.name == "OPEN":
                logger.warning(
                    f"Circuit open for {self.service_name}:{self.region}, "
                    f"skipping {self.__class__.__name__}"
                )
                result.circuit_open = True
                result.skipped_regions.append(self.region)
                result.errors.append(
                    f"Circuit breaker open for {self.service_name}:{self.region}"
                )
                return result
        except Exception as e:
            logger.warning(f"Failed to check circuit breaker: {e}")

        async with self._get_global_semaphore():
            try:
                result = await self._do_scan(graph)
            except CircuitOpenError as e:
                logger.warning(f"Scanner {self.__class__.__name__} skipped: {e}")
                result.circuit_open = True
                result.errors.append(str(e))
            except Exception as e:
                logger.error(
                    f"Scanner {self.__class__.__name__} failed: {e}",
                    exc_info=True,
                )
                result.errors.append(str(e))

        result.duration_seconds = time.time() - start_time
        return result

    @abstractmethod
    async def _do_scan(self, graph: GraphEngine) -> ScanResult:
        """
        Implement actual scanning logic.

        Subclasses should:
        1. Call self._call_api() for all AWS API calls
        2. Add resources to graph
        3. Return ScanResult with statistics
        """
        pass

    # ═══════════════════════════════════════════════════════════════════════
    # PROTECTED API (For subclasses)
    # ═══════════════════════════════════════════════════════════════════════

    async def _call_api(
        self,
        client: Any,
        method_name: str,
        operation_name: str | None = None,
        max_retries: int = 5,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Call AWS API with full resilience stack.

        Args:
            client: boto3/aiobotocore client
            method_name: Method to call on client
            operation_name: API operation for error context (defaults to method_name)
            max_retries: Maximum retry attempts
            **kwargs: Arguments to pass to API

        Returns:
            API response dictionary
        """
        operation_name = operation_name or method_name

        context = ErrorContext(
            service_name=self.service_name,
            region=self.region,
            operation_name=operation_name,
            is_list_operation=(
                "list" in method_name.lower() or "describe" in method_name.lower()
            ),
        )

        # Get circuit breaker
        breaker = await CircuitBreakerRegistry.get_breaker(
            service_name=self.service_name,
            region=self.region,
            operation_name=operation_name,
        )

        # Check backpressure
        if await BackpressureMonitor.should_slow_down():
            logger.debug("Backpressure detected, adding delay")
            await asyncio.sleep(1.0)

        # Retry loop
        last_error: Exception | None = None

        for attempt in range(max_retries + 1):
            context.consecutive_failures = attempt

            async with self._rate_limiter:
                start = time.time()

                try:
                    # Check circuit state
                    if breaker.state.name == "OPEN":
                        raise CircuitOpenError(f"Circuit {breaker.name} is open")

                    # Make API call
                    method = getattr(client, method_name)
                    response = await method(**kwargs)

                    # Record success
                    latency = (time.time() - start) * 1000
                    await BackpressureMonitor.record_latency(latency)
                    breaker.record_result(success=True)

                    return response

                except CircuitOpenError:
                    # Re-raise circuit open errors immediately
                    raise

                except Exception as e:
                    last_error = e
                    latency = (time.time() - start) * 1000
                    await BackpressureMonitor.record_latency(latency)

                    # Classify error
                    classification = self._classifier.classify(e, context)

                    # Record in circuit breaker
                    breaker.record_result(success=False, classification=classification)

                    # Handle based on action
                    if classification.action == ErrorAction.FAIL:
                        logger.debug(
                            f"Fatal error in {operation_name}: {classification.reason}"
                        )
                        raise

                    if classification.action == ErrorAction.IGNORE:
                        logger.debug(
                            f"Ignoring error in {operation_name}: {classification.reason}"
                        )
                        return {}  # Return empty result

                    if attempt == max_retries:
                        logger.warning(
                            f"Max retries reached for {operation_name}: "
                            f"{classification.reason}"
                        )
                        raise

                    # Retry with delay
                    delay = classification.suggested_delay_ms / 1000
                    logger.debug(
                        f"Retrying {operation_name} in {delay:.2f}s: "
                        f"{classification.reason} (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)

        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected state in _call_api")

    async def _paginate(
        self,
        client: Any,
        method_name: str,
        result_key: str,
        operation_name: str | None = None,
        page_size: int | None = None,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Paginate through AWS API results.

        Args:
            client: boto3/aiobotocore client
            method_name: Method to call (must support pagination)
            result_key: Key in response containing results
            operation_name: API operation for error context
            page_size: Optional page size limit
            **kwargs: Arguments to pass to API

        Returns:
            List of all results across pages
        """
        all_results: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            if next_token:
                kwargs["NextToken"] = next_token
            if page_size:
                kwargs["MaxResults"] = page_size

            response = await self._call_api(
                client=client,
                method_name=method_name,
                operation_name=operation_name,
                **kwargs,
            )

            if not response:
                break

            results = response.get(result_key, [])

            # Handle nested results (e.g., EC2 Reservations -> Instances)
            if isinstance(results, list):
                all_results.extend(results)
            elif isinstance(results, dict):
                all_results.append(results)

            # Check for pagination token
            next_token = (
                response.get("NextToken")
                or response.get("NextMarker")
                or response.get("Marker")
            )
            if not next_token:
                break

        return all_results

    async def _get_client(self, service: str | None = None) -> Any:
        """
        Get or create an aiobotocore client.

        Args:
            service: Service name (defaults to self.service_name)

        Returns:
            aiobotocore client context manager
        """
        service = service or self.service_name
        return self.session.create_client(
            service,
            region_name=self.region,
        )

    def _make_arn(
        self,
        resource_type: str,
        resource_id: str,
        service: str | None = None,
    ) -> str:
        """
        Construct an ARN for a resource.

        Args:
            resource_type: AWS resource type (e.g., 'instance', 'bucket')
            resource_id: Resource identifier
            service: Service name (defaults to self.service_name)

        Returns:
            Full ARN string
        """
        service = service or self.service_name
        return f"arn:aws:{service}:{self.region}:{self.account_id}:{resource_type}/{resource_id}"

    def _extract_tags(self, resource: dict[str, Any]) -> dict[str, str]:
        """
        Extract tags from a resource in a normalized format.

        Args:
            resource: AWS resource dict

        Returns:
            Dict of tag key -> value
        """
        tags: dict[str, str] = {}

        # Handle Tags list format (most common)
        tag_list = resource.get("Tags") or resource.get("tags") or []
        if isinstance(tag_list, list):
            for tag in tag_list:
                if isinstance(tag, dict):
                    key = tag.get("Key") or tag.get("key")
                    value = tag.get("Value") or tag.get("value")
                    if key:
                        tags[key] = str(value) if value else ""

        return tags

    def _get_name_from_tags(
        self,
        resource: dict[str, Any],
        default: str = "",
    ) -> str:
        """
        Extract Name tag from resource.

        Args:
            resource: AWS resource dict
            default: Default value if no Name tag

        Returns:
            Name tag value or default
        """
        tags = self._extract_tags(resource)
        return tags.get("Name", default)
