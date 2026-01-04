"""
Tests for Font Loader (Epic 1.2 - Geist Sans/Mono bundling).

Tests verify:
- Font path resolution in dev and frozen modes
- Idempotent registration behavior
- Status reporting for registered fonts
- Graceful handling of missing fonts
- Font constant definitions

See: docs/UX_REDESIGN_PLAN.md Phase 1 Epic 1.2
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from casare_rpa.presentation.canvas.theme.font_loader import (
    GEIST_MONO_FAMILY,
    GEIST_MONO_FILES,
    GEIST_SANS_FAMILY,
    GEIST_SANS_FILES,
    _get_fonts_dir,
    _is_family_available,
    _register_font_family,
    get_registered_fonts,
)


class TestFontConstants:
    """Test that font constants are properly defined."""

    def test_geist_sans_family_defined(self) -> None:
        """GEIST_SANS_FAMILY should be defined as 'Geist Sans'."""
        assert GEIST_SANS_FAMILY == "Geist Sans"

    def test_geist_mono_family_defined(self) -> None:
        """GEIST_MONO_FAMILY should be defined as 'Geist Mono'."""
        assert GEIST_MONO_FAMILY == "Geist Mono"

    def test_geist_sans_files_defined(self) -> None:
        """GEIST_SANS_FILES should be a tuple of expected filenames."""
        assert isinstance(GEIST_SANS_FILES, tuple)
        assert len(GEIST_SANS_FILES) == 3
        assert "Geist-Regular.ttf" in GEIST_SANS_FILES
        assert "Geist-Medium.ttf" in GEIST_SANS_FILES
        assert "Geist-SemiBold.ttf" in GEIST_SANS_FILES

    def test_geist_mono_files_defined(self) -> None:
        """GEIST_MONO_FILES should be a tuple of expected filenames."""
        assert isinstance(GEIST_MONO_FILES, tuple)
        assert len(GEIST_MONO_FILES) == 3
        assert "GeistMono-Regular.ttf" in GEIST_MONO_FILES
        assert "GeistMono-Medium.ttf" in GEIST_MONO_FILES
        assert "GeistMono-SemiBold.ttf" in GEIST_MONO_FILES


class TestGetFontsDir:
    """Test fonts directory path resolution."""

    def test_get_fonts_dir_returns_path_object(self) -> None:
        """Should always return a Path object."""
        result = _get_fonts_dir()
        assert isinstance(result, Path)

    def test_get_fonts_dir_has_fonts_name(self) -> None:
        """Result should contain 'fonts' in the path."""
        result = _get_fonts_dir()
        assert result.name == "fonts"

    def test_get_fonts_dir_frozen_mode(self, tmp_path: Path) -> None:
        """When frozen (PyInstaller), should return sys._MEIPASS/fonts."""
        # Create a frozen fonts directory
        frozen_fonts = tmp_path / "fonts"
        frozen_fonts.mkdir(parents=True)

        with (
            patch("sys.frozen", True, create=True),
            patch("sys._MEIPASS", str(tmp_path), create=True),
        ):
            import importlib

            import casare_rpa.presentation.canvas.theme.font_loader as fl

            importlib.reload(fl)

            result = fl._get_fonts_dir()
            assert result.name == "fonts"
            # When frozen, should point to the frozen location
            assert "fonts" in str(result)

    def test_get_fonts_dir_fallback_to_dev(self) -> None:
        """When no fonts dir exists, should still return a path."""
        result = _get_fonts_dir()
        # Should return a path (even if it doesn't exist)
        assert isinstance(result, Path)

    def test_get_fonts_dir_structure(self) -> None:
        """Returned path should have expected structure."""
        result = _get_fonts_dir()
        # The path should be absolute
        assert result.is_absolute()
        # Should end with fonts
        assert result.name == "fonts"


class TestRegisterFontFamily:
    """Test font family registration logic."""

    def test_register_with_nonexistent_dir(self, tmp_path: Path) -> None:
        """Should return False when fonts_dir doesn't exist."""
        nonexistent = tmp_path / "nonexistent"
        result = _register_font_family("Test Family", ("test.ttf",), nonexistent)
        assert result is False

    def test_register_with_missing_font_files(self, tmp_path: Path) -> None:
        """Should return False when font files don't exist."""
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir(parents=True)

        # Don't create any font files
        result = _register_font_family("Test Family", ("missing.ttf",), fonts_dir)
        assert result is False

    @patch("casare_rpa.presentation.canvas.theme.font_loader.QFontDatabase")
    def test_register_with_invalid_font(self, mock_qdb: MagicMock, tmp_path: Path) -> None:
        """Should handle invalid font files gracefully."""
        # Create a dummy file (not a real font)
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir(parents=True)
        dummy_font = fonts_dir / "dummy.ttf"
        dummy_font.write_text("not a real font")

        # Mock QFontDatabase to return invalid ID
        mock_qdb.addApplicationFont.return_value = -1  # Invalid font ID
        mock_qdb.applicationFontFamilies.return_value = []

        result = _register_font_family("Test", ("dummy.ttf",), fonts_dir)
        assert result is False

    @patch("casare_rpa.presentation.canvas.theme.font_loader.QFontDatabase")
    def test_register_partial_success(self, mock_qdb: MagicMock, tmp_path: Path) -> None:
        """Should return True if at least one font registers successfully."""
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir(parents=True)

        # Create dummy files
        for name in ["font1.ttf", "font2.ttf"]:
            (fonts_dir / name).write_text("dummy")

        # First font succeeds, second fails
        call_count = [0]

        def add_font_side_effect(path_str: str):
            call_count[0] += 1
            return 0 if call_count[0] == 1 else -1  # First succeeds, second fails

        mock_qdb.addApplicationFont.side_effect = add_font_side_effect
        mock_qdb.applicationFontFamilies.return_value = ["Test Family"]

        result = _register_font_family("Test Family", ("font1.ttf", "font2.ttf"), fonts_dir)
        assert result is True


class TestEnsureFontRegistered:
    """Test ensure_font_registered function."""

    def test_ensure_font_registered_is_idempotent(self) -> None:
        """Multiple calls should be safe (only register once)."""
        import casare_rpa.presentation.canvas.theme.font_loader as fl

        # Reset module state (no reload - avoids Qt crash)
        fl._font_registered = False

        # Mock _register_font_family to avoid Qt dependency
        with patch.object(fl, "_register_font_family", return_value={"Geist Sans": True}):
            # First call
            fl.ensure_font_registered()
            first_state = fl._font_registered

            # Second call - should skip (flag already True)
            fl.ensure_font_registered()
            assert fl._font_registered == first_state

    def test_ensure_font_registered_sets_flag(self) -> None:
        """Should set _font_registered flag to True."""
        import casare_rpa.presentation.canvas.theme.font_loader as fl

        # Reset module state (no reload - avoids Qt crash)
        fl._font_registered = False

        assert fl._font_registered is False

        # Mock _register_font_family to avoid Qt dependency
        with patch.object(fl, "_register_font_family", return_value={"Geist Sans": True}):
            fl.ensure_font_registered()

        assert fl._font_registered is True

    def test_missing_fonts_dir_handled_gracefully(self) -> None:
        """Should not crash when fonts directory doesn't exist."""
        import casare_rpa.presentation.canvas.theme.font_loader as fl

        # Reset module state (no reload - avoids Qt crash)
        fl._font_registered = False

        # Mock _get_fonts_dir to return non-existent path and mock registration
        with (
            patch.object(fl, "_get_fonts_dir", return_value=Path("/nonexistent/fonts")),
            patch.object(fl, "_register_font_family", return_value={}),
        ):
            # Should not raise an exception
            fl.ensure_font_registered()
            assert fl._font_registered is True

    def test_partial_font_registration(self, tmp_path: Path) -> None:
        """Should handle partial registration (one font succeeds, one fails)."""
        from unittest.mock import MagicMock, patch

        import casare_rpa.presentation.canvas.theme.font_loader as fl

        # Create a temporary fonts directory with dummy font files
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir()

        # Create dummy font files (not real fonts, but the files exist)
        (fonts_dir / "Geist-Regular.ttf").write_text("dummy")
        (fonts_dir / "Geist-Medium.ttf").write_text("dummy")
        (fonts_dir / "Geist-SemiBold.ttf").write_text("dummy")
        (fonts_dir / "GeistMono-Regular.ttf").write_text("dummy")
        (fonts_dir / "GeistMono-Medium.ttf").write_text("dummy")
        (fonts_dir / "GeistMono-SemiBold.ttf").write_text("dummy")

        # Reset module state
        fl._font_registered = False

        # Mock QFontDatabase to simulate partial success
        mock_db = MagicMock()

        # First font succeeds, second fails
        call_count = [0]

        def add_application_font_side_effect(path_str: str):
            call_count[0] += 1
            # First 3 files (Geist Sans) succeed, rest fail
            return 0 if call_count[0] <= 3 else -1

        mock_db.addApplicationFont.side_effect = add_application_font_side_effect
        mock_db.applicationFontFamilies.return_value = [GEIST_SANS_FAMILY]

        with (
            patch("casare_rpa.presentation.canvas.theme.font_loader.QFontDatabase", mock_db),
            patch.object(fl, "_get_fonts_dir", return_value=fonts_dir),
        ):
            fl.ensure_font_registered()

            # All 6 font files should be attempted
            assert call_count[0] == 6
            assert fl._font_registered is True


class TestGetRegisteredFonts:
    """Test get_registered_fonts status reporting."""

    @patch("casare_rpa.presentation.canvas.theme.font_loader._is_family_available")
    def test_get_registered_fonts_returns_status(self, mock_available: MagicMock) -> None:
        """Should return dict with font family availability."""
        # Set up mock responses
        mock_available.side_effect = lambda family: family == GEIST_SANS_FAMILY

        result = get_registered_fonts()

        assert isinstance(result, dict)
        assert GEIST_SANS_FAMILY in result
        assert GEIST_MONO_FAMILY in result
        assert result[GEIST_SANS_FAMILY] is True
        assert result[GEIST_MONO_FAMILY] is False

    @patch("casare_rpa.presentation.canvas.theme.font_loader._is_family_available")
    def test_get_registered_fonts_both_available(self, mock_available: MagicMock) -> None:
        """Should report both fonts as available when registered."""
        mock_available.return_value = True

        result = get_registered_fonts()

        assert result[GEIST_SANS_FAMILY] is True
        assert result[GEIST_MONO_FAMILY] is True

    @patch("casare_rpa.presentation.canvas.theme.font_loader._is_family_available")
    def test_get_registered_fonts_neither_available(self, mock_available: MagicMock) -> None:
        """Should report neither font as available when not registered."""
        mock_available.return_value = False

        result = get_registered_fonts()

        assert result[GEIST_SANS_FAMILY] is False
        assert result[GEIST_MONO_FAMILY] is False


class TestIsFamilyAvailable:
    """Test _is_family_available helper."""

    @patch("casare_rpa.presentation.canvas.theme.font_loader.QFontDatabase")
    def test_is_family_available_checks_database(self, mock_qdb: MagicMock) -> None:
        """Should check if family exists in QFontDatabase."""
        mock_qdb.families.return_value = ["Arial", "Times New Roman", "Geist Sans"]

        result = _is_family_available("Geist Sans")
        assert result is True

        result = _is_family_available("Geist Mono")
        assert result is False

    @patch("casare_rpa.presentation.canvas.theme.font_loader.QFontDatabase")
    def test_is_family_available_case_sensitive(self, mock_qdb: MagicMock) -> None:
        """Font family lookup should be case-sensitive."""
        mock_qdb.families.return_value = ["Geist Sans"]

        result = _is_family_available("geist sans")  # lowercase
        assert result is False

        result = _is_family_available("Geist Sans")  # exact case
        assert result is True


class TestModuleExports:
    """Test that module exports expected symbols."""

    def test_module_all_exports(self) -> None:
        """__all__ should define public API."""
        from casare_rpa.presentation.canvas.theme import font_loader

        expected = {
            "ensure_font_registered",
            "get_registered_fonts",
            "GEIST_SANS_FAMILY",
            "GEIST_MONO_FAMILY",
        }
        actual = set(font_loader.__all__)

        assert actual == expected
