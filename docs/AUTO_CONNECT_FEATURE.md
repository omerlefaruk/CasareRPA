# Auto-Connect Feature Documentation

## Overview

The Auto-Connect feature provides intelligent connection suggestions while dragging nodes in the workflow editor. It displays faded connection lines to the nearest compatible ports and allows quick connection/disconnection with right-click.

## Features

### 1. **Visual Connection Suggestions**
- While dragging a node, the system automatically finds the closest compatible ports on nearby nodes
- Displays semi-transparent cyan dashed lines showing suggested connections
- Updates in real-time as you move the node
- Maximum distance threshold: 300 pixels (configurable)

### 2. **Smart Port Matching**
- Execution ports (`exec_in`, `exec_out`) connect only to other execution ports
- Data ports connect only to other data ports
- Prevents duplicate connections
- Considers port compatibility based on naming conventions

### 3. **Quick Connect/Disconnect**
- **Right-click while dragging**: Applies all suggested connections
- **Right-click on stationary node**: Disconnects all connections from that node (both input and output)

## Usage

### Enable/Disable Auto-Connect
1. Open the **View** menu
2. Click **Auto-Connect Nodes** to toggle the feature on/off
3. Check mark indicates the feature is enabled (default: ON)

### Connecting Nodes
1. Select a node and start dragging it
2. Move it near other nodes to see suggested connections (faded cyan lines)
3. While still dragging, right-click to create all suggested connections
4. Release the left mouse button to finish

### Disconnecting Nodes
1. Right-click on any node (without dragging)
2. All connections to/from that node will be removed instantly

## Technical Details

### Architecture

**File**: `src/casare_rpa/gui/auto_connect.py`

**Main Class**: `AutoConnectManager`
- Extends `QObject` for Qt signal/slot support
- Uses event filters to monitor mouse events
- Manages suggestion line graphics items
- Calculates distances and port compatibility

### Key Methods

```python
# Core functionality
set_active(active: bool)                    # Enable/disable feature
set_max_distance(distance: float)           # Set connection range
_find_closest_connections(node, others)     # Find compatible ports
_draw_suggestion_lines(suggestions)         # Render visual feedback
_apply_suggested_connections()              # Create connections
_disconnect_node(node)                      # Remove all connections

# Port compatibility
_are_ports_compatible(port1, port2)         # Check if ports can connect
_are_nodes_connected(from_node, to_node)    # Check existing connections
```

### Event Flow

```
1. User drags node (Left Mouse + Move)
   ↓
2. eventFilter detects movement
   ↓
3. _update_suggestions() called
   ↓
4. _find_closest_connections() calculates
   ↓
5. _draw_suggestion_lines() renders
   ↓
6. User right-clicks (Right Mouse Press)
   ↓
7. _apply_suggested_connections() or _disconnect_node()
   ↓
8. Connections created/removed
   ↓
9. Suggestions cleared on mouse release
```

### Visual Styling

**Suggestion Lines**:
- Color: Cyan (`QColor(100, 200, 255, 120)`)
- Opacity: 47% (120/255)
- Style: Dashed line (`Qt.PenStyle.DashLine`)
- Width: 2 pixels

### Configuration

**Default Settings**:
- Enabled: `True`
- Max Distance: `300.0` pixels
- Status: Shown in View menu with checkmark

**Programmatic Control**:
```python
# Access via NodeGraphWidget
node_graph.auto_connect.set_active(True)
node_graph.auto_connect.set_max_distance(500)

# Or via convenience methods
node_graph.set_auto_connect_enabled(True)
node_graph.set_auto_connect_distance(500)
```

## Integration Points

### Main Window (`main_window.py`)
- Added `action_auto_connect` QAction
- Toggle action in View menu
- Status tip explains functionality

### Node Graph Widget (`node_graph_widget.py`)
- Creates `AutoConnectManager` instance
- Exposes control methods
- Manages lifecycle

### Application (`app.py`)
- Connects action to node graph
- Initializes feature on startup

## Performance Considerations

1. **Event Filtering**: Monitors all mouse events on graph viewer
2. **Distance Calculation**: Uses Euclidean distance (O(n) per drag update)
3. **Port Iteration**: Checks all ports on visible nodes
4. **Graphics Items**: Creates/destroys line items dynamically

**Optimization**:
- Only processes when feature is active
- Distance threshold limits candidates
- Fails silently on errors to prevent UI disruption

## Error Handling

- All methods wrapped in try-except blocks
- Prints debug messages to console on errors
- Never crashes the application
- Degrades gracefully if NodeGraphQt internals change

## Future Enhancements

1. **Visual Feedback**:
   - Show port highlights on hover
   - Different colors for exec vs data connections
   - Connection strength indicator (distance-based opacity)

2. **Smart Routing**:
   - Prefer connections in execution flow direction
   - Weight by node type compatibility
   - Learn from user connection patterns

3. **Customization**:
   - User-configurable distance threshold (GUI slider)
   - Color scheme preferences
   - Toggle per connection type (exec vs data)

4. **Advanced Features**:
   - Multi-node selection support
   - Connection templates/presets
   - Magnetic snap-to-align on compatible ports

## Troubleshooting

### Suggestions not appearing
- Check if feature is enabled in View menu
- Ensure nodes are within 300 pixels
- Verify ports are compatible (exec to exec, data to data)

### Right-click not connecting
- Must be actively dragging with left mouse button
- Suggestion lines must be visible
- Check console for error messages

### Disconnection not working
- Must right-click directly on node
- Node must have existing connections
- Don't drag the node while right-clicking

## Testing

Manual test steps:
1. Create two nodes (e.g., Start and End)
2. Drag one node near the other
3. Verify faded cyan lines appear
4. Right-click while dragging to connect
5. Verify connection is created
6. Right-click on node (not dragging) to disconnect
7. Verify all connections removed

## Version History

- **v0.1.0** (2025-11-23): Initial implementation
  - Basic auto-connect with distance threshold
  - Right-click connect/disconnect
  - Visual feedback with faded lines
  - Menu toggle in View menu
