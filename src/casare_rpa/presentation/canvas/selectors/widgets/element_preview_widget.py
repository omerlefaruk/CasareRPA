"""
Element Preview Widget for Element Selector Dialog.

Shows the currently selected element with:
- Syntax-highlighted HTML preview
- Property badges (Tag, ID, Classes, Text)
- Element bounding rect visualization
"""

from typing import Optional, Dict, Any, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QSyntaxHighlighter, QTextCharFormat
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextEdit,
    QFrame,
)

from casare_rpa.presentation.canvas.selectors.state.selector_state import (
    ElementSelectorState,
)


class HTMLHighlighter(QSyntaxHighlighter):
    """
    Syntax highlighter for HTML preview.

    Colors:
    - Tags: Blue
    - Attributes: Cyan
    - Values: Orange
    - Text: Default gray
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Tag format
        self._tag_format = QTextCharFormat()
        self._tag_format.setForeground(QColor("#60a5fa"))  # Blue
        self._tag_format.setFontWeight(QFont.Weight.Bold)

        # Attribute name format
        self._attr_format = QTextCharFormat()
        self._attr_format.setForeground(QColor("#22d3ee"))  # Cyan

        # Attribute value format
        self._value_format = QTextCharFormat()
        self._value_format.setForeground(QColor("#fb923c"))  # Orange

        # Comment format
        self._comment_format = QTextCharFormat()
        self._comment_format.setForeground(QColor("#6b7280"))  # Gray
        self._comment_format.setFontItalic(True)

    def highlightBlock(self, text: str) -> None:
        """Apply highlighting to text block."""
        import re

        # Tags: <tagname and </tagname and />
        for match in re.finditer(r"</?[a-zA-Z][a-zA-Z0-9]*|/?>", text):
            self.setFormat(match.start(), match.end() - match.start(), self._tag_format)

        # Attribute names: name=
        for match in re.finditer(r"[a-zA-Z][a-zA-Z0-9_-]*(?==)", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self._attr_format
            )

        # Attribute values: "value" or 'value'
        for match in re.finditer(r'"[^"]*"|\'[^\']*\'', text):
            self.setFormat(
                match.start(), match.end() - match.start(), self._value_format
            )


class PropertyBadge(QLabel):
    """
    Small badge showing an element property.

    Format: "Label: value" with colored background.
    """

    def __init__(
        self,
        label: str,
        value: str = "",
        color: str = "#3a3a3a",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self._label = label
        self._color = color
        self.update_value(value)

    def update_value(self, value: str) -> None:
        """Update the badge value."""
        if value:
            display = f"{self._label}: {value}"
            if len(display) > 30:
                display = display[:27] + "..."
            self.setText(display)
            self.setVisible(True)
        else:
            self.setVisible(False)

        self.setStyleSheet(f"""
            QLabel {{
                background: {self._color};
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 2px 6px;
                color: #e0e0e0;
                font-size: 11px;
            }}
        """)


class ElementPreviewWidget(QWidget):
    """
    Widget showing preview of selected element.

    Layout:
    +---------------------------------------------------------------+
    | <button class="btn-primary" id="submit">Submit</button>       |
    +---------------------------------------------------------------+
    | Tag: BUTTON | ID: submit | Classes: btn-primary | Text: Sub.. |
    +---------------------------------------------------------------+

    Signals:
        open_explorer_requested: User wants to open UI Explorer
    """

    open_explorer_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Element Preview")
        title.setStyleSheet("color: #60a5fa; font-weight: bold; font-size: 12px;")
        header.addWidget(title)

        header.addStretch()

        # Open in UI Explorer link
        explorer_link = QLabel(
            '<a href="#" style="color: #60a5fa;">Open in UI Explorer</a>'
        )
        explorer_link.setOpenExternalLinks(False)
        explorer_link.linkActivated.connect(lambda: self.open_explorer_requested.emit())
        explorer_link.setCursor(Qt.CursorShape.PointingHandCursor)
        explorer_link.setStyleSheet("font-size: 11px;")
        header.addWidget(explorer_link)

        layout.addLayout(header)

        # HTML preview area
        self._html_preview = QTextEdit()
        self._html_preview.setReadOnly(True)
        self._html_preview.setMaximumHeight(80)
        self._html_preview.setFont(QFont("Consolas", 10))
        self._html_preview.setPlaceholderText(
            "No element selected. Click 'Pick Element' to start."
        )
        self._html_preview.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 8px;
                color: #e0e0e0;
            }
        """)
        self._highlighter = HTMLHighlighter(self._html_preview.document())
        layout.addWidget(self._html_preview)

        # Property badges row
        badges_frame = QFrame()
        badges_frame.setStyleSheet("""
            QFrame {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)

        badges_layout = QHBoxLayout(badges_frame)
        badges_layout.setContentsMargins(8, 6, 8, 6)
        badges_layout.setSpacing(6)

        self._tag_badge = PropertyBadge("Tag", color="#1e3a5f")
        badges_layout.addWidget(self._tag_badge)

        self._id_badge = PropertyBadge("ID", color="#1a3d2e")
        badges_layout.addWidget(self._id_badge)

        self._class_badge = PropertyBadge("Class", color="#3d2e1a")
        badges_layout.addWidget(self._class_badge)

        self._text_badge = PropertyBadge("Text", color="#3d1a3d")
        badges_layout.addWidget(self._text_badge)

        badges_layout.addStretch()

        # Visibility indicator
        self._visible_badge = QLabel("V")
        self._visible_badge.setToolTip("Element is visible")
        self._visible_badge.setFixedSize(20, 20)
        self._visible_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._visible_badge.setStyleSheet("""
            QLabel {
                background: #10b981;
                border-radius: 10px;
                color: white;
                font-size: 10px;
                font-weight: bold;
            }
        """)
        self._visible_badge.setVisible(False)
        badges_layout.addWidget(self._visible_badge)

        layout.addWidget(badges_frame)

        # Empty state
        self._empty_state = QLabel(
            "No element selected\n\nClick 'Pick Element' to select an element from the page"
        )
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 12px;
                padding: 20px;
            }
        """)
        self._empty_state.setVisible(True)
        layout.addWidget(self._empty_state)

    def update_from_state(self, state: ElementSelectorState) -> None:
        """Update widget from state."""
        has_element = state.has_element()

        self._html_preview.setVisible(has_element)
        self._empty_state.setVisible(not has_element)

        if has_element:
            # Update HTML preview
            html = state.element_html
            if not html and state.element_tag:
                # Build HTML representation
                html = self._build_html(state)
            self._html_preview.setPlainText(html)

            # Update badges
            self._tag_badge.update_value(state.element_tag.upper())
            self._id_badge.update_value(state.element_id)

            classes = " ".join(state.element_classes[:3])
            if len(state.element_classes) > 3:
                classes += f" (+{len(state.element_classes) - 3})"
            self._class_badge.update_value(classes)

            text = state.element_text[:30] if state.element_text else ""
            if len(state.element_text) > 30:
                text += "..."
            self._text_badge.update_value(text)

            # Visibility indicator
            is_visible = state.element_properties.get("visible", True)
            self._visible_badge.setVisible(is_visible)
            if not is_visible:
                self._visible_badge.setText("H")
                self._visible_badge.setToolTip("Element is hidden")
                self._visible_badge.setStyleSheet("""
                    QLabel {
                        background: #ef4444;
                        border-radius: 10px;
                        color: white;
                        font-size: 10px;
                        font-weight: bold;
                    }
                """)
        else:
            # Clear badges
            self._tag_badge.update_value("")
            self._id_badge.update_value("")
            self._class_badge.update_value("")
            self._text_badge.update_value("")
            self._visible_badge.setVisible(False)

    def _build_html(self, state: ElementSelectorState) -> str:
        """Build HTML representation from state."""
        tag = state.element_tag.lower() if state.element_tag else "element"

        parts = [f"<{tag}"]

        if state.element_id:
            parts.append(f' id="{state.element_id}"')

        if state.element_classes:
            classes = " ".join(state.element_classes)
            parts.append(f' class="{classes}"')

        # Add other important attributes
        props = state.element_properties
        for attr in ["data-testid", "aria-label", "name", "type", "href", "src"]:
            if attr in props and props[attr]:
                parts.append(f' {attr}="{props[attr]}"')

        parts.append(">")

        # Add text content (truncated)
        if state.element_text:
            text = state.element_text[:50]
            if len(state.element_text) > 50:
                text += "..."
            parts.append(text)

        parts.append(f"</{tag}>")

        return "".join(parts)

    def set_element(
        self,
        html: str = "",
        tag: str = "",
        element_id: str = "",
        classes: Optional[List[str]] = None,
        text: str = "",
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Directly set element data."""
        # Build a minimal state for update
        from casare_rpa.presentation.canvas.selectors.state.selector_state import (
            ElementSelectorState,
        )

        state = ElementSelectorState(
            element_html=html,
            element_tag=tag,
            element_id=element_id,
            element_classes=classes or [],
            element_text=text,
            element_properties=properties or {},
        )
        self.update_from_state(state)

    def clear(self) -> None:
        """Clear the preview."""
        self._html_preview.clear()
        self._tag_badge.update_value("")
        self._id_badge.update_value("")
        self._class_badge.update_value("")
        self._text_badge.update_value("")
        self._visible_badge.setVisible(False)
        self._empty_state.setVisible(True)


__all__ = ["ElementPreviewWidget", "HTMLHighlighter", "PropertyBadge"]
