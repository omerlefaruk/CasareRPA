"""
Zoom display widget for status bar.

Provides:
- Current zoom percentage display
- Preset menu (25%, 50%, 75%, 100%, 150%, TOKENS.sizes.panel_width_min%, TOKENS.sizes.dialog_width_sm%)
- Fit to Window and Fit Selection options
- Zoom in/out buttons
- Mouse wheel zooming on widget
"""

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_size,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

if TYPE_CHECKING:
    from NodeGraphQt import NodeGraph


class ZoomWidget(QWidget):
    """
    Zoom display widget with presets and controls.

    Features:
    - Click label to show preset menu
    - Zoom in/out buttons (+/-)
    - Mouse wheel to zoom
    - Syncs with graph view zoom changes

    Signals:
        zoom_changed: Emitted when zoom level should change (zoom_factor)
        fit_to_window: Emitted when "Fit to Window" selected
        fit_to_selection: Emitted when "Fit Selection" selected
        reset_zoom: Emitted when "Reset to 100%" selected
    """

    zoom_changed = Signal(float)
    fit_to_window = Signal()
    fit_to_selection = Signal()
    reset_zoom = Signal()

    ZOOM_PRESETS = [25, 50, 75, 100, 150, TOKENS.sizes.panel_width_min, TOKENS.sizes.dialog_width_sm]
    ZOOM_STEP = 0.1

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize zoom widget.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._current_zoom: float = 1.0
        self._graph: NodeGraph | None = None

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Create the widget layout with label and buttons."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(*TOKENS.margins.none)
        set_spacing(layout, TOKENS.spacing.xs)

        # Zoom out button
        self._btn_zoom_out = QPushButton("-")
        set_fixed_size(self._btn_zoom_out, TOKENS.sizes.icon_lg, TOKENS.sizes.icon_lg)
        self._btn_zoom_out.setToolTip("Zoom out (Ctrl+-)")
        self._btn_zoom_out.clicked.connect(self._on_zoom_out)
        layout.addWidget(self._btn_zoom_out)

        # Zoom label (clickable for preset menu)
        self._zoom_label = QPushButton("100%")
        self._zoom_label.setToolTip("Click for zoom presets")
        self._zoom_label.setFlat(True)
        self.set_min_width(_zoom_label, 50)
        self._zoom_label.clicked.connect(self._show_preset_menu)
        layout.addWidget(self._zoom_label)

        # Zoom in button
        self._btn_zoom_in = QPushButton("+")
        set_fixed_size(self._btn_zoom_in, TOKENS.sizes.icon_lg, TOKENS.sizes.icon_lg)
        self._btn_zoom_in.setToolTip("Zoom in (Ctrl++)")
        self._btn_zoom_in.clicked.connect(self._on_zoom_in)
        layout.addWidget(self._btn_zoom_in)

        self.setLayout(layout)
        self.setFixedHeight(TOKENS.sizes.button_height_sm)

    def _apply_style(self) -> None:
        """Apply theme-aware styling."""
        self.setStyleSheet(f"""
            ZoomWidget {{
                background: transparent;
            }}
            QPushButton {{
                background: transparent;
                border: 1px solid transparent;
                border-radius: {TOKENS.radii.sm}px;
                color: {THEME.text_secondary};
                font-size: {TOKENS.fonts.sm}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                color: {THEME.text_primary};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_selected};
            }}
        """)

    def set_graph(self, graph: "NodeGraph") -> None:
        """
        Connect to a NodeGraph instance for zoom sync.

        Args:
            graph: NodeGraph to sync with
        """
        self._graph = graph

        # Connect to graph zoom changes if signal exists
        if hasattr(graph, "viewer") and graph.viewer():
            viewer = graph.viewer()
            # Listen for view transform changes
            if hasattr(viewer, "rubberBandChanged"):
                pass  # NodeGraphQt doesn't emit zoom signals directly

    def set_zoom(self, zoom_factor: float) -> None:
        """
        Update the displayed zoom level.

        Args:
            zoom_factor: Current zoom factor (1.0 = 100%)
        """
        self._current_zoom = max(0.1, min(10.0, zoom_factor))
        percent = int(self._current_zoom * 100)
        self._zoom_label.setText(f"{percent}%")

    def get_zoom(self) -> float:
        """Get current zoom factor."""
        return self._current_zoom

    def _on_zoom_in(self) -> None:
        """Handle zoom in button click."""
        new_zoom = min(10.0, self._current_zoom + self.ZOOM_STEP)
        self._apply_zoom(new_zoom)

    def _on_zoom_out(self) -> None:
        """Handle zoom out button click."""
        new_zoom = max(0.1, self._current_zoom - self.ZOOM_STEP)
        self._apply_zoom(new_zoom)

    def _apply_zoom(self, zoom_factor: float) -> None:
        """Apply zoom change to graph and emit signal."""
        self.set_zoom(zoom_factor)

        if self._graph:
            try:
                self._graph.set_zoom(zoom_factor)
            except Exception as e:
                logger.debug(f"Could not set graph zoom: {e}")

        self.zoom_changed.emit(zoom_factor)

    def _show_preset_menu(self) -> None:
        """Show the zoom preset menu."""
        menu = self._create_preset_menu()
        pos = self._zoom_label.mapToGlobal(self._zoom_label.rect().bottomLeft())
        menu.exec(pos)

    def _create_preset_menu(self) -> QMenu:
        """
        Create the zoom preset dropdown menu.

        Returns:
            QMenu with preset options
        """
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {THEME.bg_panel};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.sm}px;
                padding: {TOKENS.spacing.xs}px 0;
            }}
            QMenu::item {{
                padding: {TOKENS.spacing.sm}px 24px;
                color: {THEME.text_primary};
            }}
            QMenu::item:selected {{
                background: {THEME.bg_selected};
            }}
            QMenu::separator {{
                height: 1px;
                background: {THEME.border};
                margin: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
            }}
        """)

        # Preset percentages
        for preset in self.ZOOM_PRESETS:
            action = menu.addAction(f"{preset}%")
            zoom_factor = preset / 100.0
            action.triggered.connect(lambda checked, z=zoom_factor: self._apply_zoom(z))

            # Mark current zoom
            if abs(self._current_zoom - zoom_factor) < 0.01:
                action.setCheckable(True)
                action.setChecked(True)

        menu.addSeparator()

        # Fit options
        action_fit_window = menu.addAction("Fit to Window")
        action_fit_window.setShortcut("Ctrl+1")
        action_fit_window.triggered.connect(self._on_fit_to_window)

        action_fit_selection = menu.addAction("Fit Selection")
        action_fit_selection.triggered.connect(self._on_fit_to_selection)

        menu.addSeparator()

        # Reset to 100%
        action_reset = menu.addAction("Reset to 100%")
        action_reset.setShortcut("Ctrl+0")
        action_reset.triggered.connect(self._on_reset_zoom)

        return menu

    def _on_fit_to_window(self) -> None:
        """Handle Fit to Window action."""
        if self._graph:
            try:
                nodes = self._graph.all_nodes()
                if nodes:
                    self._graph.fit_to_selection()
                    # Update display after fit
                    zoom = self._graph.get_zoom()
                    self.set_zoom(zoom)
            except Exception as e:
                logger.debug(f"Could not fit to window: {e}")

        self.fit_to_window.emit()

    def _on_fit_to_selection(self) -> None:
        """Handle Fit Selection action."""
        if self._graph:
            try:
                selected = self._graph.selected_nodes()
                if selected:
                    self._graph.fit_to_selection()
                    zoom = self._graph.get_zoom()
                    self.set_zoom(zoom)
            except Exception as e:
                logger.debug(f"Could not fit to selection: {e}")

        self.fit_to_selection.emit()

    def _on_reset_zoom(self) -> None:
        """Handle Reset to 100% action."""
        self._apply_zoom(1.0)
        self.reset_zoom.emit()

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel for zooming."""
        delta = event.angleDelta().y()
        if delta > 0:
            self._on_zoom_in()
        elif delta < 0:
            self._on_zoom_out()
        event.accept()
