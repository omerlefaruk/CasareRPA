---
name: commit-message-generator
description: Generate well-formatted, conventional commit messages based on staged changes, following the project's commit conventions and best practices.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: git
---

When generating commit messages, analyze the staged changes and create a message following this exact format:

## Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type (Required)

Choose ONE type that best describes the change:

- **feat**: New feature for the user
- **fix**: Bug fix
- **docs**: Documentation only changes
- **style**: Changes that don't affect code meaning (formatting, whitespace)
- **refactor**: Code change that neither fixes a bug nor adds a feature
- **perf**: Performance improvement
- **test**: Adding or correcting tests
- **build**: Changes to build system or dependencies
- **ci**: Changes to CI configuration (GitHub Actions)
- **chore**: Other changes that don't modify src or test files

### Scope (Optional but Recommended)

The scope should indicate what part of the codebase is affected:

**Domain Layer**:
- `domain/entities` - Workflow, Node, Project entities
- `domain/services` - ExecutionOrchestrator, ProjectContext
- `domain/repositories` - Repository interfaces

**Application Layer**:
- `use-cases` - ExecuteWorkflowUseCase, etc.

**Infrastructure Layer**:
- `resources` - BrowserResourceManager, DatabaseResourceManager
- `persistence` - File storage implementations

**Presentation Layer**:
- `canvas` - Main window and canvas UI
- `controllers` - UI controllers
- `components` - UI components
- `visual-nodes` - Visual node wrappers

**Nodes**:
- `nodes/browser` - Browser automation nodes
- `nodes/desktop` - Desktop automation nodes
- `nodes/data` - Data operation nodes
- `nodes/control-flow` - Control flow nodes
- (etc. for other node categories)

**Other**:
- `tests` - Test files
- `ci` - GitHub Actions workflows
- `build` - PyInstaller, dependencies

### Subject Line (Required)

- Use imperative mood: "add" not "added" or "adds"
- Don't capitalize first letter
- No period at the end
- Maximum 72 characters
- Be concise but descriptive

Examples:
- ✅ `add retry mechanism to browser nodes`
- ✅ `fix variable resolution in nested scopes`
- ✅ `refactor MainWindow to use controller pattern`
- ❌ `Added retry mechanism` (wrong tense)
- ❌ `Fix bug` (not descriptive)
- ❌ `Refactored the MainWindow class to use the controller pattern for better separation of concerns.` (too long)

### Body (Optional but Recommended for Complex Changes)

- Explain WHAT and WHY, not HOW
- Wrap at 72 characters
- Separate from subject with blank line
- Use bullet points for multiple changes
- Reference issue numbers if applicable

Example:
```
- Extract node creation logic to NodeController
- Move graph operations to GraphController
- Add event bus for component communication
- Reduces MainWindow from 1,200 to 800 lines

Improves testability by isolating responsibilities.
```

### Footer (Optional)

Include metadata about the change:

**Breaking Changes**:
```
BREAKING CHANGE: Port data structure changed from dict to Port value object
Migration: Update all port references to use Port.data_type instead of port['type']
```

**Issue References**:
```
Fixes #123
Closes #456, #789
Related to #42
```

**Claude Code Attribution** (for commits generated with Claude Code):
```
🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## Analysis Process

To generate a commit message, analyze the staged changes:

### 1. Run git status and git diff

```bash
# See what files are staged
git status

# See the actual changes
git diff --staged

# See recent commits for style reference
git log --oneline -10
```

### 2. Categorize Changes

Identify the primary type of change:
- **New functionality** → `feat`
- **Bug fixes** → `fix`
- **Code reorganization** → `refactor`
- **Test additions** → `test`
- **Documentation** → `docs`
- **Performance** → `perf`

### 3. Identify Scope

Look at which directories are affected:
- `src/casare_rpa/domain/` → `domain/*`
- `src/casare_rpa/application/` → `use-cases`
- `src/casare_rpa/nodes/browser/` → `nodes/browser`
- `src/casare_rpa/presentation/canvas/controllers/` → `controllers`
- `tests/` → `tests`

### 4. Summarize Impact

Count the changes:
- Number of files modified
- Lines added/removed
- Key functionality affected

### 5. Generate Message

Combine the analysis into a well-structured commit message.

## Examples by Change Type

### Feature Addition

```
feat(nodes/browser): add screenshot capture node

- Implement ScreenshotNode with full-page and element capture
- Add PNG/JPEG format support
- Include automatic filename generation
- Add visual wrapper for canvas integration

Supports both full-page screenshots and element-specific captures
with configurable output formats.

Tests: tests/nodes/browser/test_screenshot_node.py (12 tests)
Coverage: 95%
```

### Bug Fix

```
fix(domain/services): resolve variable scope issue in nested workflows

Context variables were not being properly inherited when executing
nested workflows, causing undefined variable errors.

- Add scope hierarchy tracking in ProjectContext
- Propagate parent scope to child workflow executions
- Add test coverage for nested variable resolution

Fixes #234
```

### Refactoring

```
refactor(canvas): extract controllers from MainWindow

- Create NodeController (350 lines)
- Create GraphController (280 lines)
- Create PropertyController (220 lines)
- Add EventBus for component communication
- Reduce MainWindow from 1,200 to 650 lines

Improves testability and maintainability by separating concerns.
No breaking changes to public API.

Tests: All existing tests pass
Impact: presentation/canvas/ module only
```

### Test Addition

```
test(nodes): expand desktop node test coverage

Add comprehensive tests for 15 desktop automation nodes:
- ApplicationNode (launch, close, focus)
- WindowNode (find, resize, move)
- ElementNode (click, type, get text)
- MouseNode (click, double-click, move)
- KeyboardNode (press, type, hotkey)

Coverage increased from 45% to 78% for desktop nodes.

Tests: 156 new tests added
Files: tests/nodes/desktop/*.py
```

### Performance Improvement

```
perf(infrastructure): implement browser connection pooling

- Add BrowserResourceManager with pool of 5 browser instances
- Reuse browser contexts across workflow executions
- Reduce browser launch time from 2s to 0.1s per workflow

Benchmark results:
- Sequential workflows: 60% faster
- Parallel workflows: 75% faster
- Memory usage: Reduced by 40%

Implementation: infrastructure/resources/browser_manager.py
```

### Documentation

```
docs: add comprehensive API reference for domain layer

- Document all entities (Workflow, Project, ExecutionState)
- Add docstrings to all value objects
- Include usage examples for ExecutionOrchestrator
- Create migration guide for v2.x → v3.0

Files: 15 .md files in docs/api/
```

### Breaking Change

```
feat(domain): migrate to strict type system with value objects

Replace dict-based data structures with typed value objects:
- Port class replaces port dicts
- ExecutionResult replaces result tuples
- DataType enum replaces string literals

BREAKING CHANGE: Node port access changed
Migration:
  OLD: node.inputs['input1']['type']
  NEW: node.inputs['input1'].data_type

Compatibility layer in casare_rpa.core will be removed in v3.0.

Migration guide: docs/MIGRATION_GUIDE_WEEK2.md
Deprecation warnings: Added to all old imports
```

## Special Cases

### Multiple Scopes

If changes affect multiple scopes, choose the most significant or use a parent scope:

```
refactor(presentation): extract UI components library

Changes span canvas, visual-nodes, and orchestrator UI.
```

### Merge Commits

For merges, use a descriptive message:

```
merge: integrate Week 5 test coverage expansion

Merges branch 'refactor/week5-test-coverage-expansion' into main.

- 525 new tests added (60% node coverage)
- Domain layer tests (100% coverage)
- Controller tests (127 tests)
- Component tests (42 tests)

Total test count: 1,255 tests
```

### Revert Commits

```
revert: "feat(nodes): add experimental AI node"

This reverts commit abc123def456.

Reason: AI integration requires additional security review
before production deployment.
```

## Usage

When user requests a commit message:

1. Run `git diff --staged` to see changes
2. Analyze the changes to determine type and scope
3. Generate a commit message following the format
4. Ask user if they want to modify any part
5. Provide the final message ready to copy or use with `git commit -m`

For commits created with Claude Code assistance, always include the attribution footer.
