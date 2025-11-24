"""
Mouse and Keyboard Automation Template

Demonstrates mouse movement, clicking, and keyboard input automation.

Usage:
    python templates/desktop_automation/mouse_keyboard_demo.py
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
    GetMousePositionNode,
    MoveMouseNode,
    MouseClickNode,
    SendKeysNode,
    SendHotKeyNode,
)


async def create_mouse_keyboard_workflow() -> WorkflowSchema:
    """
    Create a workflow that demonstrates mouse and keyboard control.

    Workflow:
        Start → Get Position → Move Mouse → Click → Type Text → Hotkey → End
    """
    metadata = WorkflowMetadata(name="Mouse and Keyboard Demo")

    # Create nodes
    start = StartNode("start_1")

    get_pos = GetMousePositionNode("get_position")

    move_mouse = MoveMouseNode("move_mouse", config={
        "x": 500,
        "y": 300,
        "duration": 0.5
    })

    click = MouseClickNode("click_mouse", config={
        "button": "left",
        "clicks": 1
    })

    send_keys = SendKeysNode("type_text", config={
        "text": "Hello from CasareRPA!",
        "interval": 0.05
    })

    hotkey = SendHotKeyNode("send_hotkey", config={
        "keys": ["ctrl", "a"]  # Select all
    })

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "get_position": get_pos,
        "move_mouse": move_mouse,
        "click_mouse": click,
        "type_text": send_keys,
        "send_hotkey": hotkey,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "get_position", "exec_in"),
        NodeConnection("get_position", "exec_out", "move_mouse", "exec_in"),
        NodeConnection("move_mouse", "exec_out", "click_mouse", "exec_in"),
        NodeConnection("click_mouse", "exec_out", "type_text", "exec_in"),
        NodeConnection("type_text", "exec_out", "send_hotkey", "exec_in"),
        NodeConnection("send_hotkey", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the mouse and keyboard workflow."""
    print("=" * 60)
    print("Mouse and Keyboard Automation Template")
    print("=" * 60)

    workflow = await create_mouse_keyboard_workflow()
    runner = WorkflowRunner(workflow)

    print("\nRunning workflow...")
    print("This will control the mouse and keyboard.")
    await runner.run()

    print("\n Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
