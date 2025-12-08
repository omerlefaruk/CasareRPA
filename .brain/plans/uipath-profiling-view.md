# Plan: UiPath-Style Profiling View

**Date**: 2025-12-08
**Status**: Planning
**Reference**: UiPath Profiling Panel screenshot

---

## Goal

Implement a hierarchical profiling view similar to UiPath's profiling panel that shows:
- Tree structure of executed nodes with parent-child relationships
- Execution duration per node (e.g., "13s 583ms")
- Percentage of total time with color-coded indicators
- Search/filter functionality

---

## UiPath Reference Analysis

```
+------------------------------------------+
| Profiling                          - □ x |
+------------------------------------------+
| 🔍 Search activities                     |
+------------------------------------------+
| v UI Main.xaml • 13s 583ms        100%   | (red)
|   v [M] Main Sequence • 13s 583ms 100%   | (red)
|     > 🌐 Use Browser Edge: Rpa.. 12s 972ms 95.5% | (pink)
|       📊 Read Range Workbook • 85ms  0.6%| (green)
+------------------------------------------+
```

Key Features:
1. **Hierarchical Tree**: Parent nodes contain child activities
2. **Time Display**: Formatted as "Xs Yms"
3. **Percentage Bar**: Visual bar + percentage text
4. **Color Coding**: Red (>80%), Pink (50-80%), Green (<20%)
5. **Icons**: Different icons per node type
6. **Search**: Filter tree by activity name

---

## Implementation Approach

### Option A: New "Profiling" Tab in Debug Panel
- Add alongside Logs, Variables, Call Stack tabs
- Reuse existing debug panel infrastructure
- Pros: Consistent location, less UI clutter
- Cons: Debug panel already has many tabs

### Option B: New Standalone Panel/Dock
- Separate dock widget like Analytics Panel
- Can be positioned anywhere
- Pros: Dedicated space, can be larger
- Cons: Another panel to manage

### Option C: Replace/Enhance Timeline Tab in Analytics
- Currently Timeline shows flat table
- Transform into hierarchical tree view
- Pros: Better use of existing panel
- Cons: Loses current timeline functionality

**Recommendation**: **Option A** - New tab in Debug Panel
- Users expect profiling near debug tools
- Matches UiPath mental model
- EventBus integration already in place

---

## Data Structure

```python
@dataclass
class ProfilingEntry:
    """Single profiling entry for a node execution."""
    node_id: str
    node_name: str
    node_type: str
    start_time: datetime
    end_time: Optional[datetime]
    duration_ms: float
    parent_id: Optional[str]  # For hierarchy
    children: List["ProfilingEntry"]
    percentage: float  # Of total execution time
    status: str  # "completed", "failed", "running"
```

---

## UI Components

### 1. ProfilingTreeWidget (QTreeWidget)

```
Columns:
| Activity Name          | Duration    | % Time |
|------------------------|-------------|--------|
| v Main Sequence        | 13s 583ms   | 100%   |
|   v Use Browser Edge   | 12s 972ms   | 95.5%  |
|     Read Range         | 85ms        | 0.6%   |
```

### 2. PercentageBarDelegate (QStyledItemDelegate)
- Custom delegate for percentage column
- Draws colored progress bar + text
- Colors:
  - `#E74C3C` (red): >= 80%
  - `#F39C12` (orange): >= 50%
  - `#F1C40F` (yellow): >= 20%
  - `#27AE60` (green): < 20%

### 3. Search Bar
- QLineEdit with placeholder "Search activities"
- Filters tree in real-time
- Shows/hides non-matching items

---

## Implementation Steps

### Phase 1: Core ProfilingTab Widget
1. Create `ProfilingTab` widget in debug_panel.py or new file
2. Add QTreeWidget with 3 columns
3. Add search QLineEdit at top
4. Style with dark theme

### Phase 2: Data Collection
1. Subscribe to NODE_EXECUTION_STARTED/COMPLETED events
2. Build hierarchical structure from execution context
3. Calculate percentages based on total duration
4. Track parent-child relationships via call stack

### Phase 3: Custom Percentage Delegate
1. Create QStyledItemDelegate for percentage column
2. Draw progress bar with gradient
3. Color based on percentage value
4. Show percentage text overlay

### Phase 4: Integration
1. Add "Profiling" tab to DebugPanel._tabs
2. Connect to execution events via LazySubscription
3. Clear on new execution start
4. Auto-expand first level

### Phase 5: Polish
1. Add node type icons
2. Add "Expand All" / "Collapse All" buttons
3. Add "Export to CSV" option
4. Double-click to navigate to node

---

## File Changes

### New Files
- `src/casare_rpa/presentation/canvas/ui/widgets/profiling_tree.py`
  - `ProfilingTreeWidget` class
  - `PercentageBarDelegate` class
  - `ProfilingEntry` dataclass

### Modified Files
- `src/casare_rpa/presentation/canvas/ui/debug_panel.py`
  - Add `_create_profiling_tab()` method
  - Add tab to `_tabs` widget
  - Add event handlers for profiling data

---

## Event Flow

```
NODE_EXECUTION_STARTED
    ↓
ProfilingTab._on_node_started(event)
    ↓
Create ProfilingEntry, add to tree
    ↓
NODE_EXECUTION_COMPLETED
    ↓
ProfilingTab._on_node_completed(event)
    ↓
Update entry with duration, calculate percentage
    ↓
Refresh tree display
```

---

## Color Scheme (UiPath-inspired)

| Percentage | Color     | Hex       |
|------------|-----------|-----------|
| >= 90%     | Dark Red  | #C0392B   |
| >= 70%     | Red       | #E74C3C   |
| >= 50%     | Orange    | #F39C12   |
| >= 30%     | Yellow    | #F1C40F   |
| >= 10%     | Light Grn | #2ECC71   |
| < 10%      | Green     | #27AE60   |

---

## Open Questions

1. **Hierarchy Source**: Use call stack depth or explicit parent tracking?
   - Call stack available in debug controller
   - Could infer from subflow execution

2. **Live Updates**: Update tree during execution or only after?
   - UiPath shows progress during execution
   - Requires efficient tree updates

3. **Multiple Runs**: Keep history or clear on each run?
   - UiPath keeps history
   - Could add dropdown to select run

4. **Subflows**: How to represent subflow execution?
   - Show as nested tree
   - Different icon for subflow nodes

---

## Success Criteria

- [ ] Tree displays hierarchical node execution
- [ ] Duration shown in "Xs Yms" format
- [ ] Percentage column with colored progress bar
- [ ] Search filters tree in real-time
- [ ] Updates during execution (not just after)
- [ ] Double-click navigates to node
- [ ] Matches UiPath visual style

---

## Estimated Components

| Component | Lines | Complexity |
|-----------|-------|------------|
| ProfilingTreeWidget | ~200 | Medium |
| PercentageBarDelegate | ~80 | Low |
| ProfilingEntry dataclass | ~30 | Low |
| Debug panel integration | ~50 | Low |
| Event handlers | ~100 | Medium |
| **Total** | ~460 | Medium |
