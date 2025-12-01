# Robot Executor Implementation Plan

## Status: PLANNING

## Brain Context
- Read: .brain/activeContext.md (current session state)
- Patterns: .brain/systemPatterns.md (architecture patterns)
- Rules: .brain/projectRules.md (coding standards)
- Reference: CLAUDE.md (project structure, TDD workflow)

## Overview

Robot executor is the headless workflow execution engine for CasareRPA. It:
- Executes workflows submitted via Orchestrator API
- Polls for pending jobs and orchestrates node execution
- Manages credentials securely via vault/environment
- Handles async execution with Playwright (web) & UIAutomation (desktop)
- Reports execution results back to Orchestrator database
- Implements distributed agent model for scalability

**Key Responsibilities:**
1. Workflow Polling: Pull pending jobs from Orchestrator database
2. Execution Engine: Execute nodes sequentially/parallel based on topology
3. Credential Handling: Decrypt and inject credentials at runtime
4. Resource Management: Browser contexts, desktop automation sessions
5. Error Handling: Capture failures, retry logic, timeout management
6. Result Reporting: Store execution logs, artifacts, state snapshots

## Agents Assigned
- [ ] **rpa-engine-architect**: Workflow execution engine, polling loop, state machine
- [ ] **security-architect**: Credential vault integration, secret handling, sandboxing
- [ ] **chaos-qa-engineer**: Failure scenarios, edge cases, stress tests, timeout handling

## Architecture Context

### Current State
- Robot exists at `src/casare_rpa/robot/` (CLI entry point, distributed_agent.py)
- Orchestrator API at `src/casare_rpa/infrastructure/orchestrator/api/`
- Core execution via nodes in `src/casare_rpa/nodes/`
- ExecutionContext defined in core layer

### Design Principles
- **Clean Architecture**: Domain (execution logic) ← Infrastructure (DB polling, creds)
- **Async-First**: All I/O async (Playwright, DB queries, network)
- **Testability**: Mock all external APIs (DB, Playwright, win32, vault)
- **Distributed**: Multiple robot instances can run simultaneously (via APScheduler + DB polling)

## Implementation Steps

### Phase 1: Domain Layer (Execution Logic)
- [ ] Define ExecutionOrchestrator service (pure logic, no I/O)
  - Topology validation (circular dependency detection)
  - Node execution sequencing (topological sort)
  - State machine for workflow (PENDING → RUNNING → COMPLETED/FAILED)
  - Error handling & retry logic
- [ ] Define CredentialManager domain service
  - Credential injection rules (which node gets which secret)
  - Variable interpolation (${var_name} in node properties)

### Phase 2: Infrastructure Layer (Adapters)
- [ ] WorkflowRepository adapter (fetch from Orchestrator DB)
- [ ] ExecutionResultRepository adapter (store execution logs)
- [ ] CredentialVault adapter (decrypt secrets on demand)
- [ ] JobPoller service (continuous polling for pending jobs)

### Phase 3: Application Layer (Use Cases)
- [ ] ExecuteWorkflowUseCase (orchestrate domain + infra)
  - Fetch workflow + job metadata
  - Validate topology
  - Execute nodes with state tracking
  - Handle failures & cleanup
  - Report results

### Phase 4: Robot CLI / Distributed Agent
- [ ] Update `robot/cli.py` to start polling loop
- [ ] Update `robot/distributed_agent.py` with job polling logic
- [ ] Signal handlers (SIGTERM for graceful shutdown)
- [ ] Resource cleanup (browser contexts, sessions)

### Phase 5: Testing & Documentation
- [ ] Unit tests (domain layer, no mocks)
- [ ] Integration tests (domain + mocked infra)
- [ ] End-to-end tests (full workflow execution with mock DB)
- [ ] API documentation (Orchestrator job schema)

## Files to Modify/Create

| File | Action | Description | Owner Agent |
|------|--------|-------------|-------------|
| `src/casare_rpa/domain/services/execution_orchestrator.py` | CREATE | Execution state machine & node orchestration | rpa-engine-architect |
| `src/casare_rpa/domain/services/credential_manager.py` | CREATE | Credential injection & variable interpolation | security-architect |
| `src/casare_rpa/infrastructure/repositories/workflow_repository.py` | CREATE/MODIFY | Fetch workflows from Orchestrator | rpa-engine-architect |
| `src/casare_rpa/infrastructure/repositories/execution_result_repository.py` | CREATE | Store execution logs & results | rpa-engine-architect |
| `src/casare_rpa/infrastructure/adapters/credential_vault.py` | CREATE | Decrypt secrets from vault/env | security-architect |
| `src/casare_rpa/infrastructure/job_poller.py` | CREATE | Poll Orchestrator for pending jobs | rpa-engine-architect |
| `src/casare_rpa/application/use_cases/execute_workflow_use_case.py` | CREATE | Orchestrate full execution flow | rpa-engine-architect |
| `src/casare_rpa/robot/cli.py` | MODIFY | Add polling loop & job dispatch | rpa-engine-architect |
| `src/casare_rpa/robot/distributed_agent.py` | MODIFY | Resource lifecycle & signal handling | rpa-engine-architect |
| `tests/domain/services/test_execution_orchestrator.py` | CREATE | Domain logic tests (no mocks) | chaos-qa-engineer |
| `tests/domain/services/test_credential_manager.py` | CREATE | Credential interpolation tests | chaos-qa-engineer |
| `tests/infrastructure/test_job_poller.py` | CREATE | Job polling logic (mock DB) | chaos-qa-engineer |
| `tests/application/test_execute_workflow_use_case.py` | CREATE | Integration tests | chaos-qa-engineer |
| `tests/robot/test_robot_executor_e2e.py` | CREATE | End-to-end workflow execution | chaos-qa-engineer |

## Progress Log

- [2025-11-30] Plan created. Awaiting review.
- TODO: Execute Phase 1 (domain services)
- TODO: Execute Phase 2 (infrastructure adapters)
- TODO: Execute Phase 3 (use cases)
- TODO: Execute Phase 4 (CLI integration)
- TODO: Execute Phase 5 (tests & docs)

## Open Questions

1. **Credential Storage**: Use environment variables, vault file, or Orchestrator secrets table?
2. **Job Polling Interval**: Fixed interval or exponential backoff? Configurable?
3. **Parallel Execution**: Can multiple robots execute same workflow simultaneously? Or exclusive lock?
4. **Retry Strategy**: Exponential backoff with max retries? Backoff only on specific error types?
5. **Resource Limits**: Max concurrent browser contexts per robot? Config-driven?
6. **Logging**: Send logs to Orchestrator DB or file-based? Structured logging (JSON)?
7. **Timeout Handling**: Global workflow timeout? Per-node timeout? Cascading cancellation?
8. **State Snapshots**: Store intermediate state after each node? Or only on failure?

## Post-Completion Checklist

- [ ] All tests passing (pytest tests/ -v)
- [ ] Coverage targets met (Domain 90%+, Infra 70%+, Application 85%+)
- [ ] Code review passed (architecture patterns verified)
- [ ] Update .brain/activeContext.md with completion status
- [ ] Update .brain/systemPatterns.md if new patterns discovered
- [ ] Documentation complete (API docs, implementation guide)
- [ ] Distributed execution verified (multi-robot scenario)
- [ ] Security audit passed (credential handling, secrets not logged)
