"""
Tests for Button Components v2 - Epic 5.1 Component Library.

Tests PushButton, ToolButton, and ButtonGroup components.
"""

import pytest
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    ButtonGroup,
    ButtonSize,
    ButtonVariant,
    PushButton,
    ToolButton,
    create_button,
    create_icon_button,
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
# PUSH BUTTON TESTS
# =============================================================================


class TestPushButton:
    """Tests for PushButton component."""

    def test_initialization(self, parent_widget):
        """Test button can be initialized."""
        btn = PushButton(text="Test", parent=parent_widget)
        assert btn.text() == "Test"
        assert btn.isEnabled()

    def test_variants(self, parent_widget):
        """Test all button variants can be created."""
        variants: list[ButtonVariant] = ["primary", "secondary", "ghost", "danger"]

        for variant in variants:
            btn = PushButton(text=variant.capitalize(), variant=variant, parent=parent_widget)
            assert btn.get_variant() == variant
            assert btn.isEnabled()

    def test_sizes(self, parent_widget):
        """Test all button sizes can be created."""
        expected_heights = {
            "sm": TOKENS_V2.sizes.button_sm,
            "md": TOKENS_V2.sizes.button_md,
            "lg": TOKENS_V2.sizes.button_lg,
        }

        for size, expected_height in expected_heights.items():
            btn = PushButton(text=f"Size {size}", size=size, parent=parent_widget)
            assert btn.get_size() == size
            assert btn.height() == expected_height

    def test_variant_change(self, parent_widget):
        """Test variant can be changed."""
        btn = PushButton(text="Test", variant="primary", parent=parent_widget)

        btn.set_variant("secondary")
        assert btn.get_variant() == "secondary"

        btn.set_variant("danger")
        assert btn.get_variant() == "danger"

    def test_size_change(self, parent_widget):
        """Test size can be changed."""
        btn = PushButton(text="Test", size="md", parent=parent_widget)

        btn.set_size("lg")
        assert btn.get_size() == "lg"
        assert btn.height() == TOKENS_V2.sizes.button_lg

        btn.set_size("sm")
        assert btn.get_size() == "sm"
        assert btn.height() == TOKENS_V2.sizes.button_sm

    def test_with_icon(self, parent_widget):
        """Test button with icon."""
        icon = get_icon("check", size=20)
        btn = PushButton(
            text="With Icon",
            icon=icon,
            variant="primary",
            parent=parent_widget,
        )

        assert not btn.icon().isNull()
        assert btn.iconSize().width() == 20
        assert btn.iconSize().height() == 20

    def test_disabled_state(self, parent_widget):
        """Test button can be disabled."""
        btn = PushButton(text="Test", enabled=False, parent=parent_widget)
        assert not btn.isEnabled()

    def test_clicked_signal(self, parent_widget):
        """Test clicked signal emission."""
        from PySide6.QtWidgets import QApplication

        btn = PushButton(text="Click Me", parent=parent_widget)
        received = []

        btn.clicked.connect(lambda: received.append(True))
        btn.click()
        QApplication.instance().processEvents()

        assert len(received) == 1

    def test_minimum_width(self, parent_widget):
        """Test button has minimum width for touch targets."""
        btn = PushButton(text="OK", parent=parent_widget)
        assert btn.minimumWidth() == TOKENS_V2.sizes.button_min_width


# =============================================================================
# TOOL BUTTON TESTS
# =============================================================================


class TestToolButton:
    """Tests for ToolButton component."""

    def test_initialization(self, parent_widget):
        """Test tool button can be initialized."""
        icon = get_icon("settings", size=20)
        btn = ToolButton(icon=icon, parent=parent_widget)

        assert not btn.icon().isNull()
        assert btn.iconSize().width() == 20
        assert btn.isEnabled()

    def test_with_tooltip(self, parent_widget):
        """Test tool button with tooltip."""
        icon = get_icon("eye", size=20)
        btn = ToolButton(icon=icon, tooltip="Toggle visibility", parent=parent_widget)

        assert btn.toolTip() == "Toggle visibility"

    def test_checkable_state(self, parent_widget):
        """Test tool button can be checkable."""
        icon = get_icon("check", size=20)
        btn = ToolButton(icon=icon, checked=True, parent=parent_widget)

        assert btn.isCheckable()
        assert btn.is_checked_state()

    def test_checked_toggle(self, parent_widget):
        """Test checked state can be toggled."""
        from PySide6.QtWidgets import QApplication

        icon = get_icon("check", size=20)
        btn = ToolButton(icon=icon, checked=True, parent=parent_widget)

        assert btn.is_checked_state()

        btn.set_checked_state(False)
        QApplication.instance().processEvents()
        assert not btn.is_checked_state()

        btn.set_checked_state(True)
        QApplication.instance().processEvents()
        assert btn.is_checked_state()

    def test_with_checked_icon(self, parent_widget):
        """Test tool button with different checked icon."""
        icon = get_icon("eye", size=20)
        checked_icon = get_icon("eye-off", size=20)

        btn = ToolButton(
            icon=icon,
            checked_icon=checked_icon,
            checked=True,
            parent=parent_widget,
        )

        assert btn._checked_icon is not None
        assert btn._normal_icon is not None

    def test_icon_only_variant(self, parent_widget):
        """Test icon-only variant (default)."""
        icon = get_icon("play", size=20)
        btn = ToolButton(icon=icon, variant="icon-only", parent=parent_widget)

        assert btn.text() == ""
        # Icon-only buttons are square
        assert btn.width() <= btn.height() + 5  # Small tolerance

    def test_icon_text_variant(self, parent_widget):
        """Test icon-text variant with text label."""
        icon = get_icon("edit", size=20)
        btn = ToolButton(
            icon=icon,
            text="Edit",
            variant="icon-text",
            parent=parent_widget,
        )

        assert btn.text() == "Edit"
        # Icon-text buttons are wider
        assert btn.minimumWidth() > btn.height()

    def test_icon_sizes(self, parent_widget):
        """Test different icon sizes."""
        icon_sizes = [16, 20, 24]

        for size in icon_sizes:
            icon = get_icon("check", size=size)
            btn = ToolButton(icon=icon, icon_size=size, parent=parent_widget)
            assert btn.iconSize().width() == size
            assert btn.iconSize().height() == size

    def test_clicked_signal(self, parent_widget):
        """Test clicked signal emission."""
        from PySide6.QtWidgets import QApplication

        icon = get_icon("play", size=20)
        btn = ToolButton(icon=icon, parent=parent_widget)
        received = []

        btn.clicked.connect(lambda: received.append(True))
        btn.click()
        QApplication.instance().processEvents()

        assert len(received) == 1

    def test_toggled_signal(self, parent_widget):
        """Test toggled signal emission."""
        from PySide6.QtWidgets import QApplication

        icon = get_icon("check", size=20)
        btn = ToolButton(icon=icon, checked=True, parent=parent_widget)
        received = []

        btn.toggled.connect(lambda checked: received.append(checked))

        btn.set_checked_state(False)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] is False


# =============================================================================
# BUTTON GROUP TESTS
# =============================================================================


class TestButtonGroup:
    """Tests for ButtonGroup component."""

    def test_initialization_empty(self, parent_widget):
        """Test empty button group can be created."""
        group = ButtonGroup(parent=parent_widget)
        assert group.get_button_count() == 0
        assert group.get_selected_id() is None

    def test_initialization_with_buttons(self, parent_widget):
        """Test button group with initial buttons."""
        buttons = [("Option 1", "opt1"), ("Option 2", "opt2"), ("Option 3", "opt3")]
        group = ButtonGroup(buttons=buttons, parent=parent_widget)

        assert group.get_button_count() == 3
        assert group.get_button_ids() == ["opt1", "opt2", "opt3"]

    def test_add_button(self, parent_widget):
        """Test adding buttons to group."""
        group = ButtonGroup(parent=parent_widget)

        group.add_button("First", "btn1")
        assert group.get_button_count() == 1
        assert group.get_button_ids() == ["btn1"]

        group.add_button("Second", "btn2")
        assert group.get_button_count() == 2
        assert group.get_button_ids() == ["btn1", "btn2"]

    def test_exclusive_behavior(self, parent_widget):
        """Test exclusive group only allows one selection."""
        from PySide6.QtWidgets import QApplication

        buttons = [("One", "1"), ("Two", "2"), ("Three", "3")]
        group = ButtonGroup(buttons=buttons, exclusive=True, parent=parent_widget)

        # Select first button
        group.set_selected_id("1")
        QApplication.instance().processEvents()
        assert group.get_selected_id() == "1"

        # Select different button
        group.set_selected_id("2")
        QApplication.instance().processEvents()
        assert group.get_selected_id() == "2"
        # Only one should be selected
        selected_count = sum(1 for btn in group._buttons if btn.isChecked())
        assert selected_count == 1

    def test_non_exclusive_behavior(self, parent_widget):
        """Test non-exclusive group allows multiple selections."""
        from PySide6.QtWidgets import QApplication

        buttons = [("One", "1"), ("Two", "2")]
        group = ButtonGroup(buttons=buttons, exclusive=False, parent=parent_widget)

        # Make buttons checkable manually
        for btn in group._buttons:
            btn.setCheckable(True)

        group._buttons[0].setChecked(True)
        group._buttons[1].setChecked(True)
        QApplication.instance().processEvents()

        # Both can be checked
        assert group._buttons[0].isChecked()
        assert group._buttons[1].isChecked()

    def test_get_selected_index(self, parent_widget):
        """Test getting selected index."""
        from PySide6.QtWidgets import QApplication

        buttons = [("A", "a"), ("B", "b"), ("C", "c")]
        group = ButtonGroup(buttons=buttons, parent=parent_widget)

        group.set_selected_id("b")
        QApplication.instance().processEvents()

        assert group.get_selected_index() == 1

    def test_set_selected_index(self, parent_widget):
        """Test setting selection by index."""
        from PySide6.QtWidgets import QApplication

        buttons = [("A", "a"), ("B", "b"), ("C", "c")]
        group = ButtonGroup(buttons=buttons, parent=parent_widget)

        group.set_selected_index(2)
        QApplication.instance().processEvents()

        assert group.get_selected_id() == "c"

    def test_clear_selection(self, parent_widget):
        """Test clearing selection works with non-exclusive groups."""
        from PySide6.QtWidgets import QApplication

        # Non-exclusive group allows clearing selection
        buttons = [("A", "a"), ("B", "b")]
        group = ButtonGroup(buttons=buttons, exclusive=False, parent=parent_widget)

        # Make buttons checkable manually for non-exclusive mode
        for btn in group._buttons:
            btn.setCheckable(True)

        group._buttons[0].setChecked(True)
        QApplication.instance().processEvents()
        assert group._buttons[0].isChecked()

        group.clear_selection()
        QApplication.instance().processEvents()
        # For exclusive groups, Qt doesn't allow clearing selection
        # For non-exclusive, we can manually uncheck
        assert not group._buttons[0].isChecked()
        assert not group._buttons[1].isChecked()

    def test_button_clicked_signal(self, parent_widget):
        """Test button_clicked signal."""
        from PySide6.QtWidgets import QApplication

        buttons = [("Click Me", "btn")]
        group = ButtonGroup(buttons=buttons, parent=parent_widget)

        received = []
        group.button_clicked.connect(lambda idx, btn_id: received.append((idx, btn_id)))

        group._buttons[0].click()
        QApplication.instance().processEvents()

        assert len(received) == 1
        assert received[0] == (0, "btn")

    def test_button_toggled_signal(self, parent_widget):
        """Test button_toggled signal."""
        from PySide6.QtWidgets import QApplication

        buttons = [("Toggle", "tog")]
        group = ButtonGroup(buttons=buttons, exclusive=True, parent=parent_widget)

        received = []
        group.button_toggled.connect(
            lambda idx, btn_id, checked: received.append((idx, btn_id, checked))
        )

        group._buttons[0].click()
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1][0] == 0
        assert received[-1][1] == "tog"

    def test_horizontal_orientation(self, parent_widget):
        """Test horizontal orientation."""
        group = ButtonGroup(
            buttons=[("A", "a"), ("B", "b")],
            orientation="horizontal",
            parent=parent_widget,
        )
        assert group._orientation == "horizontal"
        assert isinstance(group.layout(), type(QHBoxLayout()))

    def test_vertical_orientation(self, parent_widget):
        """Test vertical orientation."""
        group = ButtonGroup(
            buttons=[("A", "a"), ("B", "b")],
            orientation="vertical",
            parent=parent_widget,
        )
        assert group._orientation == "vertical"
        assert isinstance(group.layout(), type(QVBoxLayout()))

    def test_size_propagation(self, parent_widget):
        """Test size is applied to group buttons."""
        sizes: dict[ButtonSize, int] = {
            "sm": TOKENS_V2.sizes.button_sm,
            "md": TOKENS_V2.sizes.button_md,
            "lg": TOKENS_V2.sizes.button_lg,
        }

        for size, expected_height in sizes.items():
            group = ButtonGroup(
                buttons=[("Test", "t")],
                size=size,
                parent=parent_widget,
            )
            assert group._buttons[0].height() == expected_height

    def test_variant_propagation(self, parent_widget):
        """Test variant is applied to group buttons."""
        variants: list[ButtonVariant] = ["primary", "secondary", "ghost", "danger"]

        for variant in variants:
            group = ButtonGroup(
                buttons=[("Test", "t")],
                variant=variant,
                parent=parent_widget,
            )
            assert group._variant == variant


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_create_button(self, parent_widget):
        """Test create_button convenience function."""
        btn = create_button("Save", variant="primary", size="md", parent=parent_widget)

        assert isinstance(btn, PushButton)
        assert btn.text() == "Save"
        assert btn.get_variant() == "primary"
        assert btn.get_size() == "md"

    def test_create_icon_button(self, parent_widget):
        """Test create_icon_button convenience function."""
        btn = create_icon_button("settings", tooltip="Settings", parent=parent_widget)

        assert isinstance(btn, ToolButton)
        assert not btn.icon().isNull()
        assert btn.toolTip() == "Settings"

    def test_create_icon_button_checkable(self, parent_widget):
        """Test create_icon_button with checkable option."""
        btn = create_icon_button("check", checkable=True, parent=parent_widget)

        assert isinstance(btn, ToolButton)
        assert btn.isCheckable()

    def test_create_icon_button_custom_size(self, parent_widget):
        """Test create_icon_button with custom icon size."""
        btn = create_icon_button("play", icon_size=24, parent=parent_widget)

        assert isinstance(btn, ToolButton)
        assert btn.iconSize().width() == 24
