import asyncio
import json
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase


async def run_node_tests():
    input_dir = Path("workflows/node_tests")
    output_file = Path("scripts/node_test_results.json")

    workflow_files = sorted(list(input_dir.glob("batch_*.json")))

    # Optional: Filter by command line args
    if len(sys.argv) > 1:
        target_batches = sys.argv[1:]
        workflow_files = [
            f for f in workflow_files if f.name in target_batches or f.stem in target_batches
        ]
        print(f"Filtering to batches: {[f.name for f in workflow_files]}")

    results = []

    for wf_path in workflow_files:
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Executing: {wf_path.name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Load workflow schema from dict
            workflow = load_workflow_from_dict(workflow_data)

            # Create use case with loaded workflow
            uc = ExecuteWorkflowUseCase(workflow=workflow)
            success = await uc.execute()

            outputs = {}
            logs = []

            if success:
                # Get node outputs from context state
                if uc.context and hasattr(uc.context, "state"):
                    state = uc.context.state
                    for node_id in state.executed_nodes:
                        node_outputs = state.get_node_outputs(node_id)
                        if node_outputs:
                            # Clean non-serializable outputs
                            serializable_outputs = {}
                            for port_name, val in node_outputs.items():
                                if val is not None:
                                    try:
                                        json.dumps(val)
                                        serializable_outputs[port_name] = val
                                    except TypeError:
                                        serializable_outputs[port_name] = (
                                            f"<{type(val).__name__} object>"
                                        )
                            if serializable_outputs:
                                outputs[node_id] = serializable_outputs
                                if "message" in serializable_outputs:
                                    logs.append(f"[{node_id}] {serializable_outputs['message']}")
                                elif "value" in serializable_outputs:
                                    logs.append(
                                        f"[{node_id}] VALUE: {serializable_outputs['value']}"
                                    )

            res_entry = {
                "file": wf_path.name,
                "status": "SUCCESS" if success else "FAILED",
                "error": None if success else "Workflow failed",
                "logs": logs,
                "node_outputs": outputs,
            }
            results.append(res_entry)

            status_color = Fore.GREEN if success else Fore.RED
            print(
                f"{status_color}Result: {res_entry['status']}{' - ' + str(res_entry['error']) if res_entry['error'] else ''}{Style.RESET_ALL}"
            )

        except Exception as e:
            results.append(
                {
                    "file": wf_path.name,
                    "status": "FAILED",
                    "error": str(e),
                    "logs": [],
                    "node_outputs": {},
                }
            )
            print(f"{Fore.RED}Result: FAILED - {e}{Style.RESET_ALL}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nNode tests complete. Results saved to {output_file}")

    # Summary
    success = sum(1 for r in results if r["status"] == "SUCCESS")
    failed = sum(1 for r in results if r["status"] == "FAILED")
    print(
        f"\n{Fore.GREEN}SUCCESS: {success}{Style.RESET_ALL} | {Fore.RED}FAILED: {failed}{Style.RESET_ALL}"
    )

    return results


if __name__ == "__main__":
    asyncio.run(run_node_tests())
