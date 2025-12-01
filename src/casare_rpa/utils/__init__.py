"""
CasareRPA - Utilities Package
Contains configuration, helpers, and shared utilities.
"""

# Core configuration
from .config import (
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
    PROJECT_ROOT,
    LOGS_DIR,
    WORKFLOWS_DIR,
    CONFIG_DIR,
    IS_FROZEN,
    setup_logging,
)
from .config_loader import (
    ConfigLoader,
    ConfigSource,
    ConfigSchema,
    ConfigurationError,
    load_config,
    load_config_with_env,
)
from .settings_manager import SettingsManager
from .hotkey_settings import get_hotkey_settings, HotkeySettings
from .id_generator import generate_node_id
from .fuzzy_search import SearchIndex, fuzzy_search, fuzzy_match
from .playwright_setup import ensure_playwright_ready
from .datetime_helpers import (
    parse_datetime,
    format_datetime,
    to_iso_format,
    DEFAULT_DATETIME_FORMATS,
)

# Subpackages - import them to make them accessible
from . import pooling
from . import selectors
from . import resilience
from . import security
from . import workflow
from . import performance

__all__ = [
    # Config
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    "PROJECT_ROOT",
    "LOGS_DIR",
    "WORKFLOWS_DIR",
    "CONFIG_DIR",
    "IS_FROZEN",
    "setup_logging",
    "ConfigLoader",
    "ConfigSource",
    "ConfigSchema",
    "ConfigurationError",
    "load_config",
    "load_config_with_env",
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
    # Subpackages
    "pooling",
    "selectors",
    "resilience",
    "security",
    "workflow",
    "performance",
]
