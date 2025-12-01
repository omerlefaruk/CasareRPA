# Project Management Implementation Plan

## Status: PLANNING

## Brain Context

- Read: `.brain/activeContext.md` (current session state)
- Patterns: `.brain/systemPatterns.md` (architecture & design patterns)
- Rules: `.brain/projectRules.md` (coding standards)
- Roadmap: CLAUDE.md line 95-98 (v2→v3 refactoring, Clean Architecture)

## Overview

Project management is a core v3 feature enabling users to organize workflows into projects, manage file persistence, and integrate with the workflow editor (Canvas). Current gaps:

- No project entity in domain layer
- No project persistence (DB/file I/O) in infrastructure
- No project CRUD use cases (Application layer)
- No project UI in presentation layer
- Workflows are isolated; need grouping/metadata management

## Agents Assigned

- [ ] **Explore Agent**: Analyze existing workflow persistence, identify patterns in Canvas, identify DB schema baseline
- [ ] **rpa-engine-architect**: Domain entities (Project, ProjectFile), Application use cases (Create/Load/Save project), Infrastructure repositories
- [ ] **chaos-qa-engineer**: Test domain logic, application orchestration, edge cases (file locks, corrupted projects, version conflicts)
- [ ] **rpa-docs-writer**: API reference (Project endpoints), User guide (creating/managing projects), Error dictionary
- [ ] **rpa-refactoring-engineer**: Ensure Project follows Clean Architecture, interfaces segregation, no coupling violations

## Implementation Steps

1. **Domain Layer** - Define Project entity and value objects
   - Project aggregate root: id, name, description, created_at, updated_at, workflows[], metadata
   - ProjectFile VO: path, version, format (JSON), checksum
   - ProjectRepository interface (abstract persistence contract)

2. **Infrastructure Layer** - Implement persistence
   - FileSystemProjectRepository: Save/load from local .casare/projects/ directory
   - Optional: SQLite/Postgres adapter for enterprise deployments
   - Connection pooling for file I/O
   - Version control (detect breaking changes, migration support)

3. **Application Layer** - Use cases
   - CreateProjectUseCase: Validate name, initialize directory structure
   - LoadProjectUseCase: Deserialize workflows, validate integrity
   - SaveProjectUseCase: Serialize workflows, auto-backup on save
   - ListProjectsUseCase: Discovery for UI
   - DeleteProjectUseCase: Cascade delete with confirmation
   - ExportProjectUseCase: Package for distribution

4. **Presentation Layer** - UI integration
   - ProjectPanelController: List/create/open/delete projects
   - ProjectPropertiesWidget: Metadata editor
   - Canvas integration: Load workflows from selected project
   - File menu: Recent projects, project templates
   - EventBus events: ProjectOpened, ProjectSaved, ProjectDeleted

5. **Testing Strategy**
   - Domain: Pure unit tests for Project entity invariants
   - Application: Mock repositories, test use case orchestration
   - Infrastructure: Mock file I/O, test serialization/deserialization
   - Presentation: qtbot tests for controller, minimal UI testing
   - Integration: End-to-end workflow: create project → add workflows → save → load → verify

6. **Migration & Backward Compatibility**
   - Detect v2 workflow files, offer import into v3 project structure
   - ProjectMigrator: Convert legacy workflows to project format
   - Characterization tests for v2 behavior

## Files to Modify/Create

| File | Action | Owner Agent | Status |
|------|--------|-------------|--------|
| `src/casare_rpa/domain/entities/project.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/domain/value_objects/project_file.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/domain/repositories/project_repository.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/application/use_cases/project/create_project.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/application/use_cases/project/load_project.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/application/use_cases/project/save_project.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/application/use_cases/project/list_projects.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/application/use_cases/project/delete_project.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/infrastructure/repositories/file_system_project_repository.py` | Create | rpa-engine-architect | Pending |
| `src/casare_rpa/presentation/controllers/project_controller.py` | Create | rpa-ui-designer | Pending |
| `src/casare_rpa/presentation/widgets/project_panel.py` | Create | rpa-ui-designer | Pending |
| `tests/domain/entities/test_project.py` | Create | chaos-qa-engineer | Pending |
| `tests/application/use_cases/test_project_use_cases.py` | Create | chaos-qa-engineer | Pending |
| `tests/infrastructure/repositories/test_file_system_project_repository.py` | Create | chaos-qa-engineer | Pending |
| `tests/presentation/test_project_controller.py` | Create | chaos-qa-engineer | Pending |
| `docs/api/project-endpoints.md` | Create | rpa-docs-writer | Pending |
| `docs/guides/managing-projects.md` | Create | rpa-docs-writer | Pending |

## Progress Log

- [2025-11-30 15:32] Plan file created. Ready for exploration phase.

## Post-Completion Checklist

- [ ] All domain entities pass pure unit tests (90%+ coverage)
- [ ] All application use cases pass integration tests (85%+ coverage)
- [ ] All infrastructure adapters pass with mocked I/O (70%+ coverage)
- [ ] Presentation controllers tested with qtbot (50%+ coverage)
- [ ] End-to-end workflow test (create → manage → save/load)
- [ ] Backward compatibility: v2 workflow import successful
- [ ] Documentation: API reference + user guides complete
- [ ] Code review: No architecture violations (CLAUDE.md layer rules)
- [ ] Update `.brain/activeContext.md` with learnings & patterns discovered
- [ ] Update `.brain/systemPatterns.md` if new patterns identified
- [ ] All tests green: `pytest tests/ -v`
- [ ] Ruff linting clean: `ruff check src/`

## Unresolved Questions

1. Where should project files be stored? (~/.casare/projects/? AppData/CasareRPA/projects/?)
2. Should projects support remote backends (Git, S3, Azure Blob)? (v3.1 or later?)
3. Version migration strategy: Auto-upgrade or prompt user?
4. Should there be a "default" project, or always require explicit project selection?
5. Multi-user scenario: File locks? Conflict resolution for concurrent edits?
