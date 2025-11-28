"""
Node property schema system.

Provides declarative property definitions for nodes via @node_schema decorator.
"""

from .property_types import PropertyType
from .property_schema import PropertyDef, NodeSchema

__all__ = ["PropertyType", "PropertyDef", "NodeSchema"]
