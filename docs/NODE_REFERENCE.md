# Node Reference

Complete reference for all CasareRPA automation nodes.

## Node Categories

| Category | Description | Count |
|----------|-------------|-------|
| Basic | Start, End, Comment | 3 |
| Browser | Launch, close, tabs | 3 |
| Navigation | URL, back, forward, refresh | 4 |
| Interaction | Click, type, select | 3 |
| Data Operations | String, math, regex, JSON | 11 |
| Control Flow | If, loops, switch | 6 |
| Error Handling | Try, retry, throw | 5 |
| Variables | Get, set, increment | 3 |
| Wait | Delays, element waits | 3 |
| Utility | HTTP, log, transform | 4 |
| File System | Read, write, copy, zip | 16 |
| Desktop - Application | Launch, close, activate | 4 |
| Desktop - Window | Resize, move, state | 7 |
| Desktop - Mouse/Keyboard | Click, type, hotkeys | 6 |
| Desktop - Wait/Verify | Wait, verify elements | 4 |
| Desktop - Screenshot/OCR | Capture, compare, OCR | 4 |
| Desktop - Office | Excel, Word, Outlook | 12 |

**Total: 98+ nodes**

---

## Basic Nodes

### StartNode
Entry point for workflow execution.

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | Output | Execution output |

### EndNode
Terminates workflow execution.

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `result` | Input | Optional result value |

### CommentNode
Annotation node for documentation.

| Property | Type | Description |
|----------|------|-------------|
| `text` | String | Comment text |

---

## Browser Nodes

### LaunchBrowserNode
Launch a browser instance.

| Property | Type | Description |
|----------|------|-------------|
| `browser_type` | String | chromium, firefox, webkit |
| `headless` | Boolean | Run headless mode |
| `args` | List | Additional browser arguments |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `browser` | Output | Browser instance |
| `page` | Output | Initial page |
| `exec_out` | Output | Execution output |

### CloseBrowserNode
Close browser instance.

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `browser` | Input | Browser to close |
| `exec_out` | Output | Execution output |

### NewTabNode
Open a new browser tab.

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `browser` | Input | Browser instance |
| `page` | Output | New page |
| `exec_out` | Output | Execution output |

---

## Navigation Nodes

### GoToURLNode
Navigate to a URL.

| Property | Type | Description |
|----------|------|-------------|
| `url` | String | Target URL |
| `timeout` | Integer | Navigation timeout (ms) |
| `wait_until` | String | load, domcontentloaded, networkidle |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `page` | Input | Page to navigate |
| `page` | Output | Navigated page |
| `exec_out` | Output | Execution output |

### GoBackNode
Navigate back in history.

### GoForwardNode
Navigate forward in history.

### RefreshPageNode
Refresh current page.

---

## Interaction Nodes

### ClickElementNode
Click on an element.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | Element selector |
| `button` | String | left, right, middle |
| `click_count` | Integer | Number of clicks |
| `delay` | Integer | Delay between clicks (ms) |
| `timeout` | Integer | Wait timeout (ms) |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `page` | Input | Page containing element |
| `exec_out` | Output | Execution output |

### TypeTextNode
Type text into an element.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | Element selector |
| `text` | String | Text to type |
| `delay` | Integer | Delay between keystrokes (ms) |
| `clear_first` | Boolean | Clear field before typing |

### SelectDropdownNode
Select option from dropdown.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | Select element selector |
| `value` | String | Option value to select |
| `by` | String | value, label, index |

---

## Data Operations Nodes

### ConcatenateNode
Join strings together.

| Property | Type | Description |
|----------|------|-------------|
| `separator` | String | String between items |

| Port | Type | Description |
|------|------|-------------|
| `string1` | Input | First string |
| `string2` | Input | Second string |
| `result` | Output | Concatenated string |

### FormatStringNode
Format string with placeholders.

| Property | Type | Description |
|----------|------|-------------|
| `template` | String | Template with {0}, {1} placeholders |

### RegexMatchNode
Match text against regex pattern.

| Property | Type | Description |
|----------|------|-------------|
| `pattern` | String | Regular expression |
| `flags` | String | Regex flags (i, m, s) |

| Port | Type | Description |
|------|------|-------------|
| `text` | Input | Text to search |
| `matches` | Output | List of matches |
| `found` | Output | Boolean if found |

### RegexReplaceNode
Replace text using regex.

### MathOperationNode
Perform math operations.

| Property | Type | Description |
|----------|------|-------------|
| `operation` | String | add, subtract, multiply, divide, modulo, power |

| Port | Type | Description |
|------|------|-------------|
| `a` | Input | First operand |
| `b` | Input | Second operand |
| `result` | Output | Calculation result |

### ComparisonNode
Compare two values.

| Property | Type | Description |
|----------|------|-------------|
| `operator` | String | ==, !=, <, >, <=, >= |

| Port | Type | Description |
|------|------|-------------|
| `a` | Input | First value |
| `b` | Input | Second value |
| `result` | Output | Boolean result |

### CreateListNode
Create a list from values.

### ListGetItemNode
Get item from list by index.

### JsonParseNode
Parse JSON string to object.

### GetPropertyNode
Get property from object.

### ExtractTextNode
Extract text from element.

### GetAttributeNode
Get attribute from element.

### ScreenshotNode
Take screenshot of page/element.

---

## Control Flow Nodes

### IfNode
Conditional branching.

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `condition` | Input | Boolean condition |
| `then` | Output | True branch |
| `else` | Output | False branch |

### ForLoopNode
Iterate over a list.

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | String | Loop variable name |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `items` | Input | List to iterate |
| `loop_body` | Output | Loop iteration |
| `current_item` | Output | Current item |
| `index` | Output | Current index |
| `completed` | Output | After loop completes |

### WhileLoopNode
Loop while condition is true.

| Property | Type | Description |
|----------|------|-------------|
| `max_iterations` | Integer | Safety limit |

| Port | Type | Description |
|------|------|-------------|
| `condition` | Input | Loop condition |
| `loop_body` | Output | Loop body |
| `completed` | Output | After loop |

### BreakNode
Exit current loop.

### ContinueNode
Skip to next iteration.

### SwitchNode
Multi-way branching.

| Property | Type | Description |
|----------|------|-------------|
| `cases` | List | Case values |

| Port | Type | Description |
|------|------|-------------|
| `value` | Input | Value to switch on |
| `case_0..N` | Output | Case outputs |
| `default` | Output | Default case |

---

## Error Handling Nodes

### TryNode
Try-catch error handling.

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `try` | Output | Try block |
| `catch` | Output | Error handler |
| `finally` | Output | Finally block |
| `error` | Output | Error message |

### RetryNode
Retry on failure.

| Property | Type | Description |
|----------|------|-------------|
| `max_retries` | Integer | Maximum attempts |
| `delay` | Float | Delay between retries (s) |
| `backoff` | Float | Backoff multiplier |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `body` | Output | Code to retry |
| `success` | Output | On success |
| `failure` | Output | On final failure |
| `attempt` | Output | Current attempt number |

### RetrySuccessNode
Signal retry success (continue).

### RetryFailNode
Signal retry failure (abort).

### ThrowErrorNode
Throw a custom error.

| Property | Type | Description |
|----------|------|-------------|
| `message` | String | Error message |
| `error_code` | Integer | Error code |

---

## Variable Nodes

### SetVariableNode
Set a workflow variable.

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | String | Variable name |

| Port | Type | Description |
|------|------|-------------|
| `exec_in` | Input | Execution input |
| `value` | Input | Value to set |
| `exec_out` | Output | Execution output |

### GetVariableNode
Get a workflow variable.

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | String | Variable name |
| `default_value` | Any | Default if not found |

| Port | Type | Description |
|------|------|-------------|
| `value` | Output | Variable value |

### IncrementVariableNode
Increment a numeric variable.

| Property | Type | Description |
|----------|------|-------------|
| `variable_name` | String | Variable name |
| `amount` | Integer | Increment amount |

---

## Wait Nodes

### WaitNode
Fixed delay.

| Property | Type | Description |
|----------|------|-------------|
| `seconds` | Float | Delay duration |

### WaitForElementNode
Wait for element to appear.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | Element selector |
| `state` | String | visible, hidden, attached, detached |
| `timeout` | Integer | Maximum wait time (ms) |

| Port | Type | Description |
|------|------|-------------|
| `page` | Input | Page to search |
| `element` | Output | Found element |

### WaitForNavigationNode
Wait for navigation to complete.

| Property | Type | Description |
|----------|------|-------------|
| `wait_until` | String | load, domcontentloaded, networkidle |
| `timeout` | Integer | Maximum wait time (ms) |

---

## Utility Nodes

### HttpRequestNode
Make HTTP requests.

| Property | Type | Description |
|----------|------|-------------|
| `url` | String | Request URL |
| `method` | String | GET, POST, PUT, DELETE, PATCH |
| `headers` | Dict | Request headers |
| `body` | Any | Request body |
| `timeout` | Integer | Request timeout (ms) |

| Port | Type | Description |
|------|------|-------------|
| `response` | Output | Response object |
| `status` | Output | HTTP status code |
| `body` | Output | Response body |

### ValidateNode
Validate data against rules.

### TransformNode
Transform data structure.

### LogNode
Log a message.

| Property | Type | Description |
|----------|------|-------------|
| `level` | String | debug, info, warning, error |

| Port | Type | Description |
|------|------|-------------|
| `message` | Input | Message to log |

---

## File System Nodes

### ReadFileNode
Read file contents.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | File path |
| `encoding` | String | File encoding (utf-8) |

| Port | Type | Description |
|------|------|-------------|
| `content` | Output | File contents |

### WriteFileNode
Write content to file.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | File path |
| `encoding` | String | File encoding |
| `create_dirs` | Boolean | Create parent directories |

| Port | Type | Description |
|------|------|-------------|
| `content` | Input | Content to write |

### AppendFileNode
Append content to file.

### DeleteFileNode
Delete a file.

### CopyFileNode
Copy a file.

| Property | Type | Description |
|----------|------|-------------|
| `source` | String | Source path |
| `destination` | String | Destination path |
| `overwrite` | Boolean | Overwrite if exists |

### MoveFileNode
Move/rename a file.

### CreateDirectoryNode
Create a directory.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | Directory path |
| `parents` | Boolean | Create parent directories |

### ListDirectoryNode
List directory contents.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | Directory path |
| `pattern` | String | Glob pattern filter |
| `recursive` | Boolean | Include subdirectories |

| Port | Type | Description |
|------|------|-------------|
| `files` | Output | List of file paths |

### FileExistsNode
Check if file exists.

| Port | Type | Description |
|------|------|-------------|
| `path` | Input | File path |
| `exists` | Output | Boolean result |

### GetFileInfoNode
Get file metadata.

| Port | Type | Description |
|------|------|-------------|
| `path` | Input | File path |
| `size` | Output | File size (bytes) |
| `modified` | Output | Last modified time |
| `created` | Output | Creation time |

### ReadCSVNode
Read CSV file to list.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | CSV file path |
| `delimiter` | String | Column delimiter |
| `has_header` | Boolean | First row is header |

| Port | Type | Description |
|------|------|-------------|
| `rows` | Output | List of row dicts |
| `headers` | Output | Column headers |

### WriteCSVNode
Write list to CSV file.

### ReadJSONFileNode
Read JSON file.

### WriteJSONFileNode
Write to JSON file.

### ZipFilesNode
Create ZIP archive.

| Property | Type | Description |
|----------|------|-------------|
| `output_path` | String | ZIP file path |

| Port | Type | Description |
|------|------|-------------|
| `files` | Input | List of file paths |

### UnzipFilesNode
Extract ZIP archive.

| Property | Type | Description |
|----------|------|-------------|
| `archive_path` | String | ZIP file path |
| `output_dir` | String | Extraction directory |

---

## Desktop - Application Nodes

### LaunchApplicationNode
Launch a Windows application.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | Executable path |
| `arguments` | String | Command line arguments |
| `working_dir` | String | Working directory |
| `wait_for_window` | Boolean | Wait for window to appear |
| `timeout` | Integer | Wait timeout (ms) |

### CloseApplicationNode
Close an application.

| Property | Type | Description |
|----------|------|-------------|
| `window_title` | String | Window title pattern |
| `force` | Boolean | Force close |

### ActivateWindowNode
Bring window to foreground.

| Property | Type | Description |
|----------|------|-------------|
| `window_title` | String | Window title pattern |

### GetWindowListNode
Get list of open windows.

| Port | Type | Description |
|------|------|-------------|
| `windows` | Output | List of window info |

---

## Desktop - Window Nodes

### ResizeWindowNode
Resize a window.

| Property | Type | Description |
|----------|------|-------------|
| `window_title` | String | Window title pattern |
| `width` | Integer | New width |
| `height` | Integer | New height |

### MoveWindowNode
Move a window.

| Property | Type | Description |
|----------|------|-------------|
| `window_title` | String | Window title pattern |
| `x` | Integer | New X position |
| `y` | Integer | New Y position |

### MaximizeWindowNode
Maximize a window.

### MinimizeWindowNode
Minimize a window.

### RestoreWindowNode
Restore a minimized/maximized window.

### GetWindowPropertiesNode
Get window properties.

| Port | Type | Description |
|------|------|-------------|
| `title` | Output | Window title |
| `x` | Output | X position |
| `y` | Output | Y position |
| `width` | Output | Width |
| `height` | Output | Height |
| `state` | Output | Window state |

### SetWindowStateNode
Set window state.

| Property | Type | Description |
|----------|------|-------------|
| `state` | String | normal, minimized, maximized |

---

## Desktop - Mouse & Keyboard Nodes

### MoveMouseNode
Move mouse cursor.

| Property | Type | Description |
|----------|------|-------------|
| `x` | Integer | Target X coordinate |
| `y` | Integer | Target Y coordinate |

### MouseClickNode
Click mouse button.

| Property | Type | Description |
|----------|------|-------------|
| `x` | Integer | Click X coordinate |
| `y` | Integer | Click Y coordinate |
| `button` | String | left, right, middle |
| `clicks` | Integer | Number of clicks |

### SendKeysNode
Type text via keyboard.

| Property | Type | Description |
|----------|------|-------------|
| `text` | String | Text to type |
| `interval` | Float | Delay between keys (s) |

### SendHotKeyNode
Send keyboard shortcut.

| Property | Type | Description |
|----------|------|-------------|
| `keys` | String | Key combination (Ctrl+C) |

### GetMousePositionNode
Get current mouse position.

| Port | Type | Description |
|------|------|-------------|
| `x` | Output | Current X |
| `y` | Output | Current Y |

### DragMouseNode
Drag mouse from point to point.

| Property | Type | Description |
|----------|------|-------------|
| `from_x` | Integer | Start X |
| `from_y` | Integer | Start Y |
| `to_x` | Integer | End X |
| `to_y` | Integer | End Y |

---

## Desktop - Wait & Verification Nodes

### WaitForElementNode (Desktop)
Wait for desktop UI element.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | UI Automation selector |
| `timeout` | Integer | Wait timeout (ms) |

### WaitForWindowNode
Wait for window to appear.

| Property | Type | Description |
|----------|------|-------------|
| `window_title` | String | Window title pattern |
| `timeout` | Integer | Wait timeout (ms) |

### VerifyElementExistsNode
Check if element exists.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | UI Automation selector |

| Port | Type | Description |
|------|------|-------------|
| `exists` | Output | Boolean result |

### VerifyElementPropertyNode
Verify element property value.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | UI Automation selector |
| `property` | String | Property name |
| `expected` | Any | Expected value |

---

## Desktop - Screenshot & OCR Nodes

### CaptureScreenshotNode
Capture screen/region screenshot.

| Property | Type | Description |
|----------|------|-------------|
| `output_path` | String | Image file path |
| `region` | Tuple | Optional region (x, y, w, h) |

### CaptureElementImageNode
Capture screenshot of element.

| Property | Type | Description |
|----------|------|-------------|
| `selector` | String | Element selector |
| `output_path` | String | Image file path |

### OCRExtractTextNode
Extract text from image using OCR.

| Property | Type | Description |
|----------|------|-------------|
| `image_path` | String | Image file path |
| `language` | String | OCR language (eng) |

| Port | Type | Description |
|------|------|-------------|
| `text` | Output | Extracted text |

### CompareImagesNode
Compare two images.

| Property | Type | Description |
|----------|------|-------------|
| `image1` | String | First image path |
| `image2` | String | Second image path |
| `threshold` | Float | Similarity threshold (0-1) |

| Port | Type | Description |
|------|------|-------------|
| `match` | Output | Boolean if similar |
| `similarity` | Output | Similarity score |

---

## Desktop - Office Nodes

### Excel Nodes

#### ExcelOpenNode
Open Excel workbook.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | Excel file path |
| `show_window` | Boolean | Show Excel window |

#### ExcelReadCellNode
Read cell value.

| Property | Type | Description |
|----------|------|-------------|
| `cell` | String | Cell address (A1) |
| `sheet` | String | Sheet name |

#### ExcelWriteCellNode
Write cell value.

| Property | Type | Description |
|----------|------|-------------|
| `cell` | String | Cell address |
| `value` | Any | Value to write |
| `sheet` | String | Sheet name |

#### ExcelGetRangeNode
Read range of cells.

| Property | Type | Description |
|----------|------|-------------|
| `range` | String | Range address (A1:D10) |
| `sheet` | String | Sheet name |

| Port | Type | Description |
|------|------|-------------|
| `data` | Output | 2D list of values |

#### ExcelCloseNode
Close Excel workbook.

| Property | Type | Description |
|----------|------|-------------|
| `save` | Boolean | Save before closing |

### Word Nodes

#### WordOpenNode
Open Word document.

| Property | Type | Description |
|----------|------|-------------|
| `path` | String | Document path |
| `show_window` | Boolean | Show Word window |

#### WordGetTextNode
Get document text.

| Port | Type | Description |
|------|------|-------------|
| `text` | Output | Document content |

#### WordReplaceTextNode
Find and replace text.

| Property | Type | Description |
|----------|------|-------------|
| `find` | String | Text to find |
| `replace` | String | Replacement text |
| `match_case` | Boolean | Case sensitive |

#### WordCloseNode
Close Word document.

| Property | Type | Description |
|----------|------|-------------|
| `save` | Boolean | Save before closing |

### Outlook Nodes

#### OutlookSendEmailNode
Send email via Outlook.

| Property | Type | Description |
|----------|------|-------------|
| `to` | String | Recipient(s) |
| `cc` | String | CC recipient(s) |
| `bcc` | String | BCC recipient(s) |
| `subject` | String | Email subject |
| `body` | String | Email body |
| `is_html` | Boolean | Body is HTML |
| `attachments` | List | File paths to attach |

#### OutlookReadEmailsNode
Read emails from folder.

| Property | Type | Description |
|----------|------|-------------|
| `folder` | String | Folder name (Inbox) |
| `count` | Integer | Number of emails |
| `unread_only` | Boolean | Only unread |

| Port | Type | Description |
|------|------|-------------|
| `emails` | Output | List of email data |

#### OutlookGetInboxCountNode
Get inbox email count.

| Port | Type | Description |
|------|------|-------------|
| `total` | Output | Total emails |
| `unread` | Output | Unread emails |
