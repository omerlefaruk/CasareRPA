import asyncio
import os
import sys
from pathlib import Path

import orjson

# Add src to path
sys.path.append(str(Path(__file__).parent.parent.parent.joinpath("src")))


class MockContext:
    def __init__(self):
        self.resources = {}
        self.variables = {}
        self.workflow_name = "MockWorkflow"
        self._stopped = False

    def clone_for_branch(self, branch_name):
        new_ctx = MockContext()
        new_ctx.variables = self.variables.copy()
        new_ctx.resources = self.resources
        return new_ctx

    def set_variable(self, name, value):
        self.variables[name] = value

    def get_variable(self, name, default=None):
        return self.variables.get(name, default)

    def is_stopped(self):
        return self._stopped

    def set_current_node(self, node_id):
        pass

    def add_error(self, node_id, error):
        print(f"MockContext Error on {node_id}: {error}")

    def resolve_value(self, value):
        # Simple resolution for testing
        return value

    def mark_completed(self):
        pass


# Import the node AFTER the sys.path hack
from loguru import logger

from casare_rpa.nodes.workflow.execute_workflow_node import ExecuteWorkflowNode


async def test_execute_workflow():
    print("--- Starting Verification ---")

    # 1. Create a dummy workflow JSON
    workflow_data = {
        "nodes": {
            "node_1": {
                "type": "VisualStartNode",
                "name": "Start",
                "custom": {"node_id": "node_1"},
                "properties": {},
            },
            "node_2": {
                "type": "VisualLogNode",
                "name": "Log",
                "custom": {"node_id": "node_2"},
                "properties": {
                    "message": "Hello from Child Workflow!",
                    "level": "INFO",
                },
            },
        },
        "connections": [{"out": ["node_1", "exec_out"], "in": ["node_2", "exec_in"]}],
        "metadata": {"name": "Child Workflow"},
    }

    temp_file = Path("temp_child_workflow.json")
    with open(temp_file, "wb") as f:  # noqa: ASYNC230
        f.write(orjson.dumps(workflow_data))

    print(f"Created temp workflow file: {temp_file}")

    try:
        # 2. Setup Node
        node = ExecuteWorkflowNode(
            node_id="main_node",
            config={
                "workflow_path": str(temp_file.absolute()),
                "wait_for_completion": True,
            },
        )

        context = MockContext()

        # 3. Execute
        print("Executing node...")
        result = await node.execute(context)

        print(f"Execution Result: {result}")

        if result["success"]:
            print("SUCCESS: Workflow executed successfully.")
        else:
            print(f"FAILURE: {result.get('error')}")

    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        if temp_file.exists():
            os.remove(temp_file)
            print("Cleaned up temp file.")


if __name__ == "__main__":
    # Configure loguru to print to stderr
    logger.remove()
    logger.add(sys.stderr, level="DEBUG")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_execute_workflow())
