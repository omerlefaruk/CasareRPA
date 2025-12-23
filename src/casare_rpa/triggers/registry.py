"""
CasareRPA - Trigger Registry

Provides a singleton registry for trigger types and a decorator
for easy trigger registration.
"""

from typing import Dict, List, Optional, Type

from loguru import logger

from casare_rpa.triggers.base import (
    BaseTrigger,
    BaseTriggerConfig,
    TriggerType,
    TriggerEventCallback,
)


class TriggerRegistry:
    """
    Singleton registry for trigger types.

    The registry maintains a mapping of TriggerType to trigger classes,
    allowing for dynamic trigger instantiation and discovery.

    Usage:
        # Register a trigger class
        TriggerRegistry().register(WebhookTrigger)

        # Or use the decorator
        @register_trigger
        class WebhookTrigger(BaseTrigger):
            trigger_type = TriggerType.WEBHOOK
            ...

        # Get a trigger class
        cls = TriggerRegistry().get(TriggerType.WEBHOOK)

        # Create an instance
        trigger = TriggerRegistry().create_instance(
            TriggerType.WEBHOOK, config, callback
        )
    """

    _instance: Optional["TriggerRegistry"] = None

    def __new__(cls) -> "TriggerRegistry":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._triggers: Dict[TriggerType, Type[BaseTrigger]] = {}
            cls._instance._initialized = False
        return cls._instance

    def _ensure_initialized(self) -> None:
        """Ensure registry is initialized with default triggers."""
        if self._initialized:
            return

        self._initialized = True
        logger.debug("TriggerRegistry initialized")

        # Auto-import implementations to register them
        try:
            from . import implementations

            logger.debug("Trigger implementations loaded")
        except ImportError as e:
            logger.warning(f"Could not load trigger implementations: {e}")

    def register(self, trigger_class: Type[BaseTrigger]) -> None:
        """
        Register a trigger class.

        Args:
            trigger_class: Trigger class to register (must have trigger_type attribute)

        Raises:
            ValueError: If trigger_class doesn't have trigger_type attribute
        """
        if not hasattr(trigger_class, "trigger_type"):
            raise ValueError(
                f"Trigger class {trigger_class.__name__} must have a trigger_type attribute"
            )

        trigger_type = trigger_class.trigger_type
        self._triggers[trigger_type] = trigger_class
        logger.debug(f"Registered trigger: {trigger_type.value} -> {trigger_class.__name__}")

    def unregister(self, trigger_type: TriggerType) -> bool:
        """
        Unregister a trigger type.

        Args:
            trigger_type: Type to unregister

        Returns:
            True if unregistered, False if not found
        """
        if trigger_type in self._triggers:
            del self._triggers[trigger_type]
            logger.debug(f"Unregistered trigger: {trigger_type.value}")
            return True
        return False

    def get(self, trigger_type: TriggerType) -> Optional[Type[BaseTrigger]]:
        """
        Get trigger class by type.

        Args:
            trigger_type: Type of trigger to get

        Returns:
            Trigger class or None if not found
        """
        self._ensure_initialized()
        return self._triggers.get(trigger_type)

    def get_all(self) -> Dict[TriggerType, Type[BaseTrigger]]:
        """
        Get all registered triggers.

        Returns:
            Dictionary mapping TriggerType to trigger class
        """
        self._ensure_initialized()
        return dict(self._triggers)

    def get_types(self) -> List[TriggerType]:
        """
        Get all registered trigger types.

        Returns:
            List of registered TriggerType values
        """
        self._ensure_initialized()
        return list(self._triggers.keys())

    def is_registered(self, trigger_type: TriggerType) -> bool:
        """
        Check if a trigger type is registered.

        Args:
            trigger_type: Type to check

        Returns:
            True if registered
        """
        self._ensure_initialized()
        return trigger_type in self._triggers

    def create_instance(
        self,
        trigger_type: TriggerType,
        config: BaseTriggerConfig,
        event_callback: Optional[TriggerEventCallback] = None,
    ) -> Optional[BaseTrigger]:
        """
        Create a trigger instance.

        Args:
            trigger_type: Type of trigger to create
            config: Trigger configuration
            event_callback: Callback for trigger events

        Returns:
            Trigger instance or None if type not found
        """
        trigger_class = self.get(trigger_type)
        if not trigger_class:
            logger.warning(f"Unknown trigger type: {trigger_type.value}")
            return None

        try:
            return trigger_class(config, event_callback)
        except Exception as e:
            logger.error(f"Failed to create trigger {trigger_type.value}: {e}")
            return None

    def get_display_info(self) -> List[Dict]:
        """
        Get display information for all registered triggers.

        Useful for populating UI trigger type selectors.

        Returns:
            List of display info dictionaries
        """
        self._ensure_initialized()
        info_list = []
        for trigger_class in self._triggers.values():
            info_list.append(trigger_class.get_display_info())
        return info_list

    def get_config_schemas(self) -> Dict[str, Dict]:
        """
        Get configuration schemas for all registered triggers.

        Returns:
            Dictionary mapping trigger type value to JSON schema
        """
        self._ensure_initialized()
        return {
            trigger_type.value: trigger_class.get_config_schema()
            for trigger_type, trigger_class in self._triggers.items()
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"TriggerRegistry(registered={list(self._triggers.keys())})"


def register_trigger(cls: Type[BaseTrigger]) -> Type[BaseTrigger]:
    """
    Decorator to register a trigger class with the global registry.

    Usage:
        @register_trigger
        class WebhookTrigger(BaseTrigger):
            trigger_type = TriggerType.WEBHOOK
            display_name = "Webhook"
            ...

    Args:
        cls: Trigger class to register

    Returns:
        The same class (allows use as decorator)
    """
    TriggerRegistry().register(cls)
    return cls


def get_trigger_registry() -> TriggerRegistry:
    """
    Get the global trigger registry instance.

    Returns:
        Singleton TriggerRegistry instance
    """
    return TriggerRegistry()


def reset_trigger_registry() -> None:
    """
    Reset the global trigger registry (primarily for testing).

    Warning: This will clear all registered triggers.
    """
    TriggerRegistry._instance = None
    logger.debug("TriggerRegistry reset")
