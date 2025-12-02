"""
CasareRPA - Parallel Execution Nodes

Provides nodes for concurrent/parallel execution:
- ForkNode: Split execution into multiple parallel branches
- JoinNode: Synchronize and merge parallel branches
- ParallelForEachNode: Process list items concurrently in batches
"""

from typing import Optional
from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.domain.value_objects.types import (
    PortType,
    DataType,
    NodeStatus,
    ExecutionResult,
)


@node_schema(
    PropertyDef(
        "branch_count",
        PropertyType.INTEGER,
        default=2,
        min_value=2,
        max_value=10,
        label="Branch Count",
        tooltip="Number of parallel branches (2-10)",
    ),
    PropertyDef(
        "fail_fast",
        PropertyType.BOOLEAN,
        default=False,
        label="Fail Fast",
        tooltip="If True, stop all branches when one fails. If False, continue other branches.",
    ),
)
@executable_node
class ForkNode(BaseNode):
    """
    Fork node that splits execution into multiple parallel branches.

    Each branch executes concurrently using asyncio.gather. Use with JoinNode
    to synchronize branches back together.

    Example Layout:
        ForkNode ──┬── branch_1 ──→ Task A ──┬──→ JoinNode
                   ├── branch_2 ──→ Task B ──┤
                   └── branch_3 ──→ Task C ──┘

    Outputs:
        - branch_1, branch_2, ..., branch_N: Parallel execution branches
        - Each branch executes concurrently

    Properties:
        - branch_count: Number of parallel branches (2-10)
        - fail_fast: If True, cancel remaining branches on first failure
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Fork node."""
        super().__init__(node_id, config)
        self.name = "Fork"
        self.node_type = "ForkNode"
        # Paired JoinNode ID - set automatically when created together
        self.paired_join_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)

        # Create branch output ports based on config
        branch_count = self.get_parameter("branch_count", 2)
        for i in range(1, branch_count + 1):
            self.add_output_port(f"branch_{i}", PortType.EXEC_OUTPUT)

    def set_paired_join(self, join_node_id: str) -> None:
        """Set the paired JoinNode ID."""
        self.paired_join_id = join_node_id
        self.config["paired_join_id"] = join_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute fork - signals parallel branch execution.

        Returns special 'parallel_branches' key that the executor uses
        to spawn concurrent tasks for each branch.
        """
        self.status = NodeStatus.RUNNING

        try:
            branch_count = self.get_parameter("branch_count", 2)
            fail_fast = self.get_parameter("fail_fast", False)

            # Build list of branch port names
            branches = [f"branch_{i}" for i in range(1, branch_count + 1)]

            logger.info(f"Fork starting {branch_count} parallel branches")

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "branch_count": branch_count,
                    "branches": branches,
                },
                # Special key for executor to handle parallel execution
                "parallel_branches": branches,
                "fork_id": self.node_id,
                "paired_join_id": self.paired_join_id,
                "fail_fast": fail_fast,
                "next_nodes": [],  # Executor handles branching
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Fork execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "merge_strategy",
        PropertyType.CHOICE,
        default="all",
        choices=["all", "first", "last"],
        label="Merge Strategy",
        tooltip="How to merge branch results: all (combine), first (first to complete), last (last to complete)",
    ),
)
@executable_node
class JoinNode(BaseNode):
    """
    Join node that synchronizes parallel branches from a ForkNode.

    Waits for all branches from the paired ForkNode to complete,
    then merges their results and continues execution.

    Inputs:
        - exec_in: Multiple connections from parallel branches

    Outputs:
        - exec_out: Single output after all branches complete
        - results: Dict containing results from each branch
        - branch_count: Number of branches that completed

    Properties:
        - merge_strategy: How to combine branch results
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize Join node."""
        super().__init__(node_id, config)
        self.name = "Join"
        self.node_type = "JoinNode"
        # Paired ForkNode ID - set automatically when created together
        self.paired_fork_id: str = ""

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_output_port("exec_out", PortType.EXEC_OUTPUT)
        self.add_output_port("results", PortType.OUTPUT, DataType.DICT)
        self.add_output_port("branch_count", PortType.OUTPUT, DataType.INTEGER)

    def set_paired_fork(self, fork_node_id: str) -> None:
        """Set the paired ForkNode ID."""
        self.paired_fork_id = fork_node_id
        self.config["paired_fork_id"] = fork_node_id

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute join - merge branch results and continue.

        The executor populates branch results before calling this.
        """
        self.status = NodeStatus.RUNNING

        try:
            fork_id = self.paired_fork_id or self.get_parameter("paired_fork_id", "")
            merge_strategy = self.get_parameter("merge_strategy", "all")

            # Get branch results stored by executor
            results_key = f"{fork_id}_branch_results"
            branch_results = context.get_variable(results_key, {})

            # Clean up branch results from context
            if context.has_variable(results_key):
                context.delete_variable(results_key)

            # Merge results based on strategy
            if merge_strategy == "all":
                merged = branch_results
            elif merge_strategy == "first" and branch_results:
                first_key = next(iter(branch_results))
                merged = {first_key: branch_results[first_key]}
            elif merge_strategy == "last" and branch_results:
                last_key = list(branch_results.keys())[-1]
                merged = {last_key: branch_results[last_key]}
            else:
                merged = branch_results

            # Set output values
            self.set_output_value("results", merged)
            self.set_output_value("branch_count", len(branch_results))

            # Merge branch variables back to main context
            for branch_name, branch_vars in branch_results.items():
                if isinstance(branch_vars, dict):
                    context.merge_branch_results(branch_name, branch_vars)

            logger.info(
                f"Join completed: {len(branch_results)} branches merged ({merge_strategy})"
            )

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "branch_count": len(branch_results),
                    "merge_strategy": merge_strategy,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"Join execution failed: {e}")
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "batch_size",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        max_value=50,
        label="Batch Size",
        tooltip="Number of items to process concurrently (1-50)",
    ),
    PropertyDef(
        "fail_fast",
        PropertyType.BOOLEAN,
        default=False,
        label="Fail Fast",
        tooltip="If True, stop processing when one item fails. If False, continue with remaining items.",
    ),
    PropertyDef(
        "timeout_per_item",
        PropertyType.INTEGER,
        default=60,
        min_value=1,
        label="Timeout per Item (s)",
        tooltip="Maximum time in seconds for each item's processing",
    ),
)
@executable_node
class ParallelForEachNode(BaseNode):
    """
    Parallel ForEach node that processes list items concurrently.

    Unlike regular ForLoop which processes items sequentially, this node
    processes multiple items at the same time (up to batch_size).

    Example:
        ParallelForEach ──→ ProcessItem ──→ Continue
            │
            ├─ items: [url1, url2, url3, url4, url5, ...]
            ├─ batch_size: 3  (process 3 at a time)
            └─ Outputs: current_item, current_index

    Inputs:
        - exec_in: Execution input
        - items: List of items to process

    Outputs:
        - body: Execution flow for each item (runs batch_size times concurrently)
        - completed: Fires when all items processed
        - current_item: Current item being processed
        - current_index: Current item index
        - results: List of results from all items

    Properties:
        - batch_size: How many items to process concurrently
        - fail_fast: Stop on first error if True
        - timeout_per_item: Timeout for each item's processing
    """

    def __init__(self, node_id: str, config: Optional[dict] = None) -> None:
        """Initialize ParallelForEach node."""
        super().__init__(node_id, config)
        self.name = "Parallel ForEach"
        self.node_type = "ParallelForEachNode"

    def _define_ports(self) -> None:
        """Define node ports."""
        self.add_input_port("exec_in", PortType.EXEC_INPUT)
        self.add_input_port("items", PortType.INPUT, DataType.LIST, required=True)
        self.add_output_port("body", PortType.EXEC_OUTPUT)
        self.add_output_port("completed", PortType.EXEC_OUTPUT)
        self.add_output_port("current_item", PortType.OUTPUT, DataType.ANY)
        self.add_output_port("current_index", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("results", PortType.OUTPUT, DataType.LIST)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        """
        Execute parallel foreach - process items in batches.

        Returns special 'parallel_foreach_batch' key for the executor
        to handle concurrent item processing.
        """
        self.status = NodeStatus.RUNNING

        try:
            state_key = f"{self.node_id}_parallel_foreach"
            batch_size = self.get_parameter("batch_size", 5)
            fail_fast = self.get_parameter("fail_fast", False)
            timeout_per_item = self.get_parameter("timeout_per_item", 60)

            # Initialize state on first call
            if not context.has_variable(state_key):
                items = self.get_input_value("items")
                if items is None:
                    items = []
                elif not isinstance(items, (list, tuple)):
                    items = [items]
                else:
                    items = list(items)

                context.set_variable(
                    state_key,
                    {
                        "items": items,
                        "index": 0,
                        "results": [],
                        "errors": [],
                    },
                )
                logger.info(
                    f"ParallelForEach initialized: {len(items)} items, batch_size={batch_size}"
                )

            state = context.get_variable(state_key)
            items = state["items"]
            index = state["index"]
            results = state["results"]

            # Check if all items processed
            if index >= len(items):
                # Clean up state
                context.delete_variable(state_key)

                # Set final results
                self.set_output_value("results", results)

                logger.info(
                    f"ParallelForEach completed: {len(results)} results, {len(state.get('errors', []))} errors"
                )

                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {
                        "total_items": len(items),
                        "processed": len(results),
                        "errors": len(state.get("errors", [])),
                    },
                    "next_nodes": ["completed"],
                }

            # Get current batch
            batch_end = min(index + batch_size, len(items))
            current_batch = items[index:batch_end]
            batch_indices = list(range(index, batch_end))

            # Update state for next iteration
            state["index"] = batch_end
            context.set_variable(state_key, state)

            logger.info(
                f"ParallelForEach batch: items {index}-{batch_end-1} of {len(items)}"
            )

            self.status = NodeStatus.RUNNING

            return {
                "success": True,
                "data": {
                    "batch_size": len(current_batch),
                    "batch_start": index,
                    "batch_end": batch_end,
                    "remaining": len(items) - batch_end,
                },
                # Special key for executor to handle parallel batch processing
                "parallel_foreach_batch": {
                    "items": current_batch,
                    "indices": batch_indices,
                    "body_port": "body",
                    "state_key": state_key,
                },
                "foreach_id": self.node_id,
                "fail_fast": fail_fast,
                "timeout_per_item": timeout_per_item,
                "next_nodes": [],  # Executor handles batching
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            logger.error(f"ParallelForEach execution failed: {e}")
            # Clean up state on error
            state_key = f"{self.node_id}_parallel_foreach"
            if context.has_variable(state_key):
                context.delete_variable(state_key)
            return {"success": False, "error": str(e), "next_nodes": []}


__all__ = [
    "ForkNode",
    "JoinNode",
    "ParallelForEachNode",
]
