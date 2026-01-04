"""
Feedback Components v2 - Epic 5.1 Component Library.

User feedback and indication components for providing visual feedback.
Provides Badge, Tooltip helper, InlineAlert, Breadcrumb, and Avatar components.

Components:
    Badge: Small colored indicator/label (dot, count, label variants)
    Tooltip: Helper wrapper for styled tooltips
    InlineAlert: Contextual banner message with dismiss button
    Breadcrumb: Path navigation with clickable items
    Avatar: User/profile placeholder with initials or image

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.feedback import (
        Badge,
        set_tooltip,
        InlineAlert,
        Breadcrumb,
        Avatar,
        create_badge,
        create_alert,
        create_breadcrumb,
        create_avatar,
    )

    # Badge for status indicators
    badge = Badge(variant="dot", color="success")
    count_badge = Badge(variant="count", text="5", color="error")
    label_badge = Badge(variant="label", text="New", color="primary")

    # Tooltip helper
    set_tooltip(widget, "Hover for help", delay_ms=500)

    # Inline alert
    alert = InlineAlert(
        text="Settings saved successfully",
        variant="success",
        dismissible=True
    )
    alert.dismissed.connect(lambda: print("Alert dismissed"))

    # Breadcrumb navigation
    breadcrumb = Breadcrumb(
        items=[
            {"label": "Home", "data": "home"},
            {"label": "Settings", "data": "settings"},
            {"label": "Profile", "data": "profile"},
        ],
        separator=">"
    )
    breadcrumb.item_clicked.connect(lambda data: navigate_to(data))

    # Avatar
    avatar = Avatar(text="JD", size="md", variant="circle")
    avatar_with_image = Avatar(image_path="/path/to/photo.png", size="lg")

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
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
    from PySide6.QtGui import QPainter, QPaintEvent


# =============================================================================
# TYPE ALIASES
# =============================================================================

BadgeVariant = Literal["dot", "count", "label"]
BadgeColor = Literal["primary", "success", "warning", "error", "info"]
AlertVariant = Literal["info", "warning", "error", "success"]
AvatarSize = Literal["sm", "md", "lg"]
AvatarVariant = Literal["circle", "square"]
BreadcrumbItem = dict[str, str]  # {"label": str, "data": str, "value": str (alias)}


# =============================================================================
# COLOR MAPPINGS
# =============================================================================

_BADGE_COLORS: dict[str, str] = {
    "primary": THEME_V2.primary,
    "success": THEME_V2.success,
    "warning": THEME_V2.warning,
    "error": THEME_V2.error,
    "info": THEME_V2.info,
    None: THEME_V2.primary,
}

_ALERT_COLORS: dict[str, tuple[str, str]] = {
    "info": (THEME_V2.info, THEME_V2.bg_elevated),
    "warning": (THEME_V2.warning, THEME_V2.bg_elevated),
    "error": (THEME_V2.error, THEME_V2.bg_elevated),
    "success": (THEME_V2.success, THEME_V2.bg_elevated),
}

_ALERT_ICONS: dict[str, str] = {
    "info": "info",
    "warning": "alert-triangle",
    "error": "alert-circle",
    "success": "check-circle",
}


# =============================================================================
# BADGE
# =============================================================================


class Badge(QFrame):
    """
    Small colored indicator/label.

    Visual indicator for status, counts, or labels. Three variants:
    - "dot": 8px circle for status indicators
    - "count": Small rounded rectangle with number (notification counts)
    - "label": Text label with colored background

    Props:
        text: Display text (for count/label variants)
        variant: Badge type ("dot", "count", or "label")
        color: Color name or None for default primary

    Example:
        # Status dot
        status_dot = Badge(variant="dot", color="success")

        # Notification count
        count = Badge(variant="count", text="5", color="error")

        # Feature label
        label = Badge(variant="label", text="NEW", color="primary")
    """

    _DOT_SIZE = 8
    _COUNT_MIN_WIDTH = 16

    def __init__(
        self,
        parent: QWidget | None = None,
        text: str = "",
        variant: BadgeVariant = "dot",
        color: BadgeColor | None = None,
    ) -> None:
        """
        Initialize the badge.

        Args:
            parent: Optional parent widget
            text: Display text (for count/label variants)
            variant: Badge type (dot/count/label)
            color: Color name (primary/success/warning/error/info)
        """
        super().__init__(parent)

        self._text: str = text
        self._variant: BadgeVariant = variant
        self._color_name: BadgeColor | None = color
        self._color: str = _BADGE_COLORS.get(color, THEME_V2.primary)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup badge UI based on variant."""
        if self._variant == "dot":
            self._setup_dot_variant()
        elif self._variant == "count":
            self._setup_count_variant()
        else:  # label
            self._setup_label_variant()

        self._apply_stylesheet()

    def _setup_dot_variant(self) -> None:
        """Setup dot variant - simple colored circle."""
        self.setFixedSize(self._DOT_SIZE, self._DOT_SIZE)
        self.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

    def _setup_count_variant(self) -> None:
        """Setup count variant - small rounded rectangle with number."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.xxs,
            0,
            TOKENS_V2.spacing.xxs,
            0,
        )

        self._label = QLabel(self._text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_on_primary};
                font-size: {TOKENS_V2.typography.caption}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                background: transparent;
            }}
        """)
        layout.addWidget(self._label)

        # Calculate size based on text
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self._text)
        width = max(self._COUNT_MIN_WIDTH, text_width + TOKENS_V2.spacing.sm)
        self.setFixedSize(width, TOKENS_V2.sizes.icon_sm)

    def _setup_label_variant(self) -> None:
        """Setup label variant - text label with colored background."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xxs,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.xxs,
        )

        self._label = QLabel(self._text, self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_on_primary};
                font-size: {TOKENS_V2.typography.body_sm}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                background: transparent;
            }}
        """)
        layout.addWidget(self._label)

        # Calculate size based on text
        metrics = self.fontMetrics()
        text_width = metrics.horizontalAdvance(self._text)
        width = text_width + TOKENS_V2.spacing.md * 2
        self.setFixedSize(width, TOKENS_V2.sizes.button_sm - 2)

    def _apply_stylesheet(self) -> None:
        """Apply v2 theme stylesheet."""
        if self._variant == "dot":
            stylesheet = f"""
                Badge {{
                    background: {self._color};
                    border: none;
                    border-radius: {self._DOT_SIZE // 2}px;
                }}
            """
        else:  # count and label
            stylesheet = f"""
                Badge {{
                    background: {self._color};
                    border: none;
                    border-radius: {TOKENS_V2.radius.sm}px;
                }}
            """
        self.setStyleSheet(stylesheet)

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_text(self, text: str) -> None:
        """
        Set the badge text.

        Only affects count and label variants.

        Args:
            text: New text to display
        """
        self._text = text
        if self._variant == "dot":
            return

        if hasattr(self, "_label"):
            self._label.setText(text)
            # Recalculate size for label variant
            if self._variant == "label":
                metrics = self.fontMetrics()
                text_width = metrics.horizontalAdvance(text)
                width = text_width + TOKENS_V2.spacing.md * 2
                self.setFixedSize(width, TOKENS_V2.sizes.button_sm - 2)

    def text(self) -> str:
        """Get the badge text."""
        return self._text if self._variant != "dot" else ""

    def set_color(self, color: BadgeColor | None) -> None:
        """
        Set the badge color.

        Args:
            color: Color name (primary/success/warning/error/info) or None
        """
        self._color_name = color
        self._color = _BADGE_COLORS.get(color, THEME_V2.primary)
        self._apply_stylesheet()

    def get_color(self) -> BadgeColor | None:
        """Get the badge color name."""
        return self._color_name

    def set_variant(self, variant: BadgeVariant) -> None:
        """
        Set the badge variant.

        Rebuilds the UI for the new variant.

        Args:
            variant: New variant type (dot/count/label)
        """
        if self._variant == variant:
            return

        # Clear existing layout
        layout = self.layout()
        if layout:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

        self._variant = variant
        self._setup_ui()

    def get_variant(self) -> BadgeVariant:
        """Get the badge variant."""
        return self._variant


# =============================================================================
# TOOLTIP HELPER
# =============================================================================


def set_tooltip(
    widget: QWidget,
    text: str,
    delay_ms: int = 500,
) -> None:
    """
    Apply styled tooltip to a widget.

    Helper function that wraps QWidget.setToolTip() and applies
    v2 tooltip styling.

    Args:
        widget: Widget to add tooltip to
        text: Tooltip text
        delay_ms: Delay before showing tooltip (default: 500ms)

    Example:
        set_tooltip(my_button, "Click to save changes")
        set_tooltip(help_icon, "View documentation", delay_ms=1000)
    """
    widget.setToolTip(text)
    widget.setProperty("tooltip_delay_ms", delay_ms)
    logger.debug(f"Tooltip set on {widget.__class__.__name__}: delay={delay_ms}ms")


# =============================================================================
# INLINE ALERT
# =============================================================================


class InlineAlert(BasePrimitive):
    """
    Contextual banner message with optional dismiss button.

    Displays a short message with an icon, styled by variant.
    Can be dismissible with an X button.

    Props:
        text: Alert message text
        variant: Alert type (info/warning/error/success)
        dismissible: Whether to show dismiss button (default: False)
        enabled: Initial enabled state

    Signals:
        dismissed: Emitted when dismiss button is clicked

    Example:
        alert = InlineAlert(
            text="Changes saved successfully",
            variant="success",
            dismissible=True
        )
        alert.dismissed.connect(lambda: alert.hide())

        error_alert = InlineAlert(
            text="Failed to save. Please try again.",
            variant="error"
        )
    """

    dismissed = Signal()

    def __init__(
        self,
        parent: QWidget | None = None,
        text: str = "",
        variant: AlertVariant = "info",
        dismissible: bool = False,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the inline alert.

        Args:
            parent: Optional parent widget
            text: Alert message text
            variant: Alert type (info/warning/error/success)
            dismissible: Whether to show dismiss button
            enabled: Initial enabled state
        """
        self._text: str = text
        self._variant: AlertVariant = variant
        self._dismissible: bool = dismissible
        self._icon_color, self._bg_color = _ALERT_COLORS.get(variant, _ALERT_COLORS["info"])
        self._icon_name: str = _ALERT_ICONS.get(variant, "info")

        super().__init__(parent)

        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
            TOKENS_V2.spacing.sm,
            TOKENS_V2.spacing.xs,
        )
        layout.setSpacing(TOKENS_V2.spacing.sm)

        # Icon
        self._icon_label = QLabel(self)
        icon_pixmap = get_icon(self._icon_name, size=TOKENS_V2.sizes.icon_md).pixmap(
            TOKENS_V2.sizes.icon_md, TOKENS_V2.sizes.icon_md
        )
        self._icon_label.setPixmap(icon_pixmap)
        layout.addWidget(self._icon_label)

        # Text
        self._text_label = QLabel(self._text, self)
        self._set_font_on_widget(self._text_label, "body_sm")
        self._text_label.setWordWrap(True)
        self._text_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        layout.addWidget(self._text_label, 1)

        # Dismiss button
        if self._dismissible:
            self._dismiss_btn = QToolButton(self)
            self._dismiss_btn.setFixedSize(
                TOKENS_V2.sizes.icon_sm,
                TOKENS_V2.sizes.icon_sm,
            )
            self._dismiss_btn.setIcon(get_icon("x", size=TOKENS_V2.sizes.icon_sm))
            self._dismiss_btn.setAutoRaise(True)
            self._dismiss_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(self._dismiss_btn)
        else:
            self._dismiss_btn = None

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        if self._dismiss_btn is not None:
            self._dismiss_btn.clicked.connect(self._on_dismiss)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        # Add subtle border colored by variant
        return f"""
            InlineAlert {{
                background: {self._bg_color};
                border: 1px solid {self._icon_color};
                border-radius: {TOKENS_V2.radius.sm}px;
            }}
            QLabel {{
                background: transparent;
                color: {THEME_V2.text_primary};
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
        widget.setFont(font)

    @Slot()
    def _on_dismiss(self) -> None:
        """Handle dismiss button click."""
        self.dismissed.emit()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_text(self, text: str) -> None:
        """
        Set the alert message text.

        Args:
            text: New message text
        """
        self._text = text
        self._text_label.setText(text)

    def text(self) -> str:
        """Get the alert message text."""
        return self._text

    def set_variant(self, variant: AlertVariant) -> None:
        """
        Set the alert variant.

        Updates colors and icon.

        Args:
            variant: New alert type (info/warning/error/success)
        """
        self._variant = variant
        self._icon_color, self._bg_color = _ALERT_COLORS.get(variant, _ALERT_COLORS["info"])
        self._icon_name = _ALERT_ICONS.get(variant, "info")

        # Update icon
        icon_pixmap = get_icon(self._icon_name, size=TOKENS_V2.sizes.icon_md).pixmap(
            TOKENS_V2.sizes.icon_md, TOKENS_V2.sizes.icon_md
        )
        self._icon_label.setPixmap(icon_pixmap)

        # Re-apply stylesheet for new colors
        self._apply_v2_theme()

    def get_variant(self) -> AlertVariant:
        """Get the alert variant."""
        return self._variant

    def set_dismissible(self, dismissible: bool) -> None:
        """
        Set whether the alert is dismissible.

        Note: Requires UI rebuild to add/remove button.

        Args:
            dismissible: Whether to show dismiss button
        """
        if self._dismissible == dismissible:
            return

        self._dismissible = dismissible
        # Full UI rebuild would be needed here
        # For now, just hide/show existing button
        if hasattr(self, "_dismiss_btn") and self._dismiss_btn is not None:
            self._dismiss_btn.setVisible(dismissible)


# =============================================================================
# BREADCRUMB
# =============================================================================


class Breadcrumb(BasePrimitive):
    """
    Path navigation with clickable items.

    Displays a horizontal trail of navigation items.
    Items are clickable except the last (current location).

    Props:
        items: List of dicts with "label" and "data"/"value" keys
        separator: Separator text between items (default: "/")
        enabled: Initial enabled state

    Signals:
        item_clicked: Emitted when a breadcrumb item is clicked (payload is data value)

    Example:
        breadcrumb = Breadcrumb(
            items=[
                {"label": "Home", "data": "home"},
                {"label": "Projects", "data": "projects"},
                {"label": "My Workflow", "data": "workflow-123"},
            ],
            separator=">"
        )
        breadcrumb.item_clicked.connect(lambda data: navigate_to(data))
    """

    item_clicked = Signal(str)

    _SIZE_MAP: dict[AvatarSize, int] = {
        "sm": TOKENS_V2.sizes.button_sm,
        "md": TOKENS_V2.sizes.button_md,
        "lg": TOKENS_V2.sizes.button_lg,
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        items: list[BreadcrumbItem] | None = None,
        separator: str = "/",
        enabled: bool = True,
    ) -> None:
        """
        Initialize the breadcrumb.

        Args:
            parent: Optional parent widget
            items: List of breadcrumb items (dict with label and data/value)
            separator: Separator text between items
            enabled: Initial enabled state
        """
        self._items: list[BreadcrumbItem] = items or []
        self._separator: str = separator
        self._item_labels: list[QLabel] = []

        super().__init__(parent)

        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.xs)

        self._refresh_items(layout)

    def _refresh_items(self, layout: QLayout | None = None) -> None:
        """Refresh breadcrumb items."""
        if layout is None:
            layout = self.layout()

        # Clear existing items
        self._item_labels.clear()
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, item in enumerate(self._items):
            # Add item label
            label = QLabel(item["label"], self)
            self._set_font_on_widget(label, "body_sm")

            # Last item is current location (not clickable)
            is_last = i == len(self._items) - 1
            if is_last:
                label.setStyleSheet(f"color: {THEME_V2.text_header};")
            else:
                label.setStyleSheet(f"""
                    QLabel {{
                        color: {THEME_V2.text_secondary};
                        background: transparent;
                    }}
                    QLabel:hover {{
                        color: {THEME_V2.primary};
                    }}
                """)
                label.setCursor(Qt.CursorShape.PointingHandCursor)

            layout.addWidget(label)
            self._item_labels.append(label)

            # Add separator (except after last item)
            if not is_last:
                sep_label = QLabel(self._separator, self)
                sep_label.setStyleSheet(f"color: {THEME_V2.text_muted};")
                self._set_font_on_widget(sep_label, "body_sm")
                layout.addWidget(sep_label)

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        for i, label in enumerate(self._item_labels):
            is_last = i == len(self._items) - 1
            if not is_last:
                # Store index for click handler
                label.mousePressEvent = lambda e, idx=i: self._on_item_click(idx)  # type: ignore[method-assign]

    def _set_font_on_widget(self, widget: QWidget, variant: str) -> None:
        """Set font on a widget using TOKENS_V2.typography."""
        from PySide6.QtGui import QFont

        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(getattr(TOKENS_V2.typography, variant))
        widget.setFont(font)

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        return """
            Breadcrumb {
                background: transparent;
            }
        """

    def _on_item_click(self, index: int) -> None:
        """Handle item click."""
        if 0 <= index < len(self._items):
            item = self._items[index]
            data = item.get("data") or item.get("value", "")
            self.item_clicked.emit(str(data))

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_items(self, items: list[BreadcrumbItem]) -> None:
        """
        Set the breadcrumb items.

        Args:
            items: List of breadcrumb items (dict with label and data/value)
        """
        self._items = items
        self._refresh_items()

    def get_items(self) -> list[BreadcrumbItem]:
        """Get the breadcrumb items."""
        return self._items.copy()

    def set_separator(self, separator: str) -> None:
        """
        Set the separator text.

        Args:
            separator: New separator text
        """
        self._separator = separator
        self._refresh_items()

    def get_separator(self) -> str:
        """Get the separator text."""
        return self._separator


# =============================================================================
# AVATAR
# =============================================================================


class Avatar(BasePrimitive):
    """
    User/profile placeholder with initials or image.

    Displays a circle or square containing:
    - User initials (if text provided)
    - Image (if image_path or QPixmap provided)
    - Default colored background with initials if no image

    Props:
        text: Initials to display (1-2 characters)
        image_path: Path to image file
        image: QPixmap for direct image use
        size: Avatar size (sm/md/lg)
        variant: Shape variant (circle/square)
        enabled: Initial enabled state

    Signals:
        clicked: Emitted when avatar is clicked

    Example:
        # Initials avatar
        avatar = Avatar(text="JD", size="md", variant="circle")

        # Image avatar
        avatar = Avatar(image_path="/path/to/photo.png", size="lg")

        # With click handler
        avatar = Avatar(text="AB", size="md")
        avatar.clicked.connect(lambda: show_profile_dialog())
    """

    clicked = Signal()

    _SIZE_MAP: dict[AvatarSize, int] = {
        "sm": 24,
        "md": 32,
        "lg": 40,
    }

    def __init__(
        self,
        parent: QWidget | None = None,
        text: str = "",
        image_path: str | Path | None = None,
        image: QPixmap | None = None,
        size: AvatarSize = "md",
        variant: AvatarVariant = "circle",
        enabled: bool = True,
    ) -> None:
        """
        Initialize the avatar.

        Args:
            parent: Optional parent widget
            text: Initials to display (1-2 characters)
            image_path: Path to image file
            image: QPixmap for direct image use
            size: Avatar size (sm/md/lg)
            variant: Shape variant (circle/square)
            enabled: Initial enabled state
        """
        self._text: str = text[:2] if text else ""  # Max 2 chars
        self._image_path: str | None = str(image_path) if image_path else None
        self._image: QPixmap | None = image
        self._size: AvatarSize = size
        self._variant: AvatarVariant = variant
        self._has_image: bool = (self._image_path is not None) or (self._image is not None)

        super().__init__(parent)

        self.setEnabled(enabled)

    def setup_ui(self) -> None:
        """Create and layout child widgets."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Set size immediately
        size_value = self._SIZE_MAP[self._size]
        self.setFixedSize(size_value, size_value)

        # Set cursor to clickable
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def connect_signals(self) -> None:
        """No signals to connect - click handled in mousePressEvent."""

    def _get_v2_stylesheet(self) -> str:
        """Get custom stylesheet for this widget."""
        radius = "50%" if self._variant == "circle" else f"{TOKENS_V2.radius.md}px"
        return f"""
            Avatar {{
                background: {THEME_V2.primary if not self._has_image else THEME_V2.bg_component};
                border: none;
                border-radius: {radius};
            }}
        """

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paint the avatar.

        Draws either the image or initials text.
        """
        from PySide6.QtGui import QPainter

        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2

        if self._has_image:
            self._paint_image(painter, rect)
        else:
            self._paint_initials(painter, center_x, center_y)

        painter.end()

    def _paint_image(self, painter: QPainter, rect) -> None:
        """Paint the image clipped to shape."""
        from PySide6.QtGui import QPainterPath

        # Create path for clipping
        path = QPainterPath()
        if self._variant == "circle":
            path.addEllipse(rect)
        else:
            radius = TOKENS_V2.radius.md
            path.addRoundedRect(rect, radius, radius)

        painter.setClipPath(path)

        # Load image
        pixmap: QPixmap | None = None
        if self._image:
            pixmap = self._image
        elif self._image_path:
            pixmap = QPixmap(self._image_path)

        if pixmap and not pixmap.isNull():
            # Scale to fit
            scaled = pixmap.scaled(
                rect.width(),
                rect.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            # Center the image
            x = (rect.width() - scaled.width()) // 2
            y = (rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)

    def _paint_initials(self, painter: QPainter, center_x: int, center_y: int) -> None:
        """Paint the initials text."""
        from PySide6.QtGui import QFont, QTextOption

        # Set font
        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(TOKENS_V2.typography.body_lg)
        font.setBold(True)
        painter.setFont(font)

        # Set text color
        painter.setPen(THEME_V2.text_on_primary)

        # Draw text centered
        text_option = QTextOption()
        text_option.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_rect = self.rect()
        painter.drawText(text_rect, self._text, text_option)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press event."""
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()

    def _on_avatar_click(self) -> None:
        """Helper for testing - emit clicked signal."""
        self.clicked.emit()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def set_text(self, text: str) -> None:
        """
        Set the initials text.

        Args:
            text: New initials (max 2 characters)
        """
        self._text = text[:2] if text else ""
        self._has_image = False
        self.update()

    def text(self) -> str:
        """Get the initials text."""
        return self._text

    def set_image(self, image_path: str | Path | QPixmap | None) -> None:
        """
        Set the avatar image.

        Args:
            image_path: Path to image file or QPixmap
        """
        if isinstance(image_path, QPixmap):
            self._image = image_path
            self._image_path = None
        else:
            self._image_path = str(image_path) if image_path else None
            self._image = None

        self._has_image = (self._image_path is not None) or (self._image is not None)
        self._apply_v2_theme()
        self.update()

    def set_size(self, size: AvatarSize) -> None:
        """
        Set the avatar size.

        Args:
            size: New size (sm/md/lg)
        """
        self._size = size
        self.setFixedSize(self._SIZE_MAP[size], self._SIZE_MAP[size])
        self.update()

    def get_size(self) -> AvatarSize:
        """Get the avatar size."""
        return self._size

    def set_variant(self, variant: AvatarVariant) -> None:
        """
        Set the avatar shape variant.

        Args:
            variant: Shape variant (circle/square)
        """
        self._variant = variant
        self._apply_v2_theme()
        self.update()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_badge(
    text: str = "",
    variant: BadgeVariant = "dot",
    color: BadgeColor | None = None,
    parent: QWidget | None = None,
) -> Badge:
    """
    Convenience function to create a badge.

    Args:
        text: Display text (for count/label variants)
        variant: Badge type (dot/count/label)
        color: Color name (primary/success/warning/error/info)
        parent: Optional parent widget

    Returns:
        Configured Badge widget
    """
    return Badge(text=text, variant=variant, color=color, parent=parent)


def create_alert(
    text: str = "",
    variant: AlertVariant = "info",
    dismissible: bool = False,
    parent: QWidget | None = None,
) -> InlineAlert:
    """
    Convenience function to create an inline alert.

    Args:
        text: Alert message text
        variant: Alert type (info/warning/error/success)
        dismissible: Whether to show dismiss button
        parent: Optional parent widget

    Returns:
        Configured InlineAlert widget
    """
    return InlineAlert(text=text, variant=variant, dismissible=dismissible, parent=parent)


def create_breadcrumb(
    items: list[BreadcrumbItem] | None = None,
    separator: str = "/",
    parent: QWidget | None = None,
) -> Breadcrumb:
    """
    Convenience function to create a breadcrumb.

    Args:
        items: List of breadcrumb items (dict with label and data/value)
        separator: Separator text between items
        parent: Optional parent widget

    Returns:
        Configured Breadcrumb widget
    """
    return Breadcrumb(items=items, separator=separator, parent=parent)


def create_avatar(
    text: str = "",
    image_path: str | Path | None = None,
    size: AvatarSize = "md",
    variant: AvatarVariant = "circle",
    parent: QWidget | None = None,
) -> Avatar:
    """
    Convenience function to create an avatar.

    Args:
        text: Initials to display
        image_path: Path to image file
        size: Avatar size (sm/md/lg)
        variant: Shape variant (circle/square)
        parent: Optional parent widget

    Returns:
        Configured Avatar widget
    """
    return Avatar(text=text, image_path=image_path, size=size, variant=variant, parent=parent)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Components
    "Badge",
    "InlineAlert",
    "Breadcrumb",
    "Avatar",
    # Types
    "BadgeVariant",
    "BadgeColor",
    "AlertVariant",
    "AvatarSize",
    "AvatarVariant",
    "BreadcrumbItem",
    # Helpers
    "set_tooltip",
    # Convenience functions
    "create_badge",
    "create_alert",
    "create_breadcrumb",
    "create_avatar",
]
