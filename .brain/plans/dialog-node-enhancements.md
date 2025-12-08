# Dialog Node Enhancements Plan

**Date**: 2025-12-08
**Status**: COMPLETED

## Goal
Enhance existing dialog nodes (TooltipNode, SystemNotificationNode) and add 8 new dialog nodes for comprehensive user interaction capabilities.

## Scope

### 1. TooltipNode Enhancements
**Current properties**: message (essential), duration
**New properties**:
- `bg_color` (STRING, default: "#ffffff") - Background color
- `text_color` (STRING, default: "#000000") - Text color
- `position` (CHOICE, default: "cursor") - Position: cursor, top_left, top_right, bottom_left, bottom_right, center
- `click_to_dismiss` (BOOLEAN, default: False) - Click to close
- `max_width` (INTEGER, default: 400) - Maximum width
- `icon` (CHOICE, default: "none") - Icon: none, info, warning, error, success
- `fade_animation` (BOOLEAN, default: True) - Fade in/out animation

### 2. SystemNotificationNode Enhancements
**Current properties**: title (essential), message (essential), duration, icon_type
**New properties**:
- `action_buttons` (STRING, default: "") - Comma-separated button labels
- `play_sound` (BOOLEAN, default: True) - Play notification sound
- `priority` (CHOICE, default: "normal") - Priority: low, normal, high

**New outputs**:
- `click_action` (BOOLEAN) - True if user clicked notification

### 3. New Nodes

#### a) ConfirmDialogNode
Yes/No confirmation dialog with customizable buttons.
- **Properties**: title, message, icon_type (question/warning/info), always_on_top, button_yes_text, button_no_text
- **Outputs**: confirmed (BOOLEAN), button_clicked (STRING: "yes"/"no"/"cancel")

#### b) ProgressDialogNode
Shows progress bar during long operations.
- **Properties**: title, message (essential), show_percent, allow_cancel, indeterminate
- **Inputs**: value (INTEGER 0-100)
- **Outputs**: canceled (BOOLEAN)

#### c) FilePickerDialogNode
Open file dialog for file selection.
- **Properties**: title, filter (e.g., "*.txt;*.csv"), multi_select, start_directory
- **Outputs**: file_path (STRING or LIST), selected (BOOLEAN)

#### d) FolderPickerDialogNode
Folder selection dialog.
- **Properties**: title, start_directory
- **Outputs**: folder_path (STRING), selected (BOOLEAN)

#### e) ColorPickerDialogNode
Color selection dialog.
- **Properties**: title, initial_color (hex), show_alpha
- **Outputs**: color (STRING hex), selected (BOOLEAN), rgb (DICT with r,g,b,a)

#### f) DateTimePickerDialogNode
Date/time selection dialog.
- **Properties**: title, mode (date/time/datetime), format, min_date, max_date
- **Outputs**: value (STRING), timestamp (INTEGER), selected (BOOLEAN)

#### g) SnackbarNode
Material-style bottom notification bar.
- **Properties**: message (essential), duration, position (bottom_left/bottom_center/bottom_right), action_text, bg_color
- **Outputs**: action_clicked (BOOLEAN), success (BOOLEAN)

#### h) BalloonTipNode
Balloon tooltip anchored to screen position.
- **Properties**: message (essential), title, x, y, duration, icon_type
- **Outputs**: success (BOOLEAN)

## Files to Modify

### 1. Logic Nodes (dialog_nodes.py)
`src/casare_rpa/nodes/system/dialog_nodes.py`
- Enhance TooltipNode
- Enhance SystemNotificationNode
- Add ConfirmDialogNode
- Add ProgressDialogNode
- Add FilePickerDialogNode
- Add FolderPickerDialogNode
- Add ColorPickerDialogNode
- Add DateTimePickerDialogNode
- Add SnackbarNode
- Add BalloonTipNode

### 2. Package Exports (system/__init__.py)
`src/casare_rpa/nodes/system/__init__.py`
- Export all new node classes

### 3. Node Registry (nodes/__init__.py)
`src/casare_rpa/nodes/__init__.py`
- Add to _NODE_REGISTRY dict for lazy loading

### 4. Workflow Loader (workflow_loader.py)
`src/casare_rpa/utils/workflow/workflow_loader.py`
- Import new node classes
- Add to NODE_TYPE_MAP

### 5. Visual Nodes (system/nodes.py)
`src/casare_rpa/presentation/canvas/visual_nodes/system/nodes.py`
- Add VisualConfirmDialogNode
- Add VisualProgressDialogNode
- Add VisualFilePickerDialogNode
- Add VisualFolderPickerDialogNode
- Add VisualColorPickerDialogNode
- Add VisualDateTimePickerDialogNode
- Add VisualSnackbarNode
- Add VisualBalloonTipNode

### 6. Visual Node Package Exports (system/__init__.py)
`src/casare_rpa/presentation/canvas/visual_nodes/system/__init__.py`
- Export all new visual node classes

### 7. Visual Node Registry (visual_nodes/__init__.py)
`src/casare_rpa/presentation/canvas/visual_nodes/__init__.py`
- Add to _VISUAL_NODE_REGISTRY dict

## Implementation Patterns

### Async Dialog Pattern
```python
async def execute(self, context: ExecutionContext) -> ExecutionResult:
    try:
        # Use asyncio.get_event_loop().create_future() for non-blocking Qt dialogs
        future = asyncio.get_event_loop().create_future()

        def on_finished(result):
            if not future.done():
                future.set_result(result)

        dialog.finished.connect(on_finished)
        dialog.show()

        result = await future

        # Process result...
        return {"success": True, "data": {...}, "next_nodes": ["exec_out"]}
    except Exception as e:
        return {"success": False, "error": str(e), "next_nodes": []}
```

### PropertyDef Pattern
```python
@node_schema(
    PropertyDef("property_name", PropertyType.TYPE,
                default=...,
                label="Label",
                tooltip="Tooltip",
                essential=True,  # Shows widget on node
                required=False,  # For optional input ports
                choices=[...],   # For CHOICE type
                min_value=...,   # For INTEGER/FLOAT
                max_value=...,   # For INTEGER/FLOAT
    ),
)
```

### Visual Node Pattern
```python
class VisualXxxNode(VisualNode):
    __identifier__ = "casare_rpa.system"
    NODE_NAME = "Xxx"
    NODE_CATEGORY = "system/dialog"

    def __init__(self) -> None:
        super().__init__()
        # Widgets auto-generated from @node_schema

    def get_node_class(self) -> type:
        return XxxNode

    def setup_ports(self) -> None:
        self.add_exec_input("exec_in")
        self.add_typed_input("input_name", DataType.STRING)
        self.add_exec_output("exec_out")
        self.add_typed_output("output_name", DataType.BOOLEAN)
```

## Implementation Order

1. **Phase 1**: Enhance existing TooltipNode and SystemNotificationNode
2. **Phase 2**: Add simple dialog nodes (ConfirmDialogNode, FilePickerDialogNode, FolderPickerDialogNode)
3. **Phase 3**: Add complex dialog nodes (ColorPickerDialogNode, DateTimePickerDialogNode)
4. **Phase 4**: Add notification nodes (SnackbarNode, BalloonTipNode)
5. **Phase 5**: Add ProgressDialogNode (requires special update handling)
6. **Phase 6**: Register all nodes in 6 files

## Unresolved Questions

1. **ProgressDialogNode**: How to handle updates during execution? Need separate `update_progress()` mechanism or input port for value?
   - **Answer**: Use input port for value - simpler and follows existing patterns

2. **SystemNotificationNode click_action**: Windows toast notifications may not reliably report clicks. Need fallback?
   - **Answer**: Use QSystemTrayIcon.messageClicked signal, document Windows-only limitation

3. **Snackbar positioning**: Fixed position or relative to main window?
   - **Answer**: Screen-relative using QScreen geometry, independent of application windows
