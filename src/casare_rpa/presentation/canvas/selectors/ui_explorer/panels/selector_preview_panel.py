"""
Selector Preview Panel for UI Explorer.

Displays the current selector in various formats (XML, CSS, XPath)
with syntax highlighting and editing capabilities.

Features:
- Copy button to clipboard
- Edit toggle for readonly/editable mode
- Format dropdown: XML, CSS, XPath
- Monospace font (Consolas/Monaco)
- XML syntax highlighting
"""

from typing import Optional

from loguru import logger
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.ui_explorer.models.selector_model import (
    SelectorModel,
)
from casare_rpa.presentation.canvas.selectors.ui_explorer.widgets.xml_highlighter import (
    XMLHighlighter,
)


class SelectorPreviewPanel(QFrame):
    """
    Selector preview panel with syntax highlighting.

    Shows the current selector in XML/CSS/XPath format with:
    - Copy to clipboard button
    - Edit toggle for manual editing
    - Format selection dropdown
    - XML syntax highlighting via XMLHighlighter

    Layout:
    +--------------------------------------------------+
    | [Copy] [Edit] [Format: XML v]                    |
    +--------------------------------------------------+
    | <html app='msedge.exe' title='Rpa Challenge' />  |
    | <button class='btn-primary' id='submit' />       |
    +--------------------------------------------------+

    Signals:
        selector_changed: Emitted when user manually edits selector (str)
        format_changed: Emitted when format dropdown changes (str)
        copy_clicked: Emitted when copy button clicked
    """

    selector_changed = Signal(str)
    format_changed = Signal(str)
    copy_clicked = Signal()

    # Available formats
    FORMAT_XML = "xml"
    FORMAT_CSS = "css"
    FORMAT_XPATH = "xpath"

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the selector preview panel.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._selector_model: SelectorModel | None = None
        self._current_format = self.FORMAT_XML
        self._is_editable = False

        self.setFixedHeight(100)
        self._setup_ui()
        self._connect_signals()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        # Header row with buttons
        header = QHBoxLayout()
        header.setSpacing(8)

        # Preview label
        preview_label = QLabel("PREVIEW:")
        preview_label.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        header.addWidget(preview_label)

        header.addStretch()

        # Copy button
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setFixedSize(60, 24)
        self._copy_btn.setToolTip("Copy selector to clipboard (Ctrl+C)")
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a5a5a;
            }
            QPushButton:pressed {
                background: #2a2a2a;
            }
        """)
        header.addWidget(self._copy_btn)

        # Edit toggle button
        self._edit_btn = QPushButton("Edit")
        self._edit_btn.setFixedSize(60, 24)
        self._edit_btn.setCheckable(True)
        self._edit_btn.setToolTip("Toggle manual editing mode")
        self._edit_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a5a5a;
            }
            QPushButton:checked {
                background: #3b82f6;
                border-color: #60a5fa;
                color: white;
            }
            QPushButton:pressed {
                background: #2a2a2a;
            }
        """)
        header.addWidget(self._edit_btn)

        # Format dropdown
        format_label = QLabel("Format:")
        format_label.setStyleSheet("color: #888888; font-size: 11px;")
        header.addWidget(format_label)

        self._format_combo = QComboBox()
        self._format_combo.setFixedWidth(80)
        self._format_combo.addItem("XML", self.FORMAT_XML)
        self._format_combo.addItem("CSS", self.FORMAT_CSS)
        self._format_combo.addItem("XPath", self.FORMAT_XPATH)
        self._format_combo.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                color: #e0e0e0;
                font-size: 11px;
                padding: 2px 8px;
            }
            QComboBox:hover {
                border-color: #5a5a5a;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid #888888;
                margin-right: 4px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                border: 1px solid #4a4a4a;
                color: #e0e0e0;
                selection-background-color: #3b82f6;
            }
        """)
        header.addWidget(self._format_combo)

        layout.addLayout(header)

        # Preview text area with syntax highlighting
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        self._preview_text.setPlaceholderText("<html app='...' title='...' />\n<element ... />")

        # Set monospace font
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Monaco", 10)
            if not font.exactMatch():
                font = QFont("Courier New", 10)
        self._preview_text.setFont(font)

        self._preview_text.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
            QTextEdit:focus {
                border-color: #3b82f6;
            }
        """)

        layout.addWidget(self._preview_text)

        # Apply XML syntax highlighter
        self._highlighter = XMLHighlighter(self._preview_text.document())

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._copy_btn.clicked.connect(self._on_copy_clicked)
        self._edit_btn.toggled.connect(self._on_edit_toggled)
        self._format_combo.currentIndexChanged.connect(self._on_format_changed)
        self._preview_text.textChanged.connect(self._on_text_changed)

    def _apply_styles(self) -> None:
        """Apply panel styling."""
        self.setStyleSheet("""
            SelectorPreviewPanel {
                background: #252525;
                border-top: 1px solid #3a3a3a;
            }
        """)

    def _on_copy_clicked(self) -> None:
        """Handle copy button click."""
        text = self._preview_text.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.copy_clicked.emit()
            logger.debug(f"Copied selector to clipboard: {text[:50]}...")

    def _on_edit_toggled(self, checked: bool) -> None:
        """
        Handle edit toggle.

        Args:
            checked: Whether edit mode is enabled
        """
        self._is_editable = checked
        self._preview_text.setReadOnly(not checked)

        if checked:
            self._preview_text.setStyleSheet("""
                QTextEdit {
                    background: #1f1f1f;
                    border: 1px solid #3b82f6;
                    border-radius: 4px;
                    padding: 6px;
                    color: #e0e0e0;
                }
            """)
            self._preview_text.setFocus()
        else:
            self._preview_text.setStyleSheet("""
                QTextEdit {
                    background: #1a1a1a;
                    border: 1px solid #3a3a3a;
                    border-radius: 4px;
                    padding: 6px;
                    color: #e0e0e0;
                }
            """)

        logger.debug(f"Edit mode: {checked}")

    def _on_format_changed(self, index: int) -> None:
        """
        Handle format dropdown change.

        Args:
            index: Selected index
        """
        format_value = self._format_combo.itemData(index)
        if format_value and format_value != self._current_format:
            self._current_format = format_value
            self.format_changed.emit(format_value)
            self.update_preview()
            logger.debug(f"Format changed to: {format_value}")

    def _on_text_changed(self) -> None:
        """Handle manual text changes when in edit mode."""
        if self._is_editable:
            self.selector_changed.emit(self._preview_text.toPlainText())

    # =========================================================================
    # Public API
    # =========================================================================

    def set_selector_model(self, model: SelectorModel) -> None:
        """
        Set the selector model for preview updates.

        Args:
            model: SelectorModel instance
        """
        # Disconnect old model if present
        if self._selector_model:
            try:
                self._selector_model.preview_updated.disconnect(self._on_model_preview_updated)
            except RuntimeError:
                pass  # Signal was not connected

        self._selector_model = model

        # Connect new model
        if model:
            model.preview_updated.connect(self._on_model_preview_updated)

        logger.debug("SelectorModel connected to preview panel")

    def _on_model_preview_updated(self, xml_string: str) -> None:
        """
        Handle preview update from model.

        Args:
            xml_string: XML selector string from model
        """
        if not self._is_editable:
            self.update_preview()

    def update_preview(self) -> None:
        """Update preview based on current model and format."""
        if not self._selector_model:
            self._preview_text.setPlainText("")
            return

        # Get selector in selected format
        if self._current_format == self.FORMAT_XML:
            text = self._selector_model.to_xml()
        elif self._current_format == self.FORMAT_CSS:
            text = self._selector_model.to_selector_string()
        else:  # XPath
            text = self._generate_xpath()

        self._preview_text.setPlainText(text)

    def _generate_xpath(self) -> str:
        """
        Generate XPath from current model.

        Returns:
            XPath selector string
        """
        if not self._selector_model:
            return ""

        included = self._selector_model.get_included_attributes()
        if not included:
            return ""

        # Get tag
        tag = "*"
        for attr in included:
            if attr.name == "tag":
                tag = attr.value
                break

        # Build predicates
        predicates = []
        for attr in included:
            if attr.name == "tag":
                continue
            if not attr.is_empty:
                value = attr.value.replace("'", "\\'")
                predicates.append(f"@{attr.name}='{value}'")

        if predicates:
            return f"//{tag}[{' and '.join(predicates)}]"
        return f"//{tag}"

    def set_format(self, format_type: str) -> None:
        """
        Set the preview format.

        Args:
            format_type: "xml", "css", or "xpath"
        """
        if format_type not in (self.FORMAT_XML, self.FORMAT_CSS, self.FORMAT_XPATH):
            logger.warning(f"Unknown format type: {format_type}")
            return

        self._current_format = format_type

        # Update combo box
        for i in range(self._format_combo.count()):
            if self._format_combo.itemData(i) == format_type:
                self._format_combo.setCurrentIndex(i)
                break

        self.update_preview()

    def get_format(self) -> str:
        """
        Get current preview format.

        Returns:
            Current format: "xml", "css", or "xpath"
        """
        return self._current_format

    def get_selector_text(self) -> str:
        """
        Get the current selector text.

        Returns:
            Current selector string
        """
        return self._preview_text.toPlainText()

    def set_preview(self, text: str) -> None:
        """
        Set the preview text directly.

        Args:
            text: Selector text to display
        """
        self._preview_text.setPlainText(text)

    def set_editable(self, editable: bool) -> None:
        """
        Set whether the preview is editable.

        Args:
            editable: Whether to enable editing
        """
        self._edit_btn.setChecked(editable)
        # The toggle handler will do the rest

    def is_editable(self) -> bool:
        """
        Check if preview is in edit mode.

        Returns:
            True if editable
        """
        return self._is_editable

    def clear(self) -> None:
        """Clear the preview text."""
        self._preview_text.clear()

    def get_highlighter(self) -> XMLHighlighter:
        """
        Get the XML highlighter instance.

        Returns:
            XMLHighlighter instance
        """
        return self._highlighter
