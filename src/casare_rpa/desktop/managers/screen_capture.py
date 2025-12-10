"""
Screen Capture - Screenshot and OCR operations for desktop automation

Handles screen capture, element screenshots, OCR text extraction, and image comparison.
All operations are async-first with proper error handling.
"""

import asyncio
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.desktop.element import DesktopElement
from casare_rpa.utils.gpu import configure_onnx_gpu


class ScreenCapture:
    """
    Handles screen capture and OCR operations for desktop automation.

    Provides async methods for screenshots, element capture, OCR,
    and image comparison.
    Uses asyncio.to_thread() for blocking operations.
    """

    def __init__(self) -> None:
        """Initialize screen capture manager."""
        logger.debug("Initializing ScreenCapture")

    async def capture_screenshot(
        self,
        file_path: str = None,
        region: Dict[str, int] = None,
        format: str = "PNG",
    ) -> Optional[Any]:
        """
        Capture a screenshot of the screen or a specific region.

        Args:
            file_path: Path to save the screenshot (optional)
            region: Dict with x, y, width, height for specific region (optional)
            format: Image format (PNG, JPEG, BMP)

        Returns:
            PIL Image object if successful, None otherwise
        """

        def _capture() -> Optional[Any]:
            try:
                from PIL import ImageGrab

                if region:
                    x = region.get("x", 0)
                    y = region.get("y", 0)
                    width = region.get("width", 100)
                    height = region.get("height", 100)
                    bbox = (x, y, x + width, y + height)
                    screenshot = ImageGrab.grab(bbox=bbox)
                    logger.info(f"Captured screenshot region: {bbox}")
                else:
                    screenshot = ImageGrab.grab()
                    logger.info("Captured full screen screenshot")

                if file_path:
                    screenshot.save(file_path, format=format)
                    logger.info(f"Screenshot saved to: {file_path}")

                return screenshot

            except ImportError:
                logger.error("PIL/Pillow not installed. Run: pip install Pillow")
                return None
            except Exception as e:
                logger.error(f"Screenshot capture failed: {e}")
                return None

        return await asyncio.to_thread(_capture)

    async def capture_element_image(
        self,
        element: DesktopElement,
        file_path: str = None,
        padding: int = 0,
        format: str = "PNG",
    ) -> Optional[Any]:
        """
        Capture an image of a specific desktop element.

        Args:
            element: DesktopElement to capture
            file_path: Path to save the image (optional)
            padding: Extra pixels around element bounds
            format: Image format (PNG, JPEG, BMP)

        Returns:
            PIL Image object if successful, None otherwise
        """

        def _capture_element() -> Optional[Any]:
            try:
                from PIL import ImageGrab

                control = element._control
                rect = control.BoundingRectangle

                if not rect:
                    logger.error("Could not get element bounding rectangle")
                    return None

                x = max(0, rect.left - padding)
                y = max(0, rect.top - padding)
                right = rect.right + padding
                bottom = rect.bottom + padding
                bbox = (x, y, right, bottom)

                screenshot = ImageGrab.grab(bbox=bbox)
                logger.info(f"Captured element image: {bbox}")

                if file_path:
                    screenshot.save(file_path, format=format)
                    logger.info(f"Element image saved to: {file_path}")

                return screenshot

            except ImportError:
                logger.error("PIL/Pillow not installed. Run: pip install Pillow")
                return None
            except Exception as e:
                logger.error(f"Element image capture failed: {e}")
                return None

        return await asyncio.to_thread(_capture_element)

    async def ocr_extract_text(
        self,
        image: Any = None,
        image_path: str = None,
        region: Dict[str, int] = None,
        language: str = "eng",
        config: str = "",
        engine: str = "auto",
    ) -> Optional[str]:
        """
        Extract text from an image using OCR.

        Args:
            image: PIL Image object (optional)
            image_path: Path to image file (optional)
            region: Dict with x, y, width, height to extract from specific region
            language: Tesseract language code (default: eng)
            config: Additional Tesseract config options
            engine: OCR engine to use ('auto', 'rapidocr', 'tesseract', 'winocr')
                   - 'auto': Try rapidocr -> tesseract -> winocr in order
                   - 'rapidocr': Use RapidOCR (ONNX-based, no Tesseract needed)
                   - 'tesseract': Use pytesseract (requires Tesseract installed)
                   - 'winocr': Use Windows built-in OCR

        Returns:
            Extracted text string if successful, None otherwise
        """

        def _extract_text() -> Optional[str]:
            try:
                from PIL import Image
                import numpy as np

                img = image
                if img is None and image_path:
                    img = Image.open(image_path)
                elif img is None:
                    from PIL import ImageGrab

                    if region:
                        x = region.get("x", 0)
                        y = region.get("y", 0)
                        width = region.get("width", 100)
                        height = region.get("height", 100)
                        bbox = (x, y, x + width, y + height)
                        img = ImageGrab.grab(bbox=bbox)
                    else:
                        img = ImageGrab.grab()

                if img is None:
                    logger.error("No image provided for OCR")
                    return None

                if region and image_path:
                    x = region.get("x", 0)
                    y = region.get("y", 0)
                    width = region.get("width", img.width)
                    height = region.get("height", img.height)
                    img = img.crop((x, y, x + width, y + height))

                def try_rapidocr() -> Optional[str]:
                    try:
                        from rapidocr_onnxruntime import RapidOCR

                        # Configure GPU providers for OCR
                        providers = configure_onnx_gpu()
                        ocr = RapidOCR(providers=providers)
                        img_array = np.array(img.convert("RGB"))
                        result, _ = ocr(img_array)
                        if result:
                            text_parts = [item[1] for item in result]
                            text = "\n".join(text_parts)
                            gpu_used = (
                                "CUDA" in str(providers[0]) if providers else False
                            )
                            backend = "GPU" if gpu_used else "CPU"
                            logger.info(
                                f"RapidOCR ({backend}) extracted {len(text)} characters"
                            )
                            return text.strip()
                        return ""
                    except ImportError:
                        logger.debug("rapidocr_onnxruntime not installed")
                        return None
                    except Exception as e:
                        logger.warning(f"RapidOCR failed: {e}")
                        return None

                def try_tesseract() -> Optional[str]:
                    try:
                        import pytesseract

                        text = pytesseract.image_to_string(
                            img, lang=language, config=config
                        )
                        text = text.strip()
                        logger.info(f"Tesseract OCR extracted {len(text)} characters")
                        return text
                    except ImportError:
                        logger.debug("pytesseract not installed")
                        return None
                    except Exception as e:
                        logger.warning(f"Tesseract OCR failed: {e}")
                        return None

                def try_winocr() -> Optional[str]:
                    try:
                        import winocr
                        import asyncio as aio

                        async def do_ocr():
                            result = await winocr.recognize_pil(img, lang=language)
                            return result.text

                        try:
                            loop = aio.get_running_loop()
                            import concurrent.futures

                            with concurrent.futures.ThreadPoolExecutor() as pool:
                                future = pool.submit(aio.run, do_ocr())
                                text = future.result()
                        except RuntimeError:
                            text = aio.run(do_ocr())

                        logger.info(f"Windows OCR extracted {len(text)} characters")
                        return text.strip()
                    except ImportError:
                        logger.debug("winocr not installed")
                        return None
                    except Exception as e:
                        logger.warning(f"Windows OCR failed: {e}")
                        return None

                if engine == "rapidocr":
                    result = try_rapidocr()
                    if result is not None:
                        return result
                    logger.error(
                        "RapidOCR not available. Install: pip install rapidocr_onnxruntime"
                    )
                    return None

                elif engine == "tesseract":
                    result = try_tesseract()
                    if result is not None:
                        return result
                    logger.error(
                        "Tesseract not available. Install: pip install pytesseract"
                    )
                    return None

                elif engine == "winocr":
                    result = try_winocr()
                    if result is not None:
                        return result
                    logger.error(
                        "Windows OCR not available. Install: pip install winocr"
                    )
                    return None

                else:
                    result = try_rapidocr()
                    if result is not None:
                        return result

                    result = try_tesseract()
                    if result is not None:
                        return result

                    result = try_winocr()
                    if result is not None:
                        return result

                    logger.error(
                        "No OCR engine available. Install one of: "
                        "rapidocr_onnxruntime, pytesseract, winocr"
                    )
                    return None

            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
                return None

        return await asyncio.to_thread(_extract_text)

    async def compare_images(
        self,
        image1: Any = None,
        image2: Any = None,
        image1_path: str = None,
        image2_path: str = None,
        method: str = "ssim",
        threshold: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Compare two images and return similarity metrics.

        Args:
            image1: First PIL Image object
            image2: Second PIL Image object
            image1_path: Path to first image file
            image2_path: Path to second image file
            method: Comparison method ('ssim', 'histogram', 'pixel')
            threshold: Similarity threshold for match (0.0 to 1.0)

        Returns:
            Dict with similarity score, is_match, and method used
        """

        def _compare() -> Dict[str, Any]:
            try:
                from PIL import Image
                import numpy as np

                img1 = image1
                img2 = image2

                if img1 is None and image1_path:
                    img1 = Image.open(image1_path)
                if img2 is None and image2_path:
                    img2 = Image.open(image2_path)

                if img1 is None or img2 is None:
                    logger.error("Both images required for comparison")
                    return {
                        "similarity": 0.0,
                        "is_match": False,
                        "method": method,
                        "error": "Missing images",
                    }

                if img1.size != img2.size:
                    img2 = img2.resize(img1.size, Image.LANCZOS)

                if img1.mode != img2.mode:
                    img2 = img2.convert(img1.mode)

                arr1 = np.array(img1)
                arr2 = np.array(img2)

                similarity = 0.0
                used_method = method

                if method == "ssim":
                    try:
                        from skimage.metrics import structural_similarity as ssim

                        if len(arr1.shape) == 3:
                            gray1 = np.mean(arr1, axis=2)
                            gray2 = np.mean(arr2, axis=2)
                        else:
                            gray1, gray2 = arr1, arr2
                        similarity = ssim(gray1, gray2, data_range=255)
                    except ImportError:
                        used_method = "histogram"
                        logger.warning("skimage not available, using histogram method")

                if used_method == "histogram":
                    hist1 = img1.histogram()
                    hist2 = img2.histogram()
                    h1 = np.array(hist1, dtype=np.float64)
                    h2 = np.array(hist2, dtype=np.float64)
                    h1 = h1 / (h1.sum() + 1e-10)
                    h2 = h2 / (h2.sum() + 1e-10)
                    similarity = np.sum(np.minimum(h1, h2))

                elif method == "pixel":
                    diff = np.abs(arr1.astype(np.float64) - arr2.astype(np.float64))
                    max_diff = 255.0 * arr1.size
                    actual_diff = np.sum(diff)
                    similarity = 1.0 - (actual_diff / max_diff)

                is_match = similarity >= threshold
                logger.info(
                    f"Image comparison ({used_method}): similarity={similarity:.4f}, "
                    f"threshold={threshold}, match={is_match}"
                )

                return {
                    "similarity": float(similarity),
                    "is_match": is_match,
                    "method": used_method,
                    "threshold": threshold,
                }

            except ImportError as e:
                logger.error(f"Required library not installed: {e}")
                return {
                    "similarity": 0.0,
                    "is_match": False,
                    "method": method,
                    "error": str(e),
                }
            except Exception as e:
                logger.error(f"Image comparison failed: {e}")
                return {
                    "similarity": 0.0,
                    "is_match": False,
                    "method": method,
                    "error": str(e),
                }

        return await asyncio.to_thread(_compare)

    async def find_image_on_screen(
        self,
        template: Any = None,
        template_path: str = None,
        region: Dict[str, int] = None,
        threshold: float = 0.8,
    ) -> Optional[Dict[str, int]]:
        """
        Find a template image on screen using template matching.

        Args:
            template: PIL Image object of the template to find
            template_path: Path to template image file
            region: Dict with x, y, width, height to search in specific region
            threshold: Match confidence threshold (0.0 to 1.0)

        Returns:
            Dict with x, y, width, height if found, None otherwise
        """

        def _find_template() -> Optional[Dict[str, int]]:
            try:
                from PIL import Image, ImageGrab
                import numpy as np

                tmpl = template
                if tmpl is None and template_path:
                    tmpl = Image.open(template_path)

                if tmpl is None:
                    logger.error("Template image required")
                    return None

                if region:
                    x = region.get("x", 0)
                    y = region.get("y", 0)
                    width = region.get("width", 100)
                    height = region.get("height", 100)
                    bbox = (x, y, x + width, y + height)
                    screen = ImageGrab.grab(bbox=bbox)
                    offset_x, offset_y = x, y
                else:
                    screen = ImageGrab.grab()
                    offset_x, offset_y = 0, 0

                try:
                    import cv2
                    from casare_rpa.utils.gpu import gpu_accelerated_template_match

                    screen_gray = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2GRAY)
                    tmpl_gray = cv2.cvtColor(np.array(tmpl), cv2.COLOR_RGB2GRAY)

                    # Use GPU-accelerated template matching if available
                    result, backend = gpu_accelerated_template_match(
                        screen_gray, tmpl_gray, cv2.TM_CCOEFF_NORMED
                    )
                    _, max_val, _, max_loc = cv2.minMaxLoc(result)
                    logger.debug(f"Template matching used: {backend}")

                    if max_val >= threshold:
                        tmpl_height, tmpl_width = tmpl_gray.shape
                        return {
                            "x": max_loc[0] + offset_x,
                            "y": max_loc[1] + offset_y,
                            "width": tmpl_width,
                            "height": tmpl_height,
                            "confidence": float(max_val),
                        }

                    logger.debug(
                        f"Template not found (confidence: {max_val:.4f} < {threshold})"
                    )
                    return None

                except ImportError:
                    logger.error("OpenCV not installed. Run: pip install opencv-python")
                    return None

            except Exception as e:
                logger.error(f"Template matching failed: {e}")
                return None

        return await asyncio.to_thread(_find_template)
