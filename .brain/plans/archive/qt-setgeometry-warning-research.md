# Research: QWindowsWindow::setGeometry Warning on Windows

## Summary

The warning `QWindowsWindow::setGeometry: Unable to set geometry X on QWidgetWindow` is a **Windows-specific informational warning** that occurs when Qt cannot apply the exact geometry requested. It is generally **harmless** and the window will still display correctly with adjusted dimensions.

---

## 1. Root Causes

### 1.1 Windows Minimum Size Constraints
The most common cause is Windows enforcing minimum window sizes to accommodate:
- **Title bar buttons** (minimize, maximize, close)
- **Window frame decorations**
- **System font metrics**

When you request a window smaller than Windows allows (e.g., `width < 120px`), the OS clamps it to its minimum, triggering the warning.

### 1.2 DPI Scaling Mismatches
On Windows with DPI scaling (125%, 150%, etc.):
- Qt requests geometry in device-independent pixels
- Windows applies its own constraints in physical pixels
- The conversion can result in geometry that violates Windows constraints

### 1.3 Geometry Outside Monitor Bounds
Requesting a window position or size that extends beyond the available screen area:
```
Requested: 1920x1080+0+0
Available: 1920x1040 (taskbar takes 40px)
Result: Warning + clamped geometry
```

### 1.4 Layout System Conflicts
- `QBoxLayout` or other layouts may request sizes before widgets are fully initialized
- Setting geometry during `resizeEvent` can cause recursive issues
- Geometry changes during window show/hide transitions

### 1.5 Restored Geometry Issues
Loading saved geometry from `QSettings` that was saved on a different:
- Monitor configuration
- DPI scale
- Windows version

---

## 2. Is It a Bug or Informational?

**Verdict: Informational Warning (Not a Bug)**

The warning is intentionally emitted by Qt to inform developers that:
1. The requested geometry could not be exactly applied
2. The window was adjusted to valid constraints
3. The UI will still work correctly

From Qt source code:
```cpp
// A ResizeEvent with resulting geometry will be sent. If we cannot
// achieve that size (for example, window title minimal constraint),
// notify and warn.
```

**Key insight**: The window still displays correctly - Qt is simply notifying you that adjustments were made.

---

## 3. Common Fixes and Suppressions

### 3.1 Set Appropriate Minimum Size (Recommended)

```python
# Ensure window is large enough for Windows frame decorations
# Minimum ~120-140px width recommended on Windows
widget.setMinimumSize(200, 150)

# Or for dialogs
dialog.setMinimumSize(300, 200)
```

### 3.2 Clamp Geometry to Screen Bounds (Already in CasareRPA)

The project already implements this in `node_output_popup.py`:

```python
# Clamp geometry to primary screen available area
screen = QApplication.primaryScreen()
if screen is not None:
    avail = screen.availableGeometry()
    # Constrain edges
    if new_geo.left() < avail.left():
        new_geo.moveLeft(avail.left())
    if new_geo.top() < avail.top():
        new_geo.moveTop(avail.top())
    if new_geo.right() > avail.right():
        new_geo.setRight(avail.right())
    if new_geo.bottom() > avail.bottom():
        new_geo.setBottom(avail.bottom())
```

### 3.3 Use resize() Instead of setGeometry()

When you only need to set size (not position):

```python
# Instead of
widget.setGeometry(x, y, width, height)

# Use resize() for size-only changes
widget.resize(width, height)

# Or setFixedSize() for fixed dimensions
widget.setFixedSize(300, 200)
```

### 3.4 Suppress the Warning via Message Handler

The project already has a message handler in `app.py`. To suppress this warning:

```python
# In app.py, add to _SUPPRESSED_PATTERNS:
_SUPPRESSED_PATTERNS = (
    "Unknown property box-shadow",
    "Unknown property text-shadow",
    "QWindowsWindow::setGeometry",  # Add this
)
```

**Note**: Only suppress if you've verified the warning is harmless for your use case.

### 3.5 Validate Geometry Before Applying

```python
def safe_set_geometry(widget: QWidget, rect: QRect) -> None:
    """Set geometry with validation to avoid warnings."""
    # Get minimum constraints
    min_size = widget.minimumSize()
    if min_size.isEmpty():
        min_size = QSize(120, 40)  # Windows minimum

    # Ensure size meets minimum
    width = max(rect.width(), min_size.width())
    height = max(rect.height(), min_size.height())

    # Clamp to screen
    screen = widget.screen() or QApplication.primaryScreen()
    if screen:
        avail = screen.availableGeometry()
        x = max(avail.left(), min(rect.x(), avail.right() - width))
        y = max(avail.top(), min(rect.y(), avail.bottom() - height))
        rect = QRect(x, y, width, height)

    widget.setGeometry(rect)
```

---

## 4. Best Practices for Window Geometry on Windows with PySide6

### 4.1 High DPI Configuration (Already Implemented)

CasareRPA correctly configures DPI handling in `app.py`:

```python
# Enable high-DPI scaling
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling)
QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps)
```

**Note**: These must be set BEFORE creating `QApplication`.

### 4.2 Use Device-Independent Coordinates

Always work in logical (device-independent) pixels:

```python
# Qt 6 handles the DPI conversion automatically
# Just use normal pixel values
widget.setMinimumSize(300, 200)  # Logical pixels

# If you need physical pixels (rare)
ratio = widget.devicePixelRatio()
physical_width = int(logical_width * ratio)
```

### 4.3 Account for Window Frame When Restoring Geometry

```python
def restore_geometry(widget: QWidget, settings: QSettings) -> None:
    """Restore geometry with frame awareness."""
    geometry = settings.value("geometry")
    if geometry:
        # Validate against current screen configuration
        screen = QApplication.primaryScreen()
        if screen:
            avail = screen.availableGeometry()
            # Verify saved geometry intersects current screen
            saved_rect = QRect.fromBytes(geometry)
            if not avail.intersects(saved_rect):
                # Geometry is off-screen, reset to center
                widget.resize(800, 600)
                widget.move(
                    avail.center() - widget.rect().center()
                )
                return

        widget.restoreGeometry(geometry)
```

### 4.4 Handle Multi-Monitor Scenarios

```python
def get_appropriate_screen(widget: QWidget, preferred_pos: QPoint) -> QScreen:
    """Find the best screen for a given position."""
    for screen in QApplication.screens():
        if screen.geometry().contains(preferred_pos):
            return screen
    return QApplication.primaryScreen()
```

### 4.5 Defer Geometry Operations Until Shown

```python
class MyWidget(QWidget):
    def showEvent(self, event):
        super().showEvent(event)
        # Geometry is reliable only after show
        if not self._geometry_initialized:
            self._apply_saved_geometry()
            self._geometry_initialized = True
```

### 4.6 Use Layouts Instead of Manual Geometry

```python
# Preferred: Let layouts handle sizing
layout = QVBoxLayout(widget)
layout.addWidget(child1)
layout.addWidget(child2)
widget.setMinimumSize(200, 150)  # Just set minimum

# Avoid: Manual geometry for child widgets
# child1.setGeometry(0, 0, 100, 50)  # Can cause issues
```

---

## 5. CasareRPA-Specific Recommendations

### 5.1 Current Implementation Status

| File | Status | Notes |
|------|--------|-------|
| `app.py` | Good | DPI handling configured correctly |
| `app.py` | Good | Message handler infrastructure exists |
| `node_output_popup.py` | Good | Screen clamping implemented |
| Dialogs | Good | Minimum sizes set appropriately |

### 5.2 Recommended Changes

**Option A: Suppress the Warning (Quick Fix)**

Add to `_SUPPRESSED_PATTERNS` in `app.py`:
```python
_SUPPRESSED_PATTERNS = (
    "Unknown property box-shadow",
    "Unknown property text-shadow",
    "QWindowsWindow::setGeometry",  # Harmless Windows constraint warning
)
```

**Option B: More Granular Filtering (Recommended)**

Update the message handler to suppress only this specific warning:

```python
def _qt_message_handler(msg_type: QtMsgType, context, message: str) -> None:
    """Custom Qt message handler to suppress known harmless warnings."""
    # Suppress known harmless warnings
    if any(pattern in message for pattern in _SUPPRESSED_PATTERNS):
        return

    # Suppress geometry warnings (Windows-specific, harmless)
    if "QWindowsWindow::setGeometry" in message:
        logger.debug(f"[Qt/Geometry] {message}")  # Log at debug level
        return

    # ... rest of handler
```

This logs the warning at DEBUG level instead of WARNING, keeping the information available for debugging while not cluttering normal output.

---

## 6. Testing DPI Scenarios

To test your application under different DPI settings without changing Windows settings:

```bash
# Force 2x scaling
set QT_SCALE_FACTOR=2
python run.py

# Force specific DPI awareness
set QT_QPA_PLATFORM=windows:dpiawareness=0  # Unaware
set QT_QPA_PLATFORM=windows:dpiawareness=1  # System aware
set QT_QPA_PLATFORM=windows:dpiawareness=2  # Per-monitor aware (default Qt6)
```

---

## Sources

- [Qt Forum: SOLVED QWindowsWindow::setGeometry](https://forum.qt.io/topic/43535/solved-qwindowswindow-setgeometry-unable-to-set-geometry)
- [Qt Forum: setGeometry Unable to set geometry](https://forum.qt.io/topic/130365/setgeometry-unable-to-set-geometry)
- [Qt 6 High DPI Documentation](https://doc.qt.io/qt-6/highdpi.html)
- [Qt 6 QWidget Documentation](https://doc.qt.io/qt-6/qwidget.html)
- [Qt Logging Documentation](https://doc.qt.io/qt-6/qtlogging.html)
- [PySide6 QLoggingCategory](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QLoggingCategory.html)
