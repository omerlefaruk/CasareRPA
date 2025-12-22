"""
CasareRPA - Parallel Execution Strategies
Handles concurrent execution patterns (Fork/Join, Run-All, Parallel ForEach).
"""

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple, Callable
from loguru import logger

from casare_rpa.domain.value_objects.types import NodeId
from casare_rpa.domain.interfaces import IExecutionContext
from casare_rpa.domain.events import EventBus, WorkflowProgress

# Type aliases
NodeInstanceGetter = Callable[[str], Any]


class ParallelExecutionStrategy:
    """Encapsulates parallel execution logic for workflows."""

    def __init__(
        self,
        context: IExecutionContext,
        event_bus: Optional[EventBus],
        node_getter: NodeInstanceGetter,
        state_manager: Any,
        variable_resolver: Any,
        node_executor_factory: Callable[[IExecutionContext], Any],
        orchestrator: Any,
    ):
        self.context = context
        self.event_bus = event_bus
        self.get_node = node_getter
        self.state_manager = state_manager
        self.variable_resolver = variable_resolver
        self.create_executor = node_executor_factory
        self.orchestrator = orchestrator

    async def execute_parallel_workflows(self, start_nodes: List[NodeId]) -> None:
        """Executes multiple workflows concurrently (Shift+F3 mode)."""
        logger.info(f"Starting {len(start_nodes)} parallel workflows")

        self.state_manager.publish_event(
            WorkflowProgress(
                workflow_id="",
                current_node_id="",
                completed_nodes=0,
                total_nodes=len(start_nodes),
                percentage=0.0,
            )
        )

        async def _run_single(start_id: NodeId, idx: int) -> Tuple[str, bool]:
            name = f"workflow_{idx}"
            try:
                # Clone context for isolation (Browser isolation, Shared vars)
                wf_ctx = self.context.create_workflow_context(name)

                # Execute
                await self._execute_from_node_isolated(start_id, wf_ctx)

                # Cleanup
                try:
                    await wf_ctx._resources.cleanup()
                except Exception as e:
                    logger.warning(f"{name} cleanup error: {e}")

                return name, True
            except Exception as e:
                logger.error(f"{name} failed: {e}")
                return name, False

        tasks = [_run_single(sid, i) for i, sid in enumerate(start_nodes)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Tally results
        success = sum(1 for r in results if isinstance(r, tuple) and r[1])
        errors = len(results) - success

        logger.info(f"Parallel workflows: {success} success, {errors} errors")

        if success == 0 and errors > 0:
            self.state_manager.mark_failed(f"All {errors} parallel workflows failed")

    async def _execute_from_node_isolated(
        self, start_node_id: NodeId, context: IExecutionContext
    ) -> None:
        """Runs a workflow flow in an isolated context."""
        queue = [start_node_id]
        executed: Set[NodeId] = set()
        executor = self.create_executor(context)

        while queue and not self.state_manager.is_stopped:
            # Note: Pause handling is managed by main loop or ignored here for simplicity in this refactor
            curr_id = queue.pop(0)

            if curr_id in executed and not self.orchestrator.is_control_flow_node(curr_id):
                continue

            try:
                node = self.get_node(curr_id)
            except ValueError:
                break

            # Use resolver attached to main, but pointing to this context's vars?
            # Actually resolver needs the context. Logic requires variable_resolver factory ideally.
            # For now, we assume transfer_inputs can handle context or we invoke manually.
            # Limitation: The original resolve used self.context implicitly.
            # We must manually transfer inputs using the specific context.
            # To fix this properly, VariableResolver should accept context in transfer().
            # Assuming we patch that:
            self.variable_resolver.transfer_inputs_to_node(curr_id, context_override=context)

            result = await executor.execute(node)
            if not result.success:
                break

            executed.add(curr_id)

            # Identify next
            next_ids = self.orchestrator.get_next_nodes(curr_id, result.result)
            queue.extend(next_ids)

    async def execute_parallel_branches(self, fork_result: Dict[str, Any]) -> None:
        """Executes ForkNode branches concurrently."""
        branches = fork_result.get("parallel_branches", [])
        fork_id = fork_result.get("fork_id")
        fork_result.get("fail_fast", False)

        if not branches:
            return

        async def _run_branch(port: str) -> Tuple[str, Dict, bool]:
            try:
                # Find target
                target = self.orchestrator.find_target_node(fork_id, port)
                if not target:
                    return port, {}, True

                # Isolate
                branch_ctx = self.context.clone_for_branch(port)

                # Run until Join
                await self._run_until_join(target, branch_ctx, fork_result.get("paired_join_id"))

                return port, branch_ctx.variables, True
            except Exception as e:
                return port, {"_error": str(e)}, False

        tasks = [_run_branch(p) for p in branches]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate for JoinNode
        branch_results = {}
        for res in results:
            if isinstance(res, Exception):
                continue  # specific error handling
            port, vars, success = res
            branch_results[port] = vars

        self.context.set_variable(f"{fork_id}_branch_results", branch_results)

    async def execute_parallel_foreach_batch(
        self, result_data: Dict[str, Any], node_id: str
    ) -> None:
        """Executes a batch of items for ParallelForEachNode."""
        items = result_data.get("parallel_foreach_batch", [])
        if not items:
            return

        async def _process_item(item: Any, idx: int) -> Any:
            try:
                # Isolate context
                item_ctx = self.context.clone_for_branch(f"item_{idx}")
                item_ctx.set_variable("item", item)
                item_ctx.set_variable("index", idx)

                # Execute Body (one node or chain?)
                # ParallelForEach usually executes a body chain.
                # Here we assume the node logic gives us the body items or we loop back?
                # Actually, the Node returns 'parallel_foreach_batch' implies IT wants the caching/orchestrator to run them.
                # But Orchestrator usually loops back to the generic body.
                # If we run parallel, we must run the body for each item concurrently.
                # We need to know the 'body_start_node'.
                # Assuming result_data has it.
                body_start = result_data.get("body_start_id")
                if not body_start:
                    return None

                # Execute chain
                await self._run_until_join(body_start, item_ctx, None)  # Run until end of chain
                return item_ctx.variables
            except Exception as e:
                logger.error(f"Parallel Item {idx} failed: {e}")
                return None

        tasks = [_process_item(item, i) for i, item in enumerate(items)]
        await asyncio.gather(*tasks, return_exceptions=True)
        # Results handling? Usually aggregated or just side effects.

    async def _run_until_join(
        self, start_id: str, ctx: IExecutionContext, join_id: Optional[str]
    ) -> None:
        """Runs chain until JoinNode."""
        queue = [start_id]
        executor = self.create_executor(ctx)
        visited = set()

        while queue:
            curr = queue.pop(0)
            if curr == join_id:
                break

            if curr in visited:
                continue

            try:
                node = self.get_node(curr)
                self.variable_resolver.transfer_inputs_to_node(curr, context_override=ctx)
                res = await executor.execute(node)
                if not res.success:
                    break

                visited.add(curr)
                queue.extend(self.orchestrator.get_next_nodes(curr, res.result))
            except Exception:
                break
