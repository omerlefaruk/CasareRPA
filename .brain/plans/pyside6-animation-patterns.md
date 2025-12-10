# Research: PySide6/Qt6 Animation Best Practices

**Date**: 2025-12-10
**Status**: COMPLETE
**Topic**: UI Animation Patterns for CasareRPA

---

## Executive Summary

This research covers Qt6 animation framework best practices, modern UI animation patterns, and performance optimization strategies. Key findings:

1. **Duration**: 150-300ms for micro-interactions, 300-500ms for larger transitions
2. **Easing**: Use `OutCubic`/`OutQuad` for most UI, `InOutQuad` for bidirectional
3. **Performance**: Avoid recalculating animations on every input; batch state changes
4. **Accessibility**: Always respect `prefers-reduced-motion`; provide instant alternatives

---

## 1. Qt Animation Framework

### 1.1 QPropertyAnimation Core Patterns

```python
from PySide6.QtCore import QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QGraphicsOpacityEffect

# Pattern 1: Simple property animation
def animate_opacity(widget, start=0.0, end=1.0, duration=150):
    """Standard fade animation pattern."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim

# Pattern 2: Position animation
def animate_slide(widget, start_pos, end_pos, duration=200):
    """Slide animation for panels/dialogs."""
    anim = QPropertyAnimation(widget, b"pos")
    anim.setDuration(duration)
    anim.setStartValue(start_pos)
    anim.setEndValue(end_pos)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
    return anim

# Pattern 3: Window opacity (for dialogs)
def animate_window_opacity(window, start=0.0, end=1.0, duration=150):
    """Animate window transparency (Windows/macOS)."""
    anim = QPropertyAnimation(window, b"windowOpacity")
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.OutCubic)
    anim.start()
    return anim
```

### 1.2 Animation Groups

```python
from PySide6.QtCore import QParallelAnimationGroup, QSequentialAnimationGroup

# Pattern: Parallel animations (fade + slide together)
def animate_popup_show(popup, target_pos):
    """Combined fade-in and slide animation."""
    group = QParallelAnimationGroup()

    # Opacity animation
    opacity_anim = QPropertyAnimation(popup, b"windowOpacity")
    opacity_anim.setDuration(150)
    opacity_anim.setStartValue(0.0)
    opacity_anim.setEndValue(1.0)
    opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    # Position animation (slide up 10px)
    pos_anim = QPropertyAnimation(popup, b"pos")
    pos_anim.setDuration(150)
    pos_anim.setStartValue(QPoint(target_pos.x(), target_pos.y() + 10))
    pos_anim.setEndValue(target_pos)
    pos_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    group.addAnimation(opacity_anim)
    group.addAnimation(pos_anim)
    group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)
    return group

# Pattern: Sequential animations (staggered list items)
def animate_list_items(items, delay_per_item=50):
    """Staggered animation for list items."""
    group = QSequentialAnimationGroup()

    for item in items:
        anim = QPropertyAnimation(item, b"opacity")
        anim.setDuration(100)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        group.addAnimation(anim)
        group.addPause(delay_per_item)

    group.start()
    return group
```

### 1.3 QEasingCurve Selection Guide

| Curve Type | Use Case | Duration |
|------------|----------|----------|
| `Linear` | Progress bars, loaders | N/A |
| `OutCubic` | Fade in, slide in, popup appear | 150-200ms |
| `InCubic` | Fade out, slide out, dismiss | 100-150ms |
| `OutQuad` | Button hover effects | 100-150ms |
| `InOutQuad` | Toggle switches, bidirectional | 200-250ms |
| `OutBack` | Attention-grabbing animations | 200-300ms |
| `OutElastic` | Success states, celebratory | 300-500ms |
| `InOutSine` | Smooth camera/viewport movement | 300-400ms |

```python
# Common easing curve mappings
EASING_MAP = {
    "fade_in": QEasingCurve.Type.OutCubic,
    "fade_out": QEasingCurve.Type.InCubic,
    "slide_in": QEasingCurve.Type.OutCubic,
    "slide_out": QEasingCurve.Type.InCubic,
    "hover": QEasingCurve.Type.OutQuad,
    "toggle": QEasingCurve.Type.InOutQuad,
    "bounce": QEasingCurve.Type.OutBounce,
    "spring": QEasingCurve.Type.OutElastic,
    "viewport": QEasingCurve.Type.InOutSine,
}
```

---

## 2. Animation Duration Guidelines

### 2.1 Material Design / Apple HIG Recommendations

| Component | Enter Duration | Exit Duration | Notes |
|-----------|---------------|---------------|-------|
| Button hover | 100ms | 100ms | Instant feedback |
| Button press | 50-100ms | - | Very fast |
| Tooltip | 150ms | 100ms | Enter slower, exit faster |
| Dropdown menu | 200ms | 150ms | - |
| Modal/Dialog | 250-300ms | 200ms | Larger = slightly slower |
| Panel slide | 200-250ms | 150-200ms | - |
| Page transition | 300-400ms | - | Mobile guideline |
| Notification | 300ms | 200ms | Toast animations |

### 2.2 CasareRPA Specific Recommendations

```python
# Suggested constants for theme.py
class Animations:
    """Animation durations in milliseconds."""

    # Micro-interactions (instant feedback)
    instant: int = 50       # Button press
    fast: int = 100         # Hover states

    # Standard UI transitions
    normal: int = 150       # Fade, slide (default)
    medium: int = 200       # Dropdowns, menus

    # Larger movements
    slow: int = 300         # Modal dialogs
    emphasis: int = 400     # Celebratory animations

    # Viewport/canvas
    viewport: int = 250     # Pan/zoom smoothing
```

---

## 3. Modern UI Animation Patterns

### 3.1 Button Animations

```python
class AnimatedButton(QPushButton):
    """Button with hover/press animations."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setup_animations()

    def _setup_animations(self):
        # Background color animation
        self._bg_anim = QPropertyAnimation(self, b"background_color")
        self._bg_anim.setDuration(100)
        self._bg_anim.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        """Animate to hover state."""
        self._bg_anim.stop()
        self._bg_anim.setStartValue(self._current_bg)
        self._bg_anim.setEndValue(self._hover_bg)
        self._bg_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Animate back to normal state."""
        self._bg_anim.stop()
        self._bg_anim.setStartValue(self._current_bg)
        self._bg_anim.setEndValue(self._normal_bg)
        self._bg_anim.start()
        super().leaveEvent(event)
```

### 3.2 Panel Slide Transitions

```python
class SlidingPanel(QFrame):
    """Panel that slides in/out from edge."""

    def __init__(self, parent, direction="right"):
        super().__init__(parent)
        self._direction = direction
        self._animation = QPropertyAnimation(self, b"pos")
        self._animation.setDuration(200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def show_animated(self):
        """Slide in from off-screen."""
        if self._direction == "right":
            start = QPoint(self.parent().width(), self.y())
            end = QPoint(self.parent().width() - self.width(), self.y())
        elif self._direction == "left":
            start = QPoint(-self.width(), self.y())
            end = QPoint(0, self.y())

        self._animation.setStartValue(start)
        self._animation.setEndValue(end)
        self.show()
        self._animation.start()

    def hide_animated(self):
        """Slide out to off-screen."""
        if self._direction == "right":
            end = QPoint(self.parent().width(), self.y())
        elif self._direction == "left":
            end = QPoint(-self.width(), self.y())

        self._animation.setStartValue(self.pos())
        self._animation.setEndValue(end)
        self._animation.finished.connect(self.hide)
        self._animation.start()
```

### 3.3 Dialog Fade Animation

```python
class FadeDialog(QDialog):
    """Dialog with fade in/out animations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        """Fade in on show."""
        self.setWindowOpacity(0.0)
        self._fade_anim.setDuration(150)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        super().showEvent(event)

    def close_animated(self):
        """Fade out before closing."""
        self._fade_anim.setDuration(100)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.close)
        self._fade_anim.start()
```

### 3.4 Loading Spinner

```python
class LoadingSpinner(QLabel):
    """Animated loading spinner using rotation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rotation = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)

    def start(self):
        """Start spinning animation."""
        self._timer.start(16)  # ~60fps

    def stop(self):
        """Stop spinning animation."""
        self._timer.stop()

    def _rotate(self):
        """Rotate by 6 degrees per frame (360 degrees per second)."""
        self._rotation = (self._rotation + 6) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self._rotation)
        # Draw spinner arcs...
```

---

## 4. Canvas/Graph Animations

### 4.1 Smooth Viewport Pan/Zoom

```python
class AnimatedGraphicsView(QGraphicsView):
    """Graphics view with smooth animated zoom."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._num_scheduled_scalings = 0
        self._zoom_timeline = QTimeLine(250)  # 250ms duration
        self._zoom_timeline.setUpdateInterval(16)  # ~60fps
        self._zoom_timeline.valueChanged.connect(self._scaling_step)
        self._zoom_timeline.finished.connect(self._animation_finished)

    def wheelEvent(self, event):
        """Smooth zoom on wheel."""
        num_degrees = event.angleDelta().y() / 8
        num_steps = num_degrees / 15

        self._num_scheduled_scalings += num_steps

        if self._num_scheduled_scalings * num_steps < 0:
            # User scrolled opposite direction, reset
            self._num_scheduled_scalings = num_steps

        if self._zoom_timeline.state() == QTimeLine.State.NotRunning:
            self._zoom_timeline.start()

    def _scaling_step(self, value):
        """Execute one step of zoom animation."""
        factor = 1.0 + self._num_scheduled_scalings / 250.0
        self.scale(factor, factor)

    def _animation_finished(self):
        """Reset scheduled scalings."""
        if self._num_scheduled_scalings > 0:
            self._num_scheduled_scalings -= 1
        else:
            self._num_scheduled_scalings += 1
```

### 4.2 Node Selection Glow Effect

```python
class AnimatedNodeItem(QGraphicsItem):
    """Node with animated selection glow."""

    def __init__(self):
        super().__init__()
        self._glow_opacity = 0.0
        self._glow_anim = None

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            self._animate_selection(value)
        return super().itemChange(change, value)

    def _animate_selection(self, selected):
        """Animate glow on selection."""
        if self._glow_anim:
            self._glow_anim.stop()

        # Create animation via QVariantAnimation
        self._glow_anim = QVariantAnimation()
        self._glow_anim.setDuration(150)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        if selected:
            self._glow_anim.setStartValue(0.0)
            self._glow_anim.setEndValue(1.0)
        else:
            self._glow_anim.setStartValue(1.0)
            self._glow_anim.setEndValue(0.0)

        self._glow_anim.valueChanged.connect(self._update_glow)
        self._glow_anim.start()

    def _update_glow(self, value):
        self._glow_opacity = value
        self.update()
```

### 4.3 Connection Drawing Animation

```python
class AnimatedConnection(QGraphicsPathItem):
    """Connection wire with animated drawing effect."""

    def __init__(self, start_point, end_point):
        super().__init__()
        self._progress = 0.0
        self._full_path = self._create_bezier_path(start_point, end_point)
        self._anim = QVariantAnimation()
        self._anim.setDuration(200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._update_progress)

    def animate_draw(self):
        """Animate connection being drawn."""
        self._anim.start()

    def _update_progress(self, value):
        """Update visible portion of path."""
        self._progress = value
        # Create partial path based on progress
        partial = QPainterPath()
        length = self._full_path.length()
        partial.moveTo(self._full_path.pointAtPercent(0))

        for i in range(1, int(value * 100) + 1):
            percent = i / 100.0
            partial.lineTo(self._full_path.pointAtPercent(percent))

        self.setPath(partial)
```

---

## 5. Performance Optimization

### 5.1 Key Principles

| Principle | Implementation |
|-----------|----------------|
| **60fps target** | Max 16ms per frame |
| **Avoid garbage collection** | Reuse animation objects |
| **Batch updates** | Group property changes |
| **Use hardware acceleration** | OpenGL viewport when appropriate |
| **Minimize redraws** | Only update changed regions |

### 5.2 Animation Performance Patterns

```python
# GOOD: Reuse animation objects
class PerformantWidget(QWidget):
    def __init__(self):
        self._opacity_anim = QPropertyAnimation(self, b"opacity")
        self._opacity_anim.setDuration(150)
        self._opacity_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def fade_in(self):
        self._opacity_anim.stop()
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.start()

# BAD: Creating new animation each time
class IneffientWidget(QWidget):
    def fade_in(self):
        anim = QPropertyAnimation(self, b"opacity")  # New object each time!
        anim.setDuration(150)
        anim.start()
```

### 5.3 QGraphicsView Optimization

```python
# Optimization settings for animated canvas
def configure_animated_view(view: QGraphicsView):
    """Configure QGraphicsView for smooth animations."""

    # Use OpenGL viewport for complex scenes (optional)
    # Note: Can slow down with 1000+ small items
    # from PySide6.QtOpenGLWidgets import QOpenGLWidget
    # view.setViewport(QOpenGLWidget())

    # Cache static background
    view.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)

    # Optimize for moving items
    view.setViewportUpdateMode(
        QGraphicsView.ViewportUpdateMode.SmartViewportUpdate
    )

    # Anchor zoom to mouse position
    view.setTransformationAnchor(
        QGraphicsView.ViewportAnchor.AnchorUnderMouse
    )

    # Enable antialiasing
    view.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Optimize for many items
    view.setOptimizationFlag(
        QGraphicsView.OptimizationFlag.DontSavePainterState, True
    )
```

### 5.4 Avoiding Jank

```python
# Pattern: Debounce rapid input
class DebouncedAnimator:
    """Debounce rapid animation requests."""

    def __init__(self, delay_ms=50):
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._execute_animation)
        self._delay = delay_ms
        self._pending_value = None

    def request_animation(self, target_value):
        """Request animation, debounced."""
        self._pending_value = target_value
        self._timer.start(self._delay)

    def _execute_animation(self):
        """Execute the actual animation."""
        if self._pending_value is not None:
            self._animate_to(self._pending_value)
            self._pending_value = None
```

---

## 6. Accessibility: Reduced Motion

### 6.1 WCAG Guidelines

- **SC 2.3.3**: Motion can be disabled unless essential
- **SC 2.2.2**: Pause, stop, hide for moving content
- Avoid animations >5 seconds without user control
- No flashing >3 times per second

### 6.2 Implementation Pattern

```python
import platform
from PySide6.QtCore import QSettings

class AccessibilitySettings:
    """Check system accessibility preferences."""

    @staticmethod
    def prefers_reduced_motion() -> bool:
        """Check if user prefers reduced motion."""
        system = platform.system()

        if system == "Windows":
            # Windows: Check SystemParametersInfo
            try:
                import ctypes
                SPI_GETCLIENTAREAANIMATION = 0x1042
                result = ctypes.c_bool()
                ctypes.windll.user32.SystemParametersInfoW(
                    SPI_GETCLIENTAREAANIMATION, 0, ctypes.byref(result), 0
                )
                return not result.value  # False = animations disabled
            except Exception:
                return False

        elif system == "Darwin":  # macOS
            # macOS: Check NSWorkspace accessibility settings
            try:
                from AppKit import NSWorkspace
                return NSWorkspace.sharedWorkspace().accessibilityDisplayShouldReduceMotion()
            except Exception:
                return False

        return False

class AnimationManager:
    """Centralized animation manager with accessibility support."""

    _reduced_motion = None

    @classmethod
    def should_animate(cls) -> bool:
        """Check if animations should run."""
        if cls._reduced_motion is None:
            cls._reduced_motion = AccessibilitySettings.prefers_reduced_motion()
        return not cls._reduced_motion

    @classmethod
    def get_duration(cls, normal_duration: int) -> int:
        """Get animation duration respecting accessibility."""
        if cls.should_animate():
            return normal_duration
        return 0  # Instant transition
```

### 6.3 Usage Pattern

```python
def animate_popup_show(popup):
    """Show popup with or without animation."""
    if AnimationManager.should_animate():
        # Full animation
        popup.setWindowOpacity(0.0)
        anim = QPropertyAnimation(popup, b"windowOpacity")
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start()
    else:
        # Instant show for reduced motion
        popup.setWindowOpacity(1.0)
    popup.show()
```

---

## 7. Implementation Recommendations for CasareRPA

### 7.1 Priority Animation Additions

| Component | Animation Type | Duration | Priority |
|-----------|---------------|----------|----------|
| Node output popup | Fade in/out | 150ms | HIGH (exists) |
| Panel slide | Slide in/out | 200ms | MEDIUM |
| Node selection | Glow pulse | 150ms | MEDIUM |
| Button hover | Color transition | 100ms | LOW |
| Tooltip | Fade in | 100ms | LOW |

### 7.2 Theme Integration

Add to `theme.py`:

```python
@dataclass(frozen=True)
class Animations:
    """Animation durations in milliseconds."""
    instant: int = 50
    fast: int = 100
    normal: int = 150
    medium: int = 200
    slow: int = 300
    emphasis: int = 400
    viewport: int = 250

# Add to Theme class
@classmethod
def get_animations(cls) -> Animations:
    """Get animation duration values."""
    return ANIMATIONS
```

### 7.3 Animation Utility Module

Create `src/casare_rpa/presentation/canvas/ui/animation.py`:

```python
"""Centralized animation utilities for CasareRPA UI."""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect

from .theme import Theme

class UIAnimator:
    """Factory for common UI animations."""

    @staticmethod
    def fade_in(widget: QWidget, duration: int = None) -> QPropertyAnimation:
        """Create fade-in animation."""
        duration = duration or Theme.get_animations().normal
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        return anim

    @staticmethod
    def slide_in(widget: QWidget, direction: str = "up",
                 offset: int = 10, duration: int = None) -> QPropertyAnimation:
        """Create slide-in animation."""
        duration = duration or Theme.get_animations().normal
        pos = widget.pos()

        offsets = {
            "up": QPoint(0, offset),
            "down": QPoint(0, -offset),
            "left": QPoint(offset, 0),
            "right": QPoint(-offset, 0),
        }

        anim = QPropertyAnimation(widget, b"pos")
        anim.setDuration(duration)
        anim.setStartValue(pos + offsets.get(direction, QPoint(0, offset)))
        anim.setEndValue(pos)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        return anim
```

---

## 8. Sources

### Official Documentation
- [Qt for Python QPropertyAnimation](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QPropertyAnimation.html)
- [Qt Animation Framework Overview](https://doc.qt.io/qt-6/animation-overview.html)
- [QEasingCurve Class](https://doc.qt.io/qt-6/qeasingcurve.html)
- [Qt Quick Performance Considerations](https://doc.qt.io/qt-6/qtquick-performance.html)
- [Qt for Windows Graphics Acceleration](https://doc.qt.io/qt-6/windows-graphics.html)

### Tutorials and Examples
- [Python GUIs - Animating PySide6 Widgets](https://www.pythonguis.com/tutorials/pyside6-animated-widgets/)
- [ZetCode PyQt QPropertyAnimation](https://zetcode.com/pyqt/qpropertyanimation/)
- [Qt Wiki - Smooth Zoom in QGraphicsView](https://wiki.qt.io/Smooth_Zoom_In_QGraphicsView)

### UX Guidelines
- [Nielsen Norman Group - Animation Duration](https://www.nngroup.com/articles/animation-duration/)
- [Val Head - How Fast Should UI Animations Be](https://valhead.com/2016/05/05/how-fast-should-your-ui-animations-be/)
- [Material Design 3 - Motion](https://m3.material.io/styles/motion/overview/how-it-works)
- [CSS-Tricks - Accessible Web Animation](https://css-tricks.com/accessible-web-animation-the-wcag-on-animation-explained/)

### Accessibility
- [W3C WCAG 2.1 - Animation from Interactions](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html)
- [MDN - prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion)
- [web.dev - Animation and Motion Accessibility](https://web.dev/learn/accessibility/motion)

### Performance
- [Qt Blog - Using Hardware Acceleration](https://www.qt.io/blog/2009/03/13/using-hardware-acceleration-for-graphics)
- [Qt Blog - Graphics and Performance OpenGL](https://www.qt.io/blog/2010/01/06/qt-graphics-and-performance-opengl)
- [Qt Blog - FrameAnimation (Qt 6.4)](https://www.qt.io/blog/new-in-qt-6.4-frameanimation-element)
