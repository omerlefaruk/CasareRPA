"""
Element Picker Overlay

Full-screen transparent overlay for visually selecting desktop UI elements
with hover highlighting and click-to-select functionality.
"""

import uiautomation as auto
from loguru import logger
from PySide6.QtCore import QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QCursor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QLabel, QWidget

from casare_rpa.desktop.element import DesktopElement


class ElementPickerOverlay(QWidget):
    """
    Full-screen transparent overlay for picking desktop elements.

    Features:
    - Transparent background
    - Red highlight on hover
    - Click to select element
    - ESC to cancel
    - Global hotkey support (Ctrl+Shift+F3)
    """

    element_selected = Signal(object)  # Emits DesktopElement when clicked
    cancelled = Signal()  # Emits when ESC pressed or cancelled

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_element: DesktopElement | None = None
        self.current_rect: QRect | None = None
        self.hover_timer: QTimer | None = None

        self._setup_ui()
        self._start_tracking()

    def _setup_ui(self):
        """Setup overlay UI"""
        # Make fullscreen, transparent, always on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.setWindowState(Qt.WindowFullScreen)

        # Set cursor to crosshair
        self.setCursor(Qt.CrossCursor)

        # Info label at top
        self.info_label = QLabel(self)
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(13, 126, 189, 200);
                color: white;
                padding: 12px 20px;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.info_label.setText("🎯 Hover over an element and click to select • ESC to cancel")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.adjustSize()

        # Position at top center
        screen_geometry = QApplication.primaryScreen().geometry()
        label_x = (screen_geometry.width() - self.info_label.width()) // 2
        self.info_label.move(label_x, 20)

        # Element info label (shows on hover)
        self.element_info_label = QLabel(self)
        self.element_info_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-family: 'Consolas', monospace;
            }
        """)
        self.element_info_label.hide()

        logger.info("Element picker overlay initialized")

    def _start_tracking(self):
        """Start tracking mouse position"""
        # Use QTimer to periodically check element under cursor
        self.hover_timer = QTimer(self)
        self.hover_timer.timeout.connect(self._update_hover_element)
        self.hover_timer.start(100)  # Check every 100ms

    def _is_same_element(self, control1, control2) -> bool:
        """
        Check if two UI Automation controls represent the same element.

        Uses runtime ID comparison which is more reliable than object equality
        for COM objects.
        """
        try:
            # Compare using RuntimeId which uniquely identifies an element
            runtime_id1 = control1.GetRuntimeId()
            runtime_id2 = control2.GetRuntimeId()
            return runtime_id1 == runtime_id2
        except Exception:
            # Fallback to native window handle comparison if available
            try:
                hwnd1 = getattr(control1, "NativeWindowHandle", None)
                hwnd2 = getattr(control2, "NativeWindowHandle", None)
                if hwnd1 and hwnd2:
                    return hwnd1 == hwnd2
            except Exception:
                pass
            # Last resort: compare string representations
            return str(control1) == str(control2)

    def _update_hover_element(self):
        """Update the element under cursor"""
        try:
            # Get cursor position
            cursor_pos = QCursor.pos()

            # Get element at cursor position using UI Automation
            element_control = auto.ControlFromPoint(cursor_pos.x(), cursor_pos.y())

            if element_control:
                # Avoid selecting the overlay itself or its children
                if self._is_overlay_or_child(element_control):
                    return

                # Check if this is a different element using safe comparison
                is_same = False
                if self.current_element is not None:
                    try:
                        is_same = self._is_same_element(
                            element_control, self.current_element._control
                        )
                    except Exception:
                        is_same = False

                if not is_same:
                    # Create DesktopElement
                    new_element = DesktopElement(element_control)
                    self.current_element = new_element

                    # Get element bounds
                    bounds = new_element.get_bounding_rect()
                    self.current_rect = QRect(
                        bounds["left"], bounds["top"], bounds["width"], bounds["height"]
                    )

                    # Update element info
                    self._update_element_info(new_element)

                    # Trigger repaint
                    self.update()

        except Exception as e:
            logger.debug(f"Error updating hover element: {e}")

    def _is_overlay_or_child(self, control: auto.Control) -> bool:
        """Check if control is the overlay window or its child"""
        try:
            # Get the window handle of the overlay
            overlay_hwnd = int(self.winId())

            # Walk up the control tree to check if it belongs to overlay
            current = control
            for _ in range(10):  # Max 10 levels
                if hasattr(current, "NativeWindowHandle"):
                    if current.NativeWindowHandle == overlay_hwnd:
                        return True

                parent = current.GetParentControl()
                if not parent or parent == current:
                    break
                current = parent

            return False

        except Exception:
            return False

    def _update_element_info(self, element: DesktopElement):
        """Update the element info label"""
        try:
            control_type = element.get_property("ControlTypeName") or "Unknown"
            if control_type.endswith("Control"):
                control_type = control_type[:-7]

            name = element.get_property("Name") or "<no name>"
            automation_id = element.get_property("AutomationId") or "<no id>"
            class_name = element.get_property("ClassName") or "<no class>"

            info_text = f"{control_type}\n"
            info_text += f"Name: {name}\n"
            info_text += f"AutomationId: {automation_id}\n"
            info_text += f"Class: {class_name}"

            self.element_info_label.setText(info_text)
            self.element_info_label.adjustSize()

            # Position near cursor but avoid edges
            cursor_pos = QCursor.pos()
            label_x = cursor_pos.x() + 15
            label_y = cursor_pos.y() + 15

            screen_geometry = QApplication.primaryScreen().geometry()

            # Adjust if too close to right edge
            if label_x + self.element_info_label.width() > screen_geometry.width():
                label_x = cursor_pos.x() - self.element_info_label.width() - 15

            # Adjust if too close to bottom edge
            if label_y + self.element_info_label.height() > screen_geometry.height():
                label_y = cursor_pos.y() - self.element_info_label.height() - 15

            self.element_info_label.move(label_x, label_y)
            self.element_info_label.show()

        except Exception as e:
            logger.warning(f"Failed to update element info: {e}")

    def paintEvent(self, event):
        """Paint the highlight overlay"""
        painter = QPainter(self)

        # Draw highlight rectangle if we have an element
        if self.current_rect:
            # Semi-transparent fill
            painter.fillRect(self.current_rect, QColor(255, 0, 0, 30))

            # Red border
            pen = QPen(QColor(255, 0, 0), 3)
            painter.setPen(pen)
            painter.drawRect(self.current_rect)

    def mousePressEvent(self, event):
        """Handle mouse click - select element"""
        if event.button() == Qt.LeftButton:
            if self.current_element:
                logger.info(f"Element selected: {self.current_element}")
                self.element_selected.emit(self.current_element)
                self.close()
        elif event.button() == Qt.RightButton:
            # Right click to cancel
            logger.info("Element picking cancelled (right click)")
            self.cancelled.emit()
            self.close()

    def keyPressEvent(self, event):
        """Handle key press - ESC to cancel"""
        if event.key() == Qt.Key_Escape:
            logger.info("Element picking cancelled (ESC)")
            self.cancelled.emit()
            self.close()

    def closeEvent(self, event):
        """Cleanup on close"""
        if self.hover_timer:
            self.hover_timer.stop()
        logger.info("Element picker closed")
        super().closeEvent(event)


def activate_element_picker(callback_on_select=None, callback_on_cancel=None):
    """
    Activate element picker overlay.

    Args:
        callback_on_select: Function to call with selected DesktopElement
        callback_on_cancel: Function to call when cancelled

    Returns:
        ElementPickerOverlay instance
    """
    logger.info("Activating element picker")

    picker = ElementPickerOverlay()

    if callback_on_select:
        picker.element_selected.connect(callback_on_select)

    if callback_on_cancel:
        picker.cancelled.connect(callback_on_cancel)

    # Show overlay
    picker.showFullScreen()
    picker.activateWindow()
    picker.raise_()

    return picker
