# MathOperationNode

Node that performs math operations.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.math_nodes`
**File:** `src\casare_rpa\nodes\math_nodes.py:61`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `a` | FLOAT | No |  |
| `b` | FLOAT | No |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | FLOAT |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `operation` | CHOICE | `add` | No | Mathematical operation to perform Choices: add, subtract, multiply, divide, floor_divide, ... (21 total) |
| `round_digits` | INTEGER | `-` | No | Number of decimal places to round result (optional) (min: 0) |

## Inheritance

Extends: `BaseNode`
