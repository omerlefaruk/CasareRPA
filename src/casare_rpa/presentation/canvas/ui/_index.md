# Canvas UI Index

```xml<ui_index>
  <!-- Quick reference for Canvas UI components. Use for fast discovery. -->

  <overview>
    <p>Reusable UI components for CasareRPA Canvas application</p>
    <struct>panels/, dialogs/, widgets/, toolbars/</struct>
    <exports>130+ total</exports>
  </overview>

  <dirs>
    <d name="panels/">   <n>21</n> <p>Dockable panels (Variables, Debug, Minimap, etc.)</p></d>
    <d name="dialogs/">  <n>26</n> <p>Modal dialogs (Properties, Settings, Preferences)</p></d>
    <d name="widgets/">  <n>26</n> <p>Reusable widgets (Variable Editor, File Path, etc.)</p></d>
    <d name="toolbars/"> <n>2</n>  <p>Action toolbars (Main, Hotkeys)</p></d>
  </dirs>

  <base_classes>
    <e>BaseWidget</e>     <s>base_widget.py</s> <d>Abstract base for all UI components</d>
    <e>BaseDockWidget</e> <s>base_widget.py</s> <d>Base for dockable widgets</d>
    <e>BaseDialog</e>     <s>base_widget.py</s> <d>Base for modal dialogs</d>
  </base_classes>

  <theme>
    <exports>
      <e>Theme</e>                    <d>Main theme configuration class</d>
      <e>ThemeMode</e>                <d>DARK, LIGHT enum</d>
      <e>Colors</e>                   <d>Primary, secondary, accent color definitions</d>
      <e>CanvasColors</e>             <d>Canvas-specific colors</d>
      <e>Spacing, BorderRadius, FontSizes, ButtonSizes, IconSizes, Animations</e>
      <e>THEME</e>                    <d>Global theme instance</d>
    </exports>
    <functions>
      <f>get_canvas_stylesheet_v2()</f>
      <f>get_node_status_color(status)</f>
      <f>get_wire_color(data_type)</f>
      <f>get_status_color(status)</f>
      <f>get_type_color(type_name)</f>
      <f>get_type_badge(type_name)</f>
    </functions>
  </theme>

  <panels>
    <e>VariablesPanel</e>            <d>Workflow variable management</d>
    <e>MinimapPanel</e>              <d>Canvas minimap navigation</d>
    <e>BottomPanelDock</e>           <d>Bottom dock container</d>
    <e>SidePanelDock</e>             <d>Side dock container</d>
    <e>LogViewerPanel</e>            <d>Execution log viewer</d>
    <e>ProcessMiningPanel</e>        <d>Process analytics</d>
    <e>AnalyticsPanel</e>            <d>Workflow analytics</d>
    <e>RobotPickerPanel</e>          <d>Remote robot selection</d>
    <e>BrowserRecordingPanel</e>     <d>Browser recording controls</d>
    <e>PortLegendPanel</e>           <d>Port type legend</d>
    <e>CredentialsPanel</e>          <d>Credential management</d>
    <e>ProjectExplorerPanel</e>      <d>Project file browser</d>
  </panels>

  <panel_tabs>
    <e>HistoryTab</e>      <d>Execution history</d>
    <e>LogTab</e>          <d>Log messages</d>
    <e>OutputTab</e>       <d>Execution output</d>
    <e>TerminalTab</e>     <d>Terminal emulator</d>
    <e>ValidationTab</e>   <d>Workflow validation</d>
  </panel_tabs>

  <dialogs>
    <e>NodePropertiesDialog</e>     <d>Edit node properties</d>
    <e>WorkflowSettingsDialog</e>   <d>Workflow configuration</d>
    <e>PreferencesDialog</e>        <d>Application preferences</d>
    <e>RecordingPreviewDialog</e>   <d>Recording preview</d>
    <e>RecordingReviewDialog</e>    <d>Review recorded actions</d>
    <e>UpdateDialog</e>             <d>Application updates</d>
    <e>ProjectManagerDialog</e>     <d>Project management</d>
    <e>CredentialManagerDialog</e>  <d>Credential CRUD</d>
    <e>FleetDashboardDialog</e>     <d>Fleet management</d>
    <e>QuickNodeConfigDialog</e>    <d>Quick node setup</d>
    <e>ParameterPromotionDialog</e> <d>Promote to variable</d>
    <e>GoogleOAuthDialog</e>        <d>Google OAuth flow (Vertex AI)</d>
    <e>GeminiStudioOAuthDialog</e>  <d>Gemini AI Studio OAuth flow</d>
    <e>EnvironmentEditorDialog</e>  <d>Environment variables</d>
    <e>ProjectWizard</e>            <d>New project wizard</d>
  </dialogs>

  <widgets>
    <core>
      <e>VariableEditorWidget</e>   <d>Variable editing</d>
      <e>OutputConsoleWidget</e>    <d>Console output</d>
      <e>SearchWidget</e>           <d>Search functionality</d>
      <e>CollapsibleSection</e>     <d>Collapsible container</d>
    </core>
    <input>
      <e>FilePathWidget</e>         <d>File/folder path input</d>
      <e>SelectorInputWidget</e>    <d>Element selector input</d>
      <e>AnchorSelectorWidget</e>   <d>Anchor element selection</d>
      <e>ValidatedLineEdit</e>      <d>Line edit with validation</d>
      <e>ValidatedInputWidget</e>   <d>Validated input container</d>
    </input>
    <variable>
      <e>VariableInfo</e>           <d>Variable metadata</d>
      <e>VariableProvider</e>       <d>Variable source interface</d>
      <e>VariablePickerPopup</e>    <d>Variable selection popup</d>
      <e>VariableButton</e>         <d>Variable insert button</d>
      <e>VariableAwareLineEdit</e>  <d>Line edit with variable support</d>
    </variable>
    <google>
      <e>GoogleCredentialPicker</e>     <d>Google credential selection</d>
      <e>GoogleSpreadsheetPicker</e>    <d>Spreadsheet picker</d>
      <e>GoogleSheetPicker</e>          <d>Sheet tab picker</d>
      <e>GoogleDriveFilePicker</e>      <d>Drive file picker</d>
      <e>GoogleDriveFolderPicker</e>    <d>Drive folder picker</d>
      <e>GoogleDriveFolderNavigator</e> <d>Folder navigation</d>
    </google>
    <specialized>
      <e>RobotOverrideWidget</e>        <d>Robot capability override</d>
      <e>AISettingsWidget</e>           <d>AI/LLM configuration</d>
      <e>TenantSelectorWidget</e>       <d>Multi-tenant selection</d>
      <e>JsonSyntaxHighlighter</e>      <d>JSON syntax coloring</d>
      <e>NodeOutputPopup</e>            <d>Node output inspector</d>
      <e>ToastNotification</e>          <d>Non-blocking toast notifications</d>
      <e>ProfilingTreeWidget</e>        <d>Performance profiling tree</d>
    </specialized>
  </widgets>

  <usage>
    <code>
# Theme usage
from casare_rpa.presentation.canvas.ui import THEME, get_canvas_stylesheet_v2, get_wire_color
stylesheet = get_canvas_stylesheet_v2()
color = get_wire_color("STRING")

# Dialog usage
from casare_rpa.presentation.canvas.ui import NodePropertiesDialog, PreferencesDialog
dialog = NodePropertiesDialog(node, parent=self)
if dialog.exec():
    config = dialog.get_config()

# Widget usage
from casare_rpa.presentation.canvas.ui.widgets import VariableAwareLineEdit, FilePathWidget
line_edit = VariableAwareLineEdit(variable_provider=self)
file_picker = FilePathWidget(path_type=PathType.FILE)
    </code>
  </usage>

  <related>
    <r>canvas.graph</r>      <d>Node rendering components</d>
    <r>canvas.controllers</r> <d>UI controllers</d>
    <r>canvas.events</r>      <d>Event bus system</d>
  </related>
</ui_index>
```
