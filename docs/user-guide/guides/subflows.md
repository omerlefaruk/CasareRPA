# Subflows Guide

Subflows are reusable workflow components that encapsulate a group of nodes into a single, callable unit. This guide explains how to create, configure, and use subflows to build modular, maintainable automations.

## Table of Contents

- [What is a Subflow?](#what-is-a-subflow)
- [Creating Reusable Workflow Blocks](#creating-reusable-workflow-blocks)
- [Calling Subflows](#calling-subflows)
- [Passing Parameters](#passing-parameters)
- [Returning Values](#returning-values)
- [Subflow vs Main Workflow](#subflow-vs-main-workflow)
- [Best Practices for Modularity](#best-practices-for-modularity)

---

## What is a Subflow?

A **subflow** is a reusable workflow fragment that:

- Encapsulates multiple nodes into a single logical unit
- Accepts input parameters
- Returns output values
- Can be called from any workflow or other subflow

Think of subflows as functions in programming - they promote code reuse, improve organization, and make complex automations easier to maintain.

### Benefits of Subflows

| Benefit | Description |
|---------|-------------|
| **Reusability** | Use the same logic in multiple workflows |
| **Maintainability** | Update logic in one place, changes apply everywhere |
| **Organization** | Break complex workflows into manageable pieces |
| **Testability** | Test subflows independently |
| **Collaboration** | Team members can work on different subflows |

---

## Creating Reusable Workflow Blocks

### Method 1: Create from Selection

1. Select the nodes you want to convert to a subflow
2. Right-click and choose **Create Subflow from Selection**
3. Configure the subflow properties:
   - **Name**: Descriptive name for the subflow
   - **Description**: What the subflow does
   - **Inputs**: Define input parameters
   - **Outputs**: Define return values

### Method 2: Create from Menu

1. Go to **File > New Subflow**
2. Build your subflow logic on the canvas
3. Add **Subflow Input** nodes for parameters
4. Add **Subflow Output** nodes for return values
5. Save the subflow

### Subflow File Structure

Subflows are saved as JSON files in the `workflows/subflows/` directory:

```
workflows/
  subflows/
    login_flow.json
    data_extraction.json
    error_reporter.json
```

### Example: Login Subflow

```json
{
  "id": "subflow_login_123",
  "name": "Website Login",
  "description": "Logs into a website with provided credentials",
  "inputs": [
    {"name": "username", "data_type": "STRING", "required": true},
    {"name": "password", "data_type": "STRING", "required": true},
    {"name": "login_url", "data_type": "STRING", "required": true}
  ],
  "outputs": [
    {"name": "success", "data_type": "BOOLEAN"},
    {"name": "session_token", "data_type": "STRING"}
  ],
  "nodes": {
    // Node definitions...
  },
  "connections": [
    // Connection definitions...
  ]
}
```

---

## Calling Subflows

### Using the Subflow Node

The **SubflowNode** executes a subflow within your main workflow.

1. Drag a **Subflow** node onto the canvas
2. Configure the subflow reference:
   - **Subflow ID**: Unique identifier of the subflow
   - **Subflow Path**: File path to the subflow definition

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `subflow_id` | String | Unique ID of the subflow to execute |
| `subflow_path` | File Path | Path to subflow definition file |

### Ports

| Port | Direction | Description |
|------|-----------|-------------|
| `exec_in` | Input | Execution input |
| `exec_out` | Output | Continues after subflow completes |
| `error` | Output | Routes here if subflow fails |
| *Dynamic inputs* | Input | One port per subflow input parameter |
| *Dynamic outputs* | Output | One port per subflow output value |

### Example Usage

```
[Get Credentials] --> [Login Subflow] --> [Dashboard Action]
                           |
                      (error) --> [Handle Login Failure]
```

---

## Passing Parameters

### Input Port Mapping

When you configure a SubflowNode, input ports are automatically created based on the subflow's input definitions:

```python
# Subflow defines inputs:
# - username (STRING)
# - password (STRING)
# - login_url (STRING)

# SubflowNode creates matching input ports:
# - username (connects to String/Variable node)
# - password (connects to Credential node)
# - login_url (connects to Constant node)
```

### Connecting Input Values

1. Create nodes that produce the input values:
   - Use **Get Variable** nodes for dynamic values
   - Use **Constant** nodes for fixed values
   - Use **Credential** nodes for sensitive data

2. Connect outputs to the subflow's input ports

### Example: Parameterized Login

```
[Variable: username] -----+
                          |
[Get Credential: pass] ---+--> [Login Subflow] --> ...
                          |
[Constant: "https://..."] +
```

### Using Context Variables

Subflows can access context variables from the parent workflow:

```python
# Parent workflow sets:
context.set_variable("environment", "production")

# Subflow can access:
env = context.get_variable("environment")  # "production"
```

---

## Returning Values

### Output Port Mapping

Subflows can return values through their output definitions:

```python
# Subflow defines outputs:
# - success (BOOLEAN)
# - extracted_data (LIST)
# - error_message (STRING)

# SubflowNode creates matching output ports
```

### Connecting Output Values

1. Inside the subflow, set values on Subflow Output nodes
2. In the parent workflow, connect subflow outputs to subsequent nodes

### Example: Using Subflow Results

```
[Data Extraction Subflow] --extracted_data--> [Process Data]
                          |
                          +--success--> [If Node]
                                           |
                                    True ---> [Save Results]
                                    False --> [Retry Logic]
```

### Error Handling

If a subflow encounters an error:

1. Execution routes to the `error` output port
2. Error details are available in the execution context
3. Parent workflow can implement recovery logic

```
[Subflow] --exec_out--> [Continue Normal Flow]
          |
          +--error--> [Log Error] --> [Retry or Abort]
```

---

## Subflow vs Main Workflow

Understanding when to use subflows vs. keeping logic in the main workflow:

### Use a Subflow When

| Scenario | Example |
|----------|---------|
| Logic is reused in multiple places | Login flow, data validation |
| Logic can be tested independently | API request handling |
| Logic represents a distinct operation | PDF generation, email sending |
| Team members work on different parts | Separate by domain |
| Logic may change independently | Third-party integrations |

### Keep in Main Workflow When

| Scenario | Example |
|----------|---------|
| Logic is specific to one workflow | Custom business rules |
| Simple, linear operations | Sequential clicks |
| Tight integration with surrounding context | Complex state management |
| Quick prototyping | Testing ideas |

### Comparison

| Aspect | Main Workflow | Subflow |
|--------|---------------|---------|
| Scope | Single workflow | Reusable across workflows |
| Variables | Direct access | Passed via parameters |
| Testing | Test entire workflow | Test in isolation |
| Maintenance | Update in place | Update affects all callers |
| Complexity | Can grow large | Enforces modular design |

---

## Best Practices for Modularity

### 1. Single Responsibility

Each subflow should do one thing well:

```python
# Good: Focused subflows
"Login to Website"
"Extract Table Data"
"Send Notification Email"

# Bad: Mixed responsibilities
"Login and Extract Data and Send Email"
```

### 2. Clear Naming

Use descriptive names that indicate what the subflow does:

```python
# Good: Action-oriented names
"Process_Invoice_PDF"
"Validate_User_Credentials"
"Export_Report_To_Excel"

# Bad: Vague names
"Subflow1"
"Helper"
"DoStuff"
```

### 3. Document Inputs and Outputs

Provide clear descriptions for all parameters:

```json
{
  "inputs": [
    {
      "name": "invoice_path",
      "data_type": "STRING",
      "required": true,
      "description": "Full path to the PDF invoice file"
    },
    {
      "name": "output_format",
      "data_type": "STRING",
      "required": false,
      "default": "json",
      "description": "Output format: json, csv, or xml"
    }
  ]
}
```

### 4. Handle Errors Gracefully

Return meaningful error information:

```python
# Include error output in subflow
outputs = [
    {"name": "success", "data_type": "BOOLEAN"},
    {"name": "error_code", "data_type": "STRING"},
    {"name": "error_message", "data_type": "STRING"}
]
```

### 5. Version Your Subflows

When making breaking changes, consider:

- Creating a new version (e.g., `login_v2.json`)
- Adding optional parameters with defaults
- Deprecating old subflows gradually

### 6. Avoid Deep Nesting

Limit subflow call depth to prevent complexity:

```
# Good: 2-3 levels deep
Main Workflow -> Login Subflow -> Credential Lookup

# Bad: Too many levels
Main -> Level1 -> Level2 -> Level3 -> Level4
```

### 7. Use Promoted Parameters

Promote internal node parameters to the subflow level for configuration:

```json
{
  "parameters": [
    {
      "name": "timeout_seconds",
      "source_node": "wait_node_1",
      "source_property": "timeout",
      "default_value": 30
    }
  ]
}
```

This allows callers to customize behavior without modifying the subflow.

### 8. Share Browser Context

When working with browser automation, subflows share the browser context from the parent:

```python
# Parent workflow:
[Launch Browser] --> [Navigate to Login] --> [Login Subflow]

# Login Subflow:
# Uses the same browser page - no need to launch again
[Fill Username] --> [Fill Password] --> [Click Login]
```

---

## Example: Complete Login Subflow

### Subflow Definition

```json
{
  "id": "subflow_login_website",
  "name": "Website Login",
  "description": "Performs secure login to a website with retry logic",
  "version": "1.0.0",
  "inputs": [
    {
      "name": "credential_name",
      "data_type": "STRING",
      "required": true,
      "description": "Name of credential in vault"
    },
    {
      "name": "login_url",
      "data_type": "STRING",
      "required": true,
      "description": "URL of the login page"
    },
    {
      "name": "max_retries",
      "data_type": "INTEGER",
      "required": false,
      "default": 3,
      "description": "Maximum retry attempts"
    }
  ],
  "outputs": [
    {
      "name": "success",
      "data_type": "BOOLEAN",
      "description": "True if login succeeded"
    },
    {
      "name": "redirect_url",
      "data_type": "STRING",
      "description": "URL after successful login"
    }
  ]
}
```

### Usage in Parent Workflow

```
[Set Login URL] --> [Login Subflow] --success--> [Continue to Dashboard]
                          |
                     (error) --> [Show Error Dialog]
                          |
                     success=false --> [Retry or Exit]
```

---

## Related Guides

- [Control Flow Patterns](./control-flow.md) - Use loops and conditions with subflows
- [Error Handling](./error-handling.md) - Handle subflow errors
- [Best Practices](./best-practices.md) - General workflow design tips
