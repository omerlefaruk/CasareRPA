"""
Window Management Template

Demonstrates window management - moving, resizing, maximizing,
minimizing, and restoring windows.

Usage:
    python templates/desktop_automation/window_management.py
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
    ActivateWindowNode,
    MoveWindowNode,
    ResizeWindowNode,
    MaximizeWindowNode,
    MinimizeWindowNode,
    RestoreWindowNode,
    GetWindowPropertiesNode,
)


async def create_window_management_workflow() -> WorkflowSchema:
    """
    Create a workflow that demonstrates window management.

    Workflow:
        Start → Launch App → Get Properties → Move → Resize →
        Maximize → Minimize → Restore → End
    """
    metadata = WorkflowMetadata(name="Window Management Demo")

    # Create nodes
    start = StartNode("start_1")

    launch = LaunchApplicationNode("launch_calc", config={
        "path": "calc.exe",
        "wait_for_window": True,
        "timeout": 10
    })

    get_props = GetWindowPropertiesNode("get_window_props")

    move_window = MoveWindowNode("move_window", config={
        "x": 100,
        "y": 100
    })

    resize_window = ResizeWindowNode("resize_window", config={
        "width": 600,
        "height": 400
    })

    maximize = MaximizeWindowNode("maximize_window")
    minimize = MinimizeWindowNode("minimize_window")
    restore = RestoreWindowNode("restore_window")

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "launch_calc": launch,
        "get_window_props": get_props,
        "move_window": move_window,
        "resize_window": resize_window,
        "maximize_window": maximize,
        "minimize_window": minimize,
        "restore_window": restore,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "launch_calc", "exec_in"),
        NodeConnection("launch_calc", "exec_out", "get_window_props", "exec_in"),
        NodeConnection("launch_calc", "window", "get_window_props", "window"),
        NodeConnection("get_window_props", "exec_out", "move_window", "exec_in"),
        NodeConnection("launch_calc", "window", "move_window", "window"),
        NodeConnection("move_window", "exec_out", "resize_window", "exec_in"),
        NodeConnection("launch_calc", "window", "resize_window", "window"),
        NodeConnection("resize_window", "exec_out", "maximize_window", "exec_in"),
        NodeConnection("launch_calc", "window", "maximize_window", "window"),
        NodeConnection("maximize_window", "exec_out", "minimize_window", "exec_in"),
        NodeConnection("launch_calc", "window", "minimize_window", "window"),
        NodeConnection("minimize_window", "exec_out", "restore_window", "exec_in"),
        NodeConnection("launch_calc", "window", "restore_window", "window"),
        NodeConnection("restore_window", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the window management workflow."""
    print("=" * 60)
    print("Window Management Template")
    print("=" * 60)

    workflow = await create_window_management_workflow()
    runner = WorkflowRunner(workflow)

    print("\nRunning workflow...")
    print("This will launch Calculator and demonstrate window operations.")
    await runner.run()

    print("\n Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
