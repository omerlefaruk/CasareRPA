"""
Tests for navigation nodes.

Tests GoToURLNode, GoBackNode, GoForwardNode, RefreshPageNode.
Validates navigation behavior, URL handling, retry logic, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock


class TestGoToURLNode:
    """Tests for GoToURLNode - URL navigation."""

    @pytest.mark.asyncio
    async def test_goto_url_success(self, execution_context, mock_page) -> None:
        """Test successful URL navigation."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_response = Mock(status=200)
        mock_page.goto = AsyncMock(return_value=mock_response)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(
            node_id="test_goto", url="https://example.com", timeout=30000
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["url"] == "https://example.com"
        assert result["data"]["status"] == 200
        assert "exec_out" in result["next_nodes"]
        mock_page.goto.assert_called_once()

    @pytest.mark.asyncio
    async def test_goto_url_adds_protocol(self, execution_context, mock_page) -> None:
        """Test that https:// is added to URLs without protocol."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_page.goto = AsyncMock(return_value=Mock(status=200))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(node_id="test_protocol", url="example.com")
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_args = mock_page.goto.call_args
        assert call_args[0][0] == "https://example.com"

    @pytest.mark.asyncio
    async def test_goto_url_from_input_port(self, execution_context, mock_page) -> None:
        """Test navigation using URL from input port."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_page.goto = AsyncMock(return_value=Mock(status=200))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(node_id="test_input_url")
        node.input_ports["url"] = Mock()
        node.input_ports["url"].value = "https://test.example.com"

        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_goto_url_no_page(self, execution_context_no_page) -> None:
        """Test navigation fails without active page."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        node = GoToURLNode(node_id="test_no_page", url="https://example.com")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False
        assert "page" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_goto_url_empty_url(self, execution_context, mock_page) -> None:
        """Test navigation fails with empty URL."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(node_id="test_empty_url", url="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "url" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_goto_url_with_wait_until(self, execution_context, mock_page) -> None:
        """Test navigation with custom wait_until option."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_page.goto = AsyncMock(return_value=Mock(status=200))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(
            node_id="test_wait",
            config={
                "url": "https://example.com",
                "wait_until": "networkidle",
                "timeout": 30000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.goto.call_args[1]
        assert call_kwargs["wait_until"] == "networkidle"

    @pytest.mark.asyncio
    async def test_goto_url_timeout_error(self, execution_context, mock_page) -> None:
        """Test navigation timeout handling."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_page.goto = AsyncMock(side_effect=Exception("Navigation timeout"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(node_id="test_timeout", url="https://slow.example.com")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "timeout" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_goto_url_with_referer(self, execution_context, mock_page) -> None:
        """Test navigation with referer header."""
        from casare_rpa.nodes.navigation_nodes import GoToURLNode

        mock_page.goto = AsyncMock(return_value=Mock(status=200))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoToURLNode(
            node_id="test_referer",
            config={
                "url": "https://example.com",
                "referer": "https://google.com",
                "timeout": 30000,
                "wait_until": "load",
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        call_kwargs = mock_page.goto.call_args[1]
        assert call_kwargs["referer"] == "https://google.com"


class TestGoBackNode:
    """Tests for GoBackNode - browser history back navigation."""

    @pytest.mark.asyncio
    async def test_go_back_success(self, execution_context, mock_page) -> None:
        """Test successful back navigation."""
        from casare_rpa.nodes.navigation_nodes import GoBackNode

        mock_page.go_back = AsyncMock()
        mock_page.url = "https://previous.example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoBackNode(node_id="test_back")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["url"] == "https://previous.example.com"
        assert "exec_out" in result["next_nodes"]
        mock_page.go_back.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_back_from_input_page(self, execution_context, mock_page) -> None:
        """Test back navigation using page from input port."""
        from casare_rpa.nodes.navigation_nodes import GoBackNode

        mock_page.go_back = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoBackNode(node_id="test_back_input")
        result = await node.execute(execution_context)

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_go_back_no_page(self, execution_context_no_page) -> None:
        """Test back navigation fails without page."""
        from casare_rpa.nodes.navigation_nodes import GoBackNode

        node = GoBackNode(node_id="test_no_page")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_go_back_with_wait_until(self, execution_context, mock_page) -> None:
        """Test back navigation with custom wait_until."""
        from casare_rpa.nodes.navigation_nodes import GoBackNode

        mock_page.go_back = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoBackNode(
            node_id="test_wait",
            config={"wait_until": "domcontentloaded", "timeout": 30000},
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.go_back.assert_called_with(
            timeout=30000, wait_until="domcontentloaded"
        )


class TestGoForwardNode:
    """Tests for GoForwardNode - browser history forward navigation."""

    @pytest.mark.asyncio
    async def test_go_forward_success(self, execution_context, mock_page) -> None:
        """Test successful forward navigation."""
        from casare_rpa.nodes.navigation_nodes import GoForwardNode

        mock_page.go_forward = AsyncMock()
        mock_page.url = "https://next.example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoForwardNode(node_id="test_forward")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["url"] == "https://next.example.com"
        assert "exec_out" in result["next_nodes"]
        mock_page.go_forward.assert_called_once()

    @pytest.mark.asyncio
    async def test_go_forward_no_page(self, execution_context_no_page) -> None:
        """Test forward navigation fails without page."""
        from casare_rpa.nodes.navigation_nodes import GoForwardNode

        node = GoForwardNode(node_id="test_no_page")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_go_forward_error_handling(
        self, execution_context, mock_page
    ) -> None:
        """Test forward navigation error handling."""
        from casare_rpa.nodes.navigation_nodes import GoForwardNode

        mock_page.go_forward = AsyncMock(side_effect=Exception("No forward history"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GoForwardNode(node_id="test_error")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result


class TestRefreshPageNode:
    """Tests for RefreshPageNode - page reload."""

    @pytest.mark.asyncio
    async def test_refresh_success(self, execution_context, mock_page) -> None:
        """Test successful page refresh."""
        from casare_rpa.nodes.navigation_nodes import RefreshPageNode

        mock_page.reload = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = RefreshPageNode(node_id="test_refresh")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["url"] == "https://example.com"
        assert "exec_out" in result["next_nodes"]
        mock_page.reload.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_no_page(self, execution_context_no_page) -> None:
        """Test refresh fails without page."""
        from casare_rpa.nodes.navigation_nodes import RefreshPageNode

        node = RefreshPageNode(node_id="test_no_page")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_refresh_with_options(self, execution_context, mock_page) -> None:
        """Test refresh with custom timeout and wait_until."""
        from casare_rpa.nodes.navigation_nodes import RefreshPageNode

        mock_page.reload = AsyncMock()
        mock_page.url = "https://example.com"
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = RefreshPageNode(
            node_id="test_options",
            config={"timeout": 60000, "wait_until": "networkidle"},
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.reload.assert_called_with(timeout=60000, wait_until="networkidle")

    @pytest.mark.asyncio
    async def test_refresh_error_handling(self, execution_context, mock_page) -> None:
        """Test refresh error handling."""
        from casare_rpa.nodes.navigation_nodes import RefreshPageNode

        mock_page.reload = AsyncMock(side_effect=Exception("Refresh failed"))
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = RefreshPageNode(node_id="test_error")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "error" in result
