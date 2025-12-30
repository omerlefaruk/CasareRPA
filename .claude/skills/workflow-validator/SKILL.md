---
name: workflow-validator
description: Validate CasareRPA workflow JSON files for structural integrity, node dependencies, and connection validity. See schemas/ for JSON schema definitions. Use when: validating workflows, checking workflow JSON, testing workflow definitions, graph structure validation, node connections.
---

# Workflow Validator

Validate workflow JSON files for structural integrity and correctness.

## Quick Start

```python
from scripts.workflow_validator import validate_workflow, ValidationReport

report = validate_workflow("path/to/workflow.json")

if report.is_valid:
    print("✓ Valid workflow")
else:
    for error in report.errors:
        print(f"✗ {error}")
```

## Validation Checks

| Check | Description |
|-------|-------------|
| JSON Structure | Valid JSON and required fields |
| Nodes | All nodes exist in registry |
| Connections | Valid node and port references |
| Graph Structure | No cycles, has start node |
| Variables | Defined before use |
| Data Types | Compatible port connections |

## JSON Schemas

See `schemas/` for workflow JSON schema definitions by version.

## Common Errors

| Error | Fix |
|-------|-----|
| Missing Start node | Add a Start node |
| Cycle detected | Remove circular connection |
| Undefined variable | Add Set Variable node |
| Type mismatch | Add type conversion node |
