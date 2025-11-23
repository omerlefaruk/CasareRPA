"""
Breakpoint Debugging Workflow Template

Demonstrates using breakpoints to pause execution and inspect state.
Perfect for learning the debugging features of CasareRPA.

Usage:
    python templates/debugging/breakpoint_debugging.py
"""

import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

import asyncio
from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode


async def create_breakpoint_workflow() -> WorkflowSchema:
    """
    Create a workflow for demonstrating breakpoint debugging.
    
    Workflow:
        Start → Set x → Set y → Set result → End
        (Use GUI to set breakpoints on any node)
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Breakpoint Debugging")
    
    # Create nodes
    start = StartNode("start_1")
    set_x = SetVariableNode("set_x", variable_name="x", default_value="10")
    set_y = SetVariableNode("set_y", variable_name="y", default_value="20")
    set_result = SetVariableNode("set_result", variable_name="result", default_value="complete")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_x": set_x,
        "set_y": set_y,
        "set_result": set_result,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_x", "exec_in"),
        NodeConnection("set_x", "exec_out", "set_y", "exec_in"),
        NodeConnection("set_y", "exec_out", "set_result", "exec_in"),
        NodeConnection("set_result", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Breakpoint Debugging workflow."""
    print("=" * 60)
    print("Breakpoint Debugging Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Setting breakpoints in GUI")
    print("  • Pausing execution at breakpoints")
    print("  • Inspecting variables during execution")
    print("  • Step-through debugging")
    print("\nNote: Load this template in GUI and use F9 to set breakpoints")
    
    # Create workflow
    workflow = await create_breakpoint_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
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


if __name__ == "__main__":
    asyncio.run(main())
