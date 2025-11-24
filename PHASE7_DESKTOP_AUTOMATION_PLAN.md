# Phase 7: Windows Desktop Automation - Implementation Plan

**Priority**: HIGH  
**Target**: Q1 2026  
**Status**: 📋 Planning Phase  
**Library**: `uiautomation` (Python UI Automation wrapper)

---

## 🎯 Overview

Phase 7 adds comprehensive Windows desktop automation capabilities to CasareRPA, enabling users to automate:
- Legacy Win32 applications
- Modern UWP/WinUI applications
- Microsoft Office applications (Word, Excel, PowerPoint, Outlook)
- Custom enterprise desktop software
- Any Windows application with UI Automation support

---

## 📚 Technology Stack

### Primary Library: `uiautomation`
- **Why**: Pure Python, lightweight, full UI Automation API coverage
- **Supports**: Win32, WPF, UWP, WinForms, Qt applications
- **Features**: Element inspection, property access, control patterns
- **Installation**: `pip install uiautomation`

### Supporting Libraries:
- **`pywinauto`** (optional): Fallback for Win32-specific scenarios
- **`psutil`**: Process management and application monitoring
- **`Pillow`**: Screenshot and image comparison
- **`opencv-python`**: Image recognition (future enhancement)

---

## 🏗️ Architecture Design

### 1. Desktop Context Manager
```
src/casare_rpa/desktop/
├── __init__.py
├── context.py           # Desktop automation context (similar to browser context)
├── element.py           # Desktop element wrapper
├── selector.py          # Desktop selector system
├── recorder.py          # Desktop action recorder
└── inspector.py         # Element inspector tool
```

### 2. Desktop Nodes
```
src/casare_rpa/nodes/desktop_nodes/
├── __init__.py
├── application_nodes.py    # Launch, close, activate applications
├── window_nodes.py         # Window management (resize, move, maximize)
├── interaction_nodes.py    # Click, type, select, get text
├── mouse_keyboard_nodes.py # Mouse move, keyboard input
└── advanced_nodes.py       # Screenshot, wait, verify elements
```

### 3. Visual Nodes
```
src/casare_rpa/gui/visual_nodes/
└── desktop_visual.py       # Visual node definitions for desktop automation
```

### 4. Desktop Selector System
```
Desktop Selector Format:
{
    "type": "desktop",
    "strategy": "control_type",  # or "name", "automation_id", "class_name", "xpath"
    "value": "Button",
    "window": "Calculator",      # Target window title
    "properties": {              # Optional filters
        "Name": "Equals",
        "AutomationId": "num1Button"
    }
}
```

---

## 📋 Implementation Phases

### **Bite 1: Foundation & Context (Week 1)**
**Goal**: Set up desktop automation infrastructure

#### Tasks:
1. ✅ Create project structure
2. ✅ Install `uiautomation` library
3. ✅ Create `DesktopContext` class
4. ✅ Create `DesktopElement` wrapper
5. ✅ Create basic selector system
6. ✅ Write unit tests for context and element

#### Deliverables:
- `src/casare_rpa/desktop/context.py`
- `src/casare_rpa/desktop/element.py`
- `src/casare_rpa/desktop/selector.py`
- `tests/test_desktop_context.py`
- Demo: Connect to Calculator app

#### Success Criteria:
- Can launch an application
- Can find a window by title
- Can find an element within a window
- All tests passing (10+ tests)

---

### **Bite 2: Application Management Nodes (Week 1-2)**
**Goal**: Create nodes to manage desktop applications

#### Nodes to Implement:
1. **LaunchApplicationNode**
   - Inputs: `application_path`, `arguments`, `working_dir`
   - Outputs: `process_id`, `window_handle`
   - Config: `wait_timeout`, `window_state` (normal/maximized/minimized)

2. **CloseApplicationNode**
   - Inputs: `process_id` or `window_title`
   - Outputs: `success`
   - Config: `force_close`, `wait_timeout`

3. **ActivateWindowNode**
   - Inputs: `window_title` or `window_handle`
   - Outputs: `success`
   - Config: `match_partial`, `wait_timeout`

4. **GetWindowListNode**
   - Inputs: None
   - Outputs: `window_list` (array of window info)
   - Config: `include_invisible`

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/application_nodes.py`
- `src/casare_rpa/gui/visual_nodes/desktop_visual.py` (app management)
- `tests/test_desktop_application_nodes.py`
- Demo: Launch Notepad, type text, save, close

#### Success Criteria:
- Can launch any Windows application
- Can activate/switch between windows
- Can close applications gracefully or forcefully
- All tests passing (15+ tests)

---

### **Bite 3: Basic Element Interaction (Week 2)**
**Goal**: Enable clicking, typing, and basic interactions

#### Nodes to Implement:
1. **FindElementNode**
   - Inputs: `selector`, `window_context`
   - Outputs: `element`
   - Config: `wait_timeout`, `retry_interval`

2. **ClickElementNode** (Desktop)
   - Inputs: `element` or `selector`
   - Outputs: `success`
   - Config: `click_type` (single/double/right), `simulate`

3. **TypeTextNode** (Desktop)
   - Inputs: `element` or `selector`, `text`
   - Outputs: `success`
   - Config: `clear_first`, `send_keys_mode`

4. **GetElementTextNode**
   - Inputs: `element` or `selector`
   - Outputs: `text`
   - Config: `property_name` (Name/Value/Help/LegacyValue)

5. **GetElementPropertyNode**
   - Inputs: `element` or `selector`, `property_name`
   - Outputs: `property_value`
   - Config: Multiple property options

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/interaction_nodes.py`
- Enhanced `desktop_visual.py`
- `tests/test_desktop_interaction_nodes.py`
- Demo: Fill form in Notepad, Calculator operations

#### Success Criteria:
- Can find elements using various strategies
- Can click buttons, links, menu items
- Can type into text boxes
- Can read text and properties from elements
- All tests passing (20+ tests)

---

### **Bite 4: Desktop Selector Builder UI (Week 3)**
**Goal**: Create visual tool for building desktop selectors

#### Components to Implement:
1. **Desktop Inspector Panel**
   - Element tree viewer (similar to browser DevTools)
   - Property inspector
   - Hover to highlight elements
   - Click to select element

2. **Selector Generator**
   - Auto-generate selector from selected element
   - Multiple strategy suggestions (AutomationId, Name, ControlType)
   - Selector validation and testing
   - Copy selector to clipboard

3. **Integration with Node Properties**
   - "Pick Element" button in node properties
   - Opens inspector in modal/docked panel
   - Selected element auto-populates selector field

#### Deliverables:
- `src/casare_rpa/gui/desktop_inspector.py`
- `src/casare_rpa/gui/desktop_selector_dialog.py`
- Enhanced node property editors
- `tests/test_desktop_inspector.py`
- Demo: Visually select Calculator button

#### Success Criteria:
- Can visually inspect any running application
- Can generate reliable selectors
- Selector works consistently across app restarts
- All tests passing (10+ tests)

---

### **Bite 5: Window Management Nodes (Week 3)**
**Goal**: Control window size, position, and state

#### Nodes to Implement:
1. **ResizeWindowNode**
   - Inputs: `window`, `width`, `height`
   - Outputs: `success`

2. **MoveWindowNode**
   - Inputs: `window`, `x`, `y`
   - Outputs: `success`

3. **MaximizeWindowNode**
   - Inputs: `window`
   - Outputs: `success`

4. **MinimizeWindowNode**
   - Inputs: `window`
   - Outputs: `success`

5. **RestoreWindowNode**
   - Inputs: `window`
   - Outputs: `success`

6. **GetWindowPropertiesNode**
   - Inputs: `window`
   - Outputs: `title`, `size`, `position`, `state`

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/window_nodes.py`
- Enhanced `desktop_visual.py`
- `tests/test_desktop_window_nodes.py`
- Demo: Arrange multiple windows on screen

#### Success Criteria:
- Can control any window's size and position
- Can maximize/minimize/restore windows
- Can read window properties
- All tests passing (12+ tests)

---

### **Bite 6: Advanced Interactions (Week 4)**
**Goal**: Support complex UI interactions

#### Nodes to Implement:
1. **SelectFromDropdownNode** (Desktop)
   - Inputs: `element`, `value` or `index`
   - Outputs: `success`

2. **CheckCheckboxNode**
   - Inputs: `element`, `state` (check/uncheck/toggle)
   - Outputs: `success`

3. **SelectRadioButtonNode**
   - Inputs: `element`
   - Outputs: `success`

4. **SelectTabNode**
   - Inputs: `tab_control`, `tab_name` or `index`
   - Outputs: `success`

5. **ExpandTreeItemNode**
   - Inputs: `tree_control`, `path`
   - Outputs: `success`

6. **ScrollElementNode**
   - Inputs: `element`, `direction`, `amount`
   - Outputs: `success`

#### Deliverables:
- Enhanced `interaction_nodes.py`
- `tests/test_desktop_advanced_interaction.py`
- Demo: Interact with File Explorer, Settings app

#### Success Criteria:
- Can interact with all common control types
- Supports Win32, WPF, and UWP controls
- All tests passing (15+ tests)

---

### **Bite 7: Mouse & Keyboard Control (Week 4)**
**Goal**: Low-level input control

#### Nodes to Implement:
1. **MoveMouseNode**
   - Inputs: `x`, `y` or `element`
   - Outputs: `success`
   - Config: `relative`, `smooth_move`

2. **MouseClickNode**
   - Inputs: `x`, `y` or current position
   - Outputs: `success`
   - Config: `button` (left/right/middle), `clicks` (1/2)

3. **SendKeysNode**
   - Inputs: `keys`
   - Outputs: `success`
   - Config: Support for modifiers (Ctrl, Alt, Shift)

4. **SendHotKeyNode**
   - Inputs: `hotkey_combo` (e.g., "Ctrl+C")
   - Outputs: `success`

5. **GetMousePositionNode**
   - Inputs: None
   - Outputs: `x`, `y`

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/mouse_keyboard_nodes.py`
- Enhanced `desktop_visual.py`
- `tests/test_desktop_mouse_keyboard.py`
- Demo: Draw in Paint, use keyboard shortcuts

#### Success Criteria:
- Can control mouse precisely
- Can send any keyboard input
- Can simulate hotkey combinations
- All tests passing (12+ tests)

---

### **Bite 8: Wait & Verification Nodes (Week 5)**
**Goal**: Reliable synchronization and verification

#### Nodes to Implement:
1. **WaitForElementNode** (Desktop)
   - Inputs: `selector`, `timeout`
   - Outputs: `element`, `found`
   - Config: `wait_condition` (exists/visible/enabled/clickable)

2. **WaitForWindowNode**
   - Inputs: `window_title`, `timeout`
   - Outputs: `window`, `found`

3. **VerifyElementExistsNode**
   - Inputs: `selector`
   - Outputs: `exists` (boolean)

4. **VerifyElementPropertyNode**
   - Inputs: `selector`, `property`, `expected_value`
   - Outputs: `matches` (boolean)

5. **WaitForPropertyChangeNode**
   - Inputs: `element`, `property`, `expected_value`, `timeout`
   - Outputs: `success`

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/wait_nodes.py`
- Enhanced `desktop_visual.py`
- `tests/test_desktop_wait_nodes.py`
- Demo: Wait for file dialog, verify save success

#### Success Criteria:
- Workflows don't fail due to timing issues
- Can verify UI state before proceeding
- All tests passing (10+ tests)

---

### **Bite 9: Screenshot & OCR (Week 5)**
**Goal**: Visual verification and data extraction

#### Nodes to Implement:
1. **CaptureScreenshotNode** (Desktop)
   - Inputs: `element` or `window` or `screen_region`
   - Outputs: `image_path`
   - Config: `format` (PNG/JPG), `quality`

2. **CaptureElementImageNode**
   - Inputs: `element`
   - Outputs: `image_path`

3. **OCRExtractTextNode**
   - Inputs: `image_path` or `element`
   - Outputs: `extracted_text`
   - Config: `language`, `confidence_threshold`

4. **CompareImagesNode**
   - Inputs: `image1_path`, `image2_path`
   - Outputs: `similarity_score`, `matches`
   - Config: `threshold`

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/vision_nodes.py`
- Integration with Tesseract OCR (optional)
- Enhanced `desktop_visual.py`
- `tests/test_desktop_vision_nodes.py`
- Demo: Extract text from image, verify UI visually

#### Success Criteria:
- Can capture any region of screen
- OCR works with reasonable accuracy
- Can compare screenshots
- All tests passing (10+ tests)

---

### **Bite 10: Desktop Recorder (Week 6)**
**Goal**: Record desktop actions and generate workflows

#### Components to Implement:
1. **Desktop Action Recorder**
   - Global hotkey to start/stop recording
   - Records mouse clicks, keyboard input, window changes
   - Element identification during recording
   - Action playback preview

2. **Recorder UI**
   - Recording indicator overlay
   - Action list viewer
   - Edit recorded actions
   - Generate workflow from recording

3. **Smart Element Identification**
   - Auto-select best selector strategy
   - Fallback selectors if primary fails
   - Context-aware recording (knows which window)

#### Deliverables:
- `src/casare_rpa/desktop/recorder.py`
- `src/casare_rpa/gui/desktop_recorder_panel.py`
- Enhanced workflow generator
- `tests/test_desktop_recorder.py`
- Demo: Record Notepad workflow, replay

#### Success Criteria:
- Can record complete workflows
- Generated workflow is reliable
- Recorded actions can be edited
- All tests passing (15+ tests)

---

### **Bite 11: Office Automation Nodes (Week 6)**
**Goal**: Specialized nodes for Office applications

#### Nodes to Implement:

**Excel:**
1. **OpenExcelFileNode**
2. **ReadExcelCellNode**
3. **WriteExcelCellNode**
4. **GetExcelRangeNode**
5. **CloseExcelFileNode**

**Word:**
1. **OpenWordDocumentNode**
2. **GetWordTextNode**
3. **ReplaceWordTextNode**
4. **CloseWordDocumentNode**

**Outlook:**
1. **SendEmailNode** (via Outlook)
2. **ReadEmailNode**
3. **GetInboxCountNode**

#### Deliverables:
- `src/casare_rpa/nodes/desktop_nodes/office_nodes.py`
- Enhanced `desktop_visual.py`
- `tests/test_desktop_office_nodes.py`
- Demo: Excel data processing, Word report generation

#### Success Criteria:
- Can automate Excel operations
- Can automate Word documents
- Can work with Outlook (if installed)
- All tests passing (20+ tests)

---

### **Bite 12: Integration & Polish (Week 7)**
**Goal**: Complete integration and comprehensive testing

#### Tasks:
1. **Context Integration**
   - Desktop context in execution context
   - Resource cleanup (close apps after workflow)
   - Error handling improvements

2. **Node Registry Integration**
   - Register all desktop nodes
   - New "Desktop Automation" category
   - Icon design for desktop nodes

3. **Templates & Demos**
   - Desktop automation templates
   - Demo workflows for common scenarios
   - Video tutorials (optional)

4. **Comprehensive Testing**
   - Integration tests with real applications
   - Performance testing
   - Memory leak testing
   - Edge case handling

#### Deliverables:
- Complete desktop automation suite
- 12+ workflow templates
- Comprehensive test suite (100+ tests)
- Documentation
- Demo videos

#### Success Criteria:
- All nodes work reliably
- No memory leaks
- Handles errors gracefully
- Complete documentation
- All tests passing (100+ tests)

---

## 🧪 Testing Strategy

### Unit Tests (Per Bite)
- Node initialization
- Input/output validation
- Configuration validation
- Serialization/deserialization

### Integration Tests
- **Notepad Automation**: Launch, type, save, close
- **Calculator Automation**: Perform calculations
- **File Explorer**: Navigate folders, select files
- **Settings App**: Navigate, change settings
- **Paint**: Draw shapes, save image
- **Office Apps** (if available): Excel, Word operations

### Workflow Tests
- Complete automation scenarios
- Error recovery
- Element not found handling
- Window closed handling
- Multi-window scenarios

### Performance Tests
- Large-scale workflows (100+ nodes)
- Memory usage monitoring
- Element finding speed
- Screenshot performance

---

## 📚 Documentation Structure

### User Documentation
1. **Desktop Automation Guide**
   - Introduction to desktop automation
   - Supported applications
   - Selector strategies explained

2. **Node Reference**
   - Each node documented with examples
   - Common use cases
   - Troubleshooting tips

3. **Selector Guide**
   - Desktop selector format
   - Best practices
   - Selector strategies comparison

4. **Cookbook**
   - Common automation recipes
   - Office automation examples
   - Legacy app automation

### Developer Documentation
1. **Architecture Overview**
2. **Desktop Context API**
3. **Element Wrapper API**
4. **Custom Node Creation**

---

## 🚀 Getting Started

### Bite 1 Start: Foundation
**What to do first:**
1. Install `uiautomation`: `pip install uiautomation`
2. Create desktop context structure
3. Implement basic window/element finding
4. Write initial tests

**Expected Output:**
```python
from casare_rpa.desktop import DesktopContext

# Example usage
context = DesktopContext()
calc = context.find_window("Calculator")
button = calc.find_element("Button", Name="One")
button.click()
```

**Tell me when ready to proceed to Bite 2!**

---

## 📊 Success Metrics

### Phase 7 Complete When:
- ✅ 100+ tests passing
- ✅ 50+ desktop nodes implemented
- ✅ Desktop recorder working
- ✅ Office automation support
- ✅ Selector builder UI complete
- ✅ 12+ workflow templates
- ✅ Complete documentation
- ✅ Can automate any Windows application

---

## 🎯 Next Steps

1. **Review this plan** - Does it meet your requirements?
2. **Start Bite 1** - Foundation & Context setup
3. **After each bite** - Test, verify, get feedback
4. **Iterate** - Adjust plan based on learnings

---

**Ready to start? Let me know and I'll begin with Bite 1!**
