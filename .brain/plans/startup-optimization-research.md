# Research: Python/PySide6 Application Startup Optimization

**Date**: 2025-12-14
**Scope**: Desktop RPA application with 400+ node types
**Technologies**: Python 3.12, PySide6, Playwright

## Executive Summary

Startup time optimization for Python desktop applications combines several strategies:
1. **Lazy module importing** - Defer heavy imports until needed
2. **Deferred UI initialization** - Show window first, load components after
3. **Background loading** - Use threads for heavy resources
4. **Python-level optimizations** - Bytecode caching, import profiling
5. **Qt-specific patterns** - Splash screens, QTimer.singleShot, QThreadPool

CasareRPA already implements several best practices (lazy node loading, deferred initialization). Additional optimizations can yield 30-50% further improvement.

---

## 1. Lazy Module Importing Strategies

### 1.1 Module-Level `__getattr__` (PEP 562) - RECOMMENDED

CasareRPA already uses this pattern in `nodes/__init__.py`. This is the most Pythonic approach for packages with many optional submodules.

**Pattern:**
```python
# In __init__.py
import importlib
from typing import TYPE_CHECKING

_LAZY_IMPORTS = {
    "HeavyClass": "heavy_module",
    "AnotherClass": "another_module",
}

_loaded_modules = {}
_loaded_classes = {}

def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        if name not in _loaded_classes:
            module_name = _LAZY_IMPORTS[name]
            if module_name not in _loaded_modules:
                _loaded_modules[module_name] = importlib.import_module(
                    f".{module_name}", __package__
                )
            _loaded_classes[name] = getattr(_loaded_modules[module_name], name)
        return _loaded_classes[name]
    raise AttributeError(f"module has no attribute '{name}'")

def __dir__():
    return list(_LAZY_IMPORTS.keys()) + ["__version__"]

# IDE support without runtime import cost
if TYPE_CHECKING:
    from .heavy_module import HeavyClass
    from .another_module import AnotherClass
```

**Benefits:**
- Zero overhead after first access (name rebinding)
- IDE autocompletion preserved via TYPE_CHECKING
- No third-party dependencies

**Sources:**
- [PEP 562 - Module __getattr__ and __dir__](https://peps.python.org/pep-0562/)
- [Snarky.ca - Lazy Importing in Python 3.7](https://snarky.ca/lazy-importing-in-python-3-7/)

### 1.2 PEP 810 - Explicit Lazy Imports (Coming Soon)

Python Steering Council approved PEP 810 in November 2025. New syntax:

```python
lazy import numpy as np  # Only loads on first attribute access
lazy from pandas import DataFrame
```

**Key Features:**
- Proxy object replaces module until first use
- Zero overhead after reification (first use)
- Small one-time cost to create proxy

**Timeline:** Python 3.14+ (experimental), stable in 3.15

**Source:** [PEP 810 - Explicit Lazy Imports](https://peps.python.org/pep-0810/)

### 1.3 importlib.util.LazyLoader

Built-in stdlib support for lazy loading:

```python
import importlib.util

def lazy_import(name):
    spec = importlib.util.find_spec(name)
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module

np = lazy_import("numpy")  # No load yet
np.array([1,2,3])  # NOW numpy loads
```

**Caveat:** "For projects where startup time is critical, LazyLoader allows potentially minimizing the cost. For projects where startup time is not essential, use of this class is heavily discouraged."

**Source:** [Python importlib docs](https://docs.python.org/3/library/importlib.html)

### 1.4 Function-Local Imports

For rarely-used features, move imports inside functions:

```python
def export_to_excel(data):
    import openpyxl  # Only loads when function is called
    # ...
```

**Trade-off:** Import statement executes on every call (though Python caches modules). Use sparingly.

---

## 2. Deferred Widget/UI Initialization

### 2.1 QTimer.singleShot(0, ...) Pattern - CRITICAL

**The "show window first" pattern CasareRPA uses:**

```python
def __init__(self):
    # Fast initial setup
    self._setup_qt_application()
    self._create_ui()  # Creates window structure

    # Show window BEFORE heavy work
    self._main_window.show()
    self._app.processEvents()  # Force paint

    # Defer heavy initialization
    QTimer.singleShot(0, self._heavy_initialization)
```

**Why `singleShot(0)` works:**
- Timeout of 0 means "execute after all pending events are processed"
- Window paint events complete first
- User sees responsive UI immediately

**Source:** [Qt QTimer documentation](https://doc.qt.io/qt-6/qtimer.html)

### 2.2 Progressive UI Loading

For complex UIs (15,000+ widgets), create only visible widgets initially:

```python
class LazyTab(QWidget):
    def __init__(self):
        super().__init__()
        self._initialized = False

    def showEvent(self, event):
        if not self._initialized:
            self._build_ui()  # Deferred widget creation
            self._initialized = True
        super().showEvent(event)
```

**Source:** [Qt Forum - Fast Loading of Complex Interfaces](https://forum.qt.io/topic/160228/fast-loading-of-complex-interfaces)

### 2.3 Virtual/On-Demand Widget Creation

For node palette with 400+ nodes:

```python
class NodePaletteModel(QAbstractItemModel):
    """Only create visual items when scrolled into view."""

    def data(self, index, role):
        if role == Qt.ItemDataRole.DecorationRole:
            # Load icon lazily
            return self._get_or_load_icon(index)
        # ...
```

---

## 3. Background Loading Patterns

### 3.1 QThreadPool + QRunnable - RECOMMENDED

CasareRPA's node preloader uses threading. For Qt apps, QThreadPool is preferred:

```python
from PySide6.QtCore import QRunnable, QThreadPool, Signal, QObject

class WorkerSignals(QObject):
    finished = Signal()
    result = Signal(object)
    progress = Signal(int)

class PreloadWorker(QRunnable):
    def __init__(self, nodes_to_load):
        super().__init__()
        self.nodes = nodes_to_load
        self.signals = WorkerSignals()

    def run(self):
        for i, node_name in enumerate(self.nodes):
            # Import node module
            getattr(casare_rpa.nodes, node_name)
            self.signals.progress.emit(i)
        self.signals.finished.emit()

# Usage
pool = QThreadPool.globalInstance()
worker = PreloadWorker(["LaunchBrowserNode", "ClickElementNode", ...])
worker.signals.finished.connect(on_preload_done)
pool.start(worker)
```

**Benefits:**
- Thread recycling (efficient for repeated tasks)
- Proper Qt event loop integration
- Signal-based progress updates

**Source:** [PythonGUIs - Multithreading PySide6 with QThreadPool](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/)

### 3.2 Priority-Based Preloading

CasareRPA's preloader.py already implements this:

```python
PRELOAD_PRIORITY = [
    # Most commonly used - load first
    "StartNode", "EndNode",
    "IfNode", "ForLoopStartNode",
    # Browser automation
    "LaunchBrowserNode", "ClickElementNode",
    # ... lower priority items
]
```

**Enhancement:** Track actual usage and adjust priority dynamically.

### 3.3 Chunked Loading with Yield

For very large registries, yield to event loop periodically:

```python
def preload_nodes_chunked(chunk_size=10):
    nodes = list(NODE_REGISTRY.keys())
    for i in range(0, len(nodes), chunk_size):
        chunk = nodes[i:i+chunk_size]
        for name in chunk:
            _lazy_import(name)
        yield  # Let event loop process
```

---

## 4. Python Import Optimization Techniques

### 4.1 Import Time Profiling

**Built-in profiler (Python 3.7+):**
```bash
python -X importtime -c "from casare_rpa.presentation.canvas.app import CasareRPAApp" 2>&1 | head -50
```

**Environment variable:**
```bash
PYTHONPROFILEIMPORTTIME=1 python your_app.py 2> imports.log
```

**Visualization with tuna:**
```bash
pip install tuna
python -X importtime app.py 2> import.log
tuna import.log
```

**Source:** [DEV.to - How to speed up Python startup time](https://dev.to/methane/how-to-speed-up-python-application-startup-time-nkf)

### 4.2 Avoid pkg_resources

`pkg_resources` from setuptools is notoriously slow:

```python
# SLOW - avoid
import pkg_resources
version = pkg_resources.get_distribution("mypackage").version

# FAST - use importlib.metadata instead
from importlib.metadata import version
version = version("mypackage")
```

### 4.3 Bytecode Caching

Ensure `.pyc` files are pre-compiled:

```bash
# Pre-compile all modules during installation
pip install --compile your_package

# Or manually compile
python -m compileall src/casare_rpa
```

**Source:** [Real Python - What is __pycache__](https://realpython.com/python-pycache/)

### 4.4 Keep __init__.py Light

Heavy `__init__.py` files slow down any import from that package:

```python
# BAD - heavy __init__.py
# __init__.py
from .module_a import *  # Imports everything
from .module_b import *
import heavy_dependency

# GOOD - light __init__.py
# __init__.py
__version__ = "1.0.0"
# Use __getattr__ for lazy loading
```

---

## 5. Qt/PySide6 Specific Optimizations

### 5.1 Splash Screen Pattern

```python
import sys
from PySide6.QtWidgets import QApplication, QSplashScreen, QMainWindow
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

def main():
    app = QApplication(sys.argv)

    # Show splash immediately
    pixmap = QPixmap("splash.png")
    splash = QSplashScreen(pixmap, Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    # Update splash with progress
    splash.showMessage("Loading nodes...", Qt.AlignBottom | Qt.AlignCenter)
    app.processEvents()

    # Heavy initialization
    import_heavy_modules()

    splash.showMessage("Creating UI...", Qt.AlignBottom | Qt.AlignCenter)
    app.processEvents()

    window = QMainWindow()
    window.show()
    splash.finish(window)

    sys.exit(app.exec())
```

**Source:** [Qt QSplashScreen docs](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplashScreen.html)

### 5.2 Avoid PySide6 Icon Loading Bug

PySide6 6.1.1+ has a known startup delay from icon loading:

```python
# Workaround: Cache icons or use minimal icon set at startup
# Load full icon set in background after window shows
```

**Source:** [Qt Forum - Extremely slow startup time for PySide6](https://forum.qt.io/topic/133093/extremely-slow-startup-time-for-pyside6-vs-pyside2)

### 5.3 Deferred Stylesheet Loading

Complex stylesheets can slow startup:

```python
def __init__(self):
    # Minimal styling first
    self.setStyleSheet("background: #1a1a2e;")

    # Full theme after window shows
    QTimer.singleShot(50, self._apply_full_theme)

def _apply_full_theme(self):
    self.setStyleSheet(load_full_stylesheet())
```

### 5.4 Resource System Optimization

Use Qt's resource system (.qrc) for frequently accessed assets:

```python
# Compile resources
pyside6-rcc resources.qrc -o resources_rc.py

# Import once
import resources_rc

# Access via Qt resource path (fast, cached)
pixmap = QPixmap(":/icons/my_icon.png")
```

---

## 6. Recommendations for CasareRPA

### Already Implemented (Good!)

1. **Lazy node loading** via `__getattr__` in `nodes/__init__.py`
2. **Background preloader** in `nodes/preloader.py`
3. **Deferred initialization** with `QTimer.singleShot(100, ...)`
4. **Show window before heavy init** pattern

### Recommended Improvements

#### High Impact (Estimated 20-30% improvement)

| Optimization | Current State | Recommendation |
|--------------|---------------|----------------|
| Import profiling | Not measured | Run `-X importtime` to find bottlenecks |
| Heavy imports | Unknown | Move Playwright, litellm, httpx imports inside functions |
| Icon preloading | 500ms delay | Consider loading icons from compiled .qrc |
| Stylesheet | Applied at init | Defer complex theme application |

#### Medium Impact (10-20% improvement)

| Optimization | Current State | Recommendation |
|--------------|---------------|----------------|
| QThreadPool | Uses threading | Migrate preloader to QThreadPool |
| Chunk loading | Loads all at once | Add yield points in preload loop |
| Virtual palette | Unknown | Use QAbstractItemModel for node palette |

#### Low Impact (5-10% improvement)

| Optimization | Current State | Recommendation |
|--------------|---------------|----------------|
| pkg_resources | Unknown | Audit and replace with importlib.metadata |
| Bytecode | OS default | Pre-compile during install |
| __init__.py files | Some heavy | Audit all __init__.py for unnecessary imports |

---

## 7. Implementation Priority

### Phase 1: Measurement (1 day)
1. Run import time profiler
2. Identify top 10 slowest imports
3. Establish baseline startup time

### Phase 2: Quick Wins (2-3 days)
1. Move heavy library imports (Playwright, litellm) into functions
2. Audit and fix heavy `__init__.py` files
3. Replace any pkg_resources usage

### Phase 3: UI Optimizations (1 week)
1. Implement splash screen with progress
2. Virtualize node palette (if not already)
3. Defer stylesheet application

### Phase 4: Advanced (2 weeks)
1. Migrate preloader to QThreadPool with signals
2. Implement chunked loading with progress
3. Pre-compile resources to .qrc

---

## Sources

### Python Lazy Imports
- [PEP 562 - Module __getattr__ and __dir__](https://peps.python.org/pep-0562/)
- [PEP 810 - Explicit Lazy Imports](https://peps.python.org/pep-0810/)
- [PEP 690 - Lazy Imports](https://peps.python.org/pep-0690/)
- [Hugo van Kemenade - Three times faster with lazy imports](https://hugovk.dev/blog/2025/lazy-imports/)
- [lazy-imports on PyPI](https://pypi.org/project/lazy-imports/)
- [Python lazy imports you can use today](https://pythontest.com/python-lazy-imports-now/)

### Python Startup Optimization
- [DEV.to - How to speed up Python application startup time](https://dev.to/methane/how-to-speed-up-python-application-startup-time-nkf)
- [Medium - How we improved our Python backend startup time](https://medium.com/alan/how-we-improved-our-python-backend-start-up-time-2c33cd4873c8)
- [Python Startup Time - Victor's notes](https://pythondev.readthedocs.io/startup_time.html)
- [What is __pycache__](https://realpython.com/python-pycache/)

### Qt/PySide6
- [Qt QSplashScreen documentation](https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplashScreen.html)
- [Qt QTimer documentation](https://doc.qt.io/qt-6/qtimer.html)
- [PythonGUIs - Multithreading with QThreadPool](https://www.pythonguis.com/tutorials/multithreading-pyside6-applications-qthreadpool/)
- [Qt Forum - Extremely slow startup time for PySide6](https://forum.qt.io/topic/133093/extremely-slow-startup-time-for-pyside6-vs-pyside2)
- [Qt Forum - Fast loading of complex interfaces](https://forum.qt.io/topic/160228/fast-loading-of-complex-interfaces)

### Heavy Library Optimization
- [TensorFlow lazy loading PR](https://github.com/tensorflow/tensorflow/pull/47833)
- [Scientific Python SPEC 1 - Lazy Loading](https://scientific-python.org/specs/spec-0001/)
- [Medium - When lazy is good: lazy import](https://medium.com/totalenergies-digital-factory/when-lazy-is-good-lazy-import-10bfae7abeb7)
