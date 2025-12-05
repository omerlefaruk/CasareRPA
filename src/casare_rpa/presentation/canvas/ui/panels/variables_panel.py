"""
Variables Panel UI Component.

Provides workflow variable management with improved UX:
- Empty state guidance when no variables
- Inline variable editing
- Type selection with visual indicators
- Scope filtering
- Design/Runtime mode switching
- Context menu for copy/delete

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.
"""

from typing import Optional, Dict, Any

from PySide6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QAbstractItemView,
    QComboBox,
    QStyledItemDelegate,
    QLabel,
    QStackedWidget,
    QApplication,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QBrush

from loguru import logger

from casare_rpa.presentation.canvas.events import (
    LazySubscriptionGroup,
    EventType,
    Event,
)
from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.ui.panels.panel_ux_helpers import (
    EmptyStateWidget,
    ToolbarButton,
    StatusBadge,
    get_panel_table_stylesheet,
    get_panel_toolbar_stylesheet,
)


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

# Type colors (matching wire colors for consistency)
TYPE_COLORS = {
    "String": THEME.wire_string,
    "Integer": THEME.wire_number,
    "Float": THEME.wire_number,
    "Boolean": THEME.wire_bool,
    "List": THEME.wire_list,
    "Dict": THEME.wire_dict,
    "DataTable": THEME.wire_table,
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
        combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {THEME.input_bg};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                padding: 2px 4px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox:hover {{
                border-color: {THEME.border_light};
            }}
            QComboBox:focus {{
                border-color: {THEME.border_focus};
            }}
            QComboBox QAbstractItemView {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                selection-background-color: {THEME.bg_selected};
            }}
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
    - Empty state when no variables
    - Inline variable creation
    - Type selection with color indicators
    - Default value editing
    - Scope filtering
    - Design/Runtime modes
    - Context menu for actions

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
        self._current_scope_filter = "All"

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_lazy_subscriptions()

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
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("variablesToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 6, 8, 6)
        toolbar.setSpacing(12)

        # Variable count label
        self._count_label = QLabel("0 variables")
        self._count_label.setProperty("muted", True)

        # Scope filter dropdown
        filter_label = QLabel("Scope:")
        self._scope_filter = QComboBox()
        self._scope_filter.addItems(["All", "Global", "Project", "Workflow"])
        self._scope_filter.setFixedWidth(90)
        self._scope_filter.currentTextChanged.connect(self._on_scope_filter_changed)
        self._scope_filter.setToolTip("Filter variables by scope")

        # Mode badge
        self._mode_badge = StatusBadge("DESIGN", "info")

        # Add variable button (primary action)
        add_btn = ToolbarButton(
            text="Add Variable",
            tooltip="Add a new workflow variable",
            primary=True,
        )
        add_btn.clicked.connect(self._on_add_variable)

        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._scope_filter)
        toolbar.addWidget(self._mode_badge)
        toolbar.addWidget(add_btn)

        main_layout.addWidget(toolbar_widget)

        # Content stack for empty state vs table
        self._content_stack = QStackedWidget()

        # Empty state (index 0)
        self._empty_state = EmptyStateWidget(
            icon_text="",  # Variable/database icon
            title="No Variables",
            description=(
                "Variables store data that can be used across your workflow.\n\n"
                "Click 'Add Variable' to create:\n"
                "- Strings, numbers, and booleans\n"
                "- Lists and dictionaries\n"
                "- DataTables for structured data"
            ),
            action_text="Add Variable",
        )
        self._empty_state.action_clicked.connect(self._on_add_variable)
        self._content_stack.addWidget(self._empty_state)

        # Table container (index 1)
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(8, 4, 8, 8)
        table_layout.setSpacing(4)

        # Variables table
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(
            ["Name", "Type", "Default Value", "Scope"]
        )

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self._table.itemChanged.connect(self._on_item_changed)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)
        self._table.verticalHeader().setVisible(False)

        # Set type column delegate
        self._table.setItemDelegateForColumn(self.COL_TYPE, TypeComboDelegate())

        # Configure column sizing
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(self.COL_NAME, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            self.COL_TYPE, QHeaderView.ResizeMode.ResizeToContents
        )
        header.setSectionResizeMode(self.COL_DEFAULT, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(
            self.COL_SCOPE, QHeaderView.ResizeMode.ResizeToContents
        )

        table_layout.addWidget(self._table)

        # Action bar
        action_bar = QWidget()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, 4, 0, 0)
        action_layout.setSpacing(8)

        # Remove selected button
        remove_btn = ToolbarButton(
            text="Remove Selected",
            tooltip="Remove the selected variable (Delete)",
        )
        remove_btn.clicked.connect(self._on_remove_variable)

        # Clear all button (danger action)
        clear_btn = ToolbarButton(
            text="Clear All",
            tooltip="Remove all variables",
            danger=True,
        )
        clear_btn.clicked.connect(self._on_clear_all)

        action_layout.addStretch()
        action_layout.addWidget(remove_btn)
        action_layout.addWidget(clear_btn)

        table_layout.addWidget(action_bar)

        self._content_stack.addWidget(table_container)

        main_layout.addWidget(self._content_stack)

        self.setWidget(container)

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _apply_styles(self) -> None:
        """Apply VSCode Dark+ theme styling using THEME constants."""
        self.setStyleSheet(f"""
            VariablesPanel, QDockWidget, QWidget, QStackedWidget, QFrame {{
                background-color: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QDockWidget::title {{
                background-color: {THEME.dock_title_bg};
                color: {THEME.dock_title_text};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {THEME.border_dark};
            }}
            #variablesToolbar {{
                background-color: {THEME.bg_header};
                border-bottom: 1px solid {THEME.border_dark};
            }}
            {get_panel_toolbar_stylesheet()}
            {get_panel_table_stylesheet()}
        """)

    def _update_display(self) -> None:
        """Update empty state vs table display and count label."""
        has_variables = len(self._variables) > 0
        self._content_stack.setCurrentIndex(1 if has_variables else 0)

        # Update count label
        count = len(self._variables)
        self._count_label.setText(f"{count} variable{'s' if count != 1 else ''}")
        self._count_label.setProperty("muted", count == 0)
        self._count_label.style().unpolish(self._count_label)
        self._count_label.style().polish(self._count_label)

    def _on_context_menu(self, pos) -> None:
        """Show context menu for variable entry."""
        item = self._table.itemAt(pos)
        if not item:
            return

        row = item.row()
        name_item = self._table.item(row, self.COL_NAME)
        if not name_item:
            return

        var_name = name_item.text()

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {THEME.accent_primary};
                color: #ffffff;
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {THEME.border};
                margin: 4px 8px;
            }}
        """)

        # Copy name
        copy_name = menu.addAction("Copy Name")
        copy_name.triggered.connect(lambda: QApplication.clipboard().setText(var_name))

        # Copy value
        default_item = self._table.item(row, self.COL_DEFAULT)
        if default_item:
            copy_value = menu.addAction("Copy Value")
            copy_value.triggered.connect(
                lambda: QApplication.clipboard().setText(default_item.text())
            )

        menu.addSeparator()

        # Delete variable
        delete_action = menu.addAction("Delete Variable")
        delete_action.triggered.connect(lambda: self.remove_variable(var_name))

        menu.exec_(self._table.mapToGlobal(pos))

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Set runtime mode.

        In runtime mode, variable values are displayed but not editable.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        self._is_runtime_mode = enabled

        if enabled:
            self._mode_badge.set_status("running", "RUNTIME")
            self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        else:
            self._mode_badge.set_status("info", "DESIGN")
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

        # Store original name in UserRole for tracking renames
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.ItemDataRole.UserRole, name)
        name_item.setForeground(QBrush(QColor(THEME.accent_primary)))
        name_item.setToolTip(f"Variable: {name}\nDouble-click to rename")
        self._table.setItem(row, self.COL_NAME, name_item)

        # Type with color indicator
        type_item = QTableWidgetItem(var_type)
        type_color = TYPE_COLORS.get(var_type, THEME.text_primary)
        type_item.setForeground(QBrush(QColor(type_color)))
        type_item.setToolTip(f"Type: {var_type}\nDouble-click to change")
        self._table.setItem(row, self.COL_TYPE, type_item)

        # Default value
        default_item = QTableWidgetItem(str(default_value))
        default_item.setToolTip(f"Default value: {default_value}\nDouble-click to edit")
        self._table.setItem(row, self.COL_DEFAULT, default_item)

        # Scope (read-only)
        scope_item = QTableWidgetItem(scope)
        scope_item.setFlags(scope_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        scope_item.setForeground(QBrush(QColor(THEME.text_muted)))
        scope_item.setToolTip(f"Scope: {scope}")
        self._table.setItem(row, self.COL_SCOPE, scope_item)

        self.variable_added.emit(name, var_type, default_value)
        self.variables_changed.emit(self._variables)

        # Update display
        self._update_display()

        # Apply scope filter in case new variable doesn't match
        self._apply_scope_filter()

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

        # Update display
        self._update_display()

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
        self._update_display()
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

    def _on_scope_filter_changed(self, scope: str) -> None:
        """
        Handle scope filter dropdown change.

        Filters the table to show only variables matching the selected scope.

        Args:
            scope: Selected scope filter ("All", "Global", "Project", "Workflow")
        """
        self._current_scope_filter = scope
        self._apply_scope_filter()
        logger.debug(f"Scope filter changed to: {scope}")

    def _apply_scope_filter(self) -> None:
        """Apply current scope filter to table rows."""
        scope_filter = self._current_scope_filter

        for row in range(self._table.rowCount()):
            scope_item = self._table.item(row, self.COL_SCOPE)
            if scope_item:
                row_scope = scope_item.text()
                # Show row if filter is "All" or matches row scope
                should_show = scope_filter == "All" or row_scope == scope_filter
                self._table.setRowHidden(row, not should_show)

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

        current_name = name_item.text()
        # Get the original/stored name from UserRole (set when variable was added)
        stored_name = name_item.data(Qt.ItemDataRole.UserRole)

        # Handle NAME column change (variable rename)
        if col == self.COL_NAME:
            old_name = stored_name
            if old_name and old_name != current_name:
                # Check if new name is empty
                if not current_name.strip():
                    logger.warning("Variable name cannot be empty, reverting")
                    self._table.blockSignals(True)
                    name_item.setText(old_name)
                    self._table.blockSignals(False)
                    return

                # Check if new name already exists
                if current_name in self._variables:
                    logger.warning(
                        f"Variable '{current_name}' already exists, reverting rename"
                    )
                    self._table.blockSignals(True)
                    name_item.setText(old_name)
                    self._table.blockSignals(False)
                    return

                # Rename the variable in the dict
                var_data = self._variables.pop(old_name)
                self._variables[current_name] = var_data

                # Update the stored name to the new name
                name_item.setData(Qt.ItemDataRole.UserRole, current_name)

                logger.debug(f"Variable renamed: {old_name} -> {current_name}")

                self.variable_changed.emit(
                    current_name,
                    var_data["type"],
                    var_data["default"],
                )
                self.variables_changed.emit(self._variables)
            return

        # For other columns, use stored name to find the variable
        # (in case table text doesn't match dict key due to pending edits)
        lookup_name = stored_name if stored_name in self._variables else current_name

        if lookup_name not in self._variables:
            logger.warning(f"Variable '{lookup_name}' not found in internal dict")
            return

        # Update variable data
        if col == self.COL_TYPE:
            var_type = item.text()
            self._variables[lookup_name]["type"] = var_type

            # Update type color
            type_color = TYPE_COLORS.get(var_type, THEME.text_primary)
            item.setForeground(QBrush(QColor(type_color)))

            # Update default value to match type
            default_value = TYPE_DEFAULTS.get(var_type, "")
            self._variables[lookup_name]["default"] = default_value
            default_item = self._table.item(row, self.COL_DEFAULT)
            if default_item:
                # Block signals to prevent double-emit
                self._table.blockSignals(True)
                default_item.setText(str(default_value))
                self._table.blockSignals(False)

        elif col == self.COL_DEFAULT:
            self._variables[lookup_name]["default"] = item.text()

        self.variable_changed.emit(
            lookup_name,
            self._variables[lookup_name]["type"],
            self._variables[lookup_name]["default"],
        )
        self.variables_changed.emit(self._variables)

    def _setup_lazy_subscriptions(self) -> None:
        """
        Set up lazy EventBus subscriptions.

        Subscriptions only activate when panel is visible, reducing
        EventBus overhead when panel is hidden.
        """
        self._lazy_subscriptions = LazySubscriptionGroup(
            self,
            [
                (EventType.VARIABLE_SET, self._on_variable_set_event),
                (EventType.VARIABLE_UPDATED, self._on_variable_updated_event),
                (EventType.VARIABLE_DELETED, self._on_variable_deleted_event),
                (EventType.EXECUTION_STARTED, self._on_execution_started),
                (EventType.EXECUTION_COMPLETED, self._on_execution_completed),
            ],
        )

    def _on_variable_set_event(self, event: Event) -> None:
        """
        Handle variable set event from execution.

        Args:
            event: Event with name, type, value data
        """
        name = event.get("name", "")
        var_type = event.get("type", "String")
        value = event.get("value", "")
        scope = event.get("scope", "Workflow")

        if name and name not in self._variables:
            self.add_variable(name, var_type, value, scope)

    def _on_variable_updated_event(self, event: Event) -> None:
        """
        Handle variable updated event from execution.

        Args:
            event: Event with name, value data
        """
        name = event.get("name", "")
        value = event.get("value")

        if name and name in self._variables:
            self.update_variable_value(name, value)

    def _on_variable_deleted_event(self, event: Event) -> None:
        """
        Handle variable deleted event.

        Args:
            event: Event with name data
        """
        name = event.get("name", "")
        if name:
            self.remove_variable(name)

    def _on_execution_started(self, event: Event) -> None:
        """
        Handle execution started event.

        Args:
            event: Execution started event
        """
        self.set_runtime_mode(True)

    def _on_execution_completed(self, event: Event) -> None:
        """
        Handle execution completed event.

        Args:
            event: Execution completed event
        """
        self.set_runtime_mode(False)
