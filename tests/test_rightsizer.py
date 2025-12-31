"""
Unit tests for Right-Sizer engines.

Tests both the local rule-based engine and the hybrid API + local fallback.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from replimap.cost.local_rightsizer import (
    LocalRecommendation,
    LocalRightSizer,
    OptimizationStrategy,
)
from replimap.cost.rightsizer import (
    DowngradeStrategy,
    ResourceSummary,
    RightSizerClient,
)


class TestLocalRightSizer:
    """Tests for local rule-based right-sizer."""

    def test_ec2_conservative_downsize(self) -> None:
        """Conservative strategy suggests safe downsizes."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-123", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        assert recs[0].current_instance == "m5.2xlarge"
        assert recs[0].recommended_instance == "m5.xlarge"
        assert recs[0].confidence >= 0.8

    def test_ec2_aggressive_downsize(self) -> None:
        """Aggressive strategy suggests bigger downsizes."""
        sizer = LocalRightSizer(OptimizationStrategy.AGGRESSIVE)
        resources = [
            {"id": "i-123", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        assert recs[0].recommended_instance == "t3.large"
        assert recs[0].confidence < 0.7  # Lower confidence for aggressive

    def test_unknown_instance_type_no_recommendation(self) -> None:
        """Unknown instance types return no recommendation."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-123", "resource_type": "aws_instance", "instance_type": "x99.unknown"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 0

    def test_rds_downsize(self) -> None:
        """RDS instances get right-size recommendations."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "mydb", "resource_type": "aws_db_instance", "instance_type": "db.r5.xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        assert recs[0].resource_type == "aws_db_instance"
        assert recs[0].recommended_instance == "db.r5.large"

    def test_elasticache_downsize(self) -> None:
        """ElastiCache nodes get right-size recommendations."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "redis-cluster", "resource_type": "aws_elasticache_cluster", "instance_type": "cache.r5.large"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        assert recs[0].resource_type == "aws_elasticache_cluster"
        # Conservative: cache.r5 -> cache.r6g (Graviton)
        assert recs[0].recommended_instance == "cache.r6g.large"

    def test_savings_calculation(self) -> None:
        """Monthly savings calculated correctly."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-123", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert recs[0].monthly_savings > 0
        # m5.2xlarge ($0.384) -> m5.xlarge ($0.192) = $0.192/hr * 730hr = ~$140/mo
        assert 100 < recs[0].monthly_savings < 200

    def test_annual_savings_is_12x_monthly(self) -> None:
        """Annual savings should be 12x monthly."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-123", "resource_type": "aws_instance", "instance_type": "m5.xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert recs[0].annual_savings == recs[0].monthly_savings * 12

    def test_multiple_resources_sorted_by_savings(self) -> None:
        """Recommendations sorted by savings descending."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-1", "resource_type": "aws_instance", "instance_type": "m5.large"},
            {"id": "i-2", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"},
        ]

        recs = sizer.analyze(resources)

        # m5.2xlarge has bigger savings, should be first
        assert recs[0].monthly_savings >= recs[1].monthly_savings

    def test_t3_to_t3a_downgrade(self) -> None:
        """T3 to T3a (AMD) is a conservative optimization."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-1", "resource_type": "aws_instance", "instance_type": "t3.large"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        assert recs[0].recommended_instance == "t3a.large"
        assert recs[0].confidence >= 0.9  # High confidence for T3->T3a

    def test_get_total_savings(self) -> None:
        """Total savings calculation works correctly."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)
        resources = [
            {"id": "i-1", "resource_type": "aws_instance", "instance_type": "m5.xlarge"},
            {"id": "i-2", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"},
        ]

        recs = sizer.analyze(resources)
        totals = sizer.get_total_savings(recs)

        assert totals["resource_count"] == 2
        assert totals["monthly_savings"] > 0
        assert totals["annual_savings"] == totals["monthly_savings"] * 12
        assert 0 <= totals["average_confidence"] <= 1

    def test_empty_resources_returns_empty(self) -> None:
        """Empty resources list returns empty recommendations."""
        sizer = LocalRightSizer(OptimizationStrategy.CONSERVATIVE)

        recs = sizer.analyze([])

        assert len(recs) == 0

    def test_balanced_strategy(self) -> None:
        """Balanced strategy provides middle-ground recommendations."""
        sizer = LocalRightSizer(OptimizationStrategy.BALANCED)
        resources = [
            {"id": "i-1", "resource_type": "aws_instance", "instance_type": "m5.2xlarge"}
        ]

        recs = sizer.analyze(resources)

        assert len(recs) == 1
        # Balanced is more aggressive than conservative
        assert recs[0].recommended_instance in ("t3.xlarge", "m5.xlarge")


class TestRightSizerClient:
    """Tests for hybrid API + local right-sizer client."""

    def test_prefer_local_skips_api(self) -> None:
        """prefer_local=True uses local engine directly."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert client.last_source == "local"
        assert len(result.suggestions) > 0

    def test_no_resources_returns_error(self) -> None:
        """Empty resources list returns error result."""
        client = RightSizerClient(prefer_local=True)

        result = client.get_suggestions([], DowngradeStrategy.CONSERVATIVE)

        assert result.success is False
        assert "No rightsizable resources" in (result.error_message or "")

    def test_local_result_has_suggestions(self) -> None:
        """Local engine provides valid suggestions."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert len(result.suggestions) == 1
        assert result.suggestions[0].original_type == "m5.2xlarge"
        assert result.suggestions[0].recommended_type == "m5.xlarge"

    def test_local_result_includes_savings(self) -> None:
        """Local result includes savings calculations."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.total_monthly_savings > 0
        assert result.total_annual_savings == result.total_monthly_savings * 12

    def test_unknown_instance_returns_skipped(self) -> None:
        """Unknown instance types are marked as skipped."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-999",
                resource_type="aws_instance",
                instance_type="z99.mega",  # Unknown type
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert len(result.suggestions) == 0
        assert len(result.skipped) == 1

    @patch("replimap.cost.rightsizer.RightSizerClient._get_license_key")
    def test_no_license_falls_back_to_local(self, mock_license: MagicMock) -> None:
        """No license key triggers local fallback."""
        mock_license.return_value = None
        client = RightSizerClient(prefer_local=False)

        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert client.last_source == "local"

    def test_aggressive_strategy_local(self) -> None:
        """Aggressive strategy works with local engine."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.AGGRESSIVE)

        assert result.success is True
        assert result.strategy_used == "aggressive"
        # Aggressive should suggest t3.large
        assert result.suggestions[0].recommended_type == "t3.large"

    def test_rds_suggestions_local(self) -> None:
        """RDS instances work with local engine."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="mydb",
                resource_type="aws_db_instance",
                instance_type="db.r5.xlarge",
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert len(result.suggestions) == 1
        assert result.suggestions[0].resource_type == "aws_db_instance"

    def test_mixed_resources_local(self) -> None:
        """Multiple resource types work together."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.xlarge",
                region="us-east-1",
            ),
            ResourceSummary(
                resource_id="mydb",
                resource_type="aws_db_instance",
                instance_type="db.m5.large",
                region="us-east-1",
            ),
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.success is True
        assert len(result.suggestions) == 2

    def test_confidence_levels_in_result(self) -> None:
        """Confidence levels are correctly mapped."""
        client = RightSizerClient(prefer_local=True)
        resources = [
            ResourceSummary(
                resource_id="i-123",
                resource_type="aws_instance",
                instance_type="m5.2xlarge",  # Has 0.85 confidence
                region="us-east-1",
            )
        ]

        result = client.get_suggestions(resources, DowngradeStrategy.CONSERVATIVE)

        assert result.suggestions[0].confidence in ("high", "medium", "low")


class TestRightSizerAPIFallback:
    """Tests for API fallback behavior."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_timeout_falls_back_to_local(self, mock_client: MagicMock) -> None:
        """API timeout gracefully falls back to local."""
        import httpx

        # Simulate timeout
        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.post.side_effect = httpx.TimeoutException("timeout")
        mock_client.return_value = mock_async_client

        client = RightSizerClient(prefer_local=False)
        # Mock license key
        with patch.object(client, "_get_license_key", return_value="test-key"):
            resources = [
                ResourceSummary(
                    resource_id="i-123",
                    resource_type="aws_instance",
                    instance_type="m5.2xlarge",
                    region="us-east-1",
                )
            ]

            result = await client.get_suggestions_async(
                resources, DowngradeStrategy.CONSERVATIVE
            )

            assert result.success is True
            assert client.last_source == "local"
            assert len(result.suggestions) > 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_500_falls_back_to_local(self, mock_client: MagicMock) -> None:
        """API 500 error gracefully falls back to local."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}

        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.post.return_value = mock_response
        mock_client.return_value = mock_async_client

        client = RightSizerClient(prefer_local=False)
        with patch.object(client, "_get_license_key", return_value="test-key"):
            resources = [
                ResourceSummary(
                    resource_id="i-123",
                    resource_type="aws_instance",
                    instance_type="m5.2xlarge",
                    region="us-east-1",
                )
            ]

            result = await client.get_suggestions_async(
                resources, DowngradeStrategy.CONSERVATIVE
            )

            # Should fallback to local on 500
            assert result.success is True
            assert client.last_source == "local"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_401_does_not_fallback(self, mock_client: MagicMock) -> None:
        """API 401 (auth error) should NOT fallback - it's a user issue."""
        mock_response = MagicMock()
        mock_response.status_code = 401

        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.post.return_value = mock_response
        mock_client.return_value = mock_async_client

        client = RightSizerClient(prefer_local=False)
        with patch.object(client, "_get_license_key", return_value="test-key"):
            resources = [
                ResourceSummary(
                    resource_id="i-123",
                    resource_type="aws_instance",
                    instance_type="m5.2xlarge",
                    region="us-east-1",
                )
            ]

            result = await client.get_suggestions_async(
                resources, DowngradeStrategy.CONSERVATIVE
            )

            # Should NOT fallback on auth error
            assert result.success is False
            assert "Invalid or expired license" in (result.error_message or "")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_api_success_returns_api_result(self, mock_client: MagicMock) -> None:
        """Successful API call returns API results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "suggestions": [
                {
                    "resource_id": "i-123",
                    "resource_type": "aws_instance",
                    "current": {"instance_type": "m5.2xlarge", "monthly_cost": 280.32},
                    "recommended": {"instance_type": "t3.medium", "monthly_cost": 30.37},
                    "monthly_savings": 249.95,
                    "annual_savings": 2999.40,
                    "savings_percentage": 89.2,
                    "savings_breakdown": {"instance": 249.95, "storage": 0, "multi_az": 0},
                    "confidence": "high",
                }
            ],
            "skipped": [],
            "summary": {
                "total_resources": 1,
                "resources_with_suggestions": 1,
                "resources_skipped": 0,
                "total_current_monthly": 280.32,
                "total_recommended_monthly": 30.37,
                "total_monthly_savings": 249.95,
                "total_annual_savings": 2999.40,
                "savings_percentage": 89.2,
                "savings_breakdown": {"instance": 249.95, "storage": 0, "multi_az": 0},
            },
            "strategy_used": "conservative",
        }

        mock_async_client = AsyncMock()
        mock_async_client.__aenter__.return_value = mock_async_client
        mock_async_client.__aexit__.return_value = None
        mock_async_client.post.return_value = mock_response
        mock_client.return_value = mock_async_client

        client = RightSizerClient(prefer_local=False)
        with patch.object(client, "_get_license_key", return_value="test-key"):
            resources = [
                ResourceSummary(
                    resource_id="i-123",
                    resource_type="aws_instance",
                    instance_type="m5.2xlarge",
                    region="us-east-1",
                )
            ]

            result = await client.get_suggestions_async(
                resources, DowngradeStrategy.CONSERVATIVE
            )

            assert result.success is True
            assert client.last_source == "api"
            assert len(result.suggestions) == 1
            assert result.suggestions[0].recommended_type == "t3.medium"
            assert result.total_monthly_savings == 249.95
