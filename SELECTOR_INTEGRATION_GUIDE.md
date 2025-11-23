# Element Selector System - Integration Guide

## Overview
Complete browser element selector tool with UiPath-style UI, smart selector generation, and self-healing capabilities.

## ✅ Completed Components

### 1. Browser Injector (`selector_injector.js`)
- **UiPath-inspired UI**: Purple gradient info panel, orange/green highlights
- **Real-time highlighting**: Elements glow orange on hover
- **Visual feedback**: Green flash on selection, recording badge
- **XPath generation**: Optimized with ID, data-*, ARIA fallbacks
- **Keyboard shortcuts**: 
  - `Esc` - Cancel
  - `Ctrl+R` - Stop recording
- **Recording mode**: Captures click sequences

### 2. Selector Generator (`selector_generator.py`)
- **Priority order**: XPath → Data attrs → ARIA → CSS → Text
- **Scoring system**: 0-100 reliability score
- **Top 5 strategies**: Multiple fallbacks per element
- **Self-healing**: Automatic fallback promotion/demotion
- **XPath optimization**: Removes unnecessary indices
- **Element fingerprinting**: For similarity detection

### 3. Playwright Integration (`selector_manager.py`)
- **Script injection**: Auto-injected via `add_init_script()`
- **Bidirectional communication**: Callbacks via `expose_function`
- **Selector validation**: Real-time testing against page
- **Performance metrics**: Execution time, match count
- **Visual highlighting**: Blue borders for testing
- **Async/await support**: Full async integration

### 4. Selector Dialog (`selector_dialog.py`)
- **Modern UI**: Purple theme, clean layout
- **Strategy list**: Shows all 5 selectors with scores
- **Live editing**: Modify selectors before use
- **Testing**: Validate against current page
- **Highlight button**: Show matches in browser
- **Copy to clipboard**: Quick selector copying
- **Real-time feedback**: Green/yellow/red indicators

### 5. UI Integration (`main_window.py`)
- **Toolbar buttons**: Pick Selector, Record Workflow
- **Menu items**: Tools → Pick Element Selector / Record Workflow
- **Global hotkeys**:
  - `Ctrl+Shift+S` - Pick selector
  - `Ctrl+Shift+R` - Record workflow
- **Browser state aware**: Enabled only when browser running

### 6. Application Integration (`selector_integration.py`)
- **Lifecycle management**: Start/stop selector mode
- **Node property updates**: Auto-fill selector fields
- **Recording capture**: Sequence of actions
- **Event signals**: selector_picked, recording_complete
- **Async coordination**: Handles event loop properly

## 📋 To Complete in app.py

### Required Integrations:

```python
from .gui.selector_integration import SelectorIntegration

class CasareRPAApp:
    def __init__(self):
        # ... existing code ...
        
        # Initialize selector integration
        self.selector_integration = SelectorIntegration(self)
        
        # Connect signals
        self.selector_integration.selector_picked.connect(self._on_selector_picked)
        self.selector_integration.recording_complete.connect(self._on_recording_complete)
        
        # Connect main window actions
        self.main_window.action_pick_selector.triggered.connect(self._start_selector_picking)
        self.main_window.action_record_workflow.triggered.connect(self._toggle_recording)
    
    async def _on_browser_launched(self, page):
        """When browser launches, initialize selector"""
        await self.selector_integration.initialize_for_page(page)
        self.main_window.set_browser_running(True)
    
    def _start_selector_picking(self):
        """Start selector picking mode"""
        if not self.selector_integration._active_page:
            QMessageBox.warning(self.main_window, "No Browser", 
                              "Please launch a browser first")
            return
        
        # Get selected node if applicable
        selected_nodes = self.node_graph.selected_nodes()
        target_node = selected_nodes[0] if selected_nodes else None
        
        asyncio.ensure_future(
            self.selector_integration.start_picking(target_node, "selector")
        )
    
    def _toggle_recording(self, checked: bool):
        """Toggle recording mode"""
        if checked:
            asyncio.ensure_future(self.selector_integration.start_recording())
        else:
            asyncio.ensure_future(self.selector_integration.stop_selector_mode())
    
    def _on_selector_picked(self, selector_value: str, selector_type: str):
        """Handle selector picked"""
        logger.info(f"Selector picked: {selector_value}")
        # Can show in status bar, etc.
    
    def _on_recording_complete(self, actions: list):
        """Handle recording complete - generate workflow"""
        logger.info(f"Recording complete: {len(actions)} actions")
        # TODO: Generate nodes from actions
```

## 🎯 Usage Flow

### Single Element Picking:
1. User clicks **Pick Selector** toolbar button or presses `Ctrl+Shift+S`
2. Browser shows purple overlay with info panel
3. User hovers over elements (orange highlight)
4. User clicks element (green flash)
5. Dialog shows with 5 selector strategies
6. User can test/highlight/edit selectors
7. User clicks "Use This Selector"
8. Selector auto-fills into node property

### Workflow Recording:
1. User clicks **Record Workflow** or presses `Ctrl+Shift+R`
2. Red recording badge appears at top
3. User performs actions (click, type, etc.)
4. Each action captured with element fingerprint
5. User presses `Ctrl+R` to stop
6. App generates node sequence from actions

## 🎨 Visual Design

**Overlay Style**:
- Semi-transparent black backdrop
- Purple gradient info panel (bottom-right)
- Orange highlight with glow (hover)
- Green highlight with glow (selected)
- Red recording badge (top-center)

**Dialog Style**:
- Modern white background
- Purple accents (#667eea)
- Split layout (selectors list | details)
- Color-coded reliability: 🟢 80+ | 🟡 60-79 | 🔴 <60
- Real-time validation feedback

## 🔧 Self-Healing Features

**Selector Ranking**:
- Each element gets 5 strategies
- Scored 0-100 for reliability
- Automatic re-ranking on failure

**Fallback Mechanism**:
- Primary selector fails → try 2nd best
- Successful fallback → promoted to primary
- Failed selector → demoted, score reduced

**Element Fingerprinting**:
- Tag name, position, text, classes
- Similarity score 0.0-1.0
- Fuzzy matching for changed elements

## 📊 Selector Priority

1. **XPath with ID**: `//button[@id='submit']` (Score: ~95)
2. **Data attributes**: `//*[@data-testid='login-btn']` (Score: ~85)
3. **ARIA labels**: `//*[@aria-label='Submit form']` (Score: ~80)
4. **CSS selectors**: `button.submit-btn` (Score: ~70)
5. **Text content**: `//*[contains(text(), 'Submit')]` (Score: ~50)

## 🚀 Next Steps

1. **Add to app.py**: Integrate SelectorIntegration class
2. **Test with browser**: Launch browser, test picking
3. **Recording workflow**: Implement node generation from actions
4. **Context menu**: Add "Pick Selector" to node right-click menu
5. **Status feedback**: Show selector mode status in status bar

## 📝 Notes

- All selectors are XPath-based for consistency
- CSS selectors converted to XPath equivalent
- Injector loads on every page navigation
- Dialog is modal to prevent interference
- All operations are fully async-aware
