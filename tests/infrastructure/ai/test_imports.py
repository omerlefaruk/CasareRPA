"""
Import verification tests for Playwright MCP integration.

Verifies that all new modules can be imported without errors,
type hints are accessible, and public APIs are properly exported.

Test Coverage:
- Module imports
- Class imports
- Function imports
- Public API completeness
- Type hint accessibility
"""

import pytest


class TestPlaywrightMCPImports:
    """Tests for playwright_mcp module imports."""

    def test_import_playwright_mcp_module(self):
        """Should import playwright_mcp module without errors."""
        from casare_rpa.infrastructure.ai import playwright_mcp

        assert playwright_mcp is not None

    def test_import_playwright_mcp_client(self):
        """Should import PlaywrightMCPClient class."""
        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

        assert PlaywrightMCPClient is not None
        assert callable(PlaywrightMCPClient)

    def test_import_mcp_tool_result(self):
        """Should import MCPToolResult dataclass."""
        from casare_rpa.infrastructure.ai.playwright_mcp import MCPToolResult

        assert MCPToolResult is not None

        # Should be a dataclass
        result = MCPToolResult(success=True)
        assert result.success is True

    def test_import_fetch_page_context(self):
        """Should import fetch_page_context function."""
        from casare_rpa.infrastructure.ai.playwright_mcp import fetch_page_context

        assert fetch_page_context is not None
        assert callable(fetch_page_context)

    def test_playwright_mcp_client_has_expected_methods(self):
        """Should have all expected public methods."""
        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

        client = PlaywrightMCPClient()

        # Lifecycle methods
        assert hasattr(client, "start")
        assert hasattr(client, "stop")

        # Context manager
        assert hasattr(client, "__aenter__")
        assert hasattr(client, "__aexit__")

        # High-level browser methods
        assert hasattr(client, "navigate")
        assert hasattr(client, "get_snapshot")
        assert hasattr(client, "click")
        assert hasattr(client, "type_text")
        assert hasattr(client, "close_browser")
        assert hasattr(client, "take_screenshot")
        assert hasattr(client, "wait_for")
        assert hasattr(client, "evaluate")

        # Tool methods
        assert hasattr(client, "call_tool")
        assert hasattr(client, "list_tools")


class TestPageAnalyzerImports:
    """Tests for page_analyzer module imports."""

    def test_import_page_analyzer_module(self):
        """Should import page_analyzer module without errors."""
        from casare_rpa.infrastructure.ai import page_analyzer

        assert page_analyzer is not None

    def test_import_page_analyzer_class(self):
        """Should import PageAnalyzer class."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer

        assert PageAnalyzer is not None
        assert callable(PageAnalyzer)

    def test_import_page_context(self):
        """Should import PageContext dataclass."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageContext

        assert PageContext is not None

        # Should be a dataclass
        context = PageContext(url="https://example.com", title="Test")
        assert context.url == "https://example.com"

    def test_import_form_info(self):
        """Should import FormInfo dataclass."""
        from casare_rpa.infrastructure.ai.page_analyzer import FormInfo

        assert FormInfo is not None

        form = FormInfo(selector="form#test")
        assert form.selector == "form#test"

    def test_import_form_field(self):
        """Should import FormField dataclass."""
        from casare_rpa.infrastructure.ai.page_analyzer import FormField

        assert FormField is not None

        field = FormField(name="test", selector="input", field_type="text")
        assert field.name == "test"

    def test_import_analyze_page_function(self):
        """Should import analyze_page convenience function."""
        from casare_rpa.infrastructure.ai.page_analyzer import analyze_page

        assert analyze_page is not None
        assert callable(analyze_page)

    def test_page_analyzer_has_expected_methods(self):
        """Should have expected public methods."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer

        analyzer = PageAnalyzer()

        assert hasattr(analyzer, "analyze_snapshot")

    def test_page_context_has_expected_methods(self):
        """Should have expected public methods."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageContext

        context = PageContext(url="", title="")

        assert hasattr(context, "to_dict")
        assert hasattr(context, "to_prompt_context")
        assert hasattr(context, "is_empty")


class TestAIModuleExports:
    """Tests for infrastructure.ai module exports."""

    def test_import_from_ai_module(self):
        """Should import all Playwright MCP components from ai module."""
        from casare_rpa.infrastructure.ai import (
            FormField,
            FormInfo,
            MCPToolResult,
            PageAnalyzer,
            PageContext,
            PlaywrightMCPClient,
            analyze_page,
            fetch_page_context,
        )

        # All imports should succeed
        assert PlaywrightMCPClient is not None
        assert MCPToolResult is not None
        assert fetch_page_context is not None
        assert PageAnalyzer is not None
        assert PageContext is not None
        assert FormInfo is not None
        assert FormField is not None
        assert analyze_page is not None

    def test_all_exports_in_module(self):
        """Should have all exports in __all__ list."""
        from casare_rpa.infrastructure import ai

        # Check __all__ includes our exports
        assert "PlaywrightMCPClient" in ai.__all__
        assert "MCPToolResult" in ai.__all__
        assert "fetch_page_context" in ai.__all__
        assert "PageAnalyzer" in ai.__all__
        assert "PageContext" in ai.__all__
        assert "FormInfo" in ai.__all__
        assert "FormField" in ai.__all__
        assert "analyze_page" in ai.__all__


class TestSmartWorkflowAgentImports:
    """Tests for SmartWorkflowAgent imports and URL detection."""

    def test_import_smart_workflow_agent(self):
        """Should import SmartWorkflowAgent from agent.core."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        assert SmartWorkflowAgent is not None

    def test_agent_has_url_pattern(self):
        """Should have URL_PATTERN for URL detection."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        assert hasattr(SmartWorkflowAgent, "URL_PATTERN")
        assert SmartWorkflowAgent.URL_PATTERN is not None

    def test_agent_has_max_urls_limit(self):
        """Should have MAX_URLS_TO_ANALYZE constant."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        assert hasattr(SmartWorkflowAgent, "MAX_URLS_TO_ANALYZE")
        assert isinstance(SmartWorkflowAgent.MAX_URLS_TO_ANALYZE, int)
        assert SmartWorkflowAgent.MAX_URLS_TO_ANALYZE > 0

    def test_agent_has_url_detection_method(self):
        """Should have _detect_urls method."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        agent = SmartWorkflowAgent(llm_client=None)
        assert hasattr(agent, "_detect_urls")
        assert callable(agent._detect_urls)

    def test_agent_has_page_context_methods(self):
        """Should have page context methods."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        agent = SmartWorkflowAgent(llm_client=None)

        assert hasattr(agent, "_check_mcp_available")
        assert hasattr(agent, "_fetch_page_context")
        assert hasattr(agent, "_fetch_page_contexts")
        assert hasattr(agent, "_format_page_contexts")

    def test_agent_has_page_context_cache(self):
        """Should have page context cache dict."""
        from casare_rpa.infrastructure.ai.agent.core import SmartWorkflowAgent

        agent = SmartWorkflowAgent(llm_client=None)

        assert hasattr(agent, "_page_context_cache")
        assert isinstance(agent._page_context_cache, dict)


class TestDataclassTypeHints:
    """Tests for type hint accessibility on dataclasses."""

    def test_mcp_tool_result_type_hints(self):
        """Should have accessible type hints."""
        import dataclasses

        from casare_rpa.infrastructure.ai.playwright_mcp import MCPToolResult

        assert dataclasses.is_dataclass(MCPToolResult)

        fields = {f.name: f.type for f in dataclasses.fields(MCPToolResult)}
        assert "success" in fields
        assert "content" in fields
        assert "error" in fields

    def test_page_context_type_hints(self):
        """Should have accessible type hints."""
        import dataclasses

        from casare_rpa.infrastructure.ai.page_analyzer import PageContext

        assert dataclasses.is_dataclass(PageContext)

        fields = {f.name for f in dataclasses.fields(PageContext)}
        assert "url" in fields
        assert "title" in fields
        assert "forms" in fields
        assert "buttons" in fields
        assert "links" in fields

    def test_form_info_type_hints(self):
        """Should have accessible type hints."""
        import dataclasses

        from casare_rpa.infrastructure.ai.page_analyzer import FormInfo

        assert dataclasses.is_dataclass(FormInfo)

        fields = {f.name for f in dataclasses.fields(FormInfo)}
        assert "selector" in fields
        assert "fields" in fields

    def test_form_field_type_hints(self):
        """Should have accessible type hints."""
        import dataclasses

        from casare_rpa.infrastructure.ai.page_analyzer import FormField

        assert dataclasses.is_dataclass(FormField)

        fields = {f.name for f in dataclasses.fields(FormField)}
        assert "name" in fields
        assert "selector" in fields
        assert "field_type" in fields


class TestImportErrorHandling:
    """Tests for graceful import error handling."""

    def test_playwright_mcp_import_no_side_effects(self):
        """Import should not cause side effects."""
        # Import should not start any processes or network connections
        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

        # Creating an instance should also be safe
        client = PlaywrightMCPClient()
        assert client._process is None
        assert client._initialized is False

    def test_page_analyzer_import_no_side_effects(self):
        """Import should not cause side effects."""
        from casare_rpa.infrastructure.ai.page_analyzer import PageAnalyzer

        # Should be able to create analyzer without any dependencies
        analyzer = PageAnalyzer()
        assert analyzer is not None


class TestAsyncMethods:
    """Tests for async method signatures."""

    def test_playwright_client_async_methods(self):
        """Should have proper async methods."""
        import asyncio
        import inspect

        from casare_rpa.infrastructure.ai.playwright_mcp import PlaywrightMCPClient

        client = PlaywrightMCPClient()

        # These should be coroutine functions
        assert inspect.iscoroutinefunction(client.start)
        assert inspect.iscoroutinefunction(client.stop)
        assert inspect.iscoroutinefunction(client.navigate)
        assert inspect.iscoroutinefunction(client.get_snapshot)
        assert inspect.iscoroutinefunction(client.click)
        assert inspect.iscoroutinefunction(client.type_text)
        assert inspect.iscoroutinefunction(client.call_tool)

    def test_fetch_page_context_is_async(self):
        """Should be a coroutine function."""
        import inspect

        from casare_rpa.infrastructure.ai.playwright_mcp import fetch_page_context

        assert inspect.iscoroutinefunction(fetch_page_context)
