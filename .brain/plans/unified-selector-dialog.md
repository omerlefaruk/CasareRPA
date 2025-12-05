# Unified Selector Dialog - UiPath-Style Element Picker

## Overview

Replace current fragmented selector dialogs with a single, powerful **UnifiedSelectorDialog** that integrates ALL selector capabilities:

- Browser element picking (CSS, XPath, ARIA, data-testid)
- Desktop element picking (AutomationId, Name, ControlType, Path)
- OCR text detection (find by visible text)
- Image/template matching (find by screenshot)
- AI fuzzy matching (synonyms, semantic, regex patterns)
- Healing context capture (for runtime resilience)

## Current State

### Files to Replace/Refactor

| File | Status |
|------|--------|
| `selectors/selector_dialog.py` | Replace → new UnifiedSelectorDialog |
| `selectors/element_picker.py` | Keep → integrate into unified |
| `selectors/desktop_selector_builder.py` | Replace → merge into unified |
| `selectors/selector_integration.py` | Refactor → use unified dialog |

### Existing Capabilities to Integrate

1. **Browser Healing Chain** (`infrastructure/browser/healing/`)
   - SelectorHealingChain (4-tier healing)
   - CVHealer (OCR + template matching)
   - AnchorHealer (spatial relationships)
   - HeuristicHealer (fingerprinting)

2. **AI Selector Healer** (`utils/selectors/ai_selector_healer.py`)
   - FuzzyMatcher (Levenshtein, Jaro-Winkler, token set)
   - SemanticMatcher (UI synonyms, optional LLM)
   - RegexPatternMatcher (dynamic ID detection)

3. **Desktop Selector Strategies** (`selectors/selector_strategy.py`)
   - 8 strategies with confidence scoring
   - Uniqueness validation

## New Architecture

### UnifiedSelectorDialog

```
┌──────────────────────────────────────────────────────────────────┐
│  Unified Element Selector                              [_][□][X] │
├──────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ [🌐 Browser] [🖥️ Desktop] [📝 OCR Text] [🖼️ Image Match]    │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌─────────────────────────┐  ┌─────────────────────────────────┐ │
│ │  🎯 Pick Element        │  │  Element Preview               │ │
│ │  [Start Picking]        │  │  ┌─────────────────────────┐   │ │
│ │                         │  │  │ <button>                │   │ │
│ │  ─── OR ───             │  │  │ ID: submit-btn          │   │ │
│ │                         │  │  │ Classes: btn, primary   │   │ │
│ │  📷 Capture Screenshot  │  │  │ Text: "Submit Order"    │   │ │
│ │  [Take Screenshot]      │  │  └─────────────────────────┘   │ │
│ │                         │  │                                 │ │
│ │  📝 Find by Text        │  │  🔍 Healing Context              │ │
│ │  [_______________]      │  │  ☑ Capture fingerprint          │ │
│ │                         │  │  ☑ Capture spatial context      │ │
│ │                         │  │  ☑ Capture CV template          │ │
│ └─────────────────────────┘  └─────────────────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │  Generated Selectors (sorted by reliability)                 │ │
│ │ ┌──────────────────────────────────────────────────────────┐ │ │
│ │ │ 🟢 98 │ XPATH │ //button[@data-testid='submit']     ✓   │ │ │
│ │ │ 🟢 95 │ CSS   │ #submit-btn                         ✓   │ │ │
│ │ │ 🟡 80 │ TEXT  │ //button[contains(text(),'Submit')] ✓   │ │ │
│ │ │ 🟡 75 │ ARIA  │ button[aria-label='Submit Order']        │ │ │
│ │ │ 🔴 60 │ CLASS │ .btn.btn-primary                         │ │ │
│ │ └──────────────────────────────────────────────────────────┘ │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │  Selector Value                                              │ │
│ │  ┌──────────────────────────────────────────────────────┐   │ │
│ │  │ //button[@data-testid='submit']                      │   │ │
│ │  └──────────────────────────────────────────────────────┘   │ │
│ │  [🔍 Test] [✨ Highlight] [📋 Copy]                          │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                  │
│   [Cancel]                              [✓ Use This Selector]   │
└──────────────────────────────────────────────────────────────────┘
```

### Tab Modes

1. **Browser Tab**
   - Pick element from browser (via injector)
   - Generate CSS, XPath, ARIA, data-testid, text selectors
   - Test/highlight in browser
   - Capture healing context (fingerprint + spatial + CV)

2. **Desktop Tab**
   - Pick element from any Windows app
   - Element tree viewer
   - Generate AutomationId, Name, ControlType, Path selectors
   - Capture healing context

3. **OCR Text Tab**
   - Take page screenshot
   - Enter text to find
   - Show OCR matches with confidence
   - Preview match locations
   - Return coordinates or generate selector

4. **Image Match Tab**
   - Take page screenshot
   - Capture element template OR load image file
   - Show template matches with similarity scores
   - Return coordinates or bounding box

### Data Flow

```
User picks element
       │
       ▼
┌─────────────────────┐
│ SmartSelectorGen    │ ◄── Generate multiple selector strategies
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ AI Enhancement      │ ◄── Add fuzzy/semantic alternatives
│ - FuzzyMatcher      │
│ - SemanticMatcher   │
│ - RegexPatternMatch │
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ Validation          │ ◄── Test each selector, check uniqueness
└─────────────────────┘
       │
       ▼
┌─────────────────────┐
│ Healing Context     │ ◄── Capture for runtime resilience
│ - Fingerprint       │
│ - Spatial context   │
│ - CV template       │
└─────────────────────┘
       │
       ▼
Return: {
  selector: "...",
  selector_type: "xpath",
  healing_context: { fingerprint, spatial, cv_template }
}
```

## Implementation Tasks

### Phase 1: Core Dialog (New Files)

1. **Create `UnifiedSelectorDialog`**
   - Location: `presentation/canvas/selectors/unified_selector_dialog.py`
   - Tab-based UI with QTabWidget
   - Common footer (Test, Highlight, Copy, Use)
   - Dark theme styling

2. **Create `BrowserSelectorTab`**
   - Inherits tab base class
   - Integrates with SelectorManager
   - Shows SmartSelectorGenerator output
   - Adds AI-enhanced alternatives

3. **Create `DesktopSelectorTab`**
   - Inherits tab base class
   - Integrates ElementPickerOverlay
   - Shows desktop selector strategies
   - Element tree viewer (optional)

4. **Create `OCRSelectorTab`**
   - Uses CVHealer.find_text_on_page()
   - Text input field
   - Screenshot preview with match highlights
   - Return text match coordinates

5. **Create `ImageMatchTab`**
   - Uses CVHealer.find_template_on_page()
   - Template capture or file load
   - Screenshot preview with match overlay
   - Return template match coordinates

### Phase 2: Integration

6. **Update SelectorController**
   - Use UnifiedSelectorDialog instead of separate dialogs
   - Pass healing context back to nodes

7. **Update ActionManager**
   - Single "Pick Element" action opens UnifiedSelectorDialog
   - Remove separate browser/desktop picker actions

8. **Update MainWindow toolbar**
   - Replace dual picker buttons with single unified button

### Phase 3: Healing Context Storage

9. **Add healing context to node config**
   - Browser nodes store: `healing_context: { fingerprint, spatial, cv }`
   - Desktop nodes store: `healing_context: { ... }`

10. **Wire healing chain to browser node execution**
    - ClickElementNode uses SelectorHealingChain.locate_element()
    - Falls back through tiers automatically

### Phase 4: Testing & Polish

11. **Unit tests for dialog components**
12. **Integration tests for full flow**
13. **Performance optimization (lazy loading)**

## File Changes Summary

### New Files
```
presentation/canvas/selectors/
├── unified_selector_dialog.py     # Main dialog
├── tabs/
│   ├── __init__.py
│   ├── base_tab.py                # Abstract tab base
│   ├── browser_tab.py             # Browser picking
│   ├── desktop_tab.py             # Desktop picking
│   ├── ocr_tab.py                 # OCR text finding
│   └── image_match_tab.py         # Template matching
```

### Modified Files
```
presentation/canvas/
├── controllers/selector_controller.py  # Use unified dialog
├── components/action_manager.py        # Single picker action
├── components/toolbar_builder.py       # Single picker button
├── main_window.py                      # Remove dual actions

nodes/browser_nodes.py                  # Use healing chain
```

### Deleted Files (after migration)
```
selectors/selector_dialog.py            # Replaced by unified
selectors/desktop_selector_builder.py   # Merged into unified
```

## Open Questions

1. **Keyboard shortcut?** Current: Ctrl+Shift+F3 for desktop. Browser?
2. **Persist healing context?** Store in workflow JSON or separate file?
3. **CV dependencies optional?** Graceful degradation if opencv/pytesseract missing?

## Timeline Estimate

- Phase 1: Core Dialog - 2-3 sessions
- Phase 2: Integration - 1 session
- Phase 3: Healing Storage - 1 session
- Phase 4: Testing - 1 session

Total: ~5-6 focused sessions
