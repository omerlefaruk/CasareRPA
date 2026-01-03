"""
Anchor Widget for Element Selector Dialog.

Provides anchor configuration UI for reliable element location.
Uses UiPath-style anchor-target relationship.
"""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme import THEME_V2 as THEME
from casare_rpa.presentation.canvas.theme import TOKENS_V2 as TOKENS
from casare_rpa.presentation.canvas.theme.helpers import (
    set_margins,
)
from casare_rpa.presentation.canvas.theme.utils import alpha


class AnchorWidget(QWidget):
    """
    Widget for anchor configuration.

    Layout:
    +---------------------------------------------------------------+
    | [ ] Use anchor for reliability                                |
    | [Suggest Anchor]  Position: [Left v]                          |
    | Anchor: label[for="username"] "Username"                      |
    +---------------------------------------------------------------+

    Signals:
        anchor_enabled_changed: Anchor checkbox toggled
        pick_anchor_requested: User clicked pick anchor
        suggest_anchor_requested: User clicked suggest anchor
        clear_anchor_requested: User clicked clear
        position_changed: Position dropdown changed
    """

    anchor_enabled_changed = Signal(bool)
    pick_anchor_requested = Signal()
    suggest_anchor_requested = Signal()
    clear_anchor_requested = Signal()
    position_changed = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._has_anchor = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build widget UI."""
        layout = QVBoxLayout(self)
        set_margins(layout, (0, 0, 0, 0))
        layout.setSpacing(TOKENS.spacing.md)

        # Main frame
        frame = QGroupBox("Anchor")
        frame.setCheckable(True)
        frame.setChecked(False)
        frame.toggled.connect(self._on_enabled_changed)
        frame.setStyleSheet(f"""
            QGroupBox {{
                font-weight: {TOKENS.typography.weight_semibold};
                font-size: {TOKENS.typography.body}px;
                color: {THEME.text_header};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                margin-top: {TOKENS.spacing.sm}px;
                padding-top: {TOKENS.spacing.sm}px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 {TOKENS.spacing.xs}px;
            }}
            QGroupBox::indicator {{
                width: {TOKENS.sizes.icon_sm}px;
                height: {TOKENS.sizes.icon_sm}px;
            }}
            QGroupBox::indicator:unchecked {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border_light};
                border-radius: {TOKENS.radius.sm}px;
            }}
            QGroupBox::indicator:checked {{
                background: {THEME.primary};
                border: 1px solid {THEME.primary};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)

        self._frame = frame

        content_layout = QVBoxLayout(frame)
        content_layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.md, TOKENS.spacing.md, TOKENS.spacing.md
        )
        content_layout.setSpacing(TOKENS.spacing.md)

        # Info banner (shown when no anchor) - use amber/warning colors
        self._info_banner = QWidget()
        self._info_banner.setStyleSheet(f"""
            QWidget {{
                background: {alpha(THEME.warning, 0.18)};
                border: 1px solid {THEME.warning};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        info_layout = QHBoxLayout(self._info_banner)
        info_layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm
        )

        info_icon = QLabel("!")
        info_icon.setStyleSheet(
            f"color: {THEME.warning}; font-size: {TOKENS.typography.display_md}px; font-weight: bold;"
        )
        info_layout.addWidget(info_icon)

        info_text = QLabel(
            "Anchors improve selector reliability. Pick a nearby stable "
            "element (label, heading) as reference."
        )
        info_text.setStyleSheet(
            f"color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px;"
        )
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text, 1)

        content_layout.addWidget(self._info_banner)

        # Success banner (shown when anchor is set) - use green/success colors
        self._success_banner = QWidget()
        self._success_banner.setStyleSheet(f"""
            QWidget {{
                background: {alpha(THEME.success, 0.18)};
                border: 1px solid {THEME.success};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        self._success_banner.setVisible(False)

        success_layout = QHBoxLayout(self._success_banner)
        success_layout.setContentsMargins(
            TOKENS.spacing.md, TOKENS.spacing.sm, TOKENS.spacing.md, TOKENS.spacing.sm
        )

        success_icon = QLabel("✓")
        success_icon.setStyleSheet(
            f"color: {THEME.success}; font-size: {TOKENS.typography.display_md}px; font-weight: bold;"
        )
        success_layout.addWidget(success_icon)

        self._anchor_info = QLabel("Anchor configured")
        self._anchor_info.setStyleSheet(
            f"color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px;"
        )
        self._anchor_info.setWordWrap(True)
        success_layout.addWidget(self._anchor_info, 1)

        content_layout.addWidget(self._success_banner)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(TOKENS.spacing.md)

        # Pick Anchor button
        self._pick_btn = QPushButton("Pick Anchor")
        self._pick_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pick_btn.clicked.connect(self.pick_anchor_requested.emit)
        self._pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.primary};
                border: 1px solid {THEME.primary};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.sizes.button_padding_h}px;
                color: {THEME.text_on_primary};
                font-weight: {TOKENS.typography.weight_semibold};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME.primary_hover};
            }}
            QPushButton:disabled {{
                background: {THEME.bg_component};
                border-color: {THEME.border};
                color: {THEME.text_muted};
            }}
        """)
        btn_row.addWidget(self._pick_btn)

        # Suggest Anchor button
        self._suggest_btn = QPushButton("Auto-detect")
        self._suggest_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._suggest_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._suggest_btn.setToolTip("Automatically find the best anchor for current target")
        self._suggest_btn.clicked.connect(self.suggest_anchor_requested.emit)
        self._suggest_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_header};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
            }}
            QPushButton:disabled {{
                color: {THEME.text_muted};
            }}
        """)
        btn_row.addWidget(self._suggest_btn)

        # Clear button
        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setEnabled(False)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_component};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_header};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME.error};
                border-color: {THEME.error};
                color: {THEME.text_on_error};
            }}
            QPushButton:disabled {{
                color: {THEME.text_muted};
            }}
        """)
        btn_row.addWidget(self._clear_btn)

        btn_row.addStretch()

        # Position dropdown
        pos_label = QLabel("Position:")
        pos_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
        )
        btn_row.addWidget(pos_label)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["Left", "Right", "Above", "Below", "Inside", "Near"])
        self._position_combo.setCurrentText("Left")
        self._position_combo.setFixedWidth(TOKENS.sizes.input_md * 3)
        self._position_combo.currentTextChanged.connect(
            lambda t: self.position_changed.emit(t.lower())
        )
        self._position_combo.setStyleSheet(f"""
            QComboBox {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.sm}px;
                color: {THEME.text_header};
                font-size: {TOKENS.typography.body}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {TOKENS.sizes.icon_sm}px;
            }}
        """)
        btn_row.addWidget(self._position_combo)

        content_layout.addLayout(btn_row)

        # Anchor selector display (hidden until anchor is set)
        self._selector_frame = QWidget()
        self._selector_frame.setVisible(False)

        selector_layout = QVBoxLayout(self._selector_frame)
        set_margins(selector_layout, (0, 0, 0, 0))
        selector_layout.setSpacing(TOKENS.spacing.xs)

        selector_label = QLabel("Anchor selector:")
        selector_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}px;"
        )
        selector_layout.addWidget(selector_label)

        self._selector_display = QTextEdit()
        self._selector_display.setReadOnly(True)
        self._selector_display.setMaximumHeight(50)
        self._selector_display.setFont(QFont(TOKENS.typography.mono, TOKENS.typography.body))
        self._selector_display.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME.input_bg};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.text_primary};
            }}
        """)
        selector_layout.addWidget(self._selector_display)

        content_layout.addWidget(self._selector_frame)

        layout.addWidget(frame)

    def _on_enabled_changed(self, enabled: bool) -> None:
        """Handle anchor checkbox toggle."""
        self.anchor_enabled_changed.emit(enabled)

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_anchor()
        self.clear_anchor_requested.emit()

    def set_anchor(
        self,
        selector: str,
        tag: str = "",
        text: str = "",
        position: str = "left",
        stability: float = 0.0,
    ) -> None:
        """Set anchor data."""
        self._has_anchor = True

        # Update UI
        self._info_banner.setVisible(False)
        self._success_banner.setVisible(True)
        self._selector_frame.setVisible(True)
        self._clear_btn.setEnabled(True)

        # Update anchor info
        if text:
            display_text = text[:30] + "..." if len(text) > 30 else text
            self._anchor_info.setText(f'<{tag}> "{display_text}" (stability: {stability:.0%})')
        else:
            short_sel = selector[:40] + "..." if len(selector) > 40 else selector
            self._anchor_info.setText(f"Anchor: {short_sel} (stability: {stability:.0%})")

        # Update selector display
        self._selector_display.setPlainText(selector)

        # Update position
        position_text = position.capitalize()
        if position_text in ["Left", "Right", "Above", "Below", "Inside", "Near"]:
            self._position_combo.setCurrentText(position_text)

        # Enable the frame
        self._frame.setChecked(True)

    def clear_anchor(self) -> None:
        """Clear anchor data."""
        self._has_anchor = False

        # Update UI
        self._info_banner.setVisible(True)
        self._success_banner.setVisible(False)
        self._selector_frame.setVisible(False)
        self._clear_btn.setEnabled(False)
        self._selector_display.clear()
        self._anchor_info.setText("Anchor configured")

    def set_enabled(self, enabled: bool) -> None:
        """Set whether anchor is enabled."""
        self._frame.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Check if anchor is enabled."""
        return self._frame.isChecked()

    def has_anchor(self) -> bool:
        """Check if anchor is configured."""
        return self._has_anchor and self._frame.isChecked()

    def get_position(self) -> str:
        """Get selected position."""
        return self._position_combo.currentText().lower()

    def get_selector(self) -> str:
        """Get anchor selector."""
        return self._selector_display.toPlainText().strip()

    def get_anchor_data(self) -> dict[str, Any] | None:
        """Get anchor data as dictionary."""
        if not self.has_anchor():
            return None

        return {
            "selector": self.get_selector(),
            "position": self.get_position(),
        }


__all__ = ["AnchorWidget"]

