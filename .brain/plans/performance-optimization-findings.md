# CasareRPA Performance Optimization Research Findings

**Date**: 2025-12-05
**Agents**: 10 Architect + 10 Researcher + 10 UI = 30 parallel agents

---

## Executive Summary

### Critical Findings (HIGH IMPACT)

| # | Finding | Location | Category |
|---|---------|----------|----------|
| 1 | **O(n) connection lookups** - Every node execution scans ALL connections | execution_orchestrator.py, variable_resolver.py | Execution |
| 2 | **QPen/QBrush/QFont created in paint()** - 60+ object allocations per frame | custom_node_item.py, custom_pipe.py | GUI |
| 3 | **Double widget creation** - VariableAwareLineEdit creates then replaces standard widget | base_visual_node.py:368-441 | GUI |
| 4 | **Spatial hash not updated on drag** - `update_node_position()` never called | viewport_culling.py:253 | GUI |
| 5 | **Type validators dict rebuilt every call** - 18 lambdas recreated per validation | property_schema.py:176-198 | Execution |
| 6 | **Checkpoint double-serialization** - Tests serializability then serializes again | checkpoint.py:183-193 | Execution |
| 7 | **All EventTypes logging subscription** - 100 subscriptions instead of 1 | execution_controller.py:191-193 | Execution |
| 8 | **Viewport culling timer always runs** - No idle detection, 33ms even when static | node_graph_widget.py:247-250 | GUI |

---

## Architect Agent Findings (Execution Engine)

### 1. Connection Index Maps (P0)
**Files**: execution_orchestrator.py, variable_resolver.py
```python
# Build once at init instead of O(n) per lookup
self._outgoing: Dict[NodeId, List[Connection]] = defaultdict(list)
self._incoming: Dict[NodeId, List[Connection]] = defaultdict(list)
for conn in workflow.connections:
    self._outgoing[conn.source_node].append(conn)
    self._incoming[conn.target_node].append(conn)
```

### 2. Pre-compile Single Variable Regex
**File**: variable_resolver.py:134
```python
# Currently: re.match(r"^\{\{\s*...", stripped) - compiled every call
# Fix: SINGLE_VAR_PATTERN = re.compile(r"^\{\{\s*...")
```

### 3. Cache Metrics Instance
**File**: node_executor.py:130
```python
# Currently: get_metrics().record_node_start() - singleton lookup per call
# Fix: self._metrics = get_metrics() in __init__
```

### 4. Node Type Cache
**File**: execution_orchestrator.py:586-639
```python
# is_control_flow_node() recreates set every call
CONTROL_FLOW_TYPES = frozenset({"IfNode", "SwitchNode", ...})
```

### 5. Browser Context Reuse
**File**: browser_nodes.py:714-716
- NewTabNode creates NEW context per tab (heavyweight)
- Should reuse existing context

### 6. Playwright Instance Singleton
**File**: browser_nodes.py:227-248
- Creates fresh Playwright instance per LaunchBrowser
- Should cache at application level

---

## Researcher Agent Findings (Technology/Best Practices)

### 1. uvloop NOT Viable
- Windows-only platform + qasync = uvloop incompatible
- Current qasync integration is correct choice

### 2. JSON Standardization
- 12 files use orjson, 8 files use stdlib json
- Standardize on orjson for 5-10x speedup

### 3. TaskGroup Migration
- Replace `asyncio.gather()` with `asyncio.TaskGroup()` (Python 3.11+)
- Better error handling + structured concurrency

### 4. Profiling Stack Recommendation
| Use Case | Tool |
|----------|------|
| Development | yappi (async-aware) |
| Production | py-spy (sampling) |
| Line-level | line_profiler |

### 5. Memory Optimization
- Add `__slots__` to Event, Port, BaseNode classes
- Domain EventBus uses list.pop(0) - change to deque
- Page callback registry leaks memory (weakref needed)

### 6. Qt Graphics View
- ItemCoordinateCache may work (unlike DeviceCoordinateCache)
- BSP tree indexing not explicitly configured
- LOD rendering not implemented

---

## UI Agent Findings (Canvas/GUI)

### 1. Paint Method Allocations (Critical)
**Files**: custom_node_item.py:260, custom_pipe.py:49-62
```python
# CURRENT: Creates per frame
painter.setPen(QPen(QColor(76, 175, 80), 2))

# FIX: Class-level cache
_SUCCESS_PEN = QPen(QColor(76, 175, 80), 2)
```

### 2. Font Cache Extension
**File**: custom_node_item.py
- `_time_font` is cached (good)
- Other fonts at line 399 are NOT cached

### 3. Signal Blocking for Batch Updates
**File**: base_visual_node.py:627-821
```python
# Wrap widget creation
self.model.blockSignals(True)
try:
    # create widgets
finally:
    self.model.blockSignals(True)
```

### 4. Lazy Variable Button
**File**: variable_picker.py:1348-1364
- Create button on first hover/focus, not in __init__

### 5. Panel Update Batching
**Files**: log_tab.py:468-517, history_tab.py:489-503
- Batch log/history entries on 16ms timer
- Debounce `_update_tab_badges()` (100-200ms)

### 6. Extend LazySubscription
**File**: lazy_subscription.py
- Only VariablesPanel uses it
- Apply to LogTab, HistoryTab, OutputTab, ValidationTab

### 7. History Filter Optimization
**File**: history_tab.py:248
- Use `setRowHidden()` instead of `setRowCount(0)` + rebuild

### 8. Pipe Visibility O(n)
**File**: viewport_culling.py:367-394
- Iterates ALL pipes every 33ms
- Use spatial hash for pipes too

### 9. LOD Rendering (Not Implemented)
- No zoom-based detail levels
- At zoom < 30%, render rectangles instead of full nodes

### 10. Auto-connect Throttle
**File**: auto_connect.py:132-161
- `_update_suggestions()` runs on every mouse pixel
- Throttle to 60ms intervals

---

## Already Well-Optimized

| Pattern | Location |
|---------|----------|
| AnimationCoordinator singleton | custom_node_item.py:27-98 |
| Viewport culling spatial hash | viewport_culling.py |
| EventBatcher (16ms batching) | event_batcher.py |
| LazySubscription | lazy_subscription.py |
| ResourceCache with LRU | resources.py |
| OpenGL viewport | node_graph_widget.py:476-500 |
| Autosave debounce | ui_state_controller.py:236 |

---

## Priority Implementation Order

### Tier 1: Quick Wins (High Impact, Low Effort)
1. Build connection index maps
2. Cache QPen/QBrush/QFont at class level
3. Pre-compile SINGLE_VAR_PATTERN regex
4. Move type_validators to module constant
5. Wire up `update_node_position()` to drag events

### Tier 2: Medium Effort
6. Direct VariableAwareLineEdit creation path
7. Extend LazySubscription to all panels
8. Batch log/history panel updates
9. Cache metrics instance in NodeExecutor
10. LOD rendering for zoom-out

### Tier 3: Architectural
11. Idle detection for viewport culling timer
12. Node/Pipe object pooling
13. Playwright instance singleton
14. TaskGroup migration

---

## Estimated Impact

| Optimization | CPU Reduction | Memory Reduction |
|--------------|---------------|------------------|
| Connection index | 20-30% execution | - |
| Paint allocations | 10-15% rendering | 5-10% |
| Viewport idle | 5-10% idle | - |
| LazySubscription | 5% UI | - |
| __slots__ | - | 15-20% objects |
| LOD rendering | 30%+ at low zoom | - |
