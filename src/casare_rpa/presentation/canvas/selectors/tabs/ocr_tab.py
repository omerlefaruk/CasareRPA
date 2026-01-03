"""
OCR Selector Tab.

Find elements by visible text using OCR (Optical Character Recognition).
Uses CVHealer for text detection.
"""

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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


class OCRSelectorTab(BaseSelectorTab):
    """
    OCR text selector tab.

    Features:
    - Take screenshot of browser/desktop
    - Enter text to find using OCR
    - Show matches with confidence scores
    - Return click coordinates for matched text
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._browser_page: Page | None = None
        self._cv_healer = None
        self._screenshot_bytes: bytes | None = None
        self._matches = []

        self.setup_ui()
        self._init_cv_healer()

    @property
    def tab_name(self) -> str:
        return "OCR Text"

    @property
    def tab_icon(self) -> str:
        return "\U0001f4dd"  # Memo emoji

    def setup_ui(self) -> None:
        """Setup tab UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Screenshot section
        screenshot_group = QGroupBox("Screenshot")
        screenshot_layout = QVBoxLayout(screenshot_group)

        btn_layout = QHBoxLayout()

        self.capture_btn = QPushButton("Capture Screenshot")
        self.capture_btn.clicked.connect(self._on_capture_clicked)
        self.capture_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.primary};
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
        self.screenshot_scroll.setMinimumHeight(200)
        self.screenshot_scroll.setMaximumHeight(300)

        self.screenshot_label = QLabel("No screenshot captured")
        self.screenshot_label.setAlignment(Qt.AlignCenter)
        self.screenshot_label.setStyleSheet(
            f"background: {THEME.bg_component}; color: {THEME.text_muted}; border-radius: 6px;"
        )
        self.screenshot_scroll.setWidget(self.screenshot_label)

        screenshot_layout.addWidget(self.screenshot_scroll)

        layout.addWidget(screenshot_group)

        # Search section
        search_group = QGroupBox("Search Text")
        search_layout = QVBoxLayout(search_group)

        input_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter text to find...")
        self.search_input.returnPressed.connect(self._on_search_clicked)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 10px;
                border: 1px solid {THEME.border};
                border-radius: 6px;
                background: {THEME.bg_canvas};
                color: {THEME.text_primary};
                font-size: 14px;
            }}
        """)
        input_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Find")
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.success};
                color: {THEME.text_primary};
                border: 1px solid {THEME.primary_hover};
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background: {THEME.primary_hover};
            }}
        """)
        input_layout.addWidget(self.search_btn)

        search_layout.addLayout(input_layout)

        # Confidence threshold
        thresh_layout = QHBoxLayout()
        thresh_layout.addWidget(QLabel("Min Confidence:"))

        self.confidence_slider = QSlider(Qt.Horizontal)
        self.confidence_slider.setMinimum(0)
        self.confidence_slider.setMaximum(100)
        self.confidence_slider.setValue(70)
        thresh_layout.addWidget(self.confidence_slider)

        self.confidence_label = QLabel("70%")
        self.confidence_slider.valueChanged.connect(
            lambda v: self.confidence_label.setText(f"{v}%")
        )
        thresh_layout.addWidget(self.confidence_label)

        search_layout.addLayout(thresh_layout)

        layout.addWidget(search_group)

        # Results section
        results_group = QGroupBox("OCR Matches")
        results_layout = QVBoxLayout(results_group)

        self.results_info = QLabel("Enter text and click 'Find' to search")
        self.results_info.setStyleSheet(f"color: {THEME.text_muted};")
        results_layout.addWidget(self.results_info)

        # Match preview (shows coordinates)
        self.match_preview = QLabel("")
        self.match_preview.setWordWrap(True)
        self.match_preview.setStyleSheet(
            f"padding: 12px; background: {THEME.bg_component}; border-radius: 6px; "
            f"font-family: Consolas; color: {THEME.wire_data};"
        )
        results_layout.addWidget(self.match_preview)

        layout.addWidget(results_group)

        # CV availability warning
        self.cv_warning = QLabel(
            "OCR requires opencv-python and pytesseract. "
            "Install with: pip install opencv-python pytesseract"
        )
        self.cv_warning.setStyleSheet(
            "color: #fbbf24; padding: 8px; background: #3d3520; "
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

        # Scale to fit
        scaled = pixmap.scaled(
            self.screenshot_scroll.width() - 20,
            self.screenshot_scroll.height() - 20,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )

        self.screenshot_label.setPixmap(scaled)

    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        search_text = self.search_input.text().strip()
        if not search_text:
            return

        asyncio.ensure_future(self._perform_ocr_search(search_text))

    async def _perform_ocr_search(self, search_text: str) -> None:
        """Perform OCR search for text."""
        if not self._cv_healer:
            self.results_info.setText("OCR not available - install dependencies")
            return

        if not self._screenshot_bytes:
            self.results_info.setText("Capture a screenshot first")
            return

        self._emit_status("Searching for text...")
        self.results_info.setText("Searching...")

        try:
            # Convert screenshot to CV image
            screenshot = self._cv_healer._bytes_to_cv_image(self._screenshot_bytes)

            # Perform OCR
            import asyncio

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                self._cv_healer._perform_ocr,
                screenshot,
                search_text,
            )

            # Filter by confidence
            min_conf = self.confidence_slider.value() / 100.0
            matches = [m for m in matches if m.confidence >= min_conf]

            self._matches = matches

            if not matches:
                self.results_info.setText("No matches found")
                self.match_preview.setText("")
                self._strategies = []
                self._current_result = None
                self.selectors_generated.emit([])
                return

            # Sort by confidence
            matches.sort(key=lambda m: -m.confidence)

            self.results_info.setText(f"Found {len(matches)} match(es)")

            # Build strategies
            self._strategies = []
            for _i, match in enumerate(matches[:5]):
                strategy = SelectorStrategy(
                    value=f"ocr:{search_text}@({match.center_x},{match.center_y})",
                    selector_type="ocr",
                    score=match.confidence * 100,
                    is_unique=(len(matches) == 1),
                    description=f"OCR: '{match.text}' at ({match.center_x}, {match.center_y})",
                )
                self._strategies.append(strategy)

            # Emit strategies
            self.selectors_generated.emit(self._strategies)

            # Show best match
            best = matches[0]
            self.match_preview.setText(
                f'Text: "{best.text}"\n'
                f"Position: ({best.x}, {best.y})\n"
                f"Size: {best.width} x {best.height}\n"
                f"Click at: ({best.center_x}, {best.center_y})\n"
                f"Confidence: {best.confidence:.1%}"
            )

            # Build result
            self._current_result = SelectorResult(
                selector_value=f"ocr:{search_text}",
                selector_type="ocr",
                confidence=best.confidence,
                is_unique=(len(matches) == 1),
                healing_context={
                    "search_text": search_text,
                    "ocr_match": best.to_dict(),
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

            self._emit_status(f"Found {len(matches)} match(es) for '{search_text}'")

        except Exception as e:
            logger.error(f"OCR search failed: {e}")
            self.results_info.setText(f"Error: {e}")
            self._emit_status(f"OCR error: {e}")

    async def test_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """Test selector - re-run OCR search."""
        if not self._cv_healer or not self._screenshot_bytes:
            return {"success": False, "error": "OCR not available or no screenshot"}

        # Extract search text from selector
        search_text = selector
        if selector.startswith("ocr:"):
            search_text = selector[4:].split("@")[0]

        try:
            screenshot = self._cv_healer._bytes_to_cv_image(self._screenshot_bytes)

            import asyncio

            loop = asyncio.get_event_loop()
            matches = await loop.run_in_executor(
                None,
                self._cv_healer._perform_ocr,
                screenshot,
                search_text,
            )

            min_conf = self.confidence_slider.value() / 100.0
            matches = [m for m in matches if m.confidence >= min_conf]

            return {
                "success": True,
                "count": len(matches),
                "time_ms": 0,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def highlight_selector(self, selector: str, selector_type: str) -> bool:
        """Highlight is done by showing match preview."""
        # Could draw rectangles on screenshot preview
        return True

    def clear(self) -> None:
        """Clear current state."""
        super().clear()
        self._screenshot_bytes = None
        self._matches = []
        self.screenshot_label.setText("No screenshot captured")
        self.screenshot_label.setPixmap(QPixmap())
        self.search_input.clear()
        self.results_info.setText("Enter text and click 'Find' to search")
        self.match_preview.setText("")

