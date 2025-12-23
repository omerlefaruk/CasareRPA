"""
Custom QFont wrapper that guards against invalid point sizes.

Replaces global QFont.setPointSize monkey patch from node_widgets.py.
Provides same safety guarantees without affecting entire application.
"""

from PySide6.QtGui import QFont


class CasareQFont(QFont):
    """
    QFont subclass that guards against invalid point sizes.

    NodeGraphQt and Qt internally may call setPointSize with -1 or 0
    when fonts are not properly initialized. This subclass ensures invalid
    values are silently corrected to a reasonable default without global patching.

    Usage:
        from casare_rpa.presentation.canvas.graph.casare_font import CasareQFont

        # Create font with automatic invalid value protection
        font = CasareQFont("Segoe UI", 9)
        font.setPointSize(-1)  # Will silently correct to 9
    """

    def setPointSize(self, size: int) -> None:
        """
        Set point size, correcting invalid values.

        If size is less than or equal to 0, it will be corrected
        to a default of 9pt. This matches the behavior of the
        removed global patch.

        Args:
            size: Requested font point size
        """
        if size <= 0:
            size = 9  # Default to 9pt for invalid sizes
        super().setPointSize(size)

    @staticmethod
    def from_base(base: QFont) -> "CasareQFont":
        """
        Create CasareQFont from existing QFont.

        Preserves all font attributes while adding invalid size protection.

        Args:
            base: Existing QFont to copy attributes from

        Returns:
            CasareQFont with same attributes as base
        """
        font = CasareQFont(base.family(), base.pointSize())
        font.setStyle(base.style())
        font.setWeight(base.weight())
        font.setItalic(base.italic())
        if base.pointSize() <= 0:
            font.setPointSize(9)
        return font
