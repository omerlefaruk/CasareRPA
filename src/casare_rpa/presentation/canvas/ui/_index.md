# Canvas UI Index

Quick reference for Canvas UI components. Use for fast discovery.

## Overview

| Aspect | Description |
|--------|-------------|
| Purpose | Reusable UI components for CasareRPA Canvas application |
| Structure | panels/, dialogs/, widgets/, toolbars/ |
| Exports | 130+ total exports |

## Directory Structure

| Directory | Files | Description |
|-----------|-------|-------------|
| `panels/` | 21 | Dockable panels (Variables, Debug, Minimap, etc.) |
| `dialogs/` | 26 | Modal dialogs (Properties, Settings, Preferences) |
| `widgets/` | 26 | Reusable widgets (Variable Editor, File Path, etc.) |
| `toolbars/` | 2 | Action toolbars (Main, Hotkeys) |

## Base Classes

| Export | Source | Description |
|--------|--------|-------------|
| `BaseWidget` | `base_widget.py` | Abstract base for all UI components |
| `BaseDockWidget` | `base_widget.py` | Base for dockable widgets |
| `BaseDialog` | `base_widget.py` | Base for modal dialogs |

## Theme System (theme.py)

| Export | Description |
|--------|-------------|
| `Theme` | Main theme configuration class |
| `ThemeMode` | DARK, LIGHT enum |
| `Colors` | Primary, secondary, accent color definitions |
| `CanvasColors` | Canvas-specific colors (background, grid) |
| `Spacing` | Standard spacing values |
| `BorderRadius` | Border radius constants |
| `FontSizes` | Typography sizes |
| `ButtonSizes` | Button dimension constants |
| `IconSizes` | Icon size constants |
| `Animations` | Animation duration/easing |
| `DARK_COLORS` | Dark theme color palette |
| `DARK_CANVAS_COLORS` | Dark canvas colors |
| `CATEGORY_COLOR_MAP` | Node category to color mapping |
| `THEME` | Global theme instance |
| `TYPE_COLORS` | Data type color mapping |
| `TYPE_BADGES` | Data type badge styling |

### Theme Functions

| Function | Description |
|----------|-------------|
| `get_canvas_stylesheet()` | Get full canvas CSS |
| `get_node_status_color(status)` | Get color for node execution status |
| `get_wire_color(data_type)` | Get wire color for data type |
| `get_status_color(status)` | Get general status color |
| `get_type_color(type_name)` | Get color for data type |
| `get_type_badge(type_name)` | Get badge style for type |

## Panels (panels/__init__.py)

| Export | Description |
|--------|-------------|
| `VariablesPanel` | Workflow variable management |
| `MinimapPanel` | Canvas minimap navigation |
| `BottomPanelDock` | Bottom dock container |
| `SidePanelDock` | Side dock container |
| `LogViewerPanel` | Execution log viewer |
| `ProcessMiningPanel` | Process analytics |
| `AnalyticsPanel` | Workflow analytics |
| `RobotPickerPanel` | Remote robot selection |
| `BrowserRecordingPanel` | Browser recording controls |
| `PortLegendPanel` | Port type legend |
| `CredentialsPanel` | Credential management |
| `ProjectExplorerPanel` | Project file browser |

### Panel Tabs

| Export | Description |
|--------|-------------|
| `HistoryTab` | Execution history |
| `LogTab` | Log messages |
| `OutputTab` | Execution output |
| `TerminalTab` | Terminal emulator |
| `ValidationTab` | Workflow validation |

### UX Helpers

| Export | Description |
|--------|-------------|
| `EmptyStateWidget` | Guidance when no data |
| `StatusBadge` | Color-coded status indicator |
| `ToolbarButton` | Consistent toolbar button |
| `SectionHeader` | Visual section separator |
| `get_panel_table_stylesheet()` | Table styling |
| `get_panel_toolbar_stylesheet()` | Toolbar styling |
| `create_context_menu()` | Standard context menu |

## Dialogs (dialogs/__init__.py)

| Export | Description |
|--------|-------------|
| `NodePropertiesDialog` | Edit node properties |
| `WorkflowSettingsDialog` | Workflow configuration |
| `PreferencesDialog` | Application preferences |
| `RecordingPreviewDialog` | Recording preview |
| `RecordingReviewDialog` | Review recorded actions |
| `UpdateDialog` | Application updates |
| `ProjectManagerDialog` | Project management |
| `CredentialManagerDialog` | Credential CRUD |
| `FleetDashboardDialog` | Fleet management |
| `QuickNodeConfigDialog` | Quick node setup |
| `ParameterPromotionDialog` | Promote to variable |
| `GoogleOAuthDialog` | Google OAuth flow (Vertex AI) |
| `GeminiStudioOAuthDialog` | Gemini AI Studio OAuth flow |
| `EnvironmentEditorDialog` | Environment variables |
| `ProjectWizard` | New project wizard |

### Dialog Styles

| Export | Description |
|--------|-------------|
| `DialogStyles` | Common dialog styling |
| `DialogSize` | Size presets enum |
| `DialogColors` | Dialog color palette |
| `apply_dialog_style(dialog)` | Apply consistent styling |
| `show_styled_message/warning/error/question()` | Styled message boxes |

## Widgets (widgets/__init__.py)

### Core Widgets

| Export | Description |
|--------|-------------|
| `VariableEditorWidget` | Variable editing |
| `OutputConsoleWidget` | Console output |
| `SearchWidget` | Search functionality |
| `CollapsibleSection` | Collapsible container |

### Input Widgets

| Export | Description |
|--------|-------------|
| `FilePathWidget` | File/folder path input |
| `SelectorInputWidget` | Element selector input |
| `AnchorSelectorWidget` | Anchor element selection |
| `ValidatedLineEdit` | Line edit with validation |
| `ValidatedInputWidget` | Validated input container |

### Variable System

| Export | Description |
|--------|-------------|
| `VariableInfo` | Variable metadata |
| `VariableProvider` | Variable source interface |
| `VariablePickerPopup` | Variable selection popup |
| `VariableButton` | Variable insert button |
| `VariableAwareLineEdit` | Line edit with variable support |

### Google Integration

| Export | Description |
|--------|-------------|
| `GoogleCredentialPicker` | Google credential selection |
| `GoogleSpreadsheetPicker` | Spreadsheet picker |
| `GoogleSheetPicker` | Sheet tab picker |
| `GoogleDriveFilePicker` | Drive file picker |
| `GoogleDriveFolderPicker` | Drive folder picker |
| `GoogleDriveFolderNavigator` | Folder navigation |

### Navigation

| Export | Description |
|--------|-------------|
| `BreadcrumbItem` | Breadcrumb data |
| `BreadcrumbNavWidget` | Breadcrumb navigation |
| `SubflowNavigationController` | Subflow nav controller |

### Specialized Widgets

| Export | Description |
|--------|-------------|
| `RobotOverrideWidget` | Robot capability override |
| `AISettingsWidget` | AI/LLM configuration |
| `TenantSelectorWidget` | Multi-tenant selection |
| `CascadingDropdownBase` | Cascading dropdown |
| `JsonSyntaxHighlighter` | JSON syntax coloring |
| `NodeOutputPopup` | Node output inspector |
| `ToastNotification` | Non-blocking toast notifications |
| `ProfilingTreeWidget` | Performance profiling tree |

### Validation Helpers

| Export | Description |
|--------|-------------|
| `ValidationStatus` | VALID, WARNING, ERROR |
| `ValidationResult` | Validation result data |
| `required_validator` | Required field check |
| `integer_validator` | Integer validation |
| `range_validator` | Range validation |

## Toolbars (toolbars/__init__.py)

| Export | Description |
|--------|-------------|
| `MainToolbar` | Main application toolbar |

## Usage Patterns

```python
# Theme usage
from casare_rpa.presentation.canvas.ui import (
    THEME, get_canvas_stylesheet, get_type_color
)

stylesheet = get_canvas_stylesheet()
color = get_type_color("STRING")

# Dialog usage
from casare_rpa.presentation.canvas.ui import (
    NodePropertiesDialog, PreferencesDialog
)

dialog = NodePropertiesDialog(node, parent=self)
if dialog.exec():
    config = dialog.get_config()

# Widget usage
from casare_rpa.presentation.canvas.ui.widgets import (
    VariableAwareLineEdit, FilePathWidget
)

line_edit = VariableAwareLineEdit(variable_provider=self)
file_picker = FilePathWidget(path_type=PathType.FILE)
```

## Related Modules

| Module | Relation |
|--------|----------|
| `canvas.graph` | Node rendering components |
| `canvas.controllers` | UI controllers |
| `canvas.events` | Event bus system |
