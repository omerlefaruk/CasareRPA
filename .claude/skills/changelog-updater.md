---
skill: changelog-updater
description: Maintain and update the CHANGELOG.md file following Keep a Changelog format, documenting features, fixes, breaking changes, and migrations for each release.
---

When updating the changelog, follow the [Keep a Changelog](https://keepachangelog.com/) format:

## CHANGELOG.md Structure

```markdown
# Changelog

All notable changes to CasareRPA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- New features that have been added

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in upcoming releases

### Removed
- Features that have been removed

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes

## [X.Y.Z] - YYYY-MM-DD

### Added
- Feature description

### Fixed
- Bug fix description

<!-- Older versions below -->
```

## Update Process

### 1. Analyze Recent Changes

```bash
# Get commits since last release
git log v2.1.0..HEAD --oneline

# Or since last changelog update
git log --since="2025-11-01" --oneline

# See detailed changes
git log v2.1.0..HEAD --pretty=format:"%h - %s (%an, %ad)" --date=short
```

### 2. Categorize Changes

**Added** - New features:
- `feat:` commits
- New nodes, controllers, components
- New capabilities or integrations

**Changed** - Modifications to existing features:
- `refactor:` commits that change public API
- Behavior changes
- Performance improvements
- Dependency updates

**Deprecated** - Features marked for removal:
- Deprecation warnings added
- Compatibility layers introduced
- Migration guides provided

**Removed** - Deleted features:
- Breaking changes removing functionality
- Deprecated code removed
- Old compatibility layers removed

**Fixed** - Bug fixes:
- `fix:` commits
- Resolved issues
- Corrected behavior

**Security** - Security-related changes:
- Vulnerability patches
- Security improvements
- Authentication/authorization changes

### 3. Write Changelog Entries

**Entry Format**:
```markdown
### Category

- Brief description of change in user-facing language
- Reference issue/PR if applicable: #123, #456
- Note breaking changes with migration guidance
```

**Good Examples**:
```markdown
### Added
- Browser node connection pooling for 60% faster workflow execution
- PostgreSQL and MySQL async database support with connection pooling
- Event-driven trigger system with 10 trigger types (Manual, Scheduled, Webhook, etc.)
- Project management system with hierarchical scoping (Projects → Scenarios → Workflows)
- Performance dashboard showing execution metrics and resource usage

### Changed
- Refactored MainWindow to controller pattern, reducing complexity from 1,200 to 650 lines
- Improved error handling in browser nodes with automatic retry on transient failures
- Updated test coverage from 45% to 78% for desktop automation nodes
- Migrated to strict type system with value objects (ExecutionResult, Port, DataType)

### Deprecated
- `casare_rpa.core.types` module - Use `casare_rpa.domain.value_objects.types` instead
- Dict-based port access - Use `Port` value object (removed in v3.0)
- See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for details

### Fixed
- Variable resolution in nested workflow scopes (#234)
- Memory leak in browser resource manager when reusing contexts
- Race condition in async node execution with parallel workflows
- Incorrect error reporting in desktop element selection

### Security
- Updated asyncpg to 0.29.2 to patch SQL injection vulnerability (CVE-2024-XXXXX)
- Implemented credential encryption for workflow variable storage
- Added input validation to prevent XSS in workflow JSON
```

**Bad Examples** (too technical, not user-focused):
```markdown
### Changed
- Refactored ExecutionOrchestrator.execute() method
- Updated imports in 15 files
- Changed variable name from `ctx` to `context`
```

### 4. Version and Date

For released versions:
```markdown
## [2.1.1] - 2025-12-01
```

For unreleased changes (ongoing development):
```markdown
## [Unreleased]
```

### 5. Breaking Changes Section

For major versions or significant breaking changes:

```markdown
## [3.0.0] - 2026-01-15

### BREAKING CHANGES

#### Removed Compatibility Layer

The `casare_rpa.core` compatibility layer has been removed. All imports must use domain layer directly.

**Migration Required**:

```python
# OLD (no longer works):
from casare_rpa.core.types import DataType, NodeId
from casare_rpa.core import Port

# NEW (required):
from casare_rpa.domain.value_objects.types import DataType, NodeId
from casare_rpa.domain.value_objects import Port
```

**Migration Tool**: Run `python scripts/migrate_imports.py` to automatically update imports.

**Timeline**: Compatibility layer was deprecated in v2.1, showing warnings since 2025-11-27.

#### Changed Port Data Structure

Ports are now value objects instead of dictionaries.

**Migration Required**:

```python
# OLD:
port_type = node.inputs['input1']['type']
port_data = node.inputs['input1']['data']

# NEW:
port_type = node.inputs['input1'].data_type
port_data = node.inputs['input1'].default_value
```

**Impact**: All custom nodes must update port access patterns.

**Documentation**: See [Port Migration Guide](docs/migrations/port-value-objects.md)

### Added
- Complete async execution engine with connection pooling
<!-- ... rest of changes ... -->
```

## Release Checklist

When preparing a release changelog entry:

- [ ] Review all commits since last release
- [ ] Categorize each significant change
- [ ] Write user-facing descriptions (not technical implementation details)
- [ ] Reference related issues/PRs
- [ ] Document breaking changes with migration guidance
- [ ] Update version number following semantic versioning
- [ ] Add release date
- [ ] Move entries from [Unreleased] to new version section
- [ ] Create new empty [Unreleased] section for next development cycle
- [ ] Update links at bottom of file

## Version Number Guidelines

Follow [Semantic Versioning](https://semver.org/):

**MAJOR** version (X.0.0): Breaking changes
- Removing features
- Changing public APIs
- Requiring user migration
Example: `2.5.3` → `3.0.0`

**MINOR** version (X.Y.0): New features, backwards compatible
- Adding new nodes
- New capabilities
- Non-breaking improvements
Example: `2.5.3` → `2.6.0`

**PATCH** version (X.Y.Z): Bug fixes, backwards compatible
- Fixing bugs
- Security patches
- Documentation updates
Example: `2.5.3` → `2.5.4`

## Full CHANGELOG.md Example

```markdown
# Changelog

All notable changes to CasareRPA will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- In-progress features not yet released

## [2.2.0] - 2025-12-15

### Added
- Advanced trigger system with 10 trigger types
- Project management system with hierarchical scoping
- Performance dashboard for monitoring workflow execution
- Connection pooling for browsers, databases, and HTTP sessions
- 25 new desktop automation nodes for Office integration

### Changed
- Improved async execution performance by 60% with connection pooling
- Enhanced error reporting with detailed stack traces and screenshots
- Updated test coverage to 78% (1,255 tests)

### Fixed
- Variable resolution in nested workflow scopes (#234)
- Memory leak in browser resource manager (#267)
- Race condition in parallel workflow execution (#289)

### Security
- Updated Playwright to 1.41.0 (security patches)
- Implemented workflow JSON schema validation

## [2.1.0] - 2025-11-27

### Added
- Clean architecture with domain, application, infrastructure, presentation layers
- 141 visual nodes organized in 12 categories
- EventBus system with 115+ event types for loose coupling
- Controller pattern (9 controllers) for UI logic
- Component pattern (9 components) for feature modules
- Comprehensive test suite with 1,255 tests (60% coverage)

### Changed
- Refactored MainWindow using controller pattern (1,200 → 650 lines)
- Migrated to domain layer with value objects (Port, ExecutionResult, DataType)
- Organized visual nodes from 3,793 lines across 27 files to 141 nodes in 12 files

### Deprecated
- `casare_rpa.core.types` - Use `casare_rpa.domain.value_objects.types` (removed in v3.0)
- `casare_rpa.core.base_node.Port` - Use `casare_rpa.domain.value_objects.port.Port`
- `visual_nodes.py` (4,285 lines) - Use category-specific files in `visual_nodes/`

### Fixed
- Runtime errors in application startup
- Encapsulation violations in Week 4 refactoring

## [2.0.0] - 2025-10-15

### Added
- Initial clean architecture implementation
- 242 automation nodes across 27 categories
- Workflow JSON format
- Visual node-based canvas editor

### BREAKING CHANGES

#### New Architecture
Complete restructuring to clean architecture pattern. See [REFACTORING_ROADMAP.md](REFACTORING_ROADMAP.md) for migration guide.

## [1.0.0] - 2025-09-01

Initial release.

### Added
- Basic workflow automation capabilities
- Browser automation with Playwright
- Desktop automation with uiautomation
- Visual workflow designer
- 50+ automation nodes

[Unreleased]: https://github.com/user/casare-rpa/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/user/casare-rpa/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/user/casare-rpa/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/user/casare-rpa/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/user/casare-rpa/releases/tag/v1.0.0
```

## Usage

When user requests changelog update:

1. Run `git log` to see recent changes
2. Categorize each significant commit
3. Write user-facing descriptions
4. Determine version number based on change types
5. Update CHANGELOG.md with new section
6. Move unreleased items if releasing
7. Update version links at bottom
8. Commit with message: `docs: update CHANGELOG for vX.Y.Z release`
