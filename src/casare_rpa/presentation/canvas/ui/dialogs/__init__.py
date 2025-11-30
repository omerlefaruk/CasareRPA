"""
UI Dialogs Module.

Reusable dialog components for the CasareRPA Canvas application.
"""

from .node_properties_dialog import NodePropertiesDialog
from .workflow_settings_dialog import WorkflowSettingsDialog
from .preferences_dialog import PreferencesDialog
from .recording_dialog import RecordingPreviewDialog
from .template_browser_dialog import TemplateBrowserDialog
from .trigger_config_dialog import TriggerConfigDialog
from .trigger_type_selector import TriggerTypeSelectorDialog
from .schedule_dialog import ScheduleDialog, ScheduleManagerDialog
from .update_dialog import UpdateDialog, UpdateNotificationWidget

__all__ = [
    "NodePropertiesDialog",
    "WorkflowSettingsDialog",
    "PreferencesDialog",
    "RecordingPreviewDialog",
    "TemplateBrowserDialog",
    "TriggerConfigDialog",
    "TriggerTypeSelectorDialog",
    "ScheduleDialog",
    "ScheduleManagerDialog",
    "UpdateDialog",
    "UpdateNotificationWidget",
]
