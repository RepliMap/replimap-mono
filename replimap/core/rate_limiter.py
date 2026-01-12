"""
AWS API Rate Limiter - Production Grade

Features:
- Token Bucket algorithm with adaptive rate control (AIMD)
- Region-aware bucket isolation
- Global service special handling
- Exponential backoff retry
- Thread-safe singleton pattern
"""

import time
import threading
import logging
import random
from typing import Dict, Optional, Tuple, Any
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class ServiceLimit:
    """Service rate limit configuration"""
    tps: float           # Tokens (requests) per second
    burst: int           # Bucket capacity for burst traffic
    is_global: bool      # True for global services (IAM, STS, etc.)


# Conservative default limits based on AWS documentation and testing
# Users can override via config file
DEFAULT_SERVICE_LIMITS: Dict[str, ServiceLimit] = {
    # Regional services
    'ec2': ServiceLimit(tps=40.0, burst=80, is_global=False),
    'rds': ServiceLimit(tps=20.0, burst=40, is_global=False),
    'elbv2': ServiceLimit(tps=25.0, burst=50, is_global=False),
    'elb': ServiceLimit(tps=25.0, burst=50, is_global=False),
    'lambda': ServiceLimit(tps=15.0, burst=30, is_global=False),
    'dynamodb': ServiceLimit(tps=25.0, burst=50, is_global=False),
    'sns': ServiceLimit(tps=30.0, burst=60, is_global=False),
    'sqs': ServiceLimit(tps=30.0, burst=60, is_global=False),
    'cloudwatch': ServiceLimit(tps=20.0, burst=40, is_global=False),
    'logs': ServiceLimit(tps=20.0, burst=40, is_global=False),
    'autoscaling': ServiceLimit(tps=20.0, burst=40, is_global=False),
    'elasticache': ServiceLimit(tps=15.0, burst=30, is_global=False),
    'secretsmanager': ServiceLimit(tps=10.0, burst=20, is_global=False),
    'ssm': ServiceLimit(tps=15.0, burst=30, is_global=False),
    'kms': ServiceLimit(tps=15.0, burst=30, is_global=False),
    'ecs': ServiceLimit(tps=20.0, burst=40, is_global=False),
    'eks': ServiceLimit(tps=10.0, burst=20, is_global=False),
    'ecr': ServiceLimit(tps=10.0, burst=20, is_global=False),
    'apigateway': ServiceLimit(tps=10.0, burst=20, is_global=False),
    'acm': ServiceLimit(tps=10.0, burst=20, is_global=False),

    # Global services (stricter limits, shared across all regions)
    'iam': ServiceLimit(tps=8.0, burst=15, is_global=True),
    'sts': ServiceLimit(tps=20.0, burst=40, is_global=True),
    's3': ServiceLimit(tps=50.0, burst=100, is_global=True),
    'route53': ServiceLimit(tps=5.0, burst=10, is_global=True),
    'cloudfront': ServiceLimit(tps=10.0, burst=20, is_global=True),
    'organizations': ServiceLimit(tps=5.0, burst=10, is_global=True),
    'waf': ServiceLimit(tps=10.0, burst=20, is_global=True),
    'wafv2': ServiceLimit(tps=10.0, burst=20, is_global=True),

    # Default for unknown services
    'default': ServiceLimit(tps=10.0, burst=20, is_global=False),
}


class TokenBucket:
    """
    Token Bucket with Adaptive Rate Control (AIMD)

    - Additive Increase: rate *= 1.1 after 100 consecutive successes
    - Multiplicative Decrease: rate *= 0.5 on throttle
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        min_rate: float = 1.0,
        name: str = "unnamed"
    ):
        self.name = name
        self.initial_rate = rate
        self.rate = rate
        self.capacity = capacity
        self.min_rate = min_rate
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

        # Adaptive statistics
        self.success_count = 0
        self.throttle_count = 0
        self.total_requests = 0
        self.total_wait_time = 0.0

    def acquire(self, tokens: int = 1, timeout: float = 60.0) -> bool:
        """
        Acquire tokens, blocking until available or timeout.

        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum wait time in seconds

        Returns:
            True if tokens acquired, False if timeout
        """
        start_time = time.monotonic()

        while True:
            with self.lock:
                self._refill()

                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.total_requests += 1
                    return True

                # Calculate wait time
                needed = tokens - self.tokens
                wait_time = needed / self.rate

            # Check timeout
            elapsed = time.monotonic() - start_time
            if elapsed + wait_time > timeout:
                logger.warning(
                    f"[{self.name}] Rate limiter timeout after {elapsed:.1f}s "
                    f"(rate={self.rate:.1f} TPS)"
                )
                return False

            # Wait with jitter to avoid thundering herd
            jitter = random.uniform(0, 0.05)
            actual_wait = min(wait_time + jitter, 1.0)
            self.total_wait_time += actual_wait
            time.sleep(actual_wait)

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.monotonic()
        elapsed = now - self.last_refill

        if elapsed > 0:
            new_tokens = elapsed * self.rate
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now

    def report_success(self):
        """Report successful API call for adaptive rate control"""
        with self.lock:
            self.success_count += 1

            # After 100 consecutive successes, try to recover rate
            if self.success_count >= 100 and self.rate < self.initial_rate:
                old_rate = self.rate
                self.rate = min(self.rate * 1.1, self.initial_rate)
                self.success_count = 0
                if old_rate != self.rate:
                    logger.debug(
                        f"[{self.name}] Rate increased: {old_rate:.1f} -> {self.rate:.1f} TPS"
                    )

    def report_throttle(self):
        """Report throttle event for adaptive rate control (AIMD)"""
        with self.lock:
            self.throttle_count += 1
            self.success_count = 0

            # Multiplicative decrease
            old_rate = self.rate
            self.rate = max(self.min_rate, self.rate * 0.5)

            logger.warning(
                f"[{self.name}] THROTTLED! Rate reduced: {old_rate:.1f} -> {self.rate:.1f} TPS "
                f"(total throttles: {self.throttle_count})"
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get bucket statistics"""
        with self.lock:
            return {
                'name': self.name,
                'current_rate': round(self.rate, 2),
                'initial_rate': self.initial_rate,
                'tokens': round(self.tokens, 2),
                'capacity': self.capacity,
                'total_requests': self.total_requests,
                'success_count': self.success_count,
                'throttle_count': self.throttle_count,
                'total_wait_time': round(self.total_wait_time, 2),
            }


class AWSRateLimiter:
    """
    Global AWS API Rate Limiter (Singleton)

    Features:
    - Service-level isolation (ec2, rds, s3, etc.)
    - Region-level isolation (us-east-1:ec2 vs eu-west-1:ec2)
    - Global service handling (iam, sts share single bucket)
    - Adaptive rate control per bucket
    - Thread-safe

    Usage:
        limiter = AWSRateLimiter()
        limiter.acquire('ec2', 'us-east-1')
        # ... make API call ...
        limiter.report_success('ec2', 'us-east-1')
    """

    _instance: Optional['AWSRateLimiter'] = None
    _lock = threading.Lock()

    def __new__(cls, custom_limits: Optional[Dict[str, ServiceLimit]] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    instance = super().__new__(cls)
                    instance._initialized = False
                    cls._instance = instance
        return cls._instance

    def __init__(self, custom_limits: Optional[Dict[str, ServiceLimit]] = None):
        if self._initialized:
            return

        self._initialized = True
        self._buckets: Dict[str, TokenBucket] = {}
        self._bucket_lock = threading.Lock()

        # Merge default and custom limits
        self._limits = DEFAULT_SERVICE_LIMITS.copy()
        if custom_limits:
            self._limits.update(custom_limits)
            logger.info(f"Custom rate limits applied for: {list(custom_limits.keys())}")

        logger.info("AWSRateLimiter initialized")

    def _get_bucket_key(self, service: str, region: Optional[str] = None) -> str:
        """
        Generate unique bucket key.

        Global services: "global:iam"
        Regional services: "us-east-1:ec2"
        """
        service = service.lower()
        limit = self._limits.get(service, self._limits['default'])

        if limit.is_global or region is None:
            return f"global:{service}"
        return f"{region}:{service}"

    def get_bucket(self, service: str, region: Optional[str] = None) -> TokenBucket:
        """Get or create token bucket for service/region"""
        key = self._get_bucket_key(service, region)

        if key not in self._buckets:
            with self._bucket_lock:
                if key not in self._buckets:
                    service_lower = service.lower()
                    limit = self._limits.get(service_lower, self._limits['default'])
                    self._buckets[key] = TokenBucket(
                        rate=limit.tps,
                        capacity=limit.burst,
                        name=key,
                    )
                    logger.debug(f"Created rate bucket: {key} ({limit.tps} TPS, burst {limit.burst})")

        return self._buckets[key]

    def acquire(
        self,
        service: str,
        region: Optional[str] = None,
        tokens: int = 1,
        timeout: float = 60.0
    ) -> bool:
        """Acquire tokens for API call"""
        bucket = self.get_bucket(service, region)
        return bucket.acquire(tokens, timeout)

    def report_success(self, service: str, region: Optional[str] = None):
        """Report successful API call"""
        bucket = self.get_bucket(service, region)
        bucket.report_success()

    def report_throttle(self, service: str, region: Optional[str] = None):
        """Report throttle/429 error"""
        bucket = self.get_bucket(service, region)
        bucket.report_throttle()

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all buckets"""
        return {key: bucket.get_stats() for key, bucket in self._buckets.items()}

    def print_stats(self):
        """Print human-readable statistics"""
        stats = self.get_all_stats()
        if not stats:
            logger.info("No rate limiter statistics available")
            return

        logger.info("=" * 60)
        logger.info("AWS Rate Limiter Statistics")
        logger.info("=" * 60)

        for key, s in sorted(stats.items()):
            throttle_info = f" [THROTTLED x{s['throttle_count']}]" if s['throttle_count'] > 0 else ""
            logger.info(
                f"  {key}: {s['current_rate']:.1f}/{s['initial_rate']:.1f} TPS, "
                f"reqs={s['total_requests']}, wait={s['total_wait_time']:.1f}s{throttle_info}"
            )

        logger.info("=" * 60)

    @classmethod
    def reset(cls):
        """Reset singleton instance (for testing)"""
        with cls._lock:
            if cls._instance:
                cls._instance.print_stats()
            cls._instance = None


# Throttle error codes from AWS
THROTTLE_ERROR_CODES = {
    'Throttling',
    'ThrottlingException',
    'RequestLimitExceeded',
    'TooManyRequestsException',
    'ProvisionedThroughputExceededException',
    'RequestThrottled',
    'SlowDown',  # S3 specific
    'BandwidthLimitExceeded',
    'EC2ThrottledException',
    'RequestThrottledException',
    'TransactionInProgressException',  # DynamoDB
}


def is_throttle_error(error: Exception) -> bool:
    """Check if exception is an AWS throttling error"""
    try:
        from botocore.exceptions import ClientError

        if not isinstance(error, ClientError):
            return False

        error_code = error.response.get('Error', {}).get('Code', '')
        return error_code in THROTTLE_ERROR_CODES
    except ImportError:
        return False


def rate_limited(
    service: str,
    region_from_arg: Optional[str] = None,
    max_retries: int = 3,
):
    """
    Decorator to add rate limiting to AWS API calls.

    Args:
        service: AWS service name (ec2, rds, iam, etc.)
        region_from_arg: How to get region - 'self.region' or kwarg name
        max_retries: Max retries on throttle (with exponential backoff)

    Usage:
        @rate_limited('ec2', region_from_arg='self.region')
        def describe_instances(self, **kwargs):
            return self.client.describe_instances(**kwargs)

        @rate_limited('iam')  # Global service, no region needed
        def list_roles(self):
            return self.client.list_roles()
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = AWSRateLimiter()

            # Extract region from arguments
            region = None
            if region_from_arg:
                if region_from_arg.startswith('self.') and args:
                    attr_name = region_from_arg[5:]  # Remove 'self.'
                    region = getattr(args[0], attr_name, None)
                elif region_from_arg in kwargs:
                    region = kwargs[region_from_arg]

            # Retry loop with exponential backoff
            last_error = None
            for attempt in range(max_retries + 1):
                # Acquire token (proactive rate limiting)
                if not limiter.acquire(service, region):
                    raise TimeoutError(
                        f"Rate limiter timeout for {service}/{region} after {attempt} attempts"
                    )

                try:
                    result = func(*args, **kwargs)
                    limiter.report_success(service, region)
                    return result

                except Exception as e:
                    last_error = e

                    if is_throttle_error(e):
                        limiter.report_throttle(service, region)

                        if attempt < max_retries:
                            # Exponential backoff with jitter
                            backoff = (2 ** attempt) + random.uniform(0, 1)
                            logger.warning(
                                f"[{service}/{region}] Throttled on attempt {attempt + 1}, "
                                f"retrying in {backoff:.1f}s..."
                            )
                            time.sleep(backoff)
                            continue

                    # Non-throttle error or max retries exceeded
                    raise

            # Should not reach here, but just in case
            raise last_error or RuntimeError("Unexpected error in rate_limited decorator")

        return wrapper
    return decorator


def rate_limited_paginate(
    service: str,
    region: Optional[str] = None,
):
    """
    Wrapper to add rate limiting to boto3 paginator results.

    Each page fetch consumes a token from the rate limiter.

    Usage:
        paginator = client.get_paginator('describe_instances')
        for page in rate_limited_paginate('ec2', 'us-east-1')(paginator.paginate()):
            process(page)
    """
    def wrapper(paginator_result):
        limiter = AWSRateLimiter()

        for page in paginator_result:
            # Acquire token for this page
            if not limiter.acquire(service, region):
                raise TimeoutError(f"Rate limiter timeout for {service} paginator")

            limiter.report_success(service, region)
            yield page

    return wrapper


# Convenience function
def get_limiter() -> AWSRateLimiter:
    """Get the global rate limiter instance"""
    return AWSRateLimiter()
