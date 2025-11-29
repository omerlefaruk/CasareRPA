"""
CasareRPA - Domain Workflow Module
Workflow versioning, migration, lifecycle management, and templates.
"""

from .versioning import (
    SemanticVersion,
    VersionStatus,
    WorkflowVersion,
    VersionHistory,
    VersionDiff,
    BreakingChange,
    BreakingChangeType,
    CompatibilityResult,
)
from .templates import (
    TemplateCategory,
    TemplateParameter,
    TemplateParameterType,
    WorkflowTemplate,
    TemplateMetadata,
    TemplateUsageStats,
    TemplateReview,
    TemplateVersion,
    ReviewStatus,
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
    # Templates
    "TemplateCategory",
    "TemplateParameter",
    "TemplateParameterType",
    "WorkflowTemplate",
    "TemplateMetadata",
    "TemplateUsageStats",
    "TemplateReview",
    "TemplateVersion",
    "ReviewStatus",
]
