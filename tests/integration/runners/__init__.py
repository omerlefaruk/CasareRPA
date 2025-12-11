"""
CasareRPA - Integration Test Runners

Provides headless execution runners for testing workflows without GUI.

Components:
    - QtHeadlessRunner: Execute workflows in headless Qt mode
    - ExecutionReport: Results from workflow execution

Usage:
    from tests.integration.runners.test_headless_ui import (
        QtHeadlessRunner,
        ExecutionReport,
    )

    runner = QtHeadlessRunner()
    workflow = runner.load_workflow_from_dict(workflow_data)
    report = await runner.execute_workflow()
    assert report.success
"""

from tests.integration.runners.test_headless_ui import (
    QtHeadlessRunner,
    ExecutionReport,
    create_simple_workflow,
    create_log_workflow,
    create_variable_workflow,
    create_error_workflow,
    create_ai_generated_workflow,
    create_messagebox_workflow,
)

__all__ = [
    "QtHeadlessRunner",
    "ExecutionReport",
    "create_simple_workflow",
    "create_log_workflow",
    "create_variable_workflow",
    "create_error_workflow",
    "create_ai_generated_workflow",
    "create_messagebox_workflow",
]
