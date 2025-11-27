"""
Zoom Toolbar UI Component.

Provides zoom and view controls for the workflow canvas.
"""

from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QWidget, QSlider, QLabel
from PySide6.QtCore import Qt

from loguru import logger


class ZoomToolbar(QToolBar):
    """
    Toolbar for zoom and view controls.

    Features:
    - Zoom in/out
    - Zoom to fit
    - Reset zoom (100%)
    - Zoom slider
    - Current zoom display

    Signals:
        zoom_in_requested: Emitted when user requests zoom in
        zoom_out_requested: Emitted when user requests zoom out
        zoom_fit_requested: Emitted when user requests zoom to fit
        zoom_reset_requested: Emitted when user requests reset zoom
        zoom_changed: Emitted when zoom level changes (float: zoom_level)
    """

    zoom_in_requested = Signal()
    zoom_out_requested = Signal()
    zoom_fit_requested = Signal()
    zoom_reset_requested = Signal()
    zoom_changed = Signal(float)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the zoom toolbar.

        Args:
            parent: Optional parent widget
        """
        super().__init__("Zoom", parent)

        self.setObjectName("ZoomToolbar")
        self.setMovable(False)
        self.setFloatable(False)

        self._current_zoom = 1.0
        self._min_zoom = 0.1
        self._max_zoom = 3.0

        self._create_actions()
        self._create_widgets()
        self._apply_styles()

        logger.debug("ZoomToolbar initialized")

    def _create_actions(self) -> None:
        """Create toolbar actions."""
        # Zoom out
        self.action_zoom_out = QAction("-", self)
        self.action_zoom_out.setToolTip("Zoom out (Ctrl+-)")
        self.action_zoom_out.setShortcut("Ctrl+-")
        self.action_zoom_out.triggered.connect(self._on_zoom_out)
        self.addAction(self.action_zoom_out)

        # Zoom in
        self.action_zoom_in = QAction("+", self)
        self.action_zoom_in.setToolTip("Zoom in (Ctrl++)")
        self.action_zoom_in.setShortcut("Ctrl++")
        self.action_zoom_in.triggered.connect(self._on_zoom_in)
        self.addAction(self.action_zoom_in)

        self.addSeparator()

        # Zoom to fit
        self.action_zoom_fit = QAction("Fit", self)
        self.action_zoom_fit.setToolTip("Zoom to fit all nodes (Ctrl+0)")
        self.action_zoom_fit.setShortcut("Ctrl+0")
        self.action_zoom_fit.triggered.connect(self._on_zoom_fit)
        self.addAction(self.action_zoom_fit)

        # Reset zoom
        self.action_zoom_reset = QAction("100%", self)
        self.action_zoom_reset.setToolTip("Reset zoom to 100% (Ctrl+1)")
        self.action_zoom_reset.setShortcut("Ctrl+1")
        self.action_zoom_reset.triggered.connect(self._on_zoom_reset)
        self.addAction(self.action_zoom_reset)

    def _create_widgets(self) -> None:
        """Create toolbar widgets."""
        self.addSeparator()

        # Zoom slider
        self._zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self._zoom_slider.setMinimum(int(self._min_zoom * 100))
        self._zoom_slider.setMaximum(int(self._max_zoom * 100))
        self._zoom_slider.setValue(int(self._current_zoom * 100))
        self._zoom_slider.setFixedWidth(120)
        self._zoom_slider.setToolTip("Zoom level")
        self._zoom_slider.valueChanged.connect(self._on_slider_changed)
        self.addWidget(self._zoom_slider)

        # Zoom label
        self._zoom_label = QLabel("100%")
        self._zoom_label.setMinimumWidth(45)
        self._zoom_label.setStyleSheet("color: #e0e0e0; padding: 0 4px;")
        self.addWidget(self._zoom_label)

    def _apply_styles(self) -> None:
        """Apply toolbar styling."""
        self.setStyleSheet("""
            QToolBar {
                background: #2d2d2d;
                border-top: 1px solid #3d3d3d;
                spacing: 3px;
                padding: 2px 4px;
            }
            QToolBar::separator {
                background: #4a4a4a;
                width: 1px;
                margin: 4px 2px;
            }
            QToolButton {
                background: transparent;
                color: #e0e0e0;
                border: none;
                border-radius: 2px;
                padding: 4px 8px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #3d3d3d;
            }
            QToolButton:pressed {
                background: #252525;
            }
            QSlider::groove:horizontal {
                background: #3d3d3d;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #5a8a9a;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #6a9aaa;
            }
        """)

    def _on_zoom_in(self) -> None:
        """Handle zoom in action."""
        new_zoom = min(self._current_zoom + 0.1, self._max_zoom)
        self.set_zoom(new_zoom)
        self.zoom_in_requested.emit()
        logger.debug(f"Zoom in: {new_zoom:.1%}")

    def _on_zoom_out(self) -> None:
        """Handle zoom out action."""
        new_zoom = max(self._current_zoom - 0.1, self._min_zoom)
        self.set_zoom(new_zoom)
        self.zoom_out_requested.emit()
        logger.debug(f"Zoom out: {new_zoom:.1%}")

    def _on_zoom_fit(self) -> None:
        """Handle zoom to fit action."""
        self.zoom_fit_requested.emit()
        logger.debug("Zoom to fit requested")

    def _on_zoom_reset(self) -> None:
        """Handle reset zoom action."""
        self.set_zoom(1.0)
        self.zoom_reset_requested.emit()
        logger.debug("Zoom reset to 100%")

    def _on_slider_changed(self, value: int) -> None:
        """
        Handle zoom slider change.

        Args:
            value: New slider value (0-300)
        """
        zoom = value / 100.0
        if abs(zoom - self._current_zoom) > 0.01:
            self._current_zoom = zoom
            self._update_zoom_display()
            self.zoom_changed.emit(zoom)

    def set_zoom(self, zoom: float) -> None:
        """
        Set zoom level programmatically.

        Args:
            zoom: Zoom level (0.1 to 3.0)
        """
        zoom = max(self._min_zoom, min(zoom, self._max_zoom))
        self._current_zoom = zoom

        # Update slider without triggering signal
        self._zoom_slider.blockSignals(True)
        self._zoom_slider.setValue(int(zoom * 100))
        self._zoom_slider.blockSignals(False)

        self._update_zoom_display()
        self.zoom_changed.emit(zoom)

    def get_zoom(self) -> float:
        """
        Get current zoom level.

        Returns:
            Current zoom level
        """
        return self._current_zoom

    def _update_zoom_display(self) -> None:
        """Update zoom percentage label."""
        self._zoom_label.setText(f"{int(self._current_zoom * 100)}%")

    def set_zoom_range(self, min_zoom: float, max_zoom: float) -> None:
        """
        Set zoom range limits.

        Args:
            min_zoom: Minimum zoom level
            max_zoom: Maximum zoom level
        """
        self._min_zoom = min_zoom
        self._max_zoom = max_zoom

        self._zoom_slider.setMinimum(int(min_zoom * 100))
        self._zoom_slider.setMaximum(int(max_zoom * 100))

        logger.debug(f"Zoom range set: {min_zoom:.1%} - {max_zoom:.1%}")
