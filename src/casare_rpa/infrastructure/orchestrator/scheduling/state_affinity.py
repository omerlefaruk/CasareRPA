"""
State Affinity Manager for CasareRPA Orchestrator.

Implements three affinity levels for workflows that maintain local state:
- Soft: Prefer robot with state, allow migration if unavailable
- Hard: Only execute on robot with state, queue if unavailable
- Session: Execute entire workflow chain on same robot

Supports state tracking per robot and migration for soft affinity.
"""

import asyncio
import threading
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from loguru import logger


class StateAffinityLevel(Enum):
    """Affinity levels for workflow state binding."""

    NONE = "none"  # No affinity - any robot can execute
    SOFT = "soft"  # Prefer robot with state, allow migration
    HARD = "hard"  # Only robot with state, queue if unavailable
    SESSION = "session"  # Entire workflow chain on same robot


class SessionAffinityError(Exception):
    """Raised when session affinity cannot be satisfied."""

    def __init__(self, message: str, workflow_id: str, required_robot_id: str | None = None):
        super().__init__(message)
        self.workflow_id = workflow_id
        self.required_robot_id = required_robot_id


@dataclass
class RobotState:
    """
    Tracks state held by a robot for a specific workflow.

    State types include:
    - Browser sessions (cookies, localStorage, authenticated sessions)
    - File system state (temp files, downloaded data, intermediate results)
    - In-memory caches (variable state from previous runs)
    - Desktop application state (open windows, logged-in apps)
    """

    robot_id: str
    workflow_id: str
    state_type: str  # "browser_session", "filesystem", "memory", "desktop_app"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(UTC))
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    is_migratable: bool = True  # Can state be transferred to another robot?

    @property
    def is_expired(self) -> bool:
        """Check if state has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get age of state in seconds."""
        return (datetime.now(UTC) - self.created_at).total_seconds()

    @property
    def idle_seconds(self) -> float:
        """Get time since last access in seconds."""
        return (datetime.now(UTC) - self.last_accessed).total_seconds()

    def touch(self) -> None:
        """Update last accessed timestamp."""
        self.last_accessed = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "robot_id": self.robot_id,
            "workflow_id": self.workflow_id,
            "state_type": self.state_type,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
            "size_bytes": self.size_bytes,
            "is_migratable": self.is_migratable,
        }


@dataclass
class WorkflowSession:
    """
    Tracks an active session for workflow chain execution.

    Used for session affinity where multiple related jobs must execute
    on the same robot to maintain state consistency.
    """

    session_id: str
    workflow_id: str
    robot_id: str
    chain_id: str | None  # ID linking related workflow executions
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_job_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    job_count: int = 0
    timeout_seconds: float = 3600.0  # Session expires after 1 hour of inactivity

    @property
    def is_expired(self) -> bool:
        """Check if session has timed out."""
        idle_time = (datetime.now(UTC) - self.last_job_at).total_seconds()
        return idle_time > self.timeout_seconds

    def record_job(self) -> None:
        """Record that a job was executed in this session."""
        self.last_job_at = datetime.now(UTC)
        self.job_count += 1


@dataclass
class StateAffinityDecision:
    """Result of affinity-based robot selection."""

    selected_robot_id: str | None
    affinity_level: StateAffinityLevel
    decision_reason: str
    has_state: bool
    state_robots: list[str]  # Robots that have relevant state
    fallback_used: bool
    should_queue: bool  # True if job should be queued instead of assigned
    queue_delay_seconds: float = 0.0
    migration_required: bool = False
    migration_source_robot: str | None = None


class StateAffinityManager:
    """
    Manages state affinity for workflow scheduling.

    Tracks which robots hold state for which workflows and makes
    intelligent decisions about job assignment based on affinity level.
    """

    def __init__(
        self,
        default_state_ttl_seconds: float = 3600.0,
        session_timeout_seconds: float = 3600.0,
        hard_affinity_queue_delay: float = 30.0,
        max_queue_attempts: int = 10,
        cleanup_interval_seconds: float = 300.0,
    ):
        """
        Initialize state affinity manager.

        Args:
            default_state_ttl_seconds: Default time-to-live for robot state
            session_timeout_seconds: Timeout for session affinity
            hard_affinity_queue_delay: Delay before requeuing hard affinity jobs
            max_queue_attempts: Max requeue attempts for hard affinity
            cleanup_interval_seconds: Interval for cleaning expired state
        """
        self._default_state_ttl = default_state_ttl_seconds
        self._session_timeout = session_timeout_seconds
        self._hard_affinity_delay = hard_affinity_queue_delay
        self._max_queue_attempts = max_queue_attempts
        self._cleanup_interval = cleanup_interval_seconds

        # State storage: workflow_id -> robot_id -> [RobotState]
        self._state_registry: dict[str, dict[str, list[RobotState]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Session storage: workflow_id -> WorkflowSession
        self._active_sessions: dict[str, WorkflowSession] = {}

        # Queue attempt tracking: job_id -> attempt_count
        self._queue_attempts: dict[str, int] = {}

        # Migration callbacks
        self._migration_handlers: dict[str, Callable] = {}

        # Thread safety
        self._lock = threading.RLock()

        # Background cleanup
        self._running = False
        self._cleanup_task: asyncio.Task | None = None

        logger.info(
            f"StateAffinityManager initialized: state_ttl={default_state_ttl_seconds}s, "
            f"session_timeout={session_timeout_seconds}s"
        )

    async def start(self) -> None:
        """Start the background cleanup task."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("StateAffinityManager cleanup task started")

    async def stop(self) -> None:
        """Stop the background cleanup task."""
        self._running = False

        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("StateAffinityManager stopped")

    # ==================== STATE REGISTRATION ====================

    def register_state(
        self,
        robot_id: str,
        workflow_id: str,
        state_type: str,
        ttl_seconds: float | None = None,
        metadata: dict[str, Any] | None = None,
        size_bytes: int = 0,
        is_migratable: bool = True,
    ) -> RobotState:
        """
        Register that a robot holds state for a workflow.

        Args:
            robot_id: Robot holding the state
            workflow_id: Workflow the state belongs to
            state_type: Type of state (browser_session, filesystem, etc.)
            ttl_seconds: Time-to-live for this state
            metadata: Additional state metadata
            size_bytes: Size of state data
            is_migratable: Whether state can be migrated

        Returns:
            Created RobotState instance
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._default_state_ttl
        expires_at = datetime.now(UTC) + timedelta(seconds=ttl) if ttl > 0 else None

        state = RobotState(
            robot_id=robot_id,
            workflow_id=workflow_id,
            state_type=state_type,
            expires_at=expires_at,
            metadata=metadata or {},
            size_bytes=size_bytes,
            is_migratable=is_migratable,
        )

        with self._lock:
            self._state_registry[workflow_id][robot_id].append(state)

        logger.debug(
            f"Registered {state_type} state for workflow {workflow_id[:8]} on robot {robot_id[:8]}"
        )
        return state

    def unregister_state(
        self,
        robot_id: str,
        workflow_id: str,
        state_type: str | None = None,
    ) -> int:
        """
        Unregister state for a robot/workflow combination.

        Args:
            robot_id: Robot ID
            workflow_id: Workflow ID
            state_type: Specific state type to remove, or None for all

        Returns:
            Number of state entries removed
        """
        with self._lock:
            if workflow_id not in self._state_registry:
                return 0

            if robot_id not in self._state_registry[workflow_id]:
                return 0

            states = self._state_registry[workflow_id][robot_id]

            if state_type:
                original_count = len(states)
                self._state_registry[workflow_id][robot_id] = [
                    s for s in states if s.state_type != state_type
                ]
                removed = original_count - len(self._state_registry[workflow_id][robot_id])
            else:
                removed = len(states)
                del self._state_registry[workflow_id][robot_id]

            # Clean up empty entries
            if not self._state_registry[workflow_id]:
                del self._state_registry[workflow_id]

        if removed > 0:
            logger.debug(
                f"Unregistered {removed} state entries for workflow {workflow_id[:8]} "
                f"on robot {robot_id[:8]}"
            )
        return removed

    def touch_state(self, robot_id: str, workflow_id: str) -> None:
        """Update last accessed time for all state on robot/workflow."""
        with self._lock:
            if workflow_id in self._state_registry:
                if robot_id in self._state_registry[workflow_id]:
                    for state in self._state_registry[workflow_id][robot_id]:
                        state.touch()

    def has_state_for(self, robot_id: str, workflow_id: str) -> bool:
        """Check if robot has any valid (non-expired) state for workflow."""
        with self._lock:
            if workflow_id not in self._state_registry:
                return False

            if robot_id not in self._state_registry[workflow_id]:
                return False

            return any(not s.is_expired for s in self._state_registry[workflow_id][robot_id])

    def get_robots_with_state(self, workflow_id: str) -> list[str]:
        """Get all robots that have valid state for a workflow."""
        with self._lock:
            if workflow_id not in self._state_registry:
                return []

            return [
                robot_id
                for robot_id, states in self._state_registry[workflow_id].items()
                if any(not s.is_expired for s in states)
            ]

    def get_state_for_robot(self, robot_id: str, workflow_id: str) -> list[RobotState]:
        """Get all state entries for a robot/workflow combination."""
        with self._lock:
            if workflow_id not in self._state_registry:
                return []

            return [
                s for s in self._state_registry[workflow_id].get(robot_id, []) if not s.is_expired
            ]

    def get_all_state_for_workflow(self, workflow_id: str) -> dict[str, list[RobotState]]:
        """Get all state for a workflow, grouped by robot."""
        with self._lock:
            if workflow_id not in self._state_registry:
                return {}

            return {
                robot_id: [s for s in states if not s.is_expired]
                for robot_id, states in self._state_registry[workflow_id].items()
                if any(not s.is_expired for s in states)
            }

    # ==================== SESSION MANAGEMENT ====================

    def create_session(
        self,
        session_id: str,
        workflow_id: str,
        robot_id: str,
        chain_id: str | None = None,
        timeout_seconds: float | None = None,
    ) -> WorkflowSession:
        """
        Create a new workflow session for session affinity.

        Args:
            session_id: Unique session identifier
            workflow_id: Workflow ID
            robot_id: Robot assigned to session
            chain_id: Optional chain ID for related workflows
            timeout_seconds: Session timeout override

        Returns:
            Created WorkflowSession
        """
        session = WorkflowSession(
            session_id=session_id,
            workflow_id=workflow_id,
            robot_id=robot_id,
            chain_id=chain_id,
            timeout_seconds=timeout_seconds or self._session_timeout,
        )

        with self._lock:
            self._active_sessions[workflow_id] = session

        logger.info(
            f"Created session {session_id[:8]} for workflow {workflow_id[:8]} "
            f"on robot {robot_id[:8]}"
        )
        return session

    def get_session(self, workflow_id: str) -> WorkflowSession | None:
        """Get active session for a workflow."""
        with self._lock:
            session = self._active_sessions.get(workflow_id)

            if session and session.is_expired:
                del self._active_sessions[workflow_id]
                logger.debug(f"Session for workflow {workflow_id[:8]} expired")
                return None

            return session

    def end_session(self, workflow_id: str) -> bool:
        """End a workflow session."""
        with self._lock:
            if workflow_id in self._active_sessions:
                session = self._active_sessions.pop(workflow_id)
                logger.info(
                    f"Ended session {session.session_id[:8]} for workflow {workflow_id[:8]} "
                    f"after {session.job_count} jobs"
                )
                return True
            return False

    def get_session_robot(self, workflow_id: str) -> str | None:
        """Get the robot assigned to a workflow's session."""
        session = self.get_session(workflow_id)
        return session.robot_id if session else None

    def record_session_job(self, workflow_id: str) -> None:
        """Record that a job was executed in a session."""
        with self._lock:
            session = self._active_sessions.get(workflow_id)
            if session:
                session.record_job()

    # ==================== AFFINITY-BASED SELECTION ====================

    def select_robot(
        self,
        workflow_id: str,
        affinity_level: StateAffinityLevel,
        available_robots: list[str],
        job_id: str | None = None,
        robot_scorer: Callable[[str], float] | None = None,
    ) -> StateAffinityDecision:
        """
        Select the best robot based on state affinity.

        Args:
            workflow_id: Workflow to execute
            affinity_level: Required affinity level
            available_robots: List of available robot IDs
            job_id: Job ID for queue tracking
            robot_scorer: Optional function to score robots (higher = better)

        Returns:
            StateAffinityDecision with selection result
        """
        if not available_robots:
            return StateAffinityDecision(
                selected_robot_id=None,
                affinity_level=affinity_level,
                decision_reason="No available robots",
                has_state=False,
                state_robots=[],
                fallback_used=False,
                should_queue=affinity_level == StateAffinityLevel.HARD,
                queue_delay_seconds=self._hard_affinity_delay,
            )

        robots_with_state = [r for r in available_robots if self.has_state_for(r, workflow_id)]

        if affinity_level == StateAffinityLevel.NONE:
            return self._select_no_affinity(available_robots, robots_with_state, robot_scorer)
        elif affinity_level == StateAffinityLevel.SOFT:
            return self._select_soft_affinity(
                workflow_id, available_robots, robots_with_state, robot_scorer
            )
        elif affinity_level == StateAffinityLevel.HARD:
            return self._select_hard_affinity(
                workflow_id, available_robots, robots_with_state, job_id, robot_scorer
            )
        elif affinity_level == StateAffinityLevel.SESSION:
            return self._select_session_affinity(
                workflow_id, available_robots, robots_with_state, robot_scorer
            )

        return StateAffinityDecision(
            selected_robot_id=available_robots[0] if available_robots else None,
            affinity_level=affinity_level,
            decision_reason="Unknown affinity level, using first available",
            has_state=False,
            state_robots=robots_with_state,
            fallback_used=True,
            should_queue=False,
        )

    def _select_no_affinity(
        self,
        available_robots: list[str],
        robots_with_state: list[str],
        robot_scorer: Callable[[str], float] | None,
    ) -> StateAffinityDecision:
        """Select robot with no affinity requirement."""
        selected = self._score_and_select(available_robots, robot_scorer)

        return StateAffinityDecision(
            selected_robot_id=selected,
            affinity_level=StateAffinityLevel.NONE,
            decision_reason="No affinity required, selected best available robot",
            has_state=selected in robots_with_state if selected else False,
            state_robots=robots_with_state,
            fallback_used=False,
            should_queue=False,
        )

    def _select_soft_affinity(
        self,
        workflow_id: str,
        available_robots: list[str],
        robots_with_state: list[str],
        robot_scorer: Callable[[str], float] | None,
    ) -> StateAffinityDecision:
        """
        Select robot with soft affinity.
        Prefer robot with state, allow migration if unavailable.
        """
        if robots_with_state:
            # Prefer robots with state
            selected = self._score_and_select(robots_with_state, robot_scorer)
            return StateAffinityDecision(
                selected_robot_id=selected,
                affinity_level=StateAffinityLevel.SOFT,
                decision_reason="Selected robot with existing state",
                has_state=True,
                state_robots=robots_with_state,
                fallback_used=False,
                should_queue=False,
            )

        # No robot has state - check if we can migrate
        # First, check if any offline robot has state we could migrate
        all_robots_with_state = self.get_robots_with_state(workflow_id)
        migration_source = None
        migration_possible = False

        for source_robot in all_robots_with_state:
            if source_robot not in available_robots:
                # Check if state is migratable
                states = self.get_state_for_robot(source_robot, workflow_id)
                if any(s.is_migratable for s in states):
                    migration_source = source_robot
                    migration_possible = True
                    break

        # Fallback to any available robot
        selected = self._score_and_select(available_robots, robot_scorer)

        return StateAffinityDecision(
            selected_robot_id=selected,
            affinity_level=StateAffinityLevel.SOFT,
            decision_reason="No robot with state available, falling back to best available"
            + (" (migration possible)" if migration_possible else ""),
            has_state=False,
            state_robots=robots_with_state,
            fallback_used=True,
            should_queue=False,
            migration_required=migration_possible,
            migration_source_robot=migration_source,
        )

    def _select_hard_affinity(
        self,
        workflow_id: str,
        available_robots: list[str],
        robots_with_state: list[str],
        job_id: str | None,
        robot_scorer: Callable[[str], float] | None,
    ) -> StateAffinityDecision:
        """
        Select robot with hard affinity.
        Only execute on robot with state, queue if unavailable.
        """
        if robots_with_state:
            selected = self._score_and_select(robots_with_state, robot_scorer)
            return StateAffinityDecision(
                selected_robot_id=selected,
                affinity_level=StateAffinityLevel.HARD,
                decision_reason="Selected robot with required state",
                has_state=True,
                state_robots=robots_with_state,
                fallback_used=False,
                should_queue=False,
            )

        # Check if any robot (available or not) has state
        all_robots_with_state = self.get_robots_with_state(workflow_id)

        if not all_robots_with_state:
            # No robot has state - this is essentially a new workflow
            # Allow execution on any robot
            selected = self._score_and_select(available_robots, robot_scorer)
            return StateAffinityDecision(
                selected_robot_id=selected,
                affinity_level=StateAffinityLevel.HARD,
                decision_reason="No state exists yet, allowing any robot for initial execution",
                has_state=False,
                state_robots=[],
                fallback_used=True,
                should_queue=False,
            )

        # Robots have state but none are available - check queue attempts
        attempts = 0
        if job_id:
            with self._lock:
                attempts = self._queue_attempts.get(job_id, 0)
                self._queue_attempts[job_id] = attempts + 1

        if attempts >= self._max_queue_attempts:
            # Max attempts reached - fail the job
            return StateAffinityDecision(
                selected_robot_id=None,
                affinity_level=StateAffinityLevel.HARD,
                decision_reason=f"Max queue attempts ({self._max_queue_attempts}) exceeded, "
                f"required robots {all_robots_with_state} unavailable",
                has_state=False,
                state_robots=all_robots_with_state,
                fallback_used=False,
                should_queue=False,  # No more queuing, fail the job
            )

        # Requeue and wait
        return StateAffinityDecision(
            selected_robot_id=None,
            affinity_level=StateAffinityLevel.HARD,
            decision_reason=f"Required robots {all_robots_with_state} unavailable, "
            f"requeuing (attempt {attempts + 1}/{self._max_queue_attempts})",
            has_state=False,
            state_robots=all_robots_with_state,
            fallback_used=False,
            should_queue=True,
            queue_delay_seconds=self._hard_affinity_delay,
        )

    def _select_session_affinity(
        self,
        workflow_id: str,
        available_robots: list[str],
        robots_with_state: list[str],
        robot_scorer: Callable[[str], float] | None,
    ) -> StateAffinityDecision:
        """
        Select robot with session affinity.
        Execute entire workflow chain on same robot.
        """
        session = self.get_session(workflow_id)

        if session:
            # Session exists - must use same robot
            if session.robot_id in available_robots:
                return StateAffinityDecision(
                    selected_robot_id=session.robot_id,
                    affinity_level=StateAffinityLevel.SESSION,
                    decision_reason=f"Using session robot (session {session.session_id[:8]}, "
                    f"{session.job_count} previous jobs)",
                    has_state=True,
                    state_robots=[session.robot_id],
                    fallback_used=False,
                    should_queue=False,
                )

            # Session robot not available - cannot proceed
            raise SessionAffinityError(
                f"Session robot {session.robot_id} is not available. "
                f"Session has {session.job_count} previous jobs.",
                workflow_id=workflow_id,
                required_robot_id=session.robot_id,
            )

        # No session exists - select a robot and create session
        if robots_with_state:
            selected = self._score_and_select(robots_with_state, robot_scorer)
        else:
            selected = self._score_and_select(available_robots, robot_scorer)

        return StateAffinityDecision(
            selected_robot_id=selected,
            affinity_level=StateAffinityLevel.SESSION,
            decision_reason="Starting new session"
            + (" with existing state" if robots_with_state else ""),
            has_state=bool(robots_with_state) and selected in robots_with_state,
            state_robots=robots_with_state,
            fallback_used=False,
            should_queue=False,
        )

    def _score_and_select(
        self,
        candidates: list[str],
        robot_scorer: Callable[[str], float] | None,
    ) -> str | None:
        """Score candidates and select the best one."""
        if not candidates:
            return None

        if robot_scorer:
            scored = [(robot_id, robot_scorer(robot_id)) for robot_id in candidates]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[0][0]

        return candidates[0]

    # ==================== MIGRATION SUPPORT ====================

    def register_migration_handler(
        self,
        state_type: str,
        handler: Callable[[str, str, RobotState], Any],
    ) -> None:
        """
        Register a handler for migrating state between robots.

        Args:
            state_type: Type of state this handler migrates
            handler: Async function (source_robot, target_robot, state) -> success
        """
        self._migration_handlers[state_type] = handler
        logger.debug(f"Registered migration handler for state type '{state_type}'")

    async def migrate_state(
        self,
        workflow_id: str,
        source_robot: str,
        target_robot: str,
        state_types: list[str] | None = None,
    ) -> tuple[int, int]:
        """
        Migrate state from one robot to another.

        Args:
            workflow_id: Workflow whose state to migrate
            source_robot: Robot to migrate from
            target_robot: Robot to migrate to
            state_types: Specific state types to migrate, or None for all

        Returns:
            Tuple of (successful_migrations, failed_migrations)
        """
        states = self.get_state_for_robot(source_robot, workflow_id)

        if state_types:
            states = [s for s in states if s.state_type in state_types]

        successful = 0
        failed = 0

        for state in states:
            if not state.is_migratable:
                logger.warning(
                    f"State {state.state_type} for workflow {workflow_id[:8]} " f"is not migratable"
                )
                failed += 1
                continue

            handler = self._migration_handlers.get(state.state_type)
            if not handler:
                logger.warning(f"No migration handler for state type '{state.state_type}'")
                failed += 1
                continue

            try:
                result = handler(source_robot, target_robot, state)
                if asyncio.iscoroutine(result):
                    await result

                # Register state on target robot
                self.register_state(
                    robot_id=target_robot,
                    workflow_id=workflow_id,
                    state_type=state.state_type,
                    metadata=state.metadata,
                    size_bytes=state.size_bytes,
                    is_migratable=state.is_migratable,
                )

                # Remove from source
                self.unregister_state(source_robot, workflow_id, state.state_type)

                successful += 1
                logger.info(
                    f"Migrated {state.state_type} state from {source_robot[:8]} "
                    f"to {target_robot[:8]}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to migrate {state.state_type} state: {e}. "
                    f"Source: {source_robot[:8]}, Target: {target_robot[:8]}"
                )
                failed += 1

        return successful, failed

    # ==================== CLEANUP ====================

    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired state and sessions."""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"State cleanup error: {e}")

    def _cleanup_expired(self) -> tuple[int, int]:
        """
        Clean up expired state and sessions.

        Returns:
            Tuple of (expired_states_removed, expired_sessions_removed)
        """
        states_removed = 0
        sessions_removed = 0

        with self._lock:
            # Clean expired states
            workflows_to_clean = list(self._state_registry.keys())
            for workflow_id in workflows_to_clean:
                robots_to_clean = list(self._state_registry[workflow_id].keys())
                for robot_id in robots_to_clean:
                    original = len(self._state_registry[workflow_id][robot_id])
                    self._state_registry[workflow_id][robot_id] = [
                        s for s in self._state_registry[workflow_id][robot_id] if not s.is_expired
                    ]
                    removed = original - len(self._state_registry[workflow_id][robot_id])
                    states_removed += removed

                    # Clean empty robot entries
                    if not self._state_registry[workflow_id][robot_id]:
                        del self._state_registry[workflow_id][robot_id]

                # Clean empty workflow entries
                if not self._state_registry[workflow_id]:
                    del self._state_registry[workflow_id]

            # Clean expired sessions
            expired_sessions = [
                wf_id for wf_id, session in self._active_sessions.items() if session.is_expired
            ]
            for workflow_id in expired_sessions:
                del self._active_sessions[workflow_id]
                sessions_removed += 1

            # Clean old queue attempts
            old_jobs = [
                job_id
                for job_id, attempts in self._queue_attempts.items()
                if attempts >= self._max_queue_attempts
            ]
            for job_id in old_jobs:
                del self._queue_attempts[job_id]

        if states_removed > 0 or sessions_removed > 0:
            logger.debug(
                f"Cleanup: removed {states_removed} expired states, "
                f"{sessions_removed} expired sessions"
            )

        return states_removed, sessions_removed

    def clear_queue_attempts(self, job_id: str) -> None:
        """Clear queue attempt counter for a job."""
        with self._lock:
            self._queue_attempts.pop(job_id, None)

    # ==================== STATISTICS ====================

    def get_statistics(self) -> dict[str, Any]:
        """Get state affinity statistics."""
        with self._lock:
            total_workflows = len(self._state_registry)
            total_states = sum(
                len(states)
                for workflow_states in self._state_registry.values()
                for states in workflow_states.values()
            )
            total_sessions = len(self._active_sessions)

            # State by type
            state_types: dict[str, int] = defaultdict(int)
            for workflow_states in self._state_registry.values():
                for states in workflow_states.values():
                    for state in states:
                        state_types[state.state_type] += 1

            return {
                "workflows_with_state": total_workflows,
                "total_state_entries": total_states,
                "active_sessions": total_sessions,
                "state_by_type": dict(state_types),
                "pending_queue_attempts": len(self._queue_attempts),
            }

    def get_workflow_state_summary(self, workflow_id: str) -> dict[str, Any]:
        """Get state summary for a specific workflow."""
        with self._lock:
            if workflow_id not in self._state_registry:
                return {
                    "workflow_id": workflow_id,
                    "has_state": False,
                    "robots_with_state": [],
                    "state_count": 0,
                    "session": None,
                }

            robots_with_state = list(self._state_registry[workflow_id].keys())
            state_count = sum(len(states) for states in self._state_registry[workflow_id].values())

            session = self._active_sessions.get(workflow_id)
            session_info = None
            if session and not session.is_expired:
                session_info = {
                    "session_id": session.session_id,
                    "robot_id": session.robot_id,
                    "job_count": session.job_count,
                    "started_at": session.started_at.isoformat(),
                }

            return {
                "workflow_id": workflow_id,
                "has_state": bool(robots_with_state),
                "robots_with_state": robots_with_state,
                "state_count": state_count,
                "session": session_info,
            }
