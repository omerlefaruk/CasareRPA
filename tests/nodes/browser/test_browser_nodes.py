"""
Tests for browser control nodes.

Tests LaunchBrowserNode, CloseBrowserNode, NewTabNode, GetAllImagesNode, DownloadFileNode.
Validates ExecutionResult pattern compliance, browser lifecycle, and error handling.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock, patch


class TestLaunchBrowserNode:
    """Tests for LaunchBrowserNode - browser launch and initial navigation."""

    @pytest.mark.asyncio
    async def test_launch_browser_success(self, execution_context):
        """Test successful browser launch with default config."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        with patch("playwright.async_api.async_playwright") as mock_pw:
            # Setup mock playwright
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()

            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_chromium = MagicMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.chromium = mock_chromium
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            node = LaunchBrowserNode(node_id="test_launch", headless=True)
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert "browser" in result["data"]
            assert "page" in result["data"]
            assert "exec_out" in result["next_nodes"]
            assert result["data"]["browser_type"] == "chromium"

    @pytest.mark.asyncio
    async def test_launch_browser_with_url(self, execution_context):
        """Test browser launch with initial URL navigation."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()

            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_chromium = MagicMock()
            mock_chromium.launch = AsyncMock(return_value=mock_browser)

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.chromium = mock_chromium
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            node = LaunchBrowserNode(
                node_id="test_launch_url",
                config={
                    "url": "https://example.com",
                    "browser_type": "chromium",
                    "headless": True,
                },
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            mock_page.goto.assert_called()

    @pytest.mark.asyncio
    async def test_launch_browser_firefox(self, execution_context):
        """Test launching Firefox browser."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()

            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_firefox = MagicMock()
            mock_firefox.launch = AsyncMock(return_value=mock_browser)

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.firefox = mock_firefox
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            node = LaunchBrowserNode(
                node_id="test_firefox", browser_type="firefox", headless=True
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["browser_type"] == "firefox"
            mock_firefox.launch.assert_called()

    @pytest.mark.asyncio
    async def test_launch_browser_webkit(self, execution_context):
        """Test launching WebKit browser."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_browser = MagicMock()
            mock_context = MagicMock()
            mock_page = MagicMock()
            mock_page.goto = AsyncMock()

            mock_context.new_page = AsyncMock(return_value=mock_page)
            mock_browser.new_context = AsyncMock(return_value=mock_context)

            mock_webkit = MagicMock()
            mock_webkit.launch = AsyncMock(return_value=mock_browser)

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.webkit = mock_webkit
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            node = LaunchBrowserNode(
                node_id="test_webkit", browser_type="webkit", headless=True
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["browser_type"] == "webkit"

    @pytest.mark.asyncio
    async def test_launch_browser_failure(self, execution_context):
        """Test browser launch failure handling."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        with patch("playwright.async_api.async_playwright") as mock_pw:
            mock_chromium = MagicMock()
            mock_chromium.launch = AsyncMock(
                side_effect=Exception("Browser launch failed")
            )

            mock_playwright_instance = MagicMock()
            mock_playwright_instance.chromium = mock_chromium
            mock_pw.return_value.start = AsyncMock(
                return_value=mock_playwright_instance
            )

            node = LaunchBrowserNode(node_id="test_fail", headless=True)
            result = await node.execute(execution_context)

            assert result["success"] is False
            assert "error" in result
            assert result["next_nodes"] == []

    def test_validate_config_valid_browser(self):
        """Test config validation with valid browser type."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        node = LaunchBrowserNode(node_id="test_valid", browser_type="chromium")
        is_valid, error = node._validate_config()

        assert is_valid is True
        assert error == ""

    def test_validate_config_invalid_browser(self):
        """Test config validation with invalid browser type."""
        from casare_rpa.nodes.browser_nodes import LaunchBrowserNode

        node = LaunchBrowserNode(node_id="test_invalid")
        node.config["browser_type"] = "invalid_browser"
        is_valid, error = node._validate_config()

        assert is_valid is False
        assert "invalid_browser" in error.lower()


class TestCloseBrowserNode:
    """Tests for CloseBrowserNode - browser cleanup."""

    @pytest.mark.asyncio
    async def test_close_browser_success(self, execution_context, mock_browser):
        """Test successful browser close."""
        from casare_rpa.nodes.browser_nodes import CloseBrowserNode

        execution_context.browser = mock_browser

        node = CloseBrowserNode(node_id="test_close")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert "exec_out" in result["next_nodes"]
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_browser_from_input(self, execution_context, mock_browser):
        """Test closing browser from input port."""
        from casare_rpa.nodes.browser_nodes import CloseBrowserNode

        node = CloseBrowserNode(node_id="test_close_input")
        node.set_input_value = MagicMock()
        node.get_input_value = MagicMock(return_value=mock_browser)

        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_browser.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_browser_no_browser(self, execution_context_no_browser):
        """Test close when no browser exists."""
        from casare_rpa.nodes.browser_nodes import CloseBrowserNode

        node = CloseBrowserNode(node_id="test_no_browser")
        node.get_input_value = MagicMock(return_value=None)

        result = await node.execute(execution_context_no_browser)

        assert result["success"] is False
        assert "error" in result
        assert "no browser" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_close_browser_clears_context(self, execution_context, mock_browser):
        """Test that close browser clears context state."""
        from casare_rpa.nodes.browser_nodes import CloseBrowserNode

        execution_context.browser = mock_browser

        node = CloseBrowserNode(node_id="test_clear")
        await node.execute(execution_context)

        execution_context.clear_pages.assert_called_once()


class TestNewTabNode:
    """Tests for NewTabNode - tab creation."""

    @pytest.mark.asyncio
    async def test_new_tab_success(
        self, execution_context, mock_browser, mock_browser_context, mock_page
    ):
        """Test successful new tab creation."""
        from casare_rpa.nodes.browser_nodes import NewTabNode

        execution_context.browser = mock_browser
        mock_browser.new_context = AsyncMock(return_value=mock_browser_context)
        mock_browser_context.new_page = AsyncMock(return_value=mock_page)

        node = NewTabNode(node_id="test_new_tab", tab_name="new_tab")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["tab_name"] == "new_tab"
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_new_tab_with_url(
        self, execution_context, mock_browser, mock_browser_context, mock_page
    ):
        """Test new tab with URL navigation."""
        from casare_rpa.nodes.browser_nodes import NewTabNode

        execution_context.browser = mock_browser
        mock_browser.new_context = AsyncMock(return_value=mock_browser_context)
        mock_browser_context.new_page = AsyncMock(return_value=mock_page)
        mock_page.goto = AsyncMock()

        node = NewTabNode(
            node_id="test_new_tab_url",
            config={
                "tab_name": "url_tab",
                "url": "https://example.com",
                "timeout": 30000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        mock_page.goto.assert_called()

    @pytest.mark.asyncio
    async def test_new_tab_no_browser(self, execution_context_no_browser):
        """Test new tab when no browser exists."""
        from casare_rpa.nodes.browser_nodes import NewTabNode

        node = NewTabNode(node_id="test_no_browser", tab_name="fail_tab")
        result = await node.execute(execution_context_no_browser)

        assert result["success"] is False
        assert "error" in result

    def test_validate_config_empty_tab_name(self):
        """Test config validation with empty tab name."""
        from casare_rpa.nodes.browser_nodes import NewTabNode

        node = NewTabNode(node_id="test_empty", tab_name="")
        node.config["tab_name"] = ""
        is_valid, error = node._validate_config()

        assert is_valid is False
        assert "empty" in error.lower()


class TestGetAllImagesNode:
    """Tests for GetAllImagesNode - image extraction from page."""

    @pytest.mark.asyncio
    async def test_get_all_images_success(self, execution_context, mock_page):
        """Test successful image extraction."""
        from casare_rpa.nodes.browser_nodes import GetAllImagesNode

        mock_images = [
            {
                "url": "https://example.com/image1.jpg",
                "width": 100,
                "height": 100,
                "alt": "",
                "type": "img",
            },
            {
                "url": "https://example.com/image2.png",
                "width": 200,
                "height": 200,
                "alt": "test",
                "type": "img",
            },
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_images)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAllImagesNode(node_id="test_images")
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 2
        assert len(result["data"]["images"]) == 2
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_get_all_images_with_size_filter(self, execution_context, mock_page):
        """Test image extraction with minimum size filter."""
        from casare_rpa.nodes.browser_nodes import GetAllImagesNode

        mock_images = [
            {
                "url": "https://example.com/small.jpg",
                "width": 50,
                "height": 50,
                "alt": "",
                "type": "img",
            },
            {
                "url": "https://example.com/large.jpg",
                "width": 200,
                "height": 200,
                "alt": "",
                "type": "img",
            },
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_images)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAllImagesNode(
            node_id="test_filter", config={"min_width": 100, "min_height": 100}
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 1

    @pytest.mark.asyncio
    async def test_get_all_images_with_type_filter(self, execution_context, mock_page):
        """Test image extraction with file type filter."""
        from casare_rpa.nodes.browser_nodes import GetAllImagesNode

        mock_images = [
            {
                "url": "https://example.com/image.jpg",
                "width": 100,
                "height": 100,
                "alt": "",
                "type": "img",
            },
            {
                "url": "https://example.com/image.png",
                "width": 100,
                "height": 100,
                "alt": "",
                "type": "img",
            },
            {
                "url": "https://example.com/image.gif",
                "width": 100,
                "height": 100,
                "alt": "",
                "type": "img",
            },
        ]
        mock_page.evaluate = AsyncMock(return_value=mock_images)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAllImagesNode(
            node_id="test_type_filter", config={"file_types": "jpg,png"}
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["count"] == 2

    @pytest.mark.asyncio
    async def test_get_all_images_no_page(self, execution_context_no_page):
        """Test image extraction with no active page."""
        from casare_rpa.nodes.browser_nodes import GetAllImagesNode

        node = GetAllImagesNode(node_id="test_no_page")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False
        assert "error" in result


class TestDownloadFileNode:
    """Tests for DownloadFileNode - file download functionality."""

    @pytest.mark.asyncio
    async def test_download_file_missing_url(self, execution_context):
        """Test download fails without URL."""
        from casare_rpa.nodes.browser_nodes import DownloadFileNode

        node = DownloadFileNode(node_id="test_no_url")
        node.get_input_value = MagicMock(return_value=None)
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "url" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_download_file_with_browser(self, execution_context, mock_page):
        """Test download using browser context."""
        from casare_rpa.nodes.browser_nodes import DownloadFileNode
        import tempfile
        import os

        mock_response = MagicMock()
        mock_response.body = AsyncMock(return_value=b"test content")
        mock_page.request = MagicMock()
        mock_page.request.get = AsyncMock(return_value=mock_response)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            save_path = os.path.join(tmpdir, "test.txt")
            node = DownloadFileNode(
                node_id="test_browser_download",
                config={"save_path": save_path, "use_browser": True},
            )
            node.get_input_value = MagicMock(
                side_effect=lambda k: "https://example.com/file.txt"
                if k == "url"
                else None
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["size"] == 12  # len("test content")
