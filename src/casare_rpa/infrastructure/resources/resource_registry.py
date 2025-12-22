"""
Registry for managing resource node lifecycle.

This module provides the ResourceRegistry class for managing the lifecycle
of ResourceNode instances. It handles:
- Resource registration and lookup
- Initialization ordering
- Cleanup in reverse order
- Dependency tracking (future)

Entry Points:
    - ResourceRegistry: Main registry class
    - get_resource_registry(): Get singleton instance

Key Patterns:
    - Resources are initialized before workflow execution
    - Cleanup happens in reverse initialization order
    - Thread-safe singleton for global access

Related:
    - See domain.entities.resource_node for ResourceNode base class
    - See infrastructure.execution for workflow execution
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

if TYPE_CHECKING:
    from casare_rpa.domain.entities.resource_node import ResourceNode
    from casare_rpa.domain.interfaces import IExecutionContext


class ResourceRegistry:
    """
    Manages resource node lifecycle.

    Handles:
    - Resource initialization order (dependencies)
    - Resource cleanup on workflow end
    - Resource lookup by ID

    Usage:
        registry = ResourceRegistry()

        # Register resource nodes
        registry.register(db_connection_node)
        registry.register(browser_profile_node)

        # Initialize all resources
        success = await registry.initialize_all(context)

        # Use resources during workflow execution...

        # Clean up when done
        await registry.cleanup_all(context)

    Attributes:
        _resources: Dict mapping resource_id to ResourceNode
        _initialization_order: List of resource_ids in init order
    """

    def __init__(self) -> None:
        """Initialize empty resource registry."""
        self._resources: Dict[str, "ResourceNode"] = {}
        self._initialization_order: List[str] = []

    def register(self, resource_node: "ResourceNode") -> None:
        """
        Register a resource node.

        If a resource with the same ID already exists, it will be
        replaced with a warning.

        Args:
            resource_node: The resource node to register
        """
        resource_id = resource_node.resource_id
        if resource_id in self._resources:
            logger.warning(f"Resource '{resource_id}' already registered, replacing")

        self._resources[resource_id] = resource_node
        logger.debug(f"Registered resource: {resource_id} ({resource_node.node_type})")

    def unregister(self, resource_id: str) -> bool:
        """
        Unregister a resource node.

        Args:
            resource_id: ID of the resource to remove

        Returns:
            True if resource was found and removed, False otherwise
        """
        if resource_id in self._resources:
            del self._resources[resource_id]
            if resource_id in self._initialization_order:
                self._initialization_order.remove(resource_id)
            logger.debug(f"Unregistered resource: {resource_id}")
            return True
        return False

    def get(self, resource_id: str) -> Optional["ResourceNode"]:
        """
        Get a resource node by ID.

        Args:
            resource_id: ID of the resource node

        Returns:
            ResourceNode instance or None if not found
        """
        return self._resources.get(resource_id)

    def get_resource(self, resource_id: str) -> Optional[Any]:
        """
        Get the actual resource instance by ID.

        This returns the resource created by the node, not the
        node itself.

        Args:
            resource_id: ID of the resource

        Returns:
            The resource instance or None if not found/not initialized
        """
        node = self._resources.get(resource_id)
        return node.resource if node else None

    def get_all_nodes(self) -> List["ResourceNode"]:
        """
        Get all registered resource nodes.

        Returns:
            List of all ResourceNode instances
        """
        return list(self._resources.values())

    async def initialize_all(self, context: "IExecutionContext") -> bool:
        """
        Initialize all registered resource nodes.

        Initializes resources in registration order. If any resource
        fails to initialize, the process stops and returns False.

        Args:
            context: Execution context for resource initialization

        Returns:
            True if all resources initialized successfully, False otherwise
        """
        self._initialization_order.clear()

        logger.info(f"Initializing {len(self._resources)} resource(s)")

        for resource_id, node in self._resources.items():
            try:
                result = await node.execute(context)
                if result and result.get("success"):
                    self._initialization_order.append(resource_id)
                else:
                    error_msg = result.get("error", "Unknown error") if result else "No result"
                    logger.error(f"Resource '{resource_id}' failed to initialize: {error_msg}")
                    # Clean up already initialized resources
                    await self._cleanup_initialized(context)
                    return False
            except Exception as e:
                logger.error(f"Resource '{resource_id}' initialization error: {e}")
                # Clean up already initialized resources
                await self._cleanup_initialized(context)
                return False

        logger.info(f"Successfully initialized {len(self._initialization_order)} resource(s)")
        return True

    async def _cleanup_initialized(self, context: "IExecutionContext") -> None:
        """
        Clean up only the resources that were initialized.

        Used for partial cleanup when initialization fails partway through.

        Args:
            context: Execution context
        """
        for resource_id in reversed(self._initialization_order):
            node = self._resources.get(resource_id)
            if node:
                try:
                    await node.cleanup(context)
                except Exception as e:
                    logger.error(f"Error cleaning up resource '{resource_id}': {e}")
        self._initialization_order.clear()

    async def cleanup_all(self, context: "IExecutionContext") -> None:
        """
        Clean up all resources in reverse initialization order.

        This ensures resources are cleaned up in the opposite order
        they were initialized, respecting dependencies.

        Args:
            context: Execution context
        """
        if not self._initialization_order:
            logger.debug("No resources to clean up")
            return

        logger.info(f"Cleaning up {len(self._initialization_order)} resource(s)")

        # Clean up in reverse order
        for resource_id in reversed(self._initialization_order):
            node = self._resources.get(resource_id)
            if node:
                try:
                    await node.cleanup(context)
                except Exception as e:
                    logger.error(f"Error cleaning up resource '{resource_id}': {e}")

        self._initialization_order.clear()
        logger.info("Resource cleanup complete")

    def clear(self) -> None:
        """
        Clear all registered resources.

        Warning: This does NOT clean up resources. Call cleanup_all()
        first if resources need to be destroyed.
        """
        self._resources.clear()
        self._initialization_order.clear()
        logger.debug("Resource registry cleared")

    @property
    def resource_ids(self) -> List[str]:
        """
        Get list of all registered resource IDs.

        Returns:
            List of resource ID strings
        """
        return list(self._resources.keys())

    @property
    def initialized_ids(self) -> List[str]:
        """
        Get list of initialized resource IDs in initialization order.

        Returns:
            List of resource IDs that have been initialized
        """
        return list(self._initialization_order)

    def is_initialized(self, resource_id: str) -> bool:
        """
        Check if a specific resource has been initialized.

        Args:
            resource_id: ID of the resource to check

        Returns:
            True if resource has been initialized
        """
        return resource_id in self._initialization_order

    def __contains__(self, resource_id: str) -> bool:
        """
        Check if a resource is registered.

        Args:
            resource_id: ID of the resource

        Returns:
            True if resource is registered
        """
        return resource_id in self._resources

    def __len__(self) -> int:
        """
        Get number of registered resources.

        Returns:
            Number of registered ResourceNode instances
        """
        return len(self._resources)

    def __repr__(self) -> str:
        """String representation of registry."""
        return (
            f"ResourceRegistry("
            f"registered={len(self._resources)}, "
            f"initialized={len(self._initialization_order)})"
        )


# Module-level singleton
_registry: Optional[ResourceRegistry] = None


def get_resource_registry() -> ResourceRegistry:
    """
    Get the default resource registry instance.

    Returns a singleton ResourceRegistry instance for global access.
    Use this when you need a shared registry across the application.

    For isolated testing or multiple workflows, create a new
    ResourceRegistry() directly.

    Returns:
        Singleton ResourceRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ResourceRegistry()
    return _registry


def reset_resource_registry() -> None:
    """
    Reset the singleton registry.

    Useful for testing or when starting a new workflow session.
    Warning: Does NOT clean up resources. Call cleanup_all() first.
    """
    global _registry
    if _registry is not None:
        _registry.clear()
    _registry = None


__all__ = [
    "ResourceRegistry",
    "get_resource_registry",
    "reset_resource_registry",
]
