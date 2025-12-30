"""
Style Gallery v2 - Visual testing for Epic 1.3 QSS v2.

This module creates a dialog that showcases all UI primitives styled
with the v2 design system. Used for manual verification of Epic 1.3.

Usage:
    from casare_rpa.presentation.canvas.theme_system.style_gallery import show_style_gallery_v2
    show_style_gallery_v2(parent)

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.3
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .icons_v2 import icon_v2
from .styles_v2 import get_canvas_stylesheet_v2
from .tokens_v2 import THEME_V2, TOKENS_V2


def _create_buttons_section(parent: QWidget) -> QGroupBox:
    """Create button variants section."""
    group = QGroupBox("Buttons", parent)
    layout = QGridLayout(group)

    # Standard button
    btn_std = QPushButton("Standard", group)
    layout.addWidget(btn_std, 0, 0)

    # Primary button (using property selector)
    btn_primary = QPushButton("Primary", group)
    btn_primary.setProperty("primary", True)
    layout.addWidget(btn_primary, 0, 1)

    # Danger button
    btn_danger = QPushButton("Danger", group)
    btn_danger.setProperty("danger", True)
    layout.addWidget(btn_danger, 0, 2)

    # Disabled button
    btn_disabled = QPushButton("Disabled", group)
    btn_disabled.setEnabled(False)
    layout.addWidget(btn_disabled, 1, 0)

    # Small buttons (using v2 sizing)
    btn_small = QPushButton("Small", group)
    btn_small.setFixedHeight(TOKENS_V2.sizes.button_sm)
    layout.addWidget(btn_small, 1, 1)

    # Large button
    btn_large = QPushButton("Large", group)
    btn_large.setFixedHeight(TOKENS_V2.sizes.button_lg)
    layout.addWidget(btn_large, 1, 2)

    return group


def _create_inputs_section(parent: QWidget) -> QGroupBox:
    """Create input fields section."""
    group = QGroupBox("Inputs", parent)
    layout = QFormLayout(group)

    # Text input
    text_input = QLineEdit(group)
    text_input.setPlaceholderText("Enter text...")
    layout.addRow("Text:", text_input)

    # Password input
    password_input = QLineEdit(group)
    password_input.setPlaceholderText("Password...")
    password_input.setEchoMode(QLineEdit.EchoMode.Password)
    layout.addRow("Password:", password_input)

    # Disabled input
    disabled_input = QLineEdit(group)
    disabled_input.setText("Disabled value")
    disabled_input.setEnabled(False)
    layout.addRow("Disabled:", disabled_input)

    # Spinbox
    spinbox = QSpinBox(group)
    spinbox.setRange(0, 100)
    spinbox.setValue(42)
    layout.addRow("Spinbox:", spinbox)

    # Double spinbox
    double_spin = QDoubleSpinBox(group)
    double_spin.setRange(0.0, 1.0)
    double_spin.setSingleStep(0.01)
    double_spin.setValue(0.5)
    layout.addRow("Double:", double_spin)

    # Combobox
    combo = QComboBox(group)
    combo.addItems(["Option 1", "Option 2", "Option 3"])
    layout.addRow("Dropdown:", combo)

    # Slider
    slider = QSlider(Qt.Orientation.Horizontal, group)
    slider.setRange(0, 100)
    slider.setValue(60)
    layout.addRow("Slider:", slider)

    return group


def _create_selection_section(parent: QWidget) -> QGroupBox:
    """Create checkbox/radio selection section."""
    group = QGroupBox("Selection", parent)
    layout = QVBoxLayout(group)

    # Checkboxes
    layout.addWidget(QLabel("Checkboxes:"))
    cb1 = QCheckBox("Unchecked checkbox", group)
    layout.addWidget(cb1)

    cb2 = QCheckBox("Checked checkbox", group)
    cb2.setChecked(True)
    layout.addWidget(cb2)

    cb3 = QCheckBox("Disabled checkbox", group)
    cb3.setEnabled(False)
    layout.addWidget(cb3)

    # Radio buttons
    layout.addWidget(QLabel("Radio buttons:"))
    rb1 = QRadioButton("Option A", group)
    rb1.setChecked(True)
    layout.addWidget(rb1)

    rb2 = QRadioButton("Option B", group)
    layout.addWidget(rb2)

    rb3 = QRadioButton("Disabled option", group)
    rb3.setEnabled(False)
    layout.addWidget(rb3)

    return group


def _create_lists_section(parent: QWidget) -> QGroupBox:
    """Create list/table/tree views section."""
    group = QGroupBox("Lists & Tables", parent)
    layout = QGridLayout(group)

    # Table widget
    table = QTableWidget(group)
    table.setColumnCount(3)
    table.setRowCount(3)
    table.setHorizontalHeaderLabels(["Name", "Type", "Status"])
    for row in range(3):
        table.setItem(row, 0, QTableWidgetItem(f"Item {row + 1}"))
        table.setItem(row, 1, QTableWidgetItem("Node"))
        table.setItem(row, 2, QTableWidgetItem("Ready"))
    header = table.horizontalHeader()
    header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
    layout.addWidget(table, 0, 0)

    # List widget
    list_widget = QListWidget(group)
    list_widget.addItems(["Item 1", "Item 2", "Item 3 (selected)"])
    list_widget.setCurrentRow(2)
    layout.addWidget(list_widget, 0, 1)

    # Tree widget
    tree = QTreeWidget(group)
    tree.setHeaderLabels(["Project", "Type"])
    root = QTreeWidgetItem(tree, ["My Project", "Folder"])
    QTreeWidgetItem(root, ["Workflow 1", "Workflow"])
    QTreeWidgetItem(root, ["Workflow 2", "Workflow"])
    root.setExpanded(True)
    layout.addWidget(tree, 1, 0, 1, 2)

    return group


def _create_tabs_section(parent: QWidget) -> QGroupBox:
    """Create tab widget section."""
    group = QGroupBox("Tabs", parent)
    layout = QVBoxLayout(group)

    tabs = QTabWidget(group)
    tabs.addTab(QLabel("Content of Tab 1\n\nTab 1 shows basic content."), "Tab 1")
    tabs.addTab(QLabel("Content of Tab 2\n\nTab 2 has more content."), "Tab 2")
    tabs.addTab(QLabel("Content of Tab 3\n\nTab 3 is here too."), "Tab 3")

    layout.addWidget(tabs)
    return group


def _create_text_section(parent: QWidget) -> QGroupBox:
    """Create text editor section."""
    group = QGroupBox("Text Editor", parent)
    layout = QVBoxLayout(group)

    text_edit = QTextEdit(group)
    text_edit.setPlainText(
        "# This is a text editor\n\n"
        "Styled with v2 tokens:\n"
        "- Dark background\n"
        "- Monospace font\n"
        "- No animations\n"
        "- Cursor blue selection"
    )
    layout.addWidget(text_edit)

    return group


def _create_progress_section(parent: QWidget) -> QGroupBox:
    """Create progress indicator section."""
    group = QGroupBox("Progress", parent)
    layout = QFormLayout(group)

    # Progress bar
    progress = QProgressBar(group)
    progress.setValue(65)
    layout.addRow("Progress:", progress)

    # Indeterminate
    progress_indet = QProgressBar(group)
    progress_indet.setRange(0, 0)  # Indeterminate
    layout.addRow("Indeterminate:", progress_indet)

    return group


def _create_icons_section(parent: QWidget) -> QGroupBox:
    """Create icon gallery section for Epic 2.1 verification."""
    group = QGroupBox("Icons (Epic 2.1)", parent)
    layout = QVBoxLayout(group)

    # Icon set to display (subset of available icons)
    icons_to_show = [
        # File operations
        ("file", "File"), ("folder", "Folder"), ("save", "Save"),
        ("download", "Download"), ("upload", "Upload"), ("trash", "Trash"),
        # Edit operations
        ("edit", "Edit"), ("copy", "Copy"), ("paste", "Paste"),
        ("undo", "Undo"), ("redo", "Redo"),
        # Actions
        ("play", "Play"), ("pause", "Pause"), ("stop", "Stop"),
        ("plus", "Plus"), ("minus", "Minus"), ("check", "Check"),
        ("search", "Search"), ("refresh", "Refresh"),
        # Navigation
        ("chevron-up", "Up"), ("chevron-down", "Down"),
        ("chevron-left", "Left"), ("chevron-right", "Right"),
        ("zoom-in", "Zoom+"), ("zoom-out", "Zoom-"),
        # Chrome
        ("settings", "Settings"), ("menu", "Menu"),
        ("close", "Close"), ("more-horizontal", "More"),
        # Panels
        ("panel-left", "Panel L"), ("panel-right", "Panel R"),
        ("panel-bottom", "Panel Btm"),
        # Git
        ("branch", "Branch"), ("commit", "Commit"), ("merge", "Merge"),
    ]

    # Sizes to display
    sizes: list[int] = [16, 20, 24]

    # Create grid for each size
    for size in sizes:
        size_label = QLabel(f"Size {size}px:", group)
        size_label.setStyleSheet(f"font-weight: {TOKENS_V2.typography.weight_medium};")
        layout.addWidget(size_label)

        size_layout = QGridLayout()
        size_layout.setSpacing(TOKENS_V2.spacing.md)

        row = 0
        col = 0
        max_cols = 10

        for icon_name, label in icons_to_show:
            icon_container = QWidget(group)
            icon_layout = QVBoxLayout(icon_container)
            icon_layout.setContentsMargins(0, 0, 0, 0)
            icon_layout.setSpacing(TOKENS_V2.spacing.xs)

            # Icon label
            icon_label = QLabel(icon_container)
            icon = icon_v2.get_icon(icon_name, size=size, state="normal")
            icon_label.setPixmap(icon.pixmap(size, size))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(icon_label)

            # Name label
            name_label = QLabel(label, group)
            name_label.setStyleSheet(f"font-size: {TOKENS_V2.typography.caption}px; color: {THEME_V2.text_secondary};")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.addWidget(name_label)

            size_layout.addWidget(icon_container, row, col)

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        layout.addLayout(size_layout)

    # State variants section
    state_label = QLabel("State Variants (play icon):", group)
    state_label.setStyleSheet(f"font-weight: {TOKENS_V2.typography.weight_medium}; margin-top: {TOKENS_V2.spacing.md}px;")
    layout.addWidget(state_label)

    state_layout = QHBoxLayout()
    for state in ["normal", "disabled", "accent"]:
        state_container = QWidget(group)
        state_inner = QVBoxLayout(state_container)
        state_inner.setContentsMargins(0, 0, 0, 0)

        state_icon_label = QLabel(state_container)
        state_icon = icon_v2.get_icon("play", size=24, state=state)  # type: ignore
        state_icon_label.setPixmap(state_icon.pixmap(24, 24))
        state_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_inner.addWidget(state_icon_label)

        state_name = QLabel(state.capitalize(), group)
        state_name.setStyleSheet(f"font-size: {TOKENS_V2.typography.caption}px; color: {THEME_V2.text_secondary};")
        state_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        state_inner.addWidget(state_name)

        state_layout.addWidget(state_container)

    layout.addLayout(state_layout)

    # Icon count info
    available_count = len(icon_v2.get_available_icons())
    count_label = QLabel(f"Available icons: {available_count}", group)
    count_label.setStyleSheet(f"color: {THEME_V2.text_muted}; font-size: {TOKENS_V2.typography.caption}px;")
    layout.addWidget(count_label)

    return group


def show_style_gallery_v2(parent=None) -> QDialog:
    """
    Show a gallery of all v2 styled widgets for Epic 1.3 verification.

    This dialog displays all Qt primitives with v2 styling applied.
    Use this to manually verify Epic 1.3: "Global QSS v2 generated from tokens".

    Args:
        parent: Parent widget (typically main window)

    Returns:
        The gallery dialog instance
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle("Style Gallery v2 - Epic 1.3 + 2.1")
    dialog.resize(900, 800)

    # Apply v2 stylesheet globally
    dialog.setStyleSheet(get_canvas_stylesheet_v2())

    # Main layout
    main_layout = QVBoxLayout(dialog)

    # Scrollable content area
    scroll = QScrollArea(dialog)
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    # Content container
    content = QWidget()
    content_layout = QVBoxLayout(content)
    content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    content_layout.setSpacing(TOKENS_V2.spacing.lg)
    content_layout.setContentsMargins(
        TOKENS_V2.spacing.xl, TOKENS_V2.spacing.xl,
        TOKENS_V2.spacing.xl, TOKENS_V2.spacing.xl
    )

    # Title
    title = QLabel("CasareRPA v2 Design System - Style Gallery", content)
    title.setStyleSheet(
        f"font-size: {TOKENS_V2.typography.display_lg}px; "
        f"font-weight: {TOKENS_V2.typography.weight_semibold};"
    )
    content_layout.addWidget(title)

    subtitle = QLabel(
        "Epic 1.3: Global QSS v2 generated from tokens "
        "(no per-widget setStyleSheet required)",
        content
    )
    subtitle.setStyleSheet(f"color: {THEME_V2.text_secondary};")
    content_layout.addWidget(subtitle)

    # Add all sections
    content_layout.addWidget(_create_buttons_section(content))
    content_layout.addWidget(_create_inputs_section(content))
    content_layout.addWidget(_create_selection_section(content))
    content_layout.addWidget(_create_lists_section(content))
    content_layout.addWidget(_create_tabs_section(content))
    content_layout.addWidget(_create_text_section(content))
    content_layout.addWidget(_create_progress_section(content))
    content_layout.addWidget(_create_icons_section(content))

    # Token info
    token_info = QGroupBox("Token Info (v2)", content)
    token_layout = QVBoxLayout(token_info)
    token_text = QLabel(
        f"Colors: {THEME_V2.primary} (primary), {THEME_V2.bg_surface} (surface)\n"
        f"Font: {TOKENS_V2.typography.sans}\n"
        f"Spacing: {TOKENS_V2.spacing.md}px grid\n"
        f"Radius: {TOKENS_V2.radius.sm}px (buttons), {TOKENS_V2.radius.md}px (panels)\n"
        f"Motion: {TOKENS_V2.motion.instant}ms (no animations)"
    )
    token_layout.addWidget(token_text)
    content_layout.addWidget(token_info)

    content_layout.addStretch()

    # Close button
    close_btn = QPushButton("Close Gallery", content)
    close_btn.setProperty("primary", True)
    close_btn.clicked.connect(dialog.accept)
    content_layout.addWidget(close_btn)

    scroll.setWidget(content)
    main_layout.addWidget(scroll)

    dialog.show()
    return dialog
