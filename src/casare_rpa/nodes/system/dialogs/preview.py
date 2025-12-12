"""
Preview and data display nodes.

Nodes for previewing images and displaying tabular data.
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
class ImagePreviewDialogNode(BaseNode):
    """
    Display an image preview dialog.

    Config (via @properties):
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


@node(category="system")
@properties(
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
class TableDialogNode(BaseNode):
    """
    Display tabular data in a dialog.

    Config (via @properties):
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
