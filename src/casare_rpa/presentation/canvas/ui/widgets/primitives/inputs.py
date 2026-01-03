"""
Input Primitive Components v2 - Epic 5.1 Component Library.

Provides reusable input widgets following the v2 design system:
- Compact sizing (sm/md/lg)
- THEME_V2 colors (dark-only, Cursor blue accent)
- icon_v2 for icons
- Proper @Slot decorators
- Type hints throughout

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import (
        TextInput,
        SearchInput,
        SpinBox,
        DoubleSpinBox,
    )

    # Basic text input
    name_input = TextInput(placeholder="Enter name", size="md")
    name_input.text_changed.connect(lambda text: print(text))

    # Search input with debounce
    search = SearchInput(placeholder="Search nodes...", search_delay=50)
    search.search_requested.connect(lambda query: perform_search(query))

    # Integer spin box
    spin = SpinBox(min=0, max=100, value=50, step=1)
    spin.value_changed.connect(lambda val: print(f"Value: {val}"))

    # Decimal spin box
    decimal = DoubleSpinBox(min=0.0, max=1.0, value=0.5, step=0.01)

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import Literal

from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QStyle,
    QToolButton,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

# =============================================================================
# TYPE ALIASES
# =============================================================================

InputSize = Literal["sm", "md", "lg"]

# =============================================================================
# SIZE HELPERS
# =============================================================================


def _get_input_height(size: InputSize) -> int:
    """Get input height for size variant."""
    return {
        "sm": TOKENS_V2.sizes.input_sm,
        "md": TOKENS_V2.sizes.input_md,
        "lg": TOKENS_V2.sizes.input_lg,
    }[size]


def _get_icon_size(size: InputSize) -> int:
    """Get icon size for input size variant."""
    return {
        "sm": 14,
        "md": 16,
        "lg": 18,
    }[size]


# =============================================================================
# STYLESHEET GENERATORS
# =============================================================================


def _get_input_stylesheet(
    size: InputSize = "md",
    readonly: bool = False,
    has_left_icon: bool = False,
    has_right_icon: bool = False,
) -> str:
    """
    Generate QSS stylesheet for TextInput.

    Args:
        size: Input size variant ("sm", "md", "lg")
        readonly: Whether input is read-only
        has_left_icon: Whether input has left icon (adjust padding)
        has_right_icon: Whether input has right icon (adjust padding)

    Returns:
        QSS stylesheet string
    """
    height = _get_input_height(size)
    padding_h = TOKENS_V2.spacing.xs
    padding_v = TOKENS_V2.spacing.xxs

    # Adjust padding when icons are present
    left_padding = padding_h + TOKENS_V2.spacing.md if has_left_icon else padding_h
    right_padding = padding_h + TOKENS_V2.spacing.md if has_right_icon else padding_h

    if readonly:
        readonly_style = f"""
            QLineEdit:disabled {{
                background-color: {THEME_V2.bg_surface};
                color: {THEME_V2.text_disabled};
                border-color: transparent;
            }}
        """
    else:
        readonly_style = ""

    return f"""
        QLineEdit {{
            background-color: {THEME_V2.input_bg};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {padding_v}px {right_padding}px {padding_v}px {left_padding}px;
            selection-background-color: {THEME_V2.primary};
            min-height: {height}px;
            font-size: {TOKENS_V2.typography.body}px;
        }}
        QLineEdit:focus {{
            border: 1px solid {THEME_V2.border_focus};
        }}
        {readonly_style}
    """


def _get_spinbox_stylesheet(size: InputSize = "md") -> str:
    """
    Generate QSS stylesheet for SpinBox/DoubleSpinBox.

    Args:
        size: Input size variant ("sm", "md", "lg")

    Returns:
        QSS stylesheet string
    """
    height = _get_input_height(size)

    return f"""
        QSpinBox, QDoubleSpinBox {{
            background-color: {THEME_V2.input_bg};
            color: {THEME_V2.text_primary};
            border: 1px solid {THEME_V2.border};
            border-radius: {TOKENS_V2.radius.sm}px;
            padding: {TOKENS_V2.spacing.xxs}px;
            min-height: {height}px;
            font-size: {TOKENS_V2.typography.body}px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 1px solid {THEME_V2.border_focus};
        }}
        QSpinBox::up-button, QDoubleSpinBox::up-button,
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            border: none;
            background: transparent;
            width: 16px;
        }}
        QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
        QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
            background: {THEME_V2.bg_hover};
            border-radius: 2px;
        }}
        QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
            image: none;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-bottom: 3px solid {THEME_V2.text_secondary};
            width: 0;
            height: 0;
        }}
        QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
            image: none;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 3px solid {THEME_V2.text_secondary};
            width: 0;
            height: 0;
        }}
        QSpinBox:disabled, QDoubleSpinBox:disabled {{
            background-color: {THEME_V2.bg_surface};
            color: {THEME_V2.text_disabled};
            border-color: transparent;
        }}
    """


# =============================================================================
# TEXT INPUT
# =============================================================================


class TextInput(QLineEdit):
    """
    Text input widget with v2 styling and optional clear button.

    Features:
    - Size variants (sm/md/lg) using TOKENS_V2
    - Optional clear button with icon_v2.get_icon("close")
    - Password mode support
    - Read-only mode
    - THEME_V2 colors throughout

    Signals:
        text_changed(str): Emitted when text changes
        editing_finished(): Emitted when editing is finished (Enter/Return pressed or focus lost)

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import TextInput

        # Basic input
        name = TextInput(placeholder="Enter name", size="md")
        name.text_changed.connect(lambda text: print(f"Typing: {text}"))

        # Password input with clear button
        password = TextInput(placeholder="Password", password=True, clearable=True)

        # Read-only input
        readonly = TextInput(value="Cannot change", readonly=True)
    """

    text_changed = Signal(str)
    editing_finished = Signal()

    def __init__(
        self,
        placeholder: str = "",
        value: str = "",
        *,
        clearable: bool = False,
        password: bool = False,
        size: InputSize = "md",
        readonly: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize TextInput.

        Args:
            placeholder: Placeholder text shown when empty
            value: Initial text value
            clearable: Show clear button (x icon) when has text
            password: Enable password mode (echo mode)
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            readonly: Disable editing
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size
        self._clearable = clearable
        self._password = password
        self._readonly = readonly
        self._placeholder_text = placeholder

        # Track if we're clearing programmatically (to avoid double emits)
        self._is_clearing = False

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()

        # Set initial value
        if value:
            self.setText(value)

        if readonly:
            self.setReadOnly(True)

        if password:
            self.setEchoMode(QLineEdit.EchoMode.Password)

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        # Set fixed height based on size variant
        self.setFixedHeight(_get_input_height(self._size))

        # Set placeholder
        if self._placeholder_text:
            self.setPlaceholderText(self._placeholder_text)

        # Add clear button if clearable
        if self._clearable:
            self._clear_btn = QToolButton(self)
            self._clear_btn.setCursor(Qt.PointingHandCursor)
            self._clear_btn.setIcon(
                get_icon("close", size=_get_icon_size(self._size), state="normal")
            )
            self._clear_btn.setStyleSheet("QToolButton { border: none; background: transparent; }")
            self._clear_btn.setVisible(False)  # Hidden until text is entered
            self._clear_btn.clicked.connect(self._on_clear_clicked)

            # Position button on the right side
            self._update_clear_button_position()
        else:
            self._clear_btn = None

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self.textChanged.connect(self._on_text_changed)
        self.editingFinished.connect(self._on_editing_finished)

    def _apply_stylesheet(self) -> None:
        """Apply the stylesheet based on current configuration."""
        has_right = self._clearable or self._password  # Password has eye button
        self.setStyleSheet(
            _get_input_stylesheet(
                size=self._size,
                readonly=self._readonly,
                has_right_icon=has_right,
            )
        )

    def _update_clear_button_position(self) -> None:
        """Position clear button on the right side of the input."""
        if self._clear_btn:
            frame_width = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
            button_size = self._clear_btn.iconSize().width() + TOKENS_V2.spacing.xs
            self._set_text_margins(right=button_size)

            # Move button to right side
            btn_y = (self.height() - self._clear_btn.height()) // 2
            self._clear_btn.move(
                self.width() - frame_width - button_size + TOKENS_V2.spacing.xxs,
                btn_y,
            )

    def _set_text_margins(self, right: int = 0) -> None:
        """Set text margins to account for clear button."""
        frame_width = self.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        self.setTextMargins(
            0,  # left
            0,  # top
            right + frame_width + TOKENS_V2.spacing.xs,  # right
            0,  # bottom
        )

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change.

        Args:
            text: New text value
        """
        # Update clear button visibility (always, even during clearing)
        if self._clearable and self._clear_btn:
            self._clear_btn.setVisible(bool(text and not self._password))

        # Emit signal (but not during programmatic clear)
        if not self._is_clearing:
            self.text_changed.emit(text)

    @Slot()
    def _on_editing_finished(self) -> None:
        """Handle editing finished event."""
        if not self._is_clearing:
            self.editing_finished.emit()

    @Slot()
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self._is_clearing = True
        try:
            self.clear()
            # Ensure button is hidden after clear
            if self._clear_btn:
                self._clear_btn.setVisible(False)
            self.setFocus()
        finally:
            self._is_clearing = False

    def clear(self) -> None:
        """Clear the text and hide the clear button."""
        super().clear()
        # Ensure button is hidden after clear (in case textChanged doesn't fire)
        if self._clearable and self._clear_btn:
            self._clear_btn.setVisible(False)

    def resizeEvent(self, event) -> None:
        """Handle resize event to reposition clear button."""
        super().resizeEvent(event)
        if self._clear_btn:
            self._update_clear_button_position()

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        if self._size != size:
            self._size = size
            self._apply_stylesheet()
            if self._clear_btn:
                self._clear_btn.setIcon(
                    get_icon("close", size=_get_icon_size(size), state="normal")
                )
                self._update_clear_button_position()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_value(self, value: str) -> None:
        """
        Set the text value programmatically.

        Args:
            value: New text value
        """
        self.setText(value)
        # Manually update clear button visibility since setText may not trigger textChanged
        if self._clearable and self._clear_btn:
            self._clear_btn.setVisible(bool(value and not self._password))

    def get_value(self) -> str:
        """Get current text value."""
        return self.text()

    def set_placeholder(self, text: str) -> None:
        """
        Set placeholder text.

        Args:
            text: Placeholder text
        """
        self.setPlaceholderText(text)

    def set_readonly(self, readonly: bool) -> None:
        """
        Set read-only state.

        Args:
            readonly: Whether input should be read-only
        """
        self._readonly = readonly
        self.setReadOnly(readonly)
        self._apply_stylesheet()

    def is_readonly(self) -> bool:
        """Check if input is read-only."""
        return self._readonly

    def set_password_mode(self, password: bool) -> None:
        """
        Set password mode.

        Args:
            password: Whether to enable password echo mode
        """
        self._password = password
        self.setEchoMode(QLineEdit.EchoMode.Password if password else QLineEdit.EchoMode.Normal)
        self._apply_stylesheet()

    def is_password_mode(self) -> bool:
        """Check if password mode is enabled."""
        return self._password

    def set_clearable(self, clearable: bool) -> None:
        """
        Set whether the input has a clear button.

        Args:
            clearable: Whether to show clear button
        """
        self._clearable = clearable
        if clearable and not self._clear_btn:
            # Add clear button
            self._setup_ui()
            self._apply_stylesheet()
            self._update_clear_button_position()
        elif not clearable and self._clear_btn:
            # Remove clear button
            self._clear_btn.deleteLater()
            self._clear_btn = None
            self._set_text_margins(right=0)
            self._apply_stylesheet()


# =============================================================================
# SEARCH INPUT
# =============================================================================


class SearchInput(QWidget):
    """
    Search input widget with debounced search signal.

    Extends TextInput with:
    - Search icon on the left (icon_v2.get_icon("search"))
    - Clear button on the right
    - Configurable debounce delay (default 50ms)
    - Separate search_requested signal that fires after debounce

    Signals:
        text_changed(str): Emitted immediately on every text change
        search_requested(str): Emitted after debounce delay

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import SearchInput

        # Create search input with default 50ms debounce
        search = SearchInput(placeholder="Search nodes...")
        search.search_requested.connect(lambda query: perform_search(query))

        # Custom debounce delay
        slow_search = SearchInput(placeholder="Search files...", search_delay=200)
    """

    text_changed = Signal(str)
    search_requested = Signal(str)

    def __init__(
        self,
        placeholder: str = "Search...",
        value: str = "",
        *,
        search_delay: int = 50,
        size: InputSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize SearchInput.

        Args:
            placeholder: Placeholder text
            value: Initial text value
            search_delay: Debounce delay in milliseconds (default: 50ms)
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size
        self._search_delay = search_delay
        self._placeholder_text = placeholder

        # Debounce timer
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)

        self._setup_ui()
        self._connect_signals()
        self._apply_stylesheet()

        # Set initial value
        if value:
            self._input.setText(value)

    def _setup_ui(self) -> None:
        """Set up the UI elements."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create main input
        self._input = QLineEdit()
        self._input.setPlaceholderText(self._placeholder_text)
        self._input.setFixedHeight(_get_input_height(self._size))
        layout.addWidget(self._input)

        # Search icon button (left side, decorative)
        self._search_icon = QToolButton(self._input)
        self._search_icon.setCursor(Qt.PointingHandCursor)
        self._search_icon.setIcon(
            get_icon("search", size=_get_icon_size(self._size), state="normal")
        )
        self._search_icon.setStyleSheet("QToolButton { border: none; background: transparent; }")
        self._search_icon.setEnabled(False)  # Just decorative

        # Clear button (right side)
        self._clear_btn = QToolButton(self._input)
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setIcon(get_icon("close", size=_get_icon_size(self._size), state="normal"))
        self._clear_btn.setStyleSheet("QToolButton { border: none; background: transparent; }")
        self._clear_btn.setVisible(False)
        self._clear_btn.clicked.connect(self.clear)

        # Set text margins for icons
        icon_size = _get_icon_size(self._size) + TOKENS_V2.spacing.sm
        self._set_text_margins(left=icon_size, right=icon_size)

        # Position icons
        self._update_icon_positions()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._input.textChanged.connect(self._on_text_changed)
        self._input.editingFinished.connect(self._on_editing_finished)

    def _apply_stylesheet(self) -> None:
        """Apply stylesheet to the wrapped input."""
        self._input.setStyleSheet(
            _get_input_stylesheet(
                size=self._size,
                readonly=False,
                has_left_icon=True,
                has_right_icon=True,
            )
        )

    def _set_text_margins(self, left: int = 0, right: int = 0) -> None:
        """Set text margins for icons."""
        frame_width = self._input.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)
        self._input.setTextMargins(
            left + frame_width,
            0,
            right + frame_width,
            0,
        )

    def _update_icon_positions(self) -> None:
        """Position search and clear icons."""
        frame_width = self._input.style().pixelMetric(QStyle.PixelMetric.PM_DefaultFrameWidth)

        # Search icon on left
        search_y = (self._input.height() - self._search_icon.height()) // 2
        self._search_icon.move(frame_width + TOKENS_V2.spacing.xxs, search_y)

        # Clear button on right
        clear_y = (self._input.height() - self._clear_btn.height()) // 2
        clear_x = (
            self._input.width() - frame_width - self._clear_btn.width() - TOKENS_V2.spacing.xxs
        )
        self._clear_btn.move(clear_x, clear_y)

    @Slot(str)
    def _on_text_changed(self, text: str) -> None:
        """
        Handle text change from the wrapped input.

        Args:
            text: New text value
        """
        # Update clear button visibility
        self._clear_btn.setVisible(bool(text))

        # Emit immediate signal
        self.text_changed.emit(text)

        # Restart debounce timer
        self._debounce_timer.start(self._search_delay)

    @Slot()
    def _on_debounce_timeout(self) -> None:
        """Handle debounce timer timeout."""
        self.search_requested.emit(self._input.text())

    @Slot()
    def _on_editing_finished(self) -> None:
        """Handle editing finished (Enter/Return pressed)."""
        # Trigger search immediately on Enter
        self._debounce_timer.stop()
        self.search_requested.emit(self._input.text())

    def resizeEvent(self, event) -> None:
        """Handle resize to reposition icons."""
        super().resizeEvent(event)
        self._update_icon_positions()

    def set_placeholder(self, text: str) -> None:
        """
        Set placeholder text.

        Args:
            text: Placeholder text
        """
        self._placeholder_text = text
        self._input.setPlaceholderText(text)

    def set_value(self, value: str) -> None:
        """
        Set the text value.

        Args:
            value: New text value
        """
        self._input.setText(value)
        # Manually update clear button visibility since setText doesn't always trigger textChanged
        if self._clear_btn:
            self._clear_btn.setVisible(bool(value))

    def get_value(self) -> str:
        """Get current text value."""
        return self._input.text()

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        if self._size != size:
            self._size = size
            icon_size = _get_icon_size(size)
            self._search_icon.setIcon(get_icon("search", size=icon_size, state="normal"))
            self._clear_btn.setIcon(get_icon("close", size=icon_size, state="normal"))
            self._apply_stylesheet()
            self._update_icon_positions()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_search_delay(self, delay_ms: int) -> None:
        """
        Set debounce delay.

        Args:
            delay_ms: Delay in milliseconds
        """
        self._search_delay = delay_ms

    def get_search_delay(self) -> int:
        """Get debounce delay in milliseconds."""
        return self._search_delay

    def clear(self) -> None:
        """Clear the search text."""
        self._input.clear()
        # Ensure clear button is hidden
        if self._clear_btn:
            self._clear_btn.setVisible(False)
        self.setFocus()

    def setFocus(self, reason: Qt.FocusReason = Qt.FocusReason.OtherFocusReason) -> None:
        """Set focus to the wrapped input."""
        self._input.setFocus(reason)

    def hasFocus(self) -> bool:
        """Check if the wrapped input has focus."""
        return self._input.hasFocus()


# =============================================================================
# SPIN BOX (INTEGER)
# =============================================================================


class SpinBox(QSpinBox):
    """
    Integer spin box with v2 styling.

    Features:
    - Size variants (sm/md/lg)
    - Configurable min/max/step
    - Optional prefix/suffix text
    - THEME_V2 colors

    Signals:
        value_changed(int): Emitted when value changes

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import SpinBox

        # Basic integer input
        quantity = SpinBox(min=0, max=100, value=1, step=1)
        quantity.value_changed.connect(lambda val: print(f"Quantity: {val}"))

        # With units
        width = SpinBox(min=10, max=1920, value=800, step=10, suffix=" px")

        # Percentage
        percent = SpinBox(min=0, max=100, value=50, suffix="%")
    """

    value_changed = Signal(int)

    def __init__(
        self,
        *,
        min: int = 0,
        max: int = 100,
        value: int = 0,
        step: int = 1,
        prefix: str = "",
        suffix: str = "",
        size: InputSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize SpinBox.

        Args:
            min: Minimum value
            max: Maximum value
            value: Initial value
            step: Increment/decrement step
            prefix: Text prefix (e.g., "$")
            suffix: Text suffix (e.g., "px", "%")
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size

        # Set fixed height based on size variant
        self.setFixedHeight(_get_input_height(size))

        # Configure range and step
        self.setMinimum(min)
        self.setMaximum(max)
        self.setValue(value)
        self.setSingleStep(step)

        # Set prefix/suffix
        if prefix:
            self.setPrefix(prefix)
        if suffix:
            self.setSuffix(suffix)

        # Apply v2 styling
        self._apply_stylesheet()

        # Connect to value change signal
        self.valueChanged.connect(self._on_value_changed)

    def _apply_stylesheet(self) -> None:
        """Apply v2 stylesheet."""
        self.setStyleSheet(_get_spinbox_stylesheet(size=self._size))

    @Slot(int)
    def _on_value_changed(self, value: int) -> None:
        """
        Handle value change from underlying widget.

        Args:
            value: New value
        """
        self.value_changed.emit(value)

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        self._size = size
        self._apply_stylesheet()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_value(self, value: int) -> None:
        """
        Set the value programmatically.

        Args:
            value: New value
        """
        # Block internal signal to avoid double emit, then emit our custom signal
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
        # Emit our custom signal
        self.value_changed.emit(value)

    def get_value(self) -> int:
        """Get current value."""
        return self.value()


# =============================================================================
# DOUBLE SPIN BOX (DECIMAL)
# =============================================================================


class DoubleSpinBox(QDoubleSpinBox):
    """
    Decimal spin box with v2 styling.

    Features:
    - Size variants (sm/md/lg)
    - Configurable min/max/step/decimals
    - Optional prefix/suffix text
    - THEME_V2 colors

    Signals:
        value_changed(float): Emitted when value changes

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.inputs import DoubleSpinBox

        # Basic decimal input
        opacity = DoubleSpinBox(min=0.0, max=1.0, value=1.0, step=0.01, decimals=2)
        opacity.value_changed.connect(lambda val: print(f"Opacity: {val}"))

        # Currency
        price = DoubleSpinBox(min=0.0, max=9999.99, value=0.0, step=0.01, decimals=2, prefix="$ ")

        # With units
        scale = DoubleSpinBox(min=0.1, max=5.0, value=1.0, step=0.1, suffix="x")
    """

    value_changed = Signal(float)

    def __init__(
        self,
        *,
        min: float = 0.0,
        max: float = 100.0,
        value: float = 0.0,
        step: float = 1.0,
        decimals: int = 2,
        prefix: str = "",
        suffix: str = "",
        size: InputSize = "md",
        parent: QWidget | None = None,
    ) -> None:
        """
        Initialize DoubleSpinBox.

        Args:
            min: Minimum value
            max: Maximum value
            value: Initial value
            step: Increment/decrement step
            decimals: Number of decimal places
            prefix: Text prefix (e.g., "$")
            suffix: Text suffix (e.g., "px", "x")
            size: Input height: "sm" (22px), "md" (28px), "lg" (34px)
            parent: Parent widget
        """
        super().__init__(parent)

        self._size = size

        # Set fixed height based on size variant
        self.setFixedHeight(_get_input_height(size))

        # Configure range and step
        self.setMinimum(min)
        self.setMaximum(max)
        self.setValue(value)
        self.setSingleStep(step)
        self.setDecimals(decimals)

        # Set prefix/suffix
        if prefix:
            self.setPrefix(prefix)
        if suffix:
            self.setSuffix(suffix)

        # Apply v2 styling
        self._apply_stylesheet()

        # Connect to value change signal
        self.valueChanged.connect(self._on_value_changed)

    def _apply_stylesheet(self) -> None:
        """Apply v2 stylesheet."""
        self.setStyleSheet(_get_spinbox_stylesheet(size=self._size))

    @Slot(float)
    def _on_value_changed(self, value: float) -> None:
        """
        Handle value change from underlying widget.

        Args:
            value: New value
        """
        self.value_changed.emit(value)

    def set_size(self, size: InputSize) -> None:
        """
        Change the input size.

        Args:
            size: New size variant ("sm", "md", "lg")
        """
        self._size = size
        self._apply_stylesheet()

    def get_size(self) -> InputSize:
        """Get current size variant."""
        return self._size

    def set_value(self, value: float) -> None:
        """
        Set the value programmatically.

        Args:
            value: New value
        """
        # Block internal signal to avoid double emit, then emit our custom signal
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
        # Emit our custom signal
        self.value_changed.emit(value)

    def get_value(self) -> float:
        """Get current value."""
        return self.value()

    def set_decimals(self, decimals: int) -> None:
        """
        Set number of decimal places.

        Args:
            decimals: Number of decimal places to show
        """
        super().setDecimals(decimals)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "InputSize",
    "TextInput",
    "SearchInput",
    "SpinBox",
    "DoubleSpinBox",
]

