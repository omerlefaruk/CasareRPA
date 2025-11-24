"""
CasareRPA Robot Agent
Main entry point for the background service.
"""
import asyncio
import os
from datetime import datetime
from loguru import logger
from dotenv import load_dotenv
from supabase import create_client, Client

from .config import get_robot_id, ROBOT_NAME

load_dotenv()

class RobotAgent:
    def __init__(self):
        self.robot_id = get_robot_id()
        self.name = ROBOT_NAME
        self.running = False
        self.connected = False
        self.client: Client = None
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        logger.add("logs/robot_{time}.log", rotation="1 day")
        logger.info(f"Initializing Robot Agent: {self.name} ({self.robot_id})")

    async def start(self):
        """Start the agent loop."""
        self.running = True
        logger.info("Agent started.")
        
        while self.running:
            try:
                if not self.connected:
                    await self.connect()
                
                if self.connected:
                    # Heartbeat
                    await self.heartbeat()
                    
                    # Check for jobs
                    await self.check_for_jobs()
                
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Agent loop error: {e}")
                await asyncio.sleep(10)

    async def connect(self):
        """Establish connection to Supabase."""
        if not self.url or not self.key:
            logger.warning("Supabase credentials not found. Running in offline mode.")
            return

        try:
            logger.info("Connecting to Supabase...")
            self.client = create_client(self.url, self.key)
            self.connected = True
            logger.info("Connected to Supabase.")
            
            # Register Robot
            await self.register()
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.connected = False

    async def register(self):
        """Register or update robot presence."""
        try:
            data = {
                "id": self.robot_id,
                "name": self.name,
                "status": "online",
                "last_seen": datetime.utcnow().isoformat()
            }
            await asyncio.to_thread(
                lambda: self.client.table("robots").upsert(data).execute()
            )
        except Exception as e:
            logger.error(f"Failed to register: {e}")

    async def heartbeat(self):
        """Update last_seen timestamp."""
        try:
            await asyncio.to_thread(
                lambda: self.client.table("robots").update({
                    "last_seen": datetime.utcnow().isoformat(),
                    "status": "online"
                }).eq("id", self.robot_id).execute()
            )
        except Exception as e:
            logger.error(f"Heartbeat failed: {e}")

    async def check_for_jobs(self):
        """Check if there are any pending jobs for this robot."""
        try:
            response = await asyncio.to_thread(
                lambda: self.client.table("jobs")
                .select("*")
                .eq("robot_id", self.robot_id)
                .eq("status", "pending")
                .execute()
            )
            
            jobs = response.data
            for job in jobs:
                await self.process_job(job)
                
        except Exception as e:
            logger.error(f"Job check failed: {e}")

    async def process_job(self, job):
        """Execute a job."""
        job_id = job["id"]
        logger.info(f"Processing job {job_id}: {job['workflow']}")
        
        # Update status to running
        await asyncio.to_thread(
            lambda: self.client.table("jobs").update({"status": "running"}).eq("id", job_id).execute()
        )
        
        # TODO: Actual execution logic here
        await asyncio.sleep(2) # Simulate work
        
        # Update status to success
        await asyncio.to_thread(
            lambda: self.client.table("jobs").update({"status": "success"}).eq("id", job_id).execute()
        )
        logger.info(f"Job {job_id} completed.")

    def stop(self):
        """Stop the agent."""
        self.running = False
        if self.connected and self.client:
            try:
                # Try to set status to offline
                self.client.table("robots").update({"status": "offline"}).eq("id", self.robot_id).execute()
            except:
                pass
        logger.info("Agent stopping...")
