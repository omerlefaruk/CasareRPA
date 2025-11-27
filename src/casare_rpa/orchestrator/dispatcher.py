"""
Job Dispatcher for CasareRPA Orchestrator.
Handles robot selection, load balancing, and job assignment.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Set, Callable, Any
from collections import defaultdict
from enum import Enum
import random

from loguru import logger

from .models import Job, Robot, RobotStatus
from .job_queue import JobQueue


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for robot selection."""

    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    AFFINITY = "affinity"  # Prefer robots that ran this workflow before


class RobotPool:
    """
    A group of robots with shared configuration.

    Pools can be used for:
    - Environment separation (Production, Development, Test)
    - Workload isolation
    - Resource allocation
    """

    def __init__(
        self,
        name: str,
        tags: Optional[List[str]] = None,
        max_concurrent_jobs: Optional[int] = None,
        allowed_workflows: Optional[Set[str]] = None,
    ):
        """
        Initialize robot pool.

        Args:
            name: Pool name
            tags: Tags that robots must have to be in this pool
            max_concurrent_jobs: Max jobs across all robots in pool
            allowed_workflows: Workflow IDs allowed in this pool
        """
        self.name = name
        self.tags = set(tags) if tags else set()
        self.max_concurrent_jobs = max_concurrent_jobs
        self.allowed_workflows = allowed_workflows
        self._robots: Dict[str, Robot] = {}

    def add_robot(self, robot: Robot) -> bool:
        """Add a robot to the pool if it matches tags."""
        if self.tags:
            robot_tags = set(robot.tags) if robot.tags else set()
            if not self.tags.issubset(robot_tags):
                return False

        self._robots[robot.id] = robot
        return True

    def remove_robot(self, robot_id: str):
        """Remove a robot from the pool."""
        self._robots.pop(robot_id, None)

    def get_robots(self) -> List[Robot]:
        """Get all robots in the pool."""
        return list(self._robots.values())

    def get_available_robots(self) -> List[Robot]:
        """Get available robots in the pool."""
        return [r for r in self._robots.values() if r.is_available]

    def get_current_job_count(self) -> int:
        """Get total jobs currently running in pool."""
        return sum(r.current_jobs for r in self._robots.values())

    def can_accept_job(self) -> bool:
        """Check if pool can accept more jobs."""
        if self.max_concurrent_jobs is None:
            return True
        return self.get_current_job_count() < self.max_concurrent_jobs

    def is_workflow_allowed(self, workflow_id: str) -> bool:
        """Check if workflow is allowed in this pool."""
        if self.allowed_workflows is None:
            return True
        return workflow_id in self.allowed_workflows

    @property
    def utilization(self) -> float:
        """Get pool utilization percentage."""
        if not self._robots:
            return 0.0
        total_capacity = sum(r.max_concurrent_jobs for r in self._robots.values())
        if total_capacity == 0:
            return 0.0
        current_load = sum(r.current_jobs for r in self._robots.values())
        return (current_load / total_capacity) * 100

    @property
    def online_count(self) -> int:
        """Get count of online robots."""
        return sum(1 for r in self._robots.values() if r.status == RobotStatus.ONLINE)


class JobDispatcher:
    """
    Dispatches jobs to robots with load balancing.

    Features:
    - Multiple load balancing strategies
    - Robot pool support
    - Concurrent job limits
    - Workflow-robot affinity
    - Health checking
    """

    def __init__(
        self,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_LOADED,
        dispatch_interval_seconds: int = 5,
        health_check_interval_seconds: int = 30,
        stale_robot_timeout_seconds: int = 60,
    ):
        """
        Initialize dispatcher.

        Args:
            strategy: Load balancing strategy
            dispatch_interval_seconds: How often to dispatch jobs
            health_check_interval_seconds: How often to check robot health
            stale_robot_timeout_seconds: Mark robot offline if no heartbeat
        """
        self._strategy = strategy
        self._dispatch_interval = dispatch_interval_seconds
        self._health_check_interval = health_check_interval_seconds
        self._stale_timeout = timedelta(seconds=stale_robot_timeout_seconds)

        self._robots: Dict[str, Robot] = {}
        self._pools: Dict[str, RobotPool] = {}
        self._default_pool = RobotPool("default")

        # Round-robin state
        self._rr_index = 0

        # Affinity tracking: workflow_id -> {robot_id -> success_count}
        self._affinity: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )

        # Callbacks
        self._on_robot_status_change: Optional[
            Callable[[Robot, RobotStatus, RobotStatus], None]
        ] = None
        self._on_job_dispatched: Optional[Callable[[Job, Robot], None]] = None

        # Running state
        self._running = False
        self._dispatch_task: Optional[asyncio.Task] = None
        self._health_task: Optional[asyncio.Task] = None

        logger.info(f"JobDispatcher initialized with {strategy.value} strategy")

    def set_callbacks(
        self,
        on_robot_status_change: Optional[
            Callable[[Robot, RobotStatus, RobotStatus], None]
        ] = None,
        on_job_dispatched: Optional[Callable[[Job, Robot], None]] = None,
    ):
        """Set event callbacks."""
        self._on_robot_status_change = on_robot_status_change
        self._on_job_dispatched = on_job_dispatched

    # ==================== ROBOT MANAGEMENT ====================

    def register_robot(self, robot: Robot, pool_name: str = "default") -> bool:
        """
        Register a robot with the dispatcher.

        Args:
            robot: Robot to register
            pool_name: Pool to assign robot to

        Returns:
            True if registered successfully
        """
        self._robots[robot.id] = robot

        # Add to pool
        pool = self._pools.get(pool_name, self._default_pool)
        pool.add_robot(robot)

        logger.info(f"Robot '{robot.name}' registered in pool '{pool_name}'")
        return True

    def unregister_robot(self, robot_id: str):
        """Unregister a robot."""
        robot = self._robots.pop(robot_id, None)
        if robot:
            # Remove from all pools
            for pool in self._pools.values():
                pool.remove_robot(robot_id)
            self._default_pool.remove_robot(robot_id)
            logger.info(f"Robot '{robot.name}' unregistered")

    def update_robot(self, robot: Robot):
        """Update robot state."""
        old_robot = self._robots.get(robot.id)
        old_status = old_robot.status if old_robot else None

        self._robots[robot.id] = robot

        # Notify status change
        if old_status and old_status != robot.status and self._on_robot_status_change:
            self._on_robot_status_change(robot, old_status, robot.status)

    def update_robot_heartbeat(self, robot_id: str):
        """Update robot heartbeat timestamp."""
        robot = self._robots.get(robot_id)
        if robot:
            robot.last_heartbeat = datetime.utcnow()
            robot.last_seen = datetime.utcnow()

    def get_robot(self, robot_id: str) -> Optional[Robot]:
        """Get robot by ID."""
        return self._robots.get(robot_id)

    def get_all_robots(self) -> List[Robot]:
        """Get all registered robots."""
        return list(self._robots.values())

    def get_available_robots(self) -> List[Robot]:
        """Get all available robots."""
        return [r for r in self._robots.values() if r.is_available]

    def get_robots_by_status(self, status: RobotStatus) -> List[Robot]:
        """Get robots by status."""
        return [r for r in self._robots.values() if r.status == status]

    # ==================== POOL MANAGEMENT ====================

    def create_pool(
        self,
        name: str,
        tags: Optional[List[str]] = None,
        max_concurrent_jobs: Optional[int] = None,
        allowed_workflows: Optional[Set[str]] = None,
    ) -> RobotPool:
        """Create a robot pool."""
        pool = RobotPool(name, tags, max_concurrent_jobs, allowed_workflows)
        self._pools[name] = pool

        # Add matching robots to pool
        for robot in self._robots.values():
            pool.add_robot(robot)

        logger.info(f"Pool '{name}' created with {len(pool.get_robots())} robots")
        return pool

    def delete_pool(self, name: str) -> bool:
        """Delete a robot pool."""
        if name == "default":
            return False
        return self._pools.pop(name, None) is not None

    def get_pool(self, name: str) -> Optional[RobotPool]:
        """Get a pool by name."""
        return self._pools.get(name, self._default_pool if name == "default" else None)

    def get_all_pools(self) -> Dict[str, RobotPool]:
        """Get all pools."""
        pools = dict(self._pools)
        pools["default"] = self._default_pool
        return pools

    # ==================== JOB DISPATCH ====================

    def select_robot(
        self, job: Job, pool_name: Optional[str] = None
    ) -> Optional[Robot]:
        """
        Select the best robot for a job.

        Args:
            job: Job to assign
            pool_name: Optional pool to select from

        Returns:
            Selected robot or None if no suitable robot
        """
        # Get candidate robots
        if pool_name:
            pool = self._pools.get(pool_name)
            if not pool:
                logger.warning(f"Pool '{pool_name}' not found")
                return None
            candidates = pool.get_available_robots()
        else:
            candidates = self.get_available_robots()

        if not candidates:
            return None

        # If job has specific robot, check if it's available
        if job.robot_id:
            specific = next((r for r in candidates if r.id == job.robot_id), None)
            if specific:
                return specific
            # Specific robot not available
            return None

        # Apply load balancing strategy
        if self._strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(candidates)
        elif self._strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._select_least_loaded(candidates)
        elif self._strategy == LoadBalancingStrategy.RANDOM:
            return self._select_random(candidates)
        elif self._strategy == LoadBalancingStrategy.AFFINITY:
            return self._select_affinity(job, candidates)

        return candidates[0] if candidates else None

    def _select_round_robin(self, candidates: List[Robot]) -> Optional[Robot]:
        """Round-robin robot selection."""
        if not candidates:
            return None
        self._rr_index = (self._rr_index + 1) % len(candidates)
        return candidates[self._rr_index]

    def _select_least_loaded(self, candidates: List[Robot]) -> Optional[Robot]:
        """Select robot with lowest utilization."""
        if not candidates:
            return None
        return min(candidates, key=lambda r: r.utilization)

    def _select_random(self, candidates: List[Robot]) -> Optional[Robot]:
        """Random robot selection."""
        if not candidates:
            return None
        return random.choice(candidates)

    def _select_affinity(self, job: Job, candidates: List[Robot]) -> Optional[Robot]:
        """Select robot with best affinity for workflow."""
        if not candidates:
            return None

        workflow_affinity = self._affinity.get(job.workflow_id, {})
        if not workflow_affinity:
            # No affinity data, fall back to least loaded
            return self._select_least_loaded(candidates)

        # Find candidate with highest success count for this workflow
        best_robot = None
        best_score = -1

        for robot in candidates:
            score = workflow_affinity.get(robot.id, 0)
            if score > best_score:
                best_score = score
                best_robot = robot

        return best_robot or self._select_least_loaded(candidates)

    def record_job_result(self, job: Job, success: bool):
        """
        Record job result for affinity tracking.

        Args:
            job: Completed job
            success: Whether job succeeded
        """
        if success and job.robot_id:
            self._affinity[job.workflow_id][job.robot_id] += 1

    # ==================== DISPATCH LOOP ====================

    async def start(self, job_queue: JobQueue):
        """
        Start the dispatcher.

        Args:
            job_queue: Job queue to dispatch from
        """
        if self._running:
            return

        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop(job_queue))
        self._health_task = asyncio.create_task(self._health_check_loop())

        logger.info("JobDispatcher started")

    async def stop(self):
        """Stop the dispatcher."""
        self._running = False

        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

        logger.info("JobDispatcher stopped")

    async def _dispatch_loop(self, job_queue: JobQueue):
        """Main dispatch loop."""
        while self._running:
            try:
                await self._dispatch_pending_jobs(job_queue)
                await asyncio.sleep(self._dispatch_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Dispatch loop error: {e}")
                await asyncio.sleep(self._dispatch_interval)

    async def _dispatch_pending_jobs(self, job_queue: JobQueue):
        """Try to dispatch pending jobs to available robots."""
        available_robots = self.get_available_robots()

        for robot in available_robots:
            # Try to get a job for this robot
            job = job_queue.dequeue(robot)
            if job:
                # Update robot's current job count
                robot.current_jobs += 1

                # Notify callback
                if self._on_job_dispatched:
                    try:
                        result = self._on_job_dispatched(job, robot)
                        if asyncio.iscoroutine(result):
                            await result
                    except Exception as e:
                        logger.error(f"Job dispatch callback error: {e}")

                logger.info(f"Dispatched job {job.id[:8]} to robot {robot.name}")

    async def _health_check_loop(self):
        """Check robot health periodically."""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self._check_robot_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    async def _check_robot_health(self):
        """Check health of all robots."""
        now = datetime.utcnow()

        for robot in list(self._robots.values()):
            if robot.status == RobotStatus.OFFLINE:
                continue

            # Check heartbeat
            last_heartbeat = robot.last_heartbeat
            if isinstance(last_heartbeat, str):
                last_heartbeat = datetime.fromisoformat(last_heartbeat.replace("Z", ""))

            if last_heartbeat and now - last_heartbeat > self._stale_timeout:
                # Robot is stale, mark offline
                old_status = robot.status
                robot.status = RobotStatus.OFFLINE
                logger.warning(
                    f"Robot '{robot.name}' marked offline (no heartbeat for "
                    f"{(now - last_heartbeat).total_seconds():.0f}s)"
                )

                if self._on_robot_status_change:
                    self._on_robot_status_change(robot, old_status, robot.status)

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get dispatcher statistics."""
        total_robots = len(self._robots)
        online = sum(1 for r in self._robots.values() if r.status == RobotStatus.ONLINE)
        busy = sum(1 for r in self._robots.values() if r.status == RobotStatus.BUSY)
        offline = sum(
            1 for r in self._robots.values() if r.status == RobotStatus.OFFLINE
        )
        error = sum(1 for r in self._robots.values() if r.status == RobotStatus.ERROR)

        total_capacity = sum(r.max_concurrent_jobs for r in self._robots.values())
        current_load = sum(r.current_jobs for r in self._robots.values())

        return {
            "total_robots": total_robots,
            "online": online,
            "busy": busy,
            "offline": offline,
            "error": error,
            "total_capacity": total_capacity,
            "current_load": current_load,
            "utilization": (current_load / total_capacity * 100)
            if total_capacity > 0
            else 0,
            "strategy": self._strategy.value,
            "pools": {
                name: {
                    "robots": len(pool.get_robots()),
                    "available": len(pool.get_available_robots()),
                    "utilization": pool.utilization,
                }
                for name, pool in self.get_all_pools().items()
            },
        }
