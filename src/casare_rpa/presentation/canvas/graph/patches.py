"""
Centralized monkey-patches for Qt and NodeGraphQt.

This module houses global fixes for library-level bugs that cannot be
easily solved via subclassing alone.
"""

from loguru import logger
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGraphicsTextItem


class CasareViewerFontFix:
    """
    Fix for NodeViewer font initialization that can cause QFont -1 warnings.
    """

    @staticmethod
    def apply_fix() -> None:
        """Patch QGraphicsTextItem.font to ensure it always returns a valid font."""
        try:
            original_font = QGraphicsTextItem.font

            def safe_font(self):
                """Return font, ensuring point size is valid (not -1)."""
                f = original_font(self)
                if f.pointSize() <= 0:
                    # Set a reasonable default if point size is invalid
                    f.setPointSize(9)
                return f

            QGraphicsTextItem.font = safe_font
            logger.debug("Applied QGraphicsTextItem.font fix")

        except Exception as e:
            logger.warning(f"CasareViewerFontFix: Could not apply fix: {e}")


class CasareQFontFix:
    """
    Fix for QFont.setPointSize being called with invalid values (-1 or 0).
    """

    _applied = False

    @staticmethod
    def apply_fix() -> None:
        """Patch QFont.setPointSize to guard against invalid values."""
        if CasareQFontFix._applied:
            return

        try:
            original_setPointSize = QFont.setPointSize

            def safe_setPointSize(self, size: int) -> None:
                """Set point size, correcting invalid values."""
                if size <= 0:
                    size = 9  # Default to 9pt for invalid sizes
                original_setPointSize(self, size)

            QFont.setPointSize = safe_setPointSize
            CasareQFontFix._applied = True
            logger.debug("Applied QFont.setPointSize fix")

        except Exception as e:
            logger.warning(f"CasareQFontFix: Could not apply fix: {e}")


def apply_early_patches() -> None:
    """
    Apply patches that must exist before any widgets are created.
    """
    CasareQFontFix.apply_fix()


def apply_graphics_patches() -> None:
    """
    Apply patches related to graphics scene and items.
    """
    CasareViewerFontFix.apply_fix()
