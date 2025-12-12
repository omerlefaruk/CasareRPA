# Getting Started with CasareRPA

Welcome to CasareRPA! This section will help you install the platform, understand the interface, and create your first automation workflow.

---

## In This Section

| Document | Description |
|----------|-------------|
| [Installation](installation.md) | System requirements and setup |
| [Canvas Overview](canvas-overview.md) | Understanding the visual designer |
| [First Workflow](first-workflow.md) | Build your first automation |
| [Quickstart Examples](quickstart-examples.md) | Ready-to-run example workflows |

---

## Quick Start (5 Minutes)

### 1. Install CasareRPA

```bash
# Install from PyPI
pip install casare-rpa

# Or install from source
git clone https://github.com/your-org/casare-rpa.git
cd casare-rpa
pip install -e .
```

### 2. Launch the Designer

```bash
python run.py
```

### 3. Create Your First Workflow

1. **Add a Start Node**: Already present on new canvas
2. **Add a Log Node**: Drag from palette → Basic → Log Message
3. **Connect**: Draw from Start's output to Log's input
4. **Configure**: Click Log node, set message to "Hello, CasareRPA!"
5. **Run**: Press F5 or click the Run button

```
[Start] → [Log Message: "Hello, CasareRPA!"]
```

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10 | Windows 11 |
| **Python** | 3.12 | 3.12 |
| **RAM** | 4 GB | 8 GB |
| **Disk** | 500 MB | 1 GB |
| **Display** | 1280x720 | 1920x1080 |

### Optional Dependencies

| Feature | Requirement |
|---------|-------------|
| Browser automation | Playwright browsers |
| Desktop automation | Windows Desktop |
| Office automation | Microsoft Office |
| PDF processing | Poppler |

---

## Interface Overview

```
┌─────────────────────────────────────────────────────────┐
│  File  Edit  View  Run  Tools  Help          [🔍] [⚙️] │
├──────────┬──────────────────────────────────┬───────────┤
│          │                                  │           │
│  Node    │                                  │ Property  │
│  Palette │        Canvas Area               │  Panel    │
│          │                                  │           │
│  [Browser]│    ┌───────┐    ┌───────┐       │ Node: Log │
│  [Desktop]│    │ Start ├───→│  Log  │       │           │
│  [Data]   │    └───────┘    └───────┘       │ Message:  │
│  [HTTP]   │                                  │ [Hello]   │
│  ...      │                                  │           │
├──────────┴──────────────────────────────────┴───────────┤
│  Logs  │  Variables  │  Breakpoints  │  Output         │
│  [Execution log messages appear here...]                │
└─────────────────────────────────────────────────────────┘
```

---

## Next Steps

| Goal | Document |
|------|----------|
| Understand the canvas | [Canvas Overview](canvas-overview.md) |
| Build a real workflow | [First Workflow](first-workflow.md) |
| See examples | [Quickstart Examples](quickstart-examples.md) |
| Learn core concepts | [Core Concepts](../core-concepts/index.md) |

---

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Run workflow | `F5` |
| Stop execution | `Shift+F5` |
| Save workflow | `Ctrl+S` |
| Undo | `Ctrl+Z` |
| Delete selected | `Delete` |
| Zoom in/out | `Ctrl+Wheel` |
| Pan canvas | `Middle Mouse Drag` |

---

## Related Documentation

- [Core Concepts](../core-concepts/index.md)
- [Tutorials](../tutorials/index.md)
- [Node Reference](../../reference/nodes/index.md)
