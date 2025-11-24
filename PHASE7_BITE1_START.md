# Phase 7 - Bite 1: Foundation & Context

## 🎯 Goal
Set up the desktop automation infrastructure with basic window/element finding capabilities.

---

## 📋 Tasks Checklist

### 1. Install Dependencies
```powershell
pip install uiautomation
pip install psutil  # For process management
```

### 2. Create Project Structure
```
src/casare_rpa/desktop/
├── __init__.py
├── context.py           # DesktopContext - main entry point
├── element.py           # DesktopElement - element wrapper
└── selector.py          # Desktop selector parsing and strategies
```

### 3. Implement Core Classes

#### `context.py` - DesktopContext
**Purpose**: Main interface for desktop automation, manages windows and applications

**Key Methods**:
```python
class DesktopContext:
    def __init__(self):
        """Initialize desktop automation context"""
        
    def find_window(self, title: str, exact: bool = False) -> Window:
        """Find a window by title"""
        
    def get_all_windows(self, include_invisible: bool = False) -> List[Window]:
        """Get all open windows"""
        
    def launch_application(self, path: str, args: str = "", timeout: int = 10) -> Window:
        """Launch an application and return its main window"""
        
    def close_application(self, window_or_pid) -> bool:
        """Close an application"""
```

#### `element.py` - DesktopElement
**Purpose**: Wrapper around uiautomation Control objects with simplified API

**Key Methods**:
```python
class DesktopElement:
    def __init__(self, control: uiautomation.Control):
        """Wrap a UI Automation control"""
        
    def click(self, simulate: bool = False) -> bool:
        """Click the element"""
        
    def type_text(self, text: str, clear_first: bool = False) -> bool:
        """Type text into the element"""
        
    def get_text(self) -> str:
        """Get element text (Name property)"""
        
    def get_property(self, property_name: str) -> Any:
        """Get any element property"""
        
    def find_child(self, selector: dict) -> "DesktopElement":
        """Find child element using selector"""
        
    def find_children(self, selector: dict) -> List["DesktopElement"]:
        """Find all matching child elements"""
```

#### `selector.py` - Selector System
**Purpose**: Parse and apply desktop selectors

**Selector Format**:
```python
{
    "type": "desktop",
    "strategy": "control_type",  # "name", "automation_id", "class_name"
    "value": "Button",
    "properties": {              # Optional additional filters
        "Name": "OK",
        "AutomationId": "btnOK"
    }
}
```

**Key Functions**:
```python
def parse_selector(selector: dict) -> dict:
    """Parse and validate selector"""
    
def find_element(parent_control, selector: dict) -> DesktopElement:
    """Find element using selector"""
    
def find_elements(parent_control, selector: dict) -> List[DesktopElement]:
    """Find all matching elements"""
```

### 4. Write Unit Tests

#### `tests/test_desktop_context.py`
**Test Coverage**:
- ✅ Context initialization
- ✅ Find window by exact title
- ✅ Find window by partial title
- ✅ Launch application (Notepad)
- ✅ Close application
- ✅ Get all windows
- ✅ Error handling (window not found)

#### `tests/test_desktop_element.py`
**Test Coverage**:
- ✅ Element creation
- ✅ Get element text/properties
- ✅ Find child elements
- ✅ Error handling (element not found)

#### `tests/test_desktop_selector.py`
**Test Coverage**:
- ✅ Parse valid selector
- ✅ Validate selector format
- ✅ Invalid selector error handling

**Minimum**: 10+ tests total

### 5. Create Demo Script

#### `demo_desktop_bite1.py`
```python
"""
Demo: Desktop Automation Bite 1
Demonstrates basic window/element finding
"""
from casare_rpa.desktop import DesktopContext

def main():
    print("=== Desktop Automation Bite 1 Demo ===\n")
    
    # Initialize context
    context = DesktopContext()
    
    # Launch Calculator
    print("1. Launching Calculator...")
    calc_window = context.launch_application("calc.exe", timeout=5)
    print(f"   ✓ Calculator launched: {calc_window.title}")
    
    # Find button element
    print("\n2. Finding 'One' button...")
    selector = {
        "strategy": "name",
        "value": "One"
    }
    one_button = calc_window.find_element(selector)
    print(f"   ✓ Found button: {one_button.get_text()}")
    
    # Get button properties
    print("\n3. Reading button properties...")
    control_type = one_button.get_property("ControlType")
    automation_id = one_button.get_property("AutomationId")
    print(f"   ✓ Control Type: {control_type}")
    print(f"   ✓ Automation ID: {automation_id}")
    
    # Click button
    print("\n4. Clicking 'One' button...")
    one_button.click()
    print("   ✓ Button clicked")
    
    # Wait for user
    input("\n5. Press Enter to close Calculator...")
    
    # Close application
    print("   Closing Calculator...")
    context.close_application(calc_window)
    print("   ✓ Calculator closed")
    
    print("\n=== Bite 1 Demo Complete! ===")

if __name__ == "__main__":
    main()
```

---

## 🧪 Testing Instructions

### Run Unit Tests
```powershell
# Run all desktop tests
pytest tests/test_desktop_context.py -v
pytest tests/test_desktop_element.py -v
pytest tests/test_desktop_selector.py -v

# Or all at once
pytest tests/test_desktop*.py -v
```

### Run Demo
```powershell
python demo_desktop_bite1.py
```

**Expected Output**:
- Calculator launches
- Button is found
- Properties are displayed
- Button click works
- Calculator closes cleanly

---

## ✅ Success Criteria

Before moving to Bite 2, verify:

1. **Installation**: ✅ `uiautomation` installed without errors
2. **Structure**: ✅ All files created in correct locations
3. **Context Works**: ✅ Can launch Calculator and find its window
4. **Element Finding**: ✅ Can find elements by name, automation ID, control type
5. **Element Interaction**: ✅ Can click button and read properties
6. **Tests Pass**: ✅ 10+ tests passing
7. **Demo Works**: ✅ Demo script runs without errors
8. **Error Handling**: ✅ Graceful errors when window/element not found

---

## 🐛 Common Issues & Solutions

### Issue 1: `ModuleNotFoundError: No module named 'uiautomation'`
**Solution**: Install with `pip install uiautomation`

### Issue 2: Calculator not found
**Solution**: 
- Windows 10: Use `"Calculator"` as window title
- Windows 11: Use `"Calculator"` as window title
- Or use partial match: `find_window("Calc", exact=False)`

### Issue 3: Element not found
**Solution**: 
- Use UI Automation tools to inspect element (Inspect.exe from Windows SDK)
- Check if element is in different control tree location
- Try different selector strategies (Name, AutomationId, ControlType)

### Issue 4: Permission errors
**Solution**: 
- Run as administrator if automating system apps
- Some apps may have UI Automation disabled

---

## 📚 Reference Materials

### UI Automation Documentation
- [uiautomation GitHub](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)
- [Microsoft UI Automation Overview](https://docs.microsoft.com/en-us/windows/win32/winauto/entry-uiauto-win32)

### Element Inspection Tools
- **Inspect.exe**: Windows SDK tool for inspecting UI elements
- **Accessibility Insights**: Microsoft's accessibility testing tool
- **UI Spy**: Legacy tool for UI Automation inspection

### Common Control Types
- `Button`, `Edit`, `Text`, `Window`, `Pane`
- `ListItem`, `TreeItem`, `TabItem`
- `Menu`, `MenuItem`, `ToolBar`
- `CheckBox`, `RadioButton`, `ComboBox`

---

## 🎓 Learning Resources

### uiautomation Library Basics
```python
import uiautomation as auto

# Find window
window = auto.WindowControl(searchDepth=1, Name="Calculator")

# Find button by name
button = window.ButtonControl(Name="One")

# Click button
button.Click()

# Get properties
print(button.Name)
print(button.AutomationId)
print(button.ControlTypeName)
```

### Control Patterns
- **InvokePattern**: Click buttons
- **ValuePattern**: Get/set text in textboxes
- **SelectionPattern**: Select from lists
- **TogglePattern**: Check/uncheck checkboxes
- **WindowPattern**: Minimize/maximize windows

---

## 🚀 Next Steps

Once Bite 1 is complete and all success criteria are met:

✅ **You're ready for Bite 2: Application Management Nodes!**

Bite 2 will implement:
- LaunchApplicationNode
- CloseApplicationNode
- ActivateWindowNode
- GetWindowListNode

**Tell me when Bite 1 is complete and we'll move forward!**
