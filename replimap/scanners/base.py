"""
Base Scanner for RepliMap.

All resource scanners inherit from BaseScanner and implement the scan() method
to extract resources from AWS and add them to the graph.
"""

from __future__ import annotations

import logging
import os
import random
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from typing import TYPE_CHECKING, Any, ClassVar

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from collections.abc import Callable

    from replimap.core import GraphEngine


logger = logging.getLogger(__name__)

# Configuration for parallel scanning
MAX_SCANNER_WORKERS = int(os.environ.get("REPLIMAP_MAX_WORKERS", "4"))

# Retry configuration for AWS rate limiting
MAX_RETRIES = int(os.environ.get("REPLIMAP_MAX_RETRIES", "5"))
BASE_DELAY = float(os.environ.get("REPLIMAP_RETRY_DELAY", "1.0"))
MAX_DELAY = float(os.environ.get("REPLIMAP_MAX_DELAY", "30.0"))


def with_retry(
    max_retries: int = MAX_RETRIES,
    base_delay: float = BASE_DELAY,
    max_delay: float = MAX_DELAY,
    retryable_errors: tuple[str, ...] = (
        "Throttling",
        "ThrottlingException",
        "RequestLimitExceeded",
        "TooManyRequestsException",
        "ProvisionedThroughputExceededException",
        "ServiceUnavailable",
        "InternalError",
    ),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator for retrying AWS API calls with exponential backoff.

    Handles AWS rate limiting and transient errors automatically.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        retryable_errors: AWS error codes that should trigger a retry
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")
                    if error_code not in retryable_errors:
                        raise

                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

                    # Exponential backoff with jitter
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)  # noqa: S311 - not crypto
                    sleep_time = delay + jitter

                    logger.warning(
                        f"Rate limited ({error_code}), retrying {func.__name__} "
                        f"in {sleep_time:.1f}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(sleep_time)

            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator


# Intra-scanner parallelization config
INTRA_SCANNER_WORKERS = int(os.environ.get("REPLIMAP_INTRA_SCANNER_WORKERS", "8"))


def parallel_process_items(
    items: list[Any],
    processor: Callable[[Any], Any],
    max_workers: int | None = None,
    description: str = "items",
) -> tuple[list[Any], list[tuple[Any, Exception]]]:
    """
    Process a list of items in parallel.

    Useful for intra-scanner parallelization (e.g., processing S3 buckets).

    Args:
        items: List of items to process
        processor: Function to process each item
        max_workers: Maximum parallel workers (default: REPLIMAP_INTRA_SCANNER_WORKERS)
        description: Description for logging

    Returns:
        Tuple of (successful_results, failed_items_with_errors)
    """
    if not items:
        return [], []

    workers = max_workers or INTRA_SCANNER_WORKERS
    results: list[Any] = []
    failures: list[tuple[Any, Exception]] = []

    # For small batches, process sequentially
    if len(items) <= 2 or workers <= 1:
        for item in items:
            try:
                result = processor(item)
                if result is not None:
                    results.append(result)
            except Exception as e:
                failures.append((item, e))
                logger.warning(f"Failed to process {description} item: {e}")
        return results, failures

    # Process in parallel
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as executor:
        future_to_item = {executor.submit(processor, item): item for item in items}

        for future in as_completed(future_to_item):
            item = future_to_item[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as e:
                failures.append((item, e))
                logger.warning(f"Failed to process {description} item: {e}")

    if failures:
        logger.warning(
            f"Parallel processing: {len(results)} succeeded, {len(failures)} failed"
        )

    return results, failures


class ScannerError(Exception):
    """Base exception for scanner errors."""

    pass


class PermissionError(ScannerError):
    """Raised when AWS permissions are insufficient."""

    pass


class BaseScanner(ABC):
    """
    Abstract base class for AWS resource scanners.

    Each scanner is responsible for:
    1. Calling AWS APIs to retrieve resources
    2. Converting AWS responses to ResourceNodes
    3. Adding nodes and dependencies to the graph

    Subclasses must implement:
    - resource_types: List of Terraform resource types this scanner handles
    - scan(): The main scanning logic

    Optionally set:
    - depends_on_types: Resource types that must be scanned first
    """

    # Terraform resource types this scanner handles
    resource_types: ClassVar[list[str]] = []

    # Resource types this scanner depends on (must be scanned first)
    # Scanners with dependencies run in phase 2, after phase 1 completes
    depends_on_types: ClassVar[list[str]] = []

    def __init__(self, session: boto3.Session, region: str) -> None:
        """
        Initialize the scanner with AWS credentials.

        Args:
            session: Configured boto3 session
            region: AWS region to scan
        """
        self.session = session
        self.region = region
        self._clients: dict[str, object] = {}

    def get_client(self, service_name: str) -> object:
        """
        Get or create a boto3 client for the specified service.

        Clients are cached for reuse within the scanner.

        Args:
            service_name: AWS service name (e.g., 'ec2', 's3')

        Returns:
            Configured boto3 client
        """
        if service_name not in self._clients:
            self._clients[service_name] = self.session.client(
                service_name, region_name=self.region
            )
        return self._clients[service_name]

    @abstractmethod
    def scan(self, graph: GraphEngine) -> None:
        """
        Scan AWS resources and add them to the graph.

        This method should:
        1. Call AWS APIs to list resources
        2. Create ResourceNode instances for each resource
        3. Add nodes to the graph
        4. Establish dependency edges

        Args:
            graph: The GraphEngine to populate

        Raises:
            ScannerError: If scanning fails
            PermissionError: If AWS permissions are insufficient
        """
        pass

    def _extract_tags(self, tag_list: list[dict] | None) -> dict[str, str]:
        """
        Convert AWS tag list to dictionary.

        AWS returns tags as [{"Key": "Name", "Value": "my-resource"}, ...].
        This converts to {"Name": "my-resource", ...}.

        Args:
            tag_list: AWS tag list or None

        Returns:
            Dictionary of tag key-value pairs
        """
        if not tag_list:
            return {}
        return {tag["Key"]: tag["Value"] for tag in tag_list}

    def _handle_aws_error(self, error: ClientError, operation: str) -> None:
        """
        Handle AWS API errors with appropriate logging and exceptions.

        Args:
            error: The boto3 ClientError
            operation: Description of the operation that failed

        Raises:
            PermissionError: If the error is access-related
            ScannerError: For other AWS errors
        """
        error_code = error.response.get("Error", {}).get("Code", "Unknown")
        error_message = error.response.get("Error", {}).get("Message", str(error))

        if error_code in (
            "AccessDenied",
            "UnauthorizedAccess",
            "AccessDeniedException",
        ):
            logger.error(f"Permission denied: {operation} - {error_message}")
            raise PermissionError(
                f"Insufficient permissions for {operation}: {error_message}"
            )

        logger.error(f"AWS error during {operation}: {error_code} - {error_message}")
        raise ScannerError(f"AWS error during {operation}: {error_message}")


class ScannerRegistry:
    """
    Registry for available scanners.

    Provides a central place to register and retrieve scanners,
    enabling dynamic discovery and execution.
    """

    _scanners: ClassVar[list[type[BaseScanner]]] = []

    @classmethod
    def register(cls, scanner_class: type[BaseScanner]) -> type[BaseScanner]:
        """
        Register a scanner class.

        Can be used as a decorator:
            @ScannerRegistry.register
            class MyScanner(BaseScanner):
                ...

        Args:
            scanner_class: The scanner class to register

        Returns:
            The same scanner class (for decorator use)
        """
        if scanner_class not in cls._scanners:
            cls._scanners.append(scanner_class)
            logger.debug(f"Registered scanner: {scanner_class.__name__}")
        return scanner_class

    @classmethod
    def get_all(cls) -> list[type[BaseScanner]]:
        """Get all registered scanner classes."""
        return cls._scanners.copy()

    @classmethod
    def get_for_type(cls, resource_type: str) -> type[BaseScanner] | None:
        """
        Get the scanner that handles a specific resource type.

        Args:
            resource_type: Terraform resource type (e.g., 'aws_vpc')

        Returns:
            Scanner class if found, None otherwise
        """
        for scanner_class in cls._scanners:
            if resource_type in scanner_class.resource_types:
                return scanner_class
        return None

    @classmethod
    def clear(cls) -> None:
        """Clear all registered scanners (useful for testing)."""
        cls._scanners.clear()


def run_all_scanners(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    parallel: bool = True,
    max_workers: int | None = None,
) -> dict[str, Exception | None]:
    """
    Run all registered scanners.

    Scanners are executed in two phases:
    - Phase 1: Scanners with no dependencies (depends_on_types is empty)
    - Phase 2: Scanners with dependencies (run after phase 1 completes)

    This ensures scanners that query the graph for resources populated by
    other scanners will find those resources.

    Args:
        session: Configured boto3 session
        region: AWS region to scan
        graph: The GraphEngine to populate
        parallel: If True, run scanners in parallel (default: True)
        max_workers: Maximum parallel workers (default: REPLIMAP_MAX_WORKERS or 4)

    Returns:
        Dictionary mapping scanner names to exceptions (None if successful)
    """
    results: dict[str, Exception | None] = {}
    scanner_classes = ScannerRegistry.get_all()

    if not scanner_classes:
        return results

    # Partition scanners into phases based on dependencies
    phase1_scanners = [sc for sc in scanner_classes if not sc.depends_on_types]
    phase2_scanners = [sc for sc in scanner_classes if sc.depends_on_types]

    workers = max_workers or MAX_SCANNER_WORKERS

    if parallel and workers > 1:
        # Phase 1: Run independent scanners in parallel
        if phase1_scanners:
            logger.debug(
                f"Phase 1: Running {len(phase1_scanners)} independent scanners"
            )
            phase1_results = _run_scanners_parallel(
                session, region, graph, phase1_scanners, workers
            )
            results.update(phase1_results)

        # Phase 2: Run dependent scanners in parallel (after phase 1 completes)
        if phase2_scanners:
            logger.debug(
                f"Phase 2: Running {len(phase2_scanners)} dependent scanners"
            )
            phase2_results = _run_scanners_parallel(
                session, region, graph, phase2_scanners, workers
            )
            results.update(phase2_results)
    else:
        # Sequential execution (for debugging or when parallel disabled)
        # Run phase 1 first, then phase 2
        results.update(
            _run_scanners_sequential(session, region, graph, phase1_scanners)
        )
        results.update(
            _run_scanners_sequential(session, region, graph, phase2_scanners)
        )

    return results


def _run_scanners_sequential(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    scanner_classes: list[type[BaseScanner]],
) -> dict[str, Exception | None]:
    """Run scanners sequentially."""
    results: dict[str, Exception | None] = {}

    for scanner_class in scanner_classes:
        scanner_name = scanner_class.__name__
        logger.info(f"Running {scanner_name}...")

        try:
            scanner = scanner_class(session, region)
            scanner.scan(graph)
            results[scanner_name] = None
            logger.info(f"{scanner_name} completed successfully")
        except Exception as e:
            results[scanner_name] = e
            logger.error(f"{scanner_name} failed: {e}")

    return results


def _run_scanners_parallel(
    session: boto3.Session,
    region: str,
    graph: GraphEngine,
    scanner_classes: list[type[BaseScanner]],
    max_workers: int,
) -> dict[str, Exception | None]:
    """Run scanners in parallel using ThreadPoolExecutor."""
    results: dict[str, Exception | None] = {}

    def run_single_scanner(
        scanner_class: type[BaseScanner],
    ) -> tuple[str, Exception | None]:
        scanner_name = scanner_class.__name__
        logger.info(f"Running {scanner_name}...")
        try:
            scanner = scanner_class(session, region)
            scanner.scan(graph)
            logger.info(f"{scanner_name} completed successfully")
            return (scanner_name, None)
        except Exception as e:
            logger.error(f"{scanner_name} failed: {e}")
            return (scanner_name, e)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_scanner, sc): sc for sc in scanner_classes
        }

        for future in as_completed(futures):
            scanner_name, error = future.result()
            results[scanner_name] = error

    return results
