"""
Quick Node Configuration Dialog.

Allows users to assign/remove hotkeys for any node in the system.
"""

from typing import TYPE_CHECKING, List, Tuple
from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLineEdit,
    QLabel,
    QMessageBox,
    QComboBox,
    QGroupBox,
    QSplitter,
    QWidget,
    QAbstractItemView,
)
from PySide6.QtCore import Qt

from PySide6.QtWidgets import QDialog

if TYPE_CHECKING:
    from ...components.quick_node_manager import QuickNodeManager


class QuickNodeConfigDialog(QDialog):
    """
    Dialog for configuring quick node hotkeys.

    Features:
    - View all assigned hotkeys
    - Assign new hotkeys to any node
    - Remove existing hotkeys
    - Search/filter nodes
    """

    def __init__(self, quick_node_manager: "QuickNodeManager", parent=None):
        super().__init__(parent)
        self._manager = quick_node_manager
        self._all_nodes: List[Tuple[str, str]] = []  # (node_type, display_name)

        self.setWindowTitle("Quick Node Hotkey Configuration")
        self.setMinimumSize(900, 600)
        self.setModal(True)

        self._setup_ui()
        self._load_data()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel(
            "Assign single-key hotkeys to quickly create nodes at cursor position.\n"
            "Press the key while on canvas to instantly create the node."
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Splitter for two tables
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # === LEFT: Current Bindings ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        bindings_group = QGroupBox("Current Hotkeys")
        bindings_layout = QVBoxLayout(bindings_group)

        self._bindings_table = QTableWidget()
        self._bindings_table.setColumnCount(3)
        self._bindings_table.setHorizontalHeaderLabels(["Key", "Node", "Category"])
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
        self._bindings_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._bindings_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._bindings_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        bindings_layout.addWidget(self._bindings_table)

        # Remove button
        remove_btn = QPushButton("Remove Selected Hotkey")
        remove_btn.clicked.connect(self._on_remove_binding)
        bindings_layout.addWidget(remove_btn)

        left_layout.addWidget(bindings_group)
        splitter.addWidget(left_widget)

        # === RIGHT: All Nodes ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        nodes_group = QGroupBox("All Available Nodes")
        nodes_layout = QVBoxLayout(nodes_group)

        # Search box
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Type to filter nodes...")
        self._search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self._search_input)
        nodes_layout.addLayout(search_layout)

        # Nodes table
        self._nodes_table = QTableWidget()
        self._nodes_table.setColumnCount(3)
        self._nodes_table.setHorizontalHeaderLabels(
            ["Node Name", "Type", "Current Key"]
        )
        self._nodes_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._nodes_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self._nodes_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self._nodes_table.setColumnWidth(1, 180)
        self._nodes_table.setColumnWidth(2, 80)
        self._nodes_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self._nodes_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._nodes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        nodes_layout.addWidget(self._nodes_table)

        # Assign hotkey section
        assign_layout = QHBoxLayout()
        assign_layout.addWidget(QLabel("Assign key:"))
        self._key_combo = QComboBox()
        self._key_combo.setMinimumWidth(60)
        assign_layout.addWidget(self._key_combo)
        assign_layout.addWidget(QLabel("to selected node"))
        assign_btn = QPushButton("Assign")
        assign_btn.clicked.connect(self._on_assign_binding)
        assign_layout.addWidget(assign_btn)
        assign_layout.addStretch()
        nodes_layout.addLayout(assign_layout)

        right_layout.addWidget(nodes_group)
        splitter.addWidget(right_widget)

        # Set splitter sizes
        splitter.setSizes([350, 550])
        layout.addWidget(splitter)

        # === Bottom buttons ===
        button_layout = QHBoxLayout()

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._on_reset_defaults)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setDefault(True)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

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

    def _populate_nodes_table(self, nodes: List[Tuple[str, str]]) -> None:
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

            reply = QMessageBox.question(
                self,
                "Remove Hotkey",
                f"Remove hotkey '{key.upper()}' for '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._manager.remove_binding(key)
                self._manager.save_bindings()
                self._load_data()

    def _on_assign_binding(self) -> None:
        """Assign a hotkey to the selected node."""
        # Get selected node
        selected = self._nodes_table.selectedItems()
        if not selected:
            QMessageBox.warning(
                self, "No Selection", "Please select a node to assign a hotkey."
            )
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
            QMessageBox.warning(self, "No Key", "Please select a key to assign.")
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
        elif (
            "desktop" in node_lower
            or "window" in node_lower
            or "application" in node_lower
        ):
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

    def _on_reset_defaults(self) -> None:
        """Reset all bindings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "This will remove all custom hotkeys and restore the default bindings.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self._manager.reset_to_defaults()
            self._manager.save_bindings()
            self._load_data()

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: #d4d4d4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #d4d4d4;
            }
            QTableWidget {
                background: #252526;
                border: 1px solid #3e3e42;
                gridline-color: #3e3e42;
                color: #d4d4d4;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background: #094771;
                color: white;
            }
            QHeaderView::section {
                background: #2d2d30;
                color: #d4d4d4;
                padding: 6px;
                border: none;
                border-right: 1px solid #3e3e42;
                border-bottom: 1px solid #3e3e42;
            }
            QLineEdit {
                background: #3c3c3c;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 6px;
                color: #d4d4d4;
            }
            QLineEdit:focus {
                border-color: #007acc;
            }
            QComboBox {
                background: #3c3c3c;
                border: 1px solid #3e3e42;
                border-radius: 4px;
                padding: 4px 8px;
                color: #d4d4d4;
                min-height: 24px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #252526;
                border: 1px solid #3e3e42;
                selection-background-color: #094771;
            }
            QPushButton {
                background: #2d2d30;
                border: 1px solid #454545;
                border-radius: 4px;
                padding: 6px 16px;
                color: #d4d4d4;
                min-height: 28px;
            }
            QPushButton:hover {
                background: #3e3e42;
                border-color: #007acc;
            }
            QPushButton:pressed {
                background: #094771;
            }
            QPushButton:default {
                background: #007acc;
                border-color: #007acc;
                color: white;
            }
            QLabel {
                color: #d4d4d4;
            }
            QSplitter::handle {
                background: #3e3e42;
            }
        """)
