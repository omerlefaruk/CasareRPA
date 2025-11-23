"""
CasareRPA - Utilities Package
Contains configuration, helpers, and shared utilities.
"""

from .config import (
    APP_NAME,
    APP_VERSION,
    APP_AUTHOR,
    APP_DESCRIPTION,
    PROJECT_ROOT,
    LOGS_DIR,
    WORKFLOWS_DIR,
    setup_logging,
)
from .hotkey_settings import get_hotkey_settings, HotkeySettings
from .template_loader import TemplateLoader, TemplateInfo, get_template_loader

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_AUTHOR",
    "APP_DESCRIPTION",
    "PROJECT_ROOT",
    "LOGS_DIR",
    "WORKFLOWS_DIR",
    "setup_logging",
    "get_hotkey_settings",
    "HotkeySettings",
    "TemplateLoader",
    "TemplateInfo",
    "get_template_loader",
]
