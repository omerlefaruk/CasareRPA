"""
File Processing Workflow Template

Demonstrates file operations workflow pattern.
A simple example for file-based automation.

Usage:
    python templates/automation/file_processing.py
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
from casare_rpa.nodes.control_flow_nodes import ForLoopNode


async def create_file_processing_workflow() -> WorkflowSchema:
    """
    Create a workflow that simulates file processing.
    
    Workflow:
        Start → Set file list → For each file → Process → End
    
    Returns:
        Configured workflow
    """
    metadata = WorkflowMetadata(name="File Processing")
    
    # Create nodes
    start = StartNode("start_1")
    set_files = SetVariableNode("set_files", variable_name="files", 
                                 default_value=["document1.txt", "document2.txt", "document3.txt"])
    for_loop = ForLoopNode("for_loop")
    for_loop.config["iterable_source"] = "files"
    for_loop.config["item_variable"] = "current_file"
    set_status = SetVariableNode("set_status", variable_name="status", default_value="processed")
    end = EndNode("end_1")
    
    # Build workflow
    nodes = {
        "start_1": start,
        "set_files": set_files,
        "for_loop": for_loop,
        "set_status": set_status,
        "end_1": end
    }
    
    connections = [
        NodeConnection("start_1", "exec_out", "set_files", "exec_in"),
        NodeConnection("set_files", "exec_out", "for_loop", "exec_in"),
        NodeConnection("for_loop", "loop_body", "set_status", "exec_in"),
        NodeConnection("set_status", "exec_out", "for_loop", "loop_continue"),
        NodeConnection("for_loop", "loop_complete", "end_1", "exec_in")
    ]
    
    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections
    
    return workflow


async def main():
    """Run the File Processing workflow."""
    print("=" * 60)
    print("File Processing Workflow Template")
    print("=" * 60)
    print("\nThis workflow demonstrates:")
    print("  • Looping over a list of files")
    print("  • Processing each file")
    print("  • File automation pattern")
    
    # Create workflow
    workflow = await create_file_processing_workflow()
    
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
