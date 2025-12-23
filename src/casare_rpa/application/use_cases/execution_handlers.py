"""
CasareRPA - Execution Handlers
Encapsulates routing logic, error recovery, and special result handling.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from casare_rpa.domain.value_objects.types import NodeId


class ExecutionResultHandler:
    """Handles routing decisions based on node execution results."""

    def __init__(
        self,
        orchestrator: Any,
        state_manager: Any,
        error_handler: Any,
        settings: Any,
        parallel_strategy: Any,
    ):
        self.orchestrator = orchestrator
        self.state_manager = state_manager
        self.error_handler = error_handler
        self.settings = settings
        self.parallel_strategy = parallel_strategy

    def handle_execution_failure(
        self,
        node_id: NodeId,
        result: dict[str, Any] | None,
        nodes_to_execute: list[NodeId],
    ) -> bool:
        """
        Routes execution on failure (Try-Catch or Stop).
        Returns True if execution should continue (error captured), False to stop.
        """
        # 1. Try-Catch Capture
        error_captured = self.error_handler.capture_from_result(result, node_id)
        if error_captured:
            catch_id = self.error_handler.find_catch_node_id()
            if catch_id:
                logger.info(f"Routing to catch: {catch_id}")
                nodes_to_execute.insert(0, catch_id)
                return True

        # 2. Continue on Error Setting
        if self.settings.continue_on_error:
            logger.warning(f"Node {node_id} failed (continue_on_error=True)")
            return True

        # 3. Stop Execution
        error_msg = result.get("error", "Unknown error") if result else "Unknown error"
        self.state_manager.mark_failed(error_msg)
        return False

    def handle_special_results(
        self,
        current_node_id: NodeId,
        exec_result: Any,
        nodes_to_execute: list[NodeId],
    ) -> bool:
        """
        Handles LoopBack, CatchRouting, and Parallel Forks.
        Returns True if special handling applied (intercepted routing).
        """
        result = exec_result.result
        if not result:
            return False

        # A. Loop Back
        if "loop_back_to" in result:
            loop_start = result["loop_back_to"]
            self._handle_loop_back(loop_start, current_node_id, nodes_to_execute)
            return True

        # B. Route to Catch (Explicit)
        if "route_to_catch" in result:
            catch_id = result["route_to_catch"]
            if catch_id:
                nodes_to_execute.insert(0, catch_id)
                return True

        # C. Error Captured (Implicit)
        if result.get("error_captured") or exec_result.error_captured:
            catch_id = self.error_handler.find_catch_node_id()
            if catch_id:
                nodes_to_execute.insert(0, catch_id)
                return True

        # D. Fork (Parallel)
        if "parallel_branches" in result:
            # Async Task - Fire & Forget (managed by main loop await? no, usually background)
            # In original code: asyncio.create_task(...)
            # Here we need access to the event loop or just delegate back.
            # Strategy: Delegate to Parallel Strategy, but await?
            # Original code fired a task. We should probably keep that pattern
            # OR make this method async. Making it async is cleaner.
            # For now, we flag it.
            return False  # Handled by caller to keep this sync or make async?

        return False

    def _handle_loop_back(self, loop_start_id: str, current_node_id: str, queue: list[str]) -> None:
        """Clears executed nodes in loop body and the start node itself to allow re-execution."""
        body_nodes = self.orchestrator.find_loop_body_nodes(loop_start_id, current_node_id)
        # MUST clear the loop start node as well, otherwise execute_workflow skips it on next pop
        self.state_manager.executed_nodes.discard(loop_start_id)

        for nid in body_nodes:
            self.state_manager.executed_nodes.discard(nid)

        queue.insert(0, loop_start_id)
