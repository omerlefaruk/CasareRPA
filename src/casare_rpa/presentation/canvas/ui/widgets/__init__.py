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
]
