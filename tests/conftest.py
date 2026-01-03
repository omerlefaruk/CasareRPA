"""
Shared pytest fixtures and configuration for CasareRPA tests.

This module provides centralized test infrastructure including:
- Pytest configuration and custom markers
- Execution context fixtures (real and mock versions)
- Browser testing fixtures (Playwright mocks)
- HTTP client fixtures
- Qt/UI testing fixtures
- Database fixtures
- File system fixtures
- Helper utilities

USAGE:
    Fixtures defined here are automatically available to all tests.
    Import helper functions explicitly:
        from tests.conftest import create_test_node, assert_node_success

RUN TESTS:
    pytest tests/ -v                           # All tests
    pytest tests/ -m "unit" -v                 # Unit tests only
    pytest tests/ -m "not slow" -v             # Skip slow tests
    pytest tests/ -m "browser" -v              # Browser tests only
"""

from __future__ import annotations

import asyncio
import importlib.abc
import json
import os
import sys
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock

# =============================================================================
# Qt Headless Configuration (MUST be before any Qt imports)
# =============================================================================
# This enables Qt to run without a display server (for CI/headless testing)
if "QT_QPA_PLATFORM" not in os.environ:
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

os.environ["CASARE_RPA_DISABLE_LOGURU_ENQUEUE"] = "1"

# Ensure src is in path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# ------------------------------------------------------------------------
# Optional dependency import guards
# ------------------------------------------------------------------------
# Some optional ML deps (notably `sentence_transformers` -> sklearn/scipy) can
# crash the Python interpreter with a Windows access violation in certain
# environments. Tests that rely on these deps use `pytest.importorskip`, so
# forcing an ImportError is the safest behavior during pytest runs.


class _BlockCrashingOptionalDeps(importlib.abc.MetaPathFinder):
    _blocked_prefixes = ("sentence_transformers",)

    def find_spec(self, fullname: str, path: Any, target: Any = None):  # type: ignore[override]
        if fullname in self._blocked_prefixes or fullname.startswith(
            tuple(f"{p}." for p in self._blocked_prefixes)
        ):
            raise ImportError(f"Blocked optional dependency import during tests: {fullname}")
        return None


sys.meta_path.insert(0, _BlockCrashingOptionalDeps())

# Ensure any preloaded casare_rpa modules resolve from this worktree
repo_root = Path(__file__).parent.parent.resolve()
for module_name, module in list(sys.modules.items()):
    if module_name == "casare_rpa" or module_name.startswith("casare_rpa."):
        module_file = getattr(module, "__file__", None)
        module_paths = [module_file] if module_file else []
        module_paths.extend(getattr(module, "__path__", []))
        if not module_paths:
            continue
        try:
            resolved_paths = [Path(path).resolve() for path in module_paths]
        except OSError:
            del sys.modules[module_name]
            continue
        if all(not path.is_relative_to(repo_root) for path in resolved_paths):
            del sys.modules[module_name]

import pytest
from loguru import logger

_RAN_UI_TESTS = False

# Work around a Windows-only interpreter crash during pytest shutdown.
#
# Pytest's built-in `unraisableexception` cleanup calls `gc.collect()` several
# times ("gc_collect_harder") to surface unraisable exceptions. In some
# environments (notably with Qt/PySide in-process), repeated collections during
# pytest teardown can trigger a fatal access violation even when all tests pass.
#
# Skipping the extra GC iterations is the smallest, test-only mitigation to
# ensure `pytest` exits cleanly (exit code 0) on Windows.
if sys.platform == "win32":
    try:
        import _pytest.unraisableexception as _unraisableexception

        _unraisableexception.gc_collect_harder = lambda _iterations: None  # type: ignore[assignment]
    except Exception:
        pass

# Force Loguru to avoid queued logging in tests.
# On Windows, Loguru's background writer thread (`enqueue=True`) can trigger
# fatal access violations during pytest shutdown/GC in some environments.
_loguru_add = logger.add


def _loguru_add_no_enqueue(*args: Any, **kwargs: Any):  # type: ignore[no-untyped-def]
    kwargs["enqueue"] = False
    return _loguru_add(*args, **kwargs)


logger.add = _loguru_add_no_enqueue  # type: ignore[method-assign]

if TYPE_CHECKING:
    from casare_rpa.infrastructure.execution import ExecutionContext


# =============================================================================
# Pytest Configuration
# =============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Configure custom markers for test categorization."""
    markers = [
        "unit: mark test as unit test (fast, isolated, no external deps)",
        "integration: mark test as integration test (may use external systems)",
        "slow: mark test as slow running (deselect with '-m \"not slow\"')",
        "e2e: mark test as end-to-end test",
        "ui: mark test as requiring UI/Qt components",
        "browser: mark test as requiring browser/Playwright",
        "database: mark test as requiring database",
        "network: mark test as requiring network access",
        "chaos: mark test as chaos/stress test",
    ]
    for marker in markers:
        config.addinivalue_line("markers", marker)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Automatically mark tests based on their location."""
    for item in items:
        # Auto-mark based on path
        if "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)
        if "browser" in str(item.fspath):
            item.add_marker(pytest.mark.browser)
        if "presentation" in str(item.fspath):
            item.add_marker(pytest.mark.ui)
        if "domain" in str(item.fspath):
            item.add_marker(pytest.mark.unit)


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    """Record whether any UI/presentation tests actually ran."""
    global _RAN_UI_TESTS
    if report.when != "call":
        return
    nodeid = getattr(report, "nodeid", "")
    if "tests/presentation/" in nodeid or "tests\\presentation\\" in nodeid:
        _RAN_UI_TESTS = True


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """
    Ensure Loguru background workers are flushed/stopped.

    Loguru's queued logging (`enqueue=True`) can leave background threads alive
    at interpreter shutdown on Windows, which can lead to fatal access violations.
    """
    # Windows + PySide6 (especially under Python 3.13) can crash during normal
    # interpreter shutdown after large Qt-heavy test runs, even when all tests
    # pass. If a QApplication was created, terminate the process immediately to
    # avoid that unstable shutdown path.
    if (
        sys.platform == "win32"
        and exitstatus == 0
        and _RAN_UI_TESTS
        and os.environ.get("CASARE_RPA_DISABLE_PYSIDE_SHUTDOWN_WORKAROUND")
        not in {"1", "true", "True"}
    ):
        try:
            sys.stdout.flush()
            sys.stderr.flush()
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel32.GetCurrentProcess.restype = wintypes.HANDLE
            kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
            kernel32.TerminateProcess.restype = wintypes.BOOL

            handle = kernel32.GetCurrentProcess()
            kernel32.TerminateProcess(handle, 0)
        except Exception:
            pass

    # Best-effort Qt teardown: avoid leaving dangling Qt wrappers for interpreter
    # shutdown/GC (a known crash source on Windows in some PySide6 setups).
    try:
        from PySide6.QtCore import QCoreApplication, QThreadPool
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is not None:
            QApplication.closeAllWindows()
            QCoreApplication.sendPostedEvents(None, 0)
            app.processEvents()
            QCoreApplication.processEvents()

        # Ensure Qt's global thread pool is drained before teardown.
        # Stray worker threads can cause crashes during interpreter shutdown on Windows.
        pool = QThreadPool.globalInstance()
        if pool is not None:
            pool.waitForDone(5_000)
    except Exception:
        pass

    try:
        logger.complete()
    except Exception:
        pass
    logger.remove()


@pytest.fixture(autouse=True)
def _qt_autocleanup(request: pytest.FixtureRequest) -> Generator[None, None, None]:
    """
    Ensure UI tests don't leak top-level windows across the suite.

    Many UI tests create windows/widgets without explicitly closing them. On
    Windows + PySide6 this can accumulate native resources and lead to fatal
    crashes during process shutdown. Cleaning up after each UI test keeps the
    suite stable.
    """
    yield
    if request.node.get_closest_marker("ui") is None:
        return
    try:
        from PySide6.QtCore import QCoreApplication
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app is None:
            return

        for widget in QApplication.topLevelWidgets():
            try:
                widget.close()
                widget.deleteLater()
            except Exception:
                pass

        QCoreApplication.sendPostedEvents(None, 0)
        app.processEvents()
        QCoreApplication.processEvents()
    except Exception:
        pass


# =============================================================================
# Event Loop Fixture (Async Support)
# =============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create event loop for async tests.

    Scoped to session to avoid creating multiple loops.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Domain Layer Fixtures - ExecutionContext
# =============================================================================


@pytest.fixture
def execution_context() -> ExecutionContext:
    """
    Create a REAL ExecutionContext for node testing.

    Use this for tests that need actual context behavior.
    The context is initialized with:
    - workflow_name: "TestWorkflow"
    - mode: ExecutionMode.NORMAL
    - empty initial variables

    Example:
        async def test_node_execution(execution_context):
            node = MyNode("test")
            result = await node.execute(execution_context)
            assert result["success"] is True
    """
    from casare_rpa.domain.value_objects.types import ExecutionMode
    from casare_rpa.infrastructure.execution import ExecutionContext

    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={},
    )


@pytest.fixture
def execution_context_with_vars() -> ExecutionContext:
    """
    Create ExecutionContext with pre-populated variables.

    Includes common test variables:
    - test_string: "hello"
    - test_number: 42
    - test_list: [1, 2, 3]
    - test_dict: {"key": "value"}
    """
    from casare_rpa.domain.value_objects.types import ExecutionMode
    from casare_rpa.infrastructure.execution import ExecutionContext

    return ExecutionContext(
        workflow_name="TestWorkflow",
        mode=ExecutionMode.NORMAL,
        initial_variables={
            "test_string": "hello",
            "test_number": 42,
            "test_list": [1, 2, 3],
            "test_dict": {"key": "value"},
        },
    )


@pytest.fixture
def mock_context() -> MagicMock:
    """
    Create a MOCK ExecutionContext for controlled testing.

    Use this when you need to:
    - Control return values of context methods
    - Verify context method calls
    - Inject specific behaviors

    Default behavior:
    - resolve_value: returns input unchanged (pass-through)
    - variables: empty dict
    - resources: empty dict

    Example:
        def test_with_controlled_context(mock_context):
            mock_context.resolve_value.return_value = "resolved_value"
            node = MyNode("test")
            # ...
    """
    from casare_rpa.infrastructure.execution import ExecutionContext

    context = MagicMock(spec=ExecutionContext)
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    context.set_variable = MagicMock()
    context.get_variable = MagicMock(return_value=None)
    context.variables = {}
    context.resources = {}
    context.workflow_id = "test-workflow-123"
    context.node_id = "test-node-456"
    return context


@pytest.fixture
def async_mock_context(mock_context: MagicMock) -> MagicMock:
    """
    Mock ExecutionContext with async methods for async node testing.

    Extends mock_context with AsyncMock for async operations.
    """
    context = mock_context
    context.get_input = AsyncMock(return_value=None)
    context.set_output = AsyncMock()
    return context


# =============================================================================
# Browser Testing Fixtures (Playwright Mocks)
# =============================================================================


@pytest.fixture
def mock_page() -> AsyncMock:
    """
    Create a mock Playwright Page object.

    Includes common methods used by browser nodes:
    - Navigation: goto, reload, go_back, go_forward
    - Selectors: query_selector, query_selector_all, wait_for_selector
    - Actions: click, fill, type, press, check, uncheck, select_option
    - JavaScript: evaluate, evaluate_handle
    - State: url, title, content, screenshot

    Example:
        async def test_browser_node(mock_context, mock_page):
            mock_page.evaluate.return_value = "My Title"
            mock_context.get_active_page.return_value = mock_page
            # ...
    """
    page = AsyncMock()

    # Navigation
    page.goto = AsyncMock(return_value=None)
    page.reload = AsyncMock(return_value=None)
    page.go_back = AsyncMock(return_value=None)
    page.go_forward = AsyncMock(return_value=None)

    # Selectors
    page.query_selector = AsyncMock(return_value=MagicMock())
    page.query_selector_all = AsyncMock(return_value=[])
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    page.wait_for_load_state = AsyncMock(return_value=None)

    # Actions
    page.click = AsyncMock(return_value=None)
    page.fill = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)
    page.press = AsyncMock(return_value=None)
    page.check = AsyncMock(return_value=None)
    page.uncheck = AsyncMock(return_value=None)
    page.select_option = AsyncMock(return_value=None)
    page.hover = AsyncMock(return_value=None)
    page.focus = AsyncMock(return_value=None)

    # JavaScript execution
    page.evaluate = AsyncMock(return_value={"data": "test"})
    page.evaluate_handle = AsyncMock(return_value=MagicMock())

    # State/Content
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example Page")
    page.content = AsyncMock(return_value="<html><body>Test</body></html>")
    page.screenshot = AsyncMock(return_value=b"fake-screenshot-bytes")
    page.pdf = AsyncMock(return_value=b"fake-pdf-bytes")

    # Frame handling
    page.frames = []
    page.main_frame = MagicMock()

    # Locator (modern Playwright API)
    page.locator = MagicMock(return_value=AsyncMock())

    return page


@pytest.fixture
def mock_browser() -> AsyncMock:
    """
    Create a mock Playwright Browser object.

    Includes:
    - new_context: creates browser contexts
    - new_page: creates pages
    - close: cleanup
    """
    browser = AsyncMock()
    browser.new_page = AsyncMock()
    browser.new_context = AsyncMock()
    browser.close = AsyncMock()
    browser.is_connected = MagicMock(return_value=True)
    return browser


@pytest.fixture
def mock_browser_context() -> AsyncMock:
    """
    Create a mock Playwright BrowserContext object.
    """
    context = AsyncMock()
    context.new_page = AsyncMock()
    context.close = AsyncMock()
    context.pages = []
    context.cookies = AsyncMock(return_value=[])
    context.add_cookies = AsyncMock()
    context.clear_cookies = AsyncMock()
    return context


@pytest.fixture
def browser_context_with_page(
    mock_context: MagicMock,
    mock_page: AsyncMock,
) -> MagicMock:
    """
    Create mock ExecutionContext with attached page.

    Convenience fixture for browser node tests that need
    both context and page connected.
    """
    mock_context.get_active_page = MagicMock(return_value=mock_page)
    return mock_context


@pytest.fixture
def browser_context_no_page(mock_context: MagicMock) -> MagicMock:
    """
    Create mock ExecutionContext without a page.

    For testing error handling when no page is available.
    """
    mock_context.get_active_page = MagicMock(return_value=None)
    return mock_context


# =============================================================================
# HTTP Client Fixtures
# =============================================================================


@pytest.fixture
def mock_http_client() -> AsyncMock:
    """
    Create a mock UnifiedHttpClient for HTTP testing.

    Default responses return 200 OK with empty JSON.
    Configure specific responses as needed.

    Example:
        async def test_api_call(mock_http_client):
            mock_http_client.get.return_value = MagicMock(
                status_code=200,
                json=MagicMock(return_value={"data": "value"})
            )
    """
    client = AsyncMock()

    # Default successful response
    default_response = MagicMock()
    default_response.status_code = 200
    default_response.json = MagicMock(return_value={})
    default_response.text = ""
    default_response.content = b""
    default_response.headers = {}
    default_response.ok = True

    client.get = AsyncMock(return_value=default_response)
    client.post = AsyncMock(return_value=default_response)
    client.put = AsyncMock(return_value=default_response)
    client.patch = AsyncMock(return_value=default_response)
    client.delete = AsyncMock(return_value=default_response)
    client.request = AsyncMock(return_value=default_response)

    return client


@pytest.fixture
def mock_http_error_response() -> MagicMock:
    """
    Create a mock HTTP error response (500 Internal Server Error).
    """
    response = MagicMock()
    response.status_code = 500
    response.json = MagicMock(return_value={"error": "Internal Server Error"})
    response.text = "Internal Server Error"
    response.ok = False
    return response


# =============================================================================
# Qt/UI Testing Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def qapp():
    """
    Create or get QApplication for the entire test session.

    Qt requires exactly one QApplication instance.
    This fixture ensures we reuse the same instance.
    """
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        pytest.skip("PySide6 not available")
        return None

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def qtbot_like(qapp):
    """
    Simple Qt event processing helper.

    For tests that don't need full pytest-qt functionality.
    """

    class QtBotLike:
        def __init__(self, app):
            self._app = app

        def process_events(self):
            """Process pending Qt events."""
            if self._app:
                self._app.processEvents()

        def add_widget(self, widget):
            """Register a widget (no-op for cleanup tracking)."""
            pass

        def wait(self, ms: int = 100):
            """Wait for specified milliseconds."""
            import time

            time.sleep(ms / 1000)
            self.process_events()

    return QtBotLike(qapp)


@pytest.fixture
def mock_theme():
    """
    Mock the Theme class to avoid actual theme loading.

    Provides all necessary color values for styled widgets.
    """
    mock_colors = MagicMock()
    mock_colors.background = "#1e1e1e"
    mock_colors.background_alt = "#252526"
    mock_colors.surface = "#2d2d30"
    mock_colors.surface_hover = "#3e3e42"
    mock_colors.header = "#323232"
    mock_colors.text_primary = "#e0e0e0"
    mock_colors.text_secondary = "#9d9d9d"
    mock_colors.border = "#454545"
    mock_colors.border_light = "#555555"
    mock_colors.border_dark = "#333333"
    mock_colors.border_focus = "#007acc"
    mock_colors.accent = "#0e639c"
    mock_colors.accent_hover = "#1177bb"
    mock_colors.secondary_hover = "#4a4a4a"
    mock_colors.selection = "#264f78"
    mock_colors.error = "#f14c4c"
    mock_colors.warning = "#cca700"
    mock_colors.info = "#3794ff"
    mock_colors.success = "#4ec9b0"

    return mock_colors


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest.fixture
def mock_db_session() -> MagicMock:
    """
    Create a mock database session.
    """
    session = MagicMock()
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    session.close = MagicMock()
    session.add = MagicMock()
    session.delete = MagicMock()
    session.query = MagicMock()
    return session


@pytest.fixture
def mock_async_db_session() -> AsyncMock:
    """
    Create a mock async database session.
    """
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


# =============================================================================
# File System Fixtures
# =============================================================================


@pytest.fixture
def temp_test_file(tmp_path: Path) -> Path:
    """Create a temporary test file with content."""
    test_file = tmp_path / "test_file.txt"
    test_file.write_text("Hello, World!", encoding="utf-8")
    return test_file


@pytest.fixture
def temp_csv_file(tmp_path: Path) -> Path:
    """Create a temporary CSV file with test data."""
    csv_file = tmp_path / "test_data.csv"
    csv_content = """name,age,city
Alice,30,New York
Bob,25,Los Angeles
Charlie,35,Chicago
"""
    csv_file.write_text(csv_content, encoding="utf-8")
    return csv_file


@pytest.fixture
def temp_json_file(tmp_path: Path) -> Path:
    """Create a temporary JSON file with test data."""
    json_file = tmp_path / "test_data.json"
    data = {"name": "Test", "items": [1, 2, 3], "nested": {"key": "value"}}
    json_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return json_file


@pytest.fixture
def temp_directory(tmp_path: Path) -> Path:
    """
    Create a temporary directory with some files.

    Structure:
        test_directory/
        ├── file1.txt
        ├── file2.txt
        ├── data.json
        └── subdir/
            └── nested.txt
    """
    test_dir = tmp_path / "test_directory"
    test_dir.mkdir()

    (test_dir / "file1.txt").write_text("Content 1")
    (test_dir / "file2.txt").write_text("Content 2")
    (test_dir / "data.json").write_text('{"key": "value"}')

    sub_dir = test_dir / "subdir"
    sub_dir.mkdir()
    (sub_dir / "nested.txt").write_text("Nested content")

    return test_dir


@pytest.fixture
def temp_workflow_file(tmp_path: Path) -> Path:
    """Create a temporary workflow JSON file."""
    workflow_file = tmp_path / "test_workflow.json"
    workflow_data = {
        "metadata": {
            "name": "TestWorkflow",
            "description": "Test workflow for testing",
            "version": "1.0.0",
        },
        "nodes": {
            "start": {
                "node_type": "StartNode",
                "config": {},
            },
        },
        "connections": [],
        "variables": {},
        "settings": {},
    }
    workflow_file.write_text(json.dumps(workflow_data, indent=2))
    return workflow_file


# =============================================================================
# Node Testing Fixtures
# =============================================================================


@pytest.fixture
def base_node_config() -> dict[str, Any]:
    """Default configuration for node instantiation."""
    return {
        "id": "test-node-id",
        "name": "Test Node",
        "position": {"x": 0, "y": 0},
    }


@pytest.fixture
def sample_workflow_data() -> dict[str, Any]:
    """Sample workflow data for testing."""
    return {
        "metadata": {
            "name": "SampleWorkflow",
            "description": "Sample workflow for testing",
            "version": "1.0.0",
        },
        "nodes": {},
        "connections": [],
        "variables": {},
        "settings": {},
        "frames": [],
    }


# =============================================================================
# Signal Capture Helper (for Qt signal testing)
# =============================================================================


class SignalCapture:
    """
    Helper class to capture Qt signals for testing.

    Example:
        capture = SignalCapture()
        widget.some_signal.connect(capture.slot)
        widget.trigger_signal()
        assert capture.called
        assert capture.last_args == ("expected", "args")
    """

    def __init__(self):
        self.signals: list[tuple] = []

    def slot(self, *args: Any) -> None:
        """Slot to capture signal emissions."""
        self.signals.append(args)

    @property
    def called(self) -> bool:
        """Check if signal was emitted at least once."""
        return len(self.signals) > 0

    @property
    def call_count(self) -> int:
        """Get number of signal emissions."""
        return len(self.signals)

    @property
    def last_args(self) -> tuple:
        """Get arguments from last signal emission."""
        if self.signals:
            return self.signals[-1]
        return ()

    def clear(self) -> None:
        """Clear captured signals."""
        self.signals.clear()


@pytest.fixture
def signal_capture() -> SignalCapture:
    """Provide a SignalCapture instance for signal testing."""
    return SignalCapture()


# =============================================================================
# Helper Functions (Import these explicitly in tests)
# =============================================================================


def create_test_node(node_class: type, node_id: str = "test-node", **config: Any):
    """
    Helper to instantiate a node for testing.

    Args:
        node_class: The node class to instantiate
        node_id: Optional node ID (default: "test-node")
        **config: Additional configuration parameters

    Returns:
        Instantiated node

    Example:
        from tests.conftest import create_test_node
        node = create_test_node(BrowserClickNode, selector="#button")
    """
    return node_class(node_id, config=config if config else None)


def assert_node_success(result: dict[str, Any], message: str = "") -> None:
    """
    Assert that a node execution result indicates success.

    Args:
        result: The result dictionary from node.execute()
        message: Optional message for assertion failure
    """
    assert result.get("success") is True, (
        f"Node execution failed: {result.get('error', 'Unknown error')}. {message}"
    )


def assert_node_failure(result: dict[str, Any], expected_error: str | None = None) -> None:
    """
    Assert that a node execution result indicates failure.

    Args:
        result: The result dictionary from node.execute()
        expected_error: Optional substring to check in error message
    """
    assert result.get("success") is False, "Expected node to fail but it succeeded"
    if expected_error:
        assert expected_error in result.get("error", ""), (
            f"Expected error to contain '{expected_error}', got: {result.get('error')}"
        )


def create_mock_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
    headers: dict | None = None,
) -> MagicMock:
    """
    Create a mock HTTP response with specified values.

    Args:
        status_code: HTTP status code
        json_data: JSON response data
        text: Text response
        headers: Response headers

    Returns:
        MagicMock configured as an HTTP response
    """
    response = MagicMock()
    response.status_code = status_code
    response.json = MagicMock(return_value=json_data or {})
    response.text = text
    response.headers = headers or {}
    response.ok = 200 <= status_code < 300
    return response


# =============================================================================
# Workflow Data Generators (for performance tests)
# =============================================================================


def generate_workflow_data(
    node_count: int,
    name: str = "TestWorkflow",
) -> dict[str, Any]:
    """
    Generate workflow data with specified number of nodes.

    Creates a linear chain of nodes connected via exec ports.

    Args:
        node_count: Number of nodes to generate
        name: Workflow name

    Returns:
        Complete workflow data dictionary
    """
    nodes = {}
    connections = []

    node_types = ["StartNode", "SetVariableNode", "LogNode", "CommentNode"]

    for i in range(node_count):
        node_id = f"node_{i:04d}"
        if i == 0:
            node_type = "StartNode"
            config = {}
        else:
            node_type = node_types[(i % (len(node_types) - 1)) + 1]
            if node_type == "SetVariableNode":
                config = {"variable_name": f"var_{i}", "value": f"value_{i}"}
            elif node_type == "LogNode":
                config = {"message": f"Log message {i}"}
            else:
                config = {"comment": f"Node {i}"}

        nodes[node_id] = {
            "node_type": node_type,
            "config": config,
            "position": {"x": 100 + (i * 150), "y": 100},
        }

    # Create linear connections
    for i in range(node_count - 1):
        connections.append(
            {
                "source_node": f"node_{i:04d}",
                "source_port": "exec_out",
                "target_node": f"node_{i + 1:04d}",
                "target_port": "exec_in",
            }
        )

    return {
        "metadata": {
            "name": name,
            "description": f"Test workflow with {node_count} nodes",
            "version": "1.0.0",
        },
        "nodes": nodes,
        "connections": connections,
        "variables": {"test_var": "value"},
        "settings": {},
        "frames": [],
    }


# =============================================================================
# Parametrize Helpers
# =============================================================================


# Common data types for parametrized tests
COMMON_DATA_TYPES = [
    ("string", "hello"),
    ("integer", 42),
    ("float", 3.14),
    ("boolean_true", True),
    ("boolean_false", False),
    ("list", [1, 2, 3]),
    ("dict", {"key": "value"}),
    ("none", None),
    ("empty_string", ""),
    ("empty_list", []),
    ("empty_dict", {}),
]

# Common error scenarios for parametrized tests
COMMON_ERROR_SCENARIOS = [
    ("timeout", TimeoutError("Operation timed out")),
    ("connection_error", ConnectionError("Connection refused")),
    ("value_error", ValueError("Invalid value")),
    ("key_error", KeyError("missing_key")),
    ("runtime_error", RuntimeError("Runtime error")),
]
