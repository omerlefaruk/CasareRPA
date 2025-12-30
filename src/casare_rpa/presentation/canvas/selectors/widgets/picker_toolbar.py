"""
Floating Picker Toolbar for Element Selector Dialog.

Appears during element picking as a floating overlay.
Provides quick actions: Stop, Mode switch, Cancel.
"""

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.state.selector_state import PickingMode
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_height,
    set_fixed_size,
    set_margins,
    set_min_width,
)


class PickerToolbar(QWidget):
    """
    Floating toolbar shown during element picking.

    Layout:
    +-----------------------------------------------------------+
    | Picking element...    [Browser][Desktop]  [Cancel][Stop]  |
    +-----------------------------------------------------------+

    This is a frameless, always-on-top widget that follows the cursor
    or stays at top of screen during picking mode.

    Signals:
        stop_requested: User clicked Stop
        cancel_requested: User clicked Cancel
        mode_changed: User switched mode during picking
    """

    stop_requested = Signal()
    cancel_requested = Signal()
    mode_changed = Signal(PickingMode)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_mode = PickingMode.AUTO
        self._setup_ui()
        self._setup_window_flags()

    def _setup_window_flags(self) -> None:
        """Configure as floating toolbar."""
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def _setup_ui(self) -> None:
        """Build toolbar UI."""
        set_fixed_height(self, 48)
        set_min_width(self, TOKENS.sizes.dialog_sm_width)

        # Main container with styling
        container = QWidget(self)
        container.setStyleSheet(f"""
            QWidget {{
                background: rgba(30, 30, 30, 0.95);
                border: 2px solid {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border-radius: {TOKENS.radius.md}px;
            }}
        """)

        container_layout = QHBoxLayout(self)
        set_margins(container_layout, (0, 0, 0, 0))
        container_layout.addWidget(container)

        layout = QHBoxLayout(container)
        layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm
        )
        layout.setSpacing(TOKENS.spacing.md)

        # Status indicator (pulsing)
        self._status_dot = QLabel()
        set_fixed_size(self._status_dot, 12, 12)
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border-radius: {TOKENS.sizes.icon_sm}px;
            }}
        """)
        layout.addWidget(self._status_dot)

        # Status text
        self._status_label = QLabel("Click any element to select it...")
        self._status_label.setStyleSheet(
            f"color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px;"
        )
        layout.addWidget(self._status_label)

        layout.addStretch()

        # Mode buttons (compact)
        self._browser_btn = QPushButton("Web")
        set_fixed_size(self._browser_btn, 48, 28)
        self._browser_btn.setCheckable(True)
        self._browser_btn.clicked.connect(self._on_browser_mode_clicked)
        self._browser_btn.setStyleSheet(self._mode_btn_style(False))
        layout.addWidget(self._browser_btn)

        self._desktop_btn = QPushButton("Win")
        set_fixed_size(self._desktop_btn, 48, 28)
        self._desktop_btn.setCheckable(True)
        self._desktop_btn.clicked.connect(self._on_desktop_mode_clicked)
        self._desktop_btn.setStyleSheet(self._mode_btn_style(False))
        layout.addWidget(self._desktop_btn)

        layout.addSpacing(TOKENS.spacing.md)

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        set_fixed_size(self._cancel_btn, 60, 28)
        self._cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._cancel_btn.clicked.connect(self.cancel_requested.emit)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
        """)
        layout.addWidget(self._cancel_btn)

        # Stop button (primary action)
        self._stop_btn = QPushButton("Stop")
        set_fixed_size(self._stop_btn, 60, 28)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.clicked.connect(self.stop_requested.emit)
        self._stop_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border: 1px solid {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                font-weight: bold;
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
            }}
        """)
        layout.addWidget(self._stop_btn)

    @Slot()
    def _on_browser_mode_clicked(self) -> None:
        """Handle browser mode button click."""
        self._set_mode(PickingMode.BROWSER)

    @Slot()
    def _on_desktop_mode_clicked(self) -> None:
        """Handle desktop mode button click."""
        self._set_mode(PickingMode.DESKTOP)

    def _mode_btn_style(self, checked: bool) -> str:
        """Get style for mode button."""
        if checked:
            return f"""
                QPushButton {{
                    background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                    border: 1px solid {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                    border-radius: {TOKENS.radius.sm}px;
                    color: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                    font-size: {TOKENS.typography.caption}px;
                    font-weight: bold;
                }}
            """
        return f"""
            QPushButton {{
                background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME.text_muted};
                font-size: {TOKENS.typography.caption}px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                color: {THEME.text_primary};
            }}
        """

    def _set_mode(self, mode: PickingMode) -> None:
        """Set current mode."""
        self._current_mode = mode
        self._browser_btn.setChecked(mode == PickingMode.BROWSER)
        self._desktop_btn.setChecked(mode == PickingMode.DESKTOP)
        self._browser_btn.setStyleSheet(self._mode_btn_style(mode == PickingMode.BROWSER))
        self._desktop_btn.setStyleSheet(self._mode_btn_style(mode == PickingMode.DESKTOP))
        self.mode_changed.emit(mode)

    def set_mode(self, mode: PickingMode) -> None:
        """Set current mode (external)."""
        self._set_mode(mode)

    def set_status(self, message: str) -> None:
        """Update status text."""
        self._status_label.setText(message)

    def set_status_color(self, color: str) -> None:
        """Update status dot color."""
        self._status_dot.setStyleSheet(f"""
            QLabel {{
                background: {color};
                border-radius: {TOKENS.sizes.icon_sm}px;
            }}
        """)

    def show_at_top(self, parent_geometry=None) -> None:
        """
        Show toolbar at top center of parent or screen.

        Args:
            parent_geometry: Optional parent geometry to position within
        """
        self.show()

        if parent_geometry:
            # Center horizontally in parent
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + 20
        else:
            # Center horizontally on screen
            from PySide6.QtWidgets import QApplication

            screen = QApplication.primaryScreen()
            if screen:
                geo = screen.geometry()
                x = (geo.width() - self.width()) // 2
                y = 50
            else:
                x, y = 100, 50

        self.move(x, y)

    def show_near_cursor(self, offset_x: int = 20, offset_y: int = 20) -> None:
        """
        Show toolbar near cursor position.

        Args:
            offset_x: Horizontal offset from cursor
            offset_y: Vertical offset from cursor
        """
        from PySide6.QtGui import QCursor

        cursor_pos = QCursor.pos()
        self.show()
        self.move(cursor_pos.x() + offset_x, cursor_pos.y() + offset_y)


__all__ = ["PickerToolbar"]
