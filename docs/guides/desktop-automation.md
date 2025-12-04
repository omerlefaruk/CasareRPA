# Desktop Automation Guide

Automate Windows desktop applications.

## Overview

CasareRPA uses UIAutomation and Win32 APIs for desktop automation.

## Key Nodes

### Application Control

| Node | Purpose |
|------|---------|
| LaunchApplicationNode | Start an application |
| CloseApplicationNode | Close an application |
| AttachToWindowNode | Connect to existing window |

### Element Interaction

| Node | Purpose |
|------|---------|
| FindElementNode | Find UI element |
| ClickDesktopElementNode | Click element |
| TypeDesktopTextNode | Type text |
| GetDesktopTextNode | Extract text |

### Window Operations

| Node | Purpose |
|------|---------|
| FocusWindowNode | Bring window to front |
| MinimizeWindowNode | Minimize window |
| MaximizeWindowNode | Maximize window |

## Finding Elements

Use the Desktop Selector tool (F12) to:

1. Hover over target element
2. Press Ctrl+Click to capture
3. Copy selector to node

### Selector Types

| Type | Example | Best For |
|------|---------|----------|
| AutomationId | #buttonSubmit | Unique IDs |
| Name | [name="OK"] | Button text |
| ControlType | [type="Button"] | Generic controls |

## Best Practices

1. **Use AutomationId** when available
2. **Wait for windows** to load
3. **Handle UAC** prompts
4. **Test on clean system**

## Example Workflow

```
Start → LaunchApp → WaitForWindow → FindElement → Click → TypeText → End
```

## Related Nodes

- [Desktop Nodes](../nodes/desktop_nodes/index.md)
