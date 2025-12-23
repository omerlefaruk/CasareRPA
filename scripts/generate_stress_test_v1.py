import asyncio
import json
import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from casare_rpa.domain.ai.config import SIMPLE_FAST_CONFIG
from casare_rpa.infrastructure.ai import SmartWorkflowAgent

IDEAS = [
    "Create a list of 5 numbers [1, 2, 3, 4, 5], loop through them using ForLoopStartNode, and calculate the total sum in a variable 'total_sum'. Finally log the total.",
    "Set a variable 'name' to 'Alice' and 'age' to 30. Use FormatStringNode with template 'Hello, my name is {name} and I am {age} years old' and log the result.",
    "Calculate (10 * 2) + (50 / 2) - 5 using only MathOperationNodes. Log the final result.",
    "Check if file 'stress_test_file.txt' exists using FileSystemSuperNode. If it exists, delete it using FileSystemSuperNode. Otherwise, log 'File does not exist'.",
    'Parse the JSON string \'{"user": {"id": 123, "settings": {"theme": "dark"}}}\' using JsonParseNode. Extract the \'theme\' property and log it.',
    "Loop through a list of numbers [10, 25, 5, 40]. For each number, use a ComparisonNode to check if it is greater than 20. If true, use LogNode to log the number.",
    "Write the string 'CasareRPA is powerful' to a file named 'power_test.txt'. Then read it back and log the content length.",
    "Use a WhileLoopStartNode to count from 0 to 3. Start with a variable 'counter' = 0. In each iteration, increment 'counter' and log its value.",
    "Create a dictionary using CreateDictNode with keys 'status' and 'code' set to 'ok' and 200 respectively. Log the resulting dictionary object.",
    "Set variable 'VarA' to 10. Set 'VarB' to the value of 'VarA' using SetVariableNode. Add 5 to 'VarB' using MathOperationNode and log the final value.",
]


async def generate_workflows():
    # Load model from settings.json
    settings_path = Path(__file__).parent.parent / "config" / "settings.json"
    with open(settings_path) as f:  # noqa: ASYNC230
        settings = json.load(f)
    model = settings.get("ai", {}).get("model", "openrouter/google/gemini-2.0-flash-exp")
    print(f"Using model: {model}")

    agent = SmartWorkflowAgent(config=SIMPLE_FAST_CONFIG)
    output_dir = Path("workflows/stress_test_v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for i, idea in enumerate(IDEAS):
        print(f"Generating workflow {i+1}/10: {idea[:50]}...")
        try:
            result = await agent.generate_workflow(user_prompt=idea, model=model)

            if result.success and result.workflow:
                filename = f"task_{i+1}.json"
                file_path = output_dir / filename
                with open(file_path, "w", encoding="utf-8") as f:  # noqa: ASYNC230
                    json.dump(result.workflow, f, indent=2)
                results.append({"id": i + 1, "status": "SUCCESS", "file": str(file_path)})
                print(f"  Saved to {filename}")
            else:
                results.append({"id": i + 1, "status": "FAILED", "error": result.error})
                print(f"  Failed: {result.error}")
        except Exception as e:
            results.append({"id": i + 1, "status": "ERROR", "error": str(e)})
            print(f"  Error: {e}")

    with open("scripts/stress_test_gen_v1.json", "w") as f:  # noqa: ASYNC230
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    asyncio.run(generate_workflows())
