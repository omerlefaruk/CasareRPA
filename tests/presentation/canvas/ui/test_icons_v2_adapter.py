"""
Tests for icons_v2_adapter - Epic 2.2 icon adapter.

Tests the legacy to v2 icon name mapping, feature flag, and convenience functions.
"""

from typing import TYPE_CHECKING

import pytest
from PySide6.QtGui import QIcon

if TYPE_CHECKING:
    from casare_rpa.presentation.canvas.ui.icons_v2_adapter import IconState, IconSize


@pytest.fixture
def reset_v2_flag(monkeypatch):
    """Reset and restore USE_V2_ICONS flag."""
    from casare_rpa.presentation.canvas.ui import icons_v2_adapter
    original = icons_v2_adapter.USE_V2_ICONS

    yield

    icons_v2_adapter.USE_V2_ICONS = original


class TestIconAdapter:
    """Test the icons_v2_adapter functionality."""

    def test_legacy_name_maps_to_v2(self) -> None:
        """Test that legacy action names map to correct v2 icon names."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import (
            map_legacy_to_v2,
        )

        # Core chrome mappings
        assert map_legacy_to_v2("new") == "file"
        assert map_legacy_to_v2("open") == "folder"
        assert map_legacy_to_v2("save") == "save"
        assert map_legacy_to_v2("run") == "play"
        assert map_legacy_to_v2("stop") == "stop"
        assert map_legacy_to_v2("undo") == "undo"
        assert map_legacy_to_v2("redo") == "redo"
        assert map_legacy_to_v2("settings") == "settings"

    def test_unknown_name_returns_none(self) -> None:
        """Test that unknown legacy names return None."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import (
            map_legacy_to_v2,
        )

        assert map_legacy_to_v2("nonexistent_icon") is None

    def test_adapter_respects_size_parameter(self) -> None:
        """Test that adapter respects the size parameter."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

        # Different sizes should return valid icons
        icon_16 = get_icon_v2("save", size=16, state="normal")
        icon_20 = get_icon_v2("save", size=20, state="normal")
        icon_24 = get_icon_v2("save", size=24, state="normal")

        # All should be valid (non-null) for known icons
        assert not icon_16.isNull()
        assert not icon_20.isNull()
        assert not icon_24.isNull()

    def test_adapter_respects_state_parameter(self) -> None:
        """Test that adapter respects the state parameter."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

        # Different states should return valid icons
        icon_normal = get_icon_v2("play", size=20, state="normal")
        icon_disabled = get_icon_v2("play", size=20, state="disabled")
        icon_accent = get_icon_v2("play", size=20, state="accent")

        # All should be valid (non-null) for known icons
        assert not icon_normal.isNull()
        assert not icon_disabled.isNull()
        assert not icon_accent.isNull()

    def test_feature_flag_disables_v2(self, monkeypatch) -> None:
        """Test that feature flag can disable v2 icons."""
        from casare_rpa.presentation.canvas.ui import icons_v2_adapter

        # Disable v2 icons
        monkeypatch.setattr(icons_v2_adapter, "USE_V2_ICONS", False)

        # get_icon_v2 should return empty icon when disabled
        icon = icons_v2_adapter.get_icon_v2("save", size=20, state="normal")
        assert icon.isNull()

    def test_get_icon_v2_safe_with_fallback(self) -> None:
        """Test get_icon_v2_safe with fallback icon."""
        from PySide6.QtGui import QIcon

        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import (
            get_icon_v2_safe,
        )

        # Create fallback icon
        fallback = QIcon()

        # Should return fallback when icon not found
        result = get_icon_v2_safe(
            "nonexistent", size=20, state="normal", fallback=fallback
        )
        assert result.isNull()  # Fallback was also null

    def test_get_available_mappings(self) -> None:
        """Test that get_available_mappings returns expected mappings."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import (
            get_available_mappings,
        )

        mappings = get_available_mappings()

        # Should have at least core chrome icons
        assert "new" in mappings
        assert "open" in mappings
        assert "save" in mappings
        assert "run" in mappings
        assert "stop" in mappings
        assert "undo" in mappings
        assert "redo" in mappings
        assert "settings" in mappings

        # Should have at least 40 mappings
        assert len(mappings) >= 40


class TestIconMappings:
    """Test specific icon mappings for Epic 2.2."""

    @pytest.mark.parametrize(
        "legacy,v2",
        [
            ("new", "file"),
            ("open", "folder"),
            ("save", "save"),
            ("undo", "undo"),
            ("redo", "redo"),
            ("run", "play"),
            ("stop", "stop"),
            ("pause", "pause"),
            ("settings", "settings"),
            ("search", "search"),
            ("refresh", "refresh"),
            ("trash", "trash"),
            ("copy", "copy"),
            ("paste", "paste"),
            ("zoom_in", "zoom-in"),
            ("zoom_out", "zoom-out"),
        ],
    )
    def test_core_mappings(self, legacy: str, v2: str) -> None:
        """Test that core legacy icons map to correct v2 icons."""
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import (
            map_legacy_to_v2,
        )

        assert map_legacy_to_v2(legacy) == v2


class TestAdapterIntegration:
    """Test adapter integration with theme system."""

    def test_adapter_uses_theme_v2(self) -> None:
        """Test that adapter integrates with THEME_V2."""
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import icon_v2
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import get_icon_v2

        # Adapter should use icon_v2 which uses THEME_V2
        icon = get_icon_v2("play", size=20, state="accent")

        # Icon should be valid
        assert not icon.isNull()

        # Verify state colors in icon_v2
        assert "normal" in icon_v2._STATE_COLORS
        assert "disabled" in icon_v2._STATE_COLORS
        assert "accent" in icon_v2._STATE_COLORS

    def test_adapter_with_v2_icons_directory(self) -> None:
        """Test that adapter works with icons directory."""
        from casare_rpa.presentation.canvas.theme_system.icons_v2 import icon_v2

        # Should have icons directory resolved
        assert icon_v2._icons_dir is not None

        # Should have available icons
        available = icon_v2.get_available_icons()
        assert len(available) > 50  # At least core Lucide icons


class TestGetIconV2OrLegacy:
    """Test the get_icon_v2_or_legacy convenience function."""

    def test_returns_v2_when_enabled(self, monkeypatch) -> None:
        """Test that get_icon_v2_or_legacy returns v2 icon when enabled."""
        from casare_rpa.presentation.canvas.ui import icons
        from casare_rpa.presentation.canvas.ui.icons_v2_adapter import USE_V2_ICONS

        # Ensure v2 is enabled
        monkeypatch.setattr(icons, "USE_V2_ICONS", True)

        icon = icons.get_icon_v2_or_legacy("save", size=20)

        # Should return valid icon (v2 or legacy)
        assert isinstance(icon, QIcon)

    def test_returns_legacy_when_disabled(self, monkeypatch) -> None:
        """Test that get_icon_v2_or_legacy returns legacy icon when v2 disabled."""
        from casare_rpa.presentation.canvas.ui import icons

        # Disable v2
        monkeypatch.setattr(icons, "USE_V2_ICONS", False)

        icon = icons.get_icon_v2_or_legacy("save", size=20)

        # Should return valid icon from legacy
        assert isinstance(icon, QIcon)
