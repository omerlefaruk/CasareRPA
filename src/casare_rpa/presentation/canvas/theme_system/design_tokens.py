"""
Unified Design Token System for CasareRPA Canvas.

A minimal, semantic design system following 2025 best practices.
All tokens are frozen dataclasses - single source of truth for UI values.

Design Principles:
- 4px base spacing scale (industry standard)
- Semantic color naming (not visual names like "blue-500")
- Modular typography scale (1.25 ratio)
- Minimal token set (~30% of previous system)

Usage:
    from casare_rpa.presentation.canvas.theme_system import TOKENS

    # Spacing
    widget.setContentsMargins(TOKENS.spacing.md, TOKENS.spacing.lg,
                              TOKENS.spacing.md, TOKENS.spacing.lg)

    # Sizes
    widget.setFixedSize(TOKENS.sizes.button_md, TOKENS.sizes.button_md)

    # Colors
    color = THEME.primary

    # Border radius
    widget.setStyleSheet(f"border-radius: {TOKENS.radius.md}px")
"""

from __future__ import annotations

from dataclasses import dataclass

# =============================================================================
# SPACING SCALE (4px base)
# =============================================================================


@dataclass(frozen=True)
class Spacing:
    """
    4px-based spacing scale.

    All padding, margins, gaps, and spacing should use these values only.
    Scale follows powers of 2 for consistency and visual harmony.
    """

    zero: int = 0  # 0px   - No spacing
    xxs: int = 4  # 0.25rem - Tight spacing (icons, compact elements)
    xs: int = 8  # 0.5rem  - Compact spacing (related items)
    sm: int = 12  # 0.75rem - Small spacing (form rows)
    md: int = 16  # 1rem    - Default spacing (standard gaps)
    lg: int = 24  # 1.5rem  - Large spacing (section separation)
    xl: int = 32  # 2rem    - Extra large (page sections)
    xxl: int = 48  # 3rem    - Huge spacing (major sections)
    xxxl: int = 64  # 4rem    - Maximum spacing


@dataclass(frozen=True)
class Margin:
    """Common margin presets using Spacing values."""

    none: tuple[int, int, int, int] = (0, 0, 0, 0)
    tight: tuple[int, int, int, int] = (4, 4, 4, 4)  # Spacing.xxs
    compact: tuple[int, int, int, int] = (8, 8, 8, 8)  # Spacing.xs
    standard: tuple[int, int, int, int] = (12, 12, 12, 12)  # Spacing.sm
    comfortable: tuple[int, int, int, int] = (16, 16, 16, 16)  # Spacing.md
    spacious: tuple[int, int, int, int] = (24, 24, 24, 24)  # Spacing.lg

    # Component-specific margins
    dialog: tuple[int, int, int, int] = (24, 24, 24, 24)  # Spacing.lg
    panel: tuple[int, int, int, int] = (12, 12, 12, 12)  # Spacing.sm
    form_row: tuple[int, int, int, int] = (0, 8, 0, 8)  # Vertical spacing only


# =============================================================================
# BORDER RADIUS
# =============================================================================


@dataclass(frozen=True)
class Radius:
    """
    Border radius values.

    Limited to essential values for consistency.
    """

    none: int = 0  # Sharp edges (dividers, inputs with custom borders)
    sm: int = 4  # Small elements (tags, chips, compact buttons)
    md: int = 8  # Default (buttons, inputs, cards)
    lg: int = 12  # Large (panels, large cards)
    xl: int = 20  # Extra large (dialogs, modals)
    pill: int = 999  # Full pill shape (badges, pills)


# =============================================================================
# TYPOGRAPHY
# =============================================================================


@dataclass(frozen=True)
class Typography:
    """
    Font families, sizes, and line heights.

    Type scale uses a modular ratio (1.25) for visual harmony.
    """

    # Font families
    sans: str = "'Inter', 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif"
    mono: str = "'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace"

    # Type scale (modular, 1.25 ratio)
    display_xl: int = 24  # Page titles, hero text
    display_l: int = 20  # Large headings
    display_m: int = 18  # Section headings
    heading_xl: int = 16  # Primary headings
    heading_l: int = 14  # Secondary headings
    heading_m: int = 13  # Tertiary headings
    body_l: int = 14  # Emphasized body text
    body: int = 12  # Default body text
    body_s: int = 11  # Secondary text, metadata
    caption: int = 10  # Captions, tiny labels

    # Line heights (ratio-based for readability)
    lh_tight: float = 1.25  # Headings (tight leading)
    lh_normal: float = 1.5  # Body text (WCAG recommended)
    lh_relaxed: float = 1.75  # Long-form content

    # Font weights
    weight_normal: int = 400
    weight_medium: int = 500
    weight_semibold: int = 600
    weight_bold: int = 700


# =============================================================================
# COMPONENT SIZES
# =============================================================================


@dataclass(frozen=True)
class Sizes:
    """
    Standard component sizes.

    Heights are aligned across button/input variants for consistency.
    Widths are flexible based on content, with minimums defined.
    """

    # Button heights (align with input heights)
    button_sm: int = 24
    button_md: int = 32
    button_lg: int = 40
    button_min_width: int = 80

    # Input heights (align with button heights)
    input_sm: int = 24
    input_md: int = 32
    input_lg: int = 40
    input_min_width: int = 120
    input_max_width: int = 400

    # Dialog sizes
    dialog_sm_width: int = 400
    dialog_md_width: int = 600
    dialog_lg_width: int = 800
    dialog_min_height: int = 200

    # Icon sizes
    icon_sm: int = 16
    icon_md: int = 20
    icon_lg: int = 24

    # Panel/dock sizes
    panel_min_width: int = 200
    panel_default_width: int = 300
    panel_max_width: int = 500

    # Toolbar
    toolbar_height: int = 40

    # Status bar
    statusbar_height: int = 24

    # Tab bar
    tab_height: int = 36
    tab_min_width: int = 100

    # Menu
    menu_item_height: int = 32
    menu_min_width: int = 200

    # Table/list
    row_height: int = 32
    row_height_compact: int = 24

    # Scrollbar
    scrollbar_width: int = 10
    scrollbar_min_height: int = 20

    # Splitter
    splitter_handle: int = 4

    # Checkbox/radio
    checkbox_size: int = 18

    # Node editor (canvas-specific)
    node_width_min: int = 100
    node_header_height: int = 32
    node_port_spacing: int = 20


# =============================================================================
# SHADOWS
# =============================================================================


@dataclass(frozen=True)
class Shadows:
    """
    Box shadow values for elevation.

    Used primarily for dropdowns, popovers, and tooltips.
    Dark mode requires subtle shadows with higher opacity.
    """

    sm: str = "0 1px 2px rgba(0, 0, 0, 0.4)"  # Subtle (buttons, inputs)
    md: str = "0 4px 6px rgba(0, 0, 0, 0.5)"  # Medium (cards, panels)
    lg: str = "0 10px 15px rgba(0, 0, 0, 0.6)"  # Large (dialogs)
    xl: str = "0 20px 25px rgba(0, 0, 0, 0.7)"  # Extra large (modals)


# =============================================================================
# Z-INDEX SCALE
# =============================================================================


@dataclass(frozen=True)
class ZIndex:
    """
    Z-index stacking order.

    Ensures consistent layering across the application.
    """

    base: int = 0
    dropdown: int = 1000
    sticky: int = 1020
    fixed: int = 1030
    modal_backdrop: int = 1040
    modal: int = 1050
    popover: int = 1060
    tooltip: int = 1070


# =============================================================================
# TRANSITION DURATIONS
# =============================================================================


@dataclass(frozen=True)
class Transitions:
    """
    Animation durations in milliseconds.

    Fast, subtle animations for professional feel.
    """

    instant: int = 50  # Button press, immediate feedback
    fast: int = 100  # Hover effects
    normal: int = 150  # Standard fade/slide
    medium: int = 200  # Panel transitions
    slow: int = 300  # Modal dialogs


# =============================================================================
# UNIFIED TOKENS
# =============================================================================


@dataclass(frozen=True)
class DesignTokens:
    """
    Unified design tokens - single entry point.

    Usage:
        from casare_rpa.presentation.canvas.theme_system import TOKENS

        # Access tokens
        width = TOKENS.sizes.button_md
        margin = TOKENS.spacing.md
        radius = TOKENS.radius.md
    """

    spacing: Spacing = Spacing()
    margin: Margin = Margin()
    radius: Radius = Radius()
    typography: Typography = Typography()
    sizes: Sizes = Sizes()
    shadows: Shadows = Shadows()
    z_index: ZIndex = ZIndex()
    transitions: Transitions = Transitions()


# Global singleton
TOKENS = DesignTokens()
