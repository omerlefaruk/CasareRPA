"""
Tests for Structural Components v2 - Epic 5.1 Component Library.

Tests SectionHeader, Divider, EmptyState, and Card components.
"""

import pytest

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    Card,
    Divider,
    EmptyState,
    Orientation,
    SectionHeader,
    create_card,
    create_divider,
    create_empty_state,
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


@pytest.fixture
def content_widget(parent_widget) -> QWidget:
    """Sample content widget for Card tests."""
    widget = QWidget(parent_widget)
    layout = QVBoxLayout(widget)
    label = QLabel("Content", widget)
    layout.addWidget(label)
    return widget


# =============================================================================
# SECTION HEADER TESTS
# =============================================================================


class TestSectionHeader:
    """Tests for SectionHeader component."""

    def test_initialization(self, parent_widget):
        """Test section header can be initialized."""
        header = SectionHeader(text="Section", parent=parent_widget)
        assert header.text() == "Section"
        assert header.isEnabled()

    def test_initial_collapsed_state(self, parent_widget):
        """Test section header initial collapsed state."""
        header = SectionHeader(
            text="Section",
            collapsed=True,
            parent=parent_widget
        )
        assert header.is_collapsed()

        header_expanded = SectionHeader(
            text="Section",
            collapsed=False,
            parent=parent_widget
        )
        assert not header_expanded.is_collapsed()

    def test_collapsible_false(self, parent_widget):
        """Test section header without collapse button."""
        header = SectionHeader(
            text="Section",
            collapsible=False,
            parent=parent_widget
        )
        assert not header.is_collapsed()
        # Should not have collapse button
        assert not hasattr(header, "_collapse_btn") or header._collapse_btn is None

    def test_collapsible_true(self, parent_widget):
        """Test section header with collapse button."""
        header = SectionHeader(
            text="Section",
            collapsible=True,
            parent=parent_widget
        )
        # Should have collapse button
        assert header._collapse_btn is not None

    def test_level_clamping(self, parent_widget):
        """Test level is clamped to valid range (1-3)."""
        header_low = SectionHeader(text="Section", level=0, parent=parent_widget)
        assert header_low._level == 1  # Clamped to minimum

        header_high = SectionHeader(text="Section", level=5, parent=parent_widget)
        assert header_high._level == 3  # Clamped to maximum

    def test_set_text(self, parent_widget):
        """Test set_text updates header text."""
        header = SectionHeader(text="Original", parent=parent_widget)
        header.set_text("Updated")
        assert header.text() == "Updated"

    def test_set_collapsed_emits_signal(self, parent_widget, qapp):
        """Test set_collapsed emits collapsed_changed signal."""
        header = SectionHeader(
            text="Section",
            collapsible=True,
            parent=parent_widget
        )

        signals = []
        header.collapsed_changed.connect(lambda c: signals.append(c))

        header.set_collapsed(True)
        assert signals == [True]

        header.set_collapsed(False)
        assert signals == [True, False]

    def test_set_collapsed_idempotent(self, parent_widget):
        """Test set_collapsed doesn't emit signal when value unchanged."""
        header = SectionHeader(
            text="Section",
            collapsible=True,
            collapsed=False,
            parent=parent_widget
        )

        signals = []
        header.collapsed_changed.connect(lambda c: signals.append(c))

        header.set_collapsed(False)  # Same state
        assert signals == []

    def test_toggle(self, parent_widget):
        """Test toggle switches collapsed state."""
        header = SectionHeader(
            text="Section",
            collapsible=True,
            collapsed=False,
            parent=parent_widget
        )

        header.toggle()
        assert header.is_collapsed()

        header.toggle()
        assert not header.is_collapsed()

    def test_initial_disabled_state(self, parent_widget):
        """Test section header can be created disabled."""
        header = SectionHeader(text="Section", enabled=False, parent=parent_widget)
        assert not header.isEnabled()

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        header = SectionHeader(text="Section", parent=parent_widget)
        stylesheet = header._get_v2_stylesheet()

        assert THEME_V2.border in stylesheet
        assert THEME_V2.bg_hover in stylesheet
        assert str(TOKENS_V2.radius.xs) in stylesheet


# =============================================================================
# DIVIDER TESTS
# =============================================================================


class TestDivider:
    """Tests for Divider component."""

    def test_initialization(self, parent_widget):
        """Test divider can be initialized."""
        divider = Divider(parent=parent_widget)
        assert divider._orientation == "horizontal"
        assert divider._margin == TOKENS_V2.margin.standard

    def test_horizontal_orientation(self, parent_widget):
        """Test horizontal divider orientation."""
        divider = Divider(
            orientation="horizontal",
            parent=parent_widget
        )
        assert divider._orientation == "horizontal"
        assert divider.frameShape() == QFrame.Shape.HLine  # type: ignore

    def test_vertical_orientation(self, parent_widget):
        """Test vertical divider orientation."""
        divider = Divider(
            orientation="vertical",
            parent=parent_widget
        )
        assert divider._orientation == "vertical"
        assert divider.frameShape() == QFrame.Shape.VLine  # type: ignore

    def test_margin_preset(self, parent_widget):
        """Test margin preset is resolved correctly."""
        divider = Divider(margin="tight", parent=parent_widget)
        assert divider._margin == TOKENS_V2.margin.tight

        divider_standard = Divider(margin="standard", parent=parent_widget)
        assert divider_standard._margin == TOKENS_V2.margin.standard

    def test_margin_tuple(self, parent_widget):
        """Test margin can be provided as tuple."""
        custom_margin = (2, 4, 6, 8)
        divider = Divider(margin=custom_margin, parent=parent_widget)
        assert divider._margin == custom_margin

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        divider = Divider(parent=parent_widget)
        stylesheet = divider.stylesheet()
        assert THEME_V2.border in stylesheet


# =============================================================================
# EMPTY STATE TESTS
# =============================================================================


class TestEmptyState:
    """Tests for EmptyState component."""

    def test_initialization(self, parent_widget):
        """Test empty state can be initialized."""
        empty = EmptyState(text="No items", parent=parent_widget)
        assert empty.text() == "No items"
        assert empty.isEnabled()

    def test_with_icon_name(self, parent_widget):
        """Test empty state with icon name."""
        empty = EmptyState(
            icon="inbox",
            text="Empty",
            parent=parent_widget
        )
        assert empty._icon_name == "inbox"
        assert empty._icon_label is not None

    def test_with_action_text(self, parent_widget):
        """Test empty state with action button."""
        empty = EmptyState(
            text="No items",
            action_text="Create new",
            parent=parent_widget
        )
        assert empty._action_text == "Create new"
        assert empty._action_btn is not None

    def test_action_enabled(self, parent_widget):
        """Test action button enabled state."""
        empty = EmptyState(
            text="No items",
            action_text="Create",
            action_enabled=True,
            parent=parent_widget
        )
        assert empty._action_enabled
        assert empty._action_btn is not None
        assert empty._action_btn.isEnabled()

    def test_action_disabled(self, parent_widget):
        """Test action button can be created disabled."""
        empty = EmptyState(
            text="No items",
            action_text="Create",
            action_enabled=False,
            parent=parent_widget
        )
        assert not empty._action_enabled
        assert empty._action_btn is not None
        assert not empty._action_btn.isEnabled()

    def test_without_action(self, parent_widget):
        """Test empty state without action button."""
        empty = EmptyState(text="No items", parent=parent_widget)
        assert empty._action_btn is None

    def test_set_text(self, parent_widget):
        """Test set_text updates message text."""
        empty = EmptyState(text="Original", parent=parent_widget)
        empty.set_text("Updated")
        assert empty.text() == "Updated"

    def test_set_action_enabled(self, parent_widget):
        """Test set_action_enabled updates button state."""
        empty = EmptyState(
            text="No items",
            action_text="Create",
            action_enabled=True,
            parent=parent_widget
        )

        empty.set_action_enabled(False)
        assert not empty._action_enabled
        assert not empty._action_btn.isEnabled()

        empty.set_action_enabled(True)
        assert empty._action_enabled
        assert empty._action_btn.isEnabled()

    def test_action_clicked_signal(self, parent_widget, qapp):
        """Test action_clicked signal is emitted."""
        empty = EmptyState(
            text="No items",
            action_text="Create",
            parent=parent_widget
        )

        signals = []
        empty.action_clicked.connect(lambda: signals.append(True))

        empty._action_btn.click()
        assert signals == [True]

    def test_initial_disabled_state(self, parent_widget):
        """Test empty state can be created disabled."""
        empty = EmptyState(text="No items", enabled=False, parent=parent_widget)
        assert not empty.isEnabled()

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        empty = EmptyState(text="No items", parent=parent_widget)
        stylesheet = empty._get_v2_stylesheet()

        assert THEME_V2.bg_component in stylesheet
        assert THEME_V2.text_primary in stylesheet
        assert THEME_V2.border in stylesheet
        assert THEME_V2.bg_hover in stylesheet


# =============================================================================
# CARD TESTS
# =============================================================================


class TestCard:
    """Tests for Card component."""

    def test_initialization(self, parent_widget):
        """Test card can be initialized."""
        card = Card(parent=parent_widget)
        assert card.title() == ""
        assert card.content() is None
        assert card.has_border()

    def test_with_title(self, parent_widget):
        """Test card with title."""
        card = Card(title="Settings", parent=parent_widget)
        assert card.title() == "Settings"
        assert card._title_label is not None
        assert card._header_widget is not None

    def test_with_content_widget(self, parent_widget, content_widget):
        """Test card with content widget."""
        card = Card(content_widget=content_widget, parent=parent_widget)
        assert card.content() is content_widget

    def test_border_default(self, parent_widget):
        """Test card has border by default."""
        card = Card(parent=parent_widget)
        assert card._border

    def test_border_disabled(self, parent_widget):
        """Test card can be created without border."""
        card = Card(border=False, parent=parent_widget)
        assert not card._border

    def test_closable_true(self, parent_widget):
        """Test card with close button."""
        card = Card(title="Closable", closable=True, parent=parent_widget)
        assert card._closable
        assert card._close_btn is not None
        assert card._header_widget is not None

    def test_closable_false(self, parent_widget):
        """Test card without close button."""
        card = Card(title="Not Closable", closable=False, parent=parent_widget)
        assert not card._closable
        assert card._close_btn is None

    def test_closable_without_title(self, parent_widget):
        """Test closable card without title still has header."""
        card = Card(closable=True, parent=parent_widget)
        assert card._header_widget is not None
        assert card._close_btn is not None

    def test_set_title(self, parent_widget, qapp):
        """Test set_title updates title."""
        card = Card(title="Original", parent=parent_widget)
        card.set_title("Updated")
        assert card.title() == "Updated"

    def test_set_title_emits_signal(self, parent_widget, qapp):
        """Test set_title emits title_changed signal."""
        card = Card(title="Original", parent=parent_widget)

        signals = []
        card.title_changed.connect(lambda t: signals.append(t))

        card.set_title("Updated")
        assert signals == ["Updated"]

    def test_set_content(self, parent_widget, content_widget):
        """Test set_content updates content widget."""
        card = Card(parent=parent_widget)
        card.set_content(content_widget)
        assert card.content() is content_widget

    def test_set_content_replaces_existing(self, parent_widget):
        """Test set_content replaces existing content."""
        widget1 = QLabel("Widget 1", parent_widget)
        widget2 = QLabel("Widget 2", parent_widget)

        card = Card(content_widget=widget1, parent=parent_widget)
        assert card.content() is widget1

        card.set_content(widget2)
        assert card.content() is widget2

    def test_set_border(self, parent_widget):
        """Test set_border updates border state."""
        card = Card(border=True, parent=parent_widget)

        card.set_border(False)
        assert not card._border

        card.set_border(True)
        assert card._border

    def test_close_requested_signal(self, parent_widget, qapp):
        """Test close_requested signal is emitted."""
        card = Card(title="Closable", closable=True, parent=parent_widget)

        signals = []
        card.close_requested.connect(lambda: signals.append(True))

        card._close_btn.click()
        assert signals == [True]

    def test_initial_disabled_state(self, parent_widget):
        """Test card can be created disabled."""
        card = Card(title="Disabled", enabled=False, parent=parent_widget)
        assert not card.isEnabled()

    def test_stylesheet_uses_theme_v2(self, parent_widget):
        """Test stylesheet uses THEME_V2 colors."""
        card = Card(title="Test", parent=parent_widget)
        stylesheet = card._get_v2_stylesheet()

        assert THEME_V2.bg_elevated in stylesheet
        assert THEME_V2.border in stylesheet
        assert str(TOKENS_V2.radius.md) in stylesheet


# =============================================================================
# CONVENIENCE FUNCTIONS TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_create_divider_default(self, parent_widget):
        """Test create_divider with defaults."""
        divider = create_divider(parent=parent_widget)
        assert isinstance(divider, Divider)
        assert divider._orientation == "horizontal"
        assert divider._margin == TOKENS_V2.margin.standard

    def test_create_divider_vertical(self, parent_widget):
        """Test create_divider with vertical orientation."""
        divider = create_divider(orientation="vertical", parent=parent_widget)
        assert isinstance(divider, Divider)
        assert divider._orientation == "vertical"

    def test_create_divider_custom_margin(self, parent_widget):
        """Test create_divider with custom margin."""
        divider = create_divider(margin="tight", parent=parent_widget)
        assert isinstance(divider, Divider)
        assert divider._margin == TOKENS_V2.margin.tight

    def test_create_empty_state_default(self, parent_widget):
        """Test create_empty_state with defaults."""
        empty = create_empty_state(parent=parent_widget)
        assert isinstance(empty, EmptyState)

    def test_create_empty_state_with_params(self, parent_widget):
        """Test create_empty_state with parameters."""
        empty = create_empty_state(
            icon="inbox",
            text="No items",
            action_text="Create",
            action_enabled=False,
            parent=parent_widget
        )
        assert isinstance(empty, EmptyState)
        assert empty.text() == "No items"
        assert not empty._action_enabled

    def test_create_card_default(self, parent_widget):
        """Test create_card with defaults."""
        card = create_card(parent=parent_widget)
        assert isinstance(card, Card)

    def test_create_card_with_params(self, parent_widget, content_widget):
        """Test create_card with parameters."""
        card = create_card(
            title="Test Card",
            content_widget=content_widget,
            border=False,
            closable=True,
            parent=parent_widget
        )
        assert isinstance(card, Card)
        assert card.title() == "Test Card"
        assert not card._border
        assert card._closable


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestStructuralIntegration:
    """Integration tests for structural components."""

    def test_section_header_with_divider(self, parent_widget):
        """Test section header above divider in layout."""
        layout = QVBoxLayout(parent_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = SectionHeader(text="Section", parent=parent_widget)
        divider = create_divider(parent=parent_widget)

        layout.addWidget(header)
        layout.addWidget(divider)

        assert layout.count() == 2

    def test_card_with_empty_state(self, parent_widget):
        """Test card containing empty state."""
        layout = QVBoxLayout(parent_widget)

        card = create_card(title="Items", parent=parent_widget)
        empty = create_empty_state(
            icon="inbox",
            text="No items yet",
            action_text="Add item",
            parent=parent_widget
        )

        card.set_content(empty)
        layout.addWidget(card)

        assert card.content() is empty

    def test_multiple_dividers_orientation(self, parent_widget):
        """Test multiple dividers with different orientations."""
        h_layout = QHBoxLayout(parent_widget)

        h_divider = create_divider(orientation="horizontal")
        v_divider = create_divider(orientation="vertical")

        # Can add both to different layouts
        v_layout = QVBoxLayout()
        v_layout.addWidget(h_divider)

        h_layout.addWidget(v_divider)
        h_layout.addLayout(v_layout)

        assert h_divider._orientation == "horizontal"
        assert v_divider._orientation == "vertical"
