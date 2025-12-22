# PDF and XML Nodes

PDF and XML nodes provide document processing capabilities for extracting text, parsing structured data, and converting between formats.

## Dependencies

| Node Category | Required Package |
|---------------|------------------|
| PDF nodes | `PyPDF2` |
| PDF to Images | `pdf2image` + Poppler |
| XML nodes | `defusedxml` (included) |

Install PDF support:
```bash
pip install PyPDF2 pdf2image
```

> **Note:** `pdf2image` requires Poppler binaries installed on the system.

---

## PDF Nodes

### ReadPDFTextNode

Extract text content from a PDF file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `page_separator` | STRING | `\n\n` | Separator between page texts |
| `password` | STRING | `""` | Password for encrypted PDFs |
| `extract_tables` | BOOLEAN | `false` | Attempt table extraction (experimental) |
| `preserve_layout` | BOOLEAN | `false` | Preserve text layout (experimental) |

#### Ports

**Inputs:**
- `file_path` (STRING) - Path to PDF file
- `start_page` (INTEGER) - Start page (1-indexed)
- `end_page` (INTEGER) - End page (default: all)
- `password` (STRING) - Password override

**Outputs:**
- `text` (STRING) - Extracted text
- `page_count` (INTEGER) - Total pages
- `pages` (LIST) - Text per page as list
- `is_encrypted` (BOOLEAN) - Whether PDF is encrypted
- `success` (BOOLEAN) - Extraction success

#### Example

```python
# Extract text from PDF
read_pdf = ReadPDFTextNode(
    node_id="extract_text",
    config={
        "page_separator": "\n---PAGE---\n",
        "password": ""  # Leave empty for unencrypted PDFs
    }
)

# Extract specific pages
read_pages = ReadPDFTextNode(
    node_id="extract_pages",
    config={}
)
# Connect start_page=1, end_page=5 to input ports
```

---

### GetPDFInfoNode

Get metadata and information from a PDF file.

#### Ports

**Inputs:**
- `file_path` (STRING) - Path to PDF file

**Outputs:**
- `page_count` (INTEGER) - Number of pages
- `title` (STRING) - Document title
- `author` (STRING) - Document author
- `subject` (STRING) - Document subject
- `creator` (STRING) - Creator application
- `producer` (STRING) - PDF producer
- `creation_date` (STRING) - Creation date
- `modification_date` (STRING) - Modification date
- `is_encrypted` (BOOLEAN) - Whether encrypted
- `success` (BOOLEAN) - Operation success

#### Example

```python
# Get PDF metadata
pdf_info = GetPDFInfoNode(
    node_id="pdf_info",
    config={}
)
# Connect file_path input
```

---

### MergePDFsNode

Merge multiple PDF files into one.

#### Ports

**Inputs:**
- `input_files` (LIST) - List of PDF file paths to merge
- `output_path` (STRING) - Output file path

**Outputs:**
- `output_path` (STRING) - Path to merged PDF
- `attachment_file` (LIST) - Output path as list
- `page_count` (INTEGER) - Total pages in merged PDF
- `success` (BOOLEAN) - Merge success

#### Example

```python
# Merge multiple PDFs
merge_pdfs = MergePDFsNode(
    node_id="merge",
    config={}
)
# Connect input_files=["file1.pdf", "file2.pdf", "file3.pdf"]
# Connect output_path="C:\\Output\\merged.pdf"
```

---

### SplitPDFNode

Split a PDF into separate files, one per page.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `filename_pattern` | STRING | `page_{n}.pdf` | Output filename pattern (use `{n}` for page number) |

#### Ports

**Inputs:**
- `input_file` (STRING) - Path to PDF file
- `output_dir` (STRING) - Output directory

**Outputs:**
- `output_files` (LIST) - List of created file paths
- `page_count` (INTEGER) - Number of pages split
- `success` (BOOLEAN) - Split success

#### Example

```python
# Split PDF into pages
split_pdf = SplitPDFNode(
    node_id="split",
    config={
        "filename_pattern": "document_page_{n}.pdf"
    }
)
# Produces: document_page_1.pdf, document_page_2.pdf, etc.
```

---

### ExtractPDFPagesNode

Extract specific pages from a PDF.

#### Ports

**Inputs:**
- `input_file` (STRING) - Path to PDF file
- `output_path` (STRING) - Output file path
- `pages` (LIST) - Page numbers to extract (1-indexed)

**Outputs:**
- `output_path` (STRING) - Path to output PDF
- `attachment_file` (LIST) - Output path as list
- `page_count` (INTEGER) - Pages extracted
- `success` (BOOLEAN) - Extraction success

#### Example

```python
# Extract pages 1, 3, and 5
extract_pages = ExtractPDFPagesNode(
    node_id="extract",
    config={}
)
# Connect pages=[1, 3, 5]
```

---

### PDFToImagesNode

Convert PDF pages to images.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `dpi` | INTEGER | `200` | Resolution (72-600 DPI) |
| `format` | CHOICE | `png` | Image format: png, jpg, jpeg, bmp, tiff |

#### Ports

**Inputs:**
- `input_file` (STRING) - Path to PDF file
- `output_dir` (STRING) - Output directory
- `start_page` (INTEGER) - Start page (optional)
- `end_page` (INTEGER) - End page (optional)

**Outputs:**
- `output_files` (LIST) - List of image file paths
- `page_count` (INTEGER) - Images created
- `success` (BOOLEAN) - Conversion success

#### Example

```python
# Convert PDF to high-resolution PNG images
pdf_to_images = PDFToImagesNode(
    node_id="convert",
    config={
        "dpi": 300,
        "format": "png"
    }
)
```

---

## XML Nodes

> **Security:** All XML parsing uses `defusedxml` to prevent XXE (XML External Entity) attacks and other XML-based vulnerabilities.

### ParseXMLNode

Parse XML from a string.

#### Ports

**Inputs:**
- `xml_string` (STRING) - XML string to parse

**Outputs:**
- `root_tag` (STRING) - Root element tag name
- `root_text` (STRING) - Root element text content
- `child_count` (INTEGER) - Number of child elements
- `success` (BOOLEAN) - Parse success

#### Example

```python
# Parse XML string
parse_xml = ParseXMLNode(
    node_id="parse",
    config={}
)
# Connect xml_string='<root><item>value</item></root>'
```

---

### ReadXMLFileNode

Read and parse an XML file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `encoding` | STRING | `utf-8` | File encoding |

#### Ports

**Inputs:**
- `file_path` (STRING) - Path to XML file

**Outputs:**
- `root_tag` (STRING) - Root element tag name
- `xml_string` (STRING) - Raw XML content
- `success` (BOOLEAN) - Read success

---

### WriteXMLFileNode

Write XML to a file.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `encoding` | STRING | `utf-8` | File encoding |
| `pretty_print` | BOOLEAN | `true` | Format with indentation |
| `xml_declaration` | BOOLEAN | `true` | Include `<?xml ...?>` declaration |

#### Ports

**Inputs:**
- `file_path` (STRING) - Path to write to
- `xml_string` (STRING) - XML content

**Outputs:**
- `file_path` (STRING) - Written file path
- `success` (BOOLEAN) - Write success

---

### XPathQueryNode

Query XML using XPath expressions.

#### Ports

**Inputs:**
- `xml_string` (STRING) - XML to query (or uses context from ParseXMLNode)
- `xpath` (STRING) - XPath expression

**Outputs:**
- `results` (LIST) - Matching elements as dicts (tag, text, attrib)
- `count` (INTEGER) - Number of matches
- `first_text` (STRING) - Text of first match
- `success` (BOOLEAN) - Query success

#### XPath Examples

| Expression | Description |
|------------|-------------|
| `.//item` | All `item` elements anywhere |
| `./item` | Direct child `item` elements |
| `.//item[@id]` | Elements with `id` attribute |
| `.//item[@id='123']` | Element with specific id |
| `.//item[1]` | First item element |
| `.//item/name` | `name` children of `item` |

#### Example

```python
# Query XML for specific elements
xpath_query = XPathQueryNode(
    node_id="query",
    config={}
)
# Connect xpath='.//product[@category="electronics"]'
```

---

### GetXMLElementNode

Get XML element by tag name.

#### Ports

**Inputs:**
- `xml_string` (STRING) - XML to search
- `tag_name` (STRING) - Tag name to find
- `index` (INTEGER) - Index if multiple elements (default: 0)

**Outputs:**
- `tag` (STRING) - Element tag name
- `text` (STRING) - Element text content
- `attributes` (DICT) - Element attributes
- `child_count` (INTEGER) - Number of children
- `found` (BOOLEAN) - Whether element was found

---

### GetXMLAttributeNode

Get an attribute value from an XML element.

#### Ports

**Inputs:**
- `xml_string` (STRING) - XML to search
- `xpath` (STRING) - XPath to element
- `attribute_name` (STRING) - Attribute name

**Outputs:**
- `value` (STRING) - Attribute value
- `found` (BOOLEAN) - Whether attribute was found

---

### XMLToJsonNode

Convert XML to JSON.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `include_attributes` | BOOLEAN | `true` | Include `@attributes` in output |
| `text_key` | STRING | `#text` | Key name for text content |

#### Ports

**Inputs:**
- `xml_string` (STRING) - XML to convert

**Outputs:**
- `json_data` (DICT) - Converted JSON data
- `json_string` (STRING) - JSON as string
- `success` (BOOLEAN) - Conversion success

#### Example

Input XML:
```xml
<book id="123">
  <title>Python Guide</title>
  <author>John Doe</author>
</book>
```

Output JSON:
```json
{
  "book": {
    "@attributes": {"id": "123"},
    "title": "Python Guide",
    "author": "John Doe"
  }
}
```

---

### JsonToXMLNode

Convert JSON to XML.

#### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `root_tag` | STRING | `root` | Root element tag name |
| `pretty_print` | BOOLEAN | `true` | Format output |

#### Ports

**Inputs:**
- `json_data` (ANY) - JSON data (dict or string)

**Outputs:**
- `xml_string` (STRING) - Converted XML
- `success` (BOOLEAN) - Conversion success

---

## Complete Examples

### PDF Processing Workflow

```python
# 1. Get PDF info
pdf_info = GetPDFInfoNode(node_id="info")

# 2. Extract text from first 5 pages
read_pdf = ReadPDFTextNode(
    node_id="read",
    config={"page_separator": "\n\n"}
)

# 3. If PDF has more than 10 pages, split it
split_pdf = SplitPDFNode(
    node_id="split",
    config={"filename_pattern": "chapter_{n}.pdf"}
)

# 4. Convert specific pages to images
pdf_to_img = PDFToImagesNode(
    node_id="images",
    config={"dpi": 300, "format": "png"}
)
```

### XML Data Processing Workflow

```python
# 1. Read XML file
read_xml = ReadXMLFileNode(
    node_id="read",
    config={"encoding": "utf-8"}
)

# 2. Query for specific data
query_products = XPathQueryNode(
    node_id="query",
    config={}
)
# xpath='.//product[@active="true"]'

# 3. Convert to JSON for API
xml_to_json = XMLToJsonNode(
    node_id="convert",
    config={"include_attributes": True}
)
```

### PDF Report Generation

```python
# 1. Generate individual PDFs per section
# ... (create section PDFs) ...

# 2. Merge all sections
merge = MergePDFsNode(node_id="merge")
# input_files=[
#   "C:\\Reports\\cover.pdf",
#   "C:\\Reports\\chapter1.pdf",
#   "C:\\Reports\\chapter2.pdf",
#   "C:\\Reports\\appendix.pdf"
# ]
# output_path="C:\\Reports\\final_report.pdf"
```

---

## Best Practices

### PDF Operations

- Check `is_encrypted` before attempting extraction
- Use appropriate `dpi` for PDFToImages (200 for screen, 300+ for print)
- Handle large PDFs with page ranges to manage memory

### XML Security

- Always use these nodes (which use defusedxml) instead of raw XML parsing
- Validate XPath expressions before execution
- Be cautious with XML from untrusted sources

### Error Handling

```python
# All nodes output success and handle errors
# Check success before using other outputs
if outputs["success"]:
    text = outputs["text"]
else:
    # Handle error
    pass
```

## Related Documentation

- [File Operations](file-operations.md) - File I/O basics
- [Data Operations](data-operations.md) - Process extracted data
