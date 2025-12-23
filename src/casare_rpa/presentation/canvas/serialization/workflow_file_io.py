"""
Workflow file I/O helpers for Canvas.

Centralizes workflow JSON writes so save and autosave share the same behavior.
"""

from pathlib import Path
from typing import Any

import orjson

from casare_rpa.nodes.file.file_security import validate_path_security


def write_workflow_file(file_path: str | Path, workflow_data: dict[str, Any]) -> Path:
    """
    Write workflow data to disk with security validation.

    Args:
        file_path: Target workflow file path.
        workflow_data: Serialized workflow data.

    Returns:
        Path to the written file.

    Raises:
        PathSecurityError: If the path fails security validation.
        OSError: If the file cannot be written.
    """
    validated_path = validate_path_security(str(file_path), operation="save_workflow")
    validated_path.parent.mkdir(parents=True, exist_ok=True)
    validated_path.write_bytes(orjson.dumps(workflow_data, option=orjson.OPT_INDENT_2))
    return validated_path
