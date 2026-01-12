"""
Tests for Robust Pagination System.

Tests cover:
- Successful pagination (all pages succeed)
- Partial failure (middle page fails after retries)
- Throttling retry with backoff
- Fatal errors (AccessDenied) fail immediately
- Nested extraction (EC2 instances from Reservations)
- Stats accessible during iteration
- Early abort functionality
- Empty response handling
- Compound token pagination (Route53)
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from replimap.core.pagination import (
    FATAL_ERROR_CODES,
    RETRYABLE_ERROR_CODES,
    PaginationStats,
    PaginationStream,
    RobustPaginator,
)
from replimap.core.pagination_config import (
    PAGINATION_CONFIGS,
    PaginationConfig,
    get_pagination_config,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_rate_limiter() -> MagicMock:
    """Create a mock rate limiter that always succeeds."""
    limiter = MagicMock()
    limiter.acquire.return_value = True
    limiter.report_success.return_value = None
    limiter.report_throttle.return_value = None
    return limiter


@pytest.fixture
def mock_ec2_client() -> MagicMock:
    """Create a mock EC2 client."""
    client = MagicMock()
    client.meta.service_model.service_name = "ec2"
    client.meta.region_name = "us-east-1"
    client._service_name = "ec2"
    return client


@pytest.fixture
def mock_logs_client() -> MagicMock:
    """Create a mock CloudWatch Logs client."""
    client = MagicMock()
    client.meta.service_model.service_name = "logs"
    client.meta.region_name = "us-east-1"
    client._service_name = "logs"
    return client


@pytest.fixture
def mock_route53_client() -> MagicMock:
    """Create a mock Route53 client."""
    client = MagicMock()
    client.meta.service_model.service_name = "route53"
    client.meta.region_name = "us-east-1"
    client._service_name = "route53"
    return client


def make_client_error(
    error_code: str,
    error_message: str = "Test error",
) -> ClientError:
    """Create a ClientError with the specified error code."""
    return ClientError(
        error_response={
            "Error": {
                "Code": error_code,
                "Message": error_message,
            }
        },
        operation_name="TestOperation",
    )


# =============================================================================
# PaginationConfig Tests
# =============================================================================


class TestPaginationConfig:
    """Tests for pagination configuration."""

    def test_get_pagination_config_ec2(self) -> None:
        """Test getting EC2 pagination config."""
        config = get_pagination_config("ec2", "describe_instances")
        assert config is not None
        assert config.input_token == "NextToken"
        assert config.output_token == "NextToken"
        assert config.result_key == "Reservations"
        assert config.is_nested is True
        assert config.nested_key == "Instances"

    def test_get_pagination_config_logs_lowercase(self) -> None:
        """Test CloudWatch Logs uses lowercase tokens."""
        config = get_pagination_config("logs", "describe_log_groups")
        assert config is not None
        assert config.input_token == "nextToken"  # lowercase!
        assert config.output_token == "nextToken"
        assert config.result_key == "logGroups"

    def test_get_pagination_config_rds_marker(self) -> None:
        """Test RDS uses Marker pattern."""
        config = get_pagination_config("rds", "describe_db_instances")
        assert config is not None
        assert config.input_token == "Marker"
        assert config.limit_key == "MaxRecords"

    def test_get_pagination_config_s3_continuation(self) -> None:
        """Test S3 uses ContinuationToken pattern."""
        config = get_pagination_config("s3", "list_objects_v2")
        assert config is not None
        assert config.input_token == "ContinuationToken"
        assert config.output_token == "NextContinuationToken"

    def test_get_pagination_config_route53_compound(self) -> None:
        """Test Route53 uses compound tokens."""
        config = get_pagination_config("route53", "list_resource_record_sets")
        assert config is not None
        assert config.is_compound_token is True
        assert "StartRecordName" in config.compound_input_keys
        assert "NextRecordName" in config.compound_output_keys

    def test_get_pagination_config_unknown_returns_none(self) -> None:
        """Test unknown service/method returns None."""
        assert get_pagination_config("unknown", "method") is None
        assert get_pagination_config("ec2", "unknown_method") is None

    def test_pagination_config_coverage(self) -> None:
        """Verify all major services are covered."""
        required_services = [
            "ec2",
            "rds",
            "s3",
            "iam",
            "elbv2",
            "logs",
            "cloudwatch",
            "autoscaling",
            "lambda",
            "sqs",
            "sns",
            "elasticache",
            "route53",
        ]
        for service in required_services:
            assert service in PAGINATION_CONFIGS, f"Missing config for {service}"


# =============================================================================
# PaginationStats Tests
# =============================================================================


class TestPaginationStats:
    """Tests for pagination statistics."""

    def test_initial_state(self) -> None:
        """Test initial stats state."""
        stats = PaginationStats()
        assert stats.total_pages == 0
        assert stats.successful_pages == 0
        assert stats.failed_pages == 0
        assert stats.items_yielded == 0
        assert stats.errors == []
        assert stats.is_complete is True
        assert stats.success_rate == 1.0
        assert stats.has_errors is False

    def test_success_rate_calculation(self) -> None:
        """Test success rate with various page counts."""
        stats = PaginationStats(total_pages=10, successful_pages=9, failed_pages=1)
        assert stats.success_rate == 0.9

        stats = PaginationStats(total_pages=10, successful_pages=10, failed_pages=0)
        assert stats.success_rate == 1.0

        stats = PaginationStats(total_pages=10, successful_pages=0, failed_pages=10)
        assert stats.success_rate == 0.0

    def test_has_errors_with_errors_list(self) -> None:
        """Test has_errors detects errors in list."""
        stats = PaginationStats(errors=["Page 1: AccessDenied"])
        assert stats.has_errors is True

    def test_has_errors_with_failed_pages(self) -> None:
        """Test has_errors detects failed pages."""
        stats = PaginationStats(failed_pages=1)
        assert stats.has_errors is True


# =============================================================================
# RobustPaginator Tests - Success Scenarios
# =============================================================================


class TestSuccessfulPagination:
    """Tests for successful pagination scenarios."""

    @patch("time.sleep")
    def test_single_page(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test pagination with single page response."""
        mock_ec2_client.describe_vpcs.return_value = {
            "Vpcs": [{"VpcId": "vpc-1"}, {"VpcId": "vpc-2"}],
            # No NextToken means single page
        }

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 2
        assert items[0]["VpcId"] == "vpc-1"
        assert items[1]["VpcId"] == "vpc-2"
        assert stream.stats.total_pages == 1
        assert stream.stats.successful_pages == 1
        assert stream.stats.failed_pages == 0
        assert stream.stats.items_yielded == 2
        assert stream.stats.is_complete is True

    @patch("time.sleep")
    def test_multiple_pages(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test pagination with multiple pages."""
        mock_ec2_client.describe_vpcs.side_effect = [
            {"Vpcs": [{"VpcId": "vpc-1"}], "NextToken": "token-1"},
            {"Vpcs": [{"VpcId": "vpc-2"}], "NextToken": "token-2"},
            {"Vpcs": [{"VpcId": "vpc-3"}]},  # No NextToken - last page
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 3
        assert stream.stats.total_pages == 3
        assert stream.stats.successful_pages == 3
        assert stream.stats.items_yielded == 3

    @patch("time.sleep")
    def test_nested_extraction_ec2_instances(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test EC2 instances are extracted from nested Reservations."""
        mock_ec2_client.describe_instances.return_value = {
            "Reservations": [
                {
                    "ReservationId": "r-1",
                    "Instances": [
                        {"InstanceId": "i-1"},
                        {"InstanceId": "i-2"},
                    ],
                },
                {
                    "ReservationId": "r-2",
                    "Instances": [
                        {"InstanceId": "i-3"},
                    ],
                },
            ],
        }

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_instances",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        # Should yield 3 instances, not 2 reservations
        assert len(items) == 3
        assert items[0]["InstanceId"] == "i-1"
        assert items[1]["InstanceId"] == "i-2"
        assert items[2]["InstanceId"] == "i-3"
        assert stream.stats.items_yielded == 3

    @patch("time.sleep")
    def test_empty_response(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test handling of empty result lists."""
        mock_ec2_client.describe_vpcs.return_value = {
            "Vpcs": [],  # Empty list
        }

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 0
        assert stream.stats.total_pages == 1
        assert stream.stats.successful_pages == 1
        assert stream.stats.items_yielded == 0
        assert stream.stats.is_complete is True


# =============================================================================
# RobustPaginator Tests - Error Scenarios
# =============================================================================


class TestPartialFailure:
    """Tests for partial failure scenarios."""

    @patch("time.sleep")
    def test_middle_page_fails_after_retries(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test that middle page failure doesn't lose earlier data."""
        error = make_client_error("InternalError", "AWS had a bad day")

        # Page 1 succeeds, Page 2 fails repeatedly, stops pagination
        mock_ec2_client.describe_vpcs.side_effect = [
            {"Vpcs": [{"VpcId": "vpc-1"}, {"VpcId": "vpc-2"}], "NextToken": "token-1"},
            error,  # Attempt 1
            error,  # Attempt 2
            error,  # Attempt 3
            error,  # Attempt 4 - max retries exceeded
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
            max_retries=3,
        )
        stream = paginator.paginate()

        items = list(stream)

        # Should have items from first page
        assert len(items) == 2
        assert items[0]["VpcId"] == "vpc-1"

        # Stats should reflect partial success
        assert stream.stats.successful_pages == 1
        assert stream.stats.failed_pages == 1
        assert stream.stats.total_pages == 2
        assert stream.stats.is_complete is False
        assert len(stream.stats.errors) == 1
        assert "InternalError" in stream.stats.errors[0]

    @patch("time.sleep")
    def test_throttling_retry_with_backoff(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test throttling errors trigger retry with backoff."""
        throttle_error = make_client_error("Throttling")

        # First attempt throttled, second succeeds
        mock_ec2_client.describe_vpcs.side_effect = [
            throttle_error,
            {"Vpcs": [{"VpcId": "vpc-1"}]},
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
            max_retries=3,
            base_backoff=1.0,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 1
        assert stream.stats.is_complete is True

        # Should have slept for backoff
        mock_sleep.assert_called()
        # Throttling doubles backoff, so expect at least 2s
        assert mock_sleep.call_args[0][0] >= 2.0

        # Should have reported throttle to rate limiter
        mock_rate_limiter.report_throttle.assert_called()

    @patch("time.sleep")
    def test_access_denied_no_retry(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test AccessDenied fails immediately without retry."""
        error = make_client_error("AccessDenied", "You shall not pass")

        mock_ec2_client.describe_vpcs.side_effect = error

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
            max_retries=3,
        )
        stream = paginator.paginate()

        items = list(stream)

        # No items - first page failed
        assert len(items) == 0
        assert stream.stats.failed_pages == 1
        assert stream.stats.is_complete is False
        assert "AccessDenied" in stream.stats.errors[0]

        # Should only be called once (no retries)
        assert mock_ec2_client.describe_vpcs.call_count == 1

        # Should NOT sleep (no backoff for fatal errors)
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_rate_limiter_timeout(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test rate limiter timeout fails gracefully."""
        mock_rate_limiter.acquire.return_value = False  # Timeout

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 0
        assert stream.stats.failed_pages == 1
        assert stream.stats.is_complete is False
        assert "Rate limiter timeout" in stream.stats.errors[0]

        # API should not be called
        mock_ec2_client.describe_vpcs.assert_not_called()


# =============================================================================
# RobustPaginator Tests - Stream Control
# =============================================================================


class TestStreamControl:
    """Tests for stream iteration control."""

    @patch("time.sleep")
    def test_stats_accessible_during_iteration(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test stats can be read during iteration."""
        mock_ec2_client.describe_vpcs.side_effect = [
            {"Vpcs": [{"VpcId": f"vpc-{i}"} for i in range(10)], "NextToken": "token-1"},
            {"Vpcs": [{"VpcId": f"vpc-{i}"} for i in range(10, 20)]},
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items_seen = 0
        for item in stream:
            items_seen += 1
            # Can access stats mid-iteration
            assert stream.stats.items_yielded == items_seen

        assert stream.stats.items_yielded == 20

    @patch("time.sleep")
    def test_abort_early(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test stream.abort() stops iteration early."""
        mock_ec2_client.describe_vpcs.side_effect = [
            {"Vpcs": [{"VpcId": f"vpc-{i}"} for i in range(100)], "NextToken": "token-1"},
            {"Vpcs": [{"VpcId": f"vpc-{i}"} for i in range(100, 200)]},  # Never reached
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items_collected = []
        for item in stream:
            items_collected.append(item)
            if len(items_collected) >= 50:
                stream.abort()
                break

        assert len(items_collected) == 50
        assert stream.stats.is_complete is False

        # Should not have fetched second page
        assert mock_ec2_client.describe_vpcs.call_count == 1

    @patch("time.sleep")
    def test_is_exhausted(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test is_exhausted property."""
        mock_ec2_client.describe_vpcs.return_value = {
            "Vpcs": [{"VpcId": "vpc-1"}],
        }

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        assert stream.is_exhausted is False

        list(stream)

        assert stream.is_exhausted is True


# =============================================================================
# RobustPaginator Tests - Special Cases
# =============================================================================


class TestSpecialCases:
    """Tests for special pagination patterns."""

    @patch("time.sleep")
    def test_compound_token_route53(
        self,
        mock_sleep: MagicMock,
        mock_route53_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test Route53 compound token handling."""
        mock_route53_client.list_resource_record_sets.side_effect = [
            {
                "ResourceRecordSets": [{"Name": "example.com", "Type": "A"}],
                "IsTruncated": True,
                "NextRecordName": "example.org",
                "NextRecordType": "A",
            },
            {
                "ResourceRecordSets": [{"Name": "example.org", "Type": "A"}],
                "IsTruncated": False,
            },
        ]

        paginator = RobustPaginator(
            client=mock_route53_client,
            method_name="list_resource_record_sets",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate(HostedZoneId="Z123")

        items = list(stream)

        assert len(items) == 2
        assert stream.stats.total_pages == 2
        assert stream.stats.is_complete is True

        # Verify compound tokens were passed to second request
        calls = mock_route53_client.list_resource_record_sets.call_args_list
        assert len(calls) == 2
        second_call_kwargs = calls[1][1]
        assert second_call_kwargs.get("StartRecordName") == "example.org"
        assert second_call_kwargs.get("StartRecordType") == "A"

    @patch("time.sleep")
    def test_cloudwatch_logs_lowercase_tokens(
        self,
        mock_sleep: MagicMock,
        mock_logs_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test CloudWatch Logs lowercase token handling."""
        mock_logs_client.describe_log_groups.side_effect = [
            {
                "logGroups": [{"logGroupName": "/aws/lambda/func1"}],
                "nextToken": "token-1",  # lowercase!
            },
            {
                "logGroups": [{"logGroupName": "/aws/lambda/func2"}],
                # No nextToken - done
            },
        ]

        paginator = RobustPaginator(
            client=mock_logs_client,
            method_name="describe_log_groups",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 2
        assert stream.stats.total_pages == 2

        # Verify lowercase token was passed
        calls = mock_logs_client.describe_log_groups.call_args_list
        second_call_kwargs = calls[1][1]
        assert "nextToken" in second_call_kwargs  # lowercase
        assert second_call_kwargs["nextToken"] == "token-1"

    @patch("time.sleep")
    def test_no_rate_limiter(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
    ) -> None:
        """Test pagination works without rate limiter."""
        mock_ec2_client.describe_vpcs.return_value = {
            "Vpcs": [{"VpcId": "vpc-1"}],
        }

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_vpcs",
            rate_limiter=None,  # No rate limiter
        )
        stream = paginator.paginate()

        items = list(stream)

        assert len(items) == 1
        assert stream.stats.is_complete is True

    def test_unknown_method_raises_error(self, mock_ec2_client: MagicMock) -> None:
        """Test unknown method raises ValueError."""
        with pytest.raises(ValueError, match="No pagination config"):
            RobustPaginator(
                client=mock_ec2_client,
                method_name="unknown_method",
            )


# =============================================================================
# Error Code Coverage Tests
# =============================================================================


class TestErrorCodeCoverage:
    """Tests to verify error code classification."""

    def test_retryable_error_codes_coverage(self) -> None:
        """Verify all expected retryable error codes are covered."""
        expected = {
            "Throttling",
            "ThrottlingException",
            "RequestLimitExceeded",
            "TooManyRequestsException",
            "ServiceUnavailable",
            "InternalError",
        }
        assert expected.issubset(RETRYABLE_ERROR_CODES)

    def test_fatal_error_codes_coverage(self) -> None:
        """Verify all expected fatal error codes are covered."""
        expected = {
            "AccessDenied",
            "AccessDeniedException",
            "InvalidParameterValue",
            "ValidationException",
        }
        assert expected.issubset(FATAL_ERROR_CODES)


# =============================================================================
# Integration Tests
# =============================================================================


class TestPaginationIntegration:
    """Integration tests for complete pagination flow."""

    @patch("time.sleep")
    def test_full_scan_scenario(
        self,
        mock_sleep: MagicMock,
        mock_ec2_client: MagicMock,
        mock_rate_limiter: MagicMock,
    ) -> None:
        """Test a realistic multi-page scan scenario."""
        # Simulate: 3 pages of instances across 2 reservations each
        mock_ec2_client.describe_instances.side_effect = [
            {
                "Reservations": [
                    {"Instances": [{"InstanceId": f"i-{j}"} for j in range(5)]},
                    {"Instances": [{"InstanceId": f"i-{j+5}"} for j in range(5)]},
                ],
                "NextToken": "token-1",
            },
            {
                "Reservations": [
                    {"Instances": [{"InstanceId": f"i-{j+10}"} for j in range(5)]},
                ],
                "NextToken": "token-2",
            },
            {
                "Reservations": [
                    {"Instances": [{"InstanceId": f"i-{j+15}"} for j in range(3)]},
                ],
            },
        ]

        paginator = RobustPaginator(
            client=mock_ec2_client,
            method_name="describe_instances",
            rate_limiter=mock_rate_limiter,
        )
        stream = paginator.paginate()

        # Simulate building a resource list
        instances = []
        for instance in stream:
            instances.append(instance)

        # Verify all instances collected
        assert len(instances) == 18  # 10 + 5 + 3
        assert stream.stats.total_pages == 3
        assert stream.stats.successful_pages == 3
        assert stream.stats.items_yielded == 18
        assert stream.stats.is_complete is True
        assert stream.stats.success_rate == 1.0

        # Rate limiter should have been called for each page
        assert mock_rate_limiter.acquire.call_count == 3
        assert mock_rate_limiter.report_success.call_count == 3
