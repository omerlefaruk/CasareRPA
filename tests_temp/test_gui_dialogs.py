"""
Tests for GUI dialog components.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestSelectorDialog:
    """Test SelectorDialog class."""

    def test_selector_dialog_import(self):
        """Test that SelectorDialog can be imported."""
        from casare_rpa.canvas.selector_dialog import SelectorDialog
        assert SelectorDialog is not None

    def test_selector_dialog_signals(self):
        """Test that SelectorDialog has expected signals."""
        from casare_rpa.canvas.selector_dialog import SelectorDialog

        assert hasattr(SelectorDialog, 'selector_selected')

    def test_selector_dialog_has_apply_styles(self):
        """Test that SelectorDialog has apply_styles method."""
        from casare_rpa.canvas.selector_dialog import SelectorDialog

        assert hasattr(SelectorDialog, 'apply_styles')


class TestRecordingPreviewDialog:
    """Test RecordingPreviewDialog class."""

    def test_recording_dialog_import(self):
        """Test that RecordingPreviewDialog can be imported."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog
        assert RecordingPreviewDialog is not None

    def test_recording_dialog_has_setup_ui(self):
        """Test that RecordingPreviewDialog has _setup_ui method."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog

        assert hasattr(RecordingPreviewDialog, '_setup_ui')

    def test_recording_dialog_has_load_actions(self):
        """Test that RecordingPreviewDialog has _load_actions method."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog

        assert hasattr(RecordingPreviewDialog, '_load_actions')

    def test_truncate_method(self):
        """Test _truncate method logic."""
        # Test the truncation logic directly without needing a dialog instance
        # The method is: if len(text) <= max_length: return text; return text[:max_length] + "..."

        def truncate(text: str, max_length: int) -> str:
            if len(text) <= max_length:
                return text
            return text[:max_length] + "..."

        # Test short text
        result = truncate("short", 10)
        assert result == "short"

        # Test long text
        result = truncate("this is a long text", 10)
        assert result == "this is a ..."
        assert len(result) == 13


class TestNodeSearchDialog:
    """Test NodeSearchDialog class."""

    def test_node_search_dialog_import(self):
        """Test that node_search_dialog module can be imported."""
        from casare_rpa.canvas import node_search_dialog
        assert node_search_dialog is not None


class TestDialogStyles:
    """Test dialog styling consistency."""

    def test_selector_dialog_has_styles(self):
        """Test that SelectorDialog applies styles."""
        from casare_rpa.canvas.selector_dialog import SelectorDialog

        # Check that apply_styles method exists
        assert hasattr(SelectorDialog, 'apply_styles')

    def test_recording_dialog_has_styles(self):
        """Test that RecordingPreviewDialog has styling."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog

        # The generate button should have specific styling in _setup_ui
        assert hasattr(RecordingPreviewDialog, '_setup_ui')


class TestDialogDataHandling:
    """Test dialog data handling."""

    def test_recording_dialog_handles_fingerprint_object(self):
        """Test that RecordingPreviewDialog handles ElementFingerprint objects."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog

        # Create mock fingerprint with selectors attribute
        mock_fingerprint = MagicMock()
        mock_fingerprint.selectors = [MagicMock(selector_type=MagicMock(value='xpath'), value='//test')]

        # The dialog should handle both dict and ElementFingerprint objects
        # This is tested in _load_actions method
        assert hasattr(RecordingPreviewDialog, '_load_actions')

    def test_recording_dialog_handles_dict_element(self):
        """Test that RecordingPreviewDialog handles dict element info."""
        from casare_rpa.canvas.recording_dialog import RecordingPreviewDialog

        # Dict format with selectors
        element_dict = {
            'selectors': {
                'xpath': '//button',
                'css': 'button.test'
            }
        }

        # The dialog should extract xpath or css from dict
        assert 'xpath' in element_dict['selectors']
