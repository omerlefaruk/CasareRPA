"""
Desktop Selector Builder Dialog

Modern UiPath-inspired dialog for visually building desktop element selectors
with element picking, tree view, and multiple selector strategies.
"""

import json
from typing import Any

import uiautomation as auto
from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.desktop.element import DesktopElement
from casare_rpa.presentation.canvas.selectors.element_picker import (
    activate_element_picker,
)
from casare_rpa.presentation.canvas.selectors.element_tree_widget import (
    ElementTreeWidget,
)
from casare_rpa.presentation.canvas.selectors.selector_strategy import (
    SelectorStrategy,
    filter_best_selectors,
    generate_selectors,
    validate_selector_uniqueness,
)
from casare_rpa.presentation.canvas.selectors.selector_validator import (
    SelectorValidator,
)


class DesktopSelectorBuilder(QDialog):
    """
    Main dialog for building desktop element selectors.

    Features:
    - Element picker with hover highlighting
    - Hierarchical element tree viewer
    - Multiple selector generation strategies
    - Real-time validation
    - JSON selector editor
    - Properties panel
    """

    selector_selected = Signal(dict)  # Emits selected selector dictionary

    def __init__(self, parent=None, target_node=None, target_property: str = "selector"):
        super().__init__(parent)

        self.target_node = target_node
        self.target_property = target_property

        self.selected_element: DesktopElement | None = None
        self.root_element: DesktopElement | None = None
        self.parent_control: auto.Control | None = None
        self.selector_strategies: list[SelectorStrategy] = []
        self.selected_strategy: SelectorStrategy | None = None
        self.validator: SelectorValidator | None = None

        self.picker_overlay = None

        self._setup_ui()
        self._apply_styles()
        self._connect_signals()

        # Start with desktop root
        self._load_desktop_root()

        logger.info("Desktop Selector Builder initialized")

    def _setup_ui(self):
        """Setup UI layout"""
        self.setWindowTitle("Desktop Selector Builder")
        self.setMinimumSize(1000, 700)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with actions
        header = self._create_header()
        layout.addWidget(header)

        # Main content area with splitter
        main_splitter = QSplitter(Qt.Horizontal)

        # Left panel: Element tree
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)

        # Right panel: Properties and selectors
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)

        # Set initial sizes
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 1)

        layout.addWidget(main_splitter, 1)

        # Footer with action buttons
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create header with title and action buttons"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # Title
        title = QLabel("🎯 Desktop Selector Builder")
        title.setObjectName("titleLabel")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        layout.addStretch()

        # Pick Element button
        pick_btn = QPushButton("🎯 Pick Element")
        pick_btn.setObjectName("pickButton")
        pick_btn.clicked.connect(self._on_pick_element)
        pick_btn.setToolTip("Click to select an element from any application (Ctrl+Shift+F3)")
        layout.addWidget(pick_btn)

        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._on_refresh)
        refresh_btn.setToolTip("Refresh element tree")
        layout.addWidget(refresh_btn)

        # Validate button
        validate_btn = QPushButton("✓ Validate")
        validate_btn.clicked.connect(self._on_validate_all)
        validate_btn.setToolTip("Validate all selector strategies")
        layout.addWidget(validate_btn)

        return header

    def _create_left_panel(self) -> QWidget:
        """Create left panel with element tree"""
        panel = QGroupBox("Element Tree")

        layout = QVBoxLayout(panel)

        # Element tree widget
        self.tree_widget = ElementTreeWidget()
        self.tree_widget.element_selected.connect(self._on_tree_element_selected)
        layout.addWidget(self.tree_widget)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create right panel with properties and selectors"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Top: Selected element properties
        properties_group = self._create_properties_group()
        layout.addWidget(properties_group)

        # Middle: Generated selectors list
        selectors_group = self._create_selectors_group()
        layout.addWidget(selectors_group, 1)

        # Bottom: Selector JSON editor
        editor_group = self._create_editor_group()
        layout.addWidget(editor_group)

        return panel

    def _create_properties_group(self) -> QWidget:
        """Create properties display group"""
        group = QGroupBox("Selected Element Properties")
        layout = QVBoxLayout(group)

        # Properties table
        self.properties_table = QTableWidget()
        self.properties_table.setColumnCount(2)
        self.properties_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.properties_table.horizontalHeader().setStretchLastSection(True)
        self.properties_table.setAlternatingRowColors(True)
        self.properties_table.setMaximumHeight(150)
        layout.addWidget(self.properties_table)

        return group

    def _create_selectors_group(self) -> QWidget:
        """Create generated selectors list group"""
        group = QGroupBox("Generated Selectors")
        layout = QVBoxLayout(group)

        # Info label
        self.selectors_info_label = QLabel("No element selected")
        self.selectors_info_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.selectors_info_label)

        # Selectors list
        self.selectors_list = QListWidget()
        self.selectors_list.setAlternatingRowColors(True)
        self.selectors_list.currentItemChanged.connect(self._on_selector_changed)
        layout.addWidget(self.selectors_list)

        # Validation status
        self.validation_status_label = QLabel("")
        self.validation_status_label.setWordWrap(True)
        layout.addWidget(self.validation_status_label)

        return group

    def _create_editor_group(self) -> QWidget:
        """Create selector JSON editor group"""
        group = QGroupBox("Selector (JSON)")
        layout = QVBoxLayout(group)

        self.selector_editor = QTextEdit()
        self.selector_editor.setMaximumHeight(120)
        self.selector_editor.setFont(QFont("Consolas", 10))
        self.selector_editor.setPlaceholderText("Selector JSON will appear here...")
        layout.addWidget(self.selector_editor)

        return group

    def _create_footer(self) -> QWidget:
        """Create footer with action buttons"""
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(0, 0, 0, 0)

        # Cancel button (left)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addStretch()

        # Copy JSON button
        copy_btn = QPushButton("📋 Copy JSON")
        copy_btn.setObjectName("copyButton")
        copy_btn.clicked.connect(self._on_copy_json)
        copy_btn.setToolTip("Copy selector JSON to clipboard")
        layout.addWidget(copy_btn)

        # Use Selector button
        use_btn = QPushButton("✓ Use This Selector")
        use_btn.setObjectName("useButton")
        use_btn.setDefault(True)
        use_btn.clicked.connect(self._on_use_selector)
        use_btn.setToolTip("Use selected selector and close dialog")
        layout.addWidget(use_btn)

        return footer

    def _apply_styles(self):
        """Apply dark theme styling"""
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                color: #e0e0e0;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #252525;
                color: #0d7ebd;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
            QLabel#titleLabel {
                color: #0d7ebd;
            }
            QPushButton {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 8px 16px;
                color: #e0e0e0;
                font-weight: 500;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border-color: #0d7ebd;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton#pickButton {
                background-color: #0d7ebd;
                border-color: #0d7ebd;
                font-weight: bold;
                color: white;
            }
            QPushButton#pickButton:hover {
                background-color: #0e8dd6;
            }
            QPushButton#useButton {
                background-color: #10b981;
                color: white;
                border: 1px solid #059669;
            }
            QPushButton#useButton:hover {
                background-color: #059669;
            }
            QPushButton#copyButton {
                background-color: #3b82f6;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton#copyButton:hover {
                background-color: #2563eb;
            }
            QPushButton#cancelButton {
                background-color: #ef4444;
                color: white;
                border: 1px solid #dc2626;
            }
            QPushButton#cancelButton:hover {
                background-color: #dc2626;
            }
            QListWidget {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #0d7ebd;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QTextEdit {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 8px;
                background-color: #1a1a1a;
                color: #e0e0e0;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QTableWidget {
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                background-color: #1e1e1e;
                color: #e0e0e0;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #0d7ebd;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #e0e0e0;
                padding: 6px;
                border: 1px solid #3c3c3c;
                font-weight: bold;
            }
        """)

    def _connect_signals(self):
        """Connect internal signals"""
        pass

    def _load_desktop_root(self):
        """Load desktop root as initial tree"""
        try:
            root_control = auto.GetRootControl()
            self.root_element = DesktopElement(root_control)
            self.parent_control = root_control
            self.validator = SelectorValidator(root_control)

            # Load tree
            self.tree_widget.load_tree(self.root_element)

            logger.info("Loaded desktop root")

        except Exception as e:
            logger.error(f"Failed to load desktop root: {e}")

    def _on_pick_element(self):
        """Handle pick element button click"""
        logger.info("Starting element picker")

        def on_element_selected(element: DesktopElement):
            logger.info(f"Element picked: {element}")
            self.selected_element = element
            self._update_for_selected_element()
            self.picker_overlay = None

        def on_cancelled():
            logger.info("Element picking cancelled")
            self.picker_overlay = None

        # Activate picker
        self.picker_overlay = activate_element_picker(on_element_selected, on_cancelled)

    def _on_refresh(self):
        """Handle refresh button click"""
        if self.root_element:
            self.tree_widget.refresh()
            logger.info("Tree refreshed")

    def _on_tree_element_selected(self, element: DesktopElement):
        """Handle element selection from tree"""
        logger.info(f"Element selected from tree: {element}")
        self.selected_element = element
        self._update_for_selected_element()

    def _update_for_selected_element(self):
        """Update UI for selected element"""
        if not self.selected_element:
            return

        logger.debug("Updating UI for selected element")

        # Update properties table
        self._update_properties_table()

        # Generate selector strategies
        self._generate_selectors()

        # Update selectors list
        self._update_selectors_list()

    def _update_properties_table(self):
        """Update properties table with selected element properties"""
        if not self.selected_element:
            self.properties_table.setRowCount(0)
            return

        # Common properties to display
        properties_to_show = [
            "Name",
            "AutomationId",
            "ControlTypeName",
            "ClassName",
            "IsEnabled",
            "IsOffscreen",
            "ProcessId",
        ]

        self.properties_table.setRowCount(len(properties_to_show))

        for i, prop_name in enumerate(properties_to_show):
            prop_value = self.selected_element.get_property(prop_name)

            name_item = QTableWidgetItem(prop_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.properties_table.setItem(i, 0, name_item)

            value_item = QTableWidgetItem(str(prop_value) if prop_value is not None else "<none>")
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.properties_table.setItem(i, 1, value_item)

        self.properties_table.resizeColumnsToContents()

    def _generate_selectors(self):
        """Generate selector strategies for selected element"""
        if not self.selected_element:
            self.selector_strategies = []
            return

        logger.info("Generating selector strategies")

        # Generate strategies
        self.selector_strategies = generate_selectors(self.selected_element, self.parent_control)

        # Validate uniqueness for each strategy
        for strategy in self.selector_strategies:
            try:
                strategy.is_unique = validate_selector_uniqueness(
                    strategy, self.parent_control, timeout=1.0
                )
            except Exception as e:
                logger.debug(f"Selector uniqueness validation failed: {e}")

        # Filter to best strategies
        self.selector_strategies = filter_best_selectors(self.selector_strategies, max_count=8)

        logger.info(f"Generated {len(self.selector_strategies)} selector strategies")

    def _update_selectors_list(self):
        """Update selectors list widget"""
        self.selectors_list.clear()

        if not self.selector_strategies:
            self.selectors_info_label.setText("No selectors generated")
            return

        self.selectors_info_label.setText(
            f"{len(self.selector_strategies)} strategies found, sorted by reliability"
        )

        for strategy in self.selector_strategies:
            item = QListWidgetItem()

            # Format display text
            confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(
                strategy.confidence.value, "⚪"
            )

            unique_text = " ✓ Unique" if strategy.is_unique else ""
            display_text = f"{confidence_icon} {strategy.description} (Score: {strategy.score:.0f}){unique_text}"

            item.setText(display_text)
            item.setData(Qt.UserRole, strategy)

            self.selectors_list.addItem(item)

        # Select first item
        if self.selectors_list.count() > 0:
            self.selectors_list.setCurrentRow(0)

    def _on_selector_changed(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle selector selection change"""
        if not current:
            return

        strategy: SelectorStrategy = current.data(Qt.UserRole)
        self.selected_strategy = strategy

        logger.debug(f"Selector changed: {strategy.description}")

        # Update JSON editor
        selector_dict = strategy.to_dict()
        selector_json = json.dumps(selector_dict, indent=2)
        self.selector_editor.setPlainText(selector_json)

        # Update validation status
        self._update_validation_status(strategy)

    def _update_validation_status(self, strategy: SelectorStrategy):
        """Update validation status label"""
        if strategy.is_unique:
            status_text = "✓ Selector is unique (matches exactly 1 element)"
            status_color = Theme.get_colors().success
        else:
            status_text = "⚠ Selector may match multiple elements"
            status_color = Theme.get_colors().warning

        self.validation_status_label.setText(status_text)
        self.validation_status_label.setStyleSheet(
            f"color: {status_color}; font-weight: bold; padding: 8px;"
        )

    def _on_validate_all(self):
        """Validate all selector strategies"""
        if not self.validator or not self.selector_strategies:
            return

        logger.info("Validating all strategies")

        for i, strategy in enumerate(self.selector_strategies):
            result = self.validator.validate(strategy.to_dict(), find_all=True)

            # Update strategy with validation results
            strategy.is_unique = result.is_unique

            # Update list item
            item = self.selectors_list.item(i)
            if item:
                current_text = item.text()
                # Remove old unique marker
                current_text = current_text.replace(" ✓ Unique", "").replace(" ⚠ Multiple", "")

                if result.is_unique:
                    current_text += " ✓ Unique"
                elif result.element_count > 1:
                    current_text += f" ⚠ Multiple ({result.element_count})"

                item.setText(current_text)

        logger.info("Validation complete")

    def _on_copy_json(self):
        """Copy selector JSON to clipboard"""
        if not self.selected_strategy:
            logger.warning("No selector selected to copy")
            return

        selector_json = self.selector_editor.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(selector_json)

        logger.info("Selector JSON copied to clipboard")

    def _on_use_selector(self):
        """Use the selected selector"""
        if not self.selected_strategy:
            logger.warning("No selector selected")
            return

        selector_dict = self.selected_strategy.to_dict()

        # Auto-paste to target node if provided
        if self.target_node and self.target_property:
            try:
                widget = self.target_node.get_widget(self.target_property)
                if widget:
                    # Convert to JSON string for text input
                    selector_json = json.dumps(selector_dict)
                    widget.set_value(selector_json)
                    logger.info(
                        f"Auto-pasted selector to {self.target_node.name()}.{self.target_property}"
                    )
            except Exception as e:
                logger.error(f"Failed to auto-paste selector: {e}")

        # Emit signal
        self.selector_selected.emit(selector_dict)

        # Close dialog
        self.accept()

    def get_selected_selector(self) -> dict[str, Any] | None:
        """Get the selected selector dictionary"""
        if self.selected_strategy:
            return self.selected_strategy.to_dict()
        return None
