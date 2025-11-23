"""
Web Scraping Skeleton Workflow Template

Demonstrates the basic structure for web automation workflows.
Provides a framework for browser-based automation (skeleton).

Usage:
    python templates/automation/web_scraping_skeleton.py

Note: This is a skeleton showing the workflow pattern.
      Browser nodes will be added when available.
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
from casare_rpa.nodes.wait_nodes import WaitNode


async def create_web_scraping_workflow() -> WorkflowSchema:
    """
    Create a workflow skeleton for web automation.
    
    Workflow:
        Start → Set URL → Wait (simulate navigation) → Set result → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="Web Scraping Skeleton")
    
    # Create nodes
    start = StartNode("start_1")
    set_url = SetVariableNode("set_url", variable_name="target_url", 
                               default_value="https://example.com")
    wait_nav = WaitNode("wait_nav")
    wait_nav.config["wait_duration"] = 2.0  # Simulate page load
    set_result = SetVariableNode("set_result", variable_name="page_title", 
                                  default_value="Example Domain")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_url": set_url,
        "wait_nav": wait_nav,
        "set_result": set_result,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_url", "exec_in"),
        NodeConnection("set_url", "exec_out", "wait_nav", "exec_in"),
        NodeConnection("wait_nav", "exec_out", "set_result", "exec_in"),
        NodeConnection("set_result", "exec_out", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the Web Scraping Skeleton workflow."""
    print("=" * 60)
    print("Web Scraping Skeleton Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Web automation workflow structure")
    print("  • URL setup")
    print("  • Simulated page navigation")
    print("  • Data extraction pattern")
    print("\nNote: This is a skeleton. Add browser nodes when available.")
    
    # Create workflow
    workflow = await create_web_scraping_workflow()
    
    # Create runner
    runner = WorkflowRunner(workflow)
    
    print("\nRunning workflow...")
    await runner.run()
    
    # Show results
    print("\nFinal Variables:")
    if hasattr(runner, 'context'):
        variables = runner.context.variables
        print(f"  URL: {variables.get('target_url')}")
        print(f"  Page Title: {variables.get('page_title')}")
    
    print("\n✓ Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
