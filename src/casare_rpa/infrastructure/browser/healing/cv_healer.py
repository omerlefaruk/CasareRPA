"""
Computer Vision Fallback Healer (Tier 3).

Last-resort healing using OCR text detection and template matching.
When DOM-based selectors fail, uses visual analysis to locate elements.

Requires:
    - pytesseract (pip install pytesseract)
    - opencv-python (pip install opencv-python)
    - Tesseract OCR installed on system
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from playwright.async_api import Page

# Lazy imports for optional CV dependencies
_cv2: Any = None
_np: Any = None
_pytesseract: Any = None
_Image: Any = None


def _ensure_cv_imports() -> bool:
    """
    Lazy import CV dependencies to avoid startup penalty.

    Returns:
        True if all dependencies available, False otherwise.
    """
    global _cv2, _np, _pytesseract, _Image

    if _cv2 is not None:
        return True

    try:
        import cv2
        import numpy as np
        import pytesseract
        from PIL import Image

        _cv2 = cv2
        _np = np
        _pytesseract = pytesseract
        _Image = Image
        return True

    except ImportError as e:
        logger.warning(
            f"CV healing unavailable - missing dependency: {e}. "
            "Install with: pip install opencv-python pytesseract pillow"
        )
        return False


class CVStrategy(Enum):
    """Computer vision healing strategies."""

    OCR_TEXT = "ocr_text"
    """Find element by visible text using OCR."""

    TEMPLATE_MATCH = "template_match"
    """Find element by template image matching."""

    VISUAL_DETECTION = "visual_detection"
    """Find element by visual features (buttons, inputs)."""

    PIXEL_FALLBACK = "pixel_fallback"
    """Fallback to absolute pixel coordinates."""


@dataclass
class OCRMatch:
    """
    Result of OCR text detection.

    Represents a detected text region with bounding box and confidence.
    """

    text: str
    """Detected text content."""

    confidence: float
    """OCR confidence score (0.0 to 1.0)."""

    x: int
    """X coordinate of bounding box."""

    y: int
    """Y coordinate of bounding box."""

    width: int
    """Width of bounding box."""

    height: int
    """Height of bounding box."""

    @property
    def center_x(self) -> int:
        """Center X coordinate for clicking."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Center Y coordinate for clicking."""
        return self.y + self.height // 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "confidence": self.confidence,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "center": (self.center_x, self.center_y),
        }


@dataclass
class TemplateMatch:
    """
    Result of template matching.

    Represents a matched region where template was found.
    """

    x: int
    """X coordinate of match."""

    y: int
    """Y coordinate of match."""

    width: int
    """Width of matched region."""

    height: int
    """Height of matched region."""

    similarity: float
    """Similarity score (0.0 to 1.0)."""

    @property
    def center_x(self) -> int:
        """Center X coordinate for clicking."""
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        """Center Y coordinate for clicking."""
        return self.y + self.height // 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "similarity": self.similarity,
            "center": (self.center_x, self.center_y),
        }


@dataclass
class CVHealingResult:
    """
    Result of a CV-based healing attempt.

    Contains click coordinates and metadata about the detection method.
    """

    success: bool
    """Whether an element was found."""

    original_selector: str
    """The original selector that failed."""

    strategy: CVStrategy
    """Strategy that succeeded (or last attempted)."""

    confidence: float
    """Confidence score of the result."""

    click_x: Optional[int] = None
    """X coordinate to click."""

    click_y: Optional[int] = None
    """Y coordinate to click."""

    bounding_box: Optional[Dict[str, int]] = None
    """Bounding box of detected element."""

    detected_text: Optional[str] = None
    """Text detected (for OCR strategy)."""

    healing_time_ms: float = 0.0
    """Time taken for CV healing."""

    candidates: List[Dict[str, Any]] = field(default_factory=list)
    """Alternative matches found."""

    error_message: Optional[str] = None
    """Error message if failed."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "original_selector": self.original_selector,
            "strategy": self.strategy.value,
            "confidence": self.confidence,
            "click_x": self.click_x,
            "click_y": self.click_y,
            "bounding_box": self.bounding_box,
            "detected_text": self.detected_text,
            "healing_time_ms": self.healing_time_ms,
            "candidates": self.candidates,
            "error_message": self.error_message,
        }


@dataclass
class CVContext:
    """
    Captured visual context for an element.

    Stores information needed for CV-based healing, captured during recording.
    """

    text_content: str
    """Expected visible text of the element."""

    template_image: Optional[bytes] = None
    """Screenshot of the element as template."""

    expected_position: Optional[Tuple[int, int]] = None
    """Expected (x, y) position as fallback."""

    expected_size: Optional[Tuple[int, int]] = None
    """Expected (width, height) of element."""

    element_type: Optional[str] = None
    """Type of element (button, input, etc.)."""

    visual_features: Dict[str, Any] = field(default_factory=dict)
    """Additional visual features for detection."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excludes binary data)."""
        return {
            "text_content": self.text_content,
            "has_template": self.template_image is not None,
            "expected_position": self.expected_position,
            "expected_size": self.expected_size,
            "element_type": self.element_type,
            "visual_features": self.visual_features,
        }


class CVHealer:
    """
    Tier 3 selector healer using computer vision.

    Uses OCR and template matching as last-resort healing when DOM-based
    approaches fail. Slower than other tiers but can handle major UI changes.

    Workflow:
        1. Capture element screenshot and text during recording
        2. When selector fails, take page screenshot
        3. Use OCR to find text or template matching for icons
        4. Return pixel coordinates for click action

    Example:
        healer = CVHealer()

        # During recording
        context = await healer.capture_cv_context(page, "#submit-btn")
        healer.store_context("#submit-btn", context)

        # During playback (when all other healing fails)
        result = await healer.heal(
            page,
            "#submit-btn",
            search_text="Submit"
        )
        if result.success:
            await page.mouse.click(result.click_x, result.click_y)
    """

    def __init__(
        self,
        ocr_confidence_threshold: float = 0.7,
        template_similarity_threshold: float = 0.8,
        budget_ms: float = 2000.0,
        tesseract_cmd: Optional[str] = None,
    ) -> None:
        """
        Initialize the CV healer.

        Args:
            ocr_confidence_threshold: Minimum OCR confidence (0.0 to 1.0).
            template_similarity_threshold: Minimum template match similarity.
            budget_ms: Maximum time budget for CV healing.
            tesseract_cmd: Path to tesseract executable (if not in PATH).
        """
        self._ocr_threshold = ocr_confidence_threshold
        self._template_threshold = template_similarity_threshold
        self._budget_ms = budget_ms
        self._tesseract_cmd = tesseract_cmd

        self._contexts: Dict[str, CVContext] = {}
        self._cv_available: Optional[bool] = None

        logger.debug(
            f"CVHealer initialized (ocr_threshold={ocr_confidence_threshold}, "
            f"template_threshold={template_similarity_threshold}, budget={budget_ms}ms)"
        )

    @property
    def is_available(self) -> bool:
        """Check if CV dependencies are available."""
        if self._cv_available is None:
            self._cv_available = _ensure_cv_imports()
            if self._cv_available and self._tesseract_cmd:
                _pytesseract.pytesseract.tesseract_cmd = self._tesseract_cmd
        return self._cv_available

    def store_context(self, selector: str, context: CVContext) -> None:
        """
        Store CV context for a selector.

        Args:
            selector: The original selector string.
            context: Captured CV context.
        """
        self._contexts[selector] = context
        logger.debug(f"Stored CV context for: {selector}")

    def get_context(self, selector: str) -> Optional[CVContext]:
        """Get stored CV context for a selector."""
        return self._contexts.get(selector)

    async def capture_cv_context(
        self,
        page: Page,
        selector: str,
    ) -> Optional[CVContext]:
        """
        Capture visual context of an element for future CV healing.

        Takes a screenshot of the element and extracts visual features.

        Args:
            page: Playwright Page object.
            selector: Selector for the target element.

        Returns:
            CVContext or None if element not found.
        """
        try:
            element = await page.query_selector(selector)
            if not element:
                logger.warning(
                    f"Cannot capture CV context: element not found: {selector}"
                )
                return None

            # Get element properties
            bounding_box = await element.bounding_box()
            if not bounding_box:
                logger.warning(
                    f"Cannot capture CV context: no bounding box: {selector}"
                )
                return None

            text_content = await element.text_content() or ""
            tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
            element_type = await element.get_attribute("type") or tag_name

            # Take element screenshot as template
            template_bytes: Optional[bytes] = None
            try:
                template_bytes = await element.screenshot(type="png")
            except Exception as e:
                logger.debug(f"Could not capture element screenshot: {e}")

            context = CVContext(
                text_content=text_content.strip(),
                template_image=template_bytes,
                expected_position=(int(bounding_box["x"]), int(bounding_box["y"])),
                expected_size=(int(bounding_box["width"]), int(bounding_box["height"])),
                element_type=element_type,
                visual_features={
                    "tag": tag_name,
                    "center_x": int(bounding_box["x"] + bounding_box["width"] / 2),
                    "center_y": int(bounding_box["y"] + bounding_box["height"] / 2),
                },
            )

            logger.debug(
                f"Captured CV context for {selector}: "
                f"text='{text_content[:30]}', type={element_type}, "
                f"has_template={template_bytes is not None}"
            )
            return context

        except Exception as e:
            logger.error(f"Failed to capture CV context for {selector}: {e}")
            return None

    async def heal(
        self,
        page: Page,
        selector: str,
        search_text: Optional[str] = None,
        template_path: Optional[Path] = None,
        context: Optional[CVContext] = None,
    ) -> CVHealingResult:
        """
        Attempt CV-based healing for a broken selector.

        Tries strategies in order:
        1. OCR text matching (if search_text provided)
        2. Template matching (if template available)
        3. Visual element detection
        4. Pixel coordinate fallback

        Args:
            page: Playwright Page object.
            selector: The original selector that failed.
            search_text: Text to search for using OCR.
            template_path: Path to template image for matching.
            context: CV context (uses stored if not provided).

        Returns:
            CVHealingResult with click coordinates or failure details.
        """
        start_time = time.perf_counter()

        if not self.is_available:
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                error_message="CV dependencies not available",
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        ctx = context or self._contexts.get(selector)
        effective_text = search_text or (ctx.text_content if ctx else None)
        template_bytes = ctx.template_image if ctx else None

        logger.info(f"Attempting CV healing for: {selector}")

        # Take page screenshot
        try:
            screenshot_bytes = await page.screenshot(type="png")
            screenshot_image = self._bytes_to_cv_image(screenshot_bytes)
        except Exception as e:
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                error_message=f"Failed to capture screenshot: {e}",
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        remaining_budget = self._budget_ms

        # Strategy 1: OCR text matching
        if effective_text and remaining_budget > 500:
            ocr_result = await self._try_ocr_healing(
                screenshot_image, effective_text, selector, start_time
            )
            if ocr_result.success:
                return ocr_result
            remaining_budget = self._budget_ms - (
                (time.perf_counter() - start_time) * 1000
            )

        # Strategy 2: Template matching
        if template_bytes and remaining_budget > 300:
            template_result = await self._try_template_healing(
                screenshot_image, template_bytes, selector, start_time
            )
            if template_result.success:
                return template_result
            remaining_budget = self._budget_ms - (
                (time.perf_counter() - start_time) * 1000
            )

        # Load template from file if provided
        if template_path and template_path.exists() and remaining_budget > 300:
            file_template_bytes = template_path.read_bytes()
            template_result = await self._try_template_healing(
                screenshot_image, file_template_bytes, selector, start_time
            )
            if template_result.success:
                return template_result
            remaining_budget = self._budget_ms - (
                (time.perf_counter() - start_time) * 1000
            )

        # Strategy 3: Visual element detection (for buttons, inputs)
        if ctx and ctx.element_type and remaining_budget > 200:
            visual_result = await self._try_visual_detection(
                screenshot_image, ctx, selector, start_time
            )
            if visual_result.success:
                return visual_result
            remaining_budget = self._budget_ms - (
                (time.perf_counter() - start_time) * 1000
            )

        # Strategy 4: Pixel fallback (last resort)
        if ctx and ctx.expected_position:
            return self._create_pixel_fallback_result(ctx, selector, start_time)

        # All strategies failed
        healing_time = (time.perf_counter() - start_time) * 1000
        logger.warning(
            f"CV healing failed for: {selector} (time: {healing_time:.1f}ms)"
        )

        return CVHealingResult(
            success=False,
            original_selector=selector,
            strategy=CVStrategy.PIXEL_FALLBACK,
            confidence=0.0,
            error_message="All CV strategies failed",
            healing_time_ms=healing_time,
        )

    async def _try_ocr_healing(
        self,
        screenshot: Any,
        search_text: str,
        selector: str,
        start_time: float,
    ) -> CVHealingResult:
        """
        Try to find element using OCR text detection.

        Args:
            screenshot: OpenCV image of the page.
            search_text: Text to search for.
            selector: Original selector.
            start_time: Start time for timing.

        Returns:
            CVHealingResult with match or failure.
        """
        try:
            # Run OCR in executor to avoid blocking
            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None, self._perform_ocr, screenshot, search_text
            )

            if matches:
                best_match = max(matches, key=lambda m: m.confidence)

                if best_match.confidence >= self._ocr_threshold:
                    healing_time = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"OCR healing succeeded: '{search_text}' found at "
                        f"({best_match.center_x}, {best_match.center_y}) "
                        f"conf={best_match.confidence:.2f}"
                    )
                    return CVHealingResult(
                        success=True,
                        original_selector=selector,
                        strategy=CVStrategy.OCR_TEXT,
                        confidence=best_match.confidence,
                        click_x=best_match.center_x,
                        click_y=best_match.center_y,
                        bounding_box={
                            "x": best_match.x,
                            "y": best_match.y,
                            "width": best_match.width,
                            "height": best_match.height,
                        },
                        detected_text=best_match.text,
                        healing_time_ms=healing_time,
                        candidates=[m.to_dict() for m in matches[:5]],
                    )

            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                candidates=[m.to_dict() for m in matches[:5]] if matches else [],
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            logger.debug(f"OCR healing error: {e}")
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.OCR_TEXT,
                confidence=0.0,
                error_message=str(e),
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _perform_ocr(self, screenshot: Any, search_text: str) -> List[OCRMatch]:
        """
        Perform OCR on screenshot and find matching text regions.

        Args:
            screenshot: OpenCV image.
            search_text: Text to find.

        Returns:
            List of OCRMatch objects sorted by confidence.
        """
        # Preprocess image for better OCR
        gray = _cv2.cvtColor(screenshot, _cv2.COLOR_BGR2GRAY)
        preprocessed = self._preprocess_for_ocr(gray)

        # Run Tesseract OCR with detailed output
        ocr_data = _pytesseract.image_to_data(
            preprocessed,
            output_type=_pytesseract.Output.DICT,
            config="--psm 11",  # Sparse text mode
        )

        matches: List[OCRMatch] = []
        search_lower = search_text.lower().strip()

        n_boxes = len(ocr_data["text"])
        for i in range(n_boxes):
            text = ocr_data["text"][i].strip()
            if not text:
                continue

            conf = int(ocr_data["conf"][i])
            if conf < 0:
                continue

            # Check for text match (exact or partial)
            text_lower = text.lower()
            if search_lower in text_lower or text_lower in search_lower:
                normalized_conf = conf / 100.0

                # Boost confidence for exact matches
                if text_lower == search_lower:
                    normalized_conf = min(1.0, normalized_conf + 0.15)

                matches.append(
                    OCRMatch(
                        text=text,
                        confidence=normalized_conf,
                        x=ocr_data["left"][i],
                        y=ocr_data["top"][i],
                        width=ocr_data["width"][i],
                        height=ocr_data["height"][i],
                    )
                )

        # Also try to find multi-word matches by combining adjacent words
        if " " in search_text and len(matches) == 0:
            matches.extend(self._find_multiword_matches(ocr_data, search_text))

        matches.sort(key=lambda m: -m.confidence)
        return matches

    def _find_multiword_matches(
        self,
        ocr_data: Dict[str, Any],
        search_text: str,
    ) -> List[OCRMatch]:
        """
        Find multi-word text by combining adjacent OCR results.

        Args:
            ocr_data: Tesseract OCR output.
            search_text: Multi-word text to find.

        Returns:
            List of matches for combined words.
        """
        matches: List[OCRMatch] = []
        search_words = search_text.lower().split()

        n_boxes = len(ocr_data["text"])
        for i in range(n_boxes - len(search_words) + 1):
            # Check if consecutive words match
            combined_text = []
            valid = True
            min_conf = 100
            min_x = float("inf")
            min_y = float("inf")
            max_x = 0
            max_y = 0

            for j, search_word in enumerate(search_words):
                idx = i + j
                text = ocr_data["text"][idx].strip().lower()
                conf = int(ocr_data["conf"][idx])

                if not text or conf < 0:
                    valid = False
                    break

                if text != search_word:
                    valid = False
                    break

                combined_text.append(ocr_data["text"][idx])
                min_conf = min(min_conf, conf)
                min_x = min(min_x, ocr_data["left"][idx])
                min_y = min(min_y, ocr_data["top"][idx])
                max_x = max(max_x, ocr_data["left"][idx] + ocr_data["width"][idx])
                max_y = max(max_y, ocr_data["top"][idx] + ocr_data["height"][idx])

            if valid and combined_text:
                matches.append(
                    OCRMatch(
                        text=" ".join(combined_text),
                        confidence=min_conf / 100.0,
                        x=int(min_x),
                        y=int(min_y),
                        width=int(max_x - min_x),
                        height=int(max_y - min_y),
                    )
                )

        return matches

    def _preprocess_for_ocr(self, gray_image: Any) -> Any:
        """
        Preprocess image for better OCR accuracy.

        Args:
            gray_image: Grayscale OpenCV image.

        Returns:
            Preprocessed image.
        """
        # Apply Gaussian blur to reduce noise
        blurred = _cv2.GaussianBlur(gray_image, (3, 3), 0)

        # Apply adaptive thresholding for better text contrast
        thresh = _cv2.adaptiveThreshold(
            blurred, 255, _cv2.ADAPTIVE_THRESH_GAUSSIAN_C, _cv2.THRESH_BINARY, 11, 2
        )

        # Optionally apply dilation to connect text components
        kernel = _cv2.getStructuringElement(_cv2.MORPH_RECT, (2, 2))
        processed = _cv2.morphologyEx(thresh, _cv2.MORPH_CLOSE, kernel)

        return processed

    async def _try_template_healing(
        self,
        screenshot: Any,
        template_bytes: bytes,
        selector: str,
        start_time: float,
    ) -> CVHealingResult:
        """
        Try to find element using template matching.

        Args:
            screenshot: OpenCV image of the page.
            template_bytes: PNG bytes of template image.
            selector: Original selector.
            start_time: Start time for timing.

        Returns:
            CVHealingResult with match or failure.
        """
        try:
            template = self._bytes_to_cv_image(template_bytes)

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None, self._perform_template_matching, screenshot, template
            )

            if matches:
                best_match = max(matches, key=lambda m: m.similarity)

                if best_match.similarity >= self._template_threshold:
                    healing_time = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"Template healing succeeded at "
                        f"({best_match.center_x}, {best_match.center_y}) "
                        f"similarity={best_match.similarity:.2f}"
                    )
                    return CVHealingResult(
                        success=True,
                        original_selector=selector,
                        strategy=CVStrategy.TEMPLATE_MATCH,
                        confidence=best_match.similarity,
                        click_x=best_match.center_x,
                        click_y=best_match.center_y,
                        bounding_box={
                            "x": best_match.x,
                            "y": best_match.y,
                            "width": best_match.width,
                            "height": best_match.height,
                        },
                        healing_time_ms=healing_time,
                        candidates=[m.to_dict() for m in matches[:5]],
                    )

            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.TEMPLATE_MATCH,
                confidence=0.0,
                candidates=[m.to_dict() for m in matches[:5]] if matches else [],
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            logger.debug(f"Template matching error: {e}")
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.TEMPLATE_MATCH,
                confidence=0.0,
                error_message=str(e),
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _perform_template_matching(
        self,
        screenshot: Any,
        template: Any,
    ) -> List[TemplateMatch]:
        """
        Perform template matching on screenshot.

        Args:
            screenshot: OpenCV image of page.
            template: OpenCV image of template.

        Returns:
            List of TemplateMatch objects.
        """
        # Convert to grayscale for matching
        gray_screenshot = _cv2.cvtColor(screenshot, _cv2.COLOR_BGR2GRAY)
        gray_template = _cv2.cvtColor(template, _cv2.COLOR_BGR2GRAY)

        template_h, template_w = gray_template.shape[:2]

        # Skip if template larger than screenshot
        if (
            template_h > gray_screenshot.shape[0]
            or template_w > gray_screenshot.shape[1]
        ):
            return []

        # Perform template matching with multiple methods
        methods = [
            _cv2.TM_CCOEFF_NORMED,
            _cv2.TM_CCORR_NORMED,
        ]

        matches: List[TemplateMatch] = []

        for method in methods:
            result = _cv2.matchTemplate(gray_screenshot, gray_template, method)

            # Find all matches above a lower threshold
            threshold = 0.6
            locations = _np.where(result >= threshold)

            for pt in zip(*locations[::-1]):
                similarity = result[pt[1], pt[0]]
                matches.append(
                    TemplateMatch(
                        x=int(pt[0]),
                        y=int(pt[1]),
                        width=template_w,
                        height=template_h,
                        similarity=float(similarity),
                    )
                )

        # Deduplicate nearby matches
        matches = self._dedupe_matches(matches)
        matches.sort(key=lambda m: -m.similarity)

        return matches[:10]

    def _dedupe_matches(
        self,
        matches: List[TemplateMatch],
        distance_threshold: int = 20,
    ) -> List[TemplateMatch]:
        """
        Remove duplicate matches that are too close together.

        Args:
            matches: List of matches to deduplicate.
            distance_threshold: Minimum pixel distance between matches.

        Returns:
            Deduplicated list.
        """
        if not matches:
            return []

        deduped: List[TemplateMatch] = []
        for match in sorted(matches, key=lambda m: -m.similarity):
            is_duplicate = False
            for existing in deduped:
                dx = abs(match.x - existing.x)
                dy = abs(match.y - existing.y)
                if dx < distance_threshold and dy < distance_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                deduped.append(match)

        return deduped

    async def _try_visual_detection(
        self,
        screenshot: Any,
        context: CVContext,
        selector: str,
        start_time: float,
    ) -> CVHealingResult:
        """
        Try to detect element by visual features.

        Uses edge detection and contour analysis to find UI elements
        matching the expected type (button, input, etc.).

        Args:
            screenshot: OpenCV image of page.
            context: CV context with element info.
            selector: Original selector.
            start_time: Start time for timing.

        Returns:
            CVHealingResult with detection or failure.
        """
        try:
            expected_size = context.expected_size
            expected_pos = context.expected_position

            if not expected_size:
                return CVHealingResult(
                    success=False,
                    original_selector=selector,
                    strategy=CVStrategy.VISUAL_DETECTION,
                    confidence=0.0,
                    error_message="No expected size in context",
                    healing_time_ms=(time.perf_counter() - start_time) * 1000,
                )

            loop = asyncio.get_event_loop()
            candidates = await loop.run_in_executor(
                None,
                self._detect_visual_elements,
                screenshot,
                expected_size,
                expected_pos,
                context.element_type,
            )

            if candidates:
                best = candidates[0]
                confidence = best.get("confidence", 0.5)

                if confidence >= 0.5:
                    healing_time = (time.perf_counter() - start_time) * 1000
                    logger.info(
                        f"Visual detection succeeded at "
                        f"({best['center_x']}, {best['center_y']}) "
                        f"conf={confidence:.2f}"
                    )
                    return CVHealingResult(
                        success=True,
                        original_selector=selector,
                        strategy=CVStrategy.VISUAL_DETECTION,
                        confidence=confidence,
                        click_x=best["center_x"],
                        click_y=best["center_y"],
                        bounding_box={
                            "x": best["x"],
                            "y": best["y"],
                            "width": best["width"],
                            "height": best["height"],
                        },
                        healing_time_ms=healing_time,
                        candidates=candidates[:5],
                    )

            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.VISUAL_DETECTION,
                confidence=0.0,
                candidates=candidates[:5] if candidates else [],
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        except Exception as e:
            logger.debug(f"Visual detection error: {e}")
            return CVHealingResult(
                success=False,
                original_selector=selector,
                strategy=CVStrategy.VISUAL_DETECTION,
                confidence=0.0,
                error_message=str(e),
                healing_time_ms=(time.perf_counter() - start_time) * 1000,
            )

    def _detect_visual_elements(
        self,
        screenshot: Any,
        expected_size: Tuple[int, int],
        expected_pos: Optional[Tuple[int, int]],
        element_type: Optional[str],
    ) -> List[Dict[str, Any]]:
        """
        Detect UI elements by visual analysis.

        Args:
            screenshot: OpenCV image.
            expected_size: Expected (width, height).
            expected_pos: Expected (x, y) position.
            element_type: Type like 'button', 'input'.

        Returns:
            List of candidate elements with confidence.
        """
        gray = _cv2.cvtColor(screenshot, _cv2.COLOR_BGR2GRAY)

        # Edge detection
        edges = _cv2.Canny(gray, 50, 150)

        # Dilate to connect edges
        kernel = _cv2.getStructuringElement(_cv2.MORPH_RECT, (3, 3))
        dilated = _cv2.dilate(edges, kernel, iterations=2)

        # Find contours
        contours, _ = _cv2.findContours(
            dilated, _cv2.RETR_EXTERNAL, _cv2.CHAIN_APPROX_SIMPLE
        )

        exp_w, exp_h = expected_size
        candidates: List[Dict[str, Any]] = []

        for contour in contours:
            x, y, w, h = _cv2.boundingRect(contour)

            # Skip if size doesn't match within tolerance
            size_ratio_w = w / exp_w if exp_w > 0 else 0
            size_ratio_h = h / exp_h if exp_h > 0 else 0

            if not (0.5 <= size_ratio_w <= 2.0 and 0.5 <= size_ratio_h <= 2.0):
                continue

            # Calculate confidence based on size match
            size_conf = 1.0 - (abs(1 - size_ratio_w) + abs(1 - size_ratio_h)) / 2

            # Boost confidence if position is close
            pos_conf = 1.0
            if expected_pos:
                exp_x, exp_y = expected_pos
                dist = ((x - exp_x) ** 2 + (y - exp_y) ** 2) ** 0.5
                max_dist = 500
                pos_conf = max(0, 1.0 - dist / max_dist)

            # Combined confidence
            confidence = size_conf * 0.6 + pos_conf * 0.4

            candidates.append(
                {
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                    "center_x": x + w // 2,
                    "center_y": y + h // 2,
                    "confidence": confidence,
                    "size_match": size_conf,
                    "position_match": pos_conf,
                }
            )

        candidates.sort(key=lambda c: -c["confidence"])
        return candidates[:20]

    def _create_pixel_fallback_result(
        self,
        context: CVContext,
        selector: str,
        start_time: float,
    ) -> CVHealingResult:
        """
        Create result using stored pixel coordinates as fallback.

        Args:
            context: CV context with expected position.
            selector: Original selector.
            start_time: Start time for timing.

        Returns:
            CVHealingResult with pixel coordinates.
        """
        healing_time = (time.perf_counter() - start_time) * 1000

        if context.expected_position and context.expected_size:
            x, y = context.expected_position
            w, h = context.expected_size
            click_x = x + w // 2
            click_y = y + h // 2

            logger.warning(
                f"Using pixel fallback for {selector}: ({click_x}, {click_y})"
            )

            return CVHealingResult(
                success=True,
                original_selector=selector,
                strategy=CVStrategy.PIXEL_FALLBACK,
                confidence=0.3,  # Low confidence for pixel fallback
                click_x=click_x,
                click_y=click_y,
                bounding_box={
                    "x": x,
                    "y": y,
                    "width": w,
                    "height": h,
                },
                healing_time_ms=healing_time,
            )

        return CVHealingResult(
            success=False,
            original_selector=selector,
            strategy=CVStrategy.PIXEL_FALLBACK,
            confidence=0.0,
            error_message="No position data for pixel fallback",
            healing_time_ms=healing_time,
        )

    def _bytes_to_cv_image(self, image_bytes: bytes) -> Any:
        """
        Convert PNG bytes to OpenCV image.

        Args:
            image_bytes: PNG image bytes.

        Returns:
            OpenCV image array.
        """
        nparr = _np.frombuffer(image_bytes, _np.uint8)
        img = _cv2.imdecode(nparr, _cv2.IMREAD_COLOR)
        return img

    async def find_text_on_page(
        self,
        page: Page,
        text: str,
        exact_match: bool = False,
    ) -> List[OCRMatch]:
        """
        Find all occurrences of text on a page using OCR.

        Utility method for discovering text locations.

        Args:
            page: Playwright Page object.
            text: Text to search for.
            exact_match: Require exact match vs partial.

        Returns:
            List of OCRMatch objects.
        """
        if not self.is_available:
            logger.warning("CV dependencies not available for text search")
            return []

        try:
            screenshot_bytes = await page.screenshot(type="png")
            screenshot = self._bytes_to_cv_image(screenshot_bytes)

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None, self._perform_ocr, screenshot, text
            )

            if exact_match:
                matches = [m for m in matches if m.text.lower() == text.lower()]

            return matches

        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    async def find_template_on_page(
        self,
        page: Page,
        template_path: Path,
    ) -> List[TemplateMatch]:
        """
        Find all occurrences of a template image on a page.

        Args:
            page: Playwright Page object.
            template_path: Path to template image file.

        Returns:
            List of TemplateMatch objects.
        """
        if not self.is_available:
            logger.warning("CV dependencies not available for template search")
            return []

        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            return []

        try:
            screenshot_bytes = await page.screenshot(type="png")
            screenshot = self._bytes_to_cv_image(screenshot_bytes)
            template = _cv2.imread(str(template_path))

            if template is None:
                logger.error(f"Could not load template: {template_path}")
                return []

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None, self._perform_template_matching, screenshot, template
            )

            return [m for m in matches if m.similarity >= self._template_threshold]

        except Exception as e:
            logger.error(f"Template search failed: {e}")
            return []


__all__ = [
    "CVStrategy",
    "OCRMatch",
    "TemplateMatch",
    "CVHealingResult",
    "CVContext",
    "CVHealer",
]
