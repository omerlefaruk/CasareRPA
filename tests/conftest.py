"""
CasareRPA Test Configuration and Fixtures.

Provides pytest fixtures and helpers for testing all node types and GUI components.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configure Qt for testing (must be before PySide6 imports)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import DataType, ExecutionMode, NodeStatus, PortType


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def execution_context() -> ExecutionContext:
    """Create a fresh ExecutionContext for testing."""
    return ExecutionContext(workflow_name="TestWorkflow", mode=ExecutionMode.NORMAL)


@pytest.fixture
def debug_context() -> ExecutionContext:
    """Create an ExecutionContext in debug mode."""
    return ExecutionContext(workflow_name="DebugWorkflow", mode=ExecutionMode.DEBUG)


@pytest.fixture
def context_with_variables(execution_context: ExecutionContext) -> ExecutionContext:
    """ExecutionContext pre-populated with test variables."""
    execution_context.set_variable("test_string", "Hello World")
    execution_context.set_variable("test_number", 42)
    execution_context.set_variable("test_float", 3.14)
    execution_context.set_variable("test_bool", True)
    execution_context.set_variable("test_list", [1, 2, 3, 4, 5])
    execution_context.set_variable("test_dict", {"name": "Test", "value": 100})
    return execution_context


@pytest.fixture
def mock_browser():
    """Create a mock Playwright browser."""
    browser = MagicMock()
    browser.close = AsyncMock()
    return browser


@pytest.fixture
def mock_page():
    """Create a mock Playwright page with common methods."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.type = AsyncMock()
    page.wait_for_selector = AsyncMock()
    page.query_selector = AsyncMock()
    page.query_selector_all = AsyncMock(return_value=[])
    page.evaluate = AsyncMock()
    page.screenshot = AsyncMock()
    page.pdf = AsyncMock()
    page.content = AsyncMock(return_value="<html></html>")
    page.title = AsyncMock(return_value="Test Page")
    page.url = "https://example.com"
    page.close = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.keyboard = MagicMock()
    page.keyboard.press = AsyncMock()
    page.keyboard.type = AsyncMock()
    page.mouse = MagicMock()
    page.mouse.click = AsyncMock()
    page.mouse.move = AsyncMock()
    return page


@pytest.fixture
def mock_element():
    """Create a mock Playwright element."""
    element = MagicMock()
    element.click = AsyncMock()
    element.fill = AsyncMock()
    element.type = AsyncMock()
    element.text_content = AsyncMock(return_value="Element Text")
    element.inner_text = AsyncMock(return_value="Inner Text")
    element.inner_html = AsyncMock(return_value="<span>Inner HTML</span>")
    element.get_attribute = AsyncMock(return_value="attribute_value")
    element.is_visible = AsyncMock(return_value=True)
    element.is_enabled = AsyncMock(return_value=True)
    element.is_checked = AsyncMock(return_value=False)
    element.screenshot = AsyncMock()
    element.scroll_into_view_if_needed = AsyncMock()
    element.select_option = AsyncMock()
    element.check = AsyncMock()
    element.uncheck = AsyncMock()
    element.hover = AsyncMock()
    element.focus = AsyncMock()
    element.bounding_box = AsyncMock(return_value={"x": 100, "y": 100, "width": 50, "height": 30})
    return element


@pytest.fixture
def context_with_page(execution_context: ExecutionContext, mock_page) -> ExecutionContext:
    """ExecutionContext with a mock page set as active."""
    execution_context.set_active_page(mock_page)
    execution_context.add_page(mock_page, "main")
    return execution_context


@pytest.fixture
def context_with_browser(execution_context: ExecutionContext, mock_browser, mock_page) -> ExecutionContext:
    """ExecutionContext with mock browser and page."""
    execution_context.set_browser(mock_browser)
    execution_context.set_active_page(mock_page)
    execution_context.add_page(mock_page, "main")
    return execution_context


def create_node(node_class, node_id: str = "test_node", config: Optional[Dict[str, Any]] = None):
    """Helper function to create a node instance with optional config."""
    node = node_class(node_id=node_id, config=config or {})
    return node


def set_node_inputs(node, **kwargs):
    """Helper to set input port values on a node."""
    for port_name, value in kwargs.items():
        if port_name in node.input_ports:
            node.input_ports[port_name].set_value(value)
        else:
            # Try setting as property/config
            node.config[port_name] = value


def get_node_output(node, port_name: str) -> Any:
    """Helper to get output port value from a node."""
    if port_name in node.output_ports:
        return node.output_ports[port_name].get_value()
    return None


async def execute_node(node, context: ExecutionContext) -> Any:
    """Execute a node and return the result."""
    result = await node.execute(context)
    return result


class NodeTestHelper:
    """Helper class for testing nodes with common patterns."""

    def __init__(self, node_class, context: ExecutionContext):
        self.node_class = node_class
        self.context = context
        self.node = None

    def create(self, node_id: str = "test_node", config: Optional[Dict[str, Any]] = None):
        """Create a new node instance."""
        self.node = create_node(self.node_class, node_id, config)
        return self

    def with_inputs(self, **kwargs):
        """Set input values on the node."""
        if self.node:
            set_node_inputs(self.node, **kwargs)
        return self

    async def execute(self) -> Any:
        """Execute the node and return result."""
        if self.node:
            return await execute_node(self.node, self.context)
        return None

    def get_output(self, port_name: str) -> Any:
        """Get an output value from the node."""
        if self.node:
            return get_node_output(self.node, port_name)
        return None

    def assert_status(self, expected_status: NodeStatus):
        """Assert the node has the expected status."""
        if self.node:
            assert self.node.status == expected_status, f"Expected {expected_status}, got {self.node.status}"
        return self


@pytest.fixture
def node_helper(execution_context):
    """Factory fixture to create NodeTestHelper instances."""
    def _create_helper(node_class):
        return NodeTestHelper(node_class, execution_context)
    return _create_helper


# Test data generators
def generate_test_strings():
    """Generate various test strings for comprehensive testing."""
    return [
        "",
        "Hello",
        "Hello World",
        "Special chars: !@#$%^&*()",
        "Unicode: \u4e2d\u6587 \u65e5\u672c\u8a9e \ud55c\uad6d\uc5b4",
        "Numbers: 12345",
        "Mixed: abc123!@#",
        "  whitespace  ",
        "\n\t\r",
        "A" * 1000,  # Long string
    ]


def generate_test_numbers():
    """Generate various test numbers."""
    return [
        0,
        1,
        -1,
        42,
        3.14,
        -3.14,
        0.001,
        1000000,
        float('inf'),
        float('-inf'),
    ]


def generate_test_lists():
    """Generate various test lists."""
    return [
        [],
        [1],
        [1, 2, 3],
        ["a", "b", "c"],
        [1, "two", 3.0, True, None],
        [[1, 2], [3, 4]],  # Nested
        list(range(100)),  # Long list
    ]


def generate_test_dicts():
    """Generate various test dictionaries."""
    return [
        {},
        {"key": "value"},
        {"a": 1, "b": 2, "c": 3},
        {"nested": {"key": "value"}},
        {"list": [1, 2, 3]},
        {"mixed": {"num": 1, "str": "text", "bool": True, "list": [1, 2]}},
    ]


# Temporary file/directory fixtures for file system tests
@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory with test files."""
    test_dir = tmp_path / "test_files"
    test_dir.mkdir()

    # Create some test files
    (test_dir / "test.txt").write_text("Test content")
    (test_dir / "data.json").write_text('{"key": "value"}')
    (test_dir / "numbers.csv").write_text("a,b,c\n1,2,3\n4,5,6")

    # Create subdirectory
    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "nested.txt").write_text("Nested content")

    return test_dir


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for output files."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# =============================================================================
# Qt/GUI Testing Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def qapp():
    """
    Create QApplication instance for GUI tests.
    This is session-scoped to avoid creating multiple QApplication instances.
    """
    from PySide6.QtWidgets import QApplication

    # Check if QApplication already exists
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # Don't quit the app here as it may be needed by other tests


@pytest.fixture
def main_window(qapp, qtbot):
    """
    Create a MainWindow instance for testing.

    Uses qtbot from pytest-qt for proper event handling.
    """
    from casare_rpa.canvas.main_window import MainWindow

    window = MainWindow()
    qtbot.addWidget(window)
    yield window
    window.close()


@pytest.fixture
def main_window_with_file(main_window, tmp_path):
    """MainWindow with a mock current file set."""
    test_file = tmp_path / "test_workflow.json"
    test_file.write_text('{"nodes": [], "connections": []}')
    main_window.set_current_file(test_file)
    return main_window


@pytest.fixture
def mock_file_dialog():
    """Mock QFileDialog for testing file operations."""
    with patch("casare_rpa.canvas.main_window.QFileDialog") as mock_dialog:
        yield mock_dialog


@pytest.fixture
def mock_message_box():
    """Mock QMessageBox for testing dialogs."""
    with patch("casare_rpa.canvas.main_window.QMessageBox") as mock_box:
        yield mock_box


@pytest.fixture
def schedule_dialog(qapp, qtbot, tmp_path):
    """Create a ScheduleDialog for testing."""
    from casare_rpa.canvas.schedule_dialog import ScheduleDialog

    test_file = tmp_path / "test_workflow.json"
    test_file.write_text('{}')

    dialog = ScheduleDialog(
        workflow_path=test_file,
        workflow_name="Test Workflow"
    )
    qtbot.addWidget(dialog)
    yield dialog
    dialog.close()


@pytest.fixture
def schedule_manager_dialog(qapp, qtbot):
    """Create a ScheduleManagerDialog for testing."""
    from casare_rpa.canvas.schedule_dialog import ScheduleManagerDialog

    dialog = ScheduleManagerDialog(schedules=[])
    qtbot.addWidget(dialog)
    yield dialog
    dialog.close()


@pytest.fixture
def node_search_dialog(qapp, qtbot):
    """Create a NodeSearchDialog for testing."""
    from casare_rpa.canvas.node_search_dialog import NodeSearchDialog

    dialog = NodeSearchDialog()
    qtbot.addWidget(dialog)
    yield dialog
    dialog.close()


# Helper functions for GUI testing
def click_action(qtbot, action):
    """Helper to trigger a QAction in tests."""
    action.trigger()
    qtbot.wait(10)  # Small delay for event processing


def get_menu_action(window, menu_name: str, action_text: str):
    """Find a menu action by menu and action text."""
    for menu_action in window.menuBar().actions():
        if menu_action.text() == menu_name:
            menu = menu_action.menu()
            for action in menu.actions():
                if action.text() == action_text:
                    return action
    return None
