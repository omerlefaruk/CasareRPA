# ComparisonNode

Node that compares two values.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.math_nodes`
**File:** `src\casare_rpa\nodes\math_nodes.py:171`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC | Yes | Execution input |
| `a` | ANY | No |  |
| `b` | ANY | No |  |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `result` | BOOLEAN |  |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `operator` | CHOICE | `==` | No | Comparison operator to use Choices: ==, equals (==), !=, not equals (!=), >, ... (12 total) |

## Inheritance

Extends: `BaseNode`
