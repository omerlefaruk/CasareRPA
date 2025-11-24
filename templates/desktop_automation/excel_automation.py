"""
Excel Automation Template

Demonstrates Excel automation - opening a workbook, reading data,
writing data, and saving changes.

Usage:
    python templates/desktop_automation/excel_automation.py
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
    ExcelOpenNode,
    ExcelReadCellNode,
    ExcelWriteCellNode,
    ExcelCloseNode,
)


async def create_excel_workflow() -> WorkflowSchema:
    """
    Create a workflow that demonstrates Excel automation.

    Workflow:
        Start → Open Excel → Read Cell → Write Cell → Close → End
    """
    metadata = WorkflowMetadata(name="Excel Automation Demo")

    # Create nodes
    start = StartNode("start_1")

    open_excel = ExcelOpenNode("open_excel", config={
        "visible": True,
        "create_if_missing": True
    })

    read_cell = ExcelReadCellNode("read_a1", config={
        "sheet": 1
    })

    write_cell = ExcelWriteCellNode("write_b1", config={
        "sheet": 1
    })

    close_excel = ExcelCloseNode("close_excel", config={
        "save": True,
        "quit_app": True
    })

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "open_excel": open_excel,
        "read_a1": read_cell,
        "write_b1": write_cell,
        "close_excel": close_excel,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "open_excel", "exec_in"),
        NodeConnection("open_excel", "exec_out", "read_a1", "exec_in"),
        NodeConnection("open_excel", "workbook", "read_a1", "workbook"),
        NodeConnection("read_a1", "exec_out", "write_b1", "exec_in"),
        NodeConnection("open_excel", "workbook", "write_b1", "workbook"),
        NodeConnection("write_b1", "exec_out", "close_excel", "exec_in"),
        NodeConnection("open_excel", "workbook", "close_excel", "workbook"),
        NodeConnection("open_excel", "app", "close_excel", "app"),
        NodeConnection("close_excel", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the Excel automation workflow."""
    print("=" * 60)
    print("Excel Automation Template")
    print("=" * 60)

    workflow = await create_excel_workflow()
    runner = WorkflowRunner(workflow)

    print("\nRunning workflow...")
    print("This will open Excel, read/write cells, and close.")
    await runner.run()

    print("\n Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
