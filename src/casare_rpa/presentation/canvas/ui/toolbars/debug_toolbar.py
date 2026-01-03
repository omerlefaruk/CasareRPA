"""
Debug Toolbar for CasareRPA.

Provides debug controls including:
- Step Over / Step Into / Step Out / Continue buttons
- Slow Step Mode toggle with configurable delay
- Debug mode indicator
- Current execution state display

Epic 7.5: Migrated to THEME_V2/TOKENS_V2 design system.
- Uses THEME_V2/TOKENS_V2 for all styling
- Uses icon_v2 singleton for Lucide SVG icons
- Zero hardcoded colors
- Zero animations/shadows
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

# Epic 7.5: Migrated to v2 design system
from casare_rpa.presentation.canvas.theme import (
    THEME_V2,
    TOKENS_V2,
    get_toolbar_styles_v2,
    icon_v2,
)

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
        self.setIconSize(TOKENS_V2.sizes.icon_md, TOKENS_V2.sizes.icon_md)

        # Step Over action (using chevron-down icon for "step over")
        self._action_step_over = QAction(
            icon_v2.get_icon("chevron-down", size=20), "Step Over", self
        )
        self._action_step_over.setToolTip("Step Over (F10) - Execute current node")
        self._action_step_over.setShortcut("F10")
        self._action_step_over.triggered.connect(self._on_step_over)
        self.addAction(self._action_step_over)

        # Step Into action (using chevron-right icon for "step into")
        self._action_step_into = QAction(
            icon_v2.get_icon("chevron-right", size=20), "Step Into", self
        )
        self._action_step_into.setToolTip("Step Into (F11) - Step into nested")
        self._action_step_into.setShortcut("F11")
        self._action_step_into.triggered.connect(self._on_step_into)
        self.addAction(self._action_step_into)

        # Step Out action (using chevron-up icon for "step out")
        self._action_step_out = QAction(icon_v2.get_icon("chevron-up", size=20), "Step Out", self)
        self._action_step_out.setToolTip("Step Out (Shift+F11) - Exit current scope")
        self._action_step_out.setShortcut("Shift+F11")
        self._action_step_out.triggered.connect(self._on_step_out)
        self.addAction(self._action_step_out)

        # Continue action (using play icon)
        self._action_continue = QAction(icon_v2.get_icon("play", size=20), "Continue", self)
        self._action_continue.setToolTip("Continue (F5) - Run to next breakpoint")
        self._action_continue.setShortcut("F5")
        self._action_continue.triggered.connect(self._on_continue)
        self.addAction(self._action_continue)

        self.addSeparator()

        # Run From Here action (using play icon with accent)
        self._action_run_from_here = QAction(
            icon_v2.get_icon("play", size=20, state="accent"), "Run From Here", self
        )
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
        layout.setContentsMargins(TOKENS_V2.spacing.sm, 0, TOKENS_V2.spacing.sm, 0)
        layout.setSpacing(TOKENS_V2.spacing.md)

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
        self._delay_slider.setFixedWidth(TOKENS_V2.sizes.input_max_width // 4)
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
        self._delay_spinbox.setFixedWidth(TOKENS_V2.sizes.input_min_width // 1.5)
        self._delay_spinbox.setToolTip("Delay in milliseconds")
        self._delay_spinbox.valueChanged.connect(self._on_spinbox_changed)
        self._delay_spinbox.setEnabled(False)
        layout.addWidget(self._delay_spinbox)

        return container

    def _apply_styles(self) -> None:
        """Apply v2 dark theme using THEME_V2/TOKENS_V2 and get_toolbar_styles_v2()."""
        # Use the standardized v2 toolbar styles
        base_toolbar_styles = get_toolbar_styles_v2()

        # Add debug-specific widget styles
        custom_styles = f"""
            /* ==================== DEBUG TOOLBAR CUSTOM ==================== */
            QFrame#SlowStepContainer {{
                background-color: transparent;
                border: none;
            }}
            QCheckBox {{
                color: {THEME_V2.text_primary};
                spacing: {TOKENS_V2.spacing.sm}px;
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
            QCheckBox::indicator {{
                width: {TOKENS_V2.sizes.icon_sm}px;
                height: {TOKENS_V2.sizes.icon_sm}px;
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.xs}px;
                background-color: {THEME_V2.bg_component};
            }}
            QCheckBox::indicator:checked {{
                background-color: {THEME_V2.primary};
                border-color: {THEME_V2.primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {THEME_V2.primary};
            }}
            QSlider::groove:horizontal {{
                background: {THEME_V2.bg_component};
                height: {TOKENS_V2.sizes.border}px;
                border-radius: {TOKENS_V2.radius.xs // 2}px;
            }}
            QSlider::handle:horizontal {{
                background: {THEME_V2.primary};
                width: {TOKENS_V2.sizes.icon_sm}px;
                margin: -4px 0;
                border-radius: {TOKENS_V2.sizes.icon_sm // 2}px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {THEME_V2.primary};
            }}
            QSlider::handle:horizontal:disabled {{
                background: {THEME_V2.text_disabled};
            }}
            QSpinBox {{
                background-color: {THEME_V2.bg_component};
                color: {THEME_V2.text_primary};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS_V2.radius.sm}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.sm}px;
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
            QSpinBox:disabled {{
                color: {THEME_V2.text_disabled};
                background-color: {THEME_V2.bg_component};
            }}
            QLabel#DebugStatusLabel {{
                color: {THEME_V2.text_secondary};
                font-style: italic;
                padding: 0 {TOKENS_V2.spacing.sm}px;
                font-size: {TOKENS_V2.typography.body_sm}px;
            }}
            QLabel#SpeedIndicator {{
                font-size: {TOKENS_V2.typography.body_sm}px;
                padding: 0 {TOKENS_V2.spacing.xs}px;
                color: {THEME_V2.text_secondary};
            }}
        """
        self.setStyleSheet(base_toolbar_styles + custom_styles)

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
            self._status_label.setStyleSheet(f"color: {THEME_V2.warning};")
        else:
            self._status_label.setText("Ready")
            self._status_label.setStyleSheet(f"color: {THEME_V2.text_secondary};")

    def _update_speed_indicator(self) -> None:
        """Update the speed indicator based on delay."""
        if not self._slow_step_enabled:
            self._speed_label.setText("")
        elif self._slow_step_delay_ms < TOKENS_V2.sizes.dialog_md_width:
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
        color = THEME_V2.warning if is_warning else THEME_V2.text_secondary
        self._status_label.setStyleSheet(f"color: {color};")

