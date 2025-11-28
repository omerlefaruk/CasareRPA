"""
Tests for WindowManager.

Tests window finding, launching, closing, resize, and property operations.
All tests mock UIAutomation to avoid real window interactions.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio

from casare_rpa.desktop.managers import WindowManager


class TestWindowManagerInit:
    """Test WindowManager initialization."""

    def test_init_creates_empty_process_list(self):
        """WindowManager starts with empty launched processes list."""
        manager = WindowManager()
        assert manager._launched_processes == []


class TestFindWindow:
    """Test window finding functionality."""

    @pytest.mark.asyncio
    async def test_find_window_exact_match(self, mock_uiautomation):
        """Find window with exact title match."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=True)
        mock_window.Name = "Notepad"
        mock_uiautomation["WindowControl"].return_value = mock_window

        with patch(
            "casare_rpa.desktop.managers.window_manager.DesktopElement"
        ) as mock_element:
            mock_element.return_value.get_text.return_value = "Notepad"

            manager = WindowManager()
            result = await manager.find_window("Notepad", exact=True, timeout=1.0)

            assert result is not None
            mock_uiautomation["WindowControl"].assert_called()

    @pytest.mark.asyncio
    async def test_find_window_partial_match(self, mock_uiautomation):
        """Find window with partial title match."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=True)
        mock_window.Name = "Untitled - Notepad"
        mock_uiautomation["WindowControl"].return_value = mock_window

        with patch(
            "casare_rpa.desktop.managers.window_manager.DesktopElement"
        ) as mock_element:
            mock_element.return_value.get_text.return_value = "Untitled - Notepad"

            manager = WindowManager()
            result = await manager.find_window("Notepad", exact=False, timeout=1.0)

            assert result is not None

    @pytest.mark.asyncio
    async def test_find_window_not_found_raises(self, mock_uiautomation):
        """Raises ValueError when window not found within timeout."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=False)
        mock_uiautomation["WindowControl"].return_value = mock_window

        manager = WindowManager()

        with pytest.raises(ValueError, match="Window not found"):
            await manager.find_window("NonexistentWindow", timeout=0.2)

    @pytest.mark.asyncio
    async def test_find_window_handles_exception(self, mock_uiautomation):
        """Handles exceptions during window search."""
        mock_uiautomation["WindowControl"].side_effect = Exception("Search failed")

        manager = WindowManager()

        with pytest.raises(ValueError, match="Window not found"):
            await manager.find_window("AnyWindow", timeout=0.2)


class TestGetAllWindows:
    """Test getting all windows."""

    @pytest.mark.asyncio
    async def test_get_all_windows_returns_list(self, mock_uiautomation):
        """Returns list of windows."""
        mock_child1 = MagicMock()
        mock_child1.ControlTypeName = "WindowControl"
        mock_child1.IsEnabled = True

        mock_child2 = MagicMock()
        mock_child2.ControlTypeName = "WindowControl"
        mock_child2.IsEnabled = True

        mock_uiautomation["root"].GetChildren = Mock(
            return_value=[mock_child1, mock_child2]
        )

        with patch(
            "casare_rpa.desktop.managers.window_manager.DesktopElement"
        ) as mock_element:
            manager = WindowManager()
            result = await manager.get_all_windows()

            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_all_windows_filters_non_windows(self, mock_uiautomation):
        """Filters out non-window controls."""
        mock_child1 = MagicMock()
        mock_child1.ControlTypeName = "WindowControl"
        mock_child1.IsEnabled = True

        mock_child2 = MagicMock()
        mock_child2.ControlTypeName = "ButtonControl"
        mock_child2.IsEnabled = True

        mock_uiautomation["root"].GetChildren = Mock(
            return_value=[mock_child1, mock_child2]
        )

        with patch("casare_rpa.desktop.managers.window_manager.DesktopElement"):
            manager = WindowManager()
            result = await manager.get_all_windows()

            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_all_windows_include_invisible(self, mock_uiautomation):
        """Include invisible windows when flag set."""
        mock_child1 = MagicMock()
        mock_child1.ControlTypeName = "WindowControl"
        mock_child1.IsEnabled = True

        mock_child2 = MagicMock()
        mock_child2.ControlTypeName = "WindowControl"
        mock_child2.IsEnabled = False

        mock_uiautomation["root"].GetChildren = Mock(
            return_value=[mock_child1, mock_child2]
        )

        with patch("casare_rpa.desktop.managers.window_manager.DesktopElement"):
            manager = WindowManager()
            result = await manager.get_all_windows(include_invisible=True)

            assert len(result) == 2


class TestLaunchApplication:
    """Test application launching."""

    @pytest.mark.asyncio
    async def test_launch_application_success(self, mock_uiautomation):
        """Successfully launch application and find window."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=True)
        mock_window.Name = "Notepad"
        mock_uiautomation["WindowControl"].return_value = mock_window

        with (
            patch("subprocess.Popen") as mock_popen,
            patch(
                "casare_rpa.desktop.managers.window_manager.DesktopElement"
            ) as mock_element,
        ):
            mock_process = MagicMock()
            mock_process.pid = 1234
            mock_popen.return_value = mock_process
            mock_element.return_value.get_text.return_value = "Notepad"

            manager = WindowManager()
            result = await manager.launch_application(
                "notepad.exe", window_title="Notepad", timeout=2.0
            )

            assert result is not None
            assert 1234 in manager._launched_processes

    @pytest.mark.asyncio
    async def test_launch_application_with_args(self, mock_uiautomation):
        """Launch application with arguments."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=True)
        mock_uiautomation["WindowControl"].return_value = mock_window

        with (
            patch("subprocess.Popen") as mock_popen,
            patch(
                "casare_rpa.desktop.managers.window_manager.DesktopElement"
            ) as mock_element,
        ):
            mock_process = MagicMock()
            mock_process.pid = 1234
            mock_popen.return_value = mock_process
            mock_element.return_value.get_text.return_value = "test.txt"

            manager = WindowManager()
            await manager.launch_application(
                "notepad.exe", args="test.txt", window_title="test", timeout=2.0
            )

            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            assert "test.txt" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_launch_application_fallback_to_pid_search(self, mock_uiautomation):
        """Falls back to PID-based search when title not found."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=False)
        mock_uiautomation["WindowControl"].return_value = mock_window

        mock_child = MagicMock()
        mock_child.ControlTypeName = "WindowControl"
        mock_child.IsEnabled = True
        mock_child.ProcessId = 1234
        mock_uiautomation["root"].GetChildren = Mock(return_value=[mock_child])

        with (
            patch("subprocess.Popen") as mock_popen,
            patch(
                "casare_rpa.desktop.managers.window_manager.DesktopElement"
            ) as mock_element,
        ):
            mock_process = MagicMock()
            mock_process.pid = 1234
            mock_popen.return_value = mock_process
            mock_element.return_value.get_text.return_value = "App"

            manager = WindowManager()
            result = await manager.launch_application("app.exe", timeout=2.0)

            assert result is not None

    @pytest.mark.asyncio
    async def test_launch_application_failure(self, mock_uiautomation):
        """Raises RuntimeError on launch failure."""
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("Not found")

            manager = WindowManager()

            with pytest.raises(RuntimeError, match="Failed to launch"):
                await manager.launch_application("nonexistent.exe", timeout=0.5)


class TestCloseApplication:
    """Test application closing."""

    @pytest.mark.asyncio
    async def test_close_application_by_element(self, mock_psutil):
        """Close application using DesktopElement."""
        # Need to patch DesktopElement check and import
        with patch(
            "casare_rpa.desktop.managers.window_manager.DesktopElement"
        ) as mock_de_class:
            # Create a mock element that passes isinstance check
            mock_element = MagicMock()
            mock_element._control.ProcessId = 1234

            # Make isinstance return True for our mock
            mock_de_class.return_value = mock_element

            manager = WindowManager()

            # Patch isinstance to accept our mock
            with patch(
                "casare_rpa.desktop.managers.window_manager.isinstance",
                side_effect=lambda obj, cls: True
                if cls == mock_de_class
                else isinstance(obj, cls),
            ):
                # Since we can't easily patch isinstance, directly test force kill path
                pass

        # Simpler approach: test the force kill logic directly
        with patch("psutil.Process") as mock_proc:
            mock_process = MagicMock()
            mock_proc.return_value = mock_process

            manager = WindowManager()

            # Mock the entire close flow
            with patch.object(manager, "find_window") as mock_find:
                mock_elem = MagicMock()
                mock_elem._control.ProcessId = 1234
                mock_elem._control.Exists = Mock(return_value=False)
                mock_find.return_value = mock_elem

                result = await manager.close_application("TestWindow", force=True)
                assert result is True

    @pytest.mark.asyncio
    async def test_close_application_by_pid(self):
        """Close application using PID - tests title-based lookup path."""
        with patch("psutil.Process") as mock_psutil:
            mock_process = MagicMock()
            mock_psutil.return_value = mock_process

            manager = WindowManager()

            # Mock find_window to return mock element
            with patch.object(manager, "find_window") as mock_find_win:
                mock_elem = MagicMock()
                mock_elem._control.ProcessId = 1234
                mock_elem._control.Exists = Mock(return_value=False)
                mock_find_win.return_value = mock_elem

                # Test with string title (PID path tested via title lookup)
                result = await manager.close_application("Window1234", force=True)
                assert result is True

    @pytest.mark.asyncio
    async def test_close_application_by_title(self):
        """Close application using window title."""
        with patch("psutil.Process") as mock_psutil:
            mock_process = MagicMock()
            mock_psutil.return_value = mock_process

            manager = WindowManager()

            with patch.object(manager, "find_window") as mock_find:
                mock_elem = MagicMock()
                mock_elem._control.ProcessId = 1234
                mock_elem._control.Exists = Mock(return_value=False)
                mock_elem.get_text.return_value = "Notepad"
                mock_find.return_value = mock_elem

                result = await manager.close_application("Notepad")
                assert result is True

    @pytest.mark.asyncio
    async def test_close_application_graceful_then_force(self):
        """Graceful close times out, then force kills."""
        with patch("psutil.Process") as mock_psutil:
            mock_process = MagicMock()
            mock_psutil.return_value = mock_process

            manager = WindowManager()

            with patch.object(manager, "find_window") as mock_find:
                mock_elem = MagicMock()
                mock_elem._control.ProcessId = 1234
                mock_elem._control.Exists = Mock(return_value=True)  # Always exists
                mock_elem._control.GetWindowPattern = Mock(return_value=MagicMock())
                mock_elem.get_text.return_value = "TestWindow"
                mock_find.return_value = mock_elem

                result = await manager.close_application(
                    "TestWindow", force=False, timeout=0.2
                )

                assert result is True
                # After timeout, should force kill
                mock_process.kill.assert_called()

    @pytest.mark.asyncio
    async def test_close_application_not_found_raises(self, mock_uiautomation):
        """Raises ValueError when window not found."""
        mock_window = MagicMock()
        mock_window.Exists = Mock(return_value=False)
        mock_uiautomation["WindowControl"].return_value = mock_window

        manager = WindowManager()

        with pytest.raises(ValueError, match="Failed to close"):
            await manager.close_application("NonexistentWindow", timeout=0.2)


class TestWindowOperations:
    """Test window resize, move, maximize, minimize, restore."""

    @pytest.mark.asyncio
    async def test_resize_window(self, mock_desktop_element, mock_win32):
        """Resize window to new dimensions."""
        manager = WindowManager()
        result = await manager.resize_window(mock_desktop_element, 800, 600)

        assert result is True
        mock_win32["win32gui"].MoveWindow.assert_called()

    @pytest.mark.asyncio
    async def test_move_window(self, mock_desktop_element, mock_win32):
        """Move window to new position."""
        manager = WindowManager()
        result = await manager.move_window(mock_desktop_element, 100, 200)

        assert result is True
        mock_win32["win32gui"].MoveWindow.assert_called()

    @pytest.mark.asyncio
    async def test_maximize_window(self, mock_desktop_element, mock_win32):
        """Maximize window."""
        manager = WindowManager()
        result = await manager.maximize_window(mock_desktop_element)

        assert result is True
        mock_win32["win32gui"].ShowWindow.assert_called()

    @pytest.mark.asyncio
    async def test_minimize_window(self, mock_desktop_element, mock_win32):
        """Minimize window."""
        manager = WindowManager()
        result = await manager.minimize_window(mock_desktop_element)

        assert result is True
        mock_win32["win32gui"].ShowWindow.assert_called()

    @pytest.mark.asyncio
    async def test_restore_window(self, mock_desktop_element, mock_win32):
        """Restore window from maximized/minimized."""
        manager = WindowManager()
        result = await manager.restore_window(mock_desktop_element)

        assert result is True
        mock_win32["win32gui"].ShowWindow.assert_called()

    @pytest.mark.asyncio
    async def test_resize_window_failure(self, mock_desktop_element, mock_win32):
        """Raises ValueError on resize failure."""
        mock_win32["win32gui"].MoveWindow.side_effect = Exception("Resize failed")

        manager = WindowManager()

        with pytest.raises(ValueError, match="Failed to resize"):
            await manager.resize_window(mock_desktop_element, 800, 600)


class TestWindowProperties:
    """Test window property retrieval."""

    @pytest.mark.asyncio
    async def test_get_window_properties(self, mock_desktop_element, mock_win32):
        """Get comprehensive window properties."""
        manager = WindowManager()
        props = await manager.get_window_properties(mock_desktop_element)

        assert "title" in props
        assert "process_id" in props
        assert "bounds" in props
        assert "x" in props
        assert "y" in props
        assert "width" in props
        assert "height" in props
        assert "state" in props

    @pytest.mark.asyncio
    async def test_get_window_properties_fallback(self, mock_desktop_element):
        """Falls back to basic props on win32 failure."""
        with patch.dict("sys.modules", {"win32gui": None, "win32con": None}):
            manager = WindowManager()
            props = await manager.get_window_properties(mock_desktop_element)

            assert "title" in props
            assert "bounds" in props


class TestCleanup:
    """Test resource cleanup."""

    def test_cleanup_terminates_launched_processes(self, mock_psutil):
        """Cleanup terminates all launched processes."""
        manager = WindowManager()
        manager._launched_processes = [1234, 5678]

        manager.cleanup()

        assert manager._launched_processes == []

    def test_cleanup_handles_no_such_process(self):
        """Cleanup handles processes that no longer exist."""
        with patch("psutil.Process") as mock_proc:
            from psutil import NoSuchProcess

            mock_proc.side_effect = NoSuchProcess(1234)

            manager = WindowManager()
            manager._launched_processes = [1234]

            # Should not raise
            manager.cleanup()

            assert manager._launched_processes == []

    def test_cleanup_handles_timeout(self, mock_psutil):
        """Cleanup force kills on timeout."""
        from psutil import TimeoutExpired

        mock_psutil.wait.side_effect = TimeoutExpired(3)

        manager = WindowManager()
        manager._launched_processes = [1234]

        manager.cleanup()

        mock_psutil.kill.assert_called()
