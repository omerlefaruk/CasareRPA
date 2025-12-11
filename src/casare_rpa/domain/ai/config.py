"""
CasareRPA - AI Agent Configuration Module.

Provides configurable settings for SmartWorkflowAgent including:
- Performance optimization settings (parallelism, wait strategies)
- Prompt customization rules
- Error handling and retry policies
- Generation constraints

This module enables fine-tuning of AI workflow generation without
modifying core agent code.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    pass


class WaitStrategy(enum.Enum):
    """Strategy for handling waits in generated workflows."""

    # Never use hardcoded waits - always dynamic element detection
    NO_HARDCODED_WAITS = "no_hardcoded_waits"

    # Minimal waits - only when element detection is impossible
    MINIMAL_WAITS = "minimal_waits"

    # Smart waits - use WaitForElement/condition nodes extensively
    SMART_WAITS = "smart_waits"

    # Default - allow hardcoded waits when needed
    DEFAULT = "default"


class ParallelizationMode(enum.Enum):
    """How aggressively to parallelize workflow operations."""

    # Maximum parallelism - split into parallel branches whenever possible
    AGGRESSIVE = "aggressive"

    # Optimize for parallel execution where safe
    OPTIMIZED = "optimized"

    # Sequential execution - no parallelization
    SEQUENTIAL = "sequential"

    # Auto-detect based on operation types
    AUTO = "auto"


class ErrorHandlingMode(enum.Enum):
    """Error handling strategy for generated workflows."""

    # Wrap every external operation in try-catch
    PARANOID = "paranoid"

    # Wrap critical operations only
    CRITICAL_ONLY = "critical_only"

    # Minimal error handling
    MINIMAL = "minimal"

    # No error handling (fastest but risky)
    NONE = "none"


@dataclass
class PromptRules:
    """
    Configurable rules that customize prompt generation.

    These rules are injected into system prompts to guide
    the AI's workflow generation behavior.
    """

    # Custom rules to append to system prompt
    custom_rules: List[str] = field(default_factory=list)

    # Required node types that must be included
    required_node_types: List[str] = field(default_factory=list)

    # Forbidden node types that must NOT be used
    forbidden_node_types: List[str] = field(default_factory=list)

    # Selector strategy preference
    selector_priority: List[str] = field(
        default_factory=lambda: [
            "data-testid",
            "data-cy",
            "aria-label",
            "id",
            "name",
            "class",
        ]
    )

    # Whether to include debug nodes
    include_debug_nodes: bool = True

    # Whether to include validation nodes (IfElse for checks)
    include_validation_nodes: bool = True

    # Maximum workflow complexity (node count)
    max_nodes: int = 50

    # Whether to allow loops
    allow_loops: bool = True

    # Whether to allow branching (IfElse)
    allow_branching: bool = True

    def to_prompt_text(self) -> str:
        """Convert rules to prompt text for injection."""
        lines = []

        if self.custom_rules:
            lines.append("## Custom Rules")
            for rule in self.custom_rules:
                lines.append(f"- {rule}")
            lines.append("")

        if self.required_node_types:
            lines.append("## Required Node Types")
            lines.append(
                f"You MUST include these nodes: {', '.join(self.required_node_types)}"
            )
            lines.append("")

        if self.forbidden_node_types:
            lines.append("## Forbidden Node Types")
            lines.append(
                f"NEVER use these nodes: {', '.join(self.forbidden_node_types)}"
            )
            lines.append("")

        if self.selector_priority:
            lines.append("## Selector Priority")
            lines.append("When choosing selectors, prefer in this order:")
            for i, sel in enumerate(self.selector_priority, 1):
                lines.append(f"  {i}. {sel}")
            lines.append("")

        if self.max_nodes < 100:
            lines.append("## Complexity Limit")
            lines.append(f"Maximum {self.max_nodes} nodes per workflow.")
            lines.append("")

        if not self.allow_loops:
            lines.append("## No Loops")
            lines.append(
                "Do NOT use ForLoopStartNode, WhileLoopNode, or any loop constructs."
            )
            lines.append("")

        if not self.allow_branching:
            lines.append("## No Branching")
            lines.append("Do NOT use IfNode, IfElseNode, or branching constructs.")
            lines.append("")

        return "\n".join(lines)


@dataclass
class PerformanceConfig:
    """
    Performance optimization settings for workflow generation.

    These settings guide the AI to generate workflows optimized
    for fast execution with minimal blocking operations.
    """

    # Wait strategy
    wait_strategy: WaitStrategy = WaitStrategy.SMART_WAITS

    # Parallelization mode
    parallelization: ParallelizationMode = ParallelizationMode.OPTIMIZED

    # Maximum hardcoded wait time in ms (0 = disabled)
    max_hardcoded_wait_ms: int = 0

    # Default element wait timeout in ms
    element_wait_timeout_ms: int = 5000

    # Whether to use page load detection instead of fixed waits
    use_page_load_detection: bool = True

    # Whether to use element visibility detection
    use_element_visibility_detection: bool = True

    # Whether to batch similar operations
    batch_similar_operations: bool = True

    # Whether to prefetch data where possible
    enable_prefetch: bool = True

    # Maximum parallel branches
    max_parallel_branches: int = 5

    # Whether to optimize selector lookup order
    optimize_selectors: bool = True

    def to_prompt_text(self) -> str:
        """Convert performance config to prompt instructions."""
        lines = ["## Performance Optimization Rules"]

        if self.wait_strategy == WaitStrategy.NO_HARDCODED_WAITS:
            lines.extend(
                [
                    "- NEVER use WaitNode with hardcoded duration_ms",
                    "- ALWAYS use WaitForElementNode or WaitForConditionNode instead",
                    "- Use page.waitForLoadState('networkidle') concepts via appropriate nodes",
                ]
            )
        elif self.wait_strategy == WaitStrategy.MINIMAL_WAITS:
            lines.extend(
                [
                    "- Minimize WaitNode usage - only when absolutely necessary",
                    "- Prefer WaitForElementNode with smart selectors",
                    f"- Maximum hardcoded wait: {self.max_hardcoded_wait_ms}ms",
                ]
            )
        elif self.wait_strategy == WaitStrategy.SMART_WAITS:
            lines.extend(
                [
                    "- Use WaitForElementNode before ALL element interactions",
                    "- Use state='visible' or state='attached' as appropriate",
                    f"- Default timeout: {self.element_wait_timeout_ms}ms",
                ]
            )

        if self.parallelization == ParallelizationMode.AGGRESSIVE:
            lines.extend(
                [
                    "",
                    "## Parallel Execution",
                    "- Split independent operations into parallel branches using ParallelStartNode",
                    "- Group related operations that can run simultaneously",
                    f"- Maximum {self.max_parallel_branches} parallel branches",
                ]
            )
        elif self.parallelization == ParallelizationMode.OPTIMIZED:
            lines.extend(
                [
                    "",
                    "## Parallel Execution",
                    "- Use ParallelStartNode for independent data fetches",
                    "- Keep UI interactions sequential to avoid race conditions",
                    "- Parallelize file/API operations when possible",
                ]
            )

        if self.use_page_load_detection:
            lines.append(
                "- Use page load detection (NavigateNode with wait_until) instead of fixed waits"
            )

        if self.optimize_selectors:
            lines.extend(
                [
                    "",
                    "## Selector Optimization",
                    "- Prefer ID and data-* selectors (fastest)",
                    "- Avoid complex CSS selectors with multiple combinators",
                    "- Use XPath only when CSS cannot express the selection",
                ]
            )

        if self.batch_similar_operations:
            lines.extend(
                [
                    "",
                    "## Operation Batching",
                    "- Group similar operations (multiple clicks, multiple type actions)",
                    "- Use batch nodes when available (BatchClickNode, etc.)",
                ]
            )

        return "\n".join(lines)


@dataclass
class RetryConfig:
    """Configuration for retry behavior on failures."""

    # Maximum LLM generation retries
    max_generation_retries: int = 3

    # Maximum validation repair attempts
    max_repair_attempts: int = 2

    # Temperature increase per retry
    temperature_increment: float = 0.1

    # Maximum temperature
    max_temperature: float = 0.7

    # Base retry delay in seconds
    base_retry_delay: float = 1.0

    # Whether to use exponential backoff
    exponential_backoff: bool = True

    # Backoff multiplier
    backoff_multiplier: float = 2.0

    # Maximum retry delay
    max_retry_delay: float = 30.0


@dataclass
class AgentConfig:
    """
    Complete configuration for SmartWorkflowAgent.

    This dataclass aggregates all configurable aspects of the AI workflow
    generation system, enabling fine-grained control over behavior.

    Example:
        config = AgentConfig(
            performance=PerformanceConfig(
                wait_strategy=WaitStrategy.NO_HARDCODED_WAITS,
                parallelization=ParallelizationMode.AGGRESSIVE,
            ),
            prompt_rules=PromptRules(
                custom_rules=["Always include error screenshots on failure"],
                forbidden_node_types=["WaitNode"],
            ),
            error_handling=ErrorHandlingMode.PARANOID,
        )
        agent = SmartWorkflowAgent(config=config)
    """

    # Performance settings
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)

    # Prompt customization rules
    prompt_rules: PromptRules = field(default_factory=PromptRules)

    # Retry configuration
    retry: RetryConfig = field(default_factory=RetryConfig)

    # Error handling mode
    error_handling: ErrorHandlingMode = ErrorHandlingMode.CRITICAL_ONLY

    # LLM model to use
    model: str = "gpt-4o-mini"

    # Base temperature for generation
    temperature: float = 0.2

    # Maximum tokens in response
    max_tokens: int = 4000

    # Whether to include robustness instructions in prompts
    include_robustness_instructions: bool = True

    # Whether to allow missing node protocol
    allow_node_creation_requests: bool = True

    # Whether to strip Start/End nodes from generated output
    strip_start_end_nodes: bool = True

    # Whether to validate workflows before returning
    validate_before_return: bool = True

    # Custom system prompt override (if set, replaces default)
    custom_system_prompt: Optional[str] = None

    # Additional context to include in prompts
    additional_context: str = ""

    # Callback for logging/monitoring
    on_generation_attempt: Optional[Callable[[int, str], None]] = None
    on_validation_error: Optional[Callable[[str, List[str]], None]] = None
    on_success: Optional[Callable[[Dict[str, Any], int], None]] = None

    def get_effective_temperature(self, attempt: int) -> float:
        """Calculate temperature for a given retry attempt."""
        temp = self.temperature + (attempt * self.retry.temperature_increment)
        return min(temp, self.retry.max_temperature)

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay for a given attempt."""
        if not self.retry.exponential_backoff:
            return self.retry.base_retry_delay

        delay = self.retry.base_retry_delay * (self.retry.backoff_multiplier**attempt)
        return min(delay, self.retry.max_retry_delay)

    def build_performance_prompt(self) -> str:
        """Build performance-focused prompt section."""
        return self.performance.to_prompt_text()

    def build_rules_prompt(self) -> str:
        """Build custom rules prompt section."""
        return self.prompt_rules.to_prompt_text()

    def build_error_handling_prompt(self) -> str:
        """Build error handling instructions."""
        lines = ["## Error Handling Requirements"]

        if self.error_handling == ErrorHandlingMode.PARANOID:
            lines.extend(
                [
                    "- Wrap EVERY external operation in TryCatchNode",
                    "- External operations: browser actions, file I/O, HTTP, database",
                    "- Log errors with DebugNode before error_out path",
                    "- Include fallback values for all critical variables",
                    "- Add validation before every operation (IfElseNode)",
                ]
            )
        elif self.error_handling == ErrorHandlingMode.CRITICAL_ONLY:
            lines.extend(
                [
                    "- Wrap critical operations in TryCatchNode:",
                    "  - Navigation and page loads",
                    "  - Form submissions",
                    "  - File write operations",
                    "  - API calls",
                    "- Non-critical operations can omit try-catch",
                ]
            )
        elif self.error_handling == ErrorHandlingMode.MINIMAL:
            lines.extend(
                [
                    "- Use TryCatchNode only for the main workflow block",
                    "- Focus on completing the happy path efficiently",
                ]
            )
        elif self.error_handling == ErrorHandlingMode.NONE:
            lines.extend(
                [
                    "- Do NOT include TryCatchNode wrappers",
                    "- Generate the simplest possible workflow",
                ]
            )

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize config to dictionary."""
        return {
            "performance": {
                "wait_strategy": self.performance.wait_strategy.value,
                "parallelization": self.performance.parallelization.value,
                "max_hardcoded_wait_ms": self.performance.max_hardcoded_wait_ms,
                "element_wait_timeout_ms": self.performance.element_wait_timeout_ms,
            },
            "prompt_rules": {
                "custom_rules": self.prompt_rules.custom_rules,
                "required_node_types": self.prompt_rules.required_node_types,
                "forbidden_node_types": self.prompt_rules.forbidden_node_types,
                "max_nodes": self.prompt_rules.max_nodes,
            },
            "retry": {
                "max_generation_retries": self.retry.max_generation_retries,
                "max_repair_attempts": self.retry.max_repair_attempts,
            },
            "error_handling": self.error_handling.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Create config from dictionary."""
        perf_data = data.get("performance", {})
        rules_data = data.get("prompt_rules", {})
        retry_data = data.get("retry", {})

        return cls(
            performance=PerformanceConfig(
                wait_strategy=WaitStrategy(
                    perf_data.get("wait_strategy", "smart_waits")
                ),
                parallelization=ParallelizationMode(
                    perf_data.get("parallelization", "optimized")
                ),
                max_hardcoded_wait_ms=perf_data.get("max_hardcoded_wait_ms", 0),
                element_wait_timeout_ms=perf_data.get("element_wait_timeout_ms", 5000),
            ),
            prompt_rules=PromptRules(
                custom_rules=rules_data.get("custom_rules", []),
                required_node_types=rules_data.get("required_node_types", []),
                forbidden_node_types=rules_data.get("forbidden_node_types", []),
                max_nodes=rules_data.get("max_nodes", 50),
            ),
            retry=RetryConfig(
                max_generation_retries=retry_data.get("max_generation_retries", 3),
                max_repair_attempts=retry_data.get("max_repair_attempts", 2),
            ),
            error_handling=ErrorHandlingMode(
                data.get("error_handling", "critical_only")
            ),
            model=data.get("model", "gpt-4o-mini"),
            temperature=data.get("temperature", 0.2),
            max_tokens=data.get("max_tokens", 4000),
        )


# Pre-configured profiles for common use cases

PERFORMANCE_OPTIMIZED_CONFIG = AgentConfig(
    performance=PerformanceConfig(
        wait_strategy=WaitStrategy.NO_HARDCODED_WAITS,
        parallelization=ParallelizationMode.AGGRESSIVE,
        max_hardcoded_wait_ms=0,
        batch_similar_operations=True,
        enable_prefetch=True,
    ),
    prompt_rules=PromptRules(
        forbidden_node_types=["WaitNode"],
        custom_rules=[
            "NEVER use hardcoded wait times",
            "Prefer parallel execution over sequential",
            "Use batch operations when processing multiple elements",
        ],
    ),
    error_handling=ErrorHandlingMode.CRITICAL_ONLY,
)


RELIABILITY_FOCUSED_CONFIG = AgentConfig(
    performance=PerformanceConfig(
        wait_strategy=WaitStrategy.SMART_WAITS,
        parallelization=ParallelizationMode.SEQUENTIAL,
        element_wait_timeout_ms=10000,
    ),
    prompt_rules=PromptRules(
        required_node_types=["TryCatchNode", "DebugNode"],
        include_debug_nodes=True,
        include_validation_nodes=True,
    ),
    error_handling=ErrorHandlingMode.PARANOID,
)


SIMPLE_FAST_CONFIG = AgentConfig(
    performance=PerformanceConfig(
        wait_strategy=WaitStrategy.MINIMAL_WAITS,
        parallelization=ParallelizationMode.SEQUENTIAL,
    ),
    prompt_rules=PromptRules(
        include_debug_nodes=False,
        include_validation_nodes=False,
        max_nodes=20,
    ),
    error_handling=ErrorHandlingMode.MINIMAL,
    temperature=0.1,
)


__all__ = [
    "AgentConfig",
    "PerformanceConfig",
    "PromptRules",
    "RetryConfig",
    "WaitStrategy",
    "ParallelizationMode",
    "ErrorHandlingMode",
    "PERFORMANCE_OPTIMIZED_CONFIG",
    "RELIABILITY_FOCUSED_CONFIG",
    "SIMPLE_FAST_CONFIG",
]
