"""
Execute test workflows and compare node outputs.

Runs each workflow JSON through ExecuteWorkflowUseCase and logs outputs.
"""

import asyncio

# Fix Windows console encoding
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from dotenv import load_dotenv

load_dotenv()


async def execute_workflow(workflow_path: Path) -> dict:
    """Execute a workflow and return results."""
    from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase
    from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

    # Load workflow data
    with open(workflow_path, encoding="utf-8") as f:
        workflow_data = json.load(f)

    # Load into WorkflowSchema
    workflow_schema = load_workflow_from_dict(workflow_data)

    # Create executor
    executor = ExecuteWorkflowUseCase(
        workflow=workflow_schema,
        initial_variables=workflow_data.get("variables", {}),
    )

    # Execute
    try:
        # Use execute() which returns bool, or handle execute_safe()
        success = await executor.execute()

        # Collect outputs from executed nodes
        outputs = {}
        for node_id in executor.executed_nodes:
            # UnWrap result from get_node_instance_safe
            node_result = executor.get_node_instance_safe(node_id)
            if node_result.is_ok():
                node = node_result.unwrap()
                node_outputs = {}
                if hasattr(node, "output_ports"):
                    for port_name in node.output_ports:
                        if not port_name.startswith("exec"):
                            val = node.get_output_value(port_name)
                            if val is not None:
                                node_outputs[port_name] = val

                if node_outputs:
                    outputs[node_id] = {"type": node.node_type, "outputs": node_outputs}

        return {
            "success": success,
            "executed_nodes": list(executor.executed_nodes),
            "outputs": outputs,
            "error": executor.state_manager.execution_error if not success else None,
        }
    except Exception as e:
        import traceback

        return {
            "success": False,
            "executed_nodes": list(executor.executed_nodes) if executor.executed_nodes else [],
            "outputs": {},
            "error": f"{str(e)}\n{traceback.format_exc()}",
        }


async def main():
    """Run all test workflows."""
    workflows_dir = Path(__file__).parent.parent / "workflows"
    test_files = [
        ("test_calculator.json", "Calculator: a=10 + b=5 = 15"),
        ("test_conditional.json", "Conditional: score=75 >= 60 → Pass"),
        ("test_loop.json", "Loop: 1, 2, 3, 4, 5"),
    ]

    # Note: Skipping browser workflows as they need a real browser
    print("=" * 70)
    print("📋 Workflow Execution Report")
    print("=" * 70)

    for filename, expected in test_files:
        filepath = workflows_dir / filename
        if not filepath.exists():
            print(f"\n❌ {filename}: FILE NOT FOUND")
            continue

        print(f"\n📄 {filename}")
        print(f"   Expected: {expected}")

        result = await execute_workflow(filepath)

        if result["success"]:
            print("   ✅ SUCCESS")
            print(f"   Executed: {len(result['executed_nodes'])} nodes")

            # Show key outputs
            for node_id, data in result["outputs"].items():
                if data["outputs"]:
                    print(f"   📤 {node_id} ({data['type']}): {data['outputs']}")
        else:
            print(f"   ❌ FAILED: {result['error']}")
            if result["executed_nodes"]:
                print(f"   Partial execution: {result['executed_nodes']}")

    print("\n" + "=" * 70)
    print("📊 Note: Browser workflows (test_web_extract.json, test_file_check.json)")
    print("   require actual file system / browser - skipped in headless mode")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
