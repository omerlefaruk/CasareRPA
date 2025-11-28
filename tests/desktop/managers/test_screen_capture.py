"""
Tests for ScreenCapture.

Tests screenshot capture, element capture, OCR, image comparison.
All tests mock PIL and OCR libraries to avoid real screen interactions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

from casare_rpa.desktop.managers import ScreenCapture


class TestScreenCaptureInit:
    """Test ScreenCapture initialization."""

    def test_init(self):
        """ScreenCapture initializes without error."""
        capture = ScreenCapture()
        assert capture is not None


class TestCaptureScreenshot:
    """Test full screen capture."""

    @pytest.mark.asyncio
    async def test_capture_screenshot_full_screen(self, mock_pil):
        """Capture full screen screenshot."""
        capture = ScreenCapture()
        result = await capture.capture_screenshot()

        assert result is not None
        mock_pil["grab"].assert_called_once()

    @pytest.mark.asyncio
    async def test_capture_screenshot_region(self, mock_pil):
        """Capture screenshot of specific region."""
        capture = ScreenCapture()
        result = await capture.capture_screenshot(
            region={"x": 100, "y": 100, "width": 400, "height": 300}
        )

        assert result is not None
        mock_pil["grab"].assert_called_once()
        call_kwargs = mock_pil["grab"].call_args
        assert call_kwargs is not None

    @pytest.mark.asyncio
    async def test_capture_screenshot_save_to_file(self, mock_pil):
        """Capture and save screenshot to file."""
        capture = ScreenCapture()
        result = await capture.capture_screenshot(
            file_path="test_screenshot.png", format="PNG"
        )

        assert result is not None
        mock_pil["image"].save.assert_called_with("test_screenshot.png", format="PNG")

    @pytest.mark.asyncio
    async def test_capture_screenshot_pil_not_installed(self):
        """Returns None when PIL not installed."""
        with patch("PIL.ImageGrab.grab", side_effect=ImportError("No PIL")):
            capture = ScreenCapture()
            result = await capture.capture_screenshot()

            assert result is None

    @pytest.mark.asyncio
    async def test_capture_screenshot_failure(self):
        """Returns None on capture failure."""
        with patch("PIL.ImageGrab.grab", side_effect=Exception("Capture failed")):
            capture = ScreenCapture()
            result = await capture.capture_screenshot()

            assert result is None


class TestCaptureElementImage:
    """Test element image capture."""

    @pytest.mark.asyncio
    async def test_capture_element_image(self, mock_pil, mock_desktop_element):
        """Capture image of specific element."""
        capture = ScreenCapture()
        result = await capture.capture_element_image(mock_desktop_element)

        assert result is not None
        mock_pil["grab"].assert_called()

    @pytest.mark.asyncio
    async def test_capture_element_image_with_padding(
        self, mock_pil, mock_desktop_element
    ):
        """Capture element image with padding."""
        capture = ScreenCapture()
        result = await capture.capture_element_image(mock_desktop_element, padding=10)

        assert result is not None

    @pytest.mark.asyncio
    async def test_capture_element_image_save_to_file(
        self, mock_pil, mock_desktop_element
    ):
        """Capture and save element image to file."""
        capture = ScreenCapture()
        result = await capture.capture_element_image(
            mock_desktop_element, file_path="element.png"
        )

        assert result is not None
        mock_pil["image"].save.assert_called()

    @pytest.mark.asyncio
    async def test_capture_element_image_no_bounds(
        self, mock_pil, mock_desktop_element
    ):
        """Returns None when element has no bounds."""
        mock_desktop_element._control.BoundingRectangle = None

        capture = ScreenCapture()
        result = await capture.capture_element_image(mock_desktop_element)

        assert result is None


class TestOCRExtractText:
    """Test OCR text extraction."""

    @pytest.mark.asyncio
    async def test_ocr_extract_text_from_image(self, mock_pil):
        """Extract text from provided image."""
        with patch("rapidocr_onnxruntime.RapidOCR") as mock_ocr:
            mock_instance = MagicMock()
            mock_instance.return_value = ([("box", "Hello World", 0.95)], None)
            mock_ocr.return_value = mock_instance

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                image=mock_pil["image"], engine="rapidocr"
            )

            assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_from_path(self, mock_pil):
        """Extract text from image file path."""
        with (
            patch("rapidocr_onnxruntime.RapidOCR") as mock_ocr,
            patch("PIL.Image.open", return_value=mock_pil["image"]),
        ):
            mock_instance = MagicMock()
            mock_instance.return_value = ([("box", "Test Text", 0.95)], None)
            mock_ocr.return_value = mock_instance

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                image_path="test.png", engine="rapidocr"
            )

            assert result == "Test Text"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_tesseract(self, mock_pil):
        """Extract text using Tesseract engine."""
        with patch("pytesseract.image_to_string") as mock_tess:
            mock_tess.return_value = "Tesseract Text"

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                image=mock_pil["image"], engine="tesseract"
            )

            assert result == "Tesseract Text"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_auto_engine(self, mock_pil):
        """Auto engine tries multiple OCR engines."""
        with patch("rapidocr_onnxruntime.RapidOCR") as mock_rapid:
            mock_instance = MagicMock()
            mock_instance.return_value = ([("box", "Auto Text", 0.95)], None)
            mock_rapid.return_value = mock_instance

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                image=mock_pil["image"], engine="auto"
            )

            assert result == "Auto Text"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_region(self, mock_pil):
        """Extract text from specific screen region."""
        with patch("rapidocr_onnxruntime.RapidOCR") as mock_ocr:
            mock_instance = MagicMock()
            mock_instance.return_value = ([("box", "Region Text", 0.95)], None)
            mock_ocr.return_value = mock_instance

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                region={"x": 100, "y": 100, "width": 200, "height": 50},
                engine="rapidocr",
            )

            assert result == "Region Text"

    @pytest.mark.asyncio
    async def test_ocr_extract_text_no_engine_available(self, mock_pil):
        """Returns None when specified OCR engine is unavailable."""
        # Test that we handle ImportError for specific engine
        with patch(
            "rapidocr_onnxruntime.RapidOCR", side_effect=ImportError("No module")
        ):
            capture = ScreenCapture()
            result = await capture.ocr_extract_text(
                image=mock_pil["image"], engine="rapidocr"
            )

            # When rapidocr not available and explicitly requested, returns None
            assert result is None

    @pytest.mark.asyncio
    async def test_ocr_extract_text_no_image(self, mock_pil):
        """Captures screen when no image provided."""
        with patch("rapidocr_onnxruntime.RapidOCR") as mock_ocr:
            mock_instance = MagicMock()
            mock_instance.return_value = ([("box", "Screen Text", 0.95)], None)
            mock_ocr.return_value = mock_instance

            capture = ScreenCapture()
            result = await capture.ocr_extract_text(engine="rapidocr")

            assert result == "Screen Text"
            mock_pil["grab"].assert_called()


class TestCompareImages:
    """Test image comparison."""

    @pytest.mark.asyncio
    async def test_compare_images_ssim(self, mock_pil):
        """Compare images using SSIM method."""
        with patch("skimage.metrics.structural_similarity") as mock_ssim:
            mock_ssim.return_value = 0.95

            capture = ScreenCapture()
            result = await capture.compare_images(
                image1=mock_pil["image"],
                image2=mock_pil["image"],
                method="ssim",
                threshold=0.9,
            )

            assert result["similarity"] == 0.95
            assert result["is_match"] is True
            assert result["method"] == "ssim"

    @pytest.mark.asyncio
    async def test_compare_images_histogram(self, mock_pil):
        """Compare images using histogram method."""
        capture = ScreenCapture()
        result = await capture.compare_images(
            image1=mock_pil["image"],
            image2=mock_pil["image"],
            method="histogram",
            threshold=0.8,
        )

        assert "similarity" in result
        assert "is_match" in result
        assert result["method"] == "histogram"

    @pytest.mark.asyncio
    async def test_compare_images_pixel(self, mock_pil):
        """Compare images using pixel method."""
        # Create mock images with numpy array support
        mock_arr = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch("numpy.array", return_value=mock_arr):
            capture = ScreenCapture()
            result = await capture.compare_images(
                image1=mock_pil["image"],
                image2=mock_pil["image"],
                method="pixel",
                threshold=0.9,
            )

            assert "similarity" in result
            assert result["method"] == "pixel"

    @pytest.mark.asyncio
    async def test_compare_images_from_paths(self, mock_pil):
        """Compare images loaded from file paths."""
        with (
            patch("PIL.Image.open", return_value=mock_pil["image"]),
            patch("skimage.metrics.structural_similarity", return_value=0.9),
        ):
            capture = ScreenCapture()
            result = await capture.compare_images(
                image1_path="image1.png", image2_path="image2.png", method="ssim"
            )

            assert "similarity" in result

    @pytest.mark.asyncio
    async def test_compare_images_below_threshold(self, mock_pil):
        """Reports no match when below threshold."""
        with patch("skimage.metrics.structural_similarity", return_value=0.5):
            capture = ScreenCapture()
            result = await capture.compare_images(
                image1=mock_pil["image"],
                image2=mock_pil["image"],
                method="ssim",
                threshold=0.9,
            )

            assert result["is_match"] is False

    @pytest.mark.asyncio
    async def test_compare_images_missing_image(self, mock_pil):
        """Returns error when images missing."""
        capture = ScreenCapture()
        result = await capture.compare_images(image1=None, image2=None)

        assert result["is_match"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_compare_images_fallback_to_histogram(self, mock_pil):
        """Falls back to histogram when skimage unavailable."""
        with patch("skimage.metrics.structural_similarity", side_effect=ImportError()):
            capture = ScreenCapture()
            result = await capture.compare_images(
                image1=mock_pil["image"], image2=mock_pil["image"], method="ssim"
            )

            assert result["method"] == "histogram"


class TestFindImageOnScreen:
    """Test template matching on screen."""

    @pytest.mark.asyncio
    async def test_find_image_on_screen(self, mock_pil):
        """Find template image on screen."""
        with (
            patch("cv2.cvtColor") as mock_cvt,
            patch("cv2.matchTemplate") as mock_match,
            patch("cv2.minMaxLoc") as mock_loc,
        ):
            mock_cvt.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_match.return_value = np.zeros((90, 90))
            mock_loc.return_value = (0, 0.95, (0, 0), (50, 60))

            capture = ScreenCapture()
            result = await capture.find_image_on_screen(
                template=mock_pil["image"], threshold=0.8
            )

            assert result is not None
            assert "x" in result
            assert "y" in result
            assert result["confidence"] >= 0.8

    @pytest.mark.asyncio
    async def test_find_image_on_screen_from_path(self, mock_pil):
        """Find template image from file path."""
        with (
            patch("PIL.Image.open", return_value=mock_pil["image"]),
            patch("cv2.cvtColor") as mock_cvt,
            patch("cv2.matchTemplate") as mock_match,
            patch("cv2.minMaxLoc") as mock_loc,
        ):
            mock_cvt.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_match.return_value = np.zeros((90, 90))
            mock_loc.return_value = (0, 0.95, (0, 0), (50, 60))

            capture = ScreenCapture()
            result = await capture.find_image_on_screen(
                template_path="template.png", threshold=0.8
            )

            assert result is not None

    @pytest.mark.asyncio
    async def test_find_image_on_screen_in_region(self, mock_pil):
        """Find template in specific screen region."""
        with (
            patch("cv2.cvtColor") as mock_cvt,
            patch("cv2.matchTemplate") as mock_match,
            patch("cv2.minMaxLoc") as mock_loc,
        ):
            mock_cvt.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_match.return_value = np.zeros((90, 90))
            mock_loc.return_value = (0, 0.9, (0, 0), (25, 30))

            capture = ScreenCapture()
            result = await capture.find_image_on_screen(
                template=mock_pil["image"],
                region={"x": 100, "y": 100, "width": 400, "height": 300},
                threshold=0.8,
            )

            assert result is not None
            # Result coords should include region offset
            assert result["x"] >= 100
            assert result["y"] >= 100

    @pytest.mark.asyncio
    async def test_find_image_on_screen_not_found(self, mock_pil):
        """Returns None when template not found."""
        with (
            patch("cv2.cvtColor") as mock_cvt,
            patch("cv2.matchTemplate") as mock_match,
            patch("cv2.minMaxLoc") as mock_loc,
        ):
            mock_cvt.return_value = np.zeros((100, 100), dtype=np.uint8)
            mock_match.return_value = np.zeros((90, 90))
            mock_loc.return_value = (0, 0.3, (0, 0), (50, 60))  # Below threshold

            capture = ScreenCapture()
            result = await capture.find_image_on_screen(
                template=mock_pil["image"], threshold=0.8
            )

            assert result is None

    @pytest.mark.asyncio
    async def test_find_image_on_screen_no_template(self, mock_pil):
        """Returns None when no template provided."""
        capture = ScreenCapture()
        result = await capture.find_image_on_screen()

        assert result is None

    @pytest.mark.asyncio
    async def test_find_image_on_screen_opencv_not_installed(self, mock_pil):
        """Returns None when OpenCV not installed."""
        with patch("cv2.cvtColor", side_effect=ImportError("No cv2")):
            capture = ScreenCapture()
            result = await capture.find_image_on_screen(template=mock_pil["image"])

            assert result is None
