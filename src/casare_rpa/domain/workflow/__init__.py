"""
CasareRPA - Domain Workflow Module
Workflow versioning, migration, lifecycle management, and templates.
"""

from casare_rpa.domain.workflow.templates import (
    ReviewStatus,
    TemplateCategory,
    TemplateMetadata,
    TemplateParameter,
    TemplateParameterType,
    TemplateReview,
    TemplateUsageStats,
    TemplateVersion,
    WorkflowTemplate,
)
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
