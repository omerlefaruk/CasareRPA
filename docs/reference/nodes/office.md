# Office Automation Nodes

Office automation nodes provide direct integration with Microsoft Office applications (Excel, Word, Outlook) using COM automation. These nodes are Windows-only and require the Office application to be installed.

## Prerequisites

```bash
pip install pywin32
```

> **Important:** These nodes require Microsoft Office installed on the Windows machine. They use COM automation to interact with Office applications directly.

---

## Excel Nodes

### ExcelOpenNode

Open an Excel workbook.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `file_path` | FILE_PATH | (required) | Path to Excel file (.xlsx, .xls) |
| `show_excel` | BOOLEAN | `false` | Show Excel window |
| `read_only` | BOOLEAN | `false` | Open in read-only mode |
| `create_if_missing` | BOOLEAN | `false` | Create new file if not found |

#### Ports

**Inputs:**
- `file_path` (STRING) - Excel file path

**Outputs:**
- `workbook` (ANY) - Excel workbook COM object
- `app` (ANY) - Excel application COM object
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Open Excel file
excel_open = ExcelOpenNode(
    node_id="open_excel",
    config={
        "file_path": "C:\\Data\\report.xlsx",
        "show_excel": False,
        "read_only": False
    }
)
```

> **Note:** Set `read_only: true` to help bypass Protected View for files from untrusted locations.

---

### ExcelReadCellNode

Read a single cell value from Excel.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sheet` | STRING | `1` | Sheet name or index (1-based) |
| `cell` | STRING | (required) | Cell reference (e.g., A1, B2) |

#### Ports

**Inputs:**
- `workbook` (ANY) - Excel workbook object
- `sheet` (ANY) - Sheet name or index
- `cell` (STRING) - Cell reference

**Outputs:**
- `value` (ANY) - Cell value
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Read cell A1 from Sheet1
read_cell = ExcelReadCellNode(
    node_id="read_cell",
    config={
        "sheet": "Sheet1",
        "cell": "A1"
    }
)
# Connect workbook from ExcelOpenNode
```

---

### ExcelWriteCellNode

Write a value to an Excel cell.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sheet` | STRING | `1` | Sheet name or index |
| `cell` | STRING | (required) | Cell reference |
| `value` | STRING | `""` | Value to write |

#### Ports

**Inputs:**
- `workbook` (ANY) - Excel workbook object
- `sheet` (ANY) - Sheet name or index
- `cell` (STRING) - Cell reference
- `value` (ANY) - Value to write

**Outputs:**
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Write value to cell B5
write_cell = ExcelWriteCellNode(
    node_id="write_cell",
    config={
        "sheet": "Results",
        "cell": "B5",
        "value": "{{calculated_total}}"
    }
)
```

---

### ExcelGetRangeNode

Read a range of cells from Excel.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sheet` | STRING | `1` | Sheet name or index |
| `range` | STRING | (required) | Range reference (e.g., A1:C10) |

#### Ports

**Inputs:**
- `workbook` (ANY) - Excel workbook object
- `sheet` (ANY) - Sheet name or index
- `range` (STRING) - Range reference

**Outputs:**
- `data` (ANY) - 2D list of values
- `rows` (INTEGER) - Number of rows
- `columns` (INTEGER) - Number of columns
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Read data table from Excel
get_range = ExcelGetRangeNode(
    node_id="get_data",
    config={
        "sheet": "Data",
        "range": "A1:G100"
    }
)
# Returns 2D list: [[row1_data], [row2_data], ...]
```

---

### ExcelCloseNode

Close an Excel workbook and optionally quit the application.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `save` | BOOLEAN | `true` | Save before closing |
| `quit_app` | BOOLEAN | `true` | Quit Excel application |

#### Ports

**Inputs:**
- `workbook` (ANY) - Excel workbook object
- `app` (ANY) - Excel application (optional)

**Outputs:**
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Close and save workbook
close_excel = ExcelCloseNode(
    node_id="close",
    config={
        "save": True,
        "quit_app": True
    }
)
```

---

## Word Nodes

### WordOpenNode

Open a Word document.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `visible` | BOOLEAN | `false` | Show Word window |
| `create_if_missing` | BOOLEAN | `false` | Create new document if not found |

#### Ports

**Inputs:**
- `file_path` (STRING) - Word file path (.docx, .doc)

**Outputs:**
- `document` (ANY) - Word document COM object
- `app` (ANY) - Word application COM object
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Open Word document
word_open = WordOpenNode(
    node_id="open_word",
    config={
        "file_path": "C:\\Documents\\template.docx",
        "visible": False
    }
)
```

---

### WordGetTextNode

Get text content from a Word document.

#### Ports

**Inputs:**
- `document` (ANY) - Word document object

**Outputs:**
- `text` (STRING) - Document text content
- `word_count` (INTEGER) - Number of words
- `success` (BOOLEAN) - Operation success

---

### WordReplaceTextNode

Find and replace text in a Word document.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `match_case` | BOOLEAN | `false` | Case-sensitive search |
| `replace_all` | BOOLEAN | `true` | Replace all occurrences |

#### Ports

**Inputs:**
- `document` (ANY) - Word document object
- `find_text` (STRING) - Text to find
- `replace_text` (STRING) - Replacement text

**Outputs:**
- `replacements` (INTEGER) - Number of replacements made
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Replace placeholders in template
replace_text = WordReplaceTextNode(
    node_id="replace",
    config={
        "match_case": False,
        "replace_all": True
    }
)
# Connect find_text="{{customer_name}}", replace_text="John Doe"
```

---

### WordCloseNode

Close a Word document.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `save` | BOOLEAN | `true` | Save before closing |
| `quit_app` | BOOLEAN | `true` | Quit Word application |

#### Ports

**Inputs:**
- `document` (ANY) - Word document object
- `app` (ANY) - Word application (optional)

**Outputs:**
- `success` (BOOLEAN) - Operation success

---

## Outlook Nodes

### OutlookSendEmailNode

Send an email via Outlook.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `html_body` | BOOLEAN | `false` | Body is HTML format |

#### Ports

**Inputs:**
- `to` (STRING) - Recipient email address(es)
- `subject` (STRING) - Email subject
- `body` (STRING) - Email body
- `cc` (STRING) - CC recipients (optional)
- `bcc` (STRING) - BCC recipients (optional)
- `attachments` (ANY) - List of file paths (optional)

**Outputs:**
- `success` (BOOLEAN) - Email sent successfully

#### Example

```python
# Send email with attachment
send_email = OutlookSendEmailNode(
    node_id="send_email",
    config={
        "html_body": False
    }
)
# Connect:
# to="recipient@company.com"
# subject="Daily Report - {{date}}"
# body="Please find attached the daily report."
# attachments=["C:\\Reports\\report.pdf"]
```

---

### OutlookReadEmailsNode

Read emails from Outlook inbox.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `folder` | STRING | `Inbox` | Folder name |
| `count` | INTEGER | `10` | Number of emails to read |
| `unread_only` | BOOLEAN | `false` | Only read unread emails |

#### Ports

**Outputs:**
- `emails` (ANY) - List of email dictionaries
- `count` (INTEGER) - Number of emails read
- `success` (BOOLEAN) - Operation success

#### Email Dictionary Structure

```python
{
    "subject": "Email subject",
    "sender": "sender@example.com",
    "sender_name": "Sender Name",
    "received": "2024-01-15 10:30:00",
    "body": "First 500 characters of body...",
    "unread": True,
    "has_attachments": False
}
```

#### Example

```python
# Read unread emails
read_emails = OutlookReadEmailsNode(
    node_id="read_inbox",
    config={
        "folder": "Inbox",
        "count": 20,
        "unread_only": True
    }
)
```

---

### OutlookGetInboxCountNode

Get the count of emails in Outlook inbox.

#### Ports

**Outputs:**
- `total_count` (INTEGER) - Total email count
- `unread_count` (INTEGER) - Unread email count
- `success` (BOOLEAN) - Operation success

---

## Complete Examples

### Excel Data Processing Workflow

```python
# 1. Open source Excel file
open_source = ExcelOpenNode(
    node_id="open_source",
    config={
        "file_path": "C:\\Data\\input.xlsx",
        "read_only": True
    }
)

# 2. Read data range
read_data = ExcelGetRangeNode(
    node_id="read_data",
    config={
        "sheet": "Data",
        "range": "A1:E100"
    }
)

# 3. Process data (via other nodes)
# ... data transformation ...

# 4. Open output file
open_output = ExcelOpenNode(
    node_id="open_output",
    config={
        "file_path": "C:\\Output\\results.xlsx",
        "create_if_missing": True
    }
)

# 5. Write results
write_results = ExcelWriteCellNode(
    node_id="write_results",
    config={
        "sheet": "Sheet1",
        "cell": "A1",
        "value": "{{processed_data}}"
    }
)

# 6. Close both files
close_source = ExcelCloseNode(
    node_id="close_source",
    config={"save": False, "quit_app": False}
)

close_output = ExcelCloseNode(
    node_id="close_output",
    config={"save": True, "quit_app": True}
)
```

### Word Template Processing

```python
# 1. Open template
open_template = WordOpenNode(
    node_id="open_template",
    config={
        "file_path": "C:\\Templates\\contract.docx"
    }
)

# 2. Replace placeholders
replace_name = WordReplaceTextNode(node_id="replace_name")
# find_text="{{customer_name}}", replace_text="Acme Corp"

replace_date = WordReplaceTextNode(node_id="replace_date")
# find_text="{{contract_date}}", replace_text="2024-01-15"

replace_amount = WordReplaceTextNode(node_id="replace_amount")
# find_text="{{contract_amount}}", replace_text="$10,000"

# 3. Save and close
close_doc = WordCloseNode(
    node_id="close",
    config={"save": True, "quit_app": True}
)
```

### Email Processing Workflow

```python
# 1. Check inbox
get_count = OutlookGetInboxCountNode(node_id="check_inbox")

# 2. Read unread emails
read_emails = OutlookReadEmailsNode(
    node_id="read_emails",
    config={
        "unread_only": True,
        "count": 50
    }
)

# 3. Process each email (via loop node)
# ... extract data, file attachments, etc. ...

# 4. Send confirmation
send_response = OutlookSendEmailNode(
    node_id="send_response",
    config={"html_body": False}
)
```

---

## Best Practices

### Resource Management

Always close Office applications when done:

```python
# Use try/finally pattern or ensure close nodes run
# even if errors occur in the workflow
```

### Visibility

- Set `visible: false` for background automation
- Set `visible: true` for debugging

### Protected View

Excel may open files in Protected View if they're from untrusted locations:
- Use `read_only: true` to bypass Protected View
- Or add the source folder to Excel's trusted locations

### Error Handling

```python
# All nodes output success
# Check before continuing workflow
if outputs["success"]:
    # Continue processing
else:
    # Handle error
```

### Performance

- Minimize Excel interactions by reading ranges instead of individual cells
- Batch write operations when possible
- Close applications when not needed

### COM Object Cleanup

COM objects should be properly released. The close nodes handle this, but if an error occurs:
- The Office application may remain open
- Use Task Manager to close orphaned Office processes

## Comparison with Other Approaches

| Approach | Pros | Cons |
|----------|------|------|
| **COM Automation (these nodes)** | Full Office features, exact compatibility | Windows-only, requires Office installed |
| **openpyxl/python-docx** | Cross-platform, no Office needed | Limited features, format differences |
| **Google Sheets/Docs** | Cloud-based, cross-platform | Requires internet, API limits |

## Related Documentation

- [File Operations](file-operations.md) - CSV/JSON for Office-free alternatives
- [Google Workspace](google.md) - Cloud-based alternatives
- [Email Nodes](email.md) - SMTP/IMAP alternatives to Outlook
