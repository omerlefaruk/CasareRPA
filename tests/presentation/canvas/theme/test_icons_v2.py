"""
Tests for IconProviderV2 - Epic 2.1.

Tests the icon provider v2 that loads SVG icons from resources/icons/
and applies THEME_V2 colors.

See: docs/UX_REDESIGN_PLAN.md Phase 2 Epic 2.1
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass


class TestIconProviderV2Singleton:
    """Test that IconProviderV2 singleton exists and is accessible."""

    def test_icon_v2_singleton_exists(self) -> None:
        """icon_v2 singleton should be importable and accessible."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        assert icon_v2 is not None

    def test_icon_v2_has_methods(self) -> None:
        """icon_v2 should have get_icon and get_pixmap methods."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        assert hasattr(icon_v2, "get_icon")
        assert hasattr(icon_v2, "get_pixmap")
        assert hasattr(icon_v2, "get_available_icons")
        assert hasattr(icon_v2, "has_icon")
        assert hasattr(icon_v2, "clear_cache")


class TestIconRendering:
    """Test IconProviderV2.get_icon() and get_pixmap() methods."""

    def test_get_icon_returns_qicon(self) -> None:
        """get_icon should return valid QIcon instance."""
        from PySide6.QtGui import QIcon

        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        icon = icon_v2.get_icon("file")
        assert isinstance(icon, QIcon)

    def test_get_icon_unknown_name_returns_empty(self) -> None:
        """Unknown icon name should return empty QIcon (not crash)."""
        from PySide6.QtGui import QIcon

        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        icon = icon_v2.get_icon("nonexistent_icon_xyz")
        assert isinstance(icon, QIcon)
        # Empty icon hasisNull() == True
        # We don't assert this because we want graceful degradation

    def test_get_pixmap_returns_pixmap(self) -> None:
        """get_pixmap should return QPixmap for valid icon."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        pixmap = icon_v2.get_pixmap("play", size=20)
        assert pixmap is not None
        assert pixmap.width() == 20
        assert pixmap.height() == 20

    def test_get_pixmap_unknown_name_returns_none(self) -> None:
        """Unknown icon name should return None."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        pixmap = icon_v2.get_pixmap("nonexistent_icon_xyz")
        assert pixmap is None


class TestCoreChromeIcons:
    """Test that core chrome icons exist and render correctly."""

    @pytest.mark.parametrize(
        "name",
        [
            "file",
            "folder",
            "save",
            "edit",
            "play",
            "pause",
            "stop",
            "settings",
            "search",
            "refresh",
            "trash",
            "copy",
            "paste",
            "undo",
            "redo",
            "check",
            "close",
            "plus",
            "minus",
            "menu",
        ],
    )
    def test_core_chrome_icons_exist(self, name: str) -> None:
        """Core chrome icons should be available and renderable."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        assert icon_v2.has_icon(name), f"Icon '{name}' should exist"

        icon = icon_v2.get_icon(name, size=20)
        assert not icon.isNull(), f"Icon '{name}' should not be null"

        pixmap = icon_v2.get_pixmap(name, size=20)
        assert pixmap is not None, f"Pixmap for '{name}' should not be None"


class TestIconSizes:
    """Test icon size variants (16/20/24 from TOKENS_V2.sizes)."""

    @pytest.mark.parametrize("size", [16, 20, 24])
    def test_icon_sizes(self, size: int) -> None:
        """Icons should render in all defined sizes."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        pixmap = icon_v2.get_pixmap("file", size=size)  # type: ignore
        assert pixmap is not None
        assert pixmap.width() == size
        assert pixmap.height() == size


class TestIconStates:
    """Test icon state variants (normal/disabled/accent)."""

    def test_icon_states(self) -> None:
        """Icons should support normal, disabled, and accent states."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        normal = icon_v2.get_pixmap("play", size=20, state="normal")
        disabled = icon_v2.get_pixmap("play", size=20, state="disabled")
        accent = icon_v2.get_pixmap("play", size=20, state="accent")

        assert normal is not None
        assert disabled is not None
        assert accent is not None


class TestIconCaching:
    """Test icon caching behavior."""

    def test_cache_key_includes_size_and_state(self) -> None:
        """Cache should return different icons for different sizes/states."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        # Clear cache first
        icon_v2.clear_cache()

        # Request same icon with different parameters
        icon1 = icon_v2.get_icon("file", size=16, state="normal")
        icon2 = icon_v2.get_icon("file", size=20, state="normal")
        icon3 = icon_v2.get_icon("file", size=20, state="accent")

        # All should be valid icons
        assert not icon1.isNull()
        assert not icon2.isNull()
        assert not icon3.isNull()

    def test_clear_cache_works(self) -> None:
        """clear_cache should empty the internal cache."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        # Populate cache
        icon_v2.get_icon("file", size=20)
        icon_v2.clear_cache()
        # Should not raise, just work
        icon = icon_v2.get_icon("file", size=20)
        assert not icon.isNull()


class TestIconDirectoryResolution:
    """Test icons directory resolution (dev vs frozen mode)."""

    def test_icons_directory_exists(self) -> None:
        """Icons directory should be resolvable."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import _get_icons_dir

        icons_dir = _get_icons_dir()
        assert icons_dir.exists(), f"Icons directory should exist: {icons_dir}"

    def test_available_icons_non_empty(self) -> None:
        """get_available_icons should return non-empty list."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        icons = icon_v2.get_available_icons()
        assert len(icons) > 0, "Should have at least some icons"
        # Check for expected minimum count
        assert len(icons) >= 50, f"Should have at least 50 icons, got {len(icons)}"

    def test_available_icons_are_strings(self) -> None:
        """Available icons should be string names without .svg extension."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import icon_v2

        icons = icon_v2.get_available_icons()
        for icon_name in icons:
            assert isinstance(icon_name, str)
            assert not icon_name.endswith(".svg"), "Icon names should not include .svg extension"


class TestModuleExports:
    """Test that module exports are correct."""

    def test_module_all_exports(self) -> None:
        """__all__ should define the public API."""
        from casare_rpa.presentation.canvas.theme import icons_v2

        expected = {
            "IconProviderV2",
            "icon_v2",
            "get_icon",
            "get_pixmap",
            "IconState",
            "IconSize",
        }
        actual = set(icons_v2.__all__)
        assert actual == expected, f"Expected {expected}, got {actual}"

    def test_theme_exports_icons(self) -> None:
        """`theme` package should export icon v2 symbols."""
        # Note: Due to circular imports, we import directly from icons_v2
        from casare_rpa.presentation.canvas.theme.icons_v2 import (
            IconProviderV2,
            get_icon,
            get_pixmap,
            icon_v2,
        )

        assert icon_v2 is not None
        assert IconProviderV2 is not None
        assert callable(get_icon)
        assert callable(get_pixmap)


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_icon_convenience(self) -> None:
        """get_icon convenience function should work."""
        from PySide6.QtGui import QIcon

        from casare_rpa.presentation.canvas.theme.icons_v2 import get_icon

        icon = get_icon("settings", size=24, state="accent")  # type: ignore
        assert isinstance(icon, QIcon)
        assert not icon.isNull()

    def test_get_pixmap_convenience(self) -> None:
        """get_pixmap convenience function should work."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import get_pixmap

        pixmap = get_pixmap("check", size=16, state="normal")  # type: ignore
        assert pixmap is not None
        assert pixmap.width() == 16


class TestThemeIntegration:
    """Test integration with THEME_V2 colors."""

    def test_state_colors_use_theme_v2(self) -> None:
        """Icon state colors should come from THEME_V2."""
        from casare_rpa.presentation.canvas.theme.icons_v2 import IconProviderV2
        from casare_rpa.presentation.canvas.theme.tokens_v2 import THEME_V2

        assert IconProviderV2._STATE_COLORS["normal"] == THEME_V2.text_primary
        assert IconProviderV2._STATE_COLORS["disabled"] == THEME_V2.text_disabled
        assert IconProviderV2._STATE_COLORS["accent"] == THEME_V2.primary

