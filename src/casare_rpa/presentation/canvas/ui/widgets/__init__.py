"""
UI Widgets Module.

Reusable widget components for the CasareRPA Canvas application.
"""

from .variable_editor_widget import VariableEditorWidget
from .output_console_widget import OutputConsoleWidget
from .search_widget import SearchWidget
from .robot_override_widget import RobotOverrideWidget, ROBOT_CAPABILITIES
from .ai_settings_widget import (
    AISettingsWidget,
    LLM_MODELS,
    PROVIDER_TO_CATEGORY,
    get_all_models,
    get_llm_credentials,
    detect_provider_from_model,
)
from .tenant_selector import TenantSelectorWidget, TenantFilterWidget

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
