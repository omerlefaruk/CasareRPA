---
description: Comprehensive guide for automatic agent chaining with loop-based error recovery
---

# Agent Chaining Guide (Enhanced)

This guide provides automatic agent chaining patterns for all development workflows with built-in error recovery loops.

## Overview

**Automatic Chaining Principle**: When you specify a task type, the system automatically chains the appropriate agents in sequence with error recovery.

## Task Type to Agent Chain Mapping

| Task Type | Primary Chain | Loop Condition | Exit Condition |
|-----------|---------------|----------------|----------------|
| **RESEARCH** | `explore` → `researcher` | N/A (exploratory) | Human approval |
| **IMPLEMENT** | `architect` → `builder` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **REFACTOR** | `explore` → `refactor` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **FIX** | `explore` → `builder` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **EXTEND** | `explore` → `architect` → `builder` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **CLONE** | `explore` → `builder` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **TEST** | `explore` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **DOCS** | `explore` → `docs` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **SECURITY** | `explore` → `security-auditor` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **UI** | `explore` → `ui` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |
| **INTEGRATION** | `explore` → `integrations` → `quality` → `reviewer` | Reviewer ISSUES | Reviewer APPROVED |

## Automatic Loop Pattern

### For IMPLEMENT/FIX/REFACTOR Tasks

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHAIN EXECUTION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│   │ EXPLORE  │────►│ ARCHITECT│────►│  BUILDER │               │
│   │ (5 min)  │     │ (10 min) │     │ (30 min) │               │
│   └──────────┘     └──────────┘     └─────┬────┘               │
│                                           │                     │
│   ┌───────────────────────────────────────▼──────┐              │
│   │            BUILD PHASE COMPLETE              │              │
│   └──────────────────────────────────────────────┘              │
│                                           │                     │
│   ┌───────────────────────────────────────▼──────┐              │
│   │              QUALITY (Tests)                │              │
│   │              (15 min)                       │              │
│   └──────────────────────────────────────┬───────┘              │
│                                          │                      │
│   ┌──────────────────────────────────────▼──────┐               │
│   │              REVIEWER (Gate)                │               │
│   │              (10 min)                       │               │
│   └────────────────────┬────────────────────────┘               │
│                        │                                         │
│         ┌──────────────┴───────────────┐                        │
│         │                              │                        │
│    ┌────▼────┐                    ┌────▼────┐                   │
│    │ APPROVED│                    │ ISSUES │                   │
│    └────┬────┘                    └────┬────┘                   │
│         │                              │                        │
│         ▼                              ▼                        │
│   ┌──────────┐                   ┌──────────┐                   │
│   │   DONE   │                   │  BUILDER │                   │
│   └──────────┘                   │ (Fix)    │                   │
│                                  └────┬─────┘                   │
│                                       │                         │
│                              LOOP ───►│                         │
└─────────────────────────────────────────────────────────────────┘
```

### Loop Control Parameters

```yaml
max_iterations: 3           # Maximum review loops
timeout_per_agent: 600      # seconds (10 min per agent)
approval_required: true     # Human approval after APPROVED
parallel_allowed:
  - explore + docs          # Can run in parallel
  - security + quality      # Can run in parallel
```

## Task-Specific Chains

### 1. RESEARCH Chain

**Trigger**: "Research [topic]", "Investigate [issue]", "Analyze [feature]"

```
EXPLORE → RESEARCHER → (Human Approval)
```

**Agent Details**:
- **EXPLORE** (5 min): Semantic search, find existing patterns
- **RESEARCHER** (10 min): Deep dive, external research, best practices
- **Output**: Research report with recommendations

### 2. IMPLEMENT Chain (Most Common)

**Trigger**: "Implement [feature]", "Add [functionality]", "Create [component]"

```
EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER → (Loop if ISSUES)
```

**Agent Details**:
- **EXPLORE** (5 min): Find similar implementations, patterns
- **ARCHITECT** (10 min): Design doc, data contracts, implementation plan
- **BUILDER** (30 min): Code implementation, tests first
- **QUALITY** (15 min): Run tests, check lint, performance check
- **REVIEWER** (10 min): Code review gate

**Loop Logic**:
```
iterations = 0
while iterations < max_iterations:
    BUILD()
    TEST()
    result = REVIEW()

    if result == APPROVED:
        break
    else:
        FIX_ISSUES(result.issues)
        iterations += 1

if iterations == max_iterations and result != APPROVED:
    ESCALATE_TO_HUMAN()
```

### 3. REFACTOR Chain

**Trigger**: "Refactor [component]", "Clean up [module]", "Optimize [code]"

```
EXPLORE → REFACTOR → QUALITY → REVIEWER → (Loop if ISSUES)
```

**Agent Details**:
- **EXPLORE** (5 min): Understand current implementation, dependencies
- **REFACTOR** (20 min): Extract methods, apply patterns, maintain behavior
- **QUALITY** (10 min): Verify tests pass, no regressions
- **REVIEWER** (10 min): Verify behavior preserved, code quality

### 4. FIX Chain (Bug Fix)

**Trigger**: "Fix [bug]", "Debug [issue]", "Repair [failure]"

```
EXPLORE → BUILDER → QUALITY → REVIEWER → (Loop if ISSUES)
```

**Agent Details**:
- **EXPLORE** (5 min): Find bug location, understand error, check similar fixes
- **BUILDER** (15 min): Implement fix with error handling
- **QUALITY** (10 min): Test fix, regression tests
- **REVIEWER** (10 min): Verify fix correctness

### 5. EXTEND Chain (Feature Extension)

**Trigger**: "Extend [feature]", "Add [capability] to [existing]", "Enhance [component]"

```
EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER → (Loop if ISSUES)
```

### 6. CLONE Chain (Duplicate Pattern)

**Trigger**: "Clone [existing]", "Duplicate [pattern] as [new]"

```
EXPLORE → BUILDER → QUALITY → REVIEWER → (Loop if ISSUES)
```

### 7. TEST Chain

**Trigger**: "Test [component]", "Add tests for [feature]", "Verify [behavior]"

```
EXPLORE → QUALITY → REVIEWER → (Loop if ISSUES)
```

### 8. DOCS Chain

**Trigger**: "Document [feature]", "Update docs for [change]", "Generate API docs"

```
EXPLORE → DOCS → REVIEWER → (Loop if ISSUES)
```

### 9. UI Chain

**Trigger**: "Create UI for [feature]", "Fix [widget]", "Style [component]"

```
EXPLORE → UI → QUALITY → REVIEWER → (Loop if ISSUES)
```

### 10. INTEGRATION Chain

**Trigger**: "Integrate [API]", "Add [service] support", "Connect to [external]"

```
EXPLORE → INTEGRATIONS → QUALITY → REVIEWER → (Loop if ISSUES)
```

## Automatic Command Format

### Basic Syntax

```
/chain <task-type> "<description>" [options]
```

### Examples

```bash
# Implement a new node
/chain implement "Click Element Node for browser automation" --parallel=security

# Fix a bug
/chain fix "Null pointer in workflow loader" --priority=high

# Research a feature
/chain research "OAuth2 integration patterns for Google APIs"

# Refactor a module
/chain refactor "Clean up legacy HTTP client code" --target=infrastructure

# Extend existing
/chain extend "Add retry capability to HTTP nodes" --based-on="HTTPRequestNode"
```

### Options

| Option | Description | Example |
|--------|-------------|---------|
| `--parallel=<agents>` | Run agents in parallel | `--parallel=security,docs` |
| `--priority=<level>` | Set priority (high, normal, low) | `--priority=high` |
| `--max-iterations=<n>` | Override max loop iterations | `--max-iterations=5` |
| `--timeout=<seconds>` | Override agent timeout | `--timeout=300` |
| `--dry-run` | Preview chain without execution | `--dry-run` |
| `--skip-review` | Skip reviewer (not recommended) | `--skip-review` |

## Loop Recovery Strategies

### Strategy 1: Issue-Based Recovery

```python
def handle_reviewer_issues(issues: List[Issue]) -> RecoveryAction:
    issue_categories = categorize(issues)

    if issue_categories.type_safety > 0:
        return RecoveryAction(
            agent="builder",
            instruction="Fix type hints: " + format_issues(issue_categories.type_safety)
        )

    if issue_categories.error_handling > 0:
        return RecoveryAction(
            agent="builder",
            instruction="Add error handling: " + format_issues(issue_categories.error_handling)
        )

    if issue_categories.coding_standards > 0:
        return RecoveryAction(
            agent="refactor",
            instruction="Apply coding standards: " + format_issues(issue_categories.coding_standards)
        )

    return RecoveryAction(agent="human", instruction="Manual review required")
```

### Strategy 2: Test-Based Recovery

```python
def handle_test_failures(failures: List[TestFailure]) -> RecoveryAction:
    if failures.contain_infrastructure_errors():
        return RecoveryAction(
            agent="builder",
            instruction="Fix infrastructure mock issues"
        )

    if failures.contain_type_errors():
        return RecoveryAction(
            agent="builder",
            instruction="Fix type errors: " + format_test_errors(failures.type_errors)
        )

    if failures.contain_logic_errors():
        return RecoveryAction(
            agent="architect",
            instruction="Review logic design: " + format_test_errors(failures.logic_errors)
        )

    return RecoveryAction(agent="human", instruction="Complex test failures")
```

### Strategy 3: Timeout Recovery

```python
def handle_timeout(agent: str, elapsed: float) -> RecoveryAction:
    if elapsed > 600:  # > 10 minutes
        return RecoveryAction(
            agent="split",
            instruction=f"Split {agent} task into smaller subtasks"
        )

    return RecoveryAction(
        agent=agent,
        instruction=f"Retry with reduced scope"
    )
```

## Parallel Execution Matrix

| Primary Agent | Can Run In Parallel | Cannot Run With |
|---------------|---------------------|-----------------|
| EXPLORE | docs, security | builder, quality |
| ARCHITECT | - | builder (sequential) |
| BUILDER | - | all (sequential) |
| QUALITY | docs, security | builder (after) |
| REVIEWER | - | all (after) |
| DOCS | explore, quality | - |
| SECURITY | explore, quality | - |

## Progress Reporting Format

### Chain Start

```
══════════════════════════════════════════════════════════════
  CHAIN STARTED: IMPLEMENT
  Task: Click Element Node for browser automation
  Chain: EXPLORE → ARCHITECT → BUILDER → QUALITY → REVIEWER
  Max Iterations: 3
  Started: 2025-12-25 03:10 UTC
══════════════════════════════════════════════════════════════
```

### Agent Progress

```
[03:10] EXPLORE: Finding existing browser node patterns...
[03:12] EXPLORE: ✓ Found 5 similar patterns in nodes/browser/
[03:12] ARCHITECT: Designing ClickElementNode implementation...
[03:15] ARCHITECT: ✓ Design complete - see .brain/plans/click-node.md
[03:15] BUILDER: Implementing ClickElementNode...
...
```

### Loop Detection

```
[03:45] REVIEWER: ISSUES FOUND (2)
  - Line 42: Missing error handling for selector not found
  - Line 78: Type hint should be Optional[str], not str

[03:45] → Loop 1/3: Returning to BUILDER with fixes required
```

### Chain Complete

```
══════════════════════════════════════════════════════════════
  CHAIN COMPLETED: APPROVED
  Task: Click Element Node for browser automation
  Iterations: 1
  Duration: 45 minutes
  Files Created: 3
  Files Modified: 2
  Tests Added: 6
══════════════════════════════════════════════════════════════
```

## Error Escalation

When loops exceed max iterations:

```
[ERROR] Chain failed after 3 iterations
  Last Review: ISSUES (remaining: 2)
  - Complex architectural concern
  - Performance optimization needed

[ESCALATION] Human review required
  Summary: Implementation complete but needs architectural review
  Link: .brain/plans/escalation-{timestamp}.md
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT CHAIN QUICK REFERENCE               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  RESEARCH       → explore → researcher → APPROVAL           │
│                                                             │
│  IMPLEMENT      → explore → architect → builder →           │
│                       quality → reviewer → [LOOP]            │
│                                                             │
│  FIX            → explore → builder → quality →             │
│                       reviewer → [LOOP]                      │
│                                                             │
│  REFACTOR       → explore → refactor → quality →            │
│                       reviewer → [LOOP]                      │
│                                                             │
│  EXTEND         → explore → architect → builder →           │
│                       quality → reviewer → [LOOP]            │
│                                                             │
│  TEST           → explore → quality → reviewer → [LOOP]     │
│                                                             │
│  DOCS           → explore → docs → reviewer → [LOOP]        │
│                                                             │
│  UI             → explore → ui → quality → reviewer →       │
│                       [LOOP]                                 │
│                                                             │
│  INTEGRATION    → explore → integrations → quality →        │
│                       reviewer → [LOOP]                      │
│                                                             │
│  SECURITY       → explore → security → reviewer → [LOOP]    │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Loop Control: /chain <type> "<task>" --max-iterations=3    │
│  Status: python scripts/mcp_test.py                         │
│  Logs: .brain/logs/chain-{timestamp}.log                    │
└─────────────────────────────────────────────────────────────┘
```
