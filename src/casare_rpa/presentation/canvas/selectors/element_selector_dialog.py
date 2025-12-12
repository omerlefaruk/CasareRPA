"""
Element Selector Dialog - UiPath/Power Automate Inspired Design.

Modern, compact design with:
- Dark theme matching CasareRPA canvas
- Card-based sections
- Clean typography
- Icon-heavy interface
- Compact but readable layout
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QImage, QPixmap, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSlider,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from PySide6.QtWidgets import QDialog
from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from casare_rpa.presentation.canvas.ui.theme import Theme

if TYPE_CHECKING:
    from playwright.async_api import Page


# =============================================================================
# Theme Adapter (Maps unified Theme to legacy attribute access pattern)
# =============================================================================


class _ThemeAdapter:
    """
    Adapter class that provides attribute-style access to unified theme colors.

    This bridges the gap between the old DarkTheme class API and the new
    Theme.get_colors() dataclass API for backward compatibility.
    """

    @property
    def bg_primary(self) -> str:
        return Theme.get_colors().surface

    @property
    def bg_secondary(self) -> str:
        return Theme.get_colors().background_alt

    @property
    def bg_tertiary(self) -> str:
        return Theme.get_colors().background

    @property
    def bg_hover(self) -> str:
        return Theme.get_colors().surface_hover

    @property
    def bg_active(self) -> str:
        return Theme.get_colors().secondary_hover

    @property
    def bg_input(self) -> str:
        return Theme.get_colors().background

    @property
    def text_primary(self) -> str:
        return Theme.get_colors().text_primary

    @property
    def text_secondary(self) -> str:
        return Theme.get_colors().text_secondary

    @property
    def text_muted(self) -> str:
        return Theme.get_colors().text_muted

    @property
    def text_disabled(self) -> str:
        return Theme.get_colors().text_disabled

    @property
    def accent_primary(self) -> str:
        return Theme.get_colors().accent

    @property
    def accent_hover(self) -> str:
        return Theme.get_colors().accent_hover

    @property
    def accent_pressed(self) -> str:
        return Theme.get_colors().primary_pressed

    @property
    def accent_light(self) -> str:
        return Theme.get_colors().selection

    @property
    def accent_orange(self) -> str:
        return Theme.get_colors().warning

    @property
    def accent_orange_light(self) -> str:
        # Derive lighter warning color
        return "#FFE4B5"  # Moccasin - light orange

    @property
    def success(self) -> str:
        return Theme.get_colors().success

    @property
    def success_light(self) -> str:
        # Derive lighter success color
        return "#90EE90"  # Light green

    @property
    def warning(self) -> str:
        return Theme.get_colors().warning

    @property
    def warning_light(self) -> str:
        # Derive lighter warning color
        return "#FFE4B5"  # Moccasin - light orange

    @property
    def error(self) -> str:
        return Theme.get_colors().error

    @property
    def error_light(self) -> str:
        # Derive lighter error color
        return "#FFB6C1"  # Light pink

    @property
    def info(self) -> str:
        return Theme.get_colors().info

    @property
    def info_light(self) -> str:
        # Derive lighter info color
        return "#ADD8E6"  # Light blue

    @property
    def border(self) -> str:
        return Theme.get_colors().border

    @property
    def border_light(self) -> str:
        return Theme.get_colors().border_light

    @property
    def border_dark(self) -> str:
        return Theme.get_colors().border_dark

    @property
    def border_focus(self) -> str:
        return Theme.get_colors().accent


# Module-level theme instance using unified theme
THEME = _ThemeAdapter()


# =============================================================================
# Reusable Style Constants
# =============================================================================

CARD_STYLE = f"""
    background: {THEME.bg_primary};
    border: 1px solid {THEME.border_light};
    border-radius: 6px;
"""

COMBO_STYLE = f"""
    QComboBox {{
        background: {THEME.bg_primary};
        border: 1px solid {THEME.border};
        border-radius: 4px;
        padding: 5px 10px;
        color: {THEME.text_primary};
        font-size: 12px;
        min-height: 28px;
    }}
    QComboBox:hover {{
        border-color: {THEME.accent_primary};
    }}
    QComboBox:focus {{
        border-color: {THEME.accent_primary};
        border-width: 2px;
    }}
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 4px solid transparent;
        border-right: 4px solid transparent;
        border-top: 5px solid {THEME.text_secondary};
    }}
    QComboBox QAbstractItemView {{
        background: {THEME.bg_primary};
        border: 1px solid {THEME.border};
        selection-background-color: {THEME.accent_light};
        selection-color: {THEME.accent_primary};
        outline: none;
    }}
"""

INPUT_STYLE = f"""
    QLineEdit {{
        background: {THEME.bg_primary};
        border: 1px solid {THEME.border};
        border-radius: 4px;
        padding: 6px 10px;
        color: {THEME.text_primary};
        font-size: 12px;
        min-height: 28px;
    }}
    QLineEdit:hover {{
        border-color: {THEME.text_muted};
    }}
    QLineEdit:focus {{
        border-color: {THEME.accent_primary};
        border-width: 2px;
    }}
    QLineEdit::placeholder {{
        color: {THEME.text_muted};
    }}
"""

PRIMARY_BTN_STYLE = f"""
    QPushButton {{
        background: {THEME.accent_primary};
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        color: white;
        font-size: 12px;
        font-weight: 600;
        min-height: 32px;
    }}
    QPushButton:hover {{
        background: {THEME.accent_hover};
    }}
    QPushButton:pressed {{
        background: {THEME.accent_pressed};
    }}
    QPushButton:disabled {{
        background: {THEME.bg_tertiary};
        color: {THEME.text_disabled};
    }}
"""

SECONDARY_BTN_STYLE = f"""
    QPushButton {{
        background: {THEME.bg_primary};
        border: 1px solid {THEME.border};
        border-radius: 4px;
        padding: 8px 16px;
        color: {THEME.text_primary};
        font-size: 12px;
        font-weight: 500;
        min-height: 32px;
    }}
    QPushButton:hover {{
        background: {THEME.bg_hover};
        border-color: {THEME.text_muted};
    }}
    QPushButton:pressed {{
        background: {THEME.bg_active};
    }}
"""

GHOST_BTN_STYLE = f"""
    QPushButton {{
        background: transparent;
        border: none;
        border-radius: 4px;
        padding: 6px 12px;
        color: {THEME.text_secondary};
        font-size: 12px;
    }}
    QPushButton:hover {{
        background: {THEME.bg_hover};
        color: {THEME.text_primary};
    }}
    QPushButton:pressed {{
        background: {THEME.bg_active};
    }}
"""


# =============================================================================
# Card Section Widget
# =============================================================================


class CardSection(QWidget):
    """Card-based collapsible section with shadow."""

    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        icon: str = "",
        expanded: bool = True,
        accent: str = None,
        parent=None,
    ):
        super().__init__(parent)
        self._expanded = expanded
        self._accent = accent or THEME.accent_primary
        self._icon = icon

        self.setObjectName("CardSection")

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 8)

        # Card container
        self._card = QWidget()
        self._card.setStyleSheet(f"""
            QWidget#Card {{
                {CARD_STYLE}
            }}
        """)
        self._card.setObjectName("Card")

        card_layout = QVBoxLayout(self._card)
        card_layout.setSpacing(0)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # Header
        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._toggle)
        self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setFixedHeight(40)

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(12, 0, 12, 0)
        header_layout.setSpacing(8)

        # Accent bar
        accent_bar = QWidget()
        accent_bar.setFixedSize(3, 20)
        accent_bar.setStyleSheet(f"background: {self._accent}; border-radius: 1px;")
        header_layout.addWidget(accent_bar)

        # Icon
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"color: {self._accent}; font-size: 14px;")
            header_layout.addWidget(icon_label)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"""
            color: {THEME.text_primary};
            font-size: 13px;
            font-weight: 600;
        """)
        header_layout.addWidget(self._title_label)
        header_layout.addStretch()

        # Chevron
        self._chevron = QLabel("▼" if expanded else "▶")
        self._chevron.setStyleSheet(f"color: {THEME.text_muted}; font-size: 10px;")
        header_layout.addWidget(self._chevron)

        self._header.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_secondary};
                border: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {THEME.bg_tertiary};
            }}
        """)
        card_layout.addWidget(self._header)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background: {THEME.border_light};")
        sep.setFixedHeight(1)
        card_layout.addWidget(sep)

        # Content
        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(12, 12, 12, 12)
        self._content_layout.setSpacing(8)
        self._content.setVisible(expanded)
        card_layout.addWidget(self._content)

        layout.addWidget(self._card)

        # Add subtle shadow (dark for dark theme)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setOffset(0, 2)
        shadow.setColor(Qt.GlobalColor.black)
        self._card.setGraphicsEffect(shadow)

    def _toggle(self):
        self._expanded = self._header.isChecked()
        self._content.setVisible(self._expanded)
        self._chevron.setText("▼" if self._expanded else "▶")
        self.toggled.emit(self._expanded)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        self._header.setChecked(expanded)
        self._content.setVisible(expanded)
        self._chevron.setText("▼" if expanded else "▶")


# =============================================================================
# Selector Row Widget
# =============================================================================


class SelectorRow(QWidget):
    """Compact selector type row with toggle, text area, and actions."""

    enabled_changed = Signal(bool)

    def __init__(self, label: str, color: str, has_accuracy: bool = False, parent=None):
        super().__init__(parent)
        self._color = color

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Header row
        header = QHBoxLayout()
        header.setSpacing(8)

        # Toggle checkbox with custom styling
        self._checkbox = QCheckBox(label)
        self._checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME.text_primary};
                font-size: 12px;
                font-weight: 500;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {THEME.border};
                border-radius: 4px;
                background: {THEME.bg_primary};
            }}
            QCheckBox::indicator:hover {{
                border-color: {color};
            }}
            QCheckBox::indicator:checked {{
                background: {color};
                border-color: {color};
            }}
            QCheckBox::indicator:checked::after {{
                content: "✓";
            }}
        """)
        self._checkbox.toggled.connect(self._on_toggle)
        header.addWidget(self._checkbox)

        header.addStretch()

        # Copy button - visible with background
        self._copy_btn = QPushButton("Copy")
        self._copy_btn.setToolTip("Copy selector to clipboard")
        self._copy_btn.setFixedHeight(28)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 10px;
                color: {THEME.text_secondary};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.text_muted};
                color: {THEME.text_primary};
            }}
        """)
        self._copy_btn.clicked.connect(self._copy)
        header.addWidget(self._copy_btn)

        # Pick button - always blue accent
        self._pick_btn = QPushButton("Pick")
        self._pick_btn.setFixedHeight(28)
        self._pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.accent_primary};
                border: none;
                border-radius: 4px;
                padding: 0 14px;
                color: white;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {THEME.accent_hover};
            }}
            QPushButton:pressed {{
                background: {THEME.accent_pressed};
            }}
        """)
        header.addWidget(self._pick_btn)

        layout.addLayout(header)

        # Selector text area
        self._text = QTextEdit()
        self._text.setMaximumHeight(52)
        self._text.setPlaceholderText("Click Pick to select an element...")
        self._text.setFont(QFont("Consolas", 10))
        self._text.setStyleSheet(f"""
            QTextEdit {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px;
                color: {THEME.text_primary};
            }}
            QTextEdit:focus {{
                border-color: {THEME.accent_primary};
            }}
        """)
        layout.addWidget(self._text)

        # Accuracy slider (if applicable)
        self._accuracy_slider = None
        self._accuracy_label = None
        if has_accuracy:
            acc_row = QHBoxLayout()
            acc_row.setSpacing(8)

            acc_icon = QLabel("🎚️")
            acc_icon.setStyleSheet("font-size: 12px;")
            acc_row.addWidget(acc_icon)

            acc_lbl = QLabel("Match accuracy:")
            acc_lbl.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
            acc_row.addWidget(acc_lbl)

            self._accuracy_slider = QSlider(Qt.Orientation.Horizontal)
            self._accuracy_slider.setRange(50, 100)
            self._accuracy_slider.setValue(80)
            self._accuracy_slider.setFixedWidth(100)
            self._accuracy_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: 4px;
                    background: {THEME.border};
                    border-radius: 2px;
                }}
                QSlider::handle:horizontal {{
                    width: 14px;
                    height: 14px;
                    margin: -5px 0;
                    background: {THEME.accent_primary};
                    border-radius: 7px;
                }}
                QSlider::sub-page:horizontal {{
                    background: {THEME.accent_primary};
                    border-radius: 2px;
                }}
            """)
            acc_row.addWidget(self._accuracy_slider)

            self._accuracy_label = QLabel("80%")
            self._accuracy_label.setFixedWidth(35)
            self._accuracy_label.setStyleSheet(
                f"color: {THEME.text_primary}; font-size: 11px; font-weight: 500;"
            )
            self._accuracy_slider.valueChanged.connect(
                lambda v: self._accuracy_label.setText(f"{v}%")
            )
            acc_row.addWidget(self._accuracy_label)

            acc_row.addStretch()
            layout.addLayout(acc_row)

        self._on_toggle(False)

    def _on_toggle(self, checked: bool):
        self._text.setEnabled(checked)
        self._copy_btn.setEnabled(checked)
        self._pick_btn.setEnabled(checked)
        if self._accuracy_slider:
            self._accuracy_slider.setEnabled(checked)
        opacity = "1.0" if checked else "0.5"
        self._text.setStyleSheet(self._text.styleSheet() + f" opacity: {opacity};")
        self.enabled_changed.emit(checked)

    def _copy(self):
        text = self._text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)

    def set_selector(self, value: str):
        self._text.setPlainText(value)

    def get_selector(self) -> str:
        return self._text.toPlainText().strip()

    def set_enabled(self, enabled: bool):
        self._checkbox.setChecked(enabled)

    def is_enabled(self) -> bool:
        return self._checkbox.isChecked()

    def get_accuracy(self) -> float:
        return self._accuracy_slider.value() / 100.0 if self._accuracy_slider else 1.0

    def get_pick_button(self) -> QPushButton:
        return self._pick_btn


# =============================================================================
# Main Dialog
# =============================================================================


class ElementSelectorDialog(QDialog):
    """
    Element Selector with UiPath/Power Automate inspired design.

    Features:
    - Dark theme matching CasareRPA canvas (VSCode Dark+)
    - Card-based collapsible sections
    - Compact but readable design
    - Icon-heavy interface
    """

    selector_selected = Signal(object)
    selector_confirmed = Signal(object)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        mode: str = "browser",
        browser_page: Optional["Page"] = None,
        initial_selector: str = "",
        target_node: Optional[Any] = None,
        property_name: str = "selector",
        target_property: str = None,
        initial_mode: str = None,
    ):
        super().__init__(parent)

        if initial_mode:
            mode = initial_mode
        if target_property:
            property_name = target_property

        self._target_node = target_node
        self._target_property = property_name
        self._browser_page = browser_page
        self._current_result: Optional[SelectorResult] = None
        self._current_mode = mode
        self._strategies: List[SelectorStrategy] = []
        self._ctrl_pressed = False
        self._anchor_data: Optional[Dict[str, Any]] = None
        self._picking_anchor: bool = False
        self._tabs: Dict[str, BaseSelectorTab] = {}

        self.setWindowTitle("Element Selector")
        self.setMinimumSize(480, 520)
        self.resize(520, 600)

        self._setup_ui()
        self._create_tabs()
        self._connect_signals()
        self._select_mode(mode)

        if initial_selector:
            self._strict_row.set_selector(initial_selector)
            self._strict_row.set_enabled(True)

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME.bg_tertiary};
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header toolbar
        layout.addWidget(self._create_header())

        # Main content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(0)
        self._content_layout.setContentsMargins(12, 12, 12, 12)

        # Sections
        self._content_layout.addWidget(self._create_quick_actions())
        self._content_layout.addWidget(self._create_anchor_section())  # Top, collapsed
        self._content_layout.addWidget(self._create_target_section())
        self._content_layout.addWidget(self._create_strategies_section())
        self._content_layout.addWidget(self._create_options_section())
        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Footer action bar
        layout.addWidget(self._create_footer())

    def _create_header(self) -> QWidget:
        """Create the header toolbar with mode buttons and status."""
        header = QWidget()
        header.setFixedHeight(52)
        header.setStyleSheet(f"""
            QWidget {{
                background: {THEME.bg_primary};
                border-bottom: 1px solid {THEME.border};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Mode toggle buttons
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        mode_btn_style = f"""
            QToolButton {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 6px 12px;
                color: {THEME.text_secondary};
                font-size: 11px;
                font-weight: 500;
            }}
            QToolButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.border_light};
            }}
            QToolButton:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
                color: white;
            }}
        """

        self._browser_btn = QToolButton()
        self._browser_btn.setText("🌐 Web")
        self._browser_btn.setToolTip("Browser automation")
        self._browser_btn.setCheckable(True)
        self._browser_btn.setFixedHeight(32)
        self._browser_btn.setStyleSheet(mode_btn_style)
        self._mode_group.addButton(self._browser_btn, 0)
        layout.addWidget(self._browser_btn)

        self._desktop_btn = QToolButton()
        self._desktop_btn.setText("🖥️ Desktop")
        self._desktop_btn.setToolTip("Windows UI automation")
        self._desktop_btn.setCheckable(True)
        self._desktop_btn.setFixedHeight(32)
        self._desktop_btn.setStyleSheet(mode_btn_style)
        self._mode_group.addButton(self._desktop_btn, 1)
        layout.addWidget(self._desktop_btn)

        self._image_btn = QToolButton()
        self._image_btn.setText("🖼️ Image")
        self._image_btn.setToolTip("Image matching")
        self._image_btn.setCheckable(True)
        self._image_btn.setFixedHeight(32)
        self._image_btn.setStyleSheet(mode_btn_style)
        self._mode_group.addButton(self._image_btn, 2)
        layout.addWidget(self._image_btn)

        self._ocr_btn = QToolButton()
        self._ocr_btn.setText("📝 OCR")
        self._ocr_btn.setToolTip("Text recognition")
        self._ocr_btn.setCheckable(True)
        self._ocr_btn.setFixedHeight(32)
        self._ocr_btn.setStyleSheet(mode_btn_style)
        self._mode_group.addButton(self._ocr_btn, 3)
        layout.addWidget(self._ocr_btn)

        layout.addStretch()

        # Status indicator
        self._status_label = QLabel("Ready")
        self._status_label.setStyleSheet(f"""
            color: {THEME.text_muted};
            font-size: 11px;
            padding: 4px 8px;
            background: {THEME.bg_secondary};
            border-radius: 4px;
        """)
        layout.addWidget(self._status_label)

        # UI Explorer button - explicit styling for visibility
        self._explorer_btn = QPushButton("UI Explorer")
        self._explorer_btn.setFixedHeight(32)
        self._explorer_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border_light};
                border-radius: 4px;
                padding: 0 12px;
                color: {THEME.text_primary};
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.accent_primary};
                color: white;
            }}
        """)
        self._explorer_btn.clicked.connect(self._on_open_explorer)
        layout.addWidget(self._explorer_btn)

        return header

    def _create_quick_actions(self) -> QWidget:
        """Create quick text search bar."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)

        # Search icon
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 14px;")
        layout.addWidget(icon)

        # Element type dropdown - explicit 28px height
        self._text_element = QComboBox()
        self._text_element.addItems(
            ["Any", "Button", "Link", "Input", "Label", "Div", "Span"]
        )
        self._text_element.setFixedWidth(80)
        self._text_element.setFixedHeight(28)
        self._text_element.setStyleSheet(f"""
            QComboBox {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 8px;
                color: {THEME.text_primary};
                font-size: 11px;
                min-height: 26px;
                max-height: 26px;
            }}
            QComboBox:hover {{
                border-color: {THEME.accent_primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {THEME.text_secondary};
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                selection-background-color: {THEME.accent_light};
                outline: none;
            }}
        """)
        layout.addWidget(self._text_element)

        # Text input - explicit 28px height
        self._text_input = QLineEdit()
        self._text_input.setPlaceholderText("Find element by text content...")
        self._text_input.setFixedHeight(28)
        self._text_input.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 8px;
                color: {THEME.text_primary};
                font-size: 11px;
                min-height: 26px;
                max-height: 26px;
            }}
            QLineEdit:hover {{
                border-color: {THEME.text_muted};
            }}
            QLineEdit:focus {{
                border-color: {THEME.accent_primary};
            }}
            QLineEdit::placeholder {{
                color: {THEME.text_muted};
            }}
        """)
        layout.addWidget(self._text_input, 1)

        # Find button - same height as combo/input (28px)
        self._text_gen_btn = QPushButton("Find")
        self._text_gen_btn.setFixedHeight(28)
        self._text_gen_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.accent_primary};
                border: none;
                border-radius: 4px;
                padding: 0 12px;
                color: white;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: {THEME.accent_hover};
            }}
            QPushButton:pressed {{
                background: {THEME.accent_pressed};
            }}
        """)
        self._text_gen_btn.clicked.connect(self._on_generate_text_selector)
        layout.addWidget(self._text_gen_btn)

        return container

    def _create_target_section(self) -> CardSection:
        """Create target selector section."""
        section = CardSection(
            "Target Element", "🎯", expanded=True, accent=THEME.accent_primary
        )
        content = section.content_layout()

        # Strict selector row
        self._strict_row = SelectorRow("Primary Selector", THEME.accent_primary)
        self._strict_row.set_enabled(True)
        content.addWidget(self._strict_row)

        # Fuzzy selector row
        self._fuzzy_row = SelectorRow(
            "Fuzzy Matching", THEME.accent_orange, has_accuracy=True
        )
        content.addWidget(self._fuzzy_row)

        # Fuzzy options
        fuzzy_opts = QHBoxLayout()
        fuzzy_opts.setContentsMargins(24, 0, 0, 0)
        fuzzy_opts.setSpacing(8)

        fuzzy_lbl = QLabel("Text match:")
        fuzzy_lbl.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        fuzzy_opts.addWidget(fuzzy_lbl)

        self._fuzzy_match = QComboBox()
        self._fuzzy_match.addItems(["Contains", "Equals", "Starts with", "Ends with"])
        self._fuzzy_match.setFixedWidth(100)
        self._fuzzy_match.setFixedHeight(28)
        self._fuzzy_match.setStyleSheet(f"""
            QComboBox {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 8px;
                color: {THEME.text_primary};
                font-size: 11px;
                min-height: 26px;
                max-height: 26px;
            }}
            QComboBox:hover {{
                border-color: {THEME.accent_primary};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {THEME.text_secondary};
            }}
            QComboBox QAbstractItemView {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                selection-background-color: {THEME.accent_light};
                outline: none;
            }}
        """)
        fuzzy_opts.addWidget(self._fuzzy_match)

        self._fuzzy_text = QLineEdit()
        self._fuzzy_text.setPlaceholderText("Text to match...")
        self._fuzzy_text.setFixedHeight(28)
        self._fuzzy_text.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 8px;
                color: {THEME.text_primary};
                font-size: 11px;
                min-height: 26px;
                max-height: 26px;
            }}
            QLineEdit:hover {{
                border-color: {THEME.text_muted};
            }}
            QLineEdit:focus {{
                border-color: {THEME.accent_primary};
            }}
            QLineEdit::placeholder {{
                color: {THEME.text_muted};
            }}
        """)
        fuzzy_opts.addWidget(self._fuzzy_text, 1)

        content.addLayout(fuzzy_opts)

        # CV selector row
        self._cv_row = SelectorRow("Computer Vision", "#8b5cf6", has_accuracy=True)
        content.addWidget(self._cv_row)

        # Image selector row
        self._image_row = SelectorRow("Image Template", "#06b6d4", has_accuracy=True)
        content.addWidget(self._image_row)

        # Image preview area
        img_container = QWidget()
        img_layout = QHBoxLayout(img_container)
        img_layout.setContentsMargins(24, 0, 0, 0)
        img_layout.setSpacing(12)

        self._image_preview = QLabel()
        self._image_preview.setFixedSize(80, 50)
        self._image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_preview.setStyleSheet(f"""
            background: {THEME.bg_secondary};
            border: 2px dashed {THEME.border};
            border-radius: 4px;
            color: {THEME.text_muted};
            font-size: 20px;
        """)
        self._image_preview.setText("📷")
        img_layout.addWidget(self._image_preview)

        img_btns = QVBoxLayout()
        img_btns.setSpacing(4)

        self._capture_btn = QPushButton("Capture")
        self._capture_btn.setFixedHeight(24)
        self._capture_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.accent_primary};
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 10px;
                font-weight: 500;
            }}
            QPushButton:hover {{ background: {THEME.accent_hover}; }}
        """)
        self._capture_btn.clicked.connect(self._on_capture_image)
        img_btns.addWidget(self._capture_btn)

        self._load_btn = QPushButton("Load")
        self._load_btn.setFixedHeight(24)
        self._load_btn.setStyleSheet(GHOST_BTN_STYLE + " font-size: 10px;")
        self._load_btn.clicked.connect(self._on_load_image)
        img_btns.addWidget(self._load_btn)

        img_layout.addLayout(img_btns)
        img_layout.addStretch()
        content.addWidget(img_container)

        return section

    def _create_anchor_section(self) -> CardSection:
        """Create anchor configuration section."""
        section = CardSection(
            "Anchor Element", "⚓", expanded=False, accent=THEME.accent_primary
        )
        self._anchor_section = section
        content = section.content_layout()

        # Info text
        info = QLabel(
            "Use a nearby stable element as a reference point for reliable selection."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        content.addWidget(info)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._pick_anchor_btn = QPushButton("Pick Anchor")
        self._pick_anchor_btn.setFixedHeight(32)
        self._pick_anchor_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.accent_primary};
                border: none;
                border-radius: 4px;
                padding: 0 16px;
                color: white;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{ background: {THEME.accent_hover}; }}
        """)
        self._pick_anchor_btn.clicked.connect(self._on_pick_anchor)
        btn_row.addWidget(self._pick_anchor_btn)

        self._auto_anchor_btn = QPushButton("Auto-detect")
        self._auto_anchor_btn.setFixedHeight(32)
        self._auto_anchor_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border_light};
                border-radius: 4px;
                padding: 0 16px;
                color: {THEME.text_primary};
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.accent_primary};
            }}
        """)
        self._auto_anchor_btn.clicked.connect(self._on_auto_detect_anchor)
        btn_row.addWidget(self._auto_anchor_btn)

        self._clear_anchor_btn = QPushButton("✕")
        self._clear_anchor_btn.setFixedSize(32, 32)
        self._clear_anchor_btn.setEnabled(False)
        self._clear_anchor_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {THEME.border};
                border-radius: 4px;
                color: {THEME.text_muted};
            }}
            QPushButton:hover {{
                background: {THEME.error_light};
                border-color: {THEME.error};
                color: {THEME.error};
            }}
            QPushButton:disabled {{ color: {THEME.text_disabled}; }}
        """)
        self._clear_anchor_btn.clicked.connect(self._on_clear_anchor)
        btn_row.addWidget(self._clear_anchor_btn)

        btn_row.addStretch()
        content.addLayout(btn_row)

        # Anchor details (hidden initially)
        self._anchor_details = QWidget()
        self._anchor_details.hide()
        details_layout = QHBoxLayout(self._anchor_details)
        details_layout.setContentsMargins(0, 8, 0, 0)
        details_layout.setSpacing(8)

        pos_lbl = QLabel("Position:")
        pos_lbl.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        details_layout.addWidget(pos_lbl)

        self._anchor_position = QComboBox()
        self._anchor_position.addItems(
            ["Left of", "Right of", "Above", "Below", "Inside"]
        )
        self._anchor_position.setStyleSheet(COMBO_STYLE)
        details_layout.addWidget(self._anchor_position)

        self._anchor_display = QLabel()
        self._anchor_display.setStyleSheet(f"""
            color: {THEME.accent_primary};
            font-size: 11px;
            font-weight: 500;
            padding: 4px 8px;
            background: {THEME.accent_light};
            border-radius: 4px;
        """)
        details_layout.addWidget(self._anchor_display, 1)

        content.addWidget(self._anchor_details)

        return section

    def _create_strategies_section(self) -> CardSection:
        """Create generated selectors section."""
        section = CardSection(
            "Generated Selectors", "📋", expanded=False, accent=THEME.accent_primary
        )
        self._strategies_section = section
        content = section.content_layout()

        self._strategies_info = QLabel(
            "Pick an element to generate selector alternatives."
        )
        self._strategies_info.setStyleSheet(
            f"color: {THEME.text_secondary}; font-size: 11px;"
        )
        content.addWidget(self._strategies_info)

        self._strategies_list = QListWidget()
        self._strategies_list.setMaximumHeight(140)
        self._strategies_list.setStyleSheet(f"""
            QListWidget {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                font-size: 11px;
                font-family: Consolas, monospace;
            }}
            QListWidget::item {{
                padding: 8px 10px;
                border-bottom: 1px solid {THEME.border_light};
            }}
            QListWidget::item:selected {{
                background: {THEME.accent_light};
                color: {THEME.accent_primary};
            }}
            QListWidget::item:hover:!selected {{
                background: {THEME.bg_hover};
            }}
        """)
        self._strategies_list.currentItemChanged.connect(self._on_strategy_changed)
        content.addWidget(self._strategies_list)

        # Test result label
        self._test_result = QLabel()
        self._test_result.setWordWrap(True)
        self._test_result.setStyleSheet(f"""
            padding: 8px;
            background: {THEME.bg_secondary};
            border-radius: 4px;
            font-size: 11px;
        """)
        self._test_result.hide()
        content.addWidget(self._test_result)

        return section

    def _create_options_section(self) -> CardSection:
        """Create advanced options section."""
        section = CardSection(
            "Options", "⚙️", expanded=False, accent=THEME.accent_primary
        )
        content = section.content_layout()

        # Window selector
        win_row = QHBoxLayout()
        win_row.setSpacing(8)

        win_icon = QLabel("🪟")
        win_icon.setStyleSheet("font-size: 14px;")
        win_row.addWidget(win_icon)

        win_lbl = QLabel("Window:")
        win_lbl.setStyleSheet(f"color: {THEME.text_secondary}; font-size: 11px;")
        win_row.addWidget(win_lbl)

        self._window_selector = QLineEdit()
        self._window_selector.setPlaceholderText("<wnd app='...' title='...' />")
        self._window_selector.setFixedHeight(28)
        self._window_selector.setStyleSheet(f"""
            QLineEdit {{
                background: {THEME.bg_primary};
                border: 1px solid {THEME.border};
                border-radius: 4px;
                padding: 0 8px;
                color: {THEME.text_primary};
                font-size: 11px;
                min-height: 26px;
                max-height: 26px;
            }}
            QLineEdit:hover {{
                border-color: {THEME.text_muted};
            }}
            QLineEdit:focus {{
                border-color: {THEME.accent_primary};
            }}
            QLineEdit::placeholder {{
                color: {THEME.text_muted};
            }}
        """)
        win_row.addWidget(self._window_selector, 1)

        content.addLayout(win_row)

        # Checkboxes
        self._wait_visible = QCheckBox("Wait for element to be visible")
        self._wait_visible.setChecked(True)
        self._wait_visible.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME.text_primary};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {THEME.border};
                border-radius: 4px;
                background: {THEME.bg_primary};
            }}
            QCheckBox::indicator:checked {{
                background: {THEME.accent_primary};
                border-color: {THEME.accent_primary};
            }}
        """)
        content.addWidget(self._wait_visible)

        self._highlight_element = QCheckBox("Highlight element before action")
        self._highlight_element.setStyleSheet(self._wait_visible.styleSheet())
        content.addWidget(self._highlight_element)

        return section

    def _create_footer(self) -> QWidget:
        """Create footer action bar."""
        footer = QWidget()
        footer.setFixedHeight(56)
        footer.setStyleSheet(f"""
            QWidget {{
                background: {THEME.bg_primary};
                border-top: 1px solid {THEME.border};
            }}
        """)

        # Button style matching UI Explorer
        btn_style = f"""
            QPushButton {{
                background: {THEME.bg_secondary};
                border: 1px solid {THEME.border_light};
                border-radius: 4px;
                padding: 0 16px;
                color: {THEME.text_primary};
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
            }}
            QPushButton:hover {{
                background: {THEME.bg_hover};
                border-color: {THEME.accent_primary};
                color: white;
            }}
            QPushButton:disabled {{
                color: {THEME.text_disabled};
                background: {THEME.bg_tertiary};
            }}
        """

        layout = QHBoxLayout(footer)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Validate button
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setFixedHeight(32)
        self._validate_btn.setStyleSheet(btn_style)
        self._validate_btn.clicked.connect(self._on_validate)
        layout.addWidget(self._validate_btn)

        layout.addStretch()

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(32)
        self._cancel_btn.setStyleSheet(btn_style)
        self._cancel_btn.clicked.connect(self.reject)
        layout.addWidget(self._cancel_btn)

        # Confirm button
        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setDefault(True)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setFixedHeight(32)
        self._confirm_btn.setStyleSheet(btn_style)
        self._confirm_btn.clicked.connect(self._on_confirm)
        layout.addWidget(self._confirm_btn)

        return footer

    def _create_tabs(self):
        """Create tab instances for functionality (hidden, backend only)."""
        try:
            from casare_rpa.presentation.canvas.selectors.tabs.browser_tab import (
                BrowserSelectorTab,
            )
            from casare_rpa.presentation.canvas.selectors.tabs.desktop_tab import (
                DesktopSelectorTab,
            )
            from casare_rpa.presentation.canvas.selectors.tabs.ocr_tab import (
                OCRSelectorTab,
            )
            from casare_rpa.presentation.canvas.selectors.tabs.image_match_tab import (
                ImageMatchTab,
            )

            self._browser_tab = BrowserSelectorTab(self)
            self._browser_tab.selectors_generated.connect(self._on_strategies_generated)
            self._browser_tab.status_changed.connect(self._on_status_changed)
            self._browser_tab.element_screenshot_captured.connect(
                self._on_element_screenshot
            )
            self._browser_tab.hide()
            self._tabs["browser"] = self._browser_tab
            if self._browser_page:
                self._browser_tab.set_browser_page(self._browser_page)

            self._desktop_tab = DesktopSelectorTab(self)
            self._desktop_tab.selectors_generated.connect(self._on_strategies_generated)
            self._desktop_tab.status_changed.connect(self._on_status_changed)
            self._desktop_tab.hide()
            self._tabs["desktop"] = self._desktop_tab

            self._ocr_tab = OCRSelectorTab(self)
            self._ocr_tab.selectors_generated.connect(self._on_strategies_generated)
            self._ocr_tab.status_changed.connect(self._on_status_changed)
            self._ocr_tab.hide()
            self._tabs["ocr"] = self._ocr_tab

            self._image_tab = ImageMatchTab(self)
            self._image_tab.selectors_generated.connect(self._on_strategies_generated)
            self._image_tab.status_changed.connect(self._on_status_changed)
            self._image_tab.hide()
            self._tabs["image"] = self._image_tab
        except ImportError as e:
            logger.warning(f"Some tabs not available: {e}")

    def _connect_signals(self):
        self._mode_group.idClicked.connect(self._on_mode_changed)
        self._strict_row.get_pick_button().clicked.connect(
            lambda: self._start_picking(self._current_mode)
        )
        self._fuzzy_row.get_pick_button().clicked.connect(
            lambda: self._start_picking(self._current_mode)
        )
        self._cv_row.get_pick_button().clicked.connect(
            lambda: self._start_picking("ocr")
        )
        self._image_row.get_pick_button().clicked.connect(
            lambda: self._start_picking("image")
        )

    def _select_mode(self, mode: str):
        mode_map = {
            "browser": self._browser_btn,
            "desktop": self._desktop_btn,
            "image": self._image_btn,
            "ocr": self._ocr_btn,
        }
        btn = mode_map.get(mode)
        if btn:
            btn.setChecked(True)
            self._current_mode = mode

    # =========================================================================
    # Status Helpers
    # =========================================================================

    def _set_status(self, message: str, status_type: str = "default") -> None:
        """Set status label with appropriate styling."""
        self._status_label.setText(message)

        styles = {
            "default": f"color: {THEME.text_muted}; background: {THEME.bg_secondary};",
            "success": f"color: {THEME.success}; background: {THEME.success_light};",
            "warning": f"color: {THEME.warning}; background: {THEME.warning_light};",
            "error": f"color: {THEME.error}; background: {THEME.error_light};",
            "info": f"color: {THEME.info}; background: {THEME.info_light};",
        }

        base = "font-size: 11px; padding: 4px 8px; border-radius: 4px;"
        self._status_label.setStyleSheet(
            f"QLabel {{ {base} {styles.get(status_type, styles['default'])} }}"
        )

    # =========================================================================
    # Public API
    # =========================================================================

    def set_browser_page(self, page: "Page"):
        self._browser_page = page
        for tab in self._tabs.values():
            tab.set_browser_page(page)

    def set_target_node(self, node: Any, property_name: str = "selector"):
        self._target_node = node
        self._target_property = property_name

    def get_result(self) -> Optional[SelectorResult]:
        return self._current_result

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_mode_changed(self, mode_id: int):
        mode_map = {0: "browser", 1: "desktop", 2: "image", 3: "ocr"}
        self._current_mode = mode_map.get(mode_id, "browser")
        for tab in self._tabs.values():
            tab.set_active(False)
        if self._current_mode in self._tabs:
            self._tabs[self._current_mode].set_active(True)

    def _on_open_explorer(self):
        try:
            from casare_rpa.presentation.canvas.selectors.ui_explorer import (
                UIExplorerDialog,
            )

            dialog = UIExplorerDialog(
                parent=self, mode=self._current_mode, browser_page=self._browser_page
            )
            dialog.selector_confirmed.connect(self._on_explorer_confirmed)
            dialog.exec()
        except ImportError as e:
            logger.error(f"UIExplorer not available: {e}")

    def _on_explorer_confirmed(self, selector: str):
        if selector:
            self._strict_row.set_selector(selector)
            self._strict_row.set_enabled(True)
            self._confirm_btn.setEnabled(True)

    def _start_picking(self, mode: str):
        if mode == "browser" and not self._browser_page:
            self._set_status("⚠ Open a browser first", "warning")
            return

        tab = self._tabs.get(mode)
        if tab:
            self._set_status(f"🎯 Picking {mode}...", "info")
            asyncio.ensure_future(tab.start_picking())

    def _on_strategies_generated(self, strategies: List[SelectorStrategy]):
        if self._picking_anchor:
            self._picking_anchor = False
            self._pick_anchor_btn.setText("🎯 Pick Anchor")
            self._pick_anchor_btn.setEnabled(True)

            if not strategies:
                self._set_status("No anchor found", "warning")
                return

            best = strategies[0]
            selector_type = getattr(best, "selector_type", "css")
            if hasattr(selector_type, "value"):
                selector_type = selector_type.value
            self._anchor_data = {
                "selector": best.value,
                "selector_type": selector_type,
                "score": best.score,
            }

            display_text = best.value[:40]
            self._anchor_display.setText(f"⚓ {display_text}")
            self._anchor_details.show()
            self._clear_anchor_btn.setEnabled(True)
            self._anchor_section.set_expanded(True)

            self._set_status("✓ Anchor set", "success")
            return

        self._strategies = strategies
        self._strategies_list.clear()

        if not strategies:
            self._strategies_info.setText("No selectors generated")
            self._confirm_btn.setEnabled(False)
            return

        self._strategies_section.set_expanded(True)
        self._strategies_info.setText(f"{len(strategies)} selector alternatives found")
        self._set_status(f"✓ {len(strategies)} found", "success")

        for strategy in strategies:
            score_icon = (
                "🟢"
                if strategy.score >= 80
                else ("🟡" if strategy.score >= 60 else "🔴")
            )
            unique_badge = " ✓" if strategy.is_unique else ""
            val = (
                strategy.value[:45] + "..."
                if len(strategy.value) > 45
                else strategy.value
            )
            item = QListWidgetItem(
                f"{score_icon} {strategy.score:.0f}% │ {val}{unique_badge}"
            )
            item.setData(Qt.ItemDataRole.UserRole, strategy)
            self._strategies_list.addItem(item)

        if self._strategies_list.count() > 0:
            self._strategies_list.setCurrentRow(0)

        if strategies:
            self._strict_row.set_selector(strategies[0].value)

    def _on_strategy_changed(self, current: Optional[QListWidgetItem], _previous):
        if not current:
            self._confirm_btn.setEnabled(False)
            return

        strategy: SelectorStrategy = current.data(Qt.ItemDataRole.UserRole)
        self._strict_row.set_selector(strategy.value)
        self._confirm_btn.setEnabled(True)

        tab = self._tabs.get(self._current_mode)
        if tab:
            result = tab.get_current_selector()
            if result:
                result.selector_value = strategy.value
                result.selector_type = strategy.selector_type
                result.confidence = strategy.score / 100.0
                result.is_unique = strategy.is_unique
                self._current_result = result
            else:
                self._current_result = SelectorResult(
                    selector_value=strategy.value,
                    selector_type=strategy.selector_type,
                    confidence=strategy.score / 100.0,
                    is_unique=strategy.is_unique,
                )

    def _on_status_changed(self, message: str):
        self._status_label.setText(message)
        if self._picking_anchor and (
            "stopped" in message.lower() or "error" in message.lower()
        ):
            self._picking_anchor = False
            self._pick_anchor_btn.setText("🎯 Pick Anchor")
            self._pick_anchor_btn.setEnabled(True)

    def _on_element_screenshot(self, screenshot_bytes: bytes):
        try:
            image = QImage.fromData(screenshot_bytes)
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                76,
                46,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_preview.setPixmap(scaled)
            self._image_row.set_enabled(True)
        except Exception as e:
            logger.error(f"Failed to display screenshot: {e}")

    def _on_validate(self):
        tab = self._tabs.get(self._current_mode)
        if not tab:
            return
        selector = self._strict_row.get_selector()
        if not selector:
            self._test_result.setText("No selector to validate")
            self._test_result.show()
            return
        asyncio.ensure_future(self._do_validate(tab, selector))

    async def _do_validate(self, tab, selector: str):
        from casare_rpa.utils.selectors.selector_manager import parse_xml_selector

        parsed_selector, selector_type = parse_xml_selector(selector)

        result = await tab.test_selector(parsed_selector, selector_type)
        self._test_result.show()

        if result.get("success"):
            count = result.get("count", 0)
            if count == 0:
                self._test_result.setText("❌ No elements found")
                self._test_result.setStyleSheet(
                    f"padding: 8px; background: {THEME.error_light}; color: {THEME.error}; border-radius: 4px; font-size: 11px;"
                )
            elif count == 1:
                self._test_result.setText("✓ Found 1 unique element")
                self._test_result.setStyleSheet(
                    f"padding: 8px; background: {THEME.success_light}; color: {THEME.success}; border-radius: 4px; font-size: 11px;"
                )
                await tab.highlight_selector(parsed_selector, selector_type)
            else:
                self._test_result.setText(f"⚠ Found {count} elements (not unique)")
                self._test_result.setStyleSheet(
                    f"padding: 8px; background: {THEME.warning_light}; color: {THEME.warning}; border-radius: 4px; font-size: 11px;"
                )
                await tab.highlight_selector(parsed_selector, selector_type)
        else:
            self._test_result.setText(f"❌ Error: {result.get('error', 'Unknown')}")
            self._test_result.setStyleSheet(
                f"padding: 8px; background: {THEME.error_light}; color: {THEME.error}; border-radius: 4px; font-size: 11px;"
            )

    def _on_confirm(self):
        """Handle confirm button click."""
        if not self._current_result:
            selector = self._strict_row.get_selector()
            if not selector:
                return
            self._current_result = SelectorResult(
                selector_value=selector, selector_type="xpath", confidence=0.5
            )

        # Wait for pending capture tasks (important for ImageClickNode cv_template)
        # We need to do this synchronously since Qt modal dialog doesn't process asyncio events
        tab = self._tabs.get(self._current_mode)
        if tab and hasattr(tab, "_pending_capture_task"):
            task = tab._pending_capture_task
            if task and not task.done():
                logger.info("Waiting for pending capture to complete...")
                try:
                    # Process events while waiting for capture to complete
                    from PySide6.QtCore import QCoreApplication
                    import time

                    start = time.time()
                    timeout = 5.0  # 5 second timeout
                    while not task.done() and (time.time() - start) < timeout:
                        QCoreApplication.processEvents()
                        time.sleep(0.05)  # Small delay to avoid busy loop

                    if task.done():
                        logger.info("Capture completed successfully")
                    else:
                        logger.warning("Capture timed out after 5 seconds")
                except Exception as e:
                    logger.warning(f"Error waiting for capture: {e}")

            # After waiting, sync healing_context from tab's result to ensure we have latest data
            # This handles case where dialog created a different SelectorResult object
            tab_result = tab.get_current_selector()
            if (
                tab_result
                and self._current_result
                and tab_result is not self._current_result
            ):
                logger.info("Syncing healing_context from tab result to dialog result")
                self._current_result.healing_context.update(tab_result.healing_context)
                logger.info(
                    f"healing_context after sync: {list(self._current_result.healing_context.keys())}"
                )
            elif self._current_result:
                logger.info(
                    f"healing_context keys: {list(self._current_result.healing_context.keys())}"
                )

        if self._anchor_data and self._anchor_data.get("selector"):
            target_selector = self._current_result.selector_value
            anchor_selector = self._anchor_data.get("selector", "")
            position = self._anchor_position.currentText().lower().replace(" ", "_")
            combined = self._build_combined_selector(
                anchor_selector, target_selector, position
            )
            self._current_result.selector_value = combined

        if self._fuzzy_row.is_enabled():
            self._current_result.metadata["fuzzy_accuracy"] = (
                self._fuzzy_row.get_accuracy()
            )
            self._current_result.metadata["fuzzy_text"] = self._fuzzy_text.text()
        if self._cv_row.is_enabled():
            self._current_result.metadata["cv_accuracy"] = self._cv_row.get_accuracy()
        if self._image_row.is_enabled():
            self._current_result.metadata["image_accuracy"] = (
                self._image_row.get_accuracy()
            )
        if self._anchor_data:
            self._current_result.metadata["anchor"] = self._anchor_data
            # Also populate the anchor field with AnchorData object
            from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
                AnchorData,
            )

            self._current_result.anchor = AnchorData(
                selector=self._anchor_data.get("selector", ""),
                position=self._anchor_position.currentText().lower().replace(" ", "_"),
                tag_name=self._anchor_data.get("tag_name", ""),
                text_content=self._anchor_data.get("text", ""),
                stability_score=self._anchor_data.get("stability_score", 0.0),
                attributes=self._anchor_data.get("attributes", {}),
                offset_x=self._anchor_data.get("offset_x", 0),
                offset_y=self._anchor_data.get("offset_y", 0),
            )
            logger.info(
                f"ElementSelectorDialog: Anchor data attached to result: {self._current_result.anchor.selector[:50]}..."
            )

        if self._target_node and self._target_property:
            try:
                widget = self._target_node.get_widget(self._target_property)
                if widget:
                    widget.set_value(self._current_result.selector_value)
            except Exception as e:
                logger.error(f"Auto-paste failed: {e}")

        self.selector_selected.emit(self._current_result)
        self.selector_confirmed.emit(self._current_result)
        self.accept()

    def _on_generate_text_selector(self):
        text = self._text_input.text().strip()
        if not text:
            return
        element = self._text_element.currentText().lower()
        if element == "any":
            element = "*"
        selector = f"itext={text}" if element == "*" else f"itext={element}:{text}"
        self._strict_row.set_selector(selector)
        self._strict_row.set_enabled(True)
        self._confirm_btn.setEnabled(True)
        self._current_result = SelectorResult(
            selector_value=selector, selector_type="itext", confidence=0.7
        )
        self._set_status("✓ Generated", "success")

    def _on_pick_anchor(self):
        if self._current_mode == "browser" and not self._browser_page:
            self._set_status("Open a browser first", "warning")
            return
        tab = self._tabs.get("browser")
        if tab:
            self._picking_anchor = True
            self._set_status("🎯 Pick anchor element...", "warning")
            self._pick_anchor_btn.setText("Picking...")
            self._pick_anchor_btn.setEnabled(False)
            asyncio.ensure_future(tab.start_picking())

    def _on_auto_detect_anchor(self):
        selector = self._strict_row.get_selector()
        if not selector or not self._browser_page:
            self._set_status("Select target first", "warning")
            return
        asyncio.ensure_future(self._do_auto_anchor(selector))

    async def _do_auto_anchor(self, selector: str):
        try:
            from casare_rpa.utils.selectors.anchor_locator import AnchorLocator

            locator = AnchorLocator()
            anchor = await locator.auto_detect_anchor(self._browser_page, selector)
            if anchor:
                self._anchor_data = anchor
                self._anchor_display.setText(
                    anchor.get("text_content", "")[:30]
                    or anchor.get("selector", "")[:30]
                )
                self._anchor_details.show()
                self._clear_anchor_btn.setEnabled(True)
                self._anchor_section.set_expanded(True)
                self._set_status("✓ Anchor detected", "success")
            else:
                self._set_status("No anchor found", "warning")
        except Exception as e:
            logger.error(f"Anchor detection failed: {e}")

    def _on_clear_anchor(self):
        self._anchor_data = None
        self._anchor_display.setText("")
        self._anchor_details.hide()
        self._clear_anchor_btn.setEnabled(False)

    def _build_combined_selector(
        self, anchor: str, target: str, position: str = "left_of"
    ) -> str:
        """Build combined anchor + target selector."""
        import re

        def xpath_to_webctrl(xpath: str) -> str:
            if xpath.strip().startswith("<"):
                return xpath.strip()
            xpath = xpath.strip()
            if xpath.startswith("//"):
                xpath = xpath[2:]
            tag_match = re.match(r"^(\w+|\*)", xpath)
            tag = tag_match.group(1) if tag_match else "*"
            attrs = [f"tag='{tag.upper()}'"]
            for m in re.finditer(r"\[@(\w+)=['\"]([^'\"]+)['\"]\]", xpath):
                attrs.append(f"{m.group(1)}='{m.group(2)}'")
            text_match = re.search(
                r"contains\s*\(\s*text\s*\(\s*\)\s*,\s*['\"]([^'\"]+)['\"]\s*\)", xpath
            )
            if text_match:
                attrs.append(f"aaname='{text_match.group(1)}'")
            return f"<webctrl {' '.join(attrs)} />"

        position_nav = {
            "left_of": "up='1'",
            "right_of": "up='1'",
            "above": "up='1'",
            "below": "up='1'",
            "inside": "",
        }

        anchor_xml = xpath_to_webctrl(anchor)
        target_xml = xpath_to_webctrl(target)
        nav = position_nav.get(position, "up='1'")

        if nav:
            return f"{anchor_xml}\n<nav {nav} />\n{target_xml}"
        return f"{anchor_xml}\n{target_xml}"

    def _on_capture_image(self):
        tab = self._tabs.get("image")
        if tab:
            asyncio.ensure_future(tab.start_picking())

    def _on_load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            try:
                from pathlib import Path

                data = Path(file_path).read_bytes()
                image = QImage.fromData(data)
                pixmap = QPixmap.fromImage(image)
                scaled = pixmap.scaled(76, 46, Qt.AspectRatioMode.KeepAspectRatio)
                self._image_preview.setPixmap(scaled)
                tab = self._tabs.get("image")
                if tab:
                    tab._template_bytes = data
            except Exception as e:
                logger.error(f"Failed to load image: {e}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pressed = True
            self._set_status("Ctrl held - click to pick", "info")
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Control:
            self._ctrl_pressed = False
            self._set_status("Ready", "default")
        super().keyReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._ctrl_pressed:
            self._start_picking(self._current_mode)
            event.accept()
            return
        super().mousePressEvent(event)

    def closeEvent(self, event):
        for tab in self._tabs.values():
            try:
                asyncio.ensure_future(tab.stop_picking())
            except Exception:
                pass
        super().closeEvent(event)


# Legacy alias
UnifiedSelectorDialog = ElementSelectorDialog

__all__ = ["ElementSelectorDialog", "UnifiedSelectorDialog"]
