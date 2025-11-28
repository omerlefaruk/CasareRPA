"""
System operation nodes for CasareRPA.

This module provides nodes for system-level operations:
- Clipboard operations (copy, paste, clear)
- Message boxes and dialogs
- Terminal/CMD command execution
- Windows Services management
"""

import subprocess
import sys

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.utils.type_converters import safe_int


class SecurityError(Exception):
    """Raised when a security check fails."""

    pass


# ==================== CLIPBOARD OPERATIONS ====================


@executable_node
class ClipboardCopyNode(BaseNode):
    """
    Copy text to the clipboard.

    Inputs:
        text: Text to copy to clipboard

    Outputs:
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Clipboard Copy", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardCopyNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = str(self.get_input_value("text", context) or "")

            # Use pyperclip if available, otherwise fall back to platform-specific
            try:
                import pyperclip

                pyperclip.copy(text)
            except ImportError:
                # Fallback for Windows
                if sys.platform == "win32":
                    import ctypes

                    CF_UNICODETEXT = 13
                    GMEM_MOVEABLE = 0x0002

                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32

                    user32.OpenClipboard(0)
                    user32.EmptyClipboard()

                    if text:
                        data = text.encode("utf-16-le") + b"\x00\x00"
                        h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                        mem_ptr = kernel32.GlobalLock(h_mem)
                        ctypes.memmove(mem_ptr, data, len(data))
                        kernel32.GlobalUnlock(h_mem)
                        user32.SetClipboardData(CF_UNICODETEXT, h_mem)

                    user32.CloseClipboard()
                else:
                    raise RuntimeError(
                        "pyperclip not installed and no native clipboard support"
                    )

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"copied_length": len(text)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class ClipboardPasteNode(BaseNode):
    """
    Get text from the clipboard.

    Outputs:
        text: Text from clipboard
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Clipboard Paste", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardPasteNode"

    def _define_ports(self) -> None:
        self.add_output_port("text", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            text = ""

            # Use pyperclip if available
            try:
                import pyperclip

                text = pyperclip.paste()
            except ImportError:
                # Fallback for Windows
                if sys.platform == "win32":
                    import ctypes

                    CF_UNICODETEXT = 13
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32

                    user32.OpenClipboard(0)
                    try:
                        h_data = user32.GetClipboardData(CF_UNICODETEXT)
                        if h_data:
                            mem_ptr = kernel32.GlobalLock(h_data)
                            if mem_ptr:
                                text = ctypes.wstring_at(mem_ptr)
                                kernel32.GlobalUnlock(h_data)
                    finally:
                        user32.CloseClipboard()
                else:
                    raise RuntimeError(
                        "pyperclip not installed and no native clipboard support"
                    )

            self.set_output_value("text", text)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"text_length": len(text)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("text", "")
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class ClipboardClearNode(BaseNode):
    """
    Clear the clipboard.

    Outputs:
        success: Whether operation succeeded
    """

    def __init__(self, node_id: str, name: str = "Clipboard Clear", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ClipboardClearNode"

    def _define_ports(self) -> None:
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            try:
                import pyperclip

                pyperclip.copy("")
            except ImportError:
                if sys.platform == "win32":
                    import ctypes

                    user32 = ctypes.windll.user32
                    user32.OpenClipboard(0)
                    user32.EmptyClipboard()
                    user32.CloseClipboard()
                else:
                    raise RuntimeError(
                        "pyperclip not installed and no native clipboard support"
                    )

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


# ==================== MESSAGE BOX / DIALOG OPERATIONS ====================


@executable_node
class MessageBoxNode(BaseNode):
    """
    Display a message box dialog.

    Config:
        title: Dialog title (default: 'Message')
        message: Message to display (default: '')
        detailed_text: Expandable details section (default: '')
        icon_type: 'information', 'warning', 'error', 'question' (default: information)
        buttons: 'ok', 'ok_cancel', 'yes_no', 'yes_no_cancel' (default: ok)
        default_button: Which button is focused by default (default: first button)
        always_on_top: Keep dialog above other windows (default: True)
        play_sound: Play system sound when dialog appears (default: False)
        auto_close_timeout: Auto-dismiss after X seconds, 0 to disable (default: 0)

    Outputs:
        result: Button clicked ('ok', 'cancel', 'yes', 'no', 'timeout')
        accepted: True if OK/Yes was clicked
    """

    def __init__(self, node_id: str, name: str = "Message Box", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MessageBoxNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", PortType.INPUT, DataType.STRING)
        self.add_output_port("result", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("accepted", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Get values from config (set by visual node widgets)
            title = str(self.config.get("title", "Message"))
            icon_type = self.config.get("icon_type", "information")
            buttons = self.config.get("buttons", "ok")
            default_button = self.config.get("default_button", "")
            always_on_top = self.config.get("always_on_top", True)
            play_sound = self.config.get("play_sound", False)
            detailed_text = str(self.config.get("detailed_text", ""))

            # Parse auto_close_timeout safely
            timeout_val = self.config.get("auto_close_timeout", 0)
            try:
                auto_close_timeout = int(timeout_val) if timeout_val else 0
            except (ValueError, TypeError):
                auto_close_timeout = 0

            # Get message from input port first, fallback to config
            message = self.get_input_value("message")
            if message is None:
                message = str(self.config.get("message", ""))

            # Resolve {{variable}} patterns in title, message, and detailed_text
            title = context.resolve_value(title)
            message = context.resolve_value(str(message))
            if detailed_text:
                detailed_text = context.resolve_value(detailed_text)

            result = "ok"
            accepted = True

            # Play sound if enabled
            if play_sound:
                try:
                    import winsound

                    # Map icon type to system sound
                    sound_map = {
                        "information": winsound.MB_ICONASTERISK,
                        "warning": winsound.MB_ICONEXCLAMATION,
                        "error": winsound.MB_ICONHAND,
                        "question": winsound.MB_ICONQUESTION,
                    }
                    winsound.MessageBeep(sound_map.get(icon_type, winsound.MB_OK))
                except Exception:
                    pass  # Ignore sound errors

            # Try PySide6 first
            try:
                from PySide6.QtWidgets import QMessageBox, QApplication, QPushButton
                from PySide6.QtCore import Qt, QTimer

                # Ensure QApplication exists
                app = QApplication.instance()
                if app is None:
                    app = QApplication([])

                # Determine icon
                icon_map = {
                    "information": QMessageBox.Information,
                    "warning": QMessageBox.Warning,
                    "error": QMessageBox.Critical,
                    "question": QMessageBox.Question,
                }
                icon = icon_map.get(icon_type, QMessageBox.Information)

                # Determine buttons
                button_map = {
                    "ok": QMessageBox.Ok,
                    "ok_cancel": QMessageBox.Ok | QMessageBox.Cancel,
                    "yes_no": QMessageBox.Yes | QMessageBox.No,
                    "yes_no_cancel": QMessageBox.Yes
                    | QMessageBox.No
                    | QMessageBox.Cancel,
                }
                btns = button_map.get(buttons, QMessageBox.Ok)

                msg_box = QMessageBox()
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.setIcon(icon)
                msg_box.setStandardButtons(btns)

                # Set detailed text if provided
                if detailed_text:
                    msg_box.setDetailedText(detailed_text)

                # Set default button if specified
                if default_button:
                    default_btn_map = {
                        "ok": QMessageBox.Ok,
                        "cancel": QMessageBox.Cancel,
                        "yes": QMessageBox.Yes,
                        "no": QMessageBox.No,
                    }
                    default_btn = default_btn_map.get(default_button.lower())
                    if default_btn:
                        msg_box.setDefaultButton(default_btn)

                # Set always on top if enabled
                if always_on_top:
                    msg_box.setWindowFlags(
                        msg_box.windowFlags() | Qt.WindowStaysOnTopHint
                    )

                # Setup auto-close timer if enabled
                timed_out = False
                if auto_close_timeout > 0:

                    def on_timeout():
                        nonlocal timed_out
                        timed_out = True
                        msg_box.done(0)  # Close with result 0

                    timer = QTimer(msg_box)
                    timer.setSingleShot(True)
                    timer.timeout.connect(on_timeout)
                    timer.start(auto_close_timeout * 1000)

                response = msg_box.exec()

                if timed_out:
                    result = "timeout"
                    accepted = False
                else:
                    result_map = {
                        QMessageBox.Ok: "ok",
                        QMessageBox.Cancel: "cancel",
                        QMessageBox.Yes: "yes",
                        QMessageBox.No: "no",
                    }
                    result = result_map.get(response, "ok")
                    accepted = result in ("ok", "yes")

            except ImportError:
                # Fallback to Windows MessageBox
                if sys.platform == "win32":
                    import ctypes

                    # Icons
                    MB_ICONINFORMATION = 0x40
                    MB_ICONWARNING = 0x30
                    MB_ICONERROR = 0x10
                    MB_ICONQUESTION = 0x20

                    # Buttons
                    MB_OK = 0x0
                    MB_OKCANCEL = 0x1
                    MB_YESNO = 0x4
                    MB_YESNOCANCEL = 0x3

                    # Modifiers
                    MB_TOPMOST = 0x40000

                    icon_map = {
                        "information": MB_ICONINFORMATION,
                        "warning": MB_ICONWARNING,
                        "error": MB_ICONERROR,
                        "question": MB_ICONQUESTION,
                    }
                    icon = icon_map.get(icon_type, MB_ICONINFORMATION)

                    button_map = {
                        "ok": MB_OK,
                        "ok_cancel": MB_OKCANCEL,
                        "yes_no": MB_YESNO,
                        "yes_no_cancel": MB_YESNOCANCEL,
                    }
                    btns = button_map.get(buttons, MB_OK)

                    flags = btns | icon
                    if always_on_top:
                        flags |= MB_TOPMOST

                    response = ctypes.windll.user32.MessageBoxW(
                        0, message, title, flags
                    )

                    # Response codes
                    IDOK = 1
                    IDCANCEL = 2
                    IDYES = 6
                    IDNO = 7

                    result_map = {
                        IDOK: "ok",
                        IDCANCEL: "cancel",
                        IDYES: "yes",
                        IDNO: "no",
                    }
                    result = result_map.get(response, "ok")
                    accepted = result in ("ok", "yes")
                else:
                    # For non-Windows without PySide6, just log and continue
                    result = "ok"
                    accepted = True

            self.set_output_value("result", result)
            self.set_output_value("accepted", accepted)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"result": result, "accepted": accepted},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("result", "error")
            self.set_output_value("accepted", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class InputDialogNode(BaseNode):
    """
    Display an input dialog to get user input.

    Config:
        password_mode: Hide input (default: False)

    Inputs:
        title: Dialog title
        prompt: Prompt message
        default_value: Default input value

    Outputs:
        value: User input value
        confirmed: Whether OK was clicked
    """

    def __init__(self, node_id: str, name: str = "Input Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "InputDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("title", PortType.INPUT, DataType.STRING)
        self.add_input_port("prompt", PortType.INPUT, DataType.STRING)
        self.add_input_port("default_value", PortType.INPUT, DataType.STRING)
        self.add_output_port("value", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("confirmed", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = str(self.get_input_value("title", context) or "Input")
            prompt = str(self.get_input_value("prompt", context) or "Enter value:")
            default_value = str(self.get_input_value("default_value", context) or "")
            password_mode = self.config.get("password_mode", False)

            # Resolve {{variable}} patterns
            title = context.resolve_value(title)
            prompt = context.resolve_value(prompt)
            default_value = context.resolve_value(default_value)

            value = ""
            confirmed = False

            try:
                from PySide6.QtWidgets import QInputDialog, QApplication, QLineEdit

                app = QApplication.instance()
                if app is None:
                    app = QApplication([])

                if password_mode:
                    text, ok = QInputDialog.getText(
                        None, title, prompt, QLineEdit.Password, default_value
                    )
                else:
                    text, ok = QInputDialog.getText(
                        None, title, prompt, QLineEdit.Normal, default_value
                    )

                value = text if ok else ""
                confirmed = ok

            except ImportError:
                # No GUI available, return default
                value = default_value
                confirmed = True

            self.set_output_value("value", value)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("value", "")
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class TooltipNode(BaseNode):
    """
    Display a tooltip/notification.

    Config:
        duration: Duration in milliseconds (default: 3000)
        position: 'bottom_right', 'bottom_left', 'top_right', 'top_left' (default: bottom_right)

    Inputs:
        title: Tooltip title
        message: Tooltip message

    Outputs:
        success: Whether tooltip was shown
    """

    def __init__(self, node_id: str, name: str = "Show Tooltip", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TooltipNode"

    def _define_ports(self) -> None:
        self.add_input_port("title", PortType.INPUT, DataType.STRING)
        self.add_input_port("message", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = str(self.get_input_value("title", context) or "Notification")
            message = str(self.get_input_value("message", context) or "")
            duration = safe_int(self.config.get("duration"), 3000)

            # Resolve {{variable}} patterns
            title = context.resolve_value(title)
            message = context.resolve_value(message)

            # Try Windows toast notification
            if sys.platform == "win32":
                try:
                    from win10toast import ToastNotifier

                    toaster = ToastNotifier()
                    toaster.show_toast(
                        title, message, duration=duration // 1000, threaded=True
                    )
                except ImportError:
                    # Fallback to system tray balloon
                    try:
                        from PySide6.QtWidgets import QSystemTrayIcon, QApplication
                        from PySide6.QtGui import QIcon

                        app = QApplication.instance()
                        if app is None:
                            app = QApplication([])

                        tray = QSystemTrayIcon()
                        tray.show()
                        tray.showMessage(
                            title, message, QSystemTrayIcon.Information, duration
                        )
                    except ImportError:
                        pass

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


# ==================== TERMINAL / CMD OPERATIONS ====================


@executable_node
class RunCommandNode(BaseNode):
    """
    Run a terminal/CMD command.

    Config:
        shell: Use shell execution (default: True)
        timeout: Command timeout in seconds (default: 60)
        working_dir: Working directory (default: current)
        capture_output: Capture stdout/stderr (default: True)

    Inputs:
        command: Command to execute
        args: Additional arguments (list or string)

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether command succeeded (return_code == 0)
    """

    def __init__(self, node_id: str, name: str = "Run Command", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunCommandNode"

    def _define_ports(self) -> None:
        self.add_input_port("command", PortType.INPUT, DataType.STRING)
        self.add_input_port("args", PortType.INPUT, DataType.ANY)
        self.add_output_port("stdout", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stderr", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("return_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    # SECURITY: Dangerous shell metacharacters that enable command injection
    DANGEROUS_CHARS = [
        "|",
        "&",
        ";",
        "$",
        "`",
        "(",
        ")",
        "{",
        "}",
        "<",
        ">",
        "\n",
        "\r",
    ]

    # SECURITY: Commands that should never be executed via workflows
    BLOCKED_COMMANDS = [
        "rm",
        "del",
        "format",
        "fdisk",
        "mkfs",  # Destructive
        "wget",
        "curl",
        "invoke-webrequest",  # Network download
        "nc",
        "netcat",
        "ncat",  # Network tools
        "powershell",
        "pwsh",
        "cmd",  # Shell spawning (use dedicated nodes)
        "reg",
        "regedit",  # Registry modification
        "net",
        "sc",  # Service/network management
        "shutdown",
        "reboot",  # System control
    ]

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING
        import shlex

        try:
            command = str(self.get_input_value("command", context) or "")
            args = self.get_input_value("args", context)
            # SECURITY: Default to shell=False to prevent command injection
            shell = self.config.get("shell", False)
            timeout = safe_int(self.config.get("timeout"), 60)
            working_dir = self.config.get("working_dir")
            capture_output = self.config.get("capture_output", True)
            # SECURITY: Allow bypassing security checks only if explicitly enabled
            allow_dangerous = self.config.get("allow_dangerous", False)

            # Resolve {{variable}} patterns
            command = context.resolve_value(command)
            if working_dir:
                working_dir = context.resolve_value(working_dir)

            if not command:
                raise ValueError("command is required")

            # SECURITY: Extract base command for validation
            base_cmd = command.split()[0].lower() if command else ""
            base_cmd = (
                base_cmd.replace(".exe", "").replace(".cmd", "").replace(".bat", "")
            )

            # SECURITY: Block dangerous commands unless explicitly allowed
            if not allow_dangerous:
                if base_cmd in self.BLOCKED_COMMANDS:
                    raise SecurityError(
                        f"Command '{base_cmd}' is blocked for security reasons. "
                        f"Set allow_dangerous=True in config to override (not recommended)."
                    )

                # SECURITY: Check for dangerous characters when shell=True
                if shell:
                    for char in self.DANGEROUS_CHARS:
                        if char in command or (isinstance(args, str) and char in args):
                            raise SecurityError(
                                f"Dangerous character '{char}' detected in command. "
                                f"This could enable command injection. "
                                f"Use shell=False or set allow_dangerous=True to override."
                            )

            # SECURITY: Build command safely
            if shell:
                # When shell=True, concatenate as string (less safe)
                if args:
                    if isinstance(args, list):
                        command = (
                            command + " " + " ".join(shlex.quote(str(a)) for a in args)
                        )
                    elif isinstance(args, str):
                        command = command + " " + args
                logger.warning(
                    f"RunCommandNode executing with shell=True: {command[:100]}..."
                )
            else:
                # When shell=False, build command list (safer)
                if isinstance(command, str):
                    try:
                        cmd_list = shlex.split(command)
                    except ValueError:
                        cmd_list = command.split()
                else:
                    cmd_list = list(command)

                if args:
                    if isinstance(args, list):
                        cmd_list.extend(str(a) for a in args)
                    elif isinstance(args, str):
                        try:
                            cmd_list.extend(shlex.split(args))
                        except ValueError:
                            cmd_list.extend(args.split())

                command = cmd_list

            # Log command execution for audit
            logger.info(f"RunCommandNode executing: {str(command)[:200]}...")

            # Run command
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=working_dir,
            )

            stdout = result.stdout if capture_output else ""
            stderr = result.stderr if capture_output else ""
            return_code = result.returncode
            success = return_code == 0

            self.set_output_value("stdout", stdout)
            self.set_output_value("stderr", stderr)
            self.set_output_value("return_code", return_code)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"return_code": return_code, "success": success},
                "next_nodes": ["exec_out"],
            }

        except subprocess.TimeoutExpired as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", f"Command timed out after {timeout}s")
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class RunPowerShellNode(BaseNode):
    """
    Run a PowerShell script or command.

    Config:
        timeout: Command timeout in seconds (default: 60)
        execution_policy: 'Bypass', 'Unrestricted', etc. (default: RemoteSigned for security)
        allow_dangerous: Allow dangerous commands (default: False)
        constrained_mode: Use PowerShell Constrained Language Mode (default: False)

    Inputs:
        script: PowerShell script or command

    Outputs:
        stdout: Standard output
        stderr: Standard error
        return_code: Process return code
        success: Whether command succeeded
    """

    # SECURITY: Dangerous PowerShell commands/patterns that could be malicious
    DANGEROUS_PATTERNS = [
        # Download and execute
        "invoke-webrequest",
        "iwr",
        "wget",
        "curl",
        "invoke-restmethod",
        "irm",
        "downloadstring",
        "downloadfile",
        "start-bitstransfer",
        # Code execution
        "invoke-expression",
        "iex",
        "invoke-command",
        "icm",
        "start-process",
        "saps",
        # Credential theft
        "get-credential",
        "convertto-securestring",
        "export-clixml",
        # System modification
        "set-executionpolicy",
        "new-service",
        "set-service",
        "new-scheduledtask",
        "register-scheduledjob",
        # Registry
        "set-itemproperty",
        "new-itemproperty",
        "remove-itemproperty",
        # Encoding (often used for obfuscation)
        "-encodedcommand",
        "-enc",
        "-e",
        "fromb64string",
        "tob64string",
        # Reflection/Assembly loading
        "add-type",
        "reflection.assembly",
        "[system.reflection",
    ]

    def __init__(self, node_id: str, name: str = "Run PowerShell", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RunPowerShellNode"

    def _define_ports(self) -> None:
        self.add_input_port("script", PortType.INPUT, DataType.STRING)
        self.add_output_port("stdout", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("stderr", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("return_code", PortType.OUTPUT, DataType.INTEGER)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            script = str(self.get_input_value("script", context) or "")
            timeout = safe_int(self.config.get("timeout"), 60)
            # SECURITY: Default to RemoteSigned instead of Bypass
            execution_policy = self.config.get("execution_policy", "RemoteSigned")
            allow_dangerous = self.config.get("allow_dangerous", False)
            constrained_mode = self.config.get("constrained_mode", False)

            # Resolve {{variable}} patterns in script
            script = context.resolve_value(script)

            if not script:
                raise ValueError("script is required")

            # SECURITY: Check for dangerous patterns unless explicitly allowed
            if not allow_dangerous:
                script_lower = script.lower()
                for pattern in self.DANGEROUS_PATTERNS:
                    if pattern in script_lower:
                        raise SecurityError(
                            f"Dangerous PowerShell pattern '{pattern}' detected in script. "
                            f"Set allow_dangerous=True in config to override (not recommended)."
                        )

            # SECURITY: Log all PowerShell executions for audit
            logger.warning(
                f"RunPowerShellNode executing script (policy={execution_policy}, "
                f"constrained={constrained_mode}): {script[:200]}..."
            )

            # Build PowerShell command
            ps_cmd = [
                "powershell.exe",
                "-ExecutionPolicy",
                execution_policy,
                "-NoProfile",
                "-NonInteractive",  # SECURITY: Prevent interactive prompts
            ]

            # SECURITY: Add Constrained Language Mode if requested
            if constrained_mode:
                # Wrap script in constrained language mode
                script = f'$ExecutionContext.SessionState.LanguageMode = "ConstrainedLanguage"; {script}'

            ps_cmd.extend(["-Command", script])

            result = subprocess.run(
                ps_cmd, capture_output=True, text=True, timeout=timeout
            )

            stdout = result.stdout
            stderr = result.stderr
            return_code = result.returncode
            success = return_code == 0

            self.set_output_value("stdout", stdout)
            self.set_output_value("stderr", stderr)
            self.set_output_value("return_code", return_code)
            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"return_code": return_code, "success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("stdout", "")
            self.set_output_value("stderr", str(e))
            self.set_output_value("return_code", -1)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


# ==================== WINDOWS SERVICES ====================


@executable_node
class GetServiceStatusNode(BaseNode):
    """
    Get the status of a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        status: Service status ('running', 'stopped', 'paused', 'starting', 'stopping', 'unknown')
        display_name: Service display name
        exists: Whether service exists
    """

    def __init__(
        self, node_id: str, name: str = "Get Service Status", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "GetServiceStatusNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("status", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("display_name", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("exists", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            import subprocess

            result = subprocess.run(
                ["sc", "query", service_name], capture_output=True, text=True
            )

            if (
                "FAILED 1060" in result.stderr
                or "does not exist" in result.stderr.lower()
            ):
                self.set_output_value("status", "not_found")
                self.set_output_value("display_name", "")
                self.set_output_value("exists", False)
            else:
                # Parse status from output
                output = result.stdout
                status = "unknown"

                if "RUNNING" in output:
                    status = "running"
                elif "STOPPED" in output:
                    status = "stopped"
                elif "PAUSED" in output:
                    status = "paused"
                elif "START_PENDING" in output:
                    status = "starting"
                elif "STOP_PENDING" in output:
                    status = "stopping"

                # Get display name
                display_result = subprocess.run(
                    ["sc", "GetDisplayName", service_name],
                    capture_output=True,
                    text=True,
                )
                display_name = ""
                if "=" in display_result.stdout:
                    display_name = display_result.stdout.split("=")[-1].strip()

                self.set_output_value("status", status)
                self.set_output_value("display_name", display_name)
                self.set_output_value("exists", True)

            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"status": self.get_output_value("status")},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("status", "error")
            self.set_output_value("exists", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class StartServiceNode(BaseNode):
    """
    Start a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was started
        message: Status message
    """

    def __init__(self, node_id: str, name: str = "Start Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StartServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            result = subprocess.run(
                ["sc", "start", service_name], capture_output=True, text=True
            )

            success = (
                result.returncode == 0 or "already running" in result.stderr.lower()
            )
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class StopServiceNode(BaseNode):
    """
    Stop a Windows service.

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was stopped
        message: Status message
    """

    def __init__(self, node_id: str, name: str = "Stop Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "StopServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            result = subprocess.run(
                ["sc", "stop", service_name], capture_output=True, text=True
            )

            success = result.returncode == 0 or "not started" in result.stderr.lower()
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class RestartServiceNode(BaseNode):
    """
    Restart a Windows service.

    Config:
        wait_time: Seconds to wait between stop and start (default: 2)

    Inputs:
        service_name: Name of the service

    Outputs:
        success: Whether service was restarted
        message: Status message
    """

    def __init__(self, node_id: str, name: str = "Restart Service", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "RestartServiceNode"

    def _define_ports(self) -> None:
        self.add_input_port("service_name", PortType.INPUT, DataType.STRING)
        self.add_output_port("success", PortType.OUTPUT, DataType.BOOLEAN)
        self.add_output_port("message", PortType.OUTPUT, DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        import asyncio

        self.status = NodeStatus.RUNNING

        try:
            service_name = str(self.get_input_value("service_name", context) or "")
            wait_time = safe_int(self.config.get("wait_time"), 2)

            # Resolve {{variable}} patterns
            service_name = context.resolve_value(service_name)

            if not service_name:
                raise ValueError("service_name is required")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            # Stop service
            subprocess.run(["sc", "stop", service_name], capture_output=True)

            # Wait
            await asyncio.sleep(wait_time)

            # Start service
            result = subprocess.run(
                ["sc", "start", service_name], capture_output=True, text=True
            )

            success = result.returncode == 0
            message = result.stdout if success else result.stderr

            self.set_output_value("success", success)
            self.set_output_value("message", message.strip())
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"success": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("message", str(e))
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""


@executable_node
class ListServicesNode(BaseNode):
    """
    List all Windows services.

    Config:
        state_filter: 'all', 'running', 'stopped' (default: all)

    Outputs:
        services: List of service info dicts
        count: Number of services
    """

    def __init__(self, node_id: str, name: str = "List Services", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListServicesNode"

    def _define_ports(self) -> None:
        self.add_output_port("services", PortType.OUTPUT, DataType.LIST)
        self.add_output_port("count", PortType.OUTPUT, DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            state_filter = self.config.get("state_filter", "all")

            if sys.platform != "win32":
                raise RuntimeError("Windows Services only available on Windows")

            # Use PowerShell to get services as it provides better output
            ps_cmd = (
                "Get-Service | Select-Object Name, DisplayName, Status | ConvertTo-Json"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_cmd], capture_output=True, text=True
            )

            services = []
            if result.returncode == 0:
                import json

                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, dict):
                        data = [data]

                    for svc in data:
                        status = str(svc.get("Status", "")).lower()
                        if status == "4":
                            status = "running"
                        elif status == "1":
                            status = "stopped"

                        # Apply filter
                        if state_filter == "running" and status != "running":
                            continue
                        if state_filter == "stopped" and status != "stopped":
                            continue

                        services.append(
                            {
                                "name": svc.get("Name", ""),
                                "display_name": svc.get("DisplayName", ""),
                                "status": status,
                            }
                        )
                except json.JSONDecodeError:
                    pass

            self.set_output_value("services", services)
            self.set_output_value("count", len(services))
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"count": len(services)},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("services", [])
            self.set_output_value("count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _validate_config(self) -> tuple[bool, str]:
        return True, ""
