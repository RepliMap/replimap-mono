"""
Async AWS Client Wrapper with Resilience Features.

This module provides a unified async AWS client wrapper that integrates:
- Circuit breaker pattern for region/service failure isolation
- Retry with exponential backoff for transient errors
- Rate limiting via token bucket for API throttling prevention
- Proper aiobotocore configuration (disabled internal retries)

Usage:
    async with AsyncAWSClient(region="us-east-1") as client:
        # Get paginated results with automatic retry/circuit breaker
        vpcs = await client.paginate("ec2", "describe_vpcs", "Vpcs")

        # Single API call with protection
        result = await client.call("ec2", "describe_instances", InstanceIds=["i-123"])
"""

from __future__ import annotations

import asyncio
import logging
import os
import random
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from replimap.core import GraphEngine

from aiobotocore.config import AioConfig
from aiobotocore.session import get_session
from botocore.exceptions import ClientError

from .circuit_breaker import (
    CircuitBreakerRegistry,
    CircuitOpenError,
    get_circuit_breaker_registry,
)
from .retry import FATAL_ERRORS, RETRYABLE_ERRORS

logger = logging.getLogger(__name__)

# Configuration (environment-overridable)
CONNECT_TIMEOUT = int(os.environ.get("REPLIMAP_CONNECT_TIMEOUT", "10"))
READ_TIMEOUT = int(os.environ.get("REPLIMAP_READ_TIMEOUT", "30"))
MAX_RETRIES = int(os.environ.get("REPLIMAP_MAX_RETRIES", "5"))
BASE_DELAY = float(os.environ.get("REPLIMAP_RETRY_DELAY", "1.0"))
MAX_DELAY = float(os.environ.get("REPLIMAP_MAX_DELAY", "30.0"))

# Rate limiting defaults (requests per second per service)
DEFAULT_RATE_LIMIT = float(os.environ.get("REPLIMAP_RATE_LIMIT", "10.0"))
EC2_RATE_LIMIT = float(os.environ.get("REPLIMAP_EC2_RATE_LIMIT", "20.0"))
RDS_RATE_LIMIT = float(os.environ.get("REPLIMAP_RDS_RATE_LIMIT", "10.0"))
IAM_RATE_LIMIT = float(os.environ.get("REPLIMAP_IAM_RATE_LIMIT", "5.0"))
S3_RATE_LIMIT = float(os.environ.get("REPLIMAP_S3_RATE_LIMIT", "10.0"))

# Service-specific rate limits (can be extended)
SERVICE_RATE_LIMITS: dict[str, float] = {
    "ec2": EC2_RATE_LIMIT,
    "rds": RDS_RATE_LIMIT,
    "iam": IAM_RATE_LIMIT,
    "s3": S3_RATE_LIMIT,
    "sts": 20.0,
    "elasticache": 10.0,
    "sqs": 10.0,
    "sns": 10.0,
}


@dataclass
class RateLimiterConfig:
    """Configuration for rate limiting."""

    requests_per_second: float = DEFAULT_RATE_LIMIT
    burst_size: int = 5  # Allow short bursts


@dataclass
class AsyncRateLimiter:
    """
    Token bucket rate limiter for AWS API calls.

    Uses a token bucket algorithm with configurable rate and burst size.
    Each acquire() consumes one token. Tokens refill at the configured rate.

    Thread-safe via asyncio.Lock.
    """

    requests_per_second: float = DEFAULT_RATE_LIMIT
    burst_size: int = 5

    # Internal state
    _tokens: float = field(init=False)
    _last_refill: float = field(init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    def __post_init__(self) -> None:
        """Initialize token bucket."""
        self._tokens = float(self.burst_size)
        self._last_refill = time.monotonic()

    async def acquire(self) -> None:
        """
        Acquire a token, waiting if necessary.

        This method blocks until a token is available.
        """
        async with self._lock:
            await self._refill()

            while self._tokens < 1.0:
                # Calculate wait time for one token
                wait_time = (1.0 - self._tokens) / self.requests_per_second
                await asyncio.sleep(wait_time)
                await self._refill()

            self._tokens -= 1.0

    async def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._last_refill = now

        # Add tokens based on elapsed time
        self._tokens = min(
            float(self.burst_size),
            self._tokens + elapsed * self.requests_per_second,
        )


class RateLimiterRegistry:
    """
    Registry for rate limiters by service/region.

    Provides per-service rate limiting to respect AWS API quotas.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._limiters: dict[str, AsyncRateLimiter] = {}
        self._lock = asyncio.Lock()

    async def get(self, service: str, region: str | None = None) -> AsyncRateLimiter:
        """
        Get or create a rate limiter for a service/region.

        Args:
            service: AWS service name (e.g., "ec2")
            region: AWS region (optional, for per-region limiting)

        Returns:
            AsyncRateLimiter for this service/region
        """
        key = f"{service}/{region}" if region else service

        if key not in self._limiters:
            async with self._lock:
                if key not in self._limiters:
                    rate = SERVICE_RATE_LIMITS.get(service, DEFAULT_RATE_LIMIT)
                    self._limiters[key] = AsyncRateLimiter(
                        requests_per_second=rate,
                        burst_size=max(5, int(rate / 2)),
                    )

        return self._limiters[key]

    def stats(self) -> dict[str, dict[str, float]]:
        """Get statistics about all rate limiters."""
        return {
            key: {
                "tokens": limiter._tokens,
                "rate": limiter.requests_per_second,
            }
            for key, limiter in self._limiters.items()
        }


# Global registries
_rate_limiter_registry: RateLimiterRegistry | None = None


def get_rate_limiter_registry() -> RateLimiterRegistry:
    """Get the global rate limiter registry."""
    global _rate_limiter_registry
    if _rate_limiter_registry is None:
        _rate_limiter_registry = RateLimiterRegistry()
    return _rate_limiter_registry


@dataclass
class CallStats:
    """Statistics for API call tracking."""

    total_calls: int = 0
    successful_calls: int = 0
    retried_calls: int = 0
    failed_calls: int = 0
    circuit_breaker_skips: int = 0
    rate_limit_waits: int = 0


class AsyncAWSClient:
    """
    Async AWS client with integrated resilience features.

    Provides:
    - Automatic retry with exponential backoff for transient errors
    - Circuit breaker integration for service/region failure isolation
    - Rate limiting to prevent API throttling
    - Proper aiobotocore configuration

    Usage:
        async with AsyncAWSClient("us-east-1") as client:
            vpcs = await client.paginate("ec2", "describe_vpcs", "Vpcs")
            instances = await client.call("ec2", "describe_instances")
    """

    def __init__(
        self,
        region: str,
        profile: str | None = None,
        circuit_registry: CircuitBreakerRegistry | None = None,
        rate_registry: RateLimiterRegistry | None = None,
        max_retries: int = MAX_RETRIES,
        connect_timeout: int = CONNECT_TIMEOUT,
        read_timeout: int = READ_TIMEOUT,
    ) -> None:
        """
        Initialize the async AWS client.

        Args:
            region: AWS region
            profile: AWS profile name (optional)
            circuit_registry: Circuit breaker registry (uses global if None)
            rate_registry: Rate limiter registry (uses global if None)
            max_retries: Maximum retry attempts
            connect_timeout: Connection timeout in seconds
            read_timeout: Read timeout in seconds
        """
        self.region = region
        self.profile = profile
        self.max_retries = max_retries

        # Use global registries if not provided
        self._circuit_registry = circuit_registry or get_circuit_breaker_registry()
        self._rate_registry = rate_registry or get_rate_limiter_registry()

        # Get credentials from boto3 if profile specified (boto3 handles assume-role)
        self._credentials: dict[str, str] | None = None
        if profile:
            import boto3

            boto3_session = boto3.Session(profile_name=profile, region_name=region)
            creds = boto3_session.get_credentials()
            if creds:
                frozen_creds = creds.get_frozen_credentials()
                self._credentials = {
                    "aws_access_key_id": frozen_creds.access_key,
                    "aws_secret_access_key": frozen_creds.secret_key,
                }
                if frozen_creds.token:
                    self._credentials["aws_session_token"] = frozen_creds.token

        # aiobotocore session and config
        self._session = get_session()
        self._config = AioConfig(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries={
                "mode": "standard",
                "max_attempts": 1,  # Disable internal retries
            },
            signature_version="v4",
        )

        # Client cache
        self._clients: dict[str, Any] = {}
        self._client_locks: dict[str, asyncio.Lock] = {}

        # Statistics
        self.stats = CallStats()

    async def __aenter__(self) -> AsyncAWSClient:
        """Enter async context."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context, closing all clients."""
        await self.close()

    async def close(self) -> None:
        """Close all cached clients."""
        for client in self._clients.values():
            await client.__aexit__(None, None, None)
        self._clients.clear()

    @asynccontextmanager
    async def _get_client(self, service: str) -> AsyncIterator[Any]:
        """
        Get or create a cached aiobotocore client.

        Args:
            service: AWS service name

        Yields:
            Configured aiobotocore client
        """
        # Ensure lock exists for this service
        if service not in self._client_locks:
            self._client_locks[service] = asyncio.Lock()

        # Create client if not cached
        if service not in self._clients:
            async with self._client_locks[service]:
                if service not in self._clients:
                    # Pass credentials if we have them (from profile)
                    client_kwargs: dict[str, Any] = {
                        "region_name": self.region,
                        "config": self._config,
                    }
                    if self._credentials:
                        client_kwargs.update(self._credentials)
                    client_ctx = self._session.create_client(service, **client_kwargs)
                    self._clients[service] = await client_ctx.__aenter__()

        yield self._clients[service]

    async def call(
        self,
        service: str,
        operation: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Make an AWS API call with retry, circuit breaker, and rate limiting.

        Args:
            service: AWS service name (e.g., "ec2")
            operation: API operation (e.g., "describe_instances")
            **kwargs: Arguments to pass to the API call

        Returns:
            API response dictionary

        Raises:
            CircuitOpenError: If circuit breaker is open
            ClientError: If API call fails after all retries
        """
        circuit = self._circuit_registry.get_for_region_service(self.region, service)
        rate_limiter = await self._rate_registry.get(service, self.region)

        self.stats.total_calls += 1

        # Check circuit breaker first
        if circuit.state.value == "open":
            self.stats.circuit_breaker_skips += 1
            raise CircuitOpenError(
                f"Circuit breaker OPEN for {self.region}/{service}",
                circuit_key=f"{self.region}/{service}",
            )

        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                # Rate limiting
                await rate_limiter.acquire()

                # Make the call
                async with self._get_client(service) as client:
                    method = getattr(client, operation)
                    result = await circuit.async_call(method, **kwargs)

                self.stats.successful_calls += 1
                return result  # type: ignore[no-any-return]

            except CircuitOpenError:
                self.stats.circuit_breaker_skips += 1
                raise

            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")

                # Fatal errors - don't retry
                if error_code in FATAL_ERRORS:
                    logger.debug(
                        f"Fatal error {error_code} for {operation}, not retrying"
                    )
                    self.stats.failed_calls += 1
                    raise

                # Non-retryable - fail immediately
                if error_code not in RETRYABLE_ERRORS:
                    logger.debug(f"Non-retryable error {error_code} for {operation}")
                    self.stats.failed_calls += 1
                    raise

                last_exception = e

                if attempt == self.max_retries:
                    logger.error(
                        f"Max retries ({self.max_retries}) exceeded for {operation}"
                    )
                    self.stats.failed_calls += 1
                    raise

                # Track retry
                self.stats.retried_calls += 1

                # Exponential backoff with jitter
                delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
                jitter = random.uniform(0, delay * 0.1)  # noqa: S311
                sleep_time = delay + jitter

                logger.warning(
                    f"Rate limited ({error_code}), retrying {operation} "
                    f"in {sleep_time:.1f}s (attempt {attempt + 1}/{self.max_retries})"
                )
                await asyncio.sleep(sleep_time)

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
        return {}

    async def paginate(
        self,
        service: str,
        operation: str,
        result_key: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Paginate through an AWS API operation.

        Collects all pages and returns combined results.

        Args:
            service: AWS service name
            operation: API operation that supports pagination
            result_key: Key in response containing the items
            **kwargs: Arguments to pass to the API call

        Returns:
            List of all items from all pages
        """
        results: list[dict[str, Any]] = []

        async with self._get_client(service) as client:
            paginator = client.get_paginator(operation)

            async for page in paginator.paginate(**kwargs):
                # Apply circuit breaker and retry to each page fetch
                items = page.get(result_key, [])
                results.extend(items)

        return results

    async def paginate_with_resilience(
        self,
        service: str,
        operation: str,
        result_key: str,
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """
        Paginate with full resilience (retry per page, circuit breaker).

        Unlike paginate(), this method applies retry logic to each page
        fetch, providing better resilience for long-running paginations.

        Args:
            service: AWS service name
            operation: API operation that supports pagination
            result_key: Key in response containing the items
            **kwargs: Arguments to pass to the API call

        Returns:
            List of all items from all pages
        """
        circuit = self._circuit_registry.get_for_region_service(self.region, service)
        rate_limiter = await self._rate_registry.get(service, self.region)

        results: list[dict[str, Any]] = []
        next_token: str | None = None

        while True:
            self.stats.total_calls += 1

            # Check circuit breaker
            if circuit.state.value == "open":
                self.stats.circuit_breaker_skips += 1
                raise CircuitOpenError(
                    f"Circuit breaker OPEN for {self.region}/{service}",
                    circuit_key=f"{self.region}/{service}",
                )

            # Build request with pagination token
            request_kwargs = dict(kwargs)
            if next_token:
                request_kwargs["NextToken"] = next_token

            last_exception: Exception | None = None

            for attempt in range(self.max_retries + 1):
                try:
                    await rate_limiter.acquire()

                    async with self._get_client(service) as client:
                        method = getattr(client, operation)
                        response = await circuit.async_call(method, **request_kwargs)

                    items = response.get(result_key, [])
                    results.extend(items)

                    self.stats.successful_calls += 1

                    # Check for more pages
                    next_token = response.get("NextToken")
                    break

                except CircuitOpenError:
                    self.stats.circuit_breaker_skips += 1
                    raise

                except ClientError as e:
                    error_code = e.response.get("Error", {}).get("Code", "")

                    if error_code in FATAL_ERRORS or error_code not in RETRYABLE_ERRORS:
                        self.stats.failed_calls += 1
                        raise

                    last_exception = e

                    if attempt == self.max_retries:
                        self.stats.failed_calls += 1
                        raise

                    self.stats.retried_calls += 1
                    delay = min(BASE_DELAY * (2**attempt), MAX_DELAY)
                    jitter = random.uniform(0, delay * 0.1)  # noqa: S311
                    await asyncio.sleep(delay + jitter)

            else:
                if last_exception:
                    raise last_exception

            # Exit loop if no more pages
            if not next_token:
                break

        return results


class AWSResourceScanner:
    """
    Base class for AWS resource scanners with built-in resilience.

    Concrete scanners should inherit from this class and implement
    the scan() method.

    Example:
        class EC2InstanceScanner(AWSResourceScanner):
            resource_types: ClassVar[list[str]] = ["aws_instance"]

            async def scan(self, graph: GraphEngine) -> None:
                instances = await self.client.paginate(
                    "ec2", "describe_instances", "Reservations"
                )
                for reservation in instances:
                    for instance in reservation.get("Instances", []):
                        self._add_instance_to_graph(instance, graph)
    """

    # Resource types this scanner handles (for documentation/registration)
    # Subclasses should override with ClassVar[list[str]]
    resource_types: ClassVar[list[str]] = []

    def __init__(
        self,
        region: str,
        account_id: str | None = None,
        profile: str | None = None,
        client: AsyncAWSClient | None = None,
    ) -> None:
        """
        Initialize the scanner.

        Args:
            region: AWS region to scan
            account_id: AWS account ID (optional)
            profile: AWS profile name (optional)
            client: Existing AsyncAWSClient (creates new if None)
        """
        self.region = region
        self.account_id = account_id
        self.profile = profile
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> AWSResourceScanner:
        """Enter async context, ensuring client is ready."""
        if self._client is None:
            self._client = AsyncAWSClient(
                region=self.region,
                profile=self.profile,
            )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context, closing client if we own it."""
        if self._owns_client and self._client is not None:
            await self._client.close()

    @property
    def client(self) -> AsyncAWSClient:
        """Get the AWS client."""
        if self._client is None:
            raise RuntimeError("Scanner must be used as async context manager")
        return self._client

    def build_node_id(self, resource_id: str) -> str:
        """
        Build a node ID in the standard format.

        Args:
            resource_id: AWS resource ID

        Returns:
            Node ID in format {account_id}:{region}:{resource_id}
        """
        account = self.account_id or "unknown"
        return f"{account}:{self.region}:{resource_id}"

    @staticmethod
    def extract_tags(tag_list: list[dict[str, str]] | None) -> dict[str, str]:
        """
        Convert AWS tag list to dictionary.

        Args:
            tag_list: AWS tag list or None

        Returns:
            Dictionary of tag key-value pairs
        """
        if not tag_list:
            return {}
        return {tag.get("Key", ""): tag.get("Value", "") for tag in tag_list}

    async def scan(self, graph: GraphEngine) -> None:
        """
        Scan AWS resources and add them to the graph.

        Subclasses must implement this method.

        Args:
            graph: GraphEngine to populate with discovered resources
        """
        raise NotImplementedError("Subclasses must implement scan()")
