import asyncio
import os
import json
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import necessary modules
from casare_rpa.utils.workflow.workflow_loader import load_workflow_from_dict
from casare_rpa.application.use_cases.execute_workflow import (
    ExecuteWorkflowUseCase,
    ExecutionSettings,
)
from casare_rpa.domain.events.bus import get_event_bus


async def run_internal_workflow(workflow_path: str):
    # Load workflow data
    with open(workflow_path, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)

    # Load workflow schema
    workflow = load_workflow_from_dict(workflow_data)

    # Execution settings
    settings = ExecutionSettings(
        target_node_id=None,
        continue_on_error=True,
        node_timeout=300,
    )

    # Initialize variables
    variables = workflow_data.get("variables", {})
    initial_vars = {}
    for var_name, var_data in variables.items():
        if isinstance(var_data, dict):
            initial_vars[var_name] = var_data.get("default_value", var_data.get("value"))
        else:
            initial_vars[var_name] = var_data

    # Create event bus
    event_bus = get_event_bus()

    # Create use case
    use_case = ExecuteWorkflowUseCase(
        workflow=workflow, event_bus=event_bus, settings=settings, initial_variables=initial_vars
    )

    logger.add("logs/execution_debug_internal.log", rotation="1 day")
    logger.info(f"🚀 Starting internal execution of {workflow_path}")
    await use_case.execute()
    logger.info("✅ Execution finished")
    if use_case.context:
        import pprint

        logger.info("FINAL VARIABLES:")
        pprint.pprint(use_case.context.variables)
    else:
        logger.warning("Context was not initialized")

    if use_case.state_manager.execution_error:
        logger.error(f"❌ Execution Error: {use_case.state_manager.execution_error}")


if __name__ == "__main__":
    workflow_file = "Projects/MonthlyMuhasebe/scenarios/ck_bogazici_login_updated.json"
    asyncio.run(run_internal_workflow(workflow_file))
