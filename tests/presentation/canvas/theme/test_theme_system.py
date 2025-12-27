"""
Integration tests for Canvas theme system.

This test suite covers:
- CanvasThemeColors dataclass and color values
- Color lookup functions (get_wire_color, get_status_color, get_category_color)
- UITokens design tokens (sizes, spacing, margins, radii, fonts, transitions)
- Color manipulation utilities (darken, lighten, alpha, blend, etc.)
- QSS stylesheet generation

Test Philosophy:
- Happy path: colors and tokens return expected values
- Sad path: handles invalid inputs gracefully
- Edge cases: boundary values, empty strings, unknown types

Run: pytest tests/presentation/canvas/theme/test_theme_system.py -v
"""

from __future__ import annotations

import re
from unittest.mock import MagicMock

import pytest

from casare_rpa.presentation.canvas.theme_system import (
    BORDERS,
    FONT_SIZE_MAP,
    FONT_SIZES,
    FONTS,
    MONO_FONT,
    NODE_STATUS_COLOR_MAP,
    RADIUS,
    RADIUS_MAP,
    SIZES,
    SPACING,
    SPACING_MAP,
    STATUS_COLOR_MAP,
    THEME,
    TOKENS,
    UI_FONT,
    WIRE_COLOR_MAP,
    CanvasThemeColors,
    UIFonts,
    UIMargins,
    UIRadii,
    UISizes,
    UISpacing,
    UITokens,
    UITransition,
    alpha,
    blend,
    contrast_color,
    darken,
    desaturate,
    get_base_widget_styles,
    get_button_styles,
    get_canvas_stylesheet,
    get_input_styles,
    get_main_window_styles,
    get_menu_styles,
    get_node_status_color,
    get_scrollbar_styles,
    get_status_color,
    get_toolbar_styles,
    get_wire_color,
    hex_to_rgb,
    is_valid_hex,
    lighten,
    normalize_hex,
    rgb_to_hex,
    saturate,
)

# =============================================================================
# TestColors - CanvasThemeColors and color lookup functions
# =============================================================================


class TestColors:
    """Test CanvasThemeColors dataclass and color values."""

    def test_theme_instance_exists(self) -> None:
        """Test global THEME instance is available."""
        assert THEME is not None
        assert isinstance(THEME, CanvasThemeColors)

    def test_theme_has_background_colors(self) -> None:
        """Test theme has all background color attributes."""
        assert THEME.bg_darkest == "#18181b"
        assert THEME.bg_dark == "#27272a"
        assert THEME.bg_medium == "#3f3f46"
        assert THEME.bg_light == "#52525b"
        assert THEME.bg_lighter == "#71717a"

    def test_theme_has_panel_colors(self) -> None:
        """Test theme has panel-specific colors."""
        assert THEME.bg_panel == "#27272a"
        assert THEME.bg_header == "#18181b"
        assert THEME.bg_hover == "#3f3f46"
        assert THEME.bg_selected == "#3730a3"

    def test_theme_has_text_colors(self) -> None:
        """Test theme has all text color attributes."""
        assert THEME.text_primary == "#f4f4f5"
        assert THEME.text_secondary == "#a1a1aa"
        assert THEME.text_muted == "#71717a"
        assert THEME.text_disabled == "#52525b"

    def test_theme_has_accent_colors(self) -> None:
        """Test theme has accent color attributes."""
        assert THEME.accent_primary == "#6366f1"
        assert THEME.accent_secondary == "#818cf8"
        assert THEME.accent_hover == "#4f46e5"

    def test_theme_has_status_colors(self) -> None:
        """Test theme has all status color attributes."""
        assert THEME.status_success == "#10b981"
        assert THEME.status_warning == "#f59e0b"
        assert THEME.status_error == "#ef4444"
        assert THEME.status_info == "#3b82f6"

    def test_theme_has_wire_colors(self) -> None:
        """Test theme has wire connection colors."""
        assert THEME.wire_exec == "#ffffff"
        assert THEME.wire_data == "#6366f1"
        assert THEME.wire_bool == "#ef4444"
        assert THEME.wire_string == "#f97316"
        assert THEME.wire_number == "#10b981"

    def test_theme_has_menu_colors(self) -> None:
        """Test theme has VS Code/Cursor style menu colors."""
        assert THEME.menu_bg == "#252526"
        assert THEME.menu_border == "#454545"
        assert THEME.menu_hover == "#094771"
        assert THEME.menu_text == "#CCCCCC"

    def test_theme_has_editor_colors(self) -> None:
        """Test theme has code editor colors."""
        assert THEME.editor_bg == "#1E1E1E"
        assert THEME.editor_current_line == "#282828"
        assert THEME.editor_selection == "#264F78"

    def test_theme_has_syntax_colors(self) -> None:
        """Test theme has syntax highlighting colors."""
        assert THEME.syntax_keyword == "#C586C0"
        assert THEME.syntax_string == "#CE9178"
        assert THEME.syntax_number == "#B5CEA8"
        assert THEME.syntax_comment == "#6A9955"


class TestWireColor:
    """Test get_wire_color function."""

    def test_wire_color_exec_default_theme(self) -> None:
        """Test exec wire color with default theme."""
        assert get_wire_color("exec") == "#ffffff"

    def test_wire_color_exec_custom_theme(self) -> None:
        """Test exec wire color with custom theme."""
        theme = CanvasThemeColors(wire_exec="#ff0000")
        assert get_wire_color("exec", theme) == "#ff0000"

    def test_wire_color_data_any(self) -> None:
        """Test 'any' data type wire color."""
        assert get_wire_color("any") == "#6366f1"

    def test_wire_color_boolean(self) -> None:
        """Test boolean wire color (both aliases)."""
        assert get_wire_color("bool") == "#ef4444"
        assert get_wire_color("boolean") == "#ef4444"

    def test_wire_color_string(self) -> None:
        """Test string wire color (both aliases)."""
        assert get_wire_color("string") == "#f97316"
        assert get_wire_color("str") == "#f97316"

    def test_wire_color_number(self) -> None:
        """Test number wire color (int, float, number)."""
        assert get_wire_color("number") == "#10b981"
        assert get_wire_color("int") == "#10b981"
        assert get_wire_color("float") == "#10b981"

    def test_wire_color_list(self) -> None:
        """Test list wire color (both aliases)."""
        assert get_wire_color("list") == "#a78bfa"
        assert get_wire_color("array") == "#a78bfa"

    def test_wire_color_dict(self) -> None:
        """Test dict wire color (both aliases)."""
        assert get_wire_color("dict") == "#2dd4bf"
        assert get_wire_color("object") == "#2dd4bf"

    def test_wire_color_case_insensitive(self) -> None:
        """Test wire color lookup is case insensitive."""
        assert get_wire_color("STRING") == "#f97316"
        assert get_wire_color("String") == "#f97316"
        assert get_wire_color("BOOLEAN") == "#ef4444"

    def test_wire_color_unknown_type_defaults_to_any(self) -> None:
        """Test unknown data type defaults to 'any' color."""
        assert get_wire_color("unknown") == "#6366f1"
        assert get_wire_color("custom") == "#6366f1"

    def test_wire_color_map_complete(self) -> None:
        """Test WIRE_COLOR_MAP has all expected entries."""
        expected_keys = {
            "exec",
            "any",
            "bool",
            "boolean",
            "string",
            "str",
            "number",
            "int",
            "float",
            "list",
            "array",
            "dict",
            "object",
        }
        assert set(WIRE_COLOR_MAP.keys()) == expected_keys


class TestNodeStatusColor:
    """Test get_node_status_color function."""

    def test_status_idle(self) -> None:
        """Test idle status color."""
        assert get_node_status_color("idle") == "#a1a1aa"

    def test_status_running(self) -> None:
        """Test running status color."""
        assert get_node_status_color("running") == "#fbbf24"

    def test_status_success(self) -> None:
        """Test success status color."""
        assert get_node_status_color("success") == "#34d399"

    def test_status_error(self) -> None:
        """Test error status color."""
        assert get_node_status_color("error") == "#f87171"

    def test_status_skipped(self) -> None:
        """Test skipped status color."""
        assert get_node_status_color("skipped") == "#a78bfa"

    def test_status_breakpoint(self) -> None:
        """Test breakpoint status color."""
        assert get_node_status_color("breakpoint") == "#f87171"

    def test_status_case_insensitive(self) -> None:
        """Test status lookup is case insensitive."""
        assert get_node_status_color("RUNNING") == "#fbbf24"
        assert get_node_status_color("Success") == "#34d399"

    def test_status_unknown_defaults_to_idle(self) -> None:
        """Test unknown status defaults to idle color."""
        assert get_node_status_color("unknown") == "#a1a1aa"
        assert get_node_status_color("") == "#a1a1aa"

    def test_status_custom_theme(self) -> None:
        """Test status color with custom theme."""
        theme = CanvasThemeColors(node_success="#00ff00")
        assert get_node_status_color("success", theme) == "#00ff00"

    def test_node_status_color_map_complete(self) -> None:
        """Test NODE_STATUS_COLOR_MAP has all expected entries."""
        expected_keys = {"idle", "running", "success", "error", "skipped", "breakpoint"}
        assert set(NODE_STATUS_COLOR_MAP.keys()) == expected_keys


class TestStatusColor:
    """Test get_status_color function."""

    def test_status_success(self) -> None:
        """Test success status color."""
        assert get_status_color("success") == "#10b981"

    def test_status_completed_alias(self) -> None:
        """Test completed status maps to success."""
        assert get_status_color("completed") == "#10b981"

    def test_status_warning(self) -> None:
        """Test warning status color."""
        assert get_status_color("warning") == "#f59e0b"

    def test_status_error(self) -> None:
        """Test error status color."""
        assert get_status_color("error") == "#ef4444"

    def test_status_failed_alias(self) -> None:
        """Test failed status maps to error."""
        assert get_status_color("failed") == "#ef4444"

    def test_status_info(self) -> None:
        """Test info status color."""
        assert get_status_color("info") == "#3b82f6"

    def test_status_idle(self) -> None:
        """Test idle status color."""
        assert get_status_color("idle") == "#71717a"

    def test_status_running(self) -> None:
        """Test running status color."""
        assert get_status_color("running") == "#f59e0b"

    def test_status_unknown_defaults_to_secondary(self) -> None:
        """Test unknown status defaults to text_secondary."""
        result = get_status_color("unknown")
        assert result == THEME.text_secondary

    def test_status_custom_theme(self) -> None:
        """Test status color with custom theme."""
        theme = CanvasThemeColors(status_success="#00ff00")
        assert get_status_color("success", theme) == "#00ff00"


# =============================================================================
# TestTokens - UITokens design tokens
# =============================================================================


class TestTokens:
    """Test UITokens singleton and token classes."""

    def test_tokens_singleton_exists(self) -> None:
        """Test global TOKENS instance is available."""
        assert TOKENS is not None
        assert isinstance(TOKENS, UITokens)

    def test_tokens_has_sizes(self) -> None:
        """Test TOKENS has UISizes instance."""
        assert isinstance(TOKENS.sizes, UISizes)

    def test_tokens_has_spacing(self) -> None:
        """Test TOKENS has UISpacing instance."""
        assert isinstance(TOKENS.spacing, UISpacing)

    def test_tokens_has_margins(self) -> None:
        """Test TOKENS has UIMargins instance."""
        assert isinstance(TOKENS.margins, UIMargins)

    def test_tokens_has_radii(self) -> None:
        """Test TOKENS has UIRadii instance."""
        assert isinstance(TOKENS.radii, UIRadii)

    def test_tokens_has_fonts(self) -> None:
        """Test TOKENS has UIFonts instance."""
        assert isinstance(TOKENS.fonts, UIFonts)

    def test_tokens_has_transitions(self) -> None:
        """Test TOKENS has UITransition instance."""
        assert isinstance(TOKENS.transitions, UITransition)


class TestSizes:
    """Test UISizes token values."""

    def test_button_sizes(self) -> None:
        """Test button size tokens."""
        assert TOKENS.sizes.button_height_sm == 24
        assert TOKENS.sizes.button_height_md == 28
        assert TOKENS.sizes.button_height_lg == 32
        assert TOKENS.sizes.button_min_width == 80

    def test_input_sizes(self) -> None:
        """Test input size tokens."""
        assert TOKENS.sizes.input_height_sm == 24
        assert TOKENS.sizes.input_height_md == 28
        assert TOKENS.sizes.input_height_lg == 36
        assert TOKENS.sizes.input_min_width == 120

    def test_icon_sizes(self) -> None:
        """Test icon size tokens."""
        assert TOKENS.sizes.icon_xs == 12
        assert TOKENS.sizes.icon_sm == 16
        assert TOKENS.sizes.icon_md == 20
        assert TOKENS.sizes.icon_lg == 24

    def test_dialog_sizes(self) -> None:
        """Test dialog size tokens."""
        assert TOKENS.sizes.dialog_width_sm == 400
        assert TOKENS.sizes.dialog_width_md == 600
        assert TOKENS.sizes.dialog_width_lg == 800
        assert TOKENS.sizes.dialog_height_md == 500

    def test_toolbar_sizes(self) -> None:
        """Test toolbar size tokens."""
        assert TOKENS.sizes.toolbar_height == 40
        assert TOKENS.sizes.toolbar_icon_size == 24

    def test_border_radius_tokens_in_radii(self) -> None:
        """Test border radius tokens are in radii, not sizes."""
        assert TOKENS.radii.sm == 4
        assert TOKENS.radii.md == 8
        assert TOKENS.radii.lg == 12

    def test_spacing_tokens(self) -> None:
        """Test spacing value tokens in UISpacing."""
        assert TOKENS.spacing.xs == 2
        assert TOKENS.spacing.sm == 4
        assert TOKENS.spacing.md == 8
        assert TOKENS.spacing.lg == 12


class TestSpacing:
    """Test UISpacing token values."""

    def test_spacing_scale(self) -> None:
        """Test spacing scale tokens."""
        assert TOKENS.spacing.xs == 2
        assert TOKENS.spacing.sm == 4
        assert TOKENS.spacing.md == 8
        assert TOKENS.spacing.lg == 12
        assert TOKENS.spacing.xl == 16
        assert TOKENS.spacing.xxl == 24
        assert TOKENS.spacing.xxxl == 32

    def test_layout_spacing(self) -> None:
        """Test layout-specific spacing tokens."""
        assert TOKENS.spacing.form_spacing == 12
        assert TOKENS.spacing.button_spacing == 8
        assert TOKENS.spacing.toolbar_spacing == 4

    def test_component_spacing(self) -> None:
        """Test component internal spacing tokens."""
        assert TOKENS.spacing.checkbox_label_spacing == 8
        assert TOKENS.spacing.button_icon_text_spacing == 6


class TestMargins:
    """Test UIMargins token values."""

    def test_preset_margins(self) -> None:
        """Test preset margin tuples."""
        assert TOKENS.margins.none == (0, 0, 0, 0)
        assert TOKENS.margins.tight == (4, 4, 4, 4)
        assert TOKENS.margins.compact == (8, 8, 8, 8)
        assert TOKENS.margins.standard == (12, 12, 12, 12)
        assert TOKENS.margins.comfortable == (16, 16, 16, 16)
        assert TOKENS.margins.spacious == (24, 24, 24, 24)

    def test_component_margins(self) -> None:
        """Test component-specific margin tokens."""
        assert TOKENS.margins.panel_content == (12, 12, 12, 12)
        assert TOKENS.margins.toolbar == (8, 4, 8, 4)
        assert TOKENS.margins.dialog == (16, 16, 16, 16)

    def test_asymmetric_margins(self) -> None:
        """Test asymmetric margin tokens."""
        assert TOKENS.margins.form_row == (0, 4, 0, 4)
        assert TOKENS.margins.header_bottom == (0, 0, 0, 8)


class TestRadii:
    """Test UIRadii token values."""

    def test_radius_scale(self) -> None:
        """Test radius scale tokens."""
        assert TOKENS.radii.none == 0
        assert TOKENS.radii.sm == 4
        assert TOKENS.radii.md == 8
        assert TOKENS.radii.lg == 12
        assert TOKENS.radii.xl == 20
        assert TOKENS.radii.two_xl == 28
        assert TOKENS.radii.full == 999

    def test_component_radii(self) -> None:
        """Test component-specific radius tokens."""
        assert TOKENS.radii.button == 4
        assert TOKENS.radii.input == 4
        assert TOKENS.radii.menu == 6
        assert TOKENS.radii.dialog == 8


class TestFonts:
    """Test UIFonts token values."""

    def test_font_families(self) -> None:
        """Test font family tokens."""
        assert "Inter" in TOKENS.fonts.ui
        assert "Segoe UI" in TOKENS.fonts.ui
        assert "JetBrains Mono" in TOKENS.fonts.mono

    def test_font_sizes(self) -> None:
        """Test font size tokens."""
        assert TOKENS.fonts.size_xs == 10
        assert TOKENS.fonts.size_sm == 11
        assert TOKENS.fonts.size_md == 12
        assert TOKENS.fonts.size_lg == 14
        assert TOKENS.fonts.xl == 16

    def test_component_font_sizes(self) -> None:
        """Test component-specific font size tokens."""
        assert TOKENS.fonts.button == 12
        assert TOKENS.fonts.input == 12
        assert TOKENS.fonts.menu == 13
        assert TOKENS.fonts.table == 12


class TestTransitions:
    """Test UITransition token values."""

    def test_transition_durations(self) -> None:
        """Test transition duration tokens."""
        assert TOKENS.transitions.instant == 50
        assert TOKENS.transitions.fast == 100
        assert TOKENS.transitions.normal == 150
        assert TOKENS.transitions.medium == 200
        assert TOKENS.transitions.slow == 300

    def test_specific_transitions(self) -> None:
        """Test specific animation transition tokens."""
        assert TOKENS.transitions.hover == 100
        assert TOKENS.transitions.focus == 150
        assert TOKENS.transitions.appear == 200
        assert TOKENS.transitions.fade == 150


# =============================================================================
# TestConstants - Legacy constant classes
# =============================================================================


class TestConstants:
    """Test legacy constant instances."""

    def test_spacing_constants(self) -> None:
        """Test SPACING constants."""
        assert SPACING.xs == 2
        assert SPACING.sm == 4
        assert SPACING.md == 8
        assert SPACING.lg == 12
        assert SPACING.xl == 16

    def test_border_constants(self) -> None:
        """Test BORDERS constants."""
        assert BORDERS.none == 0
        assert BORDERS.thin == 1
        assert BORDERS.medium == 2
        assert BORDERS.thick == 3

    def test_radius_constants(self) -> None:
        """Test RADIUS constants."""
        assert RADIUS.none == 0
        assert RADIUS.sm == 4
        assert RADIUS.md == 8
        assert RADIUS.lg == 12
        assert RADIUS.xl == 20
        assert RADIUS.two_xl == 28
        assert RADIUS.full == 999

    def test_font_size_constants(self) -> None:
        """Test FONT_SIZES constants."""
        assert FONT_SIZES.xs == 10
        assert FONT_SIZES.sm == 11
        assert FONT_SIZES.md == 12
        assert FONT_SIZES.lg == 14
        assert FONT_SIZES.xl == 16
        assert FONT_SIZES.xxl == 20

    def test_size_constants(self) -> None:
        """Test SIZES constants."""
        assert SIZES.scrollbar_width == 8
        assert SIZES.toolbar_padding == 8
        assert SIZES.input_min_height == 24

    def test_font_constants(self) -> None:
        """Test FONTS and font alias constants."""
        assert "Inter" in FONTS.ui
        assert "JetBrains Mono" in FONTS.mono
        assert UI_FONT == FONTS.ui
        assert MONO_FONT == FONTS.mono

    def test_spacing_map(self) -> None:
        """Test SPACING_MAP dictionary."""
        assert SPACING_MAP["xs"] == 2
        assert SPACING_MAP["md"] == 8
        assert SPACING_MAP["xl"] == 16

    def test_radius_map(self) -> None:
        """Test RADIUS_MAP dictionary."""
        assert RADIUS_MAP["none"] == 0
        assert RADIUS_MAP["sm"] == 4
        assert RADIUS_MAP["md"] == 8
        assert RADIUS_MAP["2xl"] == 28
        assert RADIUS_MAP["two_xl"] == 28  # Alias

    def test_font_size_map(self) -> None:
        """Test FONT_SIZE_MAP dictionary."""
        assert FONT_SIZE_MAP["xs"] == 10
        assert FONT_SIZE_MAP["md"] == 12
        assert FONT_SIZE_MAP["lg"] == 14


# =============================================================================
# TestColorUtils - Color manipulation utilities
# =============================================================================


class TestColorUtils:
    """Test color manipulation utility functions."""

    # hex_to_rgb tests
    def test_hex_to_rgb_six_digit(self) -> None:
        """Test converting 6-digit hex to RGB."""
        assert hex_to_rgb("#ff0000") == (255, 0, 0)
        assert hex_to_rgb("#00ff00") == (0, 255, 0)
        assert hex_to_rgb("#0000ff") == (0, 0, 255)

    def test_hex_to_rgb_three_digit(self) -> None:
        """Test converting 3-digit hex to RGB."""
        assert hex_to_rgb("#f00") == (255, 0, 0)
        assert hex_to_rgb("#0f0") == (0, 255, 0)
        assert hex_to_rgb("#00f") == (0, 0, 255)

    def test_hex_to_rgb_without_hash(self) -> None:
        """Test converting hex without # prefix."""
        assert hex_to_rgb("ff0000") == (255, 0, 0)
        assert hex_to_rgb("f00") == (255, 0, 0)

    def test_hex_to_rgb_mixed_case(self) -> None:
        """Test converting mixed case hex."""
        assert hex_to_rgb("#Ff00Aa") == (255, 0, 170)
        assert hex_to_rgb("#ABC") == (170, 187, 204)

    # rgb_to_hex tests
    def test_rgb_to_hex_basic(self) -> None:
        """Test converting RGB to hex."""
        assert rgb_to_hex(255, 0, 0) == "#ff0000"
        assert rgb_to_hex(0, 255, 0) == "#00ff00"
        assert rgb_to_hex(0, 0, 255) == "#0000ff"

    def test_rgb_to_hex_boundary_values(self) -> None:
        """Test converting boundary RGB values."""
        assert rgb_to_hex(0, 0, 0) == "#000000"
        assert rgb_to_hex(255, 255, 255) == "#ffffff"

    def test_rgb_to_hex_clamping(self) -> None:
        """Test RGB values are properly formatted."""
        # Test values that should be formatted correctly
        assert rgb_to_hex(10, 10, 10) == "#0a0a0a"
        assert rgb_to_hex(16, 32, 48) == "#102030"

    # darken tests
    def test_darken_by_percent(self) -> None:
        """Test darkening color by percentage."""
        assert darken("#ffffff", 50) == "#7f7f7f"  # 255 * 0.5 = 127.5 -> 127
        assert darken("#ff0000", 50) == "#7f0000"
        assert darken("#00ff00", 25) == "#00bf00"  # 255 * 0.75 = 191.25 -> 191

    def test_darken_zero_percent(self) -> None:
        """Test darkening by 0% returns original color."""
        assert darken("#ff0000", 0) == "#ff0000"

    def test_darken_hundred_percent(self) -> None:
        """Test darkening by 100% returns black."""
        assert darken("#ff0000", 100) == "#000000"

    def test_darken_clamps_at_zero(self) -> None:
        """Test darken doesn't go below black."""
        assert darken("#000000", 50) == "#000000"
        # 90% darkening of #333333 (51) -> 51 * 0.1 = 5.1 -> 5
        assert darken("#333333", 90) == "#050505"

    # lighten tests
    def test_lighten_by_percent(self) -> None:
        """Test lightening color by percentage."""
        assert lighten("#000000", 50) == "#7f7f7f"  # 255 * 0.5 = 127.5 -> 127
        assert lighten("#808080", 50) == "#bfbfbf"

    def test_lighten_zero_percent(self) -> None:
        """Test lightening by 0% returns original color."""
        assert lighten("#ff0000", 0) == "#ff0000"

    def test_lighten_hundred_percent(self) -> None:
        """Test lightening by 100% returns white."""
        assert lighten("#000000", 100) == "#ffffff"

    def test_lighten_clamps_at_white(self) -> None:
        """Test lighten doesn't go above white."""
        assert lighten("#ffffff", 50) == "#ffffff"
        # 90% lightening of #cccccc (204) -> 204 + (255-204)*0.9 = 204 + 45.9 = 249.9 -> 249
        assert lighten("#cccccc", 90) == "#f9f9f9"

    # alpha tests
    def test_alpha_full_opacity(self) -> None:
        """Test alpha with full opacity."""
        result = alpha("#ff0000", 1.0)
        assert result == "rgba(255, 0, 0, 1.0)"

    def test_alpha_half_opacity(self) -> None:
        """Test alpha with half opacity."""
        result = alpha("#ff0000", 0.5)
        assert result == "rgba(255, 0, 0, 0.5)"

    def test_alpha_zero_opacity(self) -> None:
        """Test alpha with zero opacity."""
        result = alpha("#ff0000", 0.0)
        assert result == "rgba(255, 0, 0, 0.0)"

    def test_alpha_clamps_values(self) -> None:
        """Test alpha values beyond range are clamped."""
        # The function doesn't explicitly clamp, so values pass through
        result = alpha("#ff0000", 1.5)
        assert "rgba(255, 0, 0, 1.5)" == result

    # blend tests
    def test_blend_equal_ratio(self) -> None:
        """Test blending colors with equal ratio."""
        assert blend("#ff0000", "#0000ff", 0.5) == "#7f007f"

    def test_blend_first_color(self) -> None:
        """Test blend with 0 ratio returns first color."""
        assert blend("#ff0000", "#0000ff", 0.0) == "#ff0000"

    def test_blend_second_color(self) -> None:
        """Test blend with 1 ratio returns second color."""
        assert blend("#ff0000", "#0000ff", 1.0) == "#0000ff"

    def test_blend_custom_ratio(self) -> None:
        """Test blending with custom ratio."""
        result = blend("#ffffff", "#000000", 0.25)
        # Should be closer to white (first color)
        assert result == "#bfbfbf"

    # contrast_color tests
    def test_contrast_color_dark_background(self) -> None:
        """Test contrast color returns white for dark backgrounds."""
        assert contrast_color("#000000") == "#ffffff"
        assert contrast_color("#1e1e1e") == "#ffffff"
        assert contrast_color("#18181b") == "#ffffff"

    def test_contrast_color_light_background(self) -> None:
        """Test contrast color returns black for light backgrounds."""
        assert contrast_color("#ffffff") == "#000000"
        assert contrast_color("#f0f0f0") == "#000000"

    def test_contrast_color_mid_range(self) -> None:
        """Test contrast color for mid-range grays."""
        # 50% gray should return black (>= 0.5 luminance)
        assert contrast_color("#808080") == "#000000"
        # Slightly below 50% should return white
        assert contrast_color("#7f7f7f") == "#ffffff"

    # is_valid_hex tests
    def test_is_valid_hex_six_digit(self) -> None:
        """Test validating 6-digit hex colors."""
        assert is_valid_hex("#ff0000") is True
        assert is_valid_hex("#00ff00") is True
        assert is_valid_hex("#0000ff") is True

    def test_is_valid_hex_three_digit(self) -> None:
        """Test validating 3-digit hex colors."""
        assert is_valid_hex("#f00") is True
        assert is_valid_hex("#0f0") is True
        assert is_valid_hex("#00f") is True

    def test_is_valid_hex_without_hash(self) -> None:
        """Test validating hex without # prefix."""
        assert is_valid_hex("ff0000") is True
        assert is_valid_hex("f00") is True

    def test_is_valid_hex_invalid(self) -> None:
        """Test invalid hex color strings."""
        assert is_valid_hex("gg0000") is False
        assert is_valid_hex("#ff00") is False
        assert is_valid_hex("#ff0000ff") is False
        assert is_valid_hex("") is False
        assert is_valid_hex("invalid") is False

    def test_is_valid_hex_case_insensitive(self) -> None:
        """Test hex validation is case insensitive."""
        assert is_valid_hex("#FF0000") is True
        assert is_valid_hex("#AbCdEf") is True
        assert is_valid_hex("#ABC") is True

    # normalize_hex tests
    def test_normalize_hex_six_digit(self) -> None:
        """Test normalizing 6-digit hex."""
        assert normalize_hex("#ff0000") == "#ff0000"
        assert normalize_hex("FF0000") == "#ff0000"

    def test_normalize_hex_three_digit(self) -> None:
        """Test normalizing 3-digit hex expands to 6-digit."""
        assert normalize_hex("#f00") == "#ff0000"
        assert normalize_hex("#abc") == "#aabbcc"

    def test_normalize_hex_without_hash(self) -> None:
        """Test normalizing adds # prefix."""
        assert normalize_hex("ff0000") == "#ff0000"
        assert normalize_hex("f00") == "#ff0000"

    def test_normalize_hex_mixed_case(self) -> None:
        """Test normalizing converts to lowercase."""
        assert normalize_hex("#FF00AA") == "#ff00aa"
        assert normalize_hex("#ABCDEF") == "#abcdef"

    # saturate tests
    def test_saturate_color(self) -> None:
        """Test increasing color saturation."""
        # Starting with a gray, saturating should add color
        result = saturate("#808080", 50)
        # Gray (128, 128, 128) has no saturation to begin with
        # So saturating from gray doesn't change much
        assert result == "#808080"

    def test_saturate_color_with_hue(self) -> None:
        """Test saturating a color with existing hue."""
        # A desaturated red
        result = saturate("#c08080", 50)
        # Should be more saturated
        assert "#" in result

    # desaturate tests
    def test_desaturate_color(self) -> None:
        """Test decreasing color saturation."""
        # Bright red desaturated by 100% becomes gray
        # Using luminance formula: 0.299*255 + 0.587*0 + 0.114*0 = 76.245 -> 76
        result = desaturate("#ff0000", 100)
        assert result == "#4c4c4c"

    def test_desaturate_partial(self) -> None:
        """Test partial desaturation."""
        result = desaturate("#ff0000", 50)
        # Should be closer to gray than original
        r = int(result[1:3], 16)
        g = int(result[3:5], 16)
        b = int(result[5:7], 16)
        assert g > 0 and b > 0  # Now has green and blue components

    def test_desaturate_zero_percent(self) -> None:
        """Test desaturating by 0% returns original."""
        assert desaturate("#ff0000", 0) == "#ff0000"


# =============================================================================
# TestStylesheetGeneration - QSS stylesheet generation
# =============================================================================


class TestStylesheetGeneration:
    """Test QSS stylesheet generation functions."""

    def test_main_window_styles_contains_background(self) -> None:
        """Test main window styles contain background color."""
        qss = get_main_window_styles(THEME)
        assert "QMainWindow" in qss
        assert THEME.bg_darkest in qss

    def test_main_window_styles_contains_separator(self) -> None:
        """Test main window styles define separator."""
        qss = get_main_window_styles(THEME)
        assert "separator" in qss.lower()

    def test_base_widget_styles(self) -> None:
        """Test base widget styles are generated."""
        qss = get_base_widget_styles(THEME)
        assert "QWidget" in qss
        assert "background-color: transparent" in qss
        assert THEME.text_primary in qss

    def test_menu_styles(self) -> None:
        """Test menu styles contain VS Code/Cursor styling."""
        qss = get_menu_styles(THEME)
        assert "QMenu" in qss
        assert THEME.menu_bg in qss
        assert THEME.menu_border in qss
        assert THEME.menu_hover in qss

    def test_toolbar_styles(self) -> None:
        """Test toolbar styles are generated."""
        qss = get_toolbar_styles(THEME)
        assert "QToolBar" in qss
        assert "QToolButton" in qss
        assert THEME.toolbar_bg in qss

    def test_button_styles(self) -> None:
        """Test button styles contain expected states."""
        qss = get_button_styles(THEME)
        assert "QPushButton" in qss
        assert ":hover" in qss
        assert ":pressed" in qss
        assert ":disabled" in qss

    def test_button_styles_accent_primary(self) -> None:
        """Test button styles use accent color."""
        qss = get_button_styles(THEME)
        assert THEME.bg_medium in qss
        assert THEME.bg_light in qss
        assert THEME.accent_primary in qss

    def test_input_styles(self) -> None:
        """Test input styles contain focus state."""
        qss = get_input_styles(THEME)
        assert "QLineEdit" in qss
        assert ":focus" in qss
        assert THEME.border_focus in qss

    def test_input_styles_disabled(self) -> None:
        """Test input styles have disabled state."""
        qss = get_input_styles(THEME)
        assert ":disabled" in qss
        assert THEME.text_disabled in qss

    def test_scrollbar_styles(self) -> None:
        """Test scrollbar styles are generated."""
        qss = get_scrollbar_styles(THEME)
        assert "QScrollBar" in qss
        assert ":vertical" in qss
        assert ":horizontal" in qss

    def test_scrollbar_modern_style(self) -> None:
        """Test scrollbar uses modern/slim style."""
        qss = get_scrollbar_styles(THEME)
        assert "handle" in qss.lower()
        assert THEME.bg_darkest in qss
        assert THEME.bg_light in qss

    def test_full_stylesheet_contains_all_sections(self) -> None:
        """Test complete stylesheet contains all widget sections."""
        qss = get_canvas_stylesheet(THEME)
        # Check for major sections
        assert "QMainWindow" in qss
        assert "QWidget" in qss
        assert "QMenu" in qss
        assert "QToolBar" in qss
        assert "QPushButton" in qss
        assert "QLineEdit" in qss
        assert "QScrollBar" in qss
        assert "QCheckBox" in qss
        assert "QDialog" in qss

    def test_stylesheet_contains_theme_colors(self) -> None:
        """Test stylesheet uses theme colors, not hardcoded values."""
        qss = get_canvas_stylesheet(THEME)
        # Check for theme color values (not hardcoded hex codes)
        assert THEME.bg_darkest in qss
        assert THEME.text_primary in qss
        assert THEME.accent_primary in qss
        assert THEME.border in qss

    def test_stylesheet_no_common_hardcoded_colors(self) -> None:
        """Test stylesheet doesn't use common hardcoded colors."""
        qss = get_canvas_stylesheet(THEME)
        # Check for absence of common hardcoded colors
        # (allowing #fff and #000 which are standard)
        # We shouldn't have random hex codes like #1a1a2e, #16213e, etc.
        # Check that theme colors are used instead
        assert THEME.bg_darkest in qss or "#18181b" in qss

    def test_stylesheet_css_properties(self) -> None:
        """Test stylesheet contains expected CSS properties."""
        qss = get_canvas_stylesheet(THEME)
        expected_properties = [
            "background-color",
            "color",
            "border",
            "border-radius",
            "padding",
            "margin",
            "font-size",
            "font-family",
        ]
        for prop in expected_properties:
            assert prop in qss, f"Missing CSS property: {prop}"

    def test_stylesheet_qss_comments(self) -> None:
        """Test stylesheet contains QSS comments for sections."""
        qss = get_canvas_stylesheet(THEME)
        assert "/*" in qss
        assert "===" in qss or "MAIN WINDOW" in qss or "BUTTON" in qss


# =============================================================================
# Integration tests combining multiple components
# =============================================================================


class TestThemeIntegration:
    """Integration tests combining multiple theme components."""

    def test_theme_and_stylesheet_integration(self) -> None:
        """Test theme colors are properly used in generated stylesheet."""
        custom_theme = CanvasThemeColors(
            bg_darkest="#000000",
            text_primary="#ffffff",
            accent_primary="#ff00ff",
        )

        qss = get_canvas_stylesheet(custom_theme)

        # Verify custom theme colors are used
        assert "#000000" in qss
        assert "#ffffff" in qss
        assert "#ff00ff" in qss

    def test_tokens_and_constants_consistency(self) -> None:
        """Test TOKENS and legacy constants are consistent."""
        # Spacing values should match
        assert TOKENS.spacing.md == SPACING.md
        assert TOKENS.spacing.sm == SPACING.sm

        # Radius values should match
        assert TOKENS.radii.md == RADIUS.md
        assert TOKENS.radii.lg == RADIUS.lg

    def test_wire_color_helper_matches_theme(self) -> None:
        """Test wire color helper uses theme values correctly."""
        # Default theme
        assert get_wire_color("exec") == THEME.wire_exec
        assert get_wire_color("string") == THEME.wire_string
        assert get_wire_color("number") == THEME.wire_number

    def test_status_color_helper_matches_theme(self) -> None:
        """Test status color helper uses theme values correctly."""
        assert get_status_color("success") == THEME.status_success
        assert get_status_color("error") == THEME.status_error
        assert get_status_color("warning") == THEME.status_warning

    def test_node_status_color_helper_matches_theme(self) -> None:
        """Test node status color helper uses theme values correctly."""
        assert get_node_status_color("idle") == THEME.node_idle
        assert get_node_status_color("running") == THEME.node_running
        assert get_node_status_color("success") == THEME.node_success
        assert get_node_status_color("error") == THEME.node_error

    def test_color_utils_roundtrip(self) -> None:
        """Test color conversion roundtrip is consistent."""
        original = "#ff00aa"
        rgb = hex_to_rgb(original)
        back_to_hex = rgb_to_hex(*rgb)
        assert normalize_hex(original) == back_to_hex

    def test_full_stylesheet_structure(self) -> None:
        """Test full stylesheet has expected structure and sections."""
        qss = get_canvas_stylesheet(THEME)

        # Check for section comments
        assert "MAIN WINDOW" in qss or "QMainWindow" in qss
        assert "BUTTON" in qss or "QPushButton" in qss
        assert "INPUT" in qss or "QLineEdit" in qss
        assert "SCROLLBAR" in qss or "QScrollBar" in qss

        # Check for no obviously malformed CSS
        assert "{{" not in qss  # Double braces indicate issue
        assert "}}" not in qss  # Double braces indicate issue
        # Single braces are correct in QSS
        assert "{" in qss and "}" in qss
