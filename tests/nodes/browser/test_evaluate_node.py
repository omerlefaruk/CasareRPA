"""
Tests for BrowserEvaluateNode.

This test suite covers the BrowserEvaluateNode which executes arbitrary
JavaScript code in the browser page context via Playwright's page.evaluate().

Test Philosophy:
- Happy path: Normal operation with valid scripts and arguments
- Sad path: Expected failures (script errors, missing page, timeout)
- Edge cases: Different return types, JSON parsing, variable storage

Run: pytest tests/nodes/browser/test_evaluate_node.py -v
"""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from casare_rpa.nodes.browser.evaluate_node import BrowserEvaluateNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus


# =============================================================================
# BrowserEvaluateNode Instantiation Tests
# =============================================================================


class TestBrowserEvaluateNodeInit:
    """Test node initialization and port definition."""

    def test_init_default_config(self) -> None:
        """Test creating node with default configuration."""
        node = BrowserEvaluateNode("test_node")
        assert node.node_id == "test_node"
        assert node.node_type == "BrowserEvaluateNode"
        assert node.name == "Browser Evaluate"

    def test_init_custom_name(self) -> None:
        """Test creating node with custom name."""
        node = BrowserEvaluateNode("test_node", name="Custom Evaluate")
        assert node.name == "Custom Evaluate"

    def test_init_with_script_config(self) -> None:
        """Test creating node with script configuration."""
        node = BrowserEvaluateNode(
            "test_node", config={"script": "document.title", "return_json": False}
        )
        assert node.get_parameter("script") == "document.title"
        assert node.get_parameter("return_json") is False


class TestBrowserEvaluateNodePorts:
    """Test port definitions."""

    def test_define_ports_inputs(self) -> None:
        """Test that all input ports are defined correctly."""
        node = BrowserEvaluateNode("test_node")

        # Check input ports exist
        assert "page" in node.input_ports
        assert "script" in node.input_ports
        assert "arg" in node.input_ports

        # Check exec ports
        assert "exec_in" in node.input_ports

    def test_define_ports_outputs(self) -> None:
        """Test that all output ports are defined correctly."""
        node = BrowserEvaluateNode("test_node")

        # Check output ports exist
        assert "result" in node.output_ports
        assert "success" in node.output_ports
        assert "error" in node.output_ports

        # Check exec out
        assert "exec_out" in node.output_ports

    def test_port_types(self) -> None:
        """Test that port types are correct."""
        node = BrowserEvaluateNode("test_node")

        # Check input port types
        assert node.input_ports["page"].data_type == DataType.PAGE
        assert node.input_ports["script"].data_type == DataType.STRING
        assert node.input_ports["arg"].data_type == DataType.ANY

        # Check output port types
        assert node.output_ports["result"].data_type == DataType.ANY
        assert node.output_ports["success"].data_type == DataType.BOOLEAN
        assert node.output_ports["error"].data_type == DataType.STRING


# =============================================================================
# Execute Simple Script Tests
# =============================================================================


class TestExecuteSimpleScript:
    """Tests for executing simple JavaScript scripts."""

    @pytest.mark.asyncio
    async def test_execute_simple_script(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Execute simple script returning a string."""
        mock_page.evaluate.return_value = "My Page Title"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "document.title", "return_json": False}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "My Page Title"
        assert node.get_output_value("success") is True
        assert node.get_output_value("error") == ""
        mock_page.evaluate.assert_called_once_with("document.title")

    @pytest.mark.asyncio
    async def test_execute_script_from_input_port(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script provided via input port takes precedence."""
        mock_page.evaluate.return_value = "Input Script Result"

        node = BrowserEvaluateNode("test_node", config={"script": "property_script"})
        # Set script via input port
        node.set_input_value("script", "input_script")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.evaluate.assert_called_once_with("input_script")

    @pytest.mark.asyncio
    async def test_execute_numeric_result(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returning numeric value."""
        mock_page.evaluate.return_value = 42

        node = BrowserEvaluateNode("test_node", config={"script": "1 + 41"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == 42

    @pytest.mark.asyncio
    async def test_execute_boolean_result(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returning boolean value."""
        mock_page.evaluate.return_value = True

        node = BrowserEvaluateNode("test_node", config={"script": "document.body !== null"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") is True


# =============================================================================
# Execute with Argument Tests
# =============================================================================


class TestExecuteWithArg:
    """Tests for scripts that receive arguments."""

    @pytest.mark.asyncio
    async def test_execute_with_arg(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SUCCESS: Pass argument to script."""
        mock_page.evaluate.return_value = "Header Text"

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "(selector) => document.querySelector(selector)?.innerText"},
        )
        node.set_input_value("arg", "#header")

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.evaluate.assert_called_once_with(
            "(selector) => document.querySelector(selector)?.innerText", "#header"
        )

    @pytest.mark.asyncio
    async def test_execute_with_object_arg(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Pass object argument to script."""
        mock_page.evaluate.return_value = [
            {"name": "Product 1", "price": "$10"},
            {"name": "Product 2", "price": "$20"},
        ]

        script = """(config) => {
            return Array.from(document.querySelectorAll(config.selector)).map(el => ({
                name: el.querySelector(config.nameSelector)?.innerText,
                price: el.querySelector(config.priceSelector)?.innerText
            }));
        }"""

        arg = {
            "selector": ".product-card",
            "nameSelector": ".title",
            "priceSelector": ".price",
        }

        node = BrowserEvaluateNode("test_node", config={"script": script})
        node.set_input_value("arg", arg)

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.evaluate.assert_called_once_with(script, arg)

    @pytest.mark.asyncio
    async def test_execute_without_arg(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SUCCESS: Execute script without argument."""
        mock_page.evaluate.return_value = "No Arg Result"

        node = BrowserEvaluateNode("test_node", config={"script": "document.title"})
        # Explicitly not setting arg

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Should be called without second argument
        mock_page.evaluate.assert_called_once_with("document.title")


# =============================================================================
# Execute Returns Object/Array Tests
# =============================================================================


class TestExecuteReturnsObject:
    """Tests for scripts that return objects."""

    @pytest.mark.asyncio
    async def test_execute_returns_object(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returns dictionary/object."""
        expected_result = {
            "title": "Page Title",
            "url": "https://example.com",
            "readyState": "complete",
        }
        mock_page.evaluate.return_value = expected_result

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "({title: document.title, url: location.href, readyState: document.readyState})"
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == expected_result
        assert result["data"]["result_type"] == "dict"

    @pytest.mark.asyncio
    async def test_execute_returns_nested_object(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returns nested object."""
        expected_result = {
            "page": {"title": "Page Title", "meta": {"description": "Page description"}}
        }
        mock_page.evaluate.return_value = expected_result

        node = BrowserEvaluateNode("test_node", config={"script": "getPageInfo()"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == expected_result


class TestExecuteReturnsArray:
    """Tests for scripts that return arrays."""

    @pytest.mark.asyncio
    async def test_execute_returns_array(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returns list/array."""
        expected_result = ["item1", "item2", "item3"]
        mock_page.evaluate.return_value = expected_result

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "Array.from(document.querySelectorAll('li')).map(el => el.innerText)"
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == expected_result
        assert result["data"]["result_type"] == "list"

    @pytest.mark.asyncio
    async def test_execute_returns_array_of_objects(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Script returns array of objects."""
        expected_result = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
        mock_page.evaluate.return_value = expected_result

        node = BrowserEvaluateNode("test_node", config={"script": "getItems()"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == expected_result

    @pytest.mark.asyncio
    async def test_execute_returns_empty_array(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """EDGE CASE: Script returns empty array."""
        mock_page.evaluate.return_value = []

        node = BrowserEvaluateNode("test_node", config={"script": "[]"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == []


# =============================================================================
# Timeout Tests
# =============================================================================


class TestExecuteTimeout:
    """Tests for timeout handling."""

    @pytest.mark.asyncio
    async def test_execute_timeout_passed_to_wait_for_selector(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Timeout is passed to wait_for_selector."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "getResult()",
                "wait_for_selector": "#content",
                "timeout": 5000,
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_selector.assert_called_once_with(
            "#content", timeout=5000, state="attached"
        )

    @pytest.mark.asyncio
    async def test_execute_default_timeout(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Default timeout is used when not specified."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "getResult()", "wait_for_selector": "#content"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Check that wait_for_selector was called (timeout defaults to DEFAULT_NODE_TIMEOUT * 1000)
        mock_page.wait_for_selector.assert_called_once()


# =============================================================================
# Script Error Tests
# =============================================================================


class TestExecuteScriptError:
    """Tests for JavaScript error handling."""

    @pytest.mark.asyncio
    async def test_execute_script_error(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SAD PATH: JavaScript execution throws error."""
        mock_page.evaluate.side_effect = Exception(
            "Evaluation failed: ReferenceError: undefinedVar is not defined"
        )

        node = BrowserEvaluateNode("test_node", config={"script": "undefinedVar.property"})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "undefinedVar is not defined" in result["error"]
        assert node.get_output_value("success") is False
        assert "undefinedVar" in node.get_output_value("error")

    @pytest.mark.asyncio
    async def test_execute_syntax_error(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SAD PATH: JavaScript has syntax error."""
        mock_page.evaluate.side_effect = Exception(
            "Evaluation failed: SyntaxError: Unexpected token"
        )

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "function( { }"},  # Invalid syntax
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "SyntaxError" in result["error"] or "Unexpected" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_missing_script(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SAD PATH: No script provided."""
        node = BrowserEvaluateNode("test_node", config={"script": ""})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "Script is required" in result["error"]
        assert node.get_output_value("success") is False

    @pytest.mark.asyncio
    async def test_execute_whitespace_only_script(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SAD PATH: Script contains only whitespace."""
        node = BrowserEvaluateNode("test_node", config={"script": "   \n\t  "})

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "Script is required" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_no_page_available(self, mock_context_no_page: MagicMock) -> None:
        """SAD PATH: No page instance available."""
        node = BrowserEvaluateNode("test_node", config={"script": "document.title"})

        result = await node.execute(mock_context_no_page)

        assert result["success"] is False
        assert "page" in result["error"].lower() or "No page" in result["error"]


# =============================================================================
# Wait for Selector Tests
# =============================================================================


class TestWaitForSelector:
    """Tests for wait_for_selector property."""

    @pytest.mark.asyncio
    async def test_wait_for_selector_before_execute(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Wait for selector before executing script."""
        mock_page.evaluate.return_value = "loaded content"

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "document.querySelector('#content').innerText",
                "wait_for_selector": "#content",
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        # Verify wait_for_selector was called before evaluate
        mock_page.wait_for_selector.assert_called_once()
        mock_page.evaluate.assert_called_once()

    @pytest.mark.asyncio
    async def test_wait_for_selector_empty_skips_wait(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Empty wait_for_selector skips waiting."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "document.title", "wait_for_selector": ""}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_selector.assert_not_called()

    @pytest.mark.asyncio
    async def test_wait_for_selector_timeout_error(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SAD PATH: Selector wait times out."""
        mock_page.wait_for_selector.side_effect = Exception(
            "Timeout 5000ms exceeded waiting for selector '#missing'"
        )

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "document.title",
                "wait_for_selector": "#missing",
                "timeout": 5000,
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "Timeout" in result["error"] or "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_wait_for_selector_variable_resolution(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: wait_for_selector resolves variables."""
        mock_page.evaluate.return_value = "result"
        mock_context.resolve_value.side_effect = (
            lambda x: "#resolved-selector" if x == "{{selector}}" else x
        )

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "document.title", "wait_for_selector": "{{selector}}"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.wait_for_selector.assert_called_once_with(
            "#resolved-selector", timeout=30000, state="attached"
        )


# =============================================================================
# Store Variable Tests
# =============================================================================


class TestStoreVariable:
    """Tests for store_variable property."""

    @pytest.mark.asyncio
    async def test_store_variable_in_context(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Result stored in context variable."""
        mock_page.evaluate.return_value = {"extracted": "data"}

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "getData()", "store_variable": "extracted_data"},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_context.set_variable.assert_called_once_with("extracted_data", {"extracted": "data"})
        assert result["data"]["variable"] == "extracted_data"

    @pytest.mark.asyncio
    async def test_store_variable_empty_skips_storage(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Empty store_variable skips storage."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "document.title", "store_variable": ""}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_context.set_variable.assert_not_called()
        assert result["data"]["variable"] is None

    @pytest.mark.asyncio
    async def test_store_variable_whitespace_only_skips(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Whitespace-only store_variable skips storage."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "document.title", "store_variable": "   "}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_context.set_variable.assert_not_called()


# =============================================================================
# JSON Parsing Tests
# =============================================================================


class TestJsonParsing:
    """Tests for return_json property and JSON parsing."""

    @pytest.mark.asyncio
    async def test_json_parsing_enabled_parses_json_string(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: JSON string result is parsed when return_json=True."""
        mock_page.evaluate.return_value = '{"key": "value"}'

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "JSON.stringify({key: 'value'})", "return_json": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"key": "value"}

    @pytest.mark.asyncio
    async def test_json_parsing_enabled_parses_array_string(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: JSON array string is parsed when return_json=True."""
        mock_page.evaluate.return_value = "[1, 2, 3]"

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "JSON.stringify([1, 2, 3])", "return_json": True},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_json_parsing_disabled_returns_raw_string(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: String result is not parsed when return_json=False."""
        mock_page.evaluate.return_value = '{"key": "value"}'

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "JSON.stringify({key: 'value'})", "return_json": False},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == '{"key": "value"}'

    @pytest.mark.asyncio
    async def test_json_parsing_invalid_json_returns_string(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """EDGE CASE: Invalid JSON string is returned as-is."""
        mock_page.evaluate.return_value = "{invalid json}"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "'{invalid json}'", "return_json": True}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "{invalid json}"

    @pytest.mark.asyncio
    async def test_json_parsing_non_json_string_untouched(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Non-JSON string is returned untouched."""
        mock_page.evaluate.return_value = "Hello World"

        node = BrowserEvaluateNode(
            "test_node", config={"script": "'Hello World'", "return_json": True}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "Hello World"

    @pytest.mark.asyncio
    async def test_json_parsing_object_result_untouched(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Object result is not double-parsed."""
        mock_page.evaluate.return_value = {"already": "parsed"}

        node = BrowserEvaluateNode(
            "test_node", config={"script": "({already: 'parsed'})", "return_json": True}
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == {"already": "parsed"}


# =============================================================================
# Edge Cases and Integration Tests
# =============================================================================


class TestEdgeCases:
    """Edge cases and additional scenarios."""

    @pytest.mark.asyncio
    async def test_execute_returns_null(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """EDGE CASE: Script returns null/None."""
        mock_page.evaluate.return_value = None

        node = BrowserEvaluateNode("test_node", config={"script": "null"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") is None

    @pytest.mark.asyncio
    async def test_execute_returns_undefined(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """EDGE CASE: Script returns undefined (becomes None in Python)."""
        mock_page.evaluate.return_value = None  # undefined -> None

        node = BrowserEvaluateNode("test_node", config={"script": "undefined"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") is None

    @pytest.mark.asyncio
    async def test_execute_large_result(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """EDGE CASE: Script returns large data set."""
        large_result = [{"id": i, "data": "x" * 100} for i in range(1000)]
        mock_page.evaluate.return_value = large_result

        node = BrowserEvaluateNode("test_node", config={"script": "getLargeData()"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert len(node.get_output_value("result")) == 1000

    @pytest.mark.asyncio
    async def test_node_status_success(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SUCCESS: Node status is set to SUCCESS on success."""
        mock_page.evaluate.return_value = "result"

        node = BrowserEvaluateNode("test_node", config={"script": "document.title"})

        await node.execute(mock_context)

        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_node_status_error(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SAD PATH: Node status is set to ERROR on failure."""
        mock_page.evaluate.side_effect = Exception("Script error")

        node = BrowserEvaluateNode("test_node", config={"script": "failingScript()"})

        await node.execute(mock_context)

        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_variable_resolution_in_script(
        self, mock_context: MagicMock, mock_page: AsyncMock
    ) -> None:
        """SUCCESS: Variables in script are resolved."""
        mock_page.evaluate.return_value = "result"
        mock_context.resolve_value.side_effect = lambda x: (
            "document.querySelector('#resolved')" if x == "{{script}}" else x
        )

        node = BrowserEvaluateNode("test_node", config={"script": "{{script}}"})

        result = await node.execute(mock_context)

        assert result["success"] is True
        mock_page.evaluate.assert_called_once_with("document.querySelector('#resolved')")


class TestRetryBehavior:
    """Tests for retry functionality."""

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SUCCESS: Script succeeds after retry."""
        # First call fails, second succeeds
        mock_page.evaluate.side_effect = [
            Exception("Temporary error"),
            "success after retry",
        ]

        node = BrowserEvaluateNode(
            "test_node",
            config={"script": "getData()", "retry_count": 1, "retry_interval": 100},
        )

        result = await node.execute(mock_context)

        assert result["success"] is True
        assert node.get_output_value("result") == "success after retry"
        assert mock_page.evaluate.call_count == 2
        assert result["data"]["attempts"] == 2

    @pytest.mark.asyncio
    async def test_all_retries_fail(self, mock_context: MagicMock, mock_page: AsyncMock) -> None:
        """SAD PATH: All retry attempts fail."""
        mock_page.evaluate.side_effect = Exception("Persistent error")

        node = BrowserEvaluateNode(
            "test_node",
            config={
                "script": "failingScript()",
                "retry_count": 2,
                "retry_interval": 50,
            },
        )

        result = await node.execute(mock_context)

        assert result["success"] is False
        assert "Persistent error" in result["error"]
        assert mock_page.evaluate.call_count == 3  # Initial + 2 retries
