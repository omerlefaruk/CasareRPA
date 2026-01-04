"""
Structural Components v2 - Epic 5.1 Component Library.

Layout and container components for organizing UI structure.
Provides SectionHeader, Divider, EmptyState, and Card components.

Components:
    SectionHeader: Labeled section with optional collapse button
    Divider: Visual separator line (horizontal/vertical)
    EmptyState: Placeholder for empty content areas
    Card: Container with border/background and optional title

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import (
        SectionHeader,
        Divider,
        EmptyState,
        Card,
        create_divider,
        create_empty_state,
        create_card,
    )

    # Section header with collapse
    header = SectionHeader(text="Settings", collapsible=True, collapsed=False)
    header.collapsed_changed.connect(lambda collapsed: print(f"Collapsed: {collapsed}"))

    # Divider
    divider = create_divider(orientation="horizontal", margin="standard")

    # Empty state
    empty = EmptyState(
        icon="inbox",
        text="No items found",
        action_text="Create new",
        action_enabled=True
    )
    empty.action_clicked.connect(lambda: print("Action clicked"))

    # Card with title and content
    card = Card(title="Summary", content_widget=my_widget, border=True)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import (
    BasePrimitive,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# TYPE ALIASES
# =============================================================================

MarginPreset = Literal[
    "none", "tight", "compact", "standard", "comfortable", "spacious", "dialog", "panel", "form_row"
]
Orientation = Literal["horizontal", "vertical"]


# =============================================================================
# SECTION HEADER
# =============================================================================


class SectionHeader(BasePrimitive):
    """
    Labeled section header with optional collapse button.

    Displays a section title with an optional collapse/expand button.
    A line separator appears below the header text.

    Props:
        text: Section header text
        collapsible: Whether collapse button is shown (default: False)
        collapsed: Initial collapsed state (default: False)
        level: Heading level for font size (1=largest, 3=smallest, default: 2)
        enabled: Initial enabled state

    Signals:
        collapsed_changed: Emitted when collapsed state changes (bool)

    Example:
        header = SectionHeader(text="Configuration", collapsible=True)
        header.collapsed_changed.connect(lambda c: content_widget.setHidden(c))
    """

    collapsed_changed = Signal(bool)

    # Level font size mapping
    _LEVEL_FONTS = {
        1: "heading_lg",
        2: "heading_md",
        3: "heading_sm",
    }

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        collapsible: bool = False,
        collapsed: bool = False,
        level: int = 2,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the section header.

        Args:
            text: Section header text
            parent: Optional parent widget
            collapsible: Whether to show collapse button
            collapsed: Initial collapsed state
            level: Heading level (1-3) for font size
            enabled: Initial enabled state
        """
        self._text: str = text
        self._collapsible: bool = collapsible
        self._collapsed: bool = collapsed
        self._level: int = max(1, min(3, level))

        # Initialize BasePrimitive (will call setup_ui)
        super().__init__(parent)

        # Set enabled state after initialization
        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, TOKENS_V2.spacing.xs)
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Header label
        self._label = QLabel(self._text)
        font_variant = self._LEVEL_FONTS[self._level]
        self._set_font_on_widget(self._label, font_variant)
        self._label.setStyleSheet(f"color: {THEME_V2.text_header};")
        layout.addWidget(self._label)

        # Collapse button (if collapsible)
        if self._collapsible:
            self._collapse_btn = QToolButton(self)
            self._collapse_btn.setFixedSize(
                TOKENS_V2.sizes.icon_sm,
                TOKENS_V2.sizes.icon_sm,
            )
            self._collapse_btn.setIcon(get_icon("chevron-down", size=TOKENS_V2.sizes.icon_sm))
            self._collapse_btn.setAutoRaise(True)
            self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self._collapse_btn)
        else:
            self._collapse_btn = None

        layout.addStretch()

        # Separator line at bottom
        self._separator = QFrame(self)
        self._separator.setFrameShape(QFrame.Shape.HLine)
        self._separator.setFrameShadow(QFrame.Shadow.Sunken)
        self._separator.setFixedHeight(1)

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        if self._collapse_btn is not None:
            self._collapse_btn.clicked.connect(self._on_collapse_clicked)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        return f"""
            SectionHeader {{
                background: transparent;
            }}
            QFrame {{
                background: {THEME_V2.border};
                border: none;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                padding: 0px;
            }}
            QToolButton:hover {{
                background: {THEME_V2.bg_hover};
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """

    def _set_font_on_widget(self, widget: QWidget, variant: str) -> None:
        """Set font on a widget using TOKENS_V2.typography."""
        from PySide6.QtGui import QFont

        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(getattr(TOKENS_V2.typography, variant))
        # Use QFont.Weight enum for PySide6 6.5+
        try:
            font.setWeight(QFont.Weight.Medium)
        except (AttributeError, TypeError):
            # Fallback for older versions
            font.setWeight(TOKENS_V2.typography.weight_medium)
        widget.setFont(font)

    @Slot()
    def _on_collapse_clicked(self) -> None:
        """Handle collapse button click."""
        self.set_collapsed(not self._collapsed)

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def set_text(self, text: str) -> None:
        """
        Set the header text.

        Args:
            text: New header text
        """
        self._text = text
        self._label.setText(text)

    def text(self) -> str:
        """Get the header text."""
        return self._text

    def set_collapsed(self, collapsed: bool) -> None:
        """
        Set the collapsed state.

        Args:
            collapsed: Whether section should be collapsed
        """
        if self._collapsed == collapsed:
            return

        self._collapsed = collapsed
        self._update_collapse_icon()
        self.collapsed_changed.emit(collapsed)

    def is_collapsed(self) -> bool:
        """Get the collapsed state."""
        return self._collapsed

    def toggle(self) -> None:
        """Toggle the collapsed state."""
        self.set_collapsed(not self._collapsed)

    def _update_collapse_icon(self) -> None:
        """Update collapse button icon based on state."""
        if self._collapse_btn is None:
            return

        # Use chevron-down (pointing right when collapsed via transform)
        # or use different icons
        icon_name = "chevron-right" if self._collapsed else "chevron-down"
        self._collapse_btn.setIcon(get_icon(icon_name, size=TOKENS_V2.sizes.icon_sm))

    def resizeEvent(self, event) -> None:
        """Handle resize event to position separator line."""
        super().resizeEvent(event)
        if hasattr(self, "_separator"):
            self._separator.setGeometry(0, self.height() - 1, self.width(), 1)


# =============================================================================
# DIVIDER
# =============================================================================


class Divider(QFrame):
    """
    Visual separator line.

    Simple horizontal or vertical divider for visual separation.
    Uses THEME_V2.border color for consistent styling.

    Props:
        orientation: "horizontal" or "vertical" (default: "horizontal")
        margin: Margin preset or tuple (default: "standard")

    Example:
        # Horizontal divider with standard margins
        divider = Divider(orientation="horizontal", margin="standard")

        # Vertical divider with tight margins
        divider = Divider(orientation="vertical", margin="tight")

        # Using convenience function
        from casare_rpa.presentation.canvas.ui.widgets.primitives.structural import create_divider
        divider = create_divider()
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        orientation: Orientation = "horizontal",
        margin: MarginPreset | tuple[int, int, int, int] = "standard",
    ) -> None:
        """
        Initialize the divider.

        Args:
            parent: Optional parent widget
            orientation: Divider orientation (horizontal/vertical)
            margin: Margin preset or (left, top, right, bottom) tuple
        """
        super().__init__(parent)

        self._orientation: Orientation = orientation
        self._margin = self._resolve_margin(margin)

        self._setup_ui()

        logger.debug(f"{self.__class__.__name__} created: orientation={orientation}")

    def _setup_ui(self) -> None:
        """Setup divider UI properties."""
        # Set frame shape based on orientation
        if self._orientation == "horizontal":
            self.setFrameShape(QFrame.Shape.HLine)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFrameShape(QFrame.Shape.VLine)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.setFrameShadow(QFrame.Shadow.Sunken)

    def _resolve_margin(
        self, margin: MarginPreset | tuple[int, int, int, int]
    ) -> tuple[int, int, int, int]:
        """Resolve margin preset to tuple."""
        if isinstance(margin, tuple):
            return margin
        return getattr(TOKENS_V2.margin, margin)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        return f"""
            Divider {{
                background: {THEME_V2.border};
                border: none;
            }}
        """

    def stylesheet(self) -> str:
        """Get the stylesheet."""
        return self._get_v2_stylesheet()

    def apply_stylesheet(self) -> None:
        """Apply v2 theme stylesheet."""
        self.setStyleSheet(self.stylesheet())


# =============================================================================
# EMPTY STATE
# =============================================================================


class EmptyState(BasePrimitive):
    """
    Placeholder widget for empty content areas.

    Displays an icon, message text, and optional action button.
    Centered layout with muted colors for subtle appearance.

    Props:
        icon: Icon name (for get_icon()) or QIcon
        text: Primary message text
        action_text: Optional action button text
        action_enabled: Whether action button is enabled (default: True)
        enabled: Initial enabled state

    Signals:
        action_clicked: Emitted when action button is clicked

    Example:
        empty = EmptyState(
            icon="inbox",
            text="No workflows yet",
            action_text="Create your first workflow"
        )
        empty.action_clicked.connect(lambda: show_create_dialog())
    """

    action_clicked = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        icon: str | QIcon | None = None,
        text: str = "",
        action_text: str = "",
        action_enabled: bool = True,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the empty state.

        Args:
            parent: Optional parent widget
            icon: Icon name (string) or QIcon
            text: Primary message text
            action_text: Optional action button text
            action_enabled: Whether action button is enabled
            enabled: Initial enabled state
        """
        self._icon_name: str | None = icon if isinstance(icon, str) else None
        self._icon: QIcon | None = icon if isinstance(icon, QIcon) else None
        self._text: str = text
        self._action_text: str = action_text
        self._action_enabled: bool = action_enabled

        super().__init__(parent)

        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(*self._get_margins("comfortable"))
        layout.setSpacing(TOKENS_V2.spacing.md)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icon (if provided)
        if self._icon_name or self._icon:
            self._icon_label = QLabel(self)
            if self._icon_name:
                self._icon_label.setPixmap(
                    get_icon(self._icon_name, size=TOKENS_V2.sizes.icon_lg).pixmap(
                        TOKENS_V2.sizes.icon_lg, TOKENS_V2.sizes.icon_lg
                    )
                )
            elif self._icon:
                self._icon_label.setPixmap(
                    self._icon.pixmap(TOKENS_V2.sizes.icon_lg, TOKENS_V2.sizes.icon_lg)
                )
            self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._icon_label.setStyleSheet(f"color: {THEME_V2.text_muted};")
            layout.addWidget(self._icon_label)
        else:
            self._icon_label = None

        # Text label
        self._text_label = QLabel(self._text, self)
        self._set_font_on_widget(self._text_label, "body")
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setStyleSheet(f"color: {THEME_V2.text_muted};")
        self._text_label.setWordWrap(True)
        layout.addWidget(self._text_label)

        # Action button (if text provided)
        if self._action_text:
            self._action_btn = QPushButton(self._action_text, self)
            self._action_btn.setEnabled(self._action_enabled)
            self._action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # Center the button
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            btn_layout.addWidget(self._action_btn)
            btn_layout.addStretch()
            layout.addLayout(btn_layout)
        else:
            self._action_btn = None

        # Add stretch at bottom for centering
        layout.addStretch()

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        if self._action_btn is not None:
            self._action_btn.clicked.connect(self._on_action_clicked)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        return f"""
            EmptyState {{
                background: transparent;
            }}
            QPushButton {{
                background: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
            QPushButton:pressed {{
                background: {THEME_V2.border};
            }}
            QPushButton:disabled {{
                color: {THEME_V2.text_disabled};
                background: {THEME_V2.bg_component};
            }}
        """

    def _set_font_on_widget(self, widget: QWidget, variant: str) -> None:
        """Set font on a widget using TOKENS_V2.typography."""
        from PySide6.QtGui import QFont

        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(getattr(TOKENS_V2.typography, variant))
        widget.setFont(font)

    @Slot()
    def _on_action_clicked(self) -> None:
        """Handle action button click."""
        self.action_clicked.emit()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def set_text(self, text: str) -> None:
        """
        Set the message text.

        Args:
            text: New message text
        """
        self._text = text
        self._text_label.setText(text)

    def text(self) -> str:
        """Get the message text."""
        return self._text

    def set_action_text(self, text: str) -> None:
        """
        Set the action button text.

        Args:
            text: New action button text
        """
        self._action_text = text
        if self._action_btn is not None:
            self._action_btn.setText(text)
        else:
            # Recreate UI if button wasn't there before
            self._action_btn = QPushButton(text, self)
            self._action_btn.setEnabled(self._action_enabled)
            # Note: full UI rebuild would be needed for proper insertion

    def set_action_enabled(self, enabled: bool) -> None:
        """
        Set whether the action button is enabled.

        Args:
            enabled: Whether action button should be enabled
        """
        self._action_enabled = enabled
        if self._action_btn is not None:
            self._action_btn.setEnabled(enabled)


# =============================================================================
# CARD
# =============================================================================


class Card(BasePrimitive):
    """
    Container widget with border/background and optional title.

    Provides a styled container for grouping related content.
    Can display a title in the header area and an optional close button.

    Props:
        title: Card title text (optional)
        content_widget: Main content widget (optional, can add later)
        border: Whether to show border (default: True)
        closable: Whether to show close button (default: False)
        enabled: Initial enabled state

    Signals:
        close_requested: Emitted when close button is clicked
        title_changed: Emitted when title changes (str)

    Example:
        card = Card(
            title="Settings",
            content_widget=settings_form,
            border=True,
            closable=True
        )
        card.close_requested.connect(lambda: card.deleteLater())

        # Adding content later
        card = Card(title="Details")
        card.set_content(my_widget)
    """

    close_requested = Signal()
    title_changed = Signal(str)

    def __init__(
        self,
        parent: QWidget | None = None,
        title: str = "",
        content_widget: QWidget | None = None,
        border: bool = True,
        closable: bool = False,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the card.

        Args:
            parent: Optional parent widget
            title: Optional card title
            content_widget: Optional main content widget
            border: Whether to show border
            closable: Whether to show close button
            enabled: Initial enabled state
        """
        self._title: str = title
        self._content_widget: QWidget | None = content_widget
        self._border: bool = border
        self._closable: bool = closable

        super().__init__(parent)

        # Add content widget if provided
        if self._content_widget is not None:
            self.set_content(self._content_widget)

        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header (if title or closable)
        if self._title or self._closable:
            self._header_widget = QWidget(self)
            header_layout = QHBoxLayout(self._header_widget)
            header_layout.setContentsMargins(
                TOKENS_V2.spacing.md,
                TOKENS_V2.spacing.sm,
                TOKENS_V2.spacing.sm,
                TOKENS_V2.spacing.sm,
            )
            header_layout.setSpacing(TOKENS_V2.spacing.sm)

            # Title label
            if self._title:
                self._title_label = QLabel(self._title, self._header_widget)
                self._set_font_on_widget(self._title_label, "heading_sm")
                self._title_label.setStyleSheet(f"color: {THEME_V2.text_header};")
                header_layout.addWidget(self._title_label)
            else:
                self._title_label = None

            header_layout.addStretch()

            # Close button
            if self._closable:
                self._close_btn = QToolButton(self._header_widget)
                self._close_btn.setFixedSize(
                    TOKENS_V2.sizes.icon_sm,
                    TOKENS_V2.sizes.icon_sm,
                )
                self._close_btn.setIcon(get_icon("x", size=TOKENS_V2.sizes.icon_sm))
                self._close_btn.setAutoRaise(True)
                self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                header_layout.addWidget(self._close_btn)
            else:
                self._close_btn = None

            layout.addWidget(self._header_widget)

            # Header separator
            self._header_separator = QFrame(self)
            self._header_separator.setFrameShape(QFrame.Shape.HLine)
            self._header_separator.setFixedHeight(1)
            layout.addWidget(self._header_separator)
        else:
            self._header_widget = None
            self._title_label = None
            self._close_btn = None
            self._header_separator = None

        # Content container
        self._content_container = QWidget(self)
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(
            TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md
        )
        self._content_layout.setSpacing(TOKENS_V2.spacing.md)
        layout.addWidget(self._content_container, 1)  # Expand to fill

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        if self._close_btn is not None:
            self._close_btn.clicked.connect(self._on_close_clicked)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        border_style = f"1px solid {THEME_V2.border}" if self._border else "none"
        return f"""
            Card {{
                background: {THEME_V2.bg_elevated};
                border: {border_style};
                border-radius: {TOKENS_V2.radius.md}px;
            }}
            QWidget {{
                background: transparent;
            }}
            QLabel {{
                background: transparent;
            }}
            QFrame {{
                background: {THEME_V2.border};
                border: none;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                padding: 0px;
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
            QToolButton:hover {{
                background: {THEME_V2.bg_hover};
            }}
        """

    def _set_font_on_widget(self, widget: QWidget, variant: str) -> None:
        """Set font on a widget using TOKENS_V2.typography."""
        from PySide6.QtGui import QFont

        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(getattr(TOKENS_V2.typography, variant))
        # Use QFont.Weight enum for PySide6 6.5+
        try:
            font.setWeight(QFont.Weight.Medium)
        except (AttributeError, TypeError):
            # Fallback for older versions
            font.setWeight(TOKENS_V2.typography.weight_medium)
        widget.setFont(font)

    @Slot()
    def _on_close_clicked(self) -> None:
        """Handle close button click."""
        self.close_requested.emit()

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def set_title(self, title: str) -> None:
        """
        Set the card title.

        Args:
            title: New title text
        """
        self._title = title
        if self._title_label is not None:
            self._title_label.setText(title)
        self.title_changed.emit(title)

    def title(self) -> str:
        """Get the card title."""
        return self._title

    def set_content(self, widget: QWidget) -> None:
        """
        Set the main content widget.

        Replaces any existing content.

        Args:
            widget: Content widget to display
        """
        # Clear existing content
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Add new content
        self._content_widget = widget
        if widget is not None:
            self._content_layout.addWidget(widget)

    def content(self) -> QWidget | None:
        """Get the content widget."""
        return self._content_widget

    def set_border(self, border: bool) -> None:
        """
        Set whether border is shown.

        Args:
            border: Whether to show border
        """
        self._border = border
        # Re-apply stylesheet to update border
        self._apply_v2_theme()

    def has_border(self) -> bool:
        """Get whether border is shown."""
        return self._border


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_divider(
    orientation: Orientation = "horizontal",
    margin: MarginPreset | tuple[int, int, int, int] = "standard",
    parent: QWidget | None = None,
) -> Divider:
    """
    Convenience function to create a divider.

    Args:
        orientation: Divider orientation (horizontal/vertical)
        margin: Margin preset or tuple
        parent: Optional parent widget

    Returns:
        Configured Divider widget
    """
    divider = Divider(orientation=orientation, margin=margin, parent=parent)
    divider.apply_stylesheet()
    return divider


def create_empty_state(
    icon: str | QIcon | None = None,
    text: str = "",
    action_text: str = "",
    action_enabled: bool = True,
    parent: QWidget | None = None,
) -> EmptyState:
    """
    Convenience function to create an empty state.

    Args:
        icon: Icon name (string) or QIcon
        text: Message text
        action_text: Action button text
        action_enabled: Whether action button is enabled
        parent: Optional parent widget

    Returns:
        Configured EmptyState widget
    """
    return EmptyState(
        icon=icon,
        text=text,
        action_text=action_text,
        action_enabled=action_enabled,
        parent=parent,
    )


def create_card(
    title: str = "",
    content_widget: QWidget | None = None,
    border: bool = True,
    closable: bool = False,
    parent: QWidget | None = None,
) -> Card:
    """
    Convenience function to create a card.

    Args:
        title: Card title
        content_widget: Main content widget
        border: Whether to show border
        closable: Whether to show close button
        parent: Optional parent widget

    Returns:
        Configured Card widget
    """
    return Card(
        title=title,
        content_widget=content_widget,
        border=border,
        closable=closable,
        parent=parent,
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Components
    "SectionHeader",
    "Divider",
    "EmptyState",
    "Card",
    # Types
    "MarginPreset",
    "Orientation",
    # Convenience functions
    "create_divider",
    "create_empty_state",
    "create_card",
]
