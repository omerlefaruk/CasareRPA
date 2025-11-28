"""
Screenshot and OCR Nodes for CasareRPA

Provides nodes for capturing screenshots and extracting text:
- CaptureScreenshotNode: Capture full screen or region
- CaptureElementImageNode: Capture image of specific element
- OCRExtractTextNode: Extract text from image using OCR
- CompareImagesNode: Compare two images for similarity
"""

from typing import Any, Dict

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, NodeStatus
from casare_rpa.nodes.utils.type_converters import safe_int


class CaptureScreenshotNode(BaseNode):
    """
    Node to capture a screenshot of the screen or a specific region.

    Inputs:
        - file_path: Path to save screenshot (optional)
        - region: Dict with x, y, width, height for specific region (optional)

    Config:
        - format: Image format (PNG, JPEG, BMP)

    Outputs:
        - image: PIL Image object
        - file_path: Path where image was saved (if specified)
        - success: Whether capture succeeded
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Capture Screenshot",
    ):
        default_config = {"format": "PNG"}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "CaptureScreenshotNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("file_path", DataType.STRING, "Save path (optional)")
        self.add_input_port("region", DataType.ANY, "Region dict (optional)")
        self.add_output_port("image", DataType.ANY, "Captured image")
        self.add_output_port("file_path", DataType.STRING, "Saved file path")
        self.add_output_port("success", DataType.BOOLEAN, "Capture succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute screenshot capture"""
        file_path = self.get_input_value("file_path")
        region = self.get_input_value("region")
        format_type = self.config.get("format", "PNG")

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value") and file_path:
            file_path = context.resolve_value(file_path)

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        image = desktop_ctx.capture_screenshot(
            file_path=file_path, region=region, format=format_type
        )

        success = image is not None

        self.set_output_value("image", image)
        self.set_output_value("file_path", file_path if success else None)
        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.ERROR

        return {
            "success": success,
            "image": image,
            "file_path": file_path,
            "format": format_type,
        }


class CaptureElementImageNode(BaseNode):
    """
    Node to capture an image of a specific desktop element.

    Inputs:
        - element: DesktopElement to capture
        - file_path: Path to save image (optional)
        - padding: Extra pixels around element bounds

    Config:
        - format: Image format (PNG, JPEG, BMP)

    Outputs:
        - image: PIL Image object
        - file_path: Path where image was saved (if specified)
        - success: Whether capture succeeded
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Capture Element Image",
    ):
        default_config = {"format": "PNG", "padding": 0}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "CaptureElementImageNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("element", DataType.ANY, "Element to capture")
        self.add_input_port("file_path", DataType.STRING, "Save path (optional)")
        self.add_input_port("padding", DataType.INTEGER, "Padding pixels")
        self.add_output_port("image", DataType.ANY, "Captured image")
        self.add_output_port("file_path", DataType.STRING, "Saved file path")
        self.add_output_port("success", DataType.BOOLEAN, "Capture succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute element image capture"""
        element = self.get_input_value("element")
        file_path = self.get_input_value("file_path")
        padding = self.get_input_value("padding") or self.config.get("padding", 0)
        format_type = self.config.get("format", "PNG")

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value") and file_path:
            file_path = context.resolve_value(file_path)

        padding = safe_int(padding, 0)

        if not element:
            raise ValueError("Element is required")

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        image = desktop_ctx.capture_element_image(
            element=element,
            file_path=file_path,
            padding=int(padding),
            format=format_type,
        )

        success = image is not None

        self.set_output_value("image", image)
        self.set_output_value("file_path", file_path if success else None)
        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.ERROR

        return {
            "success": success,
            "image": image,
            "file_path": file_path,
            "padding": padding,
            "format": format_type,
        }


class OCRExtractTextNode(BaseNode):
    """
    Node to extract text from an image using OCR.

    Inputs:
        - image: PIL Image object (optional)
        - image_path: Path to image file (optional)
        - region: Dict with x, y, width, height for specific region (optional)

    Config:
        - engine: OCR engine ('auto', 'rapidocr', 'tesseract', 'winocr')
        - language: Tesseract language code (default: eng)
        - config: Additional Tesseract config options

    Outputs:
        - text: Extracted text string
        - engine_used: Which OCR engine was used
        - success: Whether extraction succeeded
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "OCR Extract Text",
    ):
        default_config = {"engine": "auto", "language": "eng", "config": ""}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "OCRExtractTextNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("image", DataType.ANY, "Image object (optional)")
        self.add_input_port("image_path", DataType.STRING, "Image file path (optional)")
        self.add_input_port("region", DataType.ANY, "Region dict (optional)")
        self.add_output_port("text", DataType.STRING, "Extracted text")
        self.add_output_port("engine_used", DataType.STRING, "OCR engine used")
        self.add_output_port("success", DataType.BOOLEAN, "Extraction succeeded")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute OCR text extraction"""
        image = self.get_input_value("image")
        image_path = self.get_input_value("image_path")
        region = self.get_input_value("region")
        engine = self.config.get("engine", "auto")
        language = self.config.get("language", "eng")
        ocr_config = self.config.get("config", "")

        # Resolve {{variable}} patterns
        if hasattr(context, "resolve_value"):
            if image_path:
                image_path = context.resolve_value(image_path)
            language = context.resolve_value(language)
            ocr_config = context.resolve_value(ocr_config)

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        text = desktop_ctx.ocr_extract_text(
            image=image,
            image_path=image_path,
            region=region,
            language=language,
            config=ocr_config,
            engine=engine,
        )

        success = text is not None

        self.set_output_value("text", text or "")
        self.set_output_value("engine_used", engine)
        self.set_output_value("success", success)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.ERROR

        return {
            "success": success,
            "text": text,
            "language": language,
            "engine": engine,
            "char_count": len(text) if text else 0,
        }


class CompareImagesNode(BaseNode):
    """
    Node to compare two images and return similarity metrics.

    Inputs:
        - image1: First PIL Image object (optional)
        - image2: Second PIL Image object (optional)
        - image1_path: Path to first image file (optional)
        - image2_path: Path to second image file (optional)

    Config:
        - method: Comparison method ('ssim', 'histogram', 'pixel')
        - threshold: Similarity threshold for match (0.0 to 1.0)

    Outputs:
        - similarity: Similarity score (0.0 to 1.0)
        - is_match: Whether images match based on threshold
        - method: Comparison method used
    """

    def __init__(
        self,
        node_id: str = None,
        config: Dict[str, Any] = None,
        name: str = "Compare Images",
    ):
        default_config = {"method": "histogram", "threshold": 0.9}
        if config:
            default_config.update(config)
        super().__init__(node_id, default_config)
        self.name = name
        self.node_type = "CompareImagesNode"

    def _define_ports(self):
        """Define input and output ports"""
        self.add_input_port("image1", DataType.ANY, "First image")
        self.add_input_port("image2", DataType.ANY, "Second image")
        self.add_input_port("image1_path", DataType.STRING, "First image path")
        self.add_input_port("image2_path", DataType.STRING, "Second image path")
        self.add_output_port("similarity", DataType.FLOAT, "Similarity score")
        self.add_output_port("is_match", DataType.BOOLEAN, "Images match")
        self.add_output_port("method", DataType.STRING, "Comparison method")

    async def execute(self, context) -> Dict[str, Any]:
        """Execute image comparison"""
        image1 = self.get_input_value("image1")
        image2 = self.get_input_value("image2")
        image1_path = self.get_input_value("image1_path")
        image2_path = self.get_input_value("image2_path")
        method = self.config.get("method", "histogram")
        threshold = self.config.get("threshold", 0.9)

        desktop_ctx = getattr(context, "desktop_context", None)
        if desktop_ctx is None:
            raise ValueError("Desktop context not available")

        result = desktop_ctx.compare_images(
            image1=image1,
            image2=image2,
            image1_path=image1_path,
            image2_path=image2_path,
            method=method,
            threshold=float(threshold),
        )

        success = "error" not in result
        similarity = result.get("similarity", 0.0)
        is_match = result.get("is_match", False)
        used_method = result.get("method", method)

        self.set_output_value("similarity", similarity)
        self.set_output_value("is_match", is_match)
        self.set_output_value("method", used_method)
        self.status = NodeStatus.SUCCESS if success else NodeStatus.ERROR

        return {
            "success": success,
            "similarity": similarity,
            "is_match": is_match,
            "method": used_method,
            "threshold": threshold,
            "error": result.get("error"),
        }
