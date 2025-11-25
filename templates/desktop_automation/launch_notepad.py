"""
Launch and Automate Notepad Template

Demonstrates basic desktop automation by launching Notepad,
typing text, and saving the file.

Usage:
    python templates/desktop_automation/launch_notepad.py
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
from casare_rpa.nodes.desktop_nodes import (
    LaunchApplicationNode,
    TypeTextNode,
    SendHotKeyNode,
    CloseApplicationNode,
)


async def create_notepad_workflow() -> WorkflowSchema:
    """
    Create a workflow that launches Notepad, types text, and saves.

    Workflow:
        Start → Launch Notepad → Type Text → Save (Ctrl+S) → Close → End
    """
    metadata = WorkflowMetadata(name="Launch and Use Notepad")

    # Create nodes
    start = StartNode("start_1")

    launch = LaunchApplicationNode("launch_notepad", config={
        "path": "notepad.exe",
        "wait_for_window": True,
        "timeout": 10
    })

    type_text = TypeTextNode("type_text", config={
        "text": "Hello from CasareRPA Desktop Automation!\n\nThis text was typed automatically.",
        "delay": 0.05
    })

    save_hotkey = SendHotKeyNode("save_file", config={
        "keys": ["ctrl", "s"]
    })

    close_app = CloseApplicationNode("close_notepad")

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "launch_notepad": launch,
        "type_text": type_text,
        "save_file": save_hotkey,
        "close_notepad": close_app,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "launch_notepad", "exec_in"),
        NodeConnection("launch_notepad", "exec_out", "type_text", "exec_in"),
        NodeConnection("type_text", "exec_out", "save_file", "exec_in"),
        NodeConnection("save_file", "exec_out", "close_notepad", "exec_in"),
        NodeConnection("close_notepad", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the Notepad automation workflow."""
    print("=" * 60)
    print("Launch and Automate Notepad Template")
    print("=" * 60)

    workflow = await create_notepad_workflow()
    runner = WorkflowRunner(workflow)

    print("\nRunning workflow...")
    print("This will launch Notepad and type some text.")
    await runner.run()

    print("\n Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
