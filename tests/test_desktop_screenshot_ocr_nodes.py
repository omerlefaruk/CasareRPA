"""
Unit tests for Desktop Screenshot & OCR Nodes

Tests CaptureScreenshotNode, CaptureElementImageNode, OCRExtractTextNode,
CompareImagesNode
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from casare_rpa.nodes.desktop_nodes import (
    CaptureScreenshotNode,
    CaptureElementImageNode,
    OCRExtractTextNode,
    CompareImagesNode,
)
from casare_rpa.desktop import DesktopContext, DesktopElement
from casare_rpa.core.execution_context import ExecutionContext
from casare_rpa.core.types import NodeStatus


class MockImage:
    """Mock PIL Image for testing"""
    def __init__(self, width=100, height=100):
        self.width = width
        self.height = height
        self.size = (width, height)
        self.mode = "RGB"

    def save(self, path, format=None):
        pass

    def histogram(self):
        return [0] * 768


class MockDesktopElement:
    """Mock DesktopElement for testing"""
    def __init__(self, name="MockElement"):
        self._control = Mock()
        self._control.Name = name
        self._control.BoundingRectangle = Mock()
        self._control.BoundingRectangle.left = 100
        self._control.BoundingRectangle.top = 100
        self._control.BoundingRectangle.right = 200
        self._control.BoundingRectangle.bottom = 200


class TestCaptureScreenshotNode:
    """Test suite for CaptureScreenshotNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = CaptureScreenshotNode("screenshot_1", name="Capture Screenshot")
        assert node.node_id == "screenshot_1"
        assert node.name == "Capture Screenshot"
        assert node.node_type == "CaptureScreenshotNode"

    def test_default_config(self):
        """Test default configuration"""
        node = CaptureScreenshotNode("screenshot_2")
        assert node.config.get("format") == "PNG"

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = CaptureScreenshotNode("screenshot_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_capture_full_screen_success(self):
        """Test capturing full screen"""
        node = CaptureScreenshotNode("screenshot_4")
        context = ExecutionContext()

        mock_image = MockImage()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_screenshot.return_value = mock_image
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['image'] == mock_image
        assert node.status == NodeStatus.SUCCESS
        mock_desktop_ctx.capture_screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_screenshot_with_file_path(self):
        """Test capturing screenshot with file path"""
        node = CaptureScreenshotNode("screenshot_5")
        context = ExecutionContext()

        node.set_input_value("file_path", "C:/temp/screenshot.png")

        mock_image = MockImage()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_screenshot.return_value = mock_image
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['file_path'] == "C:/temp/screenshot.png"

    @pytest.mark.asyncio
    async def test_capture_screenshot_with_region(self):
        """Test capturing screenshot with region"""
        node = CaptureScreenshotNode("screenshot_6")
        context = ExecutionContext()

        region = {"x": 100, "y": 100, "width": 200, "height": 200}
        node.set_input_value("region", region)

        mock_image = MockImage()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_screenshot.return_value = mock_image
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        mock_desktop_ctx.capture_screenshot.assert_called_once_with(
            file_path=None,
            region=region,
            format="PNG"
        )

    @pytest.mark.asyncio
    async def test_capture_screenshot_failure(self):
        """Test capturing screenshot failure"""
        node = CaptureScreenshotNode("screenshot_7")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_screenshot.return_value = None
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is False
        assert node.status == NodeStatus.ERROR


class TestCaptureElementImageNode:
    """Test suite for CaptureElementImageNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = CaptureElementImageNode("elem_img_1", name="Capture Element Image")
        assert node.node_id == "elem_img_1"
        assert node.name == "Capture Element Image"
        assert node.node_type == "CaptureElementImageNode"

    def test_default_config(self):
        """Test default configuration"""
        node = CaptureElementImageNode("elem_img_2")
        assert node.config.get("format") == "PNG"
        assert node.config.get("padding") == 0

    @pytest.mark.asyncio
    async def test_missing_element_raises_error(self):
        """Test that missing element raises ValueError"""
        node = CaptureElementImageNode("elem_img_3")
        context = ExecutionContext()

        mock_desktop_ctx = Mock(spec=DesktopContext)
        context.desktop_context = mock_desktop_ctx

        with pytest.raises(ValueError, match="Element is required"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_capture_element_image_success(self):
        """Test capturing element image success"""
        node = CaptureElementImageNode("elem_img_4")
        context = ExecutionContext()

        mock_element = MockDesktopElement()
        node.set_input_value("element", mock_element)

        mock_image = MockImage()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_element_image.return_value = mock_image
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['image'] == mock_image
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_capture_element_image_with_padding(self):
        """Test capturing element image with padding"""
        node = CaptureElementImageNode("elem_img_5", config={"padding": 10})
        context = ExecutionContext()

        mock_element = MockDesktopElement()
        node.set_input_value("element", mock_element)

        mock_image = MockImage()
        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.capture_element_image.return_value = mock_image
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['padding'] == 10


class TestOCRExtractTextNode:
    """Test suite for OCRExtractTextNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = OCRExtractTextNode("ocr_1", name="OCR Extract Text")
        assert node.node_id == "ocr_1"
        assert node.name == "OCR Extract Text"
        assert node.node_type == "OCRExtractTextNode"

    def test_default_config(self):
        """Test default configuration"""
        node = OCRExtractTextNode("ocr_2")
        assert node.config.get("language") == "eng"
        assert node.config.get("config") == ""

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = OCRExtractTextNode("ocr_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_ocr_extract_text_success(self):
        """Test OCR text extraction success"""
        node = OCRExtractTextNode("ocr_4")
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Hello World"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['text'] == "Hello World"
        assert result['char_count'] == 11
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_ocr_extract_text_from_path(self):
        """Test OCR text extraction from image path"""
        node = OCRExtractTextNode("ocr_5")
        context = ExecutionContext()

        node.set_input_value("image_path", "C:/temp/image.png")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Test text"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['text'] == "Test text"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_failure(self):
        """Test OCR text extraction failure"""
        node = OCRExtractTextNode("ocr_6")
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = None
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is False
        assert node.status == NodeStatus.ERROR

    @pytest.mark.asyncio
    async def test_ocr_with_custom_language(self):
        """Test OCR with custom language setting"""
        node = OCRExtractTextNode("ocr_7", config={"language": "deu"})
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Hallo Welt"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['language'] == "deu"

    @pytest.mark.asyncio
    async def test_ocr_with_rapidocr_engine(self):
        """Test OCR with RapidOCR engine selection"""
        node = OCRExtractTextNode("ocr_8", config={"engine": "rapidocr"})
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "RapidOCR Text"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['text'] == "RapidOCR Text"
        assert result['engine'] == "rapidocr"
        mock_desktop_ctx.ocr_extract_text.assert_called_once_with(
            image=mock_image,
            image_path=None,
            region=None,
            language="eng",
            config="",
            engine="rapidocr"
        )

    @pytest.mark.asyncio
    async def test_ocr_with_tesseract_engine(self):
        """Test OCR with Tesseract engine selection"""
        node = OCRExtractTextNode("ocr_9", config={"engine": "tesseract"})
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Tesseract Text"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['engine'] == "tesseract"

    @pytest.mark.asyncio
    async def test_ocr_with_winocr_engine(self):
        """Test OCR with Windows OCR engine selection"""
        node = OCRExtractTextNode("ocr_10", config={"engine": "winocr"})
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "WinOCR Text"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['engine'] == "winocr"

    @pytest.mark.asyncio
    async def test_ocr_with_auto_engine(self):
        """Test OCR with auto engine selection (default)"""
        node = OCRExtractTextNode("ocr_11")
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Auto Text"
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['engine'] == "auto"

    @pytest.mark.asyncio
    async def test_ocr_engine_used_output(self):
        """Test that engine_used output is set correctly"""
        node = OCRExtractTextNode("ocr_12", config={"engine": "rapidocr"})
        context = ExecutionContext()

        mock_image = MockImage()
        node.set_input_value("image", mock_image)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.ocr_extract_text.return_value = "Test"
        context.desktop_context = mock_desktop_ctx

        await node.execute(context)

        engine_used = node.get_output_value("engine_used")
        assert engine_used == "rapidocr"

    def test_ocr_default_engine_config(self):
        """Test that default engine config is 'auto'"""
        node = OCRExtractTextNode("ocr_13")
        assert node.config.get("engine") == "auto"


class TestCompareImagesNode:
    """Test suite for CompareImagesNode"""

    def test_node_initialization(self):
        """Test that node initializes correctly"""
        node = CompareImagesNode("compare_1", name="Compare Images")
        assert node.node_id == "compare_1"
        assert node.name == "Compare Images"
        assert node.node_type == "CompareImagesNode"

    def test_default_config(self):
        """Test default configuration"""
        node = CompareImagesNode("compare_2")
        assert node.config.get("method") == "histogram"
        assert node.config.get("threshold") == 0.9

    @pytest.mark.asyncio
    async def test_missing_desktop_context_raises_error(self):
        """Test that missing desktop context raises ValueError"""
        node = CompareImagesNode("compare_3")
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Desktop context not available"):
            await node.execute(context)

    @pytest.mark.asyncio
    async def test_compare_images_match(self):
        """Test comparing images that match"""
        node = CompareImagesNode("compare_4", config={"threshold": 0.8})
        context = ExecutionContext()

        mock_image1 = MockImage()
        mock_image2 = MockImage()
        node.set_input_value("image1", mock_image1)
        node.set_input_value("image2", mock_image2)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.compare_images.return_value = {
            "similarity": 0.95,
            "is_match": True,
            "method": "histogram",
            "threshold": 0.8
        }
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['similarity'] == 0.95
        assert result['is_match'] is True
        assert node.status == NodeStatus.SUCCESS

    @pytest.mark.asyncio
    async def test_compare_images_no_match(self):
        """Test comparing images that don't match"""
        node = CompareImagesNode("compare_5", config={"threshold": 0.9})
        context = ExecutionContext()

        mock_image1 = MockImage()
        mock_image2 = MockImage()
        node.set_input_value("image1", mock_image1)
        node.set_input_value("image2", mock_image2)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.compare_images.return_value = {
            "similarity": 0.5,
            "is_match": False,
            "method": "histogram",
            "threshold": 0.9
        }
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True
        assert result['similarity'] == 0.5
        assert result['is_match'] is False

    @pytest.mark.asyncio
    async def test_compare_images_from_paths(self):
        """Test comparing images from file paths"""
        node = CompareImagesNode("compare_6")
        context = ExecutionContext()

        node.set_input_value("image1_path", "C:/temp/image1.png")
        node.set_input_value("image2_path", "C:/temp/image2.png")

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.compare_images.return_value = {
            "similarity": 0.85,
            "is_match": False,
            "method": "histogram",
            "threshold": 0.9
        }
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_compare_images_with_ssim_method(self):
        """Test comparing images with SSIM method"""
        node = CompareImagesNode("compare_7", config={"method": "ssim"})
        context = ExecutionContext()

        mock_image1 = MockImage()
        mock_image2 = MockImage()
        node.set_input_value("image1", mock_image1)
        node.set_input_value("image2", mock_image2)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.compare_images.return_value = {
            "similarity": 0.92,
            "is_match": True,
            "method": "ssim",
            "threshold": 0.9
        }
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['method'] == "ssim"

    @pytest.mark.asyncio
    async def test_compare_images_error(self):
        """Test comparing images with error"""
        node = CompareImagesNode("compare_8")
        context = ExecutionContext()

        mock_image1 = MockImage()
        node.set_input_value("image1", mock_image1)

        mock_desktop_ctx = Mock(spec=DesktopContext)
        mock_desktop_ctx.compare_images.return_value = {
            "similarity": 0.0,
            "is_match": False,
            "method": "histogram",
            "error": "Missing second image"
        }
        context.desktop_context = mock_desktop_ctx

        result = await node.execute(context)

        assert result['success'] is False
        assert node.status == NodeStatus.ERROR
