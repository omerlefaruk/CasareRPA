"""
Parameter Promotion Dialog for Subflow Editor.

Allows users to select which internal node properties to expose
at the subflow level for external configuration.
"""

from typing import Any, Dict, List, Optional

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from casare_rpa.domain.entities.subflow import Subflow, SubflowParameter
from casare_rpa.domain.schemas.property_types import PropertyType


class ParameterPromotionDialog(QDialog):
    """
    Dialog for promoting internal node parameters to subflow level.

    Features:
    - Tree view of internal nodes and their properties
    - Checkbox to select properties for promotion
    - Alias input for user-friendly names
    - Default value override
    - Preview of promoted parameters
    """

    def __init__(
        self,
        subflow: Subflow,
        node_schemas: dict[str, Any] | None = None,
        parent=None,
    ):
        """
        Initialize the Parameter Promotion Dialog.

        Args:
            subflow: Subflow entity to promote parameters for
            node_schemas: Optional dict mapping node_type -> schema with properties
            parent: Parent widget
        """
        super().__init__(parent)
        self.subflow = subflow
        self.node_schemas = node_schemas or {}

        # Track selections: {qualified_name: SubflowParameter}
        self._selections: dict[str, SubflowParameter] = {}

        # Build lookup for existing promoted params by their internal identifiers
        # This allows matching even if qualified_name format changed
        self._existing_params_lookup: dict[str, SubflowParameter] = {}
        for param in subflow.parameters:
            # Key by internal_node_id + internal_property_name for robust matching
            key = f"{param.internal_node_id}:{param.internal_property_name}"
            self._existing_params_lookup[key] = param

        # Currently selected item for editing
        self._current_item: QTreeWidgetItem | None = None

        self._setup_ui()
        self._populate_tree()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Promote Parameters to Subflow")
        self.setMinimumSize(800, 550)
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Select properties from internal nodes to expose at the subflow level.\n"
            "Users can then configure these properties without opening the subflow."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #B0B0B0; padding: 8px;")
        layout.addWidget(instructions)

        # Splitter for tree and config panel
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tree of nodes and properties
        tree_frame = QFrame()
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        tree_label = QLabel("Internal Nodes and Properties")
        tree_label.setStyleSheet("font-weight: bold; color: #E0E0E0;")
        tree_layout.addWidget(tree_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Property", "Type", "Current Value"])
        self.tree.setColumnWidth(0, 220)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 120)
        self.tree.itemChanged.connect(self._on_item_changed)
        self.tree.itemClicked.connect(self._on_item_clicked)
        tree_layout.addWidget(self.tree)

        splitter.addWidget(tree_frame)

        # Right: Configuration for selected parameter
        config_frame = QFrame()
        config_layout = QVBoxLayout(config_frame)
        config_layout.setContentsMargins(0, 0, 0, 0)

        config_label = QLabel("Parameter Configuration")
        config_label.setStyleSheet("font-weight: bold; color: #E0E0E0;")
        config_layout.addWidget(config_label)

        # Form layout for config fields
        form_widget = QGroupBox()
        self.config_layout = QFormLayout(form_widget)

        self.alias_input = QLineEdit()
        self.alias_input.setPlaceholderText("User-friendly name (e.g., 'Login URL')")
        self.alias_input.textChanged.connect(self._on_config_changed)
        self.config_layout.addRow("Display Name:", self.alias_input)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Tooltip description for users")
        self.description_input.setMaximumHeight(60)
        self.description_input.textChanged.connect(self._on_config_changed)
        self.config_layout.addRow("Description:", self.description_input)

        self.default_input = QLineEdit()
        self.default_input.setPlaceholderText("Override default value")
        self.default_input.textChanged.connect(self._on_config_changed)
        self.config_layout.addRow("Default Value:", self.default_input)

        self.placeholder_input = QLineEdit()
        self.placeholder_input.setPlaceholderText("Input placeholder text")
        self.placeholder_input.textChanged.connect(self._on_config_changed)
        self.config_layout.addRow("Placeholder:", self.placeholder_input)

        self.required_check = QCheckBox("Value must be provided")
        self.required_check.stateChanged.connect(self._on_config_changed)
        self.config_layout.addRow("Required:", self.required_check)

        config_layout.addWidget(form_widget)
        config_layout.addStretch()

        splitter.addWidget(config_frame)

        # Set splitter sizes (60% tree, 40% config)
        splitter.setSizes([500, 350])

        layout.addWidget(splitter)

        # Buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        button_layout.addWidget(self.deselect_all_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #E0E0E0;
            }
            QTreeWidget {
                background-color: #252526;
                color: #E0E0E0;
                border: 1px solid #3C3C3C;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #094771;
            }
            QTreeWidget::item:hover {
                background-color: #2A2D2E;
            }
            QLineEdit, QTextEdit {
                background-color: #3C3C3C;
                color: #E0E0E0;
                border: 1px solid #505050;
                border-radius: 3px;
                padding: 4px;
            }
            QGroupBox {
                border: 1px solid #3C3C3C;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QPushButton {
                background-color: #0E639C;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177BB;
            }
            QPushButton:pressed {
                background-color: #094771;
            }
            QCheckBox {
                color: #E0E0E0;
            }
            QLabel {
                color: #E0E0E0;
            }
        """)

    def _populate_tree(self) -> None:
        """Populate tree with internal nodes and their properties."""
        self.tree.clear()

        for node_id, node_data in self.subflow.nodes.items():
            node_type = node_data.get("node_type")
            if not node_type:
                logger.warning(f"Subflow node {node_id} missing node_type")
                continue
            node_name = node_data.get("name", node_type)

            # Create node item
            node_item = QTreeWidgetItem([node_name, "", ""])
            node_item.setData(0, Qt.ItemDataRole.UserRole, {"node_id": node_id, "is_node": True})
            node_item.setFlags(node_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            node_item.setExpanded(True)

            # Get schema for this node type
            schema = self.node_schemas.get(node_type)
            if schema and hasattr(schema, "properties"):
                self._add_properties_from_schema(node_item, node_id, schema, node_data)
            else:
                # Try to get properties from node_data directly
                properties = node_data.get("config", {})
                if properties:
                    self._add_properties_from_dict(node_item, node_id, properties)

            # Only add node if it has children
            if node_item.childCount() > 0:
                self.tree.addTopLevelItem(node_item)

    def _add_properties_from_schema(
        self,
        parent_item: QTreeWidgetItem,
        node_id: str,
        schema: Any,
        node_data: dict,
    ) -> None:
        """Add property items from node schema."""
        if not hasattr(schema, "properties"):
            return

        config = node_data.get("config", {})

        for prop_def in schema.properties:
            # Use last 8 chars of node_id (unique UUID suffix) to avoid collisions
            # e.g., MessageBoxNode_1746689e -> 1746689e_message
            qualified_name = f"{node_id[-8:]}_{prop_def.name}"
            current_value = config.get(prop_def.name, prop_def.default)

            prop_item = QTreeWidgetItem(
                [
                    prop_def.name,
                    prop_def.type.value if hasattr(prop_def.type, "value") else str(prop_def.type),
                    str(current_value)[:30] if current_value else "",
                ]
            )

            # IMPORTANT: Set data BEFORE setting flags/check state
            # because setCheckState triggers itemChanged signal
            prop_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "node_id": node_id,
                    "property_name": prop_def.name,
                    "property_type": prop_def.type,
                    "default_value": prop_def.default,
                    "qualified_name": qualified_name,
                    "is_node": False,
                },
            )

            prop_item.setFlags(prop_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            prop_item.setCheckState(0, Qt.CheckState.Unchecked)

            # Check if already promoted (using internal identifiers for robust matching)
            lookup_key = f"{node_id}:{prop_def.name}"
            if lookup_key in self._existing_params_lookup:
                prop_item.setCheckState(0, Qt.CheckState.Checked)
                # Pre-add to selections with NEW qualified_name
                existing_param = self._existing_params_lookup[lookup_key]
                # Update the param name to use new qualified_name format
                existing_param.name = qualified_name
                self._selections[qualified_name] = existing_param

            parent_item.addChild(prop_item)

    def _add_properties_from_dict(
        self,
        parent_item: QTreeWidgetItem,
        node_id: str,
        properties: dict,
    ) -> None:
        """Add property items from dictionary (fallback when no schema)."""
        for prop_name, prop_value in properties.items():
            # Skip internal/hidden properties
            if prop_name.startswith("_") or prop_name in ("node_id", "type", "name"):
                continue

            # Use last 8 chars of node_id (unique UUID suffix) to avoid collisions
            qualified_name = f"{node_id[-8:]}_{prop_name}"

            # Infer type from value
            if isinstance(prop_value, bool):
                prop_type = PropertyType.BOOLEAN
            elif isinstance(prop_value, int):
                prop_type = PropertyType.INTEGER
            elif isinstance(prop_value, float):
                prop_type = PropertyType.FLOAT
            elif isinstance(prop_value, list):
                prop_type = PropertyType.JSON
            elif isinstance(prop_value, dict):
                prop_type = PropertyType.JSON
            else:
                prop_type = PropertyType.STRING

            prop_item = QTreeWidgetItem(
                [
                    prop_name,
                    prop_type.value,
                    str(prop_value)[:30] if prop_value is not None else "",
                ]
            )

            # IMPORTANT: Set data BEFORE setting flags/check state
            # because setCheckState triggers itemChanged signal
            prop_item.setData(
                0,
                Qt.ItemDataRole.UserRole,
                {
                    "node_id": node_id,
                    "property_name": prop_name,
                    "property_type": prop_type,
                    "default_value": prop_value,
                    "qualified_name": qualified_name,
                    "is_node": False,
                },
            )

            prop_item.setFlags(prop_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            prop_item.setCheckState(0, Qt.CheckState.Unchecked)

            # Check if already promoted (using internal identifiers for robust matching)
            lookup_key = f"{node_id}:{prop_name}"
            if lookup_key in self._existing_params_lookup:
                prop_item.setCheckState(0, Qt.CheckState.Checked)
                # Pre-add to selections with NEW qualified_name
                existing_param = self._existing_params_lookup[lookup_key]
                existing_param.name = qualified_name
                self._selections[qualified_name] = existing_param

            parent_item.addChild(prop_item)

    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle checkbox state changes."""
        if column != 0:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("is_node", True):
            return

        qualified_name = data.get("qualified_name", "")
        if not qualified_name:
            return

        logger.debug(
            f"Item changed: {qualified_name}, checked={item.checkState(0) == Qt.CheckState.Checked}"
        )
        logger.debug(f"Current selections before: {list(self._selections.keys())}")

        if item.checkState(0) == Qt.CheckState.Checked:
            # Add to selections
            display_name = data["property_name"].replace("_", " ").title()
            param = SubflowParameter(
                name=qualified_name,
                display_name=display_name,
                label=display_name,  # For widget display
                internal_node_id=data["node_id"],
                internal_property_name=data["property_name"],
                property_type=data["property_type"],
                default_value=data["default_value"],
            )
            self._selections[qualified_name] = param
            logger.info(f"Added parameter: {qualified_name} (total: {len(self._selections)})")
        else:
            # Remove from selections
            removed = self._selections.pop(qualified_name, None)
            if removed:
                logger.info(f"Removed parameter: {qualified_name} (total: {len(self._selections)})")

        logger.debug(f"Current selections after: {list(self._selections.keys())}")

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item click to update config panel."""
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("is_node", True):
            self._clear_config_panel()
            return

        qualified_name = data.get("qualified_name", "")
        self._current_item = item

        # Load existing config if this item is promoted
        if qualified_name in self._selections:
            param = self._selections[qualified_name]
            self._load_param_to_config(param)
        else:
            # Show defaults for potential promotion
            self.alias_input.setText(data["property_name"].replace("_", " ").title())
            self.description_input.clear()
            default_val = data.get("default_value")
            self.default_input.setText(str(default_val) if default_val is not None else "")
            self.placeholder_input.clear()
            self.required_check.setChecked(False)

    def _load_param_to_config(self, param: SubflowParameter) -> None:
        """Load parameter values to config panel."""
        self.alias_input.setText(param.display_name)
        self.description_input.setPlainText(param.description)
        self.default_input.setText(
            str(param.default_value) if param.default_value is not None else ""
        )
        self.placeholder_input.setText(param.placeholder)
        self.required_check.setChecked(param.required)

    def _clear_config_panel(self) -> None:
        """Clear the config panel."""
        self._current_item = None
        self.alias_input.clear()
        self.description_input.clear()
        self.default_input.clear()
        self.placeholder_input.clear()
        self.required_check.setChecked(False)

    def _on_config_changed(self) -> None:
        """Handle config panel changes - update selection if item is checked."""
        if not self._current_item:
            return

        data = self._current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data.get("is_node", True):
            return

        qualified_name = data.get("qualified_name", "")
        if qualified_name not in self._selections:
            return

        # Update the parameter with new config values
        param = self._selections[qualified_name]
        param.display_name = self.alias_input.text() or param.display_name
        param.label = param.display_name
        param.description = self.description_input.toPlainText()
        param.placeholder = self.placeholder_input.text()
        param.required = self.required_check.isChecked()

        # Parse default value based on type
        default_text = self.default_input.text()
        if default_text:
            try:
                if param.property_type == PropertyType.INTEGER:
                    param.default_value = int(default_text)
                elif param.property_type == PropertyType.FLOAT:
                    param.default_value = float(default_text)
                elif param.property_type == PropertyType.BOOLEAN:
                    param.default_value = default_text.lower() in ("true", "1", "yes")
                else:
                    param.default_value = default_text
            except ValueError:
                param.default_value = default_text

    def _select_all(self) -> None:
        """Select all property items."""
        for i in range(self.tree.topLevelItemCount()):
            node_item = self.tree.topLevelItem(i)
            for j in range(node_item.childCount()):
                prop_item = node_item.child(j)
                prop_item.setCheckState(0, Qt.CheckState.Checked)

    def _deselect_all(self) -> None:
        """Deselect all property items."""
        for i in range(self.tree.topLevelItemCount()):
            node_item = self.tree.topLevelItem(i)
            for j in range(node_item.childCount()):
                prop_item = node_item.child(j)
                prop_item.setCheckState(0, Qt.CheckState.Unchecked)

    def get_promoted_parameters(self) -> list[SubflowParameter]:
        """
        Get the list of promoted parameters.

        Returns:
            List of SubflowParameter objects for all selected promotions
        """
        params = list(self._selections.values())
        logger.info(f"Returning {len(params)} promoted parameters: {[p.name for p in params]}")
        return params


def show_parameter_promotion_dialog(
    subflow: Subflow,
    node_schemas: dict[str, Any] | None = None,
    parent=None,
) -> list[SubflowParameter] | None:
    """
    Show the parameter promotion dialog and return selected parameters.

    Args:
        subflow: Subflow entity to promote parameters for
        node_schemas: Optional dict mapping node_type -> schema
        parent: Parent widget

    Returns:
        List of SubflowParameter if accepted, None if cancelled
    """
    dialog = ParameterPromotionDialog(subflow, node_schemas, parent)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.get_promoted_parameters()
    return None
