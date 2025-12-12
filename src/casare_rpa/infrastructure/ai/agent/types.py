"""
Data types for AI agent workflow generation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from casare_rpa.domain.validation import ValidationResult


@dataclass
class GenerationAttempt:
    """Record of a single generation attempt."""

    attempt_number: int
    timestamp: float
    success: bool
    temperature: float
    duration_ms: float
    error: Optional[str] = None
    validation_result: Optional[ValidationResult] = None
    token_usage: Optional[Dict[str, int]] = None


@dataclass
class WorkflowGenerationResult:
    """
    Result of a workflow generation attempt.

    Attributes:
        success: Whether generation succeeded
        workflow: Generated workflow dict (if success)
        attempts: Number of generation attempts made
        error: Error message if failed
        validation_history: List of validation results from each attempt
        generation_time_ms: Total time taken for generation
        attempt_history: Detailed history of each attempt
        raw_response: Raw LLM response text (for debugging)
    """

    success: bool
    workflow: Optional[Dict[str, Any]] = None
    attempts: int = 0
    error: Optional[str] = None
    validation_history: List[ValidationResult] = field(default_factory=list)
    generation_time_ms: float = 0.0
    attempt_history: List[GenerationAttempt] = field(default_factory=list)
    raw_response: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "success": self.success,
            "workflow": self.workflow,
            "attempts": self.attempts,
            "error": self.error,
            "generation_time_ms": self.generation_time_ms,
            "validation_history": [v.to_dict() for v in self.validation_history],
            "attempt_history": [
                {
                    "attempt": a.attempt_number,
                    "success": a.success,
                    "duration_ms": a.duration_ms,
                    "error": a.error,
                }
                for a in self.attempt_history
            ],
            "raw_response": self.raw_response,
        }
