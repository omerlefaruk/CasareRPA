"""
Primitive Gallery v2 - Epic 5.1 Component Library.

Visual verification dialog showcasing ALL primitive components.

Usage:
    from casare_rpa.presentation.canvas.theme_system.primitive_gallery import (
        show_primitive_gallery_v2,
        PrimitiveGallery,
    )

    # Show the gallery
    show_primitive_gallery_v2()

    # Or create programmatically
    gallery = PrimitiveGallery()
    gallery.show()

See: docs/UX_REDESIGN_PLAN.md Phase 5 Epic 5.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from casare_rpa.presentation.canvas.theme_system import THEME_V2, TOKENS_V2
from casare_rpa.presentation.canvas.theme_system.icons_v2 import get_icon
from casare_rpa.presentation.canvas.ui.widgets.primitives import (
    Avatar,
    # Feedback
    Badge,
    Breadcrumb,
    ButtonGroup,
    ButtonVariant,
    Card,
    # Selection
    CheckBox,
    ComboBox,
    Dial,
    Divider,
    DoubleSpinBox,
    EmptyState,
    InlineAlert,
    ItemList,
    # Lists
    ListItem,
    ProgressBar,
    # Buttons
    PushButton,
    RadioGroup,
    SearchInput,
    # Structural
    SectionHeader,
    # Selects
    Select,
    # Loading
    Skeleton,
    # Range
    Slider,
    SpinBox,
    Spinner,
    Switch,
    # Tabs
    Tab,
    TabWidget,
    # Inputs
    TextInput,
    ToolButton,
    TreeItem,
)

if TYPE_CHECKING:
    pass


# =============================================================================
# GALLERY DIALOG
# =============================================================================


class PrimitiveGallery(QDialog):
    """
    Visual verification dialog for ALL primitive components.

    Displays components organized by category with all variants and states.
    Includes export screenshot and copy QSS functionality.
    """

    # Width constants for consistent layout
    _COLUMN_WIDTH = 280
    _LABEL_WIDTH = 80
    _WIDGET_WIDTH = 180

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the primitive gallery dialog."""
        super().__init__(parent)

        self._setup_dialog()
        self._create_ui()
        self._apply_styles()

        logger.debug(f"{self.__class__.__name__} initialized")

    def _setup_dialog(self) -> None:
        """Configure dialog properties."""
        self.setWindowTitle("Primitive Gallery v2 - Component Library")
        self.resize(900, 700)
        self.setMinimumSize(800, 600)

        # Set dialog flags
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.WindowMaximizeButtonHint |
            Qt.WindowType.WindowCloseButtonHint
        )

    def _create_ui(self) -> None:
        """Create the gallery UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with title and actions
        header = self._create_header()
        layout.addWidget(header)

        # Tab widget for categories
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)
        self._tabs.setStyleSheet(self._get_tab_stylesheet())
        layout.addWidget(self._tabs)

        # Create category tabs
        self._create_buttons_tab()
        self._create_inputs_tab()
        self._create_selections_tab()
        self._create_selects_tab()
        self._create_range_tab()
        self._create_tabs_tab()
        self._create_lists_tab()
        self._create_structural_tab()
        self._create_feedback_tab()
        self._create_loading_tab()

    def _create_header(self) -> QWidget:
        """Create header with title and action buttons."""
        header = QWidget()
        header.setStyleSheet(f"""
            QWidget {{
                background: {THEME_V2.bg_header};
                border-bottom: 1px solid {THEME_V2.border};
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            TOKENS_V2.spacing.lg,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.lg,
            TOKENS_V2.spacing.md,
        )
        header_layout.setSpacing(TOKENS_V2.spacing.md)

        # Title
        title = QLabel("Primitive Gallery v2")
        title.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_header};
                font-size: {TOKENS_V2.typography.heading_lg}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
            }}
        """)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Screenshot button
        screenshot_btn = QPushButton("Export Screenshot")
        screenshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        screenshot_btn.clicked.connect(self._export_screenshot)
        self._style_button(screenshot_btn, "secondary")
        header_layout.addWidget(screenshot_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        self._style_button(close_btn, "primary")
        header_layout.addWidget(close_btn)

        return header

    def _create_scroll_area(self) -> QScrollArea:
        """Create a styled scroll area for content."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        scroll.setStyleSheet(self._get_scroll_stylesheet())
        return scroll

    def _create_section(self, title: str, parent: QWidget | None = None) -> tuple[QWidget, QVBoxLayout]:
        """Create a section container with title."""
        section = QWidget(parent)
        layout = QVBoxLayout(section)
        layout.setContentsMargins(
            TOKENS_V2.spacing.lg,
            TOKENS_V2.spacing.md,
            TOKENS_V2.spacing.lg,
            TOKENS_V2.spacing.lg,
        )
        layout.setSpacing(TOKENS_V2.spacing.md)

        # Section header
        header = QLabel(title)
        header.setStyleSheet(f"""
            QLabel {{
                color: {THEME_V2.text_header};
                font-size: {TOKENS_V2.typography.heading_md}px;
                font-weight: {TOKENS_V2.typography.weight_semibold};
                padding-bottom: {TOKENS_V2.spacing.xs}px;
            }}
        """)
        layout.addWidget(header)

        return section, layout

    def _create_row(self, label: str, widget: QWidget, parent: QWidget | None = None) -> QWidget:
        """Create a labeled row for a component."""
        row = QWidget(parent)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(TOKENS_V2.spacing.md)

        # Label
        lbl = QLabel(label)
        lbl.setFixedWidth(self._LABEL_WIDTH)
        lbl.setStyleSheet(f"color: {THEME_V2.text_secondary};")
        row_layout.addWidget(lbl)

        # Widget
        row_layout.addWidget(widget)

        row_layout.addStretch()

        return row

    # ==========================================================================
    # CATEGORY TABS
    # ==========================================================================

    def _create_buttons_tab(self) -> None:
        """Create buttons showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # PushButton variants
        section1, section1_layout = self._create_section("PushButton Variants")
        self._add_button_variants_section(section1_layout)
        layout.addWidget(section1)

        # PushButton sizes
        section2, section2_layout = self._create_section("PushButton Sizes")
        self._add_button_sizes_section(section2_layout)
        layout.addWidget(section2)

        # PushButton states
        section3, section3_layout = self._create_section("PushButton States")
        self._add_button_states_section(section3_layout)
        layout.addWidget(section3)

        # ToolButton
        section4, section4_layout = self._create_section("ToolButton")
        self._add_tool_button_section(section4_layout)
        layout.addWidget(section4)

        # ButtonGroup
        section5, section5_layout = self._create_section("ButtonGroup")
        self._add_button_group_section(section5_layout)
        layout.addWidget(section5)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Buttons")

    def _create_inputs_tab(self) -> None:
        """Create inputs showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # TextInput
        section1, section1_layout = self._create_section("TextInput")
        self._add_text_input_section(section1_layout)
        layout.addWidget(section1)

        # SearchInput
        section2, section2_layout = self._create_section("SearchInput")
        self._add_search_input_section(section2_layout)
        layout.addWidget(section2)

        # SpinBox
        section3, section3_layout = self._create_section("SpinBox")
        self._add_spin_box_section(section3_layout)
        layout.addWidget(section3)

        # DoubleSpinBox
        section4, section4_layout = self._create_section("DoubleSpinBox")
        self._add_double_spin_box_section(section4_layout)
        layout.addWidget(section4)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Inputs")

    def _create_selections_tab(self) -> None:
        """Create selection controls showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # CheckBox
        section1, section1_layout = self._create_section("CheckBox")
        self._add_checkbox_section(section1_layout)
        layout.addWidget(section1)

        # Switch
        section2, section2_layout = self._create_section("Switch")
        self._add_switch_section(section2_layout)
        layout.addWidget(section2)

        # RadioButton & RadioGroup
        section3, section3_layout = self._create_section("RadioButton / RadioGroup")
        self._add_radio_group_section(section3_layout)
        layout.addWidget(section3)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Selection")

    def _create_selects_tab(self) -> None:
        """Create selects showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # Select
        section1, section1_layout = self._create_section("Select")
        self._add_select_section(section1_layout)
        layout.addWidget(section1)

        # ComboBox
        section2, section2_layout = self._create_section("ComboBox")
        self._add_combobox_section(section2_layout)
        layout.addWidget(section2)

        # ItemList
        section3, section3_layout = self._create_section("ItemList")
        self._add_item_list_section(section3_layout)
        layout.addWidget(section3)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Selects")

    def _create_range_tab(self) -> None:
        """Create range inputs showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # Slider
        section1, section1_layout = self._create_section("Slider")
        self._add_slider_section(section1_layout)
        layout.addWidget(section1)

        # ProgressBar
        section2, section2_layout = self._create_section("ProgressBar")
        self._add_progress_bar_section(section2_layout)
        layout.addWidget(section2)

        # Dial
        section3, section3_layout = self._create_section("Dial")
        self._add_dial_section(section3_layout)
        layout.addWidget(section3)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Range")

    def _create_tabs_tab(self) -> None:
        """Create tabs showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # TabWidget
        section1, section1_layout = self._create_section("TabWidget")
        self._add_tab_widget_section(section1_layout)
        layout.addWidget(section1)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Tabs")

    def _create_lists_tab(self) -> None:
        """Create lists/trees showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # List items
        section1, section1_layout = self._create_section("ListItem")
        self._add_list_item_section(section1_layout)
        layout.addWidget(section1)

        # Tree items
        section2, section2_layout = self._create_section("TreeItem")
        self._add_tree_item_section(section2_layout)
        layout.addWidget(section2)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Lists")

    def _create_structural_tab(self) -> None:
        """Create structural components showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # SectionHeader
        section1, section1_layout = self._create_section("SectionHeader")
        self._add_section_header_section(section1_layout)
        layout.addWidget(section1)

        # Divider
        section2, section2_layout = self._create_section("Divider")
        self._add_divider_section(section2_layout)
        layout.addWidget(section2)

        # EmptyState
        section3, section3_layout = self._create_section("EmptyState")
        self._add_empty_state_section(section3_layout)
        layout.addWidget(section3)

        # Card
        section4, section4_layout = self._create_section("Card")
        self._add_card_section(section4_layout)
        layout.addWidget(section4)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Structural")

    def _create_feedback_tab(self) -> None:
        """Create feedback components showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # Badge
        section1, section1_layout = self._create_section("Badge")
        self._add_badge_section(section1_layout)
        layout.addWidget(section1)

        # InlineAlert
        section2, section2_layout = self._create_section("InlineAlert")
        self._add_alert_section(section2_layout)
        layout.addWidget(section2)

        # Breadcrumb
        section3, section3_layout = self._create_section("Breadcrumb")
        self._add_breadcrumb_section(section3_layout)
        layout.addWidget(section3)

        # Avatar
        section4, section4_layout = self._create_section("Avatar")
        self._add_avatar_section(section4_layout)
        layout.addWidget(section4)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Feedback")

    def _create_loading_tab(self) -> None:
        """Create loading states showcase tab."""
        scroll = self._create_scroll_area()
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(TOKENS_V2.spacing.xl)
        layout.setContentsMargins(TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md, TOKENS_V2.spacing.md)

        # Skeleton
        section1, section1_layout = self._create_section("Skeleton")
        self._add_skeleton_section(section1_layout)
        layout.addWidget(section1)

        # Spinner
        section2, section2_layout = self._create_section("Spinner")
        self._add_spinner_section(section2_layout)
        layout.addWidget(section2)

        layout.addStretch()
        scroll.setWidget(content)
        self._tabs.addTab(scroll, "Loading")

    # ==========================================================================
    # SECTION CONTENT HELPERS
    # ==========================================================================

    def _add_button_variants_section(self, layout: QVBoxLayout) -> None:
        """Add PushButton variants section."""
        grid = QGridLayout()
        grid.setSpacing(TOKENS_V2.spacing.md)
        grid.setContentsMargins(0, 0, 0, 0)

        variants: list[ButtonVariant] = ["primary", "secondary", "ghost", "danger"]

        for i, variant in enumerate(variants):
            btn = PushButton(text=variant.capitalize(), variant=variant, size="md")
            grid.addWidget(btn, 0, i)

        layout.addLayout(grid)

    def _add_button_sizes_section(self, layout: QVBoxLayout) -> None:
        """Add PushButton sizes section."""
        for size in ["sm", "md", "lg"]:
            row = self._create_row(size.upper(), PushButton(text=size.upper(), size=size, variant="primary"))
            layout.addWidget(row)

    def _add_button_states_section(self, layout: QVBoxLayout) -> None:
        """Add PushButton states section."""
        # Enabled/Disabled row
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(TOKENS_V2.spacing.md)

        row1_layout.addWidget(PushButton(text="Enabled", enabled=True))
        row1_layout.addWidget(PushButton(text="Disabled", enabled=False))
        row1_layout.addStretch()

        layout.addWidget(QLabel("Enabled / Disabled:"))
        layout.addWidget(row1)

    def _add_tool_button_section(self, layout: QVBoxLayout) -> None:
        """Add ToolButton section."""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.md)

        # Icon-only buttons
        for icon_name in ["home", "settings", "play", "pause", "stop", "refresh"]:
            btn = ToolButton(icon=get_icon(icon_name, size=20), tooltip=icon_name)
            container_layout.addWidget(btn)

        # Toggle button
        toggle = ToolButton(icon=get_icon("eye", size=20), tooltip="Toggle", checked=True)
        container_layout.addWidget(toggle)

        container_layout.addStretch()
        layout.addWidget(container)

    def _add_button_group_section(self, layout: QVBoxLayout) -> None:
        """Add ButtonGroup section."""
        # Horizontal group
        h_group = ButtonGroup(
            buttons=[("Small", "sm"), ("Medium", "md"), ("Large", "lg")],
            orientation="horizontal",
            size="sm",
        )
        layout.addWidget(QLabel("Horizontal ButtonGroup:"))
        layout.addWidget(h_group)

        # Vertical group
        v_group = ButtonGroup(
            buttons=[("Option A", "a"), ("Option B", "b"), ("Option C", "c")],
            orientation="vertical",
            size="sm",
        )
        layout.addWidget(QLabel("Vertical ButtonGroup:"))
        layout.addWidget(v_group)

    def _add_text_input_section(self, layout: QVBoxLayout) -> None:
        """Add TextInput section."""
        # Default input
        row1 = self._create_row("Default:", TextInput(placeholder="Enter text...", size="md"))
        layout.addWidget(row1)

        # With value
        row2 = self._create_row("With value:", TextInput(value="Sample text", size="md"))
        layout.addWidget(row2)

        # Clearable
        row3 = self._create_row("Clearable:", TextInput(placeholder="Type to see clear button", clearable=True))
        layout.addWidget(row3)

        # Password
        row4 = self._create_row("Password:", TextInput(placeholder="Enter password", password=True))
        layout.addWidget(row4)

        # Disabled
        row5 = self._create_row("Disabled:", TextInput(value="Cannot edit", readonly=True))
        layout.addWidget(row5)

        # Sizes
        row6 = QWidget()
        row6_layout = QHBoxLayout(row6)
        row6_layout.setContentsMargins(self._LABEL_WIDTH, 0, 0, 0)
        row6_layout.setSpacing(TOKENS_V2.spacing.md)
        row6_layout.addWidget(QLabel("Sizes:"))
        for size in ["sm", "md", "lg"]:
            row6_layout.addWidget(TextInput(placeholder=size, size=size))
        row6_layout.addStretch()
        layout.addWidget(row6)

    def _add_search_input_section(self, layout: QVBoxLayout) -> None:
        """Add SearchInput section."""
        row1 = self._create_row("Default:", SearchInput(placeholder="Search..."))
        layout.addWidget(row1)

        row2 = self._create_row("With value:", SearchInput(value="existing query", placeholder="Search..."))
        layout.addWidget(row2)

    def _add_spin_box_section(self, layout: QVBoxLayout) -> None:
        """Add SpinBox section."""
        row1 = self._create_row("Default:", SpinBox(min=0, max=100, value=50))
        layout.addWidget(row1)

        row2 = self._create_row("With suffix:", SpinBox(min=0, max=100, value=75, suffix=" px"))
        layout.addWidget(row2)

        row3 = self._create_row("Percentage:", SpinBox(min=0, max=100, value=50, suffix="%"))
        layout.addWidget(row3)

    def _add_double_spin_box_section(self, layout: QVBoxLayout) -> None:
        """Add DoubleSpinBox section."""
        row1 = self._create_row("Default:", DoubleSpinBox(min=0.0, max=1.0, value=0.5, decimals=2))
        layout.addWidget(row1)

        row2 = self._create_row("With prefix:", DoubleSpinBox(min=0.0, max=1000.0, value=99.99, prefix="$ ", decimals=2))
        layout.addWidget(row2)

        row3 = self._create_row("With suffix:", DoubleSpinBox(min=0.1, max=5.0, value=1.0, suffix="x", step=0.1))
        layout.addWidget(row3)

    def _add_checkbox_section(self, layout: QVBoxLayout) -> None:
        """Add CheckBox section."""
        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(TOKENS_V2.spacing.xl)

        row1_layout.addWidget(CheckBox(text="Unchecked", checked=False))
        row1_layout.addWidget(CheckBox(text="Checked", checked=True))
        row1_layout.addWidget(CheckBox(text="Disabled", enabled=False))
        row1_layout.addStretch()

        layout.addWidget(QLabel("States:"))
        layout.addWidget(row1)

        # Tristate
        tristate = CheckBox(text="Tristate (partial)", tristate=True)
        tristate.setCheckState(Qt.CheckState.PartiallyChecked)
        layout.addWidget(QLabel("Tristate:"))
        layout.addWidget(tristate)

    def _add_switch_section(self, layout: QVBoxLayout) -> None:
        """Add Switch section."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.md)

        row1 = QWidget()
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(0, 0, 0, 0)
        row1_layout.setSpacing(TOKENS_V2.spacing.xl)

        row1_layout.addWidget(Switch(text="Off", checked=False))
        row1_layout.addWidget(Switch(text="On", checked=True))
        row1_layout.addWidget(Switch(text="Disabled", enabled=False))
        row1_layout.addStretch()

        container_layout.addWidget(QLabel("States:"))
        container_layout.addWidget(row1)

        # With on/off text
        row2 = QWidget()
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(0, 0, 0, 0)
        row2_layout.setSpacing(TOKENS_V2.spacing.md)

        row2_layout.addWidget(Switch(on_text="Yes", off_text="No", checked=True))
        row2_layout.addWidget(Switch(on_text="Enabled", off_text="Disabled", checked=False))
        row2_layout.addStretch()

        container_layout.addWidget(QLabel("With on/off text:"))
        container_layout.addWidget(row2)

        layout.addWidget(container)

    def _add_radio_group_section(self, layout: QVBoxLayout) -> None:
        """Add RadioButton / RadioGroup section."""
        # Horizontal group
        h_group = RadioGroup(
            items=[
                {"value": "opt1", "label": "Option 1"},
                {"value": "opt2", "label": "Option 2"},
                {"value": "opt3", "label": "Option 3"},
            ],
            selected="opt1",
            orientation="horizontal",
        )
        layout.addWidget(QLabel("Horizontal RadioGroup:"))
        layout.addWidget(h_group)

        # Vertical group
        v_group = RadioGroup(
            items=[
                {"value": "a", "label": "Choice A"},
                {"value": "b", "label": "Choice B"},
            ],
            orientation="vertical",
        )
        layout.addWidget(QLabel("Vertical RadioGroup:"))
        layout.addWidget(v_group)

    def _add_select_section(self, layout: QVBoxLayout) -> None:
        """Add Select section."""
        items = [
            {"value": "1", "label": "Option 1"},
            {"value": "2", "label": "Option 2"},
            {"value": "3", "label": "Option 3"},
        ]

        row1 = self._create_row("Default:", Select(items=items, placeholder="Choose..."))
        layout.addWidget(row1)

        row2 = self._create_row("With value:", Select(items=items, value="1"))
        layout.addWidget(row2)

        row3 = self._create_row("Clearable:", Select(items=items, placeholder="Select...", clearable=True, value="2"))
        layout.addWidget(row3)

        # With icons
        icon_items = [
            {"value": "pending", "label": "Pending", "icon": "clock"},
            {"value": "active", "label": "Active", "icon": "play"},
            {"value": "done", "label": "Done", "icon": "check"},
        ]
        row4 = self._create_row("With icons:", Select(items=icon_items, value="pending"))
        layout.addWidget(row4)

    def _add_combobox_section(self, layout: QVBoxLayout) -> None:
        """Add ComboBox section."""
        items = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]

        row1 = self._create_row("Default:", ComboBox(items=items, placeholder="Select or type..."))
        layout.addWidget(row1)

        row2 = self._create_row("With value:", ComboBox(items=items, value="Cherry"))
        layout.addWidget(row2)

    def _add_item_list_section(self, layout: QVBoxLayout) -> None:
        """Add ItemList section."""
        items = [
            {"value": "1", "label": "First item", "icon": "file"},
            {"value": "2", "label": "Second item", "icon": "folder"},
            {"value": "3", "label": "Third item", "icon": "settings"},
            {"value": "4", "label": "Fourth item", "icon": "search"},
        ]

        list_widget = ItemList(items=items, selected="1", icons_enabled=True)
        list_widget.setFixedHeight(150)
        layout.addWidget(QLabel("ItemList with icons:"))
        layout.addWidget(list_widget)

    def _add_slider_section(self, layout: QVBoxLayout) -> None:
        """Add Slider section."""
        # Sizes
        for size in ["sm", "md", "lg"]:
            row = self._create_row(f"{size.upper()}:", Slider(min=0, max=100, value=50, show_value=True, size=size))
            layout.addWidget(row)

        # Without value label
        row = self._create_row("No value:", Slider(min=0, max=100, value=75, show_value=False))
        layout.addWidget(row)

    def _add_progress_bar_section(self, layout: QVBoxLayout) -> None:
        """Add ProgressBar section."""
        # Different values
        for value, label in [(25, "25%"), (50, "50%"), (75, "75%"), (100, "100%")]:
            row = self._create_row(label, ProgressBar(value=value, show_text=True))
            layout.addWidget(row)

        # Without text
        row = self._create_row("No text:", ProgressBar(value=60, show_text=False))
        layout.addWidget(row)

        # Sizes
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(self._LABEL_WIDTH, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.sm)
        container_layout.addWidget(QLabel("Sizes:"))
        for size in ["sm", "md", "lg"]:
            container_layout.addWidget(ProgressBar(value=50, show_text=True, size=size))
        layout.addWidget(container)

        # Indeterminate
        row = self._create_row("Loading:", ProgressBar(indeterminate=True, show_text=False))
        layout.addWidget(row)

    def _add_dial_section(self, layout: QVBoxLayout) -> None:
        """Add Dial section."""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.xl)

        for value in [0, 90, 180, 270]:
            dial = Dial(min=0, max=360, value=value, size=80)
            container_layout.addWidget(dial)

        container_layout.addStretch()

        layout.addWidget(QLabel("Dial (0, 90, 180, 270 degrees):"))
        layout.addWidget(container)

        # Wrapping dial
        row = self._create_row("Wrapping:", Dial(min=0, max=360, value=180, wrapping=True, size=80))
        layout.addWidget(row)

    def _add_tab_widget_section(self, layout: QVBoxLayout) -> None:
        """Add TabWidget section."""
        from PySide6.QtWidgets import QLabel

        tabs = [
            Tab(id="home", title="Home", content=QLabel("Home content area")),
            Tab(id="settings", title="Settings", icon=get_icon("settings", size=16), content=QLabel("Settings content")),
            Tab(id="about", title="About", content=QLabel("About content")),
        ]

        tab_widget = TabWidget(tabs=tabs, position="top")
        tab_widget.setFixedHeight(150)
        layout.addWidget(QLabel("Top position:"))
        layout.addWidget(tab_widget)

    def _add_list_item_section(self, layout: QVBoxLayout) -> None:
        """Add ListItem section."""
        from PySide6.QtWidgets import QListWidget

        list_widget = QListWidget()
        list_widget.setFixedHeight(120)

        items = [
            ListItem(text="Item 1", value="1", icon="file"),
            ListItem(text="Item 2", value="2", icon="folder"),
            ListItem(text="Item 3 (disabled)", value="3", enabled=False),
            ListItem(text="Item 4", value="4", icon="settings"),
        ]

        for item in items:
            list_widget.addItem(item)

        layout.addWidget(QLabel("Styled ListWidget:"))
        layout.addWidget(list_widget)

    def _add_tree_item_section(self, layout: QVBoxLayout) -> None:
        """Add TreeItem section."""
        from PySide6.QtWidgets import QTreeWidget

        tree = QTreeWidget()
        tree.setFixedHeight(150)
        tree.setHeaderHidden(True)

        # Parent item with children
        parent = TreeItem(text="Folder", value="folder", icon="folder")
        parent.add_child(TreeItem(text="File 1.txt", value="file1", icon="file"))
        parent.add_child(TreeItem(text="File 2.txt", value="file2", icon="file"))
        parent.set_expanded(True)

        # Another parent
        parent2 = TreeItem(text="Another Folder", value="folder2", icon="folder")
        parent2.add_child(TreeItem(text="Nested", value="nested", icon="folder"))
        parent2.add_child(TreeItem(text="Item", value="item", icon="file"))

        tree.addTopLevelItem(parent)
        tree.addTopLevelItem(parent2)

        layout.addWidget(QLabel("Styled TreeWidget:"))
        layout.addWidget(tree)

    def _add_section_header_section(self, layout: QVBoxLayout) -> None:
        """Add SectionHeader section."""
        # Default header
        header1 = SectionHeader(text="Section Title")
        layout.addWidget(QLabel("Default:"))
        layout.addWidget(header1)

        # Collapsible header
        header2 = SectionHeader(text="Collapsible Section", collapsible=True)
        layout.addWidget(QLabel("Collapsible:"))
        layout.addWidget(header2)

        # Collapsed header
        header3 = SectionHeader(text="Collapsed Section", collapsible=True, collapsed=True)
        layout.addWidget(QLabel("Collapsed:"))
        layout.addWidget(header3)

    def _add_divider_section(self, layout: QVBoxLayout) -> None:
        """Add Divider section."""
        # Horizontal divider
        layout.addWidget(QLabel("Horizontal:"))
        h_div = Divider(orientation="horizontal")
        h_div.apply_stylesheet()
        layout.addWidget(h_div)

        # Vertical divider
        container = QWidget()
        container.setFixedHeight(50)
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)

        container_layout.addWidget(QLabel("Left"))
        v_div = Divider(orientation="vertical")
        v_div.apply_stylesheet()
        container_layout.addWidget(v_div)
        container_layout.addWidget(QLabel("Right"))
        container_layout.addStretch()

        layout.addWidget(QLabel("Vertical:"))
        layout.addWidget(container)

    def _add_empty_state_section(self, layout: QVBoxLayout) -> None:
        """Add EmptyState section."""
        empty = EmptyState(
            icon="inbox",
            text="No items found",
            action_text="Create new",
        )
        empty.setFixedHeight(120)
        layout.addWidget(empty)

    def _add_card_section(self, layout: QVBoxLayout) -> None:
        """Add Card section."""
        from PySide6.QtWidgets import QLabel

        content = QLabel("Card content goes here.\nThis is the main content area\nof the card widget.")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = Card(title="Card Title", content_widget=content, border=True)
        card.setFixedHeight(120)
        layout.addWidget(card)

    def _add_badge_section(self, layout: QVBoxLayout) -> None:
        """Add Badge section."""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.xl)

        # Dot badges
        for color in ["primary", "success", "warning", "error"]:
            badge = Badge(variant="dot", color=color)
            container_layout.addWidget(badge)

        container_layout.addWidget(QLabel("|"))
        container_layout.addWidget(QLabel("Dot badges"))

        container_layout.addStretch()
        layout.addWidget(container)

        # Count badges
        container2 = QWidget()
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 0)
        container2_layout.setSpacing(TOKENS_V2.spacing.md)

        for text in ["1", "5", "99"]:
            badge = Badge(variant="count", text=text, color="error")
            container2_layout.addWidget(badge)

        container2_layout.addWidget(QLabel("Count badges"))
        container2_layout.addStretch()

        layout.addWidget(container2)

        # Label badges
        container3 = QWidget()
        container3_layout = QHBoxLayout(container3)
        container3_layout.setContentsMargins(0, 0, 0, 0)
        container3_layout.setSpacing(TOKENS_V2.spacing.md)

        for label, color in [("NEW", "primary"), ("BETA", "warning"), ("PRO", "success")]:
            badge = Badge(variant="label", text=label, color=color)
            container3_layout.addWidget(badge)

        container3_layout.addWidget(QLabel("Label badges"))
        container3_layout.addStretch()

        layout.addWidget(container3)

    def _add_alert_section(self, layout: QVBoxLayout) -> None:
        """Add InlineAlert section."""
        variants = ["info", "warning", "error", "success"]

        for variant in variants:
            alert = InlineAlert(
                text=f"This is a {variant} message",
                variant=variant,
                dismissible=True,
            )
            layout.addWidget(alert)

    def _add_breadcrumb_section(self, layout: QVBoxLayout) -> None:
        """Add Breadcrumb section."""
        items = [
            {"label": "Home", "data": "home"},
            {"label": "Library", "data": "library"},
            {"label": "Components", "data": "components"},
            {"label": "Primitives", "data": "primitives"},
        ]

        breadcrumb = Breadcrumb(items=items, separator="/")
        layout.addWidget(breadcrumb)

    def _add_avatar_section(self, layout: QVBoxLayout) -> None:
        """Add Avatar section."""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.md)

        # Initials avatars
        for text, size in [("AB", "sm"), ("JD", "md"), ("XY", "lg")]:
            avatar = Avatar(text=text, size=size)
            container_layout.addWidget(avatar)

        container_layout.addWidget(QLabel("Initials"))

        container_layout.addStretch()
        layout.addWidget(container)

        # Colored variants (via custom styling)
        container2 = QWidget()
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 0)
        container2_layout.setSpacing(TOKENS_V2.spacing.md)

        # Custom background avatars
        for color_name, color_hex in [("primary", THEME_V2.primary), ("success", THEME_V2.success)]:
            avatar = Avatar(text="U", size="md")
            avatar.setStyleSheet(f"Avatar {{ background: {color_hex}; }}")
            container2_layout.addWidget(avatar)

        container2_layout.addWidget(QLabel("Colored"))
        container2_layout.addStretch()

        layout.addWidget(container2)

    def _add_skeleton_section(self, layout: QVBoxLayout) -> None:
        """Add Skeleton section."""
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.md)

        # Text skeleton
        text_skel = Skeleton(variant="text", width=300, height=40)
        container_layout.addWidget(QLabel("Text variant:"))
        container_layout.addWidget(text_skel)

        # Rect skeleton
        rect_container = QWidget()
        rect_layout = QHBoxLayout(rect_container)
        rect_layout.setContentsMargins(0, 0, 0, 0)
        rect_layout.setSpacing(TOKENS_V2.spacing.md)
        for w, h in [(100, 60), (150, 80), (200, 100)]:
            rect_layout.addWidget(Skeleton(variant="rect", width=w, height=h))
        rect_layout.addStretch()
        container_layout.addWidget(QLabel("Rect variants:"))
        container_layout.addWidget(rect_container)

        # Circle skeleton
        circle_container = QWidget()
        circle_layout = QHBoxLayout(circle_container)
        circle_layout.setContentsMargins(0, 0, 0, 0)
        circle_layout.setSpacing(TOKENS_V2.spacing.md)
        for size in [24, 32, 40]:
            circle_layout.addWidget(Skeleton(variant="circle", width=size, height=size))
        circle_layout.addStretch()
        container_layout.addWidget(QLabel("Circle variants:"))
        container_layout.addWidget(circle_container)

        layout.addWidget(container)

    def _add_spinner_section(self, layout: QVBoxLayout) -> None:
        """Add Spinner section."""
        container = QWidget()
        container_layout = QHBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(TOKENS_V2.spacing.xl)

        # Different sizes
        for size in [16, 20, 24, 32]:
            container_layout.addWidget(Spinner(size=size))

        container_layout.addStretch()

        layout.addWidget(QLabel("Spinners (16, 20, 24, 32px):"))
        layout.addWidget(container)

        # Different colors
        container2 = QWidget()
        container2_layout = QHBoxLayout(container2)
        container2_layout.setContentsMargins(0, 0, 0, 0)
        container2_layout.setSpacing(TOKENS_V2.spacing.xl)

        for color_name, color in [("primary", THEME_V2.primary), ("success", THEME_V2.success), ("error", THEME_V2.error)]:
            container2_layout.addWidget(Spinner(size=24, color=color))
            container2_layout.addWidget(QLabel(color_name))

        container2_layout.addStretch()

        layout.addWidget(QLabel("Colored spinners:"))
        layout.addWidget(container2)

    # ==========================================================================
    # STYLESHEETS
    # ==========================================================================

    def _get_tab_stylesheet(self) -> str:
        """Get stylesheet for tab widget."""
        t = THEME_V2
        return f"""
            QTabWidget {{
                background: {t.bg_surface};
                border: none;
            }}
            QTabWidget::pane {{
                background: {t.bg_surface};
                border: none;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {t.text_secondary};
                border: none;
                border-bottom: 2px solid transparent;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                margin-right: {TOKENS_V2.spacing.xs}px;
                font-size: {TOKENS_V2.typography.body}px;
                font-weight: {TOKENS_V2.typography.weight_medium};
            }}
            QTabBar::tab:selected {{
                color: {t.text_primary};
                border-bottom-color: {t.primary};
            }}
            QTabBar::tab:hover:!selected {{
                color: {t.text_primary};
                background: {t.bg_hover};
            }}
        """

    def _get_scroll_stylesheet(self) -> str:
        """Get stylesheet for scroll area."""
        t = THEME_V2
        return f"""
            QScrollArea {{
                background: {t.bg_surface};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {t.scrollbar_bg};
                width: {TOKENS_V2.sizes.scrollbar_width}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {t.scrollbar_handle};
                border-radius: {TOKENS_V2.radius.xs}px;
                min-height: {TOKENS_V2.sizes.scrollbar_min_height}px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {t.scrollbar_hover};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar:horizontal {{
                background: {t.scrollbar_bg};
                height: {TOKENS_V2.sizes.scrollbar_width}px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: {t.scrollbar_handle};
                border-radius: {TOKENS_V2.radius.xs}px;
                min-width: {TOKENS_V2.sizes.scrollbar_min_height}px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: {t.scrollbar_hover};
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
        """

    def _style_button(self, btn: QPushButton, variant: ButtonVariant) -> None:
        """Apply quick styling to a button."""
        t = THEME_V2
        radius = TOKENS_V2.radius.sm

        match variant:
            case "primary":
                bg = t.primary
                bg_hover = t.primary_hover
                text = t.text_on_primary
            case "secondary":
                bg = t.bg_component
                bg_hover = t.bg_hover
                text = t.text_primary
            case "ghost":
                bg = "transparent"
                bg_hover = t.bg_hover
                text = t.text_primary
            case "danger":
                bg = t.error
                bg_hover = "#f87171"
                text = t.text_on_error
            case _:
                bg = t.primary
                bg_hover = t.primary_hover
                text = t.text_on_primary

        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {text};
                border: 1px solid {bg};
                border-radius: {radius}px;
                padding: {TOKENS_V2.spacing.xs}px {TOKENS_V2.spacing.md}px;
                font-size: {TOKENS_V2.typography.body}px;
            }}
            QPushButton:hover {{
                background: {bg_hover};
                border-color: {bg_hover};
            }}
        """)

    def _apply_styles(self) -> None:
        """Apply overall dialog styling."""
        t = THEME_V2
        self.setStyleSheet(f"""
            PrimitiveGallery {{
                background: {t.bg_surface};
            }}
            QLabel {{
                color: {t.text_primary};
                font-size: {TOKENS_V2.typography.body}px;
                background: transparent;
            }}
        """)

    # ==========================================================================
    # ACTIONS
    # ==========================================================================

    @Slot()
    def _export_screenshot(self) -> None:
        """
        Export gallery content as screenshot image.

        Saves the current tab view to a PNG file.
        """
        # Grab the current tab widget
        current_widget = self._tabs.currentWidget()

        # Create pixmap of the tab content
        pixmap = QPixmap(current_widget.size())
        current_widget.render(pixmap)

        # Convert to image
        image = QPixmap.toImage(pixmap)

        # Get save path
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Screenshot",
            f"primitive_gallery_{self._tabs.tabText(self._tabs.currentIndex()).lower()}.png",
            "PNG Images (*.png);;All Files (*.*)",
        )

        if file_path:
            if image.save(file_path):
                logger.info(f"Screenshot saved to: {file_path}")
                QMessageBox.information(
                    self,
                    "Export Complete",
                    f"Screenshot saved to:\n{file_path}"
                )
            else:
                logger.error(f"Failed to save screenshot to: {file_path}")
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to save screenshot to:\n{file_path}"
                )


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def show_primitive_gallery_v2(parent: QWidget | None = None) -> PrimitiveGallery:
    """
    Show the primitive gallery dialog.

    Args:
        parent: Optional parent widget

    Returns:
        The PrimitiveGallery instance

    Example:
        from casare_rpa.presentation.canvas.theme_system.primitive_gallery import (
            show_primitive_gallery_v2,
        )

        gallery = show_primitive_gallery_v2()
    """
    gallery = PrimitiveGallery(parent)
    gallery.show()
    return gallery


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "PrimitiveGallery",
    "show_primitive_gallery_v2",
]
