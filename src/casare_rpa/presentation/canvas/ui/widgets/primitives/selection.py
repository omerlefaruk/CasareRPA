"""
Selection Controls v2 - Epic 5.1 Component Library.

Themed selection controls using THEME_V2 and TOKENS_V2 for consistent styling.
Provides CheckBox, Switch, RadioButton, and RadioGroup components.

Components:
    CheckBox: Checkbox with tristate support
    Switch: Toggle switch with pill-shaped track
    RadioButton: Single radio button
    RadioGroup: Container managing radio button exclusivity

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.selection import (
        CheckBox,
        Switch,
        RadioButton,
        RadioGroup,
    )

    # Checkbox with tristate
    checkbox = CheckBox(text="Enable feature", checked=True, tristate=True)
    checkbox.checked_changed.connect(lambda checked: print(f"Checked: {checked}"))

    # Switch with on/off text
    switch = Switch(text="Dark mode", on_text="On", off_text="Off")
    switch.checked_changed.connect(lambda checked: print(f"Switch: {checked}"))

    # Radio group
    group = RadioGroup(
        items=[("Option 1", "opt1"), ("Option 2", "opt2"), ("Option 3", "opt3")],
        selected="opt1",
        orientation="horizontal"
    )
    group.selection_changed.connect(lambda value: print(f"Selected: {value}"))

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.ui.widgets.primitives.base_primitive import BasePrimitive

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


# =============================================================================
# TYPE ALIASES
# =============================================================================

RadioOrientation = Literal["horizontal", "vertical"]


# =============================================================================
# CHECK BOX
# =============================================================================


class CheckBox(QCheckBox):
    """
    Themed checkbox with tristate support.

    Uses THEME_V2 colors for consistent styling across the application.
    Supports three states when tristate is enabled: unchecked, checked, and partially checked.

    Props:
        text: Checkbox label text
        checked: Initial checked state (True/False)
        tristate: Enable three-state mode (unchecked/checked/partial)
        enabled: Initial enabled state

    Signals:
        checked_changed: Emitted when checkbox state changes (bool: checked)
        state_changed: Emitted when any state change occurs (int: state)

    Example:
        # Simple checkbox
        checkbox = CheckBox(text="Remember me", checked=True)
        checkbox.checked_changed.connect(lambda checked: print(f"Remember: {checked}"))

        # Tristate checkbox (for tree parent nodes)
        tristate = CheckBox(text="Select all", tristate=True)
        tristate.setCheckState(Qt.CheckState.PartiallyChecked)
    """

    checked_changed = Signal(bool)

    # Size constants
    _INDICATOR_SIZE = TOKENS_V2.sizes.checkbox_size  # 16px

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        checked: bool = False,
        tristate: bool = False,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the checkbox.

        Args:
            text: Checkbox label text
            parent: Optional parent widget
            checked: Initial checked state
            tristate: Enable three-state mode
            enabled: Initial enabled state
        """
        super().__init__(text, parent)

        self._tristate: bool = tristate

        self._setup_ui(checked, enabled)
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: text='{text}', checked={checked}")

    def _setup_ui(self, checked: bool, enabled: bool) -> None:
        """Setup checkbox UI properties."""
        # Set initial state
        self.setChecked(checked)

        # Enable tristate if requested
        if self._tristate:
            self.setTristate(True)

        # Set enabled state
        self.setEnabled(enabled)

        # Set cursor for better UX
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _apply_styles(self) -> None:
        """Apply checkbox styling using THEME_V2."""
        t = THEME_V2
        size = self._INDICATOR_SIZE
        radius = TOKENS_V2.radius.xs  # 2px for sharp-ish corners

        stylesheet = f"""
            QCheckBox {{
                spacing: {TOKENS_V2.spacing.xs}px;
                color: {t.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.family};
            }}

            QCheckBox::indicator {{
                width: {size}px;
                height: {size}px;
                border: 1px solid {t.border_light};
                border-radius: {radius}px;
                background-color: {t.input_bg};
            }}

            QCheckBox::indicator:hover {{
                border-color: {t.primary};
            }}

            QCheckBox::indicator:checked {{
                background-color: {t.primary};
                border-color: {t.primary};
            }}

            QCheckBox::indicator:indeterminate {{
                background-color: {t.primary};
                border-color: {t.primary};
            }}

            QCheckBox:disabled {{
                color: {t.text_disabled};
            }}

            QCheckBox::indicator:disabled {{
                background-color: {t.bg_surface};
                border-color: {t.border};
            }}
        """

        self.setStyleSheet(stylesheet)

    def checkState(self) -> Qt.CheckState:
        """Override to ensure checkState returns enum not int."""
        state = super().checkState()
        # Convert int to enum if needed
        if isinstance(state, int):
            state = Qt.CheckState(state)
        return state

    @Slot()
    def nextCheckState(self) -> None:
        """Override to emit custom signal."""
        super().nextCheckState()
        self.checked_changed.emit(self.isChecked())

    def setChecked(self, checked: bool) -> None:
        """Override to emit signal when programmatically set."""
        super().setChecked(checked)
        self.checked_changed.emit(checked)

    def set_tristate(self, tristate: bool) -> None:
        """
        Update tristate mode.

        Args:
            tristate: True to enable three-state mode
        """
        if self._tristate != tristate:
            self._tristate = tristate
            self.setTristate(tristate)
            logger.debug(f"{self.__class__.__name__} tristate set to: {tristate}")

    def is_tristate(self) -> bool:
        """Get current tristate mode."""
        return self._tristate


# =============================================================================
# SWITCH
# =============================================================================


class Switch(QWidget):
    """
    Toggle switch with pill-shaped track and sliding thumb.

    Modern toggle switch similar to iOS/Android switches.
    Displays an optional label and on/off text indicators.

    Props:
        text: Label text shown next to the switch
        checked: Initial checked state
        on_text: Text shown when checked (e.g., "On", "Yes")
        off_text: Text shown when unchecked (e.g., "Off", "No")
        enabled: Initial enabled state

    Signals:
        checked_changed: Emitted when switch state changes (bool: checked)

    Example:
        # Simple switch
        switch = Switch(text="Notifications", checked=True)
        switch.checked_changed.connect(lambda checked: print(f"Notifications: {checked}"))

        # Switch with on/off labels
        dark_mode = Switch(
            text="Dark mode",
            on_text="On",
            off_text="Off",
            checked=False
        )
    """

    checked_changed = Signal(bool)

    # Switch dimensions
    _TRACK_WIDTH = 40
    _TRACK_HEIGHT = 22
    _THUMB_SIZE = 18
    _THUMB_MARGIN = 2  # (TRACK_HEIGHT - THUMB_SIZE) / 2

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        checked: bool = False,
        on_text: str = "",
        off_text: str = "",
        enabled: bool = True,
    ) -> None:
        """
        Initialize the switch.

        Args:
            text: Label text shown next to the switch
            parent: Optional parent widget
            checked: Initial checked state
            on_text: Text shown when checked
            off_text: Text shown when unchecked
            enabled: Initial enabled state
        """
        super().__init__(parent)

        self._checked: bool = checked
        self._on_text: str = on_text
        self._off_text: str = off_text
        self._enabled: bool = enabled
        self._hovered: bool = False

        # Track position for animation thumb position
        self._thumb_position: float = (
            0.0 if not checked else self._TRACK_WIDTH - self._THUMB_SIZE - self._THUMB_MARGIN
        )

        self._setup_ui(text)
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: text='{text}', checked={checked}")

    def _setup_ui(self, text: str) -> None:
        """Setup switch UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.xs)

        # Add label if text provided
        if text or self._on_text or self._off_text:
            self._label = QLabel(text, self)
            self._label._base_text = text  # Store base text
            layout.addWidget(self._label)

        # Set widget size
        self.setFixedHeight(self._TRACK_HEIGHT)
        if text or self._on_text or self._off_text:
            layout.addStretch()

        # Enable mouse tracking for hover effect
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set enabled state
        self.setEnabled(self._enabled)

        # Update label with on/off text if provided
        self._update_label()

    def _apply_styles(self) -> None:
        """Apply widget styling."""
        self.setStyleSheet(f"""
            Switch {{
                background-color: transparent;
            }}
            QLabel {{
                color: {THEME_V2.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.family};
            }}
            Switch[disabled="true"] QLabel {{
                color: {THEME_V2.text_disabled};
            }}
        """)

    def _update_label(self) -> None:
        """Update label text with on/off indicator if configured."""
        if not hasattr(self, "_label"):
            return

        base_text = getattr(self._label, "_base_text", "")
        state_text = self._on_text if self._checked else self._off_text

        if base_text and state_text:
            # Format: "Label: State"
            self._label.setText(f"{base_text}: {state_text}")
        elif state_text and not base_text:
            # Just the state text
            self._label.setText(state_text)
        else:
            # Just the base text
            self._label.setText(base_text)

    @Slot()
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the switch widget."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        t = THEME_V2

        # Calculate switch position (after label if present)
        if hasattr(self, "_label") and self._label.text():
            switch_x = self._label.width() + TOKENS_V2.spacing.xs
        else:
            switch_x = 0

        # Determine colors based on state
        if not self.isEnabled():
            track_color = t.bg_component
            border_color = t.border
            thumb_color = t.text_disabled
        elif self._checked:
            track_color = t.primary
            border_color = t.primary
            thumb_color = t.text_on_primary
        else:
            track_color = t.bg_component
            border_color = t.border_light
            thumb_color = t.text_secondary

        # Draw track (rounded pill shape)
        track_rect = (switch_x, 0, self._TRACK_WIDTH, self._TRACK_HEIGHT)
        radius = self._TRACK_HEIGHT / 2

        painter.setPen(border_color)
        painter.setBrush(track_color)
        painter.drawRoundedRect(*track_rect, radius, radius)

        # Calculate thumb position
        if self._checked:
            thumb_x = switch_x + self._TRACK_WIDTH - self._THUMB_SIZE - self._THUMB_MARGIN
        else:
            thumb_x = switch_x + self._THUMB_MARGIN

        thumb_y = self._THUMB_MARGIN

        # Draw thumb (circle)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(thumb_color)
        painter.drawEllipse(int(thumb_x), int(thumb_y), self._THUMB_SIZE, self._THUMB_SIZE)

        painter.end()

    @Slot()
    def mousePressEvent(self, event) -> None:
        """Handle mouse click to toggle state."""
        if self.isEnabled():
            # Only toggle if clicking within switch area
            if hasattr(self, "_label") and self._label.text():
                switch_x = self._label.width() + TOKENS_V2.spacing.xs
                switch_end = switch_x + self._TRACK_WIDTH
            else:
                switch_x = 0
                switch_end = self._TRACK_WIDTH

            if switch_x <= event.position().x() <= switch_end:
                self.toggle()
            else:
                # Click on label also toggles
                self.toggle()

    @Slot()
    def toggle(self) -> None:
        """Toggle the switch state."""
        self._checked = not self._checked
        self._update_label()
        self.update()  # Trigger repaint
        self.checked_changed.emit(self._checked)
        logger.debug(f"{self.__class__.__name__} toggled to: {self._checked}")

    def set_checked(self, checked: bool) -> None:
        """
        Update switch state.

        Args:
            checked: True to check, False to uncheck
        """
        if self._checked != checked:
            self._checked = checked
            self._update_label()
            self.update()

    def is_checked(self) -> bool:
        """Get current checked state."""
        return self._checked

    def setEnabled(self, enabled: bool) -> None:
        """
        Update enabled state.

        Args:
            enabled: True to enable, False to disable
        """
        super().setEnabled(enabled)
        self._enabled = enabled
        self.setProperty("disabled", "true" if not enabled else "false")
        self.update()

    def is_enabled(self) -> bool:
        """Get enabled state."""
        return self._enabled


# =============================================================================
# RADIO BUTTON
# =============================================================================


class RadioButton(QRadioButton):
    """
    Themed radio button with v2 styling.

    Single radio button that should be used with RadioGroup for exclusivity.
    Uses THEME_V2 colors for consistent styling.

    Props:
        text: Button label text
        checked: Initial checked state
        enabled: Initial enabled state

    Signals:
        clicked: Emitted when button is clicked (inherited from QRadioButton)

    Example:
        # Use with RadioGroup for proper exclusivity
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selection import RadioGroup

        group = RadioGroup(
            items=[("Option A", "a"), ("Option B", "b")],
            selected="a"
        )
        group.selection_changed.connect(lambda value: print(f"Selected: {value}"))
    """

    # Indicator size
    _INDICATOR_SIZE = TOKENS_V2.sizes.checkbox_size  # 16px

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        checked: bool = False,
        enabled: bool = True,
    ) -> None:
        """
        Initialize the radio button.

        Args:
            text: Button label text
            parent: Optional parent widget
            checked: Initial checked state
            enabled: Initial enabled state
        """
        super().__init__(text, parent)

        self._setup_ui(checked, enabled)
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: text='{text}', checked={checked}")

    def _setup_ui(self, checked: bool, enabled: bool) -> None:
        """Setup radio button UI properties."""
        # Set initial state
        self.setChecked(checked)

        # Set enabled state
        self.setEnabled(enabled)

        # Set cursor for better UX
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _apply_styles(self) -> None:
        """Apply radio button styling using THEME_V2."""
        t = THEME_V2
        size = self._INDICATOR_SIZE

        stylesheet = f"""
            QRadioButton {{
                spacing: {TOKENS_V2.spacing.xs}px;
                color: {t.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                font-family: {TOKENS_V2.typography.family};
            }}

            QRadioButton::indicator {{
                width: {size}px;
                height: {size}px;
                border: 1px solid {t.border_light};
                border-radius: {size // 2}px;
                background-color: {t.input_bg};
            }}

            QRadioButton::indicator:hover {{
                border-color: {t.primary};
            }}

            QRadioButton::indicator:checked {{
                background-color: {t.input_bg};
                border-color: {t.primary};
            }}

            QRadioButton::indicator:checked::after {{
                /* Inner circle for checked state */
                content: "";
                width: {size // 2 - 2}px;
                height: {size // 2 - 2}px;
                border-radius: {size // 4}px;
                background-color: {t.primary};
            }}

            QRadioButton:disabled {{
                color: {t.text_disabled};
            }}

            QRadioButton::indicator:disabled {{
                background-color: {t.bg_surface};
                border-color: {t.border};
            }}
        """

        self.setStyleSheet(stylesheet)


# =============================================================================
# RADIO GROUP
# =============================================================================


class RadioGroup(BasePrimitive):
    """
    Container managing radio button exclusivity.

    Groups radio buttons together for mutually exclusive selection.
    Can be oriented horizontally or vertically.

    Props:
        items: List of dict with keys: value (str), label (str)
        selected: Initially selected value
        orientation: Layout orientation (horizontal/vertical)
        enabled: Initial enabled state for all buttons

    Signals:
        selection_changed: Emitted when selection changes (str: value)

    Example:
        # Create radio group
        group = RadioGroup(
            items=[
                {"value": "small", "label": "Small"},
                {"value": "medium", "label": "Medium"},
                {"value": "large", "label": "Large"},
            ],
            selected="medium",
            orientation="horizontal"
        )
        group.selection_changed.connect(lambda value: print(f"Size: {value}"))

        # Add to layout
        layout.addWidget(group)

        # Get/set selection
        current = group.get_selected()  # Returns "medium"
        group.set_selected("large")
    """

    selection_changed = Signal(str)

    def __init__(
        self,
        items: list[dict[str, str]] | None = None,
        parent: QWidget | None = None,
        selected: str | None = None,
        orientation: RadioOrientation = "vertical",
        enabled: bool = True,
    ) -> None:
        """
        Initialize the radio group.

        Args:
            items: List of {value, label} dicts for radio options
            parent: Optional parent widget
            selected: Initially selected value
            orientation: Layout orientation (horizontal/vertical)
            enabled: Initial enabled state for all buttons
        """
        self._items: list[dict[str, str]] = items or []
        self._selected: str | None = selected
        self._orientation: RadioOrientation = orientation
        self._enabled: bool = enabled
        self._buttons: list[QRadioButton] = []
        self._button_values: list[str] = []

        # Initialize base primitive (calls setup_ui, _apply_v2_theme, connect_signals)
        super().__init__(parent)

        # Add items after initialization
        if items:
            for item in items:
                self._add_radio_button(
                    label=item.get("label", item.get("value", "")),
                    value=item.get("value", item.get("label", "")),
                )

        # Set initial selection
        if selected:
            self.set_selected(selected)

        logger.debug(f"{self.__class__.__name__} created: {len(self._items)} items")

    def setup_ui(self) -> None:
        """Setup radio group layout."""
        if self._orientation == "horizontal":
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.sm)

    def connect_signals(self) -> None:
        """Connect signal handlers."""
        # Signals connected in _add_radio_button
        pass

    def _add_radio_button(self, label: str, value: str) -> None:
        """
        Add a radio button to the group.

        Args:
            label: Button label text
            value: Associated value for this option
        """
        btn = RadioButton(text=label, parent=self, enabled=self._enabled)

        # Add to layout
        self.layout().addWidget(btn)

        # Store references
        idx = len(self._buttons)
        self._buttons.append(btn)
        self._button_values.append(value)

        # Connect signal
        btn.clicked.connect(partial(self._on_button_clicked, idx, value))

        logger.debug(f"{self.__class__.__name__} added radio: {label} (value={value})")

    @Slot()
    def _on_button_clicked(self, index: int, value: str) -> None:
        """Handle radio button click."""
        # Update selection if this button is checked
        if self._buttons[index].isChecked():
            self._selected = value
            self.selection_changed.emit(value)
            logger.debug(f"{self.__class__.__name__} selection changed: {value}")

    def get_selected(self) -> str | None:
        """
        Get the currently selected value.

        Returns:
            Selected value or None if no selection
        """
        return self._selected

    def get_selected_index(self) -> int | None:
        """
        Get the index of the currently selected button.

        Returns:
            Button index or None if no selection
        """
        for idx, btn in enumerate(self._buttons):
            if btn.isChecked():
                return idx
        return None

    def set_selected(self, value: str) -> None:
        """
        Set the selected value.

        Args:
            value: Value to select
        """
        try:
            idx = self._button_values.index(value)
            self._buttons[idx].setChecked(True)
            self._selected = value
            logger.debug(f"{self.__class__.__name__} selection set to: {value}")
        except ValueError:
            logger.warning(f"{self.__class__.__name__}: value not found: {value}")

    def set_selected_index(self, index: int) -> None:
        """
        Set the selected button by index.

        Args:
            index: Button index to select
        """
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
            self._selected = self._button_values[index]
        else:
            logger.warning(f"{self.__class__.__name__}: index out of range: {index}")

    def get_items(self) -> list[dict[str, str]]:
        """Get list of all items."""
        return [
            {"value": value, "label": self._buttons[idx].text()}
            for idx, value in enumerate(self._button_values)
        ]

    def set_enabled(self, enabled: bool) -> None:
        """
        Set enabled state for all buttons.

        Args:
            enabled: True to enable, False to disable
        """
        self._enabled = enabled
        for btn in self._buttons:
            btn.setEnabled(enabled)

    def is_enabled(self) -> bool:
        """Get enabled state."""
        return self._enabled


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_checkbox(
    text: str,
    checked: bool = False,
    parent: QWidget | None = None,
) -> CheckBox:
    """
    Convenience function to create a CheckBox.

    Args:
        text: Checkbox label text
        checked: Initial checked state
        parent: Optional parent widget

    Returns:
        Configured CheckBox instance

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selection import (
            create_checkbox
        )

        checkbox = create_checkbox("Remember me", checked=True)
    """
    return CheckBox(text=text, checked=checked, parent=parent)


def create_switch(
    text: str = "",
    checked: bool = False,
    parent: QWidget | None = None,
) -> Switch:
    """
    Convenience function to create a Switch.

    Args:
        text: Label text
        checked: Initial checked state
        parent: Optional parent widget

    Returns:
        Configured Switch instance

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.selection import (
            create_switch
        )

        switch = create_switch("Dark mode", checked=False)
    """
    return Switch(text=text, checked=checked, parent=parent)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types
    "RadioOrientation",
    # Components
    "CheckBox",
    "Switch",
    "RadioButton",
    "RadioGroup",
    # Utilities
    "create_checkbox",
    "create_switch",
]
