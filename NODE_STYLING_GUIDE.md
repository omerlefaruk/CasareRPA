# Node Visual Styling - Implementation Guide

## Overview
Enhanced node visual appearance with:
- Dark themed nodes with rounded corners
- Bright yellow selection borders
- Animated execution states
- Completion indicators
- Temporary icon placeholders
- Dotted connection lines while dragging

## Implemented Features

### 1. Node Appearance
- **Background**: Dark gray (#2d2d2d)
- **Border**: Dark gray (#444444) when idle
- **Selection Border**: Bright yellow (#FFD700) - 2px solid
- **Corner Radius**: 8px rounded corners
- **Text**: Light gray (#DCDCDC) with medium weight font

### 2. Execution States

#### Idle State
- Normal dark background
- Dark gray border
- No special indicators

#### Running State
- **Border**: Bright yellow (#FFD700)
- **Style**: Dotted/dashed line
- **Animation**: Dash pattern moves around the node (animated)
- Border appears to "chase" around the node perimeter

#### Completed State
- Returns to normal appearance
- **Checkmark**: Green circle with white checkmark in top-right corner
- Checkmark size: 20x20px
- Position: 8px from top-right corner

#### Error State
- **Background**: Red (#F44336)
- **Border**: Red (#F44336)
- Checkmark removed

### 3. Icons
- **Temporary placeholders**: Colored rounded squares (24x24px)
- **Position**: Left side of node, 12px from edges
- **Colors by category**:
  - Basic: Light blue (#64B5F6)
  - Browser: Purple (#9C27B0)
  - Navigation: Blue (#42A5F5)
  - Interaction: Orange (#FFA726)
  - Data: Green (#66BB6A)
  - Wait: Yellow (#FFCA28)
  - Variable: Deep purple (#AB47BC)

### 4. Connection Lines
- **Default**: Gray (#646464) solid curved lines
- **While Dragging**: Gray dotted line with 4px dash pattern
- **Style**: Cubic bezier curves

## File Structure

```
src/casare_rpa/gui/
├── custom_node_item.py      # Custom node graphics with animations
├── custom_pipe.py            # Custom connection line styling
├── visual_nodes.py           # Updated with new styling
└── node_graph_widget.py      # Graph configuration
```

## Usage

### Updating Node Status

```python
# In workflow execution
visual_node.update_status("running")   # Shows yellow animated border
visual_node.update_status("success")   # Shows checkmark
visual_node.update_status("error")     # Shows red background
visual_node.update_status("idle")      # Returns to normal
```

### Adding Custom Icons (Future)

Icons are currently placeholders. To add real icons:

1. Create 24x24px SVG or PNG icons for each node type
2. Place in `src/casare_rpa/gui/icons/` directory
3. Update `_create_temp_icon()` method in `visual_nodes.py` to load actual icons

Example:
```python
def _get_node_icon(self) -> str:
    icon_map = {
        'VisualStartNode': 'icons/start.svg',
        'VisualClickElementNode': 'icons/click.svg',
        # etc...
    }
    return icon_map.get(self.__class__.__name__, 'icons/default.svg')
```

## Animation Details

### Running Border Animation
- **Frame Rate**: 20 FPS (50ms intervals)
- **Dash Pattern**: [4, 4] (4px dash, 4px gap)
- **Offset Increment**: 1px per frame
- **Loop**: Resets after 8px offset

### Checkmark Drawing
- **Shape**: SVG-like path
- **Stroke**: 2px white
- **Background**: 10px radius green circle (#4CAF50)
- **Path**: 
  - Start: 25% from left, 50% from top
  - Middle: 45% from left, 70% from top  
  - End: 75% from left, 30% from top

## Testing

To test the visual states:

```python
# Get a node in the graph
node = graph.get_node_by_name("My Node")

# Test each state
node.update_status("running")  # Should show animated yellow border
await asyncio.sleep(2)
node.update_status("success")  # Should show checkmark
await asyncio.sleep(1)
node.update_status("idle")     # Should return to normal
```

## Future Enhancements

1. **Replace Placeholder Icons**
   - Design icon set for all node types
   - Add icon loading system
   - Support SVG for scalability

2. **Additional States**
   - Paused state (yellow solid border, no animation)
   - Skipped state (gray, semi-transparent)
   - Breakpoint indicator (red dot)

3. **Enhanced Animations**
   - Fade transitions between states
   - Pulse effect on error
   - Glow effect on completion

4. **Accessibility**
   - Ensure color contrast meets WCAG standards
   - Add text labels for states
   - Support screen readers

## Notes

- NodeGraphQt caching may prevent immediate visual updates in some cases
- Call `node.view.update()` to force refresh if needed
- Animation timers are automatically cleaned up when nodes are deleted
- Custom node items inherit from NodeGraphQt's NodeItem class
