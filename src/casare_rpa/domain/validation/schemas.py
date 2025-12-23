"""
CasareRPA - Validation Schemas Module

Contains schema definitions, constants, and type mappings for validation.
"""

import logging
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)


# Required fields for node data
NODE_REQUIRED_FIELDS: set[str] = {"node_id", "node_type"}

# Required fields for connection data
CONNECTION_REQUIRED_FIELDS: set[str] = {
    "source_node",
    "source_port",
    "target_node",
    "target_port",
}

# Data type compatibility matrix (source -> compatible targets)
DATA_TYPE_COMPATIBILITY: dict[str, set[str]] = {
    "ANY": {
        "STRING",
        "INTEGER",
        "FLOAT",
        "BOOLEAN",
        "LIST",
        "DICT",
        "ANY",
        "ELEMENT",
        "PAGE",
        "BROWSER",
    },
    "STRING": {"STRING", "ANY"},
    "INTEGER": {"INTEGER", "FLOAT", "STRING", "ANY"},
    "FLOAT": {"FLOAT", "STRING", "ANY"},
    "BOOLEAN": {"BOOLEAN", "STRING", "ANY"},
    "LIST": {"LIST", "ANY"},
    "DICT": {"DICT", "ANY"},
    "ELEMENT": {"ELEMENT", "ANY"},
    "PAGE": {"PAGE", "ANY"},
    "BROWSER": {"BROWSER", "ANY"},
}


def _get_valid_node_types() -> set[str]:
    """
    Dynamically get valid node types from the central node registry.

    This ensures VALID_NODE_TYPES always stays in sync with the actual
    available node types in the system.
    """
    try:
        from casare_rpa.nodes.registry_data import NODE_REGISTRY

        return set(NODE_REGISTRY.keys())
    except ImportError:
        logger.warning("Could not import NODE_REGISTRY, using minimal node set")
        return {
            "StartNode",
            "EndNode",
            "IfNode",
            "ForLoopStartNode",
            "ForLoopEndNode",
            "WhileLoopStartNode",
            "WhileLoopEndNode",
            "SetVariableNode",
            "GetVariableNode",
            "LogNode",
            "CommentNode",
        }


# Lazily evaluated to avoid circular imports
_valid_node_types_cache: set[str] | None = None


def get_valid_node_types() -> set[str]:
    """Get the set of valid node types."""
    global _valid_node_types_cache
    if _valid_node_types_cache is None:
        _valid_node_types_cache = _get_valid_node_types()
    return _valid_node_types_cache


# Legacy alias for backwards compatibility (will be evaluated lazily when accessed)
VALID_NODE_TYPES: set[str] = set()  # Placeholder, use get_valid_node_types() instead


__all__ = [
    "NODE_REQUIRED_FIELDS",
    "CONNECTION_REQUIRED_FIELDS",
    "DATA_TYPE_COMPATIBILITY",
    "VALID_NODE_TYPES",
    "get_valid_node_types",
]
