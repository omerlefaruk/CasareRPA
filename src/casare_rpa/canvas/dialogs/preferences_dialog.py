"""
CasareRPA - Preferences Dialog
Application settings dialog.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QDialogButtonBox,
)
from loguru import logger

from ...utils.settings_manager import get_settings_manager


class PreferencesDialog(QDialog):
    """
    Application preferences dialog.

    Provides UI for configuring:
    - Autosave settings
    - Future settings...
    """

    def __init__(self, parent=None):
        """Initialize preferences dialog."""
        super().__init__(parent)

        self.setWindowTitle("Preferences")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)

        # Get settings manager
        self.settings = get_settings_manager()

        # Setup UI
        self._setup_ui()

        # Load current settings
        self._load_settings()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)

        # Create tab widget for different setting categories
        self.tabs = QTabWidget()

        # General settings tab
        general_tab = self._create_general_tab()
        self.tabs.addTab(general_tab, "General")

        # Autosave settings tab
        autosave_tab = self._create_autosave_tab()
        self.tabs.addTab(autosave_tab, "Autosave")

        layout.addWidget(self.tabs)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(
            self._on_apply
        )

        layout.addWidget(button_box)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # General settings group
        general_group = QGroupBox("General")
        general_layout = QFormLayout()

        # Theme setting (placeholder for future)
        self.theme_label = QLabel("Theme: Dark (default)")
        general_layout.addRow("Theme:", self.theme_label)

        general_group.setLayout(general_layout)
        layout.addWidget(general_group)

        # Add stretch to push everything to top
        layout.addStretch()

        return widget

    def _create_autosave_tab(self) -> QWidget:
        """Create autosave settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Autosave group
        autosave_group = QGroupBox("Autosave Settings")
        autosave_layout = QFormLayout()

        # Enable autosave checkbox
        self.autosave_enabled = QCheckBox()
        autosave_layout.addRow("Enable Autosave:", self.autosave_enabled)

        # Autosave interval
        interval_widget = QWidget()
        interval_layout = QHBoxLayout(interval_widget)
        interval_layout.setContentsMargins(0, 0, 0, 0)

        self.autosave_interval = QSpinBox()
        self.autosave_interval.setMinimum(1)
        self.autosave_interval.setMaximum(60)
        self.autosave_interval.setSuffix(" minute(s)")
        self.autosave_interval.setToolTip(
            "How often to automatically save (in minutes)"
        )

        interval_layout.addWidget(self.autosave_interval)
        interval_layout.addStretch()

        autosave_layout.addRow("Save Interval:", interval_widget)

        # Add info label
        info_label = QLabel(
            "Autosave only works for workflows that have been saved at least once.\n"
            "New workflows must be manually saved first."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        autosave_layout.addRow("", info_label)

        autosave_group.setLayout(autosave_layout)
        layout.addWidget(autosave_group)

        # Add stretch to push everything to top
        layout.addStretch()

        return widget

    def _load_settings(self):
        """Load current settings into UI."""
        # Autosave settings
        self.autosave_enabled.setChecked(self.settings.is_autosave_enabled())
        self.autosave_interval.setValue(self.settings.get_autosave_interval())

    def _save_settings(self):
        """Save settings from UI."""
        # Autosave settings
        self.settings.set_autosave_enabled(self.autosave_enabled.isChecked())
        self.settings.set_autosave_interval(self.autosave_interval.value())

        logger.info("Preferences saved")

    def _on_apply(self):
        """Handle Apply button click."""
        self._save_settings()

        # Notify user
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.information(
            self,
            "Settings Applied",
            "Settings have been saved. Some changes may require restarting the application.",
        )

    def _on_ok(self):
        """Handle OK button click."""
        self._save_settings()
        self.accept()
