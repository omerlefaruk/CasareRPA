"""
UI Widgets Module.

Reusable widget components for the CasareRPA Canvas application.
"""

from casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget import (
    LLM_MODELS,
    PROVIDER_TO_CATEGORY,
    AISettingsWidget,
    detect_provider_from_model,
    get_all_models,
    get_llm_credentials,
)
from casare_rpa.presentation.canvas.ui.widgets.anchor_selector_widget import (
    AnchorSelectorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.breadcrumb_nav import (
    BreadcrumbItem,
    BreadcrumbNavWidget,
    SubflowNavigationController,
)
from casare_rpa.presentation.canvas.ui.widgets.cascading_dropdown import (
    CascadingDropdownBase,
    CascadingDropdownWithLabel,
    DropdownItem,
)
from casare_rpa.presentation.canvas.ui.widgets.expression_editor import (
    CodeExpressionEditor,
    EditorType,
    ExpandButton,
    ExpressionEditorPopup,
    MarkdownEditor,
    RichTextEditor,
)
from casare_rpa.presentation.canvas.ui.widgets.file_path_widget import (
    FilePathWidget,
    PathType,
    get_filter_for_property,
    is_directory_path_property,
    is_file_path_property,
)
from casare_rpa.presentation.canvas.ui.widgets.google_credential_picker import (
    GoogleCredentialPicker,
    GoogleCredentialPickerWithLabel,
)
from casare_rpa.presentation.canvas.ui.widgets.google_folder_navigator import (
    FolderCache,
    FolderInfo,
    FolderNavigatorState,
    FolderSearchInput,
    GoogleDriveFolderNavigator,
    NavigatorMode,
    PathBreadcrumb,
    extract_folder_id_from_url,
    fetch_folder_children,
    fetch_folders_recursive,
    get_folder_path,
    search_folders,
    validate_folder_id,
)
from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
    GoogleDriveFilePicker,
    GoogleDriveFolderPicker,
    GoogleSheetPicker,
    GoogleSpreadsheetPicker,
)
from casare_rpa.presentation.canvas.ui.widgets.json_syntax_highlighter import (
    JsonColors,
    JsonSyntaxHighlighter,
    get_json_highlighter_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.node_output_popup import (
    NodeOutputPopup,
    OutputJsonView,
    OutputSchemaView,
    OutputTableView,
    PopupColors,
    SchemaItemWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.output_console_widget import (
    OutputConsoleWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.profiling_tree import (
    PercentageBarDelegate,
    ProfilingEntry,
    ProfilingTreeWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.robot_override_widget import (
    ROBOT_CAPABILITIES,
    RobotOverrideWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.search_widget import SearchWidget
from casare_rpa.presentation.canvas.ui.widgets.selector_input_widget import (
    SelectorInputWidget,
    is_selector_property,
)
from casare_rpa.presentation.canvas.ui.widgets.tenant_selector import (
    TenantFilterWidget,
    TenantSelectorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.toast import ToastNotification
from casare_rpa.presentation.canvas.ui.widgets.validated_input import (
    ValidatedInputWidget,
    ValidatedLineEdit,
    ValidationResult,
    ValidationStatus,
    get_validated_line_edit_style,
    integer_validator,
    max_value_validator,
    min_value_validator,
    non_negative_validator,
    positive_validator,
    range_validator,
    required_validator,
    selector_warning_validator,
)
from casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget import (
    VariableEditorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableAwareLineEdit,
    VariableButton,
    VariableInfo,
    VariablePickerPopup,
    VariableProvider,
    create_variable_aware_line_edit,
)

__all__ = [
    "VariableEditorWidget",
    "OutputConsoleWidget",
    "SearchWidget",
    # Robot Override
    "RobotOverrideWidget",
    "ROBOT_CAPABILITIES",
    # AI Settings
    "AISettingsWidget",
    "LLM_MODELS",
    "PROVIDER_TO_CATEGORY",
    "get_all_models",
    "get_llm_credentials",
    "detect_provider_from_model",
    # Tenant Selector
    "TenantSelectorWidget",
    "TenantFilterWidget",
    # File Path
    "FilePathWidget",
    "PathType",
    "get_filter_for_property",
    "is_file_path_property",
    "is_directory_path_property",
    # Variable Picker
    "VariableInfo",
    "VariableProvider",
    "VariablePickerPopup",
    "VariableButton",
    "VariableAwareLineEdit",
    "create_variable_aware_line_edit",
    # Selector Input
    "SelectorInputWidget",
    "is_selector_property",
    # Anchor Selector
    "AnchorSelectorWidget",
    # Validation
    "ValidationStatus",
    "ValidationResult",
    "ValidatedLineEdit",
    "ValidatedInputWidget",
    "get_validated_line_edit_style",
    "required_validator",
    "min_value_validator",
    "max_value_validator",
    "range_validator",
    "integer_validator",
    "positive_validator",
    "non_negative_validator",
    "selector_warning_validator",
    # Breadcrumb Navigation
    "BreadcrumbItem",
    "BreadcrumbNavWidget",
    "SubflowNavigationController",
    # Google Credential Picker
    "GoogleCredentialPicker",
    "GoogleCredentialPickerWithLabel",
    # Cascading Dropdown
    "CascadingDropdownBase",
    "CascadingDropdownWithLabel",
    "DropdownItem",
    # Google Pickers
    "GoogleSpreadsheetPicker",
    "GoogleSheetPicker",
    "GoogleDriveFilePicker",
    "GoogleDriveFolderPicker",
    # Google Folder Navigator
    "FolderInfo",
    "FolderNavigatorState",
    "FolderCache",
    "NavigatorMode",
    "PathBreadcrumb",
    "FolderSearchInput",
    "GoogleDriveFolderNavigator",
    "fetch_folder_children",
    "fetch_folders_recursive",
    "search_folders",
    "validate_folder_id",
    "get_folder_path",
    "extract_folder_id_from_url",
    # JSON Syntax Highlighter
    "JsonSyntaxHighlighter",
    "JsonColors",
    "get_json_highlighter_stylesheet",
    # Node Output Inspector
    "NodeOutputPopup",
    "OutputSchemaView",
    "OutputTableView",
    "OutputJsonView",
    "PopupColors",
    "SchemaItemWidget",
    # Profiling Tree
    "ProfilingTreeWidget",
    "ProfilingEntry",
    "PercentageBarDelegate",
    # Expression Editor
    "ExpressionEditorPopup",
    "EditorType",
    "CodeExpressionEditor",
    "MarkdownEditor",
    "RichTextEditor",
    "ExpandButton",
    "ToastNotification",
]
