"""
CasareRPA Infrastructure: Aggregation Strategies

Strategy pattern implementations for different aggregation types:
- Time-based aggregation (hourly, daily, weekly)
- Statistical aggregation (mean, median, percentiles)
- Dimensional aggregation (by robot, workflow, node)
- Rolling window aggregation
"""

from __future__ import annotations

import statistics
from abc import ABC, abstractmethod
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Generic, TypeVar

T = TypeVar("T")
V = TypeVar("V")


class AggregationPeriod(str, Enum):
    """Time period for metrics aggregation."""

    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


@dataclass
class TimeSeriesDataPoint:
    """Single data point in a time series."""

    timestamp: datetime
    value: float
    count: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": round(self.value, 2),
            "count": self.count,
            "metadata": self.metadata,
        }


class AggregationStrategy(ABC, Generic[T, V]):
    """Base class for aggregation strategies."""

    @abstractmethod
    def aggregate(self, data: list[T]) -> V:
        """Aggregate data according to strategy."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state."""
        pass


class TimeBasedAggregationStrategy(AggregationStrategy[dict[str, Any], list[TimeSeriesDataPoint]]):
    """
    Aggregates metrics over time periods.

    Groups data points by time buckets (hour, day, week, etc.)
    and calculates aggregate values for each bucket.
    """

    PERIOD_DELTAS = {
        AggregationPeriod.HOUR: timedelta(hours=1),
        AggregationPeriod.DAY: timedelta(days=1),
        AggregationPeriod.WEEK: timedelta(weeks=1),
        AggregationPeriod.MONTH: timedelta(days=30),
        AggregationPeriod.QUARTER: timedelta(days=90),
        AggregationPeriod.YEAR: timedelta(days=365),
    }

    def __init__(
        self,
        period: AggregationPeriod = AggregationPeriod.HOUR,
        value_field: str = "value",
        timestamp_field: str = "timestamp",
        max_buckets: int = 168,  # 7 days of hourly data
    ):
        """
        Initialize time-based aggregation.

        Args:
            period: Time period for bucketing.
            value_field: Field name for numeric value.
            timestamp_field: Field name for timestamp.
            max_buckets: Maximum number of time buckets to retain.
        """
        self.period = period
        self.value_field = value_field
        self.timestamp_field = timestamp_field
        self.max_buckets = max_buckets
        self._buckets: dict[datetime, list[float]] = defaultdict(list)

    def _truncate_to_period(self, dt: datetime) -> datetime:
        """Truncate datetime to period boundary."""
        if self.period == AggregationPeriod.HOUR:
            return dt.replace(minute=0, second=0, microsecond=0)
        elif self.period == AggregationPeriod.DAY:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == AggregationPeriod.WEEK:
            start_of_week = dt - timedelta(days=dt.weekday())
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period == AggregationPeriod.MONTH:
            return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == AggregationPeriod.QUARTER:
            quarter_month = ((dt.month - 1) // 3) * 3 + 1
            return dt.replace(month=quarter_month, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == AggregationPeriod.YEAR:
            return dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        return dt

    def add_data_point(self, record: dict[str, Any]) -> None:
        """
        Add a single data point to aggregation.

        Args:
            record: Data record with timestamp and value fields.
        """
        timestamp = record.get(self.timestamp_field)
        value = record.get(self.value_field)

        if timestamp is None or value is None:
            return

        bucket = self._truncate_to_period(timestamp)
        self._buckets[bucket].append(float(value))

        # Prune old buckets
        if len(self._buckets) > self.max_buckets:
            sorted_keys = sorted(self._buckets.keys())
            for key in sorted_keys[: len(sorted_keys) - self.max_buckets]:
                del self._buckets[key]

    def aggregate(self, data: list[dict[str, Any]]) -> list[TimeSeriesDataPoint]:
        """
        Aggregate data into time series.

        Args:
            data: List of records to aggregate.

        Returns:
            List of TimeSeriesDataPoint objects.
        """
        for record in data:
            self.add_data_point(record)

        return self.get_time_series()

    def get_time_series(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[TimeSeriesDataPoint]:
        """
        Get aggregated time series.

        Args:
            start_time: Filter start time.
            end_time: Filter end time.
            limit: Maximum points to return.

        Returns:
            List of TimeSeriesDataPoint objects.
        """
        result = []

        for bucket, values in sorted(self._buckets.items()):
            if start_time and bucket < start_time:
                continue
            if end_time and bucket > end_time:
                continue

            if values:
                avg_value = sum(values) / len(values)
                result.append(
                    TimeSeriesDataPoint(
                        timestamp=bucket,
                        value=avg_value,
                        count=len(values),
                    )
                )

        return result[-limit:] if len(result) > limit else result

    def reset(self) -> None:
        """Reset aggregation state."""
        self._buckets.clear()


@dataclass
class StatisticalResult:
    """Result of statistical aggregation."""

    count: int = 0
    min_value: float = 0.0
    max_value: float = 0.0
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    p50: float = 0.0
    p75: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    p99: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "count": self.count,
            "min": round(self.min_value, 2),
            "max": round(self.max_value, 2),
            "mean": round(self.mean, 2),
            "median": round(self.median, 2),
            "std_dev": round(self.std_dev, 2),
            "p50": round(self.p50, 2),
            "p75": round(self.p75, 2),
            "p90": round(self.p90, 2),
            "p95": round(self.p95, 2),
            "p99": round(self.p99, 2),
        }


class StatisticalAggregationStrategy(AggregationStrategy[float, StatisticalResult]):
    """
    Computes statistical measures from numeric data.

    Calculates mean, median, standard deviation, and percentiles.
    """

    def __init__(self, max_samples: int = 10000):
        """
        Initialize statistical aggregation.

        Args:
            max_samples: Maximum samples to retain for calculation.
        """
        self.max_samples = max_samples
        self._values: list[float] = []

    def add_value(self, value: float) -> None:
        """Add a single value."""
        self._values.append(value)
        if len(self._values) > self.max_samples:
            self._values = self._values[-self.max_samples :]

    @staticmethod
    def percentile(sorted_data: list[float], p: float) -> float:
        """
        Calculate percentile value.

        Args:
            sorted_data: Sorted list of values.
            p: Percentile (0-100).

        Returns:
            Percentile value.
        """
        if not sorted_data:
            return 0.0

        n = len(sorted_data)
        k = (n - 1) * (p / 100.0)
        f = int(k)
        c = f + 1 if f + 1 < n else f
        d = k - f

        return sorted_data[f] + d * (sorted_data[c] - sorted_data[f]) if c != f else sorted_data[f]

    def aggregate(self, data: list[float]) -> StatisticalResult:
        """
        Compute statistics from data.

        Args:
            data: List of numeric values.

        Returns:
            StatisticalResult with all metrics.
        """
        self._values.extend(data)
        if len(self._values) > self.max_samples:
            self._values = self._values[-self.max_samples :]

        return self.get_statistics()

    def get_statistics(self) -> StatisticalResult:
        """
        Get current statistics.

        Returns:
            StatisticalResult with all metrics.
        """
        if not self._values:
            return StatisticalResult()

        sorted_values = sorted(self._values)
        n = len(sorted_values)

        mean = statistics.mean(sorted_values)
        std_dev = statistics.stdev(sorted_values) if n > 1 else 0.0

        return StatisticalResult(
            count=n,
            min_value=sorted_values[0],
            max_value=sorted_values[-1],
            mean=mean,
            median=statistics.median(sorted_values),
            std_dev=std_dev,
            p50=self.percentile(sorted_values, 50),
            p75=self.percentile(sorted_values, 75),
            p90=self.percentile(sorted_values, 90),
            p95=self.percentile(sorted_values, 95),
            p99=self.percentile(sorted_values, 99),
        )

    def reset(self) -> None:
        """Reset aggregation state."""
        self._values.clear()


@dataclass
class DimensionalBucket:
    """A bucket for dimensional aggregation."""

    dimension_key: str
    count: int = 0
    sum_value: float = 0.0
    min_value: float = float("inf")
    max_value: float = float("-inf")
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def avg_value(self) -> float:
        """Calculate average value."""
        return self.sum_value / self.count if self.count > 0 else 0.0

    def add(self, value: float) -> None:
        """Add a value to the bucket."""
        self.count += 1
        self.sum_value += value
        self.min_value = min(self.min_value, value)
        self.max_value = max(self.max_value, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dimension_key": self.dimension_key,
            "count": self.count,
            "sum": round(self.sum_value, 2),
            "avg": round(self.avg_value, 2),
            "min": round(self.min_value, 2) if self.min_value != float("inf") else 0.0,
            "max": round(self.max_value, 2) if self.max_value != float("-inf") else 0.0,
            "metadata": self.metadata,
        }


class DimensionalAggregationStrategy(
    AggregationStrategy[dict[str, Any], dict[str, DimensionalBucket]]
):
    """
    Aggregates metrics by dimension (robot, workflow, node, etc.).

    Groups data by a dimension field and calculates aggregates per group.
    """

    def __init__(
        self,
        dimension_field: str,
        value_field: str = "value",
        name_field: str | None = None,
    ):
        """
        Initialize dimensional aggregation.

        Args:
            dimension_field: Field name for grouping dimension.
            value_field: Field name for numeric value.
            name_field: Optional field for dimension display name.
        """
        self.dimension_field = dimension_field
        self.value_field = value_field
        self.name_field = name_field
        self._buckets: dict[str, DimensionalBucket] = {}

    def add_record(self, record: dict[str, Any]) -> None:
        """
        Add a record to aggregation.

        Args:
            record: Data record with dimension and value fields.
        """
        dimension_key = record.get(self.dimension_field)
        value = record.get(self.value_field)

        if dimension_key is None or value is None:
            return

        dimension_key = str(dimension_key)

        if dimension_key not in self._buckets:
            self._buckets[dimension_key] = DimensionalBucket(
                dimension_key=dimension_key,
                metadata={
                    "name": record.get(self.name_field, dimension_key)
                    if self.name_field
                    else dimension_key
                },
            )

        self._buckets[dimension_key].add(float(value))

    def aggregate(self, data: list[dict[str, Any]]) -> dict[str, DimensionalBucket]:
        """
        Aggregate data by dimension.

        Args:
            data: List of records to aggregate.

        Returns:
            Dictionary of dimension key to bucket.
        """
        for record in data:
            self.add_record(record)

        return self._buckets.copy()

    def get_top_dimensions(self, n: int = 10, by: str = "count") -> list[DimensionalBucket]:
        """
        Get top N dimensions by metric.

        Args:
            n: Number of top dimensions.
            by: Metric to sort by (count, sum, avg).

        Returns:
            List of top DimensionalBucket objects.
        """

        def get_sum(b: DimensionalBucket) -> float:
            return b.sum_value

        def get_avg(b: DimensionalBucket) -> float:
            return b.avg_value

        def get_count(b: DimensionalBucket) -> float:
            return float(b.count)

        key_func: Callable[[DimensionalBucket], float]
        if by == "sum":
            key_func = get_sum
        elif by == "avg":
            key_func = get_avg
        else:  # count
            key_func = get_count

        sorted_buckets = sorted(self._buckets.values(), key=key_func, reverse=True)
        return sorted_buckets[:n]

    def reset(self) -> None:
        """Reset aggregation state."""
        self._buckets.clear()


@dataclass
class RollingWindowResult:
    """Result of rolling window aggregation."""

    window_size: int
    current_count: int
    current_sum: float
    current_avg: float
    trend: str  # "increasing", "decreasing", "stable"
    change_rate: float  # Percentage change over window

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "window_size": self.window_size,
            "current_count": self.current_count,
            "current_sum": round(self.current_sum, 2),
            "current_avg": round(self.current_avg, 2),
            "trend": self.trend,
            "change_rate": round(self.change_rate, 2),
        }


class RollingWindowAggregationStrategy(AggregationStrategy[float, RollingWindowResult]):
    """
    Aggregates values over a rolling time window.

    Maintains a sliding window of values for real-time metrics.
    """

    def __init__(
        self,
        window_size: int = 100,
        trend_threshold: float = 5.0,
    ):
        """
        Initialize rolling window aggregation.

        Args:
            window_size: Number of values in the window.
            trend_threshold: Percentage change threshold for trend detection.
        """
        self.window_size = window_size
        self.trend_threshold = trend_threshold
        self._values: list[float] = []

    def add_value(self, value: float) -> None:
        """
        Add a value to the window.

        Args:
            value: Numeric value to add.
        """
        self._values.append(value)
        if len(self._values) > self.window_size:
            self._values = self._values[-self.window_size :]

    def aggregate(self, data: list[float]) -> RollingWindowResult:
        """
        Aggregate values and return window result.

        Args:
            data: List of values to add.

        Returns:
            RollingWindowResult with current metrics.
        """
        for value in data:
            self.add_value(value)

        return self.get_result()

    def get_result(self) -> RollingWindowResult:
        """
        Get current rolling window result.

        Returns:
            RollingWindowResult with metrics.
        """
        if not self._values:
            return RollingWindowResult(
                window_size=self.window_size,
                current_count=0,
                current_sum=0.0,
                current_avg=0.0,
                trend="stable",
                change_rate=0.0,
            )

        current_sum = sum(self._values)
        current_avg = current_sum / len(self._values)

        # Calculate trend by comparing first and second half
        mid = len(self._values) // 2
        if mid > 0:
            first_half_avg = sum(self._values[:mid]) / mid
            second_half_avg = sum(self._values[mid:]) / (len(self._values) - mid)

            if first_half_avg > 0:
                change_rate = ((second_half_avg - first_half_avg) / first_half_avg) * 100
            else:
                change_rate = 0.0

            if abs(change_rate) < self.trend_threshold:
                trend = "stable"
            elif change_rate > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "stable"
            change_rate = 0.0

        return RollingWindowResult(
            window_size=self.window_size,
            current_count=len(self._values),
            current_sum=current_sum,
            current_avg=current_avg,
            trend=trend,
            change_rate=change_rate,
        )

    def reset(self) -> None:
        """Reset the window."""
        self._values.clear()


class AggregationStrategyFactory:
    """Factory for creating aggregation strategies."""

    @staticmethod
    def create_time_based(
        period: AggregationPeriod = AggregationPeriod.HOUR,
        value_field: str = "duration_ms",
        timestamp_field: str = "started_at",
    ) -> TimeBasedAggregationStrategy:
        """Create time-based aggregation strategy."""
        return TimeBasedAggregationStrategy(
            period=period,
            value_field=value_field,
            timestamp_field=timestamp_field,
        )

    @staticmethod
    def create_statistical(max_samples: int = 10000) -> StatisticalAggregationStrategy:
        """Create statistical aggregation strategy."""
        return StatisticalAggregationStrategy(max_samples=max_samples)

    @staticmethod
    def create_dimensional(
        dimension_field: str,
        value_field: str = "duration_ms",
        name_field: str | None = None,
    ) -> DimensionalAggregationStrategy:
        """Create dimensional aggregation strategy."""
        return DimensionalAggregationStrategy(
            dimension_field=dimension_field,
            value_field=value_field,
            name_field=name_field,
        )

    @staticmethod
    def create_rolling_window(
        window_size: int = 100,
        trend_threshold: float = 5.0,
    ) -> RollingWindowAggregationStrategy:
        """Create rolling window aggregation strategy."""
        return RollingWindowAggregationStrategy(
            window_size=window_size,
            trend_threshold=trend_threshold,
        )


__all__ = [
    # Enums and data classes
    "AggregationPeriod",
    "TimeSeriesDataPoint",
    "StatisticalResult",
    "DimensionalBucket",
    "RollingWindowResult",
    # Strategy classes
    "AggregationStrategy",
    "TimeBasedAggregationStrategy",
    "StatisticalAggregationStrategy",
    "DimensionalAggregationStrategy",
    "RollingWindowAggregationStrategy",
    # Factory
    "AggregationStrategyFactory",
]
