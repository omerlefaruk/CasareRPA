# Property Types Reference

Property types define the configuration widgets displayed in the node property panel. Each type renders a specific UI widget optimized for its data entry requirements.

---

## Overview

Property types are defined in `casare_rpa.domain.schemas.property_types.PropertyType`:

```python
from casare_rpa.domain.schemas import PropertyType, PropertyDef
```

---

## Basic Types

### STRING

Single-line text input.

| Property | Value |
|----------|-------|
| Widget | Text input field |
| Python Type | `str` |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `placeholder` | str | Placeholder text |
| `pattern` | str | Regex validation pattern |
| `min_length` | int | Minimum character count |
| `max_length` | int | Maximum character count |

**Example:**

```python
PropertyDef(
    "url",
    PropertyType.STRING,
    default="https://",
    placeholder="Enter URL",
    pattern=r"^https?://",
    label="Target URL",
    tooltip="URL to navigate to"
)
```

### TEXT

Multi-line text area.

| Property | Value |
|----------|-------|
| Widget | Multi-line textarea |
| Python Type | `str` |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `placeholder` | str | Placeholder text |
| `rows` | int | Number of visible rows (default: 3) |

**Example:**

```python
PropertyDef(
    "script",
    PropertyType.TEXT,
    default="",
    rows=10,
    label="Python Script",
    tooltip="Python code to execute"
)
```

### INTEGER

Numeric spin box for whole numbers.

| Property | Value |
|----------|-------|
| Widget | Spin box |
| Python Type | `int` |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `min_value` | int | Minimum allowed value |
| `max_value` | int | Maximum allowed value |
| `step` | int | Increment step (default: 1) |

**Example:**

```python
PropertyDef(
    "timeout",
    PropertyType.INTEGER,
    default=30000,
    min_value=1000,
    max_value=120000,
    step=1000,
    label="Timeout (ms)",
    tooltip="Maximum wait time in milliseconds"
)
```

### FLOAT

Numeric spin box for decimal numbers.

| Property | Value |
|----------|-------|
| Widget | Double spin box |
| Python Type | `float` |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `min_value` | float | Minimum allowed value |
| `max_value` | float | Maximum allowed value |
| `decimals` | int | Decimal places (default: 2) |
| `step` | float | Increment step (default: 0.1) |

**Example:**

```python
PropertyDef(
    "delay",
    PropertyType.FLOAT,
    default=1.0,
    min_value=0.0,
    max_value=60.0,
    decimals=1,
    step=0.5,
    label="Delay (seconds)"
)
```

### BOOLEAN

Checkbox toggle.

| Property | Value |
|----------|-------|
| Widget | Checkbox |
| Python Type | `bool` |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "headless",
    PropertyType.BOOLEAN,
    default=True,
    label="Headless Mode",
    tooltip="Run browser without visible window"
)
```

### ANY

Generic input that accepts any type.

| Property | Value |
|----------|-------|
| Widget | Text input (serialized) |
| Python Type | `Any` |
| Supports Variables | Yes |

**Use Cases:**
- Variable nodes
- Dynamic configuration
- Pass-through values

---

## Selection Types

### CHOICE

Dropdown selection from predefined options.

| Property | Value |
|----------|-------|
| Widget | Combo box |
| Python Type | `str` |
| Supports Variables | No |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `choices` | list | List of valid options (required) |

**Example:**

```python
PropertyDef(
    "browser_type",
    PropertyType.CHOICE,
    default="chromium",
    choices=["chromium", "firefox", "webkit"],
    label="Browser",
    tooltip="Browser engine to use"
)
```

### MULTI_CHOICE

Multiple selection from options.

| Property | Value |
|----------|-------|
| Widget | Multi-select list |
| Python Type | `list[str]` |
| Supports Variables | No |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `choices` | list | List of available options |

**Example:**

```python
PropertyDef(
    "capabilities",
    PropertyType.MULTI_CHOICE,
    default=["javascript", "cookies"],
    choices=["javascript", "cookies", "geolocation", "notifications"],
    label="Browser Capabilities"
)
```

---

## File and Path Types

### FILE_PATH

File selection dialog.

| Property | Value |
|----------|-------|
| Widget | File picker with browse button |
| Python Type | `str` (path) |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `filters` | str | File type filters (e.g., "JSON (*.json)") |
| `mode` | str | `open` or `save` |

**Example:**

```python
PropertyDef(
    "file_path",
    PropertyType.FILE_PATH,
    default="",
    filters="JSON Files (*.json);;All Files (*.*)",
    mode="open",
    label="Input File",
    tooltip="Select file to read"
)
```

### DIRECTORY_PATH

Directory/folder selection dialog.

| Property | Value |
|----------|-------|
| Widget | Folder picker with browse button |
| Python Type | `str` (path) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "output_dir",
    PropertyType.DIRECTORY_PATH,
    default="",
    label="Output Directory",
    tooltip="Folder for output files"
)
```

### FILE_PATTERN

Glob pattern input for file matching.

| Property | Value |
|----------|-------|
| Widget | Text input with pattern hint |
| Python Type | `str` |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "pattern",
    PropertyType.FILE_PATTERN,
    default="*.csv",
    label="File Pattern",
    tooltip="Glob pattern (e.g., *.csv, **/*.json)"
)
```

---

## Advanced Types

### JSON

JSON editor with syntax highlighting.

| Property | Value |
|----------|-------|
| Widget | Code editor (JSON mode) |
| Python Type | `dict` or `list` |
| Supports Variables | Yes (in string values) |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `schema` | dict | JSON Schema for validation |

**Example:**

```python
PropertyDef(
    "headers",
    PropertyType.JSON,
    default={"Content-Type": "application/json"},
    label="HTTP Headers",
    tooltip="Request headers as JSON object"
)
```

### CODE

Code editor with syntax highlighting.

| Property | Value |
|----------|-------|
| Widget | Code editor |
| Python Type | `str` |
| Supports Variables | Yes |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `language` | str | Syntax highlighting mode |

**Languages:**
- `python`, `javascript`, `json`, `html`, `css`, `sql`, `xml`

**Example:**

```python
PropertyDef(
    "script",
    PropertyType.CODE,
    default="# Your Python code here\nresult = data['value'] * 2",
    language="python",
    label="Python Script"
)
```

### SELECTOR

Element selector with picker tool.

| Property | Value |
|----------|-------|
| Widget | Text input + selector picker button |
| Python Type | `str` |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "selector",
    PropertyType.SELECTOR,
    default="",
    essential=True,
    label="Element Selector",
    tooltip="CSS or XPath selector",
    placeholder="#submit-button"
)
```

### COLOR

Color picker dialog.

| Property | Value |
|----------|-------|
| Widget | Color picker button |
| Python Type | `str` (hex color) |
| Supports Variables | No |

**Example:**

```python
PropertyDef(
    "highlight_color",
    PropertyType.COLOR,
    default="#FF0000",
    label="Highlight Color"
)
```

### DATE

Date picker.

| Property | Value |
|----------|-------|
| Widget | Calendar date picker |
| Python Type | `str` (ISO format) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "start_date",
    PropertyType.DATE,
    default="",
    label="Start Date",
    tooltip="Select start date"
)
```

### TIME

Time picker.

| Property | Value |
|----------|-------|
| Widget | Time picker |
| Python Type | `str` (HH:MM format) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "schedule_time",
    PropertyType.TIME,
    default="09:00",
    label="Schedule Time"
)
```

### DATETIME

Combined date and time picker.

| Property | Value |
|----------|-------|
| Widget | DateTime picker |
| Python Type | `str` (ISO format) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "scheduled_at",
    PropertyType.DATETIME,
    default="",
    label="Scheduled Date/Time"
)
```

### LIST

List of values editor.

| Property | Value |
|----------|-------|
| Widget | List editor with add/remove |
| Python Type | `list` |
| Supports Variables | Yes (per item) |

**Example:**

```python
PropertyDef(
    "urls",
    PropertyType.LIST,
    default=[],
    label="URLs to Process",
    tooltip="List of URLs to visit"
)
```

---

## Google Integration Types

### GOOGLE_CREDENTIAL

Google OAuth credential selector.

| Property | Value |
|----------|-------|
| Widget | Credential picker dropdown |
| Python Type | `str` (credential name) |
| Supports Variables | No |

**Example:**

```python
PropertyDef(
    "credential_name",
    PropertyType.GOOGLE_CREDENTIAL,
    default="google",
    label="Google Account"
)
```

### GOOGLE_SPREADSHEET

Google Sheets spreadsheet picker.

| Property | Value |
|----------|-------|
| Widget | Spreadsheet selector |
| Python Type | `str` (spreadsheet ID) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "spreadsheet_id",
    PropertyType.GOOGLE_SPREADSHEET,
    default="",
    label="Spreadsheet"
)
```

### GOOGLE_SHEET

Sheet name picker (depends on spreadsheet).

| Property | Value |
|----------|-------|
| Widget | Sheet selector dropdown |
| Python Type | `str` (sheet name) |
| Supports Variables | Yes |

**Example:**

```python
PropertyDef(
    "sheet_name",
    PropertyType.GOOGLE_SHEET,
    default="Sheet1",
    label="Sheet"
)
```

### GOOGLE_DRIVE_FILE

Google Drive file picker.

| Property | Value |
|----------|-------|
| Widget | File picker dialog |
| Python Type | `str` (file ID) |
| Supports Variables | Yes |

### GOOGLE_DRIVE_FOLDER

Google Drive folder picker.

| Property | Value |
|----------|-------|
| Widget | Folder picker dialog |
| Python Type | `str` (folder ID) |
| Supports Variables | Yes |

---

## Custom Type

### CUSTOM

Fully custom widget implementation.

| Property | Value |
|----------|-------|
| Widget | Custom widget class |
| Python Type | Any |
| Supports Variables | Depends on implementation |

**Options:**

| Option | Type | Description |
|--------|------|-------------|
| `widget_class` | type | Custom widget class reference |

**Example:**

```python
PropertyDef(
    "credentials",
    PropertyType.CUSTOM,
    widget_class=CredentialPickerWidget,
    label="Credentials"
)
```

---

## Property Visibility

Control when properties are displayed:

```python
from casare_rpa.domain.schemas import PropertyVisibility

PropertyDef(
    "advanced_option",
    PropertyType.STRING,
    visibility=PropertyVisibility.ADVANCED,  # Hidden in collapsible section
    ...
)
```

### Visibility Levels

| Level | Description |
|-------|-------------|
| `ESSENTIAL` | Always visible, even when node collapsed |
| `NORMAL` | Visible when node expanded (default) |
| `ADVANCED` | Hidden in "Advanced" collapsible section |
| `INTERNAL` | Never shown in UI (system use) |

---

## PropertyDef Reference

### Constructor

```python
PropertyDef(
    name: str,                    # Property identifier
    property_type: PropertyType,  # Widget type
    default: Any = None,          # Default value
    required: bool = False,       # Is required
    essential: bool = False,      # Keep visible when collapsed
    label: str = None,            # Display label (defaults to name)
    tooltip: str = "",            # Help tooltip
    placeholder: str = "",        # Placeholder text
    tab: str = "general",         # Property panel tab
    visibility: PropertyVisibility = PropertyVisibility.NORMAL,
    secret: bool = False,         # Mask in logs
    **kwargs                      # Type-specific options
)
```

### Common Options

| Option | Type | Description |
|--------|------|-------------|
| `default` | Any | Default value |
| `required` | bool | Validation required |
| `essential` | bool | Show when collapsed |
| `label` | str | Display label |
| `tooltip` | str | Help text |
| `placeholder` | str | Input placeholder |
| `tab` | str | Group tab name |
| `visibility` | PropertyVisibility | UI visibility |
| `secret` | bool | Mask in logs |

---

## Usage in Nodes

### Defining Properties

```python
from casare_rpa.domain.decorators import node, properties
from casare_rpa.domain.schemas import PropertyDef, PropertyType

@node(category="http")
@properties(
    PropertyDef(
        "url",
        PropertyType.STRING,
        required=True,
        essential=True,
        label="URL",
        placeholder="https://api.example.com"
    ),
    PropertyDef(
        "method",
        PropertyType.CHOICE,
        default="GET",
        choices=["GET", "POST", "PUT", "DELETE"],
        label="HTTP Method"
    ),
    PropertyDef(
        "headers",
        PropertyType.JSON,
        default={},
        label="Headers",
        tab="advanced"
    ),
    PropertyDef(
        "timeout",
        PropertyType.INTEGER,
        default=30000,
        min_value=1000,
        max_value=120000,
        label="Timeout (ms)",
        tab="advanced"
    )
)
class HttpRequestNode(BaseNode):
    pass
```

### Accessing Properties

```python
async def execute(self, inputs, context):
    # MODERN: Use get_parameter() for dual-source access (port -> config fallback)
    url = self.get_parameter("url")
    method = self.get_parameter("method", "GET")
    headers = self.get_parameter("headers", {})
    timeout = self.get_parameter("timeout", 30000)

    # LEGACY (DON'T USE): self.config.get("url")

    # Perform request...
```

---

## Related Documentation

- [Data Types](data-types.md) - Port data types
- [Creating Nodes](../developer-guide/extending/creating-nodes.md) - Node development guide
- [Visual Nodes](../developer-guide/extending/visual-nodes.md) - UI customization
