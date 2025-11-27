# Changelog

All notable changes to the CasareRPA project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Week 2: Clean Architecture Migration (2025-11-27) - COMPLETE

A comprehensive refactoring to establish Clean Architecture with domain-driven design principles.

#### Added

**Architecture**:
- Domain layer (`domain/`) with 15 files, 3,201 lines
  - `domain/entities/` - WorkflowSchema, ExecutionState, Project, Scenario
  - `domain/value_objects/` - DataType, Port, ExecutionResult
  - `domain/services/` - ExecutionOrchestrator, ProjectContext
- Infrastructure layer (`infrastructure/`) with 3 files, 673 lines
  - `infrastructure/resources/` - BrowserResourceManager
  - `infrastructure/persistence/` - ProjectStorage
- Application layer (`application/`) with 1 file, ~200 lines
  - `application/use_cases/` - ExecuteWorkflowUseCase

**Testing**:
- 235 new tests added (34 → 269 total)
- 5 new test files created
- Test coverage for 71 nodes (30% of 238 nodes)
- Comprehensive test suite for:
  - Data operations (32 nodes, 100% coverage)
  - Control flow (8 nodes)
  - System operations (13 nodes)
  - Script execution (3 nodes)

**Documentation**:
- `docs/ARCHITECTURE.md` - 450+ line comprehensive architecture guide
- `docs/MIGRATION_GUIDE_WEEK2.md` - Step-by-step migration instructions
- `docs/WEEK2_METRICS.md` - Detailed metrics tracking
- `docs/WEEK2_PR_DESCRIPTION.md` - Pull request documentation

**CI/CD**:
- Pre-commit hooks framework with basic file checks
- GitHub Actions CI pipeline (test, lint, security jobs)
- Pull request template
- CI/CD status badges in README.md
- Codecov integration

#### Changed

**Refactored Components**:
- `core/execution_context.py` - Split into domain state + infrastructure resources
- `core/workflow_schema.py` - Converted to re-export wrapper
- `core/types.py` - Converted to re-export wrapper
- `core/project_schema.py` - Converted to re-export wrapper
- `runner/workflow_runner.py` - Refactored to composition pattern
- `project/project_storage.py` - Converted to re-export wrapper
- `project/project_context.py` - Converted to re-export wrapper

**Architecture Improvements**:
- ExecutionContext now uses composition (domain + infrastructure)
- WorkflowRunner now uses use case pattern
- Project entities properly separated into domain + infrastructure
- All business logic isolated in domain layer
- Infrastructure properly abstracted

#### Deprecated

**Core Layer Imports** (emit DeprecationWarning):
- `casare_rpa.core.types` → use `casare_rpa.domain.value_objects.types`
- `casare_rpa.core.workflow_schema` → use `casare_rpa.domain.entities.workflow`
- `casare_rpa.core.project_schema` → use `casare_rpa.domain.entities.project`
- `casare_rpa.core.execution_context` → use domain + infrastructure layers

**Project Layer Imports** (emit DeprecationWarning):
- `casare_rpa.project.project_storage` → use `casare_rpa.infrastructure.persistence.project_storage`
- `casare_rpa.project.project_context` → use `casare_rpa.domain.services.project_context`

**Timeline**: All deprecated imports will be removed in v3.0

#### Removed
- None (100% backward compatibility maintained)

#### Fixed
- Trailing whitespace in 54 source files
- End-of-file issues in 53 source files
- Data operation nodes now use ExecutionResult pattern consistently
- Proper error handling in all 32 data operation nodes

#### Security
- Added pip-audit security scanning to CI pipeline

#### Breaking Changes
- **None** - 100% backward compatibility maintained via re-export wrappers

#### Migration Path
All existing code continues to work unchanged. Deprecation warnings guide developers to new import paths. See `docs/MIGRATION_GUIDE_WEEK2.md` for details.

#### Metrics

**Architecture**:
- Domain files: 0 → 15
- Domain lines: 0 → 3,201
- Infrastructure files: 0 → 3
- Layers defined: 0 → 3 (domain, application, infrastructure)

**Testing**:
- Test files: 3 → 8 (+5)
- Total tests: 34 → 269 (+235, 7.9x increase)
- Nodes tested: 24 → 71 (+47, 3x increase)
- Node coverage: 10% → 30%

**Code Quality**:
- Deprecation warnings: Active
- Breaking changes: 0
- Backward compatibility: 100%

---

## [Week 1] - 2025-11-20 to 2025-11-26

### Added
- Comprehensive trigger system with 10 trigger types
  - Manual, Scheduled, Webhook, FileWatch, Email triggers
  - AppEvent, Form, Chat, Error, WorkflowCall triggers
- Trigger registry with dynamic type registration
- Project management system with hierarchical structure
  - Projects contain Scenarios contain Workflows
  - Variable and credential scoping
- Connection pooling for performance optimization
  - Browser context pooling
  - Database connection pooling
  - HTTP session pooling
- Performance dashboard UI with metrics visualization
- 1255+ comprehensive tests covering all major features
- Integration tests for system and script nodes
- 32 data operation nodes migrated to ExecutionResult pattern

### Changed
- All data operation nodes now use ExecutionResult for consistency
- Enhanced workflow execution with trigger event handling
- Improved error handling throughout the codebase

### Removed
- Deprecated `extended_visual_nodes.py` file
- Legacy node implementations without ExecutionResult

### Fixed
- Various bug fixes in trigger event handling
- Improved stability of workflow execution engine

---

## [0.1.0] - Initial Development

### Added
- Visual node-based workflow editor using NodeGraphQt
- 140+ automation nodes across 27 categories
- Browser automation with Playwright
- Desktop automation with uiautomation
- Async/await architecture with qasync
- Workflow serialization with orjson
- Comprehensive logging with loguru
- Three main applications:
  - Canvas (Designer)
  - Robot (Executor)
  - Orchestrator (Manager)

---

## Version History

- **Week 2 (Current)**: CI/CD Foundation & Refactoring Initiative
- **Week 1**: Trigger System, Project Management, Performance Optimization
- **0.1.0**: Initial Core Platform Development

---

## Contributing

When adding entries to the changelog:
1. Add new items to the `[Unreleased]` section
2. Categorize under: Added, Changed, Deprecated, Removed, Fixed, Security
3. Use present tense ("Add feature" not "Added feature")
4. Include issue/PR references where applicable
5. Move items to a version section when releasing

---

## Notes

- This changelog tracks all significant changes to the project
- For detailed commit history, see the Git log
- For planning and roadmaps, see `DEVELOPMENT_ROADMAP.md`
- For metrics tracking, see `docs/WEEK2_METRICS.md`
