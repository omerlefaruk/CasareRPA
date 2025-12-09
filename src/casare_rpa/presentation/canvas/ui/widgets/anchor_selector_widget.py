"""
Anchor-Aware Selector Input Widget.

A compound widget that combines element selector with anchor configuration.
Used in the properties panel for selector properties.

Features:
- Main selector input with element picker button
- Collapsible anchor section
- Anchor preview with position dropdown
- Clear anchor button
"""

from typing import Optional, Any, Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QLabel,
    QComboBox,
    QCheckBox,
    QFrame,
    QSizePolicy,
)

from loguru import logger

from casare_rpa.nodes.browser.anchor_config import NodeAnchorConfig
from casare_rpa.presentation.canvas.ui.theme import THEME


class AnchorSelectorWidget(QWidget):
    """
    Compound widget for selector input with anchor configuration.

    Signals:
        selector_changed: Emitted when the selector value changes
        anchor_config_changed: Emitted when anchor config changes (JSON string)
    """

    selector_changed = Signal(str)
    anchor_config_changed = Signal(str)

    def __init__(
        self,
        initial_selector: str = "",
        initial_anchor_config: str = "",
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the anchor selector widget.

        Args:
            initial_selector: Initial selector value
            initial_anchor_config: Initial anchor config JSON
            parent: Parent widget
        """
        super().__init__(parent)

        self._target_node = None
        self._property_name = "selector"
        self._browser_page = None
        self._anchor_config = NodeAnchorConfig.from_json(initial_anchor_config)

        self._setup_ui(initial_selector)

    def _setup_ui(self, initial_selector: str) -> None:
        """Build the widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # -----------------------------------------------------------------
        # Main selector row
        # -----------------------------------------------------------------
        selector_row = QHBoxLayout()
        selector_row.setSpacing(2)

        # Selector input
        self._selector_edit = QLineEdit()
        self._selector_edit.setText(initial_selector)
        self._selector_edit.setPlaceholderText("Enter selector or click picker...")
        self._selector_edit.textChanged.connect(self._on_selector_changed)
        self._selector_edit.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: 3px;
                color: {THEME.selector_text};
                padding: 4px;
                font-family: Consolas, monospace;
            }}
            QLineEdit:focus {{
                border: 1px solid {THEME.accent};
            }}
        """)
        selector_row.addWidget(self._selector_edit, 1)

        # Element picker button
        self._picker_btn = QToolButton()
        self._picker_btn.setText("...")
        self._picker_btn.setToolTip("Open Element Selector")
        self._picker_btn.setFixedSize(24, 24)
        self._picker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._picker_btn.clicked.connect(self._on_picker_clicked)
        self._picker_btn.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.accent};
                border: 1px solid {THEME.accent_dark};
                border-radius: 3px;
                color: white;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background: {THEME.accent_dark};
            }}
            QToolButton:pressed {{
                background: {THEME.accent_darker};
            }}
        """)
        selector_row.addWidget(self._picker_btn)

        layout.addLayout(selector_row)

        # -----------------------------------------------------------------
        # Anchor section (collapsible)
        # -----------------------------------------------------------------
        self._anchor_frame = QFrame()
        self._anchor_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        self._anchor_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME.bg_darker};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        anchor_layout = QVBoxLayout(self._anchor_frame)
        anchor_layout.setContentsMargins(6, 4, 6, 4)
        anchor_layout.setSpacing(4)

        # Anchor checkbox row
        anchor_header = QHBoxLayout()

        self._anchor_checkbox = QCheckBox("Use anchor for reliability")
        self._anchor_checkbox.setChecked(self._anchor_config.enabled)
        self._anchor_checkbox.toggled.connect(self._on_anchor_toggled)
        self._anchor_checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME.text_secondary};
                font-size: 11px;
            }}
            QCheckBox:checked {{
                color: {THEME.selector_text};
            }}
        """)
        anchor_header.addWidget(self._anchor_checkbox)
        anchor_header.addStretch()

        # Pick anchor button
        self._pick_anchor_btn = QToolButton()
        self._pick_anchor_btn.setText("Pick")
        self._pick_anchor_btn.setToolTip("Pick anchor element")
        self._pick_anchor_btn.setFixedHeight(20)
        self._pick_anchor_btn.clicked.connect(self._on_pick_anchor_clicked)
        self._pick_anchor_btn.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.button_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 2px;
                color: {THEME.text_primary};
                padding: 2px 8px;
                font-size: 10px;
            }}
            QToolButton:hover {{
                background: {THEME.button_hover};
            }}
        """)
        anchor_header.addWidget(self._pick_anchor_btn)

        # Clear anchor button
        self._clear_anchor_btn = QToolButton()
        self._clear_anchor_btn.setText("Clear")
        self._clear_anchor_btn.setToolTip("Clear anchor")
        self._clear_anchor_btn.setFixedHeight(20)
        self._clear_anchor_btn.clicked.connect(self._on_clear_anchor)
        self._clear_anchor_btn.setStyleSheet(f"""
            QToolButton {{
                background: {THEME.button_bg};
                border: 1px solid {THEME.border_light};
                border-radius: 2px;
                color: {THEME.text_primary};
                padding: 2px 8px;
                font-size: 10px;
            }}
            QToolButton:hover {{
                background: {THEME.button_hover};
            }}
        """)
        anchor_header.addWidget(self._clear_anchor_btn)

        anchor_layout.addLayout(anchor_header)

        # Anchor details row (only visible when anchor is set)
        self._anchor_details = QWidget()
        details_layout = QHBoxLayout(self._anchor_details)
        details_layout.setContentsMargins(0, 2, 0, 0)
        details_layout.setSpacing(4)

        # Position dropdown
        pos_label = QLabel("Position:")
        pos_label.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 10px;")
        details_layout.addWidget(pos_label)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["left", "right", "above", "below", "near"])
        self._position_combo.setCurrentText(self._anchor_config.position)
        self._position_combo.currentTextChanged.connect(self._on_position_changed)
        self._position_combo.setFixedHeight(20)
        self._position_combo.setStyleSheet(f"""
            QComboBox {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: 2px;
                color: {THEME.text_primary};
                padding: 2px;
                font-size: 10px;
            }}
        """)
        details_layout.addWidget(self._position_combo)

        # Anchor preview label
        self._anchor_preview = QLabel()
        self._anchor_preview.setStyleSheet(f"""
            color: {THEME.selector_text};
            font-size: 10px;
            font-family: Consolas, monospace;
        """)
        self._anchor_preview.setWordWrap(True)
        details_layout.addWidget(self._anchor_preview, 1)

        anchor_layout.addWidget(self._anchor_details)

        layout.addWidget(self._anchor_frame)

        # Update visibility
        self._update_anchor_visibility()

    def _on_selector_changed(self, text: str) -> None:
        """Handle selector text change."""
        self.selector_changed.emit(text)

    def _on_anchor_toggled(self, checked: bool) -> None:
        """Handle anchor checkbox toggle."""
        self._anchor_config.enabled = checked
        self._update_anchor_visibility()
        self._emit_anchor_config()

    def _on_position_changed(self, position: str) -> None:
        """Handle position dropdown change."""
        self._anchor_config.position = position
        self._emit_anchor_config()

    def _on_picker_clicked(self) -> None:
        """Handle main element picker button click."""
        self._open_element_selector_dialog(pick_anchor=False)

    def _on_pick_anchor_clicked(self) -> None:
        """Handle pick anchor button click."""
        self._open_element_selector_dialog(pick_anchor=True)

    def _on_clear_anchor(self) -> None:
        """Clear anchor configuration."""
        self._anchor_config = NodeAnchorConfig()
        self._anchor_checkbox.setChecked(False)
        self._update_anchor_visibility()
        self._emit_anchor_config()

    def _open_element_selector_dialog(self, pick_anchor: bool = False) -> None:
        """
        Open the element selector dialog.

        Args:
            pick_anchor: If True, start in anchor picking mode
        """
        try:
            from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
                ElementSelectorDialog,
            )

            mode = "browser" if self._browser_page else "desktop"

            dialog = ElementSelectorDialog(
                parent=self.window(),
                mode=mode,
                browser_page=self._browser_page,
                initial_selector=self._selector_edit.text(),
                target_node=self._target_node,
                property_name=self._property_name,
            )

            # Connect signals
            dialog.selector_confirmed.connect(
                lambda result: self._on_dialog_result(result, pick_anchor)
            )

            # If pick_anchor, automatically click the anchor button after dialog opens
            if pick_anchor:
                # This would need the dialog to support starting in anchor mode
                # For now, user picks anchor manually in dialog
                pass

            dialog.exec()

        except ImportError as e:
            logger.warning(f"ElementSelectorDialog not available: {e}")
        except Exception as e:
            logger.error(f"Failed to open element selector: {e}")

    def _on_dialog_result(self, result, was_picking_anchor: bool) -> None:
        """
        Handle result from element selector dialog.

        Args:
            result: SelectorResult object
            was_picking_anchor: True if we were picking an anchor
        """
        if not result:
            return

        if was_picking_anchor:
            # Store as anchor
            if hasattr(result, "selector_value"):
                self._anchor_config.enabled = True
                self._anchor_config.selector = result.selector_value
                self._anchor_config.text = getattr(result, "text_content", "")
                self._anchor_config.tag_name = getattr(result, "tag_name", "")

                # Check if result has anchor data
                if hasattr(result, "anchor") and result.anchor:
                    anchor_data = result.anchor
                    if hasattr(anchor_data, "selector"):
                        self._anchor_config.selector = anchor_data.selector
                    if hasattr(anchor_data, "position"):
                        self._anchor_config.position = anchor_data.position
                    if hasattr(anchor_data, "text"):
                        self._anchor_config.text = anchor_data.text

                self._anchor_checkbox.setChecked(True)
                self._update_anchor_visibility()
                self._emit_anchor_config()
        else:
            # Store as main selector
            if hasattr(result, "selector_value"):
                self._selector_edit.setText(result.selector_value)

                # If result has anchor configuration, also set that
                if hasattr(result, "anchor") and result.anchor:
                    anchor_data = result.anchor
                    if hasattr(anchor_data, "enabled") and anchor_data.enabled:
                        self._anchor_config.enabled = True
                        self._anchor_config.selector = getattr(
                            anchor_data, "selector", ""
                        )
                        self._anchor_config.position = getattr(
                            anchor_data, "position", "near"
                        )
                        self._anchor_config.text = getattr(anchor_data, "text", "")
                        self._anchor_config.tag_name = getattr(
                            anchor_data, "tag_name", ""
                        )
                        self._anchor_checkbox.setChecked(True)
                        self._update_anchor_visibility()
                        self._emit_anchor_config()

    def _update_anchor_visibility(self) -> None:
        """Update visibility of anchor details based on state."""
        has_anchor = bool(self._anchor_config.selector)
        self._anchor_details.setVisible(has_anchor)
        self._clear_anchor_btn.setEnabled(has_anchor)

        if has_anchor:
            preview_text = self._anchor_config.display_text
            self._anchor_preview.setText(preview_text)
            self._position_combo.setCurrentText(self._anchor_config.position)

    def _emit_anchor_config(self) -> None:
        """Emit anchor config changed signal."""
        json_str = self._anchor_config.to_json() if self._anchor_config.is_valid else ""
        self.anchor_config_changed.emit(json_str)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_selector(self, value: str) -> None:
        """Set the selector value."""
        self._selector_edit.setText(value)

    def get_selector(self) -> str:
        """Get the selector value."""
        return self._selector_edit.text()

    def set_anchor_config(self, json_str: str) -> None:
        """Set anchor configuration from JSON string."""
        self._anchor_config = NodeAnchorConfig.from_json(json_str)
        self._anchor_checkbox.setChecked(self._anchor_config.enabled)
        self._update_anchor_visibility()

    def get_anchor_config(self) -> str:
        """Get anchor configuration as JSON string."""
        return self._anchor_config.to_json() if self._anchor_config.is_valid else ""

    def set_target_node(self, node: Any, property_name: str = "selector") -> None:
        """
        Set the target node for context.

        Args:
            node: The visual node instance
            property_name: The property name being edited
        """
        self._target_node = node
        self._property_name = property_name

    def set_browser_page(self, page: Any) -> None:
        """
        Set the browser page for browser-mode operations.

        Args:
            page: Playwright Page instance
        """
        self._browser_page = page

    # Aliases for compatibility with SelectorInputWidget
    def text(self) -> str:
        """Get selector text (alias for get_selector)."""
        return self.get_selector()

    def setText(self, text: str) -> None:
        """Set selector text (alias for set_selector)."""
        self.set_selector(text)

    def get_value(self) -> str:
        """Get selector value (alias for get_selector)."""
        return self.get_selector()

    def set_value(self, value: str) -> None:
        """Set selector value (alias for set_selector)."""
        self.set_selector(value)
