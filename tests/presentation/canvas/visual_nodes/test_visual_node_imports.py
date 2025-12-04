"""
Tests for visual node module imports and instantiation.

These tests verify that the visual node fixes for the "property already exists"
NodePropertyError have been successfully applied to all modified files.

Test Categories:
1. Import Tests - Verify all modules import without errors
2. Class Discovery - Check visual node classes are exported correctly
3. No Duplicate Widget Pattern Detection - Verify no duplicate widget creation

Files Modified:
- data_operations/nodes.py
- error_handling/nodes.py
- utility/nodes.py
- scripts/nodes.py
- google/sheets_nodes.py
- google/docs_nodes.py
- google/drive_nodes.py
- google/gmail_nodes.py
"""

import pytest
import importlib
import inspect
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# =============================================================================
# Import Tests
# =============================================================================


class TestVisualNodeModuleImports:
    """Test that all modified visual node modules import successfully."""

    def test_import_data_operations_nodes(self):
        """Verify data_operations/nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.data_operations import (
                nodes,
            )

            assert nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import data_operations nodes: {e}")

    def test_import_error_handling_nodes(self):
        """Verify error_handling/nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.error_handling import nodes

            assert nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import error_handling nodes: {e}")

    def test_import_utility_nodes(self):
        """Verify utility/nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.utility import nodes

            assert nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import utility nodes: {e}")

    def test_import_scripts_nodes(self):
        """Verify scripts/nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.scripts import nodes

            assert nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import scripts nodes: {e}")

    def test_import_google_sheets_nodes(self):
        """Verify google/sheets_nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.google import sheets_nodes

            assert sheets_nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google sheets nodes: {e}")

    def test_import_google_docs_nodes(self):
        """Verify google/docs_nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.google import docs_nodes

            assert docs_nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google docs nodes: {e}")

    def test_import_google_drive_nodes(self):
        """Verify google/drive_nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.google import drive_nodes

            assert drive_nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google drive nodes: {e}")

    def test_import_google_gmail_nodes(self):
        """Verify google/gmail_nodes.py imports without errors."""
        try:
            from casare_rpa.presentation.canvas.visual_nodes.google import gmail_nodes

            assert gmail_nodes is not None
        except ImportError as e:
            pytest.fail(f"Failed to import google gmail nodes: {e}")


# =============================================================================
# Class Discovery Tests
# =============================================================================


class TestVisualNodeClassDiscovery:
    """Test that visual node classes are properly defined and exported."""

    def test_data_operations_visual_classes_exist(self):
        """Verify data_operations has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import nodes

        expected_classes = [
            "VisualConcatenateNode",
            "VisualFormatStringNode",
            "VisualRegexMatchNode",
            "VisualRegexReplaceNode",
            "VisualMathOperationNode",
            "VisualComparisonNode",
            "VisualCreateListNode",
            "VisualListGetItemNode",
            "VisualJsonParseNode",
            "VisualGetPropertyNode",
            "VisualListLengthNode",
            "VisualListAppendNode",
            "VisualListContainsNode",
            "VisualListSliceNode",
            "VisualListJoinNode",
            "VisualListSortNode",
            "VisualListReverseNode",
            "VisualListUniqueNode",
            "VisualListFilterNode",
            "VisualListMapNode",
            "VisualListReduceNode",
            "VisualListFlattenNode",
            "VisualDictGetNode",
            "VisualDictSetNode",
            "VisualDictRemoveNode",
            "VisualDictMergeNode",
            "VisualDictKeysNode",
            "VisualDictValuesNode",
            "VisualDictHasKeyNode",
            "VisualCreateDictNode",
            "VisualDictToJsonNode",
            "VisualDictItemsNode",
        ]

        for class_name in expected_classes:
            assert hasattr(nodes, class_name), f"Missing class: {class_name}"

    def test_error_handling_visual_classes_exist(self):
        """Verify error_handling has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.error_handling import nodes

        expected_classes = [
            "VisualRetryNode",
            "VisualRetrySuccessNode",
            "VisualRetryFailNode",
            "VisualThrowErrorNode",
            "VisualWebhookNotifyNode",
            "VisualOnErrorNode",
            "VisualErrorRecoveryNode",
            "VisualLogErrorNode",
            "VisualAssertNode",
        ]

        for class_name in expected_classes:
            assert hasattr(nodes, class_name), f"Missing class: {class_name}"

    def test_utility_visual_classes_exist(self):
        """Verify utility has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.utility import nodes

        expected_classes = [
            "VisualRandomNumberNode",
            "VisualRandomChoiceNode",
            "VisualRandomStringNode",
            "VisualRandomUUIDNode",
            "VisualShuffleListNode",
            "VisualGetCurrentDateTimeNode",
            "VisualFormatDateTimeNode",
            "VisualParseDateTimeNode",
            "VisualDateTimeAddNode",
            "VisualDateTimeDiffNode",
            "VisualDateTimeCompareNode",
            "VisualGetTimestampNode",
            "VisualTextSplitNode",
            "VisualTextReplaceNode",
            "VisualTextTrimNode",
            "VisualTextCaseNode",
            "VisualTextPadNode",
            "VisualTextSubstringNode",
            "VisualTextContainsNode",
            "VisualTextStartsWithNode",
            "VisualTextEndsWithNode",
            "VisualTextLinesNode",
            "VisualTextReverseNode",
            "VisualTextCountNode",
            "VisualTextJoinNode",
            "VisualTextExtractNode",
        ]

        for class_name in expected_classes:
            assert hasattr(nodes, class_name), f"Missing class: {class_name}"

    def test_scripts_visual_classes_exist(self):
        """Verify scripts has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.scripts import nodes

        expected_classes = [
            "VisualRunPythonScriptNode",
            "VisualRunPythonFileNode",
            "VisualEvalExpressionNode",
            "VisualRunBatchScriptNode",
            "VisualRunJavaScriptNode",
        ]

        for class_name in expected_classes:
            assert hasattr(nodes, class_name), f"Missing class: {class_name}"

    def test_google_sheets_visual_classes_exist(self):
        """Verify google/sheets_nodes has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.google import sheets_nodes

        expected_classes = [
            "VisualSheetsGetCellNode",
            "VisualSheetsSetCellNode",
            "VisualSheetsGetRangeNode",
            "VisualSheetsWriteRangeNode",
            "VisualSheetsClearRangeNode",
            "VisualSheetsCreateSpreadsheetNode",
            "VisualSheetsGetSpreadsheetNode",
            "VisualSheetsAddSheetNode",
            "VisualSheetsDeleteSheetNode",
            "VisualSheetsDuplicateSheetNode",
            "VisualSheetsRenameSheetNode",
            "VisualSheetsAppendRowNode",
            "VisualSheetsInsertRowNode",
            "VisualSheetsDeleteRowNode",
            "VisualSheetsInsertColumnNode",
            "VisualSheetsDeleteColumnNode",
            "VisualSheetsFormatCellsNode",
            "VisualSheetsAutoResizeNode",
            "VisualSheetsBatchUpdateNode",
            "VisualSheetsBatchGetNode",
            "VisualSheetsBatchClearNode",
        ]

        for class_name in expected_classes:
            assert hasattr(sheets_nodes, class_name), f"Missing class: {class_name}"

    def test_google_docs_visual_classes_exist(self):
        """Verify google/docs_nodes has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.google import docs_nodes

        expected_classes = [
            "VisualDocsCreateDocumentNode",
            "VisualDocsGetDocumentNode",
            "VisualDocsGetContentNode",
            "VisualDocsInsertTextNode",
            "VisualDocsDeleteContentNode",
            "VisualDocsReplaceTextNode",
            "VisualDocsInsertTableNode",
            "VisualDocsInsertImageNode",
            "VisualDocsUpdateStyleNode",
            "VisualDocsBatchUpdateNode",
        ]

        for class_name in expected_classes:
            assert hasattr(docs_nodes, class_name), f"Missing class: {class_name}"

    def test_google_drive_visual_classes_exist(self):
        """Verify google/drive_nodes has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.google import drive_nodes

        expected_classes = [
            "VisualDriveUploadFileNode",
            "VisualDriveDownloadFileNode",
            "VisualDriveDeleteFileNode",
            "VisualDriveCopyFileNode",
            "VisualDriveMoveFileNode",
            "VisualDriveRenameFileNode",
            "VisualDriveGetFileNode",
            "VisualDriveCreateFolderNode",
            "VisualDriveListFilesNode",
            "VisualDriveSearchFilesNode",
            "VisualDriveShareFileNode",
            "VisualDriveRemovePermissionNode",
            "VisualDriveGetPermissionsNode",
            "VisualDriveExportFileNode",
            "VisualDriveBatchDeleteNode",
            "VisualDriveBatchMoveNode",
            "VisualDriveBatchCopyNode",
        ]

        for class_name in expected_classes:
            assert hasattr(drive_nodes, class_name), f"Missing class: {class_name}"

    def test_google_gmail_visual_classes_exist(self):
        """Verify google/gmail_nodes has expected visual node classes."""
        from casare_rpa.presentation.canvas.visual_nodes.google import gmail_nodes

        expected_classes = [
            "VisualGmailSendEmailNode",
            "VisualGmailSendWithAttachmentNode",
            "VisualGmailReplyToEmailNode",
            "VisualGmailForwardEmailNode",
            "VisualGmailCreateDraftNode",
            "VisualGmailSendDraftNode",
            "VisualGmailGetEmailNode",
            "VisualGmailListEmailsNode",
            "VisualGmailSearchEmailsNode",
            "VisualGmailGetThreadNode",
            "VisualGmailGetAttachmentNode",
            "VisualGmailModifyLabelsNode",
            "VisualGmailMoveToTrashNode",
            "VisualGmailMarkAsReadNode",
            "VisualGmailMarkAsUnreadNode",
            "VisualGmailStarEmailNode",
            "VisualGmailArchiveEmailNode",
            "VisualGmailDeleteEmailNode",
            "VisualGmailBatchSendNode",
            "VisualGmailBatchModifyNode",
            "VisualGmailBatchDeleteNode",
        ]

        for class_name in expected_classes:
            assert hasattr(gmail_nodes, class_name), f"Missing class: {class_name}"


# =============================================================================
# Node Attribute Validation Tests
# =============================================================================


class TestVisualNodeAttributes:
    """Test that visual node classes have required attributes."""

    def _get_visual_node_classes(self, module):
        """Get all VisualNode subclasses from a module."""
        from casare_rpa.presentation.canvas.visual_nodes.base_visual_node import (
            VisualNode,
        )

        classes = []
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if name.startswith("Visual") and name != "VisualNode":
                # Check if it's a VisualNode subclass (may fail due to import structure)
                try:
                    if issubclass(obj, VisualNode):
                        classes.append((name, obj))
                except TypeError:
                    # Not a class or inheritance check failed
                    pass
                # Also include if it looks like a visual node
                if hasattr(obj, "__identifier__") and hasattr(obj, "NODE_NAME"):
                    if (name, obj) not in classes:
                        classes.append((name, obj))
        return classes

    def test_data_operations_nodes_have_required_attributes(self):
        """Verify data_operations visual nodes have __identifier__ and NODE_NAME."""
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import nodes

        visual_classes = self._get_visual_node_classes(nodes)
        assert len(visual_classes) > 0, "No visual node classes found"

        for name, cls in visual_classes:
            assert hasattr(cls, "__identifier__"), f"{name} missing __identifier__"
            assert hasattr(cls, "NODE_NAME"), f"{name} missing NODE_NAME"
            assert hasattr(cls, "NODE_CATEGORY"), f"{name} missing NODE_CATEGORY"
            assert hasattr(cls, "setup_ports"), f"{name} missing setup_ports method"

    def test_error_handling_nodes_have_required_attributes(self):
        """Verify error_handling visual nodes have __identifier__ and NODE_NAME."""
        from casare_rpa.presentation.canvas.visual_nodes.error_handling import nodes

        visual_classes = self._get_visual_node_classes(nodes)
        assert len(visual_classes) > 0, "No visual node classes found"

        for name, cls in visual_classes:
            assert hasattr(cls, "__identifier__"), f"{name} missing __identifier__"
            assert hasattr(cls, "NODE_NAME"), f"{name} missing NODE_NAME"

    def test_utility_nodes_have_required_attributes(self):
        """Verify utility visual nodes have __identifier__ and NODE_NAME."""
        from casare_rpa.presentation.canvas.visual_nodes.utility import nodes

        visual_classes = self._get_visual_node_classes(nodes)
        assert len(visual_classes) > 0, "No visual node classes found"

        for name, cls in visual_classes:
            assert hasattr(cls, "__identifier__"), f"{name} missing __identifier__"
            assert hasattr(cls, "NODE_NAME"), f"{name} missing NODE_NAME"

    def test_scripts_nodes_have_required_attributes(self):
        """Verify scripts visual nodes have __identifier__ and NODE_NAME."""
        from casare_rpa.presentation.canvas.visual_nodes.scripts import nodes

        visual_classes = self._get_visual_node_classes(nodes)
        assert len(visual_classes) > 0, "No visual node classes found"

        for name, cls in visual_classes:
            assert hasattr(cls, "__identifier__"), f"{name} missing __identifier__"
            assert hasattr(cls, "NODE_NAME"), f"{name} missing NODE_NAME"

    def test_google_sheets_nodes_have_required_attributes(self):
        """Verify google sheets visual nodes have __identifier__ and NODE_NAME."""
        from casare_rpa.presentation.canvas.visual_nodes.google import sheets_nodes

        visual_classes = self._get_visual_node_classes(sheets_nodes)
        assert len(visual_classes) > 0, "No visual node classes found"

        for name, cls in visual_classes:
            assert hasattr(cls, "__identifier__"), f"{name} missing __identifier__"
            assert hasattr(cls, "NODE_NAME"), f"{name} missing NODE_NAME"
            # Google nodes should have CASARE_NODE_CLASS
            assert hasattr(
                cls, "CASARE_NODE_CLASS"
            ), f"{name} missing CASARE_NODE_CLASS"


# =============================================================================
# Duplicate Widget Pattern Detection Tests
# =============================================================================


class TestNoDuplicateWidgetPatterns:
    """
    Test that visual nodes don't have duplicate widget creation patterns.

    The fix removed manual widget creation in __init__ for properties that are
    auto-generated from @node_schema. This test ensures no regression.
    """

    def _check_init_source_for_duplicate_widgets(self, module, excluded_classes=None):
        """
        Analyze __init__ methods to detect potential duplicate widget patterns.

        Looks for visual nodes that:
        1. Override __init__
        2. Call self.add_text_input/add_combo_menu/add_checkbox
        3. Also have a get_node_class() that references a logic node with @node_schema

        Returns list of (class_name, potential_issue) tuples.
        """
        if excluded_classes is None:
            excluded_classes = set()

        potential_issues = []

        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not name.startswith("Visual") or name in excluded_classes:
                continue

            # Check if it has __init__
            if not hasattr(obj, "__init__"):
                continue

            try:
                source = inspect.getsource(obj.__init__)
            except (OSError, TypeError):
                continue

            # Check for widget creation patterns in __init__
            widget_patterns = [
                "add_text_input",
                "add_combo_menu",
                "add_checkbox",
                "add_int_input",
                "add_float_input",
            ]

            found_widgets = []
            for pattern in widget_patterns:
                if f"self.{pattern}" in source:
                    found_widgets.append(pattern)

            # If widgets are created AND there's get_node_class, flag for review
            if found_widgets:
                has_get_node_class = hasattr(obj, "get_node_class")
                if has_get_node_class:
                    # This might be intentional (widgets not in schema)
                    # Just note it for review
                    potential_issues.append(
                        (name, f"Manual widgets in __init__: {found_widgets}")
                    )

        return potential_issues

    def test_data_operations_no_conflicting_init_widgets(self):
        """
        Verify data_operations nodes don't have conflicting widget definitions.

        After the fix, nodes should not manually create widgets that would
        conflict with auto-generated widgets from @node_schema.
        """
        from casare_rpa.presentation.canvas.visual_nodes.data_operations import nodes

        # These nodes intentionally have manual widgets that are NOT in schema
        # (they define widgets for properties that are port inputs, not config)
        known_manual_widgets = {
            "VisualListSliceNode",  # start, end, step are ports, widgets just for UI hints
            "VisualDictGetNode",  # key, default are ports
            "VisualDictSetNode",  # key is a port
            "VisualDictRemoveNode",  # key is a port
            "VisualDictHasKeyNode",  # key is a port
        }

        issues = self._check_init_source_for_duplicate_widgets(
            nodes, known_manual_widgets
        )

        # Filter out known intentional cases
        unexpected_issues = [
            (name, issue) for name, issue in issues if name not in known_manual_widgets
        ]

        if unexpected_issues:
            issue_str = "\n".join(
                f"  - {name}: {issue}" for name, issue in unexpected_issues
            )
            pytest.fail(f"Potential duplicate widget patterns found:\n{issue_str}")

    def test_utility_no_conflicting_init_widgets(self):
        """Verify utility nodes don't have unexpected conflicting widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.utility import nodes

        # Utility nodes intentionally have manual widgets for UI hints
        # These properties are port inputs, not schema properties
        known_manual_widgets = {
            "VisualRandomNumberNode",  # min_value, max_value are ports
            "VisualRandomStringNode",  # length is a port
            "VisualRandomUUIDNode",  # format is manual widget
            "VisualGetCurrentDateTimeNode",  # format is manual widget
            "VisualFormatDateTimeNode",  # format is manual widget
            "VisualParseDateTimeNode",  # format is manual widget
            "VisualGetTimestampNode",  # milliseconds checkbox
            "VisualTextSplitNode",  # max_split is manual widget
            "VisualTextReplaceNode",  # use_regex checkbox
            "VisualTextTrimNode",  # mode combo
            "VisualTextCaseNode",  # case combo
            "VisualTextPadNode",  # mode, fill_char
            "VisualTextContainsNode",  # case_sensitive
            "VisualTextStartsWithNode",  # case_sensitive
            "VisualTextEndsWithNode",  # case_sensitive
            "VisualTextLinesNode",  # mode, keep_ends
            "VisualTextCountNode",  # mode
            "VisualTextExtractNode",  # all_matches
        }

        issues = self._check_init_source_for_duplicate_widgets(
            nodes, known_manual_widgets
        )

        unexpected_issues = [
            (name, issue) for name, issue in issues if name not in known_manual_widgets
        ]

        if unexpected_issues:
            issue_str = "\n".join(
                f"  - {name}: {issue}" for name, issue in unexpected_issues
            )
            pytest.fail(f"Potential duplicate widget patterns found:\n{issue_str}")

    def test_google_sheets_no_init_widgets(self):
        """
        Verify Google Sheets nodes have no manual __init__ widgets.

        All Google Sheets visual nodes should rely entirely on auto-generated
        widgets from @node_schema on the logic nodes.
        """
        from casare_rpa.presentation.canvas.visual_nodes.google import sheets_nodes

        issues = self._check_init_source_for_duplicate_widgets(sheets_nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(
                f"Google Sheets nodes should not have manual widgets:\n{issue_str}"
            )

    def test_google_docs_no_init_widgets(self):
        """Verify Google Docs nodes have no manual __init__ widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.google import docs_nodes

        issues = self._check_init_source_for_duplicate_widgets(docs_nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(
                f"Google Docs nodes should not have manual widgets:\n{issue_str}"
            )

    def test_google_drive_no_init_widgets(self):
        """Verify Google Drive nodes have no manual __init__ widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.google import drive_nodes

        issues = self._check_init_source_for_duplicate_widgets(drive_nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(
                f"Google Drive nodes should not have manual widgets:\n{issue_str}"
            )

    def test_google_gmail_no_init_widgets(self):
        """Verify Google Gmail nodes have no manual __init__ widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.google import gmail_nodes

        issues = self._check_init_source_for_duplicate_widgets(gmail_nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(
                f"Google Gmail nodes should not have manual widgets:\n{issue_str}"
            )

    def test_error_handling_no_unexpected_init_widgets(self):
        """Verify error_handling nodes don't have unexpected manual widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.error_handling import nodes

        issues = self._check_init_source_for_duplicate_widgets(nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(f"Error handling nodes with manual widgets:\n{issue_str}")

    def test_scripts_no_unexpected_init_widgets(self):
        """Verify scripts nodes don't have unexpected manual widgets."""
        from casare_rpa.presentation.canvas.visual_nodes.scripts import nodes

        issues = self._check_init_source_for_duplicate_widgets(nodes)

        if issues:
            issue_str = "\n".join(f"  - {name}: {issue}" for name, issue in issues)
            pytest.fail(f"Script nodes with manual widgets:\n{issue_str}")


# =============================================================================
# Module Structure Tests
# =============================================================================


class TestModuleStructure:
    """Test module structure and organization."""

    def test_all_modified_modules_have_base_visual_node_import(self):
        """Verify all modified modules import VisualNode from base_visual_node."""
        modules_to_check = [
            "casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.utility.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.scripts.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.docs_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes",
        ]

        for module_path in modules_to_check:
            module = importlib.import_module(module_path)

            # Check that VisualNode is used (imported)
            try:
                source = inspect.getsource(module)
                assert "VisualNode" in source, f"{module_path} does not use VisualNode"
            except OSError:
                # Can't get source, skip
                pass

    def test_data_type_enum_imported(self):
        """Verify DataType is imported for port type definitions."""
        modules_to_check = [
            "casare_rpa.presentation.canvas.visual_nodes.data_operations.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.error_handling.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.utility.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.scripts.nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.sheets_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.docs_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.drive_nodes",
            "casare_rpa.presentation.canvas.visual_nodes.google.gmail_nodes",
        ]

        for module_path in modules_to_check:
            module = importlib.import_module(module_path)

            try:
                source = inspect.getsource(module)
                assert "DataType" in source, f"{module_path} does not import DataType"
            except OSError:
                pass
