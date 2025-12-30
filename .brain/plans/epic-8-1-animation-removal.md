# Epic 8.1: Remove All Animations and Shadows from Canvas

**Created**: 2025-12-30
**Status**: PLAN
**Epic**: Zero-Motion Canvas Design

## Overview

Remove all QPropertyAnimation/QVariantAnimation instances and QGraphicsDropShadowEffect
from the Canvas presentation layer. Replace with instant state changes and crisp 1px borders.

**Policy Reference**: TOKENS_V2.motion (all 0ms durations) - zero-motion is already the standard.

---

## Files to Modify

### Animations (9 files)

| File | Animation Type | Lines | Agent |
|------|---------------|-------|-------|
| `ui/widgets/toast.py` | QPropertyAnimation fade (150ms) | ~20 | builder |
| `ui/widgets/collapsible_section.py` | QPropertyAnimation height (200ms) | ~30 | builder |
| `ui/widgets/node_output_popup.py` | QPropertyAnimation fade (150ms) | ~15 | builder |
| `ui/widgets/expression_editor/expression_editor_popup.py` | QPropertyAnimation fade (150ms) | ~15 | builder |
| `controllers/viewport_controller.py` | QVariantAnimation zoom (medium) | ~60 | builder |
| `graph/auto_layout_manager.py` | QPropertyAnimation position (300ms) | ~80 | builder |
| `graph/focus_ring.py` | QPropertyAnimation pulse (1500ms loop) | ~40 | builder |
| `graph/node_aligner.py` | QPropertyAnimation position (duration) | ~50 | builder |
| `ui/widgets/ai_assistant/chat_area.py` | QPropertyAnimation scroll (300ms) | ~10 | builder |

### Shadows (7 files)

| File | Shadow Type | Lines | Agent |
|------|-------------|-------|-------|
| `ui/widgets/node_output_popup.py` | QGraphicsDropShadowEffect (blur=20) | ~10 | builder |
| `ui/widgets/expression_editor/expression_editor_popup.py` | QGraphicsDropShadowEffect (blur=20) | ~10 | builder |
| `graph/focus_ring.py` | QGraphicsDropShadowEffect (blur=20) | ~25 | builder |
| `connections/shake_to_detach.py` | QGraphicsDropShadowEffect (blur=30) | ~15 | builder |
| `ui/widgets/context_menu.py` | QGraphicsDropShadowEffect (blur=16) | ~10 | builder |
| `ui/panels/port_legend_panel.py` | QGraphicsDropShadowEffect (blur=16) | ~10 | builder |
| `ui/widgets/collapsible_section.py` | QGraphicsDropShadowEffect (blur=16) | ~10 | builder |

**Total**: 16 files, ~400 lines of animation/shadow code to remove/replace.

---

## Change Specifications

### 1. Toast Notifications (`ui/widgets/toast.py`)

**Current**: Fade-in/fade-out with 150ms QPropertyAnimation on windowOpacity

**Change**:
```python
# BEFORE:
def _fade_in(self) -> None:
    self.setWindowOpacity(0.0)
    self.show()
    self._animation = QPropertyAnimation(self, b"windowOpacity")
    self._animation.setDuration(150)
    self._animation.setStartValue(0.0)
    self._animation.setEndValue(1.0)
    self._animation.start()

# AFTER:
def _fade_in(self) -> None:
    self.setWindowOpacity(1.0)  # Instant, no animation
    self.show()
```

**Also remove**: `_animation` attribute, `QPropertyAnimation`, `QEasingCurve` imports

---

### 2. Collapsible Section (`ui/widgets/collapsible_section.py`)

**Current**: Animated height expand/collapse with QPropertyAnimation

**Change**:
```python
# BEFORE:
def _animate_toggle(self) -> None:
    self._animation = QPropertyAnimation(self._content_frame, b"maximumHeight")
    self._animation.setDuration(TOKENS.transitions.medium)  # 200ms
    self._animation.setStartValue(0)
    self._animation.setEndValue(self._content_height)
    self._animation.start()

# AFTER:
def _animate_toggle(self) -> None:
    # Instant toggle - always call _instant_toggle
    self._instant_toggle()

# OR refactor setExpanded to always skip animation:
def setExpanded(self, expanded: bool, animate: bool = False) -> None:
    # animate param ignored - always instant
```

**Also remove**: `_animation` attribute, animation imports, `animate` parameter logic

---

### 3. Node Output Popup (`ui/widgets/node_output_popup.py`)

**Current**: Fade-in animation + drop shadow

**Changes**:

**Remove animation**:
```python
# BEFORE:
def _animate_fade_in(self) -> None:
    self.setWindowOpacity(0.0)
    self._animation = QPropertyAnimation(self, b"windowOpacity")
    self._animation.setDuration(150)
    self._animation.setStartValue(0.0)
    self._animation.setEndValue(1.0)
    self._animation.start()

# AFTER:
def _animate_fade_in(self) -> None:
    self.setWindowOpacity(1.0)  # Instant
    # No animation
```

**Remove shadow**:
```python
# BEFORE (in __init__):
shadow = QGraphicsDropShadowEffect(self)
shadow.setBlurRadius(20)
shadow.setXOffset(0)
shadow.setYOffset(4)
shadow.setColor(QColor(0, 0, 0, 100))
self.setGraphicsEffect(shadow)

# AFTER:
# No shadow - use 1px border instead (already exists in styles)
# The border in _apply_styles provides sufficient visual separation
```

---

### 4. Expression Editor Popup (`ui/widgets/expression_editor/expression_editor_popup.py`)

**Current**: Fade-in animation + drop shadow

**Changes**: Same pattern as NodeOutputPopup

- Remove `_animate_fade_in()` animation, use `setWindowOpacity(1.0)` and `show()`
- Remove `QGraphicsDropShadowEffect` from `__init__`
- Border in styles already provides visual separation

---

### 5. Viewport Controller - Zoom (`controllers/viewport_controller.py`)

**Current**: Smooth zoom with QVariantAnimation interpolation

**Change**:
```python
# BEFORE:
def smooth_zoom(self, factor: float, center: QPointF | None = None) -> None:
    self._zoom_animation = QVariantAnimation()
    self._zoom_animation.setDuration(TOKENS.transitions.medium)
    self._zoom_animation.setStartValue(float(current_scale))
    self._zoom_animation.setEndValue(float(target_scale))
    self._zoom_animation.valueChanged.connect(self._apply_zoom_step)
    self._zoom_animation.start()

# AFTER:
def smooth_zoom(self, factor: float, center: QPointF | None = None) -> None:
    # Instant zoom - no animation
    graph = self._get_graph()
    if not graph:
        return
    viewer = graph.viewer()
    if not viewer:
        return

    current_scale = viewer.transform().m11()
    target_scale = max(self.MIN_ZOOM, min(current_scale * factor, self.MAX_ZOOM))

    if abs(target_scale - current_scale) < 0.001:
        return

    if center is None:
        viewport_center = viewer.viewport().rect().center()
        center = viewer.mapToScene(viewport_center)

    # Apply transform directly (no animation)
    viewer.resetTransform()
    viewer.scale(target_scale, target_scale)

    # Reposition to keep zoom center stable
    old_pos = viewer.mapFromScene(center)
    new_pos = viewer.mapFromScene(center)
    delta = old_pos - new_pos
    viewer.translate(delta.x(), delta.y())

    # Update display
    self.update_zoom_display(target_scale * 100.0)
```

**Also remove**: `_zoom_animation` attribute, `_apply_zoom_step()` method, animation cleanup in `cleanup()`

---

### 6. Auto Layout Manager (`graph/auto_layout_manager.py`)

**Current**: Animated node positioning with QPropertyAnimation

**Change**:
```python
# BEFORE:
def _apply_positions(self, nodes, positions) -> None:
    if self._options.animate:
        self._animate_positions(nodes, positions)
    else:
        self._set_positions_immediate(nodes, positions)

# AFTER:
def _apply_positions(self, nodes, positions) -> None:
    # Always instant - ignore animate option
    self._set_positions_immediate(nodes, positions)

# Remove _animate_positions() method entirely
# Remove _stop_animations() method
# Remove self._animations list
```

---

### 7. Focus Ring (`graph/focus_ring.py`)

**Current**: Pulsing glow animation with QGraphicsDropShadowEffect

**Change**:
```python
# BEFORE:
def _setup_glow_effect(self) -> None:
    glow = QGraphicsDropShadowEffect()
    glow.setBlurRadius(20)
    glow.setOffset(0, 0)
    glow.setColor(self.RING_COLOR)
    self.setGraphicsEffect(glow)

def _start_pulse(self) -> None:
    self._pulse_animation = QPropertyAnimation(self, b"glowOpacity")
    self._pulse_animation.setDuration(1500)
    self._pulse_animation.setStartValue(0.6)
    self._pulse_animation.setEndValue(1.0)
    self._pulse_animation.setLoopCount(-1)  # Infinite
    self._pulse_animation.start()

# AFTER:
def _setup_glow_effect(self) -> None:
    # No shadow - use solid border only
    # The paint() method already draws a solid ring
    pass

def _start_pulse(self) -> None:
    # No animation - just show the ring
    self._glow_opacity = 1.0
    self.show()

# Remove: _pulse_animation, glowOpacity property, _stop_pulse() animation logic
```

**Note**: The `paint()` method already draws a solid ring. The shadow was just extra glow.

---

### 8. Node Aligner (`graph/node_aligner.py`)

**Current**: Animated position changes during alignment

**Change**: Same pattern as AutoLayoutManager - set positions immediately, remove all animation code.

---

### 9. Chat Area Scroll (`ui/widgets/ai_assistant/chat_area.py`)

**Current**: Smooth scroll to bottom with QPropertyAnimation

**Change**:
```python
# BEFORE:
def _do_scroll(self) -> None:
    scrollbar = self.verticalScrollBar()
    anim = QPropertyAnimation(scrollbar, b"value")
    anim.setDuration(300)
    anim.setStartValue(scrollbar.value())
    anim.setEndValue(scrollbar.maximum())
    anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
    self._scroll_anim = anim

# AFTER:
def _do_scroll(self) -> None:
    scrollbar = self.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())  # Instant
```

---

### 10. Context Menu (`ui/widgets/context_menu.py`)

**Shadow Removal**:
```python
# BEFORE:
shadow = QGraphicsDropShadowEffect(self)
shadow.setBlurRadius(16)
shadow.setXOffset(0)
shadow.setYOffset(4)
shadow.setColor(shadow_color)
self.setGraphicsEffect(shadow)

# AFTER:
# No shadow - border provides separation
```

---

### 11. Port Legend Panel (`ui/panels/port_legend_panel.py`)

**Shadow Removal**: Same pattern - remove `QGraphicsDropShadowEffect`, rely on border.

---

### 12. Shake to Detach (`connections/shake_to_detach.py`)

**Shadow Removal**:
```python
# BEFORE:
def _show_visual_feedback(self, node: BaseNode):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(30)
    effect.setColor(QColor(255, 100, 100, 200))  # Red glow
    effect.setOffset(0, 0)
    view.setGraphicsEffect(effect)
    self._shake_effect = effect
    self._feedback_timer.start(200)

# AFTER:
def _show_visual_feedback(self, node: BaseNode):
    # Instant visual feedback - use border color change
    # This requires the node view to support a "highlight" mode
    # For now, just skip the shadow effect
    pass

# Keep _clear_visual_feedback for cleanup, but it will do nothing
```

---

## Parallel Execution Opportunities

All 16 files can be modified **independently**. No cross-file dependencies.

**Recommended parallelization**:
- **Batch 1** (Animations): toast.py, collapsible_section.py, chat_area.py
- **Batch 2** (Animations): viewport_controller.py, node_aligner.py
- **Batch 3** (Animations): auto_layout_manager.py, focus_ring.py
- **Batch 4** (Popups): node_output_popup.py, expression_editor_popup.py
- **Batch 5** (Shadows): context_menu.py, port_legend_panel.py, shake_to_detach.py

Each batch can run in parallel with a builder agent.

---

## Test Approach

### Manual Verification Checklist

1. **Toast Notifications**: Show/hide instantly, no fade
2. **Collapsible Sections**: Expand/collapse instantly, no slide
3. **Popups**: Appear instantly, no fade-in
4. **Zoom**: Instant zoom, no interpolation
5. **Auto Layout**: Nodes snap to positions instantly
6. **Focus Ring**: Solid ring, no pulsing glow
7. **Node Align**: Snap to grid instantly
8. **Chat Scroll**: Instant scroll to bottom

### Visual Verification

All components should have:
- Crisp 1px borders (already in place)
- No shadow effects
- Instant state changes

### Regression Testing

- [ ] Toast still shows for correct duration
- [ ] Collapsible sections still expand/collapse
- [ ] Popups still position correctly
- [ ] Zoom still works (Ctrl+scroll, zoom buttons)
- [ ] Auto layout still produces valid layouts
- [ ] Focus ring still shows on keyboard navigation
- [ ] Node align still snaps to grid
- [ ] Chat still scrolls to new messages

---

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| User accustomed to smooth zoom may find instant jarring | Low | This is by design (zero-motion policy) |
| Focus ring less visible without pulse | Low | Solid ring still visible; high-contrast mode available |
| Shake gesture feedback less clear | Low | Shake still disconnects wires; feedback is secondary |
| Existing tests may fail on timing | Medium | Update any test assertions about animation duration |

---

## Imports to Remove

Across all files, remove these imports (if unused after changes):

```python
from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QVariantAnimation, QAbstractAnimation
from PySide6.QtWidgets import QGraphicsDropShadowEffect
```

---

## Success Criteria

1. All `QPropertyAnimation` instances removed
2. All `QVariantAnimation` instances removed
3. All `QGraphicsDropShadowEffect` instances removed
4. No `QEasingCurve` usage (except maybe in kept code)
5. All instant state changes work correctly
6. Visual appearance consistent with TOKENS_V2.motion (0ms)

---

## Agent Assignments

| Agent | Task | Files |
|-------|------|-------|
| builder | Remove animations (toast, collapsible, chat) | 3 files |
| builder | Remove animations (viewport, aligner) | 2 files |
| builder | Remove animations (layout, focus_ring) | 2 files |
| builder | Remove animations+shadows (popups) | 2 files |
| builder | Remove shadows (menus, panels) | 3 files |

**Total**: 5 parallel builder tasks, all independent.

---

## Notes

- `toast_v2.py` already has no animations (uses QTimer.singleShot) - NO CHANGE needed
- `TOKENS_V2.motion` already defines all durations as 0ms - this enforces the policy
- Borders are already in place - shadows were redundant visual enhancement

---

## Approval Status

[ ] Plan reviewed
[ ] User approved EXECUTE
