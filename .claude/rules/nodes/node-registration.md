---
paths: src/casare_rpa/nodes/**/*.py, src/casare_rpa/presentation/canvas/visual_nodes/**/*.py
---

# Node Registration Checklist

When creating or modifying nodes, follow this 5-step process:

## Step 1: Logic Node Export
**File**: `nodes/{category}/__init__.py`
**Action**: Export the node class

```python
from .my_node import MyNode
__all__ = ["MyNode"]
```

## Step 2: Node Registry
**File**: `nodes/__init__.py`
**Action**: Add to `_NODE_REGISTRY`

```python
_NODE_REGISTRY = {
    # ...existing nodes...
    "MyNode": ("casare_rpa.nodes.category", "MyNode"),
}
```

## Step 3: Workflow Loader
**File**: `workflow_loader.py`
**Action**: Add to `NODE_TYPE_MAP`

```python
NODE_TYPE_MAP = {
    # ...existing mappings...
    "MyNode": MyNode,
}
```

## Step 4: Visual Node
**File**: `visual_nodes/{category}/nodes.py`
**Action**: Create `VisualMyNode` class

```python
class VisualMyNode(BaseVisualNode):
    NODE_NAME = "MyNode"
    # ...implementation...
```

### ⚠️ CRITICAL: @properties Auto-Generation

**NEVER manually add widgets for properties already defined in `@properties`!**

The `@properties` decorator on the logic layer node auto-generates widgets. Adding them again in the visual node causes:
```
NodePropertyError: "pattern" property already exists
```

#### ❌ WRONG - Duplicate widget
```python
# Logic node has: @properties(PropertyDef("pattern", ...))
class VisualListDirectoryNode(VisualNode):
    def __init__(self):
        super().__init__()
        self.add_text_input("pattern", ...)  # ERROR! Already auto-generated
```

#### ✅ CORRECT - Let schema handle it
```python
class VisualListDirectoryNode(VisualNode):
    def __init__(self):
        super().__init__()
        # pattern, recursive, etc. are auto-generated from @properties
        # Only add CUSTOM widgets not in schema (e.g., file path picker)
        _replace_widget(self, NodeDirectoryPathWidget(name="dir_path", ...))
```

#### When to Use `_replace_widget()`
Use ONLY when replacing an auto-generated widget with a custom one (e.g., file picker):
```python
_replace_widget(self, NodeFilePathWidget(name="file_path", ...))
```

#### Rule: Check Logic Node First
Before adding ANY widget in visual node `__init__`:
1. Check if property exists in logic node's `@properties`
2. If YES → Do NOT add widget (auto-generated)
3. If NO → Safe to add widget manually

## Step 5: Visual Registry
**File**: `visual_nodes/__init__.py`
**Action**: Add to `_VISUAL_NODE_REGISTRY`

```python
_VISUAL_NODE_REGISTRY = {
    # ...existing visual nodes...
    "MyNode": VisualMyNode,
}
```

## Verification

After registration, verify:
- [ ] Node appears in canvas palette
- [ ] Node can be dragged onto canvas
- [ ] Node properties display correctly (no "property already exists" errors)
- [ ] No duplicate widgets (check @properties vs visual node __init__)
- [ ] Node executes without errors
- [ ] Node saves/loads in workflow JSON
