"""
Variables Panel UI Component.

Provides workflow variable management with improved UX:
- Grouped tree view by scope (Global, Project, Scenario)
- Inline variable editing with type-appropriate editors
- Sensitive variable masking (*****)
- Type selection with visual indicators
- Scope filtering
- Design/Runtime mode switching
- Context menu for copy/edit/delete
- Variable picker integration

Uses LazySubscription for EventBus optimization - subscriptions are only active
when the panel is visible, reducing overhead when panel is hidden.

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.domain.entities.variable import Variable
from casare_rpa.infrastructure.security.data_masker import get_masker
from casare_rpa.presentation.canvas.events import (
    Event,
    EventType,
    LazySubscriptionGroup,
)
from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton
from casare_rpa.presentation.canvas.ui.widgets.primitives.feedback import Badge
from casare_rpa.presentation.canvas.ui.widgets.primitives.lists import apply_tree_style
from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import EmptyState

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
TYPE_DEFAULTS: dict[str, Any] = {
    "String": "",
    "Integer": 0,
    "Float": 0.0,
    "Boolean": False,
    "List": [],
    "Dict": {},
    "DataTable": None,
}

# Type colors (matching type colors for consistency)
# Use THEME_V2 wire colors for v2 design system
TYPE_COLORS = {
    "String": THEME_V2.wire_string,
    "Integer": THEME_V2.wire_number,
    "Float": THEME_V2.wire_number,
    "Boolean": THEME_V2.wire_bool,
    "List": THEME_V2.wire_list,
    "Dict": THEME_V2.wire_dict,
    "DataTable": THEME_V2.wire_table,
}

# Type badges for compact display
TYPE_BADGES = {
    "String": "T",
    "Integer": "#",
    "Float": ".",
    "Boolean": "?",
    "List": "[]",
    "Dict": "{}",
    "DataTable": "tbl",
}

# Masked value display for sensitive variables
MASKED_VALUE = "******"


class VariableEditDialog(QDialog):
    """
    Dialog for adding or editing a variable.

    Provides type-appropriate value editors:
    - String: QLineEdit
    - Integer: QSpinBox
    - Float: QDoubleSpinBox
    - Boolean: QCheckBox
    - List/Dict: QTextEdit (JSON)
    - DataTable: QTextEdit (JSON)
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        variable: Variable | None = None,
        scope: str = "Workflow",
    ) -> None:
        """
        Initialize the dialog.

        Args:
            parent: Parent widget
            variable: Existing variable to edit (None for new)
            scope: Default scope for new variables
        """
        super().__init__(parent)

        self._variable = variable
        self._is_edit = variable is not None
        self._current_type = variable.type if variable else "String"

        title = "Edit Variable" if self._is_edit else "Add Variable"
        self.setWindowTitle(title)
        self.setMinimumWidth(TOKENS_V2.sizes.dialog_sm_width)
        self.setModal(True)

        self._setup_ui(scope)
        self._apply_styles()
        self._populate_from_variable()
        self._connect_signals()

    def _setup_ui(self, default_scope: str) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS_V2.spacing.md)
        layout.setContentsMargins(
            TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg, TOKENS_V2.spacing.lg
        )

        # Form layout for fields
        form = QFormLayout()
        form.setSpacing(TOKENS_V2.spacing.sm)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Name field
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter variable name...")
        self._name_edit.setObjectName("nameEdit")
        form.addRow("Name:", self._name_edit)

        # Type dropdown
        self._type_combo = QComboBox()
        self._type_combo.addItems(VARIABLE_TYPES)
        self._type_combo.setObjectName("typeCombo")
        form.addRow("Type:", self._type_combo)

        # Scope dropdown
        self._scope_combo = QComboBox()
        self._scope_combo.addItems(["Global", "Project", "Scenario"])
        self._scope_combo.setCurrentText(default_scope)
        self._scope_combo.setObjectName("scopeCombo")
        form.addRow("Scope:", self._scope_combo)

        layout.addLayout(form)

        # Value editor stack (different widgets for different types)
        value_label = QLabel("Default Value:")
        layout.addWidget(value_label)

        self._value_stack = QStackedWidget()
        self._value_stack.setMinimumHeight(80)

        # String value (index 0)
        self._string_edit = QLineEdit()
        self._string_edit.setPlaceholderText("Enter string value...")
        self._value_stack.addWidget(self._string_edit)

        # Integer value (index 1)
        self._int_edit = QSpinBox()
        self._int_edit.setRange(-2147483648, 2147483647)
        self._value_stack.addWidget(self._int_edit)

        # Float value (index 2)
        self._float_edit = QDoubleSpinBox()
        self._float_edit.setRange(-1e15, 1e15)
        self._float_edit.setDecimals(6)
        self._value_stack.addWidget(self._float_edit)

        # Boolean value (index 3)
        bool_container = QWidget()
        bool_layout = QHBoxLayout(bool_container)
        bool_layout.setContentsMargins(0, 0, 0, 0)
        self._bool_check = QCheckBox("True")
        bool_layout.addWidget(self._bool_check)
        bool_layout.addStretch()
        self._value_stack.addWidget(bool_container)

        # List/Dict/DataTable value - JSON editor (index 4)
        self._json_edit = QTextEdit()
        self._json_edit.setPlaceholderText("Enter JSON value (e.g., [] or {})...")
        self._json_edit.setAcceptRichText(False)
        self._value_stack.addWidget(self._json_edit)

        layout.addWidget(self._value_stack)

        # Sensitive checkbox
        self._sensitive_check = QCheckBox("Sensitive (mask value in UI)")
        self._sensitive_check.setProperty("spacing", TOKENS_V2.spacing.sm)
        self._sensitive_check.setToolTip(
            "When checked, the variable value will be displayed as ****** in the UI"
        )
        layout.addWidget(self._sensitive_check)

        # Description field
        desc_label = QLabel("Description (optional):")
        layout.addWidget(desc_label)

        self._desc_edit = QLineEdit()
        self._desc_edit.setPlaceholderText("Enter description...")
        layout.addWidget(self._desc_edit)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _apply_styles(self) -> None:
        """Apply dialog styling using v2 tokens."""
        t = THEME_V2
        tok = TOKENS_V2
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {t.bg_surface};
                color: {t.text_primary};
            }}
            QLabel {{
                color: {t.text_primary};
                background: transparent;
            }}
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
                background-color: {t.input_bg};
                color: {t.text_primary};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: 4px 8px;
                min-height: {tok.sizes.input_md}px;
            }}
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
                border-color: {t.border_focus};
            }}
            QTextEdit {{
                background-color: {t.input_bg};
                color: {t.text_primary};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                font-family: {tok.typography.mono};
                font-size: {tok.typography.body_sm}px;
            }}
            QTextEdit:focus {{
                border-color: {t.border_focus};
            }}
            QCheckBox {{
                color: {t.text_primary};
                spacing: 8px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t.bg_elevated};
                color: {t.text_primary};
                border: 1px solid {t.border};
                selection-background-color: {t.primary};
            }}
            QDialogButtonBox QPushButton {{
                background-color: {t.bg_hover};
                color: {t.text_primary};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 4px 12px;
                min-width: 80px;
                min-height: {tok.sizes.button_md}px;
            }}
            QDialogButtonBox QPushButton:hover {{
                background-color: {t.bg_component};
                border-color: {t.border_light};
            }}
            QDialogButtonBox QPushButton:default {{
                background-color: {t.primary};
                border-color: {t.primary};
                color: {t.text_on_primary};
            }}
            QDialogButtonBox QPushButton:default:hover {{
                background-color: {t.primary_hover};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect UI signals."""
        self._type_combo.currentTextChanged.connect(self._on_type_changed)

    def _populate_from_variable(self) -> None:
        """Populate fields from existing variable."""
        if self._variable:
            self._name_edit.setText(self._variable.name)
            self._name_edit.setEnabled(False)  # Cannot rename
            self._type_combo.setCurrentText(self._variable.type)
            self._sensitive_check.setChecked(self._variable.sensitive)
            self._desc_edit.setText(self._variable.description)

            # Set value based on type
            self._set_value_for_type(self._variable.type, self._variable.default_value)
        else:
            # Default for new variable
            self._on_type_changed("String")

    @Slot(str)
    def _on_type_changed(self, var_type: str) -> None:
        """Handle type change - switch value editor."""
        self._current_type = var_type

        # Map type to stack index
        type_to_index = {
            "String": 0,
            "Integer": 1,
            "Float": 2,
            "Boolean": 3,
            "List": 4,
            "Dict": 4,
            "DataTable": 4,
        }
        index = type_to_index.get(var_type, 0)
        self._value_stack.setCurrentIndex(index)

        # Set default value for new type
        default = TYPE_DEFAULTS.get(var_type, "")
        self._set_value_for_type(var_type, default)

    def _set_value_for_type(self, var_type: str, value: Any) -> None:
        """Set value editor based on type."""
        if var_type == "String":
            self._string_edit.setText(str(value) if value else "")
        elif var_type == "Integer":
            try:
                self._int_edit.setValue(int(value) if value else 0)
            except (ValueError, TypeError):
                self._int_edit.setValue(0)
        elif var_type == "Float":
            try:
                self._float_edit.setValue(float(value) if value else 0.0)
            except (ValueError, TypeError):
                self._float_edit.setValue(0.0)
        elif var_type == "Boolean":
            self._bool_check.setChecked(bool(value) if value else False)
        else:
            # List, Dict, DataTable - JSON
            import json as json_module

            try:
                if isinstance(value, list | dict):
                    text = json_module.dumps(value, indent=2)
                elif value is None:
                    text = (
                        "null" if var_type == "DataTable" else "[]" if var_type == "List" else "{}"
                    )
                else:
                    text = str(value)
                self._json_edit.setPlainText(text)
            except Exception:
                self._json_edit.setPlainText("")

    def _get_value_from_editor(self) -> Any:
        """Get value from the current editor."""
        var_type = self._type_combo.currentText()

        if var_type == "String":
            return self._string_edit.text()
        elif var_type == "Integer":
            return self._int_edit.value()
        elif var_type == "Float":
            return self._float_edit.value()
        elif var_type == "Boolean":
            return self._bool_check.isChecked()
        else:
            # List, Dict, DataTable - JSON
            import json as json_module

            text = self._json_edit.toPlainText().strip()
            if not text:
                return [] if var_type == "List" else {} if var_type == "Dict" else None
            try:
                return json_module.loads(text)
            except json_module.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON: {e}") from e

    @Slot()
    def _on_accept(self) -> None:
        """Validate and accept the dialog."""
        name = self._name_edit.text().strip()

        # Validate name
        if not name:
            self._show_error("Name is required")
            self._name_edit.setFocus()
            return

        # Validate name format (Python identifier)
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            self._show_error(
                "Invalid variable name. Must start with a letter or underscore "
                "and contain only letters, numbers, and underscores."
            )
            self._name_edit.setFocus()
            return

        # Validate value
        try:
            self._get_value_from_editor()
        except ValueError as e:
            self._show_error(str(e))
            return

        self.accept()

    def _show_error(self, message: str) -> None:
        """Show error message using v2 styling."""
        t = THEME_V2
        tok = TOKENS_V2
        msg = QMessageBox(self)
        msg.setWindowTitle("Validation Error")
        msg.setText(message)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {t.bg_surface}; }}
            QMessageBox QLabel {{ color: {t.text_primary}; }}
            QPushButton {{
                background: {t.bg_hover};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 4px 12px;
                color: {t.text_primary};
                min-width: 80px;
                min-height: {tok.sizes.button_md}px;
            }}
            QPushButton:hover {{ background: {t.bg_component}; }}
        """)
        msg.exec()

    def get_variable(self) -> Variable:
        """
        Get the configured variable.

        Returns:
            Variable entity with configured values
        """
        return Variable(
            name=self._name_edit.text().strip(),
            type=self._type_combo.currentText(),
            default_value=self._get_value_from_editor(),
            description=self._desc_edit.text().strip(),
            sensitive=self._sensitive_check.isChecked(),
            readonly=False,
        )

    def get_scope(self) -> str:
        """Get the selected scope."""
        return self._scope_combo.currentText()


class VariablesPanel(QDockWidget):
    """
    Dockable variables panel for workflow variable management.

    Features:
    - Grouped tree view by scope (Global, Project, Scenario)
    - Empty state when no variables
    - Type-appropriate value editors
    - Sensitive variable masking
    - Type selection with color indicators
    - Default value editing
    - Scope filtering
    - Design/Runtime modes
    - Context menu for actions
    - EventBus integration for variable events

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

    # Scope display order
    SCOPE_ORDER = ["Global", "Project", "Scenario"]

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the variables panel.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Variables", parent)
        self.setObjectName("VariablesDock")

        # Variables organized by scope: {scope: {name: Variable}}
        self._variables: dict[str, dict[str, Variable]] = {
            "Global": {},
            "Project": {},
            "Scenario": {},
        }
        self._is_runtime_mode = False
        self._current_scope_filter = "All"

        # Tree item tracking
        self._scope_items: dict[str, QTreeWidgetItem] = {}

        self._setup_dock()
        self._setup_ui()
        self._apply_styles()
        self._setup_lazy_subscriptions()

        logger.debug("VariablesPanel initialized")

    def _setup_dock(self) -> None:
        """Configure dock widget properties (Epic 6.1: dock-only constraint)."""
        self.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        # Dock-only: NO DockWidgetFloatable (Epic 6.1 requirement)
        self.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable
            | QDockWidget.DockWidgetFeature.DockWidgetClosable
        )
        self.setMinimumWidth(TOKENS_V2.sizes.panel_min_width)

    def _setup_ui(self) -> None:
        """Set up the user interface using v2 primitives."""
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar (v2 style)
        toolbar_widget = QWidget()
        toolbar_widget.setObjectName("variablesToolbar")
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.sm,
        )
        toolbar.setSpacing(TOKENS_V2.spacing.xs)

        # Variable count label
        self._count_label = QLabel("0 variables")
        self._count_label.setProperty("muted", True)

        # Scope filter dropdown
        filter_label = QLabel("Scope:")
        self._scope_filter = QComboBox()
        self._scope_filter.addItems(["All", "Global", "Project", "Scenario"])
        self._scope_filter.setFixedWidth(90)
        self._scope_filter.currentTextChanged.connect(self._on_scope_filter_changed)
        self._scope_filter.setToolTip("Filter variables by scope")

        # Mode badge (v2 Badge)
        self._mode_badge = Badge(text="DESIGN", variant="label", color="info")

        # Add variable button (v2 PushButton)
        add_btn = PushButton(
            text="Add Variable",
            variant="primary",
            size="sm",
        )
        add_btn.setToolTip("Add a new variable (Ctrl+N)")
        add_btn.clicked.connect(self._on_add_variable)

        toolbar.addWidget(self._count_label)
        toolbar.addStretch()
        toolbar.addWidget(filter_label)
        toolbar.addWidget(self._scope_filter)
        toolbar.addWidget(self._mode_badge)
        toolbar.addWidget(add_btn)

        main_layout.addWidget(toolbar_widget)

        # Content stack for empty state vs tree
        self._content_stack = QStackedWidget()

        # Empty state (index 0) - v2 EmptyState component
        self._empty_state = EmptyState(
            icon="inbox",
            text=(
                "Variables store data that can be used across your workflow.\n\n"
                "Click 'Add Variable' to create:\n"
                "- Strings, numbers, and booleans\n"
                "- Lists and dictionaries\n"
                "- DataTables for structured data\n\n"
                "Scopes:\n"
                "- Global: Available to all projects\n"
                "- Project: Available within project\n"
                "- Scenario: Current workflow only"
            ),
            action_text="Add Variable",
        )
        self._empty_state.action_clicked.connect(self._on_add_variable)
        self._content_stack.addWidget(self._empty_state)

        # Tree container (index 1)
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.md,
        )
        tree_layout.setSpacing(TOKENS_V2.spacing.xs)

        # Variables tree widget
        self._tree = QTreeWidget()
        self._tree.setColumnCount(4)
        self._tree.setHeaderLabels(["Name", "Type", "Value", ""])
        self._tree.setAlternatingRowColors(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)
        self._tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._tree.setIndentation(TOKENS_V2.spacing.lg)
        self._tree.setRootIsDecorated(True)

        # Apply v2 tree styling
        apply_tree_style(self._tree)
        # Re-enable header for columns (apply_tree_style hides it)
        self._tree.setHeaderHidden(False)

        # Configure column sizing
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Value
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Actions
        header.resizeSection(3, 40)

        tree_layout.addWidget(self._tree)

        # Action bar
        action_bar = QWidget()
        action_bar.setObjectName("actionBar")
        action_layout = QHBoxLayout(action_bar)
        action_layout.setContentsMargins(0, TOKENS_V2.spacing.xs, 0, 0)
        action_layout.setSpacing(TOKENS_V2.spacing.sm)

        # Edit button (v2 PushButton)
        edit_btn = PushButton(
            text="Edit",
            variant="secondary",
            size="sm",
        )
        edit_btn.setToolTip("Edit selected variable (Enter or double-click)")
        edit_btn.clicked.connect(self._on_edit_variable)

        # Remove selected button (v2 PushButton)
        remove_btn = PushButton(
            text="Delete",
            variant="ghost",
            size="sm",
        )
        remove_btn.setToolTip("Delete selected variable (Delete key)")
        remove_btn.clicked.connect(self._on_remove_variable)

        # Clear all button (v2 PushButton with danger)
        clear_btn = PushButton(
            text="Clear All",
            variant="danger",
            size="sm",
        )
        clear_btn.setToolTip("Remove all variables")
        clear_btn.clicked.connect(self._on_clear_all)

        action_layout.addStretch()
        action_layout.addWidget(edit_btn)
        action_layout.addWidget(remove_btn)
        action_layout.addWidget(clear_btn)

        tree_layout.addWidget(action_bar)

        self._content_stack.addWidget(tree_container)

        main_layout.addWidget(self._content_stack)

        self.setWidget(container)

        # Initialize scope groups
        self._initialize_scope_groups()

        # Show empty state initially
        self._content_stack.setCurrentIndex(0)

    def _initialize_scope_groups(self) -> None:
        """Initialize the scope group items in the tree."""
        for scope in self.SCOPE_ORDER:
            scope_item = QTreeWidgetItem([scope, "", "", ""])
            scope_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "scope", "scope": scope})

            # Style scope header (v2 theme)
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            scope_item.setFont(0, font)
            scope_item.setForeground(0, QBrush(QColor(THEME_V2.text_header)))

            # Make it non-selectable
            scope_item.setFlags(scope_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)

            self._tree.addTopLevelItem(scope_item)
            scope_item.setExpanded(True)
            self._scope_items[scope] = scope_item

    def _apply_styles(self) -> None:
        """Apply v2 theme styling using THEME_V2/TOKENS_V2."""
        t = THEME_V2
        tok = TOKENS_V2
        self.setStyleSheet(f"""
            VariablesPanel, QDockWidget, QWidget, QStackedWidget, QFrame {{
                background-color: {t.bg_surface};
                color: {t.text_primary};
            }}
            QDockWidget::title {{
                background-color: {t.bg_header};
                color: {t.text_header};
                padding: 8px 12px;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                border-bottom: 1px solid {t.border};
            }}
            #variablesToolbar {{
                background-color: {t.bg_header};
                border-bottom: 1px solid {t.border};
            }}
            QLabel {{
                background: transparent;
                color: {t.text_secondary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.ui};
            }}
            QLabel[muted="true"] {{
                color: {t.text_muted};
            }}
            QComboBox {{
                background-color: {t.bg_hover};
                color: {t.text_primary};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 4px 6px;
                min-width: {tok.sizes.input_min_width}px;
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.ui};
            }}
            QComboBox:hover {{
                border-color: {t.border_light};
            }}
            QComboBox:focus {{
                border-color: {t.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: {tok.sizes.icon_sm}px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t.bg_elevated};
                color: {t.text_primary};
                border: 1px solid {t.border};
                selection-background-color: {t.primary};
            }}
        """)

    def _update_display(self) -> None:
        """Update empty state vs tree display and count label."""
        total_count = sum(len(vars) for vars in self._variables.values())
        has_variables = total_count > 0
        self._content_stack.setCurrentIndex(1 if has_variables else 0)

        # Update count label
        self._count_label.setText(f"{total_count} variable{'s' if total_count != 1 else ''}")
        self._count_label.setProperty("muted", total_count == 0)
        self._count_label.style().unpolish(self._count_label)
        self._count_label.style().polish(self._count_label)

        # Update scope group visibility
        self._apply_scope_filter()

    def _is_sensitive_variable_name(self, name: str) -> bool:
        """
        Check if a variable name suggests sensitive data.

        Uses DataMasker to detect sensitive key patterns.

        Args:
            name: Variable name to check

        Returns:
            True if name suggests sensitive data
        """
        try:
            masker = get_masker()
            return masker.is_sensitive_key(name)
        except Exception:
            # Fallback to basic check if masker unavailable
            sensitive_patterns = {
                "password",
                "passwd",
                "pwd",
                "secret",
                "token",
                "api_key",
                "apikey",
                "credential",
                "auth",
                "key",
                "private",
            }
            name_lower = name.lower()
            return any(pattern in name_lower for pattern in sensitive_patterns)

    def _format_value_display(self, variable: Variable) -> str:
        """
        Format value for display in the tree.

        Automatically masks sensitive values based on variable name
        patterns or explicit sensitive flag.

        Args:
            variable: Variable entity

        Returns:
            Formatted display string (masked if sensitive)
        """
        # Explicit sensitive flag takes priority
        if variable.sensitive:
            return MASKED_VALUE

        # Auto-detect sensitive variable names
        if self._is_sensitive_variable_name(variable.name):
            return MASKED_VALUE

        value = variable.default_value

        if value is None:
            return "(null)"
        elif isinstance(value, bool):
            return "true" if value else "false"
        elif isinstance(value, list | dict):
            import json as json_module

            try:
                text = json_module.dumps(value)
                # Mask any sensitive values in the JSON
                try:
                    masker = get_masker()
                    text = masker.mask_string(text)
                except Exception:
                    pass
                if len(text) > 30:
                    text = text[:27] + "..."
                return text
            except Exception:
                return str(value)[:30]
        else:
            text = str(value)
            # Mask any sensitive patterns in string values
            try:
                masker = get_masker()
                text = masker.mask_string(text)
            except Exception:
                pass
            if len(text) > 30:
                text = text[:27] + "..."
            return text

    def _add_variable_to_tree(self, variable: Variable, scope: str) -> QTreeWidgetItem:
        """
        Add a variable item to the tree under its scope group.

        Args:
            variable: Variable entity
            scope: Scope string

        Returns:
            Created tree widget item
        """
        scope_item = self._scope_items.get(scope)
        if not scope_item:
            logger.warning(f"Unknown scope: {scope}")
            scope_item = self._scope_items.get("Scenario", self._scope_items["Global"])

        # Create variable item
        type_badge = TYPE_BADGES.get(variable.type, "?")
        value_display = self._format_value_display(variable)

        var_item = QTreeWidgetItem(
            [
                variable.name,
                f"[{type_badge}] {variable.type}",
                value_display,
                "",  # Actions column
            ]
        )

        # Store variable data
        var_item.setData(
            0,
            Qt.ItemDataRole.UserRole,
            {
                "type": "variable",
                "name": variable.name,
                "scope": scope,
                "variable": variable,
            },
        )

        # Apply type color to name (v2 theme)
        var_item.setForeground(0, QBrush(QColor(THEME_V2.primary)))

        # Apply type color to type column
        type_color = THEME_V2.text_muted
        var_item.setForeground(1, QBrush(QColor(type_color)))

        # Value color
        if variable.sensitive:
            var_item.setForeground(2, QBrush(QColor(THEME_V2.text_muted)))
        else:
            var_item.setForeground(2, QBrush(QColor(THEME_V2.text_secondary)))

        # Tooltip with full info
        tooltip = f"Name: {variable.name}\nType: {variable.type}\nScope: {scope}"
        if variable.description:
            tooltip += f"\nDescription: {variable.description}"
        if variable.sensitive:
            tooltip += "\n(Sensitive - value hidden)"
        var_item.setToolTip(0, tooltip)
        var_item.setToolTip(1, tooltip)
        var_item.setToolTip(2, tooltip)

        scope_item.addChild(var_item)
        return var_item

    def _find_variable_item(self, name: str, scope: str) -> QTreeWidgetItem | None:
        """
        Find a variable item in the tree.

        Args:
            name: Variable name
            scope: Scope string

        Returns:
            Tree item or None if not found
        """
        scope_item = self._scope_items.get(scope)
        if not scope_item:
            return None

        for i in range(scope_item.childCount()):
            child = scope_item.child(i)
            data = child.data(0, Qt.ItemDataRole.UserRole)
            if data and data.get("name") == name:
                return child

        return None

    @Slot(object)
    def _on_context_menu(self, pos: QPoint) -> None:
        """Show context menu for variable entry (v2 styling)."""
        item = self._tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "variable":
            return  # Only show menu for variable items

        var_name = data.get("name", "")
        scope = data.get("scope", "")
        variable = data.get("variable")

        # Store context menu data for slot methods
        self._context_var_name = var_name
        self._context_scope = scope
        self._context_variable = variable

        # Create context menu with v2 styling
        t = THEME_V2
        tok = TOKENS_V2
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {t.bg_elevated};
                color: {t.text_primary};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 6px 24px 6px 12px;
                border-radius: 3px;
            }}
            QMenu::item:selected {{
                background-color: {t.primary};
                color: {t.text_on_primary};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {t.border};
                margin: 4px 8px;
            }}
        """)

        # Edit variable
        edit_action = menu.addAction("Edit Variable")
        edit_action.triggered.connect(self._on_context_edit_variable)

        menu.addSeparator()

        # Copy name
        copy_name = menu.addAction("Copy Name")
        copy_name.triggered.connect(self._on_context_copy_name)

        # Copy value (only if not sensitive)
        if variable and not variable.sensitive:
            copy_value = menu.addAction("Copy Value")
            copy_value.triggered.connect(self._on_context_copy_value)

        # Copy insertion text
        copy_insert = menu.addAction("Copy {{variable}}")
        copy_insert.triggered.connect(self._on_context_copy_insertion)

        menu.addSeparator()

        # Delete variable
        delete_action = menu.addAction("Delete Variable")
        delete_action.triggered.connect(self._on_context_delete_variable)

        menu.exec_(self._tree.mapToGlobal(pos))

    @Slot()
    def _on_context_edit_variable(self) -> None:
        """Edit variable from context menu."""
        if hasattr(self, "_context_var_name") and hasattr(self, "_context_scope"):
            self._edit_variable(self._context_var_name, self._context_scope)

    @Slot()
    def _on_context_copy_name(self) -> None:
        """Copy variable name from context menu."""
        if hasattr(self, "_context_var_name"):
            QApplication.clipboard().setText(self._context_var_name)

    @Slot()
    def _on_context_copy_value(self) -> None:
        """Copy variable value from context menu."""
        if hasattr(self, "_context_variable") and self._context_variable:
            QApplication.clipboard().setText(str(self._context_variable.default_value))

    @Slot()
    def _on_context_copy_insertion(self) -> None:
        """Copy variable insertion text from context menu."""
        if hasattr(self, "_context_var_name"):
            QApplication.clipboard().setText(f"{{{{{self._context_var_name}}}}}")

    @Slot()
    def _on_context_delete_variable(self) -> None:
        """Delete variable from context menu."""
        if hasattr(self, "_context_var_name") and hasattr(self, "_context_scope"):
            self.remove_variable(self._context_var_name, self._context_scope)

    @Slot(QTreeWidgetItem, int)
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle double-click on tree item."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "variable":
            return

        var_name = data.get("name", "")
        scope = data.get("scope", "")
        self._edit_variable(var_name, scope)

    def set_runtime_mode(self, enabled: bool) -> None:
        """
        Set runtime mode using v2 Badge API.

        In runtime mode, variable values are displayed but not editable.

        Args:
            enabled: True for runtime mode, False for design mode
        """
        self._is_runtime_mode = enabled

        if enabled:
            self._mode_badge.set_text("RUNTIME")
            self._mode_badge.set_color("warning")
        else:
            self._mode_badge.set_text("DESIGN")
            self._mode_badge.set_color("info")

        logger.debug(f"Variables panel mode: {'Runtime' if enabled else 'Design'}")

    def add_variable(
        self,
        name: str,
        var_type: str = "String",
        default_value: Any = "",
        scope: str = "Scenario",
        description: str = "",
        sensitive: bool = False,
    ) -> bool:
        """
        Add a variable to the panel.

        Args:
            name: Variable name
            var_type: Variable type
            default_value: Default value
            scope: Variable scope (Global, Project, Scenario)
            description: Optional description
            sensitive: Whether to mask value

        Returns:
            True if added successfully
        """
        # Normalize scope
        if scope not in self.SCOPE_ORDER:
            scope = "Scenario"

        # Check if variable already exists in this scope
        if name in self._variables.get(scope, {}):
            logger.warning(f"Variable '{name}' already exists in {scope} scope")
            return False

        # Auto-detect sensitive variables based on name
        if not sensitive and self._is_sensitive_variable_name(name):
            sensitive = True
            logger.debug(f"Auto-detected sensitive variable: {name}")

        # Create Variable entity
        try:
            variable = Variable(
                name=name,
                type=var_type,
                default_value=default_value,
                description=description,
                sensitive=sensitive,
                readonly=False,
            )
        except ValueError as e:
            logger.error(f"Invalid variable: {e}")
            return False

        # Store variable
        if scope not in self._variables:
            self._variables[scope] = {}
        self._variables[scope][name] = variable

        # Add to tree
        self._add_variable_to_tree(variable, scope)

        # Emit signals
        self.variable_added.emit(name, var_type, default_value)
        self.variables_changed.emit(self.get_all_variables_flat())

        # Update display
        self._update_display()

        logger.debug(f"Variable added: {name} ({var_type}) in {scope} scope")
        return True

    def remove_variable(self, name: str, scope: str | None = None) -> bool:
        """
        Remove a variable from the panel.

        Args:
            name: Variable name
            scope: Scope to remove from (None = search all scopes)

        Returns:
            True if removed successfully
        """
        if scope:
            scopes_to_check = [scope]
        else:
            scopes_to_check = self.SCOPE_ORDER

        for s in scopes_to_check:
            if s in self._variables and name in self._variables[s]:
                # Remove from dict
                del self._variables[s][name]

                # Remove from tree
                item = self._find_variable_item(name, s)
                if item:
                    parent = item.parent()
                    if parent:
                        parent.removeChild(item)

                # Emit signals
                self.variable_removed.emit(name)
                self.variables_changed.emit(self.get_all_variables_flat())

                # Update display
                self._update_display()

                logger.debug(f"Variable removed: {name} from {s} scope")
                return True

        return False

    def update_variable_value(self, name: str, value: Any, scope: str | None = None) -> None:
        """
        Update variable value (runtime mode).

        Args:
            name: Variable name
            value: New value
            scope: Scope to update (None = search all scopes)
        """
        if scope:
            scopes_to_check = [scope]
        else:
            scopes_to_check = self.SCOPE_ORDER

        for s in scopes_to_check:
            if s in self._variables and name in self._variables[s]:
                variable = self._variables[s][name]
                variable.default_value = value

                # Update tree item
                item = self._find_variable_item(name, s)
                if item:
                    value_display = self._format_value_display(variable)
                    item.setText(2, value_display)

                logger.debug(f"Variable updated: {name} = {value}")
                return

    def _edit_variable(self, name: str, scope: str) -> None:
        """
        Open edit dialog for a variable.

        Args:
            name: Variable name
            scope: Scope
        """
        if self._is_runtime_mode:
            return

        variable = self._variables.get(scope, {}).get(name)
        if not variable:
            return

        dialog = VariableEditDialog(self, variable=variable, scope=scope)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_var = dialog.get_variable()

            # Update the variable
            self._variables[scope][name] = new_var

            # Update tree item
            item = self._find_variable_item(name, scope)
            if item:
                type_badge = TYPE_BADGES.get(new_var.type, "?")
                item.setText(1, f"[{type_badge}] {new_var.type}")
                item.setText(2, self._format_value_display(new_var))

                # Update colors (v2 theme)
                type_color = THEME_V2.text_muted
                item.setForeground(1, QBrush(QColor(type_color)))

                if new_var.sensitive:
                    item.setForeground(2, QBrush(QColor(THEME_V2.text_muted)))
                else:
                    item.setForeground(2, QBrush(QColor(THEME_V2.text_secondary)))

                # Update stored data
                item.setData(
                    0,
                    Qt.ItemDataRole.UserRole,
                    {
                        "type": "variable",
                        "name": name,
                        "scope": scope,
                        "variable": new_var,
                    },
                )

            # Emit signals
            self.variable_changed.emit(name, new_var.type, new_var.default_value)
            self.variables_changed.emit(self.get_all_variables_flat())

            logger.debug(f"Variable edited: {name}")

    def get_variables(self) -> dict[str, dict[str, Any]]:
        """
        Get all variables in flat format for variable picker.

        Returns:
            Dictionary of {name: {type: str, default: Any, scope: str}}
        """
        result = {}
        for scope, vars in self._variables.items():
            for name, var in vars.items():
                result[name] = {
                    "type": var.type,
                    "default": var.default_value,
                    "scope": scope,
                }
        return result

    def get_all_variables_flat(self) -> dict[str, dict[str, Any]]:
        """
        Get all variables in flat format.

        Returns:
            Dictionary of {name: {type: str, default: Any, scope: str, sensitive: bool}}
        """
        result = {}
        for scope, vars in self._variables.items():
            for name, var in vars.items():
                result[name] = {
                    "type": var.type,
                    "default": var.default_value,
                    "scope": scope,
                    "sensitive": var.sensitive,
                    "description": var.description,
                }
        return result

    def get_variables_by_scope(self, scope: str) -> dict[str, Variable]:
        """
        Get variables for a specific scope.

        Args:
            scope: Scope string

        Returns:
            Dictionary of {name: Variable}
        """
        return self._variables.get(scope, {}).copy()

    def clear_variables(self, scope: str | None = None) -> None:
        """
        Clear variables.

        Args:
            scope: Specific scope to clear (None = clear all)
        """
        if scope:
            scopes_to_clear = [scope]
        else:
            scopes_to_clear = self.SCOPE_ORDER

        for s in scopes_to_clear:
            self._variables[s] = {}
            scope_item = self._scope_items.get(s)
            if scope_item:
                # Remove all children
                while scope_item.childCount() > 0:
                    scope_item.removeChild(scope_item.child(0))

        self.variables_changed.emit(self.get_all_variables_flat())
        self._update_display()
        logger.debug(f"Variables cleared: {scope or 'all scopes'}")

    @Slot()
    def _on_add_variable(self) -> None:
        """Handle add variable button click."""
        if self._is_runtime_mode:
            return

        # Determine default scope based on filter
        default_scope = self._current_scope_filter
        if default_scope == "All":
            default_scope = "Scenario"

        dialog = VariableEditDialog(self, scope=default_scope)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            variable = dialog.get_variable()
            scope = dialog.get_scope()

            self.add_variable(
                name=variable.name,
                var_type=variable.type,
                default_value=variable.default_value,
                scope=scope,
                description=variable.description,
                sensitive=variable.sensitive,
            )

    @Slot()
    def _on_edit_variable(self) -> None:
        """Handle edit button click."""
        current = self._tree.currentItem()
        if not current:
            return

        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "variable":
            return

        self._edit_variable(data.get("name", ""), data.get("scope", ""))

    @Slot()
    def _on_remove_variable(self) -> None:
        """Handle remove variable button click."""
        current = self._tree.currentItem()
        if not current:
            return

        data = current.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("type") != "variable":
            return

        self.remove_variable(data.get("name", ""), data.get("scope", ""))

    @Slot()
    def _on_clear_all(self) -> None:
        """Handle clear all button click (v2 styling)."""
        if self._is_runtime_mode:
            return

        # Confirm dialog with v2 styling
        t = THEME_V2
        tok = TOKENS_V2
        msg = QMessageBox(self)
        msg.setWindowTitle("Clear All Variables")
        msg.setText("Are you sure you want to delete all variables?")
        msg.setInformativeText("This action cannot be undone.")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(f"""
            QMessageBox {{ background: {t.bg_surface}; }}
            QMessageBox QLabel {{ color: {t.text_primary}; }}
            QPushButton {{
                background: {t.bg_hover};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                padding: 4px 12px;
                color: {t.text_primary};
                min-width: 80px;
                min-height: {tok.sizes.button_md}px;
            }}
            QPushButton:hover {{ background: {t.bg_component}; }}
        """)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            self.clear_variables()

    @Slot(str)
    def _on_scope_filter_changed(self, scope: str) -> None:
        """
        Handle scope filter dropdown change.

        Args:
            scope: Selected scope filter
        """
        self._current_scope_filter = scope
        self._apply_scope_filter()
        logger.debug(f"Scope filter changed to: {scope}")

    def _apply_scope_filter(self) -> None:
        """Apply current scope filter to tree items."""
        scope_filter = self._current_scope_filter

        for scope, scope_item in self._scope_items.items():
            # Show/hide scope groups based on filter
            if scope_filter == "All":
                # Show scope if it has variables
                has_vars = scope_item.childCount() > 0
                scope_item.setHidden(not has_vars)
            else:
                # Only show matching scope
                scope_item.setHidden(scope != scope_filter)

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
        scope = event.get("scope", "Scenario")

        # Check if variable already exists in any scope
        exists = any(name in vars for vars in self._variables.values())
        if not exists:
            self.add_variable(name, var_type, value, scope)

    def _on_variable_updated_event(self, event: Event) -> None:
        """
        Handle variable updated event from execution.

        Args:
            event: Event with name, value data
        """
        name = event.get("name", "")
        value = event.get("value")

        if name:
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
        """Handle execution started event."""
        self.set_runtime_mode(True)

    def _on_execution_completed(self, event: Event) -> None:
        """Handle execution completed event."""
        self.set_runtime_mode(False)
