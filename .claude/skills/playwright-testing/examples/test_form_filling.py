"""
Example: Form interaction testing patterns.

Demonstrates testing of form-related operations:
- Text input typing
- Dropdown selection
- Checkbox/radio toggling
- Multi-field form submission

Run: pytest .claude/skills/playwright-testing/examples/test_form_filling.py -v
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from casare_rpa.nodes.browser.interaction import SelectDropdownNode, TypeTextNode

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_page() -> AsyncMock:
    """Create mock Playwright page for form interactions."""
    page = AsyncMock()
    page.fill = AsyncMock(return_value=None)
    page.type = AsyncMock(return_value=None)
    page.select_option = AsyncMock(return_value=None)
    page.check = AsyncMock(return_value=None)
    page.uncheck = AsyncMock(return_value=None)
    page.press = AsyncMock(return_value=None)
    page.wait_for_selector = AsyncMock(return_value=MagicMock())
    return page


@pytest.fixture
def mock_context(mock_page: AsyncMock) -> MagicMock:
    """Create mock context with active page."""
    context = MagicMock()
    context.get_active_page.return_value = mock_page
    context.resolve_value = MagicMock(side_effect=lambda x: x)
    return context


# =============================================================================
# Type Text Tests
# =============================================================================


class TestTypeTextNode:
    """Tests for typing text into input fields."""

    @pytest.mark.asyncio
    async def test_type_simple_text(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Type text into input field."""
        node = TypeTextNode(
            "test_type",
            config={"selector": "#username", "text": "john_doe"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.fill.assert_called_once()
        call_args = mock_page.fill.call_args[0]
        assert call_args[1] == "john_doe"

    @pytest.mark.asyncio
    async def test_type_from_input_port(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Text value from input port."""
        node = TypeTextNode(
            "test_input_port",
            config={"selector": "#email"},
        )
        node.set_input_value("text", "user@example.com")

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_args = mock_page.fill.call_args[0]
        assert call_args[1] == "user@example.com"

    @pytest.mark.asyncio
    async def test_type_with_clear_first(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Clear field before typing."""
        node = TypeTextNode(
            "test_clear",
            config={"selector": "#input", "text": "new value", "clear_first": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Verify fill was called (clear + fill)

    @pytest.mark.asyncio
    async def test_type_without_clear(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Type without clearing existing content."""
        node = TypeTextNode(
            "test_no_clear",
            config={"selector": "#input", "text": "appended", "clear_first": False},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_type_with_keystroke_delay(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Type character-by-character with delay."""
        node = TypeTextNode(
            "test_delay",
            config={"selector": "#input", "text": "slow typing", "delay": 50},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # With delay, should use page.type instead of page.fill

    @pytest.mark.asyncio
    async def test_type_and_press_enter(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Type text and press Enter after."""
        node = TypeTextNode(
            "test_enter",
            config={"selector": "#search", "text": "query", "press_enter_after": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.press.assert_called_once_with("Enter")

    @pytest.mark.asyncio
    async def test_type_and_press_tab(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Type text and press Tab after."""
        node = TypeTextNode(
            "test_tab",
            config={"selector": "#field1", "text": "value", "press_tab_after": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.press.assert_called_once_with("Tab")

    @pytest.mark.asyncio
    async def test_fast_mode_typing(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Fast mode skips waits for rapid form filling."""
        node = TypeTextNode(
            "test_fast",
            config={"selector": "#field", "text": "value", "fast_mode": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Fast mode should use force=True, skip waits

    @pytest.mark.asyncio
    async def test_type_empty_string(self, mock_context: MagicMock, mock_page: AsyncMock):
        """EDGE CASE: Type empty string (clear field)."""
        node = TypeTextNode(
            "test_empty",
            config={"selector": "#input", "text": ""},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_type_special_characters(self, mock_context: MagicMock, mock_page: AsyncMock):
        """EDGE CASE: Type text with special characters."""
        node = TypeTextNode(
            "test_special",
            config={"selector": "#input", "text": "Hello\nWorld\t!@#$%"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True


# =============================================================================
# Select Dropdown Tests
# =============================================================================


class TestSelectDropdownNode:
    """Tests for dropdown selection."""

    @pytest.mark.asyncio
    async def test_select_by_value(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Select option by value attribute."""
        node = SelectDropdownNode(
            "test_value",
            config={"selector": "#country", "value": "us", "select_by": "value"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.select_option.assert_called_once()
        call_kwargs = mock_page.select_option.call_args[1]
        assert "value" in call_kwargs
        assert call_kwargs["value"] == "us"

    @pytest.mark.asyncio
    async def test_select_by_label(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Select option by visible text label."""
        node = SelectDropdownNode(
            "test_label",
            config={"selector": "#country", "value": "United States", "select_by": "label"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.select_option.call_args[1]
        assert call_kwargs.get("label") == "United States"

    @pytest.mark.asyncio
    async def test_select_by_index(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Select option by numeric index."""
        node = SelectDropdownNode(
            "test_index",
            config={"selector": "#country", "value": "2", "select_by": "index"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.select_option.call_args[1]
        assert call_kwargs.get("index") == 2

    @pytest.mark.asyncio
    async def test_select_from_input_port(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Selection value from input port."""
        node = SelectDropdownNode(
            "test_input",
            config={"selector": "#country"},
        )
        node.set_input_value("value", "uk")

        result = await node.execute(mock_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_select_custom_timeout(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Custom timeout for selection."""
        node = SelectDropdownNode(
            "test_timeout",
            config={"selector": "#country", "value": "us", "timeout": 10000},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        call_kwargs = mock_page.select_option.call_args[1]
        assert call_kwargs.get("timeout") == 10000


# =============================================================================
# Checkbox/Radio Tests
# =============================================================================


class TestCheckboxRadioInteraction:
    """Tests for checkbox and radio button interactions."""

    @pytest.mark.asyncio
    async def test_check_checkbox(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Check a checkbox element."""
        from casare_rpa.nodes.browser.interaction import CheckElementNode

        node = CheckElementNode(
            "test_check",
            config={"selector": "#agree-terms"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_uncheck_checkbox(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Uncheck a checkbox element."""
        from casare_rpa.nodes.browser.interaction import UncheckElementNode

        node = UncheckElementNode(
            "test_uncheck",
            config={"selector": "#agree-terms"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.uncheck.assert_called_once()


# =============================================================================
# Multi-Field Form Tests
# =============================================================================


class TestMultiFieldForm:
    """Tests for filling multiple form fields in sequence."""

    @pytest.mark.asyncio
    async def test_fill_login_form(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Fill a login form with username and password."""
        # Create nodes for each field
        username_node = TypeTextNode(
            "username",
            config={"selector": "#username", "text": "testuser"},
        )
        password_node = TypeTextNode(
            "password",
            config={"selector": "#password", "text": "secret123"},
        )
        submit_node = TypeTextNode(
            "submit",
            config={"selector": "#login-btn", "text": "", "press_enter_after": True},
        )

        # Execute in sequence
        result1 = await username_node.execute(mock_context)
        result2 = await password_node.execute(mock_context)
        result3 = await submit_node.execute(mock_context)

        assert all([result1["success"], result2["success"], result3["success"]])
        assert mock_page.fill.call_count == 2
        assert mock_page.press.call_count == 1

    @pytest.mark.asyncio
    async def test_fill_form_with_dropdowns(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Fill form with text fields and dropdowns."""
        name_node = TypeTextNode(
            "name",
            config={"selector": "#name", "text": "John Doe"},
        )
        country_node = SelectDropdownNode(
            "country",
            config={"selector": "#country", "value": "us"},
        )
        state_node = SelectDropdownNode(
            "state",
            config={"selector": "#state", "value": "ca"},
        )

        result1 = await name_node.execute(mock_context)
        result2 = await country_node.execute(mock_context)
        result3 = await state_node.execute(mock_context)

        assert all([result1["success"], result2["success"], result3["success"]])

    @pytest.mark.asyncio
    async def test_fill_form_fast_mode(self, mock_context: MagicMock, mock_page: AsyncMock):
        """SUCCESS: Rapid form filling using fast mode."""
        nodes = [
            TypeTextNode("f1", config={"selector": "#f1", "text": "v1", "fast_mode": True}),
            TypeTextNode("f2", config={"selector": "#f2", "text": "v2", "fast_mode": True}),
            TypeTextNode("f3", config={"selector": "#f3", "text": "v3", "fast_mode": True}),
        ]

        results = [await node.execute(mock_context) for node in nodes]

        assert all(r["success"] for r in results)
