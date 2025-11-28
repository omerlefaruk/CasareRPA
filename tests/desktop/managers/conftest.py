"""
Shared fixtures for desktop manager tests.

Provides mocks for UIAutomation, win32gui, and other Windows APIs.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from typing import Any, Dict, List, Optional


class MockRect:
    """Mock rectangle object."""

    def __init__(
        self, left: int = 100, top: int = 100, right: int = 500, bottom: int = 400
    ):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def width(self) -> int:
        return self.right - self.left

    def height(self) -> int:
        return self.bottom - self.top


class MockUIControl:
    """Mock UIAutomation Control for testing."""

    def __init__(
        self,
        name: str = "TestWindow",
        control_type: str = "WindowControl",
        process_id: int = 1234,
        class_name: str = "TestClass",
        automation_id: str = "test_auto_id",
        is_enabled: bool = True,
        handle: int = 12345,
    ):
        self.Name = name
        self.ControlTypeName = control_type
        self.ProcessId = process_id
        self.ClassName = class_name
        self.AutomationId = automation_id
        self.IsEnabled = is_enabled
        self.NativeWindowHandle = handle
        self.BoundingRectangle = MockRect()
        self._exists = True
        self._children: List["MockUIControl"] = []

        # Pattern mocks
        self._toggle_pattern = Mock()
        self._toggle_pattern.ToggleState = 0  # Off
        self._toggle_pattern.Toggle = Mock()

        self._expand_pattern = Mock()
        self._expand_pattern.ExpandCollapseState = 1  # Collapsed
        self._expand_pattern.Expand = Mock()
        self._expand_pattern.Collapse = Mock()

        self._selection_pattern = Mock()
        self._selection_item_pattern = Mock()
        self._selection_item_pattern.Select = Mock()

        self._value_pattern = Mock()
        self._value_pattern.Value = ""
        self._value_pattern.IsReadOnly = False
        self._value_pattern.SetValue = Mock()

        self._scroll_pattern = Mock()
        self._scroll_pattern.HorizontalScrollPercent = 0
        self._scroll_pattern.VerticalScrollPercent = 0
        self._scroll_pattern.SetScrollPercent = Mock()

        self._window_pattern = Mock()
        self._window_pattern.Close = Mock()

    def Exists(self, timeout: float = 0, interval: float = 0) -> bool:
        return self._exists

    def SetFocus(self) -> None:
        pass

    def Click(self, x: int = None, y: int = None, simulateMove: bool = False) -> None:
        pass

    def DoubleClick(self, x: int = None, y: int = None) -> None:
        pass

    def SendKeys(self, keys: str, interval: float = 0) -> None:
        pass

    def GetChildren(self) -> List["MockUIControl"]:
        return self._children

    def GetTogglePattern(self) -> Mock:
        return self._toggle_pattern

    def GetExpandCollapsePattern(self) -> Mock:
        return self._expand_pattern

    def GetSelectionPattern(self) -> Mock:
        return self._selection_pattern

    def GetSelectionItemPattern(self) -> Mock:
        return self._selection_item_pattern

    def GetValuePattern(self) -> Mock:
        return self._value_pattern

    def GetScrollPattern(self) -> Mock:
        return self._scroll_pattern

    def GetWindowPattern(self) -> Mock:
        return self._window_pattern


class MockDesktopElement:
    """Mock DesktopElement for manager tests."""

    def __init__(
        self,
        name: str = "TestElement",
        enabled: bool = True,
        visible: bool = True,
        exists: bool = True,
        rect: Optional[Dict[str, int]] = None,
    ):
        self._name = name
        self._enabled = enabled
        self._visible = visible
        self._exists_val = exists
        self._rect = rect or {"left": 100, "top": 100, "width": 400, "height": 300}

        # Create mock control
        self._control = MockUIControl(name=name, is_enabled=enabled)
        self._control._exists = exists

    def get_text(self) -> str:
        return self._name

    def get_property(self, prop: str) -> Any:
        props = {
            "ProcessId": self._control.ProcessId,
            "AutomationId": self._control.AutomationId,
        }
        return props.get(prop)

    def is_enabled(self) -> bool:
        return self._enabled

    def is_visible(self) -> bool:
        return self._visible

    def exists(self) -> bool:
        return self._exists_val

    def get_bounding_rect(self) -> Dict[str, int]:
        return self._rect

    def click(self) -> bool:
        return True


@pytest.fixture
def mock_ui_control() -> MockUIControl:
    """Create mock UIAutomation control."""
    return MockUIControl()


@pytest.fixture
def mock_desktop_element() -> MockDesktopElement:
    """Create mock desktop element."""
    return MockDesktopElement()


@pytest.fixture
def mock_window_element() -> MockDesktopElement:
    """Create mock window element."""
    return MockDesktopElement(name="TestWindow")


@pytest.fixture
def mock_uiautomation():
    """Patch uiautomation module."""
    with (
        patch("uiautomation.WindowControl") as mock_window,
        patch("uiautomation.GetRootControl") as mock_root,
        patch("uiautomation.Click") as mock_click,
        patch("uiautomation.RightClick") as mock_rclick,
        patch("uiautomation.MiddleClick") as mock_mclick,
        patch("uiautomation.WheelDown") as mock_wdown,
        patch("uiautomation.WheelUp") as mock_wup,
        patch("uiautomation.SendKeys") as mock_send,
    ):
        root_control = MockUIControl(name="Desktop", control_type="PaneControl")
        mock_root.return_value = root_control

        yield {
            "WindowControl": mock_window,
            "GetRootControl": mock_root,
            "Click": mock_click,
            "RightClick": mock_rclick,
            "MiddleClick": mock_mclick,
            "WheelDown": mock_wdown,
            "WheelUp": mock_wup,
            "SendKeys": mock_send,
            "root": root_control,
        }


@pytest.fixture
def mock_win32():
    """Patch win32gui and win32con modules."""
    mock_win32gui = MagicMock()
    mock_win32con = MagicMock()

    # Window states
    mock_win32con.SW_HIDE = 0
    mock_win32con.SW_MINIMIZE = 6
    mock_win32con.SW_MAXIMIZE = 3
    mock_win32con.SW_RESTORE = 9
    mock_win32con.SW_SHOW = 5
    mock_win32con.SW_SHOWMINIMIZED = 2
    mock_win32con.SW_SHOWMAXIMIZED = 3
    mock_win32con.SW_SHOWNOACTIVATE = 4
    mock_win32con.SW_SHOWNORMAL = 1

    # Window styles
    mock_win32con.GWL_STYLE = -16
    mock_win32con.WS_MAXIMIZE = 0x01000000
    mock_win32con.WS_MINIMIZE = 0x20000000
    mock_win32con.WS_THICKFRAME = 0x00040000
    mock_win32con.WS_CAPTION = 0x00C00000

    mock_win32gui.GetWindowPlacement = Mock(
        return_value=(0, 1, (0, 0), (0, 0), (0, 0, 100, 100))
    )
    mock_win32gui.GetWindowLong = Mock(return_value=0)
    mock_win32gui.MoveWindow = Mock()
    mock_win32gui.ShowWindow = Mock()

    with patch.dict(
        "sys.modules",
        {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        },
    ):
        yield {
            "win32gui": mock_win32gui,
            "win32con": mock_win32con,
        }


@pytest.fixture
def mock_ctypes():
    """Patch ctypes for mouse/keyboard operations."""
    with (
        patch("ctypes.windll.user32.SetCursorPos") as mock_cursor,
        patch("ctypes.windll.user32.GetCursorPos") as mock_getcursor,
        patch("ctypes.windll.user32.mouse_event") as mock_mouse,
        patch("ctypes.windll.user32.keybd_event") as mock_keybd,
    ):
        yield {
            "SetCursorPos": mock_cursor,
            "GetCursorPos": mock_getcursor,
            "mouse_event": mock_mouse,
            "keybd_event": mock_keybd,
        }


@pytest.fixture
def mock_pil():
    """Patch PIL for screen capture tests."""
    mock_image = MagicMock()
    mock_image.size = (1920, 1080)
    mock_image.mode = "RGB"
    mock_image.save = Mock()
    mock_image.histogram = Mock(return_value=[0] * 768)
    mock_image.crop = Mock(return_value=mock_image)
    mock_image.resize = Mock(return_value=mock_image)
    mock_image.convert = Mock(return_value=mock_image)

    mock_grab = Mock(return_value=mock_image)

    with (
        patch("PIL.ImageGrab.grab", mock_grab),
        patch("PIL.Image.open", Mock(return_value=mock_image)),
    ):
        yield {
            "image": mock_image,
            "grab": mock_grab,
        }


@pytest.fixture
def mock_psutil():
    """Patch psutil for process management."""
    mock_process = MagicMock()
    mock_process.is_running = Mock(return_value=True)
    mock_process.terminate = Mock()
    mock_process.kill = Mock()
    mock_process.wait = Mock()

    with patch("psutil.Process", return_value=mock_process):
        yield mock_process
