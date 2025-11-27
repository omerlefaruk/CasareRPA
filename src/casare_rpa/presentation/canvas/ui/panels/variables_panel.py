"""
Variables Panel UI Component.

Provides workflow variable management with inline editing similar to UiPath.
Extracted from canvas/panels/variables_tab.py for reusability.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QStyledItemDelegate,
    QLabel,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from loguru import logger


# Variable type definitions
VARIABLE_TYPES = [
    "String",
    "Integer",
    "Float",
    "Boolean",
    "List",
    "Dict",
    "DataTable",
]

# Default values for each type
TYPE_DEFAULTS = {
    "String": "",
    "Integer": 0,
    "Float": 0.0,
    "Boolean": False,
    "List": [],
    "Dict": {},
    "DataTable": None,
}


class TypeComboDelegate(QStyledItemDelegate):
    """
    Delegate for type selection dropdown in table.

    Provides a dropdown for selecting variable types when editing.
    """

    def createEditor(self, parent, option, index):
        """
        Create combo box editor.

        Args:
            parent: Parent widget
            option: Style option
            index: Model index

        Returns:
            QComboBox editor
        """
        combo = QComboBox(parent)
        combo.addItems(VARIABLE_TYPES)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #3c3f41;
                color: #d4d4d4;
                border: none;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
        """)
        return combo

    def setEditorData(self, editor, index):
        """
        Set editor data from model.

        Args:
            editor: Editor widget
            index: Model index
        """
        value = index.data(Qt.ItemDataRole.EditRole)
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)

    def setModelData(self, editor, model, index):
        """
        Set model data from editor.

        Args:
            editor: Editor widget
            model: Data model
            index: Model index
        """
        model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)


class VariablesPanel(QDockWidget):
    """
    Dockable variables panel for workflow variable management.

    Features:
    - Inline variable creation
    - Type selection
    - Default value editing
    - Scope indicators
    - Design/Runtime modes

    Signals:
        variable_added: Emitted when variable is added (str: name, str: type, Any: default_value)
        variable_changed: Emitted when variable is modified (str: name, str: type, Any: default_value)
        variable_removed: Emitted when variable is removed (str: name)
        variables_changed: Emitted when variables dict changes (dict: all_variables)
    """

    variable_added = Signal(str, str, object)
    variable_changed = Signal(str, str, object)
    variable_removed = Signal(str)
    variables_changed = Signal(dict)

    # Table columns
    COL_NAME = 0
    COL_TYPE = 1
    COL_DEFAULT = 2
    COL_SCOPE = 3

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the variables panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Variables", parent)
        self.setObjectName("VariablesDock")

        self._variables: Dict[str, Dict[str, Any]] = {}
        self._is_runtime_mode = False

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()

        logger.debug("VariablesPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
            | QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.setMinimumWidth(250)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        # Mode label
        self._mode_label = QLabel("Mode: Design")
        self._mode_label.setStyleSheet("color: #a0a0a0;")

        # Add variable button
        add_btn = QPushButton("Add Variable")
        add_btn.setFixedWidth(100)
        add_btn.clicked.connect(self._on_add_variable)

        # Remove variable button
        remove_btn = QPushButton("Remove")
        remove_btn.setFixedWidth(70)
        remove_btn.clicked.connect(self._on_remove_variable)

        # Clear all button
        clear_btn = QPushButton("Clear All")
        clear_btn.setFixedWidth(70)
        clear_btn.clicked.connect(self._on_clear_all)

        toolbar.addWidget(self._mode_label)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(remove_btn)
        toolbar.addWidget(clear_btn)

        main_layout.addLayout(toolbar)

        # Variables table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Name", "Type", "Default Value", "Scope"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self._table.itemChanged.connect(self._on_item_changed)

        # Set type column delegate
        self._table.setItemDelegateForColumn(self.COL_TYPE, TypeComboDelegate())

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(self.COL_DEFAULT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(self.COL_SCOPE, QHeaderView.ResizeMode.ResizeToContents)

        main_layout.addWidget(self._table)

        self.setWidget(container)

    def _apply_styles(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #252525;
                color: #e0e0e0;
            }
            QDockWidget::title {
                background: #2d2d2d;
                padding: 6px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #323232;
                border: 1px solid #4a4a4a;
                gridline-color: #3d3d3d;
                color: #e0e0e0;
            }
            QTableWidget::item:selected {
                background-color: #5a8a9a;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: none;
                border-right: 1px solid #4a4a4a;
                border-bottom: 1px solid #4a4a4a;
                padding: 4px;
            }
        """)

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Set runtime mode.

        In runtime mode, variable values are displayed but not editable.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        self._is_runtime_mode = enabled
        self._mode_label.setText(f"Mode: {'Runtime' if enabled else 'Design'}")

        # Make table read-only in runtime mode
        if enabled:
            self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        else:
            self._table.setEditTriggers(
                QAbstractItemView.EditTrigger.DoubleClicked
                | QAbstractItemView.EditTrigger.EditKeyPressed
            )

        logger.debug(f"Variables panel mode: {'Runtime' if enabled else 'Design'}")

    def add_variable(
        self,
        name: str,
        var_type: str = "String",
        default_value: Any = "",
        scope: str = "Workflow",
    ) -> None:
        """
        Add a variable to the panel.

        Args:
            name: Variable name
            var_type: Variable type
            default_value: Default value
            scope: Variable scope
        """
        # Check if variable already exists
        if name in self._variables:
            logger.warning(f"Variable '{name}' already exists")
            return

        # Store variable
        self._variables[name] = {
            "type": var_type,
            "default": default_value,
            "scope": scope,
        }

        # Add to table
        row = self._table.rowCount()
        self._table.insertRow(row)

        name_item = QTableWidgetItem(name)
        self._table.setItem(row, self.COL_NAME, name_item)

        type_item = QTableWidgetItem(var_type)
        self._table.setItem(row, self.COL_TYPE, type_item)

        default_item = QTableWidgetItem(str(default_value))
        self._table.setItem(row, self.COL_DEFAULT, default_item)

        scope_item = QTableWidgetItem(scope)
        scope_item.setFlags(scope_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._table.setItem(row, self.COL_SCOPE, scope_item)

        self.variable_added.emit(name, var_type, default_value)
        self.variables_changed.emit(self._variables)

        logger.debug(f"Variable added: {name} ({var_type})")

    def remove_variable(self, name: str) -> None:
        """
        Remove a variable from the panel.

        Args:
            name: Variable name
        """
        if name not in self._variables:
            return

        # Remove from dict
        del self._variables[name]

        # Remove from table
        for row in range(self._table.rowCount()):
            item = self._table.item(row, self.COL_NAME)
            if item and item.text() == name:
                self._table.removeRow(row)
                break

        self.variable_removed.emit(name)
        self.variables_changed.emit(self._variables)

        logger.debug(f"Variable removed: {name}")

    def update_variable_value(self, name: str, value: Any) -> None:
        """
        Update variable value (runtime mode).

        Args:
            name: Variable name
            value: New value
        """
        if name not in self._variables:
            return

        self._variables[name]["current_value"] = value

        # Update table
        for row in range(self._table.rowCount()):
            item = self._table.item(row, self.COL_NAME)
            if item and item.text() == name:
                default_item = self._table.item(row, self.COL_DEFAULT)
                if default_item:
                    default_item.setText(str(value))
                break

        logger.debug(f"Variable updated: {name} = {value}")

    def get_variables(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all variables.

        Returns:
            Dictionary of all variables
        """
        return self._variables.copy()

    def clear_variables(self) -> None:
        """Clear all variables."""
        self._variables.clear()
        self._table.setRowCount(0)
        self.variables_changed.emit(self._variables)
        logger.debug("All variables cleared")

    def _on_add_variable(self) -> None:
        """Handle add variable button click."""
        # Generate unique name
        i = 1
        while f"variable{i}" in self._variables:
            i += 1

        name = f"variable{i}"
        self.add_variable(name, "String", "", "Workflow")

    def _on_remove_variable(self) -> None:
        """Handle remove variable button click."""
        current_row = self._table.currentRow()
        if current_row >= 0:
            name_item = self._table.item(current_row, self.COL_NAME)
            if name_item:
                self.remove_variable(name_item.text())

    def _on_clear_all(self) -> None:
        """Handle clear all button click."""
        self.clear_variables()

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        """
        Handle table item change.

        Args:
            item: Changed table item
        """
        if self._is_runtime_mode:
            return

        row = item.row()
        col = item.column()

        name_item = self._table.item(row, self.COL_NAME)
        if not name_item:
            return

        name = name_item.text()
        if name not in self._variables:
            return

        # Update variable data
        if col == self.COL_TYPE:
            var_type = item.text()
            self._variables[name]["type"] = var_type
            # Update default value to match type
            default_value = TYPE_DEFAULTS.get(var_type, "")
            self._variables[name]["default"] = default_value
            default_item = self._table.item(row, self.COL_DEFAULT)
            if default_item:
                default_item.setText(str(default_value))

        elif col == self.COL_DEFAULT:
            self._variables[name]["default"] = item.text()

        self.variable_changed.emit(
            name,
            self._variables[name]["type"],
            self._variables[name]["default"],
        )
        self.variables_changed.emit(self._variables)
