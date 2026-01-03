import os
import sys
from unittest.mock import AsyncMock

# Force headless mode before Qt imports.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import asyncio

import pytest
from PySide6.QtWidgets import QApplication

from casare_rpa.presentation.canvas.app import CasareRPAApp


class HeadlessTestApp(CasareRPAApp):
    def _setup_qt_application(self):
        self._app = QApplication.instance()
        if not self._app:
            self._app = QApplication(sys.argv)

        try:
            from qasync import QEventLoop

            self._loop = QEventLoop(self._app)
            asyncio.set_event_loop(self._loop)
        except Exception as exc:
            print(f"Warning setting up loop: {exc}")


@pytest.fixture
def headless_app(qapp):
    os.environ.setdefault("ORCHESTRATOR_URL", "http://localhost:8000")
    try:
        app = HeadlessTestApp()
        yield app
    finally:
        pass


@pytest.mark.asyncio
async def test_workflow_submission_from_ui(headless_app, qtbot, monkeypatch):
    window = headless_app._main_window
    qtbot.addWidget(window)

    robot_controller = window._robot_controller

    robot_controller._selected_robot_id = "test-robot-id"
    monkeypatch.setattr(
        robot_controller,
        "_get_workflow_data",
        lambda: {
            "metadata": {"name": "TestWorkflow", "version": "1.0.0"},
            "nodes": {},
            "connections": [],
            "variables": {},
            "settings": {},
            "frames": [],
        },
    )
    monkeypatch.setattr(robot_controller, "_get_workflow_variables", lambda: {})

    robot_controller.submit_job = AsyncMock(return_value="test-job-id")

    await robot_controller._submit_current_workflow()

    robot_controller.submit_job.assert_awaited_once()
