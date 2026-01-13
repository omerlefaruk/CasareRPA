"""
Selector Picker Dialog - PySide6 UI
Beautiful, modern dialog for managing and testing selectors
"""

from collections.abc import Callable

from loguru import logger
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget)

from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_margins)
from casare_rpa.utils.selectors.selector_generator import (
    ElementFingerprint,
    SelectorStrategy,
    SelectorType)

from ..theme_system.tokens import TOKENS
from ..ui.theme import Theme


class SelectorDialog(QDialog):
    """
    Modern dialog for selecting and testing element selectors
    Shows all generated strategies with validation and preview
    """

    selector_selected = Signal(str, str)  # (selector_value, selector_type)

    def __init__(
        self,
        fingerprint: ElementFingerprint,
        test_callback: Callable | None = None,
        target_node=None,
        target_property: str = "selector",
        parent=None):
        super().__init__(parent)

        self.fingerprint = fingerprint
        self.test_callback = test_callback
        self.target_node = target_node
        self.target_property = target_property
        self.selected_strategy: SelectorStrategy | None = None

        self.setWindowTitle("Element Selector")
        self.setMinimumSize(
            TOKENS.sizes.dialog_lg,
            TOKENS.sizes.dialog_lg)
        self.setup_ui()
        self.apply_styles()
        self.populate_data()

    def setup_ui(self):
        """Build the UI layout"""
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS.spacing.lg)
        layout.setContentsMargins(*TOKENS.margin.dialog)

        # Header with element info
        header = self._create_header()
        layout.addWidget(header)

        # Main content: splitter with selectors list and details
        splitter = QSplitter(Qt.Horizontal)

        # Left: Selector strategies list
        left_panel = self._create_selectors_panel()
        splitter.addWidget(left_panel)

        # Right: Details and testing
        right_panel = self._create_details_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter, 1)

        # Footer with actions
        footer = self._create_footer()
        layout.addWidget(footer)

    def _create_header(self) -> QWidget:
        """Create header with element information"""
        header = QGroupBox("Selected Element")
        layout = QVBoxLayout(header)

        # Element tag display
        tag_label = QLabel(f"<{self.fingerprint.tag_name}>")
        tag_label.setFont(QFont("Consolas", 14, QFont.Bold))
        cc = Theme.get_canvas_colors()
        tag_label.setStyleSheet(f"color: {cc.status_success};")
        layout.addWidget(tag_label)

        # Element details in grid
        details_widget = QWidget()
        details_layout = QHBoxLayout(details_widget)
        set_margins(details_layout, (0, 0, 0, 0))

        # ID
        if self.fingerprint.element_id:
            id_label = QLabel(f"<b>ID:</b> {self.fingerprint.element_id}")
            details_layout.addWidget(id_label)

        # Classes
        if self.fingerprint.class_names:
            classes_text = ", ".join(self.fingerprint.class_names[:3])
            class_label = QLabel(f"<b>Classes:</b> {classes_text}")
            details_layout.addWidget(class_label)

        # Text preview
        if self.fingerprint.text_content:
            text_preview = self.fingerprint.text_content[:50]
            if len(self.fingerprint.text_content) > 50:
                text_preview += "..."
            text_label = QLabel(f"<b>Text:</b> {text_preview}")
            details_layout.addWidget(text_label)

        details_layout.addStretch()
        layout.addWidget(details_widget)

        return header

    def _create_selectors_panel(self) -> QWidget:
        """Create left panel with selector strategies list"""
        panel = QGroupBox("Available Selectors")
        layout = QVBoxLayout(panel)

        # Info label
        info = QLabel(f"{len(self.fingerprint.selectors)} strategies found, sorted by reliability")
        info.setStyleSheet(f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;")
        layout.addWidget(info)

        # List of selectors
        self.selectors_list = QListWidget()
        self.selectors_list.setAlternatingRowColors(True)
        self.selectors_list.currentItemChanged.connect(self._on_selector_changed)
        layout.addWidget(self.selectors_list)

        return panel

    def _create_details_panel(self) -> QWidget:
        """Create right panel with selector details and testing"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(*TOKENS.margin.none)

        # Selector details group
        details_group = QGroupBox("Selector Details")
        details_layout = QVBoxLayout(details_group)

        # Type selector
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["xpath", "css", "aria", "data_attr", "text"])
        self.type_combo.setEnabled(False)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        details_layout.addLayout(type_layout)

        # Selector value (editable)
        details_layout.addWidget(QLabel("Selector:"))
        self.selector_edit = QTextEdit()
        self.selector_edit.setMaximumHeight(TOKENS.sizes.panel_min - 20)
        self.selector_edit.setFont(QFont(TOKENS.typography.mono, TOKENS.typography.body))
        details_layout.addWidget(self.selector_edit)

        # Score display
        score_layout = QHBoxLayout()
        score_layout.addWidget(QLabel("Reliability Score:"))
        self.score_label = QLabel("--")
        self.score_label.setFont(QFont("Arial", 12, QFont.Bold))
        score_layout.addWidget(self.score_label)
        score_layout.addStretch()
        details_layout.addLayout(score_layout)

        # Uniqueness indicator
        self.unique_label = QLabel()
        self.unique_label.setFont(QFont("Arial", 10))
        details_layout.addWidget(self.unique_label)

        layout.addWidget(details_group)

        # Testing group
        test_group = QGroupBox("Test Selector")
        test_layout = QVBoxLayout(test_group)

        # Test button
        test_btn_layout = QHBoxLayout()
        self.test_button = QPushButton("🔍 Test Selector")
        self.test_button.setObjectName("testButton")
        self.test_button.clicked.connect(self._on_test_selector)
        test_btn_layout.addWidget(self.test_button)

        self.highlight_button = QPushButton("✨ Highlight in Browser")
        self.highlight_button.setObjectName("highlightButton")
        self.highlight_button.clicked.connect(self._on_highlight_selector)
        test_btn_layout.addWidget(self.highlight_button)
        test_layout.addLayout(test_btn_layout)

        # Test results
        self.test_results = QLabel("Click 'Test Selector' to validate")
        self.test_results.setWordWrap(True)
        self.test_results.setStyleSheet(
            "padding: {TOKENS.spacing.md}px; background: #2d2d2d; border-radius: {TOKENS.radius.sm}px; color: {THEME.text_secondary};"
        )
        test_layout.addWidget(self.test_results)

        # Performance metrics
        self.perf_label = QLabel()
        self.perf_label.setStyleSheet("color: #666; font-size: {TOKENS.typography.caption}px;")
        test_layout.addWidget(self.perf_label)

        layout.addWidget(test_group)
        layout.addStretch()

        return panel

    def _create_footer(self) -> QWidget:
        """Create footer with action buttons"""
        footer = QWidget()
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(*TOKENS.margin.none)

        # Cancel button (left side)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        layout.addStretch()

        # Copy button
        copy_btn = QPushButton("📋 Copy")
        copy_btn.setObjectName("copyButton")
        copy_btn.clicked.connect(self._on_copy_selector)
        layout.addWidget(copy_btn)

        # Use button
        use_btn = QPushButton("✓ Use This Selector")
        use_btn.setObjectName("useButton")
        use_btn.setDefault(True)
        use_btn.clicked.connect(self._on_use_selector)
        layout.addWidget(use_btn)

        return footer

    def apply_styles(self):
        """Apply dark mode styling"""
        self.setStyleSheet("""
            QDialog {
                background: {THEME.bg_darkest};
                color: {THEME.text_secondary};
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3a3a3a;
                border-radius: {TOKENS.radius.md}px;
                margin-top: 12px;
                padding-top: 8px;
                background: #252525;
                color: {THEME.text_secondary};
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
                color: #60a5fa;
            }
            QLabel {
                color: {THEME.text_secondary};
            }
            QPushButton {
                background: #3a3a3a;
                color: {THEME.text_secondary};
                border: 1px solid #4a4a4a;
                padding: {TOKENS.spacing.md}px 16px;
                border-radius: {TOKENS.radius.md}px;
                font-weight: TOKENS.sizes.dialog_md;
                min-width: {80}px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border: 1px solid #5a5a5a;
            }
            QPushButton:pressed {
                background: #2a2a2a;
            }
            QPushButton#useButton {
                background: #10b981;
                color: white;
                border: 1px solid #059669;
            }
            QPushButton#useButton:hover {
                background: #059669;
            }
            QPushButton#useButton:pressed {
                background: #047857;
            }
            QPushButton#copyButton {
                background: #3b82f6;
                color: white;
                border: 1px solid #2563eb;
            }
            QPushButton#copyButton:hover {
                background: #2563eb;
            }
            QPushButton#copyButton:pressed {
                background: #1d4ed8;
            }
            QPushButton#cancelButton {
                background: #ef4444;
                color: white;
                border: 1px solid #dc2626;
            }
            QPushButton#cancelButton:hover {
                background: #dc2626;
            }
            QPushButton#cancelButton:pressed {
                background: #b91c1c;
            }
            QPushButton#testButton, QPushButton#highlightButton {
                background: #3a3a3a;
                color: {THEME.text_secondary};
                border: 1px solid #4a4a4a;
            }
            QPushButton#testButton:hover, QPushButton#highlightButton:hover {
                background: #4a4a4a;
                border: 1px solid #5a5a5a;
            }
            QPushButton#testButton:pressed, QPushButton#highlightButton:pressed {
                background: #2a2a2a;
            }
            QListWidget {
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.md}px;
                background: #252525;
                outline: none;
                color: {THEME.text_secondary};
            }
            QListWidget::item {
                padding: {TOKENS.spacing.md}px;
                border-bottom: 1px solid #3a3a3a;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QListWidget::item:hover {
                background: #2a2a2a;
            }
            QTextEdit {
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.md}px;
                background: #1a1a1a;
                font-family: 'Consolas', 'Courier New', monospace;
                color: {THEME.text_secondary};
                selection-background-color: #3b82f6;
            }
            QLineEdit {
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.md}px;
                background: #252525;
                color: {THEME.text_secondary};
            }
            QComboBox {
                border: 1px solid #3a3a3a;
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.sm}px;
                background: #252525;
                color: {THEME.text_secondary};
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid {THEME.text_secondary};
                margin-right: 6px;
            }
            QComboBox QAbstractItemView {
                background: #252525;
                color: {THEME.text_secondary};
                selection-background-color: #3b82f6;
                border: 1px solid #3a3a3a;
            }
        """)

    def populate_data(self):
        """Populate selectors list with strategies"""
        for strategy in self.fingerprint.selectors:
            item = QListWidgetItem()

            # Format display text
            type_icon = {
                SelectorType.XPATH: "🎯",
                SelectorType.CSS: "🎨",
                SelectorType.ARIA: "♿",
                SelectorType.DATA_ATTR: "📊",
                SelectorType.TEXT: "📝",
            }.get(strategy.selector_type, "•")

            score_color = "🟢" if strategy.score >= 80 else "🟡" if strategy.score >= 60 else "🔴"

            display_text = f"{type_icon} {strategy.selector_type.value.upper()} {score_color} {strategy.score:.0f}"
            if strategy.is_unique:
                display_text += " ✓ Unique"

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

        # Update details panel
        self.type_combo.setCurrentText(strategy.selector_type.value)
        self.selector_edit.setPlainText(strategy.value)

        # Update score with color
        score_color = (
            Theme.get_colors().status_success
            if strategy.score >= 80
            else Theme.get_colors().status_warning
            if strategy.score >= 60
            else Theme.get_colors().status_error
        )
        self.score_label.setText(f"{strategy.score:.1f} / 100")
        self.score_label.setStyleSheet(f"color: {score_color};")

        # Update uniqueness
        if strategy.is_unique:
            self.unique_label.setText("✓ Selector is unique (matches exactly 1 element)")
            self.unique_label.setStyleSheet(f"color: {Theme.get_colors().status_success};")
        else:
            self.unique_label.setText("⚠ Selector may match multiple elements")
            self.unique_label.setStyleSheet(f"color: {Theme.get_colors().status_warning};")

        # Update performance if available
        if strategy.execution_time_ms > 0:
            self.perf_label.setText(f"Last execution: {strategy.execution_time_ms:.2f}ms")
        else:
            self.perf_label.setText("")

    def _on_test_selector(self):
        """Test the current selector against the page"""
        if not self.selected_strategy or not self.test_callback:
            self.test_results.setText("⚠ Testing not available")
            self.test_results.setStyleSheet(
                "padding: {TOKENS.spacing.md}px; background: #fff3cd; border-radius: {TOKENS.radius.sm}px;"
            )
            return

        # Get current selector value (may have been edited)
        selector_value = self.selector_edit.toPlainText().strip()
        selector_type = self.type_combo.currentText()

        self.test_button.setEnabled(False)
        self.test_results.setText("⏳ Testing selector...")
        self.test_results.setStyleSheet(
            "padding: {TOKENS.spacing.md}px; background: #e3f2fd; border-radius: {TOKENS.radius.sm}px;"
        )

        # Use QTimer to call async test function
        QTimer.singleShot(100, lambda: self._do_test(selector_value, selector_type))

    def _do_test(self, selector_value: str, selector_type: str):
        """Actually perform the test"""
        try:
            # Call the test callback (should be async-safe)
            result = self.test_callback(selector_value, selector_type)

            if result.get("success"):
                count = result.get("count", 0)
                time_ms = result.get("time", 0)

                if count == 0:
                    self.test_results.setText("❌ No elements found")
                    self.test_results.setStyleSheet(
                        "padding: {TOKENS.spacing.md}px; background: #3d1e1e; color: #ef4444; border: 1px solid #7f1d1d; border-radius: {TOKENS.radius.sm}px;"
                    )
                elif count == 1:
                    self.test_results.setText(
                        f"✓ Found exactly 1 element\nExecution time: {time_ms:.2f}ms"
                    )
                    self.test_results.setStyleSheet(
                        "padding: {TOKENS.spacing.md}px; background: #1e3d2e; color: #10b981; border: 1px solid #065f46; border-radius: {TOKENS.radius.sm}px;"
                    )
                else:
                    self.test_results.setText(
                        f"⚠ Found {count} elements (not unique)\nExecution time: {time_ms:.2f}ms"
                    )
                    self.test_results.setStyleSheet(
                        "padding: {TOKENS.spacing.md}px; background: #3d3520; color: #fbbf24; border: 1px solid #78350f; border-radius: {TOKENS.radius.sm}px;"
                    )

                # Update performance label
                self.perf_label.setText(f"Execution time: {time_ms:.2f}ms")
            else:
                error = result.get("error", "Unknown error")
                self.test_results.setText(f"❌ Test failed: {error}")
                self.test_results.setStyleSheet(
                    "padding: {TOKENS.spacing.md}px; background: #3d1e1e; color: #ef4444; border: 1px solid #7f1d1d; border-radius: {TOKENS.radius.sm}px;"
                )

        except Exception as e:
            logger.error(f"Selector test error: {e}")
            self.test_results.setText(f"❌ Error: {str(e)}")
            self.test_results.setStyleSheet(
                "padding: {TOKENS.spacing.md}px; background: #3d1e1e; color: #ef4444; border: 1px solid #7f1d1d; border-radius: {TOKENS.radius.sm}px;"
            )

        finally:
            self.test_button.setEnabled(True)

    def _on_highlight_selector(self):
        """Highlight matching elements in the browser"""
        if not self.selected_strategy:
            return

        selector_value = self.selector_edit.toPlainText().strip()
        selector_type = self.type_combo.currentText()

        # Emit signal for parent to handle highlighting
        self.selector_selected.emit(selector_value, f"highlight:{selector_type}")

    def _on_copy_selector(self):
        """Copy selector to clipboard and close dialog"""
        if not self.selected_strategy:
            return

        from PySide6.QtWidgets import QApplication

        selector_value = self.selector_edit.toPlainText().strip()
        clipboard = QApplication.clipboard()
        clipboard.setText(selector_value)

        logger.info(f"Selector copied to clipboard: {selector_value}")

        # Close the dialog
        self.accept()

    def _on_use_selector(self):
        """Accept and use the selected selector - auto-paste if target node provided"""
        if not self.selected_strategy:
            return

        selector_value = self.selector_edit.toPlainText().strip()
        selector_type = self.type_combo.currentText()

        # Auto-paste to target node if provided
        if self.target_node and self.target_property:
            try:
                widget = self.target_node.get_widget(self.target_property)
                if widget:
                    widget.set_value(selector_value)
                    logger.info(
                        f"Auto-pasted selector to {self.target_node.name()}.{self.target_property}"
                    )
                else:
                    logger.warning(
                        f"Widget '{self.target_property}' not found on node {self.target_node.name()}"
                    )
            except Exception as e:
                logger.error(f"Failed to auto-paste selector: {e}")

        self.selector_selected.emit(selector_value, selector_type)
        self.accept()

    def get_selected_selector(self) -> tuple[str, str]:
        """Get the selected selector value and type"""
        if not self.selected_strategy:
            return "", ""

        return (self.selector_edit.toPlainText().strip(), self.type_combo.currentText())
