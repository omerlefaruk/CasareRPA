"""
CasareRPA - ROI Estimator

Score automation candidates by potential Return on Investment (ROI).
Estimates time savings, development costs, and payback periods.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.infrastructure.analytics.pattern_recognizer import RecognizedPattern


class ComplexityLevel(str, Enum):
    """Complexity level for automation development."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RecommendationLevel(str, Enum):
    """Recommendation level for automation."""

    HIGHLY_RECOMMENDED = "highly_recommended"
    RECOMMENDED = "recommended"
    CONSIDER = "consider"
    LOW_PRIORITY = "low_priority"
    NOT_RECOMMENDED = "not_recommended"


@dataclass
class ROIEstimate:
    """ROI estimation for an automation candidate."""

    pattern_id: str
    annual_hours_saved: float
    annual_cost_savings: float
    estimated_dev_hours: float
    payback_months: float
    roi_score: float  # 0-100
    recommendation: RecommendationLevel
    complexity: ComplexityLevel
    confidence: float  # 0-1, how confident is this estimate
    factors: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pattern_id": self.pattern_id,
            "annual_hours_saved": round(self.annual_hours_saved, 1),
            "annual_cost_savings": round(self.annual_cost_savings, 2),
            "estimated_dev_hours": round(self.estimated_dev_hours, 1),
            "payback_months": round(self.payback_months, 1),
            "roi_score": round(self.roi_score, 1),
            "recommendation": self.recommendation.value,
            "complexity": self.complexity.value,
            "confidence": round(self.confidence, 2),
            "factors": self.factors,
        }


@dataclass
class ROIConfig:
    """Configuration for ROI estimation."""

    hourly_labor_cost: float = 50.0  # Default hourly cost in USD
    automation_efficiency: float = 0.9  # Expected automation success rate
    maintenance_factor: float = 0.1  # Annual maintenance as % of dev cost
    hours_per_year: float = 2080.0  # Work hours per year
    dev_hours_per_activity: float = 2.0  # Base dev hours per activity in pattern
    complexity_multipliers: Dict[str, float] = field(
        default_factory=lambda: {
            "browser": 1.5,  # Browser automation more complex
            "desktop": 2.0,  # Desktop automation most complex
            "file": 1.0,
            "data": 0.8,
            "variable": 0.5,
            "control_flow": 1.0,
            "api": 1.2,
            "database": 1.5,
            "default": 1.0,
        }
    )


class ROIEstimator:
    """
    Estimate ROI for automation candidates.

    Calculates potential time savings, development costs,
    and payback periods for identified patterns.
    """

    def __init__(self, config: Optional[ROIConfig] = None) -> None:
        """
        Initialize ROI estimator.

        Args:
            config: Configuration for ROI calculations. Uses defaults if not provided.
        """
        self.config = config or ROIConfig()
        logger.debug(
            f"ROIEstimator initialized (hourly_cost=${self.config.hourly_labor_cost})"
        )

    def estimate_roi(
        self,
        pattern: RecognizedPattern,
        executions_per_year: Optional[int] = None,
    ) -> ROIEstimate:
        """
        Estimate ROI for automating a pattern.

        Args:
            pattern: Recognized pattern to estimate ROI for.
            executions_per_year: Override for annual execution count.
                If not provided, extrapolates from pattern frequency.

        Returns:
            ROIEstimate with calculated metrics.
        """
        # Calculate annual executions
        if executions_per_year is not None:
            annual_execs = executions_per_year
        else:
            # Extrapolate: assume frequency represents a sample period
            # Default assumption: 1 month of data
            annual_execs = pattern.frequency * 12

        # Time savings calculation
        manual_time_per_exec_hours = pattern.avg_duration / 3600000  # ms to hours
        automated_time_factor = 1 - self.config.automation_efficiency
        time_saved_per_exec = (
            manual_time_per_exec_hours * self.config.automation_efficiency
        )

        annual_hours_saved = time_saved_per_exec * annual_execs

        # Cost savings
        annual_cost_savings = annual_hours_saved * self.config.hourly_labor_cost

        # Development cost estimation
        complexity = self._estimate_complexity(pattern)
        dev_hours = self._estimate_dev_hours(pattern, complexity)

        # Payback calculation
        dev_cost = dev_hours * self.config.hourly_labor_cost
        annual_maintenance = dev_cost * self.config.maintenance_factor

        if annual_cost_savings > 0:
            # Simple payback: dev_cost / (annual_savings - annual_maintenance)
            net_annual_savings = annual_cost_savings - annual_maintenance
            if net_annual_savings > 0:
                payback_months = (dev_cost / net_annual_savings) * 12
            else:
                payback_months = float("inf")
        else:
            payback_months = float("inf")

        # ROI Score (0-100)
        roi_score = self._calculate_roi_score(
            annual_hours_saved=annual_hours_saved,
            payback_months=payback_months,
            pattern=pattern,
        )

        # Recommendation
        recommendation = self._determine_recommendation(
            roi_score=roi_score,
            payback_months=payback_months,
            pattern=pattern,
        )

        # Confidence (based on data quality)
        confidence = self._calculate_confidence(pattern, annual_execs)

        return ROIEstimate(
            pattern_id=pattern.pattern_id,
            annual_hours_saved=annual_hours_saved,
            annual_cost_savings=annual_cost_savings,
            estimated_dev_hours=dev_hours,
            payback_months=min(payback_months, 999.0),  # Cap for display
            roi_score=roi_score,
            recommendation=recommendation,
            complexity=complexity,
            confidence=confidence,
            factors={
                "annual_executions": annual_execs,
                "time_per_exec_hours": manual_time_per_exec_hours,
                "pattern_success_rate": pattern.success_rate,
                "pattern_variance": pattern.variance_score,
                "activity_count": len(pattern.activity_sequence),
                "dev_cost_usd": dev_cost,
                "annual_maintenance_usd": annual_maintenance,
            },
        )

    def estimate_batch(
        self,
        patterns: List[RecognizedPattern],
        executions_per_year: Optional[Dict[str, int]] = None,
    ) -> List[ROIEstimate]:
        """
        Estimate ROI for multiple patterns.

        Args:
            patterns: List of patterns to estimate.
            executions_per_year: Optional dict mapping pattern_id to annual executions.

        Returns:
            List of ROIEstimates sorted by ROI score (descending).
        """
        estimates = []
        exec_map = executions_per_year or {}

        for pattern in patterns:
            exec_count = exec_map.get(pattern.pattern_id)
            estimate = self.estimate_roi(pattern, exec_count)
            estimates.append(estimate)

        # Sort by ROI score descending
        estimates.sort(key=lambda e: e.roi_score, reverse=True)

        return estimates

    def _estimate_complexity(self, pattern: RecognizedPattern) -> ComplexityLevel:
        """Estimate development complexity based on pattern characteristics."""
        # Base complexity from activity count
        activity_count = len(pattern.activity_sequence)

        if activity_count <= 3:
            base_complexity = 1.0
        elif activity_count <= 6:
            base_complexity = 1.5
        elif activity_count <= 10:
            base_complexity = 2.0
        else:
            base_complexity = 2.5

        # Adjust for node types
        type_multipliers = []
        for node_type in pattern.node_types:
            node_category = self._categorize_node_type(node_type)
            mult = self.config.complexity_multipliers.get(
                node_category, self.config.complexity_multipliers["default"]
            )
            type_multipliers.append(mult)

        if type_multipliers:
            avg_type_mult = sum(type_multipliers) / len(type_multipliers)
        else:
            avg_type_mult = 1.0

        # Adjust for variance (high variance = harder to automate)
        variance_mult = 1.0 + pattern.variance_score * 0.5

        # Final complexity score
        complexity_score = base_complexity * avg_type_mult * variance_mult

        if complexity_score < 1.5:
            return ComplexityLevel.LOW
        elif complexity_score < 2.5:
            return ComplexityLevel.MEDIUM
        elif complexity_score < 4.0:
            return ComplexityLevel.HIGH
        else:
            return ComplexityLevel.VERY_HIGH

    def _estimate_dev_hours(
        self, pattern: RecognizedPattern, complexity: ComplexityLevel
    ) -> float:
        """Estimate development hours for automation."""
        base_hours = len(pattern.activity_sequence) * self.config.dev_hours_per_activity

        complexity_multipliers = {
            ComplexityLevel.LOW: 0.75,
            ComplexityLevel.MEDIUM: 1.0,
            ComplexityLevel.HIGH: 1.5,
            ComplexityLevel.VERY_HIGH: 2.5,
        }

        mult = complexity_multipliers.get(complexity, 1.0)

        # Additional hours for testing and debugging
        testing_hours = base_hours * 0.3

        # Additional hours for error handling if low success rate
        if pattern.success_rate < 0.95:
            error_handling_hours = base_hours * 0.2
        else:
            error_handling_hours = 0

        total_hours = (base_hours * mult) + testing_hours + error_handling_hours

        # Minimum 4 hours, maximum 200 hours
        return max(4.0, min(200.0, total_hours))

    def _categorize_node_type(self, node_type: str) -> str:
        """Categorize a node type for complexity estimation."""
        node_type_lower = node_type.lower()

        if any(
            kw in node_type_lower
            for kw in ["browser", "navigate", "click", "type", "page"]
        ):
            return "browser"
        elif any(
            kw in node_type_lower for kw in ["desktop", "window", "ui", "element"]
        ):
            return "desktop"
        elif any(
            kw in node_type_lower for kw in ["file", "read", "write", "csv", "excel"]
        ):
            return "file"
        elif any(kw in node_type_lower for kw in ["api", "http", "rest", "request"]):
            return "api"
        elif any(kw in node_type_lower for kw in ["database", "query", "sql"]):
            return "database"
        elif any(kw in node_type_lower for kw in ["variable", "set", "get"]):
            return "variable"
        elif any(
            kw in node_type_lower for kw in ["if", "loop", "for", "while", "switch"]
        ):
            return "control_flow"
        elif any(kw in node_type_lower for kw in ["data", "transform", "convert"]):
            return "data"
        else:
            return "default"

    def _calculate_roi_score(
        self,
        annual_hours_saved: float,
        payback_months: float,
        pattern: RecognizedPattern,
    ) -> float:
        """
        Calculate ROI score (0-100).

        Higher score = better ROI candidate.
        """
        # Time savings factor (0-40 points)
        # Max score at 500+ hours saved annually
        time_score = min(40.0, (annual_hours_saved / 500) * 40)

        # Payback factor (0-30 points)
        # Max score at 1 month payback, 0 at 24+ months
        if payback_months <= 1:
            payback_score = 30.0
        elif payback_months >= 24:
            payback_score = 0.0
        else:
            payback_score = 30.0 * (1 - (payback_months - 1) / 23)

        # Automation potential from pattern (0-20 points)
        potential_score = pattern.automation_potential * 20

        # Consistency factor (0-10 points)
        # Low variance = more consistent = better
        consistency_score = (1 - min(1.0, pattern.variance_score)) * 10

        total = time_score + payback_score + potential_score + consistency_score

        return max(0.0, min(100.0, total))

    def _determine_recommendation(
        self,
        roi_score: float,
        payback_months: float,
        pattern: RecognizedPattern,
    ) -> RecommendationLevel:
        """Determine recommendation level based on ROI metrics."""
        # Check for disqualifying factors
        if pattern.success_rate < 0.5:
            return RecommendationLevel.NOT_RECOMMENDED

        if payback_months > 36:
            return RecommendationLevel.NOT_RECOMMENDED

        # Score-based recommendation
        if roi_score >= 75:
            return RecommendationLevel.HIGHLY_RECOMMENDED
        elif roi_score >= 55:
            return RecommendationLevel.RECOMMENDED
        elif roi_score >= 35:
            return RecommendationLevel.CONSIDER
        elif roi_score >= 20:
            return RecommendationLevel.LOW_PRIORITY
        else:
            return RecommendationLevel.NOT_RECOMMENDED

    def _calculate_confidence(
        self, pattern: RecognizedPattern, annual_execs: int
    ) -> float:
        """
        Calculate confidence in the ROI estimate (0-1).

        Higher confidence when:
        - More data points (frequency)
        - Lower variance
        - Higher success rate
        """
        # Frequency factor (more data = more confidence)
        freq_confidence = min(1.0, pattern.frequency / 50)

        # Variance factor (lower variance = more predictable)
        variance_confidence = 1 - min(1.0, pattern.variance_score)

        # Success rate factor
        success_confidence = pattern.success_rate

        # Sample size for annual extrapolation
        if annual_execs >= 100:
            sample_confidence = 1.0
        elif annual_execs >= 50:
            sample_confidence = 0.8
        elif annual_execs >= 20:
            sample_confidence = 0.6
        else:
            sample_confidence = 0.4

        # Weighted average
        confidence = (
            freq_confidence * 0.3
            + variance_confidence * 0.25
            + success_confidence * 0.25
            + sample_confidence * 0.2
        )

        return confidence

    def generate_report(
        self,
        estimates: List[ROIEstimate],
        title: str = "Automation ROI Analysis",
    ) -> Dict[str, Any]:
        """
        Generate a summary report of ROI estimates.

        Args:
            estimates: List of ROI estimates.
            title: Report title.

        Returns:
            Dict with report data.
        """
        if not estimates:
            return {
                "title": title,
                "summary": {"total_candidates": 0},
                "estimates": [],
            }

        # Aggregate statistics
        total_annual_hours = sum(e.annual_hours_saved for e in estimates)
        total_annual_savings = sum(e.annual_cost_savings for e in estimates)
        total_dev_hours = sum(e.estimated_dev_hours for e in estimates)

        # Recommendation breakdown
        recommendation_counts = {}
        for level in RecommendationLevel:
            count = sum(1 for e in estimates if e.recommendation == level)
            if count > 0:
                recommendation_counts[level.value] = count

        # Complexity breakdown
        complexity_counts = {}
        for level in ComplexityLevel:
            count = sum(1 for e in estimates if e.complexity == level)
            if count > 0:
                complexity_counts[level.value] = count

        # Top candidates
        top_candidates = [
            e.to_dict()
            for e in estimates[:10]
            if e.recommendation
            in (
                RecommendationLevel.HIGHLY_RECOMMENDED,
                RecommendationLevel.RECOMMENDED,
            )
        ]

        return {
            "title": title,
            "summary": {
                "total_candidates": len(estimates),
                "total_annual_hours_saved": round(total_annual_hours, 1),
                "total_annual_cost_savings": round(total_annual_savings, 2),
                "total_dev_hours_needed": round(total_dev_hours, 1),
                "avg_roi_score": round(
                    sum(e.roi_score for e in estimates) / len(estimates), 1
                ),
                "avg_payback_months": round(
                    sum(min(e.payback_months, 36) for e in estimates) / len(estimates),
                    1,
                ),
            },
            "recommendations": recommendation_counts,
            "complexity_distribution": complexity_counts,
            "top_candidates": top_candidates,
            "estimates": [e.to_dict() for e in estimates],
        }


__all__ = [
    "ROIEstimator",
    "ROIEstimate",
    "ROIConfig",
    "ComplexityLevel",
    "RecommendationLevel",
]
