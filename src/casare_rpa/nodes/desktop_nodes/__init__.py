"""
Desktop Automation Nodes for CasareRPA

This package provides nodes for Windows desktop automation:
- Application management (launch, close, activate)
- Window management (resize, move, maximize, minimize)
- Element interaction (find, click, type)
- Advanced interactions (dropdowns, checkboxes, tabs)
- Mouse and keyboard control
- Wait and verification
- Screenshot and OCR
- Office automation (Excel, Word, Outlook)
"""

# Base classes and utilities
# Application Nodes
from casare_rpa.nodes.desktop_nodes.application_nodes import (
    ActivateWindowNode,
    CloseApplicationNode,
    GetWindowListNode,
    LaunchApplicationNode,
)
from casare_rpa.nodes.desktop_nodes.desktop_base import (
    DesktopNodeBase,
    ElementInteractionMixin,
    WindowOperationMixin,
)

# Element Nodes
from casare_rpa.nodes.desktop_nodes.element_nodes import (
    ClickElementNode,
    FindElementNode,
    GetElementPropertyNode,
    GetElementTextNode,
    TypeTextNode,
)

# Interaction Nodes
from casare_rpa.nodes.desktop_nodes.interaction_nodes import (
    BY_TEXT_PROP,
    CHECK_PROP,
    EXPAND_PROP,
    SCROLL_AMOUNT_PROP,
    SCROLL_DIRECTION_PROP,
    TAB_INDEX_PROP,
    TAB_NAME_PROP,
    CheckCheckboxNode,
    ExpandTreeItemNode,
    InteractionNodeBase,
    ScrollElementNode,
    SelectFromDropdownNode,
    SelectRadioButtonNode,
    SelectTabNode,
)

# Mouse and Keyboard Nodes
from casare_rpa.nodes.desktop_nodes.mouse_keyboard_nodes import (
    CLICK_COUNT_PROP,
    CLICK_DELAY_PROP,
    EASE_PROP,
    KEY_PROP,
    PRESS_ENTER_AFTER_PROP,
    STEPS_PROP,
    WAIT_TIME_PROP,
    DragMouseNode,
    GetMousePositionNode,
    MouseClickNode,
    MoveMouseNode,
    SendHotKeyNode,
    SendKeysNode,
)

# Office Nodes
from casare_rpa.nodes.desktop_nodes.office_nodes import (
    ExcelCloseNode,
    ExcelGetRangeNode,
    # Excel
    ExcelOpenNode,
    ExcelReadCellNode,
    ExcelWriteCellNode,
    OutlookGetInboxCountNode,
    OutlookReadEmailsNode,
    # Outlook
    OutlookSendEmailNode,
    WordCloseNode,
    WordGetTextNode,
    # Word
    WordOpenNode,
    WordReplaceTextNode,
)

# Reusable PropertyDef constants
from casare_rpa.nodes.desktop_nodes.properties import (
    # Application
    APPLICATION_PATH_PROP,
    ARGUMENTS_PROP,
    BRING_TO_FRONT_PROP,
    CELL_PROP,
    CLEAR_FIRST_PROP,
    CLICK_TYPE_PROP,
    COMPARISON_PROP,
    CREATE_IF_MISSING_PROP,
    DURATION_PROP,
    # Screenshot/OCR
    FILE_PATH_PROP,
    FILTER_TITLE_PROP,
    FORCE_CLOSE_PROP,
    HOTKEY_MODIFIER_PROP,
    HTML_BODY_PROP,
    IMAGE_FORMAT_PROP,
    INCLUDE_INVISIBLE_PROP,
    INTERVAL_PROP,
    # Keyboard
    KEYS_PROP,
    MATCH_PARTIAL_PROP,
    # Mouse
    MOUSE_BUTTON_PROP,
    OCR_ENGINE_PROP,
    OCR_LANGUAGE_PROP,
    PADDING_PROP,
    POLL_INTERVAL_PROP,
    QUIT_APP_PROP,
    RANGE_PROP,
    RETRY_COUNT_PROP,
    RETRY_INTERVAL_PROP,
    SAVE_BEFORE_CLOSE_PROP,
    # Element
    SELECTOR_PROP,
    SHEET_PROP,
    SIMULATE_PROP,
    TEXT_PROP,
    THROW_ON_NOT_FOUND_PROP,
    TIMEOUT_LONG_PROP,
    # Common
    TIMEOUT_PROP,
    VARIABLE_NAME_PROP,
    # Office
    VISIBLE_PROP,
    # Wait/Verification
    WAIT_STATE_PROP,
    WINDOW_STATE_PROP,
    WINDOW_TITLE_HINT_PROP,
    WITH_ALT_PROP,
    WITH_CTRL_PROP,
    WITH_SHIFT_PROP,
    WORKING_DIRECTORY_PROP,
    X_OFFSET_PROP,
    Y_OFFSET_PROP,
)

# Screenshot and OCR Nodes
from casare_rpa.nodes.desktop_nodes.screenshot_ocr_nodes import (
    CaptureElementImageNode,
    CaptureScreenshotNode,
    CompareImagesNode,
    OCRExtractTextNode,
)

# Wait and Verification Nodes
from casare_rpa.nodes.desktop_nodes.wait_verification_nodes import (
    VerifyElementExistsNode,
    VerifyElementPropertyNode,
    WaitForElementNode,
    WaitForWindowNode,
)

# Window Nodes
from casare_rpa.nodes.desktop_nodes.window_nodes import (
    HEIGHT_PROP,
    POSITION_X_PROP,
    POSITION_Y_PROP,
    WIDTH_PROP,
    GetWindowPropertiesNode,
    MaximizeWindowNode,
    MinimizeWindowNode,
    MoveWindowNode,
    ResizeWindowNode,
    RestoreWindowNode,
    SetWindowStateNode,
    WindowNodeBase,
)

__all__ = [
    # Base classes
    "DesktopNodeBase",
    "ElementInteractionMixin",
    "WindowOperationMixin",
    "WindowNodeBase",
    "InteractionNodeBase",
    # Element Nodes
    "FindElementNode",
    "ClickElementNode",
    "TypeTextNode",
    "GetElementTextNode",
    "GetElementPropertyNode",
    # Application Nodes
    "LaunchApplicationNode",
    "CloseApplicationNode",
    "ActivateWindowNode",
    "GetWindowListNode",
    # Window Nodes
    "ResizeWindowNode",
    "MoveWindowNode",
    "MaximizeWindowNode",
    "MinimizeWindowNode",
    "RestoreWindowNode",
    "GetWindowPropertiesNode",
    "SetWindowStateNode",
    # Interaction Nodes
    "SelectFromDropdownNode",
    "CheckCheckboxNode",
    "SelectRadioButtonNode",
    "SelectTabNode",
    "ExpandTreeItemNode",
    "ScrollElementNode",
    # Mouse/Keyboard Nodes
    "MoveMouseNode",
    "MouseClickNode",
    "SendKeysNode",
    "SendHotKeyNode",
    "GetMousePositionNode",
    "DragMouseNode",
    # Wait/Verification Nodes
    "WaitForElementNode",
    "WaitForWindowNode",
    "VerifyElementExistsNode",
    "VerifyElementPropertyNode",
    # Screenshot/OCR Nodes
    "CaptureScreenshotNode",
    "CaptureElementImageNode",
    "OCRExtractTextNode",
    "CompareImagesNode",
    # Excel Nodes
    "ExcelOpenNode",
    "ExcelReadCellNode",
    "ExcelWriteCellNode",
    "ExcelGetRangeNode",
    "ExcelCloseNode",
    # Word Nodes
    "WordOpenNode",
    "WordGetTextNode",
    "WordReplaceTextNode",
    "WordCloseNode",
    # Outlook Nodes
    "OutlookSendEmailNode",
    "OutlookReadEmailsNode",
    "OutlookGetInboxCountNode",
    # PropertyDef constants - Common
    "TIMEOUT_PROP",
    "TIMEOUT_LONG_PROP",
    "RETRY_COUNT_PROP",
    "RETRY_INTERVAL_PROP",
    # PropertyDef constants - Element
    "SELECTOR_PROP",
    "THROW_ON_NOT_FOUND_PROP",
    "SIMULATE_PROP",
    "X_OFFSET_PROP",
    "Y_OFFSET_PROP",
    "TEXT_PROP",
    "CLEAR_FIRST_PROP",
    "INTERVAL_PROP",
    "VARIABLE_NAME_PROP",
    # PropertyDef constants - Application/Window
    "APPLICATION_PATH_PROP",
    "ARGUMENTS_PROP",
    "WORKING_DIRECTORY_PROP",
    "WINDOW_TITLE_HINT_PROP",
    "WINDOW_STATE_PROP",
    "FORCE_CLOSE_PROP",
    "MATCH_PARTIAL_PROP",
    "INCLUDE_INVISIBLE_PROP",
    "FILTER_TITLE_PROP",
    "BRING_TO_FRONT_PROP",
    "WIDTH_PROP",
    "HEIGHT_PROP",
    "POSITION_X_PROP",
    "POSITION_Y_PROP",
    # PropertyDef constants - Mouse
    "MOUSE_BUTTON_PROP",
    "CLICK_TYPE_PROP",
    "DURATION_PROP",
    "EASE_PROP",
    "STEPS_PROP",
    "CLICK_COUNT_PROP",
    "CLICK_DELAY_PROP",
    # PropertyDef constants - Keyboard
    "KEYS_PROP",
    "HOTKEY_MODIFIER_PROP",
    "WITH_CTRL_PROP",
    "WITH_SHIFT_PROP",
    "WITH_ALT_PROP",
    "PRESS_ENTER_AFTER_PROP",
    "WAIT_TIME_PROP",
    "KEY_PROP",
    # PropertyDef constants - Wait/Verification
    "WAIT_STATE_PROP",
    "POLL_INTERVAL_PROP",
    "COMPARISON_PROP",
    # PropertyDef constants - Interaction
    "BY_TEXT_PROP",
    "CHECK_PROP",
    "EXPAND_PROP",
    "TAB_NAME_PROP",
    "TAB_INDEX_PROP",
    "SCROLL_DIRECTION_PROP",
    "SCROLL_AMOUNT_PROP",
    # PropertyDef constants - Screenshot/OCR
    "FILE_PATH_PROP",
    "IMAGE_FORMAT_PROP",
    "PADDING_PROP",
    "OCR_ENGINE_PROP",
    "OCR_LANGUAGE_PROP",
    # PropertyDef constants - Office
    "VISIBLE_PROP",
    "CREATE_IF_MISSING_PROP",
    "SHEET_PROP",
    "CELL_PROP",
    "RANGE_PROP",
    "SAVE_BEFORE_CLOSE_PROP",
    "QUIT_APP_PROP",
    "HTML_BODY_PROP",
]
