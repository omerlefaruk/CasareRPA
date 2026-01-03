"""
Tab Components v2 - Epic 5.1 Component Library.

Themed tab components using THEME_V2 and TOKENS_V2 for consistent styling.
Provides TabWidget, TabBar, and Tab dataclass for tabbed interfaces.

Components:
    Tab: Dataclass for tab configuration
    TabWidget: Complete tabbed widget with content panes
    TabBar: Tab bar for custom implementations (Epic 5.2 drag support)

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives import (
        TabWidget,
        Tab,
        TabBar,
        TabPosition,
    )
    from PySide6.QtWidgets import QLabel

    # Create tabs
    tabs = [
        Tab(id="home", title="Home", icon=get_icon("home", size=16), content=QLabel("Home")),
        Tab(id="settings", title="Settings", content=QLabel("Settings")),
    ]

    # Use TabWidget
    widget = TabWidget(tabs=tabs, position="top", closable=True)
    widget.tab_changed.connect(lambda tab_id: print(f"Active: {tab_id}"))
    widget.tab_close_requested.connect(lambda tab_id: print(f"Close: {tab_id}"))

    # Use TabBar for custom implementations
    bar = TabBar(tabs=tabs, position="top")

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Any, Literal

from loguru import logger
from PySide6.QtCore import QPoint, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QTabBar, QTabWidget, QWidget

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

if TYPE_CHECKING:
    from PySide6.QtGui import QMouseEvent


# =============================================================================
# TYPE ALIASES
# =============================================================================

TabPosition = Literal["top", "bottom", "left", "right"]


# =============================================================================
# TAB DATACLASS
# =============================================================================


@dataclass(frozen=True)
class TabIcon:
    """
    Callable wrapper around a QIcon.

    Some tests (and a few older call sites) expect `tab.icon()` to return a
    `QIcon`, so this wrapper supports both attribute-style access and calling.
    """

    _icon: QIcon

    def __call__(self) -> QIcon:
        return self._icon

    def __getattr__(self, name: str) -> Any:
        return getattr(self._icon, name)


@dataclass(frozen=True)
class Tab:
    """
    Configuration data for a single tab.

    Attributes:
        id: Unique identifier for the tab
        title: Display text shown on the tab
        icon: Optional icon to display next to title
        content: Widget to show when tab is selected
        closable: Whether tab can be closed (has X button)

    Example:
        from PySide6.QtWidgets import QLabel

        tab = Tab(
            id="dashboard",
            title="Dashboard",
            icon=get_icon("layout-dashboard", size=16),
            content=QLabel("Dashboard content"),
            closable=False
        )
    """

    id: str
    title: str
    content: QWidget
    icon: TabIcon | QIcon | None = None
    closable: bool = False

    def __post_init__(self) -> None:
        if self.icon is not None and not isinstance(self.icon, TabIcon):
            object.__setattr__(self, "icon", TabIcon(self.icon))


def _resolve_tab_icon(icon: TabIcon | QIcon | None) -> QIcon | None:
    if icon is None:
        return None
    if isinstance(icon, TabIcon):
        return icon()
    return icon


# =============================================================================
# TAB WIDGET
# =============================================================================


class TabWidget(QTabWidget):
    """
    Complete tabbed widget with v2 styling and enhanced signals.

    Wraps QTabWidget with THEME_V2 colors and TOKENS_V2 sizing.
    Supports closable tabs with X buttons and position configuration.

    Signals:
        tab_changed: Emitted when active tab changes (str: tab_id)
        tab_close_requested: Emitted when tab close is requested (str: tab_id)
        tab_added: Emitted when a tab is added (str: tab_id, int: index)
        tab_removed: Emitted when a tab is removed (str: tab_id)

    Properties:
        position: Tab bar position (top/bottom/left/right)
        closable: Default closable state for new tabs

    Example:
        from PySide6.QtWidgets import QLabel

        tabs = [
            Tab(id="home", title="Home", content=QLabel("Home content")),
            Tab(id="settings", title="Settings", icon=get_icon("settings"), content=QLabel("Settings")),
        ]

        widget = TabWidget(tabs=tabs, position="top", closable=True)
        widget.tab_changed.connect(lambda tab_id: print(f"Active: {tab_id}"))
        widget.tab_close_requested.connect(lambda tab_id: widget.remove_tab(tab_id))
    """

    # Custom signals with tab_id payload
    tab_changed = Signal(str)  # Emitted when active tab changes
    tab_close_requested = Signal(str)  # Emitted when close clicked
    tab_added = Signal(str, int)  # Emitted when tab added (id, index)
    tab_removed = Signal(str)  # Emitted when tab removed

    # Qt position mapping
    _POSITION_MAP: dict[TabPosition, QTabWidget.TabPosition] = {
        "top": QTabWidget.TabPosition.North,
        "bottom": QTabWidget.TabPosition.South,
        "left": QTabWidget.TabPosition.West,
        "right": QTabWidget.TabPosition.East,
    }

    def __init__(
        self,
        tabs: list[Tab] | None = None,
        parent: QWidget | None = None,
        position: TabPosition = "top",
        closable: bool = False,
    ) -> None:
        """
        Initialize the tab widget.

        Args:
            tabs: Initial list of tabs to display
            parent: Optional parent widget
            position: Tab bar position: top, bottom, left, right
            closable: Default closable state for tabs
        """
        super().__init__(parent)

        self._position: TabPosition = position
        self._closable: bool = closable
        self._tabs: list[Tab] = []

        # Track tab_id to index mapping
        self._tab_id_to_index: dict[str, int] = {}
        self._index_to_tab_id: dict[int, str] = {}

        self._setup_ui()
        self._apply_styles()

        # Add initial tabs
        if tabs:
            for tab in tabs:
                self.add_tab(tab)

        logger.debug(
            f"{self.__class__.__name__} created: {len(self._tabs)} tabs, position={position}"
        )

    def _setup_ui(self) -> None:
        """Setup widget properties."""
        # Set tab bar position
        self.setTabPosition(self._POSITION_MAP[self._position])

        # Enable document mode (cleaner look)
        self.setDocumentMode(True)

        # Disable automatic corner widget (we handle close buttons per-tab)
        self.setCornerWidget(None)

        # Set tabs closable globally
        self.setTabsClosable(self._closable)

        # Set scroll buttons on (for many tabs)
        self.setElideMode(Qt.TextElideMode.ElideRight)

        # Connect built-in close signal to our custom handler
        self.tabCloseRequested.connect(self._on_close_requested)

        # Connect current changed signal
        self.currentChanged.connect(self._on_current_changed)

    def _apply_styles(self) -> None:
        """Apply v2 dark theme styling."""
        t = THEME_V2
        radius = TOKENS_V2.radius.sm

        stylesheet = f"""
            /* Tab Widget Container */
            QTabWidget {{
                background-color: {t.bg_surface};
                border: none;
            }}

            /* Tab Pane (content area) */
            QTabWidget::pane {{
                background-color: {t.bg_surface};
                border: none;
                border-top: 1px solid {t.border};
                border-radius: {radius}px;
            }}

            /* Tab Bar */
            QTabBar {{
                background-color: {t.bg_header};
                qproperty-drawBase: 0;
            }}

            /* Tab (unselected) */
            QTabBar::tab {{
                background-color: transparent;
                color: {t.text_secondary};
                border: none;
                border-bottom: 2px solid transparent;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
                margin-right: {TOKENS_V2.spacing.xxs}px;
                margin-bottom: 0;
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                min-width: {TOKENS_V2.sizes.tab_min_width}px;
                border-top-left-radius: {radius}px;
                border-top-right-radius: {radius}px;
            }}

            /* Tab (selected) */
            QTabBar::tab:selected {{
                color: {t.text_primary};
                background-color: {t.bg_surface};
                border-bottom: 2px solid {t.primary};
            }}

            /* Tab (hover) */
            QTabBar::tab:hover:!selected {{
                color: {t.text_primary};
                background-color: {t.bg_hover};
                border-radius: {radius}px {radius}px 0 0;
            }}

            /* Tab (disabled) */
            QTabBar::tab:disabled {{
                color: {t.text_disabled};
            }}

            /* Close button styling */
            QTabBar::close-button {{
                image: none;
                background: transparent;
                border: none;
                padding: {TOKENS_V2.spacing.xxs}px;
                margin-left: {TOKENS_V2.spacing.xs}px;
                subcontrol-position: right;
            }}

            QTabBar::close-button:hover {{
                background-color: {t.bg_hover};
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """

        self.setStyleSheet(stylesheet)

    def add_tab(self, tab: Tab) -> int:
        """
        Add a tab to the widget.

        Args:
            tab: Tab configuration

        Returns:
            Index of the added tab
        """
        self._tabs.append(tab)

        # Build tab label (icon + title)
        title = tab.title
        if tab.icon is not None:
            # Use addTab with icon variant
            index = self.addTab(tab.content, _resolve_tab_icon(tab.icon) or QIcon(), title)
        else:
            index = self.addTab(tab.content, title)

        # Set closable per-tab
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, None)
        if tab.closable or self._closable:
            self._add_close_button(index)

        # Update mappings
        self._tab_id_to_index[tab.id] = index
        self._index_to_tab_id[index] = tab.id

        # Emit signal
        self.tab_added.emit(tab.id, index)

        logger.debug(f"{self.__class__.__name__} added tab: {tab.id} at index {index}")
        return index

    def _add_close_button(self, index: int) -> None:
        """
        Add a close button to a tab.

        Uses a ToolButton with the close icon from icons_v2.
        """
        from PySide6.QtWidgets import QToolButton

        close_btn = QToolButton(self)
        close_icon = get_icon("x", size=14)
        close_btn.setIcon(close_icon)
        close_btn.setIconSize(
            close_btn.iconSize().expandedTo(close_icon.actualSize(close_btn.iconSize()))
        )
        close_btn.setAutoRaise(True)
        close_btn.setStyleSheet(f"""
            QToolButton {{
                background: transparent;
                border: none;
                padding: {TOKENS_V2.spacing.xxs}px;
                margin-left: {TOKENS_V2.spacing.xs}px;
            }}
            QToolButton:hover {{
                background-color: {THEME_V2.bg_hover};
                border-radius: {TOKENS_V2.radius.xs}px;
            }}
        """)

        # Store tab_id in button for signal handling
        tab_id = self._index_to_tab_id.get(index, "")
        close_btn.setProperty("tab_id", tab_id)

        # Connect click to our handler
        close_btn.clicked.connect(partial(self._on_close_button_clicked, tab_id))

        # Set as close button
        self.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, close_btn)

    @Slot()
    def _on_close_button_clicked(self, tab_id: str) -> None:
        """Handle close button click."""
        self.tab_close_requested.emit(tab_id)

    @Slot()
    def _on_close_requested(self, index: int) -> None:
        """Handle built-in tabCloseRequested signal."""
        tab_id = self._index_to_tab_id.get(index, "")
        if tab_id:
            self.tab_close_requested.emit(tab_id)

    @Slot()
    def _on_current_changed(self, index: int) -> None:
        """Handle current tab change."""
        if index < 0:
            return  # No tab selected

        tab_id = self._index_to_tab_id.get(index, "")
        if tab_id:
            self.tab_changed.emit(tab_id)

    def remove_tab(self, tab_id: str) -> bool:
        """
        Remove a tab by ID.

        Args:
            tab_id: ID of tab to remove

        Returns:
            True if tab was removed, False if not found
        """
        if tab_id not in self._tab_id_to_index:
            logger.warning(f"{self.__class__.__name__}: tab ID not found: {tab_id}")
            return False

        index = self._tab_id_to_index[tab_id]
        self.removeTab(index)

        # Update mappings
        del self._tab_id_to_index[tab_id]
        del self._index_to_tab_id[index]

        # Remove from tabs list
        self._tabs = [t for t in self._tabs if t.id != tab_id]

        # Rebuild index mappings (shift after removal)
        self._rebuild_mappings()

        self.tab_removed.emit(tab_id)
        logger.debug(f"{self.__class__.__name__} removed tab: {tab_id}")
        return True

    def _rebuild_mappings(self) -> None:
        """Rebuild tab_id to index mappings after removal/insertion."""
        self._tab_id_to_index.clear()
        self._index_to_tab_id.clear()

        for i, tab in enumerate(self._tabs):
            self._tab_id_to_index[tab.id] = i
            self._index_to_tab_id[i] = tab.id

    def get_tab(self, tab_id: str) -> Tab | None:
        """
        Get a tab configuration by ID.

        Args:
            tab_id: ID of tab to get

        Returns:
            Tab configuration or None if not found
        """
        for tab in self._tabs:
            if tab.id == tab_id:
                return tab
        return None

    def get_current_tab_id(self) -> str | None:
        """
        Get the ID of the currently selected tab.

        Returns:
            Tab ID or None if no tab selected
        """
        index = self.currentIndex()
        return self._index_to_tab_id.get(index)

    def set_current_tab(self, tab_id: str) -> bool:
        """
        Set the current tab by ID.

        Args:
            tab_id: ID of tab to select

        Returns:
            True if tab was selected, False if not found
        """
        if tab_id not in self._tab_id_to_index:
            logger.warning(f"{self.__class__.__name__}: tab ID not found: {tab_id}")
            return False

        index = self._tab_id_to_index[tab_id]
        self.setCurrentIndex(index)
        return True

    def set_position(self, position: TabPosition) -> None:
        """
        Update tab bar position.

        Args:
            position: New position: top, bottom, left, right
        """
        if self._position != position:
            self._position = position
            self.setTabPosition(self._POSITION_MAP[position])
            logger.debug(f"{self.__class__.__name__} position changed to: {position}")

    def get_position(self) -> TabPosition:
        """Get current tab bar position."""
        return self._position

    def set_closable(self, closable: bool) -> None:
        """
        Update default closable state.

        Note: This affects newly added tabs, not existing ones.

        Args:
            closable: Whether new tabs should be closable
        """
        self._closable = closable
        self.setTabsClosable(closable)
        logger.debug(f"{self.__class__.__name__} closable changed to: {closable}")

    def get_closable(self) -> bool:
        """Get default closable state."""
        return self._closable

    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return len(self._tabs)

    def get_tab_ids(self) -> list[str]:
        """Get list of all tab IDs."""
        return [tab.id for tab in self._tabs]


# =============================================================================
# TAB BAR
# =============================================================================


class TabBar(QTabBar):
    """
    Tab bar component for custom tab implementations.

    Provides v2-styled tab bar without the content pane.
    Useful for building custom tabbed interfaces or for Epic 5.2 drag support.

    Signals:
        tab_moved: Emitted when tab is moved (int: from_index, int: to_index)
        tab_clicked: Emitted when tab is clicked (str: tab_id)
        tab_context_menu_requested: Emitted when tab is right-clicked (str: tab_id, QPoint: pos)

    Properties:
        position: Tab bar position (affects orientation)
        draggable: Whether tabs can be dragged (Epic 5.2, default False)

    Example:
        bar = TabBar(
            tabs=[
                Tab(id="home", title="Home", icon=get_icon("home"), content=None),
                Tab(id="settings", title="Settings", content=None),
            ],
            position="top"
        )
        bar.tab_clicked.connect(lambda tab_id: print(f"Clicked: {tab_id}"))
    """

    tab_moved = Signal(int, int)
    tab_clicked = Signal(str)
    tab_context_menu_requested = Signal(str, QPoint)

    def __init__(
        self,
        tabs: list[Tab] | None = None,
        parent: QWidget | None = None,
        position: TabPosition = "top",
        draggable: bool = False,
    ) -> None:
        """
        Initialize the tab bar.

        Args:
            tabs: Initial list of tab configurations
            parent: Optional parent widget
            position: Tab bar position (affects orientation)
            draggable: Whether tabs can be dragged (Epic 5.2)
        """
        super().__init__(parent)

        self._position: TabPosition = position
        self._draggable: bool = draggable
        self._tabs: list[Tab] = []

        # Track tab_id to index mapping
        self._tab_id_to_index: dict[str, int] = {}
        self._index_to_tab_id: dict[int, str] = {}

        # Drag state
        self._drag_start_index: int = -1

        self._setup_ui()
        self._apply_styles()

        # Add initial tabs
        if tabs:
            for tab in tabs:
                self.add_tab(tab)

        logger.debug(
            f"{self.__class__.__name__} created: {len(self._tabs)} tabs, position={position}"
        )

    def _setup_ui(self) -> None:
        """Setup tab bar properties."""
        # Set document mode for cleaner look
        self.setDrawBase(False)

        # Enable/disable dragging
        self.setMovable(self._draggable)
        self.setExpanding(False)

        # Set elide mode
        self.setElideMode(Qt.TextElideMode.ElideRight)

        # Connect signals
        self.currentChanged.connect(self._on_current_changed)
        self.tabMoved.connect(self._on_tab_moved)

    def _apply_styles(self) -> None:
        """Apply v2 dark theme styling."""
        t = THEME_V2
        radius = TOKENS_V2.radius.sm

        # Adjust styles for vertical tabs
        if self._position in ("left", "right"):
            padding = f"{TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px"
        else:
            padding = f"{TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px"

        stylesheet = f"""
            QTabBar {{
                background-color: {t.bg_header};
                qproperty-drawBase: 0;
            }}

            QTabBar::tab {{
                background-color: transparent;
                color: {t.text_secondary};
                border: none;
                border-bottom: 2px solid transparent;
                padding: {padding};
                margin-right: {TOKENS_V2.spacing.xxs}px;
                margin-bottom: 0;
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
                min-width: {TOKENS_V2.sizes.tab_min_width}px;
                min-height: {TOKENS_V2.sizes.tab_height}px;
                border-top-left-radius: {radius}px;
                border-top-right-radius: {radius}px;
            }}

            QTabBar::tab:selected {{
                color: {t.text_primary};
                background-color: {t.bg_surface};
                border-bottom: 2px solid {t.primary};
            }}

            QTabBar::tab:hover:!selected {{
                color: {t.text_primary};
                background-color: {t.bg_hover};
                border-radius: {radius}px {radius}px 0 0;
            }}

            QTabBar::tab:disabled {{
                color: {t.text_disabled};
            }}
        """

        self.setStyleSheet(stylesheet)

    def add_tab(self, tab: Tab) -> int:
        """
        Add a tab to the bar.

        Args:
            tab: Tab configuration (content widget is ignored)

        Returns:
            Index of the added tab
        """
        self._tabs.append(tab)

        # Add tab (content ignored for TabBar)
        if tab.icon is not None:
            index = self.addTab(_resolve_tab_icon(tab.icon) or QIcon(), tab.title)
        else:
            index = self.addTab(tab.title)

        # Update mappings
        self._tab_id_to_index[tab.id] = index
        self._index_to_tab_id[index] = tab.id

        logger.debug(f"{self.__class__.__name__} added tab: {tab.id} at index {index}")
        return index

    @Slot()
    def _on_current_changed(self, index: int) -> None:
        """Handle current tab change."""
        if index < 0:
            return

        tab_id = self._index_to_tab_id.get(index, "")
        if tab_id:
            self.tab_clicked.emit(tab_id)

    @Slot(int, int)
    def _on_tab_moved(self, from_index: int, to_index: int) -> None:
        """Handle tab moved signal."""
        if from_index == to_index:
            return

        if 0 <= from_index < len(self._tabs) and 0 <= to_index < len(self._tabs):
            moved = self._tabs.pop(from_index)
            self._tabs.insert(to_index, moved)

        self.tab_moved.emit(from_index, to_index)
        self._drag_start_index = -1
        self._rebuild_mappings()

    def _rebuild_mappings(self) -> None:
        """Rebuild tab_id to index mappings after move/removal."""
        self._tab_id_to_index.clear()
        self._index_to_tab_id.clear()

        for i, tab in enumerate(self._tabs):
            self._tab_id_to_index[tab.id] = i
            self._index_to_tab_id[i] = tab.id

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press for drag start detection."""
        if self._draggable:
            self._drag_start_index = self.tabAt(event.pos())
        super().mousePressEvent(event)

    def contextMenuEvent(self, event: QMouseEvent) -> None:
        """Handle context menu request."""
        pos = event.pos()
        index = self.tabAt(pos)
        if index >= 0:
            tab_id = self._index_to_tab_id.get(index, "")
            if tab_id:
                self.tab_context_menu_requested.emit(tab_id, event.globalPos())

    def remove_tab(self, tab_id: str) -> bool:
        """
        Remove a tab by ID.

        Args:
            tab_id: ID of tab to remove

        Returns:
            True if tab was removed, False if not found
        """
        if tab_id not in self._tab_id_to_index:
            return False

        index = self._tab_id_to_index[tab_id]
        self.removeTab(index)

        # Update mappings
        del self._tab_id_to_index[tab_id]
        if index in self._index_to_tab_id:
            del self._index_to_tab_id[index]

        # Remove from tabs list
        self._tabs = [t for t in self._tabs if t.id != tab_id]

        self._rebuild_mappings()
        return True

    def get_tab(self, tab_id: str) -> Tab | None:
        """
        Get a tab configuration by ID.

        Args:
            tab_id: ID of tab to get

        Returns:
            Tab configuration or None if not found
        """
        for tab in self._tabs:
            if tab.id == tab_id:
                return tab
        return None

    def get_current_tab_id(self) -> str | None:
        """
        Get the ID of the currently selected tab.

        Returns:
            Tab ID or None if no tab selected
        """
        index = self.currentIndex()
        return self._index_to_tab_id.get(index)

    def set_current_tab(self, tab_id: str) -> bool:
        """
        Set the current tab by ID.

        Args:
            tab_id: ID of tab to select

        Returns:
            True if tab was selected, False if not found
        """
        if tab_id not in self._tab_id_to_index:
            return False

        index = self._tab_id_to_index[tab_id]
        self.setCurrentIndex(index)
        return True

    def set_position(self, position: TabPosition) -> None:
        """
        Update tab bar position.

        Args:
            position: New position: top, bottom, left, right
        """
        if self._position != position:
            self._position = position
            self._apply_styles()
            logger.debug(f"{self.__class__.__name__} position changed to: {position}")

    def get_position(self) -> TabPosition:
        """Get current tab bar position."""
        return self._position

    def set_draggable(self, draggable: bool) -> None:
        """
        Update draggable state.

        Args:
            draggable: Whether tabs can be dragged
        """
        if self._draggable != draggable:
            self._draggable = draggable
            self.setMovable(draggable)
            logger.debug(f"{self.__class__.__name__} draggable changed to: {draggable}")

    def get_draggable(self) -> bool:
        """Get draggable state."""
        return self._draggable

    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return len(self._tabs)

    def get_tab_ids(self) -> list[str]:
        """Get list of all tab IDs."""
        return [tab.id for tab in self._tabs]


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_tab(
    tab_id: str,
    title: str,
    content: QWidget | None = None,
    icon_name: str | None = None,
    closable: bool = False,
) -> Tab:
    """
    Convenience function to create a Tab.

    Args:
        tab_id: Unique identifier for the tab
        title: Display text
        content: Content widget (required for TabWidget, optional for TabBar)
        icon_name: Icon name from icons_v2 (e.g., "home", "settings")
        closable: Whether tab is closable

    Returns:
        Configured Tab instance

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives import create_tab

        tab = create_tab("dashboard", "Dashboard", icon_name="layout", closable=False)
    """
    icon = get_icon(icon_name, size=16) if icon_name else None
    # Tab requires content, but TabBar ignores it
    if content is None:
        from PySide6.QtWidgets import QWidget

        content = QWidget()
    return Tab(id=tab_id, title=title, content=content, icon=icon, closable=closable)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types
    "TabPosition",
    # Dataclass
    "Tab",
    # Components
    "TabWidget",
    "TabBar",
    # Utilities
    "create_tab",
]

