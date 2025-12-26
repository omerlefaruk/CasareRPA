---
description: Execute task with automatic agent parallelization
arguments:
  - name: task
    description: The task to execute
    required: true
  - name: mode
    description: Execution mode (auto, chain, decompose)
    required: false
  - name: parallel
    description: Enable parallel execution (true/false)
    required: false
  - name: dry_run
    description: Show execution plan without executing
    required: false
---

# Parallel Agent Execution

## Task: $ARGUMENTS.task

## Mode: $ARGUMENTS.mode (default: auto)
## Parallel: $ARGUMENTS.parallel (default: true)
## Dry Run: $ARGUMENTS.dry_run (default: false)

The parallel agent framework will:
1. **Analyze** the task for parallelizable work items
2. **Build** a dependency graph
3. **Schedule** agents in optimal parallel phases
4. **Execute** with shared state coordination
5. **Aggregate** results with timing metrics

## Expected Parallelization

For complex implementation tasks:
- **Phase 1 (Parallel)**: 3 explore agents (domain, tests, patterns)
- **Phase 2 (Sequential)**: 1 architect agent
- **Phase 3 (Parallel)**: 2-3 agents (builder, ui, integrations)
- **Phase 4 (Parallel)**: 2 agents (quality, docs)
- **Phase 5 (Sequential)**: 1 reviewer agent

**Estimated speedup**: 2-3x for multi-layer tasks

## Usage

```bash
# Dry run to see the plan
parallel-exec "Implement login feature with UI, backend, and tests" --dry_run true

# Execute with parallelization
parallel-exec "Implement login feature with UI, backend, and tests" --parallel true

# Force sequential execution
parallel-exec "Fix bug in node X" --parallel false
```

## Python API

```python
from casare_rpa.application.use_cases import ParallelAgentExecutor, ExecutorConfig

executor = ParallelAgentExecutor()
result = await executor.execute(
    task_description="Implement login and register features",
    config=ExecutorConfig(
        fail_fast=True,
        enable_parallel=True,
        dry_run=False,
    )
)

print(f"Status: {result.status}")
print(f"Parallel groups: {result.parallel_groups_executed}")
print(f"Total time: {result.total_time_ms}ms")
print(f"Estimated savings: {result.estimated_savings_ms}ms")
```

## Chain Executor Integration

The ChainExecutor now supports parallel execution:

```python
from casare_rpa.domain.services import ChainExecutor

executor = ChainExecutor(orchestrator, enable_parallel=True)

# Dry run with parallel plan
result = await executor.execute(
    description="Implement login feature",
    parallel=True,
    dry_run=True,
)
print(result.message)  # Shows parallel execution plan

# Execute with parallelization
result = await executor.execute(
    description="Implement login feature",
    parallel=True,
)
```
