"""
Cost Optimizer - Track and minimize token usage across chains.

This service provides:
- Token usage tracking
- Cost estimation
- Optimization suggestions
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.chain_types import (
    ChainCost,
    ComplexityLevel,
    CostEntry,
    TaskType,
)


@dataclass
class PeriodSummary:
    """Cost summary for a time period."""

    start: datetime
    end: datetime
    total_cost: float
    total_tokens: int
    by_task_type: dict[str, dict[str, Any]]
    by_model: dict[str, dict[str, Any]]
    optimization_potential: float


class CostTracker:
    """Track token usage and costs."""

    # Model pricing (per 1M tokens)
    MODEL_PRICES: dict[str, dict[str, float]] = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-haiku": {"input": 0.25, "output": 1.25},
        "gemini-pro": {"input": 0.125, "output": 0.375},
        "gemini-ultra": {"input": 1.00, "output": 3.00},
    }

    def __init__(self):
        self.entries: list[CostEntry] = []
        self.chain_costs: dict[str, ChainCost] = {}
        logger.info("CostTracker initialized")

    def record_usage(
        self,
        chain_id: str,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int = 0,
    ) -> CostEntry:
        """
        Record token usage for an agent execution.

        Args:
            chain_id: The chain ID
            agent: The agent name
            model: The model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration_ms: Duration in milliseconds

        Returns:
            CostEntry with calculated cost
        """
        entry = CostEntry(
            chain_id=chain_id,
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            timestamp=datetime.utcnow(),
            duration_ms=duration_ms,
        )

        # Calculate cost
        entry.cost = self._calculate_cost(entry)
        self.entries.append(entry)

        # Update chain cost
        self._update_chain_cost(entry)

        logger.debug(
            f"Recorded usage: {chain_id}/{agent}: {entry.total_tokens} tokens, ${entry.cost:.4f}"
        )

        return entry

    def _calculate_cost(self, entry: CostEntry) -> float:
        """Calculate cost for a cost entry."""
        prices = self.MODEL_PRICES.get(entry.model, {"input": 0, "output": 0})
        input_cost = (entry.input_tokens / 1_000_000) * prices.get("input", 0)
        output_cost = (entry.output_tokens / 1_000_000) * prices.get("output", 0)
        return round(input_cost + output_cost, 6)

    def _update_chain_cost(self, entry: CostEntry) -> None:
        """Update aggregated chain cost."""
        if entry.chain_id not in self.chain_costs:
            self.chain_costs[entry.chain_id] = ChainCost(
                chain_id=entry.chain_id,
                task_type=TaskType.IMPLEMENT,  # Will be updated
                total_input_tokens=0,
                total_output_tokens=0,
                estimated_cost=0.0,
                agent_breakdown={},
            )

        chain_cost = self.chain_costs[entry.chain_id]
        chain_cost.total_input_tokens += entry.input_tokens
        chain_cost.total_output_tokens += entry.output_tokens
        chain_cost.estimated_cost += entry.cost or 0

        # Update agent breakdown
        if entry.agent not in chain_cost.agent_breakdown:
            chain_cost.agent_breakdown[entry.agent] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
            }
        agent_data = chain_cost.agent_breakdown[entry.agent]
        agent_data["input_tokens"] += entry.input_tokens
        agent_data["output_tokens"] += entry.output_tokens
        agent_data["cost"] += entry.cost or 0

    def get_chain_cost(self, chain_id: str) -> ChainCost | None:
        """Get cost breakdown for a chain."""
        return self.chain_costs.get(chain_id)

    def get_period_summary(
        self, start: datetime, end: datetime, task_type: TaskType | None = None
    ) -> PeriodSummary:
        """
        Get cost summary for a time period.

        Args:
            start: Start of period
            end: End of period
            task_type: Optional filter by task type

        Returns:
            PeriodSummary with cost breakdown
        """
        # Filter entries
        filtered_entries = [e for e in self.entries if start <= e.timestamp <= end]

        # Calculate totals
        total_cost = sum(e.cost or 0 for e in filtered_entries)
        total_tokens = sum(e.total_tokens for e in filtered_entries)

        # Group by task type
        by_task_type: dict[str, dict[str, Any]] = {}
        for entry in filtered_entries:
            task_type_str = entry.chain_id.split("-")[0] if "-" in entry.chain_id else "unknown"
            if task_type_str not in by_task_type:
                by_task_type[task_type_str] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "chains": set(),
                }
            by_task_type[task_type_str]["cost"] += entry.cost or 0
            by_task_type[task_type_str]["tokens"] += entry.total_tokens
            by_task_type[task_type_str]["chains"].add(entry.chain_id)

        # Convert sets to counts
        for tt in by_task_type:
            by_task_type[tt]["chain_count"] = len(by_task_type[tt]["chains"])
            del by_task_type[tt]["chains"]

        # Group by model
        by_model: dict[str, dict[str, Any]] = {}
        for entry in filtered_entries:
            if entry.model not in by_model:
                by_model[entry.model] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "calls": 0,
                }
            by_model[entry.model]["cost"] += entry.cost or 0
            by_model[entry.model]["tokens"] += entry.total_tokens
            by_model[entry.model]["calls"] += 1

        # Calculate optimization potential
        optimization_potential = self._calculate_optimization_potential(filtered_entries)

        return PeriodSummary(
            start=start,
            end=end,
            total_cost=total_cost,
            total_tokens=total_tokens,
            by_task_type=by_task_type,
            by_model=by_model,
            optimization_potential=optimization_potential,
        )

    def _calculate_optimization_potential(self, entries: list[CostEntry]) -> float:
        """Calculate potential cost savings."""
        potential_savings = 0.0

        for entry in entries:
            # Check if using expensive model for simple task
            if entry.model == "gpt-4" and entry.agent in ["explore", "docs"]:
                # Could use gpt-4-turbo instead
                savings = (entry.cost or 0) * 0.6
                potential_savings += savings

        return round(potential_savings, 4)

    def get_usage_stats(self) -> dict[str, Any]:
        """Get overall usage statistics."""
        if not self.entries:
            return {
                "total_cost": 0,
                "total_tokens": 0,
                "chain_count": 0,
                "average_cost_per_chain": 0,
            }

        total_cost = sum(e.cost or 0 for e in self.entries)
        total_tokens = sum(e.total_tokens for e in self.entries)
        chain_count = len(self.chain_costs)

        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "chain_count": chain_count,
            "average_cost_per_chain": round(total_cost / chain_count, 4) if chain_count > 0 else 0,
            "entry_count": len(self.entries),
        }


class CostOptimizer:
    """Optimize chain execution for cost efficiency."""

    # Model selection by agent
    MODEL_SELECTION: dict[str, str] = {
        "explore": "gpt-4-turbo",
        "architect": "claude-3-sonnet",
        "builder": "claude-3-opus",
        "quality": "gpt-4-turbo",
        "reviewer": "claude-3-sonnet",
        "docs": "gpt-4-turbo",
        "researcher": "gpt-4-turbo",
        "refactor": "claude-3-sonnet",
        "integrations": "claude-3-sonnet",
        "security": "claude-3-opus",
        "ui": "gpt-4-turbo",
    }

    # Context reduction targets
    CONTEXT_REDUCTION: dict[str, dict[str, int]] = {
        "explore": {"max_tokens": 8000},
        "builder": {"max_tokens": 16000},
        "quality": {"max_tokens": 8000},
        "reviewer": {"max_tokens": 12000},
    }

    def __init__(self, cost_tracker: CostTracker):
        self.cost_tracker = cost_tracker
        logger.info("CostOptimizer initialized")

    def optimize_chain(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        budget: float | None = None,
        model_overrides: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate cost-optimized chain configuration.

        Args:
            task_type: The task type
            complexity: The complexity level
            budget: Optional budget limit
            model_overrides: Optional model overrides

        Returns:
            Dict with optimized configuration
        """
        # Select models for each agent
        agents = self._get_agents_for_task(task_type)
        model_config = {}

        for agent in agents:
            if model_overrides and agent in model_overrides:
                model = model_overrides[agent]
            else:
                model = self.MODEL_SELECTION.get(agent, "gpt-4-turbo")
            model_config[agent] = model

        # Estimate cost
        estimated_cost = self._estimate_cost(task_type, complexity, agents)

        # Generate suggestions
        suggestions = self._generate_suggestions(task_type, complexity, agents)

        return {
            "agents": agents,
            "model_config": model_config,
            "estimated_cost": estimated_cost,
            "suggestions": suggestions,
            "budget_compliant": budget is None or estimated_cost <= budget,
        }

    def _get_agents_for_task(self, task_type: TaskType) -> list[str]:
        """Get agents for a task type."""
        agent_templates = {
            TaskType.IMPLEMENT: ["explore", "architect", "builder", "quality", "reviewer"],
            TaskType.FIX: ["explore", "builder", "quality", "reviewer"],
            TaskType.RESEARCH: ["explore", "researcher"],
            TaskType.REFACTOR: ["explore", "refactor", "quality", "reviewer"],
            TaskType.EXTEND: ["explore", "architect", "builder", "quality", "reviewer"],
            TaskType.CLONE: ["explore", "builder", "quality", "reviewer"],
            TaskType.TEST: ["explore", "quality", "reviewer"],
            TaskType.DOCS: ["explore", "docs", "reviewer"],
            TaskType.UI: ["explore", "ui", "quality", "reviewer"],
            TaskType.INTEGRATION: ["explore", "integrations", "quality", "reviewer"],
            TaskType.SECURITY: ["explore", "security", "reviewer"],
        }
        return agent_templates.get(task_type, agent_templates[TaskType.IMPLEMENT])

    def _estimate_cost(
        self, task_type: TaskType, complexity: ComplexityLevel, agents: list[str]
    ) -> float:
        """Estimate cost for a chain."""
        # Base cost multipliers by complexity
        complexity_multiplier = {
            ComplexityLevel.TRIVIAL: 0.3,
            ComplexityLevel.SIMPLE: 0.5,
            ComplexityLevel.MODERATE: 1.0,
            ComplexityLevel.COMPLEX: 1.5,
            ComplexityLevel.EPIC: 2.5,
        }

        # Agent cost weights
        agent_weights = {
            "explore": 0.1,
            "architect": 0.15,
            "builder": 0.35,
            "quality": 0.15,
            "reviewer": 0.15,
            "docs": 0.1,
            "researcher": 0.1,
            "refactor": 0.25,
            "integrations": 0.3,
            "security": 0.2,
            "ui": 0.2,
        }

        # Base cost for IMPLEMENT/MODERATE
        base_cost = 2.0  # USD

        total = base_cost * complexity_multiplier[complexity]

        # Add agent-specific costs
        for agent in agents:
            weight = agent_weights.get(agent, 0.2)
            model = self.MODEL_SELECTION.get(agent, "gpt-4-turbo")
            model_multiplier = self._get_model_cost_multiplier(model)
            total += weight * model_multiplier

        return round(total, 2)

    def _get_model_cost_multiplier(self, model: str) -> float:
        """Get cost multiplier for a model (relative to gpt-4-turbo)."""
        # gpt-4-turbo = 1.0
        multipliers = {
            "gpt-4-turbo": 1.0,
            "gpt-4": 3.0,
            "gpt-3.5-turbo": 0.1,
            "claude-3-opus": 2.5,
            "claude-3-sonnet": 0.5,
            "claude-3-haiku": 0.1,
            "gemini-pro": 0.05,
            "gemini-ultra": 0.3,
        }
        return multipliers.get(model, 1.0)

    def _generate_suggestions(
        self, task_type: TaskType, complexity: ComplexityLevel, agents: list[str]
    ) -> list[str]:
        """Generate cost optimization suggestions."""
        suggestions = []

        # Suggest model changes
        expensive_agents = [
            a
            for a in agents
            if a in ["builder", "security"] and self.MODEL_SELECTION.get(a) == "gpt-4"
        ]
        if expensive_agents:
            suggestions.append(
                f"Consider using gpt-4-turbo instead of gpt-4 for {', '.join(expensive_agents)} "
                f"(saves ~60%)"
            )

        # Suggest parallel execution
        if "docs" not in agents and "security" not in agents:
            suggestions.append("Run docs and security checks in parallel with main chain")

        # Suggest context reduction
        if "explore" in agents:
            suggestions.append("Reduce EXPLORE context to 8000 tokens (save ~200 tokens)")

        return suggestions

    def get_cost_dashboard(self) -> dict[str, Any]:
        """Get cost dashboard data."""
        stats = self.cost_tracker.get_usage_stats()
        return {
            "stats": stats,
            "model_pricing": self.MODEL_PRICES,
            "recommendations": [
                "Use gpt-4-turbo for EXPLORE, QUALITY, and DOCS",
                "Run QUALITY and SECURITY in parallel when possible",
                "Reduce context in EXPLORE phase for faster processing",
            ],
        }
