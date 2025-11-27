# TODO Audit - Week 2

## Overview
Total TODOs found: 10
Audit Date: 2025-11-27
Branch: docs/update-week1-summary

## Critical (Must Fix Before Merge)
**Count**: 0

No critical TODOs that would cause immediate bugs or data loss.

## High Priority (Create GitHub Issues)
**Count**: 3

### 1. Visual Highlighting in Selector Validator
**File**: `src/casare_rpa/canvas/selectors/selector_validator.py:252`
**Context**:
```python
# TODO: Implement visual highlighting
# Could draw rectangles over elements or flash them
```
**Impact**: User experience - would help users validate element selectors visually
**Recommendation**: Create GitHub issue for enhanced selector preview feature
**Estimated Effort**: 4-6 hours (requires overlay rendering)

### 2. Path-based Element Expansion
**File**: `src/casare_rpa/canvas/selectors/element_tree_widget.py:372`
**Context**:
```python
def expand_to_element(self, target_element: DesktopElement):
    # TODO: Implement path-based expansion
    # This would require walking up the tree to find the path
    pass
```
**Impact**: User experience - tree navigation would be more intuitive
**Recommendation**: Create GitHub issue for tree navigation enhancement
**Estimated Effort**: 2-3 hours (tree traversal logic)

### 3. Environment Matching for Job Queue
**File**: `src/casare_rpa/orchestrator/job_queue.py:405`
**Context**:
```python
# Check environment match
# TODO: Add environment matching logic
```
**Impact**: Orchestrator functionality - jobs could run on wrong environments
**Recommendation**: Implement environment matching logic before production deployment
**Estimated Effort**: 3-4 hours (requires environment schema definition)
**Action**: Fix this in current session

## Medium Priority (Technical Debt)
**Count**: 4

### 4. Orchestrator Monitor - Pause Jobs
**File**: `src/casare_rpa/orchestrator/monitor_window.py:678`
**Context**:
```python
elif action == "pause":
    # TODO: Implement pause
    pass
```
**Impact**: Missing feature in orchestrator UI
**Recommendation**: Add to backlog for orchestrator enhancements
**Estimated Effort**: 2-3 hours (pause/resume state management)

### 5. Orchestrator Monitor - Start Jobs Now
**File**: `src/casare_rpa/orchestrator/monitor_window.py:681`
**Context**:
```python
elif action == "start":
    # TODO: Implement start now
    pass
```
**Impact**: Missing feature in orchestrator UI
**Recommendation**: Add to backlog for orchestrator enhancements
**Estimated Effort**: 2-3 hours (immediate job execution)

### 6. Orchestrator Monitor - Apply Filters
**File**: `src/casare_rpa/orchestrator/monitor_window.py:713`
**Context**:
```python
def _on_filter_changed(self, filters: Dict):
    # TODO: Apply filters to jobs/robots panels
    pass
```
**Impact**: Missing feature in orchestrator UI
**Recommendation**: Add to backlog for orchestrator enhancements
**Estimated Effort**: 2-3 hours (filter implementation)

### 7. Orchestrator Monitor - New Job Dialog
**File**: `src/casare_rpa/orchestrator/monitor_window.py:719`
**Context**:
```python
def _show_new_job_dialog(self):
    # TODO: Implement new job dialog
    QMessageBox.information(self, "New Job", "New job dialog coming soon...")
```
**Impact**: Missing feature in orchestrator UI
**Recommendation**: Add to backlog for orchestrator enhancements
**Estimated Effort**: 4-6 hours (dialog design and implementation)

## Low Priority (Can Defer)
**Count**: 3

### 8. Example Workflow Controller - Load Implementation
**File**: `src/casare_rpa/presentation/canvas/controllers/example_workflow_controller.py:138`
**Context**:
```python
# TODO: In real implementation, load workflow from file
# For now, just update state
```
**Impact**: This is example/demo code in presentation layer
**Recommendation**: Keep TODO as documentation - this controller is for demonstration purposes
**Action**: None - acceptable for example code

### 9. Example Workflow Controller - Save Implementation
**File**: `src/casare_rpa/presentation/canvas/controllers/example_workflow_controller.py:182`
**Context**:
```python
# TODO: In real implementation, save workflow to file
# For now, just update state
```
**Impact**: This is example/demo code in presentation layer
**Recommendation**: Keep TODO as documentation - this controller is for demonstration purposes
**Action**: None - acceptable for example code

### 10. Robot Tray Icon - Real Icon
**File**: `src/casare_rpa/robot/tray_icon.py:28`
**Context**:
```python
# TODO: Add a real icon
self.tray_icon.setIcon(QIcon.fromTheme("computer"))
```
**Impact**: Cosmetic - uses system default icon instead of branded icon
**Recommendation**: Add to design/branding backlog
**Estimated Effort**: 1 hour (once icon asset is provided)
**Action**: None - acceptable for now

## False Positives (Can Ignore)
**Count**: 0

No false positives found.

## Action Plan

### Immediate Actions (This Session)
1. Fix environment matching logic in job queue (High Priority #3)
2. Add validation to prevent initialization order bugs in CanvasApplication
3. Update pre-commit hooks to enable Ruff with selective ignores
4. Add MyPy for clean architecture layers only

### GitHub Issues to Create
1. **Issue**: Implement visual selector highlighting (#High Priority #1)
2. **Issue**: Add tree path-based expansion (#High Priority #2)
3. **Issue**: Complete orchestrator monitor features (pause, start, filter, new job) (#Medium Priority #4-7)
4. **Issue**: Replace robot tray icon with branded asset (#Low Priority #10)

### Documentation Updates
1. Note in ARCHITECTURE.md that example_workflow_controller is for demonstration only
2. Add note about system icon usage in Robot deployment guide

## Summary

| Priority | Count | Action |
|----------|-------|--------|
| Critical | 0 | - |
| High | 3 | Fix 1, Create 2 issues |
| Medium | 4 | Create 1 combined issue |
| Low | 3 | Create 1 issue, Keep 2 as-is |
| False Positives | 0 | - |

**Total TODOs to fix now**: 1 (environment matching)
**Total GitHub issues to create**: 4
**Total acceptable as-is**: 2 (example code)
**Total deferred**: 7 (tracked via issues)
