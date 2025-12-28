"""
AWS Cost Explorer Integration.

Provides async access to AWS Cost Explorer API for retrieving
actual cost data, usage patterns, and cost forecasts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any

from replimap.core.async_aws import AsyncAWSClient

logger = logging.getLogger(__name__)


class Granularity(str, Enum):
    """Cost data granularity."""

    DAILY = "DAILY"
    MONTHLY = "MONTHLY"
    HOURLY = "HOURLY"

    def __str__(self) -> str:
        return self.value


class MetricType(str, Enum):
    """Cost metric types."""

    BLENDED_COST = "BlendedCost"
    UNBLENDED_COST = "UnblendedCost"
    AMORTIZED_COST = "AmortizedCost"
    NET_AMORTIZED_COST = "NetAmortizedCost"
    NET_UNBLENDED_COST = "NetUnblendedCost"
    USAGE_QUANTITY = "UsageQuantity"
    NORMALIZED_USAGE_AMOUNT = "NormalizedUsageAmount"

    def __str__(self) -> str:
        return self.value


class GroupByDimension(str, Enum):
    """Dimensions for grouping cost data."""

    SERVICE = "SERVICE"
    REGION = "REGION"
    LINKED_ACCOUNT = "LINKED_ACCOUNT"
    USAGE_TYPE = "USAGE_TYPE"
    INSTANCE_TYPE = "INSTANCE_TYPE"
    RESOURCE_ID = "RESOURCE_ID"
    OPERATION = "OPERATION"
    PURCHASE_TYPE = "PURCHASE_TYPE"

    def __str__(self) -> str:
        return self.value


@dataclass
class CostDataPoint:
    """Single cost data point."""

    start_date: date
    end_date: date
    amount: float
    unit: str = "USD"
    estimated: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "amount": round(self.amount, 2),
            "unit": self.unit,
            "estimated": self.estimated,
        }


@dataclass
class GroupedCost:
    """Cost data grouped by a dimension."""

    group_key: str
    group_value: str
    data_points: list[CostDataPoint] = field(default_factory=list)
    total: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "group_key": self.group_key,
            "group_value": self.group_value,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "total": round(self.total, 2),
        }


@dataclass
class CostForecast:
    """Cost forecast data."""

    start_date: date
    end_date: date
    mean_value: float
    prediction_interval_lower: float
    prediction_interval_upper: float
    unit: str = "USD"
    confidence_level: float = 80.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "mean_value": round(self.mean_value, 2),
            "prediction_interval": {
                "lower": round(self.prediction_interval_lower, 2),
                "upper": round(self.prediction_interval_upper, 2),
            },
            "unit": self.unit,
            "confidence_level": self.confidence_level,
        }


@dataclass
class CostExplorerResults:
    """Results from Cost Explorer queries."""

    start_date: date
    end_date: date
    granularity: Granularity
    metric: MetricType

    # Cost data
    data_points: list[CostDataPoint] = field(default_factory=list)
    grouped_costs: list[GroupedCost] = field(default_factory=list)

    # Totals
    total_cost: float = 0.0
    average_daily: float = 0.0

    # Forecast (if requested)
    forecast: CostForecast | None = None

    # Metadata
    account_id: str = ""
    query_timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        result: dict[str, Any] = {
            "period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat(),
            },
            "granularity": str(self.granularity),
            "metric": str(self.metric),
            "total_cost": round(self.total_cost, 2),
            "average_daily": round(self.average_daily, 2),
            "data_points": [dp.to_dict() for dp in self.data_points],
            "account_id": self.account_id,
            "query_timestamp": self.query_timestamp.isoformat(),
        }

        if self.grouped_costs:
            result["grouped_costs"] = [gc.to_dict() for gc in self.grouped_costs]

        if self.forecast:
            result["forecast"] = self.forecast.to_dict()

        return result


class CostExplorerClient:
    """
    Async client for AWS Cost Explorer API.

    Provides methods for retrieving cost and usage data,
    forecasts, and cost allocation information.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
    ) -> None:
        """
        Initialize Cost Explorer client.

        Args:
            region: AWS region (Cost Explorer is global, but client needs region)
            account_id: AWS account ID for filtering
        """
        self.region = region
        self.account_id = account_id
        self._client: AsyncAWSClient | None = None

    async def _get_client(self) -> AsyncAWSClient:
        """Get or create async AWS client."""
        if self._client is None:
            self._client = AsyncAWSClient(region=self.region)
        return self._client

    async def get_cost_and_usage(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity = Granularity.DAILY,
        metrics: list[MetricType] | None = None,
        group_by: list[GroupByDimension] | None = None,
        filter_expression: dict[str, Any] | None = None,
    ) -> CostExplorerResults:
        """
        Get cost and usage data from Cost Explorer.

        Args:
            start_date: Start of the time period
            end_date: End of the time period
            granularity: Data granularity (DAILY, MONTHLY, HOURLY)
            metrics: Metrics to retrieve (defaults to UnblendedCost)
            group_by: Dimensions to group by
            filter_expression: Optional filter expression

        Returns:
            CostExplorerResults with cost data
        """
        client = await self._get_client()

        if metrics is None:
            metrics = [MetricType.UNBLENDED_COST]

        params: dict[str, Any] = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Granularity": str(granularity),
            "Metrics": [str(m) for m in metrics],
        }

        if group_by:
            params["GroupBy"] = [
                {"Type": "DIMENSION", "Key": str(dim)} for dim in group_by
            ]

        if filter_expression:
            params["Filter"] = filter_expression

        try:
            response = await client.call("ce", "get_cost_and_usage", **params)
            return self._parse_cost_response(
                response, start_date, end_date, granularity, metrics[0]
            )
        except Exception as e:
            logger.error(f"Failed to get cost data: {e}")
            raise

    async def get_cost_by_service(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity = Granularity.MONTHLY,
    ) -> CostExplorerResults:
        """
        Get costs grouped by AWS service.

        Args:
            start_date: Start of the time period
            end_date: End of the time period
            granularity: Data granularity

        Returns:
            CostExplorerResults with service-level costs
        """
        return await self.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            group_by=[GroupByDimension.SERVICE],
        )

    async def get_cost_by_region(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity = Granularity.MONTHLY,
    ) -> CostExplorerResults:
        """
        Get costs grouped by AWS region.

        Args:
            start_date: Start of the time period
            end_date: End of the time period
            granularity: Data granularity

        Returns:
            CostExplorerResults with region-level costs
        """
        return await self.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            group_by=[GroupByDimension.REGION],
        )

    async def get_cost_by_resource(
        self,
        start_date: date,
        end_date: date,
        resource_ids: list[str] | None = None,
    ) -> CostExplorerResults:
        """
        Get costs grouped by resource ID.

        Note: Resource-level data requires Cost Allocation Tags
        to be enabled in AWS Cost Management.

        Args:
            start_date: Start of the time period
            end_date: End of the time period
            resource_ids: Optional filter for specific resource IDs

        Returns:
            CostExplorerResults with resource-level costs
        """
        filter_expr: dict[str, Any] | None = None
        if resource_ids:
            filter_expr = {
                "Dimensions": {
                    "Key": "RESOURCE_ID",
                    "Values": resource_ids,
                }
            }

        return await self.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=Granularity.DAILY,
            group_by=[GroupByDimension.RESOURCE_ID],
            filter_expression=filter_expr,
        )

    async def get_cost_forecast(
        self,
        start_date: date,
        end_date: date,
        granularity: Granularity = Granularity.MONTHLY,
        metric: MetricType = MetricType.UNBLENDED_COST,
        prediction_interval: int = 80,
    ) -> CostForecast:
        """
        Get cost forecast from Cost Explorer.

        Args:
            start_date: Start of forecast period (must be in future)
            end_date: End of forecast period
            granularity: Forecast granularity
            metric: Cost metric to forecast
            prediction_interval: Confidence level (50-99)

        Returns:
            CostForecast with predicted costs
        """
        client = await self._get_client()

        params = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Metric": str(metric),
            "Granularity": str(granularity),
            "PredictionIntervalLevel": prediction_interval,
        }

        try:
            response = await client.call("ce", "get_cost_forecast", **params)
            return self._parse_forecast_response(
                response, start_date, end_date, prediction_interval
            )
        except Exception as e:
            logger.error(f"Failed to get cost forecast: {e}")
            raise

    async def get_monthly_spend(self, months: int = 6) -> CostExplorerResults:
        """
        Get monthly spending for the past N months.

        Args:
            months: Number of months to retrieve

        Returns:
            CostExplorerResults with monthly costs
        """
        today = date.today()
        start_date = date(today.year, today.month, 1) - timedelta(days=months * 30)
        start_date = date(start_date.year, start_date.month, 1)  # First of month
        end_date = date(today.year, today.month, 1)  # First of current month

        return await self.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=Granularity.MONTHLY,
        )

    async def get_current_month_cost(self) -> CostExplorerResults:
        """
        Get cost for the current month to date.

        Returns:
            CostExplorerResults with current month costs
        """
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = today + timedelta(days=1)  # Tomorrow (exclusive)

        return await self.get_cost_and_usage(
            start_date=start_date,
            end_date=end_date,
            granularity=Granularity.DAILY,
        )

    async def get_yesterday_cost(self) -> CostExplorerResults:
        """
        Get cost for yesterday.

        Returns:
            CostExplorerResults with yesterday's costs
        """
        today = date.today()
        yesterday = today - timedelta(days=1)

        return await self.get_cost_and_usage(
            start_date=yesterday,
            end_date=today,
            granularity=Granularity.DAILY,
        )

    def _parse_cost_response(
        self,
        response: dict[str, Any],
        start_date: date,
        end_date: date,
        granularity: Granularity,
        metric: MetricType,
    ) -> CostExplorerResults:
        """Parse Cost Explorer response into results object."""
        results = CostExplorerResults(
            start_date=start_date,
            end_date=end_date,
            granularity=granularity,
            metric=metric,
            account_id=self.account_id,
        )

        results_by_time = response.get("ResultsByTime", [])
        grouped_data: dict[str, list[CostDataPoint]] = {}

        for result in results_by_time:
            period = result.get("TimePeriod", {})
            period_start = date.fromisoformat(period.get("Start", ""))
            period_end = date.fromisoformat(period.get("End", ""))
            estimated = result.get("Estimated", False)

            # Handle ungrouped data
            if "Total" in result:
                total = result["Total"]
                metric_data = total.get(str(metric), {})
                amount = float(metric_data.get("Amount", 0))
                unit = metric_data.get("Unit", "USD")

                dp = CostDataPoint(
                    start_date=period_start,
                    end_date=period_end,
                    amount=amount,
                    unit=unit,
                    estimated=estimated,
                )
                results.data_points.append(dp)
                results.total_cost += amount

            # Handle grouped data
            if "Groups" in result:
                for group in result["Groups"]:
                    keys = group.get("Keys", [])
                    group_key = keys[0] if keys else "Unknown"

                    metrics_data = group.get("Metrics", {})
                    metric_data = metrics_data.get(str(metric), {})
                    amount = float(metric_data.get("Amount", 0))
                    unit = metric_data.get("Unit", "USD")

                    dp = CostDataPoint(
                        start_date=period_start,
                        end_date=period_end,
                        amount=amount,
                        unit=unit,
                        estimated=estimated,
                    )

                    if group_key not in grouped_data:
                        grouped_data[group_key] = []
                    grouped_data[group_key].append(dp)
                    results.total_cost += amount

        # Convert grouped data to GroupedCost objects
        for key, data_points in grouped_data.items():
            total = sum(dp.amount for dp in data_points)
            gc = GroupedCost(
                group_key="SERVICE",  # Default, could be parameterized
                group_value=key,
                data_points=data_points,
                total=total,
            )
            results.grouped_costs.append(gc)

        # Sort grouped costs by total (descending)
        results.grouped_costs.sort(key=lambda x: x.total, reverse=True)

        # Calculate average daily
        days = (end_date - start_date).days
        if days > 0:
            results.average_daily = results.total_cost / days

        return results

    def _parse_forecast_response(
        self,
        response: dict[str, Any],
        start_date: date,
        end_date: date,
        prediction_interval: int,
    ) -> CostForecast:
        """Parse forecast response into CostForecast object."""
        total = response.get("Total", {})
        mean_value = float(total.get("Amount", 0))
        unit = total.get("Unit", "USD")

        # Get prediction intervals from forecast results
        forecast_results = response.get("ForecastResultsByTime", [])
        lower_bound = 0.0
        upper_bound = 0.0

        for result in forecast_results:
            intervals = result.get("PredictionIntervalLowerBound", "0")
            lower_bound += float(intervals)
            intervals = result.get("PredictionIntervalUpperBound", "0")
            upper_bound += float(intervals)

        return CostForecast(
            start_date=start_date,
            end_date=end_date,
            mean_value=mean_value,
            prediction_interval_lower=lower_bound,
            prediction_interval_upper=upper_bound,
            unit=unit,
            confidence_level=float(prediction_interval),
        )


async def get_cost_comparison(
    client: CostExplorerClient,
    current_start: date,
    current_end: date,
    previous_start: date,
    previous_end: date,
) -> dict[str, Any]:
    """
    Compare costs between two periods.

    Args:
        client: CostExplorerClient instance
        current_start: Start of current period
        current_end: End of current period
        previous_start: Start of previous period
        previous_end: End of previous period

    Returns:
        Dictionary with comparison data
    """
    current = await client.get_cost_and_usage(current_start, current_end)
    previous = await client.get_cost_and_usage(previous_start, previous_end)

    change = current.total_cost - previous.total_cost
    change_pct = (change / previous.total_cost * 100) if previous.total_cost > 0 else 0

    return {
        "current_period": {
            "start": current_start.isoformat(),
            "end": current_end.isoformat(),
            "total": round(current.total_cost, 2),
        },
        "previous_period": {
            "start": previous_start.isoformat(),
            "end": previous_end.isoformat(),
            "total": round(previous.total_cost, 2),
        },
        "change": {
            "amount": round(change, 2),
            "percentage": round(change_pct, 1),
            "direction": "increase" if change > 0 else "decrease" if change < 0 else "unchanged",
        },
    }
