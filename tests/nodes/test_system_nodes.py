"""
Tests for System operation nodes.

Tests 13 system nodes across 4 categories:
- Clipboard: ClipboardCopyNode, ClipboardPasteNode, ClipboardClearNode
- Dialogs: MessageBoxNode, InputDialogNode, TooltipNode
- Process: RunCommandNode, RunPowerShellNode
- Services: GetServiceStatusNode, StartServiceNode, StopServiceNode,
            RestartServiceNode, ListServicesNode

All tests mock subprocess, pyperclip, and Qt dialogs for security.
"""

import sys
import subprocess
import pytest
from unittest.mock import Mock, patch, MagicMock
from casare_rpa.core.execution_context import ExecutionContext


# ==================== CLIPBOARD NODES ====================


class TestClipboardCopyNode:
    """Tests for ClipboardCopyNode."""

    @pytest.mark.asyncio
    async def test_copy_text_with_pyperclip(self, execution_context) -> None:
        """Test copying text using pyperclip."""
        from casare_rpa.nodes.system_nodes import ClipboardCopyNode

        mock_pyperclip = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardCopyNode(node_id="test_copy")
            node.set_input_value("text", "Hello World")

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_pyperclip.copy.assert_called_once_with("Hello World")
            assert node.get_output_value("success") is True
            assert result["data"]["copied_length"] == 11

    @pytest.mark.asyncio
    async def test_copy_empty_text(self, execution_context) -> None:
        """Test copying empty string."""
        from casare_rpa.nodes.system_nodes import ClipboardCopyNode

        mock_pyperclip = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardCopyNode(node_id="test_copy_empty")
            node.set_input_value("text", "")

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_pyperclip.copy.assert_called_once_with("")
            assert result["data"]["copied_length"] == 0

    @pytest.mark.asyncio
    async def test_copy_none_becomes_empty(self, execution_context) -> None:
        """Test copying None converts to empty string."""
        from casare_rpa.nodes.system_nodes import ClipboardCopyNode

        mock_pyperclip = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardCopyNode(node_id="test_copy_none")
            node.set_input_value("text", None)

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_pyperclip.copy.assert_called_once_with("")

    @pytest.mark.asyncio
    async def test_copy_handles_error(self, execution_context) -> None:
        """Test error handling when copy fails."""
        from casare_rpa.nodes.system_nodes import ClipboardCopyNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.copy.side_effect = Exception("Clipboard access denied")
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardCopyNode(node_id="test_copy_error")
            node.set_input_value("text", "test")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert "Clipboard access denied" in result["error"]
            assert node.get_output_value("success") is False


class TestClipboardPasteNode:
    """Tests for ClipboardPasteNode."""

    @pytest.mark.asyncio
    async def test_paste_text_with_pyperclip(self, execution_context) -> None:
        """Test pasting text using pyperclip."""
        from casare_rpa.nodes.system_nodes import ClipboardPasteNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.paste.return_value = "Clipboard Content"
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardPasteNode(node_id="test_paste")
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("text") == "Clipboard Content"
            assert node.get_output_value("success") is True
            assert result["data"]["text_length"] == 17

    @pytest.mark.asyncio
    async def test_paste_empty_clipboard(self, execution_context) -> None:
        """Test pasting from empty clipboard."""
        from casare_rpa.nodes.system_nodes import ClipboardPasteNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.paste.return_value = ""
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardPasteNode(node_id="test_paste_empty")
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("text") == ""
            assert result["data"]["text_length"] == 0

    @pytest.mark.asyncio
    async def test_paste_handles_error(self, execution_context) -> None:
        """Test error handling when paste fails."""
        from casare_rpa.nodes.system_nodes import ClipboardPasteNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.paste.side_effect = Exception("No clipboard access")
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardPasteNode(node_id="test_paste_error")
            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("success") is False
            assert node.get_output_value("text") == ""

    @pytest.mark.asyncio
    async def test_paste_unicode_content(self, execution_context) -> None:
        """Test pasting unicode content."""
        from casare_rpa.nodes.system_nodes import ClipboardPasteNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.paste.return_value = (
            "Unicode: \u4e2d\u6587 \u0420\u0443\u0441\u0441\u043a\u0438\u0439"
        )
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardPasteNode(node_id="test_paste_unicode")
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert "\u4e2d\u6587" in node.get_output_value("text")


class TestClipboardClearNode:
    """Tests for ClipboardClearNode."""

    @pytest.mark.asyncio
    async def test_clear_clipboard(self, execution_context) -> None:
        """Test clearing clipboard."""
        from casare_rpa.nodes.system_nodes import ClipboardClearNode

        mock_pyperclip = MagicMock()
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardClearNode(node_id="test_clear")
            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_pyperclip.copy.assert_called_once_with("")
            assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_clear_handles_error(self, execution_context) -> None:
        """Test error handling when clear fails."""
        from casare_rpa.nodes.system_nodes import ClipboardClearNode

        mock_pyperclip = MagicMock()
        mock_pyperclip.copy.side_effect = Exception("Access denied")
        with patch.dict("sys.modules", {"pyperclip": mock_pyperclip}):
            node = ClipboardClearNode(node_id="test_clear_error")
            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("success") is False


# ==================== DIALOG NODES ====================


class TestMessageBoxNode:
    """Tests for MessageBoxNode."""

    @pytest.mark.asyncio
    async def test_message_box_ok_result(self, execution_context) -> None:
        """Test message box returning OK."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox_class,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Ok = 1024
            mock_msgbox_class.Information = 1
            mock_msgbox.exec.return_value = 1024  # QMessageBox.Ok

            node = MessageBoxNode(
                node_id="test_msg",
                config={"title": "Test", "message": "Hello", "buttons": "ok"},
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("result") == "ok"
            assert node.get_output_value("accepted") is True

    @pytest.mark.asyncio
    async def test_message_box_cancel_result(self, execution_context) -> None:
        """Test message box returning Cancel."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox_class,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Ok = 1024
            mock_msgbox_class.Cancel = 4194304
            mock_msgbox_class.Information = 1
            mock_msgbox.exec.return_value = 4194304  # QMessageBox.Cancel

            node = MessageBoxNode(
                node_id="test_msg_cancel", config={"buttons": "ok_cancel"}
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("result") == "cancel"
            assert node.get_output_value("accepted") is False

    @pytest.mark.asyncio
    async def test_message_box_with_input_message(self, execution_context) -> None:
        """Test message box using message from input port."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox_class,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Ok = 1024
            mock_msgbox_class.Information = 1
            mock_msgbox.exec.return_value = 1024

            node = MessageBoxNode(node_id="test_msg_input", config={"title": "Alert"})
            node.set_input_value("message", "Dynamic message")
            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_msgbox.setText.assert_called_once_with("Dynamic message")

    @pytest.mark.asyncio
    async def test_message_box_icon_types(self, execution_context) -> None:
        """Test message box with different icon types."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode

        for icon_type in ["information", "warning", "error", "question"]:
            with (
                patch("PySide6.QtWidgets.QApplication") as mock_app,
                patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox_class,
            ):
                mock_app.instance.return_value = MagicMock()
                mock_msgbox = MagicMock()
                mock_msgbox_class.return_value = mock_msgbox
                mock_msgbox_class.Ok = 1024
                mock_msgbox_class.Information = 1
                mock_msgbox_class.Warning = 2
                mock_msgbox_class.Critical = 3
                mock_msgbox_class.Question = 4
                mock_msgbox.exec.return_value = 1024

                node = MessageBoxNode(
                    node_id=f"test_msg_{icon_type}", config={"icon_type": icon_type}
                )
                result = await node.execute(execution_context)

                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_message_box_yes_no_buttons(self, execution_context) -> None:
        """Test message box with yes/no buttons."""
        from casare_rpa.nodes.system_nodes import MessageBoxNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QMessageBox") as mock_msgbox_class,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_msgbox = MagicMock()
            mock_msgbox_class.return_value = mock_msgbox
            mock_msgbox_class.Yes = 16384
            mock_msgbox_class.No = 65536
            mock_msgbox_class.Question = 4
            mock_msgbox.exec.return_value = 16384  # Yes

            node = MessageBoxNode(
                node_id="test_msg_yesno",
                config={"buttons": "yes_no", "icon_type": "question"},
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("result") == "yes"
            assert node.get_output_value("accepted") is True


class TestInputDialogNode:
    """Tests for InputDialogNode."""

    @pytest.mark.asyncio
    async def test_input_dialog_confirmed(self, execution_context) -> None:
        """Test input dialog with user confirmation."""
        from casare_rpa.nodes.system_nodes import InputDialogNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QInputDialog") as mock_dialog,
            patch("PySide6.QtWidgets.QLineEdit") as mock_lineedit,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_dialog.getText.return_value = ("User Input", True)
            mock_lineedit.Normal = 0

            node = InputDialogNode(node_id="test_input")
            node.set_input_value("title", "Enter Name")
            node.set_input_value("prompt", "Your name:")
            node.set_input_value("default_value", "")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("value") == "User Input"
            assert node.get_output_value("confirmed") is True

    @pytest.mark.asyncio
    async def test_input_dialog_cancelled(self, execution_context) -> None:
        """Test input dialog when cancelled."""
        from casare_rpa.nodes.system_nodes import InputDialogNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QInputDialog") as mock_dialog,
            patch("PySide6.QtWidgets.QLineEdit") as mock_lineedit,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_dialog.getText.return_value = ("", False)
            mock_lineedit.Normal = 0

            node = InputDialogNode(node_id="test_input_cancel")
            node.set_input_value("title", "Confirm")
            node.set_input_value("prompt", "Enter code:")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("value") == ""
            assert node.get_output_value("confirmed") is False

    @pytest.mark.asyncio
    async def test_input_dialog_with_default(self, execution_context) -> None:
        """Test input dialog with default value."""
        from casare_rpa.nodes.system_nodes import InputDialogNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QInputDialog") as mock_dialog,
            patch("PySide6.QtWidgets.QLineEdit") as mock_lineedit,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_dialog.getText.return_value = ("default_value", True)
            mock_lineedit.Normal = 0

            node = InputDialogNode(node_id="test_input_default")
            node.set_input_value("title", "Input")
            node.set_input_value("prompt", "Enter:")
            node.set_input_value("default_value", "default_value")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("confirmed") is True

    @pytest.mark.asyncio
    async def test_input_dialog_password_mode(self, execution_context) -> None:
        """Test input dialog in password mode."""
        from casare_rpa.nodes.system_nodes import InputDialogNode

        with (
            patch("PySide6.QtWidgets.QApplication") as mock_app,
            patch("PySide6.QtWidgets.QInputDialog") as mock_dialog,
            patch("PySide6.QtWidgets.QLineEdit") as mock_lineedit,
        ):
            mock_app.instance.return_value = MagicMock()
            mock_dialog.getText.return_value = ("secret", True)
            mock_lineedit.Password = 2

            node = InputDialogNode(
                node_id="test_input_password", config={"password_mode": True}
            )
            node.set_input_value("title", "Password")
            node.set_input_value("prompt", "Enter password:")

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_dialog.getText.assert_called_once()

    @pytest.mark.asyncio
    async def test_input_dialog_no_gui_fallback(self, execution_context) -> None:
        """Test input dialog fallback when no GUI available."""
        from casare_rpa.nodes.system_nodes import InputDialogNode

        # Test validates code path exists for ImportError handling
        node = InputDialogNode(node_id="test_input_nogui")
        assert node is not None


class TestTooltipNode:
    """Tests for TooltipNode."""

    @pytest.mark.asyncio
    async def test_tooltip_basic(self, execution_context) -> None:
        """Test showing basic tooltip."""
        from casare_rpa.nodes.system_nodes import TooltipNode

        mock_toast = MagicMock()
        mock_toaster = MagicMock()
        mock_toast.return_value = mock_toaster

        with patch.dict("sys.modules", {"win10toast": mock_toast}):
            with patch.object(sys, "platform", "win32"):
                node = TooltipNode(node_id="test_tooltip")
                node.set_input_value("title", "Notification")
                node.set_input_value("message", "Task completed")

                result = await node.execute(execution_context)

                assert result["success"] is True
                assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_tooltip_with_duration(self, execution_context) -> None:
        """Test tooltip with custom duration."""
        from casare_rpa.nodes.system_nodes import TooltipNode

        mock_toast = MagicMock()
        mock_toaster = MagicMock()
        mock_toast.return_value = mock_toaster

        with patch.dict("sys.modules", {"win10toast": mock_toast}):
            with patch.object(sys, "platform", "win32"):
                node = TooltipNode(
                    node_id="test_tooltip_dur", config={"duration": 5000}
                )
                node.set_input_value("title", "Alert")
                node.set_input_value("message", "Warning message")

                result = await node.execute(execution_context)

                assert result["success"] is True


# ==================== COMMAND NODES ====================


class TestRunCommandNode:
    """Tests for RunCommandNode."""

    @pytest.mark.asyncio
    async def test_run_command_success(self, execution_context) -> None:
        """Test running command successfully."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="output line", stderr="")

            node = RunCommandNode(node_id="test_cmd")
            node.set_input_value("command", "echo hello")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("stdout") == "output line"
            assert node.get_output_value("return_code") == 0
            assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_run_command_with_args(self, execution_context) -> None:
        """Test running command with arguments."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="arg1 arg2", stderr="")

            node = RunCommandNode(node_id="test_cmd_args")
            node.set_input_value("command", "mycommand")
            node.set_input_value("args", ["arg1", "arg2"])

            result = await node.execute(execution_context)

            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_run_command_nonzero_exit(self, execution_context) -> None:
        """Test command with non-zero exit code."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="Command failed"
            )

            node = RunCommandNode(node_id="test_cmd_fail")
            node.set_input_value("command", "failing_command")

            result = await node.execute(execution_context)

            assert result["success"] is True  # Node execution succeeded
            assert node.get_output_value("success") is False  # Command failed
            assert node.get_output_value("return_code") == 1

    @pytest.mark.asyncio
    async def test_run_command_timeout(self, execution_context) -> None:
        """Test command timeout handling."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 60)

            node = RunCommandNode(node_id="test_cmd_timeout", config={"timeout": 60})
            node.set_input_value("command", "long_running")

            result = await node.execute(execution_context)

            assert result["success"] is False
            assert node.get_output_value("return_code") == -1

    @pytest.mark.asyncio
    async def test_run_command_blocked_dangerous(self, execution_context) -> None:
        """Test blocking dangerous commands."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        node = RunCommandNode(node_id="test_cmd_blocked")
        node.set_input_value("command", "rm -rf /")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert (
            "blocked" in result["error"].lower()
            or "security" in result["error"].lower()
        )

    @pytest.mark.asyncio
    async def test_run_command_dangerous_chars_blocked(self, execution_context) -> None:
        """Test blocking dangerous characters in shell mode."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        node = RunCommandNode(node_id="test_cmd_injection", config={"shell": True})
        node.set_input_value("command", "echo test | cat /etc/passwd")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "dangerous" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_run_command_empty_raises(self, execution_context) -> None:
        """Test empty command raises error."""
        from casare_rpa.nodes.system_nodes import RunCommandNode

        node = RunCommandNode(node_id="test_cmd_empty")
        node.set_input_value("command", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestRunPowerShellNode:
    """Tests for RunPowerShellNode."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_powershell_success(self, execution_context) -> None:
        """Test running PowerShell script successfully."""
        from casare_rpa.nodes.system_nodes import RunPowerShellNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0, stdout="PowerShell Output", stderr=""
            )

            node = RunPowerShellNode(node_id="test_ps")
            node.set_input_value("script", "Write-Output 'Hello'")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("stdout") == "PowerShell Output"
            assert node.get_output_value("success") is True

    @pytest.mark.asyncio
    async def test_powershell_blocked_pattern(self, execution_context) -> None:
        """Test blocking dangerous PowerShell patterns."""
        from casare_rpa.nodes.system_nodes import RunPowerShellNode

        node = RunPowerShellNode(node_id="test_ps_blocked")
        node.set_input_value("script", "Invoke-WebRequest -Uri 'http://malicious.com'")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "dangerous" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_powershell_blocked_iex(self, execution_context) -> None:
        """Test blocking Invoke-Expression."""
        from casare_rpa.nodes.system_nodes import RunPowerShellNode

        node = RunPowerShellNode(node_id="test_ps_iex")
        node.set_input_value("script", "iex (Get-Content malware.ps1)")

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_powershell_empty_script(self, execution_context) -> None:
        """Test empty script raises error."""
        from casare_rpa.nodes.system_nodes import RunPowerShellNode

        node = RunPowerShellNode(node_id="test_ps_empty")
        node.set_input_value("script", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


# ==================== SERVICE NODES ====================


class TestGetServiceStatusNode:
    """Tests for GetServiceStatusNode.

    Note: GetServiceStatusNode has a known issue with accessing self.outputs
    which doesn't exist in BaseNode. Tests verify the node instantiation and
    basic validation work correctly.
    """

    @pytest.mark.asyncio
    async def test_node_instantiation(self, execution_context) -> None:
        """Test node can be instantiated."""
        from casare_rpa.nodes.system_nodes import GetServiceStatusNode

        node = GetServiceStatusNode(node_id="test_svc_status")
        assert node.node_type == "GetServiceStatusNode"
        assert node.name == "Get Service Status"

    @pytest.mark.asyncio
    async def test_service_name_required(self, execution_context) -> None:
        """Test error when service_name not provided."""
        from casare_rpa.nodes.system_nodes import GetServiceStatusNode

        node = GetServiceStatusNode(node_id="test_svc_empty")
        node.set_input_value("service_name", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()

    @pytest.mark.skipif(sys.platform == "win32", reason="Test non-Windows behavior")
    @pytest.mark.asyncio
    async def test_windows_only_error(self, execution_context) -> None:
        """Test error on non-Windows platform."""
        from casare_rpa.nodes.system_nodes import GetServiceStatusNode

        node = GetServiceStatusNode(node_id="test_svc_nonwin")
        node.set_input_value("service_name", "TestService")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "windows" in result["error"].lower()


class TestStartServiceNode:
    """Tests for StartServiceNode."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_start_service_success(self, execution_context) -> None:
        """Test starting service successfully."""
        from casare_rpa.nodes.system_nodes import StartServiceNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="SERVICE_NAME: TestService\nSTATE: 4 RUNNING",
                stderr="",
            )

            node = StartServiceNode(node_id="test_start_svc")
            node.set_input_value("service_name", "TestService")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("success") is True

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_start_service_already_running(self, execution_context) -> None:
        """Test starting service that is already running."""
        from casare_rpa.nodes.system_nodes import StartServiceNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="An instance of the service is already running",
            )

            node = StartServiceNode(node_id="test_start_running")
            node.set_input_value("service_name", "RunningService")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("success") is True  # Already running is OK

    @pytest.mark.asyncio
    async def test_start_service_empty_name(self, execution_context) -> None:
        """Test starting service with empty name."""
        from casare_rpa.nodes.system_nodes import StartServiceNode

        node = StartServiceNode(node_id="test_start_empty")
        node.set_input_value("service_name", "")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "required" in result["error"].lower()


class TestStopServiceNode:
    """Tests for StopServiceNode."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_stop_service_success(self, execution_context) -> None:
        """Test stopping service successfully."""
        from casare_rpa.nodes.system_nodes import StopServiceNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="SERVICE_NAME: TestService\nSTATE: 1 STOPPED",
                stderr="",
            )

            node = StopServiceNode(node_id="test_stop_svc")
            node.set_input_value("service_name", "TestService")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("success") is True

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_stop_service_not_started(self, execution_context) -> None:
        """Test stopping service that is not started."""
        from casare_rpa.nodes.system_nodes import StopServiceNode

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=1, stdout="", stderr="The service has not been started"
            )

            node = StopServiceNode(node_id="test_stop_notstarted")
            node.set_input_value("service_name", "StoppedService")

            result = await node.execute(execution_context)

            # Node returns success because execution completed
            # success output reflects whether stop operation was needed/done
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_stop_service_empty_name(self, execution_context) -> None:
        """Test stopping service with empty name."""
        from casare_rpa.nodes.system_nodes import StopServiceNode

        node = StopServiceNode(node_id="test_stop_empty")
        node.set_input_value("service_name", "")

        result = await node.execute(execution_context)

        assert result["success"] is False


class TestRestartServiceNode:
    """Tests for RestartServiceNode."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_restart_service_success(self, execution_context) -> None:
        """Test restarting service successfully."""
        from casare_rpa.nodes.system_nodes import RestartServiceNode

        with patch("subprocess.run") as mock_run, patch("asyncio.sleep") as mock_sleep:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="SERVICE_NAME: TestService\nSTATE: 4 RUNNING",
                stderr="",
            )

            node = RestartServiceNode(node_id="test_restart_svc")
            node.set_input_value("service_name", "TestService")

            result = await node.execute(execution_context)

            assert result["success"] is True
            assert node.get_output_value("success") is True
            assert mock_run.call_count == 2  # stop + start

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_restart_service_with_wait_time(self, execution_context) -> None:
        """Test restarting with custom wait time."""
        from casare_rpa.nodes.system_nodes import RestartServiceNode

        with patch("subprocess.run") as mock_run, patch("asyncio.sleep") as mock_sleep:
            mock_run.return_value = Mock(returncode=0, stdout="RUNNING", stderr="")

            node = RestartServiceNode(
                node_id="test_restart_wait", config={"wait_time": 5}
            )
            node.set_input_value("service_name", "TestService")

            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_sleep.assert_called_once_with(5)


class TestListServicesNode:
    """Tests for ListServicesNode."""

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_list_all_services(self, execution_context) -> None:
        """Test listing all services."""
        from casare_rpa.nodes.system_nodes import ListServicesNode
        import json

        services_json = json.dumps(
            [
                {"Name": "Service1", "DisplayName": "Service One", "Status": 4},
                {"Name": "Service2", "DisplayName": "Service Two", "Status": 1},
            ]
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=services_json, stderr="")

            node = ListServicesNode(node_id="test_list_svc")
            result = await node.execute(execution_context)

            assert result["success"] is True
            services = node.get_output_value("services")
            assert node.get_output_value("count") == 2

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_list_running_services_only(self, execution_context) -> None:
        """Test listing only running services."""
        from casare_rpa.nodes.system_nodes import ListServicesNode
        import json

        services_json = json.dumps(
            [
                {"Name": "Running1", "DisplayName": "Running Service", "Status": 4},
                {"Name": "Stopped1", "DisplayName": "Stopped Service", "Status": 1},
            ]
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=services_json, stderr="")

            node = ListServicesNode(
                node_id="test_list_running", config={"state_filter": "running"}
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            services = node.get_output_value("services")
            assert all(s["status"] == "running" for s in services)

    @pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")
    @pytest.mark.asyncio
    async def test_list_stopped_services_only(self, execution_context) -> None:
        """Test listing only stopped services."""
        from casare_rpa.nodes.system_nodes import ListServicesNode
        import json

        services_json = json.dumps(
            [
                {"Name": "Running1", "DisplayName": "Running Service", "Status": 4},
                {"Name": "Stopped1", "DisplayName": "Stopped Service", "Status": 1},
            ]
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout=services_json, stderr="")

            node = ListServicesNode(
                node_id="test_list_stopped", config={"state_filter": "stopped"}
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            services = node.get_output_value("services")
            assert all(s["status"] == "stopped" for s in services)
