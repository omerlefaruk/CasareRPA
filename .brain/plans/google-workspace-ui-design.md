# Google Workspace UI Design

> UI components for Google Drive, Sheets, Gmail integration in CasareRPA Canvas.

## 1. Google OAuth Tab in Credential Manager

### Layout
```
+------------------------------------------------------------------+
|                    Credential Manager                        [x] |
+----------+------+------------+----------------------------------+
| API Keys | Logins | All Creds | **Google Accounts**              |
+----------+------+------------+----------------------------------+
|                                                                  |
|  Connected Accounts                                              |
|  +------------------------------------------------------------+  |
|  |  [G] john@gmail.com                          [Default] [x] |  |
|  |      Scopes: Drive, Sheets, Gmail                          |  |
|  |      Status: Valid | Expires: 2024-01-15                   |  |
|  +------------------------------------------------------------+  |
|  |  [G] work@company.com                                  [x] |  |
|  |      Scopes: Drive, Sheets                                 |  |
|  |      Status: Expired | Click to refresh                    |  |
|  +------------------------------------------------------------+  |
|                                                                  |
|  [+ Add Google Account]                                          |
|                                                                  |
+------------------------------------------------------------------+
|  Scope Management                                                |
|  +------------------------------------------------------------+  |
|  |  [ ] Gmail - Send and read emails                          |  |
|  |  [x] Google Drive - Read and write files                   |  |
|  |  [x] Google Sheets - Read and write spreadsheets           |  |
|  |  [ ] Google Calendar - Manage calendar events              |  |
|  |  [ ] Google Tasks - Manage tasks                           |  |
|  +------------------------------------------------------------+  |
|                                                                  |
+------------------------------------------------------------------+
|                                            [Save Changes] [Close]|
+------------------------------------------------------------------+
```

### Component Specifications

#### GoogleAccountListItem
| Property | Value |
|----------|-------|
| Height | 72px |
| Background | #252526 (card) |
| Border | 1px solid #3E3E42 |
| Border-radius | 6px |
| Padding | 12px 16px |
| Margin-bottom | 8px |

States:
- **Default**: Background #252526, border #3E3E42
- **Hover**: Background #2A2D2E, border #454545
- **Selected**: Background #094771, border #007ACC
- **Expired**: Red warning icon, "Expired" badge in #F44336
- **Refreshing**: Spinner animation, disabled controls

Elements:
```
+-----------------------------------------------------------+
| [G]  john@gmail.com                       [Default] [x]   |
|      Scopes: Drive, Sheets, Gmail                         |
|      Status: Valid | Expires: 2024-01-15                  |
+-----------------------------------------------------------+

[G] = Google logo icon (24x24)
Email = 14px, #E0E0E0, font-weight: 500
Scopes = 11px, #888888
Status = 11px, #4CAF50 (valid) / #F44336 (expired) / #FF9800 (warning)
[Default] = Badge, 11px, bg #264F78, text #4FC3F7
[x] = Remove button, 16x16, #888888 hover:#F44336
```

#### ScopeCheckbox
| Property | Value |
|----------|-------|
| Height | 32px |
| Checkbox size | 18x18 |
| Label font | 12px |
| Label color | #D4D4D4 |
| Description | 11px, #888888 |

States:
- **Unchecked**: Border #3E3E42, bg transparent
- **Checked**: Border #007ACC, bg #007ACC, checkmark white
- **Disabled**: Opacity 0.5, cursor not-allowed

#### AddAccountButton
```css
QPushButton {
    background: #2D2D30;
    border: 1px dashed #454545;
    border-radius: 6px;
    padding: 12px 16px;
    color: #007ACC;
    font-size: 13px;
    font-weight: 500;
    min-height: 40px;
}
QPushButton:hover {
    background: #2A2D2E;
    border-style: solid;
    border-color: #007ACC;
}
```

---

## 2. Credential Picker Dropdown Widget

### Layout
```
+----------------------------------+
| Google Credential            [v] |
+----------------------------------+
      |
      v
+----------------------------------+
| * john@gmail.com (default)       |
|   work@company.com               |
| --------------------------       |
| + Add Google Account...          |
+----------------------------------+
```

### Component Specifications

#### GoogleCredentialComboBox (NodeWidget)

Extends NodeComboBox with Google-specific features:
- Account avatar/icon prefix
- Default account indicator
- "Add Account" action item

Widget Properties:
| Property | Value |
|----------|-------|
| Width | 100% of property panel |
| Height | 28px (inline button standard) |
| Background | #3C3C50 |
| Border | 1px solid #505064 |
| Border-radius | 3px |
| Dropdown icon | Chevron-down, 12px |

Dropdown Item:
| Property | Value |
|----------|-------|
| Height | 32px |
| Padding | 8px 12px |
| Icon | [G] 16x16 |
| Email | 12px, #E0E0E0 |
| (default) badge | 10px, #888888 |

States:
- **Default**: bg #252526
- **Hover**: bg #2A2D2E
- **Selected**: bg #094771, checkmark icon

Separator:
- Height: 1px
- Color: #3E3E42
- Margin: 4px 8px

"Add Account" Item:
- Icon: + (16x16, #007ACC)
- Text: "Add Google Account...", #007ACC
- On click: Opens OAuth flow dialog

### Implementation Notes

```python
# Widget factory function pattern (from node_widgets.py)
def create_google_credential_widget(
    name: str,
    label: str,
    placeholder: str = "Select Google Account...",
) -> NodeBaseWidget:
    """
    Create a Google credential picker widget for node properties.

    Features:
    - Lists connected Google accounts
    - Shows default account indicator
    - "Add Account" action opens OAuth flow
    - Refreshes token if expired before listing
    """
    # Implementation follows create_selector_widget pattern
    pass
```

---

## 3. Cascading Dropdown Widgets

### Layout (Sheets Example)
```
+------------------------------------------------+
| Credential:   [john@gmail.com              v]  |
+------------------------------------------------+
| Spreadsheet:  [Loading...                  v]  |
|                      |
|                      v (after credential selected)
| Spreadsheet:  [Sales Data 2024             v]  |
+------------------------------------------------+
| Sheet:        [Sheet1                      v]  |
+------------------------------------------------+
| Range:        [A1:Z100                       ] |
+------------------------------------------------+
```

### Component Specifications

#### CascadingDropdown System

Parent-child relationship:
```
GoogleCredentialComboBox
    |
    +-> SpreadsheetComboBox (async fetch on parent change)
            |
            +-> SheetComboBox (async fetch on parent change)
```

#### SpreadsheetComboBox

| Property | Value |
|----------|-------|
| Width | 100% |
| Height | 28px |
| Background | #3C3C50 |
| Border | 1px solid #505064 |
| Font | 12px |

States:
- **Disabled (no credential)**: Opacity 0.5, placeholder "Select credential first"
- **Loading**: Spinner icon (animated), text "Loading..."
- **Loaded**: Normal dropdown with items
- **Error**: Red border #F44336, tooltip with error message
- **Empty**: Text "No spreadsheets found"

Dropdown Item:
| Property | Value |
|----------|-------|
| Height | 36px |
| Icon | Spreadsheet icon (16x16, green #34A853) |
| Title | 12px, #E0E0E0, truncate with ellipsis |
| Last modified | 10px, #888888 |

```
+--------------------------------------------------+
| [sheet-icon] Sales Data 2024                     |
|              Modified: Dec 5, 2024               |
+--------------------------------------------------+
| [sheet-icon] Monthly Report                      |
|              Modified: Dec 1, 2024               |
+--------------------------------------------------+
```

#### SheetComboBox

Similar to SpreadsheetComboBox but:
- Icon: Tab icon (16x16)
- Shows sheet color as left border (if available)
- Shows row count as secondary text

```
+--------------------------------------------------+
| [tab-icon] Sheet1                    (1000 rows) |
+--------------------------------------------------+
| [tab-icon] Summary                   (50 rows)   |
+--------------------------------------------------+
```

#### Range Input

VariableAwareLineEdit with validation:
- Pattern: `^[A-Z]+[0-9]+:[A-Z]+[0-9]+$`
- Examples shown in placeholder: "e.g., A1:Z100"
- Invalid input: Red border, tooltip "Invalid range format"

---

## 4. OAuth Flow Dialog

### Layout
```
+------------------------------------------------+
|            Connect Google Account              |
+------------------------------------------------+
|                                                |
|        [Google G Logo - Large 64x64]           |
|                                                |
|    Connecting to Google...                     |
|    A browser window will open.                 |
|                                                |
|    +--------------------------------------+    |
|    |  [spinner]  Waiting for             |    |
|    |             authorization...        |    |
|    +--------------------------------------+    |
|                                                |
|    Requested permissions:                      |
|    - Read and write Google Drive files         |
|    - Read and write Google Sheets              |
|                                                |
|                              [Cancel]          |
+------------------------------------------------+
```

### Component Specifications

#### OAuthFlowDialog

| Property | Value |
|----------|-------|
| Width | 400px |
| Min-height | 280px |
| Background | #1E1E1E |
| Border | 1px solid #3E3E42 |
| Border-radius | 8px |
| Modal | True |

#### Status Panel

| Property | Value |
|----------|-------|
| Background | #252526 |
| Border | 1px solid #3E3E42 |
| Border-radius | 4px |
| Padding | 16px |
| Text-align | center |

States:
- **Connecting**: Spinner + "Waiting for authorization..."
- **Success**: Green checkmark + "Connected successfully!"
- **Error**: Red X + "Connection failed" + error message
- **Timeout**: Orange warning + "Authorization timed out"

#### Cancel Button

Per UI Standards (32px action button):
```css
QPushButton {
    background: #2D2D30;
    border: 1px solid #454545;
    border-radius: 4px;
    padding: 0 16px;
    color: #D4D4D4;
    font-size: 12px;
    font-weight: 500;
    min-height: 32px;
}
```

### Flow States

1. **Initial**: Shows "Connecting..." message
2. **Browser Opened**: Shows "Waiting for authorization..."
3. **Success**: Shows checkmark, auto-closes after 2s
4. **Error**: Shows error message, enables "Try Again" button
5. **Cancelled**: Dialog closes immediately

---

## 5. Node Visual Design

### Google Node Category Colors

| Service | Primary Color | Icon Color | Border |
|---------|--------------|------------|--------|
| Google Drive | #4285F4 (blue) | #4285F4 | #3367D6 |
| Google Sheets | #34A853 (green) | #34A853 | #2D9249 |
| Gmail | #EA4335 (red) | #EA4335 | #D93025 |
| Google Calendar | #4285F4 | #4285F4 | #3367D6 |
| Google Tasks | #4285F4 | #4285F4 | #3367D6 |

### Node Layout Template
```
+----------------------------------------------+
| [icon] Read Spreadsheet                      |
+----------------------------------------------+
| exec_in o                         o exec_out |
+----------------------------------------------+
| Credential:  [john@gmail.com          v]     |
| Spreadsheet: [Sales Data 2024         v]     |
| Sheet:       [Sheet1                  v]     |
| Range:       [A1:Z100                   ]    |
+----------------------------------------------+
|                                  o data_out  |
|                               (DataTable)    |
+----------------------------------------------+
```

### Node Icon Specifications

| Icon | Size | Format | Colors |
|------|------|--------|--------|
| Header icon | 20x20 | SVG | Service color |
| Port icons | 10x10 | Shape | Type-based (per port_shapes.py) |

Google-specific icons (SVG paths):
- Drive: Folder/cloud shape
- Sheets: Grid/table shape
- Gmail: Envelope shape
- Calendar: Calendar grid shape

### Port Layout

Input ports (left side):
```
o exec_in      (EXECUTION - triangle)
o spreadsheet  (STRING - circle, for dynamic input)
```

Output ports (right side):
```
exec_out o     (EXECUTION - triangle)
data_out o     (DATATABLE - hexagon)
row_count o    (INTEGER - square)
```

### Node Header Styling

```css
/* Google Sheets node example */
.node-header {
    background: linear-gradient(180deg, #34A853 0%, #2D9249 100%);
    border-radius: 6px 6px 0 0;
    padding: 8px 12px;
    color: white;
}

.node-header-icon {
    width: 20px;
    height: 20px;
    margin-right: 8px;
}

.node-header-title {
    font-size: 13px;
    font-weight: 600;
}
```

---

## 6. Widget Implementation Hierarchy

```
casare_rpa/presentation/canvas/
+-- ui/
|   +-- widgets/
|   |   +-- google_credential_picker.py     # NEW: Credential dropdown
|   |   +-- cascading_dropdown.py           # NEW: Parent-child dropdowns
|   |   +-- async_combo_box.py              # NEW: Async-loading combo
|   +-- dialogs/
|   |   +-- credential_manager_dialog.py    # MODIFY: Add Google tab
|   |   +-- oauth_flow_dialog.py            # NEW: OAuth browser flow
+-- graph/
|   +-- node_widgets.py                     # MODIFY: Add factory functions
```

### Factory Functions (node_widgets.py additions)

```python
def create_google_credential_widget(
    name: str,
    label: str,
    scopes: List[str],
) -> NodeBaseWidget:
    """Google account picker with add account action."""
    pass

def create_async_combo_widget(
    name: str,
    label: str,
    fetch_func: Callable[[], Awaitable[List[dict]]],
    parent_widget: Optional[NodeBaseWidget] = None,
    placeholder: str = "Select...",
    loading_text: str = "Loading...",
) -> NodeBaseWidget:
    """Async-loading dropdown that fetches items on demand."""
    pass

def create_cascading_dropdowns(
    configs: List[CascadingDropdownConfig],
) -> List[NodeBaseWidget]:
    """Create linked parent-child dropdown widgets."""
    pass
```

### CascadingDropdownConfig

```python
@dataclass
class CascadingDropdownConfig:
    name: str
    label: str
    fetch_func: Callable[[Optional[str]], Awaitable[List[dict]]]
    parent_name: Optional[str] = None  # Name of parent widget
    placeholder: str = "Select..."
    loading_text: str = "Loading..."
```

---

## 7. Interaction Flows

### Connect Google Account Flow

```
User clicks "Add Google Account"
    |
    v
OAuth Dialog opens
    |
    v
Browser opens to Google OAuth
    |
    +---> User authorizes ---> Dialog shows success
    |                              |
    |                              v
    |                         Token stored
    |                              |
    |                              v
    |                         Dialog closes
    |                              |
    |                              v
    |                         Account appears in list
    |
    +---> User cancels/times out ---> Dialog shows error/timeout
                                           |
                                           v
                                      User can retry or close
```

### Cascading Dropdown Flow

```
User selects credential
    |
    v
Spreadsheet dropdown: Loading...
    |
    v
API fetch spreadsheets (async)
    |
    +---> Success: Populate dropdown
    |        |
    |        v
    |     User selects spreadsheet
    |        |
    |        v
    |     Sheet dropdown: Loading...
    |        |
    |        v
    |     API fetch sheets (async)
    |        |
    |        v
    |     Populate sheet dropdown
    |
    +---> Error: Show error state
             |
             v
          Red border + tooltip
```

---

## 8. Keyboard Navigation

### Credential Manager Dialog

| Key | Action |
|-----|--------|
| Tab | Move between accounts |
| Enter | Select account / toggle scope |
| Delete | Remove selected account |
| Escape | Close dialog |

### Cascading Dropdowns

| Key | Action |
|-----|--------|
| Tab | Move to next dropdown |
| Up/Down | Navigate dropdown items |
| Enter | Select item |
| Escape | Close dropdown |
| Backspace | Clear and focus parent |

---

## 9. Error States

### Credential Errors

| Error | Visual | Message |
|-------|--------|---------|
| Token expired | Yellow warning icon | "Token expired. Click to refresh." |
| Token invalid | Red X icon | "Token invalid. Please reconnect." |
| No scopes | Orange warning | "No permissions granted." |
| Network error | Red X | "Could not connect to Google." |

### Dropdown Errors

| Error | Visual | Message |
|-------|--------|---------|
| Fetch failed | Red border | "Failed to load items" |
| No items | Gray text | "No items found" |
| Invalid parent | Disabled | "Select [parent] first" |

---

## 10. Implementation Notes

### Qt Widget Recommendations

| Component | Qt Widget | Notes |
|-----------|-----------|-------|
| Account list | QListWidget | Custom delegate for complex items |
| Credential picker | QComboBox | Custom popup with sections |
| Scope checkboxes | QCheckBox | Styled with QSS |
| Async combo | QComboBox | Subclass with fetch_items() |
| OAuth dialog | QDialog | Modal, custom styling |
| Status spinner | QMovie/QPropertyAnimation | Animated GIF or CSS animation |

### Async Patterns

```python
# Use QTimer.singleShot for async-to-sync bridge
async def fetch_spreadsheets(credential_id: str) -> List[dict]:
    """Async fetch from Google API."""
    pass

def on_credential_changed(credential_id: str):
    """Sync slot that triggers async fetch."""
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_spreadsheets(credential_id))
    future.add_done_callback(lambda f: self._populate_spreadsheets(f.result()))
```

### Token Refresh Strategy

1. Check token expiry before API calls
2. If expired, attempt silent refresh
3. If refresh fails, prompt re-authentication
4. Cache refresh token securely (CredentialStore)

---

## 11. Accessibility

### Color Contrast Compliance (WCAG 2.1 AA)

| Element | Foreground | Background | Ratio |
|---------|------------|------------|-------|
| Primary text | #E0E0E0 | #252526 | 11.3:1 |
| Secondary text | #888888 | #252526 | 4.5:1 |
| Error text | #F44336 | #252526 | 5.5:1 |
| Success text | #4CAF50 | #252526 | 5.2:1 |
| Accent (blue) | #007ACC | #252526 | 4.6:1 |

### Non-Color Indicators

- Token expired: Warning icon + "Expired" text
- Selected account: Checkmark icon + background change
- Error state: Icon + border + tooltip text
- Loading state: Spinner animation + "Loading..." text

### Keyboard Support

All interactive elements must be:
- Focusable via Tab
- Operable via Enter/Space
- Dismissable via Escape
- Navigable via arrow keys (lists/dropdowns)

---

## 12. Open Questions

1. **Multi-tenant support**: Should credentials be per-project or global?
2. **Default account**: Auto-select last-used or require explicit selection?
3. **Scope granularity**: Per-account or per-node scope configuration?
4. **Offline access**: Store refresh tokens for headless robot execution?
5. **Rate limiting**: How to handle Google API quota exceeded errors?
6. **Sheet preview**: Show data preview in dropdown or separate panel?
