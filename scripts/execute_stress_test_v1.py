import asyncio
import json
import os
import sys
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
from casare_rpa.application.use_cases.execute_workflow import ExecuteWorkflowUseCase


async def run_stress_test():
    input_dir = Path("workflows/stress_test_v1")
    output_file = Path("scripts/stress_test_results_v1.json")

    workflow_files = sorted(
        list(input_dir.glob("task_*.json")), key=lambda p: int(p.stem.split("_")[1])
    )

    # Optional: Filter by command line args
    if len(sys.argv) > 1:
        target_tasks = sys.argv[1:]
        workflow_files = [
            f for f in workflow_files if f.name in target_tasks or f.stem in target_tasks
        ]
        print(f"Filtering to tasks: {[f.name for f in workflow_files]}")

    results = []

    for wf_path in workflow_files:
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Executing: {wf_path.name}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

        try:
            with open(wf_path, "r", encoding="utf-8") as f:
                workflow_data = json.load(f)

            # Load into WorkflowSchema
            workflow_schema = load_workflow_from_dict(workflow_data)

            # Create executor
            executor = ExecuteWorkflowUseCase(
                workflow=workflow_schema,
                initial_variables=workflow_data.get("variables", {}),
            )

            # Execute
            success = await executor.execute()
            status_str = "SUCCESS" if success else "FAILED"

            # Extract logs/outputs
            logs = []
            outputs = {}
            for node_id in executor.executed_nodes:
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
                        # Clean non-serializable outputs (like Page objects)
                        serializable_outputs = {}
                        for k, v in node_outputs.items():
                            try:
                                json.dumps(v)
                                serializable_outputs[k] = v
                            except TypeError:
                                serializable_outputs[k] = f"<{type(v).__name__} object>"

                        outputs[node_id] = serializable_outputs
                        if "message" in serializable_outputs:
                            logs.append(f"[{node_id}] {serializable_outputs['message']}")
                        elif "value" in serializable_outputs:
                            logs.append(f"[{node_id}] VALUE: {serializable_outputs['value']}")

            res_entry = {
                "file": wf_path.name,
                "status": status_str,
                "error": str(executor.state_manager.execution_error) if not success else None,
                "logs": logs,
                "node_outputs": outputs,
            }
            results.append(res_entry)

            if success:
                print(f"{Fore.GREEN}Result: SUCCESS{Style.RESET_ALL}")
            else:
                print(
                    f"{Fore.RED}Result: FAILED - {executor.state_manager.execution_error}{Style.RESET_ALL}"
                )

            for log in logs:
                print(f"  {log}")

        except Exception as e:
            import traceback

            print(f"{Fore.RED}Error executing {wf_path.name}: {e}{Style.RESET_ALL}")
            results.append(
                {
                    "file": wf_path.name,
                    "status": "ERROR",
                    "error": f"{str(e)}\n{traceback.format_exc()}",
                }
            )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n{Fore.YELLOW}Stress test complete. Results saved to {output_file}{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(run_stress_test())
