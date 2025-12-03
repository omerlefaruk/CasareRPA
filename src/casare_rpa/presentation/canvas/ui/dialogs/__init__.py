"""
UI Dialogs Module.

Reusable dialog components for the CasareRPA Canvas application.
"""

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
from casare_rpa.presentation.canvas.ui.dialogs.template_browser_dialog import (
    TemplateBrowserDialog,
)

# Trigger dialogs removed - triggers are now visual nodes
from casare_rpa.presentation.canvas.ui.dialogs.schedule_dialog import (
    ScheduleDialog,
    ScheduleManagerDialog,
)
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

__all__ = [
    "NodePropertiesDialog",
    "WorkflowSettingsDialog",
    "PreferencesDialog",
    "RecordingPreviewDialog",
    "TemplateBrowserDialog",
    "ScheduleDialog",
    "ScheduleManagerDialog",
    "UpdateDialog",
    "UpdateNotificationWidget",
    "ProjectManagerDialog",
    "CredentialManagerDialog",
    "FleetDashboardDialog",
]
