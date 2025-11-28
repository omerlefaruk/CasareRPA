"""
Canvas Workflow Runner.

Bridges serialized workflow from Canvas to Application layer execution.
"""

from typing import Optional
from loguru import logger


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

            # Step 4: Extract initial variables
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    initial_vars[var_name] = var_data.get("default_value")
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
            )

            logger.info("Starting workflow execution")
            await self._current_use_case.execute()

            logger.success("Workflow execution completed successfully")
            return True

        except Exception as e:
            logger.exception(f"Workflow execution failed: {e}")
            return False

        finally:
            self._is_running = False
            self._current_use_case = None

    def stop(self) -> None:
        """Stop execution."""
        if self._current_use_case:
            logger.info("Stopping workflow execution")
            # TODO: Implement stop functionality in ExecuteWorkflowUseCase
            self._is_running = False

    def pause(self) -> None:
        """Pause execution."""
        if self._current_use_case and self._is_running:
            logger.info("Pausing workflow execution")
            self._is_paused = True
            # TODO: Implement pause functionality in ExecuteWorkflowUseCase

    def resume(self) -> None:
        """Resume execution."""
        if self._current_use_case and self._is_paused:
            logger.info("Resuming workflow execution")
            self._is_paused = False
            # TODO: Implement resume functionality in ExecuteWorkflowUseCase

    @property
    def is_running(self) -> bool:
        """Check if workflow is currently running."""
        return self._is_running

    @property
    def is_paused(self) -> bool:
        """Check if workflow is currently paused."""
        return self._is_paused
