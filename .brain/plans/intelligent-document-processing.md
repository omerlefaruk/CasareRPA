# Intelligent Document Processing (IDP) Plan

**Status**: COMPLETE
**Created**: 2025-12-01
**Priority**: HIGHEST (builds on LLM integration)

## Overview

Implement document processing nodes that leverage LLM capabilities for intelligent extraction, classification, and validation of business documents (invoices, receipts, forms, contracts).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                      │
├─────────────────────────────────────────────────────────────┤
│  DocumentAIManager                                           │
│  - Coordinates LLM + OCR + Vision                            │
│  - Document preprocessing (image enhancement)                │
│  - Confidence scoring                                        │
│  - Extraction validation                                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Node Layer                              │
├─────────────────────────────────────────────────────────────┤
│  DocumentBaseNode (abstract)                                 │
│  ├── ClassifyDocumentNode    - Document type classification  │
│  ├── ExtractInvoiceNode      - Invoice field extraction      │
│  ├── ExtractFormNode         - Form field extraction         │
│  ├── ExtractTableNode        - Table data extraction         │
│  └── ValidateExtractionNode  - Confidence validation         │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Tasks

### Phase 1: Infrastructure - COMPLETE
- [x] Create `src/casare_rpa/infrastructure/resources/document_ai_manager.py`
  - Document preprocessing
  - LLM coordination
  - Confidence scoring

### Phase 2: Base Node - COMPLETE
- [x] Create `src/casare_rpa/nodes/document/__init__.py`
- [x] Create `src/casare_rpa/nodes/document/document_nodes.py`
  - Abstract base with shared logic
  - Document type detection
  - Preprocessing pipeline

### Phase 3: Core Nodes - COMPLETE
- [x] `ClassifyDocumentNode` - Document type (invoice, receipt, form, contract)
- [x] `ExtractInvoiceNode` - Invoice fields (vendor, amount, date, line items)
- [x] `ExtractFormNode` - Generic form field extraction
- [x] `ExtractTableNode` - Table structure extraction
- [x] `ValidateExtractionNode` - Confidence validation and human review flagging

### Phase 4: Tests - COMPLETE
- [x] Unit tests with mocked LLM responses (45 tests)
- [x] Test fixtures for sample documents

## Node Specifications

### ClassifyDocumentNode
```python
Inputs:
  - document: STRING | BYTES (file path or base64)
  - categories: LIST (default: ["invoice", "receipt", "form", "contract", "other"])

Outputs:
  - document_type: STRING
  - confidence: FLOAT
  - all_scores: DICT
  - success: BOOLEAN
  - error: STRING
```

### ExtractInvoiceNode
```python
Inputs:
  - document: STRING | BYTES
  - custom_fields: LIST (optional, additional fields to extract)

Outputs:
  - vendor_name: STRING
  - invoice_number: STRING
  - invoice_date: STRING
  - due_date: STRING
  - total_amount: FLOAT
  - currency: STRING
  - line_items: LIST[DICT]
  - tax_amount: FLOAT
  - subtotal: FLOAT
  - raw_extraction: DICT
  - confidence: FLOAT
  - success: BOOLEAN
  - error: STRING
```

### ExtractFormNode
```python
Inputs:
  - document: STRING | BYTES
  - field_schema: DICT (expected fields and types)
  - fuzzy_match: BOOLEAN (default: True)

Outputs:
  - extracted_fields: DICT
  - unmatched_fields: LIST
  - confidence: FLOAT
  - success: BOOLEAN
  - error: STRING
```

### ExtractTableNode
```python
Inputs:
  - document: STRING | BYTES
  - table_hint: STRING (optional, description of expected table)
  - output_format: STRING (json, csv, list)

Outputs:
  - tables: LIST[DICT]
  - row_count: INTEGER
  - column_count: INTEGER
  - confidence: FLOAT
  - success: BOOLEAN
  - error: STRING
```

### ValidateExtractionNode
```python
Inputs:
  - extraction: DICT
  - confidence_threshold: FLOAT (default: 0.8)
  - required_fields: LIST
  - validation_rules: DICT (optional)

Outputs:
  - is_valid: BOOLEAN
  - needs_review: BOOLEAN
  - validation_errors: LIST
  - confidence_score: FLOAT
  - success: BOOLEAN
```

## Leverages Existing

- `LLMResourceManager` - API calls to GPT-4V/Claude for vision
- `LLMExtractDataNode` - Structured JSON extraction
- `LLMClassifyNode` - Document classification
- `screenshot_ocr_nodes.py` - OCR fallback

## Dependencies

Already available via LiteLLM:
- GPT-4V (vision) - OpenAI
- Claude 3 Vision - Anthropic
- Ollama with LLaVA - Local

## Unresolved Questions

1. Should we support PDF directly or require image conversion first?
2. Multi-page document handling - concatenate or process separately?
3. Should extracted data be validated against business rules (e.g., total = sum of line items)?
