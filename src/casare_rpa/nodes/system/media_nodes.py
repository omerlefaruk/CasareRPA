"""
Media nodes for CasareRPA.

This module provides media-related nodes:
- TextToSpeechNode: Read text aloud using pyttsx3
- PDFPreviewDialogNode: Preview PDF with page navigation
- WebcamCaptureNode: Capture image from webcam
"""

import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType
from casare_rpa.domain.value_objects.types import (
    NodeStatus,
    DataType,
)
from casare_rpa.infrastructure.execution import ExecutionContext


# =============================================================================
# TextToSpeechNode - Read text aloud using pyttsx3
# =============================================================================


@properties(
    PropertyDef(
        "text",
        PropertyType.TEXT,
        required=True,
        label="Text",
        tooltip="Text to speak",
        essential=True,
    ),
    PropertyDef(
        "speech_text",
        PropertyType.TEXT,
        required=False,
        label="Speech Text",
        tooltip="Text to speak (deprecated, use 'text')",
    ),
    PropertyDef(
        "rate",
        PropertyType.INTEGER,
        default=150,
        min_value=50,
        max_value=300,
        label="Rate",
        tooltip="Speech rate (words per minute)",
    ),
    PropertyDef(
        "volume",
        PropertyType.FLOAT,
        default=1.0,
        min_value=0.0,
        max_value=1.0,
        label="Volume",
        tooltip="Volume level (0.0 to 1.0)",
    ),
    PropertyDef(
        "wait",
        PropertyType.BOOLEAN,
        default=True,
        label="Wait",
        tooltip="Wait for speech to complete before continuing",
    ),
)
@node(category="system")
class TextToSpeechNode(BaseNode):
    """Read text aloud using text-to-speech."""

    # @category: system
    # @requires: opencv, pdf
    # @ports: text -> success

    def __init__(self, node_id: str, name: str = "Text to Speech", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "TextToSpeechNode"

    def _define_ports(self) -> None:
        self.add_input_port("text", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            rate = int(self.get_parameter("rate", 150) or 150)
            volume = float(self.get_parameter("volume", 1.0) or 1.0)
            wait = self.get_parameter("wait", True)

            text = self.get_input_value("text")
            if text is None:
                text = self.get_parameter("speech_text", "")
            # Resolve variables first, THEN convert to string (resolve preserves types for {{var}} patterns)
            text = str(context.resolve_value(text) or "")

            if not text:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "Text is required",
                    "outputs": {"success": False},
                }

            try:
                import pyttsx3
            except ImportError:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "pyttsx3 library not installed. Install with: pip install pyttsx3",
                    "outputs": {"success": False},
                }

            def speak():
                engine = pyttsx3.init()
                engine.setProperty("rate", rate)
                engine.setProperty("volume", max(0.0, min(1.0, volume)))
                engine.say(text)
                if wait:
                    engine.runAndWait()
                else:
                    engine.startLoop(False)
                    engine.iterate()
                    engine.endLoop()

            if wait:
                await asyncio.get_event_loop().run_in_executor(None, speak)
            else:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, speak)

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {"success": True},
            }

        except Exception as e:
            logger.error(f"TextToSpeechNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"success": False},
            }


# =============================================================================
# PDFPreviewDialogNode - Preview PDF with page navigation
# =============================================================================


@properties(
    PropertyDef(
        "pdf_path",
        PropertyType.FILE_PATH,
        required=True,
        label="PDF Path",
        tooltip="Path to the PDF file to preview",
        essential=True,
    ),
    PropertyDef(
        "initial_page",
        PropertyType.INTEGER,
        default=1,
        min_value=1,
        label="Initial Page",
        tooltip="Page number to start on",
    ),
    PropertyDef(
        "zoom",
        PropertyType.FLOAT,
        default=1.0,
        min_value=0.25,
        max_value=4.0,
        label="Zoom",
        tooltip="Zoom level (0.25 to 4.0)",
    ),
)
@node(category="system")
class PDFPreviewDialogNode(BaseNode):
    """Preview a PDF file with page navigation."""

    # @category: system
    # @requires: opencv, pdf
    # @ports: none -> confirmed, current_page, page_count

    def __init__(self, node_id: str, name: str = "PDF Preview", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "PDFPreviewDialogNode"

    def _define_ports(self) -> None:
        self.add_output_port("confirmed", DataType.BOOLEAN)
        self.add_output_port("current_page", DataType.INTEGER)
        self.add_output_port("page_count", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            pdf_path = self.get_parameter("pdf_path", "")
            initial_page = int(self.get_parameter("initial_page", 1) or 1)
            zoom = float(self.get_parameter("zoom", 1.0) or 1.0)

            pdf_path = context.resolve_value(str(pdf_path))

            if not pdf_path or not os.path.exists(pdf_path):
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": f"PDF file not found: {pdf_path}",
                    "outputs": {"confirmed": False, "current_page": 0, "page_count": 0},
                }

            try:
                import fitz  # PyMuPDF
            except ImportError:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "PyMuPDF library not installed. Install with: pip install PyMuPDF",
                    "outputs": {"confirmed": False, "current_page": 0, "page_count": 0},
                }

            doc = fitz.open(pdf_path)
            page_count = len(doc)

            if page_count == 0:
                doc.close()
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "PDF has no pages",
                    "outputs": {"confirmed": False, "current_page": 0, "page_count": 0},
                }

            initial_page = max(1, min(initial_page, page_count))

            from PySide6.QtWidgets import (
                QDialog,
                QVBoxLayout,
                QHBoxLayout,
                QLabel,
                QPushButton,
                QScrollArea,
                QSpinBox,
                QApplication,
            )
            from PySide6.QtCore import Qt
            from PySide6.QtGui import QPixmap, QImage

            app = QApplication.instance()
            if app is None:
                doc.close()
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "No QApplication instance",
                    "outputs": {"confirmed": False, "current_page": 0, "page_count": 0},
                }

            future = asyncio.get_event_loop().create_future()

            class PDFPreviewDialog(QDialog):
                def __init__(
                    self, pdf_doc, start_page: int, zoom_level: float, result_future
                ):
                    super().__init__()
                    self._future = result_future
                    self.doc = pdf_doc
                    self.current_page = start_page
                    self.zoom_level = zoom_level
                    self.page_count = len(pdf_doc)

                    self.setWindowTitle(f"PDF Preview - {Path(pdf_path).name}")
                    self.setMinimumSize(600, 800)
                    self.setWindowFlags(
                        self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint
                    )
                    self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

                    self._setup_ui()
                    self._render_page()

                def _setup_ui(self):
                    layout = QVBoxLayout(self)

                    nav_layout = QHBoxLayout()

                    self.prev_btn = QPushButton("< Previous")
                    self.prev_btn.clicked.connect(self._prev_page)
                    nav_layout.addWidget(self.prev_btn)

                    nav_layout.addStretch()

                    self.page_spin = QSpinBox()
                    self.page_spin.setMinimum(1)
                    self.page_spin.setMaximum(self.page_count)
                    self.page_spin.setValue(self.current_page)
                    self.page_spin.valueChanged.connect(self._go_to_page)
                    nav_layout.addWidget(QLabel("Page:"))
                    nav_layout.addWidget(self.page_spin)
                    nav_layout.addWidget(QLabel(f"of {self.page_count}"))

                    nav_layout.addStretch()

                    self.next_btn = QPushButton("Next >")
                    self.next_btn.clicked.connect(self._next_page)
                    nav_layout.addWidget(self.next_btn)

                    layout.addLayout(nav_layout)

                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)
                    scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

                    self.page_label = QLabel()
                    self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    scroll.setWidget(self.page_label)
                    layout.addWidget(scroll)

                    close_btn = QPushButton("Close")
                    close_btn.clicked.connect(self.accept)
                    layout.addWidget(close_btn)

                def _render_page(self):
                    page = self.doc[self.current_page - 1]
                    mat = fitz.Matrix(self.zoom_level * 2, self.zoom_level * 2)
                    pix = page.get_pixmap(matrix=mat)

                    img_data = pix.samples
                    if pix.alpha:
                        fmt = QImage.Format.Format_RGBA8888
                    else:
                        fmt = QImage.Format.Format_RGB888

                    qimg = QImage(img_data, pix.width, pix.height, pix.stride, fmt)
                    pixmap = QPixmap.fromImage(qimg)
                    self.page_label.setPixmap(pixmap)

                    self.prev_btn.setEnabled(self.current_page > 1)
                    self.next_btn.setEnabled(self.current_page < self.page_count)

                def _prev_page(self):
                    if self.current_page > 1:
                        self.current_page -= 1
                        self.page_spin.setValue(self.current_page)
                        self._render_page()

                def _next_page(self):
                    if self.current_page < self.page_count:
                        self.current_page += 1
                        self.page_spin.setValue(self.current_page)
                        self._render_page()

                def _go_to_page(self, page: int):
                    self.current_page = page
                    self._render_page()

                def _set_result(self, accepted: bool):
                    if not self._future.done():
                        self._future.set_result(
                            {
                                "confirmed": accepted,
                                "current_page": self.current_page,
                                "page_count": self.page_count,
                            }
                        )
                    self.doc.close()

                def closeEvent(self, event):
                    self._set_result(False)
                    super().closeEvent(event)

            dialog = PDFPreviewDialog(doc, initial_page, zoom, future)

            def on_finished(result_code):
                if not future.done():
                    dialog._set_result(result_code == QDialog.DialogCode.Accepted)

            dialog.finished.connect(on_finished)
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()

            result = await future

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": result,
            }

        except Exception as e:
            logger.error(f"PDFPreviewDialogNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {"confirmed": False, "current_page": 0, "page_count": 0},
            }


# =============================================================================
# WebcamCaptureNode - Capture image from webcam
# =============================================================================


@properties(
    PropertyDef(
        "camera_id",
        PropertyType.INTEGER,
        default=0,
        min_value=0,
        max_value=10,
        label="Camera ID",
        tooltip="Camera device index (0 is usually default camera)",
    ),
    PropertyDef(
        "output_path",
        PropertyType.FILE_PATH,
        default="",
        label="Output Path",
        tooltip="Path to save the captured image",
    ),
    PropertyDef(
        "show_preview",
        PropertyType.BOOLEAN,
        default=True,
        label="Show Preview",
        tooltip="Show preview window before capturing",
    ),
)
@node(category="system")
class WebcamCaptureNode(BaseNode):
    """Capture an image from a webcam."""

    # @category: system
    # @requires: opencv, pdf
    # @ports: none -> image_path, success, width, height

    def __init__(self, node_id: str, name: str = "Webcam Capture", **kwargs) -> None:
        config = kwargs.get("config", {})
        super().__init__(node_id, config)
        self.name = name
        self.node_type = "WebcamCaptureNode"

    def _define_ports(self) -> None:
        self.add_output_port("image_path", DataType.STRING)
        self.add_output_port("success", DataType.BOOLEAN)
        self.add_output_port("width", DataType.INTEGER)
        self.add_output_port("height", DataType.INTEGER)

    async def execute(self, context: ExecutionContext) -> Optional[Dict[str, Any]]:
        self.status = NodeStatus.RUNNING

        try:
            camera_id = int(self.get_parameter("camera_id", 0) or 0)
            output_path = self.get_parameter("output_path", "")
            show_preview = self.get_parameter("show_preview", True)

            output_path = context.resolve_value(str(output_path))

            if not output_path:
                output_path = os.path.join(
                    tempfile.gettempdir(),
                    f"webcam_capture_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                )

            try:
                import cv2
            except ImportError:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": "opencv-python library not installed. Install with: pip install opencv-python",
                    "outputs": {
                        "image_path": "",
                        "success": False,
                        "width": 0,
                        "height": 0,
                    },
                }

            def capture_image() -> Dict[str, Any]:
                cap = cv2.VideoCapture(camera_id)

                if not cap.isOpened():
                    return {
                        "success": False,
                        "error": f"Could not open camera {camera_id}",
                        "image_path": "",
                        "width": 0,
                        "height": 0,
                    }

                for _ in range(5):
                    cap.read()

                if show_preview:
                    window_name = (
                        "Webcam Capture - Press SPACE to capture, ESC to cancel"
                    )
                    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
                    cv2.resizeWindow(window_name, 640, 480)

                    captured = False
                    frame = None

                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        cv2.imshow(window_name, frame)
                        key = cv2.waitKey(1) & 0xFF

                        if key == 32:  # SPACE
                            captured = True
                            break
                        elif key == 27:  # ESC
                            break

                    cv2.destroyWindow(window_name)

                    if not captured or frame is None:
                        cap.release()
                        return {
                            "success": False,
                            "error": "Capture cancelled",
                            "image_path": "",
                            "width": 0,
                            "height": 0,
                        }
                else:
                    ret, frame = cap.read()
                    if not ret or frame is None:
                        cap.release()
                        return {
                            "success": False,
                            "error": "Failed to capture frame",
                            "image_path": "",
                            "width": 0,
                            "height": 0,
                        }

                Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                cv2.imwrite(output_path, frame)
                height, width = frame.shape[:2]

                cap.release()

                return {
                    "success": True,
                    "image_path": output_path,
                    "width": width,
                    "height": height,
                }

            result = await asyncio.get_event_loop().run_in_executor(None, capture_image)

            if not result["success"]:
                self.status = NodeStatus.ERROR
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "outputs": {
                        "image_path": "",
                        "success": False,
                        "width": 0,
                        "height": 0,
                    },
                }

            self.status = NodeStatus.SUCCESS
            return {
                "success": True,
                "outputs": {
                    "image_path": result["image_path"],
                    "success": True,
                    "width": result["width"],
                    "height": result["height"],
                },
            }

        except Exception as e:
            logger.error(f"WebcamCaptureNode error: {e}")
            self.status = NodeStatus.ERROR
            return {
                "success": False,
                "error": str(e),
                "outputs": {
                    "image_path": "",
                    "success": False,
                    "width": 0,
                    "height": 0,
                },
            }
