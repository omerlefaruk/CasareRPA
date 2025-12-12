"""
CasareRPA - Visual Regression Testing.

Provides canvas screenshot comparison for UI testing.
Captures widget states and compares against baseline images.

Usage:
    @pytest.fixture
    def visual_test(qtbot):
        return VisualRegressionTest()

    def test_canvas_with_nodes(visual_test, canvas_widget):
        # Add nodes to canvas...
        result = visual_test.compare_with_baseline(
            "canvas_with_nodes",
            visual_test.capture_canvas(canvas_widget)
        )
        assert result.passed, f"Visual regression failed: {result.similarity:.2%}"

    # Update baseline when UI intentionally changes
    def test_update_baseline(visual_test, canvas_widget):
        visual_test.update_baseline("canvas_with_nodes", canvas_widget)
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from loguru import logger

try:
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    from PySide6.QtGui import QImage, QPixmap
    from PySide6.QtWidgets import QWidget

    HAS_PYSIDE6 = True
except ImportError:
    HAS_PYSIDE6 = False
    logger.warning("PySide6 not available - visual regression tests disabled")


@dataclass
class ComparisonResult:
    """Result of visual comparison."""

    passed: bool
    similarity: float
    is_new: bool = False
    baseline_path: Optional[str] = None
    diff_path: Optional[str] = None
    message: str = ""


class VisualRegressionTest:
    """
    Visual regression test helper for canvas UI testing.

    Captures widget screenshots and compares against baseline images
    stored in tests/baselines/.

    Features:
    - Automatic baseline creation for new tests
    - Configurable similarity threshold
    - Diff image generation on failure
    - Support for updating baselines via flag
    """

    def __init__(
        self,
        baseline_dir: Union[str, Path] = "tests/baselines",
        threshold: float = 0.99,
        save_diff_on_failure: bool = True,
    ) -> None:
        """
        Initialize visual regression test helper.

        Args:
            baseline_dir: Directory for baseline images
            threshold: Minimum similarity (0.0-1.0) to pass
            save_diff_on_failure: Whether to save diff images on failure
        """
        self.baseline_dir = Path(baseline_dir)
        self.threshold = threshold
        self.save_diff_on_failure = save_diff_on_failure

        # Ensure baseline directory exists
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

        # Diff images stored in baselines/diffs/
        self.diff_dir = self.baseline_dir / "diffs"
        self.diff_dir.mkdir(exist_ok=True)

    def capture_widget(self, widget: "QWidget") -> "QPixmap":
        """
        Capture a widget as a QPixmap.

        Args:
            widget: QWidget to capture

        Returns:
            QPixmap of the widget

        Raises:
            RuntimeError: If PySide6 not available
        """
        if not HAS_PYSIDE6:
            raise RuntimeError("PySide6 required for visual regression testing")

        return widget.grab()

    def capture_canvas(self, canvas_widget: "QWidget") -> "QPixmap":
        """
        Capture a canvas widget (NodeGraphQt graph).

        This is an alias for capture_widget with canvas-specific
        handling if needed in the future.

        Args:
            canvas_widget: Canvas widget to capture

        Returns:
            QPixmap of the canvas
        """
        return self.capture_widget(canvas_widget)

    def compare_with_baseline(
        self,
        name: str,
        current: "QPixmap",
        threshold: Optional[float] = None,
    ) -> ComparisonResult:
        """
        Compare a screenshot against its baseline.

        If no baseline exists, the current image is saved as the
        new baseline and is_new=True is returned.

        Args:
            name: Test name (used for baseline filename)
            current: Current screenshot as QPixmap
            threshold: Optional custom threshold (uses instance default if None)

        Returns:
            ComparisonResult with passed status, similarity, and paths
        """
        if not HAS_PYSIDE6:
            return ComparisonResult(
                passed=False,
                similarity=0.0,
                message="PySide6 not available",
            )

        threshold = threshold if threshold is not None else self.threshold
        baseline_path = self.baseline_dir / f"{name}.png"

        # If no baseline exists, create it
        if not baseline_path.exists():
            current.save(str(baseline_path), "PNG")
            logger.info(f"Created new baseline: {baseline_path}")
            return ComparisonResult(
                passed=True,
                similarity=1.0,
                is_new=True,
                baseline_path=str(baseline_path),
                message="New baseline created",
            )

        # Load baseline
        baseline = QPixmap(str(baseline_path))
        if baseline.isNull():
            return ComparisonResult(
                passed=False,
                similarity=0.0,
                baseline_path=str(baseline_path),
                message=f"Failed to load baseline: {baseline_path}",
            )

        # Compare images
        similarity = self._compare_images(current, baseline)
        passed = similarity >= threshold

        result = ComparisonResult(
            passed=passed,
            similarity=similarity,
            baseline_path=str(baseline_path),
            message=f"Similarity: {similarity:.2%} (threshold: {threshold:.2%})",
        )

        # Generate diff on failure
        if not passed and self.save_diff_on_failure:
            diff_path = self.diff_dir / f"{name}_diff.png"
            self._save_diff_image(current, baseline, diff_path)
            result.diff_path = str(diff_path)

            # Also save the current screenshot
            current_path = self.diff_dir / f"{name}_current.png"
            current.save(str(current_path), "PNG")

        return result

    def update_baseline(
        self,
        name: str,
        widget: "QWidget",
    ) -> str:
        """
        Update a baseline image from a widget.

        Use this when UI has intentionally changed and you want
        to update the expected baseline.

        Args:
            name: Test name (baseline filename)
            widget: Widget to capture as new baseline

        Returns:
            Path to the updated baseline
        """
        if not HAS_PYSIDE6:
            raise RuntimeError("PySide6 required for visual regression testing")

        baseline_path = self.baseline_dir / f"{name}.png"
        pixmap = self.capture_widget(widget)
        pixmap.save(str(baseline_path), "PNG")
        logger.info(f"Updated baseline: {baseline_path}")
        return str(baseline_path)

    def get_baseline_path(self, name: str) -> Path:
        """Get the path to a baseline image."""
        return self.baseline_dir / f"{name}.png"

    def baseline_exists(self, name: str) -> bool:
        """Check if a baseline exists for the given name."""
        return self.get_baseline_path(name).exists()

    def delete_baseline(self, name: str) -> bool:
        """
        Delete a baseline image.

        Args:
            name: Test name (baseline filename)

        Returns:
            True if deleted, False if didn't exist
        """
        path = self.get_baseline_path(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def _compare_images(
        self,
        img1: "QPixmap",
        img2: "QPixmap",
    ) -> float:
        """
        Compare two images and return similarity (0.0-1.0).

        Uses pixel-by-pixel comparison. For more sophisticated
        comparison (SSIM), numpy and scikit-image would be needed.

        Args:
            img1: First image
            img2: Second image

        Returns:
            Similarity ratio (1.0 = identical)
        """
        # Convert to QImage for pixel access
        image1 = img1.toImage()
        image2 = img2.toImage()

        # Size check
        if image1.size() != image2.size():
            logger.warning(f"Image size mismatch: {image1.size()} vs {image2.size()}")
            return 0.0

        width = image1.width()
        height = image1.height()
        total_pixels = width * height

        if total_pixels == 0:
            return 1.0

        matching_pixels = 0

        # Compare pixels
        for y in range(height):
            for x in range(width):
                pixel1 = image1.pixel(x, y)
                pixel2 = image2.pixel(x, y)
                if pixel1 == pixel2:
                    matching_pixels += 1

        return matching_pixels / total_pixels

    def _save_diff_image(
        self,
        current: "QPixmap",
        baseline: "QPixmap",
        output_path: Path,
    ) -> None:
        """
        Generate and save a diff image highlighting differences.

        Differences are shown in red on a semi-transparent overlay.

        Args:
            current: Current screenshot
            baseline: Baseline screenshot
            output_path: Where to save the diff image
        """
        from PySide6.QtGui import QColor, QPainter

        image1 = current.toImage()
        image2 = baseline.toImage()

        # Create diff image
        width = min(image1.width(), image2.width())
        height = min(image1.height(), image2.height())

        diff_image = QImage(width, height, QImage.Format_ARGB32)
        diff_image.fill(QColor(255, 255, 255, 255))

        for y in range(height):
            for x in range(width):
                pixel1 = (
                    image1.pixel(x, y)
                    if x < image1.width() and y < image1.height()
                    else 0
                )
                pixel2 = (
                    image2.pixel(x, y)
                    if x < image2.width() and y < image2.height()
                    else 0
                )

                if pixel1 != pixel2:
                    # Mark difference in red
                    diff_image.setPixel(x, y, QColor(255, 0, 0, 200).rgba())
                else:
                    # Keep original pixel (faded)
                    color = QColor(pixel1)
                    color.setAlpha(100)
                    diff_image.setPixel(x, y, color.rgba())

        QPixmap.fromImage(diff_image).save(str(output_path), "PNG")
        logger.debug(f"Saved diff image: {output_path}")


# Convenience function for pytest
def visual_regression_test(
    baseline_dir: Union[str, Path] = "tests/baselines",
) -> VisualRegressionTest:
    """
    Create a visual regression test helper.

    Convenience function for use in pytest fixtures.

    Usage:
        @pytest.fixture
        def visual_test():
            return visual_regression_test()

    Args:
        baseline_dir: Directory for baseline images

    Returns:
        VisualRegressionTest instance
    """
    return VisualRegressionTest(baseline_dir=baseline_dir)
