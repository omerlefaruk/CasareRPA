"""
Comprehensive tests for desktop wait and verification nodes.

Tests WaitForElementNode, WaitForWindowNode, VerifyElementExistsNode,
VerifyElementPropertyNode from CasareRPA desktop automation layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from casare_rpa.core.types import NodeStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_element():
    """Create a mock desktop element."""
    element = Mock()
    element.get_text = Mock(return_value="Test Element")
    element.get_property = Mock(return_value="test_value")
    element.is_enabled = Mock(return_value=True)
    element.is_visible = Mock(return_value=True)
    element._control = Mock()
    element._control.Name = "TestElement"
    element._control.ClassName = "Button"
    element._control.IsEnabled = True
    return element


@pytest.fixture
def mock_window():
    """Create a mock window element."""
    window = Mock()
    window.get_text = Mock(return_value="Test Window")
    window.is_visible = Mock(return_value=True)
    return window


@pytest.fixture
def mock_desktop_context(mock_element, mock_window):
    """Create mock desktop context for wait/verification operations."""
    ctx = Mock()
    ctx.async_wait_for_element = AsyncMock(return_value=mock_element)
    ctx.async_wait_for_window = AsyncMock(return_value=mock_window)
    ctx.element_exists = Mock(return_value=True)
    ctx.verify_element_property = Mock(return_value=True)
    return ctx


@pytest.fixture
def mock_execution_context(mock_desktop_context):
    """Create execution context with desktop context attached."""
    context = Mock()
    context.variables = {}
    context.resolve_value = lambda x: x
    context.desktop_context = mock_desktop_context
    return context


@pytest.fixture
def sample_selector():
    """Create a sample element selector."""
    return {"strategy": "automation_id", "value": "btn_ok"}


# =============================================================================
# WaitForElementNode Tests
# =============================================================================


class TestWaitForElementNode:
    """Tests for WaitForElementNode - element state waiting."""

    @pytest.mark.asyncio
    async def test_wait_for_element_visible_success(
        self, mock_execution_context, sample_selector, mock_element
    ):
        """Test waiting for element to become visible."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(node_id="test_wait_visible")
        node.set_input_value("selector", sample_selector)
        node.set_input_value("timeout", 5.0)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["element"] == mock_element
        assert result["state"] == "visible"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_wait_for_element_hidden(
        self, mock_execution_context, sample_selector
    ):
        """Test waiting for element to become hidden."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(
            node_id="test_wait_hidden", config={"state": "hidden"}
        )
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["state"] == "hidden"

    @pytest.mark.asyncio
    async def test_wait_for_element_enabled(
        self, mock_execution_context, sample_selector
    ):
        """Test waiting for element to become enabled."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(
            node_id="test_wait_enabled", config={"state": "enabled"}
        )
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["state"] == "enabled"

    @pytest.mark.asyncio
    async def test_wait_for_element_timeout(
        self, mock_execution_context, sample_selector
    ):
        """Test wait timeout returns success=False."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        mock_execution_context.desktop_context.async_wait_for_element.side_effect = (
            TimeoutError("Element not found within timeout")
        )

        node = WaitForElementNode(node_id="test_timeout")
        node.set_input_value("selector", sample_selector)
        node.set_input_value("timeout", 0.1)

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_wait_for_element_missing_selector(self, mock_execution_context):
        """Test error when selector is missing."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(node_id="test_missing_selector")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "selector" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_wait_for_element_no_desktop_context(self, sample_selector):
        """Test error when desktop context not available."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        context = Mock()
        context.desktop_context = None

        node = WaitForElementNode(node_id="test_no_context")
        node.set_input_value("selector", sample_selector)

        with pytest.raises(ValueError) as exc_info:
            await node.execute(context)

        assert "Desktop context not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_element_custom_poll_interval(
        self, mock_execution_context, sample_selector
    ):
        """Test wait with custom poll interval configuration."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(
            node_id="test_poll", config={"poll_interval": 0.25, "timeout": 5.0}
        )
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_kwargs = (
            mock_execution_context.desktop_context.async_wait_for_element.call_args
        )
        assert call_kwargs[1]["poll_interval"] == 0.25


# =============================================================================
# WaitForWindowNode Tests
# =============================================================================


class TestWaitForWindowNode:
    """Tests for WaitForWindowNode - window state waiting."""

    @pytest.mark.asyncio
    async def test_wait_for_window_by_title(self, mock_execution_context, mock_window):
        """Test waiting for window by title."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_wait_title")
        node.set_input_value("title", "Test Window")
        node.set_input_value("timeout", 5.0)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["window"] == mock_window
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_wait_for_window_by_regex(self, mock_execution_context, mock_window):
        """Test waiting for window by title regex."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_wait_regex")
        node.set_input_value("title_regex", r"Test.*Window")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_kwargs = (
            mock_execution_context.desktop_context.async_wait_for_window.call_args
        )
        assert call_kwargs[1]["title_regex"] == r"Test.*Window"

    @pytest.mark.asyncio
    async def test_wait_for_window_by_class(self, mock_execution_context, mock_window):
        """Test waiting for window by class name."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_wait_class")
        node.set_input_value("class_name", "Notepad")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_kwargs = (
            mock_execution_context.desktop_context.async_wait_for_window.call_args
        )
        assert call_kwargs[1]["class_name"] == "Notepad"

    @pytest.mark.asyncio
    async def test_wait_for_window_timeout(self, mock_execution_context):
        """Test window wait timeout."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        mock_execution_context.desktop_context.async_wait_for_window.side_effect = (
            TimeoutError("Window not found")
        )

        node = WaitForWindowNode(node_id="test_timeout")
        node.set_input_value("title", "NonExistent")
        node.set_input_value("timeout", 0.1)

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert "error" in result
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_wait_for_window_no_criteria(self, mock_execution_context):
        """Test error when no search criteria provided."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_no_criteria")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Must provide at least one of" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_wait_for_window_hidden_state(self, mock_execution_context):
        """Test waiting for window to become hidden."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_hidden", config={"state": "hidden"})
        node.set_input_value("title", "Closing Window")

        result = await node.execute(mock_execution_context)

        assert result["state"] == "hidden"


# =============================================================================
# VerifyElementExistsNode Tests
# =============================================================================


class TestVerifyElementExistsNode:
    """Tests for VerifyElementExistsNode - element existence verification."""

    @pytest.mark.asyncio
    async def test_verify_element_exists_true(
        self, mock_execution_context, sample_selector, mock_element
    ):
        """Test verifying element exists returns True."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        node = VerifyElementExistsNode(node_id="test_exists_true")
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["exists"] is True
        assert result["element"] is not None
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_verify_element_exists_false(
        self, mock_execution_context, sample_selector
    ):
        """Test verifying element exists returns False."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        mock_execution_context.desktop_context.element_exists.return_value = False

        node = VerifyElementExistsNode(node_id="test_exists_false")
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["exists"] is False
        assert result["element"] is None

    @pytest.mark.asyncio
    async def test_verify_element_with_timeout(
        self, mock_execution_context, sample_selector
    ):
        """Test element verification with search timeout."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        node = VerifyElementExistsNode(node_id="test_timeout", config={"timeout": 2.0})
        node.set_input_value("selector", sample_selector)
        node.set_input_value("timeout", 3.0)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.element_exists.assert_called_once()
        call_kwargs = mock_execution_context.desktop_context.element_exists.call_args
        assert call_kwargs[1]["timeout"] == 3.0

    @pytest.mark.asyncio
    async def test_verify_element_missing_selector(self, mock_execution_context):
        """Test error when selector is missing."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        node = VerifyElementExistsNode(node_id="test_missing")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "selector" in str(exc_info.value).lower()


# =============================================================================
# VerifyElementPropertyNode Tests
# =============================================================================


class TestVerifyElementPropertyNode:
    """Tests for VerifyElementPropertyNode - element property verification."""

    @pytest.mark.asyncio
    async def test_verify_property_equals_success(
        self, mock_execution_context, mock_element
    ):
        """Test verifying property equals expected value."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(node_id="test_equals")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "TestElement")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["result"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_verify_property_contains(self, mock_execution_context, mock_element):
        """Test verifying property contains expected substring."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(
            node_id="test_contains", config={"comparison": "contains"}
        )
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["comparison"] == "contains"
        mock_execution_context.desktop_context.verify_element_property.assert_called_with(
            element=mock_element,
            property_name="Name",
            expected_value="Test",
            comparison="contains",
        )

    @pytest.mark.asyncio
    async def test_verify_property_failure(self, mock_execution_context, mock_element):
        """Test property verification failure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        mock_execution_context.desktop_context.verify_element_property.return_value = (
            False
        )

        node = VerifyElementPropertyNode(node_id="test_failure")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "WrongValue")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True  # Node executed
        assert result["result"] is False  # Verification failed
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_verify_property_missing_element(self, mock_execution_context):
        """Test error when element is missing."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(node_id="test_missing_element")
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Element is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_property_missing_property_name(
        self, mock_execution_context, mock_element
    ):
        """Test error when property_name is missing."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(node_id="test_missing_prop")
        node.set_input_value("element", mock_element)
        node.set_input_value("expected_value", "Test")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Property name is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_property_actual_value_output(
        self, mock_execution_context, mock_element
    ):
        """Test actual value is included in output."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(node_id="test_actual")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "TestElement")

        result = await node.execute(mock_execution_context)

        assert "actual_value" in result
        assert "expected_value" in result
        assert "property_name" in result


# =============================================================================
# ExecutionResult Pattern Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Tests verifying all nodes follow ExecutionResult pattern."""

    @pytest.mark.asyncio
    async def test_wait_element_result_structure(
        self, mock_execution_context, sample_selector
    ):
        """Test WaitForElementNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForElementNode,
        )

        node = WaitForElementNode(node_id="test_result")
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "element" in result
        assert "state" in result
        assert "timeout" in result

    @pytest.mark.asyncio
    async def test_wait_window_result_structure(self, mock_execution_context):
        """Test WaitForWindowNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            WaitForWindowNode,
        )

        node = WaitForWindowNode(node_id="test_result")
        node.set_input_value("title", "Test")

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "window" in result
        assert "state" in result
        assert "timeout" in result

    @pytest.mark.asyncio
    async def test_verify_exists_result_structure(
        self, mock_execution_context, sample_selector
    ):
        """Test VerifyElementExistsNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        node = VerifyElementExistsNode(node_id="test_result")
        node.set_input_value("selector", sample_selector)

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "exists" in result
        assert "element" in result
        assert isinstance(result["exists"], bool)

    @pytest.mark.asyncio
    async def test_verify_property_result_structure(
        self, mock_execution_context, mock_element
    ):
        """Test VerifyElementPropertyNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        node = VerifyElementPropertyNode(node_id="test_result")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "result" in result
        assert "actual_value" in result
        assert "expected_value" in result
        assert "property_name" in result
        assert "comparison" in result
