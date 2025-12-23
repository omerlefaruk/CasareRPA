"""
Anchor Panel Widget for UI Explorer.

Displays the selected anchor element and provides controls for anchor management.
Shows anchor selector, position, and relationship to target element.
"""

from typing import Any, Dict, Optional

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class AnchorPanel(QWidget):
    """
    Panel for displaying and managing anchor element.

    Shows:
    - Anchor status (configured/not configured)
    - Anchor element info (tag, text, selector)
    - Position selector (left/right/above/below)
    - Clear button

    Signals:
        anchor_cleared: Emitted when anchor is cleared
        position_changed: Emitted when position changes (str: position)
    """

    anchor_cleared = Signal()
    position_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anchor_data: dict[str, Any] | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("Anchor Element")
        title.setStyleSheet("color: #fbbf24; font-weight: bold; font-size: 12px;")
        header.addWidget(title)

        header.addStretch()

        # Status indicator
        self._status_label = QLabel("Not set")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        header.addWidget(self._status_label)

        layout.addLayout(header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background: #3a3a3a;")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

        # Empty state container
        self._empty_state = QWidget()
        empty_layout = QVBoxLayout(self._empty_state)
        empty_layout.setContentsMargins(0, 8, 0, 8)

        empty_text = QLabel(
            "No anchor selected.\n\n"
            "Click 'Indicate Anchor' to pick a stable\n"
            "reference element (label, heading)."
        )
        empty_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_text.setStyleSheet("color: #666; font-size: 11px;")
        empty_layout.addWidget(empty_text)

        layout.addWidget(self._empty_state)

        # Anchor details container (hidden initially)
        self._details_container = QWidget()
        self._details_container.hide()
        details_layout = QVBoxLayout(self._details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)

        # Anchor info row
        info_row = QHBoxLayout()
        info_row.setSpacing(8)

        tag_label = QLabel("Element:")
        tag_label.setStyleSheet("color: #888; font-size: 11px;")
        info_row.addWidget(tag_label)

        self._anchor_tag_label = QLabel("-")
        self._anchor_tag_label.setStyleSheet("color: #e0e0e0; font-size: 11px;")
        info_row.addWidget(self._anchor_tag_label)

        info_row.addStretch()

        # Clear button
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(24)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 2px 8px;
                color: #e0e0e0;
                font-size: 10px;
            }
            QPushButton:hover {
                background: #ef4444;
                border-color: #dc2626;
                color: white;
            }
        """)
        self._clear_btn.clicked.connect(self._on_clear)
        info_row.addWidget(self._clear_btn)

        details_layout.addLayout(info_row)

        # Position row
        position_row = QHBoxLayout()
        position_row.setSpacing(8)

        position_label = QLabel("Position:")
        position_label.setStyleSheet("color: #888; font-size: 11px;")
        position_row.addWidget(position_label)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["Left", "Right", "Above", "Below", "Inside", "Near"])
        self._position_combo.setCurrentText("Left")
        self._position_combo.setFixedWidth(90)
        self._position_combo.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
        """)
        self._position_combo.currentTextChanged.connect(self._on_position_changed)
        position_row.addWidget(self._position_combo)

        position_row.addStretch()
        details_layout.addLayout(position_row)

        # Selector display
        self._selector_display = QTextEdit()
        self._selector_display.setMaximumHeight(50)
        self._selector_display.setReadOnly(True)
        self._selector_display.setFont(QFont("Consolas", 9))
        self._selector_display.setPlaceholderText("Anchor selector...")
        self._selector_display.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #fbbf24;
            }
        """)
        details_layout.addWidget(self._selector_display)

        layout.addWidget(self._details_container)

        # Preview showing anchor relationship
        self._preview_container = QWidget()
        self._preview_container.hide()
        preview_layout = QVBoxLayout(self._preview_container)
        preview_layout.setContentsMargins(0, 8, 0, 0)

        preview_label = QLabel("Relationship:")
        preview_label.setStyleSheet("color: #888; font-size: 10px;")
        preview_layout.addWidget(preview_label)

        self._relationship_preview = QLabel("")
        self._relationship_preview.setStyleSheet("""
            QLabel {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 8px;
                color: #10b981;
                font-family: Consolas;
                font-size: 11px;
            }
        """)
        self._relationship_preview.setWordWrap(True)
        preview_layout.addWidget(self._relationship_preview)

        layout.addWidget(self._preview_container)

        layout.addStretch()

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply panel styling."""
        self.setStyleSheet("""
            QWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
            }
        """)

    def _on_clear(self) -> None:
        """Handle clear button click."""
        self.clear_anchor()
        self.anchor_cleared.emit()
        logger.debug("Anchor cleared from panel")

    def _on_position_changed(self, position: str) -> None:
        """Handle position combo change."""
        if self._anchor_data:
            self._anchor_data["position"] = position.lower()
            self._update_relationship_preview()
        self.position_changed.emit(position.lower())
        logger.debug(f"Anchor position changed to: {position}")

    def _update_relationship_preview(self) -> None:
        """Update the relationship preview text."""
        if not self._anchor_data:
            return

        tag = self._anchor_data.get("tag_name", "element")
        text = self._anchor_data.get("text_content", "")
        position = self._anchor_data.get("position", "left")

        if text:
            anchor_desc = f'"{text[:20]}..."' if len(text) > 20 else f'"{text}"'
        else:
            anchor_desc = f"<{tag}>"

        # Build relationship preview
        position_desc = {
            "left": "to the right of",
            "right": "to the left of",
            "above": "below",
            "below": "above",
            "inside": "inside",
            "near": "near",
        }.get(position, "near")

        preview = f"<target> is {position_desc} {anchor_desc}"
        self._relationship_preview.setText(preview)

    def set_anchor(
        self,
        anchor_data: dict[str, Any],
        target_tag: str = "element",
    ) -> None:
        """
        Set the anchor data and update display.

        Args:
            anchor_data: Dictionary with anchor info
            target_tag: Tag name of target element (for preview)
        """
        self._anchor_data = anchor_data
        self._target_tag = target_tag

        # Update UI
        self._empty_state.hide()
        self._details_container.show()
        self._preview_container.show()

        # Update status
        stability = anchor_data.get("stability_score", 0)
        if stability >= 0.7:
            self._status_label.setText("Stable anchor")
            self._status_label.setStyleSheet("color: #10b981; font-size: 11px;")
        elif stability >= 0.4:
            self._status_label.setText("Medium stability")
            self._status_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
        else:
            self._status_label.setText("Low stability")
            self._status_label.setStyleSheet("color: #ef4444; font-size: 11px;")

        # Update anchor info
        tag = anchor_data.get("tag_name", "element")
        text = anchor_data.get("text_content", "")
        if text:
            display = f"<{tag}> {text[:30]}{'...' if len(text) > 30 else ''}"
        else:
            display = f"<{tag}>"
        self._anchor_tag_label.setText(display)

        # Update position combo
        position = anchor_data.get("position", "left")
        position_text = position.capitalize()
        if position_text in ["Left", "Right", "Above", "Below", "Inside", "Near"]:
            self._position_combo.blockSignals(True)
            self._position_combo.setCurrentText(position_text)
            self._position_combo.blockSignals(False)

        # Update selector display
        selector = anchor_data.get("selector", "")
        self._selector_display.setPlainText(selector)

        # Update relationship preview
        self._update_relationship_preview()

        logger.debug(f"Anchor set in panel: {tag}")

    def clear_anchor(self) -> None:
        """Clear the anchor data and reset display."""
        self._anchor_data = None

        self._empty_state.show()
        self._details_container.hide()
        self._preview_container.hide()

        self._status_label.setText("Not set")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        self._anchor_tag_label.setText("-")
        self._selector_display.clear()
        self._relationship_preview.clear()

    def get_anchor_data(self) -> dict[str, Any] | None:
        """Get the current anchor data."""
        return self._anchor_data

    def has_anchor(self) -> bool:
        """Check if an anchor is configured."""
        return self._anchor_data is not None


__all__ = ["AnchorPanel"]
