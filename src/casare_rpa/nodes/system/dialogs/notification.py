"""
Notification and alert nodes.

Nodes for displaying tooltips, notifications, snackbars, and playing sounds.
"""

import sys
import asyncio
from typing import Tuple

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@properties(
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
@node(category="system")
class TooltipNode(BaseNode):
    """
    Display a tooltip at a specified position.

    Config (via @properties):
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

    def _format_message_with_variables(self, original: str, context: "ExecutionContext") -> str:
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
        from PySide6.QtGui import QCursor, QFont

        app = QApplication.instance()
        if app is None:
            return

        icon_char = {
            "info": "\u2139",
            "warning": "\u26a0",
            "error": "\u2717",
            "success": "\u2713",
        }

        container = QWidget()
        container.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

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


@properties(
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
@node(category="system")
class SystemNotificationNode(BaseNode):
    """
    Display a Windows system notification (toast).

    Config (via @properties):
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

    def __init__(self, node_id: str, name: str = "System Notification", **kwargs) -> None:
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


@properties(
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
@node(category="system")
class SnackbarNode(BaseNode):
    """
    Display a Material-style snackbar notification.

    Config (via @properties):
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
        )
        from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
        from PySide6.QtGui import QFont

        app = QApplication.instance()
        if app is None:
            return False

        snackbar = QWidget()
        snackbar.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
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


@properties(
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
@node(category="system")
class BalloonTipNode(BaseNode):
    """
    Display a balloon tooltip at a screen position.

    Config (via @properties):
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
        from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
        from PySide6.QtGui import QCursor, QFont, QPainter, QPainterPath, QColor, QPen

        app = QApplication.instance()
        if app is None:
            return

        class BalloonWidget(QWidget):
            def __init__(self):
                super().__init__()
                self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
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
                icon_label.setStyleSheet(f"color: {icon_colors.get(icon_type, '#000')};")
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


@properties(
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
@node(category="system")
class AudioAlertNode(BaseNode):
    """
    Play an audio file or system beep.

    Config (via @properties):
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
