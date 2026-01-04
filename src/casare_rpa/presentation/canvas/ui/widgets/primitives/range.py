"""
Range Input Components v2 - Epic 5.1 Component Library.

Themed range input components using THEME_V2 and TOKENS_V2 for consistent styling.
Provides Slider, ProgressBar, and Dial for numerical value display and input.

Components:
    Slider: Horizontal slider with value label option
    ProgressBar: Progress indicator with indeterminate mode
    Dial: Rotary dial widget for angular value input

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.range import (
        Slider,
        ProgressBar,
        Dial,
    )

    # Slider with value display
    slider = Slider(min=0, max=100, value=50, show_value=True)
    slider.value_changed.connect(lambda v: print(f"Value: {v}"))

    # Progress bar
    progress = ProgressBar(value=75, min=0, max=100)
    progress.set_value(90)  # Update progress

    # Indeterminate progress (loading state)
    loading = ProgressBar(indeterminate=True)

    # Dial for angular input
    dial = Dial(min=0, max=360, value=180, wrapping=True)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Literal

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QDial,
    QProgressBar,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import BasePrimitive

if TYPE_CHECKING:
    pass


# =============================================================================
# TYPE ALIASES
# =============================================================================

SliderSize = Literal["sm", "md", "lg"]
ProgressBarSize = Literal["sm", "md", "lg"]


# =============================================================================
# SLIDER
# =============================================================================


class Slider(BasePrimitive):
    """
    Themed horizontal slider with optional value label.

    Wraps QSlider with v2 dark theme styling. Shows current value
    alongside the slider when show_value=True.

    Properties:
        min: Minimum value (default: 0)
        max: Maximum value (default: 100)
        value: Current value (default: 0)
        step: Step size for keyboard navigation (default: 1)
        show_value: Whether to display value label (default: True)
        enabled: Whether slider is interactive (default: True)

    Signals:
        value_changed(int): Emitted when slider value changes
        slider_pressed(): Emitted when user presses handle
        slider_released(): Emitted when user releases handle

    Example:
        slider = Slider(min=0, max=100, value=50, show_value=True)
        slider.value_changed.connect(lambda v: print(f"Value: {v}"))

        # Update programmatically
        slider.set_value(75)

        # Get current value
        current = slider.get_value()
    """

    # Custom signals beyond BasePrimitive
    value_changed = Signal(int)  # Slider value changed
    slider_pressed = Signal()  # Handle pressed
    slider_released = Signal()  # Handle released

    # Size configurations
    _SIZES = {
        "sm": {
            "height": TOKENS_V2.sizes.button_sm,  # 22px
            "handle_size": 12,
        },
        "md": {
            "height": TOKENS_V2.sizes.button_md,  # 28px
            "handle_size": 14,
        },
        "lg": {
            "height": TOKENS_V2.sizes.button_lg,  # 34px
            "handle_size": 16,
        },
    }

    def __init__(
        self,
        min: int = 0,
        max: int = 100,
        value: int = 0,
        step: int = 1,
        show_value: bool = True,
        enabled: bool = True,
        size: SliderSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the slider.

        Args:
            min: Minimum value
            max: Maximum value
            value: Initial value
            step: Step increment for keyboard
            show_value: Show value label next to slider
            enabled: Initial enabled state
            size: Size variant (sm/md/lg)
            parent: Optional parent widget
        """
        self._min_val = min
        self._max_val = max
        self._initial_value = value
        self._step = step
        self._show_value = show_value
        self._size: SliderSize = size
        self._enabled = enabled

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Create slider and optional value label."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Create horizontal slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setRange(self._min_val, self._max_val)
        self._slider.setValue(self._initial_value)
        self._slider.setSingleStep(self._step)
        self._slider.setEnabled(self._enabled)

        # Apply v2 styling
        self._slider.setStyleSheet(self._get_slider_stylesheet())

        # Set fixed height based on size
        size_config = self._SIZES[self._size]
        self._slider.setFixedHeight(size_config["height"])

        layout.addWidget(self._slider)

        # Add value label if requested
        if self._show_value:
            from PySide6.QtWidgets import QLabel

            self._value_label = QLabel(str(self._initial_value))
            self._value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._value_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME_V2.text_secondary};
                    font-size: {TOKENS_V2.typography.body_sm}px;
                    background: transparent;
                }}
            """)
            layout.addWidget(self._value_label)
        else:
            self._value_label = None

    def connect_signals(self) -> None:
        """Connect slider signals."""
        self._slider.valueChanged.connect(self._on_value_changed)
        self._slider.sliderPressed.connect(self._on_pressed)
        self._slider.sliderReleased.connect(self._on_released)

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle slider value change."""
        if self._value_label is not None:
            self._value_label.setText(str(value))
        self.value_changed.emit(value)

    @Slot()
    def _on_pressed(self) -> None:
        """Handle slider press."""
        self.slider_pressed.emit()

    @Slot()
    def _on_released(self) -> None:
        """Handle slider release."""
        self.slider_released.emit()

    def _get_slider_stylesheet(self) -> str:
        """Get v2 stylesheet for slider."""
        size_config = self._SIZES[self._size]
        handle_size = size_config["handle_size"]

        return f"""
            QSlider::groove:horizontal {{
                background: {THEME_V2.bg_component};
                height: 4px;
                border-radius: 2px;
                margin: 0px;
            }}

            QSlider::handle:horizontal {{
                background: {THEME_V2.primary};
                border: 2px solid {THEME_V2.bg_surface};
                width: {handle_size}px;
                height: {handle_size}px;
                border-radius: {handle_size // 2}px;
                margin: -{(handle_size - 4) // 2}px 0;
            }}

            QSlider::handle:horizontal:hover {{
                background: {THEME_V2.primary_hover};
            }}

            QSlider::handle:horizontal:pressed {{
                background: {THEME_V2.primary_active};
            }}

            QSlider::sub-page:horizontal {{
                background: {THEME_V2.primary};
                border-radius: 2px;
            }}

            QSlider::add-page:horizontal {{
                background: {THEME_V2.bg_component};
                border-radius: 2px;
            }}

            QSlider:disabled {{
                opacity: 0.5;
            }}
        """

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def get_value(self) -> int:
        """Get current slider value."""
        return self._slider.value()

    def set_value(self, value: int) -> None:
        """Set slider value."""
        self._slider.setValue(value)

    def get_min(self) -> int:
        """Get minimum value."""
        return self._slider.minimum()

    def set_min(self, min: int) -> None:
        """Set minimum value."""
        self._slider.setMinimum(min)

    def get_max(self) -> int:
        """Get maximum value."""
        return self._slider.maximum()

    def set_max(self, max: int) -> None:
        """Set maximum value."""
        self._slider.setMaximum(max)

    def get_step(self) -> int:
        """Get step size."""
        return self._slider.singleStep()

    def set_step(self, step: int) -> None:
        """Set step size."""
        self._slider.setSingleStep(step)

    def set_show_value(self, show: bool) -> None:
        """Show or hide value label."""
        if show and self._value_label is None:
            # Need to add label
            from PySide6.QtWidgets import QLabel

            layout = self.layout()
            self._value_label = QLabel(str(self._slider.value()))
            self._value_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self._value_label.setStyleSheet(f"""
                QLabel {{
                    color: {THEME_V2.text_secondary};
                    font-size: {TOKENS_V2.typography.body_sm}px;
                    background: transparent;
                }}
            """)
            layout.addWidget(self._value_label)
        elif not show and self._value_label is not None:
            # Remove label
            self._value_label.deleteLater()
            self._value_label = None


# =============================================================================
# PROGRESS BAR
# =============================================================================


class ProgressBar(BasePrimitive):
    """
    Themed progress bar with v2 styling and indeterminate mode.

    Display-only component that shows progress within a range.
    Indeterminate mode shows a striped pattern for loading states.

    Properties:
        value: Current progress value (default: 0)
        min: Minimum value (default: 0)
        max: Maximum value (default: 100)
        indeterminate: Show striped loading pattern (default: False)
        show_text: Display percentage text (default: True)

    Signals:
        None - display only component

    Example:
        # Normal progress
        progress = ProgressBar(value=50, min=0, max=100, show_text=True)
        progress.set_value(75)  # Update to 75%

        # Indeterminate (loading)
        loading = ProgressBar(indeterminate=True, show_text=False)

        # Hide text for cleaner look
        quiet = ProgressBar(value=30, show_text=False)
    """

    # Size configurations
    _SIZES = {
        "sm": {
            "height": TOKENS_V2.sizes.button_sm,  # 22px
        },
        "md": {
            "height": TOKENS_V2.sizes.button_md,  # 28px
        },
        "lg": {
            "height": TOKENS_V2.sizes.button_lg,  # 34px
        },
    }

    def __init__(
        self,
        value: int = 0,
        min: int = 0,
        max: int = 100,
        indeterminate: bool = False,
        show_text: bool = True,
        size: ProgressBarSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the progress bar.

        Args:
            value: Initial progress value
            min: Minimum value
            max: Maximum value
            indeterminate: Show indeterminate loading state
            show_text: Show percentage text
            size: Size variant (sm/md/lg)
            parent: Optional parent widget
        """
        self._initial_value = value
        self._min_val = min
        self._max_val = max
        self._indeterminate = indeterminate
        self._show_text = show_text
        self._size: ProgressBarSize = size

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Create progress bar."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._progress = QProgressBar()
        self._progress.setRange(self._min_val, self._max_val)
        self._progress.setValue(self._initial_value)
        self._progress.setTextVisible(self._show_text)

        # Apply v2 styling
        self._progress.setStyleSheet(self._get_progress_stylesheet())

        # Set fixed height based on size
        size_config = self._SIZES[self._size]
        self._progress.setFixedHeight(size_config["height"])

        layout.addWidget(self._progress)

    def connect_signals(self) -> None:
        """No signals for display-only component."""
        pass

    def _get_progress_stylesheet(self) -> str:
        """Get v2 stylesheet for progress bar."""
        if self._indeterminate:
            # Striped pattern for indeterminate state
            return f"""
                QProgressBar {{
                    background: {THEME_V2.bg_component};
                    border: 1px solid {THEME_V2.border};
                    border-radius: {TOKENS_V2.radius.sm}px;
                    text-align: center;
                    color: {THEME_V2.text_primary};
                    font-size: {TOKENS_V2.typography.body_sm}px;
                }}

                QProgressBar::chunk {{
                    background-color: {THEME_V2.primary};
                    border-radius: {TOKENS_V2.radius.sm}px;
                    /* Striped pattern using gradient (static, no animation) */
                    background: qlineargradient(
                        x1:0, y1:0, x2:10, y2:0,
                        stop:0 {THEME_V2.primary},
                        stop:0.25 {THEME_V2.primary_active},
                        stop:0.5 {THEME_V2.primary},
                        stop:0.75 {THEME_V2.primary_active},
                        stop:1 {THEME_V2.primary}
                    );
                }}
            """
        else:
            # Solid fill for determinate state
            return f"""
                QProgressBar {{
                    background: {THEME_V2.bg_component};
                    border: 1px solid {THEME_V2.border};
                    border-radius: {TOKENS_V2.radius.sm}px;
                    text-align: center;
                    color: {THEME_V2.text_primary};
                    font-size: {TOKENS_V2.typography.body_sm}px;
                }}

                QProgressBar::chunk {{
                    background-color: {THEME_V2.primary};
                    border-radius: {TOKENS_V2.radius.sm}px;
                }}
            """

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def get_value(self) -> int:
        """Get current progress value."""
        return self._progress.value()

    def set_value(self, value: int) -> None:
        """Set progress value."""
        self._progress.setValue(value)

    def get_min(self) -> int:
        """Get minimum value."""
        return self._progress.minimum()

    def set_min(self, min: int) -> None:
        """Set minimum value."""
        self._progress.setMinimum(min)

    def get_max(self) -> int:
        """Get maximum value."""
        return self._progress.maximum()

    def set_max(self, max: int) -> None:
        """Set maximum value."""
        self._progress.setMaximum(max)

    def set_indeterminate(self, indeterminate: bool) -> None:
        """Set indeterminate mode (shows striped pattern)."""
        self._indeterminate = indeterminate
        self._progress.setStyleSheet(self._get_progress_stylesheet())

    def is_indeterminate(self) -> bool:
        """Check if in indeterminate mode."""
        return self._indeterminate

    def set_show_text(self, show: bool) -> None:
        """Show or hide percentage text."""
        self._show_text = show
        self._progress.setTextVisible(show)


# =============================================================================
# DIAL
# =============================================================================


class Dial(BasePrimitive):
    """
    Themed rotary dial for angular value input.

    Wraps QDial with v2 dark theme styling. Useful for angular
    or rotational controls (volume, angle, etc).

    Properties:
        min: Minimum value (default: 0)
        max: Maximum value (default: 100)
        value: Current value (default: 0)
        wrapping: Allow wraparound at min/max (default: False)
        enabled: Whether dial is interactive (default: True)

    Signals:
        value_changed(int): Emitted when dial value changes

    Example:
        # Volume control style
        volume = Dial(min=0, max=100, value=50)
        volume.value_changed.connect(lambda v: print(f"Volume: {v}%"))

        # Angle control with wrapping
        angle = Dial(min=0, max=360, value=180, wrapping=True)
    """

    # Custom signal
    value_changed = Signal(int)  # Dial value changed

    # Fixed dial size (square)
    _DEFAULT_SIZE = 80
    _MIN_SIZE = 60
    _MAX_SIZE = 120

    def __init__(
        self,
        min: int = 0,
        max: int = 100,
        value: int = 0,
        wrapping: bool = False,
        enabled: bool = True,
        size: int = _DEFAULT_SIZE,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize the dial.

        Args:
            min: Minimum value
            max: Maximum value
            value: Initial value
            wrapping: Allow wraparound at range limits
            enabled: Initial enabled state
            size: Dial size in pixels (square)
            parent: Optional parent widget
        """
        # Store parameters before shadowing built-ins
        min_val = min
        max_val = max
        val = value
        wrap = wrapping
        en = enabled
        sz = size

        self._min_val = min_val
        self._max_val = max_val
        self._initial_value = val
        self._wrapping = wrap
        self._enabled = en
        # Use builtins.min/max since parameter names shadow the built-ins
        self._size = builtins.max(self._MIN_SIZE, builtins.min(self._MAX_SIZE, sz))

        super().__init__(parent)

    def setup_ui(self) -> None:
        """Create dial widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._dial = QDial()
        self._dial.setRange(self._min_val, self._max_val)
        self._dial.setValue(self._initial_value)
        self._dial.setWrapping(self._wrapping)
        self._dial.setEnabled(self._enabled)
        self._dial.setNotchesVisible(True)
        self._dial.setNotchTarget(10)  # Show notch every 10 units

        # Apply v2 styling
        self._dial.setStyleSheet(self._get_dial_stylesheet())

        # Fixed square size
        self._dial.setFixedSize(self._size, self._size)

        layout.addWidget(self._dial)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def connect_signals(self) -> None:
        """Connect dial signals."""
        self._dial.valueChanged.connect(self._on_value_changed)

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """Handle dial value change."""
        self.value_changed.emit(value)

    def _get_dial_stylesheet(self) -> str:
        """Get v2 stylesheet for dial."""
        return f"""
            QDial {{
                background: {THEME_V2.bg_component};
                border: 1px solid {THEME_V2.border};
                border-radius: {self._size // 2}px;
            }}

            QDial::handle {{
                background: {THEME_V2.primary};
                border: 2px solid {THEME_V2.bg_surface};
                width: 8px;
                height: 8px;
                border-radius: 4px;
            }}

            QDial::handle:hover {{
                background: {THEME_V2.primary_hover};
            }}

            QDial::handle:pressed {{
                background: {THEME_V2.primary_active};
            }}

            QDial::groove {{
                background: {THEME_V2.bg_canvas};
                border: 1px solid {THEME_V2.border};
                border-radius: {self._size // 2}px;
            }}

            QDial:disabled {{
                opacity: 0.5;
            }}
        """

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def get_value(self) -> int:
        """Get current dial value."""
        return self._dial.value()

    def set_value(self, value: int) -> None:
        """Set dial value."""
        self._dial.setValue(value)

    def get_min(self) -> int:
        """Get minimum value."""
        return self._dial.minimum()

    def set_min(self, min: int) -> None:
        """Set minimum value."""
        self._dial.setMinimum(min)

    def get_max(self) -> int:
        """Get maximum value."""
        return self._dial.maximum()

    def set_max(self, max: int) -> None:
        """Set maximum value."""
        self._dial.setMaximum(max)

    def get_wrapping(self) -> bool:
        """Get wrapping state."""
        return self._dial.wrapping()

    def set_wrapping(self, wrapping: bool) -> None:
        """Set wrapping state."""
        self._dial.setWrapping(wrapping)

    def set_notches_visible(self, visible: bool) -> None:
        """Show or hide notch marks."""
        self._dial.setNotchesVisible(visible)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_slider(
    min: int = 0,
    max: int = 100,
    value: int = 0,
    show_value: bool = True,
    size: SliderSize = "md",
    parent: QWidget | None = None,
) -> Slider:
    """
    Convenience function to create a Slider.

    Args:
        min: Minimum value
        max: Maximum value
        value: Initial value
        show_value: Show value label
        size: Size variant
        parent: Optional parent widget

    Returns:
        Configured Slider instance
    """
    return Slider(min=min, max=max, value=value, show_value=show_value, size=size, parent=parent)


def create_progress(
    value: int = 0,
    min: int = 0,
    max: int = 100,
    indeterminate: bool = False,
    show_text: bool = True,
    size: ProgressBarSize = "md",
    parent: QWidget | None = None,
) -> ProgressBar:
    """
    Convenience function to create a ProgressBar.

    Args:
        value: Initial progress value
        min: Minimum value
        max: Maximum value
        indeterminate: Show indeterminate loading state
        show_text: Show percentage text
        size: Size variant
        parent: Optional parent widget

    Returns:
        Configured ProgressBar instance
    """
    return ProgressBar(
        value=value,
        min=min,
        max=max,
        indeterminate=indeterminate,
        show_text=show_text,
        size=size,
        parent=parent,
    )


def create_dial(
    min: int = 0,
    max: int = 100,
    value: int = 0,
    wrapping: bool = False,
    size: int = Dial._DEFAULT_SIZE,
    parent: QWidget | None = None,
) -> Dial:
    """
    Convenience function to create a Dial.

    Args:
        min: Minimum value
        max: Maximum value
        value: Initial value
        wrapping: Allow wraparound
        size: Dial size in pixels
        parent: Optional parent widget

    Returns:
        Configured Dial instance
    """
    return Dial(min=min, max=max, value=value, wrapping=wrapping, size=size, parent=parent)


__all__ = [
    # Types
    "SliderSize",
    "ProgressBarSize",
    # Components
    "Slider",
    "ProgressBar",
    "Dial",
    # Utilities
    "create_slider",
    "create_progress",
    "create_dial",
]
