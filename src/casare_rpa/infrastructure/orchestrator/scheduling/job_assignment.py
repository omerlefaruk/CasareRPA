"""
Intelligent Job Assignment Engine for CasareRPA Orchestrator.

Implements constraint-based robot selection with soft scoring for optimal job assignment.
Supports capability matching, load balancing, tag affinity, and state preferences.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple
from collections import defaultdict
import threading

from loguru import logger


class NoCapableRobotError(Exception):
    """Raised when no robot can execute the requested job."""

    def __init__(
        self, job_name: str, required_capabilities: Optional[List[str]] = None
    ):
        self.job_name = job_name
        self.required_capabilities = required_capabilities or []
        caps_str = (
            ", ".join(self.required_capabilities)
            if self.required_capabilities
            else "none"
        )
        super().__init__(
            f"No robot can execute job '{job_name}'. "
            f"Required capabilities: [{caps_str}]"
        )


class CapabilityType(Enum):
    """Types of capabilities a robot can have."""

    BROWSER = "browser"
    DESKTOP = "desktop"
    OFFICE = "office"
    DATABASE = "database"
    OCR = "ocr"
    AI_ML = "ai_ml"
    HIGH_MEMORY = "high_memory"
    HIGH_CPU = "high_cpu"
    GPU = "gpu"
    SECURE_ENCLAVE = "secure_enclave"
    CUSTOM = "custom"


@dataclass
class RobotCapability:
    """
    Represents a capability that a robot possesses.

    Attributes:
        capability_type: Type of capability
        name: Human-readable name
        version: Optional version string
        metadata: Additional capability metadata
    """

    capability_type: CapabilityType
    name: str
    version: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches(self, required: "RobotCapability") -> bool:
        """
        Check if this capability satisfies a requirement.

        Args:
            required: Required capability to match against

        Returns:
            True if this capability satisfies the requirement
        """
        if self.capability_type != required.capability_type:
            return False

        if self.name.lower() != required.name.lower():
            return False

        if required.version and self.version:
            return self._version_satisfies(self.version, required.version)

        return True

    def _version_satisfies(self, have: str, need: str) -> bool:
        """
        Check if version satisfies requirement.
        Supports simple semver comparison (>=, >, ==, etc.).
        """
        try:
            have_parts = [int(p) for p in have.split(".")]
            need_clean = need.lstrip(">=<")
            need_parts = [int(p) for p in need_clean.split(".")]

            if need.startswith(">="):
                return have_parts >= need_parts
            elif need.startswith(">"):
                return have_parts > need_parts
            elif need.startswith("<="):
                return have_parts <= need_parts
            elif need.startswith("<"):
                return have_parts < need_parts
            else:
                return have_parts >= need_parts
        except (ValueError, AttributeError):
            return have == need


@dataclass
class JobRequirements:
    """
    Specifies requirements for a job to be assigned to a robot.

    Attributes:
        workflow_id: ID of the workflow to execute
        workflow_name: Human-readable workflow name
        required_capabilities: Capabilities the robot must have
        required_tags: Tags the robot must possess
        preferred_tags: Tags that are preferred but not required
        requires_state: Whether job needs local state from previous execution
        min_memory_gb: Minimum RAM required
        min_cpu_cores: Minimum CPU cores required
        environment: Target environment (production, staging, etc.)
        timeout_seconds: Job timeout in seconds
        priority: Job priority (0-3, higher = more important)
    """

    workflow_id: str
    workflow_name: str
    required_capabilities: List[RobotCapability] = field(default_factory=list)
    required_tags: List[str] = field(default_factory=list)
    preferred_tags: List[str] = field(default_factory=list)
    requires_state: bool = False
    min_memory_gb: float = 0.0
    min_cpu_cores: int = 0
    environment: str = "default"
    timeout_seconds: int = 3600
    priority: int = 1


class RobotPresenceProtocol(Protocol):
    """Protocol for accessing robot presence/metrics data."""

    @property
    def robot_id(self) -> str:
        """Robot identifier."""
        ...

    @property
    def name(self) -> str:
        """Robot name."""
        ...

    @property
    def status(self) -> str:
        """Current status (online, busy, offline, etc.)."""
        ...

    @property
    def cpu_percent(self) -> float:
        """Current CPU utilization percentage."""
        ...

    @property
    def memory_percent(self) -> float:
        """Current memory utilization percentage."""
        ...

    @property
    def current_jobs(self) -> int:
        """Number of jobs currently running."""
        ...

    @property
    def max_concurrent_jobs(self) -> int:
        """Maximum concurrent jobs allowed."""
        ...

    @property
    def tags(self) -> List[str]:
        """Robot tags."""
        ...

    @property
    def environment(self) -> str:
        """Robot environment."""
        ...

    @property
    def capabilities(self) -> Dict[str, Any]:
        """Robot capabilities dictionary."""
        ...


@dataclass
class RobotInfo:
    """
    Robot information for assignment decisions.
    Implements RobotPresenceProtocol.
    """

    robot_id: str
    name: str
    status: str = "online"
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    disk_percent: float = 0.0
    current_jobs: int = 0
    max_concurrent_jobs: int = 1
    tags: List[str] = field(default_factory=list)
    environment: str = "default"
    capabilities: Dict[str, Any] = field(default_factory=dict)
    network_zone: str = "default"
    last_heartbeat: Optional[datetime] = None

    @property
    def is_available(self) -> bool:
        """Check if robot can accept new jobs."""
        return self.status == "online" and self.current_jobs < self.max_concurrent_jobs

    @property
    def utilization(self) -> float:
        """Get overall utilization percentage."""
        if self.max_concurrent_jobs == 0:
            return 100.0
        job_util = (self.current_jobs / self.max_concurrent_jobs) * 100
        return max(job_util, self.cpu_percent, self.memory_percent)

    def has_capability(self, capability: RobotCapability) -> bool:
        """Check if robot has a specific capability."""
        robot_caps = self._parse_capabilities()
        for robot_cap in robot_caps:
            if robot_cap.matches(capability):
                return True
        return False

    def _parse_capabilities(self) -> List[RobotCapability]:
        """Parse capabilities dict into RobotCapability objects."""
        result = []
        for key, value in self.capabilities.items():
            try:
                cap_type = CapabilityType(key.lower())
            except ValueError:
                cap_type = CapabilityType.CUSTOM

            if isinstance(value, dict):
                result.append(
                    RobotCapability(
                        capability_type=cap_type,
                        name=value.get("name", key),
                        version=value.get("version"),
                        metadata=value,
                    )
                )
            elif isinstance(value, bool) and value:
                result.append(
                    RobotCapability(
                        capability_type=cap_type,
                        name=key,
                    )
                )
            elif isinstance(value, str):
                result.append(
                    RobotCapability(
                        capability_type=cap_type,
                        name=key,
                        version=value,
                    )
                )

        return result


@dataclass
class ScoringWeights:
    """
    Configurable weights for robot scoring algorithm.

    All weights are positive values. Higher weight = more influence on final score.
    """

    cpu_load_weight: float = 1.0
    memory_load_weight: float = 0.8
    tag_match_weight: float = 1.5
    state_affinity_weight: float = 2.0
    network_proximity_weight: float = 0.5
    job_count_weight: float = 1.2

    # Thresholds for load penalties
    cpu_high_threshold: float = 80.0
    cpu_medium_threshold: float = 60.0
    memory_high_threshold: float = 85.0
    memory_medium_threshold: float = 70.0

    # Bonus/penalty values
    high_load_penalty: float = 50.0
    medium_load_penalty: float = 25.0
    tag_match_bonus: float = 20.0
    state_affinity_bonus: float = 100.0
    same_zone_bonus: float = 15.0


@dataclass
class AssignmentResult:
    """
    Result of a job assignment decision.

    Attributes:
        robot_id: ID of assigned robot
        robot_name: Name of assigned robot
        score: Final score of the selected robot
        scores_breakdown: Detailed score breakdown for debugging
        alternatives: Other considered robots with their scores
        assignment_time_ms: Time taken to make assignment decision
    """

    robot_id: str
    robot_name: str
    score: float
    scores_breakdown: Dict[str, float] = field(default_factory=dict)
    alternatives: List[Tuple[str, float]] = field(default_factory=list)
    assignment_time_ms: float = 0.0


class StateAffinityTracker:
    """
    Tracks which robots have state for which workflows.
    Used to prefer robots that can reuse existing state.
    """

    def __init__(self, state_ttl_seconds: int = 3600):
        """
        Initialize state affinity tracker.

        Args:
            state_ttl_seconds: How long state records are considered valid
        """
        self._state_ttl = timedelta(seconds=state_ttl_seconds)
        self._state_records: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self._lock = threading.Lock()

    def record_state(self, workflow_id: str, robot_id: str) -> None:
        """
        Record that a robot has state for a workflow.

        Args:
            workflow_id: Workflow identifier
            robot_id: Robot that executed the workflow
        """
        with self._lock:
            self._state_records[workflow_id][robot_id] = datetime.now(timezone.utc)

    def has_state(self, workflow_id: str, robot_id: str) -> bool:
        """
        Check if a robot has valid state for a workflow.

        Args:
            workflow_id: Workflow identifier
            robot_id: Robot to check

        Returns:
            True if robot has valid (non-expired) state
        """
        with self._lock:
            workflow_states = self._state_records.get(workflow_id, {})
            if robot_id not in workflow_states:
                return False

            state_time = workflow_states[robot_id]
            return datetime.now(timezone.utc) - state_time < self._state_ttl

    def get_robots_with_state(self, workflow_id: str) -> List[str]:
        """
        Get all robots that have valid state for a workflow.

        Args:
            workflow_id: Workflow identifier

        Returns:
            List of robot IDs with valid state
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            workflow_states = self._state_records.get(workflow_id, {})
            return [
                robot_id
                for robot_id, state_time in workflow_states.items()
                if now - state_time < self._state_ttl
            ]

    def clear_state(self, workflow_id: str, robot_id: Optional[str] = None) -> None:
        """
        Clear state records.

        Args:
            workflow_id: Workflow identifier
            robot_id: Optional specific robot, or all robots if None
        """
        with self._lock:
            if robot_id:
                self._state_records.get(workflow_id, {}).pop(robot_id, None)
            else:
                self._state_records.pop(workflow_id, None)

    def cleanup_expired(self) -> int:
        """
        Remove expired state records.

        Returns:
            Number of records removed
        """
        removed = 0
        now = datetime.now(timezone.utc)

        with self._lock:
            for workflow_id in list(self._state_records.keys()):
                robot_states = self._state_records[workflow_id]
                expired = [
                    rid
                    for rid, ts in robot_states.items()
                    if now - ts >= self._state_ttl
                ]
                for rid in expired:
                    del robot_states[rid]
                    removed += 1

                if not robot_states:
                    del self._state_records[workflow_id]

        return removed


class JobAssignmentEngine:
    """
    Intelligent job assignment engine with constraint matching and soft scoring.

    Features:
    - Hard constraint filtering (capabilities, environment)
    - Soft scoring with configurable weights
    - State affinity for workflow sessions
    - Load-based distribution
    - Tag matching preferences
    """

    def __init__(
        self,
        weights: Optional[ScoringWeights] = None,
        state_ttl_seconds: int = 3600,
        network_zone: str = "default",
    ):
        """
        Initialize the assignment engine.

        Args:
            weights: Scoring weights configuration
            state_ttl_seconds: TTL for state affinity records
            network_zone: Default network zone for proximity scoring
        """
        self._weights = weights or ScoringWeights()
        self._state_tracker = StateAffinityTracker(state_ttl_seconds)
        self._network_zone = network_zone
        self._lock = threading.Lock()

        logger.info(
            f"JobAssignmentEngine initialized with weights: "
            f"cpu={self._weights.cpu_load_weight}, "
            f"memory={self._weights.memory_load_weight}, "
            f"tags={self._weights.tag_match_weight}, "
            f"affinity={self._weights.state_affinity_weight}"
        )

    @property
    def weights(self) -> ScoringWeights:
        """Get current scoring weights."""
        return self._weights

    @weights.setter
    def weights(self, value: ScoringWeights) -> None:
        """Set scoring weights."""
        self._weights = value

    def assign_job(
        self,
        requirements: JobRequirements,
        available_robots: List[RobotInfo],
        orchestrator_zone: Optional[str] = None,
    ) -> AssignmentResult:
        """
        Assign a job to the best-fit robot.

        Algorithm:
        1. Filter robots by hard constraints (capabilities, environment)
        2. Score remaining robots by soft preferences
        3. Select highest-scoring robot

        Args:
            requirements: Job requirements specification
            available_robots: List of available robots
            orchestrator_zone: Network zone of orchestrator for proximity scoring

        Returns:
            AssignmentResult with selected robot and scoring details

        Raises:
            NoCapableRobotError: If no robot can execute the job
        """
        start_time = datetime.now(timezone.utc)
        zone = orchestrator_zone or self._network_zone

        capable_robots = self._filter_by_hard_constraints(
            requirements, available_robots
        )

        if not capable_robots:
            cap_names = [c.name for c in requirements.required_capabilities]
            logger.warning(
                f"No capable robot found for job '{requirements.workflow_name}'. "
                f"Required capabilities: {cap_names}, "
                f"Environment: {requirements.environment}, "
                f"Available robots: {len(available_robots)}"
            )
            raise NoCapableRobotError(requirements.workflow_name, cap_names)

        scored_robots = self._score_robots(requirements, capable_robots, zone)

        scored_robots.sort(key=lambda x: x[1], reverse=True)

        best_robot, best_score, breakdown = scored_robots[0]

        alternatives = [(r.robot_id, score) for r, score, _ in scored_robots[1:5]]

        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        logger.info(
            f"Assigned job '{requirements.workflow_name}' to robot '{best_robot.name}' "
            f"(score: {best_score:.1f}, alternatives: {len(scored_robots) - 1})"
        )

        return AssignmentResult(
            robot_id=best_robot.robot_id,
            robot_name=best_robot.name,
            score=best_score,
            scores_breakdown=breakdown,
            alternatives=alternatives,
            assignment_time_ms=elapsed,
        )

    def _filter_by_hard_constraints(
        self,
        requirements: JobRequirements,
        robots: List[RobotInfo],
    ) -> List[RobotInfo]:
        """
        Filter robots by hard constraints.

        Hard constraints (all must be satisfied):
        - Robot must be available (online, not at capacity)
        - Robot must have all required capabilities
        - Robot must be in matching environment
        - Robot must meet minimum resource requirements

        Args:
            requirements: Job requirements
            robots: Available robots

        Returns:
            List of robots that satisfy all hard constraints
        """
        capable = []

        for robot in robots:
            if not robot.is_available:
                logger.debug(
                    f"Robot '{robot.name}' filtered: not available "
                    f"(status={robot.status}, jobs={robot.current_jobs}/{robot.max_concurrent_jobs})"
                )
                continue

            if not self._matches_capabilities(requirements, robot):
                logger.debug(
                    f"Robot '{robot.name}' filtered: missing required capabilities"
                )
                continue

            if (
                requirements.environment != "default"
                and robot.environment != requirements.environment
            ):
                if robot.environment != "default":
                    logger.debug(
                        f"Robot '{robot.name}' filtered: environment mismatch "
                        f"(required={requirements.environment}, has={robot.environment})"
                    )
                    continue

            if not self._meets_resource_requirements(requirements, robot):
                logger.debug(f"Robot '{robot.name}' filtered: insufficient resources")
                continue

            capable.append(robot)

        return capable

    def _matches_capabilities(
        self,
        requirements: JobRequirements,
        robot: RobotInfo,
    ) -> bool:
        """
        Check if robot has all required capabilities.

        Args:
            requirements: Job requirements
            robot: Robot to check

        Returns:
            True if robot has all required capabilities
        """
        for required_cap in requirements.required_capabilities:
            if not robot.has_capability(required_cap):
                return False
        return True

    def _meets_resource_requirements(
        self,
        requirements: JobRequirements,
        robot: RobotInfo,
    ) -> bool:
        """
        Check if robot meets minimum resource requirements.

        Args:
            requirements: Job requirements
            robot: Robot to check

        Returns:
            True if robot meets resource requirements
        """
        robot_memory_gb = robot.capabilities.get("memory_total_gb", 0)
        if (
            requirements.min_memory_gb > 0
            and robot_memory_gb < requirements.min_memory_gb
        ):
            return False

        robot_cpu_cores = robot.capabilities.get("cpu_count", 0)
        if (
            requirements.min_cpu_cores > 0
            and robot_cpu_cores < requirements.min_cpu_cores
        ):
            return False

        return True

    def _score_robots(
        self,
        requirements: JobRequirements,
        robots: List[RobotInfo],
        orchestrator_zone: str,
    ) -> List[Tuple[RobotInfo, float, Dict[str, float]]]:
        """
        Score robots by soft preferences.

        Scoring factors:
        - Current load (CPU, memory) - penalty for high load
        - Tag matching - bonus for each matching tag
        - State affinity - large bonus if robot has state
        - Network proximity - bonus for same zone

        Args:
            requirements: Job requirements
            robots: Capable robots
            orchestrator_zone: Network zone for proximity

        Returns:
            List of (robot, total_score, breakdown) tuples
        """
        scored = []

        for robot in robots:
            breakdown: Dict[str, float] = {}
            score = 100.0

            cpu_penalty = self._calculate_cpu_penalty(robot.cpu_percent)
            breakdown["cpu_load"] = -cpu_penalty
            score -= cpu_penalty * self._weights.cpu_load_weight

            memory_penalty = self._calculate_memory_penalty(robot.memory_percent)
            breakdown["memory_load"] = -memory_penalty
            score -= memory_penalty * self._weights.memory_load_weight

            job_penalty = self._calculate_job_count_penalty(robot)
            breakdown["job_count"] = -job_penalty
            score -= job_penalty * self._weights.job_count_weight

            tag_bonus = self._calculate_tag_bonus(requirements, robot)
            breakdown["tag_match"] = tag_bonus
            score += tag_bonus * self._weights.tag_match_weight

            if requirements.requires_state:
                affinity_bonus = self._calculate_state_affinity_bonus(
                    requirements, robot
                )
                breakdown["state_affinity"] = affinity_bonus
                score += affinity_bonus * self._weights.state_affinity_weight

            proximity_bonus = self._calculate_proximity_bonus(robot, orchestrator_zone)
            breakdown["network_proximity"] = proximity_bonus
            score += proximity_bonus * self._weights.network_proximity_weight

            breakdown["total"] = score
            scored.append((robot, score, breakdown))

        return scored

    def _calculate_cpu_penalty(self, cpu_percent: float) -> float:
        """
        Calculate penalty based on CPU load.

        Args:
            cpu_percent: Current CPU utilization

        Returns:
            Penalty value (0-50)
        """
        if cpu_percent > self._weights.cpu_high_threshold:
            return self._weights.high_load_penalty
        elif cpu_percent > self._weights.cpu_medium_threshold:
            return self._weights.medium_load_penalty
        return 0.0

    def _calculate_memory_penalty(self, memory_percent: float) -> float:
        """
        Calculate penalty based on memory load.

        Args:
            memory_percent: Current memory utilization

        Returns:
            Penalty value (0-50)
        """
        if memory_percent > self._weights.memory_high_threshold:
            return self._weights.high_load_penalty
        elif memory_percent > self._weights.memory_medium_threshold:
            return self._weights.medium_load_penalty
        return 0.0

    def _calculate_job_count_penalty(self, robot: RobotInfo) -> float:
        """
        Calculate penalty based on current job count.

        Args:
            robot: Robot info

        Returns:
            Penalty value based on utilization
        """
        if robot.max_concurrent_jobs == 0:
            return self._weights.high_load_penalty

        utilization = robot.current_jobs / robot.max_concurrent_jobs
        if utilization > 0.8:
            return self._weights.high_load_penalty
        elif utilization > 0.5:
            return self._weights.medium_load_penalty
        return utilization * 10

    def _calculate_tag_bonus(
        self,
        requirements: JobRequirements,
        robot: RobotInfo,
    ) -> float:
        """
        Calculate bonus for tag matching.

        Args:
            requirements: Job requirements
            robot: Robot info

        Returns:
            Total tag bonus
        """
        robot_tags = set(robot.tags) if robot.tags else set()
        bonus = 0.0

        required_matches = set(requirements.required_tags) & robot_tags
        bonus += len(required_matches) * self._weights.tag_match_bonus

        preferred_matches = set(requirements.preferred_tags) & robot_tags
        bonus += len(preferred_matches) * (self._weights.tag_match_bonus * 0.5)

        return bonus

    def _calculate_state_affinity_bonus(
        self,
        requirements: JobRequirements,
        robot: RobotInfo,
    ) -> float:
        """
        Calculate bonus for state affinity.

        Args:
            requirements: Job requirements
            robot: Robot info

        Returns:
            Affinity bonus if robot has state, 0 otherwise
        """
        if self._state_tracker.has_state(requirements.workflow_id, robot.robot_id):
            return self._weights.state_affinity_bonus
        return 0.0

    def _calculate_proximity_bonus(
        self,
        robot: RobotInfo,
        orchestrator_zone: str,
    ) -> float:
        """
        Calculate bonus for network proximity.

        Args:
            robot: Robot info
            orchestrator_zone: Orchestrator's network zone

        Returns:
            Proximity bonus if same zone
        """
        if robot.network_zone == orchestrator_zone:
            return self._weights.same_zone_bonus
        return 0.0

    def record_job_completion(
        self,
        workflow_id: str,
        robot_id: str,
        success: bool,
    ) -> None:
        """
        Record job completion for state affinity tracking.

        Args:
            workflow_id: Executed workflow ID
            robot_id: Robot that executed the workflow
            success: Whether execution was successful
        """
        if success:
            self._state_tracker.record_state(workflow_id, robot_id)
            logger.debug(
                f"Recorded state affinity: workflow={workflow_id}, robot={robot_id}"
            )

    def clear_state_affinity(
        self,
        workflow_id: str,
        robot_id: Optional[str] = None,
    ) -> None:
        """
        Clear state affinity records.

        Args:
            workflow_id: Workflow ID
            robot_id: Optional specific robot, or all if None
        """
        self._state_tracker.clear_state(workflow_id, robot_id)

    def cleanup_expired_state(self) -> int:
        """
        Clean up expired state affinity records.

        Returns:
            Number of records removed
        """
        return self._state_tracker.cleanup_expired()

    def get_assignment_stats(self) -> Dict[str, Any]:
        """
        Get assignment engine statistics.

        Returns:
            Dictionary with engine statistics
        """
        return {
            "weights": {
                "cpu_load": self._weights.cpu_load_weight,
                "memory_load": self._weights.memory_load_weight,
                "tag_match": self._weights.tag_match_weight,
                "state_affinity": self._weights.state_affinity_weight,
                "network_proximity": self._weights.network_proximity_weight,
                "job_count": self._weights.job_count_weight,
            },
            "thresholds": {
                "cpu_high": self._weights.cpu_high_threshold,
                "cpu_medium": self._weights.cpu_medium_threshold,
                "memory_high": self._weights.memory_high_threshold,
                "memory_medium": self._weights.memory_medium_threshold,
            },
            "network_zone": self._network_zone,
        }


async def assign_job_to_robot(
    job_requirements: JobRequirements,
    available_robots: List[RobotInfo],
    engine: Optional[JobAssignmentEngine] = None,
    weights: Optional[ScoringWeights] = None,
) -> AssignmentResult:
    """
    Convenience function to assign a job to the best-fit robot.

    This is the main entry point for job assignment as specified in the roadmap.

    Algorithm:
    1. Filter robots by hard constraints (capabilities)
    2. Score remaining robots by soft preferences
    3. Select highest-scoring robot

    Args:
        job_requirements: Job requirements specification
        available_robots: List of available robots
        engine: Optional pre-configured engine (creates one if not provided)
        weights: Optional scoring weights (uses defaults if not provided)

    Returns:
        AssignmentResult with selected robot ID and scoring details

    Raises:
        NoCapableRobotError: If no robot can execute the job

    Example:
        >>> requirements = JobRequirements(
        ...     workflow_id="wf-123",
        ...     workflow_name="Invoice Processing",
        ...     required_capabilities=[
        ...         RobotCapability(CapabilityType.BROWSER, "playwright"),
        ...         RobotCapability(CapabilityType.OCR, "tesseract"),
        ...     ],
        ...     required_tags=["finance"],
        ...     requires_state=True,
        ... )
        >>> robots = [robot1, robot2, robot3]
        >>> result = await assign_job_to_robot(requirements, robots)
        >>> print(f"Assigned to: {result.robot_name} (score: {result.score})")
    """
    if engine is None:
        engine = JobAssignmentEngine(weights=weights)

    return engine.assign_job(job_requirements, available_robots)
