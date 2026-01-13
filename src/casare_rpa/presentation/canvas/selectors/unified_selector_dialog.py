"""
Unified Selector Dialog - UiPath-inspired design.

Single-panel element picker combining:
- Browser element picking (CSS, XPath, ARIA)
- Desktop element picking (AutomationId, Name, Path)
- OCR text detection
- Image/template matching
- Fuzzy matching with accuracy controls

Design inspired by UiPath Modern Selector dialog:
- Mode toolbar at top
- Anchor section (optional)
- Collapsible configuration sections
- Target section with multiple selector types

This module serves as the main orchestrator, delegating to specialized components:
- SelectorPicker: Element picking logic
- SelectorValidator: Selector validation
- SelectorPreview: Preview rendering
- SelectorHistoryManager: History management

Epic 7.3 Migration: Migrated to THEME_V2/TOKENS_V2 (Cursor-like dark theme)
- Replaced THEME/TOKENS with THEME_V2/TOKENS_V2
- Zero hardcoded colors
- Zero animations/shadows
"""

from typing import TYPE_CHECKING, Any

from loguru import logger
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont, QImage, QKeyEvent, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.selectors.components import (
    SelectorHistoryManager,
    SelectorPicker,
    SelectorPreview,
    SelectorValidator,
)
from casare_rpa.presentation.canvas.selectors.components.selector_history_manager import (
    style_history_combo,
)
from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from casare_rpa.presentation.canvas.theme_system import THEME, TOKENS
from casare_rpa.presentation.canvas.theme_system.helpers import (
    set_fixed_height,
    set_fixed_size,
    set_fixed_width,
    set_margins,
    set_max_height,
    set_max_width,
    set_min_width,
    set_spacing,
)
from casare_rpa.presentation.canvas.theme_system.utils import alpha

if TYPE_CHECKING:
    from playwright.async_api import Page


# Theme aliases for consistency with existing code
THEME = THEME_V2
TOKENS = TOKENS_V2


# =============================================================================
# Collapsible Section Widget
# =============================================================================


class CollapsibleSection(QWidget):
    """
    A collapsible section widget with header and content.

    Click header to expand/collapse content area.
    """

    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        parent: QWidget | None = None,
        expanded: bool = True,
        accent_color: str | None = None,
    ) -> None:
        if accent_color is None:
            accent_color = THEME_V2.primary
        super().__init__(parent)
        self._expanded = expanded
        self._accent_color = accent_color
        self._animation_duration = TOKENS.sizes.combo_width_md

        self._setup_ui(title)
        self._apply_state()

    def _setup_ui(self, title: str) -> None:
        """Build collapsible section UI."""
        layout = QVBoxLayout(self)
        set_spacing(layout, 0)
        set_margins(layout, (0, 0, 0, 0))

        # Header button
        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(self._expanded)
        self._header.clicked.connect(self._on_toggle)
        self._header.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout(self._header)
        set_margins(
            header_layout,
            TOKENS.margin.standard[0],
            TOKENS.spacing.xs,
            TOKENS.margin.standard[2],
            TOKENS.spacing.xs,
        )

        # Arrow indicator
        self._arrow = QLabel()
        set_fixed_size(self._arrow, TOKENS.sizes.icon_md, TOKENS.sizes.icon_md)
        header_layout.addWidget(self._arrow)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(f"color: {self._accent_color}; font-weight: bold;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        # Optional action buttons container
        self._header_actions = QHBoxLayout()
        set_spacing(self._header_actions, TOKENS.spacing.xs)
        header_layout.addLayout(self._header_actions)

        layout.addWidget(self._header)

        # Content container
        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        set_margins(
            self._content_layout,
            TOKENS.margin.standard[0],
            TOKENS.spacing.xs,
            TOKENS.margin.standard[2],
            TOKENS.margin.standard[2],
        )
        set_spacing(self._content_layout, TOKENS.spacing.md)

        layout.addWidget(self._content_container)

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply styling using THEME_V2."""
        # Use THEME_V2 colors directly
        self._header.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.md}px;
                text-align: left;
                color: {THEME_V2.text_primary};
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_hover};
                border-color: {THEME_V2.border_light};
            }}
            QPushButton:checked {{
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }}
        """)

        self._content_container.setStyleSheet(f"""
            QWidget {{
                background: {THEME_V2.bg_canvas};
                border: 1px solid {THEME_V2.border};
                border-top: none;
                border-bottom-left-radius: {TOKENS.radius.md}px;
                border-bottom-right-radius: {TOKENS.radius.md}px;
            }}
        """)

    def _apply_state(self) -> None:
        """Apply expanded/collapsed state."""
        self._content_container.setVisible(self._expanded)
        arrow_text = "v" if self._expanded else ">"
        self._arrow.setText(arrow_text)
        self._arrow.setStyleSheet(f"color: {self._accent_color}; font-weight: bold;")

    def _on_toggle(self) -> None:
        """Handle toggle click."""
        self._expanded = self._header.isChecked()
        self._apply_state()
        self.toggled.emit(self._expanded)

    def add_header_action(self, widget: QWidget) -> None:
        """Add action button to header."""
        self._header_actions.addWidget(widget)

    def content_layout(self) -> QVBoxLayout:
        """Get content layout for adding widgets."""
        return self._content_layout

    def set_expanded(self, expanded: bool) -> None:
        """Programmatically set expanded state."""
        self._expanded = expanded
        self._header.setChecked(expanded)
        self._apply_state()

    def is_expanded(self) -> bool:
        """Check if section is expanded."""
        return self._expanded


# =============================================================================
# Mode Toolbar Button
# =============================================================================


class ModeToolButton(QToolButton):
    """Styled toolbar button for mode selection."""

    def __init__(
        self,
        icon_text: str,
        tooltip: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setText(icon_text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        set_fixed_size(
            self,
            TOKENS.sizes.button_lg + TOKENS.spacing.xs,
            TOKENS.sizes.button_lg + TOKENS.spacing.xs,
        )
        self.setCursor(Qt.PointingHandCursor)

        colors = THEME
        self.setStyleSheet(f"""
            QToolButton {{
                background: {colors.bg_component};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
                font-size: {TOKENS.typography.display_md}px;
                color: {colors.text_disabled};
            }}
            QToolButton:hover {{
                background: {colors.bg_hover};
                border-color: {colors.border_light};
                color: {colors.text_secondary};
            }}
            QToolButton:checked {{
                background: {self._accent_color};
                border-color: {self._accent_color};
                color: {THEME.text_on_primary};
            }}
        """)


# =============================================================================
# Selector Type Row Widget
# =============================================================================


class SelectorTypeRow(QWidget):
    """
    A row for a selector type with checkbox, selector display, and action buttons.

    Used in Target section for Strict/Fuzzy/CV/Image selectors.
    """

    enabled_changed = Signal(bool)
    selector_changed = Signal(str)

    def __init__(
        self,
        label: str,
        selector_type: str,
        parent: QWidget | None = None,
        has_accuracy: bool = False,
        has_radio: bool = False,
        accent_color: str | None = None,
    ) -> None:
        super().__init__(parent)
        self._selector_type = selector_type
        self._accent_color = accent_color

        self._setup_ui(label, has_accuracy, has_radio)

    def _setup_ui(self, label: str, has_accuracy: bool, has_radio: bool) -> None:
        """Build selector type row UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(TOKENS.spacing.md)
        set_margins(layout, (0, 0, 0, 0))

        # Header row with checkbox
        header = QHBoxLayout()
        set_spacing(header, TOKENS.spacing.md)

        self._checkbox = QCheckBox(label)
        self._checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {THEME.text_primary};
                font-weight: TOKENS.sizes.dialog_md_width;
            }}
            QCheckBox::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
            }}
            QCheckBox::indicator:checked {{
                background: {self._accent_color};
                border: 1px solid {self._accent_color};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)
        self._checkbox.toggled.connect(self._on_enabled_changed)
        header.addWidget(self._checkbox)

        if has_radio:
            self._radio = QCheckBox()
            self._radio.setStyleSheet(f"""
                QCheckBox::indicator {{
                    width: {TOKENS.sizes.checkbox_size - 2}px;
                    height: {TOKENS.sizes.checkbox_size - 2}px;
                    border-radius: {(TOKENS.sizes.checkbox_size - 2) // 2}px;
                }}
            """)
            self._radio.setToolTip("Use as primary selector")
            header.addWidget(self._radio)
        else:
            self._radio = None

        header.addStretch()

        # Action buttons
        self._copy_btn = QPushButton()
        self._copy_btn.setText("Copy")
        self._copy_btn.setFixedHeight(TOKENS.sizes.button_sm)
        self._copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_muted};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                color: {THEME.text_primary};
            }}
        """)
        self._copy_btn.clicked.connect(self._on_copy)
        header.addWidget(self._copy_btn)

        self._pick_btn = QPushButton()
        self._pick_btn.setText("Pick")
        self._pick_btn.setFixedHeight(TOKENS.sizes.button_sm)
        self._pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
            }}
        """)
        header.addWidget(self._pick_btn)

        layout.addLayout(header)

        # Selector value display
        self._selector_edit = QTextEdit()
        self._selector_edit.setMaximumHeight(TOKENS.sizes.text_block_max_height)
        self._selector_edit.setPlaceholderText("No selector defined")
        self._selector_edit.setFont(QFont(TOKENS.typography.mono, TOKENS.typography.body))
        colors = THEME
        self._selector_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {colors.input_bg};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px;
                color: {colors.info};
            }}
        """)
        layout.addWidget(self._selector_edit)

        # Accuracy slider (optional)
        if has_accuracy:
            accuracy_layout = QHBoxLayout()
            set_spacing(accuracy_layout, TOKENS.spacing.md)

            accuracy_label = QLabel("Accuracy:")
            accuracy_label.setStyleSheet(
                f"color: {THEME.text_disabled}; font-size: {TOKENS.typography.body}px;"
            )
            accuracy_layout.addWidget(accuracy_label)

            self._accuracy_slider = QSlider(Qt.Horizontal)
            self._accuracy_slider.setMinimum(0)
            self._accuracy_slider.setMaximum(100)
            self._accuracy_slider.setValue(100)
            self._accuracy_slider.setFixedWidth(TOKENS.sizes.input_max_width // 3)
            colors = THEME
            self._accuracy_slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: {TOKENS.spacing.xs}px;
                    background: {colors.border};
                    border-radius: {TOKENS.spacing.xs}px;
                }}
                QSlider::handle:horizontal {{
                    width: {TOKENS.sizes.slider_handle_size}px;
                    height: {TOKENS.sizes.slider_handle_size}px;
                    margin: -5px 0;
                    background: {colors.info};
                    border-radius: {TOKENS.sizes.slider_handle_size // 2}px;
                }}
                QSlider::sub-page:horizontal {{
                    background: {colors.info};
                    border-radius: {TOKENS.spacing.xs}px;
                }}
            """)
            accuracy_layout.addWidget(self._accuracy_slider)

            self._accuracy_value = QLabel("1.00")
            self._accuracy_value.setStyleSheet(
                f"color: {THEME.text_primary}; font-size: {TOKENS.typography.body}px; min-width: {TOKENS.sizes.input_min_width // 3}px;"
            )
            self._accuracy_slider.valueChanged.connect(self._update_accuracy_label)
            accuracy_layout.addWidget(self._accuracy_value)

            accuracy_layout.addStretch()
            layout.addLayout(accuracy_layout)
        else:
            self._accuracy_slider = None
            self._accuracy_value = None

        # Initially disabled appearance
        self._update_enabled_state(False)

    @Slot(int)
    def _update_accuracy_label(self, value: int) -> None:
        """Update accuracy label when slider changes."""
        if self._accuracy_value:
            self._accuracy_value.setText(f"{value / 100:.2f}")

    @Slot(bool)
    def _on_enabled_changed(self, enabled: bool) -> None:
        """Handle checkbox toggle."""
        self._update_enabled_state(enabled)
        self.enabled_changed.emit(enabled)

    def _update_enabled_state(self, enabled: bool) -> None:
        """Update visual state based on enabled."""
        self._selector_edit.setEnabled(enabled)
        self._copy_btn.setEnabled(enabled)
        self._pick_btn.setEnabled(enabled)
        if self._accuracy_slider:
            self._accuracy_slider.setEnabled(enabled)

        opacity = "1.0" if enabled else "0.5"
        colors = THEME
        self._selector_edit.setStyleSheet(f"""
            QTextEdit {{
                background: {colors.input_bg};
                border: 1px solid {colors.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px;
                color: {colors.info};
                opacity: {opacity};
            }}
        """)

    def _on_copy(self) -> None:
        """Copy selector to clipboard."""
        selector = self._selector_edit.toPlainText().strip()
        if selector:
            clipboard = QApplication.clipboard()
            clipboard.setText(selector)

    def set_selector(self, value: str) -> None:
        """Set selector value."""
        self._selector_edit.setPlainText(value)

    def get_selector(self) -> str:
        """Get selector value."""
        return self._selector_edit.toPlainText().strip()

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state."""
        self._checkbox.setChecked(enabled)

    def is_enabled(self) -> bool:
        """Check if selector type is enabled."""
        return self._checkbox.isChecked()

    def get_accuracy(self) -> float:
        """Get accuracy value (0.0-1.0)."""
        if self._accuracy_slider:
            return self._accuracy_slider.value() / 100.0
        return 1.0

    def set_accuracy(self, value: float) -> None:
        """Set accuracy value (0.0-1.0)."""
        if self._accuracy_slider:
            self._accuracy_slider.setValue(int(value * 100))

    def get_pick_button(self) -> QPushButton:
        """Get pick button for connecting signals."""
        return self._pick_btn


# =============================================================================
# Main Dialog
# =============================================================================


class UnifiedSelectorDialog(QDialog):
    """
    Unified Element Selector Dialog - UiPath-inspired design.

    Single-panel interface combining all selector methods:
    - Mode toolbar for switching between Browser/Desktop/OCR/Image
    - Collapsible configuration sections
    - Target section with multiple selector types (Strict, Fuzzy, CV, Image)
    - Accuracy sliders for fuzzy matching
    - Validate/Confirm/Cancel action bar

    This dialog orchestrates the following components:
    - SelectorPicker: Handles element picking across modes
    - SelectorValidator: Validates and tests selectors
    - SelectorPreview: Displays strategies and previews
    - SelectorHistoryManager: Manages selector history

    Signals:
        selector_selected: Emitted when user confirms selector (SelectorResult)
    """

    selector_selected = Signal(object)

    def __init__(
        self,
        parent: QWidget | None = None,
        target_node: Any | None = None,
        target_property: str = "selector",
        initial_mode: str = "browser",
    ) -> None:
        """
        Initialize the dialog.

        Args:
            parent: Parent widget
            target_node: Optional visual node to auto-paste selector to
            target_property: Property name on target node
            initial_mode: Which mode to activate first
        """
        super().__init__(parent)

        self._target_node = target_node
        self._target_property = target_property
        self._browser_page: Page | None = None
        self._current_result: SelectorResult | None = None
        self._current_mode = initial_mode
        self._ctrl_pressed = False

        # Initialize components
        self._picker = SelectorPicker(self)
        self._validator = SelectorValidator(self)
        self._history_manager = SelectorHistoryManager(self)

        # Tab references
        self._tabs: dict[str, BaseSelectorTab] = {}

        self.setWindowTitle("Element Selector")
        self.setMinimumSize(TOKENS.sizes.dialog_lg_width, TOKENS.sizes.dialog_height_xl)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self._setup_ui()
        self._create_tabs()
        self._apply_styles()
        self._connect_signals()
        self._select_mode(initial_mode)
        self._history_manager.load_history()

        logger.info("UnifiedSelectorDialog initialized (UiPath style)")

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        set_spacing(layout, 0)
        set_margins(layout, (0, 0, 0, 0))

        # Mode toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: {THEME_V2.bg_elevated};
            }
        """)

        # Scrollable content
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        set_spacing(self._content_layout, TOKENS.spacing.md + TOKENS.spacing.xs)
        set_margins(
            self._content_layout,
            TOKENS.margin.standard[0],
            TOKENS.margin.standard[0],
            TOKENS.margin.standard[2],
            TOKENS.margin.standard[2],
        )

        # Anchor section
        anchor_section = self._create_anchor_section()
        self._content_layout.addWidget(anchor_section)

        # Configuration section (collapsible)
        config_section = self._create_config_section()
        self._content_layout.addWidget(config_section)

        # Target section (main selector configuration)
        target_section = self._create_target_section()
        self._content_layout.addWidget(target_section)

        # Strategies section
        self._strategies_section = self._create_strategies_section()
        self._content_layout.addWidget(self._strategies_section)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Action bar
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)

    def _create_toolbar(self) -> QWidget:
        """Create mode selection toolbar."""
        toolbar = QWidget()
        toolbar.setFixedHeight(TOKENS.sizes.header_height_lg + TOKENS.spacing.xs)
        toolbar.setStyleSheet("""
            QWidget {
                background: {THEME_V2.bg_elevated};
                border-bottom: 1px solid {THEME.border};
            }
        """)

        layout = QHBoxLayout(toolbar)
        set_margins(
            layout,
            TOKENS.margin.standard[0],
            TOKENS.spacing.xs,
            TOKENS.margin.standard[2],
            TOKENS.spacing.xs,
        )
        set_spacing(layout, TOKENS.spacing.md)

        # Pause dropdown placeholder
        pause_btn = QPushButton("Pause")
        pause_btn.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        pause_btn.setStyleSheet("""
            QPushButton {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 12px;
                color: {THEME.text_muted};
            }
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                color: {THEME.text_primary};
            }
        """)
        layout.addWidget(pause_btn)

        layout.addSpacing(TOKENS.spacing.xs)

        # Mode buttons
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        self._browser_mode_btn = ModeToolButton("\U0001f446", "Browser Element Picker")
        self._mode_group.addButton(self._browser_mode_btn, 0)
        layout.addWidget(self._browser_mode_btn)

        self._desktop_mode_btn = ModeToolButton("\U0001f5a5", "Desktop Element Picker")
        self._mode_group.addButton(self._desktop_mode_btn, 1)
        layout.addWidget(self._desktop_mode_btn)

        self._image_mode_btn = ModeToolButton("\U0001f5bc", "Image Matching")
        self._mode_group.addButton(self._image_mode_btn, 2)
        layout.addWidget(self._image_mode_btn)

        self._ocr_mode_btn = ModeToolButton("TI", "OCR Text Recognition")
        self._mode_group.addButton(self._ocr_mode_btn, 3)
        layout.addWidget(self._ocr_mode_btn)

        layout.addSpacing(TOKENS.spacing.xs)

        # Settings button
        settings_btn = ModeToolButton("\u2699", "Settings")
        settings_btn.setCheckable(False)
        layout.addWidget(settings_btn)

        # UI Explorer button
        self._explorer_btn = QPushButton("UI Explorer")
        self._explorer_btn.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        self._explorer_btn.setToolTip("Open UI Explorer for advanced element inspection")
        self._explorer_btn.setCursor(Qt.PointingHandCursor)
        self._explorer_btn.setStyleSheet("""
            QPushButton {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 12px;
                color: {THEME.text_muted};
                font-size: {TOKENS.typography.body}px;
                font-weight: bold;
            }
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME.text_primary};
            }
            QPushButton:pressed {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME.text_primary};
            }
        """)
        self._explorer_btn.clicked.connect(self._on_open_explorer)
        layout.addWidget(self._explorer_btn)

        layout.addSpacing(TOKENS.spacing.xs)

        # History dropdown
        self._history_combo = QComboBox()
        self._history_combo.setPlaceholderText("Recent Selectors...")
        set_min_width(self._history_combo, TOKENS.sizes.panel_min_width)
        set_max_width(self._history_combo, TOKENS.sizes.panel_default_width)
        self._history_combo.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        self._history_combo.setToolTip("Select from recently used selectors")
        style_history_combo(self._history_combo)
        layout.addWidget(self._history_combo)

        # Bind history manager to combo
        self._history_manager.set_combo_box(self._history_combo)

        # Wildcard generator button
        self._wildcard_btn = QPushButton("*.*")
        set_fixed_size(
            self._wildcard_btn,
            TOKENS.sizes.button_md,
            TOKENS.sizes.button_md + TOKENS.spacing.xs,
        )
        self._wildcard_btn.setToolTip("Generate wildcard selector pattern from current selector")
        self._wildcard_btn.setCursor(Qt.PointingHandCursor)
        self._wildcard_btn.clicked.connect(self._on_generate_wildcard)
        self._wildcard_btn.setStyleSheet("""
            QPushButton {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME_V2.text_primary};
                font-size: {TOKENS.typography.body}px;
                font-weight: bold;
            }
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME_V2.text_primary};
            }
            QPushButton:pressed {{
                background: {THEME_V2.bg_elevated};
                color: {THEME_V2.text_primary};
            }
        """)
        layout.addWidget(self._wildcard_btn)

        layout.addStretch()

        # Auto dropdown
        auto_combo = QComboBox()
        auto_combo.addItems(["Auto", "Strict", "Fuzzy", "Image"])
        auto_combo.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        colors = THEME
        auto_combo.setStyleSheet(f"""
            QComboBox {{
                background: {colors.input_bg};
                border: 1px solid {colors.border_light};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.sizes.combo_dropdown_width}px {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {colors.text_primary};
                min-width: {TOKENS.sizes.button_min_width}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {TOKENS.sizes.combo_dropdown_width}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: {TOKENS.spacing.xs}px solid transparent;
                border-right: {TOKENS.spacing.xs}px solid transparent;
                border-top: {TOKENS.spacing.sm}px solid {colors.text_disabled};
                margin-right: {TOKENS.spacing.sm}px;
            }}
        """)
        layout.addWidget(auto_combo)

        # Status label
        self._status_label = QLabel("Ctrl+Click to pick")
        self._status_label.setStyleSheet(
            f"color: {colors.text_disabled}; font-size: {TOKENS.typography.body}px;"
        )
        self._status_label.setToolTip("Hold Ctrl and click anywhere to start element picking")
        layout.addWidget(self._status_label)

        return toolbar

    def _create_anchor_section(self) -> CollapsibleSection:
        """Create anchor/context section."""
        section = CollapsibleSection(
            "Anchor",
            expanded=False,
            accent_color=f"{THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle}",
        )
        self._anchor_section = section

        content = section.content_layout()

        self._anchor_data: dict[str, Any] | None = None

        # Warning banner
        colors = THEME
        self._anchor_warning = QWidget()
        self._anchor_warning.setStyleSheet(f"""
            QWidget {{
                background: {alpha(colors.warning, 0.18)};
                border: 1px solid {colors.warning};
                border-radius: {TOKENS.radius.md}px;
            }}
        """)
        warning_layout = QHBoxLayout(self._anchor_warning)
        set_margins(
            warning_layout,
            TOKENS.margin.compact[0],
            TOKENS.spacing.xs,
            TOKENS.margin.compact[2],
            TOKENS.spacing.xs,
        )

        warning_icon = QLabel("!")
        warning_icon.setStyleSheet(
            f"color: {colors.warning}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
        )
        warning_layout.addWidget(warning_icon)

        warning_text = QLabel("No anchor configured. Consider adding one for reliability.")
        warning_text.setStyleSheet(
            f"color: {colors.warning}; font-size: {TOKENS.typography.body}px;"
        )
        warning_text.setWordWrap(True)
        warning_layout.addWidget(warning_text, 1)

        content.addWidget(self._anchor_warning)

        # Success banner
        self._anchor_success = QWidget()
        self._anchor_success.setStyleSheet(f"""
            QWidget {{
                background: {alpha(colors.success, 0.18)};
                border: 1px solid {colors.success};
                border-radius: {TOKENS.radius.md}px;
            }}
        """)
        self._anchor_success.hide()
        success_layout = QHBoxLayout(self._anchor_success)
        set_margins(
            success_layout,
            TOKENS.margin.compact[0],
            TOKENS.spacing.xs,
            TOKENS.margin.compact[2],
            TOKENS.spacing.xs,
        )

        success_icon = QLabel("V")
        success_icon.setStyleSheet(
            f"color: {colors.success}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
        )
        success_layout.addWidget(success_icon)

        self._anchor_info_label = QLabel("Anchor: (none)")
        self._anchor_info_label.setStyleSheet(
            f"color: {colors.success}; font-size: {TOKENS.typography.body}px;"
        )
        self._anchor_info_label.setWordWrap(True)
        success_layout.addWidget(self._anchor_info_label, 1)

        content.addWidget(self._anchor_success)

        # Info text
        info = QLabel(
            "Anchors help identify elements when the UI changes. "
            "Pick a nearby stable element (label, heading) as reference."
        )
        info.setStyleSheet(
            f"color: {colors.text_disabled}; font-size: {TOKENS.typography.caption}px;"
        )
        info.setWordWrap(True)
        content.addWidget(info)

        # Button row
        button_row = QHBoxLayout()
        set_spacing(button_row, TOKENS.spacing.md)

        self._pick_anchor_btn = QPushButton("Pick Anchor")
        self._pick_anchor_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._pick_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._pick_anchor_btn.setStyleSheet("""
            QPushButton {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 16px;
                color: {THEME_V2.text_primary};
                font-weight: bold;
                font-size: {TOKENS.typography.body}px;
            }
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
            }
            QPushButton:disabled {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME.text_muted};
            }
        """)
        self._pick_anchor_btn.clicked.connect(self._on_pick_anchor)
        button_row.addWidget(self._pick_anchor_btn)

        self._auto_anchor_btn = QPushButton("Auto-detect")
        self._auto_anchor_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._auto_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._auto_anchor_btn.setToolTip("Automatically find the best anchor for current target")
        self._auto_anchor_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
            }}
            QPushButton:disabled {{
                color: {THEME.text_disabled};
            }}
        """)
        self._auto_anchor_btn.clicked.connect(self._on_auto_detect_anchor)
        button_row.addWidget(self._auto_anchor_btn)

        self._clear_anchor_btn = QPushButton("Clear")
        self._clear_anchor_btn.setFixedHeight(TOKENS.sizes.button_lg)
        self._clear_anchor_btn.setEnabled(False)
        self._clear_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._clear_anchor_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME.text_primary};
            }}
            QPushButton:disabled {{
                color: {THEME.text_disabled};
            }}
        """)
        self._clear_anchor_btn.clicked.connect(self._on_clear_anchor)
        button_row.addWidget(self._clear_anchor_btn)

        button_row.addStretch()
        content.addLayout(button_row)

        # Anchor details
        self._anchor_details = QWidget()
        self._anchor_details.hide()
        details_layout = QVBoxLayout(self._anchor_details)
        set_margins(details_layout, 0, TOKENS.spacing.xs, 0, 0)
        set_spacing(details_layout, TOKENS.spacing.xs)

        position_row = QHBoxLayout()
        set_spacing(position_row, TOKENS.spacing.xs)

        position_label = QLabel("Position:")
        position_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption}px;"
        )
        position_row.addWidget(position_label)

        self._anchor_position_combo = QComboBox()
        self._anchor_position_combo.addItems(["Left", "Right", "Above", "Below", "Inside", "Near"])
        self._anchor_position_combo.setCurrentText("Left")
        self._anchor_position_combo.setFixedWidth(TOKENS.sizes.input_max_width // 4)
        self._anchor_position_combo.setStyleSheet(f"""
            QComboBox {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: {TOKENS.spacing.md + TOKENS.spacing.xs}px;
            }}
        """)
        self._anchor_position_combo.currentTextChanged.connect(self._on_anchor_position_changed)
        position_row.addWidget(self._anchor_position_combo)

        position_row.addStretch()
        details_layout.addLayout(position_row)

        self._anchor_selector_display = QTextEdit()
        set_max_height(self._anchor_selector_display, TOKENS.sizes.input_min_height)
        self._anchor_selector_display.setReadOnly(True)
        self._anchor_selector_display.setPlaceholderText("Anchor selector...")
        self._anchor_selector_display.setFont(QFont("Consolas", 9))
        self._anchor_selector_display.setStyleSheet("""
            QTextEdit {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME_V2.text_primary};
            }
        """)
        details_layout.addWidget(self._anchor_selector_display)

        content.addWidget(self._anchor_details)

        return section

    def _create_config_section(self) -> CollapsibleSection:
        """Create collapsible configuration section."""
        section = CollapsibleSection("Options", expanded=False)

        content = section.content_layout()

        window_layout = QHBoxLayout()
        window_label = QLabel("Window Selector:")
        window_label.setStyleSheet("color: {THEME.text_primary};")
        window_layout.addWidget(window_label)

        self._window_selector = QLineEdit()
        self._window_selector.setPlaceholderText("<wnd app='...' title='...' />")
        self._window_selector.setStyleSheet("""
            QLineEdit {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME_V2.text_primary};
                font-family: Consolas;
            }
        """)
        window_layout.addWidget(self._window_selector, 1)

        content.addLayout(window_layout)

        self._wait_visible = QCheckBox("Wait for element to be visible")
        self._wait_visible.setChecked(True)
        self._wait_visible.setStyleSheet("color: {THEME.text_primary};")
        content.addWidget(self._wait_visible)

        self._highlight_element = QCheckBox("Highlight element before action")
        self._highlight_element.setChecked(False)
        self._highlight_element.setStyleSheet("color: {THEME.text_primary};")
        content.addWidget(self._highlight_element)

        return section

    def _create_target_section(self) -> CollapsibleSection:
        """Create target selector section."""
        section = CollapsibleSection(
            "Target",
            expanded=True,
            accent_color=f"{THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle}",
        )

        content = section.content_layout()

        # Quick Text Search
        text_search_group = QWidget()
        text_search_group.setStyleSheet("""
            QWidget {
                background: {alpha(THEME_V2.bg_selected, 0.15)};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.md}px;
            }
        """)
        text_search_layout = QVBoxLayout(text_search_group)
        set_margins(
            text_search_layout,
            TOKENS.margin.compact[0],
            TOKENS.spacing.xs,
            TOKENS.margin.compact[2],
            TOKENS.spacing.xs,
        )
        set_spacing(text_search_layout, TOKENS.spacing.xs)

        text_search_header = QHBoxLayout()
        text_search_label = QLabel("Quick Text Search (case-insensitive)")
        text_search_label.setStyleSheet(
            f"color: {THEME_V2.text_primary}; font-weight: bold; font-size: {TOKENS.typography.body}px;"
        )
        text_search_header.addWidget(text_search_label)
        text_search_header.addStretch()
        text_search_layout.addLayout(text_search_header)

        text_input_layout = QHBoxLayout()
        set_spacing(text_input_layout, TOKENS.spacing.xs)

        self._text_search_element = QComboBox()
        self._text_search_element.addItems(
            ["*", "button", "a", "span", "div", "input", "label", "h1", "h2", "p"]
        )
        self._text_search_element.setCurrentText("*")
        set_fixed_width(self._text_search_element, TOKENS.sizes.input_min_width)
        self._text_search_element.setToolTip("Element type (* = any)")
        self._text_search_element.setStyleSheet("""
            QComboBox {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 8px;
                color: {THEME.text_primary};
            }
        """)
        self._text_search_element.currentTextChanged.connect(self._on_text_search_changed)
        text_input_layout.addWidget(self._text_search_element)

        self._text_search_input = QLineEdit()
        self._text_search_input.setPlaceholderText(
            "Enter text to find (e.g., Start, Submit, Login)"
        )
        self._text_search_input.setStyleSheet("""
            QLineEdit {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 8px;
                color: {THEME.text_primary};
            }
            QLineEdit:focus {
                border-color: {THEME_V2.border};
            }
        """)
        self._text_search_input.textChanged.connect(self._on_text_search_changed)
        text_input_layout.addWidget(self._text_search_input, 1)

        self._text_search_btn = QPushButton("Generate")
        self._text_search_btn.setFixedHeight(TOKENS.sizes.button_md)
        self._text_search_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.xs}px {TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
            }}
            QPushButton:disabled {{
                background: {alpha(THEME_V2.bg_selected, 0.2)};
                color: {THEME.text_disabled};
            }}
        """)
        self._text_search_btn.clicked.connect(self._on_generate_text_selector)
        text_input_layout.addWidget(self._text_search_btn)

        text_search_layout.addLayout(text_input_layout)

        text_search_info = QLabel("Finds elements containing text regardless of case")
        text_search_info.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.caption - 1}px;"
        )
        text_search_layout.addWidget(text_search_info)

        content.addWidget(text_search_group)

        # Separators and selector rows
        sep0 = QFrame()
        sep0.setFrameShape(QFrame.HLine)
        sep0.setStyleSheet(
            "background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
        )
        sep0.setFixedHeight(TOKENS.spacing.xs // 2)
        content.addWidget(sep0)

        self._strict_selector = SelectorTypeRow(
            "Strict selector",
            "strict",
            has_accuracy=False,
            accent_color=f"{THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle}",
        )
        self._strict_selector.set_enabled(True)
        content.addWidget(self._strict_selector)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(
            "background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
        )
        sep1.setFixedHeight(TOKENS.spacing.xs // 2)
        content.addWidget(sep1)

        self._fuzzy_selector = SelectorTypeRow(
            "Fuzzy selector",
            "fuzzy",
            has_accuracy=True,
            has_radio=True,
            accent_color=None,
        )
        content.addWidget(self._fuzzy_selector)

        # Fuzzy options
        fuzzy_options = QWidget()
        fuzzy_layout = QGridLayout(fuzzy_options)
        set_margins(fuzzy_layout, TOKENS.spacing.xl, 0, 0, 0)
        set_spacing(fuzzy_layout, TOKENS.spacing.xs)

        fuzzy_layout.addWidget(QLabel("InnerText:"), 0, 0)
        self._fuzzy_innertext_combo = QComboBox()
        self._fuzzy_innertext_combo.addItems(
            ["Contains", "Equals", "StartsWith", "EndsWith", "Regex"]
        )
        self._fuzzy_innertext_combo.setStyleSheet("""
            QComboBox {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 8px;
                color: {THEME.text_primary};
                min-width: {TOKENS.sizes.button_width_sm}px;
            }
        """)
        fuzzy_layout.addWidget(self._fuzzy_innertext_combo, 0, 1)

        self._fuzzy_innertext_value = QLineEdit()
        self._fuzzy_innertext_value.setPlaceholderText("Text to match...")
        self._fuzzy_innertext_value.setStyleSheet("""
            QLineEdit {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.text_primary};
            }
        """)
        fuzzy_layout.addWidget(self._fuzzy_innertext_value, 0, 2)

        content.addWidget(fuzzy_options)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(
            "background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
        )
        sep2.setFixedHeight(TOKENS.spacing.xs // 2)
        content.addWidget(sep2)

        self._cv_selector = SelectorTypeRow(
            "Computer Vision", "cv", has_accuracy=True, accent_color=f"{THEME.wire_list}"
        )
        content.addWidget(self._cv_selector)

        # CV options
        cv_options = QWidget()
        cv_layout = QHBoxLayout(cv_options)
        set_margins(cv_layout, TOKENS.spacing.xl, 0, 0, 0)
        set_spacing(cv_layout, TOKENS.spacing.xs)

        cv_layout.addWidget(QLabel("Element type:"))
        self._cv_element_type = QComboBox()
        self._cv_element_type.addItems(
            ["Button", "Link", "Input", "Text", "Image", "Checkbox", "Any"]
        )
        self._cv_element_type.setStyleSheet("""
            QComboBox {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 8px;
                color: {THEME.text_primary};
                min-width: {TOKENS.sizes.button_min_width}px;
            }
        """)
        cv_layout.addWidget(self._cv_element_type)

        self._cv_text = QLineEdit()
        self._cv_text.setPlaceholderText("Visible text...")
        self._cv_text.setStyleSheet("""
            QLineEdit {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px;
                color: {THEME.text_primary};
            }
        """)
        cv_layout.addWidget(self._cv_text, 1)

        content.addWidget(cv_options)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet(
            "background: {THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle};"
        )
        sep3.setFixedHeight(TOKENS.spacing.xs // 2)
        content.addWidget(sep3)

        self._image_selector = SelectorTypeRow(
            "Image", "image", has_accuracy=True, accent_color=f"{THEME.node_skipped}"
        )
        content.addWidget(self._image_selector)

        # Image preview
        image_preview = QWidget()
        image_layout = QHBoxLayout(image_preview)
        set_margins(image_layout, TOKENS.spacing.xl, 0, 0, 0)
        set_spacing(image_layout, TOKENS.spacing.xs)

        self._image_preview_label = QLabel("No image captured")
        set_fixed_size(
            self._image_preview_label, TOKENS.sizes.thumbnail_width, TOKENS.sizes.thumbnail_height
        )
        self._image_preview_label.setAlignment(Qt.AlignCenter)
        self._image_preview_label.setStyleSheet("""
            QLabel {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                color: {THEME.text_muted};
                font-size: {TOKENS.typography.caption}px;
            }
        """)
        image_layout.addWidget(self._image_preview_label)

        image_buttons = QVBoxLayout()
        set_spacing(image_buttons, TOKENS.spacing.xs)

        self._capture_image_btn = QPushButton("Capture")
        self._capture_image_btn.setStyleSheet("""
            QPushButton {
                background: {THEME.node_skipped};
                border: 1px solid {THEME.node_skipped};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 12px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }
            QPushButton:hover {{
                background: {THEME.node_skipped};
            }
        """)
        image_buttons.addWidget(self._capture_image_btn)

        self._load_image_btn = QPushButton("Load File")
        self._load_image_btn.setStyleSheet("""
            QPushButton {
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.sm}px 12px;
                color: {THEME.text_primary};
                font-size: {TOKENS.typography.body}px;
            }
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
            }
        """)
        image_buttons.addWidget(self._load_image_btn)

        image_buttons.addStretch()
        image_layout.addLayout(image_buttons)
        image_layout.addStretch()

        content.addWidget(image_preview)

        return section

    def _create_strategies_section(self) -> CollapsibleSection:
        """Create strategies list section."""
        section = CollapsibleSection(
            "Generated Selectors",
            expanded=False,
            accent_color=f"{THEME.bg_canvas|THEME.bg_header|THEME.bg_surface|THEME.bg_component|THEME.bg_hover|THEME.bg_border|THEME.bg_surface|THEME.primary|THEME.primary_hover|THEME.primary|THEME.error|THEME.warning|THEME.primary|THEME.success|THEME.warning|THEME.error|THEME.info|THEME.node_running|THEME.node_idle}",
        )

        content = section.content_layout()

        # Create preview component and add to content
        self._preview = SelectorPreview(self)
        content.addWidget(self._preview)

        return section

    def _create_action_bar(self) -> QWidget:
        """Create action bar."""
        bar = QWidget()
        bar.setFixedHeight(TOKENS.sizes.footer_height + TOKENS.spacing.xs)
        bar.setStyleSheet("""
            QWidget {
                background: {THEME_V2.bg_elevated};
                border-top: 1px solid {THEME.border};
            }
        """)

        layout = QHBoxLayout(bar)
        set_margins(
            layout,
            TOKENS.margin.standard[0],
            TOKENS.spacing.md,
            TOKENS.margin.standard[2],
            TOKENS.spacing.md,
        )
        set_spacing(layout, TOKENS.spacing.md + TOKENS.spacing.xs)

        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        self._validate_btn.clicked.connect(self._on_validate)
        self._validate_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.md}px {TOKENS.spacing.xl}px;
                color: {THEME.text_primary};
                font-weight: TOKENS.sizes.dialog_md_width;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME.border_light};
            }}
        """)
        layout.addWidget(self._validate_btn)

        layout.addStretch()

        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        self._confirm_btn.setDefault(True)
        self._confirm_btn.clicked.connect(self._on_confirm)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.md}px {TOKENS.spacing.xl + TOKENS.spacing.md}px;
                color: {THEME.text_primary};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
            }}
            QPushButton:disabled {{
                background: {alpha(THEME_V2.bg_component, 0.5)};
                border-color: {THEME_V2.border};
                color: {THEME_V2.text_disabled};
            }}
        """)
        layout.addWidget(self._confirm_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(TOKENS.sizes.button_lg + TOKENS.spacing.xs)
        self._cancel_btn.clicked.connect(self.reject)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
                padding: {TOKENS.spacing.md}px {TOKENS.spacing.xl}px;
                color: {THEME.text_primary};
                font-weight: TOKENS.sizes.dialog_md_width;
            }}
            QPushButton:hover {{
                background: {THEME_V2.bg_elevated};
                border-color: {THEME_V2.border};
                color: {THEME.text_primary};
            }}
        """)
        layout.addWidget(self._cancel_btn)

        return bar

    def _create_tabs(self) -> None:
        """Create tab instances for functionality."""
        from casare_rpa.presentation.canvas.selectors.tabs.browser_tab import (
            BrowserSelectorTab,
        )
        from casare_rpa.presentation.canvas.selectors.tabs.desktop_tab import (
            DesktopSelectorTab,
        )
        from casare_rpa.presentation.canvas.selectors.tabs.image_match_tab import (
            ImageMatchTab,
        )
        from casare_rpa.presentation.canvas.selectors.tabs.ocr_tab import OCRSelectorTab

        # Browser tab
        self._browser_tab = BrowserSelectorTab(self)
        self._browser_tab.hide()
        self._tabs["browser"] = self._browser_tab
        self._picker.register_tab("browser", self._browser_tab)
        self._validator.register_tab("browser", self._browser_tab)

        if self._browser_page:
            self._browser_tab.set_browser_page(self._browser_page)

        # Desktop tab
        self._desktop_tab = DesktopSelectorTab(self)
        self._desktop_tab.hide()
        self._tabs["desktop"] = self._desktop_tab
        self._picker.register_tab("desktop", self._desktop_tab)
        self._validator.register_tab("desktop", self._desktop_tab)

        # OCR tab
        self._ocr_tab = OCRSelectorTab(self)
        self._ocr_tab.hide()
        self._tabs["ocr"] = self._ocr_tab
        self._picker.register_tab("ocr", self._ocr_tab)
        self._validator.register_tab("ocr", self._ocr_tab)

        # Image tab
        self._image_tab = ImageMatchTab(self)
        self._image_tab.hide()
        self._tabs["image"] = self._image_tab
        self._picker.register_tab("image", self._image_tab)
        self._validator.register_tab("image", self._image_tab)

    def _apply_styles(self) -> None:
        """Apply global dialog styling."""
        self.setStyleSheet(f"""
            QDialog {{
                background: {THEME_V2.bg_elevated};
                color: {THEME.text_primary};
            }}
            QLabel {{
                color: {THEME.text_primary};
            }}
            QCheckBox {{
                color: {THEME.text_primary};
            }}
            QCheckBox::indicator {{
                width: {TOKENS.sizes.checkbox_size}px;
                height: {TOKENS.sizes.checkbox_size}px;
            }}
            QCheckBox::indicator:unchecked {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME.border};
                border-radius: {TOKENS.radius.sm}px;
            }}
            QCheckBox::indicator:checked {{
                background: {THEME_V2.bg_elevated};
                border: 1px solid {THEME_V2.border};
                border-radius: {TOKENS.radius.sm}px;
            }}
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Mode button group
        self._mode_group.idClicked.connect(self._on_mode_changed)

        # Selector row pick buttons - using named methods instead of lambdas
        self._strict_selector.get_pick_button().clicked.connect(self._on_strict_pick_clicked)
        self._fuzzy_selector.get_pick_button().clicked.connect(self._on_fuzzy_pick_clicked)
        self._cv_selector.get_pick_button().clicked.connect(self._on_cv_pick_clicked)
        self._image_selector.get_pick_button().clicked.connect(self._on_image_pick_clicked)

        # Image buttons
        self._capture_image_btn.clicked.connect(self._on_capture_image)
        self._load_image_btn.clicked.connect(self._on_load_image)

        # Picker component signals
        self._picker.strategies_generated.connect(self._on_strategies_generated)
        self._picker.status_changed.connect(self._on_status_changed)
        self._picker.element_screenshot_captured.connect(self._on_element_screenshot_captured)
        self._picker.anchor_picked.connect(self._on_anchor_picked)

        # Preview component signals
        self._preview.strategy_selected.connect(self._on_strategy_selected)

        # History component signals
        self._history_manager.selector_selected.connect(self._on_history_selected)

    def _select_mode(self, mode: str) -> None:
        """Select initial mode."""
        mode_map = {
            "browser": self._browser_mode_btn,
            "desktop": self._desktop_mode_btn,
            "image": self._image_mode_btn,
            "ocr": self._ocr_mode_btn,
        }
        btn = mode_map.get(mode)
        if btn:
            btn.setChecked(True)
            self._current_mode = mode
            self._picker.set_current_mode(mode)
            self._validator.set_current_mode(mode)

    # =========================================================================
    # Public API
    # =========================================================================

    def set_browser_page(self, page: "Page") -> None:
        """Set the browser page for browser-related operations."""
        logger.info(f"UnifiedSelectorDialog.set_browser_page: page={page is not None}")
        self._browser_page = page
        self._picker.set_browser_page(page)
        for tab in self._tabs.values():
            tab.set_browser_page(page)

    def set_target_node(self, node: Any, property_name: str = "selector") -> None:
        """Set target node for auto-pasting selector."""
        self._target_node = node
        self._target_property = property_name
        for tab in self._tabs.values():
            tab.set_target_node(node, property_name)

    def get_result(self) -> SelectorResult | None:
        """Get the selected selector result."""
        return self._current_result

    # =========================================================================
    # Event Handlers
    # =========================================================================

    @Slot(int)
    def _on_mode_changed(self, mode_id: int) -> None:
        """Handle mode button change."""
        mode_map = {0: "browser", 1: "desktop", 2: "image", 3: "ocr"}
        mode = mode_map.get(mode_id, "browser")
        self._current_mode = mode
        self._picker.set_current_mode(mode)
        self._validator.set_current_mode(mode)

        for m, tab in self._tabs.items():
            tab.set_active(m == mode)

        logger.debug(f"Mode changed to: {mode}")

    @Slot()
    def _on_strict_pick_clicked(self) -> None:
        """Handle strict selector pick button click."""
        self._start_picking(self._current_mode)

    @Slot()
    def _on_fuzzy_pick_clicked(self) -> None:
        """Handle fuzzy selector pick button click."""
        self._start_picking(self._current_mode)

    @Slot()
    def _on_cv_pick_clicked(self) -> None:
        """Handle CV selector pick button click."""
        self._start_picking("ocr")

    @Slot()
    def _on_image_pick_clicked(self) -> None:
        """Handle image selector pick button click."""
        self._start_picking("image")

    @Slot()
    def _on_open_explorer(self) -> None:
        """Open the UI Explorer dialog."""
        from casare_rpa.presentation.canvas.selectors.ui_explorer import (
            UIExplorerDialog,
        )

        current_tab = self._tabs.get(self._current_mode)
        initial_element = None
        if current_tab:
            result = current_tab.get_current_selector()
            if result and result.healing_context:
                initial_element = result.healing_context

        dialog = UIExplorerDialog(
            parent=self,
            mode=self._current_mode,
            browser_page=self._browser_page,
            initial_element=initial_element,
        )

        dialog.selector_confirmed.connect(self._on_explorer_selector_confirmed)

        logger.info(f"Opening UI Explorer (mode={self._current_mode})")
        dialog.exec()

    @Slot(str)
    def _on_explorer_selector_confirmed(self, selector: str) -> None:
        """Handle selector confirmed from UI Explorer."""
        if selector:
            self._strict_selector.set_selector(selector)
            self._strict_selector.set_enabled(True)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Selector imported from UI Explorer")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            logger.info(f"Imported selector from UI Explorer: {selector[:50]}...")

    @Slot(str)
    def _on_history_selected(self, selector: str) -> None:
        """Apply selected history item to selector input."""
        if selector:
            self._strict_selector.set_selector(selector)
            self._strict_selector.set_enabled(True)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Selector loaded from history")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            logger.info(f"Loaded selector from history: {selector[:50]}...")

    @Slot()
    def _on_generate_wildcard(self) -> None:
        """Generate wildcard version of current selector."""
        current = self._strict_selector.get_selector()
        if not current:
            self._status_label.setText("No selector to convert to wildcard")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px;"
            )
            return

        wildcard = self._validator.generate_wildcard_selector(current)
        if wildcard:
            self._strict_selector.set_selector(wildcard)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Generated wildcard selector")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
        else:
            self._status_label.setText("Selector has no patterns to convert")
            self._status_label.setStyleSheet(
                f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
            )

    def _start_picking(self, mode: str) -> None:
        """Start element picking for specified mode."""
        import asyncio

        if mode == "browser" and not self._picker.has_browser_page():
            self._status_label.setText("Run a Navigate node first to open browser")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            self._preview.set_test_result(
                "Browser element picking requires an active browser.\n"
                "Run a workflow with a Navigate node first, then try again.",
                f"padding: {TOKENS.spacing.md}px; background: {alpha(THEME_V2.bg_selected, 0.2)}; color: {THEME_V2.text_primary}; border-radius: {TOKENS.radius.sm}px;",
            )
            logger.warning("Cannot start browser picking: no browser page")
            return

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._picker.start_picking(mode))
            else:
                loop.run_until_complete(self._picker.start_picking(mode))
        except Exception as e:
            logger.error(f"Failed to start picking: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px;"
            )

    @Slot(list)
    def _on_strategies_generated(self, strategies: list[SelectorStrategy]) -> None:
        """Handle strategies generated from picker."""
        logger.info(f"Dialog received {len(strategies)} strategies")

        self._preview.set_strategies(strategies)

        if strategies:
            self._strategies_section.set_expanded(True)
            best = strategies[0]
            self._strict_selector.set_selector(best.value)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText(f"{len(strategies)} selectors generated")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
        else:
            self._confirm_btn.setEnabled(False)

    @Slot(object)
    def _on_strategy_selected(self, strategy: SelectorStrategy) -> None:
        """Handle strategy selection from preview."""
        self._strict_selector.set_selector(strategy.value)
        self._confirm_btn.setEnabled(True)
        self._picker.update_result_from_strategy(strategy)
        self._current_result = self._picker.current_result

    @Slot(str)
    def _on_status_changed(self, message: str) -> None:
        """Handle status message from picker."""
        self._status_label.setText(message)

    def _on_element_screenshot_captured(self, screenshot_bytes: bytes) -> None:
        """Handle element screenshot captured."""
        logger.info(f"Element screenshot captured: {len(screenshot_bytes)} bytes")

        image_tab = self._tabs.get("image")
        if image_tab:
            image_tab.set_template_from_bytes(screenshot_bytes)

        try:
            image = QImage.fromData(screenshot_bytes)
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(
                TOKENS.sizes.thumbnail_width,
                TOKENS.sizes.thumbnail_height - TOKENS.spacing.xs,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._image_preview_label.setPixmap(scaled)

            self._image_selector.set_enabled(True)
            self._status_label.setText("Element image captured for template matching")
            self._status_label.setStyleSheet(
                f"color: {THEME.node_skipped}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )

        except Exception as e:
            logger.error(f"Failed to display element screenshot: {e}")

    def _on_validate(self) -> None:
        """Validate current selector."""
        import asyncio

        selector = self._strict_selector.get_selector()
        if not selector:
            self._preview.set_test_result(
                "No selector to validate",
                f"padding: {TOKENS.spacing.md}px; background: {alpha(THEME_V2.bg_selected, 0.2)}; color: {THEME_V2.text_primary}; border-radius: {TOKENS.radius.sm}px;",
            )
            return

        selected = self._preview.get_selected_strategy()
        selector_type = selected.selector_type if selected else "xpath"

        asyncio.ensure_future(self._do_validate(selector, selector_type))

    async def _do_validate(self, selector: str, selector_type: str) -> None:
        """Perform async validation."""
        result = await self._validator.validate_selector(selector, selector_type)
        message = self._validator.format_validation_message(result)
        style = self._validator.get_validation_style(result)
        self._preview.set_test_result(message, style)

    def _on_confirm(self) -> None:
        """Confirm and use the selected selector."""
        if not self._current_result:
            selector = self._strict_selector.get_selector()
            if not selector:
                return

            selected = self._preview.get_selected_strategy()
            if selected:
                self._current_result = SelectorResult(
                    selector_value=selector,
                    selector_type=selected.selector_type,
                    confidence=selected.score / 100.0,
                    is_unique=selected.is_unique,
                )
            else:
                self._current_result = SelectorResult(
                    selector_value=selector,
                    selector_type="xpath",
                    confidence=0.5,
                )

        # Add metadata from UI settings
        result = self._current_result

        if self._fuzzy_selector.is_enabled():
            result.metadata["fuzzy_accuracy"] = self._fuzzy_selector.get_accuracy()
            result.metadata["fuzzy_innertext"] = self._fuzzy_innertext_value.text()
            result.metadata["fuzzy_match_type"] = self._fuzzy_innertext_combo.currentText()

        if self._cv_selector.is_enabled():
            result.metadata["cv_accuracy"] = self._cv_selector.get_accuracy()
            result.metadata["cv_element_type"] = self._cv_element_type.currentText()
            result.metadata["cv_text"] = self._cv_text.text()

        if self._image_selector.is_enabled():
            result.metadata["image_accuracy"] = self._image_selector.get_accuracy()

        if self._anchor_data:
            result.metadata["anchor"] = self._anchor_data

        # Auto-paste to target node
        if self._target_node and self._target_property:
            try:
                widget = self._target_node.get_widget(self._target_property)
                if widget:
                    widget.set_value(result.selector_value)
                    logger.info(
                        f"Auto-pasted selector to {self._target_node.name()}.{self._target_property}"
                    )

                if result.healing_context:
                    healing_key = f"{self._target_property}_healing_context"
                    casare_node = getattr(self._target_node, "_casare_node", None)
                    if casare_node and hasattr(casare_node, "config"):
                        casare_node.config[healing_key] = result.healing_context
                        logger.info(f"Stored healing context in {healing_key}")
            except Exception as e:
                logger.error(f"Failed to auto-paste: {e}")

        # Save to history
        self._history_manager.save_selector(
            result.selector_value,
            result.selector_type,
        )

        self.selector_selected.emit(result)
        logger.info(f"Selector confirmed: {result.selector_value[:50]}...")
        self.accept()

    def _on_capture_image(self) -> None:
        """Capture image for template matching."""
        import asyncio

        image_tab = self._tabs.get("image")
        if image_tab:
            asyncio.ensure_future(image_tab.start_picking())

    def _on_load_image(self) -> None:
        """Load image file for template matching."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Template Image",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp);;All Files (*.*)",
        )

        if file_path:
            try:
                from pathlib import Path

                path = Path(file_path)
                image_bytes = path.read_bytes()

                image = QImage.fromData(image_bytes)
                pixmap = QPixmap.fromImage(image)
                scaled = pixmap.scaled(
                    TOKENS.sizes.thumbnail_width,
                    TOKENS.sizes.thumbnail_height - TOKENS.spacing.xs,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._image_preview_label.setPixmap(scaled)

                image_tab = self._tabs.get("image")
                if image_tab:
                    image_tab._template_bytes = image_bytes
                    image_tab._display_template()
                    image_tab._update_find_button()

                self._status_label.setText(f"Image loaded: {path.name}")

            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                self._status_label.setText(f"Error: {e}")

    def _on_text_search_changed(self) -> None:
        """Handle text search input change."""
        text = self._text_search_input.text().strip()
        self._text_search_btn.setEnabled(bool(text))

    def _on_generate_text_selector(self) -> None:
        """Generate itext= selector from text search input."""
        text = self._text_search_input.text().strip()
        if not text:
            return

        element = self._text_search_element.currentText()

        try:
            result = self._validator.generate_text_selector(text, element)

            self._strict_selector.set_selector(result.selector_value)
            self._strict_selector.set_enabled(True)
            self._confirm_btn.setEnabled(True)
            self._current_result = result

            self._status_label.setText(f"Generated text selector: {result.selector_value}")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )

        except ValueError as e:
            logger.error(f"Failed to generate text selector: {e}")

    # =========================================================================
    # Anchor Management
    # =========================================================================

    def _on_pick_anchor(self) -> None:
        """Start anchor picking mode."""
        import asyncio

        if self._current_mode == "browser" and not self._picker.has_browser_page():
            self._status_label.setText("Run a Navigate node first to open browser")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            return

        self._status_label.setText("ANCHOR MODE: Ctrl+Click a reference element...")
        self._status_label.setStyleSheet(
            "color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
        )
        self._pick_anchor_btn.setText("Picking...")
        self._pick_anchor_btn.setEnabled(False)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._do_pick_anchor())
            else:
                loop.run_until_complete(self._do_pick_anchor())
        except Exception as e:
            logger.error(f"Failed to start anchor picking: {e}")
            self._reset_anchor_picking_ui()

    async def _do_pick_anchor(self) -> None:
        """Perform async anchor picking."""
        try:
            await self._picker.start_anchor_picking()
        except Exception as e:
            logger.error(f"Anchor picking failed: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px;"
            )
        finally:
            self._reset_anchor_picking_ui()

    def _on_anchor_picked(self, anchor_data: dict[str, Any]) -> None:
        """Handle anchor element picked."""
        self._set_anchor(
            {
                "selector": anchor_data.get("selector", ""),
                "tag_name": "",
                "text_content": anchor_data.get("selector", "")[:30],
                "position": "left",
                "stability_score": anchor_data.get("score", 0) / 100.0,
            }
        )

    def _reset_anchor_picking_ui(self) -> None:
        """Reset anchor picking button state."""
        self._pick_anchor_btn.setText("Pick Anchor")
        self._pick_anchor_btn.setEnabled(True)

    def _on_auto_detect_anchor(self) -> None:
        """Auto-detect the best anchor for current target element."""
        import asyncio

        if self._current_mode == "browser" and not self._picker.has_browser_page():
            self._status_label.setText("No browser open - cannot auto-detect anchor")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            return

        target_selector = self._strict_selector.get_selector()
        if not target_selector:
            self._status_label.setText("Select a target element first")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
            return

        self._status_label.setText("Auto-detecting anchor...")
        self._status_label.setStyleSheet(
            "color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
        )
        self._auto_anchor_btn.setEnabled(False)

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._do_auto_detect_anchor(target_selector))
            else:
                loop.run_until_complete(self._do_auto_detect_anchor(target_selector))
        except Exception as e:
            logger.error(f"Failed to auto-detect anchor: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px;"
            )
            self._auto_anchor_btn.setEnabled(True)

    async def _do_auto_detect_anchor(self, target_selector: str) -> None:
        """Perform async anchor auto-detection."""
        try:
            anchor_data = await self._picker.auto_detect_anchor(target_selector)

            if anchor_data:
                self._set_anchor(anchor_data)
                self._status_label.setText("Anchor auto-detected successfully")
                self._status_label.setStyleSheet(
                    "color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
                )
            else:
                self._status_label.setText("No suitable anchor found nearby")
                self._status_label.setStyleSheet(
                    "color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
                )
        except Exception as e:
            logger.error(f"Anchor auto-detection failed: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px;"
            )
        finally:
            self._auto_anchor_btn.setEnabled(True)

    def _on_clear_anchor(self) -> None:
        """Clear the configured anchor."""
        self._anchor_data = None

        self._anchor_warning.show()
        self._anchor_success.hide()
        self._anchor_details.hide()
        self._clear_anchor_btn.setEnabled(False)

        self._status_label.setText("Anchor cleared")
        self._status_label.setStyleSheet(
            f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
        )

        if self._current_result and self._current_result.metadata:
            self._current_result.metadata.pop("anchor", None)

        logger.debug("Anchor cleared")

    def _on_anchor_position_changed(self, position: str) -> None:
        """Handle anchor position dropdown change."""
        if self._anchor_data:
            self._anchor_data["position"] = position.lower()
            logger.debug(f"Anchor position changed to: {position}")

    def _set_anchor(self, anchor_data: dict[str, Any]) -> None:
        """Set the anchor data and update UI."""
        self._anchor_data = anchor_data

        self._anchor_warning.hide()
        self._anchor_success.show()
        self._anchor_details.show()
        self._clear_anchor_btn.setEnabled(True)

        tag = anchor_data.get("tag_name", "element")
        text = anchor_data.get("text_content", "")
        if text:
            display_text = text[:30] + "..." if len(text) > 30 else text
            self._anchor_info_label.setText(f"Anchor: <{tag}> {display_text}")
        else:
            selector = anchor_data.get("selector", "")
            short_sel = selector[:40] + "..." if len(selector) > 40 else selector
            self._anchor_info_label.setText(f"Anchor: {short_sel}")

        position = anchor_data.get("position", "left")
        position_text = position.capitalize()
        if position_text in ["Left", "Right", "Above", "Below", "Inside", "Near"]:
            self._anchor_position_combo.setCurrentText(position_text)

        selector = anchor_data.get("selector", "")
        self._anchor_selector_display.setPlainText(selector)

        self._anchor_section.set_expanded(True)

        if self._current_result:
            self._current_result.metadata["anchor"] = anchor_data

        logger.info(f"Anchor set: {tag} - {text[:30] if text else selector[:30]}")

    def set_anchor_from_element(self, element_data: dict[str, Any], position: str = "left") -> None:
        """Set anchor from picked element data."""
        from casare_rpa.presentation.canvas.selectors.ui_explorer.models.anchor_model import (
            calculate_anchor_stability,
        )

        tag = element_data.get("tag", element_data.get("tag_or_control", ""))
        attrs = element_data.get("attributes", {})
        text = element_data.get("text", element_data.get("text_content", ""))

        selector = ""
        if attrs.get("id"):
            selector = f"#{attrs['id']}"
        elif attrs.get("data-testid"):
            selector = f'[data-testid="{attrs["data-testid"]}"]'
        elif text and len(text) < 50:
            escaped_text = text.replace('"', '\\"')
            selector = f'{tag}:has-text("{escaped_text}")'
        elif attrs.get("class"):
            first_class = attrs["class"].split()[0] if attrs["class"] else ""
            if first_class:
                selector = f"{tag}.{first_class}"
            else:
                selector = tag
        else:
            selector = tag

        stability = calculate_anchor_stability(tag, attrs, text)

        anchor_data = {
            "selector": selector,
            "tag_name": tag,
            "text_content": text,
            "position": position,
            "attributes": attrs,
            "stability_score": stability,
            "fingerprint": element_data,
        }

        self._set_anchor(anchor_data)

    def get_anchor_data(self) -> dict[str, Any] | None:
        """Get the configured anchor data."""
        return self._anchor_data

    # =========================================================================
    # Key/Mouse Event Handlers
    # =========================================================================

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key_Control:
            self._ctrl_pressed = True
            self._status_label.setText("Ctrl held - click to pick element")
            self._status_label.setStyleSheet(
                f"color: {THEME_V2.text_primary}; font-size: {TOKENS.typography.body}px; font-weight: bold;"
            )
        elif event.key() == Qt.Key_Escape:
            self.reject()

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events."""
        if event.key() == Qt.Key_Control:
            self._ctrl_pressed = False
            self._status_label.setText("Ctrl+Click to pick")
            self._status_label.setStyleSheet(
                f"color: {THEME.text_muted}; font-size: {TOKENS.typography.body}px;"
            )

        super().keyReleaseEvent(event)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press events."""
        from PySide6.QtCore import Qt as QtCore

        if event.button() == QtCore.LeftButton and getattr(self, "_ctrl_pressed", False):
            self._start_picking(self._current_mode)
            event.accept()
            return

        super().mousePressEvent(event)

    def closeEvent(self, event) -> None:
        """Handle dialog close - stop any active picking."""
        import asyncio

        asyncio.ensure_future(self._picker.stop_picking())
        super().closeEvent(event)
