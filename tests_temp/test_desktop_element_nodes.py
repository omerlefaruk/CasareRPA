"""
Unit and Integration tests for Desktop Element Interaction Nodes

Tests FindElementNode, ClickElementNode, TypeTextNode, GetElementTextNode, GetElementPropertyNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    FindElementNode,
    ClickElementNode,
    TypeTextNode,
    GetElementTextNode,
    GetElementPropertyNode,
)
from casare_rpa.desktop import DesktopContext, DesktopElement
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class TestFindElementNode:
    """Test suite for FindElementNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = FindElementNode("find_1", name="Find Element")
        assert node.node_id == "find_1"
        assert node.name == "Find Element"
        assert node.node_type == "FindElementNode"

    @pytest.mark.asyncio
    async def test_find_element_with_mock(self):
        """Test finding element with mock"""
        node = FindElementNode("find_1")
        context = ExecutionContext()

        # Create mock window and element
        mock_element = MagicMock(spec=DesktopElement)
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=mock_element)

        # Set inputs
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "TestButton"})

        # Execute
        result = await node.execute(context)

        assert result["success"] is True
        assert result["element"] == mock_element
        assert result["found"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_find_element_not_found_throw(self):
        """Test finding element that doesn't exist with throw_on_not_found=True"""
        node = FindElementNode("find_2", config={"throw_on_not_found": True})
        context = ExecutionContext()

        # Create mock window that returns None
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=None)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "NonExistent"})

        with pytest.raises(RuntimeError, match="Element not found"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_find_element_not_found_no_throw(self):
        """Test finding element that doesn't exist with throw_on_not_found=False"""
        node = FindElementNode("find_3", config={"throw_on_not_found": False})
        context = ExecutionContext()

        # Create mock window that returns None
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=None)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "NonExistent"})

        result = await node.execute(context)

        assert result["success"] is True
        assert result["element"] is None
        assert result["found"] is False
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_find_element_missing_window(self):
        """Test that missing window raises error"""
        node = FindElementNode("find_4")
        context = ExecutionContext()

        node.set_input_value("selector", {"strategy": "name", "value": "Button"})

        with pytest.raises(ValueError, match="Window is required"):
            await node.execute(context)


class TestClickElementNode:
    """Test suite for ClickElementNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = ClickElementNode("click_1", name="Click Element")
        assert node.node_id == "click_1"
        assert node.name == "Click Element"
        assert node.node_type == "ClickElementNode"

    @pytest.mark.asyncio
    async def test_click_with_element_input(self):
        """Test clicking element when element is provided directly"""
        node = ClickElementNode("click_1")
        context = ExecutionContext()

        # Create mock element
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.click = MagicMock(return_value=True)

        node.set_input_value("element", mock_element)

        result = await node.execute(context)

        assert result["success"] is True
        assert node.status == NodeStatus.SUCCESS
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_with_window_and_selector(self):
        """Test clicking element via window + selector"""
        node = ClickElementNode("click_2")
        context = ExecutionContext()

        # Create mock element and window
        mock_element = MagicMock(spec=DesktopElement)
        mock_element.click = MagicMock(return_value=True)
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=mock_element)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Button"})

        result = await node.execute(context)

        assert result["success"] is True
        mock_window.find_child.assert_called_once()
        mock_element.click.assert_called_once()

    @pytest.mark.asyncio
    async def test_click_with_offsets(self):
        """Test clicking with x/y offsets"""
        node = ClickElementNode("click_3", config={"x_offset": 10, "y_offset": 20})
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.click = MagicMock(return_value=True)

        node.set_input_value("element", mock_element)

        result = await node.execute(context)

        assert result["success"] is True
        mock_element.click.assert_called_with(simulate=False, x_offset=10, y_offset=20)

    @pytest.mark.asyncio
    async def test_click_missing_inputs(self):
        """Test that missing inputs raises error"""
        node = ClickElementNode("click_4")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Must provide"):
            await node.execute(context)


class TestTypeTextNode:
    """Test suite for TypeTextNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = TypeTextNode("type_1", name="Type Text")
        assert node.node_id == "type_1"
        assert node.name == "Type Text"
        assert node.node_type == "TypeTextNode"

    @pytest.mark.asyncio
    async def test_type_text_with_element(self):
        """Test typing text when element is provided"""
        node = TypeTextNode("type_1")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.type_text = MagicMock(return_value=True)

        node.set_input_value("element", mock_element)
        node.set_input_value("text", "Hello World")

        result = await node.execute(context)

        assert result["success"] is True
        mock_element.type_text.assert_called_once_with(
            text="Hello World",
            clear_first=False,
            interval=0.01
        )

    @pytest.mark.asyncio
    async def test_type_text_with_clear_first(self):
        """Test typing with clear_first option"""
        node = TypeTextNode("type_2", config={"clear_first": True})
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.type_text = MagicMock(return_value=True)

        node.set_input_value("element", mock_element)
        node.set_input_value("text", "New Text")

        result = await node.execute(context)

        assert result["success"] is True
        mock_element.type_text.assert_called_once_with(
            text="New Text",
            clear_first=True,
            interval=0.01
        )

    @pytest.mark.asyncio
    async def test_type_text_via_window_selector(self):
        """Test typing via window + selector"""
        node = TypeTextNode("type_3")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.type_text = MagicMock(return_value=True)
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=mock_element)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "automation_id", "value": "textbox1"})
        node.set_input_value("text", "Test")

        result = await node.execute(context)

        assert result["success"] is True
        mock_window.find_child.assert_called_once()
        mock_element.type_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_type_text_missing_text(self):
        """Test that missing text raises error"""
        node = TypeTextNode("type_4")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        node.set_input_value("element", mock_element)

        with pytest.raises(ValueError, match="Text is required"):
            await node.execute(context)


class TestGetElementTextNode:
    """Test suite for GetElementTextNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = GetElementTextNode("get_text_1", name="Get Element Text")
        assert node.node_id == "get_text_1"
        assert node.name == "Get Element Text"
        assert node.node_type == "GetElementTextNode"

    @pytest.mark.asyncio
    async def test_get_text_with_element(self):
        """Test getting text when element is provided"""
        node = GetElementTextNode("get_text_1")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_text = MagicMock(return_value="Button Text")

        node.set_input_value("element", mock_element)

        result = await node.execute(context)

        assert result["success"] is True
        assert result["text"] == "Button Text"
        assert result["element"] == mock_element
        mock_element.get_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_text_via_window_selector(self):
        """Test getting text via window + selector"""
        node = GetElementTextNode("get_text_2")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_text = MagicMock(return_value="Label Content")
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=mock_element)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "MyLabel"})

        result = await node.execute(context)

        assert result["success"] is True
        assert result["text"] == "Label Content"
        mock_window.find_child.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_text_with_variable_storage(self):
        """Test storing text in context variable"""
        node = GetElementTextNode("get_text_3", config={"variable_name": "my_text"})
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_text = MagicMock(return_value="Stored Text")

        node.set_input_value("element", mock_element)

        result = await node.execute(context)

        assert result["success"] is True
        assert context.get_variable("my_text") == "Stored Text"


class TestGetElementPropertyNode:
    """Test suite for GetElementPropertyNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = GetElementPropertyNode("get_prop_1", name="Get Element Property")
        assert node.node_id == "get_prop_1"
        assert node.name == "Get Element Property"
        assert node.node_type == "GetElementPropertyNode"

    @pytest.mark.asyncio
    async def test_get_property_with_element(self):
        """Test getting property when element is provided"""
        node = GetElementPropertyNode("get_prop_1")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property = MagicMock(return_value="MyButton")

        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")

        result = await node.execute(context)

        assert result["success"] is True
        assert result["value"] == "MyButton"
        assert result["element"] == mock_element
        mock_element.get_property.assert_called_once_with("Name")

    @pytest.mark.asyncio
    async def test_get_property_automation_id(self):
        """Test getting AutomationId property"""
        node = GetElementPropertyNode("get_prop_2")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property = MagicMock(return_value="button_123")

        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "AutomationId")

        result = await node.execute(context)

        assert result["success"] is True
        assert result["value"] == "button_123"
        mock_element.get_property.assert_called_once_with("AutomationId")

    @pytest.mark.asyncio
    async def test_get_property_via_window_selector(self):
        """Test getting property via window + selector"""
        node = GetElementPropertyNode("get_prop_3")
        context = ExecutionContext()

        mock_element = MagicMock(spec=DesktopElement)
        mock_element.get_property = MagicMock(return_value="ButtonControl")
        mock_window = MagicMock()
        mock_window.find_child = MagicMock(return_value=mock_element)

        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "SubmitBtn"})
        node.set_input_value("property_name", "ControlTypeName")

        result = await node.execute(context)

        assert result["success"] is True
        assert result["value"] == "ButtonControl"


# Integration tests with real applications
class TestDesktopElementNodesIntegration:
    """Integration tests using real Calculator application"""

    @pytest.fixture
    def calculator_window(self):
        """Fixture to launch Calculator and return its window"""
        from casare_rpa.nodes.desktop_nodes import LaunchApplicationNode

        launch_node = LaunchApplicationNode("launch")
        context = ExecutionContext()
        launch_node.set_input_value("application_path", "calc.exe")

        # Launch calculator
        result = asyncio.run(launch_node.execute(context))
        window = result['window']

        yield window

        # Cleanup
        try:
            if hasattr(context, 'desktop_context'):
                context.desktop_context.cleanup()
        except:
            pass

    @pytest.mark.asyncio
    async def test_find_calculator_button(self, calculator_window):
        """Test finding a button in Calculator"""
        node = FindElementNode("find_calc")
        context = ExecutionContext()

        node.set_input_value("window", calculator_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Seven"})

        result = await node.execute(context)

        assert result["success"] is True
        assert result["found"] is True
        assert result["element"] is not None

    @pytest.mark.asyncio
    async def test_click_calculator_button(self, calculator_window):
        """Test clicking a button in Calculator"""
        node = ClickElementNode("click_calc")
        context = ExecutionContext()

        node.set_input_value("window", calculator_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Seven"})

        result = await node.execute(context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_get_button_text(self, calculator_window):
        """Test getting text from a Calculator button"""
        node = GetElementTextNode("get_text_calc")
        context = ExecutionContext()

        node.set_input_value("window", calculator_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Seven"})

        result = await node.execute(context)

        assert result["success"] is True
        assert "Seven" in result["text"] or "7" in result["text"]

    @pytest.mark.asyncio
    async def test_get_button_property(self, calculator_window):
        """Test getting property from a Calculator button"""
        node = GetElementPropertyNode("get_prop_calc")
        context = ExecutionContext()

        node.set_input_value("window", calculator_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Seven"})
        node.set_input_value("property_name", "ControlTypeName")

        result = await node.execute(context)

        assert result["success"] is True
        assert result["value"] is not None
