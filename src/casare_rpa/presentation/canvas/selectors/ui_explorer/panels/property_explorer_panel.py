"""
Property Explorer Panel for UI Explorer.

Full property table showing ALL element properties (not just selector attributes).
Supports filtering, sorting, copying values, and computed property display.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.element_model import (
    ElementSource,
    UIExplorerElement)


class PropertyExplorerPanel(QFrame):
    """
    Property Explorer Panel.

    Full property table showing ALL element properties.
    Features:
    - QTableWidget with 2 columns (Property, Value)
    - Sortable by property name
    - Filter input at top
    - Copy value on double-click
    - Computed properties in italic
    - Empty values shown as "(empty)" in gray

    Signals:
        property_copied: Emitted when a property value is copied (property_name, value)
    """

    property_copied = Signal(str, str)  # property_name, value

    # Browser element properties to extract
    BROWSER_CORE_PROPS = ["tag", "id", "class", "name", "type", "value"]
    BROWSER_LINK_PROPS = ["href", "src", "alt", "title"]
    BROWSER_TEXT_PROPS = ["innerText", "textContent", "visibleInnerText"]
    BROWSER_COMPUTED_PROPS = ["css-selector", "xpath", "boundingRect"]
    BROWSER_STATE_PROPS = ["checked", "disabled", "readonly", "hidden"]

    # Desktop element properties to extract
    DESKTOP_IDENTITY_PROPS = ["Name", "AutomationId", "ControlType", "ClassName"]
    DESKTOP_PROCESS_PROPS = ["ProcessId", "ProcessName", "WindowHandle"]
    DESKTOP_STATE_PROPS = [
        "IsEnabled",
        "IsOffscreen",
        "IsKeyboardFocusable",
        "HasKeyboardFocus",
    ]
    DESKTOP_GEOMETRY_PROPS = ["BoundingRectangle"]
    DESKTOP_PATTERN_PROPS = ["SupportedPatterns"]
    DESKTOP_VALUE_PROPS = ["CurrentValue"]

    # Properties that are computed (not direct attributes)
    COMPUTED_PROPERTIES = {
        "css-selector",
        "xpath",
        "boundingRect",
        "SupportedPatterns",
        "BoundingRectangle",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the property explorer panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._current_element: UIExplorerElement | None = None
        self._all_properties: list[dict[str, Any]] = []  # Stores all properties for filtering
        self._context_row: int = -1  # Context menu target row

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 4)
        header.setSpacing(8)

        # Title
        title_label = QLabel("PROPERTIES")
        title_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                font-weight: bold;
                letter-spacing: 1px;
            }
        """)
        header.addWidget(title_label)
        header.addStretch()

        layout.addLayout(header)

        # Filter input
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(8, 0, 8, 4)

        self._filter_input = QLineEdit()
        self._filter_input.setPlaceholderText("Filter properties...")
        self._filter_input.textChanged.connect(self._on_filter_changed)
        self._filter_input.setClearButtonEnabled(True)
        filter_layout.addWidget(self._filter_input)

        layout.addLayout(filter_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background: #3a3a3a; max-height: 1px;")
        layout.addWidget(separator)

        # Property table
        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Property", "Value"])
        self._table.setFrameShape(QFrame.Shape.NoFrame)
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Configure columns
        header_view = self._table.horizontalHeader()
        header_view.setStretchLastSection(True)
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft)

        # Connect signals
        self._table.doubleClicked.connect(self._on_double_click)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self._table, 1)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(8, 4, 8, 8)

        self._count_label = QLabel("0 properties")
        self._count_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 10px;
            }
        """)
        footer.addWidget(self._count_label)
        footer.addStretch()

        layout.addLayout(footer)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            PropertyExplorerPanel {
                background: #1e1e1e;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
            }
        """)

        self._filter_input.setStyleSheet("""
            QLineEdit {
                background: #2d2d2d;
                border: 1px solid #3a3a3a;
                border-radius: 3px;
                padding: 4px 8px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QLineEdit:focus {
                border-color: #60a5fa;
            }
            QLineEdit::placeholder {
                color: #666666;
            }
        """)

        self._table.setStyleSheet("""
            QTableWidget {
                background: transparent;
                border: none;
                outline: none;
                gridline-color: #2a2a2a;
            }
            QTableWidget::item {
                padding: 4px 8px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTableWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QTableWidget::item:hover {
                background: #2a2a2a;
            }
            QHeaderView::section {
                background: #2d2d2d;
                color: #888888;
                font-size: 10px;
                font-weight: bold;
                padding: 6px 8px;
                border: none;
                border-bottom: 1px solid #3a3a3a;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3a3a3a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4a4a4a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

    def load_from_element(self, element: UIExplorerElement) -> None:
        """
        Load properties from a UIExplorerElement.

        Args:
            element: UIExplorerElement to display properties for
        """
        self._current_element = element
        self._all_properties = []

        if element.source == ElementSource.BROWSER:
            self._load_browser_properties(element)
        else:
            self._load_desktop_properties(element)

        # Apply current filter
        self._apply_filter()
        self._update_count()

        logger.debug(
            f"PropertyExplorer: Loaded {len(self._all_properties)} properties "
            f"from {element.source.value} element"
        )

    def _load_browser_properties(self, element: UIExplorerElement) -> None:
        """Load properties for a browser element."""
        attrs = element.attributes
        raw_data = element.raw_data or {}

        # Core properties
        self._add_property("tag", element.tag_or_control)
        for prop in self.BROWSER_CORE_PROPS[1:]:  # Skip 'tag', already added
            value = attrs.get(prop, raw_data.get(prop, ""))
            self._add_property(prop, value)

        # Link properties
        for prop in self.BROWSER_LINK_PROPS:
            value = attrs.get(prop, raw_data.get(prop, ""))
            self._add_property(prop, value)

        # Text properties
        for prop in self.BROWSER_TEXT_PROPS:
            value = raw_data.get(prop, "")
            if not value:
                # Try alternative keys
                if prop == "innerText":
                    value = raw_data.get("text", "")
            self._add_property(prop, value)

        # Data attributes
        for key, value in attrs.items():
            if key.startswith("data-"):
                self._add_property(key, value)
        # Also check raw_data for data-* attributes
        for key, value in raw_data.items():
            if key.startswith("data-") and key not in attrs:
                self._add_property(key, value)

        # ARIA attributes
        for key, value in attrs.items():
            if key.startswith("aria-"):
                self._add_property(key, value)
        # Also check raw_data
        for key, value in raw_data.items():
            if key.startswith("aria-") and key not in attrs:
                self._add_property(key, value)

        # Computed properties
        if raw_data.get("css-selector"):
            self._add_property("css-selector", raw_data["css-selector"], computed=True)
        if raw_data.get("xpath"):
            self._add_property("xpath", raw_data["xpath"], computed=True)

        # Bounding rect
        rect = element.rect
        if rect:
            rect_str = f"{rect.get('x', 0)},{rect.get('y', 0)},{rect.get('width', 0)},{rect.get('height', 0)}"
            self._add_property("boundingRect", rect_str, computed=True)

        # State properties
        for prop in self.BROWSER_STATE_PROPS:
            value = raw_data.get(prop, attrs.get(prop, ""))
            if value not in ("", None):
                self._add_property(prop, str(value))

        # Role
        if attrs.get("role") or raw_data.get("role"):
            self._add_property("role", attrs.get("role", raw_data.get("role", "")))

    def _load_desktop_properties(self, element: UIExplorerElement) -> None:
        """Load properties for a desktop element."""
        attrs = element.attributes
        raw_data = element.raw_data or {}

        # Identity properties
        self._add_property("ControlType", element.tag_or_control)
        self._add_property("Name", element.name)
        self._add_property("AutomationId", element.element_id)

        for prop in ["ClassName"]:
            value = attrs.get(prop, "")
            if not value and isinstance(raw_data, dict):
                value = raw_data.get(prop, "")
            self._add_property(prop, value)

        # Process properties
        for prop in self.DESKTOP_PROCESS_PROPS:
            value = ""
            if isinstance(raw_data, dict):
                value = raw_data.get(prop, "")
            if not value:
                value = attrs.get(prop, "")
            self._add_property(prop, str(value) if value else "")

        # State properties
        for prop in self.DESKTOP_STATE_PROPS:
            value = None
            if isinstance(raw_data, dict):
                value = raw_data.get(prop)
            if value is None:
                value = attrs.get(prop, "")
            self._add_property(prop, str(value) if value not in (None, "") else "")

        # Bounding rect
        rect = element.rect
        if rect:
            rect_str = f"x={rect.get('x', 0)}, y={rect.get('y', 0)}, w={rect.get('width', 0)}, h={rect.get('height', 0)}"
            self._add_property("BoundingRectangle", rect_str, computed=True)

        # Supported patterns
        patterns = []
        if isinstance(raw_data, dict):
            patterns = raw_data.get("SupportedPatterns", [])
        if patterns:
            self._add_property("SupportedPatterns", ", ".join(patterns), computed=True)

        # Current value (for edit controls)
        if isinstance(raw_data, dict) and raw_data.get("CurrentValue"):
            self._add_property("CurrentValue", raw_data["CurrentValue"])

        # LocalizedControlType
        localized = attrs.get("LocalizedControlType", "")
        if not localized and isinstance(raw_data, dict):
            localized = raw_data.get("LocalizedControlType", "")
        if localized:
            self._add_property("LocalizedControlType", localized)

    def _add_property(
        self,
        name: str,
        value: Any,
        computed: bool = False) -> None:
        """
        Add a property to the internal list.

        Args:
            name: Property name
            value: Property value
            computed: Whether this is a computed property
        """
        # Convert value to string
        if value is None:
            str_value = ""
        elif isinstance(value, bool):
            str_value = str(value).lower()
        else:
            str_value = str(value)

        # Check if computed from set
        is_computed = computed or name in self.COMPUTED_PROPERTIES

        self._all_properties.append(
            {
                "name": name,
                "value": str_value,
                "computed": is_computed,
            }
        )

    def _apply_filter(self) -> None:
        """Apply the current filter to the table."""
        filter_text = self._filter_input.text().lower().strip()

        # Disable sorting while updating
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)

        filtered_props = []
        for prop in self._all_properties:
            name = prop["name"]
            value = prop["value"]

            # Filter by name or value
            if filter_text:
                if filter_text not in name.lower() and filter_text not in value.lower():
                    continue

            filtered_props.append(prop)

        # Populate table
        self._table.setRowCount(len(filtered_props))

        for row, prop in enumerate(filtered_props):
            name = prop["name"]
            value = prop["value"]
            is_computed = prop["computed"]

            # Property name item
            name_item = QTableWidgetItem(name)
            name_item.setForeground(QColor("#e0e0e0"))

            # Apply italic for computed
            if is_computed:
                font = QFont()
                font.setItalic(True)
                name_item.setFont(font)
                name_item.setForeground(QColor("#888888"))

            self._table.setItem(row, 0, name_item)

            # Value item
            if value:
                value_item = QTableWidgetItem(value)
                value_item.setForeground(QColor("#e0e0e0"))
            else:
                value_item = QTableWidgetItem("(empty)")
                value_item.setForeground(QColor("#666666"))
                font = QFont()
                font.setPointSize(10)  # Explicit size to avoid Qt warning
                font.setItalic(True)
                value_item.setFont(font)

            # Apply italic for computed values
            if is_computed and value:
                font = value_item.font()
                # Ensure valid point size (Qt can return -1 for unset fonts)
                if font.pointSize() <= 0:
                    font.setPointSize(10)
                font.setItalic(True)
                value_item.setFont(font)
                value_item.setForeground(QColor("#888888"))

            self._table.setItem(row, 1, value_item)

        # Re-enable sorting
        self._table.setSortingEnabled(True)

        # Update count label
        if filter_text:
            self._count_label.setText(
                f"{len(filtered_props)} of {len(self._all_properties)} properties"
            )
        else:
            self._count_label.setText(f"{len(self._all_properties)} properties")

    def _update_count(self) -> None:
        """Update the count label."""
        self._count_label.setText(f"{len(self._all_properties)} properties")

    def _on_filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        self._apply_filter()

    def _on_double_click(self, index) -> None:
        """Handle double-click to copy value."""
        row = index.row()
        self._copy_value_at_row(row)

    def _copy_value_at_row(self, row: int) -> None:
        """Copy the value at the specified row."""
        if row < 0 or row >= self._table.rowCount():
            return

        name_item = self._table.item(row, 0)
        value_item = self._table.item(row, 1)

        if not name_item or not value_item:
            return

        name = name_item.text()
        value = value_item.text()

        # Don't copy "(empty)" placeholder
        if value == "(empty)":
            value = ""

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(value)

        # Emit signal
        self.property_copied.emit(name, value)

        logger.debug(f"PropertyExplorer: Copied '{name}' = '{value}'")

    def _show_context_menu(self, position) -> None:
        """Show context menu at position."""
        row = self._table.rowAt(position.y())
        if row < 0:
            return

        # Store context row for slot methods
        self._context_row = row

        menu = QMenu(self)

        # Copy value action
        copy_action = menu.addAction("Copy Value")
        copy_action.triggered.connect(self._on_copy_value_action)

        # Copy name action
        copy_name_action = menu.addAction("Copy Property Name")
        copy_name_action.triggered.connect(self._on_copy_name_action)

        menu.addSeparator()

        # Copy both action
        copy_both_action = menu.addAction("Copy Name = Value")
        copy_both_action.triggered.connect(self._on_copy_both_action)

        menu.exec(self._table.viewport().mapToGlobal(position))

    @Slot()
    def _on_copy_value_action(self) -> None:
        """Handle copy value context menu action."""
        self._copy_value_at_row(self._context_row)

    @Slot()
    def _on_copy_name_action(self) -> None:
        """Handle copy property name context menu action."""
        self._copy_name_at_row(self._context_row)

    @Slot()
    def _on_copy_both_action(self) -> None:
        """Handle copy name = value context menu action."""
        self._copy_both_at_row(self._context_row)

    def _copy_name_at_row(self, row: int) -> None:
        """Copy the property name at the specified row."""
        if row < 0 or row >= self._table.rowCount():
            return

        name_item = self._table.item(row, 0)
        if name_item:
            clipboard = QApplication.clipboard()
            clipboard.setText(name_item.text())
            logger.debug(f"PropertyExplorer: Copied property name '{name_item.text()}'")

    def _copy_both_at_row(self, row: int) -> None:
        """Copy name = value at the specified row."""
        if row < 0 or row >= self._table.rowCount():
            return

        name_item = self._table.item(row, 0)
        value_item = self._table.item(row, 1)

        if name_item and value_item:
            name = name_item.text()
            value = value_item.text()
            if value == "(empty)":
                value = ""
            text = f"{name} = {value}"

            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logger.debug(f"PropertyExplorer: Copied '{text}'")

    def clear(self) -> None:
        """Clear all properties."""
        self._current_element = None
        self._all_properties = []
        self._table.setRowCount(0)
        self._filter_input.clear()
        self._count_label.setText("0 properties")

    def filter_properties(self, query: str) -> None:
        """
        Filter properties by query string.

        Args:
            query: Filter query (matches against name and value)
        """
        self._filter_input.setText(query)
        # Filter will be applied via textChanged signal

    def copy_selected_value(self) -> None:
        """Copy the currently selected property value."""
        current_row = self._table.currentRow()
        if current_row >= 0:
            self._copy_value_at_row(current_row)

    def get_property_count(self) -> int:
        """Get the total number of properties."""
        return len(self._all_properties)

    def get_current_element(self) -> UIExplorerElement | None:
        """Get the current element being displayed."""
        return self._current_element

    def load_from_dict(self, element_data: dict[str, Any]) -> None:
        """
        Load properties from a raw element dictionary.

        This method accepts raw element data (from browser or desktop)
        and populates the property table with all available attributes.

        Args:
            element_data: Element data dict with source, tag, attributes, etc.
        """
        self._all_properties = []

        # Add all top-level properties (except children/complex objects)
        skip_keys = {"children", "raw_data", "parent"}
        for key, value in element_data.items():
            if key in skip_keys:
                continue
            if isinstance(value, dict | list):
                # Handle nested dicts/lists specially
                if key == "attributes":
                    continue  # Process attributes separately below
                elif key == "rect" and isinstance(value, dict):
                    # Format bounding rect
                    rect_str = f"x={value.get('x', 0)}, y={value.get('y', 0)}, w={value.get('width', 0)}, h={value.get('height', 0)}"
                    self._add_property("boundingRect", rect_str, computed=True)
                else:
                    # Convert complex values to string
                    self._add_property(key, str(value))
            else:
                self._add_property(key, value)

        # Add nested attributes
        attrs = element_data.get("attributes", {})
        for key, value in attrs.items():
            # Avoid duplicates
            if not any(p["name"] == key for p in self._all_properties):
                self._add_property(key, str(value) if value else "")

        # Apply current filter and update display
        self._apply_filter()
        self._update_count()

        logger.debug(f"PropertyExplorer: Loaded {len(self._all_properties)} properties from dict")
