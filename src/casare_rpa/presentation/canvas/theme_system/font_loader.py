"""
Font loader for Epic 1.2 - Geist Sans/Mono bundling.

Provides font registration at app startup with clean fallbacks to system fonts.
Uses QFontDatabase to register bundled fonts before UI creation.

Usage (in app.py, before QApplication creates widgets):
    from casare_rpa.presentation.canvas.theme_system.font_loader import ensure_font_registered
    ensure_font_registered()

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.2
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from loguru import logger
from PySide6.QtGui import QFontDatabase

# =============================================================================
# FONT ASSET PATHS
# =============================================================================

# Expected font filenames (will be added in Epic 1.2 full implementation)
GEIST_SANS_FILES: Final = ("Geist-Regular.ttf", "Geist-Medium.ttf", "Geist-SemiBold.ttf")
GEIST_MONO_FILES: Final = ("GeistMono-Regular.ttf", "GeistMono-Medium.ttf", "GeistMono-SemiBold.ttf")

# Font family names to register
GEIST_SANS_FAMILY: Final = "Geist Sans"
GEIST_MONO_FAMILY: Final = "Geist Mono"

# =============================================================================
# FONT REGISTRATION STATE
# =============================================================================

_font_registered: bool = False


def _get_fonts_dir() -> Path:
    """
    Get the directory containing bundled font files.

    Looks in:
    1. Development: src/casare_rpa/resources/fonts/
    2. PyInstaller: sys._MEIPASS/fonts/

    Returns:
        Path to fonts directory (may not exist)
    """
    # Try development path first
    dev_path = Path(__file__).parent.parent.parent.parent / "resources" / "fonts"
    if dev_path.exists():
        return dev_path

    # Try PyInstaller frozen path
    import sys

    if getattr(sys, "frozen", False):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        bundle_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        frozen_path = bundle_dir / "fonts"
        if frozen_path.exists():
            return frozen_path

    # Fallback to dev path even if it doesn't exist (for graceful failure)
    return dev_path


def _register_font_family(
    family_name: str, font_files: tuple[str, ...], fonts_dir: Path
) -> bool:
    """
    Register a font family from TTF files.

    Args:
        family_name: The font family name (e.g., "Geist Sans")
        font_files: Tuple of font filenames to register
        fonts_dir: Directory containing the font files

    Returns:
        True if at least one font was registered successfully
    """
    registered_count = 0

    for font_file in font_files:
        font_path = fonts_dir / font_file
        if not font_path.exists():
            continue

        try:
            id_ = QFontDatabase.addApplicationFont(str(font_path))
            if id_ >= 0:
                # Verify the family name matches what we expect
                families = QFontDatabase.applicationFontFamilies(id_)
                if family_name in families:
                    registered_count += 1
                    logger.debug(f"Registered font: {font_file} as {family_name}")
                else:
                    # Font loaded but with different family name - log it
                    logger.debug(
                        f"Registered font: {font_file} as {families[0] if families else 'Unknown'}"
                    )
                    registered_count += 1
            else:
                logger.warning(f"Failed to load font: {font_file} (id={id_})")
        except Exception as e:
            logger.warning(f"Error loading font {font_file}: {e}")

    return registered_count > 0


def ensure_font_registered() -> None:
    """
    Ensure Geist fonts are registered with Qt.

    This function:
    1. Checks if fonts are already registered (idempotent)
    2. Attempts to register bundled Geist Sans/Mono fonts
    3. Falls back gracefully if fonts are not available
    4. Logs the result

    Call this early in app initialization, before creating any widgets.

    Note:
        In Epic 1.2, the actual font files may not exist yet.
        This function handles that gracefully - it will log and continue.
        The fallback fonts (Segoe UI, Cascadia Code) are specified in
        tokens_v2.py TypographyV2 and work without registration.

    Example:
        from casare_rpa.presentation.canvas.theme_system.font_loader import ensure_font_registered

        ensure_font_registered()  # Call before QApplication creates widgets
    """
    global _font_registered

    if _font_registered:
        return  # Already done

    fonts_dir = _get_fonts_dir()

    if not fonts_dir.exists():
        logger.debug(
            f"Fonts directory not found: {fonts_dir} - using system font fallbacks"
        )
        _font_registered = True
        return

    # Try to register Geist Sans
    geist_sans_ok = _register_font_family(
        GEIST_SANS_FAMILY, GEIST_SANS_FILES, fonts_dir
    )

    # Try to register Geist Mono
    geist_mono_ok = _register_font_family(
        GEIST_MONO_FAMILY, GEIST_MONO_FILES, fonts_dir
    )

    if geist_sans_ok and geist_mono_ok:
        logger.info("Geist Sans and Geist Mono fonts registered successfully")
    elif geist_sans_ok or geist_mono_ok:
        logger.info(
            f"Partial font registration: Geist Sans={'OK' if geist_sans_ok else 'FAIL'}, "
            f"Geist Mono={'OK' if geist_mono_ok else 'FAIL'}"
        )
    else:
        logger.debug("No Geist fonts registered - using system fallbacks")

    _font_registered = True


def get_registered_fonts() -> dict[str, bool]:
    """
    Get registration status of bundled font families.

    Returns:
        Dict with font family names as keys and registration status as values
    """
    return {
        GEIST_SANS_FAMILY: _is_family_available(GEIST_SANS_FAMILY),
        GEIST_MONO_FAMILY: _is_family_available(GEIST_MONO_FAMILY),
    }


def _is_family_available(family_name: str) -> bool:
    """Check if a font family is available in the QFontDatabase."""
    return family_name in QFontDatabase.families()


__all__ = [
    "ensure_font_registered",
    "get_registered_fonts",
    "GEIST_SANS_FAMILY",
    "GEIST_MONO_FAMILY",
]
