"""
Cost Trend Analyzer.

Analyzes historical cost data to identify trends, anomalies,
and provide forecasting for AWS spending.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any

from replimap.cost.explorer import (
    CostDataPoint,
    CostExplorerClient,
    CostExplorerResults,
    Granularity,
    GroupByDimension,
)

logger = logging.getLogger(__name__)


class TrendDirection(str, Enum):
    """Direction of cost trend."""

    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

    def __str__(self) -> str:
        return self.value


class AnomalyType(str, Enum):
    """Types of cost anomalies."""

    SPIKE = "spike"  # Sudden increase
    DROP = "drop"  # Sudden decrease
    SUSTAINED_INCREASE = "sustained_increase"  # Gradual but consistent increase
    UNEXPECTED_SERVICE = "unexpected_service"  # New service with significant cost

    def __str__(self) -> str:
        return self.value


class SeasonalPattern(str, Enum):
    """Seasonal patterns in cost data."""

    WEEKLY = "weekly"  # Higher weekdays, lower weekends
    MONTHLY = "monthly"  # Month-end spikes
    NONE = "none"

    def __str__(self) -> str:
        return self.value


@dataclass
class TrendAnalysis:
    """Analysis of cost trend."""

    direction: TrendDirection
    slope: float  # Rate of change ($/day)
    r_squared: float  # Trend fit quality (0-1)
    confidence: str  # HIGH, MEDIUM, LOW

    # Predictions
    projected_monthly: float
    projected_annual: float

    # Change analysis
    period_change_pct: float
    period_change_amount: float

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "direction": str(self.direction),
            "slope_per_day": round(self.slope, 2),
            "trend_fit": round(self.r_squared, 3),
            "confidence": self.confidence,
            "projected_monthly": round(self.projected_monthly, 2),
            "projected_annual": round(self.projected_annual, 2),
            "period_change": {
                "percentage": round(self.period_change_pct, 1),
                "amount": round(self.period_change_amount, 2),
            },
        }


@dataclass
class CostAnomaly:
    """Detected cost anomaly."""

    anomaly_type: AnomalyType
    date: date
    expected_amount: float
    actual_amount: float
    deviation_pct: float
    severity: str  # HIGH, MEDIUM, LOW

    # Context
    affected_services: list[str] = field(default_factory=list)
    possible_causes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": str(self.anomaly_type),
            "date": self.date.isoformat(),
            "expected": round(self.expected_amount, 2),
            "actual": round(self.actual_amount, 2),
            "deviation_pct": round(self.deviation_pct, 1),
            "severity": self.severity,
            "affected_services": self.affected_services,
            "possible_causes": self.possible_causes,
        }


@dataclass
class ServiceTrend:
    """Cost trend for a specific service."""

    service: str
    current_monthly: float
    previous_monthly: float
    change_pct: float
    trend: TrendDirection
    contribution_pct: float  # Percentage of total cost

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "service": self.service,
            "current_monthly": round(self.current_monthly, 2),
            "previous_monthly": round(self.previous_monthly, 2),
            "change_pct": round(self.change_pct, 1),
            "trend": str(self.trend),
            "contribution_pct": round(self.contribution_pct, 1),
        }


@dataclass
class CostForecastResult:
    """Cost forecast with confidence intervals."""

    forecast_date: date
    mean_value: float
    lower_bound: float  # 80% confidence
    upper_bound: float
    method: str  # linear, exponential, seasonal

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "date": self.forecast_date.isoformat(),
            "mean": round(self.mean_value, 2),
            "lower_80": round(self.lower_bound, 2),
            "upper_80": round(self.upper_bound, 2),
            "method": self.method,
        }


@dataclass
class TrendReport:
    """Complete cost trend analysis report."""

    analysis_date: date
    period_start: date
    period_end: date
    account_id: str

    # Overall trends
    overall_trend: TrendAnalysis
    current_month_cost: float
    previous_month_cost: float
    month_over_month_change: float

    # Service trends
    service_trends: list[ServiceTrend] = field(default_factory=list)
    top_growing_services: list[ServiceTrend] = field(default_factory=list)
    top_declining_services: list[ServiceTrend] = field(default_factory=list)

    # Anomalies
    anomalies: list[CostAnomaly] = field(default_factory=list)

    # Forecast
    forecast: list[CostForecastResult] = field(default_factory=list)

    # Patterns
    seasonal_pattern: SeasonalPattern = SeasonalPattern.NONE

    # Insights
    insights: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "analysis_date": self.analysis_date.isoformat(),
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
            "account_id": self.account_id,
            "summary": {
                "current_month": round(self.current_month_cost, 2),
                "previous_month": round(self.previous_month_cost, 2),
                "month_over_month_change": round(self.month_over_month_change, 1),
            },
            "overall_trend": self.overall_trend.to_dict(),
            "service_trends": [st.to_dict() for st in self.service_trends],
            "top_growing": [st.to_dict() for st in self.top_growing_services],
            "top_declining": [st.to_dict() for st in self.top_declining_services],
            "anomalies": [a.to_dict() for a in self.anomalies],
            "forecast": [f.to_dict() for f in self.forecast],
            "seasonal_pattern": str(self.seasonal_pattern),
            "insights": self.insights,
            "warnings": self.warnings,
        }


class CostTrendAnalyzer:
    """
    Analyzes cost trends and detects anomalies.

    Uses historical cost data to identify spending patterns,
    forecast future costs, and detect unusual spending.
    """

    def __init__(
        self,
        region: str = "us-east-1",
        account_id: str = "",
        anomaly_threshold: float = 2.0,  # Standard deviations
    ) -> None:
        """
        Initialize analyzer.

        Args:
            region: AWS region
            account_id: AWS account ID
            anomaly_threshold: Number of standard deviations for anomaly detection
        """
        self.region = region
        self.account_id = account_id
        self.anomaly_threshold = anomaly_threshold
        self._ce_client: CostExplorerClient | None = None

    async def _get_ce_client(self) -> CostExplorerClient:
        """Get Cost Explorer client."""
        if self._ce_client is None:
            self._ce_client = CostExplorerClient(
                region=self.region,
                account_id=self.account_id,
            )
        return self._ce_client

    async def analyze(
        self,
        lookback_days: int = 90,
        forecast_days: int = 30,
    ) -> TrendReport:
        """
        Perform comprehensive trend analysis.

        Args:
            lookback_days: Days of historical data to analyze
            forecast_days: Days to forecast

        Returns:
            TrendReport with analysis results
        """
        today = date.today()
        start_date = today - timedelta(days=lookback_days)

        ce_client = await self._get_ce_client()

        # Get daily cost data
        daily_data = await ce_client.get_cost_and_usage(
            start_date=start_date,
            end_date=today,
            granularity=Granularity.DAILY,
        )

        # Get monthly data for comparison
        monthly_data = await ce_client.get_cost_and_usage(
            start_date=start_date,
            end_date=today,
            granularity=Granularity.MONTHLY,
        )

        # Get service breakdown
        service_data = await ce_client.get_cost_by_service(
            start_date=start_date,
            end_date=today,
            granularity=Granularity.MONTHLY,
        )

        # Analyze overall trend
        overall_trend = self._analyze_trend(daily_data.data_points)

        # Analyze service trends
        service_trends = self._analyze_service_trends(service_data)

        # Detect anomalies
        anomalies = self._detect_anomalies(daily_data.data_points)

        # Generate forecast
        forecast = self._generate_forecast(daily_data.data_points, forecast_days)

        # Detect seasonal patterns
        seasonal_pattern = self._detect_seasonality(daily_data.data_points)

        # Calculate month-over-month
        current_month = sum(
            dp.amount
            for dp in monthly_data.data_points
            if dp.start_date.month == today.month
        )
        previous_month = sum(
            dp.amount
            for dp in monthly_data.data_points
            if dp.start_date.month == (today.month - 1) or (today.month == 1 and dp.start_date.month == 12)
        )

        if previous_month > 0:
            mom_change = ((current_month - previous_month) / previous_month) * 100
        else:
            mom_change = 0

        # Generate insights
        insights = self._generate_insights(
            overall_trend,
            service_trends,
            anomalies,
            mom_change,
        )

        # Sort service trends
        top_growing = sorted(
            [st for st in service_trends if st.change_pct > 0],
            key=lambda x: x.change_pct,
            reverse=True,
        )[:5]

        top_declining = sorted(
            [st for st in service_trends if st.change_pct < 0],
            key=lambda x: x.change_pct,
        )[:5]

        return TrendReport(
            analysis_date=today,
            period_start=start_date,
            period_end=today,
            account_id=self.account_id,
            overall_trend=overall_trend,
            current_month_cost=current_month,
            previous_month_cost=previous_month,
            month_over_month_change=mom_change,
            service_trends=service_trends,
            top_growing_services=top_growing,
            top_declining_services=top_declining,
            anomalies=anomalies,
            forecast=forecast,
            seasonal_pattern=seasonal_pattern,
            insights=insights,
        )

    def _analyze_trend(self, data_points: list[CostDataPoint]) -> TrendAnalysis:
        """Analyze trend from data points."""
        if not data_points:
            return TrendAnalysis(
                direction=TrendDirection.STABLE,
                slope=0.0,
                r_squared=0.0,
                confidence="LOW",
                projected_monthly=0.0,
                projected_annual=0.0,
                period_change_pct=0.0,
                period_change_amount=0.0,
            )

        # Sort by date
        sorted_points = sorted(data_points, key=lambda x: x.start_date)

        # Extract values
        costs = [dp.amount for dp in sorted_points]
        n = len(costs)

        # Calculate linear regression
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = sum(costs) / n

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, costs))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)

        slope = numerator / denominator if denominator > 0 else 0

        # Calculate R-squared
        y_pred = [y_mean + slope * (x - x_mean) for x in x_vals]
        ss_res = sum((y - yp) ** 2 for y, yp in zip(costs, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in costs)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

        # Determine direction
        if abs(slope) < 0.01 * y_mean:  # Less than 1% change per day
            direction = TrendDirection.STABLE
        elif slope > 0:
            direction = TrendDirection.INCREASING
        else:
            direction = TrendDirection.DECREASING

        # Check for volatility
        std_dev = (sum((y - y_mean) ** 2 for y in costs) / n) ** 0.5
        cv = std_dev / y_mean if y_mean > 0 else 0
        if cv > 0.5:  # High coefficient of variation
            direction = TrendDirection.VOLATILE

        # Calculate confidence
        if r_squared > 0.8:
            confidence = "HIGH"
        elif r_squared > 0.5:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        # Project future costs
        daily_avg = y_mean + slope * 15  # 15 days ahead
        projected_monthly = daily_avg * 30
        projected_annual = projected_monthly * 12

        # Calculate period change
        if costs[0] > 0:
            period_change_pct = ((costs[-1] - costs[0]) / costs[0]) * 100
        else:
            period_change_pct = 0
        period_change_amount = costs[-1] - costs[0]

        return TrendAnalysis(
            direction=direction,
            slope=slope,
            r_squared=r_squared,
            confidence=confidence,
            projected_monthly=projected_monthly,
            projected_annual=projected_annual,
            period_change_pct=period_change_pct,
            period_change_amount=period_change_amount,
        )

    def _analyze_service_trends(
        self,
        service_data: CostExplorerResults,
    ) -> list[ServiceTrend]:
        """Analyze trends per service."""
        trends = []

        for grouped_cost in service_data.grouped_costs:
            service = grouped_cost.group_value
            data_points = grouped_cost.data_points

            if len(data_points) < 2:
                continue

            # Sort by date
            sorted_points = sorted(data_points, key=lambda x: x.start_date)

            # Get current and previous month
            current = sorted_points[-1].amount if sorted_points else 0
            previous = sorted_points[-2].amount if len(sorted_points) > 1 else current

            # Calculate change
            if previous > 0:
                change_pct = ((current - previous) / previous) * 100
            else:
                change_pct = 0 if current == 0 else 100

            # Determine trend
            if abs(change_pct) < 5:
                trend = TrendDirection.STABLE
            elif change_pct > 0:
                trend = TrendDirection.INCREASING
            else:
                trend = TrendDirection.DECREASING

            # Calculate contribution
            total = service_data.total_cost
            contribution = (grouped_cost.total / total * 100) if total > 0 else 0

            trends.append(
                ServiceTrend(
                    service=service,
                    current_monthly=current,
                    previous_monthly=previous,
                    change_pct=change_pct,
                    trend=trend,
                    contribution_pct=contribution,
                )
            )

        # Sort by current cost
        trends.sort(key=lambda x: x.current_monthly, reverse=True)
        return trends

    def _detect_anomalies(
        self,
        data_points: list[CostDataPoint],
    ) -> list[CostAnomaly]:
        """Detect cost anomalies."""
        anomalies: list[CostAnomaly] = []

        if len(data_points) < 7:  # Need enough data for statistics
            return anomalies

        costs = [dp.amount for dp in data_points]

        # Calculate rolling statistics
        window_size = 7
        for i in range(window_size, len(costs)):
            window = costs[i - window_size : i]
            mean = sum(window) / len(window)
            variance = sum((x - mean) ** 2 for x in window) / len(window)
            std_dev = variance ** 0.5

            current = costs[i]
            deviation = (current - mean) / std_dev if std_dev > 0 else 0

            if abs(deviation) > self.anomaly_threshold:
                # Determine anomaly type
                if deviation > 0:
                    anomaly_type = AnomalyType.SPIKE
                else:
                    anomaly_type = AnomalyType.DROP

                # Determine severity
                if abs(deviation) > 3:
                    severity = "HIGH"
                elif abs(deviation) > 2.5:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"

                anomalies.append(
                    CostAnomaly(
                        anomaly_type=anomaly_type,
                        date=data_points[i].start_date,
                        expected_amount=mean,
                        actual_amount=current,
                        deviation_pct=(current - mean) / mean * 100 if mean > 0 else 0,
                        severity=severity,
                        possible_causes=[
                            "New resource deployment" if deviation > 0 else "Resource termination",
                            "Pricing change",
                            "Usage spike" if deviation > 0 else "Reduced usage",
                        ],
                    )
                )

        return anomalies

    def _generate_forecast(
        self,
        data_points: list[CostDataPoint],
        forecast_days: int,
    ) -> list[CostForecastResult]:
        """Generate cost forecast."""
        if len(data_points) < 7:
            return []

        forecasts = []
        costs = [dp.amount for dp in sorted(data_points, key=lambda x: x.start_date)]
        last_date = data_points[-1].end_date

        # Calculate trend
        n = len(costs)
        x_mean = (n - 1) / 2
        y_mean = sum(costs) / n

        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(costs))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        slope = numerator / denominator if denominator > 0 else 0

        # Calculate standard error
        y_pred = [y_mean + slope * (i - x_mean) for i in range(n)]
        mse = sum((y - yp) ** 2 for y, yp in zip(costs, y_pred)) / n
        std_error = mse ** 0.5

        # Generate forecasts
        for day in range(1, forecast_days + 1):
            forecast_date = last_date + timedelta(days=day)
            predicted = y_mean + slope * (n + day - x_mean)

            # Confidence interval (80%)
            margin = 1.28 * std_error * (1 + day / n) ** 0.5  # Wider as we go further

            forecasts.append(
                CostForecastResult(
                    forecast_date=forecast_date,
                    mean_value=max(0, predicted),
                    lower_bound=max(0, predicted - margin),
                    upper_bound=predicted + margin,
                    method="linear",
                )
            )

        return forecasts

    def _detect_seasonality(
        self,
        data_points: list[CostDataPoint],
    ) -> SeasonalPattern:
        """Detect seasonal patterns in cost data."""
        if len(data_points) < 14:  # Need at least 2 weeks
            return SeasonalPattern.NONE

        # Group by day of week
        day_costs: dict[int, list[float]] = {i: [] for i in range(7)}

        for dp in data_points:
            day_of_week = dp.start_date.weekday()
            day_costs[day_of_week].append(dp.amount)

        # Calculate average for weekdays vs weekends
        weekday_avg = sum(
            sum(day_costs[i]) / len(day_costs[i])
            for i in range(5)
            if day_costs[i]
        ) / 5

        weekend_avg = sum(
            sum(day_costs[i]) / len(day_costs[i])
            for i in range(5, 7)
            if day_costs[i]
        ) / 2

        # Check for weekly pattern
        if weekday_avg > 0 and weekend_avg > 0:
            ratio = weekday_avg / weekend_avg
            if ratio > 1.2 or ratio < 0.8:  # 20% difference
                return SeasonalPattern.WEEKLY

        return SeasonalPattern.NONE

    def _generate_insights(
        self,
        trend: TrendAnalysis,
        service_trends: list[ServiceTrend],
        anomalies: list[CostAnomaly],
        mom_change: float,
    ) -> list[str]:
        """Generate insights from analysis."""
        insights = []

        # Trend insights
        if trend.direction == TrendDirection.INCREASING:
            insights.append(
                f"Costs are trending upward at ${trend.slope:.2f}/day "
                f"(projected ${trend.projected_monthly:.0f}/month)"
            )
        elif trend.direction == TrendDirection.DECREASING:
            insights.append(
                f"Costs are trending downward, saving ${abs(trend.slope):.2f}/day"
            )
        elif trend.direction == TrendDirection.VOLATILE:
            insights.append(
                "Cost patterns show high volatility - consider investigating variability"
            )

        # Month-over-month
        if abs(mom_change) > 20:
            direction = "increased" if mom_change > 0 else "decreased"
            insights.append(
                f"Month-over-month spending has {direction} by {abs(mom_change):.1f}%"
            )

        # Service insights
        growing_services = [s for s in service_trends if s.change_pct > 50 and s.current_monthly > 100]
        for service in growing_services[:3]:
            insights.append(
                f"{service.service} costs increased {service.change_pct:.0f}% "
                f"(${service.previous_monthly:.0f} -> ${service.current_monthly:.0f})"
            )

        # Anomaly insights
        high_anomalies = [a for a in anomalies if a.severity == "HIGH"]
        if high_anomalies:
            insights.append(
                f"Detected {len(high_anomalies)} significant cost anomalies requiring attention"
            )

        return insights


async def get_cost_trend_summary(
    analyzer: CostTrendAnalyzer,
    days: int = 30,
) -> dict[str, Any]:
    """
    Get a quick cost trend summary.

    Args:
        analyzer: CostTrendAnalyzer instance
        days: Days to analyze

    Returns:
        Summary dictionary
    """
    report = await analyzer.analyze(lookback_days=days, forecast_days=7)

    return {
        "trend": str(report.overall_trend.direction),
        "current_month": round(report.current_month_cost, 2),
        "mom_change_pct": round(report.month_over_month_change, 1),
        "projected_monthly": round(report.overall_trend.projected_monthly, 2),
        "anomaly_count": len(report.anomalies),
        "top_insight": report.insights[0] if report.insights else None,
    }
