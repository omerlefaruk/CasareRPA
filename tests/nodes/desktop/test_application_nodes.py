"""
Comprehensive tests for desktop application automation nodes.

Tests LaunchApplicationNode, CloseApplicationNode, ActivateWindowNode,
and GetWindowListNode with mocked desktop context and UIAutomation.
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import Any, Dict, List, Optional

from casare_rpa.nodes.desktop_nodes.application_nodes import (
    LaunchApplicationNode,
    CloseApplicationNode,
    ActivateWindowNode,
    GetWindowListNode,
)
from casare_rpa.domain.value_objects.types import NodeStatus


class MockDesktopElement:
    """Mock DesktopElement for testing."""

    def __init__(
        self,
        name: str = "Test Window",
        process_id: int = 1234,
        automation_id: str = "auto_id",
        enabled: bool = True,
        visible: bool = True,
    ):
        self._name = name
        self._process_id = process_id
        self._automation_id = automation_id
        self._enabled = enabled
        self._visible = visible
        self._control = Mock()
        self._control.ProcessId = process_id
        self._control.SetFocus = Mock()
        self._control.NativeWindowHandle = 12345
        self._control.GetWindowPattern = Mock(return_value=Mock())

    def get_text(self) -> str:
        return self._name

    def get_property(self, prop: str) -> Any:
        props = {
            "ProcessId": self._process_id,
            "AutomationId": self._automation_id,
        }
        return props.get(prop)

    def is_enabled(self) -> bool:
        return self._enabled

    def is_visible(self) -> bool:
        return self._visible

    def get_bounding_rect(self) -> Dict[str, int]:
        return {"left": 0, "top": 0, "width": 800, "height": 600}


class MockDesktopContext:
    """Mock DesktopContext for testing without system interaction."""

    def __init__(self):
        self._launched_windows: List[MockDesktopElement] = []
        self._all_windows: List[MockDesktopElement] = []
        self._should_fail = False
        self._fail_message = "Mock failure"
        self._launch_timeout = False
        self._file_not_found = False

    def set_windows(self, windows: List[MockDesktopElement]) -> None:
        """Set mock windows for get_all_windows."""
        self._all_windows = windows

    async def async_launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
    ) -> MockDesktopElement:
        if self._file_not_found:
            raise FileNotFoundError(f"Application not found: {path}")
        if self._launch_timeout:
            raise TimeoutError("Timeout waiting for window")
        if self._should_fail:
            raise RuntimeError(self._fail_message)

        window = MockDesktopElement(
            name=window_title or "Launched App",
            process_id=5678,
        )
        self._launched_windows.append(window)
        return window

    async def async_close_application(
        self,
        window_or_pid: Any,
        force: bool = False,
        timeout: float = 5.0,
    ) -> bool:
        if self._should_fail:
            raise ValueError(self._fail_message)
        return True

    async def async_find_window(
        self,
        title: str,
        exact: bool = False,
        timeout: float = 5.0,
    ) -> Optional[MockDesktopElement]:
        if self._should_fail:
            raise ValueError(f"Window not found: {title}")

        for window in self._all_windows:
            if exact:
                if window.get_text() == title:
                    return window
            else:
                if title.lower() in window.get_text().lower():
                    return window
        raise ValueError(f"Window not found: {title}")

    def get_all_windows(
        self, include_invisible: bool = False
    ) -> List[MockDesktopElement]:
        if include_invisible:
            return self._all_windows
        return [w for w in self._all_windows if w.is_visible()]


@pytest.fixture
def mock_desktop_context():
    """Create a mock desktop context."""
    return MockDesktopContext()


@pytest.fixture
def execution_context(mock_desktop_context):
    """Create execution context with mock desktop context."""
    context = Mock()
    context.desktop_context = mock_desktop_context
    context.resolve_value = lambda x: x
    context.variables = {}
    return context


@pytest.fixture
def execution_context_no_desktop():
    """Create execution context without desktop context (to test creation)."""
    context = Mock(spec=[])
    context.resolve_value = lambda x: x
    context.variables = {}
    return context


# =============================================================================
# LaunchApplicationNode Tests
# =============================================================================


class TestLaunchApplicationNode:
    """Tests for LaunchApplicationNode."""

    @pytest.mark.asyncio
    async def test_launch_application_success(self, execution_context):
        """Test successful application launch."""
        node = LaunchApplicationNode(node_id="test_launch")
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["process_id"] == 5678
        assert "window" in result
        assert "window_title" in result
        assert "next_nodes" in result
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_launch_application_with_arguments(self, execution_context):
        """Test application launch with command line arguments."""
        node = LaunchApplicationNode(node_id="test_launch_args")
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")
        node.set_input_value("arguments", "--new-window")
        node.set_input_value("working_directory", "C:\\Temp")

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_ctx = execution_context.desktop_context
        assert len(mock_ctx._launched_windows) == 1

    @pytest.mark.asyncio
    async def test_launch_application_with_config_path(self, execution_context):
        """Test application launch with path from config."""
        node = LaunchApplicationNode(
            node_id="test_launch_config",
            config={"application_path": "C:\\Windows\\calc.exe"},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_launch_application_missing_path_raises_error(
        self, execution_context
    ):
        """Test that missing application path raises ValueError."""
        node = LaunchApplicationNode(node_id="test_launch_no_path")

        with pytest.raises(ValueError, match="Application path is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_launch_application_file_not_found(self, execution_context):
        """Test error handling when application file not found."""
        execution_context.desktop_context._file_not_found = True
        node = LaunchApplicationNode(node_id="test_launch_fnf")
        node.set_input_value("application_path", "C:\\nonexistent\\app.exe")

        with pytest.raises(RuntimeError, match="Application not found"):
            await node.execute(execution_context)

        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_launch_application_timeout(self, execution_context):
        """Test error handling when window not found within timeout."""
        execution_context.desktop_context._launch_timeout = True
        node = LaunchApplicationNode(
            node_id="test_launch_timeout",
            config={"timeout": 1.0},
        )
        node.set_input_value("application_path", "C:\\Windows\\slow_app.exe")

        with pytest.raises(RuntimeError, match="Timeout"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_launch_application_creates_desktop_context(
        self, execution_context_no_desktop
    ):
        """Test that DesktopContext is created if not present."""
        node = LaunchApplicationNode(node_id="test_launch_create_ctx")
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")

        with patch(
            "casare_rpa.nodes.desktop_nodes.application_nodes.DesktopContext"
        ) as MockCtx:
            mock_instance = MockDesktopContext()
            MockCtx.return_value = mock_instance

            result = await node.execute(execution_context_no_desktop)

            assert hasattr(execution_context_no_desktop, "desktop_context")

    @pytest.mark.asyncio
    async def test_launch_application_with_window_state_maximized(
        self, execution_context
    ):
        """Test launching application with maximized window state."""
        node = LaunchApplicationNode(
            node_id="test_launch_max",
            config={"window_state": "maximized"},
        )
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_launch_application_with_window_state_minimized(
        self, execution_context
    ):
        """Test launching application with minimized window state."""
        node = LaunchApplicationNode(
            node_id="test_launch_min",
            config={"window_state": "minimized"},
        )
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")

        result = await node.execute(execution_context)

        assert result["success"] is True


# =============================================================================
# CloseApplicationNode Tests
# =============================================================================


class TestCloseApplicationNode:
    """Tests for CloseApplicationNode."""

    @pytest.mark.asyncio
    async def test_close_application_by_window(self, execution_context):
        """Test closing application by window object."""
        mock_window = MockDesktopElement(name="Test App", process_id=1234)
        node = CloseApplicationNode(node_id="test_close_window")
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "next_nodes" in result
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_close_application_by_process_id(self, execution_context):
        """Test closing application by process ID."""
        node = CloseApplicationNode(node_id="test_close_pid")
        node.set_input_value("process_id", 1234)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_application_by_window_title(self, execution_context):
        """Test closing application by window title."""
        node = CloseApplicationNode(node_id="test_close_title")
        node.set_input_value("window_title", "Notepad")

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_application_force_close(self, execution_context):
        """Test force closing application."""
        mock_window = MockDesktopElement(name="Stuck App", process_id=9999)
        node = CloseApplicationNode(
            node_id="test_force_close",
            config={"force_close": True},
        )
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_application_with_timeout(self, execution_context):
        """Test closing application with custom timeout."""
        mock_window = MockDesktopElement(name="Slow App", process_id=1111)
        node = CloseApplicationNode(
            node_id="test_close_timeout",
            config={"timeout": 10.0},
        )
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_close_application_missing_identifier_raises_error(
        self, execution_context
    ):
        """Test that missing window/pid/title raises ValueError."""
        node = CloseApplicationNode(node_id="test_close_no_id")

        with pytest.raises(
            ValueError,
            match="Must provide either 'window', 'process_id', or 'window_title'",
        ):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_close_application_failure(self, execution_context):
        """Test error handling when close fails."""
        execution_context.desktop_context._should_fail = True
        execution_context.desktop_context._fail_message = "Close failed"
        node = CloseApplicationNode(node_id="test_close_fail")
        node.set_input_value("process_id", 1234)

        with pytest.raises(RuntimeError, match="Failed to close application"):
            await node.execute(execution_context)

        assert node.status == NodeStatus.ERROR


# =============================================================================
# ActivateWindowNode Tests
# =============================================================================


class TestActivateWindowNode:
    """Tests for ActivateWindowNode."""

    @pytest.mark.asyncio
    async def test_activate_window_by_object(self, execution_context):
        """Test activating window by window object."""
        mock_window = MockDesktopElement(name="Target Window", process_id=2222)
        node = ActivateWindowNode(node_id="test_activate_obj")
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window"] == mock_window
        assert "next_nodes" in result
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_activate_window_by_title(self, execution_context):
        """Test activating window by title."""
        mock_window = MockDesktopElement(name="Notepad", process_id=3333)
        execution_context.desktop_context.set_windows([mock_window])

        node = ActivateWindowNode(node_id="test_activate_title")
        node.set_input_value("window_title", "Notepad")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window"].get_text() == "Notepad"

    @pytest.mark.asyncio
    async def test_activate_window_partial_title_match(self, execution_context):
        """Test activating window with partial title match."""
        mock_window = MockDesktopElement(
            name="Document - Notepad",
            process_id=4444,
        )
        execution_context.desktop_context.set_windows([mock_window])

        node = ActivateWindowNode(
            node_id="test_activate_partial",
            config={"match_partial": True},
        )
        node.set_input_value("window_title", "Notepad")

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_activate_window_missing_identifier_raises_error(
        self, execution_context
    ):
        """Test that missing window/title raises ValueError."""
        node = ActivateWindowNode(node_id="test_activate_no_id")

        with pytest.raises(
            ValueError, match="Must provide either 'window' or 'window_title'"
        ):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_activate_window_not_found(self, execution_context):
        """Test error handling when window not found."""
        execution_context.desktop_context.set_windows([])
        execution_context.desktop_context._should_fail = True

        node = ActivateWindowNode(node_id="test_activate_not_found")
        node.set_input_value("window_title", "NonExistent Window")

        with pytest.raises(RuntimeError, match="Failed to activate window"):
            await node.execute(execution_context)

        assert node.status == NodeStatus.ERROR


# =============================================================================
# GetWindowListNode Tests
# =============================================================================


class TestGetWindowListNode:
    """Tests for GetWindowListNode."""

    @pytest.mark.asyncio
    async def test_get_window_list_empty(self, execution_context):
        """Test getting empty window list."""
        execution_context.desktop_context.set_windows([])

        node = GetWindowListNode(node_id="test_list_empty")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window_list"] == []
        assert result["window_count"] == 0
        assert "next_nodes" in result
        assert "exec_out" in result["next_nodes"]
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_get_window_list_multiple_windows(self, execution_context):
        """Test getting list with multiple windows."""
        windows = [
            MockDesktopElement(name="Window 1", process_id=1001),
            MockDesktopElement(name="Window 2", process_id=1002),
            MockDesktopElement(name="Window 3", process_id=1003),
        ]
        execution_context.desktop_context.set_windows(windows)

        node = GetWindowListNode(node_id="test_list_multi")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window_count"] == 3
        assert len(result["window_list"]) == 3

        for window_info in result["window_list"]:
            assert "window" in window_info
            assert "title" in window_info
            assert "process_id" in window_info
            assert "is_enabled" in window_info
            assert "is_visible" in window_info

    @pytest.mark.asyncio
    async def test_get_window_list_with_title_filter(self, execution_context):
        """Test filtering windows by title."""
        windows = [
            MockDesktopElement(name="Notepad", process_id=2001),
            MockDesktopElement(name="Calculator", process_id=2002),
            MockDesktopElement(name="Notepad++", process_id=2003),
        ]
        execution_context.desktop_context.set_windows(windows)

        node = GetWindowListNode(
            node_id="test_list_filter",
            config={"filter_title": "Notepad"},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window_count"] == 2
        for window_info in result["window_list"]:
            assert "Notepad" in window_info["title"]

    @pytest.mark.asyncio
    async def test_get_window_list_include_invisible(self, execution_context):
        """Test including invisible windows."""
        windows = [
            MockDesktopElement(name="Visible Window", process_id=3001, visible=True),
            MockDesktopElement(name="Hidden Window", process_id=3002, visible=False),
        ]
        execution_context.desktop_context.set_windows(windows)

        node = GetWindowListNode(
            node_id="test_list_invisible",
            config={"include_invisible": True},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window_count"] == 2

    @pytest.mark.asyncio
    async def test_get_window_list_exclude_invisible(self, execution_context):
        """Test excluding invisible windows (default behavior)."""
        windows = [
            MockDesktopElement(name="Visible Window", process_id=4001, visible=True),
            MockDesktopElement(name="Hidden Window", process_id=4002, visible=False),
        ]
        execution_context.desktop_context.set_windows(windows)

        node = GetWindowListNode(
            node_id="test_list_visible_only",
            config={"include_invisible": False},
        )

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["window_count"] == 1
        assert result["window_list"][0]["title"] == "Visible Window"


# =============================================================================
# ExecutionResult Pattern Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Verify all nodes return proper ExecutionResult dictionaries."""

    @pytest.mark.asyncio
    async def test_launch_returns_expected_keys(self, execution_context):
        """LaunchApplicationNode returns all required keys."""
        node = LaunchApplicationNode(node_id="test_result")
        node.set_input_value("application_path", "C:\\Windows\\notepad.exe")

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "window" in result
        assert "process_id" in result
        assert "window_title" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_close_returns_expected_keys(self, execution_context):
        """CloseApplicationNode returns all required keys."""
        mock_window = MockDesktopElement()
        node = CloseApplicationNode(node_id="test_result")
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_activate_returns_expected_keys(self, execution_context):
        """ActivateWindowNode returns all required keys."""
        mock_window = MockDesktopElement()
        node = ActivateWindowNode(node_id="test_result")
        node.set_input_value("window", mock_window)

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "window" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_get_list_returns_expected_keys(self, execution_context):
        """GetWindowListNode returns all required keys."""
        execution_context.desktop_context.set_windows([])
        node = GetWindowListNode(node_id="test_result")

        result = await node.execute(execution_context)

        assert isinstance(result, dict)
        assert "success" in result
        assert "window_list" in result
        assert "window_count" in result
        assert "next_nodes" in result


# =============================================================================
# Node Configuration Tests
# =============================================================================


class TestNodeConfiguration:
    """Test node configuration and defaults."""

    def test_launch_application_default_config(self):
        """Test LaunchApplicationNode default configuration."""
        node = LaunchApplicationNode(node_id="test")

        assert node.config.get("timeout") == 10.0
        assert node.config.get("window_title_hint") == ""
        assert node.config.get("window_state") == "normal"

    def test_close_application_default_config(self):
        """Test CloseApplicationNode default configuration."""
        node = CloseApplicationNode(node_id="test")

        assert node.config.get("force_close") is False
        assert node.config.get("timeout") == 5.0

    def test_activate_window_default_config(self):
        """Test ActivateWindowNode default configuration."""
        node = ActivateWindowNode(node_id="test")

        assert node.config.get("match_partial") is True
        assert node.config.get("timeout") == 5.0

    def test_get_window_list_default_config(self):
        """Test GetWindowListNode default configuration."""
        node = GetWindowListNode(node_id="test")

        assert node.config.get("include_invisible") is False
        assert node.config.get("filter_title") == ""


# =============================================================================
# Port Definition Tests
# =============================================================================


class TestPortDefinitions:
    """Test that all nodes have correct port definitions."""

    def test_launch_application_ports(self):
        """Test LaunchApplicationNode port definitions."""
        node = LaunchApplicationNode(node_id="test")

        assert "exec_in" in node.input_ports
        assert "application_path" in node.input_ports
        assert "arguments" in node.input_ports
        assert "working_directory" in node.input_ports

        assert "exec_out" in node.output_ports
        assert "window" in node.output_ports
        assert "process_id" in node.output_ports
        assert "window_title" in node.output_ports

    def test_close_application_ports(self):
        """Test CloseApplicationNode port definitions."""
        node = CloseApplicationNode(node_id="test")

        assert "exec_in" in node.input_ports
        assert "window" in node.input_ports
        assert "process_id" in node.input_ports
        assert "window_title" in node.input_ports

        assert "exec_out" in node.output_ports
        assert "success" in node.output_ports

    def test_activate_window_ports(self):
        """Test ActivateWindowNode port definitions."""
        node = ActivateWindowNode(node_id="test")

        assert "exec_in" in node.input_ports
        assert "window" in node.input_ports
        assert "window_title" in node.input_ports

        assert "exec_out" in node.output_ports
        assert "success" in node.output_ports
        assert "window" in node.output_ports

    def test_get_window_list_ports(self):
        """Test GetWindowListNode port definitions."""
        node = GetWindowListNode(node_id="test")

        assert "exec_in" in node.input_ports

        assert "exec_out" in node.output_ports
        assert "window_list" in node.output_ports
        assert "window_count" in node.output_ports


# =============================================================================
# Node Metadata Tests
# =============================================================================


class TestNodeMetadata:
    """Test node metadata and type information."""

    def test_launch_application_metadata(self):
        """Test LaunchApplicationNode metadata."""
        node = LaunchApplicationNode(node_id="test")

        assert node.node_type == "LaunchApplicationNode"
        assert node.NODE_NAME == "Launch Application"
        assert node.__identifier__ == "casare_rpa.nodes.desktop"

    def test_close_application_metadata(self):
        """Test CloseApplicationNode metadata."""
        node = CloseApplicationNode(node_id="test")

        assert node.node_type == "CloseApplicationNode"
        assert node.NODE_NAME == "Close Application"

    def test_activate_window_metadata(self):
        """Test ActivateWindowNode metadata."""
        node = ActivateWindowNode(node_id="test")

        assert node.node_type == "ActivateWindowNode"
        assert node.NODE_NAME == "Activate Window"

    def test_get_window_list_metadata(self):
        """Test GetWindowListNode metadata."""
        node = GetWindowListNode(node_id="test")

        assert node.node_type == "GetWindowListNode"
        assert node.NODE_NAME == "Get Window List"
