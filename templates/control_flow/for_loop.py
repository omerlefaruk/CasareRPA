"""
For Loop Workflow Template

Demonstrates iteration over a collection using ForLoopNode.
Shows how to repeat tasks for each item in a list.

Usage:
    python templates/control_flow/for_loop.py
"""

import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent.parent / "src"
if src_path.exists():
    sys.path.insert(0, str(src_path))

import asyncio
from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
from casare_rpa.runner.workflow_runner import WorkflowRunner
from casare_rpa.nodes.basic_nodes import StartNode, EndNode
from casare_rpa.nodes.variable_nodes import SetVariableNode
from casare_rpa.nodes.control_flow_nodes import ForLoopNode


async def create_for_loop_workflow() -> WorkflowSchema:
    """
    Create a workflow that uses a for loop.
    
    Workflow:
        Start → Set items → For each item → Increment counter → Loop back → End
    
    Returns:
        Configured workflow schema
    """
    metadata = WorkflowMetadata(
        name="For Loop Example",
        description="Demonstrates iteration over a collection using ForLoopNode"
    )
    
    # Create node instances
    start = StartNode("start_1")
    
    # Set list of items to iterate
    set_items = SetVariableNode(
        "set_items_1",
        name="Set Items",
        variable_name="items",
        default_value=["Apple", "Banana", "Cherry", "Date", "Elderberry"]
    )
    
    # Initialize counter
    init_counter = SetVariableNode(
        "init_counter_1",
        name="Init Counter",
        variable_name="counter",
        default_value=0
    )
    
    # For loop over items
    for_loop = ForLoopNode("for_loop_1", config={
        "iterable_source": "items",
        "item_variable": "current_item",
        "index_variable": "loop_index"
    })
    
    # Increment counter in loop body
    increment = SetVariableNode(
        "increment_1",
        name="Increment Counter",
        variable_name="counter",
        default_value=None  # Will be set via expression in context
    )
    
    end = EndNode("end_1")
    
    # Build nodes dict
    nodes = {
        "start_1": start,
        "set_items_1": set_items,
        "init_counter_1": init_counter,
        "for_loop_1": for_loop,
        "increment_1": increment,
        "end_1": end
    }
    
    # Build connections list
    connections = [
        NodeConnection("start_1", "exec_out", "set_items_1", "exec_in"),
        NodeConnection("set_items_1", "exec_out", "init_counter_1", "exec_in"),
        NodeConnection("init_counter_1", "exec_out", "for_loop_1", "exec_in"),
        NodeConnection("for_loop_1", "loop_body", "increment_1", "exec_in"),
        NodeConnection("increment_1", "exec_out", "for_loop_1", "loop_continue"),
        NodeConnection("for_loop_1", "loop_complete", "end_1", "exec_in")
    ]
    
    # Create workflow
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    # Set start node
    workflow.set_start_node(set_items.node_id)
    
    return workflow


async def main():
    """Run the For Loop workflow."""
    print("=" * 60)
    print("For Loop Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • For loop iteration")
    print("  • Looping over a list")
    print("  • Accessing loop variables (item, index)")
    print("  • Loop body execution")
    
    # Create workflow
    workflow = await create_for_loop_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    # Run workflow
    print("\nRunning workflow...")
    await runner.run()
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
