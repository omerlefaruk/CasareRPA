"""
Generate a Simple Notepad Workflow using CasareRPA AI Infrastructure.

This script demonstrates how to use the SmartWorkflowAgent to generate
a workflow from natural language descriptions.

Usage:
    python scripts/generate_notepad_workflow.py
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


async def generate_notepad_workflow():
    """Generate a simple Notepad workflow using AI."""
    from casare_rpa.domain.ai import SIMPLE_FAST_CONFIG
    from casare_rpa.infrastructure.ai import (
        SmartWorkflowAgent,
        WorkflowGenerationResult,
    )

    # Create the agent with simple/fast config for quick generation
    agent = SmartWorkflowAgent(config=SIMPLE_FAST_CONFIG)

    # Define the workflow request
    prompt = """
    Create a simple Notepad automation workflow that:
    1. Launches Windows Notepad application
    2. Waits 1 second for the window to appear
    3. Types a simple greeting message: "Hello from CasareRPA!"
    4. Types a new line with the current date/time placeholder
    5. Closes the application (keeping the unsaved dialog for user to handle)

    Use these specific nodes:
    - LaunchApplicationNode: application_path="notepad.exe"
    - WaitNode: for delays
    - SendKeysNode: for typing text
    - CloseApplicationNode: to close at the end
    """

    print("=" * 60)
    print("Generating Notepad Workflow with AI")
    print("=" * 60)
    print(f"\nPrompt:\n{prompt}\n")
    print("=" * 60)

    try:
        # Generate the workflow
        result: WorkflowGenerationResult = await agent.generate(prompt)

        if result.success:
            print("\n✅ Workflow generated successfully!")
            print(f"   Attempts: {result.attempts}")
            print(f"   Generation time: {result.generation_time_ms:.2f}ms")

            # Pretty print the workflow
            workflow_json = json.dumps(result.workflow, indent=2)
            print("\n📋 Generated Workflow JSON:")
            print("-" * 40)
            print(workflow_json)

            # Save to file
            output_path = Path(__file__).parent.parent / "workflows" / "ai_notepad_workflow.json"
            output_path.parent.mkdir(exist_ok=True)
            with open(output_path, "w") as f:  # noqa: ASYNC230
                json.dump(result.workflow, f, indent=2)
            print(f"\n💾 Saved to: {output_path}")

            return result.workflow
        else:
            print(f"\n❌ Generation failed: {result.error}")
            print(f"   Attempts: {result.attempts}")

            if result.validation_history:
                print("\n📝 Validation History:")
                for i, validation in enumerate(result.validation_history):
                    print(f"   Attempt {i+1}: {len(validation.errors)} errors")
                    for error in validation.errors[:3]:  # Show first 3 errors
                        print(f"      - {error.message}")

            return None

    except Exception as e:
        print(f"\n❌ Error during generation: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Run the workflow generation."""
    print("\n🚀 Starting AI Workflow Generator")
    print("   Using: SmartWorkflowAgent from infrastructure/ai")
    print("   Config: SIMPLE_FAST_CONFIG\n")

    result = asyncio.run(generate_notepad_workflow())

    if result:
        print("\n✅ Done! You can load this workflow in the CasareRPA canvas.")
    else:
        print("\n⚠️ Workflow generation was not successful.")
        print("   Make sure you have LLM API credentials configured in .env")


if __name__ == "__main__":
    main()
