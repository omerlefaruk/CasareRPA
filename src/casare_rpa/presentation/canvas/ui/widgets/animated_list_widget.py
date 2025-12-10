"""
Animated List Widget for CasareRPA.

A QListWidget extension with smooth animations for item add/remove operations.
Respects user accessibility preferences for reduced motion.

Features:
- Fade in + slide animation on item insertion
- Fade out + slide animation on item removal
- Subtle selection highlight transition
- Accessibility-aware (respects reduced motion preference)

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.animated_list_widget import (
        AnimatedListWidget,
        create_animated_list_widget,
    )

    # Create widget
    list_widget = create_animated_list_widget()

    # Add items with animation
    list_widget.addAnimatedItem("Item 1")
    list_widget.addAnimatedItem("Item 2")

    # Remove items with animation
    list_widget.removeAnimatedItem(0)
"""

from typing import Dict, List, Optional

from PySide6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QPoint,
    QPropertyAnimation,
    QSequentialAnimationGroup,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from loguru import logger

from casare_rpa.presentation.canvas.ui.accessibility import AccessibilitySettings
from casare_rpa.presentation.canvas.ui.theme import ANIMATIONS, Theme


class AnimatedItemWidget(QWidget):
    """
    Internal widget wrapper for animated list items.

    Provides opacity effect and position tracking for animations.
    Each list item is wrapped in this widget to enable smooth transitions.
    """

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        """
        Initialize animated item widget.

        Args:
            text: The text to display in the item.
            parent: Parent widget.
        """
        super().__init__(parent)

        self._text = text
        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._label: Optional[QLabel] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the widget UI."""
        from PySide6.QtWidgets import QHBoxLayout

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(0)

        self._label = QLabel(self._text)
        colors = Theme.get_colors()
        self._label.setStyleSheet(f"color: {colors.text_primary};")
        layout.addWidget(self._label)

        # Setup opacity effect for fade animations
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

    @property
    def text(self) -> str:
        """Get the item text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set the item text."""
        self._text = value
        if self._label:
            self._label.setText(value)

    @property
    def opacity_effect(self) -> Optional[QGraphicsOpacityEffect]:
        """Get the opacity effect for animations."""
        return self._opacity_effect


class AnimatedListWidget(QListWidget):
    """
    QListWidget with smooth item add/remove animations.

    Provides animated transitions for:
    - Item insertion: Fade in with slide from direction
    - Item removal: Fade out with slide
    - Selection changes: Subtle highlight transition

    Respects AccessibilitySettings.prefers_reduced_motion() for users
    who prefer reduced motion.

    Signals:
        item_animation_finished: Emitted when an item animation completes.
    """

    item_animation_finished = Signal(int)  # row index

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize animated list widget.

        Args:
            parent: Parent widget.
        """
        super().__init__(parent)

        # Track active animations to prevent cleanup during animation
        self._active_animations: Dict[int, QParallelAnimationGroup] = {}

        # Track item widgets for animation access
        self._item_widgets: Dict[int, AnimatedItemWidget] = {}

        # Selection tracking for animation
        self._last_selected_row: int = -1

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup widget styling."""
        colors = Theme.get_colors()
        spacing = Theme.get_spacing()

        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {colors.background_alt};
                border: 1px solid {colors.border};
                border-radius: 4px;
                outline: none;
            }}
            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px;
            }}
            QListWidget::item:selected {{
                background-color: {colors.selection};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {colors.surface_hover};
            }}
            QScrollBar:vertical {{
                background: {colors.background};
                width: 10px;
                border: none;
            }}
            QScrollBar::handle:vertical {{
                background: {colors.secondary_hover};
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors.border_light};
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.setSpacing(1)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.currentRowChanged.connect(self._on_selection_changed)

    def _get_animation_duration(self) -> int:
        """
        Get effective animation duration based on accessibility settings.

        Returns:
            Animation duration in milliseconds (0 if reduced motion preferred).
        """
        return AccessibilitySettings.get_duration(ANIMATIONS.normal)

    def addAnimatedItem(
        self,
        text: str,
        from_top: bool = False,
    ) -> int:
        """
        Add an item with fade-in and slide animation.

        Args:
            text: Text for the new item.
            from_top: If True, slide from top; otherwise slide from bottom.

        Returns:
            The row index of the added item.
        """
        # Create list item
        item = QListWidgetItem()
        item.setSizeHint(self._get_item_size_hint())

        # Create animated widget
        widget = AnimatedItemWidget(text)

        # Add to list
        if from_top:
            self.insertItem(0, item)
            row = 0
        else:
            self.addItem(item)
            row = self.count() - 1

        self.setItemWidget(item, widget)
        self._item_widgets[row] = widget

        # Animate if duration > 0 (animations enabled)
        duration = self._get_animation_duration()
        if duration > 0:
            self._animate_item_in(widget, row, from_top, duration)
        else:
            # Instant show for reduced motion
            if widget.opacity_effect:
                widget.opacity_effect.setOpacity(1.0)

        logger.debug(f"Added animated item '{text}' at row {row}")
        return row

    def _get_item_size_hint(self) -> "QSize":
        """Get the default size hint for items."""
        from PySide6.QtCore import QSize

        return QSize(0, 32)

    def _animate_item_in(
        self,
        widget: AnimatedItemWidget,
        row: int,
        from_top: bool,
        duration: int,
    ) -> None:
        """
        Animate item appearing with fade and slide.

        Args:
            widget: The item widget to animate.
            row: The row index.
            from_top: Direction of slide.
            duration: Animation duration in milliseconds.
        """
        if not widget.opacity_effect:
            return

        # Start fully transparent
        widget.opacity_effect.setOpacity(0.0)

        # Create animation group
        group = QParallelAnimationGroup(self)

        # Fade animation
        fade_anim = QPropertyAnimation(widget.opacity_effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(fade_anim)

        # Slide animation using widget position
        slide_offset = 20 if from_top else -20
        start_pos = QPoint(0, slide_offset)
        end_pos = QPoint(0, 0)

        # Store original position and apply offset
        original_pos = widget.pos()
        widget.move(original_pos.x(), original_pos.y() + slide_offset)

        slide_anim = QPropertyAnimation(widget, b"pos")
        slide_anim.setDuration(duration)
        slide_anim.setStartValue(widget.pos())
        slide_anim.setEndValue(original_pos)
        slide_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        group.addAnimation(slide_anim)

        # Track animation
        self._active_animations[row] = group

        # Cleanup on finish
        group.finished.connect(lambda: self._on_animation_finished(row))

        group.start()

    def removeAnimatedItem(self, row: int) -> bool:
        """
        Remove an item with fade-out and slide animation.

        Args:
            row: The row index to remove.

        Returns:
            True if item was found and removal initiated, False otherwise.
        """
        if row < 0 or row >= self.count():
            logger.warning(f"Cannot remove item at invalid row {row}")
            return False

        item = self.item(row)
        widget = self.itemWidget(item)

        duration = self._get_animation_duration()

        if duration > 0 and isinstance(widget, AnimatedItemWidget):
            # Animate out before removal
            self._animate_item_out(widget, row, item, duration)
        else:
            # Instant removal for reduced motion
            self._remove_item_immediate(row, item)

        return True

    def _animate_item_out(
        self,
        widget: AnimatedItemWidget,
        row: int,
        item: QListWidgetItem,
        duration: int,
    ) -> None:
        """
        Animate item disappearing with fade and slide.

        Args:
            widget: The item widget to animate.
            row: The row index.
            item: The list widget item.
            duration: Animation duration in milliseconds.
        """
        if not widget.opacity_effect:
            self._remove_item_immediate(row, item)
            return

        # Create animation group
        group = QParallelAnimationGroup(self)

        # Fade out animation
        fade_anim = QPropertyAnimation(widget.opacity_effect, b"opacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(widget.opacity_effect.opacity())
        fade_anim.setEndValue(0.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        group.addAnimation(fade_anim)

        # Slide out animation
        slide_offset = -20
        end_pos = QPoint(widget.pos().x(), widget.pos().y() + slide_offset)

        slide_anim = QPropertyAnimation(widget, b"pos")
        slide_anim.setDuration(duration)
        slide_anim.setStartValue(widget.pos())
        slide_anim.setEndValue(end_pos)
        slide_anim.setEasingCurve(QEasingCurve.Type.InCubic)
        group.addAnimation(slide_anim)

        # Track animation
        self._active_animations[row] = group

        # Remove item after animation completes
        group.finished.connect(lambda: self._remove_item_immediate(row, item))

        group.start()
        logger.debug(f"Started removal animation for row {row}")

    def _remove_item_immediate(self, row: int, item: QListWidgetItem) -> None:
        """
        Immediately remove an item without animation.

        Args:
            row: The row index.
            item: The list widget item to remove.
        """
        # Cleanup tracking
        if row in self._item_widgets:
            del self._item_widgets[row]
        if row in self._active_animations:
            del self._active_animations[row]

        # Remove from list
        self.takeItem(row)

        # Re-index remaining widgets
        self._reindex_widgets(row)

        logger.debug(f"Removed item at row {row}")
        self.item_animation_finished.emit(row)

    def _reindex_widgets(self, removed_row: int) -> None:
        """
        Re-index widget tracking after item removal.

        Args:
            removed_row: The row that was removed.
        """
        new_widgets: Dict[int, AnimatedItemWidget] = {}
        for old_row, widget in self._item_widgets.items():
            if old_row > removed_row:
                new_widgets[old_row - 1] = widget
            elif old_row < removed_row:
                new_widgets[old_row] = widget
        self._item_widgets = new_widgets

    def _on_animation_finished(self, row: int) -> None:
        """
        Handle animation completion.

        Args:
            row: The row index that finished animating.
        """
        if row in self._active_animations:
            del self._active_animations[row]
        self.item_animation_finished.emit(row)

    def _on_selection_changed(self, current_row: int) -> None:
        """
        Handle selection change with optional highlight animation.

        Args:
            current_row: The newly selected row.
        """
        # Selection animation is handled by stylesheet for simplicity
        # The :selected pseudo-class provides instant feedback
        # More complex animations would require custom painting
        self._last_selected_row = current_row

    def clear(self) -> None:
        """Clear all items, stopping any active animations."""
        # Stop all active animations
        for group in list(self._active_animations.values()):
            group.stop()
        self._active_animations.clear()
        self._item_widgets.clear()

        # Clear list
        super().clear()

    def addItem(self, *args, **kwargs) -> None:
        """
        Override addItem to use animated version.

        For non-animated addition, use QListWidget.addItem directly
        by calling super().addItem().
        """
        # If called with a string, use animated version
        if args and isinstance(args[0], str):
            self.addAnimatedItem(args[0])
        else:
            super().addItem(*args, **kwargs)

    def insertItem(self, row: int, *args, **kwargs) -> None:
        """
        Override insertItem to support both animated and non-animated insertion.

        Args:
            row: Row index to insert at.
            *args: Standard QListWidget.insertItem arguments.
            **kwargs: Additional arguments.
        """
        # For string items at row 0, use animated with from_top=True
        if args and isinstance(args[0], str):
            if row == 0:
                self.addAnimatedItem(args[0], from_top=True)
            else:
                # For other positions, use base implementation
                # and wrap with animation
                item = QListWidgetItem(args[0])
                super().insertItem(row, item)
        else:
            super().insertItem(row, *args, **kwargs)


def create_animated_list_widget(
    parent: Optional[QWidget] = None,
) -> AnimatedListWidget:
    """
    Factory function to create an AnimatedListWidget.

    Args:
        parent: Optional parent widget.

    Returns:
        A configured AnimatedListWidget instance.
    """
    widget = AnimatedListWidget(parent)
    return widget
