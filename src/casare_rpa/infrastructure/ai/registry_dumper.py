"""
CasareRPA - Node Registry Dumper

Generates structured manifests of all available nodes for LLM consumption.
Supports multiple output formats optimized for different AI use cases.

Entry Points:
    - dump_node_manifest(): Generate complete manifest from registry
    - manifest_to_markdown(): Token-optimized markdown for prompts
    - manifest_to_json(): JSON format for structured output
    - get_nodes_by_category(): Filter nodes by category

Key Patterns:
    - Lazy loading: Nodes instantiated temporarily to read port definitions
    - Caching: Manifest cached at module level (immutable at runtime)
    - LLM optimization: Concise descriptions, clear port specs
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Type

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import DataType, PortType


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass(frozen=True)
class PortManifestEntry:
    """
    Immutable representation of a node port for manifest generation.

    Attributes:
        name: Port identifier (e.g., "url", "selector")
        data_type: Data type as string (e.g., "STRING", "PAGE")
        required: Whether the port must be connected
        label: Human-readable display label
    """

    name: str
    data_type: str
    required: bool
    label: str

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "data_type": self.data_type,
            "required": self.required,
            "label": self.label,
        }


@dataclass(frozen=True)
class NodeManifestEntry:
    """
    Immutable representation of a node for manifest generation.

    Attributes:
        type: Node class name (e.g., "LaunchBrowserNode")
        category: Node category (e.g., "browser", "control_flow")
        description: Brief description of node functionality
        inputs: List of input port specifications
        outputs: List of output port specifications
    """

    type: str
    category: str
    description: str
    inputs: tuple[PortManifestEntry, ...] = field(default_factory=tuple)
    outputs: tuple[PortManifestEntry, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type,
            "category": self.category,
            "description": self.description,
            "inputs": [p.to_dict() for p in self.inputs],
            "outputs": [p.to_dict() for p in self.outputs],
        }


@dataclass(frozen=True)
class NodeManifest:
    """
    Complete manifest of all available nodes.

    Attributes:
        nodes: List of all node manifest entries
        categories: Set of unique categories
        total_count: Total number of nodes
        generated_at: ISO timestamp of generation
    """

    nodes: tuple[NodeManifestEntry, ...] = field(default_factory=tuple)
    categories: frozenset[str] = field(default_factory=frozenset)
    total_count: int = 0
    generated_at: str = ""

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization."""
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "categories": sorted(self.categories),
            "total_count": self.total_count,
            "generated_at": self.generated_at,
        }


# =============================================================================
# MODULE-LEVEL CACHE
# =============================================================================

_manifest_cache: Optional[NodeManifest] = None


def get_cached_manifest() -> Optional[NodeManifest]:
    """
    Get cached manifest if available.

    Returns:
        Cached NodeManifest or None if not yet generated
    """
    return _manifest_cache


def clear_manifest_cache() -> None:
    """Clear the manifest cache. Used for testing."""
    global _manifest_cache
    _manifest_cache = None


# =============================================================================
# CORE FUNCTIONS
# =============================================================================


def _extract_description(node_class: Type[BaseNode]) -> str:
    """
    Extract a concise description from node docstring.

    Optimized for LLM consumption - extracts first meaningful sentence.

    Args:
        node_class: Node class to extract description from

    Returns:
        Concise description string (max ~100 chars)
    """
    doc = node_class.__doc__ or ""
    if not doc.strip():
        return f"{node_class.__name__} node"

    # Get first paragraph (before double newline)
    paragraphs = doc.strip().split("\n\n")
    first_para = paragraphs[0] if paragraphs else doc

    # Clean up whitespace
    lines = [line.strip() for line in first_para.split("\n")]
    text = " ".join(lines).strip()

    # Extract first sentence
    for end in [".", "!", "?"]:
        idx = text.find(end)
        if idx > 0:
            text = text[: idx + 1]
            break

    # Truncate if still too long
    if len(text) > 150:
        text = text[:147] + "..."

    return text


def _extract_category(node_class: Type[BaseNode], node_instance: BaseNode) -> str:
    """
    Extract category from node, falling back through multiple sources.

    Args:
        node_class: Node class
        node_instance: Instantiated node

    Returns:
        Category string
    """
    # Try instance attribute first
    if hasattr(node_instance, "category") and node_instance.category:
        cat = node_instance.category
        if cat != "General":
            return cat

    # Try class attribute
    if hasattr(node_class, "category") and node_class.category:
        return node_class.category

    # Try to extract from docstring comment: @category: xxx
    doc = node_class.__doc__ or ""
    for line in doc.split("\n"):
        line = line.strip()
        if line.startswith("@category:") or line.startswith("# @category:"):
            cat = line.split(":", 1)[1].strip()
            if cat:
                return cat

    # Infer from module path
    module = node_class.__module__
    if "browser" in module:
        return "browser"
    if "file" in module:
        return "file"
    if "database" in module:
        return "database"
    if "google" in module:
        return "google"
    if "control_flow" in module:
        return "control_flow"
    if "system" in module:
        return "system"
    if "http" in module or "rest" in module:
        return "rest_api"
    if "email" in module:
        return "email"
    if "desktop" in module:
        return "desktop"
    if "llm" in module:
        return "ai_ml"
    if "trigger" in module:
        return "triggers"
    if "messaging" in module:
        return "messaging"

    return "utility"


def _create_port_entry(port) -> PortManifestEntry:
    """
    Create a PortManifestEntry from a Port object.

    Args:
        port: Port instance from node

    Returns:
        PortManifestEntry with port details
    """
    # Get data type name, handling cases where PortType is mistakenly
    # used as data_type (bug in some node implementations)
    if isinstance(port.data_type, DataType):
        data_type = port.data_type.name
    elif isinstance(port.data_type, PortType):
        # Node mistakenly passed PortType as data_type
        # Infer ANY as fallback
        data_type = "ANY"
    else:
        # String or other type
        data_type_str = str(port.data_type)
        # Clean up enum representation if needed
        if "PortType." in data_type_str:
            data_type = "ANY"
        elif "DataType." in data_type_str:
            data_type = data_type_str.replace("DataType.", "")
        else:
            data_type = data_type_str

    # Get label, handling cases where DataType/PortType is used as label
    # (another bug in some node implementations)
    label = port.label
    if label is None:
        label = port.name
    elif isinstance(label, (DataType, PortType)):
        # Label should be a string, not an enum
        label = port.name
    elif not isinstance(label, str):
        label = str(label)

    return PortManifestEntry(
        name=port.name,
        data_type=data_type,
        required=port.required,
        label=label,
    )


def _is_exec_port(port) -> bool:
    """Check if port is an execution flow port (not data)."""
    if port.port_type in (PortType.EXEC_INPUT, PortType.EXEC_OUTPUT):
        return True
    if port.name.startswith("exec_"):
        return True
    if isinstance(port.data_type, DataType) and port.data_type == DataType.EXEC:
        return True
    return False


def dump_node_manifest() -> NodeManifest:
    """
    Generate complete node manifest from registry.

    Loads all nodes, extracts metadata, and creates a comprehensive
    manifest optimized for LLM consumption.

    Returns:
        NodeManifest containing all registered nodes

    Note:
        Result is cached - subsequent calls return cached version.
        Use clear_manifest_cache() to regenerate.
    """
    global _manifest_cache

    if _manifest_cache is not None:
        return _manifest_cache

    logger.info("Generating node manifest from registry...")

    try:
        from casare_rpa.nodes import get_all_node_classes
    except ImportError as e:
        logger.error(f"Failed to import node registry: {e}")
        return NodeManifest(
            nodes=tuple(),
            categories=frozenset(),
            total_count=0,
            generated_at=datetime.now().isoformat(),
        )

    node_classes = get_all_node_classes()
    entries: List[NodeManifestEntry] = []
    categories: set[str] = set()
    errors: List[str] = []

    for node_type, node_class in node_classes.items():
        try:
            # Create temporary instance to read ports
            # Use a dummy node_id since we just need port definitions
            instance = node_class(node_id=f"__manifest_{node_type}")

            # Extract category
            category = _extract_category(node_class, instance)
            categories.add(category)

            # Extract description
            description = _extract_description(node_class)

            # Extract input ports (exclude exec ports)
            input_ports: List[PortManifestEntry] = []
            for port in instance.input_ports.values():
                if not _is_exec_port(port):
                    input_ports.append(_create_port_entry(port))

            # Extract output ports (exclude exec ports)
            output_ports: List[PortManifestEntry] = []
            for port in instance.output_ports.values():
                if not _is_exec_port(port):
                    output_ports.append(_create_port_entry(port))

            # Create entry
            entry = NodeManifestEntry(
                type=node_type,
                category=category,
                description=description,
                inputs=tuple(input_ports),
                outputs=tuple(output_ports),
            )
            entries.append(entry)

        except Exception as e:
            errors.append(f"{node_type}: {e}")
            logger.warning(f"Failed to process node {node_type}: {e}")

    if errors:
        logger.warning(f"Failed to process {len(errors)} nodes")

    # Sort entries by category then by type for consistent output
    entries.sort(key=lambda e: (e.category, e.type))

    manifest = NodeManifest(
        nodes=tuple(entries),
        categories=frozenset(categories),
        total_count=len(entries),
        generated_at=datetime.now().isoformat(),
    )

    _manifest_cache = manifest
    logger.info(
        f"Generated manifest: {manifest.total_count} nodes, "
        f"{len(manifest.categories)} categories"
    )

    return manifest


def get_nodes_by_category(category: str) -> List[NodeManifestEntry]:
    """
    Get all nodes in a specific category.

    Args:
        category: Category name (e.g., "browser", "file")

    Returns:
        List of NodeManifestEntry objects in the category
    """
    manifest = dump_node_manifest()
    return [n for n in manifest.nodes if n.category == category]


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================


def manifest_to_json(manifest: Optional[NodeManifest] = None, indent: int = 2) -> str:
    """
    Convert manifest to JSON format.

    Args:
        manifest: NodeManifest to convert (uses cached if None)
        indent: JSON indentation level

    Returns:
        JSON string representation
    """
    if manifest is None:
        manifest = dump_node_manifest()

    return json.dumps(manifest.to_dict(), indent=indent)


def manifest_to_markdown(manifest: Optional[NodeManifest] = None) -> str:
    """
    Convert manifest to token-optimized markdown for LLM prompts.

    Format is designed for minimal token usage while maintaining clarity:
    - Grouped by category
    - Compact port notation: `name:TYPE` or `name:TYPE?` for optional
    - Single-line node entries where possible

    Args:
        manifest: NodeManifest to convert (uses cached if None)

    Returns:
        Markdown string optimized for LLM consumption
    """
    if manifest is None:
        manifest = dump_node_manifest()

    lines: List[str] = []
    lines.append("# CasareRPA Node Reference")
    lines.append(
        f"Total: {manifest.total_count} nodes | {len(manifest.categories)} categories"
    )
    lines.append("")

    # Group by category
    by_category: Dict[str, List[NodeManifestEntry]] = {}
    for node in manifest.nodes:
        if node.category not in by_category:
            by_category[node.category] = []
        by_category[node.category].append(node)

    # Output each category
    for category in sorted(by_category.keys()):
        nodes = by_category[category]
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")

        for node in nodes:
            # Node header: **TypeName** - Description
            lines.append(f"**{node.type}** - {node.description}")

            # Input ports (compact notation)
            if node.inputs:
                inputs_str = ", ".join(
                    f"`{p.name}:{p.data_type}{'?' if not p.required else ''}`"
                    for p in node.inputs
                )
                lines.append(f"  IN: {inputs_str}")

            # Output ports
            if node.outputs:
                outputs_str = ", ".join(
                    f"`{p.name}:{p.data_type}`" for p in node.outputs
                )
                lines.append(f"  OUT: {outputs_str}")

            lines.append("")

    return "\n".join(lines)


def manifest_to_compact_markdown(manifest: Optional[NodeManifest] = None) -> str:
    """
    Convert manifest to ultra-compact markdown for context-limited prompts.

    Even more token-efficient than manifest_to_markdown:
    - No descriptions
    - Minimal formatting
    - Tabular format

    Args:
        manifest: NodeManifest to convert (uses cached if None)

    Returns:
        Ultra-compact markdown string
    """
    if manifest is None:
        manifest = dump_node_manifest()

    lines: List[str] = []
    lines.append(f"# Nodes ({manifest.total_count})")
    lines.append("")

    # Group by category
    by_category: Dict[str, List[NodeManifestEntry]] = {}
    for node in manifest.nodes:
        if node.category not in by_category:
            by_category[node.category] = []
        by_category[node.category].append(node)

    for category in sorted(by_category.keys()):
        nodes = by_category[category]
        lines.append(f"## {category}")
        for node in nodes:
            # Ultra-compact: Type(in1,in2)->out1,out2
            ins = ",".join(p.name for p in node.inputs) if node.inputs else "-"
            outs = ",".join(p.name for p in node.outputs) if node.outputs else "-"
            lines.append(f"- {node.type}({ins})->{outs}")
        lines.append("")

    return "\n".join(lines)
