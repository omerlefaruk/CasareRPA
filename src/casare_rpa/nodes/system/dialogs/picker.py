"""
Picker dialog nodes.

Nodes for selecting files, folders, colors, dates, and items from lists.
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

from .widgets import _create_styled_line_edit


@properties(
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
@node(category="system")
class FilePickerDialogNode(BaseNode):
    """
    Display a file picker dialog.

    Config (via @properties):
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


@properties(
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
@node(category="system")
class FolderPickerDialogNode(BaseNode):
    """
    Display a folder picker dialog.

    Config (via @properties):
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


@properties(
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
@node(category="system")
class ColorPickerDialogNode(BaseNode):
    """
    Display a color picker dialog.

    Config (via @properties):
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


@properties(
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
@node(category="system")
class DateTimePickerDialogNode(BaseNode):
    """
    Display a date/time picker dialog.

    Config (via @properties):
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


@properties(
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
@node(category="system")
class ListPickerDialogNode(BaseNode):
    """
    Display a list picker dialog for single/multi-select.

    Config (via @properties):
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
                    QListWidget,
                    QListWidgetItem,
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
