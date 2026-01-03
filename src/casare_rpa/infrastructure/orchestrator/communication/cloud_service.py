"""
Cloud Service Interface
Handles communication with Supabase.
"""

import asyncio
import os
from typing import Any

from dotenv import load_dotenv
from loguru import logger
from supabase import Client, create_client

load_dotenv()


class CloudService:
    def __init__(self):
        self.connected = False
        self.client: Client = None
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

    async def connect(self):
        """Connect to Supabase."""
        if not self.url or not self.key:
            logger.error("SUPABASE_URL or SUPABASE_KEY not found in environment.")
            return

        try:
            logger.info("Connecting to Supabase...")
            # Supabase client creation is synchronous but lightweight
            self.client = create_client(self.url, self.key)
            self.connected = True
            logger.info("Connected to Supabase.")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")

    async def get_robots(self) -> list[dict[str, Any]]:
        """Fetch list of connected robots."""
        if not self.connected:
            await self.connect()

        if not self.client:
            return []

        try:
            # Run in executor to avoid blocking async loop
            response = await asyncio.to_thread(
                lambda: self.client.table("robots")
                .select("*")
                .order("last_seen", desc=True)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch robots: {e}")
            return []

    async def get_jobs(self) -> list[dict[str, Any]]:
        """Fetch job history."""
        if not self.connected:
            await self.connect()

        if not self.client:
            return []

        try:
            response = await asyncio.to_thread(
                lambda: self.client.table("jobs")
                .select("*")
                .order("created_at", desc=True)
                .limit(50)
                .execute()
            )
            return response.data
        except Exception as e:
            logger.error(f"Failed to fetch jobs: {e}")
            return []

    async def dispatch_job(self, robot_id: str, workflow_json: str):
        """Send a job to a robot."""
        if not self.client:
            return False

        logger.info(f"Dispatching workflow to robot {robot_id}")
        try:
            data = {
                "robot_id": robot_id,
                "workflow": workflow_json,
                "status": "pending",
            }
            await asyncio.to_thread(lambda: self.client.table("jobs").insert(data).execute())
            return True
        except Exception as e:
            logger.error(f"Failed to dispatch job: {e}")
            return False
