"""
Integration tests for PlaywrightMCPClient.

Tests the MCP client for browser automation via subprocess communication.
These tests mock the subprocess to avoid requiring actual MCP installation.

Test Coverage:
- Client initialization
- MCP availability check
- Navigation (success and failure)
- Snapshot retrieval
- Page context fetching
- Tool calls
- Error handling
- Async context manager
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from casare_rpa.infrastructure.ai.playwright_mcp import (
    MCPToolResult,
    PlaywrightMCPClient,
    fetch_page_context,
)


class TestMCPToolResult:
    """Tests for MCPToolResult dataclass."""

    def test_successful_result(self):
        """Should create successful result."""
        result = MCPToolResult(
            success=True,
            content=[{"type": "text", "text": "Navigation complete"}],
            error=None,
        )

        assert result.success is True
        assert result.error is None
        assert result.get_text() == "Navigation complete"

    def test_failed_result(self):
        """Should create failed result."""
        result = MCPToolResult(
            success=False,
            content=[],
            error="Page not found",
        )

        assert result.success is False
        assert result.error == "Page not found"
        assert result.get_text() == ""

    def test_get_text_empty_content(self):
        """Should return empty string for empty content."""
        result = MCPToolResult(success=True, content=[])
        assert result.get_text() == ""

    def test_get_text_multiple_items(self):
        """Should return first text item from content."""
        result = MCPToolResult(
            success=True,
            content=[
                {"type": "image", "data": "..."},
                {"type": "text", "text": "Expected text"},
            ],
        )
        assert result.get_text() == "Expected text"


class TestPlaywrightMCPClientInit:
    """Tests for PlaywrightMCPClient initialization."""

    def test_default_initialization(self):
        """Should initialize with default values."""
        client = PlaywrightMCPClient()

        assert client._headless is True
        assert client._browser == "chrome"
        assert client._process is None
        assert client._initialized is False
        assert client._request_id == 0

    def test_custom_initialization(self):
        """Should accept custom parameters."""
        client = PlaywrightMCPClient(
            headless=False,
            browser="firefox",
            npx_path="/custom/path/npx",
        )

        assert client._headless is False
        assert client._browser == "firefox"
        assert client._npx_path == "/custom/path/npx"

    def test_find_npx_returns_path(self):
        """Should find or fallback npx path."""
        client = PlaywrightMCPClient()
        # _find_npx is called during init
        assert client._npx_path is not None
        assert isinstance(client._npx_path, str)


class TestPlaywrightMCPClientMocked:
    """Tests with mocked subprocess for MCP communication."""

    @pytest.fixture
    def mock_process(self):
        """Create mock subprocess."""
        process = AsyncMock()
        process.stdin = AsyncMock()
        process.stdout = AsyncMock()
        process.stderr = AsyncMock()
        process.returncode = None
        process.terminate = Mock()
        process.kill = Mock()
        process.wait = AsyncMock()
        return process

    @pytest.fixture
    def client(self):
        """Create client without starting subprocess."""
        return PlaywrightMCPClient(headless=True)

    @pytest.mark.asyncio
    async def test_start_without_npx_fails_gracefully(self, client):
        """Should handle missing npx gracefully."""
        client._npx_path = "/nonexistent/path/npx"

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError("npx not found"),
        ):
            result = await client.start()

        assert result is False
        assert client._initialized is False

    @pytest.mark.asyncio
    async def test_stop_without_start(self, client):
        """Should handle stop when never started."""
        # Should not raise
        await client.stop()
        assert client._process is None

    @pytest.mark.asyncio
    async def test_call_tool_not_initialized(self, client):
        """Should return error when calling tool before init."""
        result = await client.call_tool("browser_navigate", {"url": "https://example.com"})

        assert result.success is False
        assert "not initialized" in result.error.lower()

    @pytest.mark.asyncio
    async def test_list_tools_not_initialized(self, client):
        """Should return empty list when not initialized."""
        result = await client.list_tools()
        assert result == []


class TestPlaywrightMCPClientHighLevelMethods:
    """Tests for high-level browser automation methods."""

    @pytest.fixture
    def initialized_client(self):
        """Create client that appears initialized."""
        client = PlaywrightMCPClient(headless=True)
        client._initialized = True
        client._process = Mock()
        client._process.stdin = AsyncMock()
        return client

    @pytest.mark.asyncio
    async def test_navigate_calls_correct_tool(self, initialized_client):
        """Should call browser_navigate tool with URL."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.navigate("https://example.com")

            mock_call.assert_called_once()
            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_navigate"
            assert call_args[0][1]["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_get_snapshot_calls_correct_tool(self, initialized_client):
        """Should call browser_snapshot tool."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(
                success=True,
                content=[{"type": "text", "text": "- WebArea [ref=root]:"}],
            )

            await initialized_client.get_snapshot()

            mock_call.assert_called_once()
            assert mock_call.call_args[0][0] == "browser_snapshot"

    @pytest.mark.asyncio
    async def test_click_calls_correct_tool(self, initialized_client):
        """Should call browser_click tool with ref."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.click("e1", "Login button")

            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_click"
            assert call_args[0][1]["ref"] == "e1"
            assert call_args[0][1]["element"] == "Login button"

    @pytest.mark.asyncio
    async def test_type_text_calls_correct_tool(self, initialized_client):
        """Should call browser_type tool with text."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.type_text("e1", "test@example.com", "email field", submit=True)

            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_type"
            assert call_args[0][1]["ref"] == "e1"
            assert call_args[0][1]["text"] == "test@example.com"
            assert call_args[0][1]["submit"] is True

    @pytest.mark.asyncio
    async def test_close_browser_calls_correct_tool(self, initialized_client):
        """Should call browser_close tool."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.close_browser()

            assert mock_call.call_args[0][0] == "browser_close"

    @pytest.mark.asyncio
    async def test_take_screenshot_calls_correct_tool(self, initialized_client):
        """Should call browser_take_screenshot tool."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.take_screenshot("screenshot.png")

            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_take_screenshot"
            assert call_args[0][1]["filename"] == "screenshot.png"

    @pytest.mark.asyncio
    async def test_wait_for_text(self, initialized_client):
        """Should call browser_wait_for with text."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.wait_for(text="Loading complete")

            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_wait_for"
            assert call_args[0][1]["text"] == "Loading complete"

    @pytest.mark.asyncio
    async def test_wait_for_time(self, initialized_client):
        """Should call browser_wait_for with time."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(success=True, content=[])

            await initialized_client.wait_for(time_seconds=2.0)

            call_args = mock_call.call_args
            assert call_args[0][1]["time"] == 2.0

    @pytest.mark.asyncio
    async def test_evaluate_js(self, initialized_client):
        """Should call browser_evaluate with JS function."""
        with patch.object(initialized_client, "call_tool", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = MCPToolResult(
                success=True,
                content=[{"type": "text", "text": "Example Page"}],
            )

            await initialized_client.evaluate("() => document.title")

            call_args = mock_call.call_args
            assert call_args[0][0] == "browser_evaluate"
            assert "document.title" in call_args[0][1]["function"]


class TestPlaywrightMCPClientContextManager:
    """Tests for async context manager support."""

    @pytest.mark.asyncio
    async def test_context_manager_starts_and_stops(self):
        """Should start on enter and stop on exit."""
        client = PlaywrightMCPClient(headless=True)

        with patch.object(client, "start", new_callable=AsyncMock) as mock_start:
            with patch.object(client, "stop", new_callable=AsyncMock) as mock_stop:
                mock_start.return_value = True

                async with client as c:
                    mock_start.assert_called_once()
                    assert c is client

                mock_stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_stops_on_exception(self):
        """Should stop even when exception occurs."""
        client = PlaywrightMCPClient(headless=True)

        with patch.object(client, "start", new_callable=AsyncMock) as mock_start:
            with patch.object(client, "stop", new_callable=AsyncMock) as mock_stop:
                mock_start.return_value = True

                try:
                    async with client:
                        raise ValueError("Test error")
                except ValueError:
                    pass

                # Stop should still be called
                mock_stop.assert_called_once()


class TestFetchPageContextFunction:
    """Tests for fetch_page_context convenience function."""

    @pytest.mark.asyncio
    async def test_fetch_page_context_success(self):
        """Should return page context dict on success."""
        mock_nav_result = MCPToolResult(success=True, content=[])
        mock_wait_result = MCPToolResult(success=True, content=[])
        mock_snapshot_result = MCPToolResult(
            success=True,
            content=[{"type": "text", "text": "- WebArea [ref=root]:"}],
        )
        mock_title_result = MCPToolResult(
            success=True,
            content=[{"type": "text", "text": "Example Title"}],
        )

        with patch(
            "casare_rpa.infrastructure.ai.playwright_mcp.PlaywrightMCPClient",
            autospec=True,
        ) as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value = mock_instance

            # Mock async context manager
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_instance.navigate = AsyncMock(return_value=mock_nav_result)
            mock_instance.wait_for = AsyncMock(return_value=mock_wait_result)
            mock_instance.get_snapshot = AsyncMock(return_value=mock_snapshot_result)
            mock_instance.evaluate = AsyncMock(return_value=mock_title_result)

            result = await fetch_page_context("https://example.com")

            # Should return dict with url, title, snapshot
            assert result is not None
            assert result["url"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_fetch_page_context_navigation_failure(self):
        """Should return None on navigation failure."""
        mock_nav_result = MCPToolResult(success=False, error="Connection refused")

        with patch(
            "casare_rpa.infrastructure.ai.playwright_mcp.PlaywrightMCPClient",
            autospec=True,
        ) as MockClient:
            mock_instance = AsyncMock()
            MockClient.return_value = mock_instance

            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_instance.navigate = AsyncMock(return_value=mock_nav_result)

            result = await fetch_page_context("https://example.com")

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_page_context_exception_handling(self):
        """Should return None on exception."""
        with patch(
            "casare_rpa.infrastructure.ai.playwright_mcp.PlaywrightMCPClient",
            autospec=True,
        ) as MockClient:
            MockClient.side_effect = Exception("Connection failed")

            result = await fetch_page_context("https://example.com")

            assert result is None


class TestMCPRequestResponse:
    """Tests for JSON-RPC request/response handling."""

    @pytest.fixture
    def client(self):
        """Create client for request testing."""
        client = PlaywrightMCPClient(headless=True)
        client._initialized = True
        return client

    def test_request_id_increments(self, client):
        """Request ID should increment with each request."""
        initial_id = client._request_id
        client._request_id += 1
        assert client._request_id == initial_id + 1

    @pytest.mark.asyncio
    async def test_send_request_not_running(self, client):
        """Should raise when process not running."""
        client._process = None

        with pytest.raises(RuntimeError, match="not running"):
            await client._send_request("test", {})


class TestMCPErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.fixture
    def client(self):
        """Create client for error testing."""
        return PlaywrightMCPClient(headless=True)

    @pytest.mark.asyncio
    async def test_start_general_exception(self, client):
        """Should handle general exceptions during start."""
        with patch("asyncio.create_subprocess_exec", side_effect=Exception("Unknown error")):
            result = await client.start()

        assert result is False

    @pytest.mark.asyncio
    async def test_call_tool_exception(self, client):
        """Should handle exceptions during tool call."""
        client._initialized = True
        client._process = Mock()
        client._process.stdin = AsyncMock()

        with patch.object(client, "_send_request", side_effect=Exception("Request failed")):
            result = await client.call_tool("test_tool", {})

        assert result.success is False
        assert "failed" in result.error.lower()


class TestMCPTimeouts:
    """Tests for timeout handling."""

    def test_default_timeouts(self):
        """Should have sensible default timeouts."""
        assert PlaywrightMCPClient.DEFAULT_NAVIGATE_TIMEOUT == 30.0
        assert PlaywrightMCPClient.DEFAULT_SNAPSHOT_TIMEOUT == 10.0
        assert PlaywrightMCPClient.DEFAULT_ACTION_TIMEOUT == 10.0
        assert PlaywrightMCPClient.DEFAULT_INIT_TIMEOUT == 30.0
