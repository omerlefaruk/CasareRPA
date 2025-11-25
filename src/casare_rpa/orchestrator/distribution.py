"""
Workflow Distribution System for CasareRPA Orchestrator.
Handles intelligent job distribution to robots with load balancing and capability matching.
"""
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import random

from loguru import logger

from .models import Robot, RobotStatus, Job, JobStatus, Workflow


class DistributionStrategy(Enum):
    """Strategies for distributing jobs to robots."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    RANDOM = "random"
    CAPABILITY_MATCH = "capability_match"
    AFFINITY = "affinity"


@dataclass
class DistributionRule:
    """Rule for job distribution."""
    name: str
    workflow_pattern: str = "*"  # Glob pattern for workflow names
    required_tags: List[str] = field(default_factory=list)
    preferred_robots: List[str] = field(default_factory=list)
    excluded_robots: List[str] = field(default_factory=list)
    environment: Optional[str] = None
    strategy: DistributionStrategy = DistributionStrategy.LEAST_LOADED
    priority_boost: int = 0  # Add to job priority


@dataclass
class DistributionResult:
    """Result of a job distribution attempt."""
    success: bool
    job_id: str
    robot_id: Optional[str] = None
    message: str = ""
    retry_count: int = 0
    attempted_robots: List[str] = field(default_factory=list)


class RobotSelector:
    """
    Selects the best robot for a job based on various criteria.
    """

    def __init__(self):
        self._last_selected: Dict[str, int] = {}  # For round-robin
        self._robot_affinity: Dict[str, str] = {}  # workflow_id -> robot_id

    def select(
        self,
        job: Job,
        available_robots: List[Robot],
        strategy: DistributionStrategy = DistributionStrategy.LEAST_LOADED,
        required_tags: Optional[List[str]] = None,
        preferred_robots: Optional[List[str]] = None,
        excluded_robots: Optional[List[str]] = None,
    ) -> Optional[Robot]:
        """
        Select the best robot for a job.

        Args:
            job: Job to assign
            available_robots: List of available robots
            strategy: Distribution strategy to use
            required_tags: Tags the robot must have
            preferred_robots: Preferred robot IDs
            excluded_robots: Robot IDs to exclude

        Returns:
            Selected robot or None if no suitable robot found
        """
        if not available_robots:
            return None

        # Filter by availability
        candidates = [r for r in available_robots if r.status == RobotStatus.ONLINE]

        # Filter by environment
        job_env = getattr(job, 'environment', None)
        if job_env:
            candidates = [r for r in candidates if r.environment == job_env]

        # Filter by required tags
        if required_tags:
            candidates = [
                r for r in candidates
                if all(tag in r.tags for tag in required_tags)
            ]

        # Filter out excluded robots
        if excluded_robots:
            candidates = [r for r in candidates if r.id not in excluded_robots]

        if not candidates:
            return None

        # Prefer specified robots
        if preferred_robots:
            preferred = [r for r in candidates if r.id in preferred_robots]
            if preferred:
                candidates = preferred

        # Apply strategy
        if strategy == DistributionStrategy.ROUND_ROBIN:
            return self._select_round_robin(candidates)
        elif strategy == DistributionStrategy.LEAST_LOADED:
            return self._select_least_loaded(candidates)
        elif strategy == DistributionStrategy.RANDOM:
            return self._select_random(candidates)
        elif strategy == DistributionStrategy.CAPABILITY_MATCH:
            return self._select_by_capability(job, candidates)
        elif strategy == DistributionStrategy.AFFINITY:
            return self._select_by_affinity(job, candidates)
        else:
            return self._select_least_loaded(candidates)

    def _select_round_robin(self, robots: List[Robot]) -> Robot:
        """Select using round-robin."""
        robot_ids = sorted([r.id for r in robots])
        robot_map = {r.id: r for r in robots}

        # Find next robot in rotation
        last_idx = -1
        for i, rid in enumerate(robot_ids):
            if rid in self._last_selected:
                last_idx = max(last_idx, self._last_selected[rid])

        next_idx = (last_idx + 1) % len(robot_ids)
        selected_id = robot_ids[next_idx]

        self._last_selected[selected_id] = next_idx
        return robot_map[selected_id]

    def _select_least_loaded(self, robots: List[Robot]) -> Robot:
        """Select robot with fewest current jobs."""
        return min(robots, key=lambda r: (
            r.current_jobs / max(r.max_concurrent_jobs, 1),
            r.metrics.get("cpu_percent", 0.0) if r.metrics else 0.0
        ))

    def _select_random(self, robots: List[Robot]) -> Robot:
        """Select random robot."""
        return random.choice(robots)

    def _select_by_capability(self, job: Job, robots: List[Robot]) -> Robot:
        """Select robot with best capability match."""
        # Score robots by tag match
        job_tags = set(getattr(job, 'tags', []) or [])

        def score(robot: Robot) -> tuple:
            robot_tags = set(robot.tags or [])
            common_tags = len(job_tags & robot_tags)
            load_factor = robot.current_jobs / max(robot.max_concurrent_jobs, 1)
            return (-common_tags, load_factor)

        return min(robots, key=score)

    def _select_by_affinity(self, job: Job, robots: List[Robot]) -> Robot:
        """Select robot based on workflow affinity (sticky sessions)."""
        robot_map = {r.id: r for r in robots}

        # Check if we have affinity for this workflow
        if job.workflow_id in self._robot_affinity:
            affine_robot_id = self._robot_affinity[job.workflow_id]
            if affine_robot_id in robot_map:
                return robot_map[affine_robot_id]

        # No affinity, select least loaded and set affinity
        selected = self._select_least_loaded(robots)
        self._robot_affinity[job.workflow_id] = selected.id
        return selected

    def clear_affinity(self, workflow_id: str):
        """Clear affinity for a workflow."""
        self._robot_affinity.pop(workflow_id, None)

    def clear_all_affinity(self):
        """Clear all affinity mappings."""
        self._robot_affinity.clear()


class WorkflowDistributor:
    """
    Distributes workflows to robots.

    Integrates with the orchestrator server to send jobs to selected robots
    and handles distribution rules, retries, and failure handling.
    """

    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 5.0,
        distribution_timeout: float = 30.0,
    ):
        """
        Initialize the workflow distributor.

        Args:
            max_retries: Maximum retry attempts per job
            retry_delay: Delay between retries in seconds
            distribution_timeout: Timeout for job acceptance
        """
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._distribution_timeout = distribution_timeout

        self._selector = RobotSelector()
        self._rules: List[DistributionRule] = []
        self._default_strategy = DistributionStrategy.LEAST_LOADED

        # Distribution tracking
        self._pending_distributions: Dict[str, asyncio.Task] = {}
        self._distribution_history: List[DistributionResult] = []
        self._max_history = 1000

        # Send function (to be set by engine)
        self._send_job_fn: Optional[Callable] = None

        # Callbacks
        self._on_distribution_success: Optional[Callable] = None
        self._on_distribution_failure: Optional[Callable] = None

        logger.info("WorkflowDistributor initialized")

    def set_send_job_function(self, fn: Callable):
        """Set the function to send jobs to robots."""
        self._send_job_fn = fn

    def set_callbacks(
        self,
        on_success: Optional[Callable] = None,
        on_failure: Optional[Callable] = None,
    ):
        """Set distribution callbacks."""
        self._on_distribution_success = on_success
        self._on_distribution_failure = on_failure

    def add_rule(self, rule: DistributionRule):
        """Add a distribution rule."""
        self._rules.append(rule)
        logger.debug(f"Added distribution rule: {rule.name}")

    def remove_rule(self, name: str) -> bool:
        """Remove a distribution rule by name."""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False

    def clear_rules(self):
        """Clear all distribution rules."""
        self._rules.clear()

    def _find_matching_rule(self, job: Job) -> Optional[DistributionRule]:
        """Find the first rule that matches a job."""
        import fnmatch

        job_env = getattr(job, 'environment', None)

        for rule in self._rules:
            # Check workflow pattern
            if rule.workflow_pattern != "*":
                if not fnmatch.fnmatch(job.workflow_name, rule.workflow_pattern):
                    continue

            # Check environment
            if rule.environment and job_env != rule.environment:
                continue

            return rule

        return None

    async def distribute(
        self,
        job: Job,
        available_robots: List[Robot],
        strategy: Optional[DistributionStrategy] = None,
    ) -> DistributionResult:
        """
        Distribute a job to an available robot.

        Args:
            job: Job to distribute
            available_robots: List of available robots
            strategy: Optional strategy override

        Returns:
            Distribution result
        """
        if not self._send_job_fn:
            return DistributionResult(
                success=False,
                job_id=job.id,
                message="No send function configured",
            )

        # Find matching rule
        rule = self._find_matching_rule(job)

        # Determine strategy
        use_strategy = strategy or (rule.strategy if rule else self._default_strategy)

        # Get rule parameters
        required_tags = rule.required_tags if rule else None
        preferred_robots = rule.preferred_robots if rule else None
        excluded_robots = rule.excluded_robots if rule else None

        attempted_robots = []
        retry_count = 0

        for attempt in range(self._max_retries + 1):
            # Select robot
            robot = self._selector.select(
                job=job,
                available_robots=[r for r in available_robots if r.id not in attempted_robots],
                strategy=use_strategy,
                required_tags=required_tags,
                preferred_robots=preferred_robots,
                excluded_robots=excluded_robots,
            )

            if not robot:
                break

            attempted_robots.append(robot.id)

            # Try to send job
            try:
                result = await asyncio.wait_for(
                    self._send_job_fn(robot.id, job),
                    timeout=self._distribution_timeout,
                )

                if result.get("accepted"):
                    dist_result = DistributionResult(
                        success=True,
                        job_id=job.id,
                        robot_id=robot.id,
                        message="Job accepted",
                        retry_count=retry_count,
                        attempted_robots=attempted_robots,
                    )
                    self._record_result(dist_result)

                    if self._on_distribution_success:
                        try:
                            callback_result = self._on_distribution_success(job.id, robot.id)
                            if asyncio.iscoroutine(callback_result):
                                await callback_result
                        except Exception as e:
                            logger.error(f"Distribution success callback error: {e}")

                    return dist_result

                # Job rejected, try next robot
                retry_count += 1
                logger.warning(
                    f"Job {job.id[:8]} rejected by robot {robot.id}: "
                    f"{result.get('reason', 'Unknown')}"
                )

            except asyncio.TimeoutError:
                retry_count += 1
                logger.warning(f"Timeout distributing job {job.id[:8]} to robot {robot.id}")

            except Exception as e:
                retry_count += 1
                logger.error(f"Error distributing job {job.id[:8]}: {e}")

            if attempt < self._max_retries:
                await asyncio.sleep(self._retry_delay)

        # All attempts failed
        dist_result = DistributionResult(
            success=False,
            job_id=job.id,
            message=f"Distribution failed after {retry_count} attempts",
            retry_count=retry_count,
            attempted_robots=attempted_robots,
        )
        self._record_result(dist_result)

        if self._on_distribution_failure:
            try:
                callback_result = self._on_distribution_failure(job.id, dist_result.message)
                if asyncio.iscoroutine(callback_result):
                    await callback_result
            except Exception as e:
                logger.error(f"Distribution failure callback error: {e}")

        return dist_result

    async def distribute_batch(
        self,
        jobs: List[Job],
        available_robots: List[Robot],
    ) -> List[DistributionResult]:
        """
        Distribute multiple jobs to available robots.

        Args:
            jobs: Jobs to distribute
            available_robots: Available robots

        Returns:
            List of distribution results
        """
        results = []

        # Sort jobs by priority (higher first)
        sorted_jobs = sorted(jobs, key=lambda j: getattr(j.priority, 'value', j.priority), reverse=True)

        for job in sorted_jobs:
            result = await self.distribute(job, available_robots)
            results.append(result)

            # Update available robots list
            if result.success and result.robot_id:
                available_robots = [
                    r for r in available_robots
                    if r.id != result.robot_id or r.current_jobs < r.max_concurrent_jobs - 1
                ]

        return results

    def _record_result(self, result: DistributionResult):
        """Record distribution result in history."""
        self._distribution_history.append(result)

        # Trim history
        if len(self._distribution_history) > self._max_history:
            self._distribution_history = self._distribution_history[-self._max_history:]

    def get_statistics(self) -> Dict[str, Any]:
        """Get distribution statistics."""
        total = len(self._distribution_history)
        successful = sum(1 for r in self._distribution_history if r.success)
        failed = total - successful

        return {
            "total_distributions": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "avg_retry_count": (
                sum(r.retry_count for r in self._distribution_history) / total
                if total > 0 else 0.0
            ),
            "rules_count": len(self._rules),
        }

    def get_recent_results(self, limit: int = 10) -> List[DistributionResult]:
        """Get recent distribution results."""
        return self._distribution_history[-limit:]


class JobRouter:
    """
    Routes jobs to appropriate robots based on job metadata.

    Handles job routing with support for:
    - Environment-based routing
    - Tag-based routing
    - Priority handling
    - Fallback strategies
    """

    def __init__(self):
        self._routes: Dict[str, List[str]] = {}  # environment -> robot_ids
        self._tag_routes: Dict[str, List[str]] = {}  # tag -> robot_ids
        self._fallback_robots: List[str] = []

    def add_route(self, environment: str, robot_ids: List[str]):
        """Add a route for an environment."""
        self._routes[environment] = robot_ids

    def add_tag_route(self, tag: str, robot_ids: List[str]):
        """Add a route for a tag."""
        self._tag_routes[tag] = robot_ids

    def set_fallback_robots(self, robot_ids: List[str]):
        """Set fallback robots for unmatched jobs."""
        self._fallback_robots = robot_ids

    def get_eligible_robots(
        self,
        job: Job,
        all_robots: List[Robot],
    ) -> List[Robot]:
        """
        Get robots eligible to run a job.

        Args:
            job: Job to route
            all_robots: All available robots

        Returns:
            List of eligible robots
        """
        robot_map = {r.id: r for r in all_robots}
        eligible_ids: Set[str] = set()

        # Check environment routes
        job_env = getattr(job, 'environment', None)
        if job_env and job_env in self._routes:
            eligible_ids.update(self._routes[job_env])

        # Check tag routes
        job_tags = getattr(job, 'tags', []) or []
        for tag in job_tags:
            if tag in self._tag_routes:
                eligible_ids.update(self._tag_routes[tag])

        # If no specific routes, use all robots or fallback
        if not eligible_ids:
            if self._fallback_robots:
                eligible_ids.update(self._fallback_robots)
            else:
                eligible_ids.update(robot_map.keys())

        # Filter to only existing robots
        return [robot_map[rid] for rid in eligible_ids if rid in robot_map]

    def clear_routes(self):
        """Clear all routes."""
        self._routes.clear()
        self._tag_routes.clear()
        self._fallback_robots.clear()
