"""
Desktop automation test fixtures.

Provides:
- MockDesktopElement: Mock UIAutomation element for testing
- MockDesktopContext: Mock DesktopResourceManager for testing
- Fixtures for common desktop testing scenarios

Used by all desktop automation node tests (application, interaction, mouse/keyboard, elements).
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Any, Dict, List, Optional


class MockDesktopElement:
    """
    Mock DesktopElement for testing without system interaction.

    Simulates a UIAutomation element with configurable properties.
    Supports:
    - Text/name retrieval
    - Property queries
    - Enabled/visible states
    - Bounding rectangle
    - Click, type, find operations
    - Mock underlying control object

    Attributes:
        _name: Element text/display name
        _process_id: Associated process ID
        _automation_id: UIAutomation automation ID
        _enabled: Element enabled state
        _visible: Element visibility state
        _control: Mock underlying control object
    """

    def __init__(
        self,
        name: str = "TestElement",
        process_id: int = 1234,
        automation_id: str = "auto_id",
        enabled: bool = True,
        visible: bool = True,
        exists: bool = True,
    ):
        """
        Initialize mock desktop element.

        Args:
            name: Element text/display name.
            process_id: Associated process ID.
            automation_id: UIAutomation automation ID.
            enabled: Whether element is enabled.
            visible: Whether element is visible.
            exists: Whether element exists (for interaction testing).
        """
        self._name = name
        self._process_id = process_id
        self._automation_id = automation_id
        self._enabled = enabled
        self._visible = visible
        self._exists = exists
        self._clicked = False
        self._typed_text = None
        self._control = Mock()
        self._control.ProcessId = process_id
        self._control.SetFocus = Mock()
        self._control.NativeWindowHandle = 12345
        self._control.GetWindowPattern = Mock(return_value=Mock())
        self._control.Name = name
        self._control.BoundingRectangle = Mock(
            left=100,
            top=100,
            right=200,
            bottom=150,
            width=lambda: 100,
            height=lambda: 50,
        )
        self._control.IsEnabled = enabled

    def get_text(self) -> str:
        """Get element text/display name."""
        return self._name

    def get_property(self, prop: str) -> Any:
        """
        Get element property by name.

        Supports:
            - ProcessId: Associated process ID
            - AutomationId: UIAutomation automation ID
        """
        props = {
            "ProcessId": self._process_id,
            "AutomationId": self._automation_id,
        }
        return props.get(prop)

    def is_enabled(self) -> bool:
        """Check if element is enabled."""
        return self._enabled

    def is_visible(self) -> bool:
        """Check if element is visible."""
        return self._visible

    def get_bounding_rect(self) -> Dict[str, int]:
        """Get element bounding rectangle."""
        return {"left": 0, "top": 0, "width": 800, "height": 600}

    def click(
        self, simulate: bool = False, x_offset: int = 0, y_offset: int = 0
    ) -> bool:
        """Mock click operation."""
        if not self._exists:
            raise RuntimeError("Element does not exist")
        self._clicked = True
        return True

    def type_text(
        self, text: str, clear_first: bool = False, interval: float = 0.01
    ) -> bool:
        """Mock type text operation."""
        if not self._exists:
            raise RuntimeError("Element does not exist")
        self._typed_text = text
        return True

    def exists(self) -> bool:
        """Check if element exists."""
        return self._exists

    def find_child(
        self, selector: Any, timeout: float = 5.0
    ) -> Optional["MockDesktopElement"]:
        """Find child element."""
        return MockDesktopElement(name="ChildElement")


class MockDesktopContext:
    """
    Mock DesktopResourceManager for testing.

    Simulates Windows desktop automation without system interaction.
    Supports:
    - Application launch/close
    - Window finding and activation
    - Mouse/keyboard operations
    - Window list retrieval

    Configurable for:
    - Success/failure scenarios
    - Timeout simulation
    - File not found errors
    """

    def __init__(self):
        """Initialize mock desktop context."""
        self._launched_windows: List[MockDesktopElement] = []
        self._all_windows: List[MockDesktopElement] = []
        self._should_fail = False
        self._fail_message = "Mock failure"
        self._launch_timeout = False
        self._file_not_found = False
        self.move_mouse_calls: List[Dict[str, Any]] = []
        self.click_mouse_calls: List[Dict[str, Any]] = []
        self.send_keys_calls: List[Dict[str, Any]] = []
        self.send_hotkey_calls: List[List[str]] = []
        self._hotkeys_sent: List[List[str]] = []
        self.drag_mouse_calls: List[Dict[str, Any]] = []
        self._mouse_position = (100, 200)
        self._click_calls: List[Dict[str, Any]] = []
        self._keys_sent: List[Dict[str, Any]] = []
        self._dropdown_selections: List[Dict[str, Any]] = []
        self._checkbox_states: Dict[int, bool] = {}

    def set_windows(self, windows: List[MockDesktopElement]) -> None:
        """Set mock windows for get_all_windows."""
        self._all_windows = windows

    def set_should_fail(self, should_fail: bool, message: str = "Mock failure") -> None:
        """Configure context to fail operations."""
        self._should_fail = should_fail
        self._fail_message = message

    def set_launch_timeout(self, timeout: bool) -> None:
        """Configure launch to timeout."""
        self._launch_timeout = timeout

    def set_file_not_found(self, not_found: bool) -> None:
        """Configure launch to raise FileNotFoundError."""
        self._file_not_found = not_found

    async def async_launch_application(
        self,
        path: str,
        args: str = "",
        working_dir: Optional[str] = None,
        timeout: float = 10.0,
        window_title: Optional[str] = None,
    ) -> MockDesktopElement:
        """Mock async launch application."""
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
        """Mock async close application."""
        if self._should_fail:
            raise ValueError(self._fail_message)
        return True

    async def async_find_window(
        self,
        title: str,
        exact: bool = False,
        timeout: float = 5.0,
    ) -> Optional[MockDesktopElement]:
        """Mock async find window."""
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
        """Get all mock windows."""
        if include_invisible:
            return self._all_windows
        return [w for w in self._all_windows if w.is_visible()]

    def move_mouse(self, x: int, y: int, duration: float = 0.0, **kwargs) -> bool:
        """Mock move mouse operation."""
        if self._should_fail:
            return False
        self.move_mouse_calls.append({"x": x, "y": y, "duration": duration, **kwargs})
        self._mouse_position = (x, y)
        return True

    def click_mouse(
        self,
        x: int = None,
        y: int = None,
        button: str = "left",
        click_type: str = "single",
        **kwargs,
    ) -> bool:
        """Mock click mouse operation."""
        if self._should_fail:
            return False
        click_call = {
            "x": x,
            "y": y,
            "button": button,
            "click_type": click_type,
            **kwargs,
        }
        self.click_mouse_calls.append(click_call)
        self._click_calls.append(click_call)
        return True

    def send_keys(self, keys: str, interval: float = 0.0) -> bool:
        """Mock send keys operation."""
        if self._should_fail:
            return False
        keys_call = {"keys": keys, "interval": interval}
        self.send_keys_calls.append(keys_call)
        self._keys_sent.append(keys_call)
        return True

    def send_hotkey(self, *keys: str) -> bool:
        """Mock send hotkey operation."""
        if self._should_fail:
            return False
        keys_list = list(keys)
        self.send_hotkey_calls.append(keys_list)
        self._hotkeys_sent.append(keys_list)
        return True

    def get_mouse_position(self) -> tuple:
        """Get current mouse position."""
        return self._mouse_position

    def drag_mouse(
        self,
        start_x: int,
        start_y: int,
        end_x: int,
        end_y: int,
        button: str = "left",
        duration: float = 0.5,
    ) -> bool:
        """Mock drag mouse operation."""
        if self._should_fail:
            return False
        self.drag_mouse_calls.append(
            {
                "start_x": start_x,
                "start_y": start_y,
                "end_x": end_x,
                "end_y": end_y,
                "button": button,
                "duration": duration,
            }
        )
        return True

    def select_from_dropdown(
        self, element: Any, value: str, by_text: bool = True
    ) -> bool:
        """Mock select from dropdown operation."""
        if self._should_fail:
            return False
        self._dropdown_selections.append(
            {"element": element, "value": value, "by_text": by_text}
        )
        return True

    def check_checkbox(self, element: Any, check: bool = True) -> bool:
        """Mock check/uncheck checkbox operation."""
        if self._should_fail:
            return False
        self._checkbox_states[id(element)] = check
        return True


@pytest.fixture
def mock_desktop_context() -> MockDesktopContext:
    """
    Create a mock desktop context for testing desktop automation nodes.

    Returns:
        Configured MockDesktopContext ready for use in tests.

    Usage:
        def test_launch_app(mock_desktop_context):
            node = LaunchApplicationNode()
            context = Mock()
            context.desktop_context = mock_desktop_context
            result = await node.execute(context)
    """
    return MockDesktopContext()


@pytest.fixture
def mock_desktop_element() -> MockDesktopElement:
    """
    Create a default mock desktop element.

    Returns:
        MockDesktopElement with sensible defaults.

    Usage:
        def test_element_interaction(mock_desktop_element):
            mock_desktop_element.get_text()  # Returns "TestElement"
    """
    return MockDesktopElement()


@pytest.fixture
def execution_context_with_desktop(mock_desktop_context) -> Mock:
    """
    Create execution context with mock desktop context.

    Provides ExecutionContext pre-configured for desktop automation testing.

    Args:
        mock_desktop_context: Mock desktop context fixture.

    Returns:
        Mock ExecutionContext with desktop_context property set.

    Usage:
        def test_desktop_node(execution_context_with_desktop):
            node = DesktopNode()
            result = await node.execute(execution_context_with_desktop)
    """
    context = Mock()
    context.desktop_context = mock_desktop_context
    context.resolve_value = lambda x: x
    context.variables = {}
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    return context


@pytest.fixture
def execution_context_no_desktop() -> Mock:
    """
    Create execution context without desktop context.

    Useful for testing error handling when desktop context is unavailable.

    Returns:
        Mock ExecutionContext with no desktop_context property.

    Usage:
        def test_desktop_node_no_context(execution_context_no_desktop):
            # Test error handling when desktop context is missing
            result = await node.execute(execution_context_no_desktop)
    """
    context = Mock(spec=[])
    context.resolve_value = lambda x: x
    context.variables = {}
    return context


@pytest.fixture
def execution_context(mock_desktop_context) -> Mock:
    """
    Create execution context with mock desktop context.

    Alias for execution_context_with_desktop for backwards compatibility.

    Args:
        mock_desktop_context: Mock desktop context fixture.

    Returns:
        Mock ExecutionContext with desktop_context property set.

    Usage:
        def test_desktop_node(execution_context):
            node = DesktopNode()
            result = await node.execute(execution_context)
    """
    context = Mock()
    context.desktop_context = mock_desktop_context
    context.resolve_value = lambda x: x
    context.variables = {}
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )
    return context


@pytest.fixture
def mock_element() -> MockDesktopElement:
    """
    Create a default mock desktop element fixture.

    Returns:
        MockDesktopElement with default configuration.

    Usage:
        def test_element(mock_element):
            assert mock_element.get_text() == "TestElement"
    """
    return MockDesktopElement()


@pytest.fixture
def mock_window() -> MockDesktopElement:
    """
    Create a mock window element fixture.

    Returns:
        MockDesktopElement configured as a window.

    Usage:
        def test_window(mock_window):
            assert mock_window.get_text() == "TestWindow"
    """
    return MockDesktopElement(name="TestWindow")
