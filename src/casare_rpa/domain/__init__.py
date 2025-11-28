"""
CasareRPA Domain Layer - Pure Business Logic

This layer contains:
- Entities: Core business objects (Workflow, Node, Connection)
- Services: Domain services (validation, dependency analysis)
- Ports: Interfaces for adapters (dependency inversion)
- Decorators: Node class decorators (executable_node)

CRITICAL: This layer must have ZERO dependencies on infrastructure or presentation.
All domain logic should be framework-agnostic and testable in isolation.
"""

from casare_rpa.domain.decorators import executable_node

__all__ = ["executable_node"]
