"""
CasareRPA - Project Base Constants and Utilities

Constants and ID generators for project entities.
"""

import uuid


PROJECT_SCHEMA_VERSION: str = "1.0.0"


def generate_project_id() -> str:
    """Generate unique project ID."""
    return f"proj_{uuid.uuid4().hex[:8]}"


def generate_scenario_id() -> str:
    """Generate unique scenario ID."""
    return f"scen_{uuid.uuid4().hex[:8]}"
