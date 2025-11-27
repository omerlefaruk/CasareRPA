"""
CasareRPA Domain Layer - Pure Business Logic

This layer contains:
- Entities: Core business objects (Workflow, Node, Connection)
- Services: Domain services (validation, dependency analysis)
- Ports: Interfaces for adapters (dependency inversion)

CRITICAL: This layer must have ZERO dependencies on infrastructure or presentation.
All domain logic should be framework-agnostic and testable in isolation.
"""

__all__ = []
