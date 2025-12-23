"""Test the workflow generation."""

import asyncio

from dotenv import load_dotenv

# Load environment BEFORE importing casare_rpa
load_dotenv()


async def test():
    from casare_rpa.domain.ai import SIMPLE_FAST_CONFIG
    from casare_rpa.infrastructure.ai import SmartWorkflowAgent

    print("Creating agent...")
    agent = SmartWorkflowAgent(config=SIMPLE_FAST_CONFIG)
    print("Agent created")

    prompt = "Create a simple workflow that prints hello world using a LogNode"
    print(f"Generating workflow for: {prompt}")

    try:
        result = await agent.generate_workflow(prompt)
        print(f"Success: {result.success}")
        if result.success:
            import json

            print(f"Nodes: {len(result.workflow.get('nodes', {}))}")
            print(json.dumps(result.workflow, indent=2))
        else:
            print(f"Error: {result.error}")
            if result.validation_history:
                for v in result.validation_history:
                    print(f"  - Validation errors: {[e.message for e in v.errors]}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test())
