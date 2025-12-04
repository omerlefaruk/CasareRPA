# ParallelForEachNode

Parallel ForEach node that processes list items concurrently.

`:material-sync: Async` `:material-play: Executable`


**Module:** `casare_rpa.nodes.parallel_nodes`
**File:** `src\casare_rpa\nodes\parallel_nodes.py:266`


## Input Ports

| Port | Type | Required | Description |
|------|------|----------|-------------|
| `exec_in` | EXEC_INPUT | Yes |  |
| `items` | INPUT | No | DataType.LIST |

## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `exec_out` | EXEC | Execution output |
| `body` | EXEC_OUTPUT |  |
| `completed` | EXEC_OUTPUT |  |
| `current_item` | OUTPUT | DataType.ANY |
| `current_index` | OUTPUT | DataType.INTEGER |
| `results` | OUTPUT | DataType.LIST |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `batch_size` | INTEGER | `5` | No | Number of items to process concurrently (1-50) (min: 1, max: 50) |
| `fail_fast` | BOOLEAN | `False` | No | If True, stop processing when one item fails. If False, continue with remaining items. |
| `timeout_per_item` | INTEGER | `60` | No | Maximum time in seconds for each item's processing (min: 1) |

## Inheritance

Extends: `BaseNode`
