"""
Quick Node Configuration Dialog.

Allows users to assign/remove hotkeys for any node in the system.

Epic 7.x migration: Converted to use BaseDialogV2, THEME_V2/TOKENS_V2, and prompts_v2.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2
from casare_rpa.presentation.canvas.ui.dialogs_v2.prompts_v2 import show_question, show_warning
from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import PushButton

if TYPE_CHECKING:
    from ...components.quick_node_manager import QuickNodeManager


class QuickNodeConfigDialog(BaseDialogV2):
    """
    Dialog for configuring quick node hotkeys.

    Features:
    - View all assigned hotkeys
    - Assign new hotkeys to any node
    - Remove existing hotkeys
    - Search/filter nodes
    """

    def __init__(self, quick_node_manager: QuickNodeManager, parent=None):
        super().__init__(
            title="Quick Node Hotkey Configuration",
            parent=parent,
            size=DialogSizeV2.LG,
            resizable=True,
        )
        self._manager = quick_node_manager
        self._all_nodes: list[tuple[str, str]] = []  # (node_type, display_name)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Header
        header = QLabel(
            "Assign single-key hotkeys to quickly create nodes at cursor position.\n"
            "Press the key while on canvas to instantly create the node."
        )
        header.setWordWrap(True)
        header.setStyleSheet(f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body}px;")
        layout.addWidget(header)

        # Splitter for two tables
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT: Current Bindings ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(TOKENS_V2.spacing.md)

        bindings_group = QGroupBox("Current Hotkeys")
        self._apply_group_style(bindings_group)
        bindings_layout = QVBoxLayout(bindings_group)
        bindings_layout.setSpacing(TOKENS_V2.spacing.sm)

        self._bindings_table = QTableWidget()
        self._bindings_table.setColumnCount(3)
        self._bindings_table.setHorizontalHeaderLabels(["Key", "Node", "Category"])
        self._apply_table_style(self._bindings_table)
        self._bindings_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self._bindings_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._bindings_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self._bindings_table.setColumnWidth(0, 50)
        self._bindings_table.setColumnWidth(2, 100)
        self._bindings_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._bindings_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._bindings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        bindings_layout.addWidget(self._bindings_table)

        # Remove button
        remove_btn = PushButton(text="Remove Selected Hotkey", variant="secondary", size="md")
        remove_btn.clicked.connect(self._on_remove_binding)
        bindings_layout.addWidget(remove_btn)

        left_layout.addWidget(bindings_group)
        splitter.addWidget(left_widget)

        # === RIGHT: All Nodes ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(TOKENS_V2.spacing.md)

        nodes_group = QGroupBox("All Available Nodes")
        self._apply_group_style(nodes_group)
        nodes_layout = QVBoxLayout(nodes_group)
        nodes_layout.setSpacing(TOKENS_V2.spacing.sm)

        # Search box
        search_layout = QFormLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter nodes...")
        self._apply_input_style(self._search_input)
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addRow("Search:", self._search_input)
        nodes_layout.addLayout(search_layout)

        # Nodes table
        self._nodes_table = QTableWidget()
        self._nodes_table.setColumnCount(3)
        self._nodes_table.setHorizontalHeaderLabels(["Node Name", "Type", "Current Key"])
        self._apply_table_style(self._nodes_table)
        self._nodes_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._nodes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._nodes_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._nodes_table.setColumnWidth(1, 180)
        self._nodes_table.setColumnWidth(2, 80)
        self._nodes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._nodes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._nodes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        nodes_layout.addWidget(self._nodes_table)

        # Assign hotkey section
        assign_layout = QHBoxLayout()
        assign_layout.setSpacing(TOKENS_V2.spacing.sm)

        assign_layout.addWidget(QLabel("Assign key:"))
        self._key_combo = QComboBox()
        self._key_combo.setMinimumWidth(60)
        self._apply_combo_style(self._key_combo)
        assign_layout.addWidget(self._key_combo)

        assign_layout.addWidget(QLabel("to selected node"))

        assign_btn = PushButton(text="Assign", variant="primary", size="md")
        assign_btn.clicked.connect(self._on_assign_binding)
        assign_layout.addWidget(assign_btn)

        assign_layout.addStretch()
        nodes_layout.addLayout(assign_layout)

        right_layout.addWidget(nodes_group)
        splitter.addWidget(right_widget)

        # Set splitter sizes
        splitter.setSizes([350, 550])
        layout.addWidget(splitter)

        # Set as body widget
        self.set_body_widget(content)

        # Reset button (added to left side of footer via a separate layout)
        reset_btn = PushButton(text="Reset to Defaults", variant="secondary", size="md")
        reset_btn.clicked.connect(self._on_reset_defaults)

        # Add reset button to body layout above footer
        button_layout = QHBoxLayout()
        button_layout.addWidget(reset_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Setup footer buttons
        self.set_secondary_button("Close", self.accept)

    def _load_data(self) -> None:
        """Load all data into tables."""
        self._load_bindings()
        self._load_all_nodes()
        self._update_available_keys()

    def _load_bindings(self) -> None:
        """Load current bindings into the bindings table."""
        bindings = self._manager.get_bindings()

        self._bindings_table.setRowCount(len(bindings))

        for row, (key, binding) in enumerate(sorted(bindings.items())):
            key_item = QTableWidgetItem(key.upper())
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._bindings_table.setItem(row, 0, key_item)

            name_item = QTableWidgetItem(binding.display_name)
            name_item.setData(Qt.ItemDataRole.UserRole, binding.node_type)
            self._bindings_table.setItem(row, 1, name_item)

            cat_item = QTableWidgetItem(binding.category)
            self._bindings_table.setItem(row, 2, cat_item)

    def _load_all_nodes(self) -> None:
        """Load all available nodes into the nodes table."""
        self._all_nodes = self._manager.get_all_node_types()
        self._populate_nodes_table(self._all_nodes)

    def _populate_nodes_table(self, nodes: list[tuple[str, str]]) -> None:
        """Populate the nodes table with given nodes."""
        bindings = self._manager.get_bindings()

        # Build reverse lookup: node_type -> key
        node_to_key = {}
        for key, binding in bindings.items():
            node_to_key[binding.node_type] = key

        self._nodes_table.setRowCount(len(nodes))

        for row, (node_type, display_name) in enumerate(nodes):
            # Display name
            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.ItemDataRole.UserRole, node_type)
            self._nodes_table.setItem(row, 0, name_item)

            # Node type
            type_item = QTableWidgetItem(node_type)
            self._nodes_table.setItem(row, 1, type_item)

            # Current key (if any)
            current_key = node_to_key.get(node_type, "")
            key_item = QTableWidgetItem(current_key.upper() if current_key else "-")
            key_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._nodes_table.setItem(row, 2, key_item)

    def _update_available_keys(self) -> None:
        """Update the combo box with available keys."""
        self._key_combo.clear()
        available = self._manager.get_available_keys()
        self._key_combo.addItems([k.upper() for k in available])

    @Slot()
    def _on_search_changed(self, text: str) -> None:
        """Filter nodes based on search text."""
        if not text.strip():
            self._populate_nodes_table(self._all_nodes)
            return

        search_lower = text.lower()
        filtered = [
            (node_type, display_name)
            for node_type, display_name in self._all_nodes
            if search_lower in display_name.lower() or search_lower in node_type.lower()
        ]
        self._populate_nodes_table(filtered)

    @Slot()
    def _on_remove_binding(self) -> None:
        """Remove the selected hotkey binding."""
        selected = self._bindings_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        key_item = self._bindings_table.item(row, 0)
        name_item = self._bindings_table.item(row, 1)

        if key_item and name_item:
            key = key_item.text().lower()
            name = name_item.text()

            if show_question(self, "Remove Hotkey", f"Remove hotkey '{key.upper()}' for '{name}'?"):
                self._manager.remove_binding(key)
                self._manager.save_bindings()
                self._load_data()

    @Slot()
    def _on_assign_binding(self) -> None:
        """Assign a hotkey to the selected node."""
        # Get selected node
        selected = self._nodes_table.selectedItems()
        if not selected:
            show_warning(self, "No Selection", "Please select a node to assign a hotkey.")
            return

        row = selected[0].row()
        name_item = self._nodes_table.item(row, 0)
        if not name_item:
            return

        node_type = name_item.data(Qt.ItemDataRole.UserRole)
        display_name = name_item.text()

        # Get selected key
        key = self._key_combo.currentText().lower()
        if not key:
            show_warning(self, "No Key", "Please select a key to assign.")
            return

        # Determine category from node type
        category = self._get_category_for_node(node_type)

        # Assign the binding
        self._manager.set_binding(key, node_type, display_name, category)
        self._manager.save_bindings()
        self._load_data()

    def _get_category_for_node(self, node_type: str) -> str:
        """Determine category based on node type name."""
        node_lower = node_type.lower()

        if "browser" in node_lower or "url" in node_lower or "click" in node_lower:
            return "browser"
        elif "desktop" in node_lower or "window" in node_lower or "application" in node_lower:
            return "desktop"
        elif "variable" in node_lower:
            return "variables"
        elif "loop" in node_lower or "if" in node_lower or "switch" in node_lower:
            return "flow"
        elif "file" in node_lower or "csv" in node_lower or "json" in node_lower:
            return "file"
        elif "database" in node_lower or "query" in node_lower:
            return "database"
        elif "email" in node_lower or "gmail" in node_lower:
            return "email"
        elif "excel" in node_lower or "word" in node_lower:
            return "office"
        else:
            return "other"

    @Slot()
    def _on_reset_defaults(self) -> None:
        """Reset all bindings to defaults."""
        if show_question(
            self,
            "Reset to Defaults",
            "This will remove all custom hotkeys and restore the default bindings.\n\nContinue?"
        ):
            self._manager.reset_to_defaults()
            self._manager.save_bindings()
            self._load_data()

    def _apply_styles(self) -> None:
        """Apply dark theme styles using THEME_V2/TOKENS_V2."""
        t = THEME_V2
        tok = TOKENS_V2

        self.setStyleSheet(f"""
            QuickNodeConfigDialog {{
                background-color: {t.bg_surface};
            }}
            QLabel {{
                color: {t.text_primary};
                font-family: {tok.typography.family};
            }}
            QSplitter::handle {{
                background: {t.border};
            }}
        """)

    def _apply_input_style(self, widget: QLineEdit) -> None:
        """Apply v2 input styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QLineEdit {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                min-height: {tok.sizes.input_md}px;
            }}
            QLineEdit:focus {{
                border-color: {t.border_focus};
            }}
        """)

    def _apply_combo_style(self, widget: QComboBox) -> None:
        """Apply v2 combo box styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QComboBox {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                min-height: {tok.sizes.input_md}px;
            }}
            QComboBox:focus {{
                border-color: {t.border_focus};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {t.bg_elevated};
                border: 1px solid {t.border};
                selection-background-color: {t.bg_selected};
                color: {t.text_primary};
            }}
        """)

    def _apply_table_style(self, widget: QTableWidget) -> None:
        """Apply v2 table styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QTableWidget {{
                background: {t.bg_component};
                border: 1px solid {t.border};
                gridline-color: {t.border};
                color: {t.text_primary};
                font-family: {tok.typography.family};
                font-size: {tok.typography.body}px;
            }}
            QTableWidget::item {{
                padding: {tok.spacing.xs}px;
            }}
            QTableWidget::item:selected {{
                background: {t.bg_selected};
                color: {t.text_primary};
            }}
            QHeaderView::section {{
                background: {t.bg_elevated};
                color: {t.text_primary};
                padding: {tok.spacing.xs}px;
                border: none;
                border-right: 1px solid {t.border};
                border-bottom: 1px solid {t.border};
                font-weight: {tok.typography.weight_medium};
            }}
        """)

    def _apply_group_style(self, widget: QGroupBox) -> None:
        """Apply v2 group box styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {tok.typography.weight_medium};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                border: 1px solid {t.border};
                border-radius: {tok.radius.sm}px;
                margin-top: {tok.spacing.xs}px;
                padding-top: {tok.spacing.xs}px;
                background: {t.bg_surface};
                color: {t.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tok.spacing.sm}px;
                padding: 0 {tok.spacing.xs}px;
                color: {t.text_primary};
            }}
        """)
