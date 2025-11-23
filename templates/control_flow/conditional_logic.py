"""
Conditional Logic Workflow Template

Demonstrates if/else conditional branching in workflows.
Shows how to make decisions based on variable values.

Usage:
    python templates/control_flow/conditional_logic.py
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
from casare_rpa.nodes.control_flow_nodes import IfNode


async def create_conditional_workflow(age: int = 25) -> WorkflowSchema:
    """
    Create a workflow that uses conditional logic.
    
    Workflow:
        Start → Set age → If Node → (true: Adult var, false: Minor var) → End
    
    Args:
        age: Age value to test (default: 25)
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Conditional Logic")
    
    # Create nodes
    start = StartNode("start_1")
    set_age = SetVariableNode("set_age", variable_name="age", default_value=str(age))
    check_age = IfNode("check_age")
    # Configure condition: age >= 18
    check_age.config["condition"] = "age >= 18"
    
    # True branch: set status to "adult"
    adult_status = SetVariableNode("adult_status", variable_name="status", default_value="adult")
    
    # False branch: set status to "minor"
    minor_status = SetVariableNode("minor_status", variable_name="status", default_value="minor")
    
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_age": set_age,
        "check_age": check_age,
        "adult_status": adult_status,
        "minor_status": minor_status,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_age", "exec_in"),
        NodeConnection("set_age", "exec_out", "check_age", "exec_in"),
        # True branch: age >= 18
        NodeConnection("check_age", "true", "adult_status", "exec_in"),
        # False branch: age < 18
        NodeConnection("check_age", "false", "minor_status", "exec_in"),
        # Both paths converge to end
        NodeConnection("adult_status", "exec_out", "end_1", "exec_in"),
        NodeConnection("minor_status", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Conditional Logic workflow with different ages."""
    print("=" * 60)
    print("Conditional Logic Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • If/Else conditional branching")
    print("  • Condition evaluation based on variables")
    print("  • Multiple execution paths")
    
    # Test with adult age
    print("\n" + "-" * 60)
    print("Test 1: Adult user (age 25)")
    print("-" * 60)
    workflow1 = await create_conditional_workflow(age=25)
    runner1 = WorkflowRunner(workflow1)
    await runner1.run()
    
    if hasattr(runner1, 'context'):
        print(f"Age: {runner1.context.variables.get('age')}")
        print(f"Status: {runner1.context.variables.get('status')}")
    
    # Test with minor age
    print("\n" + "-" * 60)
    print("Test 2: Minor user (age 15)")
    print("-" * 60)
    workflow2 = await create_conditional_workflow(age=15)
    runner2 = WorkflowRunner(workflow2)
    await runner2.run()
    
    if hasattr(runner2, 'context'):
        print(f"Age: {runner2.context.variables.get('age')}")
        print(f"Status: {runner2.context.variables.get('status')}")
    
    print("\n✓ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
