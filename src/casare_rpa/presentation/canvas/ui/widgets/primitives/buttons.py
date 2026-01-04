"""
Button Components v2 - Epic 5.1 Component Library.

Themed button components using THEME_V2 and TOKENS_V2 for consistent styling.
Provides PushButton, ToolButton, and ButtonGroup with variants and sizes.

Components:
    PushButton: Primary button with variants (primary, secondary, ghost, danger)
    ToolButton: Icon-only or icon-text toggle button
    ButtonGroup: Container for mutually exclusive button groups

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import (
        PushButton,
        ToolButton,
        ButtonGroup,
    )

    # Push button with variants
    btn_primary = PushButton(text="Save", variant="primary", size="md")
    btn_danger = PushButton(text="Delete", variant="danger", size="sm")

    # Tool button with icon
    from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon
    btn_tool = ToolButton(icon=get_icon("settings", size=20), tooltip="Settings")

    # Button group for radio behavior
    group = ButtonGroup(
        buttons=[("Option 1", "opt1"), ("Option 2", "opt2")],
        exclusive=True
    )
    group.button_clicked.connect(lambda idx, btn: print(f"Selected: {btn}"))

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Literal

from loguru import logger
from PySide6.QtCore import QSize, Qt, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QDockWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

if TYPE_CHECKING:
    from PySide6.QtGui import QPaintEvent


# =============================================================================
# DENSITY HELPERS
# =============================================================================


def _is_in_dock_widget(widget: QWidget) -> bool:
    parent = widget.parentWidget()
    while parent is not None:
        if isinstance(parent, QDockWidget):
            return True
        parent = parent.parentWidget()
    return False


def _panel_compact_px(value: int, *, minimum: int) -> int:
    """
    Make panel buttons ~2x smaller while keeping a usable minimum size.

    We treat "x2 smaller" as "half the size", but clamp to a safe minimum so
    buttons remain clickable.
    """
    return max(minimum, int(round(value * 0.5)))


# =============================================================================
# TYPE ALIASES
# =============================================================================

ButtonVariant = Literal["primary", "secondary", "ghost", "danger", "warning"]
ButtonSize = Literal["sm", "md", "lg"]
ToolButtonVariant = Literal["icon-only", "icon-text"]
GroupOrientation = Literal["horizontal", "vertical"]


# =============================================================================
# PUSH BUTTON
# =============================================================================


class PushButton(QPushButton):
    """
    Themed push button with variants and sizes.

    Variants:
        primary: Accent color background (THEME_V2.primary)
        secondary: Component background (THEME_V2.bg_component)
        ghost: Transparent background with hover border
        danger: Error color background (THEME_V2.error)
        warning: Warning color background (THEME_V2.warning)

    Sizes:
        sm: 22px height, 16px icons
        md: 28px height, 20px icons (default)
        lg: 34px height, 24px icons

    Signals:
        clicked: Emitted when button is clicked (inherited from QPushButton)

    Example:
        btn = PushButton(text="Save", variant="primary", size="md")
        btn.clicked.connect(lambda: print("Clicked!"))

        btn_with_icon = PushButton(
            text="Delete",
            icon=get_icon("trash", size=20),
            variant="danger"
        )
    """

    # Size definitions from TOKENS_V2
    _SIZES = {
        "sm": {
            "height": TOKENS_V2.sizes.button_sm,
            "icon": TOKENS_V2.sizes.icon_sm,
            "padding_h": TOKENS_V2.spacing.sm,
            "padding_v": TOKENS_V2.spacing.xs,
        },
        "md": {
            "height": TOKENS_V2.sizes.button_md,
            "icon": TOKENS_V2.sizes.icon_md,
            "padding_h": TOKENS_V2.spacing.md,
            "padding_v": TOKENS_V2.spacing.xs,
        },
        "lg": {
            "height": TOKENS_V2.sizes.button_lg,
            "icon": TOKENS_V2.sizes.icon_lg,
            "padding_h": TOKENS_V2.spacing.lg,
            "padding_v": TOKENS_V2.spacing.xs,
        },
    }

    def __init__(
        self,
        text: str = "",
        parent: QWidget | None = None,
        icon: QIcon | None = None,
        variant: ButtonVariant = "primary",
        size: ButtonSize = "md",
        enabled: bool = True,
    ) -> None:
        """
        Initialize the push button.

        Args:
            text: Button text label
            parent: Optional parent widget
            icon: Optional icon (QIcon or use get_icon())
            variant: Button variant: primary, secondary, ghost, danger
            size: Button size: sm, md, lg
            enabled: Initial enabled state
        """
        super().__init__(text, parent)

        self._variant: ButtonVariant = variant
        self._size: ButtonSize = size

        self._setup_ui(icon, enabled)
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: variant={variant}, size={size}")

    def _setup_ui(self, icon: QIcon | None, enabled: bool) -> None:
        """Setup button UI properties."""
        # Set icon if provided
        if icon is not None:
            self.setIcon(icon)

        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set size policy
        self.setSizePolicy(
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )

        # Set enabled state
        self.setEnabled(enabled)

        # Apply size-specific settings
        size_spec = self._SIZES[self._size]
        is_panel_compact = _is_in_dock_widget(self)
        height = size_spec["height"]
        if is_panel_compact:
            # Avoid clipping descenders (p/y/g) in compact mode.
            height = _panel_compact_px(height, minimum=16)
        self.setFixedHeight(height)

        # Set icon size
        if icon is not None:
            icon_size = size_spec["icon"]
            if is_panel_compact:
                icon_size = _panel_compact_px(icon_size, minimum=12)
            self.setIconSize(QSize(icon_size, icon_size))

        # Set minimum width for better touch targets
        min_width = TOKENS_V2.sizes.button_min_width
        if is_panel_compact:
            min_width = _panel_compact_px(min_width, minimum=36)
        self.setMinimumWidth(min_width)

    def _apply_styles(self) -> None:
        """Apply variant-specific styling using THEME_V2."""
        t = THEME_V2
        radius = TOKENS_V2.radius.sm
        size_spec = self._SIZES[self._size]

        # Variant-specific colors
        match self._variant:
            case "primary":
                bg = t.primary
                bg_hover = t.primary_hover
                bg_active = t.primary_active
                text = t.text_on_primary
                border = t.primary
                border_hover = t.primary_hover
            case "secondary":
                bg = t.bg_component
                bg_hover = t.bg_hover
                bg_active = t.bg_selected
                text = t.text_primary
                border = t.border
                border_hover = t.border_focus
            case "ghost":
                bg = "transparent"
                bg_hover = t.bg_hover
                bg_active = t.bg_selected
                text = t.text_primary
                border = "transparent"
                border_hover = t.border_focus
            case "danger":
                bg = t.error
                bg_hover = t.error_hover
                bg_active = t.error_active
                text = t.text_on_error
                border = t.error
                border_hover = t.error_hover
            case "warning":
                bg = t.warning
                bg_hover = t.warning_hover
                bg_active = t.warning
                text = t.text_on_warning
                border = t.warning
                border_hover = t.warning_hover
            case _:
                # Fallback to primary
                bg = t.primary
                bg_hover = t.primary_hover
                bg_active = t.primary_active
                text = t.text_on_primary
                border = t.primary
                border_hover = t.primary_hover

        # Build stylesheet
        padding_h = size_spec["padding_h"]
        padding_v = size_spec["padding_v"]
        if _is_in_dock_widget(self):
            padding_h = _panel_compact_px(padding_h, minimum=2)
            padding_v = _panel_compact_px(padding_v, minimum=1)
            radius = TOKENS_V2.radius.xs
            font_size = TOKENS_V2.typography.body_sm
            font_weight = TOKENS_V2.typography.weight_medium
        else:
            font_size = TOKENS_V2.typography.body
            font_weight = TOKENS_V2.typography.weight_normal

        stylesheet = f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {radius}px;
                color: {text};
                font-family: {TOKENS_V2.typography.family};
                font-size: {font_size}px;
                font-weight: {font_weight};
                padding: {padding_v}px {padding_h}px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {bg_hover};
                border-color: {border_hover};
            }}
            QPushButton:pressed {{
                background-color: {bg_active};
                border-color: {bg_active};
            }}
            QPushButton:disabled {{
                background-color: {t.bg_component};
                border-color: {t.border};
                color: {t.text_disabled};
            }}
        """

        # Apply to button
        self.setStyleSheet(stylesheet)

    def set_variant(self, variant: ButtonVariant) -> None:
        """
        Update button variant.

        Args:
            variant: New variant: primary, secondary, ghost, danger
        """
        if self._variant != variant:
            self._variant = variant
            self._apply_styles()
            logger.debug(f"{self.__class__.__name__} variant changed to: {variant}")

    def get_variant(self) -> ButtonVariant:
        """Get current variant."""
        return self._variant

    def set_size(self, size: ButtonSize) -> None:
        """
        Update button size.

        Args:
            size: New size: sm, md, lg
        """
        if self._size != size:
            self._size = size
            size_spec = self._SIZES[size]
            height = size_spec["height"]
            if _is_in_dock_widget(self):
                height = _panel_compact_px(height, minimum=16)
            self.setFixedHeight(height)
            self._apply_styles()
            logger.debug(f"{self.__class__.__name__} size changed to: {size}")

    def get_size(self) -> ButtonSize:
        """Get current size."""
        return self._size


# =============================================================================
# TOOL BUTTON
# =============================================================================


class ToolButton(QPushButton):
    """
    Icon-based tool button with toggle support.

    Designed for toolbar actions and icon-only buttons.
    Supports icon-only mode or icon-with-text mode.

    Variants:
        icon-only: Shows only the icon (default)
        icon-text: Shows icon and optional text label

    States:
        checked: Visual indication when toggle button is active

    Signals:
        clicked: Emitted when button is clicked (inherited)
        toggled: Emitted when checked state changes (bool: checked)

    Example:
        from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

        # Icon-only toggle button
        toggle_btn = ToolButton(
            icon=get_icon("eye", size=20),
            tooltip="Toggle visibility",
            checked=True
        )
        toggle_btn.toggled.connect(lambda checked: print(f"Visible: {checked}"))

        # Icon with text
        edit_btn = ToolButton(
            icon=get_icon("edit", size=20),
            text="Edit",
            variant="icon-text"
        )
    """

    # Icon sizes from TOKENS_V2
    _ICON_SIZES = {
        "sm": TOKENS_V2.sizes.icon_sm,
        "md": TOKENS_V2.sizes.icon_md,
        "lg": TOKENS_V2.sizes.icon_lg,
    }

    def __init__(
        self,
        icon: QIcon,
        parent: QWidget | None = None,
        tooltip: str = "",
        checked: bool = False,
        checked_icon: QIcon | None = None,
        variant: ToolButtonVariant = "icon-only",
        text: str = "",
        icon_size: int = 20,
    ) -> None:
        """
        Initialize the tool button.

        Args:
            icon: Icon to display (use get_icon() from icons_v2)
            parent: Optional parent widget
            tooltip: Tooltip text
            checked: Initial checked state (sets checkable=True)
            checked_icon: Optional different icon when checked
            variant: Button variant: icon-only or icon-text
            text: Optional text label (only shown in icon-text variant)
            icon_size: Icon size in pixels (16, 20, or 24)
        """
        super().__init__(parent)

        self._variant: ToolButtonVariant = variant
        self._icon_size: int = icon_size
        self._checked_icon: QIcon | None = checked_icon
        self._normal_icon: QIcon = icon

        self._setup_ui(icon, text, tooltip, checked)
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} created: variant={variant}, checked={checked}")

    def _setup_ui(
        self,
        icon: QIcon,
        text: str,
        tooltip: str,
        checked: bool,
    ) -> None:
        """Setup button UI properties."""
        # Set icon and text
        self.setIcon(icon)
        if self._variant == "icon-text" and text:
            self.setText(text)

        # Set tooltip
        if tooltip:
            self.setToolTip(tooltip)

        # Set cursor
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Set size
        is_panel_compact = _is_in_dock_widget(self)
        icon_size = self._icon_size
        if is_panel_compact:
            icon_size = _panel_compact_px(icon_size, minimum=10)
        size = icon_size + TOKENS_V2.spacing.xs
        if is_panel_compact:
            size = _panel_compact_px(size, minimum=12)
        self.setFixedSize(size, size)

        if self._variant == "icon-text":
            # Wider for text
            self.setMinimumWidth(size * 2)
            self.setFixedHeight(size)

        # Set icon size
        self.setIconSize(QSize(icon_size, icon_size))

        # Enable toggle if checked state is specified
        if checked:
            self.setCheckable(True)
            self.setChecked(True)

    def _apply_styles(self) -> None:
        """Apply tool button styling using THEME_V2."""
        t = THEME_V2
        radius = TOKENS_V2.radius.xs
        padding = TOKENS_V2.spacing.xs
        if _is_in_dock_widget(self):
            padding = _panel_compact_px(padding, minimum=1)

        stylesheet = f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: {radius}px;
                color: {t.text_primary};
                padding: {padding}px;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                border-color: {t.border};
            }}
            QPushButton:pressed {{
                background-color: {t.bg_selected};
            }}
            QPushButton:checked {{
                background-color: {t.bg_selected};
                border-color: {t.border_focus};
            }}
            QPushButton:disabled {{
                color: {t.text_disabled};
            }}
        """

        self.setStyleSheet(stylesheet)

    @Slot()
    def paintEvent(self, event: QPaintEvent) -> None:
        """Override paint event to swap icons when checked."""
        # Swap icon if checked and checked_icon is set
        if self.isChecked() and self._checked_icon is not None:
            current_icon = self.icon()
            if current_icon.cacheKey() != self._checked_icon.cacheKey():
                self.setIcon(self._checked_icon)
        elif not self.isChecked() and self._normal_icon:
            current_icon = self.icon()
            if self._normal_icon.cacheKey() != current_icon.cacheKey():
                self.setIcon(self._normal_icon)

        super().paintEvent(event)

    def set_checked_state(self, checked: bool) -> None:
        """
        Update checked state.

        Args:
            checked: True to check, False to uncheck
        """
        if not self.isCheckable():
            self.setCheckable(True)
        self.setChecked(checked)

    def is_checked_state(self) -> bool:
        """Get current checked state."""
        return self.isChecked()


# =============================================================================
# BUTTON GROUP
# =============================================================================


class ButtonGroup(QWidget):
    """
    Container for mutually exclusive button groups.

    Groups buttons together for radio-like behavior when exclusive=True.
    Can be oriented horizontally or vertically.

    Signals:
        button_clicked: Emitted when any button is clicked (int: index, str: id)
        button_toggled: Emitted when button toggles (int: index, str: id, bool: checked)

    Example:
        group = ButtonGroup(
            buttons=[("Small", "sm"), ("Medium", "md"), ("Large", "lg")],
            exclusive=True,
            orientation="horizontal"
        )
        group.button_clicked.connect(lambda idx, btn_id: print(f"Selected: {btn_id}"))

        # Add to layout
        layout.addWidget(group)

        # Get selected
        selected_id = group.get_selected_id()  # Returns "sm", "md", or "lg"
    """

    button_clicked = Signal(int, str)
    button_toggled = Signal(int, str, bool)

    def __init__(
        self,
        buttons: list[tuple[str, str]] | None = None,
        parent: QWidget | None = None,
        exclusive: bool = True,
        orientation: GroupOrientation = "horizontal",
        size: ButtonSize = "sm",
        variant: ButtonVariant = "secondary",
    ) -> None:
        """
        Initialize the button group.

        Args:
            buttons: List of (label, id) tuples for group buttons
            parent: Optional parent widget
            exclusive: If True, only one button can be selected at a time
            orientation: Layout orientation: horizontal or vertical
            size: Button size for all buttons
            variant: Button variant for all buttons
        """
        super().__init__(parent)

        self._exclusive: bool = exclusive
        self._orientation: GroupOrientation = orientation
        self._size: ButtonSize = size
        self._variant: ButtonVariant = variant

        self._buttons: list[QPushButton] = []
        self._button_ids: list[str] = []

        # Qt button group for exclusive behavior
        self._qt_group = QButtonGroup(self)
        self._qt_group.setExclusive(exclusive)

        self._setup_ui()
        self._apply_styles()

        # Add buttons if provided
        if buttons:
            for label, btn_id in buttons:
                self.add_button(label, btn_id)

        logger.debug(f"{self.__class__.__name__} created: {len(self._buttons)} buttons")

    def _setup_ui(self) -> None:
        """Setup layout."""
        if self._orientation == "horizontal":
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(TOKENS_V2.spacing.xs)

    def _apply_styles(self) -> None:
        """Apply container styling."""
        stylesheet = """
            ButtonGroup {
                background-color: transparent;
                border: none;
            }
        """
        self.setStyleSheet(stylesheet)

    def add_button(self, label: str, btn_id: str) -> None:
        """
        Add a button to the group.

        Args:
            label: Button text label
            btn_id: Unique identifier for the button
        """
        # Create button
        btn = QPushButton(label, self)
        btn.setCheckable(self._exclusive)

        # Apply size-specific styling
        size_spec = PushButton._SIZES[self._size]
        btn.setFixedHeight(size_spec["height"])
        btn.setMinimumWidth(TOKENS_V2.sizes.button_min_width)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # Variant-specific base styling
        t = THEME_V2
        padding_h = size_spec["padding_h"]
        padding_v = size_spec["padding_v"]

        match self._variant:
            case "primary":
                bg = t.bg_component
                bg_selected = t.primary
                text = t.text_primary
                border = t.border
            case "secondary":
                bg = t.bg_component
                bg_selected = t.bg_selected
                text = t.text_primary
                border = t.border
            case "ghost":
                bg = "transparent"
                bg_selected = t.bg_selected
                text = t.text_primary
                border = "transparent"
            case _:
                bg = t.bg_component
                bg_selected = t.bg_selected
                text = t.text_primary
                border = t.border

        # Apply stylesheet with checked state
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: {TOKENS_V2.radius.sm}px;
                color: {text};
                font-family: {TOKENS_V2.typography.family};
                font-size: {TOKENS_V2.typography.body}px;
                padding: {padding_v}px {padding_h}px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {t.bg_hover};
                border-color: {t.border_focus};
            }}
            QPushButton:checked {{
                background-color: {bg_selected};
                border-color: {t.border_focus};
            }}
            QPushButton:disabled {{
                background-color: {t.bg_component};
                border-color: {t.border};
                color: {t.text_disabled};
            }}
        """)

        # Add to layout
        self.layout().addWidget(btn)

        # Add to internal lists
        idx = len(self._buttons)
        self._buttons.append(btn)
        self._button_ids.append(btn_id)
        self._qt_group.addButton(btn, idx)

        # Connect signals
        btn.clicked.connect(partial(self._on_button_clicked, idx, btn_id))
        if self._exclusive:
            # Use a wrapper for toggled to capture the checked parameter
            self._make_toggle_connection(btn, idx, btn_id)

        logger.debug(f"{self.__class__.__name__} added button: {label} (id={btn_id})")

    @Slot()
    def _on_button_clicked(self, index: int, btn_id: str) -> None:
        """Handle button click."""
        self.button_clicked.emit(index, btn_id)

    @Slot()
    def _on_button_toggled(self, index: int, btn_id: str, checked: bool) -> None:
        """Handle button toggle."""
        self.button_toggled.emit(index, btn_id, checked)

    def _make_toggle_connection(self, btn: QPushButton, index: int, btn_id: str) -> None:
        """
        Create toggle connection without lambda.

        Creates a closure that captures index and btn_id while accepting
        the checked parameter from the toggled signal.
        """
        # Store the connection parameters for later lookup
        if not hasattr(self, "_toggle_connections"):
            self._toggle_connections = {}

        def toggle_handler(checked: bool) -> None:
            self._on_button_toggled(index, btn_id, checked)

        # Store reference to prevent garbage collection
        self._toggle_connections[btn_id] = toggle_handler
        btn.toggled.connect(toggle_handler)

    def get_selected_id(self) -> str | None:
        """
        Get the ID of the currently selected button.

        Returns:
            Button ID or None if no selection
        """
        for btn in self._buttons:
            if btn.isChecked():
                idx = self._buttons.index(btn)
                return self._button_ids[idx]
        return None

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

    def set_selected_id(self, btn_id: str) -> None:
        """
        Set the selected button by ID.

        Args:
            btn_id: Button ID to select
        """
        try:
            idx = self._button_ids.index(btn_id)
            self._buttons[idx].setChecked(True)
        except ValueError:
            logger.warning(f"{self.__class__.__name__}: button ID not found: {btn_id}")

    def set_selected_index(self, index: int) -> None:
        """
        Set the selected button by index.

        Args:
            index: Button index to select
        """
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)
        else:
            logger.warning(f"{self.__class__.__name__}: button index out of range: {index}")

    def clear_selection(self) -> None:
        """Clear all button selections."""
        for btn in self._buttons:
            btn.setChecked(False)

    def get_button_count(self) -> int:
        """Get the number of buttons in the group."""
        return len(self._buttons)

    def get_button_ids(self) -> list[str]:
        """Get list of all button IDs."""
        return self._button_ids.copy()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def create_button(
    text: str,
    variant: ButtonVariant = "primary",
    size: ButtonSize = "md",
    parent: QWidget | None = None,
) -> PushButton:
    """
    Convenience function to create a PushButton.

    Args:
        text: Button text
        variant: Button variant (default: primary)
        size: Button size (default: md)
        parent: Optional parent widget

    Returns:
        Configured PushButton instance

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import (
            create_button
        )

        save_btn = create_button("Save", variant="primary")
        cancel_btn = create_button("Cancel", variant="secondary")
    """
    return PushButton(text=text, variant=variant, size=size, parent=parent)


def create_icon_button(
    icon_name: str,
    tooltip: str = "",
    parent: QWidget | None = None,
    icon_size: int = 20,
    checkable: bool = False,
) -> ToolButton:
    """
    Convenience function to create an icon-only ToolButton.

    Args:
        icon_name: Icon name from icons_v2 (e.g., "settings", "play")
        tooltip: Tooltip text
        parent: Optional parent widget
        icon_size: Icon size in pixels (default: 20)
        checkable: Whether button is toggleable

    Returns:
        Configured ToolButton instance

    Example:
        from casare_rpa.presentation.canvas.ui.widgets.primitives.buttons import (
            create_icon_button
        )

        play_btn = create_icon_button("play", tooltip="Run", checkable=True)
    """
    icon = get_icon(icon_name, size=icon_size)
    return ToolButton(
        icon=icon, parent=parent, tooltip=tooltip, checked=checkable, icon_size=icon_size
    )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types
    "ButtonVariant",
    "ButtonSize",
    "ToolButtonVariant",
    "GroupOrientation",
    # Components
    "PushButton",
    "ToolButton",
    "ButtonGroup",
    # Utilities
    "create_button",
    "create_icon_button",
]
