"""
Selector Input Widget.

A QLineEdit with a UI Explorer button for selector properties.
Used in the properties panel for selector/xpath inputs.

Now supports both UIExplorerDialog (full) and ElementSelectorDialog (simplified).
"""

from typing import Optional, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QMenu,
)

from loguru import logger


# Properties that should show the selector explorer button
SELECTOR_PROPERTY_NAMES = {
    "selector",
    "xpath",
    "css_selector",
    "css",
    "target_selector",
    "element_selector",
    "wait_selector",
    "anchor_selector",
    "parent_selector",
    "container_selector",
    "locator",
}


def is_selector_property(name: str) -> bool:
    """
    Check if a property name is a selector-type property.

    Args:
        name: Property name

    Returns:
        True if this is a selector property that should show the explorer button
    """
    lower_name = name.lower()

    # Direct match
    if lower_name in SELECTOR_PROPERTY_NAMES:
        return True

    # Suffix match (e.g., "close_button_selector")
    for selector_name in SELECTOR_PROPERTY_NAMES:
        if lower_name.endswith(f"_{selector_name}"):
            return True

    return False


class SelectorInputWidget(QWidget):
    """
    A line edit with an attached UI Explorer button.

    Used for selector/xpath property inputs in the properties panel.
    When the button is clicked, opens either:
    - ElementSelectorDialog (default, simplified picker)
    - UIExplorerDialog (advanced, right-click menu)

    Signals:
        value_changed: Emitted when the selector value changes
        explorer_requested: Emitted when the explorer button is clicked
    """

    value_changed = Signal(str)
    explorer_requested = Signal()

    def __init__(
        self,
        initial_value: str = "",
        parent: Optional[QWidget] = None,
        use_new_dialog: bool = True,
    ) -> None:
        """
        Initialize the selector input widget.

        Args:
            initial_value: Initial selector value
            parent: Parent widget
            use_new_dialog: If True, use new ElementSelectorDialog by default
        """
        super().__init__(parent)

        self._target_node = None
        self._property_name = ""
        self._browser_page = None
        self._use_new_dialog = use_new_dialog

        self._setup_ui(initial_value)

    def _setup_ui(self, initial_value: str) -> None:
        """Build the widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Line edit for selector value
        self._line_edit = QLineEdit()
        self._line_edit.setText(initial_value)
        self._line_edit.setPlaceholderText("Enter selector or click icon...")
        self._line_edit.textChanged.connect(self._on_text_changed)
        self._line_edit.setStyleSheet("""
            QLineEdit {
                background: #3d3d3d;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
                color: #60a5fa;
                padding: 4px;
                font-family: Consolas, monospace;
            }
            QLineEdit:focus {
                border: 1px solid #3b82f6;
            }
        """)
        layout.addWidget(self._line_edit, 1)

        # UI Explorer button
        self._explorer_btn = QToolButton()
        self._explorer_btn.setText("...")
        self._explorer_btn.setToolTip(
            "Click: Element Picker | Right-click: Advanced UI Explorer"
        )
        self._explorer_btn.setFixedSize(24, 24)
        self._explorer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._explorer_btn.clicked.connect(self._on_explorer_clicked)
        self._explorer_btn.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._explorer_btn.customContextMenuRequested.connect(self._on_context_menu)
        self._explorer_btn.setStyleSheet("""
            QToolButton {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 3px;
                color: white;
                font-weight: bold;
            }
            QToolButton:hover {
                background: #2563eb;
            }
            QToolButton:pressed {
                background: #1d4ed8;
            }
        """)
        layout.addWidget(self._explorer_btn)

    def _on_text_changed(self, text: str) -> None:
        """Handle text change."""
        self.value_changed.emit(text)

    def _on_explorer_clicked(self) -> None:
        """Handle explorer button click."""
        try:
            logger.debug(
                f"SelectorInputWidget: Explorer requested for {self._property_name}"
            )
            self.explorer_requested.emit()

            # Open appropriate dialog based on setting
            if self._use_new_dialog:
                self._open_element_selector_dialog()
            else:
                self._open_ui_explorer()
        except Exception as e:
            logger.error(f"SelectorInputWidget: Failed to open explorer: {e}")

    def _on_context_menu(self, pos) -> None:
        """Show context menu with dialog options."""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                color: #e0e0e0;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background: #3b82f6;
            }
        """)

        # Quick picker action
        picker_action = menu.addAction("Element Picker (Simple)")
        picker_action.triggered.connect(self._open_element_selector_dialog)

        # Advanced explorer action
        explorer_action = menu.addAction("UI Explorer (Advanced)")
        explorer_action.triggered.connect(self._open_ui_explorer)

        menu.exec(self._explorer_btn.mapToGlobal(pos))

    def _open_element_selector_dialog(self) -> None:
        """Open the new ElementSelectorDialog."""
        try:
            from casare_rpa.presentation.canvas.selectors.element_selector_dialog import (
                ElementSelectorDialog,
            )

            # Determine mode from browser page availability
            mode = "browser" if self._browser_page else "desktop"

            # Create dialog
            dialog = ElementSelectorDialog(
                parent=self.window(),
                mode=mode,
                browser_page=self._browser_page,
                initial_selector=self._line_edit.text(),
                target_node=self._target_node,
                property_name=self._property_name,
            )

            # Connect selector confirmed signal
            dialog.selector_confirmed.connect(self._on_selector_result_confirmed)

            # Show dialog
            dialog.exec()

        except ImportError as e:
            logger.warning(f"ElementSelectorDialog not available: {e}")
            # Fall back to UI Explorer
            self._open_ui_explorer()
        except Exception as e:
            logger.error(f"SelectorInputWidget: Failed to open Element Selector: {e}")

    def _open_ui_explorer(self) -> None:
        """Open the full UI Explorer dialog."""
        try:
            from casare_rpa.presentation.canvas.selectors.ui_explorer import (
                UIExplorerDialog,
            )

            # Determine mode from browser page availability
            mode = "browser" if self._browser_page else "desktop"

            # Create dialog
            dialog = UIExplorerDialog(
                parent=self.window(),
                mode=mode,
                browser_page=self._browser_page,
            )

            # Connect selector confirmed signal
            dialog.selector_confirmed.connect(self._on_selector_confirmed)

            # Show dialog
            dialog.exec()
        except ImportError as e:
            logger.error(f"SelectorInputWidget: UIExplorerDialog not available: {e}")
        except Exception as e:
            logger.error(f"SelectorInputWidget: Failed to open UI Explorer: {e}")

    def _on_selector_confirmed(self, selector: str) -> None:
        """
        Handle selector confirmed from UI Explorer.

        Args:
            selector: The confirmed selector string
        """
        if selector:
            self._line_edit.setText(selector)
            logger.debug(f"SelectorInputWidget: Selector set: {selector[:50]}...")

    def _on_selector_result_confirmed(self, result) -> None:
        """
        Handle SelectorResult confirmed from ElementSelectorDialog.

        Args:
            result: SelectorResult object with selector_value and metadata
        """
        if result and hasattr(result, "selector_value"):
            self._line_edit.setText(result.selector_value)
            logger.debug(
                f"SelectorInputWidget: Selector set from result: "
                f"{result.selector_value[:50]}... (unique={result.is_unique})"
            )

            # Also save anchor config to target node if present
            self._save_anchor_config_to_node(result)

    def _save_anchor_config_to_node(self, result) -> None:
        """
        Save anchor configuration to target node if available.

        Args:
            result: SelectorResult object that may contain anchor data
        """
        if not self._target_node:
            return

        try:
            # Check if result has anchor data
            anchor_config = None

            if hasattr(result, "anchor") and result.anchor:
                # SelectorResult.anchor is AnchorData object
                # Presence of anchor means it's enabled (no explicit "enabled" field)
                anchor_data = result.anchor
                from casare_rpa.nodes.browser.anchor_config import NodeAnchorConfig

                config = NodeAnchorConfig(
                    enabled=True,
                    selector=getattr(anchor_data, "selector", ""),
                    position=getattr(anchor_data, "position", "near"),
                    text=getattr(
                        anchor_data, "text_content", ""
                    ),  # AnchorData uses text_content
                    tag_name=getattr(anchor_data, "tag_name", ""),
                    stability_score=getattr(anchor_data, "stability_score", 0.0),
                    offset_x=getattr(anchor_data, "offset_x", 0),
                    offset_y=getattr(anchor_data, "offset_y", 0),
                )
                anchor_config = config.to_json()

            # If we have anchor config, save it to node
            if anchor_config:
                # Try to set anchor_config property on node
                if hasattr(self._target_node, "set_property"):
                    self._target_node.set_property("anchor_config", anchor_config)
                    logger.info(
                        f"SelectorInputWidget: Saved anchor config to node: "
                        f"{anchor_config[:50]}..."
                    )
                elif hasattr(self._target_node, "model") and hasattr(
                    self._target_node.model, "set_property"
                ):
                    self._target_node.model.set_property("anchor_config", anchor_config)
                    logger.info(
                        f"SelectorInputWidget: Saved anchor config via model: "
                        f"{anchor_config[:50]}..."
                    )

        except Exception as e:
            logger.warning(f"SelectorInputWidget: Failed to save anchor config: {e}")

    # =========================================================================
    # Public API
    # =========================================================================

    def set_value(self, value: str) -> None:
        """Set the selector value."""
        self._line_edit.setText(value)

    def get_value(self) -> str:
        """Get the selector value."""
        return self._line_edit.text()

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

    def text(self) -> str:
        """Get the text (alias for get_value)."""
        return self.get_value()

    def setText(self, text: str) -> None:
        """Set the text (alias for set_value)."""
        self.set_value(text)
