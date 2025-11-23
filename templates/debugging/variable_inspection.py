"""
Variable Inspection Workflow Template

Demonstrates real-time variable inspection during execution.
Shows how to watch variable changes throughout the workflow.

Usage:
    python templates/debugging/variable_inspection.py
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


async def create_variable_inspection_workflow() -> WorkflowSchema:
    """
    Create a workflow for demonstrating variable inspection.
    
    Workflow:
        Start → Set var1 → Set var2 → Set var3 → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Variable Inspection")
    
    # Create nodes
    start = StartNode("start_1")
    set_name = SetVariableNode("set_name", variable_name="name", default_value="CasareRPA")
    set_version = SetVariableNode("set_version", variable_name="version", default_value="1.0.0")
    set_count = SetVariableNode("set_count", variable_name="execution_count", default_value="1")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_name": set_name,
        "set_version": set_version,
        "set_count": set_count,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_name", "exec_in"),
        NodeConnection("set_name", "exec_out", "set_version", "exec_in"),
        NodeConnection("set_version", "exec_out", "set_count", "exec_in"),
        NodeConnection("set_count", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Variable Inspection workflow."""
    print("=" * 60)
    print("Variable Inspection Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Setting multiple variables")
    print("  • Inspecting variable values in GUI")
    print("  • Watching variables change")
    
    # Create workflow
    workflow = await create_variable_inspection_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    print("\nRunning workflow...")
    await runner.run()
    
    # Show all variables
    print("\nFinal Variables:")
    if hasattr(runner, 'context'):
        variables = runner.context.variables
        for name, value in variables.items():
            print(f"  {name} = {value}")
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
