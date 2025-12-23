"""
CasareRPA - Utilities Package
Contains helpers and shared utilities.

NOTE: Configuration has moved to casare_rpa.config
Import from casare_rpa.config instead of casare_rpa.utils for:
- Path constants (PROJECT_ROOT, LOGS_DIR, etc.)
- App constants (APP_NAME, APP_VERSION, etc.)
- setup_logging()
- ConfigLoader, load_config, etc.
"""

# Subpackages - import them to make them accessible
from casare_rpa.utils import performance, pooling, resilience, security, selectors, workflow
from casare_rpa.utils.datetime_helpers import (
    DEFAULT_DATETIME_FORMATS,
    format_datetime,
    parse_datetime,
    to_iso_format,
)
from casare_rpa.utils.fuzzy_search import SearchIndex, fuzzy_match, fuzzy_search
from casare_rpa.utils.hotkey_settings import HotkeySettings, get_hotkey_settings
from casare_rpa.utils.id_generator import generate_node_id
from casare_rpa.utils.playwright_setup import ensure_playwright_ready
from casare_rpa.utils.settings_manager import SettingsManager
from casare_rpa.utils.type_converters import safe_bool, safe_float, safe_int, safe_str

__all__ = [
    "SettingsManager",
    # Hotkeys
    "get_hotkey_settings",
    "HotkeySettings",
    # Utilities
    "generate_node_id",
    "SearchIndex",
    "fuzzy_search",
    "fuzzy_match",
    "ensure_playwright_ready",
    # Datetime helpers
    "parse_datetime",
    "format_datetime",
    "to_iso_format",
    "DEFAULT_DATETIME_FORMATS",
    # Type converters
    "safe_int",
    "safe_float",
    "safe_str",
    "safe_bool",
    # Subpackages
    "pooling",
    "selectors",
    "resilience",
    "security",
    "workflow",
    "performance",
]
