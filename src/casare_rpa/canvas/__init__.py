"""
CasareRPA - Canvas Package
Contains PySide6 UI components and windows for the visual workflow editor.

The canvas package is organized into subpackages:
- graph/: Node graph core (NodeGraphWidget, NodeRegistry, minimap)
- connections/: Connection handling (AutoConnect, ConnectionCutter, Validator)
- search/: Search functionality (NodeSearch, CommandPalette)
- selectors/: Selector UI (SelectorDialog, ElementPicker)
- snippets/: Snippet system (SnippetCreator, SnippetBrowser)
- scheduling/: Scheduling UI (ScheduleDialog, ScheduleStorage)
- desktop/: Desktop-specific UI (RecordingPanel)
- execution/: Execution UI (TriggerRunner, PerformanceDashboard)
- toolbar/: Toolbar components (HotkeyManager)
- workflow/: Workflow operations (WorkflowImport, RecentFiles)
- panels/: Dockable panels (BottomPanel, PropertiesPanel, DebugToolbar)
- dialogs/: Dialog windows (Preferences, Templates, etc.)
- visual_nodes/: Visual node definitions
"""

__version__ = "0.1.0"

# Main application - these are the primary entry points
from .app import CasareRPAApp, main
from .main_window import MainWindow

__all__ = [
    "__version__",
    "CasareRPAApp",
    "main",
    "MainWindow",
]
