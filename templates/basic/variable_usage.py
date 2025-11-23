"""
Variable Usage Workflow Template

Demonstrates how to set and use variables in a workflow.
Shows variable storage and retrieval across multiple nodes.

Usage:
    python templates/basic/variable_usage.py
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


async def create_variable_workflow() -> WorkflowSchema:
    """
    Create a workflow that demonstrates variable usage.
    
    Workflow:
        Start → Set username → Set greeting → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Variable Usage")
    
    # Create nodes
    start = StartNode("start_1")
    set_username = SetVariableNode("set_username", variable_name="username", default_value="CasareRPA User")
    set_greeting = SetVariableNode("set_greeting", variable_name="greeting", default_value="Welcome to CasareRPA!")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_username": set_username,
        "set_greeting": set_greeting,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_username", "exec_in"),
        NodeConnection("set_username", "exec_out", "set_greeting", "exec_in"),
        NodeConnection("set_greeting", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Variable Usage workflow."""
    print("=" * 60)
    print("Variable Usage Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Setting variables")
    print("  • Variable persistence across nodes")
    print("  • Accessing variables after execution")
    
    # Create workflow
    workflow = await create_variable_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    # Run workflow
    print("\nRunning workflow...")
    await runner.run()
    
    # Show final variables
    print("\nFinal Variables:")
    if hasattr(runner, 'context'):
        variables = runner.context.variables
        for name, value in variables.items():
            print(f"  {name} = {value}")
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
