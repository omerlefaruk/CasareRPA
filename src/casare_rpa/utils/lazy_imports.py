"""
Lazy Import Utilities for CasareRPA.

PERFORMANCE: Heavy modules like Playwright, uiautomation, and win32com
add significant startup overhead when imported at module load time.
This utility provides lazy import patterns that defer loading until
the module is actually used.

Usage:
    # Instead of: import uiautomation
    # Use: uiautomation = get_uiautomation()

    from casare_rpa.utils.lazy_imports import get_uiautomation, get_playwright

    async def my_function():
        playwright = await get_playwright()
        browser = await playwright.chromium.launch()
"""

from typing import Any, Optional
import sys
from functools import lru_cache

from loguru import logger


# =============================================================================
# Lazy Import Caches
# =============================================================================

_uiautomation: Optional[Any] = None
_win32gui: Optional[Any] = None
_win32con: Optional[Any] = None
_win32api: Optional[Any] = None
_pythoncom: Optional[Any] = None


@lru_cache(maxsize=1)
def get_uiautomation():
    """
    Lazily import uiautomation module.

    PERFORMANCE: uiautomation takes ~200-400ms to import.
    Only imported on first call, then cached.

    Returns:
        uiautomation module
    """
    logger.debug("Lazy loading uiautomation module...")
    import uiautomation

    return uiautomation


@lru_cache(maxsize=1)
def get_win32gui():
    """
    Lazily import win32gui module.

    PERFORMANCE: win32gui takes ~100-200ms to import.
    Only imported on first call, then cached.

    Returns:
        win32gui module
    """
    logger.debug("Lazy loading win32gui module...")
    import win32gui

    return win32gui


@lru_cache(maxsize=1)
def get_win32con():
    """
    Lazily import win32con module.

    Returns:
        win32con module
    """
    logger.debug("Lazy loading win32con module...")
    import win32con

    return win32con


@lru_cache(maxsize=1)
def get_win32api():
    """
    Lazily import win32api module.

    Returns:
        win32api module
    """
    logger.debug("Lazy loading win32api module...")
    import win32api

    return win32api


@lru_cache(maxsize=1)
def get_pythoncom():
    """
    Lazily import pythoncom module.

    Returns:
        pythoncom module
    """
    logger.debug("Lazy loading pythoncom module...")
    import pythoncom

    return pythoncom


def is_uiautomation_loaded() -> bool:
    """Check if uiautomation module is already loaded."""
    return "uiautomation" in sys.modules


def is_win32_loaded() -> bool:
    """Check if win32gui module is already loaded."""
    return "win32gui" in sys.modules


# =============================================================================
# Lazy Class Wrapper
# =============================================================================


class LazyModule:
    """
    Lazy module wrapper that defers import until first attribute access.

    PERFORMANCE: Wraps any module for lazy loading.

    Usage:
        heavy_module = LazyModule("some_heavy_module")
        # Module not loaded yet

        heavy_module.some_function()  # Module loaded on first access
    """

    def __init__(self, module_name: str):
        """
        Initialize lazy module wrapper.

        Args:
            module_name: Name of the module to lazily import
        """
        self._module_name = module_name
        self._module: Optional[Any] = None

    def _load(self) -> Any:
        """Load the module if not already loaded."""
        if self._module is None:
            logger.debug(f"Lazy loading module: {self._module_name}")
            import importlib

            self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying module."""
        return getattr(self._load(), name)

    def __repr__(self) -> str:
        loaded = "loaded" if self._module is not None else "not loaded"
        return f"LazyModule({self._module_name!r}, {loaded})"


# =============================================================================
# Pre-configured Lazy Modules
# =============================================================================

# These can be used as drop-in replacements for imports at the top of files
# Example: from casare_rpa.utils.lazy_imports import uiautomation_lazy as uiautomation

uiautomation_lazy = LazyModule("uiautomation")
win32gui_lazy = LazyModule("win32gui")
win32con_lazy = LazyModule("win32con")
win32api_lazy = LazyModule("win32api")
