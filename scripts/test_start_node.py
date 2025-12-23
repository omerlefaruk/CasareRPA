import json
import sys
from pathlib import Path

# Add src to sys.path
cwd = Path.cwd()
sys.path.append(str(cwd / "src"))

from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict

with open("workflows/stress_test_v1/task_1.json") as f:
    data = json.load(f)

workflow = load_workflow_from_dict(data)
orchestrator = ExecutionOrchestrator(workflow)
start_id = orchestrator.find_start_node()
print(f"Start ID: {start_id}")
