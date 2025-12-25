---
description: Enhanced agent chaining with ML-based selection, dynamic loops, dependencies, cost optimization, and predictive timing
---

# Enhanced Agent Chaining Features (v2.0)

**Version**: 2.0 | **Status**: Planned | **Target**: 2026-02-01

This document describes the 5 enhanced features for the agent chaining system.

---

## 1. Smart Chain Selection (ML-Based Task Classification)

### Overview

Automatically classify user requests into appropriate task types using machine learning, moving beyond simple keyword matching to understand intent, complexity, and context.

### Features

#### Intent Classification Model

```python
class TaskClassifier:
    """ML-based task type classifier."""

    def classify(self, request: str, context: dict = None) -> ClassificationResult:
        """
        Classify a user request into task type and complexity.

        Uses:
        - NLP for intent extraction
        - Complexity scoring
        - Historical patterns
        - Context awareness
        """
```

#### Classification Features

| Feature | Description | Data Source |
|---------|-------------|-------------|
| **Intent Detection** | Extract core action (create, fix, research, etc.) | NLP model |
| **Entity Recognition** | Identify components, features, files | NER model |
| **Complexity Scoring** | Estimate effort and scope | Rule-based + ML |
| **Context Awareness** | Use session context for accuracy | `.brain/context/` |
| **Historical Patterns** | Learn from similar past requests | Chain history |

#### Complexity Levels

```python
class ComplexityLevel(Enum):
    """Task complexity levels."""

    TRIVIAL = 1  # Simple fix, < 1 hour
    SIMPLE = 2   # Small feature, 1-4 hours
    MODERATE = 3 # Medium feature, 4-8 hours
    COMPLEX = 4  # Large feature, 8-24 hours
    EPIC = 5     # Major feature, 24+ hours
```

#### Classification Output

```python
@dataclass
class ClassificationResult:
    """Result of task classification."""

    task_type: TaskType  # implement, fix, research, etc.
    complexity: ComplexityLevel
    confidence: float  # 0.0 to 1.0
    suggested_chain: ChainTemplate
    estimated_duration: int  # minutes
    risk_level: RiskLevel
    suggested_parallel: List[str]
    reasoning: List[str]  # Explanation
```

### Implementation Components

```
smart_chain_selection/
├── classifiers/
│   ├── __init__.py
│   ├── intent_classifier.py      # NLP-based intent detection
│   ├── complexity_scorer.py      # Complexity estimation
│   ├── entity_recognizer.py      # Component identification
│   └── context_aware.py          # Context integration
├── models/
│   ├── __init__.py
│   ├── task_classifier.pkl       # Trained model
│   ├── embeddings/               # Embeddings for similarity
│   └── training_data/            # Labeled examples
└── evaluation/
    ├── __init__.py
    ├── metrics.py                # Classification metrics
    └── feedback.py               # Collect user feedback
```

### Usage Example

```python
# Before: Manual task type selection
/chain implement "Add OAuth2 support"

# After: Smart classification
> "Add OAuth2 authentication for Google APIs"
Classifier: "IMPLEMENT (confidence: 0.94)"
- Task Type: implement
- Complexity: MODERATE
- Estimated: 45 minutes
- Risk: MEDIUM
- Suggested: --parallel=security
- Reasoning: "Contains 'authentication' keyword, mentions specific API"
```

---

## 2. Dynamic Loop Adjustment

### Overview

Automatically adjust loop iterations based on issue severity, type, and frequency, rather than fixed iteration counts. Critical issues get immediate escalation; minor issues auto-fix.

### Features

#### Severity-Based Loop Control

```python
class DynamicLoopManager:
    """Manages loop iterations based on issue characteristics."""

    def should_continue_loop(
        self,
        issues: List[Issue],
        iteration: int,
        chain_type: TaskType
    ) -> LoopDecision:
        """
        Determine if looping should continue.

        Logic:
        - CRITICAL issues: Escalate immediately
        - HIGH issues: Max 1 iteration
        - MEDIUM issues: Max 2 iterations
        - LOW issues: Max 3 iterations (can auto-fix)
        """
```

#### Issue Severity Classification

```python
class IssueSeverity(Enum):
    """Issue severity levels."""

    CRITICAL = 5  # Security vulnerability, data loss
    HIGH = 4      # Core functionality broken
    MEDIUM = 3    # Feature impaired, workarounds exist
    LOW = 2       # Minor issues, best practices
    COSMETIC = 1  # Style, formatting

class IssueCategory(Enum):
    """Issue categories for routing."""

    SECURITY = "security"
    CORRECTNESS = "correctness"
    PERFORMANCE = "performance"
    TYPE_SAFETY = "type_safety"
    ERROR_HANDLING = "error_handling"
    CODING_STANDARDS = "coding_standards"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
```

#### Dynamic Loop Rules

```python
LOOP_RULES = {
    TaskType.IMPLEMENT: {
        IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
        IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
        IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
        IssueSeverity.LOW: {"max_iterations": 3, "action": "refactor"},
        IssueSeverity.COSMETIC: {"max_iterations": 3, "action": "auto-fix"},
    },
    TaskType.FIX: {
        IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
        IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
        IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
        IssueSeverity.LOW: {"max_iterations": 2, "action": "auto-fix"},
        IssueSeverity.COSMETIC: {"max_iterations": 2, "action": "auto-fix"},
    },
    TaskType.SECURITY: {
        IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
        IssueSeverity.HIGH: {"max_iterations": 0, "action": "security-audit"},
        # Security issues never loop - always escalate
    },
}
```

#### Auto-Fix Capability

```python
class AutoFixEngine:
    """Automatically fix certain issue types."""

    ISSUE_HANDLERS = {
        IssueCategory.CODING_STANDARDS: {
            "ruff_format": self._fix_formatting,
            "black_format": self._fix_formatting,
            "import_order": self._fix_imports,
        },
        IssueCategory.DOCUMENTATION: {
            "missing_docstring": self._add_docstring,
            "outdated_docs": self._update_docs,
        },
        IssueCategory.TYPE_SAFETY: {
            "missing_type": self._infer_type,
            "optional_required": self._add_optional,
        },
    }

    def can_auto_fix(self, issue: Issue) -> bool:
        """Check if issue is auto-fixable."""
        return (
            issue.category in self.ISSUE_HANDLERS and
            issue.severity in [IssueSeverity.LOW, IssueSeverity.COSMETIC]
        )
```

#### Loop Progress Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                    DYNAMIC LOOP STATUS                          │
├─────────────────────────────────────────────────────────────────┤
│ Chain: IMPLEMENT - OAuth2 Node                                  │
│ Iteration: 2/3                                                  │
│                                                                  │
│ Issues Found: 5                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ CRITICAL: 0 │ HIGH: 1 │ MEDIUM: 2 │ LOW: 2 │ COSMETIC: 0   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Loop Decision: CONTINUE (HIGH issue detected)                   │
│ Next Action: BUILDER - Fix HIGH severity issues                 │
│                                                                  │
│ Auto-Fixable: 2 issues (LOW category)                           │
│ Auto-Fixed: 1 issue (import order)                              │
│ Remaining: 1 issue (naming convention)                          │
│                                                                  │
│ Progress: ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  66%    │
│ Elapsed: 28 minutes                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Cross-Chain Dependencies

### Overview

Manage dependencies between chains when features require coordinated changes across multiple components. Prevents conflicts and ensures proper ordering.

### Features

#### Dependency Graph Management

```python
class DependencyManager:
    """Manages cross-chain dependencies."""

    def register_chain(
        self,
        chain_id: str,
        depends_on: List[str] = None,
        provides: List[str] = None
    ) -> DependencyGraph:
        """Register a chain with its dependencies."""

    def get_execution_order(self, chain_ids: List[str]) -> List[str]:
        """Get safe execution order for multiple chains."""
```

#### Dependency Types

```python
class DependencyType(Enum):
    """Types of dependencies between chains."""

    BLOCKING = 1  # Must complete before dependent can start
    BLOCKED_BY = 2  # Cannot start until dependency completes
    SHOULD_COMPLETE_BEFORE = 3  # Recommended order
    CONFLICTS_WITH = 4  # Cannot run in parallel
    CAN_RUN_PARALLEL = 5  # Safe to run in parallel

class DependencyStatus(Enum):
    """Status of a dependency."""

    PENDING = "pending"
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    FAILED = "failed"
    COMPLETED = "completed"
```

#### Dependency Declaration

```python
# When registering a chain, declare dependencies
chain_id = dependency_manager.register_chain(
    chain_id="chain-oauth2",
    depends_on=[
        Dependency(
            target="chain-base-http",
            type=DependencyType.BLOCKED_BY,
            reason="Needs HTTP client foundation"
        )
    ],
    provides=[
        ProvidedFeature(
            name="oauth2_authentication",
            description="OAuth2 authentication capability"
        )
    ]
)

# Check if chain can start
can_start, blocked_by = dependency_manager.can_start(chain_id)
```

#### Conflict Detection

```python
class ConflictDetector:
    """Detect and resolve conflicts between chains."""

    def detect_conflicts(
        self,
        chain_a: Chain,
        chain_b: Chain
    ) -> List[Conflict]:
        """Detect conflicts between two chains."""

    CONFLICT_TYPES = {
        "file_overwrite": "Both chains modify same file",
        "api_conflict": "Both modify same API endpoint",
        "schema_conflict": "Both change same data schema",
        "resource_conflict": "Both require exclusive resource",
    }

    def resolve_conflict(self, conflict: Conflict) -> Resolution:
        """Resolve a detected conflict."""
```

#### Execution Orchestrator

```python
class ChainOrchestrator:
    """Orchestrate execution of multiple dependent chains."""

    def execute_with_dependencies(
        self,
        chain_specs: List[ChainSpec],
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    ) -> ExecutionResult:
        """
        Execute multiple chains with dependency management.

        Strategies:
        - SEQUENTIAL: One at a time, in dependency order
        - PARALLEL: Independent chains run together
        - PIPELINED: Stage-based execution
        """

    # Example execution
    orchestrator = ChainOrchestrator()

    result = orchestrator.execute_with_dependencies([
        ChainSpec(
            task_type="implement",
            description="Base HTTP client",
            provides=["http_client"]
        ),
        ChainSpec(
            task_type="implement",
            description="OAuth2 authentication",
            depends_on=["http_client"]
        ),
        ChainSpec(
            task_type="implement",
            description="Google Sheets integration",
            depends_on=["oauth2_authentication"]
        ),
    ])
```

---

## 4. Cost Optimization

### Overview

Track and minimize token usage across chains, providing cost visibility and optimization suggestions.

### Features

#### Cost Tracking

```python
class CostTracker:
    """Track token usage and costs across chains."""

    def __init__(self):
        self.chain_costs: Dict[str, ChainCost] = {}
        self.agent_costs: Dict[str, AgentCost] = {}

    def record_usage(
        self,
        chain_id: str,
        agent: str,
        input_tokens: int,
        output_tokens: int,
        model: str
    ) -> CostEntry:
        """Record token usage for an agent."""
```

#### Cost Components

```python
@dataclass
class ChainCost:
    """Cost breakdown for a chain."""

    chain_id: str
    task_type: TaskType
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    estimated_cost: float  # USD
    agent_breakdown: Dict[str, AgentCost]
    optimization_suggestions: List[str]

@dataclass
class AgentCost:
    """Cost for a single agent execution."""

    agent_name: str
    input_tokens: int
    output_tokens: int
    duration_seconds: int
    iterations: int
    cost: float
```

#### Cost Model

```python
class CostModel:
    """Model for estimating and optimizing costs."""

    # Current pricing (per 1M tokens)
    MODEL_PRICES = {
        "gpt-4": {"input": 30.00, "output": 60.00},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
        "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
        "claude-3-sonnet": {"input": 3.00, "output": 15.00},
        "gemini-pro": {"input": 0.125, "output": 0.375},
    }

    def estimate_cost(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        model: str = "gpt-4-turbo"
    ) -> CostEstimate:
        """Estimate cost for a task type."""
```

#### Optimization Strategies

```python
class CostOptimizer:
    """Optimize chain execution for cost efficiency."""

    STRATEGIES = {
        "reduce_context": self._reduce_context_size,
        "parallel_execution": self._enable_parallel,
        "model_selection": self._select_cheaper_model,
        "early_termination": self._enable_early_stop,
        "caching": self._enable_result_caching,
    }

    def optimize(
        self,
        chain: ChainTemplate,
        budget: float = None
    ) -> OptimizedChain:
        """Generate cost-optimized chain execution plan."""
```

#### Cost Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                      COST DASHBOARD                             │
├─────────────────────────────────────────────────────────────────┤
│ Period: 2025-12-25                                              │
│                                                                  │
│ Total Spend: $4.32                                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Today's Spend:     $1.24                                     │ │
│ │ This Week:         $4.32                                     │ │
│ │ This Month:        $12.87                                    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ By Task Type:                                                   │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ implement  ████████████████░░░░░░░░░░░░░░  $2.10 (49%)      │ │
│ │ fix        ████████░░░░░░░░░░░░░░░░░░░░░░  $1.20 (28%)      │ │
│ │ refactor   ████░░░░░░░░░░░░░░░░░░░░░░░░░░  $0.45 (10%)      │ │
│ │ research   ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $0.32 (7%)       │ │
│ │ docs       █░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  $0.25 (6%)       │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Optimization Suggestions:                                       │
│ 1. Use gpt-4-turbo instead of gpt-4 (saves ~60%)               │
│ 2. Enable parallel execution for independent chains             │
│ 3. Reduce context in EXPLORE phase (save ~200 tokens/chain)    │
│                                                                  │
│ Budget Status: ████████████░░░░░░░  $5.68 remaining (68%)      │
└─────────────────────────────────────────────────────────────────┘
```

#### Optimization Rules

```python
COST_OPTIMIZATION_RULES = {
    "model_selection": {
        "explore": "gpt-4-turbo",  # Fast, cheap for search
        "architect": "claude-3-sonnet",  # Good for planning
        "builder": "claude-3-opus",  # Best for code
        "quality": "gpt-4-turbo",  # Fast for tests
        "reviewer": "claude-3-sonnet",  # Good for review
        "docs": "gpt-4-turbo",  # Fast for docs
    },
    "context_reduction": {
        "explore": {"max_tokens": 8000},
        "builder": {"max_tokens": 16000},
        "quality": {"max_tokens": 8000},
        "reviewer": {"max_tokens": 12000},
    },
    "early_termination": {
        "enable_for": ["docs", "test"],
        "conditions": ["high_confidence", "simple_task"],
    },
}
```

---

## 5. Predictive Timing

### Overview

Estimate completion times for chains based on historical data, task characteristics, and current system load.

### Features

#### Time Series Model

```python
class PredictiveTimer:
    """Predict chain completion times."""

    def __init__(self, history_store: HistoryStore):
        self.history = history_store
        self.model = self._load_model()

    def predict(
        self,
        task_type: TaskType,
        complexity: ComplexityLevel,
        chain_history: List[ChainExecution],
        current_load: SystemLoad
    ) -> TimePrediction:
        """Predict completion time for a chain."""
```

#### Prediction Features

| Feature | Description | Data Source |
|---------|-------------|-------------|
| **Historical Average** | Mean duration for task type | Chain history |
| **Complexity Factor** | Adjustment for complexity | Complexity scorer |
| **System Load** | Current system capacity | Monitoring |
| **Confidence Score** | Prediction reliability | Model output |
| **Variance** | Expected variation | Historical std dev |
| **Milestone Estimates** | Per-agent breakdowns | Agent-level data |

#### Prediction Output

```python
@dataclass
class TimePrediction:
    """Prediction for chain completion."""

    estimated_total_minutes: int
    confidence: float  # 0.0 to 1.0
    percentile_estimates: Dict[int, int]  # P50, P90, P99
    agent_breakdown: Dict[str, int]  # Per-agent estimates
    factors: List[PredictionFactor]  # What affected prediction
    recommendations: List[str]  # Speedup suggestions

@dataclass
class PredictionFactor:
    """Factor that influenced the prediction."""

    factor: str  # e.g., "system_load", "complexity"
    impact: float  # + or - percentage
    description: str
```

#### Milestone Tracking

```python
class MilestoneTracker:
    """Track and predict milestones during execution."""

    def predict_next_milestone(
        self,
        chain_id: str,
        current_state: ChainState
    ) -> MilestonePrediction:
        """Predict when next milestone will be reached."""

    def update_predictions(
        self,
        chain_id: str,
        actual: List[Milestone]
    ) -> None:
        """Update model with actual timing data."""
```

#### Timeline Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    PREDICTIVE TIMELINE                          │
├─────────────────────────────────────────────────────────────────┤
│ Chain: IMPLEMENT - OAuth2 Node                                  │
│                                                                  │
│ Total Estimate: 45 minutes (P50)                                │
│ Confidence: 0.85                                                │
│                                                                  │
│ Timeline:                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ EXPLORE    ████████████░░░░░░░░░░░░░░░░░░░░░░░░░  5 min    │ │
│ │ ARCHITECT  ██████████████████████████████░░░░░░░░  10 min   │ │
│ │ BUILDER    ████████████████████████████████████████  20 min  │ │
│ │ QUALITY    ████████████████████████░░░░░░░░░░░░░░  7 min    │ │
│ │ REVIEWER   ████████████████████░░░░░░░░░░░░░░░░░░  3 min    │ │
│ └─────────────────────────────────────────────────────────────┘ │ │
│                                                                  │
│ Milestones:                                                     │
│ 1. ✓ EXPLORE complete (5 min - on time)                        │
│ 2. ○ ARCHITECT 80% complete (8 min elapsed, 2 min remaining)  │
│ 3. ○ BUILDER not started (eta: +20 min from now)              │
│ 4. ○ QUALITY not started (eta: +30 min from now)              │
│ 5. ○ REVIEWER not started (eta: +40 min from now)             │
│                                                                  │
│ Speedup Suggestions:                                            │
│ • Run QUALITY in parallel with BUILD completion                 │
│ • System load is HIGH (+15% estimated time)                    │
│ • Use cache for similar patterns (save ~2 min)                 │
│                                                                  │
│ Updated: 2025-12-25 03:20 UTC                                   │
└─────────────────────────────────────────────────────────────────┘
```

#### Historical Pattern Learning

```python
class PatternLearner:
    """Learn from historical chain executions."""

    def learn_from_execution(self, execution: ChainExecution) -> None:
        """Update model with new execution data."""

    def get_patterns(self, task_type: TaskType) -> List[Pattern]:
        """Get learned patterns for task type."""

    PATTERNS = {
        "implement": [
            Pattern(
                name="high_confidence_estimate",
                description="Accurate when EXPLORE finds similar patterns",
                accuracy_improvement=0.15,
            ),
            Pattern(
                name="complexity_mismatch",
                description="Often underestimated for UI work",
                correction_factor=1.3,
            ),
        ],
        "fix": [
            Pattern(
                name="bug_fix_speed",
                description="Faster when similar bugs fixed before",
                speedup_factor=1.5,
            ),
        ],
    }
```

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENHANCED CHAIN ARCHITECTURE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Request                                                  │
│        │                                                        │
│        ▼                                                        │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  SMART CHAIN SELECTION                                       │ │
│ │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │ │
│ │  │ Intent Class │  │ Complexity   │  │ Context      │       │ │
│ │  │ (NLP)        │  │ Scorer       │  │ Awareness    │       │ │
│ │  └──────────────┘  └──────────────┘  └──────────────┘       │ │
│ └───────────────────────────┬──────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  DEPENDENCY MANAGER                                          │ │
│ │  Check for cross-chain dependencies                          │ │
│ │  Resolve conflicts                                           │ │
│ └───────────────────────────┬──────────────────────────────────┘ │
│                            │                                    │
│                            ▼                                    │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │  CHAIN ORCHESTRATOR                                          │ │
│ │  Execute with dependencies                                   │ │
│ │  Parallel where possible                                     │ │
│ └───────────────────────────┬──────────────────────────────────┘ │
│                            │                                    │
│        ┌───────────────────┼───────────────────┐                │
│        │                   │                   │                │
│        ▼                   ▼                   ▼                │
│ ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│ │ DYNAMIC     │    │ COST        │    │ PREDICTIVE  │          │
│ │ LOOP        │    │ OPTIMIZER   │    │ TIMER       │          │
│ │             │    │             │    │             │          │
│ │ - Severity  │    │ - Track     │    │ - Estimate  │          │
│ │ - Auto-fix  │    │ - Optimize  │    │ - Milestones│          │
│ │ - Escalate  │    │ - Dashboard │    │ - Patterns  │          │
│ └─────────────┘    └─────────────┘    └─────────────┘          │
│                            │                                    │
│                            ▼                                    │
│                    ┌─────────────┐                              │
│                    │ DASHBOARD   │                              │
│                    └─────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

| Phase | Feature | Timeline |
|-------|---------|----------|
| **Phase 1** | Cost Tracking & Optimization | Week 1 |
| **Phase 2** | Predictive Timing | Week 2 |
| **Phase 3** | Dynamic Loop Adjustment | Week 3 |
| **Phase 4** | Smart Chain Selection | Week 4 |
| **Phase 5** | Cross-Chain Dependencies | Week 5 |
| **Phase 6** | Integration & Testing | Week 6 |

---

## Backward Compatibility

All enhanced features are backward compatible:

```python
# Existing command still works
/chain implement "New feature"

/# Enhanced command (optional)
/chain implement "New feature" \
    --smart-select=true \
    --cost-budget=5.00 \
    --max-time=60 \
    --allow-dependencies=true
```

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
