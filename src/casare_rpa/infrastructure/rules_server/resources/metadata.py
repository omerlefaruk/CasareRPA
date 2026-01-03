"""
Rule metadata catalog.

Simple registry with category, priority, and trigger keywords.
No complex schemas - just Python dicts for fast lookups.
"""

TRIGGER_KEYWORDS = {
    "nodes": ["node", "workflow", "execute", "browser", "desktop", "automation"],
    "ui": ["popup", "toolbar", "theme", "widget", "qt", "pyside", "dialog", "gui"],
    "testing": ["test", "pytest", "fixture", "mock", "spec"],
    "workflow": ["plan", "implement", "refactor", "optimize", "feature"],
    "http": ["http", "api", "request", "fetch", "url"],
    "database": ["database", "db", "sql", "query", "migration"],
    "domain": ["event", "ddd", "aggregate", "entity", "value object"],
    "async": ["async", "await", "asyncio", "qasync"],
    "error": ["error", "exception", "retry", "timeout", "fail"],
}

RULE_CATALOG = {
    # Core rules
    "core/index-first": {
        "category": "core",
        "priority": "critical",
        "tokens": 150,
        "file": "core/index-first.md",
    },
    "core/domain-purity": {
        "category": "core",
        "priority": "critical",
        "tokens": 200,
        "file": "core/domain-purity.md",
    },
    "core/enforcement": {
        "category": "core",
        "priority": "critical",
        "tokens": 250,
        "file": "core/enforcement.md",
    },
    "core/tools": {
        "category": "core",
        "priority": "normal",
        "tokens": 200,
        "file": "core/tools.md",
    },
    "core/error-handling": {
        "category": "core",
        "priority": "critical",
        "tokens": 350,
        "file": "core/error-handling.md",
    },
    "core/async-patterns": {
        "category": "core",
        "priority": "critical",
        "tokens": 300,
        "file": "core/async-patterns.md",
    },
    "core/type-safety": {
        "category": "core",
        "priority": "normal",
        "tokens": 200,
        "file": "core/type-safety.md",
    },
    # Domain rules
    "domain/events": {
        "category": "domain",
        "priority": "normal",
        "tokens": 300,
        "file": "domain/events.md",
    },
    "domain/aggregates": {
        "category": "domain",
        "priority": "normal",
        "tokens": 350,
        "file": "domain/aggregates.md",
    },
    # Workflow rules
    "workflow/phases": {
        "category": "workflow",
        "priority": "normal",
        "tokens": 400,
        "file": "workflow/phases.md",
    },
    "workflow/gates": {
        "category": "workflow",
        "priority": "normal",
        "tokens": 300,
        "file": "workflow/gates.md",
    },
    # Node rules
    "nodes/standard-2025": {
        "category": "nodes",
        "priority": "normal",
        "tokens": 500,
        "file": "nodes/standard-2025.md",
    },
    "nodes/registration": {
        "category": "nodes",
        "priority": "normal",
        "tokens": 300,
        "file": "nodes/registration.md",
    },
    "nodes/base-classes": {
        "category": "nodes",
        "priority": "normal",
        "tokens": 450,
        "file": "nodes/base-classes.md",
    },
    "nodes/schema-driven": {
        "category": "nodes",
        "priority": "normal",
        "tokens": 400,
        "file": "nodes/schema-driven.md",
    },
    # UI rules
    "ui/theme": {
        "category": "ui",
        "priority": "critical",
        "tokens": 200,
        "file": "ui/theme.md",
    },
    "ui/theme-v2": {
        "category": "ui",
        "priority": "critical",
        "tokens": 350,
        "file": "ui/theme-v2.md",
    },
    "ui/popup": {
        "category": "ui",
        "priority": "normal",
        "tokens": 250,
        "file": "ui/popup.md",
    },
    "ui/signals": {
        "category": "ui",
        "priority": "normal",
        "tokens": 200,
        "file": "ui/signals.md",
    },
    "ui/widgets": {
        "category": "ui",
        "priority": "normal",
        "tokens": 400,
        "file": "ui/widgets.md",
    },
    # Testing rules
    "testing/organization": {
        "category": "testing",
        "priority": "normal",
        "tokens": 300,
        "file": "testing/organization.md",
    },
    "testing/patterns": {
        "category": "testing",
        "priority": "normal",
        "tokens": 400,
        "file": "testing/patterns.md",
    },
}


def detect_context(prompt: str) -> tuple[str, str | None]:
    """Detect rule category from user prompt.

    Returns:
        (category, task_type) tuple
    """
    prompt_lower = prompt.lower()

    for category, triggers in TRIGGER_KEYWORDS.items():
        if any(trigger in prompt_lower for trigger in triggers):
            return category, None

    return "core", None


def get_rules_for_category(category: str, urgency: str = "normal") -> list[str]:
    """Get rule file paths for a category.

    Args:
        category: Rule category (core, workflow, nodes, ui, testing, domain)
        urgency: Return depth (critical, normal, optional)

    Returns:
        List of rule file paths
    """
    result = []

    for rule_id, meta in RULE_CATALOG.items():
        if meta["category"] != category:
            continue

        # Filter by urgency
        if urgency == "critical" and meta["priority"] != "critical":
            continue

        result.append(meta["file"])

    return result
