"""
Selector Picker Dialog - PySide6 UI
Beautiful, modern dialog for managing and testing selectors

Epic 7.3 Migration: Migrated to THEME_V2/TOKENS_V2 (Cursor-like dark theme)
- Replaced THEME/TOKENS with THEME_V2/TOKENS_V2
- Zero hardcoded colors
- Zero animations/shadows
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
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme.helpers import (
    set_margins,
)
from casare_rpa.presentation.canvas.theme.utils import alpha
from casare_rpa.utils.selectors.selector_generator import (
    ElementFingerprint,
    SelectorStrategy,
    SelectorType,
)

# Theme aliases for consistency
THEME = THEME_V2
TOKENS = TOKENS_V2


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
        parent=None,
    ):
        super().__init__(parent)

        self.fingerprint = fingerprint
        self.test_callback = test_callback
        self.target_node = target_node
        self.target_property = target_property
        self.selected_strategy: SelectorStrategy | None = None

        self.setWindowTitle("Element Selector")
        self.setMinimumSize(
            TOKENS.sizes.dialog_lg_width,
            TOKENS.sizes.dialog_height_lg,
        )
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
        tag_label.setStyleSheet(f"color: {THEME.success};")
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
        self.selector_edit.setMaximumHeight(TOKENS.sizes.expression_editor_height - 20)
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
            f"padding: {TOKENS.spacing.md}px; "
            f"background: {THEME.bg_component}; "
            f"border: 1px solid {THEME.border}; "
            f"border-radius: {TOKENS.radius.sm}px; "
            f"color: {THEME.text_secondary};"
        )
        test_layout.addWidget(self.test_results)

        # Performance metrics
        self.perf_label = QLabel()
        self.perf_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}px;"
        )
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
        combo_drop_width = TOKENS.sizes.icon_sm + TOKENS.spacing.sm
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {THEME.bg_surface};
                color: {THEME.text_secondary};
            }}
            QGroupBox {{
                font-weight: {TOKENS.typography.weight_semibold};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                margin-top: {TOKENS.spacing.md}px;
                padding-top: {TOKENS.spacing.sm}px;
                background: {THEME.bg_component};
                color: {THEME.text_secondary};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: {TOKENS.spacing.sm}px;
                padding: 0 {TOKENS.spacing.sm}px;
                color: {THEME.primary};
            }}
            QLabel {{
                color: {THEME.text_secondary};
            }}
            QPushButton {{
                background: {THEME.bg_component};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.lg}px;
                border-radius: {TOKENS.radius.md}px;
                font-weight: {TOKENS.typography.weight_medium};
                min-width: {TOKENS.sizes.button_min_width}px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            QPushButton:pressed {{
                background: {THEME.bg_surface};
            }}
            QPushButton#useButton {{
                background: {THEME.success};
                color: {THEME.text_on_success};
                border: 1px solid {THEME.success};
            }}
            QPushButton#useButton:hover {{
                background: {THEME.success_hover};
            }}
            QPushButton#copyButton {{
                background: {THEME.primary};
                color: {THEME.text_on_primary};
                border: 1px solid {THEME.primary};
            }}
            QPushButton#copyButton:hover {{
                background: {THEME.primary_hover};
            }}
            QPushButton#cancelButton {{
                background: {THEME.error};
                color: {THEME.text_on_error};
                border: 1px solid {THEME.error_active};
            }}
            QPushButton#cancelButton:hover {{
                background: {THEME.error_hover};
            }}
            QPushButton#testButton, QPushButton#highlightButton {{
                background: {THEME.bg_component};
                color: {THEME.text_primary};
                border: 1px solid {THEME.border};
            }}
            QPushButton#testButton:hover, QPushButton#highlightButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            QListWidget {{
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                background: {THEME.bg_surface};
                outline: none;
                color: {THEME.text_secondary};
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.sm}px;
                border-bottom: 1px solid {THEME.border};
            }}
            QListWidget::item:selected {{
                background: {THEME.bg_selected};
                color: {THEME.text_on_primary};
            }}
            QListWidget::item:hover {{
                background: {THEME.bg_hover};
            }}
            QTextEdit {{
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.md}px;
                background: {THEME.input_bg};
                font-family: {TOKENS.typography.mono};
                color: {THEME.text_primary};
                selection-background-color: {THEME.primary};
                selection-color: {THEME.text_on_primary};
            }}
            QLineEdit {{
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.sm}px;
                background: {THEME.input_bg};
                color: {THEME.text_primary};
            }}
            QComboBox {{
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.md}px;
                padding: {TOKENS.spacing.sm}px;
                background: {THEME.input_bg};
                color: {THEME.text_primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: {combo_drop_width}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {TOKENS.spacing.xs}px solid transparent;
                border-right: {TOKENS.spacing.xs}px solid transparent;
                border-top: {TOKENS.spacing.sm}px solid {THEME.text_secondary};
                margin-right: {TOKENS.spacing.sm}px;
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.bg_elevated};
                color: {THEME.text_primary};
                selection-background-color: {THEME.bg_selected};
                selection-color: {THEME.text_on_primary};
                border: 1px solid {THEME.border};
            }}
            """
        )

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
            THEME.bg_canvas
            | THEME.bg_header
            | THEME.bg_surface
            | THEME.bg_component
            | THEME.bg_hover
            | THEME.bg_border
            | THEME.bg_surface
            | THEME.primary
            | THEME.primary_hover
            | THEME.primary
            | THEME.error
            | THEME.warning
            | THEME.primary
            | THEME.success
            | THEME.warning
            | THEME.error
            | THEME.info
            | THEME.node_running
            | THEME.node_idle
            if strategy.score >= 80
            else THEME.bg_canvas
            | THEME.bg_header
            | THEME.bg_surface
            | THEME.bg_component
            | THEME.bg_hover
            | THEME.bg_border
            | THEME.bg_surface
            | THEME.primary
            | THEME.primary_hover
            | THEME.primary
            | THEME.error
            | THEME.warning
            | THEME.primary
            | THEME.success
            | THEME.warning
            | THEME.error
            | THEME.info
            | THEME.node_running
            | THEME.node_idle
            if strategy.score >= 60
            else THEME.bg_canvas
            | THEME.bg_header
            | THEME.bg_surface
            | THEME.bg_component
            | THEME.bg_hover
            | THEME.bg_border
            | THEME.bg_surface
            | THEME.primary
            | THEME.primary_hover
            | THEME.primary
            | THEME.error
            | THEME.warning
            | THEME.primary
            | THEME.success
            | THEME.warning
            | THEME.error
            | THEME.info
            | THEME.node_running
            | THEME.node_idle
        )
        self.score_label.setText(f"{strategy.score:.1f} / 100")
        self.score_label.setStyleSheet(f"color: {score_color};")

        # Update uniqueness
        if strategy.is_unique:
            self.unique_label.setText("✓ Selector is unique (matches exactly 1 element)")
            self.unique_label.setStyleSheet(
                f"color: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
            )
        else:
            self.unique_label.setText("⚠ Selector may match multiple elements")
            self.unique_label.setStyleSheet(
                f"color: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
            )

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
                f"padding: {TOKENS.spacing.md}px; "
                f"background: {alpha(THEME.warning, 0.18)}; "
                f"border: 1px solid {THEME.warning}; "
                f"border-radius: {TOKENS.radius.sm}px; "
                f"color: {THEME.text_primary};"
            )
            return

        # Get current selector value (may have been edited)
        selector_value = self.selector_edit.toPlainText().strip()
        selector_type = self.type_combo.currentText()

        self.test_button.setEnabled(False)
        self.test_results.setText("⏳ Testing selector...")
        self.test_results.setStyleSheet(
            f"padding: {TOKENS.spacing.md}px; "
            f"background: {alpha(THEME.info, 0.18)}; "
            f"border: 1px solid {THEME.info}; "
            f"border-radius: {TOKENS.radius.sm}px; "
            f"color: {THEME.text_primary};"
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
                        f"padding: {TOKENS.spacing.md}px; "
                        f"background: {alpha(THEME.error, 0.18)}; "
                        f"color: {THEME.error}; "
                        f"border: 1px solid {THEME.error}; "
                        f"border-radius: {TOKENS.radius.sm}px;"
                    )
                elif count == 1:
                    self.test_results.setText(
                        f"✓ Found exactly 1 element\nExecution time: {time_ms:.2f}ms"
                    )
                    self.test_results.setStyleSheet(
                        f"padding: {TOKENS.spacing.md}px; "
                        f"background: {alpha(THEME.success, 0.18)}; "
                        f"color: {THEME.success}; "
                        f"border: 1px solid {THEME.success}; "
                        f"border-radius: {TOKENS.radius.sm}px;"
                    )
                else:
                    self.test_results.setText(
                        f"⚠ Found {count} elements (not unique)\nExecution time: {time_ms:.2f}ms"
                    )
                    self.test_results.setStyleSheet(
                        f"padding: {TOKENS.spacing.md}px; "
                        f"background: {alpha(THEME.warning, 0.18)}; "
                        f"color: {THEME.warning}; "
                        f"border: 1px solid {THEME.warning}; "
                        f"border-radius: {TOKENS.radius.sm}px;"
                    )

                # Update performance label
                self.perf_label.setText(f"Execution time: {time_ms:.2f}ms")
            else:
                error = result.get("error", "Unknown error")
                self.test_results.setText(f"❌ Test failed: {error}")
                self.test_results.setStyleSheet(
                    f"padding: {TOKENS.spacing.md}px; "
                    f"background: {alpha(THEME.error, 0.18)}; "
                    f"color: {THEME.error}; "
                    f"border: 1px solid {THEME.error}; "
                    f"border-radius: {TOKENS.radius.sm}px;"
                )

        except Exception as e:
            logger.error(f"Selector test error: {e}")
            self.test_results.setText(f"❌ Error: {str(e)}")
            self.test_results.setStyleSheet(
                f"padding: {TOKENS.spacing.md}px; "
                f"background: {alpha(THEME.error, 0.18)}; "
                f"color: {THEME.error}; "
                f"border: 1px solid {THEME.error}; "
                f"border-radius: {TOKENS.radius.sm}px;"
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
