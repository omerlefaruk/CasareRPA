"""
Dynamic Loop Manager - Auto-adjust loop iterations based on issue severity.

This service provides:
- Severity-based loop control
- Auto-fix for certain issue types
- Escalation for critical issues
"""

import re
from typing import Any

from casare_rpa.domain.logging import get_domain_logger

logger = get_domain_logger()

from casare_rpa.domain.entities.chain_types import (
    Issue,
    IssueCategory,
    IssueSeverity,
    LoopDecision,
    TaskType,
)


class IssueSeverityClassifier:
    """Classify issue severity for loop decisions."""

    # Severity keywords for classification
    SEVERITY_KEYWORDS: dict[IssueSeverity, list[str]] = {
        IssueSeverity.CRITICAL: [
            "security",
            "vulnerability",
            "data loss",
            "breach",
            "unauthenticated",
            "injection",
            "privilege escalation",
            "critical",
            "emergency",
            "immediate",
        ],
        IssueSeverity.HIGH: [
            "broken",
            "failing",
            "crash",
            "error",
            "bug",
            "memory leak",
            "deadlock",
            "data corruption",
            "severe",
            "major",
            "important",
        ],
        IssueSeverity.MEDIUM: [
            "impaired",
            "workaround",
            "partial",
            "inconsistent",
            "performance degradation",
            "race condition potential",
            "moderate",
            "significant",
        ],
        IssueSeverity.LOW: [
            "minor",
            "best practice",
            "suggestion",
            "warning",
            "cosmetic",
            "styling",
            "documentation improvement",
            "enhancement",
            "nice to have",
        ],
        IssueSeverity.COSMETIC: [
            "style",
            "formatting",
            "typo",
            "spelling",
            "whitespace",
            "indentation",
            "naming convention",
            "trivial",
            "superficial",
        ],
    }

    # Category-based severity defaults
    CATEGORY_SEVERITY: dict[IssueCategory, IssueSeverity] = {
        IssueCategory.SECURITY: IssueSeverity.CRITICAL,
        IssueCategory.CORRECTNESS: IssueSeverity.HIGH,
        IssueCategory.PERFORMANCE: IssueSeverity.MEDIUM,
        IssueCategory.TYPE_SAFETY: IssueSeverity.HIGH,
        IssueCategory.ERROR_HANDLING: IssueSeverity.MEDIUM,
        IssueCategory.CODING_STANDARDS: IssueSeverity.LOW,
        IssueCategory.DOCUMENTATION: IssueSeverity.LOW,
        IssueCategory.ARCHITECTURE: IssueSeverity.MEDIUM,
        IssueCategory.TESTING: IssueSeverity.LOW,
    }

    def classify_severity(self, issue: Issue) -> IssueSeverity:
        """
        Classify the severity of an issue.

        Args:
            issue: The issue to classify

        Returns:
            IssueSeverity level
        """
        # First check explicit category
        if issue.category in self.CATEGORY_SEVERITY:
            category_severity = self.CATEGORY_SEVERITY[issue.category]

            # Check for keywords that might increase severity
            description_lower = issue.description.lower()

            # Check for critical keywords that could elevate severity
            critical_keywords = self.SEVERITY_KEYWORDS[IssueSeverity.CRITICAL]
            if any(kw in description_lower for kw in critical_keywords):
                return IssueSeverity.CRITICAL

            # Check for high severity keywords
            high_keywords = self.SEVERITY_KEYWORDS[IssueSeverity.HIGH]
            if any(kw in description_lower for kw in high_keywords):
                return IssueSeverity.HIGH

            return category_severity

        # Fallback: keyword-based classification
        description_lower = issue.description.lower()

        for severity, keywords in self.SEVERITY_KEYWORDS.items():
            if any(kw in description_lower for kw in keywords):
                return severity

        # Default to LOW if no keywords match
        return IssueSeverity.LOW

    def classify_severity_from_description(
        self, description: str, category: IssueCategory | None = None
    ) -> IssueSeverity:
        """
        Classify severity from description text.

        Args:
            description: The issue description
            category: Optional category hint

        Returns:
            IssueSeverity level
        """
        # Create a mock issue for classification
        mock_issue = Issue(
            issue_id="temp",
            category=category or IssueCategory.CODING_STANDARDS,
            severity=IssueSeverity.LOW,
            description=description,
            file_path="",
            line_number=0,
        )
        return self.classify_severity(mock_issue)


class AutoFixEngine:
    """Automatically fix certain issue types."""

    # Issue handlers by category
    ISSUE_HANDLERS: dict[IssueCategory, dict[str, str]] = {
        IssueCategory.CODING_STANDARDS: {
            "ruff_format": "Format code with ruff",
            "black_format": "Format code with black",
            "import_order": "Fix import order",
            "line_length": "Adjust line length",
            "naming_convention": "Fix naming convention",
        },
        IssueCategory.DOCUMENTATION: {
            "missing_docstring": "Add docstring",
            "outdated_docs": "Update documentation",
            "type_hint_doc": "Add type hints to docs",
        },
        IssueCategory.TYPE_SAFETY: {
            "missing_type": "Add type hint",
            "optional_required": "Add Optional wrapper",
            "any_type": "Replace Any with specific type",
        },
    }

    # Auto-fixable issue patterns
    AUTO_FIX_PATTERNS: dict[str, tuple[IssueCategory, str, list[str]]] = {
        "import order": (
            IssueCategory.CODING_STANDARDS,
            "import_order",
            [r"import.*\n.*import", r"from.*\n.*from"],
        ),
        "line too long": (IssueCategory.CODING_STANDARDS, "line_length", [r".{121,}"]),
        "missing docstring": (
            IssueCategory.DOCUMENTATION,
            "missing_docstring",
            [r"def \w+\([^)]*\):\s*(?!\s*\"\"\")"],
        ),
        "type hint": (IssueCategory.TYPE_SAFETY, "missing_type", [r"def \w+\([^)]*\):(?!\s*->)"]),
    }

    def can_auto_fix(self, issue: Issue) -> bool:
        """
        Check if an issue can be auto-fixed.

        Args:
            issue: The issue to check

        Returns:
            True if the issue is auto-fixable
        """
        # Check if category has handlers
        if issue.category not in self.ISSUE_HANDLERS:
            return False

        # Check severity (only LOW and COSMETIC are auto-fixable)
        if issue.severity not in [IssueSeverity.LOW, IssueSeverity.COSMETIC]:
            return False

        # Check if suggestion matches a known handler
        category_handlers = self.ISSUE_HANDLERS[issue.category]
        suggestion_lower = issue.suggestion.lower()

        for handler_key in category_handlers:
            if handler_key in suggestion_lower:
                return True

        # Check against patterns
        for pattern_name, (category, handler, regex_list) in self.AUTO_FIX_PATTERNS.items():
            if category == issue.category:
                for regex in regex_list:
                    if re.search(regex, issue.description, re.IGNORECASE):
                        return True

        return False

    def auto_fix(self, issue: Issue) -> dict[str, Any]:
        """
        Apply auto-fix to an issue.

        Args:
            issue: The issue to fix

        Returns:
            Dict with fix result and details
        """
        if not self.can_auto_fix(issue):
            return {
                "success": False,
                "message": "Issue is not auto-fixable",
                "issue_id": issue.issue_id,
            }

        # Determine the fix type
        fix_type = self._determine_fix_type(issue)

        # Apply fix based on type
        fix_result = self._apply_fix(issue, fix_type)

        return {
            "success": True,
            "message": f"Auto-fixed: {fix_type}",
            "issue_id": issue.issue_id,
            "fix_type": fix_type,
            "changes": fix_result,
        }

    def _determine_fix_type(self, issue: Issue) -> str:
        """Determine the type of fix to apply."""
        category_handlers = self.ISSUE_HANDLERS.get(issue.category, {})

        for handler_key in category_handlers:
            if handler_key in issue.suggestion.lower():
                return handler_key

        # Check patterns
        for pattern_name, (category, handler, regex_list) in self.AUTO_FIX_PATTERNS.items():
            if category == issue.category:
                for regex in regex_list:
                    if re.search(regex, issue.description, re.IGNORECASE):
                        return handler

        return "unknown"

    def _apply_fix(self, issue: Issue, fix_type: str) -> dict[str, Any]:
        """Apply the specific fix."""
        # In a real implementation, this would modify the file
        # For now, return the fix details
        return {
            "file": issue.file_path,
            "line": issue.line_number,
            "fix_description": f"Applied {fix_type} fix",
            "preview": f"# Auto-fix at {issue.file_path}:{issue.line_number}\n# {fix_type}",
        }


# Default loop rules for task types not explicitly defined
_DEFAULT_LOOP_RULES: dict[IssueSeverity, dict[str, Any]] = {
    IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
    IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
    IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
    IssueSeverity.LOW: {"max_iterations": 3, "action": "auto-fix"},
    IssueSeverity.COSMETIC: {"max_iterations": 3, "action": "auto-fix"},
}


class DynamicLoopManager:
    """Manage loop iterations based on issue characteristics."""

    # Loop rules by task type and severity
    LOOP_RULES: dict[TaskType | str, dict[IssueSeverity, dict[str, Any]]] = {
        TaskType.IMPLEMENT: {
            IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
            IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
            IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
            IssueSeverity.LOW: {"max_iterations": 3, "action": "auto-fix"},
            IssueSeverity.COSMETIC: {"max_iterations": 3, "action": "auto-fix"},
        },
        TaskType.FIX: {
            IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
            IssueSeverity.HIGH: {"max_iterations": 1, "action": "builder"},
            IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "builder"},
            IssueSeverity.LOW: {"max_iterations": 2, "action": "auto-fix"},
            IssueSeverity.COSMETIC: {"max_iterations": 2, "action": "auto-fix"},
        },
        TaskType.REFACTOR: {
            IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
            IssueSeverity.HIGH: {"max_iterations": 1, "action": "refactor"},
            IssueSeverity.MEDIUM: {"max_iterations": 2, "action": "refactor"},
            IssueSeverity.LOW: {"max_iterations": 2, "action": "auto-fix"},
            IssueSeverity.COSMETIC: {"max_iterations": 2, "action": "auto-fix"},
        },
        TaskType.SECURITY: {
            IssueSeverity.CRITICAL: {"max_iterations": 0, "action": "escalate"},
            IssueSeverity.HIGH: {"max_iterations": 0, "action": "security-audit"},
            IssueSeverity.MEDIUM: {"max_iterations": 1, "action": "security-audit"},
            IssueSeverity.LOW: {"max_iterations": 2, "action": "auto-fix"},
            IssueSeverity.COSMETIC: {"max_iterations": 2, "action": "auto-fix"},
        },
        # Default rules for other task types
        "default": _DEFAULT_LOOP_RULES,
    }

    def __init__(self):
        self.severity_classifier = IssueSeverityClassifier()
        self.auto_fix_engine = AutoFixEngine()
        logger.info("DynamicLoopManager initialized")

    def should_continue_loop(
        self, issues: list[Issue], iteration: int, task_type: TaskType
    ) -> LoopDecision:
        """
        Determine if looping should continue based on issues.

        Args:
            issues: List of issues from reviewer
            iteration: Current iteration number (0-based)
            task_type: The task type being executed

        Returns:
            LoopDecision with action to take
        """
        if not issues:
            return LoopDecision(
                should_continue=False,
                action="complete",
                max_iterations=0,
                current_iteration=iteration,
                reason="No issues found, chain complete",
            )

        # Classify severity for all issues
        classified_issues = []
        for issue in issues:
            severity = self.severity_classifier.classify_severity(issue)
            classified_issue = Issue(
                issue_id=issue.issue_id,
                category=issue.category,
                severity=severity,
                description=issue.description,
                file_path=issue.file_path,
                line_number=issue.line_number,
                suggestion=issue.suggestion,
                auto_fixable=self.auto_fix_engine.can_auto_fix(issue),
            )
            classified_issues.append(classified_issue)

        # Get rules for task type (use "default" if task_type not found)
        rules = self.LOOP_RULES.get(task_type, self.LOOP_RULES["default"])

        # Group issues by severity
        issues_by_severity: dict[IssueSeverity, list[Issue]] = {}
        for issue in classified_issues:
            if issue.severity not in issues_by_severity:
                issues_by_severity[issue.severity] = []
            issues_by_severity[issue.severity].append(issue)

        # Check for critical issues (immediate escalation)
        if IssueSeverity.CRITICAL in issues_by_severity:
            critical_count = len(issues_by_severity[IssueSeverity.CRITICAL])
            return LoopDecision(
                should_continue=False,
                action="escalate",
                max_iterations=0,
                current_iteration=iteration,
                reason=f"Found {critical_count} CRITICAL issue(s) - immediate escalation required",
                issues_by_severity=issues_by_severity,
            )

        # Determine the appropriate action based on highest severity
        highest_severity = max(issues_by_severity.keys())
        issues_by_severity[highest_severity]
        rule = rules.get(highest_severity, _DEFAULT_LOOP_RULES[highest_severity])

        max_allowed = rule["max_iterations"]
        action = rule["action"]

        # Check if we've exceeded max iterations
        if iteration >= max_allowed:
            return LoopDecision(
                should_continue=False,
                action="escalate",
                max_iterations=max_allowed,
                current_iteration=iteration,
                reason=f"Reached maximum iterations ({max_allowed}) for {highest_severity.name} issues",
                issues_by_severity=issues_by_severity,
            )

        # Determine if we should continue
        should_continue = iteration < max_allowed

        # Build reason string
        issue_counts = ", ".join(
            f"{len(v)} {k.name.lower()}"
            for k, v in sorted(issues_by_severity.items(), reverse=True)
        )

        if should_continue:
            remaining = max_allowed - iteration
            reason = (
                f"Found {len(issues)} issue(s): {issue_counts}. "
                f"Continuing loop ({remaining} iteration(s) remaining for {highest_severity.name})"
            )
        else:
            reason = (
                f"Found {len(issues)} issue(s): {issue_counts}. "
                f"Maximum iterations reached, escalating to human review"
            )

        # Auto-fixable issues
        [
            i
            for i in classified_issues
            if i.auto_fixable and i.severity in [IssueSeverity.LOW, IssueSeverity.COSMETIC]
        ]

        return LoopDecision(
            should_continue=should_continue,
            action=action,
            max_iterations=max_allowed,
            current_iteration=iteration,
            reason=reason,
            issues_by_severity=issues_by_severity,
        )

    def get_fix_plan(self, issues: list[Issue]) -> dict[str, Any]:
        """
        Generate a plan for fixing issues.

        Args:
            issues: List of issues to fix

        Returns:
            Dict with fix plan
        """
        auto_fixable = []
        manual_fix = []

        for issue in issues:
            if self.auto_fix_engine.can_auto_fix(issue):
                auto_fixable.append(issue)
            else:
                manual_fix.append(issue)

        # Define constant for time estimation
        MINUTES_PER_AUTO_FIX = 5

        return {
            "auto_fixable_count": len(auto_fixable),
            "manual_fix_count": len(manual_fix),
            "auto_fixable": [i.to_dict() for i in auto_fixable],
            "manual_fix": [i.to_dict() for i in manual_fix],
            "estimated_time_saved": len(auto_fixable) * MINUTES_PER_AUTO_FIX,
        }

    def apply_auto_fixes(self, issues: list[Issue]) -> dict[str, Any]:
        """
        Apply auto-fixes to applicable issues.

        Args:
            issues: List of issues

        Returns:
            Dict with fix results
        """
        results = []
        for issue in issues:
            if self.auto_fix_engine.can_auto_fix(issue):
                result = self.auto_fix_engine.auto_fix(issue)
                results.append(result)
            else:
                results.append(
                    {
                        "success": False,
                        "message": "Not auto-fixable",
                        "issue_id": issue.issue_id,
                    }
                )

        success_count = sum(1 for r in results if r.get("success"))

        return {
            "total_issues": len(issues),
            "fixed": success_count,
            "failed": len(results) - success_count,
            "results": results,
        }
