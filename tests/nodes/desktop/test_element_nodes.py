"""
Comprehensive tests for desktop element automation nodes.

Tests FindElementNode, GetElementPropertyNode, VerifyElementExistsNode,
VerifyElementPropertyNode from CasareRPA desktop automation layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_execution_context():
    """Create a mock execution context with desktop context support."""
    context = Mock()
    context.variables = {}
    context.resolve_value = lambda x: x
    context.get_variable = lambda name, default=None: context.variables.get(
        name, default
    )
    context.set_variable = lambda name, value: context.variables.__setitem__(
        name, value
    )

    # Create mock desktop context
    desktop_ctx = Mock()
    desktop_ctx.element_exists = Mock(return_value=True)
    desktop_ctx.async_wait_for_element = AsyncMock(return_value=Mock())
    desktop_ctx.verify_element_property = Mock(return_value=True)

    context.desktop_context = desktop_ctx
    return context


@pytest.fixture
def mock_window():
    """Create a mock window element."""
    window = Mock()
    window.find_child = Mock()
    return window


@pytest.fixture
def mock_element():
    """Create a mock desktop element with common properties."""
    element = Mock()
    element.get_text = Mock(return_value="Test Element Text")
    element.get_property = Mock(return_value="test_value")
    element.click = Mock(return_value=True)
    element.type_text = Mock(return_value=True)
    element.exists = Mock(return_value=True)
    element.is_enabled = Mock(return_value=True)
    element.is_visible = Mock(return_value=True)

    # Mock the underlying control for property verification
    mock_control = Mock()
    mock_control.Name = "TestElement"
    mock_control.ClassName = "Button"
    mock_control.AutomationId = "btn_test"
    mock_control.IsEnabled = True
    element._control = mock_control

    return element


@pytest.fixture
def sample_selector_name():
    """Sample selector using name strategy."""
    return {"strategy": "name", "value": "OK"}


@pytest.fixture
def sample_selector_automation_id():
    """Sample selector using automation_id strategy."""
    return {"strategy": "automation_id", "value": "btnSubmit"}


@pytest.fixture
def sample_selector_class_name():
    """Sample selector using class_name strategy."""
    return {"strategy": "class_name", "value": "Button"}


@pytest.fixture
def sample_selector_control_type():
    """Sample selector using control_type strategy."""
    return {"strategy": "control_type", "value": "Button"}


# =============================================================================
# FindElementNode Tests
# =============================================================================


class TestFindElementNode:
    """Tests for FindElementNode - element discovery within windows."""

    @pytest.mark.asyncio
    async def test_find_element_success(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test successful element finding with valid window and selector."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_find_element")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "OK"})

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["found"] is True
        assert result["element"] == mock_element
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_find_element_not_found_throw(
        self, mock_execution_context, mock_window
    ):
        """Test element not found raises error when throw_on_not_found is True."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = None

        node = FindElementNode(node_id="test_find_not_found")
        node.config["throw_on_not_found"] = True
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "NonExistent"})

        with pytest.raises(RuntimeError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Element not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_element_not_found_no_throw(
        self, mock_execution_context, mock_window
    ):
        """Test element not found returns found=False when throw_on_not_found is False."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = None

        node = FindElementNode(node_id="test_find_no_throw")
        node.config["throw_on_not_found"] = False
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "NonExistent"})

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["found"] is False
        assert result["element"] is None
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_find_element_missing_window(self, mock_execution_context):
        """Test error when window input is missing."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        node = FindElementNode(node_id="test_missing_window")
        node.set_input_value("selector", {"strategy": "name", "value": "OK"})

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Window is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_element_missing_selector(
        self, mock_execution_context, mock_window
    ):
        """Test error when selector input is missing."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        node = FindElementNode(node_id="test_missing_selector")
        node.set_input_value("window", mock_window)

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Selector is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_find_element_with_timeout(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test element finding respects timeout configuration."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_timeout")
        node.config["timeout"] = 10.0
        node.set_input_value("window", mock_window)
        node.set_input_value(
            "selector", {"strategy": "automation_id", "value": "btn_test"}
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_window.find_child.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_element_selector_from_config(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test selector can be read from config when not provided as input."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_selector_config")
        node.config["selector"] = {"strategy": "class_name", "value": "Button"}
        node.set_input_value("window", mock_window)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["found"] is True


# =============================================================================
# GetElementPropertyNode Tests
# =============================================================================


class TestGetElementPropertyNode:
    """Tests for GetElementPropertyNode - reading element properties."""

    @pytest.mark.asyncio
    async def test_get_property_direct_element(
        self, mock_execution_context, mock_element
    ):
        """Test getting property from directly provided element."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        mock_element.get_property.return_value = "TestValue"

        node = GetElementPropertyNode(node_id="test_get_property")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "AutomationId")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["value"] == "TestValue"
        assert result["element"] == mock_element

    @pytest.mark.asyncio
    async def test_get_property_via_window_selector(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test getting property by finding element via window and selector."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        mock_window.find_child.return_value = mock_element
        mock_element.get_property.return_value = "Button"

        node = GetElementPropertyNode(node_id="test_get_via_selector")
        node.set_input_value("window", mock_window)
        node.set_input_value(
            "selector", {"strategy": "automation_id", "value": "btn_test"}
        )
        node.set_input_value("property_name", "ClassName")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["value"] == "Button"

    @pytest.mark.asyncio
    async def test_get_property_default_name(
        self, mock_execution_context, mock_element
    ):
        """Test default property_name is Name."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        mock_element.get_property.return_value = "ElementName"

        node = GetElementPropertyNode(node_id="test_default_name")
        node.set_input_value("element", mock_element)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_element.get_property.assert_called_with("Name")

    @pytest.mark.asyncio
    async def test_get_property_missing_element_and_window(
        self, mock_execution_context
    ):
        """Test error when neither element nor window+selector provided."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        node = GetElementPropertyNode(node_id="test_missing_element")
        node.set_input_value("property_name", "Name")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert (
            "element" in str(exc_info.value).lower()
            or "window" in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_get_property_failure(self, mock_execution_context, mock_element):
        """Test error handling when property access fails."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        mock_element.get_property.side_effect = Exception("Property access denied")

        node = GetElementPropertyNode(node_id="test_property_failure")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "InvalidProperty")

        with pytest.raises(RuntimeError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Failed to get element property" in str(exc_info.value)


# =============================================================================
# VerifyElementExistsNode Tests (ElementExistsNode equivalent)
# =============================================================================


class TestVerifyElementExistsNode:
    """Tests for VerifyElementExistsNode - checking element existence."""

    @pytest.mark.asyncio
    async def test_element_exists_positive(self, mock_execution_context, mock_element):
        """Test verifying element exists returns True when element found."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        mock_execution_context.desktop_context.element_exists.return_value = True
        mock_execution_context.desktop_context.async_wait_for_element.return_value = (
            mock_element
        )

        node = VerifyElementExistsNode(node_id="test_exists_true")
        node.set_input_value(
            "selector", {"strategy": "name", "value": "ExistingElement"}
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["exists"] is True
        assert result["element"] is not None

    @pytest.mark.asyncio
    async def test_element_exists_negative(self, mock_execution_context):
        """Test verifying element exists returns False when element not found."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        mock_execution_context.desktop_context.element_exists.return_value = False

        node = VerifyElementExistsNode(node_id="test_exists_false")
        node.set_input_value(
            "selector", {"strategy": "name", "value": "NonExistentElement"}
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["exists"] is False
        assert result["element"] is None

    @pytest.mark.asyncio
    async def test_element_exists_with_timeout(self, mock_execution_context):
        """Test element existence check with timeout configuration."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        mock_execution_context.desktop_context.element_exists.return_value = True
        mock_execution_context.desktop_context.async_wait_for_element.return_value = (
            Mock()
        )

        node = VerifyElementExistsNode(node_id="test_exists_timeout")
        node.config["timeout"] = 5.0
        node.set_input_value(
            "selector", {"strategy": "automation_id", "value": "btn_test"}
        )
        node.set_input_value("timeout", 5.0)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.element_exists.assert_called_once()

    @pytest.mark.asyncio
    async def test_element_exists_missing_selector(self, mock_execution_context):
        """Test error when selector is missing."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        node = VerifyElementExistsNode(node_id="test_missing_selector")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "selector" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_element_exists_missing_desktop_context(self):
        """Test error when desktop context not available."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        context = Mock()
        context.desktop_context = None

        node = VerifyElementExistsNode(node_id="test_no_desktop_ctx")
        node.set_input_value("selector", {"strategy": "name", "value": "Test"})

        with pytest.raises(ValueError) as exc_info:
            await node.execute(context)

        assert "Desktop context" in str(exc_info.value)


# =============================================================================
# VerifyElementPropertyNode Tests
# =============================================================================


class TestVerifyElementPropertyNode:
    """Tests for VerifyElementPropertyNode - verifying element property values."""

    @pytest.mark.asyncio
    async def test_verify_property_equals_success(
        self, mock_execution_context, mock_element
    ):
        """Test verifying property equals expected value succeeds."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        mock_execution_context.desktop_context.verify_element_property.return_value = (
            True
        )

        node = VerifyElementPropertyNode(node_id="test_verify_equals")
        node.config["comparison"] = "equals"
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "TestElement")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["result"] is True

    @pytest.mark.asyncio
    async def test_verify_property_contains(self, mock_execution_context, mock_element):
        """Test verifying property contains expected substring."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        mock_execution_context.desktop_context.verify_element_property.return_value = (
            True
        )

        node = VerifyElementPropertyNode(node_id="test_verify_contains")
        node.config["comparison"] = "contains"
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "Test")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.verify_element_property.assert_called_with(
            element=mock_element,
            property_name="Name",
            expected_value="Test",
            comparison="contains",
        )

    @pytest.mark.asyncio
    async def test_verify_property_failure(self, mock_execution_context, mock_element):
        """Test verification returns False when property does not match."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        mock_execution_context.desktop_context.verify_element_property.return_value = (
            False
        )

        node = VerifyElementPropertyNode(node_id="test_verify_failure")
        node.config["comparison"] = "equals"
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")
        node.set_input_value("expected_value", "WrongValue")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True  # Node executed successfully
        assert result["result"] is False  # But verification failed

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

        node = VerifyElementPropertyNode(node_id="test_missing_property_name")
        node.set_input_value("element", mock_element)
        node.set_input_value("expected_value", "Test")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Property name is required" in str(exc_info.value)


# =============================================================================
# Selector Strategy Tests (Integration with Find nodes)
# =============================================================================


class TestSelectorStrategies:
    """Tests for different selector strategies across element nodes."""

    @pytest.mark.asyncio
    async def test_selector_strategy_name(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test finding element by name selector strategy."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_strategy_name")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "OK Button"})

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_window.find_child.assert_called_once()
        call_args = mock_window.find_child.call_args
        assert call_args[0][0]["strategy"] == "name"
        assert call_args[0][0]["value"] == "OK Button"

    @pytest.mark.asyncio
    async def test_selector_strategy_automation_id(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test finding element by automation_id selector strategy."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_strategy_automation_id")
        node.set_input_value("window", mock_window)
        node.set_input_value(
            "selector", {"strategy": "automation_id", "value": "btnSubmit"}
        )

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_args = mock_window.find_child.call_args
        assert call_args[0][0]["strategy"] == "automation_id"

    @pytest.mark.asyncio
    async def test_selector_strategy_class_name(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test finding element by class_name selector strategy."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_strategy_class")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "class_name", "value": "Button"})

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_args = mock_window.find_child.call_args
        assert call_args[0][0]["strategy"] == "class_name"

    @pytest.mark.asyncio
    async def test_selector_strategy_control_type(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test finding element by control_type selector strategy."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_strategy_control_type")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "control_type", "value": "Edit"})

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_args = mock_window.find_child.call_args
        assert call_args[0][0]["strategy"] == "control_type"


# =============================================================================
# ExecutionResult Pattern Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Tests verifying all nodes follow the ExecutionResult pattern."""

    @pytest.mark.asyncio
    async def test_find_element_result_structure(
        self, mock_execution_context, mock_window, mock_element
    ):
        """Test FindElementNode returns proper ExecutionResult structure."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import FindElementNode

        mock_window.find_child.return_value = mock_element

        node = FindElementNode(node_id="test_result_structure")
        node.set_input_value("window", mock_window)
        node.set_input_value("selector", {"strategy": "name", "value": "Test"})

        result = await node.execute(mock_execution_context)

        # Verify required ExecutionResult fields
        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "next_nodes" in result
        assert isinstance(result["next_nodes"], list)

    @pytest.mark.asyncio
    async def test_get_property_result_structure(
        self, mock_execution_context, mock_element
    ):
        """Test GetElementPropertyNode returns proper ExecutionResult structure."""
        from casare_rpa.nodes.desktop_nodes.element_nodes import GetElementPropertyNode

        mock_element.get_property.return_value = "value"

        node = GetElementPropertyNode(node_id="test_result_structure")
        node.set_input_value("element", mock_element)
        node.set_input_value("property_name", "Name")

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "value" in result
        assert "element" in result
        assert "next_nodes" in result

    @pytest.mark.asyncio
    async def test_verify_exists_result_structure(self, mock_execution_context):
        """Test VerifyElementExistsNode returns proper ExecutionResult structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementExistsNode,
        )

        mock_execution_context.desktop_context.element_exists.return_value = True
        mock_execution_context.desktop_context.async_wait_for_element.return_value = (
            Mock()
        )

        node = VerifyElementExistsNode(node_id="test_result_structure")
        node.set_input_value("selector", {"strategy": "name", "value": "Test"})

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "exists" in result
        assert "element" in result
        assert isinstance(result["exists"], bool)

    @pytest.mark.asyncio
    async def test_verify_property_result_structure(
        self, mock_execution_context, mock_element
    ):
        """Test VerifyElementPropertyNode returns proper ExecutionResult structure."""
        from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
            VerifyElementPropertyNode,
        )

        mock_execution_context.desktop_context.verify_element_property.return_value = (
            True
        )

        node = VerifyElementPropertyNode(node_id="test_result_structure")
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
