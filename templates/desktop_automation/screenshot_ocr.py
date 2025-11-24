"""
Screenshot and OCR Template

Demonstrates capturing screenshots and extracting text using OCR.

Usage:
    python templates/desktop_automation/screenshot_ocr.py
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
    CaptureScreenshotNode,
    OCRExtractTextNode,
)
from casare_rpa.nodes.variable_nodes import SetVariableNode


async def create_screenshot_ocr_workflow() -> WorkflowSchema:
    """
    Create a workflow that captures a screenshot and extracts text.

    Workflow:
        Start → Capture Screenshot → OCR Extract → Set Result Variable → End
    """
    metadata = WorkflowMetadata(name="Screenshot and OCR Demo")

    # Create nodes
    start = StartNode("start_1")

    screenshot = CaptureScreenshotNode("capture_screen", config={
        "save_path": "screenshot.png",
        "region": None  # Full screen
    })

    ocr = OCRExtractTextNode("extract_text", config={
        "engine": "auto",
        "language": "eng"
    })

    save_result = SetVariableNode("save_result",
        variable_name="extracted_text",
        default_value=""
    )

    end = EndNode("end_1")

    # Build workflow
    nodes = {
        "start_1": start,
        "capture_screen": screenshot,
        "extract_text": ocr,
        "save_result": save_result,
        "end_1": end
    }

    connections = [
        NodeConnection("start_1", "exec_out", "capture_screen", "exec_in"),
        NodeConnection("capture_screen", "exec_out", "extract_text", "exec_in"),
        NodeConnection("capture_screen", "image_path", "extract_text", "image_path"),
        NodeConnection("extract_text", "exec_out", "save_result", "exec_in"),
        NodeConnection("extract_text", "text", "save_result", "value"),
        NodeConnection("save_result", "exec_out", "end_1", "exec_in"),
    ]

    workflow = WorkflowSchema(metadata)
    workflow.nodes = nodes
    workflow.connections = connections

    return workflow


async def main():
    """Run the screenshot and OCR workflow."""
    print("=" * 60)
    print("Screenshot and OCR Template")
    print("=" * 60)

    workflow = await create_screenshot_ocr_workflow()
    runner = WorkflowRunner(workflow)

    print("\nRunning workflow...")
    print("This will capture a screenshot and extract text using OCR.")
    await runner.run()

    # Show extracted text
    variables = runner.context.variables if hasattr(runner, 'context') else {}
    text = variables.get('extracted_text', '')
    if text:
        print(f"\nExtracted text (first 200 chars):\n{text[:200]}...")

    print("\n Workflow completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
