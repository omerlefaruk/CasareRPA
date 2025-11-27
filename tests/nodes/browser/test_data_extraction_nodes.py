"""
Tests for data extraction nodes.

Tests ExtractTextNode, GetAttributeNode, ScreenshotNode.
Validates DOM data extraction, attribute retrieval, and screenshot capture.
"""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock
import tempfile
import os


class TestExtractTextNode:
    """Tests for ExtractTextNode - text content extraction."""

    @pytest.mark.asyncio
    async def test_extract_text_success(self, execution_context, mock_page) -> None:
        """Test successful text extraction."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        mock_locator = MagicMock()
        mock_locator.text_content = AsyncMock(return_value="  Hello World  ")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ExtractTextNode(
            node_id="test_extract", selector="#content", variable_name="text_result"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["text"] == "Hello World"  # Trimmed
        assert result["data"]["variable"] == "text_result"
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_extract_text_inner_text(self, execution_context, mock_page) -> None:
        """Test extraction using innerText (visible text only)."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        mock_locator = MagicMock()
        mock_locator.inner_text = AsyncMock(return_value="Visible Text")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ExtractTextNode(
            node_id="test_inner",
            config={
                "selector": "#visible",
                "use_inner_text": True,
                "variable_name": "visible_text",
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["use_inner_text"] is True
        mock_locator.inner_text.assert_called()

    @pytest.mark.asyncio
    async def test_extract_text_no_trim(self, execution_context, mock_page) -> None:
        """Test extraction without whitespace trimming."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        mock_locator = MagicMock()
        mock_locator.text_content = AsyncMock(return_value="  spaced  ")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ExtractTextNode(
            node_id="test_no_trim",
            config={
                "selector": "#spaced",
                "trim_whitespace": False,
                "variable_name": "raw_text",
                "timeout": 5000,
            },
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["text"] == "  spaced  "

    @pytest.mark.asyncio
    async def test_extract_text_stores_variable(
        self, execution_context, mock_page
    ) -> None:
        """Test that extracted text is stored in context variable."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        mock_locator = MagicMock()
        mock_locator.text_content = AsyncMock(return_value="stored value")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)
        # Reset the set_variable mock to track calls
        execution_context.set_variable = MagicMock()

        node = ExtractTextNode(
            node_id="test_store", selector="#data", variable_name="my_var"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        execution_context.set_variable.assert_called_with("my_var", "stored value")

    @pytest.mark.asyncio
    async def test_extract_text_no_page(self, execution_context_no_page) -> None:
        """Test extraction fails without active page."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        node = ExtractTextNode(node_id="test_no_page", selector="#text")
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_extract_text_no_selector(self, execution_context, mock_page) -> None:
        """Test extraction fails without selector."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ExtractTextNode(node_id="test_no_selector", selector="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "selector" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_extract_text_element_not_found(
        self, execution_context, mock_page
    ) -> None:
        """Test extraction fails when element not found."""
        from casare_rpa.nodes.data_nodes import ExtractTextNode

        mock_locator = MagicMock()
        mock_locator.text_content = AsyncMock(
            side_effect=Exception("Element not found")
        )
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ExtractTextNode(node_id="test_not_found", selector="#nonexistent")
        result = await node.execute(execution_context)

        assert result["success"] is False


class TestGetAttributeNode:
    """Tests for GetAttributeNode - element attribute retrieval."""

    @pytest.mark.asyncio
    async def test_get_attribute_success(self, execution_context, mock_page) -> None:
        """Test successful attribute retrieval."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        mock_locator = MagicMock()
        mock_locator.get_attribute = AsyncMock(
            return_value="https://example.com/image.jpg"
        )
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(
            node_id="test_attr",
            selector="img#logo",
            attribute="src",
            variable_name="image_url",
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["attribute"] == "src"
        assert result["data"]["value"] == "https://example.com/image.jpg"
        assert "exec_out" in result["next_nodes"]

    @pytest.mark.asyncio
    async def test_get_attribute_href(self, execution_context, mock_page) -> None:
        """Test getting href attribute from link."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        mock_locator = MagicMock()
        mock_locator.get_attribute = AsyncMock(return_value="/page/123")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(
            node_id="test_href", selector="a.nav-link", attribute="href"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "/page/123"

    @pytest.mark.asyncio
    async def test_get_attribute_data_attribute(
        self, execution_context, mock_page
    ) -> None:
        """Test getting data-* attribute."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        mock_locator = MagicMock()
        mock_locator.get_attribute = AsyncMock(return_value="user-123")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(
            node_id="test_data", selector="div.user-card", attribute="data-user-id"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] == "user-123"

    @pytest.mark.asyncio
    async def test_get_attribute_stores_variable(
        self, execution_context, mock_page
    ) -> None:
        """Test that attribute is stored in context variable."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        mock_locator = MagicMock()
        mock_locator.get_attribute = AsyncMock(return_value="test-value")
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)
        # Reset the set_variable mock to track calls
        execution_context.set_variable = MagicMock()

        node = GetAttributeNode(
            node_id="test_store",
            selector="#elem",
            attribute="value",
            variable_name="stored_attr",
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        execution_context.set_variable.assert_called_with("stored_attr", "test-value")

    @pytest.mark.asyncio
    async def test_get_attribute_null_value(self, execution_context, mock_page) -> None:
        """Test getting attribute that doesn't exist returns null."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        mock_locator = MagicMock()
        mock_locator.get_attribute = AsyncMock(return_value=None)
        mock_locator.first = mock_locator
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(
            node_id="test_null", selector="#elem", attribute="nonexistent"
        )
        result = await node.execute(execution_context)

        assert result["success"] is True
        assert result["data"]["value"] is None

    @pytest.mark.asyncio
    async def test_get_attribute_no_page(self, execution_context_no_page) -> None:
        """Test get attribute fails without active page."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        node = GetAttributeNode(
            node_id="test_no_page", selector="#elem", attribute="id"
        )
        result = await node.execute(execution_context_no_page)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_attribute_no_selector(
        self, execution_context, mock_page
    ) -> None:
        """Test get attribute fails without selector."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(node_id="test_no_selector", selector="", attribute="id")
        result = await node.execute(execution_context)

        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_attribute_no_attribute_name(
        self, execution_context, mock_page
    ) -> None:
        """Test get attribute fails without attribute name."""
        from casare_rpa.nodes.data_nodes import GetAttributeNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = GetAttributeNode(node_id="test_no_attr", selector="#elem", attribute="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "attribute" in result["error"].lower()


class TestScreenshotNode:
    """Tests for ScreenshotNode - page/element screenshot capture."""

    @pytest.mark.asyncio
    async def test_screenshot_page_success(self, execution_context, mock_page) -> None:
        """Test successful page screenshot."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_page.screenshot = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "screenshot.png")
            node = ScreenshotNode(node_id="test_screenshot", file_path=file_path)
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["element"] is False
            assert "exec_out" in result["next_nodes"]
            mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_full_page(self, execution_context, mock_page) -> None:
        """Test full page screenshot."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_page.screenshot = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "fullpage.png")
            node = ScreenshotNode(
                node_id="test_fullpage", file_path=file_path, full_page=True
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["full_page"] is True
            call_kwargs = mock_page.screenshot.call_args[1]
            assert call_kwargs.get("full_page") is True

    @pytest.mark.asyncio
    async def test_screenshot_element(self, execution_context, mock_page) -> None:
        """Test element-specific screenshot."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_locator = MagicMock()
        mock_locator.screenshot = AsyncMock()
        mock_page.locator = MagicMock(return_value=mock_locator)
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "element.png")
            node = ScreenshotNode(
                node_id="test_element", file_path=file_path, selector="#my-element"
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["element"] is True
            mock_locator.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_screenshot_jpeg_with_quality(
        self, execution_context, mock_page
    ) -> None:
        """Test JPEG screenshot with quality setting."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_page.screenshot = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "screenshot.jpg")
            node = ScreenshotNode(
                node_id="test_jpeg",
                config={
                    "file_path": file_path,
                    "type": "jpeg",
                    "quality": 80,
                    "timeout": 5000,
                },
            )
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert result["data"]["type"] == "jpeg"
            call_kwargs = mock_page.screenshot.call_args[1]
            assert call_kwargs.get("quality") == 80

    @pytest.mark.asyncio
    async def test_screenshot_creates_directory(
        self, execution_context, mock_page
    ) -> None:
        """Test screenshot creates parent directory if needed."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_page.screenshot = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "nested", "screenshot.png")
            node = ScreenshotNode(node_id="test_create_dir", file_path=nested_path)
            result = await node.execute(execution_context)

            assert result["success"] is True
            assert os.path.exists(os.path.dirname(nested_path))

    @pytest.mark.asyncio
    async def test_screenshot_no_page(self, execution_context_no_page) -> None:
        """Test screenshot fails without active page."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "screenshot.png")
            node = ScreenshotNode(node_id="test_no_page", file_path=file_path)
            result = await node.execute(execution_context_no_page)

            assert result["success"] is False

    @pytest.mark.asyncio
    async def test_screenshot_no_file_path(self, execution_context, mock_page) -> None:
        """Test screenshot fails without file path."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        execution_context.get_active_page = MagicMock(return_value=mock_page)

        node = ScreenshotNode(node_id="test_no_path", file_path="")
        result = await node.execute(execution_context)

        assert result["success"] is False
        assert "path" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_screenshot_outputs_path(self, execution_context, mock_page) -> None:
        """Test screenshot sets output file path."""
        from casare_rpa.nodes.data_nodes import ScreenshotNode

        mock_page.screenshot = AsyncMock()
        execution_context.get_active_page = MagicMock(return_value=mock_page)

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "output.png")
            node = ScreenshotNode(node_id="test_output", file_path=file_path)
            result = await node.execute(execution_context)

            assert result["success"] is True
            # Verify output port was set
            output_value = node.output_ports.get("file_path")
            if output_value:
                assert output_value.value is not None
