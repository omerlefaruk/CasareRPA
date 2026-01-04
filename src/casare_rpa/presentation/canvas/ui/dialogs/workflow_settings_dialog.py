"""
Workflow Settings Dialog UI Component.

Modal dialog for editing workflow-level settings and metadata.

Epic 7.x migration: Converted to use BaseDialogV2 and THEME_V2/TOKENS_V2.
"""

from __future__ import annotations

from typing import Any

from loguru import logger
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import BaseDialogV2, DialogSizeV2


class WorkflowSettingsDialog(BaseDialogV2):
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
        settings: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize workflow settings dialog.

        Args:
            settings: Current workflow settings
            parent: Optional parent widget
        """
        super().__init__(
            title="Workflow Settings",
            parent=parent,
            size=DialogSizeV2.LG,  # Larger for tabs content
        )

        self.settings = settings or {}

        self._setup_ui()
        self._load_settings()

        logger.debug("WorkflowSettingsDialog opened")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main content widget
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

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

        # Set as body widget
        self.set_body_widget(content)

        # Setup footer buttons
        self.set_primary_button("Save", self._on_accept)
        self.set_secondary_button("Cancel", self.reject)

    def _apply_tab_styles(self) -> None:
        """Apply v2 styling to tab widget."""
        t = THEME_V2
        tok = TOKENS_V2

        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid {t.border};
                background-color: {t.bg_surface};
                border-radius: {tok.radius.md}px;
            }}
            QTabBar::tab {{
                background-color: {t.bg_component};
                color: {t.text_primary};
                padding: {tok.spacing.sm}px {tok.spacing.md}px;
                border: 1px solid {t.border};
                border-bottom: none;
                border-top-left-radius: {tok.radius.sm}px;
                border-top-right-radius: {tok.radius.sm}px;
                margin-right: 2px;
                font-family: {tok.typography.family};
                font-size: {tok.typography.body}px;
            }}
            QTabBar::tab:selected {{
                background-color: {t.bg_surface};
                border-bottom: 2px solid {t.primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {t.bg_hover};
            }}
        """)

    def _create_general_tab(self) -> QWidget:
        """
        Create general settings tab.

        Returns:
            General tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Metadata group
        meta_group = QGroupBox("Metadata")
        self._apply_group_box_style(meta_group)
        meta_layout = QFormLayout()

        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Workflow name")
        self._apply_input_style(self._name_edit)
        meta_layout.addRow("Name:", self._name_edit)

        self._description_edit = QTextEdit()
        self._description_edit.setPlaceholderText("Workflow description")
        self._description_edit.setMaximumHeight(100)
        self._apply_text_edit_style(self._description_edit)
        meta_layout.addRow("Description:", self._description_edit)

        self._author_edit = QLineEdit()
        self._author_edit.setPlaceholderText("Author name")
        self._apply_input_style(self._author_edit)
        meta_layout.addRow("Author:", self._author_edit)

        self._version_edit = QLineEdit()
        self._version_edit.setPlaceholderText("1.0.0")
        self._apply_input_style(self._version_edit)
        meta_layout.addRow("Version:", self._version_edit)

        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # Tags group
        tags_group = QGroupBox("Tags")
        self._apply_group_box_style(tags_group)
        tags_layout = QVBoxLayout()

        self._tags_edit = QLineEdit()
        self._tags_edit.setPlaceholderText("comma, separated, tags")
        self._apply_input_style(self._tags_edit)
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
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Timeout settings
        timeout_group = QGroupBox("Timeout Settings")
        self._apply_group_box_style(timeout_group)
        timeout_layout = QFormLayout()

        self._global_timeout_spin = QSpinBox()
        self._global_timeout_spin.setRange(0, 36000)
        self._global_timeout_spin.setSuffix(" seconds")
        self._global_timeout_spin.setSpecialValueText("No timeout")
        self._global_timeout_spin.setToolTip("Maximum workflow execution time")
        self._apply_spin_box_style(self._global_timeout_spin)
        timeout_layout.addRow("Global Timeout:", self._global_timeout_spin)

        self._node_timeout_spin = QSpinBox()
        self._node_timeout_spin.setRange(0, 3600)
        self._node_timeout_spin.setSuffix(" seconds")
        self._node_timeout_spin.setSpecialValueText("No timeout")
        self._node_timeout_spin.setToolTip("Default timeout for individual nodes")
        self._apply_spin_box_style(self._node_timeout_spin)
        timeout_layout.addRow("Node Timeout:", self._node_timeout_spin)

        timeout_group.setLayout(timeout_layout)
        layout.addWidget(timeout_group)

        # Error handling
        error_group = QGroupBox("Error Handling")
        self._apply_group_box_style(error_group)
        error_layout = QFormLayout()

        self._stop_on_error = QCheckBox("Stop workflow on first error")
        self._stop_on_error.setChecked(True)
        self._apply_checkbox_style(self._stop_on_error)
        error_layout.addRow("", self._stop_on_error)

        self._retry_failed = QCheckBox("Retry failed nodes automatically")
        self._apply_checkbox_style(self._retry_failed)
        error_layout.addRow("", self._retry_failed)

        self._max_retries_spin = QSpinBox()
        self._max_retries_spin.setRange(0, 10)
        self._max_retries_spin.setValue(3)
        self._apply_spin_box_style(self._max_retries_spin)
        error_layout.addRow("Max Retries:", self._max_retries_spin)

        error_group.setLayout(error_layout)
        layout.addWidget(error_group)

        # Logging
        log_group = QGroupBox("Logging")
        self._apply_group_box_style(log_group)
        log_layout = QFormLayout()

        self._log_level_combo = QComboBox()
        self._log_level_combo.addItems(["Debug", "Info", "Warning", "Error"])
        self._log_level_combo.setCurrentText("Info")
        self._apply_combo_box_style(self._log_level_combo)
        log_layout.addRow("Log Level:", self._log_level_combo)

        self._save_logs = QCheckBox("Save execution logs to file")
        self._apply_checkbox_style(self._save_logs)
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
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Variable scope
        scope_group = QGroupBox("Variable Scope")
        self._apply_group_box_style(scope_group)
        scope_layout = QVBoxLayout()

        self._inherit_variables = QCheckBox("Inherit variables from parent workflow/scenario")
        self._inherit_variables.setChecked(True)
        self._apply_checkbox_style(self._inherit_variables)
        scope_layout.addWidget(self._inherit_variables)

        self._expose_variables = QCheckBox("Expose local variables to parent workflow")
        self._apply_checkbox_style(self._expose_variables)
        scope_layout.addWidget(self._expose_variables)

        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)

        # Variable initialization
        init_group = QGroupBox("Initialization")
        self._apply_group_box_style(init_group)
        init_layout = QVBoxLayout()

        self._init_from_file = QCheckBox("Initialize variables from JSON file")
        self._apply_checkbox_style(self._init_from_file)
        init_layout.addWidget(self._init_from_file)

        init_label = QLabel("Note: Initial variable values can be set in the Variables panel")
        init_label.setWordWrap(True)
        init_label.setStyleSheet(
            f"color: {THEME_V2.text_secondary}; font-size: {TOKENS_V2.typography.body_sm}px;"
        )
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

        # Apply widget styles after all widgets are created
        self._apply_tab_styles()

    def _gather_settings(self) -> dict[str, Any]:
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

    @Slot()
    def _on_accept(self) -> None:
        """Handle dialog accept."""
        if not self._validate():
            return

        settings = self._gather_settings()
        self.settings_changed.emit(settings)
        self.accept()

        logger.debug("Workflow settings saved")

    def get_settings(self) -> dict[str, Any]:
        """
        Get the current settings.

        Returns:
            Dictionary of settings
        """
        return self._gather_settings()

    # ========================================================================
    # WIDGET STYLING HELPERS (using THEME_V2/TOKENS_V2)
    # ========================================================================

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

    def _apply_text_edit_style(self, widget: QTextEdit) -> None:
        """Apply v2 text edit styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QTextEdit {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
            }}
            QTextEdit:focus {{
                border-color: {t.border_focus};
            }}
        """)

    def _apply_spin_box_style(self, widget: QSpinBox) -> None:
        """Apply v2 spin box styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QSpinBox {{
                background: {t.input_bg};
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.sm}px;
                padding: {tok.spacing.xs}px {tok.spacing.sm}px;
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                min-height: {tok.sizes.input_md}px;
            }}
            QSpinBox:focus {{
                border-color: {t.border_focus};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background: {t.bg_component};
                border: none;
                width: 16px;
            }}
        """)

    def _apply_combo_box_style(self, widget: QComboBox) -> None:
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

    def _apply_checkbox_style(self, widget: QCheckBox) -> None:
        """Apply v2 checkbox styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QCheckBox {{
                color: {t.text_primary};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                spacing: {tok.spacing.xs}px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 1px solid {t.input_border};
                border-radius: {tok.radius.xs}px;
                background: {t.input_bg};
            }}
            QCheckBox::indicator:unchecked:hover {{
                border-color: {t.border_focus};
            }}
            QCheckBox::indicator:checked {{
                border: 1px solid {t.primary};
                border-radius: {tok.radius.xs}px;
                background: {t.primary};
            }}
        """)

    def _apply_group_box_style(self, widget: QGroupBox) -> None:
        """Apply v2 group box styling."""
        t = THEME_V2
        tok = TOKENS_V2
        widget.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {tok.typography.weight_medium};
                font-size: {tok.typography.body}px;
                font-family: {tok.typography.family};
                border: 1px solid {t.border};
                border-radius: {tok.radius.md}px;
                margin-top: {tok.spacing.sm}px;
                padding-top: {tok.spacing.sm}px;
                background: {t.bg_surface};
                color: {t.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {tok.spacing.md}px;
                padding: 0 {tok.spacing.xs}px;
                color: {t.text_primary};
            }}
        """)
