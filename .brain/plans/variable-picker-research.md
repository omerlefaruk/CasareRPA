# Variable Picker/Insertion Feature Research

**Research Date**: 2025-12-05
**Purpose**: Inform CasareRPA variable picker implementation for node parameters

---

## Executive Summary

Three dominant patterns exist for variable insertion in RPA/IDE tools:
1. **Button-triggered popup** (Power Automate) - Lightning bolt / fx button opens panel
2. **Keyboard-triggered autocomplete** (UiPath, VS Code) - Ctrl+Space or trigger chars
3. **Hybrid approach** - Both button and keyboard triggers supported

**Recommendation for CasareRPA**: Hybrid approach combining Ctrl+Space autocomplete with optional button trigger.

---

## 1. Power Automate's Approach

### Trigger Mechanisms
| Trigger | Description |
|---------|-------------|
| **Lightning bolt button** | Opens dynamic content panel for variables |
| **fx button** | Opens expression editor for functions |
| **Forward slash (/)** | Keyboard shortcut to invoke popup when in action field |
| **@ symbol** | Prefix required for expressions in trigger conditions |

### UI Layout
- **Two-tab design**: "Dynamic content" tab + "Function" tab
- **Search box**: Filters variables and functions across both views
- **Multi-line expression editor**: Gripper allows expansion by 1-2 lines
- **Full-page view**: Available when gripper expansion insufficient
- **Position**: Popup appears adjacent to input field in configuration pane

### Variable Format
```
Cloud flows:     @{expression}           e.g., @{variables('myVar')}
Desktop flows:   ${expression}           e.g., ${variableName}
Inline strings:  @{function('param')}    e.g., "Hello @{variables('name')}"
```

### Enhanced Features (March 2024)
- Variable picker with filtering and sorting
- Type indicators for variables
- Inline selector editing for UI automation actions

### Sources
- [Power Fx in desktop flows](https://learn.microsoft.com/en-us/power-automate/desktop-flows/power-fx)
- [Explore the cloud flows designer](https://learn.microsoft.com/en-us/power-automate/flows-designer)
- [March 2024 update](https://www.microsoft.com/en-us/power-platform/blog/power-automate/march-2024-update-of-power-automate-for-desktop/)

---

## 2. UiPath's Approach

### Trigger Mechanisms
| Trigger | Action |
|---------|--------|
| **Ctrl+K** | Create new variable from current context |
| **Ctrl+Space** | Open IntelliPrompt autocomplete |
| **Ctrl+Shift+E** | Open Expression Editor |
| **Ctrl+M** | Create In argument of required type |
| **Tune icon** | Visual indicator for expression-capable fields |
| **Right-click menu** | "Create Variable" context option |
| **Plus (+) menu** | "Create Variable" option on field right side |

### IntelliPrompt Controls (while open)
- **Ctrl+1**: Toggle Methods
- **Ctrl+2**: Toggle Properties
- **Ctrl+3**: Toggle Classes
- **Ctrl+4**: Toggle Namespaces
- **Ctrl+5**: Toggle Constants
- **Ctrl+6**: Toggle Keywords

### Variable Format
```
VB.NET style:      variableName              (direct reference)
String.Format:     String.Format("{0} {1}", var1, var2)
C# interpolation:  $"Hello {variableName}"  (C# projects only)
```

### UI Patterns
- **Tune selector icon**: Switches between text/variables/expressions modes
- **Variable selection panel**: Dropdown for existing variables/arguments
- **Expression Editor**: Full editor with autocomplete, validation, test button
- **Error icon**: Shows type incompatibility between expression and property

### Sources
- [UiPath Managing Variables](https://docs.uipath.com/studio/docs/managing-variables)
- [UiPath Keyboard Shortcuts](https://docs.uipath.com/studio/standalone/2023.4/user-guide/keyboard-shortcuts)
- [UiPath Expression Editor](https://docs.uipath.com/apps/automation-suite/2023.10/user-guide/the-expression-editor)

---

## 3. VS Code IntelliSense Pattern (Industry Standard)

### Trigger Mechanisms
| Trigger | Behavior |
|---------|----------|
| **Ctrl+Space** | Manual trigger for suggestion list |
| **Trigger characters** | Automatic (e.g., `.` in JavaScript) |
| **Typing** | Quick suggestions appear as you type |

### UI Behavior
- **Position**: Dropdown appears below cursor/caret position
- **Filtering**: CamelCase filtering (e.g., "cra" matches "createApplication")
- **Documentation**: Quick info expands to the side
- **Dismiss**: Ctrl+Space again or close icon

### Keyboard Navigation
| Key | Action |
|-----|--------|
| **Up/Down** | Navigate suggestion list |
| **Tab** | Insert selected item (cycles if Tab completion enabled) |
| **Enter** | Insert selected item |
| **Escape** | Dismiss suggestions |

### Icon Types
- Methods/Functions/Constructors
- Variables/Fields/Properties
- Classes/Interfaces/Structs
- Keywords/Snippets
- Simple word completions ("abc" icon)

### Source
- [VS Code IntelliSense](https://code.visualstudio.com/docs/editing/intellisense)

---

## 4. Best Practices Summary

### Triggering
| Pattern | When to Use |
|---------|-------------|
| **Ctrl+Space** | Standard, expected by developers |
| **Trigger char (e.g., `$`, `%`, `{{`)** | Quick access for frequent use |
| **Button/Icon** | Discoverability for new users |
| **Forward slash (/)** | Quick command pattern (Power Automate style) |

### Dropdown Design
- **Max items**: 8-10 visible (avoid choice paralysis)
- **Position**: Below input field, left-aligned with caret
- **Width**: Match or slightly exceed input field width
- **Spacing**: Adequate tap targets for touch (44px minimum)
- **Font**: Title case for readability

### Filtering & Search
- **Instant filtering**: As user types
- **CamelCase support**: "cWD" matches "currentWorkingDir"
- **Fuzzy matching**: Optional but helpful
- **Type indicators**: Icons or badges for variable types

### Keyboard Accessibility
| Key | Standard Behavior |
|-----|-------------------|
| **Up/Down** | Navigate list |
| **Enter** | Select item |
| **Tab** | Select item (alternative) |
| **Escape** | Close dropdown |
| **Ctrl+Space** | Toggle/reopen |

### ARIA Accessibility
- `aria-expanded`: Toggle on dropdown open/close
- `aria-controls`: Link input to dropdown
- `aria-activedescendant`: Track selected item
- Screen reader announcements for selections

### Performance
- **Response time**: < 100ms feels instant
- **Debounce**: 150-300ms for search input
- **Lazy loading**: For large variable lists

### Sources
- [Baymard Autocomplete Design](https://baymard.com/blog/autocomplete-design)
- [Smart Interface Design Patterns](https://smart-interface-design-patterns.com/articles/autocomplete-ux/)
- [UX Patterns for Developers](https://uxpatterns.dev/patterns/forms/autocomplete)

---

## 5. Recommended Implementation for CasareRPA

### Trigger Strategy (Hybrid)
```
Primary:    Ctrl+Space      -> Opens variable dropdown
Secondary:  ${              -> Triggers inline autocomplete (typing)
Tertiary:   Button icon     -> Opens dropdown (discoverability)
```

### Variable Syntax Options
| Option | Example | Pros | Cons |
|--------|---------|------|------|
| `${varName}` | `${user_input}` | Python f-string familiar | Dollar sign common in shell |
| `%{varName}` | `%{user_input}` | Less collision with shell | Unfamiliar |
| `{{varName}}` | `{{user_input}}` | Template engine familiar | Double chars to type |
| `@{varName}` | `@{user_input}` | Power Automate style | Unfamiliar to Python devs |

**Recommendation**: `${varName}` - familiar to Python developers, matches Power Automate Desktop

### Dropdown Content
1. **Variables section**: User-defined workflow variables
2. **Output ports section**: Data from previous nodes (grouped by node)
3. **System variables**: Built-in values (e.g., `$currentDate`, `$workflowName`)
4. **Recent/Suggested**: Most recently used variables

### Dropdown Structure
```
+------------------------------------------+
| [Search variables...]                     |
+------------------------------------------+
| VARIABLES                                 |
|   $ counter         Integer              |
|   $ file_path       String               |
|   $ items           List                 |
+------------------------------------------+
| FROM: Read CSV Node                       |
|   $ row_data        Dict                 |
|   $ row_count       Integer              |
+------------------------------------------+
| SYSTEM                                    |
|   $ currentDate     DateTime             |
|   $ workflowId      String               |
+------------------------------------------+
```

### Visual Design
- **Type badges**: Color-coded icons (String=green, Integer=blue, List=purple)
- **Source grouping**: Collapsible sections by node
- **Search highlight**: Matched characters in bold
- **Empty state**: "No variables defined yet"

### Implementation Checklist
- [ ] Ctrl+Space triggers dropdown at caret position
- [ ] `${` triggers inline autocomplete
- [ ] Arrow keys navigate, Enter selects
- [ ] Escape closes dropdown
- [ ] Typing filters list instantly
- [ ] Type icons distinguish variable types
- [ ] Recent variables shown at top
- [ ] Variable button in input field for discoverability
- [ ] ARIA attributes for accessibility

---

## 6. Technical Implementation Notes

### Qt/PySide6 Components
- `QLineEdit` with custom event filter for Ctrl+Space
- `QCompleter` for autocomplete (or custom `QListWidget` popup)
- `QMenu` or `QWidget` for positioned dropdown
- Signal/slot for selection events

### Positioning Logic
```python
def show_dropdown(input_widget):
    cursor_rect = input_widget.cursorRect()
    global_pos = input_widget.mapToGlobal(cursor_rect.bottomLeft())
    dropdown.move(global_pos)
    dropdown.show()
```

### Variable Detection in Text
```python
import re
# Pattern to find ${variable} references
VAR_PATTERN = re.compile(r'\$\{([^}]+)\}')

def extract_variables(text):
    return VAR_PATTERN.findall(text)
```

---

## Questions for Implementation

1. **Scope visibility**: Should variables from all scopes be shown, or only current + parent?
2. **Type coercion**: How to handle type mismatches when inserting?
3. **Nested access**: Support for `${data.field}` or `${list[0]}`?
4. **Expression support**: Full expressions like `${counter + 1}` or variables only?
5. **Preview**: Show current variable value on hover?
