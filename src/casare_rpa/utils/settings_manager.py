"""
CasareRPA - Settings Manager
Handles application settings persistence.
"""

import orjson
from typing import Any, Optional
from loguru import logger

from .config import CONFIG_DIR


class SettingsManager:
    """
    Manages application settings with JSON persistence.

    Settings are stored in config/settings.json
    """

    DEFAULT_SETTINGS = {
        "autosave": {
            "enabled": True,
            "interval_minutes": 5,  # Auto-save every 5 minutes
        },
        "ui": {
            "theme": "dark",
            "show_minimap": True,
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


# Global settings manager instance
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """
    Get the global settings manager instance.

    Returns:
        SettingsManager instance
    """
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager
