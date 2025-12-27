"""
Desktop Selector Tab.

Pick elements from Windows desktop applications using UIAutomation.
Generates AutomationId, Name, ControlType, Path selectors.
"""

import json
from typing import Any

from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from casare_rpa.presentation.canvas.theme_system import THEME


class DesktopSelectorTab(BaseSelectorTab):
    """
    Desktop element selector tab.

    Features:
    - Pick element from any Windows application
    - Generate AutomationId, Name, ControlType, Path selectors
    - Element properties viewer
    - Selector uniqueness validation
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._selected_element = None
        self._parent_control = None
        self._picker_overlay = None
        self._target_node = None
        self._target_property = "selector"

        self.setup_ui()
        self._load_desktop_root()

    @property
    def tab_name(self) -> str:
        return "Desktop"

    @property
    def tab_icon(self) -> str:
        return "\U0001f5a5"  # Desktop computer emoji

    def setup_ui(self) -> None:
        """Setup tab UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Pick element section
        pick_group = QGroupBox("Pick Element")
        pick_layout = QVBoxLayout(pick_group)

        info = QLabel(
            "Click 'Start Picking' then hover over any desktop element.\n"
            "Click to select, press ESC to cancel."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {THEME.text_muted};")
        pick_layout.addWidget(info)

        btn_layout = QHBoxLayout()

        self.pick_btn = QPushButton("Start Picking")
        self.pick_btn.setObjectName("pickButton")
        self.pick_btn.clicked.connect(self._on_pick_clicked)
        self.pick_btn.setStyleSheet(f"""
            QPushButton#pickButton {{
                background: {THEME.warning};
                color: {THEME.text_primary};
                border: 1px solid {THEME.primary_hover};
                padding: 12px 24px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton#pickButton:hover {{
                background: {THEME.primary_hover};
            }}
        """)
        btn_layout.addWidget(self.pick_btn)

        btn_layout.addStretch()
        pick_layout.addLayout(btn_layout)

        layout.addWidget(pick_group)

        # Element properties section
        props_group = QGroupBox("Selected Element Properties")
        props_layout = QVBoxLayout(props_group)

        self.props_table = QTableWidget()
        self.props_table.setColumnCount(2)
        self.props_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.props_table.horizontalHeader().setStretchLastSection(True)
        self.props_table.setAlternatingRowColors(True)
        self.props_table.setMaximumHeight(180)
        self.props_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {THEME.border};
                border-radius: 6px;
                background: {THEME.bg_component};
                color: {THEME.text_primary};
            }}
            QTableWidget::item {{
                padding: 4px;
            }}
            QHeaderView::section {{
                background: {THEME.bg_surface};
                color: {THEME.text_primary};
                padding: 6px;
                border: 1px solid {THEME.border};
            }}
        """)
        props_layout.addWidget(self.props_table)

        layout.addWidget(props_group)

        # Healing context options
        healing_group = QGroupBox("Healing Context")
        healing_layout = QVBoxLayout(healing_group)

        self.capture_properties = QCheckBox("Capture all element properties")
        self.capture_properties.setChecked(True)
        healing_layout.addWidget(self.capture_properties)

        self.capture_hierarchy = QCheckBox("Capture parent hierarchy")
        self.capture_hierarchy.setChecked(True)
        healing_layout.addWidget(self.capture_hierarchy)

        layout.addWidget(healing_group)

        layout.addStretch()

    def _load_desktop_root(self) -> None:
        """Load desktop root control."""
        try:
            import uiautomation as auto

            self._parent_control = auto.GetRootControl()
            logger.debug("Desktop root loaded")
        except Exception as e:
            logger.error(f"Failed to load desktop root: {e}")

    def set_target_node(self, node: Any, property_name: str) -> None:
        """Set target node for auto-pasting."""
        self._target_node = node
        self._target_property = property_name

    async def start_picking(self) -> None:
        """Start element picking mode."""
        self._start_picking_sync()

    def _start_picking_sync(self) -> None:
        """Sync version of start picking."""
        from casare_rpa.presentation.canvas.selectors.element_picker import (
            activate_element_picker,
        )

        self._emit_status("Picking mode active - hover and click...")
        self.pick_btn.setEnabled(False)

        def on_selected(element):
            self._on_element_selected(element)
            self._picker_overlay = None
            self.pick_btn.setEnabled(True)

        def on_cancelled():
            self._picker_overlay = None
            self.pick_btn.setEnabled(True)
            self._emit_status("")

        self._picker_overlay = activate_element_picker(on_selected, on_cancelled)

    async def stop_picking(self) -> None:
        """Stop element picking mode."""
        if self._picker_overlay:
            self._picker_overlay.close()
            self._picker_overlay = None
        self.pick_btn.setEnabled(True)

    def get_current_selector(self) -> SelectorResult | None:
        """Get current selector result."""
        return self._current_result

    def get_strategies(self) -> list[SelectorStrategy]:
        """Get generated strategies."""
        return self._strategies

    def _on_pick_clicked(self) -> None:
        """Handle pick button click."""
        self._start_picking_sync()

    def _on_element_selected(self, element) -> None:
        """Handle element selection from desktop."""
        logger.info(f"Desktop element selected: {element}")

        self._selected_element = element

        # Update properties table
        self._update_properties_table()

        # Generate selectors
        self._generate_selectors()

        # Emit strategies
        self.selectors_generated.emit(self._strategies)

        # Build result
        if self._strategies:
            best = self._strategies[0]

            healing_context = {}
            if self.capture_properties.isChecked():
                healing_context["properties"] = self._get_element_properties()
            if self.capture_hierarchy.isChecked():
                healing_context["hierarchy"] = self._get_hierarchy()

            self._current_result = SelectorResult(
                selector_value=json.dumps(best.value)
                if isinstance(best.value, dict)
                else best.value,
                selector_type=best.selector_type,
                confidence=best.score / 100.0,
                is_unique=best.is_unique,
                healing_context=healing_context,
                metadata=self._get_element_properties(),
            )

        self._emit_status(f"Selected element - {len(self._strategies)} selectors generated")

    def _update_properties_table(self) -> None:
        """Update properties table with element data."""
        if not self._selected_element:
            self.props_table.setRowCount(0)
            return

        props = [
            "Name",
            "AutomationId",
            "ControlTypeName",
            "ClassName",
            "IsEnabled",
            "IsOffscreen",
            "ProcessId",
        ]

        self.props_table.setRowCount(len(props))

        for i, prop_name in enumerate(props):
            value = self._selected_element.get_property(prop_name)

            name_item = QTableWidgetItem(prop_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.props_table.setItem(i, 0, name_item)

            value_item = QTableWidgetItem(str(value) if value else "<none>")
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.props_table.setItem(i, 1, value_item)

        self.props_table.resizeColumnsToContents()

    def _generate_selectors(self) -> None:
        """Generate selector strategies for element."""
        if not self._selected_element:
            self._strategies = []
            return

        from casare_rpa.presentation.canvas.selectors.selector_strategy import (
            filter_best_selectors,
            generate_selectors,
            validate_selector_uniqueness,
        )

        # Generate strategies
        strategies = generate_selectors(self._selected_element, self._parent_control)

        # Validate uniqueness
        for strategy in strategies:
            try:
                strategy.is_unique = validate_selector_uniqueness(
                    strategy, self._parent_control, timeout=1.0
                )
            except Exception:
                pass

        # Filter to best
        strategies = filter_best_selectors(strategies, max_count=8)

        # Convert to our format
        self._strategies = []
        for s in strategies:
            self._strategies.append(
                SelectorStrategy(
                    value=s.to_dict(),
                    selector_type=s.strategy,
                    score=s.score,
                    is_unique=s.is_unique,
                    description=s.description,
                )
            )

        logger.info(f"Generated {len(self._strategies)} desktop selectors")

    def _get_element_properties(self) -> dict[str, Any]:
        """Get all element properties as dict."""
        if not self._selected_element:
            return {}

        props = {}
        for prop in [
            "Name",
            "AutomationId",
            "ControlTypeName",
            "ClassName",
            "ProcessId",
        ]:
            value = self._selected_element.get_property(prop)
            if value:
                props[prop] = value

        return props

    def _get_hierarchy(self) -> list[dict[str, str]]:
        """Get parent hierarchy."""
        if not self._selected_element:
            return []

        hierarchy = []
        try:
            current = self._selected_element._control
            for _ in range(5):  # Max 5 levels
                parent = current.GetParentControl()
                if not parent or parent == current:
                    break

                hierarchy.append(
                    {
                        "name": parent.Name or "",
                        "control_type": parent.ControlTypeName or "",
                        "automation_id": parent.AutomationId or "",
                    }
                )
                current = parent

        except Exception as e:
            logger.debug(f"Failed to get hierarchy: {e}")

        return hierarchy

    async def test_selector(self, selector: str, selector_type: str) -> dict[str, Any]:
        """Test selector against desktop."""
        if not self._parent_control:
            return {"success": False, "error": "No desktop root"}

        try:
            # Parse selector if JSON
            if selector.startswith("{"):
                selector_dict = json.loads(selector)
            else:
                selector_dict = {"strategy": selector_type, "value": selector}

            import time

            from casare_rpa.desktop.selector import find_elements

            start = time.perf_counter()
            elements = find_elements(self._parent_control, selector_dict, max_depth=10)
            elapsed = (time.perf_counter() - start) * 1000

            return {
                "success": True,
                "count": len(elements),
                "time_ms": elapsed,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def highlight_selector(self, selector: str, selector_type: str) -> bool:
        """Highlight is not supported for desktop (would require drawing overlay)."""
        logger.debug("Desktop highlight not implemented")
        return False

    def clear(self) -> None:
        """Clear current state."""
        super().clear()
        self._selected_element = None
        self.props_table.setRowCount(0)
