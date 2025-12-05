"""
CasareRPA - Domain Workflow Module
Workflow versioning, migration, and lifecycle management.
"""

from casare_rpa.domain.workflow.versioning import (
    BreakingChange,
    BreakingChangeType,
    CompatibilityResult,
    SemanticVersion,
    VersionDiff,
    VersionHistory,
    VersionStatus,
    WorkflowVersion,
)

__all__ = [
    # Versioning
    "SemanticVersion",
    "VersionStatus",
    "WorkflowVersion",
    "VersionHistory",
    "VersionDiff",
    "BreakingChange",
    "BreakingChangeType",
    "CompatibilityResult",
]
