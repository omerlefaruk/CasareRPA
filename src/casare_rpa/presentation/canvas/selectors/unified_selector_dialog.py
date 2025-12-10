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
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QEvent
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QKeyEvent
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QSplitter,
    QStackedWidget,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from loguru import logger

from casare_rpa.presentation.canvas.selectors.tabs.base_tab import (
    BaseSelectorTab,
    SelectorResult,
    SelectorStrategy,
)
from PySide6.QtWidgets import QDialog

if TYPE_CHECKING:
    from playwright.async_api import Page


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
        parent: Optional[QWidget] = None,
        expanded: bool = True,
        accent_color: str = "#60a5fa",
    ) -> None:
        super().__init__(parent)
        self._expanded = expanded
        self._accent_color = accent_color
        self._animation_duration = 150

        self._setup_ui(title)
        self._apply_state()

    def _setup_ui(self, title: str) -> None:
        """Build collapsible section UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header button
        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(self._expanded)
        self._header.clicked.connect(self._on_toggle)
        self._header.setCursor(Qt.PointingHandCursor)

        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(12, 8, 12, 8)

        # Arrow indicator
        self._arrow = QLabel()
        self._arrow.setFixedSize(16, 16)
        header_layout.addWidget(self._arrow)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet(
            f"color: {self._accent_color}; font-weight: bold;"
        )
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        # Optional action buttons container
        self._header_actions = QHBoxLayout()
        self._header_actions.setSpacing(4)
        header_layout.addLayout(self._header_actions)

        layout.addWidget(self._header)

        # Content container
        self._content_container = QWidget()
        self._content_layout = QVBoxLayout(self._content_container)
        self._content_layout.setContentsMargins(12, 8, 12, 12)
        self._content_layout.setSpacing(8)

        layout.addWidget(self._content_container)

        self._apply_styles()

    def _apply_styles(self) -> None:
        """Apply styling."""
        self._header.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                text-align: left;
            }
            QPushButton:hover {
                background: #333333;
                border-color: #4a4a4a;
            }
            QPushButton:checked {
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }
        """)

        self._content_container.setStyleSheet("""
            QWidget {
                background: #252525;
                border: 1px solid #3a3a3a;
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
            }
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
    """
    Styled toolbar button for mode selection.
    """

    def __init__(
        self,
        icon_text: str,
        tooltip: str,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setText(icon_text)
        self.setToolTip(tooltip)
        self.setCheckable(True)
        self.setFixedSize(40, 40)
        self.setCursor(Qt.PointingHandCursor)

        self.setStyleSheet("""
            QToolButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                font-size: 16px;
                color: #888888;
            }
            QToolButton:hover {
                background: #333333;
                border-color: #4a4a4a;
                color: #e0e0e0;
            }
            QToolButton:checked {
                background: #3b82f6;
                border-color: #2563eb;
                color: white;
            }
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
        parent: Optional[QWidget] = None,
        has_accuracy: bool = False,
        has_radio: bool = False,
        accent_color: str = "#60a5fa",
    ) -> None:
        super().__init__(parent)
        self._selector_type = selector_type
        self._accent_color = accent_color

        self._setup_ui(label, has_accuracy, has_radio)

    def _setup_ui(self, label: str, has_accuracy: bool, has_radio: bool) -> None:
        """Build selector type row UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header row with checkbox
        header = QHBoxLayout()
        header.setSpacing(8)

        self._checkbox = QCheckBox(label)
        self._checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: #e0e0e0;
                font-weight: 500;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
            }}
            QCheckBox::indicator:checked {{
                background: {self._accent_color};
                border: 1px solid {self._accent_color};
                border-radius: 3px;
            }}
        """)
        self._checkbox.toggled.connect(self._on_enabled_changed)
        header.addWidget(self._checkbox)

        if has_radio:
            # Radio button for primary selection
            self._radio = QCheckBox()
            self._radio.setStyleSheet("""
                QCheckBox::indicator {
                    width: 14px;
                    height: 14px;
                    border-radius: 7px;
                }
            """)
            self._radio.setToolTip("Use as primary selector")
            header.addWidget(self._radio)
        else:
            self._radio = None

        header.addStretch()

        # Action buttons
        self._copy_btn = QPushButton()
        self._copy_btn.setText("Copy")
        self._copy_btn.setFixedHeight(24)
        self._copy_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 2px 8px;
                color: #888;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #3a3a3a;
                color: #e0e0e0;
            }
        """)
        self._copy_btn.clicked.connect(self._on_copy)
        header.addWidget(self._copy_btn)

        self._pick_btn = QPushButton()
        self._pick_btn.setText("Pick")
        self._pick_btn.setFixedHeight(24)
        self._pick_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 4px;
                padding: 2px 8px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #2563eb;
            }
        """)
        header.addWidget(self._pick_btn)

        layout.addLayout(header)

        # Selector value display
        self._selector_edit = QTextEdit()
        self._selector_edit.setMaximumHeight(60)
        self._selector_edit.setPlaceholderText("No selector defined")
        self._selector_edit.setFont(QFont("Consolas", 9))
        self._selector_edit.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #60a5fa;
            }
        """)
        layout.addWidget(self._selector_edit)

        # Accuracy slider (optional)
        if has_accuracy:
            accuracy_layout = QHBoxLayout()
            accuracy_layout.setSpacing(8)

            accuracy_label = QLabel("Accuracy:")
            accuracy_label.setStyleSheet("color: #888; font-size: 11px;")
            accuracy_layout.addWidget(accuracy_label)

            self._accuracy_slider = QSlider(Qt.Horizontal)
            self._accuracy_slider.setMinimum(0)
            self._accuracy_slider.setMaximum(100)
            self._accuracy_slider.setValue(80)
            self._accuracy_slider.setFixedWidth(120)
            self._accuracy_slider.setStyleSheet("""
                QSlider::groove:horizontal {
                    height: 4px;
                    background: #3a3a3a;
                    border-radius: 2px;
                }
                QSlider::handle:horizontal {
                    width: 14px;
                    height: 14px;
                    margin: -5px 0;
                    background: #60a5fa;
                    border-radius: 7px;
                }
                QSlider::sub-page:horizontal {
                    background: #3b82f6;
                    border-radius: 2px;
                }
            """)
            accuracy_layout.addWidget(self._accuracy_slider)

            self._accuracy_value = QLabel("0.80")
            self._accuracy_value.setStyleSheet(
                "color: #e0e0e0; font-size: 11px; min-width: 32px;"
            )
            self._accuracy_slider.valueChanged.connect(
                lambda v: self._accuracy_value.setText(f"{v/100:.2f}")
            )
            accuracy_layout.addWidget(self._accuracy_value)

            accuracy_layout.addStretch()
            layout.addLayout(accuracy_layout)
        else:
            self._accuracy_slider = None
            self._accuracy_value = None

        # Initially disabled appearance
        self._update_enabled_state(False)

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
        self._selector_edit.setStyleSheet(f"""
            QTextEdit {{
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #60a5fa;
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

    Signals:
        selector_selected: Emitted when user confirms selector (SelectorResult)
    """

    selector_selected = Signal(object)  # SelectorResult

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        target_node: Optional[Any] = None,
        target_property: str = "selector",
        initial_mode: str = "browser",
    ) -> None:
        """
        Initialize the dialog.

        Args:
            parent: Parent widget
            target_node: Optional visual node to auto-paste selector to
            target_property: Property name on target node
            initial_mode: Which mode to activate first ("browser", "desktop", "ocr", "image")
        """
        super().__init__(parent)

        self._target_node = target_node
        self._target_property = target_property
        self._browser_page: Optional["Page"] = None
        self._current_result: Optional[SelectorResult] = None
        self._current_mode = initial_mode
        self._strategies: List[SelectorStrategy] = []
        self._ctrl_pressed = False  # Track Ctrl key for Ctrl+LMB picking
        self._picking_anchor: bool = False  # Track anchor picking mode

        # Tab references for functionality
        self._tabs: Dict[str, BaseSelectorTab] = {}

        self.setWindowTitle("Element Selector")
        self.setMinimumSize(700, 800)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMaximizeButtonHint)

        self._setup_ui()
        self._create_tabs()
        self._apply_styles()
        self._connect_signals()
        self._select_mode(initial_mode)
        self._load_selector_history()

        logger.info("UnifiedSelectorDialog initialized (UiPath style)")

    def _setup_ui(self) -> None:
        """Build the UI layout."""
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

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
                background: #1e1e1e;
            }
        """)

        # Scrollable content
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(12)
        self._content_layout.setContentsMargins(16, 16, 16, 16)

        # Anchor section
        anchor_section = self._create_anchor_section()
        self._content_layout.addWidget(anchor_section)

        # Configuration section (collapsible)
        config_section = self._create_config_section()
        self._content_layout.addWidget(config_section)

        # Target section (main selector configuration)
        target_section = self._create_target_section()
        self._content_layout.addWidget(target_section)

        # Strategies list
        self._strategies_section = self._create_strategies_section()
        self._content_layout.addWidget(self._strategies_section)

        self._content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        # Action bar (Validate | Confirm | Cancel)
        action_bar = self._create_action_bar()
        layout.addWidget(action_bar)

    def _create_toolbar(self) -> QWidget:
        """Create mode selection toolbar."""
        toolbar = QWidget()
        toolbar.setFixedHeight(56)
        toolbar.setStyleSheet("""
            QWidget {
                background: #252525;
                border-bottom: 1px solid #3a3a3a;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Pause dropdown placeholder
        pause_btn = QPushButton("Pause")
        pause_btn.setFixedHeight(36)
        pause_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #888;
            }
            QPushButton:hover {
                background: #4a4a4a;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(pause_btn)

        layout.addSpacing(8)

        # Mode buttons
        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        # Browser mode (pointer/finger icon)
        self._browser_mode_btn = ModeToolButton("\U0001f446", "Browser Element Picker")
        self._mode_group.addButton(self._browser_mode_btn, 0)
        layout.addWidget(self._browser_mode_btn)

        # Desktop mode (computer icon)
        self._desktop_mode_btn = ModeToolButton("\U0001f5a5", "Desktop Element Picker")
        self._mode_group.addButton(self._desktop_mode_btn, 1)
        layout.addWidget(self._desktop_mode_btn)

        # Image mode
        self._image_mode_btn = ModeToolButton("\U0001f5bc", "Image Matching")
        self._mode_group.addButton(self._image_mode_btn, 2)
        layout.addWidget(self._image_mode_btn)

        # OCR mode (text icon)
        self._ocr_mode_btn = ModeToolButton("TI", "OCR Text Recognition")
        self._mode_group.addButton(self._ocr_mode_btn, 3)
        layout.addWidget(self._ocr_mode_btn)

        layout.addSpacing(8)

        # Settings button
        settings_btn = ModeToolButton("\u2699", "Settings")
        settings_btn.setCheckable(False)
        layout.addWidget(settings_btn)

        # UI Explorer button - use visible text instead of emoji
        self._explorer_btn = QPushButton("UI Explorer")
        self._explorer_btn.setFixedHeight(36)
        self._explorer_btn.setToolTip(
            "Open UI Explorer for advanced element inspection"
        )
        self._explorer_btn.setCursor(Qt.PointingHandCursor)
        self._explorer_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #888;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #333333;
                border-color: #4a4a4a;
                color: #e0e0e0;
            }
            QPushButton:pressed {
                background: #3b82f6;
                border-color: #2563eb;
                color: white;
            }
        """)
        self._explorer_btn.clicked.connect(self._on_open_explorer)
        layout.addWidget(self._explorer_btn)

        layout.addSpacing(8)

        # History dropdown - recent selectors
        self._history_combo = QComboBox()
        self._history_combo.setPlaceholderText("Recent Selectors...")
        self._history_combo.setMinimumWidth(200)
        self._history_combo.setMaximumWidth(300)
        self._history_combo.setFixedHeight(36)
        self._history_combo.setToolTip("Select from recently used selectors")
        self._history_combo.currentIndexChanged.connect(self._on_history_selected)
        self._history_combo.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 24px 4px 8px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #888;
                margin-right: 8px;
            }
            QComboBox:hover {
                background: #333333;
                border-color: #4a4a4a;
            }
            QComboBox QAbstractItemView {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                selection-background-color: #3b82f6;
                color: #e0e0e0;
            }
        """)
        layout.addWidget(self._history_combo)

        # Wildcard generator button
        self._wildcard_btn = QPushButton("*.*")
        self._wildcard_btn.setFixedSize(40, 36)
        self._wildcard_btn.setToolTip(
            "Generate wildcard selector pattern from current selector"
        )
        self._wildcard_btn.setCursor(Qt.PointingHandCursor)
        self._wildcard_btn.clicked.connect(self._on_generate_wildcard)
        self._wildcard_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #f59e0b;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #333333;
                border-color: #f59e0b;
                color: #fbbf24;
            }
            QPushButton:pressed {
                background: #f59e0b;
                color: #1a1a1a;
            }
        """)
        layout.addWidget(self._wildcard_btn)

        layout.addStretch()

        # Auto dropdown
        auto_combo = QComboBox()
        auto_combo.addItems(["Auto", "Strict", "Fuzzy", "Image"])
        auto_combo.setFixedHeight(36)
        auto_combo.setStyleSheet("""
            QComboBox {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 24px 4px 12px;
                color: #e0e0e0;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 6px solid #888;
                margin-right: 8px;
            }
        """)
        layout.addWidget(auto_combo)

        # Status label with shortcut hint
        self._status_label = QLabel("Ctrl+Click to pick")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")
        self._status_label.setToolTip(
            "Hold Ctrl and click anywhere to start element picking"
        )
        layout.addWidget(self._status_label)

        return toolbar

    def _create_anchor_section(self) -> CollapsibleSection:
        """Create anchor/context section with UiPath-style anchoring UI."""
        section = CollapsibleSection("Anchor", expanded=False, accent_color="#fbbf24")
        self._anchor_section = section

        content = section.content_layout()

        # Anchor state
        self._anchor_data: Optional[Dict[str, Any]] = None

        # Warning banner (shown when no anchor)
        self._anchor_warning = QWidget()
        self._anchor_warning.setStyleSheet("""
            QWidget {
                background: #3d3520;
                border: 1px solid #fbbf24;
                border-radius: 6px;
            }
        """)
        warning_layout = QHBoxLayout(self._anchor_warning)
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

        content.addWidget(self._anchor_warning)

        # Success banner (shown when anchor is set)
        self._anchor_success = QWidget()
        self._anchor_success.setStyleSheet("""
            QWidget {
                background: #1a3d2e;
                border: 1px solid #10b981;
                border-radius: 6px;
            }
        """)
        self._anchor_success.hide()
        success_layout = QHBoxLayout(self._anchor_success)
        success_layout.setContentsMargins(12, 8, 12, 8)

        success_icon = QLabel("V")
        success_icon.setStyleSheet(
            "color: #10b981; font-size: 14px; font-weight: bold;"
        )
        success_layout.addWidget(success_icon)

        self._anchor_info_label = QLabel("Anchor: (none)")
        self._anchor_info_label.setStyleSheet("color: #10b981; font-size: 12px;")
        self._anchor_info_label.setWordWrap(True)
        success_layout.addWidget(self._anchor_info_label, 1)

        content.addWidget(self._anchor_success)

        # Info text
        info = QLabel(
            "Anchors help identify elements when the UI changes. "
            "Pick a nearby stable element (label, heading) as reference."
        )
        info.setStyleSheet("color: #888; font-size: 11px;")
        info.setWordWrap(True)
        content.addWidget(info)

        # Button row
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        # Pick Anchor button
        self._pick_anchor_btn = QPushButton("Pick Anchor")
        self._pick_anchor_btn.setFixedHeight(32)
        self._pick_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._pick_anchor_btn.setStyleSheet("""
            QPushButton {
                background: #fbbf24;
                border: 1px solid #f59e0b;
                border-radius: 4px;
                padding: 4px 16px;
                color: #1a1a1a;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #f59e0b;
            }
            QPushButton:disabled {
                background: #4a4a4a;
                border-color: #3a3a3a;
                color: #888;
            }
        """)
        self._pick_anchor_btn.clicked.connect(self._on_pick_anchor)
        button_row.addWidget(self._pick_anchor_btn)

        # Auto-detect Anchor button
        self._auto_anchor_btn = QPushButton("Auto-detect")
        self._auto_anchor_btn.setFixedHeight(32)
        self._auto_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._auto_anchor_btn.setToolTip(
            "Automatically find the best anchor for current target"
        )
        self._auto_anchor_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #3a3a3a;
                border-color: #4a4a4a;
            }
            QPushButton:disabled {
                color: #666;
            }
        """)
        self._auto_anchor_btn.clicked.connect(self._on_auto_detect_anchor)
        button_row.addWidget(self._auto_anchor_btn)

        # Clear Anchor button
        self._clear_anchor_btn = QPushButton("Clear")
        self._clear_anchor_btn.setFixedHeight(32)
        self._clear_anchor_btn.setEnabled(False)
        self._clear_anchor_btn.setCursor(Qt.PointingHandCursor)
        self._clear_anchor_btn.setStyleSheet("""
            QPushButton {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #ef4444;
                border-color: #dc2626;
                color: white;
            }
            QPushButton:disabled {
                color: #666;
            }
        """)
        self._clear_anchor_btn.clicked.connect(self._on_clear_anchor)
        button_row.addWidget(self._clear_anchor_btn)

        button_row.addStretch()
        content.addLayout(button_row)

        # Anchor details section (shown when anchor is set)
        self._anchor_details = QWidget()
        self._anchor_details.hide()
        details_layout = QVBoxLayout(self._anchor_details)
        details_layout.setContentsMargins(0, 8, 0, 0)
        details_layout.setSpacing(8)

        # Position row
        position_row = QHBoxLayout()
        position_row.setSpacing(8)

        position_label = QLabel("Position:")
        position_label.setStyleSheet("color: #888; font-size: 11px;")
        position_row.addWidget(position_label)

        self._anchor_position_combo = QComboBox()
        self._anchor_position_combo.addItems(
            ["Left", "Right", "Above", "Below", "Inside", "Near"]
        )
        self._anchor_position_combo.setCurrentText("Left")
        self._anchor_position_combo.setFixedWidth(100)
        self._anchor_position_combo.setStyleSheet("""
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
        self._anchor_position_combo.currentTextChanged.connect(
            self._on_anchor_position_changed
        )
        position_row.addWidget(self._anchor_position_combo)

        position_row.addStretch()
        details_layout.addLayout(position_row)

        # Selector display
        self._anchor_selector_display = QTextEdit()
        self._anchor_selector_display.setMaximumHeight(50)
        self._anchor_selector_display.setReadOnly(True)
        self._anchor_selector_display.setPlaceholderText("Anchor selector...")
        self._anchor_selector_display.setFont(QFont("Consolas", 9))
        self._anchor_selector_display.setStyleSheet("""
            QTextEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #fbbf24;
            }
        """)
        details_layout.addWidget(self._anchor_selector_display)

        content.addWidget(self._anchor_details)

        return section

    def _create_config_section(self) -> CollapsibleSection:
        """Create collapsible configuration section."""
        section = CollapsibleSection("Options", expanded=False)

        content = section.content_layout()

        # Window selector option
        window_layout = QHBoxLayout()
        window_label = QLabel("Window Selector:")
        window_label.setStyleSheet("color: #e0e0e0;")
        window_layout.addWidget(window_label)

        self._window_selector = QLineEdit()
        self._window_selector.setPlaceholderText("<wnd app='...' title='...' />")
        self._window_selector.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #60a5fa;
                font-family: Consolas;
            }
        """)
        window_layout.addWidget(self._window_selector, 1)

        content.addLayout(window_layout)

        # Additional options
        self._wait_visible = QCheckBox("Wait for element to be visible")
        self._wait_visible.setChecked(True)
        self._wait_visible.setStyleSheet("color: #e0e0e0;")
        content.addWidget(self._wait_visible)

        self._highlight_element = QCheckBox("Highlight element before action")
        self._highlight_element.setChecked(False)
        self._highlight_element.setStyleSheet("color: #e0e0e0;")
        content.addWidget(self._highlight_element)

        return section

    def _create_target_section(self) -> CollapsibleSection:
        """Create target selector section with all selector types."""
        section = CollapsibleSection("Target", expanded=True, accent_color="#10b981")

        content = section.content_layout()

        # Quick Text Search (itext= generator)
        text_search_group = QWidget()
        text_search_group.setStyleSheet("""
            QWidget {
                background: #1a2a1a;
                border: 1px solid #10b981;
                border-radius: 6px;
            }
        """)
        text_search_layout = QVBoxLayout(text_search_group)
        text_search_layout.setContentsMargins(12, 8, 12, 8)
        text_search_layout.setSpacing(8)

        # Header
        text_search_header = QHBoxLayout()
        text_search_icon = QLabel("🔍")
        text_search_header.addWidget(text_search_icon)
        text_search_label = QLabel("Quick Text Search (case-insensitive)")
        text_search_label.setStyleSheet(
            "color: #10b981; font-weight: bold; font-size: 12px;"
        )
        text_search_header.addWidget(text_search_label)
        text_search_header.addStretch()
        text_search_layout.addLayout(text_search_header)

        # Input row
        text_input_layout = QHBoxLayout()
        text_input_layout.setSpacing(8)

        # Element type dropdown
        self._text_search_element = QComboBox()
        self._text_search_element.addItems(
            ["*", "button", "a", "span", "div", "input", "label", "h1", "h2", "p"]
        )
        self._text_search_element.setCurrentText("*")
        self._text_search_element.setFixedWidth(80)
        self._text_search_element.setToolTip("Element type (* = any)")
        self._text_search_element.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                color: #e0e0e0;
            }
        """)
        self._text_search_element.currentTextChanged.connect(
            self._on_text_search_changed
        )
        text_input_layout.addWidget(self._text_search_element)

        # Text input
        self._text_search_input = QLineEdit()
        self._text_search_input.setPlaceholderText(
            "Enter text to find (e.g., Start, Submit, Login)"
        )
        self._text_search_input.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px 8px;
                color: #e0e0e0;
            }
            QLineEdit:focus {
                border-color: #10b981;
            }
        """)
        self._text_search_input.textChanged.connect(self._on_text_search_changed)
        text_input_layout.addWidget(self._text_search_input, 1)

        # Generate button
        self._text_search_btn = QPushButton("Generate")
        self._text_search_btn.setFixedHeight(30)
        self._text_search_btn.setStyleSheet("""
            QPushButton {
                background: #10b981;
                border: 1px solid #059669;
                border-radius: 4px;
                padding: 4px 16px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #059669;
            }
            QPushButton:disabled {
                background: #1a3a2a;
                color: #666;
            }
        """)
        self._text_search_btn.clicked.connect(self._on_generate_text_selector)
        text_input_layout.addWidget(self._text_search_btn)

        text_search_layout.addLayout(text_input_layout)

        # Info label
        text_search_info = QLabel(
            "Finds elements containing text regardless of case (Start, START, start)"
        )
        text_search_info.setStyleSheet("color: #888; font-size: 10px;")
        text_search_layout.addWidget(text_search_info)

        content.addWidget(text_search_group)

        # Separator
        sep0 = QFrame()
        sep0.setFrameShape(QFrame.HLine)
        sep0.setStyleSheet("background: #3a3a3a;")
        sep0.setFixedHeight(1)
        content.addWidget(sep0)

        # Strict Selector
        self._strict_selector = SelectorTypeRow(
            "Strict selector",
            "strict",
            has_accuracy=False,
            accent_color="#3b82f6",
        )
        self._strict_selector.set_enabled(True)
        content.addWidget(self._strict_selector)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet("background: #3a3a3a;")
        sep1.setFixedHeight(1)
        content.addWidget(sep1)

        # Fuzzy Selector
        self._fuzzy_selector = SelectorTypeRow(
            "Fuzzy selector",
            "fuzzy",
            has_accuracy=True,
            has_radio=True,
            accent_color="#f59e0b",
        )
        content.addWidget(self._fuzzy_selector)

        # Fuzzy options
        fuzzy_options = QWidget()
        fuzzy_layout = QGridLayout(fuzzy_options)
        fuzzy_layout.setContentsMargins(24, 0, 0, 0)
        fuzzy_layout.setSpacing(8)

        fuzzy_layout.addWidget(QLabel("InnerText:"), 0, 0)
        self._fuzzy_innertext_combo = QComboBox()
        self._fuzzy_innertext_combo.addItems(
            ["Contains", "Equals", "StartsWith", "EndsWith", "Regex"]
        )
        self._fuzzy_innertext_combo.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 100px;
            }
        """)
        fuzzy_layout.addWidget(self._fuzzy_innertext_combo, 0, 1)

        self._fuzzy_innertext_value = QLineEdit()
        self._fuzzy_innertext_value.setPlaceholderText("Text to match...")
        self._fuzzy_innertext_value.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
        """)
        fuzzy_layout.addWidget(self._fuzzy_innertext_value, 0, 2)

        content.addWidget(fuzzy_options)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("background: #3a3a3a;")
        sep2.setFixedHeight(1)
        content.addWidget(sep2)

        # Computer Vision Selector
        self._cv_selector = SelectorTypeRow(
            "Computer Vision",
            "cv",
            has_accuracy=True,
            accent_color="#8b5cf6",
        )
        content.addWidget(self._cv_selector)

        # CV options
        cv_options = QWidget()
        cv_layout = QHBoxLayout(cv_options)
        cv_layout.setContentsMargins(24, 0, 0, 0)
        cv_layout.setSpacing(8)

        cv_layout.addWidget(QLabel("Element type:"))
        self._cv_element_type = QComboBox()
        self._cv_element_type.addItems(
            ["Button", "Link", "Input", "Text", "Image", "Checkbox", "Any"]
        )
        self._cv_element_type.setStyleSheet("""
            QComboBox {
                background: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 4px 8px;
                color: #e0e0e0;
                min-width: 80px;
            }
        """)
        cv_layout.addWidget(self._cv_element_type)

        self._cv_text = QLineEdit()
        self._cv_text.setPlaceholderText("Visible text...")
        self._cv_text.setStyleSheet("""
            QLineEdit {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                padding: 6px;
                color: #e0e0e0;
            }
        """)
        cv_layout.addWidget(self._cv_text, 1)

        content.addWidget(cv_options)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("background: #3a3a3a;")
        sep3.setFixedHeight(1)
        content.addWidget(sep3)

        # Image Selector
        self._image_selector = SelectorTypeRow(
            "Image",
            "image",
            has_accuracy=True,
            accent_color="#ec4899",
        )
        content.addWidget(self._image_selector)

        # Image preview
        image_preview = QWidget()
        image_layout = QHBoxLayout(image_preview)
        image_layout.setContentsMargins(24, 0, 0, 0)
        image_layout.setSpacing(8)

        self._image_preview_label = QLabel("No image captured")
        self._image_preview_label.setFixedSize(120, 80)
        self._image_preview_label.setAlignment(Qt.AlignCenter)
        self._image_preview_label.setStyleSheet("""
            QLabel {
                background: #1a1a1a;
                border: 1px solid #3a3a3a;
                border-radius: 4px;
                color: #888;
                font-size: 10px;
            }
        """)
        image_layout.addWidget(self._image_preview_label)

        image_buttons = QVBoxLayout()
        image_buttons.setSpacing(4)

        self._capture_image_btn = QPushButton("Capture")
        self._capture_image_btn.setStyleSheet("""
            QPushButton {
                background: #ec4899;
                border: 1px solid #db2777;
                border-radius: 4px;
                padding: 4px 12px;
                color: white;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #db2777;
            }
        """)
        image_buttons.addWidget(self._capture_image_btn)

        self._load_image_btn = QPushButton("Load File")
        self._load_image_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #e0e0e0;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #4a4a4a;
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
            "Generated Selectors", expanded=False, accent_color="#60a5fa"
        )

        content = section.content_layout()

        # Info label
        self._strategies_info = QLabel("Pick an element to generate selectors")
        self._strategies_info.setStyleSheet("color: #888; font-size: 11px;")
        content.addWidget(self._strategies_info)

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
        content.addWidget(self._strategies_list)

        # Test result
        self._test_result = QLabel("")
        self._test_result.setWordWrap(True)
        self._test_result.setStyleSheet(
            "padding: 8px; background: #252525; border-radius: 4px; color: #e0e0e0; font-size: 11px;"
        )
        content.addWidget(self._test_result)

        return section

    def _create_action_bar(self) -> QWidget:
        """Create action bar with Validate | Confirm | Cancel buttons."""
        bar = QWidget()
        bar.setFixedHeight(64)
        bar.setStyleSheet("""
            QWidget {
                background: #252525;
                border-top: 1px solid #3a3a3a;
            }
        """)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # Validate button
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setFixedHeight(36)
        self._validate_btn.clicked.connect(self._on_validate)
        self._validate_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 8px 24px;
                color: #e0e0e0;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #4a4a4a;
                border-color: #5a5a5a;
            }
        """)
        layout.addWidget(self._validate_btn)

        layout.addStretch()

        # Confirm button (primary action)
        self._confirm_btn = QPushButton("Confirm")
        self._confirm_btn.setFixedHeight(36)
        self._confirm_btn.setDefault(True)
        self._confirm_btn.clicked.connect(self._on_confirm)
        self._confirm_btn.setEnabled(False)
        self._confirm_btn.setStyleSheet("""
            QPushButton {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 6px;
                padding: 8px 32px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #2563eb;
            }
            QPushButton:disabled {
                background: #1e3a5f;
                border-color: #1e3a5f;
                color: #666;
            }
        """)
        layout.addWidget(self._confirm_btn)

        # Cancel button
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setFixedHeight(36)
        self._cancel_btn.clicked.connect(self.reject)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background: #3a3a3a;
                border: 1px solid #4a4a4a;
                border-radius: 6px;
                padding: 8px 24px;
                color: #e0e0e0;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #ef4444;
                border-color: #dc2626;
                color: white;
            }
        """)
        layout.addWidget(self._cancel_btn)

        return bar

    def _create_tabs(self) -> None:
        """Create tab instances for functionality (not displayed as tabs)."""
        from casare_rpa.presentation.canvas.selectors.tabs.browser_tab import (
            BrowserSelectorTab,
        )
        from casare_rpa.presentation.canvas.selectors.tabs.desktop_tab import (
            DesktopSelectorTab,
        )
        from casare_rpa.presentation.canvas.selectors.tabs.ocr_tab import OCRSelectorTab
        from casare_rpa.presentation.canvas.selectors.tabs.image_match_tab import (
            ImageMatchTab,
        )

        # Browser tab (hidden, used for functionality)
        self._browser_tab = BrowserSelectorTab(self)
        self._browser_tab.selectors_generated.connect(self._on_strategies_generated)
        self._browser_tab.status_changed.connect(self._on_status_changed)
        self._browser_tab.element_screenshot_captured.connect(
            self._on_element_screenshot_captured
        )
        self._browser_tab.hide()
        self._tabs["browser"] = self._browser_tab
        # Pass browser page to tab if available
        if self._browser_page:
            self._browser_tab.set_browser_page(self._browser_page)

        # Desktop tab
        self._desktop_tab = DesktopSelectorTab(self)
        self._desktop_tab.selectors_generated.connect(self._on_strategies_generated)
        self._desktop_tab.status_changed.connect(self._on_status_changed)
        self._desktop_tab.hide()
        self._tabs["desktop"] = self._desktop_tab

        # OCR tab
        self._ocr_tab = OCRSelectorTab(self)
        self._ocr_tab.selectors_generated.connect(self._on_strategies_generated)
        self._ocr_tab.status_changed.connect(self._on_status_changed)
        self._ocr_tab.hide()
        self._tabs["ocr"] = self._ocr_tab

        # Image tab
        self._image_tab = ImageMatchTab(self)
        self._image_tab.selectors_generated.connect(self._on_strategies_generated)
        self._image_tab.status_changed.connect(self._on_status_changed)
        self._image_tab.hide()
        self._tabs["image"] = self._image_tab

    def _apply_styles(self) -> None:
        """Apply global dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QCheckBox {
                color: #e0e0e0;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background: #2a2a2a;
                border: 1px solid #4a4a4a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #3b82f6;
                border: 1px solid #2563eb;
                border-radius: 3px;
            }
        """)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        # Mode button group
        self._mode_group.idClicked.connect(self._on_mode_changed)

        # Selector row pick buttons - use current mode for strict/fuzzy
        self._strict_selector.get_pick_button().clicked.connect(
            lambda: self._start_picking(self._current_mode)
        )
        self._fuzzy_selector.get_pick_button().clicked.connect(
            lambda: self._start_picking(self._current_mode)
        )
        self._cv_selector.get_pick_button().clicked.connect(
            lambda: self._start_picking("ocr")
        )
        self._image_selector.get_pick_button().clicked.connect(
            lambda: self._start_picking("image")
        )

        # Image buttons
        self._capture_image_btn.clicked.connect(self._on_capture_image)
        self._load_image_btn.clicked.connect(self._on_load_image)

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

    # =========================================================================
    # Public API
    # =========================================================================

    def set_browser_page(self, page: "Page") -> None:
        """Set the browser page for browser-related operations."""
        logger.info(
            f"UnifiedSelectorDialog.set_browser_page called: page={page is not None}"
        )
        self._browser_page = page
        for tab_name, tab in self._tabs.items():
            logger.debug(f"Setting browser page on tab: {tab_name}")
            tab.set_browser_page(page)

    def set_target_node(self, node: Any, property_name: str = "selector") -> None:
        """Set target node for auto-pasting selector."""
        self._target_node = node
        self._target_property = property_name
        for tab in self._tabs.values():
            tab.set_target_node(node, property_name)

    def get_result(self) -> Optional[SelectorResult]:
        """Get the selected selector result."""
        return self._current_result

    # =========================================================================
    # Event Handlers
    # =========================================================================

    def _on_mode_changed(self, mode_id: int) -> None:
        """Handle mode button change."""
        mode_map = {0: "browser", 1: "desktop", 2: "image", 3: "ocr"}
        mode = mode_map.get(mode_id, "browser")
        self._current_mode = mode

        # Deactivate all tabs
        for tab in self._tabs.values():
            tab.set_active(False)

        # Activate selected tab
        if mode in self._tabs:
            self._tabs[mode].set_active(True)

        logger.debug(f"Mode changed to: {mode}")

    def _on_open_explorer(self) -> None:
        """Open the UI Explorer dialog for advanced element inspection."""
        from casare_rpa.presentation.canvas.selectors.ui_explorer import (
            UIExplorerDialog,
        )

        # Get current element fingerprint if available
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

        # Connect element selection back to this dialog
        dialog.selector_confirmed.connect(self._on_explorer_selector_confirmed)

        logger.info(f"Opening UI Explorer (mode={self._current_mode})")
        dialog.exec()

    def _on_explorer_selector_confirmed(self, selector: str) -> None:
        """Handle selector confirmed from UI Explorer."""
        if selector:
            self._strict_selector.set_selector(selector)
            self._strict_selector.set_enabled(True)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Selector imported from UI Explorer")
            self._status_label.setStyleSheet(
                "color: #10b981; font-size: 11px; font-weight: bold;"
            )
            logger.info(f"Imported selector from UI Explorer: {selector[:50]}...")

    def _load_selector_history(self) -> None:
        """Load recent selectors into history dropdown."""
        try:
            from casare_rpa.presentation.canvas.selectors.selector_history import (
                get_selector_history,
            )

            history = get_selector_history()
            recent = history.get_recent(limit=15)

            self._history_combo.blockSignals(True)
            self._history_combo.clear()
            self._history_combo.addItem("")  # Empty placeholder

            for entry in recent:
                selector = entry.selector
                element_tag = entry.element_tag or "element"
                selector_type = entry.selector_type

                # Truncate long selectors for display
                display_selector = (
                    selector[:50] + "..." if len(selector) > 50 else selector
                )
                display_text = f"{display_selector} ({element_tag}, {selector_type})"

                self._history_combo.addItem(display_text, selector)

            self._history_combo.blockSignals(False)
            logger.debug(f"Loaded {len(recent)} selectors into history dropdown")

        except Exception as e:
            logger.warning(f"Failed to load selector history: {e}")

    def _on_history_selected(self, index: int) -> None:
        """Apply selected history item to selector input."""
        if index <= 0:  # Skip empty placeholder
            return

        selector = self._history_combo.currentData()
        if selector:
            self._strict_selector.set_selector(selector)
            self._strict_selector.set_enabled(True)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Selector loaded from history")
            self._status_label.setStyleSheet(
                "color: #60a5fa; font-size: 11px; font-weight: bold;"
            )
            logger.info(f"Loaded selector from history: {selector[:50]}...")

    def _on_generate_wildcard(self) -> None:
        """Generate wildcard version of current selector."""
        import re

        current = self._strict_selector.get_selector()
        if not current:
            self._status_label.setText("No selector to convert to wildcard")
            self._status_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
            return

        wildcard = current
        original = current

        # Convert ID patterns with numbers: #user-123 -> #user-*
        # Matches: #prefix-123, #prefix_456, #prefix123
        wildcard = re.sub(r"#([a-zA-Z_-]+)[-_]?\d+", r"#\1-*", wildcard)

        # Convert dynamic class patterns: .btn-primary-42 -> .btn-*
        # Be careful not to break semantic class names
        wildcard = re.sub(r"\.([a-zA-Z]+)[-_]\d+", r".\1-*", wildcard)

        # Convert numbered index patterns: [1] -> [*] (be selective)
        wildcard = re.sub(r"\[(\d+)\]", r"[*]", wildcard)

        # Convert nth-child with numbers: nth-child(3) -> nth-child(*)
        wildcard = re.sub(r"nth-child\(\d+\)", "nth-child(*)", wildcard)

        # Convert data attributes with GUIDs/UUIDs: data-id="abc-123-def" -> data-id="*"
        wildcard = re.sub(
            r'(data-[a-zA-Z-]+)="[a-f0-9-]{8,}"',
            r'\1="*"',
            wildcard,
            flags=re.IGNORECASE,
        )

        # Convert session/token-like attributes
        wildcard = re.sub(
            r'(data-[a-zA-Z-]+)="[a-zA-Z0-9]{16,}"',
            r'\1="*"',
            wildcard,
        )

        if wildcard != original:
            self._strict_selector.set_selector(wildcard)
            self._confirm_btn.setEnabled(True)
            self._status_label.setText("Generated wildcard selector")
            self._status_label.setStyleSheet(
                "color: #f59e0b; font-size: 11px; font-weight: bold;"
            )
            logger.info(f"Generated wildcard: {original[:30]} -> {wildcard[:30]}")
        else:
            self._status_label.setText("Selector has no patterns to convert")
            self._status_label.setStyleSheet("color: #888; font-size: 11px;")

    def _start_picking(self, mode: str) -> None:
        """Start element picking for specified mode."""
        import asyncio

        # Check browser page for browser mode
        if mode == "browser" and not self._browser_page:
            self._status_label.setText("⚠ Run a Navigate node first to open browser")
            self._status_label.setStyleSheet(
                "color: #fbbf24; font-size: 11px; font-weight: bold;"
            )
            self._test_result.setText(
                "Browser element picking requires an active browser.\n"
                "Run a workflow with a Navigate node first, then try again."
            )
            self._test_result.setStyleSheet(
                "padding: 8px; background: #3d3520; color: #fbbf24; border-radius: 4px;"
            )
            logger.warning("Cannot start browser picking: no browser page available")
            return

        tab = self._tabs.get(mode)
        if not tab:
            logger.error(f"No tab found for mode: {mode}")
            return

        # Update status
        mode_names = {
            "browser": "Browser",
            "desktop": "Desktop",
            "ocr": "OCR",
            "image": "Image",
        }
        mode_name = mode_names.get(mode, mode)

        if mode == "browser":
            self._status_label.setText(
                f"🎯 {mode_name} picking active - Ctrl+Click element in browser"
            )
        else:
            self._status_label.setText(f"🎯 {mode_name} picking active...")
        self._status_label.setStyleSheet(
            "color: #10b981; font-size: 11px; font-weight: bold;"
        )

        # Use qasync-compatible async call
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(tab.start_picking())
            else:
                loop.run_until_complete(tab.start_picking())
        except Exception as e:
            logger.error(f"Failed to start picking: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet("color: #ef4444; font-size: 11px;")

    def _on_strategies_generated(self, strategies: List[SelectorStrategy]) -> None:
        """Handle strategies generated from a tab."""
        logger.info(
            f"Dialog._on_strategies_generated: Received {len(strategies)} strategies"
        )

        # Check if we're in anchor picking mode
        if self._picking_anchor:
            self._picking_anchor = False  # Reset flag
            self._reset_anchor_picking_ui()

            if not strategies:
                self._status_label.setText("⚠ No anchor element found")
                self._status_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
                return

            # Use the best strategy as anchor
            best = strategies[0]
            if hasattr(self, "_anchor_widget") and self._anchor_widget:
                self._anchor_widget.set_anchor(
                    selector=best.value,
                    tag="",  # SelectorStrategy doesn't have metadata
                    text=best.value[:30],  # Use truncated selector as display
                    stability=best.score / 100.0,
                )

            self._status_label.setText(f"✓ Anchor set: {best.value[:30]}...")
            self._status_label.setStyleSheet(
                "color: #10b981; font-size: 11px; font-weight: bold;"
            )
            logger.info(f"Anchor picked: {best.value[:50]}")
            return

        # Normal element picking flow
        self._strategies = strategies
        self._strategies_list.clear()

        if not strategies:
            self._strategies_info.setText("No selectors generated")
            self._confirm_btn.setEnabled(False)
            return

        # Auto-expand strategies section when selectors found
        if hasattr(self, "_strategies_section"):
            self._strategies_section.set_expanded(True)

        self._strategies_info.setText(
            f"{len(strategies)} selectors found, sorted by reliability"
        )

        # Update status
        self._status_label.setText(f"✓ {len(strategies)} selectors generated")
        self._status_label.setStyleSheet(
            "color: #10b981; font-size: 11px; font-weight: bold;"
        )

        for strategy in strategies:
            item = QListWidgetItem()

            # Score icon
            if strategy.score >= 80:
                score_icon = "\U0001f7e2"  # Green circle
            elif strategy.score >= 60:
                score_icon = "\U0001f7e1"  # Yellow circle
            else:
                score_icon = "\U0001f534"  # Red circle

            # Unique marker
            unique_mark = " \u2713" if strategy.is_unique else ""

            display = (
                f"{score_icon} {strategy.score:.0f} | "
                f"{strategy.selector_type.upper()} | "
                f"{strategy.value[:40]}{'...' if len(strategy.value) > 40 else ''}"
                f"{unique_mark}"
            )
            item.setText(display)
            item.setData(Qt.UserRole, strategy)

            self._strategies_list.addItem(item)

        # Select first
        if self._strategies_list.count() > 0:
            self._strategies_list.setCurrentRow(0)

        # Update selector rows with best selector
        if strategies:
            best = strategies[0]
            self._strict_selector.set_selector(best.value)

    def _on_strategy_changed(
        self, current: Optional[QListWidgetItem], _previous: Optional[QListWidgetItem]
    ) -> None:
        """Handle strategy selection change."""
        if not current:
            self._confirm_btn.setEnabled(False)
            return

        strategy: SelectorStrategy = current.data(Qt.UserRole)

        # Update strict selector display
        self._strict_selector.set_selector(strategy.value)
        self._confirm_btn.setEnabled(True)

        # Build current result
        current_tab = self._tabs.get(self._current_mode)
        if current_tab:
            result = current_tab.get_current_selector()
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

    def _on_status_changed(self, message: str) -> None:
        """Handle status message from tab."""
        self._status_label.setText(message)

    def _on_element_screenshot_captured(self, screenshot_bytes: bytes) -> None:
        """Handle element screenshot captured from browser tab."""
        logger.info(f"Element screenshot captured: {len(screenshot_bytes)} bytes")

        # Update image tab with captured template
        image_tab = self._tabs.get("image")
        if image_tab:
            image_tab.set_template_from_bytes(screenshot_bytes)

        # Update image preview in target section
        try:
            image = QImage.fromData(screenshot_bytes)
            pixmap = QPixmap.fromImage(image)
            scaled = pixmap.scaled(110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._image_preview_label.setPixmap(scaled)

            # Enable image selector
            self._image_selector.set_enabled(True)
            self._status_label.setText("Element image captured for template matching")
            self._status_label.setStyleSheet(
                "color: #ec4899; font-size: 11px; font-weight: bold;"
            )

        except Exception as e:
            logger.error(f"Failed to display element screenshot: {e}")

    def _on_validate(self) -> None:
        """Validate current selector."""
        import asyncio

        current_tab = self._tabs.get(self._current_mode)
        if not current_tab:
            return

        selector = self._strict_selector.get_selector()
        if not selector:
            self._test_result.setText("No selector to validate")
            self._test_result.setStyleSheet(
                "padding: 8px; background: #3d3520; color: #fbbf24; border-radius: 4px;"
            )
            return

        current_item = self._strategies_list.currentItem()
        if current_item:
            strategy: SelectorStrategy = current_item.data(Qt.UserRole)
            selector_type = strategy.selector_type
        else:
            selector_type = "xpath"

        asyncio.ensure_future(self._do_validate(current_tab, selector, selector_type))

    async def _do_validate(
        self, tab: BaseSelectorTab, selector: str, selector_type: str
    ) -> None:
        """Perform async validation."""
        result = await tab.test_selector(selector, selector_type)

        if result.get("success"):
            count = result.get("count", 0)
            time_ms = result.get("time_ms", 0)

            if count == 0:
                self._test_result.setText("No elements found")
                self._test_result.setStyleSheet(
                    "padding: 8px; background: #3d1e1e; color: #ef4444; border-radius: 4px;"
                )
            elif count == 1:
                self._test_result.setText(
                    f"\u2713 Found exactly 1 element ({time_ms:.1f}ms)"
                )
                self._test_result.setStyleSheet(
                    "padding: 8px; background: #1e3d2e; color: #10b981; border-radius: 4px;"
                )
            else:
                self._test_result.setText(
                    f"\u26a0 Found {count} elements - not unique ({time_ms:.1f}ms)"
                )
                self._test_result.setStyleSheet(
                    "padding: 8px; background: #3d3520; color: #fbbf24; border-radius: 4px;"
                )
        else:
            error = result.get("error", "Unknown error")
            self._test_result.setText(f"\u2717 Error: {error}")
            self._test_result.setStyleSheet(
                "padding: 8px; background: #3d1e1e; color: #ef4444; border-radius: 4px;"
            )

    def _on_confirm(self) -> None:
        """Confirm and use the selected selector."""
        if not self._current_result:
            # Build result from current state
            selector = self._strict_selector.get_selector()
            if not selector:
                return

            current_item = self._strategies_list.currentItem()
            if current_item:
                strategy: SelectorStrategy = current_item.data(Qt.UserRole)
                self._current_result = SelectorResult(
                    selector_value=selector,
                    selector_type=strategy.selector_type,
                    confidence=strategy.score / 100.0,
                    is_unique=strategy.is_unique,
                )
            else:
                self._current_result = SelectorResult(
                    selector_value=selector,
                    selector_type="xpath",
                    confidence=0.5,
                )

        # Include accuracy settings
        if self._fuzzy_selector.is_enabled():
            self._current_result.metadata["fuzzy_accuracy"] = (
                self._fuzzy_selector.get_accuracy()
            )
            self._current_result.metadata["fuzzy_innertext"] = (
                self._fuzzy_innertext_value.text()
            )
            self._current_result.metadata["fuzzy_match_type"] = (
                self._fuzzy_innertext_combo.currentText()
            )

        if self._cv_selector.is_enabled():
            self._current_result.metadata["cv_accuracy"] = (
                self._cv_selector.get_accuracy()
            )
            self._current_result.metadata["cv_element_type"] = (
                self._cv_element_type.currentText()
            )
            self._current_result.metadata["cv_text"] = self._cv_text.text()

        if self._image_selector.is_enabled():
            self._current_result.metadata["image_accuracy"] = (
                self._image_selector.get_accuracy()
            )

        # Auto-paste to target node if provided
        if self._target_node and self._target_property:
            try:
                widget = self._target_node.get_widget(self._target_property)
                if widget:
                    widget.set_value(self._current_result.selector_value)
                    logger.info(
                        f"Auto-pasted selector to {self._target_node.name()}.{self._target_property}"
                    )

                # Store healing_context in node config for runtime healing
                if self._current_result.healing_context:
                    healing_key = f"{self._target_property}_healing_context"
                    # Access casare_node directly to store healing context
                    casare_node = getattr(self._target_node, "_casare_node", None)
                    if casare_node and hasattr(casare_node, "config"):
                        casare_node.config[healing_key] = (
                            self._current_result.healing_context
                        )
                        logger.info(
                            f"Stored healing context ({len(self._current_result.healing_context)} keys) "
                            f"in {self._target_node.name()}.{healing_key}"
                        )
            except Exception as e:
                logger.error(f"Failed to auto-paste: {e}")

        # Emit signal
        self.selector_selected.emit(self._current_result)

        logger.info(
            f"Selector confirmed: {self._current_result.selector_value[:50]}..."
        )
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

                # Display in preview
                image = QImage.fromData(image_bytes)
                pixmap = QPixmap.fromImage(image)
                scaled = pixmap.scaled(
                    110, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._image_preview_label.setPixmap(scaled)

                # Pass to image tab
                image_tab = self._tabs.get("image")
                if image_tab:
                    image_tab._template_bytes = image_bytes
                    image_tab._display_template()
                    image_tab._update_find_button()

                self._status_label.setText(f"Image loaded: {path.name}")

            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                self._status_label.setText(f"Error: {e}")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handle key press events.

        Ctrl+LMB: Start element picking for current mode.
        Escape: Cancel/close dialog.
        """
        # Ctrl key held - prepare for Ctrl+Click picking
        if event.key() == Qt.Key_Control:
            self._ctrl_pressed = True
            self._status_label.setText("Ctrl held - click to pick element")
            self._status_label.setStyleSheet(
                "color: #60a5fa; font-size: 11px; font-weight: bold;"
            )

        # Escape to close
        elif event.key() == Qt.Key_Escape:
            self.reject()

        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle key release events."""
        if event.key() == Qt.Key_Control:
            self._ctrl_pressed = False
            self._status_label.setText("Ctrl+Click to pick")
            self._status_label.setStyleSheet("color: #888; font-size: 11px;")

        super().keyReleaseEvent(event)

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse press events.

        Ctrl+LMB triggers element picking for current mode.
        """
        from PySide6.QtCore import Qt as QtCore

        if event.button() == QtCore.LeftButton and getattr(
            self, "_ctrl_pressed", False
        ):
            # Ctrl+LMB - start picking for current mode
            self._start_picking(self._current_mode)
            event.accept()
            return

        super().mousePressEvent(event)

    def closeEvent(self, event) -> None:
        """Handle dialog close - stop any active picking."""
        import asyncio

        for tab in self._tabs.values():
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(tab.stop_picking())
            except Exception:
                pass

        super().closeEvent(event)

    # =========================================================================
    # Quick Text Search (itext= selector)
    # =========================================================================

    def _on_text_search_changed(self) -> None:
        """Handle text search input change - enable/disable generate button."""
        text = self._text_search_input.text().strip()
        self._text_search_btn.setEnabled(bool(text))

    def _on_generate_text_selector(self) -> None:
        """Generate itext= selector from text search input."""
        text = self._text_search_input.text().strip()
        if not text:
            return

        element = self._text_search_element.currentText()

        # Build itext= selector
        if element == "*":
            selector = f"itext={text}"
        else:
            selector = f"itext={element}:{text}"

        # Update strict selector with generated value
        self._strict_selector.set_selector(selector)
        self._strict_selector.set_enabled(True)

        # Enable confirm button
        self._confirm_btn.setEnabled(True)

        # Update status
        self._status_label.setText(f"✓ Generated text selector: {selector}")
        self._status_label.setStyleSheet(
            "color: #10b981; font-size: 11px; font-weight: bold;"
        )

        # Build result
        self._current_result = SelectorResult(
            selector_value=selector,
            selector_type="itext",
            confidence=0.7,  # Text selectors are medium confidence
            is_unique=False,  # Can't know without testing
            metadata={
                "search_text": text,
                "element_type": element,
            },
        )

        logger.info(f"Generated itext selector: {selector}")

    # =========================================================================
    # Anchor Management
    # =========================================================================

    def _on_pick_anchor(self) -> None:
        """Start anchor picking mode."""
        import asyncio

        # Check browser page for browser mode
        if self._current_mode == "browser" and not self._browser_page:
            self._status_label.setText("⚠ Run a Navigate node first to open browser")
            self._status_label.setStyleSheet(
                "color: #fbbf24; font-size: 11px; font-weight: bold;"
            )
            return

        self._picking_anchor = True  # Enter anchor picking mode
        self._status_label.setText("🎯 ANCHOR MODE: Ctrl+Click a reference element...")
        self._status_label.setStyleSheet(
            "color: #fbbf24; font-size: 11px; font-weight: bold;"
        )
        self._pick_anchor_btn.setText("Picking...")
        self._pick_anchor_btn.setEnabled(False)

        # Start anchor picking via browser tab
        tab = self._tabs.get("browser")
        if tab:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._do_pick_anchor(tab))
                else:
                    loop.run_until_complete(self._do_pick_anchor(tab))
            except Exception as e:
                logger.error(f"Failed to start anchor picking: {e}")
                self._reset_anchor_picking_ui()

    async def _do_pick_anchor(self, tab) -> None:
        """Perform async anchor picking."""
        try:
            # Use existing element picking but mark as anchor mode
            await tab.start_picking()

            # The tab will emit selectors_generated when an element is picked
            # We intercept this for anchor mode
        except Exception as e:
            logger.error(f"Anchor picking failed: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        finally:
            self._reset_anchor_picking_ui()

    def _reset_anchor_picking_ui(self) -> None:
        """Reset anchor picking button state."""
        self._pick_anchor_btn.setText("Pick Anchor")
        self._pick_anchor_btn.setEnabled(True)

    def _on_auto_detect_anchor(self) -> None:
        """Auto-detect the best anchor for the current target element."""
        import asyncio

        if self._current_mode == "browser" and not self._browser_page:
            self._status_label.setText("No browser open - cannot auto-detect anchor")
            self._status_label.setStyleSheet(
                "color: #fbbf24; font-size: 11px; font-weight: bold;"
            )
            return

        # Get current target selector
        target_selector = self._strict_selector.get_selector()
        if not target_selector:
            self._status_label.setText("Select a target element first")
            self._status_label.setStyleSheet(
                "color: #fbbf24; font-size: 11px; font-weight: bold;"
            )
            return

        self._status_label.setText("Auto-detecting anchor...")
        self._status_label.setStyleSheet(
            "color: #fbbf24; font-size: 11px; font-weight: bold;"
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
            self._status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
            self._auto_anchor_btn.setEnabled(True)

    async def _do_auto_detect_anchor(self, target_selector: str) -> None:
        """Perform async anchor auto-detection."""
        try:
            from casare_rpa.utils.selectors.anchor_locator import AnchorLocator

            locator = AnchorLocator()
            anchor_data = await locator.auto_detect_anchor(
                self._browser_page,
                target_selector,
            )

            if anchor_data:
                self._set_anchor(anchor_data)
                self._status_label.setText("Anchor auto-detected successfully")
                self._status_label.setStyleSheet(
                    "color: #10b981; font-size: 11px; font-weight: bold;"
                )
            else:
                self._status_label.setText("No suitable anchor found nearby")
                self._status_label.setStyleSheet(
                    "color: #fbbf24; font-size: 11px; font-weight: bold;"
                )
        except ImportError:
            logger.warning("AnchorLocator not available")
            self._status_label.setText("Anchor auto-detect not available")
            self._status_label.setStyleSheet("color: #fbbf24; font-size: 11px;")
        except Exception as e:
            logger.error(f"Anchor auto-detection failed: {e}")
            self._status_label.setText(f"Error: {e}")
            self._status_label.setStyleSheet("color: #ef4444; font-size: 11px;")
        finally:
            self._auto_anchor_btn.setEnabled(True)

    def _on_clear_anchor(self) -> None:
        """Clear the configured anchor."""
        self._anchor_data = None

        # Update UI state
        self._anchor_warning.show()
        self._anchor_success.hide()
        self._anchor_details.hide()
        self._clear_anchor_btn.setEnabled(False)

        # Update status
        self._status_label.setText("Anchor cleared")
        self._status_label.setStyleSheet("color: #888; font-size: 11px;")

        # Clear from current result if present
        if self._current_result and self._current_result.metadata:
            self._current_result.metadata.pop("anchor", None)

        logger.debug("Anchor cleared")

    def _on_anchor_position_changed(self, position: str) -> None:
        """Handle anchor position dropdown change."""
        if self._anchor_data:
            self._anchor_data["position"] = position.lower()
            logger.debug(f"Anchor position changed to: {position}")

    def _set_anchor(self, anchor_data: Dict[str, Any]) -> None:
        """
        Set the anchor data and update UI.

        Args:
            anchor_data: Dictionary with anchor info:
                - selector: CSS/XPath selector
                - tag_name: HTML tag
                - text_content: Visible text
                - position: Relative position (left/right/above/below)
                - stability_score: 0.0-1.0
        """
        self._anchor_data = anchor_data

        # Update UI state
        self._anchor_warning.hide()
        self._anchor_success.show()
        self._anchor_details.show()
        self._clear_anchor_btn.setEnabled(True)

        # Update anchor info
        tag = anchor_data.get("tag_name", "element")
        text = anchor_data.get("text_content", "")
        if text:
            display_text = text[:30] + "..." if len(text) > 30 else text
            self._anchor_info_label.setText(f"Anchor: <{tag}> {display_text}")
        else:
            selector = anchor_data.get("selector", "")
            short_sel = selector[:40] + "..." if len(selector) > 40 else selector
            self._anchor_info_label.setText(f"Anchor: {short_sel}")

        # Update position combo
        position = anchor_data.get("position", "left")
        position_text = position.capitalize()
        if position_text in ["Left", "Right", "Above", "Below", "Inside", "Near"]:
            self._anchor_position_combo.setCurrentText(position_text)

        # Update selector display
        selector = anchor_data.get("selector", "")
        self._anchor_selector_display.setPlainText(selector)

        # Expand anchor section to show the configured anchor
        self._anchor_section.set_expanded(True)

        # Include anchor in current result
        if self._current_result:
            self._current_result.metadata["anchor"] = anchor_data

        logger.info(f"Anchor set: {tag} - {text[:30] if text else selector[:30]}")

    def set_anchor_from_element(
        self, element_data: Dict[str, Any], position: str = "left"
    ) -> None:
        """
        Set anchor from picked element data.

        Args:
            element_data: Element fingerprint/data from picker
            position: Relative position to target
        """
        from casare_rpa.presentation.canvas.selectors.ui_explorer.models.anchor_model import (
            calculate_anchor_stability,
        )

        # Build anchor data from element
        tag = element_data.get("tag", element_data.get("tag_or_control", ""))
        attrs = element_data.get("attributes", {})
        text = element_data.get("text", element_data.get("text_content", ""))

        # Build selector from element
        selector = ""
        if attrs.get("id"):
            selector = f"#{attrs['id']}"
        elif attrs.get("data-testid"):
            selector = f"[data-testid=\"{attrs['data-testid']}\"]"
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

        # Calculate stability
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

    def get_anchor_data(self) -> Optional[Dict[str, Any]]:
        """Get the configured anchor data."""
        return self._anchor_data
