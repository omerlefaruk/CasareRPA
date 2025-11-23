"""
Error Handling Workflow Template

Demonstrates error handling and recovery in workflows.
Shows how to catch errors and execute fallback logic.

Usage:
    python templates/control_flow/error_handling.py
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
from casare_rpa.nodes.variable_nodes import SetVariableNode
from casare_rpa.nodes.error_handling_nodes import TryNode


async def create_error_handling_workflow() -> WorkflowSchema:
    """
    Create a workflow that demonstrates error handling.
    
    Workflow:
        Start → Set value → Try Node → (Success: Set result / Error: Set error) → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Error Handling")
    
    # Create nodes
    start = StartNode("start_1")
    set_status = SetVariableNode("set_status", variable_name="status", default_value="initializing")
    
    # Try node for error handling
    try_node = TryNode("try_node")
    
    # Success path: set status to "success"
    success_status = SetVariableNode("success_status", variable_name="status", default_value="success")
    
    # Error path: set status to "error"
    error_status = SetVariableNode("error_status", variable_name="status", default_value="error")
    
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_status": set_status,
        "try_node": try_node,
        "success_status": success_status,
        "error_status": error_status,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_status", "exec_in"),
        NodeConnection("set_status", "exec_out", "try_node", "exec_in"),
        # Try body leads to success status
        NodeConnection("try_node", "try_body", "success_status", "exec_in"),
        # Catch body leads to error status
        NodeConnection("try_node", "catch_body", "error_status", "exec_in"),
        # Both paths converge to end
        NodeConnection("success_status", "exec_out", "end_1", "exec_in"),
        NodeConnection("error_status", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Error Handling workflow."""
    print("=" * 60)
    print("Error Handling Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Try-Catch error handling")
    print("  • Error recovery paths")
    print("  • Status tracking")
    print("  • Graceful error handling")
    
    # Create and run workflow
    workflow = await create_error_handling_workflow()
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
    
    print("\n✓ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
