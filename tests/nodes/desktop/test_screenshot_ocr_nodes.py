"""
Comprehensive tests for screenshot and OCR automation nodes.

Tests CaptureScreenshotNode, CaptureElementImageNode, OCRExtractTextNode,
CompareImagesNode from CasareRPA desktop automation layer.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any

from casare_rpa.domain.value_objects.types import NodeStatus


# =============================================================================
# Test Fixtures
# =============================================================================


@pytest.fixture
def mock_image():
    """Create a mock PIL Image object."""
    image = Mock()
    image.save = Mock()
    image.size = (1920, 1080)
    image.mode = "RGB"
    return image


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
    desktop_ctx.capture_screenshot = Mock(return_value=Mock())  # Returns mock image
    desktop_ctx.capture_element_image = Mock(return_value=Mock())
    desktop_ctx.ocr_extract_text = Mock(return_value="Extracted OCR text")
    desktop_ctx.compare_images = Mock(
        return_value={"similarity": 0.95, "is_match": True, "method": "histogram"}
    )

    context.desktop_context = desktop_ctx
    return context


@pytest.fixture
def mock_element():
    """Create a mock desktop element with bounding rectangle."""
    element = Mock()
    element.get_bounding_rect = Mock(
        return_value={"left": 100, "top": 100, "width": 200, "height": 150}
    )
    element._control = Mock()
    element._control.BoundingRectangle = Mock(
        left=100, top=100, right=300, bottom=250, width=lambda: 200, height=lambda: 150
    )
    return element


# =============================================================================
# CaptureScreenshotNode Tests
# =============================================================================


class TestCaptureScreenshotNode:
    """Tests for CaptureScreenshotNode - full screen and region capture."""

    @pytest.mark.asyncio
    async def test_capture_screenshot_full_screen(
        self, mock_execution_context, mock_image
    ):
        """Test capturing full screen screenshot without region."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        mock_execution_context.desktop_context.capture_screenshot.return_value = (
            mock_image
        )

        node = CaptureScreenshotNode(node_id="test_full_capture")
        node.set_input_value("file_path", "C:/screenshots/test.png")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["image"] == mock_image
        assert result["file_path"] == "C:/screenshots/test.png"
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_capture_screenshot_with_region(
        self, mock_execution_context, mock_image
    ):
        """Test capturing screenshot of specific region."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        mock_execution_context.desktop_context.capture_screenshot.return_value = (
            mock_image
        )
        region = {"x": 100, "y": 100, "width": 400, "height": 300}

        node = CaptureScreenshotNode(node_id="test_region_capture")
        node.set_input_value("region", region)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        mock_execution_context.desktop_context.capture_screenshot.assert_called_once()
        call_kwargs = (
            mock_execution_context.desktop_context.capture_screenshot.call_args
        )
        assert call_kwargs[1]["region"] == region

    @pytest.mark.asyncio
    async def test_capture_screenshot_format_png(
        self, mock_execution_context, mock_image
    ):
        """Test screenshot with PNG format configuration."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        mock_execution_context.desktop_context.capture_screenshot.return_value = (
            mock_image
        )

        node = CaptureScreenshotNode(
            node_id="test_format_png", config={"format": "PNG"}
        )
        node.set_input_value("file_path", "test.png")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["format"] == "PNG"

    @pytest.mark.asyncio
    async def test_capture_screenshot_failure(self, mock_execution_context):
        """Test screenshot capture failure returns success=False."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        mock_execution_context.desktop_context.capture_screenshot.return_value = None

        node = CaptureScreenshotNode(node_id="test_capture_fail")

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_capture_screenshot_no_desktop_context(self):
        """Test error when desktop context not available."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        context = Mock()
        context.desktop_context = None

        node = CaptureScreenshotNode(node_id="test_no_context")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(context)

        assert "Desktop context not available" in str(exc_info.value)


# =============================================================================
# CaptureElementImageNode Tests
# =============================================================================


class TestCaptureElementImageNode:
    """Tests for CaptureElementImageNode - element-specific capture."""

    @pytest.mark.asyncio
    async def test_capture_element_image_success(
        self, mock_execution_context, mock_element, mock_image
    ):
        """Test capturing image of specific element."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureElementImageNode,
        )

        mock_execution_context.desktop_context.capture_element_image.return_value = (
            mock_image
        )

        node = CaptureElementImageNode(node_id="test_element_capture")
        node.set_input_value("element", mock_element)
        node.set_input_value("file_path", "element.png")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["image"] == mock_image
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_capture_element_with_padding(
        self, mock_execution_context, mock_element, mock_image
    ):
        """Test element capture with padding configuration."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureElementImageNode,
        )

        mock_execution_context.desktop_context.capture_element_image.return_value = (
            mock_image
        )

        node = CaptureElementImageNode(node_id="test_padding", config={"padding": 10})
        node.set_input_value("element", mock_element)
        node.set_input_value("padding", 20)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["padding"] == 20
        call_kwargs = (
            mock_execution_context.desktop_context.capture_element_image.call_args
        )
        assert call_kwargs[1]["padding"] == 20

    @pytest.mark.asyncio
    async def test_capture_element_missing_element(self, mock_execution_context):
        """Test error when element input is missing."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureElementImageNode,
        )

        node = CaptureElementImageNode(node_id="test_missing_element")

        with pytest.raises(ValueError) as exc_info:
            await node.execute(mock_execution_context)

        assert "Element is required" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_capture_element_failure(self, mock_execution_context, mock_element):
        """Test element capture failure returns success=False."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureElementImageNode,
        )

        mock_execution_context.desktop_context.capture_element_image.return_value = None

        node = CaptureElementImageNode(node_id="test_fail")
        node.set_input_value("element", mock_element)

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert node.status == NodeStatus.ERROR


# =============================================================================
# OCRExtractTextNode Tests
# =============================================================================


class TestOCRExtractTextNode:
    """Tests for OCRExtractTextNode - text extraction from images."""

    @pytest.mark.asyncio
    async def test_ocr_extract_from_image(self, mock_execution_context, mock_image):
        """Test OCR text extraction from image object."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = (
            "Hello World"
        )

        node = OCRExtractTextNode(node_id="test_ocr_image")
        node.set_input_value("image", mock_image)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["text"] == "Hello World"
        assert result["char_count"] == 11
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_ocr_extract_from_path(self, mock_execution_context):
        """Test OCR text extraction from image file path."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = (
            "Text from file"
        )

        node = OCRExtractTextNode(node_id="test_ocr_path")
        node.set_input_value("image_path", "C:/images/document.png")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["text"] == "Text from file"

    @pytest.mark.asyncio
    async def test_ocr_with_region(self, mock_execution_context, mock_image):
        """Test OCR with specific region extraction."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = (
            "Region text"
        )
        region = {"x": 50, "y": 50, "width": 200, "height": 100}

        node = OCRExtractTextNode(node_id="test_ocr_region")
        node.set_input_value("image", mock_image)
        node.set_input_value("region", region)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_kwargs = mock_execution_context.desktop_context.ocr_extract_text.call_args
        assert call_kwargs[1]["region"] == region

    @pytest.mark.asyncio
    async def test_ocr_with_language(self, mock_execution_context, mock_image):
        """Test OCR with specific language configuration."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = "Texto"

        node = OCRExtractTextNode(node_id="test_ocr_lang", config={"language": "spa"})
        node.set_input_value("image", mock_image)

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["language"] == "spa"

    @pytest.mark.asyncio
    async def test_ocr_failure(self, mock_execution_context, mock_image):
        """Test OCR extraction failure returns empty text."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = None

        node = OCRExtractTextNode(node_id="test_ocr_fail")
        node.set_input_value("image", mock_image)

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert node.status == NodeStatus.ERROR


# =============================================================================
# CompareImagesNode Tests
# =============================================================================


class TestCompareImagesNode:
    """Tests for CompareImagesNode - image similarity comparison."""

    @pytest.mark.asyncio
    async def test_compare_images_match(self, mock_execution_context):
        """Test image comparison with matching images."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CompareImagesNode,
        )

        mock_execution_context.desktop_context.compare_images.return_value = {
            "similarity": 0.98,
            "is_match": True,
            "method": "histogram",
        }

        node = CompareImagesNode(node_id="test_compare_match")
        node.set_input_value("image1", Mock())
        node.set_input_value("image2", Mock())

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["similarity"] == 0.98
        assert result["is_match"] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_compare_images_no_match(self, mock_execution_context):
        """Test image comparison with non-matching images."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CompareImagesNode,
        )

        mock_execution_context.desktop_context.compare_images.return_value = {
            "similarity": 0.45,
            "is_match": False,
            "method": "histogram",
        }

        node = CompareImagesNode(
            node_id="test_compare_no_match", config={"threshold": 0.9}
        )
        node.set_input_value("image1", Mock())
        node.set_input_value("image2", Mock())

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        assert result["similarity"] == 0.45
        assert result["is_match"] is False

    @pytest.mark.asyncio
    async def test_compare_images_from_paths(self, mock_execution_context):
        """Test image comparison using file paths."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CompareImagesNode,
        )

        mock_execution_context.desktop_context.compare_images.return_value = {
            "similarity": 0.92,
            "is_match": True,
            "method": "histogram",
        }

        node = CompareImagesNode(node_id="test_compare_paths")
        node.set_input_value("image1_path", "C:/images/ref.png")
        node.set_input_value("image2_path", "C:/images/test.png")

        result = await node.execute(mock_execution_context)

        assert result["success"] is True
        call_kwargs = mock_execution_context.desktop_context.compare_images.call_args
        assert call_kwargs[1]["image1_path"] == "C:/images/ref.png"
        assert call_kwargs[1]["image2_path"] == "C:/images/test.png"

    @pytest.mark.asyncio
    async def test_compare_images_error(self, mock_execution_context):
        """Test image comparison with error response."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CompareImagesNode,
        )

        mock_execution_context.desktop_context.compare_images.return_value = {
            "error": "Failed to load image",
            "similarity": 0.0,
            "is_match": False,
        }

        node = CompareImagesNode(node_id="test_compare_error")
        node.set_input_value("image1", Mock())
        node.set_input_value("image2", Mock())

        result = await node.execute(mock_execution_context)

        assert result["success"] is False
        assert result["error"] == "Failed to load image"
        assert node.status == NodeStatus.ERROR


# =============================================================================
# ExecutionResult Pattern Compliance Tests
# =============================================================================


class TestExecutionResultCompliance:
    """Tests verifying all nodes follow ExecutionResult pattern."""

    @pytest.mark.asyncio
    async def test_capture_screenshot_result_structure(self, mock_execution_context):
        """Test CaptureScreenshotNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CaptureScreenshotNode,
        )

        mock_execution_context.desktop_context.capture_screenshot.return_value = Mock()

        node = CaptureScreenshotNode(node_id="test_result")

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert isinstance(result["success"], bool)
        assert "image" in result
        assert "file_path" in result
        assert "format" in result

    @pytest.mark.asyncio
    async def test_ocr_result_structure(self, mock_execution_context):
        """Test OCRExtractTextNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            OCRExtractTextNode,
        )

        mock_execution_context.desktop_context.ocr_extract_text.return_value = "text"

        node = OCRExtractTextNode(node_id="test_result")
        node.set_input_value("image", Mock())

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "text" in result
        assert "char_count" in result
        assert "language" in result
        assert "engine" in result

    @pytest.mark.asyncio
    async def test_compare_images_result_structure(self, mock_execution_context):
        """Test CompareImagesNode returns proper structure."""
        from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
            CompareImagesNode,
        )

        mock_execution_context.desktop_context.compare_images.return_value = {
            "similarity": 0.9,
            "is_match": True,
            "method": "histogram",
        }

        node = CompareImagesNode(node_id="test_result")
        node.set_input_value("image1", Mock())
        node.set_input_value("image2", Mock())

        result = await node.execute(mock_execution_context)

        assert "success" in result
        assert "similarity" in result
        assert "is_match" in result
        assert "method" in result
        assert "threshold" in result
