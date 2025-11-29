"""
Robot management service.
Handles robot registration, status updates, and availability checks.
"""

import os
import asyncio
from datetime import datetime
from typing import List, Optional, Callable

from loguru import logger
from dotenv import load_dotenv

from casare_rpa.domain.orchestrator.entities import Robot, RobotStatus
from casare_rpa.infrastructure.orchestrator.persistence import LocalStorageRepository

load_dotenv()


class RobotManagementService:
    """
    Service for managing robot lifecycle and status.
    Supports both cloud (Supabase) and local storage modes.
    """

    def __init__(self):
        self._supabase_url = os.getenv("SUPABASE_URL")
        self._supabase_key = os.getenv("SUPABASE_KEY")
        self._client = None
        self._connected = False
        self._use_local = False
        self._local_storage = LocalStorageRepository()

        # Event callbacks
        self._on_robot_update: Optional[Callable[[Robot], None]] = None

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

    # ==================== ROBOT OPERATIONS ====================

    async def get_robots(self) -> List[Robot]:
        """Get all registered robots."""
        if self._use_local:
            data = self._local_storage.get_robots()
        else:
            try:
                response = await asyncio.to_thread(
                    lambda: self._client.table("robots")
                    .select("*")
                    .order("last_seen", desc=True)
                    .execute()
                )
                data = response.data
            except Exception as e:
                logger.error(f"Failed to fetch robots: {e}")
                data = []

        return [Robot.from_dict(r) for r in data]

    async def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Get a specific robot by ID."""
        robots = await self.get_robots()
        for robot in robots:
            if robot.id == robot_id:
                return robot
        return None

    async def get_available_robots(self) -> List[Robot]:
        """Get robots that can accept new jobs."""
        robots = await self.get_robots()
        return [r for r in robots if r.is_available]

    async def update_robot_status(self, robot_id: str, status: RobotStatus) -> bool:
        """Update robot status."""
        data = {"status": status.value, "last_seen": datetime.utcnow().isoformat()}

        if self._use_local:
            robots = self._local_storage.get_robots()
            for r in robots:
                if r["id"] == robot_id:
                    r.update(data)
                    return self._local_storage.save_robot(r)
            return False
        else:
            try:
                await asyncio.to_thread(
                    lambda: self._client.table("robots")
                    .update(data)
                    .eq("id", robot_id)
                    .execute()
                )
                return True
            except Exception as e:
                logger.error(f"Failed to update robot status: {e}")
                return False
