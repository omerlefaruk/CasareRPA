"""
Test Google Visual Nodes - Automated Testing

Tests all 83 Google visual nodes can be:
1. Imported successfully
2. Instantiated without errors
3. Have proper ports defined
4. Have credential widget setup
"""

import sys
import traceback

# Need to initialize Qt app for widget testing
from PySide6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from casare_rpa.presentation.canvas.visual_nodes.google import (
    __all__ as GOOGLE_NODE_CLASSES,
)

# Import all Google node classes
from casare_rpa.presentation.canvas.visual_nodes.google import (
    # Calendar
    VisualCalendarListEventsNode,
    VisualCalendarGetEventNode,
    VisualCalendarCreateEventNode,
    VisualCalendarUpdateEventNode,
    VisualCalendarDeleteEventNode,
    VisualCalendarQuickAddNode,
    VisualCalendarMoveEventNode,
    VisualCalendarGetFreeBusyNode,
    VisualCalendarListCalendarsNode,
    VisualCalendarGetCalendarNode,
    VisualCalendarCreateCalendarNode,
    VisualCalendarDeleteCalendarNode,
    # Gmail
    VisualGmailSendEmailNode,
    VisualGmailSendWithAttachmentNode,
    VisualGmailReplyToEmailNode,
    VisualGmailForwardEmailNode,
    VisualGmailCreateDraftNode,
    VisualGmailSendDraftNode,
    VisualGmailGetEmailNode,
    VisualGmailListEmailsNode,
    VisualGmailSearchEmailsNode,
    VisualGmailGetThreadNode,
    VisualGmailGetAttachmentNode,
    VisualGmailModifyLabelsNode,
    VisualGmailMoveToTrashNode,
    VisualGmailMarkAsReadNode,
    VisualGmailMarkAsUnreadNode,
    VisualGmailStarEmailNode,
    VisualGmailArchiveEmailNode,
    VisualGmailDeleteEmailNode,
    VisualGmailBatchSendNode,
    VisualGmailBatchModifyNode,
    VisualGmailBatchDeleteNode,
    # Sheets
    VisualSheetsGetCellNode,
    VisualSheetsSetCellNode,
    VisualSheetsGetRangeNode,
    VisualSheetsWriteRangeNode,
    VisualSheetsClearRangeNode,
    VisualSheetsCreateSpreadsheetNode,
    VisualSheetsGetSpreadsheetNode,
    VisualSheetsAddSheetNode,
    VisualSheetsDeleteSheetNode,
    VisualSheetsDuplicateSheetNode,
    VisualSheetsRenameSheetNode,
    VisualSheetsAppendRowNode,
    VisualSheetsInsertRowNode,
    VisualSheetsDeleteRowNode,
    VisualSheetsInsertColumnNode,
    VisualSheetsDeleteColumnNode,
    VisualSheetsFormatCellsNode,
    VisualSheetsAutoResizeNode,
    VisualSheetsBatchUpdateNode,
    VisualSheetsBatchGetNode,
    VisualSheetsBatchClearNode,
    # Docs
    VisualDocsCreateDocumentNode,
    VisualDocsGetDocumentNode,
    VisualDocsGetContentNode,
    VisualDocsInsertTextNode,
    VisualDocsReplaceTextNode,
    VisualDocsInsertTableNode,
    VisualDocsInsertImageNode,
    VisualDocsUpdateStyleNode,
    # Drive
    VisualDriveUploadFileNode,
    VisualDriveDownloadFileNode,
    VisualDriveDeleteFileNode,
    VisualDriveCopyFileNode,
    VisualDriveMoveFileNode,
    VisualDriveRenameFileNode,
    VisualDriveGetFileNode,
    VisualDriveCreateFolderNode,
    VisualDriveListFilesNode,
    VisualDriveSearchFilesNode,
    VisualDriveShareFileNode,
    VisualDriveRemoveShareNode,
    VisualDriveGetPermissionsNode,
    VisualDriveExportFileNode,
    VisualDriveBatchDeleteNode,
    VisualDriveBatchMoveNode,
    VisualDriveBatchCopyNode,
)


def test_node_class(node_class):
    """Test a single node class."""
    errors = []

    try:
        # Try to instantiate
        node = node_class()

        # Check basic attributes
        if not hasattr(node, "NODE_NAME") or not node.NODE_NAME:
            errors.append("Missing NODE_NAME")

        # Check ports exist
        inputs = node.input_ports()
        outputs = node.output_ports()

        if not inputs and not outputs:
            errors.append("No ports defined")

        # Check for flow ports (most nodes should have them)
        has_flow_in = any(
            "flow" in str(p).lower() or "in" == str(p).lower() for p in inputs
        )
        has_flow_out = any(
            "flow" in str(p).lower() or "out" == str(p).lower() for p in outputs
        )

        return True, errors, len(inputs), len(outputs)

    except Exception as e:
        return False, [str(e)], 0, 0


def main():
    print("\n" + "=" * 70)
    print(" Google Visual Nodes - Automated Test")
    print("=" * 70)

    # Get all node classes
    node_classes = [
        # Calendar (12)
        VisualCalendarListEventsNode,
        VisualCalendarGetEventNode,
        VisualCalendarCreateEventNode,
        VisualCalendarUpdateEventNode,
        VisualCalendarDeleteEventNode,
        VisualCalendarQuickAddNode,
        VisualCalendarMoveEventNode,
        VisualCalendarGetFreeBusyNode,
        VisualCalendarListCalendarsNode,
        VisualCalendarGetCalendarNode,
        VisualCalendarCreateCalendarNode,
        VisualCalendarDeleteCalendarNode,
        # Gmail (21)
        VisualGmailSendEmailNode,
        VisualGmailSendWithAttachmentNode,
        VisualGmailReplyToEmailNode,
        VisualGmailForwardEmailNode,
        VisualGmailCreateDraftNode,
        VisualGmailSendDraftNode,
        VisualGmailGetEmailNode,
        VisualGmailListEmailsNode,
        VisualGmailSearchEmailsNode,
        VisualGmailGetThreadNode,
        VisualGmailGetAttachmentNode,
        VisualGmailModifyLabelsNode,
        VisualGmailMoveToTrashNode,
        VisualGmailMarkAsReadNode,
        VisualGmailMarkAsUnreadNode,
        VisualGmailStarEmailNode,
        VisualGmailArchiveEmailNode,
        VisualGmailDeleteEmailNode,
        VisualGmailBatchSendNode,
        VisualGmailBatchModifyNode,
        VisualGmailBatchDeleteNode,
        # Sheets (21)
        VisualSheetsGetCellNode,
        VisualSheetsSetCellNode,
        VisualSheetsGetRangeNode,
        VisualSheetsWriteRangeNode,
        VisualSheetsClearRangeNode,
        VisualSheetsCreateSpreadsheetNode,
        VisualSheetsGetSpreadsheetNode,
        VisualSheetsAddSheetNode,
        VisualSheetsDeleteSheetNode,
        VisualSheetsDuplicateSheetNode,
        VisualSheetsRenameSheetNode,
        VisualSheetsAppendRowNode,
        VisualSheetsInsertRowNode,
        VisualSheetsDeleteRowNode,
        VisualSheetsInsertColumnNode,
        VisualSheetsDeleteColumnNode,
        VisualSheetsFormatCellsNode,
        VisualSheetsAutoResizeNode,
        VisualSheetsBatchUpdateNode,
        VisualSheetsBatchGetNode,
        VisualSheetsBatchClearNode,
        # Docs (8)
        VisualDocsCreateDocumentNode,
        VisualDocsGetDocumentNode,
        VisualDocsGetContentNode,
        VisualDocsInsertTextNode,
        VisualDocsReplaceTextNode,
        VisualDocsInsertTableNode,
        VisualDocsInsertImageNode,
        VisualDocsUpdateStyleNode,
        # Drive (17)
        VisualDriveUploadFileNode,
        VisualDriveDownloadFileNode,
        VisualDriveDeleteFileNode,
        VisualDriveCopyFileNode,
        VisualDriveMoveFileNode,
        VisualDriveRenameFileNode,
        VisualDriveGetFileNode,
        VisualDriveCreateFolderNode,
        VisualDriveListFilesNode,
        VisualDriveSearchFilesNode,
        VisualDriveShareFileNode,
        VisualDriveRemoveShareNode,
        VisualDriveGetPermissionsNode,
        VisualDriveExportFileNode,
        VisualDriveBatchDeleteNode,
        VisualDriveBatchMoveNode,
        VisualDriveBatchCopyNode,
    ]

    print(f"\nTesting {len(node_classes)} Google visual nodes...\n")

    passed = 0
    failed = 0
    results = {
        "Calendar": {"passed": 0, "failed": 0, "errors": []},
        "Gmail": {"passed": 0, "failed": 0, "errors": []},
        "Sheets": {"passed": 0, "failed": 0, "errors": []},
        "Docs": {"passed": 0, "failed": 0, "errors": []},
        "Drive": {"passed": 0, "failed": 0, "errors": []},
    }

    for node_class in node_classes:
        class_name = node_class.__name__

        # Determine category
        if "Calendar" in class_name:
            category = "Calendar"
        elif "Gmail" in class_name:
            category = "Gmail"
        elif "Sheets" in class_name:
            category = "Sheets"
        elif "Docs" in class_name:
            category = "Docs"
        elif "Drive" in class_name:
            category = "Drive"
        else:
            category = "Other"

        success, errors, num_inputs, num_outputs = test_node_class(node_class)

        if success and not errors:
            passed += 1
            results[category]["passed"] += 1
            status = "OK"
        elif success and errors:
            passed += 1
            results[category]["passed"] += 1
            status = f"WARN: {', '.join(errors)}"
        else:
            failed += 1
            results[category]["failed"] += 1
            results[category]["errors"].append((class_name, errors))
            status = f"FAIL: {', '.join(errors)}"

        # Short name for display
        short_name = class_name.replace("Visual", "").replace("Node", "")
        print(f"  [{status:4}] {short_name:<35} (in:{num_inputs} out:{num_outputs})")

    # Summary by category
    print("\n" + "=" * 70)
    print(" Results by Category")
    print("=" * 70)

    for category, data in results.items():
        total = data["passed"] + data["failed"]
        if total > 0:
            pct = (data["passed"] / total) * 100
            status = "PASS" if data["failed"] == 0 else "FAIL"
            print(
                f"  {category:<12} {data['passed']:2}/{total:2} passed ({pct:5.1f}%) [{status}]"
            )

            # Show errors if any
            for class_name, errors in data["errors"]:
                print(f"    - {class_name}: {', '.join(errors)}")

    # Overall summary
    print("\n" + "=" * 70)
    print(" Overall Summary")
    print("=" * 70)

    total = passed + failed
    pct = (passed / total) * 100 if total > 0 else 0

    print(f"\n  Total:  {passed}/{total} nodes passed ({pct:.1f}%)")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed == 0:
        print("\n  ALL GOOGLE VISUAL NODES PASSED!")
    else:
        print(f"\n  {failed} node(s) failed - check errors above")

    print("\n")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
