"""
YOLO UI Element Detector - Real-time element detection using YOLOv8.

Provides DOM-independent element detection for:
- Desktop automation without UI Automation framework
- VDI/Citrix environments
- Legacy applications without accessibility APIs

Usage:
    detector = YOLOElementDetector()

    elements = await detector.detect_elements(
        screenshot=screenshot_bytes,
        element_types=["button", "input", "checkbox"]
    )

    for element in elements:
        if element.element_type == "button" and element.confidence > 0.8:
            await page.mouse.click(element.center_x, element.center_y)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger


class UIElementType(Enum):
    """Supported UI element types for detection."""

    BUTTON = "button"
    INPUT = "input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    LINK = "link"
    IMAGE = "image"
    ICON = "icon"
    TEXT = "text"
    MENU = "menu"
    TAB = "tab"
    SCROLLBAR = "scrollbar"
    SLIDER = "slider"
    TOGGLE = "toggle"
    DIALOG = "dialog"
    UNKNOWN = "unknown"


# YOLO class name to UIElementType mapping
YOLO_CLASS_MAPPING = {
    "button": UIElementType.BUTTON,
    "input": UIElementType.INPUT,
    "text_input": UIElementType.INPUT,
    "textbox": UIElementType.INPUT,
    "checkbox": UIElementType.CHECKBOX,
    "radio": UIElementType.RADIO,
    "radio_button": UIElementType.RADIO,
    "dropdown": UIElementType.DROPDOWN,
    "combobox": UIElementType.DROPDOWN,
    "select": UIElementType.DROPDOWN,
    "link": UIElementType.LINK,
    "hyperlink": UIElementType.LINK,
    "image": UIElementType.IMAGE,
    "icon": UIElementType.ICON,
    "text": UIElementType.TEXT,
    "label": UIElementType.TEXT,
    "menu": UIElementType.MENU,
    "menubar": UIElementType.MENU,
    "tab": UIElementType.TAB,
    "scrollbar": UIElementType.SCROLLBAR,
    "slider": UIElementType.SLIDER,
    "toggle": UIElementType.TOGGLE,
    "switch": UIElementType.TOGGLE,
    "dialog": UIElementType.DIALOG,
    "modal": UIElementType.DIALOG,
}


@dataclass
class DetectedElement:
    """
    A detected UI element from YOLO inference.

    Contains bounding box, classification, and confidence.
    """

    element_type: UIElementType
    """Type of UI element detected."""

    class_name: str
    """Original YOLO class name."""

    x: int
    """X coordinate of bounding box top-left."""

    y: int
    """Y coordinate of bounding box top-left."""

    width: int
    """Width of bounding box."""

    height: int
    """Height of bounding box."""

    confidence: float
    """Detection confidence score (0.0 to 1.0)."""

    @property
    def center_x(self) -> int:
        """Center X coordinate for clicking."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Center Y coordinate for clicking."""
        return self.y + self.height // 2

    @property
    def area(self) -> int:
        """Area of bounding box in pixels."""
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "element_type": self.element_type.value,
            "class_name": self.class_name,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center_x": self.center_x,
            "center_y": self.center_y,
            "confidence": self.confidence,
            "area": self.area,
        }


@dataclass
class DetectionResult:
    """
    Result of YOLO detection on a screenshot.

    Contains all detected elements and metadata.
    """

    success: bool
    """Whether detection completed successfully."""

    elements: list[DetectedElement] = field(default_factory=list)
    """List of detected elements."""

    inference_time_ms: float = 0.0
    """Time for model inference in milliseconds."""

    preprocessing_time_ms: float = 0.0
    """Time for image preprocessing."""

    total_time_ms: float = 0.0
    """Total processing time."""

    model_name: str = ""
    """Name of model used."""

    image_size: tuple[int, int] = (0, 0)
    """Size of input image (width, height)."""

    error_message: str | None = None
    """Error message if detection failed."""

    def filter_by_type(
        self,
        element_types: list[UIElementType],
    ) -> list[DetectedElement]:
        """Filter elements by type."""
        return [e for e in self.elements if e.element_type in element_types]

    def filter_by_confidence(
        self,
        min_confidence: float,
    ) -> list[DetectedElement]:
        """Filter elements by minimum confidence."""
        return [e for e in self.elements if e.confidence >= min_confidence]

    def get_by_position(
        self,
        x: int,
        y: int,
        tolerance: int = 10,
    ) -> DetectedElement | None:
        """Get element at or near a specific position."""
        for element in self.elements:
            if (
                element.x - tolerance <= x <= element.x + element.width + tolerance
                and element.y - tolerance <= y <= element.y + element.height + tolerance
            ):
                return element
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "elements": [e.to_dict() for e in self.elements],
            "inference_time_ms": self.inference_time_ms,
            "preprocessing_time_ms": self.preprocessing_time_ms,
            "total_time_ms": self.total_time_ms,
            "model_name": self.model_name,
            "image_size": self.image_size,
            "error_message": self.error_message,
            "element_count": len(self.elements),
        }


# Lazy import for ultralytics
_ultralytics: Any = None
_cv2: Any = None
_np: Any = None


def _ensure_yolo_imports() -> bool:
    """
    Lazy import YOLO dependencies.

    Returns:
        True if imports successful, False otherwise.
    """
    global _ultralytics, _cv2, _np

    if _ultralytics is not None:
        return True

    try:
        import cv2
        import numpy as np
        from ultralytics import YOLO

        _ultralytics = YOLO
        _cv2 = cv2
        _np = np
        return True

    except ImportError as e:
        logger.warning(
            f"YOLO dependencies not available: {e}. "
            "Install with: pip install ultralytics opencv-python"
        )
        return False


class YOLOElementDetector:
    """
    Detect UI elements using YOLOv8 object detection.

    Provides DOM-independent element detection by analyzing screenshots
    with a trained YOLOv8 model. Useful for:
    - Desktop automation without accessibility APIs
    - Citrix/VDI environments
    - Legacy applications
    - Visual verification of UI state

    Example:
        detector = YOLOElementDetector()

        # Detect all elements
        result = await detector.detect_elements(screenshot)

        # Find buttons
        buttons = result.filter_by_type([UIElementType.BUTTON])

        # Click the most confident button
        if buttons:
            best = max(buttons, key=lambda e: e.confidence)
            await page.mouse.click(best.center_x, best.center_y)
    """

    # Default models for UI detection
    DEFAULT_MODEL = "yolov8n.pt"  # Fallback to generic model
    UI_DETECTION_MODEL = "nicholascelestin/yolov8s-ui-detection"

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str | None = None,
        use_gpu: bool = True,
    ) -> None:
        """
        Initialize YOLO detector.

        Args:
            model_path: Path to YOLO model weights (uses default if None).
            confidence_threshold: Minimum detection confidence.
            iou_threshold: IoU threshold for NMS.
            device: Device to run on ('cuda', 'cpu', 'mps'). Auto-detected if None.
            use_gpu: Whether to prefer GPU if available.
        """
        self._model_path = model_path
        self._confidence_threshold = confidence_threshold
        self._iou_threshold = iou_threshold
        self._device = device
        self._use_gpu = use_gpu
        self._model: Any = None
        self._initialized = False

        logger.debug(
            f"YOLOElementDetector created (confidence={confidence_threshold}, iou={iou_threshold})"
        )

    @property
    def is_available(self) -> bool:
        """Check if YOLO dependencies are available."""
        return _ensure_yolo_imports()

    def _ensure_model_loaded(self) -> bool:
        """
        Load the YOLO model if not already loaded.

        Returns:
            True if model is ready, False otherwise.
        """
        if self._initialized and self._model is not None:
            return True

        if not _ensure_yolo_imports():
            return False

        try:
            # Determine model path
            model_path = self._model_path

            if model_path is None:
                # Try to use UI-specific model from HuggingFace
                try:
                    model_path = self.UI_DETECTION_MODEL
                    self._model = _ultralytics(model_path)
                    logger.info(f"Loaded UI detection model: {model_path}")
                except Exception:
                    # Fall back to generic YOLOv8
                    model_path = self.DEFAULT_MODEL
                    self._model = _ultralytics(model_path)
                    logger.warning(f"UI model unavailable, using generic: {model_path}")
            else:
                self._model = _ultralytics(model_path)
                logger.info(f"Loaded custom model: {model_path}")

            # Set device
            if self._device:
                self._model.to(self._device)
            elif self._use_gpu:
                # Auto-detect GPU
                try:
                    import torch

                    if torch.cuda.is_available():
                        self._model.to("cuda")
                        logger.debug("Using CUDA GPU for inference")
                    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        self._model.to("mps")
                        logger.debug("Using MPS (Apple Silicon) for inference")
                except ImportError:
                    pass

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    async def detect_elements(
        self,
        screenshot: bytes,
        element_types: list[str] | None = None,
        region: tuple[int, int, int, int] | None = None,
    ) -> DetectionResult:
        """
        Detect UI elements in a screenshot.

        Args:
            screenshot: PNG screenshot bytes.
            element_types: Filter to specific element types (e.g., ["button", "input"]).
                None returns all detected elements.
            region: Optional region of interest (x, y, width, height).
                Crops screenshot before detection for performance.

        Returns:
            DetectionResult with all detected elements.
        """
        start_time = time.perf_counter()

        if not self._ensure_model_loaded():
            return DetectionResult(
                success=False,
                error_message="YOLO model not available",
                total_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        try:
            # Convert bytes to numpy array
            preprocess_start = time.perf_counter()
            nparr = _np.frombuffer(screenshot, _np.uint8)
            image = _cv2.imdecode(nparr, _cv2.IMREAD_COLOR)

            if image is None:
                return DetectionResult(
                    success=False,
                    error_message="Failed to decode screenshot",
                    total_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            original_size = (image.shape[1], image.shape[0])

            # Crop to region if specified
            offset_x, offset_y = 0, 0
            if region:
                rx, ry, rw, rh = region
                image = image[ry : ry + rh, rx : rx + rw]
                offset_x, offset_y = rx, ry

            preprocessing_time = (time.perf_counter() - preprocess_start) * 1000

            # Run inference in thread pool (YOLO can be CPU-bound)
            inference_start = time.perf_counter()
            results = await asyncio.to_thread(
                self._run_inference,
                image,
            )
            inference_time = (time.perf_counter() - inference_start) * 1000

            # Process detections
            elements = self._process_results(
                results,
                offset_x,
                offset_y,
                element_types,
            )

            total_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                f"YOLO detected {len(elements)} elements "
                f"(inference={inference_time:.1f}ms, total={total_time:.1f}ms)"
            )

            return DetectionResult(
                success=True,
                elements=elements,
                inference_time_ms=inference_time,
                preprocessing_time_ms=preprocessing_time,
                total_time_ms=total_time,
                model_name=str(self._model_path or self.UI_DETECTION_MODEL),
                image_size=original_size,
            )

        except Exception as e:
            total_time = (time.perf_counter() - start_time) * 1000
            logger.error(f"YOLO detection failed: {e}")
            return DetectionResult(
                success=False,
                error_message=str(e),
                total_time_ms=total_time,
            )

    def _run_inference(self, image: Any) -> Any:
        """
        Run YOLO inference on image.

        Args:
            image: OpenCV image (BGR numpy array).

        Returns:
            YOLO Results object.
        """
        return self._model(
            image,
            conf=self._confidence_threshold,
            iou=self._iou_threshold,
            verbose=False,
        )

    def _process_results(
        self,
        results: Any,
        offset_x: int,
        offset_y: int,
        element_types: list[str] | None,
    ) -> list[DetectedElement]:
        """
        Process YOLO results into DetectedElement objects.

        Args:
            results: YOLO Results object.
            offset_x: X offset for cropped images.
            offset_y: Y offset for cropped images.
            element_types: Filter element types.

        Returns:
            List of DetectedElement objects.
        """
        elements: list[DetectedElement] = []

        # Type filter set for efficiency
        type_filter: set | None = None
        if element_types:
            type_filter = set(t.lower() for t in element_types)

        for result in results:
            boxes = result.boxes

            if boxes is None:
                continue

            # Get class names from model
            names = self._model.names

            for _i, box in enumerate(boxes):
                # Get bounding box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

                # Get class and confidence
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                class_name = names.get(class_id, f"class_{class_id}").lower()

                # Map to UIElementType
                element_type = YOLO_CLASS_MAPPING.get(
                    class_name,
                    UIElementType.UNKNOWN,
                )

                # Apply type filter
                if type_filter:
                    if class_name not in type_filter and element_type.value not in type_filter:
                        continue

                elements.append(
                    DetectedElement(
                        element_type=element_type,
                        class_name=class_name,
                        x=int(x1) + offset_x,
                        y=int(y1) + offset_y,
                        width=int(x2 - x1),
                        height=int(y2 - y1),
                        confidence=confidence,
                    )
                )

        # Sort by confidence (highest first)
        elements.sort(key=lambda e: -e.confidence)

        return elements

    async def find_element_by_type(
        self,
        screenshot: bytes,
        element_type: str,
        index: int = 0,
    ) -> DetectedElement | None:
        """
        Find a specific element by type.

        Args:
            screenshot: PNG screenshot bytes.
            element_type: Type to find (e.g., "button", "input").
            index: Index if multiple elements (0 = first).

        Returns:
            DetectedElement if found, None otherwise.
        """
        result = await self.detect_elements(
            screenshot,
            element_types=[element_type],
        )

        if not result.success or not result.elements:
            return None

        if index >= len(result.elements):
            return None

        return result.elements[index]

    async def find_element_at_position(
        self,
        screenshot: bytes,
        x: int,
        y: int,
    ) -> DetectedElement | None:
        """
        Find element at a specific screen position.

        Args:
            screenshot: PNG screenshot bytes.
            x: X coordinate.
            y: Y coordinate.

        Returns:
            DetectedElement at position, or None if none found.
        """
        result = await self.detect_elements(screenshot)

        if not result.success:
            return None

        return result.get_by_position(x, y)

    async def get_clickable_elements(
        self,
        screenshot: bytes,
        min_confidence: float = 0.7,
    ) -> list[DetectedElement]:
        """
        Get all clickable elements (buttons, links, icons).

        Args:
            screenshot: PNG screenshot bytes.
            min_confidence: Minimum confidence threshold.

        Returns:
            List of clickable elements sorted by confidence.
        """
        clickable_types = [
            UIElementType.BUTTON,
            UIElementType.LINK,
            UIElementType.ICON,
            UIElementType.CHECKBOX,
            UIElementType.RADIO,
            UIElementType.TOGGLE,
            UIElementType.TAB,
        ]

        result = await self.detect_elements(screenshot)

        if not result.success:
            return []

        return [
            e
            for e in result.elements
            if e.element_type in clickable_types and e.confidence >= min_confidence
        ]


__all__ = [
    "YOLOElementDetector",
    "DetectedElement",
    "DetectionResult",
    "UIElementType",
    "YOLO_CLASS_MAPPING",
]
