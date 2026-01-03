"""
Preferences Dialog UI Component.

Epic 7.x - Migrated to BaseDialogV2 with THEME_V2/TOKENS_V2.

Modal dialog for editing application-wide preferences and settings.
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.dialogs_v2 import (
    BaseDialogV2,
    DialogSizeV2,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget import (
    AISettingsWidget,
)


class PreferencesDialog(BaseDialogV2):
    """
    Application preferences dialog.

    Migrated to BaseDialogV2 (Epic 7.x).

    Features:
    - General settings (theme, language)
    - Autosave settings
    - Editor settings
    - Performance settings

    Signals:
        preferences_changed: Emitted when preferences are saved (dict: preferences)
    """

    preferences_changed = Signal(dict)

    def __init__(
        self,
        preferences: dict[str, Any] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize preferences dialog.

        Args:
            preferences: Current preferences
            parent: Optional parent widget
        """
        self.preferences = preferences or {}

        super().__init__(
            title="Preferences",
            parent=parent,
            size=DialogSizeV2.MD,
        )

        self._setup_content()
        self._load_preferences()

        logger.debug("PreferencesDialog opened")

    def _setup_content(self) -> None:
        """Set up the dialog content."""
        # Main content widget with tabs
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Create tab widget
        self._tabs = QTabWidget()

        # General settings tab
        general_tab = self._create_general_tab()
        self._tabs.addTab(general_tab, "General")

        # Autosave settings tab
        autosave_tab = self._create_autosave_tab()
        self._tabs.addTab(autosave_tab, "Autosave")

        # Editor settings tab
        editor_tab = self._create_editor_tab()
        self._tabs.addTab(editor_tab, "Editor")

        # Performance settings tab
        performance_tab = self._create_performance_tab()
        self._tabs.addTab(performance_tab, "Performance")

        # AI settings tab
        ai_tab = self._create_ai_tab()
        self._tabs.addTab(ai_tab, "AI")

        layout.addWidget(self._tabs)

        # Set content and buttons
        self.set_body_widget(content)
        self.set_primary_button("Save", self._on_ok)
        self.set_secondary_button("Cancel", self.reject)

    def _create_general_tab(self) -> QWidget:
        """
        Create general settings tab.

        Returns:
            General tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # General settings group
        general_group = QGroupBox("General")
        general_group.setStyleSheet(self._get_group_box_style())
        general_layout = QFormLayout()

        # Theme setting
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light", "Auto"])
        self._theme_combo.setCurrentText("Dark")
        self._theme_combo.setStyleSheet(self._get_combo_style())
        general_layout.addRow("Theme:", self._theme_combo)

        # Language setting
        self._language_combo = QComboBox()
        self._language_combo.addItems(["English", "Spanish", "French", "German"])
        self._language_combo.setStyleSheet(self._get_combo_style())
        general_layout.addRow("Language:", self._language_combo)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Startup settings
        startup_group = QGroupBox("Startup")
        startup_group.setStyleSheet(self._get_group_box_style())
        startup_layout = QVBoxLayout()

        self._restore_session = QCheckBox("Restore previous session on startup")
        self._restore_session.setChecked(True)
        self._restore_session.setStyleSheet(self._get_checkbox_style())
        startup_layout.addWidget(self._restore_session)

        self._check_updates = QCheckBox("Check for updates on startup")
        self._check_updates.setChecked(True)
        self._check_updates.setStyleSheet(self._get_checkbox_style())
        startup_layout.addWidget(self._check_updates)

        startup_group.setLayout(startup_layout)
        layout.addWidget(startup_group)

        layout.addStretch()

        return widget

    def _create_autosave_tab(self) -> QWidget:
        """
        Create autosave settings tab.

        Returns:
            Autosave tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Autosave group
        autosave_group = QGroupBox("Autosave Settings")
        autosave_group.setStyleSheet(self._get_group_box_style())
        autosave_layout = QFormLayout()

        # Enable autosave checkbox
        self._autosave_enabled = QCheckBox()
        self._autosave_enabled.setChecked(True)
        self._autosave_enabled.setStyleSheet(self._get_checkbox_style())
        autosave_layout.addRow("Enable Autosave:", self._autosave_enabled)

        # Autosave interval
        self._autosave_interval = QSpinBox()
        self._autosave_interval.setMinimum(1)
        self._autosave_interval.setMaximum(60)
        self._autosave_interval.setValue(5)
        self._autosave_interval.setSuffix(" minute(s)")
        self._autosave_interval.setToolTip("How often to automatically save")
        self._autosave_interval.setStyleSheet(self._get_spin_box_style())
        autosave_layout.addRow("Save Interval:", self._autosave_interval)

        # Create backup copies
        self._create_backups = QCheckBox()
        self._create_backups.setChecked(True)
        self._create_backups.setStyleSheet(self._get_checkbox_style())
        autosave_layout.addRow("Create Backups:", self._create_backups)

        # Max backup files
        self._max_backups = QSpinBox()
        self._max_backups.setMinimum(1)
        self._max_backups.setMaximum(20)
        self._max_backups.setValue(5)
        self._max_backups.setSuffix(" file(s)")
        self._max_backups.setStyleSheet(self._get_spin_box_style())
        autosave_layout.addRow("Max Backups:", self._max_backups)

        # Add info label
        info_label = QLabel(
            "Autosave only works for workflows that have been saved at least once.\n"
            "New workflows must be manually saved first."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"""
            color: {THEME_V2.text_muted};
            font-size: {TOKENS_V2.typography.caption}px;
        """)
        autosave_layout.addRow("", info_label)

        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)

        layout.addStretch()

        return widget

    def _create_editor_tab(self) -> QWidget:
        """
        Create editor settings tab.

        Returns:
            Editor tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Grid settings
        grid_group = QGroupBox("Grid")
        grid_group.setStyleSheet(self._get_group_box_style())
        grid_layout = QFormLayout()

        self._show_grid = QCheckBox()
        self._show_grid.setChecked(True)
        self._show_grid.setStyleSheet(self._get_checkbox_style())
        grid_layout.addRow("Show Grid:", self._show_grid)

        self._snap_to_grid = QCheckBox()
        self._snap_to_grid.setChecked(True)
        self._snap_to_grid.setStyleSheet(self._get_checkbox_style())
        grid_layout.addRow("Snap to Grid:", self._snap_to_grid)

        self._grid_size = QSpinBox()
        self._grid_size.setMinimum(5)
        self._grid_size.setMaximum(100)
        self._grid_size.setValue(20)
        self._grid_size.setSuffix(" px")
        self._grid_size.setStyleSheet(self._get_spin_box_style())
        grid_layout.addRow("Grid Size:", self._grid_size)

        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)

        # Node settings
        node_group = QGroupBox("Nodes")
        node_group.setStyleSheet(self._get_group_box_style())
        node_layout = QFormLayout()

        self._auto_align = QCheckBox()
        self._auto_align.setChecked(False)
        self._auto_align.setStyleSheet(self._get_checkbox_style())
        node_layout.addRow("Auto-align Nodes:", self._auto_align)

        self._show_node_ids = QCheckBox()
        self._show_node_ids.setChecked(False)
        self._show_node_ids.setStyleSheet(self._get_checkbox_style())
        node_layout.addRow("Show Node IDs:", self._show_node_ids)

        node_group.setLayout(node_layout)
        layout.addWidget(node_group)

        # Connection settings
        conn_group = QGroupBox("Connections")
        conn_group.setStyleSheet(self._get_group_box_style())
        conn_layout = QFormLayout()

        self._connection_style = QComboBox()
        self._connection_style.addItems(["Curved", "Straight", "Manhattan"])
        self._connection_style.setStyleSheet(self._get_combo_style())
        conn_layout.addRow("Connection Style:", self._connection_style)

        self._show_port_labels = QCheckBox()
        self._show_port_labels.setChecked(True)
        self._show_port_labels.setStyleSheet(self._get_checkbox_style())
        conn_layout.addRow("Show Port Labels:", self._show_port_labels)

        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)

        layout.addStretch()

        return widget

    def _create_performance_tab(self) -> QWidget:
        """
        Create performance settings tab.

        Returns:
            Performance tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Rendering settings
        render_group = QGroupBox("Rendering")
        render_group.setStyleSheet(self._get_group_box_style())
        render_layout = QFormLayout()

        self._enable_antialiasing = QCheckBox()
        self._enable_antialiasing.setChecked(True)
        self._enable_antialiasing.setStyleSheet(self._get_checkbox_style())
        render_layout.addRow("Antialiasing:", self._enable_antialiasing)

        self._enable_shadows = QCheckBox()
        self._enable_shadows.setChecked(False)
        self._enable_shadows.setStyleSheet(self._get_checkbox_style())
        render_layout.addRow("Node Shadows:", self._enable_shadows)

        self._fps_limit = QSpinBox()
        self._fps_limit.setMinimum(30)
        self._fps_limit.setMaximum(144)
        self._fps_limit.setValue(60)
        self._fps_limit.setSuffix(" FPS")
        self._fps_limit.setStyleSheet(self._get_spin_box_style())
        render_layout.addRow("FPS Limit:", self._fps_limit)

        render_group.setLayout(render_layout)
        layout.addWidget(render_group)

        # Memory settings
        memory_group = QGroupBox("Memory")
        memory_group.setStyleSheet(self._get_group_box_style())
        memory_layout = QFormLayout()

        self._max_undo_steps = QSpinBox()
        self._max_undo_steps.setMinimum(10)
        self._max_undo_steps.setMaximum(1000)
        self._max_undo_steps.setValue(100)
        self._max_undo_steps.setSuffix(" steps")
        self._max_undo_steps.setStyleSheet(self._get_spin_box_style())
        memory_layout.addRow("Max Undo Steps:", self._max_undo_steps)

        self._cache_size = QSpinBox()
        self._cache_size.setMinimum(50)
        self._cache_size.setMaximum(1000)
        self._cache_size.setValue(200)
        self._cache_size.setSuffix(" MB")
        self._cache_size.setStyleSheet(self._get_spin_box_style())
        memory_layout.addRow("Cache Size:", self._cache_size)

        memory_group.setLayout(memory_layout)
        layout.addWidget(memory_group)

        layout.addStretch()

        return widget

    def _create_ai_tab(self) -> QWidget:
        """
        Create AI settings tab.

        Returns:
            AI tab widget
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # AI Settings Widget
        self._ai_settings = AISettingsWidget(
            title="AI Configuration",
            show_credential=True,
            show_provider=True,
            show_model=True,
        )
        layout.addWidget(self._ai_settings)
        layout.addStretch()

        return widget

    def _get_group_box_style(self) -> str:
        """Get QGroupBox styling."""
        return f"""
            QGroupBox {{
                font-weight: {TOKENS_V2.typography.weight_semibold};
                font-size: {TOKENS_V2.typography.body}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                margin-top: {TOKENS_V2.spacing.lg}px;
                padding-top: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS_V2.spacing.lg}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
            }}
        """

    def _get_combo_style(self) -> str:
        """Get QComboBox styling."""
        return f"""
            QComboBox {{
                background: {THEME_V2.input_bg};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QComboBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """

    def _get_spin_box_style(self) -> str:
        """Get QSpinBox styling."""
        return f"""
            QSpinBox {{
                background: {THEME_V2.input_bg};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.md}px;
                padding: {TOKENS_V2.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QSpinBox:focus {{
                border-color: {THEME_V2.border_focus};
            }}
        """

    def _get_checkbox_style(self) -> str:
        """Get QCheckBox styling."""
        return f"""
            QCheckBox {{
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                spacing: {TOKENS_V2.spacing.sm}px;
            }}
        """

    def _load_preferences(self) -> None:
        """Load current preferences into widgets."""
        # General
        if "theme" in self.preferences:
            self._theme_combo.setCurrentText(str(self.preferences["theme"]))

        if "language" in self.preferences:
            self._language_combo.setCurrentText(str(self.preferences["language"]))

        if "restore_session" in self.preferences:
            self._restore_session.setChecked(bool(self.preferences["restore_session"]))

        if "check_updates" in self.preferences:
            self._check_updates.setChecked(bool(self.preferences["check_updates"]))

        # Autosave
        if "autosave_enabled" in self.preferences:
            self._autosave_enabled.setChecked(bool(self.preferences["autosave_enabled"]))

        if "autosave_interval" in self.preferences:
            self._autosave_interval.setValue(int(self.preferences["autosave_interval"]))

        if "create_backups" in self.preferences:
            self._create_backups.setChecked(bool(self.preferences["create_backups"]))

        if "max_backups" in self.preferences:
            self._max_backups.setValue(int(self.preferences["max_backups"]))

        # Editor
        if "show_grid" in self.preferences:
            self._show_grid.setChecked(bool(self.preferences["show_grid"]))

        if "snap_to_grid" in self.preferences:
            self._snap_to_grid.setChecked(bool(self.preferences["snap_to_grid"]))

        if "grid_size" in self.preferences:
            self._grid_size.setValue(int(self.preferences["grid_size"]))

        if "auto_align" in self.preferences:
            self._auto_align.setChecked(bool(self.preferences["auto_align"]))

        if "show_node_ids" in self.preferences:
            self._show_node_ids.setChecked(bool(self.preferences["show_node_ids"]))

        if "connection_style" in self.preferences:
            self._connection_style.setCurrentText(str(self.preferences["connection_style"]))

        if "show_port_labels" in self.preferences:
            self._show_port_labels.setChecked(bool(self.preferences["show_port_labels"]))

        # Performance
        if "enable_antialiasing" in self.preferences:
            self._enable_antialiasing.setChecked(bool(self.preferences["enable_antialiasing"]))

        if "enable_shadows" in self.preferences:
            self._enable_shadows.setChecked(bool(self.preferences["enable_shadows"]))

        if "fps_limit" in self.preferences:
            self._fps_limit.setValue(int(self.preferences["fps_limit"]))

        if "max_undo_steps" in self.preferences:
            self._max_undo_steps.setValue(int(self.preferences["max_undo_steps"]))

        if "cache_size" in self.preferences:
            self._cache_size.setValue(int(self.preferences["cache_size"]))

        # AI
        if "ai_settings" in self.preferences:
            self._ai_settings.set_settings(self.preferences["ai_settings"])

    def _gather_preferences(self) -> dict[str, Any]:
        """
        Gather preferences from widgets.

        Returns:
            Dictionary of all preferences
        """
        preferences = {}

        # General
        preferences["theme"] = self._theme_combo.currentText()
        preferences["language"] = self._language_combo.currentText()
        preferences["restore_session"] = self._restore_session.isChecked()
        preferences["check_updates"] = self._check_updates.isChecked()

        # Autosave
        preferences["autosave_enabled"] = self._autosave_enabled.isChecked()
        preferences["autosave_interval"] = self._autosave_interval.value()
        preferences["create_backups"] = self._create_backups.isChecked()
        preferences["max_backups"] = self._max_backups.value()

        # Editor
        preferences["show_grid"] = self._show_grid.isChecked()
        preferences["snap_to_grid"] = self._snap_to_grid.isChecked()
        preferences["grid_size"] = self._grid_size.value()
        preferences["auto_align"] = self._auto_align.isChecked()
        preferences["show_node_ids"] = self._show_node_ids.isChecked()
        preferences["connection_style"] = self._connection_style.currentText()
        preferences["show_port_labels"] = self._show_port_labels.isChecked()

        # Performance
        preferences["enable_antialiasing"] = self._enable_antialiasing.isChecked()
        preferences["enable_shadows"] = self._enable_shadows.isChecked()
        preferences["fps_limit"] = self._fps_limit.value()
        preferences["max_undo_steps"] = self._max_undo_steps.value()
        preferences["cache_size"] = self._cache_size.value()

        # AI
        preferences["ai_settings"] = self._ai_settings.get_settings()

        return preferences

    def _on_ok(self) -> None:
        """Handle OK button click."""
        self._apply_preferences()
        self.accept()

    def _apply_preferences(self) -> None:
        """Apply preferences and emit signal."""
        preferences = self._gather_preferences()
        self.preferences_changed.emit(preferences)
        logger.debug("Preferences applied")

    def get_preferences(self) -> dict[str, Any]:
        """
        Get the current preferences.

        Returns:
            Dictionary of preferences
        """
        return self._gather_preferences()

