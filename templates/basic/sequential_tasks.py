"""
Sequential Tasks Workflow Template

Demonstrates a sequence of tasks executed in order.
Shows how to chain multiple nodes together.

Usage:
    python templates/basic/sequential_tasks.py
"""

import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

import asyncio
from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode, IncrementVariableNode
from casare_rpa.nodes.wait_nodes import WaitNode


async def create_sequential_workflow() -> WorkflowSchema:
    """
    Create a workflow with sequential task execution.
    
    Workflow:
        Start → Task 1 → Wait → Task 2 → Wait → Task 3 → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Sequential Tasks")
    
    # Create nodes
    start = StartNode("start_1")
    
    # Task 1: Set counter to 0
    task1 = SetVariableNode("task_1", variable_name="task_count", default_value="0")
    
    # Wait 1 second
    wait1 = WaitNode("wait_1")
    wait1.config["wait_duration"] = 1.0
    
    # Task 2: Increment counter
    task2 = IncrementVariableNode("task_2", variable_name="task_count", increment=1)
    
    # Wait 1 second
    wait2 = WaitNode("wait_2")
    wait2.config["wait_duration"] = 1.0
    
    # Task 3: Increment counter again
    task3 = IncrementVariableNode("task_3", variable_name="task_count", increment=1)
    
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "task_1": task1,
        "wait_1": wait1,
        "task_2": task2,
        "wait_2": wait2,
        "task_3": task3,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "task_1", "exec_in"),
        NodeConnection("task_1", "exec_out", "wait_1", "exec_in"),
        NodeConnection("wait_1", "exec_out", "task_2", "exec_in"),
        NodeConnection("task_2", "exec_out", "wait_2", "exec_in"),
        NodeConnection("wait_2", "exec_out", "task_3", "exec_in"),
        NodeConnection("task_3", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Sequential Tasks workflow."""
    print("=" * 60)
    print("Sequential Tasks Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Sequential task execution")
    print("  • Task chaining with connections")
    print("  • Wait nodes for delays")
    print("  • Variable increments")
    
    # Create workflow
    workflow = await create_sequential_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    # Run workflow
    print("\nRunning workflow...")
    await runner.run()
    
    # Show results
    print("\nFinal Variables:")
    if hasattr(runner, 'context'):
        variables = runner.context.variables
        for name, value in variables.items():
            print(f"  {name} = {value}")
    
    print("\n✓ Workflow completed successfully!")
    print(f"  Total nodes executed: {len(workflow.nodes)}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
