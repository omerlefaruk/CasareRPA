"""
BasePrimitive - V2 Primitive Widget Base Class.

Epic 5.1 Component Library v2:
Lightweight base class for all primitive UI widgets (buttons, inputs, etc.).

Provides:
- Template pattern for consistent widget initialization
- V2 theming helpers (THEME_V2, TOKENS_V2)
- Common signals for value/state changes
- Abstract setup_ui() requirement
- Optional connect_signals() and custom stylesheet hooks

Usage:
    from casare_rpa.presentation.canvas.ui.widgets.primitives import BasePrimitive

    class MyButton(BasePrimitive):
        def setup_ui(self) -> None:
            # Create child widgets
            self._button = QPushButton("Click me", self)

        def connect_signals(self) -> None:
            # Connect signal handlers
            self._button.clicked.connect(self._on_clicked)

        def _on_clicked(self) -> None:
            self.value_changed.emit("clicked")

    # In use
    button = MyButton()
    button.value_changed.connect(lambda v: print(f"Value: {v}"))

Pattern:
- __init__ calls: setup_ui() -> _apply_v2_theme() -> connect_signals()
- No hardcoded colors (use THEME_V2 only)
- All sizing uses TOKENS_V2 helpers
- Signals for loose coupling

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Literal

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from casare_rpa.presentation.canvas.theme import TOKENS_V2

if TYPE_CHECKING:
    from PySide6.QtGui import QFont

# Type aliases for helper methods
SizeVariant = Literal["sm", "md", "lg"]
FontVariant = Literal[
    "display_lg",
    "display_md",
    "heading_lg",
    "heading_md",
    "heading_sm",
    "body_lg",
    "body",
    "body_sm",
    "caption",
]
MarginPreset = Literal[
    "none", "tight", "compact", "standard", "comfortable", "spacious", "dialog", "panel", "form_row"
]


class BasePrimitive(QWidget):
    """
    Base class for v2 primitive widgets.

    Provides template pattern for consistent widget initialization:
    1. setup_ui() - create child widgets (ABSTRACT, must override)
    2. _apply_v2_theme() - apply v2 dark theme (optional override)
    3. connect_signals() - connect signal handlers (optional override)

    Signals:
        value_changed: Emitted when widget value changes (payload is widget-specific)
        state_changed: Emitted when widget state changes (key, value pair)

    Theme Helpers:
        _set_size(size_variant): Set height using TOKENS_V2.sizes
        _set_font(variant): Set font using TOKENS_V2.typography
        _get_margins(preset): Get margin tuple from TOKENS_V2.margin
        _get_v2_stylesheet(): Override to provide custom stylesheet

    Example:
        class SearchInput(BasePrimitive):
            def setup_ui(self) -> None:
                layout = QHBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)

                self._input = QLineEdit()
                self._input.setPlaceholderText("Search...")
                layout.addWidget(self._input)

                self._clear_btn = QPushButton()
                self._clear_btn.setIcon(icon_v2.get_icon("x", size=16))
                self._clear_btn.setFixedSize(20, 20)
                layout.addWidget(self._clear_btn)

            def connect_signals(self) -> None:
                self._clear_btn.clicked.connect(self._on_clear)

            def _on_clear(self) -> None:
                self._input.clear()
                self.state_changed.emit("cleared", True)

        # Usage
        search = SearchInput()
        search.state_changed.connect(lambda k, v: print(f"{k}: {v}"))
    """

    # Common signals for all primitives
    value_changed = Signal(object)  # Payload varies by widget type
    state_changed = Signal(str, object)  # (key, value) for generic state events

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the primitive widget.

        Follows template pattern:
        1. Call QWidget.__init__
        2. Call setup_ui() - ABSTRACT, subclasses must implement
        3. Call _apply_v2_theme() - applies v2 dark theme styling
        4. Call connect_signals() - default: pass (no-op)

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Template pattern - fixed order for consistent initialization
        self.setup_ui()
        self._apply_v2_theme()
        self.connect_signals()

    # =========================================================================
    # ABSTRACT - Must Override
    # =========================================================================

    @abstractmethod
    def setup_ui(self) -> None:
        """
        Create and layout child widgets.

        Called during __init__, before theming and signal connection.
        Subclasses MUST implement this to create their UI components.

        Example:
            def setup_ui(self) -> None:
                layout = QVBoxLayout(self)
                layout.setContentsMargins(0, 0, 0, 0)

                self._label = QLabel("Hello")
                layout.addWidget(self._label)
        """
        raise NotImplementedError(f"{self.__class__.__name__}.setup_ui() must be implemented")

    # =========================================================================
    # Optional Overrides
    # =========================================================================

    def connect_signals(self) -> None:
        """
        Connect widget signals to handlers.

        Called during __init__, after setup_ui() and theming.
        Default implementation does nothing (no-op).

        Override this to connect signal handlers for child widgets.

        Example:
            def connect_signals(self) -> None:
                self._button.clicked.connect(self._on_clicked)
        """
        pass

    def _get_v2_stylesheet(self) -> str:
        """
        Get custom v2 stylesheet for this widget.

        Called by _apply_v2_theme(). Default returns empty string.
        Override to provide widget-specific styling.

        Use THEME_V2 colors and TOKENS_V2 values - no hardcoded colors.

        Example:
            def _get_v2_stylesheet(self) -> str:
                return f'''
                    BasePrimitive {{
                        background: {THEME_V2.bg_surface};
                        border: 1px solid {THEME_V2.border};
                        border-radius: {TOKENS_V2.radius.sm}px;
                    }}
                '''

        Returns:
            Stylesheet string (empty for default styling)
        """
        return ""

    # =========================================================================
    # Theme Helpers
    # =========================================================================

    def _apply_v2_theme(self) -> None:
        """
        Apply v2 dark theme styling to this widget.

        Calls _get_v2_stylesheet() and applies the result.
        Subclasses can override _get_v2_stylesheet() to customize styling.

        For most cases, prefer setting styles on child widgets in setup_ui()
        rather than overriding this method.
        """
        stylesheet = self._get_v2_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def _set_size(self, size_variant: SizeVariant = "md") -> None:
        """
        Set widget height using TOKENS_V2.sizes.

        Uses button sizing tokens as default (sm=22, md=28, lg=34).

        Args:
            size_variant: Size variant ("sm", "md", or "lg")

        Example:
            self._set_size("sm")  # Height = 22px
        """
        size_map: dict[SizeVariant, int] = {
            "sm": TOKENS_V2.sizes.button_sm,
            "md": TOKENS_V2.sizes.button_md,
            "lg": TOKENS_V2.sizes.button_lg,
        }
        self.setFixedHeight(size_map[size_variant])

    def _set_font(self, variant: FontVariant = "body") -> QFont:
        """
        Set widget font using TOKENS_V2.typography.

        Creates a new QFont with the specified size and family.
        Returns the QFont for further customization if needed.

        Args:
            variant: Typography variant from TOKENS_V2.typography

        Returns:
            QFont object applied to this widget

        Example:
            self._set_font("heading_md")
            font = self._set_font("body_sm")
            font.setBold(True)
        """
        from PySide6.QtGui import QFont

        font = QFont()
        font.setFamily(TOKENS_V2.typography.family)
        font.setPointSize(getattr(TOKENS_V2.typography, variant))
        self.setFont(font)
        return font

    def _get_margins(self, preset: MarginPreset = "standard") -> tuple[int, int, int, int]:
        """
        Get margin tuple from TOKENS_V2.margin presets.

        Returns (left, top, right, bottom) tuple for use with
        QLayout.setContentsMargins().

        Args:
            preset: Margin preset name

        Returns:
            Tuple of (left, top, right, bottom) margins

        Example:
            margins = self._get_margins("compact")
            layout.setContentsMargins(*margins)
        """
        return getattr(TOKENS_V2.margin, preset)

    def _set_margins(self, layout, preset: MarginPreset = "standard") -> None:
        """
        Apply margin preset to a layout.

        Convenience wrapper around _get_margins().

        Args:
            layout: QLayout to apply margins to
            preset: Margin preset name

        Example:
            self._set_margins(layout, "tight")
        """
        layout.setContentsMargins(*self._get_margins(preset))


__all__ = [
    "BasePrimitive",
    "SizeVariant",
    "FontVariant",
    "MarginPreset",
]
