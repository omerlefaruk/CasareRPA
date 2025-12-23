"""
Domain Variable Resolver Re-export Module.

Re-exports variable resolution utilities from domain.services.variable_resolver.
"""

from casare_rpa.domain.services.variable_resolver import (
    VARIABLE_PATTERN,
    extract_variable_names,
    has_variables,
    resolve_dict_variables,
    resolve_variables,
)

__all__ = [
    "VARIABLE_PATTERN",
    "resolve_variables",
    "resolve_dict_variables",
    "extract_variable_names",
    "has_variables",
]
