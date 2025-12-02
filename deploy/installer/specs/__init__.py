"""
PyInstaller Spec Configuration Modules.

This package contains shared configuration for PyInstaller builds:
- base.py: Common configuration (hidden imports, excludes, paths)
- canvas.py: Full application build (Designer + Robot)
- robot.py: Lightweight robot-only build

Usage from spec files:
    from specs.base import HIDDEN_IMPORTS, EXCLUDES, PROJECT_ROOT
"""

from .base import (
    APP_AUTHOR,
    APP_ICON,
    DATAS,
    EXCLUDES,
    HIDDEN_IMPORTS_BASE,
    HIDDEN_IMPORTS_CANVAS,
    HIDDEN_IMPORTS_ROBOT,
    HOOKSPATH,
    PROJECT_ROOT,
    RUNTIME_HOOKS,
    SRC_DIR,
    get_version,
)

__all__ = [
    "PROJECT_ROOT",
    "SRC_DIR",
    "HIDDEN_IMPORTS_BASE",
    "HIDDEN_IMPORTS_CANVAS",
    "HIDDEN_IMPORTS_ROBOT",
    "EXCLUDES",
    "DATAS",
    "HOOKSPATH",
    "RUNTIME_HOOKS",
    "APP_AUTHOR",
    "APP_ICON",
    "get_version",
]
