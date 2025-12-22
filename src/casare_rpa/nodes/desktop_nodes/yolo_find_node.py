"""
YOLO Find Element Node - Find desktop elements using YOLOv8 detection.

Uses YOLOv8 object detection for DOM-independent element detection.
Works in VDI/Citrix environments without accessibility APIs.

Usage in workflow:
    1. Optionally connect to active window
    2. Specify element type to find (button, input, etc.)
    3. Get element location for subsequent actions
"""

from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import DataType, NodeStatus
from casare_rpa.infrastructure.execution import ExecutionContext
from casare_rpa.nodes.desktop_nodes.desktop_base import DesktopNodeBase
from casare_rpa.nodes.desktop_nodes.properties import (
    TIMEOUT_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)


# =============================================================================
# Property Constants
# =============================================================================

ELEMENT_TYPE_PROP = PropertyDef(
    "element_type",
    PropertyType.CHOICE,
    default="button",
    choices=[
        "button",
        "input",
        "checkbox",
        "radio",
        "dropdown",
        "link",
        "icon",
        "text",
        "menu",
        "tab",
        "toggle",
    ],
    label="Element Type",
    tooltip="Type of UI element to detect",
)

ELEMENT_INDEX_PROP = PropertyDef(
    "element_index",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Element Index",
    tooltip="Index of element to select (0 = first, 1 = second, etc.)",
)

CONFIDENCE_THRESHOLD_PROP = PropertyDef(
    "confidence_threshold",
    PropertyType.NUMBER,
    default=0.5,
    min_value=0.0,
    max_value=1.0,
    label="Confidence Threshold",
    tooltip="Minimum confidence score for detection (0.0-1.0)",
)

REGION_X_PROP = PropertyDef(
    "region_x",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Region X",
    tooltip="X coordinate of search region (0 for full screen)",
    tab="advanced",
)

REGION_Y_PROP = PropertyDef(
    "region_y",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Region Y",
    tooltip="Y coordinate of search region (0 for full screen)",
    tab="advanced",
)

REGION_WIDTH_PROP = PropertyDef(
    "region_width",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Region Width",
    tooltip="Width of search region (0 for full screen)",
    tab="advanced",
)

REGION_HEIGHT_PROP = PropertyDef(
    "region_height",
    PropertyType.INTEGER,
    default=0,
    min_value=0,
    label="Region Height",
    tooltip="Height of search region (0 for full screen)",
    tab="advanced",
)

CLICK_AFTER_FIND_PROP = PropertyDef(
    "click_after_find",
    PropertyType.BOOLEAN,
    default=False,
    label="Click After Find",
    tooltip="Automatically click the element after finding it",
)

USE_GPU_PROP = PropertyDef(
    "use_gpu",
    PropertyType.BOOLEAN,
    default=True,
    label="Use GPU",
    tooltip="Use GPU acceleration if available",
    tab="advanced",
)


@properties(
    ELEMENT_TYPE_PROP,
    ELEMENT_INDEX_PROP,
    CONFIDENCE_THRESHOLD_PROP,
    REGION_X_PROP,
    REGION_Y_PROP,
    REGION_WIDTH_PROP,
    REGION_HEIGHT_PROP,
    CLICK_AFTER_FIND_PROP,
    USE_GPU_PROP,
    TIMEOUT_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
)
@node(category="desktop")
class YOLOFindElementNode(DesktopNodeBase):
    """
    Find UI elements using YOLO object detection.

    Uses YOLOv8 for real-time element detection in screenshots.
    Works without DOM/accessibility APIs, ideal for:
    - VDI/Citrix environments
    - Legacy applications
    - Remote desktop sessions
    - Games and custom UI frameworks

    Config (via @properties):
        element_type: Type to find (button, input, etc.)
        element_index: Which match to use (0 = first)
        confidence_threshold: Min detection confidence (default: 0.5)
        region_*: Limit search to screen region (0 = full screen)
        click_after_find: Auto-click after finding (default: False)
        use_gpu: Use GPU acceleration (default: True)

    Inputs:
        window_handle: Optional window to focus/capture

    Outputs:
        x: X coordinate of element center
        y: Y coordinate of element center
        width: Element bounding box width
        height: Element bounding box height
        confidence: Detection confidence score
        found: Whether element was found
        all_elements: List of all detected elements
    """

    # @category: desktop
    # @requires: none
    # @ports: window_handle -> x, y, width, height, confidence, found, all_elements

    NODE_NAME = "YOLO Find Element"

    def __init__(
        self,
        node_id: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        name: str = "YOLO Find Element",
    ):
        super().__init__(node_id, config or {}, name=name)
        self.node_type = "YOLOFindElementNode"
        self._detector = None

    def _define_ports(self) -> None:
        """Define input and output ports."""
        # Inputs
        self.add_exec_input("exec_in")
        self.add_input_port("window_handle", DataType.INTEGER, required=False)

        # Outputs
        self.add_exec_output("exec_out")
        self.add_output_port("x", DataType.INTEGER)
        self.add_output_port("y", DataType.INTEGER)
        self.add_output_port("width", DataType.INTEGER)
        self.add_output_port("height", DataType.INTEGER)
        self.add_output_port("confidence", DataType.NUMBER)
        self.add_output_port("found", DataType.BOOLEAN)
        self.add_output_port("all_elements", DataType.LIST)

    def _get_detector(self) -> Any:
        """Get or create YOLO detector."""
        if self._detector is None:
            try:
                from casare_rpa.infrastructure.ai.yolo_detector import (
                    YOLOElementDetector,
                )

                use_gpu = self.get_parameter("use_gpu", True)
                confidence = self.get_parameter("confidence_threshold", 0.5)

                self._detector = YOLOElementDetector(
                    confidence_threshold=confidence,
                    use_gpu=use_gpu,
                )
            except ImportError as e:
                raise ImportError(
                    "YOLOElementDetector not available. "
                    "Install with: pip install ultralytics opencv-python"
                ) from e
        return self._detector

    async def _capture_screenshot(
        self,
        window_handle: Optional[int] = None,
        region: Optional[tuple] = None,
    ) -> bytes:
        """
        Capture screenshot of screen or window.

        Args:
            window_handle: Optional window to capture.
            region: Optional (x, y, width, height) region.

        Returns:
            PNG screenshot bytes.
        """
        try:
            import io
            from PIL import ImageGrab, Image

            if window_handle:
                # Try to capture specific window
                try:
                    import win32gui
                    import win32ui
                    import win32con
                    from ctypes import windll

                    # Get window rect
                    left, top, right, bottom = win32gui.GetWindowRect(window_handle)
                    width = right - left
                    height = bottom - top

                    # Capture window
                    hwnd_dc = win32gui.GetWindowDC(window_handle)
                    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
                    save_dc = mfc_dc.CreateCompatibleDC()

                    bitmap = win32ui.CreateBitmap()
                    bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
                    save_dc.SelectObject(bitmap)

                    # Try PrintWindow for better capture
                    windll.user32.PrintWindow(window_handle, save_dc.GetSafeHdc(), 2)

                    bmpinfo = bitmap.GetInfo()
                    bmpstr = bitmap.GetBitmapBits(True)

                    image = Image.frombuffer(
                        "RGB",
                        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
                        bmpstr,
                        "raw",
                        "BGRX",
                        0,
                        1,
                    )

                    # Cleanup
                    win32gui.DeleteObject(bitmap.GetHandle())
                    save_dc.DeleteDC()
                    mfc_dc.DeleteDC()
                    win32gui.ReleaseDC(window_handle, hwnd_dc)

                except Exception as e:
                    logger.warning(f"Window capture failed, using full screen: {e}")
                    image = ImageGrab.grab(bbox=region if region else None)
            else:
                # Full screen or region capture
                image = ImageGrab.grab(bbox=region if region else None)

            # Convert to PNG bytes
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            return buffer.getvalue()

        except ImportError:
            raise ImportError(
                "Screenshot capture requires Pillow. " "Install with: pip install Pillow"
            )

    async def execute(self, context: ExecutionContext) -> Dict[str, Any]:
        """Execute YOLO element detection."""
        try:
            # Get parameters
            element_type = self.get_parameter("element_type", "button")
            element_index = self.get_parameter("element_index", 0)
            confidence_threshold = self.get_parameter("confidence_threshold", 0.5)
            click_after = self.get_parameter("click_after_find", False)

            # Get region parameters
            region_x = self.get_parameter("region_x", 0)
            region_y = self.get_parameter("region_y", 0)
            region_width = self.get_parameter("region_width", 0)
            region_height = self.get_parameter("region_height", 0)

            region = None
            if region_width > 0 and region_height > 0:
                region = (region_x, region_y, region_width, region_height)

            # Get optional window handle
            window_handle = self.get_input_value("window_handle")

            logger.info(
                f"[{self.name}] YOLO detecting {element_type} "
                f"(index={element_index}, threshold={confidence_threshold})"
            )

            # Get detector
            detector = self._get_detector()
            detector._confidence_threshold = confidence_threshold

            # Check if YOLO is available
            if not detector.is_available:
                return self.error_result(
                    "YOLO dependencies not available. "
                    "Install with: pip install ultralytics opencv-python"
                )

            # Capture screenshot
            screenshot_bytes = await self._capture_screenshot(
                window_handle=window_handle,
                region=region,
            )

            # Run detection
            result = await detector.detect_elements(
                screenshot=screenshot_bytes,
                element_types=[element_type],
                region=region,
            )

            if not result.success:
                return self.error_result(result.error_message or "Detection failed")

            # Filter by confidence and get all matching elements
            matching_elements = [e for e in result.elements if e.confidence >= confidence_threshold]

            # Convert to list of dicts for output
            all_elements_data = [e.to_dict() for e in matching_elements]
            self.set_output_value("all_elements", all_elements_data)

            if not matching_elements:
                logger.warning(
                    f"[{self.name}] No {element_type} elements found "
                    f"with confidence >= {confidence_threshold}"
                )
                return self.success_result(
                    {
                        "x": 0,
                        "y": 0,
                        "width": 0,
                        "height": 0,
                        "confidence": 0.0,
                        "found": False,
                        "all_elements": [],
                        "inference_time_ms": result.inference_time_ms,
                    }
                )

            # Get element by index
            if element_index >= len(matching_elements):
                logger.warning(
                    f"[{self.name}] Element index {element_index} out of range "
                    f"(found {len(matching_elements)} elements)"
                )
                element_index = len(matching_elements) - 1

            target_element = matching_elements[element_index]

            logger.info(
                f"[{self.name}] Found {element_type} at "
                f"({target_element.center_x}, {target_element.center_y}) "
                f"confidence={target_element.confidence:.2f}"
            )

            # Click if requested
            if click_after:
                try:
                    import pyautogui

                    pyautogui.click(target_element.center_x, target_element.center_y)
                    logger.info(
                        f"[{self.name}] Clicked at "
                        f"({target_element.center_x}, {target_element.center_y})"
                    )
                except ImportError:
                    logger.warning(
                        "pyautogui not available for clicking. "
                        "Install with: pip install pyautogui"
                    )

            return self.success_result(
                {
                    "x": target_element.center_x,
                    "y": target_element.center_y,
                    "width": target_element.width,
                    "height": target_element.height,
                    "confidence": target_element.confidence,
                    "found": True,
                    "element_type": target_element.element_type.value,
                    "all_elements": all_elements_data,
                    "total_detected": len(matching_elements),
                    "inference_time_ms": result.inference_time_ms,
                }
            )

        except Exception as e:
            logger.error(f"[{self.name}] YOLO detection failed: {e}")
            return self.error_result(str(e))

    def success_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Build success result with output port values."""
        self.status = NodeStatus.SUCCESS

        # Set output values
        self.set_output_value("x", data.get("x", 0))
        self.set_output_value("y", data.get("y", 0))
        self.set_output_value("width", data.get("width", 0))
        self.set_output_value("height", data.get("height", 0))
        self.set_output_value("confidence", data.get("confidence", 0.0))
        self.set_output_value("found", data.get("found", False))

        return {
            "success": True,
            "data": data,
            "next_nodes": ["exec_out"],
        }

    def error_result(self, error: str) -> Dict[str, Any]:
        """Build error result."""
        self.status = NodeStatus.ERROR
        logger.error(f"{self.__class__.__name__} failed: {error}")

        # Set default output values
        self.set_output_value("x", 0)
        self.set_output_value("y", 0)
        self.set_output_value("width", 0)
        self.set_output_value("height", 0)
        self.set_output_value("confidence", 0.0)
        self.set_output_value("found", False)
        self.set_output_value("all_elements", [])

        return {
            "success": False,
            "error": error,
            "next_nodes": [],
        }


# =============================================================================
# Property Export
# =============================================================================

__all__ = [
    "YOLOFindElementNode",
    "ELEMENT_TYPE_PROP",
    "ELEMENT_INDEX_PROP",
    "CONFIDENCE_THRESHOLD_PROP",
    "REGION_X_PROP",
    "REGION_Y_PROP",
    "REGION_WIDTH_PROP",
    "REGION_HEIGHT_PROP",
    "CLICK_AFTER_FIND_PROP",
    "USE_GPU_PROP",
]
