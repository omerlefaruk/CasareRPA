import os
import sys

# 1. Force Headless Mode before generic imports
os.environ["QT_QPA_PLATFORM"] = "offscreen"

import asyncio
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Import strictly what is needed
from casare_rpa.presentation.canvas.app import CasareRPAApp


# Mocking the app setup to avoid creating a second QApplication
class HeadlessTestApp(CasareRPAApp):
    def _setup_qt_application(self):
        # Use existing instance from pytest-qt
        self._app = QApplication.instance()
        if not self._app:
            # Fallback if pytest-qt didn't creating it yet? (Unlikely)
            self._app = QApplication(sys.argv)

        # We need a qasync loop for the app to function properly with async tasks
        try:
            from qasync import QEventLoop

            self._loop = QEventLoop(self._app)
            asyncio.set_event_loop(self._loop)
        except Exception as e:
            print(f"Warning setting up loop: {e}")


@pytest.fixture
def headless_app(qapp):
    """Fixture to create the app with proper mocking."""
    # Ensure env vars are set for orchestration
    os.environ["ORCHESTRATOR_URL"] = "http://localhost:8000"

    try:
        app = HeadlessTestApp()
        yield app
    finally:
        pass


@pytest.mark.asyncio
async def test_workflow_submission_from_ui(headless_app, qtbot):
    """
    Detailed E2E Test:
    1. Initialize Canvas UI (Headless).
    2. Create a 'Start' node and 'Log' node.
    3. Connect them.
    4. Trigger 'Run'.
    5. Verify Job Submission to Orchestrator.
    """
    # Wait for app init
    window = headless_app._main_window
    qtbot.addWidget(window)
    # window.show() # Can cause issues in pure offscreen if no screen exists, but harmless usually.

    # 1. Setup Graph
    print("🎨 Setting up Workflow Graph...")
    graph = headless_app._node_graph.graph

    # Verify Node Registry
    available_nodes = graph.node_factory.nodes.keys()
    print(f"ℹ️  Available Node Types: {len(available_nodes)}")

    # Uses CORRECT identifiers found in codebase
    start_node_id = "casare_rpa.nodes.basic_nodes.StartNode"
    log_node_id = "casare_rpa.nodes.utility_nodes.LogNode"

    # Verify existence
    if start_node_id not in available_nodes:
        # Fallback search
        print(f"⚠️  {start_node_id} not found. Searching aliases...")
        for n in available_nodes:
            if "StartNode" in n:
                print(f"   -> Found potential match: {n}")
                start_node_id = n
                break

    if log_node_id not in available_nodes:
        for n in available_nodes:
            if "LogNode" in n:
                log_node_id = n
                break

    # Create Nodes
    try:
        start_node = graph.create_node(start_node_id, pos=[0, 0])
        log_node = graph.create_node(log_node_id, pos=[300, 0])
    except Exception as e:
        pytest.fail(f"Failed to create nodes: {e}")

    assert start_node, "Start Node failed to create"
    assert log_node, "Log Node failed to create"

    # Set Properties
    # StartNode usually has no properties
    if hasattr(log_node, "set_property"):
        log_node.set_property("message", "Hello from Headless QT!")

    # Connect
    # StartNode: exec_out (usually index 0) -> LogNode: exec_in (usually index 0)
    try:
        start_node.set_output(0, log_node.input(0))
        print("🔗 Nodes Connected.")
    except Exception as e:
        pytest.fail(f"Connection failed: {e}")

    # 2. Trigger Run
    print("▶️ Triggering Workflow Run...")

    # Spy on submit_job
    robot_controller = headless_app._execution_controller._robot_controller
    real_submit = robot_controller.submit_job
    submission_result = {}

    async def spy_submit_job(*args, **kwargs):
        print("🕵️ Spy: submit_job called!")
        try:
            # We explicitly await the specific coroutine
            # Note: submit_job might verify auth inside.
            res = await real_submit(*args, **kwargs)
            submission_result["job_id"] = res
            print(f"✅ Spy: Job Submitted ID: {res}")
            return res
        except Exception as e:
            submission_result["error"] = str(e)
            print(f"❌ Spy: Submission Failed: {e}")
            raise e

    # Apply Spy
    robot_controller.submit_job = spy_submit_job

    # Trigger Run Signal
    window.workflow_run.emit()

    # 3. Wait for Async Execution
    # Wait up to 10 seconds
    print("⏳ Waiting for submission...")
    for i in range(100):
        if "job_id" in submission_result:
            print(f"   ✓ Job captured after {i*0.1}s")
            break
        if "error" in submission_result:
            print(f"   X Error captured after {i*0.1}s: {submission_result['error']}")
            break
        await asyncio.sleep(0.1)

    # 4. Assertions
    if "error" in submission_result:
        # Check if error is "Authentication" - verify system state
        if "Authentication" in submission_result["error"]:
            print("⚠️  Authenticaion Error - Check .env or Server Status")
        elif "Connection" in submission_result["error"]:
            print("⚠️  Connection Error - Check Database Block")

        # Fail the test but output is useful
        pytest.fail(f"Job Submission Failed: {submission_result['error']}")

    assert "job_id" in submission_result, "Job ID not captured (Run timed out?)"
    job_id = submission_result["job_id"]
    print(f"🎉 TEST SUCCESS: Job {job_id} submitted via Canvas UI!")


if __name__ == "__main__":
    pass
