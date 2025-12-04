# WorkflowCallTriggerNode

Workflow call trigger node for sub-workflow invocation.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.workflow_call_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\workflow_call_trigger_node.py:61`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `params` | DICT | Input Parameters |
| `caller_workflow_id` | STRING | Caller Workflow |
| `caller_node_id` | STRING | Caller Node |
| `call_id` | STRING | Call ID |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `call_alias` | STRING | `-` | Yes | Unique alias to call this workflow |
| `input_schema` | JSON | `{}` | No | JSON schema for expected input parameters |
| `output_schema` | JSON | `{}` | No | JSON schema for output parameters |
| `wait_for_completion` | BOOLEAN | `True` | No | Caller waits for this workflow to complete |
| `timeout_seconds` | INTEGER | `300` | No | Maximum time to wait for completion |

## Inheritance

Extends: `BaseTriggerNode`
