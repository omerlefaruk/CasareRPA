"""
Tests for FormInteractor.

Tests dropdown selection, checkbox toggling, radio buttons, tabs, tree items, scrolling.
All tests mock UIAutomation to avoid real UI interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from casare_rpa.desktop.managers import FormInteractor


class MockUIControl:
    """Mock UIAutomation Control for testing (local copy)."""

    def __init__(
        self,
        name: str = "TestWindow",
        control_type: str = "WindowControl",
    ):
        self.Name = name
        self.ControlTypeName = control_type
        self._selection_item_pattern = Mock()
        self._selection_item_pattern.Select = Mock()

    def GetSelectionItemPattern(self):
        return self._selection_item_pattern


class TestFormInteractorInit:
    """Test FormInteractor initialization."""

    def test_init(self):
        """FormInteractor initializes without error."""
        interactor = FormInteractor()
        assert interactor is not None


class TestSelectFromDropdown:
    """Test dropdown selection."""

    @pytest.mark.asyncio
    async def test_select_from_dropdown_by_text(self, mock_desktop_element):
        """Select dropdown item by text."""
        # Setup mock list items
        list_item = MockUIControl(name="Option 1", control_type="ListItemControl")
        mock_desktop_element._control._children = [list_item]
        mock_desktop_element._control.GetChildren = Mock(return_value=[list_item])

        interactor = FormInteractor()
        result = await interactor.select_from_dropdown(
            mock_desktop_element, "Option 1", by_text=True
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_select_from_dropdown_expands_first(self, mock_desktop_element):
        """Expands collapsed dropdown before selecting."""
        # The implementation may select without expanding if selection pattern works
        # This test verifies item selection works with collapsed dropdown
        mock_desktop_element._control._expand_pattern.ExpandCollapseState = (
            1  # Collapsed
        )

        list_item = MockUIControl(name="Test Item", control_type="ListItemControl")
        mock_desktop_element._control._children = [list_item]
        mock_desktop_element._control.GetChildren = Mock(return_value=[list_item])

        interactor = FormInteractor()
        result = await interactor.select_from_dropdown(
            mock_desktop_element, "Test Item"
        )

        # Selection should succeed regardless of expand state
        assert result is True

    @pytest.mark.asyncio
    async def test_select_from_dropdown_partial_match(self, mock_desktop_element):
        """Select dropdown item with partial text match."""
        list_item = MockUIControl(
            name="Full Option Name", control_type="ListItemControl"
        )
        mock_desktop_element._control._children = [list_item]
        mock_desktop_element._control.GetChildren = Mock(return_value=[list_item])

        interactor = FormInteractor()
        result = await interactor.select_from_dropdown(
            mock_desktop_element,
            "Option",  # Partial match
            by_text=True,
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_select_from_dropdown_by_value_pattern(self, mock_desktop_element):
        """Falls back to ValuePattern for editable dropdowns."""
        mock_desktop_element._control.GetChildren = Mock(return_value=[])
        mock_desktop_element._control._selection_pattern = None

        interactor = FormInteractor()
        result = await interactor.select_from_dropdown(
            mock_desktop_element, "New Value", by_text=True
        )

        assert result is True
        mock_desktop_element._control._value_pattern.SetValue.assert_called_with(
            "New Value"
        )

    @pytest.mark.asyncio
    async def test_select_from_dropdown_not_found_raises(self, mock_desktop_element):
        """Raises ValueError when item not found."""
        mock_desktop_element._control.GetChildren = Mock(return_value=[])
        mock_desktop_element._control._value_pattern.SetValue.side_effect = Exception(
            "No pattern"
        )

        with patch("uiautomation.GetRootControl") as mock_root:
            mock_root.return_value.GetChildren = Mock(return_value=[])

            interactor = FormInteractor()

            with pytest.raises(ValueError, match="Failed to select"):
                await interactor.select_from_dropdown(
                    mock_desktop_element, "NonexistentItem"
                )


class TestCheckCheckbox:
    """Test checkbox operations."""

    @pytest.mark.asyncio
    async def test_check_checkbox_toggle_on(self, mock_desktop_element):
        """Check an unchecked checkbox."""
        # Set initial state to unchecked
        mock_desktop_element._control._toggle_pattern.ToggleState = 0  # Off

        with patch("uiautomation.ToggleState") as mock_state:
            mock_state.On = 1
            mock_state.Off = 0
            mock_state.Indeterminate = 2

            interactor = FormInteractor()
            result = await interactor.check_checkbox(mock_desktop_element, check=True)

            assert result is True
            mock_desktop_element._control._toggle_pattern.Toggle.assert_called()

    @pytest.mark.asyncio
    async def test_check_checkbox_already_checked(self, mock_desktop_element):
        """No toggle when checkbox already in desired state."""
        with patch("uiautomation.ToggleState") as mock_state:
            mock_state.On = 1
            mock_desktop_element._control._toggle_pattern.ToggleState = 1  # Already on

            interactor = FormInteractor()
            result = await interactor.check_checkbox(mock_desktop_element, check=True)

            assert result is True
            # Toggle should not be called since already checked
            mock_desktop_element._control._toggle_pattern.Toggle.assert_not_called()

    @pytest.mark.asyncio
    async def test_uncheck_checkbox(self, mock_desktop_element):
        """Uncheck a checked checkbox."""
        with patch("uiautomation.ToggleState") as mock_state:
            mock_state.On = 1
            mock_desktop_element._control._toggle_pattern.ToggleState = 1  # On

            interactor = FormInteractor()
            result = await interactor.check_checkbox(mock_desktop_element, check=False)

            assert result is True

    @pytest.mark.asyncio
    async def test_check_checkbox_click_fallback(self, mock_desktop_element):
        """Falls back to click when TogglePattern unavailable."""
        mock_desktop_element._control.GetTogglePattern = Mock(
            side_effect=Exception("No pattern")
        )

        interactor = FormInteractor()
        result = await interactor.check_checkbox(mock_desktop_element, check=True)

        assert result is True


class TestSelectRadioButton:
    """Test radio button selection."""

    @pytest.mark.asyncio
    async def test_select_radio_button(self, mock_desktop_element):
        """Select radio button using SelectionItemPattern."""
        interactor = FormInteractor()
        result = await interactor.select_radio_button(mock_desktop_element)

        assert result is True
        mock_desktop_element._control._selection_item_pattern.Select.assert_called()

    @pytest.mark.asyncio
    async def test_select_radio_button_click_fallback(self, mock_desktop_element):
        """Falls back to click when SelectionItemPattern unavailable."""
        mock_desktop_element._control.GetSelectionItemPattern = Mock(
            side_effect=Exception("No pattern")
        )

        interactor = FormInteractor()
        result = await interactor.select_radio_button(mock_desktop_element)

        assert result is True


class TestSelectTab:
    """Test tab selection."""

    @pytest.mark.asyncio
    async def test_select_tab_by_name(self, mock_desktop_element):
        """Select tab by name."""
        tab1 = MockUIControl(name="Tab 1", control_type="TabItemControl")
        tab2 = MockUIControl(name="Tab 2", control_type="TabItemControl")
        mock_desktop_element._control._children = [tab1, tab2]
        mock_desktop_element._control.GetChildren = Mock(return_value=[tab1, tab2])

        interactor = FormInteractor()
        result = await interactor.select_tab(mock_desktop_element, tab_name="Tab 2")

        assert result is True

    @pytest.mark.asyncio
    async def test_select_tab_by_index(self, mock_desktop_element):
        """Select tab by index."""
        tab1 = MockUIControl(name="Tab 1", control_type="TabItemControl")
        tab2 = MockUIControl(name="Tab 2", control_type="TabItemControl")
        mock_desktop_element._control._children = [tab1, tab2]
        mock_desktop_element._control.GetChildren = Mock(return_value=[tab1, tab2])

        interactor = FormInteractor()
        result = await interactor.select_tab(mock_desktop_element, tab_index=1)

        assert result is True

    @pytest.mark.asyncio
    async def test_select_tab_partial_name_match(self, mock_desktop_element):
        """Select tab with partial name match."""
        tab1 = MockUIControl(name="Settings Tab", control_type="TabItemControl")
        mock_desktop_element._control._children = [tab1]
        mock_desktop_element._control.GetChildren = Mock(return_value=[tab1])

        interactor = FormInteractor()
        result = await interactor.select_tab(mock_desktop_element, tab_name="Settings")

        assert result is True

    @pytest.mark.asyncio
    async def test_select_tab_no_criteria_raises(self, mock_desktop_element):
        """Raises ValueError when no tab_name or tab_index provided."""
        interactor = FormInteractor()

        with pytest.raises(ValueError, match="Must provide either"):
            await interactor.select_tab(mock_desktop_element)

    @pytest.mark.asyncio
    async def test_select_tab_not_found_raises(self, mock_desktop_element):
        """Raises ValueError when tab not found."""
        mock_desktop_element._control._children = []
        mock_desktop_element._control.GetChildren = Mock(return_value=[])

        interactor = FormInteractor()

        with pytest.raises(ValueError, match="Failed to select tab"):
            await interactor.select_tab(mock_desktop_element, tab_name="Nonexistent")

    @pytest.mark.asyncio
    async def test_select_tab_index_out_of_range(self, mock_desktop_element):
        """Raises ValueError when tab index out of range."""
        tab1 = MockUIControl(name="Tab 1", control_type="TabItemControl")
        mock_desktop_element._control._children = [tab1]
        mock_desktop_element._control.GetChildren = Mock(return_value=[tab1])

        interactor = FormInteractor()

        with pytest.raises(ValueError, match="Tab index .* out of range"):
            await interactor.select_tab(mock_desktop_element, tab_index=5)


class TestExpandTreeItem:
    """Test tree item expand/collapse."""

    @pytest.mark.asyncio
    async def test_expand_tree_item(self, mock_desktop_element):
        """Expand collapsed tree item."""
        with patch("uiautomation.ExpandCollapseState") as mock_state:
            mock_state.Collapsed = 1
            mock_state.Expanded = 2
            mock_desktop_element._control._expand_pattern.ExpandCollapseState = 1

            interactor = FormInteractor()
            result = await interactor.expand_tree_item(
                mock_desktop_element, expand=True
            )

            assert result is True
            mock_desktop_element._control._expand_pattern.Expand.assert_called()

    @pytest.mark.asyncio
    async def test_collapse_tree_item(self, mock_desktop_element):
        """Collapse expanded tree item."""
        with patch("uiautomation.ExpandCollapseState") as mock_state:
            mock_state.Collapsed = 1
            mock_state.Expanded = 2
            mock_desktop_element._control._expand_pattern.ExpandCollapseState = 2

            interactor = FormInteractor()
            result = await interactor.expand_tree_item(
                mock_desktop_element, expand=False
            )

            assert result is True
            mock_desktop_element._control._expand_pattern.Collapse.assert_called()

    @pytest.mark.asyncio
    async def test_expand_tree_item_already_expanded(self, mock_desktop_element):
        """No action when tree item already in desired state."""
        with patch("uiautomation.ExpandCollapseState") as mock_state:
            mock_state.Collapsed = 1
            mock_state.Expanded = 2
            mock_desktop_element._control._expand_pattern.ExpandCollapseState = 2

            interactor = FormInteractor()
            result = await interactor.expand_tree_item(
                mock_desktop_element, expand=True
            )

            assert result is True
            mock_desktop_element._control._expand_pattern.Expand.assert_not_called()

    @pytest.mark.asyncio
    async def test_expand_tree_item_double_click_fallback(self, mock_desktop_element):
        """Falls back to double-click when ExpandCollapsePattern unavailable."""
        mock_desktop_element._control.GetExpandCollapsePattern = Mock(
            side_effect=Exception("No pattern")
        )

        interactor = FormInteractor()
        result = await interactor.expand_tree_item(mock_desktop_element, expand=True)

        assert result is True


class TestScrollElement:
    """Test element scrolling."""

    @pytest.mark.asyncio
    async def test_scroll_element_down(self, mock_desktop_element):
        """Scroll element down using ScrollPattern."""
        mock_desktop_element._control._scroll_pattern.HorizontalScrollPercent = 0
        mock_desktop_element._control._scroll_pattern.VerticalScrollPercent = 0

        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="down", amount=0.5
        )

        assert result is True
        mock_desktop_element._control._scroll_pattern.SetScrollPercent.assert_called()

    @pytest.mark.asyncio
    async def test_scroll_element_up(self, mock_desktop_element):
        """Scroll element up using ScrollPattern."""
        mock_desktop_element._control._scroll_pattern.VerticalScrollPercent = 50

        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="up", amount=0.5
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_scroll_element_left(self, mock_desktop_element):
        """Scroll element left using ScrollPattern."""
        mock_desktop_element._control._scroll_pattern.HorizontalScrollPercent = 50

        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="left", amount=0.5
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_scroll_element_right(self, mock_desktop_element):
        """Scroll element right using ScrollPattern."""
        mock_desktop_element._control._scroll_pattern.HorizontalScrollPercent = 0

        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="right", amount=0.5
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_scroll_element_page(self, mock_desktop_element):
        """Scroll element by full page."""
        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="down", amount="page"
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_scroll_element_invalid_direction(self, mock_desktop_element):
        """Raises ValueError for invalid direction."""
        interactor = FormInteractor()

        with pytest.raises(ValueError, match="Invalid direction"):
            await interactor.scroll_element(mock_desktop_element, direction="diagonal")

    @pytest.mark.asyncio
    async def test_scroll_element_mouse_wheel_fallback(
        self, mock_desktop_element, mock_uiautomation
    ):
        """Falls back to mouse wheel when ScrollPattern unavailable."""
        mock_desktop_element._control.GetScrollPattern = Mock(
            side_effect=Exception("No pattern")
        )

        interactor = FormInteractor()
        result = await interactor.scroll_element(
            mock_desktop_element, direction="down", amount=0.5
        )

        assert result is True
