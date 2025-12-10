# GPU Acceleration Implementation Plan

**Date**: 2025-12-09
**Status**: COMPLETED (Phase 1)
**Priority**: High - 15-50x performance improvement potential

---

## Executive Summary

Enable GPU acceleration across CasareRPA for:
- Canvas rendering (OpenGL viewport)
- Image processing (CUDA/OpenCV)
- OCR inference (ONNX GPU runtime)

---

## Phase 1: Quick Wins (1-2 days) - IMPLEMENTING NOW

### 1.1 OpenGL Viewport for Canvas
| Attribute | Value |
|-----------|-------|
| File | `node_graph_widget.py` |
| Impact | 30-50x faster for 500+ nodes |
| Effort | 20 LOC |
| Risk | Medium (driver compatibility) |

**Implementation:**
```python
from PySide6.QtOpenGL import QOpenGLWidget
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QSurfaceFormat

# Set format for OpenGL
fmt = QSurfaceFormat()
fmt.setSamples(4)  # MSAA antialiasing
fmt.setSwapInterval(1)  # VSync
QSurfaceFormat.setDefaultFormat(fmt)

# Set OpenGL viewport
gl_widget = QOpenGLWidget()
view.setViewport(gl_widget)
view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
```

### 1.2 GPU-Accelerated OCR
| Attribute | Value |
|-----------|-------|
| File | `screen_capture.py` |
| Impact | 3-8x faster OCR |
| Effort | 5 LOC |
| Risk | Low (CPU fallback) |

**Implementation:**
```python
# Change ONNX runtime to use GPU if available
try:
    import onnxruntime as ort
    providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
    # RapidOCR will auto-detect GPU
except ImportError:
    providers = ['CPUExecutionProvider']
```

### 1.3 Hardware-Accelerated Rendering Hints
| Attribute | Value |
|-----------|-------|
| File | `custom_node_item.py`, `custom_pipe.py` |
| Impact | 2-3x smoother animations |
| Effort | 10 LOC |
| Risk | Low |

---

## Phase 2: Image Processing GPU (3-5 days)

### 2.1 cv2.cuda for Template Matching
- File: `screen_capture.py:477-482`
- Fallback: CPU if no CUDA available

### 2.2 GPU Array Operations
- Use `cupy` as numpy drop-in replacement
- Fallback: numpy if no GPU

---

## Phase 3: Advanced GPU Features (Future)

### 3.1 Custom Shaders for Wire Rendering
- OpenGL fragment shaders for bezier curves
- Instanced rendering for batch performance

### 3.2 GPU Occlusion Queries
- Hardware culling for viewport optimization

---

## Implementation Order

1. [x] Plan created
2. [x] Enable OpenGL viewport in node_graph_widget.py (already existed at lines 714-735)
3. [x] GPU utility module created (utils/gpu/gpu_utils.py)
4. [x] GPU template matching in screen_capture.py (lines 476-486)
5. [x] GPU template matching in cv_healer.py (lines 891-896)
6. [x] GPU OCR configuration with ONNX providers (lines 198-200)
7. [ ] Test on systems with/without GPU

---

## Fallback Strategy

All GPU features must have CPU fallback:
```python
try:
    # GPU path
except Exception:
    # CPU fallback
```

---

## Files to Modify

| File | Change |
|------|--------|
| `node_graph_widget.py` | OpenGL viewport |
| `custom_node_item.py` | GPU render hints |
| `custom_pipe.py` | GPU render hints |
| `screen_capture.py` | GPU OCR config |
