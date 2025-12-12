"""
Selector Preview Component.

Handles preview rendering and strategy display:
- Strategies list display
- Image preview rendering
- Element screenshot display
- Anchor preview
"""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import SelectorStrategy


class SelectorPreview(QWidget):
    """
    Widget for displaying selector strategies and previews.

    Shows:
    - List of generated selector strategies with scores
    - Image preview for template matching
    - Anchor element preview
    - Test result display

    Signals:
        strategy_selected: Emitted when a strategy is selected (SelectorStrategy)
        image_preview_clicked: Emitted when image preview is clicked
    """

    strategy_selected = Signal(object)
    image_preview_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._strategies: List[SelectorStrategy] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the preview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Strategies section
        strategies_header = QHBoxLayout()
        self._strategies_label = QLabel("Generated Selectors")
        self._strategies_label.setStyleSheet(
            "color: #60a5fa; font-weight: bold; font-size: 12px;"
        )
        strategies_header.addWidget(self._strategies_label)

        self._strategies_count = QLabel("")
        self._strategies_count.setStyleSheet("color: #888; font-size: 11px;")
        strategies_header.addWidget(self._strategies_count)
        strategies_header.addStretch()

        layout.addLayout(strategies_header)

        # Info label
        self._strategies_info = QLabel("Pick an element to generate selectors")
        self._strategies_info.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._strategies_info)

        # Strategies list
        self._strategies_list = QListWidget()
        self._strategies_list.setMaximumHeight(150)
        self._strategies_list.setAlternatingRowColors(True)
        self._strategies_list.currentItemChanged.connect(self._on_strategy_changed)
        self._strategies_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                background: #1e1e1e;
                outline: none;
                color: #e0e0e0;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:selected {
                background: #3b82f6;
                color: white;
            }
            QListWidget::item:hover:!selected {
                background: #2a2a2a;
            }
        """)
        layout.addWidget(self._strategies_list)

        # Test result
        self._test_result = QLabel("")
        self._test_result.setWordWrap(True)
        self._test_result.setStyleSheet(
            "padding: 8px; background: #252525; border-radius: 4px; "
            "color: #e0e0e0; font-size: 11px;"
        )
        layout.addWidget(self._test_result)

        # Image preview section (initially hidden)
        self._image_preview_section = QWidget()
        self._image_preview_section.hide()
        image_layout = QHBoxLayout(self._image_preview_section)
        image_layout.setContentsMargins(0, 8, 0, 0)
        image_layout.setSpacing(8)

        self._image_preview_label = QLabel("No image captured")
        self._image_preview_label.setFixedSize(120, 80)
        self._image_preview_label.setAlignment(Qt.AlignCenter)
        self._image_preview_label.setCursor(Qt.PointingHandCursor)
        self._image_preview_label.mousePressEvent = (
            lambda e: self.image_preview_clicked.emit()
        )
        self._image_preview_label.setStyleSheet("""
            QLabel {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #888;
                font-size: 10px;
            }
            QLabel:hover {
                border-color: #60a5fa;
            }
        """)
        image_layout.addWidget(self._image_preview_label)
        image_layout.addStretch()

        layout.addWidget(self._image_preview_section)

    def set_strategies(self, strategies: List[SelectorStrategy]) -> None:
        """
        Update the strategies list display.

        Args:
            strategies: List of selector strategies to display
        """
        self._strategies = strategies
        self._strategies_list.clear()

        if not strategies:
            self._strategies_info.setText("No selectors generated")
            self._strategies_count.setText("")
            return

        self._strategies_info.setText(
            f"{len(strategies)} selectors found, sorted by reliability"
        )
        self._strategies_count.setText(f"({len(strategies)})")

        for strategy in strategies:
            item = QListWidgetItem()

            # Score indicator
            if strategy.score >= 80:
                score_icon = "\U0001f7e2"  # Green circle
            elif strategy.score >= 60:
                score_icon = "\U0001f7e1"  # Yellow circle
            else:
                score_icon = "\U0001f534"  # Red circle

            # Unique marker
            unique_mark = " \u2713" if strategy.is_unique else ""

            # Truncate long selectors
            display_value = strategy.value
            if len(display_value) > 40:
                display_value = display_value[:40] + "..."

            display = (
                f"{score_icon} {strategy.score:.0f} | "
                f"{strategy.selector_type.upper()} | "
                f"{display_value}{unique_mark}"
            )
            item.setText(display)
            item.setData(Qt.UserRole, strategy)

            self._strategies_list.addItem(item)

        # Select first item
        if self._strategies_list.count() > 0:
            self._strategies_list.setCurrentRow(0)

    def get_selected_strategy(self) -> Optional[SelectorStrategy]:
        """Get the currently selected strategy."""
        current = self._strategies_list.currentItem()
        if current:
            return current.data(Qt.UserRole)
        return None

    def set_test_result(self, message: str, style: str) -> None:
        """
        Set the test result display.

        Args:
            message: Result message to display
            style: CSS style for the label
        """
        self._test_result.setText(message)
        self._test_result.setStyleSheet(style)

    def clear_test_result(self) -> None:
        """Clear the test result display."""
        self._test_result.setText("")
        self._test_result.setStyleSheet(
            "padding: 8px; background: #252525; border-radius: 4px; "
            "color: #e0e0e0; font-size: 11px;"
        )

    def set_image_preview(self, image_bytes: bytes) -> bool:
        """
        Set the image preview from bytes.

        Args:
            image_bytes: Image data in bytes

        Returns:
            True if image was set successfully
        """
        try:
            image = QImage.fromData(image_bytes)
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._image_preview_label.setPixmap(scaled)
            self._image_preview_section.show()
            return True
        except Exception as e:
            logger.error(f"Failed to set image preview: {e}")
            return False

    def set_image_preview_from_pixmap(self, pixmap: QPixmap) -> None:
        """
        Set the image preview from a pixmap.

        Args:
            pixmap: QPixmap to display
        """
        scaled = pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self._image_preview_label.setPixmap(scaled)
        self._image_preview_section.show()

    def clear_image_preview(self) -> None:
        """Clear the image preview."""
        self._image_preview_label.clear()
        self._image_preview_label.setText("No image captured")
        self._image_preview_section.hide()

    def show_image_section(self, visible: bool = True) -> None:
        """Show or hide the image preview section."""
        self._image_preview_section.setVisible(visible)

    def clear(self) -> None:
        """Clear all preview state."""
        self._strategies = []
        self._strategies_list.clear()
        self._strategies_info.setText("Pick an element to generate selectors")
        self._strategies_count.setText("")
        self.clear_test_result()
        self.clear_image_preview()

    def _on_strategy_changed(
        self,
        current: Optional[QListWidgetItem],
        _previous: Optional[QListWidgetItem],
    ) -> None:
        """Handle strategy selection change."""
        if current:
            strategy = current.data(Qt.UserRole)
            self.strategy_selected.emit(strategy)


class AnchorPreview(QWidget):
    """
    Widget for displaying anchor element preview.

    Shows:
    - Anchor status (configured/not configured)
    - Anchor selector
    - Position indicator
    - Stability score
    """

    anchor_cleared = Signal()
    position_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._anchor_data: Optional[Dict[str, Any]] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the anchor preview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Warning banner (shown when no anchor)
        self._warning = QWidget()
        self._warning.setStyleSheet("""
            QWidget {
                background: #3d3520;
                border: 1px solid #fbbf24;
                border-radius: 6px;
            }
        """)
        warning_layout = QHBoxLayout(self._warning)
        warning_layout.setContentsMargins(12, 8, 12, 8)

        warning_icon = QLabel("!")
        warning_icon.setStyleSheet(
            "color: #fbbf24; font-size: 14px; font-weight: bold;"
        )
        warning_layout.addWidget(warning_icon)

        warning_text = QLabel(
            "No anchor configured. Consider adding one for reliability."
        )
        warning_text.setStyleSheet("color: #fbbf24; font-size: 12px;")
        warning_text.setWordWrap(True)
        warning_layout.addWidget(warning_text, 1)

        layout.addWidget(self._warning)

        # Success banner (shown when anchor is set)
        self._success = QWidget()
        self._success.setStyleSheet("""
            QWidget {
                background: #1a3d2e;
                border: 1px solid #10b981;
                border-radius: 6px;
            }
        """)
        self._success.hide()
        success_layout = QHBoxLayout(self._success)
        success_layout.setContentsMargins(12, 8, 12, 8)

        success_icon = QLabel("\u2713")
        success_icon.setStyleSheet(
            "color: #10b981; font-size: 14px; font-weight: bold;"
        )
        success_layout.addWidget(success_icon)

        self._info_label = QLabel("Anchor: (none)")
        self._info_label.setStyleSheet("color: #10b981; font-size: 12px;")
        self._info_label.setWordWrap(True)
        success_layout.addWidget(self._info_label, 1)

        layout.addWidget(self._success)

        # Selector display (hidden initially)
        self._selector_display = QTextEdit()
        self._selector_display.setMaximumHeight(50)
        self._selector_display.setReadOnly(True)
        self._selector_display.setPlaceholderText("Anchor selector...")
        self._selector_display.setFont(QFont("Consolas", 9))
        self._selector_display.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #fbbf24;
            }
        """)
        self._selector_display.hide()
        layout.addWidget(self._selector_display)

    def set_anchor(self, anchor_data: Dict[str, Any]) -> None:
        """
        Set and display anchor data.

        Args:
            anchor_data: Anchor configuration dictionary
        """
        self._anchor_data = anchor_data

        self._warning.hide()
        self._success.show()
        self._selector_display.show()

        tag = anchor_data.get("tag_name", "element")
        text = anchor_data.get("text_content", "")
        selector = anchor_data.get("selector", "")

        if text:
            display_text = text[:30] + "..." if len(text) > 30 else text
            self._info_label.setText(f"Anchor: <{tag}> {display_text}")
        else:
            short_sel = selector[:40] + "..." if len(selector) > 40 else selector
            self._info_label.setText(f"Anchor: {short_sel}")

        self._selector_display.setPlainText(selector)

    def clear_anchor(self) -> None:
        """Clear the anchor configuration."""
        self._anchor_data = None
        self._warning.show()
        self._success.hide()
        self._selector_display.hide()
        self._selector_display.clear()
        self.anchor_cleared.emit()

    def get_anchor_data(self) -> Optional[Dict[str, Any]]:
        """Get the current anchor data."""
        return self._anchor_data

    def has_anchor(self) -> bool:
        """Check if anchor is configured."""
        return self._anchor_data is not None
