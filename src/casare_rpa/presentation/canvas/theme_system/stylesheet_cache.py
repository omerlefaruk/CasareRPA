"""
Stylesheet disk cache for faster startup.

PERFORMANCE: Caches the compiled stylesheet to disk to avoid rebuilding
on each startup. Cache is invalidated when theme version changes.

C1 Optimization - Expected savings: ~15-25ms on cache hit.
"""

import hashlib
from pathlib import Path

from loguru import logger

# Cache configuration
_CACHE_DIR = Path.home() / ".casare_rpa" / "cache"
_STYLESHEET_CACHE_FILE = _CACHE_DIR / "stylesheet_cache.qss"
_STYLESHEET_HASH_FILE = _CACHE_DIR / "stylesheet_hash.txt"

# Bump this version when theme structure changes
_THEME_VERSION = "1.0.1"


def _compute_theme_hash() -> str:
    """
    Compute hash of theme configuration.

    Uses theme version + key theme values to detect changes.

    Returns:
        12-character hash string
    """
    try:
        from casare_rpa.presentation.canvas.theme_system.colors import CanvasThemeColors

        theme = CanvasThemeColors()
        # Include key colors that affect stylesheet (including menu colors)
        theme_data = (
            f"{_THEME_VERSION}:"
            f"{theme.bg_darkest}:{theme.bg_dark}:{theme.bg_panel}:"
            f"{theme.accent_primary}:{theme.text_primary}:"
            f"{theme.menu_bg}:{theme.menu_border}:{theme.menu_hover}:{theme.menu_text}"
        )
        return hashlib.md5(theme_data.encode()).hexdigest()[:12]
    except Exception:
        # If we can't compute hash, return version only
        return hashlib.md5(_THEME_VERSION.encode()).hexdigest()[:12]


def get_cached_stylesheet() -> str | None:
    """
    Load stylesheet from disk cache if valid.

    Returns:
        Cached stylesheet string, or None if cache miss/invalid
    """
    try:
        if not _STYLESHEET_CACHE_FILE.exists():
            logger.debug("Stylesheet cache miss: file not found")
            return None

        if not _STYLESHEET_HASH_FILE.exists():
            logger.debug("Stylesheet cache miss: hash file not found")
            return None

        # Check hash
        stored_hash = _STYLESHEET_HASH_FILE.read_text().strip()
        current_hash = _compute_theme_hash()

        if stored_hash != current_hash:
            logger.debug(
                f"Stylesheet cache invalidated: hash mismatch " f"({stored_hash} != {current_hash})"
            )
            return None

        stylesheet = _STYLESHEET_CACHE_FILE.read_text(encoding="utf-8")
        logger.debug(f"Loaded stylesheet from cache ({len(stylesheet)} bytes)")
        return stylesheet

    except Exception as e:
        logger.debug(f"Stylesheet cache read error: {e}")
        return None


def cache_stylesheet(stylesheet: str) -> None:
    """
    Save stylesheet to disk cache.

    Args:
        stylesheet: The compiled stylesheet string
    """
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _STYLESHEET_CACHE_FILE.write_text(stylesheet, encoding="utf-8")
        _STYLESHEET_HASH_FILE.write_text(_compute_theme_hash())
        logger.debug(f"Stylesheet cached to disk ({len(stylesheet)} bytes)")
    except Exception as e:
        logger.warning(f"Failed to cache stylesheet: {e}")


def invalidate_cache() -> None:
    """
    Invalidate the stylesheet disk cache.

    Call this when theme is modified at runtime.
    """
    try:
        if _STYLESHEET_CACHE_FILE.exists():
            _STYLESHEET_CACHE_FILE.unlink()
        if _STYLESHEET_HASH_FILE.exists():
            _STYLESHEET_HASH_FILE.unlink()
        logger.debug("Stylesheet disk cache invalidated")
    except Exception as e:
        logger.warning(f"Failed to invalidate stylesheet cache: {e}")
