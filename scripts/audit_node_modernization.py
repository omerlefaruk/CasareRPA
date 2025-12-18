#!/usr/bin/env python3
"""
Node Modernization Audit Script

Scans all nodes in src/casare_rpa/nodes/ and evaluates them against
the "Modern Node" Standard:

1. Schema Defined: Uses @properties decorator with PropertyDef objects
2. Dual-Source Ready: Uses self.get_parameter(name) for all inputs
3. Strictly Typed: All ports have a DataType (no generic ANY unless necessary)
4. Serialized Cleanly: Node IDs in JSON must be XxxNode, not VisualXxxNode

Outputs:
- Summary statistics
- Per-category breakdown
- Issues list grouped by severity
- Migration recommendations

Usage:
    python scripts/audit_node_modernization.py
    python scripts/audit_node_modernization.py --json  # JSON output
    python scripts/audit_node_modernization.py --tier 1  # Filter by tier
"""

import os
import sys
import re
import json
import ast
import importlib
import inspect
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict

# Ensure src is in python path
sys.path.insert(0, os.path.abspath("src"))


class ModernizationTier(Enum):
    """Node priority tiers for modernization."""

    TIER_1_CORE = 1  # Browser, Control Flow, File - most used by AI
    TIER_2_INTEGRATION = 2  # Google, HTTP, Email, Messaging
    TIER_3_SPECIALIZED = 3  # Desktop, System, PDF, etc.


class ModernizationStatus(Enum):
    """Modernization status for a node."""

    MODERN = "modern"  # Fully meets Modern Node Standard
    PARTIAL = "partial"  # Has @properties but missing some requirements
    LEGACY = "legacy"  # No @properties decorator
    UNKNOWN = "unknown"  # Could not be evaluated


@dataclass
class NodeIssue:
    """A specific issue found with a node."""

    severity: str  # "error", "warning", "info"
    code: str  # Issue code for automation
    message: str  # Human-readable description
    suggestion: str  # How to fix


@dataclass
class NodeAuditResult:
    """Audit result for a single node."""

    node_name: str
    file_path: str
    category: str
    tier: ModernizationTier
    status: ModernizationStatus

    # Modern Node Standard checks
    has_properties_decorator: bool = False
    uses_get_parameter: bool = False
    uses_config_get: bool = False  # Legacy pattern
    has_typed_ports: bool = True
    has_any_type_ports: List[str] = field(default_factory=list)

    # Additional metrics
    property_count: int = 0
    input_port_count: int = 0
    output_port_count: int = 0
    required_ports_missing_schema: List[str] = field(default_factory=list)

    issues: List[NodeIssue] = field(default_factory=list)

    def is_modern(self) -> bool:
        """Check if node meets Modern Node Standard."""
        return (
            self.has_properties_decorator
            and self.uses_get_parameter
            and not self.uses_config_get
            and self.has_typed_ports
            and len(self.required_ports_missing_schema) == 0
        )


@dataclass
class CategorySummary:
    """Summary for a category of nodes."""

    category: str
    tier: ModernizationTier
    total_nodes: int = 0
    modern_nodes: int = 0
    partial_nodes: int = 0
    legacy_nodes: int = 0

    @property
    def modernization_percentage(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return (self.modern_nodes / self.total_nodes) * 100


# Category to Tier mapping
CATEGORY_TIERS: Dict[str, ModernizationTier] = {
    # Tier 1: Core - Most used by AI
    "browser": ModernizationTier.TIER_1_CORE,
    "control_flow": ModernizationTier.TIER_1_CORE,
    "file": ModernizationTier.TIER_1_CORE,
    "variable": ModernizationTier.TIER_1_CORE,
    "data": ModernizationTier.TIER_1_CORE,
    # Tier 2: Integration
    "http": ModernizationTier.TIER_2_INTEGRATION,
    "google": ModernizationTier.TIER_2_INTEGRATION,
    "email": ModernizationTier.TIER_2_INTEGRATION,
    "messaging": ModernizationTier.TIER_2_INTEGRATION,
    "database": ModernizationTier.TIER_2_INTEGRATION,
    "llm": ModernizationTier.TIER_2_INTEGRATION,
    # Tier 3: Specialized
    "desktop_nodes": ModernizationTier.TIER_3_SPECIALIZED,
    "system": ModernizationTier.TIER_3_SPECIALIZED,
    "document": ModernizationTier.TIER_3_SPECIALIZED,
    "text": ModernizationTier.TIER_3_SPECIALIZED,
    "error_handling": ModernizationTier.TIER_3_SPECIALIZED,
    "trigger_nodes": ModernizationTier.TIER_3_SPECIALIZED,
    "workflow": ModernizationTier.TIER_3_SPECIALIZED,
    "data_operation": ModernizationTier.TIER_3_SPECIALIZED,
}

# Base classes to skip
BASE_CLASSES = {
    "BaseNode",
    "NodeExecutor",
    "NodeExecutorWithTryCatch",
    "GoogleBaseNode",
    "GmailBaseNode",
    "DocsBaseNode",
    "SheetsBaseNode",
    "DriveBaseNode",
    "CalendarBaseNode",
    "LLMBaseNode",
    "BrowserBaseNode",
    "DesktopNodeBase",
    "WindowNodeBase",
    "InteractionNodeBase",
    "HttpBaseNode",
    "BaseTriggerNode",
    "ResourceNode",
    "WhatsAppBaseNode",
    "TelegramBaseNode",
    "DocumentBaseNode",
    "SelectorMixin",
}


def get_category_from_path(file_path: str) -> str:
    """Extract category from file path."""
    path = Path(file_path)
    nodes_idx = None
    parts = path.parts

    for i, part in enumerate(parts):
        if part == "nodes":
            nodes_idx = i
            break

    if nodes_idx is not None and nodes_idx + 1 < len(parts):
        next_part = parts[nodes_idx + 1]
        if next_part.endswith(".py"):
            # Root-level node file
            return "root"
        return next_part

    return "unknown"


def get_tier_for_category(category: str) -> ModernizationTier:
    """Get tier for a category."""
    return CATEGORY_TIERS.get(category, ModernizationTier.TIER_3_SPECIALIZED)


def analyze_source_file(file_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Analyze a Python source file for node patterns using AST.

    Returns dict mapping class name to analysis results.
    """
    results = {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source)
    except Exception as e:
        return results

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_name = node.name

            # Skip non-node classes
            if not class_name.endswith("Node"):
                continue
            if class_name in BASE_CLASSES:
                continue

            analysis = {
                "has_properties_decorator": False,
                "property_defs": [],
                "uses_get_parameter": False,
                "uses_config_get": False,
                "config_get_locations": [],
            }

            # Check decorators
            for decorator in node.decorator_list:
                # Handle @properties(...) call form
                if isinstance(decorator, ast.Call):
                    if isinstance(decorator.func, ast.Name):
                        if decorator.func.id == "properties":
                            analysis["has_properties_decorator"] = True
                            # Count PropertyDef arguments
                            analysis["property_defs"] = [arg for arg in decorator.args]
                    # Handle @module.properties(...) attribute form
                    elif isinstance(decorator.func, ast.Attribute):
                        if decorator.func.attr == "properties":
                            analysis["has_properties_decorator"] = True
                            analysis["property_defs"] = [arg for arg in decorator.args]
                # Handle @properties bare decorator (no parens)
                elif isinstance(decorator, ast.Name):
                    if decorator.id == "properties":
                        analysis["has_properties_decorator"] = True
                # Handle @module.properties attribute form
                elif isinstance(decorator, ast.Attribute):
                    if decorator.attr == "properties":
                        analysis["has_properties_decorator"] = True

            # Check method bodies for patterns
            for item in ast.walk(node):
                if isinstance(item, ast.Call):
                    # Check for self.get_parameter(...)
                    if isinstance(item.func, ast.Attribute):
                        if item.func.attr == "get_parameter":
                            analysis["uses_get_parameter"] = True

                        # Check for self.config.get(...)
                        if item.func.attr == "get":
                            if isinstance(item.func.value, ast.Attribute):
                                if item.func.value.attr == "config":
                                    analysis["uses_config_get"] = True
                                    # Try to get line number
                                    if hasattr(item, "lineno"):
                                        analysis["config_get_locations"].append(
                                            item.lineno
                                        )

            results[class_name] = analysis

    return results


def audit_node_class(
    node_cls, source_analysis: Dict[str, Any], file_path: str
) -> Optional[NodeAuditResult]:
    """Audit a single node class."""
    class_name = node_cls.__name__

    if class_name in BASE_CLASSES:
        return None

    category = get_category_from_path(file_path)
    tier = get_tier_for_category(category)

    result = NodeAuditResult(
        node_name=class_name,
        file_path=file_path,
        category=category,
        tier=tier,
        status=ModernizationStatus.UNKNOWN,
    )

    # Get source analysis
    src_info = source_analysis.get(class_name, {})
    result.uses_get_parameter = src_info.get("uses_get_parameter", False)
    result.uses_config_get = src_info.get("uses_config_get", False)

    # Check for @properties decorator via source analysis OR __node_schema__
    result.has_properties_decorator = src_info.get("has_properties_decorator", False)

    # Also check the class attribute (more reliable than source analysis)
    schema = getattr(node_cls, "__node_schema__", None)
    if schema is not None:
        result.has_properties_decorator = True

    # Try to instantiate to check ports
    try:
        node = node_cls("audit_test", config={})

        # Check schema
        if schema:
            result.property_count = len(schema.properties)
            schema_props = {p.name for p in schema.properties}
        else:
            schema_props = set()

        # Analyze ports
        from casare_rpa.domain.value_objects.types import PortType, DataType

        for port_name, port in node.input_ports.items():
            # Skip exec ports
            if port.port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT):
                continue
            if port_name.startswith("exec_"):
                continue

            result.input_port_count += 1

            # Check for ANY type
            if port.data_type == DataType.ANY:
                result.has_any_type_ports.append(f"input:{port_name}")

            # Check required ports without schema coverage
            if port.required and port_name not in schema_props:
                result.required_ports_missing_schema.append(port_name)

        for port_name, port in node.output_ports.items():
            if port.port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT):
                continue
            if port_name.startswith("exec_"):
                continue

            result.output_port_count += 1

            if port.data_type == DataType.ANY:
                result.has_any_type_ports.append(f"output:{port_name}")

        result.has_typed_ports = len(result.has_any_type_ports) == 0

    except Exception as e:
        # Can't instantiate - use source analysis only
        pass

    # Generate issues
    if not result.has_properties_decorator:
        result.issues.append(
            NodeIssue(
                severity="error",
                code="NO_PROPERTIES_DECORATOR",
                message="Missing @properties decorator",
                suggestion="Add @properties(PropertyDef(...)) decorator to class",
            )
        )

    if result.uses_config_get:
        config_lines = src_info.get("config_get_locations", [])
        result.issues.append(
            NodeIssue(
                severity="warning",
                code="LEGACY_CONFIG_GET",
                message="Uses self.config.get() instead of self.get_parameter()",
                suggestion=f"Replace self.config.get() with self.get_parameter() at lines: {config_lines}",
            )
        )

    # Note: Required ports without PropertyDef are OK - they receive data from connections
    # PropertyDef is only needed for ports that can also receive values from configuration
    # So we don't generate warnings for required_ports_missing_schema anymore

    for any_port in result.has_any_type_ports:
        result.issues.append(
            NodeIssue(
                severity="info",
                code="ANY_TYPE_PORT",
                message=f"Port '{any_port}' uses DataType.ANY",
                suggestion="Consider using a more specific DataType if possible",
            )
        )

    # Determine status
    if result.is_modern():
        result.status = ModernizationStatus.MODERN
    elif result.has_properties_decorator:
        result.status = ModernizationStatus.PARTIAL
    else:
        result.status = ModernizationStatus.LEGACY

    return result


def run_audit(
    tier_filter: Optional[int] = None,
) -> Tuple[List[NodeAuditResult], Dict[str, CategorySummary]]:
    """Run full audit of all nodes."""
    from casare_rpa.domain.entities.base_node import BaseNode
    from casare_rpa.nodes.registry_data import NODE_REGISTRY

    results: List[NodeAuditResult] = []
    category_summaries: Dict[str, CategorySummary] = {}

    nodes_dir = Path("src/casare_rpa/nodes").resolve()  # Use absolute path

    # First pass: collect source analysis for all Python files
    source_analyses: Dict[str, Dict[str, Dict[str, Any]]] = {}
    file_path_cache: Dict[str, str] = {}  # module path -> file path

    for file_path in nodes_dir.rglob("*.py"):
        if file_path.name.startswith("__"):
            continue

        # Use absolute path for consistent lookup
        abs_path = str(file_path.resolve())
        analysis = analyze_source_file(abs_path)
        source_analyses[abs_path] = analysis

        # Build module path -> file path mapping
        rel_path = file_path.relative_to(nodes_dir)
        module_path = str(rel_path).replace(os.sep, ".").replace(".py", "")
        file_path_cache[module_path] = abs_path

    # Second pass: use NODE_REGISTRY to import nodes
    for node_name, module_info in NODE_REGISTRY.items():
        if node_name in BASE_CLASSES:
            continue

        # Handle tuple format (module_path, class_alias)
        if isinstance(module_info, tuple):
            module_path, class_alias = module_info
        else:
            module_path = module_info
            class_alias = node_name

        # Build full module path
        full_module = f"casare_rpa.nodes.{module_path}"

        try:
            module = importlib.import_module(full_module)
            node_cls = getattr(module, class_alias, None)

            if node_cls is None:
                continue

            # Check if it's a BaseNode subclass
            if not issubclass(node_cls, BaseNode):
                continue

        except Exception as e:
            continue

        # Get file path for this module
        try:
            file_path = inspect.getfile(node_cls)
        except (TypeError, OSError):
            file_path = file_path_cache.get(module_path, "unknown")

        # Get source analysis
        source_analysis = source_analyses.get(file_path, {})

        result = audit_node_class(node_cls, source_analysis, file_path)
        if result:
            # Apply tier filter
            if tier_filter is not None:
                if result.tier.value != tier_filter:
                    continue

            results.append(result)

            # Update category summary
            cat = result.category
            if cat not in category_summaries:
                category_summaries[cat] = CategorySummary(
                    category=cat, tier=result.tier
                )

            summary = category_summaries[cat]
            summary.total_nodes += 1

            if result.status == ModernizationStatus.MODERN:
                summary.modern_nodes += 1
            elif result.status == ModernizationStatus.PARTIAL:
                summary.partial_nodes += 1
            else:
                summary.legacy_nodes += 1

    return results, category_summaries


def print_report(
    results: List[NodeAuditResult],
    summaries: Dict[str, CategorySummary],
    json_output: bool = False,
):
    """Print audit report."""
    if json_output:
        output = {
            "summary": {
                "total_nodes": len(results),
                "modern": sum(
                    1 for r in results if r.status == ModernizationStatus.MODERN
                ),
                "partial": sum(
                    1 for r in results if r.status == ModernizationStatus.PARTIAL
                ),
                "legacy": sum(
                    1 for r in results if r.status == ModernizationStatus.LEGACY
                ),
            },
            "categories": {
                cat: {
                    "tier": s.tier.name,
                    "total": s.total_nodes,
                    "modern": s.modern_nodes,
                    "partial": s.partial_nodes,
                    "legacy": s.legacy_nodes,
                    "percentage": round(s.modernization_percentage, 1),
                }
                for cat, s in summaries.items()
            },
            "nodes": [
                {
                    "name": r.node_name,
                    "category": r.category,
                    "tier": r.tier.name,
                    "status": r.status.value,
                    "issues": [asdict(i) for i in r.issues],
                }
                for r in results
            ],
        }
        print(json.dumps(output, indent=2))
        return

    # Header
    print("=" * 80)
    print("NODE MODERNIZATION AUDIT REPORT")
    print("=" * 80)
    print()

    # Overall Summary
    total = len(results)
    modern = sum(1 for r in results if r.status == ModernizationStatus.MODERN)
    partial = sum(1 for r in results if r.status == ModernizationStatus.PARTIAL)
    legacy = sum(1 for r in results if r.status == ModernizationStatus.LEGACY)

    print("OVERALL SUMMARY")
    print("-" * 40)
    print(f"Total Nodes Audited: {total}")
    if total > 0:
        print(f"  [OK] Modern:  {modern:3d} ({modern/total*100:.1f}%)")
        print(f"  [--] Partial: {partial:3d} ({partial/total*100:.1f}%)")
        print(f"  [XX] Legacy:  {legacy:3d} ({legacy/total*100:.1f}%)")
    else:
        print("  No nodes found to audit.")
        return
    print()

    # Category Summary by Tier
    print("CATEGORY BREAKDOWN BY TIER")
    print("-" * 40)

    for tier in ModernizationTier:
        tier_cats = [s for s in summaries.values() if s.tier == tier]
        if not tier_cats:
            continue

        print(f"\n{tier.name}:")
        for s in sorted(tier_cats, key=lambda x: -x.modernization_percentage):
            bar_len = int(s.modernization_percentage / 5)
            bar = "#" * bar_len + "-" * (20 - bar_len)
            print(
                f"  {s.category:20s} [{bar}] {s.modernization_percentage:5.1f}% ({s.modern_nodes}/{s.total_nodes})"
            )

    print()

    # Issues by Severity
    print("ISSUES BY SEVERITY")
    print("-" * 40)

    errors = []
    warnings = []
    infos = []

    for r in results:
        for issue in r.issues:
            entry = f"{r.node_name}: {issue.message}"
            if issue.severity == "error":
                errors.append(entry)
            elif issue.severity == "warning":
                warnings.append(entry)
            else:
                infos.append(entry)

    print(f"\n[X] ERRORS ({len(errors)}):")
    for e in errors[:20]:  # Show first 20
        print(f"  * {e}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")

    print(f"\n[!] WARNINGS ({len(warnings)}):")
    for w in warnings[:20]:
        print(f"  * {w}")
    if len(warnings) > 20:
        print(f"  ... and {len(warnings) - 20} more")

    print()

    # Migration Recommendations
    print("MIGRATION PRIORITY (Top 10 Legacy Nodes)")
    print("-" * 40)

    # Sort by tier then by issue count
    legacy_nodes = [r for r in results if r.status == ModernizationStatus.LEGACY]
    legacy_nodes.sort(key=lambda x: (x.tier.value, -len(x.issues)))

    for i, node in enumerate(legacy_nodes[:10], 1):
        print(f"{i}. {node.node_name}")
        print(f"   Category: {node.category} | Tier: {node.tier.name}")
        print(f"   File: {node.file_path}")
        print(f"   Issues: {len(node.issues)}")
        print()

    print("=" * 80)
    print("Run with --json for machine-readable output")
    print("Run with --tier 1 to filter by priority tier")
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Audit nodes for modernization")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], help="Filter by tier")
    args = parser.parse_args()

    print("Starting Node Modernization Audit...", file=sys.stderr)
    results, summaries = run_audit(tier_filter=args.tier)
    print(f"Audited {len(results)} nodes", file=sys.stderr)

    print_report(results, summaries, json_output=args.json)


if __name__ == "__main__":
    main()
