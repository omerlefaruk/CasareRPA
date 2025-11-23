# Auto-Connect Testing Guide

## Current Status
✅ Code fixed with enhanced debugging
✅ Event filters installed on viewer, viewport, and scene
✅ Context menu suppression added
✅ Debug print statements added

## How to Test

### 1. Start the Application
```bash
.\.venv\Scripts\Activate.ps1
python run.py
```

### 2. Expected Console Output on Startup
You should see:
```
Installed event filter on viewer: NodeViewer
Installed event filter on viewport: QWidget
Installed event filter on scene: NodeScene
```

### 3. Test Auto-Connect

#### Test 1: Connect Nodes
1. Create two nodes (e.g., Start and End)
2. **Click and hold LEFT mouse button** on Start node
3. **While holding LMB, drag** the node near End node
4. **Watch console** - you should see:
   ```
   Started dragging node: Start
   ```
5. You should see **faded cyan dashed lines** appear
6. **While still holding LMB, click RIGHT mouse button**
7. **Watch console** - you should see:
   ```
   Right-click detected. Dragging: True
   Processing right-click while dragging. Suggestions: 1
   Connected: Start.exec_out -> End.exec_in
   Blocking context menu during drag
   ```
8. Release LMB
9. **Verify**: Connection should be created, NO context menu should appear

#### Test 2: Disconnect Node
1. Use a connected node from Test 1
2. **Click and hold LMB** on Start node
3. **Drag it far away** from other nodes (>300 pixels)
4. **No cyan lines should appear**
5. **While holding LMB, click RMB**
6. **Watch console**:
   ```
   Right-click detected. Dragging: True
   Processing right-click while dragging. Suggestions: 0
   Disconnected 1 connection(s) from node: Start
   Blocking context menu during drag
   ```
7. Release LMB
8. **Verify**: Connection removed, NO context menu

#### Test 3: Normal Context Menu (Not Dragging)
1. Right-click on a node **WITHOUT dragging**
2. **Verify**: Normal context menu appears
3. **Console should NOT show** "Blocking context menu"

## Troubleshooting

### Issue: Context Menu Still Appears While Dragging
**Check console for:**
- "Started dragging node: ..." - If missing, drag detection failed
- "Blocking context menu during drag" - If missing, event filter not working

**Possible causes:**
1. Event filter not installed on correct widget
2. NodeGraphQt handling context menu before our filter
3. Need to override NodeGraphQt's context menu handler

### Issue: Auto-Connect Not Working
**Check console for:**
- "Started dragging node: ..." - Should appear when dragging
- "Right-click detected. Dragging: True" - Should appear on RMB press
- "Processing right-click while dragging" - Should appear when handling

**If you see "Dragging: False":**
- The drag state wasn't detected
- Try dragging more before right-clicking

### Issue: No Cyan Lines Appear
**Check:**
- Nodes are within 300 pixels
- Ports are compatible (exec-to-exec or data-to-data)
- Auto-connect is enabled in View menu

## Debug Output Reference

### Normal Operation
```
# On startup
Installed event filter on viewer: NodeViewer
Installed event filter on viewport: QWidget  
Installed event filter on scene: NodeScene

# When dragging starts
Started dragging node: Start

# When right-clicking while dragging
Right-click detected. Dragging: True
Processing right-click while dragging. Suggestions: 1
Connected: Start.exec_out -> End.exec_in
Blocking context menu during drag

# When drag ends
Stopped dragging node: Start
```

### No Auto-Connect (Normal Right-Click)
```
Right-click detected. Dragging: False
# (Then normal context menu appears - this is correct)
```

## Next Steps If Still Not Working

If context menu still appears:
1. Check if debug messages appear in console
2. If "Blocking context menu" appears but menu still shows, we need to override NodeGraphQt's context menu method
3. May need to disable viewer's native context menu: `viewer.setContextMenuPolicy(Qt.NoContextMenu)` during drag

If auto-connect not triggering:
1. Verify "Started dragging" message appears
2. Check if right-click is detected ("Right-click detected. Dragging: True")
3. May need to check if NodeGraphQt consumes the event before our filter

## Alternative Approach

If event filtering doesn't work, we can:
1. Override `NodeViewer.contextMenuEvent()` method
2. Subclass NodeViewer and install custom version
3. Use keyboard modifier (Ctrl+RMB) instead of just RMB
