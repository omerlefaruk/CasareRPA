"""
Workflow Settings Dialog UI Component.

Modal dialog for editing workflow-level settings and metadata.
"""

from typing import Optional, Any, Dict

from PySide6.QtWidgets import (
    QVBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QCheckBox,
    QComboBox,
    QDialogButtonBox,
    QGroupBox,
    QTabWidget,
    QWidget,
)
from PySide6.QtCore import Signal

from loguru import logger

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles,
    DialogSize,
    apply_dialog_style,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_dialog import AnimatedDialog


class WorkflowSettingsDialog(AnimatedDialog):
    """
    Dialog for editing workflow settings.

    Features:
    - Workflow metadata (name, description, author)
    - Execution settings
    - Variable defaults
    - Error handling configuration

    Signals:
        settings_changed: Emitted when settings are saved (dict: settings)
    """

    settings_changed = Signal(dict)

    def __init__(
        self,
        settings: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize workflow settings dialog.

        Args:
            settings: Current workflow settings
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.settings = settings or {}

        self.setWindowTitle("Workflow Settings")
        self.setModal(True)

        # Apply standardized dialog styling
        apply_dialog_style(self, DialogSize.MD)

        self._setup_ui()
        self._load_settings()

        logger.debug("WorkflowSettingsDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("Workflow Settings")
        header.setStyleSheet(DialogStyles.header(font_size=16))
        layout.addWidget(header)

        # Tabs
        self._tabs = QTabWidget()

        # General tab
        general_tab = self._create_general_tab()
        self._tabs.addTab(general_tab, "General")

        # Execution tab
        execution_tab = self._create_execution_tab()
        self._tabs.addTab(execution_tab, "Execution")

        # Variables tab
        variables_tab = self._create_variables_tab()
        self._tabs.addTab(variables_tab, "Variables")

        layout.addWidget(self._tabs)

        # Button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """
        Create general settings tab.

        Returns:
            General tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Metadata group
        meta_group = QGroupBox("Metadata")
        meta_layout = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Workflow name")
        meta_layout.addRow("Name:", self._name_edit)

        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Workflow description")
        self._description_edit.setMaximumHeight(100)
        meta_layout.addRow("Description:", self._description_edit)

        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("Author name")
        meta_layout.addRow("Author:", self._author_edit)

        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText("1.0.0")
        meta_layout.addRow("Version:", self._version_edit)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Tags group
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout()

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("comma, separated, tags")
        tags_layout.addWidget(self._tags_edit)

        tags_group.setLayout(tags_layout)
        layout.addWidget(tags_group)

        layout.addStretch()

        return widget

    def _create_execution_tab(self) -> QWidget:
        """
        Create execution settings tab.

        Returns:
            Execution tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Timeout settings
        timeout_group = QGroupBox("Timeout Settings")
        timeout_layout = QFormLayout()

        self._global_timeout_spin = QSpinBox()
        self._global_timeout_spin.setRange(0, 36000)
        self._global_timeout_spin.setSuffix(" seconds")
        self._global_timeout_spin.setSpecialValueText("No timeout")
        self._global_timeout_spin.setToolTip("Maximum workflow execution time")
        timeout_layout.addRow("Global Timeout:", self._global_timeout_spin)

        self._node_timeout_spin = QSpinBox()
        self._node_timeout_spin.setRange(0, 3600)
        self._node_timeout_spin.setSuffix(" seconds")
        self._node_timeout_spin.setSpecialValueText("No timeout")
        self._node_timeout_spin.setToolTip("Default timeout for individual nodes")
        timeout_layout.addRow("Node Timeout:", self._node_timeout_spin)

        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)

        # Error handling
        error_group = QGroupBox("Error Handling")
        error_layout = QFormLayout()

        self._stop_on_error = QCheckBox("Stop workflow on first error")
        self._stop_on_error.setChecked(True)
        error_layout.addRow("", self._stop_on_error)

        self._retry_failed = QCheckBox("Retry failed nodes automatically")
        error_layout.addRow("", self._retry_failed)

        self._max_retries_spin = QSpinBox()
        self._max_retries_spin.setRange(0, 10)
        self._max_retries_spin.setValue(3)
        error_layout.addRow("Max Retries:", self._max_retries_spin)

        error_group.setLayout(error_layout)
        layout.addWidget(error_group)

        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout()

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self._log_level_combo.setCurrentText("Info")
        log_layout.addRow("Log Level:", self._log_level_combo)

        self._save_logs = QCheckBox("Save execution logs to file")
        log_layout.addRow("", self._save_logs)

        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        layout.addStretch()

        return widget

    def _create_variables_tab(self) -> QWidget:
        """
        Create variables settings tab.

        Returns:
            Variables tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Variable scope
        scope_group = QGroupBox("Variable Scope")
        scope_layout = QVBoxLayout()

        self._inherit_variables = QCheckBox(
            "Inherit variables from parent workflow/scenario"
        )
        self._inherit_variables.setChecked(True)
        scope_layout.addWidget(self._inherit_variables)

        self._expose_variables = QCheckBox("Expose local variables to parent workflow")
        scope_layout.addWidget(self._expose_variables)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Variable initialization
        init_group = QGroupBox("Initialization")
        init_layout = QVBoxLayout()

        self._init_from_file = QCheckBox("Initialize variables from JSON file")
        init_layout.addWidget(self._init_from_file)

        init_label = QLabel(
            "Note: Initial variable values can be set in the Variables panel"
        )
        init_label.setWordWrap(True)
        init_label.setStyleSheet(DialogStyles.info_label())
        init_layout.addWidget(init_label)

        init_group.setLayout(init_layout)
        layout.addWidget(init_group)

        layout.addStretch()

        return widget

    def _load_settings(self) -> None:
        """Load current settings into widgets."""
        # General settings
        if "name" in self.settings:
            self._name_edit.setText(str(self.settings["name"]))

        if "description" in self.settings:
            self._description_edit.setPlainText(str(self.settings["description"]))

        if "author" in self.settings:
            self._author_edit.setText(str(self.settings["author"]))

        if "version" in self.settings:
            self._version_edit.setText(str(self.settings["version"]))

        if "tags" in self.settings:
            tags = self.settings["tags"]
            if isinstance(tags, list):
                self._tags_edit.setText(", ".join(tags))
            else:
                self._tags_edit.setText(str(tags))

        # Execution settings
        if "global_timeout" in self.settings:
            self._global_timeout_spin.setValue(int(self.settings["global_timeout"]))

        if "node_timeout" in self.settings:
            self._node_timeout_spin.setValue(int(self.settings["node_timeout"]))

        if "stop_on_error" in self.settings:
            self._stop_on_error.setChecked(bool(self.settings["stop_on_error"]))

        if "retry_failed" in self.settings:
            self._retry_failed.setChecked(bool(self.settings["retry_failed"]))

        if "max_retries" in self.settings:
            self._max_retries_spin.setValue(int(self.settings["max_retries"]))

        if "log_level" in self.settings:
            self._log_level_combo.setCurrentText(str(self.settings["log_level"]))

        if "save_logs" in self.settings:
            self._save_logs.setChecked(bool(self.settings["save_logs"]))

        # Variable settings
        if "inherit_variables" in self.settings:
            self._inherit_variables.setChecked(bool(self.settings["inherit_variables"]))

        if "expose_variables" in self.settings:
            self._expose_variables.setChecked(bool(self.settings["expose_variables"]))

        if "init_from_file" in self.settings:
            self._init_from_file.setChecked(bool(self.settings["init_from_file"]))

    def _gather_settings(self) -> Dict[str, Any]:
        """
        Gather settings from widgets.

        Returns:
            Dictionary of all settings
        """
        settings = {}

        # General
        settings["name"] = self._name_edit.text()
        settings["description"] = self._description_edit.toPlainText()
        settings["author"] = self._author_edit.text()
        settings["version"] = self._version_edit.text()
        tags_text = self._tags_edit.text()
        settings["tags"] = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

        # Execution
        settings["global_timeout"] = self._global_timeout_spin.value()
        settings["node_timeout"] = self._node_timeout_spin.value()
        settings["stop_on_error"] = self._stop_on_error.isChecked()
        settings["retry_failed"] = self._retry_failed.isChecked()
        settings["max_retries"] = self._max_retries_spin.value()
        settings["log_level"] = self._log_level_combo.currentText()
        settings["save_logs"] = self._save_logs.isChecked()

        # Variables
        settings["inherit_variables"] = self._inherit_variables.isChecked()
        settings["expose_variables"] = self._expose_variables.isChecked()
        settings["init_from_file"] = self._init_from_file.isChecked()

        return settings

    def _validate(self) -> bool:
        """
        Validate settings.

        Returns:
            True if validation passes
        """
        if not self._name_edit.text().strip():
            logger.warning("Workflow name cannot be empty")
            return False

        return True

    def _on_accept(self) -> None:
        """Handle dialog accept."""
        if not self._validate():
            return

        settings = self._gather_settings()
        self.settings_changed.emit(settings)
        self.accept()

        logger.debug("Workflow settings saved")

    def get_settings(self) -> Dict[str, Any]:
        """
        Get the current settings.

        Returns:
            Dictionary of settings
        """
        return self._gather_settings()
