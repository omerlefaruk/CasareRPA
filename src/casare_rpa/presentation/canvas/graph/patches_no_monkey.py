"""
Centralized monkey-patches for Qt and NodeGraphQt.

MONKEY PATCH REMOVAL STATUS:
- CasareViewerFontFix: REMOVED - Font fix moved to CasareNodeItem._create_port_text_item()
- CasareQFontFix: REMOVED - Font protection now in CasareQFont class (casare_font.py)

This module now contains only no-op functions for compatibility.
Any remaining patches in this file must be carefully reviewed and approved per project rules.
"""

from loguru import logger


def apply_early_patches() -> None:
    """
    Apply patches that must exist before any widgets are created.

    REMOVED: CasareQFontFix patch
    Font protection now handled by CasareQFont class (casare_font.py)
    """
    logger.debug("Early patches: No active patches (CasareQFont removed)")


def apply_graphics_patches() -> None:
    """
    Apply patches related to graphics scene and items.

    REMOVED: CasareViewerFontFix patch
    Font protection now handled by CasareNodeItem._create_port_text_item()
    """
    logger.debug("Graphics patches: No active patches (CasareViewerFontFix removed)")
