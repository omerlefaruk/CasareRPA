"""
Canvas Workflow Runner.

Bridges serialized workflow from Canvas to Application layer execution.
"""

import asyncio
from typing import Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.serialization.workflow_serializer import (
        WorkflowSerializer,
    )
    from casare_rpa.presentation.events.event_bus import EventBus
    from casare_rpa.presentation.main_window import MainWindow
    from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase


class CanvasWorkflowRunner:
    """
    Runs workflows from the Canvas context.

    Coordinates:
    - WorkflowSerializer to get workflow data from graph
    - load_workflow_from_dict to create WorkflowSchema
    - ExecuteWorkflowUseCase for actual execution
    - EventBus for progress notifications (handled by use case)
    """

    def __init__(
        self,
        serializer: "WorkflowSerializer",
        event_bus: "EventBus",
        main_window: "MainWindow",
    ):
        """
        Initialize the workflow runner.

        Args:
            serializer: WorkflowSerializer instance
            event_bus: EventBus for publishing execution events
            main_window: MainWindow for accessing settings
        """
        self._serializer = serializer
        self._event_bus = event_bus
        self._main_window = main_window

        # Execution state
        self._is_running = False
        self._is_paused = False
        self._current_use_case: Optional["ExecuteWorkflowUseCase"] = None

        logger.debug("CanvasWorkflowRunner initialized")

    async def run_workflow(
        self, target_node_id: Optional[str] = None, single_node: bool = False
    ) -> bool:
        """
        Execute the workflow.

        Args:
            target_node_id: For Run-To-Node (F4), stop at this node
            single_node: For Run-Single-Node (F5), execute only this node

        Returns:
            True if completed successfully, False otherwise
        """
        if self._is_running:
            logger.warning("Workflow is already running")
            return False

        self._is_running = True

        try:
            # Step 1: Serialize the graph to workflow dict
            logger.info("Serializing workflow from canvas graph")
            workflow_data = self._serializer.serialize()

            # Check if workflow is empty
            if not workflow_data.get("nodes"):
                logger.warning("Workflow has no nodes - cannot execute")
                self._is_running = False
                return False

            # Step 2: Load workflow dict into WorkflowSchema
            logger.info("Loading workflow schema")
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(workflow_data)

            # Step 3: Create execution settings
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            settings = ExecutionSettings(
                target_node_id=target_node_id,
                continue_on_error=False,  # TODO: Get from main_window settings
                node_timeout=120.0,
            )

            # Step 4: Extract initial variables with fallback chain
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    # Try "default_value" first, then "value", then None
                    initial_vars[var_name] = var_data.get(
                        "default_value", var_data.get("value")
                    )
                else:
                    initial_vars[var_name] = var_data

            logger.info(f"Initialized {len(initial_vars)} variables")

            # Step 5: Create and execute use case
            logger.info("Creating execution use case")
            self._current_use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=None,  # TODO: Add project context support
                pause_event=None,  # No pause support in standard run
            )

            logger.info("Starting workflow execution")
            await self._current_use_case.execute()

            logger.success("Workflow execution completed successfully")
            return True

        except asyncio.CancelledError:
            logger.info("Workflow execution cancelled")
            raise  # Re-raise to propagate cancellation properly

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return False

        finally:
            self._is_running = False
            self._current_use_case = None

    async def run_workflow_with_pause_support(
        self, pause_event: asyncio.Event, target_node_id: Optional[str] = None
    ) -> bool:
        """
        Execute workflow with pause/resume support.

        This method is called by ExecutionLifecycleManager to run workflows
        with pause coordination.

        Args:
            pause_event: Event for pause/resume coordination
            target_node_id: For Run-To-Node (F4), stop at this node

        Returns:
            True if completed successfully, False otherwise
        """
        if self._is_running:
            logger.warning("Workflow is already running")
            return False

        self._is_running = True

        try:
            # Step 1: Serialize the graph to workflow dict
            logger.info("Serializing workflow from canvas graph")
            workflow_data = self._serializer.serialize()

            # Check if workflow is empty
            if not workflow_data.get("nodes"):
                logger.warning("Workflow has no nodes - cannot execute")
                self._is_running = False
                return False

            # Step 2: Load workflow dict into WorkflowSchema
            logger.info("Loading workflow schema")
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(workflow_data)

            # Step 3: Create execution settings
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            settings = ExecutionSettings(
                target_node_id=target_node_id,
                continue_on_error=False,
                node_timeout=120.0,
            )

            # Step 4: Extract initial variables
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    initial_vars[var_name] = var_data.get(
                        "default_value", var_data.get("value")
                    )
                else:
                    initial_vars[var_name] = var_data

            logger.info(f"Initialized {len(initial_vars)} variables")

            # Step 5: Create and execute use case with pause support
            logger.info("Creating execution use case with pause support")
            self._current_use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=None,
                pause_event=pause_event,  # Pass pause_event for pause/resume
            )

            logger.info("Starting workflow execution")
            await self._current_use_case.execute()

            logger.success("Workflow execution completed successfully")
            return True

        except asyncio.CancelledError:
            logger.info("Workflow execution cancelled")
            raise

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return False

        finally:
            self._is_running = False
            self._current_use_case = None

    def stop(self) -> None:
        """
        Stop workflow execution.

        Signals the ExecuteWorkflowUseCase to stop at the next opportunity
        (after the current node completes). The use case checks _stop_requested
        flag in its execution loop.
        """
        if not self._is_running:
            logger.debug("Stop called but workflow is not running")
            return

        if self._current_use_case is None:
            logger.warning("Stop called but no active use case - clearing state")
            self._is_running = False
            self._is_paused = False
            return

        logger.info("Stopping workflow execution - signaling use case to terminate")
        self._current_use_case.stop()
        self._is_running = False
        self._is_paused = False
        logger.info("Workflow stop signal sent successfully")

    def pause(self) -> None:
        """
        Pause workflow execution (legacy method).

        NOTE: This method is for legacy run_workflow() calls. Workflows started
        via run_workflow_with_pause_support() (called by ExecutionLifecycleManager)
        have full pause/resume support via asyncio.Event.

        This legacy method only sets UI state flag and has no effect on execution.
        """
        if not self._is_running:
            logger.debug("Pause called but workflow is not running")
            return

        if self._current_use_case is None:
            logger.warning("Pause called but no active use case")
            return

        if self._is_paused:
            logger.debug("Workflow is already paused")
            return

        logger.info("Pausing workflow execution (UI state only)")
        self._is_paused = True
        logger.warning(
            "Legacy pause method called - execution will not actually pause. "
            "Use ExecutionLifecycleManager.pause_workflow() for real pause/resume."
        )

    def resume(self) -> None:
        """
        Resume workflow execution (legacy method).

        NOTE: This method is for legacy run_workflow() calls. Workflows started
        via run_workflow_with_pause_support() (called by ExecutionLifecycleManager)
        have full pause/resume support via asyncio.Event.

        This legacy method only clears UI state flag and has no effect on execution.
        """
        if not self._is_running:
            logger.debug("Resume called but workflow is not running")
            return

        if self._current_use_case is None:
            logger.warning("Resume called but no active use case")
            return

        if not self._is_paused:
            logger.debug("Workflow is not paused")
            return

        logger.info("Resuming workflow execution (UI state only)")
        self._is_paused = False
        logger.debug("Legacy resume method - use ExecutionLifecycleManager for real functionality")

    @property
    def is_running(self) -> bool:
        """Check if workflow is currently running."""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """Check if workflow is currently paused."""
        return self._is_paused
