"""
CasareRPA - Validation Schemas Module

Contains schema definitions, constants, and type mappings for validation.
"""

from typing import Dict, Optional, Set

import logging

logger = logging.getLogger(__name__)


# Required fields for node data
NODE_REQUIRED_FIELDS: Set[str] = {"node_id", "node_type"}

# Required fields for connection data
CONNECTION_REQUIRED_FIELDS: Set[str] = {
    "source_node",
    "source_port",
    "target_node",
    "target_port",
}

# Data type compatibility matrix (source -> compatible targets)
DATA_TYPE_COMPATIBILITY: Dict[str, Set[str]] = {
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


def _get_valid_node_types() -> Set[str]:
    """
    Dynamically get valid node types from NODE_TYPE_MAP.

    This ensures VALID_NODE_TYPES always stays in sync with the actual
    available node types in the system.
    """
    try:
        from casare_rpa.utils.workflow.workflow_loader import NODE_TYPE_MAP

        return set(NODE_TYPE_MAP.keys())
    except ImportError:
        # Fallback to a minimal set if workflow_loader isn't available
        logger.warning("Could not import NODE_TYPE_MAP, using minimal node set")
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
_valid_node_types_cache: Optional[Set[str]] = None


def get_valid_node_types() -> Set[str]:
    """Get the set of valid node types."""
    global _valid_node_types_cache
    if _valid_node_types_cache is None:
        _valid_node_types_cache = _get_valid_node_types()
    return _valid_node_types_cache


# Legacy alias for backwards compatibility (will be evaluated lazily when accessed)
VALID_NODE_TYPES: Set[str] = set()  # Placeholder, use get_valid_node_types() instead


__all__ = [
    "NODE_REQUIRED_FIELDS",
    "CONNECTION_REQUIRED_FIELDS",
    "DATA_TYPE_COMPATIBILITY",
    "VALID_NODE_TYPES",
    "get_valid_node_types",
]
