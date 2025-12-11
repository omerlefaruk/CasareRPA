"""
Dialog and notification nodes for CasareRPA.

This module provides nodes for user interaction:
- Message boxes
- Input dialogs
- Tooltip/notifications
- File/folder pickers
- Color/datetime pickers
- Progress dialogs
- Snackbar/balloon notifications
"""

import sys
import asyncio
from typing import Dict, Any, Optional, Tuple

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


# =============================================================================
# Styled Widget Factories for Runtime Dialogs
# =============================================================================
# These factory functions create themed widgets for runtime dialogs,
# ensuring visual consistency with the CasareRPA theme.


def _create_styled_line_edit(
    placeholder: str = "",
    text: str = "",
    echo_mode: Optional[int] = None,
) -> "QLineEdit":
    """
    Create a themed QLineEdit for runtime dialogs.

    Args:
        placeholder: Placeholder text
        text: Initial text value
        echo_mode: Optional echo mode (e.g., QLineEdit.Password)

    Returns:
        Styled QLineEdit widget
    """
    from PySide6.QtWidgets import QLineEdit

    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setText(text)
    if echo_mode is not None:
        line_edit.setEchoMode(echo_mode)

    # Apply CasareRPA dark theme styling
    line_edit.setStyleSheet("""
        QLineEdit {
            background: #18181b;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            color: #f4f4f5;
            padding: 6px 10px;
            font-size: 13px;
            selection-background-color: #4338ca;
        }
        QLineEdit:focus {
            border: 1px solid #6366f1;
            background: #27272a;
        }
        QLineEdit:hover {
            border: 1px solid #52525b;
        }
        QLineEdit::placeholder {
            color: #71717a;
        }
    """)
    return line_edit


def _create_styled_text_edit(
    placeholder: str = "",
    text: str = "",
) -> "QTextEdit":
    """
    Create a themed QTextEdit for runtime dialogs.

    Args:
        placeholder: Placeholder text
        text: Initial text value

    Returns:
        Styled QTextEdit widget
    """
    from PySide6.QtWidgets import QTextEdit

    text_edit = QTextEdit()
    text_edit.setPlaceholderText(placeholder)
    text_edit.setPlainText(text)

    # Apply CasareRPA dark theme styling
    text_edit.setStyleSheet("""
        QTextEdit {
            background: #18181b;
            border: 1px solid #3f3f46;
            border-radius: 4px;
            color: #f4f4f5;
            padding: 8px;
            font-size: 13px;
            selection-background-color: #4338ca;
        }
        QTextEdit:focus {
            border: 1px solid #6366f1;
            background: #27272a;
        }
        QTextEdit:hover {
            border: 1px solid #52525b;
        }
    """)
    return text_edit


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
    ) -> tuple[str, bool]:
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
    ) -> tuple[str, bool]:
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
        default="Input",
        label="Title",
        tooltip="Dialog window title",
    ),
    PropertyDef(
        "prompt",
        PropertyType.STRING,
        default="Enter value:",
        label="Prompt",
        tooltip="Message displayed to the user",
    ),
    PropertyDef(
        "default_value",
        PropertyType.STRING,
        default="",
        label="Default Value",
        tooltip="Pre-filled value in the input field",
    ),
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
        title: Dialog window title (default: "Input")
        prompt: Message displayed to user (default: "Enter value:")
        default_value: Pre-filled value (default: "")
        password_mode: Hide input (default: False)

    Outputs:
        value: User input value
        confirmed: Whether OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: -> value, confirmed

    def __init__(self, node_id: str, name: str = "Input Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "InputDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("value", PortType.OUTPUT, DataType.STRING)
        self.add_output_port("confirmed", PortType.OUTPUT, DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            # Get config properties (now PropertyDefs, not input ports)
            title_raw = self.get_parameter("title", "Input")
            prompt_raw = self.get_parameter("prompt", "Enter value:")
            default_raw = self.get_parameter("default_value", "")
            password_mode = self.get_parameter("password_mode", False)

            # Resolve variables (supports {{variable}} syntax)
            title = str(context.resolve_value(title_raw) or "Input")
            prompt = str(context.resolve_value(prompt_raw) or "Enter value:")
            default_value = str(context.resolve_value(default_raw) or "")

            value = ""
            confirmed = False

            try:
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
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Message to display in tooltip",
        essential=True,
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=3000,
        min_value=500,
        max_value=30000,
        label="Duration (ms)",
        tooltip="Duration to show tooltip",
    ),
    PropertyDef(
        "bg_color",
        PropertyType.STRING,
        default="#ffffff",
        label="Background Color",
        tooltip="Background color (hex)",
    ),
    PropertyDef(
        "tooltip_text_color",
        PropertyType.STRING,
        default="#000000",
        label="Text Color",
        tooltip="Text color (hex)",
    ),
    PropertyDef(
        "position",
        PropertyType.CHOICE,
        default="cursor",
        choices=[
            "cursor",
            "top_left",
            "top_right",
            "bottom_left",
            "bottom_right",
            "center",
        ],
        label="Position",
        tooltip="Tooltip position on screen",
    ),
    PropertyDef(
        "click_to_dismiss",
        PropertyType.BOOLEAN,
        default=False,
        label="Click to Dismiss",
        tooltip="Allow clicking to close the tooltip",
    ),
    PropertyDef(
        "max_width",
        PropertyType.INTEGER,
        default=400,
        min_value=100,
        max_value=1000,
        label="Max Width",
        tooltip="Maximum width in pixels",
    ),
    PropertyDef(
        "tooltip_icon",
        PropertyType.CHOICE,
        default="none",
        choices=["none", "info", "warning", "error", "success"],
        label="Icon",
        tooltip="Icon to show in tooltip",
    ),
    PropertyDef(
        "fade_animation",
        PropertyType.BOOLEAN,
        default=True,
        label="Fade Animation",
        tooltip="Enable fade in/out animation",
    ),
)
@executable_node
class TooltipNode(BaseNode):
    """
    Display a tooltip at a specified position.

    Config (via @node_schema):
        message: Message to display (essential - shows widget)
        duration: Duration in milliseconds (default: 3000)
        bg_color: Background color hex (default: #ffffff)
        tooltip_text_color: Text color hex (default: #000000)
        position: Position: cursor, top_left, top_right, bottom_left, bottom_right, center
        click_to_dismiss: Allow clicking to close (default: False)
        max_width: Maximum width in pixels (default: 400)
        tooltip_icon: Icon type: none, info, warning, error, success (default: none)
        fade_animation: Enable fade animation (default: True)

    Inputs:
        message: Optional - overrides config if connected

    Outputs:
        success: Whether tooltip was shown
    """

    # @category: system
    # @requires: none
    # @ports: message -> success

    # Class-level tracking for tooltip stacking
    _active_tooltips: list = []  # Track active tooltip widgets for stacking
    _tooltip_height: int = 50  # Approximate height of a tooltip for stacking

    def __init__(self, node_id: str, name: str = "Show Tooltip", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TooltipNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")
            message = str(message)

            duration = int(self.get_parameter("duration", 3000) or 3000)
            bg_color = self.get_parameter("bg_color", "#ffffff")
            text_color = self.get_parameter("tooltip_text_color", "#000000")
            position = self.get_parameter("position", "cursor")
            click_to_dismiss = self.get_parameter("click_to_dismiss", False)
            max_width = int(self.get_parameter("max_width", 400) or 400)
            icon = self.get_parameter("tooltip_icon", "none")
            fade_animation = self.get_parameter("fade_animation", True)

            formatted_message = self._format_message_with_variables(message, context)

            if not message:
                self.set_output_value("success", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"shown": False},
                    "next_nodes": ["exec_out"],
                }

            await self._show_tooltip(
                formatted_message,
                duration,
                bg_color,
                text_color,
                position,
                click_to_dismiss,
                max_width,
                icon,
                fade_animation,
            )

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"shown": True},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    def _format_message_with_variables(
        self, original: str, context: "ExecutionContext"
    ) -> str:
        """Format message with variable values highlighted in bold blue."""
        import re
        import html

        pattern = re.compile(r"\{\{(\w+)\}\}")
        result = []
        last_end = 0

        for match in pattern.finditer(original):
            before = original[last_end : match.start()]
            result.append(html.escape(before))

            var_name = match.group(1)
            var_value = context.get_variable(var_name, match.group(0))
            escaped_value = html.escape(str(var_value))
            result.append(f'<b style="color: #0288D1;">{escaped_value}</b>')

            last_end = match.end()

        result.append(html.escape(original[last_end:]))

        return "".join(result)

    async def _show_tooltip(
        self,
        message: str,
        duration: int,
        bg_color: str,
        text_color: str,
        position: str,
        click_to_dismiss: bool,
        max_width: int,
        icon: str,
        fade_animation: bool,
    ) -> None:
        """Show a tooltip popup."""
        from PySide6.QtWidgets import QApplication, QLabel, QWidget, QHBoxLayout
        from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
        from PySide6.QtGui import QCursor, QFont, QScreen

        app = QApplication.instance()
        if app is None:
            return

        icon_map = {
            "info": "information",
            "warning": "warning",
            "error": "critical",
            "success": "check",
        }
        icon_char = {
            "info": "\u2139",
            "warning": "\u26a0",
            "error": "\u2717",
            "success": "\u2713",
        }

        container = QWidget()
        container.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )

        layout = QHBoxLayout(container)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        if icon != "none" and icon in icon_char:
            icon_label = QLabel(icon_char[icon])
            icon_label.setFont(QFont("Segoe UI", 14))
            icon_colors = {
                "info": "#0288D1",
                "warning": "#FF9800",
                "error": "#F44336",
                "success": "#4CAF50",
            }
            icon_label.setStyleSheet(f"color: {icon_colors.get(icon, text_color)};")
            layout.addWidget(icon_label)

        tooltip_label = QLabel()
        tooltip_label.setTextFormat(Qt.RichText)
        tooltip_label.setText(message)
        tooltip_label.setWordWrap(True)
        tooltip_label.setMaximumWidth(max_width)
        layout.addWidget(tooltip_label)

        container.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                color: {text_color};
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }}
            QLabel {{
                background-color: transparent;
                font-size: 13px;
            }}
        """)

        container.adjustSize()

        screen = app.primaryScreen()
        screen_geo = screen.availableGeometry()

        # Calculate stacking offset based on active tooltips
        stack_offset = len(TooltipNode._active_tooltips) * (container.height() + 5)

        if position == "cursor":
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() + 10
            y = cursor_pos.y() + 20 + stack_offset
        elif position == "top_left":
            x = screen_geo.x() + 20
            y = screen_geo.y() + 20 + stack_offset
        elif position == "top_right":
            x = screen_geo.right() - container.width() - 20
            y = screen_geo.y() + 20 + stack_offset
        elif position == "bottom_left":
            x = screen_geo.x() + 20
            y = screen_geo.bottom() - container.height() - 20 - stack_offset
        elif position == "bottom_right":
            x = screen_geo.right() - container.width() - 20
            y = screen_geo.bottom() - container.height() - 20 - stack_offset
        elif position == "center":
            x = screen_geo.center().x() - container.width() // 2
            y = screen_geo.center().y() - container.height() // 2 + stack_offset
        else:
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() + 10
            y = cursor_pos.y() + 20 + stack_offset

        if x + container.width() > screen_geo.right():
            x = screen_geo.right() - container.width()
        if y + container.height() > screen_geo.bottom():
            y = screen_geo.bottom() - container.height()

        container.move(x, y)

        # Track this tooltip for stacking
        TooltipNode._active_tooltips.append(container)

        if fade_animation:
            container.setWindowOpacity(0.0)
            container.show()
            fade_in = QPropertyAnimation(container, b"windowOpacity")
            fade_in.setDuration(150)
            fade_in.setStartValue(0.0)
            fade_in.setEndValue(1.0)
            fade_in.setEasingCurve(QEasingCurve.OutCubic)
            fade_in.start()
        else:
            container.show()

        follow_timer = None
        if position == "cursor":
            follow_timer = QTimer()

            def update_position():
                if container.isVisible():
                    pos = QCursor.pos()
                    container.move(pos.x() + 10, pos.y() + 20)

            follow_timer.timeout.connect(update_position)
            follow_timer.start(16)

        def hide_tooltip():
            if follow_timer:
                follow_timer.stop()

            # Remove from active tooltips list
            if container in TooltipNode._active_tooltips:
                TooltipNode._active_tooltips.remove(container)

            if fade_animation:
                fade_out = QPropertyAnimation(container, b"windowOpacity")
                fade_out.setDuration(150)
                fade_out.setStartValue(1.0)
                fade_out.setEndValue(0.0)
                fade_out.setEasingCurve(QEasingCurve.InCubic)
                fade_out.finished.connect(container.deleteLater)
                fade_out.start()
            else:
                container.hide()
                container.deleteLater()

        if click_to_dismiss:
            container.mousePressEvent = lambda e: hide_tooltip()

        QTimer.singleShot(duration, hide_tooltip)

        await asyncio.sleep(0.1)


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Notification",
        label="Title",
        tooltip="Notification title",
        essential=True,
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Notification message",
        essential=True,
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=5,
        min_value=1,
        max_value=30,
        label="Duration (seconds)",
        tooltip="How long to show the notification",
    ),
    PropertyDef(
        "icon_type",
        PropertyType.CHOICE,
        default="info",
        choices=["info", "warning", "error"],
        label="Icon",
        tooltip="Notification icon type",
    ),
    PropertyDef(
        "action_buttons",
        PropertyType.STRING,
        default="",
        label="Action Buttons",
        tooltip="Comma-separated button labels (Windows 10+)",
    ),
    PropertyDef(
        "play_sound",
        PropertyType.BOOLEAN,
        default=True,
        label="Play Sound",
        tooltip="Play notification sound",
    ),
    PropertyDef(
        "priority",
        PropertyType.CHOICE,
        default="normal",
        choices=["low", "normal", "high"],
        label="Priority",
        tooltip="Notification priority",
    ),
)
@executable_node
class SystemNotificationNode(BaseNode):
    """
    Display a Windows system notification (toast).

    Config (via @node_schema):
        title: Notification title (essential - shows widget)
        message: Notification message (essential - shows widget)
        duration: Duration in seconds (default: 5)
        icon_type: 'info', 'warning', 'error' (default: info)
        action_buttons: Comma-separated button labels (default: '')
        play_sound: Play notification sound (default: True)
        priority: low, normal, high (default: normal)

    Inputs:
        title: Optional - overrides config if connected
        message: Optional - overrides config if connected

    Outputs:
        success: Whether notification was shown
        click_action: True if user clicked the notification
    """

    # @category: system
    # @requires: none
    # @ports: title, message -> success, click_action

    def __init__(
        self, node_id: str, name: str = "System Notification", **kwargs
    ) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SystemNotificationNode"

    def _define_ports(self) -> None:
        self.add_input_port("title", DataType.STRING, required=False)
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("click_action", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_input_value("title")
            if title is None:
                title = self.get_parameter("title", "Notification")
            title = str(title)

            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")
            message = str(message)

            duration = int(self.get_parameter("duration", 5) or 5)
            icon_type = self.get_parameter("icon_type", "info")
            play_sound = self.get_parameter("play_sound", True)

            title = context.resolve_value(title)
            message = context.resolve_value(message)

            if not message and not title:
                self.set_output_value("success", False)
                self.set_output_value("click_action", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"shown": False},
                    "next_nodes": ["exec_out"],
                }

            shown, clicked = await self._show_notification(
                title, message, duration, icon_type, play_sound
            )

            self.set_output_value("success", shown)
            self.set_output_value("click_action", clicked)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"shown": shown, "clicked": clicked},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.set_output_value("click_action", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    async def _show_notification(
        self, title: str, message: str, duration: int, icon_type: str, play_sound: bool
    ) -> Tuple[bool, bool]:
        """Show a Windows system notification. Returns (shown, clicked)."""

        if sys.platform != "win32":
            return False, False

        try:
            from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QStyle
            from PySide6.QtCore import QTimer

            app = QApplication.instance()
            if app is None:
                return False, False

            tray = QSystemTrayIcon()

            style = app.style()
            icon_style_map = {
                "info": QStyle.StandardPixmap.SP_MessageBoxInformation,
                "warning": QStyle.StandardPixmap.SP_MessageBoxWarning,
                "error": QStyle.StandardPixmap.SP_MessageBoxCritical,
            }
            pixmap_type = icon_style_map.get(
                icon_type, QStyle.StandardPixmap.SP_MessageBoxInformation
            )
            tray.setIcon(style.standardIcon(pixmap_type))

            icon_map = {
                "info": QSystemTrayIcon.MessageIcon.Information,
                "warning": QSystemTrayIcon.MessageIcon.Warning,
                "error": QSystemTrayIcon.MessageIcon.Critical,
            }
            msg_icon = icon_map.get(icon_type, QSystemTrayIcon.MessageIcon.Information)

            clicked = False
            future = asyncio.get_event_loop().create_future()

            def on_clicked():
                nonlocal clicked
                clicked = True

            def on_timeout():
                if not future.done():
                    future.set_result(clicked)

            tray.messageClicked.connect(on_clicked)

            tray.show()
            tray.showMessage(title, message, msg_icon, duration * 1000)

            QTimer.singleShot(duration * 1000 + 500, on_timeout)

            await future

            tray.hide()
            return True, clicked

        except Exception:
            try:
                from win10toast import ToastNotifier

                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=duration, threaded=True)
                return True, False
            except ImportError:
                pass

        return False, False


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


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Progress",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="Processing...",
        label="Message",
        tooltip="Progress message",
        essential=True,
    ),
    PropertyDef(
        "show_percent",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Percent",
        tooltip="Show percentage value",
    ),
    PropertyDef(
        "allow_cancel",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Cancel",
        tooltip="Show cancel button",
    ),
    PropertyDef(
        "indeterminate",
        PropertyType.BOOLEAN,
        default=False,
        label="Indeterminate",
        tooltip="Show indeterminate progress bar",
    ),
)
@executable_node
class ProgressDialogNode(BaseNode):
    """
    Display a progress dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Progress')
        message: Progress message (essential - shows widget)
        show_percent: Show percentage (default: True)
        allow_cancel: Show cancel button (default: True)
        indeterminate: Show indeterminate bar (default: False)

    Inputs:
        value: Progress value 0-100

    Outputs:
        canceled: True if user canceled
    """

    # @category: system
    # @requires: none
    # @ports: value -> canceled

    def __init__(self, node_id: str, name: str = "Progress Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ProgressDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("value", DataType.INTEGER, required=False)
        self.add_output_port("canceled", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Progress")
            message = self.get_parameter("message", "Processing...")
            show_percent = self.get_parameter("show_percent", True)
            allow_cancel = self.get_parameter("allow_cancel", True)
            indeterminate = self.get_parameter("indeterminate", False)

            value = self.get_input_value("value")
            if value is None:
                value = 0
            value = int(value)
            value = max(0, min(100, value))

            title = context.resolve_value(title)
            message = context.resolve_value(message)

            try:
                from PySide6.QtWidgets import QProgressDialog, QApplication
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QProgressDialog(
                    message, "Cancel" if allow_cancel else None, 0, 100
                )
                dialog.setWindowTitle(title)
                dialog.setWindowModality(Qt.WindowModal)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)
                dialog.setAutoClose(False)
                dialog.setAutoReset(False)

                if indeterminate:
                    dialog.setRange(0, 0)
                else:
                    dialog.setValue(value)
                    if show_percent:
                        dialog.setLabelText(f"{message} ({value}%)")

                future = asyncio.get_event_loop().create_future()

                def on_canceled():
                    if not future.done():
                        future.set_result(True)

                if allow_cancel:
                    dialog.canceled.connect(on_canceled)

                dialog.show()

                if value >= 100 and not indeterminate:
                    await asyncio.sleep(0.5)
                    dialog.close()
                    canceled = False
                else:
                    try:
                        canceled = await asyncio.wait_for(future, timeout=0.5)
                    except asyncio.TimeoutError:
                        canceled = False
                        dialog.close()

            except ImportError:
                canceled = False

            self.set_output_value("canceled", canceled)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"canceled": canceled},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("canceled", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select File",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "filter",
        PropertyType.STRING,
        default="All Files (*.*)",
        label="Filter",
        tooltip="File filter (e.g., 'Text Files (*.txt);;All Files (*.*)')",
    ),
    PropertyDef(
        "multi_select",
        PropertyType.BOOLEAN,
        default=False,
        label="Multi-Select",
        tooltip="Allow selecting multiple files",
    ),
    PropertyDef(
        "start_directory",
        PropertyType.STRING,
        default="",
        label="Start Directory",
        tooltip="Initial directory",
    ),
)
@executable_node
class FilePickerDialogNode(BaseNode):
    """
    Display a file picker dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Select File')
        filter: File filter (default: 'All Files (*.*)')
        multi_select: Allow multiple selection (default: False)
        start_directory: Initial directory (default: '')

    Outputs:
        file_path: Selected file path(s) - string or list
        selected: True if file was selected
    """

    # @category: system
    # @requires: none
    # @ports: none -> file_path, selected

    def __init__(self, node_id: str, name: str = "File Picker", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FilePickerDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("file_path", DataType.ANY)
        self.add_output_port("selected", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Select File")
            file_filter = self.get_parameter("filter", "All Files (*.*)")
            multi_select = self.get_parameter("multi_select", False)
            start_dir = self.get_parameter("start_directory", "")

            title = context.resolve_value(title)
            start_dir = context.resolve_value(start_dir)

            try:
                from PySide6.QtWidgets import QFileDialog, QApplication
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QFileDialog()
                dialog.setWindowTitle(title)
                dialog.setNameFilter(file_filter)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                if start_dir:
                    dialog.setDirectory(start_dir)

                if multi_select:
                    dialog.setFileMode(QFileDialog.ExistingFiles)
                else:
                    dialog.setFileMode(QFileDialog.ExistingFile)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QFileDialog.Accepted:
                            files = dialog.selectedFiles()
                            if multi_select:
                                future.set_result((files, True))
                            else:
                                future.set_result(
                                    (files[0] if files else "", bool(files))
                                )
                        else:
                            future.set_result(("" if not multi_select else [], False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                file_path, selected = await future

            except ImportError:
                file_path = "" if not multi_select else []
                selected = False

            self.set_output_value("file_path", file_path)
            self.set_output_value("selected", selected)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"file_path": file_path, "selected": selected},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("file_path", "")
            self.set_output_value("selected", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select Folder",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "start_directory",
        PropertyType.STRING,
        default="",
        label="Start Directory",
        tooltip="Initial directory",
    ),
)
@executable_node
class FolderPickerDialogNode(BaseNode):
    """
    Display a folder picker dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Select Folder')
        start_directory: Initial directory (default: '')

    Outputs:
        folder_path: Selected folder path
        selected: True if folder was selected
    """

    # @category: system
    # @requires: none
    # @ports: none -> folder_path, selected

    def __init__(self, node_id: str, name: str = "Folder Picker", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FolderPickerDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("folder_path", DataType.STRING)
        self.add_output_port("selected", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Select Folder")
            start_dir = self.get_parameter("start_directory", "")

            title = context.resolve_value(title)
            start_dir = context.resolve_value(start_dir)

            try:
                from PySide6.QtWidgets import QFileDialog, QApplication
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QFileDialog()
                dialog.setWindowTitle(title)
                dialog.setFileMode(QFileDialog.Directory)
                dialog.setOption(QFileDialog.ShowDirsOnly, True)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                if start_dir:
                    dialog.setDirectory(start_dir)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QFileDialog.Accepted:
                            folders = dialog.selectedFiles()
                            future.set_result(
                                (folders[0] if folders else "", bool(folders))
                            )
                        else:
                            future.set_result(("", False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                folder_path, selected = await future

            except ImportError:
                folder_path = ""
                selected = False

            self.set_output_value("folder_path", folder_path)
            self.set_output_value("selected", selected)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"folder_path": folder_path, "selected": selected},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("folder_path", "")
            self.set_output_value("selected", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select Color",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "initial_color",
        PropertyType.STRING,
        default="#ffffff",
        label="Initial Color",
        tooltip="Initial color (hex)",
    ),
    PropertyDef(
        "show_alpha",
        PropertyType.BOOLEAN,
        default=False,
        label="Show Alpha",
        tooltip="Show alpha channel slider",
    ),
)
@executable_node
class ColorPickerDialogNode(BaseNode):
    """
    Display a color picker dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Select Color')
        initial_color: Initial color hex (default: '#ffffff')
        show_alpha: Show alpha channel (default: False)

    Outputs:
        color: Selected color (hex string)
        selected: True if color was selected
        rgb: RGB dict with r, g, b, a keys
    """

    # @category: system
    # @requires: none
    # @ports: none -> color, selected, rgb

    def __init__(self, node_id: str, name: str = "Color Picker", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ColorPickerDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("color", DataType.STRING)
        self.add_output_port("selected", DataType.BOOLEAN)
        self.add_output_port("rgb", DataType.DICT)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Select Color")
            initial_color = self.get_parameter("initial_color", "#ffffff")
            show_alpha = self.get_parameter("show_alpha", False)

            title = context.resolve_value(title)
            initial_color = context.resolve_value(initial_color)

            try:
                from PySide6.QtWidgets import QColorDialog, QApplication
                from PySide6.QtGui import QColor
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QColorDialog()
                dialog.setWindowTitle(title)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                if initial_color:
                    dialog.setCurrentColor(QColor(initial_color))

                if show_alpha:
                    dialog.setOption(QColorDialog.ShowAlphaChannel, True)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QColorDialog.Accepted:
                            color = dialog.currentColor()
                            hex_color = color.name(
                                QColor.HexArgb if show_alpha else QColor.HexRgb
                            )
                            rgb_dict = {
                                "r": color.red(),
                                "g": color.green(),
                                "b": color.blue(),
                                "a": color.alpha(),
                            }
                            future.set_result((hex_color, True, rgb_dict))
                        else:
                            future.set_result(("", False, {}))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                color, selected, rgb = await future

            except ImportError:
                color = ""
                selected = False
                rgb = {}

            self.set_output_value("color", color)
            self.set_output_value("selected", selected)
            self.set_output_value("rgb", rgb)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"color": color, "selected": selected, "rgb": rgb},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("color", "")
            self.set_output_value("selected", False)
            self.set_output_value("rgb", {})
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select Date/Time",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "mode",
        PropertyType.CHOICE,
        default="datetime",
        choices=["date", "time", "datetime"],
        label="Mode",
        tooltip="Selection mode",
    ),
    PropertyDef(
        "format",
        PropertyType.STRING,
        default="yyyy-MM-dd HH:mm:ss",
        label="Format",
        tooltip="Output format",
    ),
    PropertyDef(
        "min_date",
        PropertyType.STRING,
        default="",
        label="Min Date",
        tooltip="Minimum date (YYYY-MM-DD)",
    ),
    PropertyDef(
        "max_date",
        PropertyType.STRING,
        default="",
        label="Max Date",
        tooltip="Maximum date (YYYY-MM-DD)",
    ),
)
@executable_node
class DateTimePickerDialogNode(BaseNode):
    """
    Display a date/time picker dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Select Date/Time')
        mode: date, time, datetime (default: datetime)
        format: Output format (default: 'yyyy-MM-dd HH:mm:ss')
        min_date: Minimum date YYYY-MM-DD (default: '')
        max_date: Maximum date YYYY-MM-DD (default: '')

    Outputs:
        value: Formatted date/time string
        timestamp: Unix timestamp (seconds)
        selected: True if value was selected
    """

    # @category: system
    # @requires: none
    # @ports: none -> value, timestamp, selected

    def __init__(self, node_id: str, name: str = "DateTime Picker", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "DateTimePickerDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("value", DataType.STRING)
        self.add_output_port("timestamp", DataType.INTEGER)
        self.add_output_port("selected", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Select Date/Time")
            mode = self.get_parameter("mode", "datetime")
            format_str = self.get_parameter("format", "yyyy-MM-dd HH:mm:ss")
            min_date = self.get_parameter("min_date", "")
            max_date = self.get_parameter("max_date", "")

            title = context.resolve_value(title)

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QDialogButtonBox,
                    QDateTimeEdit,
                    QDateEdit,
                    QTimeEdit,
                    QApplication,
                    QLabel,
                )
                from PySide6.QtCore import Qt, QDateTime, QDate, QTime

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                if mode == "date":
                    picker = QDateEdit()
                    picker.setCalendarPopup(True)
                    picker.setDate(QDate.currentDate())
                    if min_date:
                        picker.setMinimumDate(QDate.fromString(min_date, "yyyy-MM-dd"))
                    if max_date:
                        picker.setMaximumDate(QDate.fromString(max_date, "yyyy-MM-dd"))
                elif mode == "time":
                    picker = QTimeEdit()
                    picker.setTime(QTime.currentTime())
                else:
                    picker = QDateTimeEdit()
                    picker.setCalendarPopup(True)
                    picker.setDateTime(QDateTime.currentDateTime())
                    if min_date:
                        picker.setMinimumDate(QDate.fromString(min_date, "yyyy-MM-dd"))
                    if max_date:
                        picker.setMaximumDate(QDate.fromString(max_date, "yyyy-MM-dd"))

                picker.setDisplayFormat(format_str)
                layout.addWidget(picker)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            if mode == "date":
                                dt = QDateTime(picker.date(), QTime(0, 0, 0))
                            elif mode == "time":
                                dt = QDateTime(QDate.currentDate(), picker.time())
                            else:
                                dt = picker.dateTime()

                            value_str = dt.toString(format_str)
                            timestamp = int(dt.toSecsSinceEpoch())
                            future.set_result((value_str, timestamp, True))
                        else:
                            future.set_result(("", 0, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                value, timestamp, selected = await future

            except ImportError:
                from datetime import datetime as dt

                now = dt.now()
                value = now.strftime("%Y-%m-%d %H:%M:%S")
                timestamp = int(now.timestamp())
                selected = True

            self.set_output_value("value", value)
            self.set_output_value("timestamp", timestamp)
            self.set_output_value("selected", selected)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"value": value, "timestamp": timestamp, "selected": selected},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("value", "")
            self.set_output_value("timestamp", 0)
            self.set_output_value("selected", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Snackbar message",
        essential=True,
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=3000,
        min_value=1000,
        max_value=10000,
        label="Duration (ms)",
        tooltip="Display duration",
    ),
    PropertyDef(
        "position",
        PropertyType.CHOICE,
        default="bottom_center",
        choices=["bottom_left", "bottom_center", "bottom_right"],
        label="Position",
        tooltip="Snackbar position",
    ),
    PropertyDef(
        "action_text",
        PropertyType.STRING,
        default="",
        label="Action Text",
        tooltip="Action button text (empty to hide)",
    ),
    PropertyDef(
        "bg_color",
        PropertyType.STRING,
        default="#323232",
        label="Background Color",
        tooltip="Background color (hex)",
    ),
)
@executable_node
class SnackbarNode(BaseNode):
    """
    Display a Material-style snackbar notification.

    Config (via @node_schema):
        message: Snackbar message (essential - shows widget)
        duration: Display duration in ms (default: 3000)
        position: bottom_left, bottom_center, bottom_right (default: bottom_center)
        action_text: Action button text (default: '')
        bg_color: Background color hex (default: '#323232')

    Outputs:
        action_clicked: True if action button was clicked
        success: True if snackbar was shown
    """

    # @category: system
    # @requires: none
    # @ports: message -> action_clicked, success

    def __init__(self, node_id: str, name: str = "Snackbar", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SnackbarNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("action_clicked", DataType.BOOLEAN)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")
            message = str(message)

            duration = int(self.get_parameter("duration", 3000) or 3000)
            position = self.get_parameter("position", "bottom_center")
            action_text = self.get_parameter("action_text", "")
            bg_color = self.get_parameter("bg_color", "#323232")

            message = context.resolve_value(message)
            action_text = context.resolve_value(action_text)

            if not message:
                self.set_output_value("action_clicked", False)
                self.set_output_value("success", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"shown": False},
                    "next_nodes": ["exec_out"],
                }

            action_clicked = await self._show_snackbar(
                message, duration, position, action_text, bg_color
            )

            self.set_output_value("action_clicked", action_clicked)
            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"action_clicked": action_clicked, "shown": True},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("action_clicked", False)
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    async def _show_snackbar(
        self,
        message: str,
        duration: int,
        position: str,
        action_text: str,
        bg_color: str,
    ) -> bool:
        """Show a Material-style snackbar."""
        from PySide6.QtWidgets import (
            QWidget,
            QLabel,
            QPushButton,
            QHBoxLayout,
            QApplication,
            QGraphicsOpacityEffect,
        )
        from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
        from PySide6.QtGui import QFont

        app = QApplication.instance()
        if app is None:
            return False

        snackbar = QWidget()
        snackbar.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        snackbar.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(snackbar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 11))
        layout.addWidget(msg_label, 1)

        action_clicked = False

        if action_text:
            action_btn = QPushButton(action_text.upper())
            action_btn.setFlat(True)
            action_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            action_btn.setCursor(Qt.PointingHandCursor)
            action_btn.setStyleSheet("""
                QPushButton {
                    color: #BB86FC;
                    background: transparent;
                    border: none;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    background: rgba(187, 134, 252, 0.1);
                }
            """)

            def on_action():
                nonlocal action_clicked
                action_clicked = True
                snackbar.close()

            action_btn.clicked.connect(on_action)
            layout.addWidget(action_btn)

        snackbar.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border-radius: 4px;
            }}
            QLabel {{
                color: #ffffff;
                background: transparent;
            }}
        """)

        snackbar.adjustSize()

        screen = app.primaryScreen()
        screen_geo = screen.availableGeometry()

        if position == "bottom_left":
            x = screen_geo.x() + 24
        elif position == "bottom_right":
            x = screen_geo.right() - snackbar.width() - 24
        else:
            x = screen_geo.center().x() - snackbar.width() // 2

        y = screen_geo.bottom() - snackbar.height() - 24

        snackbar.move(x, y)

        snackbar.setWindowOpacity(0.0)
        snackbar.show()

        fade_in = QPropertyAnimation(snackbar, b"windowOpacity")
        fade_in.setDuration(150)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        fade_in.start()

        future = asyncio.get_event_loop().create_future()

        def hide_snackbar():
            fade_out = QPropertyAnimation(snackbar, b"windowOpacity")
            fade_out.setDuration(150)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InCubic)
            fade_out.finished.connect(lambda: complete())
            fade_out.start()

        def complete():
            snackbar.deleteLater()
            if not future.done():
                future.set_result(action_clicked)

        QTimer.singleShot(duration, hide_snackbar)

        return await future


@node_schema(
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="",
        label="Message",
        tooltip="Balloon tip message",
        essential=True,
    ),
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="",
        label="Title",
        tooltip="Balloon tip title",
    ),
    PropertyDef(
        "x",
        PropertyType.INTEGER,
        default=0,
        label="X Position",
        tooltip="X position on screen (0 = cursor)",
    ),
    PropertyDef(
        "y",
        PropertyType.INTEGER,
        default=0,
        label="Y Position",
        tooltip="Y position on screen (0 = cursor)",
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=5000,
        min_value=1000,
        max_value=30000,
        label="Duration (ms)",
        tooltip="Display duration",
    ),
    PropertyDef(
        "icon_type",
        PropertyType.CHOICE,
        default="info",
        choices=["none", "info", "warning", "error"],
        label="Icon",
        tooltip="Balloon icon type",
    ),
)
@executable_node
class BalloonTipNode(BaseNode):
    """
    Display a balloon tooltip at a screen position.

    Config (via @node_schema):
        message: Balloon message (essential - shows widget)
        title: Balloon title (default: '')
        x: X position (0 = cursor) (default: 0)
        y: Y position (0 = cursor) (default: 0)
        duration: Display duration in ms (default: 5000)
        icon_type: none, info, warning, error (default: info)

    Outputs:
        success: True if balloon was shown
    """

    # @category: system
    # @requires: none
    # @ports: message -> success

    def __init__(self, node_id: str, name: str = "Balloon Tip", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "BalloonTipNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "")
            message = str(message)

            title = self.get_parameter("title", "")
            x = int(self.get_parameter("x", 0) or 0)
            y = int(self.get_parameter("y", 0) or 0)
            duration = int(self.get_parameter("duration", 5000) or 5000)
            icon_type = self.get_parameter("icon_type", "info")

            message = context.resolve_value(message)
            title = context.resolve_value(title)

            if not message:
                self.set_output_value("success", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"shown": False},
                    "next_nodes": ["exec_out"],
                }

            await self._show_balloon(message, title, x, y, duration, icon_type)

            self.set_output_value("success", True)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"shown": True},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}

    async def _show_balloon(
        self,
        message: str,
        title: str,
        x: int,
        y: int,
        duration: int,
        icon_type: str,
    ) -> None:
        """Show a balloon tooltip."""
        from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
        from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
        from PySide6.QtGui import QCursor, QFont, QPainter, QPainterPath, QColor, QPen

        app = QApplication.instance()
        if app is None:
            return

        class BalloonWidget(QWidget):
            def __init__(self):
                super().__init__()
                self.setWindowFlags(
                    Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                )
                self.setAttribute(Qt.WA_TranslucentBackground)
                self._tail_pos = "bottom"

            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.Antialiasing)

                bg_color = QColor("#fffde7")
                border_color = QColor("#ffc107")

                path = QPainterPath()
                rect = self.rect().adjusted(1, 1, -1, -11)
                path.addRoundedRect(rect, 6, 6)

                tail_x = 20
                tail_y = rect.bottom()
                path.moveTo(tail_x, tail_y)
                path.lineTo(tail_x + 8, tail_y + 10)
                path.lineTo(tail_x + 16, tail_y)

                painter.fillPath(path, bg_color)
                painter.setPen(QPen(border_color, 1))
                painter.drawPath(path)

        balloon = BalloonWidget()
        layout = QVBoxLayout(balloon)
        layout.setContentsMargins(12, 8, 12, 18)
        layout.setSpacing(4)

        icon_chars = {
            "info": "\u2139",
            "warning": "\u26a0",
            "error": "\u2717",
        }
        icon_colors = {
            "info": "#0288D1",
            "warning": "#FF9800",
            "error": "#F44336",
        }

        if title or icon_type != "none":
            title_layout = QVBoxLayout()
            title_layout.setSpacing(4)

            if icon_type != "none" and icon_type in icon_chars:
                icon_label = QLabel(icon_chars[icon_type])
                icon_label.setFont(QFont("Segoe UI", 14))
                icon_label.setStyleSheet(
                    f"color: {icon_colors.get(icon_type, '#000')};"
                )
                title_layout.addWidget(icon_label)

            if title:
                title_label = QLabel(title)
                title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
                title_label.setStyleSheet("color: #212121;")
                title_layout.addWidget(title_label)

            layout.addLayout(title_layout)

        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setStyleSheet("color: #424242;")
        msg_label.setWordWrap(True)
        msg_label.setMaximumWidth(300)
        layout.addWidget(msg_label)

        balloon.adjustSize()

        if x == 0 and y == 0:
            cursor_pos = QCursor.pos()
            x = cursor_pos.x() - 20
            y = cursor_pos.y() - balloon.height() - 10
        else:
            y = y - balloon.height() - 10

        screen = app.primaryScreen()
        screen_geo = screen.availableGeometry()

        if x + balloon.width() > screen_geo.right():
            x = screen_geo.right() - balloon.width()
        if x < screen_geo.x():
            x = screen_geo.x()
        if y < screen_geo.y():
            y = screen_geo.y() + 20

        balloon.move(x, y)

        balloon.setWindowOpacity(0.0)
        balloon.show()

        fade_in = QPropertyAnimation(balloon, b"windowOpacity")
        fade_in.setDuration(200)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.OutCubic)
        fade_in.start()

        def hide_balloon():
            fade_out = QPropertyAnimation(balloon, b"windowOpacity")
            fade_out.setDuration(200)
            fade_out.setStartValue(1.0)
            fade_out.setEndValue(0.0)
            fade_out.setEasingCurve(QEasingCurve.InCubic)
            fade_out.finished.connect(balloon.deleteLater)
            fade_out.start()

        QTimer.singleShot(duration, hide_balloon)

        await asyncio.sleep(0.1)


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Select Item",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "items",
        PropertyType.STRING,
        default="",
        label="Items",
        tooltip="Items to display (comma-separated or JSON array)",
        essential=True,
    ),
    PropertyDef(
        "multi_select",
        PropertyType.BOOLEAN,
        default=False,
        label="Multi-Select",
        tooltip="Allow selecting multiple items",
    ),
    PropertyDef(
        "search_enabled",
        PropertyType.BOOLEAN,
        default=True,
        label="Enable Search",
        tooltip="Show search/filter box",
    ),
    PropertyDef(
        "default_selection",
        PropertyType.STRING,
        default="",
        label="Default Selection",
        tooltip="Default selected item(s)",
    ),
)
@executable_node
class ListPickerDialogNode(BaseNode):
    """
    Display a list picker dialog for single/multi-select.

    Config (via @node_schema):
        title: Dialog title (default: 'Select Item')
        items: Items to display, comma-separated or JSON array (essential)
        multi_select: Allow multiple selection (default: False)
        search_enabled: Show search box (default: True)
        default_selection: Pre-selected item(s) (default: '')

    Inputs:
        items: Optional - overrides config if connected

    Outputs:
        selected: Selected item(s) - string or list
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: items -> selected, confirmed

    def __init__(self, node_id: str, name: str = "List Picker", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ListPickerDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("items", DataType.ANY, required=False)
        self.add_output_port("selected", DataType.ANY)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Select Item")
            items_input = self.get_input_value("items")
            if items_input is None:
                items_input = self.get_parameter("items", "")

            multi_select = self.get_parameter("multi_select", False)
            search_enabled = self.get_parameter("search_enabled", True)
            default_selection = self.get_parameter("default_selection", "")

            title = context.resolve_value(title)

            # Parse items - can be list, comma-separated string, or JSON array
            if isinstance(items_input, list):
                items = items_input
            elif isinstance(items_input, str):
                items_input = context.resolve_value(items_input)
                try:
                    items = json.loads(items_input)
                except json.JSONDecodeError:
                    items = [
                        item.strip() for item in items_input.split(",") if item.strip()
                    ]
            else:
                items = []

            if not items:
                self.set_output_value("selected", [] if multi_select else "")
                self.set_output_value("confirmed", False)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"selected": None},
                    "next_nodes": ["exec_out"],
                }

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QHBoxLayout,
                    QListWidget,
                    QListWidgetItem,
                    QLineEdit,
                    QDialogButtonBox,
                    QApplication,
                    QAbstractItemView,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(300, 400)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                # Search box
                search_box = None
                if search_enabled:
                    search_box = _create_styled_line_edit(placeholder="Search...")
                    layout.addWidget(search_box)

                # List widget
                list_widget = QListWidget()
                if multi_select:
                    list_widget.setSelectionMode(QAbstractItemView.MultiSelection)
                else:
                    list_widget.setSelectionMode(QAbstractItemView.SingleSelection)

                for item in items:
                    list_item = QListWidgetItem(str(item))
                    list_widget.addItem(list_item)
                    if default_selection:
                        if (
                            str(item) == default_selection
                            or str(item) in default_selection
                        ):
                            list_item.setSelected(True)

                layout.addWidget(list_widget)

                # Filter function
                if search_box:

                    def filter_items(text):
                        for i in range(list_widget.count()):
                            item = list_widget.item(i)
                            item.setHidden(text.lower() not in item.text().lower())

                    search_box.textChanged.connect(filter_items)

                # Buttons
                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            selected_items = [
                                item.text() for item in list_widget.selectedItems()
                            ]
                            if multi_select:
                                future.set_result((selected_items, True))
                            else:
                                future.set_result(
                                    (selected_items[0] if selected_items else "", True)
                                )
                        else:
                            future.set_result(([] if multi_select else "", False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                selected, confirmed = await future

            except ImportError:
                selected = items[0] if items else ""
                confirmed = True

            self.set_output_value("selected", selected)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"selected": selected, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("selected", "")
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Enter Text",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "default_text",
        PropertyType.TEXT,
        default="",
        label="Default Text",
        tooltip="Default text in the input area",
    ),
    PropertyDef(
        "placeholder",
        PropertyType.STRING,
        default="",
        label="Placeholder",
        tooltip="Placeholder text when empty",
    ),
    PropertyDef(
        "max_chars",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        label="Max Characters",
        tooltip="Maximum character limit (0 = unlimited)",
    ),
)
@executable_node
class MultilineInputDialogNode(BaseNode):
    """
    Display a multi-line text input dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Enter Text')
        default_text: Default text (default: '')
        placeholder: Placeholder text (default: '')
        max_chars: Max characters, 0 = unlimited (default: 0)

    Outputs:
        text: Entered text
        confirmed: True if OK was clicked
        char_count: Number of characters entered
    """

    # @category: system
    # @requires: none
    # @ports: none -> text, confirmed, char_count

    def __init__(self, node_id: str, name: str = "Multiline Input", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "MultilineInputDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("text", DataType.STRING)
        self.add_output_port("confirmed", DataType.BOOLEAN)
        self.add_output_port("char_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Enter Text")
            default_text = self.get_parameter("default_text", "")
            placeholder = self.get_parameter("placeholder", "")
            max_chars = int(self.get_parameter("max_chars", 0) or 0)

            title = context.resolve_value(title)
            default_text = context.resolve_value(default_text)

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QTextEdit,
                    QDialogButtonBox,
                    QApplication,
                    QLabel,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(400, 300)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                text_edit = _create_styled_text_edit(
                    placeholder=placeholder or "",
                    text=default_text,
                )
                layout.addWidget(text_edit)

                # Character counter
                char_label = QLabel(f"Characters: {len(default_text)}")
                layout.addWidget(char_label)

                def on_text_changed():
                    current_text = text_edit.toPlainText()
                    if max_chars > 0 and len(current_text) > max_chars:
                        text_edit.setPlainText(current_text[:max_chars])
                        from PySide6.QtGui import QTextCursor

                        text_edit.moveCursor(QTextCursor.MoveOperation.End)
                    char_label.setText(f"Characters: {len(text_edit.toPlainText())}")

                text_edit.textChanged.connect(on_text_changed)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            entered_text = text_edit.toPlainText()
                            future.set_result((entered_text, True, len(entered_text)))
                        else:
                            future.set_result(("", False, 0))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                text, confirmed, char_count = await future

            except ImportError:
                text = default_text
                confirmed = True
                char_count = len(text)

            self.set_output_value("text", text)
            self.set_output_value("confirmed", confirmed)
            self.set_output_value("char_count", char_count)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {
                    "text": text,
                    "confirmed": confirmed,
                    "char_count": char_count,
                },
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("text", "")
            self.set_output_value("confirmed", False)
            self.set_output_value("char_count", 0)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Login",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "username_label",
        PropertyType.STRING,
        default="Username:",
        label="Username Label",
        tooltip="Label for username field",
    ),
    PropertyDef(
        "password_label",
        PropertyType.STRING,
        default="Password:",
        label="Password Label",
        tooltip="Label for password field",
    ),
    PropertyDef(
        "show_remember",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Remember Me",
        tooltip="Show 'Remember me' checkbox",
    ),
    PropertyDef(
        "mask_password",
        PropertyType.BOOLEAN,
        default=True,
        label="Mask Password",
        tooltip="Hide password characters",
    ),
)
@executable_node
class CredentialDialogNode(BaseNode):
    """
    Display a username/password credential dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Login')
        username_label: Label for username (default: 'Username:')
        password_label: Label for password (default: 'Password:')
        show_remember: Show remember checkbox (default: True)
        mask_password: Mask password input (default: True)

    Outputs:
        username: Entered username
        password: Entered password
        remember: Whether remember was checked
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: none -> username, password, remember, confirmed

    def __init__(self, node_id: str, name: str = "Credential Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "CredentialDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("username", DataType.STRING)
        self.add_output_port("password", DataType.STRING)
        self.add_output_port("remember", DataType.BOOLEAN)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            title = self.get_parameter("title", "Login")
            username_label = self.get_parameter("username_label", "Username:")
            password_label = self.get_parameter("password_label", "Password:")
            show_remember = self.get_parameter("show_remember", True)
            mask_password = self.get_parameter("mask_password", True)

            title = context.resolve_value(title)

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QFormLayout,
                    QLineEdit,
                    QCheckBox,
                    QDialogButtonBox,
                    QApplication,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumWidth(300)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)
                form = QFormLayout()

                username_input = _create_styled_line_edit()
                form.addRow(username_label, username_input)

                password_input = _create_styled_line_edit(
                    echo_mode=QLineEdit.Password if mask_password else None,
                )
                form.addRow(password_label, password_input)

                layout.addLayout(form)

                remember_check = None
                if show_remember:
                    remember_check = QCheckBox("Remember me")
                    layout.addWidget(remember_check)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            remember = (
                                remember_check.isChecked() if remember_check else False
                            )
                            future.set_result(
                                (
                                    username_input.text(),
                                    password_input.text(),
                                    remember,
                                    True,
                                )
                            )
                        else:
                            future.set_result(("", "", False, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                username, password, remember, confirmed = await future

            except ImportError:
                username = ""
                password = ""
                remember = False
                confirmed = False

            self.set_output_value("username", username)
            self.set_output_value("password", password)
            self.set_output_value("remember", remember)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"username": username, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("username", "")
            self.set_output_value("password", "")
            self.set_output_value("remember", False)
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Form",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "fields",
        PropertyType.JSON,
        default="[]",
        label="Fields (JSON)",
        tooltip='JSON array: [{"name": "field1", "type": "text", "label": "Field 1", "required": true}]',
        essential=True,
    ),
)
@executable_node
class FormDialogNode(BaseNode):
    """
    Display a custom form dialog with dynamic fields.

    Config (via @node_schema):
        title: Dialog title (default: 'Form')
        fields: JSON array defining fields (essential)
            Each field: {"name": "id", "type": "text|number|checkbox|select", "label": "...", "required": bool, "options": [...]}

    Outputs:
        data: Dictionary of field values
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: fields -> data, confirmed

    def __init__(self, node_id: str, name: str = "Form Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "FormDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("fields", DataType.ANY, required=False)
        self.add_output_port("data", DataType.DICT)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Form")
            fields_input = self.get_input_value("fields")
            if fields_input is None:
                fields_input = self.get_parameter("fields", "[]")

            title = context.resolve_value(title)

            if isinstance(fields_input, str):
                fields_input = context.resolve_value(fields_input)
                try:
                    fields = json.loads(fields_input)
                except json.JSONDecodeError:
                    fields = []
            elif isinstance(fields_input, list):
                fields = fields_input
            else:
                fields = []

            if not fields:
                self.set_output_value("data", {})
                self.set_output_value("confirmed", False)
                self.status = NodeStatus.SUCCESS
                return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QFormLayout,
                    QLineEdit,
                    QSpinBox,
                    QDoubleSpinBox,
                    QCheckBox,
                    QComboBox,
                    QDialogButtonBox,
                    QApplication,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumWidth(350)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)
                form = QFormLayout()

                widgets = {}
                for field in fields:
                    field_name = field.get("name", "")
                    field_type = field.get("type", "text")
                    field_label = field.get("label", field_name)
                    field_default = field.get("default", "")
                    field_options = field.get("options", [])

                    if field_type == "text":
                        widget = _create_styled_line_edit(text=str(field_default))
                        widgets[field_name] = ("text", widget)
                    elif field_type == "number":
                        if isinstance(field_default, float):
                            widget = QDoubleSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(float(field_default or 0))
                        else:
                            widget = QSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(int(field_default or 0))
                        widgets[field_name] = ("number", widget)
                    elif field_type == "checkbox":
                        widget = QCheckBox()
                        widget.setChecked(bool(field_default))
                        widgets[field_name] = ("checkbox", widget)
                    elif field_type == "select":
                        widget = QComboBox()
                        widget.addItems([str(opt) for opt in field_options])
                        if field_default and str(field_default) in [
                            str(o) for o in field_options
                        ]:
                            widget.setCurrentText(str(field_default))
                        widgets[field_name] = ("select", widget)
                    else:
                        widget = _create_styled_line_edit(text=str(field_default))
                        widgets[field_name] = ("text", widget)

                    form.addRow(field_label, widget)

                layout.addLayout(form)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            form_data = {}
                            for name, (ftype, widget) in widgets.items():
                                if ftype == "text":
                                    form_data[name] = widget.text()
                                elif ftype == "number":
                                    form_data[name] = widget.value()
                                elif ftype == "checkbox":
                                    form_data[name] = widget.isChecked()
                                elif ftype == "select":
                                    form_data[name] = widget.currentText()
                            future.set_result((form_data, True))
                        else:
                            future.set_result(({}, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                data, confirmed = await future

            except ImportError:
                data = {}
                confirmed = False

            self.set_output_value("data", data)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"data": data, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("data", {})
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "image_path",
        PropertyType.FILE_PATH,
        default="",
        label="Image Path",
        tooltip="Path to image file",
        essential=True,
    ),
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Image Preview",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "scale",
        PropertyType.FLOAT,
        default=1.0,
        min_value=0.1,
        max_value=5.0,
        label="Scale",
        tooltip="Image scale factor",
    ),
    PropertyDef(
        "allow_zoom",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Zoom",
        tooltip="Enable mouse wheel zoom",
    ),
)
@executable_node
class ImagePreviewDialogNode(BaseNode):
    """
    Display an image preview dialog.

    Config (via @node_schema):
        image_path: Path to image (essential)
        title: Dialog title (default: 'Image Preview')
        scale: Initial scale factor (default: 1.0)
        allow_zoom: Enable zoom with mouse wheel (default: True)

    Inputs:
        image_path: Optional - overrides config if connected

    Outputs:
        confirmed: True if OK was clicked
        canceled: True if Cancel was clicked
    """

    # @category: system
    # @requires: none
    # @ports: image_path -> confirmed, canceled

    def __init__(self, node_id: str, name: str = "Image Preview", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "ImagePreviewDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("image_path", DataType.STRING, required=False)
        self.add_output_port("confirmed", DataType.BOOLEAN)
        self.add_output_port("canceled", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import os

            image_path = self.get_input_value("image_path")
            if image_path is None:
                image_path = self.get_parameter("image_path", "")
            image_path = context.resolve_value(str(image_path))

            title = self.get_parameter("title", "Image Preview")
            scale = float(self.get_parameter("scale", 1.0) or 1.0)
            allow_zoom = self.get_parameter("allow_zoom", True)

            title = context.resolve_value(title)

            if not image_path or not os.path.exists(image_path):
                self.set_output_value("confirmed", False)
                self.set_output_value("canceled", True)
                self.status = NodeStatus.SUCCESS
                return {
                    "success": True,
                    "data": {"error": "Image not found"},
                    "next_nodes": ["exec_out"],
                }

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QLabel,
                    QScrollArea,
                    QDialogButtonBox,
                    QApplication,
                )
                from PySide6.QtCore import Qt
                from PySide6.QtGui import QPixmap

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(400, 300)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                scroll = QScrollArea()
                scroll.setWidgetResizable(True)

                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        int(pixmap.width() * scale),
                        int(pixmap.height() * scale),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )

                    label = QLabel()
                    label.setPixmap(scaled_pixmap)
                    label.setAlignment(Qt.AlignCenter)

                    if allow_zoom:
                        current_scale = [scale]

                        def wheel_event(event):
                            delta = event.angleDelta().y()
                            if delta > 0:
                                current_scale[0] *= 1.1
                            else:
                                current_scale[0] /= 1.1
                            current_scale[0] = max(0.1, min(5.0, current_scale[0]))
                            new_pixmap = pixmap.scaled(
                                int(pixmap.width() * current_scale[0]),
                                int(pixmap.height() * current_scale[0]),
                                Qt.KeepAspectRatio,
                                Qt.SmoothTransformation,
                            )
                            label.setPixmap(new_pixmap)

                        scroll.wheelEvent = wheel_event

                    scroll.setWidget(label)
                else:
                    error_label = QLabel("Failed to load image")
                    scroll.setWidget(error_label)

                layout.addWidget(scroll)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        future.set_result(result == QDialog.Accepted)

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                confirmed = await future

            except ImportError:
                confirmed = True

            self.set_output_value("confirmed", confirmed)
            self.set_output_value("canceled", not confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("confirmed", False)
            self.set_output_value("canceled", True)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Data Table",
        label="Title",
        tooltip="Dialog title",
    ),
    PropertyDef(
        "data",
        PropertyType.JSON,
        default="[]",
        label="Data (JSON)",
        tooltip="Table data as JSON array of arrays or objects",
        essential=True,
    ),
    PropertyDef(
        "columns",
        PropertyType.STRING,
        default="",
        label="Columns",
        tooltip="Column headers (comma-separated), auto-detected if empty",
    ),
    PropertyDef(
        "selectable",
        PropertyType.BOOLEAN,
        default=False,
        label="Selectable",
        tooltip="Allow row selection",
    ),
)
@executable_node
class TableDialogNode(BaseNode):
    """
    Display tabular data in a dialog.

    Config (via @node_schema):
        title: Dialog title (default: 'Data Table')
        data: Table data as JSON (essential)
        columns: Column headers, comma-separated (default: auto-detect)
        selectable: Allow row selection (default: False)

    Inputs:
        data: Optional - overrides config if connected

    Outputs:
        selected_row: Selected row data (if selectable)
        selected_index: Selected row index (if selectable)
        confirmed: True if OK was clicked
    """

    # @category: system
    # @requires: none
    # @ports: data -> selected_row, selected_index, confirmed

    def __init__(self, node_id: str, name: str = "Table Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TableDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("data", DataType.ANY, required=False)
        self.add_output_port("selected_row", DataType.ANY)
        self.add_output_port("selected_index", DataType.INTEGER)
        self.add_output_port("confirmed", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Data Table")
            data_input = self.get_input_value("data")
            if data_input is None:
                data_input = self.get_parameter("data", "[]")

            columns_str = self.get_parameter("columns", "")
            selectable = self.get_parameter("selectable", False)

            title = context.resolve_value(title)

            # Parse data
            if isinstance(data_input, str):
                data_input = context.resolve_value(data_input)
                try:
                    data = json.loads(data_input)
                except json.JSONDecodeError:
                    data = []
            elif isinstance(data_input, list):
                data = data_input
            else:
                data = []

            if not data:
                self.set_output_value("selected_row", None)
                self.set_output_value("selected_index", -1)
                self.set_output_value("confirmed", False)
                self.status = NodeStatus.SUCCESS
                return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

            # Determine columns
            if columns_str:
                columns = [c.strip() for c in columns_str.split(",")]
            elif isinstance(data[0], dict):
                columns = list(data[0].keys())
            else:
                columns = [f"Column {i+1}" for i in range(len(data[0]))]

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QTableWidget,
                    QTableWidgetItem,
                    QDialogButtonBox,
                    QApplication,
                    QAbstractItemView,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(600, 400)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                layout = QVBoxLayout(dialog)

                table = QTableWidget()
                table.setColumnCount(len(columns))
                table.setHorizontalHeaderLabels(columns)
                table.setRowCount(len(data))

                if selectable:
                    table.setSelectionBehavior(QAbstractItemView.SelectRows)
                    table.setSelectionMode(QAbstractItemView.SingleSelection)
                else:
                    table.setSelectionMode(QAbstractItemView.NoSelection)

                for row_idx, row in enumerate(data):
                    if isinstance(row, dict):
                        for col_idx, col_name in enumerate(columns):
                            value = row.get(col_name, "")
                            table.setItem(
                                row_idx, col_idx, QTableWidgetItem(str(value))
                            )
                    elif isinstance(row, (list, tuple)):
                        for col_idx, value in enumerate(row):
                            if col_idx < len(columns):
                                table.setItem(
                                    row_idx, col_idx, QTableWidgetItem(str(value))
                                )

                table.resizeColumnsToContents()
                layout.addWidget(table)

                buttons = QDialogButtonBox(
                    QDialogButtonBox.Ok | QDialogButtonBox.Cancel
                )
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        if result == QDialog.Accepted:
                            selected_row_data = None
                            selected_idx = -1
                            if selectable:
                                selected_items = table.selectedItems()
                                if selected_items:
                                    selected_idx = selected_items[0].row()
                                    selected_row_data = (
                                        data[selected_idx]
                                        if selected_idx < len(data)
                                        else None
                                    )
                            future.set_result((selected_row_data, selected_idx, True))
                        else:
                            future.set_result((None, -1, False))

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                selected_row, selected_index, confirmed = await future

            except ImportError:
                selected_row = None
                selected_index = -1
                confirmed = True

            self.set_output_value("selected_row", selected_row)
            self.set_output_value("selected_index", selected_index)
            self.set_output_value("confirmed", confirmed)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"selected_index": selected_index, "confirmed": confirmed},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("selected_row", None)
            self.set_output_value("selected_index", -1)
            self.set_output_value("confirmed", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "title",
        PropertyType.STRING,
        default="Wizard",
        label="Title",
        tooltip="Wizard title",
    ),
    PropertyDef(
        "steps",
        PropertyType.JSON,
        default="[]",
        label="Steps (JSON)",
        tooltip='JSON array: [{"title": "Step 1", "fields": [...]}]',
        essential=True,
    ),
    PropertyDef(
        "allow_back",
        PropertyType.BOOLEAN,
        default=True,
        label="Allow Back",
        tooltip="Allow navigating to previous steps",
    ),
)
@executable_node
class WizardDialogNode(BaseNode):
    """
    Display a multi-step wizard dialog.

    Config (via @node_schema):
        title: Wizard title (default: 'Wizard')
        steps: JSON array of steps (essential)
            Each step: {"title": "Step N", "description": "...", "fields": [...]}
        allow_back: Allow going back (default: True)

    Outputs:
        data: Dictionary of all field values
        completed: True if wizard completed
        canceled: True if canceled
        last_step: Index of last completed step
    """

    # @category: system
    # @requires: none
    # @ports: steps -> data, completed, canceled, last_step

    def __init__(self, node_id: str, name: str = "Wizard Dialog", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WizardDialogNode"

    def _define_ports(self) -> None:
        self.add_input_port("steps", DataType.ANY, required=False)
        self.add_output_port("data", DataType.DICT)
        self.add_output_port("completed", DataType.BOOLEAN)
        self.add_output_port("canceled", DataType.BOOLEAN)
        self.add_output_port("last_step", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import json

            title = self.get_parameter("title", "Wizard")
            steps_input = self.get_input_value("steps")
            if steps_input is None:
                steps_input = self.get_parameter("steps", "[]")
            allow_back = self.get_parameter("allow_back", True)

            title = context.resolve_value(title)

            if isinstance(steps_input, str):
                steps_input = context.resolve_value(steps_input)
                try:
                    steps = json.loads(steps_input)
                except json.JSONDecodeError:
                    steps = []
            elif isinstance(steps_input, list):
                steps = steps_input
            else:
                steps = []

            if not steps:
                self.set_output_value("data", {})
                self.set_output_value("completed", False)
                self.set_output_value("canceled", True)
                self.set_output_value("last_step", -1)
                self.status = NodeStatus.SUCCESS
                return {"success": True, "data": {}, "next_nodes": ["exec_out"]}

            try:
                from PySide6.QtWidgets import (
                    QDialog,
                    QVBoxLayout,
                    QHBoxLayout,
                    QLabel,
                    QStackedWidget,
                    QPushButton,
                    QFormLayout,
                    QLineEdit,
                    QSpinBox,
                    QCheckBox,
                    QComboBox,
                    QApplication,
                    QWidget,
                )
                from PySide6.QtCore import Qt

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                dialog = QDialog()
                dialog.setWindowTitle(title)
                dialog.setMinimumSize(450, 350)
                dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowStaysOnTopHint)

                main_layout = QVBoxLayout(dialog)

                # Step indicator
                step_label = QLabel(f"Step 1 of {len(steps)}")
                step_label.setStyleSheet("font-weight: bold; font-size: 14px;")
                main_layout.addWidget(step_label)

                # Stacked widget for steps
                stack = QStackedWidget()
                all_widgets = {}

                for step_idx, step in enumerate(steps):
                    step_widget = QWidget()
                    step_layout = QVBoxLayout(step_widget)

                    step_title = step.get("title", f"Step {step_idx + 1}")
                    title_lbl = QLabel(step_title)
                    title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
                    step_layout.addWidget(title_lbl)

                    description = step.get("description", "")
                    if description:
                        desc_lbl = QLabel(description)
                        desc_lbl.setWordWrap(True)
                        step_layout.addWidget(desc_lbl)

                    form = QFormLayout()
                    fields = step.get("fields", [])

                    for field in fields:
                        field_name = field.get("name", "")
                        field_type = field.get("type", "text")
                        field_label = field.get("label", field_name)
                        field_default = field.get("default", "")
                        field_options = field.get("options", [])

                        full_name = f"step{step_idx}_{field_name}"

                        if field_type == "text":
                            widget = _create_styled_line_edit(text=str(field_default))
                            all_widgets[full_name] = ("text", widget)
                        elif field_type == "number":
                            widget = QSpinBox()
                            widget.setRange(-999999, 999999)
                            widget.setValue(int(field_default or 0))
                            all_widgets[full_name] = ("number", widget)
                        elif field_type == "checkbox":
                            widget = QCheckBox()
                            widget.setChecked(bool(field_default))
                            all_widgets[full_name] = ("checkbox", widget)
                        elif field_type == "select":
                            widget = QComboBox()
                            widget.addItems([str(opt) for opt in field_options])
                            all_widgets[full_name] = ("select", widget)
                        else:
                            widget = _create_styled_line_edit(text=str(field_default))
                            all_widgets[full_name] = ("text", widget)

                        form.addRow(field_label, widget)

                    step_layout.addLayout(form)
                    step_layout.addStretch()
                    stack.addWidget(step_widget)

                main_layout.addWidget(stack)

                # Navigation buttons
                nav_layout = QHBoxLayout()
                back_btn = QPushButton("Back")
                back_btn.setEnabled(False)
                next_btn = QPushButton("Next")
                cancel_btn = QPushButton("Cancel")

                nav_layout.addWidget(back_btn)
                nav_layout.addStretch()
                nav_layout.addWidget(cancel_btn)
                nav_layout.addWidget(next_btn)
                main_layout.addLayout(nav_layout)

                current_step = [0]
                result_data = [{}]
                completed_flag = [False]

                def update_buttons():
                    back_btn.setEnabled(allow_back and current_step[0] > 0)
                    if current_step[0] == len(steps) - 1:
                        next_btn.setText("Finish")
                    else:
                        next_btn.setText("Next")
                    step_label.setText(f"Step {current_step[0] + 1} of {len(steps)}")

                def go_back():
                    if current_step[0] > 0:
                        current_step[0] -= 1
                        stack.setCurrentIndex(current_step[0])
                        update_buttons()

                def go_next():
                    if current_step[0] < len(steps) - 1:
                        current_step[0] += 1
                        stack.setCurrentIndex(current_step[0])
                        update_buttons()
                    else:
                        # Collect all data
                        for name, (ftype, widget) in all_widgets.items():
                            if ftype == "text":
                                result_data[0][name] = widget.text()
                            elif ftype == "number":
                                result_data[0][name] = widget.value()
                            elif ftype == "checkbox":
                                result_data[0][name] = widget.isChecked()
                            elif ftype == "select":
                                result_data[0][name] = widget.currentText()
                        completed_flag[0] = True
                        dialog.accept()

                back_btn.clicked.connect(go_back)
                next_btn.clicked.connect(go_next)
                cancel_btn.clicked.connect(dialog.reject)

                update_buttons()

                future = asyncio.get_event_loop().create_future()

                def on_finished(result):
                    if not future.done():
                        future.set_result(
                            (result_data[0], completed_flag[0], current_step[0])
                        )

                dialog.finished.connect(on_finished)
                dialog.show()
                dialog.raise_()
                dialog.activateWindow()

                data, completed, last_step = await future

            except ImportError:
                data = {}
                completed = False
                last_step = -1

            self.set_output_value("data", data)
            self.set_output_value("completed", completed)
            self.set_output_value("canceled", not completed)
            self.set_output_value("last_step", last_step)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"data": data, "completed": completed, "last_step": last_step},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("data", {})
            self.set_output_value("completed", False)
            self.set_output_value("canceled", True)
            self.set_output_value("last_step", -1)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "message",
        PropertyType.STRING,
        default="Loading...",
        label="Message",
        tooltip="Message to display",
        essential=True,
    ),
    PropertyDef(
        "image_path",
        PropertyType.FILE_PATH,
        default="",
        label="Image Path",
        tooltip="Optional splash image",
    ),
    PropertyDef(
        "duration",
        PropertyType.INTEGER,
        default=3000,
        min_value=500,
        max_value=30000,
        label="Duration (ms)",
        tooltip="Display duration in milliseconds",
    ),
    PropertyDef(
        "progress",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Progress",
        tooltip="Show progress bar",
    ),
)
@executable_node
class SplashScreenNode(BaseNode):
    """
    Display a splash screen with optional progress.

    Config (via @node_schema):
        message: Message to display (essential)
        image_path: Optional splash image (default: '')
        duration: Display duration ms (default: 3000)
        progress: Show progress bar (default: True)

    Inputs:
        message: Optional - overrides config if connected

    Outputs:
        success: True if splash was shown
    """

    # @category: system
    # @requires: none
    # @ports: message -> success

    def __init__(self, node_id: str, name: str = "Splash Screen", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "SplashScreenNode"

    def _define_ports(self) -> None:
        self.add_input_port("message", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import os

            message = self.get_input_value("message")
            if message is None:
                message = self.get_parameter("message", "Loading...")
            # Resolve variables first, THEN convert to string (resolve preserves types for {{var}} patterns)
            message = str(context.resolve_value(message) or "Loading...")

            image_path = self.get_parameter("image_path", "")
            duration = int(self.get_parameter("duration", 3000) or 3000)
            show_progress = self.get_parameter("progress", True)

            if image_path:
                image_path = context.resolve_value(image_path)

            try:
                from PySide6.QtWidgets import (
                    QSplashScreen,
                    QApplication,
                    QWidget,
                    QVBoxLayout,
                    QLabel,
                    QProgressBar,
                )
                from PySide6.QtCore import Qt, QTimer
                from PySide6.QtGui import QPixmap, QColor, QPainter

                app = QApplication.instance()
                if app is None:
                    raise ImportError("No QApplication")

                # Create splash pixmap
                if image_path and os.path.exists(image_path):
                    pixmap = QPixmap(image_path)
                else:
                    # Create default splash
                    pixmap = QPixmap(400, 200)
                    pixmap.fill(QColor("#2196F3"))
                    painter = QPainter(pixmap)
                    painter.setPen(QColor("white"))
                    painter.drawText(pixmap.rect(), Qt.AlignCenter, message)
                    painter.end()

                splash = QSplashScreen(pixmap)
                splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)

                if show_progress:
                    # Overlay progress bar
                    splash.showMessage(
                        message, Qt.AlignBottom | Qt.AlignHCenter, QColor("white")
                    )

                splash.show()

                # Animate progress if enabled
                if show_progress:
                    progress_steps = 20
                    step_duration = duration // progress_steps

                    for i in range(progress_steps):
                        await asyncio.sleep(step_duration / 1000)
                        pct = int((i + 1) / progress_steps * 100)
                        splash.showMessage(
                            f"{message} ({pct}%)",
                            Qt.AlignBottom | Qt.AlignHCenter,
                            QColor("white"),
                        )
                        app.processEvents()
                else:
                    await asyncio.sleep(duration / 1000)

                splash.close()
                success = True

            except ImportError:
                await asyncio.sleep(duration / 1000)
                success = True

            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"shown": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}


@node_schema(
    PropertyDef(
        "file_path",
        PropertyType.FILE_PATH,
        default="",
        label="Audio File Path",
        tooltip="Path to audio file (WAV, MP3)",
    ),
    PropertyDef(
        "use_beep",
        PropertyType.BOOLEAN,
        default=False,
        label="Use System Beep",
        tooltip="Use system beep instead of audio file",
    ),
    PropertyDef(
        "frequency",
        PropertyType.INTEGER,
        default=440,
        min_value=37,
        max_value=32767,
        label="Beep Frequency",
        tooltip="Beep frequency in Hz (if using beep)",
    ),
    PropertyDef(
        "beep_duration",
        PropertyType.INTEGER,
        default=500,
        min_value=50,
        max_value=5000,
        label="Beep Duration",
        tooltip="Beep duration in ms (if using beep)",
    ),
    PropertyDef(
        "loop",
        PropertyType.BOOLEAN,
        default=False,
        label="Loop",
        tooltip="Loop audio playback",
    ),
)
@executable_node
class AudioAlertNode(BaseNode):
    """
    Play an audio file or system beep.

    Config (via @node_schema):
        file_path: Path to audio file (default: '')
        use_beep: Use system beep instead (default: False)
        frequency: Beep frequency Hz (default: 440)
        beep_duration: Beep duration ms (default: 500)
        loop: Loop playback (default: False)

    Outputs:
        success: True if audio played
    """

    # @category: system
    # @requires: none
    # @ports: file_path -> success

    def __init__(self, node_id: str, name: str = "Audio Alert", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "AudioAlertNode"

    def _define_ports(self) -> None:
        self.add_input_port("file_path", DataType.STRING, required=False)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> ExecutionResult:
        self.status = NodeStatus.RUNNING

        try:
            import os

            file_path = self.get_input_value("file_path")
            if file_path is None:
                file_path = self.get_parameter("file_path", "")
            if file_path:
                file_path = context.resolve_value(str(file_path))

            use_beep = self.get_parameter("use_beep", False)
            frequency = int(self.get_parameter("frequency", 440) or 440)
            beep_duration = int(self.get_parameter("beep_duration", 500) or 500)
            loop = self.get_parameter("loop", False)

            success = False

            if use_beep or not file_path:
                # Use system beep
                try:
                    import winsound

                    if loop:
                        # Play 3 times for "loop" effect
                        for _ in range(3):
                            winsound.Beep(frequency, beep_duration)
                    else:
                        winsound.Beep(frequency, beep_duration)
                    success = True
                except Exception:
                    # Fallback to MessageBeep
                    try:
                        import winsound

                        winsound.MessageBeep()
                        success = True
                    except Exception:
                        pass
            else:
                # Play audio file
                if os.path.exists(file_path):
                    try:
                        import winsound

                        flags = winsound.SND_FILENAME
                        if not loop:
                            flags |= winsound.SND_ASYNC
                        winsound.PlaySound(file_path, flags)
                        success = True
                    except Exception:
                        # Try playsound library
                        try:
                            from playsound import playsound

                            playsound(file_path, block=not loop)
                            success = True
                        except Exception:
                            pass

            self.set_output_value("success", success)
            self.status = NodeStatus.SUCCESS

            return {
                "success": True,
                "data": {"played": success},
                "next_nodes": ["exec_out"],
            }

        except Exception as e:
            self.set_output_value("success", False)
            self.status = NodeStatus.ERROR
            return {"success": False, "error": str(e), "next_nodes": []}
