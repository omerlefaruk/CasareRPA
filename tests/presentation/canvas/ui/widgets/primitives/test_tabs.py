"""
Tests for Tab Components v2 - Epic 5.1 Component Library.

Tests TabWidget, TabBar, and Tab dataclass components.
"""

from dataclasses import FrozenInstanceError

import pytest
from PySide6.QtWidgets import QLabel, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    Tab,
    TabBar,
    TabWidget,
    create_tab,
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
def sample_tabs():
    """Sample tabs for testing."""
    return [
        Tab(id="home", title="Home", content=QLabel("Home content")),
        Tab(id="settings", title="Settings", content=QLabel("Settings content")),
        Tab(id="about", title="About", content=QLabel("About content")),
    ]


@pytest.fixture
def sample_tabs_with_icons():
    """Sample tabs with icons for testing."""
    return [
        Tab(
            id="home",
            title="Home",
            icon=get_icon("home", size=16),
            content=QLabel("Home content"),
        ),
        Tab(
            id="settings",
            title="Settings",
            icon=get_icon("settings", size=16),
            content=QLabel("Settings content"),
        ),
    ]


# =============================================================================
# TAB DATACLASS TESTS
# =============================================================================


class TestTab:
    """Tests for Tab dataclass."""

    def test_tab_creation(self):
        """Test tab can be created with required fields."""
        tab = Tab(id="test", title="Test", content=QLabel("Content"))

        assert tab.id == "test"
        assert tab.title == "Test"
        assert tab.icon is None
        assert not tab.closable

    def test_tab_with_icon(self):
        """Test tab with icon."""
        icon = get_icon("check", size=16)
        tab = Tab(id="test", title="Test", icon=icon, content=QLabel("Content"))

        assert tab.icon is not None
        assert not tab.icon().isNull()

    def test_tab_closable(self):
        """Test closable tab."""
        tab = Tab(id="test", title="Test", content=QLabel("Content"), closable=True)

        assert tab.closable

    def test_tab_is_frozen(self):
        """Test tab is frozen (immutable)."""
        tab = Tab(id="test", title="Test", content=QLabel("Content"))

        with pytest.raises(FrozenInstanceError):
            tab.id = "new_id"


# =============================================================================
# TAB WIDGET TESTS
# =============================================================================


class TestTabWidget:
    """Tests for TabWidget component."""

    def test_initialization_empty(self, parent_widget):
        """Test empty tab widget can be created."""
        widget = TabWidget(parent=parent_widget)

        assert widget.get_tab_count() == 0
        assert widget.get_current_tab_id() is None

    def test_initialization_with_tabs(self, parent_widget, sample_tabs):
        """Test tab widget with initial tabs."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert widget.get_tab_count() == 3
        assert widget.get_tab_ids() == ["home", "settings", "about"]

    def test_add_tab(self, parent_widget):
        """Test adding tabs."""
        widget = TabWidget(parent=parent_widget)

        widget.add_tab(Tab(id="home", title="Home", content=QLabel("Home")))
        assert widget.get_tab_count() == 1

        widget.add_tab(Tab(id="settings", title="Settings", content=QLabel("Settings")))
        assert widget.get_tab_count() == 2

    def test_add_tab_with_icon(self, parent_widget, sample_tabs_with_icons):
        """Test adding tabs with icons."""
        widget = TabWidget(tabs=sample_tabs_with_icons, parent=parent_widget)

        assert widget.get_tab_count() == 2
        # Icons should be present
        assert widget.tabIcon(0) is not None
        assert widget.tabIcon(1) is not None

    def test_remove_tab(self, parent_widget, sample_tabs):
        """Test removing tabs by ID."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert widget.get_tab_count() == 3
        assert widget.remove_tab("settings")
        assert widget.get_tab_count() == 2
        assert widget.get_tab_ids() == ["home", "about"]

    def test_remove_nonexistent_tab(self, parent_widget, sample_tabs):
        """Test removing non-existent tab returns False."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert not widget.remove_tab("nonexistent")
        assert widget.get_tab_count() == 3

    def test_get_tab(self, parent_widget, sample_tabs):
        """Test getting tab by ID."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        tab = widget.get_tab("settings")
        assert tab is not None
        assert tab.id == "settings"
        assert tab.title == "Settings"

    def test_get_nonexistent_tab(self, parent_widget, sample_tabs):
        """Test getting non-existent tab returns None."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert widget.get_tab("nonexistent") is None

    def test_get_current_tab_id(self, parent_widget, sample_tabs):
        """Test getting current tab ID."""
        from PySide6.QtWidgets import QApplication

        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        # First tab should be selected by default
        QApplication.instance().processEvents()
        assert widget.get_current_tab_id() == "home"

    def test_set_current_tab(self, parent_widget, sample_tabs):
        """Test setting current tab by ID."""
        from PySide6.QtWidgets import QApplication

        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert widget.set_current_tab("settings")
        QApplication.instance().processEvents()
        assert widget.get_current_tab_id() == "settings"

    def test_set_nonexistent_current_tab(self, parent_widget, sample_tabs):
        """Test setting non-existent tab returns False."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert not widget.set_current_tab("nonexistent")

    def test_position_top(self, parent_widget, sample_tabs):
        """Test top position (default)."""
        widget = TabWidget(tabs=sample_tabs, position="top", parent=parent_widget)

        assert widget.get_position() == "top"

    def test_position_bottom(self, parent_widget, sample_tabs):
        """Test bottom position."""
        widget = TabWidget(tabs=sample_tabs, position="bottom", parent=parent_widget)

        assert widget.get_position() == "bottom"

    def test_position_left(self, parent_widget, sample_tabs):
        """Test left position."""
        widget = TabWidget(tabs=sample_tabs, position="left", parent=parent_widget)

        assert widget.get_position() == "left"

    def test_position_right(self, parent_widget, sample_tabs):
        """Test right position."""
        widget = TabWidget(tabs=sample_tabs, position="right", parent=parent_widget)

        assert widget.get_position() == "right"

    def test_set_position(self, parent_widget, sample_tabs):
        """Test changing position."""
        widget = TabWidget(tabs=sample_tabs, position="top", parent=parent_widget)

        widget.set_position("bottom")
        assert widget.get_position() == "bottom"

        widget.set_position("left")
        assert widget.get_position() == "left"

    def test_closable_false(self, parent_widget):
        """Test non-closable tabs."""
        tabs = [
            Tab(id="home", title="Home", content=QLabel("Home"), closable=False),
        ]
        widget = TabWidget(tabs=tabs, closable=False, parent=parent_widget)

        assert not widget.get_closable()

    def test_closable_true(self, parent_widget):
        """Test closable tabs."""
        tabs = [
            Tab(id="home", title="Home", content=QLabel("Home"), closable=True),
        ]
        widget = TabWidget(tabs=tabs, closable=True, parent=parent_widget)

        assert widget.get_closable()

    def test_set_closable(self, parent_widget):
        """Test changing closable state."""
        widget = TabWidget(closable=False, parent=parent_widget)

        widget.set_closable(True)
        assert widget.get_closable()

        widget.set_closable(False)
        assert not widget.get_closable()

    def test_tab_changed_signal(self, parent_widget, sample_tabs):
        """Test tab_changed signal emission."""
        from PySide6.QtWidgets import QApplication

        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)
        received = []

        widget.tab_changed.connect(lambda tab_id: received.append(tab_id))

        widget.setCurrentIndex(1)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == "settings"

    def test_tab_close_requested_signal(self, parent_widget):
        """Test tab_close_requested signal emission."""
        from PySide6.QtWidgets import QApplication

        tabs = [Tab(id="home", title="Home", content=QLabel("Home"), closable=True)]
        widget = TabWidget(tabs=tabs, closable=True, parent=parent_widget)
        received = []

        widget.tab_close_requested.connect(lambda tab_id: received.append(tab_id))

        # Simulate close request
        widget.tabCloseRequested.emit(0)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == "home"

    def test_tab_added_signal(self, parent_widget):
        """Test tab_added signal emission."""
        widget = TabWidget(parent=parent_widget)
        received = []

        widget.tab_added.connect(lambda tab_id, index: received.append((tab_id, index)))

        widget.add_tab(Tab(id="test", title="Test", content=QLabel("Test")))

        assert len(received) == 1
        assert received[0] == ("test", 0)

    def test_tab_removed_signal(self, parent_widget, sample_tabs):
        """Test tab_removed signal emission."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)
        received = []

        widget.tab_removed.connect(lambda tab_id: received.append(tab_id))

        widget.remove_tab("settings")

        assert len(received) == 1
        assert received[0] == "settings"

    def test_styling_applied(self, parent_widget, sample_tabs):
        """Test v2 styling is applied."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        # Check stylesheet is set
        assert widget.styleSheet() != ""
        # Should contain THEME_V2 colors
        assert THEME_V2.bg_surface in widget.styleSheet()

    def test_document_mode_enabled(self, parent_widget, sample_tabs):
        """Test document mode is enabled for cleaner look."""
        widget = TabWidget(tabs=sample_tabs, parent=parent_widget)

        assert widget.documentMode()

    def test_tabs_closable_state(self, parent_widget):
        """Test tabsClosable property is set correctly."""
        widget_closable = TabWidget(closable=True, parent=parent_widget)
        assert widget_closable.tabsClosable()

        widget_not_closable = TabWidget(closable=False, parent=parent_widget)
        assert not widget_not_closable.tabsClosable()


# =============================================================================
# TAB BAR TESTS
# =============================================================================


class TestTabBar:
    """Tests for TabBar component."""

    def test_initialization_empty(self, parent_widget):
        """Test empty tab bar can be created."""
        bar = TabBar(parent=parent_widget)

        assert bar.get_tab_count() == 0
        assert bar.get_current_tab_id() is None

    def test_initialization_with_tabs(self, parent_widget, sample_tabs):
        """Test tab bar with initial tabs."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert bar.get_tab_count() == 3
        assert bar.get_tab_ids() == ["home", "settings", "about"]

    def test_add_tab(self, parent_widget):
        """Test adding tabs."""
        bar = TabBar(parent=parent_widget)

        bar.add_tab(Tab(id="home", title="Home", content=QLabel("Home")))
        assert bar.get_tab_count() == 1

        bar.add_tab(Tab(id="settings", title="Settings", content=QLabel("Settings")))
        assert bar.get_tab_count() == 2

    def test_add_tab_with_icon(self, parent_widget, sample_tabs_with_icons):
        """Test adding tabs with icons."""
        bar = TabBar(tabs=sample_tabs_with_icons, parent=parent_widget)

        assert bar.get_tab_count() == 2
        # Icons should be present
        assert bar.tabIcon(0) is not None
        assert bar.tabIcon(1) is not None

    def test_remove_tab(self, parent_widget, sample_tabs):
        """Test removing tabs by ID."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert bar.get_tab_count() == 3
        assert bar.remove_tab("settings")
        assert bar.get_tab_count() == 2

    def test_remove_nonexistent_tab(self, parent_widget, sample_tabs):
        """Test removing non-existent tab returns False."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert not bar.remove_tab("nonexistent")
        assert bar.get_tab_count() == 3

    def test_get_tab(self, parent_widget, sample_tabs):
        """Test getting tab by ID."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        tab = bar.get_tab("settings")
        assert tab is not None
        assert tab.id == "settings"
        assert tab.title == "Settings"

    def test_get_nonexistent_tab(self, parent_widget, sample_tabs):
        """Test getting non-existent tab returns None."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert bar.get_tab("nonexistent") is None

    def test_get_current_tab_id(self, parent_widget, sample_tabs):
        """Test getting current tab ID."""
        from PySide6.QtWidgets import QApplication

        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        # First tab should be selected by default
        QApplication.instance().processEvents()
        assert bar.get_current_tab_id() == "home"

    def test_set_current_tab(self, parent_widget, sample_tabs):
        """Test setting current tab by ID."""
        from PySide6.QtWidgets import QApplication

        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert bar.set_current_tab("settings")
        QApplication.instance().processEvents()
        assert bar.get_current_tab_id() == "settings"

    def test_set_nonexistent_current_tab(self, parent_widget, sample_tabs):
        """Test setting non-existent tab returns False."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert not bar.set_current_tab("nonexistent")

    def test_position_property(self, parent_widget):
        """Test position property."""
        bar = TabBar(position="top", parent=parent_widget)
        assert bar.get_position() == "top"

        bar.set_position("bottom")
        assert bar.get_position() == "bottom"

    def test_draggable_false(self, parent_widget):
        """Test non-draggable tabs (default)."""
        bar = TabBar(draggable=False, parent=parent_widget)

        assert not bar.get_draggable()
        assert not bar.isMovable()

    def test_draggable_true(self, parent_widget):
        """Test draggable tabs."""
        bar = TabBar(draggable=True, parent=parent_widget)

        assert bar.get_draggable()
        assert bar.isMovable()

    def test_set_draggable(self, parent_widget):
        """Test changing draggable state."""
        bar = TabBar(draggable=False, parent=parent_widget)

        bar.set_draggable(True)
        assert bar.get_draggable()
        assert bar.isMovable()

        bar.set_draggable(False)
        assert not bar.get_draggable()
        assert not bar.isMovable()

    def test_tab_clicked_signal(self, parent_widget, sample_tabs):
        """Test tab_clicked signal emission."""
        from PySide6.QtWidgets import QApplication

        bar = TabBar(tabs=sample_tabs, parent=parent_widget)
        received = []

        bar.tab_clicked.connect(lambda tab_id: received.append(tab_id))

        bar.setCurrentIndex(1)
        QApplication.instance().processEvents()

        assert len(received) >= 1
        assert received[-1] == "settings"

    def test_tab_moved_signal(self, parent_widget):
        """Test tab_moved signal emission."""
        from PySide6.QtWidgets import QApplication

        bar = TabBar(
            tabs=[
                Tab(id="a", title="A", content=QLabel()),
                Tab(id="b", title="B", content=QLabel()),
            ],
            draggable=True,
            parent=parent_widget,
        )
        received = []

        bar.tab_moved.connect(lambda from_idx, to_idx: received.append((from_idx, to_idx)))

        # Simulate tab move
        bar.tabMoved.emit(0, 1)
        QApplication.instance().processEvents()

        assert len(received) >= 1

    def test_styling_applied(self, parent_widget, sample_tabs):
        """Test v2 styling is applied."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        # Check stylesheet is set
        assert bar.styleSheet() != ""
        # Should contain THEME_V2 colors
        assert THEME_V2.bg_header in bar.styleSheet()

    def test_draw_base_disabled(self, parent_widget, sample_tabs):
        """Test drawBase is False for cleaner look."""
        bar = TabBar(tabs=sample_tabs, parent=parent_widget)

        assert not bar.drawBase()

    def test_get_tab_count(self, parent_widget):
        """Test getting tab count."""
        bar = TabBar(parent=parent_widget)

        assert bar.get_tab_count() == 0

        bar.add_tab(Tab(id="a", title="A", content=QLabel()))
        assert bar.get_tab_count() == 1

        bar.add_tab(Tab(id="b", title="B", content=QLabel()))
        assert bar.get_tab_count() == 2

    def test_get_tab_ids(self, parent_widget):
        """Test getting list of tab IDs."""
        bar = TabBar(parent=parent_widget)

        bar.add_tab(Tab(id="a", title="A", content=QLabel()))
        bar.add_tab(Tab(id="b", title="B", content=QLabel()))
        bar.add_tab(Tab(id="c", title="C", content=QLabel()))

        assert bar.get_tab_ids() == ["a", "b", "c"]


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_create_tab_basic(self, parent_widget):
        """Test create_tab with basic parameters."""
        tab = create_tab("home", "Home")

        assert tab.id == "home"
        assert tab.title == "Home"
        assert tab.icon is None
        assert not tab.closable
        # Content is a placeholder widget
        assert tab.content is not None

    def test_create_tab_with_content(self, parent_widget):
        """Test create_tab with custom content."""
        content = QLabel("Custom content")
        tab = create_tab("test", "Test", content=content)

        assert tab.content is content

    def test_create_tab_with_icon(self, parent_widget):
        """Test create_tab with icon."""
        tab = create_tab("settings", "Settings", icon_name="settings")

        assert tab.icon is not None
        assert not tab.icon().isNull()

    def test_create_tab_closable(self, parent_widget):
        """Test create_tab closable parameter."""
        tab = create_tab("test", "Test", closable=True)

        assert tab.closable

    def test_create_tab_full(self, parent_widget):
        """Test create_tab with all parameters."""
        content = QLabel("Content")
        tab = create_tab(
            tab_id="dashboard",
            title="Dashboard",
            content=content,
            icon_name="layout",
            closable=True,
        )

        assert tab.id == "dashboard"
        assert tab.title == "Dashboard"
        assert tab.content is content
        assert tab.icon is not None
        assert tab.closable

