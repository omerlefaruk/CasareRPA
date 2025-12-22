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

    workflows_dir = Path(__file__).parent.parent / "workflows"
    test_files = [
        "test_calculator.json",
        "test_file_check.json",
        "test_web_extract.json",
        "test_conditional.json",
        "test_loop.json",
    ]

    sandbox = HeadlessWorkflowSandbox()

    print("=" * 60)
    print("📋 Workflow Validation Report")
    print("=" * 60)

    results = []

    for filename in test_files:
        filepath = workflows_dir / filename
        if not filepath.exists():
            print(f"\n❌ {filename}: FILE NOT FOUND")
            results.append({"file": filename, "status": "NOT_FOUND"})
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            workflow = json.load(f)

        print(f"\n📄 {filename}")
        print(f"   Name: {workflow.get('metadata', {}).get('name', 'Unknown')}")
        print(f"   Nodes: {len(workflow.get('nodes', {}))}")
        print(f"   Connections: {len(workflow.get('connections', []))}")

        # Run validation
        result = sandbox.validate_workflow(workflow)

        if result.is_valid:
            print("   ✅ VALID")
            results.append({"file": filename, "status": "VALID"})
        else:
            print(f"   ❌ INVALID - {len(result.errors)} errors:")
            for error in result.errors:
                print(f"      - [{error.code}] {error.message}")
                if error.suggestion:
                    print(f"        💡 {error.suggestion}")
            results.append(
                {
                    "file": filename,
                    "status": "INVALID",
                    "errors": [e.to_dict() for e in result.errors],
                }
            )

    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)

    valid_count = sum(1 for r in results if r["status"] == "VALID")
    invalid_count = sum(1 for r in results if r["status"] == "INVALID")
    not_found_count = sum(1 for r in results if r["status"] == "NOT_FOUND")

    print(f"   ✅ Valid: {valid_count}")
    print(f"   ❌ Invalid: {invalid_count}")
    print(f"   ⚠️ Not Found: {not_found_count}")

    return results


if __name__ == "__main__":
    results = asyncio.run(validate_workflows())
