"""
Unit tests for the Canvas theme package (Design System 2025).

These tests validate:
- Design token singletons (`TOKENS`) and semantic theme colors (`THEME`)
- Wire/status color helpers
- Core QSS generation functions return usable stylesheets
- Basic color utility helpers behave sanely
"""

from __future__ import annotations

import re

import pytest

from casare_rpa.domain.value_objects.types import DataType
from casare_rpa.presentation.canvas.theme import (
    THEME,
    TOKENS,
    DesignTokensV2,
    ThemeColorsV2,
    darken,
    get_canvas_stylesheet_v2,
    get_main_window_styles_v2,
    get_status_color,
    get_wire_color,
    hex_to_rgb,
    rgb_to_hex,
)

pytestmark = pytest.mark.unit


def _is_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", value))


def test_singletons_are_available() -> None:
    assert isinstance(THEME, ThemeColorsV2)
    assert isinstance(TOKENS, DesignTokensV2)


def test_theme_has_expected_semantic_colors() -> None:
    assert _is_hex_color(THEME.bg_canvas)
    assert _is_hex_color(THEME.bg_surface)
    assert _is_hex_color(THEME.text_primary)
    assert _is_hex_color(THEME.primary)
    assert _is_hex_color(THEME.success)
    assert _is_hex_color(THEME.error)


def test_tokens_spacing_scale() -> None:
    assert TOKENS.spacing.zero == 0
    assert TOKENS.spacing.xs == 4
    assert TOKENS.spacing.md == 8
    assert TOKENS.spacing.xl == 16


def test_tokens_radius_scale() -> None:
    assert TOKENS.radius.none == 0
    assert TOKENS.radius.sm == 3
    assert TOKENS.radius.md == 4
    assert TOKENS.radius.lg == 6


def test_wire_color_helper_returns_hex() -> None:
    assert _is_hex_color(get_wire_color(DataType.STRING.name))
    assert _is_hex_color(get_wire_color(DataType.INTEGER.name))
    assert _is_hex_color(get_wire_color(DataType.ANY.name))


def test_status_color_helper_returns_hex() -> None:
    assert _is_hex_color(get_status_color("success"))
    assert _is_hex_color(get_status_color("warning"))
    assert _is_hex_color(get_status_color("error"))


def test_qss_generation_contains_main_window_rules() -> None:
    qss = get_canvas_stylesheet_v2()
    assert isinstance(qss, str)
    assert "QMainWindow" in qss

    mw_qss = get_main_window_styles_v2()
    assert "QMainWindow" in mw_qss


def test_color_utils_round_trip() -> None:
    rgb = hex_to_rgb("#6366f1")
    assert rgb == (99, 102, 241)
    assert rgb_to_hex(*rgb) == "#6366f1"

    darker = darken("#6366f1", 0.2)
    assert _is_hex_color(darker)
