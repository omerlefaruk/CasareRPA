"""
Debug Toolbar for CasareRPA.

Provides debug controls including:
- Step Over / Step Into / Step Out / Continue buttons
- Slow Step Mode toggle with configurable delay
- Debug mode indicator
- Current execution state display
"""

from typing import TYPE_CHECKING, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QToolBar,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.debugger.debug_controller import (
        DebugController,
    )


class DebugToolbar(QToolBar):
    """
    Debug toolbar with execution controls and slow step mode.

    Features:
    - Step controls (Over, Into, Out, Continue)
    - Slow step mode toggle and delay slider
    - Execution state indicator
    - Run From Here action

    Signals:
        step_over_clicked: Step over requested
        step_into_clicked: Step into requested
        step_out_clicked: Step out requested
        continue_clicked: Continue execution requested
        slow_step_toggled: Slow step mode toggled (enabled, delay_ms)
        run_from_here_requested: Run from selected node requested
    """

    step_over_clicked = Signal()
    step_into_clicked = Signal()
    step_out_clicked = Signal()
    continue_clicked = Signal()
    slow_step_toggled = Signal(bool, int)  # enabled, delay_ms
    run_from_here_requested = Signal()

    # Default slow step settings
    DEFAULT_DELAY_MS = 1000
    MIN_DELAY_MS = 100
    MAX_DELAY_MS = 5000
    DELAY_STEP_MS = 100

    def __init__(
        self,
        parent: QWidget | None = None,
        debug_controller: Optional["DebugController"] = None,
    ) -> None:
        """
        Initialize the debug toolbar.

        Args:
            parent: Optional parent widget
            debug_controller: Optional debug controller for integration
        """
        super().__init__("Debug", parent)
        self.setObjectName("DebugToolbar")
        self._debug_controller = debug_controller

        self._slow_step_enabled = False
        self._slow_step_delay_ms = self.DEFAULT_DELAY_MS

        self._setup_toolbar()
        self._apply_styles()
        self._update_controls_state(debug_paused=False)

        logger.debug("DebugToolbar initialized")

    def set_debug_controller(self, controller: "DebugController") -> None:
        """
        Set the debug controller for integration.

        Args:
            controller: Debug controller instance
        """
        self._debug_controller = controller
        self._connect_controller_signals()

    def _connect_controller_signals(self) -> None:
        """Connect to debug controller signals."""
        if not self._debug_controller:
            return

        self._debug_controller.execution_paused.connect(
            lambda: self._update_controls_state(debug_paused=True)
        )
        self._debug_controller.execution_resumed.connect(
            lambda: self._update_controls_state(debug_paused=False)
        )
        self._debug_controller.debug_mode_changed.connect(self._on_debug_mode_changed)

    def _setup_toolbar(self) -> None:
        """Set up the toolbar layout and widgets."""
        self.setMovable(False)
        self.setIconSize(TOKENS.sizes.toolbar_icon_size, TOKENS.sizes.toolbar_icon_size)

        # Step Over action
        self._action_step_over = QAction("Step Over", self)
        self._action_step_over.setToolTip("Step Over (F10) - Execute current node")
        self._action_step_over.setShortcut("F10")
        self._action_step_over.triggered.connect(self._on_step_over)
        self.addAction(self._action_step_over)

        # Step Into action
        self._action_step_into = QAction("Step Into", self)
        self._action_step_into.setToolTip("Step Into (F11) - Step into nested")
        self._action_step_into.setShortcut("F11")
        self._action_step_into.triggered.connect(self._on_step_into)
        self.addAction(self._action_step_into)

        # Step Out action
        self._action_step_out = QAction("Step Out", self)
        self._action_step_out.setToolTip("Step Out (Shift+F11) - Exit current scope")
        self._action_step_out.setShortcut("Shift+F11")
        self._action_step_out.triggered.connect(self._on_step_out)
        self.addAction(self._action_step_out)

        # Continue action
        self._action_continue = QAction("Continue", self)
        self._action_continue.setToolTip("Continue (F5) - Run to next breakpoint")
        self._action_continue.setShortcut("F5")
        self._action_continue.triggered.connect(self._on_continue)
        self.addAction(self._action_continue)

        self.addSeparator()

        # Run From Here action
        self._action_run_from_here = QAction("Run From Here", self)
        self._action_run_from_here.setToolTip("Start execution from selected node (Ctrl+Shift+F5)")
        self._action_run_from_here.setShortcut("Ctrl+Shift+F5")
        self._action_run_from_here.triggered.connect(self._on_run_from_here)
        self.addAction(self._action_run_from_here)

        self.addSeparator()

        # Slow Step Mode controls
        slow_step_widget = self._create_slow_step_widget()
        self.addWidget(slow_step_widget)

        self.addSeparator()

        # Status indicator
        self._status_label = QLabel("Ready")
        self._status_label.setObjectName("DebugStatusLabel")
        self.addWidget(self._status_label)

    def _create_slow_step_widget(self) -> QWidget:
        """
        Create the slow step mode control widget.

        Returns:
            Widget containing slow step controls
        """
        container = QFrame()
        container.setObjectName("SlowStepContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(TOKENS.spacing.sm, 0, TOKENS.spacing.sm, 0)
        layout.setSpacing(TOKENS.spacing.md)

        # Checkbox to enable slow step
        self._slow_step_checkbox = QCheckBox("Slow Step")
        self._slow_step_checkbox.setToolTip("Enable slow step mode - pause between each node")
        self._slow_step_checkbox.toggled.connect(self._on_slow_step_toggled)
        layout.addWidget(self._slow_step_checkbox)

        # Speed indicator icon
        self._speed_label = QLabel()
        self._speed_label.setObjectName("SpeedIndicator")
        self._update_speed_indicator()
        layout.addWidget(self._speed_label)

        # Delay slider
        self._delay_slider = QSlider(Qt.Orientation.Horizontal)
        self._delay_slider.setMinimum(self.MIN_DELAY_MS // self.DELAY_STEP_MS)
        self._delay_slider.setMaximum(self.MAX_DELAY_MS // self.DELAY_STEP_MS)
        self._delay_slider.setValue(self.DEFAULT_DELAY_MS // self.DELAY_STEP_MS)
        self._delay_slider.setFixedWidth(TOKENS.sizes.input_max_width // 4)
        self._delay_slider.setToolTip("Adjust delay between nodes")
        self._delay_slider.valueChanged.connect(self._on_delay_changed)
        self._delay_slider.setEnabled(False)  # Disabled until slow step enabled
        layout.addWidget(self._delay_slider)

        # Delay display
        self._delay_spinbox = QSpinBox()
        self._delay_spinbox.setMinimum(self.MIN_DELAY_MS)
        self._delay_spinbox.setMaximum(self.MAX_DELAY_MS)
        self._delay_spinbox.setValue(self.DEFAULT_DELAY_MS)
        self._delay_spinbox.setSingleStep(self.DELAY_STEP_MS)
        self._delay_spinbox.setSuffix(" ms")
        self._delay_spinbox.setFixedWidth(TOKENS.sizes.input_min_width // 1.5)
        self._delay_spinbox.setToolTip("Delay in milliseconds")
        self._delay_spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._delay_spinbox.setEnabled(False)
        layout.addWidget(self._delay_spinbox)

        return container

    def _apply_styles(self) -> None:
        """Apply VSCode-style dark theme."""
        self.setStyleSheet(f"""
            QToolBar {{
                background-color: {THEME.bg_header};
                border: none;
                border-bottom: 1px solid {THEME.border_dark};
                spacing: {TOKENS.spacing.toolbar_spacing}px;
                padding: {TOKENS.spacing.sm}px;
            }}
            QToolBar QToolButton {{
                background-color: transparent;
                color: {THEME.text_primary};
                border: 1px solid transparent;
                border-radius: {TOKENS.radii.button}px;
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                font-size: {TOKENS.fonts.sm}px;
            }}
            QToolBar QToolButton:hover {{
                background-color: {THEME.bg_hover};
                border-color: {THEME.border};
            }}
            QToolBar QToolButton:pressed {{
                background-color: {THEME.bg_lighter};
            }}
            QToolBar QToolButton:disabled {{
                color: {THEME.text_disabled};
            }}
            QFrame#SlowStepContainer {{
                background-color: transparent;
                border: none;
            }}
            QCheckBox {{
                color: {THEME.text_primary};
                spacing: {TOKENS.spacing.sm}px;
            }}
            QCheckBox::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.sm}px;
                background-color: {THEME.bg_light};
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {THEME.accent_primary};
            }}
            QSlider::groove:horizontal {{
                background: {THEME.bg_light};
                height: {TOKENS.sizes.slider_height // 2}px;
                border-radius: {TOKENS.radii.sm // 2}px;
            }}
            QSlider::handle:horizontal {{
                background: {THEME.accent_primary};
                width: {TOKENS.sizes.slider_handle_size}px;
                margin: -4px 0;
                border-radius: {TOKENS.sizes.slider_handle_size // 2}px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {THEME.accent_secondary};
            }}
            QSlider::handle:horizontal:disabled {{
                background: {THEME.text_disabled};
            }}
            QSpinBox {{
                background-color: {THEME.bg_light};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radii.input}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
            }}
            QSpinBox:disabled {{
                color: {THEME.text_disabled};
                background-color: {THEME.bg_medium};
            }}
            QLabel#DebugStatusLabel {{
                color: {THEME.text_secondary};
                font-style: italic;
                padding: 0 {TOKENS.spacing.md}px;
            }}
            QLabel#SpeedIndicator {{
                font-size: {TOKENS.fonts.lg}px;
                padding: 0 {TOKENS.spacing.sm}px;
            }}
        """)

    def _update_controls_state(self, debug_paused: bool) -> None:
        """
        Update control states based on debug mode.

        Args:
            debug_paused: Whether execution is paused at breakpoint
        """
        # Step controls only enabled when paused at breakpoint
        self._action_step_over.setEnabled(debug_paused)
        self._action_step_into.setEnabled(debug_paused)
        self._action_step_out.setEnabled(debug_paused)
        self._action_continue.setEnabled(debug_paused)

        if debug_paused:
            self._status_label.setText("Paused")
            self._status_label.setStyleSheet(f"color: {THEME.warning};")
        else:
            self._status_label.setText("Ready")
            self._status_label.setStyleSheet(f"color: {THEME.text_secondary};")

    def _update_speed_indicator(self) -> None:
        """Update the speed indicator based on delay."""
        if not self._slow_step_enabled:
            self._speed_label.setText("")
        elif self._slow_step_delay_ms < 500:
            self._speed_label.setText("[Fast]")
        elif self._slow_step_delay_ms < 2000:
            self._speed_label.setText("[Normal]")
        else:
            self._speed_label.setText("[Slow]")

    def _on_step_over(self) -> None:
        """Handle step over action."""
        if self._debug_controller:
            self._debug_controller.step_over()
        self.step_over_clicked.emit()
        logger.debug("Step over requested")

    def _on_step_into(self) -> None:
        """Handle step into action."""
        if self._debug_controller:
            self._debug_controller.step_into()
        self.step_into_clicked.emit()
        logger.debug("Step into requested")

    def _on_step_out(self) -> None:
        """Handle step out action."""
        if self._debug_controller:
            self._debug_controller.step_out()
        self.step_out_clicked.emit()
        logger.debug("Step out requested")

    def _on_continue(self) -> None:
        """Handle continue action."""
        if self._debug_controller:
            self._debug_controller.continue_execution()
        self.continue_clicked.emit()
        logger.debug("Continue requested")

    def _on_run_from_here(self) -> None:
        """Handle run from here action."""
        self.run_from_here_requested.emit()
        logger.debug("Run from here requested")

    def _on_slow_step_toggled(self, checked: bool) -> None:
        """
        Handle slow step checkbox toggled.

        Args:
            checked: Whether slow step is enabled
        """
        self._slow_step_enabled = checked
        self._delay_slider.setEnabled(checked)
        self._delay_spinbox.setEnabled(checked)
        self._update_speed_indicator()

        self.slow_step_toggled.emit(checked, self._slow_step_delay_ms)
        logger.debug(f"Slow step {'enabled' if checked else 'disabled'}")

    def _on_delay_changed(self, value: int) -> None:
        """
        Handle delay slider value changed.

        Args:
            value: Slider value (scaled)
        """
        self._slow_step_delay_ms = value * self.DELAY_STEP_MS

        # Update spinbox without triggering its signal
        self._delay_spinbox.blockSignals(True)
        self._delay_spinbox.setValue(self._slow_step_delay_ms)
        self._delay_spinbox.blockSignals(False)

        self._update_speed_indicator()

        if self._slow_step_enabled:
            self.slow_step_toggled.emit(True, self._slow_step_delay_ms)

    def _on_spinbox_changed(self, value: int) -> None:
        """
        Handle delay spinbox value changed.

        Args:
            value: Delay in milliseconds
        """
        self._slow_step_delay_ms = value

        # Update slider without triggering its signal
        self._delay_slider.blockSignals(True)
        self._delay_slider.setValue(value // self.DELAY_STEP_MS)
        self._delay_slider.blockSignals(False)

        self._update_speed_indicator()

        if self._slow_step_enabled:
            self.slow_step_toggled.emit(True, self._slow_step_delay_ms)

    def _on_debug_mode_changed(self, enabled: bool) -> None:
        """
        Handle debug mode changed.

        Args:
            enabled: Whether debug mode is enabled
        """
        self.setVisible(enabled)

    # Public API

    def is_slow_step_enabled(self) -> bool:
        """Check if slow step mode is enabled."""
        return self._slow_step_enabled

    def get_slow_step_delay_ms(self) -> int:
        """Get current slow step delay in milliseconds."""
        return self._slow_step_delay_ms

    def set_slow_step_enabled(self, enabled: bool) -> None:
        """
        Set slow step mode.

        Args:
            enabled: Whether to enable slow step mode
        """
        self._slow_step_checkbox.setChecked(enabled)

    def set_slow_step_delay(self, delay_ms: int) -> None:
        """
        Set slow step delay.

        Args:
            delay_ms: Delay in milliseconds
        """
        delay_ms = max(self.MIN_DELAY_MS, min(self.MAX_DELAY_MS, delay_ms))
        self._delay_spinbox.setValue(delay_ms)

    def set_status(self, text: str, is_warning: bool = False) -> None:
        """
        Set status label text.

        Args:
            text: Status text
            is_warning: Whether to show as warning color
        """
        self._status_label.setText(text)
        color = THEME.warning if is_warning else THEME.text_secondary
        self._status_label.setStyleSheet(f"color: {color};")
