---
description: Implement a new automation node with parallel agent orchestration. Modes: implement (default), extend, refactor, clone
arguments:
  - name: node_name
    description: Name of the node (e.g., GoogleSheetsRowRead, ClickElement)
    required: true
  - name: category
    description: Node category (browser, desktop, data, integration, system, flow, ai)
    required: false
  - name: mode
    description: Mode (implement, extend, refactor, clone). Default is implement.
    required: false
---

# Implement Node: $ARGUMENTS.node_name

Execute the full automated workflow with parallel agents. Reference: `agent-rules/commands/implement-node.md`

## Mode: $ARGUMENTS.mode (default: implement)
## Category: $ARGUMENTS.category

## Parallel Execution Rule

> **CRITICAL**: Launch up to **5 agents in parallel** when tasks are independent.

## Phase 1: RESEARCH (explore)

```
Task(subagent_type="explore", prompt="Find similar nodes in src/casare_rpa/nodes/$ARGUMENTS.category/. Look for patterns matching $ARGUMENTS.node_name. Return: file paths, class structure, port definitions, decorators used.")

Task(subagent_type="explore", prompt="Find base class and decorators in domain/entities/base_node.py and domain/decorators.py. Return: required methods, port types, property definitions.")
```

### For integration nodes, add:
```
Task(subagent_type="researcher", prompt="Research best practices for integrating with the external API/service for $ARGUMENTS.node_name")
```

## Phase 2: PLAN (architect)

```
Task(subagent_type="architect", prompt="""
Create node specification for $ARGUMENTS.node_name.

Category: $ARGUMENTS.category
Mode: $ARGUMENTS.mode

Create plan in .brain/plans/node-$ARGUMENTS.node_name.md with:
- Node purpose (one sentence)
- Input ports (name, DataType, description)
- Output ports (name, DataType, description)
- Exec ports (exec_in, exec_out, exec_error if needed)
- Properties (PropertyDef with PropertyType)
- Similar nodes to reference
- Agent assignments

Follow patterns from explore findings.
""")
```

**Gate**: "Plan ready. Approve EXECUTE?"

## Phase 3: EXECUTE (Parallel - 3 agents)

### For mode=implement or mode=clone:
```
Task(subagent_type="builder", prompt="""
Create node logic: src/casare_rpa/nodes/$ARGUMENTS.category/$ARGUMENTS.node_name.py

Follow plan in .brain/plans/node-$ARGUMENTS.node_name.md

Include:
- @node(category="$ARGUMENTS.category") decorator
- @properties with PropertyDef
- add_exec_input() / add_exec_output() for exec ports
- add_input_port() / add_output_port() for data ports
- async execute() returning ExecutionResult
- Error handling with loguru logger
- Type hints on all methods
""")

Task(subagent_type="ui", prompt="""
Create visual wrapper: src/casare_rpa/presentation/canvas/visual_nodes/$ARGUMENTS.category/$ARGUMENTS.node_name.py

Include:
- VisualNodeBase inheritance
- NODE_CLASS = $ARGUMENTS.node_name
- CATEGORY = "$ARGUMENTS.category"
- _create_from_node_class() call
""")

Task(subagent_type="quality", prompt="""
mode: test

Create test suite: tests/nodes/test_$ARGUMENTS.node_name.py

Cover:
- test_init: Verify ports and properties
- test_execute_success: Happy path with mocked externals
- test_execute_error_handling: Exception handling

Use @pytest.mark.asyncio for async tests.
Mock ALL external APIs (Playwright, HTTP, file I/O).
""")
```

### For mode=extend:
```
Task(subagent_type="builder", prompt="Add new ports/properties to existing $ARGUMENTS.node_name following plan")
Task(subagent_type="quality", prompt="mode: test - Update tests for new ports/properties")
```

### For mode=refactor:
```
Task(subagent_type="refactor", prompt="Improve $ARGUMENTS.node_name code quality following plan, maintain existing behavior")
Task(subagent_type="quality", prompt="mode: test - Verify existing tests still pass")
```

## Phase 4: VALIDATE (Sequential Loop)

### Quality Agent:
```
Task(subagent_type="quality", prompt="""
mode: test

Run tests:
pytest tests/nodes/test_$ARGUMENTS.node_name.py -v
pytest tests/nodes/$ARGUMENTS.category/ -v  # Regression

All must pass.
""")
```

### Reviewer Agent:
```
Task(subagent_type="reviewer", prompt="""
Review $ARGUMENTS.node_name implementation.

Checklist:
- [ ] Exec ports use add_exec_input()/add_exec_output()
- [ ] All external calls wrapped in try/except
- [ ] Loguru logging with context
- [ ] Type hints on all methods
- [ ] Tests cover success + error paths
- [ ] @node and @properties decorators used

Output: APPROVED or ISSUES with file:line references
""")
```

**Loop**: If ISSUES → fix → quality → reviewer again

## Phase 5: REGISTRATION (builder)

After APPROVED, register the node:

```
Task(subagent_type="builder", prompt="""
Register $ARGUMENTS.node_name:

1. nodes/$ARGUMENTS.category/__init__.py - Add export
2. nodes/registry_data.py - Add registration entry
3. visual_nodes/$ARGUMENTS.category/__init__.py - Add visual export
""")
```

## Phase 6: DOCS (docs)

```
Task(subagent_type="docs", prompt="""
Update documentation:
- nodes/_index.md - Add node entry
- visual_nodes/_index.md - Add visual node entry
- .brain/context/current.md - Log completion
""")
```

## Completion

Report:
- Files created: node, visual node, tests
- Registration: registry_data.py updated
- Tests: All passing
- Review: APPROVED
- Ready for use in Canvas
