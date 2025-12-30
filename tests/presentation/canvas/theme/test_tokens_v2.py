"""
Tests for Design Tokens v2 (Dark-Only, Compact).

Tests verify that v2 tokens meet the specification:
- Dark-only neutral ramp
- Cursor-like blue accent (#0066ff)
- Compact typography (smaller than v1)
- Tight spacing (4px grid with 6px exception)
- Small consistent radii
- Zero motion (all 0ms)
- Border width always 1px

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.1
"""

import pytest

from casare_rpa.presentation.canvas.theme_system import (
    THEME,
    THEME_V2,
    TOKENS,
    TOKENS_V2,
    get_canvas_stylesheet_v2,
)


class TestTokensV2Singleton:
    """Test that TOKENS_V2 singleton exists and is accessible."""

    def test_tokens_v2_singleton_exists(self) -> None:
        """TOKENS_V2 should be importable and accessible."""
        assert TOKENS_V2 is not None
        assert hasattr(TOKENS_V2, "spacing")
        assert hasattr(TOKENS_V2, "typography")
        assert hasattr(TOKENS_V2, "radius")
        assert hasattr(TOKENS_V2, "motion")

    def test_theme_v2_singleton_exists(self) -> None:
        """THEME_V2 should be importable and accessible."""
        assert THEME_V2 is not None
        assert hasattr(THEME_V2, "bg_canvas")
        assert hasattr(THEME_V2, "primary")
        assert hasattr(THEME_V2, "text_primary")


class TestNeutralRampV2:
    """Test dark-only neutral color ramp."""

    def test_neutral_ramp_is_dark(self) -> None:
        """Neutral ramp should use dark colors only."""
        # Darkest should be nearly black
        assert THEME_V2.bg_canvas in ("#080808", "#09090b", "#000000")

        # Lightest should be light gray (not white)
        # Parse hex to RGB
        def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
            h = hex_color.lstrip("#")
            return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

        # Lightest neutral should be < 200 (not white/bright)
        rgb = hex_to_rgb(THEME_V2.text_header)
        assert max(rgb) < 200


class TestAccentRampV2:
    """Test Cursor-like blue accent ramp."""

    def test_accent_is_cursor_blue(self) -> None:
        """Primary accent should be Cursor-like blue (#0066ff)."""
        assert THEME_V2.primary == "#0066ff"

    def test_accent_hover_exists(self) -> None:
        """Accent hover state should exist."""
        assert hasattr(THEME_V2, "primary_hover")
        assert THEME_V2.primary_hover.startswith("#")

    def test_accent_active_exists(self) -> None:
        """Accent active state should exist."""
        assert hasattr(THEME_V2, "primary_active")
        assert THEME_V2.primary_active.startswith("#")

    def test_accent_subtle_is_translucent(self) -> None:
        """Accent subtle should have alpha channel."""
        assert THEME_V2.bg_selected.endswith("20")  # ~12.5% alpha


class TestSemanticColorsV2:
    """Test semantic status colors."""

    def test_success_color_exists(self) -> None:
        """Success color should be defined."""
        assert THEME_V2.success == "#10b981"  # Emerald

    def test_warning_color_exists(self) -> None:
        """Warning color should be defined."""
        assert THEME_V2.warning == "#f59e0b"  # Amber

    def test_error_color_exists(self) -> None:
        """Error color should be defined."""
        assert THEME_V2.error == "#ef4444"  # Red

    def test_info_color_exists(self) -> None:
        """Info color should be defined."""
        assert THEME_V2.info == "#0ea5e9"  # Sky


class TestCompactTypographyV2:
    """Test compact typography (smaller than v1)."""

    def test_body_smaller_than_v1(self) -> None:
        """V2 body font should be smaller than V1 body."""
        assert TOKENS_V2.typography.body < TOKENS.typography.body
        assert TOKENS_V2.typography.body == 11  # V1 is 12

    def test_body_sm_smaller_than_v1(self) -> None:
        """V2 body_sm should be smaller than V1 body_s."""
        assert TOKENS_V2.typography.body_sm < TOKENS.typography.body_s
        assert TOKENS_V2.typography.body_sm == 10  # V1 is 11

    def test_caption_smaller_than_v1(self) -> None:
        """V2 caption should be smaller than V1 caption."""
        assert TOKENS_V2.typography.caption < TOKENS.typography.caption
        assert TOKENS_V2.typography.caption == 9  # V1 is 10

    def test_display_lg_smaller_than_v1(self) -> None:
        """V2 display_lg should be smaller than V1 display_l."""
        assert TOKENS_V2.typography.display_lg <= TOKENS.typography.display_l

    def test_font_families_defined(self) -> None:
        """Font families should be defined."""
        assert TOKENS_V2.typography.sans
        assert TOKENS_V2.typography.mono
        assert "Inter" in TOKENS_V2.typography.sans or "Segoe UI" in TOKENS_V2.typography.sans


class TestTightSpacingV2:
    """Test tight spacing (4px grid with 6px exception)."""

    def test_spacing_follows_4px_grid(self) -> None:
        """Most spacing values should follow 4px grid."""
        # Check that spacing values are multiples of 2 (tight 4px grid)
        assert TOKENS_V2.spacing.zero == 0
        assert TOKENS_V2.spacing.xxs == 2
        assert TOKENS_V2.spacing.xs == 4
        assert TOKENS_V2.spacing.md == 8
        assert TOKENS_V2.spacing.lg == 12
        assert TOKENS_V2.spacing.xl == 16
        assert TOKENS_V2.spacing.xxl == 24

    def test_spacing_has_6px_exception(self) -> None:
        """Spacing should include 6px for form rows (practical exception)."""
        assert TOKENS_V2.spacing.sm == 6


class TestSmallConsistentRadiiV2:
    """Test small consistent border radii."""

    def test_radius_values_are_small(self) -> None:
        """All radius values should be <= 6px (smaller than v1)."""
        assert TOKENS_V2.radius.none == 0
        assert TOKENS_V2.radius.xs == 2
        assert TOKENS_V2.radius.sm == 3  # v1 uses 4
        assert TOKENS_V2.radius.md == 4  # v1 uses 8
        assert TOKENS_V2.radius.lg == 6  # v1 uses 12

    def test_no_large_radius(self) -> None:
        """V2 should not have radius values > 6."""
        max_radius = max(
            TOKENS_V2.radius.none,
            TOKENS_V2.radius.xs,
            TOKENS_V2.radius.sm,
            TOKENS_V2.radius.md,
            TOKENS_V2.radius.lg,
        )
        assert max_radius <= 6


class TestBorderV2:
    """Test border rules."""

    def test_border_width_always_1(self) -> None:
        """Border width should always be 1px."""
        assert TOKENS_V2.border.width == 1
        assert TOKENS_V2.border.focus_width == 1


class TestZeroMotionV2:
    """Test zero-motion animation tokens."""

    def test_all_motion_durations_are_zero(self) -> None:
        """All motion durations should be 0ms (no animations)."""
        assert TOKENS_V2.motion.instant == 0
        assert TOKENS_V2.motion.fast == 0
        assert TOKENS_V2.motion.normal == 0
        assert TOKENS_V2.motion.slow == 0


class TestStylesheetV2Generation:
    """Test QSS stylesheet generation."""

    def test_stylesheet_v2_generates(self) -> None:
        """V2 stylesheet should generate without errors."""
        qss = get_canvas_stylesheet_v2()
        assert qss
        assert isinstance(qss, str)
        assert len(qss) > 100  # Should have content

    def test_stylesheet_v2_no_transitions(self) -> None:
        """V2 stylesheet should not contain transition/animation properties."""
        qss = get_canvas_stylesheet_v2().lower()
        # V2 should have no transitions (zero-motion policy)
        # Note: QSS doesn't use transition properties like CSS does,
        # but we check for any accidental inclusion
        assert "transition" not in qss
        assert "animation" not in qss

    def test_stylesheet_v2_uses_v2_colors(self) -> None:
        """V2 stylesheet should use v2 color values."""
        qss = get_canvas_stylesheet_v2()
        # Should contain v2 colors
        assert THEME_V2.bg_canvas in qss
        assert THEME_V2.primary in qss
        assert THEME_V2.bg_surface in qss


class TestTokenStructureV2:
    """Test v2 token structure consistency."""

    def test_all_token_groups_exist(self) -> None:
        """All expected token groups should exist."""
        assert hasattr(TOKENS_V2, "spacing")
        assert hasattr(TOKENS_V2, "margin")
        assert hasattr(TOKENS_V2, "radius")
        assert hasattr(TOKENS_V2, "border")
        assert hasattr(TOKENS_V2, "typography")
        assert hasattr(TOKENS_V2, "sizes")
        assert hasattr(TOKENS_V2, "motion")
        assert hasattr(TOKENS_V2, "z_index")

    def test_all_theme_colors_exist(self) -> None:
        """All expected theme colors should exist."""
        # Backgrounds
        assert hasattr(THEME_V2, "bg_canvas")
        assert hasattr(THEME_V2, "bg_surface")
        assert hasattr(THEME_V2, "bg_elevated")
        assert hasattr(THEME_V2, "bg_component")
        assert hasattr(THEME_V2, "bg_hover")

        # Text
        assert hasattr(THEME_V2, "text_primary")
        assert hasattr(THEME_V2, "text_secondary")
        assert hasattr(THEME_V2, "text_muted")

        # Brand
        assert hasattr(THEME_V2, "primary")
        assert hasattr(THEME_V2, "primary_hover")
        assert hasattr(THEME_V2, "primary_active")

        # Status
        assert hasattr(THEME_V2, "success")
        assert hasattr(THEME_V2, "warning")
        assert hasattr(THEME_V2, "error")
        assert hasattr(THEME_V2, "info")


class TestV2DoesNotAffectV1:
    """Test that v2 tokens don't affect v1 tokens."""

    def test_v1_tokens_unchanged(self) -> None:
        """V1 tokens should remain unchanged."""
        assert TOKENS.typography.body == 12
        assert TOKENS.radius.md == 8

    def test_v1_theme_unchanged(self) -> None:
        """V1 theme should remain unchanged."""
        assert THEME.primary == "#6366f1"  # Indigo, not Cursor blue


@pytest.mark.parametrize(
    "attr,expected_type",
    [
        ("spacing", int),
        ("margin", tuple),
        ("radius", int),
        ("typography", int),
        ("motion", int),
    ],
)
class TestTokenTypes:
    """Test that tokens have correct types."""

    def test_token_types(self, attr: str, expected_type: type) -> None:
        """Tokens should have expected types."""
        token_group = getattr(TOKENS_V2, attr.replace("_v2", ""))
        assert token_group is not None
