"""
Hello World Workflow Template

The simplest possible workflow - sets a "Hello, World!" message variable.
Perfect for testing your CasareRPA installation.

Usage:
    python templates/basic/hello_world.py
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


async def create_hello_world_workflow() -> WorkflowSchema:
    """
    Create a simple Hello World workflow.
    
    Workflow:
        Start → Set "message" variable → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Hello World")
    
    # Create nodes
    start = StartNode("start_1")
    set_message = SetVariableNode("set_message", variable_name="message", default_value="Hello, World!")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_message": set_message,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_message", "exec_in"),
        NodeConnection("set_message", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Hello World workflow."""
    print("=" * 60)
    print("Hello World Workflow Template")
    print("=" * 60)
    
    # Create workflow
    workflow = await create_hello_world_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    # Run workflow
    print("\nRunning workflow...")
    await runner.run()
    
    # Show result
    variables = runner.context.variables if hasattr(runner, 'context') else {}
    print(f"\nMessage: {variables.get('message', 'N/A')}")
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
