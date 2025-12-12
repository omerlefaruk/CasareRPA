"""
CasareRPA - Settings Manager
Handles application settings persistence.
"""

import orjson
from typing import Any
from loguru import logger

from casare_rpa.config import CONFIG_DIR


class SettingsManager:
    """
    Manages application settings with JSON persistence.

    Settings are stored in config/settings.json
    """

    DEFAULT_SETTINGS = {
        "general": {
            "language": "English",
            "restore_session": True,
            "check_updates": True,
        },
        "autosave": {
            "enabled": True,
            "interval_minutes": 5,
            "create_backups": True,
            "max_backups": 5,
        },
        "ui": {
            "theme": "Dark",
            "show_minimap": True,
        },
        "editor": {
            "show_grid": True,
            "snap_to_grid": True,
            "grid_size": 20,
            "auto_align": False,
            "show_node_ids": False,
            "connection_style": "Curved",
            "show_port_labels": True,
        },
        "performance": {
            "antialiasing": True,
            "shadows": False,
            "fps_limit": 60,
            "max_undo_steps": 100,
            "cache_size_mb": 200,
        },
        "ai": {
            "provider": "OpenAI",
            "model": "gpt-4o-mini",
            "credential_id": "auto",
            "debug_mode": False,
        },
    }

    def __init__(self):
        """Initialize settings manager."""
        self.settings_file = CONFIG_DIR / "settings.json"
        self.settings = self._load_settings()

    def _load_settings(self) -> dict:
        """
        Load settings from JSON file.

        Returns:
            Settings dictionary
        """
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "rb") as f:
                    settings = orjson.loads(f.read())
                    logger.debug(f"Loaded settings from {self.settings_file}")

                    # Merge with defaults to handle new settings
                    merged = self._merge_with_defaults(settings)
                    return merged
            else:
                logger.info("Settings file not found, using defaults")
                return self.DEFAULT_SETTINGS.copy()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            return self.DEFAULT_SETTINGS.copy()

    def _merge_with_defaults(self, settings: dict) -> dict:
        """
        Merge loaded settings with defaults to handle new settings.

        Args:
            settings: Loaded settings

        Returns:
            Merged settings
        """
        merged = self.DEFAULT_SETTINGS.copy()

        # Deep merge
        for key, value in settings.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key].update(value)
            else:
                merged[key] = value

        return merged

    def save_settings(self) -> None:
        """Save settings to JSON file."""
        try:
            # Ensure config directory exists
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)

            # Write settings
            with open(self.settings_file, "wb") as f:
                f.write(orjson.dumps(self.settings, option=orjson.OPT_INDENT_2))
            logger.debug(f"Saved settings to {self.settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation.

        Args:
            key: Setting key (e.g., "autosave.enabled")
            default: Default value if key not found

        Returns:
            Setting value
        """
        keys = key.split(".")
        value = self.settings

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value using dot notation.

        Args:
            key: Setting key (e.g., "autosave.enabled")
            value: Value to set
        """
        keys = key.split(".")
        target = self.settings

        # Navigate to the parent dict
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set the value
        target[keys[-1]] = value

        # Auto-save settings
        self.save_settings()

    # Convenience methods for autosave settings

    def is_autosave_enabled(self) -> bool:
        """Check if autosave is enabled."""
        return self.get("autosave.enabled", True)

    def get_autosave_interval(self) -> int:
        """Get autosave interval in minutes."""
        return self.get("autosave.interval_minutes", 5)

    def set_autosave_enabled(self, enabled: bool) -> None:
        """Enable or disable autosave."""
        self.set("autosave.enabled", enabled)

    def set_autosave_interval(self, minutes: int) -> None:
        """Set autosave interval in minutes."""
        if minutes < 1:
            minutes = 1
        self.set("autosave.interval_minutes", minutes)


# Thread-safe singleton holder
from casare_rpa.application.dependency_injection.singleton import Singleton

_settings_manager_holder = Singleton(SettingsManager, name="SettingsManager")


def get_settings_manager() -> SettingsManager:
    """
    Get the global settings manager instance.

    Returns:
        SettingsManager instance
    """
    return _settings_manager_holder.get()


def reset_settings_manager() -> None:
    """Reset the settings manager instance (for testing)."""
    _settings_manager_holder.reset()
