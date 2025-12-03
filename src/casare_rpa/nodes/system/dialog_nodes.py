"""
Dialog and notification nodes for CasareRPA.

This module provides nodes for user interaction:
- Message boxes
- Input dialogs
- Tooltip/notifications
"""

import sys

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import executable_node, node_schema
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Message",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Message to display",
    ),
    PropertyDef(
        "detailed_text",
        PropertyType.STRING,
        default="",
        label="Detailed Text",
        tooltip="Expandable details section",
    ),
    PropertyDef(
        "icon_type",
        PropertyType.CHOICE,
        default="information",
        choices=["information", "warning", "error", "question"],
        label="Icon Type",
        tooltip="Dialog icon type",
    ),
    PropertyDef(
        "buttons",
        PropertyType.CHOICE,
        default="ok",
        choices=["ok", "ok_cancel", "yes_no", "yes_no_cancel"],
        label="Buttons",
        tooltip="Button configuration",
    ),
    PropertyDef(
        "default_button",
        PropertyType.STRING,
        default="",
        label="Default Button",
        tooltip="Which button is focused by default",
    ),
    PropertyDef(
        "always_on_top",
        PropertyType.BOOLEAN,
        default=True,
        label="Always On Top",
        tooltip="Keep dialog above other windows",
    ),
    PropertyDef(
        "play_sound",
        PropertyType.BOOLEAN,
        default=False,
        label="Play Sound",
        tooltip="Play system sound when dialog appears",
    ),
    PropertyDef(
        "auto_close_timeout",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Auto-Close Timeout (seconds)",
        tooltip="Auto-dismiss after X seconds, 0 to disable",
    ),
)
@executable_node
class MessageBoxNode(BaseNode):
    """
    Display a message box dialog.

    Config (via @node_schema):
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
            title = self.get_parameter("title", "Message")
            icon_type = self.get_parameter("icon_type", "information")
            buttons = self.get_parameter("buttons", "ok")
            default_button = self.get_parameter("default_button", "")
            always_on_top = self.get_parameter("always_on_top", True)
            play_sound = self.get_parameter("play_sound", False)
            detailed_text = self.get_parameter("detailed_text", "")
            # Ensure auto_close_timeout is int (widgets may return strings)
            auto_close_timeout = int(self.get_parameter("auto_close_timeout", 0) or 0)

            # Get message from input port first, fallback to config
            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")

            # Resolve {{variable}} patterns in title, message, and detailed_text
            title = context.resolve_value(title)
            message = context.resolve_value(str(message))
            if detailed_text:
                detailed_text = context.resolve_value(detailed_text)

            result = "ok"
            accepted = True

            # Play sound if enabled
            if play_sound:
                self._play_system_sound(icon_type)

            # Try PySide6 first - BUT only if a QApplication already exists
            try:
                result, accepted = await self._show_qt_dialog(
                    title,
                    message,
                    icon_type,
                    buttons,
                    default_button,
                    always_on_top,
                    detailed_text,
                    auto_close_timeout,
                )
            except ImportError:
                # Fallback to Windows MessageBox API
                if sys.platform == "win32":
                    result, accepted = self._show_windows_dialog(
                        title,
                        message,
                        icon_type,
                        buttons,
                        default_button,
                        always_on_top,
                        play_sound,
                        auto_close_timeout,
                    )
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

    def _play_system_sound(self, icon_type: str) -> None:
        """Play system sound based on icon type."""
        try:
            import winsound

            sound_map = {
                "information": winsound.MB_ICONASTERISK,
                "warning": winsound.MB_ICONEXCLAMATION,
                "error": winsound.MB_ICONHAND,
                "question": winsound.MB_ICONQUESTION,
            }
            winsound.MessageBeep(sound_map.get(icon_type, winsound.MB_OK))
        except Exception:
            pass  # Ignore sound errors

    async def _show_qt_dialog(
        self,
        title: str,
        message: str,
        icon_type: str,
        buttons: str,
        default_button: str,
        always_on_top: bool,
        detailed_text: str,
        auto_close_timeout: int,
    ) -> tuple[str, bool]:
        """Show dialog using PySide6."""
        import asyncio
        from PySide6.QtWidgets import QMessageBox, QApplication
        from PySide6.QtCore import Qt, QTimer

        # Check if QApplication exists and is running
        app = QApplication.instance()
        if app is None:
            raise ImportError("No QApplication running - use native dialog")

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
            "yes_no_cancel": QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
        }
        btns = button_map.get(buttons, QMessageBox.Ok)

        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(btns)

        if detailed_text:
            msg_box.setDetailedText(detailed_text)

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

        if always_on_top:
            msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint)

        # Setup auto-close timer if enabled
        timed_out = False
        if auto_close_timeout > 0:

            def on_timeout():
                nonlocal timed_out
                timed_out = True
                msg_box.done(0)

            timer = QTimer(msg_box)
            timer.setSingleShot(True)
            timer.timeout.connect(on_timeout)
            timer.start(auto_close_timeout * 1000)

        # Use non-blocking approach
        future = asyncio.get_event_loop().create_future()

        def on_finished(button_result):
            if not future.done():
                future.set_result(button_result)

        msg_box.finished.connect(on_finished)
        msg_box.show()
        msg_box.raise_()
        msg_box.activateWindow()

        response = await future

        if timed_out:
            return "timeout", False
        else:
            result_map = {
                QMessageBox.Ok: "ok",
                QMessageBox.Cancel: "cancel",
                QMessageBox.Yes: "yes",
                QMessageBox.No: "no",
            }
            result = result_map.get(response, "ok")
            return result, result in ("ok", "yes")

    def _show_windows_dialog(
        self,
        title: str,
        message: str,
        icon_type: str,
        buttons: str,
        default_button: str,
        always_on_top: bool,
        play_sound: bool,
        auto_close_timeout: int,
    ) -> tuple[str, bool]:
        """Show dialog using Windows MessageBox API."""
        import ctypes

        # Windows MessageBox Constants
        MB_ICONINFORMATION = 0x40
        MB_ICONWARNING = 0x30
        MB_ICONERROR = 0x10
        MB_ICONQUESTION = 0x20

        MB_OK = 0x0
        MB_OKCANCEL = 0x1
        MB_YESNO = 0x4
        MB_YESNOCANCEL = 0x3

        MB_DEFBUTTON1 = 0x0
        MB_DEFBUTTON2 = 0x100
        MB_DEFBUTTON3 = 0x200

        MB_TOPMOST = 0x40000
        MB_SETFOREGROUND = 0x10000
        MB_SYSTEMMODAL = 0x1000

        # Icon mapping
        icon_map = {
            "information": MB_ICONINFORMATION,
            "warning": MB_ICONWARNING,
            "error": MB_ICONERROR,
            "question": MB_ICONQUESTION,
        }
        win_icon = icon_map.get(icon_type, MB_ICONINFORMATION)

        # Button mapping
        button_map = {
            "ok": MB_OK,
            "ok_cancel": MB_OKCANCEL,
            "yes_no": MB_YESNO,
            "yes_no_cancel": MB_YESNOCANCEL,
        }
        win_buttons = button_map.get(buttons, MB_OK)

        # Default button mapping
        default_btn_map = {
            "ok": {"ok": MB_DEFBUTTON1},
            "ok_cancel": {"ok": MB_DEFBUTTON1, "cancel": MB_DEFBUTTON2},
            "yes_no": {"yes": MB_DEFBUTTON1, "no": MB_DEFBUTTON2},
            "yes_no_cancel": {
                "yes": MB_DEFBUTTON1,
                "no": MB_DEFBUTTON2,
                "cancel": MB_DEFBUTTON3,
            },
        }
        win_default = MB_DEFBUTTON1
        if default_button:
            btn_options = default_btn_map.get(buttons, {})
            win_default = btn_options.get(default_button.lower(), MB_DEFBUTTON1)

        flags = win_buttons | win_icon | win_default | MB_SETFOREGROUND
        if always_on_top:
            flags |= MB_TOPMOST | MB_SYSTEMMODAL

        if play_sound:
            self._play_system_sound(icon_type)

        # Force foreground permission
        try:
            user32 = ctypes.windll.user32
            user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

        # Auto-close timeout support
        timed_out = False
        if auto_close_timeout > 0:
            import threading

            dialog_closed = threading.Event()

            def auto_close_timer():
                nonlocal timed_out
                if not dialog_closed.wait(timeout=auto_close_timeout):
                    timed_out = True
                    hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if hwnd:
                        WM_CLOSE = 0x10
                        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)

            timer_thread = threading.Thread(target=auto_close_timer, daemon=True)
            timer_thread.start()

            response = ctypes.windll.user32.MessageBoxW(0, message, title, flags)
            dialog_closed.set()
        else:
            response = ctypes.windll.user32.MessageBoxW(0, message, title, flags)

        IDOK = 1
        IDCANCEL = 2
        IDYES = 6
        IDNO = 7

        if timed_out:
            return "timeout", False
        else:
            result_map = {IDOK: "ok", IDCANCEL: "cancel", IDYES: "yes", IDNO: "no"}
            result = result_map.get(response, "ok")
            return result, result in ("ok", "yes")


@node_schema(
    PropertyDef(
        "password_mode",
        PropertyType.BOOLEAN,
        default=False,
        label="Password Mode",
        tooltip="Hide input characters",
    ),
)
@executable_node
class InputDialogNode(BaseNode):
    """
    Display an input dialog to get user input.

    Config (via @node_schema):
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
            password_mode = self.get_parameter("password_mode", False)

            # Resolve {{variable}} patterns
            title = context.resolve_value(title)
            prompt = context.resolve_value(prompt)
            default_value = context.resolve_value(default_value)

            value = ""
            confirmed = False

            try:
                import asyncio
                from PySide6.QtWidgets import QInputDialog, QApplication, QLineEdit
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    app = QApplication([])

                dialog = QInputDialog()
                dialog.setWindowTitle(title)
                dialog.setLabelText(prompt)
                dialog.setTextValue(default_value)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                if password_mode:
                    dialog.setTextEchoMode(QLineEdit.Password)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result_code):
                    if not future.done():
                        future.set_result(
                            (dialog.textValue(), result_code == QInputDialog.Accepted)
                        )

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                text, ok = await future

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


@node_schema(
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=3000,
        min_value=100,
        label="Duration (milliseconds)",
        tooltip="Duration to show tooltip",
    ),
    PropertyDef(
        "position",
        PropertyType.CHOICE,
        default="bottom_right",
        choices=["bottom_right", "bottom_left", "top_right", "top_left"],
        label="Position",
        tooltip="Screen position for tooltip",
    ),
)
@executable_node
class TooltipNode(BaseNode):
    """
    Display a tooltip/notification.

    Config (via @node_schema):
        duration: Duration in milliseconds (default: 3000)
        position: 'bottom_right', 'bottom_left', 'top_right', 'top_left'

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
            duration = self.get_parameter("duration", 3000)

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
