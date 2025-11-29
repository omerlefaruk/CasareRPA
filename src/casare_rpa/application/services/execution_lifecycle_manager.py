"""
Execution Lifecycle Manager for CasareRPA.

Centralized workflow execution lifecycle management with state machine,
resource cleanup, and browser process tracking.
"""

import asyncio
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Set
from loguru import logger


class ExecutionState(str, Enum):
    """Execution state machine states."""

    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    RESUMING = "resuming"
    STOPPING = "stopping"
    FORCE_STOPPING = "force_stopping"
    CLEANING_UP = "cleaning_up"
    ERROR = "error"


@dataclass
class ExecutionSession:
    """
    Tracks single workflow execution session.

    Holds references to task, context, and use_case to enable
    proper cleanup and cancellation.
    """

    session_id: str
    """Unique session identifier."""

    workflow_name: str
    """Name of the workflow being executed."""

    task: asyncio.Task
    """Async task running the workflow."""

    context: Optional[object] = None  # ExecutionContext
    """Execution context (set after use_case creates it)."""

    use_case: Optional[object] = None  # ExecuteWorkflowUseCase
    """Use case instance (set after creation)."""

    start_time: datetime = None
    """Execution start time."""

    pause_event: Optional[asyncio.Event] = None
    """Event for pause/resume coordination."""

    def __post_init__(self):
        """Initialize default values."""
        if self.start_time is None:
            self.start_time = datetime.now()


class ExecutionLifecycleManager:
    """
    Centralized workflow execution lifecycle management.

    Features:
    - State machine with atomic transitions
    - Force cleanup of previous execution before new F3
    - Browser PID tracking for orphan cleanup
    - Pause/resume support with asyncio.Event
    - Guaranteed cleanup on stop/cancel
    """

    def __init__(self):
        """Initialize lifecycle manager."""
        self._state: ExecutionState = ExecutionState.IDLE
        self._current_session: Optional[ExecutionSession] = None
        self._state_lock = asyncio.Lock()
        self._orphaned_browser_pids: Set[int] = set()

    async def start_workflow(self, workflow_runner, force_cleanup: bool = True) -> bool:
        """
        Start new workflow execution, cleaning up previous if needed.

        Args:
            workflow_runner: CanvasWorkflowRunner instance
            force_cleanup: Force cleanup of previous execution if still running

        Returns:
            True if started successfully, False otherwise
        """
        async with self._state_lock:
            if self._state != ExecutionState.IDLE:
                if force_cleanup:
                    logger.warning(
                        "Forcing cleanup of previous execution before starting new"
                    )
                    try:
                        await self._force_cleanup()
                    except Exception as e:
                        logger.error(f"Force cleanup failed: {e}")
                        # Reset to IDLE on cleanup failure
                        self._state = ExecutionState.IDLE
                        return False
                else:
                    logger.error("Cannot start: workflow already running")
                    return False

            self._state = ExecutionState.STARTING

            # Create new execution session
            session_id = str(uuid.uuid4())
            pause_event = asyncio.Event()
            pause_event.set()  # Initially not paused

            # Create task
            task = asyncio.create_task(
                self._run_workflow_with_session(
                    workflow_runner, session_id, pause_event
                )
            )

            # Context and use_case will be set by _run_workflow_with_session
            self._current_session = ExecutionSession(
                session_id=session_id,
                workflow_name="",  # Set later when use_case is available
                task=task,
                context=None,  # Set when use_case creates it
                use_case=None,  # Set when created
                start_time=datetime.now(),
                pause_event=pause_event,
            )

            # Transition to RUNNING before releasing lock
            # This ensures state consistency - any concurrent is_running() checks
            # will see RUNNING state before task actually starts executing
            self._state = ExecutionState.RUNNING
            logger.info(f"Started workflow execution session: {session_id}")
            return True

    async def _run_workflow_with_session(
        self, workflow_runner, session_id: str, pause_event: asyncio.Event
    ):
        """
        Execute workflow and track context/use_case in session.

        Args:
            workflow_runner: CanvasWorkflowRunner instance
            session_id: Unique session ID
            pause_event: Event for pause/resume coordination
        """
        try:
            # Run workflow - this creates ExecuteWorkflowUseCase internally
            await workflow_runner.run_workflow_with_pause_support(pause_event)

            # Update session with context reference (workflow_runner exposes it)
            if self._current_session:
                if hasattr(workflow_runner, "_current_use_case"):
                    self._current_session.use_case = workflow_runner._current_use_case

                    if self._current_session.use_case:
                        # Get context from use_case
                        if hasattr(self._current_session.use_case, "context"):
                            self._current_session.context = (
                                self._current_session.use_case.context
                            )

                        # Get workflow name
                        if hasattr(self._current_session.use_case, "workflow"):
                            workflow = self._current_session.use_case.workflow
                            if hasattr(workflow, "metadata"):
                                self._current_session.workflow_name = (
                                    workflow.metadata.name
                                )

            logger.info(f"Workflow execution {session_id} completed successfully")

        except asyncio.CancelledError:
            logger.info(f"Workflow execution {session_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Workflow execution {session_id} failed: {e}")
            self._state = ExecutionState.ERROR
            raise
        finally:
            # Always cleanup
            await self._cleanup_session()

    async def pause_workflow(self) -> bool:
        """
        Pause workflow execution.

        Returns:
            True if paused successfully, False otherwise
        """
        async with self._state_lock:
            if self._state != ExecutionState.RUNNING:
                logger.warning(f"Cannot pause: state is {self._state}")
                return False

            self._state = ExecutionState.PAUSING

            # Clear pause event - execution will wait at checkpoints
            if self._current_session and self._current_session.pause_event:
                self._current_session.pause_event.clear()
                logger.info("Workflow paused - waiting at checkpoint")

            self._state = ExecutionState.PAUSED
            return True

    async def resume_workflow(self) -> bool:
        """
        Resume paused workflow.

        Returns:
            True if resumed successfully, False otherwise
        """
        async with self._state_lock:
            if self._state != ExecutionState.PAUSED:
                logger.warning(f"Cannot resume: state is {self._state}")
                return False

            self._state = ExecutionState.RESUMING

            # Set pause event - execution continues
            if self._current_session and self._current_session.pause_event:
                self._current_session.pause_event.set()
                logger.info("Workflow resumed from pause")

            self._state = ExecutionState.RUNNING
            return True

    async def stop_workflow(self, force: bool = False) -> bool:
        """
        Stop workflow execution gracefully or forcefully.

        Args:
            force: Force stop immediately (cancel task)

        Returns:
            True if stopped successfully, False otherwise
        """
        async with self._state_lock:
            if self._state == ExecutionState.IDLE:
                return True

            self._state = (
                ExecutionState.FORCE_STOPPING if force else ExecutionState.STOPPING
            )
            logger.info(f"Stopping workflow (force={force})")

            if self._current_session:
                # Signal use_case to stop
                if self._current_session.use_case:
                    if hasattr(self._current_session.use_case, "stop"):
                        self._current_session.use_case.stop()

                # Resume if paused (so it can exit)
                if self._current_session.pause_event:
                    self._current_session.pause_event.set()

                # Cancel task if force
                if force and not self._current_session.task.done():
                    self._current_session.task.cancel()

                # Wait for cleanup with timeout
                try:
                    timeout = 5.0 if force else 30.0
                    await asyncio.wait_for(self._current_session.task, timeout=timeout)
                except asyncio.TimeoutError:
                    logger.error("Workflow stop timed out - forcing cleanup")
                    await self._force_cleanup()
                except asyncio.CancelledError:
                    pass  # Expected when force cancelling

            logger.info("Workflow stopped")
            return True

    async def _cleanup_session(self):
        """Cleanup current execution session."""
        self._state = ExecutionState.CLEANING_UP

        if self._current_session:
            # Cleanup ExecutionContext
            if self._current_session.context:
                try:
                    # Track browser PIDs before cleanup
                    await self._track_browser_pid(self._current_session.context)

                    # Cleanup context with timeout
                    if hasattr(self._current_session.context, "cleanup"):
                        await asyncio.wait_for(
                            self._current_session.context.cleanup(), timeout=30.0
                        )
                        logger.info("Context cleanup completed")
                except asyncio.TimeoutError:
                    logger.error("Context cleanup timed out after 30s")
                except Exception as e:
                    logger.error(f"Context cleanup error: {e}")

            self._current_session = None

        self._state = ExecutionState.IDLE

    async def _track_browser_pid(self, context):
        """
        Track browser process PID for orphan cleanup.

        NOTE: Uses Playwright internal API (_impl_obj._proc) which may change.
        Fallback to psutil parent PID search if this fails in future versions.

        Args:
            context: ExecutionContext instance
        """
        try:
            if hasattr(context, "_resources") and hasattr(
                context._resources, "browser"
            ):
                browser = context._resources.browser
                if browser:
                    # Try to get browser process PID via Playwright internals
                    # WARNING: Relies on undocumented API, may break in future versions
                    if hasattr(browser, "_impl_obj") and hasattr(
                        browser._impl_obj, "_proc"
                    ):
                        pid = browser._impl_obj._proc.pid
                        self._orphaned_browser_pids.add(pid)
                        logger.debug(
                            f"Tracking browser PID {pid} for cleanup (via Playwright internal API)"
                        )
                    else:
                        logger.warning(
                            "Playwright internal API changed - cannot track browser PID. "
                            "Orphaned browser processes may not be cleaned up automatically."
                        )
        except Exception as e:
            logger.warning(
                f"Could not track browser PID: {e}. Orphan cleanup may be incomplete."
            )

    async def _force_cleanup(self):
        """Force cleanup of orphaned resources."""
        if self._current_session:
            # Cancel task forcefully
            if self._current_session.task and not self._current_session.task.done():
                self._current_session.task.cancel()
                try:
                    await self._current_session.task
                except asyncio.CancelledError:
                    pass

            # Force context cleanup
            await self._cleanup_session()

        # Kill orphaned browser processes
        await self._kill_orphaned_browsers()

    async def _kill_orphaned_browsers(self):
        """Kill tracked browser PIDs that may be orphaned."""
        for pid in list(self._orphaned_browser_pids):
            try:
                import psutil

                if psutil.pid_exists(pid):
                    process = psutil.Process(pid)
                    # Check if it's a browser process
                    proc_name = process.name().lower()
                    if any(
                        name in proc_name
                        for name in ["chrome", "firefox", "webkit", "msedge"]
                    ):
                        logger.warning(f"Killing orphaned browser process {pid}")
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except psutil.TimeoutExpired:
                            logger.warning(
                                f"Browser process {pid} didn't terminate, killing forcefully"
                            )
                            process.kill()
                self._orphaned_browser_pids.remove(pid)
            except psutil.NoSuchProcess:
                # Process already gone
                self._orphaned_browser_pids.remove(pid)
            except Exception as e:
                logger.error(f"Failed to kill browser PID {pid}: {e}")

    def get_state(self) -> ExecutionState:
        """
        Get current execution state.

        Returns:
            Current ExecutionState
        """
        return self._state

    def is_running(self) -> bool:
        """
        Check if workflow is running.

        Returns:
            True if running or paused
        """
        return self._state in (ExecutionState.RUNNING, ExecutionState.PAUSED)

    def get_session_info(self) -> Optional[dict]:
        """
        Get current session information.

        Returns:
            Dict with session info, or None if no active session
        """
        if not self._current_session:
            return None

        return {
            "session_id": self._current_session.session_id,
            "workflow_name": self._current_session.workflow_name,
            "start_time": self._current_session.start_time.isoformat(),
            "state": self._state.value,
        }
