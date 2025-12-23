"""
Centralized monkey-patches for Qt and NodeGraphQt.

This module houses global fixes for library-level bugs that cannot be
easily solved via subclassing alone.
"""

from loguru import logger


class CasareViewerFontFix:
    """
    Fix for NodeViewer font initialization that can cause QFont -1 warnings.

    DEPRECATED: Global patching removed per codebase modernization.
    Font protection moved to CasareNodeItem._create_port_text_item().

    This function now does nothing (no-op).
    """

    @staticmethod
    def apply_fix() -> None:
        """
        Patch QGraphicsTextItem.font to ensure it always returns a valid font.

        DEPRECATED: No longer applies global patch.
        Font protection handled by CasareNodeItem._create_port_text_item().
        """
        logger.debug("CasareViewerFontFix: No-op (global patch removed)")


class CasareQFontFix:
    """
    Fix for QFont.setPointSize being called with invalid values (-1 or 0).

    DEPRECATED: Global patching removed per codebase modernization.
    Font protection moved to CasareQFont class (casare_font.py).

    This function now does nothing (no-op).
    """

    _applied = False

    @staticmethod
    def apply_fix() -> None:
        """
        Patch QFont.setPointSize to guard against invalid values.

        DEPRECATED: No longer applies global patch.
        Font protection handled by CasareQFont class (casare_font.py).
        Use CasareQFont directly where needed.
        """
        if CasareQFontFix._applied:
            return

        logger.debug("CasareQFontFix: No-op (global patch removed)")


def apply_early_patches() -> None:
    """
    Apply patches that must exist before any widgets are created.

    MONKEY PATCH REMOVAL STATUS:
    - CasareQFontFix: REMOVED (now uses CasareQFont class)
    - CasareViewerFontFix: REMOVED (now uses CasareNodeItem._create_port_text_item)
    """
    CasareQFontFix.apply_fix()


def apply_graphics_patches() -> None:
    """
    Apply patches related to graphics scene and items.

    MONKEY PATCH REMOVAL STATUS:
    - CasareViewerFontFix: REMOVED (now uses CasareNodeItem._create_port_text_item)
    """
    CasareViewerFontFix.apply_fix()
