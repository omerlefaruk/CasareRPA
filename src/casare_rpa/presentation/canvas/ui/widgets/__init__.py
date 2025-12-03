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
]
