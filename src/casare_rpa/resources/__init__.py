"""
CasareRPA - Resources Package

Contains built-in templates, icons, and other static resources.
"""

from pathlib import Path

RESOURCES_DIR = Path(__file__).parent
TEMPLATES_DIR = RESOURCES_DIR / "templates"


def get_templates_dir() -> Path:
    """Get path to built-in templates directory."""
    return TEMPLATES_DIR


__all__ = [
    "RESOURCES_DIR",
    "TEMPLATES_DIR",
    "get_templates_dir",
]
