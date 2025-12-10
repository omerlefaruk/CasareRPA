"""
AnimatedTreeWidget with smooth expand/collapse animations.

Extends QTreeWidget to provide visual feedback during expand/collapse operations.
Since Qt's tree items don't expose height as an animatable property, we use
an overlay approach to animate visual feedback effects.

Features:
- Smooth fade effect during expand/collapse
- Respects AccessibilitySettings.prefers_reduced_motion()
- Uses ANIMATIONS from theme.py for consistent timing

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_tree_widget import (
        AnimatedTreeWidget,
        create_animated_tree_widget,
    )

    # Factory function (recommended)
    tree = create_animated_tree_widget(parent)

    # Direct instantiation
    tree = AnimatedTreeWidget(parent)
    tree.setColumnCount(2)
    tree.setHeaderLabels(["Name", "Value"])
"""

from typing import Dict, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    Qt,
)
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QTreeWidget,
    QTreeWidgetItem,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, THEME


class _ExpandCollapseOverlay(QWidget):
    """
    Transparent overlay widget that provides visual feedback during expansion.

    This overlay sits on top of the tree viewport and animates opacity to
    create a subtle flash effect when items are expanded/collapsed.
    """

    def __init__(self, parent: QWidget) -> None:
        """
        Initialize the overlay.

        Args:
            parent: Parent widget (typically tree viewport).
        """
        super().__init__(parent)
        self._opacity: float = 0.0
        self._highlight_color = QColor(THEME.accent)
        self._highlight_color.setAlphaF(0.15)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        self.hide()

    @property
    def opacity(self) -> float:
        """Get current opacity."""
        return self._opacity

    @opacity.setter
    def opacity(self, value: float) -> None:
        """Set opacity and trigger repaint."""
        self._opacity = max(0.0, min(1.0, value))
        self.update()

    def set_highlight_rect(self, rect: QRect) -> None:
        """
        Set the rectangle to highlight.

        Args:
            rect: Rectangle in viewport coordinates.
        """
        self.setGeometry(rect)

    def paintEvent(self, event) -> None:
        """Paint the highlight with current opacity."""
        if self._opacity <= 0.0:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(self._highlight_color)
        color.setAlphaF(self._highlight_color.alphaF() * self._opacity)

        painter.fillRect(self.rect(), color)
        painter.end()


class AnimatedTreeWidget(QTreeWidget):
    """
    QTreeWidget with animated expand/collapse visual feedback.

    Provides a subtle highlight flash when items are expanded or collapsed,
    giving visual feedback without disrupting the standard tree behavior.

    Animations are disabled when:
    - AccessibilitySettings.prefers_reduced_motion() returns True
    - Animation is already in progress for the item

    Attributes:
        animation_duration: Duration in ms (from ANIMATIONS.normal).
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the animated tree widget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Animation state tracking
        self._animations: Dict[int, QPropertyAnimation] = {}
        self._overlay: Optional[_ExpandCollapseOverlay] = None

        # Connect expand/collapse signals
        self.itemExpanded.connect(self._on_item_expanded)
        self.itemCollapsed.connect(self._on_item_collapsed)

        # Enable smooth scrolling
        self.setVerticalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QTreeWidget.ScrollMode.ScrollPerPixel)

        # Standard tree animation (Qt's built-in)
        self.setAnimated(True)

        logger.debug("AnimatedTreeWidget initialized")

    def _ensure_overlay(self) -> _ExpandCollapseOverlay:
        """
        Ensure overlay widget exists and is parented to viewport.

        Returns:
            The overlay widget.
        """
        if self._overlay is None:
            self._overlay = _ExpandCollapseOverlay(self.viewport())
        return self._overlay

    def _get_item_id(self, item: QTreeWidgetItem) -> int:
        """
        Get a unique identifier for a tree item.

        Args:
            item: Tree widget item.

        Returns:
            Unique integer ID (memory address).
        """
        return id(item)

    def _on_item_expanded(self, item: QTreeWidgetItem) -> None:
        """
        Handle item expanded event.

        Args:
            item: The expanded item.
        """
        self._animate_item(item, expanding=True)

    def _on_item_collapsed(self, item: QTreeWidgetItem) -> None:
        """
        Handle item collapsed event.

        Args:
            item: The collapsed item.
        """
        self._animate_item(item, expanding=False)

    def _animate_item(self, item: QTreeWidgetItem, expanding: bool) -> None:
        """
        Animate visual feedback for item expand/collapse.

        Args:
            item: The tree item being expanded/collapsed.
            expanding: True if expanding, False if collapsing.
        """
        # Check accessibility preference
        if AccessibilitySettings.prefers_reduced_motion():
            return

        item_id = self._get_item_id(item)

        # Cancel any existing animation for this item
        if item_id in self._animations:
            existing = self._animations[item_id]
            existing.stop()
            del self._animations[item_id]

        # Get item visual rect
        item_rect = self.visualItemRect(item)
        if not item_rect.isValid() or item_rect.isEmpty():
            return

        # Setup overlay
        overlay = self._ensure_overlay()

        # Expand rect to include children area (approximate)
        if expanding and item.childCount() > 0:
            # Estimate expanded height based on visible children
            child_height = item_rect.height() * min(item.childCount(), 5)
            item_rect.setHeight(item_rect.height() + child_height)

        # Ensure rect stays within viewport
        viewport_rect = self.viewport().rect()
        item_rect = item_rect.intersected(viewport_rect)

        if item_rect.isEmpty():
            return

        overlay.set_highlight_rect(item_rect)
        overlay.opacity = 1.0
        overlay.show()
        overlay.raise_()

        # Create fade-out animation
        animation = QPropertyAnimation(overlay, b"opacity", self)
        animation.setDuration(AccessibilitySettings.get_duration(ANIMATIONS.normal))
        animation.setStartValue(1.0)
        animation.setEndValue(0.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Store animation reference
        self._animations[item_id] = animation

        # Cleanup on finish
        def on_finished():
            if item_id in self._animations:
                del self._animations[item_id]
            if overlay.opacity <= 0.0:
                overlay.hide()

        animation.finished.connect(on_finished)
        animation.start()

    def clear(self) -> None:
        """Clear tree and cancel all animations."""
        self._cancel_all_animations()
        super().clear()

    def _cancel_all_animations(self) -> None:
        """Cancel all running animations."""
        for animation in list(self._animations.values()):
            animation.stop()
        self._animations.clear()

        if self._overlay is not None:
            self._overlay.hide()
            self._overlay.opacity = 0.0

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        # Ensure overlay is properly sized
        if self._overlay is not None:
            self._overlay.hide()

    def resizeEvent(self, event) -> None:
        """Handle resize event."""
        super().resizeEvent(event)
        # Cancel animations on resize to avoid visual glitches
        self._cancel_all_animations()


def create_animated_tree_widget(
    parent: Optional[QWidget] = None,
    column_count: int = 1,
    headers: Optional[list] = None,
) -> AnimatedTreeWidget:
    """
    Factory function to create an AnimatedTreeWidget with common settings.

    Args:
        parent: Parent widget.
        column_count: Number of columns (default 1).
        headers: Optional list of header labels.

    Returns:
        Configured AnimatedTreeWidget instance.

    Example:
        tree = create_animated_tree_widget(
            parent=self,
            column_count=2,
            headers=["Name", "Value"],
        )
    """
    tree = AnimatedTreeWidget(parent)

    if column_count > 0:
        tree.setColumnCount(column_count)

    if headers:
        tree.setHeaderLabels(headers)

    # Apply common settings
    tree.setAlternatingRowColors(True)
    tree.setIndentation(20)
    tree.setRootIsDecorated(True)

    # Apply theme styling
    tree.setStyleSheet(f"""
        QTreeWidget {{
            background-color: {THEME.bg_medium};
            alternate-background-color: {THEME.bg_light};
            border: 1px solid {THEME.border};
            color: {THEME.text_primary};
        }}
        QTreeWidget::item {{
            padding: 4px 2px;
            min-height: 24px;
        }}
        QTreeWidget::item:selected {{
            background-color: {THEME.selected};
        }}
        QTreeWidget::item:hover {{
            background-color: {THEME.hover};
        }}
        QHeaderView::section {{
            background-color: {THEME.input_bg};
            color: {THEME.text_primary};
            border: none;
            border-right: 1px solid {THEME.border};
            border-bottom: 1px solid {THEME.border};
            padding: 6px;
            font-weight: bold;
        }}
    """)

    logger.debug(
        f"Created AnimatedTreeWidget with {column_count} columns, " f"headers={headers}"
    )

    return tree
