# Auto-Connect Feature - Quick Reference

## What It Does
Automatically suggests connections between nodes while you drag them, with visual feedback and right-click actions.

## How to Use

### 🔗 Connect Nodes
1. Drag a node near another node
2. See faded cyan dashed lines showing suggested connections
3. **Right-click while dragging** to create those connections
4. Release mouse to finish

### ✂️ Disconnect Node  
**Right-click on a node** (without dragging) to remove ALL its connections

### 🎛️ Toggle Feature
**View Menu → Auto-Connect Nodes** (checkmark = enabled)

## Visual Indicators
- **Faded cyan dashed lines** = suggested connections
- Lines appear within 300 pixels of compatible ports
- Updates in real-time as you drag

## Smart Matching
- ✅ Exec ports connect to exec ports only
- ✅ Data ports connect to data ports only  
- ✅ Won't create duplicate connections
- ✅ Finds closest compatible matches

## Files Modified
1. `src/casare_rpa/gui/auto_connect.py` - NEW (main feature code)
2. `src/casare_rpa/gui/node_graph_widget.py` - Integration
3. `src/casare_rpa/gui/main_window.py` - Menu action
4. `src/casare_rpa/gui/app.py` - Signal connection
5. `src/casare_rpa/gui/__init__.py` - Export

## Configuration
```python
# Programmatic control
node_graph.set_auto_connect_enabled(True/False)
node_graph.set_auto_connect_distance(300)  # pixels
```

## Status
✅ **READY TO USE** - Feature is enabled by default when you start the application
