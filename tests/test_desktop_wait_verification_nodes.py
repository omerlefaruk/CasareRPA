"""
Unit tests for Desktop Wait & Verification Nodes

Tests WaitForElementNode, WaitForWindowNode, VerifyElementExistsNode,
VerifyElementPropertyNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    WaitForElementNode,
    WaitForWindowNode,
    VerifyElementExistsNode,
    VerifyElementPropertyNode,
)
from casare_rpa.desktop import DesktopContext, DesktopElement
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class MockDesktopElement:
    """Mock DesktopElement for testing"""
    def __init__(self, name="MockElement", enabled=True):
        self._control = Mock()
        self._control.Name = name
        self._control.ClassName = "MockClass"
        self._control.IsEnabled = enabled
        self._control.AutomationId = "mock_id"

    def exists(self):
        return True


class TestWaitForElementNode:
    """Test suite for WaitForElementNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = WaitForElementNode("wait_1", name="Wait For Element")
        assert node.node_id == "wait_1"
        assert node.name == "Wait For Element"
        assert node.node_type == "WaitForElementNode"

    def test_default_config(self):
        """Test default configuration"""
        node = WaitForElementNode("wait_2")
        assert node.config.get("timeout") == 10.0
        assert node.config.get("state") == "visible"
        assert node.config.get("poll_interval") == 0.5

    @pytest.mark.asyncio
    async def test_missing_selector_raises_error(self):
        """Test that missing selector raises ValueError"""
        node = WaitForElementNode("wait_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Element selector is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = WaitForElementNode("wait_4")
        context = ExecutionContext()

        node.set_input_value("selector", {"name": "Test"})

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_wait_for_visible_element_success(self):
        """Test waiting for visible element success"""
        node = WaitForElementNode("wait_5", config={"state": "visible"})
        context = ExecutionContext()

        node.set_input_value("selector", {"name": "TestElement"})
        node.set_input_value("timeout", 5.0)

        mock_element = MockDesktopElement()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.wait_for_element.return_value = mock_element
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['element'] == mock_element
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.wait_for_element.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(self):
        """Test waiting for element timeout"""
        node = WaitForElementNode("wait_6", config={"state": "visible"})
        context = ExecutionContext()

        node.set_input_value("selector", {"name": "Missing"})
        node.set_input_value("timeout", 1.0)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.wait_for_element.side_effect = TimeoutError("Element not found")
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is False
        assert 'error' in result
        assert node.status == NodeStatus.ERROR


class TestWaitForWindowNode:
    """Test suite for WaitForWindowNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = WaitForWindowNode("win_wait_1", name="Wait For Window")
        assert node.node_id == "win_wait_1"
        assert node.name == "Wait For Window"
        assert node.node_type == "WaitForWindowNode"

    def test_default_config(self):
        """Test default configuration"""
        node = WaitForWindowNode("win_wait_2")
        assert node.config.get("timeout") == 10.0
        assert node.config.get("state") == "visible"

    @pytest.mark.asyncio
    async def test_missing_search_criteria_raises_error(self):
        """Test that missing search criteria raises ValueError"""
        node = WaitForWindowNode("win_wait_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Must provide at least one"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_wait_for_window_by_title(self):
        """Test waiting for window by title"""
        node = WaitForWindowNode("win_wait_4")
        context = ExecutionContext()

        node.set_input_value("title", "Calculator")
        node.set_input_value("timeout", 5.0)

        mock_window = Mock()
        mock_window.Name = "Calculator"
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.wait_for_window.return_value = mock_window
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['window'] == mock_window
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_wait_for_window_timeout(self):
        """Test waiting for window timeout"""
        node = WaitForWindowNode("win_wait_5")
        context = ExecutionContext()

        node.set_input_value("title", "NonExistent")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.wait_for_window.side_effect = TimeoutError("Window not found")
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is False
        assert node.status == NodeStatus.ERROR


class TestVerifyElementExistsNode:
    """Test suite for VerifyElementExistsNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = VerifyElementExistsNode("verify_1", name="Verify Element Exists")
        assert node.node_id == "verify_1"
        assert node.name == "Verify Element Exists"
        assert node.node_type == "VerifyElementExistsNode"

    def test_default_config(self):
        """Test default configuration"""
        node = VerifyElementExistsNode("verify_2")
        assert node.config.get("timeout") == 0.0

    @pytest.mark.asyncio
    async def test_missing_selector_raises_error(self):
        """Test that missing selector raises ValueError"""
        node = VerifyElementExistsNode("verify_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Element selector is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_element_exists_true(self):
        """Test verifying element exists returns True"""
        node = VerifyElementExistsNode("verify_4")
        context = ExecutionContext()

        node.set_input_value("selector", {"name": "ExistingElement"})

        mock_element = MockDesktopElement()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.element_exists.return_value = True
        mock_desktop_ctx.wait_for_element.return_value = mock_element
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['exists'] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_element_exists_false(self):
        """Test verifying element exists returns False"""
        node = VerifyElementExistsNode("verify_5")
        context = ExecutionContext()

        node.set_input_value("selector", {"name": "MissingElement"})

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.element_exists.return_value = False
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['exists'] is False
        assert node.status == NodeStatus.SUCCESS


class TestVerifyElementPropertyNode:
    """Test suite for VerifyElementPropertyNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = VerifyElementPropertyNode("prop_1", name="Verify Element Property")
        assert node.node_id == "prop_1"
        assert node.name == "Verify Element Property"
        assert node.node_type == "VerifyElementPropertyNode"

    def test_default_config(self):
        """Test default configuration"""
        node = VerifyElementPropertyNode("prop_2")
        assert node.config.get("comparison") == "equals"

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = VerifyElementPropertyNode("prop_3")
        context = ExecutionContext()

        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_missing_property_name_raises_error(self):
        """Test that missing property name raises ValueError"""
        node = VerifyElementPropertyNode("prop_4")
        context = ExecutionContext()

        mock_element = MockDesktopElement()
        node.set_input_value("element", mock_element)
        node.set_input_value("expected_value", "Test")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Property name is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_verify_property_equals_success(self):
        """Test verifying property equals expected value"""
        node = VerifyElementPropertyNode("prop_5", config={"comparison": "equals"})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TestButton")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "TestButton")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.verify_element_property.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['result'] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_verify_property_equals_failure(self):
        """Test verifying property does not equal expected value"""
        node = VerifyElementPropertyNode("prop_6", config={"comparison": "equals"})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TestButton")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "OtherButton")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.verify_element_property.return_value = False
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['result'] is False
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_verify_property_contains(self):
        """Test verifying property contains expected value"""
        node = VerifyElementPropertyNode("prop_7", config={"comparison": "contains"})
        context = ExecutionContext()

        mock_element = MockDesktopElement("Test Button Label")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Button")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.verify_element_property.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['result'] is True

    @pytest.mark.asyncio
    async def test_verify_property_startswith(self):
        """Test verifying property starts with expected value"""
        node = VerifyElementPropertyNode("prop_8", config={"comparison": "startswith"})
        context = ExecutionContext()

        mock_element = MockDesktopElement("TestButton")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.verify_element_property.return_value = True
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['result'] is True
