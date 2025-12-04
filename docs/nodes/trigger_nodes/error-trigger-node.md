# ErrorTriggerNode

Error trigger node that fires when errors occur.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.error_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\error_trigger_node.py:61`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `error` | DICT | Error Object |
| `error_type` | STRING | Error Type |
| `error_message` | STRING | Error Message |
| `workflow_id` | STRING | Workflow ID |
| `node_id` | STRING | Node ID |
| `stack_trace` | STRING | Stack Trace |
| `timestamp` | STRING | Timestamp |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `error_types` | STRING | `*` | No | Comma-separated error types to catch (* for all) |
| `workflow_filter` | STRING | `` | No | Comma-separated workflow IDs to monitor (empty = all) |
| `severity` | CHOICE | `all` | No | Minimum error severity to trigger Choices: all, critical, error, warning |
| `error_pattern` | STRING | `` | No | Regex pattern to match error messages |
| `include_warnings` | BOOLEAN | `False` | No | Also trigger on warning-level events |

## Inheritance

Extends: `BaseTriggerNode`
