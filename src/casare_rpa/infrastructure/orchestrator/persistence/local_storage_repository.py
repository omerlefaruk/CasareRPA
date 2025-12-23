"""
Local storage repository implementation using JSON files.
Stores orchestrator data in JSON files for offline/development mode.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


class LocalStorageRepository:
    """
    Local storage repository for offline/development mode.
    Stores data in JSON files when cloud backend is not available.
    """

    def __init__(self, storage_dir: Path | None = None):
        """Initialize local storage in user's home directory."""
        self.storage_dir = storage_dir or Path.home() / ".casare_rpa" / "orchestrator"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._robots_file = self.storage_dir / "robots.json"
        self._jobs_file = self.storage_dir / "jobs.json"
        self._workflows_file = self.storage_dir / "workflows.json"
        self._schedules_file = self.storage_dir / "schedules.json"
        self._triggers_file = self.storage_dir / "triggers.json"

        # Initialize files if they don't exist
        for file_path in [
            self._robots_file,
            self._jobs_file,
            self._workflows_file,
            self._schedules_file,
            self._triggers_file,
        ]:
            if not file_path.exists():
                file_path.write_text("[]")

    def _load_json(self, file_path: Path) -> list[dict[str, Any]]:
        """Load JSON data from file."""
        try:
            return json.loads(file_path.read_text())
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return []

    def _save_json(self, file_path: Path, data: list[dict[str, Any]]) -> bool:
        """Save JSON data to file."""
        try:
            file_path.write_text(json.dumps(data, indent=2, default=str))
            return True
        except Exception as e:
            logger.error(f"Failed to save {file_path}: {e}")
            return False

    # ==================== ROBOTS ====================

    def get_robots(self) -> list[dict[str, Any]]:
        """Get all robots from local storage."""
        return self._load_json(self._robots_file)

    def save_robot(self, robot: dict[str, Any]) -> bool:
        """Save or update a robot."""
        robots = self.get_robots()
        # Update existing or add new
        for i, r in enumerate(robots):
            if r["id"] == robot["id"]:
                robots[i] = robot
                return self._save_json(self._robots_file, robots)
        robots.append(robot)
        return self._save_json(self._robots_file, robots)

    def delete_robot(self, robot_id: str) -> bool:
        """Delete a robot."""
        robots = [r for r in self.get_robots() if r["id"] != robot_id]
        return self._save_json(self._robots_file, robots)

    # ==================== JOBS ====================

    def get_jobs(self, limit: int = 100, status: str | None = None) -> list[dict[str, Any]]:
        """Get jobs with optional filtering."""
        jobs = self._load_json(self._jobs_file)
        if status:
            jobs = [j for j in jobs if j.get("status") == status]
        # Sort by created_at descending
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]

    def save_job(self, job: dict[str, Any]) -> bool:
        """Save or update a job."""
        jobs = self._load_json(self._jobs_file)
        for i, j in enumerate(jobs):
            if j["id"] == job["id"]:
                jobs[i] = job
                return self._save_json(self._jobs_file, jobs)
        jobs.append(job)
        return self._save_json(self._jobs_file, jobs)

    def delete_job(self, job_id: str) -> bool:
        """Delete a job."""
        jobs = [j for j in self._load_json(self._jobs_file) if j["id"] != job_id]
        return self._save_json(self._jobs_file, jobs)

    # ==================== WORKFLOWS ====================

    def get_workflows(self) -> list[dict[str, Any]]:
        """Get all workflows from local storage."""
        return self._load_json(self._workflows_file)

    def save_workflow(self, workflow: dict[str, Any]) -> bool:
        """Save or update a workflow."""
        workflows = self.get_workflows()
        for i, w in enumerate(workflows):
            if w["id"] == workflow["id"]:
                workflows[i] = workflow
                return self._save_json(self._workflows_file, workflows)
        workflows.append(workflow)
        return self._save_json(self._workflows_file, workflows)

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        workflows = [w for w in self.get_workflows() if w["id"] != workflow_id]
        return self._save_json(self._workflows_file, workflows)

    # ==================== SCHEDULES ====================

    def get_schedules(self) -> list[dict[str, Any]]:
        """Get all schedules from local storage."""
        return self._load_json(self._schedules_file)

    def save_schedule(self, schedule: dict[str, Any]) -> bool:
        """Save or update a schedule."""
        schedules = self.get_schedules()
        for i, s in enumerate(schedules):
            if s["id"] == schedule["id"]:
                schedules[i] = schedule
                return self._save_json(self._schedules_file, schedules)
        schedules.append(schedule)
        return self._save_json(self._schedules_file, schedules)

    def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        schedules = [s for s in self.get_schedules() if s["id"] != schedule_id]
        return self._save_json(self._schedules_file, schedules)

    # ==================== TRIGGERS ====================

    def get_triggers(self) -> list[dict[str, Any]]:
        """Get all triggers from local storage."""
        return self._load_json(self._triggers_file)

    def save_trigger(self, trigger: dict[str, Any]) -> bool:
        """Save or update a trigger."""
        triggers = self.get_triggers()
        for i, t in enumerate(triggers):
            if t["id"] == trigger["id"]:
                triggers[i] = trigger
                return self._save_json(self._triggers_file, triggers)
        triggers.append(trigger)
        return self._save_json(self._triggers_file, triggers)

    def delete_trigger(self, trigger_id: str) -> bool:
        """Delete a trigger."""
        triggers = [t for t in self.get_triggers() if t["id"] != trigger_id]
        return self._save_json(self._triggers_file, triggers)

    def delete_triggers_by_scenario(self, scenario_id: str) -> int:
        """Delete all triggers for a scenario. Returns count deleted."""
        triggers = self.get_triggers()
        original_count = len(triggers)
        filtered = [t for t in triggers if t.get("scenario_id") != scenario_id]
        self._save_json(self._triggers_file, filtered)
        return original_count - len(filtered)
