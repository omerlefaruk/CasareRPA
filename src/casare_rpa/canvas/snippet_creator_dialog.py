"""
CasareRPA - Snippet Creator Dialog
UI for creating snippets from selected nodes with parameter and scope configuration.
"""

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QCheckBox,
    QGroupBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
    QMessageBox,
)
from loguru import logger

from .snippet_creator import SnippetCreator
from ..core.snippet_definition import ParameterMapping, VariableScopeConfig
from ..core.snippet_library import get_snippet_library
from ..core.types import DataType


class SnippetCreatorDialog(QDialog):
    """
    Dialog for creating snippets from selected nodes.

    Features:
    - Metadata input (name, description, category, author)
    - Parameter configuration with auto-detection
    - Variable scope options
    - Preview of snippet structure
    - Save to library
    """

    def __init__(self, selected_visual_nodes: List, all_connections: List, parent=None):
        """
        Initialize snippet creator dialog.

        Args:
            selected_visual_nodes: List of selected visual nodes
            all_connections: List of all connections in the graph
            parent: Parent widget
        """
        super().__init__(parent)
        self.selected_visual_nodes = selected_visual_nodes
        self.all_connections = all_connections
        self.snippet_creator = SnippetCreator()

        self.setWindowTitle("Create Snippet from Selection")
        self.setModal(True)
        self.resize(700, 600)

        self._init_ui()
        self._populate_defaults()

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Metadata section
        metadata_group = QGroupBox("Snippet Metadata")
        metadata_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter a descriptive name for this snippet")
        metadata_layout.addRow("Name*:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Describe what this snippet does...")
        self.description_edit.setMaximumHeight(60)
        metadata_layout.addRow("Description:", self.description_edit)

        self.category_combo = QComboBox()
        self._populate_categories()
        self.category_combo.setEditable(True)
        metadata_layout.addRow("Category:", self.category_combo)

        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Your name or team name")
        metadata_layout.addRow("Author:", self.author_edit)

        metadata_group.setLayout(metadata_layout)
        layout.addWidget(metadata_group)

        # Variable scope section
        scope_group = QGroupBox("Variable Scope")
        scope_layout = QVBoxLayout()

        self.inherit_scope_check = QCheckBox("Inherit parent workflow variables")
        self.inherit_scope_check.setChecked(True)
        self.inherit_scope_check.setToolTip(
            "If checked, the snippet can access variables from the parent workflow"
        )
        scope_layout.addWidget(self.inherit_scope_check)

        self.export_vars_check = QCheckBox("Export local variables back to parent")
        self.export_vars_check.setChecked(False)
        self.export_vars_check.setToolTip(
            "If checked, variables created/modified in the snippet will be visible to the parent workflow"
        )
        scope_layout.addWidget(self.export_vars_check)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Parameters section
        params_group = QGroupBox("Parameters (Optional)")
        params_layout = QVBoxLayout()

        params_info = QLabel(
            "Parameters allow you to customize snippet behavior when inserting it.\n"
            "Click 'Auto-Detect' to scan for common parameterizable values."
        )
        params_info.setWordWrap(True)
        params_info.setStyleSheet("color: #888; font-size: 10pt;")
        params_layout.addWidget(params_info)

        # Parameters table
        self.params_table = QTableWidget(0, 5)
        self.params_table.setHorizontalHeaderLabels([
            "Parameter Name", "Target Node", "Config Key", "Type", "Required"
        ])
        self.params_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.params_table.setMaximumHeight(150)
        params_layout.addWidget(self.params_table)

        # Parameter buttons
        params_buttons = QHBoxLayout()
        self.auto_detect_btn = QPushButton("Auto-Detect Parameters")
        self.auto_detect_btn.clicked.connect(self._auto_detect_parameters)
        params_buttons.addWidget(self.auto_detect_btn)

        self.clear_params_btn = QPushButton("Clear All")
        self.clear_params_btn.clicked.connect(self._clear_parameters)
        params_buttons.addWidget(self.clear_params_btn)

        params_buttons.addStretch()
        params_layout.addLayout(params_buttons)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # Info section
        info_label = QLabel(
            f"<b>Selected Nodes:</b> {len(self.selected_visual_nodes)}<br>"
            f"<b>Connections:</b> Will be analyzed when creating snippet"
        )
        info_label.setStyleSheet("background: #2a2a2a; padding: 8px; border-radius: 4px;")
        layout.addWidget(info_label)

        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.create_btn = QPushButton("Create Snippet")
        self.create_btn.setDefault(True)
        self.create_btn.clicked.connect(self._create_snippet)
        button_layout.addWidget(self.create_btn)

        layout.addLayout(button_layout)

    def _populate_categories(self):
        """Populate category combo box with existing categories."""
        library = get_snippet_library()
        categories = library.get_categories()

        # Add default categories
        default_categories = ["custom", "web", "desktop", "data", "flow"]
        for cat in default_categories:
            if cat not in categories:
                self.category_combo.addItem(cat)

        # Add existing categories
        for cat in categories:
            if cat not in default_categories:
                self.category_combo.addItem(cat)

    def _populate_defaults(self):
        """Populate form with default values."""
        # Set default category
        self.category_combo.setCurrentText("custom")

        # Set default name based on node count
        node_count = len(self.selected_visual_nodes)
        self.name_edit.setText(f"Snippet with {node_count} nodes")
        self.name_edit.selectAll()

    def _auto_detect_parameters(self):
        """Auto-detect parameters from selected nodes."""
        # Get serialized nodes
        casare_nodes = {}
        for visual_node in self.selected_visual_nodes:
            if hasattr(visual_node, "_casare_node") and visual_node._casare_node:
                node_id = visual_node.get_property("node_id")
                if node_id:
                    casare_nodes[node_id] = visual_node._casare_node.serialize()

        # Auto-detect parameters
        detected = self.snippet_creator.auto_detect_parameters(casare_nodes)

        # Clear existing table
        self.params_table.setRowCount(0)

        # Populate table with detected parameters
        for param in detected:
            self._add_parameter_row(param)

        logger.info(f"Auto-detected {len(detected)} parameters")

    def _add_parameter_row(self, param: ParameterMapping):
        """Add a parameter to the table."""
        row = self.params_table.rowCount()
        self.params_table.insertRow(row)

        # Parameter name
        name_item = QTableWidgetItem(param.snippet_param_name)
        self.params_table.setItem(row, 0, name_item)

        # Target node ID (shortened for display)
        node_item = QTableWidgetItem(param.target_node_id[:12] + "...")
        node_item.setToolTip(param.target_node_id)
        node_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.params_table.setItem(row, 1, node_item)

        # Config key
        key_item = QTableWidgetItem(param.target_config_key)
        key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.params_table.setItem(row, 2, key_item)

        # Type
        type_item = QTableWidgetItem(param.param_type.value)
        type_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.params_table.setItem(row, 3, type_item)

        # Required
        required_item = QTableWidgetItem("Yes" if param.required else "No")
        required_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
        self.params_table.setItem(row, 4, required_item)

    def _clear_parameters(self):
        """Clear all parameters from the table."""
        self.params_table.setRowCount(0)

    def _get_parameters_from_table(self) -> List[ParameterMapping]:
        """Extract parameter mappings from the table."""
        # For now, we'll use the auto-detected parameters
        # In a full implementation, the table would be editable
        # and we'd parse the table contents here
        return []

    def _create_snippet(self):
        """Create the snippet and save to library."""
        # Validate inputs
        snippet_name = self.name_edit.text().strip()
        if not snippet_name:
            QMessageBox.warning(
                self,
                "Missing Name",
                "Please enter a name for the snippet."
            )
            self.name_edit.setFocus()
            return

        # Get form values
        description = self.description_edit.toPlainText().strip()
        category = self.category_combo.currentText().strip() or "custom"
        author = self.author_edit.text().strip()

        # Get variable scope config
        variable_scope = VariableScopeConfig(
            inherit_parent_scope=self.inherit_scope_check.isChecked(),
            export_local_vars=self.export_vars_check.isChecked(),
            isolated_vars=[],
            input_mappings={},
            output_mappings={},
        )

        # Get parameters (if any were detected)
        parameters = self._get_parameters_from_table()

        try:
            # Create snippet definition
            snippet = self.snippet_creator.create_from_selection(
                selected_visual_nodes=self.selected_visual_nodes,
                all_connections=self.all_connections,
                snippet_name=snippet_name,
                description=description,
                category=category,
                author=author,
                parameters=parameters,
                variable_scope=variable_scope,
            )

            # Save to library
            file_path = self.snippet_creator.save_snippet(snippet)

            logger.info(f"Snippet '{snippet_name}' created and saved to {file_path}")

            # Show success message
            QMessageBox.information(
                self,
                "Snippet Created",
                f"Snippet '{snippet_name}' has been created successfully!\n\n"
                f"Category: {category}\n"
                f"Nodes: {len(snippet.nodes)}\n"
                f"Connections: {len(snippet.connections)}\n"
                f"Entry points: {len(snippet.entry_node_ids)}\n"
                f"Exit points: {len(snippet.exit_node_ids)}\n\n"
                f"You can now insert this snippet from the Snippet Library."
            )

            # Close dialog
            self.accept()

        except Exception as e:
            logger.exception(f"Failed to create snippet: {e}")
            QMessageBox.critical(
                self,
                "Error Creating Snippet",
                f"An error occurred while creating the snippet:\n\n{str(e)}"
            )
