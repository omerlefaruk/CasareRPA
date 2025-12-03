"""
Node property schema system.

Provides declarative property definitions for nodes via @node_schema decorator.
"""

from casare_rpa.domain.schemas.property_schema import NodeSchema, PropertyDef
from casare_rpa.domain.schemas.property_types import PropertyType

__all__ = ["PropertyType", "PropertyDef", "NodeSchema"]
