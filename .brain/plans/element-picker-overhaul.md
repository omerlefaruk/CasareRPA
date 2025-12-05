# Element Picker UI/UX Complete Overhaul

**Author**: Research Agent
**Date**: 2025-12-05
**Status**: PLAN
**Priority**: HIGH

---

## 1. Current State Analysis

### 1.1 Existing Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `selectors/unified_selector_dialog.py` | Main UiPath-inspired dialog | ~2300 | Complex, needs refactor |
| `selectors/selector_dialog.py` | Legacy simple dialog | ~600 | Deprecated, remove |
| `selectors/element_picker.py` | Desktop overlay picker | ~270 | Functional, needs polish |
| `selectors/ui_explorer/ui_explorer_dialog.py` | Advanced 4-panel inspector | ~1200 | Feature-rich but slow |
| `selectors/tabs/browser_tab.py` | Browser picking tab | ~490 | Good foundation |
| `selectors/tabs/desktop_tab.py` | Desktop picking tab | ~200 | Stub implementation |
| `selectors/tabs/ocr_tab.py` | OCR-based selection | ~150 | Basic |
| `selectors/tabs/image_match_tab.py` | Template matching | ~200 | Basic |
| `ui/widgets/selector_input_widget.py` | Properties panel widget | ~236 | Clean, good |

### 1.2 Architecture Overview

```
User Interaction Flow:

  Properties Panel          Quick Pick             Advanced
  [selector ][...]    OR    Ctrl+Click       OR    UI Explorer
        |                      |                      |
        v                      v                      v
+------------------+    +--------------+    +------------------+
| SelectorInput    |    | Browser Tab  |    | UIExplorerDialog |
| Widget           |--->| start_       |--->| (4-panel layout) |
+------------------+    | picking()    |    +------------------+
                        +--------------+
                               |
                               v
                    +-------------------+
                    | SelectorManager   |
                    | (JS Injector)     |
                    +-------------------+
                               |
                               v
                    +-------------------+
                    | SmartSelector     |
                    | Generator         |
                    +-------------------+
                               |
                               v
                    +-------------------+
                    | SelectorResult    |
                    | + Healing Context |
                    +-------------------+
```

### 1.3 Current UI Layout (UnifiedSelectorDialog)

```
+----------------------------------------------------------+
| [Pause] [Browser][Desktop][Image][OCR] [Settings][UIExp] |  <- Mode toolbar
+----------------------------------------------------------+
| [Anchor Section - Collapsible]                           |
|   [Pick Anchor][Auto-detect][Clear]                      |
|   Position: [Left v] label[for="user"]                   |
+----------------------------------------------------------+
| [Options Section - Collapsible]                          |
|   Window Selector: <wnd app=.../>                        |
|   [x] Wait visible  [ ] Highlight before action          |
+----------------------------------------------------------+
| [Target Section - Expanded]                              |
|   [Quick Text Search] Element:[*v] Text:[______][Gen]    |
|   +-- Strict selector ----+                              |
|   | [x] Strict selector   [Copy][Pick]                   |
|   | [selector text area                        ]         |
|   +-- Fuzzy selector ----+                               |
|   | [ ] Fuzzy selector    [Copy][Pick]                   |
|   | Accuracy: [========80%]                              |
|   +-- Computer Vision ----+                              |
|   | [ ] CV selector       [Copy][Pick]                   |
|   | Element type: [Button v] Text: [____]                |
|   +-- Image Template ----+                               |
|   | [ ] Image             [Copy][Pick]                   |
|   | [Preview] [Capture][Load]                            |
+----------------------------------------------------------+
| [Generated Selectors - Collapsible]                      |
|   (list of strategies sorted by score)                   |
+----------------------------------------------------------+
| [Validate]                    [Confirm]      [Cancel]    |
+----------------------------------------------------------+
```

---

## 2. UX Pain Points Identified

### 2.1 Critical Issues

| Issue | Severity | Description |
|-------|----------|-------------|
| **Too Many Panels** | HIGH | 2 separate dialogs (Unified + UIExplorer) creates confusion |
| **No Live Preview** | HIGH | User cannot see highlighted element while building selector |
| **Slow Picking** | HIGH | Ctrl+Click requires browser focus, not intuitive |
| **Anchor Friction** | MEDIUM | Anchor setup is separate from main flow, feels disconnected |
| **No Validation Feedback** | MEDIUM | Match count shown only after explicit Validate click |
| **Overwhelming Options** | MEDIUM | Fuzzy/CV/Image options visible always, rarely used |
| **No History** | LOW | Cannot recall previously picked selectors |
| **Desktop Tab Incomplete** | LOW | Desktop selector tab is a stub |

### 2.2 User Journey Problems

1. **Discovery**: User doesn't know which mode to use (Browser vs Desktop vs OCR)
2. **Picking**: Must switch to browser, Ctrl+Click, return to dialog
3. **Refinement**: Generated selectors shown in small list, hard to compare
4. **Validation**: Manual click required, no auto-validate
5. **Anchor Setup**: Separate step, not guided
6. **Healing Context**: Captured silently, user doesn't understand value

### 2.3 Technical Debt

- `selector_dialog.py` is legacy, duplicates `unified_selector_dialog.py`
- `element_picker.py` only works for desktop, no browser equivalent
- Tab classes (`browser_tab.py` etc.) are hidden, not displayed to user
- `UIExplorerDialog` is powerful but rarely opened (buried under button)
- Collapsible sections use custom widget, could use Qt QGroupBox

---

## 3. Competitive Analysis

### 3.1 UiPath Modern Selector

**Strengths:**
- Unified "Indicate Element" button that auto-detects target type
- Live element tree with instant selector preview
- Anchor-target relationship visualized graphically
- Fuzzy matching with accuracy slider (80% default)
- Auto-repair/healing agent in latest versions (v25.10)
- WEBCTRL selectors auto-generated

**Key UX Patterns:**
- Single dialog for all selector types
- "Indicate" is primary action, not text input
- Selector attributes shown as checkboxes (toggle inclusion)
- Preview panel with syntax highlighting (XML)
- Status bar shows match count in real-time

### 3.2 Power Automate Desktop

**Strengths:**
- UIA/MSAA toggle for legacy apps
- Text-based selector capture (right-click menu)
- Custom screens for date pickers, dropdowns
- Real-time recorder feedback
- MSAA banner when in legacy mode

**Key UX Patterns:**
- Right-click context menu for advanced options
- Mode indicator visible at all times
- Hierarchical element tree with search
- Capture modes: Click, Hover, Right-click

### 3.3 Automation Anywhere

**Strengths:**
- AISense for automatic UI object detection
- Generative Recorder with GenAI fallback
- Three recorder types: Smart, Screen, Web
- Coordinates/Objects/Images selection modes

**Key UX Patterns:**
- AI-first approach (auto-detect UI elements)
- Fallback chain visible to user
- Cloud-based healing recommendations

### 3.4 Feature Comparison Matrix

| Feature | CasareRPA Current | UiPath | Power Automate | AA |
|---------|-------------------|--------|----------------|-----|
| Single Indicate Button | No (mode-specific) | Yes | Yes | Yes |
| Live Element Highlight | Partial | Yes | Yes | Yes |
| Anchor System | Yes | Yes | No | Limited |
| Fuzzy/CV/Image Fallback | Yes (separate) | Integrated | No | AISense |
| Auto-Validation | No | Yes | Yes | Yes |
| Element Tree | UIExplorer only | Integrated | Integrated | Integrated |
| Self-Healing | Backend only | Visual | Limited | GenAI |
| Desktop/Browser Unified | Partial | Yes | Yes | No |
| Recording Mode | Backend | Yes | Yes | Yes |
| History/Favorites | No | Yes | No | No |

---

## 4. Proposed New Architecture

### 4.1 Design Principles

1. **Single Entry Point**: One "Indicate Element" action for all modes
2. **Live Feedback**: Always show element highlight while dialog is open
3. **Progressive Disclosure**: Simple mode first, advanced options on demand
4. **Inline Validation**: Auto-validate as user edits selector
5. **Guided Anchoring**: Anchor suggestion as part of main flow
6. **Visual Healing Context**: Show what will be stored for healing

### 4.2 New Dialog Structure

```
+----------------------------------------------------------------------+
| Element Selector                                            [_][X]   |
+----------------------------------------------------------------------+
| [Pick Element]  [Stop]     Mode: [Auto v]     [Settings] [History]   |
+----------------------------------------------------------------------+
|                                                                      |
|  +--- Element Preview -------------------------------------------+   |
|  |  <button class="btn-primary" id="submit">Submit</button>     |   |
|  |  -----------------------------------------------------------  |   |
|  |  Tag: BUTTON | ID: submit | Classes: btn-primary             |   |
|  |  Text: "Submit" | Visible: Yes | Enabled: Yes                |   |
|  +---------------------------------------------------------------+   |
|                                                                      |
|  +--- Selector Builder ------------------------------------------+   |
|  |  [x] id         submit                        Score: 95       |   |
|  |  [x] class      btn-primary                   Score: 70       |   |
|  |  [ ] text       Submit                        Score: 60       |   |
|  |  [ ] xpath      //button[@id='submit']        Score: 90       |   |
|  |  -----------------------------------------------------------  |   |
|  |  Generated: #submit                           Matches: 1      |   |
|  +---------------------------------------------------------------+   |
|                                                                      |
|  +--- Anchor (Optional) -----------------------------------------+   |
|  |  [ ] Use anchor for reliability                               |   |
|  |  [Suggest Anchor]  Anchor: (none)  Position: [Left v]        |   |
|  +---------------------------------------------------------------+   |
|                                                                      |
|  +--- Advanced [>] ---------------------------------------------+    |
|  |  (collapsed by default: Fuzzy, CV, Image, Healing options)   |   |
|  +---------------------------------------------------------------+   |
|                                                                      |
+----------------------------------------------------------------------+
| Matches: 1 unique | Validation: Passed | Mode: Browser (Playwright) |
+----------------------------------------------------------------------+
|                                          [Cancel]  [Use Selector]   |
+----------------------------------------------------------------------+
```

### 4.3 Component Hierarchy

```
ElementSelectorDialog (new unified dialog)
    |
    +-- ToolbarWidget
    |       +-- IndicateButton (primary action)
    |       +-- StopButton
    |       +-- ModeDropdown (Auto/Browser/Desktop/OCR/Image)
    |       +-- SettingsButton
    |       +-- HistoryButton
    |
    +-- ElementPreviewWidget
    |       +-- HTMLPreview (syntax highlighted)
    |       +-- PropertyGrid (Tag, ID, Classes, Text)
    |
    +-- SelectorBuilderWidget
    |       +-- AttributeRow[] (checkbox + name + value + score)
    |       +-- GeneratedSelectorDisplay
    |       +-- MatchCountBadge (real-time)
    |
    +-- AnchorWidget (collapsible)
    |       +-- EnableCheckbox
    |       +-- SuggestButton
    |       +-- AnchorDisplay
    |       +-- PositionDropdown
    |
    +-- AdvancedOptionsWidget (collapsible)
    |       +-- FuzzyOptionsPanel
    |       +-- CVOptionsPanel
    |       +-- ImageOptionsPanel
    |       +-- HealingContextPanel
    |
    +-- StatusBarWidget
    |       +-- MatchCountLabel
    |       +-- ValidationStatusLabel
    |       +-- ModeLabel
    |
    +-- ActionButtonsWidget
            +-- CancelButton
            +-- UseSelectorButton
```

### 4.4 State Management

```python
@dataclass
class ElementSelectorState:
    """Centralized state for element selector dialog."""

    # Mode
    mode: Literal["auto", "browser", "desktop", "ocr", "image"] = "auto"
    is_picking: bool = False

    # Current element
    element: Optional[ElementFingerprint] = None
    element_preview_html: str = ""
    element_properties: Dict[str, Any] = field(default_factory=dict)

    # Selector building
    selected_attributes: List[str] = field(default_factory=list)
    generated_selector: str = ""
    selector_type: str = "css"  # css, xpath, aria, etc.
    match_count: int = 0
    is_unique: bool = False
    validation_status: Literal["pending", "valid", "invalid", "error"] = "pending"

    # Anchor
    anchor_enabled: bool = False
    anchor_element: Optional[ElementFingerprint] = None
    anchor_position: str = "left"

    # Advanced
    fuzzy_enabled: bool = False
    fuzzy_accuracy: float = 0.8
    cv_enabled: bool = False
    cv_template: Optional[bytes] = None
    image_enabled: bool = False
    image_template: Optional[bytes] = None

    # Healing context
    capture_fingerprint: bool = True
    capture_spatial: bool = True
    capture_cv: bool = False

    # History
    recent_selectors: List[str] = field(default_factory=list)
```

---

## 5. UI Mockup Descriptions

### 5.1 Main Dialog - Initial State

**Layout**: 600x500px minimum, resizable
**Theme**: Dark mode (#1e1e1e background)

**Top Toolbar**:
- Large blue "Pick Element" button (40px height) with finger icon
- "Stop" button (hidden when not picking)
- Mode dropdown: "Auto" (default), "Browser", "Desktop", "OCR", "Image"
- Settings gear icon (opens preferences)
- History clock icon (opens recent selectors)

**Element Preview** (collapsed when no element):
- Monospace font, syntax-highlighted HTML
- Property badges: Tag, ID, Classes, Text preview
- Small "Open in UI Explorer" link

**Selector Builder** (main content):
- List of attributes as rows
- Each row: [checkbox] [attribute name] [value] [score bar]
- Checkboxes toggle inclusion in final selector
- Score bar: green (80+), yellow (60-79), red (<60)
- Generated selector in monospace below list
- "Matches: N" badge updates as attributes toggled

**Anchor Section** (collapsed by default):
- Simple checkbox: "Use anchor for reliability"
- "Suggest Anchor" button auto-finds nearby label/heading
- Position dropdown when anchor set

**Advanced Section** (collapsed by default):
- Tabs: Fuzzy | CV | Image | Healing
- Each tab has mode-specific options

**Status Bar** (24px fixed):
- Left: Match count with icon (1 = green checkmark, >1 = yellow warning, 0 = red X)
- Center: Validation status
- Right: Mode indicator (Browser/Desktop)

**Action Buttons**:
- Cancel (gray, left)
- Use Selector (blue, right, disabled until valid)

### 5.2 Picking Mode

When user clicks "Pick Element":
1. Dialog minimizes to small floating toolbar (200x48px)
2. Toolbar shows: "Click element..." + [Cancel] button
3. Browser/desktop overlay activates with red highlight on hover
4. On click: element captured, dialog restores, preview populated

### 5.3 Selector Builder Interactions

**Attribute Row**:
```
[x] id="submit"                    [=======95]
    ^checkbox  ^attribute           ^score bar (green)
```

- Click checkbox: toggles attribute in generated selector
- Click row (not checkbox): expands to show full value
- Drag rows: reorder priority
- Double-click value: edit inline

**Generated Selector**:
```
#submit.btn-primary                 Matches: 1 [Validate]
^generated selector                 ^badge     ^button
```

- Editable text field with Consolas font
- Syntax highlighting (blue for IDs, green for classes)
- "Matches" badge updates on every change (debounced 300ms)
- Validate button runs full test and shows timing

### 5.4 Anchor Workflow

When user enables anchor:
1. "Suggest Anchor" auto-finds nearest label/heading
2. Anchor preview shows: `<label> "Username" (to the left)`
3. Position dropdown: Left, Right, Above, Below
4. Final selector includes anchor context for healing

### 5.5 History Panel

Dropdown shows recent selectors:
```
+-- Recent Selectors ----------------------+
|  #submit              (2 min ago)       |
|  .login-form input    (5 min ago)       |
|  //button[text()]     (1 hour ago)      |
+------------------------------------------+
```

Click to reuse, with confirmation if current element differs.

---

## 6. Implementation Phases

### Phase 1: Core Dialog Refactor (3-4 days)

**Goal**: Replace UnifiedSelectorDialog with new ElementSelectorDialog

**Tasks**:
1. Create `ElementSelectorState` dataclass
2. Create `ElementSelectorDialog` with new layout
3. Create `ToolbarWidget` with Pick/Stop/Mode
4. Create `ElementPreviewWidget` with HTML preview
5. Create `SelectorBuilderWidget` with attribute rows
6. Connect to existing `SelectorManager` and `SmartSelectorGenerator`

**Files to Create**:
- `selectors/element_selector_dialog.py`
- `selectors/widgets/toolbar_widget.py`
- `selectors/widgets/element_preview_widget.py`
- `selectors/widgets/selector_builder_widget.py`
- `selectors/state/selector_state.py`

### Phase 2: Live Validation & Feedback (2 days)

**Goal**: Real-time match count and validation

**Tasks**:
1. Add debounced auto-validation on selector change
2. Update MatchCountBadge in real-time
3. Add validation status to status bar
4. Add highlight toggle (show matched elements in browser)

**Files to Modify**:
- `selectors/element_selector_dialog.py`
- `utils/selectors/selector_manager.py`

### Phase 3: Anchor Integration (2 days)

**Goal**: Seamless anchor configuration

**Tasks**:
1. Create `AnchorWidget` with suggest button
2. Integrate with `AnchorLocator` utility
3. Show anchor relationship visually
4. Include anchor in final SelectorResult

**Files to Create**:
- `selectors/widgets/anchor_widget.py`

**Files to Modify**:
- `utils/selectors/anchor_locator.py`

### Phase 4: Advanced Options (2 days)

**Goal**: Fuzzy, CV, Image options in collapsible section

**Tasks**:
1. Create `AdvancedOptionsWidget` with tabs
2. Move Fuzzy/CV/Image options from old dialog
3. Add Healing Context visibility panel
4. Connect to healing chain for context capture

**Files to Create**:
- `selectors/widgets/advanced_options_widget.py`

### Phase 5: History & Settings (1 day)

**Goal**: Recent selectors and preferences

**Tasks**:
1. Create selector history storage (SQLite or JSON)
2. Add History dropdown to toolbar
3. Add Settings dialog for defaults (mode, healing options)

**Files to Create**:
- `selectors/selector_history.py`
- `selectors/dialogs/selector_settings_dialog.py`

### Phase 6: Cleanup & Migration (1 day)

**Goal**: Remove legacy code, update integrations

**Tasks**:
1. Delete `selector_dialog.py` (legacy)
2. Update `SelectorInputWidget` to use new dialog
3. Update node widgets to use new dialog
4. Update documentation

**Files to Delete**:
- `selectors/selector_dialog.py`

**Files to Modify**:
- `ui/widgets/selector_input_widget.py`
- `canvas/graph/node_widgets.py`

---

## 7. Technical Specifications

### 7.1 Auto-Validation Debouncing

```python
class SelectorBuilderWidget(QWidget):
    def __init__(self):
        self._validation_timer = QTimer()
        self._validation_timer.setSingleShot(True)
        self._validation_timer.timeout.connect(self._validate)

    def _on_selector_changed(self, selector: str):
        # Debounce: wait 300ms after last change
        self._validation_timer.start(300)

    async def _validate(self):
        result = await self._selector_manager.test_selector(
            self._state.generated_selector,
            self._state.selector_type
        )
        self._update_match_count(result["count"])
```

### 7.2 Floating Picker Toolbar

```python
class PickerToolbar(QWidget):
    """Small floating toolbar shown during picking."""

    def __init__(self):
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setFixedSize(200, 48)
        # Position at top-center of screen
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - 200) // 2,
            50
        )
```

### 7.3 Selector Generation Priority

```python
ATTRIBUTE_PRIORITY = [
    ("id", 100),           # Unique IDs first
    ("data-testid", 95),   # Test IDs
    ("data-*", 90),        # Other data attributes
    ("aria-label", 85),    # Accessibility
    ("name", 80),          # Form elements
    ("class", 70),         # CSS classes
    ("text", 60),          # Text content
    ("xpath", 50),         # Full XPath
]
```

### 7.4 History Storage Schema

```python
@dataclass
class SelectorHistoryEntry:
    selector: str
    selector_type: str
    element_tag: str
    page_url: str
    timestamp: datetime
    healing_context: Dict[str, Any]

# Store in: config/selector_history.json
```

---

## 8. Migration Plan

### 8.1 Backward Compatibility

1. Keep `UnifiedSelectorDialog` temporarily during migration
2. Add feature flag: `use_new_element_picker = True`
3. `SelectorInputWidget` checks flag to choose dialog
4. Node widgets use `SelectorInputWidget`, get new dialog automatically

### 8.2 Rollout Strategy

| Week | Action |
|------|--------|
| 1 | Implement Phase 1-2, internal testing |
| 2 | Implement Phase 3-4, beta users |
| 3 | Implement Phase 5-6, full rollout |
| 4 | Remove legacy code, docs update |

---

## 9. Unresolved Questions

1. **Keyboard Shortcut Conflict**: Ctrl+A for anchor conflicts with Select All. Use Ctrl+Shift+A instead?

2. **UIExplorer Future**: Keep UIExplorer as separate "advanced" mode, or merge entirely into new dialog?

3. **Desktop Tab Priority**: Is desktop selector picking a priority for this release, or defer?

4. **Recording Integration**: Should new dialog support workflow recording, or keep recorder separate?

5. **Cloud Sync**: Should selector history sync across machines (future Orchestrator feature)?

6. **AI Integration**: Add AI-powered selector suggestions (like AA's Generative Recorder)?

7. **Performance**: Current SelectorManager injects JS on every pick. Cache injector per page?

8. **Mobile Support**: Future support for mobile element picking (Appium integration)?

---

## 10. Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Time to pick element | 8-10s | <3s |
| Clicks to confirm selector | 5-7 | 2-3 |
| Selector validation time | Manual | <300ms auto |
| User errors (invalid selector) | ~20% | <5% |
| Anchor adoption | <5% | 30%+ |
| Healing context capture | Always on | User-visible |

---

## 11. References

### Sources Used

- [UiPath About Selectors](https://docs.uipath.com/activities/other/latest/ui-automation/about-selectors)
- [UiPath Selection Helper](https://docs.uipath.com/activities/other/latest/ui-automation/selection-options)
- [UiPath Modern UI Automation](https://docs.uipath.com/activities/other/latest/ui-automation/about-the-ui-automation-next-activities-pack)
- [Power Automate UI Elements](https://learn.microsoft.com/en-us/power-automate/desktop-flows/ui-elements)
- [Power Automate Recording](https://learn.microsoft.com/en-us/power-automate/desktop-flows/recording-flow)
- [Power Automate Inspect UI Element](https://learn.microsoft.com/en-us/power-automate/desktop-flows/inspect-ui-elements)
- [Automation Anywhere Features Overview](https://www.clariontech.com/platform-blog/important-features-of-automation-anywhere-a-complete-overview)
- [Appian RPA Selectors](https://docs.appian.com/suite/help/24.2/rpa-9.11/selectors.html)
- [Kofax RPA Finders](https://docshield.tungstenautomation.com/RPA/en_US/11.0.0_qrvv5i5e1a/help/kap_help/designstudio/c_guardsandfinders.html)

---

## 12. Appendix: File Inventory

### Current Files (to refactor/remove)

```
src/casare_rpa/presentation/canvas/selectors/
    __init__.py
    unified_selector_dialog.py     # REPLACE with element_selector_dialog.py
    selector_dialog.py             # DELETE (legacy)
    element_picker.py              # KEEP (desktop overlay)
    element_tree_widget.py         # KEEP
    selector_strategy.py           # KEEP
    selector_validator.py          # KEEP
    desktop_selector_builder.py    # REFACTOR
    selector_integration.py        # UPDATE

    tabs/
        __init__.py
        base_tab.py                # KEEP (base classes)
        browser_tab.py             # INTEGRATE into new dialog
        desktop_tab.py             # INTEGRATE into new dialog
        ocr_tab.py                 # INTEGRATE into advanced
        image_match_tab.py         # INTEGRATE into advanced

    ui_explorer/
        __init__.py
        ui_explorer_dialog.py      # KEEP as "advanced mode"
        toolbar.py                 # KEEP
        models/
            element_model.py
            selector_model.py
            anchor_model.py
        panels/
            visual_tree_panel.py
            selector_editor_panel.py
            selected_attrs_panel.py
            property_explorer_panel.py
            selector_preview_panel.py
        widgets/
            attribute_row.py
            xml_highlighter.py
            status_bar_widget.py
            anchor_panel.py
```

### New Files (to create)

```
src/casare_rpa/presentation/canvas/selectors/
    element_selector_dialog.py     # NEW main dialog
    selector_history.py            # NEW history storage

    state/
        selector_state.py          # NEW centralized state

    widgets/
        toolbar_widget.py          # NEW toolbar
        element_preview_widget.py  # NEW HTML preview
        selector_builder_widget.py # NEW attribute builder
        anchor_widget.py           # NEW anchor section
        advanced_options_widget.py # NEW advanced panel
        picker_toolbar.py          # NEW floating toolbar

    dialogs/
        selector_settings_dialog.py # NEW settings
```
