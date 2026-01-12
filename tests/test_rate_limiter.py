"""Tests for AWS Rate Limiter"""

import threading
import time

import pytest

from replimap.core.rate_limiter import (
    AWSRateLimiter,
    ServiceLimit,
    TokenBucket,
    rate_limited,
)


class TestTokenBucket:
    def test_basic_acquire(self):
        bucket = TokenBucket(rate=10.0, capacity=10, name="test")

        # Should acquire immediately when tokens available
        assert bucket.acquire(1) is True
        assert bucket.tokens == 9.0

    def test_burst_capacity(self):
        bucket = TokenBucket(rate=10.0, capacity=5, name="test")

        # Should be able to burst up to capacity
        for _ in range(5):
            assert bucket.acquire(1) is True

        # 6th request should block (we'll timeout quickly)
        start = time.monotonic()
        assert bucket.acquire(1, timeout=0.2) is True  # Will wait for refill
        elapsed = time.monotonic() - start
        assert elapsed >= 0.05  # Should have waited

    def test_adaptive_rate_decrease(self):
        bucket = TokenBucket(rate=10.0, capacity=10, name="test")

        initial_rate = bucket.rate
        bucket.report_throttle()

        assert bucket.rate == initial_rate * 0.5
        assert bucket.throttle_count == 1

    def test_adaptive_rate_increase(self):
        bucket = TokenBucket(rate=5.0, capacity=10, name="test")
        bucket.initial_rate = 10.0  # Pretend we were throttled

        # Report 100 successes
        for _ in range(100):
            bucket.report_success()

        # Rate should have increased
        assert bucket.rate > 5.0


class TestAWSRateLimiter:
    def setup_method(self):
        AWSRateLimiter.reset()

    def teardown_method(self):
        AWSRateLimiter.reset()

    def test_singleton(self):
        limiter1 = AWSRateLimiter()
        limiter2 = AWSRateLimiter()
        assert limiter1 is limiter2

    def test_region_isolation(self):
        limiter = AWSRateLimiter()

        bucket1 = limiter.get_bucket("ec2", "us-east-1")
        bucket2 = limiter.get_bucket("ec2", "eu-west-1")

        assert bucket1 is not bucket2
        assert bucket1.name == "us-east-1:ec2"
        assert bucket2.name == "eu-west-1:ec2"

    def test_global_service_no_region_isolation(self):
        limiter = AWSRateLimiter()

        bucket1 = limiter.get_bucket("iam", "us-east-1")
        bucket2 = limiter.get_bucket("iam", "eu-west-1")

        # IAM is global, should be same bucket
        assert bucket1 is bucket2
        assert bucket1.name == "global:iam"

    def test_custom_limits(self):
        AWSRateLimiter.reset()

        custom = {"custom_service": ServiceLimit(tps=100.0, burst=200, is_global=False)}
        limiter = AWSRateLimiter(custom_limits=custom)

        bucket = limiter.get_bucket("custom_service", "us-east-1")
        assert bucket.rate == 100.0
        assert bucket.capacity == 200


class TestRateLimitedDecorator:
    def setup_method(self):
        AWSRateLimiter.reset()

    def teardown_method(self):
        AWSRateLimiter.reset()

    def test_basic_decoration(self):
        call_count = 0

        @rate_limited("ec2", region_from_arg="region")
        def mock_api_call(region: str):
            nonlocal call_count
            call_count += 1
            return f"result-{region}"

        result = mock_api_call(region="us-east-1")

        assert result == "result-us-east-1"
        assert call_count == 1

    def test_retry_on_throttle(self):
        from botocore.exceptions import ClientError

        call_count = 0

        @rate_limited("ec2", max_retries=2)
        def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ClientError(
                    {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
                    "DescribeInstances",
                )
            return "success"

        result = mock_api_call()

        assert result == "success"
        assert call_count == 2


class TestConcurrentAccess:
    def setup_method(self):
        AWSRateLimiter.reset()

    def teardown_method(self):
        AWSRateLimiter.reset()

    def test_thread_safety(self):
        """Verify rate limiter is thread-safe"""
        limiter = AWSRateLimiter()
        results = []
        errors = []

        def worker(worker_id: int):
            try:
                for _ in range(10):
                    if limiter.acquire("ec2", "us-east-1", timeout=5):
                        limiter.report_success("ec2", "us-east-1")
                        results.append(worker_id)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(results) == 50  # 5 workers * 10 requests


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
