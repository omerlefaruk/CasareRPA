"""
Data Transformation Workflow Template

Demonstrates data manipulation and transformation operations.
Shows filtering and processing patterns.

Usage:
    python templates/automation/data_transformation.py
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
from casare_rpa.nodes.control_flow_nodes import ForLoopNode, IfNode


async def create_data_transformation_workflow() -> WorkflowSchema:
    """
    Create a workflow that transforms data with filtering.
    
    Workflow:
        Start → Set data → Init counter → For each item → If check → Increment → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Data Transformation")
    
    # Create nodes
    start = StartNode("start_1")
    set_data = SetVariableNode("set_data", variable_name="data", 
                                default_value=[10, 25, 33, 50, 67, 85, 90])
    init_count = SetVariableNode("init_count", variable_name="count", default_value="0")
    for_loop = ForLoopNode("for_loop")
    for_loop.config["iterable_source"] = "data"
    for_loop.config["item_variable"] = "item"
    
    check_value = IfNode("check_value")
    check_value.config["condition"] = "item >= 50"
    
    increment = IncrementVariableNode("increment", variable_name="count", increment=1)
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_data": set_data,
        "init_count": init_count,
        "for_loop": for_loop,
        "check_value": check_value,
        "increment": increment,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_data", "exec_in"),
        NodeConnection("set_data", "exec_out", "init_count", "exec_in"),
        NodeConnection("init_count", "exec_out", "for_loop", "exec_in"),
        NodeConnection("for_loop", "loop_body", "check_value", "exec_in"),
        NodeConnection("check_value", "true", "increment", "exec_in"),
        NodeConnection("increment", "exec_out", "for_loop", "loop_continue"),
        NodeConnection("check_value", "false", "for_loop", "loop_continue"),
        NodeConnection("for_loop", "loop_complete", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Data Transformation workflow."""
    print("=" * 60)
    print("Data Transformation Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Data filtering (items >= 50)")
    print("  • Conditional logic in loops")
    print("  • Counter increments")
    
    # Create workflow
    workflow = await create_data_transformation_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    print("\nRunning workflow...")
    await runner.run()
    
    # Show results
    print("\nFinal Variables:")
    if hasattr(runner, 'context'):
        variables = runner.context.variables
        print(f"  Data: {variables.get('data')}")
        print(f"  Count (items >= 50): {variables.get('count')}")
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
