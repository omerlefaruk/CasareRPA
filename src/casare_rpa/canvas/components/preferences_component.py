"""
Preferences management component.

This component handles user preferences and settings:
- Settings management
- Hotkey configuration
- Theme management
"""

from typing import TYPE_CHECKING
from loguru import logger

from .base_component import BaseComponent
from ...utils.settings_manager import get_settings_manager

if TYPE_CHECKING:
    from ..main_window import MainWindow


class PreferencesComponent(BaseComponent):
    """
    Manages user preferences and settings.

    Responsibilities:
    - Settings management
    - Hotkey configuration
    - Theme management
    - Preference persistence
    """

    def __init__(self, main_window: "MainWindow") -> None:
        super().__init__(main_window)
        self._settings_manager = None

    def _do_initialize(self) -> None:
        """Initialize the preferences component."""
        # Get settings manager instance
        self._settings_manager = get_settings_manager()

        # Connect signals
        self._main_window.preferences_saved.connect(self._on_preferences_saved)

        logger.info("PreferencesComponent initialized")

    def _on_preferences_saved(self) -> None:
        """Handle preferences saved event."""
        logger.info("Preferences saved, notifying components")
        # Settings are automatically persisted by SettingsManager
        # Other components can react to preferences_saved signal

    def get_settings_manager(self):
        """Get the settings manager instance."""
        return self._settings_manager

    def cleanup(self) -> None:
        """Cleanup resources."""
        logger.debug("PreferencesComponent cleaned up")
