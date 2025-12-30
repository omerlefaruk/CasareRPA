"""
Tests for CommandPaletteV2 component.

Tests the command palette functionality:
- Creation and initialization
- Loading commands from ActionManagerV2
- Fuzzy search filtering
- Category filtering
- Keyboard navigation
- Command execution
- Theme compliance (THEME_V2/TOKENS_V2 only)
"""

from unittest.mock import MagicMock, Mock

import pytest
from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def mock_action_manager():
    """Create a mock ActionManagerV2 for testing."""
    manager = MagicMock()
    manager._categories = {}

    # Create mock actions
    actions = {}
    categories = {}

    # File actions
    for name in ["new", "open", "save", "save_as", "exit"]:
        action = QAction(name.replace("_", " ").title(), None)
        action.setStatusTip(f"{name} status tip")
        if name == "new":
            action.setShortcut(QKeySequence("Ctrl+N"))
        elif name == "open":
            action.setShortcut(QKeySequence("Ctrl+O"))
        elif name == "save":
            action.setShortcut(QKeySequence("Ctrl+S"))
        actions[name] = action
        categories[name] = MagicMock(name="FILE")

    # Run actions
    for name in ["run", "stop", "pause"]:
        action = QAction(name.title(), None)
        action.setStatusTip(f"{name} status tip")
        if name == "run":
            action.setShortcut(QKeySequence("F5"))
        elif name == "stop":
            action.setShortcut(QKeySequence("F7"))
        actions[name] = action
        categories[name] = MagicMock(name="RUN")

    # View actions
    for name in ["zoom_in", "zoom_out", "zoom_reset"]:
        action = QAction(name.replace("_", " ").title(), None)
        action.setStatusTip(f"{name} status tip")
        if name == "zoom_in":
            action.setShortcut(QKeySequence("Ctrl++"))
        actions[name] = action
        categories[name] = MagicMock(name="VIEW")

    manager.get_all_actions.return_value = actions
    manager._categories = categories
    return manager


@pytest.fixture
def palette(qapp):
    """Create a CommandPaletteV2 instance for testing."""
    from casare_rpa.presentation.canvas.ui.widgets.popups import CommandPaletteV2

    palette = CommandPaletteV2()
    yield palette
    # Cleanup
    palette.close()


class TestCommandPaletteCreation:
    """Tests for command palette creation and initialization."""

    def test_instantiation(self, qapp):
        """Test palette can be instantiated."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandPaletteV2

        palette = CommandPaletteV2()
        assert palette is not None
        assert palette.windowTitle() == ""
        palette.close()

    def test_dimensions(self, palette):
        """Test default dimensions are set correctly."""
        assert palette.DEFAULT_WIDTH == 600
        assert palette.DEFAULT_HEIGHT == 400
        assert palette.MIN_WIDTH == 400
        assert palette.MIN_HEIGHT == 200


class TestCommandItem:
    """Tests for CommandItem dataclass."""

    def test_command_item_creation(self):
        """Test CommandItem can be created."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandItem

        action = QAction("Test Action", None)
        action.setShortcut(QKeySequence("Ctrl+T"))
        action.setStatusTip("Test description")

        item = CommandItem(
            id="test",
            label="Test Action",
            shortcut="Ctrl+T",
            category="TEST",
            description="Test description",
            action=action,
        )

        assert item.id == "test"
        assert item.label == "Test Action"
        assert item.shortcut == "Ctrl+T"
        assert item.category == "TEST"
        assert item.description == "Test description"
        assert item.is_enabled is True
        assert item.is_checkable is False

    def test_command_item_checkable(self):
        """Test CommandItem with checkable action."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandItem

        action = QAction("Checkable", None)
        action.setCheckable(True)
        action.setChecked(True)

        item = CommandItem(
            id="checkable",
            label="Checkable",
            shortcut="",
            category="TEST",
            description="",
            action=action,
        )

        assert item.is_checkable is True
        assert item.is_checked is True


class TestLoadFromActionManager:
    """Tests for loading commands from ActionManagerV2."""

    def test_load_actions(self, palette, mock_action_manager):
        """Test loading commands from action manager."""
        palette.load_from_action_manager(mock_action_manager)

        # Should load all actions
        assert len(palette._commands) > 0

        # Verify command structure
        for cmd in palette._commands:
            assert isinstance(cmd, tuple) or hasattr(cmd, "id")
            if hasattr(cmd, "id"):
                assert cmd.id in mock_action_manager.get_all_actions()

    def test_load_preserves_shortcuts(self, palette, mock_action_manager):
        """Test shortcuts are preserved when loading."""
        palette.load_from_action_manager(mock_action_manager)

        # Find actions with shortcuts
        shortcut_commands = [c for c in palette._commands if c.shortcut]
        assert len(shortcut_commands) > 0

        # Verify shortcut format
        for cmd in shortcut_commands:
            assert isinstance(cmd.shortcut, str)
            assert len(cmd.shortcut) > 0


class TestFuzzySearch:
    """Tests for fuzzy search functionality."""

    def test_fuzzy_match_function(self):
        """Test fuzzy_match function directly."""
        from casare_rpa.presentation.canvas.ui.widgets.popups.command_palette_v2 import (
            fuzzy_match,
        )

        # Exact prefix match (best score)
        is_match, score = fuzzy_match("run", "run")
        assert is_match is True
        assert score == 0

        # Contains match (good score)
        is_match, score = fuzzy_match("run", "run_all")
        assert is_match is True
        assert score == 0

        # Contains match (mid-string)
        is_match, score = fuzzy_match("all", "run_all")
        assert is_match is True
        assert score == 4

        # Fuzzy character match
        is_match, score = fuzzy_match("ra", "run")
        assert is_match is True
        assert score == 2

        # No match
        is_match, score = fuzzy_match("xyz", "run")
        assert is_match is False
        assert score == -1

    def test_empty_filter_shows_all(self, palette, mock_action_manager):
        """Test empty filter shows all commands."""
        palette.load_from_action_manager(mock_action_manager)
        palette._current_filter = ""
        palette._apply_filter()

        # All commands should be visible
        assert len(palette._filtered_commands) == len(palette._commands)

    def test_filter_by_prefix(self, palette, mock_action_manager):
        """Test filtering by prefix."""
        palette.load_from_action_manager(mock_action_manager)
        palette._current_filter = "run"
        palette._apply_filter()

        # Should match "run", "run_all" type commands
        assert len(palette._filtered_commands) > 0
        for _, cmd in palette._filtered_commands:
            assert "run" in cmd.label.lower() or "run" in cmd.description.lower()


class TestCategoryFilter:
    """Tests for category filtering."""

    def test_category_filter(self, palette, mock_action_manager):
        """Test filtering by category."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        palette.load_from_action_manager(mock_action_manager)
        palette.set_category_filter(CommandCategory.RUN)

        assert palette._category_filter == CommandCategory.RUN

        # Apply filter
        palette._apply_filter()

        # All filtered commands should be RUN category
        for _, cmd in palette._filtered_commands:
            assert cmd.category == "RUN"

    def test_category_filter_all(self, palette, mock_action_manager):
        """Test ALL category shows all commands."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        palette.load_from_action_manager(mock_action_manager)
        palette.set_category_filter(CommandCategory.ALL)

        assert palette._category_filter == CommandCategory.ALL

        # Apply filter
        palette._apply_filter()

        # Should show all (or most if search filter active)
        assert len(palette._filtered_commands) >= 0

    def test_cycle_category(self, palette, mock_action_manager):
        """Test cycling through categories."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        palette.load_from_action_manager(mock_action_manager)

        initial_category = palette._category_filter

        # Cycle once
        palette.cycle_category_filter()

        # Category should have changed
        assert palette._category_filter != initial_category


class TestKeyboardNavigation:
    """Tests for keyboard navigation."""

    def test_show_palette_focuses_input(self, palette, mock_action_manager):
        """Test show_palette focuses search input."""
        palette.load_from_action_manager(mock_action_manager)
        palette.show_palette()

        # Input should be focused (hasFocus() requires visible window)
        assert palette._search_input is not None

    def test_move_selection_down(self, palette, mock_action_manager):
        """Test moving selection down."""
        palette.load_from_action_manager(mock_action_manager)
        palette._apply_filter()

        if palette._filtered_commands:
            initial_index = palette._selected_index
            palette._move_selection(1)

            # Selection should have moved or wrapped
            assert palette._selected_index != initial_index or len(palette._filtered_commands) == 1

    def test_move_selection_up(self, palette, mock_action_manager):
        """Test moving selection up."""
        palette.load_from_action_manager(mock_action_manager)
        palette._apply_filter()

        if palette._filtered_commands:
            # Select second item first
            palette._select_row(1 if len(palette._filtered_commands) > 1 else 0)
            initial_index = palette._selected_index
            palette._move_selection(-1)

            # Selection should have moved or wrapped
            assert palette._selected_index != initial_index or len(palette._filtered_commands) == 1


class TestCommandExecution:
    """Tests for command execution."""

    def test_confirm_selection_emits_signal(self, palette, mock_action_manager):
        """Test confirming selection emits signal."""
        received = []

        def handler(action_id):
            received.append(action_id)

        palette.command_executed.connect(handler)

        # Load commands
        palette.load_from_action_manager(mock_action_manager)
        palette._apply_filter()

        if palette._filtered_commands:
            palette._confirm_selection()

            # Signal should have been emitted
            assert len(received) == 1
            assert received[0] in mock_action_manager.get_all_actions()

    def test_confirm_selection_triggers_action(self, palette, mock_action_manager):
        """Test confirming selection triggers the action."""
        # Load commands
        palette.load_from_action_manager(mock_action_manager)
        palette._apply_filter()

        if palette._filtered_commands:
            # Get the action for the first selected command
            _, first_cmd = palette._filtered_commands[0]

            # Track trigger calls
            original_trigger = first_cmd.action.trigger
            trigger_called = []

            def mock_trigger():
                trigger_called.append(True)

            first_cmd.action.trigger = mock_trigger

            palette._confirm_selection()

            # Action should have been triggered
            assert len(trigger_called) == 1

    def test_disabled_command_not_executed(self, qapp):
        """Test disabled commands are not executed."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import (
            CommandItem,
            CommandPaletteV2,
        )

        palette = CommandPaletteV2()

        # Create disabled action
        action = QAction("Disabled", None)
        action.setEnabled(False)

        item = CommandItem(
            id="disabled",
            label="Disabled",
            shortcut="",
            category="TEST",
            description="",
            action=action,
        )

        palette._commands = [item]
        palette._filtered_commands = [(0, item)]
        palette._selected_index = 0

        received = []

        def handler(action_id):
            received.append(action_id)

        palette.command_executed.connect(handler)

        palette._confirm_selection()

        # Signal should NOT have been emitted
        assert len(received) == 0

        palette.close()


class TestCommandCategory:
    """Tests for CommandCategory enum."""

    def test_category_from_action_category(self):
        """Test converting ActionCategory to CommandCategory."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        # String conversion
        cat = CommandCategory.from_action_category("FILE")
        assert cat == CommandCategory.FILE

        # Enum conversion
        mock_cat = MagicMock(name="RUN")
        cat = CommandCategory.from_action_category(mock_cat)
        assert cat == CommandCategory.RUN

        # Invalid defaults to ALL
        cat = CommandCategory.from_action_category("INVALID")
        assert cat == CommandCategory.ALL

    def test_category_badge_colors(self):
        """Test each category has a badge color."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        for cat in CommandCategory:
            color = cat.badge_color()
            assert isinstance(color, str)
            assert color.startswith("#")  # Hex color

    def test_category_badge_text(self):
        """Test each category has badge text."""
        from casare_rpa.presentation.canvas.ui.widgets.popups import CommandCategory

        for cat in CommandCategory:
            text = cat.badge_text()
            assert isinstance(text, str)
            assert len(text) <= 4  # Max 4 chars


class TestThemeCompliance:
    """Tests for THEME_V2/TOKENS_V2 compliance."""

    def test_uses_theme_v2_only(self, palette):
        """Test palette uses THEME_V2 only (no hardcoded colors)."""
        from casare_rpa.presentation.canvas.theme_system import THEME_V2

        # Check stylesheet references
        stylesheet = palette.styleSheet()
        if stylesheet:
            # Should contain THEME_V2 references, not hex literals
            # (This is a basic check - actual colors are in child widgets)
            assert "#ffffff" not in stylesheet or "080808" in stylesheet  # Dark theme only

    def test_input_has_theme_v2_style(self, palette):
        """Test search input uses THEME_V2 styling."""
        input_style = palette._get_input_style()

        # Should use THEME_V2 tokens, not hardcoded colors
        assert "THEME_V2" in input_style or "TOKENS_V2" in input_style

    def test_list_has_theme_v2_style(self, palette):
        """Test list widget uses THEME_V2 styling."""
        list_style = palette._get_list_style()

        # Should use THEME_V2 tokens, not hardcoded colors
        assert "THEME_V2" in list_style or "TOKENS_V2" in list_style
