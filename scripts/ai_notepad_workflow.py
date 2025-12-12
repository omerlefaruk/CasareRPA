"""
AI-Generated Notepad Automation Workflow

Uses SmartWorkflowAgent to generate a simple Notepad automation workflow.
Demonstrates node lookups using node indexes from registry_data.py.

Node Registry References (from registry_data.py):
    Line 471: "LaunchApplicationNode": "desktop_nodes"
    Line 472: "CloseApplicationNode": "desktop_nodes"
    Line 499: "SendKeysNode": "desktop_nodes"
    Line 500: "SendHotKeyNode": "desktop_nodes"
    Line 46:  "WaitNode": "wait_nodes"
"""

import asyncio
import json
from pathlib import Path

from casare_rpa.infrastructure.ai.agent import (
    SmartWorkflowAgent,
    generate_smart_workflow,
)
from casare_rpa.domain.ai import SIMPLE_FAST_CONFIG


async def generate_notepad_workflow_with_agent():
    """Generate a Notepad automation workflow using SmartWorkflowAgent."""

    # Create the agent with simple/fast configuration
    agent = SmartWorkflowAgent(config=SIMPLE_FAST_CONFIG)

    # Natural language prompt describing the workflow
    prompt = """
    Create a simple Notepad automation workflow that:
    1. Launches Notepad application (notepad.exe)
    2. Waits 1 second for the application to load
    3. Types "Hello from CasareRPA AI!" into the editor
    4. Waits 500ms
    5. Types a new line with today's date placeholder

    Use these specific nodes:
    - LaunchApplicationNode (registry line 471) for launching notepad.exe
    - WaitNode (registry line 46) for delays
    - SendKeysNode (registry line 499) for typing text

    Do NOT include StartNode or EndNode - they are added automatically.
    """

    print("=" * 60)
    print("Generating Notepad Automation Workflow with AI...")
    print("=" * 60)
    print(f"\nPrompt:\n{prompt.strip()}\n")
    print("-" * 60)

    # Generate the workflow
    result = await agent.generate_workflow(user_prompt=prompt)

    if result.success:
        print(f"\n[SUCCESS] Workflow generated in {result.attempts} attempt(s)")
        print(f"Generation time: {result.generation_time_ms:.2f}ms")

        # Pretty print the workflow
        print("\nGenerated Workflow JSON:")
        print("-" * 60)
        print(json.dumps(result.workflow, indent=2))

        # Save the workflow
        output_path = (
            Path(__file__).parent.parent / "templates" / "ai_notepad_automation.json"
        )
        output_path.parent.mkdir(exist_ok=True)
        output_path.write_text(json.dumps(result.workflow, indent=2))
        print(f"\nWorkflow saved to: {output_path}")

        # Print node summary
        nodes = result.workflow.get("nodes", {})
        print(f"\nGenerated {len(nodes)} nodes:")
        for node_id, node_data in nodes.items():
            node_type = node_data.get("node_type", "Unknown")
            print(f"  - {node_id}: {node_type}")

        return result.workflow
    else:
        print(f"\n[FAILED] Workflow generation failed after {result.attempts} attempts")
        print(f"Error: {result.error}")

        # Print validation history for debugging
        if result.validation_history:
            print("\nValidation History:")
            for i, validation in enumerate(result.validation_history):
                if validation.errors:
                    print(f"  Attempt {i+1}: {len(validation.errors)} errors")
                    for err in validation.errors[:5]:
                        print(f"    - {err.code}: {err.message}")
        return None


async def generate_notepad_workflow_simple():
    """
    Generate a Notepad workflow using the convenience function.

    This is a simpler alternative using generate_smart_workflow().
    """

    prompt = """
    Create a workflow to automate Notepad:
    1. Launch notepad.exe using LaunchApplicationNode
    2. Wait 1000ms using WaitNode
    3. Type "Automated by CasareRPA" using SendKeysNode

    Connect nodes with exec_out -> exec_in connections.
    """

    print("\n" + "=" * 60)
    print("Using generate_smart_workflow() convenience function...")
    print("=" * 60)

    result = await generate_smart_workflow(
        prompt=prompt, max_retries=3, model="gpt-4o-mini"
    )

    if result.success:
        print(f"\n[SUCCESS] Generated in {result.generation_time_ms:.2f}ms")
        return result.workflow
    else:
        print(f"\n[FAILED] {result.error}")
        return None


def verify_nodes_in_registry():
    """
    Verify that the nodes we need exist in the registry.

    Node Registry Index References:
        - LaunchApplicationNode: registry_data.py:471
        - CloseApplicationNode: registry_data.py:472
        - SendKeysNode: registry_data.py:499
        - SendHotKeyNode: registry_data.py:500
        - WaitNode: registry_data.py:46
    """
    from casare_rpa.nodes.registry_data import NODE_REGISTRY

    required_nodes = [
        ("LaunchApplicationNode", 471),
        ("CloseApplicationNode", 472),
        ("SendKeysNode", 499),
        ("SendHotKeyNode", 500),
        ("WaitNode", 46),
    ]

    print("\nVerifying required nodes in registry:")
    print("-" * 40)

    all_found = True
    for node_name, line_num in required_nodes:
        if node_name in NODE_REGISTRY:
            module = NODE_REGISTRY[node_name]
            if isinstance(module, tuple):
                module = f"{module[0]} (alias: {module[1]})"
            print(f"  [OK] {node_name} -> {module} (line {line_num})")
        else:
            print(f"  [MISSING] {node_name} (expected at line {line_num})")
            all_found = False

    return all_found


def create_manual_workflow():
    """
    Create a Notepad workflow manually (without AI) for comparison.

    Uses the same nodes verified from registry_data.py:
        - LaunchApplicationNode (line 471)
        - WaitNode (line 46)
        - SendKeysNode (line 499)
    """

    workflow = {
        "metadata": {
            "name": "Manual Notepad Automation",
            "description": "Manually created workflow for Notepad automation",
            "version": "1.0.0",
            "tags": ["notepad", "desktop", "automation", "manual"],
        },
        "nodes": {
            "launch_notepad": {
                "node_id": "launch_notepad",
                "node_type": "LaunchApplicationNode",  # registry_data.py:471
                "config": {
                    "application_path": "notepad.exe",
                    "window_title_hint": "Notepad",
                    "timeout": 10.0,
                    "keep_open": True,
                },
                "position": [0, 0],
            },
            "wait_for_load": {
                "node_id": "wait_for_load",
                "node_type": "WaitNode",  # registry_data.py:46
                "config": {"duration_ms": 1000},
                "position": [400, 0],
            },
            "type_hello": {
                "node_id": "type_hello",
                "node_type": "SendKeysNode",  # registry_data.py:499
                "config": {"keys": "Hello from CasareRPA!", "interval": 0.02},
                "position": [800, 0],
            },
            "wait_brief": {
                "node_id": "wait_brief",
                "node_type": "WaitNode",  # registry_data.py:46
                "config": {"duration_ms": 500},
                "position": [1200, 0],
            },
            "type_signature": {
                "node_id": "type_signature",
                "node_type": "SendKeysNode",  # registry_data.py:499
                "config": {"keys": "\n-- Automated with AI --", "interval": 0.02},
                "position": [1600, 0],
            },
        },
        "connections": [
            {
                "source_node": "launch_notepad",
                "source_port": "exec_out",
                "target_node": "wait_for_load",
                "target_port": "exec_in",
            },
            {
                "source_node": "wait_for_load",
                "source_port": "exec_out",
                "target_node": "type_hello",
                "target_port": "exec_in",
            },
            {
                "source_node": "type_hello",
                "source_port": "exec_out",
                "target_node": "wait_brief",
                "target_port": "exec_in",
            },
            {
                "source_node": "wait_brief",
                "source_port": "exec_out",
                "target_node": "type_signature",
                "target_port": "exec_in",
            },
        ],
        "variables": {},
        "settings": {"stop_on_error": True, "timeout": 60, "retry_count": 0},
    }

    return workflow


async def main():
    """Main entry point."""

    print("\n" + "=" * 60)
    print("  CasareRPA - AI Notepad Workflow Generator")
    print("=" * 60)

    # Step 1: Verify nodes exist in registry
    if not verify_nodes_in_registry():
        print("\n[ERROR] Some required nodes are missing from registry!")
        return

    # Step 2: Create manual workflow for comparison
    print("\n" + "-" * 60)
    print("Creating manual workflow for comparison...")
    manual_workflow = create_manual_workflow()
    manual_path = (
        Path(__file__).parent.parent / "templates" / "manual_notepad_workflow.json"
    )
    manual_path.write_text(json.dumps(manual_workflow, indent=2))
    print(f"Manual workflow saved to: {manual_path}")

    # Step 3: Generate AI workflow
    try:
        ai_workflow = await generate_notepad_workflow_with_agent()

        if ai_workflow:
            print("\n" + "=" * 60)
            print("  Comparison Summary")
            print("=" * 60)
            print(f"  Manual workflow nodes: {len(manual_workflow['nodes'])}")
            print(f"  AI workflow nodes: {len(ai_workflow.get('nodes', {}))}")

    except Exception as e:
        print(f"\n[ERROR] AI generation failed: {e}")
        print("Manual workflow is still available for use.")


if __name__ == "__main__":
    asyncio.run(main())
