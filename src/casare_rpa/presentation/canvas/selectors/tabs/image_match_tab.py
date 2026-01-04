"""
Image Match Selector Tab.

Find elements by template/image matching using computer vision.
Uses CVHealer for template matching.
"""

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME

if TYPE_CHECKING:
    from playwright.async_api import Page


class ImageMatchTab(BaseSelectorTab):
    """
    Image/template matching selector tab.

    Features:
    - Take screenshot of browser/desktop
    - Capture element region as template or load from file
    - Find template matches with similarity scores
    - Return click coordinates for matched regions
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._browser_page: Page | None = None
        self._cv_healer = None
        self._screenshot_bytes: bytes | None = None
        self._template_bytes: bytes | None = None
        self._matches = []

        self.setup_ui()
        self._init_cv_healer()

    @property
    def tab_name(self) -> str:
        return "Image Match"

    @property
    def tab_icon(self) -> str:
        return "\U0001f5bc"  # Frame with picture emoji

    def setup_ui(self) -> None:
        """Setup tab UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Screenshot section
        screenshot_group = QGroupBox("Target Screenshot")
        screenshot_layout = QVBoxLayout(screenshot_group)

        btn_layout = QHBoxLayout()

        self.capture_btn = QPushButton("Capture Screenshot")
        self.capture_btn.clicked.connect(self._on_capture_clicked)
        self.capture_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.error};
                color: {THEME.text_primary};
                border: 1px solid {THEME.primary_hover};
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME.primary_hover};
            }}
        """)
        btn_layout.addWidget(self.capture_btn)

        btn_layout.addStretch()
        screenshot_layout.addLayout(btn_layout)

        # Screenshot preview
        self.screenshot_scroll = QScrollArea()
        self.screenshot_scroll.setWidgetResizable(True)
        self.screenshot_scroll.setMinimumHeight(150)
        self.screenshot_scroll.setMaximumHeight(200)

        self.screenshot_label = QLabel("No screenshot captured")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setStyleSheet(
            f"background: {THEME.bg_component}; color: {THEME.text_muted}; border-radius: 6px;"
        )
        self.screenshot_scroll.setWidget(self.screenshot_label)

        screenshot_layout.addWidget(self.screenshot_scroll)

        layout.addWidget(screenshot_group)

        # Template section
        template_group = QGroupBox("Template Image")
        template_layout = QVBoxLayout(template_group)

        template_info = QLabel("Load an image file to use as template for matching.")
        template_info.setStyleSheet(f"color: {THEME.text_muted}; font-size: 11px;")
        template_layout.addWidget(template_info)

        template_btn_layout = QHBoxLayout()

        self.load_template_btn = QPushButton("Load Template File")
        self.load_template_btn.clicked.connect(self._on_load_template_clicked)
        template_btn_layout.addWidget(self.load_template_btn)

        self.clear_template_btn = QPushButton("Clear")
        self.clear_template_btn.clicked.connect(self._on_clear_template_clicked)
        self.clear_template_btn.setEnabled(False)
        template_btn_layout.addWidget(self.clear_template_btn)

        template_btn_layout.addStretch()
        template_layout.addLayout(template_btn_layout)

        # Template preview
        self.template_label = QLabel("No template loaded")
        self.template_label.setAlignment(Qt.AlignCenter)
        self.template_label.setMinimumHeight(80)
        self.template_label.setMaximumHeight(120)
        self.template_label.setStyleSheet(
            f"background: {THEME.bg_component}; color: {THEME.text_muted}; border-radius: 6px;"
        )
        template_layout.addWidget(self.template_label)

        layout.addWidget(template_group)

        # Match settings
        settings_group = QGroupBox("Match Settings")
        settings_layout = QVBoxLayout(settings_group)

        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(QLabel("Min Similarity:"))

        self.similarity_slider = QSlider(Qt.Horizontal)
        self.similarity_slider.setMinimum(50)
        self.similarity_slider.setMaximum(100)
        self.similarity_slider.setValue(80)
        thresh_layout.addWidget(self.similarity_slider)

        self.similarity_label = QLabel("80%")
        self.similarity_slider.valueChanged.connect(
            lambda v: self.similarity_label.setText(f"{v}%")
        )
        thresh_layout.addWidget(self.similarity_label)

        settings_layout.addLayout(thresh_layout)

        # Find button
        self.find_btn = QPushButton("Find Template")
        self.find_btn.clicked.connect(self._on_find_clicked)
        self.find_btn.setEnabled(False)
        self.find_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.success};
                color: {THEME.text_primary};
                border: 1px solid {THEME.primary_hover};
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: {THEME.primary_hover};
            }}
            QPushButton:disabled {{
                background: {THEME.text_disabled};
                color: {THEME.text_muted};
            }}
        """)
        settings_layout.addWidget(self.find_btn)

        layout.addWidget(settings_group)

        # Results section
        results_group = QGroupBox("Match Results")
        results_layout = QVBoxLayout(results_group)

        self.results_info = QLabel("Load a template and click 'Find Template'")
        self.results_info.setStyleSheet(f"color: {THEME.text_muted};")
        results_layout.addWidget(self.results_info)

        self.match_preview = QLabel("")
        self.match_preview.setWordWrap(True)
        self.match_preview.setStyleSheet(
            f"padding: 12px; background: {THEME.bg_component}; border-radius: 6px; "
            f"font-family: Consolas; color: {THEME.error};"
        )
        results_layout.addWidget(self.match_preview)

        layout.addWidget(results_group)

        # CV availability warning
        self.cv_warning = QLabel(
            "Image matching requires opencv-python. Install with: pip install opencv-python"
        )
        self.cv_warning.setStyleSheet(
            f"color: {THEME.warning}; padding: 8px; background: {THEME.bg_component}; "
            "border-radius: 4px; font-size: 11px;"
        )
        self.cv_warning.setWordWrap(True)
        self.cv_warning.hide()
        layout.addWidget(self.cv_warning)

        layout.addStretch()

    def _init_cv_healer(self) -> None:
        """Initialize CV healer if available."""
        try:
            from casare_rpa.infrastructure.browser.healing.cv_healer import CVHealer

            self._cv_healer = CVHealer()
            if not self._cv_healer.is_available:
                self.cv_warning.show()
                self._cv_healer = None

        except ImportError:
            logger.debug("CVHealer not available")
            self.cv_warning.show()

    def set_browser_page(self, page: "Page") -> None:
        """Set browser page."""
        self._browser_page = page

    async def start_picking(self) -> None:
        """Start picking - capture screenshot."""
        await self._capture_screenshot()

    async def stop_picking(self) -> None:
        """Stop picking mode."""
        pass

    def get_current_selector(self) -> SelectorResult | None:
        """Get current selector result."""
        return self._current_result

    def get_strategies(self) -> list[SelectorStrategy]:
        """Get generated strategies."""
        return self._strategies

    def _on_capture_clicked(self) -> None:
        """Handle capture button click."""
        asyncio.ensure_future(self._capture_screenshot())

    async def _capture_screenshot(self) -> None:
        """Capture screenshot from browser or desktop."""
        self._emit_status("Capturing screenshot...")

        if self._browser_page:
            try:
                self._screenshot_bytes = await self._browser_page.screenshot(type="png")
                self._display_screenshot()
                self._update_find_button()
                self._emit_status("Screenshot captured from browser")
                return
            except Exception as e:
                logger.error(f"Browser screenshot failed: {e}")

        # Fallback: desktop screenshot
        try:
            import io

            from PIL import ImageGrab

            img = ImageGrab.grab()
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            self._screenshot_bytes = buffer.getvalue()
            self._display_screenshot()
            self._update_find_button()
            self._emit_status("Screenshot captured from desktop")

        except Exception as e:
            logger.error(f"Desktop screenshot failed: {e}")
            self._emit_status(f"Screenshot failed: {e}")

    def _display_screenshot(self) -> None:
        """Display screenshot in preview."""
        if not self._screenshot_bytes:
            return

        image = QImage.fromData(self._screenshot_bytes)
        pixmap = QPixmap.fromImage(image)

        scaled = pixmap.scaled(
            self.screenshot_scroll.width() - 20,
            150,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.screenshot_label.setPixmap(scaled)

    def set_template_from_bytes(self, template_bytes: bytes) -> None:
        """
        Set template image from bytes (e.g., from browser element capture).

        Args:
            template_bytes: PNG image bytes
        """
        if not template_bytes:
            return

        self._template_bytes = template_bytes
        self._display_template()
        self._update_find_button()
        self.clear_template_btn.setEnabled(True)
        self._emit_status("Template captured from browser element")
        logger.info(f"Template set from bytes: {len(template_bytes)} bytes")

    def _on_load_template_clicked(self) -> None:
        """Handle load template button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
        )

        if not file_path:
            return

        try:
            path = Path(file_path)
            self._template_bytes = path.read_bytes()
            self._display_template()
            self._update_find_button()
            self.clear_template_btn.setEnabled(True)
            self._emit_status(f"Template loaded: {path.name}")

        except Exception as e:
            logger.error(f"Failed to load template: {e}")
            self._emit_status(f"Error loading template: {e}")

    def _display_template(self) -> None:
        """Display template in preview."""
        if not self._template_bytes:
            return

        image = QImage.fromData(self._template_bytes)
        pixmap = QPixmap.fromImage(image)

        scaled = pixmap.scaled(
            200,
            100,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.template_label.setPixmap(scaled)

    def _on_clear_template_clicked(self) -> None:
        """Clear loaded template."""
        self._template_bytes = None
        self.template_label.setText("No template loaded")
        self.template_label.setPixmap(QPixmap())
        self.clear_template_btn.setEnabled(False)
        self._update_find_button()

    def _update_find_button(self) -> None:
        """Update find button state."""
        can_find = (
            self._screenshot_bytes is not None
            and self._template_bytes is not None
            and self._cv_healer is not None
        )
        self.find_btn.setEnabled(can_find)

    def _on_find_clicked(self) -> None:
        """Handle find button click."""
        asyncio.ensure_future(self._perform_template_matching())

    async def _perform_template_matching(self) -> None:
        """Perform template matching."""
        if not self._cv_healer:
            self.results_info.setText("CV not available")
            return

        if not self._screenshot_bytes or not self._template_bytes:
            self.results_info.setText("Need screenshot and template")
            return

        self._emit_status("Searching for template...")
        self.results_info.setText("Searching...")

        try:
            # Convert to CV images
            screenshot = self._cv_healer._bytes_to_cv_image(self._screenshot_bytes)
            template = self._cv_healer._bytes_to_cv_image(self._template_bytes)

            # Perform matching
            import asyncio

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                self._cv_healer._perform_template_matching,
                screenshot,
                template,
            )

            # Filter by similarity
            min_sim = self.similarity_slider.value() / 100.0
            matches = [m for m in matches if m.similarity >= min_sim]

            self._matches = matches

            if not matches:
                self.results_info.setText("No matches found")
                self.match_preview.setText("")
                self._strategies = []
                self._current_result = None
                self.selectors_generated.emit([])
                return

            # Sort by similarity
            matches.sort(key=lambda m: -m.similarity)

            self.results_info.setText(f"Found {len(matches)} match(es)")

            # Build strategies
            self._strategies = []
            for _i, match in enumerate(matches[:5]):
                strategy = SelectorStrategy(
                    value=f"image:({match.center_x},{match.center_y})",
                    selector_type="image",
                    score=match.similarity * 100,
                    is_unique=(len(matches) == 1),
                    description=f"Image match at ({match.center_x}, {match.center_y}) - {match.similarity:.1%}",
                )
                self._strategies.append(strategy)

            # Emit strategies
            self.selectors_generated.emit(self._strategies)

            # Show best match
            best = matches[0]
            self.match_preview.setText(
                f"Position: ({best.x}, {best.y})\n"
                f"Size: {best.width} x {best.height}\n"
                f"Click at: ({best.center_x}, {best.center_y})\n"
                f"Similarity: {best.similarity:.1%}"
            )

            # Build result
            self._current_result = SelectorResult(
                selector_value=f"image:({best.center_x},{best.center_y})",
                selector_type="image",
                confidence=best.similarity,
                is_unique=(len(matches) == 1),
                healing_context={
                    "template_match": best.to_dict(),
                },
                metadata={
                    "click_x": best.center_x,
                    "click_y": best.center_y,
                    "bounding_box": {
                        "x": best.x,
                        "y": best.y,
                        "width": best.width,
                        "height": best.height,
                    },
                },
            )

            self._emit_status(f"Found {len(matches)} match(es)")

        except Exception as e:
            logger.error(f"Template matching failed: {e}")
            self.results_info.setText(f"Error: {e}")
            self._emit_status(f"Matching error: {e}")

    async def test_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """Test selector - re-run template matching."""
        if not self._cv_healer or not self._screenshot_bytes or not self._template_bytes:
            return {"success": False, "error": "Not ready"}

        try:
            screenshot = self._cv_healer._bytes_to_cv_image(self._screenshot_bytes)
            template = self._cv_healer._bytes_to_cv_image(self._template_bytes)

            import asyncio

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                self._cv_healer._perform_template_matching,
                screenshot,
                template,
            )

            min_sim = self.similarity_slider.value() / 100.0
            matches = [m for m in matches if m.similarity >= min_sim]

            return {
                "success": True,
                "count": len(matches),
                "time_ms": 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def highlight_selector(self, selector: str, selector_type: str) -> bool:
        """Highlight is done by showing match preview."""
        return True

    def clear(self) -> None:
        """Clear current state."""
        super().clear()
        self._screenshot_bytes = None
        self._template_bytes = None
        self._matches = []
        self.screenshot_label.setText("No screenshot captured")
        self.screenshot_label.setPixmap(QPixmap())
        self.template_label.setText("No template loaded")
        self.template_label.setPixmap(QPixmap())
        self.results_info.setText("Load a template and click 'Find Template'")
        self.match_preview.setText("")
        self.clear_template_btn.setEnabled(False)
        self._update_find_button()
