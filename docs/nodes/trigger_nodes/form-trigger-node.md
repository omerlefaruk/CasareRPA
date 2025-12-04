# FormTriggerNode

Form trigger node that fires when a form is submitted.

`:material-bell: Trigger`


**Module:** `casare_rpa.nodes.trigger_nodes.form_trigger_node`
**File:** `src\casare_rpa\nodes\trigger_nodes\form_trigger_node.py:62`


## Output Ports

| Port | Type | Description |
|------|------|-------------|
| `form_data` | DICT | Form Data |
| `submitted_at` | STRING | Submitted At |
| `user_id` | STRING | User ID |
| `ip_address` | STRING | IP Address |

## Configuration Properties

| Property | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `form_title` | STRING | `Submit Data` | No | Form Title |
| `form_description` | STRING | `` | No | Form Description |
| `form_fields` | JSON | `[{"name": "data",...` | No | JSON array of field definitions |
| `submit_button_text` | STRING | `Submit` | No | Submit Button Text |
| `success_message` | STRING | `Form submitted su...` | No | Success Message |
| `require_auth` | BOOLEAN | `False` | No | Require user to be logged in |

## Inheritance

Extends: `BaseTriggerNode`
