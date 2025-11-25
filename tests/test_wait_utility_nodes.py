"""
Tests for wait and utility nodes.

Tests wait/delay operations, data validation, transformation, and logging.
"""

import pytest
from unittest.mock import AsyncMock, patch

from casare_rpa.nodes.wait_nodes import WaitNode, WaitForElementNode, WaitForNavigationNode
from casare_rpa.nodes.utility_nodes import (
    HttpRequestNode,
    ValidateNode,
    TransformNode,
    LogNode,
)
from casare_rpa.core.types import NodeStatus


class TestWaitNode:
    """Tests for simple wait/delay node."""

    @pytest.mark.asyncio
    async def test_wait_basic(self, execution_context):
        """Test basic wait operation."""
        node = WaitNode(node_id="wait_1", duration=0.01)  # Short wait for testing

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0.01
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_wait_zero_duration(self, execution_context):
        """Test wait with zero duration."""
        node = WaitNode(node_id="wait_1", duration=0)

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_wait_from_input(self, execution_context):
        """Test wait duration from input port."""
        node = WaitNode(node_id="wait_1")
        node.set_input_value("duration", 0.02)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["duration"] == 0.02

    @pytest.mark.asyncio
    async def test_wait_negative_duration_fails(self, execution_context):
        """Test wait with negative duration fails."""
        node = WaitNode(node_id="wait_1", duration=-1)

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "non-negative" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_wait_string_duration_converted(self, execution_context):
        """Test string duration is converted to float."""
        node = WaitNode(node_id="wait_1")
        node.set_input_value("duration", "0.01")

        result = await node.execute(execution_context)

        assert result["success"] is True


class TestWaitForElementNode:
    """Tests for wait for element node."""

    @pytest.mark.asyncio
    async def test_wait_for_element_basic(self, context_with_page, mock_page):
        """Test waiting for an element."""
        mock_page.wait_for_selector = AsyncMock()

        node = WaitForElementNode(node_id="wait_elem_1", selector="#my-element")

        result = await node.execute(context_with_page)

        assert result["success"] is True
        mock_page.wait_for_selector.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_element_no_page_fails(self, execution_context):
        """Test wait for element fails without page."""
        node = WaitForElementNode(node_id="wait_elem_1", selector="#element")

        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "no page" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_wait_for_element_no_selector_fails(self, context_with_page):
        """Test wait for element fails without selector."""
        node = WaitForElementNode(node_id="wait_elem_1", selector="")

        result = await node.execute(context_with_page)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_wait_for_element_with_state(self, context_with_page, mock_page):
        """Test waiting for element with specific state."""
        mock_page.wait_for_selector = AsyncMock()

        node = WaitForElementNode(
            node_id="wait_elem_1",
            selector=".hidden-element",
            state="hidden"
        )

        await node.execute(context_with_page)

        mock_page.wait_for_selector.assert_called_once()
        call_args = mock_page.wait_for_selector.call_args
        assert call_args.kwargs.get("state") == "hidden"


class TestWaitForNavigationNode:
    """Tests for wait for navigation node."""

    @pytest.mark.asyncio
    async def test_wait_for_navigation_basic(self, context_with_page, mock_page):
        """Test waiting for navigation."""
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com/new-page"

        node = WaitForNavigationNode(node_id="wait_nav_1")

        result = await node.execute(context_with_page)

        assert result["success"] is True
        mock_page.wait_for_load_state.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_navigation_no_page_fails(self, execution_context):
        """Test wait for navigation fails without page."""
        node = WaitForNavigationNode(node_id="wait_nav_1")

        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_wait_for_navigation_domcontentloaded(self, context_with_page, mock_page):
        """Test waiting for DOMContentLoaded event."""
        mock_page.wait_for_load_state = AsyncMock()
        mock_page.url = "https://example.com"

        node = WaitForNavigationNode(
            node_id="wait_nav_1",
            wait_until="domcontentloaded"
        )

        await node.execute(context_with_page)

        mock_page.wait_for_load_state.assert_called()
        call_args = mock_page.wait_for_load_state.call_args
        assert call_args[0][0] == "domcontentloaded"


class TestValidateNode:
    """Tests for data validation node."""

    @pytest.mark.asyncio
    async def test_validate_not_empty_pass(self, execution_context):
        """Test not_empty validation passes for non-empty value."""
        node = ValidateNode(node_id="validate_1", validation_type="not_empty")
        node.set_input_value("value", "Hello")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True
        assert "valid" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_validate_not_empty_fail(self, execution_context):
        """Test not_empty validation fails for empty value."""
        node = ValidateNode(node_id="validate_1", validation_type="not_empty")
        node.set_input_value("value", "")

        result = await node.execute(execution_context)

        assert result["is_valid"] is False
        assert "invalid" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_validate_is_string(self, execution_context):
        """Test is_string validation."""
        node = ValidateNode(node_id="validate_1", validation_type="is_string")
        node.set_input_value("value", "text")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_is_number(self, execution_context):
        """Test is_number validation."""
        node = ValidateNode(node_id="validate_1", validation_type="is_number")
        node.set_input_value("value", 42.5)

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_is_email_valid(self, execution_context):
        """Test email validation with valid email."""
        node = ValidateNode(node_id="validate_1", validation_type="is_email")
        node.set_input_value("value", "user@example.com")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_is_email_invalid(self, execution_context):
        """Test email validation with invalid email."""
        node = ValidateNode(node_id="validate_1", validation_type="is_email")
        node.set_input_value("value", "not-an-email")

        result = await node.execute(execution_context)

        assert result["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_is_url_valid(self, execution_context):
        """Test URL validation with valid URL."""
        node = ValidateNode(node_id="validate_1", validation_type="is_url")
        node.set_input_value("value", "https://example.com/path")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_matches_regex(self, execution_context):
        """Test regex pattern validation."""
        node = ValidateNode(
            node_id="validate_1",
            validation_type="matches_regex",
            validation_param=r"^\d{3}-\d{4}$"
        )
        node.set_input_value("value", "123-4567")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_min_length(self, execution_context):
        """Test minimum length validation."""
        node = ValidateNode(
            node_id="validate_1",
            validation_type="min_length",
            validation_param=5
        )
        node.set_input_value("value", "Hello")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_min_value(self, execution_context):
        """Test minimum value validation."""
        node = ValidateNode(
            node_id="validate_1",
            validation_type="min_value",
            validation_param=0
        )
        node.set_input_value("value", 10)

        result = await node.execute(execution_context)

        assert result["is_valid"] is True

    @pytest.mark.asyncio
    async def test_validate_in_list(self, execution_context):
        """Test in_list validation."""
        node = ValidateNode(
            node_id="validate_1",
            validation_type="in_list",
            validation_param=["red", "green", "blue"]
        )
        node.set_input_value("value", "green")

        result = await node.execute(execution_context)

        assert result["is_valid"] is True


class TestTransformNode:
    """Tests for data transformation node."""

    @pytest.mark.asyncio
    async def test_transform_to_string(self, execution_context):
        """Test transforming to string."""
        node = TransformNode(node_id="transform_1", transform_type="to_string")
        node.set_input_value("value", 42)

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "42"

    @pytest.mark.asyncio
    async def test_transform_to_integer(self, execution_context):
        """Test transforming to integer."""
        node = TransformNode(node_id="transform_1", transform_type="to_integer")
        node.set_input_value("value", "123")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 123

    @pytest.mark.asyncio
    async def test_transform_to_float(self, execution_context):
        """Test transforming to float."""
        node = TransformNode(node_id="transform_1", transform_type="to_float")
        node.set_input_value("value", "3.14")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 3.14

    @pytest.mark.asyncio
    async def test_transform_to_boolean_true(self, execution_context):
        """Test transforming to boolean true."""
        node = TransformNode(node_id="transform_1", transform_type="to_boolean")
        node.set_input_value("value", "true")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True

    @pytest.mark.asyncio
    async def test_transform_uppercase(self, execution_context):
        """Test transforming to uppercase."""
        node = TransformNode(node_id="transform_1", transform_type="uppercase")
        node.set_input_value("value", "hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_transform_lowercase(self, execution_context):
        """Test transforming to lowercase."""
        node = TransformNode(node_id="transform_1", transform_type="lowercase")
        node.set_input_value("value", "Hello World")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello world"

    @pytest.mark.asyncio
    async def test_transform_trim(self, execution_context):
        """Test trimming whitespace."""
        node = TransformNode(node_id="transform_1", transform_type="trim")
        node.set_input_value("value", "  hello  ")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "hello"

    @pytest.mark.asyncio
    async def test_transform_split(self, execution_context):
        """Test splitting string."""
        node = TransformNode(
            node_id="transform_1",
            transform_type="split",
            transform_param=","
        )
        node.set_input_value("value", "a,b,c")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_transform_join(self, execution_context):
        """Test joining list."""
        node = TransformNode(
            node_id="transform_1",
            transform_type="join",
            transform_param="-"
        )
        node.set_input_value("value", ["a", "b", "c"])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "a-b-c"

    @pytest.mark.asyncio
    async def test_transform_to_json(self, execution_context):
        """Test converting to JSON string."""
        node = TransformNode(node_id="transform_1", transform_type="to_json")
        node.set_input_value("value", {"key": "value"})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_transform_from_json(self, execution_context):
        """Test parsing JSON string."""
        node = TransformNode(node_id="transform_1", transform_type="from_json")
        node.set_input_value("value", '{"name": "Alice"}')

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"name": "Alice"}

    @pytest.mark.asyncio
    async def test_transform_get_key(self, execution_context):
        """Test getting key from dict."""
        node = TransformNode(
            node_id="transform_1",
            transform_type="get_key",
            transform_param="name"
        )
        node.set_input_value("value", {"name": "Bob", "age": 30})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Bob"

    @pytest.mark.asyncio
    async def test_transform_get_index(self, execution_context):
        """Test getting index from list."""
        node = TransformNode(
            node_id="transform_1",
            transform_type="get_index",
            transform_param=1
        )
        node.set_input_value("value", [10, 20, 30])

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 20

    @pytest.mark.asyncio
    async def test_transform_replace(self, execution_context):
        """Test string replacement."""
        node = TransformNode(
            node_id="transform_1",
            transform_type="replace",
            transform_param={"old": "world", "new": "universe"}
        )
        node.set_input_value("value", "Hello world")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello universe"


class TestLogNode:
    """Tests for logging node."""

    @pytest.mark.asyncio
    async def test_log_basic_message(self, execution_context):
        """Test logging a basic message."""
        node = LogNode(node_id="log_1", message="Test log message")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Test log message" in result["message"]

    @pytest.mark.asyncio
    async def test_log_with_data(self, execution_context):
        """Test logging with data."""
        node = LogNode(node_id="log_1", message="Processing")
        node.set_input_value("data", {"count": 42})

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "42" in result["message"]

    @pytest.mark.asyncio
    async def test_log_message_from_input(self, execution_context):
        """Test logging message from input port."""
        node = LogNode(node_id="log_1")
        node.set_input_value("message", "Dynamic message")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Dynamic message" in result["message"]

    @pytest.mark.asyncio
    async def test_log_with_variable_interpolation(self, execution_context):
        """Test logging with variable interpolation."""
        execution_context.set_variable("user_name", "Alice")

        node = LogNode(node_id="log_1", message="Hello, {user_name}!")

        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "Alice" in result["message"]


class TestWaitUtilityScenarios:
    """Integration tests for wait and utility node workflows."""

    @pytest.mark.asyncio
    async def test_validate_transform_flow(self, execution_context):
        """Test validate then transform workflow."""
        # First validate
        validate_node = ValidateNode(
            node_id="validate_1",
            validation_type="is_string"
        )
        validate_node.set_input_value("value", "  test  ")

        validate_result = await validate_node.execute(execution_context)
        assert validate_result["is_valid"] is True

        # Then transform (trim)
        transform_node = TransformNode(
            node_id="transform_1",
            transform_type="trim"
        )
        transform_node.set_input_value("value", "  test  ")

        transform_result = await transform_node.execute(execution_context)
        assert transform_node.get_output_value("result") == "test"

    @pytest.mark.asyncio
    async def test_multiple_validations(self, execution_context):
        """Test multiple validations in sequence."""
        email = "user@example.com"

        # Validate not empty
        v1 = ValidateNode(node_id="v1", validation_type="not_empty")
        v1.set_input_value("value", email)
        r1 = await v1.execute(execution_context)
        assert r1["is_valid"] is True

        # Validate is string
        v2 = ValidateNode(node_id="v2", validation_type="is_string")
        v2.set_input_value("value", email)
        r2 = await v2.execute(execution_context)
        assert r2["is_valid"] is True

        # Validate is email
        v3 = ValidateNode(node_id="v3", validation_type="is_email")
        v3.set_input_value("value", email)
        r3 = await v3.execute(execution_context)
        assert r3["is_valid"] is True

    @pytest.mark.asyncio
    async def test_transform_chain(self, execution_context):
        """Test chaining multiple transformations."""
        value = '{"name": "Alice", "age": 30}'

        # Parse JSON
        t1 = TransformNode(node_id="t1", transform_type="from_json")
        t1.set_input_value("value", value)
        await t1.execute(execution_context)
        parsed = t1.get_output_value("result")

        # Get name
        t2 = TransformNode(node_id="t2", transform_type="get_key", transform_param="name")
        t2.set_input_value("value", parsed)
        await t2.execute(execution_context)
        name = t2.get_output_value("result")

        # Uppercase
        t3 = TransformNode(node_id="t3", transform_type="uppercase")
        t3.set_input_value("value", name)
        await t3.execute(execution_context)

        assert t3.get_output_value("result") == "ALICE"

    @pytest.mark.asyncio
    async def test_wait_between_operations(self, execution_context):
        """Test adding wait between operations."""
        import time

        start_time = time.time()

        # Wait
        wait_node = WaitNode(node_id="wait_1", duration=0.05)
        await wait_node.execute(execution_context)

        # Transform
        transform_node = TransformNode(node_id="transform_1", transform_type="uppercase")
        transform_node.set_input_value("value", "test")
        await transform_node.execute(execution_context)

        elapsed = time.time() - start_time

        # Should have waited at least 0.05 seconds
        assert elapsed >= 0.05
        assert transform_node.get_output_value("result") == "TEST"

    @pytest.mark.asyncio
    async def test_conditional_validation_workflow(self, execution_context):
        """Test workflow with conditional validation."""
        # Process different data types
        values = [42, "hello", "", None, ["a", "b"]]
        results = []

        for value in values:
            # Validate not empty
            validate = ValidateNode(node_id="v", validation_type="not_empty")
            validate.set_input_value("value", value)
            result = await validate.execute(execution_context)
            results.append({
                "value": value,
                "is_valid": result["is_valid"]
            })

        # Check results
        assert results[0]["is_valid"] is True   # 42
        assert results[1]["is_valid"] is True   # "hello"
        assert results[2]["is_valid"] is False  # ""
        assert results[3]["is_valid"] is False  # None
        assert results[4]["is_valid"] is True   # ["a", "b"]
