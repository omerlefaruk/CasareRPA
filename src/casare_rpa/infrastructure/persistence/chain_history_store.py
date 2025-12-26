"""
Chain History Store - Store and retrieve chain execution history.

This service provides:
- Persistent storage for chain execution records
- Historical data retrieval for predictions
- Pattern analysis data
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from loguru import logger

from casare_rpa.domain.entities.chain_types import (
    ChainExecution,
    ComplexityLevel,
    TaskType,
)

HISTORY_DIR = ".brain/data"
HISTORY_FILE = os.path.join(HISTORY_DIR, "chain_history.json")


@dataclass
class SystemLoad:
    """System load metrics at prediction time."""

    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    active_chains: int = 0
    queue_depth: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "active_chains": self.active_chains,
            "queue_depth": self.queue_depth,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemLoad":
        return cls(
            cpu_percent=data.get("cpu_percent", 0.0),
            memory_percent=data.get("memory_percent", 0.0),
            active_chains=data.get("active_chains", 0),
            queue_depth=data.get("queue_depth", 0),
        )


class ChainHistoryStore:
    """Store and retrieve chain execution history."""

    def __init__(self, history_file: str = HISTORY_FILE):
        self.history_file = history_file
        self._ensure_data_dir()
        self._ensure_history_file()
        logger.info(f"ChainHistoryStore initialized with {history_file}")

    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        os.makedirs(HISTORY_DIR, exist_ok=True)

    def _ensure_history_file(self) -> None:
        """Ensure the history file exists."""
        if not os.path.exists(self.history_file):
            with open(self.history_file, "w") as f:
                json.dump({"executions": [], "patterns": []}, f)

    def save_execution(self, execution: ChainExecution) -> None:
        """
        Save an execution to history.

        Args:
            execution: The execution record to save
        """
        try:
            with open(self.history_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = {"executions": [], "patterns": []}

        # Convert execution to dict
        exec_dict = execution.to_dict()
        exec_dict["saved_at"] = datetime.utcnow().isoformat()

        data["executions"].append(exec_dict)

        # Keep only last 1000 executions
        if len(data["executions"]) > 1000:
            data["executions"] = data["executions"][-1000:]

        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved execution: {execution.chain_id}")

    def get_history(
        self,
        task_type: TaskType | None = None,
        complexity: ComplexityLevel | None = None,
        limit: int = 100,
    ) -> list[ChainExecution]:
        """
        Get historical executions.

        Args:
            task_type: Optional filter by task type
            complexity: Optional filter by complexity
            limit: Maximum number of records to return

        Returns:
            List of ChainExecution records
        """
        try:
            with open(self.history_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

        executions = []
        for exec_dict in data.get("executions", []):
            # Apply filters
            if task_type:
                if exec_dict.get("task_type") != task_type.value:
                    continue

            if complexity:
                if exec_dict.get("complexity") != complexity.value:
                    continue

            # Parse datetime
            try:
                exec_dict["started"] = datetime.fromisoformat(exec_dict["started"])
                exec_dict["completed"] = datetime.fromisoformat(exec_dict["completed"])
            except (KeyError, ValueError):
                continue

            # Reconstruct ChainExecution
            execution = ChainExecution(
                chain_id=exec_dict["chain_id"],
                task_type=TaskType(exec_dict["task_type"]),
                complexity=ComplexityLevel(exec_dict["complexity"]),
                started=exec_dict["started"],
                completed=exec_dict["completed"],
                duration_seconds=exec_dict["duration_seconds"],
                agent_durations=exec_dict.get("agent_durations", {}),
                success=exec_dict.get("success", False),
                iterations=exec_dict.get("iterations", 1),
                cost=exec_dict.get("cost"),
            )
            executions.append(execution)

            if len(executions) >= limit:
                break

        return executions

    def get_recent_executions(self, days: int = 7, limit: int = 100) -> list[ChainExecution]:
        """
        Get executions from recent days.

        Args:
            days: Number of days to look back
            limit: Maximum number of records

        Returns:
            List of recent ChainExecution records
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        try:
            with open(self.history_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

        executions = []
        for exec_dict in data.get("executions", []):
            try:
                completed = datetime.fromisoformat(exec_dict.get("completed", ""))
                if completed < cutoff:
                    continue
            except ValueError:
                continue

            # Reconstruct execution (simplified)
            execution = ChainExecution(
                chain_id=exec_dict["chain_id"],
                task_type=TaskType(exec_dict["task_type"]),
                complexity=ComplexityLevel(exec_dict["complexity"]),
                started=datetime.fromisoformat(exec_dict["started"]),
                completed=datetime.fromisoformat(exec_dict["completed"]),
                duration_seconds=exec_dict["duration_seconds"],
                agent_durations=exec_dict.get("agent_durations", {}),
                success=exec_dict.get("success", False),
                iterations=exec_dict.get("iterations", 1),
                cost=exec_dict.get("cost"),
            )
            executions.append(execution)

            if len(executions) >= limit:
                break

        return executions

    def get_statistics(self, task_type: TaskType | None = None) -> dict[str, Any]:
        """
        Get statistics for historical executions.

        Args:
            task_type: Optional filter by task type

        Returns:
            Dict with statistics
        """
        executions = self.get_history(task_type=task_type, limit=1000)

        if not executions:
            return {
                "count": 0,
                "avg_duration": 0,
                "success_rate": 0,
                "avg_iterations": 0,
            }

        successful = [e for e in executions if e.success]
        durations = [e.duration_seconds for e in executions]
        iterations = [e.iterations for e in executions]

        return {
            "count": len(executions),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "success_rate": len(successful) / len(executions) * 100 if executions else 0,
            "avg_iterations": sum(iterations) / len(iterations),
            "by_complexity": self._get_stats_by_complexity(executions),
            "by_task_type": self._get_stats_by_task_type(executions),
        }

    def _get_stats_by_complexity(self, executions: list[ChainExecution]) -> dict[str, Any]:
        """Get statistics grouped by complexity."""
        stats = {}
        for cl in ComplexityLevel:
            filtered = [e for e in executions if e.complexity == cl]
            if filtered:
                durations = [e.duration_seconds for e in filtered]
                stats[cl.name] = {
                    "count": len(filtered),
                    "avg_duration": sum(durations) / len(durations),
                    "success_rate": sum(1 for e in filtered if e.success) / len(filtered) * 100,
                }
        return stats

    def _get_stats_by_task_type(self, executions: list[ChainExecution]) -> dict[str, Any]:
        """Get statistics grouped by task type."""
        stats = {}
        for tt in TaskType:
            filtered = [e for e in executions if e.task_type == tt]
            if filtered:
                durations = [e.duration_seconds for e in filtered]
                stats[tt.value] = {
                    "count": len(filtered),
                    "avg_duration": sum(durations) / len(durations),
                    "success_rate": sum(1 for e in filtered if e.success) / len(filtered) * 100,
                }
        return stats

    def clear_history(self, days_to_keep: int = 30) -> int:
        """
        Clear old history entries.

        Args:
            days_to_keep: Number of days to retain

        Returns:
            Number of entries removed
        """
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)

        try:
            with open(self.history_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return 0

        original_count = len(data.get("executions", []))

        # Filter out old entries
        data["executions"] = [
            e
            for e in data.get("executions", [])
            if "completed" in e and datetime.fromisoformat(e["completed"]) >= cutoff
        ]

        with open(self.history_file, "w") as f:
            json.dump(data, f, indent=2)

        removed = original_count - len(data["executions"])
        logger.info(f"Cleared {removed} old history entries")
        return removed

    def export_history(self, output_file: str) -> None:
        """Export history to a file."""
        try:
            with open(self.history_file) as f:
                data = json.load(f)

            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Exported history to {output_file}")
        except Exception as e:
            logger.error(f"Failed to export history: {e}")
