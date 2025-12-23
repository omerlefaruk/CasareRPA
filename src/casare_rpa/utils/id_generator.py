"""
UUID-based node ID generation for CasareRPA.

Provides unique, collision-resistant IDs for workflow nodes.
Replaces the legacy incremental counter system (NodeType_1, NodeType_2)
with UUID-based IDs (NodeType_a1b2c3d4).
"""

import uuid
from typing import Set

# Track generated IDs in current session for debugging
_generated_ids: set[str] = set()


def generate_node_id(node_type: str, short: bool = True) -> str:
    """
    Generate a unique node ID using UUID.

    Args:
        node_type: The node class name (e.g., "ClickElementNode")
        short: If True, use 8-char hex suffix; if False, full UUID

    Returns:
        Unique ID like "ClickElementNode_a1b2c3d4"
    """
    if short:
        # Use first 8 characters of UUID hex for readability
        # 8 hex chars = 32 bits = ~4 billion possible values
        unique_suffix = uuid.uuid4().hex[:8]
    else:
        # Full UUID for maximum uniqueness
        unique_suffix = str(uuid.uuid4())

    node_id = f"{node_type}_{unique_suffix}"
    _generated_ids.add(node_id)
    return node_id


def is_uuid_based_id(node_id: str) -> bool:
    """
    Check if a node ID uses the new UUID format.

    Old format: "NodeType_123" (numeric suffix)
    New format: "NodeType_a1b2c3d4" (hex suffix)

    Args:
        node_id: The node ID to check

    Returns:
        True if the ID uses UUID format, False if legacy numeric format
    """
    if not node_id or "_" not in node_id:
        return False

    suffix = node_id.rsplit("_", 1)[-1]

    # Legacy format has purely numeric suffix
    if suffix.isdigit():
        return False

    # UUID format has hex characters (at least some letters mixed with numbers)
    try:
        int(suffix, 16)  # Valid hex
        return len(suffix) >= 8  # Require at least 8 hex chars for UUID format
    except ValueError:
        return False


def is_valid_node_id(node_id: str) -> bool:
    """
    Check if a string is a valid node ID (either format).

    Args:
        node_id: The node ID to validate

    Returns:
        True if valid node ID format
    """
    if not node_id or "_" not in node_id:
        return False

    parts = node_id.rsplit("_", 1)
    if len(parts) != 2:
        return False

    node_type, suffix = parts

    # Node type should be non-empty and start with uppercase
    if not node_type or not node_type[0].isupper():
        return False

    # Suffix should be either numeric (legacy) or hex (UUID)
    if suffix.isdigit():
        return True

    try:
        int(suffix, 16)
        return True
    except ValueError:
        return False


def clear_session_ids() -> None:
    """Clear tracked IDs (for testing)."""
    _generated_ids.clear()


def get_session_ids() -> set[str]:
    """Get all IDs generated in this session (for debugging)."""
    return _generated_ids.copy()
