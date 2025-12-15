"""
Generate a robust workflow plan using SmartWorkflowAgent.
This script takes the existing Zip->Gmail workflow and asks the AI to make it more robust.
"""

import asyncio
import json

from casare_rpa.infrastructure.ai.smart_agent import SmartWorkflowAgent


async def main():
    # Original workflow from user
    original_workflow = {
        "nodes": {
            "zip_node": {
                "node_type": "ZipFilesNode",
                "config": {
                    "compression": "ZIP_STORED",
                    "zip_path": "C:/Users/Rau/Desktop/muhasebe/zip.zip",
                    "source_path": "C:/Users/Rau/Desktop/muhasebe",
                    "base_dir": "",
                },
                "position": [-368, 35],
            },
            "gmail_node": {
                "node_type": "GmailSendWithAttachmentNode",
                "config": {
                    "credential_id": "cred_3be9a941dfef",
                    "to": "omerlefaruk@gmail.com",
                    "cc": "",
                    "bcc": "",
                    "subject": "hey",
                    "body": "hey",
                    "body_type": "plain",
                    "attachments": "",
                },
                "position": [186, 35],
            },
        },
        "connections": [
            {
                "source_node": "zip_node",
                "source_port": "exec_out",
                "target_node": "gmail_node",
                "target_port": "exec_in",
            },
            {
                "source_node": "zip_node",
                "source_port": "attachment_file",
                "target_node": "gmail_node",
                "target_port": "attachments",
            },
        ],
    }

    prompt = """
Make this workflow more robust with proper error handling and validation.
The current workflow:
1. Zips files from C:/Users/Rau/Desktop/muhasebe folder
2. Sends the zip via Gmail to omerlefaruk@gmail.com

Please add:
1. Folder existence check before zipping
2. File exist check after zipping to verify the zip was created
3. Error handling with MessageBox for failures
4. Success notification at the end
5. Proper connection of data outputs (zip path to Gmail attachments)

Generate a complete, production-ready workflow with all nodes and connections.
Use real node types from the registry.
"""

    print("=" * 80)
    print("GENERATING ROBUST WORKFLOW WITH SmartWorkflowAgent")
    print("=" * 80)
    print()
    print("Original workflow:")
    print("-" * 40)
    print(json.dumps(original_workflow, indent=2))
    print("-" * 40)
    print()
    print("Prompt:", prompt[:200], "...")
    print()

    agent = SmartWorkflowAgent()

    try:
        result = await agent.generate_workflow(
            user_prompt=prompt,
            existing_workflow=original_workflow,
            model="gpt-4o-mini",
            temperature=0.3,
        )

        print("=" * 80)
        print("GENERATION RESULT")
        print("=" * 80)
        print(f"Success: {result.success}")
        print(f"Error: {result.error or 'None'}")
        print()

        if result.success and result.workflow:
            print("Generated Workflow:")
            print("-" * 40)
            print(json.dumps(result.workflow, indent=2))
            print("-" * 40)

            # Print ASCII diagram
            print()
            print("=" * 80)
            print("WORKFLOW ASCII DIAGRAM")
            print("=" * 80)
            print_ascii_workflow(result.workflow)

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


def print_ascii_workflow(workflow: dict):
    """Print ASCII representation of workflow."""
    nodes = workflow.get("nodes", {})
    connections = workflow.get("connections", [])

    if not nodes:
        print("(no nodes)")
        return

    # Build connection map
    exec_connections = {}  # target -> source
    data_connections = []  # (source_node, source_port, target_node, target_port)

    for conn in connections:
        src_node = conn.get("source_node", "")
        src_port = conn.get("source_port", "")
        tgt_node = conn.get("target_node", "")
        tgt_port = conn.get("target_port", "")

        if "exec" in src_port.lower() or "exec" in tgt_port.lower():
            exec_connections[tgt_node] = src_node
        else:
            data_connections.append((src_node, src_port, tgt_node, tgt_port))

    # Find start nodes (no incoming exec)
    all_targets = set(exec_connections.keys())
    start_nodes = [nid for nid in nodes.keys() if nid not in all_targets]

    # Order nodes by execution flow
    ordered = []
    visited = set()

    def visit(node_id):
        if node_id in visited or node_id not in nodes:
            return
        visited.add(node_id)
        ordered.append(node_id)
        # Find next nodes
        for conn in connections:
            if (
                conn.get("source_node") == node_id
                and "exec" in conn.get("source_port", "").lower()
            ):
                visit(conn.get("target_node", ""))

    for start in start_nodes:
        visit(start)

    # Add any remaining nodes
    for nid in nodes:
        if nid not in visited:
            ordered.append(nid)

    # Print header
    print()
    print("┌" + "─" * 78 + "┐")
    print("│ ROBUST WORKFLOW EXECUTION FLOW" + " " * 46 + "│")
    print("└" + "─" * 78 + "┘")
    print()

    # Print nodes in order
    for i, node_id in enumerate(ordered):
        node_data = nodes[node_id]
        node_type = node_data.get("node_type", "Unknown")
        config = node_data.get("config", {})

        # Node box
        box_width = 70
        type_line = f"  [{node_type}]"
        id_line = f"  ID: {node_id}"

        print("    ┌" + "─" * box_width + "┐")
        print(f"    │{type_line:<{box_width}}│")
        print(f"    │{id_line:<{box_width}}│")

        # Show key config
        for key, val in list(config.items())[:3]:
            if val:
                val_str = str(val)[:50]
                config_line = f"    {key}: {val_str}"
                print(f"    │{config_line:<{box_width}}│")

        print("    └" + "─" * box_width + "┘")

        # Connection arrow
        if i < len(ordered) - 1:
            print("           │")
            print("           ▼")

    # Print data connections
    if data_connections:
        print()
        print("    DATA CONNECTIONS:")
        print("    " + "─" * 40)
        for src_node, src_port, tgt_node, tgt_port in data_connections:
            print(f"    {src_node}.{src_port} ──→ {tgt_node}.{tgt_port}")

    print()


if __name__ == "__main__":
    asyncio.run(main())
