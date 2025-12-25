---
name: workflow-validator
description: Validate CasareRPA workflow JSON files for structural integrity, node dependencies, connection validity, and execution requirements.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: validation
---

When the user requests workflow validation, perform the following comprehensive checks:

## Validation Checklist

### 1. JSON Structure Validation

```python
import orjson
from pathlib import Path

def validate_json_structure(workflow_path: str) -> tuple[bool, list[str]]:
    """
    Validate basic JSON structure and required fields.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    try:
        content = Path(workflow_path).read_bytes()
        workflow = orjson.loads(content)
    except orjson.JSONDecodeError as e:
        return (False, [f"Invalid JSON: {e}"])

    # Check required top-level fields
    required_fields = ['workflow_id', 'name', 'nodes', 'connections']
    for field in required_fields:
        if field not in workflow:
            errors.append(f"Missing required field: '{field}'")

    # Validate data types
    if 'nodes' in workflow and not isinstance(workflow['nodes'], list):
        errors.append("'nodes' must be an array")

    if 'connections' in workflow and not isinstance(workflow['connections'], list):
        errors.append("'connections' must be an array")

    return (len(errors) == 0, errors)
```

### 2. Node Validation

```python
from casare_rpa.nodes import node_registry

def validate_nodes(workflow: dict) -> tuple[bool, list[str]]:
    """
    Validate all nodes exist and have required fields.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    node_ids = set()

    for idx, node in enumerate(workflow.get('nodes', [])):
        # Check required node fields
        required = ['node_id', 'type', 'x', 'y']
        for field in required:
            if field not in node:
                errors.append(f"Node {idx}: Missing '{field}'")

        node_id = node.get('node_id')
        if node_id:
            # Check for duplicate IDs
            if node_id in node_ids:
                errors.append(f"Duplicate node_id: '{node_id}'")
            node_ids.add(node_id)

            # Check if node type exists in registry
            node_type = node.get('type')
            if node_type and not node_registry.exists(node_type):
                errors.append(f"Node {node_id}: Unknown type '{node_type}'")

    return (len(errors) == 0, errors)
```

### 3. Connection Validation

```python
def validate_connections(workflow: dict) -> tuple[bool, list[str]]:
    """
    Validate all connections reference valid nodes and ports.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Build node ID set
    node_ids = {n['node_id'] for n in workflow.get('nodes', []) if 'node_id' in n}

    for idx, conn in enumerate(workflow.get('connections', [])):
        # Check required connection fields
        required = ['from_node', 'from_port', 'to_node', 'to_port']
        for field in required:
            if field not in conn:
                errors.append(f"Connection {idx}: Missing '{field}'")
                continue

        # Validate nodes exist
        from_node = conn.get('from_node')
        to_node = conn.get('to_node')

        if from_node not in node_ids:
            errors.append(f"Connection {idx}: 'from_node' '{from_node}' not found")

        if to_node not in node_ids:
            errors.append(f"Connection {idx}: 'to_node' '{to_node}' not found")

        # Check for self-connections (usually invalid)
        if from_node == to_node:
            errors.append(f"Connection {idx}: Node '{from_node}' connected to itself")

    return (len(errors) == 0, errors)
```

### 4. Graph Structure Validation

```python
def validate_graph_structure(workflow: dict) -> tuple[bool, list[str]]:
    """
    Validate graph structure (cycles, start node, reachability).

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', [])

    # Check for start node
    start_nodes = [n for n in nodes if n.get('type') == 'start']
    if len(start_nodes) == 0:
        errors.append("Workflow must have at least one Start node")
    elif len(start_nodes) > 1:
        errors.append(f"Workflow has {len(start_nodes)} Start nodes (should have 1)")

    # Build adjacency list
    graph = {}
    for node in nodes:
        graph[node['node_id']] = []

    for conn in connections:
        from_node = conn.get('from_node')
        to_node = conn.get('to_node')
        if from_node and to_node:
            graph[from_node].append(to_node)

    # Check for cycles (using DFS)
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    visited = set()
    rec_stack = set()

    for node_id in graph:
        if node_id not in visited:
            if has_cycle(node_id, visited, rec_stack):
                errors.append("Workflow contains a cycle (infinite loop)")
                break

    # Check reachability from start node
    if start_nodes:
        start_id = start_nodes[0]['node_id']
        reachable = set()

        def dfs(node):
            reachable.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in reachable:
                    dfs(neighbor)

        dfs(start_id)

        unreachable = set(graph.keys()) - reachable
        if unreachable:
            errors.append(f"Unreachable nodes: {', '.join(unreachable)}")

    return (len(errors) == 0, errors)
```

### 5. Variable Validation

```python
def validate_variables(workflow: dict) -> tuple[bool, list[str]]:
    """
    Validate variable usage (defined before use).

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    # Track variables defined by nodes
    defined_vars = set()

    # Get execution order (topological sort)
    nodes = workflow.get('nodes', [])
    connections = workflow.get('connections', [])

    # Build simple execution order (BFS from start node)
    start_nodes = [n for n in nodes if n.get('type') == 'start']
    if not start_nodes:
        return (True, [])  # Already reported in graph validation

    # For each node, check if it uses undefined variables
    for node in nodes:
        node_type = node.get('type')
        properties = node.get('properties', {})

        # Check if node references variables
        for key, value in properties.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                var_name = value[2:-1]  # Extract variable name
                if var_name not in defined_vars:
                    errors.append(
                        f"Node '{node.get('node_id')}': "
                        f"Uses undefined variable '${var_name}'"
                    )

        # Track variables defined by this node
        if node_type in ['set_variable', 'assign']:
            var_name = properties.get('variable_name')
            if var_name:
                defined_vars.add(var_name)

    return (len(errors) == 0, errors)
```

### 6. Data Type Validation

```python
def validate_data_types(workflow: dict) -> tuple[bool, list[str]]:
    """
    Validate port connections have compatible data types.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    nodes = {n['node_id']: n for n in workflow.get('nodes', [])}
    connections = workflow.get('connections', [])

    for conn in connections:
        from_node_id = conn.get('from_node')
        to_node_id = conn.get('to_node')
        from_port = conn.get('from_port')
        to_port = conn.get('to_port')

        # Get node instances from registry
        from_node_type = nodes.get(from_node_id, {}).get('type')
        to_node_type = nodes.get(to_node_id, {}).get('type')

        if not (from_node_type and to_node_type):
            continue

        # Get node class from registry
        from_node_class = node_registry.get(from_node_type)
        to_node_class = node_registry.get(to_node_type)

        if not (from_node_class and to_node_class):
            continue

        # Check port data types match
        from_instance = from_node_class()
        to_instance = to_node_class()

        from_port_obj = from_instance.outputs.get(from_port)
        to_port_obj = to_instance.inputs.get(to_port)

        if from_port_obj and to_port_obj:
            if from_port_obj.data_type != to_port_obj.data_type:
                errors.append(
                    f"Type mismatch: {from_node_id}.{from_port} "
                    f"({from_port_obj.data_type}) -> "
                    f"{to_node_id}.{to_port} ({to_port_obj.data_type})"
                )

    return (len(errors) == 0, errors)
```

## Validation Report Format

```python
from dataclasses import dataclass
from typing import List

@dataclass
class ValidationReport:
    """Workflow validation report."""

    workflow_path: str
    is_valid: bool
    errors: List[str]
    warnings: List[str]

    def __str__(self) -> str:
        """Format validation report as readable text."""
        output = [f"Workflow Validation Report: {self.workflow_path}"]
        output.append("=" * 60)

        if self.is_valid:
            output.append("✓ VALID: All checks passed")
        else:
            output.append("✗ INVALID: Validation failed")

        if self.errors:
            output.append("\nErrors:")
            for error in self.errors:
                output.append(f"  • {error}")

        if self.warnings:
            output.append("\nWarnings:")
            for warning in self.warnings:
                output.append(f"  ⚠ {warning}")

        return "\n".join(output)


def validate_workflow(workflow_path: str) -> ValidationReport:
    """
    Perform comprehensive workflow validation.

    Args:
        workflow_path: Path to workflow JSON file

    Returns:
        ValidationReport with all errors and warnings
    """
    all_errors = []
    warnings = []

    # Run all validation checks
    checks = [
        ("JSON Structure", validate_json_structure),
        ("Nodes", validate_nodes),
        ("Connections", validate_connections),
        ("Graph Structure", validate_graph_structure),
        ("Variables", validate_variables),
        ("Data Types", validate_data_types),
    ]

    workflow = None
    for check_name, check_func in checks:
        if check_name == "JSON Structure":
            is_valid, errors = check_func(workflow_path)
            if not is_valid:
                all_errors.extend([f"[{check_name}] {e}" for e in errors])
                break  # Can't continue without valid JSON

            # Load workflow for subsequent checks
            content = Path(workflow_path).read_bytes()
            workflow = orjson.loads(content)
        else:
            is_valid, errors = check_func(workflow)
            if not is_valid:
                all_errors.extend([f"[{check_name}] {e}" for e in errors])

    return ValidationReport(
        workflow_path=workflow_path,
        is_valid=len(all_errors) == 0,
        errors=all_errors,
        warnings=warnings
    )
```

## Usage

When user requests: "Validate my workflow"

1. Ask for workflow path if not provided
2. Run all validation checks
3. Generate comprehensive validation report
4. Suggest fixes for common errors:
   - Missing Start node → Add Start node
   - Undefined variables → Add Set Variable node
   - Unreachable nodes → Add connections
   - Type mismatches → Insert type conversion node
   - Cycles → Remove or break circular connections
