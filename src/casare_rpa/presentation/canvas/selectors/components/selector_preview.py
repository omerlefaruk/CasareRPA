"""
Selector Preview Component.

Handles preview rendering and strategy display:
- Strategies list display
- Image preview rendering
- Element screenshot display
- Anchor preview
"""

from typing import Any

from loguru import logger
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget)

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import SelectorStrategy
from casare_rpa.presentation.canvas.theme import THEME
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_margins)
from casare_rpa.presentation.canvas.theme_system import TOKENS


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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._strategies: list[SelectorStrategy] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the preview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS.spacing.md)
        set_margins(layout, (0, 0, 0, 0))

        # Strategies section
        strategies_header = QHBoxLayout()
        self._strategies_label = QLabel("Generated Selectors")
        self._strategies_label.setStyleSheet(
            f"color: {THEME.status_info}; font-weight: bold; "
            f"font-size: {TOKENS.typography.body}px;"
        )
        strategies_header.addWidget(self._strategies_label)

        self._strategies_count = QLabel("")
        self._strategies_count.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
        )
        strategies_header.addWidget(self._strategies_count)
        strategies_header.addStretch()

        layout.addLayout(strategies_header)

        # Info label
        self._strategies_info = QLabel("Pick an element to generate selectors")
        self._strategies_info.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
        )
        layout.addWidget(self._strategies_info)

        # Strategies list
        self._strategies_list = QListWidget()
        self._strategies_list.setMaximumHeight(150)
        self._strategies_list.setAlternatingRowColors(True)
        self._strategies_list.currentItemChanged.connect(self._on_strategy_changed)
        self._strategies_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                background: {THEME.bg_surface};
                outline: none;
                color: {THEME.text_primary};
            }}
            QListWidget::item {{
                padding: {TOKENS.spacing.sm}px {TOKENS.spacing.md}px;
                border-bottom: 1px solid {THEME.bg_medium};
            }}
            QListWidget::item:selected {{
                background: {THEME.status_info};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background: {THEME.bg_medium};
            }}
        """)
        layout.addWidget(self._strategies_list)

        # Test result
        self._test_result = QLabel("")
        self._test_result.setWordWrap(True)
        self._test_result.setStyleSheet(
            f"padding: {TOKENS.spacing.md}px; background: {THEME.bg_dark}; "
            f"border-radius: {TOKENS.radius.sm}px; "
            f"color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px;"
        )
        layout.addWidget(self._test_result)

        # Image preview section (initially hidden)
        self._image_preview_section = QWidget()
        self._image_preview_section.hide()
        image_layout = QHBoxLayout(self._image_preview_section)
        image_layout.setContentsMargins(0, TOKENS.spacing.md, 0, 0)
        image_layout.setSpacing(TOKENS.spacing.md)

        self._image_preview_label = QLabel("No image captured")
        # Use TOKENS for sizing - 120x80 is reasonable for thumbnail
        thumbnail_width = TOKENS.sizes.input_md * 4  # ~112px
        thumbnail_height = TOKENS.sizes.row_height * 2 + TOKENS.spacing.md  # ~72px
        self._image_preview_label.setFixedSize(thumbnail_width, thumbnail_height)
        self._image_preview_label.setAlignment(Qt.AlignCenter)
        self._image_preview_label.setCursor(Qt.PointingHandCursor)
        self._image_preview_label.mousePressEvent = lambda e: self.image_preview_clicked.emit()
        self._image_preview_label.setStyleSheet(f"""
            QLabel {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME.text_muted};
                font-size: {TOKENS.typography.caption}px;
            }}
            QLabel:hover {{
                border-color: {THEME.status_info};
            }}
        """)
        image_layout.addWidget(self._image_preview_label)
        image_layout.addStretch()

        layout.addWidget(self._image_preview_section)

    def set_strategies(self, strategies: list[SelectorStrategy]) -> None:
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

        self._strategies_info.setText(f"{len(strategies)} selectors found, sorted by reliability")
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

    def get_selected_strategy(self) -> SelectorStrategy | None:
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
            "padding: {TOKENS.spacing.md}px; background: #252525; border-radius: {TOKENS.radius.sm}px; "
            "color: {THEME.text_secondary}; font-size: {TOKENS.typography.body}px;"
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
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None) -> None:
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._anchor_data: dict[str, Any] | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the anchor preview UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS.spacing.md)
        set_margins(layout, (0, 0, 0, 0))

        # Warning banner (shown when no anchor)
        self._warning = QWidget()
        self._warning.setStyleSheet(f"""
            QWidget {{
                background: {THEME.bg_medium};
                border: 1px solid {THEME.warning};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        warning_layout = QHBoxLayout(self._warning)
        warning_layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm
        )

        warning_icon = QLabel("!")
        warning_icon.setStyleSheet(
            f"color: {THEME.warning}; font-size: {TOKENS.typography.display_md}px; "
            "font-weight: bold;"
        )
        warning_layout.addWidget(warning_icon)

        warning_text = QLabel("No anchor configured. Consider adding one for reliability.")
        warning_text.setStyleSheet(
            f"color: {THEME.warning}; font-size: {TOKENS.typography.body}px;"
        )
        warning_text.setWordWrap(True)
        warning_layout.addWidget(warning_text, 1)

        layout.addWidget(self._warning)

        # Success banner (shown when anchor is set)
        self._success = QWidget()
        self._success.setStyleSheet(f"""
            QWidget {{
                background: {THEME.bg_medium};
                border: 1px solid {THEME.status_success};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        self._success.hide()
        success_layout = QHBoxLayout(self._success)
        success_layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm
        )

        success_icon = QLabel("\u2713")
        success_icon.setStyleSheet(
            f"color: {THEME.status_success}; font-size: {TOKENS.typography.display_md}px; "
            "font-weight: bold;"
        )
        success_layout.addWidget(success_icon)

        self._info_label = QLabel("Anchor: (none)")
        self._info_label.setStyleSheet(
            f"color: {THEME.status_success}; font-size: {TOKENS.typography.body}px;"
        )
        self._info_label.setWordWrap(True)
        success_layout.addWidget(self._info_label, 1)

        layout.addWidget(self._success)

        # Selector display (hidden initially)
        self._selector_display = QTextEdit()
        self._selector_display.setMaximumHeight(50)
        self._selector_display.setReadOnly(True)
        self._selector_display.setPlaceholderText("Anchor selector...")
        self._selector_display.setFont(QFont(TOKENS.typography.mono, TOKENS.typography.body))
        self._selector_display.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME.bg_surface};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.warning};
            }}
        """)
        self._selector_display.hide()
        layout.addWidget(self._selector_display)

    def set_anchor(self, anchor_data: dict[str, Any]) -> None:
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

    def get_anchor_data(self) -> dict[str, Any] | None:
        """Get the current anchor data."""
        return self._anchor_data

    def has_anchor(self) -> bool:
        """Check if anchor is configured."""
        return self._anchor_data is not None
