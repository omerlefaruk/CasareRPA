"""
Tests for ToolbarIcons icon provider.

Tests the icon mapping system for toolbar actions including:
- Standard toolbar icons (run, stop, pause)
- New performance/dashboard icons
- Trigger control icons (listen, stop_listen)
- Edge cases (unknown icons, empty names)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestToolbarIconsMapping:
    """Tests for ToolbarIcons._ICON_MAP completeness and correctness."""

    def test_performance_icons_exist(self):
        """Test that performance-related icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "performance" in ToolbarIcons._ICON_MAP
        assert "dashboard" in ToolbarIcons._ICON_MAP
        assert "metrics" in ToolbarIcons._ICON_MAP

    def test_project_settings_icons_exist(self):
        """Test that project and settings icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "project" in ToolbarIcons._ICON_MAP
        assert "credentials" in ToolbarIcons._ICON_MAP

    def test_trigger_control_icons_exist(self):
        """Test that trigger control icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "listen" in ToolbarIcons._ICON_MAP
        assert "stop_listen" in ToolbarIcons._ICON_MAP

    def test_execution_control_icons_exist(self):
        """Test that execution control icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "run" in ToolbarIcons._ICON_MAP
        assert "pause" in ToolbarIcons._ICON_MAP
        assert "stop" in ToolbarIcons._ICON_MAP
        assert "resume" in ToolbarIcons._ICON_MAP

    def test_file_operation_icons_exist(self):
        """Test that file operation icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "new" in ToolbarIcons._ICON_MAP
        assert "open" in ToolbarIcons._ICON_MAP
        assert "save" in ToolbarIcons._ICON_MAP
        assert "save_as" in ToolbarIcons._ICON_MAP

    def test_edit_operation_icons_exist(self):
        """Test that edit operation icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "undo" in ToolbarIcons._ICON_MAP
        assert "redo" in ToolbarIcons._ICON_MAP
        assert "cut" in ToolbarIcons._ICON_MAP
        assert "copy" in ToolbarIcons._ICON_MAP
        assert "paste" in ToolbarIcons._ICON_MAP
        assert "delete" in ToolbarIcons._ICON_MAP

    def test_tool_icons_exist(self):
        """Test that tool icons are in the icon map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert "record" in ToolbarIcons._ICON_MAP
        assert "pick_selector" in ToolbarIcons._ICON_MAP

    def test_icon_map_values_are_valid_qt_pixmap_names(self):
        """Test that all icon map values are valid Qt StandardPixmap names."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        # All values should start with SP_ (Qt StandardPixmap convention)
        for name, pixmap_name in ToolbarIcons._ICON_MAP.items():
            assert pixmap_name.startswith(
                "SP_"
            ), f"Icon '{name}' has invalid pixmap name: {pixmap_name}"


class TestToolbarIconsGetIcon:
    """Tests for ToolbarIcons.get_icon method."""

    def test_get_icon_returns_qicon_for_known_name(self):
        """Test that get_icon returns QIcon for known icon names."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        # Set up mock style
        mock_style = Mock()
        mock_icon = Mock()
        mock_style.standardIcon.return_value = mock_icon

        # Reset cached style to use our mock
        ToolbarIcons._style = mock_style

        with patch("PySide6.QtWidgets.QStyle") as mock_qstyle:
            # Set up StandardPixmap enum
            mock_qstyle.StandardPixmap.SP_MediaPlay = 1

            result = ToolbarIcons.get_icon("run")

            # Should call standardIcon
            mock_style.standardIcon.assert_called_once()

    def test_get_icon_returns_empty_qicon_for_unknown_name(self):
        """Test that get_icon returns empty QIcon for unknown names."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        # Set up mock style
        mock_style = Mock()
        ToolbarIcons._style = mock_style

        # Patch at PySide6 level since it's imported inside the method
        with patch("PySide6.QtGui.QIcon") as mock_icon_class:
            result = ToolbarIcons.get_icon("nonexistent_icon")

            # Should return empty QIcon (called with no args)
            mock_icon_class.assert_called_once_with()

    def test_get_toolbar_icon_convenience_function(self):
        """Test the convenience function get_toolbar_icon."""
        from casare_rpa.presentation.canvas.ui.icons import (
            get_toolbar_icon,
            ToolbarIcons,
        )

        # Set up mock style
        mock_style = Mock()
        mock_style.standardIcon.return_value = Mock()
        ToolbarIcons._style = mock_style

        # Patch at PySide6 level since it's imported inside the method
        with patch("PySide6.QtGui.QIcon"):
            with patch("PySide6.QtWidgets.QStyle"):
                # Should not raise
                get_toolbar_icon("run")
                get_toolbar_icon("performance")
                get_toolbar_icon("unknown")


class TestToolbarIconsNewMappings:
    """Specific tests for the newly added icon mappings."""

    def test_performance_uses_computer_icon(self):
        """Test that performance icon uses SP_ComputerIcon."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["performance"] == "SP_ComputerIcon"

    def test_dashboard_uses_computer_icon(self):
        """Test that dashboard icon uses SP_ComputerIcon."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["dashboard"] == "SP_ComputerIcon"

    def test_metrics_uses_drive_hd_icon(self):
        """Test that metrics icon uses SP_DriveHDIcon."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["metrics"] == "SP_DriveHDIcon"

    def test_project_uses_dir_icon(self):
        """Test that project icon uses SP_DirIcon."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["project"] == "SP_DirIcon"

    def test_credentials_uses_dialog_apply_button(self):
        """Test that credentials icon uses SP_DialogApplyButton."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["credentials"] == "SP_DialogApplyButton"

    def test_listen_uses_media_play(self):
        """Test that listen icon uses SP_MediaPlay."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["listen"] == "SP_MediaPlay"

    def test_stop_listen_uses_media_stop(self):
        """Test that stop_listen icon uses SP_MediaStop."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        assert ToolbarIcons._ICON_MAP["stop_listen"] == "SP_MediaStop"


class TestGetAllIcons:
    """Tests for ToolbarIcons.get_all_icons method."""

    def test_get_all_icons_returns_all_mapped_icons(self):
        """Test that get_all_icons returns all icons in the map."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        with patch.object(ToolbarIcons, "get_icon") as mock_get_icon:
            mock_get_icon.return_value = Mock()

            result = ToolbarIcons.get_all_icons()

            # Should return dict with all mapped names
            assert len(result) == len(ToolbarIcons._ICON_MAP)

            # Should call get_icon for each name
            assert mock_get_icon.call_count == len(ToolbarIcons._ICON_MAP)

    def test_get_all_icons_includes_new_icons(self):
        """Test that get_all_icons includes newly added icons."""
        from casare_rpa.presentation.canvas.ui.icons import ToolbarIcons

        with patch.object(ToolbarIcons, "get_icon") as mock_get_icon:
            mock_get_icon.return_value = Mock()

            result = ToolbarIcons.get_all_icons()

            # Check new icons are included
            assert "performance" in result
            assert "dashboard" in result
            assert "metrics" in result
            assert "project" in result
            assert "credentials" in result
            assert "listen" in result
            assert "stop_listen" in result
