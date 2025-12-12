"""
Message dialog nodes.

Nodes for displaying information or confirmation dialogs.
"""

import sys
import asyncio
from typing import Optional, Tuple

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
        essential=True,
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

    # @category: system
    # @requires: none
    # @ports: message -> result, accepted

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
            auto_close_timeout = int(self.get_parameter("auto_close_timeout", 0) or 0)

            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")

            title = str(context.resolve_value(title) or "")
            # Resolve variable first, THEN convert to string (resolve preserves types for {{var}} patterns)
            resolved_message = context.resolve_value(message)
            message = str(resolved_message) if resolved_message is not None else ""
            if detailed_text:
                detailed_text = context.resolve_value(detailed_text)

            result = "ok"
            accepted = True

            if play_sound:
                self._play_system_sound(icon_type)

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
            pass

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
    ) -> Tuple[str, bool]:
        """Show dialog using PySide6."""
        from PySide6.QtWidgets import QMessageBox, QApplication
        from PySide6.QtCore import Qt, QTimer

        app = QApplication.instance()
        if app is None:
            raise ImportError("No QApplication running - use native dialog")

        icon_map = {
            "information": QMessageBox.Information,
            "warning": QMessageBox.Warning,
            "error": QMessageBox.Critical,
            "question": QMessageBox.Question,
        }
        icon = icon_map.get(icon_type, QMessageBox.Information)

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
    ) -> Tuple[str, bool]:
        """Show dialog using Windows MessageBox API."""
        import ctypes

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

        icon_map = {
            "information": MB_ICONINFORMATION,
            "warning": MB_ICONWARNING,
            "error": MB_ICONERROR,
            "question": MB_ICONQUESTION,
        }
        win_icon = icon_map.get(icon_type, MB_ICONINFORMATION)

        button_map = {
            "ok": MB_OK,
            "ok_cancel": MB_OKCANCEL,
            "yes_no": MB_YESNO,
            "yes_no_cancel": MB_YESNOCANCEL,
        }
        win_buttons = button_map.get(buttons, MB_OK)

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

        try:
            user32 = ctypes.windll.user32
            user32.AllowSetForegroundWindow(-1)
        except Exception:
            pass

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
        "title",
        PropertyType.STRING,
        default="Confirm",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="Are you sure?",
        label="Message",
        tooltip="Confirmation message",
        essential=True,
    ),
    PropertyDef(
        "icon_type",
        PropertyType.CHOICE,
        default="question",
        choices=["question", "warning", "info"],
        label="Icon Type",
        tooltip="Dialog icon",
    ),
    PropertyDef(
        "always_on_top",
        PropertyType.BOOLEAN,
        default=True,
        label="Always On Top",
        tooltip="Keep dialog above other windows",
    ),
    PropertyDef(
        "button_yes_text",
        PropertyType.STRING,
        default="Yes",
        label="Yes Button Text",
        tooltip="Text for Yes button",
    ),
    PropertyDef(
        "button_no_text",
        PropertyType.STRING,
        default="No",
        label="No Button Text",
        tooltip="Text for No button",
    ),
)
@executable_node
class ConfirmDialogNode(BaseNode):
    """
    Display a Yes/No confirmation dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Confirm')
        message: Confirmation message (essential - shows widget)
        icon_type: question, warning, info (default: question)
        always_on_top: Keep above other windows (default: True)
        button_yes_text: Text for Yes button (default: 'Yes')
        button_no_text: Text for No button (default: 'No')

    Outputs:
        confirmed: True if Yes was clicked
        button_clicked: 'yes', 'no', or 'cancel'
    """

    # @category: system
    # @requires: none
    # @ports: message -> confirmed, button_clicked

    def __init__(self, node_id: str, name: str = "Confirm Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ConfirmDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("confirmed", DataType.BOOLEAN)
        self.add_output_port("button_clicked", DataType.STRING)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Confirm")
            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "Are you sure?")
            message = str(message)

            icon_type = self.get_parameter("icon_type", "question")
            always_on_top = self.get_parameter("always_on_top", True)
            button_yes_text = self.get_parameter("button_yes_text", "Yes")
            button_no_text = self.get_parameter("button_no_text", "No")

            title = context.resolve_value(title)
            message = context.resolve_value(message)

            try:
                from PySide6.QtWidgets import QMessageBox, QApplication
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                icon_map = {
                    "question": QMessageBox.Question,
                    "warning": QMessageBox.Warning,
                    "info": QMessageBox.Information,
                }
                icon = icon_map.get(icon_type, QMessageBox.Question)

                msg_box = QMessageBox()
                msg_box.setWindowTitle(title)
                msg_box.setText(message)
                msg_box.setIcon(icon)

                yes_btn = msg_box.addButton(button_yes_text, QMessageBox.YesRole)
                no_btn = msg_box.addButton(button_no_text, QMessageBox.NoRole)

                if always_on_top:
                    msg_box.setWindowFlags(
                        msg_box.windowFlags() | Qt.WindowStaysOnTopHint
                    )

                future = asyncio.get_event_loop().create_future()

                def on_finished():
                    if not future.done():
                        clicked_btn = msg_box.clickedButton()
                        if clicked_btn == yes_btn:
                            future.set_result(("yes", True))
                        else:
                            future.set_result(("no", False))

                msg_box.finished.connect(on_finished)
                msg_box.show()
                msg_box.raise_()
                msg_box.activateWindow()

                button_clicked, confirmed = await future

            except ImportError:
                confirmed = True
                button_clicked = "yes"

            self.set_output_value("confirmed", confirmed)
            self.set_output_value("button_clicked", button_clicked)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"confirmed": confirmed, "button_clicked": button_clicked},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("confirmed", False)
            self.set_output_value("button_clicked", "error")
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}
