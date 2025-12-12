# System Nodes

System nodes provide user interaction dialogs, clipboard operations, command execution, environment management, and system information gathering.

## Overview

| Category | Nodes | Purpose |
|----------|-------|---------|
| Dialogs | 7 | User interaction and input |
| Clipboard | 2 | Copy/paste operations |
| Commands | 3 | Process and command execution |
| Environment | 2 | Environment variables |
| System Info | 3 | Hardware and OS information |

---

## Dialog Nodes

### MessageBoxNode

Display a message box with customizable buttons.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Message" | Dialog title |
| message | STRING | "" | Message text to display |
| icon | CHOICE | "information" | information/warning/error/question |
| buttons | CHOICE | "ok" | ok/ok_cancel/yes_no/yes_no_cancel |
| timeout | INTEGER | 0 | Auto-close timeout (0 = never) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | message | STRING | Message text |
| Output | button_clicked | STRING | Which button was clicked |
| Output | result | BOOLEAN | True for OK/Yes, False for Cancel/No |

**Example:**

```python
# Confirmation dialog
workflow.add_node(
    "MessageBoxNode",
    config={
        "title": "Confirm Action",
        "message": "Are you sure you want to proceed?",
        "icon": "question",
        "buttons": "yes_no",
    }
)
```

---

### InputDialogNode

Prompt the user for text input.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Input" | Dialog title |
| prompt | STRING | "" | Prompt text |
| default_value | STRING | "" | Pre-filled value |
| input_type | CHOICE | "text" | text/password/number |
| required | BOOLEAN | True | Input cannot be empty |
| min_length | INTEGER | 0 | Minimum input length |
| max_length | INTEGER | 0 | Maximum length (0 = unlimited) |
| placeholder | STRING | "" | Placeholder text |
| variable_name | STRING | "" | Store result in variable |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | default_value | STRING | Pre-filled value |
| Output | value | STRING | User input |
| Output | confirmed | BOOLEAN | True if user clicked OK |
| Output | cancelled | BOOLEAN | True if user cancelled |

**Example:**

```python
# Get username
workflow.add_node(
    "InputDialogNode",
    config={
        "title": "Login",
        "prompt": "Enter your username:",
        "required": True,
        "variable_name": "username",
    }
)
```

---

### FilePickerNode

Open file selection dialog.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Select File" | Dialog title |
| mode | CHOICE | "open" | open/save/open_multiple |
| filter | STRING | "" | File filter (e.g., "*.txt;*.csv") |
| filter_name | STRING | "All Files" | Filter display name |
| default_dir | STRING | "" | Starting directory |
| default_filename | STRING | "" | Pre-filled filename (save mode) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | file_path | STRING | Selected file path |
| Output | file_paths | LIST | Selected paths (multiple mode) |
| Output | confirmed | BOOLEAN | Selection was made |
| Output | filename | STRING | Just the filename |
| Output | directory | STRING | Parent directory |

**Example:**

```python
# Select CSV files
workflow.add_node(
    "FilePickerNode",
    config={
        "title": "Select Data File",
        "mode": "open",
        "filter": "*.csv;*.xlsx",
        "filter_name": "Data Files",
    }
)
```

---

### FolderPickerNode

Open folder selection dialog.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Select Folder" | Dialog title |
| default_dir | STRING | "" | Starting directory |
| show_hidden | BOOLEAN | False | Show hidden folders |
| create_new | BOOLEAN | True | Allow creating new folders |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | folder_path | STRING | Selected folder path |
| Output | confirmed | BOOLEAN | Selection was made |
| Output | folder_name | STRING | Just the folder name |

---

### NotificationNode

Display a system notification (toast).

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Notification" | Notification title |
| message | STRING | "" | Notification body |
| icon | CHOICE | "info" | info/success/warning/error |
| duration | INTEGER | 5000 | Display time (ms) |
| position | CHOICE | "bottom_right" | Position on screen |
| sound | BOOLEAN | True | Play notification sound |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | message | STRING | Notification text |
| Output | success | BOOLEAN | Notification shown |

> **Note:** Notifications are non-blocking - workflow continues immediately.

---

### ProgressDialogNode

Display a progress indicator during long operations.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Progress" | Dialog title |
| message | STRING | "" | Progress message |
| total | INTEGER | 100 | Total progress steps |
| show_cancel | BOOLEAN | True | Show cancel button |
| show_percentage | BOOLEAN | True | Display percentage |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | progress | INTEGER | Current progress value |
| Input | message | STRING | Updated status message |
| Output | cancelled | BOOLEAN | User cancelled |
| Output | completed | BOOLEAN | Progress reached 100% |

**Example:**

```python
# Use with a loop
progress = workflow.add_node(
    "ProgressDialogNode",
    config={
        "title": "Processing Files",
        "total": 100,
    }
)

# Inside loop, update progress
progress.set_input("progress", current_index)
progress.set_input("message", f"Processing file {current_index}...")
```

---

### FormDialogNode

Display a custom form with multiple fields.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Form" | Dialog title |
| fields | JSON | [] | Field definitions |
| submit_text | STRING | "Submit" | Submit button text |
| cancel_text | STRING | "Cancel" | Cancel button text |
| width | INTEGER | 400 | Dialog width |

**Field Definition:**

```json
[
  {
    "name": "username",
    "type": "text",
    "label": "Username",
    "required": true,
    "placeholder": "Enter username"
  },
  {
    "name": "password",
    "type": "password",
    "label": "Password",
    "required": true
  },
  {
    "name": "role",
    "type": "dropdown",
    "label": "Role",
    "options": ["Admin", "User", "Guest"]
  },
  {
    "name": "remember",
    "type": "checkbox",
    "label": "Remember me",
    "default": true
  }
]
```

**Supported Field Types:**
- `text` - Single line text
- `password` - Masked text
- `number` - Numeric input
- `dropdown` - Select from options
- `checkbox` - Boolean toggle
- `textarea` - Multi-line text
- `date` - Date picker
- `file` - File selection

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | values | DICT | All field values |
| Output | confirmed | BOOLEAN | Form was submitted |

---

### PreviewDialogNode

Display data preview (image, text, or table).

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Preview" | Dialog title |
| mode | CHOICE | "auto" | auto/image/text/table/json |
| width | INTEGER | 600 | Dialog width |
| height | INTEGER | 400 | Dialog height |
| editable | BOOLEAN | False | Allow editing |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | data | ANY | Data to preview |
| Input | file_path | STRING | File to preview |
| Output | edited_data | ANY | Edited data (if editable) |
| Output | closed | BOOLEAN | Dialog was closed |

---

## Clipboard Nodes

### GetClipboardNode

Read content from the system clipboard.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| format | CHOICE | "auto" | auto/text/html/image/files |
| variable_name | STRING | "" | Store result in variable |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | content | ANY | Clipboard content |
| Output | format | STRING | Detected format |
| Output | has_content | BOOLEAN | Clipboard not empty |
| Output | text | STRING | Text if available |

---

### SetClipboardNode

Write content to the system clipboard.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| format | CHOICE | "text" | text/html/image |
| clear_first | BOOLEAN | True | Clear clipboard first |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | content | ANY | Content to copy |
| Output | success | BOOLEAN | Copy succeeded |

**Example:**

```python
# Copy text to clipboard
workflow.add_node(
    "SetClipboardNode",
    config={"format": "text"}
)
node.set_input("content", "Text to copy")
```

---

## Command Execution

### RunCommandNode

Execute a shell command or program.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| command | STRING | "" | Command to execute |
| shell | BOOLEAN | True | Run in shell |
| working_dir | STRING | "" | Working directory |
| timeout | INTEGER | 60 | Timeout (seconds) |
| capture_output | BOOLEAN | True | Capture stdout/stderr |
| environment | JSON | {} | Additional env vars |
| encoding | STRING | "utf-8" | Output encoding |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | command | STRING | Command to run |
| Input | args | LIST | Command arguments |
| Output | stdout | STRING | Standard output |
| Output | stderr | STRING | Standard error |
| Output | return_code | INTEGER | Exit code |
| Output | success | BOOLEAN | Exit code == 0 |

**Example:**

```python
# Run Python script
workflow.add_node(
    "RunCommandNode",
    config={
        "command": "python process_data.py",
        "working_dir": "C:\\scripts",
        "timeout": 300,
    }
)

# Run with captured output
workflow.add_node(
    "RunCommandNode",
    config={
        "command": "dir /b",
        "shell": True,
    }
)
```

---

### GetEnvironmentVarNode

Get the value of an environment variable.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| var_name | STRING | "" | Variable name |
| default_value | STRING | "" | Value if not found |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | var_name | STRING | Variable name |
| Output | value | STRING | Variable value |
| Output | exists | BOOLEAN | Variable exists |

---

### SetEnvironmentVarNode

Set an environment variable.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| var_name | STRING | "" | Variable name |
| value | STRING | "" | Value to set |
| scope | CHOICE | "process" | process/user/system |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | var_name | STRING | Variable name |
| Input | value | STRING | Value to set |
| Output | success | BOOLEAN | Operation succeeded |

> **Warning:** Setting `user` or `system` scope requires appropriate permissions.

---

### EnvironmentVariableNode

Combined get/set environment variable node.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| action | CHOICE | "get" | get/set |
| var_name | STRING | "" | Variable name |
| value | STRING | "" | Value (for set) |
| scope | CHOICE | "process" | process/user/system |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | var_name | STRING | Variable name |
| Input | value | STRING | Value to set |
| Output | result_value | STRING | Variable value |
| Output | exists | BOOLEAN | Variable exists |
| Output | success | BOOLEAN | Operation succeeded |

---

## System Information

### SystemInfoNode

Get comprehensive system information.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| info_type | CHOICE | "all" | os/cpu/ram/disk/network/all |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | info | DICT | All requested info |
| Output | os_name | STRING | OS name and version |
| Output | cpu_percent | FLOAT | Current CPU usage |
| Output | ram_percent | FLOAT | Current RAM usage |
| Output | disk_percent | FLOAT | Primary disk usage |

**Output Structure:**

```json
{
  "os": {
    "system": "Windows",
    "release": "10",
    "version": "10.0.19041",
    "machine": "AMD64",
    "processor": "Intel64 Family 6...",
    "hostname": "DESKTOP-123",
    "python_version": "3.12.0"
  },
  "cpu": {
    "percent": 45.2,
    "cores_physical": 4,
    "cores_logical": 8,
    "frequency_mhz": 3600
  },
  "ram": {
    "total_gb": 16.0,
    "available_gb": 8.5,
    "used_gb": 7.5,
    "percent": 46.9
  },
  "disk": [
    {
      "device": "C:\\",
      "mountpoint": "C:\\",
      "fstype": "NTFS",
      "total_gb": 500.0,
      "used_gb": 250.0,
      "free_gb": 250.0,
      "percent": 50.0
    }
  ],
  "network": {
    "bytes_sent": 1234567890,
    "bytes_recv": 9876543210,
    "interfaces": [...]
  }
}
```

---

### ProcessListNode

List running processes.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| filter_name | STRING | "" | Filter by name |
| include_details | BOOLEAN | True | Include CPU/memory |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | filter_name | STRING | Name filter |
| Output | processes | LIST | Process list |
| Output | count | INTEGER | Process count |

**Process Info:**

```json
{
  "pid": 1234,
  "name": "notepad.exe",
  "status": "running",
  "cpu_percent": 0.5,
  "memory_mb": 25.5,
  "username": "user",
  "create_time": 1699000000.0
}
```

---

### ProcessKillNode

Terminate a process by PID or name.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| pid_or_name | STRING | "" | Process ID or name |
| force | BOOLEAN | False | Force kill (SIGKILL) |
| timeout | INTEGER | 5 | Graceful termination timeout |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | pid_or_name | STRING | Process to kill |
| Output | killed_count | INTEGER | Processes killed |
| Output | success | BOOLEAN | At least one killed |

---

### VolumeControlNode

Get or set system audio volume.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| action | CHOICE | "get" | get/set/mute/unmute |
| level | INTEGER | 50 | Volume level (0-100) |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | level | INTEGER | Volume level |
| Output | volume | INTEGER | Current volume |
| Output | muted | BOOLEAN | Mute state |
| Output | success | BOOLEAN | Operation succeeded |

> **Note:** Requires `pycaw` package for volume control.

---

### ScreenRegionPickerNode

Let user select a screen region with mouse.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| title | STRING | "Select Screen Region" | Picker title |
| show_coordinates | BOOLEAN | True | Show real-time coordinates |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | x | INTEGER | Region X |
| Output | y | INTEGER | Region Y |
| Output | width | INTEGER | Region width |
| Output | height | INTEGER | Region height |
| Output | confirmed | BOOLEAN | Selection made |

---

## Sleep and Timing

### SleepNode

Pause workflow execution for a specified duration.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| duration | FLOAT | 1.0 | Sleep time (seconds) |
| random_extra | FLOAT | 0.0 | Random additional time |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Input | duration | FLOAT | Sleep duration |
| Output | actual_duration | FLOAT | Actual time slept |

---

### GetCurrentTimeNode

Get current date and time.

**Properties:**

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| format | STRING | "%Y-%m-%d %H:%M:%S" | Output format |
| timezone | STRING | "local" | Timezone |

**Ports:**

| Direction | Port | Type | Description |
|-----------|------|------|-------------|
| Output | datetime | STRING | Formatted datetime |
| Output | timestamp | FLOAT | Unix timestamp |
| Output | year, month, day | INTEGER | Date components |
| Output | hour, minute, second | INTEGER | Time components |

---

## Complete Example

```python
# Interactive data processing workflow

# 1. Show welcome and get user input
msg = workflow.add_node(
    "MessageBoxNode",
    config={
        "title": "Data Processor",
        "message": "This will process your data files. Continue?",
        "buttons": "yes_no",
    }
)

# 2. Select input file
file_picker = workflow.add_node(
    "FilePickerNode",
    config={
        "title": "Select Data File",
        "filter": "*.csv;*.xlsx",
    }
)

# 3. Show progress during processing
progress = workflow.add_node(
    "ProgressDialogNode",
    config={
        "title": "Processing",
        "message": "Processing data...",
    }
)

# 4. Display completion notification
notify = workflow.add_node(
    "NotificationNode",
    config={
        "title": "Complete",
        "message": "Data processing finished!",
        "icon": "success",
    }
)

# 5. Copy result to clipboard
clipboard = workflow.add_node("SetClipboardNode")
clipboard.set_input("content", "Processing completed successfully")

# Connect flow
workflow.connect(msg, file_picker)
workflow.connect(file_picker, progress)
workflow.connect(progress, notify)
workflow.connect(notify, clipboard)
```

---

## Error Handling

System operations can fail due to permissions, user cancellation, or system state:

1. **User cancellation** - Check `confirmed`/`cancelled` outputs
2. **Permission errors** - System scope env vars require admin
3. **Missing dependencies** - Volume control needs `pycaw`
4. **Process access** - Some processes can't be killed

---

## Related Documentation

- [Desktop Automation](desktop.md) - Windows app automation
- [Variable Nodes](variables.md) - Data management
- [Scripts](scripts.md) - Script execution
- [Control Flow](control-flow.md) - Workflow logic
