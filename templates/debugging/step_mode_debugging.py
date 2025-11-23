"""
Step Mode Debugging Workflow Template

Demonstrates step-by-step execution for detailed inspection.
Shows how to step through each node one at a time.

Usage:
    python templates/debugging/step_mode_debugging.py
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
from casare_rpa.nodes.variable_nodes import SetVariableNode, IncrementVariableNode


async def create_step_mode_workflow() -> WorkflowSchema:
    """
    Create a workflow for demonstrating step mode debugging.
    
    Workflow:
        Start → Step 1 → Step 2 → Step 3 → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Step Mode Debugging")
    
    # Create nodes
    start = StartNode("start_1")
    step1 = SetVariableNode("step1", variable_name="counter", default_value="1")
    step2 = IncrementVariableNode("step2", variable_name="counter", increment=1)
    step3 = IncrementVariableNode("step3", variable_name="counter", increment=2)
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "step1": step1,
        "step2": step2,
        "step3": step3,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "step1", "exec_in"),
        NodeConnection("step1", "exec_out", "step2", "exec_in"),
        NodeConnection("step2", "exec_out", "step3", "exec_in"),
        NodeConnection("step3", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Step Mode Debugging workflow."""
    print("=" * 60)
    print("Step Mode Debugging Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Step-by-step execution in GUI")
    print("  • Inspecting variables at each step")
    print("  • Use F10 to step through nodes")
    
    # Create workflow
    workflow = await create_step_mode_workflow()
    
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
