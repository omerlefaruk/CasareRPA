"""
Pytest configuration and shared fixtures for CasareRPA tests.
"""

import sys
import asyncio
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, AsyncMock

import pytest

# Add src to python path
src_path = str(Path(__file__).parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)


# ============================================================================
# ASYNC FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# EXECUTION CONTEXT FIXTURES
# ============================================================================

@pytest.fixture
def execution_context():
    """Create a fresh ExecutionContext for each test."""
    from casare_rpa.core.execution_context import ExecutionContext
    return ExecutionContext()


@pytest.fixture
def context_with_variables():
    """Create an ExecutionContext with some pre-set variables."""
    from casare_rpa.core.execution_context import ExecutionContext

    ctx = ExecutionContext()
    ctx.set_variable("test_string", "hello")
    ctx.set_variable("test_number", 42)
    ctx.set_variable("test_list", [1, 2, 3])
    ctx.set_variable("test_dict", {"key": "value"})
    return ctx


# ============================================================================
# NODE FIXTURES
# ============================================================================

@pytest.fixture
def start_node():
    """Create a StartNode instance."""
    from casare_rpa.nodes.basic_nodes import StartNode
    return StartNode("test_start")


@pytest.fixture
def end_node():
    """Create an EndNode instance."""
    from casare_rpa.nodes.basic_nodes import EndNode
    return EndNode("test_end")


@pytest.fixture
def set_variable_node():
    """Create a SetVariableNode instance."""
    from casare_rpa.nodes.variable_nodes import SetVariableNode
    return SetVariableNode("test_set_var", config={
        "variable_name": "test_var",
        "value": "test_value"
    })


@pytest.fixture
def if_node():
    """Create an IfNode instance."""
    from casare_rpa.nodes.control_flow_nodes import IfNode
    return IfNode("test_if", config={"condition": "True"})


@pytest.fixture
def for_loop_node():
    """Create a ForLoopNode instance."""
    from casare_rpa.nodes.control_flow_nodes import ForLoopNode
    return ForLoopNode("test_for", config={
        "start": 0,
        "end": 3,
        "step": 1
    })


# ============================================================================
# WORKFLOW FIXTURES
# ============================================================================

@pytest.fixture
def empty_workflow():
    """Create an empty workflow."""
    from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata
    return WorkflowSchema(WorkflowMetadata(name="Test Workflow"))


@pytest.fixture
def simple_workflow():
    """Create a simple Start -> End workflow."""
    from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
    from casare_rpa.nodes.basic_nodes import StartNode, EndNode

    workflow = WorkflowSchema(WorkflowMetadata(name="Simple Test"))
    workflow.nodes = {
        "start": StartNode("start"),
        "end": EndNode("end")
    }
    workflow.connections = [
        NodeConnection("start", "exec_out", "end", "exec_in")
    ]
    return workflow


@pytest.fixture
def variable_workflow():
    """Create a workflow with variable operations."""
    from casare_rpa.core.workflow_schema import WorkflowSchema, WorkflowMetadata, NodeConnection
    from casare_rpa.nodes.basic_nodes import StartNode, EndNode
    from casare_rpa.nodes.variable_nodes import SetVariableNode

    workflow = WorkflowSchema(WorkflowMetadata(name="Variable Test"))
    workflow.nodes = {
        "start": StartNode("start"),
        "set_x": SetVariableNode("set_x", config={"variable_name": "x", "value": "10"}),
        "set_y": SetVariableNode("set_y", config={"variable_name": "y", "value": "20"}),
        "end": EndNode("end")
    }
    workflow.connections = [
        NodeConnection("start", "exec_out", "set_x", "exec_in"),
        NodeConnection("set_x", "exec_out", "set_y", "exec_in"),
        NodeConnection("set_y", "exec_out", "end", "exec_in"),
    ]
    return workflow


# ============================================================================
# WORKFLOW RUNNER FIXTURES
# ============================================================================

@pytest.fixture
def workflow_runner(simple_workflow, execution_context):
    """Create a WorkflowRunner with a simple workflow."""
    from casare_rpa.runner.workflow_runner import WorkflowRunner
    return WorkflowRunner(simple_workflow, execution_context)


# ============================================================================
# MOCK FIXTURES FOR BROWSER/PLAYWRIGHT
# ============================================================================

@pytest.fixture
def mock_browser():
    """Create a mock browser object."""
    browser = MagicMock()
    browser.close = AsyncMock()
    browser.new_page = AsyncMock()
    return browser


@pytest.fixture
def mock_page():
    """Create a mock page object."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.type = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.content = AsyncMock(return_value="<html></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.url = "https://example.com"
    page.close = AsyncMock()
    return page


@pytest.fixture
def mock_playwright():
    """Create a mock Playwright instance."""
    playwright = MagicMock()
    playwright.chromium = MagicMock()
    playwright.chromium.launch = AsyncMock()
    playwright.firefox = MagicMock()
    playwright.firefox.launch = AsyncMock()
    playwright.webkit = MagicMock()
    playwright.webkit.launch = AsyncMock()
    return playwright


# ============================================================================
# MOCK FIXTURES FOR DESKTOP AUTOMATION
# ============================================================================

@pytest.fixture
def mock_desktop_element():
    """Create a mock DesktopElement."""
    element = MagicMock()
    element.get_text.return_value = "Test Text"
    element.get_property.return_value = "ButtonControl"
    element.is_enabled.return_value = True
    element.is_visible.return_value = True
    element.click.return_value = None
    element.type_text.return_value = None
    element.find_element.return_value = None
    element.find_elements.return_value = []
    return element


@pytest.fixture
def mock_desktop_context():
    """Create a mock DesktopContext."""
    context = MagicMock()
    context.find_window.return_value = MagicMock()
    context.launch_application.return_value = MagicMock()
    context.get_active_window.return_value = MagicMock()
    return context


# ============================================================================
# RECORDING FIXTURES
# ============================================================================

@pytest.fixture
def recording_session():
    """Create a RecordingSession."""
    from casare_rpa.recorder.recording_session import RecordingSession
    return RecordingSession()


@pytest.fixture
def recorded_actions():
    """Create a list of sample recorded actions."""
    from casare_rpa.recorder.recording_session import RecordedAction, ActionType

    return [
        RecordedAction(ActionType.NAVIGATE, "", url="https://example.com"),
        RecordedAction(ActionType.CLICK, "#submit-button"),
        RecordedAction(ActionType.TYPE, "#username", value="testuser"),
        RecordedAction(ActionType.SELECT, "#country", value="US"),
    ]


@pytest.fixture
def workflow_generator():
    """Create a WorkflowGenerator."""
    from casare_rpa.recorder.workflow_generator import WorkflowGenerator
    return WorkflowGenerator()


# ============================================================================
# HOTKEY FIXTURES
# ============================================================================

@pytest.fixture
def temp_hotkeys_file(tmp_path):
    """Create a temporary file path for hotkey settings."""
    return tmp_path / "test_hotkeys.json"


@pytest.fixture
def hotkey_settings(temp_hotkeys_file):
    """Create a HotkeySettings instance with temp file."""
    from casare_rpa.utils.hotkey_settings import HotkeySettings
    return HotkeySettings(temp_hotkeys_file)


# ============================================================================
# EVENT FIXTURES
# ============================================================================

@pytest.fixture
def event_recorder():
    """Create an EventRecorder for capturing events during tests."""
    from casare_rpa.core.events import EventRecorder
    return EventRecorder()


# ============================================================================
# GUI MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_qapplication():
    """Mock QApplication for GUI tests."""
    with pytest.MonkeyPatch.context() as mp:
        mock_app = MagicMock()
        mp.setattr("PySide6.QtWidgets.QApplication", MagicMock(return_value=mock_app))
        yield mock_app


# ============================================================================
# PYTEST MARKERS
# ============================================================================

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "gui: mark test as requiring GUI (may be slow)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "browser: mark test as requiring browser automation"
    )
    config.addinivalue_line(
        "markers", "desktop: mark test as requiring desktop automation"
    )
