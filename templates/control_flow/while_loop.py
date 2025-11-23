"""
While Loop Workflow Template

Demonstrates conditional iteration using WhileLoopNode.
Shows how to repeat tasks until a condition is met.

Usage:
    python templates/control_flow/while_loop.py
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
from casare_rpa.nodes.control_flow_nodes import WhileLoopNode


async def create_while_loop_workflow() -> WorkflowSchema:
    """
    Create a workflow that uses a while loop.
    
    Workflow:
        Start → Init counter → While counter < 5 → Increment → Loop back → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="While Loop Example")
    
    # Create nodes
    start = StartNode("start_1")
    init_counter = SetVariableNode("init_counter", variable_name="counter", default_value="0")
    
    # While loop (counter < 5)
    while_loop = WhileLoopNode("while_loop")
    while_loop.config["condition"] = "counter < 5"
    
    # Increment counter in loop body
    increment = IncrementVariableNode("increment", variable_name="counter", increment=1)
    
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "init_counter": init_counter,
        "while_loop": while_loop,
        "increment": increment,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "init_counter", "exec_in"),
        NodeConnection("init_counter", "exec_out", "while_loop", "exec_in"),
        NodeConnection("while_loop", "loop_body", "increment", "exec_in"),
        NodeConnection("increment", "exec_out", "while_loop", "loop_continue"),
        NodeConnection("while_loop", "loop_complete", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the While Loop workflow."""
    print("=" * 60)
    print("While Loop Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • While loop conditional iteration")
    print("  • Loop condition evaluation")
    print("  • Variable increments in loop body")
    print("  • Loop termination when condition becomes false")
    
    # Create workflow
    workflow = await create_while_loop_workflow()
    
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
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
