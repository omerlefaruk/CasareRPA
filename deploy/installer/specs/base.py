"""
Base PyInstaller Configuration.

Shared configuration for all CasareRPA builds.
Import this in spec files to get common settings.

Usage in spec files:
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from specs.base import *
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Get project root (deploy/installer/specs -> project root)
_SPECS_DIR = Path(__file__).parent
INSTALLER_DIR = _SPECS_DIR.parent
PROJECT_ROOT = INSTALLER_DIR.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Application metadata
APP_AUTHOR = "CasareRPA Team"
APP_ICON = str(INSTALLER_DIR / "assets" / "casarerpa.ico")


def get_version() -> str:
    """Get version from pyproject.toml."""
    try:
        # Try using the version module
        sys.path.insert(0, str(INSTALLER_DIR))
        from version import get_version as _get_version

        return _get_version().string
    except Exception:
        # Fallback
        return "3.0.0"


# Hidden imports shared across all builds
HIDDEN_IMPORTS_BASE = [
    # Async support
    "asyncio",
    # Database drivers
    "asyncpg",
    "aiomysql",
    # HTTP/WebSocket
    "aiohttp",
    "websockets",
    "httpx",
    # Playwright (browser automation)
    "playwright",
    "playwright.async_api",
    # JSON/Serialization
    "orjson",
    "pydantic",
    "pydantic_core",
    # Utilities
    "psutil",
    "loguru",
    "dotenv",
    # Fix urllib3/brotli compatibility
    "brotli",
    "urllib3.contrib.pyopenssl",
    # CasareRPA core modules
    "casare_rpa",
    "casare_rpa.nodes",
    "casare_rpa.infrastructure.execution",
    "casare_rpa.infrastructure.resources",
]

# Additional hidden imports for Canvas (Designer) build
HIDDEN_IMPORTS_CANVAS = [
    # Qt/PySide6 plugins
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtNetwork",
    "PySide6.QtPrintSupport",
    # Async Qt support
    "qasync",
    # Windows desktop automation
    "uiautomation",
    # Scheduling
    "apscheduler",
    "apscheduler.schedulers.asyncio",
    "apscheduler.triggers.cron",
    "apscheduler.triggers.interval",
    "apscheduler.triggers.date",
    # Security
    "jwt",
    "hvac",
    # Utilities
    "numpy",
    "simpleeval",
    "croniter",
    # FastAPI (for orchestrator client)
    "fastapi",
    "uvicorn",
    "starlette",
    # CasareRPA Canvas modules
    "casare_rpa.presentation.canvas",
    "casare_rpa.infrastructure.agent",
]

# Hidden imports for Robot-only build
HIDDEN_IMPORTS_ROBOT = [
    # Windows desktop automation
    "uiautomation",
    # CLI tools
    "typer",
    "rich",
    # Supabase
    "supabase",
    # CasareRPA Robot modules
    "casare_rpa.robot",
    "casare_rpa.robot.cli",
    "casare_rpa.robot.distributed_agent",
    "casare_rpa.infrastructure.queue",
]

# Excludes common to all builds
EXCLUDES_BASE = [
    # Testing modules
    "pytest",
    "pytest_asyncio",
    "pytest_qt",
    "pytest_cov",
    "pytest_benchmark",
    # Development tools
    "black",
    "mypy",
    "ruff",
    "pip_audit",
    # Fix brotlicffi incompatibility
    "brotlicffi",
]

# Additional excludes for Robot build (minimize size)
EXCLUDES_ROBOT = [
    # GUI components
    "PySide6",
    "PyQt5",
    "PyQt6",
    "tkinter",
    "NodeGraphQt",
    "qasync",
    # Unused large ML/AI packages
    "torch",
    "torchvision",
    "tensorflow",
    "onnxruntime",
    "cv2",
    "opencv-python",
    "skimage",
    "scikit-image",
    "pyarrow",
    "fsspec",
    "IPython",
    "jedi",
    "parso",
    # Unused large packages
    "matplotlib",
    "scipy",
    "pandas",
    "numpy",
]

# Combined exclude lists
EXCLUDES = EXCLUDES_BASE
EXCLUDES_ROBOT_FULL = EXCLUDES_BASE + EXCLUDES_ROBOT

# Data files to include
DATAS = [
    # Configuration files
    (str(PROJECT_ROOT / "config"), "config"),
]

# Hooks directory
HOOKSPATH = [str(INSTALLER_DIR / "hooks")]

# Runtime hooks
RUNTIME_HOOKS = [
    str(INSTALLER_DIR / "hooks" / "rthook_brotli_fix.py"),
]


def get_canvas_analysis_kwargs() -> dict:
    """Get Analysis kwargs for Canvas build."""
    return {
        "pathex": [str(SRC_DIR)],
        "binaries": [],
        "datas": DATAS + [(str(INSTALLER_DIR / "assets"), "assets")],
        "hiddenimports": HIDDEN_IMPORTS_BASE + HIDDEN_IMPORTS_CANVAS,
        "hookspath": HOOKSPATH,
        "hooksconfig": {},
        "runtime_hooks": [],
        "excludes": EXCLUDES,
        "noarchive": False,
        "optimize": 0,
    }


def get_robot_analysis_kwargs() -> dict:
    """Get Analysis kwargs for Robot build."""
    return {
        "pathex": [str(SRC_DIR)],
        "binaries": [],
        "datas": DATAS,
        "hiddenimports": HIDDEN_IMPORTS_BASE + HIDDEN_IMPORTS_ROBOT,
        "hookspath": HOOKSPATH,
        "hooksconfig": {},
        "runtime_hooks": RUNTIME_HOOKS,
        "excludes": EXCLUDES_ROBOT_FULL,
        "noarchive": False,
        "optimize": 1,
    }


def check_icon_exists() -> str | None:
    """Check if icon file exists and return path or None."""
    if Path(APP_ICON).exists():
        return APP_ICON
    return None


def check_version_info_exists() -> str | None:
    """Check if version info file exists and return path or None."""
    version_info_path = INSTALLER_DIR / "file_version_info.txt"
    if version_info_path.exists():
        return str(version_info_path)
    return None
