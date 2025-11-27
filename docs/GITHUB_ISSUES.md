# GitHub Issues - Code Quality Improvements

This document contains GitHub issues to be created for tracking deferred work from the Week 2 code quality audit.

---

## Issue 1: Implement Visual Selector Highlighting

**Title**: Implement visual selector highlighting in element validator

**Labels**: enhancement, ui-ux, good-first-issue

**Priority**: High

**Description**:
Add visual highlighting capability to the selector validator to help users validate element selectors by drawing overlay rectangles or flashing matched elements.

**Current Behavior**:
When users validate a selector, matching elements are only logged to the console. There is no visual feedback showing which elements were matched.

**Expected Behavior**:
When validation finds matching elements, they should be visually highlighted on the target window/application using overlay rectangles or a flash effect.

**Technical Details**:
- File: `src/casare_rpa/canvas/selectors/selector_validator.py:252`
- TODO comment: `# TODO: Implement visual highlighting`
- Requires:
  - Overlay window creation (transparent, always-on-top)
  - Drawing rectangles around element bounding boxes
  - Optional flash animation
  - Cleanup after timeout (e.g., 3 seconds)

**Estimated Effort**: 4-6 hours

**Implementation Hints**:
```python
def highlight_matches(self, max_count: int = 10) -> None:
    """Highlight matching elements with visual overlay."""
    try:
        elements = find_elements(self.parent_control, selector, max_depth=10)
        elements = elements[:max_count]

        # Create overlay window for each element
        for element in elements:
            bounds = element.get_bounding_rect()
            overlay = HighlightOverlay(bounds)
            overlay.show()
            # Auto-close after 3 seconds
    except Exception as e:
        logger.error(f"Failed to highlight matches: {e}")
```

**Acceptance Criteria**:
- [ ] Visual overlay appears on matched elements
- [ ] Overlay disappears after timeout
- [ ] Works with multiple elements simultaneously
- [ ] No crashes if element becomes invalid during highlight
- [ ] User can dismiss highlights manually

---

## Issue 2: Add Tree Path-Based Element Expansion

**Title**: Implement path-based tree expansion in element tree widget

**Labels**: enhancement, ui-ux, good-first-issue

**Priority**: High

**Description**:
Add the ability to automatically expand the element tree to show and select a specific element by walking up its parent hierarchy.

**Current Behavior**:
The `expand_to_element()` method exists but is not implemented. Users must manually expand tree nodes to navigate to a specific element.

**Expected Behavior**:
When `expand_to_element(target)` is called, the tree should automatically expand all parent nodes and scroll to make the target element visible.

**Technical Details**:
- File: `src/casare_rpa/canvas/selectors/element_tree_widget.py:372`
- TODO comment: `# TODO: Implement path-based expansion`
- Requires:
  - Walk up element hierarchy to root
  - Find corresponding tree items
  - Expand each parent node
  - Scroll to and select target item

**Estimated Effort**: 2-3 hours

**Implementation Hints**:
```python
def expand_to_element(self, target_element: DesktopElement):
    """Expand tree to show and select a specific element."""
    # Build path from target to root
    path = []
    current = target_element
    while current:
        path.append(current)
        current = current.parent
    path.reverse()

    # Expand tree following path
    current_item = self.invisibleRootItem()
    for element in path:
        for i in range(current_item.childCount()):
            child = current_item.child(i)
            if child.data(0, Qt.UserRole) == element:
                child.setExpanded(True)
                current_item = child
                break

    # Select and scroll to target
    if current_item:
        self.setCurrentItem(current_item)
        self.scrollToItem(current_item)
```

**Acceptance Criteria**:
- [ ] Tree expands automatically to show target element
- [ ] Target element is selected and visible
- [ ] Works for deeply nested elements
- [ ] Handles missing elements gracefully
- [ ] No performance issues with large trees

---

## Issue 3: Complete Orchestrator Monitor Features

**Title**: Implement remaining orchestrator monitor window features

**Labels**: enhancement, orchestrator, feature

**Priority**: Medium

**Description**:
Complete the orchestrator monitor window by implementing the following features:
1. Pause/resume jobs
2. Start jobs immediately (skip schedule)
3. Apply filters to jobs/robots panels
4. New job creation dialog

**Current Behavior**:
These menu actions exist but show "coming soon" messages or do nothing.

**Expected Behavior**:
All orchestrator monitor features should be fully functional.

**Technical Details**:

### Feature 1: Pause Jobs
- File: `src/casare_rpa/orchestrator/monitor_window.py:678`
- Requires: Job state machine support for PAUSED state
- Estimated effort: 2-3 hours

### Feature 2: Start Now
- File: `src/casare_rpa/orchestrator/monitor_window.py:681`
- Requires: Bypass schedule and queue job immediately
- Estimated effort: 2-3 hours

### Feature 3: Apply Filters
- File: `src/casare_rpa/orchestrator/monitor_window.py:713`
- Requires: Filter implementation for jobs/robots tables
- Estimated effort: 2-3 hours

### Feature 4: New Job Dialog
- File: `src/casare_rpa/orchestrator/monitor_window.py:719`
- Requires: Dialog UI for job creation
- Estimated effort: 4-6 hours

**Total Estimated Effort**: 10-15 hours

**Acceptance Criteria**:
- [ ] Can pause and resume running jobs
- [ ] Can start scheduled jobs immediately
- [ ] Filters work on all panels (jobs, robots, workflows)
- [ ] Can create new jobs via dialog
- [ ] All actions have proper error handling
- [ ] Changes persist across restarts

**Implementation Notes**:
These features are independent and can be implemented in separate PRs if preferred.

---

## Issue 4: Fix Remaining Ruff Linting Errors

**Title**: Fix 108 Ruff linting errors in legacy code

**Labels**: code-quality, good-first-issue, refactoring

**Priority**: Medium

**Description**:
Fix the 108 Ruff linting errors that were ignored during Week 2 refactoring. These are currently bypassed in pre-commit hooks but should be addressed incrementally.

**Error Breakdown**:
- E402 (module import not at top of file): ~90 errors
- F401 (unused imports): ~10 errors
- F821 (undefined name): 6 errors
- F841 (unused variable): 2 errors

**Current State**:
Pre-commit config ignores these errors:
```yaml
args:
  - --ignore=E402,F401,F821,F841
```

**Expected Behavior**:
All code should pass Ruff linting without ignores.

**Implementation Strategy**:
1. Run `ruff check src/casare_rpa/ --select=E402,F401,F821,F841` to see all errors
2. Fix errors in batches by module:
   - Canvas/UI layer (~60 errors)
   - Orchestrator (~20 errors)
   - Robot (~15 errors)
   - Core/Nodes (~13 errors)
3. Remove corresponding ignore from pre-commit config after each batch
4. Verify tests still pass after each batch

**Estimated Effort**: 8-12 hours total (can be split across multiple PRs)

**Acceptance Criteria**:
- [ ] Zero E402 errors (imports at top)
- [ ] Zero F401 errors (no unused imports)
- [ ] Zero F821 errors (all names defined)
- [ ] Zero F841 errors (no unused variables)
- [ ] Pre-commit hook runs without --ignore flags
- [ ] All tests passing
- [ ] No functionality broken

**Good First Issue**: Yes - can be tackled file by file

---

## Issue 5: Add Branded Icon for Robot Tray

**Title**: Replace system default icon with branded CasareRPA icon for Robot tray

**Labels**: design, enhancement, ui-ux

**Priority**: Low

**Description**:
The Robot tray icon currently uses the system default "computer" icon. Replace with a proper branded CasareRPA icon.

**Current Behavior**:
```python
# File: src/casare_rpa/robot/tray_icon.py:28
# TODO: Add a real icon
self.tray_icon.setIcon(QIcon.fromTheme("computer"))
```

**Expected Behavior**:
Display a custom CasareRPA robot icon in the system tray.

**Technical Details**:
- Requires: Icon asset file (PNG or SVG)
- Formats needed: 16x16, 32x32, 64x64 (for different DPI)
- Should be added to: `src/casare_rpa/resources/icons/robot_tray.png`
- Update code to load from resource file

**Estimated Effort**: 1 hour (once icon asset is provided by designer)

**Implementation**:
```python
icon_path = Path(__file__).parent.parent / "resources" / "icons" / "robot_tray.png"
self.tray_icon.setIcon(QIcon(str(icon_path)))
```

**Acceptance Criteria**:
- [ ] Icon displays correctly in system tray
- [ ] Icon visible on Windows 10/11
- [ ] Icon scales properly for different DPI settings
- [ ] Icon file included in PyInstaller bundle
- [ ] Fallback to system icon if resource missing

**Blockers**:
- Waiting on icon asset from design team

---

## Summary

| Issue | Title | Priority | Effort | Labels |
|-------|-------|----------|--------|--------|
| #1 | Visual selector highlighting | High | 4-6h | enhancement, ui-ux, good-first-issue |
| #2 | Tree path expansion | High | 2-3h | enhancement, ui-ux, good-first-issue |
| #3 | Orchestrator monitor features | Medium | 10-15h | enhancement, orchestrator, feature |
| #4 | Fix Ruff linting errors | Medium | 8-12h | code-quality, good-first-issue, refactoring |
| #5 | Branded robot icon | Low | 1h | design, enhancement, ui-ux |

**Total Estimated Effort**: 25-37 hours

**Recommended Priority Order**:
1. Issue #4 (Ruff errors) - Improves code quality foundation
2. Issue #1 (Visual highlighting) - High user value
3. Issue #2 (Tree expansion) - High user value
4. Issue #3 (Orchestrator features) - Complete existing functionality
5. Issue #5 (Robot icon) - Polish/branding

**Good First Issues**: #1, #2, and #4 are suitable for new contributors
