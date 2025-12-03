"""
CasareRPA - Base Error Handler.

Abstract base class for error handlers.
"""

from abc import ABC, abstractmethod

from casare_rpa.domain.errors.context import ErrorContext, RecoveryDecision


class ErrorHandler(ABC):
    """
    Abstract base class for error handlers.

    Error handlers analyze errors and recommend recovery actions.
    Subclasses implement domain-specific error handling logic.
    """

    @abstractmethod
    def can_handle(self, context: ErrorContext) -> bool:
        """
        Check if this handler can handle the given error.

        Args:
            context: Error context to evaluate.

        Returns:
            True if this handler should process the error.
        """
        pass

    @abstractmethod
    def classify(self, context: ErrorContext) -> ErrorContext:
        """
        Classify the error (set classification, category, severity).

        Args:
            context: Error context to classify.

        Returns:
            Updated error context with classification.
        """
        pass

    @abstractmethod
    def decide_recovery(self, context: ErrorContext) -> RecoveryDecision:
        """
        Decide recovery action for the error.

        Args:
            context: Classified error context.

        Returns:
            Recovery decision with recommended action.
        """
        pass


__all__ = ["ErrorHandler"]
