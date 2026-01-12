"""Integration tests for scanner rate limiting"""

import inspect

import pytest

from replimap.core.rate_limiter import AWSRateLimiter


class TestScannerRateLimitingIntegration:
    """Test that all scanners properly integrate with rate limiting"""

    def setup_method(self):
        AWSRateLimiter.reset()

    def teardown_method(self):
        AWSRateLimiter.reset()

    def test_ec2_scanner_uses_rate_limiting(self):
        """Verify EC2Scanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.ec2_scanner import EC2Scanner

        source = inspect.getsource(EC2Scanner)
        assert "rate_limited_paginate" in source, (
            "EC2Scanner should use rate_limited_paginate"
        )

    def test_vpc_scanner_uses_rate_limiting(self):
        """Verify VPCScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.vpc_scanner import VPCScanner

        source = inspect.getsource(VPCScanner)
        assert "rate_limited_paginate" in source, (
            "VPCScanner should use rate_limited_paginate"
        )
        # VPC scanner has 4 paginators
        assert source.count("rate_limited_paginate") >= 4

    def test_rds_scanner_uses_rate_limiting(self):
        """Verify RDSScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.rds_scanner import RDSScanner

        source = inspect.getsource(RDSScanner)
        assert "rate_limited_paginate" in source, (
            "RDSScanner should use rate_limited_paginate"
        )
        # RDS scanner has 2 paginators
        assert source.count("rate_limited_paginate") >= 2

    def test_iam_scanner_uses_rate_limiting(self):
        """Verify IAM scanners use rate_limited_paginate"""
        import inspect

        from replimap.scanners.iam_scanner import IAMRoleScanner

        source = inspect.getsource(IAMRoleScanner)
        assert "rate_limited_paginate" in source, (
            "IAMRoleScanner should use rate_limited_paginate"
        )

    def test_compute_scanner_uses_rate_limiting(self):
        """Verify ComputeScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.compute_scanner import ComputeScanner

        source = inspect.getsource(ComputeScanner)
        assert "rate_limited_paginate" in source, (
            "ComputeScanner should use rate_limited_paginate"
        )
        # Compute scanner has 4 paginators
        assert source.count("rate_limited_paginate") >= 4

    def test_networking_scanner_uses_rate_limiting(self):
        """Verify NetworkingScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.networking_scanner import NetworkingScanner

        source = inspect.getsource(NetworkingScanner)
        assert "rate_limited_paginate" in source, (
            "NetworkingScanner should use rate_limited_paginate"
        )
        # Networking scanner has 5 paginators
        assert source.count("rate_limited_paginate") >= 5

    def test_storage_scanner_uses_rate_limiting(self):
        """Verify StorageScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.storage_scanner import EBSScanner

        source = inspect.getsource(EBSScanner)
        assert "rate_limited_paginate" in source, (
            "EBSScanner should use rate_limited_paginate"
        )

    def test_elasticache_scanner_uses_rate_limiting(self):
        """Verify ElastiCacheScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.elasticache_scanner import ElastiCacheScanner

        source = inspect.getsource(ElastiCacheScanner)
        assert "rate_limited_paginate" in source, (
            "ElastiCacheScanner should use rate_limited_paginate"
        )

    def test_messaging_scanner_uses_rate_limiting(self):
        """Verify MessagingScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.messaging_scanner import SNSScanner, SQSScanner

        sqs_source = inspect.getsource(SQSScanner)
        sns_source = inspect.getsource(SNSScanner)
        assert "rate_limited_paginate" in sqs_source, (
            "SQSScanner should use rate_limited_paginate"
        )
        assert "rate_limited_paginate" in sns_source, (
            "SNSScanner should use rate_limited_paginate"
        )

    def test_monitoring_scanner_uses_rate_limiting(self):
        """Verify MonitoringScanner uses rate_limited_paginate"""
        import inspect

        from replimap.scanners.monitoring_scanner import CloudWatchLogGroupScanner

        source = inspect.getsource(CloudWatchLogGroupScanner)
        assert "rate_limited_paginate" in source, (
            "CloudWatchLogGroupScanner should use rate_limited_paginate"
        )

    def test_all_scanners_have_rate_limiter_import(self):
        """Verify all scanners import rate_limited_paginate"""
        scanner_modules = [
            "replimap.scanners.ec2_scanner",
            "replimap.scanners.vpc_scanner",
            "replimap.scanners.rds_scanner",
            "replimap.scanners.iam_scanner",
            "replimap.scanners.compute_scanner",
            "replimap.scanners.networking_scanner",
            "replimap.scanners.storage_scanner",
            "replimap.scanners.elasticache_scanner",
            "replimap.scanners.messaging_scanner",
            "replimap.scanners.monitoring_scanner",
            "replimap.scanners.s3_scanner",
        ]

        missing_imports = []
        for module_name in scanner_modules:
            try:
                import importlib

                module = importlib.import_module(module_name)
                source = inspect.getsource(module)
                if "from replimap.core.rate_limiter import" not in source:
                    missing_imports.append(module_name)
            except Exception as e:
                pytest.fail(f"Failed to check {module_name}: {e}")

        assert len(missing_imports) == 0, (
            f"Scanners missing rate_limiter import: {missing_imports}"
        )

    def test_rate_limiter_creates_correct_buckets_for_services(self):
        """Verify rate limiter creates appropriate buckets for scanner services"""
        limiter = AWSRateLimiter()

        # Test regional services
        ec2_bucket = limiter.get_bucket("ec2", "us-east-1")
        assert ec2_bucket.name == "us-east-1:ec2"

        rds_bucket = limiter.get_bucket("rds", "us-east-1")
        assert rds_bucket.name == "us-east-1:rds"

        # Test global services
        iam_bucket = limiter.get_bucket("iam", "us-east-1")
        assert iam_bucket.name == "global:iam"

        s3_bucket = limiter.get_bucket("s3", "us-east-1")
        assert s3_bucket.name == "global:s3"

    def test_scanner_service_limits_configured(self):
        """Verify all scanner services have rate limits configured"""
        from replimap.core.rate_limiter import DEFAULT_SERVICE_LIMITS

        scanner_services = [
            "ec2",
            "rds",
            "iam",
            "s3",
            "elbv2",
            "autoscaling",
            "elasticache",
            "sqs",
            "sns",
            "cloudwatch",
            "logs",
        ]

        missing_limits = []
        for service in scanner_services:
            if service not in DEFAULT_SERVICE_LIMITS:
                missing_limits.append(service)

        assert len(missing_limits) == 0, (
            f"Services missing rate limits: {missing_limits}"
        )


class TestRateLimitingCoverage:
    """Test rate limiting coverage across all scanners"""

    def test_sync_scanner_coverage(self):
        """Verify 100% sync scanner coverage"""
        import glob

        scanner_dir = "replimap/scanners"
        sync_scanners = glob.glob(f"{scanner_dir}/*_scanner.py")
        # Exclude async scanners
        sync_scanners = [s for s in sync_scanners if "async" not in s]

        scanners_with_rate_limiting = []
        scanners_without_rate_limiting = []

        for scanner_file in sync_scanners:
            with open(scanner_file) as f:
                content = f.read()
                # Check for any rate limiting usage: paginators, decorators, or direct limiter
                if (
                    "rate_limited_paginate" in content
                    or "rate_limited" in content
                    or "get_limiter" in content
                ):
                    scanners_with_rate_limiting.append(scanner_file)
                else:
                    scanners_without_rate_limiting.append(scanner_file)

        coverage = len(scanners_with_rate_limiting) / len(sync_scanners) * 100

        print(f"\nRate Limiting Coverage: {coverage:.1f}%")
        print(
            f"Scanners with rate limiting: {len(scanners_with_rate_limiting)}/{len(sync_scanners)}"
        )

        if scanners_without_rate_limiting:
            print("Scanners without rate limiting:")
            for scanner in scanners_without_rate_limiting:
                print(f"  ❌ {scanner}")

        assert coverage == 100.0, f"Expected 100% coverage, got {coverage:.1f}%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
