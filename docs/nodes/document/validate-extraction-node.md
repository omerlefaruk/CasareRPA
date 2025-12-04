# ValidateExtractionNode

Node that validates extracted document data.

`:material-sync: Async`


**Module:** `casare_rpa.nodes.document.document_nodes`
**File:** `src\casare_rpa\nodes\document\document_nodes.py:494`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `extraction` | INPUT | No | DataType.DICT |
| `required_fields` | INPUT | No | DataType.LIST |
| `confidence_threshold` | INPUT | No | DataType.FLOAT |
| `validation_rules` | INPUT | No | DataType.DICT |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `is_valid` | OUTPUT | DataType.BOOLEAN |
| `needs_review` | OUTPUT | DataType.BOOLEAN |
| `confidence_score` | OUTPUT | DataType.FLOAT |
| `validation_errors` | OUTPUT | DataType.LIST |
| `field_status` | OUTPUT | DataType.DICT |
| `success` | OUTPUT | DataType.BOOLEAN |
| `error` | OUTPUT | DataType.STRING |

## Inheritance

Extends: `BaseNode`
