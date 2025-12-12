"""
Progress and splash screen nodes.

Nodes for displaying progress bars and splash screens.
"""

import asyncio
from typing import Optional, Tuple

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    PortType,
    DataType,
    ExecutionResult,
)
from casare_rpa.infrastructure.execution import ExecutionContext


@node(category="system")
@properties(
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
class ProgressDialogNode(BaseNode):
    """
    Display a progress dialog.

    Config (via @properties):
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


@node(category="system")
@properties(
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
class SplashScreenNode(BaseNode):
    """
    Display a splash screen with optional progress.

    Config (via @properties):
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
