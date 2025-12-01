"""
Schedule management service.
Handles schedule CRUD operations and enable/disable toggling.
"""

import os
import asyncio
from datetime import datetime, timezone
from typing import List, Optional

from loguru import logger
from dotenv import load_dotenv

from casare_rpa.domain.orchestrator.entities import Schedule
from casare_rpa.domain.orchestrator.repositories import ScheduleRepository

load_dotenv()


class ScheduleManagementService:
    """Service for managing schedules."""

    def __init__(self, schedule_repository: ScheduleRepository):
        """Initialize with injected repository."""
        self._schedule_repository = schedule_repository
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._client = None
        self._connected = False
        self._use_local = True  # Default to local mode

    @property
    def is_cloud_mode(self) -> bool:
        """Check if using cloud (Supabase) mode."""
        return self._connected and not self._use_local

    async def connect(self) -> bool:
        """Connect to Supabase or fall back to local storage."""
        if not self._supabase_url or not self._supabase_key:
            logger.warning("Supabase credentials not found. Using local storage mode.")
            self._use_local = True
            return True

        try:
            from supabase import create_client

            logger.info("Connecting to Supabase...")
            self._client = create_client(self._supabase_url, self._supabase_key)
            self._connected = True
            self._use_local = False
            logger.info("Connected to Supabase successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}. Using local storage.")
            self._use_local = True
            return True

    async def get_schedules(self, enabled_only: bool = False) -> List[Schedule]:
        """Get all schedules."""
        if self._use_local:
            if enabled_only:
                return await self._schedule_repository.get_enabled()
            return await self._schedule_repository.get_all()
        else:
            try:
                query = self._client.table("schedules").select("*")
                if enabled_only:
                    query = query.eq("enabled", True)
                query = query.order("next_run", desc=False)
                response = await asyncio.to_thread(lambda: query.execute())
                data = response.data
            except Exception as e:
                logger.error(f"Failed to fetch schedules: {e}")
                data = []

        return [Schedule.from_dict(s) for s in data]

    async def get_schedule(self, schedule_id: str) -> Optional[Schedule]:
        """Get a specific schedule by ID."""
        schedules = await self.get_schedules()
        for s in schedules:
            if s.id == schedule_id:
                return s
        return None

    async def save_schedule(self, schedule: Schedule) -> bool:
        """Save or update a schedule."""
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "id": schedule.id,
            "name": schedule.name,
            "workflow_id": schedule.workflow_id,
            "workflow_name": schedule.workflow_name,
            "robot_id": schedule.robot_id,
            "robot_name": schedule.robot_name,
            "frequency": schedule.frequency.value,
            "cron_expression": schedule.cron_expression,
            "timezone": schedule.timezone,
            "enabled": schedule.enabled,
            "priority": schedule.priority.value,
            "last_run": schedule.last_run,
            "next_run": schedule.next_run,
            "run_count": schedule.run_count,
            "success_count": schedule.success_count,
            "created_at": schedule.created_at or now,
            "created_by": schedule.created_by,
        }

        if self._use_local:
            schedule_entity = Schedule.from_dict(data)
            await self._schedule_repository.save(schedule_entity)
            return True
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("schedules").upsert(data).execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to save schedule: {e}")
                return False

    async def toggle_schedule(self, schedule_id: str, enabled: bool) -> bool:
        """Enable or disable a schedule."""
        schedule = await self.get_schedule(schedule_id)
        if schedule:
            schedule.enabled = enabled
            return await self.save_schedule(schedule)
        return False

    async def delete_schedule(self, schedule_id: str) -> bool:
        """Delete a schedule."""
        if self._use_local:
            await self._schedule_repository.delete(schedule_id)
            return True
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("schedules")
                    .delete()
                    .eq("id", schedule_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to delete schedule: {e}")
                return False
