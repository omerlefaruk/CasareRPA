# Action Recorder Plan

**Status**: COMPLETE
**Created**: 2025-12-01
**Priority**: HIGH (productivity boost)

## Overview

Implement browser action recording and enhance desktop recording integration. Desktop recording is 90% complete; focus is on browser recording via Playwright.

## Current Status

### Desktop Recording - COMPLETE
- `src/casare_rpa/desktop/desktop_recorder.py` - Core engine
- `src/casare_rpa/presentation/canvas/desktop/desktop_recording_panel.py` - UI
- Captures: clicks, keyboard, drag, window activation
- Converts to workflow nodes

### Browser Recording - TODO
- No implementation exists
- Need Playwright event capture
- Need selector generation
- Need node conversion

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Recording Layer                           │
├─────────────────────────────────────────────────────────────┤
│  BrowserRecorder                                             │
│  ├── Event Listener (CDP/Playwright)                        │
│  ├── Selector Generator (smart selectors)                    │
│  ├── Action Optimizer (merge, dedupe)                        │
│  └── Workflow Generator (to browser nodes)                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Integration                               │
├─────────────────────────────────────────────────────────────┤
│  - Canvas integration for live recording                     │
│  - Combined desktop/browser recording                        │
│  - Action editing before workflow generation                 │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Browser Recorder Core - IN PROGRESS
- [x] Create `src/casare_rpa/utils/recording/__init__.py`
- [x] Create `src/casare_rpa/utils/recording/browser_recorder.py`
  - Event capture via Playwright page events
  - Click, type, navigation capture
  - Smart selector generation

### Phase 2: Action Processing
- [x] Create `src/casare_rpa/utils/recording/action_processor.py`
  - Action merging (consecutive text input)
  - Deduplication
  - Wait insertion

### Phase 3: Workflow Generation
- [x] Create `src/casare_rpa/utils/recording/workflow_generator.py`
  - Map to browser nodes
  - Generate workflow JSON
  - Support both browser and desktop actions

### Phase 4: Tests
- [ ] Unit tests for recorder
- [ ] Tests for action processor
- [ ] Tests for workflow generator

## Browser Action Types

| Action Type | Captured From | Target Node |
|-------------|---------------|-------------|
| NAVIGATE | page.on('load') | GoToURLNode |
| CLICK | mouse.click event | ClickElementNode |
| TYPE | keyboard input | TypeTextNode |
| SELECT | select change | SelectDropdownNode |
| SCROLL | scroll event | ScrollNode |
| WAIT_NAVIGATION | navigation event | WaitForNavigationNode |
| SCREENSHOT | user request | ScreenshotNode |

## Recorded Action Schema

```python
@dataclass
class BrowserRecordedAction:
    action_type: BrowserActionType
    timestamp: datetime
    url: str
    selector: Optional[str]
    value: Optional[str]  # For text input
    coordinates: Optional[Tuple[int, int]]
    element_info: Dict[str, Any]  # tag, id, classes, text

    def to_node_config(self) -> Dict[str, Any]
    def get_description(self) -> str
```

## Dependencies

- Playwright (already installed)
- No new dependencies required

## Unresolved Questions

1. Should recording capture all navigations or just user-initiated?
2. How to handle dynamic content (SPAs with route changes)?
3. Should we capture network requests for API workflows?
