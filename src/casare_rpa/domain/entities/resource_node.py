"""
Resource node base class for shared configuration.

Based on Node-RED's config node pattern. Resource nodes:
- Define reusable configurations (DB connections, credentials, etc.)
- Are not part of normal execution flow
- Register their resources in execution context
- Can be referenced by other nodes via resource_id

Entry Points:
    - ResourceNode: Abstract base class for resource/config nodes
    - create_resource(): Override to create the resource instance
    - destroy_resource(): Override to clean up resources

Key Patterns:
    - Resources are initialized before workflow execution
    - Resources are stored in context.resources by resource_id
    - Other nodes reference resources via resource_id string
    - Cleanup happens in reverse initialization order

Related:
    - See domain.entities.base_node for BaseNode implementation
    - See infrastructure.resources.resource_registry for lifecycle management
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Any

from loguru import logger

from casare_rpa.domain.entities.base_node import BaseNode
from casare_rpa.domain.value_objects.types import (
    DataType,
    ExecutionResult,
    NodeStatus,
)

if TYPE_CHECKING:
    from casare_rpa.domain.interfaces import IExecutionContext


class ResourceNode(BaseNode):
    """
    Base class for configuration/resource nodes.

    Resource nodes define reusable configurations that other nodes
    can reference. They don't execute in the normal flow but provide
    shared resources.

    Examples:
        - BrowserProfileNode -> browser settings
        - CredentialNode -> secure credential reference
        - ConnectionPoolNode -> connection pool settings

    Usage:
        @node(
            name=\"Browser Profile\",
            category=\"browser\",
        )
        @properties(
            PropertyDef(\"resource_name\", STRING, required=True),
            PropertyDef(\"headless\", BOOLEAN, default=True),
            PropertyDef(\"timeout\", INTEGER, default=30000),
        )
        class BrowserProfileNode(ResourceNode):
            async def create_resource(self, context):
                return await create_browser_context(...)

    Attributes:
        resource_id: Unique identifier for this resource instance
        resource_name: Human-readable name for display
        resource: The created resource instance (after initialization)
    """

    def __init__(self, node_id: str, config: dict[str, Any] | None = None) -> None:
        """
        Initialize resource node.

        Args:
            node_id: Unique identifier for this node instance
            config: Node configuration dictionary. May contain:
                - resource_id: Custom resource identifier (defaults to node_id)
                - resource_name: Human-readable name (defaults to resource_id)
        """
        super().__init__(node_id, config)
        self._resource_id: str | None = config.get("resource_id") if config else None
        self._resource_name: str = config.get("resource_name", "") if config else ""
        self._resource: Any | None = None
        self._initialized: bool = False

    @property
    def resource_id(self) -> str:
        """
        Unique identifier for this resource.

        Defaults to node_id if not explicitly set via config.
        Other nodes reference this resource by this ID.

        Returns:
            Resource identifier string
        """
        return self._resource_id or self.node_id

    @property
    def resource_name(self) -> str:
        """
        Human-readable name for this resource.

        Used in logs and UI displays.
        Defaults to resource_id if not set.

        Returns:
            Resource display name
        """
        return self._resource_name or self.resource_id

    @property
    def resource(self) -> Any | None:
        """
        The created resource instance, if any.

        Returns None before create_resource() is called.

        Returns:
            Resource instance or None
        """
        return self._resource

    @property
    def is_initialized(self) -> bool:
        """
        Check if resource has been initialized.

        Returns:
            True if create_resource() has been called successfully
        """
        return self._initialized

    def _define_ports(self) -> None:
        """
        Define ports for resource nodes.

        Resource nodes have minimal ports since they don't
        participate in the normal execution flow.
        They output their resource_id for reference.
        """
        self.add_output_port("resource_id", DataType.STRING, "Resource ID")

    @abstractmethod
    async def create_resource(self, context: "IExecutionContext") -> Any:
        """
        Create and return the resource instance.

        This is called once when the resource node is initialized,
        before the main workflow execution begins.

        The returned resource is stored in context.resources and
        can be accessed by other nodes via the resource_id.

        Args:
            context: Execution context providing runtime services:
                - Variable access: context.get_variable()
                - Other resources: context.resources

        Returns:
            The resource instance (connection pool, client, config, etc.)

        Raises:
            Exception: If resource creation fails. The error will be
                caught and logged by the execute() method.

        Example:
            async def create_resource(self, context):
                host = self.get_parameter("host", "localhost")
                port = self.get_parameter("port", 5432)
                return await asyncpg.create_pool(
                    host=host,
                    port=port,
                    database=self.get_parameter("database"),
                )
        """
        pass

    async def destroy_resource(self, resource: Any) -> None:
        """
        Clean up the resource when workflow ends.

        Override this to close connections, release resources, etc.
        Default implementation does nothing.

        This is called during cleanup, after the main workflow
        execution completes (success or failure).

        Args:
            resource: The resource instance to clean up

        Note:
            Exceptions are caught and logged but don't propagate.
            Cleanup should be best-effort.

        Example:
            async def destroy_resource(self, resource):
                await resource.close()
        """
        pass

    async def execute(self, context: "IExecutionContext") -> ExecutionResult:
        """
        Initialize the resource and register it in context.

        This is called during workflow initialization, before
        the main execution flow begins.

        The resource is created via create_resource() and stored
        in context.resources under the resource_id key.

        Args:
            context: Execution context for resource registration

        Returns:
            ExecutionResult with success status and resource_id
        """
        try:
            self.status = NodeStatus.RUNNING

            logger.info(
                f"Creating resource '{self.resource_name}' "
                f"(id={self.resource_id}, type={self.node_type})"
            )

            # Create the resource
            resource = await self.create_resource(context)
            self._resource = resource
            self._initialized = True

            # Register in context
            context.resources[self.resource_id] = resource

            # Set output port value
            self.set_output_value("resource_id", self.resource_id)

            self.status = NodeStatus.SUCCESS
            logger.info(f"Resource '{self.resource_name}' created successfully")

            return {
                "success": True,
                "data": {
                    "resource_id": self.resource_id,
                    "resource_name": self.resource_name,
                },
            }

        except Exception as e:
            self.status = NodeStatus.ERROR
            error_msg = f"Failed to create resource '{self.resource_name}': {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": str(e),
                "error_code": "RESOURCE_CREATION_FAILED",
            }

    async def cleanup(self, context: "IExecutionContext") -> None:
        """
        Clean up this resource node.

        Called when workflow execution ends (success or failure).
        Calls destroy_resource() and removes from context.resources.

        Args:
            context: Execution context
        """
        if self._resource is not None:
            try:
                logger.info(f"Cleaning up resource '{self.resource_name}'")
                await self.destroy_resource(self._resource)
                self._resource = None
                self._initialized = False

                # Remove from context
                if self.resource_id in context.resources:
                    del context.resources[self.resource_id]

                logger.debug(f"Resource '{self.resource_name}' cleaned up")

            except Exception as e:
                logger.error(f"Error cleaning up resource '{self.resource_name}': {e}")

    def reset(self) -> None:
        """
        Reset resource node to initial state.

        Note: This does NOT clean up the resource - call cleanup() first
        if the resource needs to be destroyed.
        """
        super().reset()
        self._initialized = False

    def serialize(self) -> dict[str, Any]:
        """
        Serialize resource node to dictionary.

        Includes resource-specific fields in addition to base node data.

        Returns:
            Dictionary containing node data
        """
        data = super().serialize()
        data["resource_id"] = self.resource_id
        data["resource_name"] = self.resource_name
        data["is_resource_node"] = True
        return data


__all__ = ["ResourceNode"]
