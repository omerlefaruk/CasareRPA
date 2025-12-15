# Slash Commands Research: Best Practices and Ideas for CasareRPA

**Date**: 2025-12-14
**Researcher**: Claude Research Specialist

## Executive Summary

This research identifies 15 high-value slash command ideas for CasareRPA based on:
1. Industry best practices from Claude Code ecosystem
2. RPA-specific automation patterns (UiPath, Power Automate)
3. DDD/Architecture validation patterns (ArchUnit concepts)
4. Current CasareRPA architecture analysis

---

## Current Command Inventory

CasareRPA already has 3 well-structured commands:

| Command | Purpose | Complexity |
|---------|---------|------------|
| `/implement-feature` | Full feature implementation with agents | High |
| `/implement-node` | Node creation with registration | High |
| `/fix-feature` | Bug diagnosis and fixing | Medium |

These follow a consistent pattern:
- YAML frontmatter with description/arguments
- Multi-phase execution (RESEARCH > PLAN > EXECUTE > VALIDATE > DOCS)
- Parallel agent orchestration
- Quality gates between phases

---

## Recommended New Commands (15 Total)

### Category 1: Code Review and Quality

#### 1. `/security-scan`
**Description**: Scan code for security vulnerabilities and credential leaks
**Use Cases**:
- Pre-commit security check
- Audit credential handling in nodes
- Find hardcoded secrets, API keys, tokens
- Check for injection vulnerabilities in browser nodes

**Implementation**:
```
Phases:
1. SCAN: Grep for patterns (API_KEY, password, secret, token)
2. ANALYZE: Check credential.py usage, environment variable patterns
3. REPORT: List findings with severity and line numbers
```

**Complexity**: Low
**Estimated LOC**: 50-80

---

#### 2. `/review-pr`
**Description**: AI-powered pull request review with checklist validation
**Use Cases**:
- Review changes before merge
- Validate against CasareRPA coding standards
- Check for DDD layer violations
- Verify theme usage, signal/slot patterns

**Implementation**:
```
Phases:
1. DIFF: git diff main...HEAD
2. ANALYZE: Check against CLAUDE.md rules
3. REVIEW: Generate findings with severity
4. CHECKLIST: Output pass/fail for each rule
```

**Complexity**: Medium
**Estimated LOC**: 100-150

---

#### 3. `/perf-profile`
**Description**: Profile code performance and identify bottlenecks
**Use Cases**:
- Analyze slow workflow loading
- Profile node execution time
- Find blocking operations in UI
- Memory usage analysis

**Implementation**:
```
Phases:
1. IDENTIFY: Find target functions/modules
2. PROFILE: Run with cProfile/line_profiler
3. ANALYZE: Parse results, identify hotspots
4. RECOMMEND: Suggest optimizations
```

**Complexity**: Medium
**Estimated LOC**: 80-120

---

### Category 2: Testing Automation

#### 4. `/test-node`
**Description**: Generate and run comprehensive tests for a specific node
**Use Cases**:
- Test new nodes during development
- Validate node behavior changes
- Generate test coverage report

**Implementation**:
```yaml
arguments:
  - name: node_name
    required: true
  - name: mode
    description: generate | run | both
```

```
Phases:
1. LOCATE: Find node in registry
2. ANALYZE: Extract ports, properties, execute signature
3. GENERATE: Create test_node_name.py with:
   - test_init (ports, properties exist)
   - test_execute_success (mocked externals)
   - test_execute_error (exception handling)
4. RUN: pytest tests/nodes/test_{node_name}.py -v
```

**Complexity**: Medium
**Estimated LOC**: 120-160

---

#### 5. `/coverage-gaps`
**Description**: Find untested code paths and suggest tests
**Use Cases**:
- Identify missing test coverage
- Prioritize testing efforts
- Pre-release quality check

**Implementation**:
```
Phases:
1. RUN: pytest --cov=src/casare_rpa --cov-report=xml
2. PARSE: Extract uncovered lines from coverage.xml
3. PRIORITIZE: Rank by file importance (nodes, domain, infrastructure)
4. SUGGEST: Generate test stubs for top gaps
```

**Complexity**: Medium
**Estimated LOC**: 100-140

---

#### 6. `/test-workflow`
**Description**: Validate and dry-run a workflow file
**Use Cases**:
- Pre-execution validation
- Detect broken connections
- Verify node availability
- Check credential requirements

**Implementation**:
```yaml
arguments:
  - name: workflow_path
    required: true
  - name: mode
    description: validate | dry-run | execute
```

```
Phases:
1. LOAD: Parse workflow JSON
2. VALIDATE: Schema check, node existence, connection validity
3. DRY-RUN: Trace execution path without side effects
4. REPORT: List issues, warnings, required credentials
```

**Complexity**: High
**Estimated LOC**: 200-300

---

### Category 3: RPA-Specific Commands

#### 7. `/debug-node`
**Description**: Interactive debugging session for a node
**Use Cases**:
- Troubleshoot node execution failures
- Trace data flow through ports
- Inspect runtime state

**Implementation**:
```yaml
arguments:
  - name: node_type
    required: true
  - name: input_data
    description: JSON input for ports
```

```
Phases:
1. SETUP: Create isolated execution context
2. TRACE: Add logging to port input/output
3. EXECUTE: Run with enhanced logging
4. INSPECT: Show state at each step
5. REPORT: Execution timeline, data transformations
```

**Complexity**: High
**Estimated LOC**: 180-250

---

#### 8. `/migrate-uipath`
**Description**: Convert UiPath XAML workflow to CasareRPA JSON
**Use Cases**:
- Import customer UiPath workflows
- Migration assistance
- Feature parity analysis

**Implementation**:
```yaml
arguments:
  - name: xaml_path
    required: true
  - name: output_path
    required: false
```

```
Phases:
1. PARSE: Read XAML, extract activities
2. MAP: UiPath activity -> CasareRPA node mapping
3. CONVERT: Generate workflow JSON
4. VALIDATE: Check for unsupported activities
5. REPORT: Conversion summary, manual steps needed
```

**Complexity**: High
**Estimated LOC**: 300-400

---

#### 9. `/credential-audit`
**Description**: Audit credential usage across workflows and nodes
**Use Cases**:
- Security review
- Credential rotation planning
- Dependency mapping

**Implementation**:
```
Phases:
1. SCAN: Find credential references in nodes
2. MAP: Track credential -> node -> workflow dependencies
3. VALIDATE: Check credential store for missing/expired
4. REPORT: Usage matrix, rotation recommendations
```

**Complexity**: Medium
**Estimated LOC**: 100-150

---

### Category 4: DDD/Architecture Commands

#### 10. `/layer-check`
**Description**: Validate DDD layer dependencies
**Use Cases**:
- Pre-commit architecture validation
- Prevent layer violations
- Enforce import rules

**Implementation**:
```
Phases:
1. SCAN: Parse imports in all .py files
2. VALIDATE: Check against layer rules:
   - Domain imports nothing
   - Application imports Domain only
   - Infrastructure imports Domain, Application
   - Presentation imports all
3. REPORT: Violations with file:line
```

**Complexity**: Medium
**Estimated LOC**: 120-180

Inspired by: ArchUnit (Java), ArchUnitNET (C#)

---

#### 11. `/event-trace`
**Description**: Trace event flow through the EventBus
**Use Cases**:
- Debug event not received issues
- Understand event propagation
- Verify subscription patterns

**Implementation**:
```yaml
arguments:
  - name: event_type
    required: true
    description: NodeCompleted, WorkflowStarted, etc.
```

```
Phases:
1. LOCATE: Find event class definition
2. FIND: Subscribers (bus.subscribe calls)
3. FIND: Publishers (bus.publish calls)
4. GRAPH: Visualize publisher -> subscriber flow
5. VALIDATE: Check for orphaned events, missing handlers
```

**Complexity**: Medium
**Estimated LOC**: 100-140

---

#### 12. `/domain-health`
**Description**: Comprehensive domain model validation
**Use Cases**:
- Verify aggregate boundaries
- Check entity consistency
- Validate value object immutability

**Implementation**:
```
Phases:
1. SCAN: Find domain entities, aggregates, value objects
2. VALIDATE:
   - Aggregates have proper boundaries
   - Entities have unique identifiers
   - Value objects are immutable
   - Events are frozen dataclasses
3. REPORT: Health score, violations, recommendations
```

**Complexity**: High
**Estimated LOC**: 200-280

---

### Category 5: Documentation and Maintenance

#### 13. `/update-index`
**Description**: Regenerate _index.md files from source
**Use Cases**:
- Keep documentation in sync
- Post-refactor cleanup
- Pre-release documentation update

**Implementation**:
```yaml
arguments:
  - name: scope
    description: nodes | visual_nodes | all
```

```
Phases:
1. SCAN: Find all relevant files in scope
2. EXTRACT: Parse class names, docstrings, decorators
3. GENERATE: Rebuild _index.md with current state
4. DIFF: Show changes for approval
```

**Complexity**: Medium
**Estimated LOC**: 150-200

---

#### 14. `/changelog`
**Description**: Generate changelog from git commits
**Use Cases**:
- Release preparation
- Sprint summary
- Stakeholder updates

**Implementation**:
```yaml
arguments:
  - name: since
    description: Tag, commit, or date
  - name: format
    description: markdown | slack | html
```

```
Phases:
1. FETCH: git log --oneline since..HEAD
2. CATEGORIZE: feat, fix, refactor, docs, test
3. GROUP: By component (nodes, canvas, orchestrator)
4. FORMAT: Generate structured output
```

**Complexity**: Low
**Estimated LOC**: 60-100

---

#### 15. `/impact-analysis`
**Description**: Analyze impact of changing a file or symbol
**Use Cases**:
- Pre-refactoring risk assessment
- Understand dependencies before changes
- Change impact matrix from CLAUDE.md

**Implementation**:
```yaml
arguments:
  - name: target
    required: true
    description: File path or symbol name
```

```
Phases:
1. LOCATE: Find target in codebase
2. TRACE: Find all imports/usages (grep + AST)
3. CLASSIFY: Direct vs transitive dependencies
4. MAP: Affected tests, visual nodes, infrastructure
5. REPORT: Impact matrix, risk level, test requirements
```

**Complexity**: High
**Estimated LOC**: 180-250

---

## Implementation Priority Matrix

| Command | Value | Complexity | Priority | Phase |
|---------|-------|------------|----------|-------|
| `/layer-check` | High | Medium | P0 | 1 |
| `/test-node` | High | Medium | P0 | 1 |
| `/security-scan` | High | Low | P0 | 1 |
| `/review-pr` | High | Medium | P1 | 2 |
| `/event-trace` | Medium | Medium | P1 | 2 |
| `/coverage-gaps` | Medium | Medium | P1 | 2 |
| `/test-workflow` | High | High | P2 | 3 |
| `/debug-node` | High | High | P2 | 3 |
| `/credential-audit` | Medium | Medium | P2 | 3 |
| `/update-index` | Medium | Medium | P2 | 3 |
| `/changelog` | Low | Low | P3 | 4 |
| `/perf-profile` | Medium | Medium | P3 | 4 |
| `/domain-health` | Medium | High | P3 | 4 |
| `/impact-analysis` | High | High | P3 | 4 |
| `/migrate-uipath` | Low | High | P4 | Future |

---

## Command Template Recommendations

Based on research, the ideal command structure for CasareRPA:

```markdown
---
description: One-line description (10-200 chars)
arguments:
  - name: arg_name
    description: Argument purpose
    required: true|false
model: opus|sonnet|haiku  # Optional: prefer specific model
allowed-tools: Read, Write, Bash, Grep  # Optional: restrict tools
---

# Command Title: $ARGUMENTS.arg_name

Execute workflow description. Reference: `agent-rules/commands/command-name.md`

## Mode/Options
- **mode**: $ARGUMENTS.mode (default: X)

## Parallel Execution Rule
> **CRITICAL**: Launch up to **5 agents in parallel** when tasks are independent.

## Phase 1: NAME (Parallel agents)
```
Task(subagent_type="type", prompt="...")
```

## Phase 2: NAME (agent)
```
Task(subagent_type="type", prompt="...")
```

**Gate**: "Phase complete. Continue?"

## Completion
Report:
- Key outcome 1
- Key outcome 2
- Summary
```

---

## Research Sources

### Claude Code Best Practices
- Anthropic Engineering: Claude Code Best Practices (2025-04)
- eesel.ai: Slash Commands Guide (2025-09)
- liquidmetal.ai: Claude Code Hooks Guide (2025-08)

### RPA Testing Patterns
- UiPath Test Suite Best Practices
- MuleSoft RPA Builder Testing and Debugging
- Blue Prism RPA Testing Guide

### Architecture Validation
- ArchUnit: Java architecture testing
- ArchUnitNET: C# port
- Spring Modulith: Application module verification
- QAvalidator: Architecture dependency checking

### Claude Code Community
- wshobson/commands: Workflow and tool commands
- davila7/claude-code-templates: Component templates
- tokenbender/agent-guides: Multi-agent patterns
- qdhenry/Claude-Command-Suite: Command organization

---

## Next Steps

1. **Phase 1 Implementation** (Priority P0):
   - Create `/layer-check` command
   - Create `/test-node` command
   - Create `/security-scan` command

2. **Create Command Development Guide**:
   - Document command template
   - Define agent orchestration patterns
   - Create testing strategy for commands

3. **Establish Command Metrics**:
   - Track command usage
   - Measure execution time
   - Collect user feedback

---

*This research is based on external best practices and internal codebase analysis. Recommendations align with CasareRPA's DDD architecture and multi-agent workflow patterns.*
