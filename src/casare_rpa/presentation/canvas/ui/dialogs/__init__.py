"""
UI Dialogs Module.

Reusable dialog components for the CasareRPA Canvas application.
"""

from casare_rpa.presentation.canvas.ui.dialogs.dialog_styles import (
    DialogStyles,
    DialogSize,
    DialogColors,
    COLORS,
    DIALOG_DIMENSIONS,
    apply_dialog_style,
    show_styled_message,
    show_styled_warning,
    show_styled_error,
    show_styled_question,
)
from casare_rpa.presentation.canvas.ui.dialogs.node_properties_dialog import (
    NodePropertiesDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.workflow_settings_dialog import (
    WorkflowSettingsDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.preferences_dialog import (
    PreferencesDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.recording_dialog import (
    RecordingPreviewDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.recording_review_dialog import (
    RecordingReviewDialog,
)

# Template browser removed - templates system removed
# Trigger dialogs removed - triggers are now visual nodes
# Schedule dialogs removed - use Schedule Trigger node instead
from casare_rpa.presentation.canvas.ui.dialogs.update_dialog import (
    UpdateDialog,
    UpdateNotificationWidget,
)
from casare_rpa.presentation.canvas.ui.dialogs.project_manager_dialog import (
    ProjectManagerDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.credential_manager_dialog import (
    CredentialManagerDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.fleet_dashboard import (
    FleetDashboardDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.migration_dialog import (
    MigrationDialog,
    show_migration_dialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.quick_node_config_dialog import (
    QuickNodeConfigDialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.parameter_promotion_dialog import (
    ParameterPromotionDialog,
    show_parameter_promotion_dialog,
)
from casare_rpa.presentation.canvas.ui.dialogs.google_oauth_dialog import (
    GoogleOAuthDialog,
    GOOGLE_SCOPES,
)
from casare_rpa.presentation.canvas.ui.dialogs.environment_editor import (
    EnvironmentEditorDialog,
    show_environment_editor,
)
from casare_rpa.presentation.canvas.ui.dialogs.project_wizard import (
    ProjectWizard,
    show_project_wizard,
)

__all__ = [
    # Dialog Styles
    "DialogStyles",
    "DialogSize",
    "DialogColors",
    "COLORS",
    "DIALOG_DIMENSIONS",
    "apply_dialog_style",
    "show_styled_message",
    "show_styled_warning",
    "show_styled_error",
    "show_styled_question",
    # Dialogs
    "NodePropertiesDialog",
    "WorkflowSettingsDialog",
    "PreferencesDialog",
    "RecordingPreviewDialog",
    "RecordingReviewDialog",
    "UpdateDialog",
    "UpdateNotificationWidget",
    "ProjectManagerDialog",
    "CredentialManagerDialog",
    "FleetDashboardDialog",
    "MigrationDialog",
    "show_migration_dialog",
    "QuickNodeConfigDialog",
    "ParameterPromotionDialog",
    "show_parameter_promotion_dialog",
    # Google OAuth
    "GoogleOAuthDialog",
    "GOOGLE_SCOPES",
    # Environment Editor
    "EnvironmentEditorDialog",
    "show_environment_editor",
    # Project Wizard
    "ProjectWizard",
    "show_project_wizard",
]
