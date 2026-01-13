"""
UI Explorer Dialog.

UiPath-style UI Explorer window for deep element inspection and selector building.
Features:
- 4-panel horizontal splitter layout
- Visual tree navigation (left)
- Selector attribute editor (center-left)
- Selected attributes summary (center-right)
- Property explorer (right)
- Selector preview panel (bottom) with syntax highlighting
- Save/Cancel buttons
- Status bar with element info

Complements UnifiedSelectorDialog with advanced inspection capabilities.
"""

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.element_model import (
    UIExplorerElement,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import SelectorModel
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.property_explorer_panel import (
    PropertyExplorerPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selected_attrs_panel import (
    SelectedAttributesPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selector_editor_panel import (
    SelectorEditorPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.selector_preview_panel import (
    SelectorPreviewPanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.panels.visual_tree_panel import (
    VisualTreePanel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.toolbar import UIExplorerToolbar
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.status_bar_widget import (
    UIExplorerStatusBar,
)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.design_tokens import Radius
from casare_rpa.presentation.canvas.theme_system.helpers import set_margins, set_spacing

if TYPE_CHECKING:
    from playwright.async_api import Page


class UIExplorerDialog(QDialog):
    """
    UI Explorer Dialog - UiPath-style element inspector.

    Main window for deep element inspection and selector building.
    Features:
    - 4-panel horizontal splitter (25%/35%/15%/25%)
    - Fixed toolbar at top (48px)
    - Fixed preview panel at bottom (80px)
    - Fixed status bar (24px)

    Layout:
    +-----------------------------------------------------------------------------------+
    | UIExplorerToolbar (fixed height 48px)                                             |
    +---------------+---------------------------+---------------------+-----------------+
    | Visual Tree   | Selector Editor           | Selected Attrs      | Property        |
    | (25%)         | (35%)                     | (15%)               | Explorer (25%)  |
    +---------------+---------------------------+---------------------+-----------------+
    | Selector Preview (fixed height 80px)                                              |
    +-----------------------------------------------------------------------------------+
    | Status Bar (fixed height 24px)                                                    |
    +-----------------------------------------------------------------------------------+

    Signals:
        element_selected: Emitted when user selects an element (dict: element_data)
        selector_confirmed: Emitted when user confirms selector (str: selector)
    """

    element_selected = Signal(dict)
    selector_confirmed = Signal(str)

    # Panel minimum widths
    MIN_VISUAL_TREE_WIDTH = 200
    MIN_SELECTOR_EDITOR_WIDTH = 250
    MIN_SELECTED_ATTRS_WIDTH = 120
    MIN_PROPERTY_EXPLORER_WIDTH = 200

    def __init__(
        self,
        parent: QWidget | None = None,
        mode: str = "browser",
        browser_page: Optional["Page"] = None,
        initial_element: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the UI Explorer dialog.

        Args:
            parent: Parent widget
            mode: "browser" or "desktop"
            browser_page: Playwright page for browser mode
            initial_element: Optional element to start with
        """
        super().__init__(parent)

        self._mode = mode
        self._browser_page = browser_page
        self._initial_element = initial_element
        self._current_element: dict[str, Any] | None = None
        self._current_selector: str = ""
        self._anchor_data: dict[str, Any] | None = None
        self._anchor_selector: str = ""

        # Create selector model for state management
        self._selector_model = SelectorModel()

        # Selector manager for browser operations (lazy init)
        self._selector_manager = None

        # Options state
        self._options = {
            "show_hidden_elements": False,
            "include_computed_properties": True,
            "auto_expand_tree": True,
        }

        # Picking state
        self._is_picking_element = False
        self._is_picking_anchor = False
        self._highlight_active = False
        self._desktop_picker = None  # ElementPickerOverlay instance for desktop mode

        # Snapshot state for visual diff
        self._snapshot_data: dict[str, Any] | None = None

        # Track pending async tasks for cleanup
        self._pending_tasks: list = []

        self.setWindowTitle("UI Explorer")
        self.setMinimumSize(TOKENS.sizes.dialog_lg, TOKENS.sizes.dialog_lg)
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()
        self._apply_styles()

        logger.info(f"UIExplorerDialog initialized (mode={mode})")

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar (fixed height)
        self._toolbar = UIExplorerToolbar()
        layout.addWidget(self._toolbar)

        # Main content area with splitter
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setHandleWidth(TOKENS.spacing.xs)
        self._main_splitter.setChildrenCollapsible(False)

        # Panel 1: Visual Tree (25%)
        self._visual_tree_panel = VisualTreePanel()
        self._visual_tree_panel.setMinimumWidth(self.MIN_VISUAL_TREE_WIDTH)
        self._visual_tree_panel.set_mode(self._mode)
        self._main_splitter.addWidget(self._visual_tree_panel)

        # Panel 2: Selector Editor (35%)
        self._selector_editor_panel = SelectorEditorPanel(model=self._selector_model)
        self._selector_editor_panel.setMinimumWidth(self.MIN_SELECTOR_EDITOR_WIDTH)
        self._main_splitter.addWidget(self._selector_editor_panel)

        # Panel 3: Selected Attributes (15%)
        self._selected_attrs_panel = SelectedAttributesPanel(model=self._selector_model)
        self._selected_attrs_panel.setMinimumWidth(self.MIN_SELECTED_ATTRS_WIDTH)
        self._main_splitter.addWidget(self._selected_attrs_panel)

        # Panel 4: Property Explorer (25%)
        self._property_explorer_panel = PropertyExplorerPanel()
        self._property_explorer_panel.setMinimumWidth(self.MIN_PROPERTY_EXPLORER_WIDTH)
        self._main_splitter.addWidget(self._property_explorer_panel)

        # Set initial splitter sizes (25% / 35% / 15% / 25%)
        total_width = TOKENS.sizes.dialog_lg  # Initial width
        self._main_splitter.setSizes(
            [
                int(total_width * 0.25),
                int(total_width * 0.35),
                int(total_width * 0.15),
                int(total_width * 0.25),
            ]
        )

        layout.addWidget(self._main_splitter, 1)  # Stretch factor 1

        # Preview panel (fixed height) with syntax highlighting
        self._preview_panel = SelectorPreviewPanel()
        self._preview_panel.set_selector_model(self._selector_model)
        layout.addWidget(self._preview_panel)

        # Button row: Save/Cancel
        button_row = QHBoxLayout()
        set_margins(
            button_row, TOKENS.spacing.md, TOKENS.spacing.md, TOKENS.spacing.md, TOKENS.spacing.md
        )
        set_spacing(button_row, TOKENS.spacing.md)

        button_row.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedSize(80 * 5, TOKENS.sizes.button_lg)
        self._cancel_btn.setToolTip("Close without saving (Escape)")
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_dark};
                border: 1px solid {THEME.border};
                border-radius: {Radius.sm}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME.bg_medium};
                border-color: {THEME.border_light};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_darkest};
            }}
        """)
        button_row.addWidget(self._cancel_btn)

        # Save button
        self._save_btn = QPushButton("Save Selector")
        self._save_btn.setFixedSize(80 * 6, TOKENS.sizes.button_lg)
        self._save_btn.setToolTip("Save selector and close (Enter)")
        self._save_btn.setEnabled(False)  # Disabled until selector is ready
        self._save_btn.setStyleSheet(f"""
            QPushButton {{
                background: #3b82f6;
                border: 1px solid #60a5fa;
                border-radius: {TOKENS.radius.sm}px;
                color: white;
                font-size: {TOKENS.typography.body}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: #2563eb;
                border-color: #3b82f6;
            }}
            QPushButton:pressed {{
                background: #1d4ed8;
            }}
            QPushButton:disabled {{
                background: #374151;
                border-color: #4b5563;
                color: #6b7280;
            }}
        """)
        button_row.addWidget(self._save_btn)

        layout.addLayout(button_row)

        # Enhanced status bar
        self._status_bar = UIExplorerStatusBar()
        self._status_bar.set_mode(self._mode)

        layout.addWidget(self._status_bar)

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # F5: Refresh tree
        refresh_shortcut = QShortcut(QKeySequence("F5"), self)
        refresh_shortcut.activated.connect(self._on_refresh)

        # Ctrl+E: Start element picking
        element_shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        element_shortcut.activated.connect(self._on_indicate_element)

        # Ctrl+A: Start anchor picking
        anchor_shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        anchor_shortcut.activated.connect(self._on_indicate_anchor)

        # Ctrl+Shift+A: Clear anchor
        clear_anchor_shortcut = QShortcut(QKeySequence("Ctrl+Shift+A"), self)
        clear_anchor_shortcut.activated.connect(self._clear_anchor)

        # Ctrl+H: Toggle highlight
        highlight_shortcut = QShortcut(QKeySequence("Ctrl+H"), self)
        highlight_shortcut.activated.connect(self._on_toggle_highlight)

        # Ctrl+V: Validate selector
        validate_shortcut = QShortcut(QKeySequence("Ctrl+Shift+V"), self)
        validate_shortcut.activated.connect(self._on_validate)

        # Ctrl+C: Copy selector
        copy_shortcut = QShortcut(QKeySequence("Ctrl+C"), self)
        copy_shortcut.activated.connect(self._on_copy_selector)

        # Escape: Cancel/close
        escape_shortcut = QShortcut(QKeySequence("Escape"), self)
        escape_shortcut.activated.connect(self._on_escape)

        # Enter: Save and close (when selector is ready)
        enter_shortcut = QShortcut(QKeySequence("Return"), self)
        enter_shortcut.activated.connect(self._on_save)

    def _connect_signals(self) -> None:
        """Connect toolbar and panel signals to handlers."""
        # Toolbar signals
        self._toolbar.validate_clicked.connect(self._on_validate)
        self._toolbar.indicate_element_clicked.connect(self._on_indicate_element)
        self._toolbar.indicate_anchor_clicked.connect(self._on_indicate_anchor)
        self._toolbar.repair_clicked.connect(self._on_repair)
        self._toolbar.highlight_toggled.connect(self._on_highlight_changed)
        self._toolbar.options_clicked.connect(self._on_options)
        self._toolbar.snapshot_clicked.connect(self._on_snapshot)
        self._toolbar.compare_clicked.connect(self._on_compare)
        self._toolbar.find_similar_clicked.connect(self._on_find_similar)
        self._toolbar.ai_suggest_clicked.connect(self._on_ai_suggest)

        # Visual tree panel signals
        self._visual_tree_panel.element_selected.connect(self._on_tree_element_selected)
        self._visual_tree_panel.element_double_clicked.connect(self._on_tree_element_double_clicked)

        # Selector model signals
        self._selector_model.preview_updated.connect(self._on_preview_updated)
        self._selector_model.attribute_toggled.connect(self._on_attribute_toggled)

        # Property explorer signals
        self._property_explorer_panel.property_copied.connect(self._on_property_copied)

        # Preview panel signals
        self._preview_panel.copy_clicked.connect(self._on_preview_copy)
        self._preview_panel.format_changed.connect(self._on_format_changed)
        self._preview_panel.selector_changed.connect(self._on_selector_manually_changed)

        # Save/Cancel buttons
        self._save_btn.clicked.connect(self._on_save)
        self._cancel_btn.clicked.connect(self._on_cancel)

    def _apply_styles(self) -> None:
        """Apply dialog styling."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_panel};
                color: {THEME.text_primary};
            }}
            QSplitter::handle {{
                background: {THEME.border};
            }}
            QSplitter::handle:hover {{
                background: {THEME.border_light};
            }}
            QStatusBar {{
                background: {THEME.bg_darkest};
                border-top: 1px solid {THEME.border};
            }}
        """)

    # =========================================================================
    # Selector Manager Initialization
    # =========================================================================

    def _init_selector_manager(self) -> None:
        """Initialize selector manager if browser page is available."""
        if not self._browser_page:
            return

        if self._selector_manager is not None:
            return

        try:
            from casare_rpa.utils.selectors.selector_manager import SelectorManager

            self._selector_manager = SelectorManager()
            logger.info("UIExplorer: Created SelectorManager instance")
        except Exception as e:
            logger.error(f"UIExplorer: Failed to init selector manager: {e}")

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_refresh(self) -> None:
        """Handle refresh (F5)."""
        try:
            logger.debug("UIExplorer: Refresh requested")
            self._status_bar.set_status_message("Refreshing tree...", "info")

            if self._mode == "browser" and self._browser_page:
                # Refresh browser tree
                self._schedule_task(self._refresh_browser_tree())
            elif self._mode == "desktop":
                # Refresh desktop tree
                self._refresh_desktop_tree()
            else:
                self._status_bar.set_status_message("No page to refresh", "warning")
        except Exception as e:
            logger.error(f"UIExplorer: Refresh failed: {e}")
            self._status_bar.set_status_message(f"Refresh failed: {e}", "error")

    async def _refresh_browser_tree(self) -> None:
        """Refresh browser element tree."""
        try:
            if not self._browser_page:
                self._status_bar.set_status_message("No browser page", "warning")
                return

            self._init_selector_manager()

            if self._selector_manager:
                await self._selector_manager.inject_into_page(self._browser_page)
                self._status_bar.set_status_message("Tree refreshed", "success")
            else:
                self._status_bar.set_status_message("Selector manager unavailable", "warning")
        except Exception as e:
            logger.error(f"UIExplorer: Browser tree refresh failed: {e}")
            self._status_bar.set_status_message(f"Refresh failed: {e}", "error")

    def _refresh_desktop_tree(self) -> None:
        """Refresh desktop element tree."""
        try:
            self._status_bar.set_status_message("Desktop tree refresh not yet implemented", "info")
        except Exception as e:
            logger.error(f"UIExplorer: Desktop tree refresh failed: {e}")
            self._status_bar.set_status_message(f"Refresh failed: {e}", "error")

    def _on_indicate_element(self) -> None:
        """Handle indicate element."""
        try:
            logger.debug("UIExplorer: Indicate element requested")

            if self._mode == "browser" and not self._browser_page:
                self._status_bar.set_status_message(
                    "No browser page - open a browser first", "warning"
                )
                return

            self._is_picking_element = True
            self._is_picking_anchor = False
            self._toolbar.set_picking_active(element=True, anchor=False)
            self._status_bar.show_picking_active("element")

            if self._mode == "browser":
                self._schedule_task(self._start_browser_picking())
            else:
                self._start_desktop_picking()
        except Exception as e:
            logger.error(f"UIExplorer: Indicate element failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
            self._cancel_picking()

    async def _start_browser_picking(self) -> None:
        """Start browser element picking mode."""
        try:
            if not self._browser_page:
                self._status_bar.set_status_message("No browser page", "warning")
                self._cancel_picking()
                return

            self._init_selector_manager()

            if not self._selector_manager:
                self._status_bar.set_status_message("Selector manager unavailable", "warning")
                self._cancel_picking()
                return

            # Inject and activate
            await self._selector_manager.inject_into_page(self._browser_page)
            await self._selector_manager.activate_selector_mode(
                recording=False, on_element_selected=self._on_browser_element_picked
            )

            logger.info("UIExplorer: Browser picking mode started")
        except Exception as e:
            logger.error(f"UIExplorer: Failed to start browser picking: {e}")
            self._status_bar.set_status_message(f"Pick failed: {e}", "error")
            self._cancel_picking()

    def _start_desktop_picking(self) -> None:
        """Start desktop element picking mode using ElementPickerOverlay."""
        try:
            from casare_rpa.presentation.canvas.selectors.element_picker import (
                activate_element_picker,
            )

            self._status_bar.set_status_message(
                "Hover over elements and click to select • ESC to cancel", "info"
            )

            def on_element_selected(desktop_element):
                """Handle desktop element selection."""
                try:
                    is_anchor = self._is_picking_anchor
                    logger.info(
                        f"UIExplorer: Desktop {'anchor' if is_anchor else 'element'} picked"
                    )

                    # Build element data from DesktopElement
                    control_type = desktop_element.get_property("ControlTypeName") or "Unknown"
                    if control_type.endswith("Control"):
                        control_type = control_type[:-7]

                    name = desktop_element.get_property("Name") or ""
                    automation_id = desktop_element.get_property("AutomationId") or ""
                    class_name = desktop_element.get_property("ClassName") or ""

                    element_data = {
                        "tag_or_control": control_type,
                        "tag": control_type,
                        "element_id": automation_id,
                        "name": name[:50] if name else "",
                        "source": "desktop",
                        "attributes": {
                            "AutomationId": automation_id,
                            "Name": name,
                            "ControlType": control_type,
                            "ClassName": class_name,
                        },
                    }

                    # Build selector
                    selector = self._build_desktop_selector(desktop_element)

                    if is_anchor:
                        self._anchor_data = element_data
                        self._anchor_selector = selector
                        self._status_bar.set_status_message(
                            "Anchor set! Pick target (Ctrl+E) or clear anchor (Ctrl+Shift+A)",
                            "success",
                        )
                        self._status_bar.set_anchor_element(control_type, name)
                    else:
                        self._on_tree_element_selected(element_data)
                        self._current_selector = selector
                        self._status_bar.set_status_message(
                            f"Selected {control_type}: {name[:30] if name else automation_id[:30]}",
                            "success",
                        )

                except Exception as e:
                    logger.error(f"UIExplorer: Failed to process desktop element: {e}")
                    self._status_bar.set_status_message(f"Error: {e}", "error")
                finally:
                    self._cancel_picking()

            def on_cancelled():
                """Handle picker cancelled."""
                self._status_bar.set_status_message("Selection cancelled", "info")
                self._cancel_picking()

            # Hide the dialog temporarily so user can pick elements
            self.hide()

            # Activate the element picker
            self._desktop_picker = activate_element_picker(
                callback_on_select=on_element_selected, callback_on_cancel=on_cancelled
            )

        except ImportError as e:
            logger.error(f"UIExplorer: ElementPickerOverlay not available: {e}")
            self._status_bar.set_status_message("Desktop picker not available", "error")
            self._cancel_picking()
        except Exception as e:
            logger.error(f"UIExplorer: Failed to start desktop picking: {e}")
            self._status_bar.set_status_message(f"Pick failed: {e}", "error")
            self._cancel_picking()

    def _build_desktop_selector(self, desktop_element) -> str:
        """Build a UiPath-style selector from a desktop element."""
        control_type = desktop_element.get_property("ControlTypeName") or "Unknown"
        if control_type.endswith("Control"):
            control_type = control_type[:-7]

        attrs = [f"type='{control_type}'"]

        automation_id = desktop_element.get_property("AutomationId")
        if automation_id:
            attrs.append(f"AutomationId='{automation_id}'")

        name = desktop_element.get_property("Name")
        if name:
            # Escape single quotes in name
            name_escaped = name.replace("'", "&apos;")[:50]
            attrs.append(f"Name='{name_escaped}'")

        class_name = desktop_element.get_property("ClassName")
        if class_name:
            attrs.append(f"ClassName='{class_name}'")

        return f"<ctrl {' '.join(attrs)} />"

    def _on_browser_element_picked(self, fingerprint) -> None:
        """
        Handle element picked from browser.

        Args:
            fingerprint: Element fingerprint from selector manager
        """
        try:
            is_anchor = self._is_picking_anchor
            logger.info(
                f"UIExplorer: {'Anchor' if is_anchor else 'Element'} picked: {fingerprint.tag_name}"
            )

            # Build element data from fingerprint
            element_data = {
                "tag_or_control": fingerprint.tag_name,
                "tag": fingerprint.tag_name,
                "element_id": fingerprint.element_id or "",
                "name": fingerprint.text_content[:50] if fingerprint.text_content else "",
                "source": "browser",
                "attributes": {
                    "id": fingerprint.element_id or "",
                    "class": " ".join(fingerprint.class_names) if fingerprint.class_names else "",
                    "text": fingerprint.text_content or "",
                },
            }

            # Add selectors as attributes
            if fingerprint.selectors:
                for sel in fingerprint.selectors:
                    element_data["attributes"][sel.selector_type.value] = sel.value

            # Build selector from fingerprint
            selector = self._build_selector_from_fingerprint(fingerprint)

            if is_anchor:
                # Store as anchor
                self._anchor_data = element_data
                self._anchor_selector = selector
                self._status_bar.set_status_message(
                    "Anchor set! Pick target (Ctrl+E) or clear anchor (Ctrl+Shift+A)", "success"
                )
                # Update status bar to show anchor info
                self._status_bar.set_anchor_element(
                    fingerprint.tag_name, element_data.get("name", "")
                )
            else:
                # Store as target element and load into UI
                self._on_tree_element_selected(element_data)
                self._status_bar.set_status_message(f"Selected <{fingerprint.tag_name}>", "success")
        except Exception as e:
            logger.error(f"UIExplorer: Failed to process picked element: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
        finally:
            self._cancel_picking()

    def _build_selector_from_fingerprint(self, fingerprint) -> str:
        """Build a selector string from element fingerprint."""
        tag = fingerprint.tag_name.upper()
        attrs = [f"tag='{tag}'"]

        if fingerprint.element_id:
            attrs.append(f"id='{fingerprint.element_id}'")

        if fingerprint.text_content:
            text = fingerprint.text_content[:50].replace("'", "&apos;")
            attrs.append(f"aaname='{text}'")

        # Look for good selectors in the fingerprint
        if fingerprint.selectors:
            for sel in fingerprint.selectors:
                if sel.selector_type.value == "css" and sel.value.startswith("#"):
                    # ID-based CSS selector
                    pass  # Already have ID
                elif sel.selector_type.value == "css" and "[data-testid=" in sel.value:
                    # Extract data-testid
                    import re

                    match = re.search(r'\[data-testid=["\']([^"\']+)["\']\]', sel.value)
                    if match:
                        attrs.append(f"data-testid='{match.group(1)}'")

        return f"<webctrl {' '.join(attrs)} />"

    def _build_combined_selector(self, anchor: str, target: str, position: str = "left_of") -> str:
        """
        Build combined anchor + target selector in UiPath XML format.

        Args:
            anchor: Anchor element selector (XML or XPath format)
            target: Target element selector (XML or XPath format)
            position: Relative position ("left_of", "right_of", "above", "below", "inside")

        Returns:
            Combined selector string with anchor, nav, and target
        """
        import re

        def ensure_webctrl_format(selector: str) -> str:
            """Convert selector to webctrl XML format if needed."""
            selector = selector.strip()

            # Already in webctrl format
            if selector.startswith("<webctrl") or selector.startswith("<wnd"):
                return selector

            # XPath format - convert to webctrl
            if selector.startswith("//"):
                xpath = selector[2:]
                tag_match = re.match(r"^(\w+|\*)", xpath)
                tag = tag_match.group(1).upper() if tag_match else "*"
                attrs = [f"tag='{tag}'"]

                # Extract attributes [@attr='value']
                for m in re.finditer(r"\[@(\w+)=['\"]([^'\"]+)['\"]\]", xpath):
                    attrs.append(f"{m.group(1)}='{m.group(2)}'")

                # Extract text() contains
                text_match = re.search(
                    r"contains\s*\(\s*text\s*\(\s*\)\s*,\s*['\"]([^'\"]+)['\"]\s*\)", xpath
                )
                if text_match:
                    attrs.append(f"aaname='{text_match.group(1)}'")

                return f"<webctrl {' '.join(attrs)} />"

            # CSS selector - basic conversion
            if selector.startswith("#"):
                element_id = selector[1:].split("[")[0].split(".")[0]
                return f"<webctrl id='{element_id}' />"

            if selector.startswith("."):
                class_name = selector[1:].split("[")[0].split(".")[0]
                return f"<webctrl class='{class_name}' />"

            # Unknown format - wrap as-is
            return f"<webctrl selector='{selector}' />"

        # Navigation direction based on position
        position_nav = {
            "left_of": "up='1'",
            "right_of": "up='1'",
            "above": "up='1'",
            "below": "up='1'",
            "inside": "",  # Direct child relationship
        }

        anchor_xml = ensure_webctrl_format(anchor)
        target_xml = ensure_webctrl_format(target)
        nav = position_nav.get(position, "up='1'")

        if nav:
            return f"{anchor_xml}\n<nav {nav} />\n{target_xml}"
        return f"{anchor_xml}\n{target_xml}"

    def _on_indicate_anchor(self) -> None:
        """Handle indicate anchor."""
        try:
            logger.debug("UIExplorer: Indicate anchor requested")

            if self._mode == "browser" and not self._browser_page:
                self._status_bar.set_status_message(
                    "No browser page - open a browser first", "warning"
                )
                return

            self._is_picking_element = False
            self._is_picking_anchor = True
            self._toolbar.set_picking_active(element=False, anchor=True)
            self._status_bar.show_picking_active("anchor")

            if self._mode == "browser":
                self._schedule_task(self._start_browser_picking())
            else:
                self._start_desktop_picking()
        except Exception as e:
            logger.error(f"UIExplorer: Indicate anchor failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
            self._cancel_picking()

    def _cancel_picking(self) -> None:
        """Cancel any active picking mode."""
        self._is_picking_element = False
        self._is_picking_anchor = False
        self._toolbar.set_picking_active(element=False, anchor=False)

        # Close desktop picker overlay if active
        if self._desktop_picker:
            try:
                self._desktop_picker.close()
            except Exception:
                pass
            self._desktop_picker = None

        # Show dialog again if it was hidden for desktop picking
        if not self.isVisible():
            self.show()
            self.raise_()
            self.activateWindow()

        if self._selector_manager and self._browser_page:
            self._schedule_task(self._stop_browser_picking())

    async def _stop_browser_picking(self) -> None:
        """Stop browser picking mode."""
        try:
            if self._selector_manager:
                await self._selector_manager.deactivate_selector_mode()
        except Exception as e:
            logger.debug(f"UIExplorer: Stop picking error (ignored): {e}")

    def _on_validate(self) -> None:
        """Handle validate selector."""
        try:
            logger.debug("UIExplorer: Validate requested")

            if not self._current_selector:
                self._status_bar.set_status_message("No selector to validate", "warning")
                self._toolbar.reset_validate_button()
                return

            self._status_bar.set_status_message("Validating...", "info")

            if self._mode == "browser":
                self._schedule_task(self._validate_browser_selector())
            else:
                self._validate_desktop_selector()
        except Exception as e:
            logger.error(f"UIExplorer: Validate failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
            self._toolbar.set_validate_result(False)

    async def _validate_browser_selector(self) -> None:
        """Validate selector against browser page."""
        try:
            if not self._browser_page:
                self._status_bar.set_status_message("No browser page", "warning")
                self._toolbar.set_validate_result(False)
                return

            self._init_selector_manager()

            if not self._selector_manager:
                self._status_bar.set_status_message("Selector manager unavailable", "warning")
                self._toolbar.set_validate_result(False)
                return

            # Ensure page is injected for test/highlight to work
            await self._selector_manager.inject_into_page(self._browser_page)

            # Parse selector - converts XML format to XPath if needed
            from casare_rpa.utils.selectors.selector_manager import parse_xml_selector

            selector, selector_type = parse_xml_selector(self._current_selector)

            import time

            start = time.time()
            result = await self._selector_manager.test_selector(selector, selector_type)
            elapsed = (time.time() - start) * 1000

            count = result.get("count", 0)
            self._status_bar.show_validation_result(count, elapsed)

            if count == 1:
                self._toolbar.set_validate_result(True)
            elif count > 1:
                self._toolbar.set_validate_result(False)  # Not unique
            else:
                self._toolbar.set_validate_result(False)

            # Highlight the matched elements
            if count > 0:
                await self._selector_manager.highlight_elements(selector, selector_type)

        except Exception as e:
            logger.error(f"UIExplorer: Browser validation failed: {e}")
            self._status_bar.set_status_message(f"Validation error: {e}", "error")
            self._toolbar.set_validate_result(False)

    def _validate_desktop_selector(self) -> None:
        """Validate selector against desktop."""
        self._status_bar.set_status_message("Desktop validation not yet implemented", "info")
        self._toolbar.reset_validate_button()

    def _on_repair(self) -> None:
        """Handle repair selector."""
        try:
            logger.debug("UIExplorer: Repair requested")

            if not self._current_selector:
                self._status_bar.set_status_message("No selector to repair", "warning")
                return

            # Repair functionality will integrate with selector healing later
            self._status_bar.set_status_message("Selector repair not yet implemented", "info")

            # Show tooltip on repair button
            QMessageBox.information(
                self,
                "Repair Selector",
                "Selector repair/healing is not yet implemented.\n\n"
                "This feature will use the healing chain to automatically\n"
                "fix broken selectors using heuristics, anchors, and CV.",
            )
        except Exception as e:
            logger.error(f"UIExplorer: Repair failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _on_highlight_changed(self, active: bool) -> None:
        """Handle highlight toggle."""
        try:
            logger.debug(f"UIExplorer: Highlight toggled: {active}")
            self._highlight_active = active

            if active:
                if self._current_selector:
                    self._schedule_task(self._highlight_current_selector())
                else:
                    self._status_bar.set_status_message("No selector to highlight", "warning")
                    self._toolbar.set_highlight_checked(False)
            else:
                self._schedule_task(self._clear_highlights())
        except Exception as e:
            logger.error(f"UIExplorer: Highlight toggle failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    async def _highlight_current_selector(self) -> None:
        """Highlight the current selector in the browser/desktop."""
        try:
            if self._mode != "browser" or not self._browser_page:
                self._status_bar.set_status_message("Highlight requires browser", "warning")
                return

            self._init_selector_manager()

            if not self._selector_manager:
                self._status_bar.set_status_message("Selector manager unavailable", "warning")
                return

            selector = self._current_selector.strip()
            if selector.startswith("//") or selector.startswith("(//"):
                selector_type = "xpath"
            else:
                selector_type = "css"

            await self._selector_manager.highlight_elements(selector, selector_type)
            self._status_bar.show_highlight_active(True)
        except Exception as e:
            logger.error(f"UIExplorer: Highlight failed: {e}")
            self._status_bar.set_status_message(f"Highlight error: {e}", "error")

    async def _clear_highlights(self) -> None:
        """Clear any active highlights."""
        try:
            # Highlighting is typically temporary, just update status
            self._status_bar.clear_status_message()
        except Exception as e:
            logger.debug(f"UIExplorer: Clear highlights error (ignored): {e}")

    def _on_toggle_highlight(self) -> None:
        """Toggle highlight via keyboard shortcut."""
        current = self._toolbar._highlight_btn.isChecked()
        self._toolbar.set_highlight_checked(not current)
        self._on_highlight_changed(not current)

    def _on_options(self) -> None:
        """Handle options button - show options menu."""
        try:
            logger.debug("UIExplorer: Options requested")

            # Create options menu
            menu = QMenu(self)
            menu.setStyleSheet("""
                QMenu {
                    background: #2d2d2d;
                    border: 1px solid #3a3a3a;
                    border-radius: {TOKENS.radius.sm}px;
                    padding: 4px;
                }
                QMenu::item {
                    padding: 6px 24px 6px 12px;
                    color: #e0e0e0;
                }
                QMenu::item:selected {
                    background: #3b82f6;
                }
                QMenu::indicator {
                    width: 16px;
                    height: 16px;
                    margin-left: 4px;
                }
            """)

            # Show hidden elements option
            show_hidden_action = QAction("Show hidden elements", self)
            show_hidden_action.setCheckable(True)
            show_hidden_action.setChecked(self._options.get("show_hidden_elements", False))
            show_hidden_action.triggered.connect(
                lambda checked: self._set_option("show_hidden_elements", checked)
            )
            menu.addAction(show_hidden_action)

            # Include computed properties option
            computed_action = QAction("Include computed properties", self)
            computed_action.setCheckable(True)
            computed_action.setChecked(self._options.get("include_computed_properties", True))
            computed_action.triggered.connect(
                lambda checked: self._set_option("include_computed_properties", checked)
            )
            menu.addAction(computed_action)

            # Auto-expand tree option
            auto_expand_action = QAction("Auto-expand tree", self)
            auto_expand_action.setCheckable(True)
            auto_expand_action.setChecked(self._options.get("auto_expand_tree", True))
            auto_expand_action.triggered.connect(
                lambda checked: self._set_option("auto_expand_tree", checked)
            )
            menu.addAction(auto_expand_action)

            # Show menu at button position
            btn = self._toolbar._options_btn
            menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))
        except Exception as e:
            logger.error(f"UIExplorer: Options menu failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _set_option(self, name: str, value: bool) -> None:
        """
        Set an option value.

        Args:
            name: Option name
            value: Option value
        """
        self._options[name] = value
        logger.debug(f"UIExplorer: Option {name} = {value}")

        # Apply option changes
        if name == "show_hidden_elements":
            # Would filter hidden elements in tree
            pass
        elif name == "include_computed_properties":
            # Would affect property explorer display
            pass
        elif name == "auto_expand_tree":
            # Would auto-expand tree items
            pass

    # =========================================================================
    # Snapshot / Compare / Find Similar / Smart Suggest Handlers
    # =========================================================================

    def _on_snapshot(self) -> None:
        """Capture current element snapshot for comparison."""
        try:
            if not self._current_element:
                self._status_bar.set_status_message("No element selected for snapshot", "warning")
                self._toolbar.reset_snapshot_button()
                return

            if self._mode == "browser" and not self._browser_page:
                self._status_bar.set_status_message("No browser page for snapshot", "warning")
                self._toolbar.reset_snapshot_button()
                return

            logger.debug("UIExplorer: Capturing snapshot")
            self._schedule_task(self._capture_snapshot())

        except Exception as e:
            logger.error(f"UIExplorer: Snapshot failed: {e}")
            self._status_bar.set_status_message(f"Snapshot error: {e}", "error")
            self._toolbar.reset_snapshot_button()

    async def _capture_snapshot(self) -> None:
        """Async snapshot capture."""
        try:
            # Build snapshot data from current element
            snapshot = {
                "timestamp": asyncio.get_event_loop().time(),
                "element": self._current_element.copy() if self._current_element else {},
                "selector": self._current_selector,
            }

            # For browser mode, capture live element state
            if self._mode == "browser" and self._browser_page and self._current_selector:
                self._init_selector_manager()
                if self._selector_manager:
                    try:
                        # Try to get live element attributes
                        selector = self._current_selector.strip()
                        selector_type = "xpath" if selector.startswith("//") else "css"
                        await self._selector_manager.inject_into_page(self._browser_page)

                        # Get element info via JS
                        element_info = await self._browser_page.evaluate(
                            """(selector) => {
                                const el = document.querySelector(selector);
                                if (!el) return null;
                                return {
                                    tag: el.tagName.toLowerCase(),
                                    id: el.id || '',
                                    classes: Array.from(el.classList),
                                    text: el.innerText?.substring(0, 100) || '',
                                    rect: el.getBoundingClientRect(),
                                    attributes: Object.fromEntries(
                                        Array.from(el.attributes).map(a => [a.name, a.value])
                                    )
                                };
                            }""",
                            self._current_selector if selector_type == "css" else None,
                        )
                        if element_info:
                            snapshot["live_element"] = element_info
                    except Exception as e:
                        logger.debug(f"Could not capture live element: {e}")

            self._snapshot_data = snapshot
            self._toolbar.set_compare_enabled(True)
            self._toolbar.set_snapshot_success()
            self._status_bar.set_status_message(
                "Snapshot captured. Make changes and click Compare.", "success"
            )
            logger.info("UIExplorer: Snapshot captured successfully")

        except Exception as e:
            logger.error(f"UIExplorer: Async snapshot failed: {e}")
            self._status_bar.set_status_message(f"Snapshot error: {e}", "error")
        finally:
            self._toolbar.reset_snapshot_button()

    def _on_compare(self) -> None:
        """Compare current state with previous snapshot."""
        try:
            if not self._snapshot_data:
                self._status_bar.set_status_message("No snapshot to compare with", "warning")
                return

            if not self._current_element:
                self._status_bar.set_status_message("No current element to compare", "warning")
                return

            logger.debug("UIExplorer: Comparing with snapshot")
            self._schedule_task(self._compare_with_snapshot())

        except Exception as e:
            logger.error(f"UIExplorer: Compare failed: {e}")
            self._status_bar.set_status_message(f"Compare error: {e}", "error")

    async def _compare_with_snapshot(self) -> None:
        """Async comparison with snapshot."""
        try:
            before = self._snapshot_data.get("element", {})
            after = self._current_element or {}

            # Calculate differences
            diff = self._calculate_element_diff(before, after)

            # Show diff dialog
            self._show_diff_dialog(before, after, diff)

        except Exception as e:
            logger.error(f"UIExplorer: Async compare failed: {e}")
            self._status_bar.set_status_message(f"Compare error: {e}", "error")

    def _calculate_element_diff(
        self, before: dict[str, Any], after: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Calculate differences between two element snapshots.

        Returns:
            Dict with diff information
        """
        before_attrs = before.get("attributes", {})
        after_attrs = after.get("attributes", {})

        before_keys = set(before_attrs.keys())
        after_keys = set(after_attrs.keys())

        added = after_keys - before_keys
        removed = before_keys - after_keys
        common = before_keys & after_keys

        changed = {
            k: {"before": before_attrs[k], "after": after_attrs[k]}
            for k in common
            if before_attrs[k] != after_attrs[k]
        }

        return {
            "has_changes": bool(added or removed or changed),
            "attributes_added": list(added),
            "attributes_removed": list(removed),
            "attributes_changed": changed,
            "tag_changed": before.get("tag_or_control") != after.get("tag_or_control"),
            "text_changed": before.get("name", "") != after.get("name", ""),
        }

    def _show_diff_dialog(
        self, before: dict[str, Any], after: dict[str, Any], diff: dict[str, Any]
    ) -> None:
        """Show diff results in a dialog."""
        from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit, QVBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Element Diff")
        dialog.setMinimumSize(TOKENS.sizes.dialog_md, TOKENS.sizes.dialog_md)
        dialog.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: #e0e0e0;
            }
            QTextEdit {{
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.sm}px;
                color: #e0e0e0;
                font-family: Consolas, monospace;
                font-size: {TOKENS.typography.body}px;
            }}
        """)

        layout = QVBoxLayout(dialog)

        # Build diff text
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)

        if not diff["has_changes"]:
            diff_text = "No changes detected between snapshot and current element."
        else:
            lines = ["ELEMENT DIFF REPORT", "=" * 40, ""]

            if diff["tag_changed"]:
                lines.append(
                    f"Tag: {before.get('tag_or_control', '?')} -> {after.get('tag_or_control', '?')}"
                )

            if diff["text_changed"]:
                lines.append(
                    f"Text: '{before.get('name', '')[:30]}' -> '{after.get('name', '')[:30]}'"
                )

            if diff["attributes_added"]:
                lines.append("")
                lines.append("+ ATTRIBUTES ADDED:")
                for attr in diff["attributes_added"]:
                    val = after.get("attributes", {}).get(attr, "")
                    lines.append(f"  + {attr}: {str(val)[:50]}")

            if diff["attributes_removed"]:
                lines.append("")
                lines.append("- ATTRIBUTES REMOVED:")
                for attr in diff["attributes_removed"]:
                    val = before.get("attributes", {}).get(attr, "")
                    lines.append(f"  - {attr}: {str(val)[:50]}")

            if diff["attributes_changed"]:
                lines.append("")
                lines.append("~ ATTRIBUTES CHANGED:")
                for attr, vals in diff["attributes_changed"].items():
                    lines.append(f"  ~ {attr}:")
                    lines.append(f"      before: {str(vals['before'])[:40]}")
                    lines.append(f"      after:  {str(vals['after'])[:40]}")

            diff_text = "\n".join(lines)

        text_edit.setPlainText(diff_text)
        layout.addWidget(text_edit)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        buttons.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 4px;
                padding: 6px 16px;
                color: white;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        layout.addWidget(buttons)

        dialog.exec()

        if diff["has_changes"]:
            self._status_bar.set_status_message(
                f"Diff: {len(diff['attributes_added'])} added, "
                f"{len(diff['attributes_removed'])} removed, "
                f"{len(diff['attributes_changed'])} changed",
                "info",
            )
        else:
            self._status_bar.set_status_message("No changes detected", "success")

    def _on_find_similar(self) -> None:
        """Find elements similar to current selection."""
        try:
            if not self._current_element:
                self._status_bar.set_status_message("No element selected", "warning")
                self._toolbar.reset_find_similar_button()
                return

            if self._mode == "browser" and not self._browser_page:
                self._status_bar.set_status_message("No browser page", "warning")
                self._toolbar.reset_find_similar_button()
                return

            logger.debug("UIExplorer: Finding similar elements")
            self._status_bar.set_status_message("Searching for similar elements...", "info")
            self._schedule_task(self._find_similar_elements())

        except Exception as e:
            logger.error(f"UIExplorer: Find similar failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
            self._toolbar.reset_find_similar_button()

    async def _find_similar_elements(self) -> None:
        """Async find similar elements."""
        try:
            if self._mode != "browser" or not self._browser_page:
                self._toolbar.reset_find_similar_button()
                return

            # Get current element properties
            current_tag = self._current_element.get(
                "tag_or_control", self._current_element.get("tag", "")
            )
            self._current_element.get("name", "")
            self._current_element.get("attributes", {})

            # Find elements by same tag
            similar_elements = await self._browser_page.evaluate(
                """(tag) => {
                    const elements = document.querySelectorAll(tag);
                    const results = [];
                    for (let i = 0; i < Math.min(elements.length, 25); i++) {
                        const el = elements[i];
                        results.push({
                            selector: el.id ? '#' + el.id :
                                     (el.className ? '.' + el.className.split(' ')[0] : el.tagName.toLowerCase()),
                            text: (el.innerText || '').substring(0, 50).trim(),
                            tag: el.tagName.toLowerCase(),
                            classes: el.className || '',
                            id: el.id || ''
                        });
                    }
                    return results;
                }""",
                current_tag.lower() if current_tag else "*",
            )

            self._show_similar_dialog(similar_elements or [])

        except Exception as e:
            logger.error(f"UIExplorer: Async find similar failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")
        finally:
            self._toolbar.reset_find_similar_button()

    def _show_similar_dialog(self, results: list) -> None:
        """Show similar elements dialog."""
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QListWidget,
            QListWidgetItem,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Similar Elements ({len(results)} found)")
        dialog.setMinimumSize(TOKENS.sizes.dialog_md, TOKENS.sizes.dialog_md)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: #1e1e1e;
                color: #e0e0e0;
            }}
            QLabel {{
                color: #888;
                font-size: {TOKENS.typography.body}px;
            }}
            QListWidget {{
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.sm}px;
                color: #e0e0e0;
                font-family: Consolas, monospace;
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.xs}px;
                border-bottom: 1px solid #2a2a2a;
            }}
            QListWidget::item:selected {{
                background: #3b82f6;
            }}
            QListWidget::item:hover:!selected {{
                background: #2a2a2a;
            }}
        """)

        layout = QVBoxLayout(dialog)

        info_label = QLabel("Double-click to use selector. Found elements with same tag:")
        layout.addWidget(info_label)

        list_widget = QListWidget()
        for r in results:
            selector = r.get("selector", "")
            text = r.get("text", "")[:30]
            r.get("tag", "")
            display = f"{selector}"
            if text:
                display += f' - "{text}"'
            if r.get("id"):
                display += f" (id={r['id']})"

            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, selector)
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        layout.addWidget(buttons)

        # Double-click handler
        def on_item_double_clicked(item):
            selector = item.data(Qt.ItemDataRole.UserRole)
            if selector:
                self._preview_panel.set_preview(selector)
                self._current_selector = selector
                self._update_save_button_state()
                dialog.accept()
                self._status_bar.set_status_message(f"Selected: {selector}", "success")

        list_widget.itemDoubleClicked.connect(on_item_double_clicked)

        dialog.exec()

    def _on_ai_suggest(self) -> None:
        """Get AI-powered selector suggestions."""
        try:
            if not self._current_element:
                self._status_bar.set_status_message("No element selected", "warning")
                return

            logger.debug("UIExplorer: Generating AI suggestions")
            self._status_bar.set_status_message("Generating selector suggestions...", "info")

            # Generate strategies from current element
            strategies = self._generate_selector_strategies(self._current_element)

            if strategies:
                self._show_suggestions_dialog(strategies)
            else:
                self._status_bar.set_status_message("No suggestions generated", "warning")

        except Exception as e:
            logger.error(f"UIExplorer: AI suggest failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _generate_selector_strategies(self, element_data: dict[str, Any]) -> list:
        """
        Generate multiple selector strategies for an element.

        Returns:
            List of strategy dicts with selector, type, score, and description
        """
        strategies = []
        attrs = element_data.get("attributes", {})
        tag = element_data.get("tag_or_control", element_data.get("tag", ""))
        name = element_data.get("name", "")

        # Strategy 1: ID (highest priority)
        element_id = attrs.get("id", "")
        if element_id and not any(c.isdigit() for c in element_id[-4:]):
            strategies.append(
                {
                    "selector": f"#{element_id}",
                    "type": "id",
                    "score": 95,
                    "description": "ID selector - most reliable if ID is stable",
                }
            )

        # Strategy 2: data-testid (designed for testing)
        data_testid = attrs.get("data-testid", "")
        if data_testid:
            strategies.append(
                {
                    "selector": f'[data-testid="{data_testid}"]',
                    "type": "data-testid",
                    "score": 92,
                    "description": "Test ID - designed for automation",
                }
            )

        # Strategy 3: aria-label (accessible)
        aria_label = attrs.get("aria-label", "")
        if aria_label:
            strategies.append(
                {
                    "selector": f'[aria-label="{aria_label}"]',
                    "type": "aria",
                    "score": 88,
                    "description": "ARIA label - accessible and semantic",
                }
            )

        # Strategy 4: name attribute
        name_attr = attrs.get("name", "")
        if name_attr:
            strategies.append(
                {
                    "selector": f'{tag}[name="{name_attr}"]',
                    "type": "name",
                    "score": 85,
                    "description": "Name attribute - common for form elements",
                }
            )

        # Strategy 5: Text content (for buttons/links)
        if name and tag.lower() in ("button", "a", "span", "label", "h1", "h2", "h3"):
            escaped_text = name.replace('"', '\\"')[:40]
            strategies.append(
                {
                    "selector": f'{tag}:has-text("{escaped_text}")',
                    "type": "text",
                    "score": 75,
                    "description": "Text selector - good for visible labels",
                }
            )

        # Strategy 6: Class-based
        class_names = attrs.get("class", "").split()
        semantic_classes = [
            c for c in class_names if not any(x in c for x in ["-", "_", "0", "1", "2"])
        ]
        if semantic_classes:
            strategies.append(
                {
                    "selector": f"{tag}.{semantic_classes[0]}",
                    "type": "class",
                    "score": 65,
                    "description": "Class selector - may match multiple elements",
                }
            )

        # Strategy 7: Role attribute
        role = attrs.get("role", "")
        if role:
            strategies.append(
                {
                    "selector": f'[role="{role}"]',
                    "type": "role",
                    "score": 70,
                    "description": "Role selector - semantic but may not be unique",
                }
            )

        # Strategy 8: Combination (tag + class + text)
        if semantic_classes and name:
            escaped_text = name.replace('"', '\\"')[:20]
            strategies.append(
                {
                    "selector": f'{tag}.{semantic_classes[0]}:has-text("{escaped_text}")',
                    "type": "combo",
                    "score": 82,
                    "description": "Combined selector - more specific",
                }
            )

        # Sort by score descending
        strategies.sort(key=lambda s: s["score"], reverse=True)

        return strategies

    def _show_suggestions_dialog(self, strategies: list) -> None:
        """Show Smart Suggest dialog with ranked selector options."""
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QListWidget,
            QListWidgetItem,
            QVBoxLayout,
        )

        dialog = QDialog(self)
        dialog.setWindowTitle("Smart Selector Suggestions")
        dialog.setMinimumSize(TOKENS.sizes.dialog_lg, TOKENS.sizes.dialog_lg)
        dialog.setStyleSheet(f"""
            QDialog {{
                background: #1e1e1e;
                color: #e0e0e0;
            }}
            QLabel {{
                color: #888;
                font-size: {TOKENS.typography.body}px;
            }}
            QListWidget {{
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.sm}px;
                color: #e0e0e0;
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.md}px;
                border-bottom: 1px solid #2a2a2a;
            }}
            QListWidget::item:selected {{
                background: #3b82f6;
            }}
            QListWidget::item:hover:!selected {{
                background: #2a2a2a;
            }}
        """)

        layout = QVBoxLayout(dialog)

        info_label = QLabel("Ranked by reliability. Double-click to apply:")
        layout.addWidget(info_label)

        list_widget = QListWidget()
        for s in strategies:
            score = s["score"]
            selector = s["selector"]
            strategy_type = s["type"]
            description = s["description"]

            # Color code by score
            if score >= 85:
                pass  # Green
            elif score >= 70:
                pass  # Yellow
            else:
                pass  # Red

            display = f"[{score}] {selector}"

            item = QListWidgetItem()
            item.setText(display)
            item.setToolTip(f"{strategy_type}: {description}")
            item.setData(Qt.ItemDataRole.UserRole, selector)
            list_widget.addItem(item)

        layout.addWidget(list_widget)

        # Description label
        desc_label = QLabel("Hover over items for details")
        desc_label.setStyleSheet("color: #666; font-style: italic;")
        layout.addWidget(desc_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        buttons.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 16px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: #4a4a4a;
            }
        """)
        layout.addWidget(buttons)

        # Double-click handler
        def on_item_double_clicked(item):
            selector = item.data(Qt.ItemDataRole.UserRole)
            if selector:
                self._preview_panel.set_preview(selector)
                self._current_selector = selector
                self._update_save_button_state()
                dialog.accept()
                self._status_bar.set_status_message(f"Applied: {selector[:50]}...", "success")

        list_widget.itemDoubleClicked.connect(on_item_double_clicked)

        # Show tooltip on selection change
        def on_selection_changed():
            current = list_widget.currentItem()
            if current:
                desc_label.setText(current.toolTip())

        list_widget.currentItemChanged.connect(on_selection_changed)

        dialog.exec()

    def _on_copy_selector(self) -> None:
        """Copy current selector to clipboard."""
        try:
            selector = self._preview_panel.get_selector_text()
            if selector:
                clipboard = QApplication.clipboard()
                clipboard.setText(selector)
                self._status_bar.set_status_message("Selector copied to clipboard", "success")
            else:
                self._status_bar.set_status_message("No selector to copy", "warning")
        except Exception as e:
            logger.error(f"UIExplorer: Copy selector failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _on_escape(self) -> None:
        """Handle escape key - cancel picking or close dialog."""
        try:
            # If picking is active, cancel it
            if self._is_picking_element or self._is_picking_anchor:
                self._cancel_picking()
                self._status_bar.clear_status_message()
                return

            # Otherwise close dialog
            self.reject()
        except Exception as e:
            logger.error(f"UIExplorer: Escape handling failed: {e}")
            self.reject()

    def _on_tree_element_selected(self, element_data: dict[str, Any]) -> None:
        """
        Handle element selection from visual tree panel.

        This method coordinates loading element data into all panels:
        1. Update current element reference
        2. Update status bar with element info
        3. Load into selector model (which updates SelectorEditorPanel and SelectedAttributesPanel)
        4. Load into PropertyExplorerPanel (raw dict method for full attribute access)
        5. Enable repair button
        6. Emit signal for external listeners

        Args:
            element_data: Element data dictionary from tree
        """
        try:
            tag = element_data.get("tag_or_control", element_data.get("tag", "unknown"))
            logger.debug(f"UIExplorer: Tree element selected: {tag}")

            # 1. Update current element
            self._current_element = element_data

            # 2. Update status bar
            name = element_data.get("name", "")
            self._status_bar.set_target_element(tag, name)

            # 3. Load element into selector model (this updates editor and attrs panels)
            # The selector model creates UIExplorerElement internally
            self._selector_model.load_from_dict(element_data)

            # 4. Load element into property explorer panel using raw dict
            # This gives access to ALL attributes, not just those in the selector model
            self._property_explorer_panel.load_from_dict(element_data)

            # 5. Enable repair button
            self._toolbar.set_repair_enabled(True)

            # 6. Emit element_selected signal for external listeners
            self.element_selected.emit(element_data)
        except Exception as e:
            logger.error(f"UIExplorer: Tree element selection failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _load_property_explorer(self, element_data: dict[str, Any]) -> None:
        """
        Load element data into the property explorer panel.

        Note: This method now uses load_from_dict for broader attribute support.
        The old approach using UIExplorerElement is still available via load_from_element.

        Args:
            element_data: Element data dictionary
        """
        # Use the new dict-based loading for broader attribute access
        self._property_explorer_panel.load_from_dict(element_data)

    def _on_property_copied(self, name: str, value: str) -> None:
        """
        Handle property value copied from property explorer.

        Args:
            name: Property name that was copied
            value: Property value that was copied
        """
        try:
            if value:
                self._status_bar.set_status_message(f"Copied '{name}' to clipboard", "success")
            else:
                self._status_bar.set_status_message(f"Copied empty value for '{name}'", "info")
        except Exception as e:
            logger.error(f"UIExplorer: Property copy notification failed: {e}")

    def _on_tree_element_double_clicked(self, element_data: dict[str, Any]) -> None:
        """
        Handle double-click on tree element for quick selection.

        Args:
            element_data: Element data dictionary from tree
        """
        try:
            logger.debug(
                f"UIExplorer: Tree element double-clicked: {element_data.get('tag_or_control', 'unknown')}"
            )

            # Update current element
            self._on_tree_element_selected(element_data)

            # Confirm selector on double-click
            if self._current_selector:
                self.selector_confirmed.emit(self._current_selector)
                self._status_bar.set_status_message("Selector confirmed", "success")
        except Exception as e:
            logger.error(f"UIExplorer: Double-click handling failed: {e}")
            self._status_bar.set_status_message(f"Error: {e}", "error")

    def _on_preview_updated(self, xml_string: str) -> None:
        """
        Handle selector model preview update.

        Args:
            xml_string: Updated XML selector string
        """
        # Preview panel now gets updates via model connection, but keep current_selector in sync
        self._current_selector = xml_string
        self._update_save_button_state()

        # Update preview with combined anchor+target if anchor is set
        self._update_preview_with_anchor()

    def _on_attribute_toggled(self, name: str, included: bool) -> None:
        """
        Handle attribute toggle from selector model.

        Args:
            name: Attribute name
            included: Whether it's now included
        """
        logger.debug(f"UIExplorer: Attribute {name} toggled to {included}")

        # Enable save button when we have a valid selector
        self._update_save_button_state()

    def _on_preview_copy(self) -> None:
        """Handle copy from preview panel."""
        self._status_bar.set_status_message("Selector copied to clipboard", "success")

    def _on_format_changed(self, format_type: str) -> None:
        """
        Handle format change in preview panel.

        Args:
            format_type: New format ("xml", "css", "xpath")
        """
        logger.debug(f"UIExplorer: Preview format changed to {format_type}")
        self._status_bar.set_status_message(f"Format: {format_type.upper()}", "info")

    def _on_selector_manually_changed(self, selector: str) -> None:
        """
        Handle manual selector text changes in edit mode.

        Args:
            selector: New selector text
        """
        self._current_selector = selector
        self._update_save_button_state()
        logger.debug("UIExplorer: Selector manually edited")

    def _on_save(self) -> None:
        """Handle save button click or Enter key."""
        try:
            if not self._current_selector:
                self._status_bar.set_status_message("No selector to save", "warning")
                return

            final_selector = self._current_selector

            # Combine with anchor if both are present
            if self._anchor_data and self._anchor_selector:
                final_selector = self._build_combined_selector(
                    anchor=self._anchor_selector,
                    target=self._current_selector,
                    position="left_of",  # Default position
                )
                logger.info("UIExplorer: Combined anchor + target selector")

            logger.info(f"UIExplorer: Saving selector: {final_selector[:80]}...")
            self.selector_confirmed.emit(final_selector)
            self.accept()
        except Exception as e:
            logger.error(f"UIExplorer: Save failed: {e}")
            self._status_bar.set_status_message(f"Save failed: {e}", "error")

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        logger.debug("UIExplorer: Cancelled")
        self.reject()

    def _clear_anchor(self) -> None:
        """Clear the current anchor selection."""
        if not self._anchor_data:
            self._status_bar.set_status_message("No anchor to clear", "info")
            return

        self._anchor_data = None
        self._anchor_selector = ""
        self._status_bar.clear_anchor_element()
        self._update_preview_with_anchor()
        self._status_bar.set_status_message("Anchor cleared", "success")
        logger.debug("UIExplorer: Anchor cleared")

    def _update_preview_with_anchor(self) -> None:
        """Update preview to show combined anchor + target selector if both exist."""
        if not self._current_selector:
            return

        if self._anchor_data and self._anchor_selector:
            # Show combined selector in preview
            combined = self._build_combined_selector(
                anchor=self._anchor_selector, target=self._current_selector, position="left_of"
            )
            self._preview_panel.set_preview(combined)
        else:
            # Show just the target selector
            self._preview_panel.set_preview(self._current_selector)

    def _update_save_button_state(self) -> None:
        """Update save button enabled state based on selector validity."""
        has_selector = bool(self._current_selector and self._current_selector.strip())
        self._save_btn.setEnabled(has_selector)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_browser_page(self, page: "Page") -> None:
        """
        Set the browser page for browser mode operations.

        Args:
            page: Playwright Page instance
        """
        self._browser_page = page
        self._mode = "browser"
        self._status_bar.set_mode("browser")
        logger.debug("UIExplorer: Browser page set")

    def set_mode(self, mode: str) -> None:
        """
        Set the explorer mode.

        Args:
            mode: "browser" or "desktop"
        """
        self._mode = mode
        self._status_bar.set_mode(mode)
        self._visual_tree_panel.set_mode(mode)
        logger.debug(f"UIExplorer: Mode set to {mode}")

    def set_element(self, element_data: dict[str, Any]) -> None:
        """
        Set the current element being explored.

        Args:
            element_data: Element data dictionary
        """
        self._current_element = element_data

        # Update status bar
        tag = element_data.get("tag", element_data.get("control_type", "unknown"))
        name = element_data.get("name", "")
        self._status_bar.set_target_element(tag, name)

        # Load element into selector model (updates preview via signal)
        self._selector_model.load_from_dict(element_data)

        # Enable repair button
        self._toolbar.set_repair_enabled(True)

        logger.debug(f"UIExplorer: Element set: {tag}")

    def get_selector(self) -> str:
        """
        Get the current selector string.

        Returns:
            The current selector value
        """
        return self._current_selector

    def load_tree(self, root_element: dict[str, Any]) -> None:
        """
        Load the visual tree with element hierarchy.

        Args:
            root_element: Root element data with children
        """
        self._visual_tree_panel.load_tree(root_element)
        logger.debug("UIExplorer: Tree loaded")

    def load_tree_from_element(self, element: UIExplorerElement) -> None:
        """
        Load the visual tree from UIExplorerElement.

        Args:
            element: Root UIExplorerElement
        """
        self._visual_tree_panel.load_tree_from_element(element)
        logger.debug("UIExplorer: Tree loaded from element")

    def clear_tree(self) -> None:
        """Clear the visual tree."""
        self._visual_tree_panel.clear()

    def get_visual_tree_panel(self) -> VisualTreePanel:
        """
        Get the visual tree panel for advanced configuration.

        Returns:
            VisualTreePanel instance
        """
        return self._visual_tree_panel

    def get_selector_editor_panel(self) -> SelectorEditorPanel:
        """
        Get the selector editor panel.

        Returns:
            SelectorEditorPanel instance
        """
        return self._selector_editor_panel

    def get_selected_attrs_panel(self) -> SelectedAttributesPanel:
        """
        Get the selected attributes panel.

        Returns:
            SelectedAttributesPanel instance
        """
        return self._selected_attrs_panel

    def get_selector_model(self) -> SelectorModel:
        """
        Get the selector model for state access.

        Returns:
            SelectorModel instance
        """
        return self._selector_model

    def get_property_explorer_panel(self) -> PropertyExplorerPanel:
        """
        Get the property explorer panel.

        Returns:
            PropertyExplorerPanel instance
        """
        return self._property_explorer_panel

    def get_preview_panel(self) -> SelectorPreviewPanel:
        """
        Get the selector preview panel.

        Returns:
            SelectorPreviewPanel instance
        """
        return self._preview_panel

    def _update_preview(self) -> None:
        """Update the preview panel with current element."""
        if not self._current_element:
            self._preview_panel.set_preview("")
            return

        # Generate UiPath-style XML preview
        # Handle both old format (tag/control_type) and new format (tag_or_control)
        tag = self._current_element.get(
            "tag_or_control",
            self._current_element.get("tag", self._current_element.get("control_type", "element")),
        )
        attrs = self._current_element.get("attributes", {})

        # Build XML attributes string
        attr_parts = []

        # Add element_id if present
        element_id = self._current_element.get("element_id", "")
        if element_id:
            attr_parts.append(f"id='{element_id}'")

        # Add name if present
        name = self._current_element.get("name", "")
        if name:
            escaped_name = name.replace("'", "&apos;")[:50]
            attr_parts.append(f"name='{escaped_name}'")

        # Add other attributes
        for key, value in attrs.items():
            if value and key not in ("id", "name"):
                # Escape quotes in value
                escaped_value = str(value).replace("'", "&apos;")[:50]
                attr_parts.append(f"{key}='{escaped_value}'")
                if len(attr_parts) >= 5:
                    break

        attr_str = " ".join(attr_parts)
        if len(attrs) > 5:
            attr_str += " ..."

        xml_preview = f"<{tag} {attr_str} />"
        self._preview_panel.set_preview(xml_preview)
        self._current_selector = xml_preview

    def resizeEvent(self, event) -> None:
        """Handle resize to maintain splitter proportions."""
        super().resizeEvent(event)
        # Recalculate splitter sizes on resize
        total_width = self._main_splitter.width()
        if total_width > 0:
            self._main_splitter.setSizes(
                [
                    int(total_width * 0.25),
                    int(total_width * 0.35),
                    int(total_width * 0.15),
                    int(total_width * 0.25),
                ]
            )

    def _schedule_task(self, coro) -> None:
        """Schedule an async coroutine and track it for cleanup."""
        task = asyncio.ensure_future(coro)
        self._pending_tasks.append(task)
        task.add_done_callback(
            lambda t: self._pending_tasks.remove(t) if t in self._pending_tasks else None
        )

    def _cancel_pending_tasks(self) -> None:
        """Cancel all pending async tasks."""
        for task in self._pending_tasks:
            if not task.done():
                task.cancel()
        self._pending_tasks.clear()

    def closeEvent(self, event) -> None:
        """Handle dialog close - cleanup resources."""
        self._cancel_pending_tasks()
        if self._selector_manager:
            try:
                # Clean up selector manager if needed
                self._selector_manager = None
            except Exception as e:
                logger.debug(f"Error cleaning up selector manager: {e}")
        super().closeEvent(event)
