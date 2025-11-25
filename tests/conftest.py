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


# =============================================================================
# Chaos Testing Fixtures
# =============================================================================

class NetworkFailureSimulator:
    """Simulate various network failure scenarios."""

    def __init__(self):
        self.failure_mode = None
        self.failure_count = 0
        self.max_failures = float('inf')

    def set_failure_mode(self, mode: str, max_failures: int = float('inf')):
        """Set the failure mode for network operations."""
        self.failure_mode = mode
        self.max_failures = max_failures
        self.failure_count = 0

    def reset(self):
        """Reset the simulator."""
        self.failure_mode = None
        self.failure_count = 0
        self.max_failures = float('inf')

    async def maybe_fail(self):
        """Potentially raise an exception based on failure mode."""
        if self.failure_mode and self.failure_count < self.max_failures:
            self.failure_count += 1
            if self.failure_mode == "timeout":
                raise asyncio.TimeoutError("Simulated network timeout")
            elif self.failure_mode == "connection_refused":
                raise ConnectionRefusedError("Simulated connection refused")
            elif self.failure_mode == "connection_reset":
                raise ConnectionResetError("Simulated connection reset")
            elif self.failure_mode == "dns_failure":
                raise OSError("Simulated DNS lookup failed")
            elif self.failure_mode == "ssl_error":
                import ssl
                raise ssl.SSLError("Simulated SSL certificate error")


@pytest.fixture
def network_failure():
    """Fixture for simulating network failures."""
    simulator = NetworkFailureSimulator()
    yield simulator
    simulator.reset()


class BrowserCrashSimulator:
    """Simulate browser crash scenarios."""

    def __init__(self):
        self.crash_on_next = False
        self.crash_after_calls = None
        self.call_count = 0
        self.crash_reason = "Browser disconnected"

    def set_crash_on_next(self, reason: str = "Browser disconnected"):
        """Crash on next browser operation."""
        self.crash_on_next = True
        self.crash_reason = reason

    def set_crash_after_calls(self, count: int, reason: str = "Browser disconnected"):
        """Crash after N successful calls."""
        self.crash_after_calls = count
        self.call_count = 0
        self.crash_reason = reason

    def reset(self):
        """Reset the simulator."""
        self.crash_on_next = False
        self.crash_after_calls = None
        self.call_count = 0

    def check_and_maybe_crash(self):
        """Check if we should crash and raise if so."""
        from playwright.async_api import Error as PlaywrightError

        if self.crash_on_next:
            self.crash_on_next = False
            raise PlaywrightError(self.crash_reason)

        if self.crash_after_calls is not None:
            self.call_count += 1
            if self.call_count >= self.crash_after_calls:
                self.crash_after_calls = None
                raise PlaywrightError(self.crash_reason)


@pytest.fixture
def browser_crash():
    """Fixture for simulating browser crashes."""
    simulator = BrowserCrashSimulator()
    yield simulator
    simulator.reset()


@pytest.fixture
def crashing_mock_page(browser_crash):
    """Create a mock page that can simulate crashes."""
    page = MagicMock()

    async def maybe_crash_then(*args, **kwargs):
        browser_crash.check_and_maybe_crash()
        return MagicMock()

    async def maybe_crash_return_text(*args, **kwargs):
        browser_crash.check_and_maybe_crash()
        return "Test content"

    page.goto = AsyncMock(side_effect=maybe_crash_then)
    page.click = AsyncMock(side_effect=maybe_crash_then)
    page.fill = AsyncMock(side_effect=maybe_crash_then)
    page.wait_for_selector = AsyncMock(side_effect=maybe_crash_then)
    page.query_selector = AsyncMock(side_effect=maybe_crash_then)
    page.content = AsyncMock(side_effect=maybe_crash_return_text)
    page.title = AsyncMock(side_effect=maybe_crash_return_text)
    page.close = AsyncMock()
    page.url = "https://example.com"

    return page


class SelectorFailureSimulator:
    """Simulate selector/element failures."""

    def __init__(self):
        self.failure_mode = None
        self.target_selector = None

    def set_selector_not_found(self, selector: str = None):
        """Simulate element not found for specific or all selectors."""
        self.failure_mode = "not_found"
        self.target_selector = selector

    def set_element_stale(self, selector: str = None):
        """Simulate stale element reference."""
        self.failure_mode = "stale"
        self.target_selector = selector

    def set_element_detached(self, selector: str = None):
        """Simulate detached element."""
        self.failure_mode = "detached"
        self.target_selector = selector

    def reset(self):
        """Reset the simulator."""
        self.failure_mode = None
        self.target_selector = None

    def should_fail(self, selector: str) -> bool:
        """Check if the given selector should fail."""
        if self.failure_mode is None:
            return False
        if self.target_selector is None:
            return True
        return selector == self.target_selector

    def get_error(self, selector: str):
        """Get the error to raise for a failed selector."""
        from playwright.async_api import TimeoutError as PWTimeoutError

        if self.failure_mode == "not_found":
            return PWTimeoutError(f"Element not found: {selector}")
        elif self.failure_mode == "stale":
            from playwright.async_api import Error as PlaywrightError
            return PlaywrightError(f"Element is stale: {selector}")
        elif self.failure_mode == "detached":
            from playwright.async_api import Error as PlaywrightError
            return PlaywrightError(f"Element is detached from DOM: {selector}")
        return None


@pytest.fixture
def selector_failure():
    """Fixture for simulating selector failures."""
    simulator = SelectorFailureSimulator()
    yield simulator
    simulator.reset()


@pytest.fixture
def failing_mock_page(selector_failure):
    """Create a mock page with controllable selector failures."""
    page = MagicMock()

    async def wait_with_failure(selector, **kwargs):
        if selector_failure.should_fail(selector):
            raise selector_failure.get_error(selector)
        element = MagicMock()
        element.click = AsyncMock()
        element.fill = AsyncMock()
        element.text_content = AsyncMock(return_value="Text")
        return element

    async def query_with_failure(selector):
        if selector_failure.should_fail(selector):
            return None  # query_selector returns None when not found
        element = MagicMock()
        element.click = AsyncMock()
        element.fill = AsyncMock()
        element.text_content = AsyncMock(return_value="Text")
        return element

    page.goto = AsyncMock()
    page.click = AsyncMock()
    page.fill = AsyncMock()
    page.wait_for_selector = AsyncMock(side_effect=wait_with_failure)
    page.query_selector = AsyncMock(side_effect=query_with_failure)
    page.query_selector_all = AsyncMock(return_value=[])
    page.content = AsyncMock(return_value="<html></html>")
    page.title = AsyncMock(return_value="Test")
    page.close = AsyncMock()
    page.url = "https://example.com"

    return page


# Desktop automation mocks
class DesktopAutomationMock:
    """Mock for Windows desktop automation (uiautomation)."""

    def __init__(self):
        self.windows = {}
        self.fail_on_find = False
        self.fail_on_click = False
        self.delay_ms = 0

    def add_mock_window(self, name: str, class_name: str = "MockWindow"):
        """Add a mock window."""
        window = MagicMock()
        window.Name = name
        window.ClassName = class_name
        window.SetFocus = MagicMock()
        window.Close = MagicMock()
        window.Exists = MagicMock(return_value=True)
        self.windows[name] = window
        return window

    def find_window(self, name: str = None, class_name: str = None):
        """Find a mock window."""
        if self.fail_on_find:
            return None
        for wname, window in self.windows.items():
            if name and name in wname:
                return window
            if class_name and window.ClassName == class_name:
                return window
        return None

    def set_fail_on_find(self, fail: bool = True):
        """Configure window finding to fail."""
        self.fail_on_find = fail

    def set_fail_on_click(self, fail: bool = True):
        """Configure click operations to fail."""
        self.fail_on_click = fail

    def reset(self):
        """Reset the mock."""
        self.windows.clear()
        self.fail_on_find = False
        self.fail_on_click = False


@pytest.fixture
def desktop_mock():
    """Fixture for desktop automation mocking."""
    mock = DesktopAutomationMock()
    yield mock
    mock.reset()


# Chaos workflow fixtures
@pytest.fixture
def chaos_workflow_simple():
    """A simple workflow for chaos testing."""
    return {
        "nodes": [
            {"id": "start_1", "type": "StartNode", "position": [0, 0], "config": {}},
            {"id": "log_1", "type": "LogNode", "position": [200, 0], "config": {"message": "Test"}},
            {"id": "end_1", "type": "EndNode", "position": [400, 0], "config": {}}
        ],
        "connections": [
            {"from_node": "start_1", "from_port": "exec_out", "to_node": "log_1", "to_port": "exec_in"},
            {"from_node": "log_1", "from_port": "exec_out", "to_node": "end_1", "to_port": "exec_in"}
        ],
        "variables": {}
    }


@pytest.fixture
def chaos_workflow_with_loop():
    """A workflow with loop for stress testing."""
    return {
        "nodes": [
            {"id": "start_1", "type": "StartNode", "position": [0, 0], "config": {}},
            {"id": "for_1", "type": "ForLoopNode", "position": [200, 0], "config": {"iterations": 10}},
            {"id": "log_1", "type": "LogNode", "position": [400, 0], "config": {"message": "Iteration"}},
            {"id": "end_1", "type": "EndNode", "position": [600, 0], "config": {}}
        ],
        "connections": [
            {"from_node": "start_1", "from_port": "exec_out", "to_node": "for_1", "to_port": "exec_in"},
            {"from_node": "for_1", "from_port": "loop_body", "to_node": "log_1", "to_port": "exec_in"},
            {"from_node": "log_1", "from_port": "exec_out", "to_node": "for_1", "to_port": "loop_back"},
            {"from_node": "for_1", "from_port": "exec_out", "to_node": "end_1", "to_port": "exec_in"}
        ],
        "variables": {}
    }


@pytest.fixture
def chaos_workflow_with_error_handling():
    """A workflow with try-catch for error handling tests."""
    return {
        "nodes": [
            {"id": "start_1", "type": "StartNode", "position": [0, 0], "config": {}},
            {"id": "try_1", "type": "TryCatchNode", "position": [200, 0], "config": {}},
            {"id": "risky_1", "type": "LogNode", "position": [400, 0], "config": {"message": "Risky operation"}},
            {"id": "catch_1", "type": "LogNode", "position": [400, 100], "config": {"message": "Error caught"}},
            {"id": "end_1", "type": "EndNode", "position": [600, 0], "config": {}}
        ],
        "connections": [
            {"from_node": "start_1", "from_port": "exec_out", "to_node": "try_1", "to_port": "exec_in"},
            {"from_node": "try_1", "from_port": "try_body", "to_node": "risky_1", "to_port": "exec_in"},
            {"from_node": "try_1", "from_port": "catch_body", "to_node": "catch_1", "to_port": "exec_in"},
            {"from_node": "risky_1", "from_port": "exec_out", "to_node": "end_1", "to_port": "exec_in"},
            {"from_node": "catch_1", "from_port": "exec_out", "to_node": "end_1", "to_port": "exec_in"}
        ],
        "variables": {}
    }


@pytest.fixture
def chaos_workflow_deep_nesting():
    """A deeply nested workflow for stack depth testing."""
    nodes = [{"id": "start_1", "type": "StartNode", "position": [0, 0], "config": {}}]
    connections = []

    # Create 20 nested if statements
    prev_node = "start_1"
    for i in range(20):
        node_id = f"if_{i}"
        nodes.append({
            "id": node_id,
            "type": "IfNode",
            "position": [(i + 1) * 200, 0],
            "config": {"condition": "True"}
        })
        connections.append({
            "from_node": prev_node,
            "from_port": "exec_out" if i == 0 else "true_branch",
            "to_node": node_id,
            "to_port": "exec_in"
        })
        prev_node = node_id

    nodes.append({"id": "end_1", "type": "EndNode", "position": [4400, 0], "config": {}})
    connections.append({
        "from_node": prev_node,
        "from_port": "true_branch",
        "to_node": "end_1",
        "to_port": "exec_in"
    })

    return {"nodes": nodes, "connections": connections, "variables": {}}


# Timeout configuration for chaos tests
@pytest.fixture
def short_timeout():
    """Short timeout for testing timeout handling."""
    return 0.1  # 100ms


@pytest.fixture
def medium_timeout():
    """Medium timeout for normal chaos tests."""
    return 1.0  # 1 second


@pytest.fixture
def long_timeout():
    """Long timeout for stress tests."""
    return 10.0  # 10 seconds


# Resource exhaustion fixtures
class ResourceExhaustionSimulator:
    """Simulate resource exhaustion scenarios."""

    def __init__(self):
        self.memory_limit_mb = None
        self.cpu_throttle = False
        self.disk_full = False
        self.file_handle_limit = None
        self._allocated = []

    def simulate_low_memory(self, limit_mb: int = 10):
        """Simulate low memory conditions."""
        self.memory_limit_mb = limit_mb

    def simulate_disk_full(self):
        """Simulate disk full condition."""
        self.disk_full = True

    def check_memory(self, requested_mb: int):
        """Check if memory allocation should fail."""
        if self.memory_limit_mb and requested_mb > self.memory_limit_mb:
            raise MemoryError(f"Simulated OOM: requested {requested_mb}MB, limit {self.memory_limit_mb}MB")

    def check_disk(self, requested_bytes: int):
        """Check if disk write should fail."""
        if self.disk_full:
            raise OSError("Simulated: No space left on device")

    def reset(self):
        """Reset the simulator."""
        self.memory_limit_mb = None
        self.cpu_throttle = False
        self.disk_full = False
        self.file_handle_limit = None
        self._allocated.clear()


@pytest.fixture
def resource_exhaustion():
    """Fixture for simulating resource exhaustion."""
    simulator = ResourceExhaustionSimulator()
    yield simulator
    simulator.reset()


# Flaky operation simulator
class FlakyOperationSimulator:
    """Simulate operations that fail intermittently."""

    def __init__(self):
        self.failure_rate = 0.0  # 0.0 to 1.0
        self.failures_before_success = 0
        self._attempt_count = 0
        import random
        self._random = random

    def set_failure_rate(self, rate: float):
        """Set random failure rate (0.0 - 1.0)."""
        self.failure_rate = min(max(rate, 0.0), 1.0)

    def set_failures_before_success(self, count: int):
        """Fail N times before succeeding."""
        self.failures_before_success = count
        self._attempt_count = 0

    def should_fail(self) -> bool:
        """Determine if current operation should fail."""
        if self.failures_before_success > 0:
            self._attempt_count += 1
            if self._attempt_count <= self.failures_before_success:
                return True
            return False

        if self.failure_rate > 0:
            return self._random.random() < self.failure_rate

        return False

    def maybe_fail(self, error_class=Exception, message="Simulated flaky failure"):
        """Potentially raise an error based on configured behavior."""
        if self.should_fail():
            raise error_class(message)

    def reset(self):
        """Reset the simulator."""
        self.failure_rate = 0.0
        self.failures_before_success = 0
        self._attempt_count = 0


@pytest.fixture
def flaky_operation():
    """Fixture for simulating flaky operations."""
    simulator = FlakyOperationSimulator()
    yield simulator
    simulator.reset()


# Async timing helpers
@pytest.fixture
def slow_async():
    """Factory for creating slow async operations."""
    async def _slow_operation(delay_seconds: float = 1.0, result=None):
        await asyncio.sleep(delay_seconds)
        return result
    return _slow_operation


@pytest.fixture
def racing_async():
    """Factory for creating racing async operations."""
    async def _race(*coros, timeout: float = 5.0):
        """Run coroutines and return the first to complete."""
        done, pending = await asyncio.wait(
            [asyncio.create_task(c) for c in coros],
            timeout=timeout,
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if done:
            return done.pop().result()
        raise asyncio.TimeoutError("Race timed out")
    return _race
