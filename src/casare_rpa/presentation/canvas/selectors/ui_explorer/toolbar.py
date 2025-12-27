"""
UI Explorer Toolbar.

Toolbar component with action buttons for the UI Explorer dialog:
- Validate: Test current selector
- Indicate Element: Start element picker
- Indicate Anchor: Pick anchor element
- Repair: Try selector healing
- Highlight: Flash element on screen
- Options: Settings dropdown
"""

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QToolButton,
    QWidget,
)

from ...ui.theme import BORDER_RADIUS, FONT_SIZES, SPACING, THEME, TOKENS


class UIExplorerToolButton(QToolButton):
    """
    Styled toolbar button for UI Explorer actions.

    Supports toggle mode for buttons like Highlight.
    """

    def __init__(
        self,
        text: str,
        tooltip: str,
        checkable: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setText(text)
        self.setToolTip(tooltip)
        self.setCheckable(checkable)
        self.setFixedHeight(TOKENS.sizes.button_lg)
        self.setMinimumWidth(TOKENS.sizes.button_width_md)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._apply_style()

    def _apply_style(self) -> None:
        """Apply button styling."""
        self.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {BORDER_RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {FONT_SIZES.md}px;
                color: {THEME.text_primary};
            }}
            QToolButton:hover {{
                background: {THEME.bg_medium};
                border-color: {THEME.border_light};
            }}
            QToolButton:pressed {{
                background: {THEME.bg_darkest};
            }}
            QToolButton:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_hover};
                color: white;
            }}
            QToolButton:disabled {{
                background: {THEME.bg_darkest};
                color: {THEME.text_disabled};
                border-color: {THEME.bg_darker};
            }}
        """)

    def set_success_state(self) -> None:
        """Set button to success state (green indicator)."""
        self.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.accent_success};
                border: 1px solid {THEME.accent_success};
                border-radius: {BORDER_RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {FONT_SIZES.md}px;
                color: {THEME.accent_success};
            }}
            QToolButton:hover {{
                background: {THEME.accent_hover};
            }}
        """)

    def set_error_state(self) -> None:
        """Set button to error state (red indicator)."""
        self.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.accent_error};
                border: 1px solid {THEME.accent_error};
                border-radius: {BORDER_RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {FONT_SIZES.md}px;
                color: {THEME.accent_error};
            }}
            QToolButton:hover {{
                background: {THEME.accent_hover};
            }}
        """)

    def set_active_state(self) -> None:
        """Set button to active/pulsing state (blue)."""
        self.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.accent_primary};
                border: 1px solid {THEME.accent_primary};
                border-radius: {BORDER_RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {FONT_SIZES.md}px;
                color: {THEME.text_primary};
            }}
            QToolButton:hover {{
                background: {THEME.accent_hover};
            }}
        """)

    def reset_state(self) -> None:
        """Reset button to default state."""
        self._apply_style()


class UIExplorerToolbar(QWidget):
    """
    UI Explorer toolbar with action buttons.

    Signals:
        validate_clicked: Emitted when Validate button is clicked
        indicate_element_clicked: Emitted when Indicate Element button is clicked
        indicate_anchor_clicked: Emitted when Indicate Anchor button is clicked
        repair_clicked: Emitted when Repair button is clicked
        highlight_toggled: Emitted when Highlight button is toggled (bool: active)
        options_clicked: Emitted when Options button is clicked
        snapshot_clicked: Emitted when Snapshot button is clicked
        compare_clicked: Emitted when Compare button is clicked
        find_similar_clicked: Emitted when Find Similar button is clicked
        ai_suggest_clicked: Emitted when Smart Suggest button is clicked
    """

    validate_clicked = Signal()
    indicate_element_clicked = Signal()
    indicate_anchor_clicked = Signal()
    repair_clicked = Signal()
    highlight_toggled = Signal(bool)
    options_clicked = Signal()
    snapshot_clicked = Signal()
    compare_clicked = Signal()
    find_similar_clicked = Signal()
    ai_suggest_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Validate button (checkmark icon placeholder)
        self._validate_btn = UIExplorerToolButton(
            "Validate",
            "Test current selector (Ctrl+V)",
        )
        self._validate_btn.clicked.connect(self._on_validate)
        layout.addWidget(self._validate_btn)

        # Separator
        layout.addWidget(self._create_separator())

        # Indicate Element button (crosshair icon placeholder)
        self._indicate_element_btn = UIExplorerToolButton(
            "Indicate Element",
            "Start element picker (Ctrl+E)",
        )
        self._indicate_element_btn.clicked.connect(self._on_indicate_element)
        layout.addWidget(self._indicate_element_btn)

        # Indicate Anchor button (anchor icon placeholder)
        self._indicate_anchor_btn = UIExplorerToolButton(
            "Indicate Anchor",
            "Pick anchor element (Ctrl+A)",
        )
        self._indicate_anchor_btn.clicked.connect(self._on_indicate_anchor)
        layout.addWidget(self._indicate_anchor_btn)

        # Separator
        layout.addWidget(self._create_separator())

        # Repair button (wrench icon placeholder)
        self._repair_btn = UIExplorerToolButton(
            "Repair",
            "Try to heal broken selector",
        )
        self._repair_btn.setEnabled(False)  # Disabled until selector exists
        self._repair_btn.clicked.connect(self._on_repair)
        layout.addWidget(self._repair_btn)

        # Highlight button (toggle, lightbulb icon placeholder)
        self._highlight_btn = UIExplorerToolButton(
            "Highlight",
            "Toggle element highlight on screen (Ctrl+H)",
            checkable=True,
        )
        self._highlight_btn.toggled.connect(self._on_highlight_toggled)
        layout.addWidget(self._highlight_btn)

        # Separator
        layout.addWidget(self._create_separator())

        # Snapshot button
        self._snapshot_btn = UIExplorerToolButton(
            "Snapshot",
            "Capture element snapshot for comparison",
        )
        self._snapshot_btn.clicked.connect(self._on_snapshot)
        layout.addWidget(self._snapshot_btn)

        # Compare button
        self._compare_btn = UIExplorerToolButton(
            "Compare",
            "Compare current element with previous snapshot",
        )
        self._compare_btn.setEnabled(False)  # Disabled until snapshot exists
        self._compare_btn.clicked.connect(self._on_compare)
        layout.addWidget(self._compare_btn)

        # Separator
        layout.addWidget(self._create_separator())

        # Find Similar button
        self._find_similar_btn = UIExplorerToolButton(
            "Find Similar",
            "Find elements similar to current selection",
        )
        self._find_similar_btn.clicked.connect(self._on_find_similar)
        layout.addWidget(self._find_similar_btn)

        # Smart Suggest button (rule-based selector suggestions)
        self._ai_suggest_btn = UIExplorerToolButton(
            "Smart Suggest",
            "Generate ranked selector suggestions",
        )
        self._ai_suggest_btn.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.accent_info};
                border: 1px solid {THEME.accent_primary};
                border-radius: {BORDER_RADIUS.sm}px;
                padding: {SPACING.xs}px {SPACING.md}px;
                font-size: {FONT_SIZES.md}px;
                color: {THEME.accent_secondary};
            }}
            QToolButton:hover {{
                background: {THEME.accent_hover};
                border-color: {THEME.accent_primary};
                color: white;
            }}
            QToolButton:pressed {{
                background: {THEME.accent_primary};
            }}
            QToolButton:disabled {{
                background: {THEME.bg_darkest};
                color: {THEME.text_disabled};
                border-color: {THEME.bg_darker};
            }}
        """)
        self._ai_suggest_btn.clicked.connect(self._on_ai_suggest)
        layout.addWidget(self._ai_suggest_btn)

        # Spacer
        layout.addStretch()

        # Options button (gear icon placeholder)
        self._options_btn = UIExplorerToolButton(
            "Options",
            "Explorer settings",
        )
        self._options_btn.clicked.connect(self._on_options)
        layout.addWidget(self._options_btn)

        self._apply_styles()

    def _create_separator(self) -> QFrame:
        """Create a vertical separator line."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"background: {THEME.border};")
        sep.setFixedWidth(1)
        return sep

    def _apply_styles(self) -> None:
        """Apply toolbar styling."""
        self.setStyleSheet(f"""
            QWidget {{
                background: {THEME.bg_darkest};
                border-bottom: 1px solid {THEME.border};
            }}
        """)

    # =========================================================================
    # Signal Handlers
    # =========================================================================

    def _on_validate(self) -> None:
        """Handle Validate button click."""
        logger.debug("UIExplorerToolbar: Validate clicked")
        self.validate_clicked.emit()

    def _on_indicate_element(self) -> None:
        """Handle Indicate Element button click."""
        logger.debug("UIExplorerToolbar: Indicate Element clicked")
        self._indicate_element_btn.set_active_state()
        self.indicate_element_clicked.emit()

    def _on_indicate_anchor(self) -> None:
        """Handle Indicate Anchor button click."""
        logger.debug("UIExplorerToolbar: Indicate Anchor clicked")
        self._indicate_anchor_btn.set_active_state()
        self.indicate_anchor_clicked.emit()

    def _on_repair(self) -> None:
        """Handle Repair button click."""
        logger.debug("UIExplorerToolbar: Repair clicked")
        self.repair_clicked.emit()

    def _on_highlight_toggled(self, checked: bool) -> None:
        """Handle Highlight button toggle."""
        logger.debug(f"UIExplorerToolbar: Highlight toggled: {checked}")
        self.highlight_toggled.emit(checked)

    def _on_options(self) -> None:
        """Handle Options button click."""
        logger.debug("UIExplorerToolbar: Options clicked")
        self.options_clicked.emit()

    def _on_snapshot(self) -> None:
        """Handle Snapshot button click."""
        logger.debug("UIExplorerToolbar: Snapshot clicked")
        self._snapshot_btn.set_active_state()
        self.snapshot_clicked.emit()

    def _on_compare(self) -> None:
        """Handle Compare button click."""
        logger.debug("UIExplorerToolbar: Compare clicked")
        self.compare_clicked.emit()

    def _on_find_similar(self) -> None:
        """Handle Find Similar button click."""
        logger.debug("UIExplorerToolbar: Find Similar clicked")
        self._find_similar_btn.set_active_state()
        self.find_similar_clicked.emit()

    def _on_ai_suggest(self) -> None:
        """Handle Smart Suggest button click."""
        logger.debug("UIExplorerToolbar: Smart Suggest clicked")
        self.ai_suggest_clicked.emit()

    # =========================================================================
    # Public API
    # =========================================================================

    def set_validate_result(self, success: bool) -> None:
        """
        Update validate button to show result.

        Args:
            success: True for success (green), False for error (red)
        """
        if success:
            self._validate_btn.set_success_state()
        else:
            self._validate_btn.set_error_state()

    def reset_validate_button(self) -> None:
        """Reset validate button to default state."""
        self._validate_btn.reset_state()

    def set_picking_active(self, element: bool = False, anchor: bool = False) -> None:
        """
        Update picking button states.

        Args:
            element: True if element picking is active
            anchor: True if anchor picking is active
        """
        if element:
            self._indicate_element_btn.set_active_state()
        else:
            self._indicate_element_btn.reset_state()

        if anchor:
            self._indicate_anchor_btn.set_active_state()
        else:
            self._indicate_anchor_btn.reset_state()

    def set_repair_enabled(self, enabled: bool) -> None:
        """Enable or disable the repair button."""
        self._repair_btn.setEnabled(enabled)

    def set_highlight_checked(self, checked: bool) -> None:
        """Set the highlight button checked state without emitting signal."""
        self._highlight_btn.blockSignals(True)
        self._highlight_btn.setChecked(checked)
        self._highlight_btn.blockSignals(False)

    def set_snapshot_enabled(self, enabled: bool) -> None:
        """Enable or disable the snapshot button."""
        self._snapshot_btn.setEnabled(enabled)

    def set_compare_enabled(self, enabled: bool) -> None:
        """Enable or disable the compare button."""
        self._compare_btn.setEnabled(enabled)

    def reset_snapshot_button(self) -> None:
        """Reset snapshot button to default state."""
        self._snapshot_btn.reset_state()

    def set_snapshot_success(self) -> None:
        """Set snapshot button to success state."""
        self._snapshot_btn.set_success_state()

    def set_find_similar_enabled(self, enabled: bool) -> None:
        """Enable or disable the find similar button."""
        self._find_similar_btn.setEnabled(enabled)

    def reset_find_similar_button(self) -> None:
        """Reset find similar button to default state."""
        self._find_similar_btn.reset_state()

    def set_ai_suggest_enabled(self, enabled: bool) -> None:
        """Enable or disable the AI suggest button."""
        self._ai_suggest_btn.setEnabled(enabled)
