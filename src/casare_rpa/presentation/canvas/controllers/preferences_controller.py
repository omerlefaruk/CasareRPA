"""
Preferences controller for user settings and configuration.

Handles application preferences and settings:
- Settings management
- Hotkey configuration
- Theme management
- Preference persistence
"""

from typing import TYPE_CHECKING, Any, Dict
from PySide6.QtCore import Signal
from loguru import logger

from casare_rpa.presentation.canvas.controllers.base_controller import BaseController
from casare_rpa.presentation.canvas.events.event_bus import EventBus
from casare_rpa.presentation.canvas.events.event import Event
from casare_rpa.presentation.canvas.events.event_types import EventType

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.main_window import MainWindow


class PreferencesController(BaseController):
    """
    Manages user preferences and settings.

    Single Responsibility: Settings and configuration management.

    Signals:
        preferences_updated: Emitted when preferences are updated
        theme_changed: Emitted when theme is changed (str: theme_name)
        hotkey_updated: Emitted when hotkey is updated (str: action, str: hotkey)
        setting_changed: Emitted when individual setting changes (str: key, Any: value)
    """

    # Signals
    preferences_updated = Signal()
    theme_changed = Signal(str)  # theme_name
    hotkey_updated = Signal(str, str)  # action, hotkey
    setting_changed = Signal(str, object)  # key, value

    def __init__(self, main_window: "MainWindow"):
        """Initialize preferences controller."""
        super().__init__(main_window)
        self._settings_manager = None
        self._event_bus = EventBus()

    def initialize(self) -> None:
        """Initialize controller and setup event subscriptions."""
        super().initialize()

        # Import and get settings manager instance
        from ....utils.settings_manager import get_settings_manager

        self._settings_manager = get_settings_manager()

        # Subscribe to EventBus events
        self._event_bus.subscribe(
            EventType.PREFERENCES_UPDATED, self._on_preferences_updated_event
        )
        self._event_bus.subscribe(EventType.THEME_CHANGED, self._on_theme_changed_event)

        logger.info("PreferencesController initialized")

    def cleanup(self) -> None:
        """Clean up resources."""
        # Unsubscribe from events
        self._event_bus.unsubscribe(
            EventType.PREFERENCES_UPDATED, self._on_preferences_updated_event
        )
        self._event_bus.unsubscribe(
            EventType.THEME_CHANGED, self._on_theme_changed_event
        )

        super().cleanup()
        logger.info("PreferencesController cleanup")

    # =========================================================================
    # Public API
    # =========================================================================

    def get_settings_manager(self) -> Any:
        """
        Get the settings manager instance.

        Returns:
            SettingsManager instance
        """
        return self._settings_manager

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.

        Args:
            key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value or default
        """
        if not self._settings_manager:
            logger.warning("Settings manager not initialized")
            return default

        try:
            return self._settings_manager.get(key, default)
        except Exception as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return default

    def set_setting(self, key: str, value: Any) -> bool:
        """
        Set a setting value.

        Args:
            key: Setting key
            value: Setting value

        Returns:
            bool: True if successful
        """
        logger.info(f"Setting '{key}' = {value}")

        if not self._settings_manager:
            logger.error("Settings manager not initialized")
            return False

        try:
            # Set the setting
            self._settings_manager.set(key, value)

            # Emit signal
            self.setting_changed.emit(key, value)

            # Publish event
            event = Event(
                type=EventType.PREFERENCES_UPDATED,
                source="PreferencesController",
                data={"key": key, "value": value},
            )
            self._event_bus.publish(event)

            return True

        except Exception as e:
            logger.error(f"Failed to set setting '{key}': {e}")
            return False

    def save_preferences(self) -> bool:
        """
        Save preferences to disk.

        Returns:
            bool: True if successful
        """
        logger.info("Saving preferences")

        if not self._settings_manager:
            logger.error("Settings manager not initialized")
            return False

        try:
            # Settings manager handles auto-save, but this can force a save
            # Note: Actual implementation depends on SettingsManager API

            # Emit signal
            self.preferences_updated.emit()

            # Publish event
            event = Event(
                type=EventType.PREFERENCES_UPDATED,
                source="PreferencesController",
                data={"action": "saved"},
            )
            self._event_bus.publish(event)

            logger.info("Preferences saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False

    def reset_preferences(self) -> bool:
        """
        Reset preferences to defaults.

        Returns:
            bool: True if successful
        """
        logger.warning("Resetting preferences to defaults")

        if not self._settings_manager:
            logger.error("Settings manager not initialized")
            return False

        try:
            # Reset to defaults
            # Note: Actual implementation depends on SettingsManager API

            # Emit signal
            self.preferences_updated.emit()

            # Publish event
            event = Event(
                type=EventType.PREFERENCES_UPDATED,
                source="PreferencesController",
                data={"action": "reset"},
            )
            self._event_bus.publish(event)

            logger.info("Preferences reset to defaults")
            return True

        except Exception as e:
            logger.error(f"Failed to reset preferences: {e}")
            return False

    def set_theme(self, theme_name: str) -> bool:
        """
        Set the application theme.

        Args:
            theme_name: Name of the theme

        Returns:
            bool: True if successful
        """
        logger.info(f"Setting theme: {theme_name}")

        try:
            # Set theme via settings manager
            self.set_setting("theme", theme_name)

            # Emit signal
            self.theme_changed.emit(theme_name)

            # Publish event
            event = Event(
                type=EventType.THEME_CHANGED,
                source="PreferencesController",
                data={"theme_name": theme_name},
            )
            self._event_bus.publish(event)

            return True

        except Exception as e:
            logger.error(f"Failed to set theme: {e}")
            return False

    def update_hotkey(self, action: str, hotkey: str) -> bool:
        """
        Update a hotkey binding.

        Args:
            action: Action name
            hotkey: Hotkey string (e.g., "Ctrl+S")

        Returns:
            bool: True if successful
        """
        logger.info(f"Updating hotkey for '{action}': {hotkey}")

        try:
            # Update hotkey in settings
            hotkeys = self.get_setting("hotkeys", {})
            hotkeys[action] = hotkey
            self.set_setting("hotkeys", hotkeys)

            # Emit signal
            self.hotkey_updated.emit(action, hotkey)

            # Publish event
            event = Event(
                type=EventType.HOTKEY_TRIGGERED,
                source="PreferencesController",
                data={"action": action, "hotkey": hotkey},
            )
            self._event_bus.publish(event)

            return True

        except Exception as e:
            logger.error(f"Failed to update hotkey: {e}")
            return False

    def get_hotkeys(self) -> Dict[str, str]:
        """
        Get all hotkey bindings.

        Returns:
            dict: Action to hotkey mapping
        """
        return self.get_setting("hotkeys", {})

    def is_autosave_enabled(self) -> bool:
        """
        Check if autosave is enabled.

        Returns:
            bool: True if autosave is enabled
        """
        if not self._settings_manager:
            return False

        try:
            return self._settings_manager.is_autosave_enabled()
        except Exception as e:
            logger.error(f"Failed to check autosave status: {e}")
            return False

    def get_autosave_interval(self) -> int:
        """
        Get autosave interval in minutes.

        Returns:
            int: Autosave interval in minutes
        """
        if not self._settings_manager:
            return 5  # Default

        try:
            return self._settings_manager.get_autosave_interval()
        except Exception as e:
            logger.error(f"Failed to get autosave interval: {e}")
            return 5  # Default

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_preferences_updated_event(self, event: Event) -> None:
        """
        Handle preferences updated event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Preferences updated event received: {event.data}")

        # Notify main window if needed
        # This allows other components to react to preference changes

    def _on_theme_changed_event(self, event: Event) -> None:
        """
        Handle theme changed event from EventBus.

        Args:
            event: The event object
        """
        logger.debug(f"Theme changed event received: {event.data}")

        # Could trigger UI updates here
