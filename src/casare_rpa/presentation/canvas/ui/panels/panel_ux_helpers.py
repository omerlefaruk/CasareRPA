"""
Panel UX Helpers for CasareRPA Bottom Panel.

Provides reusable UI components for consistent UX across all panels:
- Empty state widgets with icons and guidance
- Status badge labels
- Styled toolbar buttons
- Context menu builders
- Quick variable creation row

Epic 6.1: Migrated to v2 design system (THEME_V2, TOKENS_V2).
"""

from collections.abc import Callable
from functools import partial
from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QAction, QBrush, QColor, QCursor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.helpers import (
    set_fixed_width,
    set_margins,
    set_min_width,
    set_spacing,
)


def configure_panel_toolbar(toolbar_widget: QWidget, toolbar_layout: Any) -> None:
    """
    Standardize panel toolbars (the header strip that holds controls).

    This keeps the "button bar" consistent across bottom/side/left/right panels:
    same height, padding, spacing, and background via the `panelToolbar` property.
    """
    toolbar_widget.setProperty("panelToolbar", True)
    # Avoid fixed heights; let the toolbar size to its contents (terminal-like).
    toolbar_widget.setMinimumHeight(TOKENS_V2.sizes.input_lg)
    # Compact, consistent padding around controls.
    toolbar_layout.setContentsMargins(
        TOKENS_V2.spacing.xs,
        TOKENS_V2.spacing.xxs,
        TOKENS_V2.spacing.xs,
        TOKENS_V2.spacing.xxs,
    )
    toolbar_layout.setSpacing(TOKENS_V2.spacing.xxs)

# Variable types for quick creation
QUICK_VAR_TYPES = ["String", "Integer", "Float", "Boolean", "List", "Dict"]

# Type badges for compact display
TYPE_BADGES = {
    "String": "T",
    "Integer": "#",
    "Float": ".",
    "Boolean": "?",
    "List": "[]",
    "Dict": "{}",
}

# TYPE_COLORS: VSCode Dark+ syntax highlighting colors for data type visualization
# Uses THEME_V2.wire_* tokens for type coloring (v2 design system)
TYPE_COLORS = {
    "String": THEME_V2.wire_string,
    "Integer": THEME_V2.wire_number,
    "Float": THEME_V2.wire_number,
    "Boolean": THEME_V2.wire_bool,
    "List": THEME_V2.wire_list,
    "Dict": THEME_V2.wire_dict,
}

# Default values for each type
TYPE_DEFAULTS: dict[str, Any] = {
    "String": "",
    "Integer": 0,
    "Float": 0.0,
    "Boolean": False,
    "List": [],
    "Dict": {},
}


class VariablesTableWidget(QWidget):
    """
    UiPath-style flat table for variable management.

    Features:
    - Flat table (not tree) with columns: Name, Type, Scope, Default
    - "Create Variable" row at top with distinct styling (click to add)
    - Inline editing - click cell and type
    - Tab to navigate between fields
    - Enter commits, Escape cancels

    Signals:
        variable_created: Emitted when variable created (name, type, scope, default)
        variable_changed: Emitted when variable changed (name, type, scope, default)
        variable_deleted: Emitted when variable deleted (name)
    """

    COL_NAME = 0
    COL_TYPE = 1
    COL_SCOPE = 2
    COL_DEFAULT = 3

    variable_created = Signal(str, str, str, object)
    variable_changed = Signal(str, str, str, object)
    variable_deleted = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the variables table."""
        super().__init__(parent)

        self._variables: dict[str, dict[str, Any]] = {}
        self._is_editing_create_row = False
        self._create_row_data = {"name": "", "type": "String", "scope": "Scenario", "default": ""}

        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QVBoxLayout(self)
        set_margins(layout, (0, 0, 0, 0))
        set_spacing(layout, 0)

        # Table widget
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Name", "Type", "Scope", "Default"])

        # Configure table
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(True)

        # Configure columns
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Connect signals
        self._table.itemClicked.connect(self._on_item_clicked)
        self._table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._on_context_menu)

        layout.addWidget(self._table)

        # Initial setup - add create row
        self._refresh_table()

    def _apply_styles(self) -> None:
        """Apply v2 table styling (shared with other bottom-panel tabs)."""
        self._table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {THEME_V2.bg_surface};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                gridline-color: {THEME_V2.border_dark};
                outline: none;
            }}
            QTableWidget::item {{
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.xs}px;
                color: {THEME_V2.text_primary};
                border: none;
                border-bottom: 1px solid {THEME_V2.border_dark};
            }}
            QTableWidget::item:selected {{
                background-color: {THEME_V2.bg_selected};
                color: {THEME_V2.text_primary};
            }}
            QTableWidget::item:hover {{
                background-color: {THEME_V2.bg_hover};
            }}
            """
        )
        self._table.horizontalHeader().setStyleSheet(
            f"""
            QHeaderView {{
                background-color: {THEME_V2.bg_header};
                color: {THEME_V2.text_secondary};
                border: none;
                border-bottom: 1px solid {THEME_V2.border};
                padding: 0;
                margin: 0;
            }}
            QHeaderView::section {{
                background-color: {THEME_V2.bg_header};
                color: {THEME_V2.text_secondary};
                min-height: {TOKENS_V2.sizes.input_lg}px;
                max-height: {TOKENS_V2.sizes.input_lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
                border: none;
                border-right: 1px solid {THEME_V2.border_dark};
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body_sm}px;
                text-transform: uppercase;
            }}
            QHeaderView::section:hover {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_primary};
            }}
            """
        )
        self.setStyleSheet(
            f"VariablesTableWidget {{ background-color: {THEME_V2.bg_surface}; }}"
        )

    def _refresh_table(self) -> None:
        """Refresh the table with current variables."""
        self._table.setRowCount(0)

        # Add create row at top (index 0)
        create_row = self._table.rowCount()
        self._table.insertRow(create_row)

        for col in range(4):
            item = QTableWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, {"is_create_row": True})

            if col == self.COL_NAME:
                item.setText("Click to add variable...")
                item.setForeground(QBrush(QColor(THEME_V2.text_muted)))
            elif col == self.COL_TYPE:
                item.setText("String")
            elif col == self.COL_SCOPE:
                item.setText("Scenario")
            elif col == self.COL_DEFAULT:
                item.setText("")

            self._table.setItem(create_row, col, item)

        # Add variable rows
        for name, var_data in self._variables.items():
            self._add_variable_row(name, var_data)

    def _add_variable_row(self, name: str, var_data: dict[str, Any]) -> None:
        """Add a variable row to the table."""
        row = self._table.rowCount()
        self._table.insertRow(row)

        # Name
        name_item = QTableWidgetItem(name)
        name_item.setForeground(QBrush(QColor(THEME_V2.primary)))
        self._table.setItem(row, self.COL_NAME, name_item)

        # Type
        var_type = var_data.get("type", "String")
        type_item = QTableWidgetItem(var_type)
        type_color = THEME_V2.text_muted
        type_item.setForeground(QBrush(QColor(type_color)))
        self._table.setItem(row, self.COL_TYPE, type_item)

        # Scope
        scope = var_data.get("scope", "Scenario")
        scope_item = QTableWidgetItem(scope)
        self._table.setItem(row, self.COL_SCOPE, scope_item)

        # Default
        default_val = var_data.get("default", "")
        default_str = self._format_default(default_val)
        default_item = QTableWidgetItem(default_str)
        default_item.setData(Qt.ItemDataRole.UserRole, default_val)
        self._table.setItem(row, self.COL_DEFAULT, default_item)

    def _format_default(self, value: Any) -> str:
        """Format default value for display."""
        if value is None:
            return ""
        if isinstance(value, bool):
            return "True" if value else "False"
        if isinstance(value, list):
            return f"[{len(value)} items]"
        if isinstance(value, dict):
            return f"{{{len(value)} keys}}"
        return str(value)

    @Slot(QTableWidgetItem)
    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        """Handle item click - check if create row."""
        row = item.row()
        if row == 0:  # Create row
            self._start_create_variable(item.column())

    @Slot(QTableWidgetItem)
    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """Handle double-click - same as click for create row."""
        self._on_item_clicked(item)

    def _start_create_variable(self, focus_column: int = 0) -> None:
        """Start creating a new variable with inline editor."""
        if self._is_editing_create_row:
            return

        self._is_editing_create_row = True
        row = 0  # Create row is always at top

        # Create inline editor for name
        self._create_editor = QLineEdit()
        self._create_editor.setPlaceholderText("variable name...")
        self._create_editor.setStyleSheet(f"""
            QLineEdit {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
                border: 2px solid {THEME_V2.border_focus};
                border-radius: {TOKENS_V2.radius.sm}px;  /* 4px */
                padding: {TOKENS_V2.spacing.sm}px;
                font-family: {TOKENS_V2.typography.ui};
            }}
        """)
        self._create_editor.setText(self._create_row_data["name"])

        # Connect signals
        self._create_editor.editingFinished.connect(self._on_create_editor_finished)
        self._create_editor.returnPressed.connect(self._on_create_editor_commit)

        # Position and show editor
        rect = self._table.visualItemRect(self._table.item(row, focus_column))
        self._create_editor.setParent(self._table.viewport())
        self._create_editor.setGeometry(rect)
        self._create_editor.show()
        self._create_editor.setFocus()

    @Slot()
    def _on_create_editor_finished(self) -> None:
        """Handle create editor finished."""
        if hasattr(self, "_create_editor"):
            self._create_editor.deleteLater()
            del self._create_editor
        self._is_editing_create_row = False

    @Slot()
    def _on_create_editor_commit(self) -> None:
        """Commit the new variable."""
        if not hasattr(self, "_create_editor"):
            return

        name = self._create_editor.text().strip()
        if not name or not self._is_valid_name(name):
            self._create_editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {THEME_V2.bg_surface};
                    color: {THEME_V2.text_primary};
                    border: 2px solid {THEME_V2.error};
                    border-radius: {TOKENS_V2.radius.sm}px;  /* 4px */
                    padding: {TOKENS_V2.spacing.sm}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
            """)
            return

        # Check for duplicate
        if name in self._variables:
            self._create_editor.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {THEME_V2.bg_surface};
                    color: {THEME_V2.text_primary};
                    border: 2px solid {THEME_V2.error};
                    border-radius: {TOKENS_V2.radius.sm}px;  /* 4px */
                    padding: {TOKENS_V2.spacing.sm}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
            """)
            return

        # Create variable with defaults
        var_type = self._create_row_data["type"]
        scope = self._create_row_data["scope"]
        default = TYPE_DEFAULTS.get(var_type, "")

        self.variable_created.emit(name, var_type, scope, default)

        # Reset and close editor
        self._create_row_data = {"name": "", "type": "String", "scope": "Scenario", "default": ""}
        self._on_create_editor_finished()

    def _is_valid_name(self, name: str) -> bool:
        """Check if variable name is valid."""
        import re

        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    @Slot(object)
    def _on_context_menu(self, pos) -> None:
        """Show context menu."""
        item = self._table.itemAt(pos)
        if not item or item.row() == 0:  # No menu for create row
            return

        row = item.row()
        name_item = self._table.item(row, self.COL_NAME)
        name = name_item.text() if name_item else ""

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.sm}px;
            }}
            QMenu::item {{
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.xl}px {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                border-radius: {TOKENS_V2.radius.sm}px;  /* 4px */
                font-family: {TOKENS_V2.typography.ui};
            }}
            QMenu::item:selected {{
                background-color: {THEME_V2.primary};
                color: {THEME_V2.text_primary};
            }}
        """)

        delete_action = menu.addAction("Delete")
        delete_action.triggered.connect(partial(self.variable_deleted.emit, name))

        menu.exec_(self._table.mapToGlobal(pos))

    def add_variable(self, name: str, var_type: str, scope: str, default: Any) -> None:
        """Add a variable to the table."""
        self._variables[name] = {
            "type": var_type,
            "scope": scope,
            "default": default,
        }
        self._refresh_table()

    def remove_variable(self, name: str) -> None:
        """Remove a variable from the table."""
        if name in self._variables:
            del self._variables[name]
            self._refresh_table()

    def set_variables(self, variables: dict[str, dict[str, Any]]) -> None:
        """Set all variables."""
        self._variables = variables.copy()
        self._refresh_table()

    def get_variables(self) -> dict[str, dict[str, Any]]:
        """Get all variables."""
        return self._variables.copy()


class EmptyStateWidget(QWidget):
    """
    Empty state display for panels with no data.

    Shows an icon, title, description, and optional action button.
    Uses muted styling to indicate placeholder content.
    """

    action_clicked = Signal()

    def __init__(
        self,
        icon_text: str = "",
        title: str = "No data",
        description: str = "",
        action_text: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize empty state widget.

        Args:
            icon_text: Unicode icon or emoji to display (e.g., folder icon)
            title: Main title text
            description: Detailed description/guidance
            action_text: Optional button text (shows button if provided)
            parent: Parent widget
        """
        super().__init__(parent)

        self._setup_ui(icon_text, title, description, action_text)
        self._apply_styles()

    def _setup_ui(
        self,
        icon_text: str,
        title: str,
        description: str,
        action_text: str,
    ) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        set_margins(layout, TOKENS_V2.margin.comfortable)
        set_spacing(layout, TOKENS_V2.spacing.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon (large, muted)
        if icon_text:
            icon_label = QLabel(icon_text)
            icon_label.setObjectName("emptyStateIcon")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        # Title
        title_label = QLabel(title)
        title_label.setObjectName("emptyStateTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Description
        if description:
            desc_label = QLabel(description)
            desc_label.setObjectName("emptyStateDescription")
            desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

        # Action button
        if action_text:
            action_btn = QPushButton(action_text)
            action_btn.setObjectName("emptyStateAction")
            action_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            action_btn.clicked.connect(self.action_clicked.emit)

            # Center the button
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(action_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)

    def _apply_styles(self) -> None:
        """Apply empty state styling."""
        self.setStyleSheet(f"""
            EmptyStateWidget {{
                background-color: {THEME_V2.bg_surface};
            }}
            QLabel {{
                background: transparent;
                font-family: {TOKENS_V2.typography.ui};
            }}
            #emptyStateIcon {{
                font-size: 64px;
                color: {THEME_V2.text_disabled};
            }}
            #emptyStateTitle {{
                font-size: {TOKENS_V2.typography.display_md}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                color: {THEME_V2.text_secondary};
            }}
            #emptyStateDescription {{
                font-size: {TOKENS_V2.typography.body}px;
                color: {THEME_V2.text_muted};
                line-height: 1.4;
            }}
            #emptyStateAction {{
                background-color: {THEME_V2.primary};
                color: {THEME_V2.text_primary};
                border: none;
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.md}px {TOKENS_V2.spacing.xl}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
            }}
            #emptyStateAction:hover {{
                background-color: {THEME_V2.primary_hover};
            }}
        """)


class StatusBadge(QLabel):
    """
    Status badge label with color-coded backgrounds.

    Used to display status indicators like SUCCESS, ERROR, WARNING.
    """

    def __init__(
        self,
        text: str = "",
        status: str = "info",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize status badge.

        Args:
            text: Badge text
            status: Status type (success, error, warning, info, idle)
            parent: Parent widget
        """
        super().__init__(text, parent)
        self.set_status(status)
        self._apply_base_styles()

    def _apply_base_styles(self) -> None:
        """Apply base badge styling."""
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        set_min_width(self, 60)

    def set_status(self, status: str, text: str | None = None) -> None:
        """
        Set badge status and optionally update text.

        Args:
            status: Status type (success, error, warning, info, idle, running)
            text: Optional new text
        """
        if text is not None:
            self.setText(text)

        # Color mappings: (fg_color, bg_color) - None bg means no badge styling
        colors = {
            "success": (THEME_V2.success, f"{THEME_V2.success}20"),
            "error": (THEME_V2.error, f"{THEME_V2.error}20"),
            "warning": (THEME_V2.warning, f"{THEME_V2.warning}20"),
            "info": (THEME_V2.info, f"{THEME_V2.info}20"),
            "idle": (THEME_V2.text_muted, None),  # No badge, just plain text
            "running": (THEME_V2.warning, f"{THEME_V2.warning}20"),
        }

        fg_color, bg_color = colors.get(status.lower(), colors["info"])

        if bg_color is None:
            # Idle: plain text, no background at all
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            self.setStyleSheet(f"""
                QLabel {{
                    background: none;
                    border: none;
                    color: {fg_color};
                    font-size: {TOKENS_V2.typography.caption}px;
                    font-weight: {TOKENS_V2.typography.weight_semibold};
                    text-transform: uppercase;
                    font-family: {TOKENS_V2.typography.ui};
                }}
            """)
        else:
            # Active states: badge with colored background
            self.setAutoFillBackground(False)
            self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg_color};
                    color: {fg_color};
                    padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                    border-radius: {TOKENS_V2.radius.sm}px;  /* 4px */
                    font-size: {TOKENS_V2.typography.caption}px;
                    font-weight: {TOKENS_V2.typography.weight_semibold};
                    text-transform: uppercase;
                    font-family: {TOKENS_V2.typography.ui};
                }}
            """)


class ToolbarButton(QPushButton):
    """
    Styled toolbar button with icon and optional text.

    Provides consistent hover and pressed states.
    """

    def __init__(
        self,
        text: str = "",
        icon_text: str = "",
        tooltip: str = "",
        primary: bool = False,
        danger: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize toolbar button.

        Args:
            text: Button text
            icon_text: Unicode icon (prepended to text)
            tooltip: Tooltip text
            primary: Use primary accent color
            danger: Use danger/error color
            parent: Parent widget
        """
        display_text = f"{icon_text} {text}".strip() if icon_text else text
        super().__init__(display_text, parent)

        if tooltip:
            self.setToolTip(tooltip)

        self._apply_styles(primary, danger)

    def _apply_styles(self, primary: bool, danger: bool) -> None:
        """Apply ElevenLabs-style button styling."""
        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME_V2.primary};
                    color: {THEME_V2.text_primary};
                    border: none;
                    border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                    padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                    font-weight: {TOKENS_V2.typography.weight_medium};
                    font-size: {TOKENS_V2.typography.body}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
                QPushButton:hover {{
                    background-color: {THEME_V2.primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {THEME_V2.primary};
                }}
                QPushButton:disabled {{
                    background-color: {THEME_V2.bg_hover};
                    color: {THEME_V2.text_disabled};
                }}
            """)
        elif danger:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME_V2.bg_hover};
                    color: {THEME_V2.error};
                    border: 1px solid {THEME_V2.error};
                    border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                    padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                    font-weight: {TOKENS_V2.typography.weight_medium};
                    font-size: {TOKENS_V2.typography.body}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
                QPushButton:hover {{
                    background-color: {THEME_V2.error};
                    color: {THEME_V2.text_primary};
                }}
                QPushButton:pressed {{
                    background-color: {THEME_V2.error};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {THEME_V2.bg_hover};
                    color: {THEME_V2.text_secondary};
                    border: 1px solid {THEME_V2.border};
                    border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                    padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                    font-size: {TOKENS_V2.typography.body}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
                QPushButton:hover {{
                    background-color: {THEME_V2.bg_hover};
                    color: {THEME_V2.text_primary};
                    border-color: {THEME_V2.border_light};
                }}
                QPushButton:pressed {{
                    background-color: {THEME_V2.bg_hover};
                }}
                QPushButton:disabled {{
                    background-color: {THEME_V2.bg_component};
                    color: {THEME_V2.text_disabled};
                    border-color: {THEME_V2.border_dark};
                }}
            """)


class SectionHeader(QFrame):
    """
    Section header with title and optional count badge.

    Used to separate sections within panels.
    """

    def __init__(
        self,
        title: str,
        count: int | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize section header.

        Args:
            title: Section title
            count: Optional count to display as badge
            parent: Parent widget
        """
        super().__init__(parent)

        self._title_label: QLabel
        self._count_label: QLabel | None = None

        self._setup_ui(title, count)
        self._apply_styles()

    def _setup_ui(self, title: str, count: int | None) -> None:
        """Set up the UI."""
        layout = QHBoxLayout(self)
        set_margins(layout, (8, 6, 8, 6))
        set_spacing(layout, TOKENS_V2.spacing.md)

        self._title_label = QLabel(title.upper())
        self._title_label.setObjectName("sectionTitle")
        layout.addWidget(self._title_label)

        if count is not None:
            self._count_label = QLabel(str(count))
            self._count_label.setObjectName("sectionCount")
            layout.addWidget(self._count_label)

        layout.addStretch()

    def _apply_styles(self) -> None:
        """Apply section header styling."""
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME_V2.bg_header};
                border-bottom: 1px solid {THEME_V2.border_dark};
            }}
            #sectionTitle {{
                color: {THEME_V2.text_header};
                font-size: {TOKENS_V2.typography.caption}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                letter-spacing: 0.5px;
                font-family: {TOKENS_V2.typography.ui};
            }}
            #sectionCount {{
                background-color: {THEME_V2.bg_hover};
                color: {THEME_V2.text_muted};
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                font-size: {TOKENS_V2.typography.caption}px;
                font-family: {TOKENS_V2.typography.ui};
            }}
        """)

    def set_count(self, count: int) -> None:
        """Update the count badge."""
        if self._count_label:
            self._count_label.setText(str(count))


class QuickVariableRow(QWidget):
    """
    Inline variable creation row for quick variable addition.

    Features:
    - Click-to-edit name field with placeholder
    - Type selector dropdown
    - Scope toggle buttons (Global/Project/Scenario)
    - Enter to commit, Escape to cancel
    - Visual validation feedback

    Signals:
        variable_created: Emitted when a variable is created (name, type, scope)
        cancelled: Emitted when editing is cancelled (Escape key)
    """

    variable_created = Signal(str, str, str)  # name, type, scope
    cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize quick variable row."""
        super().__init__(parent)

        self._current_scope = "Scenario"
        self._is_editing = False

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Set up the UI."""
        layout = QHBoxLayout(self)
        set_margins(layout, (8, 6, 8, 6))
        set_spacing(layout, TOKENS_V2.spacing.md)

        # Name input (placeholder text when not editing)
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("Click to add variable...")
        self._name_input.setObjectName("quickVarName")
        layout.addWidget(self._name_input, 2)

        # Type selector
        self._type_combo = QComboBox()
        self._type_combo.addItems(QUICK_VAR_TYPES)
        self._type_combo.setCurrentText("String")
        self._type_combo.setObjectName("quickVarType")
        set_fixed_width(self._type_combo, TOKENS_V2.sizes.combo_width_md)
        layout.addWidget(self._type_combo)

        # Scope toggle buttons
        self._scope_container = QWidget()
        scope_layout = QHBoxLayout(self._scope_container)
        set_margins(scope_layout, (0, 0, 0, 0))
        set_spacing(scope_layout, TOKENS_V2.spacing.sm)

        self._scope_buttons: dict[str, QPushButton] = {}
        for scope in ["Global", "Project", "Scenario"]:
            btn = QPushButton(scope)
            btn.setObjectName(f"scopeBtn_{scope}")
            btn.setCheckable(True)
            set_fixed_width(btn, TOKENS_V2.sizes.button_min_width)
            if scope == self._current_scope:
                btn.setChecked(True)
            self._scope_buttons[scope] = btn
            scope_layout.addWidget(btn)

        layout.addWidget(self._scope_container)

        # Add button
        self._add_btn = QPushButton("Add")
        self._add_btn.setObjectName("quickVarAdd")
        self._add_btn.setEnabled(False)  # Disabled until name is valid
        set_fixed_width(self._add_btn, TOKENS_V2.sizes.button_width_sm)
        layout.addWidget(self._add_btn)

    def _apply_styles(self) -> None:
        """Apply ElevenLabs-style quick variable row styling."""
        self.setStyleSheet(f"""
            QuickVariableRow {{
                background-color: {THEME_V2.bg_hover};
                border-bottom: 1px solid {THEME_V2.border};
            }}
            QLineEdit#quickVarName {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.ui};
            }}
            QLineEdit#quickVarName:focus {{
                border-color: {THEME_V2.border_focus};
            }}
            QComboBox#quickVarType {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.sm}px;
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.ui};
            }}
            QPushButton[objectName^="scopeBtn_"] {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_muted};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.sm}px;
                font-size: {TOKENS_V2.typography.caption}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                text-transform: uppercase;
                font-family: {TOKENS_V2.typography.ui};
            }}
            QPushButton[objectName^="scopeBtn_"]:checked {{
                background-color: {THEME_V2.primary};
                color: {THEME_V2.text_primary};
                border-color: {THEME_V2.primary};
            }}
            QPushButton[objectName^="scopeBtn_"]:hover {{
                border-color: {THEME_V2.border_light};
            }}
            QPushButton#quickVarAdd {{
                background-color: {THEME_V2.primary};
                color: {THEME_V2.text_primary};
                border: none;
                border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.ui};
            }}
            QPushButton#quickVarAdd:hover {{
                background-color: {THEME_V2.primary_hover};
            }}
            QPushButton#quickVarAdd:disabled {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_disabled};
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._name_input.textChanged.connect(self._on_name_changed)
        self._name_input.returnPressed.connect(self._on_commit)
        self._add_btn.clicked.connect(self._on_commit)

        for scope, btn in self._scope_buttons.items():
            btn.clicked.connect(partial(self._on_scope_changed, scope))

    @Slot(str)
    def _on_name_changed(self, text: str) -> None:
        """Handle name text change - validate and enable/disable add button."""
        is_valid = self._is_valid_name(text)
        self._add_btn.setEnabled(is_valid)

        # Visual feedback
        if text and not is_valid:
            self._name_input.setStyleSheet(f"""
                QLineEdit#quickVarName {{
                    background-color: {THEME_V2.bg_surface};
                    color: {THEME_V2.text_primary};
                    border: 1px solid {THEME_V2.error};
                    border-radius: {TOKENS_V2.radius.md}px;  /* 8px */
                    padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
                    font-size: {TOKENS_V2.typography.body}px;
                    font-family: {TOKENS_V2.typography.ui};
                }}
            """)
        else:
            # Reset to default style
            self._apply_styles()

    @Slot(str)
    def _on_scope_changed(self, scope: str) -> None:
        """Handle scope button click."""
        self._current_scope = scope
        for s, btn in self._scope_buttons.items():
            btn.setChecked(s == scope)

    def _is_valid_name(self, name: str) -> bool:
        """Check if variable name is valid."""
        if not name or not name.strip():
            return False

        import re

        name = name.strip()
        # Must be valid Python identifier
        return bool(re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name))

    @Slot()
    def _on_commit(self) -> None:
        """Commit variable creation."""
        name = self._name_input.text().strip()
        if not self._is_valid_name(name):
            return

        var_type = self._type_combo.currentText()
        scope = self._current_scope

        self.variable_created.emit(name, var_type, scope)
        self.clear()

    def clear(self) -> None:
        """Clear input for next variable."""
        self._name_input.clear()
        self._type_combo.setCurrentText("String")
        self._add_btn.setEnabled(False)
        self._apply_styles()

    def keyPressEvent(self, event) -> None:
        """Handle key press - Escape cancels."""
        super().keyPressEvent(event)
        if event.key() == Qt.Key.Key_Escape:
            self.clear()
            self.cancelled.emit()


def create_context_menu(
    actions: list[tuple[str, str, Callable]],
    parent: QWidget | None = None,
) -> QMenu:
    """
    Create a styled context menu with VS Code/Cursor design.

    Args:
        actions: List of (icon_text, label, callback) tuples.
                 Use "-" as label for separator.
        parent: Parent widget

    Returns:
        Configured QMenu
    """
    menu = QMenu(parent)
    menu.setStyleSheet(f"""
        QMenu {{
            background-color: {THEME_V2.bg_hover};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.md}px;
            padding: {TOKENS_V2.spacing.sm}px;
        }}
        QMenu::item {{
            padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.xl}px {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
            border-radius: {TOKENS_V2.radius.sm}px;
        }}
        QMenu::item:selected {{
            background-color: {THEME_V2.primary};
            color: {THEME_V2.text_primary};
        }}
    """)

    for icon_text, label, callback in actions:
        if label == "-":
            menu.addSeparator()
        else:
            text = f"{icon_text} {label}" if icon_text else label
            action = QAction(text, menu)
            action.triggered.connect(callback)
            menu.addAction(action)

    return menu


def get_panel_table_stylesheet() -> str:
    """
    Get consistent table stylesheet for all panels with ElevenLabs design tokens.

    Returns:
        QSS stylesheet string
    """
    return f"""
        QTableWidget, QTreeWidget {{
            background-color: {THEME_V2.bg_surface};
            alternate-background-color: {THEME_V2.bg_surface};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border_dark};
            gridline-color: {THEME_V2.border_dark};
            selection-background-color: {THEME_V2.bg_selected};
            selection-color: {THEME_V2.text_primary};
            outline: none;
            font-family: {TOKENS_V2.typography.ui};
            font-size: {TOKENS_V2.typography.body}px;
        }}
        QTableWidget::item, QTreeWidget::item {{
            padding: {TOKENS_V2.spacing.sm}px {TOKENS_V2.spacing.md}px;
            border-bottom: 1px solid {THEME_V2.border_dark};
        }}
        QTableWidget::item:selected, QTreeWidget::item:selected {{
            background-color: {THEME_V2.bg_selected};
        }}
        QTableWidget::item:hover, QTreeWidget::item:hover {{
            background-color: {THEME_V2.bg_hover};
        }}
        QTableWidget::item:focus, QTreeWidget::item:focus {{
            outline: 1px solid {THEME_V2.border_focus};
            outline-offset: -1px;
        }}
        QHeaderView {{
            background-color: {THEME_V2.bg_header};
        }}
        QHeaderView::section {{
            background-color: {THEME_V2.bg_header};
            color: {THEME_V2.text_header};
            padding: {TOKENS_V2.spacing.md}px {TOKENS_V2.spacing.md}px;
            border: none;
            border-right: 1px solid {THEME_V2.border_dark};
            border-bottom: 1px solid {THEME_V2.border_dark};
            font-weight: {TOKENS_V2.typography.weight_semibold};
            font-size: {TOKENS_V2.typography.caption}px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-family: {TOKENS_V2.typography.ui};
        }}
        QHeaderView::section:last {{
            border-right: none;
        }}
        QHeaderView::section:hover {{
            background-color: {THEME_V2.bg_hover};
            color: {THEME_V2.text_primary};
        }}
        QHeaderView::section:pressed {{
            background-color: {THEME_V2.bg_hover};
        }}
    """


def get_panel_toolbar_stylesheet() -> str:
    """
    Get consistent toolbar stylesheet for all panels with ElevenLabs design tokens.

    Returns:
        QSS stylesheet string
    """
    return f"""
        QLabel {{
            background: transparent;
            color: {THEME_V2.text_secondary};
            font-size: {TOKENS_V2.typography.body_sm}px;
            font-family: {TOKENS_V2.typography.ui};
        }}
        QLabel[muted="true"] {{
            color: {THEME_V2.text_muted};
        }}
        QComboBox {{
            background-color: {THEME_V2.input_bg};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {TOKENS_V2.spacing.xxs}px {TOKENS_V2.spacing.xs}px;
            min-width: {TOKENS_V2.sizes.input_min_width}px;
            min-height: {TOKENS_V2.sizes.input_sm}px;
            font-size: {TOKENS_V2.typography.body_sm}px;
            font-family: {TOKENS_V2.typography.ui};
        }}
        QComboBox:hover {{
            border-color: {THEME_V2.border_light};
        }}
        QComboBox:focus {{
            border-color: {THEME_V2.border_focus};
        }}
        QComboBox::drop-down {{
            border: none;
            width: {TOKENS_V2.sizes.checkbox_size}px;
        }}
        QComboBox::down-arrow {{
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {THEME_V2.text_secondary};
        }}
        QComboBox QAbstractItemView {{
            background-color: {THEME_V2.bg_hover};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            selection-background-color: {THEME_V2.primary};
            outline: none;
            font-family: {TOKENS_V2.typography.ui};
        }}
    """
