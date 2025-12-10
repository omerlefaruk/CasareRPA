"""
UI Widgets Module.

Reusable widget components for the CasareRPA Canvas application.
"""

from casare_rpa.presentation.canvas.ui.widgets.variable_editor_widget import (
    VariableEditorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.output_console_widget import (
    OutputConsoleWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.search_widget import SearchWidget
from casare_rpa.presentation.canvas.ui.widgets.robot_override_widget import (
    RobotOverrideWidget,
    ROBOT_CAPABILITIES,
)
from casare_rpa.presentation.canvas.ui.widgets.ai_settings_widget import (
    AISettingsWidget,
    LLM_MODELS,
    PROVIDER_TO_CATEGORY,
    get_all_models,
    get_llm_credentials,
    detect_provider_from_model,
)
from casare_rpa.presentation.canvas.ui.widgets.tenant_selector import (
    TenantSelectorWidget,
    TenantFilterWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.file_path_widget import (
    FilePathWidget,
    PathType,
    get_filter_for_property,
    is_file_path_property,
    is_directory_path_property,
)
from casare_rpa.presentation.canvas.ui.widgets.variable_picker import (
    VariableInfo,
    VariableProvider,
    VariablePickerPopup,
    VariableButton,
    VariableAwareLineEdit,
    create_variable_aware_line_edit,
)
from casare_rpa.presentation.canvas.ui.widgets.selector_input_widget import (
    SelectorInputWidget,
    is_selector_property,
)
from casare_rpa.presentation.canvas.ui.widgets.anchor_selector_widget import (
    AnchorSelectorWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.validated_input import (
    ValidationStatus,
    ValidationResult,
    ValidatedLineEdit,
    ValidatedInputWidget,
    get_validated_line_edit_style,
    required_validator,
    min_value_validator,
    max_value_validator,
    range_validator,
    integer_validator,
    positive_validator,
    non_negative_validator,
    selector_warning_validator,
)
from casare_rpa.presentation.canvas.ui.widgets.breadcrumb_nav import (
    BreadcrumbItem,
    BreadcrumbNavWidget,
    SubflowNavigationController,
)
from casare_rpa.presentation.canvas.ui.widgets.google_credential_picker import (
    GoogleCredentialPicker,
    GoogleCredentialPickerWithLabel,
)
from casare_rpa.presentation.canvas.ui.widgets.cascading_dropdown import (
    CascadingDropdownBase,
    CascadingDropdownWithLabel,
    DropdownItem,
)
from casare_rpa.presentation.canvas.ui.widgets.google_pickers import (
    GoogleSpreadsheetPicker,
    GoogleSheetPicker,
    GoogleDriveFilePicker,
    GoogleDriveFolderPicker,
)
from casare_rpa.presentation.canvas.ui.widgets.google_folder_navigator import (
    FolderInfo,
    FolderNavigatorState,
    FolderCache,
    NavigatorMode,
    PathBreadcrumb,
    FolderSearchInput,
    GoogleDriveFolderNavigator,
    fetch_folder_children,
    fetch_folders_recursive,
    search_folders,
    validate_folder_id,
    get_folder_path,
    extract_folder_id_from_url,
)
from casare_rpa.presentation.canvas.ui.widgets.json_syntax_highlighter import (
    JsonSyntaxHighlighter,
    JsonColors,
    get_json_highlighter_stylesheet,
)
from casare_rpa.presentation.canvas.ui.widgets.node_output_popup import (
    NodeOutputPopup,
    OutputSchemaView,
    OutputTableView,
    OutputJsonView,
    PopupColors,
    SchemaItemWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.profiling_tree import (
    ProfilingTreeWidget,
    ProfilingEntry,
    PercentageBarDelegate,
)
from casare_rpa.presentation.canvas.ui.widgets.animation_profiler import (
    AnimationProfiler,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_dialog import (
    AnimatedDialog,
)
from casare_rpa.presentation.canvas.ui.widgets.collapsible_section import (
    CollapsibleSection,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_dock import (
    AnimatedDockWidget,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_tab_widget import (
    AnimatedTabWidget,
    AnimatedTabBar,
    create_animated_tab_widget,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_spin_box import (
    AnimatedSpinBox,
    AnimatedDoubleSpinBox,
    create_animated_spin_box,
    create_animated_double_spin_box,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_combo_box import (
    AnimatedComboBox,
    create_animated_combo_box,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_checkbox import (
    AnimatedCheckBox,
    create_animated_checkbox,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_progress_bar import (
    AnimatedProgressBar,
    create_animated_progress_bar,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_line_edit import (
    AnimatedLineEdit,
    create_animated_line_edit,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_button import (
    AnimatedButton,
    AnimatedIconButton,
    create_animated_button,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_scroll_area import (
    AnimatedScrollArea,
    create_animated_scroll_area,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_tooltip import (
    AnimatedToolTip,
    show_animated_tooltip,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_status_bar import (
    AnimatedStatusBar,
    create_animated_status_bar,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_list_widget import (
    AnimatedListWidget,
    create_animated_list_widget,
)
from casare_rpa.presentation.canvas.ui.widgets.animated_tree_widget import (
    AnimatedTreeWidget,
    create_animated_tree_widget,
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
    # Animation Profiler
    "AnimationProfiler",
    # Animated Dialog
    "AnimatedDialog",
    # Collapsible Section
    "CollapsibleSection",
    # Animated Dock Widget
    "AnimatedDockWidget",
    # Animated Tab Widget
    "AnimatedTabWidget",
    "AnimatedTabBar",
    "create_animated_tab_widget",
    # Animated Spin Box
    "AnimatedSpinBox",
    "AnimatedDoubleSpinBox",
    "create_animated_spin_box",
    "create_animated_double_spin_box",
    # Animated Combo Box
    "AnimatedComboBox",
    "create_animated_combo_box",
    # Animated Checkbox
    "AnimatedCheckBox",
    "create_animated_checkbox",
    # Animated Progress Bar
    "AnimatedProgressBar",
    "create_animated_progress_bar",
    # Animated Line Edit
    "AnimatedLineEdit",
    "create_animated_line_edit",
    # Animated Button
    "AnimatedButton",
    "AnimatedIconButton",
    "create_animated_button",
    # Animated Scroll Area
    "AnimatedScrollArea",
    "create_animated_scroll_area",
    # Animated Tooltip
    "AnimatedToolTip",
    "show_animated_tooltip",
    # Animated Status Bar
    "AnimatedStatusBar",
    "create_animated_status_bar",
    # Animated List Widget
    "AnimatedListWidget",
    "create_animated_list_widget",
    # Animated Tree Widget
    "AnimatedTreeWidget",
    "create_animated_tree_widget",
]
