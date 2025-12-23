"""
Canvas Workflow Runner.

Bridges serialized workflow from Canvas to Application layer execution.
Supports both one-time execution and trigger-based listening.
"""

import asyncio
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
    from casare_rpa.domain.services.project_context import ProjectContext
    from casare_rpa.presentation.canvas.main_window import MainWindow
    from casare_rpa.presentation.canvas.serialization.workflow_serializer import (
        WorkflowSerializer,
    )
    from casare_rpa.presentation.events.event_bus import EventBus
    from casare_rpa.triggers.base import BaseTrigger, TriggerEvent


class CanvasWorkflowRunner:
    """
    Runs workflows from the Canvas context.

    Coordinates:
    - WorkflowSerializer to get workflow data from graph
    - load_workflow_from_dict to create WorkflowSchema
    - ExecuteWorkflowUseCase for actual execution
    - EventBus for progress notifications (handled by use case)
    - Trigger activation for trigger-based workflows
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
        self._current_use_case: ExecuteWorkflowUseCase | None = None

        # Trigger listening state
        self._is_listening = False
        self._active_trigger: BaseTrigger | None = None
        self._trigger_run_count = 0
        self._trigger_node_id: str | None = None
        self._cached_workflow_data: dict | None = None

        logger.debug("CanvasWorkflowRunner initialized")

    def _get_continue_on_error(self, workflow_data: dict[str, Any]) -> bool:
        """
        Get continue_on_error setting from workflow data or project context.

        Priority (highest to lowest):
        1. Workflow-level execution_settings
        2. Project settings (stop_on_error inverted)
        3. Default: False

        Args:
            workflow_data: Serialized workflow data

        Returns:
            True if execution should continue after node errors
        """
        # Check workflow-level settings first
        exec_settings = workflow_data.get("execution_settings", {})
        if "continue_on_error" in exec_settings:
            return bool(exec_settings["continue_on_error"])

        # Check stop_on_error (inverted logic) in execution_settings
        if "stop_on_error" in exec_settings:
            return not bool(exec_settings["stop_on_error"])

        # Check project context if available
        project_context = self._get_project_context()
        if project_context is not None:
            try:
                # ProjectContext.get_stop_on_error() returns True if should stop
                return not project_context.get_stop_on_error()
            except Exception as e:
                logger.debug(f"Could not get stop_on_error from project: {e}")

        # Default: stop on error (continue_on_error = False)
        return False

    def _get_node_timeout(self, workflow_data: dict[str, Any]) -> float:
        """
        Get node timeout setting from workflow data or project context.

        Args:
            workflow_data: Serialized workflow data

        Returns:
            Node timeout in seconds
        """
        # Check workflow-level settings
        exec_settings = workflow_data.get("execution_settings", {})
        if "node_timeout" in exec_settings:
            timeout = exec_settings["node_timeout"]
            if isinstance(timeout, (int, float)) and timeout > 0:
                return float(timeout)

        # Check project context
        project_context = self._get_project_context()
        if project_context is not None:
            try:
                timeout = project_context.get_timeout()
                if timeout > 0:
                    return float(timeout)
            except Exception as e:
                logger.debug(f"Could not get timeout from project: {e}")

        # Default timeout
        return 120.0

    def _get_project_context(self) -> Optional["ProjectContext"]:
        """
        Get project context from main window's project controller.

        Returns:
            ProjectContext if a project is open, None otherwise
        """
        try:
            project_controller = self._main_window.get_project_controller()
            if project_controller is None:
                return None

            current_project = project_controller.current_project
            if current_project is None:
                return None

            # Create ProjectContext from current project
            from casare_rpa.domain.services.project_context import ProjectContext

            return ProjectContext(project=current_project)

        except Exception as e:
            logger.debug(f"Could not get project context: {e}")
            return None

    async def run_workflow(
        self, target_node_id: str | None = None, single_node: bool = False
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

            continue_on_error = self._get_continue_on_error(workflow_data)
            node_timeout = self._get_node_timeout(workflow_data)

            settings = ExecutionSettings(
                target_node_id=target_node_id,
                continue_on_error=continue_on_error,
                node_timeout=node_timeout,
            )

            logger.debug(
                f"Execution settings: continue_on_error={continue_on_error}, "
                f"node_timeout={node_timeout}s"
            )

            # Step 4: Extract initial variables with fallback chain
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    # Try "default_value" first, then "value", then None
                    initial_vars[var_name] = var_data.get("default_value", var_data.get("value"))
                else:
                    initial_vars[var_name] = var_data

            logger.info(f"Initialized {len(initial_vars)} variables")

            # Step 5: Get project context for scoped variables and credentials
            project_context = self._get_project_context()
            if project_context:
                logger.debug(f"Using project context: {project_context}")

            # Step 6: Create and execute use case
            logger.info("Creating execution use case")
            self._current_use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=project_context,
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
        self,
        pause_event: asyncio.Event,
        target_node_id: str | None = None,
        single_node: bool = False,
    ) -> bool:
        """
        Execute workflow with pause/resume support.

        This method is called by ExecutionLifecycleManager to run workflows
        with pause coordination.

        Args:
            pause_event: Event for pause/resume coordination
            target_node_id: For Run-To-Node (F4), stop at this node.
                            For Run-Single-Node (F5), run only this node.
            single_node: If True, execute only the target_node_id node (F5 mode)

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

            continue_on_error = self._get_continue_on_error(workflow_data)
            node_timeout = self._get_node_timeout(workflow_data)

            settings = ExecutionSettings(
                target_node_id=target_node_id,
                single_node=single_node,
                continue_on_error=continue_on_error,
                node_timeout=node_timeout,
            )

            logger.debug(
                f"Execution settings: continue_on_error={continue_on_error}, "
                f"node_timeout={node_timeout}s"
            )

            # Step 4: Extract initial variables
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    initial_vars[var_name] = var_data.get("default_value", var_data.get("value"))
                else:
                    initial_vars[var_name] = var_data

            logger.info(f"Initialized {len(initial_vars)} variables")

            # Step 5: Get project context for scoped variables and credentials
            project_context = self._get_project_context()
            if project_context:
                logger.debug(f"Using project context: {project_context}")

            # Step 6: Create and execute use case with pause support
            logger.info("Creating execution use case with pause support")
            self._current_use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=project_context,
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

    async def run_all_workflows(self, pause_event: asyncio.Event) -> bool:
        """
        Execute all workflows on canvas concurrently (Shift+F3).

        NOTE: Shortcut is Shift+F3 (not Shift+F5 which is Stop).

        When the canvas contains multiple independent workflows (each with its
        own StartNode), this method executes them all in parallel. Each workflow
        gets SHARED variables but SEPARATE browser instances.

        Args:
            pause_event: Event for pause/resume coordination

        Returns:
            True if at least one workflow completed successfully, False if all failed
        """
        if self._is_running:
            logger.warning("Workflow is already running")
            return False

        self._is_running = True

        try:
            # Step 1: Serialize the graph to workflow dict
            logger.info("Serializing workflow for Run All mode")
            workflow_data = self._serializer.serialize()

            if not workflow_data.get("nodes"):
                logger.warning("Workflow has no nodes - cannot execute")
                self._is_running = False
                return False

            # Step 2: Load workflow dict into WorkflowSchema
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(workflow_data)

            # Step 3: Create execution settings
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )

            continue_on_error = self._get_continue_on_error(workflow_data)
            node_timeout = self._get_node_timeout(workflow_data)

            settings = ExecutionSettings(
                target_node_id=None,
                single_node=False,
                continue_on_error=continue_on_error,
                node_timeout=node_timeout,
            )

            logger.debug(
                f"Execution settings: continue_on_error={continue_on_error}, "
                f"node_timeout={node_timeout}s"
            )

            # Step 4: Extract initial variables
            variables = workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    initial_vars[var_name] = var_data.get("default_value", var_data.get("value"))
                else:
                    initial_vars[var_name] = var_data

            # Step 5: Get project context for scoped variables and credentials
            project_context = self._get_project_context()
            if project_context:
                logger.debug(f"Using project context: {project_context}")

            # Step 6: Create and execute use case with run_all=True
            logger.info("Creating execution use case for Run All mode")
            self._current_use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=project_context,
                pause_event=pause_event,
            )

            logger.info("Starting Run All workflow execution")
            result = await self._current_use_case.execute(run_all=True)

            if result:
                logger.success("Run All workflows completed successfully")
            else:
                logger.warning("Run All workflows completed with errors")

            return result

        except asyncio.CancelledError:
            logger.info("Run All workflow execution cancelled")
            raise

        except Exception as e:
            logger.exception(f"Run All workflow execution failed: {e}")
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

    @property
    def is_listening(self) -> bool:
        """Check if trigger is actively listening."""
        return self._is_listening

    @property
    def trigger_run_count(self) -> int:
        """Get number of times trigger has fired."""
        return self._trigger_run_count

    def _find_trigger_node(self, workflow_data: dict) -> tuple | None:
        """
        Find trigger node in workflow data.

        Returns:
            Tuple of (node_id, node_type, node_config) or None if no trigger found
        """
        nodes = workflow_data.get("nodes", {})
        for node_id, node_data in nodes.items():
            # Check node_type field (WorkflowSerializer format)
            # e.g., "ScheduleTriggerNode"
            node_type = node_data.get("node_type", "")
            if "Trigger" in node_type and node_type.endswith("Node"):
                # Get config directly from node_data
                config = node_data.get("config", {})
                # Filter internal keys
                config = {k: v for k, v in config.items() if not k.startswith("_")}

                logger.debug(f"Found trigger node: {node_type} with config: {config}")
                return (node_id, node_type, config)
        return None

    async def start_listening(self) -> bool:
        """
        Start trigger listening mode.

        For workflows with a trigger node as entry point, this creates
        and activates the trigger to listen for events. When the trigger
        fires, the workflow is executed with the trigger payload.

        Returns:
            True if listening started successfully, False otherwise
        """
        if self._is_listening:
            logger.warning("Already listening for trigger events")
            return False

        try:
            # Serialize workflow
            logger.info("Starting trigger listening mode")
            workflow_data = self._serializer.serialize()

            if not workflow_data.get("nodes"):
                logger.warning("Workflow has no nodes")
                return False

            # Find trigger node
            trigger_info = self._find_trigger_node(workflow_data)
            if not trigger_info:
                logger.warning("No trigger node found in workflow")
                return False

            trigger_node_id, trigger_node_type, trigger_config = trigger_info
            logger.info(f"Found trigger node: {trigger_node_type} ({trigger_node_id})")

            # Create trigger instance based on trigger type
            trigger = await self._create_trigger(trigger_node_type, trigger_config, trigger_node_id)
            if not trigger:
                logger.error("Failed to create trigger instance")
                return False

            # Start trigger
            success = await trigger.start()
            if not success:
                logger.error("Failed to start trigger")
                return False

            # Store state
            self._active_trigger = trigger
            self._is_listening = True
            self._trigger_run_count = 0
            self._trigger_node_id = trigger_node_id
            self._cached_workflow_data = workflow_data

            logger.success(f"Trigger listening started: {trigger_node_type}")
            return True

        except Exception as e:
            logger.exception(f"Failed to start listening: {e}")
            return False

    async def stop_listening(self) -> bool:
        """
        Stop trigger listening mode.

        Returns:
            True if stopped successfully, False otherwise
        """
        if not self._is_listening:
            logger.debug("Not currently listening")
            return True

        try:
            if self._active_trigger:
                await self._active_trigger.stop()
                self._active_trigger = None

            self._is_listening = False
            self._trigger_node_id = None
            self._cached_workflow_data = None

            logger.info("Trigger listening stopped")
            return True

        except Exception as e:
            logger.exception(f"Failed to stop listening: {e}")
            return False

    async def _create_trigger(
        self, trigger_node_type: str, trigger_config: dict, trigger_node_id: str
    ) -> Optional["BaseTrigger"]:
        """
        Create a trigger instance from node configuration.

        Args:
            trigger_node_type: Type of trigger node (e.g., "ScheduleTriggerNode")
            trigger_config: Trigger configuration from node
            trigger_node_id: ID of the trigger node

        Returns:
            BaseTrigger instance or None on failure
        """
        from casare_rpa.triggers.base import BaseTriggerConfig, TriggerType
        from casare_rpa.triggers.registry import TriggerRegistry

        # Map node types to trigger types
        node_type_to_trigger_type = {
            "ScheduleTriggerNode": TriggerType.SCHEDULED,
            "WebhookTriggerNode": TriggerType.WEBHOOK,
            "FileWatchTriggerNode": TriggerType.FILE_WATCH,
            "EmailTriggerNode": TriggerType.EMAIL,
            "AppEventTriggerNode": TriggerType.APP_EVENT,
            "ErrorTriggerNode": TriggerType.ERROR,
            "WorkflowCallTriggerNode": TriggerType.WORKFLOW_CALL,
            "FormTriggerNode": TriggerType.FORM,
            "ChatTriggerNode": TriggerType.CHAT,
            "RSSFeedTriggerNode": TriggerType.RSS_FEED,
            "SSETriggerNode": TriggerType.SSE,
        }

        trigger_type = node_type_to_trigger_type.get(trigger_node_type)
        if not trigger_type:
            logger.error(f"Unknown trigger node type: {trigger_node_type}")
            return None

        # Create trigger config
        config = BaseTriggerConfig(
            id=f"canvas_{trigger_node_id}",
            name=f"Canvas {trigger_node_type}",
            trigger_type=trigger_type,
            scenario_id="canvas",
            workflow_id="canvas_workflow",
            enabled=True,
            config=trigger_config,
        )

        # Get trigger class from registry (TriggerRegistry is a singleton)
        trigger_class = TriggerRegistry().get(trigger_type)
        if not trigger_class:
            logger.error(f"No trigger implementation for type: {trigger_type}")
            return None

        # Create trigger with callback
        trigger = trigger_class(config, event_callback=self._on_trigger_fire)
        return trigger

    async def _on_trigger_fire(self, event: "TriggerEvent") -> None:
        """
        Callback when trigger fires.

        Executes the workflow with trigger payload as initial variables.

        Args:
            event: TriggerEvent containing payload and metadata
        """
        if not self._is_listening or not self._cached_workflow_data:
            logger.warning("Trigger fired but not in listening mode")
            return

        # Extract payload and metadata from event
        payload = event.payload
        metadata = event.metadata

        self._trigger_run_count += 1
        logger.info(f"Trigger fired (run #{self._trigger_run_count}): {metadata}")

        try:
            # Load workflow from cached data
            from casare_rpa.application.use_cases.execute_workflow import (
                ExecuteWorkflowUseCase,
                ExecutionSettings,
            )
            from casare_rpa.utils.workflow.workflow_loader import (
                load_workflow_from_dict,
            )

            workflow = load_workflow_from_dict(self._cached_workflow_data)

            # Merge trigger payload with existing variables
            variables = self._cached_workflow_data.get("variables", {})
            initial_vars = {}
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    initial_vars[var_name] = var_data.get("default_value", var_data.get("value"))
                else:
                    initial_vars[var_name] = var_data

            # Add trigger payload to variables
            initial_vars.update(payload)
            initial_vars["_trigger_metadata"] = metadata
            initial_vars["_trigger_run_number"] = self._trigger_run_count
            initial_vars["_trigger_timestamp"] = datetime.now(UTC).isoformat()

            # Get execution settings from cached workflow data
            continue_on_error = self._get_continue_on_error(self._cached_workflow_data)
            node_timeout = self._get_node_timeout(self._cached_workflow_data)

            settings = ExecutionSettings(
                target_node_id=None,
                continue_on_error=continue_on_error,
                node_timeout=node_timeout,
            )

            # Get project context for scoped variables and credentials
            project_context = self._get_project_context()

            use_case = ExecuteWorkflowUseCase(
                workflow=workflow,
                event_bus=self._event_bus,
                settings=settings,
                initial_variables=initial_vars,
                project_context=project_context,
                pause_event=None,
            )

            logger.info(f"Executing workflow from trigger (run #{self._trigger_run_count})")
            await use_case.execute()
            logger.success(f"Trigger execution #{self._trigger_run_count} completed")

        except Exception as e:
            logger.exception(f"Trigger execution failed: {e}")
