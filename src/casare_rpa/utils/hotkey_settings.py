"""
Hotkey settings manager for persistent storage of keyboard shortcuts.

This module handles loading and saving custom keyboard shortcuts to a JSON file.
Uses orjson for fast serialization.
"""

import orjson
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

from casare_rpa.config import HOTKEYS_FILE


# Default hotkeys configuration
DEFAULT_HOTKEYS: Dict[str, List[str]] = {
    "new": ["Ctrl+N"],
    "open": ["Ctrl+O"],
    "save": ["Ctrl+S"],
    "save_as": ["Ctrl+Shift+S"],
    "exit": ["Ctrl+Q"],
    "undo": ["Ctrl+Z"],
    "redo": ["Ctrl+Y", "Ctrl+Shift+Z"],
    "cut": ["Ctrl+X"],
    "copy": ["Ctrl+C"],
    "paste": ["Ctrl+V"],
    "delete": ["X"],
    "select_all": ["Ctrl+A"],
    "deselect_all": ["Ctrl+Shift+A"],
    "zoom_in": ["Ctrl++"],
    "zoom_out": ["Ctrl+-"],
    "zoom_reset": ["Ctrl+0"],
    "fit_view": ["Ctrl+F"],
    "run": ["F3"],
    "run_to_node": ["F4"],
    "run_single_node": ["F5"],
    "pause": ["F6"],
    "stop": ["Shift+F3"],
    "create_frame": ["Shift+W"],
    "hotkey_manager": ["Ctrl+K, Ctrl+S"],
}


class HotkeySettings:
    """Manager for hotkey settings with persistent storage."""

    def __init__(self, settings_file: Optional[Path] = None):
        """
        Initialize hotkey settings manager.

        Args:
            settings_file: Path to settings file (defaults to HOTKEYS_FILE)
        """
        self._settings_file = settings_file or HOTKEYS_FILE
        self._hotkeys: Dict[str, List[str]] = {}
        self.load()

    def load(self) -> None:
        """Load hotkeys from file, or use defaults if file doesn't exist."""
        if self._settings_file.exists():
            try:
                data = self._settings_file.read_bytes()
                self._hotkeys = orjson.loads(data)
                logger.info(f"Loaded hotkeys from {self._settings_file}")
            except Exception as e:
                logger.error(f"Failed to load hotkeys: {e}")
                self._hotkeys = DEFAULT_HOTKEYS.copy()
        else:
            logger.info("No hotkey settings file found, using defaults")
            self._hotkeys = DEFAULT_HOTKEYS.copy()

    def save(self) -> None:
        """Save current hotkeys to file."""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            data = orjson.dumps(self._hotkeys, option=orjson.OPT_INDENT_2)
            self._settings_file.write_bytes(data)
            logger.info(f"Saved hotkeys to {self._settings_file}")
        except Exception as e:
            logger.error(f"Failed to save hotkeys: {e}")

    def get_shortcuts(self, action_name: str) -> List[str]:
        """
        Get shortcuts for an action.

        Args:
            action_name: Name of the action

        Returns:
            List of shortcut strings
        """
        return self._hotkeys.get(action_name, [])

    def set_shortcuts(self, action_name: str, shortcuts: List[str]) -> None:
        """
        Set shortcuts for an action.

        Args:
            action_name: Name of the action
            shortcuts: List of shortcut strings
        """
        if shortcuts:
            self._hotkeys[action_name] = shortcuts
        else:
            # Remove empty shortcuts
            self._hotkeys.pop(action_name, None)

    def reset_to_defaults(self) -> None:
        """Reset all hotkeys to defaults."""
        self._hotkeys = DEFAULT_HOTKEYS.copy()
        logger.info("Reset hotkeys to defaults")

    def get_all_hotkeys(self) -> Dict[str, List[str]]:
        """Get all hotkeys."""
        return self._hotkeys.copy()


# Thread-safe singleton holder
from casare_rpa.application.dependency_injection.singleton import Singleton

_hotkey_settings_holder = Singleton(HotkeySettings, name="HotkeySettings")


def get_hotkey_settings() -> HotkeySettings:
    """
    Get the global hotkey settings instance.

    Returns:
        Global HotkeySettings instance
    """
    return _hotkey_settings_holder.get()


def reset_hotkey_settings() -> None:
    """Reset the hotkey settings instance (for testing)."""
    _hotkey_settings_holder.reset()
