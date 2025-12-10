# UI Smooth Animations - Comprehensive Plan

**Created**: 2025-12-10 | **Phase**: PLAN
**Scope**: Add smooth animations EVERYWHERE for premium UI experience
**Performance Target**: 60fps minimum, <16ms frame budget, zero jank

---

## Executive Summary

Transform CasareRPA into a visually stunning, fluid application by implementing comprehensive animations across all UI interactions. Goal: Match the polish of Figma, Linear, and modern design tools while maintaining buttery-smooth 60fps performance even with 100+ nodes.

---

## Phase 0: Performance Architecture (CRITICAL)

### 0.1 Performance Requirements

| Metric | Target | Hard Limit |
|--------|--------|------------|
| Frame Rate | 60fps | Never below 30fps |
| Frame Budget | <16ms | <33ms worst case |
| Animation CPU | <5% | <10% during animations |
| Memory Growth | 0 | No leaks from animations |
| GPU Utilization | <30% | Use OpenGL acceleration |

### 0.2 Animation Pool System

**File**: `presentation/canvas/ui/animation_pool.py`

```python
class AnimationPool:
    """
    Object pool for QPropertyAnimation instances.
    Prevents GC churn from creating/destroying animations.
    """
    _instance: Optional["AnimationPool"] = None

    # Pre-allocated pools by animation type
    _fade_pool: List[QPropertyAnimation]      # 20 pre-allocated
    _slide_pool: List[QPropertyAnimation]     # 20 pre-allocated
    _scale_pool: List[QPropertyAnimation]     # 10 pre-allocated
    _color_pool: List[QPropertyAnimation]     # 10 pre-allocated

    POOL_SIZE = 20  # Per-type pool size

    @classmethod
    def acquire(cls, anim_type: str) -> QPropertyAnimation:
        """Get animation from pool or create if exhausted."""
        pool = getattr(cls, f"_{anim_type}_pool")
        if pool:
            anim = pool.pop()
            anim.stop()  # Reset state
            return anim
        return QPropertyAnimation()  # Fallback: create new

    @classmethod
    def release(cls, anim: QPropertyAnimation, anim_type: str) -> None:
        """Return animation to pool for reuse."""
        anim.stop()
        anim.setTargetObject(None)
        pool = getattr(cls, f"_{anim_type}_pool")
        if len(pool) < cls.POOL_SIZE:
            pool.append(anim)
        # else: let GC collect (pool full)

    @classmethod
    def prewarm(cls) -> None:
        """Pre-allocate animation objects at startup."""
        for _ in range(cls.POOL_SIZE):
            cls._fade_pool.append(QPropertyAnimation())
            cls._slide_pool.append(QPropertyAnimation())
        for _ in range(10):
            cls._scale_pool.append(QPropertyAnimation())
            cls._color_pool.append(QPropertyAnimation())
```

### 0.3 Centralized Animation Coordinator (Extend Existing)

**File**: `graph/custom_node_item.py` (enhance existing `AnimationCoordinator`)

```python
class AnimationCoordinator:
    """
    Singleton managing ALL canvas animations with single timer.
    Prevents per-widget timers (100 nodes = 100 timers = bad).
    """
    _instance: Optional["AnimationCoordinator"] = None

    TICK_INTERVAL_MS = 16  # ~60fps (existing)
    MAX_ANIMATIONS_PER_FRAME = 50  # Throttle if too many

    def __init__(self):
        self._timer = QTimer()
        self._timer.setTimerType(Qt.PreciseTimer)  # High precision
        self._timer.timeout.connect(self._tick)

        # Categorized animation queues
        self._node_animations: Dict[str, Set[CasareNodeItem]] = {
            "running": set(),
            "fade_in": set(),
            "fade_out": set(),
            "selection": set(),
        }
        self._pipe_animations: Set[CasarePipe] = set()
        self._widget_animations: Set[QWidget] = set()

        # Performance tracking
        self._frame_times: deque = deque(maxlen=60)  # Last 60 frames
        self._dropped_frames = 0

    def _tick(self) -> None:
        """Process all animations in single frame."""
        start = time.perf_counter_ns()

        # Process in priority order
        processed = 0

        # 1. Running node borders (highest priority - user feedback)
        for node in list(self._node_animations["running"]):
            if processed >= self.MAX_ANIMATIONS_PER_FRAME:
                break
            node._update_running_animation()
            processed += 1

        # 2. Selection animations
        for node in list(self._node_animations["selection"]):
            if processed >= self.MAX_ANIMATIONS_PER_FRAME:
                break
            node._update_selection_animation()
            processed += 1

        # 3. Pipe flow animations
        for pipe in list(self._pipe_animations):
            if processed >= self.MAX_ANIMATIONS_PER_FRAME:
                break
            pipe._update_flow_animation()
            processed += 1

        # Track frame time
        elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000
        self._frame_times.append(elapsed_ms)

        if elapsed_ms > 16:
            self._dropped_frames += 1
            logger.warning(f"Animation frame took {elapsed_ms:.1f}ms (budget: 16ms)")

    def get_stats(self) -> Dict:
        """Performance stats for debugging."""
        times = list(self._frame_times)
        return {
            "avg_frame_ms": sum(times) / len(times) if times else 0,
            "max_frame_ms": max(times) if times else 0,
            "dropped_frames": self._dropped_frames,
            "active_animations": sum(len(q) for q in self._node_animations.values()),
        }
```

### 0.4 Level-of-Detail Animation System

**File**: `presentation/canvas/ui/animation_lod.py`

```python
class AnimationLOD:
    """
    Reduce animation complexity at low zoom levels.
    Integrates with existing ViewportLODManager.
    """

    # Zoom thresholds
    FULL_QUALITY = 0.5      # 50%+ zoom: all animations
    REDUCED_QUALITY = 0.25  # 25-50%: simplified animations
    MINIMAL_QUALITY = 0.1   # 10-25%: only essential
    DISABLED = 0.05         # <10%: no animations

    @staticmethod
    def get_animation_level(zoom: float) -> str:
        """Determine animation complexity level."""
        if zoom >= AnimationLOD.FULL_QUALITY:
            return "full"
        elif zoom >= AnimationLOD.REDUCED_QUALITY:
            return "reduced"
        elif zoom >= AnimationLOD.MINIMAL_QUALITY:
            return "minimal"
        return "disabled"

    @staticmethod
    def should_animate(zoom: float, anim_type: str) -> bool:
        """Check if animation should run at current zoom."""
        level = AnimationLOD.get_animation_level(zoom)

        # Always animate (user feedback critical)
        always_animate = {"selection", "error", "running"}
        if anim_type in always_animate:
            return level != "disabled"

        # Reduced: skip decorative animations
        skip_at_reduced = {"hover", "glow", "bounce"}
        if level == "reduced" and anim_type in skip_at_reduced:
            return False

        # Minimal: only critical animations
        if level == "minimal":
            return anim_type in always_animate

        return level != "disabled"

    @staticmethod
    def get_duration_multiplier(zoom: float) -> float:
        """Shorten animations at low zoom (less noticeable)."""
        level = AnimationLOD.get_animation_level(zoom)
        return {
            "full": 1.0,
            "reduced": 0.7,
            "minimal": 0.5,
            "disabled": 0.0,
        }[level]
```

### 0.5 Debouncing & Throttling

**File**: `presentation/canvas/ui/animation_utils.py`

```python
class AnimationThrottler:
    """Prevent animation spam from rapid events."""

    def __init__(self):
        self._last_trigger: Dict[str, float] = {}
        self._pending: Dict[str, QTimer] = {}

    def throttle(
        self,
        key: str,
        callback: Callable,
        min_interval_ms: int = 100
    ) -> bool:
        """
        Throttle animation triggers.
        Returns True if animation should proceed.
        """
        now = time.time() * 1000
        last = self._last_trigger.get(key, 0)

        if now - last < min_interval_ms:
            return False  # Too soon, skip

        self._last_trigger[key] = now
        return True

    def debounce(
        self,
        key: str,
        callback: Callable,
        delay_ms: int = 150
    ) -> None:
        """
        Debounce animation triggers.
        Only fires after events stop for delay_ms.
        """
        # Cancel pending
        if key in self._pending:
            self._pending[key].stop()

        # Schedule new
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._fire_debounced(key, callback))
        timer.start(delay_ms)
        self._pending[key] = timer

    def _fire_debounced(self, key: str, callback: Callable) -> None:
        del self._pending[key]
        callback()


# Usage example:
throttler = AnimationThrottler()

def on_hover(node):
    # Throttle hover animations to max 10/second
    if throttler.throttle(f"hover_{node.id}", node.animate_hover, 100):
        node.animate_hover()

def on_search_input(text):
    # Debounce search highlight animations
    throttler.debounce("search", lambda: highlight_results(text), 200)
```

### 0.6 GPU-Accelerated Rendering

**Leverage existing OpenGL viewport** (`node_graph_widget.py:714-735`):

```python
class PerformantGraphicsView(QGraphicsView):
    """Enhanced view with GPU optimizations for animations."""

    def __init__(self):
        super().__init__()

        # OpenGL acceleration (already enabled)
        gl_widget = QOpenGLWidget()
        gl_format = QSurfaceFormat()
        gl_format.setSamples(4)  # MSAA
        gl_format.setSwapInterval(1)  # VSync
        gl_widget.setFormat(gl_format)
        self.setViewport(gl_widget)

        # Optimization flags
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setOptimizationFlags(
            QGraphicsView.DontSavePainterState |
            QGraphicsView.DontAdjustForAntialiasing
        )
        self.setCacheMode(QGraphicsView.CacheBackground)

        # Rendering hints
        self.setRenderHints(
            QPainter.Antialiasing |
            QPainter.SmoothPixmapTransform |
            QPainter.TextAntialiasing
        )

    def set_high_performance_mode(self, enabled: bool) -> None:
        """Toggle performance mode for many nodes."""
        if enabled:
            # Disable expensive rendering
            self.setRenderHint(QPainter.Antialiasing, False)
            self.setRenderHint(QPainter.SmoothPixmapTransform, False)
            self.setViewportUpdateMode(QGraphicsView.MinimalViewportUpdate)
        else:
            # Full quality
            self.setRenderHint(QPainter.Antialiasing, True)
            self.setRenderHint(QPainter.SmoothPixmapTransform, True)
            self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
```

### 0.7 Batch Update System

```python
class BatchUpdater:
    """
    Batch multiple visual updates into single repaint.
    Prevents N repaints for N property changes.
    """

    def __init__(self, scene: QGraphicsScene):
        self._scene = scene
        self._pending_updates: Set[QGraphicsItem] = set()
        self._batch_timer = QTimer()
        self._batch_timer.setSingleShot(True)
        self._batch_timer.timeout.connect(self._flush)
        self._batch_timer.setInterval(0)  # Next event loop

    def schedule_update(self, item: QGraphicsItem) -> None:
        """Queue item for update, batch with others."""
        self._pending_updates.add(item)
        if not self._batch_timer.isActive():
            self._batch_timer.start()

    def _flush(self) -> None:
        """Apply all pending updates in single pass."""
        if not self._pending_updates:
            return

        # Calculate bounding rect of all updates
        rect = QRectF()
        for item in self._pending_updates:
            rect = rect.united(item.sceneBoundingRect())

        self._pending_updates.clear()

        # Single scene update
        self._scene.update(rect)
```

### 0.8 Performance Monitoring Dashboard

**File**: `presentation/canvas/ui/widgets/animation_profiler.py`

```python
class AnimationProfiler(QWidget):
    """
    Debug widget showing animation performance.
    Toggle with Ctrl+Shift+A in dev mode.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setFixedSize(300, 200)

        layout = QVBoxLayout(self)

        self._fps_label = QLabel("FPS: --")
        self._frame_label = QLabel("Frame: --ms")
        self._active_label = QLabel("Active: --")
        self._dropped_label = QLabel("Dropped: --")

        layout.addWidget(self._fps_label)
        layout.addWidget(self._frame_label)
        layout.addWidget(self._active_label)
        layout.addWidget(self._dropped_label)

        # Update every 500ms
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(500)

    def _update_stats(self):
        stats = AnimationCoordinator.instance().get_stats()
        fps = 1000 / stats["avg_frame_ms"] if stats["avg_frame_ms"] > 0 else 0

        self._fps_label.setText(f"FPS: {fps:.0f}")
        self._frame_label.setText(f"Frame: {stats['avg_frame_ms']:.1f}ms (max: {stats['max_frame_ms']:.1f}ms)")
        self._active_label.setText(f"Active Animations: {stats['active_animations']}")
        self._dropped_label.setText(f"Dropped Frames: {stats['dropped_frames']}")
```

---

## Phase 1: Animation Infrastructure (Foundation)

### 1.1 Create Animation Utility Module

**File**: `presentation/canvas/ui/animation.py`

```python
class UIAnimator:
    """Centralized animation controller for all UI components."""

    # Reusable animation instances (performance)
    _fade_animations: Dict[int, QPropertyAnimation]
    _slide_animations: Dict[int, QPropertyAnimation]

    @staticmethod
    def fade_in(widget, duration=150, easing=QEasingCurve.OutCubic)

    @staticmethod
    def fade_out(widget, duration=100, easing=QEasingCurve.InCubic)

    @staticmethod
    def slide_in(widget, direction="left", duration=200)

    @staticmethod
    def slide_out(widget, direction="left", duration=150)

    @staticmethod
    def scale_in(widget, from_scale=0.8, duration=200)

    @staticmethod
    def bounce(widget, intensity=1.1, duration=150)

    @staticmethod
    def shake(widget, intensity=5, duration=300)  # For validation errors

    @staticmethod
    def glow_pulse(widget, color, cycles=2, duration=600)
```

### 1.2 Update Theme Animation Constants

**File**: `presentation/canvas/ui/theme.py`

```python
@dataclass(frozen=True)
class Animations:
    """Animation durations in milliseconds."""
    instant: int = 50      # Button press feedback
    fast: int = 100        # Hover effects
    normal: int = 150      # Standard fade/slide
    medium: int = 200      # Panel transitions
    slow: int = 300        # Modal dialogs
    emphasis: int = 400    # Attention-grabbing effects
```

### 1.3 Accessibility Support

**File**: `presentation/canvas/ui/accessibility.py`

```python
class AccessibilitySettings:
    """Respect user's reduced motion preferences."""

    @staticmethod
    def prefers_reduced_motion() -> bool:
        """Check OS-level reduced motion setting."""
        # Windows: SystemParametersInfo(SPI_GETCLIENTAREAANIMATION)
        # macOS: NSWorkspace.accessibilityDisplayShouldReduceMotion

    @staticmethod
    def get_duration(base_duration: int) -> int:
        """Return 0 if reduced motion, else base_duration."""
```

---

## Phase 2: Canvas Graph Animations (High Impact)

### 2.1 Node Lifecycle Animations

**Files to modify**:
- `graph/custom_node_item.py`
- `graph/node_graph_widget.py`

| Animation | Trigger | Duration | Easing | Effect |
|-----------|---------|----------|--------|--------|
| Node Create | `addNode()` | 200ms | OutBack | Scale 0.8→1.0 + Fade 0→1 |
| Node Delete | `removeNode()` | 150ms | InCubic | Scale 1.0→0.8 + Fade 1→0 |
| Node Select | Selection change | 100ms | OutQuad | Border glow pulse |
| Node Deselect | Selection change | 80ms | InQuad | Border glow fade |
| Node Running | Execution start | Loop | Linear | Dotted border rotate (EXISTING) |
| Node Complete | Execution end | 300ms | OutElastic | Checkmark scale-in |
| Node Error | Execution error | 400ms | - | Red pulse + shake |

**Implementation Pattern** (using existing AnimationCoordinator):

```python
# In CasareNodeItem
def animate_creation(self):
    """Smooth entrance animation."""
    self.setOpacity(0)
    self.setScale(0.8)

    group = QParallelAnimationGroup(self)

    fade = QPropertyAnimation(self, b"opacity")
    fade.setDuration(200)
    fade.setStartValue(0)
    fade.setEndValue(1)
    fade.setEasingCurve(QEasingCurve.OutCubic)

    scale = QPropertyAnimation(self, b"scale")
    scale.setDuration(200)
    scale.setStartValue(0.8)
    scale.setEndValue(1.0)
    scale.setEasingCurve(QEasingCurve.OutBack)

    group.addAnimation(fade)
    group.addAnimation(scale)
    group.start(QAbstractAnimation.DeleteWhenStopped)
```

### 2.2 Connection/Wire Animations

**Files to modify**:
- `graph/custom_pipe.py`
- `connections/auto_connect.py`

| Animation | Trigger | Duration | Effect |
|-----------|---------|----------|--------|
| Wire Create | Connection made | 200ms | Draw from source → target |
| Wire Delete | Disconnection | 150ms | Fade out + retract |
| Wire Drag Preview | Dragging | Real-time | Ghost wire with 50% opacity |
| Wire Drop Valid | Valid target | 150ms | Target port glow green |
| Wire Drop Invalid | Invalid target | 150ms | Target port flash red |
| Execution Flow | Node executing | 500ms loop | White dot flowing (EXISTING) |
| Completion Glow | Execution done | 300ms | Green glow pulse (EXISTING) |

**New: Wire Draw Animation**:

```python
class AnimatedPipe(CasarePipe):
    def animate_connection(self):
        """Animate wire drawing from source to target."""
        self._draw_progress = 0.0
        self._draw_animation = QVariantAnimation(self)
        self._draw_animation.setDuration(200)
        self._draw_animation.setStartValue(0.0)
        self._draw_animation.setEndValue(1.0)
        self._draw_animation.valueChanged.connect(self._update_draw_progress)
        self._draw_animation.start()

    def paint(self, painter, option, widget):
        # Draw partial path based on _draw_progress
        path = self.path()
        partial_path = self._get_partial_path(path, self._draw_progress)
        painter.drawPath(partial_path)
```

### 2.3 Selection Animations

**Files to modify**:
- `graph/selection_manager.py`
- `graph/custom_node_item.py`

| Animation | Effect |
|-----------|--------|
| Single select | Yellow border glow (fade in 100ms) |
| Multi-select | Staggered glow (30ms delay per node) |
| Select all | Ripple effect from center |
| Deselect all | Simultaneous fade (80ms) |
| Box select preview | Dashed rect with subtle pulse |

### 2.4 Viewport Animations

**Files to modify**:
- `controllers/viewport_controller.py`
- `graph/node_graph_widget.py`

| Animation | Trigger | Duration | Easing |
|-----------|---------|----------|--------|
| Zoom In/Out | Mouse wheel | 250ms | InOutSine |
| Pan | Middle mouse | Smooth | InOutQuad |
| Fit to View | Double-click/Shortcut | 350ms | InOutCubic |
| Focus on Node | Double-click node | 300ms | OutCubic |
| Minimap Navigate | Click minimap | 250ms | OutCubic |

**Smooth Zoom Implementation**:

```python
class SmoothViewport:
    def smooth_zoom(self, factor: float, center: QPointF):
        """Animated zoom with easing."""
        current_scale = self.transform().m11()
        target_scale = current_scale * factor

        animation = QVariantAnimation(self)
        animation.setDuration(250)
        animation.setStartValue(current_scale)
        animation.setEndValue(target_scale)
        animation.setEasingCurve(QEasingCurve.InOutSine)
        animation.valueChanged.connect(
            lambda v: self._apply_zoom(v, center)
        )
        animation.start(QAbstractAnimation.DeleteWhenStopped)
```

---

## Phase 3: Panel & Dock Animations

### 3.1 Panel Show/Hide

**Files to modify**:
- `ui/panels/side_panel_dock.py`
- `ui/panels/bottom_panel_dock.py`
- `managers/panel_manager.py`

| Animation | Trigger | Duration | Effect |
|-----------|---------|----------|--------|
| Panel Open | Toggle/Shortcut | 200ms | Slide in + Fade |
| Panel Close | Toggle/Shortcut | 150ms | Slide out + Fade |
| Panel Resize | Drag splitter | Real-time | Smooth with easing |

**Implementation**:

```python
class AnimatedDockWidget(QDockWidget):
    def showEvent(self, event):
        super().showEvent(event)
        self._animate_show()

    def _animate_show(self):
        """Slide in from edge."""
        # Get dock area to determine slide direction
        area = self.parent().dockWidgetArea(self)

        if area == Qt.LeftDockWidgetArea:
            self._slide_from("left")
        elif area == Qt.RightDockWidgetArea:
            self._slide_from("right")
        elif area == Qt.BottomDockWidgetArea:
            self._slide_from("bottom")
```

### 3.2 Tab Switching Animations

**Files to modify**:
- `ui/panels/bottom_panel_dock.py`
- `ui/panels/side_panel_dock.py`

| Animation | Effect |
|-----------|--------|
| Tab Activate | Content fade in (150ms) + slide up (5px) |
| Tab Deactivate | Content fade out (100ms) |
| Tab Indicator | Underline slide to active tab (200ms) |

**Implementation**:

```python
class AnimatedTabWidget(QTabWidget):
    def __init__(self):
        super().__init__()
        self.currentChanged.connect(self._animate_tab_change)
        self._content_stack = QStackedWidget()

    def _animate_tab_change(self, index):
        """Crossfade between tab contents."""
        outgoing = self._content_stack.currentWidget()
        incoming = self._content_stack.widget(index)

        # Parallel fade out old, fade in new
        group = QParallelAnimationGroup(self)

        fade_out = self._create_fade(outgoing, 1.0, 0.0, 100)
        fade_in = self._create_fade(incoming, 0.0, 1.0, 150)

        group.addAnimation(fade_out)
        group.addAnimation(fade_in)
        group.start()
```

### 3.3 Collapsible Sections

**Files to modify**:
- `ui/widgets/collapsible_section.py` (create new)
- Apply to dialogs with sections

| Animation | Effect |
|-----------|--------|
| Expand | Height animate 0→content (200ms OutCubic) + arrow rotate |
| Collapse | Height animate content→0 (150ms InCubic) + arrow rotate |

---

## Phase 4: Dialog Animations

### 4.1 Dialog Lifecycle

**Files to modify**:
- `ui/dialogs/dialog_styles.py`
- All dialog files (30+)

| Animation | Trigger | Duration | Effect |
|-----------|---------|----------|--------|
| Dialog Open | `exec()`/`show()` | 250ms | Fade in + Scale 0.95→1.0 |
| Dialog Close | `accept()`/`reject()` | 150ms | Fade out + Scale 1.0→0.95 |
| Modal Backdrop | Dialog open | 200ms | Dim background (opacity 0→0.5) |

**Base AnimatedDialog Class**:

```python
class AnimatedDialog(QDialog):
    """Base class for all animated dialogs."""

    def showEvent(self, event):
        super().showEvent(event)
        self._animate_open()

    def _animate_open(self):
        self.setWindowOpacity(0)

        group = QParallelAnimationGroup(self)

        # Fade in
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(250)
        fade.setStartValue(0)
        fade.setEndValue(1)
        fade.setEasingCurve(QEasingCurve.OutCubic)

        group.addAnimation(fade)
        group.start(QAbstractAnimation.DeleteWhenStopped)

    def accept(self):
        self._animate_close(super().accept)

    def reject(self):
        self._animate_close(super().reject)

    def _animate_close(self, callback):
        fade = QPropertyAnimation(self, b"windowOpacity")
        fade.setDuration(150)
        fade.setStartValue(1)
        fade.setEndValue(0)
        fade.setEasingCurve(QEasingCurve.InCubic)
        fade.finished.connect(callback)
        fade.start(QAbstractAnimation.DeleteWhenStopped)
```

### 4.2 Form Field Animations

| Animation | Trigger | Duration | Effect |
|-----------|---------|----------|--------|
| Focus | Field focus | 100ms | Border color transition to accent |
| Blur | Field blur | 80ms | Border color transition to default |
| Validation Error | Invalid input | 300ms | Shake + red border pulse |
| Validation Success | Valid input | 200ms | Green checkmark fade in |
| Field Enable | setEnabled(True) | 150ms | Fade in from 50% opacity |
| Field Disable | setEnabled(False) | 100ms | Fade to 50% opacity |

### 4.3 Wizard Step Transitions

**Files to modify**:
- `ui/dialogs/project_wizard.py`

| Animation | Effect |
|-----------|--------|
| Next Step | Current slide left + fade out, Next slide right + fade in |
| Previous Step | Current slide right + fade out, Previous slide left + fade in |
| Step Indicator | Progress bar animate + dot highlight |

---

## Phase 5: Widget Micro-Interactions

### 5.1 Button Animations

**Files to modify**:
- `ui/theme.py` (CSS transitions)
- Create `ui/widgets/animated_button.py`

| State | Duration | Effect |
|-------|----------|--------|
| Hover In | 100ms | Background color transition + slight scale 1.02 |
| Hover Out | 80ms | Background color transition + scale 1.0 |
| Press | 50ms | Scale 0.98 + darker background |
| Release | 100ms | Scale 1.0 + original background |
| Disabled | 150ms | Opacity fade to 0.5 |

**CSS-based (simpler)**:

```css
QPushButton {
    transition: background-color 100ms ease-out,
                transform 100ms ease-out;
}
QPushButton:hover {
    transform: scale(1.02);
}
QPushButton:pressed {
    transform: scale(0.98);
}
```

**Note**: Qt CSS doesn't support `transition`. Use QPropertyAnimation instead:

```python
class AnimatedButton(QPushButton):
    def enterEvent(self, event):
        self._animate_hover(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate_hover(False)
        super().leaveEvent(event)

    def _animate_hover(self, hovering: bool):
        # Animate background color
        color_anim = QPropertyAnimation(self, b"backgroundColor")
        color_anim.setDuration(100)
        color_anim.setEndValue(self._hover_color if hovering else self._normal_color)
        color_anim.start()
```

### 5.2 Checkbox/Toggle Animations

| Animation | Duration | Effect |
|-----------|----------|--------|
| Check | 150ms | Checkmark draw animation + background fill |
| Uncheck | 100ms | Checkmark fade + background unfill |
| Toggle Switch | 200ms | Knob slide + track color change |

### 5.3 Dropdown/ComboBox Animations

| Animation | Duration | Effect |
|-----------|----------|--------|
| Open | 150ms | Dropdown slide down + fade in |
| Close | 100ms | Dropdown slide up + fade out |
| Item Hover | 80ms | Background highlight slide |

### 5.4 Tooltip Animations

**Files to modify**:
- Create custom tooltip system or use QToolTip with effects

| Animation | Duration | Effect |
|-----------|----------|--------|
| Show | 150ms | Fade in + slide up 5px |
| Hide | 100ms | Fade out + slide down 5px |
| Reposition | 100ms | Smooth move to new position |

### 5.5 Progress Indicators

| Animation | Effect |
|-----------|--------|
| Determinate | Smooth width transition (not jumpy) |
| Indeterminate | Shimmer/pulse animation |
| Circular | Rotation + dash animation |
| Success | Green fill + checkmark |
| Error | Red pulse + X mark |

---

## Phase 6: List & Table Animations

### 6.1 List Item Animations

**Files to modify**:
- `ui/panels/variables_panel.py`
- `ui/panels/log_tab.py`
- Any QListWidget/QTreeWidget usage

| Animation | Duration | Effect |
|-----------|----------|--------|
| Item Add | 200ms | Fade in + slide down from above |
| Item Remove | 150ms | Fade out + slide up + collapse height |
| Item Reorder | 200ms | Smooth position interpolation |
| Item Select | 100ms | Background highlight fade |
| Item Hover | 80ms | Subtle background highlight |

**Implementation with QSequentialAnimationGroup**:

```python
def add_item_animated(self, item):
    """Add item with staggered animation."""
    row = self.count()
    self.insertItem(row, item)

    # Get item widget
    widget = self.itemWidget(item)
    widget.setOpacity(0)
    widget.setPos(widget.pos() - QPointF(0, 20))

    group = QParallelAnimationGroup()

    fade = QPropertyAnimation(widget, b"opacity")
    fade.setDuration(200)
    fade.setStartValue(0)
    fade.setEndValue(1)

    slide = QPropertyAnimation(widget, b"pos")
    slide.setDuration(200)
    slide.setEndValue(widget.pos() + QPointF(0, 20))

    group.addAnimation(fade)
    group.addAnimation(slide)
    group.start()
```

### 6.2 Log/Terminal Animations

| Animation | Effect |
|-----------|--------|
| New Line | Fade in + highlight briefly (200ms yellow, then fade) |
| Error Line | Red flash + persist red background |
| Clear All | Staggered fade out from bottom to top |
| Scroll to Bottom | Smooth scroll (200ms) |

---

## Phase 7: Specialized Animations

### 7.1 Node Output Popup (Already Has Fade)

**Current**: 150ms fade in/out with OutCubic
**Enhance**:
- Add subtle slide up on appear
- Add scale animation (0.95→1.0)
- Tab content crossfade

### 7.2 Variable Picker

| Animation | Effect |
|-----------|--------|
| Open | Fade + slide from button |
| Close | Fade + slide to button |
| Type Filter | Content crossfade |
| Variable Insert | Flash highlight on inserted text |

### 7.3 Breadcrumb Navigation

| Animation | Effect |
|-----------|--------|
| Add Crumb | Slide in from right + fade |
| Remove Crumb | Slide out to right + fade |
| Click Transition | Current slides out, content crossfades |

### 7.4 Minimap

| Animation | Effect |
|-----------|--------|
| Viewport Indicator | Smooth position/size updates |
| Node Highlight | Pulse on hover corresponding node |
| Zoom Change | Smooth scale transition |

### 7.5 Search/Find Widget

| Animation | Effect |
|-----------|--------|
| Open | Slide down from toolbar + fade |
| Close | Slide up + fade |
| Results Highlight | Flash highlight on matches |
| Navigate Results | Smooth viewport pan to result |

---

## Phase 8: Context Menu Animations

**Files to modify**:
- Create custom context menu or use QMenu with effects

| Animation | Duration | Effect |
|-----------|----------|--------|
| Open | 100ms | Scale from click point + fade |
| Close | 80ms | Fade out |
| Submenu Open | 100ms | Slide in from parent |
| Item Hover | 50ms | Background highlight slide |

---

## Implementation Order (Priority)

### Sprint 0: Performance Foundation (FIRST - Critical)
0. **AnimationPool** - Object pooling for zero GC pauses
1. **AnimationLOD** - Level-of-detail system integration
2. **AnimationThrottler** - Debounce/throttle utilities
3. **AnimationProfiler** - Debug dashboard (Ctrl+Shift+A)
4. **Enhance AnimationCoordinator** - Add priority queues, stats tracking
5. **BatchUpdater** - Coalesce scene updates

**Gate**: Must pass 60fps test with 100 nodes before proceeding

### Sprint 1: Foundation + High-Impact Canvas
6. **Animation utility module** (`ui/animation.py`)
7. **Update theme constants** (add `instant`, `emphasis`)
8. **Accessibility detection** (reduced motion)
9. **Node create/delete animations** (using pool)
10. **Selection animations** (glow pulse)
11. **Smooth viewport zoom** (InOutSine easing)

**Gate**: Profile and verify no regression

### Sprint 2: Panels & Dialogs
12. **AnimatedDockWidget base class**
13. **Panel slide animations** (slide in/out)
14. **Tab switching animations** (crossfade)
15. **AnimatedDialog base class**
16. **Dialog open/close animations** (fade + scale)
17. **Collapsible sections** (height animation)

**Gate**: All panels/dialogs animated, 60fps maintained

### Sprint 3: Widgets & Micro-Interactions
18. **Button hover/press animations** (scale + color)
19. **Form field focus animations** (border glow)
20. **Validation feedback animations** (shake, pulse)
21. **Checkbox/toggle animations** (draw + slide)
22. **Dropdown animations** (slide + fade)
23. **Tooltip animations** (fade + offset)

**Gate**: All widgets have micro-interactions

### Sprint 4: Lists, Canvas Polish & Final
24. **List item add/remove animations** (staggered)
25. **Log line animations** (highlight + fade)
26. **Connection draw animations** (progressive draw)
27. **Context menu animations** (scale from point)
28. **Wire reconnection animations** (morph)
29. **Final performance audit** (100 nodes, all animations)
30. **Accessibility final pass** (reduced motion for all)

**Gate**: Full test suite passes, 60fps guaranteed

---

## Performance Guidelines (Comprehensive)

### P1. Animation Object Management

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| Object Pooling | `AnimationPool.acquire()`/`release()` | Prevents GC pauses |
| Lazy Creation | Create on first use, not constructor | Faster startup |
| Eager Cleanup | `DeleteWhenStopped` flag | No memory leaks |
| Singleton Timer | `AnimationCoordinator` for canvas | 1 timer vs N timers |

### P2. Frame Budget Allocation

```
Total Budget: 16.67ms (60fps)
├── Animation Logic:     2ms  (12%)
├── Layout Updates:      3ms  (18%)
├── Paint/Render:        8ms  (48%)
├── Event Processing:    2ms  (12%)
└── Buffer/Headroom:     1.67ms (10%)
```

**Rules:**
- Animation tick must complete in <2ms
- If >50 animations active, throttle to 30 per frame
- Skip decorative animations under load

### P3. LOD Animation Rules

| Zoom Level | Node Count | Animation Policy |
|------------|------------|------------------|
| >50% | Any | Full quality |
| 25-50% | <50 | Full quality |
| 25-50% | 50-100 | Reduce durations 30% |
| 25-50% | >100 | Essential only (selection, error) |
| 10-25% | Any | Minimal (running border, selection) |
| <10% | Any | Disabled (instant state changes) |

### P4. Debounce & Throttle Matrix

| Event Type | Strategy | Interval | Reason |
|------------|----------|----------|--------|
| Mouse hover | Throttle | 100ms | Prevent spam |
| Mouse wheel zoom | Debounce | 50ms | Coalesce rapid scrolls |
| Selection change | Immediate | - | User feedback critical |
| Search input | Debounce | 200ms | Wait for typing pause |
| Window resize | Debounce | 150ms | Expensive layout |
| Panel toggle | Throttle | 300ms | Prevent rapid toggle |

### P5. GPU Optimization Checklist

- [x] OpenGL viewport enabled (`QOpenGLWidget`)
- [x] VSync enabled (prevent tearing)
- [x] Background caching (`CacheBackground`)
- [ ] Texture atlasing for icons (reduce draw calls)
- [ ] Shader-based effects for glows (offload CPU)
- [ ] Double buffering for smooth transitions

### P6. Memory Management

```python
# BAD: Creates new animation every call
def animate_hover(self):
    anim = QPropertyAnimation(self, b"opacity")  # New object
    anim.start()

# GOOD: Reuse from pool
def animate_hover(self):
    anim = AnimationPool.acquire("fade")
    anim.setTargetObject(self)
    anim.setPropertyName(b"opacity")
    anim.finished.connect(lambda: AnimationPool.release(anim, "fade"))
    anim.start()
```

### P7. Batch Update Pattern

```python
# BAD: N updates = N repaints
for node in selected_nodes:
    node.set_selected(True)  # Triggers repaint
    node.update()            # Another repaint

# GOOD: Single batched repaint
batch = BatchUpdater(scene)
for node in selected_nodes:
    node._selected = True  # State only
    batch.schedule_update(node)
# Single repaint on next event loop
```

### P8. Profiling Requirements

**Before each sprint:**
1. Record baseline FPS with 100 nodes
2. Measure animation frame times
3. Count active QTimer instances
4. Monitor memory growth over 10 minutes

**Tools:**
- `AnimationProfiler` widget (Ctrl+Shift+A)
- Qt Creator's performance analyzer
- Python `cProfile` for tick functions
- Windows Task Manager for GPU %

### P9. Fallback Strategies

| Condition | Detection | Fallback |
|-----------|-----------|----------|
| Low FPS (<30) | `AnimationCoordinator.get_stats()` | Disable non-essential |
| High CPU (>50%) | System monitor | Reduce animation count |
| Many nodes (>100) | `scene.items().count()` | Enable high-perf mode |
| Old GPU | OpenGL version check | Software rendering |
| User pref | Accessibility API | Instant transitions |

### P10. Testing Performance Requirements

```python
def test_animation_performance():
    """Ensure animations meet 60fps target."""
    # Setup: 100 nodes, 50 connections
    graph = create_test_graph(nodes=100, connections=50)

    # Trigger 20 simultaneous node selections
    select_nodes(graph.nodes[:20])

    # Measure
    stats = AnimationCoordinator.instance().get_stats()

    assert stats["avg_frame_ms"] < 16, "Frame budget exceeded"
    assert stats["dropped_frames"] == 0, "Frames dropped"
    assert stats["max_frame_ms"] < 33, "Spike exceeded 30fps floor"
```

---

## Files to Create

### Performance Infrastructure (Phase 0)

| File | Purpose | Priority |
|------|---------|----------|
| `ui/animation_pool.py` | Object pool for QPropertyAnimation reuse | P0 |
| `ui/animation_lod.py` | Level-of-detail animation system | P0 |
| `ui/animation_utils.py` | Throttler, debouncer, batch updater | P0 |
| `ui/widgets/animation_profiler.py` | Debug performance dashboard (Ctrl+Shift+A) | P0 |

### Animation Components (Phase 1+)

| File | Purpose | Priority |
|------|---------|----------|
| `ui/animation.py` | UIAnimator utility class | P1 |
| `ui/accessibility.py` | Reduced motion detection (Windows/macOS) | P1 |
| `ui/widgets/animated_button.py` | Button with hover/press animations | P2 |
| `ui/widgets/animated_dialog.py` | Base dialog with open/close animations | P2 |
| `ui/widgets/animated_tab_widget.py` | Tab widget with crossfade | P2 |
| `ui/widgets/collapsible_section.py` | Animated expand/collapse | P2 |
| `ui/widgets/animated_list_widget.py` | List with item animations | P3 |
| `ui/widgets/animated_dock.py` | Dock panel with slide animations | P2 |

---

## Files to Modify

| File | Changes |
|------|---------|
| `ui/theme.py` | Update ANIMATIONS constants |
| `graph/custom_node_item.py` | Add lifecycle animations |
| `graph/custom_pipe.py` | Add draw animation |
| `graph/node_graph_widget.py` | Add smooth zoom |
| `controllers/viewport_controller.py` | Smooth pan/zoom |
| `ui/panels/side_panel_dock.py` | Slide animations |
| `ui/panels/bottom_panel_dock.py` | Slide + tab animations |
| `managers/panel_manager.py` | Coordinate panel animations |
| `ui/dialogs/*.py` | Inherit from AnimatedDialog |

---

## Success Metrics

- [ ] All node operations animated (create, delete, select)
- [ ] All panel operations animated (show, hide, tab switch)
- [ ] All dialogs animated (open, close)
- [ ] All buttons have hover/press feedback
- [ ] All form fields have focus animations
- [ ] Viewport zoom/pan is buttery smooth
- [ ] No animation causes frame drops below 60fps
- [ ] Reduced motion preference respected
- [ ] Consistent timing across similar interactions

---

## Risk Mitigation

1. **Performance regression** → Profile before/after, use LOD
2. **Accessibility issues** → Implement reduced motion from start
3. **Inconsistent feel** → Use UIAnimator for all animations
4. **Scope creep** → Strict sprint boundaries, MVP first
5. **Qt limitations** → Test on Windows early, fallback plans

---

**Ready for Implementation**: Awaiting approval to proceed to EXECUTE phase.
