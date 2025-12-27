"""
Environment Editor Dialog.

Full-featured dialog for managing environments (dev, staging, production, custom):
- View/edit environment variables with inheritance visualization
- Create/clone/delete custom environments
- Switch active environment
- Variable override management
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.domain.entities.project import (
    Environment,
    EnvironmentType,
)
from casare_rpa.domain.entities.project.environment import (
    generate_environment_id,
)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS


class EnvironmentEditorDialog(QDialog):
    """
    Environment management dialog.

    Features:
    - List all environments (dev, staging, prod, custom)
    - Highlight current environment
    - Edit environment name (custom only), description
    - Variables table with inheritance visualization
    - Clone/delete custom environments
    - Inheritance chain visualization

    Signals:
        environment_changed(str): Emitted when environment is modified
        environment_created(str): Emitted when new environment is created
        environment_deleted(str): Emitted when environment is deleted
    """

    environment_changed = Signal(str)  # environment_id
    environment_created = Signal(str)  # environment_id
    environment_deleted = Signal(str)  # environment_id

    def __init__(
        self,
        project: Any | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize environment editor dialog.

        Args:
            project: Current project with environments_dir property
            parent: Parent widget
        """
        super().__init__(parent)

        self._project = project
        self._environments: list[Environment] = []
        self._current_env: Environment | None = None
        self._resolved_variables: dict[str, Any] = {}
        self._inherited_keys: set = set()

        self.setWindowTitle("Environment Editor")
        self.setMinimumSize(900, 650)
        self.setModal(True)

        self._setup_ui()
        self._load_environments()
        self._apply_styles()

        logger.debug("EnvironmentEditorDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Inheritance visualization header
        self._inheritance_label = QLabel()
        self._inheritance_label.setStyleSheet(
            f"font-size: 11px; color: {THEME.text_disabled}; padding: {SPACING.xs}px;"
        )
        self._update_inheritance_label()
        layout.addWidget(self._inheritance_label)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel - environment list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        list_label = QLabel("Environments")
        list_label.setStyleSheet("font-weight: bold; font-size: 14px; color: {THEME.text_primary};")
        left_layout.addWidget(list_label)

        self._env_list = QListWidget()
        self._env_list.setMinimumWidth(180)
        self._env_list.setMaximumWidth(220)
        self._env_list.itemClicked.connect(self._on_environment_selected)
        left_layout.addWidget(self._env_list)

        # Add custom environment button
        self._add_btn = QPushButton("+ Add Custom Environment")
        self._add_btn.clicked.connect(self._add_custom_environment)
        left_layout.addWidget(self._add_btn)

        splitter.addWidget(left_widget)

        # Right panel - environment details
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Environment info group
        self._info_group = QGroupBox("Environment Details")
        info_layout = QFormLayout()

        self._env_name_input = QLineEdit()
        self._env_name_input.setPlaceholderText("Environment name")
        self._env_name_input.textChanged.connect(self._on_name_changed)
        info_layout.addRow("Name:", self._env_name_input)

        self._env_type_label = QLabel("-")
        self._env_type_label.setStyleSheet(f"color: {THEME.text_disabled};")
        info_layout.addRow("Type:", self._env_type_label)

        self._env_description = QTextEdit()
        self._env_description.setMaximumHeight(60)
        self._env_description.setPlaceholderText("Environment description...")
        self._env_description.textChanged.connect(self._on_description_changed)
        info_layout.addRow("Description:", self._env_description)

        # Color indicator
        color_layout = QHBoxLayout()
        self._color_indicator = QLabel()
        self._color_indicator.setFixedSize(24, 24)
        self._color_indicator.setStyleSheet(
            f"border: 1px solid {THEME.border}; border-radius: {RADIUS.sm}px;"
        )
        color_layout.addWidget(self._color_indicator)
        color_layout.addStretch()
        info_layout.addRow("Color:", color_layout)

        self._info_group.setLayout(info_layout)
        right_layout.addWidget(self._info_group)

        # Variables group
        self._variables_group = QGroupBox("Variables")
        var_layout = QVBoxLayout()

        # Variables toolbar
        var_toolbar = QHBoxLayout()
        self._add_var_btn = QPushButton("+ Add Variable")
        self._add_var_btn.clicked.connect(self._add_variable)
        var_toolbar.addWidget(self._add_var_btn)

        self._delete_var_btn = QPushButton("Delete Variable")
        self._delete_var_btn.clicked.connect(self._delete_variable)
        self._delete_var_btn.setEnabled(False)
        var_toolbar.addWidget(self._delete_var_btn)

        var_toolbar.addStretch()

        # Show inherited toggle
        self._show_inherited_cb = QCheckBox("Show Inherited")
        self._show_inherited_cb.setChecked(True)
        self._show_inherited_cb.toggled.connect(self._refresh_variables_table)
        var_toolbar.addWidget(self._show_inherited_cb)

        var_layout.addLayout(var_toolbar)

        # Variables table
        self._variables_table = QTableWidget()
        self._variables_table.setColumnCount(4)
        self._variables_table.setHorizontalHeaderLabels(["Name", "Value", "Inherited", "Source"])
        self._variables_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self._variables_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._variables_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )
        self._variables_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )
        self._variables_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._variables_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._variables_table.itemSelectionChanged.connect(self._on_variable_selection_changed)
        self._variables_table.cellChanged.connect(self._on_variable_cell_changed)
        var_layout.addWidget(self._variables_table)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))

        local_indicator = QLabel("Local")
        local_indicator.setStyleSheet(
            f"background-color: {THEME.bg_surface}; padding: {SPACING.xs}px {SPACING.sm}px; "
            f"border-radius: {RADIUS.sm}px;"
        )
        legend_layout.addWidget(local_indicator)

        inherited_indicator = QLabel("Inherited")
        inherited_indicator.setStyleSheet(
            f"background-color: {THEME.bg_surface}; color: {THEME.text_disabled}; "
            f"padding: {SPACING.xs}px {SPACING.sm}px; border-radius: {RADIUS.sm}px; font-style: italic;"
        )
        legend_layout.addWidget(inherited_indicator)

        overridden_indicator = QLabel("Overridden")
        overridden_indicator.setStyleSheet(
            f"background-color: {THEME.bg_component}; padding: {SPACING.xs}px {SPACING.sm}px; "
            f"border-radius: {RADIUS.sm}px;"
        )
        legend_layout.addWidget(overridden_indicator)

        legend_layout.addStretch()
        var_layout.addLayout(legend_layout)

        self._variables_group.setLayout(var_layout)
        right_layout.addWidget(self._variables_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self._clone_btn = QPushButton("Clone Environment")
        self._clone_btn.clicked.connect(self._clone_environment)
        action_layout.addWidget(self._clone_btn)

        self._delete_btn = QPushButton("Delete Environment")
        self._delete_btn.clicked.connect(self._delete_environment)
        self._delete_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {THEME.error};
            }}
            QPushButton:hover {{
                background-color: {THEME.error};
                filter: brightness(1.1);
            }}
            QPushButton:disabled {{
                background-color: {THEME.border};
            }}
        """
        )
        action_layout.addWidget(self._delete_btn)

        self._set_active_btn = QPushButton("Set as Active")
        self._set_active_btn.clicked.connect(self._set_active_environment)
        self._set_active_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {THEME.success};
            }}
            QPushButton:hover {{
                background-color: {THEME.success};
                filter: brightness(1.1);
            }}
        """
        )
        action_layout.addWidget(self._set_active_btn)

        action_layout.addStretch()
        right_layout.addLayout(action_layout)

        splitter.addWidget(right_widget)
        splitter.setSizes([200, 700])

        layout.addWidget(splitter)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._save_and_close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _update_inheritance_label(self) -> None:
        """Update the inheritance chain visualization label."""
        chain = "Inheritance Chain: " "Development -> Staging -> Production"
        self._inheritance_label.setText(chain)

    def _load_environments(self) -> None:
        """Load environments from storage."""
        self._env_list.clear()
        self._environments = []

        if not self._project or not hasattr(self._project, "environments_dir"):
            # Create default environments for display
            self._environments = Environment.create_default_environments()
        else:
            try:
                from casare_rpa.infrastructure.persistence.environment_storage import (
                    EnvironmentStorage,
                )

                self._environments = EnvironmentStorage.load_all_environments(
                    self._project.environments_dir
                )

                if not self._environments:
                    # Create defaults if none exist
                    self._environments = EnvironmentStorage.create_default_environments(
                        self._project.environments_dir
                    )
            except Exception as e:
                logger.error(f"Failed to load environments: {e}")
                self._environments = Environment.create_default_environments()

        # Sort: standard types first, then custom by name
        type_order = {
            EnvironmentType.DEVELOPMENT: 0,
            EnvironmentType.STAGING: 1,
            EnvironmentType.PRODUCTION: 2,
            EnvironmentType.CUSTOM: 3,
        }
        self._environments.sort(key=lambda e: (type_order.get(e.env_type, 99), e.name))

        # Populate list
        active_env_id = (
            self._project.active_environment_id
            if self._project and hasattr(self._project, "active_environment_id")
            else None
        )

        for env in self._environments:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, env.id)

            # Display with type indicator and active marker
            type_indicators = {
                EnvironmentType.DEVELOPMENT: "[D]",
                EnvironmentType.STAGING: "[S]",
                EnvironmentType.PRODUCTION: "[P]",
                EnvironmentType.CUSTOM: "[C]",
            }
            indicator = type_indicators.get(env.env_type, "[?]")
            active_marker = " *" if env.id == active_env_id else ""
            item.setText(f"{indicator} {env.name}{active_marker}")

            # Set color based on environment type
            item.setForeground(QColor(env.color))

            # Bold for active environment
            if env.id == active_env_id:
                font = item.font()
                font.setBold(True)
                item.setFont(font)

            self._env_list.addItem(item)

        # Select first environment
        if self._env_list.count() > 0:
            self._env_list.setCurrentRow(0)
            self._on_environment_selected(self._env_list.item(0))

    def _on_environment_selected(self, item: QListWidgetItem) -> None:
        """Handle environment selection."""
        env_id = item.data(Qt.ItemDataRole.UserRole)
        self._current_env = next((e for e in self._environments if e.id == env_id), None)

        if not self._current_env:
            return

        # Update UI
        self._env_name_input.blockSignals(True)
        self._env_name_input.setText(self._current_env.name)
        self._env_name_input.blockSignals(False)

        # Name is only editable for custom environments
        is_custom = self._current_env.env_type == EnvironmentType.CUSTOM
        self._env_name_input.setEnabled(is_custom)

        # Type label
        type_names = {
            EnvironmentType.DEVELOPMENT: "Development (Base)",
            EnvironmentType.STAGING: "Staging (Inherits from Development)",
            EnvironmentType.PRODUCTION: "Production (Inherits from Staging)",
            EnvironmentType.CUSTOM: "Custom",
        }
        self._env_type_label.setText(type_names.get(self._current_env.env_type, "Unknown"))

        # Description
        self._env_description.blockSignals(True)
        self._env_description.setPlainText(self._current_env.description)
        self._env_description.blockSignals(False)

        # Color indicator
        self._color_indicator.setStyleSheet(
            f"background-color: {self._current_env.color}; "
            f"border: 1px solid {THEME.border}; border-radius: {RADIUS.sm}px;"
        )

        # Delete button only for custom environments
        self._delete_btn.setEnabled(is_custom)

        # Refresh variables table
        self._resolve_variables_with_inheritance()
        self._refresh_variables_table()

    def _resolve_variables_with_inheritance(self) -> None:
        """Resolve variables with inheritance chain."""
        if not self._current_env:
            self._resolved_variables = {}
            self._inherited_keys = set()
            return

        # Get inheritance chain
        chain: list[Environment] = []
        current_type = self._current_env.env_type

        # Build chain from base to current
        if current_type == EnvironmentType.PRODUCTION:
            chain = [e for e in self._environments if e.env_type == EnvironmentType.DEVELOPMENT]
            chain.extend(e for e in self._environments if e.env_type == EnvironmentType.STAGING)
            chain.append(self._current_env)
        elif current_type == EnvironmentType.STAGING:
            chain = [e for e in self._environments if e.env_type == EnvironmentType.DEVELOPMENT]
            chain.append(self._current_env)
        else:
            chain = [self._current_env]

        # Merge variables
        self._resolved_variables = {}
        self._inherited_keys = set()

        for env in chain:
            for key, value in env.variables.items():
                if env != self._current_env and key not in self._current_env.variables:
                    self._inherited_keys.add(key)
                self._resolved_variables[key] = value

    def _refresh_variables_table(self) -> None:
        """Refresh the variables table."""
        self._variables_table.blockSignals(True)
        self._variables_table.setRowCount(0)

        if not self._current_env:
            self._variables_table.blockSignals(False)
            return

        show_inherited = self._show_inherited_cb.isChecked()

        # Get all variable keys
        all_keys = set(self._resolved_variables.keys())
        local_keys = set(self._current_env.variables.keys())

        if not show_inherited:
            all_keys = local_keys

        for key in sorted(all_keys):
            value = self._resolved_variables.get(key, "")
            is_inherited = key in self._inherited_keys and key not in local_keys
            is_overridden = key in self._inherited_keys and key in local_keys

            row = self._variables_table.rowCount()
            self._variables_table.insertRow(row)

            # Name cell
            name_item = QTableWidgetItem(key)
            if is_inherited:
                name_item.setForeground(QColor(THEME.text_disabled))
                font = name_item.font()
                font.setItalic(True)
                name_item.setFont(font)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._variables_table.setItem(row, 0, name_item)

            # Value cell
            value_str = str(value) if value is not None else ""
            value_item = QTableWidgetItem(value_str)
            if is_inherited:
                value_item.setForeground(QColor(THEME.text_disabled))
                font = value_item.font()
                font.setItalic(True)
                value_item.setFont(font)
                value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            elif is_overridden:
                value_item.setBackground(QColor(THEME.bg_component))
            self._variables_table.setItem(row, 1, value_item)

            # Inherited checkbox
            inherited_item = QTableWidgetItem()
            inherited_item.setFlags(inherited_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if is_inherited:
                inherited_item.setCheckState(Qt.CheckState.Checked)
            else:
                inherited_item.setCheckState(Qt.CheckState.Unchecked)
            inherited_item.setFlags(inherited_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
            self._variables_table.setItem(row, 2, inherited_item)

            # Source cell
            source = self._get_variable_source(key)
            source_item = QTableWidgetItem(source)
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            source_item.setForeground(QColor(THEME.text_disabled))
            self._variables_table.setItem(row, 3, source_item)

        self._variables_table.blockSignals(False)

    def _get_variable_source(self, key: str) -> str:
        """Get the source environment for a variable."""
        if not self._current_env:
            return "Unknown"

        # Check if it's local
        if key in self._current_env.variables:
            return self._current_env.name

        # Check inheritance chain
        current_type = self._current_env.env_type

        if current_type == EnvironmentType.PRODUCTION:
            # Check staging
            staging = next(
                (e for e in self._environments if e.env_type == EnvironmentType.STAGING),
                None,
            )
            if staging and key in staging.variables:
                return staging.name

            # Check dev
            dev = next(
                (e for e in self._environments if e.env_type == EnvironmentType.DEVELOPMENT),
                None,
            )
            if dev and key in dev.variables:
                return dev.name

        elif current_type == EnvironmentType.STAGING:
            # Check dev
            dev = next(
                (e for e in self._environments if e.env_type == EnvironmentType.DEVELOPMENT),
                None,
            )
            if dev and key in dev.variables:
                return dev.name

        return "Unknown"

    def _on_name_changed(self, text: str) -> None:
        """Handle environment name change."""
        if self._current_env and self._current_env.env_type == EnvironmentType.CUSTOM:
            self._current_env.name = text
            self._current_env.touch_modified()

    def _on_description_changed(self) -> None:
        """Handle environment description change."""
        if self._current_env:
            self._current_env.description = self._env_description.toPlainText()
            self._current_env.touch_modified()

    def _on_variable_selection_changed(self) -> None:
        """Handle variable selection change."""
        selected = self._variables_table.selectedItems()
        if selected:
            row = selected[0].row()
            # Check if it's an inherited variable
            inherited_item = self._variables_table.item(row, 2)
            is_inherited = inherited_item and inherited_item.checkState() == Qt.CheckState.Checked
            self._delete_var_btn.setEnabled(not is_inherited)
        else:
            self._delete_var_btn.setEnabled(False)

    def _on_variable_cell_changed(self, row: int, column: int) -> None:
        """Handle variable cell edit."""
        if not self._current_env:
            return

        # Only process name (0) and value (1) columns
        if column not in (0, 1):
            return

        name_item = self._variables_table.item(row, 0)
        value_item = self._variables_table.item(row, 1)

        if not name_item or not value_item:
            return

        key = name_item.text().strip()
        value = value_item.text()

        if not key:
            return

        # Update environment variables
        self._current_env.variables[key] = value
        self._current_env.touch_modified()

        # Update resolution
        self._resolve_variables_with_inheritance()

    def _add_variable(self) -> None:
        """Add a new variable."""
        if not self._current_env:
            return

        name, ok = QInputDialog.getText(
            self,
            "Add Variable",
            "Variable name:",
            QLineEdit.EchoMode.Normal,
            "",
        )

        if ok and name:
            name = name.strip()
            if not name:
                return

            if name in self._current_env.variables:
                QMessageBox.warning(
                    self,
                    "Variable Exists",
                    f"Variable '{name}' already exists in this environment.",
                )
                return

            # Add variable
            self._current_env.variables[name] = ""
            self._current_env.touch_modified()

            # Refresh
            self._resolve_variables_with_inheritance()
            self._refresh_variables_table()

            self.environment_changed.emit(self._current_env.id)

    def _delete_variable(self) -> None:
        """Delete selected variable."""
        if not self._current_env:
            return

        selected = self._variables_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        name_item = self._variables_table.item(row, 0)
        if not name_item:
            return

        key = name_item.text()

        # Cannot delete inherited variables
        if key not in self._current_env.variables:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Cannot delete inherited variables. Override them instead.",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete variable '{key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            del self._current_env.variables[key]
            self._current_env.touch_modified()

            self._resolve_variables_with_inheritance()
            self._refresh_variables_table()

            self.environment_changed.emit(self._current_env.id)

    def _add_custom_environment(self) -> None:
        """Add a new custom environment."""
        name, ok = QInputDialog.getText(
            self,
            "New Custom Environment",
            "Environment name:",
            QLineEdit.EchoMode.Normal,
            "Custom Environment",
        )

        if ok and name:
            name = name.strip()
            if not name:
                return

            # Check for duplicates
            if any(e.name.lower() == name.lower() for e in self._environments):
                QMessageBox.warning(
                    self,
                    "Name Exists",
                    f"Environment '{name}' already exists.",
                )
                return

            # Create new environment
            new_env = Environment(
                id=generate_environment_id(),
                name=name,
                env_type=EnvironmentType.CUSTOM,
                description=f"Custom environment: {name}",
                is_default=False,
            )

            self._environments.append(new_env)

            # Save if project available
            if self._project and hasattr(self._project, "environments_dir"):
                try:
                    from casare_rpa.infrastructure.persistence.environment_storage import (
                        EnvironmentStorage,
                    )

                    EnvironmentStorage.save_environment(new_env, self._project.environments_dir)
                except Exception as e:
                    logger.error(f"Failed to save new environment: {e}")

            # Reload list
            self._load_environments()

            # Select new environment
            for i in range(self._env_list.count()):
                item = self._env_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == new_env.id:
                    self._env_list.setCurrentItem(item)
                    self._on_environment_selected(item)
                    break

            self.environment_created.emit(new_env.id)

    def _clone_environment(self) -> None:
        """Clone the current environment."""
        if not self._current_env:
            return

        name, ok = QInputDialog.getText(
            self,
            "Clone Environment",
            "New environment name:",
            QLineEdit.EchoMode.Normal,
            f"{self._current_env.name} (Copy)",
        )

        if ok and name:
            name = name.strip()
            if not name:
                return

            # Check for duplicates
            if any(e.name.lower() == name.lower() for e in self._environments):
                QMessageBox.warning(
                    self,
                    "Name Exists",
                    f"Environment '{name}' already exists.",
                )
                return

            # Create clone
            clone = Environment(
                id=generate_environment_id(),
                name=name,
                env_type=EnvironmentType.CUSTOM,
                description=f"Cloned from {self._current_env.name}",
                variables=self._current_env.variables.copy(),
                credential_overrides=self._current_env.credential_overrides.copy(),
                is_default=False,
            )

            self._environments.append(clone)

            # Save if project available
            if self._project and hasattr(self._project, "environments_dir"):
                try:
                    from casare_rpa.infrastructure.persistence.environment_storage import (
                        EnvironmentStorage,
                    )

                    EnvironmentStorage.save_environment(clone, self._project.environments_dir)
                except Exception as e:
                    logger.error(f"Failed to save cloned environment: {e}")

            # Reload list
            self._load_environments()

            # Select cloned environment
            for i in range(self._env_list.count()):
                item = self._env_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == clone.id:
                    self._env_list.setCurrentItem(item)
                    self._on_environment_selected(item)
                    break

            self.environment_created.emit(clone.id)

    def _delete_environment(self) -> None:
        """Delete the current environment."""
        if not self._current_env:
            return

        # Cannot delete standard environments
        if self._current_env.env_type != EnvironmentType.CUSTOM:
            QMessageBox.warning(
                self,
                "Cannot Delete",
                "Cannot delete standard environments (Development, Staging, Production).",
            )
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Delete environment '{self._current_env.name}'?\n\n" "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            env_id = self._current_env.id

            # Remove from list
            self._environments = [e for e in self._environments if e.id != env_id]

            # Delete from storage if project available
            if self._project and hasattr(self._project, "environments_dir"):
                try:
                    from casare_rpa.infrastructure.persistence.environment_storage import (
                        EnvironmentStorage,
                    )

                    EnvironmentStorage.delete_environment(env_id, self._project.environments_dir)
                except Exception as e:
                    logger.error(f"Failed to delete environment: {e}")

            self._current_env = None

            # Reload list
            self._load_environments()

            self.environment_deleted.emit(env_id)

    def _set_active_environment(self) -> None:
        """Set current environment as active."""
        if not self._current_env:
            return

        if self._project and hasattr(self._project, "active_environment_id"):
            self._project.active_environment_id = self._current_env.id

        # Reload to update active indicator
        self._load_environments()

        QMessageBox.information(
            self,
            "Active Environment",
            f"'{self._current_env.name}' is now the active environment.",
        )

        self.environment_changed.emit(self._current_env.id)

    def _save_and_close(self) -> None:
        """Save all changes and close."""
        if self._project and hasattr(self._project, "environments_dir"):
            try:
                from casare_rpa.infrastructure.persistence.environment_storage import (
                    EnvironmentStorage,
                )

                for env in self._environments:
                    EnvironmentStorage.save_environment(env, self._project.environments_dir)

                logger.info(f"Saved {len(self._environments)} environments")

            except Exception as e:
                logger.error(f"Failed to save environments: {e}")
                QMessageBox.critical(
                    self,
                    "Save Error",
                    f"Failed to save environments: {e}",
                )
                return

        self.accept()

    def _apply_styles(self) -> None:
        """Apply dark theme styles."""
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                margin-top: {SPACING.sm}px;
                padding-top: {SPACING.xl}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 {SPACING.xs}px;
            }}
            QLineEdit, QTextEdit {{
                background-color: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.text_primary};
            }}
            QLineEdit:focus, QTextEdit:focus {{
                border: 1px solid {THEME.border_focus};
            }}
            QLineEdit:disabled {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_disabled};
            }}
            QPushButton {{
                background-color: {THEME.primary};
                color: white;
                border: none;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.xl}px;
                border-radius: {TOKENS.radius.md}px;
                min-height: 28px;
            }}
            QPushButton:hover {{
                background-color: {THEME.primary_hover};
            }}
            QPushButton:pressed {{
                background-color: {THEME.bg_selected};
            }}
            QPushButton:disabled {{
                background-color: {THEME.input_bg};
                color: {THEME.text_disabled};
            }}
            QListWidget {{
                background-color: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.sm}px;
                border-bottom: 1px solid {THEME.bg_surface};
            }}
            QListWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QListWidget::item:hover {{
                background-color: {THEME.bg_hover};
            }}
            QTableWidget {{
                background-color: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                gridline-color: {THEME.border};
            }}
            QTableWidget::item {{
                padding: {TOKENS.spacing.xs}px {SPACING.sm}px;
            }}
            QTableWidget::item:selected {{
                background-color: {THEME.bg_selected};
            }}
            QHeaderView::section {{
                background-color: {THEME.bg_surface};
                color: {THEME.text_primary};
                padding: {TOKENS.spacing.sm}px;
                border: none;
                border-bottom: 1px solid {THEME.border};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {THEME.border};
                background-color: {THEME.input_bg};
                border-radius: {RADIUS.sm}px;
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {THEME.border_focus};
                background-color: {THEME.border_focus};
                border-radius: {RADIUS.sm}px;
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QSplitter::handle {{
                background-color: {THEME.border};
            }}
            QDialogButtonBox QPushButton {{
                min-width: 80px;
            }}
        """
        )


def show_environment_editor(
    project: Any | None = None,
    parent: QWidget | None = None,
) -> str | None:
    """
    Show environment editor dialog.

    Args:
        project: Current project
        parent: Parent widget

    Returns:
        Active environment ID if dialog accepted, None if cancelled
    """
    dialog = EnvironmentEditorDialog(project=project, parent=parent)
    result = dialog.exec()

    if result == QDialog.DialogCode.Accepted:
        if project and hasattr(project, "active_environment_id"):
            return project.active_environment_id
    return None
