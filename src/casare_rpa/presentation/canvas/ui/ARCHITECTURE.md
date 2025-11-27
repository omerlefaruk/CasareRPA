# UI Components Architecture

## Component Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                          BaseWidget                                 │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Abstract Methods:                                             │  │
│  │  - setup_ui() -> None                                         │  │
│  │  - apply_stylesheet() -> None                                 │  │
│  │  - connect_signals() -> None                                  │  │
│  │                                                                │  │
│  │ Provided Methods:                                             │  │
│  │  - set_state(key, value)                                      │  │
│  │  - get_state(key, default)                                    │  │
│  │  - clear_state()                                              │  │
│  │  - is_initialized() -> bool                                   │  │
│  │                                                                │  │
│  │ Signals:                                                       │  │
│  │  - value_changed(object)                                       │  │
│  │  - state_changed(str, object)                                  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼─────────┐   ┌──────▼──────┐   ┌─────────▼──────────┐
│BaseDockWidget   │   │BaseDialog   │   │Direct Inheritance  │
│                 │   │             │   │                    │
│+ get_title()    │   │+ validate() │   │Panels without dock │
│+ set_title()    │   │+ get_result()│   │features            │
│                 │   │+ set_result()│   │                    │
│Signals:         │   │             │   │                    │
│visibility_changed│   │Signals:     │   │                    │
└─────────────────┘   │accepted()   │   └────────────────────┘
                      │rejected()   │
                      └─────────────┘
```

## Component Organization

```
presentation/canvas/ui/
│
├── Base Layer (Foundation)
│   └── base_widget.py
│       ├── BaseWidget (ABC)
│       ├── BaseDockWidget (BaseWidget)
│       └── BaseDialog (BaseWidget)
│
├── Panels Layer (Dockable Components)
│   ├── properties_panel.py
│   │   ├── PropertiesPanel (QDockWidget)
│   │   └── CollapsibleSection (QWidget)
│   │
│   ├── debug_panel.py
│   │   └── DebugPanel (QDockWidget)
│   │       └── Tabs: Logs, Console, Breakpoints
│   │
│   ├── variables_panel.py
│   │   ├── VariablesPanel (QDockWidget)
│   │   └── TypeComboDelegate (QStyledItemDelegate)
│   │
│   └── minimap_panel.py
│       ├── MinimapPanel (QWidget)
│       ├── MinimapView (QGraphicsView)
│       └── MinimapChangeTracker
│
├── Toolbars Layer (Action Controls)
│   ├── main_toolbar.py
│   │   └── MainToolbar (QToolBar)
│   │
│   ├── debug_toolbar.py
│   │   └── DebugToolbar (QToolBar)
│   │
│   └── zoom_toolbar.py
│       └── ZoomToolbar (QToolBar)
│
├── Dialogs Layer (Modal Windows)
│   ├── node_properties_dialog.py
│   │   └── NodePropertiesDialog (QDialog)
│   │       └── Tabs: Basic, Advanced
│   │
│   ├── workflow_settings_dialog.py
│   │   └── WorkflowSettingsDialog (QDialog)
│   │       └── Tabs: General, Execution, Variables
│   │
│   └── preferences_dialog.py
│       └── PreferencesDialog (QDialog)
│           └── Tabs: General, Autosave, Editor, Performance
│
└── Widgets Layer (Reusable Controls)
    ├── variable_editor_widget.py
    │   └── VariableEditorWidget (BaseWidget)
    │
    ├── output_console_widget.py
    │   └── OutputConsoleWidget (BaseWidget)
    │
    └── search_widget.py
        └── SearchWidget (BaseWidget)
```

## Signal Flow Diagram

```
┌─────────────┐
│ Main Window │
└──────┬──────┘
       │
       │ creates & connects
       │
       ├─────────────────────────────────────────┐
       │                                         │
       ▼                                         ▼
┌──────────────┐                        ┌────────────────┐
│   Toolbars   │                        │     Panels     │
├──────────────┤                        ├────────────────┤
│MainToolbar   │                        │PropertiesPanel │
│ - run ──────────► workflow_runner ◄───┤DebugPanel      │
│ - save ─────────► workflow_manager    │VariablesPanel  │
│ - undo ─────────► undo_stack          │MinimapPanel    │
│              │                        │                │
│DebugToolbar  │                        │                │
│ - step ─────────► workflow_runner     │                │
│ - debug ────────► debug_manager       │                │
│              │                        │                │
│ZoomToolbar   │                        │                │
│ - zoom ─────────► graph_view          │                │
└──────────────┘                        └────────────────┘
       │                                         │
       └──────────────────┬──────────────────────┘
                          │
                          │ feedback signals
                          │
                          ▼
                 ┌─────────────────┐
                 │ Workflow Runner │
                 ├─────────────────┤
                 │ - node_executed ├──► DebugPanel.add_log()
                 │ - started       ├──► MainToolbar.set_state()
                 │ - stopped       ├──► MainToolbar.set_state()
                 │ - error         ├──► DebugPanel.add_error()
                 └─────────────────┘
```

## Data Flow Patterns

### Pattern 1: User Action → Request Signal → Handler

```
┌──────────┐    request signal    ┌─────────┐    handler    ┌────────────┐
│ Toolbar  ├───────────────────►  │  Main   ├──────────────►│  Business  │
│ (UI)     │                       │ Window  │               │   Logic    │
└──────────┘                       └─────────┘               └────────────┘
   ▲                                                                │
   │                     feedback signal                            │
   └────────────────────────────────────────────────────────────────┘
```

### Pattern 2: State Change → Update Signal → UI Update

```
┌────────────┐   state_changed    ┌─────────┐   update_ui   ┌──────────┐
│  Business  ├───────────────────► │  Panel  ├──────────────►│   Qt     │
│   Logic    │                     │  (UI)   │               │  Widget  │
└────────────┘                     └─────────┘               └──────────┘
```

### Pattern 3: User Input → Validation → Emit Signal

```
┌──────────┐    input    ┌──────────┐   validate   ┌──────────┐   emit    ┌─────────┐
│   User   ├────────────►│  Widget  ├─────────────►│ Convert  ├──────────►│ Signal  │
│          │             │          │               │  Type    │           │         │
└──────────┘             └──────────┘               └──────────┘           └─────────┘
```

## Component Lifecycle

```
┌──────────────────┐
│ Component Init   │
└────────┬─────────┘
         │
         ▼
┌────────────────────────────┐
│ 1. Call super().__init__() │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 2. setup_ui()              │
│    - Create widgets        │
│    - Setup layouts         │
│    - Configure properties  │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 3. apply_stylesheet()      │
│    - Apply dark theme      │
│    - Set custom styles     │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 4. connect_signals()       │
│    - Internal connections  │
│    - Widget events         │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ 5. Mark initialized        │
│    _is_initialized = True  │
└────────┬───────────────────┘
         │
         ▼
┌────────────────────────────┐
│ Component Ready to Use     │
└────────────────────────────┘
```

## Styling Architecture

```
┌────────────────────────────────────────┐
│      BaseWidget Default Styles         │
│  ┌──────────────────────────────────┐  │
│  │ Color Palette:                   │  │
│  │  --bg-main: #252525             │  │
│  │  --bg-panel: #2d2d2d            │  │
│  │  --bg-input: #3d3d3d            │  │
│  │  --text-primary: #e0e0e0        │  │
│  │  --accent: #5a8a9a              │  │
│  │  --border: #4a4a4a              │  │
│  │  --error: #f44747               │  │
│  │  --warning: #cca700             │  │
│  │  --success: #89d185             │  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
                  │
                  │ inherited by
                  │
    ┌─────────────┼──────────────┬──────────────┐
    │             │              │              │
┌───▼───┐   ┌────▼────┐   ┌─────▼─────┐  ┌────▼─────┐
│Panels │   │Toolbars │   │ Dialogs   │  │ Widgets  │
│       │   │         │   │           │  │          │
│Can    │   │Can      │   │Can        │  │Can       │
│override│  │override │   │override   │  │override  │
└───────┘   └─────────┘   └───────────┘  └──────────┘
```

## Error Handling Flow

```
┌──────────────┐
│ User Action  │
└──────┬───────┘
       │
       ▼
┌──────────────────────┐
│  Component Method    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Try/Except Block    │
├──────────────────────┤
│ try:                 │
│   # Operation        │
│ except Exception:    │
│   logger.error()     │
│   # Handle gracefully│
└──────┬───────────────┘
       │
       ├──── Success ────► Continue
       │
       └──── Error ─────► Log → Notify User → Recover
```

## Testing Strategy

```
┌─────────────────────────────────────────┐
│         Component Testing               │
├─────────────────────────────────────────┤
│                                         │
│  Unit Tests:                            │
│  ┌────────────────────────────────┐    │
│  │ - Initialization               │    │
│  │ - Signal emission              │    │
│  │ - State management             │    │
│  │ - Widget creation              │    │
│  │ - Validation logic             │    │
│  └────────────────────────────────┘    │
│                                         │
│  Integration Tests:                     │
│  ┌────────────────────────────────┐    │
│  │ - Signal/slot connections      │    │
│  │ - Component interactions       │    │
│  │ - Data flow                    │    │
│  │ - State synchronization        │    │
│  └────────────────────────────────┘    │
│                                         │
│  UI Tests:                              │
│  ┌────────────────────────────────┐    │
│  │ - User interactions            │    │
│  │ - Keyboard navigation          │    │
│  │ - Visual rendering             │    │
│  │ - Responsive behavior          │    │
│  └────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

## Extension Points

Components are designed for extension:

1. **Custom Stylesheets**: Override `apply_stylesheet()`
2. **Additional Signals**: Add component-specific signals
3. **Custom Validation**: Override `validate()` in dialogs
4. **State Persistence**: Use `set_state()` / `get_state()`
5. **Event Filters**: Install event filters for custom behavior

```python
class CustomPanel(BaseDockWidget):
    # Custom signal
    custom_event = Signal(str)

    def apply_stylesheet(self) -> None:
        # Custom styling
        super().apply_stylesheet()
        self.setStyleSheet(self.styleSheet() + """
            /* Additional custom styles */
        """)

    def setup_ui(self) -> None:
        # Custom UI elements
        pass

    def connect_signals(self) -> None:
        # Custom signal connections
        pass
```

## Performance Considerations

1. **Lazy Loading**: MinimapPanel uses event-driven updates
2. **Signal Optimization**: Use `blockSignals()` during batch updates
3. **Widget Reuse**: Cache expensive widgets
4. **Deferred Rendering**: Update UI only when visible
5. **Efficient Layouts**: Use proper size policies

```
Performance Optimizations:
┌──────────────────────────┐
│ MinimapChangeTracker     │ ← Event sourcing pattern
│ - Only update on change  │
│ - Debounce updates       │
└──────────────────────────┘

┌──────────────────────────┐
│ OutputConsoleWidget      │ ← Line limiting
│ - Max 1000 lines         │
│ - Remove old entries     │
└──────────────────────────┘

┌──────────────────────────┐
│ SearchWidget             │ ← Fuzzy matching
│ - Custom match function  │
│ - Filter on type         │
└──────────────────────────┘
```

---

**Architecture Status**: ✅ STABLE
**Version**: 1.0.0
**Last Updated**: November 27, 2025
