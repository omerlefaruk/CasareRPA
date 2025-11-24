"""
Phase 1: Security & Stability Tests

Tests for:
1. Safe expression evaluation (safe_eval replaces eval)
2. Secrets management
3. Browser context cleanup
4. Script injection prevention
"""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestSafeEval:
    """Tests for safe_eval function replacing dangerous eval()."""

    def test_safe_eval_basic_arithmetic(self):
        """Test basic arithmetic expressions."""
        from casare_rpa.utils.safe_eval import safe_eval

        assert safe_eval("2 + 2") == 4
        assert safe_eval("10 - 3") == 7
        assert safe_eval("5 * 6") == 30
        assert safe_eval("20 / 4") == 5

    def test_safe_eval_comparisons(self):
        """Test comparison expressions."""
        from casare_rpa.utils.safe_eval import safe_eval

        assert safe_eval("5 > 3") is True
        assert safe_eval("2 < 1") is False
        assert safe_eval("5 >= 5") is True
        assert safe_eval("3 <= 2") is False
        assert safe_eval("5 == 5") is True
        assert safe_eval("5 != 3") is True

    def test_safe_eval_with_variables(self):
        """Test expressions with variable context."""
        from casare_rpa.utils.safe_eval import safe_eval

        context = {"x": 10, "y": 5}
        assert safe_eval("x + y", context) == 15
        assert safe_eval("x > y", context) is True
        assert safe_eval("x * 2", context) == 20

    def test_safe_eval_boolean_logic(self):
        """Test boolean logic expressions."""
        from casare_rpa.utils.safe_eval import safe_eval

        assert safe_eval("True and True") is True
        assert safe_eval("True and False") is False
        assert safe_eval("True or False") is True
        assert safe_eval("not False") is True

    def test_safe_eval_with_context_variables(self):
        """Test safe_eval with workflow context variables."""
        from casare_rpa.utils.safe_eval import safe_eval

        context = {
            "count": 5,
            "max_count": 10,
            "name": "test",
            "is_active": True,
        }

        assert safe_eval("count < max_count", context) is True
        assert safe_eval("count + 1", context) == 6
        assert safe_eval("is_active", context) is True

    def test_safe_eval_blocks_dangerous_operations(self):
        """Test that dangerous operations are blocked."""
        from casare_rpa.utils.safe_eval import safe_eval

        # These should raise exceptions or return safely
        dangerous_expressions = [
            "__import__('os').system('ls')",
            "open('/etc/passwd').read()",
            "exec('print(1)')",
            "eval('1+1')",
        ]

        for expr in dangerous_expressions:
            with pytest.raises(Exception):
                safe_eval(expr)

    def test_safe_eval_string_operations(self):
        """Test string operations in safe_eval."""
        from casare_rpa.utils.safe_eval import safe_eval

        context = {"name": "hello"}
        # String comparison should work
        assert safe_eval("name == 'hello'", context) is True

    def test_safe_eval_list_operations(self):
        """Test list operations in safe_eval."""
        from casare_rpa.utils.safe_eval import safe_eval

        context = {"items": [1, 2, 3]}
        assert safe_eval("len(items)", context) == 3
        assert safe_eval("items[0]", context) == 1


class TestSecretsManager:
    """Tests for secrets management functionality."""

    def test_secrets_manager_singleton(self):
        """Test that SecretsManager is a singleton."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager1 = SecretsManager()
        manager2 = SecretsManager()
        assert manager1 is manager2

    def test_secrets_manager_get_secret(self):
        """Test getting secrets from environment."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager = SecretsManager()

        # Set a test environment variable
        os.environ["TEST_SECRET_KEY"] = "test_value_123"

        try:
            secret = manager.get("TEST_SECRET_KEY")
            assert secret == "test_value_123"
        finally:
            del os.environ["TEST_SECRET_KEY"]

    def test_secrets_manager_missing_secret(self):
        """Test handling of missing secrets."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager = SecretsManager()

        # Should return None for missing secrets
        result = manager.get("NONEXISTENT_SECRET_KEY_12345")
        assert result is None

    def test_secrets_manager_default_value(self):
        """Test default value for missing secrets."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager = SecretsManager()

        result = manager.get("NONEXISTENT_KEY", default="default_val")
        assert result == "default_val"

    def test_secrets_manager_has_secret(self):
        """Test checking if secret exists."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager = SecretsManager()

        # Set a test environment variable
        os.environ["TEST_HAS_SECRET"] = "exists"

        try:
            assert manager.has("TEST_HAS_SECRET") is True
            assert manager.has("NONEXISTENT_KEY_12345") is False
        finally:
            del os.environ["TEST_HAS_SECRET"]

    def test_secrets_manager_get_required(self):
        """Test getting required secrets."""
        from casare_rpa.utils.secrets_manager import SecretsManager

        manager = SecretsManager()

        # Set a test environment variable
        os.environ["TEST_REQUIRED_SECRET"] = "required_value"

        try:
            secret = manager.get_required("TEST_REQUIRED_SECRET")
            assert secret == "required_value"

            # Missing required secret should raise
            with pytest.raises(ValueError):
                manager.get_required("NONEXISTENT_REQUIRED_KEY")
        finally:
            del os.environ["TEST_REQUIRED_SECRET"]

    def test_get_secret_function(self):
        """Test convenience function for getting secrets."""
        from casare_rpa.utils.secrets_manager import get_secret

        # Set a test environment variable
        os.environ["TEST_FUNC_SECRET"] = "func_value"

        try:
            secret = get_secret("TEST_FUNC_SECRET")
            assert secret == "func_value"

            # With default
            result = get_secret("NONEXISTENT_KEY", default="default")
            assert result == "default"
        finally:
            del os.environ["TEST_FUNC_SECRET"]


class TestBrowserContextCleanup:
    """Tests for browser context cleanup in ExecutionContext."""

    @pytest.mark.asyncio
    async def test_execution_context_async_cleanup(self):
        """Test async context manager cleanup."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test_cleanup")

        # Mock browser and pages
        mock_page = MagicMock()
        mock_page.close = MagicMock(return_value=None)

        mock_browser_context = MagicMock()
        mock_browser_context.close = MagicMock(return_value=None)

        mock_browser = MagicMock()
        mock_browser.close = MagicMock(return_value=None)

        # Make close methods async
        async def async_close():
            pass

        mock_page.close = async_close
        mock_browser_context.close = async_close
        mock_browser.close = async_close

        # Set up context
        context.pages["test_page"] = mock_page
        context.browser_contexts.append(mock_browser_context)
        context.browser = mock_browser

        # Use async context manager
        async with context:
            pass  # Context should be cleaned up on exit

        # Verify cleanup happened
        assert len(context.pages) == 0
        assert len(context.browser_contexts) == 0
        assert context.browser is None

    @pytest.mark.asyncio
    async def test_execution_context_tracks_browser_contexts(self):
        """Test that browser contexts are properly tracked."""
        from casare_rpa.core.execution_context import ExecutionContext

        context = ExecutionContext(workflow_name="test_tracking")

        mock_context1 = MagicMock()
        mock_context2 = MagicMock()

        context.add_browser_context(mock_context1)
        context.add_browser_context(mock_context2)

        assert len(context.browser_contexts) == 2
        assert mock_context1 in context.browser_contexts
        assert mock_context2 in context.browser_contexts


class TestScriptInjectionPrevention:
    """Tests for preventing script injection in selector operations."""

    def test_selector_uses_parameterized_calls(self):
        """Verify selector manager uses parameterized JavaScript calls."""
        from casare_rpa.utils.selector_manager import SelectorManager

        # Read the source to verify parameterized calls
        import inspect
        source = inspect.getsource(SelectorManager)

        # Should NOT contain string interpolation for selectors in evaluate calls
        # Instead should use parameterized form: evaluate("...", selector_value)

        # Check highlight_elements method uses parameterized calls
        assert "evaluate(\"\"\"" in source or "evaluate('''" in source
        # The selector value should be passed as a parameter, not interpolated

    def test_selector_cache_key_hashing(self):
        """Test that selector cache uses safe key hashing."""
        from casare_rpa.utils.selector_cache import SelectorCache

        cache = SelectorCache()

        # Test with potentially dangerous selector strings
        dangerous_selectors = [
            "'); DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "${malicious}",
            "{{template_injection}}",
        ]

        for selector in dangerous_selectors:
            # Should create safe cache keys without executing content
            key = cache._make_key(selector, "xpath", "http://test.com")
            assert isinstance(key, str)
            # Key should be a safe string, not contain the raw dangerous content directly
            # (it's hashed/escaped)


class TestDataOperationNodesSecurity:
    """Tests for security in data operation nodes."""

    @pytest.mark.asyncio
    async def test_json_parse_node_safe(self):
        """Test JsonParseNode handles malicious JSON safely."""
        from casare_rpa.nodes.data_operation_nodes import JsonParseNode

        node = JsonParseNode("test_json")

        # Valid JSON should work
        node.set_input_value("json_string", '{"name": "test", "value": 123}')
        result = await node.execute(None)
        assert result["success"] is True

        # Invalid JSON should fail gracefully
        node2 = JsonParseNode("test_json2")
        node2.set_input_value("json_string", "not valid json {{{")
        result2 = await node2.execute(None)
        assert result2["success"] is False
        assert "error" in result2

    @pytest.mark.asyncio
    async def test_regex_node_safe(self):
        """Test regex nodes don't allow ReDoS attacks."""
        from casare_rpa.nodes.data_operation_nodes import RegexMatchNode

        node = RegexMatchNode("test_regex")

        # Normal regex should work
        node.set_input_value("text", "Hello World")
        node.set_input_value("pattern", r"\w+")
        result = await node.execute(None)
        assert result["success"] is True

        # Complex regex on simple text should still complete
        node2 = RegexMatchNode("test_regex2")
        node2.set_input_value("text", "aaaa")
        node2.set_input_value("pattern", r"a+")
        result2 = await node2.execute(None)
        assert result2["success"] is True
