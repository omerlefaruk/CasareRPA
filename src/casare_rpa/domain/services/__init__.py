"""
CasareRPA - Domain Services

Domain services contain business logic that doesn't naturally fit in entities or value objects.
"""

# Parallel agent framework services
from casare_rpa.domain.services.agent_scheduler import (
    AgentScheduler,
    Schedule,
    ScheduledPhase,
)
from casare_rpa.domain.services.decomposition_engine import DecompositionEngine
from casare_rpa.domain.services.execution_orchestrator import ExecutionOrchestrator
from casare_rpa.domain.services.expression_evaluator import (
    ExpressionError,
    ExpressionEvaluator,
    evaluate_expression,
    get_expression_evaluator,
    has_expressions,
)
from casare_rpa.domain.services.project_context import ProjectContext
from casare_rpa.domain.services.task_analyzer import TaskAnalyzer, WorkItem
from casare_rpa.domain.services.variable_resolver import (
    VARIABLE_PATTERN,
    extract_variable_names,
    has_variables,
    resolve_dict_variables,
    resolve_variables,
)
from casare_rpa.domain.validation import (
    ValidationIssue,
    ValidationResult,
    ValidationSeverity,
    get_valid_node_types,
    quick_validate,
    validate_connections,
    validate_node,
    validate_workflow,
)

__all__ = [
    "ExecutionOrchestrator",
    "ProjectContext",
    # Parallel agent framework
    "TaskAnalyzer",
    "WorkItem",
    "DecompositionEngine",
    "AgentScheduler",
    "Schedule",
    "ScheduledPhase",
    # Variable resolver
    "VARIABLE_PATTERN",
    "resolve_variables",
    "resolve_dict_variables",
    "extract_variable_names",
    "has_variables",
    # Expression evaluator (Power Automate style)
    "ExpressionEvaluator",
    "ExpressionError",
    "get_expression_evaluator",
    "evaluate_expression",
    "has_expressions",
    # Validation
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "validate_workflow",
    "validate_node",
    "validate_connections",
    "quick_validate",
    "get_valid_node_types",
]
