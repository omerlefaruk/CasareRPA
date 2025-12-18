import sys
import os
import json

# Add src to sys.path
sys.path.append(os.path.join(os.getcwd(), "src"))

from casare_rpa.tools.workflow_builder import WorkflowBuilder


def create_scene():
    builder = WorkflowBuilder()
    builder.workflow_data["metadata"]["name"] = "Market Index Snapshot (Fixed)"
    builder.workflow_data["metadata"]["description"] = (
        "Extracted following AI SmartWorkflow Assistant rules - StructuredDataSuperNode Fix"
    )

    # 1. Launch Browser
    launch_id = "launch_browser"
    builder.add_node(
        node_type="LaunchBrowserNode",
        node_id=launch_id,
        config={
            "url": "https://www.google.com/finance/markets/indexes",
            "headless": True,
        },
        position=(0, 0),
    )

    # 2. Extract Market Data
    extract_id = "extract_market_data"
    builder.add_node(
        node_type="ExtractTextNode",
        node_id=extract_id,
        config={
            "selector": "ul.sbnBtf",
            "variable_name": "raw_market_text",
            "use_inner_text": True,
            "timeout": 30000,
        },
        position=(400, 0),
    )

    # 3. Filter Data
    filter_id = "filter_data"
    code_content = """result = []
if market_text:
    blocks = market_text.split('INDEX')
    for b in blocks:
        lines = [l.strip() for l in b.splitlines() if l.strip()]
        if len(lines) >= 2:
            name = lines[0]
            price = lines[1]
            if any(c.isdigit() for c in price):
                result.append({'Index': name, 'Last Price': price})"""

    builder.add_node(
        node_type="RunPythonScriptNode",
        node_id=filter_id,
        config={
            "variables": {"market_text": f"{{{{{extract_id}.text}}}}"},
            "code": code_content,
        },
        position=(800, 0),
    )

    # 4. Save JSON
    save_id = "save_json"
    builder.add_node(
        node_type="StructuredDataSuperNode",
        node_id=save_id,
        config={
            "action": "Write JSON",
            "file_path": "C:\\Users\\Rau\\Documents\\market_snapshot.json",
            "data": f"{{{{{filter_id}.result}}}}",
            "indent": 2,
        },
        position=(1200, 0),
    )

    # 5. Close Browser
    close_id = "close_browser"
    builder.add_node(
        node_type="CloseBrowserNode", node_id=close_id, config={}, position=(1600, 0)
    )

    # Connections
    builder.connect(launch_id, "exec_out", extract_id, "exec_in")
    builder.connect(extract_id, "exec_out", filter_id, "exec_in")
    builder.connect(filter_id, "exec_out", save_id, "exec_in")
    builder.connect(save_id, "exec_out", close_id, "exec_in")

    # Save
    output_path = "workflows/market_snapshot_scene.json"
    builder.save(output_path)
    print(f"Scene file created at {output_path}")


if __name__ == "__main__":
    create_scene()
