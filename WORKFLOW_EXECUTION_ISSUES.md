# Workflow Execution Issues - Investigation Report

## Problem Summary
Workflow execution fails with `EMPTY_WORKFLOW` error even when nodes are present on the canvas.

## Root Causes Identified

### 1. Missing Graph Widget Initialization
**File:** `src/casare_rpa/presentation/canvas/main_window.py`

**Issue:** The `self.graph` attribute is accessed (line 1315) but never initialized:
```python
def get_graph(self):
    return self.graph  # ❌ AttributeError: 'MainWindow' object has no attribute 'graph'
```

**Impact:** Any code trying to access the graph widget will fail, preventing workflow serialization.

### 2. Workflow Data Provider Not Configured
**File:** `src/casare_rpa/presentation/canvas/main_window.py:1422-1429`

**Issue:** The `_workflow_data_provider` callback is initialized to `None` but never set:
```python
def _get_workflow_data(self) -> Optional[dict]:
    if self._workflow_data_provider:  # Always None
        try:
            return self._workflow_data_provider()
        except Exception as e:
            logger.debug(f"Workflow data provider failed: {e}")
    return None  # ❌ Always returns None
```

**Impact:** Validation always sees an empty workflow because no data is provided.

### 3. Missing Graph-to-JSON Serialization
**Status:** No serialization method found in controllers or main window.

**Expected:** A method like:
```python
def serialize_workflow(self) -> dict:
    """Convert current graph state to workflow JSON."""
    graph = self.get_graph()
    nodes = []
    for node in graph.all_nodes():
        nodes.append({
            "id": node.get_property("node_id"),
            "type": node.type_,
            "position": node.pos(),
            "properties": node.get_properties()
        })
    # ... connections, variables, etc
    return {"nodes": nodes, "connections": [...]}
```

**Actual:** Missing entirely.

## Execution Flow Analysis

### Expected Flow
1. User clicks "Run" (F3)
2. `ExecutionController.run_workflow()` emits `execution_started` signal
3. `MainWindow.workflow_run` signal emitted
4. **[MISSING]** Listener serializes graph to workflow JSON
5. **[MISSING]** Executor receives workflow dict and runs nodes
6. Visual feedback updates

### Actual Flow
1. User clicks "Run" (F3) ✅
2. Signals emitted ✅
3. **BREAKS HERE** - No graph serialization, no executor

## Related Files to Investigate

1. **Graph Widget Creation:**
   - Where should `NodeGraphQt.NodeGraph()` be instantiated?
   - Who should own the graph widget lifecycle?

2. **Workflow Serialization:**
   - `src/casare_rpa/utils/workflow/` - any serializers?
   - Does `WorkflowController` handle this?

3. **Execution Engine:**
   - Who listens to `workflow_run` signal?
   - Is there a `WorkflowExecutor` class?
   - Check `src/casare_rpa/robot/job_executor.py` (Robot component)

## Recommendations

### Short-term Fixes (This PR)
1. ✅ Fix crash bugs (eventFilter, missing modules)
2. ✅ Fix asset paths
3. ❌ Workflow execution requires architectural work (separate issue)

### Long-term (New Issue/PR)
1. Initialize graph widget properly in `MainWindow`
2. Create `WorkflowSerializer` to convert graph → JSON
3. Wire `workflow_run` signal to execution engine
4. Set `_workflow_data_provider` to serializer method

## Test Results

### Manual Test Script
**File:** `test_workflow_execution.py`

**Status:** Nodes execute correctly when called directly:
```python
context = ExecutionContext()
start = StartNode(node_id="start_1")
assign = AssignNode(node_id="assign_1")
msgbox = MessageBoxNode(node_id="msgbox_1")

start.execute(context)  # ✅ Works
assign.execute(context)  # ✅ Works
msgbox.execute(context)  # ✅ Would work if QApplication exists
```

**Conclusion:** Node execution logic is functional. Issue is in canvas→execution pipeline.

---

**Date:** 2025-11-28
**Investigator:** Claude Code
**Status:** Architectural gap identified, not a simple bug fix
