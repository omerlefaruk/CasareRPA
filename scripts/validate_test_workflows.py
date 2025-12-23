"""
Validate all 5 test workflows using HeadlessWorkflowSandbox.

This script loads each workflow JSON and runs Qt-based validation.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


async def validate_workflows():
    """Validate all test workflows."""
    from casare_rpa.infrastructure.ai.agent.sandbox import HeadlessWorkflowSandbox

    workflows_dir = Path(__file__).parent.parent / "workflows" / "node_tests"
    test_files = [
        "batch_1_1_variables.json",
        "batch_1_4_math.json",
        "batch_1_5_control_flow.json",
        "batch_2_1_files.json",
        "batch_3_1_browser_core.json",
    ]

    sandbox = HeadlessWorkflowSandbox()

    print("=" * 60)
    print("Workflow Validation Report")
    print("=" * 60)

    results = []

    for filename in test_files:
        filepath = workflows_dir / filename
        if not filepath.exists():
            print(f"\n[NOT FOUND] {filename}")
            results.append({"file": filename, "status": "NOT_FOUND"})
            continue

        with open(filepath, encoding="utf-8") as f:  # noqa: ASYNC230
            workflow = json.load(f)

        print(f"\nFILE: {filename}")
        print(f"   Name: {workflow.get('metadata', {}).get('name', 'Unknown')}")
        print(f"   Nodes: {len(workflow.get('nodes', {}))}")
        print(f"   Connections: {len(workflow.get('connections', []))}")

        # Run validation
        result = sandbox.validate_workflow(workflow)

        if result.is_valid:
            print("   Status: VALID")
            results.append({"file": filename, "status": "VALID"})
        else:
            print(f"   Status: INVALID - {len(result.errors)} errors:")
            for error in result.errors:
                print(f"      - [{error.code}] {error.message}")
                if error.suggestion:
                    print(f"        Suggestion: {error.suggestion}")
            results.append(
                {
                    "file": filename,
                    "status": "INVALID",
                    "errors": [e.to_dict() for e in result.errors],
                }
            )

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    valid_count = sum(1 for r in results if r["status"] == "VALID")
    invalid_count = sum(1 for r in results if r["status"] == "INVALID")
    not_found_count = sum(1 for r in results if r["status"] == "NOT_FOUND")

    print(f"   Valid: {valid_count}")
    print(f"   Invalid: {invalid_count}")
    print(f"   Not Found: {not_found_count}")

    return results


if __name__ == "__main__":
    results = asyncio.run(validate_workflows())
    if any(r["status"] != "VALID" for r in results):
        sys.exit(1)
    sys.exit(0)
