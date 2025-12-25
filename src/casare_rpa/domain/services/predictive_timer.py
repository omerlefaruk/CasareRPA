"""
Predictive Timer - Estimate chain completion times based on historical data.

This service provides:
- Time prediction based on historical patterns
- Confidence intervals (P50, P90, P99)
- Per-agent milestone predictions
- System load adjustments
"""

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from casare_rpa.domain.entities.chain_types import (
    ComplexityLevel,
    TaskType,
    TimePrediction,
)


@dataclass
class PredictionFactor:
    """Factor that influenced the prediction."""

    factor: str
    impact: float  # Percentage impact (+/-)
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor,
            "impact": self.impact,
            "description": self.description,
        }


# Base duration estimates by complexity (in minutes)
BASE_DURATIONS: dict[ComplexityLevel, dict[TaskType, int]] = {
    ComplexityLevel.TRIVIAL: {
        TaskType.IMPLEMENT: 15,
        TaskType.FIX: 10,
        TaskType.RESEARCH: 5,
        TaskType.REFACTOR: 15,
        TaskType.EXTEND: 15,
        TaskType.CLONE: 10,
        TaskType.TEST: 10,
        TaskType.DOCS: 5,
        TaskType.UI: 15,
        TaskType.INTEGRATION: 20,
        TaskType.SECURITY: 15,
    },
    ComplexityLevel.SIMPLE: {
        TaskType.IMPLEMENT: 30,
        TaskType.FIX: 20,
        TaskType.RESEARCH: 10,
        TaskType.REFACTOR: 25,
        TaskType.EXTEND: 25,
        TaskType.CLONE: 20,
        TaskType.TEST: 20,
        TaskType.DOCS: 10,
        TaskType.UI: 25,
        TaskType.INTEGRATION: 35,
        TaskType.SECURITY: 25,
    },
    ComplexityLevel.MODERATE: {
        TaskType.IMPLEMENT: 60,
        TaskType.FIX: 35,
        TaskType.RESEARCH: 20,
        TaskType.REFACTOR: 45,
        TaskType.EXTEND: 50,
        TaskType.CLONE: 35,
        TaskType.TEST: 35,
        TaskType.DOCS: 20,
        TaskType.UI: 45,
        TaskType.INTEGRATION: 60,
        TaskType.SECURITY: 45,
    },
    ComplexityLevel.COMPLEX: {
        TaskType.IMPLEMENT: 120,
        TaskType.FIX: 60,
        TaskType.RESEARCH: 40,
        TaskType.REFACTOR: 90,
        TaskType.EXTEND: 100,
        TaskType.CLONE: 60,
        TaskType.TEST: 60,
        TaskType.DOCS: 35,
        TaskType.UI: 75,
        TaskType.INTEGRATION: 100,
        TaskType.SECURITY: 75,
    },
    ComplexityLevel.EPIC: {
        TaskType.IMPLEMENT: 240,
        TaskType.FIX: 120,
        TaskType.RESEARCH: 60,
        TaskType.REFACTOR: 180,
        TaskType.EXTEND: 200,
        TaskType.CLONE: 120,
        TaskType.TEST: 100,
        TaskType.DOCS: 60,
        TaskType.UI: 120,
        TaskType.INTEGRATION: 180,
        TaskType.SECURITY: 120,
    },
}

# Agent duration percentages (approximate)
AGENT_PERCENTAGES: dict[TaskType, dict[str, float]] = {
    TaskType.IMPLEMENT: {
        "explore": 0.10,
        "architect": 0.20,
        "builder": 0.45,
        "quality": 0.15,
        "reviewer": 0.10,
    },
    TaskType.FIX: {
        "explore": 0.15,
        "builder": 0.50,
        "quality": 0.20,
        "reviewer": 0.15,
    },
    TaskType.RESEARCH: {
        "explore": 0.40,
        "researcher": 0.60,
    },
    TaskType.REFACTOR: {
        "explore": 0.10,
        "refactor": 0.60,
        "quality": 0.20,
        "reviewer": 0.10,
    },
    TaskType.EXTEND: {
        "explore": 0.10,
        "architect": 0.15,
        "builder": 0.50,
        "quality": 0.15,
        "reviewer": 0.10,
    },
    TaskType.CLONE: {
        "explore": 0.15,
        "builder": 0.55,
        "quality": 0.20,
        "reviewer": 0.10,
    },
    TaskType.TEST: {
        "explore": 0.15,
        "quality": 0.65,
        "reviewer": 0.20,
    },
    TaskType.DOCS: {
        "explore": 0.20,
        "docs": 0.60,
        "reviewer": 0.20,
    },
    TaskType.UI: {
        "explore": 0.10,
        "ui": 0.60,
        "quality": 0.20,
        "reviewer": 0.10,
    },
    TaskType.INTEGRATION: {
        "explore": 0.10,
        "integrations": 0.60,
        "quality": 0.20,
        "reviewer": 0.10,
    },
    TaskType.SECURITY: {
        "explore": 0.25,
        "security": 0.55,
        "reviewer": 0.20,
    },
}


class PredictiveTimer:
    """Predict chain completion times."""

    def __init__(self, history_store=None):
        self.history_store = history_store
        logger.info("PredictiveTimer initialized")

    def predict(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        system_load: Optional[float] = None,
        historical_data: Optional[list[dict]] = None,
    ) -> TimePrediction:
        """
        Predict completion time for a chain.

        Args:
            task_type: The task type
            complexity: The complexity level
            system_load: Optional system load factor (1.0 = normal, 1.5 = high)
            historical_data: Optional historical execution data

        Returns:
            TimePrediction with estimates and confidence
        """
        factors: list[PredictionFactor] = []

        # Get base duration
        base_duration = self._get_base_duration(task_type, complexity)
        total_duration = base_duration

        # Adjust for historical data if available
        if historical_data:
            historical_avg = self._calculate_historical_avg(historical_data)
            if historical_avg > 0:
                adjustment = (historical_avg - base_duration) / base_duration
                total_duration = base_duration * (1 + adjustment * 0.3)
                factors.append(
                    PredictionFactor(
                        factor="historical_data",
                        impact=round(adjustment * 30, 1),
                        description="Based on similar past executions",
                    )
                )

        # Adjust for system load
        if system_load and system_load != 1.0:
            load_impact = (system_load - 1.0) * 100
            total_duration *= system_load
            factors.append(
                PredictionFactor(
                    factor="system_load",
                    impact=round(load_impact, 1),
                    description=f"System load factor: {system_load}",
                )
            )

        # Convert to int (minutes)
        estimated_minutes = max(5, int(round(total_duration)))

        # Calculate confidence based on data availability
        confidence = self._calculate_confidence(historical_data, complexity, system_load)

        # Calculate percentile estimates
        percentile_estimates = self._calculate_percentiles(estimated_minutes, confidence)

        # Get agent breakdown
        agent_breakdown = self._get_agent_breakdown(task_type, estimated_minutes)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            task_type, complexity, system_load, confidence
        )

        logger.info(
            f"Prediction: {task_type.value}/{complexity.name} = "
            f"{estimated_minutes} min (confidence: {confidence:.2f})"
        )

        return TimePrediction(
            estimated_total_minutes=estimated_minutes,
            confidence=confidence,
            percentile_estimates=percentile_estimates,
            agent_breakdown=agent_breakdown,
            factors=[f.to_dict() for f in factors],
            recommendations=recommendations,
        )

    def _get_base_duration(self, task_type: TaskType, complexity: ComplexityLevel) -> float:
        """Get base duration for task type and complexity."""
        return BASE_DURATIONS.get(complexity, {}).get(
            task_type, BASE_DURATIONS[ComplexityLevel.MODERATE][TaskType.IMPLEMENT]
        )

    def _calculate_historical_avg(self, historical_data: list[dict]) -> float:
        """Calculate average duration from historical data."""
        if not historical_data:
            return 0

        durations = [
            d.get("duration_seconds", 0) / 60  # Convert to minutes
            for d in historical_data
            if "duration_seconds" in d
        ]

        if not durations:
            return 0

        return sum(durations) / len(durations)

    def _calculate_confidence(
        self,
        historical_data: Optional[list[dict]],
        complexity: ComplexityLevel,
        system_load: Optional[float],
    ) -> float:
        """Calculate confidence score for prediction."""
        confidence = 0.5  # Base confidence

        # Increase with historical data
        if historical_data:
            count = len(historical_data)
            confidence += min(0.3, count * 0.05)

        # Decrease for higher complexity
        confidence -= (complexity.value - 1) * 0.05

        # Decrease for uncertain system load
        if system_load is None:
            confidence -= 0.1

        # Confidence bounds
        return max(0.3, min(0.95, confidence))

    def _calculate_percentiles(self, estimated_minutes: int, confidence: float) -> dict[int, int]:
        """Calculate percentile estimates (P50, P90, P99)."""
        # The spread increases as confidence decreases
        spread_factor = 1 + (1 - confidence) * 0.5

        p50 = estimated_minutes
        p90 = int(round(estimated_minutes * spread_factor * 1.3))
        p99 = int(round(estimated_minutes * spread_factor * 1.6))

        return {
            50: p50,
            90: p90,
            99: p99,
        }

    def _get_agent_breakdown(self, task_type: TaskType, total_minutes: int) -> dict[str, int]:
        """Get per-agent time breakdown."""
        percentages = AGENT_PERCENTAGES.get(task_type, AGENT_PERCENTAGES[TaskType.IMPLEMENT])

        breakdown: dict[str, int] = {}
        for agent, percentage in percentages.items():
            breakdown[agent] = max(1, int(round(total_minutes * percentage)))

        return breakdown

    def _generate_recommendations(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        system_load: Optional[float],
        confidence: float,
    ) -> list[str]:
        """Generate recommendations based on prediction."""
        recommendations = []

        if confidence < 0.6:
            recommendations.append("Low confidence prediction - monitor progress")

        if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.EPIC]:
            recommendations.append("Consider breaking into smaller chains")

        if system_load and system_load > 1.2:
            recommendations.append("High system load - expect delays")

        if task_type in [TaskType.INTEGRATION, TaskType.SECURITY]:
            recommendations.append("May require additional review time")

        if not recommendations:
            recommendations.append("Standard execution expected")

        return recommendations

    def predict_with_agents(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        agents: list[str],
        system_load: Optional[float] = None,
    ) -> TimePrediction:
        """
        Predict time with specific agent list.

        Args:
            task_type: The task type
            complexity: The complexity level
            agents: List of agent names
            system_load: Optional system load factor

        Returns:
            TimePrediction with per-agent estimates
        """
        base_prediction = self.predict(task_type, complexity, system_load)

        # Adjust for specific agent list
        total_percentage = 0
        for agent in agents:
            if agent in base_prediction.agent_breakdown:
                total_percentage += (
                    base_prediction.agent_breakdown[agent] / base_prediction.estimated_total_minutes
                )

        # If agents represent partial chain, adjust
        if total_percentage > 0 and total_percentage < 1:
            adjustment = total_percentage
            adjusted_minutes = int(base_prediction.estimated_total_minutes * adjustment)

            # Recalculate agent breakdown for selected agents
            new_breakdown: dict[str, int] = {}
            for agent in agents:
                if agent in base_prediction.agent_breakdown:
                    new_breakdown[agent] = base_prediction.agent_breakdown[agent]

            return TimePrediction(
                estimated_total_minutes=adjusted_minutes,
                confidence=base_prediction.confidence * 0.9,  # Slightly lower confidence
                percentile_estimates=self._calculate_percentiles(
                    adjusted_minutes, base_prediction.confidence
                ),
                agent_breakdown=new_breakdown,
                factors=base_prediction.factors,
                recommendations=base_prediction.recommendations,
            )

        return base_prediction

    def compare_predictions(self, predictions: list[TimePrediction]) -> dict[str, Any]:
        """Compare multiple predictions."""
        if not predictions:
            return {"error": "No predictions to compare"}

        min_time = min(p.estimated_total_minutes for p in predictions)
        max_time = max(p.estimated_total_minutes for p in predictions)
        avg_confidence = sum(p.confidence for p in predictions) / len(predictions)

        # Group by confidence level
        high_conf = [p for p in predictions if p.confidence >= 0.7]
        low_conf = [p for p in predictions if p.confidence < 0.7]

        return {
            "count": len(predictions),
            "min_time_minutes": min_time,
            "max_time_minutes": max_time,
            "avg_confidence": round(avg_confidence, 2),
            "high_confidence_count": len(high_conf),
            "low_confidence_count": len(low_conf),
            "recommendation": (
                "Use prediction with highest confidence"
                if high_conf
                else "Consider gathering more historical data"
            ),
        }

    def get_timeline_estimate(
        self, prediction: TimePrediction, start_time: datetime
    ) -> dict[str, datetime]:
        """Get estimated completion times from start time."""
        p50 = start_time.minutes(prediction.percentile_estimates[50])
        p90 = start_time.minutes(prediction.percentile_estimates[90])
        p99 = start_time.minutes(prediction.percentile_estimates[99])

        return {
            "optimistic": start_time,
            "p50": p50,
            "p90": p90,
            "p99": p99,
        }
