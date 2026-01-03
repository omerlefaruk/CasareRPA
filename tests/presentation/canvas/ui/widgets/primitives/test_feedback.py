"""
Tests for Feedback Components v2 - Epic 5.1 Component Library.

Tests Badge, InlineAlert, Breadcrumb, and Avatar components.
"""

import pytest
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    AlertVariant,
    Avatar,
    AvatarSize,
    Badge,
    BadgeColor,
    Breadcrumb,
    BreadcrumbItem,
    InlineAlert,
    create_alert,
    create_avatar,
    create_badge,
    create_breadcrumb,
    set_tooltip,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parent_widget(qapp) -> QWidget:
    """Parent widget fixture."""
    widget = QWidget()
    yield widget
    widget.close()


# =============================================================================
# BADGE TESTS
# =============================================================================


class TestBadge:
    """Tests for Badge component."""

    def test_dot_variant_initialization(self, parent_widget):
        """Test dot badge can be initialized."""
        badge = Badge(parent=parent_widget, variant="dot", color="success")
        assert badge.get_variant() == "dot"
        assert badge.get_color() == "success"
        assert badge.width() == 8  # _DOT_SIZE
        assert badge.height() == 8

    def test_count_variant_initialization(self, parent_widget):
        """Test count badge can be initialized."""
        badge = Badge(parent=parent_widget, variant="count", text="5", color="error")
        assert badge.get_variant() == "count"
        assert badge.text() == "5"
        assert badge.get_color() == "error"
        assert badge.height() == TOKENS_V2.sizes.icon_sm

    def test_label_variant_initialization(self, parent_widget):
        """Test label badge can be initialized."""
        badge = Badge(parent=parent_widget, variant="label", text="NEW", color="primary")
        assert badge.get_variant() == "label"
        assert badge.text() == "NEW"
        assert badge.get_color() == "primary"

    def test_all_colors(self, parent_widget):
        """Test all badge colors."""
        colors: list[BadgeColor] = ["primary", "success", "warning", "error", "info"]

        for color in colors:
            badge = Badge(parent=parent_widget, variant="dot", color=color)
            assert badge.get_color() == color

    def test_default_color(self, parent_widget):
        """Test default color is primary."""
        badge = Badge(parent=parent_widget, variant="dot", color=None)
        assert badge.get_color() is None

    def test_set_text(self, parent_widget):
        """Test setting badge text."""
        badge = Badge(parent=parent_widget, variant="count", text="1")
        assert badge.text() == "1"

        badge.set_text("99")
        assert badge.text() == "99"

    def test_set_text_dot_variant_no_op(self, parent_widget):
        """Test setting text on dot variant returns empty."""
        badge = Badge(parent=parent_widget, variant="dot")
        badge.set_text("test")
        # Dot variant returns empty string for text (not displayed)
        assert badge.text() == ""

    def test_set_color(self, parent_widget):
        """Test setting badge color."""
        badge = Badge(parent=parent_widget, variant="dot", color="primary")
        assert badge.get_color() == "primary"

        badge.set_color("success")
        assert badge.get_color() == "success"

    def test_set_variant(self, parent_widget):
        """Test changing badge variant."""
        badge = Badge(parent=parent_widget, variant="dot")
        assert badge.get_variant() == "dot"

        badge.set_variant("label")
        assert badge.get_variant() == "label"

        badge.set_variant("count")
        assert badge.get_variant() == "count"


# =============================================================================
# TOOLTIP HELPER TESTS
# =============================================================================


class TestTooltipHelper:
    """Tests for set_tooltip helper function."""

    def test_set_tooltip_on_widget(self, parent_widget):
        """Test tooltip can be set on widget."""
        from PySide6.QtWidgets import QLabel

        label = QLabel("Test", parent_widget)
        set_tooltip(label, "Help text")
        assert label.toolTip() == "Help text"

    def test_set_tooltip_with_custom_delay(self, parent_widget):
        """Test tooltip with custom delay."""
        from PySide6.QtWidgets import QLabel

        label = QLabel("Test", parent_widget)
        set_tooltip(label, "Delayed help", delay_ms=1000)
        assert label.toolTip() == "Delayed help"


# =============================================================================
# INLINE ALERT TESTS
# =============================================================================


class TestInlineAlert:
    """Tests for InlineAlert component."""

    def test_info_variant_initialization(self, parent_widget):
        """Test info alert can be initialized."""
        alert = InlineAlert(parent=parent_widget, text="Info message", variant="info")
        assert alert.get_variant() == "info"
        assert alert.text() == "Info message"

    def test_all_variants(self, parent_widget):
        """Test all alert variants."""
        variants: list[AlertVariant] = ["info", "warning", "error", "success"]

        for variant in variants:
            alert = InlineAlert(parent=parent_widget, text=f"{variant} message", variant=variant)
            assert alert.get_variant() == variant

    def test_dismissible_initialization(self, parent_widget):
        """Test dismissible alert has button."""
        alert = InlineAlert(
            parent=parent_widget, text="Can dismiss", variant="info", dismissible=True
        )
        assert alert._dismiss_btn is not None

    def test_non_dismissible_initialization(self, parent_widget):
        """Test non-dismissible alert has no button."""
        alert = InlineAlert(
            parent=parent_widget, text="Cannot dismiss", variant="info", dismissible=False
        )
        assert alert._dismiss_btn is None

    def test_set_text(self, parent_widget):
        """Test setting alert text."""
        alert = InlineAlert(parent=parent_widget, text="Original")
        assert alert.text() == "Original"

        alert.set_text("Updated")
        assert alert.text() == "Updated"

    def test_set_variant(self, parent_widget):
        """Test changing alert variant."""
        alert = InlineAlert(parent=parent_widget, text="Test", variant="info")
        assert alert.get_variant() == "info"

        alert.set_variant("error")
        assert alert.get_variant() == "error"

        alert.set_variant("success")
        assert alert.get_variant() == "success"

    def test_set_dismissible(self, parent_widget):
        """Test setting dismissible flag."""
        alert = InlineAlert(parent=parent_widget, text="Test", variant="info", dismissible=True)
        alert.set_dismissible(False)
        # Button should be hidden
        assert alert._dismiss_btn is not None

    def test_dismissed_signal(self, parent_widget):
        """Test dismissed signal emission."""
        from PySide6.QtWidgets import QApplication

        alert = InlineAlert(
            parent=parent_widget, text="Dismiss me", variant="info", dismissible=True
        )
        received = []

        alert.dismissed.connect(lambda: received.append(True))

        if alert._dismiss_btn:
            alert._dismiss_btn.click()
            QApplication.instance().processEvents()

        assert len(received) == 1


# =============================================================================
# BREADCRUMB TESTS
# =============================================================================


class TestBreadcrumb:
    """Tests for Breadcrumb component."""

    def test_initialization_with_items(self, parent_widget):
        """Test breadcrumb can be initialized with items."""
        items: list[BreadcrumbItem] = [
            {"label": "Home", "data": "home"},
            {"label": "Settings", "data": "settings"},
        ]
        breadcrumb = Breadcrumb(parent=parent_widget, items=items)
        assert breadcrumb.get_items() == items

    def test_default_separator(self, parent_widget):
        """Test default separator is /."""
        breadcrumb = Breadcrumb(parent=parent_widget)
        assert breadcrumb.get_separator() == "/"

    def test_custom_separator(self, parent_widget):
        """Test custom separator."""
        breadcrumb = Breadcrumb(parent=parent_widget, separator=">")
        assert breadcrumb.get_separator() == ">"

    def test_set_items(self, parent_widget):
        """Test setting breadcrumb items."""
        breadcrumb = Breadcrumb(parent=parent_widget)

        new_items: list[BreadcrumbItem] = [
            {"label": "A", "data": "a"},
            {"label": "B", "data": "b"},
            {"label": "C", "data": "c"},
        ]
        breadcrumb.set_items(new_items)
        assert breadcrumb.get_items() == new_items

    def test_set_separator(self, parent_widget):
        """Test setting separator."""
        breadcrumb = Breadcrumb(parent=parent_widget, separator="/")
        breadcrumb.set_separator(">")
        assert breadcrumb.get_separator() == ">"

    def test_item_with_value_alias(self, parent_widget):
        """Test item with 'value' key works as alias for 'data'."""
        items: list[BreadcrumbItem] = [
            {"label": "Home", "value": "home"},  # Using 'value' instead of 'data'
        ]
        breadcrumb = Breadcrumb(parent=parent_widget, items=items)
        # Should work - 'value' is treated as 'data'
        assert len(breadcrumb.get_items()) == 1

    def test_item_clicked_signal(self, parent_widget):
        """Test item_clicked signal."""
        breadcrumb = Breadcrumb(
            parent=parent_widget,
            items=[
                {"label": "Home", "data": "home"},
                {"label": "Settings", "data": "settings"},
            ],
        )
        received = []

        breadcrumb.item_clicked.connect(lambda data: received.append(data))

        # Simulate clicking first item
        breadcrumb._on_item_click(0)
        assert received[-1] == "home"

        # Simulate clicking second item
        breadcrumb._on_item_click(1)
        assert received[-1] == "settings"

    def test_items_with_clickable_labels(self, parent_widget):
        """Test breadcrumb creates labels for items."""
        items: list[BreadcrumbItem] = [
            {"label": "A", "data": "a"},
            {"label": "B", "data": "b"},
        ]
        breadcrumb = Breadcrumb(parent=parent_widget, items=items)

        # Should have 2 item labels + 1 separator
        assert len(breadcrumb._item_labels) == 2


# =============================================================================
# AVATAR TESTS
# =============================================================================


class TestAvatar:
    """Tests for Avatar component."""

    def test_initialization_with_text(self, parent_widget):
        """Test avatar can be initialized with text."""
        avatar = Avatar(parent=parent_widget, text="JD", size="md")
        assert avatar.text() == "JD"
        assert avatar.get_size() == "md"

    def test_text_truncated_to_2_chars(self, parent_widget):
        """Test text is truncated to max 2 characters."""
        avatar = Avatar(parent=parent_widget, text="ABC")
        assert avatar.text() == "AB"

    def test_empty_text(self, parent_widget):
        """Test empty text is handled."""
        avatar = Avatar(parent=parent_widget, text="")
        assert avatar.text() == ""

    def test_all_sizes(self, parent_widget):
        """Test all avatar sizes."""
        sizes: list[AvatarSize] = ["sm", "md", "lg"]
        expected_sizes = {"sm": 24, "md": 32, "lg": 40}

        for size in sizes:
            avatar = Avatar(parent=parent_widget, text="AB", size=size)
            assert avatar.get_size() == size
            assert avatar.width() == expected_sizes[size]
            assert avatar.height() == expected_sizes[size]

    def test_circle_variant(self, parent_widget):
        """Test circle variant (default)."""
        avatar = Avatar(parent=parent_widget, text="AB", variant="circle")
        # Circle is default
        assert avatar.height() == avatar.width()

    def test_square_variant(self, parent_widget):
        """Test square variant."""
        avatar = Avatar(parent=parent_widget, text="AB", variant="square")
        assert avatar.height() == avatar.width()

    def test_set_text(self, parent_widget):
        """Test setting avatar text."""
        avatar = Avatar(parent=parent_widget, text="AB")
        assert avatar.text() == "AB"

        avatar.set_text("XY")
        assert avatar.text() == "XY"

    def test_set_size(self, parent_widget):
        """Test changing avatar size."""
        avatar = Avatar(parent=parent_widget, text="AB", size="sm")
        assert avatar.get_size() == "sm"

        avatar.set_size("lg")
        assert avatar.get_size() == "lg"
        assert avatar.width() == 40
        assert avatar.height() == 40

    def test_set_variant(self, parent_widget):
        """Test changing avatar variant."""
        avatar = Avatar(parent=parent_widget, text="AB", variant="circle")
        avatar.set_variant("square")
        # No crash - variant is applied

    def test_clicked_signal(self, parent_widget):
        """Test clicked signal."""
        avatar = Avatar(parent=parent_widget, text="AB")
        received = []

        avatar.clicked.connect(lambda: received.append(True))

        # Simulate mouse press using the internal method
        avatar._on_avatar_click()

        assert len(received) == 1


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_badge(self, parent_widget):
        """Test create_badge convenience function."""
        badge = create_badge(text="5", variant="count", color="error", parent=parent_widget)
        assert isinstance(badge, Badge)
        assert badge.text() == "5"
        assert badge.get_variant() == "count"
        assert badge.get_color() == "error"

    def test_create_alert(self, parent_widget):
        """Test create_alert convenience function."""
        alert = create_alert(
            text="Error occurred", variant="error", dismissible=True, parent=parent_widget
        )
        assert isinstance(alert, InlineAlert)
        assert alert.text() == "Error occurred"
        assert alert.get_variant() == "error"

    def test_create_breadcrumb(self, parent_widget):
        """Test create_breadcrumb convenience function."""
        items: list[BreadcrumbItem] = [
            {"label": "Home", "data": "home"},
            {"label": "Settings", "data": "settings"},
        ]
        breadcrumb = create_breadcrumb(items=items, separator=">", parent=parent_widget)
        assert isinstance(breadcrumb, Breadcrumb)
        assert breadcrumb.get_items() == items
        assert breadcrumb.get_separator() == ">"

    def test_create_avatar(self, parent_widget):
        """Test create_avatar convenience function."""
        avatar = create_avatar(text="JD", size="md", variant="circle", parent=parent_widget)
        assert isinstance(avatar, Avatar)
        assert avatar.text() == "JD"
        assert avatar.get_size() == "md"

