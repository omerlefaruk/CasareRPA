# Data Types

Port data types used in CasareRPA nodes.

## Core Types

| Type | Description | Example |
|------|-------------|---------|
| STRING | Text string | "hello world" |
| TEXT | Multi-line text | "line1\nline2" |
| INTEGER | Whole number | 42, -10 |
| FLOAT | Decimal number | 3.14, -0.5 |
| BOOLEAN | True/False | true, false |
| ANY | Any type | - |

## Complex Types

| Type | Description | Example |
|------|-------------|---------|
| ARRAY | List of items | [1, 2, 3] |
| OBJECT | Dictionary | {"key": "value"} |
| JSON | JSON data | {"data": [...]} |

## Specialized Types

| Type | Description | Used By |
|------|-------------|---------|
| PAGE | Playwright page | Browser nodes |
| BROWSER | Browser instance | Browser nodes |
| ELEMENT | Desktop element | Desktop nodes |
| FILE | File path | File nodes |
| DATE | Date value | DateTime nodes |
| TIME | Time value | DateTime nodes |
| DATETIME | Date and time | DateTime nodes |

## Execution Types

| Type | Description |
|------|-------------|
| EXEC | Execution flow (no data) |

## Type Coercion

Automatic conversions:

| From | To | Example |
|------|-----|---------|
| INTEGER | FLOAT | 42 → 42.0 |
| INTEGER | STRING | 42 → "42" |
| BOOLEAN | STRING | true → "true" |
| ARRAY | STRING | [1,2] → "[1, 2]" |
