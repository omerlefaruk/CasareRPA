"""
Comprehensive tests for desktop interaction nodes.

Tests the following nodes:
- ClickElementNode - left click operations
- MouseClickNode - double-click, right-click, configurable clicks
- TypeTextNode - text input into elements
- SelectFromDropdownNode - dropdown/combobox selection
- SendKeysNode - keyboard input
- CheckCheckboxNode - checkbox operations

Fixtures and classes imported from tests/nodes/desktop/conftest.py:
- MockDesktopElement: Mock UIAutomation element
- MockDesktopContext: Mock desktop resource manager
- mock_desktop_context: Fixture providing MockDesktopContext instance
- execution_context: Fixture with desktop context
- mock_element: Default mock element fixture
- mock_window: Mock window element fixture
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from casare_rpa.domain.value_objects.types import NodeStatus

# Import mock classes from conftest
try:
    from .conftest import MockDesktopElement, MockDesktopContext
except ImportError:
    import sys
    from pathlib import Path

    conftest_path = str(Path(__file__).parent / "conftest.py")
    if "conftest" not in sys.modules:
        import importlib.util

        spec = importlib.util.spec_from_file_location("conftest", conftest_path)
        conftest = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(conftest)
        sys.modules["conftest"] = conftest
    MockDesktopElement = sys.modules["conftest"].MockDesktopElement
    MockDesktopContext = sys.modules["conftest"].MockDesktopContext


class TestClickElementNode:
    """Tests for ClickElementNode - left click operations."""

    @pytest.mark.asyncio
    async def test_click_element_with_direct_element(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_click")
        node.set_input_value("element", mock_element)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
        assert mock_element._clicked is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_click_element_with_window_and_selector(
        self, execution_context, mock_window
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_click_selector")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Button"})
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_click_element_with_simulate_option(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_click_sim", config={"simulate": True})
        node.set_input_value("element", mock_element)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert mock_element._clicked is True

    @pytest.mark.asyncio
    async def test_click_element_missing_element_raises_error(
        self, execution_context
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_click_no_elem")
        with pytest.raises(ValueError, match="Must provide"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_click_element_not_found_raises_error(
        self, execution_context
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        mock_win = MockDesktopElement(name="Window", exists=True)
        mock_win.find_child = Mock(return_value=None)
        node = ClickElementNode(node_id="test_click_not_found")
        node.set_input_value("window", mock_win)
        node.set_input_value("selector", {"strategy": "name", "value": "NonExistent"})
        with pytest.raises(RuntimeError, match="Element not found"):
            await node.execute(execution_context)


class TestMouseClickNode:
    """Tests for MouseClickNode - double-click, right-click, configurable clicks."""

    @pytest.mark.asyncio
    async def test_mouse_click_double_click(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(
            node_id="test_double_click", config={"click_type": "double"}
        )
        node.set_input_value("x", 100)
        node.set_input_value("y", 200)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert result["click_type"] == "double"
        assert node.status == NodeStatus.SUCCESS
        desktop_ctx = execution_context.desktop_context
        assert len(desktop_ctx._click_calls) == 1
        assert desktop_ctx._click_calls[0]["click_type"] == "double"

    @pytest.mark.asyncio
    async def test_mouse_click_right_click(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(node_id="test_right_click", config={"button": "right"})
        node.set_input_value("x", 150)
        node.set_input_value("y", 250)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert result["button"] == "right"
        desktop_ctx = execution_context.desktop_context
        assert desktop_ctx._click_calls[0]["button"] == "right"

    @pytest.mark.asyncio
    async def test_mouse_click_triple_click(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(
            node_id="test_triple_click", config={"click_type": "triple"}
        )
        node.set_input_value("x", 200)
        node.set_input_value("y", 300)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert result["click_type"] == "triple"

    @pytest.mark.asyncio
    async def test_mouse_click_with_modifiers(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(
            node_id="test_modifier_click", config={"ctrl": True, "shift": True}
        )
        node.set_input_value("x", 100)
        node.set_input_value("y", 100)
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "ctrl" in result["modifiers"]
        assert "shift" in result["modifiers"]

    @pytest.mark.asyncio
    async def test_mouse_click_at_current_position(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(node_id="test_click_current")
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert result["x"] is None
        assert result["y"] is None


class TestTypeTextNode:
    """Tests for TypeTextNode - text input operations."""

    @pytest.mark.asyncio
    async def test_type_text_basic(self, execution_context, mock_element) -> None:
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_type")
        node.set_input_value("element", mock_element)
        node.set_input_value("text", "Hello World")
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert mock_element._typed_text == "Hello World"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_type_text_with_clear_first(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_type_clear", config={"clear_first": True})
        node.set_input_value("element", mock_element)
        node.set_input_value("text", "New Text")
        result = await node.execute(execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_type_text_empty_raises_error(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_type_empty")
        node.set_input_value("element", mock_element)
        with pytest.raises(ValueError, match="Text is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_type_text_via_window_selector(
        self, execution_context, mock_window
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_type_selector")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "InputField"})
        node.set_input_value("text", "Test Input")
        result = await node.execute(execution_context)
        assert result["success"] is True


class TestSelectFromDropdownNode:
    """Tests for SelectFromDropdownNode - dropdown selection."""

    @pytest.mark.asyncio
    async def test_select_dropdown_by_text(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import SelectFromDropdownNode

        node = SelectFromDropdownNode(node_id="test_dropdown")
        node.set_input_value("element", mock_element)
        node.set_input_value("value", "Option 2")
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
        desktop_ctx = execution_context.desktop_context
        assert len(desktop_ctx._dropdown_selections) == 1
        assert desktop_ctx._dropdown_selections[0]["value"] == "Option 2"
        assert desktop_ctx._dropdown_selections[0]["by_text"] is True

    @pytest.mark.asyncio
    async def test_select_dropdown_by_index(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import SelectFromDropdownNode

        node = SelectFromDropdownNode(
            node_id="test_dropdown_idx", config={"by_text": False}
        )
        node.set_input_value("element", mock_element)
        node.set_input_value("value", "2")
        result = await node.execute(execution_context)
        assert result["success"] is True
        desktop_ctx = execution_context.desktop_context
        assert desktop_ctx._dropdown_selections[0]["by_text"] is False

    @pytest.mark.asyncio
    async def test_select_dropdown_missing_element_raises_error(
        self, execution_context
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import SelectFromDropdownNode

        node = SelectFromDropdownNode(node_id="test_dropdown_no_elem")
        node.set_input_value("value", "Option 1")
        with pytest.raises(ValueError, match="Dropdown element is required"):
            await node.execute(execution_context)

    @pytest.mark.asyncio
    async def test_select_dropdown_missing_value_raises_error(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import SelectFromDropdownNode

        node = SelectFromDropdownNode(node_id="test_dropdown_no_val")
        node.set_input_value("element", mock_element)
        with pytest.raises(ValueError, match="Value to select is required"):
            await node.execute(execution_context)


class TestCheckCheckboxNode:
    """Tests for CheckCheckboxNode - checkbox operations."""

    @pytest.mark.asyncio
    async def test_check_checkbox(self, execution_context, mock_element) -> None:
        from casare_rpa.nodes.desktop_nodes import CheckCheckboxNode

        node = CheckCheckboxNode(node_id="test_checkbox", config={"check": True})
        node.set_input_value("element", mock_element)
        result = await node.execute(execution_context)
        assert result["success"] is True
        desktop_ctx = execution_context.desktop_context
        assert desktop_ctx._checkbox_states[id(mock_element)] is True

    @pytest.mark.asyncio
    async def test_uncheck_checkbox(self, execution_context, mock_element) -> None:
        from casare_rpa.nodes.desktop_nodes import CheckCheckboxNode

        node = CheckCheckboxNode(node_id="test_uncheck", config={"check": False})
        node.set_input_value("element", mock_element)
        result = await node.execute(execution_context)
        assert result["success"] is True
        desktop_ctx = execution_context.desktop_context
        assert desktop_ctx._checkbox_states[id(mock_element)] is False

    @pytest.mark.asyncio
    async def test_checkbox_missing_element_raises_error(
        self, execution_context
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import CheckCheckboxNode

        node = CheckCheckboxNode(node_id="test_checkbox_no_elem")
        with pytest.raises(ValueError, match="Checkbox element is required"):
            await node.execute(execution_context)


class TestSendKeysNode:
    """Tests for SendKeysNode - keyboard input operations."""

    @pytest.mark.asyncio
    async def test_send_keys_basic(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendKeysNode

        node = SendKeysNode(node_id="test_sendkeys")
        node.set_input_value("keys", "Hello")
        result = await node.execute(execution_context)
        assert result["success"] is True
        assert result["keys"] == "Hello"
        desktop_ctx = execution_context.desktop_context
        assert len(desktop_ctx._keys_sent) == 1
        assert desktop_ctx._keys_sent[0]["keys"] == "Hello"

    @pytest.mark.asyncio
    async def test_send_keys_special_keys(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendKeysNode

        node = SendKeysNode(node_id="test_special_keys")
        node.set_input_value("keys", "{Enter}{Tab}")
        result = await node.execute(execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_keys_with_clear_first(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendKeysNode

        node = SendKeysNode(node_id="test_keys_clear", config={"clear_first": True})
        node.set_input_value("keys", "NewText")
        result = await node.execute(execution_context)
        assert result["success"] is True
        desktop_ctx = execution_context.desktop_context
        assert len(desktop_ctx._hotkeys_sent) >= 1

    @pytest.mark.asyncio
    async def test_send_keys_empty_raises_error(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendKeysNode

        node = SendKeysNode(node_id="test_keys_empty")
        with pytest.raises(ValueError, match="Keys to send are required"):
            await node.execute(execution_context)


class TestSendHotKeyNode:
    """Tests for SendHotKeyNode - hotkey combinations."""

    @pytest.mark.asyncio
    async def test_send_hotkey_ctrl_c(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendHotKeyNode

        node = SendHotKeyNode(
            node_id="test_ctrl_c", config={"modifier": "Ctrl", "key": "c"}
        )
        result = await node.execute(execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_hotkey_from_input(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendHotKeyNode

        node = SendHotKeyNode(node_id="test_hotkey_input")
        node.set_input_value("keys", "Ctrl,V")
        result = await node.execute(execution_context)
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_send_hotkey_enter_key(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import SendHotKeyNode

        node = SendHotKeyNode(
            node_id="test_enter", config={"modifier": "none", "key": "Enter"}
        )
        result = await node.execute(execution_context)
        assert result["success"] is True


class TestExecutionResultPatternCompliance:
    """Tests verifying ExecutionResult pattern compliance."""

    @pytest.mark.asyncio
    async def test_click_node_returns_proper_structure(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_result")
        node.set_input_value("element", mock_element)
        result = await node.execute(execution_context)
        assert isinstance(result, dict)
        assert "success" in result
        assert "next_nodes" in result
        assert isinstance(result["next_nodes"], list)

    @pytest.mark.asyncio
    async def test_type_text_returns_proper_structure(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        node = TypeTextNode(node_id="test_result_type")
        node.set_input_value("element", mock_element)
        node.set_input_value("text", "Test")
        result = await node.execute(execution_context)
        assert isinstance(result, dict)
        assert "success" in result
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_dropdown_returns_proper_structure(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import SelectFromDropdownNode

        node = SelectFromDropdownNode(node_id="test_result_dropdown")
        node.set_input_value("element", mock_element)
        node.set_input_value("value", "Test")
        result = await node.execute(execution_context)
        assert isinstance(result, dict)
        assert "success" in result
        assert "next_nodes" in result


class TestNodeStatusUpdates:
    """Tests verifying proper NodeStatus updates."""

    @pytest.mark.asyncio
    async def test_click_success_sets_success_status(
        self, execution_context, mock_element
    ) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_status")
        node.set_input_value("element", mock_element)
        await node.execute(execution_context)
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_error_sets_error_status(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import ClickElementNode

        node = ClickElementNode(node_id="test_error_status")
        try:
            await node.execute(execution_context)
        except ValueError:
            pass
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_mouse_click_success_status(self, execution_context) -> None:
        from casare_rpa.nodes.desktop_nodes import MouseClickNode

        node = MouseClickNode(node_id="test_mouse_status")
        node.set_input_value("x", 100)
        node.set_input_value("y", 100)
        await node.execute(execution_context)
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_type_text_not_found_sets_error_status(
        self, execution_context
    ) -> None:
        """Test TypeTextNode sets ERROR status when element not found."""
        from casare_rpa.nodes.desktop_nodes import TypeTextNode

        mock_win = MockDesktopElement(name="Window", exists=True)
        mock_win.find_child = Mock(return_value=None)
        node = TypeTextNode(node_id="test_type_error")
        node.set_input_value("window", mock_win)
        node.set_input_value("selector", {"strategy": "name", "value": "NotFound"})
        node.set_input_value("text", "test")
        try:
            await node.execute(execution_context)
        except RuntimeError:
            pass
        assert node.status == NodeStatus.ERROR
