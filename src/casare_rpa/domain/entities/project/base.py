"""
CasareRPA - Project Base Constants and Utilities

Constants and ID generators for project entities.
"""

import uuid


PROJECT_SCHEMA_VERSION: str = "2.0.0"


def generate_project_id() -> str:
    """Generate unique project ID."""
    return f"proj_{uuid.uuid4().hex[:8]}"


def generate_scenario_id() -> str:
    """Generate unique scenario ID."""
    return f"scen_{uuid.uuid4().hex[:8]}"


def generate_environment_id() -> str:
    """Generate unique environment ID."""
    return f"env_{uuid.uuid4().hex[:8]}"


def generate_folder_id() -> str:
    """Generate unique folder ID."""
    return f"fold_{uuid.uuid4().hex[:8]}"


def generate_template_id() -> str:
    """Generate unique template ID."""
    return f"tmpl_{uuid.uuid4().hex[:8]}"
