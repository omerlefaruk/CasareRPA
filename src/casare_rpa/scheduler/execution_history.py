"""
Execution History for CasareRPA Scheduler.
Tracks schedule execution results over time.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any

from loguru import logger


@dataclass
class ExecutionHistoryEntry:
    """Single entry in execution history."""

    id: str
    schedule_id: str
    schedule_name: str
    workflow_path: str
    workflow_name: str
    status: str  # completed, failed, skipped
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: int = 0
    success: bool = False
    error_message: str = ""
    output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "schedule_name": self.schedule_name,
            "workflow_path": self.workflow_path,
            "workflow_name": self.workflow_name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "duration_ms": self.duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "output": self.output,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExecutionHistoryEntry":
        """Create from dictionary."""

        def parse_datetime(val):
            if val is None:
                return None
            if isinstance(val, datetime):
                return val
            try:
                return datetime.fromisoformat(val)
            except (ValueError, TypeError):
                return None

        return cls(
            id=data.get("id", ""),
            schedule_id=data.get("schedule_id", ""),
            schedule_name=data.get("schedule_name", ""),
            workflow_path=data.get("workflow_path", ""),
            workflow_name=data.get("workflow_name", ""),
            status=data.get("status", ""),
            started_at=parse_datetime(data.get("started_at")) or datetime.now(),
            completed_at=parse_datetime(data.get("completed_at")),
            duration_ms=data.get("duration_ms", 0),
            success=data.get("success", False),
            error_message=data.get("error_message", ""),
            output=data.get("output", {}),
        )

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if self.duration_ms == 0:
            return "-"
        seconds = self.duration_ms / 1000
        if seconds < 60:
            return f"{seconds:.1f}s"
        minutes = seconds / 60
        if minutes < 60:
            return f"{minutes:.1f}m"
        hours = minutes / 60
        return f"{hours:.1f}h"


class ExecutionHistory:
    """
    Manages execution history storage and retrieval.
    Stores history in a JSON file with automatic cleanup of old entries.
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        max_entries: int = 1000,
        retention_days: int = 30,
    ):
        """
        Initialize execution history.

        Args:
            storage_path: Path to history JSON file
            max_entries: Maximum entries to keep
            retention_days: Days to retain entries
        """
        if storage_path:
            self._storage_path = storage_path
        else:
            config_dir = Path.home() / ".casare_rpa" / "scheduler"
            config_dir.mkdir(parents=True, exist_ok=True)
            self._storage_path = config_dir / "execution_history.json"

        self._max_entries = max_entries
        self._retention_days = retention_days

        # Create file if doesn't exist
        if not self._storage_path.exists():
            self._storage_path.write_text("[]")

        logger.debug(f"Execution history initialized at: {self._storage_path}")

    def _load_raw(self) -> List[Dict[str, Any]]:
        """Load raw JSON data from storage."""
        try:
            content = self._storage_path.read_text(encoding="utf-8")
            return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Failed to load execution history: {e}")
            return []

    def _save_raw(self, data: List[Dict[str, Any]]) -> bool:
        """Save raw JSON data to storage."""
        try:
            content = json.dumps(data, indent=2, default=str)
            self._storage_path.write_text(content, encoding="utf-8")
            return True
        except Exception as e:
            logger.error(f"Failed to save execution history: {e}")
            return False

    def add_entry(self, result) -> bool:
        """
        Add an execution result to history.

        Args:
            result: ScheduleExecutionResult or ExecutionHistoryEntry

        Returns:
            True if added successfully
        """
        import uuid

        # Convert ScheduleExecutionResult to entry
        if hasattr(result, "schedule_id"):
            entry = ExecutionHistoryEntry(
                id=str(uuid.uuid4()),
                schedule_id=result.schedule_id,
                schedule_name=result.schedule_name,
                workflow_path=result.workflow_path,
                workflow_name=result.workflow_name,
                status=result.status.value
                if hasattr(result.status, "value")
                else str(result.status),
                started_at=result.started_at,
                completed_at=result.completed_at,
                duration_ms=result.duration_ms,
                success=result.success,
                error_message=result.error_message,
                output=result.output if hasattr(result, "output") else {},
            )
        else:
            entry = result

        # Load existing
        raw_data = self._load_raw()

        # Add new entry at the beginning
        raw_data.insert(0, entry.to_dict())

        # Cleanup old entries
        raw_data = self._cleanup_entries(raw_data)

        return self._save_raw(raw_data)

    def _cleanup_entries(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean up old entries based on retention policy."""
        # Remove entries older than retention period
        cutoff = datetime.now() - timedelta(days=self._retention_days)
        filtered = []

        for entry in entries:
            started_at = entry.get("started_at")
            if started_at:
                try:
                    if isinstance(started_at, str):
                        entry_date = datetime.fromisoformat(started_at)
                    else:
                        entry_date = started_at
                    if entry_date >= cutoff:
                        filtered.append(entry)
                except (ValueError, TypeError):
                    filtered.append(entry)  # Keep if can't parse
            else:
                filtered.append(entry)

        # Trim to max entries
        return filtered[: self._max_entries]

    def get_entries(
        self,
        limit: int = 100,
        schedule_id: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
    ) -> List[ExecutionHistoryEntry]:
        """
        Get execution history entries.

        Args:
            limit: Maximum entries to return
            schedule_id: Filter by schedule ID
            status: Filter by status (completed, failed, skipped)
            since: Only entries after this datetime

        Returns:
            List of ExecutionHistoryEntry objects
        """
        raw_data = self._load_raw()
        entries = []

        for item in raw_data:
            if len(entries) >= limit:
                break

            # Apply filters
            if schedule_id and item.get("schedule_id") != schedule_id:
                continue
            if status and item.get("status") != status:
                continue
            if since:
                started_at = item.get("started_at")
                if started_at:
                    try:
                        if isinstance(started_at, str):
                            entry_date = datetime.fromisoformat(started_at)
                        else:
                            entry_date = started_at
                        if entry_date < since:
                            continue
                    except (ValueError, TypeError):
                        pass

            try:
                entries.append(ExecutionHistoryEntry.from_dict(item))
            except Exception as e:
                logger.warning(f"Failed to parse history entry: {e}")

        return entries

    def get_recent(self, limit: int = 10) -> List[ExecutionHistoryEntry]:
        """Get most recent entries."""
        return self.get_entries(limit=limit)

    def get_for_schedule(
        self, schedule_id: str, limit: int = 50
    ) -> List[ExecutionHistoryEntry]:
        """Get entries for a specific schedule."""
        return self.get_entries(limit=limit, schedule_id=schedule_id)

    def get_failures(self, limit: int = 50) -> List[ExecutionHistoryEntry]:
        """Get failed executions."""
        return self.get_entries(limit=limit, status="failed")

    def get_today(self) -> List[ExecutionHistoryEntry]:
        """Get today's executions."""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.get_entries(limit=1000, since=today)

    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get execution statistics.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with statistics
        """
        since = datetime.now() - timedelta(days=days)
        entries = self.get_entries(limit=10000, since=since)

        total = len(entries)
        successful = sum(1 for e in entries if e.success)
        failed = sum(1 for e in entries if not e.success and e.status == "failed")
        skipped = sum(1 for e in entries if e.status == "skipped")

        # Calculate average duration
        durations = [e.duration_ms for e in entries if e.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        # Group by schedule
        by_schedule: Dict[str, Dict] = {}
        for entry in entries:
            sid = entry.schedule_id
            if sid not in by_schedule:
                by_schedule[sid] = {
                    "name": entry.schedule_name,
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                }
            by_schedule[sid]["total"] += 1
            if entry.success:
                by_schedule[sid]["successful"] += 1
            elif entry.status == "failed":
                by_schedule[sid]["failed"] += 1

        # Group by day
        by_day: Dict[str, Dict] = {}
        for entry in entries:
            day = entry.started_at.strftime("%Y-%m-%d")
            if day not in by_day:
                by_day[day] = {"total": 0, "successful": 0, "failed": 0}
            by_day[day]["total"] += 1
            if entry.success:
                by_day[day]["successful"] += 1
            elif entry.status == "failed":
                by_day[day]["failed"] += 1

        return {
            "period_days": days,
            "total_executions": total,
            "successful": successful,
            "failed": failed,
            "skipped": skipped,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration_ms": avg_duration,
            "by_schedule": by_schedule,
            "by_day": dict(sorted(by_day.items())),
        }

    def clear_history(self) -> bool:
        """Clear all execution history."""
        return self._save_raw([])

    def delete_for_schedule(self, schedule_id: str) -> bool:
        """Delete all history for a specific schedule."""
        raw_data = self._load_raw()
        filtered = [e for e in raw_data if e.get("schedule_id") != schedule_id]
        return self._save_raw(filtered)


# Singleton instance
_history_instance: Optional[ExecutionHistory] = None


def get_execution_history() -> ExecutionHistory:
    """Get the global execution history instance."""
    global _history_instance
    if _history_instance is None:
        _history_instance = ExecutionHistory()
    return _history_instance


def set_execution_history(history: ExecutionHistory) -> None:
    """Set the global execution history instance (for testing)."""
    global _history_instance
    _history_instance = history
