"""
UI Token System for CasareRPA Canvas.

This module defines all UI design tokens as frozen dataclasses, providing
a single source of truth for widget sizes, spacing, margins, border radii,
fonts, and transition durations.

Usage:
    from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

    # Access any token
    width = TOKENS.sizes.dialog_width_md
    margin = TOKENS.margins.panel_content
    spacing = TOKENS.spacing.md
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UISizes:
    """
    Standard widget sizes in pixels.

    All setFixedSize(), setMinimumSize(), resize() values
    should reference these constants.
    """

    # Button heights (width varies by content)
    button_height_sm: int = 24  # Compact toolbar buttons
    button_height_md: int = 28  # Standard buttons
    button_height_lg: int = 32  # Primary dialog actions
    button_min_width: int = 80  # Minimum button width
    button_width_sm: int = 80  # Small button width
    button_padding_h: int = 16  # Horizontal padding

    # Input field sizes
    input_height_xs: int = 20  # Extra compact inputs
    input_height_sm: int = 24  # Compact inputs
    input_height_md: int = 28  # Standard inputs
    input_height_lg: int = 36  # Large inputs
    input_min_width: int = 120  # Minimum input width
    input_max_width: int = 400  # Maximum input width

    # Icon sizes
    icon_xs: int = 12
    icon_sm: int = 16
    icon_md: int = 20
    icon_lg: int = 24
    icon_xl: int = 32
    icon_width: int = 16  # Standard icon width for alignment

    # Dialog sizes
    dialog_width_sm: int = 400
    dialog_width_md: int = 600
    dialog_width_lg: int = 800
    dialog_width_xl: int = 1000
    dialog_height_sm: int = 300
    dialog_height_md: int = 500
    dialog_height_lg: int = 700

    # Panel sizes (dock widgets)
    panel_width_min: int = 200
    panel_width_default: int = 300
    panel_width_max: int = 600
    panel_height_min: int = 150
    panel_height_default: int = 500
    panel_bottom_min: int = 120
    bottom_panel_width: int = 800
    bottom_panel_height: int = 250

    # Sidebar/Navigator sizes
    sidebar_width_min: int = 150
    sidebar_width_default: int = 250
    sidebar_width_max: int = 400

    # Node editor sizes
    node_width_min: int = 100
    node_width_default: int = 180
    node_port_spacing: int = 20
    node_header_height: int = 32

    # Status bar
    statusbar_height: int = 24

    # Toolbar
    toolbar_height: int = 40
    toolbar_icon_size: int = 24

    # Tab bar
    tab_min_width: int = 100
    tab_height: int = 36

    # Table/List row height
    row_height: int = 32
    row_height_compact: int = 24

    # Menus
    menu_item_height: int = 28
    menu_min_width: int = 200
    menu_width: int = 280
    menu_width_min: int = 200
    menu_width_max: int = 400

    # Separators and lines
    separator_height: int = 9
    line_height: int = 1

    # Collapsible section
    collapsible_header_height: int = 32

    # Shadows
    shadow_blur: int = 16
    shadow_offset: int = 4

    # Scrollbar
    scrollbar_width: int = 10
    scrollbar_min_handle: int = 40
    scrollbar_min_height: int = 20

    # Splitter handle
    splitter_handle: int = 4

    # Checkbox/Radio
    checkbox_size: int = 18
    radio_size: int = 18

    # Combo box
    combo_height: int = 28
    combo_dropdown_width: int = 24
    combo_width_sm: int = 90
    combo_width_md: int = 120
    combo_width_lg: int = 160
    date_picker_width: int = 160

    # Spinbox
    spinbox_height: int = 28
    spinbox_button_width: int = 20

    # Slider
    slider_height: int = 20
    slider_handle_size: int = 16

    # Progress bar
    progress_height: int = 18
    progress_bar_height: int = 4

    # Score bar (selector builder)
    score_bar_width: int = 60
    score_bar_height: int = 16

    # Attribute name label width
    attribute_name_width: int = 80

    # Preview sizes
    thumbnail_width: int = 110
    thumbnail_height: int = 70

    # Image preview size
    image_preview_width: int = 120
    image_preview_height: int = 80

    # Slider control width
    slider_control_width: int = 150

    # Border width
    border_width: int = 1

    # Tooltip
    tooltip_max_width: int = 300

    # Badge
    badge_width: int = 16
    badge_height: int = 16

    # Specialized widget sizes
    variable_button_width: int = 24
    variable_button_height: int = 20

    expression_editor_height: int = 120
    property_panel_width: int = 320

    # Window sizes
    window_min_width: int = 800
    window_min_height: int = 600
    window_default_width: int = 1200
    window_default_height: int = 800

    # Additional sizes for dialogs and widgets
    label_width_default: int = 80
    type_label_width: int = 120
    drag_handle_width: int = 20
    icon_button_size: int = 28
    spinner_width_sm: int = 90
    spinner_width_md: int = 100
    spinner_width_lg: int = 120
    spin_button_width: int = 100
    text_edit_height_sm: int = 60
    text_edit_height_md: int = 80
    text_edit_height_lg: int = 100
    text_edit_height_xl: int = 120
    dialog_lg: int = 50  # Additional height for dialog
    dialog_md_lg: int = 32  # Large margin
    dialog_md_md: int = 24  # Medium margin
    qr_code_size: int = 200
    verify_input_max_width: int = 250
    success_icon_size: int = 80
    success_icon_radius: int = 40

    # Table column widths
    column_width_xs: int = 60
    column_width_sm: int = 80
    column_width_md: int = 100
    column_width_lg: int = 120

    # Text block heights
    text_block_max_height: int = 80
    json_block_max_height: int = 120

    # Graph/Node editor specific sizes
    node_header_height_sm: int = 26  # Compact node header
    node_collapsed_width: int = 200
    node_collapsed_height: int = 50
    node_resize_handle_size: int = 12
    node_port_label_max_length: int = 12
    node_port_label_max_width: int = 80

    # Focus ring
    focus_ring_width: int = 3
    focus_ring_padding: int = 6
    focus_ring_blur_radius: int = 20
    focus_ring_blur_radius_high_contrast: int = 25

    # Wire/Connection drawing
    wire_thickness: int = 2
    wire_border_width: int = 1

    # Cache sizes (non-UI, but configuration)
    background_cache_max_size: int = 200

    # Icon drawing
    icon_margin: int = 2
    icon_border_width: float = 1.5
    icon_font_scale: float = 0.5  # Font size as ratio of icon size

    # Port/Frame drawing
    port_border_width: float = 1.5
    port_border_width_hollow: float = 2.0
    port_corner_radius_small: float = 3.0
    frame_selection_width: int = 3
    frame_drop_target_width: int = 3
    frame_pen_width: int = 2
    collapse_button_size: int = 18
    collapse_button_margin: int = 8
    collapse_symbol_size: int = 6
    exposed_port_size: int = 10
    exposed_port_border_width: float = 1.5
    exposed_port_margin: int = 12
    exposed_port_spacing: int = 14

    # Wire/Pipe drawing
    wire_exec_thickness: float = 3.0
    wire_data_active_thickness: float = 2.0
    wire_data_idle_thickness: float = 1.5
    wire_label_padding: int = 4
    wire_label_border_width: int = 1
    wire_label_corner_radius: int = 3
    wire_preview_padding: int = 6
    wire_preview_border_width: int = 1
    wire_preview_corner_radius: int = 4
    wire_preview_offset_x: int = 10
    wire_phantom_padding: int = 3
    wire_phantom_offset_y: int = 8
    wire_phantom_corner_radius: int = 3
    wire_phantom_bg_alpha: int = 140
    wire_phantom_text_alpha: int = 200
    wire_font_size_label: int = 8
    wire_font_size_preview: int = 9
    wire_font_size_phantom: int = 8
    wire_flow_dot_radius: float = 4.0
    wire_flow_dot_glow_radius: float = 8.0
    wire_animation_interval_ms: int = 16
    wire_animation_interval_slow_ms: int = 50
    wire_animation_cycle_ms: int = 500
    wire_completion_glow_ms: int = 300
    wire_max_tangent: float = 150.0
    wire_lo_thickness: float = 1.0
    wire_live_thickness: float = 2.5

    # Frame/Node frame drawing
    frame_default_width: float = 400.0
    frame_default_height: float = 300.0
    frame_padding: int = 30
    frame_padding_top_multiplier: int = 3
    frame_title_offset_x: int = 10
    frame_title_offset_y: int = 5
    frame_minimum_width: float = 100.0
    frame_minimum_height: float = 60.0

    # Node widget fonts
    node_widget_font_size: int = 8
    node_title_font_size: int = 9
    node_time_font_size: int = 8
    node_badge_font_size: int = 8
    default_font_size: int = 9


@dataclass(frozen=True)
class UISpacing:
    """
    Layout spacing values in pixels.

    All setSpacing(), layout spacing values
    should reference these constants.
    """

    # Spacing scale
    xs: int = 2  # Tight spacing
    sm: int = 4  # Compact spacing
    md: int = 8  # Default spacing
    lg: int = 12  # Relaxed spacing
    xl: int = 16  # Spacious spacing
    xxl: int = 24  # Extra spacious
    xxxl: int = 32  # Maximum spacing

    # Layout-specific spacing
    form_spacing: int = 12  # Form row spacing
    button_spacing: int = 8  # Button group spacing
    toolbar_spacing: int = 4  # Toolbar item spacing
    tab_spacing: int = 4  # Tab spacing
    menu_spacing: int = 0  # Menu item spacing
    table_spacing: int = 0  # Table cell spacing
    grid_spacing: int = 8  # Grid layout spacing
    splitter_spacing: int = 0  # Splitter spacing

    # Component internal spacing
    checkbox_label_spacing: int = 8
    radio_label_spacing: int = 8
    button_icon_text_spacing: int = 6
    menu_icon_text_spacing: int = 12
    table_header_spacing: int = 4
    panel_content_spacing: int = 12


@dataclass(frozen=True)
class UIMargins:
    """
    Margin presets in pixels.

    All setContentsMargins() values should use these presets.
    Returns tuple of (left, top, right, bottom).
    """

    # Preset margins
    none: tuple[int, int, int, int] = (0, 0, 0, 0)
    tight: tuple[int, int, int, int] = (4, 4, 4, 4)
    compact: tuple[int, int, int, int] = (8, 8, 8, 8)
    standard: tuple[int, int, int, int] = (12, 12, 12, 12)
    comfortable: tuple[int, int, int, int] = (16, 16, 16, 16)
    spacious: tuple[int, int, int, int] = (24, 24, 24, 24)

    # Component-specific margins
    panel_content: tuple[int, int, int, int] = (12, 12, 12, 12)
    panel_header: tuple[int, int, int, int] = (12, 8, 12, 8)
    toolbar: tuple[int, int, int, int] = (8, 4, 8, 4)
    dialog: tuple[int, int, int, int] = (16, 16, 16, 16)
    dialog_header: tuple[int, int, int, int] = (16, 12, 16, 8)
    dialog_footer: tuple[int, int, int, int] = (16, 12, 16, 12)
    form_row: tuple[int, int, int, int] = (0, 4, 0, 4)
    button_group: tuple[int, int, int, int] = (4, 4, 4, 4)
    menu_item: tuple[int, int, int, int] = (12, 6, 12, 6)
    menu_item_horizontal: tuple[int, int, int, int] = (12, 0, 12, 0)
    separator_vertical: tuple[int, int, int, int] = (0, 4, 0, 4)
    table_cell: tuple[int, int, int, int] = (8, 4, 8, 4)
    table_header: tuple[int, int, int, int] = (10, 8, 10, 8)
    tab_content: tuple[int, int, int, int] = (12, 12, 12, 12)
    dock_widget: tuple[int, int, int, int] = (0, 0, 0, 0)
    statusbar: tuple[int, int, int, int] = (8, 2, 8, 2)
    sidebar: tuple[int, int, int, int] = (0, 8, 0, 8)
    property_item: tuple[int, int, int, int] = (4, 6, 4, 6)

    # Asymmetric margins for specific layouts
    input_horizontal: tuple[int, int, int, int] = (10, 6, 10, 6)
    button_horizontal: tuple[int, int, int, int] = (12, 6, 12, 6)
    header_bottom: tuple[int, int, int, int] = (0, 0, 0, 8)
    footer_top: tuple[int, int, int, int] = (0, 8, 0, 0)

    # Additional margin presets for dialogs
    dialog_lg: int = 32
    dialog_md: int = 24


@dataclass(frozen=True)
class UIRadii:
    """
    Border radius values in pixels.

    All border-radius CSS values should use these constants.
    """

    none: int = 0  # No rounding
    sm: int = 4  # Small elements (buttons, inputs)
    md: int = 8  # Default radius (cards, panels)
    lg: int = 12  # Large radius (large cards)
    xl: int = 20  # Extra large radius
    two_xl: int = 28  # Dialog radius
    full: int = 999  # Pill shape (badges, tags)

    # Component-specific radii
    button: int = 4
    input: int = 4
    menu: int = 6
    menu_item: int = 4
    dialog: int = 8
    panel: int = 4
    tooltip: int = 4
    badge: int = 999
    tag: int = 4
    popover: int = 8
    scrollbar: int = 5


@dataclass(frozen=True)
class UIFonts:
    """
    Font sizes and families.
    """

    # Font families
    ui: str = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"

    # Font sizes (points)
    size_xs: int = 10  # Tiny labels, captions
    size_sm: int = 11  # Secondary text, metadata
    size_md: int = 12  # Default body text
    size_lg: int = 14  # Emphasized text, subheadings
    xl: int = 16  # Headings, titles
    xxl: int = 20  # Large headings
    xxxl: int = 24  # Display headings

    # Aliases for common use
    xs: int = 10
    sm: int = 11
    md: int = 12
    lg: int = 14

    # Component-specific sizes
    button: int = 12
    input: int = 12
    menu: int = 13
    table: int = 12
    table_header: int = 11
    statusbar: int = 11
    tooltip: int = 11
    dialog_title: int = 16
    dialog_message: int = 12
    node_title: int = 12
    node_port: int = 11
    code: int = 11
    log: int = 10


@dataclass(frozen=True)
class UITransition:
    """
    Animation durations in milliseconds.
    """

    instant: int = 50  # Button press, immediate feedback
    fast: int = 100  # Hover effects
    normal: int = 150  # Standard fade/slide
    medium: int = 200  # Panel transitions
    slow: int = 300  # Modal dialogs
    emphasis: int = 400  # Attention effects (shake, pulse)

    # Specific animations
    hover: int = 100
    focus: int = 150
    appear: int = 200
    disappear: int = 150
    slide: int = 200
    fade: int = 150


@dataclass(frozen=True)
class UITokens:
    """
    Unified UI tokens - single entry point for all theme values.

    Usage:
        from casare_rpa.presentation.canvas.theme_system.tokens import TOKENS

        # Access any token
        width = TOKENS.sizes.dialog_width_md
        margin = TOKENS.margins.panel_content
        spacing = TOKENS.spacing.md
    """

    sizes: UISizes = UISizes()
    spacing: UISpacing = UISpacing()
    margins: UIMargins = UIMargins()
    radii: UIRadii = UIRadii()
    fonts: UIFonts = UIFonts()
    transitions: UITransition = UITransition()


# Global singleton
TOKENS = UITokens()
