# Enhanced Agent Chaining Implementation Plan

**Created**: 2025-12-25 | **Version**: 2.0 | **Status**: In Progress

## Overview

Implementation plan for 5 enhanced agent chaining features:
1. Smart Chain Selection (ML-Based Task Classification)
2. Dynamic Loop Adjustment (Auto-Adjust Iterations)
3. Cross-Chain Dependencies (Handle Dependent Features)
4. Cost Optimization (Minimize Token Usage)
5. Predictive Timing (Estimate Completion Time)

---

## Architecture

```
src/casare_rpa/
├── application/
│   └── orchestrators/
│       └── enhanced_chain_orchestrator.py  # Main orchestrator
├── domain/
│   └── services/
│       ├── smart_chain_selector.py         # Feature 1
│       ├── dynamic_loop_manager.py         # Feature 2
│       ├── dependency_manager.py           # Feature 3
│       ├── cost_optimizer.py               # Feature 4
│       └── predictive_timer.py             # Feature 5
├── infrastructure/
│   └── persistence/
│       ├── chain_history_store.py          # Historical data
│       └── cost_tracker.py                 # Cost tracking
└── interfaces/
    └── chain_cli.py                        # CLI interface
```

---

## Feature 1: Smart Chain Selection

### Files to Create

| File | Purpose |
|------|---------|
| `domain/services/smart_chain_selector.py` | Main classifier |
| `domain/services/intent_classifier.py` | NLP-based intent detection |
| `domain/services/complexity_scorer.py` | Complexity estimation |
| `domain/services/entity_recognizer.py` | Component identification |
| `domain/services/context_aware_classifier.py` | Context integration |

### Implementation Steps

#### Step 1.1: Create TaskType Enum Extensions

```python
# domain/entities/task_type.py
from enum import Enum
from dataclasses import dataclass

class ComplexityLevel(Enum):
    TRIVIAL = 1
    SIMPLE = 2
    MODERATE = 3
    COMPLEX = 4
    EPIC = 5

@dataclass
class ClassificationResult:
    task_type: TaskType
    complexity: ComplexityLevel
    confidence: float
    estimated_duration: int
    suggested_parallel: List[str]
    reasoning: List[str]
```

#### Step 1.2: Intent Classifier

```python
# domain/services/intent_classifier.py
class IntentClassifier:
    """NLP-based intent classification for task types."""

    INTENT_PATTERNS = {
        "implement": ["create", "add", "implement", "build", "develop", "new"],
        "fix": ["fix", "repair", "debug", "resolve", "solve", "correct", "bug"],
        "research": ["research", "investigate", "analyze", "explore", "understand"],
        "refactor": ["refactor", "clean", "optimize", "improve", "modernize"],
        "extend": ["extend", "enhance", "add to", "augment", "expand"],
        "clone": ["clone", "duplicate", "copy", "replicate"],
        "test": ["test", "verify", "check", "validate", "ensure"],
        "docs": ["document", "write docs", "generate docs", "update docs"],
        "ui": ["ui", "widget", "style", "design", "layout", "component"],
        "integration": ["integrate", "connect", "api", "service", "external"],
        "security": ["security", "audit", "review", "scan", "vulnerability"],
    }

    def classify_intent(self, request: str) -> Tuple[str, float]:
        """Classify intent from request text."""
        # Implementation with keyword matching + scoring
```

#### Step 1.3: Complexity Scorer

```python
# domain/services/complexity_scorer.py
class ComplexityScorer:
    """Estimate task complexity based on request characteristics."""

    COMPLEXITY_INDICATORS = {
        "trivial": ["simple", "one line", "minor", "tiny"],
        "simple": ["small", "basic", "easy", "straightforward"],
        "moderate": ["feature", "component", "add", "implement"],
        "complex": ["architecture", "refactor", "redesign", "major"],
        "epic": ["system", "complete overhaul", "redesign", "foundation"],
    }

    def score_complexity(
        self,
        request: str,
        task_type: TaskType,
        context: dict = None
    ) -> ComplexityLevel:
        """Score complexity of the request."""
        # Implementation with multi-factor scoring
```

#### Step 1.4: Smart Chain Selector Main Class

```python
# domain/services/smart_chain_selector.py
class SmartChainSelector:
    """Main service for intelligent task classification."""

    def __init__(
        self,
        intent_classifier: IntentClassifier,
        complexity_scorer: ComplexityScorer,
        context_aware: ContextAwareClassifier
    ):
        self.intent_classifier = intent_classifier
        self.complexity_scorer = complexity_scorer
        self.context_aware = context_aware

    def classify(self, request: str, context: dict = None) -> ClassificationResult:
        """Classify request into task type and complexity."""
        # Orchestrate classification pipeline
```

### Tests

- `tests/domain/services/test_smart_chain_selector.py`
- `tests/domain/services/test_intent_classifier.py`
- `tests/domain/services/test_complexity_scorer.py`

### Acceptance Criteria

- [ ] Intent classification accuracy > 90% on test set
- [ ] Complexity estimation within 1 level of actual
- [ ] Classification latency < 100ms
- [ ] Falls back to manual selection if confidence < 70%

---

## Feature 2: Dynamic Loop Adjustment

### Files to Create

| File | Purpose |
|------|---------|
| `domain/services/dynamic_loop_manager.py` | Main loop manager |
| `domain/services/issue_severity_classifier.py` | Issue severity detection |
| `domain/services/auto_fix_engine.py` | Auto-fix certain issues |
| `domain/entities/loop_decision.py` | Loop decision dataclass |

### Implementation Steps

#### Step 2.1: Issue Severity Classifier

```python
# domain/services/issue_severity_classifier.py
class IssueSeverityClassifier:
    """Classify issue severity for loop decisions."""

    SEVERITY_KEYWORDS = {
        IssueSeverity.CRITICAL: ["security", "vulnerability", "data loss", "breach"],
        IssueSeverity.HIGH: ["broken", "failing", "crash", "error"],
        IssueSeverity.MEDIUM: ["impaired", "workaround", "partial"],
        IssueSeverity.LOW: ["minor", "best practice", "suggestion"],
        IssueSeverity.COSMETIC: ["style", "formatting", "typo"],
    }

    def classify_severity(self, issue: Issue) -> IssueSeverity:
        """Classify severity of an issue."""
```

#### Step 2.2: Dynamic Loop Manager

```python
# domain/services/dynamic_loop_manager.py
class DynamicLoopManager:
    """Manage loop iterations based on issue characteristics."""

    LOOP_RULES = {
        TaskType.IMPLEMENT: {
            IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
            IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
            IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
            IssueSeverity.LOW: {"max_iterations": 3, "action": "auto-fix"},
            IssueSeverity.COSMETIC: {"max_iterations": 3, "action": "auto-fix"},
        },
        # ... other task types
    }

    def should_continue_loop(
        self,
        issues: List[Issue],
        iteration: int,
        task_type: TaskType
    ) -> LoopDecision:
        """Determine if looping should continue."""
```

#### Step 2.3: Auto-Fix Engine

```python
# domain/services/auto_fix_engine.py
class AutoFixEngine:
    """Automatically fix certain issue types."""

    ISSUE_HANDLERS = {
        IssueCategory.CODING_STANDARDS: {
            "ruff_format": self._fix_formatting,
            "import_order": self._fix_imports,
        },
        IssueCategory.DOCUMENTATION: {
            "missing_docstring": self._add_docstring,
        },
        IssueCategory.TYPE_SAFETY: {
            "missing_type": self._infer_type,
        },
    }

    def can_auto_fix(self, issue: Issue) -> bool:
        """Check if issue is auto-fixable."""

    def auto_fix(self, issue: Issue) -> FixResult:
        """Apply auto-fix to issue."""
```

### Tests

- `tests/domain/services/test_dynamic_loop_manager.py`
- `tests/domain/services/test_issue_severity_classifier.py`
- `tests/domain/services/test_auto_fix_engine.py`

### Acceptance Criteria

- [ ] Critical issues escalate immediately (0 iterations)
- [ ] High severity issues get max 1 iteration
- [ ] Auto-fix works for LOW/COSMETIC issues
- [ ] Loop decisions logged for audit

---

## Feature 3: Cross-Chain Dependencies

### Files to Create

| File | Purpose |
|------|---------|
| `domain/services/dependency_manager.py` | Dependency graph management |
| `domain/services/conflict_detector.py` | Conflict detection |
| `domain/services/chain_orchestrator.py` | Multi-chain execution |
| `domain/entities/dependency.py` | Dependency dataclasses |

### Implementation Steps

#### Step 3.1: Dependency Entities

```python
# domain/entities/dependency.py
from enum import Enum
from dataclasses import dataclass, field

class DependencyType(Enum):
    BLOCKING = 1
    BLOCKED_BY = 2
    SHOULD_COMPLETE_BEFORE = 3
    CONFLICTS_WITH = 4
    CAN_RUN_PARALLEL = 5

@dataclass
class Dependency:
    target_chain_id: str
    dependency_type: DependencyType
    reason: str

@dataclass
class ProvidedFeature:
    name: str
    description: str

@dataclass
class ChainSpec:
    chain_id: str
    task_type: TaskType
    description: str
    depends_on: List[Dependency] = field(default_factory=list)
    provides: List[ProvidedFeature] = field(default_factory=list)
```

#### Step 3.2: Dependency Manager

```python
# domain/services/dependency_manager.py
class DependencyManager:
    """Manage cross-chain dependencies."""

    def __init__(self):
        self.dependency_graph: Dict[str, ChainSpec] = {}
        self.dependency_graph_vis: Dict[str, Set[str]] = {}

    def register_chain(self, spec: ChainSpec) -> None:
        """Register a chain with its dependencies."""

    def can_start(self, chain_id: str) -> Tuple[bool, List[str]]:
        """Check if chain can start (dependencies satisfied)."""

    def get_execution_order(self, chain_ids: List[str]) -> List[str]:
        """Get safe execution order for multiple chains."""
```

#### Step 3.3: Conflict Detector

```python
# domain/services/conflict_detector.py
class ConflictDetector:
    """Detect conflicts between chains."""

    CONFLICT_TYPES = {
        "file_overwrite": "Both chains modify same file",
        "api_conflict": "Both modify same API endpoint",
        "schema_conflict": "Both change same data schema",
        "resource_conflict": "Both require exclusive resource",
    }

    def detect_conflicts(
        self,
        chain_a: ChainSpec,
        chain_b: ChainSpec
    ) -> List[Conflict]:
        """Detect conflicts between two chains."""
```

#### Step 3.4: Chain Orchestrator

```python
# domain/services/chain_orchestrator.py
class ChainOrchestrator:
    """Orchestrate execution of multiple dependent chains."""

    def execute_with_dependencies(
        self,
        chain_specs: List[ChainSpec],
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    ) -> ExecutionResult:
        """Execute multiple chains with dependency management."""
```

### Tests

- `tests/domain/services/test_dependency_manager.py`
- `tests/domain/services/test_conflict_detector.py`
- `tests/domain/services/test_chain_orchestrator.py`

### Acceptance Criteria

- [ ] Dependencies correctly registered
- [ ] Execution order respects dependencies
- [ ] Conflicts detected between chains
- [ ] Parallel execution for non-conflicting chains

---

## Feature 4: Cost Optimization

### Files to Create

| File | Purpose |
|------|---------|
| `infrastructure/persistence/cost_tracker.py` | Token usage tracking |
| `domain/services/cost_optimizer.py` | Cost optimization |
| `domain/services/cost_model.py` | Cost estimation model |
| `infrastructure/cost_dashboard.py` | Cost visualization |

### Implementation Steps

#### Step 4.1: Cost Tracker

```python
# infrastructure/persistence/cost_tracker.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CostEntry:
    chain_id: str
    agent: str
    model: str
    input_tokens: int
    output_tokens: int
    timestamp: datetime
    cost: float

class CostTracker:
    """Track token usage and costs."""

    MODEL_PRICES = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
    }

    def record_usage(
        self,
        chain_id: str,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> CostEntry:
        """Record token usage."""

    def get_chain_cost(self, chain_id: str) -> ChainCost:
        """Get cost breakdown for a chain."""

    def get_period_summary(
        self,
        start: datetime,
        end: datetime
    ) -> PeriodSummary:
        """Get cost summary for a period."""
```

#### Step 4.2: Cost Model

```python
# domain/services/cost_model.py
class CostModel:
    """Model for estimating costs."""

    def estimate_cost(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        model: str = "gpt-4-turbo"
    ) -> CostEstimate:
        """Estimate cost for a task."""
```

#### Step 4.3: Cost Optimizer

```python
# domain/services/cost_optimizer.py
class CostOptimizer:
    """Optimize chain execution for cost efficiency."""

    MODEL_SELECTION = {
        "explore": "gpt-4-turbo",
        "architect": "claude-3-sonnet",
        "builder": "claude-3-opus",
        "quality": "gpt-4-turbo",
        "reviewer": "claude-3-sonnet",
        "docs": "gpt-4-turbo",
    }

    def optimize(
        self,
        chain: ChainTemplate,
        budget: float = None
    ) -> OptimizedChain:
        """Generate cost-optimized chain execution plan."""
```

### Tests

- `tests/infrastructure/test_cost_tracker.py`
- `tests/domain/services/test_cost_model.py`
- `tests/domain/services/test_cost_optimizer.py`

### Acceptance Criteria

- [ ] All token usage tracked accurately
- [ ] Cost estimates within 10% of actual
- [ ] Optimization suggestions reduce cost by > 20%
- [ ] Dashboard shows current period spending

---

## Feature 5: Predictive Timing

### Files to Create

| File | Purpose |
|------|---------|
| `infrastructure/persistence/chain_history_store.py` | Historical data |
| `domain/services/predictive_timer.py` | Time prediction |
| `domain/services/milestone_tracker.py` | Milestone tracking |
| `domain/services/pattern_learner.py` | Historical patterns |

### Implementation Steps

#### Step 5.1: Chain History Store

```python
# infrastructure/persistence/chain_history_store.py
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass
class ChainExecution:
    chain_id: str
    task_type: TaskType
    complexity: ComplexityLevel
    started: datetime
    completed: datetime
    duration_seconds: int
    agent_durations: Dict[str, int]
    success: bool
    iterations: int

class ChainHistoryStore:
    """Store and retrieve chain execution history."""

    def save_execution(self, execution: ChainExecution) -> None:
        """Save execution to history."""

    def get_history(
        self,
        task_type: TaskType = None,
        complexity: ComplexityLevel = None,
        limit: int = 100
    ) -> List[ChainExecution]:
        """Get historical executions."""
```

#### Step 5.2: Predictive Timer

```python
# domain/services/predictive_timer.py
class PredictiveTimer:
    """Predict chain completion times."""

    def __init__(self, history_store: ChainHistoryStore):
        self.history = history_store

    def predict(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        system_load: SystemLoad = None
    ) -> TimePrediction:
        """Predict completion time for a chain."""
```

#### Step 5.3: Milestone Tracker

```python
# domain/services/milestone_tracker.py
class MilestoneTracker:
    """Track and predict milestones during execution."""

    def predict_next_milestone(
        self,
        chain_id: str,
        current_state: ChainState
    ) -> MilestonePrediction:
        """Predict when next milestone will be reached."""
```

#### Step 5.4: Pattern Learner

```python
# domain/services/pattern_learner.py
class PatternLearner:
    """Learn from historical chain executions."""

    def learn_from_execution(self, execution: ChainExecution) -> None:
        """Update model with new execution data."""

    def get_patterns(self, task_type: TaskType) -> List[Pattern]:
        """Get learned patterns for task type."""
```

### Tests

- `tests/infrastructure/test_chain_history_store.py`
- `tests/domain/services/test_predictive_timer.py`
- `tests/domain/services/test_milestone_tracker.py`

### Acceptance Criteria

- [ ] P50 predictions within ±20% of actual
- [ ] P90 predictions within ±40% of actual
- [ ] Milestone updates in real-time
- [ ] Patterns learned from history improve predictions

---

## Integration

### Enhanced Chain Orchestrator

```python
# application/orchestrators/enhanced_chain_orchestrator.py
class EnhancedChainOrchestrator:
    """Main orchestrator for enhanced chain execution."""

    def __init__(
        self,
        smart_selector: SmartChainSelector,
        loop_manager: DynamicLoopManager,
        dependency_manager: DependencyManager,
        cost_optimizer: CostOptimizer,
        predictive_timer: PredictiveTimer,
        cost_tracker: CostTracker
    ):
        self.smart_selector = smart_selector
        self.loop_manager = loop_manager
        self.dependency_manager = dependency_manager
        self.cost_optimizer = cost_optimizer
        self.predictive_timer = predictive_timer
        self.cost_tracker = cost_tracker

    def execute(
        self,
        request: str,
        context: dict = None,
        options: ChainOptions = None
    ) -> ExecutionResult:
        """Execute chain with all enhanced features."""
```

### CLI Integration

```python
# interfaces/chain_cli.py
class ChainCLI:
    """CLI interface for chain commands."""

    def handle_chain_command(
        self,
        task_type: str,
        description: str,
        options: dict
    ) -> None:
        """Handle /chain command."""
```

### OpenCode Integration

```json
{
  "enhanced_chaining": {
    "smart_selection": true,
    "dynamic_loops": true,
    "dependencies": true,
    "cost_optimization": true,
    "predictive_timing": true
  }
}
```

---

## Implementation Schedule

| Week | Feature | Milestone |
|------|---------|-----------|
| **1** | Cost Optimization | Cost tracking + dashboard working |
| **2** | Predictive Timing | History store + prediction working |
| **3** | Dynamic Loops | Auto-loop + auto-fix working |
| **4** | Smart Selection | Classification working |
| **5** | Cross-Chain Dependencies | Dependency management working |
| **6** | Integration | All features integrated + tested |

---

## Testing Strategy

### Unit Tests

- Each service has dedicated unit tests
- Mock external dependencies
- Test edge cases and error conditions

### Integration Tests

- End-to-end chain execution tests
- Multi-chain dependency tests
- Cost tracking integration tests

### Performance Tests

- Classification latency < 100ms
- Prediction accuracy targets
- Cost tracking overhead < 1%

---

## Migration Plan

### Phase 1: Backward Compatibility

All new features opt-in via flags:
```bash
/chain implement "Feature" --smart-select=true --cost-optimize=true
```

### Phase 2: Default Enabling

After testing period, enable by default:
```bash
/chain implement "Feature"  # All enhancements enabled
```

### Phase 3: Deprecation

Remove old implementation after transition:
```bash
/chain implement "Feature" --legacy=false  # Default
```

---

## Files to Create (Summary)

| File | Layer | Feature |
|------|-------|---------|
| `domain/services/smart_chain_selector.py` | Domain | 1 |
| `domain/services/intent_classifier.py` | Domain | 1 |
| `domain/services/complexity_scorer.py` | Domain | 1 |
| `domain/services/dynamic_loop_manager.py` | Domain | 2 |
| `domain/services/issue_severity_classifier.py` | Domain | 2 |
| `domain/services/auto_fix_engine.py` | Domain | 2 |
| `domain/services/dependency_manager.py` | Domain | 3 |
| `domain/services/conflict_detector.py` | Domain | 3 |
| `domain/services/chain_orchestrator.py` | Domain | 3 |
| `domain/services/cost_optimizer.py` | Domain | 4 |
| `domain/services/cost_model.py` | Domain | 4 |
| `domain/services/predictive_timer.py` | Domain | 5 |
| `domain/services/milestone_tracker.py` | Domain | 5 |
| `domain/services/pattern_learner.py` | Domain | 5 |
| `infrastructure/persistence/cost_tracker.py` | Infrastructure | 4 |
| `infrastructure/persistence/chain_history_store.py` | Infrastructure | 5 |
| `application/orchestrators/enhanced_chain_orchestrator.py` | Application | All |
| `interfaces/chain_cli.py` | Interfaces | All |

---

## Dependencies

### External

- None required for MVP (simple heuristic-based ML)
- Optional: `scikit-learn` for advanced classification (future)

### Internal

- `domain/entities/task_type.py` - Task type enum
- `domain/entities/chain.py` - Chain definition
- `infrastructure/persistence/json_store.py` - Base persistence

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Classification accuracy low | High | Fallback to manual selection |
| Cost prediction inaccurate | Medium | Wide confidence intervals |
| Dependency conflicts | Medium | Conflict detection + resolution |
| Performance overhead | Low | Async execution, caching |
| Data privacy | Low | Local processing only |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Classification Accuracy | > 90% | User feedback |
| Loop Efficiency | > 50% reduction | Iteration count |
| Cost Savings | > 30% | vs. baseline |
| Time Prediction Accuracy | > 85% | P50 within ±20% |
| Dependency Resolution | 100% | No conflicts |
| User Satisfaction | > 4.5/5 | Survey |
