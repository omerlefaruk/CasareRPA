# Anchor-Based Selector System Overhaul

## Problem Statement

CasareRPA has complete anchor infrastructure (AnchorLocator, AnchorModel, AnchorHealer) but interactive nodes (ClickElement, TypeText, etc.) **cannot use anchors** because:

1. No `anchor_selector` property in node schemas
2. Dialog captures anchor but doesn't save to node config
3. Nodes don't read/use anchor data at execution time

## Goal

Enable users to:
1. Pick an anchor element in ElementSelectorDialog
2. Have anchor data persist in workflow JSON
3. Use anchor for reliable element location at runtime

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       NEW DATA FLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. UI: ElementSelectorDialog                                   │
│     └─ User picks target + anchor                               │
│     └─ Returns SelectorResult with anchor config                │
│                                                                  │
│  2. SelectorInputWidget receives result                         │
│     └─ Stores selector in "selector" property                   │
│     └─ NEW: Stores anchor in "anchor_config" property (JSON)    │
│                                                                  │
│  3. Workflow JSON                                                │
│     {                                                            │
│       "selector": "#submit-btn",                                │
│       "anchor_config": {                                         │
│         "enabled": true,                                         │
│         "selector": "label[for='email']",                        │
│         "position": "above",                                     │
│         "text": "Email Address"                                  │
│       }                                                          │
│     }                                                            │
│                                                                  │
│  4. Execution: BrowserBaseNode                                  │
│     └─ Reads anchor_config                                       │
│     └─ Uses AnchorLocator.find_element_with_anchor()            │
│     └─ Falls back to direct selector if anchor fails            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Backend - Property & Execution (architect)

#### 1.1 Add Anchor PropertyDef Constants
File: `src/casare_rpa/nodes/browser/property_constants.py`

```python
ANCHOR_CONFIG = PropertyDef(
    "anchor_config",
    PropertyType.JSON,
    default="",
    label="Anchor Configuration",
    tooltip="JSON config for anchor-based element location",
    tab="advanced",
)
```

#### 1.2 Update Node Schemas
Files: `src/casare_rpa/nodes/interaction_nodes.py`, `navigation_nodes.py`

Add `ANCHOR_CONFIG` to all browser nodes:
- ClickElementNode
- TypeTextNode
- HoverElementNode
- SelectOptionNode
- GetTextNode
- GetAttributeNode
- WaitForElementNode
- etc.

#### 1.3 Implement Anchor-Based Execution in BrowserBaseNode
File: `src/casare_rpa/nodes/browser/browser_base.py`

Add method:
```python
async def find_element_with_anchor(
    self,
    page,
    selector: str,
    anchor_config: dict,
) -> Optional[ElementHandle]:
    """Find element using anchor if configured, fallback to direct selector."""
```

#### 1.4 Create Anchor Config Dataclass
File: `src/casare_rpa/nodes/browser/anchor_config.py` (NEW)

```python
@dataclass
class NodeAnchorConfig:
    enabled: bool = False
    selector: str = ""
    position: str = "near"  # left, right, above, below, near
    text: str = ""  # Display text for UI
    offset_x: int = 0
    offset_y: int = 0

    @classmethod
    def from_json(cls, json_str: str) -> "NodeAnchorConfig"

    def to_json(self) -> str
```

### Phase 2: UI - Selector Input Widget (ui)

#### 2.1 Create AnchorSelectorWidget
File: `src/casare_rpa/presentation/canvas/ui/widgets/anchor_selector_widget.py` (NEW)

A compound widget that replaces SelectorInputWidget for selector properties:

```
┌────────────────────────────────────────────────────────────────┐
│ Element Selector                                                │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ #submit-btn                                    [...]      │   │
│ └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│ ☑ Use Anchor                                                   │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ label[for='email']                             [Pick]    │   │
│ └──────────────────────────────────────────────────────────┘   │
│ Position: [Above ▼]  "Email Address"                           │
└────────────────────────────────────────────────────────────────┘
```

Features:
- Collapsible anchor section (hidden by default)
- Pick Anchor button opens ElementSelectorDialog in anchor mode
- Shows anchor text preview
- Position dropdown
- Clear anchor button

#### 2.2 Update ElementSelectorDialog Result Handling
File: `src/casare_rpa/presentation/canvas/selectors/element_selector_dialog.py`

Ensure `_on_confirm()` populates SelectorResult.anchor properly.

#### 2.3 Integrate with Properties Panel
File: `src/casare_rpa/presentation/canvas/ui/panels/properties_panel.py`

When PropertyType.SELECTOR is encountered:
- Use AnchorSelectorWidget instead of SelectorInputWidget
- Pass both "selector" and "anchor_config" to widget
- Save both values when changed

### Phase 3: Serialization

#### 3.1 Update Workflow Serialization
File: `src/casare_rpa/presentation/canvas/serialization/workflow_serializer.py`

Ensure anchor_config JSON is properly serialized/deserialized.

#### 3.2 Update Workflow Loader
File: `src/casare_rpa/utils/workflow/workflow_loader.py`

No changes needed - JSON property types are already supported.

### Phase 4: Testing

#### 4.1 Unit Tests
- `tests/nodes/browser/test_anchor_execution.py`
- `tests/presentation/ui/test_anchor_selector_widget.py`

#### 4.2 Integration Tests
- Test full flow: pick element + anchor → save workflow → load → execute

## File Changes Summary

| File | Change |
|------|--------|
| `nodes/browser/property_constants.py` | Add ANCHOR_CONFIG |
| `nodes/browser/anchor_config.py` | NEW - NodeAnchorConfig dataclass |
| `nodes/browser/browser_base.py` | Add find_element_with_anchor() |
| `nodes/interaction_nodes.py` | Add ANCHOR_CONFIG to schemas |
| `nodes/navigation_nodes.py` | Add ANCHOR_CONFIG to schemas |
| `presentation/canvas/ui/widgets/anchor_selector_widget.py` | NEW - Compound widget |
| `presentation/canvas/ui/widgets/__init__.py` | Export AnchorSelectorWidget |
| `presentation/canvas/selectors/element_selector_dialog.py` | Fix anchor result population |
| `presentation/canvas/visual_nodes/base_visual_node.py` | Use AnchorSelectorWidget for SELECTOR type |

## Unresolved Questions

1. Should anchor_config be a separate property or embedded in selector string?
   - **Decision**: Separate JSON property in "advanced" tab for clean separation

2. How to handle anchor validation at runtime?
   - **Decision**: Log warning if anchor not found, fallback to direct selector

3. Should we support multiple anchors (redundancy)?
   - **Decision**: Start with single anchor, add multi-anchor in v2

4. How to show anchor status in canvas?
   - **Decision**: Add small anchor icon badge on nodes with anchor configured

## Success Criteria

1. User can pick anchor in ElementSelectorDialog
2. Anchor persists in workflow JSON
3. Node uses anchor at execution time
4. Falls back gracefully if anchor missing
5. UI shows anchor configuration clearly

## Timeline Estimate

- Phase 1 (Backend): 2-3 hours
- Phase 2 (UI): 2-3 hours
- Phase 3 (Serialization): 1 hour
- Phase 4 (Testing): 1-2 hours

Total: ~8 hours
